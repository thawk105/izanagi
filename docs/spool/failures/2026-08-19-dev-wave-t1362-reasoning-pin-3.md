---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t1362-reasoning-pin
seq: 3
---

## 再発

### F57

- **再発: 2026-08-19** — `orchestrator/tests/test_codex_worker_launch.py` の全体スイート実行
  (`-n` 既定の高並列 xdist) で、共有計算機の負荷が高い時間帯に毎回50〜70件前後の
  非決定的失敗が発生した (`codex_exit_code=-15`・`evidence_status='missing'`・
  `stop_reason='max_wall_clock_s'`/`'max_attempts'` の signature、失敗node集合は
  走行ごとに異なる)。fix 適用前 commit (`0333abe6`) 単独でも対照実験で同数程度の
  flake を再現し、本 wave の変更とは無関係と確定した。`-n 4`/`-n 8` へ並列度を下げると
  flake 数は大きく減るが 0 にはならない。新設テストは分離実行 (タイミング非依存) で
  毎回全緑だった。
