## 現物で確かめた事実

[refuted] **親の「FakeMemo の差し替えが `pytest_configure_node` に間に合わない」という読解は誤りです。**
実体の [xdist/dsession.py:82](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:82) に `@pytest.hookimpl(trylast=True)` があります。pluggy は `_hooks.py:464` で trylast 実装を先頭へ入れ、`_callers.py:93` で逆順に呼びます。したがって、この probe の通常の `pytest_sessionstart`（`test_real_repo_serialization.py:5074`）が先に FakeMemo を取り付け、その後 DSession → `setup_nodes()` → `WorkerController.setup()` → `pytest_configure_node`（`xdist/workermanage.py:342`）となります。**再現条件:** 現在の probe の argv と、指定された xdist／pluggy の実体。静的読解であり、実走はしていません。

[real] **shard 環境変数の継承と、Config の spec 属性の存在は別です。**
`tools/acceptance_shards.py:797` が環境を読み、同:873–891 の登録済み hook が初めて属性を設定します。正規 runner は `tools/run_tests.py:1499` で plugin を argv に、同:1517 で spec を env に入れます。**再現条件:** `IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1` だけを残し、plugin を登録しない入れ子 pytest。属性は設定されません。

[real] **nonce 伝播を発火条件の外へ残す必要があります。**
`conftest.py:2336,2355` の伝播を「spec なしなら return」で飛ばすと、worker が同:2603 または同:2660 で `UsageError` を送出します。**再現条件:** spec のない既存 xdist probe に対し、`pytest_configure_node` 冒頭で return する変異。plan:126 の対処はこの退行を閉じます。過去の赤2件との同定ではありません。

以下の行番号は指定 checkout に対するものです。必読11ファイルはすべて読取り可能でした。ファイル変更、pytest 実行、commit、git 状態の変更はしていません。

表中の略号は次のファイルを指します。テストファイルはすべて `orchestrator/tests/` 配下です。

| 略号 | ファイル |
|---|---|
| C / R / T | `conftest.py` / `real_repo_receipt_memo.py` / `test_real_repo_serialization.py` |
| P / F | `test_run_tests_task_run.py` / `test_pytest_failure_digest.py` |
| S / Q | `test_acceptance_schedule_order.py` / `test_pytest_collection_config.py` |
| G / L | `test_growth_test_holds_contract.py` / `test_flaky_test_holds_contract.py` |
| M / W | `test_mutation_harness.py` / `test_mutation_worktree.py` |
| B / K | `test_p3_b4_producer_auth_experiment.py` / `test_codex_worker_launch.py` |

## 入れ子走行の全列挙と判定 (1 件 1 行)

[real] 以下の「偽」は、plan:111–116 の**早期起動条件**に対する判定です。collection 後の既存 prewarm まで不発という意味ではありません。再現条件は、正規受入から各テストを実行し、記載された子 argv／env／cwd を使用することです。正規受入は `PYTEST_ADDOPTS`／`PYTEST_PLUGINS` を許しません（`tools/run_tests.py:695–699`）。

[real] **下表の実 pytest 起動経路は、すべて shard spec 環境変数を削除していません。直接の子 argv に `-p tools.acceptance_shards` を加えるものは確認されませんでした。**
環境の根拠は T:1030,1139,5093,5437,5472,5541,5561、P:887,930,978,1019、F:521、S:265,665、Q:127、G:1478,1575、L:230、B:276、K:2231,2292、および `tools/mutation_harness.py:1933–1942` です。pytester も環境をコピーします（`_pytest/pytester.py:1364`）。

