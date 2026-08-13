"""Decimal 秒を launcher の nanosecond domain へ安全に写像する。"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal, InvalidOperation, Overflow, localcontext


NANOSECONDS_PER_SECOND = 1_000_000_000
_MAX_SAFE_NANOSECONDS = Decimal.from_float(sys.float_info.max)
_SAFE_NANOSECOND_ERROR = (
    "正の有限数で nanosecond へ安全に変換できる値を指定すること"
)


def decimal_seconds_to_nanoseconds(value: Decimal) -> int:
    """launcher の deadline 計算と同じ変換を行い、0 ns と overflow を拒む。"""
    try:
        with localcontext() as context:
            context.prec = max(
                context.prec, len(value.as_tuple().digits) + 10
            )
            exact_nanoseconds = value * Decimal(NANOSECONDS_PER_SECOND)
    except (InvalidOperation, Overflow) as exc:
        raise ValueError(_SAFE_NANOSECOND_ERROR) from exc
    if (
        not exact_nanoseconds.is_finite()
        or exact_nanoseconds < 1
        or exact_nanoseconds > _MAX_SAFE_NANOSECONDS
    ):
        raise ValueError(_SAFE_NANOSECOND_ERROR)
    try:
        return int(exact_nanoseconds)
    except (OverflowError, ValueError) as exc:
        raise ValueError(_SAFE_NANOSECOND_ERROR) from exc


def positive_safe_nanosecond_decimal(text: str) -> Decimal:
    """argparse type: 正の有限 Decimal かつ deadline へ安全に変換可能。"""
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(_SAFE_NANOSECOND_ERROR) from exc
    if not value.is_finite() or value <= 0:
        raise argparse.ArgumentTypeError(_SAFE_NANOSECOND_ERROR)
    try:
        decimal_seconds_to_nanoseconds(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(_SAFE_NANOSECOND_ERROR) from exc
    return value
