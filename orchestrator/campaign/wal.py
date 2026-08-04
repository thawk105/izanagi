# -*- coding: utf-8 -*-
"""WAL (write-ahead log) と クラッシュリカバリ (orchestrator-design.md D/A)。

探索は一晩回しっぱなしでクラッシュ前提。各 variant の評価を**ログ先行書き込み**で
進め (`build_start → build_done → verify_done → bench_done → commit`)、再起動時に
リプレイして「どこまで評価済みか」を復元し途中再開する。

- **D (durability):** 追記ごとに flush+fsync。クラッシュで追記済みレコードを失わない。
- **A (atomicity):** commit レコードがある variant だけ採用。なければ破棄して再評価
  (half-evaluated を population に混ぜない)。
- **末尾切れトレラント:** 追記中のクラッシュで最終行が壊れていても、その 1 行だけ
  捨ててリプレイを続ける (WAL の定石)。

各行は duplicate key と record の基本形を構造検査する。hash chain はなく、任意の
変更に対する真正性を保証するものではない。
"""
from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import math
import os
import stat
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterator, List, Optional

from .build_admission import (
    ADMISSION_SCHEMA_V2,
    BuildAdmissionError,
    BuildAdmissionPolicy,
    validate_build_admission_receipt,
)
from .trigger_gate_language import TRIGGER_GATE_LANGUAGE
from .layout import CampaignLayout
from .model import (
    STAGE_ABORT,
    STAGE_BUILD_DONE,
    STAGE_BUILD_START,
    STAGE_COMMIT,
    WAL_STAGES,
    BuildAttemptState,
    EvalState,
    WalRecord,
)


# ---- シリアライズ ----

class WalLineError(ValueError):
    """WAL 1 行が record 契約を満たさない。"""


class WalDuplicateKeyError(WalLineError):
    """WAL の JSON object に duplicate key がある。"""


class WalFramingError(WalLineError):
    """WAL に newline 終端の無い最終 frame がある。"""


class WalPayloadTypeError(WalLineError):
    """payload の値が WAL の JSON-native 型契約を満たさない。"""

    def __init__(self, message: str, path: Optional[str] = None):
        super().__init__(message)
        self.path = path


class WalAppendError(RuntimeError):
    """WAL 追記の末尾 gate / write / fsync / close が失敗した。"""

    def __init__(self, wal_path: str, total_bytes: int, written_bytes: int,
                 phase: str, cause: BaseException):
        if phase not in {"tail-gate", "write", "fsync", "close"}:
            raise ValueError("unknown WAL append phase: %r" % phase)
        super().__init__(
            "WAL append failed during %s (%d/%d bytes): %s"
            % (phase, written_bytes, total_bytes, cause)
        )
        self.wal_path = wal_path
        self.total_bytes = total_bytes
        self.written_bytes = written_bytes
        self.phase = phase
        self.cause = cause


class AttemptTopologyError(ValueError):
    """Admission-aware WAL records do not form attempt-local transactions."""


class ReceiptlessAbortReason(str, Enum):
    """Closed issuer vocabulary for failures before an admission receipt exists."""

    TRIGGER_GATE_REJECT = "trigger-gate-reject"
    IDENTITY_ERROR = "identity-error"
    ADMISSION_ERROR = "admission-error"
    DIFF_QUARANTINE = "diff-quarantine"
    EVAL_EXCEPTION = "eval-exception"


@dataclass(frozen=True)
class WalTailRepairResult:
    status: str
    original_size: int
    final_size: int
    removed_bytes: int
    removed_sha256: Optional[str]
    preview: str
    receipt_path: Optional[str]


def _reject_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise WalDuplicateKeyError("duplicate key in WAL JSON object: %r" % key)
        value[key] = item
    return value


def _reject_json_constant(value: str):
    raise WalPayloadTypeError(
        "non-finite JSON constant is not allowed: %s" % value,
        path=None,
    )


def _payload_path(parent: str, item) -> str:
    if isinstance(item, int):
        return "%s[%d]" % (parent, item)
    return "%s[%s]" % (parent, json.dumps(item, ensure_ascii=True))


