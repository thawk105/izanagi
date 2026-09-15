# -*- coding: utf-8 -*-
"""S-1 直接比較 driver の positive control (実 build/bench・subprocess なし)。"""
from __future__ import annotations

import ast
import argparse
import copy
import contextlib
import errno
import functools
import hashlib
import importlib.util
import inspect
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
ORCH = TESTS.parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(ORCH.parent))

from orchestrator.campaign import (axis_trigger_gating, condition_meaning_gate,  # noqa: E402
                                   env_contract, pipeline, wal)
from orchestrator.campaign.build_admission import (BuildRunContext, GeneratorId,  # noqa: E402
                                      add_coder_build_authority_argument,
                                      build_run_context)
from orchestrator.campaign.layout import CampaignLayout  # noqa: E402
from orchestrator.campaign.model import Genome, STAGE_BUILD_START, STAGE_S1_SESSION  # noqa: E402
from orchestrator.campaign.pipeline import EvalResult, PerfConfig  # noqa: E402
from orchestrator.campaign.source_digest import (EMPTY_TRACKED_DIFF_SHA256, STOCK,  # noqa: E402
                                    SourceEvidence)
from orchestrator.campaign.reflux_ir import TriggerGateIR, emit_predicate  # noqa: E402
from orchestrator.campaign import s1_direct_comparison as S  # noqa: E402
from orchestrator.campaign import t080_freeze_migration as T080  # noqa: E402
from s1_expected_goldens import (  # noqa: E402
    EXPECTED_GATES,
    EXPECTED_IDENT_ALL_PREDICATE,
    EXPECTED_SORT,
)
from campaign_lock_test_support import build_v2_lock              # noqa: E402
import commit_receipt_support as receipt_support                   # noqa: E402

_REAL_CONDITION_RECORDS_FOR_GENOME = S._condition_records_for_genome


@pytest.fixture(autouse=True)
def _avoid_condition_compiler_work_in_driver_tests(monkeypatch):
    monkeypatch.setattr(
        S, "_condition_records_for_genome",
        lambda _root, genome, **_kwargs: _condition_records(genome),
    )


def test_prepare_cell_condition_family_uses_real_two_arm_api():
    source = inspect.getsource(_REAL_CONDITION_RECORDS_FOR_GENOME)
    assert "evaluate_define_supply_effectuation" in source
    assert "evaluate_define_runtime_meaning" in source
    assert "require_condition_gate_family" in source
    assert "declare_define_runtime_meaning" in source


def _observe_real_condition_admission(monkeypatch):
    observed = []
    real_admission = condition_meaning_gate.require_condition_gate_family

    def observe(supply, meaning, **kwargs):
        admission = real_admission(supply, meaning, **kwargs)
        records = (tuple(supply), tuple(meaning))
        observed.append((records, admission, tuple(
            record.canonical_json() for arm in records for record in arm
        )))
        return admission

    monkeypatch.setattr(condition_meaning_gate, "require_condition_gate_family", observe)
    return observed


@pytest.mark.parametrize("source_note", ["first source", "changed volatile source"])
def test_condition_rejection_preserves_every_real_red_detail(
        tmp_path, monkeypatch, source_note):
    """拒否は実 gate の両 red arm の理由と detail を本文へ運ぶ。
    受理は下の正例で同一の発行 record と canonical bytes を返す。
    """
    source = tmp_path / "supplied"
    shutil.copytree(TESTS / "fixtures/condition_meaning_gate/supplied", source)
    owner = source / condition_meaning_gate.SOURCE_REL
    owner.write_bytes(owner.read_bytes() + f"\n// {source_note}\n".encode())
    observed = _observe_real_condition_admission(monkeypatch)

    with pytest.raises(S.DriverError) as rejected:
        _REAL_CONDITION_RECORDS_FOR_GENOME(
            str(source), Genome("silo", {"BACKOFF_FIXED": 5}),
            driver_id="test.s1.detail", use_class="certified-selection",
            cxx=str(tmp_path / "absent-compiler"),
        )

    (records, admission, _raw), = observed
    assert admission.admitted is False
    rows = [record for arm in records for record in arm]
    assert [(record.macro, record.arm, record.terminal_status, record.reason_code)
            for record in rows] == [
        ("BACKOFF_FIXED", "supply-effectuation", "red", "compiler-failed"),
        ("BACKOFF_FIXED", "runtime-meaning", "red", "compiler-failed"),
    ]
    lines = str(rejected.value).splitlines()
    assert len(lines) == 3
    for record, line in zip(rows, lines[1:]):
        assert type(record) is condition_meaning_gate.ConditionArmRecord
        assert record.evidence["detail"] == "compiler cannot be resolved"
        assert line == (
            f"{record.macro}:{record.arm}:{record.reason_code}: "
            "evidence.detail='compiler cannot be resolved'"
        )


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt, SystemExit, GeneratorExit])
def test_condition_detail_formatter_failure_preserves_rejection(
        tmp_path, monkeypatch, failure):
    """拒否済み record の整形失敗は gate 拒否を置換せず、終了割込みは伝播する。
    受理時には detail 整形を実行せず発行 record を返す。
    """
    observed = _observe_real_condition_admission(monkeypatch)
    calls = []

    def broken_detail(argv):
        calls.append(argv)
        raise failure("formatting failed")

    monkeypatch.setattr(condition_meaning_gate, "_bounded_process_argv_detail", broken_detail)
    expected = S.DriverError if failure is RuntimeError else failure
    with pytest.raises(expected) as rejected:
        _REAL_CONDITION_RECORDS_FOR_GENOME(
            str(TESTS / "fixtures/condition_meaning_gate/supplied"),
            Genome("silo", {"BACKOFF_FIXED": 5}), driver_id="test.s1.detail",
            use_class="certified-selection", cxx=str(tmp_path / "absent-compiler"),
        )
    assert len(observed) == 1
    assert observed[0][1].admitted is False
    if failure is RuntimeError:
        assert str(rejected.value) == (
            "condition gate rejected prepared cell: "
            "BACKOFF_FIXED:supply-effectuation:compiler-failed,"
            "BACKOFF_FIXED:runtime-meaning:compiler-failed"
            "\n<condition detail unavailable>\n<condition detail unavailable>"
        )
        assert len(calls) == 2
    else:
        assert len(calls) == 1


def test_condition_long_real_process_detail_keeps_d1912_bound_and_digest(
        tmp_path, monkeypatch):
    """拒否は実 preprocess の長い detail を D1912 の上限と digest 付きで運ぶ。
    受理は別の正例で同一の発行 record と canonical bytes を返す。
    """
    source = tmp_path / "supplied"
    shutil.copytree(TESTS / "fixtures/condition_meaning_gate/supplied", source)
    owner = source / condition_meaning_gate.SOURCE_REL
    owner.write_bytes(owner.read_bytes() + b"\n#error " + b"detail-diagnostic-" * 80 + b"\n")
    observed = _observe_real_condition_admission(monkeypatch)
    with pytest.raises(S.DriverError) as rejected:
        _REAL_CONDITION_RECORDS_FOR_GENOME(
            str(source), Genome("silo", {"BACKOFF_FIXED": 5}),
            driver_id="test.s1.detail", use_class="certified-selection", cxx=_any_cxx(),
        )
    (records, admission, _raw), = observed
    assert admission.admitted is False
    record = records[0][0]
    assert type(record) is condition_meaning_gate.ConditionArmRecord
    assert (record.terminal_status, record.reason_code) == ("red", "preprocess-failed")
    detail = record.evidence["detail"]
    assert "rc=" in detail and "stderr=" in detail and "argv=" in detail
    encoded = shlex.join([detail]).encode("utf-8", errors="backslashreplace")
    assert len(encoded) > 500
    marker = (
        "...<argv truncated; limit=500 bytes; "
        f"original={len(encoded)} bytes; sha256={hashlib.sha256(encoded).hexdigest()}>"
    ).encode("ascii")
    expected = (encoded[:500 - len(marker)] + marker).decode("utf-8", errors="ignore")
    assert f"evidence.detail={expected}" in str(rejected.value)
    assert len(expected.encode("utf-8")) <= 500


def test_condition_accepted_records_and_bytes_are_unchanged(monkeypatch):
    """拒否は別の負例で実 gate の両 red record を検査する。
    受理は実 admission が検査した record 自体と canonical bytes をそのまま返す。
    """
    observed = _observe_real_condition_admission(monkeypatch)
    returned = _REAL_CONDITION_RECORDS_FOR_GENOME(
        str(TESTS / "fixtures/condition_meaning_gate/supplied"),
        Genome("silo", {"BACKOFF_FIXED": 5}), driver_id="test.s1.detail",
        use_class="certified-selection", cxx=_any_cxx(),
    )
    (records, admission, raw), = observed
    assert admission.admitted is True
    assert tuple(record.canonical_json() for arm in returned for record in arm) == raw
    assert all(actual is issued for actual_arm, issued_arm in zip(returned, records)
               for actual, issued in zip(actual_arm, issued_arm))
    assert [[record.terminal_status for record in arm] for arm in returned] == [
        ["green"], ["green"],
    ]


def test_noinline_inert_meaning_record_comes_from_registry_factory():
    driver_id = "test.s1_direct_comparison.noinline-factory"
    genome = Genome("silo", {"BACKOFF_NOINLINE": 0})
    supply_records, meaning_records = _issued_condition_records(
        tuple(sorted(genome.flags.items())), driver_id,
    )
    request = S._condition_requests_for_flags(
        genome.flags, driver_id=driver_id,
    )[0]
    declaration = condition_meaning_gate.declare_define_runtime_meaning(request)
    admission = _assert_promotion_admission_contract(
        supply_records, meaning_records,
    )

    assert type(declaration) is \
        condition_meaning_gate.ConditionalBranchMeaningDeclaration
    assert S._condition_meaning_declaration("BACKOFF_NOINLINE", 0) is None
    assert [record.terminal_status for record in meaning_records] == ["green"]
    assert meaning_records[0].evidence["source_rel"] == declaration.source_rel
    assert admission.unestablished_meaning_macros == ()


_OUTER_WHITESPACE = (
    ("space", " "),
    ("tab", "\t"),
    ("crlf", "\r\n"),
    ("vertical-tab", "\x0b"),
    ("form-feed", "\x0c"),
    ("nbsp", "\u00a0"),
    ("ideographic-space", "\u3000"),
)
_FAKE_OPTIONS_CMAKE = (
    'set(CCBENCH_BACK_OFF 1 CACHE STRING "backoff")\n'
    'set(CCBENCH_BACKOFF_TRIGGER_GATING 0 CACHE STRING "trigger gate")\n'
    "function(ccbench_universal_definitions out_var)\n"
    "  set(${out_var}\n"
    "    BACK_OFF=${CCBENCH_BACK_OFF}\n"
    "    BACKOFF_TRIGGER_GATING=${CCBENCH_BACKOFF_TRIGGER_GATING}\n"
    "    PARENT_SCOPE)\n"
    "endfunction()\n"
)
_FAKE_SILO_CMAKE = (
    "ccbench_add_protocol(silo\n"
    "  SOURCES transaction.cc\n"
    "  WORKLOADS ycsb)\n"
)
_FAKE_MOCC_CMAKE = (
    "ccbench_add_protocol(mocc\n"
    "  SOURCES transaction.cc\n"
    "  WORKLOADS ycsb)\n"
)
_FAKE_MOCC_TRANSACTION_CC = "int mocc_fixture;\n"
_FAKE_BACKOFF_HH = (
    "class Backoff {\n"
    " public:\n"
    "  static int wait() {\n"
    "#if BACK_OFF\n"
    "    return 1;\n"
    "#else\n"
    "    return 0;\n"
    "#endif\n"
    "  }\n"
    "};\n"
)
_FAKE_GATE_TRANSACTION_CC = (
    "class Transaction {\n"
    " public:\n"
    "  void abort() {\n"
    "    bool izanagi_gate_pass = false;\n"
    "    // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating\n"
    "#if BACKOFF_TRIGGER_GATING\n"
    "    izanagi_gate_pass = true;\n"
    "#else\n"
    "    izanagi_gate_pass = false;\n"
    "#endif\n"
    "    // EVOLVE-BLOCK-END silo-backoff-trigger-gating\n"
    "  }\n"
    "};\n"
)


