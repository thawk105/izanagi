# 実装プラン

結論として、新規 8 ファイルと policy registry 1 箇所の純増で構成する。凍結 artifact は canonical JSON の bytes 自体を SHA-256 で固定し、runner と validator は digest 検証済みの immutable object しか受け取らない。

親裁定では P2・P3 に賛成する。一方、P1 の「`.claude/` 全体を除外」には反対する。§6.3 の ignored-untracked 全走査を弱めるためである。

実装・テスト実行・ファイル変更は行っていない。

## 1. 変更ファイル

新規ファイルにはまだ実在行番号がないため、以下の `new:Lx-Ly` は実装時のブロック順を示す予定範囲である。

| ファイル | 予定位置 | 責務 |
|---|---:|---|
| `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/t810_prereg_v1.json` | new:L1-L410 | 単一の凍結事前登録 artifact。測定面、build-preimage 要求、閾値、設計、推定式、判定表、終端状態、期待ファイル集合、argv 契約を保持 |
| `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_preregistration.py` | new:L1-L420 | canonical JSON、digest pin、厳密 schema 検証、immutable projection、presence rule の展開 |
| `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_runner_policy.py` | new:L1-L230 | runner 自身の argv と、CCBench に渡す完全 argv の allowlist |
| `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py` | new:L1-L700 | §6.3 の 5 検査を一括実行する唯一の validator 本体 |
| `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/validate_t810.py` | new:L1-L120 | `pre` / `post` を同じ実装へ dispatch する薄い CLI |
| `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_preregistration.py` | new:L1-L420 | artifact、digest、schema、presence projection のテスト |
| `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_runner_policy.py` | new:L1-L280 | argv allowlist と calibration 拒否のテスト |
| `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_validator.py` | new:L1-L750 | root、inventory、ignored file、manifest、namespace、終端状態、CLI のテスト |

既存ファイルの変更は次だけに限定する。

- [tools/pegasus/policies/registry_v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/registry_v1.json:3) の `policy_paths` に `tools/pegasus/policies/t810_prereg_v1.json` をソート順で追加する。既存閉集合テストは registry と policy directory の一致を要求している。
- [durable_root.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/durable_root.py:20) は変更しない。`DurableRootPolicy`、`ApprovedRoot`、`WriteCapability`、[resolve_policy_root](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/durable_root.py:196) を新規 module から利用する。
- [test_durable_root.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_durable_root.py:30) も変更しない。`tmp_path`、symlink escape、mount 境界の書き方だけを新規テストで踏襲する。

## 2. 公開 API とデータ構造

### `t810_preregistration.py`

予定 API:

```python
PREREG_PATH: Path
T810_PREREG_SHA256: str

class T810PreregistrationError(ValueError): ...

@dataclass(frozen=True)
class VerifiedT810Preregistration:
    sha256: str
    measurement: MeasurementContract
    build_preimage: BuildPreimageContract
    coordination: CoordinationContract
    design: DesignContract
    estimator: EstimatorContract
    decisions: tuple[DecisionRule, ...]
    terminal_states: tuple[TerminalRule, ...]
    artifacts: ArtifactContract
    runner: RunnerContract

def load_t810_preregistration(
    path: Path = PREREG_PATH,
) -> VerifiedT810Preregistration: ...

def expected_attempt_layout(
    prereg: VerifiedT810Preregistration,
    evidence: TerminalEvidence,
) -> ExpectedLayout: ...
```

`VerifiedT810Preregistration` の nested collection も tuple、frozenset、frozen dataclass に変換し、元の mutable `dict` は公開しない。公開 loader から expected digest を上書きできる引数は出さない。

### `t810_runner_policy.py`

予定 API:

```python
class T810RunnerPolicyError(ValueError): ...

@dataclass(frozen=True)
class T810RunnerInvocation:
    slot_id: str
    binary: Path
    output_root: Path
    frozen_manifest: Path
    prereg_sha256: str

@dataclass(frozen=True)
class ApprovedMeasurementCommand:
    executable: Path
    executable_sha256: str
    argv: tuple[str, ...]

def parse_t810_runner_argv(
    argv: Sequence[str],
    prereg: VerifiedT810Preregistration,
) -> T810RunnerInvocation: ...

def build_benchmark_argv(
    prereg: VerifiedT810Preregistration,
) -> tuple[str, ...]: ...

def validate_executed_commands(
    records: Sequence[ExecutionRecord],
    prereg: VerifiedT810Preregistration,
    frozen_manifest: FrozenManifest,
) -> tuple[ApprovedMeasurementCommand, ...]: ...
```

runner に N、R、workload、thread 数を変更する CLI option は与えない。これらは artifact からのみ取得する。`--certify`、`--workload`、`--threads`、`--reps`、`--` passthrough、shell command 文字列は unknown option として拒否する。

CCBench の完全 argv は次の順序に固定する。

```text
<verified-binary>
-thread_num=48
-ycsb_tuple_num=1000000
-extime=3
-clocks_per_us=2100
-ycsb_rratio=50
-ycsb_zipf_skew=0.9
-ycsb_rmw=0
```

`R=10` は runner がこの argv を 10 回実行する契約であり、CCBench に追加 flag として渡さない。protocol にない `-ycsb_max_ope`、`perf` wrapper、numactl、環境変数 prefix も拒否する。

