# 段 2 実装プラン

結論は条件付き **NO-GO**。S-B と S-D、S-A の「申告 hash と実 bytes の不一致拒否」、S-C の ledger 実 bytes 照合までは実装可能である。一方、次の 2 点は現 brief の不変条件だけでは閉じない。

- S-A は `/tmp/evil.py` とその正しい hash を同時に申告すると通る。任意 wrapper / executable の拒否には caller 外の authority が要るが、P1 はそれを禁止している。
- S-C の guard producer が必要とする qstat transcript、owner、qsub 後の B job identity は coordinator config に存在しない。`snapshot_sha256` は preimage ではない。

したがって、以下では実装可能部分と、裁定なしに実装してはならない部分を分ける。

## S-A — wrapper / executable の live bytes 束縛

### 実装箇所と述語

1. `tools/pegasus/t810_harness_schema.py:301-360`、`validate_launch_intent()`

   `:350-353` の prefix 検査を次の exact 検査へ強化する。

   ```python
   wrapper == [
       "python3.10",
       slot["wrapper_path"],
       "--request",
       f"{work_root}/{slot['slot_id']}/wrapper-request.json",
   ]
   ```

   - 発火: `["python3.10", "/tmp/wrapper.py", "--request", "/tmp/other.json"]`
   - 非発火: `["python3.10", "/tmp/wrapper.py", "--request", f"{work_root}/slot-00/wrapper-request.json"]`

2. `tools/pegasus/t810_coordinator.py:169-196, 543-553`

   `_read_regular_bytes()` を使う `_assert_declared_file_identity(path, declared_sha256, name)` を `:553` 後へ追加する。述語は逐語で次のとおり。

   ```python
   schema.sha256_bytes(_read_regular_bytes(path, name)) == declared_sha256
   ```

   `O_NOFOLLOW`、regular-file、読取前後の `(dev, ino, size, mtime_ns)` 一致は既存 `:169-196` を再利用する。

   - 発火: file bytes が `b"wrapper-v2"`、申告値が `sha256(b"wrapper-v1")`
   - 非発火: file bytes が `b"wrapper-v2"`、申告値が `sha256(b"wrapper-v2")`

3. `tools/pegasus/t810_coordinator.py:664-684`、`prepare_group()`

   slot loop 内、receipt 読取 `:685` より前に次を追加する。

   ```python
   Path(slot["binary_source_path"]) == document["validator_kwargs"]["executable"]
   slot["binary_sha256"] == document["validator_kwargs"]["expected_executable_sha256"]
   actual_sha256(slot["wrapper_path"]) == slot["wrapper_sha256"]
   actual_sha256(slot["binary_source_path"]) == slot["binary_sha256"]
   ```

   - 発火: slot executable=`/tmp/package/CCBench-A`、validator executable=`/tmp/package/CCBench-B`
   - 非発火: 両方 `/tmp/package/CCBench-A`、両 hash と実 bytes の hash も同一

4. `tools/pegasus/t810_coordinator.py:773-801`、`_scheduler_effect()`

   `_assert_canonical_job_script(selected)` の直後、scheduler adapter 呼出し直前に wrapper と binary の live hash を再検査する。prepare 後の改変を捕捉する effect-boundary 検査である。

   - 発火: `prepare_group()` 後に `wrapper.py` を `b"tampered"` へ変更
   - 非発火: prepare 後から qsub effect まで bytes 不変

5. `tools/pegasus/t810_pbs_wrapper.py:341-386`、`publish_wrapper_request()`

   `slot` 確定後 `:352` に、publication 前の次の述語を追加する。

   ```python
   _sha256_file(Path(slot["wrapper_path"])) == slot["wrapper_sha256"]
   _sha256_file(Path(slot["binary_source_path"])) == slot["binary_sha256"]
   ```

   `tools/pegasus/t810_pbs_wrapper.py:527-537` の `_sha256_file()` も、coordinator と同様に non-symlink regular file と読取中の fingerprint 不変を要求する。

   - 発火: `wrapper_sha256 == "a"*64` だが wrapper 実 bytes の hash が別値
   - 非発火: 両方が実 hash

### 新規テスト候補

- `orchestrator/tests/test_t810_harness_schema.py::test_launch_intent_requires_exact_wrapper_request_cli`
  - 単独で殺す変異: wrapper argv 検査を再び `wrapper[:2]` だけに戻す。
- `orchestrator/tests/test_t810_pbs_wrapper.py::test_publication_rejects_declared_wrapper_hash_mismatch`
  - 変異: `publish_wrapper_request()` の wrapper live hash 検査を削除。
