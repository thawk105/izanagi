---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-t2105-freeze-successor
seq: 3
---

## 再発

### F333

- **再発: 2026-09-03** — [T-2105] wave の段 6 で、`nohup setsid` で detach した
  `tools/mutation_harness.py` が、親の Claude Code process の終了に巻き込まれて SIGKILL された。
  **F333 とその 2026-08-23 再発が記録していない帰結が 3 つ同時に残った。**
  (a) 変異注入後のソースが復元されず、`orchestrator/campaign/s8b_ratified_freeze.py` に M01 の
  置換が残ったまま作業ツリーが dirty になった (harness の signal 復元は SIGKILL を捕捉できない)。
  (b) `output/pegasus-dispatch/orphan-hold.json` と `orphan-holds/unknown-*.json` の 2 ファイルが
  武装し、以後この worktree からの dispatch を全停止した。
  (c) `--attempt-out` sidecar の最後の attempt が `state=started` のまま残り、
  **`--resume` が「finished でない attempt からは再開不能」で fail-closed 拒否した** —
  すなわち SIGKILL 後は `--resume` による復旧経路そのものが使えない。
  復旧は harness が印字する順序どおりに行った (qstat で対象 job 名の不在を確認 →
  `git checkout --` でソース復元 → clean/HEAD 確認 → hold 2 ファイルと orphan-stop sidecar を削除)。
  手動 qdel は F47 ラッチを武装させるため行っていない。
  **孤児化した job 自体は計算ノード側で完走しており**、その stdout から M01 の観測 node
  (`test_approval_commit_with_extra_file_rejected` ちょうど 1 件、他 60 件緑) を回収できた。
  再開時は `--resume` を諦め、中断分を `mutation-probe-INTERRUPTED-*` として erratum に保全したうえで
  新しい `--out` / `--attempt-out` で走らせ直した。
- **再発: 2026-09-03** — 同 wave で、上記復旧の直後に投入した変異走が collection 段で
  `rc=16, collected=0, artifact_error='receipt scheduler_logs.stdout.path がない'` で停止した。
  orphan-hold は残っておらず、原因は queue 混雑である (同時刻の `qstat` で 5 件が QUE)。
  D612 の opt-in 上書き `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600` /
  `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600` を runner script の環境へ export して再投入した
  (`mutation_harness` の `runner_env = os.environ.copy()` により `run_tests.py` へ伝播する)。
  spec 側の `timeout_seconds` / `hang_timeout_seconds` も 5400 秒へ引き上げた。
  **`rc=16` は実装の回帰ではなく基盤側の失敗であり、変異結果として記録してはならない。**
  上書きは効かなかった。runner の環境に `=3600` が入っていることを `env` で実測し、
  `run_tests.py` の main 経路を repo 外 probe で直接通すと
  `dispatch_compute.dispatch` は `queue_wait_timeout_s=3600.0` を受け取る。それでも
  harness 経由の実走は 902 秒と 904 秒で `DispatchError: queue-wait-timeout` に落ちた。
  **原因は未特定である。** 回避策は逐次リトライで、5 回目の投入が完走した。
  なお `--runner-mode local` は PEGASUS_LOGIN で禁止され、runner argv の先頭は harness と
  同じ Python 実行体に束縛されるため `env VAR=... python3 ...` の前置もできない。
  harness は**完全な clean tree を要求する** — docs の untracked fragment 2 件だけでも停止した。
