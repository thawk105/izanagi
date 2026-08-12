from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest

from orchestrator.preregistration import stress_check_simulation as sim
from tools.pegasus import run_t139_a12_stress_check as cli


REPO_ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_D264_NAMES = (
    "resolve_effective_preregistration",
    "PreregBinding",
    "submit_pilot",
    "verify_receipt",
)


def _synthetic_results(B: int, overrides: dict[tuple[int, str, str], dict] | None = None):
    overrides = overrides or {}
    results = []
    for J, workload, component in sim._cell_keys():
        item = {
            "J": J,
            "workload": workload,
            "component": component,
            "x": 0,
            "completed_datasets": B,
            "accepted_draws": 6 * J * B,
            "stream_sha256": {"value": "0" * 64, "description": "test"},
        }
        item.update(overrides.get((J, workload, component), {}))
        results.append(item)
    return results


def _copy_fixed_input(root: Path, raw: bytes) -> None:
    target = root / sim.INPUT_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)


def test_seed_derivation_and_fixed_input_digest():
    assert hashlib.sha256(sim.SEED_DERIVATION_PREIMAGE.encode("ascii")).hexdigest() == sim.SEED
    raw = (REPO_ROOT / sim.INPUT_RELATIVE_PATH).read_bytes()
    assert len(raw) == 587
    assert len(raw.splitlines()) == 31
    assert hashlib.sha256(raw).hexdigest() == sim.INPUT_SHA256


def test_aggregate_rejects_point_estimate_at_alpha():
    key = sim._cell_keys()[0]
    results = _synthetic_results(1_000_000, {key: {"x": 25_000}})
    verdict, cells, _ = sim._aggregate_cells(results, 1_000_000)
    target = next(cell for cell in cells if (cell["J"], cell["workload"], cell["component"]) == key)
    assert 25_000 / 1_000_000 == sim.ALPHA_1
    assert target["U"] > sim.ALPHA_1
    assert verdict == "design_not_feasible"


def test_aggregate_boundary_U_equal_alpha_passes():
    verdict, cells, _ = sim._aggregate_cells(
        _synthetic_results(7),
        7,
        upper_bound_fn=lambda _x, _B: sim.ALPHA_1,
    )
    assert verdict == "pass"
    assert all(cell["cell_pass"] for cell in cells)


def test_aggregate_ignores_worker_U_and_cell_pass():
    key = sim._cell_keys()[0]
    results = _synthetic_results(
        1_000_000,
        {key: {"x": 25_000, "U": 0.020, "cell_pass": True}},
    )
    verdict, cells, _ = sim._aggregate_cells(results, 1_000_000)
    target = next(cell for cell in cells if (cell["J"], cell["workload"], cell["component"]) == key)
    assert target["U"] > sim.ALPHA_1
    assert target["cell_pass"] is False
    assert verdict == "design_not_feasible"


def test_clopper_pearson_zero_golden_uses_familywise_delta():
    actual = sim._clopper_pearson_upper(0, 1_000_000)
    assert actual == pytest.approx(0.0000110020393183, rel=0.0, abs=5e-17)


def test_positive_sample_mean_fixed_draw_golden_is_not_recentered():
    draws = np.asarray([[10.0, 10.0, 10.0, 11.0]])
    flags, means, variances = sim._false_pass_from_cluster_sums(
        draws, sim._q_value(4)
    )
    assert means.tolist() == [10.25]
    assert variances.tolist() == pytest.approx([0.25])
    assert flags.tolist() == [True]


def test_zero_variance_positive_mean_is_false_pass():
    flags, means, variances = sim._false_pass_from_cluster_sums(
        np.asarray([[7, 7, 7, 7]], dtype=np.int64), sim._q_value(4)
    )
    assert means.tolist() == [7.0]
    assert variances.tolist() == [0.0]
    assert flags.tolist() == [True]


