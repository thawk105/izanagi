import ast
import base64
import contextlib
import copy
import errno
import hashlib
import inspect
import json
import os
import socket
import subprocess
import time
from pathlib import Path

import pytest

from orchestrator.campaign import build_admission, buildcache, loop, source_digest
from orchestrator.campaign import (
    campaign_lock,
    env_contract,
    ident,
    pin,
    reservation,
    wal,
)
from orchestrator.campaign import paper_story_a2_certification as A2
from orchestrator.campaign.model import (
    CampaignConfig,
    STAGE_ABORT,
    STAGE_BENCH_DONE,
    STAGE_BUILD_DONE,
    STAGE_BUILD_START,
    STAGE_COMMIT,
    STAGE_VERIFY_DONE,
    WalRecord,
)
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.calibrator.runner import PERF_EVENTS
from orchestrator.campaign.pipeline import (
    LEGACY_TAG,
    PERFORMANCE_TAG,
    PerfConfig,
    VERIFY_LEGACY_PLUS_PERFORMANCE,
    VERIFY_LEGACY_PLUS_S2,
    performance_correctness_workload,
    s2_correctness_workload,
    variant_id,
)

_REAL_CONDITION_GATE_FAMILY = A2._condition_gate_family_context


def _staged_sources(fetchcontent_base):
    base = Path(fetchcontent_base)
    return {
        "masstree": base / "masstree-src",
        "mimalloc": base / "mimalloc-src",
        "googletest": base / "googletest-src",
    }


@pytest.fixture(autouse=True)
def _avoid_condition_compiler_work_in_protocol_tests(monkeypatch):
    @contextlib.contextmanager
    def bypass_condition_gate(source_root, genomes, **_kwargs):
        records = tuple(
            json.dumps({
                "admission_id": f"condition-gate/admission/{index}",
                "admission_digest": hashlib.sha256(
                    f"admission-{index}".encode("ascii")).hexdigest(),
                "use_class": "paper",
                "admitted": True,
                "record_ids": [f"record-{index}"],
                "unestablished_meaning_macros": [],
            }, sort_keys=True, separators=(",", ":"))
            for index, _genome in enumerate(genomes)
        )
        yield Path(source_root), None, records

    monkeypatch.setattr(A2, "_condition_gate_family_context", bypass_condition_gate)


@pytest.fixture(autouse=True)
def _avoid_live_third_party_git_probes_in_protocol_tests(monkeypatch):
    def verify(fetchcontent_base_dir, *, repo_root):
        assert repo_root == A2.POLICY_PATH.parents[2]
        return _staged_sources(fetchcontent_base_dir)

    monkeypatch.setattr(
        A2.s8b_floor_campaign,
        "_verify_pristine_floor_dependency_sources",
        verify,
    )
    monkeypatch.setattr(
        A2.buildcache,
        "_observe_fetchcontent_dependency_receipt",
        lambda _source: {"masstree_head": "a" * 40, "config_sha256": "b" * 64},
    )


def test_paper_condition_gate_is_p_strict_and_precedes_campaign(monkeypatch):
    run_source = inspect.getsource(A2.run_workload)
    assert run_source.index("_condition_gate_family_context(") < run_source.index(
        "summary = run_campaign("
    )
    assert run_source.index("_write_condition_gate_admissions_x(") \
        < run_source.index("summary = run_campaign(")
    helper_source = inspect.getsource(_REAL_CONDITION_GATE_FAMILY)
    assert 'use_class="paper"' in helper_source
    assert '"BACKOFF_FIXED"' in helper_source
    assert '"BACKOFF_NOINLINE"' in helper_source
    assert "declare_define_runtime_meaning" in helper_source
    assert "stock_root=source_root" in helper_source
    assert "STOCK_ADAPTIVE_BRANCH" in helper_source
    assert "condition_gate_receipts" in run_source
    assert '"patches/silo-backoff-fixed.patch"' in helper_source
    assert helper_source.count("patchharness.checkout(") == 1
    assert helper_source.index("patchharness.checkout(") < helper_source.index(
        "patchharness.applied("
    ) < helper_source.index("capture_define_inputs(")
    assert "as (variant_root, condition_gate_receipts," in run_source

    tree = ast.parse(run_source)
    condition_context = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.With)
        and any(
            isinstance(item.context_expr, ast.Call)
            and isinstance(item.context_expr.func, ast.Name)
            and item.context_expr.func.id == "_condition_gate_family_context"
            for item in node.items
        )
    )
    calls = [
        node
        for statement in condition_context.body
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
    ]
    campaign_call = next(
        call for call in calls
        if isinstance(call.func, ast.Name) and call.func.id == "run_campaign"
    )
    ccbench_dir = next(
        keyword.value for keyword in campaign_call.keywords
        if keyword.arg == "ccbench_dir"
    )
    assert (
        isinstance(ccbench_dir, ast.Call)
        and isinstance(ccbench_dir.func, ast.Attribute)
        and isinstance(ccbench_dir.func.value, ast.Name)
        and ccbench_dir.func.value.id == "os"
        and ccbench_dir.func.attr == "fspath"
        and len(ccbench_dir.args) == 1
        and isinstance(ccbench_dir.args[0], ast.Name)
        and ccbench_dir.args[0].id == "variant_root"
    )
    assert any(
        isinstance(call.func, ast.Name) and call.func.id == "write_json_x"
        for call in calls
    )
    _assert_condition_gate_context(monkeypatch)
    _assert_condition_gate_rejection(monkeypatch)


def _assert_condition_gate_context(monkeypatch):
    source_root = Path("/shared/ccbench")
    variant_root = Path("/scratch/job-variant")
    fetchcontent_base = Path("/scratch/fetchcontent")
    expected_toolchain_manifest = {"fixture": "toolchain"}
    events = []

    @contextlib.contextmanager
    def checkout(pin_commit, *, base_dir):
        events.append((
            "checkout-enter", variant_root, Path(base_dir), pin_commit))
        try:
            yield os.fspath(variant_root)
        finally:
            events.append(("checkout-exit", variant_root))

    @contextlib.contextmanager
    def applied(patch_path, pin_commit, *, ccbench_dir):
        assert patch_path == os.fspath(
            Path(A2.__file__).resolve().parents[2]
            / "patches/silo-backoff-fixed.patch"
        )
        events.append(("applied-enter", Path(ccbench_dir), pin_commit))
        try:
            yield None
        finally:
            events.append(("applied-exit", Path(ccbench_dir)))

    def prepare_masstree_fetchcontent(**kwargs):
        events.append((
            "prebuild", Path(kwargs["ccbench_dir"]),
            Path(kwargs["fetchcontent_base_dir"]),
        ))
        assert kwargs["expected_toolchain_manifest"] \
            is expected_toolchain_manifest
        assert kwargs == {
            "ccbench_dir": os.fspath(variant_root),
            "fetchcontent_base_dir": os.fspath(fetchcontent_base),
            "masstree_source_dir": os.fspath(
                fetchcontent_base / "masstree-src"),
            "mimalloc_source_dir": os.fspath(
                fetchcontent_base / "mimalloc-src"),
            "googletest_source_dir": os.fspath(
                fetchcontent_base / "googletest-src"),
            "expected_toolchain_manifest": expected_toolchain_manifest,
            "configure_timeout_s": 900,
            "target_timeout_s": 900,
            "dependency_prefix": "/dependency",
        }

    def capture(source, *, stock_root, configure_args):
        events.append(("capture", Path(source), Path(stock_root)))
        assert configure_args == (
            "-DCMAKE_PREFIX_PATH=/dependency",
            f"-DFETCHCONTENT_BASE_DIR={fetchcontent_base}",
            f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={fetchcontent_base}/masstree-src",
            f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={fetchcontent_base}/mimalloc-src",
            f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={fetchcontent_base}/googletest-src",
        )
        return object()

    def record(request, arm):
        payload = {
            "macro": request.macro,
            "arm": arm,
            "terminal_status": "green",
        }
        return A2.SimpleNamespace(
            macro=request.macro,
            arm=arm,
            reason_code="established",
            terminal_status="green",
            evidence={},
            canonical_json=lambda: json.dumps(payload),
        )

    def admit(supply_records, meaning_records, *, use_class):
        events.append(("admit", use_class))
        assert supply_records and meaning_records
        return A2.SimpleNamespace(
            admitted=True,
            canonical_json=lambda: json.dumps({"admitted": True}),
        )

    monkeypatch.setattr(A2.patchharness, "checkout", checkout)
    monkeypatch.setattr(A2.patchharness, "applied", applied)
    monkeypatch.setattr(
        A2.buildcache, "prepare_masstree_fetchcontent",
        prepare_masstree_fetchcontent)
    monkeypatch.setattr(
        A2.condition_meaning_gate, "capture_define_inputs", capture)
    monkeypatch.setattr(
        A2.condition_meaning_gate, "evaluate_define_supply_effectuation",
        lambda _captured, *, request, **_kwargs: record(request, "supply"))
    monkeypatch.setattr(
        A2.condition_meaning_gate, "evaluate_define_runtime_meaning",
        lambda _captured, *, request, **_kwargs: record(request, "meaning"))
    monkeypatch.setattr(
        A2.condition_meaning_gate, "require_condition_gate_family", admit)

    genome = A2.SimpleNamespace(
        flags={"BACKOFF_FIXED": 10, "BACKOFF_NOINLINE": 0})
    with _REAL_CONDITION_GATE_FAMILY(
            source_root, [genome], cxx="g++",
            dependency_prefix=Path("/dependency"),
            current_pin="abc1234",
            expected_toolchain_manifest=expected_toolchain_manifest,
            fetchcontent_base_dir=fetchcontent_base,
            staged_sources=_staged_sources(fetchcontent_base),
    ) as (observed_variant, receipts, canonical_records):
        assert observed_variant == variant_root
        assert len(receipts) == 1
        assert len(canonical_records) == 1
        events.append(("campaign", observed_variant))
        assert not any(event[0] == "applied-exit" for event in events)

    assert variant_root != source_root
    assert events.index(("applied-enter", variant_root, "abc1234")) < events.index(
        ("prebuild", variant_root, fetchcontent_base)
    ) < events.index(
        ("capture", variant_root, source_root)
    ) < events.index(("admit", "paper")) < events.index(
        ("campaign", variant_root)
    ) < events.index(("applied-exit", variant_root))
    assert [event[0] for event in events].count("prebuild") == 1
    assert [event[0] for event in events].count("checkout-enter") == 1
    assert events[-2:] == [
        ("applied-exit", variant_root),
        ("checkout-exit", variant_root),
    ]


def test_condition_gate_uses_exact_offline_fetchcontent_argv(monkeypatch):
    _assert_condition_gate_context(monkeypatch)


def test_condition_gate_context_cleans_up_on_body_exception(monkeypatch):
    source_root = Path("/shared/ccbench")
    variant_root = Path("/scratch/job-variant")
    fetchcontent_base = Path("/scratch/fetchcontent")
    expected_toolchain_manifest = {"fixture": "toolchain"}
    events = []

    @contextlib.contextmanager
    def checkout(pin_commit, *, base_dir):
        events.append((
            "checkout-enter", variant_root, Path(base_dir), pin_commit))
        try:
            yield os.fspath(variant_root)
        finally:
            events.append(("checkout-exit", variant_root))

    @contextlib.contextmanager
    def applied(_patch_path, pin_commit, *, ccbench_dir):
        events.append(("applied-enter", Path(ccbench_dir), pin_commit))
        try:
            yield None
        finally:
            events.append(("applied-exit", Path(ccbench_dir)))

    def prepare_masstree_fetchcontent(**kwargs):
        assert Path(kwargs["ccbench_dir"]) == variant_root
        assert Path(kwargs["fetchcontent_base_dir"]) == fetchcontent_base
        assert kwargs["masstree_source_dir"] == os.fspath(
            fetchcontent_base / "masstree-src")
        assert kwargs["mimalloc_source_dir"] == os.fspath(
            fetchcontent_base / "mimalloc-src")
        assert kwargs["googletest_source_dir"] == os.fspath(
            fetchcontent_base / "googletest-src")
        events.append(("prebuild", variant_root, fetchcontent_base))

    def capture(source, *, stock_root, configure_args):
        events.append(("capture", Path(source), Path(stock_root)))
        assert configure_args == (
            "-DCMAKE_PREFIX_PATH=/dependency",
            f"-DFETCHCONTENT_BASE_DIR={fetchcontent_base}",
            f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={fetchcontent_base}/masstree-src",
            f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={fetchcontent_base}/mimalloc-src",
            f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={fetchcontent_base}/googletest-src",
        )
        return object()

    def record(request, arm):
        payload = {
            "macro": request.macro,
            "arm": arm,
            "terminal_status": "green",
        }
        return A2.SimpleNamespace(
            macro=request.macro,
            arm=arm,
            reason_code="established",
            terminal_status="green",
            evidence={},
            canonical_json=lambda: json.dumps(payload),
        )

    def admit(supply_records, meaning_records, *, use_class):
        assert supply_records and meaning_records
        events.append(("admit", use_class))
        return A2.SimpleNamespace(
            admitted=True,
            canonical_json=lambda: json.dumps({"admitted": True}),
        )

    monkeypatch.setattr(A2.patchharness, "checkout", checkout)
    monkeypatch.setattr(A2.patchharness, "applied", applied)
    monkeypatch.setattr(
        A2.buildcache, "prepare_masstree_fetchcontent",
        prepare_masstree_fetchcontent)
    monkeypatch.setattr(
        A2.condition_meaning_gate, "capture_define_inputs", capture)
    monkeypatch.setattr(
        A2.condition_meaning_gate, "evaluate_define_supply_effectuation",
        lambda _captured, *, request, **_kwargs: record(request, "supply"))
    monkeypatch.setattr(
        A2.condition_meaning_gate, "evaluate_define_runtime_meaning",
        lambda _captured, *, request, **_kwargs: record(request, "meaning"))
    monkeypatch.setattr(
        A2.condition_meaning_gate, "require_condition_gate_family", admit)

    genome = A2.SimpleNamespace(
        flags={"BACKOFF_FIXED": 10, "BACKOFF_NOINLINE": 0})
    with pytest.raises(RuntimeError, match="campaign failed"):
        with _REAL_CONDITION_GATE_FAMILY(
                source_root, [genome], cxx="g++",
                dependency_prefix=Path("/dependency"),
                current_pin="abc1234",
                expected_toolchain_manifest=expected_toolchain_manifest,
                fetchcontent_base_dir=fetchcontent_base,
                staged_sources=_staged_sources(fetchcontent_base),
        ) as (observed_variant, receipts, canonical_records):
            assert observed_variant == variant_root
            assert len(receipts) == 1
            assert len(canonical_records) == 1
            events.append(("campaign", observed_variant))
            raise RuntimeError("campaign failed")

    assert events == [
        ("checkout-enter", variant_root, source_root, "abc1234"),
        ("applied-enter", variant_root, "abc1234"),
        ("prebuild", variant_root, fetchcontent_base),
        ("capture", variant_root, source_root),
        ("admit", "paper"),
        ("campaign", variant_root),
        ("applied-exit", variant_root),
        ("checkout-exit", variant_root),
    ]


def test_condition_gate_context_cleans_up_on_prebuild_exception(monkeypatch):
    source_root = Path("/shared/ccbench")
    variant_root = Path("/scratch/job-variant")
    fetchcontent_base = Path("/scratch/fetchcontent")
    events = []

    @contextlib.contextmanager
    def checkout(_pin_commit, *, base_dir):
        events.append(("checkout-enter", Path(base_dir)))
        try:
            yield os.fspath(variant_root)
        finally:
            events.append(("checkout-exit", variant_root))

    @contextlib.contextmanager
    def applied(_patch_path, _pin_commit, *, ccbench_dir):
        events.append(("applied-enter", Path(ccbench_dir)))
        try:
            yield None
        finally:
            events.append(("applied-exit", Path(ccbench_dir)))

    def fail_prebuild(**kwargs):
        events.append((
            "prebuild", Path(kwargs["ccbench_dir"]),
            Path(kwargs["fetchcontent_base_dir"]),
        ))
        raise RuntimeError("prebuild failed")

    monkeypatch.setattr(A2.patchharness, "checkout", checkout)
    monkeypatch.setattr(A2.patchharness, "applied", applied)
    monkeypatch.setattr(
        A2.buildcache, "prepare_masstree_fetchcontent", fail_prebuild)
    monkeypatch.setattr(
        A2.condition_meaning_gate, "capture_define_inputs",
        lambda *_args, **_kwargs: pytest.fail(
            "condition gate capture ran after prebuild failure"))

    genome = A2.SimpleNamespace(flags={"BACKOFF_FIXED": 10})
    with pytest.raises(RuntimeError, match="prebuild failed"):
        with _REAL_CONDITION_GATE_FAMILY(
                source_root, [genome], cxx="g++",
                dependency_prefix=Path("/dependency"),
                current_pin="abc1234",
                expected_toolchain_manifest={"fixture": "toolchain"},
                fetchcontent_base_dir=fetchcontent_base,
                staged_sources=_staged_sources(fetchcontent_base),
        ):
            pass

    assert events == [
        ("checkout-enter", source_root),
        ("applied-enter", variant_root),
        ("prebuild", variant_root, fetchcontent_base),
        ("applied-exit", variant_root),
        ("checkout-exit", variant_root),
    ]


def test_condition_gate_prebuild_runs_once_for_multiple_cells(monkeypatch):
    variant_root = Path("/scratch/job-variant")
    fetchcontent_base = Path("/scratch/fetchcontent")
    prebuild_calls = []

    monkeypatch.setattr(
        A2.patchharness, "checkout",
        lambda *_args, **_kwargs: contextlib.nullcontext(
            os.fspath(variant_root)))
    monkeypatch.setattr(
        A2.patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext())
    monkeypatch.setattr(
        A2.buildcache, "prepare_masstree_fetchcontent",
        lambda **kwargs: prebuild_calls.append(kwargs))
    monkeypatch.setattr(
        A2.condition_meaning_gate, "capture_define_inputs",
        lambda *_args, **_kwargs: object())

    def green_record(_captured, *, request, **_kwargs):
        payload = {
            "macro": request.macro,
            "terminal_status": "green",
        }
        return A2.SimpleNamespace(
            macro=request.macro,
            terminal_status="green",
            canonical_json=lambda: json.dumps(payload),
        )

    monkeypatch.setattr(
        A2.condition_meaning_gate,
        "evaluate_define_supply_effectuation", green_record)
    monkeypatch.setattr(
        A2.condition_meaning_gate,
        "evaluate_define_runtime_meaning", green_record)
    monkeypatch.setattr(
        A2.condition_meaning_gate, "require_condition_gate_family",
        lambda *_args, **_kwargs: A2.SimpleNamespace(
            admitted=True,
            canonical_json=lambda: json.dumps({"admitted": True}),
        ))

    genomes = [
        A2.SimpleNamespace(flags={"BACKOFF_FIXED": value})
        for value in (-1, 5, 10, 20)
    ]
    with _REAL_CONDITION_GATE_FAMILY(
            Path("/shared/ccbench"), genomes, cxx="g++",
            dependency_prefix=Path("/dependency"),
            current_pin="abc1234",
            expected_toolchain_manifest={"fixture": "toolchain"},
            fetchcontent_base_dir=fetchcontent_base,
            staged_sources=_staged_sources(fetchcontent_base),
    ) as (observed_variant, receipts, canonical_records):
        assert observed_variant == variant_root
        assert len(receipts) == len(genomes)
        assert len(canonical_records) == len(genomes)

    assert prebuild_calls == [{
        "ccbench_dir": os.fspath(variant_root),
        "fetchcontent_base_dir": os.fspath(fetchcontent_base),
        "masstree_source_dir": os.fspath(fetchcontent_base / "masstree-src"),
        "mimalloc_source_dir": os.fspath(fetchcontent_base / "mimalloc-src"),
        "googletest_source_dir": os.fspath(
            fetchcontent_base / "googletest-src"),
        "expected_toolchain_manifest": {"fixture": "toolchain"},
        "configure_timeout_s": 900,
        "target_timeout_s": 900,
        "dependency_prefix": "/dependency",
    }]


def _assert_condition_gate_rejection(monkeypatch):
    variant_root = Path("/scratch/job-variant")
    monkeypatch.setattr(
        A2.patchharness, "checkout",
        lambda *_args, **_kwargs: contextlib.nullcontext(
            os.fspath(variant_root)))
    monkeypatch.setattr(
        A2.patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext())
    monkeypatch.setattr(
        A2.buildcache, "prepare_masstree_fetchcontent",
        lambda **_kwargs: None)
    monkeypatch.setattr(
        A2.condition_meaning_gate, "capture_define_inputs",
        lambda *_args, **_kwargs: object())

    red = A2.SimpleNamespace(
        macro="BACKOFF_FIXED", arm="supply-effectuation",
        reason_code="configure-failed", terminal_status="red",
        evidence={"detail": "cmake emitted an unused-variable warning"},
    )
    green = A2.SimpleNamespace(
        macro="BACKOFF_FIXED", arm="runtime-meaning",
        reason_code="established", terminal_status="green", evidence={},
    )
    noinline_declaration = object()
    factory_calls = []

    def declare(request):
        factory_calls.append(request)
        return noinline_declaration \
            if request.macro == "BACKOFF_NOINLINE" else None

    def evaluate_meaning(_captured, *, request, declaration, **_kwargs):
        if request.macro == "BACKOFF_NOINLINE":
            assert declaration is noinline_declaration
        return green

    monkeypatch.setattr(
        A2.condition_meaning_gate, "declare_define_runtime_meaning", declare)
    monkeypatch.setattr(
        A2.condition_meaning_gate, "evaluate_define_supply_effectuation",
        lambda _captured, *, request, **_kwargs: (
            red if request.macro == "BACKOFF_FIXED" else green))
    monkeypatch.setattr(
        A2.condition_meaning_gate, "evaluate_define_runtime_meaning",
        evaluate_meaning)
    monkeypatch.setattr(
        A2.condition_meaning_gate, "require_condition_gate_family",
        lambda *_args, **_kwargs: A2.SimpleNamespace(admitted=False))

    genome = A2.SimpleNamespace(
        flags={"BACKOFF_FIXED": 10, "BACKOFF_NOINLINE": 0})
    with pytest.raises(A2.CertificationError) as error:
        with _REAL_CONDITION_GATE_FAMILY(
                Path("/shared/ccbench"), [genome], cxx="g++",
                dependency_prefix=Path("/dependency"),
                current_pin="abc1234",
                expected_toolchain_manifest={"fixture": "toolchain"},
                fetchcontent_base_dir=Path("/scratch/fetchcontent"),
                staged_sources=_staged_sources("/scratch/fetchcontent"),
        ):
            pass

    message = str(error.value)
    assert [
        (request.macro, request.requested_value, request.default_value)
        for request in factory_calls if request.macro == "BACKOFF_NOINLINE"
    ] == [("BACKOFF_NOINLINE", 0, 0)]
    assert "cmake emitted an unused-variable warning" in message
    assert (
        "BACKOFF_NOINLINE:runtime-meaning:meaning-witness-undeclared"
    ) not in message


