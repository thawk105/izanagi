# -*- coding: utf-8 -*-
"""検証のトップレベル: trace ディレクトリ -> VerifyResult。

verifier の入力は **trace のみ**。性能数値 (throughput 等) をここに渡さない
(roadmap §3.4-4 anti-fabrication isolation = 入力側隔離。捏造経路をデータレベル
で断つ。書き込み権限を持たない出力側隔離と対になる)。
"""
from __future__ import annotations

from typing import Dict, Optional

from .dsg import DSG
from .model import VerifyResult
from .parse import parse_trace_dir


def verify_trace_dir(trace_dir: str, max_report: Optional[int] = 20) -> VerifyResult:
    """1 run (= 1 trace ディレクトリ) を検証する。"""
    txns, issues = parse_trace_dir(trace_dir)
    dsg = DSG(txns)
    dsg.integrity.dup_txids = len(issues.dup_txids)
    if issues.dup_txids:
        sample = ", ".join(str(x) for x in issues.dup_txids[:5])
        dsg.integrity.notes.append(f"duplicate txid C-lines: {sample} ...")
    dsg.integrity.missing_txids = issues.missing_txids
    if issues.missing_txids:
        sample = ", ".join(str(x) for x in issues.missing_sample)
        dsg.integrity.notes.append(
            f"{issues.missing_txids} txid gap(s) — trace-hook guarantees dense txids, "
            f"gaps mean whole txns are missing (e.g. {sample})")
    dsg.integrity.write_version_mismatch = len(issues.write_version_mismatches)
    if issues.write_version_mismatches:
        sample = ", ".join(str(x) for x in issues.write_version_mismatches[:5])
        dsg.integrity.notes.append(
            f"W-line version != C-line commit in txids: {sample} ...")
    dsg.integrity.malformed_keys = issues.malformed_keys
    if issues.malformed_keys:
        sample = ", ".join(issues.malformed_key_sample)
        dsg.integrity.notes.append(
            f"{issues.malformed_keys} malformed key token(s) (expect lowercase even-length "
            f"hex; case/format drift silently splits conflict edges): {sample}")

    # X 行 = writePhase の lock 被覆 assert (D38)。variant が lock 被覆を破って書いた
    # = torn read が起こりうる → trace の版 stamp が信用できず serializable を認証
    # できない (絶対規律2、他 integrity カウンタと同じ indeterminate 帰結)。cycle は
    # 生まないので anomalies でなくここに乗せ、critic は「機構欠落型」として読む。
    dsg.integrity.lock_coverage_violations = len(issues.lock_coverage_violations)
    if issues.lock_coverage_violations:
        # (txid, key, reason) の見本。reason 別の件数も出して機構の破れ方を示す。
        sample = "; ".join(
            f"txn{t} key={k} ({r})"
            for t, k, r in issues.lock_coverage_violations[:5])
        reasons: Dict[str, int] = {}
        for _t, _k, r in issues.lock_coverage_violations:
            reasons[r] = reasons.get(r, 0) + 1
        by_reason = ", ".join(f"{r}×{n}" for r, n in sorted(reasons.items()))
        dsg.integrity.notes.append(
            f"{len(issues.lock_coverage_violations)} lock-coverage violation(s) "
            f"[{by_reason}] — writePhase wrote a tuple without holding its lock "
            f"(torn-read window; variant broke lock coverage, not a trace-hook fault): "
            f"{sample}")

    anomalies, total = dsg.anomalies(max_report=max_report)
    if total > len(anomalies):
        dsg.integrity.notes.append(
            f"{total} cycles (SCCs) found; reporting {len(anomalies)} witnesses")

    return VerifyResult(
        trace_dir=trace_dir,
        serializable=(total == 0),
        anomalies=anomalies,
        integrity=dsg.integrity,
        n_txns=len(txns),
        n_reads=sum(len(t.reads) for t in txns),
        n_writes=sum(len(t.writes) for t in txns),
        n_keys=len(dsg.versions),
        n_edges=dsg.n_edges,
        total_cycles=total,
    )
