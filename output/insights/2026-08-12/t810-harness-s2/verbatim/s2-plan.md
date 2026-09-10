# 実装プラン案

結論として、共有 schema を先行させ、子 A/B/C は新規 `t810_*` module 群で実装する。既存コード変更は policy registry の 1 行追加だけとし、`t810_prereg_v1.json`、`dispatch_compute.py`、`mutation_fanout.py`、既存 validator の受理集合には触れない。

静的確認のみ実施し、pytest・qsub・qstat の実走およびファイル書込みは行っていない。

## 固定する設計境界

- `tools/pegasus/policies/t810_prereg_v1.json` は raw bytes digest が承認 receipt に束縛されるため、一切変更しない。`load_t810_preregistration()` と dormant seal も変更しない（`orchestrator/campaign/t810_preregistration.py:758-803`）。
- `dispatch_compute.py` と `mutation_fanout.py` は private 関数を直接流用せず、exact parser、create-only receipt、authority hash の設計パターンだけ参照する。
- coordinator は既存 `validate_t810()`（`orchestrator/campaign/t810_validator.py:1340-1361`）を投入前後で同じ引数契約のまま呼ぶ。validator 本体は変更しない。
- work/output/control root、PBS `-o/-e`、qsub cwd はすべて repo 外絶対 path。測定ノードへ送る package は binary、standalone wrapper、runner policy、schema module だけとする。
- 実行可能 CLI は `request_t810_launch()` を scheduler 呼出しより先に通すため、本 slice のままでは dormant seal により qsub へ到達しない。fixture 用 scheduler seam は内部関数にだけ置く。
- 要件: protocol §3.3、§3.4、§6.1–§6.3、§9.1 item 1、不変条件 1–5。

## 共通先行単位 S — schema と記録形式

### 新規ファイル

| 予定箇所 | 責務・public API 案 | 想定規模 | 対応要件 |
|---|---|---:|---|
| `tools/pegasus/t810_harness_schema.py:1-420` | stdlib-only の exact schema、canonical JSON、authority digest。`canonical_json_bytes(value) -> bytes`、`validate_group_manifest(value, *, expected_prereg_sha256) -> GroupManifest`、`group_authority_sha256(value) -> str`、`validate_node_event(...) -> NodeEvent`、`validate_terminal_state(...) -> TerminalState` | 約420行 | §3.3、§5.4、§6.2、§9.1(a) |
| `orchestrator/tests/test_t810_harness_schema.py:1-340` | field 過不足、型、hash、順序、重複、state-dependent field の静的単体検査 | 約340行 | §5.4、§6.2 |
| `orchestrator/tests/fixtures/t810/scheduler_transcripts_v1.json:1-240` | 保存済み qsub/qstat 応答。command、rc、stdout、stderr を scenario ごとに保持し、実 scheduler を呼ばない | 約240行 | §8、§9.1(f) |

### schema field set

すべて `mutation_fanout.py:826-843,873-927` の `_exact_object` 型で、`set(actual) == expected_fields` を必須にする。未知 field、欠損 field、`bool` を整数として扱う入力、重複 ID、非正規 path、symlink は拒否する。

1. `t810-group-manifest/v1`

   - root: `schema_version`, `group_id`, `run_kind`, `attempt_ordinal`, `preregistration_sha256`, `prereg_approval_id`, `created_at`, `node_count`, `round_count`, `ready_timeout_seconds`, `start_spread_max_ns`, `approved_hostnames`, `work_root`, `output_root`, `pre_submission_guard_sha256`, `budget_receipt_sha256`, `slots`
   - slot: `slot_id`, `logical_request_id`, `job_name`, `qsub_argv`, `wrapper_argv`, `pbs_stdout_path`, `pbs_stderr_path`, `binary_source_path`, `binary_sha256`, `wrapper_path`, `wrapper_sha256`, `runner_policy_path`, `runner_policy_sha256`
   - cross-check: slot は `slot-00..N-1` の連続順、logical request/job name/path は一意、N/R と timeout は verified preregistration および生死確認 literal に一致、全 path は repo 外絶対 path。
   - manifest は最初の scheduler seam 呼出し前に create-only で確定し、その canonical SHA-256 を以降の全 receipt に束縛する。
   - 要件: §3.3 items 1–4、§8、§9.1(a)。

