実装を完了し、コードとテストの 5 ファイルだけに未コミット差分を残しました。docs、予約 policy JSON、共有 policy は変更していません。

変更前は、job が well-formed な 3 行を出した後の mismatch/producer failure を受理し、submit と制御 protocol は cap 合計 29100 を保つ compensated drift を受理していました。既存の欠損・member/gap・Wmax・walltime 等の拒否は維持し、個別値と producer status の拒否だけを純増しました。

## 総括

(a) 編集箇所

- [t126_qualification.sh](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:453)
  - command substitution＋status 検査
  - submit 列挙範囲の 8 key 個別比較
  - 成功後のみ 3 値出力
  - 配列長 guard、既存代入を維持し mapping assert を追加
- [submit_t126_qualification.sh](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:187)
  - コメント更新
  - 予約 producer status の明示検査
  - prologue/attestation/finalize 個別比較を純増
- [contract.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/qualification/contract.py:225)
  - `validate_protocol` に timing 3 cap の個別比較を純増
- [test_t126_pegasus_tools.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:790)
  - commit 前 policy 変異、scratch 1 箇所置換、regular Python wrapper、late-failure・downstream marker fixture
  - 8 key 静的 assert と subprocess 境界テスト
- [test_t126_qualification_contract.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_qualification_contract.py:48)
  - canonical 正例、3 cap 個別 assert、3 compensated-drift 負例

(b) 新設・更新テスト

新設:

- `test_submit_rejects_compensating_cap_drift_before_scheduler_calls`
- `test_submit_reservation_reader_rejects_python_failure_after_complete_output`
- `test_job_reservation_policy_accepts_exact_point_and_rejects_each_frozen_value`
- `test_job_reservation_reader_rejects_python_failure_after_complete_output`
- `test_protocol_rejects_each_compensating_timing_cap_drift`

更新:

- `test_reservation_policy_and_job_headers_freeze_wmax_and_walltime`
- `test_protocol_freezes_observational_envelope_and_wmax`

(c) 実行結果

静的検査は成功:

- `git diff --check`
- 両 shell の `bash -n`
- 変更 Python 3 ファイルの `python3 -m py_compile`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

以下の焦点 nodeid を `tools/run_tests.py` で2回 dispatch しましたが、両方とも `qstat -Q preflight rc=1`、runner rc=16 で投入前停止しました。したがって pytest 実行数は 0 で、緑は主張しません。

- 上記新設・更新テスト全 nodeid
- `test_shell_scripts_pass_bash_syntax`
- `test_fr3_mutation_node_registry_is_exact_and_complete`

(d) 赤・停止の内訳

- テスト赤: 0 件（テスト自体が未実行）
- dispatch infrastructure failure: 2 件、いずれも `qstat -Q` preflight
- 親 docs 未 land に起因して許容する赤 finding: 事前指定どおり 0 件
- 静的 checker の回帰: 0 件

(e) 波及可能性

- `_attempt` と `_submit_fixture` の多数の既存 caller。optional 引数未指定時は従来 bytes・挙動を維持。
- `_run_bound_job_terminal` の既存 caller。既定の binding 後停止は変更なし。
- submit 正例 `test_fake_qsub_qstat_exact_visibility_and_durable_receipt` と既存 submit fixture 群。
- script bytes を動的 identity/hash 化する M11b、identity、collector、spooled-script consumer tests。
- `validate_protocol` を経由する submission、driver、collector/public consumer。
- scope 外として残した予約 policy consumer の意味論穴、重複 key 非対称、他 7 status 切断、orphan term-grace には変更なし。

(f) 未了・未確認

- 焦点 pytest、test file 全体、P-S 正例、変異 matrix、計算ノード全走は未実行。
- 親による新 D・worklog・変異台帳、段 6 レビュー、commit が必要。
- `git add`・commit・push は実行していません。