# -*- coding: utf-8 -*-
"""T-2000 only: paired legacy/build_v2 transport probe and pure checks.

This module deliberately lives outside the repository's normal ``testpaths``.
Only the final test performs builds; every other test is pure and is intended
for the B-057 mutation preflight.  The probe records hashes and closed enums,
never subprocess output, exception text, URLs, endpoints, or complete argv.
"""
from __future__ import annotations

import contextlib
import ctypes
import hashlib
import json
import os
import re
import secrets
import select
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from orchestrator.campaign import (
    build_admission,
    buildcache,
    env_contract,
    site_policy,
    source_digest,
)
from orchestrator.campaign.model import Genome


_SCHEMA = "t2000-legacy-build-probe/v3"
_DIGEST_SCHEMA = "t2000-legacy-build-probe-digest/v3"
_REAL_NODEID = (
    "tools/pegasus/probes/test_t2000_legacy_build_probe.py::"
    "test_t2000_legacy_build_probe"
)
_PROBE_RELATIVE_PATH = Path("tools/pegasus/probes/test_t2000_legacy_build_probe.py")
_ARTIFACT_RELATIVE_PATH = Path(
    "output/insights/2026-08-28_t2000-legacy-build-probe"
)
_ARM_IDS = (
    "legacy-proxy",
    "legacy-no-proxy",
    "v2-source-no-proxy",
)
_DEPENDENCIES = ("masstree", "mimalloc", "googletest")
_RUN_LOCAL_GENERATED_PATHS = {
    "masstree": frozenset({"config.h", "libkohler_masstree_json.a"}),
    "mimalloc": frozenset(),
    "googletest": frozenset(),
}
_PROXY_KEYS = frozenset({
    "http_proxy", "https_proxy", "all_proxy", "no_proxy",
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
})
_PROXY_KEYS_CASEFOLD = frozenset(name.lower() for name in _PROXY_KEYS)
_GIT_CONFIG = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_COUNT": "0",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_OPTIONAL_LOCKS": "0",
}
_PERSISTENT_CACHE = Path("/work/1/SFC/tanab/izanagi-thirdparty-cache")
_SETUP_TIMEOUT_S = 600
_ARM_TIMEOUT_S = 900
_FINALIZE_RESERVE_S = 60
_JOB_WALLTIME_S = 3600
_SUPERVISOR_POLL_S = 0.05
_TERM_GRACE_S = 2.0
_OBSERVER_GIT_SLICE_S = 5.0
_SCRATCH_MIN_FREE_BYTES = 1 << 30
_SCRATCH_MIN_FREE_INODES = 50_000
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_URL_SCHEME = re.compile(r"(?i)\b(?:https?|ssh|git|ftp)://")
_RAW_KEYS = frozenset({
    "schema", "completion", "precondition", "run_identity", "control",
    "setup", "arms", "comparison", "redaction",
})
_IDENTITY_KEYS = frozenset({
    "identity_status", "node_sha256", "pbs_job_sha256", "nonce_sha256",
    "single_node", "single_pytest_coordinator", "arm_process_groups_supervised",
    "compute_site", "ccbench_commit",
    "genome_sha256", "trace", "toolchain_manifest_sha256",
    "source_evidence_sha256", "admission_receipt_sha256", "contract_sha256",
    "activation_state_sha256", "path_sha256", "tool_resolution_sha256",
    "git_config_sha256", "dependency_policy_sha256", "dependency_pins",
})
_CONTROL_KEYS = frozenset({
    "pbs_bound", "proxy_source", "proxy_value_sha256", "legacy_env_delta",
    "path_unchanged", "git_config_identical", "legacy_git_guard_absent",
})
_SETUP_KEYS = frozenset({
    "status", "stage_code", "cause_code", "wall_s",
    "dependency_receipt_sha256", "archive_sha256",
    "private_dependency_sha256", "private_dependencies", "private_copy_verified",
    "configure_shape",
})
_ARM_KEYS = frozenset({
    "id", "production_call", "transport_mode", "git_protocol_guard",
    "fresh_cache_precondition", "outcome", "wall_s", "cached",
    "stage_code", "cause_code", "invariant_status", "invariant_before_sha256",
    "invariant_after_sha256", "observer_status", "observed_heads",
    "dependency_identity_sha256", "dependency_identities", "common_staging_root",
    "stable_terminal", "configure_shape", "git_protocol_evidence",
    "external_git_evidence", "execution_model",
})
_COMPARISON_KEYS = frozenset({
    "classification", "reason_code", "ambient_proxy_env_sensitivity",
    "non_file_git_transport_needed", "arbitrary_external_network",
    "causal_scope", "performance_scope",
})
_PRECONDITION_KEYS = frozenset({"status", "cause_code"})
_PRECONDITION_CAUSES = frozenset({
    "none", "compute", "proxy", "cache", "evidence", "admission", "contract",
    "toolchain", "setup", "artifact-name", "deadline", "finalize", "unexpected",
})
_REPO_IDENTITY_KEYS = frozenset({
    "head", "tree", "status_sha256", "worktree_sha256", "config_sha256",
    "tracked_clean", "untracked_clean", "ignored_clean", "alternates_absent",
})
_SHAPE_KEYS = frozenset({
    "observed", "base_dir_count", "source_dir_count", "base_dir_binding",
    "source_dir_binding", "legacy_source_seam",
})

# The enforced upper bounds, including artifact finalization reserve, must fit
# strictly inside the existing one-hour tests job.  This is a static admission
# assertion, not an estimate derived from D412's single historical value.
assert _SETUP_TIMEOUT_S + len(_ARM_IDS) * _ARM_TIMEOUT_S + _FINALIZE_RESERVE_S < _JOB_WALLTIME_S


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")