def test_aggregate_processes_all_cells_after_first_exceedance():
    calls = []

    def upper(x: int, B: int) -> float:
        calls.append((x, B))
        return 0.03 if len(calls) == 1 else 0.0

    verdict, cells, _ = sim._aggregate_cells(
        _synthetic_results(11), 11, upper_bound_fn=upper
    )
    assert verdict == "design_not_feasible"
    assert len(calls) == 60
    assert len(cells) == 60


def test_prng_fixed_bytes_and_accepted_indices_golden():
    raw = sim._prng_bytes(4, "W1", "N", 256)
    assert raw[:64].hex() == (
        "73fef50f6b034d7dcc3edc70df3ea3310a7f7bace574b9e81a6c463c547d8800"
        "34e4b042799ab3c3c35a976e83a3a020033bf644f5b63d61bfc670986e8c61de"
    )
    assert raw[211:228].hex() == "6be83486093a3f5affe345e376856e0f7b"
    assert raw[219] == 255
    accepted = sim._accept_raw_bytes(sim._prng_bytes(4, "W1", "N", 640))
    assert accepted[:40].tolist() == [
        0, 4, 0, 0, 2, 3, 2, 0, 4, 2, 0, 2, 3, 2, 3, 4, 0, 2, 3, 2,
        4, 1, 0, 2, 1, 3, 0, 0, 4, 0, 1, 0, 2, 3, 1, 1, 1, 4, 4, 0,
    ]
    assert hashlib.sha256(accepted[:512].tobytes()).hexdigest() == (
        "e53e3e0a46bc9875dec544a6c9dca7573c433055f9d365ea747e7eda268dcd55"
    )


def test_index_stream_accepted_indices_sha256_golden():
    stream = sim._IndexStream(4, "W1", "N")
    accepted = stream.take(512)
    assert hashlib.sha256(accepted.tobytes()).hexdigest() == (
        "e53e3e0a46bc9875dec544a6c9dca7573c433055f9d365ea747e7eda268dcd55"
    )
    assert stream.accepted_sha256 == (
        "e53e3e0a46bc9875dec544a6c9dca7573c433055f9d365ea747e7eda268dcd55"
    )


def test_rejection_discards_only_byte_255():
    raw = bytes(range(256))
    accepted = sim._accept_raw_bytes(raw)
    assert len(accepted) == 255
    assert np.bincount(accepted, minlength=5).tolist() == [51, 51, 51, 51, 51]


def test_chunk_size_preserves_indices_x_and_stream_hash():
    first = sim._IndexStream(4, "W1", "N")
    sequence_a = np.concatenate([first.take(37), first.take(475)])
    second = sim._IndexStream(4, "W1", "N")
    sequence_b = second.take(512)
    assert sequence_a.tolist() == sequence_b.tolist()
    assert first.accepted_sha256 == second.accepted_sha256
    support, _ = sim._load_support(REPO_ROOT)
    cell_a = sim._simulate_cell(support["W1"]["N"], 4, "W1", "N", 23, 1, sim._q_value(4))
    cell_b = sim._simulate_cell(support["W1"]["N"], 4, "W1", "N", 23, 11, sim._q_value(4))
    assert cell_a["x"] == cell_b["x"]
    assert cell_a["stream_sha256"] == cell_b["stream_sha256"]


@pytest.mark.parametrize("failure", ["modified", "missing", "wrong_digest"])
def test_input_failures_are_precondition_DNF(tmp_path, monkeypatch, failure):
    root = tmp_path / "root"
    if failure != "missing":
        raw = (REPO_ROOT / sim.INPUT_RELATIVE_PATH).read_bytes()
        if failure == "modified":
            raw = bytes([raw[0] ^ 1]) + raw[1:]
        _copy_fixed_input(root, raw)
    if failure == "wrong_digest":
        monkeypatch.setattr(sim, "INPUT_SHA256", "0" * 64)
    result = sim.run_smoke(
        repo_root=root,
        output_path=tmp_path / f"{failure}.json",
        repetitions=2,
        workers=1,
        chunk_datasets=1,
    )
    assert result.verdict == "design_not_feasible"
    assert result.run_status == "precondition_failed"
    assert result.transcript["completed_cell_count"] == 0
    assert result.transcript["cells"] == []


