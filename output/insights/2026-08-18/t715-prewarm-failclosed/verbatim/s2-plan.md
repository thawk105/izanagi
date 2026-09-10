## 1. seam 判定

判定は「P1 の UID 確定部分は成立するが、同じ session 開始 hook で P2 の collection 条件まで満たして実解決する案は成立しない」である。

xdist 3.8.0 の順序は次のとおり。

1. `xdist/plugin.py:260-278` の `pytest_configure(trylast=True)` が `DSession` を登録する。
2. pytest 本体 `_pytest/main.py:317-330` が `pytest_sessionstart` を呼ぶ。
3. `xdist/dsession.py:82-91` の `DSession.pytest_sessionstart(trylast=True)` が `NodeManager` を作り、その場で `setup_nodes()` を呼ぶ。
4. `xdist/workermanage.py:48-58` で `NodeManager.__init__` が `config.getoption("testrunuid")` を読み、未設定時だけ `uuid4().hex` を生成する。
5. 同 `workermanage.py:308-313` が UID を `workerinput` に入れ、`:342-349` で worker へ送る。
6. `xdist/remote.py:403-424`、特に `:416` が worker の `PYTEST_XDIST_TESTRUNUID` へ伝播する。

したがって `orchestrator/tests/conftest.py:616-620` の既存 `pytest_configure` から controller の xdist 実行だけを判定し、`config.option.testrunuid is None` なら 32 桁 hex UID を設定すれば、`NodeManager` が読む前に cache key を確定できる。ユーザー指定 UID は上書きせず、memo 発火時に cache key として妥当か検証する。

一方、`xdist/dsession.py:102-105` は controller の `pytest_collection` を短絡する。worker は起動後に独自 collection を行うため、session 開始時点に collected item は存在しない。これは `conftest.py:366-373` の既存コメントとも一致する。

よって実解決 seam は次のように分離する。

- xdist: `conftest.py:483-497` の既存 `pytest_xdist_node_collection_finished(node, ids)` で、worker が返した最終 node ID 群に consumer があれば controller が prewarm する。
- 非 xdist: `conftest.py:468-480` の `pytest_collection_finish(session)` で、最終 `session.items` に consumer があれば同 process で prewarm する。
- UID の確定だけは `conftest.py:616-620` から行う。

xdist 側の安全順序は、`xdist/remote.py:236-262` が最終 `session.items` を controller へ送り、`xdist/dsession.py:274-299` が `pytest_xdist_node_collection_finished` を呼んだ後に `sched.add_node_collection()` と scheduling 判定を行う形である。hook が返るまで test は 1 本も schedule されない。

したがってこの seam は「OS worker process の生成前」ではなく「全 test 実行開始前」の barrier になる。P2 の実 collection 条件と worker process 生成前を同時に満たすには二重 collection が必要だが、新しい O(collection) 経路と焦点走の時間増を生むため採らない。裁定 (b) の正しさ上必要な性質、すなわち「test 中の production 経路が実 repo を再解決しない」は満たす。OS process 生成前という字面を絶対条件とするなら P1 と P2 は両立不能であり、その主張を実装コメントに残してはならない。

`tools/run_tests.py` の argv は変更しない。`_build_pytest_command` は `tools/run_tests.py:380-399`、受入形判定は `main()` の `:1714-1724`、pytest 起動は `:1907-1916` であり、今回の hook は runner と独立に効く。

## 2. 発火条件

正本には `conftest.py:263-318` 付近へ `RECEIPT_MEMO_CONSUMER_NODES` を置く。値は parametrize suffix なしの `file::test_function` 形とし、`_real_repo_node_id()` (`:308-312`) と同じ正規化規則を使う。

現行 source から得られる集合は 32 test 関数、実 item では 35 node である。

`test_s8b_oracle_driver.py` の `_run()` 既定経路は 22 関数、parametrize 展開後 25 node。

