"""Small, explicit Q/V histories for the gen-opt gate witness."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestrator.verifier.cli import main
from orchestrator.verifier.core import verify_trace_dir
from orchestrator.verifier.report import result_to_dict

K = "0000000000000001"
L = "0000000000000002"
S1 = (1 << 48) + 1
S2 = (1 << 48) + 2
COUNTS = ("gate_unreachable", "gate_d1a", "gate_d1b1", "gate_d1b2",
          "gate_d1c", "gate_d2a", "gate_d2b_i", "gate_d2b_ii")


def _source(root: Path, gate: bool = True) -> Path:
    silo = root / "cc/silo"
    silo.mkdir(parents=True)
    (root / "include").mkdir()
    (silo / "CMakeLists.txt").write_text(
        "ccbench_add_protocol(silo SOURCES transaction.cc WORKLOADS ycsb)\n")
    (silo / "transaction.cc").write_text(
        "#if TRACE\nizanagi_trace::emit_lock_violation(0,0,{},{});\n"
        "izanagi_trace::stream(0) << \"P \";\n"
        "izanagi_trace::emit_write_intent_violation(0,0,{},{});\n"
        + ("izanagi_trace::emit_stored(0);\nizanagi_trace::set_gate_txid(0);\n"
           if gate else "") + "#endif\n")
    (root / "include/ycsb.hh").write_text(
        "#if TRACE\n" + ("izanagi_trace::emit_steps(0);\n" if gate else "") + "#endif\n")
    (silo / "ycsb_silo.cc").write_text('#include "../../include/ycsb.hh"\n')
    return root


def _run(tmp_path: Path, trace: str, gate: str | None, *, require=False,
         gate1: str | None = None, source_gate=True):
    trace_dir = tmp_path / "history"
    trace_dir.mkdir()
    (trace_dir / "trace_0.log").write_text(trace)
    if gate is not None:
        (trace_dir / "gate_0.log").write_text(gate)
    if gate1 is not None:
        (trace_dir / "gate_1.log").write_text(gate1)
    source = _source(tmp_path / "source", source_gate)
    return verify_trace_dir(str(trace_dir), protocol="silo", ccbench_root=source,
                            require_gate_witness=require)


def _assert_only(res, expected: str | None = None, amount: int = 1,
                 verdict="indeterminate"):
    assert res.verdict == verdict
    for name in COUNTS:
        assert getattr(res.integrity, name) == (amount if name == expected else 0), name
    if expected:
        assert any(n.startswith("check=") and "thid=" in n and "txid=" in n
                   and "key=" in n and "expected=" in n and "observed=" in n
                   for n in res.integrity.notes)


def _write_trace(key=K):
    return f"C 0 0 1 1 0 1\nW 0 {key} U 1 1\nE 0\n"


def _write_gate(key=K, stamp=S1):
    return f"V 0 {key} {stamp}\nQ 0 0 1 W:{key}:-:{stamp}\n"


def test_gate_b2_unregistered_write_m1(tmp_path):
    res = _run(tmp_path, "C 0 0 1 1 0 0\nE 0\n", f"Q 0 0 1 W:{K}:-:{S1}\n")
    _assert_only(res, "gate_d1a")


def test_gate_b1_missing_initial_read_m2_m15(tmp_path):
    res = _run(tmp_path, "C 0 0 1 1 0 0\nE 0\n", f"Q 0 0 1 R:{K}:1:-\n")
    _assert_only(res, "gate_d1b1")


def test_gate_trace_read_without_q_key_m3(tmp_path):
    trace = f"C 0 0 1 1 1 0\nR 0 {K} 1 0\nE 0\n"
    _assert_only(_run(tmp_path, trace, "Q 0 0 0\n"), "gate_d1b2")


@pytest.mark.parametrize(
    "gate", ["", "Q - 0 0\n", "Q 1 0 0\n", "Q 0 0 0\nQ 1 0 0\n"],
    ids=["missing-q", "dash-txid", "wrong-txid", "extra-q"],
)
def test_gate_q_frame_m4(tmp_path, gate):
    _assert_only(_run(tmp_path, "C 0 0 1 1 0 0\nE 0\n", gate), "gate_d1c")


def test_gate_b4_wrong_version_payload_m5(tmp_path):
    trace = (_write_trace() + f"C 1 0 1 2 1 0\nR 1 {K} 1 1\nE 1\n")
    gate = _write_gate() + f"Q 1 0 1 R:{K}:{S2}:-\n"
    _assert_only(_run(tmp_path, trace, gate), "gate_d2a")


def test_gate_b5_later_reader_disagrees_with_stored_stamp(tmp_path):
    trace = (_write_trace(L) + f"C 1 0 1 2 1 0\nR 1 {L} 1 1\nE 1\n")
    gate = _write_gate(L) + f"Q 1 0 1 R:{L}:{S2}:-\n"
    res = _run(tmp_path, trace, gate)
    _assert_only(res, "gate_d2a")
    assert res.integrity.gate_external_reads_checked == 1


def test_gate_second_external_read_wrong_stamp(tmp_path):
    trace = f"C 0 0 1 1 1 0\nR 0 {K} 1 0\nE 0\n"
    gate = f"Q 0 0 2 R:{K}:1:- R:{K}:2:-\n"
    res = _run(tmp_path, trace, gate)
    _assert_only(res, "gate_d2a")
    assert res.integrity.gate_external_reads_checked == 2


def test_gate_genesis_wrong_payload_m6(tmp_path):
    trace = f"C 0 0 1 1 1 0\nR 0 {K} 1 0\nE 0\n"
    _assert_only(_run(tmp_path, trace, f"Q 0 0 1 R:{K}:2:-\n"), "gate_d2a")


def test_gate_b6_stale_own_read_m7(tmp_path):
    gate = f"V 0 {K} {S1}\nQ 0 0 2 W:{K}:-:{S1} R:{K}:1:-\n"
    _assert_only(_run(tmp_path, _write_trace(), gate), "gate_d2b_i")


def test_gate_last_write_wins_m8(tmp_path):
    gate = f"V 0 {K} {S1}\nQ 0 0 2 W:{K}:-:{S1} W:{K}:-:{S2}\n"
    res = _run(tmp_path, _write_trace(), gate)
    _assert_only(res, "gate_d2b_ii")
    assert res.integrity.gate_repeated_write_key_transactions == 1


def test_gate_v_missing_m9(tmp_path):
    _assert_only(_run(tmp_path, _write_trace(), f"Q 0 0 1 W:{K}:-:{S1}\n"),
                 "gate_unreachable")


def test_gate_missing_thread_m10(tmp_path):
    trace = "C 0 0 1 1 0 0\nE 0\n"
    res = _run(tmp_path, trace, "Q 0 0 0\n")
    trace_dir = Path(res.trace_dir)
    (trace_dir / "trace_1.log").write_text("C 1 1 1 2 0 0\nE 1\n")
    res = verify_trace_dir(str(trace_dir), protocol="silo", ccbench_root=tmp_path / "source")
    _assert_only(res, "gate_unreachable")


def test_gate_required_absent_m11_cli_rc(tmp_path, capsys):
    res = _run(tmp_path, "C 0 0 1 1 0 0\nE 0\n", None, require=True)
    _assert_only(res, "gate_unreachable")
    assert not res.certified
    assert main([res.trace_dir, "--protocol", "silo", "--ccbench-root",
                 str(tmp_path / "source"), "--require-gate-witness", "--json"]) == 3
    assert json.loads(capsys.readouterr().out)["results"][0]["certified"] is False


def test_gate_required_partial_thread_cli_rc(tmp_path, capsys):
    res = _run(tmp_path, "C 0 0 1 1 0 0\nE 0\n", "Q 0 0 0\n", require=True)
    (Path(res.trace_dir) / "trace_1.log").write_text("C 1 1 1 2 0 0\nE 1\n")
    assert main([res.trace_dir, "--protocol", "silo", "--ccbench-root",
                 str(tmp_path / "source"), "--require-gate-witness", "--json"]) == 3
    payload = json.loads(capsys.readouterr().out)["results"][0]
    assert payload["certified"] is False
    assert payload["gate_witness"]["counts"]["unreachable"] == 1


def test_gate_required_unreadable_cli_rc(tmp_path, capsys):
    res = _run(tmp_path, "C 0 0 1 1 0 0\nE 0\n", "Q 0 0 0\n", require=True)
    (Path(res.trace_dir) / "gate_0.log").write_bytes(b"\xff\n")
    assert main([res.trace_dir, "--protocol", "silo", "--ccbench-root",
                 str(tmp_path / "source"), "--require-gate-witness", "--json"]) == 3
    payload = json.loads(capsys.readouterr().out)["results"][0]
    assert payload["certified"] is False
    assert payload["gate_witness"]["counts"]["unreachable"] == 1


def test_gate_real_u1_emitter_names_d5_pass(tmp_path):
    res = _run(tmp_path, _write_trace(), _write_gate(), require=True)
    assert res.integrity.gate_d5 == "pass"
    assert res.integrity.gate_unreachable == 0
    assert res.certified


def test_gate_wrong_include_target_d5_fails(tmp_path):
    res = _run(tmp_path, _write_trace(), _write_gate(), require=True)
    (tmp_path / "source/cc/silo/ycsb_silo.cc").write_text('#include "ycsb.hh"\n')
    res = verify_trace_dir(res.trace_dir, protocol="silo",
                           ccbench_root=tmp_path / "source",
                           require_gate_witness=True)
    assert res.integrity.gate_d5 == "fail"
    assert not res.certified


def test_gate_q_thread_mismatch_is_d1c(tmp_path):
    res = _run(tmp_path, "C 0 0 1 1 0 0\nE 0\n", "Q 0 1 0\n")
    _assert_only(res, "gate_d1c")


def test_gate_b7_emitter_missing_m12(tmp_path):
    res = _run(tmp_path, _write_trace(), _write_gate(), require=True, source_gate=False)
    _assert_only(res, verdict="indeterminate")
    assert res.integrity.gate_d5 == "fail"


def test_gate_invalid_filename_m13(tmp_path):
    res = _run(tmp_path, "C 0 0 1 1 0 0\nE 0\n", "Q 0 0 0\n")
    (Path(res.trace_dir) / "gate_x.log").write_text("")
    _assert_only(verify_trace_dir(res.trace_dir, protocol="silo",
                                  ccbench_root=tmp_path / "source"), "gate_unreachable")


def test_gate_legacy_parse_m14(tmp_path):
    trace = "C 0 0 9223372036854775808 1 0 0\nE 0\n"
    _assert_only(_run(tmp_path, trace, "Q 0 0 0\n"), "gate_unreachable")


def test_gate_n1_fixed_stock(tmp_path):
    trace = _write_trace() + f"C 1 0 1 2 1 0\nR 1 {K} 1 1\nE 1\n"
    gate = _write_gate() + f"Q 1 0 1 R:{K}:{S1}:-\n"
    res = _run(tmp_path, trace, gate, require=True)
    _assert_only(res, verdict="serializable")
    assert res.integrity.gate_external_reads_checked == 1
    assert result_to_dict(res)["gate_witness"]["meaning_version"] == 2


def test_gate_n3_blind_write(tmp_path):
    _assert_only(_run(tmp_path, _write_trace(), _write_gate()), verdict="serializable")


def test_gate_n4_read_only_many(tmp_path):
    trace = "".join(f"C {i} 0 1 {i+1} 1 0\nR {i} {K} 1 0\nE {i}\n"
                    for i in range(12))
    gate = "".join(f"Q {i} 0 1 R:{K}:1:-\n" for i in range(12))
    res = _run(tmp_path, trace, gate)
    _assert_only(res, verdict="serializable")
    assert res.integrity.gate_external_reads_checked == 12


@pytest.mark.parametrize(
    "corruption", ["Q 0 0 1 R:BAD:1:-\n", "Q 0 0 1 R:0000000000000001:18446744073709551616:-\n",
                   "Q 0 0 1 R:0000000000000001:-:-\n", "X 0\n"],
    ids=["bad-key", "stamp-overflow", "r-missing-observed", "unknown-tag"],
)
def test_gate_format_fail_closed(tmp_path, corruption):
    _assert_only(_run(tmp_path, "C 0 0 1 1 0 0\nE 0\n", corruption), "gate_unreachable")


def test_gate_unreadable_fail_closed(tmp_path):
    res = _run(tmp_path, "C 0 0 1 1 0 0\nE 0\n", "Q 0 0 0\n", require=True)
    (Path(res.trace_dir) / "gate_0.log").write_bytes(b"\xff\n")
    _assert_only(verify_trace_dir(res.trace_dir, protocol="silo",
                                  ccbench_root=tmp_path / "source",
                                  require_gate_witness=True), "gate_unreachable")


def test_gate_absent_legacy_projection_unchanged():
    path = Path(__file__).parent / "fixtures/g1_serial"
    result = verify_trace_dir(str(path))
    assert not result.integrity.gate_witness_enabled
    assert "gate_witness" not in result_to_dict(result)
