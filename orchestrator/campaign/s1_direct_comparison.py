# -*- coding: utf-8 -*-
"""S-1 直接比較の計測実行 driver (統計・判定・report は扱わない)。

各 CLI 起動は develop / floor / block1 / block2 のいずれか 1 campaign だけを実行する。
freeze を照合してから、その schedule と cell 定義を唯一の入力として pipeline.evaluate を
直列に呼ぶ。性能標本は legacy verify + bench 1 round、開発相は legacy+S2 verify のみ。
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import math
import os
import re
import subprocess
import struct
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
ROOT = _ORCHESTRATOR.parent

from ..calibrator import perf_preflight as _perf_preflight  # noqa: E402
from . import (buildcache, condition_meaning_gate, env_contract, ident,  # noqa: E402
               source_digest, trigger_gate_binding, wal)
from .layout import CampaignLayout, campaign_layout, repo_output_root  # noqa: E402
from .model import CampaignConfig, Genome, STAGE_S1_SESSION  # noqa: E402
from .pipeline import EvalResult, PerfConfig  # noqa: E402
from . import pipeline  # noqa: E402
from .build_admission import (REVIEW_RECEIPT_SCHEMA,  # noqa: E402
                                      GeneratorId, ReviewId, build_run_context,
                                      verify_review_receipt)


ENV_TAG = "linux-baremetal"
CLOCKS_PER_US = 1800
NUMACTL = ["numactl", "--interleave=all"]
TOTAL_BUDGET_S = 43_200.0
RETRY_RESERVE_S = 7_200.0
MAX_RETRIES = 2
SESSION_STAGE = STAGE_S1_SESSION
FREEZE_REL = "output/s1-freeze/measurement_freeze.json"
BUDGET_REL = "output/s1-budget/time_ledger.json"
_PREPARE_CELL_CONFIGURATIONS: frozenset[str] = frozenset({
    "backoff_fixed_best",
    "ident_all",
    "p2_2_flag_opt",
    "sort_best",
    "stock_common",
    "system_gate",
})

# 性能 session: trace/perf build 数分 + legacy trace run 最大120秒
# (pipeline.TRACE_TIMEOUT_S) + verifier + bench 15秒 + settle を保守側へ丸める。
SESSION_WALL_UPPER_BOUND_S = 15 * 60.0
# develop は bench 無しだが legacy と S2 の2 verifyを通すため、別の大きい上界を置く。
DEVELOP_SESSION_WALL_UPPER_BOUND_S = 20 * 60.0

ROLE_TO_FREEZE = {
    "floor": "floor",
    "block1": "test_block_1",
    "block2": "test_block_2",
}
ROLE_TO_PHASE = {
    "develop": "develop",
    "floor": "floor",
    "block1": "block1",
    "block2": "block2",
}

EXIT_OK = 0
EXIT_INCOMPLETE = 1
EXIT_REFUSED = 2
EXIT_BUDGET = 3
EXIT_VERIFIER_RED = 4
EXIT_ORACLE_REJECT = 5

SESSION_RESULT_STATUSES = frozenset({
    "success", "abandoned", "verifier-red", "retryable", "oracle-reject",
})
TERMINAL_SESSION_STATUSES = frozenset({
    "success", "abandoned", "verifier-red", "oracle-reject",
})


def _unknown_session_status_message(field: str, status: object) -> str:
    """非信頼 status を再掲せず、固定説明と短縮 digest だけを返す。"""
    try:
        canonical = json.dumps(
            status, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        )
    except (TypeError, ValueError, OverflowError):
        canonical = f"<{type(status).__module__}.{type(status).__qualname__}>"
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    return f"{field} が未知 (sha256_12={digest})"


class DriverError(RuntimeError):
    """freeze・schedule・ledger・入力 schema の fail-closed 拒否。"""


class ScheduleDeviation(DriverError):
    """session ledger が凍結 schedule の prefix ではない。"""


class BudgetExhausted(DriverError):
    """通常枠または retry 専用枠が次の session の保守上界に満たない。"""


class _SortSwoOracleRejected(DriverError):
    """REJECT の sanitized oracle record を台帳境界まで運ぶ。"""

    def __init__(self, message: str, oracle_attempt: Mapping[str, object]):
        super().__init__(message)
        self.oracle_attempt = dict(oracle_attempt)


def _sort_swo_reject_attempt_record(result: object) -> Dict[str, object]:
    from .sort_swo_oracle import OracleStatus, SortSwoOracleResult

    if (type(result) is not SortSwoOracleResult
            or result.status is not OracleStatus.REJECT
            or result.finding is None):
        raise TypeError("oracle reject record requires exact REJECT with finding")
    out: Dict[str, object] = {
        "event": "sort-swo-oracle-attempt",
        "classification": "reject",
        "reason_code": result.finding.reason_code,
        "oracle_finding": result.finding.as_dict(),
        "oracle_contract_id": result.contract_id,
        "materialized_hole_sha256": result.materialized_hole_sha256,
        "proposal_sha256": result.proposal_sha256,
    }
    if result.receipt is not None:
        out["oracle_receipt"] = result.receipt.as_dict()
    return out


@dataclass(frozen=True)
class ScheduledCell:
    schedule_index: int
    campaign_role: str
    lap: int
    freeze_cell_id: str
    cell_id: str
    cell: Mapping


@dataclass(frozen=True)
class PreparedCell:
    genome: Genome
    src_token: str
    ccbench_dir: str
    cache_root: str
    oracle_attempt: Optional[Dict] = None
    condition_supply_records: Optional[
        tuple[condition_meaning_gate.ConditionArmRecord, ...]
    ] = None
    condition_meaning_records: Optional[
        tuple[condition_meaning_gate.ConditionArmRecord, ...]
    ] = None
    sort_oracle_contract_id: Optional[str] = None


_CONDITION_DEFAULTS = {
    "BACKOFF_FIXED": -1,
    "BACKOFF_NOINLINE": 0,
    "BACKOFF_TRIGGER_GATING": 0,
    "SORT_VARIANT": 0,
}


def _condition_macros(flags: Mapping[str, object]) -> frozenset[str]:
    return frozenset(set(flags) & set(condition_meaning_gate.DEFINE_SPECS))


def _condition_driver_id(configuration: str) -> str:
    if type(configuration) is not str or not configuration:
        raise DriverError("condition gate configuration が不正")
    return "orchestrator.campaign.s1_direct_comparison.prepare_cell"


def _condition_requests_for_flags(
        flags: Mapping[str, object], *, driver_id: str,
) -> tuple[condition_meaning_gate.DefineRequest, ...]:
    macros = _condition_macros(flags)
    unknown_defaults = macros - set(_CONDITION_DEFAULTS)
    if unknown_defaults:
        raise DriverError(
            f"condition gate default が未宣言: {sorted(unknown_defaults)!r}"
        )
    requests = []
    for macro in sorted(macros):
        value = flags[macro]
        requests.append(condition_meaning_gate.make_define_request(
            driver_id=driver_id, macro=macro, requested_value=value,
            default_value=_CONDITION_DEFAULTS[macro],
            stock_comparison=(macro == "BACKOFF_FIXED" and value == -1),
        ))
    return tuple(requests)


def _condition_request_digests_for_flags(
        flags: Mapping[str, object], *, driver_id: str,
) -> dict[str, str]:
    """Independently derive the exact request identity expected from a cell."""
    expected = {}
    for request in _condition_requests_for_flags(flags, driver_id=driver_id):
        _spec, _requested, _default, companions = (
            condition_meaning_gate._validate_define_request(request)
        )
        expected[request.macro] = condition_meaning_gate._request_digest(
            request, companions,
        )
    return expected


def _condition_meaning_declaration(
        macro: str, value: object,
) -> Optional[condition_meaning_gate.MeaningWitnessDeclaration]:
    if macro != "BACKOFF_FIXED" or type(value) is not int:
        return None
    if value == -1:
        meaning_case = condition_meaning_gate.MeaningCase(
            -1, None,
            expected_selected_branch=condition_meaning_gate.STOCK_ADAPTIVE_BRANCH,
        )
    elif value >= 0:
        bits = struct.pack(">d", float(value)).hex()
        meaning_case = condition_meaning_gate.MeaningCase(value, (bits, bits))
    else:
        return None
    return condition_meaning_gate.MeaningWitnessDeclaration(
        macro, (meaning_case,),
    )


def condition_gate_receipt(
        supply: tuple[condition_meaning_gate.ConditionArmRecord, ...],
        meaning: tuple[condition_meaning_gate.ConditionArmRecord, ...],
        admission: Optional[condition_meaning_gate.ConditionFamilyAdmission],
) -> Optional[dict[str, object]]:
    """Serialize the issued records with the admission that references them."""
    if admission is None:
        if supply or meaning:
            raise DriverError("condition gate record に対応する admission がない")
        return None
    return {
        "supply_records": [json.loads(record.canonical_json()) for record in supply],
        "meaning_records": [json.loads(record.canonical_json()) for record in meaning],
        "admission": json.loads(admission.canonical_json()),
    }


def _condition_records_for_genome(
        source_root: str, genome: Genome, *, driver_id: str, use_class: str,
        cxx: str, stock_root: Optional[str] = None) -> tuple[
            tuple[condition_meaning_gate.ConditionArmRecord, ...],
            tuple[condition_meaning_gate.ConditionArmRecord, ...],
        ]:
    requests = _condition_requests_for_flags(genome.flags, driver_id=driver_id)
    if not requests:
        return (), ()
    captured = condition_meaning_gate.capture_define_inputs(
        source_root, stock_root=stock_root,
    )
    supply_records = []
    meaning_records = []
    for request in requests:
        declaration = condition_meaning_gate.declare_define_runtime_meaning(
            request,
        )
        if declaration is None:
            declaration = _condition_meaning_declaration(
                request.macro, request.requested_value,
            )
        supply_records.append(
            condition_meaning_gate.evaluate_define_supply_effectuation(
                captured, request=request, cxx=cxx, cmake="cmake",
            )
        )
        meaning_records.append(
            condition_meaning_gate.evaluate_define_runtime_meaning(
                captured, request=request, declaration=declaration, cxx=cxx,
            )
        )
    admission = condition_meaning_gate.require_condition_gate_family(
        supply_records, meaning_records, use_class=use_class,
    )
    if not admission.admitted:
        reasons = ",".join(
            f"{record.macro}:{record.arm}:{record.reason_code}"
            for record in (*supply_records, *meaning_records)
            if record.terminal_status != "green"
        )
        rejection = f"condition gate rejected prepared cell: {reasons}"
        for record in (*supply_records, *meaning_records):
            if record.terminal_status == "green":
                continue
            try:
                # Reuse D1912's byte bound, quoting and truncation digest by
                # rendering the detail as one diagnostic argument.
                detail = condition_meaning_gate._bounded_process_argv_detail(
                    [record.evidence.get("detail", "<detail unavailable>")],
                )
                rejection += (
                    f"\n{record.macro}:{record.arm}:{record.reason_code}: "
                    f"evidence.detail={detail}"
                )
            except Exception:
                rejection += "\n<condition detail unavailable>"
        raise DriverError(rejection)
    return tuple(supply_records), tuple(meaning_records)


def require_returned_condition_evidence(
        value: object, *, expected_request_digests: Mapping[str, str], use_class: str,
        label: str,
        expected_records: Optional[tuple[
            tuple[condition_meaning_gate.ConditionArmRecord, ...],
            tuple[condition_meaning_gate.ConditionArmRecord, ...],
        ]] = None) -> Optional[condition_meaning_gate.ConditionFamilyAdmission]:
    """Validate both records on an injected callable's returned object."""
    supply = getattr(value, "condition_supply_records", None)
    meaning = getattr(value, "condition_meaning_records", None)
    if type(supply) is not tuple or type(meaning) is not tuple:
        raise DriverError(f"{label} が condition gate の両 record を返さなかった")
    if type(expected_request_digests) is not dict:
        raise DriverError(f"{label} の期待 request digest が不正")

    def observed_requests(records, arm):
        if any(type(record) is not condition_meaning_gate.ConditionArmRecord
               for record in records):
            raise DriverError(f"{label} の {arm} record 型が不正")
        rows = [(record.macro, record.request_digest) for record in records]
        if len({macro for macro, _digest in rows}) != len(rows):
            raise DriverError(f"{label} の {arm} request が重複")
        return dict(rows)

    if (observed_requests(supply, "supply") != expected_request_digests
            or observed_requests(meaning, "meaning") != expected_request_digests):
        raise DriverError(f"{label} の condition gate request digest が入力と不一致")
    if not expected_request_digests:
        return None
    try:
        admission = condition_meaning_gate.require_condition_gate_family(
            supply, meaning, use_class=use_class,
        )
    except condition_meaning_gate.ConditionMeaningGateError as exc:
        raise DriverError(
            f"{label} の condition gate record が不正: {exc.reason_code}"
        ) from exc
    if not admission.admitted:
        raise DriverError(f"{label} の condition gate admission が拒否")
    if expected_records is not None:
        expected_supply, expected_meaning = expected_records
        if ([record.record_id for record in supply]
                != [record.record_id for record in expected_supply]
                or [record.record_id for record in meaning]
                != [record.record_id for record in expected_meaning]):
            raise DriverError(f"{label} の condition gate record が準備済み evidence と不一致")
    return admission


