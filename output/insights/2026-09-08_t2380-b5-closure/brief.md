# 段 1 brief — [T-2380] 軸 B5 の後継凍結物で、2026-09-07 の部分登録が閉じられなかった 3 点を閉じる

- wave: dev-wave-t2380-b5-successor-freeze / branch worktree-dev-wave-t2380-b5-successor-freeze
- worktree (子は必ずこの path を使う): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze
- base: local main 34af5a571def179d1c841ce6e8a1cbcaeb9e9771 (fresh worktree、乖離 0)
- 実測環境: Pegasus login node (外部 HTTPS 到達あり、proxy env 無し)。計算ノード投入は受入全走のみ。

## scope (純増だけ)

凍結済み部分登録 `docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md`
(blob f7e3190f9ce92345fd4a91caecae8cd6bf7a5666) の §0 が挙げた 3 点を、**新しい日付の後継凍結物 2 本 + catalog 1 本**で閉じる。
2026-09-07 本文と 2026-09-05 登録本文 (blob 901ba833…) は 1 byte も変えない (D1208)。

1. **候補主キー (§0-1、§4.2):** 候補 3 群の有限 anchor 集合を**名称・著者・venue・年を手掛かりとしてだけ**先に凍結し (下表)、
   各 anchor の主キー (DOI / arXiv ID) を一次書誌資料 (doi.org 解決先 + Crossref `works/<DOI>` + arXiv API `id_list=`) で相互確認して locator つきで固定する。
   OpenAlex / arXiv の ID lookup (収録確認) を今回行い、DBLP は下記の不達事実を記録する。
2. **catalog seal (§0-2、§3.3、§5.3):** §3.3 の展開規則を決定的に実装した生成器 (Codex author) で
   1622 主 query + control 14 本 + venue 272 stream の機械可読 catalog を生成し、file bytes の SHA-256 を後継凍結物へ書く。
   §5.3 の registration preflight 全体 (parser / fixture / schema / 実行器 bytes の束縛) は **scope 外** — 実行器は存在せず、それは実行 wave の仕事。
3. **引用・著者経路の起点 (§0-3、§4.5):** anchor に依存する 3 経路 (後方引用 / 前方引用 / 著者) の stream ID・request template・ページング規則を後継凍結物で確定し、
   確定した anchor から起点 (OpenAlex work ID・第一/最終著者の author ID) を具体化する。

## 成果物の形と commit 順 (= 凍結順、ユーザー指示)

- **commit 1 (docs、親):** `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md` —
  閉じ方の事前登録: anchor 集合 (手掛かりのみ、主キー欄は空)、主キー確定手順と一次資料、catalog の生成契約 (生成器 path・出力 path・byte 形式・digest 手順)、
  3 経路の stream ID / template / ページング規則、§4.2 gate 項目 3 の erratum/amendment (P1)、DBLP 不達の事実。**この commit の前に anchor の ID を索引へ 1 本も照会しない。**
- **commit 2 (実装面、Codex author):** `orchestrator/axis_b5_search/__init__.py` + `catalog.py` + `orchestrator/tests/test_axis_b5_search_catalog.py`、
  および親が生成器を実走して得た `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json`。
- **commit 3 (docs、親):** `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md` — 確定した主キーと locator、索引別 ID lookup の結果、catalog の SHA-256、起点の具体値。
  claim-survey README の一覧行、worklog fragment、insight (`output/insights/2026-09-08_t2380-b5-closure/`: probe の生応答・codex 逐語・変異台帳)。

## 確定済みユーザー裁定 (引数)

本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。規律 2 を緩めない。実装面は Codex author (D95)。
既に凍結済みの部分は erratum でしか直さない。commit 順を凍結順にする。

## 不変条件

- 軸 B5 は本 wave 後も `RW0`。検索の実行を認可しない (§5.3 registration preflight と live preflight、人間認可が残る)。世界の不在を支持しない。
- 本 wave が出す外部 request は (a) anchor の書誌解決 (doi.org / Crossref / arXiv `id_list`)、(b) OpenAlex / arXiv の ID lookup、だけ。**catalog の query は 1 本も送らない。**
- anchor 集合は commit 1 で閉じる。以後の追加・削除は §5.4 の意味的 amendment。**結果を見て代表を選ばない。**
- 生成器は network・時刻・環境変数を入力にしない。同じ入力 commit で同じ bytes。