def _canonical_perf_receipt(status: str) -> dict:
    available = status == "available"
    return {
        "schema": S._perf_preflight.SCHEMA,
        "status": status,
        "available": available,
        "probe_argv": list(S._perf_preflight._BASE_PROBE_ARGV),
        "rc": 0 if available else None,
        "parsed_events": list(S._perf_preflight.PERF_EVENTS) if available else [],
        "reason": (
            "available" if available else
            "probe-os-error" if status == "probe_error" else
            "perf-not-found"
        ),
        "stderr_sha256": "0" * 64,
        "candidates": [],
    }


@pytest.fixture(autouse=True)
def _pin_s1_perf_available(monkeypatch):
    """既存の perf-present fixture を実行 host の availability から隔離する。"""
    monkeypatch.setattr(
        S._perf_preflight,
        "probe_perf_availability",
        lambda: _canonical_perf_receipt("available"),
    )


def _evidence(*, stock=True, commit=None, genome_value=None):
    genome_value = genome_value or Genome("silo", {"BACK_OFF": 1})
    return SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=str(receipt_support.proof_source_root()),
        ccbench_commit=commit or _freeze()["ccbench_pin"],
        genome_sha256=hashlib.sha256(
            genome_value.canonical().encode("utf-8")
        ).hexdigest(),
        src_token=STOCK if stock else "2" * 64, source_bytes_sha256="3" * 64,
        tracked_clean=stock,
        tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256 if stock else "4" * 64,
        tracked_paths=() if stock else ("cc/silo/include/transaction.hh",),
    )


def _freeze() -> dict:
    workloads = ("balanced", "write-heavy", "read-heavy")
    configs = ("system_gate", "ident_all", "p2_2_flag_opt",
               "backoff_fixed_best", "sort_best", "stock_common")
    cells = {}
    for workload in workloads:
        for config in configs:
            cell_id = f"{workload}:{config}"
            cells[cell_id] = {
                "workload": workload, "configuration": config,
                "variant": {"flags": {"BACK_OFF": 1}},
                "source_pointer": {"path": "fixture", "key": cell_id},
            }
    order = list(cells)
    return {
        "ccbench_pin": "d706650cdb31e442bef45b9b4216951d4fb40969",
        "schedule_hash": "a" * 64,
        "operating_point": {"RECORDS": 1_000_000, "THREADS": 48,
                            "EXTIME": 3, "REPS": 5},
        "workload_flags": {
            "balanced": {"ycsb_rratio": "50"},
            "write-heavy": {"ycsb_rratio": "5"},
            "read-heavy": {"ycsb_rratio": "95"},
        },
        "cells": cells,
        "schedule": {
            "floor": [order[:] for _ in range(8)],
            "test_block_1": [order[:] for _ in range(4)],
            "test_block_2": [order[:] for _ in range(4)],
        },
    }


def _write_freeze(tmp_path: Path, document: dict | None = None) -> Path:
    path = tmp_path / "freeze.json"
    path.write_text(json.dumps(document or _freeze()), encoding="utf-8")
    return path


@contextlib.contextmanager
def _prepared(cell, pin, *, cxx):
    genome = Genome("silo", dict(cell["variant"]["flags"]))
    supply, meaning = _condition_records(genome)
    yield S.PreparedCell(
        genome, "stock", "/ccbench", "/cache",
        condition_supply_records=supply,
        condition_meaning_records=meaning,
    )


@contextlib.contextmanager
def _fixture_checkout(worktree: Path):
    yield str(worktree)


@contextlib.contextmanager
def _fixture_backoff_patch(backoff: Path):
    backoff.write_text("""// EVOLVE-BLOCK-BEGIN silo-backoff-magnitude
#if BACKOFF_FIXED >= 0
double now_backoff = static_cast<double>(BACKOFF_FIXED);
#else
double now_backoff = Backoff_.load(std::memory_order_acquire);
#endif
// EVOLVE-BLOCK-END silo-backoff-magnitude
""", encoding="utf-8")
    yield []


@contextlib.contextmanager
def _fixture_gate_patch(worktree: Path):
    source = worktree / axis_trigger_gating.SOURCE_REL
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("""#pragma once
class TxExecutor {
 public:
  void abort() {
  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating
#if BACKOFF_TRIGGER_GATING
  izanagi_gate_pass = true;
#else
  Backoff::backoff(FLAGS_clocks_per_us);
#endif
  // EVOLVE-BLOCK-END silo-backoff-trigger-gating
  }
};
""", encoding="utf-8")
    yield []


def _any_cxx() -> str:
    """同一の選択 compiler 内で source-digest の現行関係を検査する。

    compiler 版をまたぐ関係は保証しない。候補が全滅した場合だけ依存物不在として skip する。
    """
    for c in ("g++-13", "g++-12", "g++"):
        if shutil.which(c):
            return c
    pytest.skip("C++ toolchain 全滅 (g++-13/g++-12/g++ いずれも PATH に無い)")


def _fake_ccbench_repo(root: Path) -> tuple[Path, str]:
    (root / "cmake").mkdir(parents=True)
    (root / "include").mkdir()
    (root / "cc" / "silo").mkdir(parents=True)
    (root / "cc" / "mocc").mkdir(parents=True)
    (root / "cmake" / "Options.cmake").write_text(
        _FAKE_OPTIONS_CMAKE, encoding="utf-8"
    )
    (root / "include" / "backoff.hh").write_text(
        _FAKE_BACKOFF_HH, encoding="utf-8"
    )
    (root / "cc" / "silo" / "CMakeLists.txt").write_text(
        _FAKE_SILO_CMAKE, encoding="utf-8"
    )
    (root / "cc" / "mocc" / "CMakeLists.txt").write_text(
        _FAKE_MOCC_CMAKE, encoding="utf-8"
    )
    (root / "cc" / "mocc" / "transaction.cc").write_text(
        _FAKE_MOCC_TRANSACTION_CC, encoding="utf-8"
    )
    (root / axis_trigger_gating.SOURCE_REL).write_text(
        _FAKE_GATE_TRANSACTION_CC, encoding="utf-8"
    )

    def git(*args: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr
        return completed.stdout

    git("init", "-q")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "izanagi-test")
    git("add", "-A")
    git("commit", "-q", "-m", "stock")
    return root, git("rev-parse", "HEAD").strip()


class _Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        self.value += 0.01
        return self.value


def _run(tmp_path: Path, role: str, evaluate_fn, **kwargs) -> int:
    return S.run_role(
        role, freeze_path=_write_freeze(tmp_path),
        budget_path=tmp_path / "time_ledger.json",
        output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
        evaluate_fn=evaluate_fn, prepare_cell_fn=_prepared,
        single_tenant_fn=lambda: None, monotonic=_Clock(), log=lambda msg: None,
        **kwargs)


@functools.lru_cache(maxsize=None)
def _issued_condition_records(
        flags: tuple[tuple[str, object], ...], driver_id: str,
):
    genome = Genome("silo", dict(flags))
    requests = S._condition_requests_for_flags(genome.flags, driver_id=driver_id)
    if not requests:
        return (), ()
    fixture = TESTS / "fixtures" / "condition_meaning_gate" / "supplied"
    with tempfile.TemporaryDirectory(prefix="s1-condition-promotion-") as temporary:
        source_root = Path(temporary) / "supplied"
        shutil.copytree(fixture, source_root)
        _materialize_requested_condition_macros(source_root, requests)
        records = _REAL_CONDITION_RECORDS_FOR_GENOME(
            str(source_root), genome, driver_id=driver_id,
            use_class="certified-selection", cxx=_any_cxx(),
            stock_root=str(source_root / "stock"),
        )
    admission = _assert_promotion_admission_contract(*records)
    assert admission.admitted is True
    return records


def _materialize_requested_condition_macros(source_root: Path, requests) -> None:
    """Give the real evaluator a minimal owner-TU witness for S1 fixture macros."""
    options_path = source_root / condition_meaning_gate.OPTIONS_REL
    options = options_path.read_text(encoding="utf-8")
    source_suffixes: dict[Path, list[str]] = {}
    for request in requests:
        if request.macro == "BACKOFF_FIXED":
            continue
        if request.route == condition_meaning_gate.ROUTE_CMAKE_CACHE:
            option = f"CCBENCH_{request.macro}"
            mapping = f"    {request.macro}=${{{option}}}\n"
            if mapping not in options:
                options = (
                    f'set({option} {request.default_value} CACHE STRING '
                    '"promotion fixture")\n' + options
                )
                options = options.replace(
                    "    PARENT_SCOPE)\n", mapping + "    PARENT_SCOPE)\n",
                )
        for prefix in (Path(), Path("stock")):
            owner = source_root / prefix / request.owner_tu
            assert owner.is_file(), f"promotion fixture owner TU missing: {owner}"
            variable = f"condition_fixture_{request.macro.lower()}"
            source_suffixes.setdefault(owner, []).append(
                f"\n#if {request.macro}\n"
                f"static int {variable} = 1;\n"
                "#else\n"
                f"static int {variable} = 0;\n"
                "#endif\n"
            )
    options_path.write_text(options, encoding="utf-8")
    for owner, suffixes in source_suffixes.items():
        owner.write_text(
            owner.read_text(encoding="utf-8") + "".join(suffixes),
            encoding="utf-8",
        )


def _assert_promotion_admission_contract(
        supply_records, meaning_records, *, use_class="certified-selection",
):
    admission = condition_meaning_gate.require_condition_gate_family(
        supply_records, meaning_records, use_class=use_class,
    )
    supply_green = all(
        record.terminal_status == "green" for record in supply_records
    )
    meaning_not_red = all(
        record.terminal_status != "red" for record in meaning_records
    )
    assert admission.admitted is (supply_green and meaning_not_red)
    assert admission.unestablished_meaning_macros == tuple(sorted({
        record.macro
        for record in meaning_records
        if record.terminal_status == "unestablished"
    }))
    return admission


def _real_backoff_fixed_records(source_root: Path, value: int):
    driver_id = "test.s1_direct_comparison.promotion-contract"
    genome = Genome("silo", {"BACKOFF_FIXED": value})
    request = S._condition_requests_for_flags(
        genome.flags, driver_id=driver_id,
    )[0]
    captured = condition_meaning_gate.capture_define_inputs(source_root)
    supply = condition_meaning_gate.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake="cmake",
    )
    meaning = condition_meaning_gate.evaluate_define_runtime_meaning(
        captured, request=request,
        declaration=S._condition_meaning_declaration(request.macro, value),
        cxx=_any_cxx(),
    )
    return supply, meaning


def test_promotion_contract_rejects_non_green_supply_effectuation():
    fixture = TESTS / "fixtures" / "condition_meaning_gate" / "f707-missing-supply"
    supply, meaning = _real_backoff_fixed_records(fixture, 5)
    admission = _assert_promotion_admission_contract([supply], [meaning])

    assert supply.terminal_status == "red"
    assert meaning.terminal_status == "green"
    assert admission.admitted is False


def test_promotion_contract_rejects_red_runtime_meaning():
    fixture = TESTS / "fixtures" / "condition_meaning_gate" / "supplied"
    supply, meaning = _real_backoff_fixed_records(fixture, 1000)
    admission = _assert_promotion_admission_contract([supply], [meaning])

    assert supply.terminal_status == "green"
    assert meaning.terminal_status == "red"
    assert admission.admitted is False