| 所見・呼出し元 | 実 argv／cwd と発火判定 |
|---|---|
| [real] T:1197 `test_stub_free_receipt_nodes_are_selected_and_reach_setup_by_default` | T:1159,1167,1181。`-n0`、対象 file の collect-only と対象 nodeids の setup-only、cwd=repo。**偽**。 |
| [real] T:1586 `test_real_repo_group_collection_exactly_matches_canonical_nodes` | T:1037。全 tests dir だが `--collect-only`、cwd=repo。**偽**。 |
| [real] T:1735 `test_shard_assignment_preserves_live_xdist_group_components_and_split_control` | 同じ T:1037 の collect-only。allocator を直接検査するが shard plugin を起動しない。**偽**。 |
| [real] T:1820 `test_xdist_group_audit_rejects_synthetic_negative_controls` | T:1843→1037。合成 file、collect-only、cwd=temp。**偽**。 |
| [real] T:1871 `test_xdist_group_name_set_audit_rejects_isolated_negative_controls` | T:1901→1037。合成 file、collect-only、cwd=temp。**偽**。 |
| [real] T:5041 `test_receipt_memo_real_xdist_order_has_no_worker_payer` | T:5106。`-n1 -p orchestrator.tests.conftest -p receipt_order_plugin <temp-file>`、cwd=repo。spec 不在かつ file 選択で**偽**。既存 fallback は必要。 |
| [real] T:5410 `test_receipt_memo_consumers_do_not_resolve_during_collection` | T:5423,5437。子 Python 内で `pytest.main([--collect-only, …2 files])`、cwd=repo。**偽**。外側 process 内の再入ではない。 |
| [real] T:5445 `test_sort_swo_oracle_does_not_resolve_during_collection` | T:5458,5472。子 Python 内で collect-only、1 file、cwd=repo。**偽**。 |
| [real] T:5501 `test_loadgroup_scheduler_keeps_same_group_on_one_worker_and_control_detects_absence` | T:5546,5565。合成 file、`-n2`、loadgroup 有／無、cwd=temp。production conftest を登録せず**偽**。 |
| [real] P:834 `test_real_pytest_hook_records_aggregate_only_in_tmp_ledger` | P:853–856。`RT.main` が実 subprocess を起動。xdist 無効、`-p orchestrator.tests.conftest <temp-file>`、runner の cwd=repo。**偽**。 |
| [real] P:871 `test_live_xdist_controller_writes_one_sidecar_and_one_loadgroup_attestation` | P:892。`-n2 --dist loadgroup -p orchestrator.tests.conftest <temp-file>`、cwd=repo。**偽**。P:902 の空 stderr 契約あり。 |
| [real] P:914 `test_live_xdist_late_outer_wrapper_override_attests_unknown_once` | P:933–950。同じ file 選択＋`late_scheduler_override`、cwd=repo。**偽**。 |
| [real] P:960 `test_live_xdist_loadgroup_subclass_override_attests_unknown_once` | P:981–998。同じ file 選択＋`loadgroup_subclass_override`、cwd=repo。**偽**。 |
| [real] P:1008 `test_live_xdist_sessionfinish_scheduler_swap_keeps_runtestloop_value` | P:1022–1039。同じ file 選択＋`late_scheduler_swap`、cwd=repo。**偽**。 |
| [real] F:553 `test_real_pytest_end_states_have_exact_digest_presence` | F:601–625。temp file／empty dir、serial／collect-only の5走、コピーした conftest、cwd=repo。**偽**。 |
| [real] F:780 `test_e2e_real_conftest_digest_has_real_failures_and_exact_account` | F:665 fixture→714–731。`-n2 --dist loadgroup <temp-file>`、コピーした conftest、cwd=repo、timeout=15秒。**偽**。 |
| [real] F:999 `test_real_dispatch_relay_preserves_complete_e2e_digest` | 同じ F:665 fixture の入れ子結果を使用。**偽**。独立した2本目の pytest 起動ではない。 |
| [real] F:953 `test_nested_pytest_main_currently_clears_outer_failure_stash` | F:961。真の in-process `pytest.main`、`plugins=[C]`、temp file、cwd は外側のまま。新 Config に shard plugin は登録せず**偽**。 |
| [real] S:338 `test_g1_live_hook_chain_preserves_collection_identity` | S:275。pytester、`-n1 --dist loadgroup`、cwd=pytester temp。S:135–137 が production hook を転送するが spec 不在で**偽**。 |
| [real] S:615 `test_g5_two_ledgers_preserve_outcomes_skip_markers_and_properties` | S:626,628→275。同じ temp suite を2走。**偽**。 |
| [real] S:660 `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` | S:673–691。repo 全 tests dir、`-p …test_acceptance_schedule_order --collect-only`、cwd=repo。**偽**。 |
| [real] S:943 `test_g7_live_negative_categories_keep_original_order` | S:950→275。`-x`／`--ff`／collect-only／他の指定、cwd=pytester temp、spec 不在。**偽**。 |
| [real] S:957 `test_g7_live_worker_dist_no_still_reorders_with_loadgroup` | S:964→275。temp suite、spec 不在。**偽**。 |
| [real] S:971 `test_g7_live_hook_uses_loadgroup_splitter` | S:992→275。temp suite、spec 不在。**偽**。 |
| [real] S:999 `test_g7_live_worker_uses_controller_snapshot_not_mutated_file` | S:1011→275。temp suite、spec 不在。**偽**。configure-node hook 自体は通る。 |
| [real] S:1025 `test_g7_live_hook_calls_identity_guard` | S:1032→275。temp suite、spec 不在。**偽**。 |
| [real] Q:211 `test_pytest_ini_norecursedirs_restates_the_installed_pytest_defaults` | Q:221→144。`--collect-only -p norecurse_probe`、cwd=temp 空 dir。**偽**。 |
| [real] Q:246 `test_bare_pytest_collection_is_scoped_by_testpaths` | Q:255,261→144。引数なしの temp suite、ini 有／無、collect-only。**偽**。 |
| [real] Q:269 `test_norecursedirs_excludes_generated_hidden_and_vendor_trees` | Q:279,290→144。`.`、cwd=temp、collect-only。**偽**。 |
| [real] Q:298 `test_ini_addopts_narrows_collection_while_runner_gates_stay_blind` | Q:307,315→144。temp ini の `-k` 有／無、collect-only。**偽**。 |
| [real] Q:356 `test_cleanup_collection_positive_control_with_empty_production_exclusions` | Q:368–406。runner が組んだ全 dir argv、`--collect-only -k …`、除外有／無、cwd=repo。**偽**。 |
| [real] Q:1085 `test_explicit_sort_swo_target_still_collects_without_runner_ignore` | Q:1086→144。1 file、collect-only、cwd=repo。**偽**。 |
| [real] Q:1112 `test_conftest_scheduler_attestation_loads_without_xdist` | Q:1121–1135。autoload 無効、`-p orchestrator.tests.conftest <temp-file>`、serial、cwd=repo。**偽**。 |
| [real] G:1619 `test_s8c_candidate_fixture_consumers_and_remaining_nodes_are_collection_pinned` | G:1578。in-process、`--collect-only --noconftest`、`plugins=[CONF,probe]`、1 file、cwd は外側のまま。**偽**。 |
| [real] G:1721 `test_candidate_fixture_collection_negative_controls_cover_pytest_shapes` | G:1733→1578。同じ collect-only、合成 file。**偽**。 |
| [real] G:1752 `test_candidate_fixture_collection_rejects_dynamic_getfixturevalue` | G:1763→1578。同じ collect-only、合成 file。**偽**。 |
| [real] G:2267 `test_opt_in_runs_held_fixture_and_parametrize_shape` | G:2282。`--noconftest <temp-file>`、cwd=repo、growth opt-in のみ追加。**偽**。 |
| [real] G:2377 `test_call_only_mode_still_rejects_noconftest_pytest_import` | G:2379。`--noconftest <temp-file>`、cwd=repo。**偽**。 |
| [real] G:2402 `test_call_only_mode_still_rejects_confcutdir_pytest_import` | G:2404。`--confcutdir <temp> <temp-file>`、cwd=repo。**偽**。 |
| [real] G:2440 `test_noconftest_bypass_is_refused_before_held_body` | G:2441。`--noconftest <explicit-nodeid>`、cwd=repo。**偽**。 |
| [real] G:2534 `test_regular_pytest_path_keeps_single_hold_skip` | G:2538。explicit nodeid、cwd=repo、serial。**偽**。 |
| [real] G:2556 `test_plain_pytest_delegating_runner_is_not_over_rejected` | G:2557 が `test_env_attestation.py` を直接起動し、同 file:1364 が `pytest.main([__file__,"-q"])`。file 選択で**偽**。 |
| [real] L:390 `test_registry_module_lazy_loader_drives_collection_skip_and_summary` | L:484,511。子 bootstrap 内 `pytest.main`、2 nodeids、production conftest を明示、autoload 無効、cwd=temp suite。**偽**。 |
| [real] L:552 `test_real_pytest_subprocess_skips_registered_node_and_runs_same_file_sibling` | L:562。registry plugin＋2 nodeids、cwd=repo。**偽**。 |
| [real] L:602 `test_xdist_subprocess_focus_collection_does_not_run_stale_check` | L:612。`-n2 --dist load -p <registry-plugin> <focus-node>`、cwd=repo。**偽**。 |
| [real] L:647 `test_requested_xdist_collect_only_effective_serial_rejects_stale_registry` | L:657。全 tests dir＋`-n2 --collect-only`、cwd=repo。**偽**。xdist は DSession を作らない。 |
| [real] K:2224 `test_launcher_failure_artifact_reporter_live_wiring` | K:2242。explicit nodeid、cwd=repo、env の worker 名を `live-probe` に設定。file/node 選択で**偽**。 |
| [real] K:2291 `test_launcher_failure_artifact_exception_safety_live` | K:2301。explicit nodeid、cwd=repo。**偽**。 |
| [real] B:1141 `test_wave_mutant_kills_exactly_one_registered_node` | B:1160。`tools/run_tests.py <8 nodeids> -q -rf`、cwd=scratch、env=B:276。runner は焦点走と判定し、早期条件は**偽**。 |
| [real] B:1595 `_candidate_non_regression` | B:1615。`tools/run_tests.py <nodeid> -q`、cwd=scratch、env=B:276。**偽**。これは同 file の実験 helper 経路。 |

