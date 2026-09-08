from __future__ import annotations

import copy
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.campaign import backoff_counterfactual_analysis as cohort1
from orchestrator.campaign import backoff_counterfactual_cohort2_analysis as analysis
from tools.pegasus.probes import t2187_adaptive_const_probe as producer


ROOT = Path(__file__).resolve().parents[2]
PREREGISTRATION = ROOT / "docs" / "backoff-counterfactual-cohort2-preregistration.md"
PREREGISTRATION_SHA256 = (
    "8b4127f4be895da0d25da88b0837f679ecf06d43ab656b16d2944146b9f7a9e9"
)
SEEDS = sorted(analysis.PREREGISTERED_SEEDS)
DEFAULT_SEED = 11_400_714_819_323_198_485


def _build_bindings() -> dict:
    return {
        "ccbench_head": analysis.CCBENCH_PIN,
        "patch_sha256": analysis.PATCH_A_SHA256,
        "dynamic_patch_sha256": analysis.PATCH_B_SHA256,
        "counterfactual_patch_sha256": analysis.PATCH_C_SHA256,
        "patch_stack": [
            {"path": path, "sha256": digest}
            for path, digest in analysis.PATCH_STACK
        ],
        "patch_stack_sha256": analysis.PATCH_STACK_SHA256,
    }


def _lcg_bits(seed: int, count: int) -> list[int]:
    state = seed
    bits = []
    for _ in range(count):
        state = (
            state * 6_364_136_223_846_793_005
            + 1_442_695_040_888_963_407
        ) % (2**64)
        bits.append((state >> 63) & 1)
    return bits


def _events(
    effect: float,
    *,
    seed: int,
    policy: int,
    normal_count: int = 24,
) -> list[dict]:
    assignments = (
        _lcg_bits(seed, normal_count)
        if policy == 2
        else [policy] * normal_count
    )
    commits = [10**12]
    for assigned in assignments:
        delta = effect / 2 if assigned == 0 else -effect / 2
        commits.append(round(commits[-1] * math.exp(delta)))
    events = [
        {
            "seq": index,
            "tsc": 1000 + index,
            "window_us": 1,
            "window_commits": commits[index],
            "trigger": "count",
            "assigned_invert": assigned,
            "recommended_delta_sign": (-1, 0, 1)[index % 3],
            "both_actions_feasible": (index // 2) % 2,
            "inversion_realized": 0,
            "terminal_flush": 0,
            "backoff_before": 0,
            "backoff_after": 0,
        }
        for index, assigned in enumerate(assignments)
    ]
    events.append(
        {
            "seq": normal_count,
            "tsc": 1000 + normal_count,
            "window_us": 1,
            "window_commits": commits[-1],
            "trigger": "terminal",
            "assigned_invert": -1,
            "recommended_delta_sign": 0,
            "both_actions_feasible": 0,
            "inversion_realized": 0,
            "terminal_flush": 1,
            "backoff_before": 0,
            "backoff_after": 0,
        }
    )
    return events


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
        "BACKOFF_COUNT_CAP_US": 9223372036854775807,
        "BACKOFF_STEP_ADAPT": 1,
        "BACKOFF_STEP_MIN_MILLI": 1000,
        "BACKOFF_STEP_MAX_MILLI": 4000,
        "BACKOFF_DYN_CEILING": 1,
        "BACKOFF_TRACE": 1,
        "BACKOFF_TRACE_TERMINAL_US": 5000000,
        "BACKOFF_STEP_POLICY": policy,
        "BACKOFF_STEP_POLICY_SEED": seed,
    }
    return "silo|" + ",".join(
        f"{name}={value}" for name, value in sorted(flags.items())
    )


def _row(
    policy: int,
    workload: str,
    threads: int,
    seed: int,
    effect: float,
) -> dict:
    build_seed = seed if policy == 2 else DEFAULT_SEED
    events = _events(effect, seed=build_seed, policy=policy)
    row = {
        **analysis._expected_cell_identity(policy),
        "workload": workload,
        "workload_flags": copy.deepcopy(analysis.WORKLOAD_FLAGS[workload]),
        "threads": threads,
        "rep_index": 0,
        "backoff_trace": True,
        "throughput_scope": "diagnostic_only",
        "counterfactual_preregistration": PREREGISTRATION_SHA256,
        **_build_bindings(),
        "binary_sha256": hashlib.sha256(
            f"policy-{policy}-seed-{build_seed}".encode()
        ).hexdigest(),
        "genome": _genome(policy, build_seed),
        "trace_events": events,
        "trace_summary": {
            "updates": len(events) - 1,
            "retained": len(events) - 1,
            "dropped": 0,
            "flushes": 1,
        },
        "backoff_trace_symbol_count": 1,
        "backoff_trace_string_count": 1,
    }
    if policy == 2:
        row["step_policy_seed"] = seed
    return row


