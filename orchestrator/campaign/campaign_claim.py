# -*- coding: utf-8 -*-
"""single-process campaign の one-shot claim leaf。"""
from __future__ import annotations

import datetime as dt
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path


class ClaimError(ValueError):
    """claim record の型・値・UTC 表記が不正。"""

    def __init__(
        self,
        message: str,
        *,
        existing_record: "ClaimRecord | None" = None,
        claim_path: Path | None = None,
    ) -> None:
        super().__init__(message)
        self.existing_record = existing_record
        self.claim_path = claim_path


def _text(value: object, field: str) -> None:
    if type(value) is not str or not value:
        raise ClaimError(f"{field} は非空 str でなければならない")


@dataclass(frozen=True)
class ClaimRecord:
    """campaign identity と所有 process を束縛する immutable record。"""

    campaign_identity: str
    job_id: str
    host: str
    boot_id: str
    pid: int
    proc_starttime: int
    created_utc: str

    def __post_init__(self) -> None:
        for field in ("campaign_identity", "job_id", "host", "boot_id"):
            _text(getattr(self, field), field)
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


def read_proc_starttime(*, stat_text: str | None = None) -> int:
    """``/proc/self/stat`` の第 22 field (process starttime) を strict に読む。"""
    if stat_text is None:
        try:
            with open("/proc/self/stat", "r", encoding="ascii") as stream:
                stat_text = stream.read()
        except OSError as exc:
            raise ClaimError("/proc/self/stat を読み取れない") from exc
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
    try:
        starttime = int(fields_from_three[starttime_index], 10)
    except ValueError as exc:
        raise ClaimError("proc stat 第 22 field が整数でない") from exc
    if starttime <= 0:
        raise ClaimError("proc stat 第 22 field は正整数でなければならない")
    return starttime


def _claim_path(claim_root: Path, identity: str) -> Path:
    if type(identity) is not str or not identity or identity in {".", ".."}:
        raise ClaimError("campaign_identity は安全な filename component でなければならない")
    if Path(identity).name != identity or "/" in identity or "\\" in identity or "\x00" in identity:
        raise ClaimError("campaign_identity は安全な filename component でなければならない")
    return claim_root / f"{identity}.claim"


def _decode_record(raw: bytes, path: Path) -> ClaimRecord:
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
        raise ClaimError("既存 claim record を構造化して読めない", claim_path=path) from exc
    if type(payload) is not dict:
        raise ClaimError("既存 claim record が JSON object でない", claim_path=path)
    try:
        return ClaimRecord(**payload)
    except (TypeError, ClaimError) as exc:
        raise ClaimError("既存 claim record の schema が不正", claim_path=path) from exc


def _read_existing_record(path: Path) -> ClaimRecord:
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
        while True:
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            total += len(chunk)
            if total > 1 << 20:
                raise ClaimError("既存 claim record が大きすぎる", claim_path=path)
            chunks.append(chunk)
    finally:
        os.close(fd)
    return _decode_record(b"".join(chunks), path)


def _existing_owner_after_collision(path: Path) -> ClaimRecord:
    # O_EXCL の directory entry は winner の write より先に見える。短い競合窓だけ
    # bounded retry し、winner crash/破損時は削除せず fail-closed にする。
    last_error = None
    for _ in range(50):
        try:
            return _read_existing_record(path)
        except ClaimError as exc:
            last_error = exc
            time.sleep(0.001)
    assert last_error is not None
    raise last_error


def acquire_claim(claim_root: Path, record: ClaimRecord) -> AcquiredClaim:
    """``<identity>.claim`` を O_EXCL で一度だけ獲得し JSON を fsync する。

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
        existing = _existing_owner_after_collision(path)
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
    return AcquiredClaim(path=path, record=record)
