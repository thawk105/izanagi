# -*- coding: utf-8 -*-
"""T-810 estimator v1 の式独立 golden と境界検査。"""
from __future__ import annotations

import math
import ast
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parent.parent
REPO_ROOT = ORCHESTRATOR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.campaign.t810_estimator_v1 import (  # noqa: E402
    ESTIMATOR_VERSION_ID,
    F_QUANTILE_BACKEND,
    F_QUANTILE_RUNTIME,
    F_QUANTILES_BINARY64_HEX,
    REDUCED_NODE_COUNT,
    ROUND_COUNT,
    SELECTED_NODE_COUNT,
    TAU_STAR,
    assert_estimator_conformance,
    conclusion_code,
    evaluate_t810,
    f_quantile,
    slope_gate_fires,
)
from orchestrator.campaign.t810_preregistration import (  # noqa: E402
    APPROVAL_RECEIPT_SCHEMA_VERSION,
    PREREG_PATH,
    load_t810_preregistration,
)


FIXTURE_ARTIFACT_SHA256 = "3052af20993481730a826ce08ee26289948f29836d43afb2d7c743cfdd12e404"
FIXTURE_RECEIPT = {
    "artifact_sha256": FIXTURE_ARTIFACT_SHA256,
    "approval_id": "fixture-stage1-review-t810-v1",
    "schema_version": APPROVAL_RECEIPT_SCHEMA_VERSION,
}


def _artifact():
    return load_t810_preregistration(
        PREREG_PATH, approval_receipt=FIXTURE_RECEIPT
    ).projection


def _centered_grid(
    node_count: int, *, node_step: float, round_step: float, slope_step: float
) -> list[list[float]]:
    return [
        [
            node_step * (node - (node_count - 1) / 2.0)
            + (round_step + slope_step * (node - (node_count - 1) / 2.0))
            * (round_ - 4.5)
            for round_ in range(10)
        ]
        for node in range(node_count)
    ]


def _slope_boundary_grid(node_count: int, residual_amplitude: float):
    centered_rounds = [round_ - 4.5 for round_ in range(10)]
    sxx = sum(value**2 for value in centered_rounds)
    mean_square = sxx / 10
    residual_shape = [value**2 - mean_square for value in centered_rounds]
    residual_ss = residual_amplitude**2 * sum(value**2 for value in residual_shape)
    se_squared = residual_ss / 8 / sxx
    node_sample_variance = node_count * (node_count + 1) / 12
    beta_step = math.sqrt(2 * se_squared / node_sample_variance)
    matrix = [
        [
            0.001 * (node - (node_count - 1) / 2)
            + beta_step * (node - (node_count - 1) / 2) * centered_rounds[round_]
            + residual_amplitude * residual_shape[round_]
            for round_ in range(10)
        ]
        for node in range(node_count)
    ]
    return matrix, se_squared


def _matrix_from_vector(vector):
    state = vector["terminal_state"]
    node_count = 13 if state == "valid" else 12
    generation = vector["generation"]
    if generation["kind"] in {"centered-linear-grid", "constant-zero-grid"}:
        return _centered_grid(
            node_count,
            node_step=float(Decimal(generation["node_step"])),
            round_step=float(Decimal(generation["round_step"])),
            slope_step=float(Decimal(generation["slope_step"])),
        )
    if generation["kind"] == "slope-gate-equality-grid":
        matrix, _ = _slope_boundary_grid(
            node_count, float(Decimal(generation["quadratic_residual_amplitude"]))
        )
        return matrix
    if generation["kind"] == "negative-variance-grid":
        centered_nodes = [node - (node_count - 1) / 2 for node in range(node_count)]
        centered_rounds = [round_ - 4.5 for round_ in range(10)]
        mean_square = sum(value**2 for value in centered_rounds) / 10
        residual_shape = [value**2 - mean_square for value in centered_rounds]
        amplitude = float(Decimal(generation["quadratic_residual_amplitude"]))
        return [
            [amplitude * node * residual for residual in residual_shape]
            for node in centered_nodes
        ]
    raise AssertionError(f"unknown frozen generator: {generation['kind']}")


