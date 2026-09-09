# 段 4 裁定 — [T-2448] 軸 B5 の実行器

段 2 プラン (`plan_1.md`) と段 3 の敵対相談 2 本 (A = 正しさ境界、B = 整合と実効性) を裁定する。
段 3 の指摘は親が現物で裏取りしたものだけを real とした。裏取りの locator を各項に付ける。

---

## 0. 親 brief 自身の訂正 (B の指摘、real)

**brief の「DBLP 13 member は `不達`」「要求値は 2026-09-07 の実測では到達不能」は、実測を超えた一般化だった。**
閉包記録 §2 は **anchor 固有 request を 1 本も送っていない**と明記し、`不達` は共有 endpoint の環境 preflight からの
外挿だと書いている。正しい書き方は次である。

> 2026-09-07 に共有 endpoint へ出した probe は当該 host から anti-bot challenge を返した。
> **13 member の個別 live 値は未観測である。** live preflight で 13 本を実際に出すことには情報価値がある。

この訂正は実装方針を変える。live preflight は「どうせ不達だから形だけ」ではなく、**現在値を取りに行く経路**として作る。
brief 本文も同じ趣旨へ直した。

---

## 1. 成果物の名乗り (最重要の裁定)

段 3 は A・B とも「現 plan の範囲を『軸 B5 の実行器』と名乗るのは不可」と結論した。**この指摘は real である。**
部分登録 §5.2 の完走論理積は 1622 主 query・演算子 control・anchor 包含 control・補助探索・感度監査・分類・
未解決 `要裁定 == 0` の積であり、leaf 実行器はそのごく一部しか担わない。

**裁定:** 依頼が列挙した 4 点 (parser・fixture・schema・runner) と 2 つの preflight を作る。**scope は広げない。**
その代わり、**名乗りを実態へ合わせ、実装で構造的に担保する。**

1. 本 wave の成果物は **「軸 B5 の leaf 実行器 + registration preflight + anchor lookup preflight」** である。
2. **実行器は `完走` / `RW3` / 軸全体の状態を返す API を持たない。** 返せるのは leaf 単位の 6 条件の可否と証拠だけである。
   軸集約器を持たないことを、公開面の不在という形で構造的に担保する。
3. **本 wave が作る registration seal は暫定である。** checkpoint / resume を後で runner へ足すと runner の bytes が
   変わり、seal をやり直す必要がある。この事実を seal record 自身の field (`seal_scope`) と worklog に書く。
4. 「registration preflight を閉じた」とは書かない。書けるのは
   **「registration preflight の実装が揃い、親が実データで 1 回 rc=0 を得た」**までである。

---

## 2. 未登録の運用値 (A-6 / B-6、real)

content type の exact 集合・timeout・User-Agent・request 間隔・retry 対象の失敗集合・redirect の扱いは、
**凍結文が定めていない。** 実装子の便宜値で埋めると、凍結後に実装者が選んだ実行契約になる。

**裁定 (D-β):**

- **本走 (runner) の request 発行は fail-closed とする。** 実行器は本走の HTTP request を 1 本も発行できない。
  発行を試みると `UnregisteredRunPolicyError` を上げ、未登録の項目名を列挙して返す。
  **6 条件の評価そのものは、保存済み応答に対して完全に実装しテストする。** これが本 wave の実体である。
- **live preflight の content type だけは凍結文から導ける。** 閉包登録 §2.4 (b) は DBLP に `application/json` を
  逐語で書き、arXiv は Atom feed の `feed/entry`、OpenAlex は JSON の `id` を `収録` の形として書いている。
  よって live preflight は発行可能な実装にしてよい。**比較は media type だけで行い parameter を無視する** —
  arXiv は `application/atom+xml; charset=utf-8` を返す (親の実測、`parent-measurements.md` §2)。
- **timeout・User-Agent・request 間隔は既定値を持たせない。** 呼び手が明示引数で与え、実行器はその値を
  live preflight record へ逐語で記録する。実行器が値を発明しない。
- **redirect は自動追従しない。3xx は失敗として記録する。** catalog 外 URL へ自動発行しないためであり、受理集合を広げない。

**この裁定は「通らないように作る」ものではない。** 走行の認可はユーザーの手番であり、認可時に未登録値が決まる。
それまで実行器が勝手に決めないための構造である。

