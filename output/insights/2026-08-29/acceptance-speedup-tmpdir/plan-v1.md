## 総括

plan は条件付きで成立する。login 形では、canonical main repo ごとに固定された Lustre 上の TMPDIR を使う。ただし毎走固有 root は、TMPDIR 直下の lock identity を分断して正しさを緩めるため不採用とする (`orchestrator/campaign/patchharness.py:113-130`, `tools/mutation_harness.py:2869-2889`)。
設定場所は `tools/run_tests.py` ではなく `orchestrator/tests/conftest.py` の `pytest_configure` とする。runner 編集 wave は tested-main blob 束縛により land 不能だからである (`docs/decisions.md:31681-31697`, `docs/decisions.md:38624-38641`, `rulings-verbatim.md:577-578`)。
compute/dispatch 形は変更しない。compute の `/tmp` は既測定で十分速く、login の TMPDIR は dispatcher allowlist を通らない (`orchestrator/tests/README.md:15-23`, `tools/pegasus/dispatch_compute.py:114-132`, `tools/pegasus/dispatch_compute.py:3080-3091`)。
既存 fstype ガードは Lustre を許す。拒否するのは tmpfs 族だけであり、述語を弱める必要はない (`orchestrator/tests/test_real_repo_serialization.py:445-524`)。
実装採否は同一 tip の `/tmp` 対 Lustre を 3 pair、各 arm 3 走で測り、中央値 10% 未満なら land しない (`docs/decisions.md:15594-15607`, `rulings-verbatim.md:630-642`)。

## 問い 1〜8 への回答

### 問い 1. 消費者の完全な棚卸し

#### 参照関係

依存関係は次の順である。

`TMPDIR` → CPython `tempfile.gettempdir()` の cache → pytest の既定 basetemp → `tmp_path_factory` → `tmp_path` → 各テストがそこから作る repo、WAL、lock、subprocess cwd。

この関係は現行ガード自身も明記している (`orchestrator/tests/test_real_repo_serialization.py:527-540`, `orchestrator/tests/test_real_repo_serialization.py:5246-5251`)。`--basetemp` だけは pytest root を直接上書きし、TMPDIR ガードの射程外である (`orchestrator/tests/README.md:32-36`, `tools/run_tests.py:456-479`, `tools/run_tests.py:550-572`)。

静的棚卸しでは、明示的な `tmp_path` または `tmp_path_factory` fixture sink は 211 file、6507 function/fixture だった。以下の `start-end(count)` は各 file 内の最初と最後の sink 定義、および定義数である。

<details>
<summary>tmp_path / tmp_path_factory の file-level 完全表</summary>