def test_promotion_contract_carries_unestablished_meaning_macro():
    records = _issued_condition_records(
        (("BACKOFF_TRIGGER_GATING", 1),),
        "test.s1_direct_comparison.unestablished-carryover",
    )
    admission = _assert_promotion_admission_contract(*records)

    assert [record.terminal_status for record in records[0]] == ["green"]
    assert [record.terminal_status for record in records[1]] == ["unestablished"]
    assert admission.admitted is True
    assert admission.unestablished_meaning_macros == ("BACKOFF_TRIGGER_GATING",)


def _condition_records(
        genome: Genome,
        driver_id: str = "orchestrator.campaign.s1_direct_comparison.prepare_cell",
):
    return _issued_condition_records(
        tuple(sorted(genome.flags.items())), driver_id,
    )


def _forged_empty_condition_records(genome: Genome, *, driver_id: str):
    supply = []
    meaning = []
    defaults = {
        "BACKOFF_FIXED": -1,
        "BACKOFF_NOINLINE": 0,
        "BACKOFF_TRIGGER_GATING": 0,
        "SORT_VARIANT": 0,
    }
    for macro in sorted(set(genome.flags) & set(defaults)):
        request = condition_meaning_gate.make_define_request(
            driver_id=driver_id,
            macro=macro, requested_value=genome.flags[macro],
            default_value=defaults[macro],
        )
        request_digest = condition_meaning_gate._request_digest(request, ())
        supply.append(condition_meaning_gate._arm_record(
            arm="supply-effectuation", terminal_status="green",
            reason_code="requested-default-preprocess-different",
            request=request, request_digest=request_digest, evidence={},
        ))
        meaning.append(condition_meaning_gate._arm_record(
            arm="runtime-meaning", terminal_status="green",
            reason_code="declared-meaning-observed",
            request=request, request_digest=request_digest, evidence={},
        ))
    return tuple(supply), tuple(meaning)


def _with_condition_records(result: EvalResult) -> EvalResult:
    supply, meaning = _condition_records(result.genome)
    result.condition_supply_records = supply
    result.condition_meaning_records = meaning
    return result


def _green(genome, *args, **kwargs):
    return _with_condition_records(EvalResult(
        genome=genome, variant=pipeline.variant_id(genome),
        certified=True, aborted=False, fitness_tps=100.0,
    ))


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_injected_prepare_cell_without_condition_records_is_refused(tmp_path):
    @contextlib.contextmanager
    def evidence_less_prepare(cell, pin, *, cxx):
        yield S.PreparedCell(
            Genome("silo", dict(cell["variant"]["flags"])),
            "stock", "/ccbench", "/cache",
        )

    with pytest.raises(S.DriverError, match="prepare_cell_fn return"):
        S.run_role(
            "develop", freeze_path=_write_freeze(tmp_path),
            budget_path=tmp_path / "time_ledger.json",
            output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
            evaluate_fn=_green, prepare_cell_fn=evidence_less_prepare,
            single_tenant_fn=lambda: None, monotonic=_Clock(), log=lambda msg: None,
        )


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_injected_evaluate_fn_certified_result_without_condition_records_is_refused(
        tmp_path):
    def evidence_less_evaluate(genome, *args, **kwargs):
        return EvalResult(
            genome=genome, variant=pipeline.variant_id(genome),
            certified=True, aborted=False, fitness_tps=100.0,
        )

    with pytest.raises(S.DriverError, match="evaluate_fn return"):
        _run(tmp_path, "develop", evidence_less_evaluate)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_injected_callables_with_explicit_condition_records_are_accepted():
    genome = Genome("silo", {"BACKOFF_FIXED": 5})
    driver_id = "test.s1_direct_comparison.real-positive"
    records = _REAL_CONDITION_RECORDS_FOR_GENOME(
        str(TESTS / "fixtures" / "condition_meaning_gate" / "supplied"),
        genome,
        driver_id=driver_id,
        use_class="raw",
        cxx=_any_cxx(),
    )
    prepared = S.PreparedCell(
        genome, "stock", "/ccbench", "/cache",
        condition_supply_records=records[0],
        condition_meaning_records=records[1],
    )
    S.require_returned_condition_evidence(
        prepared,
        expected_request_digests=S._condition_request_digests_for_flags(
            genome.flags, driver_id=driver_id,
        ),
        use_class="raw", label="prepare_cell_fn return",
    )
    result = EvalResult(
        genome=genome, variant=pipeline.variant_id(genome),
        certified=True, aborted=False, fitness_tps=100.0,
    )
    result.condition_supply_records = records[0]
    result.condition_meaning_records = records[1]
    S.require_returned_condition_evidence(
        result,
        expected_request_digests=S._condition_request_digests_for_flags(
            genome.flags, driver_id=driver_id,
        ),
        use_class="raw", label="evaluate_fn return", expected_records=records,
    )


def test_injected_prepare_cannot_transplant_green_records_from_another_value():
    driver_id = "test.s1_direct_comparison.request-binding"
    measured = Genome("silo", {"BACKOFF_FIXED": 5})
    requested = Genome("silo", {"BACKOFF_FIXED": 10})
    records = _REAL_CONDITION_RECORDS_FOR_GENOME(
        str(TESTS / "fixtures" / "condition_meaning_gate" / "supplied"),
        measured, driver_id=driver_id, use_class="raw", cxx=_any_cxx(),
    )
    prepared = S.PreparedCell(
        measured, "stock", "/ccbench", "/cache",
        condition_supply_records=records[0],
        condition_meaning_records=records[1],
    )
    with pytest.raises(S.DriverError, match="request digest"):
        S.require_returned_condition_evidence(
            prepared,
            expected_request_digests=S._condition_request_digests_for_flags(
                requested.flags, driver_id=driver_id,
            ),
            use_class="raw", label="prepare_cell_fn return",
        )


def test_injected_prepare_cannot_self_sign_empty_green_evidence():
    genome = Genome("silo", {"BACKOFF_FIXED": 5})
    driver_id = "orchestrator.campaign.s1_direct_comparison.prepare_cell"
    supply, meaning = _forged_empty_condition_records(
        genome, driver_id=driver_id,
    )
    prepared = S.PreparedCell(
        genome, "stock", "/ccbench", "/cache",
        condition_supply_records=supply,
        condition_meaning_records=meaning,
    )
    with pytest.raises(S.DriverError, match="record が不正"):
        S.require_returned_condition_evidence(
            prepared,
            expected_request_digests=S._condition_request_digests_for_flags(
                genome.flags, driver_id=driver_id,
            ),
            use_class="raw", label="prepare_cell_fn return",
        )


def test_modified_freeze_is_refused_before_campaign_start(tmp_path):
    from orchestrator.campaign.s1_measurement_freeze import FreezeError

    calls = []

    def reject(document):
        raise FreezeError("modified")

    with pytest.raises(FreezeError, match="modified"):
        S.run_role(
            "floor", freeze_path=_write_freeze(tmp_path),
            budget_path=tmp_path / "budget.json", output_root=str(tmp_path / "out"),
            verify_document=reject, evaluate_fn=lambda *a, **k: calls.append(1),
            prepare_cell_fn=_prepared, single_tenant_fn=lambda: None)
    assert calls == []


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_run_role_available_perf_keeps_evaluate_call_shape_exact(
        tmp_path, monkeypatch):
    probe_calls = []
    evaluate_calls = []

    def probe():
        probe_calls.append(1)
        return _canonical_perf_receipt("available")

    def evaluate(genome, *args, **kwargs):
        evaluate_calls.append((args, kwargs))
        return _green(genome)

    monkeypatch.setattr(S._perf_preflight, "probe_perf_availability", probe)
    assert _run(tmp_path, "develop", evaluate) == S.EXIT_OK

    assert probe_calls == [1]
    assert evaluate_calls
    for args, kwargs in evaluate_calls:
        assert len(args) == 5
        assert set(kwargs) == {
            "numactl", "correctness", "extra_correctness", "do_bench",
            "do_settle", "src_token", "log", "ccbench_dir", "cache_root",
            "screening", "bench_max_rounds", "build_context",
            "capability_resolver", "authorization_contract",
        }
        assert "use_perf" not in kwargs
        assert "perf_preflight_receipt" not in kwargs


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_run_role_forwards_sort_contract_only_when_prepared_cell_has_one(
        tmp_path):
    from orchestrator.campaign.sort_swo_oracle import ORACLE_CONTRACT_ID

    prepared_configurations = []
    evaluate_calls = []

    @contextlib.contextmanager
    def prepare(cell, pin, *, cxx):
        del pin, cxx
        configuration = cell["configuration"]
        prepared_configurations.append(configuration)
        genome = Genome("silo", dict(cell["variant"]["flags"]))
        supply, meaning = _condition_records(genome)
        yield S.PreparedCell(
            genome, "stock", "/ccbench", "/cache",
            condition_supply_records=supply,
            condition_meaning_records=meaning,
            sort_oracle_contract_id=(
                ORACLE_CONTRACT_ID if configuration == "sort_best" else None
            ),
        )

    def evaluate(genome, *args, **kwargs):
        evaluate_calls.append(kwargs)
        return _green(genome)

    rc = S.run_role(
        "develop", freeze_path=_write_freeze(tmp_path),
        budget_path=tmp_path / "time_ledger.json",
        output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
        evaluate_fn=evaluate, prepare_cell_fn=prepare,
        single_tenant_fn=lambda: None, monotonic=_Clock(), log=lambda msg: None,
    )

    assert rc == S.EXIT_OK
    assert len(prepared_configurations) == len(evaluate_calls) == 18
    for configuration, kwargs in zip(prepared_configurations, evaluate_calls):
        if configuration == "sort_best":
            assert kwargs["sort_oracle_contract_id"] == ORACLE_CONTRACT_ID
        else:
            assert "sort_oracle_contract_id" not in kwargs


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_run_role_unavailable_perf_passes_degraded_kwargs_from_one_probe(
        tmp_path, monkeypatch):
    unavailable = _canonical_perf_receipt("unavailable")
    probe_calls = []
    evaluate_calls = []

    def probe():
        probe_calls.append(1)
        return unavailable

    def evaluate(genome, *args, **kwargs):
        evaluate_calls.append(kwargs)
        return _green(genome)

    monkeypatch.setattr(S._perf_preflight, "probe_perf_availability", probe)
    assert _run(tmp_path, "develop", evaluate) == S.EXIT_OK

    assert probe_calls == [1]
    assert evaluate_calls
    for kwargs in evaluate_calls:
        assert kwargs["use_perf"] is False
        assert kwargs["perf_preflight_receipt"] == unavailable


def test_run_role_probe_error_refuses_before_campaign_or_evaluate(
        tmp_path, monkeypatch):
    evaluate_calls = []
    monkeypatch.setattr(
        S._perf_preflight, "probe_perf_availability",
        lambda: _canonical_perf_receipt("probe_error"),
    )

    with pytest.raises(S._perf_preflight.PerfPreflightError):
        _run(
            tmp_path, "develop",
            lambda *args, **kwargs: evaluate_calls.append((args, kwargs)),
        )

    assert evaluate_calls == []
    assert not (tmp_path / "out").exists()
    assert not (tmp_path / "time_ledger.json").exists()


def test_receipt_exists_but_direct_comparison_loader_stays_legacy_strict(
        tmp_path, monkeypatch):
    from orchestrator.campaign.s1_measurement_freeze import FreezeError

    receipt = tmp_path / T080.RECEIPT_REL
    receipt.parent.mkdir(parents=True)
    receipt.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(T080, "ROOT", tmp_path)

    def adapter_must_not_run(*_args, **_kwargs):
        pytest.fail("direct comparison legacy 経路が T-080 adapter を呼んだ")

    monkeypatch.setattr(T080, "verify_receipt", adapter_must_not_run)
    monkeypatch.setattr(T080, "static_gate_adapter", adapter_must_not_run)
    assert (T080.ROOT / T080.RECEIPT_REL).is_file()

    freeze_path = _write_freeze(tmp_path)
    verified = []
    document = S.load_verified_freeze(
        freeze_path, verify_document=lambda value: verified.append(value),
    )
    assert verified == [document]
    assert document["operating_point"]["REPS"] == 5


