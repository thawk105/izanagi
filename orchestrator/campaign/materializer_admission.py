# -*- coding: utf-8 -*-
"""Single typed registry for bounded Python build authority sites.

The registry closes two separate bounded inventories through typed projections: Python
materializers and coder-authority CLI entry points.  Registration is inventory metadata; it
does not by itself reject a build downstream, prove that quarantine ran, or make an artifact
non-certifying.  Coder entry-point registration is consumed only when its CLI authority flag is
actually specified.  Receipt/consumer binding remains outside this module.

Every materializer is either an admission-aware gateway or explicitly non-admissible.
Embedding a refusal in producer output is not uniform.  In particular,
``silo_ladder_rung1`` deliberately does not add one: doing so would change its committed
exact-key evidence schema, break the driver-SHA binding, and require re-pinning frozen
``output/`` artifacts.  Its refusal therefore remains a registry fact consumed by repository
closure checks, not a field claimed by that historical producer.

This registry deliberately does not close shell materializers under ``tools/pegasus/*.sh`` or
calibrator entry points that accept an arbitrary binary path.  Those surfaces remain outside
the bounded Python inventory ruled for this wave and receive no admission credit here.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType


NON_ADMISSIBLE = "non-admissible"
ADMITTED_GATEWAY = "admitted-gateway"


class MaterializerSiteKind(str, Enum):
    """Closed kinds represented by :data:`MATERIALIZER_ADMISSION_REGISTRY`."""

    DIRECT_MATERIALIZER = "direct-materializer"
    DELEGATING_MATERIALIZER = "delegating-materializer"
    CODER_ENTRYPOINT = "coder-entrypoint"


DIRECT_MATERIALIZER = MaterializerSiteKind.DIRECT_MATERIALIZER
DELEGATING_MATERIALIZER = MaterializerSiteKind.DELEGATING_MATERIALIZER
CODER_ENTRYPOINT = MaterializerSiteKind.CODER_ENTRYPOINT


@dataclass(frozen=True, slots=True)
class MaterializerRegistration:
    admission_status: str
    reason: str
    site_kind: MaterializerSiteKind = DIRECT_MATERIALIZER


MATERIALIZER_ADMISSION_REGISTRY = MappingProxyType({
    "orchestrator.campaign.b4_binary_record._install_dependency":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "gflags/glog installation only; produces no CCBench binary or performance evidence",
        ),
    "orchestrator.campaign.b10_backoff_shape_sweep._compile_probe_harnesses":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "standalone realized-wait probe harness; never enters a certified campaign",
        ),
    "orchestrator.campaign.paper_story_a1_paired._trace0_commands_match":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "exploratory trace validator only parses recorded build argv and never materializes",
        ),
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
    "orchestrator.campaign.s3_mocc_lock_coverage._build_variant":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "trace-only mocc lock/permutation controls used to prove the verifier has teeth",
        ),
    "orchestrator.campaign.s3_mocc_template_proof._build_variant":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "fixed-producer mocc template proof; never source performance values",
        ),
    "orchestrator.campaign.s3_mocc_mutation_proof._build_variant":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "trace-only mocc mutation proof controls; never source performance values",
        ),
    "orchestrator.campaign.s3_mocc_lock_coverage._install_dependency":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "static gflags/glog installation for the diagnostic mocc build produces no CCBench binary and cannot source performance values",
        ),
    "orchestrator.campaign.s5_permutation_coverage._build_broken":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "trace-only permutation mutation used to prove the verifier has teeth",
        ),
    "orchestrator.campaign.silo_policy_coverage._build_variant":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "Silo function-policy coverage, smoke, and fixed recon builds are diagnostic only",
        ),
    "orchestrator.campaign.vhash_cicada_vlife._build_variant":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "Cicada lifetime measurement builds are diagnostic only",
        ),
    "orchestrator.campaign.vhash_cicada_hot_block._build_one":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "exploratory Cicada VHash hot-block builds are ineligible for certified selection",
        ),
    "orchestrator.campaign.vhash_ro_gc_publish._build_variant":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "Cicada read-only GC publication builds are diagnostic only",
        ),
    "orchestrator.campaign.vhash_ceiling_vs_sota._build_variant":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "Cicada VHash ceiling comparison builds are exploratory only",
        ),
    "orchestrator.campaign.vhash_forwarding_prototype._build_variant":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "VHash forwarding smoke and measurement builds are diagnostic only and ineligible for certified selection",
        ),
    "orchestrator.campaign.vhash_interval_gc._build_variant":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "VHash interval GC smoke, measurement, and trace builds are diagnostic only and ineligible for certified selection",
        ),
    "orchestrator.campaign.s8a_trigger_coverage._build":
        MaterializerRegistration(
            ADMITTED_GATEWAY,
            "registered generator receipt is required at the buildcache gateway",
        ),
    "orchestrator.campaign.s8b_oracle_n_pilot.build_binaries":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "exploratory oracle n pilot builds are ineligible for certified selection",
            DELEGATING_MATERIALIZER,
        ),
    "orchestrator.campaign.s8b_expected_materialization.produce_expected_materialization_sha256":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "reference materialization only derives the expected tree digest and never "
            "builds or produces a certified binary",
        ),
    "orchestrator.campaign.t152_write_intent_coverage._build":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "correctness-only write-intent mutation matrix; explicitly not integrated",
        ),
    "orchestrator.campaign.t1998_stock_inline_pair._build_dir_from_build":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "only reads recorded build argv and never launches a build",
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
    "orchestrator.campaign.p3_kickoff.main":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "diagnostic kickoff remains runnable pending the ruled receipt-boundary decision",
            CODER_ENTRYPOINT,
        ),
    "orchestrator.campaign.p3_s4_red.main":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "diagnostic red path remains runnable pending the ruled receipt-boundary decision",
            CODER_ENTRYPOINT,
        ),
    "orchestrator.campaign.p3_s4_loop.main":
        MaterializerRegistration(
            ADMITTED_GATEWAY,
            "registered backoff exploration CLI coder-authority issuer",
            CODER_ENTRYPOINT,
        ),
    "orchestrator.campaign.p3_s4_loop_sort.main":
        MaterializerRegistration(
            ADMITTED_GATEWAY,
            "registered sort exploration CLI coder-authority issuer",
            CODER_ENTRYPOINT,
        ),
    "orchestrator.campaign.p3_s4_loop_policy.main":
        MaterializerRegistration(
            ADMITTED_GATEWAY,
            "registered Silo policy exploration CLI coder-authority issuer",
            CODER_ENTRYPOINT,
        ),
    "orchestrator.campaign.p3_s4_loop_lock_order.main":
        MaterializerRegistration(
            ADMITTED_GATEWAY,
            "registered Silo lock order exploration CLI coder-authority issuer",
            CODER_ENTRYPOINT,
        ),
    "orchestrator.campaign.p3_s4_loop_trigger_gating.main":
        MaterializerRegistration(
            ADMITTED_GATEWAY,
            "registered trigger-gating exploration CLI coder-authority issuer",
            CODER_ENTRYPOINT,
        ),
    "orchestrator.campaign.p3_autonomous_workload_trial.main":
        MaterializerRegistration(
            ADMITTED_GATEWAY,
            "registered autonomous workload trial CLI coder-authority issuer",
            CODER_ENTRYPOINT,
        ),
})

NON_ADMISSIBLE_MATERIALIZERS = MappingProxyType({
    materializer: registration.reason
    for materializer, registration in MATERIALIZER_ADMISSION_REGISTRY.items()
    if registration.site_kind in (DIRECT_MATERIALIZER, DELEGATING_MATERIALIZER)
    and registration.admission_status == NON_ADMISSIBLE
})


def _ast_site(materializer: str) -> str:
    module, function = materializer.rsplit(".", 1)
    return f"{module.replace('.', '/')}.py:{function}"


CLOSED_PYTHON_MATERIALIZER_SITES = frozenset(
    _ast_site(materializer)
    for materializer, registration in MATERIALIZER_ADMISSION_REGISTRY.items()
    if registration.site_kind is DIRECT_MATERIALIZER
)

CLOSED_CODER_ENTRYPOINT_SITES = frozenset(
    site
    for site, registration in MATERIALIZER_ADMISSION_REGISTRY.items()
    if registration.site_kind is CODER_ENTRYPOINT
)


def non_admissible_materializer(materializer: str) -> dict[str, str]:
    """Return the exact downstream-visible refusal classification for one registry entry."""

    try:
        registration = MATERIALIZER_ADMISSION_REGISTRY[materializer]
    except KeyError as exc:
        raise ValueError(f"unregistered non-admissible materializer: {materializer}") from exc
    if registration.site_kind not in (DIRECT_MATERIALIZER, DELEGATING_MATERIALIZER):
        raise ValueError(f"site is not a materializer: {materializer}")
    if registration.admission_status != NON_ADMISSIBLE:
        raise ValueError(f"materializer is an admitted gateway: {materializer}")
    return {
        "admission_status": NON_ADMISSIBLE,
        "materializer": materializer,
        "reason": registration.reason,
    }


def require_registered_coder_entrypoint(site: str) -> MaterializerRegistration:
    """Return one exact coder entry point or reject an unknown/non-coder site.

    This is an issuer-inventory check only.  A successful lookup neither observes a
    ``DiffQuarantineResult`` nor causes any downstream artifact rejection.
    """

    if type(site) is not str:
        raise ValueError("coder entry point site must be an exact str")
    try:
        registration = MATERIALIZER_ADMISSION_REGISTRY[site]
    except KeyError as exc:
        raise ValueError(f"unregistered coder entry point: {site}") from exc
    if registration.site_kind is not CODER_ENTRYPOINT:
        raise ValueError(f"registered site is not a coder entry point: {site}")
    return registration