def _iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _load_json_object(path: Path) -> Dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DriverError(f"JSON を読めない: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DriverError(f"JSON top-level が object でない: {path}")
    return value


def load_verified_freeze(
        freeze_path: Path = ROOT / FREEZE_REL,
        verify_document: Optional[Callable[[Mapping], None]] = None) -> Dict:
    """freeze 本文を読み、B1 の公開 verify_document 契約だけを呼ぶ。"""
    document = _load_json_object(freeze_path)
    if verify_document is None:
        try:
            from . import s1_measurement_freeze as freeze_module
        except ImportError as exc:
            raise DriverError("s1_measurement_freeze を import できない") from exc
        verify_document = freeze_module.verify_document
    verify_document(document)
    return document


def _operating_point(document: Mapping) -> Dict[str, int]:
    expected = {"RECORDS": 1_000_000, "THREADS": 48, "EXTIME": 3, "REPS": 5}
    actual = document.get("operating_point")
    if actual != expected:
        raise DriverError(f"freeze operating_point が事前登録値と不一致: {actual!r}")
    return expected


def _workload_flags(document: Mapping) -> Dict[str, Dict[str, str]]:
    """freeze の workload→rratio 対応を読み、旧 schema や暗黙の既定を拒否する。"""
    actual = document.get("workload_flags")
    expected_workloads = {"balanced", "write-heavy", "read-heavy"}
    if not isinstance(actual, dict) or set(actual) != expected_workloads:
        raise DriverError("freeze workload_flags が3 workload object でない")
    out: Dict[str, Dict[str, str]] = {}
    for workload in sorted(expected_workloads):
        flags = actual.get(workload)
        if not isinstance(flags, dict) or set(flags) != {"ycsb_rratio"}:
            raise DriverError(f"freeze workload_flags.{workload} schema が不一致")
        rratio = flags.get("ycsb_rratio")
        if (not isinstance(rratio, str) or not rratio.isdigit()
                or not 0 <= int(rratio) <= 100):
            raise DriverError(
                f"freeze workload_flags.{workload}.ycsb_rratio が0..100の文字列でない")
        # skew/rmw は全 workload 共通の固定動作点。比較の意味を決める rratio 対応だけを
        # freeze から逐語使用し、records は PerfConfig.records の専権なので含めない。
        out[workload] = {
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": rratio, "ycsb_rmw": "0",
        }
    return out


def _display_cell_id(cell: Mapping) -> str:
    workload = cell.get("workload")
    configuration = cell.get("configuration")
    if not isinstance(workload, str) or not isinstance(configuration, str):
        raise DriverError("freeze cell の workload/configuration が文字列でない")
    return f"{workload}/{configuration}"


def schedule_for_role(document: Mapping, role: str) -> List[ScheduledCell]:
    """freeze の順序を平坦化する。develop だけは cells の凍結順を 1 回使う。"""
    cells = document.get("cells")
    if not isinstance(cells, dict) or len(cells) != 18:
        raise DriverError("freeze cells が18セル object でない")
    if role == "develop":
        rounds: Iterable[Sequence[str]] = [list(cells)]
    else:
        freeze_role = ROLE_TO_FREEZE.get(role)
        schedule = document.get("schedule")
        if freeze_role is None or not isinstance(schedule, dict):
            raise DriverError(f"未知の campaign role: {role}")
        rounds = schedule.get(freeze_role)
        if not isinstance(rounds, list):
            raise DriverError(f"freeze schedule に campaign がない: {freeze_role}")

    out: List[ScheduledCell] = []
    for lap, order in enumerate(rounds, 1):
        if not isinstance(order, list) or len(order) != 18:
            raise DriverError(f"freeze schedule lap が18セルでない: role={role} lap={lap}")
        for freeze_cell_id in order:
            if not isinstance(freeze_cell_id, str) or freeze_cell_id not in cells:
                raise DriverError(f"freeze schedule が未知 cell を参照: {freeze_cell_id!r}")
            cell = cells[freeze_cell_id]
            if not isinstance(cell, dict):
                raise DriverError(f"freeze cell が object でない: {freeze_cell_id}")
            out.append(ScheduledCell(
                schedule_index=len(out), campaign_role=role, lap=lap,
                freeze_cell_id=freeze_cell_id, cell_id=_display_cell_id(cell), cell=cell))
    return out


def config_for(document: Mapping, role: str) -> CampaignConfig:
    """4 campaign を role が search_config に焼かれた別 identity にする。"""
    if role not in ROLE_TO_PHASE:
        raise DriverError(f"未知の campaign role: {role}")
    pin = document.get("ccbench_pin")
    schedule_hash = document.get("schedule_hash")
    if not isinstance(pin, str) or not isinstance(schedule_hash, str):
        raise DriverError("freeze の ccbench_pin/schedule_hash が文字列でない")
    verify_mode = (pipeline.VERIFY_LEGACY_PLUS_S2
                   if role == "develop" else pipeline.LEGACY_TAG)
    from .sort_swo_oracle import ORACLE_CONTRACT_ID
    cfg = CampaignConfig(
        spec_slug=f"s1-direct-{role}", search_tag="direct-comparison",
        spec_content=("S-1 登録追試の計測実行系。freeze の18セルと固定 schedule を "
                      "pipeline.evaluate の COMMIT 唯一経路で実行する。"),
        ccbench_commit=pin,
        search_config={
            "campaign_role": role,
            "schedule_hash": schedule_hash,
            "verify": verify_mode,
            "sort_swo_oracle": ORACLE_CONTRACT_ID,
        },
        # v1 は prepare_cell 実体化バグを含む実行系で走ったため identity を分離する。
        trial="s1-direct-v2",
    )
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    cfg = ident.bind_admission_policy(cfg, context.policy)
    return ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))


