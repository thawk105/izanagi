# -*- coding: utf-8 -*-
"""Build provenance admission shared by every campaign build entry point.

This value is a caller declaration, not a capability derived from source bytes, a clean-tree
proof, or generator identity.  It is not yet bound into cache/replay preimages or historical
receipt verification either.  A plain in-process ``True`` is not operator authority: the current
trust boundary is the orchestrator code that constructs the value from its CLI.  Those unclosed
layers deliberately receive no security credit here.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BuildAdmissionError(RuntimeError):
    """The caller did not present an admitted, explicitly classified build."""


class BuildProvenance(str, Enum):
    """Closed labels callers may assign to source bytes presented to a build."""

    STOCK_OR_PINNED = "STOCK_OR_PINNED"
    MACHINE_SWEEP = "MACHINE_SWEEP"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"
    CODER_DERIVED = "CODER_DERIVED"


def _validate(provenance: object, coder_derived_opt_in: object) -> None:
    if type(provenance) is not BuildProvenance:
        raise BuildAdmissionError("provenance_class は BuildProvenance の exact member が必要")
    if type(coder_derived_opt_in) is not bool:
        raise BuildAdmissionError("coder_derived_opt_in は CLI 由来の exact bool が必要")
    if provenance is BuildProvenance.CODER_DERIVED:
        if not coder_derived_opt_in:
            raise BuildAdmissionError(
                "CODER_DERIVED build は driver CLI の明示 opt-in が必要"
            )
    elif coder_derived_opt_in:
        raise BuildAdmissionError(
            "coder_derived_opt_in は CODER_DERIVED build にだけ指定できる"
        )


@dataclass(frozen=True, slots=True)
class BuildAdmission:
    """Immutable caller declaration and its minimal ``build_start`` WAL receipt.

    Construction does not inspect source bytes and therefore cannot prove the declared class.
    """

    provenance_class: BuildProvenance
    coder_derived_opt_in: bool = False

    def __post_init__(self) -> None:
        _validate(self.provenance_class, self.coder_derived_opt_in)

    def as_wal_receipt(self) -> dict[str, object]:
        return {
            "provenance_class": self.provenance_class.value,
            "coder_derived_opt_in": self.coder_derived_opt_in,
        }


def require_build_admission(value: object) -> BuildAdmission:
    """Revalidate an exact admission before identity/preprocess/build work."""

    if type(value) is not BuildAdmission:
        raise BuildAdmissionError("admission は immutable BuildAdmission の exact value が必要")
    _validate(value.provenance_class, value.coder_derived_opt_in)
    return value