[real] mutation harness 経由にも実 pytest 起動があります。以下の各行の共通再現条件は、M:348–357 の `pytest tests/test_gate.py -q -rf`、cwd=合成 repo、`tools/mutation_harness.py:1933–1942` の環境です。**shard env は残りますが、production conftest はありません**（M:237–249 は合成 conftest）。collection 子には `--collect-only` が加わります（`tools/mutation_harness.py:1444`）。

| 所見・呼出し元 | 判定 |
|---|---|
| [real] M:632 `test_m11_m12_direct_harness_local_attempt_persists_authorization_and_schema` | **偽**。共通経路。 |
| [real] M:708 `test_normal_run_uses_cumulative_replacements_and_full_failed_line` | **偽**。共通経路。 |
| [real] M:817 `test_applied_diff_must_equal_registration_preflight` | **偽**。baseline までは実行する（M:835）。 |
| [real] M:857 `test_expected_node_must_exist_in_pytest_collection` | **偽**。collection 子のみ。 |
| [real] M:868 `test_group_suffixed_expected_node_is_collected_and_killed` | **偽**。M:362–376 が `-n2 --dist loadgroup` を追加するが production conftest 不在。 |
| [real] M:894 `test_group_unsuffixed_expected_node_matches_suffixed_failure` | **偽**。同じ group 経路。 |
| [real] M:908 `test_group_suffixed_expected_node_resume_reuses_valid_ledger` | **偽**。初回の group 経路。 |
| [real] M:946 `test_parameter_suffix_is_matched_exactly` | **偽**。共通経路。 |
| [real] M:1242 `test_resume_rejects_different_head` | **偽**。初回の共通経路。 |
| [real] M:1257 `test_resume_rejects_different_spec_hash` | **偽**。初回の共通経路。 |
| [real] M:1272 `test_resume_reruns_parse_error_and_skips_terminal_record` | **偽**。初回／resume の共通経路。 |
| [real] M:1304 `test_resume_rejects_orphan_stop_sidecar_before_runner_without_hold` | **偽**。sidecar 作成前の初回走行。 |
| [real] M:1384 `test_resume_rejects_incomplete_running_record_before_runner` | **偽**。初回走行。 |
| [real] M:1410 `test_resume_rejects_duplicate_record_id` | **偽**。初回走行。 |
| [real] M:1422 `test_resume_rejects_every_missing_terminal_and_baseline_field_before_runner` | **偽**。M:1427 の初回走行。以後は runner を禁止する。 |
| [real] M:1459 `test_resume_rejects_terminal_record_poison` | **偽**。初回走行。 |
| [real] M:1487 `test_resume_rejects_minimal_forged_terminal_record` | **偽**。初回走行。 |
| [real] M:1521 `test_abnormal_rc_with_expected_failed_node_flushes_parse_error_and_stops` | **偽**。共通経路。 |
| [real] M:1541 `test_hang_risk_uses_short_timeout_records_evidence_and_restores` | **偽**。共通経路。 |
| [real] M:1570 `test_local_timeout_after_dispatch_submission_stops_without_terminal_record` | **偽**。共通経路。 |
| [real] M:1630 `test_local_timeout_ignores_conclusively_unrelated_submission` | **偽**。共通経路。 |
| [real] M:1666 `test_local_timeout_inventory_failure_stops_without_terminal_record` | **偽**。共通経路。 |
| [real] M:1733 `test_local_timeout_with_unreadable_dispatch_request_stops_as_evidence_unavailable` | **偽**。共通経路。 |
| [real] M:2299 `test_apply_mutation_calls_restore_at_the_production_callsite` | **偽**。共通経路。 |
| [real] M:2401 `test_completed_record_is_flushed_before_next_runner_sigkill` | **偽**。M:2414 の harness subprocess から共通経路。 |
| [real] M:2434 `test_sigterm_handler_stops_child_and_restores_active_mutation` | **偽**。M:2458 の harness subprocess から共通経路。 |
| [real] W:639 `test_m11_m12_wrapper_real_harness_local_attempt_persists_authorization` | **偽**。W:679→実 harness、子は W:403 の `pytest tests/test_gate.py`、cwd=disposable tree。production conftest 不在（W:248–256）。 |
| [real] W:1432 `test_real_harness_local_e2e_uses_disposable_tree_between_observation_points` | **偽**。W:1439→同じ実 harness 経路。 |

