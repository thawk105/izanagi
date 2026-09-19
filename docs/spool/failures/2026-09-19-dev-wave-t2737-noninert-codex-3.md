---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-19
wave: dev-wave-t2737-noninert-codex
seq: 3
---

## 再発

### F386

- **再発: 2026-09-19** — [T-2737] 回収 wave。変更した production file (`patches/ss2pl-lock-protocol-study.patch`) の
  consumer test を file 名と symbol 名で引き、焦点走を `test_ss2pl_lock_study.py` (103 件) に閉じた。
  `patches/` を directory glob で目録化する `test_ccbench_spawn_sites.py` は名前で届かず、受入全走で初めて
  include guard 3 件の候補混入 (define 目録 3 test の赤) が出た。閉包の鍵は「この directory を読む test」という
  性質で立てるべきで、`DW-O26` の参照関係の抽出は glob・directory 走査の consumer も含める。
  修正は Codex author の fix3 (目録関数の新規 file include guard の構造的除外、正例 1・負例 2) で閉じ、
  記録は `output/insights/2026-09-19/t2737-noninert-implementation/README.md`。