- `orchestrator/tests/test_t810_coordinator.py::test_scheduler_effect_rejects_wrapper_or_executable_changed_after_prepare`
  - 変異: `_scheduler_effect()` の effect 直前再 hash を削除。
- `orchestrator/tests/test_t810_coordinator.py::test_slot_executable_identity_must_equal_validator_identity`
  - 変異: path/hash の validator-to-slot 照合を削除。

### P1 では閉じない変異

次のテストも事前登録すべきだが、P1 のままでは緑にできない。skip / xfail にしてはならない。

- `test_self_consistent_arbitrary_wrapper_is_rejected_before_scheduler_effect`
- `test_self_consistent_arbitrary_executable_is_rejected_before_scheduler_effect`

具体的に `wrapper_path=/tmp/evil.py`、`wrapper_sha256=sha256(evil.py)` は live hash 検査を発火させない。拒否するには、running module、staging/build manifest、または別 authority との比較が必要であり、「caller 申告値との一致以上をしない」という P1 を超える。ここは実装せず親裁定へ返す。

## S-B — live git identity から roots を導出

### 実装箇所と述語

1. `tools/pegasus/t810_coordinator.py:22-27`

   `resolve_git_identity` と `git_identity_digest` を import する。

2. `tools/pegasus/t810_coordinator.py:496-515`

   `repository_roots_from_git_identity()` 後に `_live_repository_roots(document)` を追加する。

   ```python
   live = resolve_git_identity(document["validator_kwargs"]["repo_root"])
   live == document["validator_kwargs"]["approved_git_identity"]
   git_identity_digest(live)
       == document["validator_kwargs"]["approved_git_identity_sha256"]
   ```

   両方通った `live` だけを `repository_roots_from_git_identity(live)` へ渡す。

3. `tools/pegasus/t810_coordinator.py:1623-1630`、`coordinate()`

   caller identity から直接 roots を作る現行 `:1623-1625` を `_live_repository_roots(document)` に置換する。これは `_coordinate_authorized()`、ひいては `prepare_group():660-661` の mkdir より前に実行する。

   - 発火: live repo=`/work/.../dev-wave-t922...`、caller identity=`/tmp/fake-repo`
   - 非発火: `resolve_git_identity(repo_root)` の戻り値と digest をそのまま approved 値に使用
   - 攻撃例: `work_root=<live repo>/output/t810` でも、偽 `/tmp/fake-repo` を roots に使う前に拒否され、directory は作られない。

### テスト

- `orchestrator/tests/test_t810_coordinator.py::test_coordinate_rejects_forged_git_identity_before_output_effect`
  - output/work が作られていないことまで assert する。
  - 変異: live identity を使わず caller identity から roots を作る。
- `orchestrator/tests/test_t810_coordinator.py::test_live_git_identity_derives_current_and_linked_worktree_roots`
  - 既存 `test_git_common_dir_derives_main_and_sibling_worktree_roots` は caller-provided identity の単体検査なので置換せず補完する。

既存テストは `coordinate()` を正例で呼んでいないため直接の破壊はない。ただし共通 `_config():188-197` は `resolve_git_identity(repo)` と `git_identity_digest()` から実体化し、`.git` を directory と決め打ちしない形へ直す。

## S-C — guard / budget producer と実 ledger

### 実装可能: budget ledger の検証

1. `tools/pegasus/t810_budget.py:334-393, 486-574`

   `reserve_budget()` 後に `verify_admitted_receipt()` を追加する。入力は receipt、`BudgetRequest`、`AdmissionPolicy`、repository roots。flock 下で ledger を読み、次をすべて要求する。

   ```python
   sha256(current_ledger_bytes) == receipt["ledger_sha256_after"]
   last_event["reservation_id"] == receipt["reservation_id"]
   last_event["status"] == "reserved"
   last_event["launch_intent_sha256"] == receipt["launch_intent_sha256"]
   last_event["policy_sha256"] == receipt["policy_sha256"]
   last_event["run_kind"] == receipt["run_kind"]
   last_event["requested_attempts"] == receipt["requested_attempts"]
   last_event["amount_node_seconds"] == receipt["required_node_seconds"]
   sha256(ledger_without_last_event) == receipt["ledger_sha256_before"]
   ```

   `reservation_id` は expected request の `group_id/run_kind/attempt/launch_intent_sha256` から再導出する。

   - 発火: receipt after=`"b"*64`、実 ledger SHA-256=`"c"*64`
   - 非発火: `reserve_budget()` が返した receipt を、その append 直後の同じ ledger に照合
   - 発火: hash だけ合わせても末尾 event が別 reservation または `released`
   - 非発火:末尾が同一 reservation の `reserved`

