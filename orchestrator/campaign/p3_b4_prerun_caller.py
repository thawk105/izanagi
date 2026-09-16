"""Report campaign input gaps and reach the B-4 prerun issuer.

非空 batch は現行の保存形式 (checkpoint の whiteboard 5 field、WAL の
genome / src_token) から構成できない。本 module は現物からの不足報告と、
候補 0 のときの空 batch による発行器到達までを担う。予定 attempt の全件性、
bootstrap 集合への所属、201 の適格行の調達、封印発行の成功は証明しない。
rejected だけを候補にするのは供給源を赤 precursor に限る依頼 (D1936 項 8)
によるもので、registry が SUCCESS を受理しないからではない。
"""

import argparse
import json
from pathlib import Path
from typing import Sequence

from . import p3_b4_analysis_ledgers as ledgers
from . import p3_b4_prerun_issuer as issuer


_DRIVERS = {
    "p3-s4-loop": "base",
    "p3-s5-sort-loop": "sort",
    "p3-s8a-trigger-loop": "trigger",
}
_MISSING_SOURCES = {
    "attempt_id": "No mapping from whiteboard iteration to B-4 attempt identity.",
    "block_id": "No artifact assigns this precursor to a B-4 block.",
    "digest_red_classes": "No checkpoint key binds this precursor to WAL digest evidence.",
    "workload": "No calibrated workload is bound to this precursor.",
    "calibrated_workload_member": "No evidence of membership in the calibrated workload set.",
    "initial_proposal_sha256": "Whiteboard and WAL genome/src_token do not retain the proposal document.",
    "bootstrap_member": "No evidence of initial proposal membership in a bootstrap set fixed in advance.",
    "reference_tps": "No uniquely selected ancestor throughput receipt is bound to this precursor.",
    "reference_snapshot_hash": "No selected ancestor snapshot is bound to this precursor.",
    "reference_receipt_hash": "No selected reference receipt is bound to this precursor.",
    "reference_is_unique": "No ancestry and matching configuration evidence establishes uniqueness.",
    "arm_digest_received": "No per-attempt record establishes digest receipt or non-receipt.",
}


class CampaignInputUnreadable(ValueError):
    """A named campaign cannot be interpreted as checkpoint and lock input."""

    def __init__(self, campaign_root: Path, detail: str) -> None:
        self.campaign_root = str(campaign_root)
        super().__init__(detail)


def collect_scheduled_batch(
    campaign_roots: Sequence[Path],
) -> tuple[tuple[ledgers.B4ScheduledAttemptInput, ...], tuple[dict, ...], tuple[dict, ...]]:
    """Read all campaigns, then report every missing source in candidate order.

    Candidate order is argv order followed by whiteboard array order (the
    prospective zero-based registry ordinal). No incomplete ledger rows are made.
    The twelve missing sources are a static classification based on known limits
    of the current storage format (checkpoint whiteboard's five fields and WAL
    genome/src_token), not the result of searching individual artifacts.
    artifact_path and artifact_key are null because no source was referenced.
    """
    candidates = []
    campaigns = []
    for root in campaign_roots:
        checkpoint_path = root / "loop_state.json"
        try:
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            lock = json.loads((root / "campaign.lock").read_text(encoding="utf-8"))
            if not isinstance(checkpoint, dict) or not isinstance(lock, dict):
                raise ValueError("checkpoint and lock must be JSON objects")
            whiteboard = checkpoint.get("whiteboard")
            if not isinstance(whiteboard, list):
                raise ValueError("whiteboard must be a list")
            trial = lock.get("trial")
            if not isinstance(trial, str) or trial not in _DRIVERS:
                raise ValueError(f"unknown trial: {trial!r}")
            rejected = []
            for index, row in enumerate(whiteboard):
                if not isinstance(row, dict) or not {"iteration", "result"} <= row.keys():
                    raise ValueError(f"whiteboard[{index}] lacks result/iteration")
                if row["result"] == "rejected":
                    rejected.append((root, index, row["iteration"]))
        except (OSError, UnicodeError, ValueError, RecursionError) as exc:
            raise CampaignInputUnreadable(root, str(exc)) from exc
        candidates.extend(rejected)
        campaigns.append({
            "campaign_root": str(root),
            "driver": _DRIVERS[trial],
            "whiteboard_rows": len(whiteboard),
            "rejected_rows": len(rejected),
        })

    # All twelve sources are absent in the current storage format.
    missing = tuple(
        {
            "campaign_root": str(root),
            "whiteboard_index": index,
            "iteration": iteration,
            "field": field,
            "artifact_path": None,
            "artifact_key": None,
            "explanation": explanation,
        }
        for root, index, iteration in candidates
        for field, explanation in _MISSING_SOURCES.items()
    )
    return (), missing, tuple(campaigns)


def planned_result_artifacts_for(
    batch: tuple[ledgers.B4ScheduledAttemptInput, ...], publication_root: Path,
) -> tuple[issuer.B4PlannedResultArtifact, ...]:
    """Describe each planned result leaf without creating any directory."""
    return tuple(
        issuer.B4PlannedResultArtifact(
            attempt_id=attempt.attempt_id,
            artifact_path=str(publication_root / "results" / f"{attempt.attempt_id}.json"),
        )
        for attempt in batch
    )


def issue(batch: tuple[ledgers.B4ScheduledAttemptInput, ...]) -> tuple[dict, int]:
    """Call the real issuer once and serialize its receipt or typed rejection."""
    publication_root = issuer._REPOSITORY_ROOT / "output/b4-prerun-publication"
    try:
        publication = issuer.issue_b4_prerun_publication(
            scheduled_inputs=batch,
            planned_result_artifacts=planned_result_artifacts_for(batch, publication_root),
            publication_root=str(publication_root),
        )
    except issuer.B4PrerunIssuerError as exc:
        return {
            "reason": exc.reason.value,
            "detail": str(exc).removeprefix(f"{exc.reason.value}: "),
        }, 2
    return {"issued": {
        "receipt_path": publication.receipt_path,
        "receipt_sha256": publication.receipt_sha256,
        "issuer_commitment_sha256": publication.issuer_commitment_sha256,
        "manifest_row_count": len(publication.manifest.rows),
    }}, 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--campaign-root", type=Path, nargs="+", required=True)
    args = parser.parse_args(argv)
    try:
        batch, missing, campaigns = collect_scheduled_batch(args.campaign_root)
    except CampaignInputUnreadable as exc:
        payload = {
            "reason": "campaign_input_unreadable",
            "detail": str(exc),
            "campaign_root": exc.campaign_root,
        }
        rc = 2
    else:
        if missing:
            payload = {"reason": "scheduled_input_sources_missing", "missing": missing}
            rc = 2
        else:
            payload, rc = issue(batch)
        payload.update(
            candidate_count=sum(campaign["rejected_rows"] for campaign in campaigns),
            campaigns=campaigns,
        )
    print(json.dumps(payload, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