```text
s8b_v2_freeze_fixture.py:348-348(1)
test_acceptance_nproc_study.py:160-2666(45)
test_acceptance_schedule_order.py:354-1042(5)
test_artifact_admission.py:377-2155(58)
test_attempt_registry_core_equivalence.py:370-615(5)
test_audit_dangling_commits.py:50-3659(82)
test_autonomous_trial_completeness.py:661-5605(161)
test_b10_backoff_shape_sweep.py:53-1496(27)
test_backoff_consumers.py:64-414(13)
test_backoff_extended_sweep.py:143-668(6)
test_backoff_extended_sweep_report.py:232-232(1)
test_backoff_overthrottle.py:64-64(1)
test_backoff_profile_pegasus.py:213-1057(27)
test_backoff_requested_us.py:127-1004(11)
test_backoff_sweep.py:65-65(1)
test_bench_first_real_wal.py:76-376(6)
test_build_admission.py:135-598(12)
test_buildcache_v2.py:196-4295(117)
test_calibration_freeze_authority_contract.py:75-2146(81)
test_calibrator_certify.py:369-1440(33)
test_campaign.py:236-12533(18)
test_campaign_claim.py:62-475(22)
test_campaign_lock_wal_consumers.py:48-261(10)
test_ccbench_spawn_sites.py:521-521(1)
test_check_acceptance_reds.py:42-3210(97)
test_check_ai_provenance.py:648-7107(124)
test_check_branch_landed.py:63-1462(53)
test_check_branch_rescue.py:64-1619(52)
test_check_codex_output.py:25-162(13)
test_check_docs.py:4683-4966(9)
test_check_subprocess_bytecode_guard.py:36-203(6)
test_check_trace0_preprocess_identity.py:111-1287(83)
test_check_wave_startup.py:45-1852(98)
test_check_worktree_occupancy.py:92-1740(62)
test_claude_session_ledger.py:157-2024(44)
test_claude_transport.py:255-2234(23)
test_codex_hooks.py:525-801(17)
test_codex_jsonl_line_split.py:43-260(8)
test_codex_reasoning_ab.py:464-16146(337)
test_codex_role_runtime.py:590-647(3)
test_codex_worker_launch.py:480-7432(146)
test_codex_worker_launch_budget.py:440-967(18)
test_codex_worker_ledger.py:353-2048(69)
test_collect_wave_usage.py:63-724(28)
test_condition_meaning_gate.py:43-630(21)
test_dev_wave_cleanup.py:57-1338(42)
test_dev_wave_land.py:9162-10117(5)
test_dev_wave_launch_authority.py:107-1005(32)
test_dev_wave_submodule_init.py:71-174(6)
test_dev_wave_wait.py:946-9917(37)
test_durable_root.py:30-111(7)
test_env_attestation.py:38-1330(42)
test_env_contract.py:817-1086(7)
test_env_contract_activation.py:382-3094(40)
test_flaky_test_holds_contract.py:128-722(10)
test_floor_submit_receipt.py:73-178(6)
test_fold_gate_nodes_contract.py:616-616(1)
test_growth_test_holds_contract.py:1721-2428(9)
test_holdout_observation.py:916-1073(5)
test_hooks.py:3312-4224(21)
test_layer3_admission_diagnosis.py:104-493(5)
test_layer3_report.py:115-3316(84)
test_login_headroom.py:51-1584(49)
test_migrate_output_gzip.py:37-443(13)
test_mocc_g2_discriminator.py:118-526(12)
test_mocc_g2_repro_ledger.py:247-600(19)
test_mocc_trace_job_contract.py:91-3831(72)
test_mocc_trace_pair.py:122-1418(40)
test_mutation_fanout.py:115-998(17)
test_mutation_fanout_contract.py:122-773(11)
test_mutation_harness.py:42-2593(2)
test_mutation_worktree.py:220-1269(33)
test_p3_autonomous_workload_trial.py:610-10219(161)
test_p3_b4_analysis_path.py:596-637(2)
test_p3_b4_analysis_prereg_consumer.py:442-442(1)
test_p3_b4_launcher.py:76-879(22)
test_p3_b4_prerun_issuer.py:171-969(21)
test_p3_b4_wiring_probe.py:256-1117(13)
test_p3_exploration_namespace.py:201-1527(12)
test_p3_s4_loop.py:1144-4841(30)
test_p3_s4_loop_sort.py:869-1155(7)
test_p3_s4_loop_trigger_gating.py:709-3058(15)
test_paper_story_a1_job_contract.py:61-2213(59)
test_paper_story_a1_paired.py:41-3019(46)
test_paper_story_a2_certification.py:70-2650(66)
test_paper_story_a2_job_contract.py:23-975(20)
test_pegasus_calibration_workload.py:51-51(1)
test_pegasus_dispatch_compute.py:263-6776(162)
test_pegasus_floor_scoping.py:123-187(4)
test_pegasus_floor_tools.py:206-4109(87)
test_pegasus_thirdparty_fetch.py:85-773(8)
test_pegasus_tools.py:193-1384(37)
test_profiler_directive.py:43-618(15)
test_pytest_collection_config.py:211-1112(6)
test_pytest_failure_digest.py:294-953(4)
test_real_repo_serialization.py:716-3985(10)
test_reflux_formal_consumer.py:211-211(1)
test_reflux_origin_artifacts.py:35-159(7)
test_reflux_origin_binding.py:186-186(1)
test_reflux_origin_client.py:81-557(2)
test_reflux_origin_fixture_builder.py:301-333(2)
test_reflux_origin_ledger.py:394-4293(33)
test_reflux_origin_topology.py:216-216(1)
test_reflux_originless_compatibility.py:156-1135(3)
test_reflux_result_evidence.py:185-338(9)
test_reflux_source_closure.py:95-407(14)
test_resume_gate_acceptance_boundary.py:273-273(1)
test_role_session_isolation.py:81-715(30)
test_ruleops.py:151-3247(89)
test_run_tests_preflight.py:81-2592(49)
test_run_tests_shards.py:289-1426(19)
test_run_tests_task_run.py:143-1008(20)
test_run_tests_testops_observation.py:48-1071(20)
test_s1_direct_comparison.py:177-1733(47)
test_s1_known_axes_freeze.py:397-650(6)
test_s1_measurement_freeze.py:65-263(8)
test_s1_report.py:134-585(19)
test_s1_verify_extime_calibration.py:207-207(1)
test_s6_proposal_rounds.py:314-360(4)
test_s6_sort_sweep.py:710-710(1)
test_s8a_trigger_sweep.py:919-919(1)
test_s8b_attempt_registry.py:267-1701(32)
test_s8b_binary_admission.py:61-350(17)
test_s8b_binding_driftguards.py:230-581(6)
test_s8b_budget.py:50-239(16)
test_s8b_budget_approval_preflight.py:135-543(16)
test_s8b_compiler_input.py:55-418(13)
test_s8b_expected_materialization.py:34-643(15)
test_s8b_floor_attempt_launcher.py:510-510(1)
test_s8b_floor_campaign.py:631-12899(246)
test_s8b_floor_stats.py:909-936(2)
test_s8b_freeze_io.py:42-242(11)
test_s8b_holdout_admission.py:158-3622(111)
test_s8b_holdout_freeze.py:258-2313(66)
test_s8b_materialization.py:508-508(1)
test_s8b_oracle_artifacts.py:61-477(9)
test_s8b_oracle_driver.py:512-6384(111)
test_s8b_oracle_judge.py:735-735(1)
test_s8b_oracle_manifest.py:208-1736(46)
test_s8b_oracle_n_pilot.py:208-1898(63)
test_s8b_oracle_report.py:204-5463(186)
test_s8b_predicate_build_proof.py:37-240(4)
test_s8b_prediction_runner.py:146-1790(54)
test_s8b_protocol_builder.py:242-1803(46)
test_s8b_ratified_freeze.py:156-2390(51)
test_s8b_ratified_verify.py:211-2515(84)
test_s8b_scheduler_accounting.py:45-559(18)
test_s8b_selector_freeze.py:313-754(12)
test_s8b_selector_input.py:148-166(2)
test_s8b_verdict.py:420-1300(19)
test_s8c_acceptance_receipt.py:47-332(14)
test_s8c_acceptance_receipt_v2.py:139-856(19)
test_s8c_arm_inputs.py:23-173(9)
test_s8c_budget.py:59-173(6)
test_s8c_preregistration_core.py:136-3332(66)
test_s8c_preregistration_invariant.py:191-575(3)
test_s8c_preregistration_predicates.py:123-3952(86)
test_s8c_result_judge.py:205-1936(41)
test_s8c_schedule.py:353-353(1)
test_scan_env_coincidence.py:47-252(7)
test_schema_v2.py:479-518(2)
test_screening_driver.py:143-561(17)
test_silo_ladder_rung1.py:237-237(1)
test_silo_ladder_rung1_driver.py:729-2559(24)
test_sort_swo_dependency_material.py:35-329(11)
test_sort_swo_oracle.py:206-2344(34)
test_spool_fold.py:217-4137(158)
test_ss2pl_lock_study.py:235-1256(20)
test_t080_freeze_migration.py:1516-2065(10)
test_t126_pegasus_tools.py:848-6359(113)
test_t126_qualification_artifacts.py:56-732(20)
test_t126_qualification_driver.py:146-868(19)
test_t1286_commit_receipt.py:89-610(14)
test_t139_blobref_digest_binding.py:42-42(1)
test_t139_blobref_git_trust.py:24-289(6)
test_t139_preregistration_binding.py:705-785(3)
test_t139_r4_env_probe.py:77-1174(17)
test_t139_stress_check_simulation.py:184-615(9)
test_t139_submission_path.py:27-338(9)
test_t1403_walltime_sigterm_probe.py:74-167(3)
test_t1416_backoff_compiler_binding.py:241-320(2)
test_t1434_t1222_science_slice.py:49-374(11)
test_t152_write_intent_coverage.py:208-794(12)
test_t189_oracle_wiring_slice.py:145-414(14)
test_t189_task_catalog.py:210-707(30)
test_t316_sandbox_probe.py:365-1060(24)
test_t338_submission_gate_unit1.py:57-359(2)
test_t338_submission_gate_unit2.py:19-288(4)
test_t338_submission_gate_unit3.py:181-1116(21)
test_t338_submission_gate_unit4.py:83-518(2)
test_t338_submission_gate_unit5.py:385-560(6)
test_t419_probe_causality.py:1671-1671(1)
test_t503_restore_durability_probe.py:67-505(27)
test_t671_source_binding.py:119-651(13)
test_t674_qualification_contract_lanes.py:35-152(5)
test_t762_ident_wrapper.py:108-245(5)
test_t793_approval_guard.py:113-279(9)
test_t793_publication_ledger.py:31-331(14)
test_t810_budget.py:67-465(21)
test_t810_coordinator.py:65-1300(39)
test_t810_harness_schema.py:307-307(1)
test_t810_pbs_wrapper.py:64-612(20)
test_t810_preregistration.py:103-308(7)
test_t810_runner_policy.py:39-190(10)
test_t810_validator.py:75-1020(36)
test_task_run_aggregate.py:164-376(7)
test_task_run_generation.py:44-734(10)
test_task_run_ledger.py:51-976(5)
test_trial_registry.py:152-7612(188)
test_update_acceptance_duration_ledger.py:19-677(18)
test_wave_land_window.py:131-1942(62)
```

