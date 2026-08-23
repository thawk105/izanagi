# -*- coding: utf-8 -*-
"""8b oracle session WAL を全 schedule 行の observations へ射影する。

正規 driver は単一の env_tag を全 session append に渡し、issuer には共有定数
``"oracle-session"`` を使うため、正規 producer は session identity 検査に抵触しない。
この検査は正規だがバグりうる、または内容を変更されうる WAL に対する構造検査であり、
対象は session record の identity だけである。性能証拠である pipeline record の env は
検査しない。session identity 層では、manifest が ``run_contract.env_tag`` を非空文字列で
宣言する場合に限り session env とその未検証の宣言値との一致を課す。legacy manifest、
または env_tag が欠落・空・非文字列の場合、この層は campaign 内一貫性だけを課す。
receipt expectation 層では、``run_contract`` を Mapping として宣言するなら ``env_tag`` と
``contract_sha256`` はともに非空 str を要し、欠落・空・非 str は resolver より前に拒否する。
ただしこの診断が行へ載るのは、campaign-start が一意で schedule row を持つ campaign の
観測経路だけであり、早期 return や 0-row campaign では載らない。完全な manifest env
authority は P-A1(a)/[T-002] の責務である。WAL 各行の duplicate key と record の基本形も
検査し、campaign-terminal が物理的な最終 record であることを要求する。hash chain や外部
anchor はなく、任意改変に対する真正性の保証ではない。

namespace と campaign の pathname 検査は stable filesystem を前提とする。
namespace component、campaign path、WAL、store には同一 UID の競合者による
交換と復元の ABA race が残るため、この module はそれらを完全に閉鎖しない。
"""
from __future__ import annotations

import argparse
import dataclasses
import errno
import hashlib
import json
import os
import re
import stat
import sys
from collections.abc import Mapping, Sequence
from typing import Callable, Optional, TypedDict
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
ROOT = _ORCHESTRATOR.parent

from . import artifact_admission as _artifact_admission  # noqa: E402
from . import env_attestation, env_contract, model  # noqa: E402
from . import execution_guard, s8b_oracle_manifest, wal  # noqa: E402
from . import s8b_oracle_spec  # noqa: E402
from . import s8b_oracle_artifacts as _artifacts  # noqa: E402
from . import s8b_abort_reason_contract as _abort_reason_contract  # noqa: E402
from . import s8b_experiment_numbers as _experiment_numbers  # noqa: E402
from . import s8b_freeze_io as _freeze_io  # noqa: E402
from . import s8b_outcome_stage_contract as _outcome_stage_contract  # noqa: E402
from . import s8b_ratified_freeze  # noqa: E402
from . import t080_freeze_migration as _t080  # noqa: E402
from .layout import (  # noqa: E402
    CampaignLayout,
    repo_output_root,
    resolve_campaign_output_root,
    validate_campaign_id,
)
from orchestrator.calibrator import perf_preflight as _perf_preflight  # noqa: E402