2. `tools/pegasus/t810_coordinator.py:690-698`

   `_validate_budget_receipt()` 後、manifest publication `:704` より前に上記 verifier を呼ぶ。expected request は intent の group/run kind/attempt/node count/digest と prereg の retry 上限から構成する。

3. テスト

- `orchestrator/tests/test_t810_budget.py::test_admitted_receipt_verifier_requires_exact_current_ledger_bytes`
  - 変異: current ledger の hash を読まず receipt 値を自己比較する。
- `orchestrator/tests/test_t810_budget.py::test_admitted_receipt_verifier_requires_matching_last_reserved_event`
  - 変異: ledger の構造検査を `_parse_ledger()` だけで終える。
- `orchestrator/tests/test_t810_coordinator.py::test_prepare_group_rejects_budget_receipt_after_ledger_drift`
  - 変異: coordinator から verifier 呼出しを除去。

### 実装不能: guard producer の production 結線

現 config は `tools/pegasus/t810_coordinator.py:473-492` の 7 field のみで、guard の実入力がない。一方 `t810_guard.evaluate_parallel_guard()` は `tools/pegasus/t810_guard.py:333-337` で以下を要求する。

- qstat transcripts
- expected owner
- phase
- qsub 後なら B manifest job identities

さらに coordinator は pre-existing guard receipt を `prepare_group():686-689` で qsub 前に読むが、pre-release B identity は `submit_group():807-829` 後にしか存在しない。したがって receipt を producer 出力と再照合する preimage も、正しい実行順も現 interfaceにはない。

次のような「receipt を `GuardDecision` dataclass に詰め直すだけ」の実装は、偽 allow receipt をそのまま通すため禁止する。

完全実装には少なくとも次が必要であり、現 scope と「受理面を変えない」に抵触する。

- pre-submission / pre-release の別 snapshot provider
- qsub 後の submission identity から B manifest を構成
- `evaluate_parallel_guard()` の再実行と receipt exact equality
- pre-release deny 時の cancel / `withdraw_b_group()` 結線
- 2 guard phase の digest を保存する artifact/schema

条件付き API のテスト候補は
`test_guard_receipt_verifier_recomputes_from_original_snapshot`。変異は「再計算せず receipt を deserialize する」。ただし production snapshot provider の裁定前に API だけ追加すると再び non-test caller 0 件になるため、先行実装してはならない。

## S-D — coordinator artifact から wrapper CLI へ

### P3 の選択

**(b) 同 process で `t810_pbs_wrapper.main([...])` を呼ぶ。**

`subprocess` では wrapper core の load/process/hardware/quiet/measurement probe を安定して注入できず、test-only production 分岐が必要になる。S-D の境界は「生成 script → `--request` parser → 静的 request decode → runtime identity 補完」までとし、wrapper core は既存 `test_valid_wrapper_writes_ack_then_immediately_uses_single_measurement_seam` が担う。

### テスト実装

`orchestrator/tests/test_t810_coordinator.py:458-478` 後へ、次を追加する。

`orchestrator/tests/test_t810_coordinator.py::test_coordinator_artifact_enters_wrapper_main_with_runtime_identity`

1. `_prepared(tmp_path)` で coordinator が script と request を生成する。
2. script 最終行を `shlex.split()` し、実際に生成された `argv[2:]` を `W.main()` へ渡す。
3. `monkeypatch.setenv("PBS_JOBID", "81000.server")`。
4. `W.run_wrapper` だけを capturing fake に monkeypatchし、`WrapperOutcome("valid", (), (), False)` を返す。
5. captured request について次を exact assert する。

   ```python
   request.request_path == generated_request_path
   request.pbs_request_id == "81000.server"
   request.assigned_hostname == os.uname().nodename
   request.allocated_cpus == frozenset(os.sched_getaffinity(0))
   request.expected_submission_argv == tuple(slot["qsub_argv"])
   request.observed_submission_argv == tuple(slot["qsub_argv"])
   ```

`os.uname()` と `os.sched_getaffinity(0)` は正規 runtime identity seam なので monkeypatch しない。monkeypatch は、注入 seam のない深部 `run_wrapper` にだけ最後の手段として使う。

- 発火: `PBS_JOBID` 不在、script の `--request` 欠落、request 内 path と CLI path の不一致
- 非発火: `PBS_JOBID="81000.server"`、live affinity 非空、生成 path と request 自己束縛が一致
- 単独で殺す変異: `_canonical_job_script()` から `--request` と request path を削除