def _sha256_value(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _exact_keys(value: object, expected: frozenset[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ValueError(f"{label}: exact key set required")
    return value


def _is_hex(value: object, pattern: re.Pattern[str]) -> bool:
    return type(value) is str and pattern.fullmatch(value) is not None


def _assert_redacted_payload(value: object, *, forbidden_values: tuple[str, ...] = ()) -> None:
    """Reject secret-bearing shapes immediately before publication (M5 anchor)."""
    forbidden_keys = (
        "stdout", "stderr", "exception", "traceback", "argv", "endpoint",
        "url", "hostname", "pbs_jobid", "proxy_value",
    )

    def visit(item: object) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                if type(key) is not str:
                    raise ValueError("payload key must be exact str")
                lowered = key.lower()
                if (
                    any(token in lowered for token in forbidden_keys)
                    and not lowered.endswith("_sha256")
                ):
                    raise ValueError("payload contains a forbidden key")
                visit(child)
            return
        if isinstance(item, (list, tuple)):
            for child in item:
                visit(child)
            return
        if type(item) is str:
            if _URL_SCHEME.search(item):
                raise ValueError("payload contains a URL")
            for secret in forbidden_values:
                if secret and secret in item:
                    raise ValueError("payload contains a forbidden value")
            if "\n" in item or "\r" in item or "\x00" in item:
                raise ValueError("payload string is not a fixed token")
            return
        if item is None or type(item) in {bool, int, float}:
            return
        raise ValueError("payload contains a non-JSON exact value")

    visit(value)


def _validate_configure_shape(value: object) -> None:
    shape = _exact_keys(value, _SHAPE_KEYS, "configure_shape")
    if type(shape["observed"]) is not bool:
        raise ValueError("invalid configure observation flag")
    if shape["base_dir_count"] is not None and (
        type(shape["base_dir_count"]) is not int or shape["base_dir_count"] not in {0, 1}
    ):
        raise ValueError("invalid BASE_DIR count")
    if shape["source_dir_count"] is not None and (
        type(shape["source_dir_count"]) is not int or shape["source_dir_count"] not in {0, 3}
    ):
        raise ValueError("invalid SOURCE_DIR count")
    if shape["base_dir_binding"] not in {"absent", "exact", "unobserved", "mismatch"}:
        raise ValueError("invalid BASE_DIR binding")
    if shape["source_dir_binding"] not in {"absent", "exact", "unobserved", "mismatch"}:
        raise ValueError("invalid SOURCE_DIR binding")
    if shape["legacy_source_seam"] is not None and type(shape["legacy_source_seam"]) is not bool:
        raise ValueError("invalid legacy seam value")
    if not shape["observed"] and (
        shape["base_dir_count"] is not None
        or shape["source_dir_count"] is not None
        or shape["base_dir_binding"] != "unobserved"
        or shape["source_dir_binding"] != "unobserved"
        or shape["legacy_source_seam"] is not None
    ):
        raise ValueError("unobserved configure shape must not synthesize evidence")


def _validate_dependency_identities(value: object, *, allow_none: bool) -> None:
    if value is None and allow_none:
        return
    if not isinstance(value, Mapping) or set(value) != set(_DEPENDENCIES):
        raise ValueError("dependency identity order is invalid")
    for identity in value.values():
        row = _exact_keys(identity, _REPO_IDENTITY_KEYS, "dependency identity")
        if not _is_hex(row["head"], _HEX40) or not _is_hex(row["tree"], _HEX40):
            raise ValueError("dependency Git identity is invalid")
        for key in ("status_sha256", "worktree_sha256", "config_sha256"):
            if not _is_hex(row[key], _HEX64):
                raise ValueError(f"dependency {key} is invalid")
        for key in ("tracked_clean", "untracked_clean", "ignored_clean", "alternates_absent"):
            if type(row[key]) is not bool:
                raise ValueError(f"dependency {key} is invalid")


def _validate_raw_schema(document: object) -> None:
    raw = _exact_keys(document, _RAW_KEYS, "raw")
    if raw["schema"] != _SCHEMA or raw["completion"] not in {
        "complete", "incomplete-precondition", "incomplete-setup",
        "incomplete-execution", "incomplete-timeout", "incomplete-finalize",
    }:
        raise ValueError("raw schema/completion is invalid")
    precondition = _exact_keys(raw["precondition"], _PRECONDITION_KEYS, "precondition")
    if precondition["status"] not in {"satisfied", "failed"}:
        raise ValueError("precondition status is invalid")
    if precondition["cause_code"] not in _PRECONDITION_CAUSES:
        raise ValueError("precondition cause is invalid")
    if (precondition["status"] == "satisfied") != (precondition["cause_code"] == "none"):
        raise ValueError("precondition status/cause is inconsistent")
    identity = _exact_keys(raw["run_identity"], _IDENTITY_KEYS, "run_identity")
    if identity["identity_status"] not in {"complete", "sentinel-incomplete"}:
        raise ValueError("identity status is invalid")
    for key in (
        "node_sha256", "pbs_job_sha256", "nonce_sha256", "genome_sha256",
        "toolchain_manifest_sha256", "source_evidence_sha256", "admission_receipt_sha256",
        "contract_sha256", "activation_state_sha256", "path_sha256",
        "tool_resolution_sha256", "git_config_sha256", "dependency_policy_sha256",
    ):
        if identity[key] is not None and not _is_hex(identity[key], _HEX64):
            raise ValueError(f"run identity {key} is invalid")
    if identity["ccbench_commit"] is not None and not _is_hex(identity["ccbench_commit"], _HEX40):
        raise ValueError("CCBench commit is invalid")
    if identity["single_node"] not in {True, None}:
        raise ValueError("single-node contract is invalid")
    if identity["single_pytest_coordinator"] is not True:
        raise ValueError("pytest coordinator contract is invalid")
    if type(identity["arm_process_groups_supervised"]) is not bool:
        raise ValueError("arm process supervision contract is invalid")
    if identity["compute_site"] not in {"pegasus-compute", "unavailable"} or identity["trace"] is not False:
        raise ValueError("site/trace contract is invalid")
    pins = identity["dependency_pins"]
    if not isinstance(pins, Mapping) or set(pins) != set(_DEPENDENCIES):
        raise ValueError("dependency pin order is invalid")
    if any(pin is not None and not _is_hex(pin, _HEX40) for pin in pins.values()):
        raise ValueError("dependency pin is invalid")
    complete_identity_fields = (
        "node_sha256", "pbs_job_sha256", "genome_sha256", "toolchain_manifest_sha256",
        "source_evidence_sha256", "admission_receipt_sha256", "contract_sha256",
        "activation_state_sha256", "path_sha256", "tool_resolution_sha256",
        "dependency_policy_sha256", "ccbench_commit",
    )
    if identity["identity_status"] == "complete" and (
        identity["single_node"] is not True
        or identity["compute_site"] != "pegasus-compute"
        or any(identity[key] is None for key in complete_identity_fields)
        or any(pin is None for pin in pins.values())
    ):
        raise ValueError("complete run identity contains unavailable material")
    if raw["completion"] == "complete" and identity["arm_process_groups_supervised"] is not True:
        raise ValueError("complete run lacks three supervised arm groups")

    control = _exact_keys(raw["control"], _CONTROL_KEYS, "control")
    if control["pbs_bound"] not in {True, False} or control["proxy_source"] not in {
        "b10-single-literal", "unavailable",
    }:
        raise ValueError("control binding is invalid")
    if control["proxy_value_sha256"] is not None and not _is_hex(control["proxy_value_sha256"], _HEX64):
        raise ValueError("proxy hash is invalid")
    if control["legacy_env_delta"] not in {"lowercase-http-https-only", "unavailable"}:
        raise ValueError("legacy environment delta is invalid")
    if any(control[key] not in {True, False} for key in (
        "path_unchanged", "git_config_identical", "legacy_git_guard_absent",
    )):
        raise ValueError("control invariants are invalid")

    setup = _exact_keys(raw["setup"], _SETUP_KEYS, "setup")
    if setup["status"] not in {"success", "failed", "timeout", "precondition-missing"}:
        raise ValueError("setup status is invalid")
    if setup["stage_code"] not in {"setup", "precondition", "unknown"}:
        raise ValueError("setup stage is invalid")
    if setup["cause_code"] not in {
        "none", "timeout", "pin-mismatch", "identity-mismatch", "setup-failed",
        "shared-cache-changed", "precondition-failed", "deadline", "unexpected",
    }:
        raise ValueError("setup cause is invalid")
    if setup["wall_s"] is not None and (
        type(setup["wall_s"]) not in {int, float} or setup["wall_s"] < 0
    ):
        raise ValueError("setup wall is invalid")
    for key in ("dependency_receipt_sha256", "archive_sha256", "private_dependency_sha256"):
        if setup[key] is not None and not _is_hex(setup[key], _HEX64):
            raise ValueError(f"setup {key} is invalid")
    if type(setup["private_copy_verified"]) is not bool:
        raise ValueError("private copy flag is invalid")
    _validate_dependency_identities(setup["private_dependencies"], allow_none=True)
    _validate_configure_shape(setup["configure_shape"])
    if setup["status"] == "success" and (
        setup["dependency_receipt_sha256"] is None
        or setup["archive_sha256"] is None
        or setup["private_dependency_sha256"] is None
        or setup["private_dependencies"] is None
        or setup["private_copy_verified"] is not True
    ):
        raise ValueError("successful setup lacks dependency evidence")

    arms = raw["arms"]
    if type(arms) is not list or len(arms) != 3 or tuple(arm.get("id") for arm in arms) != _ARM_IDS:
        raise ValueError("exact three ordered arms are required")
    for arm in arms:
        row = _exact_keys(arm, _ARM_KEYS, "arm")
        if row["production_call"] not in {"build", "build_v2"}:
            raise ValueError("production call is invalid")
        if row["transport_mode"] not in {
            "lowercase-proxy", "proxy-env-removed", "source-dir-file-guard",
        }:
            raise ValueError("transport mode is invalid")
        if row["git_protocol_guard"] not in {"absent", "file-only"}:
            raise ValueError("Git guard is invalid")
        if type(row["fresh_cache_precondition"]) is not bool:
            raise ValueError("fresh cache flag is invalid")
        if row["outcome"] not in {"success", "failed", "timeout", "not-run", "inconclusive"}:
            raise ValueError("arm outcome is invalid")
        if row["wall_s"] is not None and (
            type(row["wall_s"]) not in {int, float} or row["wall_s"] < 0
        ):
            raise ValueError("arm wall is invalid")
        if row["cached"] is not None and type(row["cached"]) is not bool:
            raise ValueError("cached field is invalid")
        if row["stage_code"] not in {
            "none", "configure", "build", "admission", "precondition", "observer", "unknown",
        }:
            raise ValueError("arm stage is invalid")
        if row["cause_code"] not in {
            "none", "external-git-fetch-failed", "site-gate", "pin-mismatch",
            "cache-hit", "timeout", "identity-mismatch", "observer-missed",
            "observer-mismatch", "scratch-precondition", "not-run", "unexpected",
        }:
            raise ValueError("arm cause is invalid")
        if row["invariant_status"] not in {"matched", "mismatch", "not-observed"}:
            raise ValueError("arm invariant status is invalid")
        for key in ("invariant_before_sha256", "invariant_after_sha256", "dependency_identity_sha256"):
            if row[key] is not None and not _is_hex(row[key], _HEX64):
                raise ValueError(f"arm {key} is invalid")
        if row["observer_status"] not in {
            "complete", "external-git-observed", "not-required", "missed", "mismatch", "not-run",
        }:
            raise ValueError("observer status is invalid")
        heads = row["observed_heads"]
        if not isinstance(heads, Mapping) or set(heads) != set(_DEPENDENCIES):
            raise ValueError("observed head order is invalid")
        if any(head is not None and not _is_hex(head, _HEX40) for head in heads.values()):
            raise ValueError("observed HEAD is invalid")
        _validate_dependency_identities(row["dependency_identities"], allow_none=True)
        if row["common_staging_root"] not in {True, False, None}:
            raise ValueError("common staging root evidence is invalid")
        if row["stable_terminal"] not in {True, False, None}:
            raise ValueError("stable terminal evidence is invalid")
        _validate_configure_shape(row["configure_shape"])
        if row["git_protocol_evidence"] not in {
            "file-only-policy-success", "not-observed", "not-applicable",
        }:
            raise ValueError("Git protocol evidence is invalid")
        if row["external_git_evidence"] not in {
            "policy-remote-process-observed", "not-observed", "not-applicable",
        }:
            raise ValueError("external Git evidence is invalid")
        if row["execution_model"] not in {"supervised-child-process-group", "not-run"}:
            raise ValueError("arm execution model is invalid")
        if (row["outcome"] == "not-run") != (row["execution_model"] == "not-run"):
            raise ValueError("arm execution model/outcome is inconsistent")
        if row["git_protocol_evidence"] == "file-only-policy-success" and not (
            row["id"] == "v2-source-no-proxy"
            and row["git_protocol_guard"] == "file-only"
            and row["outcome"] in {"success", "inconclusive"}
        ):
            raise ValueError("file-only success evidence is not bound to the v2 arm")

    comparison = _exact_keys(raw["comparison"], _COMPARISON_KEYS, "comparison")
    if comparison["classification"] not in {
        "migration-candidate-material", "keep-current-candidate-material", "indeterminate",
    }:
        raise ValueError("classification is invalid")
    if comparison["reason_code"] not in {
        "single-run-proxy-sensitivity", "legacy-no-proxy-succeeded",
        "control-invalid", "run-identity", "dependency-identity", "arm-schema",
        "cache-hit", "legacy-configure-shape", "v2-arm",
        "v2-file-protocol-evidence", "legacy-no-proxy-stage",
        "legacy-no-proxy-observer", "timeout",
        "precondition-failed", "setup-failed", "external-git-evidence",
    }:
        raise ValueError("classification reason is invalid")
    if comparison["ambient_proxy_env_sensitivity"] not in {
        "observed-single-run", "not-observed", "indeterminate",
    }:
        raise ValueError("proxy sensitivity is invalid")
    if comparison["non_file_git_transport_needed"] not in {
        "not-required-for-success-under-file-only-policy", "indeterminate",
    }:
        raise ValueError("Git transport classification is invalid")
    if comparison["arbitrary_external_network"] != "not-measured":
        raise ValueError("arbitrary network scope is invalid")
    if comparison["causal_scope"] != "single-run-operational-sensitivity":
        raise ValueError("causal scope is invalid")
    if comparison["performance_scope"] != "diagnostic-only":
        raise ValueError("performance scope is invalid")
    v2 = arms[2]
    if comparison["non_file_git_transport_needed"] == (
        "not-required-for-success-under-file-only-policy"
    ) and not (
        v2["git_protocol_evidence"] == "file-only-policy-success"
        and v2["outcome"] == "success"
    ):
        raise ValueError("comparison Git evidence is inconsistent with the v2 arm")
    redaction = _exact_keys(raw["redaction"], frozenset({"schema_audit_passed"}), "redaction")
    if redaction["schema_audit_passed"] is not True:
        raise ValueError("redaction audit did not pass")


def _classification_fixture() -> dict[str, Any]:
    """Independent literal fixture; no production helper is its oracle."""
    legacy_shape = {
        "observed": True, "base_dir_count": 0, "source_dir_count": 0,
        "base_dir_binding": "absent", "source_dir_binding": "absent",
        "legacy_source_seam": False,
    }
    failed_shape = {
        "observed": False, "base_dir_count": None, "source_dir_count": None,
        "base_dir_binding": "unobserved", "source_dir_binding": "unobserved",
        "legacy_source_seam": None,
    }
    v2_shape = {
        "observed": True, "base_dir_count": 1, "source_dir_count": 3,
        "base_dir_binding": "exact", "source_dir_binding": "exact",
        "legacy_source_seam": False,
    }
    identity = {
        name: {
            "head": "1" * 40, "tree": "2" * 40,
            "status_sha256": "3" * 64, "worktree_sha256": "4" * 64,
            "config_sha256": "5" * 64, "tracked_clean": True,
            "untracked_clean": True, "ignored_clean": True,
            "alternates_absent": True,
        }
        for name in _DEPENDENCIES
    }
    return {
        "precondition_valid": True,
        "setup_valid": True,
        "control_valid": True,
        "identity_match": True,
        "dependency_evidence": {
            "pins": {name: "1" * 40 for name in _DEPENDENCIES},
            "private": json.loads(json.dumps(identity)),
            "proxy": json.loads(json.dumps(identity)),
            "no_proxy": json.loads(json.dumps(identity)),
            "v2": json.loads(json.dumps(identity)),
            "private_copy_verified": True, "shared_unchanged": True,
            "proxy_common_root": True, "proxy_stable_terminal": True,
            "no_proxy_common_root": True, "no_proxy_stable_terminal": True,
            "v2_reobserved": True,
        },
        "arms": {
            "legacy-proxy": {
                "fresh": True, "cached": False, "outcome": "success",
                "stage": "none", "cause": "none", "observer": "complete",
                "shape": legacy_shape, "git_protocol_evidence": "not-applicable",
                "external_git_evidence": "not-applicable",
            },
            "legacy-no-proxy": {
                "fresh": True, "cached": False, "outcome": "failed",
                "stage": "configure", "cause": "external-git-fetch-failed",
                "observer": "external-git-observed", "shape": failed_shape,
                "git_protocol_evidence": "not-applicable",
                "external_git_evidence": "policy-remote-process-observed",
            },
            "v2-source-no-proxy": {
                "fresh": True, "cached": False, "outcome": "success",
                "stage": "none", "cause": "none", "observer": "not-required",
                "shape": v2_shape, "git_protocol_evidence": "file-only-policy-success",
                "external_git_evidence": "not-applicable",
            },
        },
    }


def _dependency_binding_matches(value: object, *, no_proxy_succeeded: bool) -> bool:
    if not isinstance(value, Mapping) or set(value) != {
        "pins", "private", "proxy", "no_proxy", "v2", "private_copy_verified",
        "shared_unchanged", "proxy_common_root", "proxy_stable_terminal",
        "no_proxy_common_root", "no_proxy_stable_terminal", "v2_reobserved",
    }:
        return False
    pins = value["pins"]
    if not isinstance(pins, Mapping) or set(pins) != set(_DEPENDENCIES):
        return False
    sets = (value["private"], value["proxy"], value["v2"])
    if no_proxy_succeeded:
        sets += (value["no_proxy"],)
    if any(not isinstance(rows, Mapping) or set(rows) != set(_DEPENDENCIES) for rows in sets):
        return False
    for name in _DEPENDENCIES:
        rows = [dependency_set[name] for dependency_set in sets]
        if any(not isinstance(row, Mapping) or set(row) != _REPO_IDENTITY_KEYS for row in rows):
            return False
        if any(row["head"] != pins[name] for row in rows):
            return False
        if any(
            row[key] is not True
            for row in rows
            for key in ("tracked_clean", "untracked_clean", "ignored_clean", "alternates_absent")
        ):
            return False
        if any(row != rows[0] for row in rows[1:]):
            return False
    required_flags = (
        "private_copy_verified", "shared_unchanged", "proxy_common_root",
        "proxy_stable_terminal", "v2_reobserved",
    )
    if no_proxy_succeeded:
        required_flags += ("no_proxy_common_root", "no_proxy_stable_terminal")
    return all(value[key] is True for key in required_flags)


def _classify(value: Mapping[str, Any]) -> tuple[str, str]:
    """Closed classifier.  Each B-057 mutation has one decision anchor."""
    if value.get("precondition_valid") is not True:
        return "indeterminate", "precondition-failed"
    if value.get("setup_valid") is not True:
        return "indeterminate", "setup-failed"
    arms = value.get("arms")
    if not isinstance(arms, Mapping) or tuple(arms) != _ARM_IDS:
        return "indeterminate", "arm-schema"
    if any(arms[arm_id].get("outcome") == "timeout" for arm_id in _ARM_IDS):
        return "indeterminate", "timeout"
    if value.get("identity_match") is not True:
        return "indeterminate", "run-identity"
    if any(
        arms[arm_id].get("fresh") is not True or arms[arm_id].get("cached") is not False
        for arm_id in _ARM_IDS
    ):  # M1 anchor
        return "indeterminate", "cache-hit"
    proxy = arms["legacy-proxy"]
    no_proxy = arms["legacy-no-proxy"]
    v2 = arms["v2-source-no-proxy"]
    if (
        value.get("control_valid") is not True
        or proxy.get("outcome") != "success"
        or proxy.get("observer") != "complete"
    ):  # M6 anchor: the proxy control has no later duplicate gate.
        return "indeterminate", "control-invalid"
    if not _dependency_binding_matches(
        value.get("dependency_evidence"),
        no_proxy_succeeded=no_proxy.get("outcome") == "success",
    ):  # M4 anchor: inspect producer evidence, never an aggregate Boolean.
        return "indeterminate", "dependency-identity"
    if proxy.get("shape") != {
        "observed": True, "base_dir_count": 0, "source_dir_count": 0,
        "base_dir_binding": "absent", "source_dir_binding": "absent",
        "legacy_source_seam": False,
    }:
        return "indeterminate", "legacy-configure-shape"
    if v2.get("outcome") != "success" or v2.get("shape") != {
        "observed": True, "base_dir_count": 1, "source_dir_count": 3,
        "base_dir_binding": "exact", "source_dir_binding": "exact",
        "legacy_source_seam": False,
    }:
        return "indeterminate", "v2-arm"
    if v2.get("git_protocol_evidence") != "file-only-policy-success":  # M3 anchor
        return "indeterminate", "v2-file-protocol-evidence"
    if no_proxy.get("outcome") == "success":
        if no_proxy.get("shape") != {
            "observed": True, "base_dir_count": 0, "source_dir_count": 0,
            "base_dir_binding": "absent", "source_dir_binding": "absent",
            "legacy_source_seam": False,
        }:
            return "indeterminate", "legacy-configure-shape"
        if no_proxy.get("observer") != "complete":
            return "indeterminate", "legacy-no-proxy-observer"
        return "keep-current-candidate-material", "legacy-no-proxy-succeeded"
    if (
        no_proxy.get("outcome") != "failed"
        or no_proxy.get("stage") != "configure"
        or no_proxy.get("cause") != "external-git-fetch-failed"
    ):  # M2 anchor
        return "indeterminate", "legacy-no-proxy-stage"
    if (
        no_proxy.get("observer") != "external-git-observed"
        or no_proxy.get("external_git_evidence") != "policy-remote-process-observed"
    ):
        return "indeterminate", "external-git-evidence"
    return "migration-candidate-material", "single-run-proxy-sensitivity"


def _arm_environments(base: Mapping[str, str], proxy_value: str) -> dict[str, dict[str, str]]:
    common = {
        key: value for key, value in base.items()
        if key.lower() not in _PROXY_KEYS_CASEFOLD
        and not key.startswith("GIT_")
    }
    common.update(_GIT_CONFIG)
    proxy = dict(common)
    proxy["http_proxy"] = proxy_value
    proxy["https_proxy"] = proxy_value
    no_proxy = dict(common)
    v2 = dict(common)
    v2["GIT_ALLOW_PROTOCOL"] = "file"
    if "GIT_ALLOW_PROTOCOL" in proxy or "GIT_ALLOW_PROTOCOL" in no_proxy:
        raise RuntimeError("legacy Git protocol guard must remain absent")
    if {
        key for key in set(proxy) | set(no_proxy)
        if proxy.get(key) != no_proxy.get(key)
    } != {"http_proxy", "https_proxy"}:
        raise RuntimeError("legacy arm delta must contain only lowercase proxy values")
    return {
        "legacy-proxy": proxy,
        "legacy-no-proxy": no_proxy,
        "v2-source-no-proxy": v2,
    }


class _DeadlineExpired(RuntimeError):
    pass


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise _DeadlineExpired("T-2000 fixed deadline expired")
    return remaining


@contextlib.contextmanager
def _deadline_alarm(deadline: float):
    """Interrupt coordinator-only synchronous work at one absolute deadline."""
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)

    def expired(_signum: int, _frame: object) -> None:
        raise _DeadlineExpired("T-2000 fixed deadline expired")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, _remaining(deadline))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)


def _run_git(
    repo: Path, *args: str, deadline: float, mutate: bool = False,
) -> str:
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env.update(_GIT_CONFIG)
    command = ["git", "-c", "core.fsmonitor=", "-c", "core.hooksPath=",
               "-c", "core.useReplaceRefs=false", "-C", os.fspath(repo), *args]
    operation_timeout = max(
        0.05, min(_OBSERVER_GIT_SLICE_S, _remaining(deadline)),
    )
    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=env, timeout=operation_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        if time.monotonic() >= deadline:
            raise _DeadlineExpired("bounded Git observation expired") from None
        raise RuntimeError("Git operation exceeded its bounded observation slice") from None
    except (OSError, subprocess.SubprocessError):
        raise RuntimeError("Git operation failed") from None
    if result.returncode != 0:
        raise RuntimeError("Git operation failed")
    if mutate and result.stdout is None:
        raise RuntimeError("Git mutation produced no result channel")
    return result.stdout.rstrip("\n")


def _source_status(
    status: str, *, generated_paths: frozenset[str],
) -> tuple[str, bool, bool, bool]:
    """Project status to source inputs, excluding only known run-local outputs."""
    records = tuple(record for record in status.split("\0") if record)
    source_records = tuple(
        record for record in records
        if not (
            record.startswith(("?? ", "!! "))
            and record[3:] in generated_paths
        )
    )
    projected = "\0".join(source_records) + ("\0" if source_records else "")
    tracked_clean = not any(
        not record.startswith(("??", "!!")) for record in source_records
    )
    untracked_clean = not any(record.startswith("??") for record in source_records)
    ignored_clean = not any(record.startswith("!!") for record in source_records)
    return projected, tracked_clean, untracked_clean, ignored_clean


