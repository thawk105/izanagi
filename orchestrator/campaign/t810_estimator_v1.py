"""T-810 の凍結参照 estimator v1。

入力は自然対数 throughput の node x round 完全行列である。この module は
事前登録した式を逐語的な式文字列の評価ではなく、固定した Python 実装として提供する。
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import isfinite, sqrt
from typing import Any, Mapping, Sequence


ESTIMATOR_VERSION_ID = "node_random_round_fixed_f_interval_v1"
SELECTED_NODE_COUNT = 13
REDUCED_NODE_COUNT = 12
ROUND_COUNT = 10
TAU_STAR = 0.006
# 導出 provenance。runtime は下記 hex lookup だけを使う。
F_QUANTILE_BACKEND = "regularized_beta_bisection_v1"
F_QUANTILE_RUNTIME = "frozen_binary64_hex_v1"
F_QUANTILES_BINARY64_HEX = {
    (12, 108, "0.05"): "0x1.b48318ba0bb12p-2",
    (12, 108, "0.95"): "0x1.d7c74477a51acp+0",
    (11, 99, "0.05"): "0x1.a0c1a840d05a8p-2",
    (11, 99, "0.95"): "0x1.e2fdb254a20a4p+0",
}


class T810EstimatorError(ValueError):
    """入力が凍結 estimator 契約に適合しない。"""


@dataclass(frozen=True)
class T810Estimate:
    estimator_version_id: str
    terminal_state: str
    effective_node_count: int
    round_count: int
    nu1: int
    nu2: int
    ms_a: float
    ms_e: float
    f_005: float
    f_095: float
    tau_hat: float
    tau_l: float
    tau_u: float
    beta_hat: tuple[float, ...]
    beta_se: tuple[float, ...]
    s_beta: float
    v_beta: float
    slope_gate_fired: bool
    conclusion_code: str


def effective_node_count(terminal_state: str) -> int:
    if terminal_state == "valid":
        return SELECTED_NODE_COUNT
    if terminal_state == "terminal_reduced":
        return REDUCED_NODE_COUNT
    raise T810EstimatorError(
        "primary estimation is forbidden for terminal state " + repr(terminal_state)
    )


def slope_gate_fires(s_beta: float, v_beta: float) -> bool:
    """凍結した狭義不等号を一箇所に置く。"""

    if not isfinite(s_beta) or not isfinite(v_beta) or s_beta < 0 or v_beta < 0:
        raise T810EstimatorError("slope variances must be finite and non-negative")
    return s_beta > 2.0 * v_beta


def conclusion_code(
    *, terminal_state: str, slope_gate_fired: bool, tau_l: float, tau_u: float,
    tau_star: float = TAU_STAR,
) -> str:
    """§5.3 の順序付き first-match 判定を行う。"""

    if terminal_state not in {"valid", "terminal_reduced"}:
        return terminal_state
    if slope_gate_fired:
        return "underdetermined_model_violation"
    if tau_u < tau_star:
        return "material_node_difference_refuted"
    if tau_l > tau_star:
        return "material_node_difference_supported"
    return "underdetermined"


def f_quantile(probability: float, numerator_df: int, denominator_df: int) -> float:
    """事前登録した 2 自由度組・2 分位点の binary64 定数を返す。"""

    if not 0.0 < probability < 1.0:
        raise T810EstimatorError("F probability must be strictly between zero and one")
    if numerator_df <= 0 or denominator_df <= 0:
        raise T810EstimatorError("F degrees of freedom must be positive")
    if probability == 0.05:
        probability_key = "0.05"
    elif probability == 0.95:
        probability_key = "0.95"
    else:
        raise T810EstimatorError("the requested F probability is not frozen")
    key = (numerator_df, denominator_df, probability_key)
    try:
        frozen_hex = F_QUANTILES_BINARY64_HEX[key]
    except KeyError as exc:
        raise T810EstimatorError(
            "F quantile is not frozen for the requested probability and degrees of freedom"
        ) from exc
    return float.fromhex(frozen_hex)


def _validated_matrix(
    values: Sequence[Sequence[float]], *, terminal_state: str
) -> tuple[tuple[float, ...], ...]:
    node_count = effective_node_count(terminal_state)
    if len(values) != node_count:
        raise T810EstimatorError(
            f"{terminal_state} requires exactly {node_count} node rows"
        )
    rows: list[tuple[float, ...]] = []
    for row in values:
        if len(row) != ROUND_COUNT:
            raise T810EstimatorError("every node must have exactly ten rounds")
        converted = tuple(float(value) for value in row)
        if any(not isfinite(value) for value in converted):
            raise T810EstimatorError("log throughput values must be finite")
        rows.append(converted)
    return tuple(rows)


def evaluate_t810(
    log_throughput: Sequence[Sequence[float]], *, terminal_state: str
) -> T810Estimate:
    """凍結した二元配置 interval、slope gate、結論を一度に評価する。"""

    matrix = _validated_matrix(log_throughput, terminal_state=terminal_state)
    node_count = len(matrix)
    round_count = ROUND_COUNT
    nu1 = node_count - 1
    nu2 = (node_count - 1) * (round_count - 1)

    node_means = tuple(sum(row) / round_count for row in matrix)
    round_means = tuple(
        sum(matrix[node][round_] for node in range(node_count)) / node_count
        for round_ in range(round_count)
    )
    grand_mean = sum(node_means) / node_count
    ss_a = round_count * sum((mean - grand_mean) ** 2 for mean in node_means)
    ss_e = sum(
        (
            matrix[node][round_]
            - node_means[node]
            - round_means[round_]
            + grand_mean
        )
        ** 2
        for node in range(node_count)
        for round_ in range(round_count)
    )
    ms_a = ss_a / nu1
    ms_e = ss_e / nu2

    f_005 = f_quantile(0.05, nu1, nu2)
    f_095 = f_quantile(0.95, nu1, nu2)
    point_variance = max(0.0, (ms_a - ms_e) / round_count)
    lower_variance = max(0.0, (ms_a / f_095 - ms_e) / round_count)
    upper_variance = max(0.0, (ms_a / f_005 - ms_e) / round_count)

    centered_rounds = tuple(
        (index + 1) - (round_count + 1) / 2.0 for index in range(round_count)
    )
    sxx = sum(value * value for value in centered_rounds)
    beta_hat: list[float] = []
    beta_se: list[float] = []
    for row, row_mean in zip(matrix, node_means):
        beta = sum(
            centered_rounds[index] * (row[index] - row_mean)
            for index in range(round_count)
        ) / sxx
        residual_ss = sum(
            (row[index] - row_mean - beta * centered_rounds[index]) ** 2
            for index in range(round_count)
        )
        beta_hat.append(beta)
        beta_se.append(sqrt(max(0.0, residual_ss / (round_count - 2) / sxx)))

    beta_bar = sum(beta_hat) / node_count
    s_beta = sum((beta - beta_bar) ** 2 for beta in beta_hat) / nu1
    v_beta = sum(value * value for value in beta_se) / node_count
    gate = slope_gate_fires(s_beta, v_beta)
    tau_hat = sqrt(point_variance)
    tau_l = sqrt(lower_variance)
    tau_u = sqrt(upper_variance)
    code = conclusion_code(
        terminal_state=terminal_state,
        slope_gate_fired=gate,
        tau_l=tau_l,
        tau_u=tau_u,
    )
    return T810Estimate(
        estimator_version_id=ESTIMATOR_VERSION_ID,
        terminal_state=terminal_state,
        effective_node_count=node_count,
        round_count=round_count,
        nu1=nu1,
        nu2=nu2,
        ms_a=ms_a,
        ms_e=ms_e,
        f_005=f_005,
        f_095=f_095,
        tau_hat=tau_hat,
        tau_l=tau_l,
        tau_u=tau_u,
        beta_hat=tuple(beta_hat),
        beta_se=tuple(beta_se),
        s_beta=s_beta,
        v_beta=v_beta,
        slope_gate_fired=gate,
        conclusion_code=code,
    )


def _matrix_from_golden_vector(
    vector: Mapping[str, Any],
) -> tuple[tuple[float, ...], ...]:
    terminal_state = str(vector["terminal_state"])
    node_count = effective_node_count(terminal_state)
    generation = vector["generation"]
    kind = generation["kind"]
    centered_rounds = tuple(index - 4.5 for index in range(ROUND_COUNT))
    centered_nodes = tuple(
        index - (node_count - 1) / 2.0 for index in range(node_count)
    )
    if kind in {"centered-linear-grid", "constant-zero-grid"}:
        node_step = float(Decimal(generation["node_step"]))
        round_step = float(Decimal(generation["round_step"]))
        slope_step = float(Decimal(generation["slope_step"]))
        return tuple(
            tuple(
                node_step * centered_node
                + (round_step + slope_step * centered_node) * centered_round
                for centered_round in centered_rounds
            )
            for centered_node in centered_nodes
        )
    if kind == "negative-variance-grid":
        amplitude = float(Decimal(generation["quadratic_residual_amplitude"]))
        mean_square = sum(value * value for value in centered_rounds) / ROUND_COUNT
        residual_shape = tuple(value * value - mean_square for value in centered_rounds)
        return tuple(
            tuple(amplitude * centered_node * residual for residual in residual_shape)
            for centered_node in centered_nodes
        )
    if kind == "slope-gate-equality-grid":
        residual_amplitude = float(
            Decimal(generation["quadratic_residual_amplitude"])
        )
        node_step = float(Decimal(generation["node_intercept_step"]))
        sxx = sum(value * value for value in centered_rounds)
        mean_square = sxx / ROUND_COUNT
        residual_shape = tuple(value * value - mean_square for value in centered_rounds)
        residual_ss = residual_amplitude**2 * sum(
            value * value for value in residual_shape
        )
        se_squared = residual_ss / (ROUND_COUNT - 2) / sxx
        node_sample_variance = node_count * (node_count + 1) / 12
        beta_step = sqrt(2 * se_squared / node_sample_variance)
        return tuple(
            tuple(
                node_step * centered_node
                + beta_step * centered_node * centered_rounds[round_index]
                + residual_amplitude * residual_shape[round_index]
                for round_index in range(ROUND_COUNT)
            )
            for centered_node in centered_nodes
        )
    raise T810EstimatorError(f"unknown frozen golden generator: {kind!r}")


def _require_frozen_float(actual: float, expected: str, field: str) -> None:
    frozen = float(Decimal(expected))
    if actual.hex() != frozen.hex():
        raise T810EstimatorError(
            f"estimator conformance failed for {field}: "
            f"{actual.hex()} != {frozen.hex()}"
        )


def assert_estimator_conformance(preregistration: Any) -> None:
    """artifact の全 matrix / exact-scalar golden を現実装で再生する。"""

    projection = preregistration.projection
    if projection["estimator"]["f_quantile_backend"] != F_QUANTILE_RUNTIME:
        raise T810EstimatorError("frozen F runtime does not match the estimator")
    artifact_f = projection["estimator"]["f_quantiles_binary64_hex"]
    implemented_f = {
        "nu1=11,nu2=99": {
            "p_005": F_QUANTILES_BINARY64_HEX[(11, 99, "0.05")],
            "p_095": F_QUANTILES_BINARY64_HEX[(11, 99, "0.95")],
        },
        "nu1=12,nu2=108": {
            "p_005": F_QUANTILES_BINARY64_HEX[(12, 108, "0.05")],
            "p_095": F_QUANTILES_BINARY64_HEX[(12, 108, "0.95")],
        },
    }
    if artifact_f != implemented_f:
        raise T810EstimatorError("frozen F constants do not match the estimator")

    for vector in projection["golden_vectors"]:
        result = evaluate_t810(
            _matrix_from_golden_vector(vector),
            terminal_state=vector["terminal_state"],
        )
        expected = vector["expected"]
        _require_frozen_float(result.tau_hat, expected["tau_hat"], vector["id"])
        _require_frozen_float(result.tau_l, expected["tau_L"], vector["id"])
        _require_frozen_float(result.tau_u, expected["tau_U"], vector["id"])
        if result.slope_gate_fired is not expected["slope_gate_fired"]:
            raise T810EstimatorError(
                f"estimator conformance failed for {vector['id']} slope gate"
            )
        if result.conclusion_code != expected["conclusion_code"]:
            raise T810EstimatorError(
                f"estimator conformance failed for {vector['id']} conclusion"
            )

    for vector in projection["scalar_golden_vectors"]:
        inputs = vector["input"]
        if vector["operation"] == "conclusion_code":
            actual = conclusion_code(
                terminal_state=inputs["terminal_state"],
                slope_gate_fired=inputs["slope_gate_fired"],
                tau_l=float.fromhex(inputs["tau_l_binary64_hex"]),
                tau_u=float.fromhex(inputs["tau_u_binary64_hex"]),
                tau_star=float.fromhex(inputs["tau_star_binary64_hex"]),
            )
            if actual != vector["expected"]["conclusion_code"]:
                raise T810EstimatorError(
                    f"estimator conformance failed for {vector['id']} conclusion"
                )
        elif vector["operation"] == "slope_gate_fires":
            actual = slope_gate_fires(
                float.fromhex(inputs["s_beta_binary64_hex"]),
                float.fromhex(inputs["v_beta_binary64_hex"]),
            )
            if actual is not vector["expected"]["slope_gate_fired"]:
                raise T810EstimatorError(
                    f"estimator conformance failed for {vector['id']} slope gate"
                )
        else:  # schema validation should make this unreachable; keep fail-closed.
            raise T810EstimatorError(
                f"unknown scalar golden operation: {vector['operation']!r}"
            )