def test_direct_comparison_production_module_does_not_import_t080_adapter():
    source = Path(S.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
            imports.extend(alias.name for alias in node.names)
    assert not [name for name in imports if "t080_freeze_migration" in name]
    assert "verify_receipt" not in source and "static_gate_adapter" not in source


def test_prepare_backoff_fixed_best_preserves_evolve_block(tmp_path, monkeypatch):
    """固定値は flag だけで選び、backoff EVOLVE-BLOCK を置換しない。"""
    from orchestrator.campaign import patchharness
    from orchestrator.campaign import p3_s4_loop as loop_axis

    worktree = tmp_path / "worktree"
    include = worktree / "include"
    include.mkdir(parents=True)
    backoff = include / "backoff.hh"
    backoff.write_text("// stock fixture\n", encoding="utf-8")
    applied = []
    monkeypatch.setattr(
        patchharness, "checkout", lambda *args, **kwargs: _fixture_checkout(worktree))
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *args, **kwargs: applied.append(args) or _fixture_backoff_patch(backoff))
    monkeypatch.setattr(
        S.source_digest, "resolve",
        lambda *args, **kwargs: "fixture-source",
    )
    monkeypatch.setattr(loop_axis, "quarantine", lambda *args, **kwargs: pytest.fail("hole を置換してはならない"))
    cell = {
        "configuration": "backoff_fixed_best",
        "variant": {"backoff_us": 5, "flags": {"BACK_OFF": 1, "BACKOFF_FIXED": 5}},
    }

    with S.prepare_cell(
            cell, "d706650cdb31e442bef45b9b4216951d4fb40969",
            cxx="g++-13") as prepared:
        assert prepared.genome.flags["BACKOFF_FIXED"] == 5
        content = backoff.read_text(encoding="utf-8")
        assert "EVOLVE-BLOCK-BEGIN silo-backoff-magnitude" in content
        assert "EVOLVE-BLOCK-END silo-backoff-magnitude" in content
        assert "#if BACKOFF_FIXED >= 0" in content
        assert "static_cast<double>(BACKOFF_FIXED)" in content
        assert "Backoff_.load" in content
        assert "\n5\n" not in content

    assert applied == [(str(S.ROOT / loop_axis.TEMPLATE_PATCH),
                        "d706650cdb31e442bef45b9b4216951d4fb40969")]


def test_prepare_backoff_fixed_best_refuses_flag_value_mismatch(tmp_path, monkeypatch):
    from orchestrator.campaign import patchharness

    worktree = tmp_path / "worktree"
    monkeypatch.setattr(patchharness, "checkout", lambda *args, **kwargs: _fixture_checkout(worktree))
    cell = {
        "configuration": "backoff_fixed_best",
        "variant": {"backoff_us": 5, "flags": {"BACK_OFF": 1, "BACKOFF_FIXED": 4}},
    }

    with pytest.raises(S.DriverError, match="backoff_us と flags.BACKOFF_FIXED が不一致"):
        with S.prepare_cell(
                cell, "d706650cdb31e442bef45b9b4216951d4fb40969",
                cxx="g++-13"):
            pass


def _capture_prepare_quarantine(
        tmp_path, monkeypatch, cell, implementation_key):
    from orchestrator.campaign import patchharness
    from orchestrator.campaign import p3_s4_loop as loop_axis
    from orchestrator.campaign import sort_swo_oracle as oracle

    expected = copy.deepcopy(cell)
    worktree = tmp_path / "worktree"
    calls = []
    resolve_calls = []
    resolve_evidence_calls = []

    def fake_quarantine(sub, implementation, *, marker_id, source_rel, write):
        calls.append({
            "sub": sub,
            "implementation": implementation,
            "marker_id": marker_id,
            "source_rel": source_rel,
            "write": write,
        })
        return types.SimpleNamespace(passed=True), "base", "edited", "diff"

    monkeypatch.setattr(
        patchharness, "checkout", lambda *args, **kwargs: _fixture_checkout(worktree))
    monkeypatch.setattr(
        patchharness, "applied", lambda *args, **kwargs: _fixture_checkout(worktree))

    def fake_resolve(*args, **kwargs):
        resolve_calls.append((args, kwargs))
        return "fixture-source"

    def fake_resolve_evidence(*args, **kwargs):
        resolve_evidence_calls.append((args, kwargs))
        return types.SimpleNamespace(src_token="fixture-sort-source")

    monkeypatch.setattr(S.source_digest, "resolve", fake_resolve)
    monkeypatch.setattr(
        S.source_digest, "resolve_evidence", fake_resolve_evidence,
    )
    monkeypatch.setattr(loop_axis, "quarantine", fake_quarantine)
    receipt = oracle.OracleReceipt(
        contract_id=oracle.ORACLE_CONTRACT_ID,
        materialized_hole_sha256="1" * 64,
        proposal_sha256="2" * 64,
        corpus_id=oracle.CORPUS_ID,
        corpus_version=oracle.CORPUS_VERSION,
        compiler_realpath="/fixture/cxx",
        compiler_version="fixture-cxx 1",
        compile_flags_sha256=oracle.COMPILE_FLAGS_SHA256,
        tu_sha256="3" * 64,
        tu_template_sha256=oracle.TU_TEMPLATE_SHA256,
        dependency_root_realpath="/fixture/dependency",
        dependency_config_sha256="4" * 64,
        dependency_manifest_sha256=oracle.DEPENDENCY_MANIFEST_SHA256,
    )
    monkeypatch.setattr(
        oracle, "check_materialized_sort_swo",
        lambda *args, **kwargs: oracle.SortSwoOracleResult(
            oracle.OracleStatus.PASS, "1" * 64, "2" * 64,
            receipt=receipt,
        ),
    )

    with S.prepare_cell(
            cell, "d706650cdb31e442bef45b9b4216951d4fb40969",
            cxx="g++-13") as prepared:
        pass

    assert len(calls) == 1
    assert calls[0]["sub"] == str(worktree)
    assert calls[0]["write"] is True
    assert calls[0]["implementation"] == expected["variant"][implementation_key]
    assert cell == expected
    calls[0]["resolve_calls"] = resolve_calls
    calls[0]["resolve_evidence_calls"] = resolve_evidence_calls
    calls[0]["prepared"] = prepared
    return calls[0]


def _oracle_reject_result():
    from orchestrator.campaign import sort_swo_oracle as oracle

    receipt = oracle.OracleReceipt(
        contract_id=oracle.ORACLE_CONTRACT_ID,
        materialized_hole_sha256="a" * 64,
        proposal_sha256="b" * 64,
        corpus_id=oracle.CORPUS_ID,
        corpus_version=oracle.CORPUS_VERSION,
        compiler_realpath="/fixture/cxx",
        compiler_version="fixture-cxx 1",
        compile_flags_sha256=oracle.COMPILE_FLAGS_SHA256,
        tu_sha256="c" * 64,
        tu_template_sha256=oracle.TU_TEMPLATE_SHA256,
        dependency_root_realpath="/fixture/dependency",
        dependency_config_sha256="d" * 64,
        dependency_manifest_sha256=oracle.DEPENDENCY_MANIFEST_SHA256,
    )
    finding = oracle.SortSwoFinding(
        oracle.OracleRejectKind.MUTATION,
        "snapshot-arena-write-denied",
        corpus_id=f"{oracle.CORPUS_ID}/corpus-0",
        order_id=1,
        observations=({
            "point": "kernel-read-only-arena", "write_denied": True,
        },),
    )
    return oracle.SortSwoOracleResult(
        oracle.OracleStatus.REJECT,
        "a" * 64,
        "b" * 64,
        finding=finding,
        receipt=receipt,
    )


def _gate_cell(configuration, predicate):
    return {
        "configuration": configuration,
        "variant": {
            "gate_predicate": predicate,
            "flags": {
                "BACKOFF_TRIGGER_GATING": 1,
                "BACK_OFF": 1,
                "NO_WAIT_LOCKING_IN_VALIDATION": 1,
                "NO_WAIT_OF_TICTOC": 0,
                "WAL": 0,
            },
        },
    }


def test_prepare_configuration_allowlist_is_fixed_six():
    assert S._PREPARE_CELL_CONFIGURATIONS == frozenset({
        "backoff_fixed_best",
        "ident_all",
        "p2_2_flag_opt",
        "sort_best",
        "stock_common",
        "system_gate",
    })


@pytest.mark.parametrize("configuration", ["stock_common", "p2_2_flag_opt"])
def test_prepare_flags_only_configurations_do_not_patch_or_quarantine(
        tmp_path, monkeypatch, configuration):
    from orchestrator.campaign import patchharness
    from orchestrator.campaign import p3_s4_loop as loop_axis

    worktree = tmp_path / "worktree"
    monkeypatch.setattr(
        patchharness, "checkout",
        lambda *args, **kwargs: _fixture_checkout(worktree),
    )
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *args, **kwargs: pytest.fail("flags-only 構成で patch してはならない"),
    )
    monkeypatch.setattr(
        loop_axis, "quarantine",
        lambda *args, **kwargs: pytest.fail("flags-only 構成で quarantine してはならない"),
    )
    monkeypatch.setattr(
        S.source_digest, "resolve", lambda *args, **kwargs: "fixture-source",
    )
    flags = {"BACK_OFF": 1, "WAL": 0}
    cell = {"configuration": configuration, "variant": {"flags": flags}}

    with S.prepare_cell(cell, "fixture-pin", cxx="site-cxx") as prepared:
        assert prepared.genome == Genome("silo", flags)
        assert prepared.src_token == "fixture-source"


@pytest.mark.parametrize(
    "cell",
    [
        pytest.param(
            {
                "configuration": "backoff_fixed_best",
                "variant": {
                    "backoff_us": 5,
                    "flags": {"BACK_OFF": 1, "BACKOFF_FIXED": 5},
                },
            },
            id="backoff-fixed-best",
        ),
        pytest.param(
            {
                "configuration": "stock_common",
                "variant": {"flags": {"BACK_OFF": 1}},
            },
            id="stock-common",
        ),
    ],
)
def test_prepare_non_sort_cells_keep_unbound_resolve_path(
        tmp_path, monkeypatch, cell):
    from orchestrator.campaign import patchharness

    worktree = tmp_path / "worktree"
    resolve_calls = []

    def resolve(*args, **kwargs):
        resolve_calls.append((args, kwargs))
        return "fixture-source"

    monkeypatch.setattr(
        patchharness, "checkout",
        lambda *args, **kwargs: _fixture_checkout(worktree),
    )
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *args, **kwargs: _fixture_checkout(worktree),
    )
    monkeypatch.setattr(S.source_digest, "resolve", resolve)
    monkeypatch.setattr(
        S.source_digest, "resolve_evidence",
        lambda *args, **kwargs: pytest.fail(
            "非 sort_best で resolve_evidence を呼んではならない"
        ),
    )

    with S.prepare_cell(cell, "fixture-pin", cxx="site-cxx") as prepared:
        assert prepared.src_token == "fixture-source"
        assert prepared.sort_oracle_contract_id is None

    assert len(resolve_calls) == 1
    args, kwargs = resolve_calls[0]
    assert args == (prepared.genome, "fixture-pin")
    assert kwargs == {"ccbench_dir": str(worktree), "cxx": "site-cxx"}


def test_prepare_cell_passes_site_cxx_to_source_digest(tmp_path, monkeypatch):
    from orchestrator.campaign import patchharness

    worktree = tmp_path / "worktree"
    observed = []

    def resolve(genome, ccbench_pin, *, ccbench_dir, cxx):
        observed.append((genome, ccbench_pin, ccbench_dir, cxx))
        return "fixture-source"

    monkeypatch.setattr(
        patchharness, "checkout",
        lambda *args, **kwargs: _fixture_checkout(worktree),
    )
    monkeypatch.setattr(S.source_digest, "resolve", resolve)
    flags = {"BACK_OFF": 1, "WAL": 0}
    cell = {"configuration": "stock_common", "variant": {"flags": flags}}

    with S.prepare_cell(cell, "fixture-pin", cxx="site-cxx") as prepared:
        assert prepared.src_token == "fixture-source"

    assert observed == [(
        Genome("silo", flags), "fixture-pin", str(worktree), "site-cxx",
    )]