[real] `-p tools.acceptance_shards` を含む**command 組立て検査**はありますが、実入れ子ではありません。`test_run_tests_shards.py:315` は同:334 で `subprocess.call` を fake に置換します。同 file:28 も plugin の import だけです。**再現条件:** これらのテストを実行しても、その command を使った pytest controller は起動しません。

[real] 名前が `tools/run_tests.py` でも pytest を起動しない合成 runner があります。例えば `test_resume_gate_acceptance_boundary.py:273` は同:211 の合成 runner を同:404–426 から起動します。`test_dev_wave_wait.py:8857,8881,9170,9191,9220,9337,9416` も同:1041 の合成 runner を使用します。**再現条件:** 各 fixture のまま実行。prewarm hook は存在せず、条件は**偽**です。

[unknown] **合成 runner を含む全間接呼出しの「テスト関数単位の完全列挙」は完了していません。** `test_dev_wave_wait.py:1084` の共有 fixture と `test_mutation_worktree.py:288–295` の fake dispatch に多数の利用元があり、上表を repository 全体の完全性証明とは扱えません。実 argv／env／cwd まで辿れた経路と、未完の列挙範囲を区別します。

## plan への所見

[real] **発火述語の実装指示が閉じていません。特に `PYTEST_ADDOPTS` 経由の narrowing が抜けます。**
[plan:116](/home/SFC/tanab/.claude/jobs/774bd912/tmp/wave-artifacts/dev-wave-t2616-prewarm-configure-node/s2-plan.md:116) は C:2016 の述語に parsed `keyword`／`markexpr` 等を足す案です。しかし C:1908–1927 が走査するのは `invocation_params.args` で、ここには `PYTEST_ADDOPTS`／ini の addopts が含まれません（`_pytest/config/__init__.py:1063–1064`）。