2. `t810-submission-receipt/v1`

   - root: `schema_version`, `group_manifest_sha256`, `created_at`, `requests`
   - request: `slot_id`, `logical_request_id`, `job_name`, `qsub_argv`, `qsub_rc`, `qsub_stdout`, `qsub_stderr`, `pbs_request_id`
   - N entry exact。部分投入失敗でも全 slot entry を残し、未投入分は `pbs_request_id=null` として `pre_release_invalid` へ倒す。
   - 要件: §3.3 item 1、§5.4 state 1、§6.2。

3. `t810-control-marker/v1`

   - fields: `schema_version`, `group_manifest_sha256`, `group_id`, `kind`, `published_at`, `nonce`
   - `kind ∈ {release,start-permit,cancel}`。create-only、相互に矛盾する marker は fail-closed。
   - marker は repo 外 `work_root/control/` に置き、成果物 exact set の `output_root` には混入させない。
   - 要件: §3.3 items 4–5, 7、§5.4。

4. `t810-node-event/v1`

   - envelope: `schema_version`, `group_manifest_sha256`, `group_id`, `slot_id`, `logical_request_id`, `pbs_request_id`, `sequence`, `event`, `observed_at`, `previous_event_sha256`, `payload`
   - `preflight` payload: `assigned_hostname`, `actual_hostname`, `hardware`, `interpreter`, `competing_processes`, `quiet_samples`, `binary_source_sha256`, `binary_copy_sha256`, `dependency_manifest_sha256`, `module_list_sha256`, `trace_symbols`, `isolation_before`, `submission_argv_match`, `repo_absence`, `passed`, `reason_codes`
   - `hardware`: `cpu_model`, `physical_cores`, `hyperthreading`, `memory`, `numa_nodes`, `cache`, `frequency_policy`
   - `start_ack`: `release_marker_sha256`, `cancel_marker_absent`, `ack_nonce`
   - `measurement`: `rounds`, `benchmark_rc`, `binary_after_sha256`, `isolation_after`
   - round: `index`, `started_at`, `ended_at`, `effective_clock`, `throughput`, `exit_code`
   - `terminal`: `state`, `reason_codes`, `measurement_started`, `completed_rounds`
   - event は slot ごとの append-only hash chain とし、最終 terminal event をちょうど 1 件要求する。
   - 要件: §3.3 item 2、§3.4、§5.4、§6.2、§8。

5. `t810-coordinator-event/v1`

   - envelope: `schema_version`, `group_manifest_sha256`, `sequence`, `event`, `wall_time`, `coordinator_monotonic_ns`, `slot_id`, `previous_event_sha256`, `details`
   - event-specific details:
     - `manifest_committed`: `manifest_sha256`
     - `ready_received`: `receipt_sha256`, `accepted`, `reason_codes`
     - `release_published`: `marker_sha256`
     - `start_ack_received`: `receipt_sha256`, `received_monotonic_ns`, `latency_ns`
     - `start_permit_published` / `cancel_published`: `marker_sha256`, `reason_codes`
     - `completion_received`: `receipt_sha256`, `accepted`, `reason_codes`
     - `terminal_decided`: `terminal_state_sha256`
   - 要件: §3.3 item 5、§5.4、§6.2。

6. `t810-terminal-state/v1`

   - fields: `schema_version`, `group_manifest_sha256`, `attempt_ordinal`, `state`, `reason_codes`, `release_event_sha256`, `start_spread_ns`, `completed_slot_ids`, `dropped_slot_ids`, `node_receipt_sha256_by_slot`, `expected_presence`, `actual_presence`, `presence_valid`, `pre_validator_receipt_sha256`, `post_validator_receipt_sha256`, `retry_allowed`
   - state は preregistration と同じ 5 値だけ。nullable field と presence matrix は state ごとに exact に固定する。
   - 要件: §5.4、§6.2–§6.3。

