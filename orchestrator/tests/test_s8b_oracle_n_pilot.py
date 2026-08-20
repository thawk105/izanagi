from __future__ import annotations

import contextlib
import ast
import hashlib
import json
import shlex
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.calibrator import perf_preflight
from orchestrator.calibrator.model import ScalePoint
from orchestrator.campaign import s1_direct_comparison
from orchestrator.campaign import s8b_holdout_freeze
from orchestrator.campaign import s8b_oracle_n_pilot as M
from orchestrator.campaign.model import Genome
from orchestrator.campaign.s1_direct_comparison import PreparedCell


ROOT = Path(__file__).resolve().parents[2]
CONFIGURATIONS = tuple(sorted(s1_direct_comparison._PREPARE_CELL_CONFIGURATIONS))
SENTINEL_RECORDS = 123457
SENTINEL_THREADS = 7


def _perf_receipt(status: str = "available") -> dict:
    if status == "available":
        available = True
        rc = 0
        parsed_events = list(perf_preflight.PERF_EVENTS)
        reason = "available"
    elif status == "unavailable":
        available = False
        rc = None
        parsed_events = []
        reason = "perf-not-found"
    else:
        assert status == "probe_error"
        available = False
        rc = None
        parsed_events = []
        reason = "probe-os-error"
    return {
        "schema": perf_preflight.SCHEMA,
        "status": status,
        "available": available,
        "probe_argv": list(perf_preflight._BASE_PROBE_ARGV),
        "rc": rc,
        "parsed_events": parsed_events,
        "reason": reason,
        "stderr_sha256": "0" * 64,
        "candidates": [],
    }


def _perf_mode(status: str = "available") -> M.PerfMode:
    receipt = _perf_receipt(status)
    return M.PerfMode(
        use_perf=perf_preflight.use_perf_from_receipt(receipt),
        receipt=receipt,
    )


def _holdout_admission_identifier(attempt_id: str) -> dict[str, str]:
    return {"role": "n_pilot", "campaign_run_id": attempt_id}


def _protocol_document() -> dict:
    return {
        "schema_version": M.PROTOCOL_SCHEMA,
        "authority": "none",
        "default_effect": "no-state-change",
        "freeze": {"path": M.FREEZE_REL.as_posix(), "sha256": "1" * 64},
        "source": {
            "commit": "2" * 40,
            "driver_path": "orchestrator/campaign/s8b_oracle_n_pilot.py",
            "driver_sha256": "3" * 64,
            "job_script_path": M.JOB_SCRIPT_REL.as_posix(),
            "job_script_sha256": "4" * 64,
        },
        "environment": {
            "env_tag": "pegasus",
            "contract_sha256": "5" * 64,
            "activation_generation": 2,
            "ccbench_pin": "6" * 40,
        },
        "design": {
            "pilot_rounds": 33,
            "master_seed": "pilot-seed",
            "allocation_count": 3,
            "allocation_role": "primary-segment",
            "reps": M.APPROVED_REPS,
            "extime_s": M.APPROVED_EXTIME_S,
            "stock_configuration": "stock_common",
            "candidate_ns": [1, 2, 3],
            "resampling_seed": "resample-seed",
            "resampling_iterations": 20,
            "ucl_confidence": 0.95,
            "deltas": [0.005, 0.01, 0.02, 0.05],
            "alphas": [0.05, 0.1],
            "conditioning": "all-rows-eligible",
            "selection_error": "indifference-zone-relative",
            "tie_rule": "not-an-error",
            "schedule_algorithm": M.SCHEDULE_ALGORITHM,
            "counterbalance_analysis": "position-and-monotonic-drift-diagnostics-only",
            "drift_diagnostics": {
                "position_metric": "spearman-rank-correlation",
                "max_abs_position_correlation": 0.95,
                "time_metric": "relative-ols-slope-per-second",
                "max_abs_relative_time_slope_per_second": 1.0,
            },
            "lower_bound": True,
        },
        "measurement_declaration": {
            "artifacts": [{"canonical_path": "/evidence/protocol.json", "sha256": "7" * 64}],
            "statement": "post-freeze Pegasus measurement bound to the declared pin",
        },
    }


def _write_protocol(path: Path, document: dict) -> Path:
    path.write_text(json.dumps(document, allow_nan=True), encoding="utf-8")
    return path


def _protocol() -> M.PilotProtocol:
    document = _protocol_document()
    design = document["design"]
    return M.PilotProtocol(
        document=document,
        protocol_sha256=hashlib.sha256(M.canonical_result_bytes(document)).hexdigest(),
        freeze_path=M.FREEZE_REL.as_posix(),
        freeze_sha256="1" * 64,
        source_commit="2" * 40,
        driver_path="orchestrator/campaign/s8b_oracle_n_pilot.py",
        driver_sha256="3" * 64,
        job_script_path=M.JOB_SCRIPT_REL.as_posix(),
        job_script_sha256="4" * 64,
        ccbench_pin="6" * 40,
        env_tag="pegasus",
        contract_sha256="5" * 64,
        activation_generation=2,
        pilot_rounds=33,
        master_seed="pilot-seed",
        allocation_count=3,
        allocation_role="primary-segment",
        stock_configuration="stock_common",
        candidate_ns=tuple(design["candidate_ns"]),
        resampling_seed="resample-seed",
        resampling_iterations=20,
        ucl_confidence=0.95,
        deltas=tuple(design["deltas"]),
        alphas=tuple(design["alphas"]),
        max_abs_position_correlation=0.95,
        max_abs_relative_time_slope_per_second=1.0,
        measurement_declaration=document["measurement_declaration"],
    )


def _freeze() -> dict:
    holdouts = {}
    for holdout_id, frozen in s8b_holdout_freeze.HOLDOUTS.items():
        holdouts[holdout_id] = {
            "records": SENTINEL_RECORDS,
            "threads": SENTINEL_THREADS,
            "ycsb": dict(frozen["ycsb"]),
            "variant_binding": {
                "entries": {
                    configuration: {"flags": {"BACK_OFF": 0}}
                    for configuration in CONFIGURATIONS
                }
            },
        }
    return {"holdouts": holdouts}


def _inputs(*, held=()) -> M.PilotInputs:
    freeze = _freeze()
    cells = M.s8b_floor_contract.enumerate_cells(
        freeze, stock_configuration="stock_common",
    )
    contract = SimpleNamespace(
        env_tag="pegasus", contract_sha256="5" * 64,
        clocks_per_us=2100, numactl=("numactl", "--interleave=all"),
    )
    return M.PilotInputs(
        protocol=_protocol(),
        freeze=freeze,
        freeze_sha256="1" * 64,
        cells=tuple(cells),
        held_markers=tuple(held),
        freeze_verification_status="held" if held else "verified",
        contract=contract,
        observed_repo_head="a" * 40,
    )


def _binary_receipts(tmp_path: Path, inputs: M.PilotInputs) -> dict[str, M.PilotBinary]:
    receipts = {}
    for index, cell in enumerate(inputs.cells):
        binary = tmp_path / f"binary-{index}"
        binary.write_bytes(f"binary-{index}".encode())
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        cell_id = str(cell["cell_id"])
        receipts[cell_id] = M.PilotBinary(
            cell_id=cell_id,
            entry_sha256="8" * 64,
            binding_sha256="9" * 64,
            binary_sha256=digest,
            binary_path=binary.resolve(),
            cache_hit=index % 2 == 0,
            materialize_elapsed_s=float(index + 1),
            worktree_identity_sha256=f"{index:064x}",
            isolated_worktree=True,
            pre_materialization_clean_assertion=True,
            source_tracked_clean=True,
            source_tracked_paths=(),
        )
    return receipts


