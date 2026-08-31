# -*- coding: utf-8 -*-
"""S-1 直接比較 report と三値判定を生成する。

freeze、4 campaign の session ledger/WAL、時間台帳を互いに照合し、hard gate が
失敗しても理由を構造化した JSON/Markdown report を必ず組み立てる。性能標本は
``s1-session`` の成功区間内にある certified COMMIT だけであり、孤立した bench 値や
COMMIT は採用しない。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
ROOT = _ORCHESTRATOR.parent

from . import artifact_admission, model, pipeline, s1_stats, wal  # noqa: E402
from .artifact_admission import (  # noqa: E402
    ArtifactAdmissionError,
    CampaignReadPurpose,
    CampaignVerifierEpoch,
    CampaignVerifierEpochRejected,
)
from .layout import repo_output_root  # noqa: E402
from .s1_direct_comparison import (  # noqa: E402
    BUDGET_REL,
    FREEZE_REL,
    SESSION_RESULT_STATUSES,
    TERMINAL_SESSION_STATUSES,
    _unknown_session_status_message,
    layout_for,
    read_budget,
    schedule_for_role,
    session_events_from_records,
    validate_session_events,
)


REPORT_REL = "reports/s1_direct_comparison"
REPORT_JSON = "report.json"
REPORT_MD = "report.md"
REFERENCE_ALPHA = 0.0125
ROLES = ("develop", "floor", "block1", "block2")
PERFORMANCE_ROLES = ("floor", "block1", "block2")
EXPECTED_N = {"develop": 1, "floor": 8, "block1": 4, "block2": 4}

ESTABLISHED = "成立"
NOT_ESTABLISHED = "不成立"
INDETERMINATE = "判定不能"


class ReportError(RuntimeError):
    """report 入力が事前登録契約を満たさず、判定に使えない。"""


@dataclass(frozen=True)
class Sample:
    """session ledger と WAL COMMIT の双方に束縛された 1 セッション標本。"""

    role: str
    schedule_index: int
    cell_id: str
    variant_id: str
    src_token: str
    fitness_tps: Optional[float]
    verify_configs: Tuple[str, ...]
    unstable: bool


@dataclass
class CampaignAssessment:
    """1 campaign の照合結果。内部 Sample は JSON へ直接出力しない。"""

    role: str
    schedule_gate: Dict
    samples: Dict[str, List[Sample]]
    sample_issues: List[Dict]
    retries: List[Dict]
    budget_refusals: List[Dict]
    rejected_commit_count: int
    campaign_verifier_epoch: Optional[Dict]
    epoch_issue: Optional[Dict]


def _reason(code: str, message: str, **fields: object) -> Dict:
    return {"code": code, "message": message, **fields}


def _dedupe_reasons(reasons: Iterable[Mapping]) -> List[Dict]:
    out: List[Dict] = []
    seen = set()
    for item in reasons:
        value = dict(item)
        key = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            out.append(value)
    return out


def _epoch_projection(epoch: CampaignVerifierEpoch) -> Dict:
    return {
        "campaign_verifier_epoch": epoch.campaign_verifier_epoch,
        "state": epoch.state,
        "reason_code": epoch.reason_code,
        "identity_scope": epoch.identity_scope,
        "excluded_scope": epoch.excluded_scope,
    }


def _rejected_epoch_projection(exc: CampaignVerifierEpochRejected) -> Dict:
    return {
        "campaign_verifier_epoch": exc.campaign_verifier_epoch,
        "state": exc.epoch_state,
        "reason_code": exc.reason_code,
        "identity_scope": exc.identity_scope,
        "excluded_scope": exc.excluded_scope,
    }


def _sha256(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def floor_cmp(cv_a: float, cv_b: float) -> float:
    """事前登録どおり ``max(cv_a, cv_b, 0.03)`` を返す純関数。"""
    values = (cv_a, cv_b)
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           for value in values):
        raise ValueError("floor CV は数値でなければならない")
    if any(not math.isfinite(float(value)) or float(value) < 0.0 for value in values):
        raise ValueError("floor CV は有限な非負値でなければならない")
    return max(float(cv_a), float(cv_b), 0.03)


def _between_session_cv(values: Sequence[float]) -> float:
    """floor の 8 独立セッションだけから標本 CV を算出する。"""
    if len(values) != 8:
        raise ValueError(f"floor CV は8セッション必須: n={len(values)}")
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           for value in values):
        raise ValueError("floor CV 入力に数値でない値がある")
    clean = tuple(float(value) for value in values)
    if any(not math.isfinite(value) for value in clean):
        raise ValueError("floor CV 入力に非有限値がある")
    mean = statistics.fmean(clean)
    if mean <= 0.0:
        raise ValueError("floor CV の平均 throughput が正でない")
    return statistics.stdev(clean) / mean


def bind_left_target(
        comparison: Mapping,
        observations: Mapping[str, Mapping[str, Sequence[float]]],
) -> Tuple[Tuple[Tuple[float, ...], Tuple[float, ...]],
           Tuple[Tuple[float, ...], Tuple[float, ...]], str]:
    """left=系側・greater・target=left の束縛を一箇所で固定する。

    ``observations`` は ``block1`` / ``block2`` の cell→4観測。freeze の left を
    ``stratified_test`` の target へ渡す向きは検定の意味そのものなので、推測や自動反転を
    行わず三点契約に反した freeze を拒否する。
    """
    left = comparison.get("left_cell")
    right = comparison.get("right_cell")
    alternative = comparison.get("alternative")
    if not isinstance(left, str) or not isinstance(right, str):
        raise ValueError("comparison の left_cell/right_cell が文字列でない")
    if left.rsplit(":", 1)[-1] != "system_gate":
        raise ValueError("freeze comparison の left_cell が system_gate でない")
    if alternative != "greater":
        raise ValueError("freeze comparison の alternative が greater でない")
    try:
        target = (tuple(observations["block1"][left]),
                  tuple(observations["block2"][left]))
        control = (tuple(observations["block1"][right]),
                   tuple(observations["block2"][right]))
    except (KeyError, TypeError) as exc:
        raise ValueError("比較セルの block 観測がない") from exc
    return target, control, "greater"


def _event(record, name: str) -> bool:
    return (record.stage == model.STAGE_S1_SESSION and isinstance(record.payload, dict)
            and record.payload.get("event") == name)


def _session_segments(records: Sequence) -> List[List]:
    """物理 WAL 順を保ち、各 session-start から次の start 直前までを切り出す。"""
    segments: List[List] = []
    current: Optional[List] = None
    for record in records:
        if _event(record, "session-start"):
            if current is not None:
                segments.append(current)
            current = [record]
        elif current is not None:
            current.append(record)
    if current is not None:
        segments.append(current)
    return segments


def _validate_event_metadata(events: Sequence[Mapping], schedule: Sequence, role: str) -> None:
    """B2a の順序 validator に加え、全 event の identity と開始時刻を照合する。"""
    campaign_starts = [event for event in events if event.get("event") == "campaign-start"]
    if len(campaign_starts) != 1:
        raise ReportError(f"{role}: campaign-start が一意でない: {len(campaign_starts)}")
    campaign_start = campaign_starts[0]
    if (campaign_start.get("campaign_role") != role
            or not isinstance(campaign_start.get("ts"), str)
            or not campaign_start.get("ts")):
        raise ReportError(f"{role}: campaign-start の role/ts が不正")

    by_index = {item.schedule_index: item for item in schedule}
    starts = {}
    retry_keys = []
    allowed = {"campaign-start", "session-start", "session-result", "retry",
               "budget-refused", "deviation"}
    for event in events:
        event_name = event.get("event")
        if event_name not in allowed:
            raise ReportError(f"{role}: 未知の s1-session event: {event_name!r}")
        index = event.get("schedule_index")
        if event_name in {"campaign-start", "deviation"}:
            continue
        if isinstance(index, bool) or not isinstance(index, int) or index not in by_index:
            raise ReportError(f"{role}: event.schedule_index が schedule 外: {index!r}")
        item = by_index[index]
        for key, expected in (("campaign_role", role), ("lap", item.lap),
                              ("cell_id", item.cell_id)):
            if event.get(key) != expected:
                raise ReportError(
                    f"{role}: event {event_name} index={index} の {key} 不一致: "
                    f"expected={expected!r} actual={event.get(key)!r}")
        if event_name == "session-start":
            attempt = event.get("attempt")
            if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 0:
                raise ReportError(f"{role}: session-start.attempt が不正")
            starts[(index, attempt)] = event
        elif event_name == "retry":
            attempt = event.get("attempt")
            if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt <= 0:
                raise ReportError(f"{role}: retry.attempt が正整数でない")
            retry_keys.append((index, attempt))
        elif event_name == "session-result":
            status = event.get("status")
            if type(status) is not str or status not in SESSION_RESULT_STATUSES:
                raise ReportError(
                    f"{role}: "
                    + _unknown_session_status_message("session-result.status", status))
            attempt = event.get("attempt")
            start = starts.get((index, attempt))
            interrupted_unknown = (
                event.get("status") == "abandoned"
                and event.get("variant") == "unknown"
                and "interrupted-before-result" in str(event.get("reason", "")))
            if start is None or (event.get("variant") != start.get("variant")
                                 and not interrupted_unknown):
                raise ReportError(
                    f"{role}: session-result が同じ index/attempt/variant の start に束縛されない")
    expected_retries = {key for key in starts if key[1] > 0}
    if len(retry_keys) != len(set(retry_keys)) or set(retry_keys) != expected_retries:
        raise ReportError(
            f"{role}: retry 記録と attempt>0 の session-start が一対一でない: "
            f"retry={retry_keys} starts={sorted(expected_retries)}")


def _read_campaign_lock_bytes(layout) -> bytes:
    try:
        return Path(layout.lock_file).read_bytes()
    except OSError as exc:
        raise ArtifactAdmissionError(
            f"campaign.lock cannot be read: {layout.lock_file}"
        ) from exc


def _campaign_verifier_epoch_from_lock_bytes(
        lock_bytes: bytes,
) -> CampaignVerifierEpoch:
    recorded = artifact_admission._recorded_campaign_verifier_epoch(
        artifact_admission._decode_campaign_lock(lock_bytes)
    )
    return artifact_admission._require_verifier_epoch_for_purpose(
        recorded, CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )


def _sample_from_segment(
        role: str, item, segment: Sequence, *, campaign_records=None,
        campaign_lock_sha256: Optional[str] = None,
        persisted_certification_error: Optional[str] = None,
) -> Tuple[Optional[Sample], Optional[Dict]]:
    start = segment[0].payload
    results = [record.payload for record in segment if _event(record, "session-result")]
    successful = [result for result in results if result.get("status") == "success"]
    if not successful:
        return None, None
    if len(successful) != 1:
        return None, _reason(
            "duplicate_success_result", "1 session 区間に success 終端が複数ある",
            campaign=role, cell=item.freeze_cell_id, schedule_index=item.schedule_index)
    result = successful[0]
    variant = start.get("variant")
    if (not isinstance(variant, str) or not variant
            or result.get("variant") != variant
            or start.get("schedule_index") != item.schedule_index
            or result.get("schedule_index") != item.schedule_index):
        return None, _reason(
            "session_identity_mismatch", "session start/result と schedule の identity が不一致",
            campaign=role, cell=item.freeze_cell_id, schedule_index=item.schedule_index)

    builds = [record for record in segment
              if record.stage == "build_start" and record.variant == variant]
    commits = [record for record in segment
               if record.stage == "commit" and record.variant == variant]
    if len(builds) != 1 or len(commits) != 1:
        return None, _reason(
            "certified_commit_missing", "success session に一意な build_start/COMMIT がない",
            campaign=role, cell=item.freeze_cell_id, schedule_index=item.schedule_index,
            build_start_count=len(builds), commit_count=len(commits))
    if persisted_certification_error is not None:
        return None, _reason(
            "persisted_certification_invalid", persisted_certification_error,
            campaign=role, cell=item.freeze_cell_id,
            schedule_index=item.schedule_index)
    try:
        artifact_admission.require_persisted_certified_commit(
            campaign_records, commits[0],
            campaign_lock_sha256=campaign_lock_sha256,
        )
    except (ArtifactAdmissionError, TypeError) as exc:
        return None, _reason(
            "persisted_certification_invalid",
            f"保存済み COMMIT の certified 証拠が不正: {exc}",
            campaign=role, cell=item.freeze_cell_id,
            schedule_index=item.schedule_index,
            error_type=type(exc).__name__)
    src_token = builds[0].payload.get("src_token")
    payload = commits[0].payload
    verify = payload.get("verify_configs")
    if not isinstance(src_token, str) or not src_token:
        return None, _reason(
            "src_token_missing", "build_start に src_token がない",
            campaign=role, cell=item.freeze_cell_id, schedule_index=item.schedule_index)
    if (not isinstance(verify, list) or not verify
            or not all(isinstance(value, str) for value in verify)):
        return None, _reason(
            "verify_configs_invalid", "COMMIT の verify_configs が空または不正",
            campaign=role, cell=item.freeze_cell_id, schedule_index=item.schedule_index)
    required = ({pipeline.LEGACY_TAG, pipeline.S2_TAG}
                if role == "develop" else {pipeline.LEGACY_TAG})
    if not required.issubset(set(verify)):
        return None, _reason(
            "verify_configs_missing", "COMMIT が campaign 必須 verify 構成を含まない",
            campaign=role, cell=item.freeze_cell_id, schedule_index=item.schedule_index,
            required=sorted(required), actual=verify)

    fitness = payload.get("fitness_tps")
    if role == "develop":
        if fitness is not None:
            return None, _reason(
                "develop_fitness_present", "bench 無し develop COMMIT に fitness_tps がある",
                campaign=role, cell=item.freeze_cell_id, schedule_index=item.schedule_index)
        clean_fitness: Optional[float] = None
    else:
        if (isinstance(fitness, bool) or not isinstance(fitness, (int, float))
                or not math.isfinite(float(fitness))):
            return None, _reason(
                "fitness_invalid", "性能 COMMIT の fitness_tps が null または非有限",
                campaign=role, cell=item.freeze_cell_id, schedule_index=item.schedule_index)
        clean_fitness = float(fitness)
    unstable = payload.get("unstable", False)
    if not isinstance(unstable, bool):
        return None, _reason(
            "unstable_invalid", "COMMIT の unstable が bool でない",
            campaign=role, cell=item.freeze_cell_id, schedule_index=item.schedule_index)
    return Sample(
        role=role, schedule_index=item.schedule_index, cell_id=item.freeze_cell_id,
        variant_id=variant, src_token=src_token, fitness_tps=clean_fitness,
        verify_configs=tuple(verify), unstable=unstable,
    ), None


def _assess_campaign(document: Mapping, role: str, output_root: str) -> CampaignAssessment:
    schedule_gate = {"status": "fail", "expected_sessions": None,
                     "recorded_sessions": 0, "reasons": []}
    samples: Dict[str, List[Sample]] = {}
    issues: List[Dict] = []
    retries: List[Dict] = []
    budget_refusals: List[Dict] = []
    rejected_commit_count = 0
    epoch_projection: Optional[Dict] = None
    epoch_issue: Optional[Dict] = None
    try:
        schedule = schedule_for_role(document, role)
        layout = layout_for(document, role, output_root=output_root)
        # S1 は破損行と切断末尾を valid prefix とともに収集するため、WAL 全体を
        # admission reader へ渡さない。中央の lock-only gate を WAL 読取前に通す。
        try:
            lock_bytes = _read_campaign_lock_bytes(layout)
            campaign_lock_sha256 = hashlib.sha256(lock_bytes).hexdigest()
            epoch = _campaign_verifier_epoch_from_lock_bytes(lock_bytes)
            epoch_projection = _epoch_projection(epoch)
        except CampaignVerifierEpochRejected as exc:
            epoch_projection = _rejected_epoch_projection(exc)
            epoch_issue = _reason(
                "campaign_verifier_epoch_rejected",
                "campaign verifier epoch が certified S1 標本を受理しない",
                campaign=role,
                **epoch_projection,
            )
            schedule_gate["reasons"].append(epoch_issue)
            schedule_gate["reasons"] = _dedupe_reasons(schedule_gate["reasons"])
            return CampaignAssessment(
                role=role, schedule_gate=schedule_gate, samples=samples,
                sample_issues=[], retries=retries,
                budget_refusals=budget_refusals,
                rejected_commit_count=rejected_commit_count,
                campaign_verifier_epoch=epoch_projection,
                epoch_issue=epoch_issue,
            )
        except ArtifactAdmissionError as exc:
            epoch_issue = _reason(
                "campaign_verifier_epoch_validation_failed",
                str(exc), campaign=role, error_type=type(exc).__name__,
            )
            schedule_gate["reasons"].append(epoch_issue)
            schedule_gate["reasons"] = _dedupe_reasons(schedule_gate["reasons"])
            return CampaignAssessment(
                role=role, schedule_gate=schedule_gate, samples=samples,
                sample_issues=[], retries=retries,
                budget_refusals=budget_refusals,
                rejected_commit_count=rejected_commit_count,
                campaign_verifier_epoch=None,
                epoch_issue=epoch_issue,
            )
        # 物理問題を収集する read は 1 回だけ。問題があっても valid prefix の解析を続ける。
        records, line_issues, truncated_tail = wal.read_records_collected(layout)
        persisted_certification_error = None
        try:
            lock_sha256_after_records = hashlib.sha256(
                _read_campaign_lock_bytes(layout)
            ).hexdigest()
        except ArtifactAdmissionError as exc:
            persisted_certification_error = (
                f"WAL 読取後に campaign.lock を再検証できない: {exc}"
            )
        else:
            if lock_sha256_after_records != campaign_lock_sha256:
                persisted_certification_error = (
                    "WAL 読取中に campaign.lock の SHA-256 が変化した"
                )
        if truncated_tail:
            schedule_gate["reasons"].append(_reason(
                "wal_truncated_tail",
                "WAL の末尾 record が newline 終端されていない",
                campaign=role,
            ))
        if line_issues:
            schedule_gate["reasons"].append(_reason(
                "wal_line_issues",
                "WAL に終端済みの decode/JSON/record 契約違反行がある",
                campaign=role,
                count=len(line_issues),
                first_issues=[
                    {"line_number": line_number, "reason": reason}
                    for line_number, reason in line_issues[:5]
                ],
            ))

        events = session_events_from_records(records)
        next_index: Optional[int] = None
        try:
            _validate_event_metadata(events, schedule, role)
            next_index = validate_session_events(events, schedule)
        except Exception as exc:
            schedule_gate["reasons"].append(_reason(
                "schedule_ledger_invalid", str(exc), campaign=role,
                error_type=type(exc).__name__))
        starts = [event for event in events if event.get("event") == "session-start"]
        schedule_gate.update(
            expected_sessions=len(schedule), recorded_attempt_starts=len(starts),
            recorded_initial_starts=sum(event.get("attempt") == 0 for event in starts),
            campaign_started_at=next(
                (event.get("ts") for event in events
                 if event.get("event") == "campaign-start"), None),
            next_index=next_index)
        if next_index is not None and next_index != len(schedule):
            schedule_gate["reasons"].append(_reason(
                "schedule_incomplete", "ledger が凍結 schedule を完走していない",
                campaign=role, next_index=next_index, expected=len(schedule)))

        by_index = {item.schedule_index: item for item in schedule}
        used_commit_ids = set()
        for segment in _session_segments(records):
            start = segment[0].payload
            index = start.get("schedule_index")
            item = by_index.get(index) if isinstance(index, int) and not isinstance(index, bool) else None
            if item is None:
                continue
            sample, issue = _sample_from_segment(
                role, item, segment,
                campaign_records=records,
                campaign_lock_sha256=campaign_lock_sha256,
                persisted_certification_error=persisted_certification_error,
            )
            if issue is not None:
                issues.append(issue)
            if sample is not None:
                samples.setdefault(sample.cell_id, []).append(sample)
                for record in segment:
                    if record.stage == "commit" and record.variant == sample.variant_id:
                        used_commit_ids.add(id(record))
        all_commits = [record for record in records if record.stage == "commit"]
        rejected_commit_count = len(all_commits) - len(used_commit_ids)

        for event in events:
            if event.get("event") != "retry":
                continue
            retry = dict(event)
            index = retry.get("schedule_index")
            item = by_index.get(index) if isinstance(index, int) and not isinstance(index, bool) else None
            retry["freeze_cell_id"] = item.freeze_cell_id if item is not None else None
            retries.append(retry)
        budget_refusals = [dict(event) for event in events
                           if event.get("event") == "budget-refused"]
        if not schedule_gate["reasons"] and next_index == len(schedule):
            schedule_gate["status"] = "pass"
    except Exception as exc:  # report は hard gate 失敗自体を出力する。
        schedule_gate["status"] = "fail"
        schedule_gate["reasons"].append(_reason(
            "schedule_ledger_invalid", str(exc), campaign=role,
            error_type=type(exc).__name__))
    schedule_gate["reasons"] = _dedupe_reasons(schedule_gate["reasons"])
    return CampaignAssessment(
        role=role, schedule_gate=schedule_gate, samples=samples,
        sample_issues=_dedupe_reasons(issues), retries=retries,
        budget_refusals=budget_refusals,
        rejected_commit_count=rejected_commit_count,
        campaign_verifier_epoch=epoch_projection,
        epoch_issue=epoch_issue,
    )


def _load_raw_json(path: Path) -> Optional[Dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _assess_budget(path: Path, assessments: Mapping[str, CampaignAssessment]) -> Dict:
    result = {
        "status": "fail", "path": str(path), "total_budget_s": None,
        "spent_s": None, "remaining_s": None, "phase_spent_s": {},
        "retry_spent_s": None, "preflight_refusals": [], "reasons": [],
    }
    if not path.is_file():
        result["reasons"].append(_reason(
            "budget_missing", "時間台帳が存在しない", path=str(path)))
        return result
    try:
        document = read_budget(path)
    except Exception as exc:
        validator_overspend = "超過済み" in str(exc)
        result["reasons"].append(_reason(
            "budget_public_validation_failed" if validator_overspend else "budget_invalid",
            str(exc), error_type=type(exc).__name__))
        document = _load_raw_json(path)
        if document is None:
            return result

    total = document.get("total_budget_s")
    spent = document.get("spent_s")
    entries = document.get("entries")
    if (isinstance(total, bool) or not isinstance(total, (int, float))
            or isinstance(spent, bool) or not isinstance(spent, (int, float))
            or not math.isfinite(float(total)) or not math.isfinite(float(spent))
            or not isinstance(entries, list)):
        result["reasons"].append(_reason(
            "budget_summary_invalid", "時間台帳の total/spent/entries を要約できない"))
        return result
    result["total_budget_s"] = float(total)
    result["spent_s"] = float(spent)
    result["remaining_s"] = float(total) - float(spent)
    phase_spent: Dict[str, float] = {}
    retry_spent = 0.0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        wall = entry.get("wall_s")
        phase = entry.get("phase")
        if isinstance(wall, (int, float)) and not isinstance(wall, bool) and math.isfinite(float(wall)):
            phase_spent[str(phase)] = phase_spent.get(str(phase), 0.0) + float(wall)
            if str(entry.get("note", "")).startswith("machine-failure-retry:"):
                retry_spent += float(wall)
        if str(entry.get("note", "")).startswith("budget-refused:"):
            result["preflight_refusals"].append(dict(entry))
    for assessment in assessments.values():
        result["preflight_refusals"].extend(assessment.budget_refusals)
    result["phase_spent_s"] = dict(sorted(phase_spent.items()))
    result["retry_spent_s"] = retry_spent
    if float(spent) > float(total):
        result["reasons"].append(_reason(
            "budget_exceeded", "spent_s が total_budget_s を超過",
            spent_s=float(spent), total_budget_s=float(total)))
    if result["preflight_refusals"]:
        result["reasons"].append(_reason(
            "budget_preflight_refused", "起動前予算検査で起動しなかった記録がある",
            count=len(result["preflight_refusals"])))
    result["reasons"] = _dedupe_reasons(result["reasons"])
    if not result["reasons"]:
        result["status"] = "pass"
    return result


def _values(assessment: CampaignAssessment, cell: str) -> List[float]:
    return [float(sample.fitness_tps) for sample in assessment.samples.get(cell, [])
            if sample.fitness_tps is not None]


def _sample_count_reasons(
        comparison: Mapping, assessments: Mapping[str, CampaignAssessment]) -> List[Dict]:
    reasons: List[Dict] = []
    for role in PERFORMANCE_ROLES:
        expected = EXPECTED_N[role]
        for side in ("left_cell", "right_cell"):
            cell = comparison.get(side)
            if not isinstance(cell, str):
                reasons.append(_reason(
                    "comparison_cell_invalid", f"{side} が文字列でない", campaign=role))
                continue
            actual = len(assessments[role].samples.get(cell, []))
            if actual != expected:
                reasons.append(_reason(
                    "sample_n_mismatch", "retry/失敗後の certified 標本数が事前登録 n と不一致",
                    campaign=role, cell=cell, expected_n=expected, actual_n=actual))
    return reasons


def _develop_match_issues(assessments: Mapping[str, CampaignAssessment]) -> List[Dict]:
    evidence = {(sample.variant_id, sample.src_token)
                for samples in assessments["develop"].samples.values() for sample in samples}
    issues: List[Dict] = []
    for role in PERFORMANCE_ROLES:
        for cell, samples in assessments[role].samples.items():
            for sample in samples:
                if (sample.variant_id, sample.src_token) not in evidence:
                    issues.append(_reason(
                        "develop_certified_missing",
                        "同じ variant_id/src_token の legacy+s2 develop COMMIT がない",
                        campaign=role, cell=cell, schedule_index=sample.schedule_index,
                        variant_id=sample.variant_id, src_token=sample.src_token))
    return _dedupe_reasons(issues)


def _sample_count_gate(document: Optional[Mapping],
                       assessments: Mapping[str, CampaignAssessment]) -> Dict:
    result = {"status": "fail", "cells": {}, "reasons": []}
    cells = document.get("cells") if document is not None else None
    if not isinstance(cells, Mapping):
        result["reasons"] = [_reason(
            "sample_counts_not_evaluated", "freeze cells がないため標本数を評価できない")]
        return result
    passed = True
    for role, assessment in assessments.items():
        role_counts = {}
        for cell in cells:
            actual = len(assessment.samples.get(str(cell), []))
            expected = EXPECTED_N[role]
            status = "pass" if actual == expected else "fail"
            role_counts[str(cell)] = {"expected_n": expected, "actual_n": actual,
                                      "status": status}
            passed = passed and status == "pass"
        result["cells"][role] = role_counts
    result["status"] = "pass" if passed else "fail"
    if not passed:
        result["reasons"] = [_reason(
            "sample_n_mismatch", "retry/失敗後の cell n に事前登録値未達がある")]
    return result


def _sample_evidence(sample: Sample) -> Dict:
    value = asdict(sample)
    value["verify_configs"] = list(sample.verify_configs)
    return value


def _sign(value: float) -> int:
    return (value > 0.0) - (value < 0.0)


def _block_effects(target, control) -> Dict:
    return {
        "left_cell_block1_minus_block2_median":
            statistics.median(target[0]) - statistics.median(target[1]),
        "right_cell_block1_minus_block2_median":
            statistics.median(control[0]) - statistics.median(control[1]),
    }


def _retries_for(comparison: Mapping, assessments: Mapping[str, CampaignAssessment]) -> List[Dict]:
    cells = {comparison.get("left_cell"), comparison.get("right_cell")}
    out = []
    for assessment in assessments.values():
        for retry in assessment.retries:
            if retry.get("freeze_cell_id") in cells:
                out.append(dict(retry))
    return out


def _comparison_complete(comparison: Mapping, assessments: Mapping[str, CampaignAssessment]) -> bool:
    return not _sample_count_reasons(comparison, assessments)


def _numeric_evaluation(comparison: Mapping,
                        assessments: Mapping[str, CampaignAssessment]) -> Dict:
    """標本数と schedule が有効な比較の検定・gate・開示値を一括計算する。"""
    left = comparison.get("left_cell")
    right = comparison.get("right_cell")
    observations = {
        role: {cell: _values(assessments[role], cell) for cell in (left, right)}
        for role in PERFORMANCE_ROLES
    }
    floor_left_cv = _between_session_cv(observations["floor"][left])
    floor_right_cv = _between_session_cv(observations["floor"][right])
    cmp_floor = floor_cmp(floor_left_cv, floor_right_cv)
    target, control, alternative = bind_left_target(comparison, observations)
    test_result = s1_stats.stratified_test(target, control, alternative)
    target_all = tuple(value for layer in target for value in layer)
    control_all = tuple(value for layer in control for value in layer)
    target_median = statistics.median(target_all)
    control_median = statistics.median(control_all)
    if control_median <= 0.0:
        raise ValueError("right/control セルの pooled median が正でない")
    relative_difference = (target_median - control_median) / control_median
    pooled_sign = _sign(target_median - control_median)
    block_signs = (
        _sign(statistics.median(target[0]) - statistics.median(control[0])),
        _sign(statistics.median(target[1]) - statistics.median(control[1])),
    )
    gate1 = relative_difference > cmp_floor
    gate2 = pooled_sign != 0 and block_signs[0] == block_signs[1] == pooled_sign
    effects = asdict(test_result.effects)
    effects.update({
        "relative_median_difference": relative_difference,
        "floor_left_cv": floor_left_cv, "floor_right_cv": floor_right_cv,
    })
    return {
        "floor_cmp": cmp_floor, "target": target, "control": control,
        "test_result": test_result, "gate1": gate1, "gate2": gate2,
        "relative_difference": relative_difference, "pooled_sign": pooled_sign,
        "block_signs": block_signs, "effects": effects,
    }


def _evaluate_comparison(
        comparison: Mapping, assessments: Mapping[str, CampaignAssessment],
        global_reasons: Sequence[Mapping], certified_issues: Sequence[Mapping],
        budget: Mapping,
) -> Tuple[Dict, Optional[Dict]]:
    comparison_id = comparison.get("comparison_id")
    entry = {
        "comparison_id": comparison_id, "family": comparison.get("family"),
        "workload": comparison.get("workload"), "left_cell": comparison.get("left_cell"),
        "right_cell": comparison.get("right_cell"),
        "alternative": comparison.get("alternative"), "judgment": INDETERMINATE,
        "reasons": [], "gates": {"gate1": None, "gate2": None},
        "floor_cmp": None, "p_perm": None, "p_star": None,
        "reference_alpha": REFERENCE_ALPHA, "reference_below_alpha": None,
        "unstable_counts": {}, "block_effects": None,
        "retry_events": _retries_for(comparison, assessments),
    }
    reasons = [dict(reason) for reason in global_reasons]
    count_reasons = _sample_count_reasons(comparison, assessments)
    reasons.extend(count_reasons)
    cells = {comparison.get("left_cell"), comparison.get("right_cell")}
    for assessment in assessments.values():
        reasons.extend(issue for issue in assessment.sample_issues
                       if issue.get("cell") in cells)
    reasons.extend(issue for issue in certified_issues if issue.get("cell") in cells)

    budget_codes = {reason.get("code") for reason in budget.get("reasons", [])}
    if budget_codes & {"budget_missing", "budget_invalid", "budget_summary_invalid"}:
        reasons.extend(budget.get("reasons", []))
    elif "budget_preflight_refused" in budget_codes:
        # 起動前拒否は拒否対象の schedule 未完を必ず伴い、schedule hard gate が
        # global に全比較を判定不能へ倒す。この分岐は当該未完比較へ拒否理由も結び付ける。
        if not _comparison_complete(comparison, assessments):
            reasons.extend(budget.get("reasons", []))

    left = comparison.get("left_cell")
    right = comparison.get("right_cell")
    if isinstance(left, str) and isinstance(right, str):
        for role in PERFORMANCE_ROLES:
            entry["unstable_counts"][role] = {
                "left": sum(sample.unstable for sample in assessments[role].samples.get(left, [])),
                "right": sum(sample.unstable for sample in assessments[role].samples.get(right, [])),
            }
    entry["reasons"] = _dedupe_reasons(reasons)
    numeric = None
    can_disclose = (not count_reasons and all(
        assessments[role].schedule_gate.get("status") == "pass"
        for role in PERFORMANCE_ROLES))
    try:
        if can_disclose:
            numeric = _numeric_evaluation(comparison, assessments)
    except Exception as exc:
        entry["reasons"] = _dedupe_reasons([*entry["reasons"], _reason(
            "comparison_evaluation_failed", str(exc), error_type=type(exc).__name__)])
        return entry, None
    if numeric is None:
        return entry, None

    entry["block_effects"] = _block_effects(numeric["target"], numeric["control"])
    if entry["reasons"]:
        # hard gate 失敗時も、信頼できる性能 WAL の記述統計は判定から切り離して開示する。
        return entry, numeric["effects"]

    try:
        test_result = numeric["test_result"]
        p_value = s1_stats.p_star(
            test_result.p_perm, numeric["gate1"] and numeric["gate2"])
        judgment = ESTABLISHED if p_value <= REFERENCE_ALPHA else NOT_ESTABLISHED
        entry.update({
            "judgment": judgment,
            "gates": {
                "gate1": {"passed": numeric["gate1"],
                          "relative_median_difference": numeric["relative_difference"],
                          "required_strictly_greater_than": numeric["floor_cmp"]},
                "gate2": {"passed": numeric["gate2"],
                          "pooled_direction_sign": numeric["pooled_sign"],
                          "block_direction_signs": list(numeric["block_signs"])},
            },
            "floor_cmp": numeric["floor_cmp"],
            "p_perm": test_result.p_perm, "p_star": p_value,
            "reference_below_alpha": p_value <= REFERENCE_ALPHA,
        })
        return entry, numeric["effects"]
    except Exception as exc:
        entry["reasons"] = [_reason(
            "comparison_evaluation_failed", str(exc), error_type=type(exc).__name__)]
        return entry, None


def _family_report(name: str, comparisons: Sequence[Mapping]) -> Dict:
    members = [comparison for comparison in comparisons
               if str(comparison.get("family", "")).lower() == name]
    result = {
        "judgment": INDETERMINATE, "comparison_ids": [m.get("comparison_id") for m in members],
        "p_family": None, "reference_alpha": REFERENCE_ALPHA,
        "reference_below_alpha": None,
        "holm_family4_adjudication": "not_performed_human_or_future",
        "judgment_basis": "reference_alpha_only_not_holm_family4_adjudication",
        "reasons": [],
    }
    if not members:
        result["reasons"] = [_reason("family_empty", "family に比較がない")]
        return result
    indeterminate = [member.get("comparison_id") for member in members
                     if member.get("judgment") == INDETERMINATE]
    if indeterminate:
        result["reasons"] = [_reason(
            "family_member_indeterminate", "family 内に判定不能の比較がある",
            comparison_ids=indeterminate)]
        return result
    try:
        p_value = s1_stats.family_p([float(member["p_star"]) for member in members])
    except (KeyError, TypeError, ValueError) as exc:
        result["reasons"] = [_reason("family_p_failed", str(exc))]
        return result
    result.update({
        "judgment": ESTABLISHED if p_value <= REFERENCE_ALPHA else NOT_ESTABLISHED,
        "p_family": p_value, "reference_below_alpha": p_value <= REFERENCE_ALPHA,
    })
    return result


def _git_head() -> str:
    try:
        process = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReportError(f"generated_at_head を取得できない: {exc}") from exc
    head = process.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise ReportError(f"generated_at_head が40桁 SHA でない: {head!r}")
    return head


def build_report(
        *, freeze_path: Path, budget_path: Path, output_root: str,
        freeze_verify: Optional[Callable[[Path], Mapping]] = None,
        generated_at_head: Optional[str] = None,
) -> Dict:
    """全入力を照合し、hard gate 失敗も値として保持する report 純データを返す。"""
    freeze_ref = {"path": str(freeze_path), "sha256": _sha256(freeze_path)}
    freeze_gate = {"status": "fail", "reasons": []}
    document: Optional[Mapping] = None
    try:
        if freeze_verify is None:
            from . import s1_measurement_freeze
            document = s1_measurement_freeze.verify(freeze_path)
        else:
            document = freeze_verify(freeze_path)
        if not isinstance(document, Mapping):
            raise ReportError("freeze verify の戻り値が object でない")
        freeze_gate["status"] = "pass"
    except Exception as exc:
        freeze_gate["reasons"] = [_reason(
            "freeze_verification_failed", str(exc), error_type=type(exc).__name__)]

    assessments: Dict[str, CampaignAssessment] = {}
    if document is not None:
        for role in ROLES:
            assessments[role] = _assess_campaign(document, role, output_root)
    else:
        for role in ROLES:
            assessments[role] = CampaignAssessment(
                role=role,
                schedule_gate={"status": "not_evaluated", "reasons": [_reason(
                    "freeze_unavailable", "freeze 照合失敗のため schedule を評価しない",
                    campaign=role)]},
                samples={}, sample_issues=[], retries=[], budget_refusals=[],
                rejected_commit_count=0, campaign_verifier_epoch=None,
                epoch_issue=None)

    budget = _assess_budget(budget_path, assessments)
    certified_issues = _develop_match_issues(assessments) if document is not None else []
    all_sample_issues = [issue for assessment in assessments.values()
                         for issue in assessment.sample_issues]
    epoch_issues = [assessment.epoch_issue for assessment in assessments.values()
                    if assessment.epoch_issue is not None]
    certified_gate = {
        "status": ("pass" if document is not None
                   and not all_sample_issues and not certified_issues
                   and not epoch_issues else "fail"),
        "issues": _dedupe_reasons([
            *all_sample_issues, *certified_issues, *epoch_issues,
        ]),
        "campaign_verifier_epochs": {
            role: assessment.campaign_verifier_epoch
            for role, assessment in assessments.items()
        },
        "accepted_samples": {
            role: sum(len(samples) for samples in assessment.samples.values())
            for role, assessment in assessments.items()
        },
        "rejected_or_unbound_commits": {
            role: assessment.rejected_commit_count for role, assessment in assessments.items()
        },
        "accepted_evidence": {
            role: [_sample_evidence(sample) for samples in assessment.samples.values()
                   for sample in samples]
            for role, assessment in assessments.items()
        },
    }
    sample_count_gate = _sample_count_gate(document, assessments)

    global_reasons: List[Dict] = []
    if freeze_gate["status"] != "pass":
        global_reasons.extend(freeze_gate["reasons"])
    for role, assessment in assessments.items():
        if assessment.schedule_gate.get("status") != "pass":
            global_reasons.extend(assessment.schedule_gate.get("reasons", []))
    # 総予算超過は freeze / schedule と同じ全体 hard gate であり、標本の完備性に
    # かかわらず全比較を判定不能へ倒す。公開 validator が先に超過を拒否した場合も同じ。
    global_reasons.extend(
        reason for reason in budget.get("reasons", [])
        if reason.get("code") in {
            "budget_exceeded", "budget_public_validation_failed",
        }
    )

    raw_comparisons = document.get("comparisons", []) if document is not None else []
    if not isinstance(raw_comparisons, list):
        raw_comparisons = []
        global_reasons.append(_reason(
            "comparisons_invalid", "freeze comparisons が list でない"))
    comparison_reports: List[Dict] = []
    effect_sizes: Dict[str, Dict] = {}
    for comparison in raw_comparisons:
        if not isinstance(comparison, Mapping):
            continue
        result, effects = _evaluate_comparison(
            comparison, assessments, global_reasons, certified_issues, budget)
        comparison_reports.append(result)
        if effects is not None and isinstance(result.get("comparison_id"), str):
            effect_sizes[result["comparison_id"]] = effects

    head = generated_at_head or _git_head()
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise ReportError("generated_at_head が40桁 SHA でない")
    return {
        "freeze_ref": freeze_ref,
        "hard_gates": {
            "freeze": freeze_gate,
            "schedule": {role: assessment.schedule_gate
                         for role, assessment in assessments.items()},
            "certified": certified_gate,
            "sample_counts": sample_count_gate,
            "budget": {"status": budget["status"], "reasons": budget["reasons"]},
        },
        "comparisons": comparison_reports,
        "families": {
            "s1a": _family_report("s-1a", comparison_reports),
            "s1b": _family_report("s-1b", comparison_reports),
        },
        "effect_sizes": effect_sizes,
        "budget": budget,
        "generated_at_head": head,
    }


def _fmt(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(report: Mapping) -> str:
    """JSON report の人間向け要約を作る。数値は JSON を正本として丸めて表示する。"""
    lines = [
        "# S-1 直接比較 report", "",
        "本設計は独立な検証相を持たない。ブロック化した単一登録追試 + gate 連言であり、"
        "旧記述の「スクリーニング → 検証相」はこの gate 連言として読み替える。", "",
        "Holm 族 4 全体の裁定は行わない。α=0.0125 との比較は参考表示であり、"
        "族全体の裁定は人間または将来の consumer が行う。", "",
        "## Hard gates", "",
        "| gate | scope | status | reasons |", "|---|---|---|---|",
    ]
    hard = report.get("hard_gates", {})
    freeze = hard.get("freeze", {})
    lines.append(f"| freeze | all | {_fmt(freeze.get('status'))} | "
                 f"{_fmt(', '.join(r.get('code', '?') for r in freeze.get('reasons', [])))} |")
    for role, gate in hard.get("schedule", {}).items():
        lines.append(f"| schedule | {_fmt(role)} | {_fmt(gate.get('status'))} | "
                     f"{_fmt(', '.join(r.get('code', '?') for r in gate.get('reasons', [])))} |")
    certified = hard.get("certified", {})
    lines.append(f"| certified | samples | {_fmt(certified.get('status'))} | "
                 f"{_fmt(', '.join(r.get('code', '?') for r in certified.get('issues', [])))} |")
    sample_counts = hard.get("sample_counts", {})
    lines.append(f"| sample counts | cells | {_fmt(sample_counts.get('status'))} | "
                 f"{_fmt(', '.join(r.get('code', '?') for r in sample_counts.get('reasons', [])))} |")
    budget_gate = hard.get("budget", {})
    lines.append(f"| budget | incomplete comparisons | {_fmt(budget_gate.get('status'))} | "
                 f"{_fmt(', '.join(r.get('code', '?') for r in budget_gate.get('reasons', [])))} |")

    lines.extend(["", "## Comparisons", "",
                  "| comparison | family | 判定 | relative median diff | floor_cmp | p_perm | p* | reasons |",
                  "|---|---|---|---:|---:|---:|---:|---|"])
    for comparison in report.get("comparisons", []):
        gate1 = comparison.get("gates", {}).get("gate1")
        relative = gate1.get("relative_median_difference") if isinstance(gate1, dict) else None
        codes = ", ".join(reason.get("code", "?") for reason in comparison.get("reasons", []))
        lines.append(
            f"| {_fmt(comparison.get('comparison_id'))} | {_fmt(comparison.get('family'))} | "
            f"{_fmt(comparison.get('judgment'))} | {_fmt(relative)} | "
            f"{_fmt(comparison.get('floor_cmp'))} | {_fmt(comparison.get('p_perm'))} | "
            f"{_fmt(comparison.get('p_star'))} | {_fmt(codes)} |")

    lines.extend(["", "## Families (Holm 族全体の裁定前の参考値)", "",
                  "| family | 三値判定 | family p | α=0.0125 以下 |",
                  "|---|---|---:|---|"])
    for name, family in report.get("families", {}).items():
        lines.append(f"| {_fmt(name)} | {_fmt(family.get('judgment'))} | "
                     f"{_fmt(family.get('p_family'))} | "
                     f"{_fmt(family.get('reference_below_alpha'))} |")

    budget = report.get("budget", {})
    lines.extend(["", "## 開示", "",
                  f"- unstable 標本は除外せず、比較行の `unstable_counts` に全数を保持した。",
                  f"- retry は比較行の `retry_events` に一覧を保持した。",
                  f"- block1 と block2 のセル別中央値差は比較行の `block_effects` に保持した。",
                  f"- 効果量 (中央値差、確率優越 A、両セル CV) は JSON の `effect_sizes` に保持した。",
                  f"- 時間台帳: spent={_fmt(budget.get('spent_s'))}s / "
                  f"total={_fmt(budget.get('total_budget_s'))}s、"
                  f"retry={_fmt(budget.get('retry_spent_s'))}s。", "",
                  f"generated_at_head: `{_fmt(report.get('generated_at_head'))}`", ""])
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def generate_report(
        *, freeze_path: Path = ROOT / FREEZE_REL,
        budget_path: Path = ROOT / BUDGET_REL,
        output_root: str = "", report_dir: Optional[Path] = None,
        freeze_verify: Optional[Callable[[Path], Mapping]] = None,
        generated_at_head: Optional[str] = None,
) -> Tuple[Dict, Path, Path]:
    """report を JSON + Markdown へ原子的に書き出す。"""
    root = Path(output_root or repo_output_root())
    destination = report_dir or (root / REPORT_REL)
    report = build_report(
        freeze_path=freeze_path, budget_path=budget_path, output_root=str(root),
        freeze_verify=freeze_verify, generated_at_head=generated_at_head)
    json_path = destination / REPORT_JSON
    md_path = destination / REPORT_MD
    json_text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    _atomic_write(json_path, json_text)
    _atomic_write(md_path, render_markdown(report))
    return report, json_path, md_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path, default=ROOT / FREEZE_REL)
    parser.add_argument("--budget", type=Path, default=ROOT / BUDGET_REL)
    parser.add_argument("--output-root", default=repo_output_root(),
                        help="campaigns/ と reports/ を含む output root")
    parser.add_argument("--report-dir", type=Path,
                        help="省略時は <output-root>/reports/s1_direct_comparison")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        _report, json_path, md_path = generate_report(
            freeze_path=args.freeze, budget_path=args.budget,
            output_root=args.output_root, report_dir=args.report_dir)
    except Exception as exc:
        print(f"report 生成失敗: {exc}", file=sys.stderr)
        return 1
    print(f"generated: {json_path}")
    print(f"generated: {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