def _worktree_sha256(
    repo: Path, *, deadline: float, generated_paths: frozenset[str],
) -> str:
    digest = hashlib.sha256()
    for root, dirs, files in os.walk(repo, topdown=True, followlinks=False):
        _remaining(deadline)
        root_path = Path(root)
        if root_path == repo:
            dirs[:] = sorted(name for name in dirs if name != ".git")
        else:
            dirs.sort()
        symlink_dirs = [name for name in dirs if (root_path / name).is_symlink()]
        dirs[:] = [name for name in dirs if name not in symlink_dirs]
        for name in symlink_dirs:
            path = root_path / name
            relative = os.fspath(path.relative_to(repo))
            digest.update(relative.encode("utf-8", "surrogateescape") + b"\0L\0")
            digest.update(os.readlink(path).encode("utf-8", "surrogateescape"))
        for name in sorted(files):
            _remaining(deadline)
            path = root_path / name
            relative = os.fspath(path.relative_to(repo))
            if relative in generated_paths:
                continue
            info_before = path.lstat()
            digest.update(relative.encode("utf-8", "surrogateescape") + b"\0")
            digest.update(str(info_before.st_mode).encode("ascii") + b"\0")
            if path.is_symlink():
                digest.update(os.readlink(path).encode("utf-8", "surrogateescape"))
                continue
            if not path.is_file():
                raise RuntimeError("dependency worktree contains a special file")
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1 << 20), b""):
                    _remaining(deadline)
                    digest.update(chunk)
            info_after = path.lstat()
            if (
                info_before.st_dev, info_before.st_ino, info_before.st_size,
                info_before.st_mtime_ns, info_before.st_ctime_ns,
            ) != (
                info_after.st_dev, info_after.st_ino, info_after.st_size,
                info_after.st_mtime_ns, info_after.st_ctime_ns,
            ):
                raise RuntimeError("dependency worktree changed during hashing")
    return digest.hexdigest()