### `t810_validator.py`

主要データ構造:

```python
@dataclass(frozen=True)
class FileRecord:
    path: str
    kind: Literal["regular", "directory", "symlink", "gitlink"]
    mode: int
    size: int
    sha256: str | None
    mtime_ns: int
    symlink_target: str | None

@dataclass(frozen=True)
class RepositorySnapshot:
    head: str
    git_index: tuple[GitIndexEntry, ...]
    porcelain_v2: bytes
    files: tuple[FileRecord, ...]

@dataclass(frozen=True)
class ValidatorSnapshot:
    schema_version: str
    prereg_sha256: str
    repository: RepositorySnapshot
    protected_inventory: tuple[FileRecord, ...]
    frozen_members: tuple[FileRecord, ...]
    execution_records_sha256: str
    snapshot_sha256: str

@dataclass(frozen=True)
class ValidationFinding:
    code: str
    path: str | None
    detail: str
    terminal_override: str

@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    findings: tuple[ValidationFinding, ...]
    terminal_override: str | None
```

公開入口は一つにする。

```python
def validate_t810(request: ValidationRequest) -> ValidationResult: ...
```

`pre` と `post` は `ValidationRequest.mode` だけを変え、repo scan、protected inventory、manifest、namespace、argv の検査関数は同じものを呼ぶ。

root policy helper は次を行う。

```python
def approve_t810_writable_root(
    *,
    repo_root: Path,
    writable_root: Path,
) -> ApprovedRoot: ...
```

- 両 path を strict realpath 化。
- 同一、`writable_root` が repo 配下、repo が `writable_root` 配下、symlink をすべて拒否。
- `approved_roots=(writable_root,)`、`forbidden_roots=(repo_root,)` とする。
- capability は T-810 の具体的な `control/<attempt-id>` または `attempts/<attempt-id>` を root として取得する。repo の祖先のような広い capability は発行しない。

これは既存 API が「candidate は forbidden root 配下か」しか見ず、approved candidate が repo の祖先である場合を単独では拒否できないために必要である。

## 3. 凍結 artifact の field 対応

数値のうち統計的な小数は JSON number にせず canonical decimal string とする。例えば `0.6%` は `"0.006"`、`0.9` は `"0.9"`。bool と整数は JSON bool/int を使う。

### identity

- `/schema_version = "pegasus-t810-preregistration/v1"`
- `/protocol/id = "T-810"`
- `/protocol/source = "docs/pegasus-node-variance-protocol.md"`
- `/protocol/run_authorized = false` — protocol 7–9 行、450–452 行。「land は投入許可ではない」。
- `/digest/canonicalization = "izanagi-t810-canonical-json/v1"`
- `/digest/algorithm = "sha256"`

### §2 測定 literal

[protocol §2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/docs/pegasus-node-variance-protocol.md:104) との対応は次のとおり。

- `/measurement/binary/benchmark = "CCBench-Silo"`
- `/measurement/binary/trace_enabled = false`
- `/measurement/ccbench_commit = "d706650cdb31e442bef45b9b4216951d4fb40969"`
- `/measurement/environment/generation = "pegasus-generation-2"`
- `/measurement/environment/contract_sha256 = "1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1"`
- `/measurement/build/build_type = "Release"`
- `/measurement/build/sanitizer_enabled = false`
- `/measurement/build/trace_enabled = false`
- `/measurement/build/backoff_enabled = false`
- `/measurement/build/fixed_backoff = -1`
- `/measurement/build/validation_no_wait = true`
- `/measurement/build/tictoc_no_wait = false`
- `/measurement/build/wal_enabled = false`
- `/measurement/compiler/family = "gcc-11"`
- `/measurement/compiler/receipt_fields = ["realpath", "sha256", "version"]`
- `/measurement/workload/ycsb_rratio = "50"`
- `/measurement/workload/ycsb_zipf_skew = "0.9"`
- `/measurement/workload/ycsb_rmw = "0"`
- `/measurement/records = 1000000`
- `/measurement/threads = 48`
- `/measurement/repetition_duration_seconds = 3`
- `/measurement/clocks_per_us = 2100`
- `/measurement/numa/policy = "unspecified"`
- `/measurement/numa/required_node_count = 1`
- `/measurement/numa/record_actual_count = true`
- `/design/selected/node_count = 13`
- `/design/selected/round_count = 10`
- `/measurement/occasion_count = 1`
- `/measurement/simultaneous_release = true`
- `/measurement/prohibited_post_selection = ["adaptive_sweep", "scale_measurement", "remeasure_and_select_best"]`
- `/measurement/recording/required = ["throughput_each_round", "round_start_time", "round_end_time", "effective_clock_each_round"]`
- `/measurement/recording/mean_only_allowed = false`

### §3.1 build-preimage 要求

[protocol §3.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/docs/pegasus-node-variance-protocol.md:130) の実測値ではなく、「後続 builder manifest が必ず持つ field」を固定する。

