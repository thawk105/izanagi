"""Quarantine and compile the Silo lock order hole before writing it."""
from __future__ import annotations

from pathlib import Path

from . import axis_silo_lock_order as axis
from . import p3_s4_loop as L
from .auditor_gate import (AuditorGateFailure, apply_mandatory_deny_only_veto,
                           compute_diff_digest)
from .diff_quarantine import DiffQuarantineResult, DiffRejectSubtype
from .silo_lock_order_compile import check_order_body


def _reject(subtype, rule_id):
    digest = {'rejection_type': 'diff-quarantine', 'subtype': subtype.value,
              'reason': subtype.value, 'diff_region': axis.SOURCE_REL,
              'template_diff_id': axis.MARKER_ID, 'evidence': rule_id,
              'rule_id': rule_id}
    return DiffQuarantineResult(passed=False, subtype=subtype,
                                reason=subtype.value, digest=digest, violations=[digest])


def order_gate(sub, implementation, auditor, *, compiler, scratch_dir, write,
               origin=None):
    """Passing means quarantine, grammar and isolated compile passed, not a real build."""
    result, base, edited, working_diff = L.quarantine(
        sub, implementation, marker_id=axis.MARKER_ID,
        source_rel=axis.SOURCE_REL, write=False)
    if result.passed:
        grammar, compiled = check_order_body(
            implementation, compiler=compiler, scratch_dir=scratch_dir)
        if not grammar.accepted:
            result = _reject(DiffRejectSubtype.POLICY_GRAMMAR,
                             grammar.rule_id or 'policy-grammar')
        elif compiled is None or not compiled.accepted:
            rule = ('compile-unavailable' if compiled is None or compiled.unavailable
                    else 'compile-timeout' if compiled.timed_out else 'compile-error')
            result = _reject(DiffRejectSubtype.POLICY_COMPILE, rule)
    if result.passed and auditor is not None:
        result = apply_mandatory_deny_only_veto(
            result, auditor, working_diff, diff_region=axis.SOURCE_REL,
            template_diff_id=axis.MARKER_ID, max_violation_type=30)
    if result.passed and write:
        if auditor is None and origin not in ('machine', 'initial'):
            raise AuditorGateFailure('auditor required for write')
        source = Path(sub) / axis.SOURCE_REL
        source.write_text(edited, encoding='utf-8')
        rebound = L.make_working_diff(base, source.read_text(encoding='utf-8'), axis.SOURCE_REL)
        if compute_diff_digest(rebound) != compute_diff_digest(working_diff):
            raise AuditorGateFailure('written order digest mismatch')
    return result, working_diff