def test_ddof_zero_reverses_the_fixed_decision():
    values = np.asarray([[4.8, 4.8, 6.8, 6.8]])
    q = sim._q_value(4)
    unbiased, _, sample_variance = sim._false_pass_from_cluster_sums(values, q, ddof=1)
    population, _, population_variance = sim._false_pass_from_cluster_sums(values, q, ddof=0)
    assert sample_variance.tolist() == pytest.approx([4.0 / 3.0])
    assert population_variance.tolist() == [1.0]
    assert unbiased.tolist() == [False]
    assert population.tolist() == [True]


def test_production_cell_fixed_x_guards_ddof_recentering_and_pd_filter():
    result = sim._simulate_cell(
        np.asarray([11, 7, 11, -6, -23], dtype=np.int64),
        4,
        "W1",
        "N",
        128,
        17,
        sim._q_value(4),
    )
    assert result["x"] == 1


@pytest.mark.parametrize("J", sim.J_VALUES)
def test_q_nine_digit_ceiling_adjacent_grid(J):
    details = sim._q_details(J)
    assert sim._q_tail(J, details["q"]) <= sim.ALPHA_1
    assert sim._q_tail(J, details["q"] - 1e-9) > sim.ALPHA_1
    assert details["q"] == details["q_nano"] / 1_000_000_000
    assert details["root_relative_bracket_width"] <= 1e-13
    low, high = details["unrounded_root_bracket"]
    assert sim._q_tail(J, low) > sim.ALPHA_1
    assert sim._q_tail(J, high) <= sim.ALPHA_1
    assert details["beta_iterations_max"] < sim.BETA_CF_MAX_ITERATIONS
    if J == 4:
        assert details["q"] == 10.999552322
    if J == 13:
        assert details["q"] == 3.449997402


def test_support_is_five_points_per_workload_and_exactly_centered():
    support, metadata = sim._load_support(REPO_ROOT)
    assert metadata["data_row_count"] == 30
    assert set(support) == {"W1", "W2"}
    for workload in sim.WORKLOADS:
        assert set(support[workload]) == {"N", "H", "G"}
        for values in support[workload].values():
            assert values.shape == (5,)
            assert values.dtype == np.int64
            assert int(values.sum()) == 0
    assert support["W1"]["N"].tolist() == [197285, -11465, 40085, -132715, -93190]
    assert support["W2"]["N"].tolist() == [1149415, -471810, -951085, -104035, 377515]


def test_cells_are_exact_cartesian_product_and_malformed_sets_reject():
    keys = sim._cell_keys()
    expected = {
        (J, workload, component)
        for J in range(4, 14)
        for workload in ("W1", "W2")
        for component in ("N", "H", "G")
    }
    assert len(keys) == 60
    assert len(set(keys)) == 60
    assert set(keys) == expected
    valid = _synthetic_results(3)
    with pytest.raises(ValueError, match="Cartesian"):
        sim._aggregate_cells(valid[:-1], 3)
    duplicate = valid + [dict(valid[0])]
    with pytest.raises(ValueError, match="duplicate"):
        sim._aggregate_cells(duplicate, 3)
    wrong = [dict(item) for item in valid]
    wrong[0]["J"] = 2
    with pytest.raises(ValueError, match="Cartesian"):
        sim._aggregate_cells(wrong, 3)


def test_smoke_reads_input_processes_60_cells_and_never_emits_pass(tmp_path):
    result = sim.run_smoke(
        repo_root=REPO_ROOT,
        output_path=tmp_path / "smoke.json",
        repetitions=3,
        workers=1,
        chunk_datasets=1,
    )
    assert result.run_status == "completed"
    assert result.authoritative is False
    assert result.verdict is None
    assert result.transcript["verdict"] is None
    assert result.transcript["input"]["sha256"] == sim.INPUT_SHA256
    assert result.transcript["completed_cell_count"] == 60
    assert result.transcript["exact_cartesian_product"] is True
    assert all(cell["completed_datasets"] == 3 for cell in result.transcript["cells"])
    assert all(cell["accepted_draws"] == 18 * cell["J"] for cell in result.transcript["cells"])
    assert all(cell["final_counter"] > 0 or cell["final_byte_offset"] > 0 for cell in result.transcript["cells"])
    assert all(cell["stream_sha256"]["value"] != hashlib.sha256(b"").hexdigest() for cell in result.transcript["cells"])


