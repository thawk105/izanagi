---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-04
wave: dev-wave-t2228-a2-gate-layers
seq: 1
---

## 再発

### F707

- **再発: 2026-09-04** — A-2 certification の既完走 attempt `t2022-20260828c` (2026-08-28) の adopted cell が同じ型だったと判明した。当時の driver (`639c1dbad`) は patch 無しの共有木を `run_campaign` へ渡し、`BACKOFF_FIXED=10` / `=5` は CMake に無視され、`BACK_OFF=1` (内蔵指数 backoff) だけが効いていた。一次資料は当時の WAL の `src_token` が adopted でも `stock` であること。関門 (D1198) を通した初の実走 `t2228-20260904a` では adopted が非 `stock` token になり、stock より速い逆符号の値が出た (certified ではない)。位置づけは `output/insights/2026-09-04_t2228-a2-gate-layers/ruling-package.md` の裁定 2。
