# -*- coding: utf-8 -*-
"""Izanagi mini trace verifier (Phase 1 タスク2)。

trace-enabled build が吐いた実行トレースを読み、serializability を検査する。
Adya の Direct Serialization Graph を作り、rw (anti-dependency) を含む cycle
(G2) まで検出する。anomaly は構造化して返す (絶対規律3)。

公開 API:
    verify_trace_dir(trace_dir, *, expected_commits=None, protocol=None,
                     ccbench_root=None) -> VerifyResult
    verify_trace_dir_with_capability(trace_dir, *, genome, source_evidence,
                     build_admission, receipt_...) -> (VerifyResult, capability)
    result_to_dict(res) / render_text(res)

設計背景: docs/roadmap.md §3、.claude/agents/verifier.md。
入力は trace、optional な trace 外 commit counter、protocol/source context。
性能数値は持ち込まない
(入力側隔離, roadmap §3.4-4)。
"""
from .core import (
    VerificationCapability,
    verify_trace_dir,
    verify_trace_dir_with_capability,
)
from .commit_receipt import (
    CAMPAIGN_WAL_SINK,
    QUALIFICATION_SINK,
    RECEIPT_PAYLOAD_KEY,
    CommitReceipt,
    CommitReceiptError,
    ReplayVerificationEvidence,
    admit_replay_evidence,
    campaign_lock_sha256,
    issue_commit_receipt,
    issue_replay_commit_receipt,
    validate_live_receipt,
    validate_serialized_receipt,
)
from .model import (Anomaly, CycleEdge, EdgeReason, Integrity, Read, Txn,
                    VerifyResult, Write, GENESIS, RW, WR, WW)
from .parse import ParseError, parse_trace_dir
from .report import render_text, result_to_dict

__all__ = [
    "verify_trace_dir",
    "verify_trace_dir_with_capability",
    "VerificationCapability",
    "CommitReceipt",
    "CommitReceiptError",
    "ReplayVerificationEvidence",
    "CAMPAIGN_WAL_SINK",
    "QUALIFICATION_SINK",
    "RECEIPT_PAYLOAD_KEY",
    "campaign_lock_sha256",
    "issue_commit_receipt",
    "issue_replay_commit_receipt",
    "admit_replay_evidence",
    "validate_live_receipt",
    "validate_serialized_receipt",
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