## 子 A — coordinator、barrier、終端 verifier

### 新規ファイル

| 予定箇所 | 責務・public API 案 | 想定規模 | 対応要件 |
|---|---|---:|---|
| `tools/pegasus/t810_coordinator.py:1-560` | group 準備、ready barrier、release/cancel、開始応答、completion verifier。`prepare_group(config, preregistration) -> GroupManifest`、`evaluate_ready_barrier(...) -> BarrierDecision`、`verify_completion(...) -> TerminalState`、`main(argv=None) -> int` | 約560行 | §3.3、§5.4、§8、§9.1(a) |
| `orchestrator/tests/test_t810_coordinator.py:1-700` | state machine、timeout、coordinator clock、orphan、validator 結線、dormant seal | 約700行 | §3.3、§5.4、§6、§8 |

### 実装内容

- `prepare_group()` は preregistration の digest/literal、子 B の canonical qsub plan、子 C の admission receipt を照合し、全 logical request を含む manifest を scheduler 呼出し前に create-only 生成する。
- qsub が返す PBS ID は immutable manifest を書き換えず、`submission-receipt.json` で logical request と束縛する。`mutation_fanout.py:1457-1465` の「group を先に確定し、authority hash を取る」順序を踏襲する。
- ready barrier は N receipt の slot/request/manifest hash、hostname、approved-host membership、binary hash、preflight pass を exact に検査する。hostname の異なり数が N でない場合は release を作らず cancel を作る。
- ready deadline は fake clock で判定し、`elapsed < 1200s` のみ待機、`>=1200s` で cancel。後発 wrapper は measurement 直前にも cancel を再確認する。
- release 後は各 wrapper が `start_ack` を書いて `start-permit` を待つ。coordinator は自身の `monotonic_ns()` だけで `max(ack_received_ns) - release_published_ns` を計算し、`<=5s` のときだけ permit を発行する。超過時は release 記録を残して cancel し、`post_release_pre_measurement_invalid` とする。
- completion verifier は manifest slot 集合と receipt/file 集合を突合し、`mutation_fanout.py:966-1084` と同様に orphan receipt、未知 slot、receipt 無し submission を拒否する。
- terminal 判定は §5.4 の上から first-match:
  1. release 前不成立
  2. release 後・measurement 前不成立
  3. measurement 後の欠損・integrity 不成立
  4. N−1 slot が全 R 完了
  5. N slot が全 R 完了
- retry は状態 1 のみ `attempt_ordinal < 2` を返す。coordinator 自身は自動再投入せず、全 attempt receipt を保存する。
- `validate_t810()` を pre/post で同一 callable として呼び、pre baseline を post へ渡す。いずれか不合格なら性能値に関係なく該当 invalid state へ倒す。
- executable CLI は prereg loader と `request_t810_launch()` を最初に通す。内部 `_coordinate_authorized(..., scheduler_run, clock_ns)` だけが fixture seam を持ち、CLI 引数から seam を差し替えられない。
- 要件: §3.3 items 1–8、§5.4、§6.2–§6.3、§8、§9.1(a)。

### テスト

- manifest が fake scheduler の最初の call より前に存在し、N logical request と全 qsub argv を含む。
- ready N 件、1 件不足、重複 hostname、未承認 hostname、assigned/actual mismatch、receipt hash mismatch。
- 1200 秒境界、cancel の create-only 性、cancel 後に遅着した ready が release を起こさない性質。
- coordinator clock の 5 秒ちょうど／5 秒+1ns。node 側 monotonic 値を改変しても判定が変わらないこと。
- 5 state の順序、N/N−1/N−2、round 欠損、追加 round、重複 slot、orphan receipt、symlink/socket/余分な file。
- pre/post validator が各 1 回かつ同じ実装へ接続され、不合格時に estimator へ進まないこと。
- CLI は dormant seal で scheduler bomb seam より先に停止する。
- fixture は `RecordedScheduler.__call__(argv, *, cwd, env) -> CompletedProcess[str]` が exact argv/cwd を照合して保存済み応答を返し、qsub/qstat は実行しない。
- 要件: §3.3、§5.4、§6、§8。

