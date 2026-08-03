# -*- coding: utf-8 -*-
"""Single closed registry for direct Python CCBench materializers.

The registry itself closes the bounded Python inventory: every direct materializer is either
an admission-aware gateway or explicitly non-admissible.  Embedding a refusal in producer
output is not uniform.  In particular, ``silo_ladder_rung1`` deliberately does not add one:
doing so would change its committed exact-key evidence schema, break the driver-SHA binding,
and require re-pinning frozen ``output/`` artifacts.  Its refusal therefore remains a registry
fact consumed by repository closure checks, not a field claimed by that historical producer.

This registry deliberately does not close shell materializers under ``tools/pegasus/*.sh`` or
calibrator entry points that accept an arbitrary binary path.  Those surfaces remain outside
the bounded Python inventory ruled for this wave and receive no admission credit here.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


NON_ADMISSIBLE = "non-admissible"
ADMITTED_GATEWAY = "admitted-gateway"


@dataclass(frozen=True, slots=True)
class MaterializerRegistration:
    admission_status: str
    reason: str


MATERIALIZER_ADMISSION_REGISTRY = MappingProxyType({
    "orchestrator.campaign.s2_verify_calibration._broken_build_and_verify":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "negative-control build intentionally rejected by the normal buildcache allowlist",
        ),
    "orchestrator.campaign.s3_lock_coverage._build_broken":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "trace-only lock-coverage mutation used to prove the verifier has teeth",
        ),
    "orchestrator.campaign.s5_permutation_coverage._build_broken":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "trace-only permutation mutation used to prove the verifier has teeth",
        ),
    "orchestrator.campaign.s8a_trigger_coverage._build":
        MaterializerRegistration(
            ADMITTED_GATEWAY,
            "registered generator receipt is required at the buildcache gateway",
        ),
    "orchestrator.campaign.t152_write_intent_coverage._build":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "correctness-only write-intent mutation matrix; explicitly not integrated",
        ),
    "orchestrator.campaign.silo_ladder_rung1._build_variant":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "ability-probe variant build whose results are ineligible for research selection",
        ),
    "orchestrator.campaign.silo_ladder_rung1._correctness_command":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "ability-probe correctness build outside the campaign buildcache namespace",
        ),
})

NON_ADMISSIBLE_MATERIALIZERS = MappingProxyType({
    materializer: registration.reason
    for materializer, registration in MATERIALIZER_ADMISSION_REGISTRY.items()
    if registration.admission_status == NON_ADMISSIBLE
})


def _ast_site(materializer: str) -> str:
    module, function = materializer.rsplit(".", 1)
    return f"{module.replace('.', '/')}.py:{function}"


CLOSED_PYTHON_MATERIALIZER_SITES = frozenset(
    _ast_site(materializer) for materializer in MATERIALIZER_ADMISSION_REGISTRY
)


def non_admissible_materializer(materializer: str) -> dict[str, str]:
    """Return the exact downstream-visible refusal classification for one registry entry."""

    try:
        registration = MATERIALIZER_ADMISSION_REGISTRY[materializer]
    except KeyError as exc:
        raise ValueError(f"unregistered non-admissible materializer: {materializer}") from exc
    if registration.admission_status != NON_ADMISSIBLE:
        raise ValueError(f"materializer is an admitted gateway: {materializer}")
    return {
        "admission_status": NON_ADMISSIBLE,
        "materializer": materializer,
        "reason": registration.reason,
    }
