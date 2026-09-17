---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-prereg-s11-3-addendum-d2103
seq: 1
---

## 再発

### F945

- **再発: 2026-09-17** — 事前登録 §11.3 追補 wave (docs のみ、post-claim merge 後の tip `f994871c7`) の受入 attempt 1 で、
  `test_t1259_qsub_env_delivery_probe.py` の 2 件が setup error になった (shard-0 errors=2、全体 24,499 passed /
  67 skipped / 2 error、子 rc=1、受領証未発行で待ち手は rc=70)。junit.xml の setup traceback は既報と同一で、
  `git -C <wave worktree> ls-files --others --exclude-standard -z` の 30.0 秒 TimeoutExpired。門番は leaders=1 /
  load1 42.5 < load5 56.9 で投入しており、受入開始時点の login load average は 40〜70 台。同 tip・同 file の
  単独再走 (`run_tests.py --force-dispatch`、2828.nqsv) は 51 passed / 16.94 秒、job Elapse 23 秒、rc=0 で非再現。
  wave の変更は docs のみで当該 fixture・probe・Git 呼出しは触っていない。既存の恒久対応どおり timeout 拡大・
  fixture の stub 化・除外・gate 新設はせず、`DW-O18` に従い受入を 1 回再走した。記録は
  `output/insights/2026-09-17/prereg-s11-3-addendum-d2103/README.md`。
