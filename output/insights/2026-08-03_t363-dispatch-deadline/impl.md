実装を完了しました。変更は指定された 2 ファイルだけで、commit・git 状態変更・docs 編集はしていません。

### 1. 変更 hunk

- [tools/pegasus/dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1215)
  - `:1215-1224`: RUN 初観測時の同じ `now` を `run_observed_at` とし、qstat `rc == 0` の場合だけ `walltime_s + overall_grace_s` を張り直す。
  - `not run_seen` により張り直しは一度だけ。
  - `run_seen`、`queue_wait_s`、receipt schema は不変。

- [orchestrator/tests/test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:40)
  - `:40-219`: `_Scheduler` に既定空文字の `qstat_error_stdout` を追加。`_dispatch` に既定値不変の poll、queue timeout、accounting grace、nonce 注入点を追加。
  - `:1350-1443`: T1・T2・T3 の回帰テスト 3 本を追加。

### 2. 受理・拒否挙動の差分

変更前:

- RUN の qstat rc に関係なく `run_seen` と queue-wait receipt を記録。
- deadline は常に `submitted_at + walltime + grace`。
- 待ち時間を挟んだ正常 RUN も、submit 起点 deadline で早期拒否され得る。

変更後:

- 成功した qstat による最初の RUN 観測だけ、deadline を `run_observed_at + walltime + grace` へ変更。
- rc≠0 の RUN stdout は、従来どおり `run_seen=True`・queue-wait 記録となるが、deadline は延長しない。
- pre-RUN の実効上界、UNKNOWN の扱い、qdel、NaN/inf を含む入力受理、receipt schema は変更なし。
- 受理集合の変更は「成功した RUN 観測後、観測時点から実行予算内に終わるジョブ」の早期拒否解消だけ。

brief と plan v2 には、qstat rc の束縛、観測時刻の意味、変異実行形などに差異があります。指示どおり plan v2 を優先しました。

### 3. 新規テストの時刻展開

T1 `test_queue_wait_does_not_consume_observed_run_budget`:

- 初期 deadline=`t=3`。
- `t=0 QUE`
- `t=1 QUE`
- `t=2 RUN` → 修正後 deadline=`2+2+1=5`
- `t=3 RUN`
- `t=4 DONE` → rc=0、qdel なし、queue wait=2秒
- 旧 HEAD は `t=3` で overall-timeout・qdel となり、rc と qdel assertion が赤。

T2 `test_post_run_unknown_state_uses_first_observation_deadline`:

- 初期 deadline=`t=3`。
- `t=0 QUE`
- `t=1 RUN` → deadline=`4`
- `t=2 RUN` → 二度目なので張り直さない
- `t=3 UNKNOWN`
- `t=4 UNKNOWN` → overall-timeout・qdel
- 旧 HEAD は `t=3` で timeout するため履歴 `[0..4]` の assertion が赤。RUN ごとに張り直す変異では deadline=`5` となるため同様に赤。

T3 `test_nonzero_qstat_run_stdout_does_not_restart_deadline`:

- 同じ node 内の rc==0 対照:
  - `t=0 QUE`
  - `t=1 RUN` → deadline=`4`
  - `t=2,3,4 UNKNOWN`、`t=4` で timeout
  - 旧 HEAD は `t=3` で timeout するため対照 assertion が赤。
- rc≠0 注入:
  - 初期 deadline=`3`
  - `t=0 QUE`
  - `t=1 rc=153 / stdout RUN` →表示は QSTAT_ERROR。`run_seen` と queue wait=1秒は記録するが deadline は延長しない
  - `t=2 UNKNOWN`
  - `t=3 UNKNOWN` → overall-timeout・qdel
- 修正後は両側が成立。rc gate を恒真化すると非ゼロ側が `t=4` まで延びるため赤。

### 4. 影響し得る既存テスト

- `test_overall_walltime_plus_grace_bound_qdels_running_job`
  - 最初の RUN が `t=0` なので、旧・新 deadline はともに `t=1`。既存期待は不変。
- `test_unknown_scheduler_state_remains_bounded_by_overall_timeout`
  - RUN 分岐が一度も発火せず、従来どおり `t=1` で timeout。
- `test_dispatch_state_machine_returns_child_rc_after_accounting`
  - queue wait と state history の計算は同じ `now` を使用し、receipt の期待値は不変。
- `test_qstat_error_during_poll_does_not_end_or_latch_job`
  - rc≠0 状態の扱いは変更せず、後続の成功 RUN で一度だけ張り直す。既定予算内で従来どおり終了する。
- その他の既定 walltime を使う fake scheduler テストは、旧 deadline より十分早く DONE へ到達するため結果不変。

### 5. Meta-test・所有外への波及

テスト名、当該ファイルの test 数、追加 node 数を固定する meta-test は `rg` による静的検索では見つかりませんでした。`test_pytest_collection_config.py` は収集範囲を固定しますが、個別 node 数・名称は固定していません。

波及可能性:

- production caller の `tools/run_tests.py` と CLI dispatch は、queue 待ち後の成功 RUN で利用可能時間が延びる。
- receipt consumer は schema・field・`run_seen` 相当の意味が不変なので改修不要。
- module-local の `_Scheduler`／`_dispatch` は既定引数が従来値と同一。既存呼び出しの挙動は不変。
- active job の qdel、UNKNOWN 保護、timeout 入力検証には触れていません。

### 6. 検査

実行済み:

- `git diff --check`
- 対象 2 ファイルの `python3 -m py_compile`
- AST parse、新規 test 関数 3 本の存在確認
- 変更ファイルが指定 2 ファイルだけであることの確認

未実行:

- **pytest は全走・部分走とも実行していません。**
- `tools/run_tests.py`、qsub、qdel、qstat、変異実走も実行していません。
- したがって実測の「緑」は主張せず、上記は fake clock/state machine の静的追跡結果です。

## 総括

- 成功した RUN 初観測時だけ、観測時刻から実行予算を一度張り直しました。
- T1・T2・T3 で主回帰、一度限りの上界、rc≠0 RUN の非延長を固定しました。
- pytest はログインノード制約により未実行で、親による計算ノード実測が必要です。