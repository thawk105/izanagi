"""Offline analysis for the preregistered backoff policy performance trial."""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
from pathlib import Path

__all__ = ["analyze_policy_performance"]

ANALYSIS_VERSION = "izanagi-backoff-policy-performance-analysis/v1"
SCHEMA_VERSION = "izanagi-cicada-adaptive-3const-probe/v3"
PERFORMANCE_CONTRACT = "backoff-policy-arm-perf/v1"
NOT_CERTIFIED = (
    "trace-disabled performance runs only; no serializability check was run"
)
BLOCK_COUNT = 18
DF = 17
T95_DF17 = 2.1098156
EQUIVALENCE_MARGIN_LOG = 0.02955880224154443
PREREGISTRATION_SHA256 = (
    "2f5170c99dda9dd70647a611bff798b6e54c5e29b60e872cd755e5b8515cc25c"
)
PREREGISTRATION_ERRATUM_1_SHA256 = (
    "9f81a61b92e88a7dcede8a779c0241c7bcbc96b00ef01332b8df8e7ed5ec3eea"
)
CCBENCH_PIN = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
PATCH_PATHS = (
    "patches/cicada-adaptive-params.patch",
    "patches/cicada-adaptive-dynamic.patch",
    "patches/cicada-adaptive-counterfactual.patch",
)
DEFAULT_STEP_POLICY_SEED = 11_400_714_819_323_198_485

CELL_LITERALS = {
    "p0": "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0",
    "p1": "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1",
    "p2": "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2",
}
CELL_LABELS = {
    "p0": "cw-as-dyn-p0",
    "p1": "cw-as-dyn-p1",
    "p2": "cw-as-dyn-p2",
}
PREREGISTERED_CELL_PERMUTATIONS = (
    (
        "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0",
        "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1",
        "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2",
    ),
    (
        "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0",
        "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2",
        "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1",
    ),
    (
        "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1",
        "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0",
        "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2",
    ),
    (
        "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1",
        "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2",
        "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0",
    ),
    (
        "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2",
        "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0",
        "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1",
    ),
    (
        "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2",
        "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1",
        "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0",
    ),
)
PREREGISTERED_SEEDS = (
    7_170_359_757_993_337_886,
    17_989_269_546_948_137_795,
    3_716_960_512_023_197_351,
    2_309_627_334_396_074_330,
    17_927_187_949_116_432_153,
    3_065_832_495_472_073_934,
    4_312_234_405_970_990_967,
    427_285_116_805_996_036,
    3_640_648_522_570_663_905,
    6_418_011_988_295_890_983,
    8_628_608_498_907_907_249,
    3_020_250_207_517_407_008,
    2_373_385_927_424_670_485,
    12_508_141_252_750_115_867,
    5_818_589_253_263_944_573,
    13_760_661_656_174_455_019,
    16_587_099_826_641_119_208,
    13_478_069_633_953_621_058,
)
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
THREADS = (6, 12, 18, 24, 30, 36, 42, 48)
WORKLOAD_FLAGS = {
    "write-heavy": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "5",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
    "balanced": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "50",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
    "read-heavy": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "95",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
}
CONTRASTS = (("p0", "p1"), ("p0", "p2"), ("p2", "p1"))
PRIMARY_POINT = ("write-heavy", 48)

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_HEX_RE = re.compile(r"[0-9a-f]+")
_EXPECTED_COORDINATES = {
    (policy, workload, threads)
    for policy in range(3)
    for workload in WORKLOADS
    for threads in THREADS
}


def _artifact_invalid(detail: str) -> None:
    raise ValueError(f"artifact-invalid: {detail}")


def _exact_int(value: object, expected: int) -> bool:
    return type(value) is int and value == expected


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    document = {}
    for key, value in pairs:
        if key in document:
            raise ValueError(f"duplicate JSON key {key!r}")
        document[key] = value
    return document


def _load_json(path: Path) -> dict:
    try:
        document = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        _artifact_invalid(f"{path}: invalid JSON artifact: {exc}")
    if type(document) is not dict:
        _artifact_invalid(f"{path}: artifact must be a JSON object")
    return document