def test_condition_gate_family_real_records_positive_then_issued_red_negative(
    monkeypatch,
):
    """Exercise a family/wiring negative, not a real configure failure."""
    import struct

    from orchestrator.campaign import condition_meaning_gate as G
    from orchestrator.tests import condition_gate_test_support as gate_support

    supplied = gate_support._FIXTURE_ROOT
    compilers = gate_support.condition_gate_compilers()
    if compilers is None:
        pytest.skip("condition gate test compilers are not installed")
    _cc, cxx = compilers
    cmake = "cmake"
    defaults = {"BACKOFF_FIXED": -1, "BACKOFF_NOINLINE": 0}
    real_family = G.require_condition_gate_family

    def request_for(index, macro, value):
        return G.make_define_request(
            driver_id=(
                "orchestrator.campaign.paper_story_a2_certification:"
                f"cell-{index}"
            ),
            macro=macro,
            requested_value=value,
            default_value=defaults[macro],
            stock_comparison=(macro == "BACKOFF_FIXED" and value == -1),
        )

    def declaration_for(request):
        macro = request.macro
        value = request.requested_value
        declaration = G.declare_define_runtime_meaning(request)
        if macro == "BACKOFF_FIXED" and value == -1:
            return G.MeaningWitnessDeclaration(
                macro,
                (G.MeaningCase(
                    -1,
                    None,
                    expected_selected_branch=G.STOCK_ADAPTIVE_BRANCH,
                ),),
            )
        if macro == "BACKOFF_FIXED" and value >= 0:
            bits = struct.pack(">d", float(value)).hex()
            return G.MeaningWitnessDeclaration(
                macro,
                (G.MeaningCase(value, (bits, bits)),),
            )
        return declaration

    captured = G.capture_define_inputs(
        supplied, stock_root=supplied / "stock",
    )
    positive_flags = (
        {"BACKOFF_FIXED": -1, "BACKOFF_NOINLINE": 0},
        {"BACKOFF_FIXED": 10, "BACKOFF_NOINLINE": 0},
    )
    expected_supply_outcomes = {
        (0, "BACKOFF_FIXED"): (
            "green", "stock-inert-preprocess-identical",
        ),
        (0, "BACKOFF_NOINLINE"): (
            "green", "stock-inert-preprocess-identical",
        ),
        (1, "BACKOFF_FIXED"): (
            "green", "requested-default-preprocess-different",
        ),
        (1, "BACKOFF_NOINLINE"): (
            "green", "stock-inert-preprocess-identical",
        ),
    }
    expected_meaning_outcomes = {
        (0, "BACKOFF_FIXED"): ("green", "declared-meaning-observed"),
        (0, "BACKOFF_NOINLINE"): (
            "green", "declared-compile-time-branch-selection-observed",
        ),
        (1, "BACKOFF_FIXED"): ("green", "declared-meaning-observed"),
        (1, "BACKOFF_NOINLINE"): (
            "green", "declared-compile-time-branch-selection-observed",
        ),
    }
    positive_cells = []
    positive_rows = []
    for index, flags in enumerate(positive_flags):
        cell_supply = []
        cell_meaning = []
        for macro in sorted(set(flags) & set(defaults)):
            value = flags[macro]
            request = request_for(index, macro, value)
            declaration = declaration_for(request)
            supply = G.evaluate_define_supply_effectuation(
                captured, request=request, cxx=cxx, cmake=cmake,
            )
            meaning = G.evaluate_define_runtime_meaning(
                captured,
                request=request,
                declaration=declaration,
                cxx=cxx,
                cmake=cmake,
            )
            assert type(supply) is G.ConditionArmRecord
            assert type(meaning) is G.ConditionArmRecord
            G._validate_arm_record_integrity(supply)
            G._validate_arm_record_integrity(meaning)
            assert (supply.terminal_status, supply.reason_code) \
                == expected_supply_outcomes[(index, macro)]
            assert (meaning.terminal_status, meaning.reason_code) \
                == expected_meaning_outcomes[(index, macro)]
            positive_rows.append((
                index, macro, request, declaration, supply, meaning,
            ))
            cell_supply.append(supply)
            cell_meaning.append(meaning)
        admission = real_family(
            cell_supply, cell_meaning, use_class="paper",
        )
        assert admission.admitted is True
        assert admission.record_ids == tuple(
            record.record_id for record in (*cell_supply, *cell_meaning)
        )
        assert admission.unestablished_meaning_macros == ()
        positive_cells.append((cell_supply, cell_meaning, admission))

    negative_request = request_for(0, "BACKOFF_FIXED", 10)
    negative_declaration = declaration_for(negative_request)
    negative_meaning = G.evaluate_define_runtime_meaning(
        captured,
        request=negative_request,
        declaration=negative_declaration,
        cxx=cxx,
        cmake=cmake,
    )
    _spec, _requested, _default, companions = (
        G._validate_define_request(negative_request)
    )
    negative_supply = G._issue_arm_record(
        arm="supply-effectuation",
        terminal_status="red",
        reason_code="configure-failed",
        request=negative_request,
        request_digest=G._request_digest(negative_request, companions),
        evidence={
            "detail": "cmake emitted an unused-variable warning",
        },
    )
    assert type(negative_supply) is G.ConditionArmRecord
    assert type(negative_meaning) is G.ConditionArmRecord
    G._validate_arm_record_integrity(negative_supply)
    G._validate_arm_record_integrity(negative_meaning)
    assert (
        negative_meaning.terminal_status,
        negative_meaning.reason_code,
    ) == ("green", "declared-meaning-observed")

    source_root = supplied
    dependency_prefix = Path("/dependency")
    current_pin = "abc1234"
    expected_toolchain_manifest = {"fixture": "toolchain"}

    def install_leaf_stubs(label, expected_rows):
        variant_root = Path(f"/scratch/{label}-job-variant")
        fetchcontent_base = Path(f"/scratch/{label}-fetchcontent")
        calls = []
        supply_index = 0
        meaning_index = 0

        @contextlib.contextmanager
        def checkout(pin_commit, *, base_dir):
            assert pin_commit == current_pin
            assert base_dir == os.fspath(source_root)
            calls.append("checkout")
            yield os.fspath(variant_root)

        @contextlib.contextmanager
        def applied(patch_path, pin_commit, *, ccbench_dir):
            assert patch_path == os.fspath(
                Path(A2.__file__).resolve().parents[2]
                / "patches/silo-backoff-fixed.patch"
            )
            assert pin_commit == current_pin
            assert ccbench_dir == os.fspath(variant_root)
            calls.append("applied")
            yield None

        def prepare_masstree_fetchcontent(
            *,
            ccbench_dir,
            fetchcontent_base_dir,
            masstree_source_dir,
            mimalloc_source_dir,
            googletest_source_dir,
            expected_toolchain_manifest,
            configure_timeout_s,
            target_timeout_s,
            dependency_prefix,
        ):
            assert ccbench_dir == os.fspath(variant_root.resolve())
            assert fetchcontent_base_dir == os.fspath(fetchcontent_base)
            assert masstree_source_dir == os.fspath(
                fetchcontent_base / "masstree-src")
            assert mimalloc_source_dir == os.fspath(
                fetchcontent_base / "mimalloc-src")
            assert googletest_source_dir == os.fspath(
                fetchcontent_base / "googletest-src")
            assert expected_toolchain_manifest is expected_manifest
            assert configure_timeout_s == 900
            assert target_timeout_s == 900
            assert dependency_prefix == os.fspath(expected_dependency_prefix)
            calls.append("prebuild")

        def capture(source, *, stock_root, configure_args):
            assert source == variant_root
            assert stock_root == source_root
            assert configure_args == (
                f"-DCMAKE_PREFIX_PATH={expected_dependency_prefix}",
                f"-DFETCHCONTENT_BASE_DIR={fetchcontent_base}",
                f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={fetchcontent_base}/masstree-src",
                f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={fetchcontent_base}/mimalloc-src",
                f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={fetchcontent_base}/googletest-src",
            )
            calls.append("capture")
            return captured

        def evaluate_supply(_captured, *, request, cxx, cmake):
            nonlocal supply_index
            assert supply_index < len(expected_rows)
            index, macro, expected_request, _declaration, record, _meaning = (
                expected_rows[supply_index]
            )
            assert _captured is captured
            assert request == expected_request
            assert cxx == expected_cxx
            assert cmake == expected_cmake
            calls.append(f"supply:cell-{index}:{macro}")
            supply_index += 1
            return record

        def evaluate_meaning(
            _captured, *, request, declaration, cxx,
        ):
            nonlocal meaning_index
            assert meaning_index < len(expected_rows)
            index, macro, expected_request, expected_declaration, _supply, record = (
                expected_rows[meaning_index]
            )
            assert _captured is captured
            assert request == expected_request
            assert declaration == expected_declaration
            assert cxx == expected_cxx
            calls.append(f"meaning:cell-{index}:{macro}")
            meaning_index += 1
            return record

        expected_cxx = cxx
        expected_cmake = cmake
        expected_dependency_prefix = dependency_prefix
        expected_manifest = expected_toolchain_manifest
        monkeypatch.setattr(A2.patchharness, "checkout", checkout)
        monkeypatch.setattr(A2.patchharness, "applied", applied)
        monkeypatch.setattr(
            A2.buildcache,
            "prepare_masstree_fetchcontent",
            prepare_masstree_fetchcontent,
        )
        monkeypatch.setattr(
            A2.condition_meaning_gate, "capture_define_inputs", capture,
        )
        monkeypatch.setattr(
            A2.condition_meaning_gate,
            "evaluate_define_supply_effectuation",
            evaluate_supply,
        )
        monkeypatch.setattr(
            A2.condition_meaning_gate,
            "evaluate_define_runtime_meaning",
            evaluate_meaning,
        )
        return variant_root, calls

    positive_variant, positive_calls = install_leaf_stubs(
        "positive", positive_rows,
    )
    positive_genomes = [
        A2.SimpleNamespace(flags=dict(flags)) for flags in positive_flags
    ]
    with _REAL_CONDITION_GATE_FAMILY(
        source_root,
        positive_genomes,
        cxx=cxx,
        dependency_prefix=dependency_prefix,
        current_pin=current_pin,
        expected_toolchain_manifest=expected_toolchain_manifest,
        fetchcontent_base_dir=Path("/scratch/positive-fetchcontent"),
        staged_sources=_staged_sources("/scratch/positive-fetchcontent"),
    ) as (observed_variant, receipts, canonical_records):
        assert observed_variant == positive_variant
        assert len(receipts) == 2
        assert len(canonical_records) == 2
        for receipt, (supply, meaning, admission) in zip(
            receipts, positive_cells, strict=True,
        ):
            assert receipt == {
                "supply_records": [
                    json.loads(record.canonical_json()) for record in supply
                ],
                "meaning_records": [
                    json.loads(record.canonical_json()) for record in meaning
                ],
                "admission": json.loads(admission.canonical_json()),
            }
    assert positive_calls == [
        "checkout",
        "applied",
        "prebuild",
        "capture",
        "supply:cell-0:BACKOFF_FIXED",
        "meaning:cell-0:BACKOFF_FIXED",
        "supply:cell-0:BACKOFF_NOINLINE",
        "meaning:cell-0:BACKOFF_NOINLINE",
        "supply:cell-1:BACKOFF_FIXED",
        "meaning:cell-1:BACKOFF_FIXED",
        "supply:cell-1:BACKOFF_NOINLINE",
        "meaning:cell-1:BACKOFF_NOINLINE",
    ]

    negative_admission = real_family(
        [negative_supply], [negative_meaning], use_class="paper",
    )
    assert negative_admission.admitted is False
    negative_rows = [(
        0,
        "BACKOFF_FIXED",
        negative_request,
        negative_declaration,
        negative_supply,
        negative_meaning,
    )]
    _negative_variant, negative_calls = install_leaf_stubs(
        "negative", negative_rows,
    )
    negative_genome = A2.SimpleNamespace(flags={"BACKOFF_FIXED": 10})
    with pytest.raises(A2.CertificationError) as error:
        with _REAL_CONDITION_GATE_FAMILY(
            source_root,
            [negative_genome],
            cxx=cxx,
            dependency_prefix=dependency_prefix,
            current_pin=current_pin,
            expected_toolchain_manifest=expected_toolchain_manifest,
            fetchcontent_base_dir=Path("/scratch/negative-fetchcontent"),
            staged_sources=_staged_sources("/scratch/negative-fetchcontent"),
        ):
            pass
    message = str(error.value)
    assert (
        "BACKOFF_FIXED:supply-effectuation:configure-failed:"
        "detail='cmake emitted an unused-variable warning'"
    ) in message
    assert "BACKOFF_FIXED:runtime-meaning:" not in message
    assert negative_calls == [
        "checkout",
        "applied",
        "prebuild",
        "capture",
        "supply:cell-0:BACKOFF_FIXED",
        "meaning:cell-0:BACKOFF_FIXED",
    ]


from orchestrator.tests import commit_receipt_support as receipt_support


CURRENT_PIN = "1" * 40
REPO_CURRENT_PIN = pin.CURRENT_PIN
SOURCE_COMMIT = "2" * 40
QSTAT_VISIBILITY_FIXTURE = (
    Path(__file__).parent / "fixtures" / "paper_story_a2"
    / "qstat-visibility-945411.stdout"
)
QSTAT_FANOUT_VISIBILITY_FIXTURE = (
    Path(__file__).parent / "fixtures" / "paper_story_a2"
)
QSTAT_FANOUT_VISIBILITY_FIXTURES = {
    "rr5": QSTAT_FANOUT_VISIBILITY_FIXTURE
    / "qstat-visibility-fanout-945411.stdout",
    "rr50": QSTAT_FANOUT_VISIBILITY_FIXTURE
    / "qstat-visibility-fanout-945412.stdout",
}
NON_ACCEPTED_VISIBILITY_VOCABULARY = (
    ("Held", "outside the submission acceptance set"),
    ("Suspended", "state vocabulary is unknown"),
)
REAL_A6_20260908B_PREREGISTRATION = {
    "attempt_id": "a6-20260908b",
    "attempt_root": (
        "/work/1/SFC/tanab/izanagi-measurements/"
        "dev-wave-paper-story-a6-cert-20260902/a6-20260908b"
    ),
    "automatic_retry": False,
    "current_pin": "511c953",
    "policy_sha256": (
        "8969a7e4ee740a94ec12084c89ef88a37ebd255073cfb0122245113a295b87a8"
    ),
    "protocol_sha256": (
        "21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc"
    ),
    "schema_version": "paper-story-a2-preregistration/v1",
    "study": "paper-story-a6-certification",
}


def _policy(tmp_path):
    document = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    document["durable_measurement_base"] = str(tmp_path / "durable-a2")
    document["tracked_destination"] = (
        "output/insights/2026-09-07_t2364-paper-story-a2-certification")
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return A2.load_policy(path)


def _a6_policy(tmp_path):
    document = json.loads(A2.A6_POLICY_PATH.read_text(encoding="utf-8"))
    document["durable_measurement_base"] = str(tmp_path / "durable-a6")
    path = tmp_path / "a6-policy.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return A2.load_policy(path)


def test_real_a6_preregistration_literal_is_materialization_eligible(tmp_path):
    policy = _a6_policy(tmp_path)
    literal = copy.deepcopy(REAL_A6_20260908B_PREREGISTRATION)

    assert set(literal) == A2._PREREGISTRATION_KEYS
    assert literal["policy_sha256"] != policy.bytes_sha256
    assert A2._validate_materialization_preregistration(
        policy, literal,
        attempt_id="a6-20260908b",
        attempt_root=Path(
            "/work/1/SFC/tanab/izanagi-measurements/"
            "dev-wave-paper-story-a6-cert-20260902/a6-20260908b"
        ),
    ) == (
        "paper-story-a6-certification",
        "8969a7e4ee740a94ec12084c89ef88a37ebd255073cfb0122245113a295b87a8",
        "511c953",
    )

    written_root = A2.preregister_attempt(
        policy, "a6-writer-positive", CURRENT_PIN)
    written, _ = A2._read_json(written_root / "preregistration.json")
    assert written["automatic_retry"] is False
    assert A2._validate_materialization_preregistration(
        policy, written,
        attempt_id=written_root.name,
        attempt_root=written_root,
    ) == (
        policy.study,
        policy.bytes_sha256,
        CURRENT_PIN[:7],
    )


def _request_ids(policy):
    return {
        workload_id: f"{945411 + index}.nqsv"
        for index, workload_id in enumerate(A2.workload_ids(policy))
    }


def _submission_visibility(request_id):
    return (
        f"Request ID: {request_id}\n"
        "    Current State = Staging\n"
        "    Ended Request Time = (none)\n"
    )


def _campaign_cfg(mode):
    search = {} if mode is None else {"verify": mode}
    return CampaignConfig(
        spec_slug="a2-test", search_tag="a2-test", spec_content="a2",
        ccbench_commit=CURRENT_PIN, search_config=search,
    )


def _verify_wal_payload(tag, build_attempt_id):
    return {
        "build_attempt_id": build_attempt_id,
        "verdict": "serializable",
        "certified": True,
        "commit_witness": {
            "commit_counts": 11,
            "batch_commit_counts": 0,
        },
        "anomalies": 0,
        "workload": {"tag": tag},
    }