- `/build_preimage/ccbench/commit_ref = "/measurement/ccbench_commit"`
- `/build_preimage/ccbench/worktree_clean_required = true`
- `/build_preimage/source_tree/required_fields = ["member_paths", "member_sha256", "aggregate_sha256"]`
- `/build_preimage/source_tree/algorithm = "sha256"`
- `/build_preimage/source_tree/member_order = "utf8-posix-path-byte-order"`
- `/build_preimage/source_tree/include_entry_type = true`
- `/build_preimage/source_tree/follow_symlinks = false`
- `/build_preimage/compiler/required_fields = ["realpath", "sha256", "version"]`
- `/build_preimage/cmake/required_fields = ["realpath", "version", "module_list"]`
- `/build_preimage/build_argv/required = true`
- `/build_preimage/build_argv/include_shared_build_path = true`
- `/build_preimage/build_argv/shell_string_allowed = false`
- `/build_preimage/dependencies/required_names = ["gflags", "glog"]`
- `/build_preimage/dependencies/per_dependency_fields = ["source_head", "worktree_clean"]`
- `/build_preimage/dependencies/additional_dependencies = "enumerate-all-or-fail"`
- `/build_preimage/environment_contract_ref = "/measurement/environment/contract_sha256"`
- `/build_preimage/digest_algorithm = "sha256"`
- `/build_preimage/builder_retry/max_retries = 2`
- `/build_preimage/builder_retry/same_preimage_required = true`
- `/build_preimage/builder_retry/changed_preimage_invalidates_protocol = true`
- `/build_preimage/completion_manifest/required_fields = ["binary_sha256", "build_preimage", "completion_manifest_sha256"]`
- `/build_preimage/binary_store/repository_external = true`
- `/build_preimage/binary_store/read_only = true`
- `/build_preimage/measurement_job_may_build = false`
- `/build_preimage/node_hash_checkpoints = ["before_copy", "after_copy", "after_measurement"]`
- `/build_preimage/runtime_identity/required_fields = ["library_names", "resolved_paths", "library_sha256", "module_list", "ld_library_path", "scr_references"]`
- `/build_preimage/runtime_identity/bound_to_release_token = true`
- `/build_preimage/trace_symbols_required_absent = true`
- `/build_preimage/mismatch_terminal_by_boundary` は `pre_release_invalid`、`post_release_pre_measurement_invalid`、`incomplete_after_start` の 3 対応を持つ。

実 compiler path、binary hash、build path は事前には存在しないため、この repo artifact へ偽の値を埋めない。後続 builder が作る `t810-build-manifest/v1` に実値を入れ、validator がこの required-field contract と照合する。

### §3.3・§3.4 の閾値と preflight

- `/coordination/request_count_ref = "/design/selected/node_count"`
- `/coordination/distinct_hostname_count_ref = "/design/selected/node_count"`
- `/coordination/duplicate_hostname_allowed = false`
- `/coordination/unapproved_hostname_allowed = false`
- `/coordination/hostname_identity_mismatch_allowed = false`
- `/coordination/release_requires_all_ready = true`
- `/coordination/start_spread/clock = "coordinator"`
- `/coordination/start_spread/max_seconds = 5`
- `/coordination/start_spread/pass_operator = "<="`
- `/coordination/ready_timeout/seconds = 1200`
- `/coordination/ready_timeout/cancellation_marker_required = true`
- `/coordination/cancellation_recheck_before_measurement = true`
- `/coordination/partial_success_included = false`

静穏 gate:

- `/preflight/quiet/load_average_window_minutes = 1`
- `/preflight/quiet/max_load = "1.0"`
- `/preflight/quiet/pass_operator = "<="`
- `/preflight/quiet/sample_interval_seconds = 30`
- `/preflight/quiet/consecutive_passes = 3`
- `/preflight/quiet/timeout_seconds = 1200`
- `/preflight/quiet/failure_state = "pre_release_invalid"`

その他の固定:

- `/preflight/hardware_fields = ["cpu_model", "physical_cores", "hyperthreading", "memory", "numa_nodes", "cache", "frequency_policy"]`
- `/preflight/assigned_host_must_equal_actual = true`
- `/preflight/competing_process_scan = true`
- `/preflight/isolation_probe_points = ["before_measurement", "after_measurement"]`
- `/preflight/interpreter/name = "python3.10"`
- `/preflight/interpreter/required_fields = ["realpath", "version"]`
- `/preflight/qsub/stdout_path = "absolute-repository-external"`
- `/preflight/qsub/stderr_path = "absolute-repository-external"`
- `/preflight/work_root = "repository-external"`
- `/preflight/output_root = "repository-external"`
- `/preflight/submission_argv_comparison = "exact"`

barrier、release、cancel marker の実装はこの wave に入れない。ここで固定するのは後続実装が従う literal と schema だけである。

### §4 N・R、設計目標、assurance

- `/design/tau_star = "0.006"`
- `/design/tau_star_origin = "human-value-judgment-rounded-conservatively"`
- `/design/alpha = "0.05"`
- `/design/alpha_sidedness = "one-sided"`
- `/design/assurance/minimum = "0.80"`
- `/design/dropout_assurance/node_count_expression = "N-1"`
- `/design/dropout_assurance/minimum = "0.80"`
- `/design/repetition_precision/formula = "1/sqrt(2*(R-1))"`
- `/design/repetition_precision/strict_upper_bound = "0.25"`
- `/design/repetition_precision/minimum_round_count = 10`
- `/design/objective = "minimize-N-times-R"`
- `/design/selected/node_count = 13`
- `/design/selected/round_count = 10`
- `/design/selected/total_measurements = 130`
- `/design/selected/unique_minimum = true`