def _expected_cell_identity(policy: int) -> dict:
    return {
        "cell": CELL_LABELS[f"p{policy}"],
        "back_off": 1,
        "step_us": 1.0,
        "ceiling_us": 1000,
        "update_us": 2560,
        "count_window": 10000,
        "count_cap_us": 10240,
        "step_adapt": 1,
        "step_min_us": 1.0,
        "step_max_us": 4.0,
        "dyn_ceiling": 1,
        "cell_format_fields": 12,
        "step_policy": policy,
    }


def _matches_exact(document: dict, expected: dict) -> bool:
    return all(
        type(document.get(key)) is type(value) and document.get(key) == value
        for key, value in expected.items()
    )


def _expected_genome_flags(policy: int, seed: int) -> dict[str, str]:
    return {
        "NO_WAIT_LOCKING_IN_VALIDATION": "1",
        "NO_WAIT_OF_TICTOC": "0",
        "WAL": "0",
        "BACK_OFF": "1",
        "BACKOFF_INCR_MILLI": "1000",
        "BACKOFF_MAX_US": "1000",
        "BACKOFF_UPDATE_US": "2560",
        "BACKOFF_COUNT_WINDOW": "10000",
        "BACKOFF_COUNT_CAP_US": "10240",
        "BACKOFF_STEP_ADAPT": "1",
        "BACKOFF_STEP_MIN_MILLI": "1000",
        "BACKOFF_STEP_MAX_MILLI": "4000",
        "BACKOFF_DYN_CEILING": "1",
        "BACKOFF_TRACE": "0",
        "BACKOFF_STEP_POLICY": str(policy),
        "BACKOFF_STEP_POLICY_SEED": str(
            seed if policy == 2 else DEFAULT_STEP_POLICY_SEED
        ),
    }


def _validate_genome(value: object, *, policy: int, seed: int, binding: str) -> str:
    if type(value) is not str or value.count("|") != 1:
        _artifact_invalid(f"{binding}: genome is not canonical")
    protocol, encoded = value.split("|", 1)
    if protocol != "silo" or not encoded:
        _artifact_invalid(f"{binding}: genome protocol or flags are invalid")
    flags = {}
    for item in encoded.split(","):
        if item.count("=") != 1:
            _artifact_invalid(f"{binding}: genome flag encoding is malformed")
        name, flag_value = item.split("=", 1)
        if not name or not flag_value or name in flags:
            _artifact_invalid(f"{binding}: genome flag is empty or duplicated")
        flags[name] = flag_value
    expected = _expected_genome_flags(policy, seed)
    canonical = "silo|" + ",".join(
        f"{name}={flag_value}" for name, flag_value in sorted(expected.items())
    )
    if flags != expected or value != canonical:
        _artifact_invalid(
            f"{binding}: build differences exceed the policy/seed allowlist"
        )
    return value


def _validate_patch_identity(document: dict, *, binding: str) -> tuple:
    hash_fields = (
        "patch_sha256",
        "dynamic_patch_sha256",
        "counterfactual_patch_sha256",
    )
    hashes = tuple(document.get(field) for field in hash_fields)
    if any(
        type(value) is not str or _SHA256_RE.fullmatch(value) is None
        for value in hashes
    ):
        _artifact_invalid(f"{binding}: patch SHA-256 identity is invalid")
    expected_stack = [
        {"path": path, "sha256": sha256}
        for path, sha256 in zip(PATCH_PATHS, hashes, strict=True)
    ]
    if document.get("patch_stack") != expected_stack:
        _artifact_invalid(f"{binding}: ordered patch stack is invalid")
    encoded = "izanagi-patch-stack/v1\n" + "".join(
        f"{entry['path']} {entry['sha256']}\n" for entry in expected_stack
    )
    expected_stack_sha256 = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    if document.get("patch_stack_sha256") != expected_stack_sha256:
        _artifact_invalid(f"{binding}: ordered patch stack digest is invalid")
    return (
        *hashes,
        tuple((entry["path"], entry["sha256"]) for entry in expected_stack),
        expected_stack_sha256,
    )


