---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2668-tmpdir-outside-repo
seq: 2
---

## supersede 追記

- F998 **supersede: 2026-09-16** — 恒久対応の「別 wave が Codex author で直す」は実施済み: t316 の fixture は 9d9df64f1 が `main checkout の親/.izanagi-t316-live` へ、`test_hooks.py` の hardlink test は [T-2668] (cc6e1fc54) が同じ形で `main checkout の親/.izanagi-t2146-hardlink` へ移設した。同型で literal grep に掛からなかった `test_s1_9pair_figure_provenance.py` の test_p9 (`dir=ROOT`) は production の `_repo_path` が repo 外を拒否するため `.gitignore` 済みの `output/runs/` 配下へ移した。pytest 受入で発火する repo 直下の生成箇所は 0 件 (`test_calibration_freeze_authority_contract.py` の `dir=str(ROOT)` は plain runner 専用)。