再現条件:

- `/design/assurance_reproduction/numpy_version = "2.2.6"`
- `/design/assurance_reproduction/generator = "Generator"`
- `/design/assurance_reproduction/bit_generator = "PCG64"`
- `/design/assurance_reproduction/seed = 810`
- `/design/assurance_reproduction/draws = 400000`
- `/design/assurance_reproduction/sigma_e = "0.012479"`
- `/design/assurance_reproduction/draw_order = ["MS_A", "MS_E"]`
- `/design/assurance_reproduction/ms_a_draw = "chisquare(N-1,draws)/(N-1)*sigma_e^2"`
- `/design/assurance_reproduction/ms_e_draw = "chisquare((N-1)*(R-1),draws)/((N-1)*(R-1))*sigma_e^2"`
- `/design/assurance_reproduction/pass_predicate = "tau_U < tau_star"`
- `/design/assurance_reproduction/selected_wins = 338491`
- `/design/assurance_reproduction/dropout_wins = 323211`
- `/design/assurance_reproduction/reported_selected = "0.8462"`
- `/design/assurance_reproduction/reported_dropout = "0.8080"`
- `/design/assurance_reproduction/independent_check/draws = 10000000`
- `/design/assurance_reproduction/independent_check/selected = "0.8463"`
- `/design/assurance_reproduction/independent_check/dropout = "0.8077"`
- `/design/assurance_reproduction/true_tau_star_non_refutation = "0.9536"`

### §5.1 区間式と報告量

[§1.1 の式](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/docs/pegasus-node-variance-protocol.md:48) と [§5.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/docs/pegasus-node-variance-protocol.md:274) を一つの estimator contract にする。

- `/estimator/response = "natural-log-throughput"`
- `/estimator/model = "node-random-effect-round-fixed-effect"`
- `/estimator/node_df = "N-1"`
- `/estimator/residual_df = "(N-1)*(R-1)"`
- `/estimator/point_variance = "max(0,(MS_A-MS_E)/R)"`
- `/estimator/lower_variance = "max(0,(MS_A/F_quantile(0.95,nu1,nu2)-MS_E)/R)"`
- `/estimator/upper_variance = "max(0,(MS_A/F_quantile(0.05,nu1,nu2)-MS_E)/R)"`
- `/estimator/point = "sqrt(point_variance)"`
- `/estimator/lower = "sqrt(lower_variance)"`
- `/estimator/upper = "sqrt(upper_variance)"`
- `/estimator/alpha_use_count = 1`
- `/estimator/truncation_means_zero_effect = false`
- `/estimator/prohibited_alternatives = ["componentwise-upper-bound-composition", "alpha-reallocation", "mu-uncertainty-addition"]`
- `/estimator/required_primary_outputs = ["tau_hat", "tau_L", "tau_U"]`
- `/estimator/required_secondary_outputs` に raw-scale fit、kappa、ICC、node mean min/max/range、各 node の mean/SD/CV/median/IQR、MS_A/MS_E/F/自由度、drift diagnostics を列挙。
- `/estimator/select_primary_after_diagnostics = false`

式文字列を `eval()` してはならない。loader は式 ID と文字列がこの v1 literal に一致することだけを検査し、後続 estimator は hard-coded な `node_random_round_fixed_f_interval_v1` へ dispatch する。

### §5.3 対応表と傾き gate

- `/decision/strategy = "first-match"`
- `/decision/order = [1,2,3,4,5]`
- 行 1: terminal state が `valid` / `terminal_reduced` 以外なら `no_primary_conclusion`
- 行 2: slope gate 発火なら `underdetermined_model_violation`
- 行 3: strict `tau_U < tau_star` なら `material_node_difference_refuted`
- 行 4: strict `tau_L > tau_star` なら `material_node_difference_supported`
- 行 5: 上記以外、等号を含め `underdetermined`

各行は `{order, predicate_op, lhs, rhs, outcome_code, report_text}` の exact key 集合にする。

傾き gate:

- `/decision/slope_gate/response = "natural-log-throughput"`
- `/decision/slope_gate/predictor = "round-index-1-through-R"`
- `/decision/slope_gate/fit = "per-node-ordinary-least-squares"`
- `/decision/slope_gate/per_node_df = "R-2"`
- `/decision/slope_gate/per_node_df_selected = 8`
- `/decision/slope_gate/S_beta = "sum((beta_i-beta_bar)^2)/(N-1)"`
- `/decision/slope_gate/V_beta = "sum(se_i^2)/N"`
- `/decision/slope_gate/multiplier = "2"`
- `/decision/slope_gate/operator = ">"`
- `/decision/slope_gate/predicate = "S_beta > 2*V_beta"`

必須 caveat も文字列 ID として固定する。

- `truncated_zero_is_not_equal_nodes`
- `single_arm_does_not_identify_additive_vs_multiplicative`
- `one-treatment-one-node_comparison_remains_forbidden`
- `zero_variance_p_value_is_secondary_only`

### §5.4 終端状態と retry

`/terminal/evaluation = "ordered-first-match"`、状態配列を次の順序で固定する。

1. `pre_release_invalid`

   `ready_timeout`、host count 不一致、duplicate/unapproved/mismatched host、copy 前後 hash 不一致、quiet gate 不成立、argv 不一致、pre inventory 不一致。主推定禁止、retry 可。

