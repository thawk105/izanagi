"""Codex role projection の semantic policy validator。

JSON Schema はtop-level envelopeを閉じcritical fieldをtypedにするが、一部nested objectは
意図的にopenである。このmoduleはschemaで表現しきれないrole間条件をtrusted launcherが
model呼出し前後に検査するfail-closed policyを提供する。

recursive detector が検査するのは JSON object の **key** だけである。opaque string 内の
自然言語・埋め込みJSON・コードを安全に再解釈することはしない。その内容から禁止情報を除く
責任は trusted projection producer に残る。この限界を prompt-only の保証で隠さない。
"""
from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Mapping, Sequence
from typing import Any

from orchestrator.campaign import backoff_hole_grammar


POLICY_VERSION = "izanagi.codex-role-policy/v1"
OPAQUE_STRING_POLICY = "trusted-projection-producer-responsibility"
OPEN_SUBTREE_POLICY = "trusted-projection-producer-responsibility"

# key は ``_normalise_key`` 後の token。role ごとに明示し、概念classから実行時に
# 推測生成しない。delimiter単位で一致させ、例えば ``expected_verdict`` を禁止しても
# trusted verifier input の ``verdict`` 自体は許可する。
ROLE_FORBIDDEN_KEY_TOKENS: dict[str, tuple[str, ...]] = {
    "auditor": (
        "fitness", "fitnesses", "throughput", "throughputs", "winner", "winners",
        "raw_wal", "raw_wals", "wal", "wals", "planner_coder_history",
        "planner_coder_histories", "history", "histories", "median_tps",
        "leading_indicator", "leading_indicators",
        "winning_mechanism", "winning_mechanisms",
    ),
    "axis-proposer": (
        "winner_value", "winner_values", "winner", "winners", "candidate_ranking",
        "candidate_rankings", "ranking", "rankings", "critic_recommend",
        "critic_recommends", "critic_recommendation", "critic_recommendations",
        "recommend", "recommends", "recommendation", "recommendations",
        "dead_axis_attribution", "dead_axis_attributions", "performance_hint",
        "performance_hints",
    ),
    "calibrator": (
        "trace_enabled_performance", "trace_enabled_performances", "trace_enabled",
        "campaign_fitness", "campaign_fitnesses", "between_run_floor_as_within_run",
        "between_run_floors_as_within_run", "between_run_floor", "between_run_floors",
    ),
    "coder": (
        "wal", "wals", "fitness", "fitnesses", "winner_value", "winner_values",
        "winner", "winners", "docs_result", "docs_results", "trace_gate_edit",
        "trace_gate_edits",
    ),
    "coder-v4-autonomous": (
        "external_winner_value", "external_winner_values", "winner", "winners",
        "candidate_ranking", "candidate_rankings", "ranking", "rankings",
        "unevaluated_performance", "unevaluated_performances",
        "known_optimal_mechanism", "known_optimal_mechanisms",
        "optimal_mechanism", "optimal_mechanisms",
    ),
    "coder-v4-autonomous-k2": (
        "unevaluated_performance", "unevaluated_performances",
    ),
    "coder-v4-autonomous-policy": (
        "external_winning_policy", "external_winning_policies",
        "winning_policy", "winning_policies", "winner", "winners",
        "candidate_ranking", "candidate_rankings", "ranking", "rankings",
        "unevaluated_performance", "unevaluated_performances",
        "known_optimal_mechanism", "known_optimal_mechanisms",
        "optimal_mechanism", "optimal_mechanisms",
    ),
    "coder-v4-autonomous-policy-ir": (
        "external_winning_policy", "external_winning_policies",
        "winning_policy", "winning_policies", "winner", "winners",
        "candidate_ranking", "candidate_rankings", "ranking", "rankings",
        "unevaluated_performance", "unevaluated_performances",
        "known_optimal_mechanism", "known_optimal_mechanisms",
        "optimal_mechanism", "optimal_mechanisms",
    ),
    "coder-v4-autonomous-sort": (
        "external_winning_comparator", "external_winning_comparators",
        "winning_comparator", "winning_comparators", "winner", "winners",
        "candidate_ranking", "candidate_rankings", "ranking", "rankings",
        "unevaluated_performance", "unevaluated_performances",
        "known_optimal_mechanism", "known_optimal_mechanisms",
        "optimal_mechanism", "optimal_mechanisms",
    ),
    "coder-v4-autonomous-trigger-gating": (
        "external_winning_gate", "external_winning_gates", "winning_gate",
        "winning_gates", "winner", "winners", "candidate_ranking",
        "candidate_rankings", "ranking", "rankings", "unevaluated_performance",
        "unevaluated_performances", "known_optimal_mechanism",
        "known_optimal_mechanisms", "optimal_mechanism", "optimal_mechanisms",
    ),
    "critic": (
        "uncertified_fitness", "uncertified_fitnesses", "raw_untrusted_instruction",
        "raw_untrusted_instructions", "noise_floor_overclaim", "noise_floor_overclaims",
    ),
    "critic-experiment": (
        "unevaluated_fitness", "unevaluated_fitnesses", "fitness", "fitnesses",
        "winner_tied_set", "winner_tied_sets", "winner", "winners",
        "arrival_verdict", "arrival_verdicts", "raw_wal", "raw_wals", "wal",
        "wals", "source_tree", "source_trees",
    ),
    "planner-v4": (
        "winner_value", "winner_values", "winner", "winners", "grid_optimum",
        "grid_optima", "technical_whiteboard_detail", "technical_whiteboard_details",
        "source_tree", "source_trees",
    ),
    "profiler": (
        "uncertified_variant", "uncertified_variants", "trace_enabled_profile",
        "trace_enabled_profiles", "trace_enabled", "concurrent_benchmark",
        "concurrent_benchmarks", "profile_throughput_as_headline",
        "profile_throughput_as_headlines", "profile_throughputs_as_headline",
    ),
    "selector-8b": (
        "arm", "holdout", "target", "descriptor_source", "variant_binding",
        "binding_key", "winner", "measured_tps", "throughput", "sources",
        "oracle",
    ),
    "verifier": (
        "throughput", "throughputs", "fitness", "fitnesses", "expected_verdict",
        "expected_verdicts", "winner", "winners", "implementation_fix_request",
        "implementation_fix_requests",
    ),
}