def layout_for(document: Mapping, role: str, output_root: str = "") -> CampaignLayout:
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    cfg = ident.bind_admission_policy(config_for(document, role), context.policy)
    return campaign_layout(str(ident.campaign_id(cfg)), output_root=output_root)


def _ensure_campaign(
        cfg: CampaignConfig, layout: CampaignLayout, *, admission_policy,
) -> wal.WalTailRepairResult:
    layout.ensure()
    return ident.ensure_resumable_wal(
        cfg, layout, admission_policy=admission_policy,
    )


def session_events_from_records(records: Sequence) -> List[Dict]:
    """既読 WAL records から S-1 session event を構築する純関数。"""
    out: List[Dict] = []
    for record in records:
        if record.stage != SESSION_STAGE:
            continue
        if not isinstance(record.payload, dict):
            raise ScheduleDeviation("s1-session payload が object でない")
        event = dict(record.payload)
        event.setdefault("wal_ts", record.ts)
        out.append(event)
    return out


def read_session_ledger(layout: CampaignLayout) -> List[Dict]:
    """S-1 session event の読み口。B2b は WAL の物理表現をここから先へ漏らさない。"""
    records, truncated_tail = wal.read_records_checked(layout)
    if truncated_tail:
        raise ScheduleDeviation(
            "s1-session WAL に newline 終端の無い tail がある")
    return session_events_from_records(records)


def _append_event(layout: CampaignLayout, event: Mapping) -> None:
    variant = event.get("variant")
    wal.log(layout, str(variant or "s1-campaign"), SESSION_STAGE, ENV_TAG, dict(event))


def _base_event(item: ScheduledCell, variant: str, attempt: int) -> Dict:
    return {
        "event": "session-start",
        "schedule_index": item.schedule_index,
        "campaign_role": item.campaign_role,
        "lap": item.lap,
        "cell_id": item.cell_id,
        "variant": variant,
        "ts": _iso_now(),
        "attempt": attempt,
    }