## 子 B — PBS wrapper、runner mediation、repo 不在

### 新規ファイル

| 予定箇所 | 責務・public API 案 | 想定規模 | 対応要件 |
|---|---|---:|---|
| `tools/pegasus/t810_runner_policy.py:1-230` | 測定 executable/argv の単一 mediation 点。`validate_measurement_argv(policy, executable, argv) -> tuple[str, ...]`、`run_allowed_measurement(..., runner=...) -> CompletedProcess[str]` | 約230行 | §6.1、§6.3、§9.1(c) |
| `tools/pegasus/t810_pbs_wrapper.py:1-540` | canonical qsub/script 生成と node-side preflight/測定。`canonical_qsub_argv(slot) -> tuple[str, ...]`、`render_pbs_script(slot) -> bytes`、`run_wrapper(request, *, probes, measurement_run) -> NodeTerminal` | 約540行 | §3.4、§6.1、§8、§9.1(b)(d2) |
| `orchestrator/tests/test_t810_runner_policy.py:1-300` | allowlist の正例 1 本と拒否面 | 約300行 | §6.1、§9.1(c) |
| `orchestrator/tests/test_t810_pbs_wrapper.py:1-650` | preflight、静穏 gate、binary copy、receipt、repo 不在、qsub 正規形 | 約650行 | §3.4、§6、§8 |

### 実装内容

- qsub argv は次の順序まで exact に固定する。

  ```text
  qsub -A <project> -q <queue> -b 1
       -l elapstim_req=<frozen-walltime>
       -N <manifest-job-name>
       -o <absolute-external-stdout>
       -e <absolute-external-stderr>
       <absolute-external-script>
  ```

  coordinator の cwd も external submission dir とし、実 argv と manifest の配列一致を receipt に記録する。既存 `dispatch_compute.py:1475-1488` は参照のみで、`-o/-e` のない既存形を変更・流用しない。

- PBS script は `python3.10 -I -B` を明示し、realpath と `3.10` version を検証する。repo path、`PBS_O_WORKDIR` 由来の repo path、calibration/floor/oracle/certify entrypoint を埋め込まない。
- node-side package は standalone schema、wrapper、runner policy、binary、dependency manifest のみ。wrapper は cwd、work/output/control root、binary/runner の全 ancestor に `.git` file/dir がないことを検査し、検出時は `pre_release_invalid` receipt を閉じる。
- competing process scan は `/proc` から「同一 UID かつ wrapper の process tree 外で、割当て CPU affinity と交差する process」を記録・拒否する。system daemon を曖昧な command-name allowlist で除外しない。
- quiet gate は注入可能な `load1_reader`、`sleep`、`monotonic_ns` を使い、`load1 <= 1.0` を30秒間隔で3連続、最大1200秒。実テストでは fake clock/sleep のみ使用する。
- binary は external shared stage から node-local scratch へ copyし、source hash、copy 直後 hash、測定後 hash を照合する。不一致の発生境界に応じて §5.4 の state/reason を返す。
- hardware、interpreter、hostname、process、quiet、binary、dependency/module/trace、isolation を一つの preflight payload に束ねる。trace symbol が1件でもあれば測定しない。
- benchmark 起動は `run_allowed_measurement()` だけを通す。許可形は「manifest が束縛した executable realpath + `measurement.canonical_benchmark_argv` の完全一致」だけ。shell string、prefix/suffix、順序変更、追加 option、symlink executable は拒否する。
- wrapper は release を見て start_ack を書いた後も、cancel と start-permit を確認するまで benchmark を起動しない。
- 要件: §3.4、§5.4、§6.1–§6.3、§8、§9.1(b)(c)(d2)。

### テスト

