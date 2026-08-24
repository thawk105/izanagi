from __future__ import annotations

import copy
import math
import statistics
from dataclasses import replace
from pathlib import Path

import pytest

from orchestrator.campaign import ident
from orchestrator.campaign import paper_story_a1_paired as paired


def _source_binding() -> dict:
    return {
        "measurement_source_commit": "a" * 40,
        "pipeline_path": paired.PIPELINE_RELATIVE_PATH,
        "pipeline_git_blob_oid": "b" * 40,
        "pipeline_source_sha256": "c" * 64,
        "evidence_level": "source-routed-trace0",
        "artifact_standalone_proof": False,
    }


def _frame(stage: str, variant: str, attempt_id: str, payload: dict) -> dict:
    return {
        "line_number": 1,
        "byte_start": 0,
        "byte_end": 1,
        "raw_sha256": "1" * 64,
        "variant": variant,
        "stage": stage,
        "env_tag": "pegasus",
        "payload": {"build_attempt_id": attempt_id, **payload},
    }


def _arm(policy: dict, name: str, tps: list[object] | None = None) -> dict:
    arm = next(item for item in policy["arms"] if item["name"] == name)
    attempt_id = f"attempt-{name}"
    variant = f"variant-{name}"
    values = list(tps if tps is not None else (
        [100.0, 102.0, 104.0, 106.0, 108.0]
        if name == "adaptive"
        else [90.0, 92.0, 94.0, 96.0, 98.0]
    ))
    numeric = all(
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        for value in values
    )
    median = statistics.median(values) if numeric and values else 1.0
    cv = (
        statistics.stdev(values) / statistics.fmean(values)
        if numeric and len(values) >= 2 and statistics.fmean(values) != 0 else 0.0
    )
    receipt_sha = "e" * 64
    configure = " ".join([
        "cmake", "-S", "/source", "-B", "/build",
        *[
            f"-DCCBENCH_{key}={arm['flags'][key]}"
            for key in sorted(arm["flags"])
        ],
        "-DCCBENCH_TRACE=0",
    ])
    frames = [
        _frame(paired.STAGE_BUILD_START, variant, attempt_id, {
            "genome": paired.Genome(
                arm["protocol"], dict(arm["flags"])
            ).canonical(),
            "src_token": "source-token",
            "build_admission_receipt_sha256": receipt_sha,
        }),
        _frame(paired.STAGE_BUILD_DONE, variant, attempt_id, {
            "build_admission_receipt_sha256": receipt_sha,
            "trace_bin_sha256": "d" * 64,
            "perf_bin_sha256": "f" * 64,
            "perf_configure_cmd": configure,
            "perf_build_cmd": "cmake --build /build --target ycsb_silo.exe -j 48",
        }),
        _frame(paired.STAGE_VERIFY_DONE, variant, attempt_id, {
            "certified": True,
            "verdict": "serializable",
            "workload": {"tag": "legacy"},
        }),
        _frame(paired.STAGE_BENCH_DONE, variant, attempt_id, {
            "median_tps": median,
            "cv": cv,
            "high_variance": False,
            "unstable": False,
            "rounds": 1,
            "tps": values,
            "rep_notes": [],
            "run_cmd": "/build/cc/silo/ycsb_silo.exe -thread_num=48",
        }),
        _frame(paired.STAGE_COMMIT, variant, attempt_id, {
            "fitness_tps": median,
            "cv": cv,
            "high_variance": False,
            "unstable": False,
            "verify_configs": ["legacy"],
            "build_admission_receipt_sha256": receipt_sha,
        }),
    ]
    frames[1]["raw_sha256"] = "2" * 64
    frames[3]["raw_sha256"] = "3" * 64
    return {
        "name": name,
        "variant": variant,
        "attempt_count": 1,
        "attempts": [{"build_attempt_id": attempt_id, "frames": frames}],
        "last_terminal_stage": paired.STAGE_COMMIT,
        "last_stage": paired.STAGE_COMMIT,
    }


def _policy() -> dict:
    return paired.load_policy()[0]


def _validated_workload(name: str = "write-heavy", campaign_id: str = "campaign-a"):
    policy = _policy()
    return paired.validate_workload_evidence(
        policy,
        workload_name=name,
        campaign_id=campaign_id,
        env_tag="pegasus",
        arms=[_arm(policy, "adaptive"), _arm(policy, "static10")],
        wal_evidence={"path": "/raw/wal.jsonl", "size": 1, "sha256": "4" * 64},
        source_binding=_source_binding(),
    )


def _frame_for(arm: dict, stage: str) -> dict:
    return next(
        frame for frame in arm["attempts"][0]["frames"]
        if frame["stage"] == stage
    )


def test_policy_file_is_the_exact_preregistered_contract() -> None:
    policy, digest = paired.load_policy()
    assert policy["study_id"] == paired.STUDY_ID
    assert policy["arm_order"] == ["adaptive", "static10"]
    assert [item["name"] for item in policy["workloads"]] == list(
        paired.WORKLOAD_ORDER
    )
    assert policy["pairing"]["design"] == "arm-grouped-positional-v1"
    assert policy["authority"] == {
        "formal": False,
        "promotion_prohibited": True,
        "result_authority": "exploratory",
        "statistics_authority": "D95 plan-v2 preregistration",
        "d510_role": "analogy-only",
    }
    assert len(digest) == 64