def _validate_execution_identity(document: dict, *, binding: str) -> tuple:
    repo_head = document.get("repo_head")
    driver_sha256 = document.get("driver_sha256")
    pbs_sha256 = document.get("pbs_sha256")
    ccbench_commit = document.get("ccbench_commit")
    ccbench_head = document.get("ccbench_head")
    cc = document.get("cc")
    cxx = document.get("cxx")
    if type(repo_head) is not str or _COMMIT_RE.fullmatch(repo_head) is None:
        _artifact_invalid(f"{binding}: repo_head identity is invalid")
    if any(
        type(value) is not str or _SHA256_RE.fullmatch(value) is None
        for value in (driver_sha256, pbs_sha256)
    ):
        _artifact_invalid(f"{binding}: driver/PBS identity is invalid")
    if (
        type(ccbench_commit) is not str
        or _HEX_RE.fullmatch(ccbench_commit) is None
        or not CCBENCH_PIN.startswith(ccbench_commit)
        or ccbench_head != CCBENCH_PIN
    ):
        _artifact_invalid(f"{binding}: ccbench pin identity is invalid")
    if any(type(value) is not str or not value for value in (cc, cxx)):
        _artifact_invalid(f"{binding}: compiler identity is invalid")
    if document.get("repo_status_clean") is not True:
        _artifact_invalid(f"{binding}: repository cleanliness evidence is invalid")
    driver_argv = document.get("driver_argv")
    if (
        type(driver_argv) is not list
        or not driver_argv
        or any(type(item) is not str for item in driver_argv)
    ):
        _artifact_invalid(f"{binding}: driver argv identity is invalid")
    patch_identity = _validate_patch_identity(document, binding=binding)
    return (
        repo_head,
        driver_sha256,
        pbs_sha256,
        ccbench_commit,
        ccbench_head,
        cc,
        cxx,
        *patch_identity,
    )


def _validate_source_evidence(
    value: object,
    *,
    genome: str,
    ccbench_commit: str,
    binding: str,
) -> dict:
    if type(value) is not dict:
        _artifact_invalid(f"{binding}: source_evidence must be an object")
    expected_genome_sha256 = hashlib.sha256(genome.encode("utf-8")).hexdigest()
    if (
        value.get("ccbench_commit") != ccbench_commit
        or value.get("genome_sha256") != expected_genome_sha256
        or type(value.get("src_token")) is not str
        or not value["src_token"]
        or type(value.get("source_bytes_sha256")) is not str
        or _SHA256_RE.fullmatch(value["source_bytes_sha256"]) is None
    ):
        _artifact_invalid(f"{binding}: source/build evidence is invalid")
    return value


def _measurement_value(row: dict, *, binding: str) -> float | None:
    value = row.get("median_tps")
    valid = (
        type(value) in {int, float}
        and math.isfinite(value)
        and value > 0
    )
    missing_reason = row.get("missing_reason")
    if valid:
        if missing_reason is not None:
            _artifact_invalid(
                f"{binding}: measured median_tps conflicts with missing_reason"
            )
        return float(value)
    if type(missing_reason) is not str or not missing_reason.strip():
        _artifact_invalid(
            f"{binding}: missing/nonpositive/nonfinite median_tps needs a reason"
        )
    return None