**再現条件:** 有効な shard spec＋plugin、`-n2 orchestrator/tests` に、環境で `PYTEST_ADDOPTS='--ignore=…'` を与える。`config.args` は全 suite root のまま、keyword／markexpr は空で、既存述語は真になります。consumer file を環境側で除外しても早期起動する実装になり得ます。parsed `ignore`／`ignore_glob` 等まで判定するか、正規 shard 起動の閉じた形を保証する必要があります。

[real] **`--lf`／`--deselect` も、提案された既存述語では閉じません。**
C:1015 の narrowing 集合には両方ともありません。pytest は `cacheprovider.py:372–408` と `_pytest/main.py:482–496` で、後から実際に item を除外します。
**再現条件:** spec＋plugin＋全 suite root＋`--deselect=orchestrator/tests/`、または非 consumer だけを lastfailed に持つ `--lf`。C:2016＋keyword／markexpr 検査だけなら早期条件は真です。plan の「等」に含める意図は読めますが、具体的な判定・負例が未指定です。

[refuted] **plan が既存 probe の seam を前倒しして assertion を通す、という批判は当たりません。**
plan:181 は「spec なしの既存 probe を維持し、別ケースを追加」です。既存 probe をそのまま残す限り、T:5118–5123 の worker payer 0回・hook 相対順は残ります。
**変異条件:** C:2299 の外側 guard と C:880 の内側 guardを同時除去する。worker の collection-finish が FakeMemo を呼び、T:5067–5068 が `prewarm-worker` を記録するので T:5122 が赤になります。これは静的に追える変異であり、今回実走した結果ではありません。