def test_prepare_cell_refuses_missing_cxx_instead_of_falling_back(
        tmp_path, monkeypatch):
    from orchestrator.campaign import patchharness

    worktree = tmp_path / "worktree"
    monkeypatch.setattr(
        patchharness, "checkout",
        lambda *args, **kwargs: _fixture_checkout(worktree),
    )
    monkeypatch.setattr(
        S.source_digest, "resolve",
        lambda *args, cxx="g++-13", **kwargs: "fixture-source",
    )
    cell = {
        "configuration": "stock_common",
        "variant": {"flags": {"BACK_OFF": 1, "WAL": 0}},
    }

    with pytest.raises(TypeError, match="cxx"):
        with S.prepare_cell(cell, "fixture-pin"):
            pass


@pytest.mark.parametrize(
    "configuration", ["system-gate", "future_configuration", "unknown"],
)
def test_prepare_rejects_multiple_unknown_configurations_before_checkout(
        monkeypatch, configuration):
    from orchestrator.campaign import patchharness

    monkeypatch.setattr(
        patchharness, "checkout",
        lambda *args, **kwargs: pytest.fail("未知構成で checkout してはならない"),
    )
    cell = {
        "configuration": configuration,
        "variant": {"flags": {"BACK_OFF": 1}},
    }
    with pytest.raises(S.DriverError) as excinfo:
        with S.prepare_cell(cell, "fixture-pin", cxx="site-cxx"):
            pass
    assert str(excinfo.value) == f"未知の freeze configuration: {configuration!r}"


def test_prepare_rejects_configuration_added_only_to_producer_domain(
        monkeypatch):
    from orchestrator.campaign import patchharness, s1_measurement_freeze

    added = "future_configuration"
    monkeypatch.setattr(
        s1_measurement_freeze,
        "CONFIGURATIONS",
        s1_measurement_freeze.CONFIGURATIONS + (added,),
    )
    monkeypatch.setattr(
        patchharness, "checkout",
        lambda *args, **kwargs: pytest.fail("producer 追加値を checkout してはならない"),
    )
    assert added in s1_measurement_freeze.CONFIGURATIONS
    with pytest.raises(S.DriverError) as excinfo:
        with S.prepare_cell(
                {"configuration": added, "variant": {"flags": {"BACK_OFF": 1}}},
                "fixture-pin", cxx="site-cxx"):
            pass
    assert str(excinfo.value) == f"未知の freeze configuration: {added!r}"


def test_fresh_prepare_rejects_configuration_added_only_to_producer_domain(
        monkeypatch):
    from orchestrator.campaign import patchharness, s1_measurement_freeze

    added = "future_configuration"
    monkeypatch.setattr(
        s1_measurement_freeze,
        "CONFIGURATIONS",
        s1_measurement_freeze.CONFIGURATIONS + (added,),
    )
    monkeypatch.setattr(
        patchharness, "checkout",
        lambda *args, **kwargs: pytest.fail(
            "producer 追加値を checkout してはならない"
        ),
    )
    module_name = "orchestrator.campaign._s1_direct_comparison_producer_independence_test"
    spec = importlib.util.spec_from_file_location(module_name, S.__file__)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        assert added in s1_measurement_freeze.CONFIGURATIONS
        with pytest.raises(module.DriverError) as excinfo:
            with module.prepare_cell(
                    {
                        "configuration": added,
                        "variant": {"flags": {"BACK_OFF": 1}},
                    },
                    "fixture-pin", cxx="site-cxx"):
                pass
        assert str(excinfo.value) == (
            f"未知の freeze configuration: {added!r}"
        )
        assert added not in module._PREPARE_CELL_CONFIGURATIONS
    finally:
        sys.modules.pop(module_name, None)


def test_real_source_digest_unifies_all_outer_whitespace_tokens(tmp_path):
    from orchestrator.campaign import p3_s4_loop as loop_axis

    cxx = _any_cxx()
    sub, head = _fake_ccbench_repo(tmp_path / "fake-ccbench")
    source = sub / axis_trigger_gating.SOURCE_REL
    predicate = emit_predicate(TriggerGateIR(20))
    genome = Genome("silo", {"BACK_OFF": 1, "BACKOFF_TRIGGER_GATING": 1})

    exact_result, *_ = loop_axis.quarantine(
        str(sub), predicate,
        marker_id=axis_trigger_gating.MARKER_ID,
        source_rel=axis_trigger_gating.SOURCE_REL,
        write=True,
    )
    assert exact_result.passed
    exact_source = source.read_bytes()
    exact_token = S.source_digest.resolve(
        genome, head, ccbench_dir=str(sub), cxx=cxx)
    exact_variant = pipeline.variant_id(genome, exact_token)

    for name, outer in _OUTER_WHITESPACE:
        source.write_text(_FAKE_GATE_TRANSACTION_CC, encoding="utf-8")
        result, *_ = loop_axis.quarantine(
            str(sub), f"{outer}{predicate}{outer}",
            marker_id=axis_trigger_gating.MARKER_ID,
            source_rel=axis_trigger_gating.SOURCE_REL,
            write=True,
        )
        assert result.passed, name
        assert source.read_bytes() == exact_source, name
        token = S.source_digest.resolve(
            genome, head, ccbench_dir=str(sub), cxx=cxx)
        assert token == exact_token, name
        assert pipeline.variant_id(genome, token) == exact_variant, name


@pytest.mark.parametrize(
    "mask", [pytest.param(mask, id=f"mask-{mask:02d}") for mask in range(32)],
)
def test_prepare_accepts_all_32_canonical_predicates(
        tmp_path, monkeypatch, mask):
    predicate = emit_predicate(TriggerGateIR(mask))
    received = _capture_prepare_quarantine(
        tmp_path, monkeypatch, _gate_cell("system_gate", predicate),
        "gate_predicate",
    )

    assert received["implementation"] == predicate
    assert received["marker_id"] == axis_trigger_gating.MARKER_ID
    assert received["source_rel"] == axis_trigger_gating.SOURCE_REL


@pytest.mark.parametrize(
    "configuration, predicate",
    [
        *[
            pytest.param(
                "system_gate", EXPECTED_GATES[workload]["gate_predicate"],
                id=f"{workload}-system-gate",
            )
            for workload in ("balanced", "write-heavy", "read-heavy")
        ],
        *[
            pytest.param(
                "ident_all", EXPECTED_IDENT_ALL_PREDICATE,
                id=f"{workload}-ident-all",
            )
            for workload in ("balanced", "write-heavy", "read-heavy")
        ],
    ],
)
def test_prepare_accepts_six_frozen_gate_predicates(
        tmp_path, monkeypatch, configuration, predicate):
    received = _capture_prepare_quarantine(
        tmp_path, monkeypatch, _gate_cell(configuration, predicate),
        "gate_predicate",
    )

    assert received["implementation"] == predicate
    assert received["marker_id"] == axis_trigger_gating.MARKER_ID
    assert received["source_rel"] == axis_trigger_gating.SOURCE_REL


def test_prepare_rejects_noncanonical_freeze_predicate(tmp_path, monkeypatch):
    from orchestrator.campaign import patchharness
    from orchestrator.campaign import p3_s4_loop as loop_axis

    predicate = "izanagi_gate_pass = true;"
    worktree = tmp_path / "worktree"
    monkeypatch.setattr(
        patchharness, "checkout",
        lambda *args, **kwargs: _fixture_checkout(worktree),
    )
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *args, **kwargs: _fixture_checkout(worktree),
    )
    monkeypatch.setattr(
        loop_axis, "quarantine",
        lambda *args, **kwargs: (
            types.SimpleNamespace(passed=True), "base", "edited", "diff"),
    )
    monkeypatch.setattr(
        S.source_digest, "resolve", lambda *args, **kwargs: "fixture-source",
    )

    with pytest.raises(S.DriverError) as excinfo:
        with S.prepare_cell(
                _gate_cell("system_gate", predicate),
                "d706650cdb31e442bef45b9b4216951d4fb40969",
                cxx="g++-13"):
            pass

    assert str(excinfo.value) == "freeze gate_predicate が正準集合外"
    assert predicate not in str(excinfo.value)


def test_prepare_rejects_noncanonical_predicate_with_real_quarantine(
        tmp_path, monkeypatch):
    from orchestrator.campaign import patchharness

    predicate = "izanagi_gate_pass = true;"
    worktree = tmp_path / "worktree"
    monkeypatch.setattr(
        patchharness, "checkout",
        lambda *args, **kwargs: _fixture_checkout(worktree),
    )
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *args, **kwargs: _fixture_gate_patch(worktree),
    )
    monkeypatch.setattr(
        S.source_digest, "resolve", lambda *args, **kwargs: "fixture-source",
    )

    with pytest.raises(S.DriverError):
        with S.prepare_cell(
                _gate_cell("system_gate", predicate),
                "d706650cdb31e442bef45b9b4216951d4fb40969",
                cxx="g++-13"):
            pass


@pytest.mark.parametrize(
    "comparator",
    [
        pytest.param(
            "\n  sort(write_set_.begin(), write_set_.end(),\n"
            "       [](const WriteElement& lhs, const WriteElement& rhs) {\n"
            "         return lhs.get_tid() < rhs.get_tid();\n"
            "       });  \n",
            id="synthetic-whitespace-sentinel",
        ),
        pytest.param(
            EXPECTED_SORT["balanced"]["comparator"],
            id="canonical-balanced-sp-dd",
        ),
        pytest.param(
            EXPECTED_SORT["write-heavy"]["comparator"],
            id="canonical-write-heavy-sk-ad",
        ),
    ],
)
def test_prepare_sort_best_passes_comparator_verbatim_to_quarantine(
        tmp_path, monkeypatch, comparator):
    from orchestrator.campaign import p3_s4_loop_sort as sort_axis

    cell = {
        "configuration": "sort_best",
        "variant": {
            "comparator": comparator,
            "flags": {
                "BACK_OFF": 1,
                "NO_WAIT_LOCKING_IN_VALIDATION": 1,
                "NO_WAIT_OF_TICTOC": 0,
                "SORT_VARIANT": 1,
                "WAL": 0,
            },
        },
    }

    received = _capture_prepare_quarantine(
        tmp_path, monkeypatch, cell, "comparator")

    assert received["marker_id"] == sort_axis.MARKER_ID
    assert received["source_rel"] == sort_axis.SOURCE_REL


def test_prepare_sort_best_binds_attested_oracle_contract_into_src_token(
        tmp_path, monkeypatch):
    from orchestrator.campaign import sort_swo_oracle as oracle

    cell = {
        "configuration": "sort_best",
        "variant": {
            "comparator": EXPECTED_SORT["balanced"]["comparator"],
            "flags": {"BACK_OFF": 1, "SORT_VARIANT": 1},
        },
    }

    received = _capture_prepare_quarantine(
        tmp_path, monkeypatch, cell, "comparator",
    )

    assert received["resolve_calls"] == []
    assert len(received["resolve_evidence_calls"]) == 1
    args, kwargs = received["resolve_evidence_calls"][0]
    prepared = received["prepared"]
    assert args == (
        prepared.genome,
        "d706650cdb31e442bef45b9b4216951d4fb40969",
    )
    assert kwargs == {
        "ccbench_dir": str(tmp_path / "worktree"),
        "cxx": "g++-13",
        "sort_oracle_contract_id": oracle.ORACLE_CONTRACT_ID,
    }
    assert prepared.src_token == "fixture-sort-source"
    assert prepared.sort_oracle_contract_id == oracle.ORACLE_CONTRACT_ID