def _document(seed: int, effect: float = 0.006) -> dict:
    rows = [
        _row(policy, workload, threads, seed, effect)
        for policy in range(3)
        for workload in analysis.WORKLOADS
        for threads in analysis.THREADS
    ]
    return {
        "schema_version": analysis.TRACE_SCHEMA_VERSION,
        "kind": "diagnostic-backoff-trace",
        "headline_eligible": False,
        "throughput_scope": "diagnostic_only",
        "grid_spec": analysis.COUNTERFACTUAL_CELLS,
        "cell_order": list(analysis.CELL_LABELS),
        "rep_index": 0,
        "records": 1_000_000,
        "extime_s": 6,
        "reps_per_job": 1,
        "counterfactual_preregistration": PREREGISTRATION_SHA256,
        **_build_bindings(),
        "step_policy_seed": seed,
        "trace_runs": rows,
    }


def _write_artifacts(directory: Path) -> list[Path]:
    directory.mkdir()
    paths = []
    for slot, seed in enumerate(SEEDS):
        path = directory / f"slot-{slot:02d}.json"
        path.write_text(
            json.dumps(_document(seed, 0.005 + slot * 0.0002), sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        paths.append(path)
    return paths


def _rewrite(path: Path, mutate) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    mutate(document)
    path.write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")


def _primary_row(document: dict) -> dict:
    return next(
        row
        for row in document["trace_runs"]
        if row["step_policy"] == 2
        and row["workload"] == "write-heavy"
        and row["threads"] == 48
    )


def _producer_stdout(events: list[dict]) -> str:
    records = [
        " ".join(
            (
                "IZANAGI_BACKOFF_TRACE v=3",
                f"seq={event['seq']}",
                f"tsc={event['tsc']}",
                f"window_us={event['window_us']}",
                f"window_commits={event['window_commits']}",
                "trigger=1",
                f"backoff_before={event['backoff_before']}",
                f"backoff_after={event['backoff_after']}",
                "gradient_sign=0",
                "step_us=1",
                "ceiling_us=1000",
                "ceiling_changed=0",
                "parity_branch=-1",
                f"recommended_delta_sign={event['recommended_delta_sign']}",
                f"assigned_invert={event['assigned_invert']}",
                f"inversion_realized={event['inversion_realized']}",
                f"both_actions_feasible={event['both_actions_feasible']}",
                "terminal_flush=0",
            )
        )
        for event in events
    ]
    count = len(records)
    records.append(
        "IZANAGI_BACKOFF_TRACE_SUMMARY v=3 "
        f"updates={count} retained={count} dropped=0 flushes=0"
    )
    return "\n".join(records) + "\n"


def test_assignment_lcg_accepts_exact_positive_sequence_and_rejects_one_bit_flip(
    tmp_path: Path,
) -> None:
    seed = 5_744_733_223_455_690_259
    assert _lcg_bits(seed, 4) == [0, 1, 0, 1]
    events = [
        {"terminal_flush": 0, "assigned_invert": assigned, "inversion_realized": 0}
        for assigned in (0, 1, 0, 1)
    ] + [{"terminal_flush": 1, "assigned_invert": -1}]
    analysis._validate_assignment_lcg(events, seed=seed, binding="positive")

    changed = copy.deepcopy(events)
    changed[0]["assigned_invert"] = 1
    assert changed[0]["inversion_realized"] == 0
    with pytest.raises(ValueError, match="assignment-integrity check"):
        analysis._validate_assignment_lcg(changed, seed=seed, binding="one-bit")

    class ExplodingSeed:
        def __mul__(self, _other):
            raise AssertionError("terminal must not consume the LCG")

    analysis._validate_assignment_lcg(
        [{"terminal_flush": 1, "assigned_invert": -1}],
        seed=ExplodingSeed(),
        binding="terminal-only",
    )

    document = _document(SEEDS[0])
    path = tmp_path / "positive.json"
    path.write_text(json.dumps(document) + "\n", encoding="utf-8")
    analysis._load_artifact(path)
    event = _primary_row(document)["trace_events"][0]
    assert event["inversion_realized"] == 0
    event["assigned_invert"] = 1 - event["assigned_invert"]
    path.write_text(json.dumps(document) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="assignment-integrity check"):
        analysis._load_artifact(path)


def test_seq_zero_is_excluded_before_pairing_under_cohort2() -> None:
    values = [80, 100, 120, 90, 180, 360]
    assignments = [1, 0, 1, 0, 1]
    events = [
        {
            "seq": index,
            "window_us": 1,
            "window_commits": value,
            "assigned_invert": assignments[index],
            "terminal_flush": 0,
        }
        for index, value in enumerate(values[:-1])
    ]
    events.append(
        {
            "seq": 5,
            "window_us": 1,
            "window_commits": values[-1],
            "assigned_invert": -1,
            "terminal_flush": 1,
        }
    )
    calls = []

    def membership(event: dict, index: int, count: int) -> bool:
        calls.append((event["seq"], index, count))
        return True

    result = analysis._run_difference({"events": events}, membership)
    expected = statistics.fmean((math.log(120 / 100), math.log(180 / 90)))
    expected -= statistics.fmean((math.log(90 / 120), math.log(360 / 180)))
    assert calls == [(1, 0, 4), (2, 1, 4), (3, 2, 4), (4, 3, 4)]
    assert result["estimate_log"] == pytest.approx(expected)

    changed = copy.deepcopy(events)
    changed[0]["window_commits"] = 0
    changed[0]["assigned_invert"] = 0
    assert analysis._run_difference(
        {"events": changed}, lambda _event, _index, _count: True
    )["estimate_log"] == pytest.approx(expected)


def test_terminal_flush_is_following_only_and_does_not_consume_lcg() -> None:
    seed = 5_744_733_223_455_690_259
    events = _events(0.01, seed=seed, policy=2, normal_count=4)
    analysis._validate_assignment_lcg(events, seed=seed, binding="terminal")
    calls = []
    result = analysis._run_difference(
        {"events": events},
        lambda event, index, count: calls.append(
            (event["seq"], index, count)
        ) or True,
    )
    assert calls == [(1, 0, 3), (2, 1, 3), (3, 2, 3)]
    assert all(seq != events[-1]["seq"] for seq, _index, _count in calls)
    assert result["assigned_forward"] + result["assigned_invert"] == 3

    summary = analysis._cluster_summary(
        [{
            "cell_literal": analysis.CELL_LITERALS[2],
            "step_policy_seed": seed,
            "binary_sha256": "a" * 64,
            "events": events,
        }],
        lambda _event, _index, _count: True,
        confirmatory=False,
    )
    assert summary["assignment_rate_all_events"][0][
        "assignment_rate_all_events"
    ] == pytest.approx(0.5)


def test_terminal_zero_commit_makes_whole_primary_inconclusive(tmp_path: Path) -> None:
    zero_events = _events(0.006, seed=SEEDS[0], policy=2)
    zero_events[-1]["window_commits"] = 0
    membership_calls = []
    direct = analysis._run_difference(
        {"events": zero_events},
        lambda event, index, count: membership_calls.append(
            (event, index, count)
        ) or True,
    )
    assert direct["reason"] == "window_commits_zero"
    assert membership_calls == []

    paths = _write_artifacts(tmp_path / "artifacts")
    _rewrite(
        paths[0],
        lambda document: _primary_row(document)["trace_events"][-1].__setitem__(
            "window_commits", 0
        ),
    )
    primary = analysis.analyze_counterfactual(paths, PREREGISTRATION)["primary"]
    assert primary["decision"] == "inconclusive"
    assert primary["theta_log"] is None
    assert "window_commits_zero" in primary["reasons"]
    assert len(primary["run_estimates"]) == 12


def test_missing_terminal_makes_whole_primary_inconclusive_without_replacement(
    tmp_path: Path,
) -> None:
    paths = _write_artifacts(tmp_path / "artifacts")
    document = json.loads(paths[0].read_text())
    missing_seed = document["step_policy_seed"]
    row = _primary_row(document)
    stdout = _producer_stdout(row["trace_events"][:-1])
    events, summary, _directional = producer._parse_backoff_trace(stdout)
    assert all(event["terminal_flush"] == 0 for event in events)
    assert summary == {
        "updates": len(events),
        "retained": len(events),
        "dropped": 0,
        "flushes": 0,
    }

    row["trace_events"] = events
    row["trace_summary"] = summary
    paths[0].write_text(json.dumps(document) + "\n", encoding="utf-8")
    primary = analysis.analyze_counterfactual(paths, PREREGISTRATION)["primary"]
    assert primary["decision"] == "inconclusive"
    assert "terminal_not_closed" in primary["reasons"]
    assert len(primary["run_estimates"]) == 12
    assert any(
        row["run_identity"][1] == missing_seed
        and row["reason"] == "terminal_not_closed"
        for row in primary["run_estimates"]
    )


def test_nonterminal_events_require_count_trigger_and_count_window() -> None:
    row = _row(2, "write-heavy", 48, SEEDS[0], 0.006)
    changed_trigger = copy.deepcopy(row)
    changed_trigger["trace_events"][1]["trigger"] = "time"
    with pytest.raises(ValueError, match="normal event trigger must be count"):
        analysis._validate_trace(changed_trigger, binding="trigger")

    changed_window = copy.deepcopy(row)
    changed_window["trace_events"][1]["window_commits"] = 9_999
    with pytest.raises(ValueError, match="at least 10000 commits"):
        analysis._validate_trace(changed_window, binding="count-window")


def test_terminal_requires_one_position_at_the_end_when_present() -> None:
    row = _row(2, "write-heavy", 48, SEEDS[0], 0.006)
    middle = copy.deepcopy(row)
    terminal = middle["trace_events"].pop()
    middle["trace_events"].insert(2, terminal)
    for index, event in enumerate(middle["trace_events"]):
        event["seq"] = index
        event["tsc"] = 1000 + index
    with pytest.raises(ValueError, match="terminal event must be last"):
        analysis._validate_trace(middle, binding="middle")

    doubled = copy.deepcopy(row)
    duplicate = copy.deepcopy(doubled["trace_events"][-1])
    duplicate["seq"] = len(doubled["trace_events"])
    duplicate["tsc"] += 1
    doubled["trace_events"].append(duplicate)
    with pytest.raises(ValueError, match="at most one terminal"):
        analysis._validate_trace(doubled, binding="double")


@pytest.mark.parametrize(
    "mutation",
    ("cell", "extime", "patch-c", "top-prereg", "row-prereg"),
)
def test_exact_cohort2_cells_extime_patch_and_preregistration_are_bound(
    tmp_path: Path,
    mutation: str,
) -> None:
    document = _document(SEEDS[0])
    if mutation == "cell":
        _primary_row(document)["count_cap_us"] -= 1
    elif mutation == "extime":
        document["extime_s"] = 5
    elif mutation == "patch-c":
        document["counterfactual_patch_sha256"] = "0" * 64
    elif mutation == "top-prereg":
        document["counterfactual_preregistration"] = "0" * 64
    else:
        _primary_row(document)["counterfactual_preregistration"] = "0" * 64
    path = tmp_path / f"near-miss-{mutation}.json"
    path.write_text(json.dumps(document) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        analysis._load_artifact(path)


@pytest.mark.parametrize(
    ("binding", "mutation"),
    (
        ("top", "missing"),
        ("top", "one-character-drift"),
        ("row", "missing"),
        ("row", "one-character-drift"),
    ),
)
def test_patch_stack_sha256_is_exact_at_top_and_row_bindings(
    tmp_path: Path,
    binding: str,
    mutation: str,
) -> None:
    document = _document(SEEDS[0])
    target = document if binding == "top" else _primary_row(document)
    if mutation == "missing":
        target.pop("patch_stack_sha256")
    else:
        observed = target["patch_stack_sha256"]
        target["patch_stack_sha256"] = (
            ("0" if observed[0] != "0" else "1") + observed[1:]
        )
    path = tmp_path / f"bad-stack-sha-{binding}-{mutation}.json"
    path.write_text(json.dumps(document) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="ordered patch stack mismatch"):
        analysis._load_artifact(path)


def test_cohort2_literal_pins_are_independent_of_fixture_helpers() -> None:
    expected_cells = {
        0: "cw-as-dyn-c2-p0:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:0",
        1: "cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1",
        2: "cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2",
    }
    expected_patch = (
        "4c04caa89244d74aa542a204bed0befae45b13616113cc5d734570c3aae7d2ff"
    )
    expected_stack = (
        "14ac8f00798d1b317854643e133c0b58543106e9c693f5c556f8b13edb591082"
    )
    assert analysis.TRACE_SCHEMA_VERSION == "izanagi-dynamic-backoff-trace/v4"
    assert analysis.CELL_LITERALS == expected_cells
    assert analysis.COUNTERFACTUAL_CELLS == ",".join(expected_cells.values())
    assert analysis.MEASUREMENT_PREREGISTRATION_SHA256 == PREREGISTRATION_SHA256
    assert analysis.ANALYSIS_PREREGISTRATION_SHA256 == PREREGISTRATION_SHA256
    assert analysis.PATCH_C_SHA256 == expected_patch
    assert analysis.PATCH_STACK_SHA256 == expected_stack
    assert hashlib.sha256(
        (ROOT / "patches" / "cicada-adaptive-counterfactual.patch").read_bytes()
    ).hexdigest() == expected_patch
    stack_text = "izanagi-patch-stack/v1\n" + "".join(
        f"{path} {hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}\n"
        for path, _digest in analysis.PATCH_STACK
    )
    assert hashlib.sha256(stack_text.encode("utf-8")).hexdigest() == expected_stack


def test_final_normal_assignment_changes_estimate_through_terminal_following_window() -> None:
    seed = 5_744_733_223_455_690_259
    events = _events(0.01, seed=seed, policy=2, normal_count=8)
    events[-1]["window_commits"] *= 4
    included = analysis._run_difference(
        {"events": events}, lambda _event, _index, _count: True
    )
    final_seq = events[-2]["seq"]
    without_final_pair = analysis._run_difference(
        {"events": events},
        lambda event, _index, _count: event["seq"] != final_seq,
    )
    assert included["estimate_log"] != pytest.approx(
        without_final_pair["estimate_log"]
    )


def test_tost_and_practical_superiority_constants_match_v2() -> None:
    assert analysis.EQUIVALENCE_MARGIN == cohort1.EQUIVALENCE_MARGIN == math.log(1.03)
    assert analysis.T90_DF11 == cohort1.T90_DF11 == 1.7958848
    assert analysis.T95_DF11 == cohort1.T95_DF11 == 2.2009852
    margin = analysis.EQUIVALENCE_MARGIN
    assert analysis._primary_decision(
        {"lower_log": -margin, "upper_log": margin - 1e-12},
        {"lower_log": -1, "upper_log": 1},
    )["decision"] == "inconclusive"
    assert analysis._primary_decision(
        {"lower_log": -1, "upper_log": 1},
        {"lower_log": margin + 1e-12, "upper_log": margin + 0.01},
    )["decision"] == "recommended_direction_superior"


def test_public_cohort2_analysis_uses_exact_twelve_equal_clusters(
    tmp_path: Path,
) -> None:
    paths = _write_artifacts(tmp_path / "artifacts")
    result = analysis.analyze_counterfactual(paths, PREREGISTRATION)
    estimates = [row["estimate_log"] for row in result["primary"]["run_estimates"]]
    assert result["analysis_version"] == (
        "izanagi-backoff-counterfactual-cohort2-analysis/v1"
    )
    assert result["primary"]["cluster_count"] == 12
    assert result["primary"]["theta_log"] == pytest.approx(
        statistics.fmean(estimates)
    )
    assert result["preregistration"]["sha256"] == PREREGISTRATION_SHA256
    assert set(SEEDS) == {
        14481721328008317845,
        7453732891837486670,
        766609016836229506,
        14479507243158715447,
        3736279228254271919,
        6574519577559702715,
        15525319108568766040,
        13039315294558381935,
        16889140200793892447,
        15536816158447092057,
        13171317188614694465,
        3421410286381859835,
    }


def test_analysis_preregistration_file_is_bound_to_literal_cohort2_sha(
    tmp_path: Path,
) -> None:
    paths = _write_artifacts(tmp_path / "artifacts")
    assert hashlib.sha256(PREREGISTRATION.read_bytes()).hexdigest() == (
        PREREGISTRATION_SHA256
    )
    changed = tmp_path / "changed-preregistration.md"
    changed.write_bytes(PREREGISTRATION.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="frozen specification"):
        analysis.analyze_counterfactual(paths, changed)


def _run() -> int:
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