## 既存 fixture / test の波及

`orchestrator/tests/test_t810_coordinator.py:104-200` の `_config()` は次のように実体化する。

- `package/wrapper.py` に現行 `t810_pbs_wrapper.py` の実 bytes を置き、その SHA-256 を全 slot の `wrapper_sha256` に使用
- binary に execute bit を付け、実 hash を `binary_sha256` と validator の executable identity の双方へ使用
- live `GitIdentity` と digest を使用
- budget genesis と reservation event を実 `t810_budget` producer で構築し、実 receipt と ledger bytes を保存
- guard fixture は少なくとも `evaluate_parallel_guard()` の戻り値から作る。ただし production 再検証問題は閉じたと主張しない

この修正なしで壊れる coordinator test は以下。全 parameter case を含む。

- `test_prepare_group_dag_is_create_only_and_policy_hosts_are_ratified`
- `test_cli_and_effect_entries_deny_missing_or_wrong_witness`
- `test_ready_barrier_recomputes_raw_evidence`
- `test_canonical_wrapper_preflight_passes_ready_barrier`
- `test_submission_must_be_complete_before_barrier_and_timeout_boundary`
- `test_release_commitment_cancel_recheck_and_create_only`
- `test_start_spread_boundary_uses_only_coordinator_receipt_times`
- `test_ack_marker_mismatch_duplicate_unknown_and_missing_are_rejected`
- `test_start_ack_recomputes_pre_measurement_process_scan`
- `test_completion_state_rows_and_exact_n_receipts`
- `test_completion_rejects_orphan_unknown_duplicate_and_receiptless_submission`
- `test_node_receipt_hash_chain_and_actual_bytes_digest_are_enforced`
- `test_terminal_state_two_precedes_twelve_completion_reduction`
- `test_wait_for_node_files_uses_injected_clock_and_sleep`
- `test_subprocess_and_publication_effects_reject_raw_dict_token`
- `test_arbitrary_qsub_is_rejected_before_scheduler_effect`
- `test_modified_pbs_script_is_rejected_at_scheduler_effect`
- `test_terminal_reduced_checks_preserved_dropped_slot_presence`
- `test_guard_and_budget_receipts_are_typed_and_digest_bound`
- `test_authorized_production_core_uses_same_validator_twice_and_dormant_prereg`

追加の fixture 波及:

- `test_t810_pbs_wrapper.py:105-186` の `test_intent_manifest_producer_binds_prereg_policy_request_and_publication` は wrapper 実 file と実 hash を作る。
- `test_t810_harness_schema.py:8-34` の `_intent()` は exact `--request` argv にする。これを怠ると `test_positive_dag_documents_and_scheduler_schemas` と `test_launch_intent_exact_rejections[*]` が本来の mutation より前に落ちる。

期待値は一切緩めない。`H` を実 hash に置き換えるのは、検査を回避する動的期待値ではなく、fixture が主張する file identity を実在させる変更である。

## P2 所有検査

所有 file は排他になる。

| owner | 排他所有 |
|---|---|
| author-1 | `t810_harness_schema.py`, `t810_coordinator.py`, `t810_pbs_wrapper.py`, `test_t810_harness_schema.py`, `test_t810_coordinator.py`, `test_t810_pbs_wrapper.py` |
| author-2 | `t810_guard.py`, `t810_budget.py`, `test_t810_guard.py`, `test_t810_budget.py` |

ただし author-1 の S-C coordinator 結線は author-2 の verifier API に依存するため、完全並列にはしない。author-2 の APIと単体テストを先行し、その patch を author-1 worktree へ展開してから author-1 を起動する。guard producer 結線が未裁定の間、author-2 に dead API を書かせない。

静的検査のみで、pytest は実走していない。admission policy の `unratified` 状態には触れない。

## 総括

1. **実装順序:** まず P1 と S-C guard 入力不足を親が裁定し、次に author-2 の budget verifier、author-1 の fixture 実体化 → S-A → S-B → S-D → 許可された S-C 結線の順とする。

2. **最大のリスク:** guard の raw evidence と qsub 後 identity が現 interface に無いまま「producer 結線済み」とすること。形式 validator の移設では偽 allow receipt を閉じられない。

3. **撤回すべき provisional:** **P1 の「これで任意 wrapper / executable identity まで閉じる」という裁定は撤回すべき。** live hash 不一致拒否だけは実装できるが、自己整合した任意 bytes の拒否には caller 外 authority が必要である。