def _independent_mean_squares(vector):
    state = vector["terminal_state"]
    node_count = 13 if state == "valid" else 12
    generation = vector["generation"]
    if generation["kind"] in {"centered-linear-grid", "constant-zero-grid"}:
        node_step = float(Decimal(generation["node_step"]))
        slope_step = float(Decimal(generation["slope_step"]))
        centered_nodes_ss = node_count * (node_count**2 - 1) / 12
        centered_rounds_ss = 82.5
        ms_a = 10 * node_step**2 * centered_nodes_ss / (node_count - 1)
        ms_e = (
            slope_step**2
            * centered_nodes_ss
            * centered_rounds_ss
            / ((node_count - 1) * 9)
        )
        return ms_a, ms_e
    matrix = _matrix_from_vector(vector)
    node_means = [sum(row) / 10 for row in matrix]
    round_means = [sum(row[r] for row in matrix) / node_count for r in range(10)]
    grand = sum(node_means) / node_count
    ms_a = 10 * sum((value - grand) ** 2 for value in node_means) / (node_count - 1)
    ms_e = sum(
        (matrix[i][r] - node_means[i] - round_means[r] + grand) ** 2
        for i in range(node_count)
        for r in range(10)
    ) / ((node_count - 1) * 9)
    return ms_a, ms_e


def _independent_interval(ms_a: float, ms_e: float, node_count: int):
    nu1 = node_count - 1
    nu2 = (node_count - 1) * 9
    frozen = json.loads(PREREG_PATH.read_text())["estimator"][
        "f_quantiles_binary64_hex"
    ][f"nu1={nu1},nu2={nu2}"]
    f_005 = float.fromhex(frozen["p_005"])
    f_095 = float.fromhex(frozen["p_095"])
    tau_hat = math.sqrt(max(0.0, (ms_a - ms_e) / 10))
    tau_l = math.sqrt(max(0.0, (ms_a / f_095 - ms_e) / 10))
    tau_u = math.sqrt(max(0.0, (ms_a / f_005 - ms_e) / 10))
    return tau_hat, tau_l, tau_u


def test_f_quantile_backend_and_reference_values_are_frozen():
    assert F_QUANTILE_BACKEND in {
        "scipy.stats.f.ppf",
        "regularized_beta_bisection_v1",
    }
    assert f_quantile(0.05, 12, 108) == pytest.approx(0.4262813437989489, abs=2e-13)
    assert f_quantile(0.95, 12, 108) == pytest.approx(1.8428843299962905, abs=2e-13)
    assert f_quantile(0.05, 11, 99) == pytest.approx(0.4069887437400106, abs=2e-13)
    assert f_quantile(0.95, 11, 99) == pytest.approx(1.8866836029647311, abs=2e-13)


def test_f_quantiles_use_exact_artifact_binary64_constants_without_runtime_backend():
    artifact_constants = json.loads(PREREG_PATH.read_text())["estimator"]
    assert F_QUANTILE_RUNTIME == "frozen_binary64_hex_v1"
    assert artifact_constants["f_quantile_backend"] == F_QUANTILE_RUNTIME
    expected = {
        (11, 99, "0.05"): "0x1.a0c1a840d05a8p-2",
        (11, 99, "0.95"): "0x1.e2fdb254a20a4p+0",
        (12, 108, "0.05"): "0x1.b48318ba0bb12p-2",
        (12, 108, "0.95"): "0x1.d7c74477a51acp+0",
    }
    assert F_QUANTILES_BINARY64_HEX == expected
    for (nu1, nu2, probability), frozen_hex in expected.items():
        assert f_quantile(float(probability), nu1, nu2).hex() == frozen_hex
        artifact_key = f"nu1={nu1},nu2={nu2}"
        probability_key = "p_005" if probability == "0.05" else "p_095"
        assert (
            artifact_constants["f_quantiles_binary64_hex"][artifact_key][probability_key]
            == frozen_hex
        )