def _observations(inputs: M.PilotInputs, rounds: int = 2) -> tuple[M.SessionObservation, ...]:
    result = []
    seq = 0
    for round_no in range(1, rounds + 1):
        for position, cell in enumerate(inputs.cells, start=1):
            configuration = str(cell["configuration_id"])
            offset = CONFIGURATIONS.index(configuration)
            outer = 100.0 + round_no + offset
            raw = (outer,) * M.APPROVED_REPS
            result.append(M.SessionObservation(
                seq=seq,
                pilot_round=round_no,
                position=position,
                cell_id=str(cell["cell_id"]),
                monotonic_start_s=float(seq),
                monotonic_end_s=float(seq) + 0.5,
                duration_s=0.5,
                load1_before=1.0,
                load1_after=1.1,
                throughputs=raw,
                throughput_binary64_hex=tuple(M._binary64_hex(value) for value in raw),
                outer_median=outer,
                abort_rate=0.1,
                returncodes=(0,) * M.APPROVED_REPS,
                binary_sha256_at_measure="a" * 64,
                cache_hit=False,
                materialize_elapsed_s=0.25,
            ))
            seq += 1
    return tuple(result)


def test_protocol_exact_schema_and_preregistered_design(tmp_path):
    loaded = M.load_protocol(_write_protocol(tmp_path / "protocol.json", _protocol_document()))
    assert loaded.pilot_rounds == 33
    assert loaded.allocation_count == 3
    assert loaded.deltas == (0.005, 0.01, 0.02, 0.05)
    assert loaded.alphas == (0.05, 0.1)
    assert loaded.max_abs_position_correlation == 0.95
    assert loaded.max_abs_relative_time_slope_per_second == 1.0
    assert loaded.protocol_sha256 == hashlib.sha256(
        M.canonical_result_bytes(_protocol_document())
    ).hexdigest()


def test_driver_has_no_round_default_and_supports_build_only_mode(tmp_path):
    args = M._parse_args([
        "--protocol", str(tmp_path / "protocol.json"),
        "--output", str(tmp_path / "result.json"),
        "--attempt-id", "attempt",
        "--cache-root", str(tmp_path / "cache"),
        "--build-only",
    ])
    assert args.build_only is True
    assert args.rounds is None
    assert args.confirm_irreversible_pilot_holdout is False
    confirmed = M._parse_args([
        "--protocol", str(tmp_path / "protocol.json"),
        "--output", str(tmp_path / "result.json"),
        "--confirm-irreversible-pilot-holdout",
    ])
    assert confirmed.confirm_irreversible_pilot_holdout is True


@pytest.mark.parametrize("mutation", ["duplicate", "nonfinite", "unknown", "short-rounds"])
def test_protocol_rejects_noncanonical_inputs(tmp_path, mutation):
    document = _protocol_document()
    path = tmp_path / "protocol.json"
    if mutation == "duplicate":
        path.write_text('{"schema_version":"x","schema_version":"y"}', encoding="utf-8")
    elif mutation == "nonfinite":
        document["design"]["ucl_confidence"] = float("nan")
        _write_protocol(path, document)
    elif mutation == "unknown":
        document["unexpected"] = True
        _write_protocol(path, document)
    else:
        document["design"]["pilot_rounds"] = 32
        _write_protocol(path, document)
    with pytest.raises(M.PilotError):
        M.load_protocol(path)