全 path は `orchestrator/tests/` 配下である。

</details>

`tmp_path_factory` の特に大きい session/module sink は、Masstree build、snapshot、failure-digest である (`orchestrator/tests/test_sort_swo_oracle.py:206-246`, `orchestrator/tests/test_codex_reasoning_ab.py:788-791`, `orchestrator/tests/test_pytest_failure_digest.py:665-710`)。

#### tempfile の直接 sink

`dir=` を与えず実効 TMPDIR に従う production sink は次である。

- calibrator: `orchestrator/calibrator/perf_preflight.py:112`, `orchestrator/calibrator/runner.py:177,637`, `orchestrator/calibrator/tsc.py:88`
- campaign core: `orchestrator/campaign/pipeline.py:549,1193`, `orchestrator/campaign/s1_verify_extime_calibration.py:253,408`, `orchestrator/campaign/s2_verify_calibration.py:109,257,297`, `orchestrator/campaign/s3_lock_coverage.py:82,209,221`, `orchestrator/campaign/s5_permutation_coverage.py:78,243,253`
- sweep/driver: `orchestrator/campaign/backoff_profile.py:844`, `orchestrator/campaign/backoff_requested_us.py:558`, `orchestrator/campaign/b10_backoff_shape_sweep.py:2221,2747`, `orchestrator/campaign/p3_b4_wiring_probe.py:1276-1281`, `orchestrator/campaign/s8a_trigger_coverage.py:171,252-253`, `orchestrator/campaign/s8a_trigger_freq.py:85,145`, `orchestrator/campaign/s8b_prediction_runner.py:1047`
- その他: `orchestrator/campaign/condition_meaning_gate.py:752`, `orchestrator/campaign/mocc_trace_pair_anchor.py:305`, `orchestrator/campaign/paper_story_a1_paired.py:2769`, `orchestrator/campaign/s6_canary_rename.py:235`, `orchestrator/campaign/s8c_preregistration.py:1076`, `orchestrator/campaign/silo_ladder_rung1.py:1888`, `orchestrator/campaign/t152_write_intent_coverage.py:491,750`, `orchestrator/campaign/trial_registry.py:5036`
- leaf: `orchestrator/preregistration/blobref.py:208`, `orchestrator/qualification/submission.py:135`, `orchestrator/submission_gate/_git.py:112`

