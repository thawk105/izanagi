# -*- coding: utf-8 -*-
"""Unit contract for the finite coder-hole lexical effect gate."""
from __future__ import annotations

from dataclasses import asdict, fields

import pytest

from orchestrator.campaign import coder_effect_gate as effect_gate
from orchestrator.campaign.coder_effect_gate import (
    DENY_TABLE,
    MALFORMED_RULE_ID,
    EffectFinding,
    scan_host_effects,
)
from orchestrator.campaign.reflux_ir import TriggerGateIR, emit_predicate
from orchestrator.campaign.s6_sort_sweep import CANDIDATES, _NOSORT_IMPL


@pytest.mark.parametrize(
    ("implementation", "category"),
    (
        ("std::system(\"ignored\");", "process-shell"),
        ("execl(\"ignored\", \"ignored\", nullptr);", "process-shell"),
        ("std::ofstream stream(\"ignored\");", "file-stdio"),
        ("while(true){}", "unconditional-loop"),
    ),
)
def test_measured_four_injections_are_rejected(implementation, category):
    findings = scan_host_effects(implementation)
    assert findings
    assert category in {finding.category for finding in findings}


@pytest.mark.parametrize(
    "implementation",
    (
        "std :: system(\"ignored\");",
        "auto run = std::system;",
        "auto run = &std :: system;",
        "auto run = std::sys\\\ntem;",
        "dlsym(handle, \"sys\" \"tem\");",
    ),
)
def test_spacing_aliases_and_resolver_calls_are_rejected(implementation):
    assert scan_host_effects(implementation)


@pytest.mark.parametrize(
    "implementation",
    (
        "int ecosystem = 0;",
        'const char* word = "system";',
        'const char* words = "sys" "tem";',
        "// system execl ofstream while(true)\nint value = 0;",
        "// system \\\nread while(true)\nint value = 0;",
        "/* system read socket thread syscall */ int value = 0;",
        'const char* word = "sys\\\ntem";',
    ),
)
def test_identifier_substrings_strings_and_comments_do_not_match(implementation):
    assert scan_host_effects(implementation) == ()


_CATEGORY_PROBES = {
    "process-shell": ("host-effect.process-shell.v1", "posix_spawnp();"),
    "file-stdio": ("host-effect.file-stdio.v1", "read();"),
    "network": ("host-effect.network.v1", "connect();"),
    "sleep-block-thread": (
        "host-effect.sleep-block-thread.v1", "sleep_for();",
    ),
    "escape-hatch": ("host-effect.escape-hatch.v1", "__asm__();"),
}


@pytest.mark.parametrize("category", tuple(_CATEGORY_PROBES))
def test_each_deny_table_category_has_a_mutation_killing_probe(category):
    """Deleting any complete category makes its dedicated positive control fail."""
    assert {rule.category for rule in DENY_TABLE} == set(_CATEGORY_PROBES)
    expected_rule_id, implementation = _CATEGORY_PROBES[category]
    expected_rule = next(rule for rule in DENY_TABLE if rule.category == category)
    assert expected_rule.rule_id == expected_rule_id
    findings = scan_host_effects(implementation)
    assert [(finding.rule_id, finding.category) for finding in findings] == [
        (expected_rule_id, category),
    ]


def test_deny_table_rule_ids_and_identifiers_are_unique():
    rule_ids = [rule.rule_id for rule in DENY_TABLE]
    categories = [rule.category for rule in DENY_TABLE]
    identifiers = [identifier for rule in DENY_TABLE for identifier in rule.identifiers]
    assert len(rule_ids) == len(set(rule_ids))
    assert len(categories) == len(set(categories))
    assert len(identifiers) == len(set(identifiers))
    assert MALFORMED_RULE_ID not in rule_ids