## 段 1 前の実測 (DW-O13、非 anchor の ID のみ使用、生応答は job dir probe/ に保存)

- OpenAlex `works/https://doi.org/<DOI>`: 収録 = 200 JSON (`id` = W-ID、`doi`、`title`、`ids`)、非収録 = 404 HTML。`works/arxiv:<id>` と `works/https://doi.org/10.48550/arXiv.<id>` は既知 arXiv 論文でも 404 → **OpenAlex は arXiv ID を鍵として引けない。**
- arXiv `api/query?id_list=<id>`: 収録 = 200 Atom で `feed/entry` 1 件、非収録 = 200 Atom で `opensearch:totalResults` 0・entry 0。arXiv は DOI を鍵として引けない (API に doi field 無し)。
- doi.org: HEAD 302 → 出版社 landing (`dl.acm.org/doi/<DOI>`)。Crossref `works/<DOI>`: 収録 = 200 JSON (`message.title/author/container-title/issued`)、非収録 = 404 text。
- **DBLP は本ホストから全入口 (`search/publ/api`、`doi/<DOI>`、`xml/release/`) が Anubis の anti-bot challenge (`algorithm=metarefresh, difficulty=1`、JS 駆動) を返し、UA (自前 / curl 既定 / ブラウザ風 / python-urllib) と `Accept` header に依らず 200 text/html。challenge の JS は模倣しない → DBLP の ID lookup は本環境で `不達`。**
  2026-08-27 の軸 3 索引実測は DBLP API に到達していたので、2026-08-27 以降に変わった事実。

## (P) 親の provisional 裁定 — 攻撃対象

- **(P1) §4.2 gate 項目 3 の erratum/amendment (受理集合が変わる、規律 2 の観点で最重要):** 凍結文は「1 件でも ID lookup が不達なら当該索引の走行と軸全体を `未完走`、slot は未配置」。
  しかし (i) arXiv は DOI を鍵に引けず 1950 年代の Annals 論文や SIGMOD 論文は arXiv に無い、(ii) OpenAlex は arXiv ID を鍵に引けない。文字どおりでは §4.2 は構造的に閉じない (D1207 型)。
  提案: 結果を (a) `収録` (索引が record を返す)、(b) `非収録` (索引は正常応答したが record 無し、または鍵型がその索引で引けない `鍵不適用`)、(c) `不達` (通信失敗・challenge・非整形応答) の 3 値にする。
  (c) は従来どおり索引可用性の失敗 = 当該索引の走行と軸全体 `未完走`。(b) は記録して当該 anchor をその索引の §4.3 包含 control から外す。
  **slot の配置 (未配置の解除) は主キーの固定 (項目 1・2) で決め、項目 3 は「実行前」= 実行 wave の live preflight で 3 索引とも再実施する。** 本 wave の OpenAlex / arXiv lookup は早期の収録確認であり live preflight を代替しない。
  ある (slot, 索引) で `収録` anchor が 0 なら、その組の包含 control は `適用不能` と記録し、限界として RW3 主張に併記する (軸全体の `未完走` にはしない)。**索引を母集合から外すことはしない。**
- **(P2) anchor 集合の構成 (下表、G1 1 件 / G2 8 件 / G3 7 件 = 16):** 登録 §3 の名指し (Cicada / KW 型 hill climbing / 加速確率近似 / SPSA の gain 選択 / polymorphic・adaptive CM / adaptive transaction scheduling) を必ず含め、
  C 相当 (標本数・推定誤差で窓幅を決める規則) の代表として適応 sampling 2 件を足す。**語彙的に検索式へ掛かりやすいかで選ばない** (D351 の逆 reward hack を避ける)。