- `-o/-e`、script、cwd が repo 外絶対 pathで、manifest/receipt と argv が byte-for-byte 一致。
- generated script/package に repo absolute path、calibration/certify、trace-enabled symbol がない。
- `.git` directory、`.git` file/worktree marker、repo alias、repo 内 PBS workdir をすべて release 前に拒否。
- assigned hostname と実 hostname の一致／不一致、hardware 7 field の欠損・余分 field。
- load `1.0` 境界、非連続 pass、3連続 pass、1200秒 timeout。実 sleep は行わない。
- competing process、binary copy 前後、dependency/module/NUMA/trace、isolation after の各失敗状態。
- runner allowlist の正例 exact 1形と、並べ替え・追加引数・別 executable・shell・symlink・certify 系の拒否。
- AST tripwire で wrapper に `subprocess.run/Popen`、`os.system` 等の別 mediation 点を増やさない。
- 各 failure path が exact terminal node event を残し、性能値を出さない。
- 要件: §3.4、§5.4、§6、§8。

## 子 C — 並走ガードと予算 admission

### 新規ファイル

| 予定箇所 | 責務・public API 案 | 想定規模 | 対応要件 |
|---|---|---:|---|
| `tools/pegasus/t810_guard.py:1-450` | exact qstat job parser、A優先判定、B取消。`parse_qstat_jobs(text, *, expected_owner) -> tuple[SchedulerJob, ...]`、`evaluate_parallel_guard(...) -> GuardDecision`、`withdraw_b_group(..., scheduler_run) -> GuardReceipt` | 約450行 | §9.1(f)、§9.3 |
| `tools/pegasus/t810_budget.py:1-400` | policy loader、external ledger、atomic reservation。`load_admission_policy(path) -> AdmissionPolicy`、`reserve_budget(request, *, ledger_path, clock) -> BudgetReceipt`、`finalize_budget(...) -> BudgetEvent` | 約400行 | §9.1(g)、§9.1 items 4/8 |
| `tools/pegasus/policies/t810_admission_v1.json:1-90` | `parallel_guard` と `budget` の機械可読 policy。raw-byte approval artifact にはしない | 約90行 | §9.1(f)(g)、§9.3 |
| `orchestrator/tests/test_t810_guard.py:1-560` | qstat ambiguity/unknown state/A優先/取消 identity | 約560行 | §9.1(f)、§9.3 |
| `orchestrator/tests/test_t810_budget.py:1-480` |式、ledger破損、競合 reservation、境界 | 約480行 | §9.1(g) |

### (f) exact parser と A 系優先

qstat block では `Job Id:`, `Job_Owner =`, `job_state =`, `Job_Name =`, `queue =`, `exec_host =` を critical field とし、それぞれ exactly once を要求する。未知の追加表示 field はデータとして無視せず raw digest に残すが、critical field の重複・欠損・矛盾、request ID mismatch は snapshot 全体を invalid にする。

状態語彙は既存コードで実在が確認できる `Q/H/R` のみを `QUE/HLD/RUN` に写像する（`mutation_fanout.py:1112-1119`）。それ以外は terminal と推測せず `unknown-job-state` で admission を拒否する。対象 B job の取消は manifest の PBS ID、owner、job name と fresh qstat が全一致した場合だけ `qdel <id>` を scheduler seam へ渡す。

ガードは2回行う。

1. manifest/qsub より前に fresh snapshot を取り、A job または parser uncertainty があれば admission を拒否する。
2. 全 B job が ready になった後、release 直前に再取得する。A job出現、B同士の host 重複、identity mismatch があれば cancel marker を先に作り、Aには触れずBだけを取り下げる。

`GuardReceipt` の exact fields は `schema_version`, `group_manifest_sha256`, `phase`, `policy_sha256`, `snapshot_sha256`, `a_series_identity_status`, `a_series_jobs`, `co_location_conflicts`, `decision`, `reason_codes`, `b_request_ids`, `withdrawal_actions`, `created_at`。各 withdrawal action は `pbs_request_id`, `job_name`, `state`, `identity_match`, `qdel_argv`, `qdel_rc` を持つ。

