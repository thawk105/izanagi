# 実装プラン

dev-wave 段2の read-only preflight に従い、brief、対象コード、実 calibration receipt、既存テスト経路を静的確認した。実装・pytest 実行はしていない。

## 1. 確認した authority と非束縛 field

実ファイル `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json` では、gate の authority は次の実在 field だけである。

- `acquisition_receipt.toolchain.compiler_path`
- `acquisition_receipt.toolchain.compiler_version`
- `acquisition_receipt.toolchain.cmake_version`
- `acquisition_receipt.ccbench.build_argv` 内の
  `-DCMAKE_C_COMPILER=...` と `-DCMAKE_CXX_COMPILER=...`

実値は CC `/usr/bin/x86_64-linux-gnu-gcc-11`、CXX `/usr/bin/x86_64-linux-gnu-g++-11`、cmake `3.25.0`。`cxx_version` と `cmake_path` は receipt に存在しない。

型側でも `schema_v2.py:389-399` の `ToolchainReceipt` と `:403-413` の `CcbenchReceipt`、`:446-452` の `AcquisitionReceipt` に一致する。floor は `s8b_floor_campaign.py:2850-2853` で既に hash 検証済みの `VerifiedCalibration.calibration` を得ているので、calibration JSON を再読しない。

## 2. 新規 pure module の API

新設:

`orchestrator/campaign/toolchain_binding.py`

```python
TOOLCHAIN_BINDING_SCHEMA = "toolchain-binding/v1"
KNOWN_UNBOUND_FIELDS = ("cmake_realpath", "cxx_version")


class ToolchainBindingError(ValueError):
    """toolchain receipt・観測・report が照合不能または不一致。"""


@dataclass(frozen=True)
class ToolchainSnapshot:
    cc_realpath: str
    cxx_realpath: str
    cmake_realpath: str
    cc_version_first_line: str
    cxx_version_first_line: str
    cmake_version_first_line: str


@dataclass(frozen=True)
class ToolchainBindingReport:
    attempt_leg: Literal["provided", "omitted"]
    cc_realpath: str
    cxx_realpath: str
    cc_version_body: str
    cmake_version_body: str
    known_unbound_fields: tuple[str, ...]


def tool_version_body(version: str) -> str:
    ...


def version_first_line(version: str) -> str:
    ...


def snapshot_from_manifest(
    manifest: Mapping[str, object],
    *,
    expected_cc: str,
    expected_cxx: str,
) -> ToolchainSnapshot:
    ...


def extract_registered_compiler_paths(
    build_argv: Sequence[object],
) -> tuple[str, str]:
    ...


def assert_registered_compiler_binding(
    *,
    receipt_build_cc_realpath: str,
    receipt_build_cxx_realpath: str,
    receipt_toolchain_cc_realpath: str,
    receipt_cc_version: str,
    observed_cc_realpath: str,
    observed_cxx_realpath: str,
    observed_cc_version: str,
) -> None:
    ...


def bind_floor_toolchain(
    *,
    receipt_toolchain: Mapping[str, object],
    receipt_build_argv: Sequence[object],
    live: ToolchainSnapshot,
    attempt: ToolchainSnapshot | None,
) -> ToolchainBindingReport:
    ...


def report_to_mapping(
    report: ToolchainBindingReport,
) -> dict[str, object]:
    ...


def report_from_mapping(
    value: Mapping[str, object],
) -> ToolchainBindingReport:
    ...
```

例外契約:

- `tool_version_body`: 従来どおり malformed version に `ValueError`。
- `assert_registered_compiler_binding`: predicate mismatch に `ToolchainBindingError`。内部の malformed version は既存 silo の意味論を守るため素の `ValueError` を通す。
- それ以外の parser/binder: shape、型、欠損、重複、不一致に `ToolchainBindingError`。
- `report_to_mapping`: exact `ToolchainBindingReport` 以外は `TypeError`。

`tool_version_body` の実装は `silo_ladder_rung1.py:454-463` から次を逐語移動する。

