## 総括

静的レビューの結果、must-fix はありません。実装は D1647 と段 4 裁定に適合しています。

pytest は指定どおり実行していません。16 node の台帳登録、4 つの lock 経路、xdist 集約、M1〜M11 の検出力を実物から照合しました。

## must-fix

なし。

## nit

- M8 の事前登録上の killer は「xdist 集約テスト」ですが、実際に赤になるのは `test_worker_payload_carries_observations_and_defaults_without_state` です。xdist 集約テストは `_WORKER_PAYLOADS` を直接構築するため、`_worker_payload` から lock interval を削る M8 では緑のままです。ただし別の新テストが確実に M8 を検出するため、変異 survivor ではありません。
- `session_timeline.workers` は全 worker の名簿ではありません。観測があった worker の部分集合として読む必要があります。判定には使用されず、裁定が指定した集合なので実装欠陥ではありません。

## 裁定との適合

1. `_acceptance_timed_real_repo_locks` の 4 経路

[conftest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/orchestrator/tests/conftest.py:1377) の制御フローは次のとおりです。

- 正常: `_real_repo_locks.__enter__` 成功後に `acquired` を採り、内側 protocol と `__exit__` が正常終了した後に `released` を採って記録します。interval は記録されます。
- lock 取得失敗: `acquired` の行へ到達しないため、interval は記録されません。元の取得例外が伝播します。
- lock 解放失敗: `acquired` は採取済みですが、`with` の `__exit__` が例外を投げるため `released` の行へ到達せず、interval は記録されません。取得済みだった区間を report から落としているのは事実ですが、段 4 裁定が「解放失敗時は記録しない」と明示した結果であり、意図どおりです。
- 内側 protocol の例外: generator の `yield` に例外が戻され、正常な lock 解放後も `with` の後へ進まず、interval は記録されません。例外を捕捉または置換する処理がないため、元の例外がそのまま伝播します。

2. 既存の `_real_repo_locks` patch

`_acceptance_timed_real_repo_locks` は `_real_repo_locks` を default 引数や import alias に保存しておらず、各呼び出し時に conftest module global から解決しています。したがって、提示された `mock.patch.object(suite_conftest, "_real_repo_locks", ...)` は新 helper を経由しても効きます。

新しい `test_runtest_protocol_configless_item_keeps_existing_lock_contract` も、同じ module 属性を patch して enter、protocol、exit の順序を確認しています。

3. xdist の collection 時刻

[acceptance_shards.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/tools/acceptance_shards.py:1019) は、controller に collection state がなければ `_WORKER_PAYLOADS` の有限かつ正の時刻だけを集め、`max(..., default=None)` を返します。

- authority 用 payload は正常にそろったが collection 時刻だけが全て欠測または不正なら、report には `null` が載ります。これは裁定が認めた欠測表現です。
- 全 worker が異常終了して custom payload が一つも届かない場合は、この `max` まで進みません。既存の `worker-payloads-missing` で report finalization が rc 16 になります。全 worker 異常終了が直接 `null` report を生成するわけではありません。
- 後者は timeline 追加前から必要だった collection authority も失われた状態であり、観測欠測だけによる新しい gate ではありません。

4. `timeline_workers` と `worker_occupancy` のずれ

具体的には次の場合にずれます。

- xdist crash report が worker ID を持たず、start/stop が 0 の場合、occupancy 側では node が `"serial"` または `"unobserved"` に帰属し得ますが、0 は bounds から除外されるため timeline 側には現れません。
- selected node が usable な TestReport を一つも出さなければ、occupancy は `"unobserved"` を持ちますが timeline には対応 entry がありません。
- lock interval payload は届いたが対応する runtime report が controller に観測されなければ、timeline には worker が現れ、occupancy はその selected node を `"unobserved"` に置きます。
- selected 集合外の report を受け取るような不正入力では、bounds だけが timeline に残り、occupancy にはその worker が現れない可能性があります。

したがって、二つの worker key 集合が同一だと仮定すると誤解を招きます。ただし timeline は「bounds または正常完了した lock interval を観測した worker」の map であり、worker roster ではありません。判定にも使用されず、段 4 の集合定義どおりです。

5. `_observed_epoch`

[acceptance_shards.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/tools/acceptance_shards.py:807) の exact-type 判定は `bool` を拒否します。通常経路は次だけなので、実運用で bool が来る経路はありません。