def test_artifact_literals_and_reference_module_dispatch_are_identical():
    artifact = _artifact()
    assert artifact["estimator"]["version_id"] == ESTIMATOR_VERSION_ID
    assert artifact["design"]["selected"]["node_count"] == SELECTED_NODE_COUNT == 13
    assert artifact["design"]["selected"]["round_count"] == ROUND_COUNT == 10
    assert (
        artifact["design"]["effective_states"]["terminal_reduced"]["effective_node_count"]
        == REDUCED_NODE_COUNT
        == 12
    )
    assert float(artifact["design"]["tau_star"]) == TAU_STAR
    source = (ORCHESTRATOR / "campaign/t810_estimator_v1.py").read_text()
    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "eval"
        for node in ast.walk(tree)
    )


def test_all_artifact_golden_vectors_match_independently_reconstructed_formula():
    artifact = _artifact()
    assert artifact["estimator"]["version_id"] == ESTIMATOR_VERSION_ID
    ids = set()
    for vector in artifact["golden_vectors"]:
        ids.add(vector["id"])
        matrix = _matrix_from_vector(vector)
        result = evaluate_t810(matrix, terminal_state=vector["terminal_state"])
        ms_a, ms_e = _independent_mean_squares(vector)
        node_count = 13 if vector["terminal_state"] == "valid" else 12
        expected = _independent_interval(ms_a, ms_e, node_count)
        assert result.ms_a == pytest.approx(ms_a, rel=2e-13, abs=2e-18)
        assert result.ms_e == pytest.approx(ms_e, rel=2e-13, abs=2e-18)
        assert (result.tau_hat, result.tau_l, result.tau_u) == pytest.approx(
            expected, rel=2e-13, abs=2e-15
        )
        frozen = vector["expected"]
        assert result.tau_hat == pytest.approx(float(frozen["tau_hat"]), abs=2e-15)
        assert result.tau_l == pytest.approx(float(frozen["tau_L"]), abs=2e-15)
        assert result.tau_u == pytest.approx(float(frozen["tau_U"]), abs=2e-15)
        assert result.slope_gate_fired is frozen["slope_gate_fired"]
        assert result.conclusion_code == frozen["conclusion_code"]
    assert ids == {
        "selected_n13_normal",
        "reduced_n12_normal",
        "upper_truncated_to_zero",
        "upper_equality_boundary",
        "lower_equality_boundary",
        "slope_gate_fires",
        "slope_gate_strict_boundary",
    }
    assert_estimator_conformance(
        load_t810_preregistration(PREREG_PATH, approval_receipt=FIXTURE_RECEIPT)
    )


def test_interval_uses_low_f_for_upper_high_f_for_lower_and_divides_by_rounds():
    matrix = _centered_grid(13, node_step=0.003, round_step=-0.0002, slope_step=0)
    result = evaluate_t810(matrix, terminal_state="valid")
    assert result.tau_u == pytest.approx(
        math.sqrt(max(0, (result.ms_a / result.f_005 - result.ms_e) / 10)), abs=1e-15
    )
    assert result.tau_l == pytest.approx(
        math.sqrt(max(0, (result.ms_a / result.f_095 - result.ms_e) / 10)), abs=1e-15
    )
    assert result.tau_u > result.tau_l


def test_interval_truncates_negative_variances_to_zero():
    vector = next(
        item
        for item in _artifact()["golden_vectors"]
        if item["id"] == "upper_truncated_to_zero"
    )
    result = evaluate_t810(_matrix_from_vector(vector), terminal_state="valid")
    assert result.ms_a < result.ms_e
    assert (result.tau_hat, result.tau_l, result.tau_u) == (0.0, 0.0, 0.0)
    assert result.slope_gate_fired is False