def _record_deviation(layout: CampaignLayout, role: str, message: str) -> None:
    _append_event(layout, {
        "event": "deviation", "campaign_role": role,
        "ts": _iso_now(), "reason": message,
    })


def validate_session_ledger(
        layout: CampaignLayout, schedule: Sequence[ScheduledCell]) -> int:
    """ledger が schedule の重複なし prefix で、各開始が終端へ至るか検査する。

    戻り値は次に実行する schedule_index。最後の attempt が start のままなら同じ index を
    retry 候補として返す。順序逸脱・重複・prefix 内欠落は自動修復しない。
    """
    return validate_session_events(read_session_ledger(layout), schedule)


def validate_session_events(
        events: Sequence[Mapping], schedule: Sequence[ScheduledCell]) -> int:
    """既に構築済みの events が schedule prefix 契約を満たすか検査する純関数。"""
    prior_deviation = next((e for e in events if e.get("event") == "deviation"), None)
    if prior_deviation is not None:
        raise ScheduleDeviation(
            f"当該 campaign は既に逸脱記録済み: {prior_deviation.get('reason')}")
    for event in events:
        status = event.get("status")
        if (event.get("event") == "session-result"
                and (type(status) is not str or status not in SESSION_RESULT_STATUSES)):
            raise ScheduleDeviation(
                _unknown_session_status_message("session-result.status", status))
    starts = [e for e in events if e.get("event") == "session-start"]
    initial = [e for e in starts if e.get("attempt") == 0]
    for expected_index, event in enumerate(initial):
        if expected_index >= len(schedule):
            raise ScheduleDeviation("session-start が freeze schedule 長を超えている")
        item = schedule[expected_index]
        actual = event.get("schedule_index")
        if actual != expected_index:
            raise ScheduleDeviation(
                f"schedule_index 順序逸脱/重複/欠落: expected={expected_index} actual={actual}")
        for key, expected in (("campaign_role", item.campaign_role), ("lap", item.lap),
                              ("cell_id", item.cell_id)):
            if event.get(key) != expected:
                raise ScheduleDeviation(
                    f"session-start {expected_index} の {key} 不一致: "
                    f"expected={expected!r} actual={event.get(key)!r}")

    starts_by_index: Dict[int, List[Dict]] = {}
    for event in starts:
        index = event.get("schedule_index")
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            raise ScheduleDeviation("session-start.schedule_index が非負整数でない")
        starts_by_index.setdefault(index, []).append(event)
    if set(starts_by_index) != set(range(len(initial))):
        raise ScheduleDeviation("session-start index が重複・欠落を含む prefix になっていない")
    for index, index_starts in starts_by_index.items():
        attempts = [e.get("attempt") for e in index_starts]
        if (any(isinstance(a, bool) or not isinstance(a, int) or a < 0 for a in attempts)
                or sorted(attempts) != list(range(max(attempts) + 1))):
            raise ScheduleDeviation(
                f"schedule_index={index} の attempt が重複または欠落: {attempts}")
        if index >= len(schedule):
            raise ScheduleDeviation(f"schedule_index={index} が freeze schedule 長を超える")
        item = schedule[index]
        for event in index_starts:
            for key, expected in (("campaign_role", item.campaign_role), ("lap", item.lap),
                                  ("cell_id", item.cell_id)):
                if event.get(key) != expected:
                    raise ScheduleDeviation(
                        f"session-start {index} attempt={event.get('attempt')} の {key} 不一致")

    by_index: Dict[int, List[Dict]] = {}
    for event in events:
        index = event.get("schedule_index")
        if isinstance(index, int) and not isinstance(index, bool):
            by_index.setdefault(index, []).append(event)
    next_index = 0
    while next_index < len(initial):
        terminal = [e for e in by_index.get(next_index, [])
                    if e.get("event") == "session-result"
                    and e.get("status") in TERMINAL_SESSION_STATUSES]
        if len(terminal) > 1:
            raise ScheduleDeviation(f"schedule_index={next_index} の終端結果が重複")
        if not terminal:
            break
        next_index += 1
    if any(i > next_index for i in by_index if any(
            e.get("event") == "session-result" and
            e.get("status") in TERMINAL_SESSION_STATUSES
            for e in by_index[i])):
        raise ScheduleDeviation("前方 session の終端が欠落したまま後方 session が終端")
    return next_index


def _empty_budget() -> Dict:
    return {"total_budget_s": int(TOTAL_BUDGET_S), "spent_s": 0.0, "entries": []}


def read_budget(path: Path) -> Dict:
    if not path.exists():
        return _empty_budget()
    doc = _load_json_object(path)
    if set(doc) != {"total_budget_s", "spent_s", "entries"}:
        raise DriverError("time_ledger top-level schema が不一致")
    if doc.get("total_budget_s") != int(TOTAL_BUDGET_S):
        raise DriverError("time_ledger total_budget_s が43200でない")
    spent = doc.get("spent_s")
    entries = doc.get("entries")
    if (isinstance(spent, bool) or not isinstance(spent, (int, float))
            or not math.isfinite(float(spent)) or spent < 0 or not isinstance(entries, list)):
        raise DriverError("time_ledger spent_s/entries が不正")
    total = 0.0
    required = {"campaign_role", "started_iso", "wall_s", "phase", "note"}
    allowed_phases = {"develop", "floor", "block1", "block2",
                      "verify-calibration", "verify-phase"}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != required:
            raise DriverError("time_ledger entry schema が不一致")
        wall_s = entry.get("wall_s")
        if (isinstance(wall_s, bool) or not isinstance(wall_s, (int, float))
                or not math.isfinite(float(wall_s)) or wall_s < 0):
            raise DriverError("time_ledger entry.wall_s が不正")
        if entry.get("phase") not in allowed_phases:
            raise DriverError("time_ledger entry.phase が未知")
        if (not isinstance(entry.get("campaign_role"), str)
                or not isinstance(entry.get("started_iso"), str)
                or not isinstance(entry.get("note"), str)):
            raise DriverError("time_ledger entry の文字列フィールドが不正")
        total += float(wall_s)
    if not math.isclose(float(spent), total, rel_tol=0.0, abs_tol=1e-6):
        raise DriverError(f"time_ledger spent_s と entries 合計が不一致: {spent} != {total}")
    if float(spent) > TOTAL_BUDGET_S + 1e-6:
        raise DriverError("time_ledger が総予算12hを超過済み")
    return doc