def _validate_string(value: str, path: str) -> None:
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise WalPayloadTypeError(
            "lone surrogate is not allowed in WAL payload at %s" % path,
            path=path,
        )


def _validate_payload(value, path: str = "payload",
                      active: Optional[set[int]] = None) -> None:
    """JSON-native/finite payload を深部まで検査する。

    container の active recursion stack だけを cycle とし、共有 DAG は許容する。
    """
    if active is None:
        active = set()
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, str):
        _validate_string(value, path)
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise WalPayloadTypeError(
                "non-finite float is not allowed in WAL payload at %s" % path,
                path=path,
            )
        return
    if isinstance(value, (dict, list)):
        identity = id(value)
        if identity in active:
            raise WalPayloadTypeError(
                "cycle is not allowed in WAL payload at %s" % path,
                path=path,
            )
        active.add(identity)
        try:
            if isinstance(value, dict):
                for key, item in value.items():
                    # key 型と文字列内容は別の防壁: isinstance 後も surrogate を検査する。
                    if not isinstance(key, str):
                        key_path = "%s[<key>]" % path
                        raise WalPayloadTypeError(
                            "WAL payload object key must be a string at %s"
                            % key_path,
                            path=key_path,
                        )
                    key_path = _payload_path(path, key)
                    _validate_string(key, key_path)
                    _validate_payload(item, key_path, active)
            else:
                for index, item in enumerate(value):
                    _validate_payload(item, _payload_path(path, index), active)
        finally:
            active.remove(identity)
        return
    raise WalPayloadTypeError(
        "unsupported WAL payload type %s at %s"
        % (type(value).__name__, path),
        path=path,
    )