def test_prepare_sort_best_reject_carries_structured_oracle_attempt(
        tmp_path, monkeypatch):
    from orchestrator.campaign import patchharness
    from orchestrator.campaign import p3_s4_loop as loop_axis
    from orchestrator.campaign import sort_swo_oracle as oracle

    worktree = tmp_path / "worktree"
    monkeypatch.setattr(
        patchharness, "checkout",
        lambda *args, **kwargs: _fixture_checkout(worktree),
    )
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *args, **kwargs: _fixture_checkout(worktree),
    )
    monkeypatch.setattr(
        loop_axis, "quarantine",
        lambda *args, **kwargs: (
            types.SimpleNamespace(passed=True), "base", "edited", "diff"),
    )
    monkeypatch.setattr(
        oracle, "resolve_oracle_environment", lambda *args, **kwargs: None,
    )
    result = _oracle_reject_result()
    monkeypatch.setattr(
        oracle, "check_materialized_sort_swo", lambda *args, **kwargs: result,
    )
    monkeypatch.setattr(
        S.source_digest, "resolve",
        lambda *args, **kwargs: pytest.fail("REJECT 後に source resolve してはならない"),
    )
    resolve_evidence_calls = []

    def resolve_evidence(*args, **kwargs):
        resolve_evidence_calls.append((args, kwargs))
        pytest.fail("REJECT 後に source evidence を resolve してはならない")

    monkeypatch.setattr(
        S.source_digest, "resolve_evidence", resolve_evidence,
    )
    cell = {
        "configuration": "sort_best",
        "variant": {
            "comparator": "sort(write_set_.begin(), write_set_.end());",
            "flags": {"BACK_OFF": 1, "SORT_VARIANT": 1},
        },
    }

    with pytest.raises(S._SortSwoOracleRejected) as excinfo:
        with S.prepare_cell(
                cell, "d706650cdb31e442bef45b9b4216951d4fb40969",
                cxx="g++-13"):
            pass

    record = excinfo.value.oracle_attempt
    assert isinstance(excinfo.value, S.DriverError)
    assert record["event"] == "sort-swo-oracle-attempt"
    assert record["classification"] == "reject"
    assert record["reason_code"] == result.finding.reason_code
    assert record["oracle_finding"] == result.finding.as_dict()
    assert record["materialized_hole_sha256"] == "a" * 64
    assert record["proposal_sha256"] == "b" * 64
    assert record["oracle_contract_id"] == oracle.ORACLE_CONTRACT_ID
    assert record["oracle_receipt"] == result.receipt.as_dict()
    assert resolve_evidence_calls == []


@pytest.mark.parametrize(
    "predicate",
    [
        pytest.param(
            "\n  izanagi_gate_pass = izanagi_abort_reason_ == "
            "IzanagiAbortReason::kUnset || izanagi_abort_reason_ == "
            "IzanagiAbortReason::kReadValiLocked;  \n",
            id="synthetic-whitespace-sentinel",
        ),
        pytest.param(
            EXPECTED_GATES["balanced"]["gate_predicate"],
            id="canonical-balanced-g-rl",
        ),
        pytest.param(
            EXPECTED_GATES["write-heavy"]["gate_predicate"],
            id="canonical-write-heavy-g-rt",
        ),
    ],
)
def test_prepare_system_gate_passes_predicate_verbatim_to_quarantine(
        tmp_path, monkeypatch, predicate):
    from orchestrator.campaign import axis_trigger_gating as gate_axis

    cell = {
        "configuration": "system_gate",
        "variant": {
            "gate_predicate": predicate,
            "flags": {
                "BACKOFF_TRIGGER_GATING": 1,
                "BACK_OFF": 1,
                "NO_WAIT_LOCKING_IN_VALIDATION": 1,
                "NO_WAIT_OF_TICTOC": 0,
                "WAL": 0,
            },
        },
    }

    received = _capture_prepare_quarantine(
        tmp_path, monkeypatch, cell, "gate_predicate")

    assert received["marker_id"] == gate_axis.MARKER_ID
    assert received["source_rel"] == gate_axis.SOURCE_REL


@pytest.mark.parametrize(
    "predicate",
    [
        pytest.param(
            "\n    izanagi_gate_pass = izanagi_abort_reason_ == "
            "IzanagiAbortReason::kUnset || izanagi_abort_reason_ == "
            "IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == "
            "IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == "
            "IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == "
            "IzanagiAbortReason::kReadValiLocked || izanagi_abort_reason_ == "
            "IzanagiAbortReason::kNodeVali;  \n",
            id="synthetic-whitespace-sentinel",
        ),
        pytest.param(
            EXPECTED_IDENT_ALL_PREDICATE,
            id="canonical-ident-all",
        ),
    ],
)
def test_prepare_ident_all_passes_predicate_verbatim_to_quarantine(
        tmp_path, monkeypatch, predicate):
    from orchestrator.campaign import axis_trigger_gating as gate_axis

    cell = {
        "configuration": "ident_all",
        "variant": {
            "gate_predicate": predicate,
            "flags": {
                "BACKOFF_TRIGGER_GATING": 1,
                "BACK_OFF": 1,
                "NO_WAIT_LOCKING_IN_VALIDATION": 1,
                "NO_WAIT_OF_TICTOC": 0,
                "WAL": 0,
            },
        },
    }

    received = _capture_prepare_quarantine(
        tmp_path, monkeypatch, cell, "gate_predicate")

    assert received["marker_id"] == gate_axis.MARKER_ID
    assert received["source_rel"] == gate_axis.SOURCE_REL


def test_s1_v2_trial_does_not_reuse_v1_campaign_id():
    campaign_id = str(S.ident.campaign_id(S.config_for(_freeze(), "develop")))
    assert campaign_id != "s1-direct-develop-direct-comparison-7bccdf1a"


def test_s1_search_identity_binds_exact_sort_swo_contract():
    from orchestrator.campaign.sort_swo_oracle import ORACLE_CONTRACT_ID

    cfg = S.config_for(_freeze(), "develop")
    assert cfg.search_config["sort_swo_oracle"] == ORACLE_CONTRACT_ID


def test_schedule_mutation_refused_and_deviation_recorded(tmp_path):
    document = _freeze()
    freeze_path = _write_freeze(tmp_path, document)
    layout = S.layout_for(document, "floor", output_root=str(tmp_path / "out"))
    layout.ensure()
    wal.write_lock(layout, build_v2_lock(
        S.ident.canonical_preimage(S.config_for(document, "floor"))
    ))
    schedule = S.schedule_for_role(document, "floor")
    S._append_event(layout, S._base_event(schedule[0], "v0", 0))
    S._append_event(layout, S._base_event(schedule[0], "v0-duplicate", 0))

    with pytest.raises(S.ScheduleDeviation):
        S.run_role(
            "floor", freeze_path=freeze_path, budget_path=tmp_path / "budget.json",
            output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
            evaluate_fn=_green, prepare_cell_fn=_prepared,
            single_tenant_fn=lambda: None, monotonic=_Clock())
    events = S.read_session_ledger(layout)
    assert any(e.get("event") == "deviation" for e in events)
    budget = S.read_budget(tmp_path / "budget.json")
    assert any(e["note"].startswith("schedule-deviation:") for e in budget["entries"])


def test_unknown_status_is_redacted_from_exception_deviation_and_budget(tmp_path):
    raw_status = "future-status\nINJECT"
    document = _freeze()
    freeze_path = _write_freeze(tmp_path, document)
    output_root = str(tmp_path / "out")
    layout = S.layout_for(document, "floor", output_root=output_root).ensure()
    wal.write_lock(layout, build_v2_lock(
        S.ident.canonical_preimage(S.config_for(document, "floor"))
    ))
    item = S.schedule_for_role(document, "floor")[0]
    start = S._base_event(item, "v0", 0)
    S._append_event(layout, start)
    S._append_event(layout, {
        **start,
        "event": "session-result",
        "status": raw_status,
        "reason": "fixture",
    })

    with pytest.raises(S.ScheduleDeviation) as caught:
        S.run_role(
            "floor", freeze_path=freeze_path, budget_path=tmp_path / "budget.json",
            output_root=output_root, verify_document=lambda doc: None,
            evaluate_fn=_green, prepare_cell_fn=_prepared,
            single_tenant_fn=lambda: None, monotonic=_Clock(), log=lambda msg: None,
        )

    deviation_reasons = [
        event["reason"] for event in S.read_session_ledger(layout)
        if event.get("event") == "deviation"
    ]
    budget_notes = [entry["note"] for entry in S.read_budget(
        tmp_path / "budget.json",
    )["entries"]]
    outputs = [str(caught.value), *deviation_reasons, *budget_notes]
    assert deviation_reasons and budget_notes
    assert all(raw_status not in output for output in outputs)
    assert all("sha256_12=" in output for output in outputs)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_budget_shortage_does_not_start_session(tmp_path):
    budget_path = tmp_path / "time_ledger.json"
    S.append_budget_entry(
        budget_path, role="floor", started_iso="2026-07-15T00:00:00+00:00",
        wall_s=43_199.0, phase="floor", note="existing non-retry work")
    calls = []
    rc = S.run_role(
        "floor", freeze_path=_write_freeze(tmp_path), budget_path=budget_path,
        output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
        evaluate_fn=lambda *a, **k: calls.append(1), prepare_cell_fn=_prepared,
        single_tenant_fn=lambda: None, monotonic=_Clock(), log=lambda msg: None)
    assert rc == S.EXIT_BUDGET
    assert calls == []
    document = _freeze()
    layout = S.layout_for(document, "floor", output_root=str(tmp_path / "out"))
    assert any(e.get("event") == "budget-refused" for e in S.read_session_ledger(layout))


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_budget_preflight_uses_conservative_upper_bound(tmp_path):
    budget_path = tmp_path / "time_ledger.json"
    # 性能実行の下限15秒は残るが、保守上界15分には足りない通常枠残額。
    S.append_budget_entry(
        budget_path, role="floor", started_iso="2026-07-15T00:00:00+00:00",
        wall_s=35_900.0, phase="floor", note="existing non-retry work")
    calls = []
    rc = S.run_role(
        "floor", freeze_path=_write_freeze(tmp_path), budget_path=budget_path,
        output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
        evaluate_fn=lambda *a, **k: calls.append(1), prepare_cell_fn=_prepared,
        single_tenant_fn=lambda: None, monotonic=_Clock(), log=lambda msg: None)
    assert rc == S.EXIT_BUDGET
    assert calls == []


def test_budget_status_parser_is_anchored_before_free_text_reason(tmp_path):
    budget_path = tmp_path / "time_ledger.json"
    S.append_budget_entry(
        budget_path, role="floor", started_iso="2026-08-13T00:00:00+00:00",
        wall_s=1.0, phase="floor",
        note=("session: index=0 attempt=0 status=success "
              "reason=mentions status=verifier-red and status=oracle-reject"),
    )
    assert S._terminal_exit_code(budget_path, []) is None

    S.append_budget_entry(
        budget_path, role="floor", started_iso="2026-08-13T00:00:01+00:00",
        wall_s=1.0, phase="floor",
        note="session: index=1 attempt=0 status=oracle-reject reason=swo-asymmetric",
    )
    assert S._terminal_exit_code(budget_path, []) == S.EXIT_ORACLE_REJECT


def test_verifier_red_has_priority_across_budget_and_local_ledger(tmp_path):
    budget_path = tmp_path / "time_ledger.json"
    S.append_budget_entry(
        budget_path, role="floor", started_iso="2026-08-13T00:00:00+00:00",
        wall_s=1.0, phase="floor",
        note="session: index=0 attempt=0 status=oracle-reject reason=swo-asymmetric",
    )
    local = [{"event": "session-result", "status": "verifier-red"}]
    assert S._terminal_exit_code(budget_path, local) == S.EXIT_VERIFIER_RED