def _atomic_write_json(path: Path, document: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(document, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
        dfd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def append_budget_entry(
        path: Path, *, role: str, started_iso: str, wall_s: float,
        phase: str, note: str) -> Dict:
    document = read_budget(path)
    entry = {"campaign_role": role, "started_iso": started_iso,
             "wall_s": float(wall_s), "phase": phase, "note": note}
    document["entries"].append(entry)
    document["spent_s"] = float(document["spent_s"]) + float(wall_s)
    if document["spent_s"] > TOTAL_BUDGET_S + 1e-6:
        raise BudgetExhausted("entry 追加で総予算12hを超える")
    _atomic_write_json(path, document)
    return document


def _retry_spent(document: Mapping) -> float:
    return sum(float(e["wall_s"]) for e in document["entries"]
               if str(e.get("note", "")).startswith("machine-failure-retry:"))


_SESSION_BUDGET_NOTE_RE = re.compile(
    r"^(?:session:|machine-failure-retry:) "
    r"index=[0-9]+ attempt=[0-9]+ status=([^ ]+) reason="
)


def _session_status_from_budget_note(note: str) -> Optional[str]:
    """現行の session note 先頭だけから status を復元する。reason は解析しない。"""
    match = _SESSION_BUDGET_NOTE_RE.match(note)
    if match is None:
        if note.startswith(("session:", "machine-failure-retry:")):
            raise DriverError("time_ledger session note の書式が不正")
        return None
    status = match.group(1)
    if status not in SESSION_RESULT_STATUSES:
        raise DriverError(
            _unknown_session_status_message("time_ledger session status", status))
    return status


def _terminal_exit_code(budget_path: Path, events: Sequence[Mapping]) -> Optional[int]:
    """budget と local ledger を集約し、強い終端を一度だけ選ぶ。"""
    statuses = {
        status
        for entry in read_budget(budget_path)["entries"]
        if (status := _session_status_from_budget_note(entry["note"])) is not None
    }
    for event in events:
        if event.get("event") != "session-result":
            continue
        status = event.get("status")
        if type(status) is not str or status not in SESSION_RESULT_STATUSES:
            raise ScheduleDeviation(
                _unknown_session_status_message("session-result.status", status))
        statuses.add(status)
    if "verifier-red" in statuses:
        return EXIT_VERIFIER_RED
    if "oracle-reject" in statuses:
        return EXIT_ORACLE_REJECT
    return None


def assert_budget_available(path: Path, required_s: float, *, retry: bool) -> None:
    document = read_budget(path)
    spent = float(document["spent_s"])
    retry_spent = _retry_spent(document)
    regular_spent = spent - retry_spent
    total_remaining = TOTAL_BUDGET_S - spent
    lane_remaining = ((RETRY_RESERVE_S - retry_spent) if retry
                      else ((TOTAL_BUDGET_S - RETRY_RESERVE_S) - regular_spent))
    if min(total_remaining, lane_remaining) + 1e-9 < required_s:
        lane = "retry専用2h枠" if retry else "通常10h枠"
        raise BudgetExhausted(
            f"{lane}の残りが session 保守上界に不足: "
            f"remaining={min(total_remaining, lane_remaining):.3f}s "
            f"required={required_s:.3f}s")


def _session_wall_upper_bound_s(role: str) -> float:
    return (DEVELOP_SESSION_WALL_UPPER_BOUND_S
            if role == "develop" else SESSION_WALL_UPPER_BOUND_S)


@contextlib.contextmanager
def prepare_cell(
        cell: Mapping, ccbench_pin: str, *, cxx: str,
        condition_use_class: str = "floor",
        oracle_dependency_root: Optional[os.PathLike[str] | str] = None,
        oracle_compiler: Optional[os.PathLike[str] | str] = None,
        oracle_phase_marker: Optional[Callable[[], None]] = None):
    """freeze variant の flags/code を使い、使い捨て worktree に該当点を実体化する。"""
    from . import patchharness
    from . import p3_s4_loop as loop_axis
    from . import p3_s4_loop_sort as sort_axis
    from . import axis_trigger_gating as gate_axis
    from . import p3_s4_loop_trigger_gating as gate_loop

    variant = cell.get("variant")
    configuration = cell.get("configuration")
    if not isinstance(variant, dict) or not isinstance(configuration, str):
        raise DriverError("freeze cell.variant/configuration が不正")
    if configuration not in _PREPARE_CELL_CONFIGURATIONS:
        raise DriverError(f"未知の freeze configuration: {configuration!r}")
    flags = variant.get("flags")
    if not isinstance(flags, dict) or not flags:
        raise DriverError(f"freeze variant.flags が不正: {configuration}")
    clean_flags: Dict[str, int] = {}
    for name, value in flags.items():
        if (not isinstance(name, str) or isinstance(value, bool)
                or not isinstance(value, int)):
            raise DriverError(f"freeze variant flag が name=int でない: {name!r}={value!r}")
        clean_flags[name] = value
    genome = Genome("silo", clean_flags)
    fixed_sub = str(ROOT / "external" / "ccbench")
    cache_root = str(Path(repo_output_root()) / "s1-build-cache")

    with contextlib.ExitStack() as stack:
        sub = stack.enter_context(patchharness.checkout(ccbench_pin, base_dir=fixed_sub))
        stock_root = None
        if any(
                macro == "BACKOFF_FIXED" and value == -1
                or value == _CONDITION_DEFAULTS.get(macro)
                for macro, value in clean_flags.items()
                if macro in _CONDITION_DEFAULTS):
            stock_root = stack.enter_context(
                patchharness.checkout(ccbench_pin, base_dir=fixed_sub)
            )
        quarantine_implementation: Optional[str] = None
        marker_id = source_rel = quarantine_patch_path = None
        patch_only_path = None
        oracle_attempt: Optional[Dict] = None
        sort_oracle_contract_id: Optional[str] = None
        if configuration in {"system_gate", "ident_all"}:
            quarantine_implementation = variant.get("gate_predicate")
            if (not isinstance(quarantine_implementation, str)
                    or not quarantine_implementation.strip()):
                raise DriverError(f"{configuration} の gate_predicate がない")
            if not trigger_gate_binding.is_canonical_predicate(
                    quarantine_implementation):
                raise DriverError("freeze gate_predicate が正準集合外")
            forbidden = gate_loop.check_syntax_contract(quarantine_implementation)
            if forbidden:
                raise DriverError(f"freeze gate_predicate が構文契約違反: {forbidden}")
            marker_id, source_rel = gate_axis.MARKER_ID, gate_axis.SOURCE_REL
            quarantine_patch_path = ROOT / "patches" / gate_axis.TEMPLATE_PATCH
        elif configuration == "sort_best":
            quarantine_implementation = variant.get("comparator")
            if (not isinstance(quarantine_implementation, str)
                    or not quarantine_implementation.strip()):
                raise DriverError("sort_best の comparator がない")
            marker_id, source_rel = sort_axis.MARKER_ID, sort_axis.SOURCE_REL
            quarantine_patch_path = ROOT / sort_axis.TEMPLATE_PATCH
        elif configuration == "backoff_fixed_best":
            value = variant.get("backoff_us")
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise DriverError("backoff_fixed_best.backoff_us が非負整数でない")
            if clean_flags.get("BACKOFF_FIXED") != value:
                raise DriverError(
                    "backoff_fixed_best の backoff_us と flags.BACKOFF_FIXED が不一致")
            # 静的値は CMake flag が選ぶ骨格枝で実現する。EVOLVE-BLOCK は置換しない。
            patch_only_path = ROOT / loop_axis.TEMPLATE_PATCH

        if quarantine_implementation is not None:
            assert (quarantine_patch_path is not None and marker_id is not None
                    and source_rel is not None)
            stack.enter_context(patchharness.applied(
                str(quarantine_patch_path), ccbench_pin, ccbench_dir=sub))
            result, _base, _edited, _diff = loop_axis.quarantine(
                sub, quarantine_implementation, marker_id=marker_id,
                source_rel=source_rel, write=True)
            if not result.passed:
                raise DriverError(
                    f"freeze variant の diff 検疫不通過: {configuration}: {result.reason}")
            if configuration == "sort_best":
                from .sort_swo_oracle import (
                    ORACLE_CONTRACT_ID,
                    OracleStatus,
                    SortSwoOracleResult,
                    SortSwoOracleUnavailable,
                    attempt_record,
                    check_materialized_sort_swo,
                    resolve_oracle_environment,
                )
                oracle_environment = resolve_oracle_environment(
                    sub,
                    compiler=oracle_compiler,
                    dependency_root=oracle_dependency_root,
                )
                oracle = check_materialized_sort_swo(
                    _edited,
                    marker_id=marker_id,
                    proposal_source=quarantine_implementation,
                    environment=oracle_environment,
                    phase_marker=oracle_phase_marker,
                )
                if (type(oracle) is not SortSwoOracleResult
                        or type(oracle.status) is not OracleStatus):
                    raise DriverError("sort_best SWO oracle が閉じた契約外の値を返した")
                if oracle.contract_id != ORACLE_CONTRACT_ID:
                    raise DriverError("sort_best SWO oracle contract_id が不一致")
                if oracle.status is OracleStatus.UNAVAILABLE:
                    raise SortSwoOracleUnavailable(oracle)
                if oracle.status is OracleStatus.REJECT:
                    assert oracle.finding is not None
                    raise _SortSwoOracleRejected(
                        f"sort_best comparator が SWO oracle 不通過: "
                        f"{oracle.finding.reason_code}",
                        _sort_swo_reject_attempt_record(oracle),
                    )
                if oracle.status is not OracleStatus.PASS:
                    raise DriverError("sort_best SWO oracle が未知 status を返した")
                sort_oracle_contract_id = oracle.contract_id
                oracle_attempt = attempt_record(oracle)
        elif patch_only_path is not None:
            stack.enter_context(patchharness.applied(
                str(patch_only_path), ccbench_pin, ccbench_dir=sub))
        condition_supply_records, condition_meaning_records = (
            _condition_records_for_genome(
                sub, genome,
                driver_id=_condition_driver_id(configuration),
                use_class=condition_use_class, cxx=cxx, stock_root=stock_root,
            )
        )
        # The materializer boundary re-resolves and validates full SourceEvidence.
        # Preparation only needs the stable variant token for scheduling/identity.
        if sort_oracle_contract_id is not None:
            src_token = source_digest.resolve_evidence(
                genome, ccbench_pin, ccbench_dir=sub, cxx=cxx,
                sort_oracle_contract_id=sort_oracle_contract_id,
            ).src_token
        else:
            src_token = source_digest.resolve(
                genome, ccbench_pin, ccbench_dir=sub, cxx=cxx,
            )
        yield PreparedCell(
            genome=genome, src_token=src_token,
            ccbench_dir=sub, cache_root=cache_root,
            oracle_attempt=oracle_attempt,
            condition_supply_records=condition_supply_records,
            condition_meaning_records=condition_meaning_records,
            sort_oracle_contract_id=sort_oracle_contract_id,
        )


def _abort_payload(layout: CampaignLayout, variant: str) -> Dict:
    all_records, truncated_tail = wal.read_records_checked(layout)
    if truncated_tail:
        raise DriverError("S-1 WAL に newline 終端の無い tail がある")
    records = [r.payload for r in all_records
               if r.variant == variant and r.stage == "abort"]
    return dict(records[-1]) if records else {}


def _result_classification(result: EvalResult, layout: CampaignLayout) -> tuple[str, str]:
    if result.certified and not result.aborted:
        return "success", "certified"
    payload = _abort_payload(layout, result.variant)
    reason = str(payload.get("reason") or getattr(result, "abort_reason", "") or "abort")
    if payload.get("verify") is not None or (result.verdict and result.verdict != "serializable"):
        return "verifier-red", reason
    # bench-probe-error / verify-probe-error は競合検知 pgrep の一時故障で、環境非シグナル
    # ゆえ既知の retry 可能集合に含める (B-3/D-3: abandoned 化して retry 枠を捨てない)。
    if reason in {"build-error", "trace-run-nonzero-exit", "trace-timeout",
                  "bench-no-throughput", "bench-cv-undefined",
                  "bench-probe-error", "verify-probe-error"}:
        return "retryable", reason
    return "abandoned", reason


def _is_transient_prepare_failure(exc: BaseException) -> bool:
    """prepare のうち OS/subprocess の一時故障だけを閉じた retry 対象にする。"""
    current: Optional[BaseException] = exc
    seen = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        from .sort_swo_oracle import SortSwoOracleUnavailable
        if isinstance(current, (OSError, subprocess.SubprocessError,
                                SortSwoOracleUnavailable)):
            return True
        current = current.__cause__ or current.__context__
    return False


def _attempts_for(events: Sequence[Mapping], index: int) -> int:
    attempts = [e.get("attempt") for e in events
                if e.get("event") == "session-start" and e.get("schedule_index") == index]
    if not attempts:
        return 0
    if any(isinstance(a, bool) or not isinstance(a, int) or a < 0 for a in attempts):
        raise ScheduleDeviation(f"schedule_index={index} の attempt が不正")
    if sorted(attempts) != list(range(max(attempts) + 1)):
        raise ScheduleDeviation(f"schedule_index={index} の attempt が重複または欠落")
    return max(attempts) + 1


def run_role(
        role: str, *, dry_run: bool = False,
        freeze_path: Path = ROOT / FREEZE_REL,
        budget_path: Path = Path(repo_output_root()) / "s1-budget" / "time_ledger.json",
        output_root: str = "",
        verify_document: Optional[Callable[[Mapping], None]] = None,
        evaluate_fn: Optional[Callable] = None,
        prepare_cell_fn: Callable = prepare_cell,
        single_tenant_fn: Optional[Callable[[], None]] = None,
        monotonic: Callable[[], float] = time.monotonic,
        log: Callable[[str], None] = print) -> int:
    """1 CLI process = 1 campaign role。注入点は subprocess 無しの positive control 用。"""
    process_started = monotonic()
    document = load_verified_freeze(freeze_path, verify_document=verify_document)
    point = _operating_point(document)
    workload_flags = _workload_flags(document)
    schedule = schedule_for_role(document, role)
    condition_use_class = "raw" if role == "develop" else "certified-selection"
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    authorization_contract = env_contract.authorize(ENV_TAG)
    authorized_contract = pipeline.execution_guard.require_certified_writer_authorization(
        authorization_contract,
        env_tag=ENV_TAG,
        clocks_per_us=CLOCKS_PER_US,
        numactl=NUMACTL,
    )
    _, cxx = buildcache.compilers_for_current_site()
    cfg = ident.bind_admission_policy(config_for(document, role), build_context.policy)
    cfg = ident.bind_environment_contract(cfg, authorized_contract)
    layout = campaign_layout(str(ident.campaign_id(cfg)), output_root=output_root)

    if dry_run:
        # dry-run は checked reader の refusal を返すが、repair/receipt/lock 作成はしない。
        next_index = validate_session_ledger(layout, schedule)
        log(f"dry-run: role={role} sessions={len(schedule)} next={next_index} schedule照合済み")
        return EXIT_OK

    perf_preflight_receipt = _perf_preflight.probe_perf_availability()
    use_perf = _perf_preflight.use_perf_from_receipt(perf_preflight_receipt)
    perf_evaluate_kwargs = {}
    if not use_perf:
        perf_evaluate_kwargs = {
            "use_perf": False,
            "perf_preflight_receipt": perf_preflight_receipt,
        }

    if single_tenant_fn is None:
        from .p2_2 import _assert_single_tenant
        single_tenant_fn = _assert_single_tenant
    try:
        repair = _ensure_campaign(
            cfg, layout, admission_policy=build_context.policy,
        )
        if repair.status == "repaired":
            log("S-1 WAL tail repair: " + json.dumps({
                "status": repair.status,
                "original_size": repair.original_size,
                "final_size": repair.final_size,
                "removed_bytes": repair.removed_bytes,
                "removed_sha256": repair.removed_sha256,
                "preview": repair.preview,
                "receipt_path": repair.receipt_path,
            }, ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        append_budget_entry(
            budget_path, role=role, started_iso=_iso_now(),
            wall_s=max(0.0, monotonic() - process_started), phase=ROLE_TO_PHASE[role],
            note=f"campaign-overhead: preflight-failure {type(exc).__name__}: {exc}")
        raise
    try:
        next_index = validate_session_ledger(layout, schedule)
    except ScheduleDeviation as exc:
        if not any(e.get("event") == "deviation" for e in read_session_ledger(layout)):
            _record_deviation(layout, role, str(exc))
        append_budget_entry(
            budget_path, role=role, started_iso=_iso_now(), wall_s=0.0,
            phase=ROLE_TO_PHASE[role], note=f"schedule-deviation: {exc}")
        raise
    existing = read_session_ledger(layout)
    terminal_exit = _terminal_exit_code(budget_path, existing)
    if terminal_exit is not None:
        return terminal_exit
    try:
        single_tenant_fn()
    except Exception as exc:
        append_budget_entry(
            budget_path, role=role, started_iso=_iso_now(),
            wall_s=max(0.0, monotonic() - process_started), phase=ROLE_TO_PHASE[role],
            note=f"campaign-overhead: preflight-failure {type(exc).__name__}: {exc}")
        raise
    if not any(e.get("event") == "campaign-start" for e in existing):
        _append_event(layout, {"event": "campaign-start", "campaign_role": role,
                               "ts": _iso_now()})

    perf_by_workload: Dict[str, PerfConfig] = {}
    for workload, flags in workload_flags.items():
        perf_by_workload[workload] = PerfConfig(
            records=point["RECORDS"], threads=point["THREADS"],
            workload=dict(flags), extime=point["EXTIME"], reps=point["REPS"])

    incomplete = False
    budget_stopped = False
    verifier_red = False
    oracle_reject = False
    process_attempt_wall = 0.0
    try:
        index = next_index
        while index < len(schedule):
            item = schedule[index]
            workload = item.cell.get("workload")
            if workload not in perf_by_workload:
                raise DriverError(f"freeze cell workload が未知: {workload!r}")
            perf = perf_by_workload[workload]
            events = read_session_ledger(layout)
            attempt = _attempts_for(events, index)
            if attempt > 0:
                if attempt > MAX_RETRIES:
                    _append_event(layout, {**_base_event(item, "unknown", attempt - 1),
                                           "event": "session-result", "status": "abandoned",
                                           "reason": "interrupted-before-result retry上限超過"})
                    incomplete = True
                    index += 1
                    continue
                if not any(e.get("event") == "retry" and e.get("retry_of") == index
                           and e.get("attempt") == attempt for e in events):
                    retryable = [e for e in events
                                 if e.get("event") == "session-result"
                                 and e.get("schedule_index") == index
                                 and e.get("status") == "retryable"]
                    retry_reason = (retryable[-1].get("reason") if retryable
                                    else "interrupted-before-result")
                    _append_event(layout, {
                        "event": "retry", "retry_of": index, "attempt": attempt,
                        "reason": retry_reason, "campaign_role": role,
                        "schedule_index": index, "lap": item.lap,
                        "cell_id": item.cell_id, "variant": "unknown", "ts": _iso_now(),
                    })

            retry = attempt > 0
            required_s = _session_wall_upper_bound_s(role)
            try:
                assert_budget_available(budget_path, required_s, retry=retry)
            except BudgetExhausted as exc:
                _append_event(layout, {
                    "event": "budget-refused", "schedule_index": index,
                    "campaign_role": role, "lap": item.lap, "cell_id": item.cell_id,
                    "variant": "not-started", "ts": _iso_now(), "reason": str(exc),
                })
                append_budget_entry(
                    budget_path, role=role, started_iso=_iso_now(), wall_s=0.0,
                    phase=ROLE_TO_PHASE[role], note=f"budget-refused: {exc}")
                budget_stopped = True
                break

            started_iso = _iso_now()
            attempt_started = monotonic()
            variant = f"prepare-failure-{index}-{attempt}"
            session_started = False
            try:
                prepare_kwargs = {"cxx": cxx}
                if prepare_cell_fn is prepare_cell:
                    prepare_kwargs["condition_use_class"] = condition_use_class
                with prepare_cell_fn(
                        item.cell, cfg.ccbench_commit, **prepare_kwargs) as prepared:
                    variant_flags = item.cell.get("variant", {}).get("flags", {})
                    configuration = item.cell.get("configuration")
                    if not isinstance(variant_flags, Mapping):
                        raise DriverError("condition gate の variant flags が不正")
                    expected_request_digests = _condition_request_digests_for_flags(
                        variant_flags,
                        driver_id=_condition_driver_id(configuration),
                    )
                    condition_admission = require_returned_condition_evidence(
                        prepared, expected_request_digests=expected_request_digests,
                        use_class=condition_use_class,
                        label="prepare_cell_fn return",
                    )
                    prepared_records = (
                        prepared.condition_supply_records,
                        prepared.condition_meaning_records,
                    )
                    review_input_sha = hashlib.sha256(
                        json.dumps(item.cell, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=True).encode("utf-8")
                    ).hexdigest()

                    def review_capability(evidence):
                        unsigned = {
                            "schema": REVIEW_RECEIPT_SCHEMA,
                            "review_id": ReviewId.S1_KNOWN_AXES.value,
                            "source": evidence.as_receipt(),
                            "input_sha256": review_input_sha,
                        }
                        receipt = dict(unsigned)
                        receipt["receipt_sha256"] = hashlib.sha256(
                            json.dumps(unsigned, sort_keys=True, separators=(",", ":"),
                                       ensure_ascii=True).encode("utf-8")
                        ).hexdigest()
                        return verify_review_receipt(
                            ReviewId.S1_KNOWN_AXES, evidence, receipt=receipt,
                        )

                    # variant_id は evaluate 直前に確定し、session-start を必ず先行耐久化する。
                    variant = pipeline.variant_id(prepared.genome, prepared.src_token)
                    start_event = _base_event(item, variant, attempt)
                    gate_receipt = condition_gate_receipt(
                        prepared_records[0], prepared_records[1],
                        condition_admission,
                    )
                    if gate_receipt is not None:
                        start_event["condition_gate"] = gate_receipt
                    if prepared.oracle_attempt is not None:
                        start_event["sort_swo_oracle"] = prepared.oracle_attempt
                        start_event["freeze_cell_id"] = item.freeze_cell_id
                    _append_event(layout, start_event)
                    session_started = True
                    kwargs = dict(
                        numactl=NUMACTL,
                        correctness=None,
                        extra_correctness=(
                            [(pipeline.S2_TAG, pipeline.s2_correctness_workload())]
                            if role == "develop" else None),
                        do_bench=(role != "develop"), do_settle=True,
                        src_token=prepared.src_token, log=log,
                        ccbench_dir=prepared.ccbench_dir, cache_root=prepared.cache_root,
                        screening=None, bench_max_rounds=1,
                        build_context=build_context,
                        capability_resolver=review_capability,
                    )
                    if prepared.sort_oracle_contract_id is not None:
                        kwargs["sort_oracle_contract_id"] = (
                            prepared.sort_oracle_contract_id
                        )
                    try:
                        if evaluate_fn is None:
                            result = pipeline.evaluate(
                                prepared.genome, layout, ENV_TAG,
                                cfg.ccbench_commit, perf, CLOCKS_PER_US,
                                authorization_contract=authorization_contract,
                                **kwargs,
                                **perf_evaluate_kwargs)
                        else:
                            result = evaluate_fn(
                                prepared.genome, layout, ENV_TAG,
                                cfg.ccbench_commit, perf, CLOCKS_PER_US,
                                authorization_contract=authorization_contract,
                                **kwargs,
                                **perf_evaluate_kwargs)
                        if evaluate_fn is not None:
                            require_returned_condition_evidence(
                                result,
                                expected_request_digests=expected_request_digests,
                                use_class=condition_use_class,
                                label="evaluate_fn return",
                                expected_records=prepared_records,
                            )
                    except (wal.WalAppendError, wal.WalFramingError):
                        # 不確かな同一 WAL に retry/session-result を重ねない。
                        raise
                    except DriverError:
                        raise
                    except Exception as exc:  # evaluate の例外は閉じた retry 対象 (a)。
                        status, reason = "retryable", f"{type(exc).__name__}: {exc}"
                    else:
                        status, reason = _result_classification(result, layout)
            except (wal.WalAppendError, wal.WalFramingError):
                # evaluate/cleanup 境界でも deviation や retry を追記せず上位へ保全する。
                raise
            except _SortSwoOracleRejected as exc:
                start_event = _base_event(item, variant, attempt)
                start_event["sort_swo_oracle"] = exc.oracle_attempt
                start_event["freeze_cell_id"] = item.freeze_cell_id
                _append_event(layout, start_event)
                status = "oracle-reject"
                reason = str(exc.oracle_attempt["reason_code"])
            except DriverError:
                # freeze 値・gate predicate・quarantine の契約違反は機械故障でない。
                raise
            except Exception as exc:
                if session_started or not _is_transient_prepare_failure(exc):
                    # evaluate 後の cleanup 失敗は COMMIT の重複を避けるため再試行しない。
                    raise
                # prepare 未到達 attempt も start/result を対にし、再開照合で欠落させない。
                start_event = _base_event(item, variant, attempt)
                from .sort_swo_oracle import SortSwoOracleUnavailable, attempt_record
                if isinstance(exc, SortSwoOracleUnavailable) and exc.result is not None:
                    start_event["sort_swo_oracle"] = attempt_record(exc.result)
                    start_event["freeze_cell_id"] = item.freeze_cell_id
                _append_event(layout, start_event)
                status, reason = "retryable", f"prepare {type(exc).__name__}: {exc}"

            wall_s = monotonic() - attempt_started
            process_attempt_wall += wall_s
            note_prefix = "machine-failure-retry:" if retry else "session:"
            append_budget_entry(
                budget_path, role=role, started_iso=started_iso, wall_s=wall_s,
                phase=ROLE_TO_PHASE[role],
                note=f"{note_prefix} index={index} attempt={attempt} status={status} reason={reason}")
            _append_event(layout, {
                "event": "session-result", "schedule_index": index,
                "campaign_role": role, "lap": item.lap, "cell_id": item.cell_id,
                "variant": variant, "ts": _iso_now(), "attempt": attempt,
                "status": status, "reason": reason,
            })

            if status == "success":
                index += 1
                continue
            if status == "verifier-red":
                verifier_red = True
                break
            if status == "oracle-reject":
                oracle_reject = True
                break
            if status == "abandoned":
                incomplete = True
                index += 1
                continue
            if status == "retryable" and attempt < MAX_RETRIES:
                _append_event(layout, {
                    "event": "retry", "retry_of": index, "attempt": attempt + 1,
                    "reason": reason, "campaign_role": role,
                    "schedule_index": index, "lap": item.lap, "cell_id": item.cell_id,
                    "variant": variant, "ts": _iso_now(),
                })
                continue
            _append_event(layout, {
                "event": "session-result", "schedule_index": index,
                "campaign_role": role, "lap": item.lap, "cell_id": item.cell_id,
                "variant": variant, "ts": _iso_now(), "attempt": attempt,
                "status": "abandoned", "reason": f"retry上限/非retryable: {reason}",
            })
            incomplete = True
            index += 1
    finally:
        # evaluate attempt 外の freeze/照合/pre-flight/ledger 処理も campaign process wall に含める。
        total_wall = monotonic() - process_started
        overhead = max(0.0, total_wall - process_attempt_wall)
        if overhead:
            append_budget_entry(
                budget_path, role=role, started_iso=_iso_now(), wall_s=overhead,
                phase=ROLE_TO_PHASE[role], note="campaign-overhead: freeze/ledger/preflight")

    if verifier_red:
        return EXIT_VERIFIER_RED
    if oracle_reject:
        return EXIT_ORACLE_REJECT
    if budget_stopped:
        return EXIT_BUDGET
    if incomplete:
        return EXIT_INCOMPLETE
    return EXIT_OK


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=("develop", "floor", "block1", "block2"))
    parser.add_argument("--dry-run", action="store_true",
                        help="freeze と既存 session ledger の schedule prefix だけを検証する")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return run_role(args.role, dry_run=args.dry_run)
    except Exception as exc:
        # B1 FreezeError を含む構成拒否は traceback で埋めず、終了コードで表明する。
        print(f"fails-closed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
