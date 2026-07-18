# -*- coding: utf-8 -*-
"""scheduler reservation の束縛と monotonic walltime 検査 leaf。"""
from __future__ import annotations

import math
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from .env_contract import IsolationPolicy


_HEX64_RE = re.compile(r"[0-9a-f]{64}")


class ReservationError(ValueError):
    """reservation binding の型・値・時刻関係が不正。"""


def _text(value: object, field: str) -> None:
    if type(value) is not str or not value:
        raise ReservationError(f"{field} は非空 str でなければならない")


@dataclass(frozen=True)
class ReservationBinding:
    """job reservation と walltime deadline を束縛する immutable record。"""

    job_id: str
    requested_s: int
    scheduler_started_epoch: float
    deadline_epoch: float
    host: str
    boot_id: str
    script_sha256: str
    nonce: str

    def __post_init__(self) -> None:
        _text(self.job_id, "job_id")
        if type(self.requested_s) is not int or self.requested_s <= 0:
            raise ReservationError("requested_s は正整数でなければならない")
        for field, value in (
            ("scheduler_started_epoch", self.scheduler_started_epoch),
            ("deadline_epoch", self.deadline_epoch),
        ):
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ReservationError(f"{field} は正の有限 epoch でなければならない")
        if self.deadline_epoch != self.scheduler_started_epoch + self.requested_s:
            raise ReservationError("deadline_epoch が scheduler_started_epoch + requested_s と不一致")
        _text(self.host, "host")
        _text(self.boot_id, "boot_id")
        if type(self.script_sha256) is not str or _HEX64_RE.fullmatch(self.script_sha256) is None:
            raise ReservationError("script_sha256 は 64 桁の小文字 hex でなければならない")
        _text(self.nonce, "nonce")


@dataclass(frozen=True)
class ReservationCheck:
    """検査時に wall clock の deadline を monotonic 座標へ写した結果。

    初回検査後の時刻判定は :meth:`recheck` だけを使う。wall clock を再読しないため、
    NTP 補正等で realtime が後退しても予約時間が延びることはない。
    """

    binding: ReservationBinding
    required_s: int
    safety_margin_s: int
    checked_realtime: float
    checked_monotonic: float
    monotonic_deadline: float
    remaining_s: float

    def recheck(
        self,
        *,
        required_s: int | None = None,
        safety_margin_s: int | None = None,
        monotonic_now_fn: Callable[[], float] = time.monotonic,
    ) -> "ReservationCheck":
        """現在の残時間を monotonic deadline のみから再検査する。

        driver が validated schedule の残量を更新した場合は、新しい正の ``required_s``
        と非負の margin を渡せる。省略時は直前の検査値を保つ。
        """
        required = self.required_s if required_s is None else _validate_duration(
            required_s, "required_s", allow_zero=False
        )
        margin = self.safety_margin_s if safety_margin_s is None else _validate_duration(
            safety_margin_s, "safety_margin_s", allow_zero=True
        )
        now = _call_clock(monotonic_now_fn, "monotonic_now")
        remaining = self.monotonic_deadline - now
        _require_capacity(required, margin, remaining)
        return ReservationCheck(
            binding=self.binding,
            required_s=required,
            safety_margin_s=margin,
            checked_realtime=self.checked_realtime,
            checked_monotonic=now,
            monotonic_deadline=self.monotonic_deadline,
            remaining_s=remaining,
        )

    def ensure_remaining(
        self,
        *,
        required_s: int,
        safety_margin_s: int,
        monotonic_now_fn: Callable[[], float] = time.monotonic,
    ) -> "ReservationCheck":
        """明示した次操作の所要時間を monotonic 基準で検査する alias。"""
        return self.recheck(
            required_s=required_s,
            safety_margin_s=safety_margin_s,
            monotonic_now_fn=monotonic_now_fn,
        )


_ENV_FIELDS = {
    "job_id": "IZANAGI_RESERVATION_JOB_ID",
    "requested_s": "IZANAGI_RESERVATION_REQUESTED_S",
    "scheduler_started_epoch": "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH",
    "deadline_epoch": "IZANAGI_RESERVATION_DEADLINE_EPOCH",
    "host": "IZANAGI_RESERVATION_HOST",
    "boot_id": "IZANAGI_RESERVATION_BOOT_ID",
    "script_sha256": "IZANAGI_RESERVATION_SCRIPT_SHA256",
    "nonce": "IZANAGI_RESERVATION_NONCE",
}


def _env_text(environ: Mapping, key: str) -> str:
    try:
        value = environ[key]
    except (KeyError, TypeError) as exc:
        raise ReservationError(f"必須環境変数 {key} がない") from exc
    if type(value) is not str or not value.strip():
        raise ReservationError(f"環境変数 {key} は非空 str でなければならない")
    return value.strip()


def _parse_int(raw: str, key: str) -> int:
    try:
        return int(raw, 10)
    except ValueError as exc:
        raise ReservationError(f"環境変数 {key} は 10 進整数でなければならない") from exc