def _validate_row(
    row: object,
    *,
    document: dict,
    rep_index: int,
    seed: int,
    index: int,
) -> dict:
    binding = f"rep_index={rep_index}:cells[{index}]"
    if type(row) is not dict:
        _artifact_invalid(f"{binding}: measurement row must be an object")
    policy = row.get("step_policy")
    if type(policy) is not int or policy not in {0, 1, 2}:
        _artifact_invalid(f"{binding}: step_policy must be an exact integer 0..2")
    if not _matches_exact(row, _expected_cell_identity(policy)):
        _artifact_invalid(f"{binding}: arm identity is not the exact literal")
    workload = row.get("workload")
    threads = row.get("threads")
    if workload not in WORKLOADS or type(threads) is not int or threads not in THREADS:
        _artifact_invalid(f"{binding}: workload/threads are outside the exact axes")
    if row.get("workload_flags") != WORKLOAD_FLAGS[workload]:
        _artifact_invalid(f"{binding}: workload flags are not exact")
    expected_row = {
        "rep_index": rep_index,
        "cell_order": document["cell_order"],
        "throughput_scope": "performance",
        "backoff_trace": False,
        "backoff_trace_symbol_count": 0,
        "backoff_trace_string_count": 0,
        "build_trace_enabled": False,
        "repo_head": document["repo_head"],
        "driver_sha256": document["driver_sha256"],
        "pbs_sha256": document["pbs_sha256"],
        "repo_status_clean": True,
        "ccbench_head": CCBENCH_PIN,
        "patch_sha256": document["patch_sha256"],
        "dynamic_patch_sha256": document["dynamic_patch_sha256"],
        "counterfactual_patch_sha256": document[
            "counterfactual_patch_sha256"
        ],
        "patch_stack": document["patch_stack"],
        "patch_stack_sha256": document["patch_stack_sha256"],
    }
    if not _matches_exact(row, expected_row):
        _artifact_invalid(f"{binding}: row/artifact structural binding mismatch")
    if policy == 2:
        if not _exact_int(row.get("step_policy_seed"), seed):
            _artifact_invalid(f"{binding}: p2 seed does not match its block slot")
    elif "step_policy_seed" in row:
        _artifact_invalid(f"{binding}: p0/p1 must not record a variable row seed")
    genome = _validate_genome(
        row.get("genome"), policy=policy, seed=seed, binding=binding
    )
    binary_sha256 = row.get("binary_sha256")
    build_cache_key = row.get("build_cache_key")
    admission_sha256 = row.get("build_admission_receipt_sha256")
    if type(binary_sha256) is not str or _SHA256_RE.fullmatch(binary_sha256) is None:
        _artifact_invalid(f"{binding}: binary_sha256 identity is invalid")
    if (
        type(build_cache_key) is not str
        or not build_cache_key
        or not build_cache_key.endswith("_t0")
    ):
        _artifact_invalid(f"{binding}: trace-disabled build cache identity is invalid")
    if (
        type(admission_sha256) is not str
        or _SHA256_RE.fullmatch(admission_sha256) is None
    ):
        _artifact_invalid(f"{binding}: build admission receipt is invalid")
    source_evidence = _validate_source_evidence(
        row.get("source_evidence"),
        genome=genome,
        ccbench_commit=document["ccbench_commit"],
        binding=binding,
    )
    return {
        "policy": policy,
        "workload": workload,
        "threads": threads,
        "median_tps": _measurement_value(row, binding=binding),
        "genome": genome,
        "binary_sha256": binary_sha256,
        "build_cache_key": build_cache_key,
        "build_admission_receipt_sha256": admission_sha256,
        "source_evidence": source_evidence,
    }