def test_slope_gate_uses_strict_inequality_at_exact_boundary():
    assert slope_gate_fires(2.0, 1.0) is False
    assert slope_gate_fires(math.nextafter(2.0, math.inf), 1.0) is True
    matrix, expected_v = _slope_boundary_grid(13, 0.001)
    result = evaluate_t810(matrix, terminal_state="valid")
    assert result.v_beta == pytest.approx(expected_v, rel=2e-14)
    assert result.s_beta == pytest.approx(2 * expected_v, rel=2e-14)
    assert result.slope_gate_fired is False


def test_reduced_state_uses_n12_degrees_of_freedom_not_selected_n13():
    matrix = _centered_grid(12, node_step=0.001, round_step=0.00015, slope_step=0)
    result = evaluate_t810(matrix, terminal_state="terminal_reduced")
    assert (result.effective_node_count, result.nu1, result.nu2) == (12, 11, 99)
    correct = math.sqrt(max(0, (result.ms_a / f_quantile(0.05, 11, 99) - result.ms_e) / 10))
    wrong_n13 = math.sqrt(max(0, (result.ms_a / f_quantile(0.05, 12, 108) - result.ms_e) / 10))
    assert result.tau_u == pytest.approx(correct, abs=1e-15)
    assert abs(result.tau_u - wrong_n13) > 1e-4


def test_reduced_golden_vector_exercises_live_slope_gate():
    vector = next(
        item
        for item in _artifact()["golden_vectors"]
        if item["id"] == "slope_gate_fires"
    )
    assert vector["terminal_state"] == "terminal_reduced"
    result = evaluate_t810(
        _matrix_from_vector(vector), terminal_state="terminal_reduced"
    )
    assert result.slope_gate_fired is True
    assert result.conclusion_code == "underdetermined_model_violation"


def test_decision_equalities_fall_to_row_five():
    assert conclusion_code(
        terminal_state="valid",
        slope_gate_fired=False,
        tau_l=0.001,
        tau_u=TAU_STAR,
    ) == "underdetermined"
    assert conclusion_code(
        terminal_state="valid",
        slope_gate_fired=False,
        tau_l=TAU_STAR,
        tau_u=0.02,
    ) == "underdetermined"


def test_artifact_exact_scalar_boundaries_replay_strict_inequalities():
    vectors = {item["id"]: item for item in _artifact()["scalar_golden_vectors"]}
    for vector_id in ("upper_exact_scalar_equality", "lower_exact_scalar_equality"):
        vector = vectors[vector_id]
        inputs = vector["input"]
        assert conclusion_code(
            terminal_state=inputs["terminal_state"],
            slope_gate_fired=inputs["slope_gate_fired"],
            tau_l=float.fromhex(inputs["tau_l_binary64_hex"]),
            tau_u=float.fromhex(inputs["tau_u_binary64_hex"]),
            tau_star=float.fromhex(inputs["tau_star_binary64_hex"]),
        ) == "underdetermined"
    slope = vectors["slope_exact_scalar_equality"]
    assert slope_gate_fires(
        float.fromhex(slope["input"]["s_beta_binary64_hex"]),
        float.fromhex(slope["input"]["v_beta_binary64_hex"]),
    ) is False


def test_decision_is_ordered_first_match_with_gate_before_interval():
    assert conclusion_code(
        terminal_state="valid",
        slope_gate_fired=True,
        tau_l=0.0,
        tau_u=0.0,
    ) == "underdetermined_model_violation"
    assert conclusion_code(
        terminal_state="incomplete_after_start",
        slope_gate_fired=True,
        tau_l=1.0,
        tau_u=2.0,
    ) == "incomplete_after_start"


def test_estimator_does_not_duplicate_validator_terminal_fsm():
    source = (ORCHESTRATOR / "campaign/t810_estimator_v1.py").read_text()
    tree = ast.parse(source)
    public_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    assert "classify_terminal_state" not in public_names
    assert "TerminalEvidence" not in public_names


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