def _parse_float(raw: str, key: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise ReservationError(f"環境変数 {key} は数値でなければならない") from exc
    if not math.isfinite(value):
        raise ReservationError(f"環境変数 {key} は有限値でなければならない")
    return value


def read_binding(environ: Mapping) -> ReservationBinding:
    """``IZANAGI_RESERVATION_*`` を strict に読み、binding を構築する。"""
    if not isinstance(environ, Mapping):
        raise ReservationError("environ は Mapping でなければならない")
    raw = {field: _env_text(environ, key) for field, key in _ENV_FIELDS.items()}
    return ReservationBinding(
        job_id=raw["job_id"],
        requested_s=_parse_int(raw["requested_s"], _ENV_FIELDS["requested_s"]),
        scheduler_started_epoch=_parse_float(
            raw["scheduler_started_epoch"], _ENV_FIELDS["scheduler_started_epoch"]
        ),
        deadline_epoch=_parse_float(raw["deadline_epoch"], _ENV_FIELDS["deadline_epoch"]),
        host=raw["host"],
        boot_id=raw["boot_id"],
        script_sha256=raw["script_sha256"],
        nonce=raw["nonce"],
    )


def _read_boot_id() -> str:
    try:
        with open("/proc/sys/kernel/random/boot_id", "r", encoding="ascii") as stream:
            value = stream.read()
    except OSError as exc:
        raise ReservationError("boot_id を読み取れない") from exc
    value = value.strip()
    if not value:
        raise ReservationError("boot_id が空")
    return value


def _call_clock(fn: Callable[[], float], name: str) -> float:
    if not callable(fn):
        raise ReservationError(f"{name} は callable でなければならない")
    try:
        value = fn()
    except Exception as exc:
        raise ReservationError(f"{name} の取得に失敗") from exc
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ReservationError(f"{name} は有限数でなければならない")
    return float(value)


def _validate_duration(value: object, name: str, *, allow_zero: bool) -> int:
    lower = 0 if allow_zero else 1
    if type(value) is not int or value < lower:
        condition = "非負整数" if allow_zero else "正整数"
        raise ReservationError(f"{name} は {condition} でなければならない")
    return value


def _require_capacity(required_s: int, safety_margin_s: int, remaining_s: float) -> None:
    if required_s + safety_margin_s > remaining_s:
        raise ReservationError(
            "reservation の残時間が不足: "
            f"required={required_s}, margin={safety_margin_s}, remaining={remaining_s}"
        )


def check_reservation(
    binding: ReservationBinding,
    *,
    required_s: int,
    safety_margin_s: int,
    environ: Mapping,
    realtime_now_fn: Callable[[], float] = time.time,
    monotonic_now_fn: Callable[[], float] = time.monotonic,
    boot_id_read_fn: Callable[[], str] = _read_boot_id,
) -> ReservationCheck:
    """job/boot/time を照合し、以後に使う monotonic deadline を返す。"""
    if not isinstance(binding, ReservationBinding):
        raise ReservationError("binding は ReservationBinding でなければならない")
    required_s = _validate_duration(required_s, "required_s", allow_zero=False)
    safety_margin_s = _validate_duration(
        safety_margin_s, "safety_margin_s", allow_zero=True
    )
    if not isinstance(environ, Mapping):
        raise ReservationError("environ は Mapping でなければならない")
    current_job_id = _env_text(environ, "PBS_JOBID")
    if current_job_id != binding.job_id:
        raise ReservationError("現在の PBS_JOBID が reservation binding と不一致")
    if not callable(boot_id_read_fn):
        raise ReservationError("boot_id_read_fn は callable でなければならない")
    try:
        current_boot_id = boot_id_read_fn()
    except ReservationError:
        raise
    except Exception as exc:
        raise ReservationError("boot_id の取得に失敗") from exc
    if type(current_boot_id) is not str or not current_boot_id.strip():
        raise ReservationError("現在の boot_id は非空 str でなければならない")
    if current_boot_id.strip() != binding.boot_id:
        raise ReservationError("現在の boot_id が reservation binding と不一致")

    realtime_now = _call_clock(realtime_now_fn, "realtime_now")
    if binding.scheduler_started_epoch > realtime_now:
        raise ReservationError("scheduler_started_epoch が現在より未来")
    remaining = binding.deadline_epoch - realtime_now
    _require_capacity(required_s, safety_margin_s, remaining)
    monotonic_now = _call_clock(monotonic_now_fn, "monotonic_now")
    monotonic_deadline = monotonic_now + remaining
    if not math.isfinite(monotonic_deadline):
        raise ReservationError("monotonic deadline を有限値として導出できない")
    return ReservationCheck(
        binding=binding,
        required_s=required_s,
        safety_margin_s=safety_margin_s,
        checked_realtime=realtime_now,
        checked_monotonic=monotonic_now,
        monotonic_deadline=monotonic_deadline,
        remaining_s=remaining,
    )


def is_reservation_required(isolation_policy: IsolationPolicy) -> bool:
    """型付けされた isolation policy の ``single_process`` から導出する。"""
    if not isinstance(isolation_policy, IsolationPolicy):
        raise ReservationError("isolation_policy は IsolationPolicy でなければならない")
    return isolation_policy.single_process
