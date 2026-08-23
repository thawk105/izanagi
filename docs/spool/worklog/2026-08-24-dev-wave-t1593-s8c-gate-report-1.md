---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1593-s8c-gate-report
seq: 1
title: [T-1593] 8c 事前登録関門の状態と根拠を既存 evaluator から構造化報告した (コード+テスト、branch worktree-dev-wave-t1593-s8c-gate-report、変異 matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 段2 plan と段3敵対相談2本で、既存 raw JSON との差分、readiness と認可の混同、非発効 exit 0、private digest、二重正本を攻撃した。
- 段4で、status は既存 `effective` の一対一射影だけ、認可は USER / DOES_NOT_AUTHORIZE / NOT_REPRESENTED、非発効は exit 1 と裁定した。
- 実装 commit `758836ab`、review fix `f3c8ed63`、self-run 索引修正 `b6d36895`。実装面は Codex author が担当した。
- 段6 review 2本は argparse の plain help/usage 迂回、schema exact key、evidence 多位置、module guard 実配線を real とし、fix後の焦点再レビューで静的 closed / regressed 0を確認した。
- 初回焦点走は親の pytest-only allowlist 誤登録で23 passed / 1 failed。self-run 節へ移した再走は24 passed。
- 変異初回は M1〜M3/M5〜M7 exact KILLED、M4は追加のschema testが発火してMISMATCH。erratum再走でM4もexact KILLEDとした。
- 現行 `c079ff04` の report は freeze valid / decider match だが、§5は1/9、C01〜C12は全件EVIDENCE_UNDEFINED、全体はNOT_EFFECTIVE / exit 1。
- report は正式測定を認可せず、欠落条件を実装せず、非充足を緑へ倒さない。詳細とscope外は `output/insights/2026-08-24_t1593-s8c-gate-report.md`。

## 次の一手差分

### 完了

- [T-1593] 既存 evaluator の commit 指定評価を再利用し、全体状態・§5・C01〜C12の状態/理由/証拠を schema v1 JSON へ構造化した。正式測定認可と欠落条件の実装は含めない。
  remaining: none
  base: f1d13afec38490e0b149676ec6b037bcbe951deddd7e26c111f1f1d9c60f2ffc
