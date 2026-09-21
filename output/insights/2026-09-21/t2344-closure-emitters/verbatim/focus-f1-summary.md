# 焦点走 f1 (実装 commit `f605a7ba2`)

- 投入: 2026-09-21 09:16 JST、計算ノード dispatch (`tools/run_tests.py … --force-dispatch`)。
- job: `14685.nqsv` (queue `gen_S@nqsv`)、job の Elapse 319 秒、pytest 区間 313.01 秒。
- 対象: 31 file = 変更した test 6 file + 変更 production の consumer test + 新収載 11 本の自 test +
  `DW-O26` の inventory 4 群 (`test_campaign.py` / `test_official_perf_closure.py` /
  `test_p3_exploration_namespace.py` / `test_p3_b4_wiring_probe.py`)。
- **結果: 4441 passed, 9 skipped, 0 failed, 0 error。**
- raw log: `focus-f1.log` (sha256 `0092070a800cee712536c6368c15cea547cdc9d30378257b849e93e029edd5c0`)。

赤は 1 件も無い。skip 9 件は既存の環境依存 skip で、本 wave の変更に帰属しない。

## 訂正 (段 6 レビュー B-8、2026-09-21 09:3x JST)

「skip 9 件は既存の環境依存 skip」は不正確。raw log には少なくとも 5 件の明示的な **growth hold** (`IZANAGI_GROWTH_HOLD_V1`) が記録されている。
内訳は「環境依存 skip + growth hold」であり、単なる環境依存ではない。いずれも本 wave の変更に帰属しない点は変わらない。
また本走は**焦点走であって受入全走ではない** (log 自身が明記)。この緑をもって変異検査・受入全走の完了とは扱わない。
