# -*- coding: utf-8 -*-
"""single-process campaign の one-shot claim leaf。"""
from __future__ import annotations

import datetime as dt
import json
import os
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path


class ClaimError(ValueError):
    """claim の policy refusal または fail-closed operational error。"""

    def __init__(
        self,
        message: str,
        *,
        existing_record: "ClaimRecord | None" = None,
        claim_path: Path | None = None,
        raw_payload: bytes | None = None,
        conflict: "ClaimConflict | None" = None,
    ) -> None:
        super().__init__(message)
        self.existing_record = existing_record
        self.claim_path = claim_path
        self.raw_payload = raw_payload
        self.conflict = conflict


def _text(value: object, field: str) -> None:
    if type(value) is not str or not value:
        raise ClaimError(f"{field} は非空 str でなければならない")


@dataclass(frozen=True)
class ClaimRecord:
    """campaign identity と所有 process を束縛する immutable record。"""

    campaign_identity: str
    protocol_digest: str
    job_id: str
    host: str
    boot_id: str
    pid: int
    proc_starttime: int
    created_utc: str

    def __post_init__(self) -> None:
        for field in ("campaign_identity", "job_id", "host", "boot_id"):
            _text(getattr(self, field), field)
        if (
            type(self.protocol_digest) is not str
            or len(self.protocol_digest) != 64
            or any(char not in "0123456789abcdef" for char in self.protocol_digest)
        ):
            raise ClaimError("protocol_digest は 64 桁小文字 hex でなければならない")
        for field in ("pid", "proc_starttime"):
            value = getattr(self, field)
            if type(value) is not int or value <= 0:
                raise ClaimError(f"{field} は正整数でなければならない")
        _text(self.created_utc, "created_utc")
        raw = self.created_utc
        try:
            parsed = dt.datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
        except ValueError as exc:
            raise ClaimError("created_utc は timezone-aware UTC ISO 形式でなければならない") from exc
        if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
            raise ClaimError("created_utc は timezone-aware UTC ISO 形式でなければならない")


@dataclass(frozen=True)
class AcquiredClaim:
    """fsync 済み one-shot claim。release API は意図的に持たない。"""

    path: Path
    record: ClaimRecord


class _OwnerState(Enum):
    LIVE = "live"
    DEAD = "dead"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class _OwnerObservation:
    owner_state: _OwnerState
    observed_boot_id: str
    observed_state: str | None
    observed_starttime: int | None
    classification_reason: str


@dataclass(frozen=True)
class ClaimConflict:
    """同一 protocol の live owner と、その分類に使った観測値。"""

    path: Path
    record: ClaimRecord
    observed_boot_id: str
    observed_state: str | None
    observed_starttime: int | None
    classification_reason: str


def _parse_proc_stat(stat_text: str) -> tuple[str, int]:
    if type(stat_text) is not str or not stat_text:
        raise ClaimError("proc stat は非空 str でなければならない")

    # comm は空白や ')' を含みうるため、最後の ") " を field 2 の終端とする。
    comm_end = stat_text.rfind(") ")
    if comm_end < 0:
        raise ClaimError("proc stat の comm field が不正")
    fields_from_three = stat_text[comm_end + 2:].split()
    starttime_index = 22 - 3
    if len(fields_from_three) <= starttime_index:
        raise ClaimError("proc stat に第 22 field がない")
    state = fields_from_three[0]
    if len(state) != 1 or state not in "RSDZTtXxKWPI":
        raise ClaimError("proc stat の state field が不正")
    try:
        starttime = int(fields_from_three[starttime_index], 10)
    except ValueError as exc:
        raise ClaimError("proc stat 第 22 field が整数でない") from exc
    if starttime <= 0:
        raise ClaimError("proc stat 第 22 field は正整数でなければならない")
    return state, starttime


def read_proc_starttime(*, stat_text: str | None = None) -> int:
    """``/proc/self/stat`` の第 22 field (process starttime) を strict に読む。"""
    if stat_text is None:
        try:
            with open("/proc/self/stat", "r", encoding="ascii") as stream:
                stat_text = stream.read()
        except OSError as exc:
            raise ClaimError("/proc/self/stat を読み取れない") from exc
    return _parse_proc_stat(stat_text)[1]


def _read_boot_id() -> str:
    try:
        with open("/proc/sys/kernel/random/boot_id", "r", encoding="ascii") as stream:
            boot_id = stream.read().strip()
    except OSError as exc:
        raise ClaimError("current boot_id を読み取れない") from exc
    if not boot_id:
        raise ClaimError("current boot_id が空")
    return boot_id


