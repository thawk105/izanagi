# -*- coding: utf-8 -*-
"""Canonical IR and C++ predicate emitter for trigger-gated backoff."""
from __future__ import annotations

import sys
from dataclasses import dataclass

from .axis_trigger_gating import GATEABLE_REASONS

__all__ = [
    "SCHEMA_ID",
    "TriggerGateIR",
    "parse_wire",
    "encode_wire",
    "emit_predicate",
    "RefluxIRError",
]

SCHEMA_ID = "izanagi-trigger-gate-ir/v1"

# checkout 内の emitter と独立 golden の同時 regression 検出器である。
# artifact schema / origin identity ではなく、成果物へ搭載してはならない。
# production import は生成済み literal だけを読み、source/golden の再導出は test が担う。
_CHECKOUT_IR_EMITTER_SOURCE_SHA256 = (
    "e11cc8d996f306698f1c1096a6026574e5dbfee8d2c5613884dd426d18eec4ca"
)
_CHECKOUT_IR_GOLDEN_32_ROWS_SHA256 = (
    "69d8274fa03829d89dd706f7a0bb16d52ea71b608c51f5db5f5cdb1ead497165"
)
CHECKOUT_IR_EMITTER_GOLDEN_REGRESSION_ID = (
    "c8289c4faf1b5420d24cb8ef94e4d1e918bb4003afe4512bfc3a600baa095d75"
)

# CHECKOUT_IR_EMITTER_PREIMAGE_BEGIN
_REJECTION_MESSAGE = "invalid reflux IR"
_WIRE_WIDTH = 5
_MAX_MASK = (1 << _WIRE_WIDTH) - 1
_EXPECTED_REASONS = (
    "lock-conflict",
    "update-absent",
    "readvali-tid",
    "readvali-locked",
    "node-vali",
)
_ENUM_MEMBERS = (
    "kLockConflict",
    "kUpdateAbsent",
    "kReadValiTid",
    "kReadValiLocked",
    "kNodeVali",
)
_ASSIGNMENT_TARGET = "izanagi_gate_pass"
_REASON_VARIABLE = "izanagi_abort_reason_"
_ENUM_TYPE = "IzanagiAbortReason"
_SENTINEL_MEMBER = "kUnset"

if GATEABLE_REASONS != _EXPECTED_REASONS:
    raise RuntimeError("trigger-gating reason order drifted")


class RefluxIRError(Exception):
    """Uniform, disclosure-free rejection for the public IR API."""


def _reject() -> None:
    raise RefluxIRError(_REJECTION_MESSAGE) from None


def _validate_mask(mask: object) -> int:
    if type(mask) is not int or not 0 <= mask <= _MAX_MASK:
        _reject()
    return mask


class _TriggerGateIRMeta(type):
    """Recognize the same IR loaded through either supported package path."""

    def __instancecheck__(cls, instance: object) -> bool:
        if type.__instancecheck__(cls, instance):
            return True
        for module_name in (
            "campaign.reflux_ir",
            "orchestrator.campaign.reflux_ir",
        ):
            module = sys.modules.get(module_name)
            peer = getattr(module, "TriggerGateIR", None)
            if peer is not None and peer is not cls and type(instance) is peer:
                return True
        return False


@dataclass(frozen=True)
class TriggerGateIR(metaclass=_TriggerGateIRMeta):
    mask: int

    def __post_init__(self) -> None:
        _validate_mask(self.mask)


def _mask_from_ir(ir: object) -> int:
    if not isinstance(ir, TriggerGateIR):
        _reject()
    try:
        mask = ir.mask
    except Exception:  # Never disclose failures from an accepted subclass.
        pass
    else:
        return _validate_mask(mask)
    # Raise after leaving the handler so the rejection has no __context__.
    _reject()


def parse_wire(value: object) -> TriggerGateIR:
    """Parse the exact five-character LSB-first wire representation."""
    if (
        type(value) is not str
        or len(value) != _WIRE_WIDTH
        or any(character not in ("0", "1") for character in value)
    ):
        _reject()
    mask = sum((character == "1") << bit for bit, character in enumerate(value))
    return TriggerGateIR(mask=mask)


def encode_wire(ir: TriggerGateIR) -> str:
    """Encode an IR as the exact five-character LSB-first wire form."""
    mask = _mask_from_ir(ir)
    return "".join("1" if mask & (1 << bit) else "0" for bit in range(_WIRE_WIDTH))


def emit_predicate(ir: TriggerGateIR) -> str:
    """Emit the canonical single-line C++ gate assignment."""
    mask = _mask_from_ir(ir)
    members = [_SENTINEL_MEMBER]
    members.extend(
        member for bit, member in enumerate(_ENUM_MEMBERS) if mask & (1 << bit)
    )
    terms = [
        f"{_REASON_VARIABLE} == {_ENUM_TYPE}::{member}" for member in members
    ]
    return f"{_ASSIGNMENT_TARGET} = {' || '.join(terms)};"
# CHECKOUT_IR_EMITTER_PREIMAGE_END
