from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.campaign import backoff_policy_performance_analysis as analysis


ROOT = Path(__file__).resolve().parents[2]
PREREGISTRATION = ROOT / "docs" / "backoff-policy-performance-preregistration.md"
PREREGISTRATION_ERRATUM_1 = Path(
    os.environ.get(
        "IZANAGI_BACKOFF_POLICY_PERFORMANCE_ERRATUM_1",
        ROOT / "docs" / "backoff-policy-performance-preregistration-erratum-1.md",
    )
)
PREREGISTRATION_SHA256 = (
    "2f5170c99dda9dd70647a611bff798b6e54c5e29b60e872cd755e5b8515cc25c"
)
PREREGISTRATION_ERRATUM_1_SHA256 = (
    "9f81a61b92e88a7dcede8a779c0241c7bcbc96b00ef01332b8df8e7ed5ec3eea"
)
SCHEMA_VERSION = "izanagi-cicada-adaptive-3const-probe/v3"
NOT_CERTIFIED = (
    "trace-disabled performance runs only; no serializability check was run"
)
CCBENCH_PIN = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
DEFAULT_STEP_POLICY_SEED = 11_400_714_819_323_198_485
ARMS = (
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0",
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1",
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2",
)
PERMUTATIONS = (
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
SEEDS = (
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
PATCH_PATHS = (
    "patches/cicada-adaptive-params.patch",
    "patches/cicada-adaptive-dynamic.patch",
    "patches/cicada-adaptive-counterfactual.patch",
)
PATCH_HASHES = tuple(
    hashlib.sha256(f"test-patch-{index}".encode()).hexdigest()
    for index in range(3)
)


def _patch_identity(hashes: tuple[str, str, str] = PATCH_HASHES) -> dict:
    stack = [
        {"path": path, "sha256": sha256}
        for path, sha256 in zip(PATCH_PATHS, hashes, strict=True)
    ]
    encoded = "izanagi-patch-stack/v1\n" + "".join(
        f"{entry['path']} {entry['sha256']}\n" for entry in stack
    )
    return {
        "patch_sha256": hashes[0],
        "dynamic_patch_sha256": hashes[1],
        "counterfactual_patch_sha256": hashes[2],
        "patch_stack": stack,
        "patch_stack_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
    }


def _genome(policy: int, seed: int) -> str:
    flags = {
        "NO_WAIT_LOCKING_IN_VALIDATION": 1,
        "NO_WAIT_OF_TICTOC": 0,
        "WAL": 0,
        "BACK_OFF": 1,
        "BACKOFF_INCR_MILLI": 1000,
        "BACKOFF_MAX_US": 1000,
        "BACKOFF_UPDATE_US": 2560,
        "BACKOFF_COUNT_WINDOW": 10000,
        "BACKOFF_COUNT_CAP_US": 10240,
        "BACKOFF_STEP_ADAPT": 1,
        "BACKOFF_STEP_MIN_MILLI": 1000,
        "BACKOFF_STEP_MAX_MILLI": 4000,
        "BACKOFF_DYN_CEILING": 1,
        "BACKOFF_TRACE": 0,
        "BACKOFF_STEP_POLICY": policy,
        "BACKOFF_STEP_POLICY_SEED": (
            seed if policy == 2 else DEFAULT_STEP_POLICY_SEED
        ),
    }
    return "silo|" + ",".join(
        f"{name}={value}" for name, value in sorted(flags.items())
    )


def _cell_identity(policy: int) -> dict:
    return {
        "cell": f"cw-as-dyn-p{policy}",
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


def _build_row(
    *,
    policy: int,
    workload: str,
    threads: int,
    rep_index: int,
    cell_order: list[str],
    top_identity: dict,
    median_tps: float,
) -> dict:
    seed = SEEDS[rep_index]
    genome = _genome(policy, seed)
    fixed_seed = seed if policy == 2 else "fixed"
    source_evidence = {
        "ccbench_commit": "511c9538e",
        "genome_sha256": hashlib.sha256(genome.encode()).hexdigest(),
        "src_token": hashlib.sha256(
            f"src-token-{policy}-{fixed_seed}".encode()
        ).hexdigest(),
        "source_bytes_sha256": hashlib.sha256(
            f"source-bytes-{policy}-{fixed_seed}".encode()
        ).hexdigest(),
    }
    row = {
        **_cell_identity(policy),
        "hostname": f"node-{rep_index:02d}",
        "repo_head": top_identity["repo_head"],
        "driver_sha256": top_identity["driver_sha256"],
        "pbs_sha256": top_identity["pbs_sha256"],
        "driver_argv": list(top_identity["driver_argv"]),
        "repo_status_clean": True,
        "ccbench_head": CCBENCH_PIN,
        **copy.deepcopy(_patch_identity()),
        "rep_index": rep_index,
        "cell_order": cell_order,
        "workload": workload,
        "workload_flags": copy.deepcopy(WORKLOAD_FLAGS[workload]),
        "threads": threads,
        "genome": genome,
        "binary_sha256": hashlib.sha256(
            f"binary-{rep_index}-{policy}-{fixed_seed}".encode()
        ).hexdigest(),
        "build_trace_enabled": False,
        "build_cache_key": f"build-{policy}-{fixed_seed}_t0",
        "build_admission_receipt_sha256": hashlib.sha256(
            f"admission-{policy}-{fixed_seed}".encode()
        ).hexdigest(),
        "source_evidence": source_evidence,
        "backoff_trace_symbol_count": 0,
        "backoff_trace_string_count": 0,
        "backoff_trace": False,
        "throughput_scope": "performance",
        "throughputs": [median_tps],
        "median_tps": median_tps,
        "abort_rate": 0.125,
    }
    if policy == 2:
        row["step_policy_seed"] = seed
    return row


def _write_artifacts(
    directory: Path,
    *,
    value_for=None,
) -> list[Path]:
    directory.mkdir()
    value_for = value_for or (
        lambda _rep_index, _policy, _workload, _threads: 1_000_000.0
    )
    paths = []
    for rep_index, seed in enumerate(SEEDS):
        permutation = PERMUTATIONS[rep_index % 6]
        cell_order = [literal.split(":", 1)[0] for literal in permutation]
        top_identity = {
            "repo_head": "a" * 40,
            "driver_sha256": hashlib.sha256(b"driver").hexdigest(),
            "pbs_sha256": hashlib.sha256(b"pbs").hexdigest(),
            "driver_argv": ["probe.py", "--mode", "performance"],
        }
        rows = [
            _build_row(
                policy=policy,
                workload=workload,
                threads=threads,
                rep_index=rep_index,
                cell_order=cell_order,
                top_identity=top_identity,
                median_tps=value_for(rep_index, policy, workload, threads),
            )
            for workload in WORKLOADS
            for threads in THREADS
            for policy in range(3)
        ]
        document = {
            "schema_version": SCHEMA_VERSION,
            "kind": "performance-only-probe",
            "not_certified": NOT_CERTIFIED,
            "headline_eligible": False,
            "correctness_status": "uncertified",
            "throughput_scope": "performance",
            "performance_contract": "backoff-policy-arm-perf/v1",
            "backoff_policy_performance_prereg_sha256": (
                PREREGISTRATION_SHA256
            ),
            "stage": 1,
            "grid_spec": ",".join(permutation),
            "cell_order": cell_order,
            "host": f"node-{rep_index:02d}",
            "hostname": f"node-{rep_index:02d}",
            "repo_head": top_identity["repo_head"],
            "rep_index": rep_index,
            "records": 1_000_000,
            "extime_s": 3,
            "reps_per_job": 1,
            "use_perf": False,
            "ccbench_commit": "511c9538e",
            "ccbench_head": CCBENCH_PIN,
            **top_identity,
            "repo_status_clean": True,
            "cc": "/usr/bin/gcc",
            "cxx": "/usr/bin/g++",
            **_patch_identity(),
            "step_policy_seed": seed,
            "cells": rows,
        }
        path = directory / f"rep-{rep_index:02d}.json"
        path.write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")


def _rewrite(path: Path, mutate) -> None:
    document = _read(path)
    mutate(document)
    _write(path, document)


def _row(document: dict, policy: int, workload: str, threads: int) -> dict:
    return next(
        row
        for row in document["cells"]
        if row["step_policy"] == policy
        and row["workload"] == workload
        and row["threads"] == threads
    )


def _point(result: dict, contrast: str, workload: str, threads: int) -> dict:
    return next(
        point
        for point in result["contrasts"][contrast]["points"]
        if point["workload"] == workload and point["threads"] == threads
    )


def test_contract_literals_are_independently_pinned() -> None:
    assert analysis.__all__ == ["analyze_policy_performance"]
    assert analysis.BLOCK_COUNT == 18
    assert analysis.DF == 17
    assert analysis.T95_DF17 == 2.1098156
    assert analysis.EQUIVALENCE_MARGIN_LOG == 0.02955880224154443
    assert analysis.PREREGISTRATION_SHA256 == PREREGISTRATION_SHA256
    assert (
        analysis.PREREGISTRATION_ERRATUM_1_SHA256
        == PREREGISTRATION_ERRATUM_1_SHA256
    )
    assert tuple(analysis.CELL_LITERALS[f"p{index}"] for index in range(3)) == ARMS
    assert analysis.PREREGISTERED_CELL_PERMUTATIONS == PERMUTATIONS
    assert analysis.PREREGISTERED_SEEDS == SEEDS
    assert analysis.WORKLOADS == WORKLOADS
    assert analysis.THREADS == THREADS


def test_public_analysis_accepts_real_identity_shape_and_uses_frozen_ci(
    tmp_path: Path,
) -> None:
    effects = [(-0.017 + index * 0.0031) for index in range(18)]

    def values(rep_index: int, policy: int, workload: str, threads: int) -> float:
        if policy == 0 and (workload, threads) == ("write-heavy", 48):
            return 1_000_000.0 * math.exp(effects[rep_index])
        return 1_000_000.0

    paths = _write_artifacts(tmp_path / "artifacts", value_for=values)
    documents = [_read(path) for path in paths]
    for document in documents:
        assert len(
            {
                _row(document, policy, "write-heavy", 6)["source_evidence"][
                    "source_bytes_sha256"
                ]
                for policy in range(3)
            }
        ) == 3
        assert len(
            {
                _row(document, policy, "write-heavy", 6)["genome"]
                for policy in range(3)
            }
        ) == 3
        assert len(
            {
                _row(document, policy, "write-heavy", 6)["binary_sha256"]
                for policy in range(3)
            }
        ) == 3
    for policy in (0, 1):
        assert len(
            {
                _row(document, policy, "write-heavy", 6)["genome"]
                for document in documents
            }
        ) == 1
        assert len(
            {
                _row(document, policy, "write-heavy", 6)["source_evidence"][
                    "source_bytes_sha256"
                ]
                for document in documents
            }
        ) == 1
        assert len(
            {
                _row(document, policy, "write-heavy", 6)["binary_sha256"]
                for document in documents
            }
        ) == 18
    result = analysis.analyze_policy_performance(
        paths, PREREGISTRATION, PREREGISTRATION_ERRATUM_1
    )
    point = _point(result, "p0/p1", "write-heavy", 48)
    observed = [item["log_ratio"] for item in point["block_log_ratios"]]
    expected_mean = sum(effects) / 18
    expected_sd = math.sqrt(
        sum((effect - expected_mean) ** 2 for effect in effects) / 17
    )
    expected_se = expected_sd / math.sqrt(18)
    expected_half = 2.1098156 * expected_se

    assert observed == pytest.approx(effects, abs=1e-15)
    assert point["n"] == 18
    assert point["df"] == 17
    assert point["estimate_log"] == pytest.approx(expected_mean)
    assert point["sample_sd"] == pytest.approx(expected_sd)
    assert point["standard_error"] == pytest.approx(expected_se)
    assert point["ci95"]["lower_log"] == pytest.approx(
        expected_mean - expected_half
    )
    assert point["ci95"]["upper_log"] == pytest.approx(
        expected_mean + expected_half
    )
    assert point["effect_percent"] == pytest.approx(
        100.0 * math.expm1(expected_mean)
    )
    assert result["analysis_status"] == "complete"
    assert result["headline_eligible"] is False
    assert result["correctness_status"] == "uncertified"
    assert result["blocks"]["present_rep_indices"] == list(range(18))
    assert result["preregistration_erratum_1"]["sha256"] == (
        PREREGISTRATION_ERRATUM_1_SHA256
    )
    assert result == analysis.analyze_policy_performance(
        list(reversed(paths)), PREREGISTRATION, PREREGISTRATION_ERRATUM_1
    )
    assert "abort_rate" not in json.dumps(result)


def test_equivalence_behavior_depends_on_frozen_95_percent_critical_and_margin(
    tmp_path: Path,
) -> None:
    target_half_width = 0.0294
    amplitude = target_half_width * math.sqrt(17) / 2.1098156
    effects = [-amplitude] * 9 + [amplitude] * 9

    def values(rep_index: int, policy: int, workload: str, threads: int) -> float:
        if policy == 0 and (workload, threads) == ("balanced", 24):
            return 1_000_000.0 * math.exp(effects[rep_index])
        return 1_000_000.0

    paths = _write_artifacts(tmp_path / "artifacts", value_for=values)
    point = _point(
        analysis.analyze_policy_performance(
            paths, PREREGISTRATION, PREREGISTRATION_ERRATUM_1
        ),
        "p0/p1",
        "balanced",
        24,
    )
    expected_mean = sum(effects) / 18
    expected_sd = math.sqrt(
        sum((effect - expected_mean) ** 2 for effect in effects) / 17
    )
    expected_se = expected_sd / math.sqrt(18)
    frozen_half_width = 2.1098156 * expected_se

    assert frozen_half_width < 0.02955880224154443
    assert point["decision"] == "equivalent"
    assert 2.2 * expected_se > 0.02955880224154443
    assert frozen_half_width > 0.029


@pytest.mark.parametrize(
    ("lower", "upper", "expected"),
    (
        (0.04, 0.05, "practical_superiority"),
        (-0.02, 0.04, "non_inferior"),
        (-0.01, 0.01, "equivalent"),
        (-0.05, -0.04, "practical_degradation"),
        (-0.04, 0.01, "inconclusive"),
        (0.02955880224154443, 0.04, "non_inferior"),
        (-0.02955880224154443, 0.0, "inconclusive"),
        (-0.04, -0.02955880224154443, "inconclusive"),
        (-0.01, 0.02955880224154443, "non_inferior"),
    ),
)
def test_decision_vocabulary_and_strict_boundaries(
    lower: float, upper: float, expected: str
) -> None:
    assert analysis._classify_interval(lower, upper) == expected


def test_hypotheses_return_preregistered_three_way_decisions(tmp_path: Path) -> None:
    def values(_rep_index: int, policy: int, workload: str, threads: int) -> float:
        effects = {0: 0.0, 1: 0.0, 2: 0.0}
        if (workload, threads) == ("write-heavy", 48):
            effects = {0: 0.05, 1: 0.0, 2: 0.05}
        elif (workload, threads) == ("balanced", 6):
            effects = {0: -0.04, 1: 0.0, 2: 0.0}
        elif (workload, threads) == ("read-heavy", 6):
            effects = {0: 0.04, 1: 0.0, 2: 0.04}
        return 1_000_000.0 * math.exp(effects[policy])

    paths = _write_artifacts(tmp_path / "artifacts", value_for=values)
    result = analysis.analyze_policy_performance(
        paths, PREREGISTRATION, PREREGISTRATION_ERRATUM_1
    )
    assert result["hypotheses"]["H1"]["decision"] == "accepted"
    assert result["hypotheses"]["H2"]["decision"] == "rejected"
    assert result["hypotheses"]["H3"]["decision"] == "rejected"

    baseline = _write_artifacts(tmp_path / "baseline")
    baseline_result = analysis.analyze_policy_performance(
        baseline, PREREGISTRATION, PREREGISTRATION_ERRATUM_1
    )
    assert baseline_result["hypotheses"]["H1"]["decision"] == "rejected"
    assert baseline_result["hypotheses"]["H2"]["decision"] == "accepted"
    assert baseline_result["hypotheses"]["H3"]["decision"] == "accepted"


def test_h3_aggregate_boundary_contact_is_inconclusive_not_rejected() -> None:
    margin = 0.02955880224154443

    def contrasts_with_boundary(lower: float, upper: float) -> dict:
        def points(name: str) -> list[dict]:
            result = []
            for workload in WORKLOADS:
                for threads in THREADS:
                    point_lower, point_upper = -0.001, 0.001
                    if (
                        name == "p0/p1"
                        and workload == "read-heavy"
                        and threads == 6
                    ):
                        point_lower, point_upper = lower, upper
                    result.append(
                        {
                            "workload": workload,
                            "threads": threads,
                            "ci95": {
                                "lower_log": point_lower,
                                "upper_log": point_upper,
                            },
                            "missing_rep_indices": [],
                        }
                    )
            return result

        return {
            name: {"points": points(name)}
            for name in ("p0/p1", "p0/p2", "p2/p1")
        }

    for lower, upper in ((margin, 0.04), (-0.04, -margin)):
        hypotheses = analysis._hypotheses(contrasts_with_boundary(lower, upper))
        assert hypotheses["H3"] == {
            "decision": "inconclusive",
            "reason": None,
            "missing_rep_indices": [],
        }


def test_one_reasoned_missing_coordinate_is_local_not_artifact_invalid(
    tmp_path: Path,
) -> None:
    paths = _write_artifacts(tmp_path / "artifacts")

    def make_missing(document: dict) -> None:
        row = _row(document, 0, "balanced", 12)
        row.pop("median_tps")
        row["throughputs"] = []
        row["missing_reason"] = "timeout"

    _rewrite(paths[4], make_missing)
    result = analysis.analyze_policy_performance(
        paths, PREREGISTRATION, PREREGISTRATION_ERRATUM_1
    )
    p0_p1 = _point(result, "p0/p1", "balanced", 12)
    p0_p2 = _point(result, "p0/p2", "balanced", 12)
    p2_p1 = _point(result, "p2/p1", "balanced", 12)
    unaffected = _point(result, "p0/p1", "balanced", 18)

    assert result["analysis_status"] == "incomplete-analysis"
    assert result["reason_codes"] == ["incomplete-analysis"]
    assert p0_p1["decision"] == p0_p2["decision"] == "inconclusive"
    assert p0_p1["reason"] == p0_p2["reason"] == "n-insufficient"
    assert p0_p1["missing_rep_indices"] == p0_p2["missing_rep_indices"] == [4]
    assert p0_p1["n"] == p0_p2["n"] == 17
    assert p2_p1["decision"] == "equivalent"
    assert p2_p1["reason"] is None
    assert unaffected["decision"] == "equivalent"
    assert result["hypotheses"]["H2"] == {
        "decision": "inconclusive",
        "reason": "incomplete-analysis",
        "missing_rep_indices": [4],
    }
    assert result["hypotheses"]["H3"]["decision"] == "accepted"


def test_absent_block_is_pointwise_incomplete_and_lists_rep_index(
    tmp_path: Path,
) -> None:
    paths = _write_artifacts(tmp_path / "artifacts")
    result = analysis.analyze_policy_performance(
        paths[:-1], PREREGISTRATION, PREREGISTRATION_ERRATUM_1
    )

    assert result["blocks"]["missing_rep_indices"] == [17]
    for contrast in ("p0/p1", "p0/p2", "p2/p1"):
        point = _point(result, contrast, "write-heavy", 6)
        assert point["reason"] == "n-insufficient"
        assert point["missing_rep_indices"] == [17]
        assert point["estimate_log"] is None
        assert point["ci95"] is None
    assert all(
        hypothesis["decision"] == "inconclusive"
        and hypothesis["reason"] == "incomplete-analysis"
        for hypothesis in result["hypotheses"].values()
    )


def _mutate_structural_case(document: dict, case: str) -> None:
    row = _row(document, 0, "write-heavy", 6)
    if case == "schema":
        document["schema_version"] = "changed"
    elif case == "order-rep":
        document["cell_order"] = list(reversed(document["cell_order"]))
    elif case == "seed":
        document["step_policy_seed"] += 1
    elif case == "row-seed":
        _row(document, 2, "write-heavy", 6)["step_policy_seed"] += 1
    elif case == "rep-18":
        document["rep_index"] = 18
    elif case == "axis":
        row["threads"] = 7
    elif case == "workload-axis":
        row["workload"] = "unregistered"
    elif case == "records":
        document["records"] = 999_999
    elif case == "extime":
        document["extime_s"] = 4
    elif case == "reps-per-job":
        document["reps_per_job"] = 2
    elif case == "stage":
        document["stage"] = 2
    elif case == "kind":
        document["kind"] = "diagnostic-backoff-trace"
    elif case == "not-certified":
        document["not_certified"] = "changed"
    elif case == "throughput-scope":
        document["throughput_scope"] = "diagnostic_only"
    elif case == "row-throughput-scope":
        row["throughput_scope"] = "diagnostic_only"
    elif case == "workload-flags":
        row["workload_flags"]["ycsb_rratio"] = "50"
    elif case == "preregistration-sha":
        document["backoff_policy_performance_prereg_sha256"] = "0" * 64
    elif case == "trace-row":
        row["backoff_trace"] = True
    elif case == "trace-symbol":
        row["backoff_trace_symbol_count"] = 1
    elif case == "arm-literal":
        row["cell"] = "cw-as-dyn-p1"
    elif case == "build-trace-enabled":
        row["build_trace_enabled"] = True
    elif case == "build-allowlist":
        row["genome"] += ",UNREGISTERED_DEFINE=1"
        row["source_evidence"]["genome_sha256"] = hashlib.sha256(
            row["genome"].encode()
        ).hexdigest()
    elif case == "source-bytes":
        p0_source_bytes = _row(
            document, 0, "write-heavy", 6
        )["source_evidence"]["source_bytes_sha256"]
        for item in document["cells"]:
            if item["step_policy"] == 1:
                item["source_evidence"][
                    "source_bytes_sha256"
                ] = p0_source_bytes
    elif case == "binary-within-arm":
        row["binary_sha256"] = "f" * 64
    elif case == "coordinate":
        document["cells"].pop()
    else:
        raise AssertionError(case)


@pytest.mark.parametrize(
    "case",
    (
        "schema",
        "order-rep",
        "seed",
        "row-seed",
        "rep-18",
        "axis",
        "workload-axis",
        "records",
        "extime",
        "reps-per-job",
        "stage",
        "kind",
        "not-certified",
        "throughput-scope",
        "row-throughput-scope",
        "workload-flags",
        "preregistration-sha",
        "trace-row",
        "trace-symbol",
        "arm-literal",
        "build-trace-enabled",
        "build-allowlist",
        "source-bytes",
        "binary-within-arm",
        "coordinate",
    ),
)
def test_structural_contract_violations_are_artifact_invalid(
    tmp_path: Path, case: str
) -> None:
    paths = _write_artifacts(tmp_path / "artifacts")
    _rewrite(paths[0], lambda document: _mutate_structural_case(document, case))
    with pytest.raises(ValueError, match="artifact-invalid"):
        analysis.analyze_policy_performance(
            paths, PREREGISTRATION, PREREGISTRATION_ERRATUM_1
        )


def test_inert_policy_identity_and_duplicate_inputs_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def collide_arm_identity(document: dict, identity: str) -> None:
        source = _row(document, 0, "write-heavy", 6)
        for row in document["cells"]:
            if row["step_policy"] != 1:
                continue
            if identity == "source_bytes_sha256":
                row["source_evidence"][identity] = source["source_evidence"][
                    identity
                ]
            elif identity == "genome":
                row["genome"] = source["genome"]
                row["source_evidence"]["genome_sha256"] = hashlib.sha256(
                    row["genome"].encode()
                ).hexdigest()
            elif identity == "binary_sha256":
                row[identity] = source[identity]
            else:
                raise AssertionError(identity)

    for identity in ("source_bytes_sha256", "genome", "binary_sha256"):
        inert_paths = _write_artifacts(tmp_path / f"inert-{identity}")
        _rewrite(
            inert_paths[0],
            lambda document, identity=identity: collide_arm_identity(
                document, identity
            ),
        )
        with monkeypatch.context() as patcher:
            if identity == "genome":
                patcher.setattr(
                    analysis,
                    "_validate_genome",
                    lambda value, **_kwargs: value,
                )
            with pytest.raises(
                ValueError,
                match="artifact-invalid.*step policy define appears inert",
            ):
                analysis.analyze_policy_performance(
                    inert_paths, PREREGISTRATION, PREREGISTRATION_ERRATUM_1
                )

    ccbench_paths = _write_artifacts(tmp_path / "ccbench-arm-mismatch")

    def change_one_arm_ccbench(document: dict) -> None:
        for row in document["cells"]:
            if row["step_policy"] == 1:
                row["source_evidence"]["ccbench_commit"] = "511c9538e4"

    _rewrite(ccbench_paths[0], change_one_arm_ccbench)
    with monkeypatch.context() as patcher:
        patcher.setattr(
            analysis,
            "_validate_source_evidence",
            lambda value, **_kwargs: value,
        )
        with pytest.raises(
            ValueError,
            match="artifact-invalid.*differs outside the allowlist",
        ):
            analysis.analyze_policy_performance(
                ccbench_paths, PREREGISTRATION, PREREGISTRATION_ERRATUM_1
            )

    paths = _write_artifacts(tmp_path / "artifacts")
    paths[1].write_bytes(paths[0].read_bytes())
    with pytest.raises(ValueError, match="artifact-invalid.*duplicate rep_index"):
        analysis.analyze_policy_performance(
            paths, PREREGISTRATION, PREREGISTRATION_ERRATUM_1
        )

    fresh = _write_artifacts(tmp_path / "fresh")
    alias = tmp_path / "alias.json"
    alias.symlink_to(fresh[0])
    with pytest.raises(ValueError, match="artifact-invalid.*unique resolved"):
        analysis.analyze_policy_performance(
            [fresh[0], alias, *fresh[2:]],
            PREREGISTRATION,
            PREREGISTRATION_ERRATUM_1,
        )


def _replace_patch_identity(document: dict, hashes: tuple[str, str, str]) -> None:
    replacement = _patch_identity(hashes)
    for key, value in replacement.items():
        document[key] = copy.deepcopy(value)
        for row in document["cells"]:
            row[key] = copy.deepcopy(value)


def _mutate_block_identity(document: dict, case: str) -> None:
    if case == "repo-head":
        document["repo_head"] = "b" * 40
        for row in document["cells"]:
            row["repo_head"] = document["repo_head"]
    elif case in {"driver-sha", "pbs-sha"}:
        key = "driver_sha256" if case == "driver-sha" else "pbs_sha256"
        document[key] = "f" * 64
        for row in document["cells"]:
            row[key] = document[key]
    elif case == "ccbench-pin":
        document["ccbench_commit"] = "511c9538e4"
        for row in document["cells"]:
            row["source_evidence"]["ccbench_commit"] = document[
                "ccbench_commit"
            ]
    elif case == "patch-stack":
        hashes = ("e" * 64, PATCH_HASHES[1], PATCH_HASHES[2])
        _replace_patch_identity(document, hashes)
    elif case == "compiler":
        document["cc"] = "/different/gcc"
    elif case == "p0-binary":
        for row in document["cells"]:
            if row["step_policy"] == 0:
                row["binary_sha256"] = "f" * 64
    elif case == "p0-source":
        for row in document["cells"]:
            if row["step_policy"] == 0:
                row["source_evidence"]["source_bytes_sha256"] = "e" * 64
    elif case == "p0-genome":
        for row in document["cells"]:
            if row["step_policy"] == 0:
                row["genome"] += ",UNREGISTERED_DEFINE=1"
                row["source_evidence"]["genome_sha256"] = hashlib.sha256(
                    row["genome"].encode()
                ).hexdigest()
    else:
        raise AssertionError(case)


@pytest.mark.parametrize(
    "case",
    (
        "repo-head",
        "driver-sha",
        "pbs-sha",
        "ccbench-pin",
        "patch-stack",
        "compiler",
        "p0-binary",
    ),
)
def test_block_identity_contract_across_blocks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    paths = _write_artifacts(tmp_path / "artifacts")
    _rewrite(paths[1], lambda document: _mutate_block_identity(document, case))
    if case == "p0-binary":
        result = analysis.analyze_policy_performance(
            paths, PREREGISTRATION, PREREGISTRATION_ERRATUM_1
        )
        assert result["analysis_status"] == "complete"
        for identity in ("p0-genome", "p0-source"):
            mismatch_paths = _write_artifacts(tmp_path / identity)
            _rewrite(
                mismatch_paths[1],
                lambda document, identity=identity: _mutate_block_identity(
                    document, identity
                ),
            )
            with monkeypatch.context() as patcher:
                if identity == "p0-genome":
                    original_validate_genome = analysis._validate_genome

                    def accept_changed_p0_genome(
                        value: object,
                        *,
                        policy: int,
                        seed: int,
                        binding: str,
                    ) -> str:
                        if policy == 0 and isinstance(value, str) and value.endswith(
                            ",UNREGISTERED_DEFINE=1"
                        ):
                            return value
                        return original_validate_genome(
                            value,
                            policy=policy,
                            seed=seed,
                            binding=binding,
                        )

                    patcher.setattr(
                        analysis,
                        "_validate_genome",
                        accept_changed_p0_genome,
                    )
                with pytest.raises(
                    ValueError,
                    match=(
                        "artifact-invalid.*p0 genome or source bytes identity "
                        "differs between blocks"
                    ),
                ):
                    analysis.analyze_policy_performance(
                        mismatch_paths,
                        PREREGISTRATION,
                        PREREGISTRATION_ERRATUM_1,
                    )
        return
    with pytest.raises(ValueError, match="artifact-invalid"):
        analysis.analyze_policy_performance(
            paths, PREREGISTRATION, PREREGISTRATION_ERRATUM_1
        )


@pytest.mark.parametrize("value", (None, 0.0, -1.0, math.inf, math.nan))
def test_missing_nonpositive_and_nonfinite_tps_require_recorded_reason(
    tmp_path: Path, value: float | None
) -> None:
    paths = _write_artifacts(tmp_path / "artifacts")

    def mutate(document: dict) -> None:
        row = _row(document, 1, "read-heavy", 30)
        row["median_tps"] = value
        row["missing_reason"] = "measurement-unavailable"

    _rewrite(paths[3], mutate)
    result = analysis.analyze_policy_performance(
        paths, PREREGISTRATION, PREREGISTRATION_ERRATUM_1
    )
    point = _point(result, "p0/p1", "read-heavy", 30)
    assert point["reason"] == "n-insufficient"
    assert point["missing_rep_indices"] == [3]

    def remove_reason(document: dict) -> None:
        _row(document, 1, "read-heavy", 30).pop("missing_reason")

    _rewrite(paths[3], remove_reason)
    with pytest.raises(ValueError, match="artifact-invalid.*needs a reason"):
        analysis.analyze_policy_performance(
            paths, PREREGISTRATION, PREREGISTRATION_ERRATUM_1
        )


def test_preregistration_bytes_are_bound_to_frozen_sha256(tmp_path: Path) -> None:
    assert hashlib.sha256(PREREGISTRATION.read_bytes()).hexdigest() == (
        PREREGISTRATION_SHA256
    )
    assert hashlib.sha256(PREREGISTRATION_ERRATUM_1.read_bytes()).hexdigest() == (
        PREREGISTRATION_ERRATUM_1_SHA256
    )
    paths = _write_artifacts(tmp_path / "artifacts")
    changed = tmp_path / "changed-preregistration.md"
    changed.write_bytes(PREREGISTRATION.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="frozen specification"):
        analysis.analyze_policy_performance(
            paths, changed, PREREGISTRATION_ERRATUM_1
        )

    changed_erratum = tmp_path / "changed-erratum-1.md"
    erratum_bytes = PREREGISTRATION_ERRATUM_1.read_bytes()
    changed_erratum.write_bytes(b"!" + erratum_bytes[1:])
    with pytest.raises(ValueError, match="erratum 1.*frozen specification"):
        analysis.analyze_policy_performance(
            paths, PREREGISTRATION, changed_erratum
        )


def test_input_type_contract_and_empty_explicit_input(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="list of Path"):
        analysis.analyze_policy_performance(
            (),  # type: ignore[arg-type]
            PREREGISTRATION,
            PREREGISTRATION_ERRATUM_1,
        )
    with pytest.raises(TypeError, match="required positional argument"):
        analysis.analyze_policy_performance(  # type: ignore[call-arg]
            [], PREREGISTRATION
        )
    with pytest.raises(TypeError, match="must be a Path"):
        analysis.analyze_policy_performance(
            [],
            str(PREREGISTRATION),  # type: ignore[arg-type]
            PREREGISTRATION_ERRATUM_1,
        )
    with pytest.raises(TypeError, match="must be a Path"):
        analysis.analyze_policy_performance(
            [],
            PREREGISTRATION,
            str(PREREGISTRATION_ERRATUM_1),  # type: ignore[arg-type]
        )

    result = analysis.analyze_policy_performance(
        [], PREREGISTRATION, PREREGISTRATION_ERRATUM_1
    )
    assert result["analysis_status"] == "incomplete-analysis"
    assert result["headline_eligible"] is False
    assert result["correctness_status"] == "uncertified"
    assert result["blocks"]["missing_rep_indices"] == list(range(18))
    assert all(
        hypothesis["decision"] == "inconclusive"
        for hypothesis in result["hypotheses"].values()
    )


def _run() -> int:
    return int(pytest.main([__file__]))


if __name__ == "__main__":
    raise SystemExit(_run())