_DIRECTION = frozenset({"increase", "decrease", "explore_both"})
_MAGNITUDE = frozenset({"small", "medium", "large"})
_CONFIDENCE = frozenset({"high", "medium", "low"})
_GENOME_RE = re.compile(r"^B[01]-[LT]-W[01]$")
_TRIGGER_GATE_WIRE_RE = re.compile(r"^[01]{5}$")
TRIGGER_GATE_SEMANTIC_LITERAL = (
    'trigger-gating-semantic/v1={"bit_order_lsb_first":["lock-conflict",'
    '"update-absent","readvali-tid","readvali-locked","node-vali"],'
    '"wire_value_meaning":{"0":"skip","1":"backoff"},'
    '"kUnset":{"owner":"emitter","always_true":true,"meaning":"backoff"}}'
)
_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_NORMALISE_RE = re.compile(r"[^a-z0-9]+")
_SELECTOR_8B_CANDIDATES = (
    ("c01", "protocol_flag_bundle"),
    ("c02", "fixed_abort_backoff"),
    ("c03", "write_set_ordering"),
    ("c04", "subset_abort_reason_gate"),
    ("c05", "all_abort_reason_gate"),
    ("c06", "upstream_defaults"),
)


class RolePolicyError(ValueError):
    """projection/result が role semantic policy に違反した。"""


def _normalise_key(key: str) -> str:
    expanded = _CAMEL_BOUNDARY_RE.sub("_", key)
    return _NORMALISE_RE.sub("_", expanded.casefold()).strip("_")


