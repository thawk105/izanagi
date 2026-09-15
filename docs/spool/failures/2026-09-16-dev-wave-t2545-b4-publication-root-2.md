---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2545-b4-publication-root
seq: 2
---

## 再発

### F357

- **再発: 2026-09-16** — 判定手順が `contract-loader-drift` に限定されていたため、別 producer で
  同じ形の偽赤を 1 本の焦点走 (9 test file・751 passed) を費やして踏んだ。今回の producer は
  `orchestrator/tests/test_p3_b4_producer_auth_experiment.py::test_main_worktree_has_no_permanent_prototype_or_pin_change`
  で、`orchestrator/campaign/p3_b4_producer_auth_experiment.py` の `PROTOTYPE_PATCHES` が名指す
  保護 path について `git diff --exit-code <HEAD>` の無差分を要求する。発行器を編集して未 commit の
  まま焦点走をかけると機械的に赤くなり、commit 後の単独再走は 50 passed・rc=0 だった。
  **これで「disk bytes が HEAD blob と一致することを要求する gate」は独立 2 producer で再現した**
  (契約 loader 閉包と producer-auth prototype pin)。判定手順を赤の理由行の語だけに依存させず、
  実装面を編集した wave では焦点走の赤を実装へ帰属する前に統合 commit 後の再走で切り分ける。
