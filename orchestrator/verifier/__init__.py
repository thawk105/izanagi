# -*- coding: utf-8 -*-
"""Izanagi mini trace verifier (Phase 1 タスク2)。

trace-enabled build が吐いた実行トレースを読み、serializability を検査する。
Adya の Direct Serialization Graph を作り、rw (anti-dependency) を含む cycle
(G2) まで検出する。anomaly は構造化して返す (絶対規律3)。

公開 API:
    verify_trace_dir(trace_dir) -> VerifyResult
    result_to_dict(res) / render_text(res)

設計背景: docs/roadmap.md §3、.claude/agents/verifier.md。
入力は trace のみ (性能数値を持ち込まない = 入力側隔離, roadmap §3.4-4)。
"""
from .core import verify_trace_dir
from .model import (Anomaly, CycleEdge, EdgeReason, Integrity, Read, Txn,
                    VerifyResult, Write, GENESIS, RW, WR, WW)
from .parse import ParseError, parse_trace_dir
from .report import render_text, result_to_dict

__all__ = [
    "verify_trace_dir",
    "parse_trace_dir",
    "ParseError",
    "render_text",
    "result_to_dict",
    "VerifyResult",
    "Anomaly",
    "CycleEdge",
    "EdgeReason",
    "Integrity",
    "Txn",
    "Read",
    "Write",
    "GENESIS",
    "WW",
    "WR",
    "RW",
]