def parse_line(line: str) -> WalRecord:
    """WAL 1 行を duplicate-aware に parse し、基本 record 契約を検査する。

    stage は generic WAL 白名簿で fail-closed に検査する。event topology と
    payload object 内の個別 schema は consumer 側の責務。
    空行は writer が生成しないため、record として受理しない。
    """
    if not line.strip():
        raise WalLineError("WAL line must not be empty")
    value = json.loads(
        line,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(value, dict):
        raise WalLineError("WAL record must be a JSON object")
    required = {"variant", "stage", "env_tag", "ts", "payload"}
    if set(value) != required:
        missing = sorted(required - set(value))
        unknown = sorted(set(value) - required)
        raise WalLineError(
            "WAL record keys must be exactly %r (missing=%r, unknown=%r)"
            % (sorted(required), missing, unknown)
        )
    if not isinstance(value["variant"], str):
        raise WalLineError("WAL variant must be a string")
    if not isinstance(value["stage"], str):
        raise WalLineError("WAL stage must be a string")
    if value["stage"] not in WAL_STAGES:
        raise WalLineError("unknown WAL stage: %r" % value["stage"])
    if not isinstance(value["env_tag"], str):
        raise WalLineError("WAL env_tag must be a string")
    ts = value["ts"]
    if (isinstance(ts, bool) or not isinstance(ts, (int, float))
            or (isinstance(ts, float) and not math.isfinite(ts))):
        raise WalLineError("WAL ts must be a finite number other than bool")
    if not isinstance(value["payload"], dict):
        raise WalLineError("WAL payload must be a JSON object")
    _validate_payload(value["payload"])
    return WalRecord(
        variant=value["variant"], stage=value["stage"], env_tag=value["env_tag"],
        ts=ts, payload=value["payload"],
    )


def _record_to_line(r: WalRecord) -> str:
    if not isinstance(r.variant, str):
        raise WalLineError("WAL variant must be a string")
    if not isinstance(r.stage, str):
        raise WalLineError("WAL stage must be a string")
    if r.stage not in WAL_STAGES:
        raise WalLineError("unknown WAL stage: %r" % r.stage)
    if not isinstance(r.env_tag, str):
        raise WalLineError("WAL env_tag must be a string")
    if (isinstance(r.ts, bool) or not isinstance(r.ts, (int, float))
            or (isinstance(r.ts, float) and not math.isfinite(r.ts))):
        raise WalLineError("WAL ts must be a finite number other than bool")
    if not isinstance(r.payload, dict):
        raise WalPayloadTypeError(
            "WAL payload root must be a JSON object at payload", path="payload",
        )
    _validate_payload(r.payload)
    obj = {"variant": r.variant, "stage": r.stage, "env_tag": r.env_tag,
           "ts": r.ts, "payload": r.payload}
    return json.dumps(
        obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False,
    )


def _line_to_record(line: str) -> WalRecord:
    return parse_line(line)


def _iter_binary_frames(
        path: str | os.PathLike[str],
) -> Iterator[tuple[int, bytes, bool, bool]]:
    """``(line_number, bytes, is_last, terminated)`` を byte 単位で返す。"""
    with open(path, "rb") as stream:
        current = stream.readline()
        line_number = 1
        while current:
            following = stream.readline()
            yield (line_number, current, not following,
                   current.endswith(b"\n"))
            current = following
            line_number += 1


def iter_lines(path: str | os.PathLike[str]) -> Iterator[tuple[int, str, bool]]:
    """WAL の全物理行を ``(行番号, text, 最終物理行か)`` として返す。

    空行を含めて一行も省略しない。各 consumer は :func:`parse_line` を通すことで
    同じ空行・record 契約を適用する。
    """
    for line_number, frame, is_last, terminated in _iter_binary_frames(path):
        if not terminated:
            raise WalFramingError(
                "WAL line %d is not newline-terminated" % line_number
            )
        yield line_number, frame.decode("utf-8"), is_last


# ---- 追記 (D) ----

def _append_error(layout: CampaignLayout, total: int, written: int,
                  phase: str, cause: BaseException) -> WalAppendError:
    return WalAppendError(
        os.fspath(layout.wal_file), total, written, phase, cause,
    )


def append(layout: CampaignLayout, record: WalRecord) -> None:
    """WAL に 1 frame を排他追記し、file/dir を fsync する。"""
    # 拒否された record で directory/file 側の効果を起こさない。
    line = _record_to_line(record) + "\n"
    parse_line(line)
    encoded = line.encode("utf-8")
    total = len(encoded)
    written = 0
    try:
        os.makedirs(layout.runs_dir, exist_ok=True)
        flags = (os.O_RDWR | os.O_APPEND | os.O_CREAT
                 | os.O_NOFOLLOW | os.O_CLOEXEC)
        fd = os.open(layout.wal_file, flags, 0o644)
    except OSError as exc:
        raise _append_error(layout, total, written, "tail-gate", exc) from exc
    try:
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX)
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode):
                    raise OSError(errno.EINVAL, "WAL is not a regular file")
                if info.st_size and os.pread(fd, 1, info.st_size - 1) != b"\n":
                    raise WalFramingError(
                        "WAL tail is not newline-terminated; explicit repair required"
                    )
            except (OSError, WalFramingError) as exc:
                raise _append_error(
                    layout, total, written, "tail-gate", exc,
                ) from exc

            while written < total:
                try:
                    count = os.write(fd, encoded[written:])
                except OSError as exc:
                    raise _append_error(
                        layout, total, written, "write", exc,
                    ) from exc
                if count <= 0:
                    exc = OSError(errno.EIO, "os.write made no progress")
                    raise _append_error(
                        layout, total, written, "write", exc,
                    ) from exc
                written += count
            try:
                os.fsync(fd)
            except OSError as exc:
                raise _append_error(
                    layout, total, written, "fsync", exc,
                ) from exc

            # WAL の flock を保持したまま、毎 append で runs dir まで耐久化する。
            try:
                dfd = os.open(
                    layout.runs_dir,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC,
                )
            except OSError as exc:
                raise _append_error(
                    layout, total, written, "fsync", exc,
                ) from exc
            try:
                try:
                    os.fsync(dfd)
                except OSError as exc:
                    raise _append_error(
                        layout, total, written, "fsync", exc,
                    ) from exc
            except BaseException:
                try:
                    os.close(dfd)
                except OSError:
                    pass
                raise
            try:
                os.close(dfd)
            except OSError as exc:
                raise _append_error(
                    layout, total, written, "close", exc,
                ) from exc
        except BaseException:
            # 既存の write/fsync 失敗を close 失敗で覆い隠さない。
            try:
                os.close(fd)
            except OSError:
                pass
            raise
        try:
            os.close(fd)
        except OSError as exc:
            raise _append_error(
                layout, total, written, "close", exc,
            ) from exc
    except BaseException:
        raise