```python
def tool_version_body(version: str) -> str:
    """起動名である第 1 token を除き、tool version 本体を返す。"""
    normalized = version.strip()
    for index, character in enumerate(normalized):
        if character.isspace():
            body = normalized[index:]
            if body.strip():
                return body
            break
    raise ValueError("tool version must contain an argv0 token and body")
```

I/O は helper の外に置く。

- live PATH・実体・`--version`: 既存 `buildcache._tool_version` / `_toolchain_manifest`
- attempt ファイル: floor 側 `_load_attempt_toolchain`
- calibration: 既存の hash-verified `VerifiedCalibration`

これにより pure helper の単体テストが login node の cmake に依存せず、silo と floor が同じ比較関数を使える。`subprocess` やファイル再読を helper に入れると、M-8 の deterministic injection seam と calibration の trust boundary を壊すため採用しない。

report の逐語形は次とする。

```json
{
  "schema_version": "toolchain-binding/v1",
  "status": "matched",
  "attempt_leg": "provided",
  "receipt_bound": {
    "cc_realpath": "/usr/bin/x86_64-linux-gnu-gcc-11",
    "cxx_realpath": "/usr/bin/x86_64-linux-gnu-g++-11",
    "cc_version_body": " (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0",
    "cmake_version_body": " version 3.25.0"
  },
  "known_unbound_fields": [
    "cmake_realpath",
    "cxx_version"
  ]
}
```

`attempt_leg` は caller 指定値ではなく `attempt is None` から helper が導出し、虚偽の `"provided"` を作れない形にする。

## 3. Gate の受理集合

次を定義する。

- `Rcc-t`: receipt `toolchain.compiler_path`
- `Rcc-a`: receipt build argv の唯一の `-DCMAKE_C_COMPILER`
- `Rcxx-a`: receipt build argv の唯一の `-DCMAKE_CXX_COMPILER`
- `Rvcc`: receipt compiler version の先頭行から argv0 を除いた body
- `Rvcm`: receipt cmake version の先頭行から argv0 を除いた body
- `L*`: live snapshot
- `A*`: attempt snapshot

pilot の受理集合は次の和集合である。

```text
Rcc-t = Rcc-a = Lcc
∧ Rcxx-a = Lcxx
∧ Rvcc = body(L.cc_version_first_line)
∧ Rvcm = body(L.cmake_version_first_line)
∧ attempt_leg = omitted

または

上記すべて
∧ Rcc-t = Rcc-a = Acc
∧ Rcxx-a = Acxx
∧ Rvcc = body(A.cc_version_first_line)
∧ Rvcm = body(A.cmake_version_first_line)
∧ attempt_leg = provided
```

official は `_assert_official_permitted` が先に無条件拒否するので、現在の production 受理集合は引き続き空集合。テストでこの guard を局所解除した後の dormant 経路では `attempt_leg=provided` だけを受理する。

拒否 signature:

```text
(missing receipt)
∨ (C/CXX definition が 0 件または複数)
∨ ¬(Rcc-t = Rcc-a)
∨ ¬(Rcc-a = Lcc)
∨ ¬(Rcxx-a = Lcxx)
∨ ¬(Rvcc = Lvcc)
∨ ¬(Rvcm = Lvcm)
∨ [attempt provided ∧ 4 predicate のいずれか不一致]
∨ [post-permit official ∧ attempt omitted]
```

CC だけ、または CXX だけ一致する混成 pair は拒否する。`cmake_realpath` と `cxx_version` は非空・型だけ検証するが authority 比較には使わず、report に既知の穴として残す。

通る正例:

```text
receipt CC   = /usr/bin/x86_64-linux-gnu-gcc-11
receipt CXX  = /usr/bin/x86_64-linux-gnu-g++-11
live CC/CXX  = 同上
attempt CC/CXX = 同上

receipt compiler first line = gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0
live/attempt first line      = x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0
receipt/live/attempt cmake   = cmake version 3.25.0
```

argv0 除去後が一致するため通る。attempt の CXX version や cmake path が異なっても、S-2 で明示受諾された非束縛 field なので通る。

## 4. file:line 単位の置換

行番号は現在の HEAD を実際に開いて確認した値。

### `orchestrator/campaign/buildcache.py`

