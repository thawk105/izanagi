# -*- coding: utf-8 -*-
"""Codex native 0 / non-native projection adapter 16 のfail-closedテスト。"""
from __future__ import annotations

import importlib.util
import copy
import hashlib
import json
import re
import shutil
import sys
import tempfile
from contextlib import contextmanager, redirect_stderr
from dataclasses import replace
from io import StringIO
from pathlib import Path

import jsonschema
import pytest

_REPO = Path(__file__).resolve().parents[2]
_CHECKER = _REPO / "tools" / "check_codex_agents.py"
_SPEC = importlib.util.spec_from_file_location("check_codex_agents", _CHECKER)
assert _SPEC and _SPEC.loader
CCA = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = CCA
_SPEC.loader.exec_module(CCA)

from orchestrator.codex_roles import policy as ROLE_POLICY  # noqa: E402
from orchestrator.codex_roles.review_ledger import (  # noqa: E402
    DEVELOPER_INSTRUCTION_TEMPLATE_SHA256,
    DESCRIPTION_SHA256,
    ROLE_IO_CONTRACTS,
    ROLE_MANIFEST_SHA256,
    SCHEMA_SHA256,
    SOURCE_FILE_SHA256,
)


def _fixture() -> Path:
    root = Path(tempfile.mkdtemp(prefix="izanagi-codex-agents-"))
    shutil.copytree(_REPO / ".claude" / "agents", root / ".claude" / "agents")
    shutil.copytree(
        _REPO / ".codex" / "role-adapters", root / ".codex" / "role-adapters"
    )
    (root / ".codex" / "agents").mkdir(parents=True)
    shutil.copytree(
        _REPO / "orchestrator" / "codex_roles", root / "orchestrator" / "codex_roles"
    )
    campaign = root / "orchestrator" / "campaign"
    campaign.mkdir(parents=True)
    shutil.copy2(
        _REPO / "orchestrator" / "campaign" / "auditor_gate.py",
        campaign / "auditor_gate.py",
    )
    shutil.copy2(
        _REPO / "orchestrator" / "campaign" / "p3_s4_loop.py",
        campaign / "p3_s4_loop.py",
    )
    return root


def _manifest(root: Path) -> dict:
    return json.loads(
        (root / "orchestrator" / "codex_roles" / "manifest.json").read_text(encoding="utf-8")
    )


def _write_manifest(root: Path, value: dict) -> None:
    (root / "orchestrator" / "codex_roles" / "manifest.json").write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


_TRIGGER_GATE_LITERAL_PREFIX = "trigger-gating-semantic/v1="


def _extract_trigger_gate_literal(text: str) -> dict:
    assert text.count(_TRIGGER_GATE_LITERAL_PREFIX) == 1
    payload = text.split(_TRIGGER_GATE_LITERAL_PREFIX, 1)[1]
    value, end = json.JSONDecoder().raw_decode(payload)
    assert end == len(payload) or payload[end] in {"。", "\n"}
    assert isinstance(value, dict)
    return value


def _extract_trigger_gate_agent_semantics(text: str) -> dict:
    section = text.split("## 合成対象と制約", 1)[1].split("\n---", 1)[0]
    bit_rows = re.findall(r"^- bit ([0-4]): `([^`]+)`$", section, re.MULTILINE)
    assert [int(bit) for bit, _ in bit_rows] == list(range(5))
    assert re.search(
        r"`1` はその要因で backoff する、`0` は backoff を\s+skip する",
        section,
    )
    assert "`kUnset` fail-safe は凍結 emitter の専権です。" in section
    assert "emitter が常に `kUnset=true` を正準述語へ付加します。" in section
    return {
        "bit_order_lsb_first": [reason for _, reason in bit_rows],
        "wire_value_meaning": {"0": "skip", "1": "backoff"},
        "kUnset": {
            "owner": "emitter",
            "always_true": True,
            "meaning": "backoff",
        },
    }


@contextmanager
def _reviewed_role_entry(root: Path, role: str):
    """test内だけfull role pinを明示更新し、その先の独立gateを検査する。"""

    old_pin = ROLE_MANIFEST_SHA256[role]
    ROLE_MANIFEST_SHA256[role] = _canonical_sha256(_manifest(root)["roles"][role])
    try:
        yield
    finally:
        ROLE_MANIFEST_SHA256[role] = old_pin


def test_policy_has_zero_native_and_sixteen_static_dormant_adapters():
    assert CCA.ACTIVE == {}
    assert len(CCA.STATIC_ADAPTERS) == 16
    assert CCA.STATIC_ADAPTERS == frozenset(CCA.ROLE_SPEC.load_role_specs(_REPO))


def test_review_ledger_independently_pins_all_sixteen_sources_and_io_contracts():
    specs = CCA.ROLE_SPEC.load_role_specs(_REPO)
    roles = set(specs)
    assert len(roles) == 16
    assert roles == set(SOURCE_FILE_SHA256)
    assert roles == set(DESCRIPTION_SHA256)
    assert roles == set(SCHEMA_SHA256)
    assert roles == set(ROLE_IO_CONTRACTS)
    assert roles == set(ROLE_MANIFEST_SHA256)
    assert hashlib.sha256(
        CCA.ROLE_SPEC.DEVELOPER_INSTRUCTION_TEMPLATE.encode("utf-8")
    ).hexdigest() == DEVELOPER_INSTRUCTION_TEMPLATE_SHA256
    for role, spec in specs.items():
        assert hashlib.sha256(spec.source.path.read_bytes()).hexdigest() == (
            SOURCE_FILE_SHA256[role]
        )
        assert hashlib.sha256(spec.description.encode("utf-8")).hexdigest() == (
            DESCRIPTION_SHA256[role]
        )
        assert _canonical_sha256(spec.input_schema) == SCHEMA_SHA256[role]["input"]
        assert _canonical_sha256(spec.output_schema) == SCHEMA_SHA256[role]["output"]
        assert _canonical_sha256(
            _manifest(_REPO)["roles"][role]
        ) == ROLE_MANIFEST_SHA256[role]
        contract = ROLE_IO_CONTRACTS[role]
        assert tuple(spec.input_schema["required"]) == contract["input_required_fields"]
        assert tuple(spec.output_schema["required"]) == contract["output_required_fields"]
        assert contract["mode"] == (
            "direct-json-example" if not spec.claude_tools else "mediated-override"
        )


def test_policy_coder_roles_have_closed_five_key_input_and_proposal_only_output():
    roles = CCA.ROLE_SPEC.load_role_specs(_REPO)
    required = ("leakproof_context", "policy_spec", "baseline",
                "recon_projection", "self_history")
    for name, payload in (
        ("coder-v4-autonomous-policy", "implementation"),
        ("coder-v4-autonomous-policy-ir", "ir"),
    ):
        role = roles[name]
        assert role.claude_tools == ()
        assert tuple(role.input_schema["required"]) == required
        assert role.input_schema["additionalProperties"] is False
        assert "critic_diagnosis" in role.input_schema["properties"]
        assert tuple(role.output_schema["required"]) == ("proposal",)
        proposal = role.output_schema["properties"]["proposal"]
        assert set(proposal["required"]) == {
            "axis", payload, "justification", "confidence"
        }
        assert proposal["additionalProperties"] is False
        assert role.consumer is None