def test_m7_load_inputs_preserves_held_markers_and_held_status(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    fixtures = {
        Path("orchestrator/campaign/s8b_oracle_n_pilot.py"): b"driver",
        M.JOB_SCRIPT_REL: b"job",
        M.FREEZE_REL: b"freeze",
    }
    for name, payload in fixtures.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    protocol = replace(
        _protocol(),
        driver_sha256=hashlib.sha256(b"driver").hexdigest(),
        job_script_sha256=hashlib.sha256(b"job").hexdigest(),
    )
    marker = {"check": "held-by-ruling"}
    verified = SimpleNamespace(document=_freeze(), sha256=protocol.freeze_sha256)
    entry = SimpleNamespace(contract=SimpleNamespace(
        env_tag="pegasus", contract_sha256=protocol.contract_sha256,
    ), generation=protocol.activation_generation)
    inputs = M.load_inputs(
        protocol,
        root=root,
        load_freeze_fn=lambda *_args, **_kwargs: verified,
        verify_fn=lambda *_args, **_kwargs: (marker,),
        contract_resolver=lambda *_args, **_kwargs: entry,
        active_contract_fn=lambda _env_tag: entry.contract,
        observed_repo_head="a" * 40,
        current_head_fn=lambda _root: "a" * 40,
        gitlink_fn=lambda _root: protocol.ccbench_pin,
        submodule_head_fn=lambda _root: protocol.ccbench_pin,
    )
    assert inputs.freeze_verification_status == "held"
    assert inputs.held_markers == (marker,)
    assert inputs.observed_repo_head == "a" * 40
    assert inputs.observed_repo_head != protocol.source_commit
    assert {cell["records"] for cell in inputs.cells} == {SENTINEL_RECORDS}
    assert {cell["threads"] for cell in inputs.cells} == {SENTINEL_THREADS}


def _build_with_fakes(
    tmp_path: Path,
    *,
    inputs=None,
    oracle_fetchcontent_base_fn=None,
    oracle_dependency_fn=None,
    cached: bool = False,
    allocation_mode: bool | None = None,
):
    inputs = inputs or _inputs()
    prepare_calls = []
    build_calls = []

    @contextlib.contextmanager
    def prepare_fn(
        _cell,
        _pin,
        *,
        cxx,
        oracle_dependency_root=None,
        oracle_compiler=None,
        oracle_phase_marker=None,
    ):
        index = len(prepare_calls)
        worktree = tmp_path / f"worktree-{index}"
        worktree.mkdir()
        prepare_calls.append({
            "worktree": worktree,
            "cxx": cxx,
            "oracle_dependency_root": oracle_dependency_root,
            "oracle_compiler": oracle_compiler,
            "oracle_phase_marker": oracle_phase_marker,
        })
        yield PreparedCell(
            genome=Genome("silo", {"BACK_OFF": 0}),
            src_token="stock",
            ccbench_dir=str(worktree.resolve()),
            cache_root=str(tmp_path / "forbidden-prepared-cache"),
        )

    def build_fn(_genome, **kwargs):
        index = len(build_calls)
        binary = tmp_path / f"built-{index}"
        binary.write_bytes(f"built-{index}".encode())
        build_calls.append(kwargs)
        return SimpleNamespace(
            trace=False,
            contract_sha256=inputs.contract.contract_sha256,
            binary=str(binary.resolve()),
            bin_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
            cached=cached,
        )

    evidence = SimpleNamespace(src_token="stock", tracked_clean=True, tracked_paths=())
    counter = iter(float(value) for value in range(100))
    cache_root = tmp_path / "persistent-cache"
    cache_root.mkdir()
    if oracle_fetchcontent_base_fn is None:
        oracle_fetchcontent_base_fn = lambda *_args, **_kwargs: (
            tmp_path / "fetchcontent"
        ).resolve()
    if oracle_dependency_fn is None:
        oracle_dependency_fn = lambda *_args, **_kwargs: SimpleNamespace(
            source_root=(tmp_path / "oracle-dependency").resolve(),
        )
    result = M.build_binaries(
        inputs,
        cache_root=cache_root,
        prepare_fn=prepare_fn,
        build_fn=build_fn,
        repo_root=ROOT,
        worktree_roots=(ROOT,),
        allocation_mode=allocation_mode,
        monotonic_fn=lambda: next(counter),
        toolchain_fn=lambda _cc, _cxx: {
            "cxx": {"realpath": str((tmp_path / "cxx-sentinel").resolve())},
        },
        compiler_fn=lambda: ("cc-sentinel", "cxx-sentinel"),
        oracle_fetchcontent_base_fn=oracle_fetchcontent_base_fn,
        oracle_dependency_fn=oracle_dependency_fn,
        evidence_fn=lambda *_args, **_kwargs: evidence,
        review_fn=lambda **_kwargs: "review",
        admission_fn=lambda *_args, **_kwargs: "admission",
        context_fn=lambda **_kwargs: "context",
    )
    return inputs, cache_root.resolve(), prepare_calls, build_calls, result


def test_sort_best_materialize_receives_oracle_environment(tmp_path):
    _inputs_value, _cache, prepare_calls, _build_calls, _result = _build_with_fakes(
        tmp_path
    )
    assert prepare_calls
    assert all(call["oracle_dependency_root"] is not None for call in prepare_calls)
    assert all(call["oracle_compiler"] is not None for call in prepare_calls)
    assert {call["oracle_phase_marker"] for call in prepare_calls} == {None}


def test_cells_without_sort_best_skip_oracle_environment(tmp_path):
    inputs = _inputs()
    without_sort = replace(
        inputs,
        cells=tuple(
            cell for cell in inputs.cells
            if cell["configuration_id"] != "sort_best"
        ),
    )
    _inputs_value, _cache, prepare_calls, _build_calls, _result = _build_with_fakes(
        tmp_path,
        inputs=without_sort,
        oracle_fetchcontent_base_fn=lambda *_args, **_kwargs: pytest.fail(
            "sort_best 無しで oracle preflight が呼ばれた"
        ),
        oracle_dependency_fn=lambda *_args, **_kwargs: pytest.fail(
            "sort_best 無しで oracle dependency prebuild が呼ばれた"
        ),
    )
    assert prepare_calls
    assert {call["oracle_dependency_root"] for call in prepare_calls} == {None}
    assert {call["oracle_compiler"] for call in prepare_calls} == {None}


def test_sort_best_oracle_preflight_failure_stops_before_build(tmp_path):
    cache_root = tmp_path / "persistent-cache"
    cache_root.mkdir()
    calls = []

    def fail_dependency(*_args, **_kwargs):
        raise RuntimeError("preflight-sentinel")

    with pytest.raises(M.PilotError, match="sort_best SWO oracle preflight"):
        M.build_binaries(
            _inputs(),
            cache_root=cache_root,
            prepare_fn=lambda *_args, **_kwargs: calls.append("prepare"),
            build_fn=lambda *_args, **_kwargs: calls.append("build"),
            repo_root=ROOT,
            worktree_roots=(ROOT,),
            compiler_fn=lambda: ("cc", "cxx"),
            toolchain_fn=lambda _cc, _cxx: {
                "cxx": {"realpath": str((tmp_path / "cxx").resolve())},
            },
            oracle_fetchcontent_base_fn=lambda *_args, **_kwargs: tmp_path.resolve(),
            oracle_dependency_fn=fail_dependency,
            context_fn=lambda **_kwargs: "context",
        )
    assert calls == []


@pytest.mark.parametrize("kind", ["repo", "freeze", "symlink"])
def test_m3_cache_containment_rejects_before_prepare_or_build(tmp_path, kind):
    calls = []
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    if kind == "repo":
        cache_root = repo_root / "output" / "pilot-cache"
        expected = "repo/freeze/git worktree の外側でない"
    elif kind == "freeze":
        cache_root = repo_root / M.FREEZE_REL.parent / "pilot-cache"
        expected = "repo/freeze/git worktree の外側でない"
    else:
        external = tmp_path / "external"
        external.mkdir()
        link = tmp_path / "link"
        link.symlink_to(external, target_is_directory=True)
        cache_root = link / "pilot-cache"
        expected = "symlink 経由である"
    cache_root.mkdir(parents=True)
    with pytest.raises(M.PilotError, match=expected):
        M.build_binaries(
            _inputs(),
            cache_root=cache_root,
            prepare_fn=lambda *_args, **_kwargs: calls.append("prepare"),
            build_fn=lambda *_args, **_kwargs: calls.append("build"),
            repo_root=repo_root,
            worktree_roots=(repo_root,),
            compiler_fn=lambda: ("cc", "cxx"),
            toolchain_fn=lambda _cc, _cxx: {},
            context_fn=lambda **_kwargs: "context",
        )
    assert calls == []


def test_cache_root_must_exist_before_api_call(tmp_path):
    calls = []
    with pytest.raises(M.PilotError, match="作成済み"):
        M.build_binaries(
            _inputs(),
            cache_root=tmp_path / "missing-cache",
            prepare_fn=lambda *_args, **_kwargs: calls.append("prepare"),
            build_fn=lambda *_args, **_kwargs: calls.append("build"),
            repo_root=ROOT,
            worktree_roots=(ROOT,),
            compiler_fn=lambda: ("cc", "cxx"),
            toolchain_fn=lambda _cc, _cxx: {},
            context_fn=lambda **_kwargs: "context",
        )
    assert calls == []


def test_cache_root_identity_detects_namespace_replacement(tmp_path):
    cache_root = tmp_path / "cache"
    cache_root.mkdir()
    identity = M._directory_identity(cache_root, "cache_root")
    original = tmp_path / "cache-original"
    cache_root.rename(original)
    cache_root.mkdir()
    with pytest.raises(M.PilotError, match="identity"):
        M._assert_directory_identity(cache_root, identity, "cache_root")


def test_m4_build_is_trace_disabled_and_uses_exact_external_cache(tmp_path):
    _inputs_value, cache_root, prepare_calls, build_calls, result = _build_with_fakes(tmp_path)
    assert len(prepare_calls) == 12
    assert len(build_calls) == 12
    assert {call["trace"] for call in build_calls} == {False}
    assert {call["cache_root"] for call in build_calls} == {str(cache_root)}
    assert all("admission" in call and "source_evidence" in call for call in build_calls)
    assert len({call["ccbench_dir"] for call in build_calls}) == 12
    assert len({item.worktree_identity_sha256 for item in result.values()}) == 12
    assert {item.cache_hit for item in result.values()} == {False}


def test_allocation_cache_requires_an_empty_directory_before_build(tmp_path):
    cache_root = tmp_path / "allocation-cache"
    cache_root.mkdir()
    (cache_root / "stale-entry").write_text("stale", encoding="utf-8")
    with pytest.raises(M.PilotError, match="空 directory"):
        M.build_binaries(
            _inputs(),
            cache_root=cache_root,
            repo_root=ROOT,
            worktree_roots=(ROOT,),
            compiler_fn=lambda: pytest.fail("compiler preflight must not run"),
        )


def test_allocation_cache_hit_is_rejected_but_legacy_cache_hit_is_retained(tmp_path):
    with pytest.raises(M.PilotError, match="cache hit"):
        _build_with_fakes(tmp_path, cached=True)

    legacy_protocol = replace(_protocol(), pilot_rounds=11)
    legacy_inputs = replace(_inputs(), protocol=legacy_protocol)
    legacy_root = tmp_path / "legacy"
    legacy_root.mkdir()
    _inputs_value, _cache, _prepare, _build, result = _build_with_fakes(
        legacy_root, inputs=legacy_inputs, cached=True,
    )
    assert {item.cache_hit for item in result.values()} == {True}


def _run_one_round(
    tmp_path: Path,
    raw=(1.0, 2.0, 3.0, 4.0, 100.0),
    *,
    perf_status="available",
):
    inputs = _inputs()
    binaries = _binary_receipts(tmp_path, inputs)
    schedule = M.build_pilot_schedule(inputs, master_seed="schedule-seed", rounds=1)
    measure_calls = []
    tenant_calls = []
    preflight_calls = []
    ticks = iter(float(index) for index in range(100))

    def measure_fn(binary, records, threads, clocks_per_us, **kwargs):
        kwargs["rep_returncodes"].extend([0] * M.APPROVED_REPS)
        measure_calls.append((binary, records, threads, clocks_per_us, kwargs))
        return ScalePoint(
            records=records, threads=threads, throughputs=list(raw),
            abort_rate=0.125, run_cmd="discarded",
        )

    observations, perf_mode = M.run_sessions(
        inputs,
        binaries,
        schedule,
        measure_fn=measure_fn,
        single_tenant_fn=lambda: tenant_calls.append("checked"),
        monotonic_fn=lambda: next(ticks),
        load1_fn=lambda: 1.25,
        perf_preflight_fn=lambda **kwargs: (
            preflight_calls.append(kwargs) or _perf_receipt(perf_status)
        ),
        perf_candidates_fn=lambda _root: ("/policy/perf",),
        irreversible_pilot_holdout_approved=True,
        n_pilot_admissions={index: object() for index in range(len(schedule))},
        consume_n_pilot_attempt_ticket_fn=(
            lambda admission, *, schedule_index: {
                "admission": admission, "schedule_index": schedule_index,
            }
        ),
    )
    return (
        inputs,
        schedule,
        measure_calls,
        tenant_calls,
        observations,
        perf_mode,
        preflight_calls,
    )


def test_m5_measure_gateway_uses_perf_and_approved_shape(tmp_path):
    inputs, _schedule, calls, _tenant, observations, perf_mode, preflight_calls = (
        _run_one_round(tmp_path, perf_status="available")
    )
    assert perf_mode.use_perf is True
    assert perf_mode.receipt["status"] == "available"
    assert preflight_calls == [{"perf_candidates": ("/policy/perf",)}]
    assert len(calls) == 12
    for _binary, _records, _threads, clocks, kwargs in calls:
        assert clocks == inputs.contract.clocks_per_us
        assert kwargs["use_perf"] is True
        assert kwargs["reps"] == M.APPROVED_REPS
        assert kwargs["extime"] == M.APPROVED_EXTIME_S
        assert kwargs["settle_first"] is False
        assert kwargs["require_all_reps"] is True
        assert kwargs["holdout_observation_admission"] is not None
        assert kwargs["workload"] in [cell["workload"] for cell in inputs.cells]
    assert all(item.cache_hit in {True, False} for item in observations)
    assert all(item.materialize_elapsed_s > 0 for item in observations)


def test_measure_gateway_uses_no_perf_only_when_preflight_is_unavailable(tmp_path):
    inputs, schedule, calls, _tenant, observations, perf_mode, _preflight_calls = (
        _run_one_round(tmp_path, perf_status="unavailable")
    )
    assert perf_mode.use_perf is False
    assert {kwargs["use_perf"] for *_prefix, kwargs in calls} == {False}
    result = M._result_document(
        inputs,
        _binary_receipts(tmp_path, inputs),
        attempt_id="no-perf",
        rounds=1,
        build_only=False,
        schedule=schedule,
        observations=observations,
        statistics_document=M.summarize_sessions(inputs, observations),
        n_analysis=None,
        run_wall_time_s=1.0,
        perf_mode=perf_mode,
        irreversible_pilot_holdout_approved=True,
        holdout_admission_identifier=_holdout_admission_identifier("no-perf"),
    )
    assert result["input_identity"]["use_perf"] is False
    assert result["input_identity"]["perf_preflight"]["status"] == "unavailable"


def test_probe_error_refuses_before_measurement(tmp_path):
    inputs = _inputs()
    binaries = _binary_receipts(tmp_path, inputs)
    schedule = M.build_pilot_schedule(inputs, master_seed="schedule-seed", rounds=1)
    measure_calls = []
    with pytest.raises(M.PilotError, match="perf preflight が判定不能"):
        M.run_sessions(
            inputs,
            binaries,
            schedule,
            measure_fn=lambda *_args, **_kwargs: measure_calls.append("called"),
            perf_preflight_fn=lambda **_kwargs: _perf_receipt("probe_error"),
            perf_candidates_fn=lambda _root: (),
            irreversible_pilot_holdout_approved=True,
            n_pilot_admissions={index: object() for index in range(len(schedule))},
            consume_n_pilot_attempt_ticket_fn=lambda *_args, **_kwargs: object(),
        )
    assert measure_calls == []


def test_missing_irreversible_approval_refuses_before_measure_fn(tmp_path):
    inputs = _inputs()
    binaries = _binary_receipts(tmp_path, inputs)
    schedule = M.build_pilot_schedule(inputs, master_seed="schedule-seed", rounds=1)
    measure_calls = []
    with pytest.raises(M.PilotError, match="confirm-irreversible-pilot-holdout"):
        M.run_sessions(
            inputs,
            binaries,
            schedule,
            measure_fn=lambda *_args, **_kwargs: measure_calls.append("called"),
            irreversible_pilot_holdout_approved=False,
        )
    assert measure_calls == []


def test_main_without_confirmation_refuses_before_loading_measurement_inputs(
    tmp_path, monkeypatch,
):
    calls = []
    monkeypatch.setattr(M, "load_protocol", lambda _path: _protocol())
    monkeypatch.setattr(
        M, "load_inputs", lambda *_args, **_kwargs: calls.append("load_inputs")
    )
    rc = M.main([
        "--protocol", str(tmp_path / "protocol.json"),
        "--output", str(tmp_path / "result.json"),
        "--attempt-id", "attempt-without-confirmation",
        "--observed-repo-head", "a" * 40,
        "--cache-root", str(tmp_path / "cache"),
        "--rounds", "1",
    ])
    assert rc == 2
    assert calls == []


def test_m6_measure_gateway_uses_nonstandard_freeze_scale_for_every_cell(tmp_path):
    _inputs_value, _schedule, calls, _tenant, _observations_value, _mode, _preflight = (
        _run_one_round(tmp_path)
    )
    assert len(calls) == 12
    assert {records for _binary, records, _threads, _clocks, _kwargs in calls} == {
        SENTINEL_RECORDS
    }
    assert {threads for _binary, _records, threads, _clocks, _kwargs in calls} == {
        SENTINEL_THREADS
    }


def test_m8_outer_trial_is_statistics_median_not_mean(tmp_path):
    _inputs_value, _schedule, _calls, _tenant, observations, _mode, _preflight = (
        _run_one_round(tmp_path)
    )
    assert {item.outer_median for item in observations} == {3.0}
    assert {item.throughput_binary64_hex for item in observations} == {
        (
            "3ff0000000000000", "4000000000000000", "4008000000000000",
            "4010000000000000", "4059000000000000",
        )
    }


def test_statistical_primitives_match_hand_calculated_literals():
    summary = M._summary([1.0, 2.0, 4.0])
    assert summary["mean"] == pytest.approx(7.0 / 3.0)
    assert summary["median"] == 2.0
    assert summary["sample_sd"] == pytest.approx((7.0 / 3.0) ** 0.5)
    assert summary["cv"] == pytest.approx(((7.0 / 3.0) ** 0.5) / (7.0 / 3.0))
    assert M._sample_covariance([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == 2.0
    assert M._sample_correlation(
        [1.0, 2.0, 3.0], [2.0, 4.0, 6.0]
    ) == (1.0, None)
    assert M._sample_correlation(
        [1.0, 1.0, 1.0], [2.0, 4.0, 6.0]
    ) == (None, "zero-variance")
    difference = M._difference_summary([-1.0, -2.0, -3.0])
    assert difference == {
        "mean": -2.0,
        "median": -2.0,
        "sample_sd": 1.0,
        "dispersion_ratio": 0.5,
    }
    assert M._binary64_hex(1.0) == "3ff0000000000000"


def test_wilson_upper_matches_known_one_sided_literals():
    assert M._wilson_upper(0, 1, 0.95) == pytest.approx(0.7301340512, abs=1e-10)
    assert M._wilson_upper(0, 20, 0.95) == pytest.approx(0.1191578374, abs=1e-10)
    assert M._wilson_upper(0, 100, 0.95) == pytest.approx(0.0263427208, abs=1e-10)
    assert M._wilson_upper(1, 1, 0.95) == 1.0
    assert M._wilson_upper(20, 20, 0.95) == 1.0


def test_m12_single_tenant_gate_runs_at_start_and_around_every_point(tmp_path):
    _inputs_value, _schedule, _calls, tenant_calls, observations, _mode, _preflight = (
        _run_one_round(tmp_path)
    )
    assert len(tenant_calls) == 1 + 2 * len(observations)


def test_m11_oracle_schedule_is_deterministic_seeded_complete_blocks():
    inputs = _inputs()
    first = M.build_pilot_schedule(inputs, master_seed="seed-a", rounds=2)
    second = M.build_pilot_schedule(inputs, master_seed="seed-a", rounds=2)
    changed = M.build_pilot_schedule(inputs, master_seed="seed-b", rounds=2)
    assert first == second
    assert first != changed
    expected = {cell["cell_id"] for cell in inputs.cells}
    for round_no in (1, 2):
        assert {row["cell_id"] for row in first if row["pilot_round"] == round_no} == expected


def test_global_schedule_is_built_once_and_sliced_into_three_local_allocations(
    monkeypatch,
):
    inputs = _inputs()
    original = M.s8b_oracle_manifest.build_schedule
    calls = []

    def recording_build_schedule(**kwargs):
        calls.append(dict(kwargs))
        return original(**kwargs)

    monkeypatch.setattr(M.s8b_oracle_manifest, "build_schedule", recording_build_schedule)
    schedule = M.build_pilot_schedule(
        inputs, master_seed=inputs.protocol.master_seed, rounds=33,
    )
    assert isinstance(schedule, M.GlobalPilotSchedule)
    assert len(calls) == 1
    assert calls[0]["n"] == 33
    assert calls[0]["block_sizes"] == {"pilot": 33}
    assert len(schedule.rows) == 396
    assert [row["global_schedule_index"] for row in schedule.rows] == list(range(396))
    for allocation_index, allocation in enumerate(schedule.allocation_slices):
        assert len(allocation) == 132
        assert [row["seq"] for row in allocation] == list(range(132))
        assert [row["global_schedule_index"] for row in allocation] == list(
            range(allocation_index * 132, allocation_index * 132 + 132)
        )
        assert {row["pilot_round"] for row in allocation} == set(range(1, 12))
        assert {row["global_pilot_round"] for row in allocation} == set(
            range(allocation_index * 11 + 1, allocation_index * 11 + 12)
        )


def test_r33_run_sessions_consumes_receipt_with_global_coordinates(tmp_path):
    inputs = _inputs()
    binaries = _binary_receipts(tmp_path, inputs)
    global_schedule = M.build_global_pilot_schedule(
        inputs, master_seed=inputs.protocol.master_seed,
    )
    schedule = global_schedule.allocation_slice(1)[:12]
    consume_calls = []
    ticks = iter(float(index) for index in range(100))

    def consume(receipt, **kwargs):
        consume_calls.append((receipt, kwargs))
        return object()

    def measure_fn(_binary, records, threads, clocks_per_us, **kwargs):
        kwargs["rep_returncodes"].extend([0] * M.APPROVED_REPS)
        return ScalePoint(
            records=records, threads=threads,
            throughputs=[1.0, 2.0, 3.0, 4.0, 5.0],
            abort_rate=0.0, run_cmd="discarded",
        )

    receipt = {"schedule_sha256": global_schedule.schedule_sha256}
    observations, _perf = M.run_sessions(
        inputs,
        binaries,
        schedule,
        measure_fn=measure_fn,
        single_tenant_fn=lambda: None,
        monotonic_fn=lambda: next(ticks),
        load1_fn=lambda: 0.0,
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(),
        perf_candidates_fn=lambda _root: (),
        repo_root=tmp_path,
        irreversible_pilot_holdout_approved=True,
        reservation_receipt=receipt,
        consume_n_pilot_attempt_ticket_fn=consume,
    )
    assert len(observations) == 12
    assert [item.global_schedule_index for item in observations] == list(range(132, 144))
    assert [item.global_pilot_round for item in observations] == [12] * 12
    assert len(consume_calls) == 12
    assert all(call[0] is receipt for call in consume_calls)
    assert [call[1]["global_schedule_index"] for call in consume_calls] == list(
        range(132, 144)
    )
    assert all(call[1]["schedule_sha256"] == global_schedule.schedule_sha256 for call in consume_calls)


def test_schedule_generator_is_the_oracle_manifest_gateway_not_floor_contract():
    path = ROOT / "orchestrator/campaign/s8b_oracle_n_pilot.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "build_schedule"
    }
    assert calls == {"s8b_oracle_manifest.build_schedule"}


def test_m9_statistics_pairs_stock_by_exact_round_and_rejects_shifted_fixture():
    inputs = _inputs()
    complete = M.summarize_sessions(inputs, _observations(inputs))
    holdout = sorted(complete["diagnostic_contrasts"])[0]
    configuration = next(iter(complete["diagnostic_contrasts"][holdout]))
    expected_delta = (
        CONFIGURATIONS.index(configuration) - CONFIGURATIONS.index("stock_common")
    )
    assert complete["diagnostic_contrasts"][holdout][configuration][
        "absolute_difference"
    ]["raw"] == [float(expected_delta), float(expected_delta)]
    observations = list(_observations(inputs))
    stock_index = next(
        index for index, item in enumerate(observations)
        if item.cell_id.endswith("::stock_common") and item.pilot_round == 2
    )
    observations[stock_index] = replace(observations[stock_index], pilot_round=3)
    with pytest.raises(M.PilotError, match="round"):
        M.summarize_sessions(inputs, observations)


def test_raw_candidate_distribution_and_diagnostic_contrasts_are_separate():
    inputs = _inputs()
    observations = _observations(inputs)
    result = M.summarize_sessions(inputs, observations)
    assert set(result) == {
        "candidate_set", "diagnostic_contrasts", "joint_covariance", "joint_correlation",
        "drift_diagnostics",
    }
    for holdout, candidates in result["candidate_set"].items():
        assert set(candidates) == set(CONFIGURATIONS)
        assert all(len(value["raw_outer_trials"]) == 2 for value in candidates.values())
        assert "stock_common" not in result["diagnostic_contrasts"][holdout]
        assert all(
            value["kind"] == "diagnostic-stock-contrast"
            for value in result["diagnostic_contrasts"][holdout].values()
        )


def test_session_records_preserve_all_drift_and_cache_confounders(tmp_path):
    _inputs_value, _schedule, _calls, _tenant, observations, _mode, _preflight = (
        _run_one_round(tmp_path)
    )
    assert [item.position for item in observations] == list(range(1, 13))
    for item in observations:
        record = item.as_record()
        assert record["monotonic_end_s"] >= record["monotonic_start_s"]
        assert record["duration_s"] >= 0.0
        assert record["load1_before"] == 1.25
        assert record["load1_after"] == 1.25
        assert record["cache_state"] in {"hit", "miss"}
        assert record["materialize_elapsed_s"] > 0.0


def _counterbalanced_observations(inputs: M.PilotInputs, schedule):
    rounds = max(int(row["pilot_round"]) for row in schedule)
    by_key = {
        (observation.pilot_round, observation.cell_id): observation
        for observation in _observations(inputs, rounds=rounds)
    }
    result = []
    for row in schedule:
        seq = int(row["seq"])
        observation = by_key[(int(row["pilot_round"]), str(row["cell_id"]))]
        result.append(replace(
            observation,
            seq=seq,
            position=(seq % len(inputs.cells)) + 1,
            monotonic_start_s=float(seq),
            monotonic_end_s=float(seq) + 0.5,
        ))
    return tuple(result)


def test_drift_thresholds_are_operational_and_invalidate_n_analysis():
    inputs = _inputs()
    observations = tuple(
        replace(observation, position=observation.pilot_round)
        for observation in _observations(inputs, rounds=11)
    )
    diagnostics = M.diagnose_drift(inputs, observations)
    assert diagnostics["valid_for_n_analysis"] is False
    assert all(
        cell["position_threshold_exceeded"] is True
        for cell in diagnostics["cells"].values()
    )
    assert all(
        reason.endswith("position-threshold-exceeded")
        for reason in diagnostics["invalidation_reasons"]
    )


def _selection_fixture():
    protocol = replace(
        _protocol(),
        candidate_ns=(1, 2),
        resampling_iterations=4,
        deltas=(0.01,),
        alphas=(0.7, 0.9),
        pilot_rounds=2,
    )
    inputs = replace(_inputs(), protocol=protocol)
    holdouts = sorted({str(cell["holdout_id"]) for cell in inputs.cells})
    best, challenger = CONFIGURATIONS[:2]
    observations = []
    for observation in _observations(inputs, rounds=2):
        holdout, configuration = observation.cell_id.split("::", 1)
        first_pattern = holdout == holdouts[0]
        if configuration == best:
            outer = 120.0 if (observation.pilot_round == 1) == first_pattern else 80.0
        elif configuration == challenger:
            outer = 80.0 if (observation.pilot_round == 1) == first_pattern else 110.0
        else:
            outer = 40.0 + CONFIGURATIONS.index(configuration)
        raw = (outer,) * M.APPROVED_REPS
        observations.append(replace(
            observation,
            throughputs=raw,
            throughput_binary64_hex=tuple(M._binary64_hex(value) for value in raw),
            outer_median=outer,
        ))
    return inputs, tuple(observations), holdouts


class _FixedBlockRng:
    def __init__(self, seed: str):
        _prefix, candidate, iteration = seed.rsplit("/", 2)
        self.candidate = int(candidate)
        self.iteration = int(iteration)
        self.calls = 0

    def choice(self, rounds):
        if self.candidate == 1:
            chosen = rounds[self.iteration % 2]
        else:
            patterns = ((0, 1), (1, 1), (0, 0), (0, 1))
            chosen = rounds[patterns[self.iteration][self.calls]]
        self.calls += 1
        return chosen


def test_indifference_zone_counts_rates_ucls_and_selected_n_are_exact():
    inputs, observations, holdouts = _selection_fixture()
    result = M.derive_n_table(
        inputs, observations, use_perf=True, rng_factory=_FixedBlockRng,
    )
    assert result["conditioning"] == (
        "all-rows-eligible/three-allocations/exact-pin-and-binaries/perf-on"
    )
    for holdout in holdouts:
        first = result["candidate_results"]["1"]["per_holdout"]["0.01"][holdout]
        second = result["candidate_results"]["2"]["per_holdout"]["0.01"][holdout]
        assert (first["errors"], first["rate"]) == (2, 0.5)
        assert first["ucl"] == pytest.approx(0.8176, abs=1e-4)
        assert (second["errors"], second["rate"]) == (1, 0.25)
        assert second["ucl"] == pytest.approx(0.6439, abs=1e-4)
    family_first = result["candidate_results"]["1"]["familywise"]["0.01"]
    family_second = result["candidate_results"]["2"]["familywise"]["0.01"]
    assert (family_first["errors"], family_first["rate"], family_first["ucl"]) == (
        4, 1.0, 1.0,
    )
    assert (family_second["errors"], family_second["rate"]) == (2, 0.5)
    assert family_second["ucl"] == pytest.approx(0.8176, abs=1e-4)
    by_alpha = {row["alpha"]: row for row in result["n_table"]}
    assert by_alpha[0.7]["per_holdout_n"] == {holdout: 2 for holdout in holdouts}
    assert by_alpha[0.7]["familywise_n"] is None
    assert by_alpha[0.9]["per_holdout_n"] == {holdout: 1 for holdout in holdouts}
    assert by_alpha[0.9]["familywise_n"] == 2
    assert by_alpha[0.7]["per_holdout_pass"][holdouts[0]] == [
        {"candidate_n": 1, "passed": False},
        {"candidate_n": 2, "passed": True},
    ]


def test_tie_iterations_are_reported_but_not_counted_as_errors():
    inputs, observations, holdouts = _selection_fixture()
    best, challenger = CONFIGURATIONS[:2]
    tied = []
    for observation in observations:
        _holdout, configuration = observation.cell_id.split("::", 1)
        if observation.pilot_round == 1 and configuration in {best, challenger}:
            outer = 100.0
        elif configuration == best:
            outer = 120.0
        elif configuration == challenger:
            outer = 80.0
        else:
            outer = observation.outer_median
        raw = (outer,) * M.APPROVED_REPS
        tied.append(replace(
            observation,
            throughputs=raw,
            throughput_binary64_hex=tuple(M._binary64_hex(value) for value in raw),
            outer_median=outer,
        ))
    result = M.derive_n_table(
        inputs, tied, use_perf=True, rng_factory=_FixedBlockRng,
    )
    for holdout in holdouts:
        candidate = result["candidate_results"]["1"]["per_holdout"]["0.01"][holdout]
        assert candidate["errors"] == 0
        assert candidate["tie_rate"] == 0.5
    assert result["candidate_results"]["1"]["familywise"]["0.01"]["errors"] == 0


def test_nonmonotonic_candidate_series_is_flagged_and_uses_passing_suffix():
    no_suffix = M._conservative_candidate_selection((1, 2, 3), (False, True, False))
    assert no_suffix == {
        "passes": [
            {"candidate_n": 1, "passed": False},
            {"candidate_n": 2, "passed": True},
            {"candidate_n": 3, "passed": False},
        ],
        "nonmonotonic": True,
        "selected_n": None,
        "null_reason": "nonmonotonic-no-passing-suffix",
    }
    passing_suffix = M._conservative_candidate_selection(
        (1, 2, 3, 4), (False, True, False, True)
    )
    assert passing_suffix["nonmonotonic"] is True
    assert passing_suffix["selected_n"] == 4
    assert passing_suffix["null_reason"] is None


def test_indifference_zone_n_table_uses_block_resampling_and_reports_ucl():
    inputs = replace(_inputs(), protocol=replace(_protocol(), pilot_rounds=3))
    result = M.derive_n_table(
        inputs, _observations(inputs, rounds=3), use_perf=False,
    )
    assert result["conditioning"] == (
        "all-rows-eligible/three-allocations/exact-pin-and-binaries/perf-off"
    )
    assert result["selection_error"] == "indifference-zone-relative"
    assert result["tie_rule"] == "not-an-error"
    assert result["resampling_unit"] == "complete-round-vector"
    assert result["allocation_variation_in_ucl"] is False
    assert len(result["n_table"]) == 8
    assert set(result["candidate_results"]) == {"1", "2", "3"}


def test_m1_contaminated_bytes_create_neither_destination_nor_parent(tmp_path):
    destination = tmp_path / "new-parent" / "result.json"
    workload = dict(next(iter(s8b_holdout_freeze.HOLDOUTS.values()))["ycsb"])
    payload = json.dumps({"workload": workload}).encode("utf-8")
    with pytest.raises(M.PilotError, match="contamination"):
        M.write_guarded_result(destination, payload)
    assert not destination.exists()
    assert not destination.parent.exists()


def test_m2_safe_writer_is_create_only(tmp_path):
    destination = tmp_path / "safe" / "result.json"
    expected = M.canonical_result_bytes({"safe": True})
    digest = M.write_guarded_result(destination, {"safe": True})
    assert destination.read_bytes() == expected
    assert digest == hashlib.sha256(expected).hexdigest()
    with pytest.raises(M.PilotError, match="create-only") as caught:
        M.write_guarded_result(destination, {"safe": False})
    assert isinstance(caught.value.__cause__, FileExistsError)
    assert destination.read_bytes() == expected


@pytest.mark.parametrize("failure", ["write", "file-fsync", "directory-fsync"])
def test_writer_removes_destination_and_refsyncs_directory_after_failure(tmp_path, failure):
    destination = tmp_path / failure / "result.json"
    fsync_calls = []

    def write_fn(descriptor, payload):
        if failure == "write":
            raise OSError("injected write failure")
        return M.os.write(descriptor, payload)

    def fsync_fn(descriptor):
        fsync_calls.append(descriptor)
        fail_at = 1 if failure == "file-fsync" else 2
        if failure.endswith("fsync") and len(fsync_calls) == fail_at:
            raise OSError(f"injected {failure} failure")
        M.os.fsync(descriptor)

    with pytest.raises(M.PilotError, match="guarded create-only write"):
        M.write_guarded_result(
            destination,
            {"safe": True},
            write_fn=write_fn,
            fsync_fn=fsync_fn,
        )
    assert not destination.exists()
    assert len(fsync_calls) >= 1


def test_writer_uses_nofollow_parent_dirfd_and_exclusive_destination_open(tmp_path):
    destination = tmp_path / "bound-parent" / "result.json"
    calls = []

    def open_fn(path, flags, *args, **kwargs):
        calls.append((path, flags, args, kwargs))
        return M.os.open(path, flags, *args, **kwargs)

    M.write_guarded_result(destination, {"safe": True}, open_fn=open_fn)
    assert len(calls) == 2
    parent_call, destination_call = calls
    assert parent_call[1] & M.os.O_NOFOLLOW
    assert destination_call[0] == destination.name
    assert destination_call[1] & M.os.O_NOFOLLOW
    assert destination_call[1] & M.os.O_EXCL
    assert destination_call[3]["dir_fd"] is not None


def test_writer_positive_cell_id_is_not_over_rejected(tmp_path):
    destination = tmp_path / "result.json"
    payload = {"cell_id": "rr20::stock_common", "throughput": 123.0}
    M.write_guarded_result(destination, payload)
    assert json.loads(destination.read_text(encoding="utf-8")) == payload


def test_writer_rejects_freeze_and_symlink_destinations(tmp_path):
    with pytest.raises(M.PilotError, match="s8b-freeze"):
        M.write_guarded_result(ROOT / M.FREEZE_REL.parent / "pilot.json", {"safe": True})
    actual = tmp_path / "actual"
    actual.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    with pytest.raises(M.PilotError, match="symlink"):
        M.write_guarded_result(alias / "pilot.json", {"safe": True})
    assert not (actual / "pilot.json").exists()


def test_m10_result_eligibility_is_exactly_all_false(tmp_path):
    inputs = _inputs(held=({"check": "held"},))
    binaries = _binary_receipts(tmp_path, inputs)
    result = M._result_document(
        inputs,
        binaries,
        attempt_id="attempt-1",
        rounds=None,
        build_only=True,
        schedule=(),
        observations=(),
        statistics_document=None,
        n_analysis=None,
        run_wall_time_s=None,
        perf_mode=_perf_mode(),
    )
    assert result["eligibility"] == {
        "certified": False,
        "floor_input": False,
        "oracle_input": False,
        "n_decision": False,
    }
    assert result["input_identity"]["freeze_verification_status"] == "held"
    assert result["input_identity"]["freeze_verification_held_markers"] == [{"check": "held"}]
    assert result["input_identity"]["observed_repo_head"] == "a" * 40
    assert result["input_identity"]["use_perf"] is True
    rendered = M.canonical_result_bytes(result)
    assert b"run_cmd" in rendered
    assert b"discarded" not in rendered


def test_complete_fake_scalepoint_result_discards_run_cmd_and_workload_object(tmp_path):
    inputs, schedule, _calls, _tenant, observations, perf_mode, _preflight = (
        _run_one_round(tmp_path)
    )
    binaries = _binary_receipts(tmp_path, inputs)
    statistics_document = M.summarize_sessions(inputs, observations)
    result = M._result_document(
        inputs,
        binaries,
        attempt_id="attempt-complete",
        rounds=1,
        build_only=False,
        schedule=schedule,
        observations=observations,
        statistics_document=statistics_document,
        n_analysis=None,
        run_wall_time_s=12.5,
        perf_mode=perf_mode,
        n_analysis_null_reason="per-allocation-result-does-not-derive-n",
        irreversible_pilot_holdout_approved=True,
        holdout_admission_identifier=(
            _holdout_admission_identifier("attempt-complete")
        ),
    )
    destination = tmp_path / "published" / "result.json"
    M.write_guarded_result(destination, result)
    payload = destination.read_bytes()
    assert b"discarded" not in payload
    M.assert_holdout_safe_bytes(destination.name, payload)
    loaded = json.loads(payload)
    assert loaded["allocation"]["one_round_wall_time_s"] == 12.5
    assert loaded["input_identity"]["irreversible_pilot_holdout_approved"] is True
    assert loaded["allocation"]["holdout_admission"] == (
        _holdout_admission_identifier("attempt-complete")
    )
    assert loaded["n_analysis"] is None
    assert loaded["n_analysis_null_reason"] == "per-allocation-result-does-not-derive-n"


def test_per_allocation_result_cannot_publish_n_analysis(tmp_path):
    inputs = _inputs()
    with pytest.raises(M.PilotError, match="aggregate"):
        M._result_document(
            inputs,
            _binary_receipts(tmp_path, inputs),
            attempt_id="allocation-only",
            rounds=1,
            build_only=False,
            schedule=(),
            observations=(),
            statistics_document=None,
            n_analysis={"forbidden": True},
            run_wall_time_s=1.0,
            perf_mode=_perf_mode(),
        )


def _allocation_result_files(tmp_path: Path):
    inputs = _inputs()
    binaries = _binary_receipts(tmp_path, inputs)
    schedule = M.build_pilot_schedule(inputs, master_seed=inputs.protocol.master_seed, rounds=11)
    base = _counterbalanced_observations(inputs, schedule)
    paths = []
    for allocation_index in range(3):
        shifted = []
        for observation in base:
            outer = observation.outer_median + allocation_index
            raw = (outer,) * M.APPROVED_REPS
            shifted.append(replace(
                observation,
                throughputs=raw,
                throughput_binary64_hex=tuple(M._binary64_hex(value) for value in raw),
                outer_median=outer,
            ))
        result = M._result_document(
            inputs,
            binaries,
            attempt_id=f"allocation-{allocation_index + 1}",
            rounds=11,
            build_only=False,
            schedule=schedule,
            observations=shifted,
            statistics_document=M.summarize_sessions(inputs, shifted),
            n_analysis=None,
            run_wall_time_s=100.0,
            perf_mode=_perf_mode(),
            n_analysis_null_reason="per-allocation-result-does-not-derive-n",
            irreversible_pilot_holdout_approved=True,
            holdout_admission_identifier=_holdout_admission_identifier(
                f"allocation-{allocation_index + 1}"
            ),
        )
        path = tmp_path / f"allocation-{allocation_index + 1}.json"
        path.write_bytes(M.canonical_result_bytes(result))
        paths.append(path)
    return inputs.protocol, paths


def test_three_allocation_aggregate_derives_n_once_and_reports_shift(tmp_path):
    protocol, paths = _allocation_result_files(tmp_path)
    result = M.aggregate_results(protocol, paths)
    assert result["schema_version"] == M.AGGREGATE_SCHEMA
    assert result["n_analysis"] is not None
    assert result["n_analysis_null_reason"] is None
    assert result["statistics"]["drift_diagnostics"]["valid_for_n_analysis"] is True
    assert result["allocation_shift"] == {
        "interpretation": "presence-and-direction-only;not-a-variance-component-estimate",
        "allocation_count": 3,
        "cells": result["allocation_shift"]["cells"],
    }
    for cell in result["allocation_shift"]["cells"].values():
        assert list(cell["allocation_medians"]) == [
            "allocation-1", "allocation-2", "allocation-3",
        ]
        assert cell["max_minus_min"] == 2.0
        assert [item["direction"] for item in cell["pairwise_differences"]] == [
            "higher", "higher", "higher",
        ]


def test_aggregate_treats_repo_heads_as_observations_not_identity_pins(tmp_path):
    protocol, paths = _allocation_result_files(tmp_path)
    observed_heads = []
    for index, path in enumerate(paths, start=1):
        document = json.loads(path.read_text(encoding="utf-8"))
        observed_head = f"{index:040x}"
        document["input_identity"]["observed_repo_head"] = observed_head
        path.write_bytes(M.canonical_result_bytes(document))
        observed_heads.append(observed_head)
    result = M.aggregate_results(protocol, paths)
    assert result["input_identity"]["observed_repo_heads"] == observed_heads


def test_aggregate_rejects_protocol_or_schedule_seed_mismatch(tmp_path):
    protocol, paths = _allocation_result_files(tmp_path)
    document = json.loads(paths[1].read_text(encoding="utf-8"))
    document["design"]["master_seed"] = "different-seed"
    paths[1].write_bytes(M.canonical_result_bytes(document))
    with pytest.raises(M.PilotError, match="schedule seed"):
        M.aggregate_results(protocol, paths)


def test_aggregate_writes_guarded_output_and_drift_failure_leaves_n_null(tmp_path):
    protocol, paths = _allocation_result_files(tmp_path)
    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        for session in document["sessions"]:
            outer = 100.0 + session["position"]
            session["throughputs"] = [outer] * M.APPROVED_REPS
            session["throughput_binary64_hex"] = [M._binary64_hex(outer)] * M.APPROVED_REPS
            session["outer_median"] = outer
        path.write_bytes(M.canonical_result_bytes(document))
    aggregate = M.aggregate_results(protocol, paths)
    assert aggregate["n_analysis"] is None
    assert aggregate["n_analysis_null_reason"].startswith("drift-diagnostics-invalid:")
    protocol_path = _write_protocol(tmp_path / "protocol.json", _protocol_document())
    destination = tmp_path / "aggregate" / "result.json"
    assert M.main([
        "--protocol", str(protocol_path),
        "--output", str(destination),
        "--aggregate", *(str(path) for path in paths),
    ]) == 0
    assert json.loads(destination.read_text(encoding="utf-8"))["n_analysis"] is None


def test_submit_wrapper_binds_exact_external_stdout_stderr_argv(tmp_path):
    output_root = tmp_path / "output"
    cache_root = tmp_path / "cache"
    output_root.mkdir()
    cache_root.mkdir()
    protocol = tmp_path / "protocol.json"
    protocol.write_text("{}\n", encoding="utf-8")
    job = tmp_path / "job.sh"
    job.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
    job.chmod(0o755)
    attempt = "attempt-1"
    completed = subprocess.run([
        "bash", str(ROOT / "tools/pegasus/submit_oracle_n_pilot.sh"),
        "--dry-run",
        "--repo-root", str(ROOT),
        "--job-script", str(job),
        "--protocol", str(protocol),
        "--output-root", str(output_root),
        "--cache-root", str(cache_root),
        "--attempt", attempt,
        "--rounds", "1",
    ], capture_output=True, text=True, encoding="utf-8")
    assert completed.returncode == 0, completed.stderr
    line = next(line for line in completed.stdout.splitlines() if line.startswith("qsub command:"))
    argv = shlex.split(line.removeprefix("qsub command:"))
    attempt_dir = output_root / attempt
    expected_export = (
        f"IZANAGI_PILOT_PROTOCOL={protocol.resolve()},"
        f"IZANAGI_PILOT_OUTPUT_ROOT={output_root.resolve()},"
        f"IZANAGI_PILOT_CACHE_ROOT={cache_root.resolve()},"
        f"IZANAGI_PILOT_ATTEMPT={attempt},IZANAGI_PILOT_BUILD_ONLY=0,"
        "IZANAGI_PILOT_ROUNDS=1"
    )
    assert argv == [
        "qsub", "-o", str(attempt_dir / "scheduler.stdout"),
        "-e", str(attempt_dir / "scheduler.stderr"),
        "-v", expected_export, str(job.resolve()),
    ]


@pytest.mark.parametrize("override", ["repo", "job"])
def test_submit_wrapper_rejects_production_path_overrides_before_qsub(tmp_path, override):
    output_root = tmp_path / "output"
    cache_root = tmp_path / "cache"
    output_root.mkdir()
    cache_root.mkdir()
    protocol = tmp_path / "protocol.json"
    protocol.write_text("{}\n", encoding="utf-8")
    command = [
        "bash", str(ROOT / "tools/pegasus/submit_oracle_n_pilot.sh"),
        "--protocol", str(protocol),
        "--output-root", str(output_root),
        "--cache-root", str(cache_root),
        "--attempt", f"production-{override}",
    ]
    if override == "repo":
        command.extend(["--repo-root", str(ROOT)])
    else:
        command.extend(["--job-script", str(ROOT / "tools/pegasus/oracle_n_pilot.sh")])
    completed = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8",
    )
    assert completed.returncode == 2
    assert "overrides require --dry-run" in completed.stderr
    assert not (output_root / f"production-{override}").exists()


def test_submit_wrapper_production_job_requires_tracked_head_blob_contract():
    source = (ROOT / "tools/pegasus/submit_oracle_n_pilot.sh").read_text(encoding="utf-8")
    assert "ls-files --error-unmatch" in source
    assert "cat-file blob" in source
    assert "working-tree job script differs from HEAD blob" in source


def test_job_script_passes_observed_head_and_preserves_clean_tree_gates():
    source = (ROOT / M.JOB_SCRIPT_REL).read_text(encoding="utf-8")
    assert 'diff-index --quiet HEAD -- || fail "repo has tracked changes"' in source
    assert "ls-files --others --exclude-standard" in source
    assert 'REPO_HEAD=$(git -C "$REPO_ROOT" rev-parse --verify HEAD)' in source
    assert '--observed-repo-head "$REPO_HEAD"' in source
    assert (
        "IZANAGI_PILOT_CONFIRM_IRREVERSIBLE_HOLDOUT="
        "${IZANAGI_PILOT_CONFIRM_IRREVERSIBLE_HOLDOUT:-0}"
    ) in source
    assert (
        '[[ "$IZANAGI_PILOT_CONFIRM_IRREVERSIBLE_HOLDOUT" =~ ^[01]$ ]]'
        in source
    )
    assert 'driver+=(--confirm-irreversible-pilot-holdout)' in source


def test_new_python_and_shell_sources_are_nfc_and_holdout_literal_safe():
    paths = [
        ROOT / "orchestrator/campaign/s8b_oracle_n_pilot.py",
        ROOT / "orchestrator/tests/test_s8b_oracle_n_pilot.py",
        ROOT / "tools/pegasus/oracle_n_pilot.sh",
        ROOT / "tools/pegasus/submit_oracle_n_pilot.sh",
    ]
    sources = {path.relative_to(ROOT).as_posix(): path.read_text(encoding="utf-8") for path in paths}
    hits = s8b_holdout_freeze.holdout_conjunction_hits(sources)
    assert all(not value for value in hits.values())
    assert all(
        not any("\u0300" <= character <= "\u036f" for character in source)
        for source in sources.values()
    )


def test_shell_scripts_parse_without_execution():
    completed = subprocess.run([
        "bash", "-n",
        str(ROOT / "tools/pegasus/oracle_n_pilot.sh"),
        str(ROOT / "tools/pegasus/submit_oracle_n_pilot.sh"),
    ], capture_output=True, text=True, encoding="utf-8")
    assert completed.returncode == 0, completed.stderr