`:127`、`:199-243`、`:454-458` は変更しない。

```python
DEFAULT_CC, DEFAULT_CXX = "gcc-13", "g++-13"
```

```python
def compilers_for_current_site() -> tuple[str, str]:
    """実 site が Pegasus compute のときだけ system compiler を選ぶ。"""
    if _resolve_site(None) == site_policy.PEGASUS_COMPUTE:
        return "gcc", "g++"
    return DEFAULT_CC, DEFAULT_CXX
```

floor だけが resolver を呼び、他 consumer の default は変えない。

gate と実 build の再観測差を閉じるため、`:575-583` の `build_v2` に narrowing-only 引数を追加する。

置換前:

```python
        timeout_s: Optional[int] = None, site: Optional[str] = None,
        dependency_prefix: str = "",
) -> BuildResult:
```

置換後:

```python
        timeout_s: Optional[int] = None, site: Optional[str] = None,
        dependency_prefix: str = "",
        expected_toolchain_manifest: Optional[Mapping[str, object]] = None,
) -> BuildResult:
```

`:657` の置換前:

```python
    toolchain = _toolchain_manifest(cc, cxx)
```

置換後:

```python
    toolchain = _toolchain_manifest(cc, cxx)
    if (
        expected_toolchain_manifest is not None
        and toolchain != expected_toolchain_manifest
    ):
        raise BuildCacheError(
            "v2 observed toolchain differs from pre-build binding"
        )
```

併せて import を逐語置換する。

```python
from typing import Any, Dict, List, Optional
```

から:

```python
from typing import Any, Dict, List, Mapping, Optional
```

これは bypass ではなく、指定時に受理集合を狭める再観測一致検査である。floor は gate が検証した manifest を必ず渡す。

### `orchestrator/campaign/silo_ladder_rung1.py`

`:41-42` の import に `toolchain_binding` を追加し、`:454-463` を削除して re-export に置換する。

置換後:

```python
from . import env_attestation, env_contract, execution_guard, patchharness
from . import silo_ladder_rung1_contract as patch_contract
from . import toolchain_binding

tool_version_body = toolchain_binding.tool_version_body
```

`:3574-3589` の置換前は現行の一体条件:

```python
        if (
            registered_dependency_pins != dependency_pins
            or tools["gcc"]["realpath"] != registered_c
            or tools["g++"]["realpath"] != registered_cxx
            or tools["gcc"]["realpath"]
            != calibration_document["acquisition_receipt"]["toolchain"][
                "compiler_path"
            ]
            or tool_version_body(tools["gcc"]["version"])
            != tool_version_body(
                calibration_document["acquisition_receipt"]["toolchain"][
                    "compiler_version"
                ]
            )
        ):
            raise DriverError("gap toolchain differs from registered calibration")
```

置換後:

```python
        if registered_dependency_pins != dependency_pins:
            raise DriverError("gap toolchain differs from registered calibration")
        try:
            toolchain_binding.assert_registered_compiler_binding(
                receipt_build_cc_realpath=registered_c,
                receipt_build_cxx_realpath=registered_cxx,
                receipt_toolchain_cc_realpath=calibration_document[
                    "acquisition_receipt"
                ]["toolchain"]["compiler_path"],
                receipt_cc_version=calibration_document[
                    "acquisition_receipt"
                ]["toolchain"]["compiler_version"],
                observed_cc_realpath=tools["gcc"]["realpath"],
                observed_cxx_realpath=tools["g++"]["realpath"],
                observed_cc_version=tools["gcc"]["version"],
            )
        except toolchain_binding.ToolchainBindingError as exc:
            raise DriverError(
                "gap toolchain differs from registered calibration"
            ) from exc
```

malformed version の素の `ValueError` は catch せず、現行 `:3512-3514` にそのまま到達させる。

### `orchestrator/campaign/s8b_floor_campaign.py`

`:83`:

```python
from . import buildcache, s8b_floor_stats, source_digest  # noqa: E402
```

から:

```python
from . import buildcache, s8b_floor_stats, source_digest, toolchain_binding  # noqa: E402
```