---

## 3. 所見ごとの裁定

### 採用する real (実装契約に入れる)

| # | 所見 | 裁定 | 裏取り |
|---|---|---|---|
| A-9 / B-7 | 3 値のどれにも入らない応答を丸めるな (DBLP の 200 JSON・`@total > 0`・該当 DOI なし) | **採用。** `unclassified` として記録し `passed=False` / `may_start_run=False`。3 値へ割り当てない | 閉包登録 §2.4 (b) の 3 形に当該応答が入らないことを本文で確認 |
| — | OpenAlex の判定は status を先に見る。404 は content type を見ずに `非収録` | **採用。** 順序を逆にすると、登録どおりなら `非収録` の応答が `不達` に化ける | 親の実測: OpenAlex 404 の content type は `text/html` (`parent-measurements.md` §2) |
| A-8 / B-4 | preflight 結果が bool で迂回できる | **採用。** production 入口が自ら registration preflight を実行し、durable で schema-valid な live preflight record (exact 30 member・同一 registration seal) を読む。bool と record 注入は test-only の private seam に限る | 軸 1 は実際に bool を受ける (`orchestrator/axis1_search/runner.py:1519-1523`) |
| A-14 | seal が file 列挙で、新規追加を検出できない | **採用。** `orchestrator/axis_b5_search/`、B5 schema 群、fixture root の **directory exact file set** を commit tree と worktree の双方で比較し、extra path を拒否する | 軸 1 も directory walk で extra を拒否 (`orchestrator/axis1_search/validator.py:730-746`) |
| A-12 / B-5 | DBLP の cutoff (`year <= 2026` の client 側判定、欠落は `要裁定`) が抜けている | **採用。** raw occurrence を 1 件も消さず、cutoff の採否と `要裁定` を別 field で記録する | 部分登録 §2.2 の DBLP 行 |
| B-4 (照合) | 短い非最終 page を条件 2 で落とすのは登録と違う | **採用。** 条件 2 は位置連続性だけ。実要素数は条件 3 が判定する | 部分登録 §5.1 条件 2 と条件 3 の逐語 |
| — | `capacity_echo` (`itemsPerPage` / `meta.per_page` / `@sent`) を gate にしない | **採用。** 記録のみ。軸 1 の条件 3 はこれを gate にしているが、B5 の登録は「実要素数の代用にしない」「最終ページで一致を要求しない」と明記している。写すと登録に無い狭さが入る | `orchestrator/axis1_search/validator.py:309-312` を実読。部分登録 §5.1 条件 3 |
| B-3 | `PAGINATION` enum が位置 parameter 名と種別を混ぜている | **採用。** `POSITION_PARAMETER = {"arxiv":"start","dblp":"f"}` と `PAGINATION_KIND = {"arxiv":"offset","openalex":"cursor","dblp":"offset"}` を分ける | 軸 1 evaluator の受理 kind は `offset` / `cursor` (`orchestrator/axis1_search/validator.py:313-335`) |
| B-2 | `G2-08` の主キーを arXiv ID と取り違えている | **採用。** 主キーは DOI `10.1137/17M1154679`、`1710.11258` は arXiv lookup key として別 field | 閉包記録 §1.2 の表 |
| A-2 | control の「発火」と request の「完走」の混同 | **一部採用。** 型として分け、**実行器は control の「発火」を出さない。** §4.1 の集合関係と §4.3 の包含の評価自体は scope 外 (下記 4) | 部分登録 §4.1 / §4.3 |
| B-1 | P1 の理由が現物と逆 | **採用 (理由の差し替え)。** 結論 (自前 parser) は維持。理由は下記 D-ε | `FROZEN_PREDECESSOR_PATHS` に軸 1 parser は無い (`orchestrator/axis1_search/validator.py:19-23`) |
| B-2 (反論) | P2 の理由が誤り | **採用 (理由の差し替え)。** 結論 (自前 runner) は維持。軸 1 は catalog policy に fallback を持つので「必ず読む」は誤り。非互換の本体は `logical_queries` 契約・`capacity_echo` gate・`get_rows` の値 | `orchestrator/axis1_search/runner.py:307-357` |
| B-3 (反論) | P3 のままでは最終 seal にならない | **採用。** 上記 1 の項 3 のとおり seal を暫定と明記する | 部分登録 §5.3 の「窓をまたぐ実行」 |
| B-1 (file:line) | 新規 file の行番号は locator でなく見積り | **採用 (nit)。** 実装指示は関数名で書き、変異の位置は実装後に振り直す | 現 `orchestrator/axis_b5_search/` は 2 file だけ |