要件: §9.1(f)、§9.3。

### T-139 の識別入力

現時点では **未特定・裁定要**。

- qstat から使える実在 field は `Job_Name`（`mutation_fanout.py:1115-1119`）。
- 汎用 dispatch の job name は `izdw-<submission nonce先頭10字>` だけで（`dispatch_compute.py:429-432`）、T-139 identity を含まない。
- fanout の receipt も同じ `izdw-*` 規約との一致しか検査しない（`mutation_fanout.py:1193-1200`）。
- 既存 T-139 probe の PBS header（`tools/pegasus/probes/t139_positive_control_probe.pbs:1-5`、`t139_r4_env_probe.pbs:1-5`）には `#PBS -N` がない。PBS の暗黙 default 名を将来の pilot/本走識別規約として扱うことはできない。
- したがって `parallel_guard.a_series_identity` は当初 `status: unresolved`, `field: Job_Name`, `pilot_patterns: []`, `main_patterns: []` とし、guard は `priority-identity-unresolved` で常時 deny する。
- 裁定後は T-139 所有側が明示的な anchored job-name 規約を定め、その exact pattern を policy に入れる。既存 dispatch/fanout を T-810 側から変更する提案はしない。

要件: §9.1(f)、§9.3、不変条件 5。

### (g) admission policy field 案

`t810-admission-policy/v1` の exact top-level fields は `schema_version`, `parallel_guard`, `budget`。

`budget` fields:

- `status`
- `accounting_unit`（`node-seconds`）
- `total_node_seconds`
- `estimates`
- `attempt_policy`
- `ledger`
- `admission`

`estimates` は exact key `builder`, `liveness`, `main`。各 entry は `walltime_seconds`, `jobs_per_attempt`, `node_seconds_per_attempt` を持ち、次を cross-checkする。

```text
node_seconds_per_attempt
  = walltime_seconds × jobs_per_attempt
```

`attempt_policy` は `builder_attempts`, `liveness_max_attempts`, `main_max_attempts_ref`。main の上限は verified preregistration の `terminal.retry.max_attempts == 2` と一致させ、caller が小さい値を自由入力して budget を過小評価できないようにする。

`ledger` は `schema_version`, `location`, `lock_method`, `counted_statuses`。location は `repository-external`、lock は同一 external root 上の `flock`。canonical ledger は JSONL append-only とする。

ledger entry fields:

- `schema_version`, `sequence`, `event_id`, `reservation_id`, `group_id`, `run_kind`, `requested_attempts`, `estimate_per_attempt_node_seconds`, `amount_node_seconds`, `status`, `created_at`, `previous_sha256`, `policy_sha256`

status は `reserved`, `consumed`, `released` の exact FSM。qsub が1件でも受理された attempt は保守的に全 frozen estimate を `consumed` とし、scheduler 未到達時だけ release を許す。

budget receipt fields:

- `schema_version`, `policy_sha256`, `ledger_path`, `ledger_sha256_before`, `ledger_sha256_after`, `reservation_id`, `run_kind`, `requested_attempts`, `estimate_per_attempt_node_seconds`, `required_node_seconds`, `total_node_seconds`, `counted_node_seconds`, `remaining_node_seconds`, `admitted`, `reason`, `created_at`

admission 式は整数演算で次に固定する。

```text
required  = Σ(frozen_estimate_per_attempt[k] × requested_attempts[k])
remaining = total_node_seconds − Σ(active reserved/consumed amount)
admit     = ledger/policy/request が exact-valid
            AND 0 <= required <= remaining
```

入力の所在は次のとおり。

- 凍結見積り: policy の `estimates.*`。その canonical semantic digest を group manifest と budget receipt に束縛する。
- attempt 数: builder/liveness launch request と、main は preregistration の最大 attempt 数。
- 残枠: repo 外 ledger の valid な最新 FSM。
- 総枠: policy の `total_node_seconds`。
- builder + 生死確認、本走最大 attempt の複合要求は上式の和で予約する。