`:1059` の直前に I/O adapter を新設する。既存の campaign `probe_fn` は競合プロセス検査なので、二義化を避けて seam 名を `toolchain_capture_fn` とする。

```python
ToolchainCapture = Callable[
    [],
    tuple[str, str, Mapping[str, Mapping[str, str]]],
]


@dataclass(frozen=True)
class _BoundFloorToolchain:
    cc: str
    cxx: str
    manifest: Mapping[str, Mapping[str, str]]
    report: toolchain_binding.ToolchainBindingReport


def _capture_current_toolchain(
) -> tuple[str, str, Mapping[str, Mapping[str, str]]]:
    cc, cxx = buildcache.compilers_for_current_site()
    return cc, cxx, buildcache._toolchain_manifest(cc, cxx)


def _bind_current_toolchain(
    *,
    receipt_toolchain: Mapping[str, object],
    receipt_build_argv: Sequence[object],
    attempt_toolchain: toolchain_binding.ToolchainSnapshot | None,
    toolchain_capture_fn: ToolchainCapture | None = None,
) -> _BoundFloorToolchain:
    ...


def _load_attempt_toolchain(
    directory: Path,
) -> toolchain_binding.ToolchainSnapshot:
    ...
```

`_load_attempt_toolchain` は六つの exact leaf を非 symlink の通常ファイルとして一度だけ読み、path は一行、version は最大 64 KiB とする。NUL、空値、余分な path 行を拒否する。

`:1059-1062` の置換前:

```python
def build_cells(freeze: Mapping, cells: list[dict], *, ccbench_pin: str,
                out_root: Path, prepare_fn, contract, build_fn=None) -> dict[str, dict]:
    """全セルを実体化し、runner/store 専用の absolute-path runtime view を返す。"""
    build_fn = build_fn or buildcache.build_v2
```

置換後:

```python
def build_cells(
    freeze: Mapping,
    cells: list[dict],
    *,
    ccbench_pin: str,
    out_root: Path,
    prepare_fn,
    contract,
    verified_calibration,
    attempt_toolchain=None,
    build_fn=None,
) -> tuple[dict[str, dict], toolchain_binding.ToolchainBindingReport]:
    """全セルを実体化し、runtime view と build toolchain binding を返す。"""
    build_fn = build_fn or buildcache.build_v2
    if verified_calibration.calibration is None:
        raise FloorCampaignError(
            "floor build は acquisition_receipt を持つ calibration を要求する"
        )
    receipt = verified_calibration.calibration.acquisition_receipt
    bound_toolchain = _bind_current_toolchain(
        receipt_toolchain={
            "compiler_path": receipt.toolchain.compiler_path,
            "compiler_version": receipt.toolchain.compiler_version,
            "cmake_version": receipt.toolchain.cmake_version,
        },
        receipt_build_argv=receipt.ccbench.build_argv,
        attempt_toolchain=attempt_toolchain,
    )
```

これを `for cell in cells:` より前に置き、一度だけ gate を発火させる。

`:1079`:

```python
                cxx=buildcache.DEFAULT_CXX,
```

から:

```python
                cxx=bound_toolchain.cxx,
```

`:1095`:

```python
                cc=buildcache.DEFAULT_CC, cxx=buildcache.DEFAULT_CXX,
```

から:

```python
                cc=bound_toolchain.cc, cxx=bound_toolchain.cxx,
```

同じ `build_fn` 呼出しへ次を追加する。

```python
                expected_toolchain_manifest=bound_toolchain.manifest,
```

`:1136`:

```python
    return built
```

から:

```python
    return built, bound_toolchain.report
```

`:1292-1315` の `assemble_manifest` に exact report を必須追加する。

```python
def assemble_manifest(*, protocol: Mapping, protocol_sha256: str,
                      freeze_sha256: str, cells: list[dict],
                      built: Mapping, schedule: list[dict],
                      build_toolchain_binding:
                      toolchain_binding.ToolchainBindingReport) -> dict:
```

return object に追加:

```python
        "build_toolchain_binding": toolchain_binding.report_to_mapping(
            build_toolchain_binding
        ),
```