このほか、テスト自身が `TemporaryDirectory` や `mkdtemp` を直接呼ぶ sink がある。主な集中箇所は `orchestrator/tests/test_acceptance_launcher.py:176-741`, `orchestrator/tests/test_dev_waves_integration.py:373-2175`, `orchestrator/tests/test_check_docs.py:1217-9800`, `orchestrator/tests/test_real_repo_serialization.py:535-5377`, `orchestrator/tests/test_t080_freeze_migration.py:216-2112` である。

`tools/run_tests.py` の task-run sidecar は `dir="/tmp"` を明示しているため、実効 TMPDIR の consumer ではなく、変更後も `/tmp` に残る (`tools/run_tests.py:1180-1185`)。これは「全 unit が一様に移る」という親 P1 の反例である。

#### TMPDIR を直接読む sink

- `patchharness` は TMPDIR 直下へ共有-tree lock と disposable worktree を置く (`orchestrator/campaign/patchharness.py:113-130`, `orchestrator/campaign/patchharness.py:345-378`)。
- floor campaign は未設定を production refusal として扱い、設定済みならその直下へ job-local base を作る (`orchestrator/campaign/s8b_floor_campaign.py:2997-3049`)。
- silo ladder は scratch root として読む (`orchestrator/campaign/silo_ladder_rung1.py:4094-4103`)。
- closed subprocess environment へ TMPDIR を運ぶ allowlist が複数ある (`orchestrator/preregistration/blobref.py:21-30`, `orchestrator/submission_gate/_git.py:20-29`, `orchestrator/campaign/contract_loader_binding.py:28-37`, `orchestrator/campaign/s8c_acceptance_receipt.py:90-99`, `tools/acceptance_shards.py:70-72`)。

#### 指定された 5 file の個別判定

- `real_repo_receipt_memo.py`: consumer。cache path は `run_id + session nonce + HEAD` の hash から `gettempdir()` 直下へ決まり、隣接 lock を `flock` する (`orchestrator/tests/real_repo_receipt_memo.py:131-163`, `orchestrator/tests/real_repo_receipt_memo.py:434-492`)。
- `sort_swo_oracle_receipt_memo.py`: consumer。同型の cache/lock である (`orchestrator/tests/sort_swo_oracle_receipt_memo.py:128-158`, `orchestrator/tests/sort_swo_oracle_receipt_memo.py:394-417`, `orchestrator/tests/sort_swo_oracle_receipt_memo.py:453-509`)。
- `test_s8b_oracle_driver.py`: consumer。module import 時点で TMPDIR、TEMP、TMP、`gettempdir()` を検査し、T-080 base をその配下へ作る (`orchestrator/tests/test_s8b_oracle_driver.py:33-55`, `orchestrator/tests/test_s8b_oracle_driver.py:890-927`)。`mkdtemp` at `:2533` は `dir=tmp_path` なので間接 consumer である (`orchestrator/tests/test_s8b_oracle_driver.py:2531-2545`)。
- `tools/mutation_worktree.py`: consumer ではない。scratch は必須 `--scratch-root` から決まり (`tools/mutation_worktree.py:286-305`, `tools/mutation_worktree.py:1118-1133`)、wrapper lock は `--out` の sibling である (`tools/mutation_worktree.py:192-219`)。親 brief の列挙はこの点で誤りである。ただし child の `tools/mutation_harness.py` は `gettempdir()` 直下に repo-keyed lock を置く真の consumer である (`tools/mutation_harness.py:2869-2889`)。
- `test_real_repo_serialization.py`: consumer。直接の `gettempdir`、`TemporaryDirectory`、`mkdtemp` と fstype guard を持つ (`orchestrator/tests/test_real_repo_serialization.py:527-540`, `orchestrator/tests/test_real_repo_serialization.py:795-942`, `orchestrator/tests/test_real_repo_serialization.py:4710`, `orchestrator/tests/test_real_repo_serialization.py:5170`, `orchestrator/tests/test_real_repo_serialization.py:5377`)。ただし real-repo 排他 lock は TMPDIR でなく固定 `/tmp` であり移動しない (`orchestrator/tests/conftest.py:918-924`)。

### 問い 2. lock の到達範囲

#### (a) 壊れる、または緩むもの

選定案ではゼロでなければならない。

ただし TMPDIR を「毎走固有 Lustre directory」にすると、次が壊れる。

- `patchharness._tree_lock()` は同じ submodule realpath を同じ TMPDIR の lock path に写している。TMPDIR が毎走異なると同一 host の二つの session さえ別 lock になり、apply/build/revert ABA 防壁が消える (`orchestrator/campaign/patchharness.py:113-130`)。
- mutation harness も同じ repo path を TMPDIR 内の一つの lock へ写す。毎走 root なら同じ repo を並行変異できてしまう (`tools/mutation_harness.py:2869-2889`)。

したがって stable root が作れない、または Lustre 上で同じ path の `flock` が同一 host 内でも相互排他にならない場合は、その時点で停止する。unique fallback は許さない。

#### (b) 強くなるもの

