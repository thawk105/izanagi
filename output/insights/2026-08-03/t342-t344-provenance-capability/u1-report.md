実装単位 U1 を完了し、変更は次の所有 3 ファイルだけに残しています。docs・commit・git add・branch 操作は行っていません。

- [build_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u1/orchestrator/campaign/build_admission.py)
- [source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u1/orchestrator/campaign/source_digest.py)
- [test_build_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u1/orchestrator/tests/test_build_admission.py)

### 変更前の受理・拒否挙動

- STOCK: `BuildAdmission(STOCK_OR_PINNED)` という caller 宣言だけで受理。clean、source token、repo 正本 pin は未検査。
- HUMAN: `BuildAdmission(HUMAN_REVIEWED)` だけで受理。review receipt、review ID、対象 source との束縛なし。
- MACHINE: `BuildAdmission(MACHINE_SWEEP)` だけで受理。generator ID、入力 digest、対象 source との束縛なし。
- CODER: `BuildAdmission(CODER_DERIVED, True)` で受理。plain bool が authority で、false は拒否。`require_build_admission()` は exact 型と bool/class 関係だけを再検査。

旧 `test_build_admission.py` の直接 constructor 前提だけを変更しました。これは段 4 §1-E に列挙された変更であり、caller 自己申告を正例とする旧期待が新契約では誤りだからです。

### 公開 API の最終 signature

```python
# source_digest.py
@dataclass(frozen=True, slots=True)
class SourceEvidence:
    schema_version: str
    source_root: str
    ccbench_commit: str
    genome_sha256: str
    src_token: str
    source_bytes_sha256: str
    tracked_clean: bool
    tracked_diff_sha256: str
    tracked_paths: tuple[str, ...]

    def as_receipt(self) -> dict[str, object]
    @classmethod
    def from_receipt(cls, value: object) -> SourceEvidence

def resolve_evidence(
    genome: Genome,
    ccbench_commit: str,
    *,
    ccbench_dir: str = "",
    cxx: str = "g++-13",
) -> SourceEvidence

# 既存互換 API
def resolve(genome: Genome, ccbench_commit: str,
            ccbench_dir: str = "", cxx: str = "g++-13") -> str
def src_token(genome: Genome, ccbench_commit: str,
              ccbench_dir: str = "", cxx: str = "g++-13") -> str
def assert_worktree_within_allowlist(ccbench_dir: str = "") -> None
```

```python
# build_admission.py
class BuildProvenance(str, Enum):
    STOCK_BASELINE = "stock-baseline"
    CODER_AUTHORED = "coder-authored"
    MACHINE_GENERATED = "machine-generated"
    HUMAN_REVIEWED = "human-reviewed"

class GeneratorId(str, Enum): ...
class ReviewId(str, Enum): ...

# 以下は init=False の factory-only sealed 型
class CoderBuildAuthority: ...
class BuildAdmissionPolicy:
    sha256: str
    def as_preimage(self) -> Mapping[str, object]

class BuildRunContext:
    @property
    def policy(self) -> BuildAdmissionPolicy
    @property
    def generator_id(self) -> GeneratorId

class GeneratorReceipt:
    def as_receipt(self) -> Mapping[str, object]

class ReviewReceipt:
    def as_receipt(self) -> Mapping[str, object]

class BuildAdmission:
    @property
    def provenance(self) -> BuildProvenance
    @property
    def provenance_class(self) -> BuildProvenance
    @property
    def receipt_sha256(self) -> str
    def as_cache_identity(self) -> Mapping[str, object]
    def as_wal_receipt(self) -> Mapping[str, object]

def add_coder_build_authority_argument(
    parser: argparse.ArgumentParser,
    *,
    dest: str = "coder_build_authority",
) -> None

def build_run_context(
    *,
    generator_id: GeneratorId,
    coder_authority: CoderBuildAuthority | None = None,
) -> BuildRunContext

def attest_generator_output(
    context: BuildRunContext,
    source: SourceEvidence,
    *,
    generator_input_sha256: str,
) -> GeneratorReceipt

def verify_review_receipt(
    review_id: ReviewId,
    source: SourceEvidence,
    *,
    receipt: Mapping[str, object],
) -> ReviewReceipt

def derive_build_admission(
    context: BuildRunContext,
    source: SourceEvidence,
    *,
    generator_receipt: GeneratorReceipt | None = None,
    review_receipt: ReviewReceipt | None = None,
) -> BuildAdmission

def require_build_admission(
    value: object,
    *,
    expected_policy: BuildAdmissionPolicy,
    expected_source: SourceEvidence,
) -> BuildAdmission

def validate_build_admission_receipt(
    value: object,
    *,
    expected_policy: BuildAdmissionPolicy,
    expected_source: SourceEvidence | None = None,
) -> Mapping[str, object]
```