この policy は registry 管理するが、preregistration のような raw bytes approval loader は新設しない。「凍結」は各 reservation receipt に semantic digest と数値をコピーして、その admission 後に差し替えられないという意味に限定する。

要件: §5.4 retry、§9.1 items 4/8、§9.1(g)。

### テスト

- 保存済み qstat fixture: Q/H/R、複数 block、重複 critical field、別 owner、別 request ID、未知 state、欠損 Job_Name、wrapped exec_host。
- identity unresolved は job が0件でも deny。裁定済み synthetic policy では pilot/main name のみ A と分類。
- pre-submission pass 後に pre-release fixture で A が出現した race、cancel-before-qdel、Bだけを exact ID で取消。
- qdel identity mismatch、unknown state、非ゼロ rc は release 不可の receipt を残す。
- budget の `<`, `==`, `>` 境界、負数、bool、overflow相当巨大値、policy digest mismatch。
- ledger の sequence gap、hash chain破損、二重 reservation、未知 status、途中行、同時 reservation を fail-closed。
- fake scheduler/ledger/clock のみ使い、qstat/qdel/qsub は実行しない。
- 要件: §9.1(f)(g)、§9.3。

## 既存ファイルへの変更

| file:line | 変更 | 理由・対応要件 |
|---|---|---|
| `tools/pegasus/policies/registry_v1.json:8-9` | sort 順を維持して `tools/pegasus/policies/t810_admission_v1.json` を1行追加 | 新規 policy を inventory gate に結線。§9.1(f)(g)、brief 不変条件4 |

`orchestrator/tests/test_pegasus_policy_registry.py` は変更しない。同 test は `:18-21` で policy directory と registry を正本化しているため、既存 inventory 検査をそのまま利用する。

以下は変更しない。

- `tools/pegasus/policies/t810_prereg_v1.json`
- `orchestrator/campaign/t810_preregistration.py`
- `orchestrator/campaign/t810_validator.py`
- `tools/pegasus/dispatch_compute.py`
- `tools/mutation_fanout.py`
- `orchestrator/campaign/queue_state.py`

要件: brief 不変条件 1、2、4、5。

## 実装順序と依存

1. 共通 S の schema、canonical digest、recorded scheduler fixture を先行実装する。
2. 子 A は shared schema と抽象 `SchedulerRun` / `AdmissionEvidence` interface だけで coordinator FSM を実装する。
3. 子 B と子 C は shared schema 後に並行実装できる。B は canonical qsub/slot plan、C は guard/budget receipt を返す。
4. B/C 完了後、A に `SlotPlan`、pre-submission guard、budget reservation、pre-release guard を結線する。
5. dormant CLI、pre/post `validate_t810()`、exact presence verifier、registry inventory を統合検査する。
6. acceptance は全 scheduler 操作を transcript seam に差し替える。生死確認を含む実 qsub は後続の承認済み wave に残す。

依存関係は `共有 schema → {A core, B, C} → A integration`。A/B/C から既存 dispatch/fanout の private API へ依存させない。

## 総括

- 新規 standalone schema を先行し、A/B/C は既存挙動を変えず新規 `t810_*` module で閉じる。
- qsub/qstat は保存済み transcript と injection seam だけで検査し、この wave では投入しない。
- manifest、receipt、ledger は exact field、canonical hash、create-only／append-onlyで束縛する。
- repo 非流入は external root、repo-free package、node 上 `.git` 不在、単一 runner mediation で閉じる。
- 既存変更は admission policy の registry 1行だけで、preregistration bytes は不変。
- 裁定要1: T-139 pilot／本走の明示的 `Job_Name` 規約が存在せず、解決まで guard は常時 deny。
- 裁定要2: budget の総 node-seconds と builder/liveness/main の walltime 見積り値が brief にない。
- 疑義: §3.3 の「request ID」が事前生成 logical ID でなく PBS ID を意味するなら、qsub 前 manifest 要件と両立しない。
- 疑義: 開始ばらつきを `max(ack受領)−release` でなく `max−min` とする意図なら式の明示裁定が必要。