2. `post_release_pre_measurement_invalid`

   start spread 5 秒超、cancel marker 後の開始、dependency/module/trace/NUMA 不一致。主推定禁止、retry 不可。

3. `incomplete_after_start`

   completed host 11 以下、完了 job の round 欠損、測定後 binary hash 不一致、post inventory 不一致、expected set/presence matrix 不一致。主推定禁止、retry 不可。

4. `terminal_reduced`

   completed host がちょうど 12、12 node が各 10 round、状態 1–3 の他条件なし。主推定 node count 12、retry 不可。

5. `valid`

   completed host 13、各 10 round、全条件成立。主推定 node count 13。

追加 field:

- `/terminal/boundaries/release`
- `/terminal/boundaries/measurement_start`
- `/terminal/reduced/integrity_scope = "completed-12-jobs"`
- `/terminal/reduced/dropped_job_receipt_required = true`
- `/terminal/missing_data_prohibitions = ["complete-case-stitching", "imputation", "extra-rounds", "outlier-removal", "replacement-after-start", "post-hoc-state-change"]`
- `/terminal/retry/eligible_states = ["pre_release_invalid"]`
- `/terminal/retry/max_attempts = 2`
- `/terminal/retry/selection = "first-valid-or-terminal_reduced-by-submission-order"`
- `/terminal/retry/report_all_attempts = true`

builder の `max_retries=2` と、測定の `max_attempts=2` は別 field にして混同を防ぐ。

### §6.2 exact file set と presence matrix

attempt root の directory は次だけとする。

```text
group-manifest.json
submission-receipt.json
coordinator-receipt.jsonl
coordinator.stdout.log
coordinator.stderr.log
terminal-state.json
estimate.json                       # 状態依存
slots/
  slot-01/ ... slot-13/
    pbs.stdout.log
    pbs.stderr.log
    node-receipt.jsonl              # 状態・到達集合依存
    measurements.jsonl             # 開始集合依存
```

artifact fields:

- `/artifacts/root/always_files` に `estimate.json` 以外の group 6 ファイル。
- `/artifacts/root/conditional_files/estimate.json`
- `/artifacts/slots/id_format = "slot-%02d"`
- `/artifacts/slots/count_ref = "/design/selected/node_count"`
- `/artifacts/slots/always_files = ["pbs.stdout.log", "pbs.stderr.log"]`
- `/artifacts/slots/conditional_files/node_receipt = "node-receipt.jsonl"`
- `/artifacts/slots/conditional_files/measurements = "measurements.jsonl"`
- `/artifacts/file_types = ["regular-file"]`
- `/artifacts/symlinks_allowed = false`
- `/artifacts/sockets_allowed = false`
- `/artifacts/unlisted_files_allowed = false`
- `/artifacts/extra_directories_allowed = false`
- `/artifacts/logs/precreated = true`
- `/artifacts/preserve_existing_logs_and_receipts = true`

`terminal-state.json` が持つ `reached_slots`、`started_slots`、`completed_slots`、`dropped_slots` は slot-01..13 の部分集合で、loader が subset 関係・重複・状態別 cardinality を検査する。これを使って「条件付きだが exact」な集合を一意に展開する。

| 状態 | release event | node receipt | measurements | `estimate.json` |
|---|---|---|---|---|
| `pre_release_invalid` | 禁止 | `reached_slots` と exact | 禁止 | 禁止 |
| `post_release_pre_measurement_invalid` | 必須 | 13 slot 全て | 禁止 | 禁止 |
| `incomplete_after_start` | 必須 | 13 slot 全て | `started_slots` と exact。欠損は保存 | 禁止 |
| `terminal_reduced` | 必須 | 13 slot 全て | 完了 12 は各 10。脱落 slot は実在分を保存 | 必須 |
| `valid` | 必須 | 13 slot 全て | 13 slot 各 10 | 必須 |

release/cancel は `coordinator-receipt.jsonl` の typed event とし、状態表は file の存在だけでなく event の存在・不在も検査する。これにより `pre_release_invalid` で coordinator log を残しながら release record を禁止できる。

validator 自身の pre snapshot と post receipt は circular な expected-set 検査を避けるため、attempt root ではなく repo 外 T-810 root の `control/<attempt-id>/` に保存する。

## 4. protocol にあるが schema に入れないもの

対象範囲の normative 値に欠落は作らない。ただし次は意図的に入れない。

- §4.2 の N=11/R=12 など不採用候補表。選択済み N=13/R=10 の代替候補として runtime から参照できると、再選択余地になる。
- §4.3 の node 秒・予算 admission。明示的に後続 wave。
- §8 の N=2/R=2 生死確認。今回の artifact が固定する本走 N/R と混在させない。
- §9.1 item 1 の barrier、PBS wrapper、並走ガード、予算 admission の実装情報。
- §7 の下流感度表。
- 実 compiler path、build path、dependency head、binary hash。現時点では未確定なので、値ではなく runtime manifest の required fields を固定する。
- protocol にない `ycsb_max_ope`。argv allowlist上も「指定しない」を固定し、追加 token を拒否する。

## 5. digest 契約

