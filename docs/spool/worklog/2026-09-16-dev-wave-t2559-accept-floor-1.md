---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2559-accept-floor
seq: 1
title: 受入の最遅 shard と床を実測で shard-0 の t080 e2e へ改め、fixture 高速化 3 案をいずれも不採用と裁定した (docs + 計測成果物、branch worktree-dev-wave-t2559-accept-floor、実装差分ゼロのため変異 matrix 免除)
---

## 本文

- ユーザー依頼は「受入全走の高速化・効率化」。**実装しないと裁定した。** 一次資料は
  `output/insights/2026-09-16/t2559-acceptance-floor-t080/` (段 1 brief・段 2 plan・段 3 の 2 レンズ・
  段 4 裁定の逐語を同 dir に凍結した)。branch 名は起案時の関連 ID に由来するが、本 wave は
  [T-2559] が求める (a)(b) の分離測定そのものではない。
- **律速を実測で確定し直した。** 2026-09-16 の直近 7 走で junit `time` の中央値は shard-0 = 325.5、
  shard-1 = 229.8、shard-2 = 236.6 秒。**300 秒超は shard-0 だけ**で、その span は最長単体 node
  (t080 e2e、222.51 秒) にほぼ等しい。**D1918 と [T-2495] が記録した「最遅は shard-2、床は
  material-report group」は失効した** — 同 group は現在 shard-1 の最忙 worker 169.5 秒である。
  対象の改めは {{D:accept-floor-is-shard0-t080}}。
- **段 1 の親前提を段 2 plan が反証した。** 「oracle は output を 4 path しか読まない」は誤りで、
  holdout の production scanner が repo 全体 (tracked + 非 ignored untracked + ccbench) を列挙して
  非除外の全件を read/decode する。したがって複製対象を固定 whitelist へ絞る案は受理集合を変える。
- **段 3 の 2 レンズが親 brief の数値 4 件を訂正した。** 「base 構築 1 回 = 144 秒」は誤帰属
  (計測元は `issue_receipt=False` かつ base→test コピー 2 回を含む)、「CPU の 32%」は誤り
  (junit 所要は待ちを含む)、「単独走なので固有費用」は強すぎる、「1,852→22,976 件と 15〜22→144 秒の
  対応」は未証明。いずれも real と裁定して採用した。棄却した所見は無い。
- **高速化 3 案をすべて不採用にした。** 詳細は {{D:t080-fixture-index-speedup-not-now}}。
  固定 whitelist は受理集合を変え、object store の全面借用は ancestry 観測を変えて既存 assert が
  検出せず、blob 移送案は効果の符号が未確認である。
- **index 化の下限は実測した。** 現行 `git add -A` が 79.33〜191.30 秒に対し、実 repo の既存 blob OID を
  `update-index --index-info` で登録すると 0.03〜0.04 秒 + `write-tree` 0.60 秒 + `commit-tree` 0.01 秒
  だった。複製 24,017 件のうち 24,017 件すべてが実 repo の index entry と path 一致する。
  ただしこの経路は実 repo の object store を fixture へ見せることで成立しており、自己完結化は
  660 MB の pack 化を要して削減分を食う見込みである (未測定)。
- **副産物として fixture の忠実性の穴を見つけた。** 上の 2 方式の tree 差はちょうど 1 file
  (`orchestrator/tests/fixtures/sort_swo_masstree/config.h`) で、原因は同 dir の `.gitignore` の
  `/config.h` である。実 repo では tracked なので ignore に優先するが、fixture は `git init` からの
  `git add -A` なのでこの tracked file を取り込めていない。
- **意味を変えない圧縮設定では効果を確認できなかった。** `core.compression=0` と
  `+core.looseCompression=0` は 3 方式とも tree OID が同一 (意味不変を確認) だったが、所要は
  round 1 で +2.99 / +18.68 秒、round 2 で −18.81 / −19.30 秒と符号が反転した。
- **login node の外乱が 28 倍あった。** 同一内容の `output/` 複製が 20.64〜571.40 秒に振れた。
  本 wave の比較はすべて同一 tree 内で方式を交互に測った対比較だけを使っている。
- **段 8 の自己改善候補 2 件は「実施しない」へ落とした。** (i) 親 probe を `cmd | tail -N` で
  背景化すると途中経過が buffer に消える、(ii) 受入の律速を選ぶ依頼では過去の受入 shard 成果物を
  親が先に集計する、の 2 件である。収容先の `DW-C01` は exact 契約かつ単節予算 1000 bytes に対し
  追記後 1236 bytes となり、既存記述の削減は exact pin の更新 (実装面) を伴う。独立 3 例には
  達していないので D782 が委任する D730 の手順に従って落とした。上限引き上げは行っていない。
- 工数: codex 子 3 本 (plan 1、consult 2、すべて rc=0 で受理検査 OK)。親 probe 6 本
  (単独走 1、複製費 1、base 構築費 1、index 対比較 2、圧縮 variant 1)。うち 1 本は
  `cmd | tail -N` の背景化で途中経過が buffer に消え、900 秒 timeout まで 1 行も得られず空費した。

## 次の一手差分

### 新規

- {{T:t080-fixture-visible-set-gap}} **P2・新規**: t080 fixture が実 repo の tracked file
  `orchestrator/tests/fixtures/sort_swo_masstree/config.h` を取り込めていない
  (同 dir の `.gitignore` の `/config.h` が、`git init` からの `git add -A` では優先されるため)。
  fixture の可視集合が実 repo と 1 件ずれており、その file は fixture 内の scan 対象から外れている。
  取り込むと忠実性は上がるが所要は増える方向なので、成果物影響を測って裁定する。
- {{T:t080-index-reuse-self-contained}} **P2・新規**: index 化の下限 0.61 秒へ自己完結で届く経路を測る。
  実 repo の object store を露出せずに必要 blob だけを fixture へ移送する費用 (pack 化 660 MB) が、
  削減分 79〜191 秒を食うかどうかは未測定である。食わないなら採用の再検討に値する。
- {{T:accept-floor-growth-design-ruling}} **P1・ユーザー裁定待ち**: 受入の床にある t080 e2e は、
  実 repo の git 可視 output を fixture へ写し production scanner がその全件を read/decode する構造で、
  tracked output は 2026-07-27 の 1,852 件から 2026-09-16 の 22,976 件へ増えた。成長比例を断つには
  この設計 (= 受理集合) を変える必要があり、親の一存では決めない。あわせて、fixture 側の全件 scan が
  守る検出力と、実 repo を直接 scan する検査 (`orchestrator/tests/growth_test_holds.py` で保留登録) の
  重複をどちらが持つべきかも諮る。
- {{T:t080-report-observation-coverage}} **P2・新規**: t080 の report の独立検算が 17 observation の
  うち先頭 15 件しか覆っていない。案 B を採らなくても残る検出力の穴であり、残り 2 件の
  ancestry 系 observation を独立期待値と比較する形にできるかを調べる。