def _campaign_lock_text(policy, workload_id, attempt_id):
    expected = A2.campaign_preimage(
        policy, workload_id, attempt_id, CURRENT_PIN)
    observed = {
        **expected,
        ident.ADMISSION_POLICY_SEARCH_KEY: build_admission.build_run_context(
            generator_id=build_admission.GeneratorId.BACKOFF_REPRO,
        ).policy.as_preimage(),
    }
    identity = {
        "spec_content": A2._canonical_json(expected).decode("ascii"),
        "ccbench_commit": CURRENT_PIN,
        "search_tag": policy.study + "-" + workload_id,
        "search_config": observed,
        "trial": attempt_id,
    }
    identity_preimage = json.dumps(
        identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    authority = {
        "environment_contract_sha256": "a" * 64,
        "activation_serial": 1,
        "activation_state_sha256": "b" * 64,
        "contract_loader_commit": "c" * 40,
        "contract_loader_blob_sha256s": {
            path: "d" * 64
            for path in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
        },
    }
    return campaign_lock.encode_campaign_lock_v2(identity_preimage, authority)


def _positive_results(
        policy, attempt_root, *, adopted_gain=1.1,
        invalid_persisted_cell=None,
):
    results = []
    fetchcontent_base = attempt_root / "fetchcontent"
    fetchcontent_base.mkdir(exist_ok=True)
    staged_sources = _staged_sources(fetchcontent_base)
    for source in staged_sources.values():
        source.mkdir(exist_ok=True)
    contract = env_contract.lookup("pegasus")
    toolchain = {
        "cc": {
            "requested": "gcc", "realpath": "/usr/bin/gcc",
            "version_first_line": "gcc fixture",
        },
        "cxx": {
            "requested": "g++", "realpath": "/usr/bin/g++",
            "version_first_line": "g++ fixture",
        },
        "cmake": {
            "requested": "cmake", "realpath": "/usr/bin/cmake",
            "version_first_line": "cmake fixture",
        },
    }
    request_ids = _request_ids(policy)
    for workload_id in A2.workload_ids(policy):
        lock_text = _campaign_lock_text(
            policy, workload_id, attempt_root.name)
        identity = campaign_lock.decode_campaign_lock(lock_text).identity
        cfg = CampaignConfig(
            spec_slug="paper-story-a2-" + workload_id,
            search_tag=policy.study + "-" + workload_id,
            spec_content=identity["spec_content"],
            ccbench_commit=CURRENT_PIN,
            search_config=identity["search_config"],
            trial=attempt_root.name,
        )
        job_root = attempt_root / "jobs" / workload_id
        for child in (job_root, job_root / "campaigns", job_root / "cache",
                      job_root / "scheduler"):
            child.mkdir(parents=True, exist_ok=True)
        campaign_id = str(ident.campaign_id(cfg))
        layout_root = job_root / "campaigns" / campaign_id
        runs = layout_root / "runs"
        runs.mkdir(parents=True)
        layout = CampaignLayout(str(layout_root))
        (layout_root / "campaign.lock").write_text(
            lock_text,
            encoding="utf-8",
        )
        cells = [cell for cell in policy.cells if cell.workload_id == workload_id]
        source_evidences = []
        condition_admissions = []
        build_context = build_admission.build_run_context(
            generator_id=build_admission.GeneratorId.BACKOFF_REPRO)
        for cell_index, cell in enumerate(cells):
            build_dir = attempt_root / "build" / cell.cell_id
            binary = (
                build_dir / "cc" / "silo" / "ycsb_silo.exe")
            binary.parent.mkdir(parents=True)
            binary.write_bytes(("binary:" + cell.cell_id).encode("ascii"))
            perf_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
            trace_sha = hashlib.sha256(
                ("trace:" + cell.cell_id).encode("ascii")).hexdigest()
            configure, build = buildcache._v2_commands(
                A2._genome_for_cell(policy, cell), False, "/source",
                str(build_dir), toolchain, jobs=48,
                dependency_prefix="/pinned/dependencies",
                fetchcontent_base_dir=os.fspath(fetchcontent_base),
                masstree_source_dir=staged_sources["masstree"],
                mimalloc_source_dir=staged_sources["mimalloc"],
                googletest_source_dir=staged_sources["googletest"],
            )
            run_flags = [
                f"-thread_num={cell.perf['threads']}",
                f"-ycsb_tuple_num={cell.perf['records']}",
                f"-extime={cell.perf['extime']}",
                f"-clocks_per_us={contract.clocks_per_us}",
            ] + [
                f"-{key}={value}" for key, value in cell.perf["workload"].items()
            ]
            run = (
                list(contract.numactl)
                + ["perf", "stat", "-e", ",".join(PERF_EVENTS), "--", str(binary)]
                + run_flags
            )
            build_attempt_id = "build-" + cell.cell_id
            genome = A2._genome_for_cell(policy, cell)
            src_token = (
                source_digest.STOCK if cell.role == "stock"
                else hashlib.sha256(
                    ("patched-source:" + cell.cell_id).encode("ascii")
                ).hexdigest()
            )
            source_evidence = source_digest.SourceEvidence(
                source_digest.SOURCE_EVIDENCE_SCHEMA,
                str((attempt_root / "variant-source" / workload_id).resolve()),
                CURRENT_PIN,
                hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest(),
                src_token,
                hashlib.sha256(
                    ("source-bytes:" + cell.cell_id).encode("ascii")
                ).hexdigest(),
                False,
                hashlib.sha256(
                    ("tracked-diff:" + workload_id).encode("ascii")
                ).hexdigest(),
                ("include/backoff.hh",),
            )
            generator_receipt = build_admission.attest_generator_output(
                build_context, source_evidence,
                generator_input_sha256=A2._generator_input_sha256(
                    policy, workload_id, source_evidence.genome_sha256),
            )
            admission = build_admission.derive_build_admission(
                build_context, source_evidence,
                generator_receipt=generator_receipt)
            variant = variant_id(genome, src_token)
            source_evidences.append(source_evidence)
            condition_admissions.append(json.dumps({
                "admission_id": (
                    "condition-gate/admission/" + cell.cell_id),
                "admission_digest": hashlib.sha256(
                    ("condition-admission:" + cell.cell_id).encode("ascii")
                ).hexdigest(),
                "use_class": "paper",
                "admitted": True,
                "record_ids": ["condition-record/" + cell.cell_id],
                "unestablished_meaning_macros": [],
            }, sort_keys=True, separators=(",", ":")))
            value = 100.0 * (
                adopted_gain if cell.role == "adopted" else 1.0)
            samples = [value - 2, value - 1, value, value + 1, value + 2]
            payloads = [
                (STAGE_BUILD_START, {
                    "build_attempt_id": build_attempt_id,
                    "genome": genome.canonical(),
                    "src_token": src_token,
                    "build_admission": admission.as_wal_receipt(),
                    "build_admission_receipt_sha256": admission.receipt_sha256,
                }),
                (STAGE_BUILD_DONE, {
                    "build_attempt_id": build_attempt_id,
                    "trace_bin_sha256": trace_sha,
                    "perf_bin_sha256": perf_sha,
                    "perf_configure_cmd": " ".join(configure),
                    "perf_build_cmd": " ".join(build),
                    "toolchain": toolchain,
                }),
                (STAGE_VERIFY_DONE, _verify_wal_payload(
                    LEGACY_TAG, build_attempt_id)),
            ]
            payloads.extend(
                (STAGE_VERIFY_DONE, _verify_wal_payload(
                    PERFORMANCE_TAG, build_attempt_id))
                for _ in range(cell.perf["reps"])
            )
            payloads.extend([
                (STAGE_BENCH_DONE, {
                    "build_attempt_id": build_attempt_id,
                    "run_cmd": " ".join(run),
                    "tps": samples,
                    "unstable": False,
                    "rep_notes": [],
                }),
                (STAGE_COMMIT, {"build_attempt_id": build_attempt_id}),
            ])
            if cell.cell_id == invalid_persisted_cell:
                payloads[2][1]["anomalies"] = 1
            for offset, (stage, payload) in enumerate(payloads):
                timestamp = float(cell_index * 100 + offset + 1)
                if stage == STAGE_COMMIT:
                    receipt_support.log_receipted_commit(
                        layout, variant, "pegasus", payload,
                        operation_identity=build_attempt_id,
                        tags=(
                            LEGACY_TAG,
                            *([PERFORMANCE_TAG] * cell.perf["reps"]),
                        ),
                        ts=timestamp,
                    )
                else:
                    wal.log(
                        layout, variant, stage, "pegasus", payload,
                        ts=timestamp,
                    )
        wal_path = runs / "wal.jsonl"
        claim_path = A2.raw_result_claim_path(
            policy, workload_id, attempt_root, campaign_id)
        claim_path.parent.mkdir(parents=True, exist_ok=True)
        claim_path.write_text(json.dumps({
            "campaign_identity": campaign_id,
            "protocol_digest": hashlib.sha256(
                ident.canonical_preimage(cfg).encode("utf-8")
            ).hexdigest(),
            "job_id": request_ids[workload_id],
            "host": "bnode001",
            "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text(
                encoding="ascii").strip(),
            "pid": 123,
            "proc_starttime": 456,
            "created_utc": "2026-08-27T00:00:00+00:00",
        }, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        receipts_root = attempt_root / "receipts"
        receipts_root.mkdir(exist_ok=True)
        A2._write_condition_gate_admissions_x(
            attempt_root / A2._condition_gate_receipt_relative(workload_id),
            condition_admissions, source_evidences)
        for cell in cells:
            expected_src_token = next(
                evidence.src_token for evidence in source_evidences
                if evidence.genome_sha256 == hashlib.sha256(
                    A2._genome_for_cell(policy, cell).canonical().encode("utf-8")
                ).hexdigest()
            )
            results.append(A2._raw_cell_from_wal(
                policy, cell,
                result=type("Result", (), {
                    "variant": variant_id(
                        A2._genome_for_cell(policy, cell),
                        expected_src_token)})(),
                layout_root=str(layout_root), attempt_id=attempt_root.name,
                current_pin=CURRENT_PIN,
                expected_src_token=expected_src_token,
            ))
    return [
        next(raw for raw in results if raw["cell_id"] == cell.cell_id)
        for cell in policy.cells
    ]


def _raw_cell(policy, cell, root, *, adopted_gain=1.1):
    return next(
        raw for raw in _positive_results(
            policy, root, adopted_gain=adopted_gain)
        if raw["cell_id"] == cell.cell_id
    )


@pytest.mark.parametrize("consumer", ["a2"], ids=["a2"])
def test_raw_cell_requires_persisted_certification(tmp_path, consumer):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-persisted-certification")

    with pytest.raises(
            A2.CertificationError,
            match="persisted campaign certification is invalid"):
        _positive_results(
            policy, root, invalid_persisted_cell="rr5-stock",
        )

    assert consumer == "a2"


def _write_receipt_bundle(
        policy, attempt_root, *, driver_rc=0, claim_manifest=True,
        terminal_reason="scheduler-end-state", record_completion=True,
        adopted_gain=1.1, force_legacy_v3=False):
    results = _positive_results(
        policy, attempt_root, adopted_gain=adopted_gain)
    for workload_id in A2.workload_ids(policy):
        raw_root = A2.workload_job_root(policy, attempt_root, workload_id) / "raw"
        if not raw_root.exists():
            raw_root.mkdir()
            for result in results:
                if policy.cell(result["cell_id"]).workload_id == workload_id:
                    A2.write_json_x(
                        raw_root / f"{result['cell_id']}.json", result)
    log_record = lambda path: {
        "path": str(path),
        "size": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    repo_root = A2.POLICY_PATH.parents[2]
    job_body = repo_root / policy.document["scheduler"]["job_body"]
    started = int(time.time()) - 1
    request_ids = _request_ids(policy)
    submission_jobs = []
    completion_jobs = []
    if type(driver_rc) is dict:
        driver_rcs = dict(driver_rc)
    else:
        driver_rcs = dict.fromkeys(A2.workload_ids(policy), 0)
        driver_rcs[A2.workload_ids(policy)[0]] = driver_rc
    assert list(driver_rcs) == list(A2.workload_ids(policy))
    for workload_id in A2.workload_ids(policy):
        request_id = request_ids[workload_id]
        job_root = A2.workload_job_root(policy, attempt_root, workload_id)
        stdout_path = job_root / "scheduler" / "job.stdout"
        stderr_path = job_root / "scheduler" / "job.stderr"
        stdout_path.write_text("job output\n", encoding="utf-8")
        stderr_path.write_text(
            f"Request ID: {request_id}\nGroup Name: SFC\n"
            "Started Request Time: now\nEnded Request Time: later\nElapse: 1\n",
            encoding="utf-8",
        )
        qsub_environment = {
            "IZANAGI_A2_ATTEMPT_ROOT": str(attempt_root),
            "IZANAGI_A2_WORKLOAD": workload_id,
            "IZANAGI_A2_EXPECTED_HEAD": SOURCE_COMMIT,
            "IZANAGI_A2_CURRENT_PIN": CURRENT_PIN,
            "IZANAGI_A2_CCBENCH_ROOT": "/pinned/ccbench",
            "IZANAGI_A2_REPO_ROOT": str(repo_root),
            "IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE": "/pinned/deps",
            "IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT": "/pinned/third-party",
        }
        if policy.study == "paper-story-a6-certification":
            qsub_environment["IZANAGI_A2_POLICY_PATH"] = str(policy.path)
        variable_arg = ",".join(
            f"{key}={value}" for key, value in qsub_environment.items())
        submission_jobs.append({
            "workload": workload_id,
            "qsub_argv": [
                "qsub", "-A", policy.document["scheduler"]["project"],
                "-q", policy.document["scheduler"]["queue"],
                "-b", str(policy.document["scheduler"]["nodes"]),
                "-l", f"elapstim_req={policy.document['scheduler']['walltime']}",
                "-N", A2._qsub_job_name(policy),
                "-v", variable_arg,
                "-o", str(stdout_path), "-e", str(stderr_path),
                str(job_body),
            ],
            "qsub_stdout": f"Request {request_id} submitted\n",
            "qsub_stderr": "",
            "qsub_returncode": 0,
            "request_id": request_id,
            "qstat_visibility": {
                "observed": True,
                "observed_at_utc": "2026-08-25T00:00:00Z",
                "request_id": request_id,
                "argv": ["qstat", "-f", request_id],
                "returncode": 0,
                "state": "QUE",
                "stdout": (
                    QSTAT_FANOUT_VISIBILITY_FIXTURES[workload_id].read_text(
                        encoding="utf-8")
                    if workload_id in QSTAT_FANOUT_VISIBILITY_FIXTURES
                    else _submission_visibility(request_id)
                ),
                "stderr": "",
            },
            "qsub_environment": qsub_environment,
        })
        allocation_stdout = job_root / "scheduler" / "allocation-qstat.stdout"
        allocation_stderr = job_root / "scheduler" / "allocation-qstat.stderr"
        walltime_hours, walltime_minutes, walltime_seconds = (
            int(part) for part in policy.document["scheduler"]["walltime"].split(":"))
        requested_seconds = (
            walltime_hours * 3600 + walltime_minutes * 60 + walltime_seconds)
        allocation_stdout.write_text(
            f"Request ID: {request_id}\nStarted Request Time = now\n"
            f"(Per-Req) Elapse Time Limit = Max: {requested_seconds}S\n",
            encoding="utf-8",
        )
        allocation_stderr.write_text("", encoding="utf-8")
        reservation_environment = {
            "IZANAGI_RESERVATION_JOB_ID": request_id,
            "IZANAGI_RESERVATION_REQUESTED_S": str(requested_seconds),
            "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": str(started),
            "IZANAGI_RESERVATION_DEADLINE_EPOCH": str(started + requested_seconds),
            "IZANAGI_RESERVATION_HOST": "bnode001",
            "IZANAGI_RESERVATION_BOOT_ID": Path(
                "/proc/sys/kernel/random/boot_id").read_text(
                    encoding="ascii").strip(),
            "IZANAGI_RESERVATION_SCRIPT_SHA256": hashlib.sha256(
                job_body.read_bytes()).hexdigest(),
            "IZANAGI_RESERVATION_NONCE": request_id,
        }
        reservation_result = job_root / "reservation.json"
        A2.write_json_x(reservation_result, {
            "schema_version": A2.RESERVATION_RESULT_SCHEMA,
            "environment": reservation_environment,
            "allocation_qstat_stdout": log_record(allocation_stdout),
            "allocation_qstat_stderr": log_record(allocation_stderr),
        })
        compute_result = job_root / "compute-result.json"
        A2.write_json_x(compute_result, {
            "schema_version": A2.COMPUTE_RESULT_SCHEMA,
            "workload": workload_id,
            "driver_rc": driver_rcs[workload_id],
            "pbs_jobid": request_id,
            "current_pin": CURRENT_PIN,
        })
        terminal_stdout = (
            f"Request ID: {request_id}\nRequest State = EXT\n"
            if terminal_reason == "scheduler-end-state"
            else f"Batch Request: {request_id} does not exist on nqsv.\n"
        )
        completion_jobs.append({
            "workload": workload_id,
            "request_id": request_id,
            "terminal_observation": {
                "observed": True,
                "request_id": request_id,
                "argv": ["qstat", "-f", request_id],
                "returncode": 0,
                "state": "END",
                "stdout": terminal_stdout,
                "stderr": "",
                "reason": terminal_reason,
            },
            "driver_rc": driver_rcs[workload_id],
            "compute_result": str(compute_result),
            "compute_result_sha256": hashlib.sha256(
                compute_result.read_bytes()).hexdigest(),
            "reservation_result": str(reservation_result),
            "reservation_result_sha256": hashlib.sha256(
                reservation_result.read_bytes()).hexdigest(),
            "scheduler_stdout": log_record(stdout_path),
            "scheduler_stderr": log_record(stderr_path),
        })
    submission = {
        "schema_version": A2.SUBMISSION_SCHEMA,
        "route": "direct-qsub",
        "study": policy.study,
        "protocol_sha256": policy.protocol_sha256,
        "attempt_id": attempt_root.name,
        "attempt_root": str(attempt_root),
        "source_commit": SOURCE_COMMIT,
        "current_pin": CURRENT_PIN,
        "submit_host": socket.gethostname(),
        "submission_cwd": str(repo_root),
        "job_body_sha256": hashlib.sha256(job_body.read_bytes()).hexdigest(),
        "jobs": submission_jobs,
    }
    A2.record_submission_receipt(
        policy, attempt_root, CURRENT_PIN, submission)
    if not record_completion:
        return None, submission
    successful_workloads = [
        workload for workload, value in driver_rcs.items() if value == 0]
    completion_schema = A2.COMPLETION_SCHEMA
    manifest_path = None
    if (len(successful_workloads) == len(A2.workload_ids(policy))
            and claim_manifest):
        manifest_path = A2.finalize_raw_manifest(
            policy, attempt_root, CURRENT_PIN)
    elif (len(A2.workload_ids(policy)) == 2
          and len(successful_workloads) == 1
          and not force_legacy_v3):
        completion_schema = A2.PARTIAL_COMPLETION_SCHEMA
        if claim_manifest:
            manifest_path = A2._finalize_partial_raw_manifest(
                policy, attempt_root, CURRENT_PIN, successful_workloads[0])
    completion = {
        "schema_version": completion_schema,
        "study": policy.study,
        "protocol_sha256": policy.protocol_sha256,
        "attempt_id": attempt_root.name,
        "attempt_root": str(attempt_root),
        "source_commit": SOURCE_COMMIT,
        "current_pin": CURRENT_PIN,
        "jobs": completion_jobs,
        "raw_result_manifest": (
            str(manifest_path) if manifest_path is not None else None),
        "raw_result_manifest_sha256": (
            hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            if manifest_path is not None else None),
    }
    if completion_schema == A2.PARTIAL_COMPLETION_SCHEMA:
        completion["successful_workload"] = successful_workloads[0]
    A2.record_completion_receipt(
        policy, attempt_root, CURRENT_PIN, completion)
    acquisition_path = A2.record_acquisition_receipt(
        policy, attempt_root, CURRENT_PIN)
    return acquisition_path, submission


def _rewrite_first_cell_science_from_wal(
        policy, attempt_root, workload_id, *, outcome):
    assert outcome in {"anomaly", "inconclusive"}
    cells = [
        cell for cell in policy.cells if cell.workload_id == workload_id]
    target = cells[0]
    target_raw_path = (
        attempt_root / "jobs" / workload_id / "raw"
        / f"{target.cell_id}.json")
    target_raw, _ = A2._read_json(target_raw_path)
    wal_path = Path(target_raw["campaign_evidence"]["wal_path"])
    records = [
        wal.parse_line(frame.decode("utf-8"))
        for frame in wal_path.read_bytes().splitlines(keepends=True)
    ]
    target_variant = variant_id(
        A2._genome_for_cell(policy, target), target_raw["src_token"])
    rewritten = []
    mutation_written = False
    target_build_attempt = None
    replacement_commit = None
    for record in records:
        if record.variant != target_variant:
            rewritten.append(record)
            continue
        if (outcome == "inconclusive"
                and record.stage == STAGE_VERIFY_DONE
                and record.payload.get("workload", {}).get("tag")
                == PERFORMANCE_TAG and not mutation_written):
            mutation_written = True
            continue
        if outcome == "inconclusive" and record.stage == STAGE_COMMIT:
            replacement_commit = record
            continue
        if outcome == "inconclusive":
            rewritten.append(record)
        elif record.stage == STAGE_BUILD_START:
            target_build_attempt = record.payload["build_attempt_id"]
            rewritten.append(record)
        elif record.stage == STAGE_BUILD_DONE:
            rewritten.append(record)
        elif (record.stage == STAGE_VERIFY_DONE
              and record.payload.get("workload", {}).get("tag") == LEGACY_TAG):
            rewritten.append(record)
        elif (record.stage == STAGE_VERIFY_DONE
              and record.payload.get("workload", {}).get("tag")
              == PERFORMANCE_TAG and not mutation_written):
            rewritten.append(WalRecord(
                variant=record.variant,
                stage=record.stage,
                env_tag=record.env_tag,
                ts=record.ts,
                payload={
                    **record.payload,
                    "certified": False,
                    "verdict": "non-serializable",
                    "anomalies": 1,
                },
            ))
            rewritten.append(WalRecord(
                variant=record.variant,
                stage=STAGE_ABORT,
                env_tag=record.env_tag,
                ts=record.ts + 0.01,
                payload={
                    "build_attempt_id": target_build_attempt,
                    "reason": "verifier-anomaly",
                    "verify": {
                        "anomalies": [{"cycle": ["rr50-a", "rr50-b"]}],
                    },
                },
            ))
            mutation_written = True
    assert mutation_written is True
    wal_path.write_text(
        "".join(wal._record_to_line(record) + "\n" for record in rewritten),
        encoding="utf-8",
    )
    layout_root = wal_path.parents[1]
    if outcome == "inconclusive":
        assert replacement_commit is not None
        terminal_payload = {
            key: value
            for key, value in replacement_commit.payload.items()
            if key != receipt_support.RECEIPT_PAYLOAD_KEY
        }
        evidence_tags = tuple(
            record.payload["workload"]["tag"]
            for record in rewritten
            if record.variant == target_variant
            and record.stage == STAGE_VERIFY_DONE
        )
        receipt_support.log_receipted_commit(
            CampaignLayout(str(layout_root)),
            replacement_commit.variant,
            replacement_commit.env_tag,
            terminal_payload,
            operation_identity=terminal_payload["build_attempt_id"],
            tags=evidence_tags,
            ts=replacement_commit.ts,
        )
    regenerated = []
    for cell in cells:
        existing, _ = A2._read_json(
            attempt_root / "jobs" / workload_id / "raw"
            / f"{cell.cell_id}.json")
        expected_src_token = existing["src_token"]
        raw = A2._raw_cell_from_wal(
            policy, cell,
            result=type("Result", (), {
                "variant": variant_id(
                    A2._genome_for_cell(policy, cell),
                    expected_src_token)})(),
            layout_root=str(layout_root), attempt_id=attempt_root.name,
            current_pin=CURRENT_PIN,
            expected_src_token=expected_src_token,
        )
        path = (
            attempt_root / "jobs" / workload_id / "raw"
            / f"{cell.cell_id}.json")
        path.write_bytes(A2._canonical_json(raw))
        regenerated.append(raw)
    assert regenerated[0]["terminal"] == (
        "abort" if outcome == "anomaly" else "commit")
    return regenerated


def _make_first_cell_anomalous_from_wal(policy, attempt_root, workload_id):
    return _rewrite_first_cell_science_from_wal(
        policy, attempt_root, workload_id, outcome="anomaly")


def _make_first_cell_inconclusive_from_wal(policy, attempt_root, workload_id):
    return _rewrite_first_cell_science_from_wal(
        policy, attempt_root, workload_id, outcome="inconclusive")


def _reseal_partial_receipts_after_manifest_mutation(attempt_root):
    manifest = attempt_root / "raw-manifest.json"
    completion_path = attempt_root / "receipts" / "completion.json"
    completion, _ = A2._read_json(completion_path)
    completion["raw_result_manifest_sha256"] = hashlib.sha256(
        manifest.read_bytes()).hexdigest()
    completion_path.write_bytes(A2._canonical_json(completion))
    acquisition_path = attempt_root / "receipts" / "acquisition.json"
    acquisition, _ = A2._read_json(acquisition_path)
    acquisition["completion_receipt_sha256"] = hashlib.sha256(
        completion_path.read_bytes()).hexdigest()
    acquisition_path.write_bytes(A2._canonical_json(acquisition))


def _reseal_manifest_member_and_receipts(attempt_root, relative):
    manifest_path = attempt_root / "raw-manifest.json"
    manifest, _ = A2._read_json(manifest_path)
    member_path = attempt_root / relative
    manifest["files"][relative] = hashlib.sha256(
        member_path.read_bytes()).hexdigest()
    manifest_path.write_bytes(A2._canonical_json(manifest))
    _reseal_partial_receipts_after_manifest_mutation(attempt_root)


def test_policy_is_the_exact_literal_four_cell_protocol(tmp_path):
    policy = _policy(tmp_path)
    assert policy.document["performance_common"]["ccbench_protocol"] == "silo"
    assert [(cell.cell_id, cell.workload_id, cell.role, dict(cell.genome))
            for cell in policy.cells] == [
        ("rr5-stock", "rr5", "stock", {"BACK_OFF": 0, "BACKOFF_FIXED": -1}),
        ("rr5-fixed10", "rr5", "adopted", {"BACK_OFF": 1, "BACKOFF_FIXED": 10}),
        ("rr50-stock", "rr50", "stock", {"BACK_OFF": 0, "BACKOFF_FIXED": -1}),
        ("rr50-fixed5", "rr50", "adopted", {"BACK_OFF": 1, "BACKOFF_FIXED": 5}),
    ]
    assert policy.cells[0].perf == {
        "records": 1_000_000,
        "threads": 48,
        "workload": {
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "5",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        },
        "extime": 3,
        "reps": 5,
    }
    assert policy.document["historical_reference"]["ccbench_commit"] == "6656e93"
    assert "never a current comparison value" in \
        policy.document["historical_reference"]["role"]
    assert policy.document["controlled_define_base"] == {
        "CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION": "1",
        "CCBENCH_NO_WAIT_OF_TICTOC": "0",
        "CCBENCH_WAL": "0",
        "CCBENCH_BACKOFF_NOINLINE": "0",
        "CCBENCH_TRACE": "0",
    }
    assert policy.document["trace0_cmake_argv"] == {
        "configure": {
            "source_option": "-S",
            "build_directory_option": "-B",
            "fixed_arguments": [
                "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
            ],
            "toolchain_arguments": [
                {"role": "cc", "prefix": "-DCMAKE_C_COMPILER="},
                {"role": "cxx", "prefix": "-DCMAKE_CXX_COMPILER="},
            ],
            "dependency_prefix_argument": "-DCMAKE_PREFIX_PATH=",
            "fetchcontent_path_argument_prefixes": [
                "-DFETCHCONTENT_BASE_DIR=",
                "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=",
                "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
                "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=",
            ],
            "controlled_define_argument": "-D",
        },
        "build": {
            "subcommand": "--build",
            "target_option": "--target",
            "target_prefix": "ycsb_",
            "target_suffix": ".exe",
            "jobs_option": "-j",
        },
    }
    assert policy.document["certification_composition"] == {
        "campaign_unit": (
            "one independently environment-contracted campaign per workload"),
        "outer_certification": "logical conjunction in policy workload order",
    }
    original = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    changed = copy.deepcopy(original)
    changed["certification_composition"]["outer_certification"] += " changed"
    original_sha = hashlib.sha256(
        A2._canonical_json(A2._protocol_preimage(original))).hexdigest()
    changed_sha = hashlib.sha256(
        A2._canonical_json(A2._protocol_preimage(changed))).hexdigest()
    assert original_sha != changed_sha
    decorative_original = dict(A2._protocol_preimage(original))
    decorative_changed = dict(A2._protocol_preimage(changed))
    decorative_original.pop("certification_composition")
    decorative_changed.pop("certification_composition")
    assert hashlib.sha256(A2._canonical_json(decorative_original)).hexdigest() == \
        hashlib.sha256(A2._canonical_json(decorative_changed)).hexdigest()


def test_p1_a2_default_policy_bytes_and_protocol_are_unchanged():
    raw = A2.POLICY_PATH.read_bytes()
    policy = A2.load_policy()

    assert hashlib.sha256(raw).hexdigest() == (
        "f8a7780600766e6c8e0248ae0e3aff70a2e1c28150f8932842cdbf67f988472c")
    assert policy.bytes_sha256 == (
        "f8a7780600766e6c8e0248ae0e3aff70a2e1c28150f8932842cdbf67f988472c")
    assert policy.protocol_sha256 == (
        "d99f08bcc50c605d24d443d387a2c3144c16b9e670c9b9e247227c5db1be7f9c")
    assert policy.raw_bytes == raw
    assert policy.document["scheduler"]["nodes"] == 5
    single_node = copy.deepcopy(policy.document)
    single_node["scheduler"]["nodes"] = 1
    assert A2._protocol_preimage(single_node) == A2._protocol_preimage(
        policy.document)
    assert A2.workload_ids(policy) == ("rr5", "rr50")
    assert A2._qsub_job_name(policy) == "paper-a2-cert"
    assert A2._qsub_environment_keys(policy) == A2._QSUB_ENV_KEYS


@pytest.mark.parametrize(
    ("mutation", "value"),
    (
        ("not-list", {"prefix": "-DFETCHCONTENT_BASE_DIR="}),
        ("wrong-length", [
            "-DFETCHCONTENT_BASE_DIR=",
            "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=",
            "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
        ]),
        pytest.param(
            "length-five-with-one-duplicate",
            [
                "-DFETCHCONTENT_BASE_DIR=",
                "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=",
                "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
                "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=",
                "-DFETCHCONTENT_BASE_DIR=",
            ],
            id="length-five-with-one-duplicate",
        ),
        ("non-string", [
            "-DFETCHCONTENT_BASE_DIR=",
            "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=",
            "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
            7,
        ]),
        ("empty", [
            "-DFETCHCONTENT_BASE_DIR=",
            "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=",
            "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
            "",
        ]),
        ("whitespace", [
            "-DFETCHCONTENT_BASE_DIR=",
            "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=",
            "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
            "-DFETCHCONTENT SOURCE_DIR_GOOGLETEST=",
        ]),
        ("missing-equals", [
            "-DFETCHCONTENT_BASE_DIR=",
            "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=",
            "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
            "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST",
        ]),
        ("duplicate", [
            "-DFETCHCONTENT_BASE_DIR=",
            "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=",
            "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
            "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
        ]),
    ),
)
def test_policy_loader_rejects_each_malformed_fetchcontent_prefix_list(
        tmp_path, mutation, value):
    document = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    document["trace0_cmake_argv"]["configure"][
        "fetchcontent_path_argument_prefixes"
    ] = value
    path = tmp_path / f"malformed-fetchcontent-prefix-{mutation}.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(A2.CertificationError, match="FetchContent path grammar"):
        A2.load_policy(path)


def test_m3_combined_count_layers_reject_three_workload_a6_policy(tmp_path):
    document = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    document["study"] = "paper-story-a6-certification"
    document["workloads"].append({
        "id": "rr95", "label": "read-heavy", "rratio": "95",
        "adopted_backoff_us": 2,
    })
    document["cells"].extend([
        {
            "id": "rr95-stock", "workload": "rr95", "role": "stock",
            "genome": {"BACK_OFF": 0, "BACKOFF_FIXED": -1},
        },
        {
            "id": "rr95-fixed2", "workload": "rr95", "role": "adopted",
            "genome": {"BACK_OFF": 1, "BACKOFF_FIXED": 2},
        },
    ])
    path = tmp_path / "three-workload-a6.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(A2.CertificationError, match="study shape"):
        A2.load_policy(path)


def test_policy_loader_rejects_unknown_study(tmp_path):
    document = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    document["study"] = "paper-story-unknown-certification"
    path = tmp_path / "unknown-study.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(A2.CertificationError, match="not a shipped certification study"):
        A2.load_policy(path)


def test_m4_cli_policy_selection_rejects_noncanonical_path(tmp_path):
    path = tmp_path / "valid-but-unshipped-a6.json"
    path.write_bytes(A2.A6_POLICY_PATH.read_bytes())
    args = type("Args", (), {"policy": str(path)})()

    with pytest.raises(A2.CertificationError, match="canonical shipped policy"):
        A2._load_selected_policy(args)
    exact_args = type("ExactArgs", (), {
        "policy": str(path), "qsub_argv": ["--", "qsub"],
    })()
    with pytest.raises(A2.CertificationError, match="canonical shipped policy"):
        A2._exact_qsub_command(exact_args)


def test_m5_workloads_remain_in_protocol_preimage():
    original = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    changed = copy.deepcopy(original)
    changed["workloads"][0]["label"] = "changed-only-in-workloads"

    original_sha = hashlib.sha256(
        A2._canonical_json(A2._protocol_preimage(original))).hexdigest()
    changed_sha = hashlib.sha256(
        A2._canonical_json(A2._protocol_preimage(changed))).hexdigest()
    assert original_sha != changed_sha


def test_a6_policy_is_exact_read_heavy_pair_with_twelve_hour_walltime():
    policy = A2.load_policy(A2.A6_POLICY_PATH)

    assert A2.workload_ids(policy) == ("rr95",)
    assert [(cell.cell_id, cell.role, dict(cell.genome)) for cell in policy.cells] == [
        ("rr95-stock", "stock", {"BACK_OFF": 0, "BACKOFF_FIXED": -1}),
        ("rr95-fixed2", "adopted", {"BACK_OFF": 1, "BACKOFF_FIXED": 2}),
    ]
    assert policy.document["scheduler"] == {
        "project": "SFC", "queue": "gen_S", "nodes": 5,
        "walltime": "12:00:00",
        "job_body": "tools/pegasus/paper_story_a2_certification.sh",
    }
    assert policy.document["trace0_cmake_argv"] == {
        "configure": {
            "source_option": "-S",
            "build_directory_option": "-B",
            "fixed_arguments": [
                "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
            ],
            "toolchain_arguments": [
                {"role": "cc", "prefix": "-DCMAKE_C_COMPILER="},
                {"role": "cxx", "prefix": "-DCMAKE_CXX_COMPILER="},
            ],
            "dependency_prefix_argument": "-DCMAKE_PREFIX_PATH=",
            "fetchcontent_path_argument_prefixes": [
                "-DFETCHCONTENT_BASE_DIR=",
                "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=",
                "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
                "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=",
            ],
            "controlled_define_argument": "-D",
        },
        "build": {
            "subcommand": "--build",
            "target_option": "--target",
            "target_prefix": "ycsb_",
            "target_suffix": ".exe",
            "jobs_option": "-j",
        },
    }
    assert policy.bytes_sha256 == (
        "682e0f4ed980b74d509426d8f074f51f5b8062a1ca7cf82cd8dbbaae93c4446a")
    assert policy.protocol_sha256 == (
        "21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc")


def test_a6_scheduler_fanout_changes_policy_bytes_but_not_protocol_preimage():
    policy = A2.load_policy(A2.A6_POLICY_PATH)
    previous_scheduler = copy.deepcopy(policy.document)
    previous_scheduler["scheduler"]["nodes"] = 1

    assert policy.bytes_sha256 == hashlib.sha256(
        A2.A6_POLICY_PATH.read_bytes()).hexdigest()
    assert policy.bytes_sha256 != (
        "96ed47d0ea72811aa8ee8ced6740fa58c5896e026cb24fa4420a31919d12384a")
    assert hashlib.sha256(A2._canonical_json(
        A2._protocol_preimage(previous_scheduler))).hexdigest() == (
            policy.protocol_sha256)


def test_verify_fanout_hosts_accept_exact_policy_counts():
    a2 = A2.load_policy(A2.POLICY_PATH)
    a6 = A2.load_policy(A2.A6_POLICY_PATH)
    hosts = ("bnode002", "bnode003", "bnode004", "bnode005")

    assert A2._validate_verify_fanout_hosts(
        a2, hosts, current_host="bnode001") == hosts
    assert A2._validate_verify_fanout_hosts(
        a6, hosts, current_host="bnode001") == hosts


@pytest.mark.parametrize(
    ("hosts", "message"),
    (
        (("bnode002", "bnode002", "bnode004", "bnode005"), "duplicate"),
        (("bnode001", "bnode003", "bnode004", "bnode005"), "current host"),
        (("bnode002", "bnode003", "bnode004"), "count differs"),
        ((), "count differs"),
        (("bnode002", "bnode003", "bnode004", "bnode005", "bnode006"),
         "count differs"),
        (("bnode002", "bad_host", "bnode004", "bnode005"), "malformed"),
    ),
    ids=("duplicate", "head", "too-few", "empty", "too-many", "malformed"),
)
@pytest.mark.parametrize("policy_path", (A2.POLICY_PATH, A2.A6_POLICY_PATH),
                         ids=("a2", "a6"))
def test_verify_fanout_hosts_reject_invalid_binding(policy_path, hosts, message):
    policy = A2.load_policy(policy_path)

    with pytest.raises(A2.CertificationError, match=message):
        A2._validate_verify_fanout_hosts(
            policy, hosts, current_host="bnode001")


def test_single_node_policy_rejects_any_verify_fanout_host(tmp_path):
    document = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    document["scheduler"]["nodes"] = 1
    path = tmp_path / "single-node-policy.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    policy = A2.load_policy(path)
    assert A2._validate_verify_fanout_hosts(
        policy, (), current_host="bnode001") == ()

    with pytest.raises(A2.CertificationError, match="count differs"):
        A2._validate_verify_fanout_hosts(
            policy, ("bnode002",), current_host="bnode001")


def test_production_policy_protocol_maps_to_real_silo_layout_and_artifacts(
        tmp_path):
    policy = A2.load_policy()
    genome = A2._genome_for_cell(policy, policy.cells[0])
    repo_root = A2.POLICY_PATH.parents[2]
    ccbench_root = repo_root / "external" / "ccbench"
    source_relative = Path(
        buildcache.source_digest._protocol_cmake_rel(genome.protocol))
    protocol_source = ccbench_root / source_relative

    assert genome.protocol == "silo"
    assert source_relative == Path("cc/silo/CMakeLists.txt")
    assert protocol_source.is_file()
    assert "ccbench_add_protocol(silo" in protocol_source.read_text(
        encoding="utf-8")

    build_dir = tmp_path / "build"
    toolchain = {
        "cc": {"realpath": "/usr/bin/gcc"},
        "cxx": {"realpath": "/usr/bin/g++"},
        "cmake": {"realpath": "/usr/bin/cmake"},
    }
    _configure, build = buildcache._v2_commands(
        genome, False, str(ccbench_root), str(build_dir), toolchain, jobs=48,
        dependency_prefix="/pinned/dependencies",
    )
    assert build == [
        "/usr/bin/cmake", "--build", str(build_dir),
        "--target", "ycsb_silo.exe", "-j", "48",
    ]
    assert build_dir / "cc" / genome.protocol / f"ycsb_{genome.protocol}.exe" \
        == build_dir / "cc" / "silo" / "ycsb_silo.exe"


def test_uppercase_silo_protocol_is_rejected_by_policy_loader(tmp_path):
    document = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    document["performance_common"]["ccbench_protocol"] = "SILO"
    path = tmp_path / "uppercase-policy.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(
            A2.CertificationError, match="must be exact lowercase silo"):
        A2.load_policy(path)


def test_m1_closed_verify_mode_wires_performance_and_rejects_unknown():
    perf = PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "5",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        }, extime=3, reps=5,
    )
    assert loop._closed_verify_workloads(_campaign_cfg(None), perf) is None
    assert loop._closed_verify_workloads(_campaign_cfg(LEGACY_TAG), perf) is None
    assert loop._closed_verify_workloads(
        _campaign_cfg(VERIFY_LEGACY_PLUS_S2), perf) == [
            ("s2", s2_correctness_workload())]
    matched = loop._closed_verify_workloads(
        _campaign_cfg(VERIFY_LEGACY_PLUS_PERFORMANCE), perf)
    assert matched == [(PERFORMANCE_TAG, performance_correctness_workload(perf))]
    with pytest.raises(ValueError, match="unsupported verify mode"):
        loop._closed_verify_workloads(_campaign_cfg("legacy+typo"), perf)
    source = inspect.getsource(loop.run_campaign)
    assert source.index("_closed_verify_workloads(cfg, perf)") \
        < source.index("_authorize_measurement(")


def test_m2_performance_constructor_is_exact_and_rejects_shrinkage():
    perf = PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "5",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        }, extime=3, reps=5,
    )
    assert performance_correctness_workload(perf).flags == {
        "ycsb_tuple_num": "1000000", "thread_num": "48",
        "ycsb_zipf_skew": "0.9", "ycsb_rratio": "5",
        "ycsb_rmw": "0", "ycsb_max_ope": "10", "extime": "3",
    }
    assert performance_correctness_workload(perf).reps == 5
    shrunk = copy.deepcopy(perf)
    shrunk.records = 200
    assert performance_correctness_workload(shrunk).flags["ycsb_tuple_num"] == "200"
    widened = copy.deepcopy(perf)
    widened.workload["ycsb_tuple_num"] = "200"
    with pytest.raises(ValueError, match="exact YCSB workload keys"):
        performance_correctness_workload(widened)


def test_m3_campaign_preimage_and_perfconfig_must_both_match(tmp_path):
    policy = _policy(tmp_path)
    cell = policy.cell("rr5-stock")
    expected = A2.campaign_preimage(policy, "rr5", "attempt-1", CURRENT_PIN)
    perf = A2.perf_config_for_cell(policy, cell.cell_id)
    A2.validate_campaign_binding(
        policy, "rr5", "attempt-1", CURRENT_PIN, expected, perf)
    changed_perf = copy.deepcopy(perf)
    changed_perf.records = 200
    with pytest.raises(A2.CertificationError, match="PerfConfig"):
        A2.validate_campaign_binding(
            policy, "rr5", "attempt-1", CURRENT_PIN, expected, changed_perf)


