# -*- coding: utf-8 -*-
"""偵察 sweep 専用 screening driver の計測なし単体テスト。"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import (condition_meaning_gate, env_contract, ident,  # noqa: E402
                                   screening_driver, wal)
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.layout import campaign_layout                     # noqa: E402
from orchestrator.campaign.model import (STAGE_BENCH_DONE, STAGE_BUILD_DONE,  # noqa: E402
                            STAGE_BUILD_START,
                            CampaignConfig, Genome)
from orchestrator.campaign.pipeline import EvalResult, PerfConfig             # noqa: E402
from orchestrator.campaign.source_digest import (  # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SOURCE_EVIDENCE_SCHEMA,
    SourceEvidence,
)
from orchestrator.tests import commit_receipt_support as receipt_support  # noqa: E402
from campaign_lock_test_support import build_v2_lock              # noqa: E402


WORKLOAD = {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}
_BUILD_CONTEXT = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
_CONTRACT = env_contract.GENERATIONS["linux-baremetal"][0].contract
_CONDITION_FIXTURES = (
    Path(__file__).parent / "fixtures" / "condition_meaning_gate"
)


def _any_cxx() -> str:
    for candidate in ("g++-13", "g++-12", "g++"):
        if shutil.which(candidate):
            return candidate
    pytest.skip("no supported C++ compiler is installed")


def _any_cmake() -> str:
    candidate = shutil.which("cmake")
    if candidate is None:
        pytest.skip("cmake is not installed")
    return candidate


def _canonical_perf_receipt(status: str) -> dict:
    available = status == "available"
    return {
        "schema": screening_driver._perf_preflight.SCHEMA,
        "status": status,
        "available": available,
        "probe_argv": list(screening_driver._perf_preflight._BASE_PROBE_ARGV),
        "rc": 0 if available else None,
        "parsed_events": (
            list(screening_driver._perf_preflight.PERF_EVENTS) if available else []
        ),
        "reason": (
            "available" if available else
            "probe-os-error" if status == "probe_error" else
            "perf-not-found"
        ),
        "stderr_sha256": "0" * 64,
        "candidates": [],
    }


@pytest.fixture(autouse=True)
def _pin_screening_perf_available(monkeypatch):
    """既存の perf-present fixture を実行 host の availability から隔離する。"""
    monkeypatch.setattr(
        screening_driver._perf_preflight,
        "probe_perf_availability",
        lambda: _canonical_perf_receipt("available"),
    )


@pytest.fixture
def _certified_writer_authority():
    authorization = env_contract.authorize("linux-baremetal")
    return authorization, authorization.contract


def _source_evidence(genome: Genome, *, root: str = "/fixture/ccbench"):
    return SourceEvidence(
        schema_version=SOURCE_EVIDENCE_SCHEMA,
        source_root=os.path.realpath(root),
        ccbench_commit="deadbeef",
        genome_sha256=hashlib.sha256(
            genome.canonical().encode("utf-8")
        ).hexdigest(),
        src_token="stock",
        source_bytes_sha256="3" * 64,
        tracked_clean=True,
        tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
        tracked_paths=(),
    )


def _toolchain_manifest(*, cxx: str = "test-cxx", cmake: str = "test-cmake"):
    requested = {"cc": cxx, "cxx": cxx, "cmake": cmake}
    return {
        role: {
            "requested": name,
            "realpath": os.path.realpath(shutil.which(name) or name),
            "version_first_line": f"{role} version A",
            "version": f"{role} version A",
        }
        for role, name in requested.items()
    }


def _log_completed_attempt(layout, variant: str, genome: Genome) -> None:
    evidence = _source_evidence(genome)
    generator = attest_generator_output(
        _BUILD_CONTEXT, evidence, generator_input_sha256="1" * 64,
    )
    admission = derive_build_admission(
        _BUILD_CONTEXT, evidence, generator_receipt=generator,
    )
    attempt_id = f"fixture-{variant}"
    common = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": admission.receipt_sha256,
    }
    wal.log(layout, variant, STAGE_BUILD_START, _CONTRACT.env_tag, {
        **common,
        "genome": genome.canonical(),
        "src_token": evidence.src_token,
        "build_admission": admission.as_wal_receipt(),
    })
    wal.log(layout, variant, STAGE_BUILD_DONE, _CONTRACT.env_tag, common)
    receipt_support.log_receipted_commit(
        layout, variant, _CONTRACT.env_tag, {
        **common, "contract_sha256": _CONTRACT.contract_sha256,
        }, operation_identity=attempt_id,
    )


def _cfg():
    cfg = ident.bind_admission_policy(CampaignConfig(
        spec_slug="screen-driver", search_tag="sweep", spec_content="fixture",
        ccbench_commit="deadbeef", search_config={"workload": "balanced"},
        trial="fixture"), _BUILD_CONTEXT.policy)
    return ident.bind_environment_contract(cfg, _CONTRACT)


@pytest.mark.parametrize("with_stock", [False, True])
@pytest.mark.parametrize("raw,physical", [(5, 5), (3000, 1000), (1000, 1000)])
def test_evaluate_candidate_declared_backoff_reaches_real_gate(
        tmp_path, monkeypatch, _certified_writer_authority,
        with_stock, raw, physical):
    """Real supply/meaning/admission; the performance sink is simulated."""
    from contextlib import contextmanager
    from orchestrator.campaign import backoff_sweep

    authorization, contract = _certified_writer_authority
    source = _CONDITION_FIXTURES / "supplied"
    flags = {"BACKOFF_FIXED": raw}
    if with_stock:
        flags["BACKOFF_NOINLINE"] = 0
    genome = Genome("silo", flags)
    declaration = backoff_sweep._backoff_fixed_declarations(
        (raw,), {raw: physical},
    )[raw]
    checkout_calls = []

    @contextmanager
    def checkout(commit, *, base_dir):
        checkout_calls.append((commit, base_dir))
        yield str(source / "stock")

    monkeypatch.setattr(screening_driver.patchharness, "checkout", checkout)
    monkeypatch.setattr(
        screening_driver.buildcache, "compilers_for_current_site",
        lambda: (_any_cxx(), _any_cxx()),
    )
    monkeypatch.setattr(
        screening_driver.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: _source_evidence(genome, root=str(source)),
    )
    runs = []
    real_gate = screening_driver._require_condition_gate_before_evaluation

    def observe_gate(*args, **kwargs):
        run = real_gate(*args, **kwargs)
        runs.append(run)
        return run

    monkeypatch.setattr(
        screening_driver, "_require_condition_gate_before_evaluation", observe_gate,
    )
    evaluated = []

    def performance_sink(candidate, *args, **kwargs):
        assert "backoff_fixed_declaration" not in kwargs
        evaluated.append(candidate)
        return EvalResult(genome=candidate, variant="candidate",
                          certified=True, aborted=False)

    monkeypatch.setattr(screening_driver, "evaluate", performance_sink)
    cfg = _cfg()
    layout = campaign_layout(str(ident.campaign_id(cfg)), str(tmp_path)).ensure()

    def call():
        return screening_driver.evaluate_candidate(
            cfg, layout, genome, PerfConfig(records=1, threads=1),
            contract.env_tag, contract.clocks_per_us,
            numactl=contract.numactl, authorization_contract=authorization,
            build_context=_BUILD_CONTEXT, screening=None,
            backoff_fixed_declaration=declaration, log=lambda _message: None,
        )

    if raw == 1000:
        with pytest.raises(condition_meaning_gate.ConditionMeaningGateError,
                           match="decoded-meaning-mismatch"):
            call()
        assert evaluated == []
    else:
        assert call() is not None
        assert evaluated == [genome]
        assert len(runs) == 1 and runs[0].admission.admitted
        assert [(r.macro, r.terminal_status) for r in runs[0].meaning_records
                if r.macro == "BACKOFF_FIXED"] == [("BACKOFF_FIXED", "green")]
        assert all(r.terminal_status == "unestablished"
                   for r in runs[0].meaning_records if r.macro != "BACKOFF_FIXED")
    assert len(checkout_calls) == int(with_stock)


def test_screening_undeclared_randomized_backoff_remains_unestablished():
    from orchestrator.campaign import b10_backoff_shape_sweep

    raw = b10_backoff_shape_sweep.encode("symmetric-modulo", 5)
    run = screening_driver._run_condition_gate_for_genome(
        str(_CONDITION_FIXTURES / "supplied"),
        Genome("silo", {"BACKOFF_FIXED": raw}),
        stock_root=None, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    assert run.admission.admitted
    assert [r.terminal_status for r in run.supply_records] == ["green"]
    assert [r.terminal_status for r in run.meaning_records] == ["unestablished"]


def _write_floor(root, *, floor=0.03, workload=WORKLOAD, protocol="silo",
                 filename="between_run_noise_fixture.json",
                 schema_version="between-run-noise-floor/v1"):
    """Write the versioned fixture by default; pass None for a legacy JSON."""
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, filename)
    document = {
        "workload": workload,
        "genome": f"{protocol}|BACK_OFF=0",
        "between_run": {"cv": floor},
    }
    if schema_version is not None:
        document["schema_version"] = schema_version
    with open(path, "w", encoding="utf-8") as f:
        json.dump(document, f)
    return path


def test_screening_condition_gate_accepts_real_runtime_genome_value(monkeypatch):
    genome = Genome("silo", {"BACKOFF_FIXED": 5})
    monkeypatch.setattr(
        screening_driver.buildcache,
        "prepare_masstree_fetchcontent",
        lambda **_kwargs: pytest.fail("manifest None path must not prepare"),
    )
    run = screening_driver._run_condition_gate_for_genome(
        str(_CONDITION_FIXTURES / "supplied"), genome,
        stock_root=None, cxx=_any_cxx(), cmake=_any_cmake(),
    )

    assert run is not None and run.admission.admitted
    assert run.admission.use_class == "raw"
    assert [(record.macro, record.terminal_status)
            for record in run.supply_records] == [("BACKOFF_FIXED", "green")]
    assert [(record.macro, record.terminal_status)
            for record in run.meaning_records] == [
                ("BACKOFF_FIXED", "unestablished")]
    requests = screening_driver._condition_requests_for_genome(genome)
    assert [(request.macro, request.requested_value)
            for request in requests] == [("BACKOFF_FIXED", 5)]


def test_screening_condition_gate_rejects_real_ignored_runtime_define(monkeypatch):
    genome = Genome("silo", {"BACKOFF_FIXED": 5})
    prepare_calls = []
    monkeypatch.setattr(
        screening_driver.buildcache,
        "prepare_masstree_fetchcontent",
        lambda **kwargs: prepare_calls.append(kwargs),
    )

    with pytest.raises(
            condition_meaning_gate.ConditionMeaningGateError,
            match="preprocess-bytes-identical",
    ):
        screening_driver._run_condition_gate_for_genome(
            str(_CONDITION_FIXTURES / "effectuation-ignored"), genome,
            stock_root=None, cxx=_any_cxx(), cmake=_any_cmake(),
            expected_toolchain_manifest={"route": "backoff-screening"},
        )
    assert len(prepare_calls) == 1


def test_screening_condition_gate_prepares_once_with_exact_fetchcontent_arguments(
        monkeypatch):
    source_root = (_CONDITION_FIXTURES / "supplied").resolve()
    genome = Genome("silo", {"BACKOFF_FIXED": 5})
    expected = {"route": "backoff-screening"}
    prepare_calls = []
    capture_calls = []
    real_capture = condition_meaning_gate.capture_define_inputs

    def prepare(**kwargs):
        prepare_calls.append(kwargs)
        assert Path(kwargs["fetchcontent_base_dir"]).is_dir()

    def capture(*args, **kwargs):
        capture_calls.append((args, kwargs))
        base_arg = kwargs["configure_args"][-1]
        base = Path(base_arg.removeprefix("-DFETCHCONTENT_BASE_DIR="))
        assert base.is_dir()
        return real_capture(*args, **kwargs)

    monkeypatch.setattr(
        screening_driver.buildcache, "prepare_masstree_fetchcontent", prepare,
    )
    monkeypatch.setattr(
        screening_driver.condition_meaning_gate, "capture_define_inputs", capture,
    )

    run = screening_driver._run_condition_gate_for_genome(
        str(source_root), genome,
        stock_root=None, cxx=_any_cxx(), cmake=_any_cmake(),
        expected_toolchain_manifest=expected,
    )

    assert run is not None and run.admission.admitted
    assert len(prepare_calls) == 1
    prepare_call = prepare_calls[0]
    base = prepare_call["fetchcontent_base_dir"]
    assert set(prepare_call) == {
        "ccbench_dir", "fetchcontent_base_dir", "expected_toolchain_manifest",
        "configure_timeout_s", "target_timeout_s", "site",
    }
    assert prepare_call["ccbench_dir"] == str(source_root)
    assert prepare_call["expected_toolchain_manifest"] is expected
    assert prepare_call["configure_timeout_s"] == 900
    assert prepare_call["target_timeout_s"] == 900
    assert prepare_call["site"] is None
    assert base == str(Path(base).resolve())
    assert capture_calls[0][0] == (str(source_root),)
    configure_args = capture_calls[0][1]["configure_args"]
    base_arg = f"-DFETCHCONTENT_BASE_DIR={base}"
    assert configure_args == (
        *screening_driver._condition_gate_base_configure_args(genome),
        base_arg,
    )
    assert sum(
        argument.startswith("-DFETCHCONTENT_BASE_DIR=")
        for argument in configure_args
    ) == 1
    assert not Path(base).exists()


def test_screening_condition_gate_supplies_prepared_base_to_real_supply_arm(
        monkeypatch):
    source_root = (_CONDITION_FIXTURES / "prepared-base-required").resolve()
    prepared_headers = []

    def prepare(**kwargs):
        header = (
            Path(kwargs["fetchcontent_base_dir"])
            / "izanagi-screening-dependency-src"
            / "include"
            / "izanagi_prepared_dependency.hh"
        )
        header.parent.mkdir(parents=True)
        header.write_text(
            "#define IZANAGI_PREPARED_DEPENDENCY 1\n", encoding="utf-8",
        )
        prepared_headers.append(header)

    monkeypatch.setattr(
        screening_driver.buildcache, "prepare_masstree_fetchcontent", prepare,
    )

    run = screening_driver._run_condition_gate_for_genome(
        str(source_root), Genome("silo", {"BACKOFF_FIXED": 5}),
        stock_root=None, cxx=_any_cxx(), cmake=_any_cmake(),
        expected_toolchain_manifest={"route": "backoff-screening"},
    )

    assert run is not None and run.admission.admitted
    assert len(prepared_headers) == 1
    supply = run.supply_records[0]
    assert (supply.terminal_status, supply.reason_code) == (
        "green", "requested-default-preprocess-different",
    )
    base_arg = f"-DFETCHCONTENT_BASE_DIR={prepared_headers[0].parents[2]}"
    for label in ("requested", "control"):
        configure_argv = supply.evidence[f"{label}_configure_argv"]
        assert configure_argv.count(base_arg) == 1
        assert str(prepared_headers[0]) in dict(
            supply.evidence[f"{label}_dependency_closure"]
        )
    assert not prepared_headers[0].exists()


def test_screening_condition_gate_fails_without_prepared_base_side_effect(
        monkeypatch):
    monkeypatch.setattr(
        screening_driver.buildcache,
        "prepare_masstree_fetchcontent",
        lambda **_kwargs: None,
    )

    with pytest.raises(
            condition_meaning_gate.ConditionMeaningGateError,
            match="preprocess-failed",
    ):
        screening_driver._run_condition_gate_for_genome(
            str(_CONDITION_FIXTURES / "prepared-base-required"),
            Genome("silo", {"BACKOFF_FIXED": 5}),
            stock_root=None, cxx=_any_cxx(), cmake=_any_cmake(),
            expected_toolchain_manifest={"route": "backoff-screening"},
        )


def test_screening_condition_gate_without_manifest_preserves_unsupplied_path(
        monkeypatch):
    capture_calls = []
    real_capture = condition_meaning_gate.capture_define_inputs

    class NoTemporaryDirectory:
        @staticmethod
        def TemporaryDirectory(*_args, **_kwargs):
            pytest.fail("manifest None path must not create a supply base")

    def capture(*args, **kwargs):
        capture_calls.append((args, kwargs))
        return real_capture(*args, **kwargs)

    monkeypatch.setattr(screening_driver, "tempfile", NoTemporaryDirectory)
    monkeypatch.setattr(
        screening_driver.buildcache,
        "prepare_masstree_fetchcontent",
        lambda **_kwargs: pytest.fail("manifest None path must not prepare"),
    )
    monkeypatch.setattr(
        screening_driver.condition_meaning_gate, "capture_define_inputs", capture,
    )

    run = screening_driver._run_condition_gate_for_genome(
        str(_CONDITION_FIXTURES / "supplied"),
        Genome("silo", {"BACKOFF_FIXED": 5}),
        stock_root=None, cxx=_any_cxx(), cmake=_any_cmake(),
    )

    assert run is not None and run.admission.admitted
    assert all(
        not argument.startswith("-DFETCHCONTENT_BASE_DIR=")
        for argument in capture_calls[0][1]["configure_args"]
    )


def test_screening_condition_gate_no_requests_does_not_prepare_with_manifest(
        monkeypatch):
    class NoTemporaryDirectory:
        @staticmethod
        def TemporaryDirectory(*_args, **_kwargs):
            pytest.fail("request-free path must not create a supply base")

    monkeypatch.setattr(screening_driver, "tempfile", NoTemporaryDirectory)
    monkeypatch.setattr(
        screening_driver.buildcache,
        "prepare_masstree_fetchcontent",
        lambda **_kwargs: pytest.fail("request-free path must not prepare"),
    )

    assert screening_driver._run_condition_gate_for_genome(
        "unused", Genome("silo", {"BACK_OFF": 1}),
        stock_root=None, cxx="unused", cmake="unused",
        expected_toolchain_manifest={"route": "backoff-screening"},
    ) is None


def test_screening_condition_gate_prepare_is_nested_inside_stock_checkout(
        tmp_path, monkeypatch):
    source_root = (tmp_path / "patched").resolve()
    stock_root = (tmp_path / "stock").resolve()
    source_root.mkdir()
    stock_root.mkdir()
    events = []
    state = {"stock_active": False, "base": None}
    expected = {"route": "backoff-screening"}

    class Checkout:
        def __enter__(self):
            state["stock_active"] = True
            events.append("stock-enter")
            return str(stock_root)

        def __exit__(self, exc_type, exc, traceback):
            events.append("stock-exit")
            assert state["base"] is not None
            assert not state["base"].exists()
            state["stock_active"] = False

    def checkout(commit, *, base_dir):
        assert commit == "deadbeef"
        assert base_dir == str(source_root)
        return Checkout()

    def prepare(**kwargs):
        events.append("prepare")
        assert state["stock_active"]
        assert kwargs["expected_toolchain_manifest"] is expected
        state["base"] = Path(kwargs["fetchcontent_base_dir"])
        assert state["base"].is_dir()

    def capture(root, *, stock_root: str, configure_args):
        events.append("capture")
        assert state["stock_active"] and state["base"].is_dir()
        assert root == str(source_root)
        assert stock_root == str(tmp_path / "stock")
        assert configure_args[-1] == (
            f"-DFETCHCONTENT_BASE_DIR={state['base']}"
        )
        return object()

    def supply(*_args, **_kwargs):
        events.append("supply")
        assert state["stock_active"] and state["base"].is_dir()
        return object()

    def meaning(*_args, **kwargs):
        events.append("meaning")
        assert kwargs["declaration"] is None
        assert state["stock_active"] and state["base"].is_dir()
        return object()

    class Admission:
        admitted = True

    def admit(*_args, **kwargs):
        events.append("admission")
        assert kwargs["use_class"] == "raw"
        assert state["stock_active"] and state["base"].is_dir()
        return Admission()

    monkeypatch.setattr(screening_driver.patchharness, "checkout", checkout)
    monkeypatch.setattr(
        screening_driver.buildcache, "prepare_masstree_fetchcontent", prepare,
    )
    monkeypatch.setattr(
        screening_driver.condition_meaning_gate, "capture_define_inputs", capture,
    )
    monkeypatch.setattr(
        screening_driver.condition_meaning_gate,
        "evaluate_define_supply_effectuation", supply,
    )
    monkeypatch.setattr(
        screening_driver.condition_meaning_gate,
        "evaluate_define_runtime_meaning", meaning,
    )
    monkeypatch.setattr(
        screening_driver.condition_meaning_gate,
        "require_condition_gate_family", admit,
    )

    run = screening_driver._require_condition_gate_before_evaluation(
        str(source_root), "deadbeef", Genome("silo", {"BACKOFF_FIXED": -1}),
        cxx="unused", cmake="unused",
        expected_toolchain_manifest=expected,
    )

    assert run is not None and run.admission.admitted
    assert events == [
        "stock-enter", "prepare", "capture", "supply", "meaning",
        "admission", "stock-exit",
    ]
    assert state["stock_active"] is False
    assert state["base"] is not None and not state["base"].exists()


def test_screening_condition_gate_rejects_route_absent_from_real_build_args(
        monkeypatch):
    genome = Genome("silo", {"IZANAGI_BREAK_PERMUTATION": 1})
    monkeypatch.setattr(
        screening_driver.buildcache,
        "prepare_masstree_fetchcontent",
        lambda **_kwargs: pytest.fail("route mismatch must precede prepare"),
    )

    with pytest.raises(
            condition_meaning_gate.ConditionMeaningGateError,
            match="screening-build-route-mismatch.*IZANAGI_BREAK_PERMUTATION=1",
    ):
        screening_driver._run_condition_gate_for_genome(
            str(_CONDITION_FIXTURES / "supplied"), genome,
            stock_root=None, cxx=_any_cxx(), cmake=_any_cmake(),
            expected_toolchain_manifest={"route": "backoff-screening"},
        )


def test_screening_condition_gate_rejects_missing_real_companion_define():
    genome = Genome("ss2pl", {"SS2PL_LOCK_KIND": 0})

    with pytest.raises(
            condition_meaning_gate.ConditionMeaningGateError,
            match="screening-build-route-mismatch.*SS2PL_LOCK_IMPL=1",
    ):
        screening_driver._run_condition_gate_for_genome(
            str(_CONDITION_FIXTURES / "supplied"), genome,
            stock_root=None, cxx=_any_cxx(), cmake=_any_cmake(),
        )


def test_screening_condition_gate_is_before_real_evaluate_build_sink():
    source = inspect.getsource(screening_driver.evaluate_candidate)

    source_evidence = source.index("evidence = source_digest.resolve_evidence(")
    gate = source.index("_require_condition_gate_before_evaluation(")
    build_sink = source.index("return evaluate(")
    assert source_evidence < gate < build_sink
    gate_call = source[gate:build_sink]
    assert "evidence.source_root" in gate_call
    assert (
        "expected_toolchain_manifest=expected_toolchain_manifest" in gate_call
    )


def test_screening_condition_requests_reject_non_exact_domain_value():
    genome = Genome("silo", {"SORT_VARIANT": True})

    with pytest.raises(TypeError, match="exact int"):
        screening_driver._condition_requests_for_genome(genome)


def test_screening_condition_requests_cover_exact_define_specs():
    flags = {
        macro: screening_driver._CONDITION_DEFAULTS[macro] + 1
        for macro in condition_meaning_gate.DEFINE_SPECS
    }
    requests = screening_driver._condition_requests_for_genome(
        Genome("silo", flags),
    )

    assert set(screening_driver._CONDITION_DEFAULTS) == set(
        condition_meaning_gate.DEFINE_SPECS
    )
    assert {
        macro: screening_driver._CONDITION_DEFAULTS[macro]
        for macro in (
            "CICADA_FWD_ENABLE",
            "CICADA_FWD_COUNT",
            "CICADA_LONGTX",
            "CICADA_INTERVAL_GC",
            "CICADA_INTERVAL_GC_GENERAL",
            "CICADA_INTERVAL_COUNT",
            "CICADA_INTERVAL_LONGTX",
        )
    } == {
        "CICADA_FWD_ENABLE": 0,
        "CICADA_FWD_COUNT": 0,
        "CICADA_LONGTX": 0,
        "CICADA_INTERVAL_GC": 0,
        "CICADA_INTERVAL_GC_GENERAL": 0,
        "CICADA_INTERVAL_COUNT": 0,
        "CICADA_INTERVAL_LONGTX": 0,
    }
    assert [request.macro for request in requests] == sorted(
        condition_meaning_gate.DEFINE_SPECS
    )
    assert [request.requested_value for request in requests] == [
        flags[macro] for macro in sorted(condition_meaning_gate.DEFINE_SPECS)
    ]
    terminal_request = next(
        request for request in requests
        if request.macro == "BACKOFF_TRACE_TERMINAL_US"
    )
    assert screening_driver._CONDITION_DEFAULTS[
        "BACKOFF_TRACE_TERMINAL_US"
    ] == 0
    assert (
        terminal_request.requested_value,
        terminal_request.default_value,
        terminal_request.stock_comparison,
    ) == (1, 0, False)


def test_screening_condition_requests_accept_no_non_domain_substitute():
    genome = Genome("silo", {"BACK_OFF": 1, "WAL": 0})

    assert screening_driver._condition_requests_for_genome(genome) == ()


def test_screening_condition_gate_preserves_real_non_domain_build_inputs():
    genome = Genome("silo", {
        "BACK_OFF": 1,
        "BACKOFF_FIXED": 5,
        "NO_WAIT_OF_TICTOC": 0,
    })

    assert screening_driver._condition_gate_base_configure_args(genome) == (
        "-DCCBENCH_BACK_OFF=1",
        "-DCCBENCH_NO_WAIT_OF_TICTOC=0",
    )


def test_load_between_run_floor_accepts_legacy_schema_without_version(tmp_path):
    calibration = str(tmp_path / "calibration")
    _write_floor(calibration, floor=0.03, schema_version=None)
    assert screening_driver.load_between_run_floor(
        WORKLOAD, protocol="silo", calibration_dir=calibration,
    ) == 0.03


def test_load_between_run_floor_accepts_current_schema_version(tmp_path):
    calibration = str(tmp_path / "calibration")
    _write_floor(calibration, floor=0.04)
    assert screening_driver.load_between_run_floor(
        WORKLOAD, protocol="silo", calibration_dir=calibration,
    ) == 0.04


def test_load_between_run_floor_rejects_mismatched_schema_version(tmp_path):
    calibration = str(tmp_path / "calibration")
    _write_floor(calibration, schema_version="between-run-noise-floor/v0")
    with pytest.raises(ValueError, match="schema_version"):
        screening_driver.load_between_run_floor(
            WORKLOAD, protocol="silo", calibration_dir=calibration,
        )


def test_load_between_run_floor_rejects_explicit_null_schema_version(tmp_path):
    calibration = tmp_path / "calibration"
    calibration.mkdir()
    (calibration / "between_run_noise_null_schema.json").write_text(
        json.dumps({
            "schema_version": None,
            "workload": WORKLOAD,
            "between_run": {"cv": 0.03},
        }), encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        screening_driver.load_between_run_floor(
            WORKLOAD, protocol="silo", calibration_dir=str(calibration),
        )


def test_load_between_run_floor_rejects_explicit_empty_schema_version(tmp_path):
    calibration = tmp_path / "calibration"
    calibration.mkdir()
    (calibration / "between_run_noise_empty_schema.json").write_text(
        json.dumps({
            "schema_version": "",
            "workload": WORKLOAD,
            "between_run": {"cv": 0.03},
        }), encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        screening_driver.load_between_run_floor(
            WORKLOAD, protocol="silo", calibration_dir=str(calibration),
        )


def test_load_between_run_floor_rejects_non_dict_json_root(tmp_path):
    calibration = tmp_path / "calibration"
    calibration.mkdir()
    (calibration / "between_run_noise_root.json").write_text(
        json.dumps([{"workload": WORKLOAD}]), encoding="utf-8")
    with pytest.raises(ValueError, match="root"):
        screening_driver.load_between_run_floor(
            WORKLOAD, protocol="silo", calibration_dir=str(calibration),
        )


def test_load_between_run_floor_rejects_non_dict_between_run(tmp_path):
    calibration = str(tmp_path / "calibration")
    _write_floor(calibration)
    path = os.path.join(calibration, "between_run_noise_fixture.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "schema_version": "between-run-noise-floor/v1",
            "workload": WORKLOAD,
            "genome": "silo|BACK_OFF=0",
            "between_run": "not-an-object",
        }, f)
    with pytest.raises(ValueError, match="between_run"):
        screening_driver.load_between_run_floor(
            WORKLOAD, protocol="silo", calibration_dir=calibration,
        )


def test_load_between_run_floor_selects_requested_protocol_among_same_workload(
        tmp_path):
    calibration = str(tmp_path / "calibration")
    _write_floor(
        calibration, floor=0.03, protocol="silo",
        filename="between_run_noise_silo.json",
    )
    _write_floor(
        calibration, floor=0.07, protocol="mocc",
        filename="between_run_noise_mocc.json",
    )
    assert screening_driver.load_between_run_floor(
        WORKLOAD, protocol="silo", calibration_dir=calibration,
    ) == 0.03
    assert screening_driver.load_between_run_floor(
        WORKLOAD, protocol="mocc", calibration_dir=calibration,
    ) == 0.07


def test_load_between_run_floor_rejects_single_wrong_protocol_floor(tmp_path):
    calibration = str(tmp_path / "calibration")
    _write_floor(
        calibration, floor=0.07, protocol="mocc",
        filename="between_run_noise_mocc.json",
    )
    with pytest.raises(ValueError, match="一意"):
        screening_driver.load_between_run_floor(
            WORKLOAD, protocol="silo", calibration_dir=calibration,
        )


def test_load_between_run_floor_rejects_duplicate_same_protocol(tmp_path):
    calibration = str(tmp_path / "calibration")
    _write_floor(calibration, filename="between_run_noise_first.json")
    _write_floor(calibration, filename="between_run_noise_second.json")
    with pytest.raises(ValueError, match="一意"):
        screening_driver.load_between_run_floor(
            WORKLOAD, protocol="silo", calibration_dir=calibration,
        )


@pytest.mark.parametrize("genome", [
    None,
    3,
    "silo",
    "|BACK_OFF=0",
    "mocc|garbage",
    "silo|B=x",
    "silo|Z=1,A=0",
    "silo|A=1,A=2",
    "silo|",
])
def test_load_between_run_floor_rejects_missing_or_malformed_genome(
        tmp_path, genome):
    calibration = tmp_path / "calibration"
    calibration.mkdir()
    document = {
        "schema_version": "between-run-noise-floor/v1",
        "workload": WORKLOAD,
        "between_run": {"cv": 0.03},
    }
    if genome is not None:
        document["genome"] = genome
    (calibration / "between_run_noise_invalid.json").write_text(
        json.dumps(document), encoding="utf-8",
    )
    with pytest.raises(ValueError, match="genome"):
        screening_driver.load_between_run_floor(
            WORKLOAD, protocol="silo", calibration_dir=str(calibration),
        )


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_prepare_screening_bakes_identity_and_uses_new_same_campaign_baseline(
        tmp_path, _certified_writer_authority):
    authorization, contract = _certified_writer_authority
    calibration = str(tmp_path / "calibration")
    output = str(tmp_path / "output")
    _write_floor(calibration, floor=0.03000001)
    seen = {}

    def measure(cfg, layout):
        seen["cfg"] = cfg
        seen["layout"] = layout
        assert cfg.search_config["screening"] == {
            "baseline_ref": "baseline-v1", "floor": "0.03000001", "k": "1.5",
            "high_abort_factor": "2.0"}
        wal.log(layout, "baseline-v1", STAGE_BENCH_DONE, "test", {
            "median_tps": 10000.0,
            "leading_indicators": {"abort_rate": 0.04},
        }, ts=1234.0)
        receipt_support.log_receipted_commit(
            layout, "baseline-v1", _CONTRACT.env_tag, {
            "fitness_tps": 10000.0,
            "contract_sha256": _CONTRACT.contract_sha256,
            }, operation_identity="baseline-v1", ts=1235.0,
        )

    prepared = screening_driver.prepare_screening_campaign(
        _cfg(), WORKLOAD, "baseline-v1", measure,
        protocol="silo",
        authorization_contract=authorization,
        env_tag=contract.env_tag,
        clocks_per_us=contract.clocks_per_us,
        numactl=contract.numactl,
        calibration_dir=calibration, output_root=output,
        build_context=_BUILD_CONTEXT)
    assert prepared.cfg is seen["cfg"] and prepared.layout is seen["layout"]
    assert prepared.screening.baseline_tps == 10000.0
    assert prepared.screening.baseline_abort_rate == 0.04
    assert prepared.screening.baseline_measured_at == 1234.0
    assert prepared.screening.floor == 0.03000001
    ident.verify_screening_preimage(
        prepared.screening, wal.read_lock(prepared.layout))


def test_prepare_screening_fails_closed_when_floor_json_missing(
        tmp_path, _certified_writer_authority):
    authorization, contract = _certified_writer_authority
    called = False

    def measure(_cfg, _layout):
        nonlocal called
        called = True

    with pytest.raises(ValueError, match="floor JSON"):
        screening_driver.prepare_screening_campaign(
            _cfg(), WORKLOAD, "baseline-v1", measure,
            protocol="silo",
            authorization_contract=authorization,
            env_tag=contract.env_tag,
            clocks_per_us=contract.clocks_per_us,
            numactl=contract.numactl,
            calibration_dir=str(tmp_path / "missing"), output_root=str(tmp_path / "out"),
            build_context=_BUILD_CONTEXT)
    assert called is False


def test_prepare_screening_rejects_authorization_before_layout_or_wal(
        tmp_path, _certified_writer_authority):
    _, contract = _certified_writer_authority
    output = tmp_path / "output"
    calibration = tmp_path / "calibration"
    _write_floor(str(calibration))
    called = False

    def measure(_cfg, _layout):
        nonlocal called
        called = True

    with pytest.raises(TypeError, match="authorization_contract"):
        screening_driver.prepare_screening_campaign(
            _cfg(), WORKLOAD, "baseline-v1", measure,
            protocol="silo",
            authorization_contract=None,
            env_tag=contract.env_tag,
            clocks_per_us=contract.clocks_per_us,
            numactl=contract.numactl,
            calibration_dir=str(calibration), output_root=str(output),
            build_context=_BUILD_CONTEXT,
        )
    assert called is False
    assert not output.exists()


@pytest.mark.parametrize("missing", ["median", "abort_rate", "commit"])
@pytest.mark.usefixtures("ratified_enforcement_source")
def test_prepare_screening_requires_complete_baseline_evidence(
        tmp_path, missing, _certified_writer_authority):
    authorization, contract = _certified_writer_authority
    calibration = str(tmp_path / f"cal-{missing}")
    _write_floor(calibration)

    def measure(_cfg, layout):
        payload = {"median_tps": 100.0,
                   "leading_indicators": {"abort_rate": 0.1}}
        if missing == "median":
            payload.pop("median_tps")
        if missing == "abort_rate":
            payload["leading_indicators"].pop("abort_rate")
        wal.log(layout, "baseline-v1", STAGE_BENCH_DONE, "test", payload, ts=10.0)
        if missing != "commit":
            receipt_support.log_receipted_commit(
                layout, "baseline-v1", _CONTRACT.env_tag, {
                "contract_sha256": _CONTRACT.contract_sha256,
                }, operation_identity=f"baseline-{missing}", ts=11.0,
            )

    with pytest.raises(ValueError):
        screening_driver.prepare_screening_campaign(
            _cfg(), WORKLOAD, "baseline-v1", measure,
            protocol="silo",
            authorization_contract=authorization,
            env_tag=contract.env_tag,
            clocks_per_us=contract.clocks_per_us,
            numactl=contract.numactl,
            calibration_dir=calibration, output_root=str(tmp_path / f"out-{missing}"),
            build_context=_BUILD_CONTEXT)


def test_prepare_repairs_tail_before_baseline_callback(
        tmp_path, _certified_writer_authority):
    authorization, contract = _certified_writer_authority
    calibration = str(tmp_path / "calibration")
    output = str(tmp_path / "output")
    _write_floor(calibration)
    policy = ident.screening_policy_search_config("baseline-v1", 0.03, 1.5, 2.0)
    cfg = CampaignConfig(
        **{**_cfg().__dict__, "search_config": {**_cfg().search_config, **policy}})
    layout = campaign_layout(str(ident.campaign_id(cfg)), output).ensure()
    wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
    _log_completed_attempt(layout, "prior", Genome("silo", {"BACK_OFF": 0}))
    with open(layout.wal_file, "ab") as stream:
        stream.write(b'{"torn":')
    surfaced = []

    def measure(_cfg, callback_layout):
        assert callback_layout.wal_file == layout.wal_file
        records, truncated = wal.read_records_checked(callback_layout)
        assert truncated is False and [r.variant for r in records] == ["prior"] * 3
        wal.log(callback_layout, "baseline-v1", STAGE_BENCH_DONE, "test", {
            "median_tps": 100.0,
            "leading_indicators": {"abort_rate": 0.1},
        }, ts=10.0)
        receipt_support.log_receipted_commit(
            callback_layout, "baseline-v1", _CONTRACT.env_tag, {
                    "contract_sha256": _CONTRACT.contract_sha256,
                }, operation_identity="baseline-after-repair", ts=11.0,
        )

    screening_driver.prepare_screening_campaign(
        _cfg(), WORKLOAD, "baseline-v1", measure,
        protocol="silo",
        authorization_contract=authorization,
        env_tag=contract.env_tag,
        clocks_per_us=contract.clocks_per_us,
        numactl=contract.numactl,
        calibration_dir=calibration, output_root=output, log=surfaced.append,
        build_context=_BUILD_CONTEXT)
    assert len(surfaced) == 1 and '"status": "repaired"' in surfaced[0]
    assert '"removed_bytes": 8' in surfaced[0]


def test_evaluate_candidate_repairs_tail_before_replay_and_evaluate(
        tmp_path, monkeypatch, _certified_writer_authority):
    authorization, contract = _certified_writer_authority
    cfg = _cfg()
    layout = campaign_layout(str(ident.campaign_id(cfg)), str(tmp_path / "out")).ensure()
    wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
    prior_genome = Genome("silo", {"BACK_OFF": 0})
    _log_completed_attempt(layout, "prior", prior_genome)
    with open(layout.wal_file, "ab") as stream:
        stream.write("途中".encode("utf-8")[:4])
    genome = Genome("silo", {"BACK_OFF": 1})
    calls = []

    def evaluate(candidate, candidate_layout, *args, **kwargs):
        records, truncated = wal.read_records_checked(candidate_layout)
        assert truncated is False and [r.variant for r in records] == ["prior"] * 3
        calls.append((candidate, args, kwargs))
        return EvalResult(
            genome=candidate, variant="candidate", certified=True, aborted=False)

    monkeypatch.setattr(screening_driver, "evaluate", evaluate)
    monkeypatch.setattr(
        screening_driver.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: _source_evidence(genome),
    )
    result = screening_driver.evaluate_candidate(
        cfg, layout, genome, PerfConfig(records=1, threads=1),
        contract.env_tag, contract.clocks_per_us,
        numactl=contract.numactl,
        authorization_contract=authorization,
        build_context=_BUILD_CONTEXT,
        screening=None, src_token="stock", log=lambda message: None)
    assert result is not None and result.certified and len(calls) == 1
    assert calls[0][0] == genome and len(calls[0][1]) == 4
    assert set(calls[0][2]) == {
        "numactl", "do_settle", "src_token", "extra_correctness", "screening",
        "log", "ccbench_dir", "cache_root", "authorization_contract",
        "build_context", "capability_resolver", "source_evidence",
    }
    assert "use_perf" not in calls[0][2]
    assert "perf_preflight_receipt" not in calls[0][2]


def test_evaluate_candidate_forwards_v2_contract_and_toolchain_binding(
        tmp_path, monkeypatch, _certified_writer_authority):
    authorization, contract = _certified_writer_authority
    cfg = _cfg()
    layout = campaign_layout(str(ident.campaign_id(cfg)), str(tmp_path / "out")).ensure()
    wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
    genome = Genome("silo", {"BACK_OFF": 1})
    expected = _toolchain_manifest()
    seen_source = []

    def evaluate(candidate, candidate_layout, *args, **kwargs):
        assert candidate_layout is layout
        seen_source.append(kwargs)
        return EvalResult(
            genome=candidate, variant="candidate", certified=True, aborted=False,
        )

    monkeypatch.setattr(screening_driver, "evaluate", evaluate)
    monkeypatch.setattr(
        screening_driver.source_digest, "resolve_evidence",
        lambda *args, **kwargs: (
            seen_source.append({"source_cxx": kwargs["cxx"]})
            or _source_evidence(genome)
        ),
    )

    result = screening_driver.evaluate_candidate(
        cfg, layout, genome, PerfConfig(records=1, threads=1),
        contract.env_tag, contract.clocks_per_us,
        numactl=contract.numactl,
        authorization_contract=authorization,
        build_context=_BUILD_CONTEXT,
        screening=None, env_contract=contract,
        expected_toolchain_manifest=expected,
        declared_use_class="official", src_token="stock", log=lambda message: None,
    )

    assert result is not None and result.certified
    evaluate_kwargs = seen_source[-1]
    assert evaluate_kwargs["env_contract"] is contract
    assert evaluate_kwargs["expected_toolchain_manifest"] == expected
    assert evaluate_kwargs["declared_use_class"] == "official"
    assert seen_source[0]["source_cxx"] == "test-cxx"


def test_evaluate_candidate_uses_one_canonical_root_for_prepare_gate_and_build(
        tmp_path, monkeypatch, _certified_writer_authority):
    authorization, contract = _certified_writer_authority
    cfg = _cfg()
    layout = campaign_layout(
        str(ident.campaign_id(cfg)), str(tmp_path / "out"),
    ).ensure()
    wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
    genome = Genome("silo", {"BACKOFF_FIXED": 5})
    source_root = (_CONDITION_FIXTURES / "supplied").resolve()
    cxx = _any_cxx()
    cmake = _any_cmake()
    expected = _toolchain_manifest(cxx=cxx, cmake=cmake)
    prepare_calls = []
    capture_calls = []
    evaluate_calls = []
    real_capture = condition_meaning_gate.capture_define_inputs

    def prepare(**kwargs):
        prepare_calls.append(kwargs)

    def capture(root, **kwargs):
        capture_calls.append((root, kwargs))
        return real_capture(root, **kwargs)

    def evaluate(candidate, candidate_layout, *args, **kwargs):
        evaluate_calls.append((candidate, candidate_layout, args, kwargs))
        return EvalResult(
            genome=candidate, variant="candidate", certified=True, aborted=False,
        )

    monkeypatch.setattr(
        screening_driver.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: _source_evidence(
            genome, root=str(source_root),
        ),
    )
    monkeypatch.setattr(
        screening_driver.buildcache, "prepare_masstree_fetchcontent", prepare,
    )
    monkeypatch.setattr(
        screening_driver.condition_meaning_gate, "capture_define_inputs", capture,
    )
    monkeypatch.setattr(screening_driver, "evaluate", evaluate)

    result = screening_driver.evaluate_candidate(
        cfg, layout, genome, PerfConfig(records=1, threads=1),
        contract.env_tag, contract.clocks_per_us,
        numactl=contract.numactl,
        authorization_contract=authorization,
        build_context=_BUILD_CONTEXT,
        screening=None, env_contract=contract,
        expected_toolchain_manifest=expected,
        declared_use_class="official", src_token="stock",
        ccbench_dir=str(source_root / ".." / "supplied"),
        log=lambda _message: None,
    )

    assert result is not None and result.certified
    assert len(prepare_calls) == len(capture_calls) == len(evaluate_calls) == 1
    prepare_call = prepare_calls[0]
    gated_root, gate_kwargs = capture_calls[0]
    build_evidence = evaluate_calls[0][3]["source_evidence"]
    assert prepare_call["ccbench_dir"] == str(source_root)
    assert gated_root == str(source_root)
    assert build_evidence.source_root == str(source_root)
    assert prepare_call["expected_toolchain_manifest"] is expected
    assert gate_kwargs["stock_root"] is None
    base = prepare_call["fetchcontent_base_dir"]
    assert gate_kwargs["configure_args"][-1] == (
        f"-DFETCHCONTENT_BASE_DIR={base}"
    )
    assert not Path(base).exists()


def test_evaluate_candidate_prepare_failure_escapes_without_wal_abort(
        tmp_path, monkeypatch, _certified_writer_authority):
    authorization, contract = _certified_writer_authority
    cfg = _cfg()
    layout = campaign_layout(
        str(ident.campaign_id(cfg)), str(tmp_path / "out"),
    ).ensure()
    wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
    genome = Genome("silo", {"BACKOFF_FIXED": 5})
    source_root = (_CONDITION_FIXTURES / "supplied").resolve()
    expected = _toolchain_manifest()
    failure = screening_driver.buildcache.MasstreeFetchContentError(
        "target", "synthetic prepare failure",
    )
    evaluate_calls = []

    def fail_prepare(**_kwargs):
        raise failure

    monkeypatch.setattr(
        screening_driver.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: _source_evidence(
            genome, root=str(source_root),
        ),
    )
    monkeypatch.setattr(
        screening_driver.buildcache,
        "prepare_masstree_fetchcontent",
        fail_prepare,
    )
    monkeypatch.setattr(
        screening_driver, "evaluate",
        lambda *args, **kwargs: evaluate_calls.append((args, kwargs)),
    )

    with pytest.raises(
            screening_driver.buildcache.MasstreeFetchContentError,
    ) as caught:
        screening_driver.evaluate_candidate(
            cfg, layout, genome, PerfConfig(records=1, threads=1),
            contract.env_tag, contract.clocks_per_us,
            numactl=contract.numactl,
            authorization_contract=authorization,
            build_context=_BUILD_CONTEXT,
            screening=None, env_contract=contract,
            expected_toolchain_manifest=expected,
            declared_use_class="official", src_token="stock",
            ccbench_dir=str(source_root), log=lambda _message: None,
        )

    assert caught.value is failure
    assert evaluate_calls == []
    assert wal.read_records(layout) == []


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_evaluate_candidate_unavailable_perf_passes_degraded_kwargs_once(
        tmp_path, monkeypatch, _certified_writer_authority):
    authorization, contract = _certified_writer_authority
    cfg = _cfg()
    layout = campaign_layout(str(ident.campaign_id(cfg)), str(tmp_path / "out")).ensure()
    ident.ensure_resumable_wal(
        cfg, layout, admission_policy=_BUILD_CONTEXT.policy,
    )
    genome = Genome("silo", {"BACK_OFF": 1})
    unavailable = _canonical_perf_receipt("unavailable")
    probe_calls = []
    evaluate_calls = []

    def probe():
        probe_calls.append(1)
        return unavailable

    def evaluate(*args, **kwargs):
        evaluate_calls.append((args, kwargs))
        return EvalResult(
            genome=genome, variant="candidate", certified=True, aborted=False,
        )

    monkeypatch.setattr(
        screening_driver._perf_preflight, "probe_perf_availability", probe,
    )
    monkeypatch.setattr(screening_driver, "evaluate", evaluate)
    monkeypatch.setattr(
        screening_driver.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: _source_evidence(genome),
    )

    result = screening_driver.evaluate_candidate(
        cfg, layout, genome, PerfConfig(records=1, threads=1),
        contract.env_tag, contract.clocks_per_us,
        numactl=contract.numactl,
        authorization_contract=authorization,
        build_context=_BUILD_CONTEXT,
        screening=None, src_token="stock", log=lambda message: None,
    )

    assert result is not None and result.certified
    assert probe_calls == [1]
    assert len(evaluate_calls) == 1
    assert evaluate_calls[0][1]["use_perf"] is False
    assert evaluate_calls[0][1]["perf_preflight_receipt"] == unavailable


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_evaluate_candidate_probe_error_refuses_before_evaluate(
        tmp_path, monkeypatch, _certified_writer_authority):
    authorization, contract = _certified_writer_authority
    cfg = _cfg()
    layout = campaign_layout(str(ident.campaign_id(cfg)), str(tmp_path / "out")).ensure()
    ident.ensure_resumable_wal(
        cfg, layout, admission_policy=_BUILD_CONTEXT.policy,
    )
    genome = Genome("silo", {"BACK_OFF": 1})
    evaluate_calls = []
    monkeypatch.setattr(
        screening_driver._perf_preflight, "probe_perf_availability",
        lambda: _canonical_perf_receipt("probe_error"),
    )
    monkeypatch.setattr(
        screening_driver, "evaluate",
        lambda *args, **kwargs: evaluate_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        screening_driver.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: _source_evidence(genome),
    )

    with pytest.raises(screening_driver._perf_preflight.PerfPreflightError):
        screening_driver.evaluate_candidate(
            cfg, layout, genome, PerfConfig(records=1, threads=1),
            contract.env_tag, contract.clocks_per_us,
            numactl=contract.numactl,
            authorization_contract=authorization,
            build_context=_BUILD_CONTEXT,
            screening=None, src_token="stock", log=lambda message: None,
        )

    assert evaluate_calls == []


@pytest.mark.parametrize("failure_kind", ["append", "framing"])
@pytest.mark.usefixtures("ratified_enforcement_source")
def test_evaluate_candidate_does_not_append_abort_after_wal_io_error(
        tmp_path, monkeypatch, failure_kind, _certified_writer_authority):
    authorization, contract = _certified_writer_authority
    cfg = _cfg()
    layout = campaign_layout(str(ident.campaign_id(cfg)), str(tmp_path / "out")).ensure()
    ident.ensure_resumable_wal(
        cfg, layout, admission_policy=_BUILD_CONTEXT.policy,
    )
    genome = Genome("silo", {"BACK_OFF": 1})
    failure = (wal.WalAppendError(
        layout.wal_file, 10, 3, "write", OSError("disk"))
        if failure_kind == "append" else wal.WalFramingError("unframed"))

    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(screening_driver, "evaluate", fail)
    monkeypatch.setattr(
        screening_driver.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: _source_evidence(genome),
    )
    with pytest.raises(type(failure)) as caught:
        screening_driver.evaluate_candidate(
            cfg, layout, genome, PerfConfig(records=1, threads=1),
            contract.env_tag, contract.clocks_per_us,
            numactl=contract.numactl,
            authorization_contract=authorization,
            build_context=_BUILD_CONTEXT,
            screening=None, src_token="stock", log=lambda message: None)
    assert caught.value is failure
    assert wal.read_records(layout) == []