def _validate_artifact(path: Path, document: dict) -> dict:
    binding = str(path)
    rep_index = document.get("rep_index")
    if type(rep_index) is not int or not 0 <= rep_index < BLOCK_COUNT:
        _artifact_invalid(f"{binding}: rep_index must be an exact integer 0..17")
    seed = PREREGISTERED_SEEDS[rep_index]
    permutation = PREREGISTERED_CELL_PERMUTATIONS[rep_index % 6]
    labels = [cell.split(":", 1)[0] for cell in permutation]
    exact_top_level = {
        "schema_version": SCHEMA_VERSION,
        "kind": "performance-only-probe",
        "not_certified": NOT_CERTIFIED,
        "headline_eligible": False,
        "correctness_status": "uncertified",
        "throughput_scope": "performance",
        "performance_contract": PERFORMANCE_CONTRACT,
        "backoff_policy_performance_prereg_sha256": PREREGISTRATION_SHA256,
        "records": 1_000_000,
        "extime_s": 3,
        "reps_per_job": 1,
        "stage": 1,
        "grid_spec": ",".join(permutation),
        "cell_order": labels,
        "rep_index": rep_index,
        "step_policy_seed": seed,
        "use_perf": False,
    }
    if not _matches_exact(document, exact_top_level):
        _artifact_invalid(f"{binding}: top-level performance contract mismatch")
    execution_identity = _validate_execution_identity(document, binding=binding)
    rows_raw = document.get("cells")
    if type(rows_raw) is not list:
        _artifact_invalid(f"{binding}: cells must be a list")
    rows = {}
    policy_builds: dict[int, tuple] = {}
    policy_source_bytes = {}
    policy_source_common = {}
    for index, raw_row in enumerate(rows_raw):
        row = _validate_row(
            raw_row,
            document=document,
            rep_index=rep_index,
            seed=seed,
            index=index,
        )
        key = (row["policy"], row["workload"], row["threads"])
        if key in rows:
            _artifact_invalid(f"{binding}: duplicate measurement coordinate {key}")
        rows[key] = row
        build_identity = (
            row["genome"],
            row["binary_sha256"],
            row["build_cache_key"],
            row["build_admission_receipt_sha256"],
            json.dumps(row["source_evidence"], sort_keys=True, separators=(",", ":")),
        )
        previous = policy_builds.setdefault(row["policy"], build_identity)
        if previous != build_identity:
            _artifact_invalid(
                f"{binding}: one arm changes build identity within a block"
            )
        evidence = row["source_evidence"]
        policy_source_bytes[row["policy"]] = evidence["source_bytes_sha256"]
        source_common = {
            key: value
            for key, value in evidence.items()
            if key
            not in {"genome_sha256", "src_token", "source_bytes_sha256"}
        }
        policy_source_common[row["policy"]] = json.dumps(
            source_common, sort_keys=True, separators=(",", ":")
        )
    if set(rows) != _EXPECTED_COORDINATES:
        missing = sorted(_EXPECTED_COORDINATES - set(rows))
        extra = sorted(set(rows) - _EXPECTED_COORDINATES)
        _artifact_invalid(
            f"{binding}: coordinate set is not exact; missing={missing} extra={extra}"
        )
    policy_identities = {
        "source_bytes_sha256": policy_source_bytes,
        "genome": {policy: policy_builds[policy][0] for policy in range(3)},
        "binary_sha256": {
            policy: policy_builds[policy][1] for policy in range(3)
        },
    }
    for identity_name, identities in policy_identities.items():
        if len(set(identities.values())) != 3:
            _artifact_invalid(
                f"{binding}: step policy define appears inert: "
                f"{identity_name} is not distinct between policy arms"
            )
    if len(set(policy_source_common.values())) != 1:
        _artifact_invalid(
            f"{binding}: source/build evidence differs outside the allowlist"
        )
    return {
        "rep_index": rep_index,
        "rows": rows,
        "execution_identity": execution_identity,
        "fixed_arm_identities": {
            policy: (policy_builds[policy][0], policy_source_bytes[policy])
            for policy in (0, 1)
        },
    }


def _classify_interval(lower: float, upper: float) -> str:
    margin = EQUIVALENCE_MARGIN_LOG
    if lower > margin:
        return "practical_superiority"
    if upper < -margin:
        return "practical_degradation"
    if lower > -margin and upper < margin:
        return "equivalent"
    if lower > -margin:
        return "non_inferior"
    return "inconclusive"


def _point_result(
    artifacts: dict[int, dict],
    *,
    left: str,
    right: str,
    workload: str,
    threads: int,
) -> dict:
    left_policy = int(left[1:])
    right_policy = int(right[1:])
    log_ratios = []
    missing_rep_indices = []
    for rep_index in range(BLOCK_COUNT):
        artifact = artifacts.get(rep_index)
        if artifact is None:
            missing_rep_indices.append(rep_index)
            continue
        left_value = artifact["rows"][(left_policy, workload, threads)][
            "median_tps"
        ]
        right_value = artifact["rows"][(right_policy, workload, threads)][
            "median_tps"
        ]
        if left_value is None or right_value is None:
            missing_rep_indices.append(rep_index)
            continue
        log_ratios.append(
            {"rep_index": rep_index, "log_ratio": math.log(left_value / right_value)}
        )
    common = {
        "workload": workload,
        "threads": threads,
        "n": len(log_ratios),
        "df": DF,
        "missing_rep_indices": missing_rep_indices,
        "block_log_ratios": log_ratios,
    }
    if missing_rep_indices:
        return {
            **common,
            "estimate_log": None,
            "effect_percent": None,
            "sample_sd": None,
            "standard_error": None,
            "ci95": None,
            "decision": "inconclusive",
            "reason": "n-insufficient",
        }
    values = [item["log_ratio"] for item in log_ratios]
    estimate = statistics.fmean(values)
    sample_sd = statistics.stdev(values)
    standard_error = sample_sd / math.sqrt(BLOCK_COUNT)
    half_width = T95_DF17 * standard_error
    lower = estimate - half_width
    upper = estimate + half_width
    return {
        **common,
        "estimate_log": estimate,
        "effect_percent": 100.0 * math.expm1(estimate),
        "sample_sd": sample_sd,
        "standard_error": standard_error,
        "ci95": {
            "lower_log": lower,
            "upper_log": upper,
            "half_width_log": half_width,
            "lower_percent": 100.0 * math.expm1(lower),
            "upper_percent": 100.0 * math.expm1(upper),
            "critical_value": T95_DF17,
        },
        "decision": _classify_interval(lower, upper),
        "reason": None,
    }


