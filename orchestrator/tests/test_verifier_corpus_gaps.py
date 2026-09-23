# -*- coding: utf-8 -*-
"""手導出の小履歴 F03 / F06 / B06。pytest と素の Python の両方で走る。"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))
sys.path.insert(0, _HERE)

from skiputil import Skip  # noqa: E402
from orchestrator.verifier import verify_trace_dir  # noqa: E402
from orchestrator.verifier.core import _parse_trace_dir_compact  # noqa: E402
from orchestrator.verifier.dsg import DSG  # noqa: E402
from orchestrator.verifier.parse import _CompactTrace  # noqa: E402


def _write_traces(root, *files):
    trace_dir = Path(root) / "traces"
    trace_dir.mkdir()
    for index, contents in enumerate(files):
        (trace_dir / f"trace_{index}.log").write_text(contents, encoding="utf-8")
    return str(trace_dir)


def _verify(root, trace_dir):
    ccbench_root = Path(root) / "ccbench"
    silo = ccbench_root / "cc" / "silo"
    silo.mkdir(parents=True)
    (silo / "CMakeLists.txt").write_text(
        "ccbench_add_protocol(silo SOURCES transaction.cc WORKLOADS ycsb)\n",
        encoding="utf-8",
    )
    (silo / "transaction.cc").write_text(
        "#if TRACE\n"
        "izanagi_trace::emit_lock_violation(0, 0, {}, {});\n"
        'izanagi_trace::stream(0) << "P ";\n'
        "#endif\n",
        encoding="utf-8",
    )
    return verify_trace_dir(trace_dir, protocol="silo", ccbench_root=ccbench_root)


def _adjacency(trace_dir):
    # VerifyResult は辺集合を返さないため、本番と同じ compact 構築を読む。
    parsed = _parse_trace_dir_compact(trace_dir)
    assert isinstance(parsed, _CompactTrace), type(parsed)
    return DSG.from_compact(parsed).adj


def _edge_set(adj):
    return {(src, dst) for src, destinations in adj.items() for dst in destinations}


def _reasons(anomaly, src, dst):
    return [reason for edge in anomaly.edges
            if (edge.src, edge.dst) == (src, dst) for reason in edge.reasons]


def test_f03_same_version_double_read():
    """F03: 手で導いた辺は wr 0→1 の 1 本 (x = aa)。
    §3.1 の「二重読みで辺を重複して数える」を検出する。
    """
    root = tempfile.mkdtemp(prefix="izanagi-corpus-f03-")
    try:
        trace_dir = _write_traces(root,
            "C 0 0 1 1 0 1\nW 0 aa U 1 1\nE 0\n"
            "C 1 0 1 2 2 0\nR 1 aa 1 1\nR 1 aa 1 1\nE 1\n")
        adj = _adjacency(trace_dir)
        assert _edge_set(adj) == {(0, 1)}, adj
        assert sum(len(v) for v in adj.values()) == 1, adj
        result = _verify(root, trace_dir)
        assert result.verdict == "serializable", result
        assert result.certified is True, result
        assert result.n_edges == 1, result.n_edges
        assert result.n_reads == 2, result.n_reads
        assert result.anomalies == [], result.anomalies
        assert result.total_cycles == 0, result.total_cycles
    finally:
        shutil.rmtree(root)


def test_f06_different_version_double_read():
    """F06: 手で導いた辺は ww 0→1、wr 0→2・1→2、rw 2→1 (x = aa)。
    §3.1 の「二重読みの後の方だけを残す」を検出する。
    """
    root = tempfile.mkdtemp(prefix="izanagi-corpus-f06-")
    try:
        trace_dir = _write_traces(root,
            "C 0 0 1 1 0 1\nW 0 aa U 1 1\nE 0\n"
            "C 1 0 1 2 0 1\nW 1 aa U 1 2\nE 1\n"
            "C 2 0 1 3 2 0\nR 2 aa 1 1\nR 2 aa 1 2\nE 2\n")
        adj = _adjacency(trace_dir)
        assert _edge_set(adj) == {(0, 1), (0, 2), (1, 2), (2, 1)}, adj
        assert sum(len(v) for v in adj.values()) == 4, adj
        result = _verify(root, trace_dir)
        assert result.n_edges == 4, result.n_edges
        assert result.verdict == "non-serializable", result
        assert result.total_cycles == 1, result.total_cycles
        assert len(result.anomalies) == 1, result.anomalies
        anomaly = result.anomalies[0]
        assert set(anomaly.cycle) == {1, 2}, anomaly.cycle
        assert anomaly.phenomenon == "G2", anomaly
        reasons = _reasons(anomaly, 2, 1)
        assert any(r.etype == "rw" and r.key == "aa"
                   and r.u_ver == (1, 1) and r.v_ver == (1, 2)
                   for r in reasons), reasons
        reasons = _reasons(anomaly, 1, 2)
        assert any(r.etype == "wr" and r.key == "aa" and r.u_ver == (1, 2)
                   for r in reasons), reasons
    finally:
        shutil.rmtree(root)


def test_b06_wr_only_cycle_is_g1c():
    """B06: 手で導いた辺は wr 0→1 (x = aa)、wr 1→0 (y = bb) のみ。
    §3.1 の常時 G2 分類と、trace 経路で wr を別種に取り違える壊れ方を検出する。
    """
    root = tempfile.mkdtemp(prefix="izanagi-corpus-b06-")
    try:
        trace_dir = _write_traces(root,
            "C 0 0 1 1 1 1\nR 0 bb 1 2\nW 0 aa U 1 1\nE 0\n"
            "C 1 0 1 2 1 1\nR 1 aa 1 1\nW 1 bb U 1 2\nE 1\n")
        adj = _adjacency(trace_dir)
        assert _edge_set(adj) == {(0, 1), (1, 0)}, adj
        assert sum(len(v) for v in adj.values()) == 2, adj
        result = _verify(root, trace_dir)
        assert result.n_edges == 2, result.n_edges
        assert result.verdict == "non-serializable", result
        assert result.total_cycles == 1, result.total_cycles
        assert len(result.anomalies) == 1, result.anomalies
        anomaly = result.anomalies[0]
        assert set(anomaly.cycle) == {0, 1}, anomaly.cycle
        assert anomaly.phenomenon == "G1c", anomaly
        assert {r.etype for edge in anomaly.edges for r in edge.reasons} == {"wr"}, anomaly
        reasons = _reasons(anomaly, 0, 1)
        assert any(r.etype == "wr" and r.key == "aa" for r in reasons), reasons
        reasons = _reasons(anomaly, 1, 0)
        assert any(r.etype == "wr" and r.key == "bb" for r in reasons), reasons
    finally:
        shutil.rmtree(root)


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = skipped = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except Skip as e:
            print(f"SKIP {fn.__name__}: {e}")
            skipped += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
