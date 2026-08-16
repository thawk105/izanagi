---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1207-closure-exact14
seq: 3
---

## supersede 追記

- F357 **supersede: 2026-08-17** — enforcement source closure は {{D:enforcement-closure-exact14}} で exact 14 path になった。「12 path」は「14 path」と読み替える。加えて本 wave の実測で偽赤の範囲が確定した — 閉包 member を編集した状態でも、`_REPO_ROOT` を一時 repo へ差し替える node (T671 / artifact admission の E1 / S6 / S8a) は偽赤にならず、統合 commit 前に赤くなったのは実 checkout の live closure を capture する `orchestrator/tests/test_layer3_report.py::test_accepted_report_requires_e1_and_records_epoch` の 1 件だけだった (commit 後の同範囲再走は 465 passed / 0 failed)。偽赤候補を「閉包 member を触る wave の広い consumer 群」と見積もるのは過大で、判定手順は既載どおり赤の理由行に `contract-loader-drift` があるかで行う。