- **(P3) catalog の field 集合は request bytes + ID + 構造 (block / 語 ID / 枝の block 順) に限る。** 期待 AST (§3.4) と期待 DBLP echo (§3.5) は凍結文の規則から実行 wave が導出する。catalog に置かない。
- **(P4) 3 経路の読み:** 前方引用は OpenAlex `works?filter=cites:<W-ID>,to_publication_date:2026-12-31&per-page=200&cursor=*` を §5.1 の条件で全頁取得し、上限 200 は client 側で横断主キー (DOI、無ければ OpenAlex ID) の辞書順昇順の先頭 200 件を採る。
  後方引用は `works/<W-ID>?select=id,referenced_works` の 1 request。著者は anchor の OpenAlex record の `authorships[0].author.id` と `authorships[-1].author.id` (同一なら 1 本) を `works?filter=author.id:<A-ID>,to_publication_date:2026-12-31&per-page=200&cursor=*` で全頁取得し上限 100 は同じ辞書順規則。
- **(P5) 変更面 = 下表のとおり。既存凍結 doc・axis1_search・related_work_search・schemas・tools/ は触らない。**

## 変更面の実アンカー表

| 種別 | path | 所有 |
|---|---|---|
| docs 新規 | docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md | 親 (commit 1) |
| 実装 新規 | orchestrator/axis_b5_search/__init__.py, orchestrator/axis_b5_search/catalog.py | Codex author (commit 2) |
| test 新規 | orchestrator/tests/test_axis_b5_search_catalog.py | Codex author (commit 2) |
| data 新規 | docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json | 親が生成器で生成 (commit 2) |
| docs 新規 | docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md | 親 (commit 3) |
| docs 更新 | docs/related-work/claim-survey/README.md (一覧行 3 行追加) | 親 |
| 参考 (読むだけ) | orchestrator/axis1_search/catalog.py (blob dfae508f…)、2026-09-01-axis3-registration-preflight.md、2026-09-02-axis1-search-amendment.md | — |

## anchor 集合 (手掛かり。主キー欄は commit 1 では空、commit 3 で一次資料により確定)

