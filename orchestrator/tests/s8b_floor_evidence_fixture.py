# -*- coding: utf-8 -*-
"""T-1155/T-1178 の test-only independent evidence builders。"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from orchestrator.campaign.sort_swo_oracle import (
    COMPILE_FLAGS_SHA256,
    CORPUS_ID,
    CORPUS_VERSION,
    DEPENDENCY_MANIFEST_SHA256,
    ORACLE_CONTRACT_ID,
    TU_TEMPLATE_SHA256,
)


def canonical_json_bytes(value: object) -> bytes:
    """Production helper から独立した test-only canonical JSON 実装。"""

    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_json_line(value: object) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def fake_sort_swo_pass_attempt() -> dict[str, object]:
    """絶対 path と raw compiler version を持つ deterministic PASS attempt。"""

    hole_sha = hashlib.sha256(b"fixture-materialized-hole").hexdigest()
    proposal_sha = hashlib.sha256(b"fixture-proposal").hexdigest()
    raw = {
        "contract_id": ORACLE_CONTRACT_ID,
        "materialized_hole_sha256": hole_sha,
        "proposal_sha256": proposal_sha,
        "corpus_id": CORPUS_ID,
        "corpus_version": CORPUS_VERSION,
        "compiler_realpath": "/fixture/toolchain/bin/c++",
        "compiler_version": "fixture-c++ 1.0 日本語",
        "compile_flags_sha256": COMPILE_FLAGS_SHA256,
        "tu_sha256": hashlib.sha256(b"fixture-tu").hexdigest(),
        "tu_template_sha256": TU_TEMPLATE_SHA256,
        "dependency_root_realpath": "/fixture/dependencies",
        "dependency_config_sha256": hashlib.sha256(
            b"fixture-dependency-config"
        ).hexdigest(),
        "dependency_manifest_sha256": DEPENDENCY_MANIFEST_SHA256,
    }
    return {
        "event": "sort-swo-oracle-attempt",
        "classification": "pass",
        "reason_code": "sort-swo-oracle-pass",
        "oracle_contract_id": ORACLE_CONTRACT_ID,
        "materialized_hole_sha256": hole_sha,
        "proposal_sha256": proposal_sha,
        "oracle_receipt": raw,
    }


def expected_portable_sort_swo_pass_receipt(
    *, cell_id: str, holdout_id: str, configuration_id: str,
    entry_sha256: str, binary_sha256: str,
) -> dict[str, object]:
    """Production projector を呼ばず portable projection の期待値を組み立てる。"""

    attempt = fake_sort_swo_pass_attempt()
    raw = attempt["oracle_receipt"]
    assert isinstance(raw, dict)
    return {
        "schema": "s8b-sort-swo-pass-receipt/v2",
        "cell_id": cell_id,
        "holdout_id": holdout_id,
        "configuration_id": configuration_id,
        "entry_sha256": entry_sha256,
        "binary_sha256": binary_sha256,
        "classification": "pass",
        "reason_code": "sort-swo-oracle-pass",
        "oracle_contract_id": raw["contract_id"],
        "materialized_hole_sha256": raw["materialized_hole_sha256"],
        "proposal_sha256": raw["proposal_sha256"],
        "corpus_id": raw["corpus_id"],
        "corpus_version": raw["corpus_version"],
        "compiler_version_sha256": hashlib.sha256(
            str(raw["compiler_version"]).encode("utf-8")
        ).hexdigest(),
        "compile_flags_sha256": raw["compile_flags_sha256"],
        "tu_sha256": raw["tu_sha256"],
        "tu_template_sha256": raw["tu_template_sha256"],
        "dependency_config_sha256": raw["dependency_config_sha256"],
        "dependency_manifest_sha256": raw["dependency_manifest_sha256"],
        "receipt_sha256": hashlib.sha256(canonical_json_bytes(raw)).hexdigest(),
    }


def _claim_key(
    *, freeze_sha256: str, holdout_id: str, configuration_id: str,
    ccbench_pin: str, env_tag: str,
) -> dict[str, str]:
    return {
        "freeze_sha256": freeze_sha256,
        "freeze_holdout_key": holdout_id,
        "configuration_id": configuration_id,
        "ccbench_pin": ccbench_pin,
        "env_tag": env_tag,
        "observation_role": "floor_campaign",
    }


def _claim_digest(key: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(dict(key))).hexdigest()


def _attempt_ids(
    *, cell_id: str, schedule: Sequence[Mapping[str, object]], retry_slots: int,
) -> list[str]:
    planned = [
        f"{cell_id}::seq{row['seq']}"
        for row in schedule if row.get("cell_id") == cell_id
    ]
    return planned + [
        f"{cell_id}::retry{ordinal}" for ordinal in range(1, retry_slots + 1)
    ]


def expected_ledger_projection_sha256(
    *, campaign_run_id: str, admission_rows: Sequence[Mapping[str, object]],
    attempt_rows: Sequence[Mapping[str, object]],
) -> str:
    """Inspector を呼ばず campaign-filtered ledger digest を独立計算する。"""

    selected_main = [
        dict(row) for row in admission_rows
        if row.get("campaign_run_id") == campaign_run_id
    ]
    selected_attempts = [
        dict(row) for row in attempt_rows
        if row.get("campaign_run_id") == campaign_run_id
    ]
    selected_main.sort(key=lambda row: (
        row["cell_id"],
        _claim_digest({
            "freeze_sha256": row["freeze_sha256"],
            "freeze_holdout_key": row["freeze_holdout_key"],
            "configuration_id": row["configuration_id"],
            "ccbench_pin": row["ccbench_pin"],
            "env_tag": row["env_tag"],
            "observation_role": row["observation_role"],
        }),
    ))
    selected_attempts.sort(key=lambda row: (
        row["cell_id"], row["attempt_id"], row["claim_digest"],
    ))
    portable_main = []
    for row in selected_main:
        assert "measurement_head" in row
        portable_main.append({
            key: value for key, value in row.items() if key != "measurement_head"
        })
    projection = {
        "schema": "s8b-floor-admission-ledger-projection/v1",
        "campaign_run_id": campaign_run_id,
        "admission_rows": portable_main,
        "attempt_rows": selected_attempts,
    }
    return hashlib.sha256(canonical_json_bytes(projection)).hexdigest()


@dataclass(frozen=True)
class FloorAdmissionEvidenceFixture:
    root: Path
    admission_rows: tuple[dict[str, object], ...]
    attempt_rows: tuple[dict[str, object], ...]
    claim_identities: dict[str, str]
    expected_receipt: dict[str, object]


def build_floor_admission_evidence(
    root: Path, *, protocol: Mapping[str, object],
    freeze: Mapping[str, object], freeze_sha256: str, manifest_sha256: str,
    campaign_run_id: str, run_relpath: str, mode: str,
    cells: Sequence[Mapping[str, object]], schedule: Sequence[Mapping[str, object]],
    sessions: Sequence[Mapping[str, object]], measurement_head: str = "1" * 40,
    irreversible_pilot_approved: bool | None = None,
    claim_schema: str = "s8b-holdout-cell-claim/v2",
    entry_kind: str = "fresh",
    nondefault_seams: Sequence[str] = (),
    resume_marker: bool = False,
) -> FloorAdmissionEvidenceFixture:
    """tmp 上へ claims/consumed/両 ledger/lock の完全な正例を構築する。"""

    if irreversible_pilot_approved is None:
        irreversible_pilot_approved = mode == "pilot"
    claims_root = root / "claims"
    consumed_root = root / "consumed"
    disqualification_root = root / "refreeze-disqualifications"
    claims_root.mkdir(parents=True)
    consumed_root.mkdir()
    disqualification_root.mkdir()
    (root / "ledger.lock").write_bytes(b"")
    protocol_sha256 = hashlib.sha256(canonical_json_bytes(dict(protocol))).hexdigest()
    holdouts = freeze["holdouts"]
    assert isinstance(holdouts, Mapping)
    retry_slots = protocol["retry_slots_per_cell"]
    assert type(retry_slots) is int

    admission_rows: list[dict[str, object]] = []
    claim_identities: dict[str, str] = {}
    cell_by_id = {str(cell["cell_id"]): cell for cell in cells}
    for cell in cells:
        cell_id = str(cell["cell_id"])
        holdout_id = str(cell["holdout_id"])
        configuration_id = str(cell["configuration_id"])
        freeze_entry = holdouts[holdout_id]
        assert isinstance(freeze_entry, Mapping)
        key = _claim_key(
            freeze_sha256=freeze_sha256, holdout_id=holdout_id,
            configuration_id=configuration_id,
            ccbench_pin=str(protocol["ccbench_pin"]), env_tag=str(protocol["env_tag"]),
        )
        digest = _claim_digest(key)
        attempt_ids = _attempt_ids(
            cell_id=cell_id, schedule=schedule, retry_slots=retry_slots,
        )
        common = {
            "freeze_candidate_id": freeze_entry["candidate_id"],
            "trial_workload_name": holdout_id,
            "cell_id": cell_id,
            "records": cell["records"],
            "threads": cell["threads"],
            "workload": dict(cell["workload"]),
        }
        claim = {
            "schema_version": claim_schema,
            "event": "claim",
            "key": key,
            "measurement_head": measurement_head,
            "protocol_sha256": protocol_sha256,
            **common,
            "campaign_run_id": campaign_run_id,
            "run_relpath": run_relpath,
            "mode": mode,
            "irreversible_pilot_approved": irreversible_pilot_approved,
            "attempt_ids": attempt_ids,
        }
        if claim_schema == "s8b-holdout-cell-claim/v2":
            claim["entry_kind"] = entry_kind
            claim["nondefault_seams"] = list(nondefault_seams)
        (claims_root / f"{digest}.claim").write_bytes(canonical_json_line(claim))
        admission_rows.append({
            "schema_version": "s8b-holdout-observation-ledger/v1",
            "event": "admit",
            **key,
            "measurement_head": measurement_head,
            "protocol_sha256": protocol_sha256,
            "manifest_sha256": manifest_sha256,
            **common,
            "campaign_run_id": campaign_run_id,
            "run_relpath": run_relpath,
            "mode": mode,
            "irreversible_pilot_approved": irreversible_pilot_approved,
            "attempt_ids": attempt_ids,
            "attempt_count": len(attempt_ids),
        })
        claim_identities[cell_id] = digest

    attempt_rows: list[dict[str, object]] = []
    for session in sessions:
        probe = session["probe_before"]
        assert isinstance(probe, Mapping)
        if probe["competing"] is True:
            continue
        cell_id = str(session["cell_id"])
        attempt_id = str(session["attempt_id"])
        cell = cell_by_id[cell_id]
        digest = claim_identities[cell_id]
        marker = {
            "schema_version": "s8b-holdout-attempt-consumption/v1",
            "event": "consume",
            "claim_digest": digest,
            "attempt_id": attempt_id,
            "campaign_run_id": campaign_run_id,
            "manifest_sha256": manifest_sha256,
            "run_relpath": run_relpath,
            "cell_id": cell_id,
            "freeze_holdout_key": cell["holdout_id"],
            "configuration_id": cell["configuration_id"],
            "observation_role": "floor_campaign",
        }
        attempt_rows.append(marker)
        marker_name = hashlib.sha256(attempt_id.encode("utf-8")).hexdigest()
        (consumed_root / f"{digest}-{marker_name}.json").write_bytes(
            canonical_json_line(marker)
        )

    (root / "ledger.jsonl").write_bytes(
        b"".join(canonical_json_line(row) for row in admission_rows)
    )
    (root / "attempt-ledger.jsonl").write_bytes(
        b"".join(canonical_json_line(row) for row in attempt_rows)
    )
    if resume_marker:
        marker = {
            "schema_version": "s8b-refreeze-disqualification/v1",
            "reason": "resume",
            "campaign_run_id": campaign_run_id,
            "run_relpath": run_relpath,
            "protocol_sha256": protocol_sha256,
            "freeze_sha256": freeze_sha256,
        }
        marker_name = hashlib.sha256(
            campaign_run_id.encode("utf-8")
        ).hexdigest()
        (disqualification_root / f"{marker_name}.json").write_bytes(
            canonical_json_line(marker)
        )
    expected_receipt = {
        "schema": "s8b-floor-holdout-admission-receipt/v1",
        "campaign_run_id": campaign_run_id,
        "run_relpath": run_relpath,
        "mode": mode,
        "protocol_sha256": protocol_sha256,
        "freeze_sha256": freeze_sha256,
        "manifest_sha256": manifest_sha256,
        "claim_identities": dict(sorted(claim_identities.items())),
        "admission_row_count": len(admission_rows),
        "attempt_row_count": len(attempt_rows),
        "ledger_projection_sha256": expected_ledger_projection_sha256(
            campaign_run_id=campaign_run_id, admission_rows=admission_rows,
            attempt_rows=attempt_rows,
        ),
    }
    return FloorAdmissionEvidenceFixture(
        root=root, admission_rows=tuple(admission_rows),
        attempt_rows=tuple(attempt_rows), claim_identities=claim_identities,
        expected_receipt=expected_receipt,
    )