@pytest.mark.parametrize(
    ("failure", "reason_prefix"),
    [
        ("worker", "worker_failure:RuntimeError"),
        ("numeric", "numerical_nonconvergence:ArithmeticError"),
        ("aggregate", "aggregation_inconsistency:ValueError"),
    ],
)
def test_simulation_failures_are_structured_DNF(
    tmp_path, monkeypatch, failure, reason_prefix
):
    root = tmp_path / "root"
    _copy_fixed_input(root, (REPO_ROOT / sim.INPUT_RELATIVE_PATH).read_bytes())

    if failure == "worker":
        def fail_worker(_arguments):
            raise RuntimeError("injected worker failure")

        monkeypatch.setattr(sim, "_simulate_cell_task", fail_worker)
    elif failure == "numeric":
        def fail_numeric(_J):
            raise ArithmeticError("injected nonconvergence")

        monkeypatch.setattr(sim, "_q_details", fail_numeric)
    else:
        def fail_aggregate(_results, _B, **_kwargs):
            raise ValueError("injected aggregate mismatch")

        monkeypatch.setattr(sim, "_aggregate_cells", fail_aggregate)

    result = sim.run_smoke(
        repo_root=root,
        output_path=tmp_path / f"{failure}.json",
        repetitions=1,
        workers=1,
        chunk_datasets=1,
    )
    assert result.run_status == "simulation_incomplete"
    assert result.verdict == "design_not_feasible"
    assert result.transcript["reason_codes"] == [reason_prefix]
    assert json.loads(result.output_path.read_text("ascii"))["verdict"] == (
        "design_not_feasible"
    )


def test_noop_cell_producer_evidence_cannot_complete(tmp_path, monkeypatch):
    root = tmp_path / "root"
    _copy_fixed_input(root, (REPO_ROOT / sim.INPUT_RELATIVE_PATH).read_bytes())

    def noop_cell(arguments):
        _support, J, workload, component, B, _chunk, _q = arguments
        return {
            "J": J,
            "workload": workload,
            "component": component,
            "x": 0,
            "completed_datasets": B,
            "accepted_draws": 6 * J * B,
            "rejected_bytes": 0,
            "final_counter": 1,
            "final_byte_offset": 0,
            "stream_sha256": {"value": "0" * 64, "description": "dummy"},
        }

    monkeypatch.setattr(sim, "_simulate_cell_task", noop_cell)
    result = sim.run_smoke(
        repo_root=root,
        output_path=tmp_path / "noop.json",
        repetitions=1,
        workers=1,
        chunk_datasets=1,
    )
    assert result.run_status == "simulation_incomplete"
    assert result.verdict == "design_not_feasible"
    assert result.transcript["reason_codes"] == [
        "aggregation_inconsistency:ValueError"
    ]


def test_completed_transcript_write_failure_is_structured_DNF(
    tmp_path, monkeypatch
):
    root = tmp_path / "root"
    _copy_fixed_input(root, (REPO_ROOT / sim.INPUT_RELATIVE_PATH).read_bytes())

    def fail_write(_path, _value):
        raise OSError("injected write failure")

    monkeypatch.setattr(sim, "_write_canonical_json", fail_write)
    result = sim.run_smoke(
        repo_root=root,
        output_path=tmp_path / "unwritten.json",
        repetitions=1,
        workers=1,
        chunk_datasets=1,
    )
    assert result.run_status == "simulation_incomplete"
    assert result.verdict == "design_not_feasible"
    assert result.transcript["reason_codes"] == [
        "transcript_write_failure:OSError"
    ]
    assert result.transcript["transcript_persisted"] is False
    assert not result.output_path.exists()