def _digest_range(fd: int, start: int, size: int) -> tuple[str, bytes]:
    digest = hashlib.sha256()
    preview = bytearray()
    offset = start
    remaining = size
    while remaining:
        chunk = os.pread(fd, min(65536, remaining), offset)
        if not chunk:
            raise OSError(errno.EIO, "unexpected EOF while scanning WAL")
        digest.update(chunk)
        if len(preview) < 128:
            preview.extend(chunk[:128 - len(preview)])
        offset += len(chunk)
        remaining -= len(chunk)
    return digest.hexdigest(), bytes(preview)


def _last_frame_boundary(fd: int, size: int) -> int:
    offset = size
    while offset:
        start = max(0, offset - 65536)
        chunk = os.pread(fd, offset - start, start)
        if len(chunk) != offset - start:
            raise OSError(errno.EIO, "short pread while scanning WAL")
        newline = chunk.rfind(b"\n")
        if newline >= 0:
            return start + newline + 1
        offset = start
    return 0


def _write_receipt(layout: CampaignLayout, receipt: dict) -> str:
    body = (json.dumps(
        receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ) + "\n").encode("utf-8")
    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL
             | os.O_NOFOLLOW | os.O_CLOEXEC)
    for attempt in range(100):
        name = "wal-tail-repair-%d-%d-%d.json" % (
            time.time_ns(), os.getpid(), attempt,
        )
        path = os.path.join(layout.runs_dir, name)
        try:
            fd = os.open(path, flags, 0o600)
            break
        except FileExistsError:
            continue
    else:
        raise OSError(errno.EEXIST, "could not allocate WAL repair receipt")
    try:
        offset = 0
        while offset < len(body):
            count = os.write(fd, body[offset:])
            if count <= 0:
                raise OSError(errno.EIO, "receipt write made no progress")
            offset += count
        os.fsync(fd)
    finally:
        os.close(fd)
    dfd = os.open(
        layout.runs_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC,
    )
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)
    return path


def repair_truncated_tail(layout: CampaignLayout) -> WalTailRepairResult:
    """newline 終端後の tail だけを証拠 receipt 作成後に切り戻す。"""
    flags = os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(layout.wal_file, flags)
    except FileNotFoundError:
        return WalTailRepairResult(
            "missing", 0, 0, 0, None, "", None,
        )
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(errno.EINVAL, "WAL is not a regular file")
        original_size = info.st_size
        if (original_size == 0
                or os.pread(fd, 1, original_size - 1) == b"\n"):
            return WalTailRepairResult(
                "noop", original_size, original_size, 0, None, "", None,
            )

        final_size = _last_frame_boundary(fd, original_size)
        removed_bytes = original_size - final_size
        removed_sha256, removed_preview = _digest_range(
            fd, final_size, removed_bytes,
        )
        # binary tail を損失なく、256 byte 相当以下の ASCII で示す。
        preview = removed_preview.hex()
        receipt = {
            "kind": "wal-tail-repair",
            "wal_path": os.fspath(layout.wal_file),
            "cut_offset": final_size,
            "original_size": original_size,
            "final_size": final_size,
            "removed_bytes": removed_bytes,
            "removed_sha256": removed_sha256,
            "preview": preview,
        }
        receipt_path = _write_receipt(layout, receipt)
        os.ftruncate(fd, final_size)
        os.fsync(fd)
        return WalTailRepairResult(
            "repaired", original_size, final_size, removed_bytes,
            removed_sha256, preview, receipt_path,
        )
    finally:
        os.close(fd)


def log(layout: CampaignLayout, variant: str, stage: str, env_tag: str,
        payload: Optional[Dict] = None, ts: Optional[float] = None) -> WalRecord:
    """WalRecord を組んで追記する糖衣。ts 省略時は現在時刻。"""
    rec = WalRecord(variant=variant, stage=stage, env_tag=env_tag,
                    ts=ts if ts is not None else time.time(),
                    payload={} if payload is None else payload)
    append(layout, rec)
    return rec


