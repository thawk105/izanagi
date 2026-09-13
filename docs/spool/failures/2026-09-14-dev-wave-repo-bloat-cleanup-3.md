---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-repo-bloat-cleanup
seq: 3
---

## 再発

### F945

- **再発: 2026-09-14** — repo 膨張監査 wave (docs のみ、tip `741e27283`) の受入 attempt 1 で、
  `test_t1259_qsub_env_delivery_probe.py` の 6 件が setup error になった
  (23,308 passed / 68 skipped / 6 error、子 rc=1、受領証は未発行で待ち手は rc=70)。
  setup traceback の Git argv は既報と同一で、
  `git -C <wave worktree> ls-files --others --exclude-standard -z` の 30.0 秒 TimeoutExpired。
  同 tip・同 file の単独再走 (`run_tests.py`、996322.nqsv) は **51 passed / 16.67 秒、job Elapse 22S、
  rc=0** で非再現。wave の変更は docs のみで、当該 fixture・probe・Git 呼出しは変更していない。
  **本 wave は既報が「分離していない」と書いた遅延の大きさ自体を実測した。** 同じ worktree で
  同 argv を 3 連続実行した wall は **34.60 / 24.96 / 15.90 秒**で、30 秒 timeout を跨いでいる
  (実行時の load average 68.35〜88.49)。作業ツリーは tracked 24,684 件 / 約 690 MB である。
  これは走査時間の分布を与えるだけで、**I/O 要因の分離ではない**。新規 worktree の cold cache と
  login node 負荷が交絡しており、どちらがどれだけ効くかは測っていない。
  恒久対応は既報のまま変えない — timeout 拡大・fixture の stub 化・除外・汎用 gate の新設は行わず、
  `DW-O18` に従って単独非再現を確認して受入を再走した。記録は
  `output/insights/2026-09-14/repo-bloat-audit/README.md` §7。