def test_canonical_transcript_rejects_overwrite_and_nonfinite(tmp_path):
    target = tmp_path / "canonical.json"
    value = {"z": 1, "a": [3, 2]}
    sim._write_canonical_json(target, value)
    assert target.read_bytes() == b'{"a":[3,2],"z":1}\n'
    assert json.loads(target.read_text("ascii")) == value
    with pytest.raises(FileExistsError):
        sim._write_canonical_json(target, {"other": True})
    with pytest.raises(ValueError):
        sim._write_canonical_json(tmp_path / "nan.json", {"value": math.nan})
    assert not (tmp_path / "nan.json").exists()


def test_forbidden_D264_names_are_absent_and_docstring_is_non_gate():
    for name in FORBIDDEN_D264_NAMES:
        assert not hasattr(sim, name)
        assert name not in sim.__all__
    assert sim.__all__ == ("SimulationResult", "run_smoke", "run_stress_check")
    assert "not an admission gate" in (sim.__doc__ or "")
    assert "does not complete" in (sim.__doc__ or "")


@pytest.mark.parametrize("J", [2, 3, 14, 20])
def test_q_helper_rejects_J_outside_preregistered_range(J):
    with pytest.raises(ValueError, match="4 <= J <= 13"):
        sim._q_value(J)


def test_all_zero_counts_are_accepted_without_shrinking_acceptance_set():
    verdict, cells, _ = sim._aggregate_cells(_synthetic_results(1_000_000), 1_000_000)
    assert verdict == "pass"
    assert len(cells) == 60
    assert all(cell["U"] <= sim.ALPHA_1 for cell in cells)


def test_strict_lower_bound_and_beta_endpoint_contracts():
    flags, _, _ = sim._false_pass_from_cluster_sums(
        np.zeros((1, 4)), sim._q_value(4)
    )
    assert flags.tolist() == [False]
    assert sim._clopper_pearson_upper(10, 10) == 1.0
    assert sim._regularized_beta(1.0, 1.0, 0.25) == pytest.approx(0.25)
    left = sim._regularized_beta(2.5, 3.5, 0.4)
    right = sim._regularized_beta(3.5, 2.5, 0.6)
    assert left + right == pytest.approx(1.0, abs=2e-15)


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        (999_998, 0.9999999942153539),
        (999_999, 0.9999999999833332),
    ],
)
def test_clopper_pearson_near_upper_endpoint_golden(x, expected):
    assert sim._clopper_pearson_upper(x, 1_000_000) == pytest.approx(
        expected, rel=0.0, abs=5e-16
    )


def test_transcript_records_complete_grammar_and_false_pass_rule():
    transcript = sim._base_transcript("smoke", False, 3, 1, None)
    prng = transcript["prng"]
    assert prng["block_generation"] == (
        "block(counter) = SHA-256(seed_ascii || domain(J,w,k) || "
        "uint64_be(counter))"
    )
    assert prng["domain"] == (
        'ASCII("|t139-a12-v1|" || dec(J) || "|" || w || "|" || k)'
    )
    assert prng["cell_streams"] == "Each (J,w,k) cell has an independent stream."
    assert prng["counter_encoding"] == "exact 8 raw bytes, unsigned big endian"
    assert prng["accepted_index"] == "byte mod 5"
    assert "same digest" in prng["rejection_consumption"]
    assert "Do not discard" in prng["chunk_boundary"]
    assert "accepted index byte sequence" in prng["stream_sha256_definition"]
    assert transcript["false_pass_rule"] == {
        "formula": "mean - q*sqrt(s/J) > 0",
        "comparison": "strict greater than zero",
        "sample_variance_divisor": "J-1",
        "dataset_recentering": "forbidden",
        "zero_variance_positive_mean": "count as a false-pass",
    }


def test_execution_path_records_declaration_and_indeterminate_handling():
    declared = sim._execution_path_record("qsub_compute")
    assert declared == {
        "value": "qsub_compute",
        "determination": "declared",
        "basis": "explicit_caller_declaration",
    }
    assert sim._execution_path_record("login_bounded")["value"] == "login_bounded"
    unknown = sim._execution_path_record(None)
    assert unknown["value"] is None
    assert unknown["determination"] == "indeterminate"
    assert unknown["basis"] == "caller_did_not_declare_execution_path"