# ---- リプレイ / リカバリ (D, A) ----

def read_records_collected(
        layout: CampaignLayout,
) -> tuple[list[WalRecord], list[tuple[int, str]], bool]:
    """WAL の有効行と行単位 issue、末尾切断の有無を返す。

    ``line_issues`` は ``(物理行番号, 理由)``。終端済みの不正行を除外して
    後続の有効 record も集める。内容によらず newline 無終端の最終 frame だけを
    crash prefix として ``truncated_tail`` へ分離する。
    """
    if not os.path.exists(layout.wal_file):
        return [], [], False
    records: list[WalRecord] = []
    line_issues: list[tuple[int, str]] = []
    truncated_tail = False
    for line_number, frame, _is_last, terminated in _iter_binary_frames(
            layout.wal_file):
        if not terminated:
            truncated_tail = True
            break
        try:
            line = frame.decode("utf-8")
            records.append(_line_to_record(line))
        except (UnicodeDecodeError, json.JSONDecodeError, WalLineError) as exc:
            line_issues.append((
                line_number, f"{type(exc).__name__}: {exc}",
            ))
    return records, line_issues, truncated_tail


def read_records_checked(layout: CampaignLayout) -> tuple[list[WalRecord], bool]:
    """WAL を読み、``(records, truncated_tail)`` を返す。

    内容によらず newline 無終端の最終 frame だけを crash prefix として許容する。
    終端済み frame の decode / JSON / record 契約違反は最終行でも伝播する。
    """
    if not os.path.exists(layout.wal_file):
        return [], False
    out: list[WalRecord] = []
    truncated_tail = False
    for _line_number, frame, _is_last, terminated in _iter_binary_frames(
            layout.wal_file):
        if not terminated:
            truncated_tail = True
            break
        line = frame.decode("utf-8")
        out.append(_line_to_record(line))
    return out, truncated_tail


def read_records(layout: CampaignLayout) -> List[WalRecord]:
    """WAL を全レコード読む。最終行の crash prefix は従来どおり捨てる。"""
    records, _ = read_records_checked(layout)
    return records


def _lock_declares_admission_policy(layout: CampaignLayout) -> bool:
    stored = read_lock(layout)
    if stored is None:
        return False
    try:
        value = json.loads(stored)
    except (json.JSONDecodeError, TypeError):
        return False
    search = value.get("search_config") if type(value) is dict else None
    return type(search) is dict and "build_admission" in search


def _lock_declares_trigger_grammar(layout: CampaignLayout) -> bool:
    stored = read_lock(layout)
    if stored is None:
        return False
    try:
        value = json.loads(stored)
    except (json.JSONDecodeError, TypeError):
        return False
    search = value.get("search_config") if type(value) is dict else None
    return (
        type(search) is dict
        and search.get("trigger_gate_language") == TRIGGER_GATE_LANGUAGE
    )


def _receipt_sha(payload: Dict, *, stage: str) -> str:
    value = payload.get("build_admission_receipt_sha256")
    if (type(value) is not str or len(value) != 64
            or any(ch not in "0123456789abcdef" for ch in value)):
        raise AttemptTopologyError(
            f"{stage}: build_admission_receipt_sha256 が exact lowercase SHA-256 でない"
        )
    return value


def _trigger_receipt_sha(payload: Dict, *, stage: str) -> str:
    value = payload.get("trigger_gate_receipt_sha256")
    if (type(value) is not str or len(value) != 64
            or any(ch not in "0123456789abcdef" for ch in value)):
        raise AttemptTopologyError(
            f"{stage}: trigger_gate_receipt_sha256 が exact lowercase SHA-256 でない"
        )
    return value


