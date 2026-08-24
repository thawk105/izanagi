from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import shlex
import statistics
from dataclasses import replace
from pathlib import Path

import pytest

from orchestrator.calibrator import runner as calibrator_runner
from orchestrator.campaign import ident, wal
from orchestrator.campaign import paper_story_a1_paired as paired
from orchestrator.campaign.build_admission import (
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.layout import exploration_campaign_layout
from orchestrator.campaign.model import WalRecord
from orchestrator.campaign.source_digest import SourceEvidence


_TEST_BUILD_DIR: Path | None = None


@pytest.fixture(autouse=True)
def _readable_perf_binary(tmp_path: Path):
    global _TEST_BUILD_DIR
    build_root = (tmp_path / "trace0-build").resolve()
    for name in ("adaptive", "static10"):
        binary = build_root / name / "cc" / "silo" / "ycsb_silo.exe"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(f"paper-story-a1-{name}-test-perf-binary\n".encode())
    _TEST_BUILD_DIR = build_root
    try:
        yield
    finally:
        _TEST_BUILD_DIR = None


def _source_binding() -> dict:
    return {
        "measurement_source_commit": "a" * 40,
        "files": {
            relative: {
                "git_blob_oid": "b" * 40,
                "working_sha256": "c" * 64,
            }
            for relative in paired.SOURCE_RELATIVE_PATHS
        },
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


def _arm(
    policy: dict,
    name: str,
    tps: list[object] | None = None,
    *,
    workload_name: str = "write-heavy",
) -> dict:
    assert _TEST_BUILD_DIR is not None
    build_dir = _TEST_BUILD_DIR / name
    binary = build_dir / "cc" / "silo" / "ycsb_silo.exe"
    arm = next(item for item in policy["arms"] if item["name"] == name)
    workload = next(
        item for item in policy["workloads"] if item["name"] == workload_name
    )
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
    genome = paired.Genome(arm["protocol"], dict(arm["flags"]))
    toolchain = {
        "cmake": {"realpath": "/toolchain/cmake"},
        "cc": {"realpath": "/toolchain/cc"},
        "cxx": {"realpath": "/toolchain/cxx"},
    }
    configure_argv, build_argv = paired.buildcache._v2_commands(
        genome,
        False,
        "/source",
        os.fspath(build_dir),
        toolchain,
        jobs=48,
    )
    contract = paired.p2_2.env_contract.lookup("pegasus")
    run_flags = [
        "-thread_num=48",
        "-ycsb_tuple_num=1000000",
        "-extime=3",
        f"-clocks_per_us={contract.clocks_per_us}",
        "-ycsb_zipf_skew=0.9",
        f"-ycsb_rratio={workload['ycsb_rratio']}",
        "-ycsb_rmw=0",
        "-ycsb_max_ope=10",
    ]
    configure = " ".join(configure_argv)
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
            "perf_bin_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            "perf_configure_cmd": configure,
            "perf_build_cmd": " ".join(build_argv),
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
            "run_cmd": calibrator_runner.repro_command(
                os.fspath(binary), run_flags, contract.numactl, use_perf=True
            ),
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
    evidence = {
        "name": name,
        "variant": variant,
        "attempt_count": 1,
        "attempts": [{"build_attempt_id": attempt_id, "frames": frames}],
        "last_terminal_stage": paired.STAGE_COMMIT,
        "last_stage": paired.STAGE_COMMIT,
    }
    evidence["all_evaluation_frames"] = frames
    return evidence


def _policy() -> dict:
    return paired.load_policy()[0]


def _validated_workload(name: str = "write-heavy", campaign_id: str = "campaign-a"):
    policy = _policy()
    result = paired.validate_workload_evidence(
        policy,
        workload_name=name,
        campaign_id=campaign_id,
        env_tag="pegasus",
        arms=[
            _arm(policy, "adaptive", workload_name=name),
            _arm(policy, "static10", workload_name=name),
        ],
        wal_evidence={"path": "/raw/wal.jsonl", "size": 1, "sha256": "4" * 64},
        source_binding=_source_binding(),
        campaign_binding={"wal_path": f"/raw/{name}/runs/wal.jsonl"},
    )
    return result


def _production_wal_workload(
    tmp_path: Path,
    name: str = "write-heavy",
    *,
    mutate_frames=None,
    raw_suffix: str = "",
) -> dict:
    policy = _policy()
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    cfg = ident.bind_admission_policy(
        paired.campaign_config(policy, name), context.policy
    )
    preimage = ident.canonical_preimage(cfg)
    campaign_id = paired._campaign_id_from_preimage(name, preimage)
    layout = exploration_campaign_layout(campaign_id, tmp_path / "campaign-output")
    Path(layout.runs_dir).mkdir(parents=True)
    wal.write_lock(layout, preimage)
    frames = []
    for arm_name in paired.ARM_ORDER:
        policy_arm = next(
            item for item in policy["arms"] if item["name"] == arm_name
        )
        genome = paired.Genome(
            policy_arm["protocol"], dict(policy_arm["flags"])
        )
        evidence = SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=str(tmp_path.resolve()),
            ccbench_commit=paired.pin.CURRENT_PIN,
            genome_sha256=hashlib.sha256(
                genome.canonical().encode("utf-8")
            ).hexdigest(),
            src_token="stock",
            source_bytes_sha256=hashlib.sha256(b"stock").hexdigest(),
            tracked_clean=True,
            tracked_diff_sha256=hashlib.sha256(b"").hexdigest(),
            tracked_paths=(),
        )
        receipt = derive_build_admission(context, evidence).as_wal_receipt()
        arm = _arm(policy, arm_name, workload_name=name)
        arm_frames = arm["attempts"][0]["frames"]
        for frame in arm_frames:
            if frame["stage"] == paired.STAGE_BUILD_START:
                frame["payload"].update({
                    "src_token": receipt["source"]["src_token"],
                    "build_admission": receipt,
                    "build_admission_receipt_sha256": receipt["receipt_sha256"],
                })
            elif frame["stage"] in {
                paired.STAGE_BUILD_DONE,
                paired.STAGE_COMMIT,
            }:
                frame["payload"]["build_admission_receipt_sha256"] = (
                    receipt["receipt_sha256"]
                )
        frames.extend(arm_frames)
    if mutate_frames is not None:
        mutate_frames(frames)
    lines = []
    for index, frame in enumerate(frames, 1):
        record = WalRecord(
            variant=frame["variant"],
            stage=frame["stage"],
            env_tag=frame["env_tag"],
            ts=float(index),
            payload=frame["payload"],
        )
        lines.append(wal._record_to_line(record))
    Path(layout.wal_file).write_text(
        "\n".join(lines) + "\n" + raw_suffix, encoding="utf-8"
    )
    return paired.collect_workload(
        policy,
        workload_name=name,
        campaign_id=campaign_id,
        layout=layout,
        admission_policy=context.policy,
        env_tag="pegasus",
        source_binding=_source_binding(),
        expected_campaign_preimage=preimage,
        expected_layout_root=layout.root,
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
    assert policy["execution"]["durable_measurement_base"] == (
        "/work/1/SFC/tanab/dev-wave-jobs/"
        "dev-wave-paper-story-a1-paired-20260824/measurement"
    )
    assert hashlib.sha256(paired.POLICY_PATH.read_bytes()).hexdigest() == digest


def test_durable_base_append_preserves_campaign_preimage_and_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _policy()
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    current = {
        workload: ident.bind_admission_policy(
            paired.campaign_config(policy, workload), context.policy
        )
        for workload in paired.WORKLOAD_ORDER
    }
    legacy = copy.deepcopy(policy)
    legacy["execution"].pop("durable_measurement_base")
    monkeypatch.setattr(paired, "validate_policy", lambda candidate: candidate)
    baseline = {
        workload: ident.bind_admission_policy(
            paired.campaign_config(legacy, workload), context.policy
        )
        for workload in paired.WORKLOAD_ORDER
    }
    for workload in paired.WORKLOAD_ORDER:
        current_preimage = ident.canonical_preimage(current[workload])
        baseline_preimage = ident.canonical_preimage(baseline[workload])
        assert current_preimage == baseline_preimage
        assert ident.campaign_id(current[workload]) == ident.campaign_id(
            baseline[workload]
        )


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
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    cfg = ident.bind_admission_policy(
        paired.campaign_config(_policy(), "write-heavy"), context.policy
    )
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
    [True, float("nan"), float("inf"), 0.0, -1.0, 10 ** 10000],
    ids=["bool", "nan", "infinity", "zero", "negative", "huge-integer"],
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
def test_collector_rejects_mixed_or_duplicate_attempts_M6(
    tmp_path: Path, mutation: str
) -> None:
    if mutation == "second-attempt":
        def add_second_attempt(frames: list[dict]) -> None:
            first = [
                frame for frame in frames
                if frame["variant"] == "variant-adaptive"
            ]
            second = copy.deepcopy(first)
            for frame in second:
                frame["payload"]["build_attempt_id"] = "attempt-adaptive-second"
            frames[len(first):len(first)] = second

        result = _production_wal_workload(
            tmp_path, mutate_frames=add_second_attempt
        )
        assert result["valid"] is False
        assert result["errors"] == ["adaptive:attempt-count-not-one"]
        assert result["arms"]["adaptive"]["errors"] == ["attempt-count-not-one"]
        return

    policy = _policy()
    adaptive = _arm(policy, "adaptive")
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

    target = tmp_path / "create-only.json"
    paired._exclusive_write(target, {"first": True})
    with pytest.raises(paired.PaperStoryError, match="create-only write refused"):
        paired._exclusive_write(target, {"second": True})


def test_materialization_is_exact_leaf_and_noreplace_publish(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    destination = repo / paired.MATERIALIZATION_RELATIVE_PATH
    destination.parent.mkdir(parents=True)
    assert paired._exact_materialization_destination(repo, destination) == destination
    with pytest.raises(paired.PaperStoryError, match="exact A-1 insight leaf"):
        paired._exact_materialization_destination(repo, destination.parent / "other")

    staging = destination.parent / ".a1-staging"
    staging.mkdir()
    paired._exclusive_write(staging / "result.json", {"complete": True})
    paired._exclusive_write(staging / "receipt.json", {"complete": True})
    paired._exclusive_write_text(staging / "README.md", "complete\n")
    paired._publish_complete_staging(staging, destination, {"complete": True})
    assert {path.name for path in destination.iterdir()} == {
        "README.md", "receipt.json", "result.json", paired.COMPLETION_MARKER,
    }

    second = destination.parent / ".a1-staging-second"
    second.mkdir()
    with pytest.raises(paired.PaperStoryError, match="no-replace"):
        paired._publish_staging_noreplace(second, destination)


def test_unpublished_materialization_staging_is_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "insight"
    staging = tmp_path / f".insight.staging-{os.getpid()}"

    def refuse_publish(source: Path, target: Path) -> None:
        assert source == staging
        assert target == destination
        raise paired.PaperStoryError("injected publish refusal")

    monkeypatch.setattr(paired, "_publish_staging_noreplace", refuse_publish)
    with pytest.raises(paired.PaperStoryError, match="injected publish refusal"):
        paired._publish_materialization_bundle(
            destination,
            {"receipt": True},
            {"complete": False, "cross_workload_conclusion": None},
        )
    assert not staging.exists()
    assert not destination.exists()


def test_publish_error_after_rename_does_not_remove_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "insight"

    def rename_then_report_error(source: Path, target: Path) -> None:
        source.rename(target)
        raise paired.PaperStoryError("injected post-rename error")

    monkeypatch.setattr(
        paired, "_publish_staging_noreplace", rename_then_report_error
    )
    with pytest.raises(paired.PaperStoryError, match="injected post-rename error"):
        paired._publish_materialization_bundle(
            destination,
            {"receipt": True},
            {"complete": False, "cross_workload_conclusion": None},
        )
    assert destination.is_dir()
    assert paired.COMPLETION_MARKER in {
        path.name for path in destination.iterdir()
    }


def test_completion_marker_is_present_at_single_publish_boundary_M17(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staging = tmp_path / "staging"
    destination = tmp_path / "published"
    staging.mkdir()
    for name in ("README.md", "receipt.json", "result.json"):
        (staging / name).write_text(name, encoding="utf-8")
    observed: dict[str, set[str]] = {}

    def inspect_publish(source: Path, target: Path) -> None:
        assert source == staging
        assert target == destination
        observed["files"] = {path.name for path in source.iterdir()}
        source.rename(target)

    monkeypatch.setattr(paired, "_publish_staging_noreplace", inspect_publish)
    paired._publish_complete_staging(staging, destination, {"complete": True})
    assert observed["files"] == {
        "README.md", "receipt.json", "result.json", paired.COMPLETION_MARKER,
    }
    assert {path.name for path in destination.iterdir()} == observed["files"]


def test_production_wal_bytes_positive_fixture(tmp_path: Path) -> None:
    result = _production_wal_workload(tmp_path)
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["campaign_binding"]["canonical_preimage"]
    assert result["wal_evidence"]["line_issues"] == []
    assert result["wal_evidence"]["truncated_tail"] is False


def test_trace0_accepts_actual_pegasus_producer_argv_positive(
    tmp_path: Path,
) -> None:
    result = _production_wal_workload(tmp_path)
    evidence = result["arms"]["adaptive"]["performance_trace0_evidence"]
    assert shlex.split(evidence["perf_configure_cmd"])[0:2] == [
        "/toolchain/cmake", "-S",
    ]
    assert shlex.split(evidence["bench_run_cmd"])[0:5] == [
        "perf",
        "stat",
        "-e",
        ",".join(calibrator_runner.PERF_EVENTS),
        "--",
    ]
    assert result["valid"] is True


@pytest.mark.parametrize(
    "mutation",
    [
        "separated-define",
        "typed-define",
        "joined-undefine",
        "separated-undefine",
        "extra-source",
        "unknown-configure-option",
        "unknown-build-option",
        "unknown-run-option",
    ],
)
def test_trace0_token_allowlist_rejects_every_unregistered_token_M18(
    tmp_path: Path, mutation: str
) -> None:
    def mutate(frames: list[dict]) -> None:
        adaptive = [
            frame for frame in frames if frame["variant"] == "variant-adaptive"
        ]
        build = next(
            frame for frame in adaptive if frame["stage"] == paired.STAGE_BUILD_DONE
        )["payload"]
        bench = next(
            frame for frame in adaptive if frame["stage"] == paired.STAGE_BENCH_DONE
        )["payload"]
        if mutation == "separated-define":
            build["perf_configure_cmd"] = build["perf_configure_cmd"].replace(
                "-DCCBENCH_TRACE=0", "-D CCBENCH_TRACE=0"
            )
        elif mutation == "typed-define":
            build["perf_configure_cmd"] = build["perf_configure_cmd"].replace(
                "-DCCBENCH_TRACE=0", "-DCCBENCH_TRACE:BOOL=0"
            )
        elif mutation == "joined-undefine":
            build["perf_configure_cmd"] += " -UCCBENCH_TRACE"
        elif mutation == "separated-undefine":
            build["perf_configure_cmd"] += " -U CCBENCH_TRACE"
        elif mutation == "extra-source":
            build["perf_configure_cmd"] += " -S /other-source"
        elif mutation == "unknown-configure-option":
            build["perf_configure_cmd"] += " --future-configure-option"
        elif mutation == "unknown-build-option":
            build["perf_build_cmd"] += " --future-build-option"
        else:
            bench["run_cmd"] += " -future_workload_knob=1"

    result = _production_wal_workload(tmp_path, mutate_frames=mutate)
    assert result["errors"] == ["adaptive:trace0-source-route-incomplete"]
    assert result["arms"]["static10"]["valid"] is True


def test_trace0_rejects_unregistered_ccbench_define_M13(tmp_path: Path) -> None:
    def mutate(frames: list[dict]) -> None:
        build = next(
            frame for frame in frames
            if frame["variant"] == "variant-adaptive"
            and frame["stage"] == paired.STAGE_BUILD_DONE
        )
        build["payload"]["perf_configure_cmd"] += " -DCCBENCH_UNREGISTERED=1"

    result = _production_wal_workload(tmp_path, mutate_frames=mutate)
    assert result["errors"] == ["adaptive:trace0-source-route-incomplete"]
    assert result["arms"]["static10"]["valid"] is True


def test_trace0_requires_canonical_argv0_M14(tmp_path: Path) -> None:
    def mutate(frames: list[dict]) -> None:
        bench = next(
            frame for frame in frames
            if frame["variant"] == "variant-adaptive"
            and frame["stage"] == paired.STAGE_BENCH_DONE
        )
        bench["payload"]["run_cmd"] = (
            f"/bin/echo {bench['payload']['run_cmd']}"
        )

    result = _production_wal_workload(tmp_path, mutate_frames=mutate)
    assert result["errors"] == ["adaptive:trace0-source-route-incomplete"]
    assert result["arms"]["static10"]["valid"] is True


@pytest.mark.parametrize(
    "mutation", ["build-directory", "binary-sha", "binary-unreadable"]
)
def test_trace0_binds_build_directory_and_binary_bytes(
    tmp_path: Path, mutation: str
) -> None:
    def mutate(frames: list[dict]) -> None:
        build = next(
            frame for frame in frames
            if frame["variant"] == "variant-adaptive"
            and frame["stage"] == paired.STAGE_BUILD_DONE
        )
        if mutation == "build-directory":
            assert _TEST_BUILD_DIR is not None
            other = (tmp_path / "other-build").resolve()
            build["payload"]["perf_build_cmd"] = build["payload"][
                "perf_build_cmd"
            ].replace(os.fspath(_TEST_BUILD_DIR), os.fspath(other))
        elif mutation == "binary-sha":
            build["payload"]["perf_bin_sha256"] = "f" * 64
        else:
            assert _TEST_BUILD_DIR is not None
            (
                _TEST_BUILD_DIR
                / "adaptive" / "cc" / "silo" / "ycsb_silo.exe"
            ).unlink()

    result = _production_wal_workload(tmp_path, mutate_frames=mutate)
    assert result["errors"] == ["adaptive:trace0-source-route-incomplete"]


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("unbound-stage", "stage-sequence-mismatch"),
        ("duplicate-macro", "trace0-source-route-incomplete"),
        ("wrong-workload-argv", "trace0-source-route-incomplete"),
        ("huge-integer", "tps-not-exact-five"),
    ],
)
def test_production_wal_mutations_are_invalid(
    tmp_path: Path, mutation: str, expected: str
) -> None:
    def mutate(frames: list[dict]) -> None:
        adaptive = [frame for frame in frames if frame["variant"] == "variant-adaptive"]
        if mutation == "unbound-stage":
            extra = copy.deepcopy(next(
                frame for frame in adaptive if frame["stage"] == paired.STAGE_VERIFY_DONE
            ))
            extra["payload"].pop("build_attempt_id")
            frames.insert(frames.index(adaptive[-2]), extra)
        elif mutation == "duplicate-macro":
            build = next(
                frame for frame in adaptive if frame["stage"] == paired.STAGE_BUILD_DONE
            )
            build["payload"]["perf_configure_cmd"] += " -DCCBENCH_BACKOFF_FIXED=0"
        elif mutation == "wrong-workload-argv":
            bench = next(
                frame for frame in adaptive if frame["stage"] == paired.STAGE_BENCH_DONE
            )
            bench["payload"]["run_cmd"] = bench["payload"]["run_cmd"].replace(
                "-ycsb_rratio=5", "-ycsb_rratio=95"
            )
        else:
            bench = next(
                frame for frame in adaptive if frame["stage"] == paired.STAGE_BENCH_DONE
            )
            bench["payload"]["tps"][2] = 10 ** 400

    result = _production_wal_workload(tmp_path, mutate_frames=mutate)
    assert result["valid"] is False
    assert any(expected in error for error in result["errors"])


def test_invalid_wal_tail_preserves_snapshot_forensics(tmp_path: Path) -> None:
    result = _production_wal_workload(tmp_path, raw_suffix="{")
    assert result["valid"] is False
    assert result["wal_evidence"]["truncated_tail"] is True
    assert len(result["wal_evidence"]["records"]) == 10


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


def test_result_and_readme_disclose_nqsv_observation_scope() -> None:
    policy, policy_sha = paired.load_policy()
    workloads = [
        _validated_workload(name, f"campaign-{index}")
        for index, name in enumerate(paired.WORKLOAD_ORDER)
    ]
    result = paired.assemble_result(
        policy,
        policy_sha256=policy_sha,
        source_binding=_source_binding(),
        workloads=workloads,
    )
    assert result["pbs_evidence_scope"] == paired._json_safe(
        paired.PBS_EVIDENCE_SCOPE
    )
    readme = paired._readme(result)
    assert "PBS_O_QUEUE is not exported" in readme
    assert "stdout/stderr FD targets are not the qsub -o/-e delivery files" in readme
    assert "scheduler completion receipt SHA-256" in readme


@pytest.mark.parametrize(
    ("field", "value"),
    [("driver_rc", True), ("driver_rc", 1), ("shell_rc", 1)],
)
def test_materializer_requires_exact_zero_driver_and_shell_rc(
    field: str, value: object
) -> None:
    policy, policy_sha = paired.load_policy()
    workloads = [
        _validated_workload(name, f"campaign-{index}")
        for index, name in enumerate(paired.WORKLOAD_ORDER)
    ]
    result = paired.assemble_result(
        policy,
        policy_sha256=policy_sha,
        source_binding=_source_binding(),
        workloads=workloads,
    )
    receipt = {
        "schema_version": paired.RECEIPT_SCHEMA,
        "study_id": paired.STUDY_ID,
        "formal": False,
        "promotion_prohibited": True,
        "pbs_jobid": "12345.nqsv",
        "source_binding": _source_binding(),
        "roots": {"completion_receipt": "/durable/attempt.completion.json"},
        "submission_receipt": {"sha256": "d" * 64},
    }
    terminal = {
        "schema_version": paired.JOB_TERMINAL_SCHEMA,
        "study_id": paired.STUDY_ID,
        "pbs_jobid": "12345.nqsv",
        "expected_head": "a" * 40,
        "observed_head": "a" * 40,
        "porcelain": "",
        "driver_rc": 0,
        "shell_rc": 0,
        "status": "finished",
        "terminal_source_binding": _source_binding(),
        "completion_receipt_path": "/durable/attempt.completion.json",
        "submission_receipt_sha256": "d" * 64,
    }
    terminal[field] = value
    with pytest.raises(paired.PaperStoryError, match="finished raw bundle"):
        paired.validate_raw_documents(result, receipt, terminal, policy)


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