@pytest.mark.parametrize("unknown_status", ["future-status", ["not", "hashable"]])
def test_unknown_session_status_is_explicit_schedule_deviation(unknown_status):
    item = S.schedule_for_role(_freeze(), "develop")[0]
    events = [
        S._base_event(item, "v", 0),
        {**S._base_event(item, "v", 0), "event": "session-result",
         "status": unknown_status, "reason": "fixture"},
    ]
    with pytest.raises(S.ScheduleDeviation, match="status が未知") as caught:
        S.validate_session_events(events, [item])
    message = str(caught.value)
    assert "sha256_12=" in message
    for fragment in ("future-status", "not", "hashable"):
        assert fragment not in message


def test_malformed_or_unknown_budget_session_status_fails_closed(tmp_path):
    budget_path = tmp_path / "time_ledger.json"
    S.append_budget_entry(
        budget_path, role="floor", started_iso="2026-08-13T00:00:00+00:00",
        wall_s=1.0, phase="floor",
        note="session: index=0 attempt=0 status=future-status reason=fixture",
    )
    with pytest.raises(S.DriverError, match="status が未知") as caught:
        S._terminal_exit_code(budget_path, [])
    assert "future-status" not in str(caught.value)
    assert "sha256_12=" in str(caught.value)


def test_terminal_exit_code_redundant_local_guard_rejects_unknown_status(tmp_path):
    raw_status = "future-local-status"
    with pytest.raises(S.ScheduleDeviation, match="status が未知") as caught:
        S._terminal_exit_code(
            tmp_path / "time_ledger.json",
            [{"event": "session-result", "status": raw_status}],
        )
    assert raw_status not in str(caught.value)
    assert "sha256_12=" in str(caught.value)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_retry_limit_abandons_session_and_continues(tmp_path):
    calls = []

    def evaluate(genome, *args, **kwargs):
        calls.append(1)
        if len(calls) <= 3:
            raise RuntimeError("machine failure")
        return _green(genome)

    rc = _run(tmp_path, "block1", evaluate)
    assert rc == S.EXIT_INCOMPLETE
    assert len(calls) == 3 + 71  # 先頭を3 attempt、残り71 session は1回ずつ。
    document = _freeze()
    layout = S.layout_for(document, "block1", output_root=str(tmp_path / "out"))
    events = S.read_session_ledger(layout)
    assert any(e.get("event") == "session-result" and e.get("schedule_index") == 0
               and e.get("status") == "abandoned" for e in events)
    assert any(e.get("event") == "session-start" and e.get("schedule_index") == 1
               for e in events)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_prepare_transient_failure_retries_twice_then_succeeds(tmp_path):
    prepare_calls = []
    evaluate_calls = []

    @contextlib.contextmanager
    def flaky_prepare(cell, pin, *, cxx):
        prepare_calls.append(1)
        if len(prepare_calls) <= 2:
            raise OSError("temporary checkout failure")
        genome = Genome("silo", dict(cell["variant"]["flags"]))
        supply, meaning = _condition_records(genome)
        yield S.PreparedCell(
            genome, "stock", "/ccbench", "/cache",
            condition_supply_records=supply,
            condition_meaning_records=meaning,
        )

    def evaluate(genome, *args, **kwargs):
        evaluate_calls.append(1)
        return _green(genome)

    rc = S.run_role(
        "develop", freeze_path=_write_freeze(tmp_path),
        budget_path=tmp_path / "time_ledger.json", output_root=str(tmp_path / "out"),
        verify_document=lambda doc: None, evaluate_fn=evaluate,
        prepare_cell_fn=flaky_prepare, single_tenant_fn=lambda: None,
        monotonic=_Clock(), log=lambda msg: None)
    assert rc == S.EXIT_OK
    assert len(prepare_calls) == 20
    assert len(evaluate_calls) == 18
    layout = S.layout_for(_freeze(), "develop", output_root=str(tmp_path / "out"))
    events = S.read_session_ledger(layout)
    assert S.validate_session_ledger(
        layout, S.schedule_for_role(_freeze(), "develop"),
    ) == 18
    first_starts = [
        e for e in events
        if e.get("event") == "session-start" and e.get("schedule_index") == 0
    ]
    assert [e["attempt"] for e in first_starts] == [0, 1, 2]
    assert len([
        e for e in events
        if e.get("event") == "retry" and e.get("retry_of") == 0
    ]) == 2
    budget = S.read_budget(tmp_path / "time_ledger.json")
    assert len([
        e for e in budget["entries"]
        if e["note"].startswith("machine-failure-retry:")
    ]) == 2


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_s1_oracle_reject_is_distinct_terminal_and_resume_does_not_prepare(tmp_path):
    result = _oracle_reject_result()
    attempt_record = S._sort_swo_reject_attempt_record(result)
    evaluate_calls = []

    @contextlib.contextmanager
    def rejected_prepare(cell, pin, *, cxx):
        raise S._SortSwoOracleRejected(
            "sort_best comparator が SWO oracle 不通過: "
            f"{result.finding.reason_code}",
            attempt_record,
        )
        yield  # pragma: no cover

    output_root = str(tmp_path / "out")
    document = _freeze()
    kwargs = dict(
        freeze_path=_write_freeze(tmp_path, document),
        budget_path=tmp_path / "time_ledger.json", output_root=output_root,
        verify_document=lambda doc: None,
        evaluate_fn=lambda *args, **kwargs: evaluate_calls.append(1),
        prepare_cell_fn=rejected_prepare, single_tenant_fn=lambda: None,
        monotonic=_Clock(), log=lambda msg: None,
    )
    assert S.run_role("develop", **kwargs) == S.EXIT_ORACLE_REJECT

    layout = S.layout_for(document, "develop", output_root=output_root)
    events = S.read_session_ledger(layout)
    starts = [event for event in events if event.get("event") == "session-start"]
    assert len(starts) == 1
    assert starts[0]["sort_swo_oracle"] == attempt_record
    assert starts[0]["sort_swo_oracle"]["classification"] == "reject"
    assert starts[0]["sort_swo_oracle"]["classification"] != "attempt-infra"
    assert starts[0]["sort_swo_oracle"]["materialized_hole_sha256"] == "a" * 64
    assert starts[0]["sort_swo_oracle"]["proposal_sha256"] == "b" * 64
    assert "freeze_cell_id" in starts[0]
    results = [event for event in events if event.get("event") == "session-result"]
    assert len(results) == 1
    assert results[0]["status"] == "oracle-reject"
    assert results[0]["reason"] == "snapshot-arena-write-denied"
    assert results[0]["status"] != "verifier-red"
    assert not any(event.get("event") == "retry" for event in events)
    assert evaluate_calls == []
    assert S.validate_session_ledger(
        layout, S.schedule_for_role(document, "develop"),
    ) == 1

    assert S.run_role("develop", **kwargs) == S.EXIT_ORACLE_REJECT
    resumed = S.read_session_ledger(layout)
    assert len([e for e in resumed if e.get("event") == "session-start"]) == 1
    assert len([e for e in resumed if e.get("event") == "session-result"]) == 1


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_s1_oracle_unavailable_is_recorded_as_attempt_infra_before_retry(tmp_path):
    from orchestrator.campaign import sort_swo_oracle as oracle

    prepare_calls = []

    @contextlib.contextmanager
    def unavailable_once(cell, pin, *, cxx):
        prepare_calls.append(1)
        if len(prepare_calls) == 1:
            result = oracle.SortSwoOracleResult(
                oracle.OracleStatus.UNAVAILABLE, "a" * 64, "b" * 64,
                infrastructure=oracle.OracleInfrastructureFailure(
                    oracle.INFRASTRUCTURE_REASON_CODE,
                    "trusted-preflight-compile", "trusted-positive-tu-compile-failed",
                ),
            )
            raise oracle.SortSwoOracleUnavailable(result)
        genome = Genome("silo", dict(cell["variant"]["flags"]))
        supply, meaning = _condition_records(genome)
        yield S.PreparedCell(
            genome, "stock", "/ccbench", "/cache",
            condition_supply_records=supply,
            condition_meaning_records=meaning,
        )

    output_root = str(tmp_path / "out")
    document = _freeze()
    rc = S.run_role(
        "develop", freeze_path=_write_freeze(tmp_path, document),
        budget_path=tmp_path / "time_ledger.json", output_root=output_root,
        verify_document=lambda doc: None, evaluate_fn=_green,
        prepare_cell_fn=unavailable_once, single_tenant_fn=lambda: None,
        monotonic=_Clock(), log=lambda msg: None,
    )
    assert rc == S.EXIT_OK
    events = S.read_session_ledger(S.layout_for(document, "develop", output_root=output_root))
    infra = [
        event["sort_swo_oracle"] for event in events
        if event.get("event") == "session-start"
        and "sort_swo_oracle" in event
    ]
    assert len(infra) == 1
    assert infra[0]["classification"] == "attempt-infra"
    assert infra[0]["reason_code"] == oracle.INFRASTRUCTURE_REASON_CODE


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_prepare_freeze_contract_error_aborts_without_retry(tmp_path):
    prepare_calls = []
    evaluate_calls = []

    @contextlib.contextmanager
    def invalid_prepare(cell, pin, *, cxx):
        prepare_calls.append(1)
        raise S.DriverError("freeze gate_predicate が構文契約違反")
        yield  # pragma: no cover

    with pytest.raises(S.DriverError, match="構文契約違反"):
        S.run_role(
            "develop", freeze_path=_write_freeze(tmp_path),
            budget_path=tmp_path / "time_ledger.json",
            output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
            evaluate_fn=lambda *a, **k: evaluate_calls.append(1),
            prepare_cell_fn=invalid_prepare, single_tenant_fn=lambda: None,
            monotonic=_Clock(), log=lambda msg: None)
    assert prepare_calls == [1]
    assert evaluate_calls == []
    layout = S.layout_for(_freeze(), "develop", output_root=str(tmp_path / "out"))
    assert not any(e.get("event") == "retry" for e in S.read_session_ledger(layout))


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_verifier_red_stops_without_retry(tmp_path):
    calls = []

    def red(genome, *args, **kwargs):
        calls.append(1)
        return _with_condition_records(EvalResult(
            genome=genome, variant=pipeline.variant_id(genome),
            certified=False, aborted=True, verdict="non-serializable",
        ))

    rc = _run(tmp_path, "floor", red)
    assert rc == S.EXIT_VERIFIER_RED
    assert len(calls) == 1
    document = _freeze()
    layout = S.layout_for(document, "floor", output_root=str(tmp_path / "out"))
    assert not any(e.get("event") == "retry" for e in S.read_session_ledger(layout))


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_trace_timeout_retries_but_verify_payload_does_not(tmp_path):
    timeout_calls = []

    def timeout_then_green(genome, layout, *args, **kwargs):
        timeout_calls.append(1)
        variant = pipeline.variant_id(genome)
        if len(timeout_calls) == 1:
            wal.log(layout, variant, "abort", S.ENV_TAG, {"reason": "trace-timeout"})
            return _with_condition_records(EvalResult(
                genome=genome, variant=variant, certified=False, aborted=True,
            ))
        return _green(genome)

    assert _run(tmp_path, "develop", timeout_then_green) == S.EXIT_OK
    assert len(timeout_calls) == 19

    red_root = tmp_path / "red"
    red_root.mkdir()
    red_calls = []

    def verifier_red(genome, layout, *args, **kwargs):
        red_calls.append(1)
        variant = pipeline.variant_id(genome)
        wal.log(layout, variant, "abort", S.ENV_TAG,
                {"reason": "trace-timeout", "verify": {"verdict": "red"}})
        return _with_condition_records(EvalResult(
            genome=genome, variant=variant, certified=False, aborted=True,
        ))

    assert _run(red_root, "develop", verifier_red) == S.EXIT_VERIFIER_RED
    assert red_calls == [1]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_driver_uses_workload_flags_from_freeze(tmp_path):
    document = _freeze()
    document["workload_flags"]["balanced"]["ycsb_rratio"] = "42"
    captured = []

    def evaluate(genome, layout, env, pin, perf, clocks, **kwargs):
        captured.append(dict(perf.workload))
        return _green(genome)

    rc = S.run_role(
        "develop", freeze_path=_write_freeze(tmp_path, document),
        budget_path=tmp_path / "time_ledger.json", output_root=str(tmp_path / "out"),
        verify_document=lambda doc: None, evaluate_fn=evaluate,
        prepare_cell_fn=_prepared, single_tenant_fn=lambda: None,
        monotonic=_Clock(), log=lambda msg: None)
    assert rc == S.EXIT_OK
    assert [flags["ycsb_rratio"] for flags in captured[:6]] == ["42"] * 6