def _validate_attempt_topology(
        records: List[WalRecord], *, admission_policy: BuildAdmissionPolicy,
        trigger_grammar_locked: bool = False,
) -> Dict[str, Dict[str, BuildAttemptState]]:
    if type(admission_policy) is not BuildAdmissionPolicy:
        raise TypeError("admission_policy は BuildRunContext.policy の exact value が必要")
    by_variant: Dict[str, Dict[str, BuildAttemptState]] = {}
    global_attempts: Dict[str, BuildAttemptState] = {}
    active: Dict[str, BuildAttemptState] = {}
    for record in records:
        payload = record.payload
        if record.stage == STAGE_BUILD_START:
            attempt_id = payload.get("build_attempt_id")
            if type(attempt_id) is not str or not attempt_id:
                raise AttemptTopologyError("build_start: build_attempt_id が欠落または不正")
            if attempt_id in global_attempts:
                raise AttemptTopologyError(
                    f"build_start: duplicate attempt id: {attempt_id}"
                )
            if record.variant in active:
                raise AttemptTopologyError(
                    f"build_start: variant に未終端 attempt がある: "
                    f"active={active[record.variant].attempt_id} next={attempt_id}"
                )
            receipt = payload.get("build_admission")
            receipt_sha = None
            trigger_receipt_sha = None
            if receipt is not None:
                try:
                    checked = validate_build_admission_receipt(
                        receipt, expected_policy=admission_policy,
                    )
                except BuildAdmissionError as exc:
                    raise AttemptTopologyError(
                        f"build_start: admission receipt canonicality/policy 不一致: {exc}"
                    ) from exc
                receipt_sha = _receipt_sha(payload, stage=record.stage)
                if checked["receipt_sha256"] != receipt_sha:
                    raise AttemptTopologyError(
                        "build_start: receipt body と伝播 SHA が不一致"
                    )
                is_trigger = checked.get("schema") == ADMISSION_SCHEMA_V2
                if is_trigger:
                    if not trigger_grammar_locked:
                        raise AttemptTopologyError(
                            "build_start: trigger admission に grammar-bound campaign lock がない"
                        )
                    if payload.get("trigger_gate_language") != TRIGGER_GATE_LANGUAGE:
                        raise AttemptTopologyError(
                            "build_start: trigger gate language が lock と不一致"
                        )
                    trigger_body = payload.get("trigger_gate_receipt")
                    if trigger_body != checked.get("trigger_gate_receipt"):
                        raise AttemptTopologyError(
                            "build_start: admission 内と伝播 trigger receipt が不一致"
                        )
                    trigger_receipt_sha = _trigger_receipt_sha(
                        payload, stage=record.stage
                    )
                    if (type(trigger_body) is not dict
                            or trigger_body.get("receipt_sha256") != trigger_receipt_sha):
                        raise AttemptTopologyError(
                            "build_start: trigger receipt body と伝播 SHA が不一致"
                        )
                elif any(key in payload for key in (
                        "trigger_gate_language", "trigger_gate_receipt",
                        "trigger_gate_receipt_sha256")):
                    raise AttemptTopologyError(
                        "build_start: non-trigger admission に trigger receipt field がある"
                    )
            elif "build_admission_receipt_sha256" in payload:
                raise AttemptTopologyError(
                    "build_start: receipt 無し attempt に receipt SHA がある"
                )
            attempt = BuildAttemptState(
                attempt_id=attempt_id,
                variant=record.variant,
                receipt_sha256=receipt_sha,
                trigger_gate_receipt_sha256=trigger_receipt_sha,
                stages_seen=[record.stage],
            )
            global_attempts[attempt_id] = attempt
            by_variant.setdefault(record.variant, {})[attempt_id] = attempt
            active[record.variant] = attempt
            continue

        if record.stage in {STAGE_BUILD_DONE, STAGE_COMMIT}:
            attempt_id = payload.get("build_attempt_id")
            attempt = global_attempts.get(attempt_id) if type(attempt_id) is str else None
            if attempt is None or attempt.variant != record.variant:
                raise AttemptTopologyError(
                    f"{record.stage}: matching build_start attempt がない"
                )
            if active.get(record.variant) is not attempt:
                raise AttemptTopologyError(
                    f"{record.stage}: attempt は active でない: {attempt_id}"
                )
            if attempt.receipt_sha256 is None:
                raise AttemptTopologyError(
                    f"{record.stage}: receiptless pre-build attempt は terminal build stage を持てない"
                )
            if _receipt_sha(payload, stage=record.stage) != attempt.receipt_sha256:
                raise AttemptTopologyError(
                    f"{record.stage}: 別 attempt の receipt SHA が流用された"
                )
            if attempt.trigger_gate_receipt_sha256 is not None:
                if (_trigger_receipt_sha(payload, stage=record.stage)
                        != attempt.trigger_gate_receipt_sha256):
                    raise AttemptTopologyError(
                        f"{record.stage}: trigger receipt SHA が build_start と不一致"
                    )
            elif "trigger_gate_receipt_sha256" in payload:
                raise AttemptTopologyError(
                    f"{record.stage}: non-trigger attempt に trigger receipt SHA がある"
                )
            if record.stage == STAGE_BUILD_DONE:
                if attempt.build_done:
                    raise AttemptTopologyError("build_done: 同一 attempt で重複")
                attempt.build_done = True
            else:
                if not attempt.build_done:
                    raise AttemptTopologyError("commit: build_done より前または別 attempt")
                if attempt.committed:
                    raise AttemptTopologyError("commit: 同一 attempt で重複")
                attempt.committed = True
                active.pop(record.variant, None)
            attempt.stages_seen.append(record.stage)
            continue

        if record.stage == STAGE_ABORT:
            attempt_id = payload.get("build_attempt_id")
            attempt = global_attempts.get(attempt_id) if type(attempt_id) is str else None
            if (attempt is None or attempt.variant != record.variant
                    or active.get(record.variant) is not attempt):
                raise AttemptTopologyError("abort: matching active attempt がない")
            if attempt.receipt_sha256 is None:
                if "build_admission_receipt_sha256" in payload:
                    raise AttemptTopologyError("abort: receiptless attempt に receipt SHA がある")
                reason = payload.get("reason")
                if (
                    type(reason) is not str
                    or reason not in {member.value for member in ReceiptlessAbortReason}
                ):
                    raise AttemptTopologyError(
                        "abort: receiptless reason が closed issuer enum にない"
                    )
            elif _receipt_sha(payload, stage=record.stage) != attempt.receipt_sha256:
                raise AttemptTopologyError("abort: attempt receipt SHA が不一致")
            if attempt.trigger_gate_receipt_sha256 is not None:
                if (_trigger_receipt_sha(payload, stage=record.stage)
                        != attempt.trigger_gate_receipt_sha256):
                    raise AttemptTopologyError("abort: trigger receipt SHA が不一致")
            elif "trigger_gate_receipt_sha256" in payload:
                raise AttemptTopologyError(
                    "abort: non-trigger/receiptless attempt に trigger receipt SHA がある"
                )
            attempt.aborted = True
            attempt.stages_seen.append(record.stage)
            active.pop(record.variant, None)
    return by_variant