[real] **ただし追加する早期 probe の検出力は未定義です。既存 assertion のコピーでは足りません。**
T:5118–5123 は prewarm の回数と payer を検査しますが、**prewarm が collection 前だったことは検査していません**。
**変異条件:** 早期起動を削り、既存 C:2422 の collection 後同期 barrier へ戻す。この変異は既存 probe を通ります。plan:181 の追加ケースは、configure-node から起動した証拠と worker collection／test-body 開始との関係を検査しなければ、この変異を落とせません。

[real] **既存 probe に plugin を足すだけでは早期経路の正例にもなりません。**
T:5109 は temp の単一 file です。plan:114 自身が file 選択を除外します。また FakeMemo は T:5064–5072 でログを書くだけで cache を公開しません。
**再現条件:** 既存 probe に `-p tools.acceptance_shards` と spec だけを追加する→早期条件は偽。逆に条件を強制して worker の ready 待機を有効にする→この FakeMemo だけでは ready にできません。seam の前倒しより、正例の選択形と公開契約を具体化することが先です。

[real] **plan の「明示した早期 job にだけ worker 待機」は必要です。**
C:2293 の collection-finish は tryfirst、xdist の collection 終了通知は `remote.py:257–262` です。
**再現条件:** 非受入 worker にも待機を入れる変異。worker は collection 終了通知前に cache を待ち、controller の fallback は通知後の C:2359–2422 なので、待つ側同士になります。F の入れ子は15秒で timeout します（F:731）。plan:128 はこの経路を断ちますが、旧(b)がこの変異だった証拠はありません。

[refuted] **通常の焦点走・単独走・collect-only・serial で早期条件が真になる、とは確認できません。**
spec のない走行は plan:112 で偽、file/nodeid と `-k/-m` は plan:114 で偽、collect-only は plan:113 で偽です。さらに xdist は collect-only で DSession を作りません（`xdist/plugin.py:268–270`）。serial では移設先 hook 自体が呼ばれません。
**再現条件:** 追加 plugin／環境側 selector を持たない通常の各走行。問題は上記の閉じていない選択経路です。

## 親 brief への所見

[refuted] **parent-probe-findings.md:69–81 の LIFO 説明は `trylast=True` を落としています。**
根拠・再現条件は冒頭の xdist／pluggy 順序です。FakeMemo が遅いという説明を旧(b)の有力機序から外すべきです。さらに spec 限定なら、この probe は早期対象外です（T:5106–5109、plan:112–114）。