def test_finding_projection_has_only_disclosure_free_fields_and_total_count():
    findings = scan_host_effects("system();\nread();")
    assert [field.name for field in fields(EffectFinding)] == [
        "rule_id", "category", "token_ordinal", "line_number", "byte_length",
        "finding_count",
    ]
    assert [finding.line_number for finding in findings] == [1, 2]
    assert [finding.byte_length for finding in findings] == [6, 4]
    assert all(finding.finding_count == 2 for finding in findings)


@pytest.mark.parametrize(
    "implementation",
    (
        'const char* value = "SENTINEL_UNTERMINATED;',
        'const char* value = R"tag(SENTINEL_UNTERMINATED;',
        "/* SENTINEL_UNTERMINATED",
        "int value = 0; @ SENTINEL_UNEXPECTED_TOKEN",
        "int value = 0; \ud800 SENTINEL_SURROGATE",
    ),
)
def test_malformed_tokens_and_strings_fail_closed_without_byte_reflection(implementation):
    findings = scan_host_effects(implementation)
    assert len(findings) == 1
    assert findings[0].rule_id == MALFORMED_RULE_ID
    assert findings[0].category == "malformed-token"
    projection = repr(findings) + repr(asdict(findings[0]))
    assert "SENTINEL" not in projection
    assert "UNTERMINATED" not in projection
    assert "UNEXPECTED" not in projection


def test_unexpected_lexer_failure_is_fixed_and_nonreflective(monkeypatch):
    sentinel = "SENTINEL_INTERNAL_EXCEPTION_PAYLOAD"

    def fail(_implementation):
        raise ValueError(sentinel)

    monkeypatch.setattr(effect_gate, "_tokens", fail)
    findings = scan_host_effects(sentinel)
    assert len(findings) == 1
    assert findings[0].rule_id == MALFORMED_RULE_ID
    assert sentinel not in repr(findings)


def test_benign_candidate_local_directive_is_left_to_structural_gate():
    assert scan_host_effects("#define LOCAL_VALUE 1\nint value = LOCAL_VALUE;") == ()
    assert scan_host_effects("#define RUN system\n")


@pytest.mark.parametrize(
    "implementation",
    (
        "for (int i = 0; i < n; ++i) { values[i] += 1; }",
        "for (const auto& value : values) { total += value; }",
        "while (remaining > 0) { --remaining; }",
        "while (0) {}",
        "for (int i = 0; i < n; ++i) {}",
    ),
)
def test_ordinary_for_range_for_and_data_dependent_loops_pass(implementation):
    assert scan_host_effects(implementation) == ()


@pytest.mark.parametrize(
    "implementation",
    (
        "while (1u) {}",
        "while (0xDEADu) {}",
        "while ((true)) {}",
        "while (tr\\\nue) {}",
        "for (;;) {}",
        "for (; true ;) {}",
        "do {} while (1);",
    ),
)
def test_explicit_unconditional_loop_headers_are_rejected(implementation):
    findings = scan_host_effects(implementation)
    assert any(finding.category == "unconditional-loop" for finding in findings)


def test_while_true_with_break_is_intentionally_conservatively_rejected():
    """過剰拒否として意図した「保守的拒否」を受理集合の契約に固定する。"""
    findings = scan_host_effects("while (true) { break; }")
    assert [finding.category for finding in findings] == ["unconditional-loop"]


def test_normal_backoff_forms_pass():
    implementation = """
double now_backoff = 100.0;
double max_backoff = 100000.0;
now_backoff = now_backoff * 2.0;
if (now_backoff > max_backoff) now_backoff = max_backoff;
"""
    assert scan_host_effects(implementation) == ()


def test_all_current_s6_sort_candidates_and_nosort_pass():
    assert scan_host_effects(_NOSORT_IMPL) == ()
    for _name, _category, implementation in CANDIDATES:
        assert scan_host_effects(implementation) == ()


def test_all_canonical_trigger_predicates_pass():
    for mask in range(32):
        implementation = emit_predicate(TriggerGateIR(mask))
        assert scan_host_effects(implementation) == ()


if __name__ == "__main__":  # pragma: no cover - plain-runner false-green guard
    raise SystemExit(pytest.main([__file__, "-q"]))