1. UTF-8、BOM なし、LF 改行、末尾 LF 1 個を要求する。
2. JSON parse 時に duplicate key を拒否する。
3. float、NaN、Infinity、negative zero を拒否する。統計的小数は canonical decimal string とする。
4. object key は Unicode code-point 順、array 順序は保存、`ensure_ascii=True`、`sort_keys=True`、indent 2、LF 末尾という `izanagi-t810-canonical-json/v1` に再直列化する。
5. 読んだ raw bytes が再直列化 bytes と完全一致しなければ拒否する。
6. その canonical raw bytes 全体を SHA-256 する。digest field を artifact 自身へ埋め込む自己参照はしない。
7. 完成後の digest を `t810_preregistration.py` の `T810_PREREG_SHA256` に literal pin する。
8. テストにも独立の literal digest を置き、artifact と loader 定数を別々に照合する。
9. runner/validator は必ず `load_t810_preregistration()` を呼ぶ。ファイルから直接 `json.load()` した dict は API 型として受理しない。

これにより、並べ替え・空白変更も frozen bytes の変更として検出される。Python の float serialization に依存しないので再現可能である。

## 6. §6.3 validator の 5 検査

### 1. repository state・tracked hash・ignored-untracked 全走査

走査するもの:

- `git rev-parse HEAD`
- `git ls-files --stage -z` の index entry
- `git status --porcelain=v2 --branch --untracked-files=all --ignore-submodules=none`
- tracked regular file の bytes SHA-256
- gitlink の index object ID、submodule HEAD、dirty status
- repo root 以下の filesystem 全 entry。`os.scandir()` を再帰し、gitignore を一切参照しない

既存走査との違いは明確にする。

- 既存の `git ls-files --cached --others --exclude-standard` 型は ignored file を返さない。
- T-810 は Git の列挙結果を filesystem 列挙の入力にしない。
- `.gitignore`、`.git/info/exclude`、global excludes のいずれも問い合わせない。
- `.ignored` な regular file、symlink、directory も path set に入れる。
- 列挙前後の path set と各 file の `lstat` を二度比較し、走査中の作成・削除・置換も scan-race として失敗させる。

比較:

- pre/post の HEAD、index、status、path、kind、mode、size、SHA-256、mtime_ns を exact 比較。
- 追加、削除、bytes 変更、type 変更、symlink target 変更、走査中 race、読取不能で失敗。

`.git` object store は filesystem walk から除くが、worktree の `.git` pointer bytes と Git の semantic state を別途記録する。`.claude/` は除外しない。

### 2. §6.1 禁止領域 inventory

専用 inventory は広く次を対象にする。

- `repo_root/output/` 全体
- `repo_root/orchestrator/campaign/env_contract.py`
- `repo_root/orchestrator/campaign/env_contract_activations/`

`output/` 全体を取ることで、以下を同時に包含する。

- `output/env/*/calibration/**` の attempts、job-staging、registered
- `output/campaigns/**` の WAL
- `output/s1-freeze/**`、`output/s8b-freeze/**` 等の freeze と journal
- `output/s8c-trial-registry/registry.jsonl` と `lifecycle.jsonl`
- floor/oracle/certification receipts、proof chain、採択 report

各 path について path、kind、mode、size、SHA-256、mtime_ns を保持する。存在しない canonical root は `absent` として snapshot に含め、post で作られた場合も検出する。

一件でも delta、読取不能、特殊 file、race があれば失敗する。一般 repo scan と結果が重複しても省略しない。禁止領域別の finding code を残すための独立検査である。

### 3. frozen manifest の全 member hash

validator 入力の runtime frozen manifest は strict schema にする。

```text
schema_version
prereg_sha256
root_identity
members[]:
  relative_path
  kind = regular-file
  size
  sha256
```

- manifest bytes 自体に、承認時に記録された expected SHA-256 を必須引数として渡す。ファイル自身から expected 値を導出しない。
- duplicate path、absolute path、`..`、symlink、missing member、size/hash 不一致を拒否。
- member を一つずつ bytes hash。
- dedicated manifest root も filesystem 走査し、列挙 member 以外の新規 file を拒否する。

これにより「列挙済み path だけ hash して新規 file を見逃す」実装を防ぐ。

### 4. calibration wildcard namespace の明示 deny

次を別の finding class として検査する。

- repo の `output/env/<env>/calibration/**` 全 namespace を filesystem で列挙。
- T-810 writable root がその namespace の内側・祖先・同一でないこと。
- expected attempt path に `env/<tag>/calibration`、`attempts`、`job-staging`、`registered` の calibration layout を生成するものがないこと。
- output JSON の `schema_version` が calibration schema を名乗らないこと。
- runner executable/argv に `certify_calibration.sh`、`exec_calibrate.py`、`orchestrator.calibrate`、`--certify` がないこと。

既存 calibration file の存在自体は失敗にしない。pre/post delta、T-810 root との namespace overlap、T-810 による calibration 名義生成で失敗する。

### 5. executable と argv

pre では予定 command manifest、post では実行 receipt を検査する。

- runner 起動 argv は exact option set、各 option 1 回、positional/passthrough なし。
- `python3.10` の realpath/version を preflight 値と比較。
- CCBench executable は regular file、symlink なし、frozen manifest の path/size/SHA-256 と一致。
- 各 completed slot は同一 benchmark argv をちょうど R=10 回。
- partial slot は記録された全実行を検査するが、結果採用は終端状態表に従う。
- executable、argv 順序、flag 値、command 件数、return code record の欠落、unknown command のいずれでも失敗。
- shell string や `shell=True` を受け取る API は作らない。

