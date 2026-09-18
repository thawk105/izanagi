# -*- coding: utf-8 -*-
"""Pure T-126 qualification contract.

No function in this module reads the repository, writes artifacts, sleeps, or
starts a process.  In particular, the SPRT decision is always recomputed from
the observed bit prefix; recorded decimal LLRs are never authoritative.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from orchestrator.calibrator import perf_preflight as _perf_preflight
from .retry_index import RetryIndexError, validate_retry_index


_HERE = Path(__file__).resolve().parent
DEFAULT_PROTOCOL_PATH = _HERE / "t126_control_v1.json"
# T-126 owns the PBS reservation policy that governs its own runs (requested
# walltime plus the phase caps the Wmax closure is derived from).  It
# deliberately does NOT live in the shared tools/pegasus/policy.json: that
# file is byte-pinned by other campaigns' committed evidence, so a T-126 edit
# there would drift their bindings.  Only genuinely shared values
# (project/queue/nodes/...) belong in the shared policy.  Distinct from the
# series result's "timing_envelope", which records the OBSERVED monotonic
# envelope of one run rather than the CONFIGURED request.
RESERVATION_POLICY_RELATIVE_PATH = (
    "orchestrator/qualification/t126_reservation_policy_v1.json")
DEFAULT_RESERVATION_POLICY_PATH = _HERE / "t126_reservation_policy_v1.json"
_HEX40 = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_ZERO_HASH = "0" * 64

REQUIRED_CODE_IDENTITY_PATHS = frozenset({
    "orchestrator/qualification/__init__.py",
    "orchestrator/qualification/atomic_publish.py",
    "orchestrator/qualification/attempt_ledger.py",
    "orchestrator/qualification/contract.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/collector.py",
    "orchestrator/qualification/identity.py",
    "orchestrator/qualification/qsub_binding.py",
    "orchestrator/qualification/retry_index.py",
    "orchestrator/qualification/series.py",
    "orchestrator/qualification/submission.py",
    "orchestrator/qualification/t126_driver.py",
    "orchestrator/qualification/t126_control_v1.json",
    "orchestrator/qualification/t126_reservation_policy_v1.json",
    "orchestrator/qualification/t126_marker_schema.json",
    "orchestrator/qualification/t126_event_schema.json",
    "orchestrator/qualification/t126_evaluation_event_schema.json",
    "orchestrator/qualification/t126_series_result_schema.json",
    "orchestrator/qualification/t126_final_receipt_schema.json",
    "orchestrator/qualification/t126_failure_receipt_schema.json",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/buildcache.py",
    "orchestrator/campaign/build_admission.py",
    "orchestrator/campaign/__init__.py",
    "orchestrator/campaign/calibration_verify.py",
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
    "orchestrator/campaign/env_attestation.py",
    "orchestrator/campaign/execution_guard.py",
    "orchestrator/campaign/site_policy.py",
    "orchestrator/campaign/source_digest.py",
    "orchestrator/calibrator/__init__.py",
    "orchestrator/calibrator/effective_clock_policy.py",
    "orchestrator/calibrator/schema_v2.py",
    "orchestrator/calibrator/tsc.py",
    "orchestrator/verifier/core.py",
    "orchestrator/verifier/dsg.py",
    "orchestrator/verifier/model.py",
    "orchestrator/verifier/parse.py",
    "orchestrator/verifier/__init__.py",
    "orchestrator/verifier/commit_receipt.py",
    "orchestrator/verifier/report.py",
    "tools/pegasus/policy.json",
})
REQUIRED_SCRIPT_IDENTITY_PATHS = frozenset({
    "tools/pegasus/submit_t126_qualification.sh",
    "tools/pegasus/t126_qualification.sh",
    "tools/pegasus/collect_t126_qualification.py",
})
REGISTERED_DEPENDENCY_BUILD_ARGV = {
    "gflags_configure": [
        "cmake", "-S", "gflags", "-B", "gflags-build",
        "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF"],
    "gflags_build": ["cmake", "--build", "gflags-build", "-j", "48"],
    "gflags_install": ["cmake", "--install", "gflags-build"],
    "glog_configure": [
        "cmake", "-S", "glog", "-B", "glog-build",
        "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF",
        "-DWITH_GTEST=OFF", "-DBUILD_TESTING=OFF", "-DWITH_UNWIND=OFF"],
    "glog_build": ["cmake", "--build", "glog-build", "-j", "48"],
    "glog_install": ["cmake", "--install", "glog-build"],
}


class ProtocolError(ValueError):
    """A protocol value or observation is outside the frozen acceptance set."""


def _duplicate_rejector(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProtocolError(f"value is not canonical JSON: {exc}") from exc


def _exact_keys(value: object, expected: set[str], label: str) -> Mapping[str, Any]:
    if type(value) is not dict or set(value) != expected:
        actual = sorted(value) if type(value) is dict else type(value).__name__
        raise ProtocolError(f"{label} key set mismatch: {actual!r}")
    return value


_TOP_KEYS = {
    "schema_version", "authority", "hold_enforced", "statistical_claim",
    "control_kind", "environment", "source", "workload", "verification",
    "threshold", "sprt", "order", "timing", "retry", "artifact",
}


def validate_protocol(document: object) -> dict[str, Any]:
    top = dict(_exact_keys(document, _TOP_KEYS, "protocol"))
    literals = {
        "schema_version": "t126-qualification-control/v1",
        "authority": "evidence-only/no-promotion",
        "hold_enforced": False,
        "statistical_claim": "none",
        "control_kind": "historically-within-linux-floor-observational-smoke",
    }
    for key, expected in literals.items():
        if top[key] != expected or type(top[key]) is not type(expected):
            raise ProtocolError(f"protocol.{key} must be {expected!r}")

    env = _exact_keys(top["environment"], {
        "env_tag", "clocks_per_us", "numactl", "attestation_mode",
        "single_process", "allow_resume",
    }, "environment")
    if env != {
        "env_tag": "pegasus", "clocks_per_us": 2100, "numactl": [],
        "attestation_mode": "required", "single_process": True,
        "allow_resume": False,
    }:
        raise ProtocolError("environment does not match exact Pegasus qualification contract")

    source = _exact_keys(top["source"], {
        "campaign_lock_path", "campaign_lock_sha256", "wal_path", "wal_sha256",
        "historical_ccbench_commit", "required_stage_order", "members",
    }, "source")
    for key in ("campaign_lock_sha256", "wal_sha256"):
        if type(source[key]) is not str or _HEX64.fullmatch(source[key]) is None:
            raise ProtocolError(f"source.{key} must be full lowercase sha256")
    if source["required_stage_order"] != [
            "build_start", "build_done", "verify_done", "bench_done", "commit"]:
        raise ProtocolError("source.required_stage_order mismatch")
    members = _exact_keys(source["members"], {"subject", "reference"}, "source.members")
    for role in ("subject", "reference"):
        row = _exact_keys(members[role], {
            "source_wal_variant", "genome", "historical_median_tps",
        }, f"source.members.{role}")
        if (type(row["source_wal_variant"]) is not str
                or type(row["genome"]) is not str
                or type(row["historical_median_tps"]) is not float
                or not math.isfinite(row["historical_median_tps"])
                or row["historical_median_tps"] <= 0):
            raise ProtocolError(f"source member {role} is invalid")
    if members["subject"]["source_wal_variant"] == members["reference"]["source_wal_variant"]:
        raise ProtocolError("source member roles must be distinct")

    workload = _exact_keys(top["workload"], {
        "records", "threads", "ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw",
        "ycsb_max_ope", "extime", "reps", "bench_max_rounds",
    }, "workload")
    if workload != {
        "records": 1_000_000, "threads": 48, "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "95", "ycsb_rmw": "0", "ycsb_max_ope": "10",
        "extime": 3, "reps": 5, "bench_max_rounds": 1,
    }:
        raise ProtocolError("workload does not match frozen qualification point")

    verification = _exact_keys(top["verification"], {
        "order", "require_settled", "require_all_rep_rc_zero",
        "require_commits_positive", "require_aborts_positive",
        "require_anomalies_zero", "require_distinct_trace_perf_binaries",
    }, "verification")
    if verification["order"] != ["legacy", "s2"]:
        raise ProtocolError("verification order must be exact legacy+s2")
    if any(verification[key] is not True for key in verification if key != "order"):
        raise ProtocolError("all verification evidence requirements must be true")

    threshold = _exact_keys(top["threshold"], {
        "relative", "comparison", "threshold_origin_env",
        "pegasus_floor_calibrated",
    }, "threshold")
    if threshold != {
        "relative": 0.03,
        "comparison": "subject/reference-1 > relative",
        "threshold_origin_env": "linux-baremetal",
        "pegasus_floor_calibrated": False,
    }:
        raise ProtocolError("threshold contract mismatch")

    sprt = _exact_keys(top["sprt"], {
        "p0", "p1", "alpha", "beta", "rmax",
        "upper_comparison", "lower_comparison",
    }, "sprt")
    if sprt != {
        "p0": 0.5, "p1": 0.9, "alpha": 0.1, "beta": 0.1, "rmax": 8,
        "upper_comparison": ">", "lower_comparison": "<",
    }:
        raise ProtocolError("SPRT parameters are not the frozen pure contract")

    order = _exact_keys(top["order"], {
        "seed", "strategy", "max_prefix_first_position_imbalance",
    }, "order")
    if (type(order["seed"]) is not str or not order["seed"]
            or order["strategy"] != "seeded-first-then-alternate"
            or order["max_prefix_first_position_imbalance"] != 1):
        raise ProtocolError("order contract mismatch")

    timing = _exact_keys(top["timing"], {
        "member_cap_s", "member_term_grace_s", "round_gap_s",
        "prologue_cap_s", "attestation_cap_s", "finalize_reserve_s",
        "wmax_s", "qualification_walltime_s",
    }, "timing")
    for key, value in timing.items():
        if type(value) is not int or value <= 0:
            raise ProtocolError(f"timing.{key} must be a positive integer")
    calculated = (
        timing["prologue_cap_s"]
        + 2 * sprt["rmax"] * timing["member_cap_s"]
        + (sprt["rmax"] - 1) * timing["round_gap_s"]
        + timing["attestation_cap_s"]
        + timing["finalize_reserve_s"]
    )
    if (timing["member_cap_s"] != 900 or timing["round_gap_s"] != 1800
            or timing["prologue_cap_s"] != 900
            or timing["attestation_cap_s"] != 600
            or timing["finalize_reserve_s"] != 600
            or calculated != 29100 or timing["wmax_s"] != calculated
            or timing["qualification_walltime_s"] != 36000
            or calculated >= timing["qualification_walltime_s"]):
        raise ProtocolError("timing Wmax closure mismatch")

    retry = _exact_keys(top["retry"], {
        "max_retries", "only_before_first_observation", "eligible_reasons",
    }, "retry")
    exact_eligible_reasons = [
        "pre-attempt-infrastructure",
        "pre-member-infrastructure",
        "pre-attestation",
        "reservation-unavailable",
    ]
    if (retry["max_retries"] != 1
            or retry["only_before_first_observation"] is not True
            or retry["eligible_reasons"] != exact_eligible_reasons):
        raise ProtocolError("retry contract mismatch")

    artifact = _exact_keys(top["artifact"], {
        "namespace", "marker_schema", "event_schema",
        "evaluation_event_schema", "series_result_schema",
        "final_receipt_schema", "failure_receipt_schema",
    }, "artifact")
    expected_artifact = {
        "namespace": "output/env/pegasus/qualification/t126",
        "marker_schema": "t126-qualification-marker/v1",
        "event_schema": "t126-qualification-event/v1",
        "evaluation_event_schema": "t126-qualification-evaluation-event/v1",
        "series_result_schema": "t126-qualification-series-result/v1",
        "final_receipt_schema": "t126-qualification-final-receipt/v1",
        "failure_receipt_schema": "t126-qualification-attempt-failure-receipt/v1",
    }
    if artifact != expected_artifact:
        raise ProtocolError("artifact namespace/schema mismatch")
    canonical_json_bytes(top)
    return top


def load_protocol(path: Path | str = DEFAULT_PROTOCOL_PATH) -> dict[str, Any]:
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            document = json.load(handle, object_pairs_hook=_duplicate_rejector)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"cannot load protocol: {path}: {exc}") from exc
    return validate_protocol(document)


def load_protocol_bytes(raw: bytes) -> dict[str, Any]:
    """Strictly parse an immutable protocol blob without materializing a file."""
    if type(raw) is not bytes:
        raise ProtocolError("protocol blob must be exact bytes")
    try:
        document = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_duplicate_rejector,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ProtocolError(f"non-finite protocol constant: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"cannot load protocol blob: {exc}") from exc
    return validate_protocol(document)


def protocol_sha256(protocol: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(validate_protocol(dict(protocol)))).hexdigest()


@dataclass(frozen=True)
class RoundObservation:
    relative: float
    bit: int
    direction: str


def observe_relative(subject_tps: float, reference_tps: float, floor: float) -> RoundObservation:
    for name, value in (
            ("subject_tps", subject_tps), ("reference_tps", reference_tps),
            ("floor", floor)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ProtocolError(f"{name} must be a finite real number")
        if not math.isfinite(float(value)):
            raise ProtocolError(f"{name} must be finite")
    if subject_tps <= 0 or reference_tps <= 0 or not (0 < floor < 1):
        raise ProtocolError("TPS values must be positive and floor must be in (0,1)")
    subject = float(subject_tps)
    reference = float(reference_tps)
    threshold = float(floor)
    relative = subject / reference - 1.0
    # Compare the original measurements against the multiplicative boundary.
    # This keeps an exactly constructed boundary (for example 103/100 at .03)
    # on the zero side even when division/subtraction rounds upward.
    if subject > reference * (1.0 + threshold):
        return RoundObservation(relative=relative, bit=1, direction="subject-above-threshold")
    if subject < reference * (1.0 - threshold):
        return RoundObservation(relative=relative, bit=0, direction="reference-above-threshold")
    return RoundObservation(relative=relative, bit=0, direction="within-borrowed-threshold")


@dataclass(frozen=True)
class SprtDecision:
    terminal: str
    rounds: int
    llr: float
    llr_hex: str
    lower_boundary: float
    upper_boundary: float


def _validate_bits(bits: Sequence[int], rmax: int) -> tuple[int, ...]:
    if isinstance(bits, (str, bytes)) or not isinstance(bits, Sequence):
        raise ProtocolError("bits must be a sequence of exact integers")
    values = tuple(bits)
    if len(values) > rmax:
        raise ProtocolError("observation count exceeds rmax")
    for bit in values:
        if type(bit) is not int or bit not in (0, 1):
            raise ProtocolError("bits accept only exact int 0 or 1")
    return values


def sprt_decide(bits: Sequence[int], params: Mapping[str, Any]) -> SprtDecision:
    required = {
        "p0", "p1", "alpha", "beta", "rmax",
        "upper_comparison", "lower_comparison",
    }
    cfg = _exact_keys(params, required, "sprt params")
    if cfg["upper_comparison"] != ">" or cfg["lower_comparison"] != "<":
        raise ProtocolError("SPRT comparisons must remain strict")
    for key in ("p0", "p1", "alpha", "beta"):
        if type(cfg[key]) is not float or not (0.0 < cfg[key] < 1.0):
            raise ProtocolError(f"sprt.{key} must be a float in (0,1)")
    if not (cfg["p0"] < cfg["p1"]):
        raise ProtocolError("sprt requires p0 < p1")
    if type(cfg["rmax"]) is not int or cfg["rmax"] <= 0:
        raise ProtocolError("sprt.rmax must be a positive exact integer")
    values = _validate_bits(bits, cfg["rmax"])
    upper = math.log((1.0 - cfg["beta"]) / cfg["alpha"])
    lower = math.log(cfg["beta"] / (1.0 - cfg["alpha"]))
    llr = 0.0
    terminal = "continuing"
    for index, bit in enumerate(values, 1):
        llr += math.log(cfg["p1"] / cfg["p0"]) if bit else math.log(
            (1.0 - cfg["p1"]) / (1.0 - cfg["p0"])
        )
        current = "continuing"
        if llr > upper:
            current = "upper_boundary"
        elif llr < lower:
            current = "lower_boundary"
        elif index == cfg["rmax"]:
            current = "indeterminate"
        if current != "continuing":
            if index != len(values):
                raise ProtocolError("terminal SPRT prefix has a forbidden suffix")
            terminal = current
    return SprtDecision(
        terminal=terminal,
        rounds=len(values),
        llr=llr,
        llr_hex=llr.hex(),
        lower_boundary=lower,
        upper_boundary=upper,
    )


def verify_recorded_decision(
        bits: Sequence[int], params: Mapping[str, Any], *,
        terminal: str, llr_hex: str) -> SprtDecision:
    decision = sprt_decide(bits, params)
    if type(terminal) is not str or terminal != decision.terminal:
        raise ProtocolError("recorded terminal does not match recomputed SPRT")
    if type(llr_hex) is not str or llr_hex != decision.llr_hex:
        raise ProtocolError("recorded LLR hex does not match recomputed SPRT")
    return decision


def operating_characteristics(
        true_p: float, params: Mapping[str, Any]) -> dict[str, float]:
    """Enumerate all 2**Rmax sequences and return exact-design OC values."""
    if type(true_p) is not float or not (0.0 < true_p < 1.0):
        raise ProtocolError("true_p must be an exact float in (0,1)")
    rmax = params.get("rmax") if isinstance(params, Mapping) else None
    if type(rmax) is not int or rmax <= 0 or rmax > 20:
        raise ProtocolError("OC rmax must be a bounded positive exact integer")
    totals = {
        "lower_boundary": 0.0,
        "upper_boundary": 0.0,
        "indeterminate": 0.0,
        "expected_rounds": 0.0,
    }
    for full in itertools.product((0, 1), repeat=rmax):
        terminal = None
        rounds = rmax
        for length in range(1, rmax + 1):
            decision = sprt_decide(full[:length], params)
            if decision.terminal != "continuing":
                terminal = decision.terminal
                rounds = length
                break
        if terminal not in {
                "lower_boundary", "upper_boundary", "indeterminate"}:
            raise ProtocolError("OC enumeration did not reach a terminal")
        ones = sum(full)
        probability = true_p ** ones * (1.0 - true_p) ** (rmax - ones)
        totals[terminal] += probability
        totals["expected_rounds"] += probability * rounds
    if not math.isclose(
            totals["lower_boundary"] + totals["upper_boundary"]
            + totals["indeterminate"], 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ProtocolError("OC probability mass does not close")
    return totals


def balanced_order(seed: str, round_index: int) -> tuple[str, str]:
    if type(seed) is not str or not seed:
        raise ProtocolError("order seed must be a non-empty string")
    if type(round_index) is not int or round_index < 1:
        raise ProtocolError("round_index must be a positive exact integer")
    first_subject = hashlib.sha256(seed.encode("utf-8")).digest()[0] & 1
    if (round_index - 1) & 1:
        first_subject ^= 1
    return ("subject", "reference") if first_subject else ("reference", "subject")


_SERIES_ID_KEYS = {
    "schema_version", "protocol_sha256", "superproject_commit",
    "superproject_tree", "ccbench_gitlink", "source_snapshots",
    "pair_roles", "workload", "verification", "threshold", "sprt",
    "timing", "order_seed", "code_identity", "script_identity",
    "toolchain_manifest",
}


def series_identity(preimage: Mapping[str, Any]) -> str:
    value = _exact_keys(preimage, _SERIES_ID_KEYS, "series identity")
    if value["schema_version"] != "t126-qualification-series-identity/v1":
        raise ProtocolError("series identity schema mismatch")
    for key in ("protocol_sha256",):
        if type(value[key]) is not str or _HEX64.fullmatch(value[key]) is None:
            raise ProtocolError(f"series identity {key} is invalid")
    for key in ("superproject_commit", "superproject_tree", "ccbench_gitlink"):
        if type(value[key]) is not str or _HEX40.fullmatch(value[key]) is None:
            raise ProtocolError(f"series identity {key} is invalid")
    snapshots = _exact_keys(
        value["source_snapshots"], {"campaign_lock", "wal"},
        "series identity source snapshots",
    )
    for label, row in snapshots.items():
        row = _exact_keys(row, {"path", "sha256"}, f"source snapshot {label}")
        if (type(row["path"]) is not str or not row["path"]
                or Path(row["path"]).is_absolute()
                or ".." in Path(row["path"]).parts
                or type(row["sha256"]) is not str
                or _HEX64.fullmatch(row["sha256"]) is None):
            raise ProtocolError(f"source snapshot {label} is invalid")
    pair_roles = _exact_keys(
        value["pair_roles"], {"subject", "reference"},
        "series identity pair roles",
    )
    for role, row in pair_roles.items():
        row = _exact_keys(
            row, {"source_wal_variant", "genome", "historical_median_tps"},
            f"series identity pair {role}",
        )
        if (type(row["source_wal_variant"]) is not str
                or not row["source_wal_variant"]
                or type(row["genome"]) is not str or not row["genome"]
                or type(row["historical_median_tps"]) is not float
                or not math.isfinite(row["historical_median_tps"])
                or row["historical_median_tps"] <= 0):
            raise ProtocolError(f"series identity pair {role} is invalid")
    for key, required in (
            ("code_identity", REQUIRED_CODE_IDENTITY_PATHS),
            ("script_identity", REQUIRED_SCRIPT_IDENTITY_PATHS)):
        rows = value[key]
        if type(rows) is not dict or set(rows) != required:
            raise ProtocolError(f"series identity {key} required set mismatch")
        if any(type(digest) is not str or _HEX64.fullmatch(digest) is None
               for digest in rows.values()):
            raise ProtocolError(f"series identity {key} hash is invalid")
    raw_toolchain = value["toolchain_manifest"]
    if not isinstance(raw_toolchain, Mapping):
        raise ProtocolError("series identity toolchain is not an object")
    receipt = raw_toolchain.get("perf_preflight")
    try:
        use_perf = _perf_preflight.use_perf_from_receipt(receipt)
    except _perf_preflight.PerfPreflightError as exc:
        raise ProtocolError("toolchain perf preflight is invalid") from exc
    if receipt is not None and use_perf:
        raise ProtocolError(
            "available perf receipt cannot select degraded toolchain shape")
    toolchain_keys = {
        "schema_version", "executables", "dependencies", "build_argv",
    }
    if not use_perf:
        toolchain_keys.add("perf_preflight")
    toolchain = _exact_keys(
        raw_toolchain, toolchain_keys, "series identity toolchain")
    if toolchain["schema_version"] != "t126-toolchain-manifest/v1":
        raise ProtocolError("toolchain schema mismatch")
    executable_keys = {"python", "cc", "cxx", "cmake"}
    if use_perf:
        executable_keys.add("perf")
    executables = _exact_keys(
        toolchain["executables"], executable_keys, "toolchain executables")
    for name, row in executables.items():
        row = _exact_keys(
            row, {"path", "sha256", "version"}, f"toolchain executable {name}")
        if (type(row["path"]) is not str or not row["path"]
                or not Path(row["path"]).is_absolute()
                or type(row["version"]) is not str or not row["version"]
                or type(row["sha256"]) is not str
                or _HEX64.fullmatch(row["sha256"]) is None):
            raise ProtocolError(f"toolchain executable {name} is invalid")
    dependencies = _exact_keys(
        toolchain["dependencies"], {"gflags", "glog"},
        "toolchain dependencies",
    )
    for name, row in dependencies.items():
        row = _exact_keys(
            row, {"commit", "tree"}, f"toolchain dependency {name}")
        if (type(row["commit"]) is not str or _HEX40.fullmatch(row["commit"]) is None
                or type(row["tree"]) is not str
                or _HEX40.fullmatch(row["tree"]) is None):
            raise ProtocolError(f"toolchain dependency {name} is invalid")
    build_argv = _exact_keys(
        toolchain["build_argv"],
        {"gflags_configure", "gflags_build", "gflags_install",
         "glog_configure", "glog_build", "glog_install"},
        "toolchain build argv",
    )
    if any(type(argv) is not list or not argv
           or any(type(item) is not str or not item for item in argv)
           for argv in build_argv.values()):
        raise ProtocolError("toolchain build argv is invalid")
    return hashlib.sha256(canonical_json_bytes(dict(value))).hexdigest()


_ATTEMPT_ID_KEYS = {
    "schema_version", "qualification_series_id", "pbs_job_id", "nonce",
    "retry_index", "submission_intent_sha256",
}


def attempt_identity(preimage: Mapping[str, Any]) -> str:
    value = _exact_keys(preimage, _ATTEMPT_ID_KEYS, "attempt identity")
    if value["schema_version"] != "t126-qualification-attempt-identity/v1":
        raise ProtocolError("attempt identity schema mismatch")
    if (type(value["qualification_series_id"]) is not str
            or _HEX64.fullmatch(value["qualification_series_id"]) is None):
        raise ProtocolError("attempt series id is invalid")
    try:
        validate_retry_index(value["retry_index"])
    except RetryIndexError as exc:
        raise ProtocolError(
            "attempt retry index must be exact 0 or 1") from exc
    if (type(value["submission_intent_sha256"]) is not str
            or _HEX64.fullmatch(value["submission_intent_sha256"]) is None):
        raise ProtocolError("attempt submission intent hash is invalid")
    for key in ("pbs_job_id", "nonce"):
        if type(value[key]) is not str or not value[key] or "\n" in value[key]:
            raise ProtocolError(f"attempt identity {key} is invalid")
    return hashlib.sha256(canonical_json_bytes(dict(value))).hexdigest()