@pytest.mark.parametrize(
    ("arm_name", "field", "replacement"),
    [
        ("adaptive", "BACKOFF_FIXED", 0),
        ("static10", "BACKOFF_FIXED", 5),
    ],
    ids=["M1-adaptive-not-minus-one", "M2-static-not-ten"],
)
def test_paired_genomes_are_exact_and_ordered(
    arm_name: str, field: str, replacement: int
) -> None:
    policy = _policy()
    assert [genome.flags["BACKOFF_FIXED"] for genome in paired.genomes(policy)] == [-1, 10]
    mutated = copy.deepcopy(policy)
    arm = next(item for item in mutated["arms"] if item["name"] == arm_name)
    arm["flags"][field] = replacement
    with pytest.raises(paired.PaperStoryError, match="arms"):
        paired.validate_policy(mutated)


def test_campaign_identity_binds_study_and_arms_M3() -> None:
    cfg = paired.campaign_config(_policy(), "write-heavy")
    preimage = ident.canonical_preimage(cfg)
    assert paired.STUDY_ID in preimage
    for genome in paired.genomes(_policy()):
        assert genome.canonical() in preimage
    without_study = replace(
        cfg,
        search_config={key: value for key, value in cfg.search_config.items() if key != "study_id"},
    )
    without_arms = replace(
        cfg,
        search_config={key: value for key, value in cfg.search_config.items() if key != "arms"},
    )
    assert ident.campaign_id(cfg) != ident.campaign_id(without_study)
    assert ident.campaign_id(cfg) != ident.campaign_id(without_arms)


@pytest.mark.parametrize("count", [4, 6])
def test_collector_requires_exact_five_points_M4(count: int) -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive", [100.0] * count)
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={},
        source_binding=_source_binding(),
    )
    assert result["valid"] is False
    assert any("tps-not-exact-five" in error for error in result["errors"])


@pytest.mark.parametrize(
    "bad",
    [True, float("nan"), float("inf"), 0.0, -1.0],
    ids=["bool", "nan", "infinity", "zero", "negative"],
)
def test_collector_rejects_bool_nonfinite_and_nonpositive_M5(bad: object) -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    bench = _frame_for(adaptive, paired.STAGE_BENCH_DONE)["payload"]
    bench["tps"][2] = bad
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={},
        source_binding=_source_binding(),
    )
    assert result["valid"] is False
    assert any("tps-not-exact-five" in error for error in result["errors"])


@pytest.mark.parametrize("mutation", ["second-attempt", "stage-order"])
def test_collector_rejects_mixed_or_duplicate_attempts_M6(mutation: str) -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    if mutation == "second-attempt":
        adaptive["attempt_count"] = 2
        second = copy.deepcopy(adaptive["attempts"][0])
        second["build_attempt_id"] = "attempt-adaptive-second"
        adaptive["attempts"].append(second)
    else:
        frames = adaptive["attempts"][0]["frames"]
        frames[2], frames[3] = frames[3], frames[2]
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={},
        source_binding=_source_binding(),
    )
    assert result["valid"] is False
    assert any(
        marker in error
        for error in result["errors"]
        for marker in ("attempt-count-not-one", "stage-sequence-mismatch")
    )


@pytest.mark.parametrize("mutation", ["round-two", "unstable"])
def test_collector_rejects_remeasured_or_unstable_arm_M7(mutation: str) -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    bench = _frame_for(adaptive, paired.STAGE_BENCH_DONE)["payload"]
    commit = _frame_for(adaptive, paired.STAGE_COMMIT)["payload"]
    if mutation == "round-two":
        bench["rounds"] = 2
    else:
        bench["unstable"] = True
        commit["unstable"] = True
    raw = list(bench["tps"])
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={},
        source_binding=_source_binding(),
    )
    assert result["valid"] is False
    assert result["arms"]["adaptive"]["raw_tps"] == raw
    assert any(
        marker in error
        for error in result["errors"]
        for marker in ("rounds-not-one", "unstable-not-false")
    )


def test_statistics_keep_static_minus_adaptive_direction_M8() -> None:
    stats = paired.positional_statistics(
        [100, 100, 100, 100, 100],
        [90, 91, 92, 93, 94],
    )
    assert [pair["signed_difference_tps"] for pair in stats["pairs"]] == [
        -10.0, -9.0, -8.0, -7.0, -6.0
    ]
    assert stats["mean_signed_positional_difference_tps"] == -8.0
    assert stats["observed_mean_negative"] is True


def test_statistics_use_n_minus_one_and_emit_variance_M9() -> None:
    stats = paired.positional_statistics(
        [100, 100, 100, 100, 100],
        [101, 103, 105, 107, 109],
    )
    assert stats["mean_signed_positional_difference_tps"] == 5.0
    assert stats["sample_variance_positional_difference_tps2"] == 10.0
    assert stats["sample_sd_positional_difference_tps"] == math.sqrt(10.0)


