---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-10-01
wave: dev-wave-selfreview-failures-record
seq: 2
title: 同原因の再試行の自己点検 (SELF-REVIEW) のうち land 済み wave の下書き 7 本を failures に記録し、型 1〜4 と手当て先を insight に残した (docs のみ、branch worktree-dev-wave-selfreview-failures-record)
---

## 本文

- land 調整役の依頼 md_3 (`/work/1/SFC/tanab/tmp/self-review-2026-10-01/md_3.txt`) による記録 wave。実装なしの軽量版 (段 2・3 省略、段 6 は独立 read-only レビュー 1 本)。
- 新規 F 3 本: 撤去 tool の rc=75 の固定間隔再試行 ({{F:cleanup-lock-busy-fixed-interval-retry}}、md_44・md_35・codex-astra-ultra・md_37 を束ねた)、共有 `--evidence-dir` による rc=20 を reason を読まず 12 回再試行 ({{F:cleanup-shared-evidence-dir-rc20-blind-retry}}、md_37)、pin 前進で壊し正例 4 本が外れても赤にならない ({{F:pin-advance-drops-positive-controls}}、md_15)。
- 再発 5 件: F26 (md_33 の `worktree add` EINTR)・F51 (md_44 の撤去 rc=21 の自己占有)・F139 (md_33 の SMOKE 1 投入 1 欠陥)・F1038 (md_35 の PYTHONPATH の空振り)・F1092 (md_35 の Bash guard 約 9 回)。
- md_15 の新規 T の下書きは起票しなかった。[T-2854] の残り (2) が同じ作業 (F で外れる壊し patch 4 本の作り直し) を P1 で既に持つため。下書きの完了条件は insight §4 に写した。
- 下書きの回数は撤去 log で数え直した。md_44・md_35・codex-astra-ultra は一致、md_37 は下書きの「rc=75 計 13 回」と log の行数 (run1 12 行・後続 15 行) が合わないので log の行数を書いた。
- 一次資料 `output/insights/2026-10-01/self-review-retry/README.md` (型 1〜4 の集約、型ごとの手当て先 md_1・md_2、取り込みの対応表)。

## 次の一手差分