| ID | 群 | 手掛かり (著者 / 題 / venue / 年) | 記憶している識別子 (未確認) | 群に入れる理由 |
|---|---|---|---|---|
| G1-01 | G1-CICADA | Lim, Kaminsky, Andersen / Cicada: Dependably Fast Multi-Core In-Memory Transactions / SIGMOD / 2017 | 10.1145/3035918.3064015 | CCBench の適応 backoff の出自 (登録 §3) |
| G2-01 | G2-SA | Robbins, Monro / A Stochastic Approximation Method / Ann. Math. Statist. 22(3) / 1951 | 10.1214/aoms/1177729586 | SA と gain sequence の起点 |
| G2-02 | G2-SA | Kiefer, Wolfowitz / Stochastic Estimation of the Maximum of a Regression Function / Ann. Math. Statist. 23(3) / 1952 | 10.1214/aoms/1177729392 | 有限差分勾配型 hill climbing の起点 (登録 §3 名指し) |
| G2-03 | G2-SA | Kesten / Accelerated Stochastic Approximation / Ann. Math. Statist. 29(1) / 1958 | 10.1214/aoms/1177706705 | 差分符号の変化で step を適応 (加速確率近似、登録 §3 名指し) |
| G2-04 | G2-SA | Spall / Multivariate Stochastic Approximation Using a Simultaneous Perturbation Gradient Approximation / IEEE TAC 37(3) / 1992 | 10.1109/9.119632 | SPSA 原論文 |
| G2-05 | G2-SA | Spall / Implementation of the Simultaneous Perturbation Algorithm for Stochastic Optimization / IEEE TAES 34(3) / 1998 | 10.1109/7.705889 | SPSA の gain 選択 (登録 §3 名指し) |
| G2-06 | G2-SA | Delyon, Juditsky / Accelerated Stochastic Approximation / SIAM J. Optim. 3(4) / 1993 | 10.1137/0803045 | 適応 step の解析 |
| G2-07 | G2-SA | Byrd, Chin, Nocedal, Wu / Sample Size Selection in Optimization Methods for Machine Learning / Math. Program. 134(1) / 2012 | 10.1007/s10107-012-0572-5 | 勾配推定の分散で標本数 (窓幅) を動的に決める = C 相当 |
| G2-08 | G2-SA | Bollapragada, Byrd, Nocedal / Adaptive Sampling Strategies for Stochastic Optimization / SIAM J. Optim. 28(4) / 2018 | 10.1137/17M1154679, arXiv 1710.11258 | 同上 (inner product test) |
| G3-01 | G3-STM | Herlihy, Luchangco, Moir, Scherer / Software Transactional Memory for Dynamic-Sized Data Structures / PODC / 2003 | 10.1145/872035.872048 | contention manager 概念の導入 (DSTM) |
| G3-02 | G3-STM | Scherer, Scott / Advanced Contention Management for Dynamic Software Transactional Memory / PODC / 2005 | 10.1145/1073814.1073861 | backoff 系 CM (Polka 等) を走行中観測で決める |
| G3-03 | G3-STM | Guerraoui, Herlihy, Pochon / Polymorphic Contention Management / DISC (LNCS 3724) / 2005 | 10.1007/11561927_23 | 走行中に CM を適応切替 (登録 §3 名指し) |
| G3-04 | G3-STM | Guerraoui, Herlihy, Pochon / Toward a Theory of Transactional Contention Managers / PODC / 2005 | 10.1145/1073814.1073863 | CM の正しさ・進行保証 (D 側) |
| G3-05 | G3-STM | Yoo, Lee / Adaptive Transaction Scheduling for Transactional Memory Systems / SPAA / 2008 | 10.1145/1378533.1378564 | adaptive transaction scheduling (登録 §3 名指し) |
| G3-06 | G3-STM | Spear, Dalessandro, Marathe, Scott / A Comprehensive Strategy for Contention Management in Software Transactional Memory / PPoPP / 2009 | 10.1145/1504176.1504199 | CM 戦略の体系化と backoff の扱い |
| G3-07 | G3-STM | Dragojević, Guerraoui, Singh, Singh / Preventing versus Curing: Avoiding Conflicts in Transactional Memories / PODC / 2009 | 10.1145/1582716.1582725 | 走行中観測に基づく scheduler (Shrink) |

## catalog 生成器の契約 (段 2 plan の入力)

- module `orchestrator/axis_b5_search/catalog.py`。入力は §3.1 の 6 block 85 語 (列挙順・表記・ハイフンを逐語)、§3.2 の 10 枝 (block 順)、§3.3 の規則 1〜7、§3.5 の直積 7 枝、§4.1 の control 14 本 (X=`backoff`, Y=`update interval`)、§4.5 の venue 8 × 年 1993〜2026。
- 出力 JSON: `json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"` を UTF-8。field: `schema_version`、`registration_path` + `registration_blob` (f7e3190f…)、`closure_preregistration_path`、`cutoff`、`blocks` (語 ID `<block><2 桁>` と term)、`branches`、`queries` (query_id / index / branch_id / term_ids / request_template (`{POS}` `{CUR}` は literal) / first_page_url (POS=0、`cursor=*`))、`controls` (14 本、`shares_request_with`)、`aux_venue_streams` (272)、`expected_cardinalities`。
- CLI: `python3 -m orchestrator.axis_b5_search.catalog --output <path>` と `--verify <path>` (file bytes == 生成 bytes を要求、不一致は非 0)。
- test: 件数 (10/10/1602/14/272)、§3.3 の照合例 `B5-Q10@dblp/T01-O01` の URL bytes 一致、percent encoding 規則 (空白 `%20`、`"` `%22`、`(` `%28`、`)` `%29`、`:` `%3A`、`[` `%5B`、`]` `%5D`、`,` は符号化しない)、6 block 互いに素・85 語、DBLP 直積に重複 bytes 無し、`B5-CTL-AND2023@dblp` が `B5-CTL-AND@dblp` と同 bytes、決定性、`--verify` が 1 byte 改変を拒否。
- network・時刻・環境変数を入力にしない。既存 `orchestrator/axis1_search` を import しない (別 epoch の catalog と束縛を混ぜない)。
