# -*- coding: utf-8 -*-
"""検証のトップレベル: trace ディレクトリ + source context -> VerifyResult。

verifier の入力は trace、optional な trace 外 commit counter、protocol/source context。
性能数値 (throughput 等) をここに渡さない
(roadmap §3.4-4 anti-fabrication isolation = 入力側隔離。捏造経路をデータレベル
で断つ。書き込み権限を持たない出力側隔離と対になる)。
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import os
from typing import Dict, Optional

from .dsg import DSG
from .model import (
    AnomalyV3, EdgeReasonV3, object_label,
    CompiledProtocolSourceSnapshot,
    VerifyResult,
    assess_compiled_protocol_source_snapshot,
    assess_protocol_proof_surfaces,
)
from .parse import _CompactTrace, _LegacyTrace, _parse_trace_dir_compact
from .commit_receipt import CommitReceiptError, _domain_digest
from .report import result_to_dict


def verify_trace_dir(
        trace_dir: str, max_report: Optional[int] = 20, *,
        expected_commits: Optional[int] = None,
        workers: Optional[int] = None,
        protocol: Optional[str] = None,
        ccbench_root: Optional[str | os.PathLike[str]] = None,
        _proof_source_snapshot: Optional[CompiledProtocolSourceSnapshot] = None,
) -> VerifyResult:
    """1 run を検証する。source context 未指定・不読は認証不能にする。"""
    parsed = _parse_trace_dir_compact(trace_dir, workers=workers)
    if isinstance(parsed, _CompactTrace):
        issues = parsed.issues
        dsg = DSG.from_compact(parsed)
        n_txns = len(parsed.winner_txid)
        n_reads = parsed.n_reads
        n_writes = parsed.n_writes
    elif isinstance(parsed, _LegacyTrace):
        txns = parsed.txns
        issues = parsed.issues
        dsg = DSG(txns)
        n_txns = len(txns)
        n_reads = sum(len(txn.reads) for txn in txns)
        n_writes = sum(len(txn.writes) for txn in txns)
    else:  # fail closed if the internal parser union grows without wiring here
        raise TypeError(f"unsupported parsed trace type: {type(parsed)!r}")
    if _proof_source_snapshot is None:
        assessment = assess_protocol_proof_surfaces(protocol, ccbench_root)
    else:
        assessment = assess_compiled_protocol_source_snapshot(
            _proof_source_snapshot,
        )
    dsg.integrity.proof_surfaces = assessment
    if expected_commits is not None:
        # witness は trace 外の CCBench counter。片側だけの部分状態を作らず、
        # expected/observed を持つ新しい Integrity へ一度で差し替える。
        observed_commits = n_txns
        dsg.integrity = replace(
            dsg.integrity,
            expected_commits=expected_commits,
            observed_commits=observed_commits,
        )
        if observed_commits != expected_commits:
            dsg.integrity.notes.append(
                "commit witness mismatch: "
                f"expected={expected_commits} observed={observed_commits} "
                f"delta={observed_commits - expected_commits}")
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

    dsg.integrity.framing_violations = len(issues.framing_violations)
    dsg.integrity.framing_violation_details = list(issues.framing_violations)
    if issues.framing_violations:
        by_kind: Dict[str, int] = {}
        for violation in issues.framing_violations:
            by_kind[violation.kind] = by_kind.get(violation.kind, 0) + 1
        kinds = ", ".join(
            f"{kind}×{count}" for kind, count in sorted(by_kind.items()))
        samples = []
        for violation in issues.framing_violations[:5]:
            sample = f"txn{violation.txid} {violation.kind}"
            if violation.expected_reads is not None:
                sample += (
                    f" reads={violation.observed_reads}/{violation.expected_reads}"
                    f" writes={violation.observed_writes}/{violation.expected_writes}")
            samples.append(sample)
        dsg.integrity.notes.append(
            f"{len(issues.framing_violations)} txn framing violation(s) "
            f"[{kinds}] — declared R/W counts or mandatory E boundary is broken "
            f"(trace may omit dependency edges): {'; '.join(samples)}")

    # X 行 = writePhase の lock 被覆 assert (D38)。variant が lock 被覆を破って書いた
    # = torn read が起こりうる → trace の版 stamp が信用できず serializable を認証
    # できない (絶対規律2、他 integrity カウンタと同じ indeterminate 帰結)。cycle は
    # 生まないので anomalies でなくここに乗せ、critic は「機構欠落型」として読む。
    dsg.integrity.lock_coverage_violations = len(issues.lock_coverage_violations)
    if issues.lock_coverage_violations:
        # (txid, key, reason) の見本。reason 別の件数も出して機構の破れ方を示す。
        sample = "; ".join(
            f"txn{t} {object_label(k)} ({r})"
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

    # I 行 = writePhase の write_set_ と API write intent の相互被覆 assert (T-152)。
    # X 行と同じ txid 相関型だが cycle ではない。write 完全性を認証できないため
    # anomalies でなく integrity に乗せ、serializable の純グラフ事実は変えない。
    dsg.integrity.write_intent_violations = len(issues.write_intent_violations)
    if issues.write_intent_violations:
        sample_i = "; ".join(
            f"txn{t} {object_label(k)} ({r})"
            for t, k, r in issues.write_intent_violations[:5])
        reasons_i: Dict[str, int] = {}
        for _t, _k, r in issues.write_intent_violations:
            reasons_i[r] = reasons_i.get(r, 0) + 1
        by_reason_i = ", ".join(
            f"{r}×{n}" for r, n in sorted(reasons_i.items()))
        dsg.integrity.notes.append(
            f"{len(issues.write_intent_violations)} write-intent coverage "
            f"violation(s) [{by_reason_i}] — write_set_ membership and API write "
            f"intent disagree (write completeness cannot be certified; not a cycle): "
            f"{sample_i}")

    # P 行 = validationPhase の permutation 保存 assert (D41)。sort が write_set_ の
    # 要素を欠落/複製させた (非 strict-weak-order comparator の UB) 可能性 — X 行と
    # 同じ理由で anomalies でなくここに乗せる (絶対規律2)。
    dsg.integrity.permutation_violations = len(issues.permutation_violations)
    dsg.integrity.permutation_violation_details = list(
        issues.permutation_violation_details)
    if issues.permutation_violations:
        reasons_p: Dict[str, int] = {}
        for r in issues.permutation_violations:
            reasons_p[r] = reasons_p.get(r, 0) + 1
        by_reason_p = ", ".join(f"{r}×{n}" for r, n in sorted(reasons_p.items()))
        dsg.integrity.notes.append(
            f"{len(issues.permutation_violations)} permutation-preservation "
            f"violation(s) [{by_reason_p}] — validationPhase's write_set_ sort "
            f"dropped or duplicated an element (non-strict-weak-order comparator "
            f"UB, not a trace-hook fault)")

    anomalies, total = dsg.anomalies(max_report=max_report)
    if total > len(anomalies):
        dsg.integrity.notes.append(
            f"{total} cycles (SCCs) found; reporting {len(anomalies)} witnesses")

    return VerifyResult(
        trace_dir=trace_dir,
        serializable=(total == 0),
        anomalies=anomalies,
        integrity=dsg.integrity,
        n_txns=n_txns,
        n_reads=n_reads,
        n_writes=n_writes,
        n_keys=len(dsg.versions),
        n_edges=dsg.n_edges,
        total_cycles=total,
        abort_reasons=dict(issues.abort_reasons),
    )


def result_to_dict_v3(res: VerifyResult) -> dict:
    """Extend v3 anomaly witnesses and existence details; preserve legacy projection."""
    result = result_to_dict(res)
    if res.integrity.existence_violation_details is not None:
        result["integrity"]["existence_violations"] = res.integrity.existence_violations
        result["integrity"]["existence_violation_details"] = [
            {"txid": v.txid, "table": v.table, "key": v.key,
             "version": list(v.version), "kind": v.kind, "ops": list(v.ops)}
            for v in res.integrity.existence_violation_details
        ]
    for anomaly, projected in zip(res.anomalies, result["anomalies"]):
        if not isinstance(anomaly, AnomalyV3):
            continue
        if len(anomaly.cycle) != len(anomaly.cycle_tx_types):
            raise ValueError("v3 cycle node/type count mismatch")
        projected["cycle_nodes"] = [
            {"txid": txid, "tx_type": tx_type}
            for txid, tx_type in zip(anomaly.cycle, anomaly.cycle_tx_types)
        ]
        for edge, edge_dict in zip(anomaly.edges, projected["edges"]):
            for reason, reason_dict in zip(edge.reasons, edge_dict["reasons"]):
                if not isinstance(reason, EdgeReasonV3):
                    raise ValueError("v3 anomaly contains a reason without table")
                reason_dict["table"] = reason.table
    return result


def _bind_verifier_capability_entrypoint():
    """Create the only issuer together with an unexported issuer token."""
    issuer_token = object()
    issued_capabilities: dict[object, tuple[object, ...]] = {}
    consumed_nonces: set[object] = set()

    def _bound_proof_source_snapshot(
            *, genome: object, source_evidence: object,
            build_admission: object, receipt_variant: str,
    ) -> CompiledProtocolSourceSnapshot:
        """Validate the build-bound, non-wire source snapshot for capability issue."""
        # Lazy imports preserve the established campaign -> verifier import
        # direction at module load while checking exact sealed runtime types.
        from ..campaign.build_admission import BuildAdmission
        from ..campaign.model import Genome
        from ..campaign.source_digest import SourceEvidence

        if (type(genome) is not Genome
                or type(source_evidence) is not SourceEvidence
                or type(build_admission) is not BuildAdmission):
            raise CommitReceiptError(
                "verification capability requires exact build source binding"
            )
        canonical = genome.canonical()
        expected_genome_sha256 = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()
        try:
            admitted_source = build_admission.as_wal_receipt()["source"]
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise CommitReceiptError(
                "verification capability build admission is invalid"
            ) from exc
        snapshot = source_evidence.proof_source_snapshot
        if (source_evidence.genome_sha256 != expected_genome_sha256
                or admitted_source != source_evidence.as_receipt()
                or source_evidence.verification_variant != receipt_variant
                or type(snapshot) is not CompiledProtocolSourceSnapshot
                or snapshot.protocol != genome.protocol
                or snapshot.ccbench_root != source_evidence.source_root):
            raise CommitReceiptError(
                "verification capability source/genome/variant binding mismatch"
            )
        return snapshot

    class _VerificationCapability:
        """Opaque, operation-bound evidence from one verifier invocation."""

        __slots__ = (
            "_verdict", "_certified", "_result_sha256", "_pid",
            "_sink_kind", "_lock_identity_sha256", "_variant",
            "_operation_identity", "_workload_tag", "_nonce",
            "_sealed",
        )

        def __init__(
                self, result: VerifyResult, *, sink_kind: str,
                lock_identity_sha256: str, variant: str,
                operation_identity: str, workload_tag: str,
                _token: object = None,
        ) -> None:
            if _token is not issuer_token or type(result) is not VerifyResult:
                raise TypeError("VerificationCapability is verifier-issued")
            projection = result_to_dict(result)
            projection.pop("trace_dir", None)
            projection["integrity"].pop("framing_violation_details", None)
            projection["integrity"].pop("permutation_violation_details", None)
            object.__setattr__(self, "_verdict", result.verdict)
            object.__setattr__(self, "_certified", result.certified)
            object.__setattr__(
                self, "_result_sha256",
                _domain_digest(b"izanagi-verifier-result-v1", projection),
            )
            object.__setattr__(self, "_pid", os.getpid())
            object.__setattr__(self, "_sink_kind", sink_kind)
            object.__setattr__(
                self, "_lock_identity_sha256", lock_identity_sha256,
            )
            object.__setattr__(self, "_variant", variant)
            object.__setattr__(self, "_operation_identity", operation_identity)
            object.__setattr__(self, "_workload_tag", workload_tag)
            nonce = object()
            issued_capabilities[nonce] = (
                result.verdict,
                result.certified,
                self._result_sha256,
                os.getpid(),
                sink_kind,
                lock_identity_sha256,
                variant,
                operation_identity,
                workload_tag,
            )
            object.__setattr__(self, "_nonce", nonce)
            object.__setattr__(self, "_sealed", True)

        def __setattr__(self, name, value):
            if getattr(self, "_sealed", False):
                raise AttributeError("VerificationCapability is immutable")
            object.__setattr__(self, name, value)

        def _assert_matches(
                self, *, sink_kind: str, lock_identity_sha256: str,
                variant: str, operation_identity: str, workload_tag: str,
        ) -> None:
            try:
                authority = issued_capabilities.get(self._nonce)
            except (AttributeError, TypeError):
                authority = None
            if authority is None:
                raise CommitReceiptError(
                    "verification capability has no issuer authority"
                )
            (
                verdict, certified, _result_sha256, issuer_pid,
                bound_sink, bound_lock, bound_variant, bound_operation,
                bound_workload,
            ) = authority
            if (type(self) is not _VerificationCapability
                    or issuer_pid != os.getpid()
                    or verdict != "serializable"
                    or certified is not True):
                raise CommitReceiptError(
                    "verification capability is not certified in this process"
                )
            if self._nonce in consumed_nonces:
                raise CommitReceiptError(
                    "verification capability was already consumed"
                )
            if (bound_sink != sink_kind
                    or bound_lock != lock_identity_sha256
                    or bound_variant != variant
                    or bound_operation != operation_identity
                    or bound_workload != workload_tag):
                raise CommitReceiptError(
                    "verification capability is bound to a different operation"
                )

        def _receipt_evidence(self) -> tuple[str, bool, str]:
            try:
                authority = issued_capabilities[self._nonce]
            except (AttributeError, KeyError, TypeError) as exc:
                raise CommitReceiptError(
                    "verification capability has no issuer authority"
                ) from exc
            return authority[0], authority[1], authority[2]

        def _consume(self) -> None:
            try:
                issued = self._nonce in issued_capabilities
                consumed = self._nonce in consumed_nonces
            except (AttributeError, TypeError):
                issued = False
                consumed = False
            if not issued or consumed:
                raise CommitReceiptError(
                    "verification capability was already consumed"
                )
            consumed_nonces.add(self._nonce)

    def _verify_trace_dir_with_capability(
            trace_dir: str, max_report: Optional[int] = 20, *,
            expected_commits: Optional[int] = None,
            workers: Optional[int] = None,
            genome: object,
            source_evidence: object,
            build_admission: object,
            receipt_sink_kind: str,
            receipt_lock_identity_sha256: str,
            receipt_variant: str,
            receipt_operation_identity: str,
            receipt_workload_tag: str,
    ) -> tuple[VerifyResult, _VerificationCapability]:
        """Run verification from the exact build-bound immutable source snapshot."""
        proof_source_snapshot = _bound_proof_source_snapshot(
            genome=genome,
            source_evidence=source_evidence,
            build_admission=build_admission,
            receipt_variant=receipt_variant,
        )
        result = verify_trace_dir(
            trace_dir, max_report=max_report, expected_commits=expected_commits,
            workers=workers, _proof_source_snapshot=proof_source_snapshot,
        )
        capability = _VerificationCapability(
            result,
            sink_kind=receipt_sink_kind,
            lock_identity_sha256=receipt_lock_identity_sha256,
            variant=receipt_variant,
            operation_identity=receipt_operation_identity,
            workload_tag=receipt_workload_tag,
            _token=issuer_token,
        )
        return result, capability

    return _VerificationCapability, _verify_trace_dir_with_capability


VerificationCapability, verify_trace_dir_with_capability = (
    _bind_verifier_capability_entrypoint()
)
del _bind_verifier_capability_entrypoint