[refuted] **「argv を継がない入れ子では必ず spec=None」は一般命題として強すぎます。**
`_pytest/config/__init__.py:872–874` は `PYTEST_PLUGINS` から plugin をロードします。同:1523–1527 は `PYTEST_ADDOPTS` を argv へ追加します。
**再現条件:** shard env と一緒に `PYTEST_PLUGINS=tools.acceptance_shards`、または `PYTEST_ADDOPTS='-p tools.acceptance_shards'` を継承する入れ子。属性が設定されます。ただし正規受入はこれらの環境を拒否するため、今回列挙した正規受入下の判定を覆すものではありません。

[refuted] **P の probe が外側 xdist 環境を残すことから、worker UID の不一致を推測する必要はありません。**
`xdist/remote.py:416–418` が内側 controller の `workerinput` で UID／worker 名／worker 数を上書きします。controller も C:2578–2587 で内側 UID を確定します。
**再現条件:** P:892 の内側 `-n2` 起動。plan:48 の worker UID に関する不確定性は、この実装面では静的に解消できます。

[unknown] **旧(a)の赤4件、旧(b)の赤2件の全件同定はできません。**
`verbatim-t2616.md:8–11` は件数と症状を記録していますが、失敗 nodeid・当時の差分・traceback がありません。**照合条件:** それらの成果物が必要です。nonce 欠落、待機と通知の循環、marker 混入を過去の実原因と断定しません。

## 見落としている経路

[real] **`IZANAGI_FREEZE_HOLD` は内側 controller の resolver が出します。環境から文字列が漏れるのではありません。**

呼出し鎖は次のとおりです。

`C:897–903`
→ `R:650–656`
→ `R:555–558`
→ `R:115–117`（production resolver は R:45 で保存）
→ `orchestrator/campaign/s8b_oracle_driver.py:166–169`
→ `t080_freeze_migration.py:2284`
→ 同:2297–2314 の `_load_artifact`
→ 同:1874–1877 の `held_marker`
→ `freeze_verification_hold.py:86–90` の stderr write／flush。

**再現条件:** 新しい内側 process、実 receipt が `never-issued` で早期 return せず、対象 artifact を読め、`HELD=True`（同 file:14）、その `(PID, check_id)` が未出力。`held_marker` 自体の出力抑制は同:77–91 の process/check 単位です。別経路として `t080_freeze_migration.py:2348–2352→2409–2410` もあります。

[real] **plan の限定条件は、P:871 の漏れ鎖を実際に起動側で断ちます。**
この子は spec 不在・単一 temp file なので早期対象外です。既存 fallback も consumer 不在で C:921,979 が偽になります。**再現条件:** P:887–899 の現行 argv/env/cwd を維持し、plan:126–129 の限定を実装すること。P:902 の `stderr == ""` を緩める必要はありません。

[real] **marker を抑制しても、不必要な prewarm を許せば空 stderr は守れません。**
C:2272–2281 は作業があった場合に `IZANAGI_MEMO_PREWARM_V1` も stderr へ出します。**再現条件:** P の consumer なし子で早期 prewarm を無条件起動する変異。対処点は marker の抑制ではなく発火条件です。

[real] **worker 待機を collection-finish に置く以上、非受入 fallback との分離は nonce 伝播とは独立した防壁です。**
nonce を正しく渡しても、C:2294 に全 worker 共通の cache 待機を入れると、`remote.py:257` の通知を止めます。**再現条件:** spec なしの T:5041 または F:665。nonce の配線テストだけでは、この通知前待機の退行を検出したことにはなりません。

## 総括

[real] **plan の方向は既存入れ子と両立しますが、実装指示としてはまだ閉じていません。** 修正すべき具体点は、①親の hook 順序誤読の撤回、②環境由来の narrowing と `--lf`／`--deselect` の扱い、③追加 probe で「collection 後へ戻す変異」を落とす assertion の明記です。再現条件と根拠は上記の各項に示しました。

[unknown] **「旧 crash を閉じた」「入れ子を完全列挙した」「非受入の所要を悪化させない」との完了判定は出せません。** 旧差分・失敗ログがなく、合成 runner の全間接利用元の列挙も未完です。今回の結論は静的検査の所見です。