def _lookup_point(contrasts: dict, contrast: str, workload: str, threads: int) -> dict:
    return next(
        point
        for point in contrasts[contrast]["points"]
        if point["workload"] == workload and point["threads"] == threads
    )


def _incomplete_hypothesis(points: list[dict]) -> dict:
    missing = sorted(
        {
            rep_index
            for point in points
            for rep_index in point["missing_rep_indices"]
        }
    )
    return {
        "decision": "inconclusive",
        "reason": "incomplete-analysis",
        "missing_rep_indices": missing,
    }


def _hypotheses(contrasts: dict) -> dict:
    margin = EQUIVALENCE_MARGIN_LOG
    h1_point = _lookup_point(contrasts, "p0/p1", *PRIMARY_POINT)
    if h1_point["ci95"] is None:
        h1 = _incomplete_hypothesis([h1_point])
    elif h1_point["ci95"]["lower_log"] > margin:
        h1 = {"decision": "accepted", "reason": None, "missing_rep_indices": []}
    elif h1_point["ci95"]["upper_log"] <= margin:
        h1 = {"decision": "rejected", "reason": None, "missing_rep_indices": []}
    else:
        h1 = {
            "decision": "inconclusive",
            "reason": None,
            "missing_rep_indices": [],
        }

    h2_points = [
        point
        for contrast in ("p0/p2", "p2/p1")
        for point in contrasts[contrast]["points"]
    ]
    complete_h2 = [point for point in h2_points if point["ci95"] is not None]
    if any(point["ci95"]["upper_log"] < -margin for point in complete_h2):
        h2 = {"decision": "rejected", "reason": None, "missing_rep_indices": []}
    elif len(complete_h2) != len(h2_points):
        h2 = _incomplete_hypothesis(h2_points)
    elif all(point["ci95"]["lower_log"] > -margin for point in h2_points):
        h2 = {"decision": "accepted", "reason": None, "missing_rep_indices": []}
    else:
        h2 = {
            "decision": "inconclusive",
            "reason": None,
            "missing_rep_indices": [],
        }

    h3_points = [
        point
        for point in contrasts["p0/p1"]["points"]
        if point["workload"] == "read-heavy"
    ]
    complete_h3 = [point for point in h3_points if point["ci95"] is not None]
    if any(
        point["ci95"]["upper_log"] < -margin
        or point["ci95"]["lower_log"] > margin
        for point in complete_h3
    ):
        h3 = {"decision": "rejected", "reason": None, "missing_rep_indices": []}
    elif len(complete_h3) != len(h3_points):
        h3 = _incomplete_hypothesis(h3_points)
    elif all(
        point["ci95"]["lower_log"] > -margin
        and point["ci95"]["upper_log"] < margin
        for point in h3_points
    ):
        h3 = {"decision": "accepted", "reason": None, "missing_rep_indices": []}
    else:
        h3 = {
            "decision": "inconclusive",
            "reason": None,
            "missing_rep_indices": [],
        }
    return {"H1": h1, "H2": h2, "H3": h3}


