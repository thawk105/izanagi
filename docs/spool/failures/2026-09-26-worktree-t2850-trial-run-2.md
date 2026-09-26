---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-26
wave: worktree-t2850-trial-run
seq: 2
---

## 再発

### F707

- **再発: 2026-09-26** — [T-2850] の費用比較で、検証の同時化を測る使い捨て script が「固定 8 µs の候補」を `-DCCBENCH_BACKOFF_FIXED=8` だけで指定し、stock と同じ build の trace を測った (取引数と検査時間が stock と一致したことで親が気づいた)。候補の値は hole code の `now_backoff` 代入か template patch で入り、define だけでは効かない。測った 1 job (458 s) は stock の再現として扱い、同じ定義の rh の job は投入前に止め、flag だけで実現できる B0-L-W0 を代理にした。記録は `output/insights/2026-09-26/t2850-trial-pause-cost-options/README.md` §3.2。
