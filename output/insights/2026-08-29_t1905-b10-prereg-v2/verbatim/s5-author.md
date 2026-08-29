## 総括

- 受理挙動: v4 の `{constant, symmetric-modulo}` × μ 6点、Holm 3族、residual 12 cell、上限 exact 1.0、完全一致する `registration_rules` と閉じた provenance のみ受理します。runtime 最大偏差は `0.5616942857142844%` です。
- 拒否挙動: v3、binary を含む grid、上限 0.5/2.0、registration rule の値変異、residual 欠落、偏差が境界 1.0% 以上の cell、probe `/v1`、driver API の code 2 を拒否します。dormant C++ code 2 は維持しています。
- 変更 file: [b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py)、[test_b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py) の2 fileのみ。
- 変更箇所数: 機械差分 85 hunks。driver 41、test 44。`+377/-138` 行。
- 新設 test: `test_v4_spec_including_binary_shape_is_rejected`
- 新設 test: `test_physical_residual_limit_other_than_exact_one_is_rejected`
- 新設 test: `test_registration_rules_values_are_checked_exactly`
- 新設 test: `test_schema_v3_document_is_rejected_after_v4_positive_control`
- 新設 test: `test_physical_residual_deviation_exactly_at_the_limit_is_rejected`
- 実走した nodeidと結果: なし。`tools/run_tests.py` に重点範囲と meta-test 5 nodeidを投入しましたが、`qstat -Q` rc=1、`child_started=false`、dispatcher rc=16で実行前に停止しました。緑とは申告しません。
- 非pytest診断: canonical v4 parse、12-cell runtime検査、全負例、probe v2正例/v1負例、15-point block算術を直接診断済み。AST parse 2 fileと `git diff --check` も成功。
- 未実走: 対象 test file全体、および ledger coverage、certified-writer inventory、process launch inventory、coder authority inventory、official-perf inventoryの各 meta-test。
- 波及可能性: CLIを呼ぶ Pegasus submit/job scripts、report/provenance consumer、`test_condition_meaning_gate.py`、production AST inventory群。共有 fixture 4種は追随済みです。`acceptance_duration_ledger.json` には改名前nodeidが残りますが、禁止どおり編集していません。
- Git操作: commit、add、stash、branch操作は行っていません。