- `patchharness` は「全 session 共有の単一 tree」を守る lock なので、同じ shared worktree を別 host から触る場合まで排他が届くのは契約を強める方向である (`orchestrator/campaign/patchharness.py:120-127`)。
- mutation harness も同じ repo への別 host mutation を拒めるようになり、意図する診断と一致する (`tools/mutation_harness.py:2874-2889`)。
- 二つの memo は run/session/HEAD が同じ cache file を別 host から読む場合に、writer/read の cache protocol まで lock で閉じられる。cache 異常は resolver fallback でなく fail-closed である (`orchestrator/tests/real_repo_receipt_memo.py:9-17`, `orchestrator/tests/real_repo_receipt_memo.py:546-578`, `orchestrator/tests/sort_swo_oracle_receipt_memo.py:128-158`)。

Lustre mount が `localflock` 相当なら cluster-wide 強化は成立しないが、現行の「別 host へ届かない」より緩くはならない。段 4 前に二 host probe で確認する。

#### (c) 変わらないもの

- real-repo P/S lock は `_REAL_REPO_LOCK_DIRECTORY = /tmp` のままなので node-local のままである (`orchestrator/tests/conftest.py:918-924`, `orchestrator/tests/conftest.py:1044-1070`)。コード自身も保証を same host/filesystem に限定している (`orchestrator/tests/conftest.py:1061-1065`)。
- 別 host shard 間の real-repo conflict は local flock に任せず allocator の conflict edge で閉じている (`tools/acceptance_shards.py:74-84`)。この層は触らない。
- `tools/mutation_worktree.py` の `--out` lock は TMPDIR 非依存なので不変である (`tools/mutation_worktree.py:192-219`)。
- `tmp_path` 内の WAL、campaign、admission lock は test 固有 path 自体が一意なので、filesystem の到達範囲だけが広がっても別テスト同士の identity は合流しない。例は oracle admission root (`orchestrator/tests/test_s8b_oracle_driver.py:2531-2545`)。

### 問い 3. 既存 fstype 回帰ガード

Lustre を許す。

実際の述語は fstype が `tmpfs`, `ramfs`, `devtmpfs`, `hugetlbfs` のいずれかなら `"tmpfs"`、それ以外なら `"ok"` を返す (`orchestrator/tests/test_real_repo_serialization.py:445-451`, `orchestrator/tests/test_real_repo_serialization.py:516-524`)。したがって `"lustre"` は `"ok"` である。

実効検査は `"tmpfs"` だけを offender とし、明示 TMPDIR なら fail、ambient default tmpfs なら skip する (`orchestrator/tests/test_real_repo_serialization.py:5268-5297`)。Lustre root はこの述語を一切変更せず通る。

実装では合成 mountinfo に `/work ... - lustre ...` を追加し、`_tmpdir_verdict("/work/...") == ("ok", "lustre")` を positive control に加える。既存 tmpfs positive control と実 `/dev/shm` 対照は残す (`orchestrator/tests/test_real_repo_serialization.py:5315-5371`)。

### 問い 4. 受入受領証への影響

選定した conftest 内部設定では次のとおり。

- argv: 変わらない。receipt は引き続き `["python3", "tools/run_tests.py"]` を要求する (`tools/acceptance_launcher.py:21-23`, `tools/dev_wave_land.py:984-987`)。
- `env_projection`: 変わらない。projection の閉集合は `PYTEST_ADDOPTS`, `PYTEST_PLUGINS`, `IZANAGI_TASK_RUN_ID`, `IZANAGI_TASK_RUNS_ROOT` だけであり TMPDIR は含まれない (`tools/acceptance_launcher.py:53-60`, `tools/dev_wave_wait.py:458-470`, `tools/dev_wave_land.py:138-143`)。conftest が変更するのは pytest child 内なので、waiter が作る projection には現れない。
- collection digest: TMPDIR は nodeid、file、loadgroup の payload に入らないため、設計上は不変である (`tools/acceptance_shards.py:259-264`, `tools/acceptance_shards.py:1010-1023`)。ただし環境依存 parametrization の不存在だけで断定せず、A/B の digest 完全一致を測定 gate にする。
- 実行器束縛: `tools/run_tests.py` を編集しないので `runner_executed_sha256` は不変である。runner hash は tested-main blob から動的に計算・再照合される (`tools/acceptance_launcher.py:565-601`, `tools/acceptance_launcher.py:614-621`)。
- suite bytes の束縛: conftest 変更は receipt の `tested_tip` と clean-tree fingerprint が束縛する (`tools/acceptance_launcher.py:495-508`, `tools/dev_wave_wait.py:2090-2142`)。

よって receipt schema/pin の更新は不要である。もし実装段階で TMPDIR を `env_projection` へ追加する案へ変えるなら、同じ commit で少なくとも `tools/acceptance_launcher.py:53-60,194-201,495-508`, `tools/dev_wave_wait.py:458-470`, `tools/dev_wave_land.py:102-143,934-1004` と対応テストを一括更新しなければならない。この案は本 plan では採らない。

### 問い 5. どこで設定するか