def replay(
        layout: CampaignLayout, *,
        admission_policy: Optional[BuildAdmissionPolicy] = None,
) -> Dict[str, EvalState]:
    """WAL をリプレイし、new-schema lock では attempt topology も検証する。"""
    records = read_records(layout)
    if admission_policy is None and _lock_declares_admission_policy(layout):
        raise AttemptTopologyError(
            "admission-aware campaign replay には current admission_policy が必要"
        )
    attempts = (
        _validate_attempt_topology(
            records,
            admission_policy=admission_policy,
            trigger_grammar_locked=_lock_declares_trigger_grammar(layout),
        )
        if admission_policy is not None else {}
    )
    states: Dict[str, EvalState] = {}
    for r in records:
        st = states.get(r.variant)
        if st is None:
            st = EvalState(variant=r.variant)
            states[r.variant] = st
        st.stages_seen.append(r.stage)
        st.env_tag = r.env_tag
        st.last = r
        if r.stage == STAGE_COMMIT:
            st.committed = True
            st.last_terminal = r
        elif r.stage == STAGE_ABORT:
            st.aborted = True
            st.last_terminal = r
    for variant, variant_attempts in attempts.items():
        states.setdefault(variant, EvalState(variant=variant)).attempts = variant_attempts
    return states


def records_by_stage(layout: CampaignLayout, variant: str) -> Dict[str, Dict]:
    """variant の stage→payload (最後勝ち)。判定は宣言でなく WAL レコードで行う。

    p3_kickoff.py / p3_s4_red.py / p3_s4_loop.py が各々独立に持っていた同一実装を
    統合 (D36 決定4-2)。**注意 (敵対レビュー 2026-07-09 で確認):** STAGE_VERIFY_DONE
    は S2 有効時 (evaluate() の extra_correctness、search_config['verify']=='legacy+s2')
    に variant ごと legacy→S2 の順で複数回書かれる。本関数は stage 単位の最後勝ちの
    ため、この場合は最後のパス (S2) の payload だけが残り、先行パスの verdict/commits/
    aborts は見えなくなる。全パスを見る・スケールを揃えて比較する必要がある consumer
    (例 critic.digest.load_verify_abort_signals) は wal.read_records() を直接使い、
    workload タグ (payload["workload"]["tag"]) で読み分けること。"""
    out: Dict[str, Dict] = {}
    for r in read_records(layout):
        if r.variant == variant:
            out[r.stage] = r.payload
    return out