- `3037/3044` `test_success_wal_order_budget_and_evaluate_contract`
- `3136/3150` `test_oracle_pipeline_contract_keyword_is_mandatory_positive_control`
- `3156/3177` `test_build_result_contract_mismatch_aborts_campaign_before_measurement`
- `3189/3198` `test_binding_mismatch_refuses_only_that_row_before_evaluate`
- `3206/3218` `test_v8_bulk_reservation_unavailable_runs_nothing`
- `3246/3261` `test_reservation_envelope_exceeded_is_fail_closed`
- `3296/3305,3323` `test_verify_inconclusive_and_unknown_abort_reasons_are_fail_closed`
- `3339/3350` `test_probe_error_reason_is_fail_closed_unknown_abort`。2 node
- `3535/3551` `test_v3_all_rows_binding_refused_is_protocol_violation`
- `3580/3591` `test_v3_partial_binding_refused_is_protocol_violation`
- `3945/3989` `test_v6_freeze_swap_after_verify_is_not_observed`
- `4008/4042` `test_v7_manifest_swap_after_verify_is_not_observed`
- `4073/4092` `test_v2_resume_rejected_at_s1_s2_s3_boundaries`
- `4127/4146` `test_atomic_one_shot_lock_rejects_second_start`
- `4153/4172` `test_resume_wal_lstat_eio_propagates_fail_closed_from_public_driver`
- `4183/4216` `test_driver_full_frame_fsync_eio_is_not_folded_or_followed_up`
- `4233/4240,4255` `test_v4_marker_fires_across_output_root_change`
- `4288/4309` `test_v5_truncated_wal_rejects_resume_even_with_zero_parseable_records`。3 node
- `4724/4813` `test_official_driver_records_returncodes_through_real_producer_flow`
- `5181/5193` `test_unavailable_preflight_creates_bound_measurement_manifest_and_passes_false_kwargs`
- `5229/5240` `test_available_preflight_preserves_call_and_artifact_shape`
- `5260/5276` `test_probe_error_precedes_claim_marker_wal_and_budget`

同 file の直接 `patch_driver_resolver()` / `real_repo_receipt()` 利用は 6 node。

- `2324/2335,2338` `test_real_freeze_gate_lists_floor_and_budget_null`
- `2599/2612` `test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing`
- `2973/2991` `test_nonnull_floor_without_active_generation_is_refused`
- `3004/3021` `test_active_resolution_and_manifest_structure_refusals_are_aggregated`
- `3802/3835` `test_run_block_reuses_launch_validated_and_legacy_loader_is_dead`
- `3869/3915` `test_run_block_verifies_manifest_once_and_reuses_object`

`test_s8b_binding_driftguards.py` は 4 node。

- `249/269` `test_run_block_broken_binding_manifest_refuses_and_writes_nothing`
- `300/312` `test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal`
- `343/367-368` `test_receipt_memo_delegates_to_production_verifier_exactly_once`
- `376/400-402` `test_receipt_memo_patches_the_driver_module_the_tests_import`

除外する opt-out は次の 2 関数、実 item では 3 node。

- `test_s8b_oracle_driver.py:2510-2537`。`with_observation` の 2 node
- `test_s8b_oracle_driver.py:2551-2572`。1 node

また `test_s8b_binding_driftguards.py:411-414` は ROOT guard で memo 本体へ到達せず、`:417-438` は cache primitive だけを検査するため consumer 集合へ入れない。

実行時の判定は次のとおり。

- `--collect-only` など test body を実行しない経路では prewarm しない。
- parametrize suffix `[...]` と loadgroup suffix `@real-repo` を落とし、basename + test 関数へ正規化する。
- xdist では controller の空の `session.items` を見ず、worker が送った `ids` を使う。既存 `conftest.py:486-489` の ID loopへ判定を併合する。
- 最初に consumer を含む worker collection が到着した時だけ prewarm し、controller config の session-local 属性へ成功済み UID を記録する。
- 後続 worker では同じ UID であることだけを確認する。collection 不一致で後続 worker にだけ consumer が現れても、全 collection 完了前なのでその時点で prewarm できる。
- worker 自身は実解決しない。test 実行時は controller が作った cache の read-only loadだけを許す。

代表 nodeid は、非 parametrize の `test_s8b_oracle_driver.py::test_success_wal_order_budget_and_evaluate_contract`、parametrize の `test_s8b_oracle_driver.py::test_probe_error_reason_is_fail_closed_unknown_abort[bench-probe-error]`、直接 patch の `test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing` である。

## 3. fail-closed 判定式

`real_repo_receipt_memo.py:73-177` を、明示的な「prewarm 書込側」と「consumer 読取側」に分ける。

実装形は module flag ではなく、兄弟 memo の factory 先例 `real_repo_ratified_memo.py:66-84` に合わせた private memo object とする。

- `_ReceiptMemo.prewarm(run_id=...)`: 唯一 `_resolve_now()` を呼べる。
- `_ReceiptMemo.get()`: process memo または既存 session cache を読むだけ。miss では必ず例外。
- module-level `prewarm_real_repo_receipt()` と `real_repo_receipt()` はそれぞれ上記の別 method へ固定委譲する。
- `memo_resolver()` (`real_repo_receipt_memo.py:171-177`) は `real_repo_receipt()` だけを呼び、prewarm 引数や capability を受け取れない。
- factory を用意し、positive control は共有 singleton を clear せず、fake resolver を持つ別 memo object を使う。