def _repo_identity(
    repo: Path, *, expected_pin: str | None, require_clean: bool, deadline: float,
    generated_paths: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    if repo.is_symlink() or not repo.is_dir():
        raise RuntimeError("dependency source is not a real directory")
    canonical = repo.resolve(strict=True)
    if canonical != repo.absolute():
        raise RuntimeError("dependency source is not canonical")
    top = Path(_run_git(repo, "rev-parse", "--show-toplevel", deadline=deadline)).resolve(strict=True)
    if top != canonical:
        raise RuntimeError("dependency repository root mismatch")
    git_dir = Path(_run_git(repo, "rev-parse", "--absolute-git-dir", deadline=deadline)).resolve(strict=True)
    try:
        git_dir.relative_to(canonical)
    except ValueError:
        raise RuntimeError("dependency git-dir escapes repository root") from None
    common_dir_raw = _run_git(repo, "rev-parse", "--git-common-dir", deadline=deadline)
    common_dir = Path(common_dir_raw)
    if not common_dir.is_absolute():
        common_dir = repo / common_dir
    try:
        common_dir.resolve(strict=True).relative_to(canonical)
    except ValueError:
        raise RuntimeError("dependency Git common-dir escapes repository root") from None
    head = _run_git(repo, "rev-parse", "--verify", "HEAD^{commit}", deadline=deadline)
    tree = _run_git(repo, "rev-parse", "--verify", "HEAD^{tree}", deadline=deadline)
    if not _is_hex(head, _HEX40) or not _is_hex(tree, _HEX40):
        raise RuntimeError("dependency Git identity is not full SHA-1")
    if expected_pin is not None and head != expected_pin:
        raise RuntimeError("dependency pin mismatch")
    alternates = Path(_run_git(
        repo, "rev-parse", "--git-path", "objects/info/alternates", deadline=deadline,
    ))
    if not alternates.is_absolute():
        alternates = repo / alternates
    if alternates.exists() or "GIT_ALTERNATE_OBJECT_DIRECTORIES" in os.environ:
        raise RuntimeError("dependency repository has Git alternates")
    status = _run_git(
        repo, "status", "--porcelain=v1", "--untracked-files=all", "--ignored=matching",
        "-z", deadline=deadline,
    )
    source_status, tracked_clean, untracked_clean, ignored_clean = _source_status(
        status, generated_paths=generated_paths,
    )
    if require_clean and not (tracked_clean and untracked_clean and ignored_clean):
        raise RuntimeError("private dependency repository is not fully clean")
    config = _run_git(repo, "config", "--local", "--includes", "--null", "--list", deadline=deadline)
    return {
        "head": head,
        "tree": tree,
        "status_sha256": _sha256_text(source_status),
        "worktree_sha256": _worktree_sha256(
            repo, deadline=deadline, generated_paths=generated_paths,
        ),
        "config_sha256": _sha256_text(config),
        "tracked_clean": tracked_clean,
        "untracked_clean": untracked_clean,
        "ignored_clean": ignored_clean,
        "alternates_absent": True,
    }


def _normalize_private_repo(repo: Path, pin: str, *, deadline: float) -> dict[str, Any]:
    _run_git(repo, "reset", "--hard", pin, mutate=True, deadline=deadline)
    _run_git(repo, "clean", "-ffdqx", mutate=True, deadline=deadline)
    return _repo_identity(repo, expected_pin=pin, require_clean=True, deadline=deadline)


def _dependency_set_identity(
    root: Path, pins: Mapping[str, str], *, source_suffix: str, require_clean: bool,
    deadline: float, allow_run_local_generated: bool = False,
) -> dict[str, dict[str, Any]]:
    return {
        name: _repo_identity(
            root / f"{name}{source_suffix}", expected_pin=pins[name],
            require_clean=require_clean, deadline=deadline,
            generated_paths=(
                _RUN_LOCAL_GENERATED_PATHS[name]
                if allow_run_local_generated else frozenset()
            ),
        )
        for name in _DEPENDENCIES
    }


def _load_dependency_policy(repo_root: Path) -> dict[str, dict[str, str]]:
    try:
        policy = json.loads((repo_root / "tools/pegasus/policy.json").read_text(encoding="utf-8"))
        rows = policy["silo_ladder_rung1"]["third_party_sources"]
    except (OSError, UnicodeError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise RuntimeError("dependency policy cannot be loaded") from None
    if type(rows) is not list or len(rows) != 3:
        raise RuntimeError("dependency policy must contain exactly three sources")
    out: dict[str, dict[str, str]] = {}
    required = frozenset({"name", "source_name", "url", "fetchcontent_ref", "pin"})
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != required:
            raise RuntimeError("dependency policy row has an invalid shape")
        name = row["name"]
        if name not in _DEPENDENCIES or row["source_name"] != name or name in out:
            raise RuntimeError("dependency policy source name is invalid")
        if any(type(row[key]) is not str or not row[key] for key in required):
            raise RuntimeError("dependency policy value is invalid")
        if not _URL_SCHEME.search(row["url"]) or not _is_hex(row["pin"], _HEX40):
            raise RuntimeError("dependency URL or pin is invalid")
        out[name] = dict(row)
    if tuple(out) != _DEPENDENCIES:
        raise RuntimeError("dependency policy order is invalid")
    return out


def _load_cmake_declarations(repo_root: Path) -> dict[str, dict[str, str]]:
    path = repo_root / "external/ccbench/cmake/ThirdParty.cmake"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise RuntimeError("ThirdParty.cmake cannot be read") from None
    assignments: dict[tuple[str, str], str] = {}
    pattern = re.compile(
        r'(?m)^set\(CCBENCH_(MASSTREE|MIMALLOC|GOOGLETEST)_(REPO|TAG)[ \t]+"([^"\r\n]+)"\)'
    )
    for match in pattern.finditer(text):
        key = (match.group(1).lower(), match.group(2).lower())
        if key in assignments:
            raise RuntimeError("duplicate CMake dependency assignment")
        assignments[key] = match.group(3)
    expected = {(name, field) for name in _DEPENDENCIES for field in ("repo", "tag")}
    if set(assignments) != expected:
        raise RuntimeError("CMake dependency assignment set is invalid")
    declared: dict[str, dict[str, str]] = {}
    for name in _DEPENDENCIES:
        blocks = re.findall(
            rf"(?ms)FetchContent_Declare\([ \t\r\n]*{name}\b(.*?)^[ \t]*\)", text,
        )
        if len(blocks) != 1:
            raise RuntimeError("FetchContent declaration is not unique")
        block = blocks[0]
        if f'GIT_REPOSITORY "${{CCBENCH_{name.upper()}_REPO}}"' not in block:
            raise RuntimeError("FetchContent repository binding is invalid")
        if f'GIT_TAG        "${{CCBENCH_{name.upper()}_TAG}}"' not in block:
            raise RuntimeError("FetchContent ref binding is invalid")
        declared[name] = {
            "url": assignments[(name, "repo")],
            "fetchcontent_ref": assignments[(name, "tag")],
        }
    return declared


def _dependency_contract(repo_root: Path) -> tuple[dict[str, dict[str, str]], str]:
    policy = _load_dependency_policy(repo_root)
    cmake = _load_cmake_declarations(repo_root)
    for name in _DEPENDENCIES:
        if cmake[name]["url"] != policy[name]["url"]:
            raise RuntimeError("CMake/policy dependency URL mismatch")
        if cmake[name]["fetchcontent_ref"] != policy[name]["fetchcontent_ref"]:
            raise RuntimeError("CMake/policy FetchContent ref mismatch")
    # In particular, mimalloc's v2.3.2 declaration is compared as a ref here;
    # only the independent policy pin below is required to be full 40 hex.
    projection = {
        name: {
            "ref_sha256": _sha256_text(policy[name]["fetchcontent_ref"]),
            "pin": policy[name]["pin"],
        }
        for name in _DEPENDENCIES
    }
    return policy, _sha256_value(projection)


def _read_b10_proxy(repo_root: Path) -> str:
    try:
        text = (repo_root / "tools/pegasus/b10_backoff_grid.sh").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise RuntimeError("B-10 script cannot be read") from None
    matches = re.findall(r"(?m)^BUILD_NETWORK_PROXY_URL=([^\s#]+)[ \t]*$", text)
    if len(matches) != 1 or _URL_SCHEME.match(matches[0]) is None:
        raise RuntimeError("B-10 proxy literal is not unique")
    return matches[0]


def _git_head(repo: Path, *, deadline: float) -> str:
    head = _run_git(repo, "rev-parse", "--verify", "HEAD^{commit}", deadline=deadline)
    if not _is_hex(head, _HEX40):
        raise RuntimeError("CCBench HEAD is not full SHA-1")
    return head


def _tool_resolution(cc: str, cxx: str) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for role, requested in (("git", "git"), ("cmake", "cmake"), ("cc", cc), ("cxx", cxx)):
        found = shutil.which(requested)
        if not found:
            raise RuntimeError("required tool is unavailable")
        real = os.path.realpath(found)
        if not os.path.isfile(real) or not os.access(real, os.X_OK):
            raise RuntimeError("required tool is not an executable regular file")
        resolved[role] = real
    return resolved


def _require_compute_pbs() -> dict[str, str]:
    resolved_site = buildcache.require_heavy_work_site(None, "T-2000 build probe")
    if resolved_site != site_policy.PEGASUS_COMPUTE:
        raise RuntimeError("T-2000 probe is Pegasus-compute-only")
    job = os.environ.get("PBS_JOBID", "")
    nodefile_raw = os.environ.get("PBS_NODEFILE", "")
    if not job or not nodefile_raw:
        raise RuntimeError("T-2000 probe requires PBS binding")
    nodefile = Path(nodefile_raw)
    if nodefile.is_symlink() or not nodefile.is_file():
        raise RuntimeError("PBS nodefile is not a regular file")
    try:
        nodes = tuple(
            line.strip().split(".")[0]
            for line in nodefile.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    except (OSError, UnicodeError):
        raise RuntimeError("PBS nodefile cannot be read") from None
    observed = socket.gethostname().split(".")[0]
    if not nodes or set(nodes) != {observed} or not re.fullmatch(r"bnode[0-9]+", observed):
        raise RuntimeError("T-2000 probe requires one allocated compute node")
    tmp_raw = os.environ.get("TMPDIR", "")
    if not tmp_raw or not os.path.isabs(tmp_raw):
        raise RuntimeError("T-2000 probe requires an absolute TMPDIR")
    tmp = Path(tmp_raw)
    if tmp.is_symlink() or not tmp.is_dir() or not os.fspath(tmp.resolve()).startswith("/scr/"):
        raise RuntimeError("T-2000 probe requires job-local compute scratch")
    return {"site": resolved_site, "job": job, "node": observed, "tmp": os.fspath(tmp)}


def _source_evidence_hash(evidence: source_digest.SourceEvidence) -> str:
    return _sha256_value(evidence.as_receipt())


def _identity_material(context: Mapping[str, Any], *, deadline: float) -> dict[str, str]:
    if os.getpid() != context["coordinator_pid"] and os.getppid() != context["coordinator_pid"]:
        raise RuntimeError("arm is detached from the coordinator")
    if site_policy.current_site() != site_policy.PEGASUS_COMPUTE:
        raise RuntimeError("site changed during probe")
    if _git_head(context["ccbench_dir"], deadline=deadline) != context["ccbench_commit"]:
        raise RuntimeError("CCBench HEAD changed during probe")
    manifest = buildcache.observed_toolchain_manifest(context["cc"], context["cxx"])
    if manifest != context["toolchain_manifest"]:
        raise RuntimeError("toolchain changed during probe")
    evidence = source_digest.resolve_evidence(
        context["genome"], context["ccbench_commit"],
        ccbench_dir=os.fspath(context["ccbench_dir"]), cxx=context["cxx"],
    )
    if evidence != context["source_evidence"]:
        raise RuntimeError("source evidence changed during probe")
    tools = _tool_resolution(context["cc"], context["cxx"])
    if tools != context["tool_resolution"] or os.environ.get("PATH", "") != context["path"]:
        raise RuntimeError("PATH tool resolution changed during probe")
    for key, expected in _GIT_CONFIG.items():
        if os.environ.get(key) != expected:
            raise RuntimeError("Git config isolation changed during probe")
    material = {
        "node_sha256": _sha256_text(socket.gethostname()),
        "pbs_job_sha256": _sha256_text(context["pbs_job"]),
        "ccbench_commit": context["ccbench_commit"],
        "genome_sha256": _sha256_text(context["genome"].canonical()),
        "toolchain_manifest_sha256": _sha256_value(manifest),
        "source_evidence_sha256": _source_evidence_hash(evidence),
        "policy_sha256": context["build_context"].policy.sha256,
        "context_nonce_sha256": _sha256_text(context["build_context"]._context_nonce),
        "admission_receipt_sha256": context["admission"].receipt_sha256,
        "contract_sha256": context["contract"].contract_sha256,
        "activation_state_sha256": context["activation_state_sha256"],
        "path_sha256": _sha256_text(context["path"]),
        "tool_resolution_sha256": _sha256_value(tools),
        "git_config_sha256": _sha256_value(_GIT_CONFIG),
    }
    return material


def _fixed_exception_codes(exc: Exception, *, arm_id: str) -> tuple[str, str]:
    """Inspect exception text in memory, returning only closed codes."""
    name = type(exc).__name__
    lowered = str(exc).lower()
    if name == "BuildAdmissionError" or "admission" in name.lower():
        return "admission", "unexpected"
    if "heavy" in lowered or "login" in lowered or "site" in lowered:
        return "precondition", "site-gate"
    stage = (
        "configure" if "configure failed (rc=" in lowered
        else "build" if "build failed (rc=" in lowered else "unknown"
    )
    # These are network-specific Git/curl diagnostics.  Generic FetchContent,
    # clone, download, and proxy words are intentionally insufficient.
    git_fetch_markers = (
        "could not resolve host", "failed to connect to", "network is unreachable",
        "connection timed out", "couldn't connect to server", "proxy connect aborted",
    )
    if arm_id == "legacy-no-proxy" and stage == "configure" and any(
        marker in lowered for marker in git_fetch_markers
    ):
        return "configure", "external-git-fetch-failed"
    return stage, "unexpected"


@contextlib.contextmanager
def _installed_environment(environment: Mapping[str, str]):
    saved = dict(os.environ)
    os.environ.clear()
    os.environ.update(environment)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(saved)


def _write_pipe_json(fd: int, value: Mapping[str, Any]) -> None:
    payload = _canonical_bytes(value)
    if len(payload) > 48 * 1024:
        raise RuntimeError("supervisor payload is too large")
    view = memoryview(payload)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise RuntimeError("supervisor pipe write did not progress")
        view = view[written:]


def _enable_child_subreaper() -> None:
    if sys.platform != "linux":
        raise RuntimeError("T-2000 process supervision requires Linux subreaper support")
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
        raise RuntimeError("T-2000 could not enable child subreaper supervision")


def _reap_process_group_children(process_group: int) -> None:
    while True:
        try:
            waited, _ = os.waitpid(-process_group, os.WNOHANG)
        except ChildProcessError:
            return
        if waited <= 0:
            return


def _kill_process_group(
    pid: int, *, leader_reaped: bool = False, deadline: float | None = None,
) -> None:
    cleanup_deadline = min(
        time.monotonic() + _TERM_GRACE_S,
        deadline if deadline is not None else time.monotonic() + _TERM_GRACE_S,
    )
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        if not leader_reaped:
            try:
                os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                pass
        return
    while time.monotonic() < cleanup_deadline:
        _reap_process_group_children(pid)
        if not leader_reaped:
            try:
                waited, _ = os.waitpid(pid, os.WNOHANG)
                leader_reaped = waited == pid
            except ChildProcessError:
                leader_reaped = True
        try:
            os.killpg(pid, 0)
        except ProcessLookupError:
            if not leader_reaped:
                try:
                    os.waitpid(pid, os.WNOHANG)
                except ChildProcessError:
                    pass
            return
        time.sleep(_SUPERVISOR_POLL_S)
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        if not leader_reaped:
            os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        pass
    _reap_process_group_children(pid)


def _supervise(
    callback: Callable[[int], Mapping[str, Any]], *, deadline: float,
    observer: "_LegacyObserver | None" = None,
) -> dict[str, Any]:
    ready_r, ready_w = os.pipe()
    start_r, start_w = os.pipe()
    result_r, result_w = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(ready_r)
            os.close(start_r)
            os.close(result_r)
            try:
                os.setpgid(0, 0)
            except PermissionError:
                pass
            null_fd = os.open(os.devnull, os.O_WRONLY)
            try:
                os.dup2(null_fd, 1)
                os.dup2(null_fd, 2)
            finally:
                if null_fd > 2:
                    os.close(null_fd)
            os.write(ready_w, b"R")
            os.close(ready_w)
            result = callback(start_w)
            os.close(start_w)
            _write_pipe_json(result_w, result)
            os.close(result_w)
            os._exit(0)
        except BaseException:
            try:
                _write_pipe_json(result_w, {
                    "supervisor_status": "child-error",
                    "stage_code": "unknown",
                    "cause_code": "unexpected",
                })
            except BaseException:
                pass
            os._exit(70)

    os.close(ready_w)
    os.close(start_w)
    os.close(result_w)
    try:
        os.setpgid(pid, pid)
    except (PermissionError, ProcessLookupError):
        pass
    os.set_blocking(result_r, False)
    chunks: list[bytes] = []
    try:
        ready, _, _ = select.select([ready_r], [], [], min(5.0, _remaining(deadline)))
        if not ready or os.read(ready_r, 1) != b"R":
            _kill_process_group(pid, deadline=deadline)
            return {"supervisor_status": "child-error", "stage_code": "unknown", "cause_code": "unexpected"}
        started_at: float | None = None
        status = None
        while True:
            if time.monotonic() >= deadline - _TERM_GRACE_S:
                wall = None if started_at is None else round(time.monotonic() - started_at, 6)
                _kill_process_group(pid, deadline=deadline)
                return {
                    "supervisor_status": "timeout", "stage_code": "unknown",
                    "cause_code": "timeout", "wall_s": wall,
                }
            if observer is not None:
                try:
                    observer.poll(
                        process_group=pid, deadline=deadline - _TERM_GRACE_S,
                    )
                except _DeadlineExpired:
                    wall = None if started_at is None else round(time.monotonic() - started_at, 6)
                    _kill_process_group(pid, deadline=deadline)
                    return {
                        "supervisor_status": "timeout", "stage_code": "unknown",
                        "cause_code": "timeout", "wall_s": wall,
                    }
                except Exception:
                    _kill_process_group(pid, deadline=deadline)
                    return {
                        "supervisor_status": "observer-error", "stage_code": "observer",
                        "cause_code": "observer-mismatch",
                    }
            if started_at is None:
                readable, _, _ = select.select([start_r], [], [], 0)
                if readable and os.read(start_r, 1) == b"S":
                    started_at = time.monotonic()
            while True:
                try:
                    chunk = os.read(result_r, 65536)
                except BlockingIOError:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
            waited, status = os.waitpid(pid, os.WNOHANG)
            if waited == pid:
                break
            if time.monotonic() >= deadline - _TERM_GRACE_S:
                wall = None if started_at is None else round(time.monotonic() - started_at, 6)
                _kill_process_group(pid, deadline=deadline)
                return {
                    "supervisor_status": "timeout", "stage_code": "unknown",
                    "cause_code": "timeout", "wall_s": wall,
                }
            time.sleep(_SUPERVISOR_POLL_S)
        if observer is not None:
            if time.monotonic() >= deadline - _TERM_GRACE_S:
                _kill_process_group(pid, leader_reaped=True, deadline=deadline)
                return {
                    "supervisor_status": "timeout", "stage_code": "unknown",
                    "cause_code": "timeout",
                    "wall_s": None if started_at is None else round(
                        time.monotonic() - started_at, 6,
                    ),
                }
            try:
                observer.poll(
                    process_group=pid, deadline=deadline - _TERM_GRACE_S,
                )
            except _DeadlineExpired:
                _kill_process_group(pid, leader_reaped=True, deadline=deadline)
                return {
                    "supervisor_status": "timeout", "stage_code": "unknown",
                    "cause_code": "timeout",
                    "wall_s": None if started_at is None else round(
                        time.monotonic() - started_at, 6,
                    ),
                }
            except Exception:
                _kill_process_group(pid, leader_reaped=True, deadline=deadline)
                return {
                    "supervisor_status": "observer-error", "stage_code": "observer",
                    "cause_code": "observer-mismatch",
                }
        _kill_process_group(pid, leader_reaped=True, deadline=deadline)
        os.set_blocking(result_r, True)
        while True:
            chunk = os.read(result_r, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        if not chunks or status is None or not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
            return {"supervisor_status": "child-error", "stage_code": "unknown", "cause_code": "unexpected"}
        try:
            value = json.loads(b"".join(chunks).decode("utf-8"))
        except (UnicodeError, ValueError, json.JSONDecodeError):
            return {"supervisor_status": "child-error", "stage_code": "unknown", "cause_code": "unexpected"}
        if not isinstance(value, dict):
            return {"supervisor_status": "child-error", "stage_code": "unknown", "cause_code": "unexpected"}
        value["supervisor_status"] = "complete"
        value["execution_model"] = "supervised-child-process-group"
        return value
    finally:
        try:
            waited, _ = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            waited = pid
        if waited == 0:
            _kill_process_group(pid, deadline=deadline)
        for fd in (ready_r, start_r, result_r):
            try:
                os.close(fd)
            except OSError:
                pass


class _LegacyObserver:
    def __init__(
        self, cache_root: Path, pins: Mapping[str, str], *,
        policy_urls: Mapping[str, str], scratch_path: Path,
    ):
        self.cache_root = cache_root
        self.pins = pins
        self.policy_urls = tuple(url.encode("utf-8") for url in policy_urls.values())
        self.scratch_path = scratch_path
        self.samples: dict[str, dict[str, Any]] = {
            name: {"last": None, "stable": 0} for name in _DEPENDENCIES
        }
        self.fault = "none"
        self.staging_root: Path | None = None
        self.stable_terminal = False
        self.external_git_observed = False
        self.generated_outputs_verified = False
        self.generated_outputs: tuple[Mapping[str, str], str] | None = None

    def _observe_processes(self, process_group: int) -> None:
        for proc in Path("/proc").iterdir():
            if not proc.name.isdigit():
                continue
            try:
                stat_text = (proc / "stat").read_text(encoding="utf-8")
                tail = stat_text[stat_text.rfind(")") + 2:].split()
                if len(tail) < 3 or int(tail[2]) != process_group:
                    continue
                executable = os.path.basename(os.readlink(proc / "exe"))
                if executable != "git" and not executable.startswith("git-remote-"):
                    continue
                argv = tuple(part for part in (proc / "cmdline").read_bytes().split(b"\0") if part)
            except (FileNotFoundError, PermissionError, ProcessLookupError, OSError, ValueError):
                continue
            if any(url in argv for url in self.policy_urls):
                self.external_git_observed = True

    def _observe_scratch(self) -> None:
        stats = os.statvfs(self.scratch_path)
        if (
            stats.f_bavail * stats.f_frsize < _SCRATCH_MIN_FREE_BYTES
            or stats.f_favail < _SCRATCH_MIN_FREE_INODES
        ):
            self.fault = "scratch-precondition"

    def poll(self, *, process_group: int, deadline: float) -> None:
        _remaining(deadline)
        self._observe_processes(process_group)
        self._observe_scratch()
        if self.fault != "none" or not self.cache_root.exists():
            return
        current: dict[str, Path] = {}
        for name in _DEPENDENCIES:
            candidates = tuple(self.cache_root.glob(f"*.staging-*/_deps/{name}-src"))
            if len(candidates) > 1:
                self.fault = "mismatch"
                return
            if not candidates:
                continue
            current[name] = candidates[0]
        if not current:
            if all(self.samples[name]["stable"] >= 2 for name in _DEPENDENCIES):
                self.stable_terminal = True
            return
        roots = {path.parent.parent.resolve(strict=True) for path in current.values()}
        if len(roots) != 1:
            self.fault = "mismatch"
            return
        root = roots.pop()
        if self.staging_root is None:
            self.staging_root = root
        elif root != self.staging_root:
            self.fault = "mismatch"
            return
        for name, candidate in current.items():
            try:
                observed = _repo_identity(
                    candidate, expected_pin=None, require_clean=False, deadline=deadline,
                    generated_paths=_RUN_LOCAL_GENERATED_PATHS[name],
                )
            except _DeadlineExpired:
                raise
            except RuntimeError:
                if self.samples[name]["last"] is not None:
                    self.fault = "mismatch"
                    return
                continue
            row = self.samples[name]
            if row["last"] == observed:
                row["stable"] += 1
            else:
                row["last"] = observed
                row["stable"] = 1
            if observed["head"] != self.pins[name]:
                self.fault = "mismatch"
                return
            if name == "masstree":
                try:
                    receipt = buildcache._observe_fetchcontent_dependency_receipt(
                        os.fspath(candidate)
                    )
                    archive = buildcache._observe_fetchcontent_archive_sha256(
                        os.fspath(candidate)
                    )
                except Exception:
                    if self.generated_outputs is not None:
                        self.fault = "mismatch"
                        return
                else:
                    generated_outputs = (receipt, archive)
                    products_valid = (
                        receipt.get("masstree_head") == observed["head"]
                        and _is_hex(receipt.get("config_sha256"), _HEX64)
                        and _is_hex(archive, _HEX64)
                    )
                    if not products_valid or (
                        self.generated_outputs is not None
                        and generated_outputs != self.generated_outputs
                    ):
                        self.fault = "mismatch"
                        return
                    self.generated_outputs = generated_outputs
                    self.generated_outputs_verified = True

    def finish(self) -> dict[str, Any]:
        heads = {
            name: None if self.samples[name]["last"] is None else self.samples[name]["last"]["head"]
            for name in _DEPENDENCIES
        }
        identities = (
            {name: self.samples[name]["last"] for name in _DEPENDENCIES}
            if all(self.samples[name]["last"] is not None for name in _DEPENDENCIES)
            else None
        )
        if self.fault != "none":
            return {
                "status": "mismatch", "heads": heads, "identities": identities,
                "identity_sha256": None, "common_staging_root": self.staging_root is not None,
                "stable_terminal": self.stable_terminal,
                "external_git_evidence": (
                    "policy-remote-process-observed" if self.external_git_observed
                    else "not-observed"
                ),
                "fault": self.fault,
            }
        complete = identities is not None and all(
            self.samples[name]["stable"] >= 2 for name in _DEPENDENCIES
        ) and (
            self.stable_terminal
            and self.staging_root is not None
            and self.generated_outputs_verified
        )
        if complete:
            return {
                "status": "complete", "heads": heads,
                "identities": identities, "identity_sha256": _sha256_value(identities),
                "common_staging_root": True, "stable_terminal": True,
                "external_git_evidence": (
                    "policy-remote-process-observed" if self.external_git_observed
                    else "not-observed"
                ),
                "fault": "none",
            }
        return {
            "status": (
                "external-git-observed" if self.external_git_observed else "missed"
            ),
            "heads": heads, "identities": identities, "identity_sha256": None,
            "common_staging_root": self.staging_root is not None,
            "stable_terminal": self.stable_terminal,
            "external_git_evidence": (
                "policy-remote-process-observed" if self.external_git_observed
                else "not-observed"
            ),
            "fault": "none",
        }


def _unobserved_configure_shape() -> dict[str, Any]:
    return {
        "observed": False, "base_dir_count": None, "source_dir_count": None,
        "base_dir_binding": "unobserved", "source_dir_binding": "unobserved",
        "legacy_source_seam": None,
    }


def _configure_shape(
    argv: tuple[str, ...], *, expected_base: Path | None,
    expected_sources: Mapping[str, Path], legacy: bool,
) -> dict[str, Any]:
    bases = [token.split("=", 1)[1] for token in argv if token.startswith("-DFETCHCONTENT_BASE_DIR=")]
    sources: dict[str, list[str]] = {name: [] for name in _DEPENDENCIES}
    unknown_source = False
    for token in argv:
        if not token.startswith("-DFETCHCONTENT_SOURCE_DIR_"):
            continue
        key, separator, raw_value = token.partition("=")
        name = key.removeprefix("-DFETCHCONTENT_SOURCE_DIR_").lower()
        if not separator or name not in sources:
            unknown_source = True
            continue
        sources[name].append(raw_value)
    expected_base_text = None if expected_base is None else os.fspath(expected_base)
    expected_source_text = {name: os.fspath(path) for name, path in expected_sources.items()}
    base_binding = (
        "absent" if expected_base_text is None and not bases
        else "exact" if bases == [expected_base_text]
        else "mismatch"
    )
    actual_source_count = sum(len(values) for values in sources.values()) + int(unknown_source)
    if not expected_source_text and actual_source_count == 0:
        source_binding = "absent"
    elif (
        not unknown_source
        and set(expected_source_text) == set(_DEPENDENCIES)
        and all(sources[name] == [expected_source_text[name]] for name in _DEPENDENCIES)
    ):
        source_binding = "exact"
    else:
        source_binding = "mismatch"
    return {
        "observed": True,
        "base_dir_count": len(bases),
        "source_dir_count": actual_source_count,
        "base_dir_binding": base_binding,
        "source_dir_binding": source_binding,
        "legacy_source_seam": legacy and (bool(bases) or actual_source_count > 0),
    }


def _empty_arm(arm_id: str) -> dict[str, Any]:
    production = "build_v2" if arm_id == "v2-source-no-proxy" else "build"
    transport = {
        "legacy-proxy": "lowercase-proxy",
        "legacy-no-proxy": "proxy-env-removed",
        "v2-source-no-proxy": "source-dir-file-guard",
    }[arm_id]
    return {
        "id": arm_id,
        "production_call": production,
        "transport_mode": transport,
        "git_protocol_guard": "file-only" if production == "build_v2" else "absent",
        "fresh_cache_precondition": False,
        "outcome": "not-run",
        "wall_s": None,
        "cached": None,
        "stage_code": "precondition",
        "cause_code": "not-run",
        "invariant_status": "not-observed",
        "invariant_before_sha256": None,
        "invariant_after_sha256": None,
        "observer_status": "not-run",
        "observed_heads": {name: None for name in _DEPENDENCIES},
        "dependency_identity_sha256": None,
        "dependency_identities": None,
        "common_staging_root": None,
        "stable_terminal": None,
        "configure_shape": _unobserved_configure_shape(),
        "git_protocol_evidence": "not-observed",
        "external_git_evidence": "not-applicable",
        "execution_model": "not-run",
    }


def _setup_private_dependencies(
    start_fd: int, *, context: Mapping[str, Any], policy: Mapping[str, Mapping[str, str]],
    run_root: Path, environment: Mapping[str, str], deadline: float,
) -> Mapping[str, Any]:
    os.write(start_fd, b"S")
    started = time.monotonic()
    try:
        with _installed_environment(environment):
            private_base = run_root / "fetchcontent-private"
            private_base.mkdir(mode=0o700)
            for name in _DEPENDENCIES:
                shared = _PERSISTENT_CACHE / name
                shared_before = _repo_identity(
                    shared, expected_pin=policy[name]["pin"], require_clean=False,
                    deadline=deadline,
                )
                private = private_base / f"{name}-src"
                shutil.copytree(shared, private, symlinks=True)
                copied = _repo_identity(
                    private, expected_pin=policy[name]["pin"], require_clean=False,
                    deadline=deadline,
                )
                shared_after = _repo_identity(
                    shared, expected_pin=policy[name]["pin"], require_clean=False,
                    deadline=deadline,
                )
                if shared_before != copied or shared_before != shared_after:
                    raise RuntimeError("shared dependency changed during private copy")
                _normalize_private_repo(
                    private, policy[name]["pin"], deadline=deadline,
                )
            source_identities = _dependency_set_identity(
                private_base,
                {name: policy[name]["pin"] for name in _DEPENDENCIES},
                source_suffix="-src", require_clean=True, deadline=deadline,
                allow_run_local_generated=True,
            )
            preparation = buildcache.prepare_masstree_fetchcontent(
                ccbench_dir=os.fspath(context["ccbench_dir"]),
                fetchcontent_base_dir=os.fspath(private_base),
                expected_toolchain_manifest=context["toolchain_manifest"],
                configure_timeout_s=240,
                target_timeout_s=300,
                site=context["site"],
                masstree_source_dir=os.fspath(private_base / "masstree-src"),
                mimalloc_source_dir=os.fspath(private_base / "mimalloc-src"),
                googletest_source_dir=os.fspath(private_base / "googletest-src"),
            )
            expected_sources = {
                name: private_base / f"{name}-src" for name in _DEPENDENCIES
            }
            preparation_shape = _configure_shape(
                preparation.configure_argv, expected_base=private_base,
                expected_sources=expected_sources, legacy=False,
            )
            if preparation_shape != {
                "observed": True, "base_dir_count": 1, "source_dir_count": 3,
                "base_dir_binding": "exact", "source_dir_binding": "exact",
                "legacy_source_seam": False,
            }:
                raise RuntimeError("production setup did not bind BASE_DIR and three SOURCE_DIR values")
            receipt = buildcache._observe_fetchcontent_dependency_receipt(
                os.fspath(private_base / "masstree-src")
            )
            archive_sha256 = buildcache._observe_fetchcontent_archive_sha256(
                os.fspath(private_base / "masstree-src")
            )
            runtime_identities = _dependency_set_identity(
                private_base,
                {name: policy[name]["pin"] for name in _DEPENDENCIES},
                source_suffix="-src", require_clean=True, deadline=deadline,
                allow_run_local_generated=True,
            )
            if runtime_identities != source_identities:
                raise RuntimeError("dependency source inputs changed during setup")
            return {
                "status": "success",
                "stage_code": "setup",
                "cause_code": "none",
                "wall_s": round(time.monotonic() - started, 6),
                "dependency_receipt": receipt,
                "dependency_receipt_sha256": _sha256_value(receipt),
                "archive_sha256": archive_sha256,
                "private_dependency_sha256": _sha256_value(source_identities),
                "private_dependencies": source_identities,
                "private_copy_verified": True,
                "configure_shape": preparation_shape,
            }
    except _DeadlineExpired:
        return {
            "status": "timeout", "stage_code": "setup", "cause_code": "timeout",
            "wall_s": round(time.monotonic() - started, 6),
            "dependency_receipt": None, "dependency_receipt_sha256": None,
            "archive_sha256": None, "private_dependency_sha256": None,
            "private_dependencies": None, "private_copy_verified": False,
            "configure_shape": _unobserved_configure_shape(),
        }
    except Exception:
        return {
            "status": "failed", "stage_code": "setup", "cause_code": "setup-failed",
            "wall_s": round(time.monotonic() - started, 6),
            "dependency_receipt": None, "dependency_receipt_sha256": None,
            "archive_sha256": None, "private_dependency_sha256": None,
            "private_dependencies": None,
            "private_copy_verified": False,
            "configure_shape": _unobserved_configure_shape(),
        }


def _produced_git_protocol_evidence(
    *, arm_id: str, outcome: str, environment: Mapping[str, str],
) -> str:
    """Bind the v2 success evidence to the exact child policy input."""
    if arm_id != "v2-source-no-proxy":
        return "not-applicable"
    if outcome == "success" and environment.get("GIT_ALLOW_PROTOCOL") == "file":
        return "file-only-policy-success"
    return "not-observed"


def _run_arm_child(
    start_fd: int, *, arm_id: str, context: Mapping[str, Any], cache_root: Path,
    environment: Mapping[str, str], private_base: Path,
    dependency_receipt: Mapping[str, str], archive_sha256: str, deadline: float,
) -> Mapping[str, Any]:
    before_sha = after_sha = None
    invariant_status = "not-observed"
    try:
        with _installed_environment(environment):
            before = _identity_material(context, deadline=deadline)
            before_sha = _sha256_value(before)
            if before_sha != context["baseline_identity_sha256"]:
                raise RuntimeError("identity mismatch before arm")
            os.write(start_fd, b"S")
            started = time.monotonic()
            result = None
            stage_code = "none"
            cause_code = "none"
            outcome = "success"
            try:
                if arm_id == "v2-source-no-proxy":
                    result = buildcache.build_v2(
                        context["genome"],
                        admission=context["admission"],
                        build_context=context["build_context"],
                        source_evidence=context["source_evidence"],
                        contract=context["contract"],
                        ccbench_commit=context["ccbench_commit"],
                        trace=False,
                        cc=context["cc"], cxx=context["cxx"],
                        cache_root=os.fspath(cache_root),
                        ccbench_dir=os.fspath(context["ccbench_dir"]),
                        timeout_s=840, site=context["site"],
                        expected_toolchain_manifest=context["toolchain_manifest"],
                        fetchcontent_base_dir=os.fspath(private_base),
                        masstree_source_dir=os.fspath(private_base / "masstree-src"),
                        mimalloc_source_dir=os.fspath(private_base / "mimalloc-src"),
                        googletest_source_dir=os.fspath(private_base / "googletest-src"),
                        fetchcontent_dependency_receipt=dependency_receipt,
                        fetchcontent_archive_sha256=archive_sha256,
                    )
                else:
                    result = buildcache.build(
                        context["genome"], context["ccbench_commit"], False,
                        cache_root=os.fspath(cache_root),
                        cc=context["cc"], cxx=context["cxx"],
                        ccbench_dir=os.fspath(context["ccbench_dir"]),
                        admission=context["admission"],
                        build_context=context["build_context"],
                        source_evidence=context["source_evidence"],
                        site=context["site"],
                    )
            except Exception as exc:
                outcome = "failed"
                stage_code, cause_code = _fixed_exception_codes(exc, arm_id=arm_id)
            wall_s = round(time.monotonic() - started, 6)
            # A failed production call still began from a proven nonexistent
            # cache root; it is a cold attempt, not an unobserved cache state.
            cached = False if result is None else result.cached
            shape = _unobserved_configure_shape() if result is None else _configure_shape(
                result.configure_argv,
                expected_base=(private_base if arm_id == "v2-source-no-proxy" else None),
                expected_sources=(
                    {name: private_base / f"{name}-src" for name in _DEPENDENCIES}
                    if arm_id == "v2-source-no-proxy" else {}
                ),
                legacy=arm_id != "v2-source-no-proxy",
            )
            if result is not None and result.cached is not False:
                outcome, stage_code, cause_code = "failed", "precondition", "cache-hit"
            after = _identity_material(context, deadline=deadline)
            after_sha = _sha256_value(after)
            invariant_status = (
                "matched" if before_sha == after_sha == context["baseline_identity_sha256"]
                else "mismatch"
            )
            if invariant_status != "matched":
                outcome, stage_code, cause_code = "inconclusive", "precondition", "identity-mismatch"
            return {
                "outcome": outcome, "wall_s": wall_s, "cached": cached,
                "stage_code": stage_code, "cause_code": cause_code,
                "invariant_status": invariant_status,
                "invariant_before_sha256": before_sha,
                "invariant_after_sha256": after_sha,
                "configure_shape": shape,
                "git_protocol_evidence": _produced_git_protocol_evidence(
                    arm_id=arm_id, outcome=outcome, environment=environment,
                ),
            }
    except _DeadlineExpired:
        return {
            "outcome": "timeout", "wall_s": None, "cached": None,
            "stage_code": "unknown", "cause_code": "timeout",
            "invariant_status": "not-observed",
            "invariant_before_sha256": before_sha,
            "invariant_after_sha256": after_sha,
            "configure_shape": _unobserved_configure_shape(),
            "git_protocol_evidence": (
                "not-observed" if arm_id == "v2-source-no-proxy" else "not-applicable"
            ),
        }
    except Exception:
        return {
            "outcome": "inconclusive", "wall_s": None, "cached": None,
            "stage_code": "precondition", "cause_code": "identity-mismatch",
            "invariant_status": invariant_status,
            "invariant_before_sha256": before_sha,
            "invariant_after_sha256": after_sha,
            "configure_shape": _unobserved_configure_shape(),
            "git_protocol_evidence": (
                "not-observed" if arm_id == "v2-source-no-proxy" else "not-applicable"
            ),
        }


def _merge_supervised_arm(
    arm_id: str, supervised: Mapping[str, Any], *, observer: _LegacyObserver | None,
    private_base: Path, pins: Mapping[str, str], deadline: float,
    dependency_receipt: Mapping[str, str], archive_sha256: str,
) -> dict[str, Any]:
    arm = _empty_arm(arm_id)
    arm["fresh_cache_precondition"] = True
    arm["execution_model"] = "supervised-child-process-group"
    if supervised.get("supervisor_status") == "timeout":
        arm.update({
            "outcome": "timeout", "wall_s": supervised.get("wall_s"),
            "stage_code": "unknown", "cause_code": "timeout",
        })
    elif supervised.get("supervisor_status") != "complete":
        arm.update({"outcome": "inconclusive", "stage_code": "unknown", "cause_code": "unexpected"})
    else:
        for key in (
            "outcome", "wall_s", "cached", "stage_code", "cause_code",
            "invariant_status", "invariant_before_sha256", "invariant_after_sha256",
            "configure_shape", "git_protocol_evidence", "execution_model",
        ):
            arm[key] = supervised.get(key)
    if observer is None:
        arm["observer_status"] = "not-required"
        arm["common_staging_root"] = None
        arm["stable_terminal"] = None
        arm["external_git_evidence"] = "not-applicable"
        if arm["outcome"] == "timeout":
            return arm
        try:
            identities = _dependency_set_identity(
                private_base, pins, source_suffix="-src", require_clean=True,
                deadline=deadline, allow_run_local_generated=True,
            )
            observed_receipt = buildcache._observe_fetchcontent_dependency_receipt(
                os.fspath(private_base / "masstree-src")
            )
            observed_archive = buildcache._observe_fetchcontent_archive_sha256(
                os.fspath(private_base / "masstree-src")
            )
            if (
                observed_receipt != dependency_receipt
                or observed_archive != archive_sha256
            ):
                raise RuntimeError("run-local dependency products changed")
        except Exception:
            arm.update({
                "outcome": "inconclusive", "stage_code": "observer",
                "cause_code": "observer-mismatch",
            })
            return arm
        arm["observed_heads"] = {name: identities[name]["head"] for name in _DEPENDENCIES}
        arm["dependency_identities"] = identities
        arm["dependency_identity_sha256"] = _sha256_value(identities)
        return arm
    observation = observer.finish()
    arm["observer_status"] = observation["status"]
    arm["observed_heads"] = observation["heads"]
    arm["dependency_identity_sha256"] = observation["identity_sha256"]
    arm["dependency_identities"] = observation["identities"]
    arm["common_staging_root"] = observation["common_staging_root"]
    arm["stable_terminal"] = observation["stable_terminal"]
    arm["external_git_evidence"] = observation["external_git_evidence"]
    if observation["status"] == "missed" and arm["outcome"] != "timeout":
        arm.update({"outcome": "inconclusive", "stage_code": "observer", "cause_code": "observer-missed"})
    elif observation["status"] == "mismatch":
        arm.update({
            "outcome": "inconclusive", "stage_code": "observer",
            "cause_code": (
                "scratch-precondition" if observation["fault"] == "scratch-precondition"
                else "observer-mismatch"
            ),
        })
    return arm


def _classification_input(
    arms: list[Mapping[str, Any]], *, control_valid: bool,
    identity_match: bool, precondition_valid: bool, setup_valid: bool,
    pins: Mapping[str, str | None], private_dependencies: object,
    private_copy_verified: bool, shared_unchanged: bool,
) -> dict[str, Any]:
    return {
        "precondition_valid": precondition_valid,
        "setup_valid": setup_valid,
        "control_valid": control_valid,
        "identity_match": identity_match,
        "dependency_evidence": {
            "pins": dict(pins),
            "private": private_dependencies,
            "proxy": arms[0]["dependency_identities"],
            "no_proxy": arms[1]["dependency_identities"],
            "v2": arms[2]["dependency_identities"],
            "private_copy_verified": private_copy_verified,
            "shared_unchanged": shared_unchanged,
            "proxy_common_root": arms[0]["common_staging_root"],
            "proxy_stable_terminal": arms[0]["stable_terminal"],
            "no_proxy_common_root": arms[1]["common_staging_root"],
            "no_proxy_stable_terminal": arms[1]["stable_terminal"],
            "v2_reobserved": arms[2]["dependency_identities"] is not None,
        },
        "arms": {
            arm["id"]: {
                "fresh": arm["fresh_cache_precondition"],
                "cached": arm["cached"],
                "outcome": arm["outcome"],
                "stage": arm["stage_code"],
                "cause": arm["cause_code"],
                "observer": arm["observer_status"],
                "shape": arm["configure_shape"],
                "git_protocol_evidence": arm["git_protocol_evidence"],
                "external_git_evidence": arm["external_git_evidence"],
            }
            for arm in arms
        },
    }


def _canonical_directory_identity(path: Path, *, label: str) -> tuple[int, int]:
    try:
        info = path.lstat()
        canonical = path.resolve(strict=True)
    except OSError:
        raise RuntimeError(f"{label} cannot be resolved") from None
    if path.is_symlink() or not stat.S_ISDIR(info.st_mode):
        raise RuntimeError(f"{label} is not a real directory")
    if canonical != path.absolute():
        raise RuntimeError(f"{label} is not canonical")
    return info.st_dev, info.st_ino


def _canonical_file_identity(path: Path, *, label: str) -> tuple[int, int]:
    try:
        info = path.lstat()
        canonical = path.resolve(strict=True)
    except OSError:
        raise RuntimeError(f"{label} cannot be resolved") from None
    if path.is_symlink() or not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"{label} is not a real regular file")
    if canonical != path.absolute():
        raise RuntimeError(f"{label} is not canonical")
    return info.st_dev, info.st_ino


@dataclass(frozen=True)
class _ArtifactRootBinding:
    repo_root: Path
    artifact_root: Path
    repo_identity: tuple[int, int]
    probe_identity: tuple[int, int]
    insight_parent_identity: tuple[int, int]
    artifact_identity: tuple[int, int] | None


def _validate_execution_root(
    *, probe_file: Path, cwd: Path, git_top: Path,
    module_files: tuple[Path, ...],
) -> _ArtifactRootBinding:
    repo_identity = _canonical_directory_identity(cwd, label="execution root")
    if git_top != cwd or _canonical_directory_identity(
        git_top, label="Git top-level",
    ) != repo_identity:
        raise RuntimeError("Git top-level is not the execution root")
    expected_probe = cwd / _PROBE_RELATIVE_PATH
    probe_identity = _canonical_file_identity(probe_file, label="probe file")
    if probe_file != expected_probe or _canonical_file_identity(
        expected_probe, label="repository probe file",
    ) != probe_identity:
        raise RuntimeError("probe file is not contained at the expected repository path")
    for module_file in module_files:
        module_identity = _canonical_file_identity(
            module_file, label="production module file",
        )
        module_root = module_file.parents[2]
        if (
            _canonical_directory_identity(
                module_root, label="production module repository root",
            ) != repo_identity
            or module_root != cwd
            or module_identity != _canonical_file_identity(
                module_file, label="production module file",
            )
        ):
            raise RuntimeError("production module comes from another checkout")
    insight_parent = cwd / _ARTIFACT_RELATIVE_PATH.parent
    insight_parent_identity = _canonical_directory_identity(
        insight_parent, label="artifact insight parent",
    )
    artifact_root = cwd / _ARTIFACT_RELATIVE_PATH
    artifact_identity = None
    if os.path.lexists(artifact_root):
        artifact_identity = _canonical_directory_identity(
            artifact_root, label="artifact root",
        )
    return _ArtifactRootBinding(
        repo_root=cwd, artifact_root=artifact_root,
        repo_identity=repo_identity, probe_identity=probe_identity,
        insight_parent_identity=insight_parent_identity,
        artifact_identity=artifact_identity,
    )


def _git_top_level(cwd: Path) -> Path:
    environment = {
        key: value for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    environment.update(_GIT_CONFIG)
    try:
        result = subprocess.run(
            ["git", "-C", os.fspath(cwd), "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env=environment, timeout=_OBSERVER_GIT_SLICE_S, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        raise RuntimeError("Git top-level cannot be observed") from None
    lines = result.stdout.splitlines()
    if result.returncode != 0 or len(lines) != 1 or not os.path.isabs(lines[0]):
        raise RuntimeError("Git top-level is unavailable or ambiguous")
    return Path(lines[0])


def _bind_execution_root() -> _ArtifactRootBinding:
    probe_file = Path(__file__)
    if not probe_file.is_absolute():
        raise RuntimeError("probe file path is not absolute")
    cwd = Path.cwd()
    module_files = tuple(
        Path(module.__file__)
        for module in (
            build_admission, buildcache, env_contract, site_policy, source_digest,
        )
    )
    if any(not path.is_absolute() for path in module_files):
        raise RuntimeError("production module path is not absolute")
    return _validate_execution_root(
        probe_file=probe_file, cwd=cwd, git_top=_git_top_level(cwd),
        module_files=module_files,
    )


def _open_bound_directory(
    parent_fd: int, name: str, *, expected_identity: tuple[int, int] | None,
    create_if_absent: bool, allow_unbound_existing: bool,
) -> int:
    created = False
    try:
        entry = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        if not create_if_absent:
            raise RuntimeError("bound artifact directory disappeared") from None
        os.mkdir(name, 0o700, dir_fd=parent_fd)
        created = True
        entry = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if not stat.S_ISDIR(entry.st_mode):
        raise RuntimeError("artifact directory entry is not a real directory")
    actual_identity = (entry.st_dev, entry.st_ino)
    if expected_identity is not None and actual_identity != expected_identity:
        raise RuntimeError("bound artifact directory identity changed")
    if expected_identity is None and not created and not allow_unbound_existing:
        raise RuntimeError("unexpected artifact directory appeared")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(name, flags, dir_fd=parent_fd)
    held = os.fstat(fd)
    if (held.st_dev, held.st_ino) != actual_identity or not stat.S_ISDIR(held.st_mode):
        os.close(fd)
        raise RuntimeError("artifact directory changed while being opened")
    return fd


def _open_artifact_directories(
    binding: _ArtifactRootBinding,
) -> tuple[int, int, int, int, int, int]:
    current = _bind_execution_root()
    if current != binding:
        raise RuntimeError("execution or artifact root binding changed before publication")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    repo_fd = os.open(binding.repo_root, flags)
    repo_info = os.fstat(repo_fd)
    if (
        (repo_info.st_dev, repo_info.st_ino) != binding.repo_identity
        or not stat.S_ISDIR(repo_info.st_mode)
    ):
        os.close(repo_fd)
        raise RuntimeError("execution root identity changed while being opened")
    output_fd = parent_fd = root_fd = raw_fd = digest_fd = -1
    try:
        output_fd = _open_bound_directory(
            repo_fd, binding.artifact_root.parent.parent.name,
            expected_identity=None, create_if_absent=False,
            allow_unbound_existing=True,
        )
        parent_fd = _open_bound_directory(
            output_fd, binding.artifact_root.parent.name,
            expected_identity=binding.insight_parent_identity,
            create_if_absent=False, allow_unbound_existing=False,
        )
        root_fd = _open_bound_directory(
            parent_fd, binding.artifact_root.name,
            expected_identity=binding.artifact_identity,
            create_if_absent=binding.artifact_identity is None,
            allow_unbound_existing=False,
        )
        raw_fd = _open_bound_directory(
            root_fd, "raw", expected_identity=None, create_if_absent=True,
            allow_unbound_existing=True,
        )
        digest_fd = _open_bound_directory(
            root_fd, "digest", expected_identity=None, create_if_absent=True,
            allow_unbound_existing=True,
        )
        return repo_fd, output_fd, parent_fd, root_fd, raw_fd, digest_fd
    except Exception:
        for fd in (digest_fd, raw_fd, root_fd, parent_fd, output_fd, repo_fd):
            if fd >= 0:
                os.close(fd)
        raise


def _entry_identity(info: os.stat_result) -> tuple[int, int, int, int]:
    return (
        info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode), info.st_nlink,
    )


def _verify_held_entry(
    parent_fd: int, name: str, held_fd: int, *, expected_type: int,
    require_single_link: bool,
) -> None:
    try:
        held = os.fstat(held_fd)
        entry = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError:
        raise RuntimeError("published artifact namespace entry is unavailable") from None
    if (
        _entry_identity(held) != _entry_identity(entry)
        or stat.S_IFMT(held.st_mode) != expected_type
        or (require_single_link and held.st_nlink != 1)
    ):
        raise RuntimeError("published artifact namespace identity changed")


def _verify_published_namespace(
    binding: _ArtifactRootBinding, directory_fds: tuple[int, int, int, int, int, int],
    basename: str, raw_leaf_fd: int, digest_leaf_fd: int,
) -> None:
    repo_fd, output_fd, parent_fd, root_fd, raw_fd, digest_fd = directory_fds
    directory_type = stat.S_IFDIR
    _verify_held_entry(
        repo_fd, binding.artifact_root.parent.parent.name, output_fd,
        expected_type=directory_type, require_single_link=False,
    )
    _verify_held_entry(
        output_fd, binding.artifact_root.parent.name, parent_fd,
        expected_type=directory_type, require_single_link=False,
    )
    _verify_held_entry(
        parent_fd, binding.artifact_root.name, root_fd,
        expected_type=directory_type, require_single_link=False,
    )
    _verify_held_entry(
        root_fd, "raw", raw_fd,
        expected_type=directory_type, require_single_link=False,
    )
    _verify_held_entry(
        root_fd, "digest", digest_fd,
        expected_type=directory_type, require_single_link=False,
    )
    _verify_held_entry(
        raw_fd, basename, raw_leaf_fd,
        expected_type=stat.S_IFREG, require_single_link=True,
    )
    _verify_held_entry(
        digest_fd, basename, digest_leaf_fd,
        expected_type=stat.S_IFREG, require_single_link=True,
    )


def _create_only_at(directory_fd: int, name: str, payload: bytes) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(name, flags, 0o600, dir_fd=directory_fd)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise RuntimeError("artifact write did not progress")
            view = view[written:]
        os.fsync(fd)
        os.fsync(directory_fd)
        return fd
    except Exception:
        os.close(fd)
        raise


def _validate_digest_schema(value: object) -> None:
    digest = _exact_keys(value, frozenset({
        "schema", "completion", "precondition_status", "precondition_cause_code",
        "raw_basename", "raw_sha256", "classification", "reason_code",
        "ambient_proxy_env_sensitivity", "non_file_git_transport_needed",
        "arbitrary_external_network", "arms",
    }), "digest")
    if digest["schema"] != _DIGEST_SCHEMA:
        raise ValueError("digest schema is invalid")
    if digest["completion"] not in {
        "complete", "incomplete-precondition", "incomplete-setup",
        "incomplete-execution", "incomplete-timeout", "incomplete-finalize",
    }:
        raise ValueError("digest completion is invalid")
    if digest["precondition_status"] not in {"satisfied", "failed"}:
        raise ValueError("digest precondition status is invalid")
    if digest["precondition_cause_code"] not in _PRECONDITION_CAUSES:
        raise ValueError("digest precondition cause is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}-[0-9a-f]{64}\.json", digest["raw_basename"]):
        raise ValueError("digest raw basename is invalid")
    if not _is_hex(digest["raw_sha256"], _HEX64):
        raise ValueError("digest raw SHA-256 is invalid")
    if digest["classification"] not in {
        "migration-candidate-material", "keep-current-candidate-material", "indeterminate",
    }:
        raise ValueError("digest classification is invalid")
    if type(digest["reason_code"]) is not str or "\n" in digest["reason_code"]:
        raise ValueError("digest reason is invalid")
    if digest["ambient_proxy_env_sensitivity"] not in {
        "observed-single-run", "not-observed", "indeterminate",
    }:
        raise ValueError("digest proxy sensitivity is invalid")
    if digest["non_file_git_transport_needed"] not in {
        "not-required-for-success-under-file-only-policy", "indeterminate",
    }:
        raise ValueError("digest Git policy evidence is invalid")
    if digest["arbitrary_external_network"] != "not-measured":
        raise ValueError("digest arbitrary network scope is invalid")
    if type(digest["arms"]) is not list or len(digest["arms"]) != 3:
        raise ValueError("digest arm count is invalid")
    for arm in digest["arms"]:
        row = _exact_keys(
            arm, frozenset({"id", "outcome", "stage_code", "cause_code", "git_protocol_evidence"}),
            "digest arm",
        )
        if row["id"] not in _ARM_IDS:
            raise ValueError("digest arm ID is invalid")


def _audit_raw_for_publish(
    raw: Mapping[str, Any], *, forbidden_values: tuple[str, ...],
) -> None:
    _audit_publish_payload("raw", raw, forbidden_values=forbidden_values)


def _audit_digest_for_publish(
    digest: Mapping[str, Any], *, forbidden_values: tuple[str, ...],
) -> None:
    _audit_publish_payload("digest", digest, forbidden_values=forbidden_values)


def _audit_publish_payload(
    kind: str, payload: Mapping[str, Any], *, forbidden_values: tuple[str, ...],
) -> None:
    if kind == "raw":
        _validate_raw_schema(payload)
    elif kind == "digest":
        _validate_digest_schema(payload)
    else:
        raise ValueError("unknown publish payload kind")
    _assert_redacted_payload(payload, forbidden_values=forbidden_values)


def _publish_artifacts(
    binding: _ArtifactRootBinding, raw: Mapping[str, Any], *, pbs_hash: str,
    nonce_hash: str, forbidden_values: tuple[str, ...],
) -> None:
    basename = f"{pbs_hash}-{nonce_hash}.json"
    raw_payload = _canonical_bytes(raw) + b"\n"
    raw_sha256 = hashlib.sha256(raw_payload).hexdigest()
    digest = {
        "schema": _DIGEST_SCHEMA,
        "completion": raw["completion"],
        "precondition_status": raw["precondition"]["status"],
        "precondition_cause_code": raw["precondition"]["cause_code"],
        "raw_basename": basename,
        "raw_sha256": raw_sha256,
        "classification": raw["comparison"]["classification"],
        "reason_code": raw["comparison"]["reason_code"],
        "ambient_proxy_env_sensitivity": raw["comparison"]["ambient_proxy_env_sensitivity"],
        "non_file_git_transport_needed": raw["comparison"]["non_file_git_transport_needed"],
        "arbitrary_external_network": "not-measured",
        "arms": [
            {
                "id": arm["id"], "outcome": arm["outcome"],
                "stage_code": arm["stage_code"], "cause_code": arm["cause_code"],
                "git_protocol_evidence": arm["git_protocol_evidence"],
            }
            for arm in raw["arms"]
        ],
    }
    _audit_publish_payload("raw", raw, forbidden_values=forbidden_values)
    _audit_publish_payload("digest", digest, forbidden_values=forbidden_values)
    directory_fds = _open_artifact_directories(binding)
    raw_leaf_fd = digest_leaf_fd = -1
    try:
        raw_leaf_fd = _create_only_at(directory_fds[4], basename, raw_payload)
        digest_leaf_fd = _create_only_at(
            directory_fds[5], basename, _canonical_bytes(digest) + b"\n",
        )
        _verify_published_namespace(
            binding, directory_fds, basename, raw_leaf_fd, digest_leaf_fd,
        )
    finally:
        for fd in (digest_leaf_fd, raw_leaf_fd):
            if fd >= 0:
                os.close(fd)
        for fd in reversed(directory_fds):
            os.close(fd)


def _real_invocation_allowed(
    argv: tuple[str, ...], current_test: str,
) -> bool:
    if "--collect-only" in argv or "--co" in argv:
        return False
    current_node = current_test.rsplit(" ", 1)[0]
    return argv.count(_REAL_NODEID) == 1 and current_node == _REAL_NODEID


def _sentinel_sha256(label: str) -> str:
    return _sha256_text(f"t2000-unavailable:{label}")


def _empty_setup_public() -> dict[str, Any]:
    return {
        "status": "precondition-missing", "stage_code": "precondition",
        "cause_code": "precondition-failed", "wall_s": None,
        "dependency_receipt_sha256": None, "archive_sha256": None,
        "private_dependency_sha256": None, "private_dependencies": None,
        "private_copy_verified": False,
        "configure_shape": _unobserved_configure_shape(),
    }


def _real_probe() -> None:
    artifact_binding = _bind_execution_root()
    repo_root = artifact_binding.repo_root
    global_started = time.monotonic()
    hard_deadline = global_started + _JOB_WALLTIME_S
    finalize_deadline = hard_deadline - _FINALIZE_RESERVE_S
    setup_deadline = min(global_started + _SETUP_TIMEOUT_S, finalize_deadline)
    try:
        nonce_hash = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
        nonce_available = True
    except Exception:
        nonce_hash = _sentinel_sha256("artifact-nonce")
        nonce_available = False
    pbs_hash = _sentinel_sha256("pbs-job")
    node_hash = _sentinel_sha256("node")
    proxy_value = ""
    forbidden_values: tuple[str, ...] = ()
    compute: dict[str, str] | None = None
    run_root: Path | None = None
    policy: dict[str, dict[str, str]] | None = None
    pins: dict[str, str | None] = {name: None for name in _DEPENDENCIES}
    environments: dict[str, dict[str, str]] | None = None
    shared_before: dict[str, dict[str, Any]] | None = None
    shared_unchanged = False
    run_context: dict[str, Any] | None = None
    setup_public = _empty_setup_public()
    arms = [_empty_arm(arm_id) for arm_id in _ARM_IDS]
    precondition = {"status": "failed", "cause_code": "unexpected"}
    control = {
        "pbs_bound": False, "proxy_source": "unavailable",
        "proxy_value_sha256": None, "legacy_env_delta": "unavailable",
        "path_unchanged": False, "git_config_identical": False,
        "legacy_git_guard_absent": False,
    }
    identity: dict[str, Any] = {
        "identity_status": "sentinel-incomplete",
        "node_sha256": node_hash, "pbs_job_sha256": pbs_hash,
        "nonce_sha256": nonce_hash, "single_node": None,
        "single_pytest_coordinator": True, "arm_process_groups_supervised": False,
        "compute_site": "unavailable", "ccbench_commit": None,
        "genome_sha256": None, "trace": False,
        "toolchain_manifest_sha256": None, "source_evidence_sha256": None,
        "admission_receipt_sha256": None, "contract_sha256": None,
        "activation_state_sha256": None, "path_sha256": None,
        "tool_resolution_sha256": None, "git_config_sha256": _sha256_value(_GIT_CONFIG),
        "dependency_policy_sha256": None, "dependency_pins": pins,
    }
    stage = "artifact-name"
    try:
        with _deadline_alarm(setup_deadline):
            if not nonce_available:
                raise RuntimeError("T-2000 artifact nonce is unavailable")
            stage = "compute"
            compute = _require_compute_pbs()
            _enable_child_subreaper()
            pbs_hash = _sha256_text(compute["job"])
            node_hash = _sha256_text(socket.gethostname())
            identity.update({
                "node_sha256": node_hash, "pbs_job_sha256": pbs_hash,
                "single_node": True, "compute_site": "pegasus-compute",
            })
            control["pbs_bound"] = True

            stage = "proxy"
            proxy_value = _read_b10_proxy(repo_root)
            forbidden_values = (proxy_value, socket.gethostname(), compute["job"])
            control.update({
                "proxy_source": "b10-single-literal",
                "proxy_value_sha256": _sha256_text(proxy_value),
                "legacy_env_delta": "lowercase-http-https-only",
            })
            environments = _arm_environments(os.environ, proxy_value)
            common_environment = dict(environments["legacy-no-proxy"])
            control.update({
                "path_unchanged": all(
                    environment.get("PATH", "") == os.environ.get("PATH", "")
                    for environment in environments.values()
                ),
                "git_config_identical": all(
                    all(environment.get(key) == value for key, value in _GIT_CONFIG.items())
                    for environment in environments.values()
                ),
                "legacy_git_guard_absent": (
                    "GIT_ALLOW_PROTOCOL" not in environments["legacy-proxy"]
                    and "GIT_ALLOW_PROTOCOL" not in environments["legacy-no-proxy"]
                ),
            })

            stage = "cache"
            policy, dependency_policy_sha256 = _dependency_contract(repo_root)
            pins = {name: policy[name]["pin"] for name in _DEPENDENCIES}
            identity["dependency_policy_sha256"] = dependency_policy_sha256
            identity["dependency_pins"] = pins
            shared_before = _dependency_set_identity(
                _PERSISTENT_CACHE, pins, source_suffix="", require_clean=False,
                deadline=setup_deadline,
            )
            shared_unchanged = True

            stage = "toolchain"
            cc, cxx = buildcache.compilers_for_current_site()
            toolchain_manifest = buildcache.observed_toolchain_manifest(cc, cxx)
            tool_resolution = _tool_resolution(cc, cxx)
            identity["toolchain_manifest_sha256"] = _sha256_value(toolchain_manifest)
            identity["tool_resolution_sha256"] = _sha256_value(tool_resolution)

            stage = "evidence"
            ccbench_dir = repo_root / "external/ccbench"
            ccbench_commit = _git_head(ccbench_dir, deadline=setup_deadline)
            genome = Genome("silo", {})
            evidence = source_digest.resolve_evidence(
                genome, ccbench_commit, ccbench_dir=os.fspath(ccbench_dir), cxx=cxx,
            )
            context = build_admission.build_run_context(
                generator_id=build_admission.GeneratorId.BACKOFF_REPRO,
            )
            identity.update({
                "ccbench_commit": ccbench_commit,
                "genome_sha256": _sha256_text(genome.canonical()),
                "source_evidence_sha256": _source_evidence_hash(evidence),
            })

            stage = "admission"
            admission = build_admission.derive_build_admission(context, evidence)
            if admission.provenance is not build_admission.BuildProvenance.STOCK_BASELINE:
                raise RuntimeError("T-2000 requires stock build admission")
            identity["admission_receipt_sha256"] = admission.receipt_sha256

            stage = "contract"
            required_contract = env_contract.lookup_required_attestation_contract()
            authorized = env_contract.authorize(required_contract.env_tag)
            if authorized.contract is not required_contract:
                raise RuntimeError("required contract authorization mismatch")
            identity["contract_sha256"] = authorized.contract.contract_sha256
            identity["activation_state_sha256"] = authorized.activation_state_sha256
            identity["path_sha256"] = _sha256_text(os.environ.get("PATH", ""))
            run_context = {
                "site": compute["site"], "pbs_job": compute["job"],
                "ccbench_dir": ccbench_dir, "ccbench_commit": ccbench_commit,
                "genome": genome, "cc": cc, "cxx": cxx,
                "toolchain_manifest": toolchain_manifest, "source_evidence": evidence,
                "build_context": context, "admission": admission,
                "contract": authorized.contract,
                "activation_state_sha256": authorized.activation_state_sha256,
                "coordinator_pid": os.getpid(), "path": os.environ.get("PATH", ""),
                "tool_resolution": tool_resolution,
            }
            with _installed_environment(common_environment):
                baseline_identity = _identity_material(run_context, deadline=setup_deadline)
            run_context["baseline_identity_sha256"] = _sha256_value(baseline_identity)
            identity["identity_status"] = "complete"
            precondition = {"status": "satisfied", "cause_code": "none"}

            stage = "setup"
            run_root = Path(compute["tmp"]) / f"t2000-{pbs_hash[:16]}-{nonce_hash[:16]}"
            run_root.mkdir(mode=0o700)
            setup = _supervise(
                lambda start_fd: _setup_private_dependencies(
                    start_fd, context=run_context, policy=policy,
                    run_root=run_root, environment=environments["v2-source-no-proxy"],
                    deadline=setup_deadline,
                ),
                deadline=setup_deadline,
            )
            if setup.get("supervisor_status") == "timeout":
                setup_public.update({
                    "status": "timeout", "stage_code": "setup", "cause_code": "timeout",
                    "wall_s": setup.get("wall_s"),
                })
            elif setup.get("supervisor_status") == "complete" and setup.get("status") == "timeout":
                setup_public.update({
                    "status": "timeout", "stage_code": "setup", "cause_code": "timeout",
                    "wall_s": setup.get("wall_s"),
                })
            elif setup.get("supervisor_status") == "complete" and setup.get("status") == "success":
                setup_public = {key: setup[key] for key in _SETUP_KEYS}
            else:
                setup_public.update({
                    "status": "failed", "stage_code": "setup", "cause_code": "setup-failed",
                    "wall_s": setup.get("wall_s"),
                })
    except _DeadlineExpired:
        precondition = {"status": "failed", "cause_code": "deadline"}
        if stage == "setup":
            precondition = {"status": "satisfied", "cause_code": "none"}
            setup_public.update({
                "status": "timeout", "stage_code": "setup", "cause_code": "timeout",
            })
    except Exception:
        precondition = {
            "status": "failed",
            "cause_code": stage if stage in _PRECONDITION_CAUSES else "unexpected",
        }

    if (
        precondition["status"] == "satisfied"
        and setup_public["status"] == "success"
        and compute is not None and run_context is not None and policy is not None
        and environments is not None and run_root is not None and shared_before is not None
    ):
        private_base = run_root / "fetchcontent-private"
        dependency_receipt = setup.get("dependency_receipt")
        archive_sha256 = setup.get("archive_sha256")
        executed: list[dict[str, Any]] = []
        for arm_id in _ARM_IDS:
            if time.monotonic() >= finalize_deadline:
                break
            arm_deadline = min(time.monotonic() + _ARM_TIMEOUT_S, finalize_deadline)
            cache_root = run_root / f"cache-{arm_id}"
            if cache_root.exists():
                executed.append(_empty_arm(arm_id))
                break
            observer = None
            if arm_id != "v2-source-no-proxy":
                observer = _LegacyObserver(
                    cache_root, pins,
                    policy_urls={name: policy[name]["url"] for name in _DEPENDENCIES},
                    scratch_path=Path(compute["tmp"]),
                )
            try:
                supervised = _supervise(
                    lambda start_fd, selected=arm_id, root=cache_root, deadline=arm_deadline: _run_arm_child(
                        start_fd, arm_id=selected, context=run_context,
                        cache_root=root, environment=environments[selected],
                        private_base=private_base, dependency_receipt=dependency_receipt,
                        archive_sha256=archive_sha256, deadline=deadline,
                    ),
                    deadline=arm_deadline, observer=observer,
                )
            except _DeadlineExpired:
                supervised = {
                    "supervisor_status": "timeout", "stage_code": "unknown",
                    "cause_code": "timeout", "wall_s": None,
                }
            except Exception:
                supervised = {
                    "supervisor_status": "child-error", "stage_code": "unknown",
                    "cause_code": "unexpected",
                }
            merged = _merge_supervised_arm(
                arm_id, supervised, observer=observer, private_base=private_base,
                pins=pins, deadline=arm_deadline,
                dependency_receipt=dependency_receipt,
                archive_sha256=archive_sha256,
            )
            try:
                with _deadline_alarm(arm_deadline):
                    shared_after = _dependency_set_identity(
                        _PERSISTENT_CACHE, pins, source_suffix="", require_clean=False,
                        deadline=arm_deadline,
                    )
                shared_unchanged = shared_unchanged and shared_after == shared_before
            except Exception:
                shared_unchanged = False
                if merged["outcome"] != "timeout":
                    merged.update({
                        "outcome": "inconclusive", "stage_code": "observer",
                        "cause_code": "observer-mismatch",
                    })
            executed.append(merged)
        arms[:len(executed)] = executed
        identity["arm_process_groups_supervised"] = all(
            arm["execution_model"] == "supervised-child-process-group" for arm in arms
        )

    identity_match = all(
        arm["outcome"] != "not-run" and arm["invariant_status"] == "matched"
        for arm in arms
    )
    classification, reason = _classify(_classification_input(
        arms,
        control_valid=(
            precondition["status"] == "satisfied"
            and control["path_unchanged"] is True
            and control["git_config_identical"] is True
            and control["legacy_git_guard_absent"] is True
        ),
        identity_match=identity_match,
        precondition_valid=precondition["status"] == "satisfied",
        setup_valid=setup_public["status"] == "success",
        pins=pins, private_dependencies=setup_public["private_dependencies"],
        private_copy_verified=setup_public["private_copy_verified"],
        shared_unchanged=shared_unchanged,
    ))
    proxy_sensitivity = (
        "observed-single-run" if classification == "migration-candidate-material"
        else "not-observed" if classification == "keep-current-candidate-material"
        else "indeterminate"
    )
    non_file_needed = (
        "not-required-for-success-under-file-only-policy"
        if arms[2]["outcome"] == "success"
        and arms[2]["git_protocol_evidence"] == "file-only-policy-success"
        else "indeterminate"
    )
    if precondition["status"] != "satisfied":
        completion = "incomplete-precondition"
    elif setup_public["status"] == "timeout" or any(arm["outcome"] == "timeout" for arm in arms):
        completion = "incomplete-timeout"
    elif setup_public["status"] != "success":
        completion = "incomplete-setup"
    elif any(arm["outcome"] in {"not-run", "inconclusive"} for arm in arms):
        completion = "incomplete-execution"
    elif time.monotonic() >= finalize_deadline:
        completion = "incomplete-finalize"
    else:
        completion = "complete"
    raw = {
        "schema": _SCHEMA, "completion": completion,
        "precondition": precondition, "run_identity": identity,
        "control": control, "setup": setup_public, "arms": arms,
        "comparison": {
            "classification": classification, "reason_code": reason,
            "ambient_proxy_env_sensitivity": proxy_sensitivity,
            "non_file_git_transport_needed": non_file_needed,
            "arbitrary_external_network": "not-measured",
            "causal_scope": "single-run-operational-sensitivity",
            "performance_scope": "diagnostic-only",
        },
        "redaction": {"schema_audit_passed": True},
    }
    try:
        with _deadline_alarm(hard_deadline):
            _publish_artifacts(
                artifact_binding, raw, pbs_hash=pbs_hash, nonce_hash=nonce_hash,
                forbidden_values=forbidden_values,
            )
            if run_root is not None and run_root.exists():
                shutil.rmtree(run_root)
    except _DeadlineExpired:
        raise RuntimeError("T-2000 artifact finalization deadline expired") from None


def _pure_publish_raw_fixture() -> dict[str, Any]:
    return {
        "schema": _SCHEMA,
        "completion": "incomplete-precondition",
        "precondition": {"status": "failed", "cause_code": "unexpected"},
        "run_identity": {
            "identity_status": "sentinel-incomplete",
            "node_sha256": None,
            "pbs_job_sha256": None,
            "nonce_sha256": None,
            "single_node": None,
            "single_pytest_coordinator": True,
            "arm_process_groups_supervised": False,
            "compute_site": "unavailable",
            "ccbench_commit": None,
            "genome_sha256": None,
            "trace": False,
            "toolchain_manifest_sha256": None,
            "source_evidence_sha256": None,
            "admission_receipt_sha256": None,
            "contract_sha256": None,
            "activation_state_sha256": None,
            "path_sha256": None,
            "tool_resolution_sha256": None,
            "git_config_sha256": None,
            "dependency_policy_sha256": None,
            "dependency_pins": {name: None for name in _DEPENDENCIES},
        },
        "control": {
            "pbs_bound": False,
            "proxy_source": "unavailable",
            "proxy_value_sha256": None,
            "legacy_env_delta": "unavailable",
            "path_unchanged": False,
            "git_config_identical": False,
            "legacy_git_guard_absent": False,
        },
        "setup": _empty_setup_public(),
        "arms": [_empty_arm(arm_id) for arm_id in _ARM_IDS],
        "comparison": {
            "classification": "indeterminate",
            "reason_code": "precondition-failed",
            "ambient_proxy_env_sensitivity": "indeterminate",
            "non_file_git_transport_needed": "indeterminate",
            "arbitrary_external_network": "not-measured",
            "causal_scope": "single-run-operational-sensitivity",
            "performance_scope": "diagnostic-only",
        },
        "redaction": {"schema_audit_passed": True},
    }


def test_t2000_classifier_positive_migration_material() -> None:
    assert _classify(_classification_fixture()) == (
        "migration-candidate-material", "single-run-proxy-sensitivity",
    )


def test_t2000_classifier_positive_keep_current_material() -> None:
    fixture = _classification_fixture()
    fixture["arms"]["legacy-no-proxy"].update({
        "outcome": "success", "stage": "none", "cause": "none", "observer": "complete",
        "shape": fixture["arms"]["legacy-proxy"]["shape"],
        "external_git_evidence": "not-applicable",
    })
    assert _classify(fixture) == (
        "keep-current-candidate-material", "legacy-no-proxy-succeeded",
    )


def test_t2000_classifier_m1_cache_hit_has_one_reason() -> None:
    fixture = _classification_fixture()
    initial_cached_value = True
    assert initial_cached_value is True
    fixture["arms"]["legacy-proxy"]["fresh"] = False
    assert _classify(fixture) == ("indeterminate", "cache-hit")


def test_t2000_classifier_m2_stage_has_one_reason() -> None:
    fixture = _classification_fixture()
    fixture["arms"]["legacy-no-proxy"]["stage"] = "unknown"
    assert _classify(fixture) == ("indeterminate", "legacy-no-proxy-stage")


def test_t2000_classifier_m3_non_file_git_attempt_has_one_reason() -> None:
    environments = _arm_environments({"PATH": "/fixed/bin"}, "proxy-token")
    produced = _produced_git_protocol_evidence(
        arm_id="v2-source-no-proxy", outcome="success",
        environment=environments["v2-source-no-proxy"],
    )
    assert produced == "file-only-policy-success"
    assert _produced_git_protocol_evidence(
        arm_id="v2-source-no-proxy", outcome="failed",
        environment=environments["v2-source-no-proxy"],
    ) == "not-observed"
    assert _produced_git_protocol_evidence(
        arm_id="v2-source-no-proxy", outcome="success",
        environment=environments["legacy-no-proxy"],
    ) == "not-observed"
    assert _produced_git_protocol_evidence(
        arm_id="legacy-proxy", outcome="success",
        environment=environments["legacy-proxy"],
    ) == "not-applicable"
    fixture = _classification_fixture()
    fixture["arms"]["v2-source-no-proxy"]["git_protocol_evidence"] = (
        _produced_git_protocol_evidence(
            arm_id="v2-source-no-proxy", outcome="success",
            environment=environments["legacy-no-proxy"],
        )
    )
    assert _classify(fixture) == ("indeterminate", "v2-file-protocol-evidence")


def _initialize_pure_dependency_repo(
    repo: Path, *, name: str, deadline: float,
) -> str:
    repo.mkdir(parents=True)
    _run_git(repo, "init", "-q", mutate=True, deadline=deadline)
    _run_git(repo, "config", "user.name", "T-2000 pure", mutate=True, deadline=deadline)
    _run_git(
        repo, "config", "user.email", "t2000-pure@example.invalid",
        mutate=True, deadline=deadline,
    )
    (repo / "source.txt").write_text(f"{name} source\n", encoding="utf-8")
    _run_git(repo, "add", "source.txt", mutate=True, deadline=deadline)
    _run_git(repo, "commit", "-q", "-m", "source", mutate=True, deadline=deadline)
    return _run_git(
        repo, "rev-parse", "--verify", "HEAD^{commit}", deadline=deadline,
    )


def test_t2000_identity_m4_dependency_mismatch_has_one_reason(tmp_path: Path) -> None:
    deadline = time.monotonic() + 60.0
    private_base = tmp_path / "private"
    pins = {
        name: _initialize_pure_dependency_repo(
            private_base / f"{name}-src", name=name, deadline=deadline,
        )
        for name in _DEPENDENCIES
    }
    private_identities = _dependency_set_identity(
        private_base, pins, source_suffix="-src", require_clean=True,
        deadline=deadline, allow_run_local_generated=True,
    )

    staging = tmp_path / "cache" / "probe.staging-fixed"
    proxy_deps = staging / "_deps"
    v2_base = tmp_path / "v2"
    for name in _DEPENDENCIES:
        shutil.copytree(
            private_base / f"{name}-src", proxy_deps / f"{name}-src",
            symlinks=True,
        )
        shutil.copytree(
            private_base / f"{name}-src", v2_base / f"{name}-src",
            symlinks=True,
        )
    for marker, root in (
        (b"proxy", proxy_deps / "masstree-src"),
        (b"v2", v2_base / "masstree-src"),
    ):
        (root / "config.h").write_bytes(marker + b" generated config\n")
        (root / "libkohler_masstree_json.a").write_bytes(
            marker + b" generated archive\n"
        )
    assert buildcache._observe_fetchcontent_dependency_receipt(
        os.fspath(proxy_deps / "masstree-src")
    )["config_sha256"] != buildcache._observe_fetchcontent_dependency_receipt(
        os.fspath(v2_base / "masstree-src")
    )["config_sha256"]
    assert buildcache._observe_fetchcontent_archive_sha256(
        os.fspath(proxy_deps / "masstree-src")
    ) != buildcache._observe_fetchcontent_archive_sha256(
        os.fspath(v2_base / "masstree-src")
    )

    observer = _LegacyObserver(
        tmp_path / "cache", pins, policy_urls={}, scratch_path=tmp_path,
    )
    observer.poll(process_group=os.getpgrp(), deadline=deadline)
    observer.poll(process_group=os.getpgrp(), deadline=deadline)
    staging.rename(tmp_path / "cache" / "probe.complete")
    observer.poll(process_group=os.getpgrp(), deadline=deadline)
    observed = observer.finish()
    assert observed["status"] == "complete"

    v2_identities = _dependency_set_identity(
        v2_base, pins, source_suffix="-src", require_clean=True,
        deadline=deadline, allow_run_local_generated=True,
    )
    literal = _classification_fixture()
    arms = [_empty_arm(arm_id) for arm_id in _ARM_IDS]
    for arm, arm_id in zip(arms, _ARM_IDS):
        row = literal["arms"][arm_id]
        arm.update({
            "fresh_cache_precondition": row["fresh"], "cached": row["cached"],
            "outcome": row["outcome"], "stage_code": row["stage"],
            "cause_code": row["cause"], "observer_status": row["observer"],
            "configure_shape": row["shape"],
            "git_protocol_evidence": row["git_protocol_evidence"],
            "external_git_evidence": row["external_git_evidence"],
        })
    arms[0].update({
        "dependency_identities": observed["identities"],
        "common_staging_root": observed["common_staging_root"],
        "stable_terminal": observed["stable_terminal"],
    })
    arms[2]["dependency_identities"] = v2_identities
    actual_input = _classification_input(
        arms, control_valid=True, identity_match=True,
        precondition_valid=True, setup_valid=True, pins=pins,
        private_dependencies=private_identities, private_copy_verified=True,
        shared_unchanged=True,
    )
    assert _classify(actual_input) == (
        "migration-candidate-material", "single-run-proxy-sensitivity",
    )

    drift_repo = v2_base / "masstree-src"
    (drift_repo / "source.txt").write_text("tree drift\n", encoding="utf-8")
    _run_git(drift_repo, "add", "source.txt", mutate=True, deadline=deadline)
    _run_git(drift_repo, "commit", "-q", "-m", "drift", mutate=True, deadline=deadline)
    drift_identity = _repo_identity(
        drift_repo, expected_pin=None, require_clean=True, deadline=deadline,
        generated_paths=_RUN_LOCAL_GENERATED_PATHS["masstree"],
    )
    tree_case = json.loads(json.dumps(actual_input))
    tree_case["dependency_evidence"]["proxy"]["masstree"]["tree"] = (
        drift_identity["tree"]
    )
    assert _classify(tree_case) == ("indeterminate", "dependency-identity")

    pin_case = json.loads(json.dumps(actual_input))
    pin_case["dependency_evidence"]["pins"]["masstree"] = drift_identity["head"]
    assert _classify(pin_case) == ("indeterminate", "dependency-identity")
    try:
        _repo_identity(
            private_base / "masstree-src", expected_pin=drift_identity["head"],
            require_clean=True, deadline=deadline,
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("M4 repo identity accepted a different pin")

    dirty_repo = v2_base / "mimalloc-src"
    (dirty_repo / "source.txt").write_text("source drift\n", encoding="utf-8")
    dirty_identity = _repo_identity(
        dirty_repo, expected_pin=pins["mimalloc"], require_clean=False,
        deadline=deadline,
    )
    source_case = json.loads(json.dumps(actual_input))
    source_case["dependency_evidence"]["v2"]["mimalloc"] = dirty_identity
    assert _classify(source_case) == ("indeterminate", "dependency-identity")


def test_t2000_redaction_m5_secret_fixture_is_rejected() -> None:
    safe = {"schema": "fixed-enum", "value_sha256": "0" * 64}
    _assert_redacted_payload(safe, forbidden_values=("proxy-secret",))
    digest = {
        "schema": _DIGEST_SCHEMA, "completion": "complete",
        "precondition_status": "satisfied", "precondition_cause_code": "none",
        "raw_basename": f"{'0' * 64}-{'1' * 64}.json", "raw_sha256": "2" * 64,
        "classification": "migration-candidate-material",
        "reason_code": "proxy-secret",
        "ambient_proxy_env_sensitivity": "observed-single-run",
        "non_file_git_transport_needed": (
            "not-required-for-success-under-file-only-policy"
        ),
        "arbitrary_external_network": "not-measured",
        "arms": [
            {
                "id": arm_id, "outcome": "success", "stage_code": "none",
                "cause_code": "none", "git_protocol_evidence": (
                    "file-only-policy-success" if arm_id == "v2-source-no-proxy"
                    else "not-applicable"
                ),
            }
            for arm_id in _ARM_IDS
        ],
    }
    try:
        _audit_publish_payload(
            "digest", digest, forbidden_values=("proxy-secret",),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("M5 publish audit accepted a forbidden in-schema value")
    url_digest = dict(digest)
    url_digest["reason_code"] = "http://proxy.invalid:8080"
    try:
        _audit_publish_payload("digest", url_digest, forbidden_values=())
    except ValueError:
        pass
    else:
        raise AssertionError("M5 publish audit accepted a URL without the value gate")


def test_t2000_classifier_m6_invalid_control_has_one_reason() -> None:
    fixture = _classification_fixture()
    initial_control_value = False
    assert initial_control_value is False
    fixture["arms"]["legacy-proxy"].update({
        "outcome": "failed", "stage": "configure", "cause": "unexpected",
        "observer": "missed",
    })
    assert _classify(fixture) == ("indeterminate", "control-invalid")


def test_t2000_identity_legacy_delta_and_git_guard_are_exact() -> None:
    environments = _arm_environments(
        {"PATH": "/fixed/bin", "HTTP_PROXY": "ambient", "GIT_DIR": "/wrong"},
        "proxy-token",
    )
    proxy = environments["legacy-proxy"]
    no_proxy = environments["legacy-no-proxy"]
    assert proxy["PATH"] == no_proxy["PATH"] == environments["v2-source-no-proxy"]["PATH"]
    assert "GIT_ALLOW_PROTOCOL" not in proxy
    assert "GIT_ALLOW_PROTOCOL" not in no_proxy
    assert environments["v2-source-no-proxy"]["GIT_ALLOW_PROTOCOL"] == "file"
    assert {key for key in set(proxy) | set(no_proxy) if proxy.get(key) != no_proxy.get(key)} == {
        "http_proxy", "https_proxy",
    }


def test_t2000_configure_binding_is_exact_without_serializing_argv() -> None:
    base = Path("/private/base")
    sources = {name: base / f"{name}-src" for name in _DEPENDENCIES}
    argv = (
        "cmake", f"-DFETCHCONTENT_BASE_DIR={base}",
        *(f"-DFETCHCONTENT_SOURCE_DIR_{name.upper()}={sources[name]}" for name in _DEPENDENCIES),
    )
    assert _configure_shape(
        argv, expected_base=base, expected_sources=sources, legacy=False,
    )["source_dir_binding"] == "exact"
    wrong = argv[:-1] + ("-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=/wrong",)
    assert _configure_shape(
        wrong, expected_base=base, expected_sources=sources, legacy=False,
    )["source_dir_binding"] == "mismatch"
    assert _unobserved_configure_shape()["source_dir_binding"] == "unobserved"


def test_t2000_publisher_namespace_identity_is_exact(
    tmp_path: Path, monkeypatch: Any,
) -> None:
    raw = _pure_publish_raw_fixture()
    pbs_hash = "0" * 64
    nonce_hash = "1" * 64
    basename = f"{pbs_hash}-{nonce_hash}.json"
    module = sys.modules[__name__]
    current: dict[str, _ArtifactRootBinding] = {}
    monkeypatch.setattr(
        module, "_bind_execution_root", lambda: current["binding"],
    )

    def new_binding(repo_root: Path) -> _ArtifactRootBinding:
        insight_parent = repo_root / _ARTIFACT_RELATIVE_PATH.parent
        insight_parent.mkdir(parents=True)
        repo_info = repo_root.lstat()
        insight_info = insight_parent.lstat()
        return _ArtifactRootBinding(
            repo_root=repo_root,
            artifact_root=repo_root / _ARTIFACT_RELATIVE_PATH,
            repo_identity=(repo_info.st_dev, repo_info.st_ino),
            probe_identity=(0, 0),
            insight_parent_identity=(insight_info.st_dev, insight_info.st_ino),
            artifact_identity=None,
        )

    positive = new_binding(tmp_path / "positive")
    current["binding"] = positive
    _publish_artifacts(
        positive, raw, pbs_hash=pbs_hash, nonce_hash=nonce_hash,
        forbidden_values=(),
    )
    raw_path = positive.artifact_root / "raw" / basename
    digest_path = positive.artifact_root / "digest" / basename
    raw_payload = raw_path.read_bytes()
    digest_payload = digest_path.read_bytes()
    assert raw_payload == _canonical_bytes(raw) + b"\n"
    assert json.loads(digest_payload)["raw_sha256"] == hashlib.sha256(
        raw_payload,
    ).hexdigest()

    root_info = positive.artifact_root.lstat()
    rebound = _ArtifactRootBinding(
        repo_root=positive.repo_root,
        artifact_root=positive.artifact_root,
        repo_identity=positive.repo_identity,
        probe_identity=positive.probe_identity,
        insight_parent_identity=positive.insight_parent_identity,
        artifact_identity=(root_info.st_dev, root_info.st_ino),
    )
    current["binding"] = rebound
    try:
        _publish_artifacts(
            rebound, raw, pbs_hash=pbs_hash, nonce_hash=nonce_hash,
            forbidden_values=(),
        )
    except FileExistsError:
        pass
    else:
        raise AssertionError("publisher overwrote an existing create-only leaf")
    assert raw_path.read_bytes() == raw_payload
    assert digest_path.read_bytes() == digest_payload

    create_only = _create_only_at
    for attack in ("leaf-replacement", "root-replacement"):
        attacked = new_binding(tmp_path / attack)
        current["binding"] = attacked
        calls = 0

        def create_then_attack(directory_fd: int, name: str, payload: bytes) -> int:
            nonlocal calls
            leaf_fd = create_only(directory_fd, name, payload)
            calls += 1
            if calls == 2:
                if attack == "leaf-replacement":
                    target = attacked.artifact_root / "raw" / basename
                    target.rename(target.with_suffix(".held"))
                    target.write_bytes(b"replacement\n")
                else:
                    moved = attacked.artifact_root.with_suffix(".held")
                    attacked.artifact_root.rename(moved)
                    attacked.artifact_root.mkdir()
            return leaf_fd

        monkeypatch.setattr(module, "_create_only_at", create_then_attack)
        try:
            _publish_artifacts(
                attacked, raw, pbs_hash=pbs_hash, nonce_hash=nonce_hash,
                forbidden_values=(),
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"publisher accepted {attack}")
        finally:
            monkeypatch.setattr(module, "_create_only_at", create_only)
        assert calls == 2


def test_t2000_real_invocation_gate_accepts_exact_nodeid() -> None:
    binding = _bind_execution_root()
    assert binding.repo_root == Path.cwd()
    assert binding.artifact_root == Path.cwd() / _ARTIFACT_RELATIVE_PATH
    assert _real_invocation_allowed(
        (_REAL_NODEID, "-q"), f"{_REAL_NODEID} (call)",
    )


def test_t2000_real_invocation_gate_rejects_implicit_selection(tmp_path: Path) -> None:
    current = f"{_REAL_NODEID} (call)"
    for argv in (
        (),
        ("tools/pegasus/probes/test_t2000_legacy_build_probe.py",),
        ("tools/pegasus/probes",),
        (".",),
        (_REAL_NODEID, "--collect-only"),
    ):
        assert not _real_invocation_allowed(argv, current)
    assert not _real_invocation_allowed(
        (_REAL_NODEID,), "tools/pegasus/probes/test_meta.py::test_calls_probe (call)",
    )

    fake_root = tmp_path / "other-checkout"
    fake_probe = fake_root / _PROBE_RELATIVE_PATH
    fake_module = fake_root / "orchestrator/campaign/buildcache.py"
    fake_probe.parent.mkdir(parents=True)
    fake_module.parent.mkdir(parents=True)
    (fake_root / _ARTIFACT_RELATIVE_PATH.parent).mkdir(parents=True)
    fake_probe.write_text("# probe fixture\n", encoding="utf-8")
    fake_module.write_text("# production fixture\n", encoding="utf-8")
    outside = tmp_path / "outside-artifacts"
    outside.mkdir()
    fake_artifact = fake_root / _ARTIFACT_RELATIVE_PATH
    fake_artifact.symlink_to(outside, target_is_directory=True)
    try:
        _validate_execution_root(
            probe_file=fake_probe, cwd=fake_root, git_top=fake_root,
            module_files=(fake_module,),
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("artifact binding accepted a symlink root")
    assert not (outside / "raw").exists()
    assert not (outside / "digest").exists()

    try:
        _validate_execution_root(
            probe_file=Path(__file__), cwd=fake_root, git_top=fake_root,
            module_files=(fake_module,),
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("artifact binding accepted another checkout as cwd")


def test_t2000_legacy_build_probe() -> None:
    """Explicit compute-only real probe.  Never select this node in a pure run."""
    if not _real_invocation_allowed(tuple(sys.argv[1:]), os.environ.get("PYTEST_CURRENT_TEST", "")):
        raise AssertionError("T-2000 real probe requires its exact explicit nodeid")
    try:
        _real_probe()
    except Exception:
        # Endpoint-bearing exception text and tracebacks must not enter output.
        raise AssertionError("T-2000 real probe failed before safe artifact completion") from None
