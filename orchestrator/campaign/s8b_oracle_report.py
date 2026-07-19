# -*- coding: utf-8 -*-
"""8b oracle session WAL を全 schedule 行の observations へ射影する。"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
ROOT = _ORCHESTRATOR.parent
sys.path.insert(0, str(_ORCHESTRATOR))

from campaign import env_attestation, env_contract  # noqa: E402
from campaign import execution_guard, s8b_oracle_manifest, wal  # noqa: E402
from campaign import s8b_oracle_artifacts as _artifacts  # noqa: E402
from campaign import s8b_abort_reason_contract as _abort_reason_contract  # noqa: E402
from campaign import s8b_experiment_numbers as _experiment_numbers  # noqa: E402
from campaign import s8b_outcome_stage_contract as _outcome_stage_contract  # noqa: E402
from campaign.layout import campaign_layout  # noqa: E402


SCHEMA_VERSION = _artifacts.OFFICIAL_OBSERVATIONS_SCHEMA
SESSION_STAGE = "s8b-oracle-session"
OUTCOMES = _outcome_stage_contract.OUTCOMES
# C3-5: bench-binary-mismatch abort が射影される terminal outcome の abort reason。
# build_done 後・trace/bench 起動前に発火するため build/verify/bench 証拠のどれにも
# 適合しない。段階証拠は outcome stage contract leaf、固定 reason はここで検査する。
BINARY_MISMATCH_REASON = "bench-binary-mismatch"
PIPELINE_STAGES = _outcome_stage_contract.PIPELINE_STAGES
EVENT_KEYS = {
    "campaign-start": {"manifest_sha256", "block_id", "campaign_id"},
    "trial-start": {"schedule_index", "holdout_id", "configuration_id", "attempt"},
    "trial-result": {"schedule_index", "holdout_id", "configuration_id", "attempt",
                     "outcome", "excluded_reason", "screen_outcome"},
    "retry": {"schedule_index", "attempt", "reason"},
    "trial-skipped": {"schedule_index", "reason"},
    "budget-refused": {"schedule_index", "reason"},
    "binding-refused": {"schedule_index", "reason"},
    "deviation": {"message"},
    "campaign-terminal": {
        "status", "scheduled_rows", "completed_rows", "execution_identity",
    },
}
_EXECUTION_IDENTITY_KEYS = {"job", "host", "boot", "pid", "starttime"}


class ReportError(ValueError):
    """manifest または WAL が report 契約を満たさない。"""


def _reject_exploration_output_root(output_root: Path) -> None:
    """realpath 後の namespace marker を検査し official/exploration 混同を拒否する。"""
    try:
        resolved = Path(output_root).resolve()
    except OSError as exc:
        raise ReportError("output_root を解決できない") from exc
    marker = resolved / "namespace.json"
    if marker.is_symlink():
        raise ReportError("output_root namespace marker が symlink")
    if not marker.exists():
        return
    try:
        document = _artifacts.strict_load_json_object(marker)
    except _artifacts.OracleArtifactTypeError as exc:
        raise ReportError(f"output_root namespace marker が不正: {exc}") from exc
    if document == {"namespace": "exploration"}:
        raise ReportError("exploration namespace を official report output_root に指定できない")
    raise ReportError("output_root namespace marker が official namespace と一致しない")


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _canonical_sha256(value: Mapping) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_manifest(
        manifest: Mapping,
) -> tuple[list[Mapping], set[str], str, int, int, list[str]]:
    if not isinstance(manifest, Mapping):
        raise ReportError("manifest は object でなければならない")
    missing = [key for key in ("campaign_ids", "schedule", "allowed_excluded_reasons")
               if key not in manifest]
    if missing:
        raise ReportError(f"manifest の必須キーがない: {', '.join(missing)}")
    raw_schedule = manifest["schedule"]
    schedule_n = None
    if isinstance(raw_schedule, Mapping):
        schedule_n = raw_schedule.get("n")
        raw_schedule = raw_schedule.get("rows")
    if (not isinstance(raw_schedule, Sequence)
            or isinstance(raw_schedule, (str, bytes, bytearray))):
        raise ReportError("manifest.schedule は array でなければならない")
    schedule = list(raw_schedule)
    if any(not isinstance(row, Mapping) for row in schedule):
        raise ReportError("manifest.schedule の各行は object でなければならない")
    allowed = manifest["allowed_excluded_reasons"]
    if (not isinstance(allowed, Sequence) or isinstance(allowed, (str, bytes, bytearray))
            or any(not isinstance(item, str) or not item for item in allowed)
            or len(set(allowed)) != len(allowed)):
        raise ReportError("allowed_excluded_reasons は重複のない非空文字列の array でなければならない")
    n = manifest.get("n_per_cell", schedule_n)
    if not _is_int(n) or n < 1:
        raise ReportError("manifest.n_per_cell は 1 以上の整数でなければならない")
    supplied_sha = manifest.get("manifest_sha256")
    if supplied_sha is not None and (not isinstance(supplied_sha, str) or not supplied_sha):
        raise ReportError("manifest_sha256 は非空文字列でなければならない")
    try:
        manifest_sha = s8b_oracle_manifest.manifest_sha256(manifest)
    except s8b_oracle_manifest.ManifestError as exc:
        raise ReportError(f"manifest canonical hash を再計算できない: {exc}") from exc
    expected_reps = _experiment_numbers.APPROVED_REPS
    run_contract_issues: list[str] = []
    if "run_contract" in manifest:
        run_contract = manifest["run_contract"]
        if not isinstance(run_contract, Mapping):
            run_contract_issues.append("manifest.run_contract が object でない")
        else:
            declared_reps = run_contract.get("reps")
            if not _is_int(declared_reps) or declared_reps <= 0:
                run_contract_issues.append(
                    "manifest.run_contract.reps が非 bool の正整数でない")
            elif declared_reps != expected_reps:
                run_contract_issues.append(
                    "manifest.run_contract.reps が APPROVED_REPS と不一致: "
                    f"actual={declared_reps}, expected={expected_reps}")
    return (schedule, set(allowed), manifest_sha, n, expected_reps,
            run_contract_issues)


def _campaign_index(raw: object) -> tuple[dict[str, str], set[str]]:
    by_block: dict[str, str] = {}
    ids: set[str] = set()
    if isinstance(raw, Mapping):
        for block, value in raw.items():
            campaign_id = value.get("campaign_id") if isinstance(value, Mapping) else value
            if not isinstance(block, str) or not isinstance(campaign_id, str) or not campaign_id:
                raise ReportError("campaign_ids mapping の block/campaign_id が不正")
            by_block[block] = campaign_id
            ids.add(campaign_id)
    elif (isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray))):
        for value in raw:
            if isinstance(value, str) and value:
                ids.add(value)
            elif isinstance(value, Mapping):
                block = value.get("block_id")
                campaign_id = value.get("campaign_id")
                if not isinstance(block, str) or not isinstance(campaign_id, str) or not campaign_id:
                    raise ReportError("campaign_ids entry の block_id/campaign_id が不正")
                by_block[block] = campaign_id
                ids.add(campaign_id)
            else:
                raise ReportError("campaign_ids は文字列または object の array でなければならない")
    else:
        raise ReportError("campaign_ids は mapping または array でなければならない")
    if not ids:
        raise ReportError("campaign_ids が空")
    return by_block, ids


def _campaign_for_row(row: Mapping, by_block: Mapping[str, str], ids: set[str]) -> str:
    block_id = row.get("block_id")
    direct = row.get("campaign_id")
    if direct is not None:
        if not isinstance(direct, str) or direct not in ids:
            raise ReportError("schedule.campaign_id が manifest.campaign_ids 外")
        if isinstance(block_id, str) and block_id in by_block and by_block[block_id] != direct:
            raise ReportError("schedule の block_id と campaign_id の対応が不一致")
        return direct
    if isinstance(block_id, str) and block_id in by_block:
        return by_block[block_id]
    if len(ids) == 1:
        return next(iter(ids))
    raise ReportError("schedule 行を campaign_id に束縛できない")


def _base_row(item: Mapping) -> dict:
    index = item.get("schedule_index")
    block = item.get("block_id")
    holdout = item.get("holdout_id")
    configuration = item.get("configuration_id")
    if not _is_int(index) or index < 0:
        raise ReportError(f"schedule_index が非負整数でない: {index!r}")
    if not all(isinstance(value, str) and value
               for value in (block, holdout, configuration)):
        raise ReportError(f"schedule_index={index} の block/holdout/configuration が不正")
    attempt = item.get("attempt", 1)
    if not _is_int(attempt) or attempt < 0:
        raise ReportError(f"schedule_index={index} の attempt が不正")
    return {
        "schedule_index": index, "block_id": block, "holdout_id": holdout,
        "configuration_id": configuration, "attempt": attempt,
        "status": "not-started", "outcome": None, "binding_ok": False,
        "legacy_verify": "missing", "s2_verify": "missing", "bench_values": [],
        "excluded_reason": None, "screen_outcome": "not_enabled",
        "attempt_verify_outcomes": [],
        "reason": "trial-start がない",
    }


def _session_event(record: object, event: Optional[str] = None) -> bool:
    payload = getattr(record, "payload", None)
    return (getattr(record, "stage", None) == SESSION_STAGE
            and isinstance(payload, Mapping)
            and (event is None or payload.get("event") == event))


def _event_contract_issues(payload: Mapping) -> list[str]:
    event = payload.get("event")
    if not isinstance(event, str) or event not in EVENT_KEYS:
        return [f"未知の session event: {event!r}"]
    missing = sorted(EVENT_KEYS[event] - set(payload))
    issues = [f"session event {event} の必須キーがない: {','.join(missing)}"] if missing else []
    if event in {"trial-start", "trial-result", "retry", "trial-skipped",
                 "budget-refused", "binding-refused"}:
        if not _is_int(payload.get("schedule_index")) or payload["schedule_index"] < 0:
            issues.append(f"session event {event}.schedule_index が非負整数でない")
    if event in {"trial-start", "trial-result", "retry"}:
        if not _is_int(payload.get("attempt")) or payload["attempt"] < 0:
            issues.append(f"session event {event}.attempt が非負整数でない")
    for key in EVENT_KEYS[event] & {"manifest_sha256", "block_id", "campaign_id",
                                   "holdout_id", "configuration_id", "reason", "message"}:
        if not isinstance(payload.get(key), str) or not payload[key]:
            issues.append(f"session event {event}.{key} が非空文字列でない")
    if event == "campaign-terminal":
        expected_keys = {"event", *EVENT_KEYS[event]}
        if set(payload) != expected_keys:
            issues.append("campaign-terminal の top-level key 集合が不正")
        if payload.get("status") not in {"completed", "aborted"}:
            issues.append("campaign-terminal.status が completed/aborted でない")
        for key in ("scheduled_rows", "completed_rows"):
            if not _is_int(payload.get(key)) or payload[key] < 0:
                issues.append(f"campaign-terminal.{key} が非負整数でない")
        identity = payload.get("execution_identity")
        if not isinstance(identity, Mapping) or set(identity) != _EXECUTION_IDENTITY_KEYS:
            issues.append("campaign-terminal.execution_identity の key 集合が不正")
        else:
            for key in ("job", "host", "boot"):
                if not isinstance(identity[key], str) or not identity[key]:
                    issues.append(f"campaign-terminal.execution_identity.{key} が不正")
            for key in ("pid", "starttime"):
                if not _is_int(identity[key]) or identity[key] <= 0:
                    issues.append(f"campaign-terminal.execution_identity.{key} が不正")
    return issues


def _trial_windows(records: Sequence[object]) -> list[list[object]]:
    starts = [i for i, record in enumerate(records) if _session_event(record, "trial-start")]
    windows: list[list[object]] = []
    for pos, start in enumerate(starts):
        stop = starts[pos + 1] if pos + 1 < len(starts) else len(records)
        windows.append(list(records[start:stop]))
    return windows


def _screen_marker(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower().replace("_", "-")
            if normalized != "screen-outcome" and (
                    normalized in {"screen", "screening", "screened"}
                    or normalized.startswith("screen-reject")
                    or normalized.startswith("screening-disabled")):
                return True
            if _screen_marker(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_screen_marker(item) for item in value)
    return False


def _binding_entry(manifest: Mapping, holdout: str, configuration: str) -> Optional[Mapping]:
    """並行実装中 manifest の list/mapping 形の binding identity を疎結合で読む。"""
    for key in ("binding_identities", "bindings", "binding_identity"):
        raw = manifest.get(key)
        if isinstance(raw, Mapping) and isinstance(raw.get("entries"), Sequence):
            raw = raw["entries"]
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
            for entry in raw:
                if (isinstance(entry, Mapping) and entry.get("holdout_id") == holdout
                        and entry.get("configuration_id") == configuration):
                    return entry
        if isinstance(raw, Mapping):
            nested = raw.get(holdout)
            if isinstance(nested, Mapping) and isinstance(nested.get(configuration), Mapping):
                return nested[configuration]
            for composite in (f"{holdout}:{configuration}", f"{holdout}/{configuration}"):
                if isinstance(raw.get(composite), Mapping):
                    return raw[composite]
    return None


_BINDING_KEYS = {
    "holdout_id", "configuration_id", "entry_sha256", "genome_canonical",
    "src_token", "variant_id", "binding_sha256",
}


def _binding_schema_issues(entry: object, *, holdout: str,
                           configuration: str) -> list[str]:
    if not isinstance(entry, Mapping):
        return ["manifest.binding_identity に expected cell がない"]
    if set(entry) != _BINDING_KEYS:
        return ["manifest.binding_identity の必須 identity field が完全でない"]
    issues = []
    if entry.get("holdout_id") != holdout or entry.get("configuration_id") != configuration:
        issues.append("manifest.binding_identity の cell identity が不一致")
    for key in ("entry_sha256", "src_token", "variant_id", "binding_sha256"):
        if not isinstance(entry.get(key), str) or not entry[key]:
            issues.append(f"binding.{key} が非空文字列でない")
    for key in ("entry_sha256", "binding_sha256"):
        value = entry.get(key)
        if (isinstance(value, str) and value
                and (len(value) != 64
                     or any(ch not in "0123456789abcdef" for ch in value))):
            issues.append(f"binding.{key} が SHA-256 でない")
    genome = entry.get("genome_canonical")
    if not ((isinstance(genome, str) and genome) or isinstance(genome, Mapping)):
        issues.append("binding.genome_canonical が非空文字列/object でない")
    if not issues:
        projected = {
            "genome_canonical": genome,
            "src_token": entry["src_token"],
            "variant_id": entry["variant_id"],
            "entry_sha256": entry["entry_sha256"],
        }
        if entry["binding_sha256"] != _canonical_sha256(projected):
            issues.append("binding.binding_sha256 が identity 再計算値と不一致")
    return issues


def _verify_state(records: Sequence[object], tag: str) -> tuple[str, list[str]]:
    matches = []
    for record in records:
        if (getattr(record, "stage", None) != "verify_done"
                or not isinstance(getattr(record, "payload", None), Mapping)):
            continue
        workload = record.payload.get("workload")
        if isinstance(workload, Mapping) and workload.get("tag") == tag:
            matches.append(record)
    if not matches:
        return "missing", []
    if len(matches) != 1:
        return "missing", [f"verify_done[{tag}] が一意でない: {len(matches)}"]
    certified = matches[0].payload.get("certified")
    if certified is True:
        return "pass", []
    if certified is False:
        return "red", []
    return "missing", [f"verify_done[{tag}].certified が bool でない"]


def _safe_payload(record: object) -> Mapping:
    payload = getattr(record, "payload", None)
    return payload if isinstance(payload, Mapping) else {}


def _pipeline_payload_issues(records: Sequence[object]) -> dict[int, str]:
    """全 pipeline record の payload 型違反を record identity へ束縛する。"""
    issues: dict[int, str] = {}
    ordinal = 0
    for record in records:
        stage = getattr(record, "stage", None)
        if not isinstance(stage, str) or stage not in _outcome_stage_contract.PIPELINE_STAGES:
            continue
        if not isinstance(getattr(record, "payload", None), Mapping):
            issues[id(record)] = f"pipeline[{ordinal}] {stage}.payload が object でない"
        ordinal += 1
    return issues


def _verify_evidence(record: object) -> tuple[str, str]:
    payload = _safe_payload(record)
    workload = payload.get("workload")
    tag = workload.get("tag") if isinstance(workload, Mapping) else None
    workload_state = tag if isinstance(tag, str) else "invalid"
    certified = payload.get("certified")
    verify_state = "pass" if certified is True else "red" if certified is False else "invalid"
    return workload_state, verify_state


def _abort_workload_evidence(abort_records: Sequence[object]) -> tuple[str, list[str]]:
    if not abort_records:
        return "absent", []
    if len(abort_records) != 1:
        return "invalid", []
    payload = _safe_payload(abort_records[0])
    if "workload" not in payload:
        return "absent", []
    workload = payload["workload"]
    if (not isinstance(workload, Mapping) or set(workload) != {"tag"}
            or workload.get("tag") not in {"legacy", "s2"}):
        return "invalid", [
            "abort.workload は exact {tag: legacy|s2} object でなければならない"
        ]
    return str(workload["tag"]), []


def _assess_window(item: Mapping, window: Sequence[object], manifest: Mapping,
                   allowed_excluded: set[str], expected_reps: int,
                   payload_issues: Sequence[str] = ()) -> dict:
    row = _base_row(item)
    start = window[0].payload
    results = [record.payload for record in window if _session_event(record, "trial-result")]
    issues: list[str] = []
    identity = ("schedule_index", "holdout_id", "configuration_id", "attempt")
    for key in identity:
        if key == "attempt" and key not in item:
            continue
        expected = item.get(key)
        if start.get(key) != expected:
            issues.append(f"trial-start.{key} が schedule と不一致")
    if len(results) != 1:
        issues.append(f"trial-result が一意でない: {len(results)}")
        result: Mapping = results[-1] if results else {}
    else:
        result = results[0]
    for key in identity:
        if result.get(key) != start.get(key):
            issues.append(f"trial-result.{key} が trial-start と不一致")

    outcome = result.get("outcome")
    excluded = result.get("excluded_reason")
    screen_outcome = result.get("screen_outcome")
    if (not isinstance(outcome, str)
            or outcome not in _outcome_stage_contract.OUTCOMES):
        issues.append(f"trial-result.outcome が不正: {outcome!r}")
        outcome = None
    if excluded is not None and (
            not isinstance(excluded, str) or excluded not in allowed_excluded):
        issues.append(f"excluded_reason が許可一覧外: {excluded!r}")
    if outcome == "correctness-red" and excluded is not None:
        issues.append("correctness-red に excluded_reason が指定されている")
    if screen_outcome != "not_enabled":
        issues.append(f"screen_outcome が not_enabled でない: {screen_outcome!r}")

    pipeline_records = [record for record in window
                        if isinstance(getattr(record, "stage", None), str)
                        and record.stage in _outcome_stage_contract.PIPELINE_STAGES]
    issues.extend(payload_issues)
    if any(_screen_marker(record.payload) for record in pipeline_records):
        issues.append("screening=off の trial 区間に screen marker がある")
    variant_values = [record.variant for record in pipeline_records]
    variants = {variant for variant in variant_values if isinstance(variant, str)}
    builds = [record for record in pipeline_records if record.stage == "build_start"]
    binding_ok = (len(variants) == 1
                  and all(isinstance(variant, str) for variant in variant_values)
                  and len(builds) == 1)
    if not binding_ok:
        issues.append("trial 区間の pipeline variant/build_start が一意でない")
    expected_binding = _binding_entry(
        manifest, row["holdout_id"], row["configuration_id"])
    binding_reasons = _binding_schema_issues(
        expected_binding, holdout=row["holdout_id"],
        configuration=row["configuration_id"],
    )
    if binding_reasons:
        binding_ok = False
    if binding_ok:
        build = builds[0]
        build_payload = _safe_payload(build)
        checks = (
            ("variant_id", build.variant),
            ("src_token", build_payload.get("src_token")),
            ("genome_canonical", build_payload.get("genome")),
        )
        for key, actual in checks:
            if expected_binding[key] != actual:
                binding_reasons.append(f"binding.{key} が build_start と不一致")
        if binding_reasons:
            binding_ok = False
    issues.extend(binding_reasons)

    legacy, legacy_issues = _verify_state(pipeline_records, "legacy")
    s2, s2_issues = _verify_state(pipeline_records, "s2")
    issues.extend(legacy_issues)
    issues.extend(s2_issues)
    for record in pipeline_records:
        if record.stage != "verify_done":
            continue
        payload = _safe_payload(record)
        workload = payload.get("workload")
        tag = workload.get("tag") if isinstance(workload, Mapping) else None
        if not isinstance(tag, str) or tag not in {"legacy", "s2"}:
            issues.append("verify_done.workload.tag が legacy/s2 でない")
    benches = [record for record in pipeline_records if record.stage == "bench_done"]
    bench_values: list[float] = []
    if len(benches) > 1:
        issues.append(f"bench_done が一意でない: {len(benches)}")
    elif len(benches) == 1:
        raw_values = _safe_payload(benches[0]).get("tps")
        if (not isinstance(raw_values, Sequence)
                or isinstance(raw_values, (str, bytes, bytearray)) or not raw_values
                or any(isinstance(value, bool) or not isinstance(value, (int, float))
                       or not math.isfinite(float(value)) for value in raw_values)):
            issues.append("bench_done.tps が空または非有限値を含む")
        elif len(raw_values) != expected_reps:
            issues.append(
                "bench_done.tps 件数が official reps と不一致: "
                f"actual={len(raw_values)}, expected={expected_reps}")
        else:
            bench_values = [float(value) for value in raw_values]

    counts = {stage: sum(record.stage == stage for record in pipeline_records)
              for stage in _outcome_stage_contract.PIPELINE_STAGES}
    abort_records = [record for record in pipeline_records if record.stage == "abort"]
    if counts["build_start"] != 1:
        issues.append(f"build_start が一意でない: {counts['build_start']}")
    if counts["abort"] > 1 or counts["commit"] > 1:
        issues.append("terminal pipeline event が重複")
    positions = [PIPELINE_ORDER.get(record.stage, 2) for record in pipeline_records]
    if positions != sorted(positions):
        issues.append("pipeline event の物理順序が不正")

    abort_workload, abort_workload_issues = _abort_workload_evidence(abort_records)
    issues.extend(abort_workload_issues)
    verify_sequence = tuple(
        _verify_evidence(record) for record in pipeline_records
        if record.stage == "verify_done"
    )
    stage_evidence = _outcome_stage_contract.StageEvidence(
        build_start=counts["build_start"],
        build_done=counts["build_done"],
        verify_sequence=verify_sequence,
        bench_done=counts["bench_done"],
        abort=counts["abort"],
        commit=counts["commit"],
        abort_workload=abort_workload,
    )
    if not _outcome_stage_contract.matches(outcome, stage_evidence):
        issues.append(
            "trial-result.outcome と段階証拠が一致しない: "
            f"outcome={outcome!r}, evidence={stage_evidence!r}")

    abort_reason = (
        _safe_payload(abort_records[0]).get("reason")
        if len(abort_records) == 1 else None
    )
    if outcome == "correctness-red":
        red_records = [
            record for record in pipeline_records
            if record.stage == "verify_done"
            and _safe_payload(record).get("certified") is False
        ]
        red_verdict = (
            _safe_payload(red_records[0]).get("verdict")
            if len(red_records) == 1 else None
        )
        if (len(red_records) != 1 or not isinstance(red_verdict, str)
                or not red_verdict or abort_reason != red_verdict):
            issues.append(
                "correctness-red 宣言と sole red verify verdict/abort reason 連鎖が一致しない")
    elif outcome == "build-failed":
        if not (
                len(abort_records) == 1
                and isinstance(abort_reason, str)
                and abort_reason
                in _abort_reason_contract.BUILD_FAILED_ABORT_REASONS):
            issues.append("build-failed 宣言と abort reason 証拠が一致しない")
    elif outcome in {"timeout", "bench-failed"}:
        allowed_reasons = {
            "timeout": _abort_reason_contract.TIMEOUT_ABORT_REASONS,
            "bench-failed": _abort_reason_contract.BENCH_FAILED_ABORT_REASONS,
        }[outcome]
        if not (
                len(abort_records) == 1
                and isinstance(abort_reason, str)
                and abort_reason in allowed_reasons):
            issues.append(f"{outcome} 宣言と abort reason 証拠が一致しない")
    elif outcome == "binary-mismatch":
        if abort_reason != BINARY_MISMATCH_REASON:
            issues.append("binary-mismatch 宣言と固定 abort reason 証拠が一致しない")
    elif outcome == "verify-inconclusive":
        if (not isinstance(abort_reason, str)
                or abort_reason
                not in _abort_reason_contract.VERIFY_INCONCLUSIVE_ABORT_REASONS):
            issues.append(
                "verify-inconclusive 宣言と missing verify/abort 証拠が一致しない")

    row.update(
        attempt=start.get("attempt", row["attempt"]), status="completed", outcome=outcome,
        binding_ok=binding_ok, legacy_verify=legacy, s2_verify=s2,
        bench_values=bench_values, excluded_reason=excluded,
        screen_outcome=screen_outcome if isinstance(screen_outcome, str) else "not_enabled",
        attempt_verify_outcomes=[{
            "attempt": start.get("attempt", row["attempt"]),
            "status": "protocol_violation" if issues else "completed",
            "outcome": outcome,
            "binding_ok": binding_ok,
            "legacy_verify": legacy,
            "s2_verify": s2,
        }],
        reason="; ".join(binding_reasons) if binding_reasons else None,
    )
    if issues:
        row["status"] = "protocol_violation"
        row["reason"] = "; ".join(dict.fromkeys([*binding_reasons, *issues]))
    return row


PIPELINE_ORDER = {
    "build_start": 0, "build_done": 1, "verify_done": 2,
    "bench_done": 3, "abort": 4, "commit": 4,
}


def _receipt_expectations(manifest: Mapping):
    """manifest run_contract から env contract と verified calibration を導出する。

    run_contract を持たない (legacy) manifest では None を返し receipt 検査を課さない。
    v2 (env_tag + contract_sha256 が揃う) manifest でのみ receipt 照合を発火させる。"""
    run_contract = manifest.get("run_contract") if isinstance(manifest, Mapping) else None
    if not isinstance(run_contract, Mapping):
        return None
    env_tag = run_contract.get("env_tag")
    contract_sha256 = run_contract.get("contract_sha256")
    if (isinstance(env_tag, str) and env_tag
            and isinstance(contract_sha256, str) and contract_sha256):
        try:
            contract = env_contract.lookup(env_tag)
            if contract.contract_sha256 != contract_sha256:
                raise ReportError("manifest contract_sha256 が registry contract と不一致")
            verified = env_attestation.load_verified_calibration(contract, ROOT)
        except (env_contract.EnvContractError, env_attestation.AttestationError) as exc:
            raise ReportError(f"manifest env contract を検証できない: {exc}") from exc
        return contract, verified
    return None


def _campaign_terminal_issue(records: Sequence[object], rows: Sequence[Mapping]) -> Optional[str]:
    """all-or-nothing 公開 gate。未完 campaign の理由を返す。"""
    terminals = [record.payload for record in records
                 if _session_event(record, "campaign-terminal")]
    if len(terminals) != 1:
        return f"campaign-terminal が一意でない: {len(terminals)}"
    terminal = terminals[0]
    schema_issues = _event_contract_issues(terminal)
    if schema_issues:
        return "; ".join(schema_issues)
    if terminal.get("status") != "completed":
        return f"campaign-terminal.status={terminal.get('status')!r}"
    scheduled = len(rows)
    if terminal.get("scheduled_rows") != scheduled:
        return "campaign-terminal.scheduled_rows が manifest campaign 行数と不一致"
    if terminal.get("completed_rows") != scheduled:
        return "campaign-terminal.completed_rows が manifest campaign 行数と不一致"
    results = [record.payload for record in records if _session_event(record, "trial-result")]
    actual_indices = [payload.get("schedule_index") for payload in results]
    expected_indices = [row.get("schedule_index") for row in rows]
    if (any(not _is_int(index) for index in actual_indices)
            or not set(expected_indices).issubset(set(actual_indices))):
        return "campaign-terminal completed だが trial-result の全 schedule 被覆がない"
    return None


def _assess_campaign(rows: Sequence[Mapping], campaign_id: str, manifest: Mapping,
                     manifest_sha: str, allowed_excluded: set[str], output_root: Path,
                     expected_reps: int,
                     manifest_issues: Sequence[str]) -> list[dict]:
    bases = [_base_row(item) for item in rows]
    try:
        layout = campaign_layout(campaign_id, output_root=str(output_root))
    except ValueError as exc:
        return [{**base, "status": "protocol_violation", "reason": str(exc)} for base in bases]
    root = Path(layout.root)
    if not root.is_dir():
        return [{**base, "status": "campaign-incomplete", "bench_values": [],
                 "reason": f"campaign-terminal がない (campaign directory 欠落): {campaign_id}"}
                for base in bases]
    try:
        records = wal.read_records(layout)
    except Exception as exc:
        return [{**base, "status": "protocol_violation",
                 "reason": f"WAL を読めない: {type(exc).__name__}: {exc}"}
                for base in bases]

    payload_issue_by_record = _pipeline_payload_issues(records)
    windows = _trial_windows(records)
    payload_issues_by_index: dict[int, list[str]] = {}
    attributed_payload_issue_ids: set[int] = set()
    for window in windows:
        index = window[0].payload.get("schedule_index")
        if not _is_int(index):
            continue
        window_issues = [
            payload_issue_by_record[id(record)] for record in window
            if id(record) in payload_issue_by_record
        ]
        if window_issues:
            payload_issues_by_index.setdefault(index, []).extend(window_issues)
            attributed_payload_issue_ids.update(
                id(record) for record in window
                if id(record) in payload_issue_by_record
            )
    unbound_payload_issues = [
        issue for record_id, issue in payload_issue_by_record.items()
        if record_id not in attributed_payload_issue_ids
    ]

    terminal_issue = _campaign_terminal_issue(records, rows)
    if terminal_issue is not None:
        output = []
        for item, base in zip(rows, bases):
            payload_issues = [
                *unbound_payload_issues,
                *payload_issues_by_index.get(item["schedule_index"], ()),
            ]
            if payload_issues:
                output.append({
                    **base, "status": "protocol_violation", "bench_values": [],
                    "reason": "; ".join(dict.fromkeys(payload_issues)),
                })
            else:
                output.append({
                    **base, "status": "campaign-incomplete", "bench_values": [],
                    "reason": terminal_issue,
                })
        return output

    campaign_starts = [record.payload for record in records
                       if _session_event(record, "campaign-start")]
    global_issues: list[str] = list(manifest_issues)
    global_issues.extend(unbound_payload_issues)
    if len(campaign_starts) != 1:
        global_issues.append(f"campaign-start が一意でない: {len(campaign_starts)}")
    else:
        start = campaign_starts[0]
        block_ids = {item.get("block_id") for item in rows}
        if start.get("manifest_sha256") != manifest_sha:
            global_issues.append("campaign-start.manifest_sha256 が manifest と不一致")
        if start.get("campaign_id") != campaign_id:
            global_issues.append("campaign-start.campaign_id が manifest と不一致")
        if len(block_ids) != 1 or start.get("block_id") not in block_ids:
            global_issues.append("campaign-start.block_id が schedule と不一致")
        # C3-10: manifest が v2 run_contract (env_tag + contract_sha256) を宣言する場合、
        # campaign-start の execution_receipt が env_tag/contract_sha256 と一致し、実行機
        # attestation を持つことを要求する (受理が恒真にならないよう存在と一致を両方検査)。
        try:
            expectations = _receipt_expectations(manifest)
        except ReportError as exc:
            global_issues.append(str(exc))
            expectations = None
        if expectations is not None:
            contract, verified = expectations
            if not execution_guard.receipt_matches_contract(
                    start.get("execution_receipt"),
                    env_tag=contract.env_tag,
                    contract_sha256=contract.contract_sha256,
                    attestation_mode=contract.attestation_mode,
                    verified_calibration=(verified if contract.attestation_mode == "required"
                                          else None)):
                global_issues.append(
                    "campaign-start.execution_receipt が manifest run_contract の "
                    "env_tag/contract_sha256/attestation と不一致 (または欠落)")
    for record in records:
        if _session_event(record):
            event = record.payload.get("event")
            global_issues.extend(_event_contract_issues(record.payload))
            if event == "deviation":
                global_issues.append(f"deviation: {record.payload.get('message')!r}")
    first_trial = next((index for index, record in enumerate(records)
                        if _session_event(record, "trial-start")), len(records))
    if any(isinstance(record.stage, str)
           and record.stage in _outcome_stage_contract.PIPELINE_STAGES
           for record in records[:first_trial]):
        global_issues.append("trial-start より前に未束縛の pipeline event がある")

    windows_by_index: dict[int, list[list[object]]] = {}
    for window in windows:
        index = window[0].payload.get("schedule_index")
        if _is_int(index):
            windows_by_index.setdefault(index, []).append(window)
    schedule_indices = {item["schedule_index"] for item in rows}
    orphan_indices = sorted(index for index in windows_by_index
                            if index not in schedule_indices)
    if orphan_indices:
        global_issues.append(
            f"trial-start.schedule_index が schedule 外: {orphan_indices!r}")
    output: list[dict] = []
    for item, base in zip(rows, bases):
        row_payload_issues = payload_issues_by_index.get(item["schedule_index"], [])
        if global_issues:
            reasons = [*row_payload_issues, *global_issues]
            output.append({**base, "status": "protocol_violation",
                           "reason": "; ".join(dict.fromkeys(reasons))})
            continue
        windows = windows_by_index.get(item["schedule_index"], [])
        if not windows:
            output.append(base)
            continue
        attempts = [window[0].payload.get("attempt") for window in windows]
        if (any(not _is_int(attempt) or attempt < 0 for attempt in attempts)
                or len(attempts) != len(set(attempts))):
            output.append({**base, "status": "protocol_violation",
                           "reason": f"trial attempt が不正または重複: {attempts!r}"})
            continue
        assessed = [
            _assess_window(
                item, window, manifest, allowed_excluded, expected_reps,
                [payload_issue_by_record[id(record)] for record in window
                 if id(record) in payload_issue_by_record],
            )
            for window in sorted(windows, key=lambda window: window[0].payload["attempt"])
        ]
        outcomes = [summary for row in assessed
                    for summary in row["attempt_verify_outcomes"]]
        definitive_reds = [
            row for row in assessed
            if row["status"] == "completed"
            and row["binding_ok"] is True
            and row["outcome"] == "correctness-red"
            and "red" in (row["legacy_verify"], row["s2_verify"])
        ]
        if definitive_reds:
            chosen = definitive_reds[-1]
        else:
            chosen = assessed[-1]
            invalid_attempts = [row for row in assessed if row["status"] != "completed"]
            if invalid_attempts and chosen["status"] == "completed":
                chosen = dict(chosen)
                chosen["status"] = "protocol_violation"
                chosen["reason"] = "; ".join(dict.fromkeys(
                    str(row.get("reason") or "過去 attempt が protocol_violation")
                    for row in invalid_attempts
                ))
        chosen = dict(chosen)
        chosen["attempt_verify_outcomes"] = outcomes
        output.append(chosen)
    return output


def build_observations(
    *, manifest: _artifacts.OfficialManifest | _artifacts.LegacyManifest,
    output_root: Path,
) -> _artifacts.OfficialObservations:
    """manifest 所有 campaign だけから JSON-safe な全件 observations を作る。"""
    if type(manifest) not in {_artifacts.OfficialManifest, _artifacts.LegacyManifest}:
        raise _artifacts.OracleArtifactTypeError(
            "build_observations は OfficialManifest/LegacyManifest exact type のみ受理する")
    _reject_exploration_output_root(Path(output_root))
    manifest_kind = (
        "official" if type(manifest) is _artifacts.OfficialManifest else "legacy"
    )
    (schedule, allowed_excluded, manifest_sha, n, expected_reps,
     manifest_issues) = _validate_manifest(manifest)
    by_block, campaign_ids = _campaign_index(manifest["campaign_ids"])
    grouped: dict[str, list[tuple[int, Mapping]]] = {
        campaign_id: [] for campaign_id in campaign_ids}
    detached: list[tuple[int, Mapping, str]] = []
    for ordinal, item in enumerate(schedule):
        try:
            campaign_id = _campaign_for_row(item, by_block, campaign_ids)
        except ReportError as exc:
            detached.append((ordinal, item, str(exc)))
            continue
        grouped[campaign_id].append((ordinal, item))
    by_ordinal: dict[int, dict] = {}
    for campaign_id in sorted(grouped):
        if grouped[campaign_id]:
            ordinals, items = zip(*grouped[campaign_id])
            assessed = _assess_campaign(items, campaign_id, manifest, manifest_sha,
                                        allowed_excluded, Path(output_root),
                                        expected_reps, manifest_issues)
            for ordinal, row in zip(ordinals, assessed):
                by_ordinal[ordinal] = row
    for ordinal, item, reason in detached:
        base = _base_row(item)
        base.update(status="protocol_violation", reason=reason)
        by_ordinal[ordinal] = base
    rows = [by_ordinal[ordinal] for ordinal in range(len(schedule))]
    expected_cells = [{
        "schedule_index": item["schedule_index"],
        "holdout_id": item["holdout_id"],
        "configuration_id": item["configuration_id"],
    } for item in schedule]
    return _artifacts.OfficialObservations({
        "schema_version": SCHEMA_VERSION,
        "manifest_kind": manifest_kind,
        "manifest_sha256": manifest_sha,
        "n_per_cell": n,
        "expected_cells": expected_cells,
        "rows": rows,
    })


def _write_create_only(path: Path, value: Mapping) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    report = sub.add_parser("report", help="manifest-owned WAL を observations にする")
    report.add_argument("--manifest", type=Path, required=True)
    report.add_argument("--output-root", type=Path, required=True)
    report.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = _artifacts.load_official_manifest(args.manifest)
        observations = build_observations(manifest=manifest, output_root=args.output_root)
        _write_create_only(args.out, observations)
    except (OSError, json.JSONDecodeError, _artifacts.OracleArtifactTypeError,
            ReportError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