永続 admission receipt は exact-key で、`schema/class/policy_sha256/source/generator_id/review_id/input_sha256/generator_receipt/review_receipt/authority_kind/receipt_sha256` を保持します。generator/review は outer SHA だけでなく canonical body 全体を保存します。

### 検査結果

pytest nodeid は実行していません。ホストが `pegasus02` であり、AGENTS.md の上位規律がログインノード上の単一 pytest も禁止しているためです。

実行済み:

- `python3 -m py_compile` — 変更した production 2 ファイルと test 1 ファイルに成功
- `git diff --check` — 成功

未実行:

- `test_build_admission.py` の全 15 nodeid
- 既存関連テスト
- フルスイート、build、campaign 実走、mutation
- repository checker 群

### 他単位未 land により期待される赤

- U2: `buildcache.py`、`pipeline.py`、`loop.py`、`screening_driver.py` が旧 `require_build_admission(value)` signature のまま。
- U3: 通常 caller が直接 `BuildAdmission(...)` を構築し、5 CLI も plain bool のまま。
- U4: `s6_sort_sweep.py`、`s8a_trigger_sweep.py` が module-level 直接 constructor を保持。
- U5: `s8b_floor_campaign.py`、`s8b_oracle_driver.py`、`qualification/t126_driver.py` が旧 constructor を保持。
- 対応するテストは collection/import 時または旧 API 呼出時に赤くなる可能性がある。

それ以外の回帰赤は観測していません。ただし pytest 未実行のため「存在しない」とは主張しません。

### 所有外への静的波及

直接 caller/consumer:

- `backoff_{overthrottle,profile,repro,sweep}.py`
- `between_run_floor.py`、`demo.py`、`p2_2.py`
- `p3_kickoff.py`、`p3_s4_red.py`、`p3_s4_loop*.py`
- `s1_direct_comparison.py`、`s1_verify_extime_calibration.py`
- `s2_verify_calibration.py`、`s3_lock_coverage.py`、`s5_permutation_coverage.py`
- `sanity_silo.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`
- `s8b_floor_campaign.py`、`s8b_oracle_driver.py`
- `buildcache.py`、`pipeline.py`、`loop.py`、`screening_driver.py`
- `qualification/t126_driver.py`

直接旧 fixture/API を持つテスト:

- `test_build_site_gate.py`
- `test_buildcache_v2.py`
- `test_campaign.py`
- `test_p3_exploration_namespace.py`
- `test_p3_s4_loop_trigger_gating.py`
- `test_s1_direct_comparison.py`
- `test_screening_driver.py`
- `test_s8b_floor_campaign.py`
- `test_s8b_oracle_driver.py`
- `test_t126_qualification_driver.py`
- 加えて `test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py` は対象 module import により波及し得ます。

### 実装しなかった項目

- U2–U5 の caller、cache/replay identity、overlay、consumer、S8b、qualification は所有外のため未編集。
- immutable source snapshot は段 4 §3-7 の scope 外。status/diff の矛盾は拒否しますが、ABA/混在 snapshot 自体は閉じていません。
- docs、handoff、worklog、decisions、commit、provenance 監査はユーザー禁止および親担当のため未実施。
- pytest はログインノード規律により未実施。

## 総括

最重要の設計判断は次の 3 点です。

1. class を constructor 引数から除去し、repo pin付き clean STOCK、source-bound review、run-bound generator、parser-issued coder tokenの順で導出する。
2. `SourceEvidence` に canonical source root、tracked clean/path/diff、source digestをまとめ、receipt・build境界で同じ root/evidenceを照合可能にする。
3. 永続 receipt は full canonical bodyとouter SHAを持ち、未知 key、欠落、policy/source/class不整合をfail-closedで拒否する。

既知限界は、同一 process 内発行器の真正性、shell materializer、ABA/混在 snapshot、推移的 provenanceが未閉包であることです。これらには security creditを与えない旨をmodule docstringへ明記しています。