def _contains_token(key: str, token: str) -> bool:
    return key == token or key.startswith(token + "_") or key.endswith("_" + token) \
        or ("_" + token + "_") in key


def _resolve_role(role: Any) -> Any:
    if isinstance(role, str):
        # top-level importを避け、spec -> policy(constants) の依存をcycleにしない。
        from .spec import get_role_spec
        return get_role_spec(role)
    if not isinstance(getattr(role, "name", None), str):
        raise RolePolicyError("role は role名またはRoleSpecでなければならない")
    return role


def find_forbidden_keys(role: Any, value: Any) -> tuple[str, ...]:
    """role別deny tokenに一致するmapping keyのJSON pathを返す。

    string value は意図的にopaqueのまま扱う。list内のobjectは再帰検査する。
    """

    spec = _resolve_role(role)
    tokens = tuple(spec.forbidden_key_tokens)
    findings: list[str] = []

    def visit(node: Any, path: str) -> None:
        if isinstance(node, Mapping):
            for raw_key, child in node.items():
                if not isinstance(raw_key, str):
                    findings.append(f"{path}: non-string-key")
                    continue
                key = _normalise_key(raw_key)
                matched = next((token for token in tokens if _contains_token(key, token)), None)
                child_path = f"{path}.{raw_key}"
                if matched is not None:
                    findings.append(f"{child_path} (deny-token={matched})")
                visit(child, child_path)
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
            for index, child in enumerate(node):
                visit(child, f"{path}[{index}]")

    visit(value, "$")
    return tuple(findings)


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RolePolicyError(f"{path}: objectでなければならない")
    return value


