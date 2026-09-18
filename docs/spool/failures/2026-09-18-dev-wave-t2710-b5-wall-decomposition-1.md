---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2710-b5-wall-decomposition
seq: 1
---

## 再発

### F945

- **再発: 2026-09-18** — [T-2710] 計測 wave の replica shard-0 (計算ノード generic dispatch、受入 child と同じ argv + 観測 plugin、
  worktree は lustre 上) で同型が 2 度出た。job 5620.nqsv の B 走 (12:58〜13:07) は `test_t1259_qsub_env_delivery_probe.py` の
  setup error 22 件 (`git ls-files --others --exclude-standard -z` の 30 秒 TimeoutExpired) に加え、real-repo flock deadline の
  worker internal error で rc=16。job 5663.nqsv の 3 走目 (13:50〜13:56) は同 file の setup error 4 件で rc=1。いずれも同時刻に
  他 wave の受入 session 4 本が別ノードで並行していた (lustre の共有負荷が疑われるが因果は未同定)。事前登録の規則 (失敗走は除外、
  同条件 1 回まで置換) に従い、前者は 5650.nqsv で置換 (344.4 秒、緑)、後者は補助観測のため置換せず n=2 とした。恒久対応は既報のまま
  変えない (timeout 拡大・fixture の stub 化・除外・汎用 gate の新設は行わない)。記録は
  `output/insights/2026-09-18/t2710-b5-wall-decomposition/README.md` §3・§10。