def test_incomplete_workload_suppresses_cross_workload_conclusion_M10() -> None:
    policy, policy_sha = paired.load_policy()
    workloads = [
        _validated_workload(name, f"campaign-{index}")
        for index, name in enumerate(paired.WORKLOAD_ORDER)
    ]
    workloads[1]["valid"] = False
    workloads[1]["statistics"] = None
    result = paired.assemble_result(
        policy,
        policy_sha256=policy_sha,
        source_binding=_source_binding(),
        workloads=workloads,
    )
    assert result["complete"] is False
    assert result["cross_workload_conclusion"] is None
    assert "No cross-workload conclusion" in paired._readme(result)


def test_materialize_refuses_existing_destination_M11(tmp_path: Path) -> None:
    destination = paired.create_materialization_destination(tmp_path / "insight")
    assert destination.is_dir()
    with pytest.raises(paired.PaperStoryError, match="already exists"):
        paired.create_materialization_destination(destination)


def test_clean_exact_two_arm_three_workload_positive_case() -> None:
    policy, policy_sha = paired.load_policy()
    workloads = [
        _validated_workload(name, f"campaign-{index}")
        for index, name in enumerate(paired.WORKLOAD_ORDER)
    ]
    assert all(item["valid"] is True for item in workloads)
    result = paired.assemble_result(
        policy,
        policy_sha256=policy_sha,
        source_binding=_source_binding(),
        workloads=workloads,
    )
    assert result["complete"] is True
    assert result["cross_workload_conclusion"] == {
        "observed_all_workloads_negative": True,
        "claim_scope": "this one arm-grouped exploratory run only",
    }
    assert "All-workload observed negative direction: `yes`" in paired._readme(result)


def test_positive_fixture_does_not_authorize_absent_settled_or_returncodes() -> None:
    result = _validated_workload()
    assert result["valid"] is True
    for arm in result["arms"].values():
        assert arm["rep_notes"] == []
        assert "settled" not in arm
        assert "rep_returncodes" not in arm


def test_collector_rejects_third_arm_and_missing_arm() -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    static10 = _arm(policy, "static10")
    third = copy.deepcopy(static10)
    third["name"] = "third"
    third["variant"] = "variant-third"
    for arms in ([adaptive], [adaptive, static10, third]):
        result = paired.validate_workload_evidence(
            policy,
            workload_name="write-heavy",
            campaign_id="campaign-a",
            env_tag="pegasus",
            arms=arms,
            wal_evidence={},
            source_binding=_source_binding(),
        )
        assert result["valid"] is False
        assert any("variant-set-cardinality" in error for error in result["errors"])


@pytest.mark.parametrize("mutation", ["uncertified", "abort"])
def test_collector_rejects_uncertified_or_abort(mutation: str) -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    if mutation == "uncertified":
        _frame_for(adaptive, paired.STAGE_VERIFY_DONE)["payload"]["certified"] = False
    else:
        terminal = _frame_for(adaptive, paired.STAGE_COMMIT)
        terminal["stage"] = paired.STAGE_ABORT
        terminal["payload"] = {
            "build_attempt_id": "attempt-adaptive",
            "reason": "verifier-red",
        }
        adaptive["last_terminal_stage"] = paired.STAGE_ABORT
        adaptive["last_stage"] = paired.STAGE_ABORT
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={},
        source_binding=_source_binding(),
    )
    assert result["valid"] is False


@pytest.mark.parametrize("mutation", ["rep-notes", "commit-fitness", "verify-projection"])
def test_collector_rejects_diagnostic_or_commit_projection_drift(mutation: str) -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    if mutation == "rep-notes":
        _frame_for(adaptive, paired.STAGE_BENCH_DONE)["payload"]["rep_notes"] = [
            "rep failed"
        ]
    elif mutation == "commit-fitness":
        _frame_for(adaptive, paired.STAGE_COMMIT)["payload"]["fitness_tps"] += 1
    else:
        _frame_for(adaptive, paired.STAGE_COMMIT)["payload"]["verify_configs"] = []
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={"path": "/raw/wal", "size": 9, "sha256": "4" * 64},
        source_binding=_source_binding(),
    )
    assert result["valid"] is False
    assert result["wal_evidence"]["sha256"] == "4" * 64


@pytest.mark.parametrize("mutation", ["trace-one", "missing-run-cmd", "bad-source"])
def test_trace0_is_source_routed_and_never_standalone(mutation: str) -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    binding = _source_binding()
    if mutation == "trace-one":
        build = _frame_for(adaptive, paired.STAGE_BUILD_DONE)["payload"]
        build["perf_configure_cmd"] = build["perf_configure_cmd"].replace(
            "-DCCBENCH_TRACE=0", "-DCCBENCH_TRACE=1"
        )
    elif mutation == "missing-run-cmd":
        _frame_for(adaptive, paired.STAGE_BENCH_DONE)["payload"].pop("run_cmd")
    else:
        binding["artifact_standalone_proof"] = True
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={},
        source_binding=binding,
    )
    assert result["valid"] is False
    assert any("trace0-source-route-incomplete" in error for error in result["errors"])