| 層 | 受理集合・到達範囲 | 迂回と問題 | 判定 |
|---|---|---|---|
| shell の ambient TMPDIR | pytest、bare runner、素の Python の全てへ届く | operator 依存、receipt 外、未設定へ戻る | 測定 arm のみ |
| `dev_wave_wait.py` / launcher | dev-wave receipt 経路へ届く | bare `python3 tools/run_tests.py` へ届かず、projection/pin 面が増える (`tools/dev_wave_wait.py:807-845`) | 不採用 |
| `tools/run_tests.py` | bare runner、launcher、local/dispatch の choke point | 編集 wave 自身が tested-main runner を使うため land 不能 (`docs/decisions.md:31681-31697`, `docs/decisions.md:38624-38641`) | 禁止 |
| `tools/acceptance_shards.py` / dispatcher | K>1 dispatch だけ | login local K=1 と直接 pytest へ届かない。compute の親 TMPDIR は allowlist 外 (`tools/pegasus/dispatch_compute.py:114-132`) | 不採用 |
| pytest `--basetemp` | `tmp_path` 系だけ | memo、patchharness、mutation lock、一般 `tempfile.*` が残る (`orchestrator/tests/README.md:32-35`) | 不採用 |
| `conftest.py::pytest_configure` | bare runner、launcher、`python -m pytest` の全 suite process と子 subprocess | 素の `python3 test_*.py` は到達不能 (`orchestrator/tests/README.md:36`) | 選定 |

選定は `orchestrator/tests/conftest.py:2502-2523` の最初で設定し、`pytest_unconfigure` で nested `pytest.main()` を壊さないよう元の env と `tempfile.tempdir` cache を復元する (`orchestrator/tests/conftest.py:2903-2935`)。

過去との違いは以下である。

- 過去は tmpfs を全環境へ注入して memory cgroup を削った (`orchestrator/tests/conftest.py:3-9`)。
- 今回は `TMPDIR` が未設定または空、かつ site が Pegasus LOGIN、かつ canonical repo の sibling root が実際に `lustre` の場合だけ既定を補う。
- 明示 TMPDIR はそのまま尊重する。したがって `/tmp` baseline arm と operator override は保たれる (`orchestrator/tests/conftest.py:24-28`)。
- compute、OTHER、素の Python は変更しない。
- stable repo-keyed root を使い、lock identity を毎走分断しない。
- tmpfs fstype は設定前にも拒否し、設定後には既存ガードが独立に再確認する。

### 問い 6. 置き場の選定

#### login 形

`/work` 配下の Lustre が正しい第一候補である。実測対象そのもので、n=32 fsync は `/tmp` 29.06 秒に対し `/work` 0.081 秒だった (`brief.md:19-35`)。

root は hardcode した wave path や per-run path ではなく、Git common-dir の parent から次のように導く。

```text
<main-repo-parent>/.izanagi-acceptance-tmp/<sha256(canonical-common-dir)[:16]>
```

Git common-dir 由来なら sibling worktree と全 wave が同じ repo identity を共有する。既存 common-dir 解決は absolute、strict resolve、directory を fail-closed で要求している (`orchestrator/tests/conftest.py:1000-1041`)。

- mode は base/root とも 0700。symlink、別 uid、group/other bit を拒否する。
- 他 repo は digest child で分離し、同 repo の他 wave は意図的に共有する。
- pytest は root 内で session ごとの numbered directory を使う。memo は run/session/HEAD hash で分離する (`orchestrator/tests/real_repo_receipt_memo.py:131-163`)。
- root 全体を自動削除しない。別 wave の live lock を消しうるためである。memo の 6 時間 stale prune は既存の prefix 限定処理へ任せる (`orchestrator/tests/real_repo_receipt_memo.py:375-402`, `orchestrator/tests/sort_swo_oracle_receipt_memo.py:394-417`)。
- `TemporaryDirectory`、T-080 atexit cleanup、各 `mkdtemp` consumer の既存 cleanup は維持する (`orchestrator/tests/test_s8b_oracle_driver.py:912-923`)。
- `/work` の Lustre quota は `statvfs` の global free だけでは証明できない。実装前に親が user quota と 2 並行走相当の余裕を確認する。quota を確認できなければ容量保証は未解決として止める。

#### dispatch / compute 形

compute には Lustre を強制しない。

- compute の `/tmp` と `/scr` は単一 process 300 fsync でそれぞれ 0.026 秒、0.021 秒である (`orchestrator/tests/README.md:15-23`)。
- tests task の parent overlay allowlist に TMPDIR は無いため、login の値は compute request へ運ばれない (`tools/pegasus/dispatch_compute.py:114-132`, `tools/pegasus/dispatch_compute.py:3088-3091`)。
- compute child は job 側環境を基礎にする (`tools/pegasus/dispatch_compute.py:1100-1111`, `tools/pegasus/dispatch_compute.py:1241-1275`)。
- `$TMPDIR` が PBS により既に設定されていればそれを尊重する。未設定なら `/tmp` のままにする。
- `/scr/$PBS_JOBID` は job-local lifetime と明示 cleanup を持てるが、現 dispatcher tests job は作成・cleanup を所有していない。既存の専用測定 job は create-only と cleanup を明示している (`tools/pegasus/acceptance_nproc_study.sh:219-224`, `tools/pegasus/b10_backoff_shape_campaign.sh:271-275`)。tests dispatch に追加するのは別 scope である。

### 問い 7. 効果の測り方

高価な全走は最低 6 回必要である。3 走未満へ減らすと D357 と D1260 を満たさない (`docs/decisions.md:15594-15607`, `rulings-verbatim.md:630-642`)。

