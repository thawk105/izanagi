---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2711-ancestry-check
seq: 1
title: [T-2711] t080 hermetic e2e の独立検算を ancestry 2 件まで拡張し 17 observation 全件にした (コード、branch worktree-dev-wave-t2711-ancestry-check)
---

## 本文

- ユーザー依頼の範囲 (本題の検算 2 件だけ、案 B 不採用のまま、規律 2 を緩めない) で 1 wave。一次資料は
  `output/insights/2026-09-20/t2711-ancestry-check/README.md` (穴の形、literal を選んだ理由、焦点走、変異 matrix 新旧両走、所見と裁定)。
  専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2711-ancestry-check/HANDOFF.md`。
- **できた。** `test_s8b_oracle_driver.py` の hermetic e2e に、`items[15:]` (known_axes / holdout の ancestry observation) を literal 2 dict
  (`status="missing-commit"`, `observed=None`, 記録 SHA の逐語) と完全一致で比較する assert 1 個を Codex author が足した (実装 commit
  `d24ec35ea`、20 行追加のみ)。production・report・fixture builder・helper・nodeid 集合は不変。
- 段 3 相談 (2 レンズ 1 本) の must-fix 2 件を採用し前提を 2 つ訂正した: (A1) `test_t080_freeze_migration.py:1227` の unit test が
  `_classify_ancestry` の missing 分岐を直接検査済みで、status/observed の変異は全スイートでは既に KILLED → 本 wave の主張は
  「e2e の独立検算を末尾 2 件まで拡張」に限定。(A2) 記録 commit `2066ce6b…` / `2e20d441…` は現行 repo の object store にも無い
  (`cat-file -t` rc=128 ×2、`docs/freeze-permanent-design-s2.md` の anchor 表が `anchor_status=="missing"` と記録する既知事実) →
  実 repo test も missing 分岐を git 導出で検算している。新 T・新 gate は起こさない。棄却した所見は無い。
- 変異 matrix は DW-M08 の新旧両走 (走行集合 = e2e node + unit node、独立 clone 2 本、計算ノード): 旧版 (b7f970dfa) = baseline PASSED、M1/M2 (status/observed) は unit test 1227 行だけが kill、M3 (subject) SURVIVED；新版 (d24ec35ea) = baseline PASSED、M1/M2 は unit + e2e、M3 は e2e だけが kill。**両版とも期待 node 完全一致 3/3**、新版 e2e の赤は 3 件とも追加 assert (2058 行)。M3 が「新 assert だけが検出する差分」。
- 段 6 レビュー 2 本: must-fix 0 (patch GO)。should 2 (実 repo test を走行集合に入れない理由の言い直し、先行裁定への「訂正」表現の限定) を docs で採用、nit 2 (comment 2 行目、M2 の削減) は不採用 (成果物不変)。fix 子なし。初回投入は親が review 段に `--reasoning` を付けて rc=2、再投入。
- 訂正: 起点 entry 1554 §2-2 の「alternates 経由で `not-ancestor` へ変わりうる」は、M `_capture_head` が alternates を 2026-07-22 から
  `receipt.git_error` で拒否する (先行裁定は可能性で書いており、案 B 不採用は他理由で残る、再裁定しない)。brief 初版の
  「source-repin 10 + generator-metadata 5」は 13 + 2 の誤り。
- 工数: codex 4 本 (consult 1、author 1、review 2、rc=0 で受理検査 OK)、計算ノード job = 焦点走 1 (348 passed / 7 skipped、303 秒、11855.nqsv) + 変異 8 走 (旧 4 + 新 4) + provenance 全史監査 1 (11770 件、新規違反なし) + 受入全走。実 repo test は growth hold で焦点走では未実行。

## 次の一手差分

### 完了

- [T-2711] hermetic e2e の `items[15:]` (ancestry 2 件) を literal の独立期待値と完全一致で比較する assert を足し、17 observation 全件が
  独立検算の対象になった (実装 commit `d24ec35ea`)。変異 matrix (新旧両走) で e2e 単体の追加検出力を実測し、既存 unit test が既に
  kill する変異と分けて記録した。
  remaining: none
  base: 93a3e67beaff726379ff3bd8efdbbe210dde26c46e88200f9b4460bfd92f7031