ただし、この receipt だけでは「記録されなかった exec が存在しない」ことまでは能力的に証明できない。この限界は総括に記す。

## 7. fail-closed と終端状態

CLI return code は次のように固定する。

- `0`: 全検査合格
- `2`: CLI/schema/required input 不正
- `3`: prereg digest/canonical bytes 不一致
- `4`: root policy・path identity 不成立
- `5`: repo/protected/frozen inventory 不一致または走査不能
- `6`: calibration namespace・argv/executable 不一致
- `7`: expected file set・presence matrix 不一致
- `70`: 未分類例外。合格 receipt は書かず、fail-closed finding のみ残す

終端状態への倒し先は、caller の任意文字列ではなく `coordinator-receipt.jsonl` と node receipt に記録された境界から導出する。

| 検出境界 | validator failure 時 |
|---|---|
| release record なし | `pre_release_invalid` |
| release recordあり、全 slot で measurement_start なし | `post_release_pre_measurement_invalid` |
| 1 slot でも measurement_start あり | `incomplete_after_start` |
| claimed `valid` / `terminal_reduced` の post validator が失敗 | `incomplete_after_start` へ強制上書き |
| claimed `valid` / `terminal_reduced` の post validator が合格 | 状態を維持。ただし validator 自身はその状態を新規判定しない |

`valid` と `terminal_reduced` の成立判定は scope 外の完了 verifier の責務である。本 validator は、その claim と presence matrix の整合を検査するだけに留める。

pre snapshot digest は承認 receipt に束縛し、post CLI は `--expected-baseline-sha256` を必須とする。baseline file 内の自己申告 digest だけを信頼しない。

## 8. テスト一覧

### artifact / loader

1. `test_prereg_digest_is_independently_pinned` — artifact と loader/test の digest の片方だけを更新するバグを殺す。
2. `test_prereg_rejects_one_byte_tamper` — N、閾値、式などの事後変更を殺す。
3. `test_prereg_rejects_duplicate_json_key` —後勝ち JSON parser で値を差し替えるバグを殺す。
4. `test_prereg_rejects_noncanonical_bytes` — CRLF、BOM、空白・key 順変更を凍結 bytes として通すバグを殺す。
5. `test_prereg_rejects_unknown_missing_or_wrong_typed_fields` — permissive schema drift を殺す。
6. `test_prereg_contains_n13_r10_only` — stale N=12/R=12 や候補表からの再選択を殺す。
7. `test_prereg_cross_field_design_invariants` — N×R、df、R−2、dropout N−1 の取り違えを殺す。
8. `test_prereg_assurance_reproduction_literals` — seed、NumPy version、draw order、winner count の drift を殺す。
9. `test_prereg_decision_order_and_strict_inequalities` — `<=` 化や判定順交換を殺す。
10. `test_prereg_terminal_states_are_exact_ordered_closed_set` —第 6 状態追加や retry 範囲拡大を殺す。
11. `test_prereg_projection_is_deeply_immutable` — loader 後の nested mutation を殺す。
12. `test_presence_projection_for_all_five_states` —状態別 release/receipt/estimate の対応ずれを殺す。
13. `test_policy_registry_contains_t810_in_sorted_closed_set` — JSON を registry 外へ置くバグを殺す。

### argv / root

14. `test_runner_accepts_only_the_frozen_invocation` — runner option を自由 knob 化するバグを殺す。
15. `test_runner_rejects_certify_calibration_forms` — `--certify`、calibration script/module の流用を殺す。
16. `test_runner_rejects_extra_or_reordered_benchmark_flags` —未登録 flag・値・順序の drift を殺す。
17. `test_runner_rejects_ycsb_max_ope_and_shell_passthrough` — protocol 外 flag と shell escape を殺す。
18. `test_runner_rejects_binary_symlink_or_hash_mismatch` —別 binary への差し替えを殺す。
19. `test_root_accepts_disjoint_external_directory` —正規の repo 外 root が利用不能になる回帰を殺す。
20. `test_root_rejects_repo_child_equal_and_ancestor` —approved root を repo の祖先にして capability を迂回するバグを殺す。
21. `test_root_rejects_symlink_and_mount_crossing` —既存 durable-root 防壁を接続し忘れるバグを殺す。

### validator