1. 全走前の停止 gate

   - stable root が Lustre、0700、same uid、repo 外であることを確認。
   - 同一 root を見る二 process flock probe、可能なら二 host flock probeを行う。
   - `TMPDIR=/tmp` と `env -u TMPDIR` で、`test_campaign.py`、二 memo、T-080 base、patchharness/mutation lock の焦点走を行い、実効 path、fstype、fsync/fdatasync 回数が期待どおり変わることを確認する。
   - 焦点走は機構発火確認だけに使い、wall 改善の証拠にしない。duration は一次証拠にしない (`rulings-verbatim.md:39-44`)。

2. collection 同値性の安価な確認

   - 同一 tip で A=`TMPDIR=/tmp`、B=`TMPDIR unset` を各一回 collect-only。
   - canonical nodeid digest、件数、skip/hold registry state を比較する。
   - 1 byte でも異なれば全走へ進まず停止する。

3. paired full

   - 同一 tested tip、K=1 の login local 形、worker=32、growth hold opt-in なしを固定する。
   - 順番は A-B、B-A、A-B の 3 pair。自分の他 job は同時に走らせない。
   - A は明示 `TMPDIR=/tmp`。B は TMPDIR unset とし conftest の既定 Lustre root を発火させる。これにより同一 code tip の比較になる。
   - 各走について tested tip、K、worker 数、collection digest、`IZANAGI_RUN_GROWTH_HELD_TESTS` の値または不在、実効 TMPDIR、fstype、pytest wall、受入全体 wall、赤/skip 集合を記録する (`rulings-verbatim.md:693-707`, `rulings-verbatim.md:190-203`)。
   - arm 別中央値と pairwise delta 中央値を両方出す。B の中央値が A より 10%以上短く、3 pair 中少なくとも 2 pair が同方向、collection/結果集合が完全一致した場合だけ効果ありとする。
   - 10%未満は「変化なし」とし land しない。D667 の 168〜274 秒変動に埋もれた単発差を採用しない (`rulings-verbatim.md:243-250`)。

4. 走行回数の最小化

   - 静的、fstype、flock、焦点、collection のいずれかが落ちれば全走 0 回で停止。
   - full の途中で red、collection drift、Lustre capacity failure が出た場合も停止。
   - 緑の改善主張をする場合だけ 3 pair を完走する。6 回未満から改善を主張しない。

### 問い 8. 変異事前登録

下の「変異事前登録の候補」を段 4 の候補集合とする。特に stable root を per-run root に変える変異は correctness mutation であり、性能変異として扱わない。

## plan v1 (file:line 粒度)

1. `orchestrator/tests/conftest.py:1-29`

   module docstring を更新する。単一 process 値だけで並列順位を判断しないこと、login n=32 の `/tmp` 対 Lustre 実測、compute は現状維持、stable root の lock 理由を明記する。依存なし。

2. `orchestrator/tests/conftest.py:30-50`

   `tempfile` を import する。`gettempdir()` cache の無効化と `pytest_unconfigure` での復元に使う。

3. `orchestrator/tests/conftest.py:918-1070`

   次を追加する。

   - canonical common-dir から repo-keyed stable root を導く helper
   - 0700、non-symlink、same uid、repo/control-container 外を検査する helper
   - `/proc/self/mountinfo` から最長前方一致で fstype を得る helper
   - auto root は `lustre` exact だけを受理する policy
   - `TMPDIR` 未設定または空、Pegasus LOGIN の場合だけ `os.environ["TMPDIR"]` を設定し、`tempfile.tempdir = None` にする
   - 元の env の「key 不在/空/値」と元の `tempfile.tempdir` を config 属性へ保存する
   - effective root、fstype、origin を controller log へ一度だけ残す

   root 全体の削除、per-run root、tmpfs fallback は実装しない。

4. `orchestrator/tests/conftest.py:1044-1070`

   `_REAL_REPO_LOCK_DIRECTORY = /tmp` と legacy/common lock path は変更しない。これは明示的な非変更点である。

5. `orchestrator/tests/conftest.py:2502-2523`

   `pytest_configure` の先頭で TMPDIR policy を発火させる。receipt memo prewarm、test module collection、worker spawn より前に環境を確定する。失敗は `pytest.UsageError` で fail-closed。

6. `orchestrator/tests/conftest.py:2903-2935`

   controller/nested session のみ、policy が所有した変更を復元する。明示 TMPDIR や外側 pytest session の値は消さない。

7. `orchestrator/tests/test_real_repo_serialization.py:434-540`

   policy helper の unit test seam を追加する。site、common-dir、mountinfo、既存 root metadata を mock し、login/compute/OTHER、明示値、空値、nested session を検査する。

8. `orchestrator/tests/test_real_repo_serialization.py:5246-5371`

   既存 tmpfs predicate を維持したまま、合成 Lustre mount と chosen root の `"ok", "lustre"` positive control を追加する。`tmp_path` と `tempfile.gettempdir()` が auto policy 時に同じ root closure にあることも検査する。

9. `orchestrator/tests/test_real_repo_serialization.py:5393-5617`

   load-bearing guard tableへ新しい policy test を登録する。tmpfs positive、disk negative、skip 条件の既存 control は削らない。

10. `orchestrator/tests/test_campaign.py:12408-12531`

    `patchharness._lock_path()` が同じ canonical treeとstable TMPDIRに対して同一 pathを返し、二つ目の process/contextが排他される testを追加する。per-run root変異を KILL する。