`:2440-2442` の `assemble_result` に同じ引数を追加し、`:2533-2571` の return に同名 field を追加する。汎用名 `"toolchain"` は使わない。

`:2763-2769` と `:2805-2811` の `run_campaign` / `_run_campaign_core` に次を追加する。

```python
                 attempt_toolchain=None,
```

`:2830` は逐語維持する。

```python
    _assert_official_permitted(mode)
```

その直後だけに追加する。

```python
    if mode == "official" and attempt_toolchain is None:
        raise FloorCampaignError(
            "official mode は attempt toolchain leg を必須とする"
        )
```

したがって production official は必ず既存 refusal が先に発火する。

`:3065-3069` と `:3119-3123`:

```python
        runtime_built = build_cells(
```

から:

```python
        runtime_built, build_toolchain_binding = build_cells(
```

へ変更し、`verified_calibration` と `attempt_toolchain` を渡す。`:3084-3088`、`:3138-3142` の manifest、`:3170-3175`、`:3219-3224` の result に同じ report を渡す。

`:3282-3308` の `_load_resume_manifest` は:

```python
    build_toolchain_binding = toolchain_binding.report_from_mapping(
        manifest.get("build_toolchain_binding")
    )
```

を追加し、5値目として返す。field 欠損・改竄は fail-closed。schema 定数は変更せず、nested field 自身を `toolchain-binding/v1` で versioning する。FROZEN_MANIFEST の bytes は触らない。

`:3514-3518` の parser に追加:

```python
    parser.add_argument(
        "--attempt-toolchain-dir",
        type=Path,
        default=None,
        help="attempt が捕捉した compiler/cmake path+version の格納先",
    )
```

`:3562-3569` の official literal refusal は逐語維持する。その後の pilot 経路でのみ:

```python
        attempt_toolchain = (
            _load_attempt_toolchain(args.attempt_toolchain_dir)
            if args.attempt_toolchain_dir is not None
            else None
        )
```

を実行し、`:3577-3580` の `run_campaign` に渡す。official 必須条件の正本は post-permit core gate とし、現在の CLI refusal 順序を変えない。

### `orchestrator/campaign/env_contract.py`

`:245-304` は変更しない。特に G2 の:

```python
path="output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json"
sha256="94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9"
```

と `expected_pegasus_g2_sha256` はそのまま。

### `tools/pegasus/floor_campaign.sh`

`:769-778` の六ファイル書出しは変更しない。

`:960-964` の置換前:

```bash
"$PY" -I -B "$REPO_ROOT/orchestrator/campaign/s8b_floor_campaign.py" \
  --mode official \
  --protocol "$REPO_ROOT/$PROTOCOL_PATH" \
  >&"$DRIVER_STDOUT_FD" 2>&"$DRIVER_STDERR_FD" || driver_rc=$?
```

置換後:

```bash
"$PY" -I -B "$REPO_ROOT/orchestrator/campaign/s8b_floor_campaign.py" \
  --mode official \
  --protocol "$REPO_ROOT/$PROTOCOL_PATH" \
  --attempt-toolchain-dir "$ATTEMPT_DIR" \
  >&"$DRIVER_STDOUT_FD" 2>&"$DRIVER_STDERR_FD" || driver_rc=$?
```

`:989-1001` の job-result は schema を `pegasus-floor-job-result/v2` にし、absolute path を記録せず、job-result の親から見た leaf 名を追加する。

```python
    "attempt_toolchain": {
        "state": "provided",
        "files": {
            "cc_realpath": "compiler.path",
            "cxx_realpath": "cxx.path",
            "cmake_realpath": "cmake.path",
            "cc_version": "compiler.version",
            "cxx_version": "cxx.version",
            "cmake_version": "cmake.version",
        },
    },
```

## 5. silo ladder の意味論保存

共通化後も silo の受理集合は現行のまま:

```text
dependency pins 一致
∧ observed gcc path = receipt build C
∧ observed g++ path = receipt build CXX
∧ observed gcc path = receipt toolchain compiler_path
∧ body(observed gcc full version) = body(receipt gcc full version)
```

