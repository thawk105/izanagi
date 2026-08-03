# -*- coding: utf-8 -*-
"""Closed registry for Python CCBench materializers that bypass build admission.

Entries here are diagnostic or characterization-only.  Their binaries are not bound to a
``BuildAdmission`` receipt by ``buildcache`` and therefore must never be consumed as admitted
campaign material.  Producers expose ``admission_status=non-admissible`` so an
admission-aware downstream reader can reject them without inferring intent from filenames.

This registry deliberately does not close shell materializers under ``tools/pegasus/*.sh`` or
calibrator entry points that accept an arbitrary binary path.  Those surfaces remain outside
the bounded Python inventory ruled for this wave and receive no admission credit here.
"""
from __future__ import annotations

from types import MappingProxyType


NON_ADMISSIBLE = "non-admissible"

NON_ADMISSIBLE_MATERIALIZERS = MappingProxyType({
    "orchestrator.campaign.s2_verify_calibration._broken_build_and_verify":
        "negative-control build intentionally rejected by the normal buildcache allowlist",
    "orchestrator.campaign.s3_lock_coverage._build_broken":
        "trace-only lock-coverage mutation used to prove the verifier has teeth",
    "orchestrator.campaign.s5_permutation_coverage._build_broken":
        "trace-only permutation mutation used to prove the verifier has teeth",
    "orchestrator.campaign.t152_write_intent_coverage._build":
        "correctness-only write-intent mutation matrix; explicitly not integrated",
    "orchestrator.campaign.silo_ladder_rung1._build_variant":
        "ability-probe variant build whose results are ineligible for research selection",
    "orchestrator.campaign.silo_ladder_rung1._correctness_command":
        "ability-probe correctness build outside the campaign buildcache namespace",
})


def non_admissible_materializer(materializer: str) -> dict[str, str]:
    """Return the exact downstream-visible refusal classification for one registry entry."""

    try:
        reason = NON_ADMISSIBLE_MATERIALIZERS[materializer]
    except KeyError as exc:
        raise ValueError(f"unregistered non-admissible materializer: {materializer}") from exc
    return {
        "admission_status": NON_ADMISSIBLE,
        "materializer": materializer,
        "reason": reason,
    }
