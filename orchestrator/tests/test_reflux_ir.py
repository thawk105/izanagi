# -*- coding: utf-8 -*-
"""Canonical trigger-gate IR and emitter tests (pytest and plain runner)."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from types import ModuleType

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
_ROOT = _ORCH.parent
_GOLDEN_PATH = _HERE / "reflux_ir_expected_goldens.py"
_PRODUCTION_PATH = _ORCH / "campaign" / "reflux_ir.py"
_SKELETON_PATCH_PATH = _ROOT / "patches" / "silo-backoff-trigger-gating-variant.patch"
_FREEZE_PATH = _ROOT / "output" / "s1-freeze" / "known_axes_freeze.json"
_PROVENANCE_PATH = (
    _ROOT
    / "output"
    / "campaigns"
    / "p3-s8a-trigger-sweep-balanced-sweep-c2d838b8"
    / "reports"
    / "s8a_trigger_sweep_provenance.json"
)

_GOLDEN_ROWS_FIRST_LINE = 25
_GOLDEN_ROWS_LAST_LINE = 56
_GOLDEN_ROWS_PREIMAGE_LENGTH = 7942
_EMITTER_PREIMAGE_BEGIN = b"# CHECKOUT_IR_EMITTER_PREIMAGE_BEGIN\n"
_EMITTER_PREIMAGE_END = b"# CHECKOUT_IR_EMITTER_PREIMAGE_END\n"
_EMITTER_PREIMAGE_LENGTH = 3104
_EXPECTED_EMITTER_SOURCE_SHA256 = (
    "e11cc8d996f306698f1c1096a6026574e5dbfee8d2c5613884dd426d18eec4ca"
)
_EXPECTED_GOLDEN_32_ROWS_SHA256 = (
    "69d8274fa03829d89dd706f7a0bb16d52ea71b608c51f5db5f5cdb1ead497165"
)
_EXPECTED_CHECKOUT_IR_EMITTER_GOLDEN_REGRESSION_ID = (
    "c8289c4faf1b5420d24cb8ef94e4d1e918bb4003afe4512bfc3a600baa095d75"
)


_GOLDEN_ALLOWED_NODE_TYPES = (
    ast.Module,
    ast.Expr,
    ast.Constant,
    ast.ImportFrom,
    ast.alias,
    ast.Assign,
    ast.Name,
    ast.Tuple,
    ast.Load,
    ast.Store,
)


def _assert_golden_literal(node: ast.expr) -> None:
    if type(node) is ast.Tuple:
        assert type(node.ctx) is ast.Load
        for element in node.elts:
            _assert_golden_literal(element)
        return
    assert type(node) is ast.Constant
    assert type(node.value) in (str, int)


def _validated_golden_assignments() -> dict[str, ast.expr]:
    """Parse the golden without executing it, enforcing a closed AST language."""
    tree = ast.parse(_GOLDEN_PATH.read_text(encoding="utf-8"))
    unexpected = {
        type(node).__name__
        for node in ast.walk(tree)
        if type(node) not in _GOLDEN_ALLOWED_NODE_TYPES
    }
    assert unexpected == set(), f"golden contains forbidden AST nodes: {unexpected}"
    assert tree.type_ignores == []
    assert len(tree.body) == 4

    docstring, future_import, *assignment_statements = tree.body
    assert (
        type(docstring) is ast.Expr
        and type(docstring.value) is ast.Constant
        and type(docstring.value.value) is str
    )
    assert (
        type(future_import) is ast.ImportFrom
        and future_import.module == "__future__"
        and future_import.level == 0
        and len(future_import.names) == 1
        and future_import.names[0].name == "annotations"
        and future_import.names[0].asname is None
    )

    assignments = {}
    for statement in assignment_statements:
        assert type(statement) is ast.Assign
        assert len(statement.targets) == 1
        target = statement.targets[0]
        assert type(target) is ast.Name and type(target.ctx) is ast.Store
        assert target.id in ("EXPECTED_REASON_ORDER", "EXPECTED_CASES")
        assert target.id not in assignments
        assert statement.type_comment is None
        _assert_golden_literal(statement.value)
        assignments[target.id] = statement.value
    assert tuple(assignments) == ("EXPECTED_REASON_ORDER", "EXPECTED_CASES")
    return assignments


# Validate before obtaining values.  The golden module is deliberately never
# imported, so import-time mutation cannot run before the purity gate.
_GOLDEN_ASSIGNMENTS = _validated_golden_assignments()
EXPECTED_REASON_ORDER = ast.literal_eval(_GOLDEN_ASSIGNMENTS["EXPECTED_REASON_ORDER"])
EXPECTED_CASES = ast.literal_eval(_GOLDEN_ASSIGNMENTS["EXPECTED_CASES"])

sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ORCH))

from campaign import axis_trigger_gating as AXIS  # noqa: E402
from campaign import reflux_ir as IR  # noqa: E402
from orchestrator.campaign import s8a_trigger_sweep as LEGACY  # noqa: E402
from orchestrator.campaign import reflux_ir as ORCH_IR  # noqa: E402
from skiputil import Skip  # noqa: E402

_HISTORICAL_MASKS = {
    "g_none": 0,
    "g_lc": 1,
    "g_rt": 4,
    "g_rl": 8,
    "g_lc+rt": 5,
    "g_lc+rl": 9,
    "g_rt+rl": 12,
    "g_lc+rt+rl": 13,
    "ident_all": 31,
}


def _golden_rhs() -> ast.expr:
    return _validated_golden_assignments()["EXPECTED_CASES"]


def _golden_rows() -> tuple[tuple[int, str, str], ...]:
    value = ast.literal_eval(_golden_rhs())
    assert value == EXPECTED_CASES
    assert type(value) is tuple and len(value) == 32
    assert all(type(row) is tuple and len(row) == 3 for row in value)
    return value


def _golden_rows_source_bytes() -> bytes:
    """source bytes を保存した規範 32-row preimage を返す。"""
    lines = _GOLDEN_PATH.read_bytes().splitlines(keepends=True)
    row_lines = lines[_GOLDEN_ROWS_FIRST_LINE - 1:_GOLDEN_ROWS_LAST_LINE]
    assert len(row_lines) == 32
    # 25--56 行は 4-space indent、末尾 comma、各 1 個の LF を含む。
    # したがって CRLF と最終 LF の欠落は拒否する。
    assert all(line[:5] == b"    (" and line.endswith(b"),\n")
               for line in row_lines)
    assert all(b"\r" not in line and line.count(b"\n") == 1
               for line in row_lines)
    preimage = b"".join(row_lines)
    assert len(preimage) == _GOLDEN_ROWS_PREIMAGE_LENGTH
    return preimage


def _emitter_source_bytes() -> bytes:
    """回帰 ID 自身を除いた checkout emitter の閉じた source preimage。"""
    lines = _PRODUCTION_PATH.read_bytes().splitlines(keepends=True)
    assert lines.count(_EMITTER_PREIMAGE_BEGIN) == 1
    assert lines.count(_EMITTER_PREIMAGE_END) == 1
    begin = lines.index(_EMITTER_PREIMAGE_BEGIN)
    end = lines.index(_EMITTER_PREIMAGE_END)
    assert begin < end
    preimage = b"".join(lines[begin + 1:end])
    assert len(preimage) == _EMITTER_PREIMAGE_LENGTH
    assert preimage.endswith(b"\n") and b"\r" not in preimage
    return preimage


def _checkout_regression_id(emitter_digest: bytes, golden_digest: bytes) -> str:
    assert len(emitter_digest) == 32 and len(golden_digest) == 32
    return hashlib.sha256(
        b"izanagi-checkout-ir-emitter-golden-regression/v1\0"
        + b"emitter-source-sha256\0"
        + emitter_digest
        + b"golden-32-rows-sha256\0"
        + golden_digest
    ).hexdigest()


def _expected_by_mask() -> dict[int, tuple[str, str]]:
    return {mask: (wire, predicate) for mask, wire, predicate in _golden_rows()}


def _capture_rejection(function, value, module=IR) -> tuple[bytes, ...]:
    try:
        function(value)
    except Exception as exc:  # noqa: BLE001 - exact public rejection is asserted
        assert type(exc) is module.RefluxIRError
        assert exc.__cause__ is None
        assert exc.__context__ is None
        fingerprint = (
            type(exc).__qualname__.encode("utf-8"),
            str(exc).encode("utf-8"),
            repr(exc).encode("utf-8"),
            repr(exc.args).encode("utf-8"),
            repr(vars(exc)).encode("utf-8"),
        )
        assert fingerprint == (
            b"RefluxIRError",
            b"invalid reflux IR",
            b"RefluxIRError('invalid reflux IR')",
            b"('invalid reflux IR',)",
            b"{}",
        )
        return fingerprint
    raise AssertionError(f"rejection expected from {function.__name__}")


def _forge(module, mask):
    forged = object.__new__(module.TriggerGateIR)
    object.__setattr__(forged, "mask", mask)
    return forged


def test_public_api_and_frozen_dataclass_contract():
    assert IR.__all__ == [
        "SCHEMA_ID",
        "TriggerGateIR",
        "parse_wire",
        "encode_wire",
        "emit_predicate",
        "RefluxIRError",
    ]
    assert type(IR.SCHEMA_ID) is str
    assert IR.SCHEMA_ID == "izanagi-trigger-gate-ir/v1"
    value = IR.TriggerGateIR(mask=0)
    try:
        value.mask = 1
    except Exception as exc:  # frozen dataclass rejects assignment
        assert type(exc).__name__ == "FrozenInstanceError"
    else:
        raise AssertionError("TriggerGateIR must be frozen")


def test_mask_acceptance_is_exact_int_in_closed_range():
    class IntSubclass(int):
        pass

    assert [IR.TriggerGateIR(mask=mask).mask for mask in range(32)] == list(range(32))
    rejected = [-1, 32, True, False, 1.0, "1", IntSubclass(1), None]
    messages = {_capture_rejection(lambda mask: IR.TriggerGateIR(mask), value)
                for value in rejected}
    assert len(messages) == 1


def test_golden_expected_cases_rhs_is_32_tuple_literals_only():
    assignments = _validated_golden_assignments()
    assert ast.literal_eval(assignments["EXPECTED_REASON_ORDER"]) == EXPECTED_REASON_ORDER
    assert EXPECTED_REASON_ORDER == AXIS.GATEABLE_REASONS
    rhs = _golden_rhs()
    assert isinstance(rhs, ast.Tuple) and len(rhs.elts) == 32
    assert all(isinstance(row, ast.Tuple) for row in rhs.elts)
    assert all(isinstance(node, (ast.Tuple, ast.Constant, ast.Load))
               for node in ast.walk(rhs))
    assert len(_golden_rows()) == 32


def test_golden_has_no_production_import_and_production_has_no_golden_consumer():
    source = _GOLDEN_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not any(
        name == "campaign"
        or name.startswith("campaign.")
        or name == "orchestrator.campaign"
        or name.startswith("orchestrator.campaign.")
        for name in imported
    )
    assert not any(isinstance(node, ast.Call) for node in ast.walk(tree))

    consumers = []
    for path in _ORCH.rglob("*.py"):
        if "tests" in path.relative_to(_ORCH).parts:
            continue
        if "reflux_ir_expected_goldens" in path.read_text(encoding="utf-8"):
            consumers.append(path.relative_to(_ROOT).as_posix())
    assert consumers == []


def test_checkout_ir_emitter_source_regression_digest():
    emitter_digest = hashlib.sha256(_emitter_source_bytes()).digest()
    assert emitter_digest.hex() == _EXPECTED_EMITTER_SOURCE_SHA256

    assert IR._CHECKOUT_IR_EMITTER_SOURCE_SHA256 == _EXPECTED_EMITTER_SOURCE_SHA256


def test_checkout_ir_golden_32_rows_regression_digest():
    golden_digest = hashlib.sha256(_golden_rows_source_bytes()).digest()
    assert golden_digest.hex() == _EXPECTED_GOLDEN_32_ROWS_SHA256

    assert IR._CHECKOUT_IR_GOLDEN_32_ROWS_SHA256 == _EXPECTED_GOLDEN_32_ROWS_SHA256


def test_m15_checkout_regression_id_binds_golden_with_fixed_emitter_digest():
    emitter_digest = bytes.fromhex(_EXPECTED_EMITTER_SOURCE_SHA256)
    golden_digest = bytes.fromhex(IR._CHECKOUT_IR_GOLDEN_32_ROWS_SHA256)
    observed_id = _checkout_regression_id(emitter_digest, golden_digest)
    assert observed_id == _EXPECTED_CHECKOUT_IR_EMITTER_GOLDEN_REGRESSION_ID
    assert (
        IR.CHECKOUT_IR_EMITTER_GOLDEN_REGRESSION_ID
        == _EXPECTED_CHECKOUT_IR_EMITTER_GOLDEN_REGRESSION_ID
    )


def test_golden_masks_wires_and_predicates_are_bijective():
    rows = _golden_rows()
    masks = [mask for mask, _wire, _predicate in rows]
    wires = [wire for _mask, wire, _predicate in rows]
    predicates = [predicate for _mask, _wire, predicate in rows]
    assert set(masks) == set(range(32)) and len(set(masks)) == 32
    assert len(set(wires)) == 32
    assert len(set(predicates)) == 32


def test_all_32_predicates_match_independent_golden_byte_for_byte():
    expected = _expected_by_mask()
    for mask in range(32):
        actual = IR.emit_predicate(IR.TriggerGateIR(mask))
        assert actual.encode("ascii") == expected[mask][1].encode("ascii")


def test_all_32_predicates_are_complete_assignments_and_never_skeleton_true():
    emitted = [IR.emit_predicate(IR.TriggerGateIR(mask)) for mask in range(32)]
    assert [len(value.encode("utf-8")) for value in emitted] == [
        len(_expected_by_mask()[mask][1].encode("utf-8")) for mask in range(32)
    ]
    assert min(map(len, emitted)) == 72
    assert max(map(len, emitted)) == 379
    assert all(value.startswith("izanagi_gate_pass = ") for value in emitted)
    assert all(value.endswith(";") for value in emitted)
    assert "true" not in emitted
    assert "izanagi_gate_pass = true;" not in emitted


def test_all_32_predicates_match_legacy_differential_oracle_byte_for_byte():
    for mask in range(32):
        reasons = [reason for bit, reason in enumerate(AXIS.GATEABLE_REASONS)
                   if mask & (1 << bit)]
        actual = IR.emit_predicate(IR.TriggerGateIR(mask))
        assert actual.encode("ascii") == LEGACY.predicate_for(reasons).encode("ascii")


def test_wire_codec_is_bijective_round_trips_and_matches_all_goldens():
    expected = _expected_by_mask()
    observed_wires = set()
    for mask in range(32):
        ir = IR.TriggerGateIR(mask)
        wire = IR.encode_wire(ir)
        assert wire.encode("ascii") == expected[mask][0].encode("ascii")
        assert len(wire) == 5 and set(wire) <= {"0", "1"}
        assert IR.parse_wire(wire) == ir
        assert IR.encode_wire(IR.parse_wire(wire)) == wire
        observed_wires.add(wire)
    assert len(observed_wires) == 32


def test_parse_wire_rejects_all_noncanonical_forms_uniformly():
    class StrSubclass(str):
        pass

    rejected = [
        "",
        "0000",
        "000000",
        " 0000",
        "0000 ",
        "00 00",
        "0000\n",
        " 00000",
        "00000 ",
        "\t00000",
        "00000\n",
        " 10010 ",
        '"00000"',
        "'10010'",
        "\u300000000\u3000",
        "0 0 0 0 0",
        "+0000",
        "-0000",
        "0b000",
        "0x000",
        *(f"0000{digit}" for digit in "23456789"),
        "abcde",
        "0000a",
        "０００００",
        "１１１１１",
        StrSubclass("00000"),
        b"00000",
        0,
        True,
        [0, 0, 0, 0, 0],
        {"wire": "00000"},
    ]
    messages = {_capture_rejection(IR.parse_wire, value) for value in rejected}
    assert len(messages) == 1


def test_every_public_rejection_uses_one_type_and_one_disclosure_free_message():
    class IntSubclass(int):
        pass

    fingerprints = set()
    for module in (IR, ORCH_IR):
        cases = [
            (module.parse_wire, "bad"),
            (lambda value, module=module: module.TriggerGateIR(value), -1),
            (lambda value, module=module: module.TriggerGateIR(value), 32),
            (lambda value, module=module: module.TriggerGateIR(value), True),
            (lambda value, module=module: module.TriggerGateIR(value), IntSubclass(1)),
            (module.encode_wire, object()),
            (module.emit_predicate, object()),
            (module.encode_wire, _forge(module, -1)),
            (module.emit_predicate, _forge(module, 32)),
        ]
        fingerprints.update(
            _capture_rejection(function, value, module) for function, value in cases
        )
    assert len(fingerprints) == 1


def test_forged_exact_ir_is_revalidated_by_both_sinks():
    class IntSubclass(int):
        pass

    for mask in (-1, 32, True, IntSubclass(1)):
        forged = _forge(IR, mask)
        assert type(forged) is IR.TriggerGateIR
        assert len({_capture_rejection(IR.encode_wire, forged),
                    _capture_rejection(IR.emit_predicate, forged)}) == 1


def test_trigger_gate_ir_subclass_mask_exception_is_uniformly_rejected():
    for module in (IR, ORCH_IR):
        class ExplodingMask(module.TriggerGateIR):
            @property
            def mask(self):
                raise RuntimeError("private subclass detail")

        value = object.__new__(ExplodingMask)
        assert len({
            _capture_rejection(module.encode_wire, value, module),
            _capture_rejection(module.emit_predicate, value, module),
        }) == 1


def test_dual_import_ir_values_are_accepted_by_each_others_sinks():
    assert IR.TriggerGateIR is not ORCH_IR.TriggerGateIR
    for mask in (0, 1, 17, 31):
        campaign_value = IR.TriggerGateIR(mask)
        orchestrator_value = ORCH_IR.TriggerGateIR(mask)
        assert IR.encode_wire(orchestrator_value) == ORCH_IR.encode_wire(campaign_value)
        assert IR.emit_predicate(orchestrator_value) == ORCH_IR.emit_predicate(
            campaign_value
        )


def test_axis_reason_order_drift_guard_fails_module_import():
    package_name = "_reflux_ir_drift_probe"
    module_name = f"{package_name}.reflux_ir"
    axis_name = f"{package_name}.axis_trigger_gating"
    package = ModuleType(package_name)
    package.__path__ = []
    axis = ModuleType(axis_name)
    axis.GATEABLE_REASONS = tuple(reversed(AXIS.GATEABLE_REASONS))
    spec = importlib.util.spec_from_file_location(module_name, _PRODUCTION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    saved = {name: sys.modules.get(name) for name in (package_name, axis_name, module_name)}
    sys.modules[package_name] = package
    sys.modules[axis_name] = axis
    sys.modules[module_name] = module
    try:
        try:
            spec.loader.exec_module(module)
        except RuntimeError as exc:
            assert str(exc) == "trigger-gating reason order drifted"
        else:
            raise AssertionError("drifted GATEABLE_REASONS must fail import")
    finally:
        for name, previous in saved.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous


def test_emitter_cpp_tokens_exist_in_authoritative_skeleton_patch():
    expected_private_tokens = {
        "_ASSIGNMENT_TARGET": "izanagi_gate_pass",
        "_REASON_VARIABLE": "izanagi_abort_reason_",
        "_ENUM_TYPE": "IzanagiAbortReason",
        "_SENTINEL_MEMBER": "kUnset",
        "_ENUM_MEMBERS": (
            "kLockConflict",
            "kUpdateAbsent",
            "kReadValiTid",
            "kReadValiLocked",
            "kNodeVali",
        ),
    }
    for name, expected in expected_private_tokens.items():
        assert getattr(IR, name) == expected

    patch = _SKELETON_PATCH_PATH.read_text(encoding="utf-8")
    added_source = "\n".join(
        line[1:] for line in patch.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    assert "enum class IzanagiAbortReason : unsigned char {" in added_source
    assert "static thread_local IzanagiAbortReason izanagi_abort_reason_ =" in added_source
    assert "bool izanagi_gate_pass = true;" in added_source
    assert re.search(r"^\s*izanagi_gate_pass\s*=", added_source, re.MULTILINE)
    enum_members = (IR._SENTINEL_MEMBER, *IR._ENUM_MEMBERS)
    assert len(enum_members) == 6
    for member in enum_members:
        assert re.search(rf"^\s*{re.escape(member)}(?:\s*=|\s*,)",
                         added_source, re.MULTILINE)


def test_frozen_gate_predicates_match_six_records_with_three_distinct_masks():
    """Freeze has 6 records but only 3 distinct masks; records are not 6 anchors."""
    document = json.loads(_FREEZE_PATH.read_text(encoding="utf-8"))
    records = [
        record
        for workload in document["entries"].values()
        for record in workload.values()
        if "gate_predicate" in record
    ]
    assert len(records) == 6
    masks = {"g_rt": 4, "g_rl": 8, "ident_all": 31}
    observed_masks = {masks[record["name"]] for record in records}
    assert observed_masks == {4, 8, 31} and len(observed_masks) == 3
    for record in records:
        expected = IR.emit_predicate(IR.TriggerGateIR(masks[record["name"]]))
        assert record["gate_predicate"].encode("ascii") == expected.encode("ascii")


def test_campaign_provenance_matches_nine_masks_as_historical_artifact_only():
    """The 9 masks are historical-artifact agreement, not an independent oracle."""
    document = json.loads(_PROVENANCE_PATH.read_text(encoding="utf-8"))
    assert tuple(document["effective_reasons"]) == (
        "lock-conflict",
        "readvali-tid",
        "readvali-locked",
    )
    entries = document["entries"]
    assert set(_HISTORICAL_MASKS) == set(entries) - {"stock"}
    assert len(_HISTORICAL_MASKS) == 9
    for name, mask in _HISTORICAL_MASKS.items():
        expected = IR.emit_predicate(IR.TriggerGateIR(mask))
        assert entries[name]["implementation"].encode("ascii") == expected.encode("ascii")


def _run() -> int:
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    passed = failed = skipped = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except Skip as exc:
            print(f"SKIP {test.__name__}: {exc}")
            skipped += 1
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001 - plain runner reports ERROR separately
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