次は追加しない。

- cmake version 比較
- cmake path 比較
- CXX version 比較
- build argv の duplicate 拒否
- first-line 化

特に silo は現行どおり `next(...)` の最初の C/CXX definition を使う。floor の unique-definition 検査は `bind_floor_toolchain` のみに置く。

意味論 drift を検出する nodeid:

- `orchestrator/tests/test_silo_ladder_rung1_driver.py::test_tool_version_body_ignores_only_argv0_and_rejects_body_mismatch`
- `orchestrator/tests/test_toolchain_binding.py::test_registered_compiler_binding_matches_silo_legacy_predicate_matrix`

後者は旧条件を独立 reference として全 predicate の真偽組合せを比較する。

## 6. M-8 の injection seam

具体的 seam は次。

```python
def _bind_current_toolchain(
    *,
    receipt_toolchain: Mapping[str, object],
    receipt_build_argv: Sequence[object],
    attempt_toolchain: toolchain_binding.ToolchainSnapshot | None,
    toolchain_capture_fn: ToolchainCapture | None = None,
) -> _BoundFloorToolchain:
```

テストでは:

```python
toolchain_capture_fn=lambda: (
    "gcc",
    "g++",
    REGISTERED_CMAKE_325_MANIFEST,
)
```

を渡し、同時に `buildcache._toolchain_manifest` を「呼ばれたら失敗」に monkeypatch する。これにより login の実 cmake 3.22.1を一切読まず、3.25.0 の一致正例と3.22.1の拒否例を完全に注入値だけで検証できる。

この seam は `run_campaign` の引数には出さず、`_bind_current_toolchain` の単体試験専用に閉じる。

## 7. 新設・改名するテストと kill 対象

改名はしない。新設 nodeid は以下。

| nodeid | kill する変異 |
|---|---|
| `orchestrator/tests/test_toolchain_binding.py::test_tool_version_body_preserves_silo_semantics` | argv0 まで比較、body の全 strip、単一 token の誤受理 |
| `...::test_registered_compiler_binding_matches_silo_legacy_predicate_matrix` | silo の4 predicate の削除・追加・順序依存 |
| `...::test_extract_registered_compiler_paths_rejects_missing_duplicate_or_non_string[*]` | first-wins、last-wins、欠損黙認 |
| `...::test_floor_binding_accepts_matching_live_and_attempt_and_records_holes` | always-reject、hole/report 欠落 |
| `...::test_floor_binding_rejects_each_live_mismatch[cc-path\|cxx-path\|cc-version\|cmake-version]` | live predicate の削除 |
| `...::test_floor_binding_rejects_each_attempt_mismatch[cc-path\|cxx-path\|cc-version\|cmake-version]` | attempt 脚の比較漏れ |
| `...::test_floor_binding_rejects_mixed_compiler_pair[cc-only\|cxx-only]` | CC/CXX 片側一致の誤受理 |
| `...::test_floor_binding_omission_is_explicit` | omitted を provided と記録、二者照合自体の省略 |
| `...::test_report_parser_rejects_missing_extra_or_changed_hole_fields[*]` | resume report の緩い parse |
| `orchestrator/tests/test_buildcache_v2.py::test_build_v2_rejects_toolchain_change_after_prebuild_binding` | gate 後の再観測 drift 黙認 |
| `orchestrator/tests/test_s8b_floor_campaign.py::test_build_cells_uses_site_pair_once_for_evidence_and_build` | `DEFAULT_CC/CXX` 残存、cell ごとの再解決 |
| `...::test_build_cells_gate_precedes_prepare_and_build` | gate の loop 内配置、build 後配置 |
| `...::test_toolchain_capture_seam_accepts_registered_cmake_without_host_probe` | login cmake の accidental read |
| `...::test_toolchain_capture_seam_rejects_injected_cmake_322_against_registered_325` | cmake predicate の削除 |
| `...::test_official_attempt_requirement_is_after_existing_permit_gate` | official refusal の順序変更・緩和 |
| `...::test_pilot_missing_attempt_records_omitted_leg` | omission の成果物記録漏れ |
| `...::test_resume_rejects_missing_or_tampered_build_toolchain_binding[*]` | report 欠損・改竄黙認 |
| `orchestrator/tests/test_pegasus_floor_tools.py::test_floor_job_attempt_file_names_match_driver_loader` | shell/driver 間の leaf 名ずれ |