def analyze_policy_performance(
    performance_paths: list[Path],
    preregistration_path: Path,
    preregistration_erratum_1_path: Path,
) -> dict:
    """Validate explicit performance artifacts and apply the frozen analysis."""
    if type(performance_paths) is not list:
        raise TypeError("performance_paths must be a list of Path objects")
    if len(performance_paths) > BLOCK_COUNT or any(
        not isinstance(path, Path) for path in performance_paths
    ):
        raise ValueError("performance_paths must contain at most 18 Path objects")
    if not isinstance(preregistration_path, Path):
        raise TypeError("preregistration_path must be a Path")
    if not isinstance(preregistration_erratum_1_path, Path):
        raise TypeError("preregistration_erratum_1_path must be a Path")
    try:
        preregistration = preregistration_path.resolve(strict=True)
        preregistration_sha256 = _sha256(preregistration)
    except OSError as exc:
        raise ValueError(f"preregistration file is unavailable: {exc}") from exc
    if preregistration_sha256 != PREREGISTRATION_SHA256:
        raise ValueError(
            "preregistration file SHA-256 does not match the frozen specification"
        )
    try:
        preregistration_erratum_1 = preregistration_erratum_1_path.resolve(
            strict=True
        )
        preregistration_erratum_1_sha256 = _sha256(preregistration_erratum_1)
    except OSError as exc:
        raise ValueError(
            f"preregistration erratum 1 file is unavailable: {exc}"
        ) from exc
    if preregistration_erratum_1_sha256 != PREREGISTRATION_ERRATUM_1_SHA256:
        raise ValueError(
            "preregistration erratum 1 file SHA-256 does not match the frozen "
            "specification"
        )
    try:
        resolved_paths = [path.resolve(strict=True) for path in performance_paths]
    except OSError as exc:
        _artifact_invalid(f"performance artifact is unavailable: {exc}")
    if len(set(resolved_paths)) != len(resolved_paths):
        _artifact_invalid("performance paths must identify unique resolved files")

    loaded = []
    for path in sorted(resolved_paths, key=str):
        document = _load_json(path)
        artifact = _validate_artifact(path, document)
        loaded.append(
            {
                **artifact,
                "path": str(path),
                "sha256": _sha256(path),
            }
        )
    by_rep = {}
    for artifact in loaded:
        rep_index = artifact["rep_index"]
        if rep_index in by_rep:
            _artifact_invalid(f"duplicate rep_index {rep_index}")
        by_rep[rep_index] = artifact
    if loaded:
        expected_execution_identity = loaded[0]["execution_identity"]
        for artifact in loaded[1:]:
            if artifact["execution_identity"] != expected_execution_identity:
                _artifact_invalid(
                    "repo/driver/PBS/ccbench/patch/compiler identity differs "
                    "between blocks"
                )
        for policy in (0, 1):
            expected_fixed_identity = loaded[0]["fixed_arm_identities"][policy]
            if any(
                artifact["fixed_arm_identities"][policy]
                != expected_fixed_identity
                for artifact in loaded[1:]
            ):
                _artifact_invalid(
                    f"p{policy} genome or source bytes identity differs between "
                    "blocks"
                )

    contrasts = {}
    for left, right in CONTRASTS:
        name = f"{left}/{right}"
        contrasts[name] = {
            "left": left,
            "right": right,
            "points": [
                _point_result(
                    by_rep,
                    left=left,
                    right=right,
                    workload=workload,
                    threads=threads,
                )
                for workload in WORKLOADS
                for threads in THREADS
            ],
        }
    incomplete = any(
        point["reason"] == "n-insufficient"
        for contrast in contrasts.values()
        for point in contrast["points"]
    )
    present_rep_indices = sorted(by_rep)
    missing_rep_indices = sorted(set(range(BLOCK_COUNT)) - set(by_rep))
    return {
        "analysis_version": ANALYSIS_VERSION,
        "analysis_status": "incomplete-analysis" if incomplete else "complete",
        "headline_eligible": False,
        "correctness_status": "uncertified",
        "reason_codes": ["incomplete-analysis"] if incomplete else [],
        "preregistration": {
            "path": str(preregistration),
            "sha256": preregistration_sha256,
        },
        "preregistration_erratum_1": {
            "path": str(preregistration_erratum_1),
            "sha256": preregistration_erratum_1_sha256,
        },
        "inputs": [
            {
                "path": artifact["path"],
                "sha256": artifact["sha256"],
                "rep_index": artifact["rep_index"],
            }
            for artifact in sorted(loaded, key=lambda item: item["rep_index"])
        ],
        "blocks": {
            "required": BLOCK_COUNT,
            "present_rep_indices": present_rep_indices,
            "missing_rep_indices": missing_rep_indices,
        },
        "equivalence_margin_log": EQUIVALENCE_MARGIN_LOG,
        "contrasts": contrasts,
        "hypotheses": _hypotheses(contrasts),
    }