### refuted / 不採用

| # | 所見 | 裁定 | 理由 |
|---|---|---|---|
| A-4 | `per_page` 流用の経路 | refuted (plan で既に塞がれている) | 上の `capacity_echo` 裁定で更に固める |
| A-5 | fixture の複製は事後登録ではない | refuted | 期待値を fixture から導かない規律は実装契約へ入れる |
| A-16 | seal record の自己参照 | refuted | plan は seal record を束縛表から外している |
| A-10 | member 削除による通過 | refuted | exact set で塞がれている |
| A-18 | 本 wave で live preflight を実行しない親裁定 | refuted (親が正しい) | 実行は不可逆で、ユーザー認可の手番 |
| — | W-ID / A-ID drift を追加の阻止 gate にする (plan の推奨) | **不採用。** 記録のみとする | 登録された述語は 3 値だけである。阻止 gate を足すと登録に無い受理集合の変更になる。`registered_openalex_work_id` と `observed_index_work_id` を並べて記録し、認可時に人間が見る |

---

## 4. scope 外の real 所見 (実装しない。ユーザー裁定パッケージへ)

次は real だが本 wave では実装しない。**実装したふりをせず、限界として記録する。**

1. **軸全体の完走述語 (§5.2 の論理積) を評価する軸集約器** (A-1)。leaf 実行器は `完走` を名乗れない。
2. **演算子 control (§4.1) の集合関係と anchor 包含 control (§4.3) の評価** (A-2)。
3. **実行証拠の exact-set manifest と offline 再評価器** (A-3)。
4. **登録全体を索引順・query ID 辞書順で走らせる production 入口** (A-11 / B-3)。
5. **checkpoint / resume と、複数窓にまたがる枝の独立 2 走 digest 一致** (P3 / B-3)。
6. **anchor 依存の補助 61 stream** (A-11 / B-8)。凍結 catalog の外なので後継凍結物での登録が要る。
7. **未登録の運用値 (content type の exact 集合・timeout・UA・間隔・retry 対象・redirect) の確定** (A-6 / B-6)。
   走行認可の前にユーザーが決める必要がある。本 wave は実行器が勝手に決めない形にするところまでを担う。

---

## 5. 実装契約 (段 5 の実装子が守る規則)

- **D-ε (自前 parser):** 軸 1 の parser を import しない。理由は 2 つあり、どちらも現物で確認済みである。
  (i) 軸 1 は次位置を `start + len(entries)` で作る (`orchestrator/axis1_search/parsers.py:189-191`) が、
  B5 は固定 step (0,200,400 / 0,100,200) を要求する。
  (ii) 軸 1 の `FROZEN_PREDECESSOR_PATHS` に parser は入っていない (`validator.py:19-23`) ので、
  import すると **B5 の seal が捕まえられない未束縛依存**になり、軸 1 側の変更が B5 の意味論を無検出で変える。
- **D-ζ (自前 runner):** 同様に軸 1 runner を import しない。写経元としてだけ読む。
- **D-η (条件の帰属):** 条件 2 = 位置連続性のみ。条件 3 = 実要素数 (container の `len` のみ)。
  `capacity_echo` は記録のみで gate にしない。
- **D-ι (OpenAlex の終端):** 条件 3 の「位置 + 実要素数 == 総件数」は cursor に適用しない。
  非最終は `actual_count == 200`、終端は `next_cursor` の不在で判定する。総件数との照合は
  **条件 5 の OpenAlex 規則** (cursor 終端までの distinct `results[].id` を `meta.count` と照合) が担う。
  これは凍結文全体の読みであって緩和ではない。条件 3 と条件 5 の両方を記録する。
