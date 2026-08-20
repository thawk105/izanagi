---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t1292-backoff-ipc-missing
seq: 1
---

## 再発

### F383

- **再発: 2026-08-20** — `tools/mutation_harness.py --runner-mode dispatch` の1回目投入
  (collection phase相当) が `orphan-hold` (`job-may-remain-without-terminal-evidence`) で
  rc=2 停止した。木の変異は無く (`変異を残した状態=unchanged`)、docs編集も行っていない
  ([T-1409] が切り分けた `dispatch_compute.py:1948` の `accounting-grace-expired` →
  `_fresh_qstat_gated_qdel` の `request-absent` 保守的latchと同型)。対象 job
  (`926304.nqsv`) は `output/pegasus-dispatch/<hash>/result.json` 上 `child_rc: 0` で
  正常終了しており (12 tests collected)、非決定的 timing 事象の再現とみなせる。
  復旧は既定手順どおり (手動qdelせずqstatの出力内容で不在を確認 → dirty file無し・
  clean/HEAD確認 → hold jsonとsubmission_dirを削除 → 新しい`--out`/`--attempt-out`で
  `--wrapper-attempt`を上げて再投入) で、2回目の投入は全7走 (collection・baseline・
  変異5件) が成功した。`check_acceptance_reds.py` 以外の呼び手 (`mutation_harness.py`
  内部のtest runner dispatch) でも同型が発生することを確認した。