L1〜L5 は次の判定にする。

| 枝 | consumer | prewarm |
|---|---|---|
| L1: cache path 不明 | process memo が無ければ赤。実解決禁止 | 非 xdist、かつ run ID が無い正規 serial 経路だけ process memo 用の実解決を許可。xdist UID/HEAD 不正なら赤 |
| L2: lock `open()` 失敗 | 赤。実解決禁止 | 赤。排他不能なので実解決もしない |
| L3: cache 不在 | 赤。実解決禁止 | valid UID + HEAD + lock 保持中だけ実解決を 1 回許可し、strict store 成功後にだけ process state を publish |
| L4: read/unpickle/type 不正 | 赤。実解決禁止 | 赤。既存の壊れ cache を resolver で上書きしない |
| L5: write/replace 失敗 | consumer から store は呼ばれない | resolver 後でも赤。process memo を publishせず、次経路にも戻り値を渡さない |

同じ UID + HEAD の cache が prewarm 前から存在し、controller process state が未設定なら `cache-preexists-before-prewarm` として赤にする。ユーザーが `--testrunuid` を再利用して前 session の cache を使い回し、「今回の実解決 0 回」になる経路を閉じる。成功済み同一 process の 2 回目 prewarm だけは process state hit とする。

`_cache_load()` (`:107-113`) は `None` を返さず、read、pickle、型不一致を区別した例外へ変える。`_cache_store()` (`:116-127`) は例外を握り潰さず、tmp cleanup を試みたうえで元の store error を送出する。`_prune_stale_caches()` (`:129-141`) は correctness に影響しない best-effort cleanup のままでよい。

新しい例外は `ReceiptMemoError(RuntimeError)` とし、message は固定 prefix `IZANAGI_RECEIPT_MEMO_FAIL_CLOSED_V1 ` + canonical JSON にする。最低限の field は次のとおり。

- `reason`: `cache-path-unavailable`、`lock-open-failed`、`cache-missing`、`cache-invalid`、`cache-store-failed` など
- `cache_path`: string または `null`
- `run_id`: string または `null`
- `head`: 40 hex または `null`
- `prewarm`: 現在の呼出しが prewarm method か
- `process_prewarmed`: process state が既に publish 済みか
- infrastructure error では `exception_type` と `errno`

誤って production 経路が prewarm 扱いになる抜けは、次の三重条件で閉じる。

1. `_resolve_now()` の静的 caller は `_ReceiptMemo.prewarm` だけ。
2. `memo_resolver()` → `real_repo_receipt()` → `_ReceiptMemo.get()` の経路に bool、token、caller-name 判定を置かない。
3. meta-test が AST で `_resolve_now` caller と `prewarm_real_repo_receipt` caller allowlist を固定する。

ROOT guard `real_repo_receipt_memo.py:171-176` と `patch_driver_resolver()` の patch 先 `:180-184` は不変とする。`s8b_oracle_driver` と `t080_freeze_migration` は変更しない。

## 4. 経路網羅

| 実行経路 | prewarm seam | consumer |
|---|---|---|
| `tools/run_tests.py` + xdist | `conftest.py:483-497`、worker final IDs 到着時に controller が prewarm | worker の `real_repo_receipt()` は disk cache loadだけ |
| 素の `pytest -n N` | 同じ conftest hook。runner 固有 env/argvに依存しない | 同上 |
| `tools/run_tests.py -n0` または xdist 不在 | `conftest.py:468-480` の serial `pytest_collection_finish` | 同 process memo |
| 素の `pytest` | 同じ serial hook | 同 process memo |

serial pytest 本体は `_pytest/main.py:383-408` で collection 後に runtestloopへ進み、`Session.perform_collect()` の `_pytest/main.py:872-884` が `pytest_collection_finish` を test 実行前に呼ぶ。よって素の pytest でも同じ規律に入る。

xdist worker は `xdist/remote.py:236-254` で最終 markerを nodeidへ反映し、`:256-262` で最終 item集合を送る。controller hook は `xdist/dsession.py:274-299` の scheduling 前に同期実行される。

`test_s8b_oracle_driver.py:34` と `test_s8b_binding_driftguards.py:44` の receipt memo import は、conftest と同じ `orchestrator.tests.real_repo_receipt_memo` module object を使う canonical importへ揃える。serial prewarm と test consumer が別 module singleton になる空振りを防ぐ。ratified memo の import は変更しない。

## 5. 既存テスト波及