def _read_proc_stat_for_pid(pid: int) -> tuple[str, int] | None:
    path = f"/proc/{pid}/stat"
    try:
        with open(path, "r", encoding="ascii") as stream:
            stat_text = stream.read()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ClaimError(f"{path} を読み取れない") from exc
    try:
        return _parse_proc_stat(stat_text)
    except ClaimError as exc:
        raise ClaimError(f"{path} を構造化して読めない") from exc


def _claim_path(claim_root: Path, identity: str) -> Path:
    if type(identity) is not str or not identity or identity in {".", ".."}:
        raise ClaimError("campaign_identity は安全な filename component でなければならない")
    if Path(identity).name != identity or "/" in identity or "\\" in identity or "\x00" in identity:
        raise ClaimError("campaign_identity は安全な filename component でなければならない")
    return claim_root / f"{identity}.claim"


def _decode_payload(raw: bytes, path: Path) -> dict:
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ClaimError(f"既存 claim に duplicate key がある: {key}", claim_path=path)
            result[key] = value
        return result

    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError, ClaimError) as exc:
        raise ClaimError(
            "既存 claim record を構造化して読めない",
            claim_path=path,
            raw_payload=raw,
        ) from exc
    if type(payload) is not dict:
        raise ClaimError(
            "既存 claim record が JSON object でない",
            claim_path=path,
            raw_payload=raw,
        )
    return payload


def _decode_record(raw: bytes, path: Path) -> ClaimRecord:
    payload = _decode_payload(raw, path)
    try:
        return ClaimRecord(**payload)
    except (TypeError, ClaimError) as exc:
        raise ClaimError(
            "既存 claim record の schema が不正",
            claim_path=path,
            raw_payload=raw,
        ) from exc


def _read_existing_payload(path: Path) -> bytes:
    flags = os.O_RDONLY
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ClaimError("O_NOFOLLOW が利用できず既存 claim を安全に読めない", claim_path=path)
    flags |= nofollow
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ClaimError("既存 claim record を開けない", claim_path=path) from exc
    try:
        chunks = []
        total = 0
        try:
            while True:
                chunk = os.read(fd, 4096)
                if not chunk:
                    break
                total += len(chunk)
                if total > 1 << 20:
                    raise ClaimError("既存 claim record が大きすぎる", claim_path=path)
                chunks.append(chunk)
        except OSError as exc:
            raise ClaimError("既存 claim record を読み取れない", claim_path=path) from exc
    finally:
        os.close(fd)
    return b"".join(chunks)


def _read_existing_record(path: Path) -> ClaimRecord:
    raw = _read_existing_payload(path)
    return _decode_record(raw, path)


_LEGACY_RECORD_KEYS = {
    "campaign_identity",
    "job_id",
    "host",
    "boot_id",
    "pid",
    "proc_starttime",
    "created_utc",
}


def _decode_scanned_record(raw: bytes, path: Path) -> ClaimRecord | None:
    payload = _decode_payload(raw, path)
    if "protocol_digest" not in payload:
        if set(payload) != _LEGACY_RECORD_KEYS:
            raise ClaimError(
                "既存 claim record の schema が不正",
                claim_path=path,
                raw_payload=raw,
            )
        try:
            ClaimRecord(protocol_digest="0" * 64, **payload)
        except (TypeError, ClaimError) as exc:
            raise ClaimError(
                "legacy claim record の schema が不正",
                claim_path=path,
                raw_payload=raw,
            ) from exc
        return None
    return _decode_record(raw, path)


def _claim_entries(claim_root: Path) -> list[Path]:
    try:
        with os.scandir(claim_root) as entries:
            paths = [
                claim_root / entry.name
                for entry in entries
                if entry.name.endswith(".claim")
            ]
    except OSError as exc:
        raise ClaimError("claim root を列挙できない", claim_path=claim_root) from exc
    return sorted(paths, key=lambda path: path.name)


def _owner_state(record: ClaimRecord, *, current_boot_id: str) -> _OwnerObservation:
    if record.boot_id != current_boot_id:
        return _OwnerObservation(
            owner_state=_OwnerState.INDETERMINATE,
            observed_boot_id=current_boot_id,
            observed_state=None,
            observed_starttime=None,
            classification_reason="boot-id-mismatch",
        )
    stat = _read_proc_stat_for_pid(record.pid)
    if stat is None:
        return _OwnerObservation(
            owner_state=_OwnerState.DEAD,
            observed_boot_id=current_boot_id,
            observed_state=None,
            observed_starttime=None,
            classification_reason="proc-not-found",
        )
    state, starttime = stat
    if state == "Z":
        owner_state = _OwnerState.DEAD
        reason = "zombie"
    elif starttime != record.proc_starttime:
        owner_state = _OwnerState.DEAD
        reason = "proc-starttime-mismatch"
    else:
        owner_state = _OwnerState.LIVE
        reason = "live-owner"
    return _OwnerObservation(
        owner_state=owner_state,
        observed_boot_id=current_boot_id,
        observed_state=state,
        observed_starttime=starttime,
        classification_reason=reason,
    )