11. `orchestrator/tests/test_mutation_harness.py:357-383`

    同じ repoとstable TMPDIRで二重 harness lockが拒否される testを追加する。既存 login site gateより後だけで発火することを保つ。

12. `orchestrator/tests/README.md:3-38`

    login/compute の二 regime、stable root、明示 override、`--basetemp` 射程外、素の Python 非到達、cleanup/quota 運用を更新する。

13. 非変更ファイル

    - `tools/run_tests.py`: D838/D1151 により編集しない。
    - `tools/acceptance_launcher.py`, `tools/dev_wave_wait.py`, `tools/dev_wave_land.py`: receipt schema/pin を変えない。
    - `tools/pegasus/dispatch_compute.py`: compute TMPDIR allowlist を変えない。
    - `tools/acceptance_shards.py`: K、割付、collection digest 定義を変えない。
    - 二 memoと `tools/mutation_harness.py`: stable rootにより既存 lock codeをそのまま強化する。機構自体は編集しない。

依存順は 1→2→3→5→6→7→8→9→10→11→12。静的・焦点検査が終わるまで full measurement へ進まない。

## 変異事前登録の候補

| 変異点 | 期待挙動 | 期待 KILLED |
|---|---|---|
| LOGIN 判定を削除し compute にも Lustre を注入 | compute は ambient `/tmp`/`$TMPDIR` のままでなければならない | 新規 `test_tmpdir_policy_is_login_only` |
| `setdefault` 相当を強制代入へ変更 | 明示 `TMPDIR=/tmp` を保存する | 新規 `test_tmpdir_policy_preserves_explicit_value` |
| 空 TMPDIR を明示値扱い | 空は未設定として auto root へ解決する | 新規 `test_tmpdir_policy_treats_empty_as_unset` |
| stable repo root を random/per-run rootへ変更 | 同じ repoの二 sessionでlock pathが同一 | `test_campaign.py` の新規 patchharness lock test、`test_mutation_harness.py` の新規二重 lock test |
| common-dirでなくwave worktree pathをhash | sibling worktreeが同一main identityを共有する | 新規 `test_tmpdir_policy_uses_git_common_dir_identity` |
| symlink、別 uid、0777 rootを許す | pytest開始前に fail-closed | 新規 root metadata parameterized test |
| fstype検査を削除、または tmpfs を許す | explicit/auto tmpfsは赤 | `test_effective_tempdir_is_not_tmpfs`, `test_tmpdir_fstype_lookup_positive_and_negative_control`, `test_tmpdir_guards_are_present_and_load_bearing` (`test_real_repo_serialization.py:5246-5297,5315-5390,5510-5617`) |
| Lustreを拒むよう述語を狭める | `"lustre"` は `"ok"` | 新規 Lustre positive control |
| `tempfile.tempdir = None` を削除 | pre-cached `/tmp` 後でも policy rootへ切替わる | 新規 cache-reset test |
| `pytest_unconfigure` の復元を削除 | nested pytest終了後に外側 env/cacheが復元される | 新規 nested-session test |
| workerがpolicy rootを継承しない | auto policy時の `tmp_path` がchosen root外になる | 新規 actual `tmp_path` closure test |
| real-repo lock directoryをTMPDIRへ変更 | `_REAL_REPO_LOCK_DIRECTORY` は `/tmp` exact | 既存 `test_real_repo_lock_paths_ignore_git_environment_poisoning` 周辺 (`test_real_repo_serialization.py:4039-4103`) に exact pin追加 |
| memo lockを削除 | prewarm/cache raceはfail-closed | 既存 memo fault/lock tests (`test_real_repo_serialization.py:2986-3193,3250-3709`) |
| login TMPDIRをcompute request allowlistへ追加 | request overlayにTMPDIRを含めない | `test_pegasus_dispatch_compute.py` の tests task allowlist exact test追加 |
| receipt env_projectionへTMPDIRを片側だけ追加 | schema exact不一致で赤 | `test_acceptance_launcher.py:52-103`, `test_dev_wave_land.py:48-63,934-1004` |
| skip/deselect/maxfailを追加して高速化 | collection/selected集合不一致 | collection digest gate、既存 runner acceptance shape gate (`tools/run_tests.py:86-123,692-720`) |

## 未解決・親が測るべきこと

- 合成 probe の 29 秒差が実 suite の fsync待ちへ何秒写るかは未証明である。親 P1 の「全 unitが一様に速くなる」は、明示 `/tmp` sinkと非consumerがあるため静的にも強すぎる (`tools/run_tests.py:1180-1185`, `orchestrator/tests/conftest.py:918-924`)。
- Lustre mountの `flock` が二 host間で coherentか、`localflock` 相当でないかを二 host probeで確認する。確認できなくても現状より緩くはならないが、「cluster全体へ強化」の主張はできない。
- canonical rootのuser quota、1走 peak、同時2 wave時のpeak、異常終了後のresidue量を測る。root全体の自動削除は行わない。
- `pytest_configure` 時点の設定が実際の `tmp_path` parentへ間に合うことを focused runで確認する。実走前には断定しない。
- paired fullは tested tip、K=1、worker=32、collection digest、growth hold opt-inなしを明示し、6走完了前に改善を主張しない。
- dispatch/K=3のcompute pytest本体には本変更は効かない。login collectionだけの短縮をK=3全体の改善として報告してはならない。