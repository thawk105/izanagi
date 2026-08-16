## 総括

指定 3 件を順番どおり修正しました。docs・凍結記録・評価器は編集せず、commit／`git add` も行っていません。

- C11 field path を次のように修正しました（[契約 JSON](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1184-prereg-contract-revision/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:420)）。

  - `main.generation_cap` → `main.args.max_generations`
  - `run_trial.generation_cap` → `run_trial.generations`
  - `_run_workload.generation_cap` → `_run_workload.generations`
  - `_run_workload.critic_feedback_consumer` → `_run_workload.apply_critic_feedback`
  - `MAX_APPROVED_GENERATIONS` は実在するため維持

  `main` の `_validate_generation_budget(args.max_generations)`、両関数の keyword-only `generations`、`_run_workload` 内の `apply_critic_feedback(...)` をソースで確認しました。`reachable_from` の関数・呼び出し名もすべて実在するため変更していません。

- 条件 11 以外の `.py` 証拠を全走査し、次の未実在識別子を確認しました。指示どおり修正していません。

  - C01: 0 件
  - C02: `manifest.cells[*].arm`、`run_start.arm`、`terminal_report.arm`、`campaign_identity.arm`、`proposal_path.arm`、`invocation_id.arm`、`bind_trial_arm`、`accept_trial`、`verify_arm_binding`
  - C03: `registry.prereg_content_commit`、`registry.prereg_effective_commit`、`registry.history_prefix_sha256`、`accept_trial`
  - C04: `run_trial.crash_handler.*`、`mark_experiment_indeterminate`、`trial_lifecycle.started_once`、`trial_lifecycle.restart_forbidden`、`forbid_trial_restart`、`reject_started_trial`
  - C05: `s8c_schedule.py` 自体が未実在。記載された `regenerate`、`verify_exact_schedule_bytes`、`verify_shared_search_space_and_initial_state`、`verify_schedule`、`consume_schedule` も未実在
  - C06: `s8c_budget.py` 自体と、その全 field path、`reserve_all_cells`、`settle`、`symmetric_indeterminate` が未実在
  - C07: `s8c_result_judge.py` 自体と、その全 field path、`accept_trial`、`verify_floor_bytes`、`judge`、`publish_result_table` が未実在
  - C08: content/effective commit を持つ全 field path、`accept_trial`、exact-parent verifier が未実在
  - C09: `run_trial.pre_publish_layer3_verification`、`accept_trial.build_reports[*].layer3_chain`、`accept_trial.no_build.certifying`、registry 側の `accept_trial`／`assert_campaign_layer3_chain`
  - C10: `role_event.*`、`provider.payload_sha256`、`provider.envelope_sha256`、`proposal.*`、`campaign_wal.*`、`layer3.source_refs`、`verify_s8c_cross_binding`、`read_and_verify_bytes`、`accept_trial.cross_binding_receipt_sha256`
  - C12: `run_trial.env_contract`、`run_trial.calibration_receipt`、`run_trial.allocation_receipt`、`run_trial.single_process`、`run_trial.allow_resume`、p3 側の `env_contract.lookup`／`execution_guard.attest_and_build_receipt`／`reservation.single_process_required`、および reservation 側の `single_process_required`。現行名は `is_reservation_required`

- C08 境界テストへ assert を追加しました（[predicates test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1184-prereg-contract-revision/orchestrator/tests/test_s8c_preregistration_predicates.py:700)）。

  - `C` の親集合が exact `{P}` である文言を要求
  - ancestry は `C` から measurement HEAD への検査だけであることを要求
  - `ancestry` の出現を 1 件に固定し、`P`–`C` 間を祖先関係で代用する改訂を検出

- hash literal を独立実装から更新しました（[core test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1184-prereg-contract-revision/orchestrator/tests/test_s8c_preregistration_core.py:734)）。

  - current: `a33e04a7…bf4ae` → `983f5d7c…adb89`
  - NUL: `77cd405f…15735` → `8b8aafce…87fdc`
  - CR: `43776aac…a8e50` → `818001ee…fa19b`
  - LF: `8218499e…da8e` → `0773bb62…878da`

  4 値とも `_independent_evidence_contract_sha256` から取得し、`M.evidence_contract_sha256` と完全一致しました。指定 3 テストファイル内に他の live-contract literal pin はありません。g1 歴史値は変更していません。

テストは次の nodeid を `tools/run_tests.py` へ投入しました。

- `test_evidence_contract_hash_accepts_non_path_controls`（3 parameter）
- `test_current_evidence_contract_hash_is_frozen`
- `test_c03_c08_contract_uses_two_stage_binding_without_self_reference`

ただし `qstat -Q preflight rc=1` により wrapper が `rc=16` で終了し、pytest 本体は実走できませんでした。緑とは申告しません。静的検査は `git diff --check`、JSON parse、`check_codex_agents.py`、`check_docs.py` がすべて `rc=0` です。

波及可能性は、契約 hash 変更による g3 凍結記録との既知不一致、親による g3 再生成、材料レポート／試行台帳に表示される C11 証拠 path の変更です。評価器・`SATISFIABLE_CONDITION_IDS`・受理集合は変えておらず、C08 の変更もテストだけです。