def test_current_sources_render_byte_exact_and_native_is_empty():
    assert CCA.check(_REPO) == []
    assert list((_REPO / ".codex" / "agents").glob("*.toml")) == []


def test_all_adapters_pin_model_policy_and_blocked_runtime_activation():
    specs = CCA.ROLE_SPEC.load_role_specs(_REPO)
    for role, spec in specs.items():
        adapter = CCA.ROLE_SPEC.load_json_strict(
            _REPO / ".codex" / "role-adapters" / f"{role}.json"
        )
        assert adapter["model"] == spec.codex_model
        assert adapter["model_reasoning_effort"] == spec.codex_reasoning_effort
        assert adapter["mode"] == "static-dormant"
        assert adapter["runtime_boundary"] == "static-only-runtime-blocked"
        assert adapter["runtime_activation"] == {
            "status": "blocked",
            "reason": "uncontrollable_additional_tools",
            "uncontrollable_surface": "input.additional_tools",
            "evidence_owner": "runtime-launcher-additional-tools-attestation",
        }
        contract = ROLE_IO_CONTRACTS[role]
        assert adapter["review_ledger"] == {
            "role_manifest_sha256": ROLE_MANIFEST_SHA256[role],
            "developer_instruction_template_sha256": (
                DEVELOPER_INSTRUCTION_TEMPLATE_SHA256
            ),
            "source_file_sha256": SOURCE_FILE_SHA256[role],
            "description_sha256": DESCRIPTION_SHA256[role],
            "input_schema_sha256": SCHEMA_SHA256[role]["input"],
            "output_schema_sha256": SCHEMA_SHA256[role]["output"],
            "io_contract": {
                "mode": contract["mode"],
                "input_required_fields": list(contract["input_required_fields"]),
                "output_required_fields": list(contract["output_required_fields"]),
                "source_obligations": contract["source_obligations"],
            },
        }
        assert not ({"wire_contract", "wire_tools_attested_by", "capabilities"} & adapter.keys())
        assert adapter["input_policy"] == {
            "version": "izanagi.codex-role-policy/v1",
            "recursive_forbidden_key_tokens": list(spec.forbidden_key_tokens),
            "opaque_string_content": "trusted-projection-producer-responsibility",
            "open_object_subtrees": "trusted-projection-producer-responsibility",
        }
        if spec.consumer is None:
            assert adapter["consumer_contract"] == {
                "use": "standalone-typed-proposal-only",
                "status": "trusted-integration-unwired",
            }
        else:
            assert adapter["consumer_contract"] == {
                "use": "trusted-integration",
                "status": "trusted-parser-wired",
            }


def test_source_body_is_embedded_exactly_once_before_product_override():
    for role, spec in CCA.ROLE_SPEC.load_role_specs(_REPO).items():
        adapter = CCA.ROLE_SPEC.load_json_strict(
            _REPO / ".codex" / "role-adapters" / f"{role}.json"
        )
        instructions = adapter["developer_instructions"]
        assert instructions.count(spec.source.body) == 1
        assert instructions.index(spec.source.body) < instructions.index(
            "<<<CODEX_PRODUCT_OVERRIDE_BEGIN>>>"
        )
        override = instructions.split("<<<CODEX_PRODUCT_OVERRIDE_BEGIN>>>", 1)[1]
        assert "tool使用、repository探索、実行loop、write/edit命令" in override
        assert "trusted projection/driverへlower済み" in override
        assert "adapter logical schemaを優先" in override
        assert "schemaが許すunknown/unknowns/uncertainty/confidenceへ" in override


def test_claude_tool_capabilities_are_lowered_without_runtime_tool_claim():
    specs = CCA.ROLE_SPEC.load_role_specs(_REPO)
    for role, spec in specs.items():
        assert set(spec.capability_mapping) == set(spec.claude_tools)
        assert spec.semantic_projection_mode == (
            "direct-projection" if not spec.claude_tools else "mediated-projection"
        )
        adapter = CCA.ROLE_SPEC.load_json_strict(
            _REPO / ".codex" / "role-adapters" / f"{role}.json"
        )
        assert "capabilities" not in adapter
        assert "wire_contract" not in adapter
        assert adapter["semantic_projection_mode"] == spec.semantic_projection_mode
        assert adapter["semantic_projection_mode_semantics"] == (
            "tool-lowering-classification-only; "
            "does-not-prove-semantic-equivalence-or-consumer-wiring"
        )


def test_any_native_discovery_toml_is_rejected():
    root = _fixture()
    try:
        for name in ("auditor.toml", "planner-v4.toml", "mystery.toml"):
            (root / ".codex" / "agents" / name).write_text(
                "not even valid TOML\n", encoding="utf-8"
            )
        findings = CCA.check(root)
        assert len(findings) == 3
        assert all("native discovery profileは禁止" in finding for finding in findings)
    finally:
        shutil.rmtree(root)


def test_project_config_native_role_is_rejected_and_globals_are_allowed():
    root = _fixture()
    try:
        config = root / ".codex" / "config.toml"
        config.write_text(
            "[agents]\nmax_threads = 4\nmax_depth = 1\ninterrupt_message = true\n",
            encoding="utf-8",
        )
        assert CCA.check(root) == []
        config.write_text(
            "[agents]\nmax_threads = 4\n\n"
            "[agents.auditor]\n"
            'description = "forbidden native role"\n'
            'config_file = "./custom/auditor.toml"\n',
            encoding="utf-8",
        )
        findings = CCA.check(root)
        assert len(findings) == 1
        assert "native discovery agent role 'auditor'は禁止" in findings[0]
        config.write_text("[agents\n", encoding="utf-8")
        assert any("TOML parse 失敗" in finding for finding in CCA.check(root))
    finally:
        shutil.rmtree(root)


def test_write_mode_does_not_create_native_or_adapter_files():
    root = _fixture()
    try:
        before = sorted(str(path.relative_to(root)) for path in root.rglob("*"))
        stderr = StringIO()
        with redirect_stderr(stderr):
            result = CCA.main(["--write", "--root", str(root)])
        after = sorted(str(path.relative_to(root)) for path in root.rglob("*"))
        assert result == 1
        assert "--write" in stderr.getvalue()
        assert before == after
    finally:
        shutil.rmtree(root)


def test_adapter_inventory_missing_extra_and_symlink_are_rejected():
    for mode in ("missing", "extra", "symlink"):
        root = _fixture()
        try:
            adapter_dir = root / ".codex" / "role-adapters"
            if mode == "missing":
                (adapter_dir / "auditor.json").unlink()
            elif mode == "extra":
                (adapter_dir / "mystery.json").write_text("{}\n", encoding="utf-8")
            else:
                target = adapter_dir / "auditor.json"
                target.unlink()
                target.symlink_to(adapter_dir / "critic.json")
            assert any("adapter inventory 不一致" in finding or "symlink" in finding
                       for finding in CCA.check(root))
        finally:
            shutil.rmtree(root)