既存 `orchestrator/tests/test_build_site_gate.py::test_site_compiler_helper_uses_system_gcc_only_on_actual_compute` も維持し、resolver を always-default / always-system にする変異を kill する。

## 8. 既存テストへの波及

### official guard を monkeypatch する経路

実在する monkeypatch は `test_s8b_floor_campaign.py:314,677,781,3209,3593,3856,4092,4232` の8箇所。post-permit attempt requirement により、次の既存 nodeid は attempt fixture を追加しない限り赤になる。

全行の prefix は `orchestrator/tests/test_s8b_floor_campaign.py::`。

```text
test_repo_root_seam_runs_production_clean_scan_on_real_tmp_repo
test_real_seal_protocol_to_floor_official_core_e2e
test_new_seam_defaults_delegate_to_production_functions
test_second_scan_digest_shift_persists_claim_but_issues_no_certificate
test_official_fresh_issues_certificate_and_binds_wall_ledger
test_checkpoint_callback_is_after_cert_validation_and_before_launch_start
test_checkpoint_raw_hash_recheck_fires_before_launch_start
test_official_scan_rejection_has_zero_filesystem_side_effects
test_official_build_failure_leaves_durable_launch_start
test_l_resume_rejects_extra_run_dir_file
test_l_resume_rejects_symlinked_launch_certificate
test_m_prestart_resume_starts_runner_fresh_without_resume_start
test_official_resume_validates_certificate_and_completes
test_resume_under_unchanged_current_contract_generation_completes
test_resume_rejects_recorded_g1_when_current_contract_is_g2_before_calibration
test_official_resume_rejects_tampered_certificate
test_official_resume_rejects_launch_start_utc_not_bound_to_certificate
test_official_resume_rejects_extra_launch_start_key
test_official_resume_rejects_renamed_run_dir
test_official_resume_rejects_certificate_time_not_bound_to_run_id
test_deterministic_artifacts_across_roots_and_subprocess_environments
test_each_determinism_seam_reaches_its_expected_json_pointer
```

`_assert_official_permitted` 自体を試す既存 rejection test は変更しない。`test_run_campaign_core_rejects_official_materializer_injection_before_side_effects` も materializer rejection が先なので不変。

### fake build まで到達する pilot 経路

`test_s8b_floor_campaign.py:293-317` の共通 `_run_campaign` を使う以下は、現状の legacy calibration または login toolchain を実測すると赤になる。

```text
test_floor_journal_manifest_and_binary_store_open_through_capability
test_partial_reps_invalidates_session_and_burns_retry_then_nulls_pair
test_stock_flaky_nulls_entire_holdout_including_scale_ref
test_retry_sequence_is_metamorphic_to_other_cells_values
test_probe_competing_invalidates_session_with_raw_stdout_in_journal
test_post_probe_runs_on_launch_error_and_competing_takes_precedence
test_probe_unexecutable_or_inconsistent_aborts_campaign[*]
test_probe_unparseable_pid_line_invalidates_session_not_abort
test_probe_own_descendant_pid_detected_as_competing_b2
test_performance_anomaly_invalidates_session_and_nulls_pair
test_machine_anomaly_valid_cell_but_pair_null
test_create_only_rejects_overwrite_journal_appends
test_idempotent_finalization_after_result_json_crash
test_finalize_pending_resume_rejects_tampered_staged_result
test_finalize_pending_resume_rejects_tampered_published_result
test_two_phase_finalize_crash_injection_recovers_at_all_four_boundaries[*]
test_resume_forward_only_skips_completed_and_crashed_seqs
test_resume_rejects_tampered_binary_but_succeeds_when_untampered
test_resume_rejects_tampered_manifest_schedule
test_resume_rejects_duplicate_session_start
test_resume_does_not_reissue_retry_slot_after_retry_start_crash
test_end_to_end_golden_floor_values_and_tamper_detection
test_result_json_records_per_attempt_duration_and_no_absolute_monotonic
test_floor_manifest_binary_sha256_matches_real_file_bytes
test_pilot_resume_rejects_launch_certificate_contamination[*]
test_pilot_path_has_no_launch_certificate_changes
test_binary_receipt_recorded_in_session_journal
test_content_addressed_store_create_only
test_verify_floor_artifact_binaries_positive_and_negative
```

