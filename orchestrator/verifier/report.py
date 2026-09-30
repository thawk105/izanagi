# -*- coding: utf-8 -*-
"""VerifyResult の構造化出力 (JSON 用 dict) と人間可読テキスト。

絶対規律3: anomaly は単なる pass/fail にしない。**どの trx 間の・どの種類の
依存 (ww/wr/rw) で・どのレコード/版で cycle ができたか** を構造化して返す。
これが次の variant 生成を導くシグナルになる。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from .model import Anomaly, CycleEdge, EdgeReason, VerifyResult
from .parse import SortPermutationViolation, TxnFramingViolation


def _reason_to_dict(r: EdgeReason) -> Dict[str, Any]:
    d: Dict[str, Any] = {"type": r.etype, "key": r.key}
    if r.u_ver is not None:
        d["u_ver"] = list(r.u_ver)
    if r.v_ver is not None:
        d["v_ver"] = list(r.v_ver)
    return d


def _edge_to_dict(e: CycleEdge) -> Dict[str, Any]:
    return {
        "from": e.src,
        "to": e.dst,
        "types": e.types,
        "reasons": [_reason_to_dict(r) for r in e.reasons],
    }


def _anomaly_to_dict(a: Anomaly) -> Dict[str, Any]:
    return {
        "phenomenon": a.phenomenon,
        "length": a.length,
        "cycle": a.cycle,
        "edges": [_edge_to_dict(e) for e in a.edges],
    }


def _framing_violation_to_dict(v: TxnFramingViolation) -> Dict[str, Any]:
    return {
        "kind": v.kind,
        "txid": v.txid,
        "expected_reads": v.expected_reads,
        "observed_reads": v.observed_reads,
        "expected_writes": v.expected_writes,
        "observed_writes": v.observed_writes,
    }


def _permutation_violation_to_dict(
        v: SortPermutationViolation,
) -> Dict[str, Any]:
    """Return only typed observation data and the non-authoritative thread hint."""
    observation = v.observation
    return {
        "observation": {
            "kind": observation.kind,
            "size_preserved": observation.size_preserved,
            "rcdptr_multiset_preserved": observation.rcdptr_multiset_preserved,
            "recognized": observation.recognized,
        },
        "source_thread_hint": v.source_thread_hint,
        "source_thread_hint_basis": v.source_thread_hint_basis,
    }


def _permutation_violation_details_to_dict(
        violations: List[SortPermutationViolation],
) -> Dict[str, Any]:
    kinds = ("size-changed", "rcdptr-set-changed", "unknown")
    counts = {kind: 0 for kind in kinds}
    sample: List[Dict[str, Any]] = []
    unknown_reason_sample: List[str] = []
    for violation in violations:
        kind = violation.observation.kind
        if kind not in counts:
            kind = "unknown"
        counts[kind] += 1
        if len(sample) < 5:
            sample.append(_permutation_violation_to_dict(violation))
        if kind == "unknown" and len(unknown_reason_sample) < 5:
            unknown_reason_sample.append(
                json.dumps(violation.raw_reason, ensure_ascii=True))
    return {
        "counts": counts,
        "sample": sample,
        "unknown_reason_sample": unknown_reason_sample,
    }


def result_to_dict(res: VerifyResult) -> Dict[str, Any]:
    result = {
        "trace_dir": res.trace_dir,
        "verdict": res.verdict,              # serializable | indeterminate | non-serializable
        "certified": res.certified,          # ゲート通過とみなしてよい唯一の信号
        "serializable": res.serializable,    # 純粋なグラフ事実 (DSG 非巡回)
        "stats": {
            "txns": res.n_txns,
            "reads": res.n_reads,
            "writes": res.n_writes,
            "keys": res.n_keys,
            "edges": res.n_edges,
            # A 行 (段 8a/D48 計装) の要因別カウント。集計データであり
            # verdict/integrity に不関与 — 通常 verify では常に {}
            "abort_reasons": dict(res.abort_reasons),
        },
        "integrity": {
            "clean": res.integrity.clean(),
            "orphan_reads": res.integrity.orphan_reads,
            "version_dups": res.integrity.version_dups,
            "dup_txids": res.integrity.dup_txids,
            "genesis_commits": res.integrity.genesis_commits,
            "missing_txids": res.integrity.missing_txids,
            "write_version_mismatch": res.integrity.write_version_mismatch,
            "malformed_keys": res.integrity.malformed_keys,
            "framing_violations": res.integrity.framing_violations,
            "framing_violation_details": [
                _framing_violation_to_dict(v)
                for v in res.integrity.framing_violation_details
            ],
            "lock_coverage_violations": res.integrity.lock_coverage_violations,
            "write_intent_violations": res.integrity.write_intent_violations,
            "permutation_violations": res.integrity.permutation_violations,
            "permutation_violation_details": _permutation_violation_details_to_dict(
                res.integrity.permutation_violation_details,
            ),
            "notes": res.integrity.notes,
        },
        "anomaly_count": len(res.anomalies),
        "total_cycles": res.total_cycles,
        "anomalies": [_anomaly_to_dict(a) for a in res.anomalies],
    }
    if res.integrity.gate_witness_enabled:
        from .model import MEANING_VERSION
        ig = res.integrity
        result["gate_witness"] = {
            "meaning_version": MEANING_VERSION,
            "required": ig.gate_witness_required,
            "counts": {
                "unreachable": ig.gate_unreachable,
                "D1a": ig.gate_d1a, "D1b1": ig.gate_d1b1,
                "D1b2": ig.gate_d1b2, "D1c": ig.gate_d1c,
                "D2a": ig.gate_d2a, "D2b_i": ig.gate_d2b_i,
                "D2b_ii": ig.gate_d2b_ii,
            },
            "occurrence": {
                "own_write_read_transactions": ig.gate_own_write_read_transactions,
                "written_transactions": ig.gate_written_transactions,
                "repeated_write_key_transactions": ig.gate_repeated_write_key_transactions,
                "external_reads_checked": ig.gate_external_reads_checked,
            },
            "D5": ig.gate_d5,
        }
    return result


def _fmt_ver(v) -> str:
    return f"({v[0]},{v[1]})" if v is not None else "-"


def _edge_line(e: CycleEdge) -> str:
    bits: List[str] = []
    for r in e.reasons:
        if r.etype == "rw":
            bits.append(f"rw key={r.key} read{_fmt_ver(r.u_ver)}→overwritten{_fmt_ver(r.v_ver)}")
        elif r.etype == "wr":
            bits.append(f"wr key={r.key} wrote{_fmt_ver(r.u_ver)}→read")
        else:
            bits.append(f"ww key={r.key} {_fmt_ver(r.u_ver)}→{_fmt_ver(r.v_ver)}")
    why = "; ".join(bits) if bits else "(no reason reconstructed)"
    return f"    T{e.src} → T{e.dst}  [{','.join(e.types) or '?'}]  {why}"


def render_text(res: VerifyResult) -> str:
    lines: List[str] = []
    lines.append(f"[{res.verdict.upper()}] {res.trace_dir}")
    s = res
    lines.append(
        f"  txns={s.n_txns} reads={s.n_reads} writes={s.n_writes} "
        f"keys={s.n_keys} edges={s.n_edges}")
    ig = res.integrity
    if not ig.clean():
        lines.append(
            f"  ! integrity UNCLEAN -> cannot certify serializable: "
            f"orphan_reads={ig.orphan_reads} version_dups={ig.version_dups} "
            f"dup_txids={ig.dup_txids} genesis_commits={ig.genesis_commits} "
            f"missing_txids={ig.missing_txids} "
            f"write_version_mismatch={ig.write_version_mismatch} "
            f"malformed_keys={ig.malformed_keys} "
            f"framing_violations={ig.framing_violations} "
            f"lock_coverage_violations={ig.lock_coverage_violations} "
            f"write_intent_violations={ig.write_intent_violations} "
            f"permutation_violations={ig.permutation_violations}")
    for note in ig.notes:
        lines.append(f"  · {note}")
    if not res.serializable:
        lines.append(f"  anomalies (showing {len(res.anomalies)}):")
        for i, a in enumerate(res.anomalies, 1):
            ring = " → ".join(f"T{t}" for t in a.cycle) + f" → T{a.cycle[0]}"
            lines.append(f"  #{i} {a.phenomenon} (len {a.length}): {ring}")
            for e in a.edges:
                lines.append(_edge_line(e))
    return "\n".join(lines)