- **D-θ (DBLP cutoff):** raw occurrence は消さない。`year <= 2026` の採否と、欠落・不正年の `要裁定` を別 field で持つ。
- **D-γ (分類不能):** 3 値に入らない応答は `unclassified` として記録し、`may_start_run=False`。
- **D-λ (preflight の束縛):** production 入口が自ら両 preflight を検証する。bool 注入は test-only。
- **D-κ (seal):** directory exact file set。extra path を拒否。seal record に自己 hash を書かない。
- **D-μ (control):** 「発火」を出さない。request 完走値だけを持つ。
- **期待値の出所:** test の期待値を production builder・parser 出力・fixture の `len` から作らない。
  凍結文の逐語からの独立 literal か、独立実装で書く。
- **自走 harness:** 新規 test file は末尾に `if __name__ == "__main__": raise SystemExit(pytest.main([__file__]))` を置く。
- **受入所要台帳:** B が最後に JUnit から `tools/update_acceptance_duration_ledger.py --add-only` で一度だけ更新する。
  手書きの秒数を書かない。

---

## 6. 所有分割 (B の指摘を容れて直列化)

段 3 B は「A の型が確定するまで B は着手できない」と指摘した。real である。**2 単位を直列に走らせる。**

- **単位 A (先行):** `orchestrator/axis_b5_search/parsers.py`、`orchestrator/tests/fixtures/axis_b5_search/**`、
  `orchestrator/tests/test_axis_b5_search_parsers.py`。
  完了時に型表 (dataclass field・parse error code・fixture manifest) を親へ返す。
- **単位 B (後続):** `orchestrator/axis_b5_search/anchor_registry.json`、`preflight.py`、`runner.py`、
  B5 schema 3 本、`orchestrator/tests/test_axis_b5_search_executor.py`、`orchestrator/tests/acceptance_duration_ledger.json`。
  `orchestrator/axis_b5_search/__init__.py` の所有者は B とする。

path は素集合で、A も自分の test file を持つ。brief の「各単位が自分の test」は満たされる。

---

## 7. 変異の事前登録 (DW-M01)

段 3 B が harness の判定 (失敗 node 集合と期待 node 集合の完全一致で `KILLED`) に照らして帰属を検査し、
plan の 12 候補のうち **安全に登録できるのは 3 件だけ**と判定した。親はこれを容れ、**probe 先行方式**を採る。

1. **probe 走行:** 下記候補を全件 SURVIVED 期待で流し、観測された赤 node 集合を収集する。
2. **本走:** 観測 node を期待へ写し、単一理由性が崩れた候補は登録から外して理由を台帳へ書く。

**候補 (実装後に位置を確定する):**

| id | 変異 | 単一理由性の見込み |
|---|---|---|
| m01 | OpenAlex の初回 cursor を literal `*` から `%2A` へ | 高 (段 3 B が refuted = 登録可と判定) |
| m02 | OpenAlex 期待 AST の children を set 化 (多重度を落とす) | 高 (同上) |
| m03 | live preflight の `all(収録)` を `any` へ | 高 (同上。29 収録 + 1 不達の fixture で member 数検査と分離) |
| m04 | 総件数 drift を最終 page の値で受理 | 中。3 page 構成にし非最終 page だけ drift させて条件 5 へ帰属させる |
| m05 | 条件 3 の実要素数を `capacity_echo` に差し替え | 中。索引を 1 つに絞り、条件 5 が同時に赤にならない fixture を使う |
| m06 | 本走発行の fail-closed (`UnregisteredRunPolicyError`) を外す | 高。発行拒否の test 単独 |
| m07 | seal の directory exact set を部分集合検査へ緩める | 高。extra file の負例単独 |
| m08 | DBLP の cutoff 判定 (`year <= 2026`) を落とす | 中 |
| m09 | 3 値に入らない応答を `収録` へ丸める | 高。`unclassified` の負例単独 |
| m10 | OpenAlex の判定順序を content type 先行へ入れ替える | 高。404 = `text/html` の fixture 単独 |
| m11 | `G2-08` の主キーを arXiv ID にする | 高。registry の exact 表単独 |
| m12 | retry delay の `6.0` を `7.0` へ (段 3 B の是正案どおり削除でなく置換) | 中 |

---

## 8. 段 5 へ進む条件

上記の実装契約を段 5 の prompt へ逐語で射影する。段 3 の 2 本の逐語は
`output/insights/2026-09-09_t2448-b5-executor/codex/` に置き、実装子には読ませない (親が裁定済みのため)。