- `time.time()` の float
- pytest TestReport の数値 `start` / `stop`
- それらから作った state と worker payload

bool は monkeypatch、合成 report、または破損 payload からだけ到達します。

Unix epoch 0 や負値は形式上の timestamp にはなり得ますが、現在実行中の pytest を観測する対象環境では正当な現在時刻ではありません。`<= 0` の除外は crash report の既定値 0 を排除するという裁定の明示条件に一致します。

6. 受入台帳

[test_run_tests_shards.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/orchestrator/tests/test_run_tests_shards.py:50) の parametrize 追加 1 node と、同ファイル 953〜1441 行の非 parametrize test 15 nodeから、次の 16 node が導かれます。台帳には全て同じ文字列で各 1 回、値 `0.0` として存在します。

- `orchestrator/tests/test_run_tests_shards.py::test_acceptance_shard_hooks_keep_pytest_hookimpl_attributes[pytest_collection_finish-trylast]`
- `orchestrator/tests/test_run_tests_shards.py::test_collection_finish_clock_runs_after_synthetic_modifyitems_wrapper`
- `orchestrator/tests/test_run_tests_shards.py::test_controller_state_serial_uses_config_local_timeline`
- `orchestrator/tests/test_run_tests_shards.py::test_controller_state_xdist_uses_latest_collection_and_worker_lock_map`
- `orchestrator/tests/test_run_tests_shards.py::test_lock_interval_recorder_is_noop_without_shard_state`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_logreport_ignores_zero_nonfinite_missing_and_huge_bounds`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_logreport_tracks_reordered_bounds_per_worker_and_serial`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_protocol_access_none_reads_no_clock_and_records_nothing`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_protocol_configless_item_keeps_existing_lock_contract`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_protocol_lock_acquire_and_release_failures_record_nothing`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_protocol_preserves_inner_exception_without_recording`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_protocol_records_only_after_lock_release`
- `orchestrator/tests/test_run_tests_shards.py::test_session_timeline_contents_do_not_change_merge_verdict`
- `orchestrator/tests/test_run_tests_shards.py::test_session_timeline_is_required_and_valid_fixture_merges`
- `orchestrator/tests/test_run_tests_shards.py::test_sessionfinish_writes_serial_session_timeline`
- `orchestrator/tests/test_run_tests_shards.py::test_worker_payload_carries_observations_and_defaults_without_state`

[acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/orchestrator/tests/acceptance_duration_ledger.json:19561) の `nodeid_count` と実際の map 長はともに 19557 です。追加漏れ、重複、存在しない追加 node はありません。

## 攻撃したが破れなかった点

M1〜M11 は全て新しい 16 node のいずれかで検出されます。

| 変異 | 赤になる新テスト |
|---|---|
| M1 | `test_collection_finish_clock_runs_after_synthetic_modifyitems_wrapper` |
| M2 | `test_runtest_logreport_ignores_zero_nonfinite_missing_and_huge_bounds` |
| M3 | `test_runtest_protocol_configless_item_keeps_existing_lock_contract` |
| M4 | `test_runtest_protocol_lock_acquire_and_release_failures_record_nothing` |
| M5 | `test_runtest_protocol_lock_acquire_and_release_failures_record_nothing` |
| M6 | `test_runtest_protocol_access_none_reads_no_clock_and_records_nothing` |
| M7 | `test_session_timeline_is_required_and_valid_fixture_merges`。最初の正常 merge が extra-key 扱いになって赤になります。 |
| M8 | `test_worker_payload_carries_observations_and_defaults_without_state` |
| M9 | `test_controller_state_xdist_uses_latest_collection_and_worker_lock_map` |
| M10 | `test_controller_state_serial_uses_config_local_timeline` |
| M11 | `test_session_timeline_contents_do_not_change_merge_verdict` |

赤になるテストを特定できない変異はありません。新しい 16 node に恒真なテストも見つかりませんでした。

そのほか、次の点も破れませんでした。

- `validate_report_evidence` は `session_timeline` を一度も読みません。
- `merge_reports` の既存 gate 本体は変更されず、必須 top-level key 集合だけが更新されています。
- malformed timeline が merge verdict を変えない positive control は実装から独立した有効な検査です。
- collection 時刻は conftest の `tryfirst` hook と modifyitems wrapper 後に、acceptance plugin の `trylast` hookで採られます。
- serial report は正常値と完全欠測の両方を明示的に検査しています。
- `SCHEMA` は v1 のままです。