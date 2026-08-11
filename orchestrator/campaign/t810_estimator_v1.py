"""T-810 の凍結参照 estimator v1。

入力は自然対数 throughput の node x round 完全行列である。この module は
事前登録した式を逐語的な式文字列の評価ではなく、固定した Python 実装として提供する。
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, lgamma, log, sqrt
from typing import Sequence


ESTIMATOR_VERSION_ID = "node_random_round_fixed_f_interval_v1"
SELECTED_NODE_COUNT = 13
REDUCED_NODE_COUNT = 12
ROUND_COUNT = 10
TAU_STAR = 0.006


try:  # pragma: no cover - この repository の標準環境には SciPy がない。
    from scipy.stats import f as _scipy_f
except ImportError:  # pragma: no cover - backend 定数を通して下の分岐を検査する。
    _scipy_f = None


F_QUANTILE_BACKEND = (
    "scipy.stats.f.ppf" if _scipy_f is not None else "regularized_beta_bisection_v1"
)


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


@dataclass(frozen=True)
class TerminalEvidence:
    """§5.4 の順序付き FSM に必要な集約済み evidence。

    receipt からこの evidence を作る join は validator の責務であり、claimed state は
    意図的に入力へ持たない。
    """

    pre_release_invalid: bool = False
    post_release_pre_measurement_invalid: bool = False
    incomplete_after_start: bool = False
    completed_node_count: int = 0
    complete_round_counts: tuple[int, ...] = ()


def classify_terminal_state(evidence: TerminalEvidence) -> str:
    """§5.4 の上から最初に一致する終端状態を返す。"""

    if evidence.pre_release_invalid:
        return "pre_release_invalid"
    if evidence.post_release_pre_measurement_invalid:
        return "post_release_pre_measurement_invalid"
    if evidence.incomplete_after_start:
        return "incomplete_after_start"
    if evidence.completed_node_count == REDUCED_NODE_COUNT:
        if evidence.complete_round_counts == (ROUND_COUNT,) * REDUCED_NODE_COUNT:
            return "terminal_reduced"
        return "incomplete_after_start"
    if evidence.completed_node_count == SELECTED_NODE_COUNT:
        if evidence.complete_round_counts == (ROUND_COUNT,) * SELECTED_NODE_COUNT:
            return "valid"
        return "incomplete_after_start"
    return "incomplete_after_start"


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


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    """正則化不完全 beta 用の Lentz continued fraction。"""

    max_iterations = 400
    epsilon = 3.0e-14
    tiny = 1.0e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    result = d
    for iteration in range(1, max_iterations + 1):
        even = 2 * iteration
        coefficient = iteration * (b - iteration) * x / (
            (qam + even) * (a + even)
        )
        d = 1.0 + coefficient * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + coefficient / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        result *= d * c

        coefficient = -(a + iteration) * (qab + iteration) * x / (
            (a + even) * (qap + even)
        )
        d = 1.0 + coefficient * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + coefficient / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        result *= delta
        if abs(delta - 1.0) <= epsilon:
            return result
    raise T810EstimatorError("incomplete beta continued fraction did not converge")


def _regularized_beta(x: float, a: float, b: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = exp(
        lgamma(a + b) - lgamma(a) - lgamma(b) + a * log(x) + b * log(1.0 - x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _beta_continued_fraction(a, b, x) / a
    return 1.0 - front * _beta_continued_fraction(b, a, 1.0 - x) / b


def _f_cdf(value: float, numerator_df: int, denominator_df: int) -> float:
    if value <= 0.0:
        return 0.0
    transformed = numerator_df * value / (
        numerator_df * value + denominator_df
    )
    return _regularized_beta(
        transformed, numerator_df / 2.0, denominator_df / 2.0
    )


def f_quantile(probability: float, numerator_df: int, denominator_df: int) -> float:
    """F 分布の分位点。SciPy があれば ppf、なければ固定 bisection を使う。"""

    if not 0.0 < probability < 1.0:
        raise T810EstimatorError("F probability must be strictly between zero and one")
    if numerator_df <= 0 or denominator_df <= 0:
        raise T810EstimatorError("F degrees of freedom must be positive")
    if _scipy_f is not None:  # pragma: no cover - SciPy 環境でのみ通る。
        return float(_scipy_f.ppf(probability, numerator_df, denominator_df))

    lower = 0.0
    upper = 1.0
    while _f_cdf(upper, numerator_df, denominator_df) < probability:
        upper *= 2.0
        if not isfinite(upper):
            raise T810EstimatorError("could not bracket F quantile")
    for _ in range(180):
        middle = (lower + upper) / 2.0
        if _f_cdf(middle, numerator_df, denominator_df) < probability:
            lower = middle
        else:
            upper = middle
    return (lower + upper) / 2.0


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