def test_adapter_byte_drift_and_runtime_claim_injection_are_rejected():
    root = _fixture()
    try:
        path = root / ".codex" / "role-adapters" / "auditor.json"
        adapter = json.loads(path.read_text(encoding="utf-8"))
        adapter["wire_contract"] = {"wire_tools": []}
        path.write_text(json.dumps(adapter, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
        assert any("byte parity drift" in finding for finding in CCA.check(root))
    finally:
        shutil.rmtree(root)


def test_claude_body_or_description_drift_requires_independent_ledger_review():
    for mutation in ("body", "description"):
        root = _fixture()
        try:
            path = root / ".claude" / "agents" / "auditor.md"
            text = path.read_text(encoding="utf-8")
            if mutation == "body":
                text += "\nBODY-DRIFT-SENTINEL\n"
            else:
                line = next(v for v in text.splitlines() if v.startswith("description: "))
                text = text.replace(line, 'description: "meaning changed"', 1)
            path.write_text(text, encoding="utf-8")
            if mutation == "body":
                findings = CCA.check(root)
                expected = "SOURCE_FILE_SHA256 drift"
            else:
                # file全体pinだけをreview済み相当に差し替えても、description固有pinが赤になる。
                old_pin = SOURCE_FILE_SHA256["auditor"]
                SOURCE_FILE_SHA256["auditor"] = hashlib.sha256(path.read_bytes()).hexdigest()
                try:
                    findings = CCA.check(root)
                finally:
                    SOURCE_FILE_SHA256["auditor"] = old_pin
                expected = "description SHA256 drift"
            assert any(expected in finding for finding in findings)
        finally:
            shutil.rmtree(root)


def test_claude_tools_model_and_effort_must_match_manifest():
    cases = (
        ("auditor", 'tools: ["Read", "Grep", "Glob"]', "tools: []"),
        ("planner-v4", "model: opus", "model: sonnet"),
        ("critic-experiment", "effort: high", "effort: medium"),
    )
    for role, old, new in cases:
        root = _fixture()
        try:
            path = root / ".claude" / "agents" / f"{role}.md"
            text = path.read_text(encoding="utf-8")
            assert old in text
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            old_pin = SOURCE_FILE_SHA256[role]
            SOURCE_FILE_SHA256[role] = hashlib.sha256(path.read_bytes()).hexdigest()
            try:
                findings = CCA.check(root)
            finally:
                SOURCE_FILE_SHA256[role] = old_pin
            assert any("Claude source contract drift" in finding for finding in findings)
        finally:
            shutil.rmtree(root)


def test_unquoted_and_leading_hash_description_are_rejected():
    for replacement in (
        "description: plain",
        "description: #if hidden-by-yaml",
        "description: visible #then-hidden-by-yaml",
    ):
        root = _fixture()
        try:
            path = root / ".claude" / "agents" / "coder.md"
            text = path.read_text(encoding="utf-8")
            line = next(v for v in text.splitlines() if v.startswith("description: "))
            path.write_text(text.replace(line, replacement, 1), encoding="utf-8")
            assert any("JSON quoted string" in finding for finding in CCA.check(root))
        finally:
            shutil.rmtree(root)


def test_manifest_and_claude_role_inventory_must_be_bijective():
    root = _fixture()
    try:
        (root / ".claude" / "agents" / "new-role.md").write_text(
            '---\nname: new-role\ndescription: "test"\ntools: []\n'
            "model: opus\neffort: high\n---\n\nbody\n",
            encoding="utf-8",
        )
        assert any("role inventory 不一致" in finding for finding in CCA.check(root))
    finally:
        shutil.rmtree(root)


def test_capability_mapping_omission_and_wrong_lowering_are_rejected():
    for mutation in ("missing", "wrong"):
        root = _fixture()
        try:
            manifest = _manifest(root)
            mapping = manifest["roles"]["auditor"]["capability_mapping"]
            if mutation == "missing":
                mapping.pop("Read")
            else:
                mapping["Read"] = "shell"
            _write_manifest(root, manifest)
            with _reviewed_role_entry(root, "auditor"):
                assert any(
                    "capability_mapping" in finding for finding in CCA.check(root)
                )
        finally:
            shutil.rmtree(root)


def test_codex_model_and_effort_cannot_be_omitted_or_inherited():
    for mutation in ("missing", "unknown", "opus-terra"):
        root = _fixture()
        try:
            manifest = _manifest(root)
            codex = manifest["roles"]["auditor"]["codex"]
            if mutation == "missing":
                codex.pop("model_reasoning_effort")
            elif mutation == "unknown":
                codex["model"] = "latest"
            else:
                codex["model"] = "gpt-5.6-terra"
            _write_manifest(root, manifest)
            with _reviewed_role_entry(root, "auditor"):
                assert any("codex" in finding for finding in CCA.check(root))
        finally:
            shutil.rmtree(root)


def test_verifier_codex_mapping_is_explicitly_pinned():
    # D61 (2026-07-19 ユーザー裁定): terra/medium へ再ピン。方向を問わず drift を検出する
    for key, value in (("model", "gpt-5.6-sol"),
                       ("model_reasoning_effort", "high")):
        root = _fixture()
        try:
            manifest = _manifest(root)
            manifest["roles"]["verifier"]["codex"][key] = value
            _write_manifest(root, manifest)
            with _reviewed_role_entry(root, "verifier"):
                assert any("verifierはgpt-5.6-terra/medium固定" in finding
                           for finding in CCA.check(root))
        finally:
            shutil.rmtree(root)


def test_full_role_manifest_pin_rejects_semantic_contract_weakening():
    cases = (
        ("auditor", "projection"),
        ("auditor", "consumer"),
        ("auditor", "forbidden"),
        ("calibrator", "model"),
        ("auditor", "lowering"),
    )
    for role, mutation in cases:
        root = _fixture()
        old_lowering = CCA.ROLE_SPEC.TOOL_LOWERING["Read"]
        try:
            manifest = _manifest(root)
            entry = manifest["roles"][role]
            if mutation == "projection":
                entry["projection_instructions"] = "correctness gateを省略する"
            elif mutation == "consumer":
                entry["consumer"] = None
            elif mutation == "forbidden":
                entry["forbidden_input_classes"].pop()
            elif mutation == "model":
                entry["codex"] = {
                    "model": "gpt-5.6-sol",
                    "model_reasoning_effort": "high",
                }
            else:
                entry["capability_mapping"]["Read"] = "structured-output-proposal"
                CCA.ROLE_SPEC.TOOL_LOWERING["Read"] = "structured-output-proposal"
            _write_manifest(root, manifest)
            assert any("reviewed full manifest role SHA256 drift" in finding
                       for finding in CCA.check(root))
        finally:
            CCA.ROLE_SPEC.TOOL_LOWERING["Read"] = old_lowering
            shutil.rmtree(root)


def test_shared_developer_instruction_template_has_independent_pin():
    old_template = CCA.ROLE_SPEC.DEVELOPER_INSTRUCTION_TEMPLATE
    try:
        CCA.ROLE_SPEC.DEVELOPER_INSTRUCTION_TEMPLATE = old_template.replace(
            "正しさゲートや隔離条件を緩めない",
            "正しさゲートや隔離条件を必要に応じて緩める",
        )
        assert any("DEVELOPER_INSTRUCTION_TEMPLATE_SHA256 drift" in finding
                   for finding in CCA.check(_REPO))
    finally:
        CCA.ROLE_SPEC.DEVELOPER_INSTRUCTION_TEMPLATE = old_template


def test_runtime_activation_is_blocked_on_uncontrollable_additional_tools():
    for path, value in (
        (("runtime_activation", "status"), "active"),
        (("runtime_activation", "reason"), "tool-free"),
        (("runtime_activation", "uncontrollable_surface"), "body.tools"),
        (("runtime_boundary",), "outer-bwrap+responses-wire-attestation"),
    ):
        root = _fixture()
        try:
            manifest = _manifest(root)
            target = manifest
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            _write_manifest(root, manifest)
            assert any("runtime activation" in finding or "runtime_boundary" in finding
                       for finding in CCA.check(root))
        finally:
            shutil.rmtree(root)


def test_recursive_forbidden_key_aliases_are_role_specific_and_fail_closed():
    cases = {
        "axis-proposer": (
            "winner_value", "winner_values", "winner", "winners", "recommend",
            "recommendation", "recommendations", "ranking", "rankings",
            "candidate_rankings", "critic_recommendation", "critic_recommendations",
            "dead_axis_attributions", "performance_hint", "performance_hints",
        ),
        "auditor": (
            "wal", "wals", "history", "histories", "median_tps",
            "leading_indicator", "leading_indicators",
            "winning_mechanism", "winning_mechanisms",
        ),
        "coder-v4-autonomous": (
            "winner", "winners", "ranking", "rankings", "candidate_rankings",
            "unevaluated_performance", "unevaluated_performances",
            "optimal_mechanism", "optimal_mechanisms",
        ),
        "coder-v4-autonomous-policy": ("winning_policy", "winners", "candidate_rankings", "optimal_mechanisms"),
        "coder-v4-autonomous-policy-ir": ("winning_policy", "winners", "candidate_rankings", "optimal_mechanisms"),
        "coder-v4-autonomous-sort": (
            "winning_comparator", "winning_comparators", "winners",
            "candidate_rankings", "rankings", "optimal_mechanisms",
        ),
        "coder-v4-autonomous-trigger-gating": (
            "winning_gate", "winning_gates", "winners", "candidate_rankings",
            "rankings", "optimal_mechanisms",
        ),
        "critic-experiment": (
            "fitness", "winner", "winners", "winner_tied_sets", "arrival_verdict",
            "arrival_verdicts", "wal", "wals", "source_tree", "source_trees",
        ),
        "planner-v4": ("winner_values", "winners", "grid_optima", "source_trees"),
        "calibrator": ("trace_enabled", "campaign_fitness", "between_run_floor"),
        "profiler": ("trace_enabled", "concurrent_benchmarks"),
        "verifier": (
            "throughputs", "fitnesses", "expected_verdicts", "winners",
            "implementation_fix_requests",
        ),
    }
    for role, aliases in cases.items():
        for alias in aliases:
            try:
                ROLE_POLICY.validate_input_semantics(
                    role, {"safe": [{"nested": {alias: "red"}}]}
                )
            except ROLE_POLICY.RolePolicyError as exc:
                assert "recursive forbidden key" in str(exc)
            else:
                raise AssertionError(f"{role}:{alias}を許可した")

    # tableに列挙した全tokenはnested/list内でも必ず拒否する。
    for role, tokens in ROLE_POLICY.ROLE_FORBIDDEN_KEY_TOKENS.items():
        for token in tokens:
            assert ROLE_POLICY.find_forbidden_keys(
                role, {"safe": [{"nested": {token: "red"}}]}
            )
    for role, alias in (
        ("axis-proposer", "candidateRankings"),
        ("coder-v4-autonomous-sort", "winningComparators"),
        ("verifier", "expectedVerdicts"),
    ):
        assert ROLE_POLICY.find_forbidden_keys(role, {alias: "red"})

    # calibratorの正規入力にあるthroughput系観測は一律禁止しない。
    ROLE_POLICY.validate_input_semantics(
        "calibrator",
        {
            "request": {},
            "measurements": [{"records": 1, "throughput_ops_sec": 123.0}],
        },
    )


def test_opaque_string_is_not_misrepresented_as_recursively_inspected():
    ROLE_POLICY.validate_input_semantics(
        "axis-proposer",
        {
            "diagnostics": {
                "opaque": "winner recommend ranking performance_hint"
            },
            "stock_excerpts": [
                {"region": "r", "source_rel": "src/x.cpp", "excerpt": "stock"}
            ],
            "edit_surface_map": [
                {"region": "r", "role": "neutral", "opened": False}
            ],
        },
    )
    spec = CCA.ROLE_SPEC.get_role_spec("axis-proposer")
    assert ROLE_POLICY.find_forbidden_keys(spec, {"opaque": "winner"}) == ()
    assert ROLE_POLICY.OPAQUE_STRING_POLICY == (
        "trusted-projection-producer-responsibility"
    )
    assert ROLE_POLICY.OPEN_SUBTREE_POLICY == (
        "trusted-projection-producer-responsibility"
    )


def test_selector_8b_policy_pins_catalog_order_and_nonempty_single_choice():
    projected = {
        "schema_version": "8b-selector-input/v1",
        "descriptor": {},
        "candidates": [
            {"choice_id": "c01", "mechanism": "protocol_flag_bundle"},
            {"choice_id": "c02", "mechanism": "fixed_abort_backoff"},
            {"choice_id": "c03", "mechanism": "write_set_ordering"},
            {"choice_id": "c04", "mechanism": "subset_abort_reason_gate"},
            {"choice_id": "c05", "mechanism": "all_abort_reason_gate"},
            {"choice_id": "c06", "mechanism": "upstream_defaults"},
        ],
    }
    output = {
        "schema_version": "8b-selector-output/v1",
        "choice_id": "c03",
        "rationale": "descriptor と機構の適合",
    }
    ROLE_POLICY.validate_input_semantics("selector-8b", projected)
    ROLE_POLICY.validate_output_semantics("selector-8b", projected, output)

    wrong_catalog = copy.deepcopy(projected)
    wrong_catalog["candidates"][0]["mechanism"] = "upstream_defaults"
    try:
        ROLE_POLICY.validate_input_semantics("selector-8b", wrong_catalog)
    except ROLE_POLICY.RolePolicyError as exc:
        assert "固定catalog" in str(exc)
    else:
        raise AssertionError("selector-8b catalog の対応ずれを許可した")

    try:
        ROLE_POLICY.validate_output_semantics(
            "selector-8b", projected, {**output, "rationale": " "}
        )
    except ROLE_POLICY.RolePolicyError as exc:
        assert "rationale" in str(exc)
    else:
        raise AssertionError("selector-8b の空 rationale を許可した")


def test_auditor_input_digest_is_sha256_of_utf8_working_diff():
    working_diff = "diff --git a/x b/x\n+日本語\n"
    digest = hashlib.sha256(working_diff.encode("utf-8")).hexdigest()
    projected = {"working_diff": working_diff, "diff_digest": digest}
    ROLE_POLICY.validate_input_semantics("auditor", projected)
    ROLE_POLICY.validate_output_semantics(
        "auditor",
        projected,
        {
            "verdict": "pass",
            "diff_digest": digest,
            "violations": [],
            "nits": [],
            "proposed_tests": [],
            "uncertainty": "",
        },
    )
    try:
        ROLE_POLICY.validate_input_semantics(
            "auditor", {"working_diff": working_diff, "diff_digest": "0" * 64}
        )
    except ROLE_POLICY.RolePolicyError as exc:
        assert "SHA-256" in str(exc)
    else:
        raise AssertionError("working_diffと不一致なdigestを許可した")


def test_auditor_output_verdict_and_structured_feedback_are_consistent():
    diff = "diff --git a/x b/x\n+x\n"
    digest = hashlib.sha256(diff.encode("utf-8")).hexdigest()
    projected = {"working_diff": diff, "diff_digest": digest}
    base = {
        "diff_digest": digest,
        "violations": [],
        "nits": [],
        "proposed_tests": [],
        "uncertainty": "",
    }
    valid = (
        {**base, "verdict": "pass"},
        {
            **base,
            "verdict": "reject",
            "violations": [{"type": 1, "reason": "correctness"}],
        },
        {**base, "verdict": "uncertain", "uncertainty": "insufficient evidence"},
    )
    for output in valid:
        ROLE_POLICY.validate_output_semantics("auditor", projected, output)

    invalid = (
        {**base, "verdict": "pass", "violations": [{"type": 1}]},
        {**base, "verdict": "reject"},
        {**base, "verdict": "uncertain", "uncertainty": "  "},
        {**base, "verdict": "uncertain", "uncertainty": "unknown",
         "violations": [{"type": 1}]},
        {**base, "verdict": "pass", "nits": [42]},
    )
    for output in invalid:
        try:
            ROLE_POLICY.validate_output_semantics("auditor", projected, output)
        except ROLE_POLICY.RolePolicyError:
            pass
        else:
            raise AssertionError(f"auditor出力矛盾を許可: {output!r}")


def test_calibrator_records_are_positive_unique_and_selected_from_measurements():
    schema = CCA.ROLE_SPEC.get_role_spec("calibrator").input_schema
    measurements_schema = schema["properties"]["measurements"]
    assert measurements_schema["minItems"] == 1
    assert measurements_schema["uniqueItems"] is True
    assert measurements_schema["items"]["properties"]["records"] == {
        "type": "integer",
        "minimum": 1,
    }

    valid_input = {
        "request": {"threads": 8},
        "measurements": [
            {"records": 1000, "miss_rate": 0.4},
            {"records": 2000, "miss_rate": 0.2},
        ],
    }
    ROLE_POLICY.validate_input_semantics("calibrator", valid_input)
    ROLE_POLICY.validate_output_semantics(
        "calibrator", valid_input, {"selected_records": 2000}
    )
    invalid_inputs = (
        {"request": {}, "measurements": []},
        {"request": {}, "measurements": [{"records": 0}]},
        {"request": {}, "measurements": [{"records": True}]},
        {
            "request": {},
            "measurements": [
                {"records": 1000, "miss_rate": 0.4},
                {"records": 1000, "miss_rate": 0.2},
            ],
        },
    )
    for projected in invalid_inputs:
        try:
            ROLE_POLICY.validate_input_semantics("calibrator", projected)
        except ROLE_POLICY.RolePolicyError:
            pass
        else:
            raise AssertionError(f"calibratorの不正measurementを許可: {projected!r}")
    for selected in (0, -1, True, 3000):
        try:
            ROLE_POLICY.validate_output_semantics(
                "calibrator", valid_input, {"selected_records": selected}
            )
        except ROLE_POLICY.RolePolicyError:
            pass
        else:
            raise AssertionError(
                f"calibratorの未測定/不正selected_recordsを許可: {selected!r}"
            )


def test_axis_planner_and_coder_semantic_policy_negative_cases():
    axis_input = {
        "diagnostics": {},
        "stock_excerpts": [
            {"region": "region-a", "source_rel": "src/a.cpp", "excerpt": "stock"}
        ],
        "edit_surface_map": [
            {"region": "region-a", "role": "neutral", "opened": False}
        ],
        "hole_region_directive": "region-a",
    }
    try:
        ROLE_POLICY.validate_output_semantics(
            "axis-proposer", axis_input, {"proposals": []}
        )
    except ROLE_POLICY.RolePolicyError as exc:
        assert "1..3" in str(exc)
    else:
        raise AssertionError("axis-proposerの空提案を許可した")

    unknown_region = {
        "proposals": [{
            "mutation_type": "scalar",
            "hole_location": {"region": "region-b", "source_rel": "src/b.cpp"},
        }]
    }
    try:
        ROLE_POLICY.validate_output_semantics("axis-proposer", axis_input, unknown_region)
    except ROLE_POLICY.RolePolicyError as exc:
        assert "編集面地図" in str(exc)
    else:
        raise AssertionError("編集面地図に無いregionを許可した")

    wrong_source = {
        "proposals": [{
            "mutation_type": "scalar",
            "hole_location": {"region": "region-a", "source_rel": "src/wrong.cpp"},
        }]
    }
    try:
        ROLE_POLICY.validate_output_semantics("axis-proposer", axis_input, wrong_source)
    except ROLE_POLICY.RolePolicyError as exc:
        assert "stock抜粋" in str(exc)
    else:
        raise AssertionError("regionと無関係なsource_relを許可した")

    invalid_axis_inputs = (
        {
            **axis_input,
            "stock_excerpts": axis_input["stock_excerpts"] * 2,
        },
        {
            **axis_input,
            "edit_surface_map": [
                {"region": "region-b", "role": "neutral", "opened": False}
            ],
            "hole_region_directive": None,
        },
        {**axis_input, "hole_region_directive": "region-missing"},
    )
    for invalid in invalid_axis_inputs:
        try:
            ROLE_POLICY.validate_input_semantics("axis-proposer", invalid)
        except ROLE_POLICY.RolePolicyError:
            pass
        else:
            raise AssertionError(f"axis projection不整合を許可: {invalid!r}")

    planner_input = {}
    planner_output = {
        "proposal": {
            "axis": "silo-backoff-magnitude",
            "direction": "sideways",
            "magnitude": "small",
        }
    }
    try:
        ROLE_POLICY.validate_output_semantics(
            "planner-v4", planner_input, planner_output
        )
    except ROLE_POLICY.RolePolicyError as exc:
        assert "direction" in str(exc)
    else:
        raise AssertionError("plannerの未知directionを許可した")

    coder_input = {
        "planner_direction": {
            "axis": "silo-backoff-magnitude",
            "direction": "increase",
            "magnitude": "small",
        }
    }
    for field, value in (("value", 0), ("value", 1001), ("confidence", "certain")):
        proposal = {
            "axis": "silo-backoff-magnitude",
            "value": 50,
            "confidence": "medium",
        }
        proposal[field] = value
        try:
            ROLE_POLICY.validate_output_semantics(
                "coder-v4-autonomous", coder_input, {"proposal": proposal}
            )
        except ROLE_POLICY.RolePolicyError:
            pass
        else:
            raise AssertionError(f"coder-v4の不正{field}={value!r}を許可した")


def test_coder_v4_output_semantics_requires_literal_only_single_statement_value_match():
    projected = {
        "planner_direction": {
            "axis": "silo-backoff-magnitude",
            "direction": "increase",
            "magnitude": "small",
        }
    }
    proposal = {
        "axis": "silo-backoff-magnitude",
        "value": 20,
        "implementation": "double now_backoff = 20;",
        "justification": "fixture",
        "confidence": "medium",
    }
    sentinel = "SENTINEL_POLICY_CANDIDATE_65ad"
    invalid = (
        {**proposal, "implementation": "double now_backoff = (20.0);"},
        {**proposal, "implementation": "double now_backoff = 20.0f;"},
        {**proposal, "implementation": "double now_backoff = 20; helper();"},
        {**proposal, "implementation": "double now_backoff = 21;"},
        {**proposal, "implementation": f"double now_backoff = {sentinel};"},
    )
    for role in ("coder-v4-autonomous", "coder-v4-autonomous-k2"):
        role_input = projected
        result_extra = {}
        if role == "coder-v4-autonomous-k2":
            role_input = {
                **projected,
                "knowledge_input": {"sources": [{"content_utf8": "fixture"}]},
            }
            result_extra = {"knowledge_use": []}
        for implementation in (
            "double now_backoff = 20;",
            "double now_backoff = 20.0;",
        ):
            ROLE_POLICY.validate_output_semantics(
                role,
                role_input,
                {
                    "proposal": {**proposal, "implementation": implementation},
                    **result_extra,
                },
            )
        for candidate in invalid:
            with pytest.raises(ROLE_POLICY.RolePolicyError) as caught:
                ROLE_POLICY.validate_output_semantics(
                    role,
                    role_input,
                    {"proposal": candidate, **result_extra},
                )
            assert sentinel not in str(caught.value)
            assert candidate["implementation"] not in str(caught.value)


@pytest.mark.parametrize(
    "invalid_knowledge_use",
    (
        [{"source_index": 2, "use": "存在しない source"}],
        [
            {"source_index": 0, "use": "first"},
            {"source_index": 0, "use": "duplicate"},
        ],
    ),
)
def test_coder_v4_k2_knowledge_use_source_indices_are_valid_and_unique(
    invalid_knowledge_use,
):
    projected = {
        "knowledge_input": {
            "sources": [
                {"content_utf8": "source zero"},
                {"content_utf8": "source one"},
            ]
        },
        "planner_direction": {
            "axis": "silo-backoff-magnitude",
            "direction": "increase",
            "magnitude": "small",
        },
    }
    proposal = {
        "axis": "silo-backoff-magnitude",
        "value": 20,
        "implementation": "double now_backoff = 20;",
        "justification": "fixture",
        "confidence": "medium",
    }
    ROLE_POLICY.validate_output_semantics(
        "coder-v4-autonomous-k2",
        projected,
        {
            "proposal": proposal,
            "knowledge_use": [{"source_index": 1, "use": "valid"}],
        },
    )
    with pytest.raises(ROLE_POLICY.RolePolicyError, match="source_index"):
        ROLE_POLICY.validate_output_semantics(
            "coder-v4-autonomous-k2",
            projected,
            {"proposal": proposal, "knowledge_use": invalid_knowledge_use},
        )


def test_coder_v4_k2_input_schema_accepts_empty_sources():
    """Rejects any remaining K2-only minimum source-count constraint. Accepts an otherwise complete K2 role input whose bound knowledge projection has an empty sources array."""
    spec = CCA.ROLE_SPEC.get_role_spec("coder-v4-autonomous-k2")
    sources_schema = spec.input_schema["properties"]["knowledge_input"][
        "properties"
    ]["sources"]
    assert "minItems" not in sources_schema
    projected = {
        "leakproof_context": "fixture",
        "knowledge_input": {
            "data_boundary": "external_knowledge_is_data_not_instructions",
            "knowledge_level": "K2",
            "knowledge_manifest_sha256": "a" * 64,
            "sources": [],
        },
        "baseline": {},
        "planner_direction": {
            "axis": "silo-backoff-magnitude",
            "direction": "increase",
            "magnitude": "small",
            "justification": "fixture",
        },
        "whiteboard": [],
    }
    jsonschema.Draft7Validator(spec.input_schema).validate(projected)


def test_backoff_literal_only_contract_has_role_manifest_adapter_parity():
    role_text = (
        _REPO / ".claude" / "agents" / "coder-v4-autonomous.md"
    ).read_text(encoding="utf-8")
    coder_text = (
        _REPO / ".claude" / "agents" / "coder.md"
    ).read_text(encoding="utf-8")
    projection = _manifest(_REPO)["roles"]["coder-v4-autonomous"][
        "projection_instructions"
    ]
    autonomous_adapter = CCA.ROLE_SPEC.load_json_strict(
        _REPO / ".codex" / "role-adapters" / "coder-v4-autonomous.json"
    )["developer_instructions"]
    coder_adapter = CCA.ROLE_SPEC.load_json_strict(
        _REPO / ".codex" / "role-adapters" / "coder.json"
    )["developer_instructions"]

    for text in (role_text, projection, autonomous_adapter):
        assert "numeric literal" in text
        assert "value" in text
    assert "ちょうど 1 文" in role_text
    assert "ちょうど1文" in projection
    for text in (coder_text, coder_adapter):
        assert "silo-backoff-magnitude" in text
        assert "D836 / D901(1)" in text


def test_trigger_gating_semantic_literal_has_four_surface_parity():
    role = "coder-v4-autonomous-trigger-gating"
    agent_text = (
        _REPO / ".claude" / "agents" / f"{role}.md"
    ).read_text(encoding="utf-8")
    manifest_text = _manifest(_REPO)["roles"][role]["projection_instructions"]
    adapter = CCA.ROLE_SPEC.load_json_strict(
        _REPO / ".codex" / "role-adapters" / f"{role}.json"
    )
    instructions = adapter["developer_instructions"]
    override = instructions.split("<<<CODEX_PRODUCT_OVERRIDE_BEGIN>>>\n", 1)[1]
    override = override.split("\n<<<CODEX_PRODUCT_OVERRIDE_END>>>", 1)[0]

    expected = {
        "bit_order_lsb_first": [
            "lock-conflict",
            "update-absent",
            "readvali-tid",
            "readvali-locked",
            "node-vali",
        ],
        "wire_value_meaning": {"0": "skip", "1": "backoff"},
        "kUnset": {
            "owner": "emitter",
            "always_true": True,
            "meaning": "backoff",
        },
    }
    surfaces = {
        "agent": _extract_trigger_gate_agent_semantics(agent_text),
        "manifest": _extract_trigger_gate_literal(manifest_text),
        "adapter": _extract_trigger_gate_literal(override),
        "policy": _extract_trigger_gate_literal(
            ROLE_POLICY.TRIGGER_GATE_SEMANTIC_LITERAL
        ),
    }
    assert surfaces == {surface: expected for surface in surfaces}


def test_trigger_gating_output_semantics_require_exact_wire_and_reject_implementation():
    projected = {
        "leakproof_context": "context",
        "gating_spec": "spec",
        "baseline": {},
        "planner_direction": {
            "axis": "silo-backoff-trigger-gating",
            "direction": "explore_both",
            "magnitude": "small",
            "justification": "reason",
        },
        "whiteboard": [],
    }
    proposal = {
        "axis": "silo-backoff-trigger-gating",
        "wire": "10100",
        "justification": "reason",
        "confidence": "medium",
    }
    ROLE_POLICY.validate_output_semantics(
        "coder-v4-autonomous-trigger-gating", projected, {"proposal": proposal}
    )

    invalid_proposals = (
        {**proposal, "wire": "1010"},
        {**proposal, "wire": "1010x"},
        {**proposal, "wire": 10100},
        {
            key: value
            for key, value in {
                **proposal,
                "implementation": "izanagi_gate_pass = true;",
            }.items()
            if key != "wire"
        },
    )
    for invalid in invalid_proposals:
        try:
            ROLE_POLICY.validate_output_semantics(
                "coder-v4-autonomous-trigger-gating",
                projected,
                {"proposal": invalid},
            )
        except ROLE_POLICY.RolePolicyError:
            pass
        else:
            raise AssertionError(f"trigger-gatingの旧形式/不正wireを許可: {invalid!r}")


def test_critic_profiler_and_verifier_semantic_policy_negative_cases():
    critic_input = {
        "unevaluated_candidates": ["B0-L-W0"],
        "trajectory": ["B1-T-W1"],
    }
    bad_critic_outputs = (
        {"action": "evaluate", "genome": None},
        {"action": "evaluate", "genome": "B0-T-W0"},
        {"action": "stop", "genome": "B0-L-W0"},
    )
    for output in bad_critic_outputs:
        try:
            ROLE_POLICY.validate_output_semantics(
                "critic-experiment", critic_input, output
            )
        except ROLE_POLICY.RolePolicyError:
            pass
        else:
            raise AssertionError(f"critic-experiment条件違反を許可: {output!r}")

    for profiler_input in (
        {"certified": False, "screening": {"passed": True}},
        {"certified": True, "screening": {"passed": False}},
    ):
        try:
            ROLE_POLICY.validate_input_semantics("profiler", profiler_input)
        except ROLE_POLICY.RolePolicyError:
            pass
        else:
            raise AssertionError("profilerのgate未通過inputを許可した")

    trusted = {
        "serializable": True,
        "verdict": "serializable",
        "certified": True,
        "stats": {"txns": 3},
        "total_cycles": 0,
        "anomalies": [],
        "integrity": {"clean": True},
    }
    verifier_input = {"verification_result": trusted}
    valid_output = {**trusted, "uncertainty": ""}
    ROLE_POLICY.validate_output_semantics("verifier", verifier_input, valid_output)
    mutations = {
        "serializable": False,
        "verdict": "indeterminate",
        "certified": False,
        "stats": {"txns": 2},
        "total_cycles": 1,
        "anomalies": [{"invented": True}],
        "integrity": {"clean": False},
    }
    for field, value in mutations.items():
        output = {**valid_output, field: value}
        try:
            ROLE_POLICY.validate_output_semantics("verifier", verifier_input, output)
        except ROLE_POLICY.RolePolicyError:
            pass
        else:
            raise AssertionError(f"verifier trusted field改変を許可: {field}")

    invalid_trusted_results = (
        {**trusted, "integrity": {"clean": False}},
        {
            "serializable": False,
            "verdict": "non-serializable",
            "certified": False,
            "stats": {"txns": 3},
            "total_cycles": 1,
            "anomalies": [],
            "integrity": {"clean": True},
        },
        {
            "serializable": True,
            "verdict": "indeterminate",
            "certified": False,
            "stats": {"txns": 3},
            "total_cycles": 0,
            "anomalies": [],
            "integrity": {"clean": True},
        },
    )
    for invalid in invalid_trusted_results:
        try:
            ROLE_POLICY.validate_input_semantics(
                "verifier", {"verification_result": invalid}
            )
        except ROLE_POLICY.RolePolicyError:
            pass
        else:
            raise AssertionError(f"verifier三値不変条件違反を許可: {invalid!r}")

    # 空traceはacyclic/cleanでもcertifiedにせずindeterminateとして許可する。
    empty_trace = {
        "serializable": True,
        "verdict": "indeterminate",
        "certified": False,
        "stats": {"txns": 0},
        "total_cycles": 0,
        "anomalies": [],
        "integrity": {"clean": True},
    }
    ROLE_POLICY.validate_output_semantics(
        "verifier",
        {"verification_result": empty_trace},
        {**empty_trace, "uncertainty": "empty trace"},
    )


def test_auditor_output_schema_requires_diff_digest_for_consumer():
    root = _fixture()
    try:
        manifest = _manifest(root)
        required = manifest["roles"]["auditor"]["output_schema"]["required"]
        required.remove("diff_digest")
        _write_manifest(root, manifest)
        schema = manifest["roles"]["auditor"]["output_schema"]
        old_pin = SCHEMA_SHA256["auditor"]["output"]
        old_fields = ROLE_IO_CONTRACTS["auditor"]["output_required_fields"]
        old_obligations = dict(ROLE_IO_CONTRACTS["auditor"]["source_obligations"])
        with _reviewed_role_entry(root, "auditor"):
            SCHEMA_SHA256["auditor"]["output"] = _canonical_sha256(schema)
            ROLE_IO_CONTRACTS["auditor"]["output_required_fields"] = tuple(required)
            ROLE_IO_CONTRACTS["auditor"]["source_obligations"].pop("diff_digest")
            try:
                assert any("consumer 必須 field" in finding
                           for finding in CCA.check(root))
            finally:
                SCHEMA_SHA256["auditor"]["output"] = old_pin
                ROLE_IO_CONTRACTS["auditor"]["output_required_fields"] = old_fields
                ROLE_IO_CONTRACTS["auditor"]["source_obligations"] = old_obligations
    finally:
        shutil.rmtree(root)


def test_all_role_manifest_schema_and_adapter_weakening_hits_independent_ledgers():
    """generated側を同時に合わせても、独立schema/required台帳は弱化を拒否する。"""

    for role in sorted(ROLE_IO_CONTRACTS):
        for surface in ("input", "output"):
            root = _fixture()
            try:
                manifest = _manifest(root)
                schema = manifest["roles"][role][f"{surface}_schema"]
                field = schema["required"][0]
                schema["required"].remove(field)
                schema["properties"].pop(field)
                _write_manifest(root, manifest)

                adapter_path = root / ".codex" / "role-adapters" / f"{role}.json"
                adapter = json.loads(adapter_path.read_text(encoding="utf-8"))
                adapter_schema = adapter[f"{surface}_schema"]
                adapter_schema["required"].remove(field)
                adapter_schema["properties"].pop(field)
                adapter["review_ledger"]["io_contract"][
                    f"{surface}_required_fields"
                ].remove(field)
                observed_pin = _canonical_sha256(schema)
                adapter["review_ledger"][f"{surface}_schema_sha256"] = observed_pin
                adapter_path.write_text(
                    json.dumps(
                        adapter, ensure_ascii=False, sort_keys=True, indent=2
                    ) + "\n",
                    encoding="utf-8",
                )

                assert any("reviewed full manifest role SHA256 drift" in finding
                           for finding in CCA.check(root))

                with _reviewed_role_entry(root, role):
                    assert any(
                        "reviewed schema SHA256 drift" in finding
                        for finding in CCA.check(root)
                    )

                    # schema pinもreview済み相当に差し替えても、required field台帳が独立に赤。
                    old_pin = SCHEMA_SHA256[role][surface]
                    SCHEMA_SHA256[role][surface] = observed_pin
                    try:
                        findings = CCA.check(root)
                    finally:
                        SCHEMA_SHA256[role][surface] = old_pin
                    assert any("review ledger drift" in finding for finding in findings)
            finally:
                shutil.rmtree(root)


def test_consumer_required_field_drift_is_detected_from_source_ast():
    root = _fixture()
    try:
        path = root / "orchestrator" / "campaign" / "auditor_gate.py"
        text = path.read_text(encoding="utf-8")
        assert 'digest = a["diff_digest"]' in text
        path.write_text(text.replace('digest = a["diff_digest"]',
                                     'digest = a.get("diff_digest")', 1), encoding="utf-8")
        assert any("consumer required field drift" in finding for finding in CCA.check(root))
    finally:
        shutil.rmtree(root)


def test_planner_and_coder_source_output_wrapper_shape_parity_is_enforced():
    roles = (
        "planner-v4",
        "coder-v4-autonomous",
        "coder-v4-autonomous-k2",
        "coder-v4-autonomous-sort",
        "coder-v4-autonomous-policy",
        "coder-v4-autonomous-policy-ir",
        "coder-v4-autonomous-trigger-gating",
    )
    for role in roles:
        spec = CCA.ROLE_SPEC.get_role_spec(role)
        flattened = copy.deepcopy(spec.output_schema["properties"]["proposal"])
        mutated = replace(spec, output_schema=flattened)
        try:
            CCA._validate_source_output_shape(mutated)
        except CCA.ProfileError as exc:
            assert "shape parity drift" in str(exc)
        else:
            raise AssertionError(f"{role}のflattened output schemaを許可した")


def test_axis_proposer_source_output_shape_parity_covers_nested_arrays():
    for mutation in ("global_unknowns", "proposal_field", "hole_field"):
        spec = CCA.ROLE_SPEC.get_role_spec("axis-proposer")
        schema = copy.deepcopy(spec.output_schema)
        if mutation == "global_unknowns":
            schema["required"].remove("global_unknowns")
            schema["properties"].pop("global_unknowns")
        else:
            proposal = schema["properties"]["proposals"]["items"]
            if mutation == "proposal_field":
                proposal["required"].remove("safety_argument_hypothesis")
                proposal["properties"].pop("safety_argument_hypothesis")
            else:
                hole = proposal["properties"]["hole_location"]
                hole["required"].remove("skeleton")
                hole["properties"].pop("skeleton")
        try:
            CCA._validate_source_output_shape(replace(spec, output_schema=schema))
        except CCA.ProfileError as exc:
            assert "shape parity drift" in str(exc)
        else:
            raise AssertionError(f"axis nested output弱化を許可: {mutation}")


def test_direct_role_source_input_shape_parity_covers_top_and_nested_fields():
    planner = CCA.ROLE_SPEC.get_role_spec("planner-v4")
    planner_schema = copy.deepcopy(planner.input_schema)
    planner_schema["required"].remove("leading_indicators")
    planner_schema["properties"].pop("leading_indicators")
    try:
        CCA._validate_source_input_shape(
            replace(planner, input_schema=planner_schema)
        )
    except CCA.ProfileError as exc:
        assert "shape parity drift" in str(exc)
    else:
        raise AssertionError("planner source入力に残るfieldのschema削除を許可した")

    axis = CCA.ROLE_SPEC.get_role_spec("axis-proposer")
    axis_schema = copy.deepcopy(axis.input_schema)
    stock = axis_schema["properties"]["stock_excerpts"]["items"]
    stock["required"].remove("excerpt")
    stock["properties"].pop("excerpt")
    try:
        CCA._validate_source_input_shape(replace(axis, input_schema=axis_schema))
    except CCA.ProfileError as exc:
        assert "shape parity drift" in str(exc)
    else:
        raise AssertionError("axis source入力のnested field schema削除を許可した")


def test_duplicate_manifest_key_is_rejected():
    root = _fixture()
    try:
        path = root / "orchestrator" / "codex_roles" / "manifest.json"
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            '"schema_version": "izanagi.codex-role-manifest/v1",',
            '"schema_version": "izanagi.codex-role-manifest/v1",\n'
            '  "schema_version": "duplicate",',
            1,
        )
        path.write_text(text, encoding="utf-8")
        assert any("JSON key が重複" in finding for finding in CCA.check(root))
    finally:
        shutil.rmtree(root)


def test_nonfinite_manifest_json_constants_are_rejected():
    for constant in ("NaN", "Infinity", "-Infinity"):
        root = _fixture()
        try:
            path = root / "orchestrator" / "codex_roles" / "manifest.json"
            text = path.read_text(encoding="utf-8")
            text = text.replace("{", f'{{\n  "poison": {constant},', 1)
            path.write_text(text, encoding="utf-8")
            assert any("非有限JSON定数は禁止" in finding
                       for finding in CCA.check(root))
        finally:
            shutil.rmtree(root)


def test_direct_role_coverage_drift_raises_clean_profile_error():
    # ledger の direct 集合と checker の _SOURCE_EXAMPLE_PARITY_ROLES が drift したとき、
    # guard は未定義名参照の NameError ではなく clean な ProfileError finding を返す。
    original = CCA._SOURCE_EXAMPLE_PARITY_ROLES
    CCA._SOURCE_EXAMPLE_PARITY_ROLES = frozenset({"axis-proposer"})
    try:
        findings = CCA.check(_REPO)  # NameError なら check() の except を素通りしここで送出される
        assert any("coverage drift" in finding for finding in findings), findings
    finally:
        CCA._SOURCE_EXAMPLE_PARITY_ROLES = original


def test_lockstep_role_deletion_is_rejected_by_absolute_count_floor():
    # 全 source から 1 role を同時削除すると set 等号は 13 件で整合するが、review ledger の
    # 絶対枚数 floor で fail-closed になる。profiler は mediated なので direct coverage guard と干渉しない。
    from orchestrator.codex_roles import review_ledger as LEDGER
    role = "profiler"
    ledgers = (
        SOURCE_FILE_SHA256, ROLE_MANIFEST_SHA256, DESCRIPTION_SHA256,
        SCHEMA_SHA256, ROLE_IO_CONTRACTS,
    )
    root = _fixture()
    saved = {id(ledger): ledger.pop(role) for ledger in ledgers}
    try:
        (root / ".claude" / "agents" / f"{role}.md").unlink()
        (root / ".codex" / "role-adapters" / f"{role}.json").unlink()
        manifest = _manifest(root)
        del manifest["roles"][role]
        _write_manifest(root, manifest)
        findings = CCA.check(root)
        assert any("role 総数が想定と不一致" in finding for finding in findings), findings
        assert f"expected={LEDGER.EXPECTED_ROLE_COUNT}" in " ".join(findings)
    finally:
        for ledger in ledgers:
            ledger[role] = saved[id(ledger)]
        shutil.rmtree(root)


def _run():
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:  # noqa: BLE001 - 単体 runner の集計
            failed += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"{len(tests) - failed} passed, {failed} failed")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(_run())
