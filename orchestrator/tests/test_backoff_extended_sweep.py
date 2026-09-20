from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import random
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import (
    artifact_admission,
    backoff_extended_sweep as M,
    backoff_extended_sweep_report as R,
    backoff_overthrottle as O,
    build_admission,
    env_contract,
    ident,
    loop,
    p2_2,
    pipeline as campaign_pipeline,
    site_policy,
)
from orchestrator.calibrator import perf_preflight


def _shell_integer_assignments(
        script: str, names: tuple[str, ...]) -> dict[str, int]:
    assignments = {}
    for name in names:
        matches = re.findall(rf"(?m)^{re.escape(name)}=([0-9]+)$", script)
        assert len(matches) == 1
        assignments[name] = int(matches[0])
    return assignments


def _git(cwd: Path, *args: str, input_text: str | None = None) -> str:
    completed = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        input=input_text,
    )
    return completed.stdout.strip()


def _fixture_git_repository(root: Path) -> tuple[Path, str, str]:
    repository = root / "objects.git"
    repository.mkdir()
    _git(repository, "init", "--bare", "--quiet")

    def commit(content: str, parent: str | None = None) -> str:
        blob = _git(repository, "hash-object", "-w", "--stdin", input_text=content)
        tree = _git(
            repository, "mktree",
            input_text=f"100644 blob {blob}\ttracked.txt\n",
        )
        argv = [
            "-c", "user.name=B10 Test", "-c", "user.email=b10@example.invalid",
            "commit-tree", tree,
        ]
        if parent is not None:
            argv.extend(["-p", parent])
        return _git(repository, *argv, input_text="fixture\n")

    expected = commit("expected\n")
    other = commit("other\n", expected)
    return repository, expected, other


def _add_detached_worktree(repository: Path, path: Path, commit: str) -> None:
    _git(repository, "worktree", "add", "--detach", str(path), commit)


def _shell_function(script: str, name: str) -> str:
    start = script.index(f"{name}() {{")
    end = script.index("\n}", start) + 2
    return script[start:end]


def _stub_patch_and_prebuild(monkeypatch, events=None):
    observed = [] if events is None else events

    @contextmanager
    def applied(patch_path, pin_commit, ccbench_dir):
        observed.append(("patch-enter", patch_path, pin_commit, ccbench_dir))
        try:
            yield ["cmake/Options.cmake", "include/backoff.hh"]
        finally:
            observed.append(("patch-exit",))

    monkeypatch.setattr(M.patchharness, "applied", applied)

    @contextmanager
    def checkout(_pin_commit, base_dir=""):
        yield f"{base_dir}/stock"

    monkeypatch.setattr(M.patchharness, "checkout", checkout)
    monkeypatch.setattr(
        M, "_assert_backoff_fixed_materialized",
        lambda _ccbench_dir: observed.append(("patch-materialized",)),
    )
    monkeypatch.setattr(
        M.buildcache,
        "prepare_masstree_fetchcontent",
        lambda **kwargs: observed.append(("masstree-prepare", kwargs)),
    )

    def prebuild(*args, **kwargs):
        observed.append(("prebuild", args, kwargs))
        return {}

    monkeypatch.setattr(M, "_prebuild_backoff_binaries", prebuild)
    monkeypatch.setattr(
        M,
        "_require_condition_gate_before_measurement",
        lambda *args, **kwargs:
            observed.append(("condition-gate", args, kwargs)) or object(),
    )
    return observed


def _condition_fixture(name: str) -> Path:
    return Path(_HERE) / "fixtures" / "condition_meaning_gate" / name


def _available_executable(*names: str) -> str:
    for name in names:
        resolved = shutil.which(name)
        if resolved is not None:
            return resolved
    pytest.skip(f"required executable is unavailable: {names!r}")


def _independent_replay_digest(record) -> str:
    argv = list(record.evidence["requested_replay_argv"])
    index = 0
    while index < len(argv):
        if argv[index] in {"-MD", "-MMD", "-MP", "-MG"}:
            del argv[index]
            continue
        if argv[index] == "-MF":
            del argv[index:index + 2]
            continue
        index += 1
    completed = subprocess.run(argv, check=True, capture_output=True)
    assert completed.stderr == b""
    return hashlib.sha256(completed.stdout).hexdigest()


def _measure_t2266_round(
        capture: M._T2266RepCapture, point_index: int, *,
        extra_parser_call: bool = False,
) -> list[float]:
    """Drive the real measurement/parser path with a subprocess boundary fake."""
    abort_rates = [0.01 * (point_index + 1) + 0.001 * rep for rep in range(p2_2.REPS)]
    calls = 0

    def subprocess_runner(*_args, **_kwargs):
        nonlocal calls
        rep = calls
        calls += 1
        if extra_parser_call and rep == 0:
            M.calibrator_runner.parse_abort_rate({"abort_rate": "0.9"})
        throughput = 1_000_000.0 + point_index * 100.0 + rep
        return SimpleNamespace(
            returncode=0,
            stdout=(
                f"throughput[tps]:\t{throughput}\n"
                f"abort_rate:\t{abort_rates[rep]}\n"
                "latency[ns]:\t100\n"
            ),
            stderr="",
        )

    M.campaign_pipeline.measure_point(
        f"/fixture/t2266-point-{point_index}",
        records=1,
        threads=1,
        clocks_per_us=1,
        extime=1,
        reps=p2_2.REPS,
        workload={},
        subprocess_runner=subprocess_runner,
        require_all_reps=True,
        use_perf=False,
    )
    assert calls == p2_2.REPS
    return abort_rates


def test_b5_pipeline_balanced_schedule_is_a_seven_key_subset_consumer():
    observation = {
        "rep_index": 0,
        "returncode": 0,
        "execution_failure": False,
        "counter_status": "not_required",
        "missing_perf_events": [],
        "perf_raw": {},
        "throughput": 1_000_000.0,
    }
    assert len(observation) == 7
    assert type(observation["execution_failure"]) is bool

    target = campaign_pipeline._run_balanced_schedule
    tree = ast.parse(inspect.getsource(target))
    observation_loads = {
        id(node)
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Name)
            and node.id == "observation"
            and isinstance(node.ctx, ast.Load)
        )
    }
    subset_reads = [
        node
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "observation"
            and len(node.args) == 1
            and not node.keywords
            and isinstance(node.args[0], ast.Constant)
            and type(node.args[0].value) is str
        )
    ]
    assert observation_loads == {id(node.func.value) for node in subset_reads}
    accessed_keys = [node.args[0].value for node in subset_reads]
    assert accessed_keys == ["throughput", "throughput", "throughput"]
    assert [observation.get(key) for key in accessed_keys] == [
        1_000_000.0,
        1_000_000.0,
        1_000_000.0,
    ]


def _measure_t2418_round(
        capture: M._T2418RepCapture, point_index: int,
) -> list[float]:
    """Drive the T-2418 capture through the real measurement/parser path."""
    abort_rates = [
        0.01 * (point_index + 1) + 0.001 * rep for rep in range(5)
    ]
    calls = 0

    def subprocess_runner(*_args, **_kwargs):
        nonlocal calls
        rep = calls
        calls += 1
        throughput = 2_000_000.0 + point_index * 100.0 + rep
        return SimpleNamespace(
            returncode=0,
            stdout=(
                f"throughput[tps]:\t{throughput}\n"
                f"abort_rate:\t{abort_rates[rep]}\n"
                "latency[ns]:\t200\n"
            ),
            stderr="",
        )

    M.campaign_pipeline.measure_point(
        f"/fixture/t2418-point-{point_index}",
        records=1,
        threads=1,
        clocks_per_us=1,
        extime=3,
        reps=5,
        workload={},
        subprocess_runner=subprocess_runner,
        require_all_reps=True,
        use_perf=False,
    )
    assert calls == 5
    return abort_rates