def test_driver_refuses_freeze_without_workload_flags(tmp_path):
    document = _freeze()
    del document["workload_flags"]
    with pytest.raises(S.DriverError, match="workload_flags"):
        S.run_role(
            "develop", freeze_path=_write_freeze(tmp_path, document),
            budget_path=tmp_path / "time_ledger.json",
            output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
            evaluate_fn=_green, prepare_cell_fn=_prepared,
            single_tenant_fn=lambda: None, monotonic=_Clock(), log=lambda msg: None)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_verifier_red_in_one_campaign_blocks_other_campaign(tmp_path):
    calls = []

    def red(genome, *args, **kwargs):
        calls.append("red")
        return _with_condition_records(EvalResult(
            genome=genome, variant=pipeline.variant_id(genome),
            certified=False, aborted=True, verdict="non-serializable",
        ))

    freeze_path = _write_freeze(tmp_path)
    common = dict(
        freeze_path=freeze_path, budget_path=tmp_path / "time_ledger.json",
        output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
        prepare_cell_fn=_prepared, single_tenant_fn=lambda: None,
        monotonic=_Clock(), log=lambda msg: None)
    assert S.run_role("floor", evaluate_fn=red, **common) == S.EXIT_VERIFIER_RED
    assert S.run_role(
        "block1", evaluate_fn=lambda *a, **k: calls.append("unexpected"),
        **common) == S.EXIT_VERIFIER_RED
    assert calls == ["red"]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_develop_calls_legacy_plus_s2_without_bench_18_times(tmp_path):
    calls = []

    def evaluate(genome, *args, **kwargs):
        calls.append(kwargs)
        return _green(genome)

    rc = _run(tmp_path, "develop", evaluate)
    assert rc == S.EXIT_OK
    assert len(calls) == 18
    for kwargs in calls:
        assert kwargs["do_bench"] is False
        assert kwargs["screening"] is None
        assert kwargs["numactl"] == S.NUMACTL
        assert kwargs["bench_max_rounds"] == 1
        assert type(kwargs["build_context"]) is BuildRunContext
        assert callable(kwargs["capability_resolver"])
        assert [(tag, wl.flags) for tag, wl in kwargs["extra_correctness"]] == [
            (pipeline.S2_TAG, pipeline.s2_correctness_workload().flags)]


def test_s1_session_stage_is_in_shared_wal_contract(tmp_path):
    layout = CampaignLayout(str(tmp_path / "campaign")).ensure()
    # '-' 入り literal を CPython が自動 intern しないことに依存し、再 literal 化を検出する。
    assert S.SESSION_STAGE is STAGE_S1_SESSION
    wal.log(layout, "v1", S.SESSION_STAGE, S.ENV_TAG, {"event": "session-start"})
    states = wal.replay(layout)
    assert states["v1"].stages_seen == [S.SESSION_STAGE]
    assert not states["v1"].terminal
    assert wal.records_by_stage(layout, "v1")[S.SESSION_STAGE] == {
        "event": "session-start"}


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_completed_campaign_resume_does_not_evaluate_again(tmp_path):
    assert _run(tmp_path, "develop", _green) == S.EXIT_OK
    calls = []
    assert _run(tmp_path, "develop", lambda *a, **k: calls.append(1)) == S.EXIT_OK
    assert calls == []


def test_resume_repairs_tail_before_retry_and_session_result(tmp_path):
    document = _freeze()
    output_root = str(tmp_path / "out")
    layout = S.layout_for(document, "develop", output_root=output_root).ensure()
    cfg = S.config_for(document, "develop")
    wal.write_lock(layout, build_v2_lock(S.ident.canonical_preimage(cfg)))
    first = S.schedule_for_role(document, "develop")[0]
    S._append_event(layout, S._base_event(first, "interrupted", 0))
    with open(layout.wal_file, "ab") as stream:
        stream.write(b'{"torn":')
    messages = []

    rc = S.run_role(
        "develop", freeze_path=_write_freeze(tmp_path, document),
        budget_path=tmp_path / "time_ledger.json", output_root=output_root,
        verify_document=lambda doc: None, evaluate_fn=_green,
        prepare_cell_fn=_prepared, single_tenant_fn=lambda: None,
        monotonic=_Clock(), log=messages.append)
    records, truncated = wal.read_records_checked(layout)
    events = S.read_session_ledger(layout)
    assert rc == S.EXIT_OK and truncated is False
    assert len(records) > 4
    assert any('"status": "repaired"' in message for message in messages)
    assert any(event.get("event") == "retry" and event.get("attempt") == 1
               for event in events)
    assert any(event.get("event") == "session-result"
               and event.get("schedule_index") == 0
               and event.get("attempt") == 1 for event in events)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_run_role_partial_wal_write_eio_preserves_error_and_stops_followup(
        tmp_path, monkeypatch):
    document = _freeze()
    freeze_path = _write_freeze(tmp_path, document)
    output_root = str(tmp_path / "out")
    layout = S.layout_for(document, "develop", output_root=output_root)
    real_write = wal.os.write
    injection = {"active": False, "calls": 0}

    def partial_then_eio(fd, data):
        try:
            path = os.readlink("/proc/self/fd/%d" % fd)
        except OSError:
            path = ""
        if injection["active"] and path == layout.wal_file:
            injection["calls"] += 1
            if injection["calls"] == 1:
                return real_write(fd, data[:7])
            raise OSError(errno.EIO, "injected S-1 partial WAL write EIO")
        return real_write(fd, data)

    def fail_inside_evaluate(genome, candidate_layout, env_tag, *_args, **_kwargs):
        injection["active"] = True
        wal.log(candidate_layout, "evaluate-write", STAGE_BUILD_START, env_tag, {})
        raise AssertionError("WalAppendError の後へ到達してはならない")

    monkeypatch.setattr(wal.os, "write", partial_then_eio)
    with pytest.raises(wal.WalAppendError) as excinfo:
        S.run_role(
            "develop", freeze_path=freeze_path,
            budget_path=tmp_path / "time_ledger.json", output_root=output_root,
            verify_document=lambda _doc: None, evaluate_fn=fail_inside_evaluate,
            prepare_cell_fn=_prepared, single_tenant_fn=lambda: None,
            monotonic=_Clock(), log=lambda _message: None,
        )
    assert excinfo.value.phase == "write"
    assert excinfo.value.written_bytes == 7 < excinfo.value.total_bytes
    records, issues, truncated = wal.read_records_collected(layout)
    assert issues == [] and truncated is True and injection["calls"] == 2
    events = S.session_events_from_records(records)
    assert [event.get("event") for event in events] == [
        "campaign-start", "session-start",
    ]


def test_dry_run_refuses_unframed_tail_without_physical_change(tmp_path):
    document = _freeze()
    output_root = str(tmp_path / "out")
    layout = S.layout_for(document, "develop", output_root=output_root).ensure()
    S._append_event(
        layout, S._base_event(S.schedule_for_role(document, "develop")[0], "v", 0))
    with open(layout.wal_file, "ab") as stream:
        stream.write("途中".encode("utf-8")[:4])
    before = Path(layout.wal_file).read_bytes()

    with pytest.raises(S.ScheduleDeviation, match="newline 終端の無い tail"):
        S.run_role(
            "develop", dry_run=True, freeze_path=_write_freeze(tmp_path, document),
            budget_path=tmp_path / "time_ledger.json", output_root=output_root,
            verify_document=lambda doc: None, log=lambda message: None)
    assert Path(layout.wal_file).read_bytes() == before
    assert not list(Path(layout.runs_dir).glob("wal-tail-repair-*.json"))
    assert not Path(layout.lock_file).exists()


def test_pipeline_bench_rounds_default_three_and_opt_in_one(tmp_path, monkeypatch):
    """未指定は従来3、S-1 opt-inだけ1を remeasure_until_stable へ渡す。"""
    captured = []
    real_verify = pipeline.verify_trace_dir_with_capability

    @contextlib.contextmanager
    def unlocked():
        yield

    def fake_build(genome, commit, trace, **kwargs):
        bin_sha256 = ("da" if trace else "db") * 32  # 64 hex (WAL 新キー用)
        return types.SimpleNamespace(
            bin_hash=bin_sha256[:16], bin_sha256=bin_sha256,
            binary="/fake/ycsb", cached=True,
            configure_cmd="cfg", build_cmd="build")

    def fake_remeasure(measure_fn, settle_fn=None, max_rounds=3):
        captured.append(max_rounds)
        point = measure_fn()
        floor = types.SimpleNamespace(median=100.0, cv=0.01, high_variance=False)
        return types.SimpleNamespace(point=point, nf=floor, rounds=1,
                                     unstable=False, cv_history=[0.01])

    monkeypatch.setattr(pipeline, "buildcache", types.SimpleNamespace(build=fake_build))
    monkeypatch.setattr(pipeline.source_digest, "resolve", lambda *a, **k: "stock")
    monkeypatch.setattr(
        pipeline, "_run_trace", lambda *a, **k: pipeline._TraceRunResult(
            trace_c_lines=10,
            returncode=0,
            abort_counts=1,
            commit_count_witness=10,
            batch_commit_count_witness=0,
        ),
    )
    monkeypatch.setattr(
        pipeline, "verify_trace_dir_with_capability",
        lambda path, *, expected_commits=None, **receipt_binding: real_verify(
            str(TESTS / "fixtures/g1_serial"),
            **receipt_binding,
        ),
    )
    monkeypatch.setattr(pipeline, "bench_lock", unlocked)
    monkeypatch.setattr(pipeline, "competing_bench_pids", lambda: [])
    monkeypatch.setattr(pipeline, "settle", lambda: {"settled": True})
    monkeypatch.setattr(pipeline, "measure_point", lambda *a, **k: types.SimpleNamespace(
        throughputs=[100.0] * 5, run_cmd="run", notes=[],
        leading_indicators=lambda: {}))
    monkeypatch.setattr(pipeline, "remeasure_until_stable", fake_remeasure)
    genome = Genome("silo", {"BACK_OFF": 1})
    perf = PerfConfig(records=1000, threads=2)
    parser = argparse.ArgumentParser()
    add_coder_build_authority_argument(parser)
    context = build_run_context(
        generator_id=GeneratorId.BACKOFF_SWEEP,
        coder_authority=parser.parse_args(
            ["--allow-coder-derived-build"]
        ).coder_build_authority,
    )
    evidence = _evidence(stock=False, commit="deadbeef")
    authorization = env_contract.authorize("linux-baremetal")
    contract = authorization.contract
    monkeypatch.setattr(
        pipeline.source_digest, "resolve_evidence", lambda *a, **k: evidence,
    )

    for max_rounds in (None, 1):
        layout = CampaignLayout(str(tmp_path / f"c-{max_rounds}")).ensure()
        kwargs = {} if max_rounds is None else {"bench_max_rounds": max_rounds}
        result = pipeline.evaluate(
            genome, layout, contract.env_tag, "deadbeef", perf,
            contract.clocks_per_us, numactl=contract.numactl,
            log=lambda msg: None, build_context=context,
            authorization_contract=authorization,
            source_evidence=evidence, **kwargs)
        assert result.certified
    assert captured == [3, 1]
