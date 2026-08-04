"""Reflux IR のテスト専用・独立 golden 台帳。

この台帳は production (``orchestrator/campaign/**``) から import してはならず、値を
実行時に導出してもならない。いずれも検査を恒真化するためである。値は親が宣言した
規範仕様と ``patches/silo-backoff-trigger-gating-variant.patch`` から独立に導出し、
旧実装、campaign 記録、freeze から転記していない。

更新契約: production の変更後にテストを緑にする目的でこの期待値を書き換えることは、
正しさゲートを緩める変異であり、絶対規律 2 違反である。規範仕様と骨格 patch の正当な
変更を独立に確認できた場合に限り、同じ独立導出手順で更新する。
"""

from __future__ import annotations


EXPECTED_REASON_ORDER = (
    "lock-conflict",
    "update-absent",
    "readvali-tid",
    "readvali-locked",
    "node-vali",
)

EXPECTED_CASES = (
    (0, "00000", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset;"),
    (1, "10000", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict;"),
    (2, "01000", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent;"),
    (3, "11000", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent;"),
    (4, "00100", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid;"),
    (5, "10100", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid;"),
    (6, "01100", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid;"),
    (7, "11100", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid;"),
    (8, "00010", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;"),
    (9, "10010", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;"),
    (10, "01010", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;"),
    (11, "11010", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;"),
    (12, "00110", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;"),
    (13, "10110", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;"),
    (14, "01110", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;"),
    (15, "11110", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;"),
    (16, "00001", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (17, "10001", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (18, "01001", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (19, "11001", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (20, "00101", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (21, "10101", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (22, "01101", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (23, "11101", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (24, "00011", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (25, "10011", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (26, "01011", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (27, "11011", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (28, "00111", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (29, "10111", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (30, "01111", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
    (31, "11111", "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"),
)
