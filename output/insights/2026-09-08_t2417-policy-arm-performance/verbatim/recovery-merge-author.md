## 総括

実装済み・未実走です。競合3ファイルだけを解決し、git add / merge / commit、docs編集、新規測定は行っていません。

変更ファイル:

- [acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2417-recovery-author/orchestrator/tests/acceptance_duration_ledger.json:22350)
  - oursの101 nodeとincomingの90 nodeを既存値のまま統合。
  - 同一keyの異値は0件、重複keyも0件。
  - 実体22346 nodeに `nodeid_count` を一致。
- [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2417-recovery-author/orchestrator/tests/test_ccbench_spawn_sites.py:929)
  - 両親のspawn分類を保持。
  - 合成済みdriverの実呼出し行、trace build 3853行とperformance build 4246行へ2組のpinを更新。
  - 静的scannerでも両sinkとの完全一致を確認。
- [test_t2187_adaptive_const_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2417-recovery-author/orchestrator/tests/test_t2187_adaptive_const_probe.py:23)
  - T-2417の `policy_analysis` importと全27追加testを保持。
  - main側cohort2の `PREREGISTERED_SEEDS` importと全12追加testを保持。
  - 現在の123 test関数は両親の完全な和集合。

静的に、T-2417のexact 18-block解析、未認証表示、headline不適格、既存certification経路からの拒否と、main側cohort2限定認証経路の共存を確認しました。既存期待値の反転、緩和、skip、削除はありません。

実走対象は以下を `tools/run_tests.py` 経由で投入しましたが、`qstat -Q` preflight rc=1でdispatchが停止し、`child_started=false`でした。

- `orchestrator/tests/test_ccbench_spawn_sites.py` 全体
- `orchestrator/tests/test_t2187_adaptive_const_probe.py` 全体
- `test_update_acceptance_duration_ledger.py::test_g7e_checked_in_ledger_has_valid_schema_and_finite_durations`

従って緑のnodeidはなく、実18 block解析も未実走です。生成されたdispatch一時物は除去済みです。

所有外の静的波及先は、production driver/PBS/T-2417 submitter、policy performance/cohort2解析module、`test_backoff_policy_performance_analysis.py`、`test_backoff_counterfactual_cohort2_analysis.py`、`test_hooks.py`、`test_plot_dynamic_backoff.py`、共有fixtureの `orchestrator/tests/conftest.py`、台帳consumer/meta-testの `test_acceptance_schedule_order.py` と `test_update_acceptance_duration_ledger.py` です。いずれも未編集です。

残る所見は、親による統合後の焦点走、全受入走、実18 block解析が必要なことだけです。競合marker、unmerged index、MERGE_HEAD、`diff --check`違反は残っていません。