def _t2266_certified_view(tmp_path: Path, capture: M._T2266RepCapture):
    """Build the real immutable WAL projection consumed by the report loader."""
    records = []
    for point_index, genome in enumerate(M.t2266_genomes("balanced")):
        captured = capture.rounds[point_index]
        variant = f"fixture-variant-{point_index}"
        attempt = f"fixture-attempt-{point_index}"
        common = {"build_attempt_id": attempt}
        records.extend((
            artifact_admission.ImmutableWalRecord(
                variant, M.wal.STAGE_BUILD_START, "fixture-env", point_index * 4,
                {**common, "genome": genome.canonical()},
            ),
            artifact_admission.ImmutableWalRecord(
                variant, M.wal.STAGE_VERIFY_DONE, "fixture-env", point_index * 4 + 1,
                {**common, "certified": True},
            ),
            artifact_admission.ImmutableWalRecord(
                variant, M.wal.STAGE_BENCH_DONE, "fixture-env", point_index * 4 + 2,
                {
                    **common,
                    "run_cmd": captured["run_cmd"],
                    "tps": captured["throughput_tps"],
                    "median_tps": captured["throughput_tps"][p2_2.REPS // 2],
                    "leading_indicators": {
                        "abort_rate": captured["reps"][p2_2.REPS // 2]["abort_rate"],
                        "latency_ns": 100.0,
                    },
                    "cv": 0.001,
                    "unstable": False,
                },
            ),
            artifact_admission.ImmutableWalRecord(
                variant, M.wal.STAGE_COMMIT, "fixture-env", point_index * 4 + 3,
                common,
            ),
        ))
    campaign_id = "t2266-fixture-campaign"
    root = tmp_path / "campaigns" / campaign_id
    (root / "reports").mkdir(parents=True)
    digest = "0" * 64
    decision = artifact_admission.CampaignAdmissionDecision(
        classification="official-certified",
        admission_status="admitted",
        verification_status="verified",
        campaign_id=campaign_id,
        campaign_path=str(root),
        campaign_lock_sha256=digest,
        wal_sha256=digest,
        policy_sha256=None,
        attempt_receipt_sha256s=(),
        overlay_ledger_sha256=digest,
        overlay_record_key=None,
        validator_sha256=digest,
    )
    epoch = artifact_admission.CampaignVerifierEpoch(
        f"E1:{digest}", "E1", "recorded-closure",
    )
    immutable_records = artifact_admission._immutable_records(tuple(records))
    return artifact_admission.CertifiedCampaignView(
        layout=artifact_admission.CampaignLayout(str(root)),
        records=immutable_records,
        decision=decision,
        campaign_verifier_epoch=epoch,
        persisted_certified_commit_count=8,
        _certification_token=artifact_admission._CERTIFIED_VIEW_TOKEN,
    )


def _t2418_certified_view(tmp_path: Path, capture: M._T2418RepCapture):
    """Freeze the T-2418 WAL through artifact_admission's production freezer."""
    records = []
    for point_index, genome in enumerate(M.t2418_genomes("balanced")):
        captured = capture.rounds[point_index]
        variant = f"t2418-fixture-variant-{point_index}"
        attempt = f"t2418-fixture-attempt-{point_index}"
        common = {"build_attempt_id": attempt}
        records.extend((
            artifact_admission.ImmutableWalRecord(
                variant, M.wal.STAGE_BUILD_START, "fixture-env", point_index * 4,
                {**common, "genome": genome.canonical()},
            ),
            artifact_admission.ImmutableWalRecord(
                variant, M.wal.STAGE_VERIFY_DONE, "fixture-env", point_index * 4 + 1,
                {**common, "certified": True},
            ),
            artifact_admission.ImmutableWalRecord(
                variant, M.wal.STAGE_BENCH_DONE, "fixture-env", point_index * 4 + 2,
                {
                    **common,
                    "run_cmd": captured["run_cmd"],
                    "tps": captured["throughput_tps"],
                    "median_tps": captured["throughput_tps"][2],
                    "leading_indicators": {
                        "abort_rate": captured["reps"][2]["abort_rate"],
                        "latency_ns": 200.0,
                    },
                    "cv": 0.002,
                    "unstable": False,
                },
            ),
            artifact_admission.ImmutableWalRecord(
                variant, M.wal.STAGE_COMMIT, "fixture-env", point_index * 4 + 3,
                common,
            ),
        ))
    campaign_id = "t2418-fixture-campaign"
    root = tmp_path / "campaigns" / campaign_id
    (root / "reports").mkdir(parents=True)
    digest = "1" * 64
    decision = artifact_admission.CampaignAdmissionDecision(
        classification="official-certified",
        admission_status="admitted",
        verification_status="verified",
        campaign_id=campaign_id,
        campaign_path=str(root),
        campaign_lock_sha256=digest,
        wal_sha256=digest,
        policy_sha256=None,
        attempt_receipt_sha256s=(),
        overlay_ledger_sha256=digest,
        overlay_record_key=None,
        validator_sha256=digest,
    )
    epoch = artifact_admission.CampaignVerifierEpoch(
        f"E1:{digest}", "E1", "recorded-closure",
    )
    immutable_records = artifact_admission._immutable_records(tuple(records))
    return artifact_admission.CertifiedCampaignView(
        layout=artifact_admission.CampaignLayout(str(root)),
        records=immutable_records,
        decision=decision,
        campaign_verifier_epoch=epoch,
        persisted_certified_commit_count=5,
        _certification_token=artifact_admission._CERTIFIED_VIEW_TOKEN,
    )


def test_mu1_extended_grid_semantic_golden_except_registered_upper_endpoint():
    adaptive_states_literal = {0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000}
    assert tuple(
        amount for amount in M.EXTENDED_SWEEP_US
        if amount not in adaptive_states_literal
    ) == (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50, 75, 150, 250, 560)


def test_mu2_grid_upper_endpoint_matches_adaptive_range():
    assert M.EXTENDED_SWEEP_US[-1] == 1000
    cfg = M.config_for("balanced", M.WORKLOAD_BY_TAG["balanced"])
    assert cfg.spec_slug == "b10-backoff-grid-static-codec-v2-silo-balanced"
    assert cfg.search_config["scale"] == "silo-backoff-extended-static-codec-v2"
    assert cfg.trial == "b10-backoff-grid-static-codec-v2"
    assert any(
        genome.flags["BACKOFF_FIXED"] == 3000
        for genome in M.genomes("balanced")
    )


def test_static_codec_is_bijective_on_its_exact_bounded_domain():
    assert M.encode_static_backoff_us(0) == 0
    assert M.encode_static_backoff_us(999) == 999
    assert M.encode_static_backoff_us(1000) == 3000
    assert M.encode_static_backoff_us(9999) == 11999
    assert M.decode_static_backoff_us(0) == 0
    assert M.decode_static_backoff_us(999) == 999
    assert M.decode_static_backoff_us(3000) == 1000
    assert M.decode_static_backoff_us(11999) == 9999
    for amount in range(10000):
        expected_raw = amount if amount <= 999 else amount + 2000
        assert M.encode_static_backoff_us(amount) == expected_raw
        assert M.decode_static_backoff_us(expected_raw) == amount
    for invalid in (-1, True, 10000):
        with pytest.raises(ValueError):
            M.encode_static_backoff_us(invalid)
    for invalid in (-1, True, 1000, 1999, 2000, 2999, 12000):
        with pytest.raises(ValueError):
            M.decode_static_backoff_us(invalid)


def test_mu15_all_adaptive_discrete_states_have_independent_literal_coverage():
    adaptive_states_literal = (0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000)
    assert set(adaptive_states_literal) <= set(M.EXTENDED_SWEEP_US)


def test_fixed_zero_and_none_are_distinct_genomes():
    points = M.genomes("balanced")
    assert len(M.EXTENDED_SWEEP_US) == len(set(M.EXTENDED_SWEEP_US))
    assert len(points) == len(M.EXTENDED_SWEEP_US) + 2
    none = next(genome for genome in points if genome.flags["BACK_OFF"] == 0)
    fixed_zero = next(
        genome for genome in points
        if genome.flags["BACK_OFF"] == 1 and genome.flags["BACKOFF_FIXED"] == 0
    )
    assert none.flags["BACKOFF_FIXED"] == -1
    assert fixed_zero.flags["BACKOFF_FIXED"] == 0
    assert none.canonical() != fixed_zero.canonical()


def test_t2266_grid_is_exact_eight_points_with_physical_1000_encoded_as_3000():
    expected_static = (150, 200, 300, 500, 750, 3000)
    for tag, _workload in M.WORKLOADS:
        points = M.t2266_genomes(tag)
        assert len(points) == 8
        assert len({point.canonical() for point in points}) == 8
        assert sum(point.flags["BACK_OFF"] == 0 for point in points) == 1
        assert sum(
            point.flags["BACK_OFF"] == 1
            and point.flags["BACKOFF_FIXED"] == -1
            for point in points
        ) == 1
        assert tuple(sorted(
            point.flags["BACKOFF_FIXED"]
            for point in points
            if point.flags["BACK_OFF"] == 1
            and point.flags["BACKOFF_FIXED"] >= 0
        )) == expected_static
        assert all(point.flags["BACKOFF_FIXED"] not in {0, 1000} for point in points)


def test_t2266_requested_realized_and_unrealized_are_separate_identity_fields():
    assert M.T2266_REQUESTED_US == (150, 200, 300, 500, 750, 1000)
    assert M.T2266_REALIZED_US == (150, 200, 300, 500, 750, 1000)
    assert M.T2266_UNREALIZED == {}

    cfg = M.t2266_config_for("balanced", M.WORKLOAD_BY_TAG["balanced"])
    assert cfg.spec_slug == "t2266-backoff-static-tail-v2-silo-balanced"
    assert cfg.search_config["scale"] == "t2266-backoff-static-tail-v2"
    assert cfg.trial == "t2266-backoff-static-tail-v2"
    assert cfg.search_config["requested_us"] == list(M.T2266_REQUESTED_US)
    assert cfg.search_config["realized_us"] == list(M.T2266_REALIZED_US)
    assert cfg.search_config["requested_us"] is not cfg.search_config["realized_us"]
    cfg.search_config["requested_us"].append(9999)
    assert cfg.search_config["realized_us"] == [150, 200, 300, 500, 750, 1000]
    cfg.search_config["requested_us"].pop()
    assert cfg.search_config["unrealized"] == []
    assert cfg.search_config["run_kind"] == M.T2266_RUN_KIND
    assert cfg.search_config["measurement_order"] == M.t2266_measurement_order(
        "balanced",
    )
    assert [point["label"] for point in cfg.search_config["grid"]] == (
        ["none", "adaptive", *[
            f"fixed-{amount}us" for amount in M.T2266_REALIZED_US
        ]]
    )
    endpoint = next(
        point for point in cfg.search_config["grid"]
        if point["label"] == "fixed-1000us"
    )
    assert endpoint["flags"]["BACKOFF_FIXED"] == 3000
    assert set(cfg.search_config["measurement_order"]) == {
        point["label"] for point in cfg.search_config["grid"]
    }

    report = M._t2266_report_document("balanced", "campaign-fixture", [])
    assert "requested_us" in report and "realized_us" in report
    assert report["requested_us"] == [150, 200, 300, 500, 750, 1000]
    assert report["realized_us"] == [150, 200, 300, 500, 750, 1000]
    assert report["requested_us"] is not report["realized_us"]
    report["requested_us"].append(9999)
    assert report["realized_us"] == [150, 200, 300, 500, 750, 1000]


def test_t2418_exact_grid_identity_order_and_disclosure_are_literal_pinned():
    assert M.T2418_RUN_KIND == "t2418-explore"
    assert M.T2418_REQUESTED_US == (2000, 4000, 9999)
    assert M.T2418_REALIZED_US == (2000, 4000, 9999)
    assert M.T2418_UNREALIZED == {}
    assert M.T2418_REPORT_SCHEMA == "t2418-backoff-static-explore-report/v2"
    assert M.T2418_CLAIM_SCOPE == (
        "exploratory_backoff_tail_only_not_formal_series"
    )
    assert M.T2418_FORMAL_GRID_STATUS == "not_selected_in_this_wave"
    assert M.T2418_FORMAL_STOPPING_CRITERION_STATUS == (
        "not_defined_in_this_wave"
    )
    assert M.T2418_MEANING_WITNESS_STATUS == (
        "driver_declared_static_backoff_physical_us"
    )
    assert p2_2.REPS == 5
    assert p2_2.EXTIME == 3

    unshuffled = M._t2418_points("balanced")
    assert [
        (flags["BACK_OFF"], flags["BACKOFF_FIXED"])
        for _label, flags in unshuffled
    ] == [(0, -1), (1, -1), (1, 4000), (1, 6000), (1, 11999)]
    assert [label for label, _flags in unshuffled] == [
        "none", "adaptive", "fixed-2000us", "fixed-4000us", "fixed-9999us",
    ]

    labels = [
        "none", "adaptive", "fixed-2000us", "fixed-4000us", "fixed-9999us",
    ]
    seeds = {
        "write-heavy": 0xB10005,
        "balanced": 0xB10050,
        "read-heavy": 0xB10095,
    }
    for tag, seed in seeds.items():
        expected_order = list(labels)
        random.Random(seed).shuffle(expected_order)
        assert M.t2418_measurement_order(tag) == expected_order
        assert len(M.t2418_genomes(tag)) == 5
        assert len({genome.canonical() for genome in M.t2418_genomes(tag)}) == 5

    cfg = M.t2418_config_for("balanced", M.WORKLOAD_BY_TAG["balanced"])
    assert cfg.spec_slug == "t2418-backoff-static-explore-v2-silo-balanced"
    assert cfg.search_tag == "sweep"
    assert cfg.trial == "t2418-backoff-static-explore-v2"
    assert cfg.search_config["scale"] == "t2418-backoff-static-explore-v2"
    assert cfg.spec_content == (
        "T-2418 exploratory static-backoff right-tail measurement; "
        "not a formal series; workload=balanced"
    )
    disclosure = {
        key: cfg.search_config[key]
        for key in (
            "run_kind", "claim_scope", "exploratory", "formal_series",
            "declared_use_class", "exploration_values_us", "requested_us",
            "realized_us", "unrealized", "formal_grid_status",
            "formal_stopping_criterion_status", "meaning_witness_status",
            "reps", "extime_s", "records", "threads",
        )
    }
    assert disclosure == {
        "run_kind": "t2418-explore",
        "claim_scope": "exploratory_backoff_tail_only_not_formal_series",
        "exploratory": True,
        "formal_series": False,
        "declared_use_class": "official",
        "exploration_values_us": [2000, 4000, 9999],
        "requested_us": [2000, 4000, 9999],
        "realized_us": [2000, 4000, 9999],
        "unrealized": [],
        "formal_grid_status": "not_selected_in_this_wave",
        "formal_stopping_criterion_status": "not_defined_in_this_wave",
        "meaning_witness_status": (
            "driver_declared_static_backoff_physical_us"
        ),
        "reps": 5,
        "extime_s": 3,
        "records": 1_000_000,
        "threads": 48,
    }
    assert [
        (point["flags"]["BACK_OFF"], point["flags"]["BACKOFF_FIXED"])
        for point in cfg.search_config["grid"]
    ] == [(0, -1), (1, -1), (1, 4000), (1, 6000), (1, 11999)]


def test_t2266_real_rep_capture_flows_through_wal_consumer_for_every_rep(
        tmp_path, monkeypatch):
    capture = M._T2266RepCapture()
    expected_abort_rates = []
    with capture.installed():
        for point_index in range(8):
            expected_abort_rates.append(_measure_t2266_round(capture, point_index))
    view = _t2266_certified_view(tmp_path, capture)
    bench_payloads = [
        record.payload
        for record in view.records
        if record.stage == M.wal.STAGE_BENCH_DONE
    ]
    assert len(bench_payloads) == 8
    assert all(type(payload["tps"]) is tuple for payload in bench_payloads)
    assert all(
        type(payload["leading_indicators"]) is MappingProxyType
        for payload in bench_payloads
    )

    def discover(slug, search_tag, output_root, *, purpose):
        assert slug == "t2266-backoff-static-tail-v2-silo-balanced"
        assert search_tag == "sweep"
        assert output_root == str(tmp_path)
        assert purpose is M.CampaignReadPurpose.CERTIFIED_ACCEPTANCE
        return view

    # Redirect only the filesystem locator; certified-view validation and WAL
    # replay remain the production consumers used by materialize_t2266_report.
    monkeypatch.setattr(M, "discover_campaign_dir", discover)

    paths = M.materialize_t2266_report("balanced", str(tmp_path), capture)
    document = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    dat = Path(paths["dat"]).read_text(encoding="utf-8")

    assert document["schema_version"] == "t2266-backoff-static-tail-report/v2"
    assert document["run_kind"] == M.T2266_RUN_KIND
    assert document["claim_scope"] == "descriptive_backoff_shape_only"
    assert document["source_measurement"] == "trace_disabled"
    assert document["performance_certified"] is False
    assert document["correctness_verified"] is True
    assert document["requested_us"] == [150, 200, 300, 500, 750, 1000]
    assert document["realized_us"] == [150, 200, 300, 500, 750, 1000]
    assert len(document["points"]) == 8
    endpoint = next(point for point in document["points"] if point["kind"] == "static" and point["backoff_us"] == 1000)
    assert endpoint["label"] == "fixed-1000us"
    assert "BACKOFF_FIXED=3000" in endpoint["genome"]
    for point_index, point in enumerate(document["points"]):
        assert len(point["reps"]) == p2_2.REPS
        assert point["throughput_tps_reps"] == (
            capture.rounds[point_index]["throughput_tps"]
        )
        assert point["throughput_tps_reps"] == [
            rep["throughput_tps"] for rep in point["reps"]
        ]
        assert point["abort_rate_reps"] == expected_abort_rates[point_index]
        assert point["abort_rate_reps"] == [
            rep["abort_rate"] for rep in point["reps"]
        ]
        assert point["certified"] is False
        assert point["performance_certified"] is False
        assert point["correctness_verified"] is True
    assert '"claim_scope":"descriptive_backoff_shape_only"' in dat
    assert '"source_measurement":"trace_disabled"' in dat
    assert '"performance_certified":false' in dat
    assert '"correctness_verified":true' in dat


def test_t2418_v2_discovery_does_not_select_v1(tmp_path, monkeypatch):
    """Real filesystem discovery; admitted WAL view supplied at the read boundary."""
    from dataclasses import replace
    from orchestrator.campaign import replay

    capture = M._T2418RepCapture()
    with capture.installed():
        for point_index in range(5):
            _measure_t2418_round(capture, point_index)
    view = _t2418_certified_view(tmp_path, capture)
    old_root = tmp_path / "campaigns" / (
        "t2418-backoff-static-explore-v1-silo-balanced-sweep-old"
    )
    (old_root / "runs").mkdir(parents=True)
    (old_root / "runs" / "wal.jsonl").write_text("", encoding="utf-8")
    selected = []

    def admitted(layout, *, purpose):
        selected.append(layout.root)
        assert purpose is M.CampaignReadPurpose.CERTIFIED_ACCEPTANCE
        assert Path(layout.root) == new_root
        return replace(
            view, layout=layout,
            _certification_token=artifact_admission._CERTIFIED_VIEW_TOKEN,
        )

    monkeypatch.setattr(replay, "require_admitted_campaign", admitted)
    with pytest.raises(FileNotFoundError, match="0 個"):
        M._load_t2418_report_points("balanced", str(tmp_path), capture)
    assert selected == []
    new_root = tmp_path / "campaigns" / (
        "t2418-backoff-static-explore-v2-silo-balanced-sweep-new"
    )
    (new_root / "runs").mkdir(parents=True)
    (new_root / "runs" / "wal.jsonl").write_text("", encoding="utf-8")
    campaign_id, points = M._load_t2418_report_points(
        "balanced", str(tmp_path), capture,
    )
    assert selected == [str(new_root)]
    assert campaign_id == new_root.name and len(points) == 5
    assert (old_root / "runs" / "wal.jsonl").read_bytes() == b""


def test_t2418_frozen_wal_view_flows_through_capture_loader_and_reports(
        tmp_path, monkeypatch):
    capture = M._T2418RepCapture()
    expected_abort_rates = []
    with capture.installed():
        for point_index in range(5):
            expected_abort_rates.append(_measure_t2418_round(capture, point_index))
    view = _t2418_certified_view(tmp_path, capture)
    bench_payloads = [
        record.payload
        for record in view.records
        if record.stage == M.wal.STAGE_BENCH_DONE
    ]
    assert len(bench_payloads) == 5
    assert [type(payload["tps"]) for payload in bench_payloads] == [tuple] * 5
    assert [
        type(payload["leading_indicators"]) for payload in bench_payloads
    ] == [MappingProxyType] * 5

    def discover(slug, search_tag, output_root, *, purpose):
        assert slug == "t2418-backoff-static-explore-v2-silo-balanced"
        assert search_tag == "sweep"
        assert output_root == str(tmp_path)
        assert purpose is M.CampaignReadPurpose.CERTIFIED_ACCEPTANCE
        return view

    monkeypatch.setattr(M, "discover_campaign_dir", discover)
    paths = M.materialize_t2418_report("balanced", str(tmp_path), capture)
    assert Path(paths["dat"]).name == (
        "t2418-backoff-static-explore-balanced.dat"
    )
    assert Path(paths["json"]).name == (
        "t2418-backoff-static-explore-balanced.json"
    )
    document = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    dat_lines = Path(paths["dat"]).read_text(encoding="utf-8").splitlines()

    disclosure_keys = (
        "run_kind", "claim_scope", "exploratory", "formal_series",
        "declared_use_class", "exploration_values_us", "requested_us",
        "realized_us", "unrealized", "formal_grid_status",
        "formal_stopping_criterion_status", "meaning_witness_status",
        "reps", "extime_s", "records", "threads",
    )
    expected_disclosure = {
        "run_kind": "t2418-explore",
        "claim_scope": "exploratory_backoff_tail_only_not_formal_series",
        "exploratory": True,
        "formal_series": False,
        "declared_use_class": "official",
        "exploration_values_us": [2000, 4000, 9999],
        "requested_us": [2000, 4000, 9999],
        "realized_us": [2000, 4000, 9999],
        "unrealized": [],
        "formal_grid_status": "not_selected_in_this_wave",
        "formal_stopping_criterion_status": "not_defined_in_this_wave",
        "meaning_witness_status": (
            "driver_declared_static_backoff_physical_us"
        ),
        "reps": 5,
        "extime_s": 3,
        "records": 1_000_000,
        "threads": 48,
    }
    assert document["schema_version"] == (
        "t2418-backoff-static-explore-report/v2"
    )
    assert {key: document[key] for key in disclosure_keys} == expected_disclosure
    assert document["campaign_id"] == "t2418-fixture-campaign"
    assert document["workload"] == "balanced"
    assert document["source_measurement"] == "trace_disabled"
    assert document["performance_certified"] is False
    assert document["correctness_verified"] is True
    assert len(document["points"]) == 5
    for point_index, point in enumerate(document["points"]):
        assert len(point["reps"]) == 5
        assert point["throughput_tps_reps"] == (
            capture.rounds[point_index]["throughput_tps"]
        )
        assert point["abort_rate_reps"] == expected_abort_rates[point_index]
        assert point["claim_scope"] == (
            "exploratory_backoff_tail_only_not_formal_series"
        )
        assert point["source_measurement"] == "trace_disabled"
        assert point["correctness_verified"] is True
        assert point["performance_certified"] is False
        assert point["certified"] is False

    provenance_line = next(
        line for line in dat_lines if line.startswith("# provenance: ")
    )
    provenance = json.loads(provenance_line.removeprefix("# provenance: "))
    assert {key: provenance[key] for key in disclosure_keys} == expected_disclosure
    data_rows = [line.split() for line in dat_lines if not line.startswith("#")]
    assert [int(row[0]) for row in data_rows] == [2000, 4000, 9999]
    assert len(data_rows) == 3


def test_t2418_frozen_campaign_is_rejected_by_existing_t2266_consumer(
        tmp_path, monkeypatch):
    capture = M._T2418RepCapture()
    with capture.installed():
        for point_index in range(5):
            _measure_t2418_round(capture, point_index)
    view = _t2418_certified_view(tmp_path, capture)
    assert any(
        type(record.payload.get("tps")) is tuple
        for record in view.records
        if record.stage == M.wal.STAGE_BENCH_DONE
    )
    monkeypatch.setattr(M, "discover_campaign_dir", lambda *_args, **_kwargs: view)

    with pytest.raises(
            RuntimeError, match="T-2266 committed genome set differs"):
        M._load_t2266_report_points("balanced", str(tmp_path), capture)


def test_t2266_rep_capture_rejects_extra_abort_parser_call():
    capture = M._T2266RepCapture()
    with capture.installed():
        with pytest.raises(RuntimeError, match="exactly one abort parser call"):
            _measure_t2266_round(capture, 0, extra_parser_call=True)
    assert capture.rounds == []


def test_t2266_report_writers_are_create_only(tmp_path):
    dat_path = tmp_path / "tail.dat"
    json_path = tmp_path / "tail.json"
    M._write_create_only_text(dat_path, "first\n")
    M._write_create_only_json(json_path, {"first": True})

    with pytest.raises(FileExistsError):
        M._write_create_only_text(dat_path, "replacement\n")
    with pytest.raises(FileExistsError):
        M._write_create_only_json(json_path, {"first": False})
    assert dat_path.read_text(encoding="utf-8") == "first\n"
    assert json.loads(json_path.read_text(encoding="utf-8")) == {"first": True}


def test_applied_tree_contains_the_backoff_fixed_build_surface(tmp_path):
    cmake = tmp_path / "cmake"
    include = tmp_path / "include"
    cmake.mkdir()
    include.mkdir()
    (cmake / "Options.cmake").write_text(
        "set(CCBENCH_BACKOFF_FIXED -1 CACHE STRING fixture)\n"
        "BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}\n",
        encoding="utf-8",
    )
    backoff = include / "backoff.hh"
    backoff.write_text(
        "#ifndef BACKOFF_FIXED\n#endif\n#if BACKOFF_FIXED >= 0\n#endif\n",
        encoding="utf-8",
    )
    M._assert_backoff_fixed_materialized(str(tmp_path))

    backoff.write_text("#ifndef BACKOFF_FIXED\n#endif\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="patch is not materialized"):
        M._assert_backoff_fixed_materialized(str(tmp_path))


def test_both_drivers_accept_the_same_explicit_ccbench_worktree_cli(monkeypatch):
    observed = []
    total = len(M.genomes("balanced"))

    def run_workload(*_args, **kwargs):
        observed.append(("sweep", kwargs["ccbench_dir"]))
        return SimpleNamespace(committed=total, aborted=0, campaign_id="cid")

    def measure(*_args, **kwargs):
        observed.append(("aa", kwargs["ccbench_dir"]))
        return {"record_count": total * O.REPS, "manifest": "/result/manifest.json"}

    monkeypatch.setattr(M, "run_workload", run_workload)
    monkeypatch.setattr(O, "measure", measure)
    common = [
        "balanced", "--output-root", "/outside/root",
        "--cache-root", "/scratch/cache",
        "--ccbench-dir", "/scratch/ccbench-source",
    ]
    assert M.main(common) == 0
    assert O.main(common) == 0
    assert observed == [
        ("sweep", "/scratch/ccbench-source"),
        ("aa", "/scratch/ccbench-source"),
    ]
    assert O._resolve_ccbench_dir is M._resolve_ccbench_dir


def test_invalid_explicit_worktree_cannot_fall_back_to_valid_shared_tree(
        tmp_path, monkeypatch):
    repository, expected, other = _fixture_git_repository(tmp_path)
    shared = tmp_path / "shared-ccbench"
    invalid = tmp_path / "invalid-ccbench"
    _add_detached_worktree(repository, shared, expected)
    _add_detached_worktree(repository, invalid, other)
    monkeypatch.setattr(M.pin, "CURRENT_PIN", expected[:7])
    fallback_calls = []

    def shared_fallback():
        fallback_calls.append("shared")
        return str(shared)

    monkeypatch.setattr(M.buildcache, "_ccbench_dir", shared_fallback)
    assert M._resolve_ccbench_dir(str(shared)) == str(shared.resolve())
    assert M._resolve_ccbench_dir(None) == str(shared)
    assert fallback_calls == ["shared"]

    with pytest.raises(RuntimeError, match="HEAD mismatch"):
        M._resolve_ccbench_dir(str(invalid))
    assert fallback_calls == ["shared"]

    (shared / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="tracked modifications"):
        M._resolve_ccbench_dir(str(shared))
    assert fallback_calls == ["shared"]


def test_distinct_backoff_fixed_amounts_produce_distinct_build_results(monkeypatch):
    points = [
        M.Genome("silo", {"BACK_OFF": 1, "BACKOFF_FIXED": amount})
        for amount in (5, 10)
    ]
    build_events = []

    def resolve_evidence(genome, *_args, **_kwargs):
        return SimpleNamespace(
            src_token=f"source-{genome.flags['BACKOFF_FIXED']}",
        )

    def build_v2(genome, **kwargs):
        amount = genome.flags["BACKOFF_FIXED"]
        build_events.append((amount, kwargs["trace"]))
        return M.buildcache.BuildResult(
            genome=genome, trace=kwargs["trace"], binary=f"/bin/fixed-{amount}",
            bin_sha256=hashlib.sha256(f"binary-{amount}".encode()).hexdigest(),
            build_dir=f"/build/fixed-{amount}", cached=False,
        )

    monkeypatch.setattr(M.source_digest, "resolve_evidence", resolve_evidence)
    monkeypatch.setattr(M, "derive_build_admission", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(M.buildcache, "build_v2", build_v2)
    built = M._prebuild_backoff_binaries(
        points,
        contract=object(),
        cache_root="/cache",
        ccbench_dir="/ccbench",
        resolved_cc="cc",
        resolved_cxx="c++",
        expected_toolchain_manifest={},
        build_context=object(),
        capability_resolver=lambda _evidence: object(),
        trace_modes=(False,),
    )
    hashes = [built[(point.canonical(), False)].bin_sha256 for point in points]
    assert build_events == [(5, False), (10, False)]
    assert len(set(hashes)) == 2


def test_real_extended_driver_gate_recomputes_preprocessed_file_digest():
    """The real extended-driver wrapper admits an effective owner-TU request."""
    _available_executable("cmake")
    source_root = _condition_fixture("supplied")
    run = M._require_condition_gate_before_measurement(
        str(source_root),
        stock_root=str(source_root / "stock"),
        points=[M.Genome("silo", {"BACKOFF_FIXED": 5})],
        cxx=_available_executable("g++-13", "g++-12", "g++"),
    )

    supply = run.supply_records[0]
    assert run.admission.admitted is True
    assert supply.driver_id == "orchestrator/campaign/backoff_extended_sweep.py"
    assert _independent_replay_digest(supply) == supply.evidence["requested_digest"]


def test_extended_gate_wrapper_forwards_configure_args(monkeypatch):
    observed = []
    configure_args = ("-DFETCHCONTENT_BASE_DIR=/canonical/base",)

    def require_gate(*args, **kwargs):
        observed.append((args, kwargs))
        return object()

    monkeypatch.setattr(M, "_require_backoff_condition_gate", require_gate)
    result = M._require_condition_gate_before_measurement(
        "/patched",
        stock_root="/stock",
        points=[M.Genome("silo", {"BACKOFF_FIXED": 5})],
        cxx="c++",
        configure_args=configure_args,
    )

    assert result is not None
    assert len(observed) == 1
    assert observed[0][1]["configure_args"] is configure_args


def test_duplicate_static_binary_hash_stops_before_campaign(monkeypatch):
    points = [
        M.Genome("silo", {"BACK_OFF": 1, "BACKOFF_FIXED": amount})
        for amount in (5, 10)
    ]
    shared_sha256 = hashlib.sha256(b"same-binary").hexdigest()
    monkeypatch.setattr(
        M.source_digest, "resolve_evidence",
        lambda genome, *_args, **_kwargs: SimpleNamespace(
            src_token=f"source-{genome.flags['BACKOFF_FIXED']}",
        ),
    )
    monkeypatch.setattr(M, "derive_build_admission", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(
        M.buildcache, "build_v2",
        lambda genome, **kwargs: M.buildcache.BuildResult(
            genome=genome, trace=kwargs["trace"], binary="/bin/shared",
            bin_sha256=shared_sha256, build_dir="/build/shared", cached=False,
        ),
    )
    with pytest.raises(RuntimeError, match="produced the same binary"):
        M._prebuild_backoff_binaries(
            points,
            contract=object(),
            cache_root="/cache",
            ccbench_dir="/ccbench",
            resolved_cc="cc",
            resolved_cxx="c++",
            expected_toolchain_manifest={},
            build_context=object(),
            capability_resolver=lambda _evidence: object(),
            trace_modes=(False,),
        )


def test_t2266_none_and_adaptive_must_have_distinct_perf_binaries(monkeypatch):
    points = M.t2266_genomes("balanced")
    shared_reference_sha256 = hashlib.sha256(b"same-reference-binary").hexdigest()

    monkeypatch.setattr(
        M.source_digest, "resolve_evidence",
        lambda genome, *_args, **_kwargs: SimpleNamespace(
            src_token=hashlib.sha256(genome.canonical().encode()).hexdigest(),
        ),
    )
    monkeypatch.setattr(M, "derive_build_admission", lambda *_args, **_kwargs: object())

    def build_v2(genome, **kwargs):
        amount = genome.flags["BACKOFF_FIXED"]
        sha256 = (
            shared_reference_sha256
            if amount == -1 else hashlib.sha256(genome.canonical().encode()).hexdigest()
        )
        return M.buildcache.BuildResult(
            genome=genome,
            trace=kwargs["trace"],
            binary=f"/bin/t2266-{genome.canonical()}",
            bin_sha256=sha256,
            build_dir=f"/build/t2266-{amount}",
            cached=False,
        )

    monkeypatch.setattr(M.buildcache, "build_v2", build_v2)
    with pytest.raises(RuntimeError, match="T-2266 genomes produced the same binary"):
        M._prebuild_backoff_binaries(
            points,
            contract=object(),
            cache_root="/cache",
            ccbench_dir="/ccbench",
            resolved_cc="cc",
            resolved_cxx="c++",
            expected_toolchain_manifest={},
            build_context=object(),
            capability_resolver=lambda _evidence: object(),
            trace_modes=(False,),
            require_all_binary_hashes=True,
        )


def test_t2418_prebuild_requires_five_distinct_trace_disabled_binaries(
        monkeypatch):
    points = M.t2418_genomes("balanced")
    monkeypatch.setattr(
        M.source_digest, "resolve_evidence",
        lambda genome, *_args, **_kwargs: SimpleNamespace(
            src_token=hashlib.sha256(genome.canonical().encode()).hexdigest(),
        ),
    )
    monkeypatch.setattr(M, "derive_build_admission", lambda *_args, **_kwargs: object())

    def build_v2(genome, **kwargs):
        return M.buildcache.BuildResult(
            genome=genome,
            trace=kwargs["trace"],
            binary=f"/bin/t2418-{hashlib.sha256(genome.canonical().encode()).hexdigest()}",
            bin_sha256=hashlib.sha256(
                ("unique-" + genome.canonical()).encode()
            ).hexdigest(),
            build_dir=f"/build/t2418-{genome.flags['BACKOFF_FIXED']}",
            cached=False,
        )

    monkeypatch.setattr(M.buildcache, "build_v2", build_v2)
    built = M._prebuild_backoff_binaries(
        points,
        contract=object(),
        cache_root="/cache",
        ccbench_dir="/ccbench",
        resolved_cc="cc",
        resolved_cxx="c++",
        expected_toolchain_manifest={},
        build_context=object(),
        capability_resolver=lambda _evidence: object(),
        trace_modes=(False,),
        require_all_t2418_binary_hashes=True,
    )
    assert len(built) == 5
    assert len({result.bin_sha256 for result in built.values()}) == 5

    shared_reference_sha256 = hashlib.sha256(b"same-reference").hexdigest()

    def duplicate_reference_build(genome, **kwargs):
        sha256 = (
            shared_reference_sha256
            if genome.flags["BACKOFF_FIXED"] == -1
            else hashlib.sha256(genome.canonical().encode()).hexdigest()
        )
        return M.buildcache.BuildResult(
            genome=genome,
            trace=kwargs["trace"],
            binary=f"/bin/t2418-{genome.flags['BACK_OFF']}",
            bin_sha256=sha256,
            build_dir=f"/build/t2418-{genome.flags['BACKOFF_FIXED']}",
            cached=False,
        )

    monkeypatch.setattr(M.buildcache, "build_v2", duplicate_reference_build)
    with pytest.raises(RuntimeError, match="T-2418 genomes produced the same binary"):
        M._prebuild_backoff_binaries(
            points,
            contract=object(),
            cache_root="/cache",
            ccbench_dir="/ccbench",
            resolved_cc="cc",
            resolved_cxx="c++",
            expected_toolchain_manifest={},
            build_context=object(),
            capability_resolver=lambda _evidence: object(),
            trace_modes=(False,),
            require_all_t2418_binary_hashes=True,
        )


def test_t2418_binary_identity_rejects_incomplete_or_malformed_bindings():
    points = M.t2418_genomes("balanced")

    def result(genome, *, trace=False, sha256=None):
        return M.buildcache.BuildResult(
            genome=genome,
            trace=trace,
            binary="/bin/t2418",
            bin_sha256=(
                sha256
                if sha256 is not None
                else hashlib.sha256(genome.canonical().encode()).hexdigest()
            ),
            build_dir="/build/t2418",
            cached=False,
        )

    builds = {
        (genome.canonical(), False): result(genome) for genome in points
    }
    M._require_distinct_t2418_binary_hashes(builds, points)

    with pytest.raises(RuntimeError, match="exactly five genomes"):
        M._require_distinct_t2418_binary_hashes(builds, points[:4])

    malformed = dict(builds)
    malformed[(points[0].canonical(), False)] = object()
    with pytest.raises(RuntimeError, match="every trace-disabled BuildResult"):
        M._require_distinct_t2418_binary_hashes(malformed, points)

    malformed = dict(builds)
    malformed[(points[0].canonical(), False)] = result(points[0], trace=True)
    with pytest.raises(RuntimeError, match="lost its genome binding"):
        M._require_distinct_t2418_binary_hashes(malformed, points)

    malformed = dict(builds)
    malformed[(points[0].canonical(), False)] = result(points[1])
    with pytest.raises(RuntimeError, match="lost its genome binding"):
        M._require_distinct_t2418_binary_hashes(malformed, points)

    malformed = dict(builds)
    malformed[(points[0].canonical(), False)] = result(points[0], sha256="short")
    with pytest.raises(RuntimeError, match="non-canonical binary sha256"):
        M._require_distinct_t2418_binary_hashes(malformed, points)

    malformed = dict(builds)
    shared = hashlib.sha256(b"shared").hexdigest()
    malformed[(points[0].canonical(), False)] = result(points[0], sha256=shared)
    malformed[(points[1].canonical(), False)] = result(points[1], sha256=shared)
    with pytest.raises(RuntimeError, match="T-2418 genomes produced the same binary"):
        M._require_distinct_t2418_binary_hashes(malformed, points)

    repeated = [*points[:4], points[0]]
    with pytest.raises(RuntimeError, match="identity check is incomplete"):
        M._require_distinct_t2418_binary_hashes(builds, repeated)


def test_mu4_workload_literal_oracle_reaches_config_diagnostic_and_argv():
    oracle = {
        "write-heavy": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"},
        "balanced": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"},
        "read-heavy": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"},
    }
    contract = SimpleNamespace(clocks_per_us=2100)
    assert M.WORKLOAD_BY_TAG == oracle
    for tag, workload in oracle.items():
        assert M.config_for(tag, workload).search_config["ycsb"] == workload
        argv = O._flags(workload, contract)
        assert f"-ycsb_zipf_skew={workload['ycsb_zipf_skew']}" in argv
        assert f"-ycsb_rratio={workload['ycsb_rratio']}" in argv
        assert f"-ycsb_rmw={workload['ycsb_rmw']}" in argv


def test_mu11_measurement_order_is_the_registered_seeded_permutation():
    seeds = {
        "write-heavy": 0xB10005,
        "balanced": 0xB10050,
        "read-heavy": 0xB10095,
    }
    labels = ["none", "adaptive", *[f"fixed-{amount}us" for amount in M.EXTENDED_SWEEP_US]]
    for tag, seed in seeds.items():
        expected = list(labels)
        random.Random(seed).shuffle(expected)
        assert M.measurement_order(tag) == expected
        assert M.config_for(tag, M.WORKLOAD_BY_TAG[tag]).search_config["measurement_order"] == expected
        assert expected != labels


def test_measurement_seed_changes_the_real_campaign_id(monkeypatch):
    context = build_admission.build_run_context(
        generator_id=build_admission.GeneratorId.BACKOFF_SWEEP,
    )
    workload = M.WORKLOAD_BY_TAG["balanced"]
    first = ident.bind_admission_policy(M.config_for("balanced", workload), context.policy)
    first_id = ident.campaign_id(first)
    monkeypatch.setitem(M.MEASUREMENT_SEEDS, "balanced", M.MEASUREMENT_SEEDS["balanced"] + 1)
    second = ident.bind_admission_policy(M.config_for("balanced", workload), context.policy)
    second_id = ident.campaign_id(second)
    assert first_id != second_id


def test_mu13_run_path_uses_the_calibration_bound_records(monkeypatch):
    contract = p2_2._legacy_linux_contract()
    authorization = env_contract.authorize(contract.env_tag)
    observed = {}
    events = _stub_patch_and_prebuild(monkeypatch)
    monkeypatch.setattr(M.p2_2, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(
        M.p2_2,
        "resolve_site_runtime",
        lambda: (site_policy.OTHER, contract, authorization),
    )

    def calibration(candidate):
        observed["calibration_contract"] = candidate

    monkeypatch.setattr(M.p2_2, "_assert_matches_calibration", calibration)
    monkeypatch.setattr(M.buildcache, "compilers_for_current_site", lambda: ("cc", "c++"))
    monkeypatch.setattr(M.buildcache, "observed_toolchain_manifest", lambda *_args: {"cc": {}, "cxx": {}})

    def run_campaign(*args, **_kwargs):
        events.append(("campaign",))
        observed["config"] = args[0]
        observed["perf"] = args[2]
        observed["cache_root"] = _kwargs["cache_root"]
        return SimpleNamespace(committed=31, aborted=0, campaign_id="cid")

    monkeypatch.setattr(M, "run_campaign", run_campaign)
    M.run_workload(
        "balanced", M.WORKLOAD_BY_TAG["balanced"], log=lambda *_args: None,
        cache_root="/tmp/b10-test-cache",
    )
    assert observed["calibration_contract"] is contract
    assert observed["perf"].records == p2_2.RECORDS == 1_000_000
    assert observed["config"].search_config["records"] == 1_000_000
    assert observed["cache_root"] == "/tmp/b10-test-cache"
    assert [event[0] for event in events] == [
        "patch-enter", "patch-materialized", "masstree-prepare",
        "condition-gate", "prebuild", "campaign", "patch-exit",
    ]
    argv = O._flags(M.WORKLOAD_BY_TAG["balanced"], contract)
    assert "-ycsb_tuple_num=1000000" in argv


def test_extended_run_path_prepares_and_gates_the_same_patched_tree(
        tmp_path, monkeypatch):
    contract = p2_2._legacy_linux_contract()
    authorization = env_contract.authorize(contract.env_tag)
    events = _stub_patch_and_prebuild(monkeypatch)
    patched_root = tmp_path / "ccbench"
    patched_root.mkdir()
    monkeypatch.setattr(M, "_resolve_ccbench_dir", lambda _value: str(patched_root))
    monkeypatch.setattr(M.p2_2, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(
        M.p2_2,
        "resolve_site_runtime",
        lambda: (site_policy.OTHER, contract, authorization),
    )
    monkeypatch.setattr(M.p2_2, "_assert_matches_calibration", lambda _contract: None)
    monkeypatch.setattr(
        M.buildcache, "compilers_for_current_site", lambda: ("cc", "c++"),
    )
    monkeypatch.setattr(
        M.buildcache,
        "observed_toolchain_manifest",
        lambda *_args: {"cc": {}, "cxx": {}},
    )

    def run_campaign(*args, **kwargs):
        events.append(("campaign", args, kwargs))
        return SimpleNamespace(total=8, committed=7, aborted=0, campaign_id="cid")

    monkeypatch.setattr(M, "run_campaign", run_campaign)

    M.run_workload(
        "balanced",
        M.WORKLOAD_BY_TAG["balanced"],
        log=lambda *_args: None,
        cache_root=str(tmp_path / "cache"),
        ccbench_dir=str(patched_root),
        run_kind=M.T2266_RUN_KIND,
    )

    prepare_events = [event for event in events if event[0] == "masstree-prepare"]
    gate_events = [event for event in events if event[0] == "condition-gate"]
    prebuild_events = [event for event in events if event[0] == "prebuild"]
    campaign_events = [event for event in events if event[0] == "campaign"]
    assert len(prepare_events) == 1
    assert len(gate_events) == 1
    assert len(prebuild_events) == 1
    assert len(campaign_events) == 1
    prepare = prepare_events[0][1]
    gate_args, gate_kwargs = gate_events[0][1:]
    prebuild_kwargs = prebuild_events[0][2]
    campaign_kwargs = campaign_events[0][2]
    canonical_base = prepare["fetchcontent_base_dir"]
    assert gate_kwargs["configure_args"] == (
        f"-DFETCHCONTENT_BASE_DIR={canonical_base}",
    )
    observed_roots = {
        Path(prepare["ccbench_dir"]).resolve(),
        Path(gate_args[0]).resolve(),
        Path(prebuild_kwargs["ccbench_dir"]).resolve(),
        Path(campaign_kwargs["ccbench_dir"]).resolve(),
    }
    assert observed_roots == {patched_root.resolve()}
    assert patched_root.resolve() != Path(gate_kwargs["stock_root"]).resolve()
    assert {
        point.flags["BACKOFF_FIXED"] for point in gate_kwargs["points"]
    } == {-1, 150, 200, 300, 500, 750, 3000}
    assert prepare["site"] == site_policy.OTHER
    assert "dependency_prefix" not in prepare


def test_t2418_run_path_uses_exact_five_genomes_and_shared_campaign_call(
        tmp_path, monkeypatch):
    contract = p2_2._legacy_linux_contract()
    authorization = env_contract.authorize(contract.env_tag)
    events = _stub_patch_and_prebuild(monkeypatch)
    patched_root = tmp_path / "ccbench"
    patched_root.mkdir()
    monkeypatch.setattr(M, "_resolve_ccbench_dir", lambda _value: str(patched_root))
    monkeypatch.setattr(M.p2_2, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(
        M.p2_2,
        "resolve_site_runtime",
        lambda: (site_policy.OTHER, contract, authorization),
    )
    monkeypatch.setattr(M.p2_2, "_assert_matches_calibration", lambda _contract: None)
    monkeypatch.setattr(
        M.buildcache, "compilers_for_current_site", lambda: ("cc", "c++"),
    )
    monkeypatch.setattr(
        M.buildcache,
        "observed_toolchain_manifest",
        lambda *_args: {"cc": {}, "cxx": {}},
    )

    committed_results = iter((4, 5))

    def run_campaign(*args, **kwargs):
        events.append(("campaign", args, kwargs))
        return SimpleNamespace(
            total=5, committed=next(committed_results), aborted=0,
            campaign_id="cid",
        )

    monkeypatch.setattr(M, "run_campaign", run_campaign)
    materialize_calls = []

    def materialize_t2418_report(*args, **kwargs):
        materialize_calls.append((args, kwargs))
        return {"dat": "/fixture/report.dat", "json": "/fixture/report.json"}

    monkeypatch.setattr(M, "materialize_t2418_report", materialize_t2418_report)
    M.run_workload(
        "balanced",
        M.WORKLOAD_BY_TAG["balanced"],
        log=lambda *_args: None,
        cache_root=str(tmp_path / "cache"),
        ccbench_dir=str(patched_root),
        run_kind=M.T2418_RUN_KIND,
    )
    assert len(materialize_calls) == 0

    assert [event[0] for event in events] == [
        "patch-enter", "patch-materialized", "masstree-prepare",
        "condition-gate", "prebuild", "campaign", "patch-exit",
    ]
    gate_event = next(event for event in events if event[0] == "condition-gate")
    prebuild_event = next(event for event in events if event[0] == "prebuild")
    campaign_event = next(event for event in events if event[0] == "campaign")
    flag_by_label = {
        "none": (0, -1),
        "adaptive": (1, -1),
        "fixed-2000us": (1, 4000),
        "fixed-4000us": (1, 6000),
        "fixed-9999us": (1, 11999),
    }
    expected_labels = [
        "none", "adaptive", "fixed-2000us", "fixed-4000us", "fixed-9999us",
    ]
    random.Random(0xB10050).shuffle(expected_labels)
    expected_flags = [flag_by_label[label] for label in expected_labels]

    gate_points = gate_event[2]["points"]
    prebuild_points = prebuild_event[1][0]
    campaign_points = campaign_event[1][1]
    for actual in (gate_points, prebuild_points, campaign_points):
        assert [
            (genome.flags["BACK_OFF"], genome.flags["BACKOFF_FIXED"])
            for genome in actual
        ] == expected_flags
    assert gate_points is prebuild_points is campaign_points
    assert prebuild_event[2]["require_all_binary_hashes"] is False
    assert prebuild_event[2]["require_all_t2418_binary_hashes"] is True

    cfg = campaign_event[1][0]
    perf = campaign_event[1][2]
    assert cfg.spec_slug == "t2418-backoff-static-explore-v2-silo-balanced"
    assert cfg.search_config["run_kind"] == "t2418-explore"
    assert cfg.search_config["scale"] == "t2418-backoff-static-explore-v2"
    assert cfg.trial == "t2418-backoff-static-explore-v2"
    assert perf.reps == 5
    assert perf.extime == 3
    assert perf.records == 1_000_000
    assert perf.threads == 48

    M.run_workload(
        "balanced",
        M.WORKLOAD_BY_TAG["balanced"],
        log=lambda *_args: None,
        cache_root=str(tmp_path / "cache"),
        ccbench_dir=str(patched_root),
        run_kind=M.T2418_RUN_KIND,
    )
    assert len(materialize_calls) == 1


def test_all_genomes_must_be_committed_and_none_aborted(monkeypatch):
    total = len(M.genomes("balanced"))
    argv = [
        "balanced", "--output-root", "/outside/root",
        "--cache-root", "/tmp/b10-cache",
    ]
    for committed, aborted, expected in (
        (total, 0, 0), (total - 1, 0, 1), (total, 1, 1), (total + 1, 0, 1),
    ):
        monkeypatch.setattr(
            M, "run_workload",
            lambda *_args, _committed=committed, _aborted=aborted, **_kwargs:
                SimpleNamespace(
                    committed=_committed, aborted=_aborted, campaign_id="cid",
                ),
        )
        assert M.main(argv) == expected


def test_t2418_cli_requires_exact_five_and_both_report_artifacts(
        tmp_path, monkeypatch):
    def invoke(
            name, *, total=5, committed=5, aborted=0,
            dat=True, json_report=True):
        layout_root = tmp_path / name
        reports = layout_root / "reports"
        reports.mkdir(parents=True)
        stem = reports / "t2418-backoff-static-explore-balanced"
        if dat:
            Path(f"{stem}.dat").write_text("fixture\n", encoding="utf-8")
        if json_report:
            Path(f"{stem}.json").write_text("{}\n", encoding="utf-8")
        monkeypatch.setattr(
            M,
            "run_workload",
            lambda *_args, **_kwargs: SimpleNamespace(
                total=total,
                committed=committed,
                aborted=aborted,
                campaign_id=name,
                layout_root=str(layout_root),
            ),
        )
        return M.main([
            "balanced",
            "--output-root", str(tmp_path / f"output-{name}"),
            "--cache-root", str(tmp_path / f"cache-{name}"),
            "--run-kind", "t2418-explore",
        ])

    assert invoke("complete") == 0
    assert invoke("four-commits", committed=4) == 1
    assert invoke("wrong-total", total=4) == 1
    assert invoke("aborted", aborted=1) == 1
    assert invoke("missing-dat", dat=False) == 1
    assert invoke("missing-json", json_report=False) == 1


def _probe_error_receipt():
    def raising(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(["perf"], 1)
    return perf_preflight.probe_perf_availability(
        perf_candidates=(), subprocess_runner=raising,
    )


def test_probe_error_receipt_is_durable_before_loop_raises(tmp_path):
    receipt = _probe_error_receipt()
    path = tmp_path / "perf-preflight.json"
    with pytest.raises(perf_preflight.PerfPreflightError, match="判定不能"):
        loop._perform_perf_preflight(
            lambda **_kwargs: receipt, receipt_path=str(path),
        )
    assert json.loads(path.read_text(encoding="utf-8")) == receipt


def test_probe_error_driver_materializes_typed_stop_receipt(tmp_path, monkeypatch):
    contract = p2_2._legacy_linux_contract()
    authorization = env_contract.authorize(contract.env_tag)
    monkeypatch.setattr(M.p2_2, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(
        M.p2_2, "resolve_site_runtime",
        lambda: (site_policy.OTHER, contract, authorization),
    )
    monkeypatch.setattr(M.p2_2, "_assert_matches_calibration", lambda _contract: None)
    monkeypatch.setattr(M.buildcache, "compilers_for_current_site", lambda: ("cc", "c++"))
    monkeypatch.setattr(
        M.buildcache, "observed_toolchain_manifest", lambda *_args: {"cc": {}, "cxx": {}},
    )
    _stub_patch_and_prebuild(monkeypatch)
    receipt = _probe_error_receipt()

    def stopped_campaign(*_args, **kwargs):
        path = Path(kwargs["perf_preflight_receipt_path"])
        path.write_text(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        raise perf_preflight.PerfPreflightError("判定不能")

    monkeypatch.setattr(M, "run_campaign", stopped_campaign)
    cache_root = tmp_path / "cache"
    cache_root.mkdir()
    with pytest.raises(M.PreflightStop, match="before measurement"):
        M.run_workload(
            "balanced", M.WORKLOAD_BY_TAG["balanced"],
            output_root=str(tmp_path), cache_root=str(cache_root),
            log=lambda *_args: None,
        )
    stop = json.loads((
        tmp_path / "b10-backoff-grid-balanced-preflight-stop.json"
    ).read_text(encoding="utf-8"))
    assert stop["status"] == "preflight-error-no-verdict"
    assert stop["perf_preflight_receipt"]["status"] == "probe_error"

    def typed_stop(*_args, **_kwargs):
        raise M.PreflightStop("typed preflight stop")

    monkeypatch.setattr(M, "run_workload", typed_stop)
    assert M.main([
        "balanced", "--output-root", str(tmp_path),
        "--cache-root", str(cache_root),
    ]) == 2


def test_b10_pbs_payload_and_submit_wrapper_are_three_independent_jobs():
    root = Path(__file__).resolve().parents[2]
    job = (root / "tools/pegasus/b10_backoff_grid.sh").read_text(encoding="utf-8")
    submit = (root / "tools/pegasus/submit_b10_backoff_grid.sh").read_text(encoding="utf-8")
    assert "#PBS -q gen_S" in job
    assert "#PBS -A SFC" in job
    assert "#PBS -b 1" in job
    assert "#PBS -l elapstim_req=05:00:00" in job
    budget = _shell_integer_assignments(job, (
        "WORKTREE_SETUP_CAP_S", "SWEEP_CAP_S", "AA_CAP_S", "REPORT_CAP_S",
        "WORKTREE_CLEANUP_CAP_S", "FINALIZE_CAP_S", "EXPECTED_WALLTIME_S",
    ))
    assert budget["WORKTREE_SETUP_CAP_S"] == 120
    assert budget["SWEEP_CAP_S"] == 11700
    assert budget["AA_CAP_S"] == 3900
    assert budget["REPORT_CAP_S"] == 300
    assert budget["WORKTREE_CLEANUP_CAP_S"] == 120
    assert budget["FINALIZE_CAP_S"] == 300
    assert budget["EXPECTED_WALLTIME_S"] == 18000
    assert (
        "EXPECTED_FREEZE_TREES_SHA256="
        "6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415"
    ) in job
    assert "WORKLOADS=(write-heavy balanced read-heavy)" in submit
    assert (
        "for command_name in qstat qsub pegasusinfo check_quota sha256sum; do"
        in submit
    )
    assert "\ncheck_quota >/dev/null\n" in submit
    assert "\nquota -s >/dev/null\n" not in submit
    assert submit.count("job_id=$(qsub") == 1
    assert "B10_WORKLOAD=$workload" in submit
    assert "B10_SUBMISSION_NONCE=$SUBMISSION_NONCE" in submit
    assert "QUEUE_STATE=$(qstat -Q)" in submit
    assert "ENABLE(?:D)?" in submit and "ACT|ACTIVE" in submit
    assert '[[ "$HOSTNAME_SHORT" =~ ^bnode[0-9]+([.].*)?$ ]]' in job
    assert 'timeout 30 qstat -f "$QSTAT_JOBID"' in job
    assert (
        'export IZANAGI_RESERVATION_SCRIPT_SHA256="$COMMITTED_SCRIPT_SHA256"'
        in job
    )
    required_commands = job.split("for command_name in ", 1)[1].split("; do", 1)[0].split()
    required_commands = [name for name in required_commands if name != "\\"]
    assert "gnuplot" not in required_commands
    assert "gnuplot" not in job
    assert required_commands == [
        "git", "cmake", "cc", "c++", "make", "ar", "ranlib", "as", "ld",
        "numactl", "timeout", "qstat", "sha256sum", "hostname", "mkdir",
        "realpath", "tr", "date", "env",
    ]
    report_call = job.split(
        '"$REPO_ROOT/orchestrator/campaign/backoff_extended_sweep_report.py"', 1,
    )[1].split("CURRENT_STAGE=finalize", 1)[0]
    assert '"$WORKLOAD" --output-root "$OUTPUT_ROOT" --defer-plot' in report_call
    assert "gnuplot" not in report_call
    # Legacy sweep, extended analysis, and formal sweep each specify the cache.
    assert job.count('--cache-root "$B10_BUILD_CACHE_ROOT"') == 3
    assert job.count("http://10.120.96.1:8080") == 1
    assert "BUILD_NETWORK_PROXY_URL=http://10.120.96.1:8080" in job
    assert 'export http_proxy="$BUILD_NETWORK_PROXY_URL"' in job
    assert 'export https_proxy="$BUILD_NETWORK_PROXY_URL"' in job
    assert '"external_fetch_via_proxy": True' in job
    assert '"dependency_revisions": "sha-pinned"' in job


def test_b10_run_kind_routes_t2266_only_by_opt_in_and_binds_all_receipts():
    root = Path(__file__).resolve().parents[2]
    job_path = root / "tools/pegasus/b10_backoff_grid.sh"
    submit_path = root / "tools/pegasus/submit_b10_backoff_grid.sh"
    for path in (job_path, submit_path):
        subprocess.run(["bash", "-n", str(path)], check=True)
    job = job_path.read_text(encoding="utf-8")
    submit = submit_path.read_text(encoding="utf-8")

    assert "B10_RUN_KIND=extended" in submit
    assert "B10_RUN_KIND=${B10_RUN_KIND:-extended}" in job
    for script in (job, submit):
        assert "extended|t2266-tail" in script
    assert "--run-kind)" in submit
    assert "B10_RUN_KIND=$B10_RUN_KIND" in submit
    assert (
        'QSUB_ENV="B10_WORKLOAD=$workload,B10_OUTPUT_ROOT=$root,'
        'B10_SUBMISSION_NONCE=$SUBMISSION_NONCE,'
        'JOB_SCRIPT_SHA256=$JOB_SCRIPT_SHA256"'
    ) in submit
    assert 'QSUB_ENV="$QSUB_ENV,B10_RUN_KIND=$B10_RUN_KIND"' in submit
    assert 'SWEEP_COMMAND+=(--run-kind "$B10_RUN_KIND")' in job
    assert 'if [[ "$B10_RUN_KIND" == "t2266-tail" ]]; then' in job
    assert 'if [[ "$B10_RUN_KIND" == "extended" ]]; then' in job

    extended_only = job.split(
        'if [[ "$B10_RUN_KIND" == "extended" ]]; then', 1,
    )[1].split("\nfi", 1)[0]
    assert "backoff_overthrottle.py" in extended_only
    assert "backoff_extended_sweep_report.py" in extended_only
    t2266_argv = job.split(
        'SWEEP_COMMAND+=(--run-kind "$B10_RUN_KIND")', 1,
    )[0].rsplit('if [[ "$B10_RUN_KIND" == "t2266-tail" ]]; then', 1)[1]
    assert "backoff_overthrottle.py" not in t2266_argv
    assert "backoff_extended_sweep_report.py" not in t2266_argv

    assert 'run_kind = os.environ["B10_RUN_KIND"]' in submit
    assert submit.count('"run_kind": run_kind') == 3
    assert 'root, rc, stage, line, job, run_kind = sys.argv[1:]' in job
    assert 'repo_commit, ccbench_commit, run_kind = sys.argv[1:]' in job
    assert 'root, workload, job, freeze_hash, run_kind = sys.argv[1:]' in job
    assert job.count('"run_kind": run_kind') == 3
    assert 'if run_kind == "t2266-tail":' in job
    assert "len(commits) != 8" in job
    assert 'for suffix in (".dat", ".json")' in job


def test_b10_run_kind_routes_t2418_through_job_submit_and_finalizer():
    root = Path(__file__).resolve().parents[2]
    job_path = root / "tools/pegasus/b10_backoff_grid.sh"
    submit_path = root / "tools/pegasus/submit_b10_backoff_grid.sh"
    for path in (job_path, submit_path):
        subprocess.run(["bash", "-n", str(path)], check=True)
    job = job_path.read_text(encoding="utf-8")
    submit = submit_path.read_text(encoding="utf-8")

    assert "extended|t2266-tail|t2418-explore" in job
    assert "extended|t2266-tail|t2418-explore" in submit
    assert "CURRENT_STAGE=t2418_explore_sweep" in job
    assert (
        'if [[ "$B10_RUN_KIND" == "t2266-tail" \\\n'
        '    || "$B10_RUN_KIND" == "t2418-explore" ]]; then'
    ) in job
    assert (
        'if [[ "$B10_RUN_KIND" == "t2266-tail" \\\n'
        '      || "$B10_RUN_KIND" == "t2418-explore" ]]; then'
    ) in submit
    assert 'SWEEP_COMMAND+=(--run-kind "$B10_RUN_KIND")' in job
    assert 'QSUB_ENV="$QSUB_ENV,B10_RUN_KIND=$B10_RUN_KIND"' in submit

    finalizer = job.split('elif run_kind == "t2418-explore":', 1)[1]
    assert "len(commits) != 5" in finalizer
    assert "T-2418 requires five committed genomes" in finalizer
    assert "t2418-backoff-static-explore-{workload}" in finalizer
    assert 'for suffix in (".dat", ".json")' in finalizer
    assert "report.is_symlink()" in finalizer


def test_b10_job_builds_pinned_dependencies_in_job_scratch():
    root = Path(__file__).resolve().parents[2]
    job = (root / "tools/pegasus/b10_backoff_grid.sh").read_text(encoding="utf-8")
    policy = json.loads(
        (root / "tools/pegasus/policy.json").read_text(encoding="utf-8")
    )
    budget = _shell_integer_assignments(job, ("DEPENDENCY_BUILD_CAP_S",))

    for key in (
        "gflags_expected_head",
        "glog_expected_head",
    ):
        assert key in policy
        assert f'"{key}"' in job
    assert budget["DEPENDENCY_BUILD_CAP_S"] == (
        policy["silo_ladder_rung1"]["dependency_build_cap_s"]
    )
    assert 'CURRENT_STAGE=dependency_policy_contract' in job
    assert 'CURRENT_STAGE=dependency_build' in job
    assert '"$OUTPUT_ROOT" "$rc" "$CURRENT_STAGE" "$line"' in job
    assert 'dep_head=$(git -C "$dep_source" rev-parse --verify HEAD)' in job
    assert 'git -C "$dep_source" status --porcelain --untracked-files=all' in job
    assert '[[ "$dep_head" != "$dep_expected"' in job
    assert 'fail 2 "$dep source is not pinned-clean"' in job
    assert 'DEPENDENCY_DEADLINE=$((SECONDS + DEPENDENCY_BUILD_CAP_S))' in job
    assert 'GFLAGS_INSTALL="$TMPDIR/gflags-install"' in job
    assert 'GLOG_INSTALL="$TMPDIR/glog-install"' in job
    assert "-DREGISTER_INSTALL_PREFIX=OFF" in job
    assert "-DWITH_GTEST=OFF -DBUILD_TESTING=OFF" in job
    assert "-DWITH_UNWIND=OFF" in job
    assert '"-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL"' in job
    assert 'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL:$GLOG_INSTALL"' in job


def test_b10_job_creates_records_and_passes_a_detached_ccbench_worktree():
    root = Path(__file__).resolve().parents[2]
    job = (root / "tools/pegasus/b10_backoff_grid.sh").read_text(encoding="utf-8")
    assert (
        'git -C "$REPO_ROOT" ls-tree "$CURRENT_COMMIT" -- external/ccbench'
        in job
    )
    assert (
        'worktree_setup_run git -C "$CCBENCH_BASE" worktree add --detach \\\n'
        '  "$CCBENCH_WORKTREE" "$CCBENCH_EXPECTED_COMMIT"'
        in job
    )
    assert '"ccbench_gitlink_commit": ccbench_commit' in job
    assert '"expected_gitlink_commit": expected' in job
    assert '"observed_head_commit": observed' in job
    assert 'status --porcelain --untracked-files=no' in job
    # Legacy sweep, extended analysis, and formal sweep each specify the worktree.
    assert job.count('--ccbench-dir "$CCBENCH_WORKTREE"') == 3
    assert 'trap cleanup_worktree EXIT' in job
    assert 'CURRENT_STAGE=ccbench_worktree_cleanup\nremove_ccbench_worktree' in job


@pytest.mark.parametrize("job_rc", [0, 23], ids=["normal", "abnormal"])
def test_b10_job_exit_trap_removes_worktree_on_normal_and_abnormal_exit(
        tmp_path, job_rc):
    root = Path(__file__).resolve().parents[2]
    job = (root / "tools/pegasus/b10_backoff_grid.sh").read_text(encoding="utf-8")
    repository, expected, _other = _fixture_git_repository(tmp_path)
    worktree = tmp_path / "job-ccbench"
    output_root = tmp_path / "output"
    (output_root / "env").mkdir(parents=True)
    _add_detached_worktree(repository, worktree, expected)
    snippet = "\n".join((
        "set -Eeuo pipefail",
        "WORKTREE_CLEANUP_CAP_S=30",
        'CCBENCH_BASE="$1"',
        'CCBENCH_WORKTREE="$2"',
        'OUTPUT_ROOT="$3"',
        _shell_function(job, "remove_ccbench_worktree"),
        _shell_function(job, "cleanup_worktree"),
        "trap cleanup_worktree EXIT",
        'exit "$4"',
    ))
    completed = subprocess.run(
        [
            "bash", "-c", snippet, "b10-cleanup-test",
            str(repository), str(worktree), str(output_root), str(job_rc),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == job_rc, completed.stderr
    assert not worktree.exists()
    assert str(worktree) not in _git(repository, "worktree", "list", "--porcelain")
    assert (output_root / "env/worktree-remove.rc").read_text() == "0\n"


def test_b10_job_time_budget_matches_walltime():
    root = Path(__file__).resolve().parents[2]
    job = (root / "tools/pegasus/b10_backoff_grid.sh").read_text(encoding="utf-8")
    cap_names = (
        "WORKTREE_SETUP_CAP_S", "DEPENDENCY_BUILD_CAP_S", "SWEEP_CAP_S",
        "AA_CAP_S", "REPORT_CAP_S", "WORKTREE_CLEANUP_CAP_S",
        "FINALIZE_CAP_S",
    )
    budget = _shell_integer_assignments(
        job, (*cap_names, "EXPECTED_RESERVE_S", "EXPECTED_WALLTIME_S"),
    )
    cap_total = sum(budget[name] for name in cap_names)
    reserve = budget["EXPECTED_RESERVE_S"]
    walltime = budget["EXPECTED_WALLTIME_S"]

    assert cap_total + reserve == walltime
    assert reserve > 0
    formula = " + ".join(str(budget[name]) for name in cap_names)
    assert f"# {formula} = {cap_total} seconds." in job
    assert f"retains the preregistered {reserve}-second reserve." in job


def test_b10_job_script_identity_uses_three_sha256_values_not_path_equality():
    root = Path(__file__).resolve().parents[2]
    job = (root / "tools/pegasus/b10_backoff_grid.sh").read_text(encoding="utf-8")
    submit = (root / "tools/pegasus/submit_b10_backoff_grid.sh").read_text(
        encoding="utf-8",
    )
    assert '"$SCRIPT_PATH" == "$REPO_ROOT/tools/pegasus/b10_backoff_grid.sh"' not in job
    assert 'CURRENT_COMMIT=$(git -C "$REPO_ROOT" rev-parse --verify HEAD^{commit})' in job
    assert 'EXECUTING_SCRIPT_SHA256=$(sha256sum -- "$SCRIPT_PATH")' in job
    assert (
        'git -C "$REPO_ROOT" cat-file blob \\\n'
        '    "$CURRENT_COMMIT:tools/pegasus/b10_backoff_grid.sh" | sha256sum'
    ) in job
    assert (
        '[[ "$EXECUTING_SCRIPT_SHA256" == "$JOB_SCRIPT_SHA256" \\\n'
        '    && "$COMMITTED_SCRIPT_SHA256" == "$JOB_SCRIPT_SHA256" ]]'
    ) in job
    assert '[[ "$JOB_SCRIPT_SHA256" =~ ^[0-9a-f]{64}$ ]]' in job
    assert 'JOB_SCRIPT_SHA256=$JOB_SCRIPT_SHA256' in submit


def test_deferred_report_writes_plot_inputs_and_records_missing_png(
        tmp_path, monkeypatch):
    layout = SimpleNamespace(reports_dir=str(tmp_path), root=str(tmp_path / "campaign-id"))
    normal = [{
        "kind": "static", "backoff_us": 10, "median_tps": 123.0,
        "abort_rate": 0.25, "latency_ns": 456.0, "cv": 0.01,
    }]
    verdict = {
        **R.CLAIM_BOUNDARY,
        "status": "complete",
        "peak": None,
        "onset": None,
        "mechanism": {"trace_disabled_table": [], "add_analysis_table": []},
    }
    monkeypatch.setattr(
        R, "load_normal_points", lambda *_args: (normal, "available", layout),
    )
    monkeypatch.setattr(R, "load_aa_records", lambda *_args: [])
    monkeypatch.setattr(R, "evaluate_workload", lambda *_args, **_kwargs: verdict)

    def forbidden_renderer(*_args, **_kwargs):
        raise AssertionError("measurement job must not start the plot renderer")

    monkeypatch.setattr(R, "make_plot", forbidden_renderer)
    result = R.report_workload(
        "balanced", str(tmp_path), log=lambda *_args: None, render_plot=False,
    )

    stem = tmp_path / "b10-backoff-grid-balanced"
    recorded = json.loads(Path(result["verdict_path"]).read_text(encoding="utf-8"))
    assert Path(f"{stem}.dat").is_file()
    assert Path(f"{stem}.plt").is_file()
    assert not Path(f"{stem}.png").exists()
    assert recorded["plot_artifact"] == {
        "status": "deferred",
        "reason": "measurement_host_plotting_prohibited",
        "renderer": "gnuplot",
        "renderer_invoked": False,
        "dat": "b10-backoff-grid-balanced.dat",
        "script": "b10-backoff-grid-balanced.plt",
        "png": {
            "path": "b10-backoff-grid-balanced.png",
            "status": "not_generated_on_measurement_host",
        },
    }
    report = Path(result["report"]).read_text(encoding="utf-8")
    assert "Plot status: `deferred`." in report
    assert "PNG was not generated" in report
    assert "![balanced]" not in report


@pytest.mark.parametrize(
    ("extra_args", "expected_render"),
    [([], True), (["--defer-plot"], False)],
)
def test_report_cli_preserves_default_render_and_allows_measurement_deferral(
        monkeypatch, extra_args, expected_render):
    observed = []

    def report(tag, output_root, *, render_plot=True):
        observed.append((tag, output_root, render_plot))
        return {"verdict": {"status": "complete"}}

    monkeypatch.setattr(R, "report_workload", report)
    assert R.main(["balanced", "--output-root", "/outside/root", *extra_args]) == 0
    assert observed == [("balanced", "/outside/root", expected_render)]


def test_failure_and_submission_receipts_cover_partial_progress():
    root = Path(__file__).resolve().parents[2]
    job = (root / "tools/pegasus/b10_backoff_grid.sh").read_text(encoding="utf-8")
    submit = (root / "tools/pegasus/submit_b10_backoff_grid.sh").read_text(encoding="utf-8")
    assert 'base.glob("campaigns/*/runs/wal.jsonl")' in job
    assert '"last_committed": committed' in job
    assert 'base.glob("campaigns/*/reports/b10-backoff-overthrottle-*.jsonl")' in job
    assert 'base.glob("campaigns/*/reports/*")' in job
    assert 'fail 2 "freeze trees changed during the job"' in job
    append = submit.index("append_submission_event submitted")
    display = submit.index("printf '%s\\n' \"$job_id\"")
    assert append < display
    assert "append_submission_event failed" in submit


def test_b10_freeze_tree_bytes_match_the_wave_local_gate():
    root = Path(__file__).resolve().parents[2]
    digest = hashlib.sha256()
    paths = [
        path
        for relative in ("output/s1-freeze", "output/s8b-freeze")
        for path in (root / relative).rglob("*")
        if path.is_file()
    ]
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    assert digest.hexdigest() == (
        "6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415"
    )


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    sys.exit(_run())
