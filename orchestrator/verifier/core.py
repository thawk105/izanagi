# -*- coding: utf-8 -*-
"""検証のトップレベル: trace ディレクトリ -> VerifyResult。

verifier の入力は **trace のみ**。性能数値 (throughput 等) をここに渡さない
(roadmap §3.4-4 anti-fabrication isolation = 入力側隔離。捏造経路をデータレベル
で断つ。書き込み権限を持たない出力側隔離と対になる)。
"""
from __future__ import annotations

from typing import Optional

from .dsg import DSG
from .model import VerifyResult
from .parse import parse_trace_dir


def verify_trace_dir(trace_dir: str, max_report: Optional[int] = 20) -> VerifyResult:
    """1 run (= 1 trace ディレクトリ) を検証する。"""
    txns, dup_txids = parse_trace_dir(trace_dir)
    dsg = DSG(txns)
    dsg.integrity.dup_txids = len(dup_txids)
    if dup_txids:
        sample = ", ".join(str(x) for x in dup_txids[:5])
        dsg.integrity.notes.append(f"duplicate txid C-lines: {sample} ...")

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
    )