22. `test_repo_snapshot_detects_tracked_byte_change` —tracked hash を Git index object IDだけで済ませるバグを殺す。
23. `test_repo_snapshot_detects_gitignored_untracked_file` —既存 exclude-standard 走査へ戻すバグを殺す。
24. `test_repo_snapshot_detects_gitignored_file_under_dot_claude` —P1 の広すぎる除外を再導入するバグを殺す。
25. `test_repo_snapshot_detects_add_remove_type_and_symlink_target` —hash 済み regular file しか比較しないバグを殺す。
26. `test_repo_snapshot_fails_on_scan_race_or_unreadable_entry` —不完全 snapshot を合格扱いするバグを殺す。
27. `test_protected_inventory_detects_output_mtime_or_hash_delta` —禁止領域を一般 scan の副作用としてしか見ないバグを殺す。
28. `test_protected_inventory_detects_new_absent_root` —pre に無い registry/staging を post で作るバグを殺す。
29. `test_frozen_manifest_rejects_missing_changed_duplicate_and_escape_member` —manifest member 検査の抜けを殺す。
30. `test_frozen_manifest_rejects_unlisted_new_file` —列挙済み member しか見ないバグを殺す。
31. `test_calibration_wildcard_namespace_is_explicitly_denied` —外部 root や filename を calibration consumer の走査面へ重ねるバグを殺す。
32. `test_execution_receipt_rejects_unknown_executable_and_missing_record` —記録された一部 command だけを見るバグを殺す。
33. `test_each_completed_slot_has_exactly_ten_commands` —R−1、R+1、best-of-R を殺す。
34. `test_expected_layout_rejects_extra_file_directory_symlink_socket` —expected set を subset 比較にするバグを殺す。
35. `test_presence_matrix_release_and_estimate_rules` —失敗状態で release/estimate を残す、成功状態で欠落させるバグを殺す。
36. `test_failure_state_is_derived_from_receipt_boundary` —caller の claimed state で failure を軽い状態へ倒すバグを殺す。
37. `test_failed_valid_or_reduced_claim_becomes_incomplete_after_start` —数値が完全なら validator failure を無視するバグを殺す。
38. `test_same_cli_runs_pre_and_post_checks` —pre/post で異なる検査実装へ drift するバグを殺す。
39. `test_every_error_class_returns_nonzero_without_pass_receipt` —例外を log して rc=0 にするバグを殺す。
40. `test_post_requires_approved_baseline_digest` —攻撃者が baseline と自己 digest を同時に書き換えるバグを殺す。

実装後の実測は親が `tools/run_tests.py` 経由で上記新規テストと既存 `test_durable_root.py`、`test_pegasus_policy_registry.py` を走らせる。今回の read-only 起草では緑を主張しない。

## 9. P1・P2・P3 への判断

### P1: 反対

`.git` の filesystem object store を除外し、Git semantic state を別途取ることには賛成する。しかし `.claude/` 全体の除外には反対する。

代案は `.claude/` を含む full filesystem scan である。並行 worktree が書くため赤くなるなら、それは validator の検出を軽くする理由ではなく、測定承認時に quiescent な専用 checkout を用意するか並行 writer を止めるべき運用条件である。その機械化はこの wave の scope に追加しない。

反対を採らず `.claude/` 全体を除外すると、例えば gitignored な `.claude/t810-result.json`、shell redirect、偽 handoff、将来 `.claude` 下へ移動した protected namespace が pre/post の双方から消え、§6.3 の「gitignore された未追跡も走査」が偽になる。

### P2: 賛成

[durable root API](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/durable_root.py:196) は協調的 write path の制約であり、素の `open()`、shell redirect、PBS log を観測できない。validator が同じ API の記録だけを調べると blind spot を共有する。独立した `os.scandir` と bytes hash が必要である。

加えて、approved root が repo の祖先になる overlap は T-810 wrapper 側で明示的に拒否する。

### P3: 条件付きで賛成

`tools/pegasus/policies/t810_prereg_v1.json` は既存 policy 群との配置一貫性があり、registry の閉集合にも載せられる。

ただし「test だけが digest を pin」では runtime 検証にならない。loader 本体にも独立 expected digest literal を持たせ、test は artifact bytes と loader constant の双方を照合する。この補強を採らない場合、runner が現在読んだ artifact の digest を「expected」として再利用する恒真検査になり得る。

## 10. 子 A / 子 B の分割

所有ファイルは重ねない。

### 子 A — 凍結 artifact と loader

所有:

- `tools/pegasus/policies/t810_prereg_v1.json`
- `tools/pegasus/policies/registry_v1.json`
- `orchestrator/campaign/t810_preregistration.py`
- `orchestrator/tests/test_t810_preregistration.py`

成果:

- schema 全 field
- canonicalization と digest pin
- immutable loader
- terminal/presence projection
- registry 登録

### 子 B — root、argv、validator

所有:

- `orchestrator/campaign/t810_runner_policy.py`
- `orchestrator/campaign/t810_validator.py`
- `tools/pegasus/validate_t810.py`
- `orchestrator/tests/test_t810_runner_policy.py`
- `orchestrator/tests/test_t810_validator.py`

子 B は子 A の確定 API、`VerifiedT810Preregistration` と `expected_attempt_layout()` を import する。artifact や loader を修正しない。API 不足が判明した場合は子 A へ変更要求を返し、同じファイルを双方で触らない。

## 総括

この slice は、N=13・R=10 を含む事前登録を canonical bytes と SHA-256 で固定し、その loader、repo 外 root、完全 argv allowlist、§6.3 の 5 検査を一つの fail-closed validator に束ねる。validator failure は性能値に関係なく、検出境界に応じて `pre_release_invalid`、`post_release_pre_measurement_invalid`、`incomplete_after_start` のいずれかへ倒す。

最も危険な残存穴は、argv 検査が runner 自身の execution receipt に依存する点である。receipt に記録されなかった別 executable の存在を、この slice だけで能力的に否定することはできない。後続 PBS wrapper が shell/passthrough を持たず、すべての exec を単一 mediation 点へ通すまでは、§9.1 第1段を満たしたとも、実行を承認できる状態とも扱ってはならない。