def terminal_variants(states: Dict[str, EvalState]) -> set:
    """評価が終わっている (commit=採用 / abort=不採用) variant 集合 = スキップ対象。"""
    return {v for v, st in states.items() if st.terminal}


def resumable_variants(states: Dict[str, EvalState]) -> set:
    """未終端 = リカバリで破棄して再評価すべき variant (in-flight クラッシュ)。"""
    return {v for v, st in states.items() if st.resumable}


# ---- campaign.lock (同一性の正準 pre-image) ----

def write_lock(layout: CampaignLayout, preimage: str) -> None:
    os.makedirs(layout.root, exist_ok=True)
    # 初回のみ書く (既存があれば上書きしない = identity は不変)。
    if not os.path.exists(layout.lock_file):
        with open(layout.lock_file, "w", encoding="utf-8") as f:
            f.write(preimage)


def read_lock(layout: CampaignLayout) -> Optional[str]:
    if not os.path.exists(layout.lock_file):
        return None
    with open(layout.lock_file, "r", encoding="utf-8") as f:
        return f.read()


# ---- 原子的 one-shot lock / WAL 存在判定 (R6 resume 拒否の強化) ----

def acquire_lock_atomic(layout: CampaignLayout, preimage: str) -> bool:
    """`O_CREAT|O_EXCL` で campaign.lock を原子的に獲得する。既存なら False。

    write_lock (exists 確認後の非原子書き込み) の resume-safe 版。並行起動では一方だけが
    True を得る。WAL 空確認から最初の campaign-start append までを覆う排他区間の起点。
    True 時は preimage を書き込み、ファイル本体と親ディレクトリを fsync して存在を
    耐久化する (作成直後の crash でも lock が残る)。
    """
    os.makedirs(layout.root, exist_ok=True)
    try:
        fd = os.open(layout.lock_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        return False
    try:
        os.write(fd, preimage.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    dfd = os.open(layout.root, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)
    return True


def wal_bytes_present(layout: CampaignLayout) -> bool:
    """WAL ファイルに byte が存在するか (parse 可否は問わない)。

    read_records は末尾切れの 1 行を捨てるため、campaign-start 1 行だけの途中切断 WAL
    では [] を返しうる。resume 拒否は「parse 可能 record の有無」でなく「byte の存在」で
    判定する必要がある (truncated/汚染 WAL 迂回の閉鎖、fail-closed)。
    """
    try:
        path_info = os.lstat(layout.wal_file)
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(path_info.st_mode):
        raise OSError(
            errno.EINVAL, "WAL is a symlink or non-regular file",
            os.fspath(layout.wal_file),
        )
    try:
        fd = os.open(
            layout.wal_file,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
    except FileNotFoundError:
        # lstat 後に消えた場合は「byte 無し」と同じ。その他の OSError は伝播する。
        return False
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(
                errno.EINVAL, "WAL is not a regular file",
                os.fspath(layout.wal_file),
            )
        return info.st_size > 0
    finally:
        os.close(fd)