def test_m4_full_scale_verify_is_required_for_cell_completion(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m4")
    results = _positive_results(policy, root)
    results[0]["correctness"].pop(PERFORMANCE_TAG)
    report = A2.collect_results(
        policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_ids={"rr5": "123.nqsv", "rr50": "124.nqsv"},
        _test_token=A2._COLLECT_TEST_TOKEN)
    assert report["cells"][0]["correctness"]["status"] == "indeterminate"
    assert report["status"] == "indeterminate"


@pytest.mark.parametrize("mutation", ("missing", "extra", "duplicate", "cross-attempt"))
def test_m5_collector_rejects_non_exact_cell_sets(tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m5-" + mutation)
    results = _positive_results(policy, root)
    if mutation == "missing":
        results.pop()
    elif mutation == "extra":
        results[-1]["cell_id"] = "rr95-extra"
    elif mutation == "duplicate":
        results[-1] = copy.deepcopy(results[0])
    else:
        results[-1]["attempt_id"] = "another-attempt"
    with pytest.raises(A2.CertificationError):
        A2.collect_results(
            policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
            request_ids={"rr5": "123.nqsv", "rr50": "124.nqsv"})


def test_m6_positive_report_never_claims_global_minimality(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m6")
    report = A2.collect_results(
        policy, _positive_results(policy, root), attempt_id=root.name,
        current_pin=CURRENT_PIN,
        request_ids={"rr5": "123.nqsv", "rr50": "124.nqsv"})
    assert report["status"] == "observed-positive"
    assert report["global_minimality_established"] is False
    assert report["smallest_observed_sufficient_in_this_two_point_protocol"] is None


def test_anomaly_is_determinate_reject_and_performance_incomplete_is_not_pass(
        tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-classification")
    results = _positive_results(policy, root)
    anomaly = results[0]
    anomaly["correctness"][PERFORMANCE_TAG][0] = {
        **anomaly["correctness"][PERFORMANCE_TAG][0],
        "status": "anomaly",
        "certified": False,
        "verdict": "non-serializable",
        "anomalies": [{"cycle": ["t1", "t2"]}],
    }
    anomaly["correctness"][PERFORMANCE_TAG] = [
        anomaly["correctness"][PERFORMANCE_TAG][0]]
    anomaly["trace0_evidence"] = None
    anomaly["performance"] = {
        "status": "indeterminate", "reason": "verify-reject"}
    results[1]["correctness"].pop(PERFORMANCE_TAG)
    report = A2.collect_results(
        policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_ids={"rr5": "123.nqsv", "rr50": "124.nqsv"},
        _test_token=A2._COLLECT_TEST_TOKEN)
    assert report["status"] == "reject"
    assert A2.driver_rc(report) == 0

    root2 = A2.create_attempt_root(policy, "attempt-perf-incomplete")
    results2 = _positive_results(policy, root2)
    results2[0]["performance"]["samples_tps"].pop()
    report2 = A2.collect_results(
        policy, results2, attempt_id=root2.name, current_pin=CURRENT_PIN,
        request_ids={"rr5": "124.nqsv", "rr50": "125.nqsv"},
        _test_token=A2._COLLECT_TEST_TOKEN)
    assert report2["status"] == "performance-indeterminate"
    assert A2.driver_rc(report2) != 0


@pytest.mark.parametrize("mutation", ("map", "argv"))
def test_m8_controlled_define_map_and_argv_are_independent_gates(
        tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m8")
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    if mutation == "map":
        evidence["controlled_defines"]["CCBENCH_UNEXPECTED"] = "1"
    else:
        evidence["configure_argv"].append("-DCCBENCH_UNEXPECTED=1")
    with pytest.raises(A2.CertificationError):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN, evidence)


def test_m9_run_argv_zero_must_be_the_canonical_binary(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m9")
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    decoy = root / "decoy"
    decoy.write_bytes(b"decoy")
    binary_index = evidence["run_argv"].index("--") + 1
    canonical_binary = evidence["run_argv"][binary_index]
    expected_workload_flags = A2._run_workload_flags(
        evidence["run_argv"][binary_index:])
    evidence["run_argv"][binary_index] = str(decoy)
    evidence["run_argv"].insert(binary_index + 1, canonical_binary)
    assert evidence["run_argv"][binary_index] == str(decoy)
    assert canonical_binary in evidence["run_argv"][binary_index + 1:]
    assert A2._run_workload_flags(
        evidence["run_argv"][binary_index + 1:]) == expected_workload_flags
    with pytest.raises(A2.CertificationError, match=r"argv\[0\]"):
        A2._require_run_binary_at_position(
            evidence["run_argv"], binary_index, Path(canonical_binary))
    with pytest.raises(A2.CertificationError, match=r"argv\[0\]"):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN, evidence)


def test_perf_sha_is_recomputed_from_binary_bytes(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-sha")
    raw = _raw_cell(policy, policy.cells[0], root)
    raw["trace0_evidence"]["perf_bin_sha256"] = "0" * 64
    with pytest.raises(A2.CertificationError, match="binary bytes"):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN,
            raw["trace0_evidence"])


def test_m10_full_submission_and_completion_receipts_are_cross_bound(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-m10", CURRENT_PIN)
    acquisition, submission = _write_receipt_bundle(policy, root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert evidence["request_ids"] == {
        "rr5": "945411.nqsv", "rr50": "945412.nqsv"}
    assert "scheduler_stdout" not in submission
    assert "scheduler_stderr" not in submission
    assert "scheduler_stdout" in evidence["completion"]["jobs"][0]
    assert "scheduler_stderr" in evidence["completion"]["jobs"][0]
    binding = reservation.read_binding(
        evidence["reservation_results"]["rr5"]["environment"])
    assert binding.job_id == "945411.nqsv"
    assert binding.deadline_epoch == binding.scheduler_started_epoch + 21600
    with pytest.raises(FileExistsError):
        A2.record_submission_receipt(
            policy, root, CURRENT_PIN, submission)
    subset = {key: submission[key] for key in (
        "route", "study", "current_pin", "attempt_root", "jobs")}
    with pytest.raises(A2.CertificationError, match="missing required"):
        A2._validate_submission_receipt(
            policy, subset, root.name, root, CURRENT_PIN)

    coordinates = [
        {
            "workload": "rr5", "request_id": "101.nqsv",
            "scheduler_stdout_path": tmp_path / "rr5.stdout",
            "scheduler_stderr_path": tmp_path / "rr5.stderr",
        },
        {
            "workload": "rr50", "request_id": "102.nqsv",
            "scheduler_stdout_path": tmp_path / "rr50.stdout",
            "scheduler_stderr_path": tmp_path / "rr50.stderr",
        },
    ]
    A2._validate_group_coordinates(policy, coordinates)
    duplicate_request = copy.deepcopy(coordinates)
    duplicate_request[1]["request_id"] = duplicate_request[0]["request_id"]
    with pytest.raises(A2.CertificationError, match="request IDs must be distinct"):
        A2._validate_group_coordinates(policy, duplicate_request)
    with pytest.raises(A2.CertificationError, match="workload order"):
        A2._validate_group_coordinates(policy, list(reversed(coordinates)))

    qsub_calls = []

    def runner(argv, **kwargs):
        qsub_calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, "101.nqsv\n", "")

    assert A2.exact_qsub(
        ["qsub", "job.sh"], runner=runner).returncode == 0
    with pytest.raises(A2.CertificationError,
                       match="ratified qsub argv is not exact"):
        A2.exact_qsub(["not-qsub", "job.sh"], runner=runner)
    assert len(qsub_calls) == 1
    assert qsub_calls[0] == (["qsub", "job.sh"], {"check": False})

    finish_root = A2.preregister_attempt(
        policy, "attempt-finish-group", CURRENT_PIN)
    _write_receipt_bundle(
        policy, finish_root, record_completion=False)

    def qstat(command, **kwargs):
        request_id = command[-1]
        return subprocess.CompletedProcess(
            command, 0,
            f"Request ID: {request_id}\nRequest State = EXT\n", "")

    completion_path, finish_acquisition = A2.finish_group(
        policy, finish_root, CURRENT_PIN, qstat_runner=qstat)
    assert completion_path == finish_root / "receipts" / "completion.json"
    finish_evidence = A2.validate_acquisition_bundle(
        policy, finish_acquisition, current_pin=CURRENT_PIN)
    assert finish_evidence["driver_rcs"] == {"rr5": 0, "rr50": 0}
    assert finish_evidence["raw_manifest_valid"] is True


def test_scheduler_request_id_diagnostic_is_create_only_and_non_symlink(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-request-sidecar", CURRENT_PIN)
    scheduler = root / "jobs" / "rr5" / "scheduler"
    fsync_calls = []
    original_fsync_dir = A2._fsync_dir

    def observed_fsync(path):
        fsync_calls.append(path)
        original_fsync_dir(path)

    monkeypatch.setattr(A2, "_fsync_dir", observed_fsync)
    sidecar = A2.record_scheduler_request_id(
        policy, root, "rr5", "0:945411.nqsv.")
    assert sidecar == scheduler / "request-id"
    assert sidecar.is_file() and not sidecar.is_symlink()
    assert sidecar.read_bytes() == b"945411.nqsv\n"
    assert fsync_calls == [scheduler]
    with pytest.raises(FileExistsError):
        A2.record_scheduler_request_id(
            policy, root, "rr5", "945411.nqsv")

    second = A2.preregister_attempt(
        policy, "attempt-request-sidecar-symlink", CURRENT_PIN)
    linked = second / "jobs" / "rr5" / "scheduler" / "request-id"
    linked.symlink_to(tmp_path / "decoy-request-id")
    with pytest.raises(FileExistsError):
        A2.record_scheduler_request_id(
            policy, second, "rr5", "945411.nqsv")


def test_qsub_diagnostics_fsync_both_files_then_scheduler_directory(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-qsub-diagnostics", CURRENT_PIN)
    scheduler = root / "jobs" / "rr5" / "scheduler"
    stdout_path = scheduler / "qsub.stdout"
    stderr_path = scheduler / "qsub.stderr"
    stdout_path.write_bytes(b"Request 945411.nqsv submitted\n")
    stderr_path.write_bytes(b"")
    fsync_targets = []
    original_fsync = A2.os.fsync

    def observed_fsync(descriptor):
        fsync_targets.append(Path(f"/proc/self/fd/{descriptor}").resolve())
        original_fsync(descriptor)

    monkeypatch.setattr(A2.os, "fsync", observed_fsync)
    assert A2.durabilize_scheduler_qsub_diagnostics(
        policy, root, "rr5") == (stdout_path, stderr_path)
    assert fsync_targets == [stdout_path, stderr_path, scheduler]


def _terminal_qstat(command, **kwargs):
    request_id = command[-1]
    return subprocess.CompletedProcess(
        command, 0,
        f"Request ID: {request_id}\nRequest State = EXT\n", "")


def test_m1_a6_single_workload_full_success_stays_v3(tmp_path):
    policy = _a6_policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-a6-full-m1", CURRENT_PIN)
    _write_receipt_bundle(policy, root, record_completion=False)

    completion_path, acquisition_path = A2.finish_group(
        policy, root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    completion, _ = A2._read_json(completion_path)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition_path, current_pin=CURRENT_PIN)

    assert completion["schema_version"] == A2.COMPLETION_SCHEMA
    assert completion["raw_result_manifest"] == str(root / "raw-manifest.json")
    assert evidence["completion_schema"] == A2.COMPLETION_SCHEMA
    assert evidence["raw_manifest_schema"] == A2.RAW_MANIFEST_SCHEMA
    assert evidence["raw_manifest_valid"] is True
    assert len(evidence["raw_files"]) == 6


def test_m2_partial_v4_completion_requires_exact_two_workloads(tmp_path):
    policy = _a6_policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-a6-forged-partial-m2", CURRENT_PIN)
    _acquisition, submission = _write_receipt_bundle(policy, root)
    completion, _ = A2._read_json(root / "receipts" / "completion.json")
    completion["schema_version"] = A2.PARTIAL_COMPLETION_SCHEMA
    completion["successful_workload"] = "rr95"
    submission_binding = A2._validate_submission_receipt(
        policy, submission, root.name, root, CURRENT_PIN)

    with pytest.raises(
            A2.CertificationError, match="exact two-workload policy"):
        A2._validate_completion_receipt(
            policy, completion, root.name, root, CURRENT_PIN,
            submission_binding,
        )


def test_p2_a6_full_v3_path_collects_and_materializes(tmp_path):
    policy = _a6_policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-a6-full-p2", CURRENT_PIN)
    _write_receipt_bundle(policy, root, record_completion=False)
    _completion, acquisition = A2.finish_group(
        policy, root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    report = A2.collect_results(
        policy, evidence["raw_results"], attempt_id=root.name,
        current_pin=CURRENT_PIN, request_ids=evidence["request_ids"],
        frozen_files=evidence["raw_files"], attempt_root=root,
    )
    report["source_commit"] = evidence["source_commit"]
    assert A2._canonical_full_report(
        policy, evidence, attempt_id=root.name,
        current_pin=CURRENT_PIN) == report
    repository = tmp_path / "a6-materialized-repository"
    repository.mkdir()
    destination = A2.materialize(
        policy, report, evidence, repo_root=repository)

    assert report["status"] == "observed-positive"
    assert [cell["workload"] for cell in report["cells"]] == ["rr95", "rr95"]
    assert all(cell["correctness"]["status"] == "certified"
               for cell in report["cells"])
    assert destination == repository / policy.tracked_destination
    assert (destination / "certification.json").is_file()
    assert (destination / "COMPLETE.json").is_file()


def test_a6_anomaly_is_immediate_reject(tmp_path):
    policy = _a6_policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-a6-anomaly")
    results = _positive_results(policy, root)
    anomaly = results[0]
    anomaly["correctness"][PERFORMANCE_TAG][0] = {
        **anomaly["correctness"][PERFORMANCE_TAG][0],
        "status": "anomaly",
        "certified": False,
        "verdict": "non-serializable",
        "anomalies": [{"cycle": ["read-a", "read-b"]}],
    }
    anomaly["correctness"][PERFORMANCE_TAG] = [
        anomaly["correctness"][PERFORMANCE_TAG][0]]
    anomaly["trace0_evidence"] = None
    anomaly["performance"] = {
        "status": "indeterminate", "reason": "verify-reject"}
    report = A2.collect_results(
        policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_ids=_request_ids(policy), _test_token=A2._COLLECT_TEST_TOKEN)

    assert report["status"] == "reject"
    assert report["cells"][0]["correctness"]["status"] == "non-serializable"
    assert A2.driver_rc(report) == 0


def test_m4_finish_rejects_compute_request_mismatch_without_raw_manifest(
        tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-finish-prevalidate-m4", CURRENT_PIN)
    _write_receipt_bundle(policy, root, record_completion=False)
    compute_path = root / "jobs" / "rr5" / "compute-result.json"
    compute, _ = A2._read_json(compute_path)
    compute["pbs_jobid"] = "945412.nqsv"
    compute_path.write_bytes(A2._canonical_json(compute))

    with pytest.raises(A2.CertificationError, match="compute result identity"):
        A2.finish_group(
            policy, root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    assert not (root / "raw-manifest.json").exists()
    assert not (root / "receipts" / "completion.json").exists()
    assert not (root / "receipts" / "acquisition.json").exists()


def test_m5_finish_prevalidates_each_job_against_its_own_request(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-finish-prevalidate-m5", CURRENT_PIN)
    _write_receipt_bundle(policy, root, record_completion=False)
    original_validate = A2._validate_completion_job
    first_calls = []

    def observed_validate(
            observed_policy, payload, attempt_id, attempt_root, current_pin,
            workload_id, request_id, submission, job_body_sha256):
        if len(first_calls) < 2:
            assert not (root / "raw-manifest.json").exists()
            assert payload["workload"] == workload_id
            assert payload["request_id"] == request_id
            assert submission["request_id"] == request_id
            first_calls.append((workload_id, request_id))
        return original_validate(
            observed_policy, payload, attempt_id, attempt_root, current_pin,
            workload_id, request_id, submission, job_body_sha256)

    monkeypatch.setattr(A2, "_validate_completion_job", observed_validate)
    A2.finish_group(
        policy, root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    assert first_calls == [
        ("rr5", "945411.nqsv"), ("rr50", "945412.nqsv")]


def test_pc2_canonical_finish_creates_manifest_completion_and_acquisition(
        tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-finish-positive-control", CURRENT_PIN)
    _write_receipt_bundle(policy, root, record_completion=False)
    assert not any(
        (root / "jobs" / workload / "scheduler" / "request-id").exists()
        for workload in A2.workload_ids(policy))

    completion, acquisition = A2.finish_group(
        policy, root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    assert completion == root / "receipts" / "completion.json"
    assert acquisition == root / "receipts" / "acquisition.json"
    assert (root / "raw-manifest.json").is_file()
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert evidence["driver_rcs"] == {"rr5": 0, "rr50": 0}
    assert evidence["raw_manifest_valid"] is True
    assert evidence["acquisition_schema"] == A2.ACQUISITION_SCHEMA
    assert evidence["completion_schema"] == A2.COMPLETION_SCHEMA
    assert evidence["raw_manifest_schema"] == A2.RAW_MANIFEST_SCHEMA


def test_authority_none_production_finish_and_collect_remain_v3_indeterminate(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-finish-failed-driver", CURRENT_PIN)
    _write_receipt_bundle(
        policy, root, driver_rc={"rr5": 7, "rr50": 9},
        record_completion=False)

    completion, acquisition = A2.finish_group(
        policy, root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    assert completion == root / "receipts" / "completion.json"
    assert acquisition == root / "receipts" / "acquisition.json"
    assert not (root / "raw-manifest.json").exists()
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert evidence["driver_rcs"] == {"rr5": 7, "rr50": 9}
    assert evidence["acquisition_schema"] == A2.ACQUISITION_SCHEMA
    assert evidence["raw_manifest_valid"] is False
    assert evidence["raw_manifest_reason"] == "driver-nonzero"

    captured = {}
    monkeypatch.setattr(A2, "load_policy", lambda: policy)

    def forbidden_positive_path(*args, **kwargs):
        raise AssertionError("failed driver reached positive collector")

    def materialize(_policy, report, _evidence, *, repo_root):
        captured.update(report)
        return Path(repo_root) / "captured"

    monkeypatch.setattr(A2, "collect_results", forbidden_positive_path)
    monkeypatch.setattr(A2, "materialize", materialize)
    assert A2.main([
        "collect", "--attempt-root", str(root),
        "--current-pin", CURRENT_PIN,
        "--acquisition-receipt", str(acquisition),
        "--repo-root", str(tmp_path),
    ]) == 2
    assert captured["status"] == "indeterminate"
    assert "compute driver exited nonzero" in captured["reason"]


def test_legacy_v3_one_failed_driver_consumer_remains_indeterminate(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-legacy-v3-failed-driver", CURRENT_PIN)
    acquisition, _submission = _write_receipt_bundle(
        policy, root, driver_rc=7, force_legacy_v3=True)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert evidence["acquisition_schema"] == A2.ACQUISITION_SCHEMA
    assert evidence["completion_schema"] == A2.COMPLETION_SCHEMA
    assert evidence["driver_rcs"] == {"rr5": 7, "rr50": 0}
    assert evidence["raw_manifest_valid"] is False

    captured = {}
    monkeypatch.setattr(A2, "load_policy", lambda: policy)

    def forbidden_partial_path(*args, **kwargs):
        raise AssertionError("legacy v3 failed driver reached raw collector")

    def materialize(_policy, report, _evidence, *, repo_root):
        captured.update(report)
        return Path(repo_root) / "captured"

    monkeypatch.setattr(A2, "collect_results", forbidden_partial_path)
    monkeypatch.setattr(A2, "materialize", materialize)
    assert A2.main([
        "collect", "--attempt-root", str(root),
        "--current-pin", CURRENT_PIN,
        "--acquisition-receipt", str(acquisition),
        "--repo-root", str(tmp_path),
    ]) == 2
    assert captured["schema_version"] == A2.CERTIFICATION_SCHEMA
    assert captured["status"] == "indeterminate"
    assert "compute driver exited nonzero" in captured["reason"]


def test_partial_anomaly_production_chain_rejects_without_failed_raw(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-partial-anomaly", CURRENT_PIN)
    _write_receipt_bundle(
        policy, root, driver_rc=7, record_completion=False)
    authoritative_raw = _make_first_cell_anomalous_from_wal(
        policy, root, "rr50")
    expected_manifest_members = {
        "jobs/rr50/raw/rr50-stock.json",
        "jobs/rr50/raw/rr50-fixed5.json",
        A2._condition_gate_receipt_relative("rr50"),
        *(
            Path(authoritative_raw[0]["campaign_evidence"][f"{kind}_path"])
            .relative_to(root).as_posix()
            for kind in ("lock", "wal", "claim")
        ),
    }
    failed_decoy = {
        "cell_id": "rr5-decoy",
        "failed_raw_decoy_tps": 987654321,
        "failed_raw_decoy_effect": 12345.0,
        "failed_raw_decoy_anomaly": True,
    }
    for name in ("rr5-stock.json", "rr5-fixed10.json"):
        (root / "jobs" / "rr5" / "raw" / name).write_bytes(
            A2._canonical_json(failed_decoy))

    original_read_json = A2._read_json

    def reject_failed_raw_read(path, **kwargs):
        candidate = Path(path)
        assert root / "jobs" / "rr5" / "raw" not in candidate.parents
        return original_read_json(candidate, **kwargs)

    monkeypatch.setattr(A2, "_read_json", reject_failed_raw_read)

    completion_path, acquisition_path = A2.finish_group(
        policy, root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    completion, _ = A2._read_json(completion_path)
    assert completion["schema_version"] == A2.PARTIAL_COMPLETION_SCHEMA
    assert completion["successful_workload"] == "rr50"
    manifest, _ = A2._read_json(root / "raw-manifest.json")
    assert manifest["schema_version"] == A2.PARTIAL_RAW_MANIFEST_SCHEMA
    assert manifest["successful_workload"] == "rr50"
    assert set(manifest["files"]) == expected_manifest_members
    assert len(manifest["files"]) == 6
    assert all(not path.startswith("jobs/rr5/") for path in manifest["files"])
    assert len([
        path for path in manifest["files"]
        if path.endswith("/campaign.lock")]) == 1
    assert len([
        path for path in manifest["files"]
        if path.endswith("/runs/wal.jsonl")]) == 1
    assert len([
        path for path in manifest["files"]
        if path.endswith(".claim")]) == 1

    evidence = A2.validate_acquisition_bundle(
        policy, acquisition_path, current_pin=CURRENT_PIN)
    assert evidence["acquisition_schema"] == A2.PARTIAL_ACQUISITION_SCHEMA
    assert [raw["cell_id"] for raw in evidence["raw_results"]] == [
        "rr50-stock", "rr50-fixed5"]
    assert len(evidence["raw_files"]) == 6
    assert all("jobs/rr5/" not in path for path in evidence["raw_files"])

    monkeypatch.setattr(A2, "load_policy", lambda: policy)
    repo = tmp_path / "partial-anomaly-repo"
    repo.mkdir()
    assert A2.main([
        "collect", "--attempt-root", str(root),
        "--current-pin", CURRENT_PIN,
        "--acquisition-receipt", str(acquisition_path),
        "--repo-root", str(repo),
    ]) == 0
    destination = repo / policy.tracked_destination
    report = json.loads(
        (destination / "certification.json").read_text(encoding="utf-8"))
    assert report["schema_version"] == A2.PARTIAL_CERTIFICATION_SCHEMA
    assert report["status"] == "reject"
    assert report["reason"] == "authoritative-workload-anomaly:rr50"
    assert report["workload_authority"] == {
        "rr5": {
            "authority": "unavailable",
            "driver_rc": 7,
            "reason": "driver-exited-nonzero:7",
        },
        "rr50": {
            "authority": "authoritative",
            "driver_rc": 0,
            "reason": "verified-partial-v4-manifest",
        },
    }
    assert [cell["cell_id"] for cell in report["cells"]] == [
        "rr50-stock", "rr50-fixed5"]
    assert report["effects"] == {}
    serialized = json.dumps(report, sort_keys=True)
    assert "987654321" not in serialized
    assert "12345.0" not in serialized


@pytest.mark.parametrize(
    "adopted_gain,expected_status,expected_reason",
    ((1.1, "partial", "authoritative-workload-positive:rr50"),
     (1.0, "reject", "authoritative-workload-effect-nonpositive:rr50"),
     (0.9, "reject", "authoritative-workload-effect-nonpositive:rr50")),
)
def test_partial_positive_and_nonpositive_effect_statuses(
        tmp_path, monkeypatch, adopted_gain, expected_status, expected_reason):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-partial-effect-" + expected_status, CURRENT_PIN)
    _write_receipt_bundle(
        policy, root, driver_rc=7, record_completion=False,
        adopted_gain=adopted_gain)
    _completion, acquisition = A2.finish_group(
        policy, root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    report = A2._canonical_partial_report(
        policy, evidence, current_pin=CURRENT_PIN)
    assert report["status"] == expected_status
    assert report["reason"] == expected_reason
    assert set(report["effects"]) == {"rr50"}
    assert [cell["workload"] for cell in report["cells"]] == ["rr50", "rr50"]
    assert A2.driver_rc(report) == 0

    monkeypatch.setattr(A2, "load_policy", lambda: policy)
    repo = tmp_path / "partial-effect-repo"
    repo.mkdir()
    assert A2.main([
        "collect", "--attempt-root", str(root),
        "--current-pin", CURRENT_PIN,
        "--acquisition-receipt", str(acquisition),
        "--repo-root", str(repo),
    ]) == 0
    destination = repo / policy.tracked_destination
    assert destination.is_dir()
    materialized = json.loads(
        (destination / "certification.json").read_text(encoding="utf-8"))
    assert materialized == report
    assert materialized["status"] == expected_status
    assert (destination / "COMPLETE.json").is_file()


def test_partial_authoritative_science_can_remain_inconclusive(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-partial-science-inconclusive", CURRENT_PIN)
    _write_receipt_bundle(
        policy, root, driver_rc=7, record_completion=False)
    _make_first_cell_inconclusive_from_wal(policy, root, "rr50")
    _completion, acquisition = A2.finish_group(
        policy, root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    report = A2._canonical_partial_report(
        policy, evidence, current_pin=CURRENT_PIN)

    assert report["status"] == "inconclusive"
    assert report["reason"] == "authoritative-workload-inconclusive:rr50"
    assert report["workload_authority"]["rr50"] == {
        "authority": "authoritative",
        "driver_rc": 0,
        "reason": "verified-partial-v4-manifest",
    }
    assert [cell["workload"] for cell in report["cells"]] == ["rr50", "rr50"]
    assert report["effects"] == {}
    assert A2.driver_rc(report) == 2

    monkeypatch.setattr(A2, "load_policy", lambda: policy)
    repo = tmp_path / "partial-inconclusive-repo"
    repo.mkdir()
    assert A2.main([
        "collect", "--attempt-root", str(root),
        "--current-pin", CURRENT_PIN,
        "--acquisition-receipt", str(acquisition),
        "--repo-root", str(repo),
    ]) == 2
    destination = repo / policy.tracked_destination
    assert destination.is_dir()
    materialized = json.loads(
        (destination / "certification.json").read_text(encoding="utf-8"))
    assert materialized == report
    assert materialized["status"] == "inconclusive"
    assert (destination / "COMPLETE.json").is_file()


def test_partial_invalid_authority_stops_before_report_or_artifact(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-partial-invalid-authority", CURRENT_PIN)
    _write_receipt_bundle(
        policy, root, driver_rc=7, record_completion=False)
    _completion, acquisition = A2.finish_group(
        policy, root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    with (root / "raw-manifest.json").open("ab") as stream:
        stream.write(b" ")
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert evidence["raw_manifest_valid"] is False
    assert evidence["raw_manifest_invalid_kind"] == "authority"
    with pytest.raises(A2.AuthorityError, match="raw manifest authority"):
        A2._canonical_partial_report(
            policy, evidence, current_pin=CURRENT_PIN)

    monkeypatch.setattr(A2, "load_policy", lambda: policy)
    repo = tmp_path / "partial-invalid-authority-repo"
    repo.mkdir()
    assert A2.main([
        "collect", "--attempt-root", str(root),
        "--current-pin", CURRENT_PIN,
        "--acquisition-receipt", str(acquisition),
        "--repo-root", str(repo),
    ]) == 2
    assert not (repo / policy.tracked_destination).exists()


@pytest.mark.parametrize("mutation", ("cross-version", "failed-raw-member"))
def test_partial_materializer_rejects_cross_schema_and_failed_raw_mixing(
        tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-partial-chain-" + mutation, CURRENT_PIN)
    _write_receipt_bundle(
        policy, root, driver_rc=7, record_completion=False)
    _completion, acquisition = A2.finish_group(
        policy, root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    manifest_path = root / "raw-manifest.json"
    manifest, _ = A2._read_json(manifest_path)
    if mutation == "cross-version":
        manifest["schema_version"] = A2.LEGACY_RAW_MANIFEST_SCHEMA
    else:
        failed_raw = root / "jobs" / "rr5" / "raw" / "rr5-stock.json"
        manifest["files"]["jobs/rr5/raw/rr5-stock.json"] = hashlib.sha256(
            failed_raw.read_bytes()).hexdigest()
    manifest_path.write_bytes(A2._canonical_json(manifest))
    _reseal_partial_receipts_after_manifest_mutation(root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert evidence["raw_manifest_invalid_kind"] == "schema-chain"
    report = A2._canonical_partial_report(
        policy, evidence, current_pin=CURRENT_PIN)
    repo = tmp_path / ("repo-" + mutation)
    repo.mkdir()
    with pytest.raises(A2.SchemaChainError):
        A2.materialize(policy, report, evidence, repo_root=repo)
    assert not (repo / policy.tracked_destination).exists()


@pytest.mark.parametrize(
    "relocated", ("manifest", "submission", "completion"))
def test_partial_v4_chain_rejects_noncanonical_authority_path_before_read(
        tmp_path, monkeypatch, relocated):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-partial-path-" + relocated, CURRENT_PIN)
    _write_receipt_bundle(
        policy, root, driver_rc=7, record_completion=False)
    _completion, acquisition_path = A2.finish_group(
        policy, root, CURRENT_PIN, qstat_runner=_terminal_qstat)

    canonical_paths = {
        "manifest": root / "raw-manifest.json",
        "submission": root / "receipts" / "submission.json",
        "completion": root / "receipts" / "completion.json",
    }
    copied_path = root / "jobs" / "rr5" / "raw" / (relocated + ".json")
    copied_path.write_bytes(canonical_paths[relocated].read_bytes())
    copied_sha = hashlib.sha256(copied_path.read_bytes()).hexdigest()
    if relocated == "manifest":
        completion, _ = A2._read_json(canonical_paths["completion"])
        completion["raw_result_manifest"] = str(copied_path)
        completion["raw_result_manifest_sha256"] = copied_sha
        canonical_paths["completion"].write_bytes(A2._canonical_json(completion))
        acquisition, _ = A2._read_json(acquisition_path)
        acquisition["completion_receipt_sha256"] = hashlib.sha256(
            canonical_paths["completion"].read_bytes()).hexdigest()
    else:
        acquisition, _ = A2._read_json(acquisition_path)
        acquisition[relocated + "_receipt"] = str(copied_path)
        acquisition[relocated + "_receipt_sha256"] = copied_sha
    acquisition_path.write_bytes(A2._canonical_json(acquisition))

    original_read_json = A2._read_json
    copied_reads = []

    def reject_copied_content_read(path, **kwargs):
        candidate = Path(path)
        if candidate == copied_path:
            copied_reads.append(candidate)
            raise AssertionError("noncanonical authority copy was read")
        return original_read_json(candidate, **kwargs)

    monkeypatch.setattr(A2, "_read_json", reject_copied_content_read)
    if relocated == "manifest":
        evidence = A2.validate_acquisition_bundle(
            policy, acquisition_path, current_pin=CURRENT_PIN)
        assert evidence["raw_manifest_valid"] is False
        assert evidence["raw_manifest_invalid_kind"] == "schema-chain"
        assert evidence["raw_manifest_reason"] == (
            "partial raw manifest path is not canonical")
        report = A2._canonical_partial_report(
            policy, evidence, current_pin=CURRENT_PIN)
        repo = tmp_path / "noncanonical-manifest-repo"
        repo.mkdir()
        with pytest.raises(
                A2.SchemaChainError,
                match="materialization rejects the raw schema chain"):
            A2.materialize(policy, report, evidence, repo_root=repo)
        assert not (repo / policy.tracked_destination).exists()
    else:
        with pytest.raises(
                A2.SchemaChainError,
                match=f"partial {relocated} receipt path is not canonical"):
            A2.validate_acquisition_bundle(
                policy, acquisition_path, current_pin=CURRENT_PIN)
    assert copied_reads == []


def test_materializer_rejects_v3_v4_result_receipt_cross_chain(tmp_path):
    policy = _policy(tmp_path)
    partial_root = A2.preregister_attempt(
        policy, "attempt-partial-result-cross", CURRENT_PIN)
    _write_receipt_bundle(
        policy, partial_root, driver_rc=7, record_completion=False)
    _completion, partial_acquisition = A2.finish_group(
        policy, partial_root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    partial_evidence = A2.validate_acquisition_bundle(
        policy, partial_acquisition, current_pin=CURRENT_PIN)
    partial_report = A2._canonical_partial_report(
        policy, partial_evidence, current_pin=CURRENT_PIN)
    forged_v3 = A2._indeterminate_report(
        policy, partial_evidence, attempt_id=partial_root.name,
        current_pin=CURRENT_PIN, reason="crossed-v3-result")
    v3_repo = tmp_path / "crossed-v3-result-repo"
    v3_repo.mkdir()
    with pytest.raises(A2.SchemaChainError, match="legacy result is crossed"):
        A2.materialize(
            policy, forged_v3, partial_evidence, repo_root=v3_repo)

    full_root = A2.preregister_attempt(
        policy, "attempt-full-result-cross", CURRENT_PIN)
    full_acquisition, _submission = _write_receipt_bundle(policy, full_root)
    full_evidence = A2.validate_acquisition_bundle(
        policy, full_acquisition, current_pin=CURRENT_PIN)
    partial_repo = tmp_path / "crossed-partial-result-repo"
    partial_repo.mkdir()
    with pytest.raises(A2.SchemaChainError, match="partial result is crossed"):
        A2.materialize(
            policy, partial_report, full_evidence, repo_root=partial_repo)


def _partial_materializer_forgery_case(tmp_path, attempt_id):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, attempt_id, CURRENT_PIN)
    _write_receipt_bundle(
        policy, root, driver_rc=7, record_completion=False)
    _completion, acquisition = A2.finish_group(
        policy, root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    report = A2._canonical_partial_report(
        policy, evidence, current_pin=CURRENT_PIN)
    return policy, root, evidence, report


def _full_materializer_forgery_case(tmp_path, attempt_id):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, attempt_id, CURRENT_PIN)
    acquisition, _submission = _write_receipt_bundle(policy, root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    report = A2._canonical_full_report(
        policy, evidence, attempt_id=root.name, current_pin=CURRENT_PIN)
    assert report["status"] == "observed-positive"
    return policy, root, evidence, report


def test_full_materializer_writes_reread_receipt_bytes_not_supplied_bytes(
        tmp_path):
    policy, _root, evidence, report = _full_materializer_forgery_case(
        tmp_path, "attempt-full-forged-receipt-bytes")
    forged_evidence = copy.deepcopy(evidence)
    forged_bytes = b'{"forged": true}\n'
    for key in (
            "acquisition_bytes", "submission_bytes", "completion_bytes"):
        forged_evidence[key] = forged_bytes
    repo = tmp_path / "full-forged-receipt-bytes-repo"
    repo.mkdir()
    destination = A2.materialize(
        policy, report, forged_evidence, repo_root=repo)
    receipt_files = {
        "acquisition-receipt.json": "acquisition_bytes",
        "submission-receipt.json": "submission_bytes",
        "completion-receipt.json": "completion_bytes",
    }
    manifest = json.loads(
        (destination / "artifact-manifest.json").read_text(encoding="utf-8"))
    for name, key in receipt_files.items():
        materialized = (destination / name).read_bytes()
        assert materialized == evidence[key]
        assert materialized != forged_evidence[key]
        assert manifest["files"][name] == hashlib.sha256(evidence[key]).hexdigest()


def test_full_materializer_rejects_reread_partial_receipt_chain_behind_forged_full_fields(
        tmp_path):
    policy, root, evidence, _report = _partial_materializer_forgery_case(
        tmp_path, "attempt-full-forged-partial-receipt-chain")
    forged_evidence = copy.deepcopy(evidence)
    forged_evidence["acquisition_schema"] = A2.ACQUISITION_SCHEMA
    forged_evidence["completion_schema"] = A2.COMPLETION_SCHEMA
    forged_evidence["raw_manifest_valid"] = False
    forged_evidence["raw_manifest_schema"] = None
    forged = A2._canonical_full_report(
        policy, forged_evidence, attempt_id=root.name,
        current_pin=CURRENT_PIN)
    repo = tmp_path / "full-forged-partial-receipt-chain-repo"
    repo.mkdir()
    with pytest.raises(
            A2.SchemaChainError,
            match="crossed with a re-read partial receipt chain"):
        A2.materialize(policy, forged, forged_evidence, repo_root=repo)
    assert not (repo / policy.tracked_destination).exists()


def test_full_materializer_rejects_forged_status_from_positive_evidence(
        tmp_path):
    policy, _root, evidence, report = _full_materializer_forgery_case(
        tmp_path, "attempt-full-forged-status")
    forged = copy.deepcopy(report)
    forged["status"] = "reject"
    repo = tmp_path / "full-forged-status-repo"
    repo.mkdir()
    with pytest.raises(
            A2.CertificationError, match="differs from evidence re-derivation"):
        A2.materialize(policy, forged, evidence, repo_root=repo)
    assert not (repo / policy.tracked_destination).exists()


def test_full_materializer_rejects_forged_effects_from_positive_evidence(
        tmp_path):
    policy, _root, evidence, report = _full_materializer_forgery_case(
        tmp_path, "attempt-full-forged-effects")
    forged = copy.deepcopy(report)
    first_workload = A2.workload_ids(policy)[0]
    forged["effects"][first_workload] = report["effects"][first_workload] + 1.0
    repo = tmp_path / "full-forged-effects-repo"
    repo.mkdir()
    with pytest.raises(
            A2.CertificationError, match="differs from evidence re-derivation"):
        A2.materialize(policy, forged, evidence, repo_root=repo)
    assert not (repo / policy.tracked_destination).exists()


def test_full_materializer_rejects_indeterminate_report_from_full_success_acquisition(
        tmp_path):
    policy, root, evidence, _report = _full_materializer_forgery_case(
        tmp_path, "attempt-full-forged-indeterminate")
    forged_evidence = copy.deepcopy(evidence)
    first_workload = A2.workload_ids(policy)[0]
    forged_evidence["driver_rcs"][first_workload] = 7
    failed_drivers = {first_workload: 7}
    forged = A2._indeterminate_report(
        policy, forged_evidence, attempt_id=root.name,
        current_pin=CURRENT_PIN,
        reason=f"compute driver exited nonzero: {failed_drivers}")
    repo = tmp_path / "full-forged-indeterminate-repo"
    repo.mkdir()
    with pytest.raises(
            A2.CertificationError, match="differs from evidence re-derivation"):
        A2.materialize(policy, forged, forged_evidence, repo_root=repo)
    assert not (repo / policy.tracked_destination).exists()


def test_m7_partial_materializer_rejects_forged_authority_and_status(tmp_path):
    policy, _root, evidence, report = _partial_materializer_forgery_case(
        tmp_path, "attempt-partial-forgery-m7")
    forged = copy.deepcopy(report)
    forged["status"] = "reject"
    forged["workload_authority"]["rr5"]["authority"] = "authoritative"
    repo = tmp_path / "forged-m7-repo"
    repo.mkdir()
    with pytest.raises(
            A2.CertificationError, match="differs from evidence re-derivation"):
        A2.materialize(policy, forged, evidence, repo_root=repo)
    assert not (repo / policy.tracked_destination).exists()


def test_m8_partial_materializer_rejects_failed_workload_cells_and_effects(
        tmp_path):
    policy, root, evidence, report = _partial_materializer_forgery_case(
        tmp_path, "attempt-partial-forgery-m8")
    failed_local = A2._classify_workload_pair(
        policy, A2._load_workload_raw_results(policy, root, "rr5"),
        workload_id="rr5", attempt_id=root.name, current_pin=CURRENT_PIN,
        attempt_root=root)
    assert [cell["workload"] for cell in failed_local["cells"]] == [
        "rr5", "rr5"]
    assert set(failed_local["effects"]) == {"rr5"}
    forged = copy.deepcopy(report)
    forged["cells"].extend(failed_local["cells"])
    forged["effects"].update(failed_local["effects"])
    repo = tmp_path / "forged-m8-repo"
    repo.mkdir()
    with pytest.raises(
            A2.CertificationError, match="differs from evidence re-derivation"):
        A2.materialize(policy, forged, evidence, repo_root=repo)
    assert not (repo / policy.tracked_destination).exists()


@pytest.mark.parametrize("missing", ("qsub_argv", "qstat_visibility"))
def test_m10_each_canonical_qsub_and_submit_observation_field_is_required(
        tmp_path, missing):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-m10-" + missing.replace("_", "-"), CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0].pop(missing)
    with pytest.raises(A2.CertificationError, match="not exact"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


@pytest.mark.parametrize("mutation", ("extra-env", "nodes", "job-body"))
def test_submission_argv_environment_nodes_and_job_body_are_exact(
        tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-" + mutation, CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    mutant = copy.deepcopy(submission)
    if mutation == "extra-env":
        mutant["jobs"][0]["qsub_environment"]["PYTHONPATH"] = "/tmp/decoy"
        mutant["jobs"][0]["qsub_argv"][12] += ",PYTHONPATH=/tmp/decoy"
    elif mutation == "nodes":
        mutant["jobs"][0]["qsub_argv"][6] = "2"
    else:
        decoy = root / "decoy" / "paper_story_a2_certification.sh"
        decoy.parent.mkdir()
        decoy.write_bytes(
            (A2.POLICY_PATH.parents[2]
             / policy.document["scheduler"]["job_body"]).read_bytes())
        mutant["jobs"][0]["qsub_argv"][-1] = str(decoy)
        mutant["job_body_sha256"] = hashlib.sha256(decoy.read_bytes()).hexdigest()
    with pytest.raises(A2.CertificationError):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


@pytest.mark.parametrize("mutation", ("missing", "changed"))
def test_submission_rejects_missing_or_changed_third_party_source_root(
        tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-third-party-" + mutation, CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    mutant = copy.deepcopy(submission)
    environment = mutant["jobs"][0]["qsub_environment"]
    if mutation == "missing":
        environment.pop("IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT")
        components = mutant["jobs"][0]["qsub_argv"][12].split(",")
        mutant["jobs"][0]["qsub_argv"][12] = ",".join(
            component for component in components
            if not component.startswith(
                "IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT="
            )
        )
    else:
        environment["IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT"] = "/changed/root"

    with pytest.raises(A2.CertificationError):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def _assert_real_submission_visibility_is_accepted(policy, root, submission):
    binding = A2._validate_submission_receipt(
        policy, submission, root.name, root, CURRENT_PIN)
    assert binding["request_ids"] == {
        "rr5": "945411.nqsv", "rr50": "945412.nqsv"}
    assert submission["jobs"][0]["qstat_visibility"]["state"] == "QUE"


def test_submission_visibility_uses_the_full_real_qstat_fixture(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-real-qstat", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    fixture_bytes = QSTAT_VISIBILITY_FIXTURE.read_bytes()
    assert hashlib.sha256(fixture_bytes).hexdigest() == (
        "55bc7a633cd903bfa592ab71c4f347b6a50cce7ca295acb068de50b390ef830d"
    )
    fixture = fixture_bytes.decode("utf-8")
    assert len(fixture.splitlines()) == 94
    assert "Current State           = Staging" in fixture
    assert "Request State = RUN" not in fixture
    historical_stdout = (
        "/work/1/SFC/tanab/izanagi-measurements/"
        "dev-wave-paper-story-a2-cert-20260824/t1647-20260825/"
        "scheduler/job.stdout")
    historical_stderr = historical_stdout.removesuffix("job.stdout") + "job.stderr"
    for workload_id, request_id in (
            ("rr5", "945411.nqsv"), ("rr50", "945412.nqsv")):
        expected = fixture.replace("945411.nqsv", request_id)
        expected = expected.replace(
            historical_stdout,
            f"/synthetic/attempt/jobs/{workload_id}/scheduler/job.stdout")
        expected = expected.replace(
            historical_stderr,
            f"/synthetic/attempt/jobs/{workload_id}/scheduler/job.stderr")
        fanout_fixture = QSTAT_FANOUT_VISIBILITY_FIXTURES[
            workload_id].read_text(encoding="utf-8")
        assert fanout_fixture == expected
        assert len(fanout_fixture.splitlines()) == 94
        assert submission["jobs"][
            0 if workload_id == "rr5" else 1]["qstat_visibility"]["stdout"] \
            == fanout_fixture
    assert A2.SUBMISSION_SCHEMA == "paper-story-a2-submission-receipt/v4"
    assert A2._SUBMISSION_VISIBLE_STATES == frozenset({"QUE", "RUN"})
    _assert_real_submission_visibility_is_accepted(
        policy, root, submission)


def test_submission_visibility_rejects_another_request_block(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-another-block", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] = (
        "Request ID: 999999.nqsv\n"
        + mutant["jobs"][0]["qstat_visibility"]["stdout"])
    with pytest.raises(A2.CertificationError, match="request ID count is not one"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_rejects_conflicting_state_fields(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-state-conflict", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] += "Request State = RUN\n"
    with pytest.raises(A2.CertificationError, match="state fields conflict"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_rejects_state_before_target_id(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-state-before-id", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] = (
        "Request State = QUE\n"
        + mutant["jobs"][0]["qstat_visibility"]["stdout"])
    with pytest.raises(
        A2.CertificationError, match="state before the target request ID"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_rejects_non_none_ended_time(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-ended-time", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] = mutant[
        "jobs"][0]["qstat_visibility"]["stdout"].replace(
            "Ended Request Time   = (none)",
            "Ended Request Time   = Tue Aug 25 09:00:00 2026",
            1,
        )
    with pytest.raises(A2.CertificationError, match=r"not \(none\)"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


@pytest.mark.parametrize(
    ("mutation", "signature"),
    (
        ("missing", "ended request time is missing"),
        ("duplicated", "ended request time is duplicated"),
        ("before-request-id", "ended request time precedes request ID"),
    ),
)
def test_submission_visibility_requires_one_ended_time_after_request_id(
        tmp_path, mutation, signature):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-ended-time-" + mutation, CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    ended_line = "    Ended Request Time   = (none)\n"
    stdout = mutant["jobs"][0]["qstat_visibility"]["stdout"]
    assert stdout.count(ended_line) == 1
    if mutation == "missing":
        stdout = stdout.replace(ended_line, "", 1)
    elif mutation == "duplicated":
        stdout = stdout.replace(ended_line, ended_line * 2, 1)
    else:
        stdout = ended_line + stdout.replace(ended_line, "", 1)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] = stdout
    with pytest.raises(A2.CertificationError, match=signature):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_rejects_disappearance_with_visible_block(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-visible-and-disappeared", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] += (
        "Batch Request: 945411.nqsv does not exist on nqsv.\n")
    with pytest.raises(
            A2.CertificationError,
            match="contains a disappeared request signature"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_rejects_receipt_state_mismatch(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-receipt-state-mismatch", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["state"] = "RUN"
    with pytest.raises(
            A2.CertificationError,
            match="receipt state differs from canonical stdout state"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_rejects_finished_request_stdout(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-finished-request", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] = mutant[
        "jobs"][0]["qstat_visibility"]["stdout"].replace(
            "Current State           = Staging",
            "Current State           = Completed",
            1,
        )
    with pytest.raises(A2.CertificationError, match="contains a terminal state"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


@pytest.mark.parametrize(
    ("raw_state", "signature"),
    NON_ACCEPTED_VISIBILITY_VOCABULARY,
)
def test_submission_visibility_rejects_nonaccepted_vocabulary(
        tmp_path, raw_state, signature):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-vocab-" + raw_state.casefold(), CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] = mutant[
        "jobs"][0]["qstat_visibility"]["stdout"].replace(
            "Current State           = Staging",
            "Current State           = " + raw_state,
            1,
        )
    with pytest.raises(A2.CertificationError, match=signature):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_vocabulary_sets_are_nonvacuous_and_exact():
    assert NON_ACCEPTED_VISIBILITY_VOCABULARY
    assert {item[0] for item in NON_ACCEPTED_VISIBILITY_VOCABULARY} == {
        "Held", "Suspended"}
    assert A2._SUBMISSION_VISIBLE_STATES == frozenset({"QUE", "RUN"})


def test_submission_visibility_requires_timestamped_nonterminal_state(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-missing-timestamp", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)

    missing_time = copy.deepcopy(submission)
    missing_time["jobs"][0]["qstat_visibility"].pop("observed_at_utc")
    with pytest.raises(A2.CertificationError, match="qstat visibility"):
        A2._validate_submission_receipt(
            policy, missing_time, root.name, root, CURRENT_PIN)


def test_m11_materializer_stages_marker_before_single_noreplace_rename(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-m11", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    report = A2.collect_results(
        policy, evidence["raw_results"], attempt_id=root.name,
        current_pin=CURRENT_PIN, request_ids=evidence["request_ids"],
        frozen_files=evidence["raw_files"], attempt_root=root)
    report["source_commit"] = evidence["source_commit"]
    repo = tmp_path / "repo"
    repo.mkdir()
    original = A2._rename_noreplace
    rename_calls = []

    def observed_rename(source, destination):
        rename_calls.append((source, destination))
        assert (source / "COMPLETE.json").is_file()
        assert (source / "certification.json").is_file()
        assert (source / "artifact-manifest.json").is_file()
        original(source, destination)

    monkeypatch.setattr(A2, "_rename_noreplace", observed_rename)
    destination = A2.materialize(policy, report, evidence, repo_root=repo)
    assert len(rename_calls) == 1
    assert (destination / "COMPLETE.json").is_file()
    assert sorted(path.name for path in destination.iterdir()) == [
        "COMPLETE.json", "acquisition-receipt.json", "artifact-manifest.json",
        "certification.json", "completion-receipt.json",
        "condition-gate-rr5.admissions.jsonl",
        "condition-gate-rr50.admissions.jsonl",
        "raw-manifest.json", "submission-receipt.json",
    ]
    materialized = json.loads(
        (destination / "certification.json").read_text(encoding="utf-8"))
    assert base64.b64decode(materialized["policy_bytes_base64"]) == policy.raw_bytes

    v2_report = copy.deepcopy(report)
    v2_report["schema_version"] = "paper-story-a2-certification-result/v2"
    v2_repo = tmp_path / "v2-repo"
    v2_repo.mkdir()
    with pytest.raises(A2.CertificationError, match="identity differ"):
        A2.materialize(policy, v2_report, evidence, repo_root=v2_repo)
    assert not (v2_repo / policy.tracked_destination).exists()


def _materialization_case(tmp_path, attempt_id):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, attempt_id, CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    report = A2.collect_results(
        policy, evidence["raw_results"], attempt_id=root.name,
        current_pin=CURRENT_PIN, request_ids=evidence["request_ids"],
        frozen_files=evidence["raw_files"], attempt_root=root)
    report["source_commit"] = evidence["source_commit"]
    repo = tmp_path / "repo"
    repo.mkdir()
    return policy, report, evidence, repo


def _rewrite_preregistration(attempt_root, mutation):
    path = attempt_root / "preregistration.json"
    preregistration, _ = A2._read_json(path)
    mutation(preregistration)
    path.write_bytes(A2._canonical_json(preregistration))


def _add_raw_result_footprint(policy, attempt_root, workload_id=None):
    selected = workload_id or A2.workload_ids(policy)[0]
    raw_root = A2.workload_job_root(policy, attempt_root, selected) / "raw"
    raw_root.mkdir()
    (raw_root / "result.json").write_bytes(b"{}\n")


@pytest.mark.parametrize(
    "mutation",
    (
        "automatic-true",
        "automatic-missing",
        "automatic-non-bool",
        "extra-key",
        "other-key-missing",
    ),
)
def test_materialize_rejects_invalid_preregistration_on_production_path(
        tmp_path, mutation):
    policy, report, evidence, repo = _materialization_case(
        tmp_path, "materialize-preregistration-" + mutation)
    attempt_root = Path(evidence["attempt_root"])

    def mutate(preregistration):
        if mutation == "automatic-true":
            preregistration["automatic_retry"] = True
        elif mutation == "automatic-missing":
            preregistration.pop("automatic_retry")
        elif mutation == "automatic-non-bool":
            preregistration["automatic_retry"] = "false"
        elif mutation == "extra-key":
            preregistration["unexpected"] = False
        else:
            preregistration.pop("protocol_sha256")

    _rewrite_preregistration(attempt_root, mutate)
    destination = repo / policy.tracked_destination
    with pytest.raises(A2.CertificationError):
        A2.materialize(policy, report, evidence, repo_root=repo)
    assert not destination.exists()
    assert not list(destination.parent.glob(f".{destination.name}.stage-*"))


def test_materialize_normalizes_short_and_full_commit_to_one_cohort(tmp_path):
    policy, report, evidence, repo = _materialization_case(
        tmp_path, "materialize-full-pin")
    target_root = Path(evidence["attempt_root"])
    full_pin = "511c953" + "8" * 33
    _rewrite_preregistration(
        target_root,
        lambda preregistration: preregistration.__setitem__(
            "current_pin", full_pin),
    )
    sibling = A2.preregister_attempt(
        policy, "materialize-short-pin", "511c953")
    _add_raw_result_footprint(policy, sibling)

    assert A2._normalize_cohort_pin(full_pin) == "511c953"
    with pytest.raises(A2.CertificationError) as raised:
        A2.materialize(policy, report, evidence, repo_root=repo)
    assert "materialize-short-pin" in str(raised.value)
    assert "jobs/rr5/raw/regular-file" in str(raised.value)


def test_materialize_ignores_result_from_different_policy_cohort(tmp_path):
    policy, report, evidence, repo = _materialization_case(
        tmp_path, "materialize-current-policy")
    sibling = A2.preregister_attempt(
        policy, "materialize-old-policy", CURRENT_PIN)
    _rewrite_preregistration(
        sibling,
        lambda preregistration: preregistration.__setitem__(
            "policy_sha256", "f" * 64),
    )
    _add_raw_result_footprint(policy, sibling)

    destination = A2.materialize(
        policy, report, evidence, repo_root=repo)
    assert destination == repo / policy.tracked_destination
    assert (destination / "COMPLETE.json").is_file()


def test_materialize_rejects_second_result_before_creating_stage(tmp_path):
    policy, report, evidence, repo = _materialization_case(
        tmp_path, "materialize-second-result")
    sibling = A2.preregister_attempt(
        policy, "materialize-first-result", CURRENT_PIN)
    A2.write_json_x(sibling / "receipts" / "acquisition.json", {"result": 1})
    _add_raw_result_footprint(policy, sibling)
    destination = repo / policy.tracked_destination

    with pytest.raises(A2.CertificationError) as raised:
        A2.materialize(policy, report, evidence, repo_root=repo)
    message = str(raised.value)
    assert "sibling_attempt_id='materialize-first-result'" in message
    assert "receipts/acquisition.json" in message
    assert "jobs/rr5/raw/regular-file" in message
    assert not destination.exists()
    assert not list(destination.parent.glob(f".{destination.name}.stage-*"))


def test_materialize_counts_completion_only_as_sibling_result(tmp_path):
    policy, report, evidence, repo = _materialization_case(
        tmp_path, "materialize-after-completion")
    sibling = A2.preregister_attempt(
        policy, "materialize-completion-only", CURRENT_PIN)
    A2.write_json_x(sibling / "receipts" / "completion.json", {"result": 1})

    with pytest.raises(A2.CertificationError) as raised:
        A2.materialize(policy, report, evidence, repo_root=repo)
    assert "materialize-completion-only" in str(raised.value)
    assert "receipts/completion.json" in str(raised.value)


def test_materialize_allows_resultless_preregistered_sibling(
        tmp_path, monkeypatch):
    policy, report, evidence, repo = _materialization_case(
        tmp_path, "materialize-valid-retry")
    sibling = A2.preregister_attempt(
        policy, "materialize-resultless-predecessor", CURRENT_PIN)
    A2.write_json_x(sibling / "receipts" / "submission.json", {"submitted": True})
    for workload_id in A2.workload_ids(policy):
        (A2.workload_job_root(policy, sibling, workload_id) / "raw").mkdir()

    real_result_footprints = A2._result_footprints
    observed = []

    def observe_result_footprints(observed_policy, observed_root):
        footprints = real_result_footprints(observed_policy, observed_root)
        observed.append((observed_root, footprints))
        return footprints

    monkeypatch.setattr(A2, "_result_footprints", observe_result_footprints)
    destination = A2.materialize(
        policy, report, evidence, repo_root=repo)
    assert destination == repo / policy.tracked_destination
    assert (destination / "COMPLETE.json").is_file()
    assert observed == [(sibling, ())]


@pytest.mark.parametrize(
    "mutation",
    (
        "fixed-symlink",
        "fixed-fifo",
        "fixed-directory",
        "raw-symlink",
        "raw-file",
    ),
)
def test_materialize_invalid_sibling_footprint_reports_identity_and_path(
        tmp_path, mutation):
    policy, report, evidence, repo = _materialization_case(
        tmp_path, "materialize-invalid-sibling-footprint-" + mutation)
    sibling = A2.preregister_attempt(
        policy, "invalid-sibling-footprint-" + mutation, CURRENT_PIN)
    if mutation.startswith("fixed-"):
        problem_path = sibling / "receipts" / "acquisition.json"
        if mutation == "fixed-symlink":
            symlink_target = tmp_path / "fixed-footprint-symlink-target"
            symlink_target.write_bytes(b"{}\n")
            problem_path.symlink_to(symlink_target)
        elif mutation == "fixed-fifo":
            os.mkfifo(problem_path)
        else:
            problem_path.mkdir()
    else:
        problem_path = (
            A2.workload_job_root(policy, sibling, A2.workload_ids(policy)[0])
            / "raw"
        )
        if mutation == "raw-symlink":
            symlink_target = tmp_path / "raw-footprint-symlink-target"
            symlink_target.mkdir()
            problem_path.symlink_to(symlink_target, target_is_directory=True)
        else:
            problem_path.write_bytes(b"not a directory\n")

    with pytest.raises(A2.CertificationError) as direct:
        A2._result_footprints(policy, sibling)
    assert "sibling_attempt_id" not in str(direct.value)

    with pytest.raises(A2.CertificationError) as raised:
        A2.materialize(policy, report, evidence, repo_root=repo)
    message = str(raised.value)
    assert f"sibling_attempt_id={sibling.name!r}" in message
    assert f"problem_path={str(problem_path)!r}" in message


@pytest.mark.parametrize(
    "mutation",
    (
        "symlink",
        "regular-file",
        "malformed-name",
        "preregistration-missing",
        "preregistration-corrupt",
        "preregistration-key-missing",
        "permission-error",
    ),
)
def test_materialize_census_is_fail_closed(
        tmp_path, monkeypatch, mutation):
    policy, report, evidence, repo = _materialization_case(
        tmp_path, "materialize-census-target-" + mutation)
    base = policy.durable_base
    if mutation == "symlink":
        target = tmp_path / "census-symlink-target"
        target.mkdir()
        (base / "census-symlink").symlink_to(
            target, target_is_directory=True)
    elif mutation == "regular-file":
        (base / "census-regular-file").write_bytes(b"not an attempt\n")
    elif mutation == "malformed-name":
        (base / "not an attempt").mkdir()
    elif mutation == "preregistration-missing":
        (base / "census-preregistration-missing").mkdir()
    elif mutation == "preregistration-corrupt":
        sibling = base / "census-preregistration-corrupt"
        sibling.mkdir()
        (sibling / "preregistration.json").write_bytes(b"{not-json}\n")
    elif mutation == "preregistration-key-missing":
        sibling = A2.preregister_attempt(
            policy, "census-preregistration-key-missing", CURRENT_PIN)
        _rewrite_preregistration(
            sibling,
            lambda preregistration: preregistration.pop("study"),
        )
    else:
        real_scandir = A2.os.scandir

        def deny_durable_census(path):
            if Path(path) == base:
                raise PermissionError(errno.EACCES, "permission denied", path)
            return real_scandir(path)

        monkeypatch.setattr(A2.os, "scandir", deny_durable_census)

    destination = repo / policy.tracked_destination
    with pytest.raises(A2.CertificationError):
        A2.materialize(policy, report, evidence, repo_root=repo)
    assert not destination.exists()
    assert not list(destination.parent.glob(f".{destination.name}.stage-*"))


def test_materialize_einval_uses_exclusive_claim_and_flags_zero_rename(
        tmp_path, monkeypatch):
    policy, report, evidence, repo = _materialization_case(
        tmp_path, "materialize-einval-positive")
    destination = repo / policy.tracked_destination
    claim = destination.parent / f".{destination.name}.publish-claim"
    rename_calls = []
    fsync_calls = []
    original_flags_zero = A2._rename_flags_zero
    original_fsync_dir = A2._fsync_dir

    def unsupported_noreplace(_source, _destination):
        raise OSError(errno.EINVAL, "unsupported no-replace")

    def observed_flags_zero(source, target):
        rename_calls.append((source, target))
        assert claim.is_file() and not claim.is_symlink()
        assert not target.exists()
        original_flags_zero(source, target)

    def observed_fsync(path):
        fsync_calls.append(path)
        original_fsync_dir(path)

    monkeypatch.setattr(A2, "_rename_noreplace", unsupported_noreplace)
    monkeypatch.setattr(A2, "_rename_flags_zero", observed_flags_zero)
    monkeypatch.setattr(A2, "_fsync_dir", observed_fsync)

    assert A2.materialize(
        policy, report, evidence, repo_root=repo) == destination
    assert len(rename_calls) == 1
    assert not claim.exists()
    assert (destination / "COMPLETE.json").is_file()
    assert fsync_calls.count(destination.parent) == 4


def test_materialize_einval_refuses_destination_created_before_recheck(
        tmp_path, monkeypatch):
    policy, report, evidence, repo = _materialization_case(
        tmp_path, "materialize-einval-destination")
    destination = repo / policy.tracked_destination
    claim = destination.parent / f".{destination.name}.publish-claim"

    def destination_race(_source, target):
        target.mkdir()
        (target / "non-cooperating-writer").write_text(
            "preserve\n", encoding="utf-8")
        raise OSError(errno.EINVAL, "unsupported no-replace")

    monkeypatch.setattr(A2, "_rename_noreplace", destination_race)
    with pytest.raises(
            A2.CertificationError, match="destination already exists"):
        A2.materialize(policy, report, evidence, repo_root=repo)

    assert (destination / "non-cooperating-writer").read_text(
        encoding="utf-8") == "preserve\n"
    assert not claim.exists()
    assert not list(destination.parent.glob(f".{destination.name}.stage-*"))


def test_materialize_einval_fails_closed_on_publish_claim_collision(
        tmp_path, monkeypatch):
    policy, report, evidence, repo = _materialization_case(
        tmp_path, "materialize-einval-claim-collision")
    destination = repo / policy.tracked_destination
    destination.parent.mkdir(parents=True)
    claim = destination.parent / f".{destination.name}.publish-claim"
    claim.write_text("other cooperating publisher\n", encoding="utf-8")

    def unsupported_noreplace(_source, _destination):
        raise OSError(errno.EINVAL, "unsupported no-replace")

    monkeypatch.setattr(A2, "_rename_noreplace", unsupported_noreplace)
    with pytest.raises(
            A2.CertificationError, match="exclusive fallback.*claim failed"):
        A2.materialize(policy, report, evidence, repo_root=repo)

    assert claim.read_text(encoding="utf-8") == "other cooperating publisher\n"
    assert not destination.exists()
    assert not list(destination.parent.glob(f".{destination.name}.stage-*"))


def test_materialize_non_einval_publish_error_does_not_enter_fallback(
        tmp_path, monkeypatch):
    policy, report, evidence, repo = _materialization_case(
        tmp_path, "materialize-non-einval")
    destination = repo / policy.tracked_destination

    def failed_noreplace(_source, _destination):
        raise OSError(errno.EIO, "I/O failure")

    def forbidden_fallback(_source, _destination):
        raise AssertionError("non-EINVAL entered fallback")

    monkeypatch.setattr(A2, "_rename_noreplace", failed_noreplace)
    monkeypatch.setattr(A2, "_publish_staging_after_einval", forbidden_fallback)
    with pytest.raises(OSError) as raised:
        A2.materialize(policy, report, evidence, repo_root=repo)

    assert raised.value.errno == errno.EIO
    assert not destination.exists()
    assert not list(destination.parent.glob(f".{destination.name}.stage-*"))


def test_materialize_noreplace_success_does_not_enter_fallback(
        tmp_path, monkeypatch):
    policy, report, evidence, repo = _materialization_case(
        tmp_path, "materialize-noreplace-success")
    destination = repo / policy.tracked_destination
    rename_calls = []

    def successful_noreplace(source, target):
        rename_calls.append((source, target))
        os.rename(source, target)

    def forbidden_fallback(_source, _destination):
        raise AssertionError("successful RENAME_NOREPLACE entered fallback")

    monkeypatch.setattr(A2, "_rename_noreplace", successful_noreplace)
    monkeypatch.setattr(A2, "_publish_staging_after_einval", forbidden_fallback)

    assert A2.materialize(
        policy, report, evidence, repo_root=repo) == destination
    assert len(rename_calls) == 1
    assert (destination / "COMPLETE.json").is_file()


def test_m12_attempt_root_must_be_direct_child_of_pinned_durable_base(tmp_path):
    policy = _policy(tmp_path)
    outside = tmp_path / "arbitrary-repo-external" / "attempt"
    outside.mkdir(parents=True)
    with pytest.raises(A2.CertificationError, match="pinned durable base"):
        A2.validate_attempt_root(policy, outside)


def test_m12_durable_base_rejects_symlinked_ancestor(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    document = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    document["durable_measurement_base"] = str(alias / "a2")
    path = tmp_path / "symlink-policy.json"
    path.write_text(json.dumps(document) + "\n", encoding="utf-8")
    policy = A2.load_policy(path)
    with pytest.raises(A2.CertificationError, match="symlink"):
        A2.create_attempt_root(policy, "attempt-symlink")


def test_correctness_requires_every_ratified_repetition(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-repetitions")
    results = _positive_results(policy, root)
    assert len(results[0]["correctness"][PERFORMANCE_TAG]) == 5
    results[0]["correctness"][PERFORMANCE_TAG].pop()
    report = A2.collect_results(
        policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_ids={"rr5": "reps-a.nqsv", "rr50": "reps-b.nqsv"},
        _test_token=A2._COLLECT_TEST_TOKEN)
    assert report["cells"][0]["correctness"]["status"] == "indeterminate"
    assert report["status"] == "indeterminate"


def test_nonfinite_json_and_samples_are_fail_closed(tmp_path):
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text('{"sample":NaN}\n', encoding="utf-8")
    with pytest.raises(A2.CertificationError, match="non-finite"):
        A2._read_json(nonfinite)

    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-infinity")
    results = _positive_results(policy, root)
    results[0]["performance"]["samples_tps"][0] = float("inf")
    report = A2.collect_results(
        policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_ids={"rr5": "finite-a.nqsv", "rr50": "finite-b.nqsv"},
        _test_token=A2._COLLECT_TEST_TOKEN)
    assert report["status"] == "performance-indeterminate"
    assert report["effects"] == {"rr50": pytest.approx(0.1)}


@pytest.mark.parametrize(
    "case_name,driver_rc,claim_manifest",
    (("authority-none", {"rr5": 7, "rr50": 9}, False),
     ("manifestless-full", 0, False)),
)
def test_collector_never_calls_positive_path_for_failed_or_manifestless_compute(
        tmp_path, monkeypatch, case_name, driver_rc, claim_manifest):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, f"attempt-collector-{case_name}", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(
        policy, root, driver_rc=driver_rc, claim_manifest=claim_manifest)
    monkeypatch.setattr(A2, "load_policy", lambda: policy)
    positive_calls = []
    monkeypatch.setattr(
        A2, "collect_results",
        lambda *args, **kwargs: positive_calls.append((args, kwargs)),
    )
    captured = {}

    def materialize(_policy, report, _evidence, *, repo_root):
        captured.update(report)
        return Path(repo_root) / "captured"

    monkeypatch.setattr(A2, "materialize", materialize)
    args = type("Args", (), {
        "policy": None,
        "acquisition_receipt": str(acquisition),
        "current_pin": CURRENT_PIN,
        "attempt_root": str(root),
        "repo_root": str(tmp_path),
    })()
    if case_name == "manifestless-full":
        with pytest.raises(A2.AuthorityError, match="raw manifest authority"):
            A2._collect_command(args)
        assert positive_calls == []
        assert captured == {}
        return
    assert A2._collect_command(args) == 2
    assert positive_calls == []
    assert captured["status"] == "indeterminate"


def test_completion_driver_rc_request_and_pin_are_bound_to_compute_result(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-compute-binding", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    compute = root / "jobs" / "rr5" / "compute-result.json"
    compute.write_text(
        json.dumps({
            "schema_version": A2.COMPUTE_RESULT_SCHEMA,
            "workload": "rr5",
            "driver_rc": 0,
            "pbs_jobid": "different.nqsv",
            "current_pin": CURRENT_PIN,
        }) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(A2.CertificationError, match="compute result"):
        A2.validate_acquisition_bundle(
            policy, acquisition, current_pin=CURRENT_PIN)


@pytest.mark.parametrize(
    "terminal_reason",
    ("scheduler-end-state", "request-disappeared-after-visibility"),
)
def test_completion_accepts_both_canonical_terminal_observations(
        tmp_path, terminal_reason):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-terminal-" + terminal_reason, CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(
        policy, root, terminal_reason=terminal_reason)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert evidence["raw_manifest_valid"] is True
    if terminal_reason == "request-disappeared-after-visibility":
        assert evidence["completion"]["jobs"][0]["terminal_observation"]["stdout"] == (
            "Batch Request: 945411.nqsv does not exist on nqsv.\n")


@pytest.mark.parametrize(
    "mutation", ("empty-output", "visible-output", "nonzero-rc", "stderr"),
)
def test_disappeared_terminal_rejects_noncanonical_observations(
        tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-disappeared-negative-" + mutation, CURRENT_PIN)
    _, submission = _write_receipt_bundle(
        policy, root, terminal_reason="request-disappeared-after-visibility")
    completion, _ = A2._read_json(root / "receipts" / "completion.json")
    terminal = completion["jobs"][0]["terminal_observation"]
    if mutation == "empty-output":
        terminal["stdout"] = ""
    elif mutation == "visible-output":
        terminal["stdout"] = "Request ID: 945411.nqsv\nRequest State = RUN\n"
    elif mutation == "nonzero-rc":
        terminal["returncode"] = 1
    else:
        terminal["stderr"] = "qstat failed\n"
    submission_binding = A2._validate_submission_receipt(
        policy, submission, root.name, root, CURRENT_PIN)
    with pytest.raises(A2.CertificationError):
        A2._validate_completion_receipt(
            policy, completion, root.name, root, CURRENT_PIN,
            submission_binding,
        )


def test_raw_manifest_binds_campaign_lock_and_wal_and_freezes_raw_bytes(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-frozen", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert len(evidence["raw_files"]) == 12
    raw_path = root / "jobs" / "rr5" / "raw" / "rr5-stock.json"
    raw_path.write_text('{"tampered":true}\n', encoding="utf-8")
    report = A2.collect_results(
        policy, evidence["raw_results"], attempt_id=root.name,
        current_pin=CURRENT_PIN, request_ids=evidence["request_ids"],
        frozen_files=evidence["raw_files"], attempt_root=root)
    assert report["status"] == "observed-positive"
    assert report["independent_observation_limits"]["correctness_run_argv"] \
        == "not-recorded-by-existing-pipeline"

    direct_root = A2.preregister_attempt(
        policy, "attempt-finalizer-direct", CURRENT_PIN)
    _write_receipt_bundle(policy, direct_root, claim_manifest=False)
    noise = direct_root / "jobs" / "not-a-policy-workload" / "raw"
    noise.mkdir(parents=True)
    (noise / "decoy.json").write_text("{}\n", encoding="utf-8")
    assert A2.finalize_raw_manifest(
        policy, direct_root, CURRENT_PIN).is_file()

    polluted_root = A2.preregister_attempt(
        policy, "attempt-job-local-raw-extra", CURRENT_PIN)
    _write_receipt_bundle(policy, polluted_root, claim_manifest=False)
    (polluted_root / "jobs" / "rr5" / "raw" / "decoy.json").write_text(
        "{}\n", encoding="utf-8")
    with pytest.raises(A2.CertificationError, match="inventory is not closed"):
        A2.finalize_raw_manifest(policy, polluted_root, CURRENT_PIN)

    consumer_root = A2.preregister_attempt(
        policy, "attempt-consumer-raw-extra", CURRENT_PIN)
    consumer_acquisition, _ = _write_receipt_bundle(policy, consumer_root)
    (consumer_root / "jobs" / "rr50" / "raw" / "decoy.json").write_text(
        "{}\n", encoding="utf-8")
    consumer_evidence = A2.validate_acquisition_bundle(
        policy, consumer_acquisition, current_pin=CURRENT_PIN)
    assert consumer_evidence["raw_manifest_valid"] is False
    assert "inventory is not closed" in consumer_evidence["raw_manifest_reason"]

    manifest_root = A2.preregister_attempt(
        policy, "attempt-manifest-inventory", CURRENT_PIN)
    _, manifest_submission = _write_receipt_bundle(policy, manifest_root)
    completion, _ = A2._read_json(
        manifest_root / "receipts" / "completion.json")
    submission_binding = A2._validate_submission_receipt(
        policy, manifest_submission, manifest_root.name, manifest_root,
        CURRENT_PIN)
    completion_binding = A2._validate_completion_receipt(
        policy, completion, manifest_root.name, manifest_root, CURRENT_PIN,
        submission_binding)
    manifest_path = Path(completion["raw_result_manifest"])
    manifest, _ = A2._read_json(manifest_path)
    manifest["files"]["jobs/rr5/raw/extra.json"] = "0" * 64
    mutant_path = manifest_root / "raw-manifest-mutant.json"
    A2.write_json_x(mutant_path, manifest)
    with pytest.raises(A2.CertificationError, match="inventory"):
        A2._load_raw_manifest_bundle(
            policy, mutant_path,
            hashlib.sha256(mutant_path.read_bytes()).hexdigest(),
            attempt_id=manifest_root.name, attempt_root=manifest_root,
            current_pin=CURRENT_PIN,
            job_bindings=completion_binding["jobs"],
        )

    raw = evidence["raw_results"][0]
    claim_path = Path(raw["campaign_evidence"]["claim_path"])
    claim = A2._decode_campaign_claim(claim_path.read_bytes(), "fixture claim")
    binding = reservation.read_binding(
        evidence["reservation_results"]["rr5"]["environment"])
    A2._validate_claim_reservation_binding(
        claim, campaign_id=raw["campaign_evidence"]["campaign_id"],
        request_id="945411.nqsv", reservation_binding=binding,
        expected_protocol_digest=claim["protocol_digest"])
    mutant_claim = dict(claim)
    mutant_claim["protocol_digest"] = "0" * 64
    with pytest.raises(A2.CertificationError, match="protocol digest"):
        A2._campaign_observation(
            policy, policy.cell(raw["cell_id"]),
            str(Path(raw["campaign_evidence"]["lock_path"]).parent),
            root.name, CURRENT_PIN,
            claim_bytes=A2._canonical_json(mutant_claim))
    with pytest.raises(A2.CertificationError, match="protocol digest"):
        A2._validate_claim_reservation_binding(
            mutant_claim,
            campaign_id=raw["campaign_evidence"]["campaign_id"],
            request_id="945411.nqsv", reservation_binding=binding,
            expected_protocol_digest=claim["protocol_digest"])

    mutant_claim = dict(claim)
    mutant_claim["job_id"] = "another-request.nqsv"
    with pytest.raises(A2.CertificationError, match="submission or reservation"):
        A2._validate_claim_reservation_binding(
            mutant_claim,
            campaign_id=raw["campaign_evidence"]["campaign_id"],
            request_id="945411.nqsv", reservation_binding=binding,
            expected_protocol_digest=claim["protocol_digest"])

    failed_root = A2.preregister_attempt(
        policy, "attempt-one-driver-failed", CURRENT_PIN)
    failed_acquisition, failed_submission = _write_receipt_bundle(
        policy, failed_root, driver_rc=7, claim_manifest=False,
        force_legacy_v3=True)
    failed_evidence = A2.validate_acquisition_bundle(
        policy, failed_acquisition, current_pin=CURRENT_PIN)
    assert failed_evidence["driver_rcs"] == {"rr5": 7, "rr50": 0}
    failed_completion, _ = A2._read_json(
        failed_root / "receipts" / "completion.json")
    decoy = failed_root / "decoy-manifest.json"
    A2.write_json_x(decoy, {"decoy": True})
    failed_completion["raw_result_manifest"] = str(decoy)
    failed_completion["raw_result_manifest_sha256"] = hashlib.sha256(
        decoy.read_bytes()).hexdigest()
    failed_submission_binding = A2._validate_submission_receipt(
        policy, failed_submission, failed_root.name, failed_root, CURRENT_PIN)
    with pytest.raises(A2.CertificationError, match="failed group"):
        A2._validate_completion_receipt(
            policy, failed_completion, failed_root.name, failed_root,
            CURRENT_PIN, failed_submission_binding)


def test_changed_campaign_wal_invalidates_the_manifest_bundle(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-wal-change", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    raw, _ = A2._read_json(
        root / "jobs" / "rr5" / "raw" / "rr5-stock.json")
    wal_path = Path(raw["campaign_evidence"]["wal_path"])
    with wal_path.open("ab") as stream:
        stream.write(b"{}\n")
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert evidence["raw_manifest_valid"] is False
    assert "hash mismatch" in evidence["raw_manifest_reason"]


@pytest.mark.parametrize(
    "error_number", [errno.EINVAL, errno.ENOSYS, errno.ENOTSUP])
def test_atomic_write_bytes_noreplace_unsupported_rename_uses_link_unlink(
        tmp_path, monkeypatch, error_number):
    path = tmp_path / "receipt.jsonl"
    payload = b"exact receipt bytes\n"
    original_link = A2.os.link
    links = []

    def unsupported_rename(_source, _destination):
        raise OSError(error_number, os.strerror(error_number))

    def observed_link(source, destination, *, follow_symlinks=True):
        assert source.parent == destination.parent == tmp_path
        assert destination == path
        assert follow_symlinks is False
        links.append((source, destination))
        return original_link(
            source, destination, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(A2, "_rename_noreplace", unsupported_rename)
    monkeypatch.setattr(A2.os, "link", observed_link)

    A2._atomic_write_bytes_noreplace(path, payload)

    assert path.read_bytes() == payload
    assert len(links) == 1
    assert not list(tmp_path.glob(f".{path.name}.tmp-*"))


def test_atomic_write_bytes_noreplace_einval_refuses_existing_destination(
        tmp_path, monkeypatch):
    path = tmp_path / "receipt.jsonl"
    original_bytes = b"preexisting bytes\n"
    path.write_bytes(original_bytes)

    def unsupported_rename(_source, _destination):
        raise OSError(errno.EINVAL, os.strerror(errno.EINVAL))

    monkeypatch.setattr(A2, "_rename_noreplace", unsupported_rename)

    with pytest.raises(FileExistsError):
        A2._atomic_write_bytes_noreplace(path, b"replacement bytes\n")

    assert path.read_bytes() == original_bytes
    assert not list(tmp_path.glob(f".{path.name}.tmp-*"))


def test_atomic_write_bytes_noreplace_nonfallback_errno_propagates(
        tmp_path, monkeypatch):
    path = tmp_path / "receipt.jsonl"
    expected_error = OSError(errno.EACCES, os.strerror(errno.EACCES))

    def denied_rename(_source, _destination):
        raise expected_error

    def forbidden_link(*_args, **_kwargs):
        raise AssertionError("non-fallback errno reached os.link")

    monkeypatch.setattr(A2, "_rename_noreplace", denied_rename)
    monkeypatch.setattr(A2.os, "link", forbidden_link)

    with pytest.raises(OSError) as caught:
        A2._atomic_write_bytes_noreplace(path, b"rejected bytes\n")

    assert caught.value is expected_error
    assert caught.value.errno == errno.EACCES
    assert not path.exists()
    assert not list(tmp_path.glob(f".{path.name}.tmp-*"))


def test_atomic_write_bytes_noreplace_link_publish_survives_unlink_error(
        tmp_path, monkeypatch):
    path = tmp_path / "receipt.jsonl"
    payload = b"durable published bytes\n"
    original_unlink = Path.unlink

    def unsupported_rename(_source, _destination):
        raise OSError(errno.EINVAL, os.strerror(errno.EINVAL))

    def fail_staging_unlink(staging, *args, **kwargs):
        if (staging.parent == tmp_path
                and staging.name.startswith(f".{path.name}.tmp-")):
            raise OSError(errno.EIO, os.strerror(errno.EIO))
        return original_unlink(staging, *args, **kwargs)

    monkeypatch.setattr(A2, "_rename_noreplace", unsupported_rename)
    monkeypatch.setattr(Path, "unlink", fail_staging_unlink)

    A2._atomic_write_bytes_noreplace(path, payload)

    assert path.read_bytes() == payload
    staging = list(tmp_path.glob(f".{path.name}.tmp-*"))
    assert len(staging) == 1
    assert staging[0].read_bytes() == payload


def test_atomic_write_bytes_noreplace_einval_uses_create_only_hard_link(
        tmp_path, monkeypatch):
    path = tmp_path / "condition-gate-rr5.admissions.jsonl"
    payload = b'{"admitted":true}\n'
    link_calls = []
    original_link = A2.os.link

    def unsupported_noreplace(_source, _destination):
        raise OSError(errno.EINVAL, "unsupported no-replace")

    def observed_link(source, destination, *, follow_symlinks=True):
        assert source.parent == destination.parent == tmp_path
        assert destination == path
        original_link(
            source, destination, follow_symlinks=follow_symlinks)
        assert source.stat().st_ino == destination.stat().st_ino
        link_calls.append((source, destination))

    monkeypatch.setattr(A2, "_rename_noreplace", unsupported_noreplace)
    monkeypatch.setattr(A2.os, "link", observed_link)
    A2._atomic_write_bytes_noreplace(path, payload)

    assert link_calls and len(link_calls) == 1
    assert path.read_bytes() == payload
    assert not list(tmp_path.glob(f".{path.name}.tmp-*"))


def test_atomic_write_bytes_noreplace_einval_hard_link_refuses_existing_name(
        tmp_path, monkeypatch):
    path = tmp_path / "condition-gate-rr5.admissions.jsonl"
    original_bytes = b'{"writer":"first"}\n'
    path.write_bytes(original_bytes)

    def unsupported_noreplace(_source, _destination):
        raise OSError(errno.EINVAL, "unsupported no-replace")

    monkeypatch.setattr(A2, "_rename_noreplace", unsupported_noreplace)
    with pytest.raises(FileExistsError):
        A2._atomic_write_bytes_noreplace(path, b'{"writer":"second"}\n')

    assert path.read_bytes() == original_bytes
    assert not list(tmp_path.glob(f".{path.name}.tmp-*"))


def test_atomic_write_bytes_noreplace_non_einval_is_not_fallback(
        tmp_path, monkeypatch):
    path = tmp_path / "condition-gate-rr5.admissions.jsonl"

    def failed_noreplace(_source, _destination):
        raise OSError(errno.EIO, "I/O failure")

    monkeypatch.setattr(A2, "_rename_noreplace", failed_noreplace)
    with pytest.raises(OSError) as raised:
        A2._atomic_write_bytes_noreplace(path, b'{"admitted":true}\n')

    assert raised.value.errno == errno.EIO
    assert not path.exists()
    assert not list(tmp_path.glob(f".{path.name}.tmp-*"))


def test_condition_receipt_publish_is_atomic_noreplace_and_durable(
        tmp_path, monkeypatch):
    path = tmp_path / "condition-gate-rr5.admissions.jsonl"
    genome = A2._genome_for_cell(_policy(tmp_path), _policy(tmp_path).cells[0])
    evidence = source_digest.SourceEvidence(
        source_digest.SOURCE_EVIDENCE_SCHEMA,
        str(tmp_path.resolve()), CURRENT_PIN,
        hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest(),
        source_digest.STOCK, "a" * 64, True,
        source_digest.EMPTY_TRACKED_DIFF_SHA256, (),
    )
    admission = json.dumps({
        "admission_id": "condition-gate/admission/atomic",
        "admission_digest": "b" * 64,
        "use_class": "paper", "admitted": True,
        "record_ids": ["condition-record/atomic"],
        "unestablished_meaning_macros": [],
    }, sort_keys=True, separators=(",", ":"))
    events = []
    original_fsync = A2.os.fsync
    original_rename = A2._rename_noreplace

    def observed_fsync(descriptor):
        target = Path(f"/proc/self/fd/{descriptor}").resolve()
        events.append(("fsync", target))
        original_fsync(descriptor)

    def observed_rename(source, destination):
        assert source.parent == destination.parent == tmp_path
        assert destination == path
        assert source.is_file() and source.stat().st_size > 0
        assert events and events[-1] == ("fsync", source)
        if not destination.exists():
            assert not path.exists()
        events.append(("rename", source, destination))
        original_rename(source, destination)

    monkeypatch.setattr(A2.os, "fsync", observed_fsync)
    monkeypatch.setattr(A2, "_rename_noreplace", observed_rename)
    A2._write_condition_gate_admissions_x(
        path, [admission], [evidence])

    assert path.is_file()
    assert events[-1] == ("fsync", tmp_path)
    assert [event[0] for event in events] == ["fsync", "rename", "fsync"]
    original_bytes = path.read_bytes()
    with pytest.raises(FileExistsError):
        A2._write_condition_gate_admissions_x(
            path, [admission], [evidence])
    assert path.read_bytes() == original_bytes
    assert not list(tmp_path.glob(f".{path.name}.tmp-*"))


@pytest.mark.parametrize(
    ("mutation", "expected_status"),
    (("adopted-stock", "patch-unapplied"),
     ("missing-token", "token-missing"),
     ("legacy-v2", "patch-unapplied")),
)
def test_source_role_and_missing_token_are_determinate_cell_rejects(
        tmp_path, mutation, expected_status):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "source-reject-" + mutation)
    results = _positive_results(policy, root)
    target = results[1]
    if mutation == "adopted-stock":
        receipt_path = root / A2._condition_gate_receipt_relative("rr5")
        frames = receipt_path.read_bytes().splitlines(keepends=True)
        source_record = json.loads(frames[3])
        source_record["src_token"] = source_digest.STOCK
        frames[3] = A2._canonical_json(source_record)
        receipt_path.write_bytes(b"".join(frames))
        target["src_token"] = source_digest.STOCK
    elif mutation == "missing-token":
        target.pop("src_token")
    else:
        for raw in results:
            raw["schema_version"] = A2.LEGACY_RAW_RESULT_SCHEMA
            raw.pop("src_token")
    if mutation == "missing-token":
        with pytest.raises(A2.AuthorityError, match="raw src_token"):
            A2.collect_results(
                policy, results, attempt_id=root.name,
                current_pin=CURRENT_PIN, request_ids=_request_ids(policy),
                _test_token=A2._COLLECT_TEST_TOKEN)
        return
    report = A2.collect_results(
        policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_ids=_request_ids(policy),
        _test_token=A2._COLLECT_TEST_TOKEN)

    assert report["status"] == "reject"
    assert report["cells"]
    if mutation == "legacy-v2":
        assert {cell["source_binding_status"] for cell in report["cells"]} \
            == {"patch-unapplied"}
        assert all(cell["src_token"] is None for cell in report["cells"])
    else:
        cell = next(
            cell for cell in report["cells"]
            if cell["cell_id"] == target["cell_id"])
        assert cell["source_binding_status"] == expected_status


def test_patched_adopted_source_binding_positive_control(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "source-binding-positive")
    report = A2.collect_results(
        policy, _positive_results(policy, root), attempt_id=root.name,
        current_pin=CURRENT_PIN, request_ids=_request_ids(policy),
        _test_token=A2._COLLECT_TEST_TOKEN)

    assert report["status"] == "observed-positive"
    adopted = [cell for cell in report["cells"] if cell["role"] == "adopted"]
    assert adopted
    assert all(cell["source_binding_status"] == "bound" for cell in adopted)
    assert all(cell["src_token"] != source_digest.STOCK for cell in adopted)


def test_raw_token_is_checked_against_precampaign_receipt_not_itself(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "receipt-token-independent")
    results = _positive_results(policy, root)
    target = results[1]
    assert target["src_token"] != source_digest.STOCK
    target["src_token"] = source_digest.STOCK

    report = A2.collect_results(
        policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_ids=_request_ids(policy), attempt_root=root)

    target_cell = next(
        cell for cell in report["cells"]
        if cell["cell_id"] == target["cell_id"])
    assert report["status"] == "reject"
    assert target_cell["source_binding_status"] == "token-mismatch"


@pytest.mark.parametrize(
    ("mutation", "signature"),
    (("wal-token", "WAL build start token"),
     ("admission-token", "build admission token"),
     ("variant", "canonical cell variant")),
)
def test_precampaign_token_cross_checks_wal_admission_and_variant(
        tmp_path, mutation, signature):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "token-cross-" + mutation)
    results = _positive_results(policy, root)
    target = results[1]
    cell = policy.cell(target["cell_id"])
    expected_token = target["src_token"]
    wal_path = Path(target["campaign_evidence"]["wal_path"])
    if mutation != "variant":
        records = [
            wal.parse_line(frame.decode("utf-8"))
            for frame in wal_path.read_bytes().splitlines(keepends=True)
        ]
        rewritten = []
        changed = False
        for record in records:
            if (record.variant == target["variant"]
                    and record.stage == STAGE_BUILD_START):
                payload = copy.deepcopy(record.payload)
                if mutation == "wal-token":
                    payload["src_token"] = source_digest.STOCK
                else:
                    payload["build_admission"]["source"]["src_token"] = (
                        source_digest.STOCK)
                record = WalRecord(
                    variant=record.variant, stage=record.stage,
                    env_tag=record.env_tag, ts=record.ts, payload=payload)
                changed = True
            rewritten.append(record)
        assert changed
        wal_path.write_text(
            "".join(wal._record_to_line(record) + "\n" for record in rewritten),
            encoding="utf-8")
    result_variant = (
        variant_id(A2._genome_for_cell(policy, cell), source_digest.STOCK)
        if mutation == "variant" else target["variant"])
    with pytest.raises(A2.CertificationError, match=signature):
        A2._raw_cell_from_wal(
            policy, cell,
            result=A2.SimpleNamespace(variant=result_variant),
            layout_root=str(wal_path.parents[1]), attempt_id=root.name,
            current_pin=CURRENT_PIN, expected_src_token=expected_token)


@pytest.mark.parametrize("mutation", ("missing", "changed"))
def test_manifest_bound_condition_receipt_is_required_and_hash_checked(
        tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "condition-receipt-" + mutation, CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    receipt = root / A2._condition_gate_receipt_relative("rr5")
    if mutation == "missing":
        receipt.unlink()
    else:
        receipt.write_bytes(receipt.read_bytes() + b" ")

    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert evidence["raw_manifest_valid"] is False
    assert "manifest member" in evidence["raw_manifest_reason"]


@pytest.mark.parametrize(
    "mutation",
    (
        "receipt-file-missing",
        "receipt-corrupt",
        "receipt-token-missing",
        "receipt-token-invalid",
        "receipt-hash-mismatch",
        "raw-token-missing",
        "raw-token-invalid",
    ),
)
def test_source_authority_failure_stops_before_tracked_artifact(
        tmp_path, monkeypatch, mutation):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "authority-hard-stop-" + mutation, CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)

    if mutation.startswith("receipt-"):
        relative = A2._condition_gate_receipt_relative("rr5")
        receipt = root / relative
        if mutation == "receipt-file-missing":
            receipt.unlink()
        elif mutation == "receipt-corrupt":
            receipt.write_bytes(b"{not-json}\n")
            _reseal_manifest_member_and_receipts(root, relative)
        elif mutation == "receipt-hash-mismatch":
            receipt.write_bytes(receipt.read_bytes() + b" ")
        else:
            frames = receipt.read_bytes().splitlines(keepends=True)
            source_record = json.loads(frames[1])
            if mutation == "receipt-token-missing":
                source_record.pop("src_token")
            else:
                source_record["src_token"] = "not-a-token"
            frames[1] = A2._canonical_json(source_record)
            receipt.write_bytes(b"".join(frames))
            _reseal_manifest_member_and_receipts(root, relative)
    else:
        relative = "jobs/rr5/raw/rr5-fixed10.json"
        raw_path = root / relative
        raw, _ = A2._read_json(raw_path)
        if mutation == "raw-token-missing":
            raw.pop("src_token")
        else:
            raw["src_token"] = "not-a-token"
        raw_path.write_bytes(A2._canonical_json(raw))
        _reseal_manifest_member_and_receipts(root, relative)

    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    if mutation.startswith("receipt-"):
        assert evidence["raw_manifest_valid"] is False
        assert evidence["raw_manifest_invalid_kind"] == "authority"
    else:
        with pytest.raises(A2.AuthorityError, match="raw src_token"):
            A2.collect_results(
                policy, evidence["raw_results"], attempt_id=root.name,
                current_pin=CURRENT_PIN, request_ids=evidence["request_ids"],
                frozen_files=evidence["raw_files"], attempt_root=root)

    monkeypatch.setattr(A2, "load_policy", lambda: policy)
    repo = tmp_path / "authority-hard-stop-repo"
    repo.mkdir()
    assert A2.main([
        "collect", "--attempt-root", str(root),
        "--current-pin", CURRENT_PIN,
        "--acquisition-receipt", str(acquisition),
        "--repo-root", str(repo),
    ]) == 2
    assert not (repo / policy.tracked_destination).exists()


def test_full_and_legacy_partial_manifest_identifiers_and_loaders_are_distinct(
        tmp_path):
    policy = _policy(tmp_path)
    assert A2.RAW_MANIFEST_SCHEMA == "paper-story-a2-full-raw-manifest/v4"
    assert A2.LEGACY_PARTIAL_RAW_MANIFEST_SCHEMA == (
        "paper-story-a2-raw-manifest/v4")
    assert A2.RAW_MANIFEST_SCHEMA != A2.LEGACY_PARTIAL_RAW_MANIFEST_SCHEMA

    full_root = A2.preregister_attempt(
        policy, "schema-distinct-full", CURRENT_PIN)
    full_acquisition, full_submission = _write_receipt_bundle(
        policy, full_root)
    full_evidence = A2.validate_acquisition_bundle(
        policy, full_acquisition, current_pin=CURRENT_PIN)
    full_manifest_path = full_root / "raw-manifest.json"
    full_manifest, _ = A2._read_json(full_manifest_path)
    assert full_manifest["schema_version"] == A2.RAW_MANIFEST_SCHEMA
    full_submission_binding = A2._validate_submission_receipt(
        policy, full_submission, full_root.name, full_root, CURRENT_PIN)
    full_completion, _ = A2._read_json(
        full_root / "receipts" / "completion.json")
    full_completion_binding = A2._validate_completion_receipt(
        policy, full_completion, full_root.name, full_root, CURRENT_PIN,
        full_submission_binding)
    assert full_evidence["raw_manifest_valid"] is True

    partial_root = A2.preregister_attempt(
        policy, "schema-distinct-legacy-partial", CURRENT_PIN)
    _, partial_submission = _write_receipt_bundle(
        policy, partial_root, driver_rc=7, record_completion=False)
    _, partial_acquisition = A2.finish_group(
        policy, partial_root, CURRENT_PIN, qstat_runner=_terminal_qstat)
    partial_submission_binding = A2._validate_submission_receipt(
        policy, partial_submission, partial_root.name, partial_root,
        CURRENT_PIN)
    partial_completion, _ = A2._read_json(
        partial_root / "receipts" / "completion.json")
    partial_completion_binding = A2._validate_completion_receipt(
        policy, partial_completion, partial_root.name, partial_root,
        CURRENT_PIN, partial_submission_binding)
    partial_manifest, _ = A2._read_json(
        partial_root / "raw-manifest.json")
    successful_workload = partial_completion["successful_workload"]
    receipt_relative = A2._condition_gate_receipt_relative(
        successful_workload)
    legacy_partial_manifest = copy.deepcopy(partial_manifest)
    legacy_partial_manifest["schema_version"] = (
        A2.LEGACY_PARTIAL_RAW_MANIFEST_SCHEMA)
    legacy_partial_manifest["files"].pop(receipt_relative)
    legacy_partial_path = partial_root / "legacy-partial-raw-manifest.json"
    A2.write_json_x(legacy_partial_path, legacy_partial_manifest)
    legacy_partial_bundle = A2._load_partial_raw_manifest_bundle(
        policy, legacy_partial_path,
        hashlib.sha256(legacy_partial_path.read_bytes()).hexdigest(),
        attempt_id=partial_root.name, attempt_root=partial_root,
        current_pin=CURRENT_PIN, successful_workload=successful_workload,
        job_bindings=partial_completion_binding["jobs"],
    )
    assert legacy_partial_bundle["manifest"]["schema_version"] == (
        A2.LEGACY_PARTIAL_RAW_MANIFEST_SCHEMA)

    with pytest.raises(A2.SchemaChainError, match="shape crosses"):
        A2._load_partial_raw_manifest_bundle(
            policy, full_manifest_path,
            hashlib.sha256(full_manifest_path.read_bytes()).hexdigest(),
            attempt_id=full_root.name, attempt_root=full_root,
            current_pin=CURRENT_PIN, successful_workload="rr5",
            job_bindings=full_completion_binding["jobs"],
        )
    with pytest.raises(A2.CertificationError, match="identity mismatch"):
        A2._load_raw_manifest_bundle(
            policy, legacy_partial_path,
            hashlib.sha256(legacy_partial_path.read_bytes()).hexdigest(),
            attempt_id=partial_root.name, attempt_root=partial_root,
            current_pin=CURRENT_PIN,
            job_bindings=partial_completion_binding["jobs"],
        )


def test_frozen_v3_certification_bytes_and_legacy_cell_shape_remain_accepted():
    path = (
        A2.POLICY_PATH.parents[2] / "output/insights"
        / "2026-08-24_paper-story-a2-certification/certification.json")
    frozen = path.read_bytes()
    report = json.loads(frozen)

    assert hashlib.sha256(frozen).hexdigest() == (
        "f685b40d194c9e4b40eed6337b294f38a7ff4aef731829317fd2e83940fbda40")
    assert report["schema_version"] == A2.LEGACY_CERTIFICATION_SCHEMA
    A2._validate_certification_cells(report, legacy=True)


def test_p3_cli_selects_default_a2_and_explicit_a6_policy():
    common = ["preregister", "--attempt-id", "cli-policy", "--current-pin", CURRENT_PIN]
    default_args = A2._parser().parse_args(common)
    a6_args = A2._parser().parse_args([
        "--policy", "orchestrator/campaign/paper_story_a6_certification.v2.json",
        *common,
    ])
    default = A2._load_selected_policy(default_args)
    a6 = A2._load_selected_policy(a6_args)

    assert (A2.workload_ids(default), A2._qsub_job_name(default)) == (
        ("rr5", "rr50"), "paper-a2-cert")
    assert (A2.workload_ids(a6), A2._qsub_job_name(a6)) == (
        ("rr95",), "paper-a6-cert")


@pytest.mark.parametrize(
    ("raw_hosts", "expected"),
    (
        (None, ()),
        ("bnode002,bnode003,bnode004,bnode005",
         ("bnode002", "bnode003", "bnode004", "bnode005")),
    ),
)
def test_run_workload_cli_converts_optional_comma_separated_verify_hosts(
        monkeypatch, raw_hosts, expected):
    arguments = [
        "run-workload", "--workload", "rr5",
        "--attempt-root", "/attempt", "--raw-root", "/raw",
        "--current-pin", REPO_CURRENT_PIN,
        "--dependency-prefix", "/dependencies",
        "--ccbench-dir", "/ccbench",
        "--third-party-source-root", "/third-party",
    ]
    if raw_hosts is not None:
        arguments.extend(["--verify-fanout-hosts", raw_hosts])
    args = A2._parser().parse_args(arguments)
    calls = []

    def fake_run_workload(*_args, **kwargs):
        calls.append(kwargs)
        return A2.SimpleNamespace(
            campaign_id="fixture", committed=2, aborted=0,
            condition_gate_receipts=None,
        )

    monkeypatch.setattr(A2, "run_workload", fake_run_workload)
    assert args.handler(args) == 0
    assert calls[0]["verify_fanout_hosts"] == expected


@pytest.mark.parametrize("mutation", ("wrong-prefix", "resolver-failure", "dirty"))
def test_run_workload_production_pin_gate_rejects_noncanonical_source(
        tmp_path, monkeypatch, mutation):
    monkeypatch.setattr(A2.socket, "gethostname", lambda: "bnode001")
    policy = _policy(tmp_path)
    attempt = A2.preregister_attempt(
        policy, "run-workload-pin-negative", REPO_CURRENT_PIN)
    raw_root = A2.workload_job_root(policy, attempt, "rr5") / "raw"
    raw_root.mkdir()
    dependency = tmp_path / "dependency"
    dependency.mkdir()
    ccbench = tmp_path / "ccbench"
    ccbench.mkdir()
    canonical_full = REPO_CURRENT_PIN + "1" * (40 - len(REPO_CURRENT_PIN))
    wrong = ("0" if REPO_CURRENT_PIN[0] != "0" else "1") * 40

    def git_run(command, **kwargs):
        if command == ["git", "rev-parse", "--verify", "HEAD^{commit}"]:
            value = wrong if mutation == "wrong-prefix" else canonical_full
            return subprocess.CompletedProcess(command, 0, value + "\n", "")
        if command == [
                "git", "rev-parse", "--verify",
                f"{REPO_CURRENT_PIN}^{{commit}}"]:
            if mutation == "resolver-failure":
                raise subprocess.CalledProcessError(41, command)
            value = wrong if mutation == "wrong-prefix" else canonical_full
            return subprocess.CompletedProcess(command, 0, value + "\n", "")
        if command == [
                "git", "status", "--porcelain", "--untracked-files=no"]:
            value = " M tracked.cc\n" if mutation == "dirty" else ""
            return subprocess.CompletedProcess(command, 0, value, "")
        raise AssertionError(command)

    monkeypatch.setattr(A2.subprocess, "run", git_run)
    with pytest.raises(A2.CertificationError, match="CCBench current pin"):
        A2.run_workload(
            policy, workload_id="rr5", attempt_root=attempt,
            raw_root=raw_root, current_pin=REPO_CURRENT_PIN,
            dependency_prefix=dependency, ccbench_dir=ccbench,
            third_party_source_root=tmp_path / "fetchcontent",
            verify_fanout_hosts=("bnode002", "bnode003", "bnode004", "bnode005"),
            log=lambda *_args: None)


@pytest.mark.parametrize("current_pin", ("1" * 40, "abcdef0"))
def test_run_workload_requires_exact_repository_canonical_short_pin(
        tmp_path, monkeypatch, current_pin):
    monkeypatch.setattr(A2.socket, "gethostname", lambda: "bnode001")
    policy = _policy(tmp_path)
    attempt = A2.preregister_attempt(
        policy, "run-workload-noncanonical-pin", REPO_CURRENT_PIN)
    raw_root = A2.workload_job_root(policy, attempt, "rr5") / "raw"
    raw_root.mkdir()
    dependency = tmp_path / "dependency"
    dependency.mkdir()
    ccbench = tmp_path / "ccbench"
    ccbench.mkdir()

    with pytest.raises(A2.CertificationError, match="canonical short pin"):
        A2.run_workload(
            policy, workload_id="rr5", attempt_root=attempt,
            raw_root=raw_root, current_pin=current_pin,
            dependency_prefix=dependency, ccbench_dir=ccbench,
            third_party_source_root=tmp_path / "fetchcontent",
            verify_fanout_hosts=("bnode002", "bnode003", "bnode004", "bnode005"),
            log=lambda *_args: None)


def test_run_workload_verifies_staged_sources_before_condition_gate(
        tmp_path, monkeypatch):
    monkeypatch.setattr(A2.socket, "gethostname", lambda: "bnode001")
    policy = _policy(tmp_path)
    attempt = A2.preregister_attempt(
        policy, "run-workload-staged-verifier", REPO_CURRENT_PIN)
    raw_root = A2.workload_job_root(policy, attempt, "rr5") / "raw"
    raw_root.mkdir()
    dependency = tmp_path / "dependency"
    dependency.mkdir()
    ccbench = tmp_path / "ccbench"
    ccbench.mkdir()
    third_party = tmp_path / "fetchcontent"
    events = []

    def verifier(fetchcontent_base_dir, *, repo_root):
        events.append(("verify", Path(fetchcontent_base_dir), repo_root))
        raise A2.s8b_floor_campaign.FloorCampaignError("staged source rejected")

    monkeypatch.setattr(
        A2.s8b_floor_campaign,
        "_verify_pristine_floor_dependency_sources",
        verifier,
    )
    monkeypatch.setattr(
        A2,
        "_condition_gate_family_context",
        lambda *_args, **_kwargs: pytest.fail(
            "condition gate started before staged source verification"
        ),
    )
    with pytest.raises(A2.CertificationError) as error:
        A2.run_workload(
            policy, workload_id="rr5", attempt_root=attempt,
            raw_root=raw_root, current_pin=REPO_CURRENT_PIN,
            dependency_prefix=dependency, ccbench_dir=ccbench,
            third_party_source_root=third_party,
            verify_fanout_hosts=("bnode002", "bnode003", "bnode004", "bnode005"),
            log=lambda *_args: None,
        )
    assert isinstance(
        error.value.__cause__, A2.s8b_floor_campaign.FloorCampaignError)
    assert events == [
        ("verify", third_party, A2.POLICY_PATH.parents[2]),
    ]

    def programming_error(*_args, **_kwargs):
        raise ValueError("invalid fixed verifier arguments")

    monkeypatch.setattr(
        A2.s8b_floor_campaign,
        "_verify_pristine_floor_dependency_sources",
        programming_error,
    )
    with pytest.raises(ValueError, match="invalid fixed verifier arguments"):
        A2.run_workload(
            policy, workload_id="rr5", attempt_root=attempt,
            raw_root=raw_root, current_pin=REPO_CURRENT_PIN,
            dependency_prefix=dependency, ccbench_dir=ccbench,
            third_party_source_root=third_party,
            verify_fanout_hosts=("bnode002", "bnode003", "bnode004", "bnode005"),
            log=lambda *_args: None,
        )


def test_official_run_observes_dependency_receipt_after_condition_prebuild(
        tmp_path, monkeypatch):
    monkeypatch.setattr(A2.socket, "gethostname", lambda: "bnode001")
    from orchestrator.campaign import layout as campaign_layout

    source = inspect.getsource(A2.run_workload)
    observed = "buildcache.observed_toolchain_manifest("
    passed = "expected_toolchain_manifest=expected_toolchain_manifest"
    assert observed in source and passed in source
    assert source.count(passed) == 2
    condition_gate_call = source.index("with _condition_gate_family_context(")
    condition_gate_call_end = source.index(
        ") as (variant_root, condition_gate_receipts,", condition_gate_call)
    condition_gate_manifest = source.index(
        passed, condition_gate_call, condition_gate_call_end)
    assert condition_gate_call < condition_gate_manifest < condition_gate_call_end
    assert source.index(observed) < source.index(
        "with _condition_gate_family_context("
    )
    assert source.index(observed) < source.index("summary = run_campaign(")
    assert "capability_resolver=capability_resolver" in source
    loop_source = inspect.getsource(loop.run_campaign)
    assert "source_evidence = source_digest.resolve_evidence(" in loop_source
    assert "capability_resolver=capability_resolver" in loop_source
    assert "source_evidence=source_evidence" in loop_source

    policy = _policy(tmp_path)
    attempt = A2.preregister_attempt(
        policy, "actual-run-workload-producer", REPO_CURRENT_PIN)
    job_root = A2.workload_job_root(policy, attempt, "rr5")
    raw_root = job_root / "raw"
    raw_root.mkdir()
    dependency = tmp_path / "dependency"
    dependency.mkdir()
    ccbench = tmp_path / "ccbench"
    ccbench.mkdir()
    calls = {}
    fetchcontent_root = tmp_path / "fetchcontent"
    staged_sources = _staged_sources(fetchcontent_root)
    order = []

    @contextlib.contextmanager
    def condition_context(source_root, genomes, **kwargs):
        assert Path(source_root) == ccbench
        assert kwargs["fetchcontent_base_dir"] == fetchcontent_root
        assert kwargs["staged_sources"] == staged_sources
        order.append("condition-prebuild-complete")
        admissions = tuple(
            json.dumps({
                "admission_id": f"condition-gate/admission/{index}",
                "admission_digest": hashlib.sha256(
                    f"receipt-order-{index}".encode("ascii")
                ).hexdigest(),
                "use_class": "paper",
                "admitted": True,
                "record_ids": [f"receipt-order-record-{index}"],
                "unestablished_meaning_macros": [],
            }, sort_keys=True, separators=(",", ":"))
            for index, _genome in enumerate(genomes)
        )
        try:
            yield ccbench, None, admissions
        finally:
            order.append("condition-context-exit")

    dependency_receipt = {
        "masstree_head": "a" * 40,
        "config_sha256": "b" * 64,
    }

    def observe_dependency_receipt(source):
        assert source == os.fspath(staged_sources["masstree"])
        assert order == ["condition-prebuild-complete"]
        order.append("dependency-receipt")
        return dependency_receipt

    def driver_resolve_evidence(genome, commit, *, ccbench_dir, cxx):
        index = len(calls.setdefault("driver_evidences", []))
        assert index < 2
        assert commit == REPO_CURRENT_PIN
        assert Path(ccbench_dir) == ccbench
        assert cxx == "g++"
        token = source_digest.STOCK if index == 0 else "d" * 64
        evidence = source_digest.SourceEvidence(
            source_digest.SOURCE_EVIDENCE_SCHEMA,
            str(ccbench.resolve()), REPO_CURRENT_PIN,
            hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest(),
            token, "e" * 64, False, "f" * 64,
            ("include/backoff.hh",),
        )
        calls["driver_evidences"].append(evidence)
        return evidence

    driver_source_digest = A2.SimpleNamespace(
        STOCK=source_digest.STOCK,
        SourceEvidence=source_digest.SourceEvidence,
        resolve_evidence=driver_resolve_evidence,
    )
    resolved_repo_pin = subprocess.run(
        ["git", "-C", str(A2.POLICY_PATH.parents[2] / "external/ccbench"),
         "rev-parse", "--verify", f"{REPO_CURRENT_PIN}^{{commit}}"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()

    def git_run(command, **kwargs):
        if command == ["git", "rev-parse", "--verify", "HEAD^{commit}"]:
            return subprocess.CompletedProcess(
                command, 0, resolved_repo_pin + "\n", "")
        if command == [
                "git", "rev-parse", "--verify",
                f"{REPO_CURRENT_PIN}^{{commit}}"]:
            return subprocess.CompletedProcess(
                command, 0, resolved_repo_pin + "\n", "")
        if command[:3] == ["git", "status", "--porcelain"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        raise AssertionError(command)

    def authorize(cfg, authorization_contract, **_kwargs):
        calls["authorized"] = True
        return loop._AuthorizationResult(
            authorized_contract=authorization_contract,
            execution_receipt=None,
            bound_cfg=cfg,
            campaign_identity=str(ident.campaign_id(cfg)),
        )

    def resolve_evidence(genome, commit, *, ccbench_dir, cxx):
        index = len(calls.setdefault("evidences", []))
        assert commit == REPO_CURRENT_PIN
        assert Path(ccbench_dir) == ccbench
        assert cxx == "g++"
        evidence_root = tmp_path / f"source-evidence-{index}"
        evidence_root.mkdir()
        genome_sha256 = hashlib.sha256(
            A2._canonical_json(genome.canonical())).hexdigest()
        if index == 0:
            evidence = source_digest.SourceEvidence(
                source_digest.SOURCE_EVIDENCE_SCHEMA,
                str(evidence_root), REPO_CURRENT_PIN, genome_sha256,
                source_digest.STOCK, "a" * 64, True,
                hashlib.sha256(b"").hexdigest(), (),
            )
        else:
            evidence = source_digest.SourceEvidence(
                source_digest.SOURCE_EVIDENCE_SCHEMA,
                str(evidence_root), REPO_CURRENT_PIN, genome_sha256,
                "b" * 64, "b" * 64, False, "c" * 64,
                ("include/backoff.h",),
            )
        calls["evidences"].append(evidence)
        return evidence

    def evaluate(genome, _layout, _env_tag, _commit, _perf,
                 _clocks_per_us, **kwargs):
        assert order == ["condition-prebuild-complete", "dependency-receipt"]
        assert kwargs["fetchcontent_base_dir"] == os.fspath(fetchcontent_root)
        assert kwargs["masstree_source_dir"] == os.fspath(
            staged_sources["masstree"])
        assert kwargs["mimalloc_source_dir"] == os.fspath(
            staged_sources["mimalloc"])
        assert kwargs["googletest_source_dir"] == os.fspath(
            staged_sources["googletest"])
        assert kwargs["fetchcontent_dependency_receipt"] is dependency_receipt
        evidence = kwargs["source_evidence"]
        resolver = kwargs["capability_resolver"]
        assert evidence is calls["evidences"][len(calls.setdefault(
            "admissions", []))]
        assert kwargs["src_token"] == evidence.src_token
        assert callable(resolver)
        receipt = resolver(evidence)
        admission = build_admission.derive_build_admission(
            kwargs["build_context"], evidence, generator_receipt=receipt)
        calls["admissions"].append(admission)
        calls.setdefault("generator_receipts", []).append(receipt)
        calls["resolver"] = resolver
        return loop.EvalResult(
            genome=genome,
            variant=variant_id(genome, evidence.src_token),
            certified=True,
            aborted=False,
        )

    def raw_producer(_policy, cell, *, layout_root, **kwargs):
        calls.setdefault("layout_roots", []).append(Path(layout_root))
        expected = calls["driver_evidences"][
            len(calls.setdefault("raw_expected_tokens", []))].src_token
        assert kwargs["expected_src_token"] == expected
        calls["raw_expected_tokens"].append(expected)
        return {"cell_id": cell.cell_id, "terminal": "commit"}

    monkeypatch.setattr(A2.subprocess, "run", git_run)
    monkeypatch.setattr(A2, "_condition_gate_family_context", condition_context)
    monkeypatch.setattr(
        A2.buildcache,
        "_observe_fetchcontent_dependency_receipt",
        observe_dependency_receipt,
    )
    monkeypatch.setattr(A2, "source_digest", driver_source_digest)
    monkeypatch.setattr(A2, "_raw_cell_from_wal", raw_producer)
    monkeypatch.setattr(loop, "_authorize_measurement", authorize)
    monkeypatch.setattr(
        loop, "_perform_perf_preflight", lambda *_args, **_kwargs: (None, True))
    monkeypatch.setattr(
        loop.ident, "ensure_resumable_wal",
        lambda *_args, **_kwargs: A2.SimpleNamespace(status="clean"))
    monkeypatch.setattr(loop.wal, "replay", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(loop.source_digest, "resolve_evidence", resolve_evidence)
    monkeypatch.setattr(loop, "evaluate", evaluate)
    monkeypatch.setattr(
        campaign_layout, "resolve_campaign_output_root",
        lambda _use_class, output_root: output_root)
    monkeypatch.setattr(
        loop, "resolve_campaign_output_root",
        lambda _use_class, output_root: output_root)
    monkeypatch.setattr(
        buildcache, "compilers_for_current_site", lambda: ("gcc", "g++"))
    monkeypatch.setattr(
        buildcache, "observed_toolchain_manifest",
        lambda *_args, **_kwargs: {"fixture": "toolchain"})
    monkeypatch.setattr(
        buildcache, "toolchain_compilers_from_manifest",
        lambda _manifest: ("gcc", "g++"))
    monkeypatch.setattr(env_contract, "authorize", lambda _tag: object())

    A2.run_workload(
        policy, workload_id="rr5", attempt_root=attempt, raw_root=raw_root,
        current_pin=REPO_CURRENT_PIN, dependency_prefix=dependency,
        ccbench_dir=ccbench,
        third_party_source_root=fetchcontent_root,
        verify_fanout_hosts=("bnode002", "bnode003", "bnode004", "bnode005"),
        log=lambda *_args: None)
    assert order == [
        "condition-prebuild-complete",
        "dependency-receipt",
        "condition-context-exit",
    ]
    assert calls["authorized"] is True
    assert len(calls["driver_evidences"]) == 2
    assert calls["raw_expected_tokens"] == [source_digest.STOCK, "d" * 64]
    assert len(set(calls["layout_roots"])) == 1
    assert calls["layout_roots"][0].parent == job_root / "campaigns"
    assert not (job_root / "campaigns" / "campaigns").exists()
    assert {path.name for path in raw_root.iterdir()} == {
        "rr5-stock.json", "rr5-fixed10.json"}
    stock, adopted = calls["admissions"]
    generator_receipts = calls["generator_receipts"]
    calls["adopted_receipt"] = generator_receipts[1].as_receipt()
    calls["adopted_receipt_repeat"] = calls["resolver"](
        calls["evidences"][1]).as_receipt()
    assert stock.provenance is build_admission.BuildProvenance.STOCK_BASELINE
    assert adopted.provenance is build_admission.BuildProvenance.MACHINE_GENERATED
    assert stock.as_wal_receipt()["generator_receipt"] is None
    expected_generator_input = hashlib.sha256(A2._canonical_json({
        "policy_protocol_sha256": policy.protocol_sha256,
        "workload_id": "rr5",
        "evidence_genome_sha256": calls[
            "adopted_receipt"]["source"]["genome_sha256"],
    })).hexdigest()
    assert calls["adopted_receipt"]["generator_input_sha256"] \
        == expected_generator_input
    assert calls["adopted_receipt_repeat"] == calls["adopted_receipt"]


def test_m10_official_run_forwards_verify_hosts_and_fetchcontent_five_tuple(
        tmp_path, monkeypatch):
    from orchestrator.campaign import layout as campaign_layout

    policy = _a6_policy(tmp_path)
    workload = "rr95"
    verify_hosts = ("bnode002", "bnode003", "bnode004", "bnode005")
    attempt = A2.preregister_attempt(
        policy, "driver-source-token-binding", REPO_CURRENT_PIN)
    job_root = A2.workload_job_root(policy, attempt, workload)
    raw_root = job_root / "raw"
    raw_root.mkdir()
    dependency = tmp_path / "dependency"
    dependency.mkdir()
    source_root = tmp_path / "ccbench"
    source_root.mkdir()
    fetchcontent_root = tmp_path / "fetchcontent"
    staged_sources = _staged_sources(fetchcontent_root)
    variant_root = tmp_path / "patched-variant"
    variant_root.mkdir()
    full_pin = REPO_CURRENT_PIN + "1" * (40 - len(REPO_CURRENT_PIN))
    events = []
    tokens = (source_digest.STOCK, "9" * 64)
    role_predicate_calls = []
    real_role_predicate = A2._require_cell_src_token_role

    def git_run(command, **_kwargs):
        if command in (
                ["git", "rev-parse", "--verify", "HEAD^{commit}"],
                ["git", "rev-parse", "--verify",
                 f"{REPO_CURRENT_PIN}^{{commit}}"]):
            return subprocess.CompletedProcess(command, 0, full_pin + "\n", "")
        if command == ["git", "status", "--porcelain", "--untracked-files=no"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        raise AssertionError(command)

    @contextlib.contextmanager
    def condition_context(*_args, **_kwargs):
        admissions = tuple(json.dumps({
            "admission_id": f"condition-gate/admission/{index}",
            "admission_digest": hashlib.sha256(
                f"driver-admission-{index}".encode("ascii")).hexdigest(),
            "use_class": "paper", "admitted": True,
            "record_ids": [f"driver-record-{index}"],
            "unestablished_meaning_macros": [],
        }, sort_keys=True, separators=(",", ":")) for index in range(2))
        yield variant_root, [{"cell": 0}, {"cell": 1}], admissions

    def resolve_evidence(genome, commit, *, ccbench_dir, cxx):
        index = len([event for event in events if event[0] == "resolve"])
        assert index < 2
        assert commit == REPO_CURRENT_PIN
        assert ccbench_dir == os.fspath(variant_root)
        assert cxx == "g++"
        evidence = source_digest.SourceEvidence(
            source_digest.SOURCE_EVIDENCE_SCHEMA,
            str(variant_root.resolve()), REPO_CURRENT_PIN,
            hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest(),
            tokens[index], hashlib.sha256(
                f"driver-source-{index}".encode("ascii")).hexdigest(),
            False, hashlib.sha256(b"driver-patch").hexdigest(),
            ("include/backoff.hh",),
        )
        events.append(("resolve", index, ccbench_dir, evidence.src_token))
        return evidence

    driver_source_digest = A2.SimpleNamespace(
        STOCK=source_digest.STOCK,
        SourceEvidence=source_digest.SourceEvidence,
        resolve_evidence=resolve_evidence,
    )

    def observed_role_predicate(cell, token):
        role_predicate_calls.append((cell.cell_id, token))
        return real_role_predicate(cell, token)

    def fake_run_campaign(*_args, **kwargs):
        assert [event[0] for event in events] == ["resolve", "resolve"]
        assert kwargs["ccbench_dir"] == os.fspath(variant_root)
        assert kwargs["fetchcontent_base_dir"] == os.fspath(fetchcontent_root)
        assert kwargs["masstree_source_dir"] == os.fspath(
            staged_sources["masstree"])
        assert kwargs["mimalloc_source_dir"] == os.fspath(
            staged_sources["mimalloc"])
        assert kwargs["googletest_source_dir"] == os.fspath(
            staged_sources["googletest"])
        assert kwargs["fetchcontent_dependency_receipt"] == {
            "masstree_head": "a" * 40,
            "config_sha256": "b" * 64,
        }
        assert kwargs["verify_fanout_hosts"] == verify_hosts
        receipt = attempt / A2._condition_gate_receipt_relative(workload)
        assert receipt.is_file()
        events.append(("campaign", receipt.read_bytes()))
        genomes = _args[1]
        return A2.SimpleNamespace(
            results=[
                A2.SimpleNamespace(variant=variant_id(genome, token))
                for genome, token in zip(genomes, tokens, strict=True)
            ],
            skipped=0,
            layout_root=str(job_root / "campaigns" / "fake-campaign"),
            campaign_id="fake-campaign", committed=2, aborted=0,
        )

    forwarded = []

    def raw_producer(_policy, cell, *, expected_src_token, **_kwargs):
        forwarded.append((cell.cell_id, expected_src_token))
        events.append(("raw", cell.cell_id, expected_src_token))
        return {
            "cell_id": cell.cell_id,
            "terminal": "commit",
        }

    monkeypatch.setattr(A2.subprocess, "run", git_run)
    monkeypatch.setattr(A2, "_condition_gate_family_context", condition_context)
    monkeypatch.setattr(A2, "source_digest", driver_source_digest)
    monkeypatch.setattr(
        A2, "_require_cell_src_token_role", observed_role_predicate)
    monkeypatch.setattr(A2, "_raw_cell_from_wal", raw_producer)
    monkeypatch.setattr(loop, "run_campaign", fake_run_campaign)
    monkeypatch.setattr(
        campaign_layout, "resolve_campaign_output_root",
        lambda _use_class, output_root: output_root)
    monkeypatch.setattr(
        buildcache, "compilers_for_current_site", lambda: ("gcc", "g++"))
    monkeypatch.setattr(
        buildcache, "observed_toolchain_manifest",
        lambda *_args: {"fixture": "toolchain"})
    monkeypatch.setattr(env_contract, "authorize", lambda _tag: object())
    monkeypatch.setattr(A2.socket, "gethostname", lambda: "bnode001")

    A2.run_workload(
        policy, workload_id=workload, attempt_root=attempt, raw_root=raw_root,
        current_pin=REPO_CURRENT_PIN, dependency_prefix=dependency,
        ccbench_dir=source_root,
        third_party_source_root=fetchcontent_root,
        verify_fanout_hosts=verify_hosts,
        log=lambda *_args: None)

    assert [event[0] for event in events] == [
        "resolve", "resolve", "campaign", "raw", "raw"]
    assert forwarded == [
        ("rr95-stock", source_digest.STOCK),
        ("rr95-fixed2", "9" * 64),
    ]
    assert role_predicate_calls == forwarded
    parsed = A2._parse_condition_gate_admissions(
        policy, workload, events[2][1], current_pin=REPO_CURRENT_PIN)
    assert [parsed[cell.cell_id].src_token for cell in policy.cells[:2]] \
        == list(tokens)


@pytest.mark.parametrize(
    ("mutation", "tokens", "expected_calls", "signature"),
    (
        (
            "adopted-stock",
            (source_digest.STOCK, source_digest.STOCK),
            (
                ("rr5-stock", source_digest.STOCK),
                ("rr5-fixed10", source_digest.STOCK),
            ),
            "source token role rejected rr5-fixed10: patch-unapplied",
        ),
        (
            "stock-non-stock",
            (
                "955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9",
                "955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9",
            ),
            ((
                "rr5-stock",
                "955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9",
            ),),
            "source token role rejected rr5-stock: role-mismatch",
        ),
    ),
    ids=("adopted-stock", "stock-non-stock"),
)
def test_live_precampaign_source_role_predicate_rejects_before_campaign(
        tmp_path, monkeypatch, mutation, tokens, expected_calls, signature):
    """Name and execute the production role predicate on rejecting inputs."""
    monkeypatch.setattr(A2.socket, "gethostname", lambda: "bnode001")
    from orchestrator.campaign import layout as campaign_layout

    policy = _policy(tmp_path)
    attempt = A2.preregister_attempt(
        policy, "live-role-reject-" + mutation, REPO_CURRENT_PIN)
    job_root = A2.workload_job_root(policy, attempt, "rr5")
    raw_root = job_root / "raw"
    raw_root.mkdir()
    dependency = tmp_path / "dependency"
    dependency.mkdir()
    source_root = tmp_path / "ccbench"
    source_root.mkdir()
    full_pin = REPO_CURRENT_PIN + "1" * (40 - len(REPO_CURRENT_PIN))
    predicate_calls = []
    campaign_calls = []
    real_role_predicate = A2._require_cell_src_token_role

    def git_run(command, **_kwargs):
        if command in (
                ["git", "rev-parse", "--verify", "HEAD^{commit}"],
                ["git", "rev-parse", "--verify",
                 f"{REPO_CURRENT_PIN}^{{commit}}"]):
            return subprocess.CompletedProcess(command, 0, full_pin + "\n", "")
        if command == ["git", "status", "--porcelain", "--untracked-files=no"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        raise AssertionError(command)

    def resolve_evidence(genome, commit, *, ccbench_dir, cxx):
        index = len(predicate_calls)
        assert index < 2
        assert commit == REPO_CURRENT_PIN
        assert ccbench_dir == os.fspath(source_root)
        assert cxx == "g++"
        return source_digest.SourceEvidence(
            source_digest.SOURCE_EVIDENCE_SCHEMA,
            str(source_root.resolve()), REPO_CURRENT_PIN,
            hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest(),
            tokens[index], hashlib.sha256(
                f"live-role-source-{index}".encode("ascii")).hexdigest(),
            False, hashlib.sha256(b"live-role-patch").hexdigest(),
            ("include/backoff.hh",),
        )

    driver_source_digest = A2.SimpleNamespace(
        STOCK=source_digest.STOCK,
        SourceEvidence=source_digest.SourceEvidence,
        resolve_evidence=resolve_evidence,
    )

    def observed_role_predicate(cell, token):
        predicate_calls.append((cell.cell_id, token))
        return real_role_predicate(cell, token)

    def forbidden_campaign(*args, **kwargs):
        campaign_calls.append((args, kwargs))
        raise AssertionError("campaign started after source role mismatch")

    monkeypatch.setattr(A2.subprocess, "run", git_run)
    monkeypatch.setattr(A2, "source_digest", driver_source_digest)
    monkeypatch.setattr(
        A2, "_require_cell_src_token_role", observed_role_predicate)
    monkeypatch.setattr(loop, "run_campaign", forbidden_campaign)
    monkeypatch.setattr(
        campaign_layout, "resolve_campaign_output_root",
        lambda _use_class, output_root: output_root)
    monkeypatch.setattr(
        buildcache, "compilers_for_current_site", lambda: ("gcc", "g++"))
    monkeypatch.setattr(
        buildcache, "observed_toolchain_manifest",
        lambda *_args: {"fixture": "toolchain"})
    monkeypatch.setattr(env_contract, "authorize", lambda _tag: object())

    with pytest.raises(A2.CertificationError, match=signature):
        A2.run_workload(
            policy, workload_id="rr5", attempt_root=attempt,
            raw_root=raw_root, current_pin=REPO_CURRENT_PIN,
            dependency_prefix=dependency, ccbench_dir=source_root,
            third_party_source_root=tmp_path / "fetchcontent",
            verify_fanout_hosts=("bnode002", "bnode003", "bnode004", "bnode005"),
            log=lambda *_args: None)

    assert predicate_calls == list(expected_calls)
    assert campaign_calls == []
    assert not (
        attempt / A2._condition_gate_receipt_relative("rr5")
    ).exists()
    assert list(raw_root.iterdir()) == []


def test_pipeline_runs_correctness_workload_repetitions_without_new_wal_fields():
    pipeline_module = __import__(
        "orchestrator.campaign.pipeline", fromlist=["evaluate"],
    )
    tree = ast.parse(
        Path(pipeline_module.__file__).read_text(encoding="utf-8"),
        filename=pipeline_module.__file__,
    )
    functions = {
        node.name: node for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    core = functions["_prepare_evaluation_core"]
    one_pass = [
        node for node in ast.walk(core)
        if isinstance(node, ast.FunctionDef) and node.name == "_run_one_pass"
    ]
    assert len(one_pass) == 1
    repetition_loops = [
        node for node in ast.walk(one_pass[0])
        if isinstance(node, ast.For)
        and isinstance(node.target, ast.Name)
        and node.target.id == "_repetition"
        and ast.unparse(node.iter) == "range(workload.reps)"
    ]
    assert len(repetition_loops) == 1
    receipt_extensions = [
        node for node in ast.walk(core)
        if isinstance(node, ast.Call)
        and ast.unparse(node.func) == "verification_receipt_tags.extend"
        and len(node.args) == 1
        and ast.unparse(node.args[0]) == "[tag] * workload.reps"
    ]
    assert len(receipt_extensions) == 1

    for caller_name in ("evaluate", "_prepare_evaluation"):
        caller = functions[caller_name]
        core_calls = [
            node for node in ast.walk(caller)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_prepare_evaluation_core"
        ]
        assert len(core_calls) == 1
        assert "workload.reps" not in ast.unparse(caller)
        assert not any(
            isinstance(node, ast.Call)
            and ast.unparse(node.func) == "wal.log"
            for node in ast.walk(caller)
        )


def test_trace0_rejects_empty_dependency_prefix_value(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-empty-dependency-prefix")
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    prefix = "-DCMAKE_PREFIX_PATH="
    index = next(
        index for index, token in enumerate(evidence["configure_argv"])
        if token.startswith(prefix)
    )
    evidence["configure_argv"][index] = prefix

    with pytest.raises(A2.CertificationError):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN, evidence)


def test_trace0_rejects_wrong_fetchcontent_prefix_with_valid_value(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-wrong-fetchcontent-prefix")
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    prefix = "-DFETCHCONTENT_SOURCE_DIR_MASSTREE="
    index = next(
        index for index, token in enumerate(evidence["configure_argv"])
        if token.startswith(prefix)
    )
    token = evidence["configure_argv"][index]
    evidence["configure_argv"][index] = "X" + token[1:]

    with pytest.raises(A2.CertificationError):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN, evidence)


@pytest.mark.parametrize("mutation", ("wrong-prefix", "empty-value", "relative"))
def test_trace0_fetchcontent_prefix_mutations_are_rejected(tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-fetch-prefix-" + mutation)
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    prefix = "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST="
    index = next(
        index for index, token in enumerate(evidence["configure_argv"])
        if token.startswith(prefix)
    )
    if mutation == "wrong-prefix":
        evidence["configure_argv"][index] = (
            "-DFETCHCONTENT_SOURCE_DIR_GOOGLE_TEST="
            + evidence["configure_argv"][index][len(prefix):]
        )
    elif mutation == "empty-value":
        evidence["configure_argv"][index] = prefix
    else:
        evidence["configure_argv"][index] = prefix + "relative/googletest"

    with pytest.raises(A2.CertificationError):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN, evidence)


def test_trace0_fetchcontent_segment_matches_v2_command_order(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-fetch-segment-order")
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    configure = evidence["configure_argv"]
    base_index = next(
        index for index, token in enumerate(configure)
        if token.startswith("-DFETCHCONTENT_BASE_DIR=")
    )
    masstree_index = next(
        index for index, token in enumerate(configure)
        if token.startswith("-DFETCHCONTENT_SOURCE_DIR_MASSTREE=")
    )
    configure[base_index], configure[masstree_index] = (
        configure[masstree_index], configure[base_index]
    )

    with pytest.raises(A2.CertificationError):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN, evidence)


@pytest.mark.parametrize(
    "invalid_path",
    ("/fetchcontent/masstree\0-src", "/../", "relative/masstree-src"),
    ids=("nul", "lexically-noncanonical", "relative"),
)
def test_trace0_fetchcontent_path_values_match_producer_domain(
        tmp_path, invalid_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-fetch-path-domain")
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    prefix = "-DFETCHCONTENT_SOURCE_DIR_MASSTREE="
    index = next(
        index for index, token in enumerate(evidence["configure_argv"])
        if token.startswith(prefix)
    )
    evidence["configure_argv"][index] = prefix + invalid_path

    with pytest.raises(A2.CertificationError):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN, evidence)


def test_trace0_accepts_canonical_argv_from_v2_producer(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-fetch-producer-positive")
    cell = policy.cells[0]
    raw = _raw_cell(policy, cell, root)
    evidence = raw["trace0_evidence"]
    fetchcontent_base = root / "fetchcontent"
    staged_sources = _staged_sources(fetchcontent_base)
    build_dir = root / "build" / cell.cell_id
    configure, build = buildcache._v2_commands(
        A2._genome_for_cell(policy, cell), False, "/source", str(build_dir),
        evidence["toolchain"], jobs=48,
        dependency_prefix="/pinned/dependencies",
        fetchcontent_base_dir=os.fspath(fetchcontent_base),
        masstree_source_dir=staged_sources["masstree"],
        mimalloc_source_dir=staged_sources["mimalloc"],
        googletest_source_dir=staged_sources["googletest"],
    )
    evidence["configure_argv"] = configure
    evidence["build_argv"] = build

    assert A2.validate_trace0_evidence(
        policy, raw["cell_id"], root.name, CURRENT_PIN, evidence
    ) == evidence


def test_trace0_configure_argv_rejects_short_path_segment(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-fetch-short-segment")
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    dependency_index = next(
        index for index, token in enumerate(evidence["configure_argv"])
        if token.startswith("-DCMAKE_PREFIX_PATH=")
    )
    evidence["configure_argv"] = evidence["configure_argv"][
        :dependency_index + 4
    ]

    with pytest.raises(
            A2.CertificationError,
            match="configure argv is shorter than the v2 grammar"):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN, evidence)


@pytest.mark.parametrize("mutation", (
    "separated-define", "duplicate-configure-token", "unknown-configure-token",
    "fully-disconnected",
    "build-subcommand", "unknown-build-token", "unknown-run-flag",
    "clocks-per-us",
))
def test_trace0_argv_closed_grammar_rejects_unconsumed_tokens(tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-argv-" + mutation)
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    if mutation == "separated-define":
        evidence["configure_argv"].extend(["-D", "CCBENCH_TRACE=0"])
    elif mutation == "duplicate-configure-token":
        evidence["configure_argv"].append("-DENABLE_SANITIZER=OFF")
    elif mutation == "unknown-configure-token":
        evidence["configure_argv"].append("-DUNKNOWN=1")
    elif mutation == "fully-disconnected":
        evidence["configure_argv"].append("-DFETCHCONTENT_FULLY_DISCONNECTED=ON")
    elif mutation == "build-subcommand":
        evidence["build_argv"][1] = "--install"
    elif mutation == "unknown-build-token":
        evidence["build_argv"].append("--verbose")
    elif mutation == "unknown-run-flag":
        evidence["run_argv"].append("-unknown_flag=1")
    else:
        clock_index = next(
            index for index, token in enumerate(evidence["run_argv"])
            if token.startswith("-clocks_per_us="))
        evidence["run_argv"][clock_index] = "-clocks_per_us=1"
    with pytest.raises(A2.CertificationError):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN, evidence)


def test_wal_configure_locator_comes_from_versioned_grammar():
    source = inspect.getsource(A2._raw_cell_from_wal)
    assert '_cmake_directory(configure, "-B")' not in source
    assert '["build_directory_option"]' in source


def test_synthetic_pbs_free_preregister_through_analyze_positive(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "synthetic-positive", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    report = A2.collect_results(
        policy, A2.load_raw_results(policy, root), attempt_id=root.name,
        current_pin=CURRENT_PIN, request_ids=evidence["request_ids"])
    report["source_commit"] = evidence["source_commit"]
    repo = tmp_path / "repo"
    repo.mkdir()
    destination = A2.materialize(policy, report, evidence, repo_root=repo)
    assert A2.driver_rc(report) == 0
    assert report["status"] == "observed-positive"
    assert (destination / "COMPLETE.json").is_file()


def test_volatile_diagnostics_are_not_fixture_authority(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "volatile-diagnostics")
    first = _positive_results(policy, root)
    second = copy.deepcopy(first)
    for index, raw in enumerate(second):
        raw["diagnostics"] = {
            "working_tree_probe": "changed-" + str(index),
            "host_payload": {"free_bytes": index * 991},
        }
    report_a = A2.collect_results(
        policy, first, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_ids={"rr5": "125.nqsv", "rr50": "126.nqsv"})
    assert report_a["status"] == "observed-positive"
    with pytest.raises(A2.CertificationError, match="raw cell result schema"):
        A2.collect_results(
            policy, second, attempt_id=root.name, current_pin=CURRENT_PIN,
            request_ids={"rr5": "125.nqsv", "rr50": "126.nqsv"})


def _run() -> int:
    """Keep this test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