def _array(value: Any, path: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise RolePolicyError(f"{path}: arrayでなければならない")
    return value


def _enum(value: Any, allowed: frozenset[str], path: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise RolePolicyError(f"{path}: 許可値は{sorted(allowed)}")
    return value


def _planner_direction(value: Any, *, axis: str, path: str) -> None:
    direction = _mapping(value, path)
    if direction.get("axis") != axis:
        raise RolePolicyError(f"{path}.axis: {axis!r}固定")
    _enum(direction.get("direction"), _DIRECTION, f"{path}.direction")
    _enum(direction.get("magnitude"), _MAGNITUDE, f"{path}.magnitude")


def _axis_source_map(data: Mapping[str, Any]) -> dict[str, str]:
    stock = _array(data.get("stock_excerpts"), "input.stock_excerpts")
    surfaces = _array(data.get("edit_surface_map"), "input.edit_surface_map")
    stock_by_region: dict[str, str] = {}
    for index, raw in enumerate(stock):
        item = _mapping(raw, f"input.stock_excerpts[{index}]")
        region = item.get("region")
        source_rel = item.get("source_rel")
        if not isinstance(region, str) or not region:
            raise RolePolicyError(f"input.stock_excerpts[{index}].regionは非空string")
        if not isinstance(source_rel, str) or not source_rel:
            raise RolePolicyError(f"input.stock_excerpts[{index}].source_relは非空string")
        if region in stock_by_region:
            raise RolePolicyError(f"input.stock_excerpts region重複: {region!r}")
        stock_by_region[region] = source_rel

    surface_regions: set[str] = set()
    for index, raw in enumerate(surfaces):
        item = _mapping(raw, f"input.edit_surface_map[{index}]")
        region = item.get("region")
        if not isinstance(region, str) or not region:
            raise RolePolicyError(f"input.edit_surface_map[{index}].regionは非空string")
        if region in surface_regions:
            raise RolePolicyError(f"input.edit_surface_map region重複: {region!r}")
        surface_regions.add(region)
    if set(stock_by_region) != surface_regions:
        raise RolePolicyError(
            "axis-proposer stock_excerpts/edit_surface_map region集合が不一致"
        )
    directive = data.get("hole_region_directive")
    if directive is not None and directive not in surface_regions:
        raise RolePolicyError("axis-proposer hole_region_directiveが編集面地図に無い")
    return stock_by_region


def _nonnegative_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RolePolicyError(f"{path}: 0以上のintegerが必要")
    return value


def _verifier_invariants(result: Mapping[str, Any], path: str) -> None:
    verdict = result.get("verdict")
    expected = {
        "serializable": (True, True),
        "non-serializable": (False, False),
        "indeterminate": (True, False),
    }
    if verdict not in expected:
        raise RolePolicyError(f"{path}.verdict: 三値判定外")
    serializable, certified = expected[verdict]
    if result.get("serializable") is not serializable:
        raise RolePolicyError(
            f"{path}.serializable: verdict={verdict!r}との不変条件に違反"
        )
    if result.get("certified") is not certified:
        raise RolePolicyError(
            f"{path}.certified: verdict={verdict!r}との不変条件に違反"
        )
    stats = _mapping(result.get("stats"), f"{path}.stats")
    txns = _nonnegative_int(stats.get("txns"), f"{path}.stats.txns")
    total_cycles = _nonnegative_int(
        result.get("total_cycles"), f"{path}.total_cycles"
    )
    integrity = _mapping(result.get("integrity"), f"{path}.integrity")
    clean = integrity.get("clean")
    if not isinstance(clean, bool):
        raise RolePolicyError(f"{path}.integrity.clean: booleanが必要")
    anomalies = _array(result.get("anomalies"), f"{path}.anomalies")
    if verdict == "serializable":
        if txns == 0 or not clean or total_cycles != 0 or anomalies:
            raise RolePolicyError(
                f"{path}: certified serializableはtxns>0/clean/cycles=0/anomalies空固定"
            )
    elif verdict == "non-serializable":
        if txns == 0 or total_cycles == 0 or not anomalies:
            raise RolePolicyError(
                f"{path}: non-serializableはtxns>0/cycles>0/anomaly witness必須"
            )
    else:
        if total_cycles != 0 or anomalies or (txns > 0 and clean):
            raise RolePolicyError(
                f"{path}: indeterminateはacyclicかつtxns=0またはintegrity unclean"
            )


def validate_input_semantics(role: Any, projected_input: Any) -> None:
    """schema検証済みprojected inputのrole間条件をfail-closedで検証する。"""

    spec = _resolve_role(role)
    data = _mapping(projected_input, "input")
    forbidden = find_forbidden_keys(spec, data)
    if forbidden:
        raise RolePolicyError(
            f"{spec.name}: recursive forbidden keyを検出: {', '.join(forbidden)}"
        )

    if spec.name == "auditor":
        working_diff = data.get("working_diff")
        diff_digest = data.get("diff_digest")
        if not isinstance(working_diff, str) or not isinstance(diff_digest, str):
            raise RolePolicyError("auditor working_diff/diff_digestはstring")
        observed = hashlib.sha256(working_diff.encode("utf-8")).hexdigest()
        if diff_digest != observed:
            raise RolePolicyError(
                "auditor diff_digestがUTF-8 working_diffのSHA-256と不一致"
            )
    elif spec.name == "axis-proposer":
        _axis_source_map(data)
    elif spec.name == "calibrator":
        measurements = _array(data.get("measurements"), "input.measurements")
        if not measurements:
            raise RolePolicyError("calibrator measurementsは1件以上必要")
        records: list[int] = []
        for index, raw in enumerate(measurements):
            item = _mapping(raw, f"input.measurements[{index}]")
            value = item.get("records")
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise RolePolicyError(
                    f"input.measurements[{index}].recordsは1以上のinteger"
                )
            records.append(value)
        if len(records) != len(set(records)):
            raise RolePolicyError("calibrator measurement records重複")
    elif spec.name in {
        "coder-v4-autonomous",
        "coder-v4-autonomous-k2",
        "coder-v4-autonomous-sort",
        "coder-v4-autonomous-trigger-gating",
    }:
        axis = {
            "coder-v4-autonomous": "silo-backoff-magnitude",
            "coder-v4-autonomous-k2": "silo-backoff-magnitude",
            "coder-v4-autonomous-sort": "silo-writeset-sort",
            "coder-v4-autonomous-trigger-gating": "silo-backoff-trigger-gating",
        }[spec.name]
        _planner_direction(data.get("planner_direction"), axis=axis,
                           path="input.planner_direction")
    elif spec.name in {"coder-v4-autonomous-policy", "coder-v4-autonomous-policy-ir"}:
        # 入力の5必須keyと任意診断はclosed schemaが検査する。自由文はopaque。
        pass
    elif spec.name == "critic-experiment":
        candidates = _array(data.get("unevaluated_candidates"),
                            "input.unevaluated_candidates")
        trajectory = _array(data.get("trajectory"), "input.trajectory")
        for path, labels in (("input.unevaluated_candidates", candidates),
                             ("input.trajectory", trajectory)):
            if not all(isinstance(label, str) and _GENOME_RE.fullmatch(label)
                       for label in labels):
                raise RolePolicyError(f"{path}: genome label形式違反")
            if len(labels) != len(set(labels)):
                raise RolePolicyError(f"{path}: genome label重複")
        overlap = set(candidates) & set(trajectory)
        if overlap:
            raise RolePolicyError(
                f"critic-experiment: evaluated/unevaluated候補が重複: {sorted(overlap)}"
            )
    elif spec.name == "profiler":
        if data.get("certified") is not True:
            raise RolePolicyError("profiler input.certifiedはtrue固定")
        screening = _mapping(data.get("screening"), "input.screening")
        if screening.get("passed") is not True:
            raise RolePolicyError("profiler input.screening.passedはtrue固定")
    elif spec.name == "selector-8b":
        candidates = _array(data.get("candidates"), "input.candidates")
        observed = []
        for index, raw in enumerate(candidates):
            candidate = _mapping(raw, f"input.candidates[{index}]")
            if set(candidate) != {"choice_id", "mechanism"}:
                raise RolePolicyError(
                    f"input.candidates[{index}]はchoice_id/mechanismだけを持つ"
                )
            observed.append((candidate.get("choice_id"), candidate.get("mechanism")))
        if tuple(observed) != _SELECTOR_8B_CANDIDATES:
            raise RolePolicyError("selector-8b candidatesが固定catalogと逐語一致しない")
    elif spec.name == "verifier":
        trusted = _mapping(data.get("verification_result"),
                           "input.verification_result")
        _verifier_invariants(trusted, "input.verification_result")


def validate_output_semantics(role: Any, projected_input: Any, result: Any) -> None:
    """logical schema検証済みresultのcross-field/input不変条件を検証する。"""

    spec = _resolve_role(role)
    validate_input_semantics(spec, projected_input)
    data = _mapping(projected_input, "input")
    output = _mapping(result, "result")

    if spec.name == "auditor":
        if output.get("diff_digest") != data.get("diff_digest"):
            raise RolePolicyError("auditor result.diff_digestがtrusted inputから変化した")
        violations = _array(output.get("violations"), "result.violations")
        nits = _array(output.get("nits"), "result.nits")
        proposed_tests = _array(
            output.get("proposed_tests"), "result.proposed_tests"
        )
        for path, values in (
            ("result.violations", violations),
            ("result.nits", nits),
            ("result.proposed_tests", proposed_tests),
        ):
            for index, value in enumerate(values):
                _mapping(value, f"{path}[{index}]")
        verdict = output.get("verdict")
        uncertainty = output.get("uncertainty")
        if not isinstance(uncertainty, str):
            raise RolePolicyError("auditor result.uncertaintyはstring")
        if verdict == "pass":
            if violations:
                raise RolePolicyError("auditor passはviolations空固定")
        elif verdict == "reject":
            if not violations:
                raise RolePolicyError("auditor rejectはviolations 1件以上が必要")
        elif verdict == "uncertain":
            if violations or not uncertainty.strip():
                raise RolePolicyError(
                    "auditor uncertainはviolations空かつnonempty uncertaintyが必要"
                )
        else:
            raise RolePolicyError("auditor verdictはpass|reject|uncertain")
    elif spec.name == "axis-proposer":
        proposals = _array(output.get("proposals"), "result.proposals")
        if not 1 <= len(proposals) <= 3:
            raise RolePolicyError("axis-proposer proposalsは1..3件")
        directive = data.get("hole_region_directive")
        stock_by_region = _axis_source_map(data)
        for index, proposal_value in enumerate(proposals):
            proposal = _mapping(proposal_value, f"result.proposals[{index}]")
            _enum(proposal.get("mutation_type"),
                  frozenset({"scalar", "code_fragment"}),
                  f"result.proposals[{index}].mutation_type")
            hole = _mapping(proposal.get("hole_location"),
                            f"result.proposals[{index}].hole_location")
            region = hole.get("region")
            if region not in stock_by_region:
                raise RolePolicyError(
                    f"result.proposals[{index}].hole_location.regionが編集面地図に無い"
                )
            if hole.get("source_rel") != stock_by_region[region]:
                raise RolePolicyError(
                    f"result.proposals[{index}].hole_location.source_relがstock抜粋と不一致"
                )
            if directive is not None and region != directive:
                raise RolePolicyError(
                    f"result.proposals[{index}].hole_location.regionがdirectiveと不一致"
                )
    elif spec.name == "calibrator":
        selected = output.get("selected_records")
        if isinstance(selected, bool) or not isinstance(selected, int) or selected < 1:
            raise RolePolicyError("calibrator selected_recordsは1以上のinteger")
        measured = {
            item["records"] for item in data["measurements"]
        }
        if selected not in measured:
            raise RolePolicyError(
                "calibrator selected_recordsはinput.measurements recordsのmemberでなければならない"
            )
    elif spec.name in {"coder-v4-autonomous-policy", "coder-v4-autonomous-policy-ir"}:
        proposal = _mapping(output.get("proposal"), "result.proposal")
        if proposal.get("axis") != "silo-function-policy":
            raise RolePolicyError("result.proposal.axis: 'silo-function-policy'固定")
        _enum(proposal.get("confidence"), _CONFIDENCE,
              "result.proposal.confidence")
    elif spec.name == "planner-v4":
        proposal = _mapping(output.get("proposal"), "result.proposal")
        _planner_direction(proposal, axis="silo-backoff-magnitude",
                           path="result.proposal")
    elif spec.name in {
        "coder-v4-autonomous",
        "coder-v4-autonomous-k2",
        "coder-v4-autonomous-sort",
        "coder-v4-autonomous-trigger-gating",
    }:
        axis = {
            "coder-v4-autonomous": "silo-backoff-magnitude",
            "coder-v4-autonomous-k2": "silo-backoff-magnitude",
            "coder-v4-autonomous-sort": "silo-writeset-sort",
            "coder-v4-autonomous-trigger-gating": "silo-backoff-trigger-gating",
        }[spec.name]
        proposal = _mapping(output.get("proposal"), "result.proposal")
        if proposal.get("axis") != axis:
            raise RolePolicyError(f"result.proposal.axis: {axis!r}固定")
        _enum(proposal.get("confidence"), _CONFIDENCE,
              "result.proposal.confidence")
        if spec.name in {"coder-v4-autonomous", "coder-v4-autonomous-k2"}:
            value = proposal.get("value")
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or not 1 <= value <= 1000):
                raise RolePolicyError("result.proposal.valueは1..1000の有限数")
            # K2 は p3_s4_loop の明示 role consumer からも到達する。その他の
            # role は従来どおり dormant adapter parity と各 loop consumer が強制点である。
            implementation = proposal.get("implementation")
            decision = backoff_hole_grammar.validate_backoff_implementation(
                implementation
            )
            if not decision.accepted:
                raise RolePolicyError(
                    f"{spec.name} implementationは固定backoff文法に不適合"
                )
            try:
                assigned, assigned_value, _literal_values = (
                    backoff_hole_grammar.attribution_numeric_literals(
                        implementation
                    )
                )
            except Exception:
                raise RolePolicyError(
                    f"{spec.name} implementationとvalueの数値一致を確認できない"
                ) from None
            if not assigned or assigned_value != value:
                raise RolePolicyError(
                    f"{spec.name} implementationとvalueの数値一致を確認できない"
                )
            if spec.name == "coder-v4-autonomous-k2":
                knowledge_input = _mapping(
                    data.get("knowledge_input"), "input.knowledge_input"
                )
                sources = _array(
                    knowledge_input.get("sources"),
                    "input.knowledge_input.sources",
                )
                knowledge_use = _array(
                    output.get("knowledge_use"), "result.knowledge_use"
                )
                seen_source_indexes: set[int] = set()
                for index, raw in enumerate(knowledge_use):
                    item = _mapping(raw, f"result.knowledge_use[{index}]")
                    source_index = item.get("source_index")
                    if (isinstance(source_index, bool)
                            or not isinstance(source_index, int)
                            or not 0 <= source_index < len(sources)):
                        raise RolePolicyError(
                            f"result.knowledge_use[{index}].source_indexは"
                            "input.knowledge_input.sourcesの有効indexでなければならない"
                        )
                    if source_index in seen_source_indexes:
                        raise RolePolicyError(
                            "result.knowledge_use.source_indexは重複禁止"
                        )
                    seen_source_indexes.add(source_index)
        elif spec.name == "coder-v4-autonomous-trigger-gating":
            expected = {"axis", "wire", "justification", "confidence"}
            if set(proposal) != expected:
                raise RolePolicyError(
                    "result.proposalはaxis/wire/justification/confidenceだけを持つ"
                )
            wire = proposal.get("wire")
            if (not isinstance(wire, str)
                    or _TRIGGER_GATE_WIRE_RE.fullmatch(wire) is None):
                raise RolePolicyError(
                    "result.proposal.wireは0|1だけからなる5文字でなければならない"
                )
    elif spec.name == "critic-experiment":
        action = output.get("action")
        genome = output.get("genome")
        if action == "evaluate":
            candidates = data.get("unevaluated_candidates")
            if not isinstance(genome, str) or genome not in candidates:
                raise RolePolicyError(
                    "critic-experiment evaluateは未評価候補内のnon-null genomeが必要"
                )
        elif action == "stop":
            if genome is not None:
                raise RolePolicyError("critic-experiment stopのgenomeはnull固定")
        else:
            raise RolePolicyError("critic-experiment actionはevaluate|stop")
    elif spec.name == "selector-8b":
        candidate_ids = {candidate["choice_id"] for candidate in data["candidates"]}
        if output.get("choice_id") not in candidate_ids:
            raise RolePolicyError("selector-8b choice_idが入力catalogにない")
        rationale = output.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            raise RolePolicyError("selector-8b rationaleは空でないstringが必要")
    elif spec.name == "verifier":
        trusted = _mapping(data.get("verification_result"),
                           "input.verification_result")
        _verifier_invariants(output, "result")
        for field in (
            "verdict", "certified", "serializable", "stats", "total_cycles",
            "anomalies", "integrity",
        ):
            if output.get(field) != trusted.get(field):
                raise RolePolicyError(
                    f"verifier result.{field}がtrusted verification_resultから変化した"
                )


__all__ = [
    "OPAQUE_STRING_POLICY",
    "OPEN_SUBTREE_POLICY",
    "POLICY_VERSION",
    "ROLE_FORBIDDEN_KEY_TOKENS",
    "TRIGGER_GATE_SEMANTIC_LITERAL",
    "RolePolicyError",
    "find_forbidden_keys",
    "validate_input_semantics",
    "validate_output_semantics",
]
