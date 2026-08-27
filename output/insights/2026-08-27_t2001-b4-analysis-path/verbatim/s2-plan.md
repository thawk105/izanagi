## 前提の確認

次の射影資料を全文読めた。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s1-brief.md`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/ref-prereg-b4.md`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/ref-decisions.md`

repo は read-only で調査した。書き込み、pytest、build は実行していない。実施したのは静的走査と、標準ライブラリだけの短い算術マイクロベンチである。

結論を先に示す。

- P1 は維持できる。事前登録 doc を編集せず、独立 consumer が現行文面を読む。
- P3 は採用可能。ただし heading の完全一致ではなく、Markdown を正規化した一意な節構造を anchor にする。
- P4 は正しい。`observe_relative()` は片側の乗法境界なので流用しない。
- P2 は「fail-closed adapter の実装」までは成立するが、producer 不在の field が多いため、これだけで §6 前提条件 9 を充足したとは扱えない。
- 親の A → B/C 並列だけでは、registry violation count と assignment compliance を adapter から verdict へ偽装不能に運ぶ統合経路がない。A → B/C → D の統合単位を追加する。

## 一覧検査の閉包

新しい production `orchestrator/campaign/*.py` が自動的に入る検査を、literal の `glob` / `rglob`、Git 列挙、AST 全走査、内容検索から逆引きした。

|検査|新 file への要求|プランでの満たし方|
|---|---|---|
|[test_campaign_import_invariant.py:1001](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_campaign_import_invariant.py:1001>) `scan_repository()`|tracked と非 ignored untracked を列挙し、全 Python を parse。campaign file には sys.path 変異禁止、direct CLI + relative import 時の canonical bootstrap、absolute sibling import 禁止を課す。[同:1040](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_campaign_import_invariant.py:1040>)|production file に `__main__` を置かない。兄弟 import は `from . import ...` または `from .x import ...` に統一。`campaign.*` legacy 名と sys.path 操作を置かない。対象 node は `test_real_repository_legacy_namespace_matches_exception_ledger`、`test_real_campaign_package_has_canonical_direct_bootstrap`、`test_real_campaign_package_uses_relative_sibling_imports`。|
|[test_campaign.py:4641](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_campaign.py:4641>)|repo 全体の production `*.py` を [5128-5179](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_campaign.py:5128>) で AST 解析し、`run_campaign` / `pipeline.evaluate` の caller 集合を exact pin。[5198-5254](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_campaign.py:5198>)|新 file から両 API を呼ばない。分析は既存 WAL bytes を入力として受け、計測を起動しない。|
|[test_p3_build_authority_cli.py:630](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_build_authority_cli.py:630>)|`git ls-files -- "*.py"` の tracked Python 全件を [194-210](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_build_authority_cli.py:194>) から AST 解析。build authority helper の caller、動的解決、star import を exact pin。|build authority API、動的 import、star import を使わない。|
|[test_p3_build_authority_cli.py:1190](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_build_authority_cli.py:1190>)|campaign の全 `*.py` 内容を読み、`--build` を含む file 集合を exact 比較。|新 production source に `--build` literal を置かない。|
|[test_p3_exploration_namespace.py:123](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_exploration_namespace.py:123>)|campaign の全 `*.py` を AST parse。campaign-root creator と判断された module は import され、`_DRIVER_CONTRACTS` exact 集合に必要。[414-417](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_exploration_namespace.py:414>)|新 file は campaign layout 作成や `run_campaign()` を持たない純粋な分析 module とし、driver census に入れない。|
|[test_ccbench_spawn_sites.py:300](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_ccbench_spawn_sites.py:300>)|`orchestrator/campaign` 全体を再帰 AST 走査し、process launch、`run_once` client、calibration issuer の exact caller 集合を検査。[476-503](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_ccbench_spawn_sites.py:476>)|`subprocess`、`os.spawn*`、calibrator runner、calibration issuer を使わない。|
|[test_p3_s4_loop.py:1108](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_s4_loop.py:1108>)|全 production Python から `render_hole` の caller 集合を exact pin。|新 file は `render_hole` を参照しない。|
|[test_pegasus_dispatch_compute.py:2232](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_pegasus_dispatch_compute.py:2232>)|`tools` と `orchestrator` 全 `*.py` から `_best_effort_qdel` の import/caller を exact pin。|scheduler 操作を置かない。|
|[test_t1286_commit_receipt.py:657](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_t1286_commit_receipt.py:657>)|production `orchestrator/**/*.py` を parse し、`STAGE_COMMIT` producer 5 件と `_VerificationCapability` issuer 1 件を exact pin。[667-702](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_t1286_commit_receipt.py:667>)|`STAGE_COMMIT` を引数にする書込みも `_VerificationCapability` 構築も行わない。|
|[test_t338_submission_gate_unit5.py:490](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_t338_submission_gate_unit5.py:490>)|repo の全 production Python を AST 走査し、`create_receipt_bytes` / `create_only_relative_bytes` caller を限定。|この2関数を使わない。分析 receipt は純粋な dataclass/bytes とし、submission gate の writer を流用しない。|
|[test_login_headroom.py:1602](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_login_headroom.py:1602>)、[1625](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_login_headroom.py:1625>)|全 tracked/untracked text から `<login-headroom-ceiling-literal>` の compact literal、全 `orchestrator` / `tools` AST から `MAX_LOCAL_BUDGET_BYTES` 等の定義を exact pin。|該当 literal・識別子を置かない。|
|[test_check_subprocess_bytecode_guard.py:223](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_check_subprocess_bytecode_guard.py:223>)|checker は `orchestrator` / `tools` の全 Python を [tools/check_subprocess_bytecode_guard.py:64](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/tools/check_subprocess_bytecode_guard.py:64>) から parse。Python subprocess に `PYTHONDONTWRITEBYTECODE` または `-B` を要求。|production file は subprocess 自体を使わない。|
|[test_reflux_ir.py:274](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_reflux_ir.py:274>)|全 production `orchestrator/**/*.py` から test-local `reflux_ir_expected_goldens` 参照を検索。|参照しない。|
|[test_s1_known_axes_freeze.py:520](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_s1_known_axes_freeze.py:520>)|campaign 全 file から `s1_expected_goldens` 参照を検索。|参照しない。|
|[test_s8b_floor_campaign.py:1586](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_s8b_floor_campaign.py:1586>)|全 production AST から特定関数への `use_perf=` caller を exact pin。|該当関数を呼ばず、識別子 `use_perf` を導入しない。|
|[test_s8b_floor_campaign.py:6290](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_s8b_floor_campaign.py:6290>)|campaign 全 Python から `--build` literal と `buildcache.build*` caller を分類。[6334-6403](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_s8b_floor_campaign.py:6334>)|build literal/API を置かない。|
|[test_s8b_floor_stats.py:875](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_s8b_floor_stats.py:875>)|campaign 全 file から `verify_floor_artifact_with_live_admission` caller 3件を exact pin。|流用しない。|
|[test_s8b_oracle_manifest_contract.py:39](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_s8b_oracle_manifest_contract.py:39>)|campaign 全 file の AST から S8B loader / `verify_manifest` consumer set を exact pin。[87-104](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_s8b_oracle_manifest_contract.py:87>)|B-4 manifest は独立型にし、S8B manifest API を参照しない。|
|[test_s8b_oracle_report.py:5488](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_s8b_oracle_report.py:5488>)|全 production AST から `s8b_oracle_report.build_observations` caller を exact pin。[5502-5594](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_s8b_oracle_report.py:5502>)|参照しない。|
|[test_s8b_ratified_freeze.py:2399](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_s8b_ratified_freeze.py:2399>)|campaign 全 file から `RatifiedFreeze(` を内容検索し、loader 外構築を禁止。|この型を使わない。|
|[test_calibration_freeze_stage6_candidate_gate.py:375](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_calibration_freeze_stage6_candidate_gate.py:375>)|tracked/untracked production Python 全件を母集合にし、2つの stage6 predicate の caller/曖昧参照集合を exact pin。[119-148](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_calibration_freeze_stage6_candidate_gate.py:119>)|両 predicate 名を source、コメント、docstring に置かない。|
|[test_pegasus_policy_registry.py:434](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_pegasus_policy_registry.py:434>)|tracked production `.py/.sh` 全件から旧 shared policy の moved key 直接読出しを検索。[485-493](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_pegasus_policy_registry.py:485>)|Pegasus policy file を読まない。|
|[test_official_perf_closure.py:508](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_official_perf_closure.py:508>)|production root 全体を走査し、perf predicate を持つ file 集合を exact pin。[855-862](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_official_perf_closure.py:855>)|`probe_perf_availability` 等の tracked callを使わない。`if` 条件の識別子に `perf` / `perf_*` を使わない。`PerfConfig` は doc parse の文字列としてのみ扱う。|
|[test_s8b_repo_scan_invariant.py:27](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_s8b_repo_scan_invariant.py:27>)|`search_repository()` が Git 列挙した全 repo file 内容を読む。[s8b_holdout_freeze.py:591](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/s8b_holdout_freeze.py:591>) holdout 三軸 conjunction の hit は空でなければならない。|新 source に holdout の ratio/skew/rmw 三軸を同居させない。B-4 の `0.60` / `0.025` は単独では conjunction にならない。|
|[test_plain_runner_coverage.py:60](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_plain_runner_coverage.py:60>)|新 `test_*.py` は self-runner を持つか README allowlist に必要。|既存 README を変えず、各新テスト末尾を `pytest.main([__file__, "-q"])` にする。|
|[test_acceptance_schedule_order.py:660](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_acceptance_schedule_order.py:660>)|全 test collection を再列挙し、duration ledger coverage 90%以上を要求。|新 node は collection に入る。数十 node の追加なので現 ledger 規模では閾値影響は小さいが、親の実測で確認する。既存 ledger の期待値変更は提案しない。|

特に「exact module 集合」の見落としやすい箇所は `test_p3_exploration_namespace.py::test_driver_contract_registry_is_exact` である。新 file を driver と誤認させる AST 形を避ける。

静的に確認できた literal `glob` / `rglob` / Git file 列挙経路は上表で閉じている。動的に組み立てた pattern 名までの完全性は証明できないため、その限界は後述する。

## 実装プラン

### 1. `p3_b4_analysis_contract.py`、S1

新規: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py`

予定配置:

- L1-95: `__all__`、hardcode 定数、enum。
- L96-220: frozen/slots dataclass。
- L221-330: 全入力検証と block score。
- L331-410: exact sign test、Clopper-Pearson。
- L411-500: verdict 全域関数。

公開型と API:

```python
class AnalysisInvalidReason(Enum): ...
class RegistryViolationReason(Enum): ...
class Arm(Enum): ...
class BlockStatus(Enum): ...
class Verdict(Enum): ...

@dataclass(frozen=True, slots=True)
class SampleAHat:
    value: Fraction

@dataclass(frozen=True, slots=True)
class ArmObservation: ...
@dataclass(frozen=True, slots=True)
class BlockObservation: ...
@dataclass(frozen=True, slots=True)
class ContractBlockBinding: ...
@dataclass(frozen=True, slots=True)
class ContractBinding: ...
@dataclass(frozen=True, slots=True)
class AnalysisInvalid: ...
@dataclass(frozen=True, slots=True)
class ExactSignPValues: ...
@dataclass(frozen=True, slots=True)
class ThetaInterval: ...
@dataclass(frozen=True, slots=True)
class AnalysisResult: ...

def validate_analysis_inputs(
    *,
    floor: object,
    contract_binding: object,
    registry_violation_count: object,
    blocks: object,
) -> ValidatedAnalysis | AnalysisInvalid: ...

def block_score(
    block: BlockObservation,
    *,
    floor: Fraction,
) -> Fraction: ...

def exact_sign_pvalues(
    *,
    on_wins: int,
    non_ties: int,
) -> ExactSignPValues: ...

def clopper_pearson_theta_95(
    *,
    on_wins: int,
    non_ties: int,
) -> ThetaInterval: ...

def evaluate_analysis(
    *,
    floor: object,
    contract_binding: object,
    registry_violation_count: object,
    blocks: object,
) -> AnalysisResult: ...
```

定数は doc から読まず、source literal とする。

```python
EXPECTED_BLOCK_COUNT = 201
A_MIN = Fraction(3, 5)
ONE_SIDED_ALPHA = Fraction(1, 40)
TWO_SIDED_ALPHA = Fraction(1, 20)
TEST_UNIT = "block"
```

`A` と `A_hat` の混同を避けるため、母数 `A` を表す実行時変数や引数を作らない。標本値だけを `SampleAHat` とし、計算は次で固定する。

```python
SampleAHat(Fraction(2 * on_wins + ties, 2 * block_count))
```

`A_MIN` は結果注記 `effect_below_a_min` にだけ使う。verdict helper の引数に `a_hat` や `A_MIN` を渡さない。

score は `Fraction(0)`, `Fraction(1, 2)`, `Fraction(1)`。両 arm が certified の場合は、保存された数値の `as_integer_ratio()` を使って exact fraction 化し、

```text
abs(on_tps - off_tps) / reference_tps <= floor
```

を境界込み tie とする。[observe_relative():332-353](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/qualification/contract.py:332>) は `subject > reference * (1 + floor)` という片側 bit なので流用しない。

符号検定は次を `Fraction` で返す。

```python
denominator = 1 << m
p_on = Fraction(sum(comb(m, k) for k in range(W, m + 1)), denominator)
p_off = Fraction(sum(comb(m, k) for k in range(0, W + 1)), denominator)
```

`m = 0` は両方 `Fraction(1)`。有意水準との比較も `<= Fraction(1, 40)` なので float 丸めで `0.025` を跨がない。

`m = 201` では `2**201` は10進61桁。裾の既約分子・分母も最大おおむね60-61桁だった。読取専用マイクロベンチでは1000組の両裾計算が約2.49秒、1分析当たり約2.5 msだった。

Clopper-Pearson は既存実装を流用しない。

- module 自体が [stress_check_simulation.py:26](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/preregistration/stress_check_simulation.py:26>) で NumPy を import する。
- `_regularized_beta()` は [309-335](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/preregistration/stress_check_simulation.py:309>) の float 演算。
- `_clopper_pearson_upper()` は [415-444](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/preregistration/stress_check_simulation.py:415>) の片側上限で、B-4 の両側95%ではない。水準も `DELTA_MC/CELL_COUNT` で異なる。

代わりに `math.comb` と整数多項式を使い、各 dyadic midpoint で二項裾と `1/40` を exact 比較する。

- `W = 0`: lower = 0。
- `W = m`: upper = 1。
- lower root: `P_p(Bin(m,p) >= W) = 1/40`。
- upper root: `P_p(Bin(m,p) <= W) = 1/40`。
- 80回の dyadic bisection 後、各 root を幅 `2**-80` の rational bracket として保持する。
- 報告区間は下端を外側へ、上端を外側へ取る。したがって数値近似で coverage を狭めない。
- `m = 0` は exact `[0, 1]`、`theta_estimable=False`。

中央付近 `m=201` の整数 power table 方式は試作計測で約0.6-0.7秒だった。これは pytest の緑ではなく、実装方式の所要見積りだけである。

全入力検証は `validate_analysis_inputs()` が11理由をすべて収集する。`evaluate_analysis()` は `ValidatedAnalysis` が得られるまで `_evaluate_validated_analysis()` を呼ばない。verdict 順は doc [468-486](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:468>) のまま固定する。

テスト新規:

`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_contract.py`

主な nodeid 案:

- `test_analysis_invalid_reason_enum_is_exact`
- `test_registry_violation_reason_enum_is_exact`
- `test_block_status_and_rank_tiers_are_exact`
- `test_certified_gain_boundary_is_inclusive_tie`
- `test_a_hat_is_sample_ahat_with_exact_fraction`
- `test_exact_sign_pvalues_use_integer_binomial_tails_at_m201`
- `test_significance_comparison_does_not_cross_float_boundary`
- `test_clopper_pearson_brackets_both_exact_binomial_roots`
- `test_clopper_pearson_m_zero_is_unestimable_zero_one`
- `test_validate_analysis_inputs_reports_all_reasons_before_verdict`
- `test_evaluate_analysis_does_not_call_validated_branch_for_invalid_input`
- `test_evaluate_analysis_establishes_below_a_min_when_p_on_is_significant`
- `test_missing_is_not_excluded_and_loses_to_rejected`
- `test_missing_does_not_tie_rejected_or_aborted`
- `test_registry_violation_count_forces_protocol_violation`
- `test_protocol_violation_precedes_contamination`
- `test_every_valid_input_reaches_one_verdict`

`A_min` 負例には `m=6, W=6, ties=195` を使う。`p_on=1/64 <= 1/40` だが `A_hat=69/134 < 3/5` なので、「A_min を成立閾値に使う」変異だけを確実に赤にできる。

### 2. `p3_b4_analysis_adapter.py`、S2

新規: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_adapter.py`

予定配置:

- L1-70: schema version、exact key set、enum。
- L71-190: raw parser。
- L191-280: status 写像。
- L281-350: contract block adapter。

公開 API:

```python
RAW_ANALYSIS_SCHEMA_VERSION = "p3-b4-raw-analysis/v1"

class ExecutionDisposition(Enum):
    EXECUTED = "executed"
    DUPLICATE = "duplicate"
    DRY_PASS = "dry-pass"
    STOPPED_BEFORE = "stopped-before"
    CRASH = "crash"
    TERMINAL_RECORD_ABSENT = "terminal-record-absent"

@dataclass(frozen=True, slots=True)
class RawArmRecord: ...
@dataclass(frozen=True, slots=True)
class RawBlockRecord: ...
@dataclass(frozen=True, slots=True)
class RawAnalysisRecords: ...

def parse_raw_analysis_records(value: object) -> RawAnalysisRecords: ...

def block_status_from_raw_arm(record: RawArmRecord) -> BlockStatus: ...

def adapt_raw_blocks(
    value: object,
    *,
    contract_binding: ContractBinding,
    assignment_followed_by_block: Mapping[str, bool],
) -> tuple[BlockObservation, ...] | AnalysisInvalid: ...
```

raw top-level key は `schema_version`, `blocks` の exact 2 key。block key は次を必須にする。

```text
block_id
reference_tps
reference_snapshot_hash
reference_receipt_hash
assignment_observation
arms
```

各 arm は次の exact key set。

```text
arm
execution_disposition
whiteboard_result
terminal_stage
terminal_reason
throughput
precursor_hash
treatment_fired
contaminated
protocol_ok
source_artifact_sha256
```

真偽値は `type(value) is bool`。hash は lowercase SHA-256。欠落、未知 key、暗黙 default、推定は禁止する。

status 写像は次で固定する。

|raw 条件|block status|
|---|---|
|`execution_disposition != executed`。duplicate、dry-pass、実行前停止、crash、終端なしを含む|`missing`|
|`executed` + fresh attempt の COMMIT + `whiteboard_result=success` + 正の throughput|`certified`|
|`executed` + diff-quarantine ABORT + `whiteboard_result=rejected`|`rejected`|
|`executed` +その他の ABORT + `whiteboard_result=fail`|`aborted`|
|上記以外の組合せ|adapter error。別 status を推定しない|

duplicate は現在の `_resolve_duplicate()` が success/fail whiteboard を追加する場合があるため、whiteboard だけでは分類しない。[p3_s4_loop.py:1021-1063](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:1021>) `execution_disposition=duplicate` が常に優先し、行は `missing` として残す。

#### 既存実 artifact との対応

|raw/contract field|既存実 artifact から取得可能か|実 writer / 根拠|
|---|---|---|
|`whiteboard_result`|可能|`project_whiteboard()` が追加する [593-611](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:593>)。`state_to_dict()` / `save_loop_state()` が checkpoint へ書く [724-732](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:724>)、[802-812](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:802>)。値域は [735-757](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:735>)。|
|candidate `throughput`|certified COMMIT に限り可能|`pipeline.evaluate()` が `fitness_tps` を COMMIT payload へ書く [1532-1562](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/pipeline.py:1532>)。no-bench COMMIT は `None` [1468-1502](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/pipeline.py:1468>) なので B-4 certified throughput には使えない。|
|terminal `commit/abort`|可能|COMMIT は上記。ABORT は `_abort()` が書く [pipeline.py:1008-1019](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/pipeline.py:1008>)。物理追記は `wal.log()` / `append()` [wal.py:411-475](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/wal.py:411>)、[689-696](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/wal.py:689>)。|
|`env_tag`|可能|`wal.log()` が `WalRecord.env_tag` に書く [wal.py:689-696](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/wal.py:689>)。ただし §5 の B-4 expected env_tag は未記入。|
|arm identity|一部可能|`default_cfg()` が `search_config["reflux"]` を持つ [p3_s4_loop.py:892-915](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:892>)。closed critic receipt にも `arm` が書かれる [p3_b4_closed_critic.py:951-1005](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_closed_critic.py:951>)。block schedule との結合 producer は無い。|
|`execution_disposition`|durable producer 不在|`run_one_iteration()` は in-memory `outcome` を返す [1087-1182](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:1087>)、`drive_iteration()` は `ran` を返す [1519-1556](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:1519>) が、B-4 raw artifact へ永続化する producer は無い。|
|`treatment_fired`|producer 不在|digest の赤節は生成できる [p3_s4_loop.py:558-587](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:558>) が、arm 別発火 bool を書く receipt は無い。推定しない。|
|`contaminated`|producer 不在|competing-tenant 等の個別 abort はあるが、B-4 の汚染定義を集約した bool producer は無い。|
|`protocol_ok`|producer 不在|既存 gate の個別結果をこの bool へ集約する producer は無い。|
|`precursor_hash`|producer 不在|`source_bytes_sha256` や variant id を precursor snapshot hash と読み替えない。|
|`reference_tps`|意味上の producer 不在|`fitness_tps` の数値自体はあるが、「祖先方向の最初の certified snapshot」を一意に選ぶ resolver が無い。`observe_relative()` の引数名だけを producer と数えない。|
|`reference_snapshot_hash`|producer 不在|該当 field は存在しない。|
|`reference_receipt_hash`|producer 不在|`build_admission_receipt_sha256` [pipeline.py:1541](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/pipeline.py:1541>) は throughput reference receipt ではないため代用しない。|
|実行 slot 順 / `assignment_followed`|producer 不在|`outcome` / `ran` は slot 順を記録しない。|
|B-4 `block_id`|producer 不在|S8B oracle の同名 field は別実験であり流用しない。本 wave の manifest generator が初めて作る。|

テスト新規:

`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_adapter.py`

nodeid 案:

- `test_raw_schema_version_and_exact_key_sets_are_closed`
- `test_raw_schema_rejects_missing_unknown_and_non_boolean_fields`
- `test_duplicate_maps_to_missing_even_with_success_whiteboard`
- `test_dry_pass_stop_crash_and_absent_terminal_map_to_missing`
- `test_executed_success_commit_maps_to_certified`
- `test_executed_diff_quarantine_maps_to_rejected`
- `test_executed_other_abort_maps_to_aborted`
- `test_inconsistent_whiteboard_terminal_pair_fails_closed`
- `test_adapter_never_drops_a_missing_block`
- `test_adapter_requires_all_currently_unproduced_fields`

### 3. `p3_b4_analysis_prereg_consumer.py`、S3

新規: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py`

公開 API:

```python
@dataclass(frozen=True, slots=True)
class ParsedPreregisteredAnalysisContract: ...

def extract_preregistered_analysis_contract(
    document_bytes: bytes,
) -> ParsedPreregisteredAnalysisContract: ...

def assert_contract_constants_are_source_literals(
    contract_source_bytes: bytes,
) -> None: ...

def assert_preregistration_matches_implementation(
    *,
    document_bytes: bytes,
    contract_source_bytes: bytes,
) -> ParsedPreregisteredAnalysisContract: ...

def verify_repository_preregistration_contract(
    *,
    repository_root: Path,
) -> ParsedPreregisteredAnalysisContract: ...
```

抽出する literal:

- `analysis_invalid` 11種: doc [427-442](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:427>)。
- registry violation 5種: [364-369](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:364>)。
- status 4値: [376-384](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:376>)。
- 順位3段と rejected/aborted tie、missing 非 tie: [397-405](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:397>)。
- block score `1`, `1/2`, `0`: [408-417](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:408>)。
- `A_min = 0.60` と判定閾値禁止: [294-313](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:294>)。
- `n = 201`、検定単位 `block`: [315-345](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:315>)。
- block ごとの独立 `1/2`、実走前固定: [273-280](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:273>)。
- `Bin(m,1/2)` の上下裾、`m=0` の p 値1: [448-459](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:448>)。
- 片側 `0.025`、両方向 `0.05`: [338](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:338>)、[456-459](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:456>)。
- verdict 7分岐の順と4表示分類: [462-486](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:462>)。
- `theta` の Clopper-Pearson 厳密両側95%、`m=0` の `[0,1]` と推定不能: [491-494](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:491>)。
- duplicate / dry-pass / 停止 / crash / 終端なし → missing: [383-384](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:383>)。

anchor は raw heading 完全一致にしない。実 doc では H4 `5.1.1` が [223](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:223>) に1件、対象 H5 は [242](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:242>)、[294](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:294>)、[315](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:315>)、[351](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:351>)、[462](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:462>)、[496](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/docs/phase3-b4-reflux-ablation-preregistration.md:496>) に各1件だけである。

抽出では次を行う。

1. UTF-8 strict decode。
2. fenced code / HTML comment 内 heading を除外。
3. heading text を NFKC、inline code/strong marker除去、空白畳込み。
4. H4 fingerprint `5.1.1 + 分析契約 + 一括凍結` を一意要求。
5. その配下の6 H5 fingerprint を各一意・順序 exact で要求。
6. body は空白、強調記号、段落改行を正規化してから、ラベル付き list/文の範囲だけを読む。
7. doc 不読、decode失敗、節0件/複数件、literal欠落/重複はすべて例外で fail-closed。

恒真化対策:

- runtime implementation は doc を import/read しない。
- consumer は contract module の AST を読み、定数 assignment と Enum value が `ast.Constant`、literal tuple、または `Fraction(<int>, <int>)` のみであることを検査する。
- doc 抽出値と、import 済み implementation 値を別々に exact 比較する。
- `evaluate_analysis()` の振る舞いは contract test の独立変異入力で検査する。

限界として、AST は「指定した定数が literal」であることは確認できるが、悪意ある実装が別の隠し定数を演算に使うことまで完全には証明できない。これを behavior mutation と、consumer・contract・docを別 file ownerにすることで補う。同一変更で consumer と実装とテストを全部弱めれば機械だけでは止められない。

テスト新規:

`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py`

nodeid 案:

- `test_current_document_contract_literals_match_implementation`
- `test_each_analysis_invalid_literal_mutation_is_rejected`
- `test_each_registry_violation_literal_mutation_is_rejected`
- `test_status_rank_and_threshold_mutations_are_rejected`
- `test_sign_test_and_clopper_pearson_literal_mutations_are_rejected`
- `test_harmless_whitespace_emphasis_and_paragraph_reflow_are_accepted`
- `test_duplicate_h4_or_h5_anchor_fails_closed`
- `test_missing_section_or_literal_fails_closed`
- `test_non_utf8_document_fails_closed`
- `test_contract_constant_derived_from_document_is_not_a_source_literal`
- `test_contract_enum_values_must_be_literal_assignments`

### 4. `p3_b4_analysis_ledgers.py`、S4・S5

新規: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_ledgers.py`

`attempt_registry_core` の full state machine は再利用しない。

理由:

- core の event は `start` / `classification` / `terminal` 等に閉じている [35-42](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/attempt_registry_core.py:35>)。
- profile に custom event を登録しても `_parse_row()` が `_CORE_SEMANTIC_EVENTS` 外を拒否する [741-757](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/attempt_registry_core.py:741>)。
- replay は attempt lifecycle の順序と terminal null matrix を hardcode する [986-1333](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/attempt_registry_core.py:986>)。
- B-4 が必要とする `scheduled-attempt` と、後続の `protocol-violation` event を既存 core に押し込むと意味がずれる。

したがって `SchemaProfile` / `DomainProfile` / `RegistryLayout` はいずれも構築しない。ここは「独立 state machine」である。ただし stateless primitive の `canonical_json_bytes()` [197-206](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/attempt_registry_core.py:197>) と `chained_event_row()` [239-250](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/attempt_registry_core.py:239>) は再利用し、hash-chain の重複実装は避ける。

予定配置:

- L1-125: registry / manifest schema、closed enum。
- L126-280: scheduled registry strict loader、append、完全性。
- L281-405: eligibility、manifest generator、再生成比較。
- L406-520: seed/schedule、遵守検査。
- L521-590: post-run violation append と binding receipt。

公開 API:

```python
class ScheduledAttemptReason(Enum): ...
class ManifestState(Enum): ...
class AssignmentArmOrder(Enum): ...

@dataclass(frozen=True, slots=True)
class ScheduledAttemptInput: ...
@dataclass(frozen=True, slots=True)
class ScheduledAttemptRegistry: ...
@dataclass(frozen=True, slots=True)
class RandomizationSeedRecord: ...
@dataclass(frozen=True, slots=True)
class AnalysisManifest: ...
@dataclass(frozen=True, slots=True)
class DesignNotFeasible: ...
@dataclass(frozen=True, slots=True)
class ManifestCompletenessReceipt: ...
@dataclass(frozen=True, slots=True)
class ExecutionAssignmentObservation: ...

def load_scheduled_attempt_registry(data: bytes) -> ScheduledAttemptRegistry: ...

def append_scheduled_attempt(
    registry: ScheduledAttemptRegistry,
    attempt: ScheduledAttemptInput,
) -> ScheduledAttemptRegistry: ...

def append_registry_violation(
    registry: ScheduledAttemptRegistry,
    *,
    attempt_id: str | None,
    block_id: str | None,
    reason: RegistryViolationReason,
    evidence_sha256: str,
) -> ScheduledAttemptRegistry: ...

def assert_scheduled_registry_complete(
    *,
    scheduled_inputs: Sequence[ScheduledAttemptInput],
    registry: ScheduledAttemptRegistry,
) -> None: ...

def derive_registry_violation_count(
    registry: ScheduledAttemptRegistry,
) -> int: ...

def derive_assignment(
    *,
    seed: RandomizationSeedRecord,
    block_id: str,
) -> AssignmentArmOrder: ...

def generate_analysis_manifest(
    *,
    registry: ScheduledAttemptRegistry,
    seed: RandomizationSeedRecord,
) -> AnalysisManifest | DesignNotFeasible: ...

def assert_analysis_manifest_complete(
    *,
    registry: ScheduledAttemptRegistry,
    manifest: AnalysisManifest,
) -> ManifestCompletenessReceipt: ...

def verify_assignment_schedule(
    manifest: AnalysisManifest,
) -> None: ...

def assignment_followed(
    *,
    manifest: AnalysisManifest,
    observation: ExecutionAssignmentObservation,
) -> bool: ...

def assert_manifest_unchanged_before_run(
    *,
    frozen_manifest_bytes: bytes,
    observed_manifest_bytes: bytes,
) -> None: ...

def record_postrun_manifest_mutation(
    registry: ScheduledAttemptRegistry,
    *,
    frozen_manifest_bytes: bytes,
    observed_manifest_bytes: bytes,
) -> ScheduledAttemptRegistry: ...
```

registry は genesis 1行、`scheduled-attempt` 全件、必要なら `protocol-violation` 追記行からなる canonical JSONL。既存 bytes を prefix として保持しない候補更新は拒否する。成功した attempt だけを渡す helper は作らず、`assert_scheduled_registry_complete()` が元の全 schedule input と exact 再生成比較する。

canonical 順序は registry physical append order。同じ schedule batch ordinal の入力は append 前に attempt id 辞書順へ正規化する。manifest は eligibility predicate を満たす行をその順に選び、先頭201件だけを取る。201未満は短い manifest を返さず `DesignNotFeasible(reason="design_not_feasible")`。

protocol violation count は eligibility filter より前に全 registry rowから数える。未認識 violation reason は registry schema errorであり、0件へ丸めない。

再生成完全性の正例:

```text
registry:
  a000 ... a200 = eligible 201件、append順
  z-screen      = screening_only_red 1件
  protocol violation = 0件

manifest:
  generate_analysis_manifest(registry, fixed_seed) の結果そのもの
```

`assert_analysis_manifest_complete(registry, manifest)` は、registry から eligibility、順序、先頭201件、reference、schedule をすべて再計算し、row tuple と canonical bytes の両方を exact 比較して `row_count=201` の receipt を返す。単に manifest hash が一致するだけでは通さない。

割当 seed は環境変数、時刻、`random` の implicit seed を使わない。`RandomizationSeedRecord` は exact schema:

```text
schema_version = p3-b4-assignment-seed/v1
seed_hex       = lowercase 64 hex
registry_prefix_sha256
source_receipt_sha256
```

`derive_assignment()` は domain-separated HMAC-SHA256 の1 bitから on-first/off-first を決める。manifest に seed record 全体を固定し、第三者は同じ関数で再計算する。seed を実際に一様抽出して事前登録する producer は現 repo に無いため、この API は explicit seed receipt が無ければ動かさない。

schedule 違反は `assignment_followed()` が manifest の2 slotと実行記録の2 slotを exact 比較する。false は `assignment_schedule_violated` として registry に追記し、統合経路が verdict の `registry_violation_count` と block の `assignment_followed` の両方へ渡す。

テスト新規:

`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_ledgers.py`

nodeid 案:

- `test_registry_append_is_strict_prefix_and_hash_chained`
- `test_registry_completeness_rejects_success_only_subset`
- `test_registry_preserves_failed_duplicate_corrupt_and_screening_rows`
- `test_manifest_uses_registry_order_and_attempt_id_tiebreak`
- `test_manifest_selects_first_201_eligible_rows_only`
- `test_fewer_than_201_eligible_rows_is_design_not_feasible`
- `test_assert_analysis_manifest_complete_accepts_exact_regeneration`
- `test_manifest_added_deleted_reordered_or_driver_swapped_is_rejected`
- `test_manifest_hash_without_row_equality_is_not_completeness`
- `test_registry_violation_count_is_derived_before_eligibility_filter`
- `test_assignment_is_deterministic_from_seed_and_block_id`
- `test_verify_assignment_schedule_recomputes_every_row`
- `test_schedule_mutation_after_freeze_is_protocol_violation`
- `test_observed_slot_order_mismatch_is_assignment_schedule_violated`
- `test_ledgers_have_no_random_time_or_environment_import`

### 5. 統合 path、S2・S4・S5 の接続

新規: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_path.py`

親案に不足していた統合単位である。

公開 API:

```python
def evaluate_b4_artifacts(
    *,
    floor: object,
    contract_binding: ContractBinding,
    scheduled_registry_bytes: bytes,
    analysis_manifest_bytes: bytes,
    raw_analysis_records: object,
) -> AnalysisResult: ...
```

予定 L1-150 で次を順番に行う。

1. registry strict load。
2. manifest strict load。
3. manifest hash / registry hash と `contract_binding` の一致。
4. registry から manifest の行集合・順序・schedule を再生成して exact 比較。
5. registry violation count を全 registry から導出。
6. raw execution slot と manifest schedule を比較。
7. adapter で全 block を構築。
8. `evaluate_analysis()` を呼ぶ。

この path は caller から `registry_violation_count` や `assignment_followed` を受け取らない。したがって violation 行を manifest から外して count=0を注入する経路を、通常の実行 path では塞げる。

テスト新規:

`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_path.py`

S6 の必須負例を実体名と対応させる。

|負例|呼ぶ実関数 / nodeid 案|
|---|---|
|(a) violation 行を manifest から外す|`evaluate_b4_artifacts()` / `test_evaluate_b4_artifacts_registry_violation_cannot_be_washed_by_manifest_filter`|
|(b) manifest の追加・削除・並べ替え|`assert_analysis_manifest_complete()` / `test_manifest_post_generation_add_delete_reorder_each_fail_exact_regeneration`|
|(c) `A_min` を判定閾値に使う|`evaluate_analysis()` / `test_evaluate_analysis_establishes_below_a_min_when_p_on_is_significant`|
|(d) missing 除外、または rejected/aborted と tie|`block_score()` と `evaluate_analysis()` / `test_missing_is_counted_and_strictly_below_rejected_and_aborted`|
|(e) 検証前に verdict 分岐|`evaluate_analysis()` / `test_invalid_input_never_reaches_evaluate_validated_analysis`|
|(f) violation count > 0 で成立|`evaluate_b4_artifacts()` / `test_positive_violation_count_cannot_return_established`|
|(g) 汚染を先に評価|`evaluate_analysis()` / `test_protocol_failure_precedes_contamination_in_combined_case`|

恒真な検査を避けるため、fixture generator で「条件を満たす候補だけ」を抽出してから assert しない。各 mutation test は次の3点を同じ real validator に通す。

1. 無制限の raw mappingから作った正例が通る。
2. 1 fieldだけ変えた bytes/rowが実際に異なる。
3. 変異後が同じ public validator で落ちる。

`A_min` 例、missing 対 rejected 例、violation + contamination 同時例は、判定したい述語が候補集合の定義から含意されない具体値を使う。

## 所有分割

親案の file 所有は素集合だが、B と C の成果を verdict へ接続する owner がない。このままでは direct adapter caller が `registry_violation_count=0` や `assignment_followed=True` を自己申告できる。

改訂案は A → B/C 並列 → D 統合である。

### 単位 A: contract、先行

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_contract.py`

### 単位 B: adapter + 文面 consumer、A 後に C と並列

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_adapter.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_adapter.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py`

### 単位 C: ledgers + schedule、A 後に B と並列

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_ledgers.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_ledgers.py`

### 単位 D: 統合 path、B/C 後

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_path.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_path.py`

4単位の所有 path は完全に素集合。依存は次だけである。

```text
A contract
├── B adapter + consumer
├── C ledgers + schedule
└── B + C 完了後
    └── D artifact-to-verdict path
```

`docs/phase3-b4-reflux-ablation-preregistration.md` はどの単位も編集しない。既存テストの期待集合・allowlist・ledgerも編集しない。

## 実在確認と焦点走

### DW-O13 実在確認

|gate|必要入力|実在状況|
|---|---|---|
|文面一致 consumer|事前登録 doc bytes、contract source bytes|両 file は実在。実行可能。|
|precursor eligibility|whiteboard result、digest red class、calibrated workload、bootstrap membership、一意 reference、arm digest 未受領|whiteboard と digest loader は実在。calibrated B-4 workload、bootstrap 集合、reference resolver、arm digest 汚染 field は不在。現在は manifest 生成不能。|
|scheduled registry 全件性|権威ある scheduled attempt 全列|producer 不在。新 generator は入力を要求できるが、現実の全列を供給する launcher が無い。|
|reference gate|`reference_tps`、snapshot hash、receipt hash、PerfConfig/env_tag 一致|TPS 候補値は WAL にあるが、祖先一意 resolver と2 hash が不在。gate は現在到達不能。|
|status adapter|fresh terminal、execution disposition、whiteboard result、throughput|whiteboard/WAL は実在。duplicate/crash/stopを区別して durable に書く disposition producer は不在。|
|treatment gate|arm 別 `treatment_fired`|producer 不在。digest textから推定しない。|
|contamination gate|arm 別 `contaminated`|producer 不在。|
|protocol gate|arm 別 `protocol_ok`、registry violation rows|aggregate bool producerとB-4 registryが不在。|
|manifest completeness|registry、seed receipt、frozen manifest bytes|generatorは新設可能。実 artifact、seed receipt producerは不在。|
|assignment schedule|事前 seed、manifest schedule、実行 slot 順|3つとも現 B-4 producer 不在。|
|統計/verdict|floor、binding、violation count、201 block|純関数は実装可能。floor と完全な201 block artifact は不在。|

したがって本 wave は機械部品と fail-closed pathを作れるが、DW-O13 の意味で実成果物から到達可能な正式実走 pathにはならない。特に P2 を理由に §6 前提条件 9を「充足」と更新してはならない。producer が land するまで事前登録は発効前のままである。

### 焦点走

新 module の直接 consumer:

- `orchestrator/tests/test_p3_b4_analysis_contract.py`
- `orchestrator/tests/test_p3_b4_analysis_adapter.py`
- `orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py`
- `orchestrator/tests/test_p3_b4_analysis_ledgers.py`
- `orchestrator/tests/test_p3_b4_analysis_path.py`

自動走査による既存 consumer nodeid:

- `orchestrator/tests/test_campaign_import_invariant.py::test_real_repository_legacy_namespace_matches_exception_ledger`
- `orchestrator/tests/test_campaign_import_invariant.py::test_real_campaign_package_has_canonical_direct_bootstrap`
- `orchestrator/tests/test_campaign_import_invariant.py::test_real_campaign_package_uses_relative_sibling_imports`
- `orchestrator/tests/test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`
- `orchestrator/tests/test_p3_build_authority_cli.py::test_tracked_python_coder_authority_ast_closure_is_exact`
- `orchestrator/tests/test_p3_build_authority_cli.py::test_python_ccbench_manual_materializers_are_explicitly_non_admissible`
- `orchestrator/tests/test_p3_exploration_namespace.py::test_driver_contract_registry_is_exact`
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_calibration_capability_issuer_has_one_certify_call_site`
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_reviewed_ccbench_measurement_launches_use_bounded_sites`
- `orchestrator/tests/test_p3_s4_loop.py::test_backoff_coder_text_materialization_ingress_is_closed_and_nonempty`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_best_effort_qdel_production_caller_is_only_fresh_gate`
- `orchestrator/tests/test_t1286_commit_receipt.py::test_production_commit_producer_census_is_exactly_five`
- `orchestrator/tests/test_t1286_commit_receipt.py::test_verification_capability_issuer_call_site_is_exactly_core_entrypoint`
- `orchestrator/tests/test_t338_submission_gate_unit5.py::test_receipt_publish_call_sites_are_path_aware_and_allow_event_sink`
- `orchestrator/tests/test_login_headroom.py::test_ceiling_numeric_literal_occurs_only_in_login_headroom_module`
- `orchestrator/tests/test_login_headroom.py::test_local_budget_constants_are_defined_only_in_login_headroom_leaf`
- `orchestrator/tests/test_check_subprocess_bytecode_guard.py::test_real_repo_clean`
- `orchestrator/tests/test_reflux_ir.py::test_golden_has_no_production_import_and_production_has_no_golden_consumer`
- `orchestrator/tests/test_s1_known_axes_freeze.py::test_goldens_helper_is_independent_of_production`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_production_use_perf_keyword_call_sites_are_a_closed_set`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches`
- `orchestrator/tests/test_s8b_floor_stats.py::test_live_refreeze_comparison_is_centralized_once_and_has_three_callers`
- `orchestrator/tests/test_s8b_oracle_manifest_contract.py::test_loader_production_consumer_sets_are_pinned_for_spec_reverification`
- `orchestrator/tests/test_s8b_oracle_manifest_contract.py::test_verify_manifest_production_consumer_set_is_auxiliary_pin`
- `orchestrator/tests/test_s8b_oracle_report.py::test_build_observations_production_caller_is_main_only`
- `orchestrator/tests/test_s8b_ratified_freeze.py::test_no_production_module_constructs_ratified_freeze_directly`
- `orchestrator/tests/test_calibration_freeze_stage6_candidate_gate.py::test_stage6_candidate_gate_caller_inventory_matches_repository_and_docs`
- `orchestrator/tests/test_pegasus_policy_registry.py::test_direct_shared_policy_reads_of_moved_keys_are_a_best_effort_tripwire`
- `orchestrator/tests/test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact`
- `orchestrator/tests/test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control`
- `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`

親が実測するときは必ず `python3 tools/run_tests.py` 経由とする。ここでは1 nodeも緑と報告しない。

## 残る不確実性

- B-4用の一様 seedを誰が、どの receipt schemaで、いつ生成するかは未実装。HMACによる schedule 再現性は閉じられるが、seedの一様性と事前性は producer receiptなしには証明できない。
- `contract_binding.registry_sha256` が pre-run prefix と final append-only registry のどちらを指すか、文面は明示していない。計画では manifest が pre-run prefix hashを持ち、分析 binding が final registry hashを持つ二段 sealとするが、命名の裁定余地が残る。
- `execution_disposition` と実行 slot 順を durable artifactへ書く producer が無い。T-1840 がこれを所有するかは、親側で scope 接続を確認する必要がある。
- `reference_tps` の祖先探索に使える snapshot graphと、throughput receiptの正本が未特定。既存 `fitness_tps` と build admission receiptを代用品にしてはならない。
- AST hardcode検査は、実装が指定定数を literalとして持つことは示せるが、別の隠し演算経路がないことの完全証明ではない。
- literal `glob` / `rglob` / Git列挙と主要 `os.walk` は調べたが、patternを実行時に連結する未知の独自scannerまで完全に列挙したとは断言できない。

## 総括

S1-S6 は5 production file、5 test fileへ分けるのが安全である。  
exact 算術は `Fraction + math.comb`、CPは exact 二項裾比較による rational bracketで実装する。  
full `attempt_registry_core` は event意味が合わないため使わず、canonical JSONとhash-chain primitiveだけを再利用する。  
文面 consumerは正規化した一意heading構造を使い、無害な空白・強調・改行変更を許容しつつ欠落や重複には fail-closedとする。  
親のA → B/C並列案には、violation countとschedule complianceを偽装不能に接続する単位Dを追加する。  
producer不在fieldは既定値や推定で補わないため、本wave単独では§6前提条件9を充足済みとは宣言できない。