SCHEMA_VERSION = _artifacts.OFFICIAL_OBSERVATIONS_SCHEMA
SESSION_STAGE = model.STAGE_S8B_ORACLE_SESSION
SESSION_ISSUER = model.S8B_ORACLE_SESSION_ISSUER
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
_TRIAL_IDENTITY_KEYS = (
    "schedule_index", "holdout_id", "configuration_id", "attempt",
)
_ROW_LIFECYCLE_EVENTS = frozenset({
    "trial-start", "trial-result", "retry", "trial-skipped",
    "budget-refused", "binding-refused",
})
# campaign-terminal 等は row の S -> pipeline -> T lifecycle の外で検査する。
# この分離により、最後の trial-result 後の campaign-terminal は row tail とみなさない。
_CAMPAIGN_LEVEL_EVENTS = frozenset({
    "campaign-start", "campaign-terminal", "deviation",
})
_T080_KEY = "t080_freeze_migration_observation"
_T080_REASON_PREFIX = "t080-freeze-migration-observation: "
_T080_TOP_KEYS = frozenset({
    "schema_version", "migration_id", "receipt", "migration_basis_commit",
    "validation_head", "items",
})
_T080_ITEM_KEYS = frozenset({
    "artifact", "kind", "subject", "recorded", "observed", "status",
})
_T080_NEVER_KEYS = frozenset({"state", "validation_head"})
_SHA1_RE = re.compile(r"[0-9a-f]{40}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_MEASUREMENT_RECORD_KEYS = frozenset({"path", "sha256"})
_STORE_REVERIFICATION_KEYS = frozenset({"state", "cells"})
_STORE_REVERIFICATION_CELL_KEYS = frozenset({
    "cell_id", "store_path", "expected_sha256", "actual_sha256", "state",
})
_STORE_REVERIFICATION_STATES = frozenset({"verified", "unverified"})
_STORE_REVERIFICATION_CELL_STATES = frozenset({"match", "mismatch", "missing"})
_MEASUREMENT_CONDITION_KEYS = frozenset({
    "campaign_id", "measurement_manifest_sha256", "perf_observation",
})
_MEASUREMENT_MANIFEST_NAME = "measurement-manifest.json"
_DEGRADED_PLACEHOLDER_CMD = ("ccbench",)
_DEGRADED_PLACEHOLDER_INDICATORS = {
    "ipc": None,
    "llc_miss_rate": None,
}


class ReportError(ValueError):
    """manifest または WAL が report 契約を満たさない。"""


class _ManifestIssue(TypedDict):
    """manifest 全域を taint する安定した構造化診断。"""

    code: str
    campaign_id: Optional[str]
    message: str


@dataclasses.dataclass(frozen=True)
class _T080CampaignObservation:
    """1 campaign の campaign-start にある T-080 値の分類。"""

    kind: str
    canonical: Optional[bytes] = None
    envelope: Optional[Mapping] = None
    issue: Optional[str] = None


def _t080_reason(detail: str) -> str:
    return f"{_T080_REASON_PREFIX}{detail}"


def _t080_hex(value: object, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _canonical_t080_envelope(value: object) -> bytes:
    """T-080 observation の exact 6-field envelope を検査して canonical 化する。"""
    if not isinstance(value, Mapping) or set(value) != _T080_TOP_KEYS:
        raise ValueError("envelope top-level key 集合が不正")
    if value.get("schema_version") != _t080.OBSERVATION_SCHEMA_VERSION:
        raise ValueError("schema_version が不正")
    if value.get("migration_id") != _t080.MIGRATION_ID:
        raise ValueError("migration_id が不正")
    receipt = value.get("receipt")
    if (not isinstance(receipt, Mapping)
            or set(receipt) != {"path", "raw_sha256"}
            or receipt.get("path") != _t080.RECEIPT_REL
            or not _t080_hex(receipt.get("raw_sha256"), _SHA256_RE)):
        raise ValueError("receipt が不正")
    if not _t080_hex(value.get("migration_basis_commit"), _SHA1_RE):
        raise ValueError("migration_basis_commit が不正")
    if not _t080_hex(value.get("validation_head"), _SHA1_RE):
        raise ValueError("validation_head が不正")

    items = value.get("items")
    if not isinstance(items, list) or len(items) != 17:
        raise ValueError("items が exact 17 件でない")
    expected = [
        *(("source-repin", "repinned-to-basis-blob") for _ in range(13)),
        *(("generator-metadata", "metadata-only") for _ in range(2)),
        ("ancestry", None),
        ("ancestry", None),
    ]
    for index, (item, (expected_kind, expected_status)) in enumerate(zip(items, expected)):
        if not isinstance(item, Mapping) or set(item) != _T080_ITEM_KEYS:
            raise ValueError(f"items[{index}] key 集合が不正")
        if item.get("artifact") not in {"known_axes", "holdout"}:
            raise ValueError(f"items[{index}].artifact が不正")
        if item.get("kind") != expected_kind:
            raise ValueError(f"items[{index}].kind が不正")
        if not isinstance(item.get("subject"), str) or not item["subject"]:
            raise ValueError(f"items[{index}].subject が不正")
        if expected_kind != "ancestry":
            spec = (
                _t080.SOURCE_REPIN_SPECS[index]
                if index < 13 else _t080.METADATA_SPECS[index - 13]
            )
            if (item.get("artifact"), item.get("subject"), item.get("recorded")) != (
                spec.artifact, spec.json_pointer, spec.recorded_sha256,
            ):
                raise ValueError(f"items[{index}] 固定値が不正")
            if item.get("status") != expected_status:
                raise ValueError(f"items[{index}].status が不正")
            if (not _t080_hex(item.get("recorded"), _SHA256_RE)
                    or not _t080_hex(item.get("observed"), _SHA256_RE)):
                raise ValueError(f"items[{index}] hash が不正")
            continue
        status = item.get("status")
        if status not in {"missing-commit", "not-ancestor", "ancestor"}:
            raise ValueError(f"items[{index}].status が不正")
        if not _t080_hex(item.get("recorded"), _SHA1_RE):
            raise ValueError(f"items[{index}].recorded が不正")
        observed = item.get("observed")
        if ((status == "missing-commit" and observed is not None)
                or (status != "missing-commit" and not _t080_hex(observed, _SHA1_RE))):
            raise ValueError(f"items[{index}].observed が不正")
    if items[15].get("artifact") != "known_axes" or items[16].get("artifact") != "holdout":
        raise ValueError("ancestry items の順序が不正")
    if (items[15].get("recorded"), items[16].get("recorded")) != (
        _t080.KNOWN_AXES_RECORDED_HEAD, _t080.HOLDOUT_RECORDED_HEAD,
    ):
        raise ValueError("ancestry items の固定値が不正")
    try:
        return _t080._canonical_bytes(value)
    except _t080.MigrationError as exc:
        raise ValueError("canonical bytes に変換できない") from exc


def _canonical_t080_never_issued(value: object) -> bytes:
    if (not isinstance(value, Mapping) or set(value) != _T080_NEVER_KEYS
            or value.get("state") != "never-issued"
            or not _t080_hex(value.get("validation_head"), _SHA1_RE)):
        raise ValueError("never-issued record が不正")
    return _t080._canonical_bytes(value)


def _history_at_validation_head(
    *, repo_root: Path, validation_head: str,
) -> "_t080.ReceiptResolution":
    return _t080.inspect_receipt_history(
        root=Path(repo_root), validation_head=validation_head, check_worktree=False,
    )


def _expected_historical_envelope(
    history: "_t080.ReceiptResolution", *, repo_root: Path, validation_head: str,
) -> Mapping[str, object]:
    if (history.introduction_commit is None or history.receipt is None
            or history.receipt_raw is None or history.refusals
            or history.state == "issued-but-missing"):
        raise ValueError("validation_head で receipt 履歴が有効でない")
    _t080._verify_historical_receipt_derivation(history.receipt, Path(repo_root))
    ancestries = (
        _t080._classify_ancestry(
            _t080.KNOWN_AXES_RECORDED_HEAD, validation_head, Path(repo_root),
            artifact="known_axes",
        ),
        _t080._classify_ancestry(
            _t080.HOLDOUT_RECORDED_HEAD, validation_head, Path(repo_root),
            artifact="holdout",
        ),
    )
    if any(item.refusal_reason for item in ancestries):
        raise ValueError("validation_head で ancestry を再導出できない")
    return _t080._make_observation(
        history.receipt, history.receipt_raw, validation_head, ancestries,
    )


def _campaign_t080_observation(
    records: Sequence[object], *, repo_root: Path,
    current_receipt_invalid: bool,
) -> _T080CampaignObservation:
    starts = [record.payload for record in records
              if _session_event(record, "campaign-start")]
    if len(starts) != 1:
        return _T080CampaignObservation("unavailable")
    start = starts[0]
    if _T080_KEY not in start:
        return _T080CampaignObservation(
            "malformed", issue=_t080_reason("campaign-start に T-080 key がない"),
        )
    value = start[_T080_KEY]
    if value is None:
        return _T080CampaignObservation(
            "malformed", issue=_t080_reason("bare null は現行 grammar で禁止"),
        )
    if isinstance(value, Mapping) and value.get("state") == "never-issued":
        try:
            canonical = _canonical_t080_never_issued(value)
            validation_head = str(value["validation_head"])
            history = _history_at_validation_head(
                repo_root=repo_root, validation_head=validation_head,
            )
            if history.state != "never-issued":
                raise ValueError("never-issued だが validation_head の履歴に R が存在する")
        except (TypeError, ValueError, _t080.MigrationError) as exc:
            return _T080CampaignObservation(
                "malformed", issue=_t080_reason(f"invalid never-issued record: {exc}"),
            )
        return _T080CampaignObservation("never-issued", canonical, value)
    try:
        canonical = _canonical_t080_envelope(value)
        validation_head = str(value["validation_head"])
        history = _history_at_validation_head(
            repo_root=repo_root, validation_head=validation_head,
        )
        expected = _expected_historical_envelope(
            history, repo_root=repo_root, validation_head=validation_head,
        )
        if canonical != _canonical_t080_envelope(expected):
            raise ValueError("envelope が R blob/Git 再導出値と不一致")
        if current_receipt_invalid:
            raise ValueError("report 生成時の receipt が issued-but-missing/invalid")
    except (TypeError, ValueError, _t080.MigrationError) as exc:
        return _T080CampaignObservation(
            "malformed", issue=_t080_reason(f"malformed envelope: {exc}"),
        )
    return _T080CampaignObservation("envelope", canonical, value)


def _force_protocol_violation(rows: Sequence[dict], issue: str) -> None:
    """既存理由を保持しつつ campaign 横断の protocol 違反を全 row へ課す。"""
    for row in rows:
        reasons = [reason for reason in (row.get("reason"), issue) if reason]
        row.update(
            status="protocol_violation",
            bench_values=[],
            reason="; ".join(dict.fromkeys(reasons)),
        )


@dataclasses.dataclass(frozen=True)
class _NamespaceLeafIdentity:
    path: Path
    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int


@dataclasses.dataclass(frozen=True)
class _ResolvedOfficialOutputRoot:
    """Stable-filesystem snapshot for one admitted output-root path."""

    path: Path
    root_identity: tuple[int, int]
    namespace_identities: tuple[_NamespaceLeafIdentity, ...]


def _reject_output_root_symlink_components(path: Path) -> None:
    """Reject every existing lexical component before path resolution."""
    if not path.is_absolute():
        raise ReportError("official output_root は絶対 path 必須")
    if ".." in path.parts:
        raise ReportError("official output_root に .. component を指定できない")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            break
        except OSError as exc:
            raise ReportError("official output_root component を検査できない") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise ReportError("official output_root に symlink component がある")
        if not stat.S_ISDIR(metadata.st_mode):
            raise ReportError("official output_root に非 directory component がある")


def _read_namespace_leaf(
        marker: Path, *, required: bool,
) -> _NamespaceLeafIdentity | None:
    """Read one namespace marker without following or blocking on its leaf."""
    nofollow = getattr(os, "O_NOFOLLOW", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or nonblock is None:
        raise ReportError("namespace marker の安全な open flag が利用できない")
    try:
        descriptor = os.open(marker, os.O_RDONLY | nofollow | nonblock)
    except FileNotFoundError:
        if required:
            raise ReportError("output_root namespace marker が存在しない")
        return None
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise ReportError(f"namespace marker が symlink: {marker}") from exc
        raise ReportError(f"namespace marker を安全に open できない: {marker}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ReportError(f"namespace marker が通常 file でない: {marker}")
        read_limit = max(
            len(_artifacts.OFFICIAL_NAMESPACE_BYTES),
            len(_artifacts.EXPLORATION_NAMESPACE_BYTES),
        ) + 1
        if before.st_size >= read_limit:
            raise ReportError(f"namespace marker が有界サイズを超える: {marker}")
        chunks: list[bytes] = []
        remaining = read_limit
        while remaining:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
    except ReportError:
        raise
    except OSError as exc:
        raise ReportError(f"namespace marker を有界 read できない: {marker}") from exc
    finally:
        os.close(descriptor)
    before_identity = (
        before.st_dev, before.st_ino, before.st_size,
        before.st_mtime_ns, before.st_ctime_ns,
    )
    after_identity = (
        after.st_dev, after.st_ino, after.st_size,
        after.st_mtime_ns, after.st_ctime_ns,
    )
    if before_identity != after_identity:
        raise ReportError(f"namespace marker が read 中に変化した: {marker}")
    payload = b"".join(chunks)
    if payload == _artifacts.EXPLORATION_NAMESPACE_BYTES:
        raise ReportError(
            f"exploration namespace を official report output_root に指定できない: {marker}"
        )
    if payload != _artifacts.OFFICIAL_NAMESPACE_BYTES:
        raise ReportError(f"namespace marker が official exact bytes と一致しない: {marker}")
    return _NamespaceLeafIdentity(
        path=marker,
        device=after.st_dev,
        inode=after.st_ino,
        size=after.st_size,
        mtime_ns=after.st_mtime_ns,
        ctime_ns=after.st_ctime_ns,
    )


def _scan_official_namespace(resolved: Path) -> _ResolvedOfficialOutputRoot:
    """Require the root marker and allowlist every marker-bearing ancestor."""
    _reject_output_root_symlink_components(resolved)
    try:
        root_metadata = resolved.lstat()
    except FileNotFoundError as exc:
        raise ReportError("official output_root が存在しない") from exc
    except OSError as exc:
        raise ReportError("official output_root を検査できない") from exc
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise ReportError("official output_root が directory でない")

    identities: list[_NamespaceLeafIdentity] = []
    for index, ancestor in enumerate((resolved, *resolved.parents)):
        identity = _read_namespace_leaf(
            ancestor / "namespace.json", required=index == 0,
        )
        if identity is not None:
            identities.append(identity)
    return _ResolvedOfficialOutputRoot(
        path=resolved,
        root_identity=(root_metadata.st_dev, root_metadata.st_ino),
        namespace_identities=tuple(identities),
    )


def _resolve_official_output_root(output_root: Path) -> _ResolvedOfficialOutputRoot:
    """Admit one official read root and snapshot its stable namespace boundary."""
    raw_candidate = Path(output_root)
    if ".." in raw_candidate.parts:
        raise ReportError("official output_root に .. component を指定できない")
    try:
        candidate = (
            raw_candidate
            if raw_candidate.is_absolute()
            else Path.cwd() / raw_candidate
        )
    except OSError as exc:
        raise ReportError("relative output_root の cwd を取得できない") from exc
    _reject_output_root_symlink_components(candidate)
    try:
        resolved = candidate.resolve(strict=False)
        canonical_repo_output = Path(repo_output_root()).resolve(strict=True)
    except OSError as exc:
        raise ReportError("output_root を解決できない") from exc
    if not raw_candidate.is_absolute() and resolved != canonical_repo_output:
        raise ReportError(
            "relative official output_root は canonical repository output exact のみ受理する"
        )
    if resolved != canonical_repo_output:
        try:
            admitted = Path(resolve_campaign_output_root(
                "official", os.fspath(candidate),
            ))
        except ValueError as exc:
            raise ReportError(str(exc)) from exc
        if admitted != resolved:
            raise ReportError("official output_root admission の解決結果が不一致")
    return _scan_official_namespace(resolved)


def _revalidate_official_output_root(
        admitted: _ResolvedOfficialOutputRoot,
) -> None:
    """Detect persistent root/marker changes; same-UID ABA remains out of scope."""
    observed = _scan_official_namespace(admitted.path)
    if (observed.root_identity != admitted.root_identity
            or observed.namespace_identities != admitted.namespace_identities):
        raise ReportError("output_root または namespace marker が観測中に変化した")


def _resolved_campaign_layout(
    campaign_id: str, resolved_output_root: Path,
) -> CampaignLayout:
    """stable tree で symlink-free campaign の resolved path carrier を作る。"""
    try:
        cid = validate_campaign_id(campaign_id)
    except ValueError as exc:
        raise ReportError(str(exc)) from exc
    campaigns_root = resolved_output_root / "campaigns"
    campaign_root = campaigns_root / cid
    for component in (campaigns_root, campaign_root):
        if component.is_symlink():
            raise ReportError(f"campaign path component が symlink: {component}")
    try:
        resolved_campaign_root = campaign_root.resolve()
        resolved_campaign_root.relative_to(campaigns_root)
    except (OSError, ValueError) as exc:
        raise ReportError(
            "resolved campaign root が official output_root/campaigns 配下でない"
        ) from exc
    if resolved_campaign_root.parent != campaigns_root:
        raise ReportError(
            "resolved campaign root が official output_root/campaigns 直下でない"
        )
    return CampaignLayout(root=str(resolved_campaign_root))


def _campaign_verifier_epoch_projection(
        campaign_id: str, resolved_output_root: Path,
) -> dict:
    """Campaign の lock-only epoch gate を observations 証拠へ射影する。"""
    layout = _resolved_campaign_layout(campaign_id, resolved_output_root)
    try:
        epoch = _artifact_admission.require_campaign_verifier_epoch(
            layout,
            purpose=(
                _artifact_admission.CampaignReadPurpose.CERTIFIED_ACCEPTANCE
            ),
        )
    except _artifact_admission.CampaignVerifierEpochRejected as exc:
        return {
            "campaign_id": campaign_id,
            "campaign_verifier_epoch": exc.campaign_verifier_epoch,
            "state": exc.epoch_state,
            "reason_code": exc.reason_code,
            "identity_scope": exc.identity_scope,
            "excluded_scope": exc.excluded_scope,
            "certified_eligible": False,
            "rejection": {
                "code": "campaign-verifier-epoch-rejected",
                "message": str(exc),
            },
        }
    except _artifact_admission.ArtifactAdmissionError as exc:
        return {
            "campaign_id": campaign_id,
            "campaign_verifier_epoch": None,
            "state": "unavailable",
            "reason_code": "campaign-verifier-epoch-unavailable",
            "identity_scope": (
                _artifact_admission.CAMPAIGN_VERIFIER_EPOCH_SCOPE
            ),
            "excluded_scope": (
                _artifact_admission.CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE
            ),
            "certified_eligible": False,
            "rejection": {
                "code": "campaign-verifier-epoch-unavailable",
                "message": (
                    "campaign verifier epoch を検証できない: "
                    f"{type(exc).__name__}"
                ),
            },
        }
    return {
        "campaign_id": campaign_id,
        "campaign_verifier_epoch": epoch.campaign_verifier_epoch,
        "state": epoch.state,
        "reason_code": epoch.reason_code,
        "identity_scope": epoch.identity_scope,
        "excluded_scope": epoch.excluded_scope,
        "certified_eligible": True,
        "rejection": None,
    }


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _canonical_sha256(value: Mapping) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_manifest(
        manifest: Mapping,
) -> tuple[list[Mapping], set[str], str, int, int, list[_ManifestIssue]]:
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
    run_contract_issues: list[_ManifestIssue] = []
    if "run_contract" in manifest:
        run_contract = manifest["run_contract"]
        if not isinstance(run_contract, Mapping):
            run_contract_issues.append({
                "code": "run-contract-not-object",
                "campaign_id": None,
                "message": "manifest.run_contract が object でない",
            })
        else:
            declared_reps = run_contract.get("reps")
            if not _is_int(declared_reps) or declared_reps <= 0:
                run_contract_issues.append({
                    "code": "run-contract-reps-not-positive-int",
                    "campaign_id": None,
                    "message": (
                        "manifest.run_contract.reps が非 bool の正整数でない"
                    ),
                })
            elif declared_reps != expected_reps:
                run_contract_issues.append({
                    "code": "run-contract-reps-not-approved",
                    "campaign_id": None,
                    "message": (
                        "manifest.run_contract.reps が APPROVED_REPS と不一致: "
                        f"actual={declared_reps}, expected={expected_reps}"
                    ),
                })
    return (schedule, set(allowed), manifest_sha, n, expected_reps,
            run_contract_issues)


def _campaign_index(
    raw: object, schedule: Sequence[Mapping],
) -> tuple[dict[str, str], set[str], list[_ManifestIssue]]:
    by_block: dict[str, str] = {}
    ids: set[str] = set()
    declaration_issues: list[_ManifestIssue] = []
    if isinstance(raw, Mapping):
        for block, value in raw.items():
            campaign_id = value.get("campaign_id") if isinstance(value, Mapping) else value
            if not isinstance(block, str) or not isinstance(campaign_id, str) or not campaign_id:
                raise ReportError("campaign_ids mapping の block/campaign_id が不正")
            by_block[block] = campaign_id
            ids.add(campaign_id)
            if not any(row.get("block_id") == block for row in schedule):
                declaration_issues.append({
                    "code": "campaign-without-schedule-row",
                    "campaign_id": campaign_id,
                    "message": (
                        "manifest.campaign_ids の宣言に schedule row がない: "
                        f"block_id={block!r}, campaign_id={campaign_id!r}"
                    ),
                })
    elif (isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray))):
        declared_ids: list[str] = []
        for value in raw:
            if isinstance(value, str) and value:
                campaign_id = value
            elif isinstance(value, Mapping):
                block = value.get("block_id")
                campaign_id = value.get("campaign_id")
                if not isinstance(block, str) or not isinstance(campaign_id, str) or not campaign_id:
                    raise ReportError("campaign_ids entry の block_id/campaign_id が不正")
                by_block[block] = campaign_id
            else:
                raise ReportError("campaign_ids は文字列または object の array でなければならない")
            ids.add(campaign_id)
            declared_ids.append(campaign_id)
    else:
        raise ReportError("campaign_ids は mapping または array でなければならない")
    if not ids:
        raise ReportError("campaign_ids が空")
    if not isinstance(raw, Mapping):
        for campaign_id in dict.fromkeys(declared_ids):
            has_row = False
            for row in schedule:
                try:
                    has_row = (
                        _campaign_for_row(row, by_block, ids) == campaign_id
                    )
                except ReportError:
                    continue
                if has_row:
                    break
            if not has_row:
                declaration_issues.append({
                    "code": "campaign-without-schedule-row",
                    "campaign_id": campaign_id,
                    "message": (
                        "manifest.campaign_ids の宣言に schedule row がない: "
                        f"campaign_id={campaign_id!r}"
                    ),
                })
    return by_block, ids, declaration_issues


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
        "lifecycle_ok": False,
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


def _measurement_condition_for_campaign(
        campaign_id: str, manifest_sha256: str, expected_block_ids: set[str],
        output_root: Path) -> dict:
    """campaign-start と runtime sidecar を bench observation へ再束縛する。"""
    condition = {
        "campaign_id": campaign_id,
        "measurement_manifest_sha256": None,
        "perf_observation": None,
    }
    layout = _resolved_campaign_layout(campaign_id, output_root)
    root = Path(layout.root)
    if not root.is_dir():
        return condition
    try:
        records, _line_issues, _truncated_tail = wal.read_records_collected(layout)
    except Exception:
        return condition
    starts = [record.payload for record in records
              if _session_event(record, "campaign-start")]
    declared = [
        start.get("measurement_manifest") for start in starts
        if start.get("measurement_manifest") is not None
    ]
    if not declared:
        if (root / _MEASUREMENT_MANIFEST_NAME).exists():
            raise ReportError(
                f"campaign_id={campaign_id!r}: measurement sidecar があるのに "
                "campaign-start file record がない"
            )
        if any(
                isinstance(getattr(record, "payload", None), Mapping)
                and record.stage == "bench_done"
                and record.payload.get("perf_observation") is not None
                for record in records):
            raise ReportError(
                f"campaign_id={campaign_id!r}: bench perf_observation があるのに "
                "campaign-start.measurement_manifest がない"
            )
        return condition
    if len(starts) != 1 or len(declared) != 1:
        raise ReportError(
            f"campaign_id={campaign_id!r}: measurement manifest を持つ "
            "campaign-start が一意でない"
        )
    record = declared[0]
    if not isinstance(record, Mapping) or set(record) != _MEASUREMENT_RECORD_KEYS:
        raise ReportError(
            f"campaign_id={campaign_id!r}: measurement_manifest file record の "
            "exact key 集合が不一致"
        )
    if record.get("path") != _MEASUREMENT_MANIFEST_NAME:
        raise ReportError(
            f"campaign_id={campaign_id!r}: measurement_manifest.path が canonical でない"
        )
    expected_sha256 = record.get("sha256")
    if (not isinstance(expected_sha256, str)
            or _SHA256_RE.fullmatch(expected_sha256) is None):
        raise ReportError(
            f"campaign_id={campaign_id!r}: measurement_manifest.sha256 が不正"
        )
    source = root / _MEASUREMENT_MANIFEST_NAME
    try:
        actual_sha256 = _artifacts.measurement_manifest_sha256(source)
        document = _artifacts.load_measurement_manifest(
            source,
            run_cmd=_DEGRADED_PLACEHOLDER_CMD,
            leading_indicators=_DEGRADED_PLACEHOLDER_INDICATORS,
        )
    except _artifacts.OracleArtifactTypeError as exc:
        raise ReportError(
            f"campaign_id={campaign_id!r}: measurement manifest が不正: {exc}"
        ) from exc
    if actual_sha256 != expected_sha256:
        raise ReportError(
            f"campaign_id={campaign_id!r}: measurement manifest raw hash が "
            "campaign-start record と不一致"
        )
    start = starts[0]
    if document["oracle_manifest_sha256"] != manifest_sha256:
        raise ReportError(
            f"campaign_id={campaign_id!r}: measurement manifest の oracle manifest hash が不一致"
        )
    if document["campaign_id"] != campaign_id:
        raise ReportError(
            f"campaign_id={campaign_id!r}: measurement manifest campaign_id が不一致"
        )
    block_id = start.get("block_id")
    if (document["block_id"] != block_id
            or expected_block_ids and block_id not in expected_block_ids):
        raise ReportError(
            f"campaign_id={campaign_id!r}: measurement manifest block_id が schedule と不一致"
        )

    observation = document["perf_observation"]
    for bench in (
            record.payload for record in records
            if record.stage == "bench_done"
            and isinstance(record.payload, Mapping)):
        try:
            rebound = _artifacts.load_measurement_manifest(
                source,
                run_cmd=bench.get("run_cmd"),
                leading_indicators=bench.get("leading_indicators"),
            )
        except _artifacts.OracleArtifactTypeError as exc:
            raise ReportError(
                f"campaign_id={campaign_id!r}: bench 測定条件で measurement manifestを"
                f"再検証できない: {exc}"
            ) from exc
        if (rebound["perf_observation"] != observation
                or bench.get("perf_observation") != observation):
            raise ReportError(
                f"campaign_id={campaign_id!r}: sidecar と bench perf_observation が不一致"
            )
    condition["measurement_manifest_sha256"] = actual_sha256
    condition["perf_observation"] = observation
    if set(condition) != _MEASUREMENT_CONDITION_KEYS:  # pragma: no cover - construction pin
        raise AssertionError("measurement condition construction keys")
    return condition


def _session_identity_issues(records, manifest) -> list[str]:
    session_records = [
        (ordinal, record) for ordinal, record in enumerate(records)
        if record.stage == SESSION_STAGE
    ]
    if not session_records:
        return []

    issues: list[str] = []
    mismatches = sorted(
        (ordinal, record.variant) for ordinal, record in session_records
        if record.variant != SESSION_ISSUER
    )
    if mismatches:
        issues.append(
            "oracle session record.variant が issuer と不一致: "
            f"expected={SESSION_ISSUER!r}, mismatches={mismatches!r}"
        )

    values = sorted({record.env_tag for _, record in session_records})
    if len(values) > 1:
        issues.append(
            f"oracle session record.env_tag が campaign 内で一意でない: values={values!r}"
        )

    run_contract = manifest.get("run_contract")
    if isinstance(run_contract, Mapping):
        expected = run_contract.get("env_tag")
        if (isinstance(expected, str) and expected
                and any(value != expected for value in values)):
            issues.append(
                "oracle session record.env_tag が manifest.run_contract.env_tag と不一致: "
                f"expected={expected!r}, values={values!r}"
            )
    return issues


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


def _pipeline_event(record: object) -> bool:
    stage = getattr(record, "stage", None)
    return (isinstance(stage, str)
            and stage in _outcome_stage_contract.PIPELINE_STAGES)


def _inert_record_issues(records: Sequence[object]) -> list[str]:
    """8b protocol の session / pipeline のどちらにも属さない record を列挙する。"""
    return [
        ("WAL record が session event / pipeline stage のどちらにも分類されない: "
         f"ordinal={ordinal} stage={getattr(record, 'stage', None)!r}")
        for ordinal, record in enumerate(records)
        if not _session_event(record) and not _pipeline_event(record)
    ]


def _row_lifecycle_event(record: object) -> bool:
    return (_session_event(record)
            and record.payload.get("event") in _ROW_LIFECYCLE_EVENTS)


def _campaign_level_event(record: object) -> bool:
    return (_session_event(record)
            and record.payload.get("event") in _CAMPAIGN_LEVEL_EVENTS)


def _terminal_result_binding(
    item: Mapping,
    window: Sequence[object],
    record_ordinals: Mapping[int, int],
) -> tuple[Mapping, list[str], list[str]]:
    """terminal window の T を start identity と物理順へ一意に束縛する。"""
    start = window[0].payload
    result_records = [
        record for record in window if _session_event(record, "trial-result")
    ]
    identity_issues: list[str] = []
    lifecycle_issues: list[str] = []
    if len(result_records) != 1:
        identity_issues.append(f"trial-result が一意でない: {len(result_records)}")
    result_record = result_records[-1] if result_records else None
    result = result_record.payload if result_record is not None else {}

    for key in _TRIAL_IDENTITY_KEYS:
        if key != "attempt" or key in item:
            if start.get(key) != item.get(key):
                identity_issues.append(f"trial-start.{key} が schedule と不一致")
        if result.get(key) != start.get(key):
            identity_issues.append(f"trial-result.{key} が trial-start と不一致")

    if len(result_records) == 1:
        result_ordinal = record_ordinals[id(result_record)]
        if any(
            record_ordinals[id(record)] > result_ordinal
            for record in window
            if _pipeline_event(record)
        ):
            # 「全 pipeline evidence より後ろ」と「T 後に pipeline がない」は
            # 同じ ordinal 述語であり、二重 gate にしない。
            lifecycle_issues.append(
                "trial-result が全 pipeline evidence より物理的に後ろでない"
            )
        if any(
            record_ordinals[id(record)] > result_ordinal
            for record in window
            if record is not result_record and _row_lifecycle_event(record)
        ):
            # campaign-level event は上の明示集合によりここへ入らない。
            lifecycle_issues.append("trial-result 後に row-scoped session event がある")
    return result, identity_issues, lifecycle_issues


def _attempt_lifecycle_plan(
    item: Mapping,
    windows: Sequence[Sequence[object]],
    all_windows: Sequence[Sequence[object]],
    record_ordinals: Mapping[int, int],
) -> dict:
    """一 schedule 行の二形 DFA を WAL の物理順のまま検査する。"""
    attempts = [window[0].payload.get("attempt") for window in windows]
    plan = {
        "valid": False,
        "reason": None,
        "terminal_window": None,
        "retried_summaries": [],
        "claimed_retry_ids": set(),
        "accounted_result_ids": {
            id(record)
            for window in windows
            for record in window
            if _session_event(record, "trial-result")
        },
    }
    if any(not _is_int(attempt) for attempt in attempts):
        plan["reason"] = (
            "attempt lifecycle の attempt 集合が {1} / {1,2} と厳密一致しない: "
            f"{attempts!r}"
        )
        return plan

    # 方針 (i): 集合述語は frozenset だけを見て、物理順を再検査しない。
    # attempt 番号で window を対応付けた後、下の ordinal 述語だけが順序を担う。
    # これにより順序 gate の変異を、集合/形状 gate から独立に帰属できる。
    attempt_set = frozenset(attempts)
    if attempt_set not in {frozenset({1}), frozenset({1, 2})}:
        plan["reason"] = (
            "attempt lifecycle の attempt 集合が {1} / {1,2} と厳密一致しない: "
            f"{attempts!r}"
        )
        return plan
    if len(attempts) != len(attempt_set):
        plan["reason"] = f"attempt lifecycle の attempt が重複: {attempts!r}"
        return plan

    windows_by_attempt = {
        window[0].payload["attempt"]: window for window in windows
    }
    if attempt_set == frozenset({1}):
        terminal = windows_by_attempt[1]
        _, identity_issues, ordering_issues = _terminal_result_binding(
            item, terminal, record_ordinals,
        )
        binding_issues = [*identity_issues, *ordering_issues]
        if binding_issues:
            plan["reason"] = binding_issues[0]
            return plan
        plan.update(valid=True, terminal_window=terminal)
        return plan

    first = windows_by_attempt[1]
    second = windows_by_attempt[2]
    retries = [record for record in first if _session_event(record, "retry")]
    plan["claimed_retry_ids"].update(id(record) for record in retries)
    if len(retries) != 1:
        plan["reason"] = f"attempt 1 retry record が一意でない: {len(retries)}"
        return plan
    if any(_session_event(record, "trial-result") for record in first[1:]):
        plan["reason"] = "attempt 1 retry window が result-less でない"
        return plan
    if any(_pipeline_event(record) for record in first[1:]):
        plan["reason"] = "attempt 1 retry window に pipeline record が混在"
        return plan
    retry_shape_records = [
        record for record in first
        if not _pipeline_event(record) and not _campaign_level_event(record)
    ]
    if len(retry_shape_records) != 2:
        # pipeline は直前の専用述語だけで検査する。ここは S/retry 以外の
        # 非 campaign-level record を捕らえる exact-shape gate である。
        plan["reason"] = (
            "attempt 1 retry window が [trial-start, retry] ちょうど 2 record でない"
        )
        return plan

    first_start = first[0].payload
    for key in ("schedule_index", "holdout_id", "configuration_id"):
        if first_start.get(key) != item.get(key):
            plan["reason"] = f"attempt 1 trial-start.{key} が schedule と不一致"
            return plan
    retry = retries[0].payload
    if retry.get("schedule_index") != item.get("schedule_index"):
        plan["reason"] = "retry.schedule_index が schedule と不一致"
        return plan
    if retry.get("attempt") != 2:
        plan["reason"] = "retry.attempt が next attempt=2 と不一致"
        return plan

    _, identity_issues, ordering_issues = _terminal_result_binding(
        item, second, record_ordinals,
    )
    terminal_binding_issues = [*identity_issues, *ordering_issues]
    if terminal_binding_issues:
        plan["reason"] = terminal_binding_issues[0]
        return plan

    physical_ordinals = {
        id(window[0]): ordinal for ordinal, window in enumerate(all_windows)
    }
    first_ordinal = physical_ordinals[id(first[0])]
    second_ordinal = physical_ordinals[id(second[0])]
    # 順方向と隣接性は一つの physical-topology 述語で受理集合を決める。
    # 内側の分岐は診断文の選択だけで、第二の reject gate ではない。
    if second_ordinal != first_ordinal + 1:
        plan["reason"] = (
            f"attempt lifecycle の物理順が 1→2 でない: {attempts!r}"
            if second_ordinal < first_ordinal
            else "attempt 2 が attempt 1 の物理的直後でない"
        )
        return plan

    plan.update(
        valid=True,
        terminal_window=second,
        retried_summaries=[{
            "attempt": 1,
            "status": "retried",
            "outcome": None,
            "binding_ok": False,
            "legacy_verify": "missing",
            "s2_verify": "missing",
        }],
    )
    return plan


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


def _verify_state(
        records: Sequence[object], tag: str,
        expected_attempt_id: str | None = None,
) -> tuple[str, list[str]]:
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
    candidate = matches[0]
    if (expected_attempt_id is not None
            and candidate.payload.get("build_attempt_id") != expected_attempt_id):
        return "missing", [
            f"verify_done[{tag}].build_attempt_id が committed attempt と不一致"
        ]
    certified = candidate.payload.get("certified")
    if certified is True:
        return "pass", []
    if certified is False:
        return "red", []
    return "missing", [f"verify_done[{tag}].certified が bool でない"]


def _safe_payload(record: object) -> Mapping:
    payload = getattr(record, "payload", None)
    return payload if isinstance(payload, Mapping) else {}


def _attempt_binding_issues(
        records: Sequence[object], *, stage: str,
        expected_attempt_id: str | None,
) -> list[str]:
    # 件数不整合 (0件/2件以上) は既存の別 gate (truth-table 不一致、bench_done 重複検査、
    # abort/commit 重複検査) が既に閉じるため、ちょうど1件のときだけ判定する
    # (T-1476 の _verify_state と同じ設計)。
    if expected_attempt_id is None or len(records) != 1:
        return []
    payload = _safe_payload(records[0])
    if payload.get("build_attempt_id") != expected_attempt_id:
        return [f"{stage}.build_attempt_id が committed attempt と不一致"]
    return []


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
                   record_ordinals: Mapping[int, int],
                   expected_perf_observation: object,
                   payload_issues: Sequence[str] = ()) -> dict:
    row = _base_row(item)
    start = window[0].payload
    result, result_identity_issues, _ = _terminal_result_binding(
        item, window, record_ordinals,
    )
    # lifecycle order/tail は DFA 側で status を赤にする。ここでは pipeline の
    # definitive-red assessment を lifecycle 違反で失わないよう identity だけを加える。
    issues: list[str] = list(result_identity_issues)

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

    expected_attempt_id = None
    if len(builds) == 1:
        build_attempt_id = _safe_payload(builds[0]).get("build_attempt_id")
        if isinstance(build_attempt_id, str) and build_attempt_id:
            expected_attempt_id = build_attempt_id
    legacy, legacy_issues = _verify_state(
        pipeline_records, "legacy", expected_attempt_id,
    )
    s2, s2_issues = _verify_state(
        pipeline_records, "s2", expected_attempt_id,
    )
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
        bench_payload = _safe_payload(benches[0])
        claim_ok = True
        observation = bench_payload.get("perf_observation")
        if observation != expected_perf_observation:
            claim_ok = False
            issues.append(
                "bench_done.perf_observation が campaign 測定条件と不一致"
            )
        elif observation is not None:
            try:
                claim_ok = _perf_preflight.perf_claim_allowed(
                    observation,
                    "throughput",
                    run_cmd=bench_payload.get("run_cmd"),
                    leading_indicators=bench_payload.get("leading_indicators"),
                )
            except _perf_preflight.PerfPreflightError as exc:
                claim_ok = False
                issues.append(f"bench_done.perf_observation が不正: {exc}")
            if not claim_ok:
                issues.append("bench_done.perf_observation は throughput claim を許可しない")
        raw_values = bench_payload.get("tps")
        projected = _artifacts.project_finite_float_sequence(raw_values)
        tps_ok = False
        if projected is None:
            issues.append("bench_done.tps が空または非有限値を含む")
        elif len(projected) != expected_reps:
            issues.append(
                "bench_done.tps 件数が official reps と不一致: "
                f"actual={len(projected)}, expected={expected_reps}")
        else:
            tps_ok = True

        raw_returncodes = bench_payload.get("rep_returncodes")
        returncodes_ok = False
        if (not isinstance(raw_returncodes, Sequence)
                or isinstance(raw_returncodes, (str, bytes, bytearray))):
            issues.append("bench_done.rep_returncodes が array でない")
        elif any(not _is_int(value) for value in raw_returncodes):
            issues.append("bench_done.rep_returncodes に非 int または bool がある")
        elif len(raw_returncodes) != expected_reps:
            issues.append(
                "bench_done.rep_returncodes 件数が official reps と不一致: "
                f"actual={len(raw_returncodes)}, expected={expected_reps}")
        elif any(value != 0 for value in raw_returncodes):
            issues.append("bench_done.rep_returncodes に非ゼロがある")
        else:
            returncodes_ok = True
        if claim_ok and tps_ok and returncodes_ok:
            bench_values = projected

    counts = {stage: sum(record.stage == stage for record in pipeline_records)
              for stage in _outcome_stage_contract.PIPELINE_STAGES}
    abort_records = [record for record in pipeline_records if record.stage == "abort"]
    build_done_records = [
        record for record in pipeline_records if record.stage == "build_done"
    ]
    commit_records = [
        record for record in pipeline_records if record.stage == "commit"
    ]
    for stage, stage_records in (
        ("build_done", build_done_records),
        ("bench_done", benches),
        ("abort", abort_records),
        ("commit", commit_records),
    ):
        issues.extend(_attempt_binding_issues(
            stage_records, stage=stage, expected_attempt_id=expected_attempt_id,
        ))
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
        binding_ok=binding_ok, lifecycle_ok=True,
        legacy_verify=legacy, s2_verify=s2,
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


def _receipt_expectations(
        manifest: Mapping, *,
        contract_resolver: Callable[..., env_contract.GenerationEntry],
):
    """manifest run_contract から env contract と verified calibration を導出する。

    run_contract を持たない (legacy) manifest では None を返し receipt 検査を課さない。
    run_contract を Mapping として宣言するなら env_tag と contract_sha256 はともに
    非空 str を要し、欠落・空・非 str は resolver より前に拒否する。この診断が行へ
    載るのは campaign-start が一意で schedule row を持つ campaign の observation
    経路だけである。directory 欠落、WAL read error、terminal issue の早期 return、
    および 0-row campaign ではこの診断は載らない。"""
    run_contract = manifest.get("run_contract") if isinstance(manifest, Mapping) else None
    if not isinstance(run_contract, Mapping):
        return None
    env_tag = run_contract.get("env_tag")
    contract_sha256 = run_contract.get("contract_sha256")
    if not isinstance(env_tag, str) or not env_tag:
        raise ReportError("manifest.run_contract.env_tag が非空 str でない")
    if not isinstance(contract_sha256, str) or not contract_sha256:
        raise ReportError(
            "manifest.run_contract.contract_sha256 が非空 str でない"
        )
    try:
        entry = contract_resolver(
            contract_sha256, expected_env_tag=env_tag,
        )
        if type(entry) is not env_contract.GenerationEntry:
            raise ReportError(
                "manifest contract resolver が exact GenerationEntry を返さなかった"
            )
        contract = entry.contract
        if (contract.env_tag != env_tag
                or contract.contract_sha256 != contract_sha256):
            raise ReportError(
                "manifest contract resolver の返却 entry が記録 env/hash と不一致"
            )
        verified = env_attestation.load_verified_calibration(contract, ROOT)
    except ReportError:
        raise
    except (env_contract.EnvContractError, env_attestation.AttestationError) as exc:
        raise ReportError(f"manifest env contract を検証できない: {exc}") from exc
    return contract, verified


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


def _campaign_terminal_position_issue(records: Sequence[object]) -> Optional[str]:
    """terminal が存在する場合、その最初の 1 件が物理的な最終 record か検査する。"""
    terminal_ordinal = next((
        index for index, record in enumerate(records)
        if _session_event(record, "campaign-terminal")
    ), None)
    if terminal_ordinal is not None and terminal_ordinal != len(records) - 1:
        return "campaign-terminal が WAL の最終 record でない"
    return None


def _assess_campaign(rows: Sequence[Mapping], campaign_id: str, manifest: Mapping,
                     manifest_sha: str, allowed_excluded: set[str], output_root: Path,
                     expected_reps: int,
                     expected_perf_observation: object,
                     manifest_issue_messages: Sequence[str], *,
                     repo_root: Path,
                     current_receipt_invalid: bool,
                     receipt_expectations,
                     receipt_expectations_error: Optional[ReportError],
                     ) -> tuple[list[dict], _T080CampaignObservation]:
    bases = [_base_row(item) for item in rows]
    layout = _resolved_campaign_layout(campaign_id, output_root)
    root = Path(layout.root)
    if not root.is_dir():
        return ([{**base, "status": "campaign-incomplete", "bench_values": [],
                  "reason": f"campaign-terminal がない (campaign directory 欠落): {campaign_id}"}
                 for base in bases], _T080CampaignObservation("unavailable"))
    try:
        records, line_issues, truncated_tail = wal.read_records_collected(layout)
    except Exception as exc:
        return ([{**base, "status": "protocol_violation",
                  "reason": f"WAL を読めない: {type(exc).__name__}: {exc}"}
                 for base in bases], _T080CampaignObservation("unavailable"))

    t080_observation = _campaign_t080_observation(
        records, repo_root=repo_root,
        current_receipt_invalid=current_receipt_invalid,
    )
    session_identity_issues = _session_identity_issues(records, manifest)
    if session_identity_issues:
        t080_observation = _T080CampaignObservation("unavailable", issue=t080_observation.issue)

    terminal_protocol_issues = [
        issue for issue in (
            _campaign_terminal_position_issue(records),
        )
        if issue is not None
    ]
    terminal_protocol_issues.extend(
        f"WAL record が不正: line {line_number}: {reason}"
        for line_number, reason in line_issues
    )
    terminal_protocol_issues.extend(_inert_record_issues(records))
    terminal_protocol_issues.extend(session_identity_issues)
    if truncated_tail:
        terminal_protocol_issues.append("WAL の末尾 record が途中で切れている")
    if t080_observation.issue is not None:
        terminal_protocol_issues.append(t080_observation.issue)

    record_ordinals = {id(record): ordinal for ordinal, record in enumerate(records)}
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
            protocol_issues = [*payload_issues, *terminal_protocol_issues]
            if protocol_issues:
                output.append({
                    **base, "status": "protocol_violation", "bench_values": [],
                    "reason": "; ".join(dict.fromkeys([
                        *protocol_issues, terminal_issue,
                    ])),
                })
            else:
                output.append({
                    **base, "status": "campaign-incomplete", "bench_values": [],
                    "reason": terminal_issue,
                })
        return output, t080_observation

    campaign_starts = [record.payload for record in records
                       if _session_event(record, "campaign-start")]
    # 通常評価経路では先に合成して correctness-red 診断を materialize する。
    # run-contract 等の issue はここで適用し、ghost issue だけは中央 post-process が
    # early return 行を含む全 row に適用する。
    global_issues: list[str] = list(manifest_issue_messages)
    global_issues.extend(unbound_payload_issues)
    global_issues.extend(terminal_protocol_issues)
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
        expectations = receipt_expectations
        if receipt_expectations_error is not None:
            global_issues.append(str(receipt_expectations_error))
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

    lifecycle_plans = {
        item["schedule_index"]: _attempt_lifecycle_plan(
            item, windows_by_index.get(item["schedule_index"], []), windows,
            record_ordinals,
        )
        for item in rows
    }
    claimed_retry_ids = {
        retry_id
        for plan in lifecycle_plans.values()
        for retry_id in plan["claimed_retry_ids"]
    }
    retry_owner_by_id = {
        id(record): window[0].payload.get("schedule_index")
        for window in windows
        for record in window
        if _session_event(record, "retry")
    }
    lifecycle_global_issues: list[str] = []
    for record in records:
        if not _session_event(record, "retry") or id(record) in claimed_retry_ids:
            continue
        index = record.payload.get("schedule_index")
        owner_index = retry_owner_by_id.get(id(record))
        target_index = owner_index if owner_index in lifecycle_plans else index
        if index not in lifecycle_plans:
            reason = (
                f"schedule 外の retry が attempt lifecycle に束縛されない: {index!r}"
            )
        else:
            reason = "retry が正当な attempt lifecycle に束縛されない"
        if target_index in lifecycle_plans:
            plan = lifecycle_plans[target_index]
            plan["valid"] = False
            if plan["reason"] is None:
                plan["reason"] = reason
        else:
            lifecycle_global_issues.append(reason)

    accounted_result_ids = {
        result_id
        for plan in lifecycle_plans.values()
        for result_id in plan["accounted_result_ids"]
    }
    result_owner_by_id = {
        id(record): window[0].payload.get("schedule_index")
        for window in windows
        for record in window
        if _session_event(record, "trial-result")
    }
    for record in records:
        if (not _session_event(record, "trial-result")
                or id(record) in accounted_result_ids):
            continue
        index = record.payload.get("schedule_index")
        owner_index = result_owner_by_id.get(id(record))
        target_index = owner_index if owner_index in lifecycle_plans else index
        if index not in lifecycle_plans:
            reason = (
                "schedule 外の trial-result が attempt lifecycle に束縛されない: "
                f"{index!r}"
            )
        else:
            reason = "trial-result が正当な attempt lifecycle に束縛されない"
        if target_index in lifecycle_plans:
            plan = lifecycle_plans[target_index]
            plan["valid"] = False
            if plan["reason"] is None:
                plan["reason"] = reason
        else:
            lifecycle_global_issues.append(reason)

    if lifecycle_global_issues:
        for plan in lifecycle_plans.values():
            plan["valid"] = False

    output: list[dict] = []
    for item, base in zip(rows, bases):
        plan = lifecycle_plans[item["schedule_index"]]
        row_windows = windows_by_index.get(item["schedule_index"], [])
        row_payload_issues = payload_issues_by_index.get(item["schedule_index"], [])
        resultful_windows = [
            window for window in row_windows
            if any(_session_event(record, "trial-result") for record in window)
        ]
        assessed = [
            _assess_window(
                item, window, manifest, allowed_excluded, expected_reps,
                record_ordinals, expected_perf_observation,
                [payload_issue_by_record[id(record)] for record in window
                 if id(record) in payload_issue_by_record],
            )
            for window in resultful_windows
        ]
        outcomes = [
            *plan["retried_summaries"],
            *(
                summary
                for assessed_row in assessed
                for summary in assessed_row["attempt_verify_outcomes"]
            ),
        ]
        definitive_reds = [
            assessed_row for assessed_row in assessed
            if assessed_row["status"] == "completed"
            and assessed_row["binding_ok"] is True
            and assessed_row["outcome"] == "correctness-red"
            and "red" in (
                assessed_row["legacy_verify"], assessed_row["s2_verify"])
        ]
        assessed_by_start = {
            id(window[0]): assessed_row
            for window, assessed_row in zip(resultful_windows, assessed)
        }
        terminal_assessed = (
            assessed_by_start.get(id(plan["terminal_window"][0]))
            if plan["terminal_window"] is not None else None
        )
        preferred = (definitive_reds[-1] if definitive_reds
                     else terminal_assessed
                     if terminal_assessed is not None
                     else assessed[-1] if assessed else base)

        forced_protocol_violation = bool(
            global_issues or lifecycle_global_issues or not plan["valid"]
        )
        if not forced_protocol_violation:
            chosen = dict(preferred)
            chosen["attempt_verify_outcomes"] = outcomes
            output.append(chosen)
            continue

        # resultful window は global/lifecycle issue より先に全件 assessment 済み。
        # そのため definitive red と attempt summary を保持したまま、campaign・
        # lifecycle・row-local の各理由を protocol_violation へ合成できる。
        local_reasons = [
            str(assessed_row["reason"])
            for assessed_row in assessed
            if assessed_row.get("reason")
        ]
        reasons = [*row_payload_issues, *global_issues, *lifecycle_global_issues]
        if plan["reason"]:
            reasons.append(str(plan["reason"]))
        elif not plan["valid"] and not lifecycle_global_issues:
            reasons.append("attempt lifecycle が二形のいずれにも一致しない")
        reasons.extend(local_reasons)
        if definitive_reds:
            reasons.append(
                "definitive correctness-red を検出: "
                f"attempt={definitive_reds[-1]['attempt']}"
            )
        chosen = dict(preferred)
        chosen.update(
            status="protocol_violation",
            lifecycle_ok=plan["valid"] and not lifecycle_global_issues,
            bench_values=[],
            reason="; ".join(dict.fromkeys(reasons)),
            attempt_verify_outcomes=outcomes,
        )
        output.append(chosen)
    return output, t080_observation


def _resolve_store_path(*, output_root: Path, store_path: object) -> Path:
    """raw POSIX store path を検査し、root containment を確認する。"""
    if not isinstance(store_path, str) or not store_path:
        raise ReportError("store_path が空でない文字列でない")
    components = store_path.split("/")
    if (store_path.startswith("/") or store_path.endswith("/")
            or "//" in store_path or "\\" in store_path
            or "." in components or ".." in components
            or any(ord(char) < 32 or 127 <= ord(char) <= 159
                   for char in store_path)):
        raise ReportError(f"store_path の raw POSIX path が非正規: {store_path!r}")
    try:
        resolved_root = Path(output_root).resolve(strict=False)
        resolved = (resolved_root / store_path).resolve(strict=False)
        resolved.relative_to(resolved_root)
    except OSError:
        # 存在しない、または読めない root / component は caller で missing にする。
        # raw path は上で containment を崩す字句を拒否済みである。
        return Path(output_root) / store_path
    except (RuntimeError, ValueError) as exc:
        raise ReportError(
            f"store_path が output_root 配下へ解決されない: {store_path!r}"
        ) from exc
    return resolved


def _store_sha256_nofollow(
        *, output_root: Path, store_path: object,
) -> str | None:
    """root fd から symlink を辿らず regular leaf を chunk hash する。"""
    _resolve_store_path(output_root=output_root, store_path=store_path)
    assert isinstance(store_path, str)
    components = store_path.split("/")
    directory_flags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    leaf_flags = (
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    )
    opened: list[int] = []
    try:
        try:
            resolved_root = Path(output_root).resolve(strict=True)
            current_fd = os.open(resolved_root, directory_flags)
        except OSError:
            return None
        opened.append(current_fd)
        for component in components[:-1]:
            try:
                component_stat = os.stat(
                    component, dir_fd=current_fd, follow_symlinks=False,
                )
            except FileNotFoundError:
                return None
            except OSError:
                return None
            if stat.S_ISLNK(component_stat.st_mode):
                raise ReportError(
                    f"store_path parent component が symlink: {store_path!r}"
                )
            if not stat.S_ISDIR(component_stat.st_mode):
                raise ReportError(
                    f"store_path parent component が directory でない: {store_path!r}"
                )
            try:
                next_fd = os.open(component, directory_flags, dir_fd=current_fd)
            except FileNotFoundError:
                return None
            except OSError as exc:
                if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise ReportError(
                        f"store_path parent component を no-follow open できない: "
                        f"{store_path!r}"
                    ) from exc
                return None
            opened.append(next_fd)
            current_fd = next_fd

        leaf = components[-1]
        try:
            leaf_lstat = os.stat(leaf, dir_fd=current_fd, follow_symlinks=False)
        except FileNotFoundError:
            return None
        except OSError:
            return None
        if stat.S_ISLNK(leaf_lstat.st_mode):
            raise ReportError(f"store_path leaf が symlink: {store_path!r}")
        if not stat.S_ISREG(leaf_lstat.st_mode):
            raise ReportError(f"store_path leaf が regular file でない: {store_path!r}")
        try:
            leaf_fd = os.open(leaf, leaf_flags, dir_fd=current_fd)
        except FileNotFoundError:
            return None
        except OSError as exc:
            if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                raise ReportError(
                    f"store_path leaf を no-follow open できない: {store_path!r}"
                ) from exc
            return None
        opened.append(leaf_fd)
        try:
            leaf_fstat = os.fstat(leaf_fd)
        except OSError:
            return None
        if not stat.S_ISREG(leaf_fstat.st_mode):
            raise ReportError(f"store_path leaf が regular file でない: {store_path!r}")
        digest = hashlib.sha256()
        try:
            while True:
                chunk = os.read(leaf_fd, 1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        except OSError:
            return None
        return digest.hexdigest()
    finally:
        for descriptor in reversed(opened):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _build_store_reverification(
        *, schedule: Sequence[Mapping], binaries_by_cell: Mapping,
        output_root: Path,
) -> dict[str, object]:
    """各 store を読んだ瞬間の freeze SHA 一致だけを receipt にする。

    一時改変後に読み取り前に復元された場合と、各読み取り後の差し替えは検出しない。
    certifying path は ``main()`` から直接渡された ``ReverifiedFreeze`` だけである。
    """
    scheduled_cell_ids: set[str] = set()
    for row in schedule:
        holdout_id = row.get("holdout_id")
        configuration_id = row.get("configuration_id")
        if (not isinstance(holdout_id, str) or not holdout_id
                or not isinstance(configuration_id, str) or not configuration_id):
            raise ReportError("schedule の logical cell identity が不正")
        scheduled_cell_ids.add(f"{holdout_id}::{configuration_id}")
    if not scheduled_cell_ids:
        raise ReportError("schedule の logical cell 集合が空")
    if not isinstance(binaries_by_cell, Mapping) or not binaries_by_cell:
        raise ReportError("ReverifiedFreeze.binaries_by_cell が空でない mapping でない")
    if set(binaries_by_cell) != scheduled_cell_ids:
        raise ReportError(
            "ReverifiedFreeze.binaries_by_cell が schedule logical cells を完全被覆しない"
        )

    cells: list[dict[str, object]] = []
    for cell_id in sorted(scheduled_cell_ids):
        record = binaries_by_cell[cell_id]
        if not isinstance(record, Mapping):
            raise ReportError(f"binaries_by_cell[{cell_id!r}] が object でない")
        store_path = record.get("store_path")
        expected_sha256 = record.get("binary_sha256")
        if (not isinstance(expected_sha256, str)
                or _SHA256_RE.fullmatch(expected_sha256) is None):
            raise ReportError(
                f"binaries_by_cell[{cell_id!r}].binary_sha256 が lowercase SHA-256 でない"
            )
        actual_sha256 = _store_sha256_nofollow(
            output_root=output_root, store_path=store_path,
        )
        if actual_sha256 is None:
            state = "missing"
        elif actual_sha256 == expected_sha256:
            state = "match"
        else:
            state = "mismatch"
        cell = {
            "cell_id": cell_id,
            "store_path": store_path,
            "expected_sha256": expected_sha256,
            "actual_sha256": actual_sha256,
            "state": state,
        }
        if set(cell) != _STORE_REVERIFICATION_CELL_KEYS:
            raise ReportError("store_reverification cell construction schema が不一致")
        cells.append(cell)
    outer_state = (
        "verified" if all(cell["state"] == "match" for cell in cells)
        else "unverified"
    )
    receipt: dict[str, object] = {"state": outer_state, "cells": cells}
    if (set(receipt) != _STORE_REVERIFICATION_KEYS
            or receipt["state"] not in _STORE_REVERIFICATION_STATES
            or any(cell["state"] not in _STORE_REVERIFICATION_CELL_STATES
                   for cell in cells)):
        raise ReportError("store_reverification construction schema が不一致")
    return receipt


def build_observations(
    *, manifest: (
        s8b_oracle_manifest.VerifiedManifest | _artifacts.LegacyManifest
    ),
    output_root: Path,
    repo_root: Path = ROOT,
    reverified_freeze: s8b_ratified_freeze.ReverifiedFreeze | None = None,
) -> _artifacts.OfficialObservations:
    """manifest 所有 campaign だけから JSON-safe な全件 observations を作る。

    pathname の検査と再検査は stable filesystem 上の永続交換を検出する境界である。
    namespace component、campaign path、WAL、store の同一 UID ABA race まで閉じない。
    """
    if type(manifest) not in {
            s8b_oracle_manifest.VerifiedManifest, _artifacts.LegacyManifest}:
        raise _artifacts.OracleArtifactTypeError(
            "build_observations は VerifiedManifest/LegacyManifest exact type のみ受理する")
    if (reverified_freeze is not None
            and type(reverified_freeze) is not s8b_ratified_freeze.ReverifiedFreeze):
        raise ReportError("reverified_freeze は ReverifiedFreeze exact type が必要")
    if type(manifest) is s8b_oracle_manifest.VerifiedManifest:
        document = manifest.document
        manifest_kind = "official"
        (schedule, allowed_excluded, _legacy_sha, n, expected_reps,
         manifest_issues) = _validate_manifest(document)
        if _canonical_sha256(document) != manifest.sha256:
            raise ReportError(
                "VerifiedManifest document canonical hash が sha256 と不一致"
            )
        manifest_sha = manifest.sha256
        spec_sha = document["spec_sha256"]
        if reverified_freeze is not None:
            freeze_record = document.get("freeze")
            if (not isinstance(freeze_record, Mapping)
                    or freeze_record.get("sha256")
                    != reverified_freeze.ratified.sha256):
                raise ReportError(
                    "ReverifiedFreeze の freeze sha256 が manifest.freeze.sha256 と不一致"
                )
    else:
        if reverified_freeze is not None:
            raise ReportError("legacy manifest は reverified_freeze を受理しない")
        document = manifest
        manifest_kind = "legacy"
        spec_sha = None
        (schedule, allowed_excluded, manifest_sha, n, expected_reps,
         manifest_issues) = _validate_manifest(document)
    by_block, campaign_ids, declaration_issues = _campaign_index(
        document["campaign_ids"], schedule,
    )
    manifest_issues.extend(declaration_issues)
    try:
        receipt_resolution = _t080.inspect_receipt_history(root=Path(repo_root))
    except _t080.MigrationError as exc:
        raise ReportError(f"T-080 receipt を検証できない: {exc}") from exc
    if receipt_resolution.state not in {
        "never-issued", "active-valid", "issued-but-missing", "invalid",
    }:
        raise ReportError("T-080 receipt state を分類できない")
    current_receipt_invalid = (
        receipt_resolution.state == "issued-but-missing"
        or (receipt_resolution.state == "invalid" and bool(receipt_resolution.refusals))
    )
    admitted_output_root = _resolve_official_output_root(Path(output_root))
    resolved_output_root = admitted_output_root.path
    campaign_verifier_epochs = [
        _campaign_verifier_epoch_projection(campaign_id, resolved_output_root)
        for campaign_id in sorted(campaign_ids)
    ]
    receipt_expectations = None
    receipt_expectations_error = None
    try:
        receipt_expectations = _receipt_expectations(
            document,
            contract_resolver=env_contract.resolve_by_contract_sha256,
        )
    except ReportError as exc:
        receipt_expectations_error = exc
    ghost_issues = [
        issue for issue in manifest_issues
        if issue["code"] == "campaign-without-schedule-row"
    ]
    assessed_manifest_issue_messages = [
        issue["message"] for issue in manifest_issues
        if issue["code"] != "campaign-without-schedule-row"
    ]
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
    measurement_conditions = [
        _measurement_condition_for_campaign(
            campaign_id,
            manifest_sha,
            {
                str(item.get("block_id"))
                for _ordinal, item in grouped[campaign_id]
                if isinstance(item.get("block_id"), str)
            },
            resolved_output_root,
        )
        for campaign_id in sorted(campaign_ids)
    ]
    measurement_conditions_by_campaign = {
        condition["campaign_id"]: condition
        for condition in measurement_conditions
    }
    by_ordinal: dict[int, dict] = {}
    t080_by_campaign: dict[str, _T080CampaignObservation] = {}
    for campaign_id in sorted(grouped):
        if grouped[campaign_id]:
            ordinals, items = zip(*grouped[campaign_id])
            assessed, t080_observation = _assess_campaign(
                items, campaign_id, document, manifest_sha,
                allowed_excluded, resolved_output_root,
                expected_reps,
                measurement_conditions_by_campaign[campaign_id]["perf_observation"],
                assessed_manifest_issue_messages,
                repo_root=Path(repo_root),
                current_receipt_invalid=current_receipt_invalid,
                receipt_expectations=receipt_expectations,
                receipt_expectations_error=receipt_expectations_error,
            )
            t080_by_campaign[campaign_id] = t080_observation
            for ordinal, row in zip(ordinals, assessed):
                row["campaign_id"] = campaign_id
                by_ordinal[ordinal] = row
    for ordinal, item, reason in detached:
        base = _base_row(item)
        base.update(
            campaign_id=None, status="protocol_violation", reason=reason,
        )
        by_ordinal[ordinal] = base

    campaign_observations = list(t080_by_campaign.values())
    canonical_values = {
        item.canonical for item in campaign_observations
        if (item.kind == "envelope" and item.canonical is not None
            and item.issue is None)
    }

    t080_report_observation = None
    if (campaign_observations
            and all(item.kind == "envelope" for item in campaign_observations)
            and all(item.issue is None for item in campaign_observations)
            and len(canonical_values) == 1
            and not current_receipt_invalid
            and not ghost_issues):
        canonical = next(iter(canonical_values))
        t080_report_observation = json.loads(canonical.decode("utf-8"))
    rows = [by_ordinal[ordinal] for ordinal in range(len(schedule))]
    for issue in ghost_issues:
        _force_protocol_violation(rows, issue["message"])
    expected_cells = [{
        "schedule_index": item["schedule_index"],
        "holdout_id": item["holdout_id"],
        "configuration_id": item["configuration_id"],
    } for item in schedule]
    store_reverification = None
    if reverified_freeze is not None:
        store_reverification = _build_store_reverification(
            schedule=schedule,
            binaries_by_cell=reverified_freeze.binaries_by_cell,
            output_root=resolved_output_root,
        )
    result = _artifacts.OfficialObservations({
        "schema_version": SCHEMA_VERSION,
        "manifest_kind": manifest_kind,
        "manifest_sha256": manifest_sha,
        "n_per_cell": n,
        "expected_cells": expected_cells,
        "rows": rows,
        "manifest_issues": [dict(issue) for issue in manifest_issues],
        "campaign_verifier_epochs": campaign_verifier_epochs,
        _T080_KEY: t080_report_observation,
    })
    if spec_sha is not None:
        result["spec_sha256"] = spec_sha
    if store_reverification is not None:
        result["store_reverification"] = store_reverification
    if any(
            condition["perf_observation"] is not None
            for condition in measurement_conditions):
        result["measurement_conditions"] = measurement_conditions
    _revalidate_official_output_root(admitted_output_root)
    return result


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
    report.add_argument("--repo-root", type=Path, default=ROOT)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = _artifacts.load_official_manifest(args.manifest)
        root = Path(args.repo_root)
        build_kwargs: dict[str, object] = {}
        if type(manifest) is _artifacts.OfficialManifest:
            ratified = s8b_ratified_freeze.load_ratified_freeze(root)
            reverified = s8b_ratified_freeze.reverify_published_freeze(
                ratified, root,
            )
            approved = s8b_oracle_spec.load_approved_spec(root)
            manifest = s8b_oracle_manifest.verify_manifest(
                args.manifest,
                root=root,
                freeze_document=reverified.ratified.document,
                freeze_sha256=reverified.ratified.sha256,
                approved_spec=approved,
            )
            build_kwargs["reverified_freeze"] = reverified
        observations = build_observations(
            manifest=manifest, output_root=args.output_root, repo_root=root,
            **build_kwargs,
        )
        _write_create_only(args.out, observations)
    except (OSError, json.JSONDecodeError, _artifacts.OracleArtifactTypeError,
            s8b_ratified_freeze.RatifiedFreezeError,
            s8b_oracle_spec.ReviewedSpecError,
            s8b_oracle_manifest.ManifestError, _freeze_io.FreezeIOError,
            ReportError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