_SCAN_DECODE_ATTEMPTS = 50
_SCAN_DECODE_RETRY_SECONDS = 0.01


def _read_scanned_record(path: Path) -> ClaimRecord | None:
    for attempt in range(_SCAN_DECODE_ATTEMPTS):
        raw = _read_existing_payload(path)
        try:
            return _decode_scanned_record(raw, path)
        except ClaimError:
            if attempt + 1 == _SCAN_DECODE_ATTEMPTS:
                raise
            time.sleep(_SCAN_DECODE_RETRY_SECONDS)
    raise AssertionError("scan decode retry loop が終端しなかった")


def _scan_protocol_conflicts(
    claim_root: Path,
    *,
    excluding_path: Path,
    protocol_digest: str,
    current_boot_id: str,
) -> ClaimConflict | None:
    for path in _claim_entries(claim_root):
        if path == excluding_path:
            continue
        existing = _read_scanned_record(path)
        if existing is None or existing.protocol_digest != protocol_digest:
            continue
        observation = _owner_state(existing, current_boot_id=current_boot_id)
        if observation.owner_state is _OwnerState.LIVE:
            return ClaimConflict(
                path=path,
                record=existing,
                observed_boot_id=observation.observed_boot_id,
                observed_state=observation.observed_state,
                observed_starttime=observation.observed_starttime,
                classification_reason=observation.classification_reason,
            )
    return None


def _raise_protocol_conflict(conflict: ClaimConflict, *, path: Path) -> None:
    raise ClaimError(
        f"同一 protocol の campaign claim は既に {conflict.record.pid} が所有している",
        existing_record=conflict.record,
        claim_path=path,
        conflict=conflict,
    )


def acquire_claim(claim_root: Path, record: ClaimRecord) -> AcquiredClaim:
    """同一 protocol の live owner を走査後、claim を O_EXCL で獲得する。

    claim は crash 後も残す。stale 判定、自動削除、release は意図的に存在しない。
    atomic ``O_EXCL`` が保証される Lustre / NFSv4 を前提とする。NFSv3 は対象外。
    複数 clone/worktree 間の排他も claim root を含む ``out_root`` を共有している場合に
    限って成立する。clone ごとに別 out_root を与えた実行同士はこの leaf では排他できない。
    """
    if not isinstance(claim_root, Path):
        try:
            claim_root = Path(claim_root)
        except TypeError as exc:
            raise ClaimError("claim_root は PathLike でなければならない") from exc
    if not isinstance(record, ClaimRecord):
        raise ClaimError("record は ClaimRecord でなければならない")
    if not claim_root.is_dir():
        raise ClaimError("claim_root は既存 directory でなければならない")
    path = _claim_path(claim_root, record.campaign_identity)
    current_boot_id = _read_boot_id()
    current_starttime = read_proc_starttime()
    if (
        record.pid != os.getpid()
        or record.proc_starttime != current_starttime
        or record.boot_id != current_boot_id
    ):
        raise ClaimError("claim record の process identity が self の実測値と一致しない")
    conflict = _scan_protocol_conflicts(
        claim_root,
        excluding_path=path,
        protocol_digest=record.protocol_digest,
        current_boot_id=current_boot_id,
    )
    if conflict is not None:
        _raise_protocol_conflict(conflict, path=path)
    payload = (
        json.dumps(asdict(record), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ClaimError("O_NOFOLLOW が利用できない", claim_path=path)
    flags |= nofollow
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        existing = _read_existing_record(path)
        raise ClaimError(
            f"campaign claim は既に {existing.pid} が所有している",
            existing_record=existing,
            claim_path=path,
        ) from exc
    except OSError as exc:
        raise ClaimError("campaign claim の原子的作成に失敗", claim_path=path) from exc

    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise ClaimError("campaign claim の書込みが進行しない", claim_path=path)
            view = view[written:]
        os.fsync(fd)
    except OSError as exc:
        # 部分 claim も自動削除しない。手動回収だけが裁定済み経路。
        raise ClaimError("campaign claim の write/fsync に失敗", claim_path=path) from exc
    finally:
        os.close(fd)

    try:
        directory_fd = os.open(claim_root, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        raise ClaimError("campaign claim directory の fsync に失敗", claim_path=path) from exc
    conflict = _scan_protocol_conflicts(
        claim_root,
        excluding_path=path,
        protocol_digest=record.protocol_digest,
        current_boot_id=current_boot_id,
    )
    if conflict is not None:
        _raise_protocol_conflict(conflict, path=path)
    return AcquiredClaim(path=path, record=record)