@pytest.mark.parametrize(
    ("mode", "authoritative", "B"),
    [
        ("full", True, 999_999),
        ("full", False, sim.FULL_REPETITIONS),
        ("smoke", True, 1),
    ],
)
def test_run_rejects_noncanonical_full_authoritative_combinations(
    tmp_path, mode, authoritative, B
):
    with pytest.raises(ValueError):
        sim._run(
            repo_root=tmp_path,
            output_path=tmp_path / "must-not-exist.json",
            mode=mode,
            authoritative=authoritative,
            B=B,
            workers=1,
            chunk_datasets=1,
        )
    assert not (tmp_path / "must-not-exist.json").exists()


def test_worker_count_is_clamped_and_cli_rejects_above_cell_count(monkeypatch):
    observed = {}

    class ImmediateFuture:
        def __init__(self, function, arguments):
            self.function = function
            self.arguments = arguments

        def result(self):
            return self.function(self.arguments)

    class FakeExecutor:
        def __init__(self, max_workers):
            observed["max_workers"] = max_workers

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def submit(self, function, arguments):
            return ImmediateFuture(function, arguments)

    monkeypatch.setattr(sim, "ProcessPoolExecutor", FakeExecutor)
    monkeypatch.setattr(sim, "as_completed", lambda futures: futures)
    support, _ = sim._load_support(REPO_ROOT)
    results, _q_details, recorded_workers = sim._run_cells(
        support, B=1, workers=sim.CELL_COUNT + 1, chunk_datasets=1
    )
    assert len(results) == sim.CELL_COUNT
    assert observed["max_workers"] == sim.CELL_COUNT
    assert recorded_workers == sim.CELL_COUNT
    assert sim._effective_workers(1) == 1
    assert sim._effective_workers(sim.CELL_COUNT) == sim.CELL_COUNT
    assert sim._effective_workers(sim.CELL_COUNT + 1) == sim.CELL_COUNT
    with pytest.raises(argparse.ArgumentTypeError, match="must not exceed 60"):
        cli._workers("61")


@pytest.mark.parametrize(
    ("run_status", "verdict", "expected_rc"),
    [
        ("completed", "pass", 0),
        ("completed", "design_not_feasible", 3),
        ("precondition_failed", "design_not_feasible", 1),
    ],
)
def test_cli_exit_codes_and_scoped_stdout(
    tmp_path, monkeypatch, capsys, run_status, verdict, expected_rc
):
    transcript = sim._base_transcript(
        "full", True, sim.FULL_REPETITIONS, 1, "login_bounded"
    )
    transcript.update({"run_status": run_status, "verdict": verdict})
    fake = sim.SimulationResult(
        verdict=verdict,
        run_status=run_status,
        authoritative=True,
        transcript=transcript,
        output_path=tmp_path / "result.json",
    )
    monkeypatch.setattr(cli, "run_stress_check", lambda **_kwargs: fake)
    rc = cli.main(
        [
            "--mode",
            "full",
            "--execution-path",
            "login_bounded",
            "--output",
            str(tmp_path / "result.json"),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc == expected_rc
    assert payload["mode"] == "full"
    assert payload["B"] == sim.FULL_REPETITIONS
    assert payload["verdict"] == verdict
    assert payload["claim_scope"] == "a11_empirical_stress_model_only"
    assert payload["pilot_ready"] is False


def test_transcript_hash_fields_are_recomputation_aids_not_acceptance(tmp_path):
    result = sim.run_smoke(
        repo_root=REPO_ROOT,
        output_path=tmp_path / "descriptions.json",
        repetitions=1,
        workers=1,
        chunk_datasets=1,
    )
    descriptions = result.transcript["field_descriptions"]
    for name in ("source_commit", "stream_sha256", "result_sha256"):
        assert "not an acceptance condition" in descriptions[name]
    assert result.transcript["source_commit"]["value"] is None
    assert result.transcript["result_sha256"]["value"]