指示どおり、まず file 名を列挙し、その後 file ごとに全 hit を `grep -nE` した。symbol 検索で該当したのは次の 4 fileだけだった。

- `orchestrator/tests/real_repo_ratified_memo.py`
- `orchestrator/tests/real_repo_receipt_memo.py`
- `orchestrator/tests/test_s8b_binding_driftguards.py`
- `orchestrator/tests/test_s8b_oracle_driver.py`

さらに `T-057`、`cache barrier`、`共有 cache`、`初回 miss`、`cache_clear()`、`壊れた cache` を意味検索し、次の隠れた依存を確認した。

- `conftest.py:263-268` の「共有 cache barrier」優先順コメント
- `test_real_repo_serialization.py:679-720` の CLI / cache barrier 順序監査
- `test_s8b_oracle_driver.py:2332-2334` の「初回 miss」コメント

波及は次のとおり。

- `test_s8b_binding_driftguards.py:343-373`: brief が許可した 1 本目。wave-before の `_session_cache_path=None` fail-open をやめ、別 memo objectを明示 prewarmして、production delegate 1 回と object identity を検査する。
- 同 `:376-408`: assertion は変更しないが、共有 singleton の `cache_clear()` をやめ、別 memo objectを prewarmしてから patch 先と spy count を検査する。
- 同 `:417-438`: brief が許可した 2 本目。壊れ cache の期待を `None` から structured `ReceiptMemoError` へ変更する。
- 同 `:411-414`: ROOT guard の期待は不変。
- `test_s8b_oracle_driver.py` の 32 consumer/opt-out の assertion は変更しない。`:2332-2334` の lazy miss 説明だけ prewarm 説明へ直す。
- `conftest.py:263-268` の優先順そのものは維持し、2 番目を correctness barrier と呼ばない説明へ直す。
- `test_real_repo_serialization.py:679-720` も expected order は変えず、`barrier` という意味付けだけ「旧 lazy payer の安定順」へ直す。
- `real_repo_ratified_memo.py:12` の receipt memo への類型参照以外に挙動依存はなく、同 memo は scope 外のため変更しない。
- `test_dev_waves_checker.py`、`test_dev_waves_integration.py`、`test_pegasus_tools.py`、`test_t080_freeze_migration.py` の T-057 hit は pycache/history predicate 等の別用途であり、本 memo への依存ではなかった。

したがって既存 assertion の期待値変更は brief §6 の 2 本だけである。`tools/run_tests.py` を変更しないため、`test_run_tests_nproc.py` 等の exact argv 期待にも波及しない。

## 6. meta-test 設計

`test_real_repo_serialization.py:36-118` 付近へ conftest から導出しない独立 consumer golden を置き、既存 payer test `:1122-1171` の直後へ次を追加する。

1. `test_receipt_memo_has_one_prewarm_payer_and_complete_consumer_inventory`

   - 32 canonical owner ID が conftest の集合と一致することを検査する。
   - `_run()` caller、直接 `patch_driver_resolver()`、直接 `real_repo_receipt()` を AST で抽出する。
   - `memo_receipt=False` の 2 関数が集合外であることを固定する。
   - `_resolve_now()` の唯一の caller が `_ReceiptMemo.prewarm` であり、`get`、`real_repo_receipt`、`memo_resolver` には存在しないことを固定する。

2. `test_receipt_memo_is_red_without_prewarm_and_resolves_exactly_once`

   - fake resolver と独立 memo objectを作る。
   - prewarm 前の `get()` が structured error、resolver count 0 になることを検査する。
   - `prewarm()` 2 回、`get()` 2 回でも fake resolver count が厳密に 1、返却 object が同一であることを検査する。
   - missing cache、壊れ cache、lock open failure、store failureを注入し、L1〜L5 の message field と resolver countを固定する。
   - store failureでは resolver count 1だが結果が publishされず、その後の `get()` も赤であることを固定する。

3. `test_receipt_memo_prewarm_is_wired_for_xdist_and_plain_pytest`

   - `_load_suite_conftest()` (`test_real_repo_serialization.py:121-128`) を使う。
   - fake serial session/itemsで `pytest_collection_finish` を直接呼び、consumerありなら prewarm 1 回、なしなら 0 回を検査する。
   - fake xdist node/IDsで `pytest_xdist_node_collection_finished` を呼び、worker UIDが prewarmへ渡ること、2 worker目では再実行しないことを検査する。
   - runner moduleを一切介さず、この hookを呼ぶことで素の pytest 経路を固定する。

合成負例は二系統を同じ test 内で実行する。