直接 `run_campaign` を呼び、build まで到達する既存 nodeid:

```text
test_required_reservation_loss_is_typed_campaign_terminal_with_no_values
test_required_recheck_pins_remaining_budget_margin_and_injected_monotonic_clock
test_required_mode_happy_path_pins_journal_claim_and_receipt_shape
test_floor_legacy_build_fallback_hits_contract_provenance_assert
test_measure_fn_default_uses_contract_clocks_and_numactl
test_pilot_does_not_apply_official_freeze_allowlist_scan
test_current_admission_reuses_exact_contract_across_successful_run
```

対処は共通 fixture `_matching_bound_floor_toolchain()` を作り、既存の outcome 期待値を変えず `_bind_current_toolchain` だけを faithful fake にする。新規 gate test ではこの patch を使わない。

### materialization と shell

次も事前に赤となる。

```text
orchestrator/tests/test_s8b_materialization.py::test_floor_manifest_golden_stable
orchestrator/tests/test_pegasus_floor_tools.py::test_floor_driver_failure_propagates_rc[rc-0]
orchestrator/tests/test_pegasus_floor_tools.py::test_floor_driver_failure_propagates_rc[rc-2]
orchestrator/tests/test_pegasus_floor_tools.py::test_floor_driver_failure_propagates_rc[rc-7]
```

`test_floor_manifest_golden_stable` は `:494-497` の戻り値を tuple unpack し、`:520-522` へ exact fixture report を渡す。exact SHA assertion は削除・緩和せず、現在の:

```python
"9b7d1f899d4e5885aa19c4d970dc05ffb8fff3c75adfd9f81705fd55f660a99f"
```

を、上記 report 形を使った静的再計算値:

```python
"43b3471253b10941e73d883e28109b749b4c894ea536f46e659626347d015e67"
```

へ更新する。

`test_pegasus_floor_tools.py:61-73` の exact key set と `:1660-1672` の exact payload は、schema v2 と `attempt_toolchain` object を含む強い期待へ更新する。skip、xfail、部分集合比較にはしない。

## 9. 段5の所有分割

brief 原案の A/B production path は互いに重ならないが、必要な編集 path を網羅していない。補正版は次。

単位A:

```text
orchestrator/campaign/toolchain_binding.py
orchestrator/campaign/silo_ladder_rung1.py
orchestrator/tests/test_toolchain_binding.py
```

単位B:

```text
orchestrator/campaign/buildcache.py
orchestrator/campaign/s8b_floor_campaign.py
tools/pegasus/floor_campaign.sh
orchestrator/tests/test_buildcache_v2.py
orchestrator/tests/test_s8b_floor_campaign.py
orchestrator/tests/test_s8b_materialization.py
orchestrator/tests/test_pegasus_floor_tools.py
```

この補正版は素集合。Aを先に完了して helper API を固定し、Bを一つの atomic land にする。特にB内の site 解決置換と floor gate 結線を分割 commit・部分 land しない。`env_contract.py`、calibration JSON、FROZEN_MANIFEST はどちらも所有しない。

## 総括

中核: site 解決した CC/CXX を receipt・live・任意 attempt と build 前に照合し、同じ観測を buildcache が再確認する。  
最大risk: receipt に compiler binary hash がなく、同一 realpath の実体差替えまでは path/version 契約だけでは完全に閉じられない。  
不同意: P2をsiloにも適用する解釈は既存受理集合を変えるため不可。P6の「同一由来」は証明できず、「registered CC/CXX pair一致」が正確。  
段5分割: yes—ただし原案へ buildcache と3テストファイルを単位Bとして追加した補正版に限る。  
未確認のまま残した前提: なし。