- wave前そのものの `if path is None: return _resolve_now()` と、cache miss時の `_resolve_now()` fallbackを持つ合成 class/sourceを AST guardへ渡し、`get が resolverを呼ぶ` として必ず拒否されることを確認する。
- consumer goldenから代表 nodeを 1 本抜いた合成集合を hook wiring guardへ渡し、prewarm 0 回を検出して必ず assertion redになることを確認する。

これにより、「検査 token が存在するだけ」の恒真 meta-testにはしない。

## 7. 変異候補

| # | 変異内容 | 期待して落ちる node |
|---|---|---|
| M1 | `real_repo_receipt_memo.py:148-149` 相当を wave前の `path is None: return _resolve_now()` に戻す | `test_receipt_memo_is_red_without_prewarm_and_resolves_exactly_once` |
| M2 | `:151-154` の lock open errorを wave前の `_resolve_now()` fallbackへ戻す | 同上の L2 case |
| M3 | `:157-163` 相当で consumer cache missから resolve/storeする wave前の形へ戻す | 同上の L3 case |
| M4 | `_cache_load()` (`:107-113`) が壊れ cacheで `None` を返す形へ戻す | `test_receipt_memo_session_cache_round_trip_preserves_the_resolution` |
| M5 | `_cache_store()` (`:116-127`) が write/replace errorを握り潰す形へ戻す | `test_receipt_memo_is_red_without_prewarm_and_resolves_exactly_once` の L5 case |
| M6 | `memo_resolver()` (`:171-177`) を `.get()` ではなく `.prewarm()` へ接続する | `test_receipt_memo_has_one_prewarm_payer_and_complete_consumer_inventory` |
| M7 | `conftest.py:483-497` の xdist prewarm 呼出しを削除または consumer 判定を恒偽化する | `test_receipt_memo_prewarm_is_wired_for_xdist_and_plain_pytest` |
| M8 | `conftest.py:468-480` の serial prewarm 呼出しを削除する | 同 node の plain pytest case |
| M9 | consumer集合から `test_success_wal_order_budget_and_evaluate_contract` を削除、または opt-out 2 本の一方を追加する | `test_receipt_memo_has_one_prewarm_payer_and_complete_consumer_inventory` |
| M10 | UID 確定を `NodeManager` 作成後へ遅らせる、または worker UIDと異なる値を prewarmへ渡す | `test_receipt_memo_prewarm_is_wired_for_xdist_and_plain_pytest` の UID case |

M1〜M5 は禁止したい wave前の実在形を直接含む。

## 8. 時間見積り

`q = 15.3 秒` を使う。

| 走行 | 変更前 | 変更後 | prewarmとして直列に乗る分 |
|---|---:|---:|---:|
| memo consumerなしの焦点走 | 実解決 0 回 | 実解決 0 回 | 0 秒 |
| memo consumer 1 node、CLIなし | lazy実解決 1 回 | prewarm実解決 1 回 | 15.3秒。ただし総実解決量は不変 |
| 対象2 fileの焦点走 | shared memo 1回 + scope外CLI 1回 = 2回 | prewarm 1回 + CLI 1回 = 2回 | prewarm 15.3秒がtest scheduling前に固定 |
| 全走 | shared memo 1回 + CLI 1回 = 2回 | prewarm 1回 + CLI 1回 = 2回 | 同じく15.3秒 |
| 非xdist単一process | 最初のconsumerで1回 | collection終了時に1回 | 総量15.3秒で不変 |

変更前の xdist 全走では実解決自体は1回でも、多数 worker が flock 待ちになる。変更後は worker scheduling前に controllerだけが解決し、workerはvalid cacheを読むため、実解決回数を増やさず待機の starvationを除ける。

最悪側の静的上界は「既存wallへ15.3秒を丸ごと加算」である。親の全走基準 173.10秒を使うと 188.40秒、比率は約1.088で、190.41秒の1.1倍閾値内である。ただしこれは待ち削減を一切差し引かない上界であり、最終判定は親が同一計算ノード、同一並列度でwallとCPU飽和度を実測する。

焦点走は consumerなしなら追加実解決ゼロである。新設 meta-test は fake resolverと合成 node IDsだけを使い、実 repo解決を起動しない。

## 総括

実装対象は `real_repo_receipt_memo.py`、`conftest.py`、2 consumer test file、`test_real_repo_serialization.py`。productionの受理経路と `tools/run_tests.py` は変更しない。

採用 seam は、UIDをworker生成前に確定し、実解決はworker collection結果をcontrollerが受け取ってtest scheduling前に1回だけ行う形である。session中のmiss、lock不能、壊れcache、store失敗はすべて structured errorへ倒す。実装・pytest実走・ファイル変更はこの段では行っていない。