# -*- coding: utf-8 -*-
"""8b holdout freeze の検索、束縛、改竄検出の限定テスト。"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import pytest


_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import s8b_holdout_freeze as M  # noqa: E402
from orchestrator.campaign import s8b_floor_contract as FC  # noqa: E402
from orchestrator.campaign import t080_freeze_migration as T080  # noqa: E402
import s8b_v2_freeze_fixture as V2FIX  # noqa: E402
import t080_fixture_roots as FIXTURE_ROOTS  # noqa: E402


_V2_CANONICAL_PROBE_DOCUMENT = {
    "z_scientific": 1e2,
    "m_label": "測定",
    "a_budget": {"as_int": 100, "as_float": 100.0},
}
_V2_WRITER_RAW_LITERAL = (
    b'{"a_budget":{"as_float":100.0,"as_int":100},'
    b'"m_label":"\xe6\xb8\xac\xe5\xae\x9a","z_scientific":100.0}\n'
)
_V2_WRITER_SHA256_LITERAL = (
    "da5d41c6a6146af354a91ebcc640e4e2785155a2e7c1911e3a54e97ce61e790f"
)

_ATTEMPT_REGISTRY_PROOF_KEYS = (
    "schema", "registry_schema", "freeze_sha256", "protocol_sha256",
    "schedule_sha256", "row_count", "chain_head_sha256",
)


def _mutate_attempt_registry_proof(proof: dict, mutation: str) -> None:
    if mutation == "extra-key":
        proof["unexpected"] = True
        return
    operation, field = mutation.split(":", 1)
    if operation == "missing":
        proof.pop(field)
        return
    if operation != "invalid":
        raise AssertionError(f"unknown proof mutation: {mutation}")
    if field == "schema":
        proof[field] = "s8b-attempt-registry-prefix-proof/unknown"
    elif field == "registry_schema":
        proof[field] = "s8b-attempt-registry/v999"
    elif field == "row_count":
        proof[field] += 1
    else:
        value = proof[field]
        proof[field] = ("0" if value[0] != "0" else "1") + value[1:]


def _axis_value(holdout_name: str, axis: str) -> str:
    keys = {"rratio": M.RRATIO_KEY, "skew": M.SKEW_KEY, "rmw": M.RMW_KEY}
    return M.HOLDOUTS[holdout_name]["ycsb"][keys[axis]]


def _three_axis_text(ratio: str, encoding: int = 0, *, omit: str | None = None) -> str:
    values = {
        "rratio": ratio,
        "skew": _axis_value("rr80", "skew"),
        "rmw": _axis_value("rr80", "rmw"),
    }
    parts = []
    for axis, value in values.items():
        if axis != omit:
            parts.append(M.concrete_axis_encodings(axis, value)[encoding])
    return "\n".join(parts) + "\n"


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path.as_posix()


def _positive_text(encoding: int = 0) -> str:
    return _three_axis_text(M._POSITIVE_RATIO, encoding)


def _positive_fixture_report() -> dict:
    """外部固定 fixture だけを明示注入し、repo 全体は検索しない。"""
    return M.search_repository(
        FIXTURE_ROOTS.REPO_ROOT,
        files=[FIXTURE_ROOTS.POSITIVE_CONTROL_PATH],
    )


def _perf_unavailable_receipt(*, marker: bytes = b"holdout-degraded") -> dict:
    events = ["LLC-load-misses", "LLC-loads", "instructions", "cycles"]
    return {
        "schema": "izanagi-perf-preflight/v1",
        "status": "unavailable",
        "available": False,
        "probe_argv": [
            "perf", "stat", "-x,", "-o", "<tmp>/perf.csv", "-e",
            ",".join(events), "--", "/bin/true",
        ],
        "rc": None,
        "parsed_events": [],
        "reason": "perf-not-found",
        "stderr_sha256": hashlib.sha256(marker).hexdigest(),
        "candidates": [],
    }


def _perf_degraded_observation(receipt: dict) -> dict:
    return {
        "use_perf": False,
        "counter_status": "not_required",
        "missing_leading_indicators": [],
        "preflight": receipt,
        "claim_scope": {
            "throughput": "eligible",
            "perf_required": "unsupported",
        },
    }


def _degrade_v2_candidate_repository(fixture: dict) -> None:
    """共有 true fixture を canonical degraded floor closure へ局所変換する。"""
    from orchestrator.campaign import env_contract
    from orchestrator.campaign import s8b_floor_contract as contract
    from orchestrator.tests.s8b_floor_evidence_fixture import (
        build_floor_admission_evidence,
    )

    root = fixture["root"]
    result_path = root / fixture["result_rel"]
    run_dir = result_path.parent
    manifest_path = run_dir / "manifest.json"
    journal_path = run_dir / "journal.jsonl"
    result = json.loads(result_path.read_bytes())
    manifest = json.loads(manifest_path.read_bytes())
    receipt = _perf_unavailable_receipt()
    observation = _perf_degraded_observation(receipt)

    for session in result["sessions"]:
        session["run_cmd"] = [
            result["binaries"][session["cell_id"]]["binary"],
        ]
        for rep in session["rep_observations"]:
            rep["counter_status"] = "not_required"
            rep["perf_raw"] = {
                event: None for event in (
                    "LLC-load-misses", "LLC-loads", "instructions", "cycles",
                )
            }
    manifest["perf_preflight"] = receipt
    manifest["perf_observation"] = observation
    manifest_raw = V2FIX.canonical_bytes(manifest)
    manifest_path.write_bytes(manifest_raw)
    manifest_sha256 = hashlib.sha256(manifest_raw).hexdigest()
    result["manifest_sha256"] = manifest_sha256
    result["perf_preflight"] = receipt
    result["perf_observation"] = observation

    protocol_document = json.loads((root / M.FLOOR_PROTOCOL_REL).read_bytes())
    protocol = contract.validate_protocol(
        protocol_document,
        contract_sha256_lookup=lambda env_tag: env_contract.lookup(
            env_tag,
        ).contract_sha256,
    )
    v1 = json.loads((root / M.FREEZE_REL).read_bytes())
    cells = contract.enumerate_cells(
        v1, stock_configuration=protocol["stock_configuration"],
    )
    schedule = contract.build_schedule(
        cells=cells, master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    admission_root = root / ".git/izanagi/s8b-holdout-admission-v1"
    shutil.rmtree(admission_root)
    evidence = build_floor_admission_evidence(
        admission_root,
        protocol=protocol,
        freeze=v1,
        freeze_sha256=protocol["freeze"]["sha256"],
        manifest_sha256=manifest_sha256,
        campaign_run_id=result["holdout_admission"]["campaign_run_id"],
        run_relpath=result["holdout_admission"]["run_relpath"],
        mode="official",
        cells=cells,
        schedule=schedule,
        sessions=result["sessions"],
    )
    result["holdout_admission"] = evidence.expected_receipt
    result_path.write_bytes(V2FIX.canonical_bytes(result))

    sessions_by_seq = {session["seq"]: session for session in result["sessions"]}
    journal = [
        json.loads(line)
        for line in journal_path.read_text(encoding="utf-8").splitlines()
    ]
    journal = [
        sessions_by_seq[row["seq"]] if row.get("event") == "session" else row
        for row in journal
    ]
    journal_path.write_bytes(b"".join(
        V2FIX.canonical_bytes(row) + b"\n" for row in journal
    ))
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "degraded floor fixture")


def test_t080_positive_control_fixture_raw_bytes_match_test_pin():
    payload = FIXTURE_ROOTS.POSITIVE_CONTROL_FILE.read_bytes()

    assert hashlib.sha256(payload).hexdigest() == FIXTURE_ROOTS.POSITIVE_CONTROL_SHA256


def test_t080_positive_control_test_pins_match_production_literals():
    # raw bytes の hash node を独立させたうえで、別値源の三 literal を相互固定する。
    assert FIXTURE_ROOTS.POSITIVE_CONTROL_SHA256 == T080.POSITIVE_CONTROL_SHA256
    assert FIXTURE_ROOTS.POSITIVE_CONTROL_PATH == T080.POSITIVE_CONTROL_PATH
    assert FIXTURE_ROOTS.POSITIVE_CONTROL_ROOT_KEY == T080.POSITIVE_CONTROL_ROOT_KEY


def test_t080_positive_control_kills_predicate_only_rr51_mutant(monkeypatch):
    baseline = _positive_fixture_report()["positive_control"]
    assert baseline["hit_count"] == 1
    assert baseline["hit_paths"] == [FIXTURE_ROOTS.POSITIVE_CONTROL_PATH]

    original_expressions = M._expressions

    def rr51_positive_expressions(rratio: str, skew: str, rmw: str) -> dict:
        expressions = original_expressions(rratio, skew, rmw)
        if rratio == M._POSITIVE_RATIO:
            expressions["rratio"] = M.RRATIO_TEMPLATE.replace("<v>", "5" + "1")
        return expressions

    with monkeypatch.context() as mutant:
        mutant.setattr(M, "_expressions", rr51_positive_expressions)
        mutated = _positive_fixture_report()["positive_control"]

    assert mutated["hit_count"] == 0
    assert mutated["hit_paths"] == []
    assert mutated["expressions"]["rratio"] != baseline["expressions"]["rratio"]
    assert mutated["expressions"]["skew"] == baseline["expressions"]["skew"]
    assert mutated["expressions"]["rmw"] == baseline["expressions"]["rmw"]

    reverted = _positive_fixture_report()["positive_control"]
    assert reverted["hit_count"] == 1
    assert reverted["hit_paths"] == [FIXTURE_ROOTS.POSITIVE_CONTROL_PATH]
    assert reverted["expressions"] == baseline["expressions"]


def _known_axes() -> dict:
    entries = {}
    for workload in M.KNOWN_READ_RATIOS:
        entries[workload] = {}
        for index, name in enumerate(M.VARIANT_NAMES):
            entries[workload][name] = {
                "identity": workload + "-" + name,
                "payload": {
                    "index": index,
                    "reference_fitness_tps": 100 + index,
                    "nested": [{"reference_points": {"x": index}}],
                },
                "remeasure_reference": {"value": index},
                "sources": [{"path": workload + "/source"}],
            }
    return {"entries": entries}


def _synthetic_freeze_root(tmp_path: Path) -> tuple[Path, list[str], str]:
    root = tmp_path / "repo"
    _write(root / M.DESIGN_REL, "design fixture\n")
    known_path = root / M.KNOWN_AXES_REL
    known_path.parent.mkdir(parents=True, exist_ok=True)
    known_path.write_text(json.dumps(_known_axes()), encoding="utf-8")
    generator_path = root / M.SCRIPT_REL
    generator_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(M.__file__), generator_path)
    ccbench = root / "external/ccbench"
    ccbench.mkdir(parents=True)
    _git(ccbench, "init", "-q")
    _git(
        ccbench, "-c", "user.name=fixture", "-c",
        "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
        "commit", "--allow-empty", "-qm", "ccbench fixture",
    )
    rel = "fixtures/positive.txt"
    _write(root / rel, _positive_text())
    return root, [rel], "a" * 40


def test_file_level_conjunction_requires_all_three_axes(tmp_path):
    ratio = _axis_value("rr80", "rratio")
    full = tmp_path / "full.txt"
    partial = tmp_path / "partial.txt"
    _write(full, _three_axis_text(ratio))
    _write(partial, _three_axis_text(ratio, omit="rmw"))

    report = M.search_repository(tmp_path, [full, partial])
    result = report["holdouts"]["rr80"]
    assert result["conjunction_hits"] == ["full.txt"]
    assert result["per_axis_counts"] == {"rratio": 2, "skew": 2, "rmw": 1}


def test_all_three_canonical_encodings_are_detected(tmp_path):
    ratio = _axis_value("rr80", "rratio")
    files = []
    for encoding in range(3):
        path = tmp_path / ("encoding-" + str(encoding) + ".txt")
        _write(path, _three_axis_text(ratio, encoding))
        files.append(path)

    hits = M.search_repository(tmp_path, files)["holdouts"]["rr80"]["conjunction_hits"]
    assert hits == ["encoding-0.txt", "encoding-1.txt", "encoding-2.txt"]


def test_binary_and_non_utf8_files_are_skipped(tmp_path):
    binary = tmp_path / "binary.dat"
    binary.write_bytes(b"\0" + _three_axis_text(_axis_value("rr80", "rratio")).encode())
    non_utf8 = tmp_path / "non-utf8.dat"
    non_utf8.write_bytes(b"\xff\xfe")
    text = tmp_path / "text.txt"
    _write(text, "irrelevant\n")

    report = M.search_repository(tmp_path, [binary, non_utf8, text])
    assert report["search"]["file_count"] == 3
    assert report["search"]["skipped_binary_count"] == 2
    assert report["holdouts"]["rr80"]["conjunction_hits"] == []


def _current_expressions(holdout_name: str = "rr80") -> dict[str, str]:
    values = {
        axis: _axis_value(holdout_name, axis)
        for axis in ("rratio", "skew", "rmw")
    }
    return M._expressions(values["rratio"], values["skew"], values["rmw"])


def test_required_literal_is_nonempty_and_present_in_all_current_encodings():
    literal = M._derive_required_literal(_current_expressions())

    assert literal
    for axis in ("rratio", "skew", "rmw"):
        value = _axis_value("rr80", axis)
        assert all(literal in encoding for encoding in M.concrete_axis_encodings(axis, value))


@pytest.mark.parametrize("expressions", [
    {},
    {"axis": object()},
    {"axis": "key=value"},
    {"axis": "(?:ke.y=value)"},
    {"axis": r"(?:key=val\\ue)"},
    {"axis": "(?:key=[value])"},
    {"axis": "(?:key=(value))"},
    {"axis": "(?:key=value+)"},
    {"axis": "(?:key=(?=value))"},
])
def test_required_literal_unsupported_grammar_falls_back(expressions):
    assert M._derive_required_literal(expressions) is None


@pytest.mark.parametrize(
    "metacharacter", tuple("\\.^$*+?{}[]()|"), ids=repr,
)
def test_required_literal_rejects_each_key_regex_metacharacter(metacharacter):
    expressions = {"axis": "(?:a" + metacharacter + "=v)"}

    assert M._derive_required_literal(expressions) is None


def test_star_in_key_falls_back_and_slow_path_detects_hit():
    expressions = {"axis": "(?:a*=v)"}

    assert M._derive_required_literal(expressions) is None
    result = M._scan_one({"hit.txt": "=v"}, "candidate", expressions)

    assert result["per_axis_counts"] == {"axis": 1}
    assert result["conjunction_hits"] == ["hit.txt"]


def test_unsupported_expression_fallback_still_detects_hit():
    expression = "(?:key=(?:value))"

    result = M._scan_one({"hit.txt": "key=value"}, "candidate", {"axis": expression})

    assert result["per_axis_counts"] == {"axis": 1}
    assert result["conjunction_hits"] == ["hit.txt"]


def test_search_derives_common_and_axis_literals_once_per_scan(
        tmp_path, monkeypatch):
    positive = tmp_path / "positive.txt"
    _write(positive, _positive_text())
    original = M._derive_required_literal
    seen = []

    def spy(expressions):
        seen.append(expressions)
        return original(expressions)

    monkeypatch.setattr(M, "_derive_required_literal", spy)
    M.search_repository(tmp_path, files=[positive])

    assert len(seen) == 12
    assert sum(len(expressions) == 3 for expressions in seen) == 3
    assert sum(len(expressions) == 1 for expressions in seen) == 9
    assert len({id(expressions) for expressions in seen}) == 12


def test_axis_prefilter_skips_common_only_text_and_memo_searches_unique_expressions(
        tmp_path, monkeypatch):
    positive_text = _positive_text()
    irrelevant_text = "ycsb_unrelated text\n"
    positive = tmp_path / "positive.txt"
    irrelevant = tmp_path / "irrelevant.txt"
    _write(positive, positive_text)
    _write(irrelevant, irrelevant_text)
    original_compile = M.re.compile
    searched = []

    class SearchSpy:
        def __init__(self, expression):
            self._pattern = original_compile(expression)

        def search(self, text):
            searched.append(text)
            return self._pattern.search(text)

    monkeypatch.setattr(M.re, "compile", SearchSpy)
    M.search_repository(tmp_path, files=[positive, irrelevant])

    assert irrelevant_text not in searched
    assert searched.count(positive_text) == 5
    assert len(searched) == 5


def test_empty_prefilter_is_distinct_from_disabled_prefilter(monkeypatch):
    original_compile = M.re.compile
    searched = []

    class SearchSpy:
        def __init__(self, expression):
            self._pattern = original_compile(expression)

        def search(self, text):
            searched.append(text)
            return self._pattern.search(text)

    monkeypatch.setattr(M.re, "compile", SearchSpy)
    result = M._scan_one(
        {"irrelevant.txt": "irrelevant\n"}, "candidate", _current_expressions(),
    )

    assert searched == []
    assert result["per_axis_counts"] == {"rratio": 0, "skew": 0, "rmw": 0}


def test_disabled_common_prefilter_disables_every_axis_prefilter(monkeypatch):
    original_compile = M.re.compile
    searched = []
    derive_calls = []

    class SearchSpy:
        def __init__(self, expression):
            self._pattern = original_compile(expression)

        def search(self, text):
            searched.append(text)
            return self._pattern.search(text)

    def disable_common(expressions):
        derive_calls.append(dict(expressions))
        if len(expressions) == 1:
            pytest.fail("共通 literal 無効時に軸 literal を導出した")
        return None

    monkeypatch.setattr(M.re, "compile", SearchSpy)
    monkeypatch.setattr(M, "_derive_required_literal", disable_common)
    result = M._scan_one(
        {"unrelated.txt": "ycsb_unrelated\n"},
        "candidate", _current_expressions(),
    )

    assert len(derive_calls) == 1
    assert searched == ["ycsb_unrelated\n"] * 3
    assert result["per_axis_counts"] == {
        "rratio": 0, "skew": 0, "rmw": 0,
    }


def test_str_subclass_disables_prefilter(monkeypatch):
    class ExpressionSubclass(str):
        pass

    monkeypatch.setattr(
        M, "_derive_required_literal",
        lambda _expressions: pytest.fail("str subclass で前置フィルタを導出した"),
    )
    result = M._scan_one(
        {"hit.txt": "key=value"}, "candidate",
        {"axis": ExpressionSubclass("(?:key=value)")},
    )

    assert result["per_axis_counts"] == {"axis": 1}
    assert result["conjunction_hits"] == ["hit.txt"]


def test_value_side_dot_is_not_used_as_required_literal():
    expressions = _current_expressions()
    skew_value = _axis_value("rr80", "skew")
    regex_encoding = M.concrete_axis_encodings("skew", skew_value)[0]
    matching_value = skew_value[:1] + "x" + skew_value[2:]
    matching_encoding = M.concrete_axis_encodings("skew", matching_value)[0]
    text = _three_axis_text(_axis_value("rr80", "rratio")).replace(
        regex_encoding, matching_encoding,
    )

    result = M._scan_one({"dot-match.txt": text}, "candidate", expressions)

    assert result["conjunction_hits"] == ["dot-match.txt"]


def test_single_axis_required_literal_excludes_value_side():
    skew_value = _axis_value("rr80", "skew")
    expressions = {"skew": _current_expressions()["skew"]}

    literal = M._derive_required_literal(expressions)

    assert literal == M.SKEW_KEY
    assert skew_value not in literal


def test_single_axis_dot_match_survives_required_literal_prefilter():
    skew_value = _axis_value("rr80", "skew")
    matching_value = skew_value.replace(".", "X", 1)
    expressions = {"skew": _current_expressions()["skew"]}
    text = M.concrete_axis_encodings("skew", matching_value)[0]

    assert matching_value != skew_value
    result = M._scan_one({"dot-match.txt": text}, "candidate", expressions)

    assert result["per_axis_counts"] == {"skew": 1}
    assert result["conjunction_hits"] == ["dot-match.txt"]


def test_axis_prefilter_keeps_each_single_axis_count_without_conjunction():
    ratio = _axis_value("rr80", "rratio")
    values = {
        "rratio": ratio,
        "skew": _axis_value("rr80", "skew"),
        "rmw": _axis_value("rr80", "rmw"),
    }
    texts = {
        axis + ".txt": M.concrete_axis_encodings(axis, value)[0]
        for axis, value in values.items()
    }

    result = M._scan_one(texts, "candidate", _current_expressions())

    assert result["per_axis_counts"] == {
        "rratio": 1, "skew": 1, "rmw": 1,
    }
    assert result["conjunction_hits"] == []


def test_scan_memo_misses_for_a_different_text_mapping(monkeypatch):
    expression = {"axis": "(?:key=value)"}
    first_texts = {"same.txt": "irrelevant\n"}
    second_texts = {"same.txt": "key=value\n"}
    memo = M._ScanMemo(first_texts)
    original_compile = M.re.compile
    searched = []

    class SearchSpy:
        def __init__(self, value):
            self._pattern = original_compile(value)

        def search(self, text):
            searched.append(text)
            return self._pattern.search(text)

    monkeypatch.setattr(M.re, "compile", SearchSpy)
    first = M._scan_one(first_texts, "first", expression, memo=memo)
    second = M._scan_one(second_texts, "second", expression, memo=memo)

    assert first["conjunction_hits"] == []
    assert second["conjunction_hits"] == ["same.txt"]
    assert searched == ["key=value\n"]


def test_scan_memo_fails_closed_if_same_mutable_mapping_changes():
    texts = {"same.txt": "irrelevant\n"}
    expressions = {"axis": "(?:key=value)"}
    memo = M._ScanMemo(texts)

    first = M._scan_one(texts, "first", expressions, memo=memo)
    texts["same.txt"] = "key=value\n"

    assert first["conjunction_hits"] == []
    with pytest.raises(M.FreezeError, match="texts 内容が再利用前に変化"):
        M._scan_one(texts, "second", expressions, memo=memo)


def test_search_repository_passes_one_read_only_mapping_to_all_scans(
        tmp_path, monkeypatch):
    positive = tmp_path / "positive.txt"
    _write(positive, _positive_text())
    original_scan_one = M._scan_one
    seen = []

    def assert_read_only(texts, candidate_id, expressions, *, memo=None):
        assert isinstance(texts, MappingProxyType)
        assert memo is not None and memo.texts is texts
        with pytest.raises(TypeError):
            texts["mutated.txt"] = "not allowed"
        seen.append(texts)
        return original_scan_one(
            texts, candidate_id, expressions, memo=memo,
        )

    monkeypatch.setattr(M, "_scan_one", assert_read_only)
    M.search_repository(tmp_path, files=[positive])

    assert len(seen) == 3
    assert all(texts is seen[0] for texts in seen)


def test_memo_cache_hit_skips_regex_and_matches_slow_counts_and_sorted_conjunction(
        monkeypatch):
    texts = MappingProxyType({
        "z-first.txt": "key=value\nother=yes\n",
        "a-second.txt": "key=value\nother=yes\n",
        "middle.txt": "key=value\n",
    })
    expressions = {
        "first": "(?:key=value)",
        "second": "(?:other=yes)",
    }
    memo = M._ScanMemo(texts)
    M._scan_one(texts, "candidate", expressions, memo=memo)
    reference = _reference_scan_one(texts, "candidate", expressions)
    original_compile = M.re.compile
    searched = []

    class SearchSpy:
        def __init__(self, expression):
            self._pattern = original_compile(expression)

        def search(self, text):
            searched.append(text)
            return self._pattern.search(text)

    monkeypatch.setattr(M.re, "compile", SearchSpy)
    cached = M._scan_one(texts, "candidate", expressions, memo=memo)

    assert searched == []
    assert cached["per_axis_counts"] == reference["per_axis_counts"]
    assert cached["conjunction_hits"] == reference["conjunction_hits"]
    assert cached["conjunction_hits"] == ["a-second.txt", "z-first.txt"]
    assert cached == reference


def test_search_memo_does_not_cross_search_repository_calls(tmp_path):
    positive = tmp_path / "positive.txt"
    changed = tmp_path / "changed.txt"
    _write(positive, _positive_text())
    _write(changed, "ycsb_unrelated\n")

    before = M.search_repository(tmp_path, files=[positive, changed])
    _write(changed, _three_axis_text(_axis_value("rr80", "rratio")))
    after = M.search_repository(tmp_path, files=[positive, changed])

    assert before["holdouts"]["rr80"]["conjunction_hits"] == []
    assert after["holdouts"]["rr80"]["conjunction_hits"] == ["changed.txt"]


def test_zero_positive_control_fails_closed(tmp_path):
    path = tmp_path / "irrelevant.txt"
    _write(path, "irrelevant\n")
    report = M.search_repository(tmp_path, [path])
    with pytest.raises(M.FreezeError, match="陽性対照が 0 件"):
        M._assert_search_pass(report)


def test_holdout_hit_rejects_generate_and_search_reports_path(
    tmp_path, monkeypatch, capsys,
):
    positive = tmp_path / "positive.txt"
    holdout = tmp_path / "holdout.txt"
    _write(positive, _positive_text())
    _write(holdout, _three_axis_text(_axis_value("rr20", "rratio")))
    files = [positive, holdout]
    report = M.search_repository(tmp_path, files)

    with pytest.raises(M.FreezeError, match="rr20: holdout hit"):
        M.generate(
            confirmed_by="reviewer",
            confirmed_at="date",
            output_path=tmp_path / "freeze.json",
            root=tmp_path,
            files=files,
            frozen_at_head="b" * 40,
        )

    monkeypatch.setattr(M, "search_repository", lambda: report)
    assert M.main(["search"]) == 1
    captured = capsys.readouterr()
    assert "holdout.txt" in captured.out
    assert "fails-closed" in captured.err


def test_binding_anchors_and_recursively_strips_measurements():
    known_axes = _known_axes()
    high = M.build_variant_binding(int(_axis_value("rr80", "rratio")), known_axes)
    low = M.build_variant_binding(int(_axis_value("rr20", "rratio")), known_axes)

    assert high["anchor_workload"] == "read-heavy"
    assert low["anchor_workload"] == "write-heavy"
    assert high["distances"] == {"read-heavy": 15, "balanced": 30, "write-heavy": 75}
    assert low["distances"] == {"read-heavy": 75, "balanced": 30, "write-heavy": 15}
    assert high["stripped_keys"] == sorted(M.STRIP_KEYS)
    serialized = json.dumps(high["entries"], sort_keys=True)
    assert all(key not in serialized for key in M.STRIP_KEYS)
    assert high["entries"]["stock_common"]["sources"]
    assert known_axes["entries"]["read-heavy"]["stock_common"]["remeasure_reference"]

    with pytest.raises(M.FreezeError, match="tie"):
        M.select_anchor(50, {"left": 40, "right": 60})


def test_generate_refuses_overwrite_and_requires_confirmation(tmp_path):
    existing = tmp_path / "freeze.json"
    existing.write_text("{}", encoding="utf-8")
    with pytest.raises(M.FreezeError, match="既に存在"):
        M.generate(
            confirmed_by="reviewer", confirmed_at="date", output_path=existing,
        )

    root, files, head = _synthetic_freeze_root(tmp_path)
    with pytest.raises(M.FreezeError, match="confirmed-by"):
        M.generate(
            confirmed_by="", confirmed_at="date",
            output_path=tmp_path / "missing-confirmation.json",
            root=root, files=files, frozen_at_head=head,
        )
    with pytest.raises(SystemExit):
        M.main(["generate", "--confirmed-at", "date"])


def test_verify_rejects_source_hash_and_binding_tamper(tmp_path, monkeypatch):
    root, files, head = _synthetic_freeze_root(tmp_path)
    freeze = tmp_path / "freeze.json"
    doc = M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=freeze,
        root=root, files=files, frozen_at_head=head,
    )
    M.verify(freeze, root=root, files=files, current_head=head)

    hash_tamper = copy.deepcopy(doc)
    hash_tamper["design_source"]["sha256"] = "0" * 64
    hash_path = tmp_path / "hash-tamper.json"
    hash_path.write_text(json.dumps(hash_tamper), encoding="utf-8")
    held_result = M.verify(hash_path, root=root, files=files, current_head=head)
    assert "s8b-holdout.design_source-implementation-bytes" in {
        marker["check_id"] for marker in held_result.held_checks
    }
    with monkeypatch.context() as released:
        released.setattr(M._freeze_hold, "HELD", False)
        with pytest.raises(M.FreezeError, match="design_source sha256 不一致"):
            M.verify(hash_path, root=root, files=files, current_head=head)

    binding_tamper = copy.deepcopy(doc)
    binding_tamper["holdouts"]["rr80"]["variant_binding"]["entries"][
        "stock_common"
    ]["identity"] = "tampered"
    binding_path = tmp_path / "binding-tamper.json"
    binding_path.write_text(json.dumps(binding_tamper), encoding="utf-8")
    with pytest.raises(M.FreezeError, match="variant_binding 不一致"):
        M.verify(binding_path, root=root, files=files, current_head=head)


@pytest.mark.parametrize(
    "field",
    ["design_source", "known_axes_freeze", "generator"],
)
def test_source_identity_hold_and_release_positive_controls(
        tmp_path, monkeypatch, field):
    root, files, head = _synthetic_freeze_root(tmp_path)
    freeze = tmp_path / "freeze.json"
    doc = M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=freeze,
        root=root, files=files, frozen_at_head=head,
    )
    doc[field]["sha256"] = "0" * 64
    freeze.write_text(json.dumps(doc), encoding="utf-8")

    held_result = M.verify(freeze, root=root, files=files, current_head=head)
    assert f"s8b-holdout.{field}-implementation-bytes" in {
        marker["check_id"] for marker in held_result.held_checks
    }
    with monkeypatch.context() as released:
        released.setattr(M._freeze_hold, "HELD", False)
        with pytest.raises(M.FreezeError, match=rf"{field} sha256 不一致"):
            M.verify(freeze, root=root, files=files, current_head=head)


def test_head_identity_hold_and_release_positive_control(tmp_path, monkeypatch):
    root, files, head = _synthetic_freeze_root(tmp_path)
    freeze = tmp_path / "freeze.json"
    M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=freeze,
        root=root, files=files, frozen_at_head=head,
    )
    foreign_head = "f" * 40
    held_result = M.verify(
        freeze, root=root, files=files, current_head=foreign_head,
    )
    assert "s8b-holdout.frozen-head-current-head" in {
        marker["check_id"] for marker in held_result.held_checks
    }
    with monkeypatch.context() as released:
        released.setattr(M._freeze_hold, "HELD", False)
        with pytest.raises(
                M.FreezeError,
                match=(
                    rf"^frozen_at_head 不一致: recorded={head} "
                    rf"current={foreign_head}$"
                )):
            M.verify(freeze, root=root, files=files, current_head=foreign_head)


def test_verify_tolerates_per_axis_drift_and_rejects_snapshot_tamper(tmp_path):
    root, files, head = _synthetic_freeze_root(tmp_path)
    freeze = tmp_path / "freeze.json"
    doc = M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=freeze,
        root=root, files=files, frozen_at_head=head,
    )

    # 生成後に単一軸 (skew+rmw) だけ一致する無関係ファイルが増えても、conjunction に
    # 至らない限り verify は通る (per_axis_counts の経時ドリフト耐性)。
    drift_rel = _write(
        root / "fixtures/drift.txt",
        _three_axis_text(_axis_value("rr80", "rratio"), omit="rratio"),
    )
    drifted = files + ["fixtures/drift.txt"]
    M.verify(freeze, root=root, files=drifted, current_head=head)

    # スナップショット改竄: 記録済み per_axis_counts を書き換えると hash 再計算で落ちる。
    tampered = copy.deepcopy(doc)
    tampered["holdouts"]["rr80"]["unknownness_check"]["per_axis_counts"]["rratio"] += 1
    tampered_path = tmp_path / "snapshot-tamper.json"
    tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(M.FreezeError, match="zero_hit_output_sha256"):
        M.verify(tampered_path, root=root, files=drifted, current_head=head)

    # 実走後 (holdout 条件が repo に記録され既知化) は現時点有効性で落ちる。
    _write(root / "fixtures/post-run.txt",
           _three_axis_text(_axis_value("rr80", "rratio")))
    with pytest.raises(M.FreezeError, match="holdout hit"):
        M.verify(freeze, root=root, files=drifted + ["fixtures/post-run.txt"],
                 current_head=head)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def _commit_all(root: Path) -> str:
    """root を git repo 化し全ファイルを 1 commit にして実在 HEAD SHA を返す。"""
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(
        root, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-q", "-m", "gen1",
    )
    return _git(root, "rev-parse", "HEAD")


def _empty_search_repo(tmp_path: Path) -> Path:
    """root と ccbench の tmp git repo を作り、実列挙経路を使えるようにする。"""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    ccbench = root / "external/ccbench"
    ccbench.mkdir(parents=True)
    _git(ccbench, "init", "-q")
    return root


def _report_bytes(report: dict) -> bytes:
    return json.dumps(
        report, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def _reference_scan_one(
    texts: Mapping[str, str], candidate_id: str, expressions: Mapping[str, str],
    *, memo=None,
) -> dict:
    """prefilter と memo を持たない report 等価性用 scanner。"""
    del memo
    expression_snapshot = dict(expressions.items())
    compiled = {
        axis: M.re.compile(expression)
        for axis, expression in expression_snapshot.items()
    }
    per_axis_paths = {axis: [] for axis in expression_snapshot}
    conjunction_hits = []
    for rel, text in texts.items():
        matched = {
            axis: bool(pattern.search(text))
            for axis, pattern in compiled.items()
        }
        for axis, is_match in matched.items():
            if is_match:
                per_axis_paths[axis].append(rel)
        if all(matched.values()):
            conjunction_hits.append(rel)
    per_axis_counts = {
        axis: len(paths) for axis, paths in per_axis_paths.items()
    }
    conjunction_hits.sort()
    hash_input = {
        "candidate_id": candidate_id,
        "expressions": expression_snapshot,
        "per_axis_counts": per_axis_counts,
        "conjunction_hits": conjunction_hits,
    }
    return {
        **hash_input,
        "result_sha256": M._canonical_sha256(hash_input),
    }


def test_prefilter_scans_common_and_axis_literals_after_8192_bytes():
    padding = "x" * 9000
    expressions = _current_expressions()
    common_literal = M._derive_required_literal(expressions)
    axis_literals = {
        axis: M._derive_required_literal({axis: expression})
        for axis, expression in expressions.items()
    }
    texts = {
        "late-hit.txt": (
            padding + _three_axis_text(_axis_value("rr80", "rratio"))
        ),
    }

    assert len(padding.encode("utf-8")) > 8192
    assert "ycsb_" not in padding
    assert common_literal is not None and common_literal not in padding
    assert all(
        literal is not None and literal not in padding
        for literal in axis_literals.values()
    )
    optimized = M._scan_one(texts, "candidate", expressions)
    reference = _reference_scan_one(texts, "candidate", expressions)

    assert optimized["conjunction_hits"] == ["late-hit.txt"]
    assert reference["conjunction_hits"] == ["late-hit.txt"]
    assert optimized == reference


def _prefilter_equivalence_fixture(root: Path) -> tuple[list[str], str]:
    positive = "fixtures/positive.txt"
    holdout = "fixtures/holdout.txt"
    skew_only = "fixtures/skew-only.txt"
    rmw_only = "fixtures/rmw-only.txt"
    binary = "fixtures/binary.dat"
    non_utf8 = "fixtures/non-utf8.dat"
    excluded = M.EXCLUDED_PATHS[0] + "excluded-hit.txt"
    exact = M.EXCLUDED_PATHS[0] + "exact-hit.txt"
    irrelevant = "fixtures/irrelevant.txt"
    _write(root / positive, _positive_text())
    _write(root / holdout, _three_axis_text(_axis_value("rr80", "rratio")))
    _write(
        root / skew_only,
        M.concrete_axis_encodings("skew", _axis_value("rr80", "skew"))[0] + "\n",
    )
    _write(
        root / rmw_only,
        M.concrete_axis_encodings("rmw", _axis_value("rr80", "rmw"))[0] + "\n",
    )
    (root / binary).write_bytes(
        b"\0" + _three_axis_text(_axis_value("rr20", "rratio")).encode("utf-8")
    )
    (root / non_utf8).write_bytes(b"\xff\xfe")
    _write(root / excluded, _three_axis_text(_axis_value("rr20", "rratio")))
    _write(root / exact, _three_axis_text(_axis_value("rr20", "rratio")))
    _write(root / irrelevant, "ycsb_unrelated\n")
    return [
        positive, holdout, skew_only, rmw_only, binary, non_utf8,
        excluded, exact, irrelevant,
    ], exact


@pytest.mark.parametrize("mode", [
    "files",
    "exempt-none",
    "empty-mapping",
    "hash-match",
    "hash-mismatch",
])
def test_prefilter_report_exactly_matches_slow_path(tmp_path, monkeypatch, mode):
    root = _empty_search_repo(tmp_path)
    files, exact = _prefilter_equivalence_fixture(root)
    if mode == "files":
        kwargs = {"files": files, "exempt_exact": None}
    elif mode == "exempt-none":
        kwargs = {"exempt_exact": None}
    elif mode == "empty-mapping":
        kwargs = {"exempt_exact": {}}
    elif mode == "hash-match":
        kwargs = {"exempt_exact": {exact: M._sha256(root / exact)}}
    else:
        kwargs = {"exempt_exact": {exact: "0" * 64}}

    original_compile = M.re.compile
    searched = []

    class SearchSpy:
        def __init__(self, expression):
            self._pattern = original_compile(expression)

        def search(self, text):
            searched.append(text)
            return self._pattern.search(text)

    monkeypatch.setattr(M.re, "compile", SearchSpy)
    optimized = M.search_repository(root, **kwargs)
    assert searched.count("ycsb_unrelated\n") == 0
    searched.clear()
    with monkeypatch.context() as memo_only_path:
        memo_only_path.setattr(
            M, "_derive_required_literal", lambda _expressions: None,
        )
        memo_only = M.search_repository(root, **kwargs)
    assert searched.count("ycsb_unrelated\n") == 5
    assert memo_only == optimized
    searched.clear()
    reference_calls = []

    def reference(texts, candidate_id, expressions, *, memo=None):
        reference_calls.append(candidate_id)
        return _reference_scan_one(
            texts, candidate_id, expressions, memo=memo,
        )

    with monkeypatch.context() as slow:
        slow.setattr(M, "_scan_one", reference)
        unfiltered = M.search_repository(root, **kwargs)

    assert reference_calls == ["H1", "H2", "rr50-positive-control"]
    assert searched.count("ycsb_unrelated\n") == 9
    assert optimized["holdouts"]["rr80"]["conjunction_hits"] == [
        "fixtures/holdout.txt",
    ]
    assert optimized["positive_control"]["hit_count"] == 1
    expected_rr20_hits = {
        "files": [],
        "exempt-none": [],
        "empty-mapping": [
            "output/s8b-freeze/exact-hit.txt",
            "output/s8b-freeze/excluded-hit.txt",
        ],
        "hash-match": ["output/s8b-freeze/excluded-hit.txt"],
        "hash-mismatch": [
            "output/s8b-freeze/exact-hit.txt",
            "output/s8b-freeze/excluded-hit.txt",
        ],
    }
    assert optimized["holdouts"]["rr20"]["conjunction_hits"] == (
        expected_rr20_hits[mode]
    )
    assert optimized == unfiltered
    assert _report_bytes(optimized) == _report_bytes(unfiltered)


def test_prefilter_derives_from_monkeypatched_expressions(tmp_path, monkeypatch):
    values_by_ratio = {
        _axis_value(name, "rratio"): name
        for name in ("rr80", "rr20")
    }

    def runtime_expressions(rratio: str, skew: str, rmw: str) -> dict[str, str]:
        values = {"rratio": rratio, "skew": skew, "rmw": rmw}
        return {
            axis: "(?:runtime_" + axis + "=" + value + ")"
            for axis, value in values.items()
        }

    def runtime_text(rratio: str) -> str:
        values = {
            "rratio": rratio,
            "skew": _axis_value("rr80", "skew"),
            "rmw": _axis_value("rr80", "rmw"),
        }
        return "\n".join(
            "runtime_" + axis + "=" + value
            for axis, value in values.items()
        ) + "\n"

    holdout = tmp_path / "runtime-holdout.txt"
    positive = tmp_path / "runtime-positive.txt"
    holdout_ratio = next(
        ratio for ratio, name in values_by_ratio.items() if name == "rr80"
    )
    _write(holdout, runtime_text(holdout_ratio))
    _write(positive, runtime_text(M._POSITIVE_RATIO))
    monkeypatch.setattr(M, "_expressions", runtime_expressions)

    optimized = M.search_repository(tmp_path, files=[holdout, positive])
    with monkeypatch.context() as slow:
        slow.setattr(M, "_derive_required_literal", lambda _expressions: None)
        unfiltered = M.search_repository(tmp_path, files=[holdout, positive])

    assert optimized["holdouts"]["rr80"]["conjunction_hits"] == [
        "runtime-holdout.txt",
    ]
    assert optimized == unfiltered
    assert _report_bytes(optimized) == _report_bytes(unfiltered)


def test_prefilter_snapshots_monkeypatched_mapping_once(tmp_path, monkeypatch):
    created = []

    class SplitViewExpressions(Mapping):
        def __init__(self):
            self.items_calls = 0
            self.values_calls = 0
            created.append(self)

        def __getitem__(self, key):
            if key != "axis":
                raise KeyError(key)
            return "(?:actual=v)"

        def __iter__(self):
            return iter(("axis",))

        def __len__(self):
            return 1

        def items(self):
            self.items_calls += 1
            return (("axis", "(?:actual=v)"),)

        def values(self):
            self.values_calls += 1
            return ("(?:safe=v)",)

    monkeypatch.setattr(
        M, "_expressions", lambda _rratio, _skew, _rmw: SplitViewExpressions(),
    )
    hit = tmp_path / "hit.txt"
    _write(hit, "actual=v")

    optimized = M.search_repository(tmp_path, files=[hit])
    with monkeypatch.context() as slow:
        slow.setattr(M, "_derive_required_literal", lambda _expressions: None)
        unfiltered = M.search_repository(tmp_path, files=[hit])

    assert all(
        result["conjunction_hits"] == ["hit.txt"]
        for result in optimized["holdouts"].values()
    )
    assert optimized["positive_control"]["hit_paths"] == ["hit.txt"]
    assert optimized["positive_control"]["expressions"] == {
        "axis": "(?:actual=v)",
    }
    assert optimized == unfiltered
    assert _report_bytes(optimized) == _report_bytes(unfiltered)
    assert len(created) == 6
    assert all(mapping.items_calls == 1 for mapping in created)
    assert all(mapping.values_calls == 0 for mapping in created)


def test_exact_exemption_matching_bytes_is_not_scanned_but_is_enumerated(tmp_path):
    root = _empty_search_repo(tmp_path)
    rel = "output/s8b-freeze/active.json"
    positive_rel = "fixtures/positive.txt"
    path = root / rel
    _write(path, _three_axis_text(_axis_value("rr80", "rratio")))
    _write(root / positive_rel, _positive_text())

    report = M.search_repository(root, exempt_exact={rel: M._sha256(path)})

    assert M.enumerate_repository_files(root) == (positive_rel, rel)
    assert report["search"]["file_count"] == 2
    assert report["search"]["excluded_paths"] == []
    assert report["holdouts"]["rr80"]["conjunction_hits"] == []
    M._assert_search_pass(report)


def test_exact_exemption_hash_mismatch_is_scanned_and_hits(tmp_path):
    root = _empty_search_repo(tmp_path)
    rel = "output/s8b-freeze/active.json"
    _write(root / rel, _three_axis_text(_axis_value("rr80", "rratio")))

    report = M.search_repository(root, exempt_exact={rel: "0" * 64})

    assert report["holdouts"]["rr80"]["conjunction_hits"] == [rel]


def test_exact_exemption_unknown_non_hit_file_is_still_scanned(tmp_path):
    root = _empty_search_repo(tmp_path)
    rel = "output/s8b-freeze/unknown.json"
    ratio = _axis_value("rr80", "rratio")
    _write(root / rel, M.concrete_axis_encodings("rratio", ratio)[0] + "\n")
    _write(root / "fixtures/positive.txt", _positive_text())

    report = M.search_repository(root, exempt_exact={})

    assert report["holdouts"]["rr80"]["per_axis_counts"] == {
        "rratio": 1, "skew": 1, "rmw": 1,
    }
    assert report["holdouts"]["rr80"]["conjunction_hits"] == []
    M._assert_search_pass(report)


def test_exact_exemption_unknown_hit_file_is_detected(tmp_path):
    root = _empty_search_repo(tmp_path)
    rel = "output/s8b-freeze/unknown.json"
    # concrete 三軸 encoding は helper 内で実行時結合し、test source へ同居させない。
    _write(root / rel, _three_axis_text(_axis_value("rr20", "rratio")))

    report = M.search_repository(root, exempt_exact={})

    assert report["holdouts"]["rr20"]["conjunction_hits"] == [rel]


@pytest.mark.parametrize("exempt_exact", [None, {}])
def test_similar_freeze_prefix_is_always_scanned(tmp_path, exempt_exact):
    root = _empty_search_repo(tmp_path)
    rel = "output/s8b-freeze-evil/hit.json"
    _write(root / rel, _three_axis_text(_axis_value("rr80", "rratio")))

    report = M.search_repository(root, exempt_exact=exempt_exact)

    assert report["holdouts"]["rr80"]["conjunction_hits"] == [rel]


def test_exempt_none_preserves_v1_prefix_report_bytes(tmp_path):
    root = _empty_search_repo(tmp_path)
    included = "fixtures/positive.txt"
    excluded = "output/s8b-freeze/hidden.json"
    _write(root / included, _positive_text())
    _write(root / excluded, _three_axis_text(_axis_value("rr80", "rratio")))

    legacy_report = M.search_repository(root, files=[included])
    default_report = M.search_repository(root, exempt_exact=None)

    assert _report_bytes(default_report) == _report_bytes(legacy_report)
    assert default_report["search"]["excluded_paths"] == list(M.EXCLUDED_PATHS)
    assert default_report["holdouts"]["rr80"]["conjunction_hits"] == []


def test_verify_rejects_active_generation_worktree_drift(tmp_path, monkeypatch):
    # v1 単一 filename freeze は唯一の発効中 (active) 世代。生成後に設計本文を worktree で
    # 改変すると、frozen_at_head 時点の blob が recorded sha256 と一致していても、verify は
    # worktree 完全一致を要求して拒否する (active 世代のドリフト検知)。blob 救済は世代別
    # 不変 filename + 承認束縛を伴う v2 の旧世代専用であり、唯一の active 世代へ適用すると
    # 設計本文の worktree 改変が骨抜きになる (fail-open) ため、ここでは通してはいけない。
    root, files, _ = _synthetic_freeze_root(tmp_path)
    head1 = _commit_all(root)
    freeze = tmp_path / "freeze.json"
    doc = M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=freeze,
        root=root, files=files, frozen_at_head=head1,
    )
    M.verify(freeze, root=root, files=files)

    # 設計本文を worktree で改変 + 再 commit。frozen_at_head=head1 の blob は不変で
    # recorded と一致し (blob 救済なら通ってしまう) が、worktree の現物は record と食い違う。
    (root / M.DESIGN_REL).write_text("design fixture drifted body\n", encoding="utf-8")
    _git(
        root, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-aqm", "gen2",
    )
    assert M._sha256(root / M.DESIGN_REL) != doc["design_source"]["sha256"]
    held_result = M.verify(freeze, root=root, files=files)
    assert "s8b-holdout.design_source-implementation-bytes" in {
        marker["check_id"] for marker in held_result.held_checks
    }
    with monkeypatch.context() as released:
        released.setattr(M._freeze_hold, "HELD", False)
        with pytest.raises(M.FreezeError, match="design_source sha256 不一致"):
            M.verify(freeze, root=root, files=files)


def test_verify_rejects_unratified_generation_documents(tmp_path):
    root, files, head = _synthetic_freeze_root(tmp_path)
    freeze = tmp_path / "freeze.json"
    doc = M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=freeze,
        root=root, files=files, frozen_at_head=head,
    )
    M.verify(freeze, root=root, files=files, current_head=head)

    # 世代別承認を検証しない v1 経路では、世代 field を 1 つでも持つ文書を拒否する。
    for field in sorted(M.GENERATION_SCHEMA_FIELDS):
        generation = copy.deepcopy(doc)
        generation[field] = "x" if field != "supersedes_sha256" else "a" * 64
        gen_path = tmp_path / f"generation-{field}.json"
        gen_path.write_text(json.dumps(generation), encoding="utf-8")
        with pytest.raises(M.FreezeError) as caught:
            M.verify(gen_path, root=root, files=files, current_head=head)
        reason = str(caught.value)
        assert "世代 document は v1 verify_document 経路では発効しない" in reason
        assert "この v1 経路は世代別承認を検証しない" in reason
        assert "未裁定" not in reason
        assert "§8" not in reason


def test_v1_source_verification_keeps_worktree_exactness_and_names_v2_authority():
    reason = M._verify_source.__doc__ or ""
    assert "worktree 完全一致のみを正とする" in reason
    assert "s8b_ratified_freeze.load_ratified_freeze" in reason
    assert "この v1 経路は" in reason
    assert "世代 schema document を発効させない" in reason


def _active_t080_resolution(*, holdout_sha256: str = T080.HOLDOUT_RAW_SHA256):
    receipt = {
        "artifacts": {
            "holdout": {"raw_sha256": holdout_sha256},
        },
    }
    return T080.ReceiptResolution(
        "active-valid", (), {"migration_id": "T-080"}, "a" * 40,
        receipt=receipt,
    )


def _t080_artifact_root(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "repo"
    holdout = root / M.FREEZE_REL
    known = root / T080.KNOWN_AXES_REL
    holdout.parent.mkdir(parents=True)
    known.parent.mkdir(parents=True)
    shutil.copyfile(M.FREEZE_PATH, holdout)
    shutil.copyfile(M.ROOT / T080.KNOWN_AXES_REL, known)
    return root, holdout, known


def test_verify_cli_accepts_active_t080_receipt_exact_match(capsys, monkeypatch):
    monkeypatch.setattr(M._freeze_hold, "_EMITTED_MARKERS", set())
    assert M.main(["verify"]) == 0
    captured = capsys.readouterr()
    assert '"status": "held"' in captured.out
    assert '"decision": "freeze-verification-hold"' in captured.out
    marker_lines = captured.err.splitlines()
    assert marker_lines
    assert all(
        line.startswith(f"{M._freeze_hold.MARKER_PREFIX} ")
        for line in marker_lines
    )


def test_verify_direct_cli_accepts_active_t080_receipt_exact_match():
    completed = subprocess.run(
        ["python3", M.SCRIPT_REL, "verify"], cwd=M.ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    assert completed.returncode == 0, completed.stderr
    assert '"status": "held"' in completed.stdout
    assert '"decision": "freeze-verification-hold"' in completed.stdout
    marker_lines = completed.stderr.splitlines()
    assert marker_lines
    assert all(
        line.startswith(f"{M._freeze_hold.MARKER_PREFIX} ")
        for line in marker_lines
    )


def test_verify_cli_active_receipt_hash_mismatch_is_immediate_red(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    path = root / M.FREEZE_REL
    path.parent.mkdir(parents=True)
    path.write_bytes(b"{}\n")
    monkeypatch.setattr(T080, "verify_receipt", lambda **_kwargs: _active_t080_resolution())
    monkeypatch.setattr(
        T080, "static_gate_adapter",
        lambda **_kwargs: pytest.fail("hash mismatch で adapter を呼んだ"),
    )
    monkeypatch.setattr(
        M, "verify", lambda *_args, **_kwargs: pytest.fail("legacy fallback へ戻った"),
    )

    with pytest.raises(M.FreezeError, match="capture bytes の sha256 が不一致"):
        M.verify_cli_with_t080_receipt(path, root=root)


def test_verify_cli_same_bytes_at_noncanonical_path_are_rejected(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    alternate = root / "alternate" / "holdout_freeze.json"
    known = root / T080.KNOWN_AXES_REL
    alternate.parent.mkdir(parents=True)
    known.parent.mkdir(parents=True)
    alternate.write_bytes(M.FREEZE_PATH.read_bytes())
    shutil.copyfile(M.ROOT / T080.KNOWN_AXES_REL, known)
    monkeypatch.setattr(T080, "verify_receipt", lambda **_kwargs: _active_t080_resolution())
    monkeypatch.setattr(
        T080, "static_gate_adapter",
        lambda **_kwargs: T080.AdapterResult((), {"migration_id": "T-080"}),
    )
    monkeypatch.setattr(
        M, "verify", lambda *_args, **_kwargs: pytest.fail("legacy fallback へ戻った"),
    )

    with pytest.raises(M.FreezeError, match="canonical active path でない"):
        M.verify_cli_with_t080_receipt(alternate, root=root)


@pytest.mark.parametrize(
    ("state", "refusals"),
    [
        ("invalid", ("migration-receipt-verify:receipt.invalid",)),
        ("issued-but-missing", ("migration-receipt-verify:receipt.issued_but_missing",)),
    ],
    ids=["invalid", "issued-but-missing"],
)
def test_verify_cli_issued_receipt_failure_never_delegates_to_legacy_verify(
        tmp_path, monkeypatch, state, refusals):
    root, files, _ = _synthetic_freeze_root(tmp_path)
    head = _commit_all(root)
    path = root / M.FREEZE_REL
    M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=path,
        root=root, files=files, frozen_at_head=head,
    )
    M.verify(path, root=root, current_head=head)
    resolution = T080.ReceiptResolution(state, refusals, None, head)
    monkeypatch.setattr(T080, "verify_receipt", lambda **_kwargs: resolution)

    with pytest.raises(M.FreezeError, match=f"receipt が有効でない: {state}"):
        M.verify_cli_with_t080_receipt(path, root=root)


def test_verify_cli_known_axes_fire_condition_mismatch_is_red(
        tmp_path, monkeypatch):
    root, path, _known = _t080_artifact_root(tmp_path)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["known_axes_freeze"]["sha256"] = "0" * 64
    raw = json.dumps(document, ensure_ascii=False, sort_keys=True).encode("utf-8")
    path.write_bytes(raw)
    monkeypatch.setattr(
        T080, "verify_receipt",
        lambda **_kwargs: _active_t080_resolution(
            holdout_sha256=hashlib.sha256(raw).hexdigest(),
        ),
    )
    monkeypatch.setattr(
        T080, "static_gate_adapter",
        lambda **_kwargs: T080.AdapterResult((), {"migration_id": "T-080"}),
    )

    with pytest.raises(M.FreezeError, match="known_axes 発火条件が一致しない"):
        M.verify_cli_with_t080_receipt(path, root=root)


def test_verify_cli_rejects_bytes_changed_while_receipt_is_verified(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    path = root / M.FREEZE_REL
    path.parent.mkdir(parents=True)
    original = M.FREEZE_PATH.read_bytes()
    path.write_bytes(original)

    def swap_after_capture(**_kwargs):
        path.write_bytes(original + b" ")
        return _active_t080_resolution()

    monkeypatch.setattr(T080, "verify_receipt", swap_after_capture)
    monkeypatch.setattr(
        T080, "static_gate_adapter",
        lambda **_kwargs: pytest.fail("TOCTOU mismatch で adapter を呼んだ"),
    )
    monkeypatch.setattr(
        M, "verify", lambda *_args, **_kwargs: pytest.fail("legacy fallback へ戻った"),
    )

    with pytest.raises(M.FreezeError, match="検証前後で freeze bytes が変化"):
        M.verify_cli_with_t080_receipt(path, root=root)


@pytest.mark.parametrize(
    ("changed_artifact", "message"),
    [
        ("holdout", "adapter 検証中に freeze bytes が変化"),
        ("known", "adapter 検証中に known_axes bytes が変化"),
    ],
    ids=["holdout", "known-axes"],
)
def test_verify_cli_rejects_artifact_changed_while_adapter_runs(
        tmp_path, monkeypatch, changed_artifact, message):
    root, path, known = _t080_artifact_root(tmp_path)
    target = path if changed_artifact == "holdout" else known
    original = target.read_bytes()
    monkeypatch.setattr(T080, "verify_receipt", lambda **_kwargs: _active_t080_resolution())

    def swap_in_adapter(**_kwargs):
        target.write_bytes(original + b" ")
        return T080.AdapterResult((), {"migration_id": "T-080"})

    monkeypatch.setattr(T080, "static_gate_adapter", swap_in_adapter)

    with pytest.raises(M.FreezeError, match=message):
        M.verify_cli_with_t080_receipt(path, root=root)


def test_verify_cli_never_issued_delegates_to_legacy_verify_and_keeps_drift_red(
        tmp_path, monkeypatch):
    root, files, _ = _synthetic_freeze_root(tmp_path)
    head = _commit_all(root)
    path = root / M.FREEZE_REL
    M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=path,
        root=root, files=files, frozen_at_head=head,
    )
    M.verify(path, root=root, current_head=head)
    (root / M.DESIGN_REL).write_text("unreceived drift\n", encoding="utf-8")
    never_issued = T080.ReceiptResolution("never-issued", (), None, head)
    monkeypatch.setattr(T080, "verify_receipt", lambda **_kwargs: never_issued)
    monkeypatch.setattr(
        T080, "static_gate_adapter",
        lambda **_kwargs: pytest.fail("never-issued で adapter を呼んだ"),
    )

    held_result = M.verify_cli_with_t080_receipt(path, root=root)
    assert "s8b-holdout.design_source-implementation-bytes" in {
        marker["check_id"] for marker in held_result.held_checks
    }
    with monkeypatch.context() as released:
        released.setattr(M._freeze_hold, "HELD", False)
        with pytest.raises(M.FreezeError, match="design_source sha256 不一致"):
            M.verify_cli_with_t080_receipt(path, root=root)


def test_read_regular_nofollow_rejects_symlink(tmp_path):
    target = tmp_path / "target"
    target.write_bytes(b"freeze\n")
    link = tmp_path / "canonical"
    link.symlink_to(target)

    with pytest.raises(M.FreezeError, match="nofollow|regular file"):
        M._read_regular_nofollow(link)


def test_read_regular_nofollow_rejects_fifo_without_blocking(tmp_path):
    fifo = tmp_path / "canonical"
    os.mkfifo(fifo)
    script = """
import sys
from pathlib import Path
from orchestrator.campaign import s8b_holdout_freeze as module
try:
    module._read_regular_nofollow(Path(sys.argv[1]))
except module.FreezeError:
    raise SystemExit(0)
raise SystemExit(1)
"""

    completed = subprocess.run(
        [sys.executable, "-c", script, str(fifo)], cwd=M.ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3,
    )

    assert completed.returncode == 0, completed.stderr


def test_verify_cli_does_not_mask_unexpected_receipt_exception(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    monkeypatch.setattr(
        T080, "verify_receipt",
        lambda **_kwargs: (_ for _ in ()).throw(ValueError("internal receipt bug")),
    )

    with pytest.raises(ValueError, match="internal receipt bug"):
        M.verify_cli_with_t080_receipt(root / M.FREEZE_REL, root=root)


def test_verify_cli_does_not_mask_unexpected_adapter_exception(tmp_path, monkeypatch):
    root, path, _known = _t080_artifact_root(tmp_path)
    monkeypatch.setattr(T080, "verify_receipt", lambda **_kwargs: _active_t080_resolution())
    monkeypatch.setattr(
        T080, "static_gate_adapter",
        lambda **_kwargs: (_ for _ in ()).throw(TypeError("internal adapter bug")),
    )

    with pytest.raises(TypeError, match="internal adapter bug"):
        M.verify_cli_with_t080_receipt(path, root=root)


def test_source_guard_has_no_static_concrete_axis_encoding():
    module_source = Path(M.__file__).read_text(encoding="utf-8")
    test_source = Path(__file__).read_text(encoding="utf-8")
    sources = (module_source, test_source)
    values = {
        "rratio": {
            _axis_value("rr80", "rratio"),
            _axis_value("rr20", "rratio"),
            M._POSITIVE_RATIO,
        },
        "skew": {_axis_value("rr80", "skew")},
        "rmw": {_axis_value("rr80", "rmw")},
    }
    for axis, axis_values in values.items():
        for value in axis_values:
            for encoding in M.concrete_axis_encodings(axis, value):
                assert all(encoding not in source for source in sources)


def test_v2_candidate_fails_closed_before_reading_inputs_when_budget_unratified(
        tmp_path, monkeypatch):
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", None)

    with pytest.raises(M.FreezeError, match="^budget-approval-not-ratified$"):
        M.build_v2_g1_candidate(
            floor_result_path="missing-result.json",
            budget_path="missing-budget.json",
            root=tmp_path,
        )
    assert M.main([
        "generate-v2-candidate",
        "--floor-result", "missing-result.json",
        "--budget", "missing-budget.json",
    ]) == 1


def test_v1_apis_import_and_execute_when_v2_dependencies_fail_to_import(
        tmp_path):
    root, files, _fixture_head = _synthetic_freeze_root(tmp_path)
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "v1 import boundary fixture")
    head = _git(root, "rev-parse", "HEAD")
    output = root / M.FREEZE_REL
    script = r'''
import importlib.abc
import pathlib
import sys

blocked = {
    "orchestrator.campaign.env_contract",
    "orchestrator.campaign.s8b_floor_contract",
    "orchestrator.campaign.s8b_floor_stats",
    "orchestrator.campaign.s8b_launch_cert",
}

class BlockV2Dependencies(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in blocked:
            raise ImportError(f"blocked v2 dependency: {fullname}")
        return None

sys.meta_path.insert(0, BlockV2Dependencies())
from orchestrator.campaign import s8b_holdout_freeze as module

root = pathlib.Path(sys.argv[1])
source = sys.argv[2]
head = sys.argv[3]
output = pathlib.Path(sys.argv[4])
report = module.search_repository(root, files=[source])
assert report["positive_control"]["hit_count"] == 1
generated = module.generate(
    confirmed_by="reviewer",
    confirmed_at="2026-08-11T00:00:00Z",
    output_path=output,
    root=root,
    files=[source],
    frozen_at_head=head,
)
assert module.verify(
    output, root=root, files=[source], current_head=head,
) == generated
assert module.verify_cli_with_t080_receipt(output, root=root) == generated
assert blocked.isdisjoint(sys.modules)
'''
    completed = subprocess.run(
        [sys.executable, "-c", script, str(root), files[0], head, str(output)],
        cwd=Path(M.ROOT), text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    assert completed.returncode == 0, completed.stderr


def _rewrite_floor_artifacts_for_uncommitted_protocol_seed(fixture: dict) -> str:
    """作業ツリーだけの protocol seed 変更に従う未 commit artifact を作る。"""
    from orchestrator.campaign import env_contract
    from orchestrator.campaign import s8b_floor_contract as contract
    from orchestrator.tests.s8b_floor_evidence_fixture import (
        build_floor_admission_evidence,
    )

    root = fixture["root"]
    v1 = json.loads((root / M.FREEZE_REL).read_bytes())
    protocol_path = root / M.FLOOR_PROTOCOL_REL
    protocol_document = json.loads(protocol_path.read_bytes())
    protocol_document["master_seed"] += "-worktree-only"
    protocol_path.write_bytes(V2FIX.canonical_bytes(protocol_document))
    protocol = contract.validate_protocol(
        protocol_document,
        contract_sha256_lookup=lambda env_tag: env_contract.lookup(
            env_tag,
        ).contract_sha256,
    )
    protocol_sha256 = contract.canonical_protocol_sha256(protocol)
    cells = contract.enumerate_cells(
        v1, stock_configuration=protocol["stock_configuration"],
    )
    schedule = contract.build_schedule(
        cells=cells, master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    result = V2FIX._synthetic_floor_result(v1, protocol, root=root)
    run_dir = (
        f"output/env/{protocol['env_tag']}/calibration/s8b-floor-official/"
        f"20260811T000000Z-{protocol_sha256[:8]}"
    )
    result_rel = f"{run_dir}/result.json"
    manifest = {
        "schema_version": contract.MANIFEST_SCHEMA,
        "protocol_sha256": protocol_sha256,
        "freeze": dict(protocol["freeze"]),
        "freeze_sha256": protocol["freeze"]["sha256"],
        "env_tag": protocol["env_tag"],
        "ccbench_pin": protocol["ccbench_pin"],
        "stock_configuration": protocol["stock_configuration"],
        "schedule_algorithm": protocol["schedule_algorithm"],
        "master_seed": protocol["master_seed"],
        "n_sessions": protocol["n_sessions"],
        "reps": protocol["reps"],
        "extime_s": protocol["extime_s"],
        "session_cv_max": protocol["session_cv_max"],
        "cell_cv_max": protocol["cell_cv_max"],
        "cells": cells,
        "binaries": result["binaries"],
        "schedule": schedule,
    }
    manifest_raw = V2FIX.canonical_bytes(manifest)
    result["manifest_sha256"] = hashlib.sha256(manifest_raw).hexdigest()

    admission_root = root / ".git/izanagi/s8b-holdout-admission-v1"
    shutil.rmtree(admission_root)
    evidence = build_floor_admission_evidence(
        admission_root,
        protocol=protocol, freeze=v1,
        freeze_sha256=protocol["freeze"]["sha256"],
        manifest_sha256=result["manifest_sha256"],
        campaign_run_id=f"20260811T000000Z-{protocol_sha256[:8]}",
        run_relpath=run_dir.removeprefix("output/"), mode="official",
        cells=cells, schedule=schedule, sessions=result["sessions"],
    )
    result["holdout_admission"] = evidence.expected_receipt

    schedule_by_seq = {row["seq"]: row for row in schedule}
    journal_records = []
    for session in result["sessions"]:
        scheduled = schedule_by_seq[session["seq"]]
        journal_records.append({
            "event": "session-start", "seq": session["seq"],
            "kind": "planned", "cell_id": session["cell_id"],
            "round": scheduled["round"], "retry_ordinal": None,
            "attempt_id": session["attempt_id"], "trigger": None,
        })
        journal_records.append(session)
    V2FIX._write(root, result_rel, V2FIX.canonical_bytes(result))
    V2FIX._write(root, f"{run_dir}/manifest.json", manifest_raw)
    V2FIX._write(root, f"{run_dir}/journal.jsonl", b"".join(
        V2FIX.canonical_bytes(record) + b"\n" for record in journal_records
    ))
    campaign_run_id = f"20260811T000000Z-{protocol_sha256[:8]}"
    V2FIX._write(
        root, f"{run_dir}/launch_certificate.json",
        V2FIX.canonical_bytes(V2FIX.launch_certificate(
            protocol_sha256=protocol_sha256,
            campaign_run_id=campaign_run_id,
        )),
    )
    return result_rel


def test_v2_candidate_rejects_worktree_only_floor_protocol_master_seed_mutation(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    result_rel = _rewrite_floor_artifacts_for_uncommitted_protocol_seed(fixture)
    protocol = json.loads((root / M.FLOOR_PROTOCOL_REL).read_bytes())
    committed_protocol = json.loads(
        _git(root, "show", f"{fixture['head']}:{M.FLOOR_PROTOCOL_REL}")
    )
    assert protocol["master_seed"] != committed_protocol["master_seed"]

    output = root / M.V2_CANDIDATE_REL
    assert not output.exists()
    assert not output.parent.exists()
    with pytest.raises(
            M.FreezeError, match="floor protocol が captured HEAD と worktree で不一致"):
        M.generate_v2_g1_candidate(
            floor_result_path=result_rel,
            budget_path=fixture["budget_rel"],
            root=root,
        )
    assert not output.exists()
    assert not output.parent.exists()


def test_v2_candidate_build_and_generate_synthetic_g1(tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    legacy_result = json.loads((root / fixture["result_rel"]).read_bytes())
    assert legacy_result["schema"] == FC.LEGACY_RESULT_SCHEMA
    assert "attempt_registry" not in legacy_result
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )

    document = M.build_v2_g1_candidate(
        floor_result_path=fixture["result_rel"],
        budget_path=fixture["budget_rel"],
        root=root,
    )

    assert frozenset(document) == M.V2_TOP_LEVEL_KEYS
    assert document["schema_version"] == M.V2_SCHEMA_VERSION
    assert document["generation_number"] == 1
    assert document["supersedes_sha256"] == T080.HOLDOUT_RAW_SHA256
    assert document["frozen_at_head"] == fixture["head"]
    assert document["generator"]["path"] == M.SCRIPT_REL
    assert document["known_axes_freeze"] == json.loads(
        (root / M.FREEZE_REL).read_bytes(),
    )["known_axes_freeze"]
    v1 = json.loads((root / M.FREEZE_REL).read_bytes())
    changed_v1_fields = {
        "schema_version", "frozen_at_head", "design_source", "generator", "floor",
        "budget", "refreeze_note",
    }
    assert all(
        document[field] == v1[field]
        for field in M.TOP_LEVEL_KEYS - changed_v1_fields
    )
    assert document["budget"] == fixture["budget"]
    assert document["floor"]["by_holdout"]
    closure = {
        entry["canonical_path"]: entry["sha256"]
        for entry in document["measurement_closure"]
    }
    assert set(fixture["closure_paths"]) <= set(closure)
    assert all(
        closure[rel] == hashlib.sha256((root / rel).read_bytes()).hexdigest()
        for rel in fixture["closure_paths"]
    )

    generated = M.generate_v2_g1_candidate(
        floor_result_path=fixture["result_rel"],
        budget_path=fixture["budget_rel"],
        root=root,
    )
    output = root / M.V2_CANDIDATE_REL
    assert output.read_bytes() == V2FIX.canonical_bytes(generated)
    assert generated == document
    with pytest.raises(M.FreezeError, match="安全に新規作成できない"):
        M.generate_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )


def test_v2_candidate_accepts_live_v5_registry_prefix_with_later_append(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(
        tmp_path, M, result_schema=FC.RESULT_SCHEMA_V5,
    )
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )

    document = M.build_v2_g1_candidate(
        floor_result_path=fixture["result_rel"],
        budget_path=fixture["budget_rel"], root=fixture["root"],
    )

    result = json.loads(
        (fixture["root"] / fixture["result_rel"]).read_bytes()
    )
    proof = result["attempt_registry"]
    assert document["floor_source"]["path"] == fixture["result_rel"]
    assert result["schema"] == FC.RESULT_SCHEMA_V5
    assert frozenset(proof) == frozenset(_ATTEMPT_REGISTRY_PROOF_KEYS)
    assert proof["row_count"] >= 3
    assert fixture["live_row_count"] > proof["row_count"]
    live_lines = fixture["registry_path"].read_bytes().splitlines()
    assert len(live_lines) == fixture["live_row_count"]
    pinned_row = json.loads(live_lines[proof["row_count"] - 1])
    assert pinned_row["event_sha256"] == proof["chain_head_sha256"]


@pytest.mark.parametrize("schema", [[], {}], ids=["list", "object"])
def test_v2_candidate_rejects_unhashable_result_schema_with_controlled_error(
        tmp_path, monkeypatch, schema):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    result_path = root / fixture["result_rel"]
    result = json.loads(result_path.read_bytes())
    result["schema"] = schema
    result_path.write_bytes(V2FIX.canonical_bytes(result))
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )

    with pytest.raises(M.FreezeError, match=r"^floor result\.schema が"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        *(f"missing:{field}" for field in _ATTEMPT_REGISTRY_PROOF_KEYS),
        "extra-key",
        *(f"invalid:{field}" for field in _ATTEMPT_REGISTRY_PROOF_KEYS),
    ],
)
def test_v2_candidate_rejects_invalid_v5_registry_proof(
        tmp_path, monkeypatch, mutation):
    fixture = V2FIX.candidate_repository(
        tmp_path, M, result_schema=FC.RESULT_SCHEMA_V5,
        mutate_attempt_registry=lambda proof: (
            _mutate_attempt_registry_proof(proof, mutation)
        ),
    )
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )

    with pytest.raises(M.FreezeError):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=fixture["root"],
        )


@pytest.mark.parametrize(
    ("ledger_mutation", "expected_reason"),
    (
        ("missing", "attempt-registry-read-unavailable"),
        ("tampered", "attempt-registry-replay-invalid"),
        ("shortened", "attempt-registry-prefix-too-short"),
    ),
)
def test_v2_candidate_rejects_invalid_live_v5_registry(
        tmp_path, monkeypatch, ledger_mutation, expected_reason):
    fixture = V2FIX.candidate_repository(
        tmp_path, M, result_schema=FC.RESULT_SCHEMA_V5,
    )
    registry_path = fixture["registry_path"]
    lines = registry_path.read_bytes().splitlines()
    if ledger_mutation == "missing":
        registry_path.unlink()
    elif ledger_mutation == "tampered":
        row = json.loads(lines[1])
        digest = row["event_sha256"]
        row["event_sha256"] = ("0" if digest[0] != "0" else "1") + digest[1:]
        registry_path.write_bytes(b"\n".join((
            lines[0], V2FIX.canonical_bytes(row), *lines[2:],
        )) + b"\n")
    else:
        registry_path.write_bytes(lines[0] + b"\n")
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )

    with pytest.raises(M.FreezeError, match=expected_reason):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=fixture["root"],
        )


def _floor_selection_context(fixture: dict) -> tuple[dict, dict, dict]:
    from orchestrator.campaign import env_contract
    from orchestrator.campaign import s8b_floor_contract
    from orchestrator.campaign.s8b_launch_cert import parse_official_run_path

    root = fixture["root"]
    v1 = json.loads((root / M.FREEZE_REL).read_bytes())
    protocol = s8b_floor_contract.validate_protocol(
        json.loads((root / M.FLOOR_PROTOCOL_REL).read_bytes()),
        contract_sha256_lookup=lambda env_tag: env_contract.lookup(
            env_tag,
        ).contract_sha256,
    )
    path_info = parse_official_run_path(
        fixture["result_rel"], expected_basename="result.json",
    )
    return v1, protocol, path_info


def _derive_fixture_floor_selection_eligibility(
        fixture: dict, *, result_rel: str | None = None) -> bool:
    from orchestrator.campaign.s8b_launch_cert import parse_official_run_path

    root = fixture["root"]
    result_rel = fixture["result_rel"] if result_rel is None else result_rel
    v1, protocol, _selected_path_info = _floor_selection_context(fixture)
    path_info = parse_official_run_path(
        result_rel, expected_basename="result.json",
    )
    run_fd = M._open_nofollow_directory_chain(
        root, result_rel.rsplit("/", 1)[0], label="test floor run",
    )
    try:
        result_before = M._capture_regular_nofollow_at(
            run_fd, "result.json", label="test floor result",
        )
        assert result_before is not None
        return M._derive_floor_selection_eligibility(
            root=root, run_fd=run_fd, result_rel=result_rel,
            result_before=result_before, path_info=path_info,
            protocol=protocol, v1=v1,
        )
    finally:
        os.close(run_fd)


def _expected_current_floor_admission_receipt(
        admission_root: Path, *, campaign_run_id: str, run_relpath: str,
        protocol_sha256: str, freeze_sha256: str,
        manifest_sha256: str) -> dict:
    """production projector から独立した current admission receipt 投影。"""
    main_rows = [
        json.loads(line)
        for line in (admission_root / "ledger.jsonl").read_text().splitlines()
    ]
    attempt_rows = [
        json.loads(line)
        for line in (admission_root / "attempt-ledger.jsonl").read_text().splitlines()
    ]
    selected_main = sorted(
        (
            row for row in main_rows
            if row["campaign_run_id"] == campaign_run_id
        ),
        key=lambda row: (row["cell_id"], row["cell_effect_digest"]),
    )
    selected_attempts = sorted(
        (
            row for row in attempt_rows
            if row["campaign_run_id"] == campaign_run_id
        ),
        key=lambda row: (
            row["cell_id"], row["attempt_id"],
            row["measurement_generation_claim_digest"],
        ),
    )
    projection = {
        "schema": "s8b-floor-admission-ledger-projection/v1",
        "campaign_run_id": campaign_run_id,
        "admission_rows": [
            {key: value for key, value in row.items() if key != "measurement_head"}
            for row in selected_main
        ],
        "attempt_rows": selected_attempts,
    }
    claim_identities = {
        row["cell_id"]: row["measurement_generation_claim_digest"]
        for row in selected_main
    }
    return {
        "schema": "s8b-floor-holdout-admission-receipt/v1",
        "campaign_run_id": campaign_run_id,
        "run_relpath": run_relpath,
        "mode": "official",
        "protocol_sha256": protocol_sha256,
        "freeze_sha256": freeze_sha256,
        "manifest_sha256": manifest_sha256,
        "claim_identities": dict(sorted(claim_identities.items())),
        "admission_row_count": len(selected_main),
        "attempt_row_count": len(selected_attempts),
        "ledger_projection_sha256": hashlib.sha256(
            V2FIX.canonical_bytes(projection)
        ).hexdigest(),
    }


def _install_real_floor_selection_runs(
        fixture: dict, run_specs: list[dict]) -> dict[str, dict]:
    """既存 fixture の実 artifact を複製し、production admission を発行する。"""
    from orchestrator.campaign import s8b_floor_contract as contract
    from orchestrator.campaign import s8b_holdout_admission as admission

    root = fixture["root"]
    selected_rel = fixture["result_rel"]
    selected_run_id = selected_rel.rsplit("/", 2)[-2]
    namespace_rel = selected_rel.rsplit("/", 2)[0]
    template_result = json.loads((root / selected_rel).read_bytes())
    template_manifest = json.loads(
        (root / selected_rel.rsplit("/", 1)[0] / "manifest.json").read_bytes()
    )
    v1, protocol, _path_info = _floor_selection_context(fixture)
    cells = contract.enumerate_cells(
        v1, stock_configuration=protocol["stock_configuration"],
    )
    admission_cells = [
        {
            "cell_id": cell["cell_id"],
            "freeze_holdout_key": cell["holdout_id"],
            "configuration_id": cell["configuration_id"],
            "records": cell["records"],
            "threads": cell["threads"],
            "workload": cell["workload"],
        }
        for cell in cells
    ]
    schedule = contract.build_schedule(
        cells=cells, master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    schedule_by_seq = {row["seq"]: row for row in schedule}
    admission_root = root / ".git/izanagi/s8b-holdout-admission-v1"
    shutil.rmtree(admission_root)

    installed = {}
    for ordinal, spec in enumerate(run_specs, 1):
        run_id = spec["run_id"]
        assert run_id.rsplit("-", 1)[1] == selected_run_id.rsplit("-", 1)[1]
        run_dir_rel = f"{namespace_rel}/{run_id}"
        result_rel = f"{run_dir_rel}/result.json"
        run_dir = root / run_dir_rel
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True)

        manifest_raw = V2FIX.canonical_bytes(template_manifest) + b"\n" * ordinal
        manifest_sha256 = hashlib.sha256(manifest_raw).hexdigest()
        (run_dir / "manifest.json").write_bytes(manifest_raw)
        journal_path = run_dir / "journal.jsonl"
        journal_path.write_bytes(b"")
        run_relpath = run_dir_rel.removeprefix("output/")
        reservation = admission.reserve_floor_holdout_observations(
            repo_root=root, protocol=protocol, verified_freeze_document=v1,
            freeze_sha256=protocol["freeze"]["sha256"],
            cells=admission_cells, schedule=schedule,
            campaign_run_id=run_id, out_root=root / "output",
            run_dir=run_dir, run_relpath=run_relpath, mode="official",
            resume=False, nondefault_seams=[],
        )
        admitted = admission.finalize_floor_holdout_admissions(reservation)
        if spec.get("resume") is True:
            resumed = admission.reserve_floor_holdout_observations(
                repo_root=root, protocol=protocol,
                verified_freeze_document=v1,
                freeze_sha256=protocol["freeze"]["sha256"],
                cells=admission_cells, schedule=schedule,
                campaign_run_id=run_id, out_root=root / "output",
                run_dir=run_dir, run_relpath=run_relpath, mode="official",
                resume=True, nondefault_seams=[],
            )
            admitted = admission.finalize_floor_holdout_admissions(resumed)

        journal_records = []
        result = copy.deepcopy(template_result)
        for session in result["sessions"]:
            scheduled = schedule_by_seq[session["seq"]]
            start = {
                "event": "session-start", "seq": session["seq"],
                "kind": "planned", "cell_id": session["cell_id"],
                "round": scheduled["round"], "retry_ordinal": None,
                "attempt_id": session["attempt_id"], "trigger": None,
            }
            journal_records.append(start)
            journal_path.write_bytes(b"".join(
                V2FIX.canonical_bytes(record) + b"\n"
                for record in journal_records
            ))
            if session["probe_before"]["competing"] is False:
                admission.consume_attempt_ticket(
                    admitted[session["cell_id"]],
                    attempt_id=session["attempt_id"],
                )
            journal_records.append(session)
            journal_path.write_bytes(b"".join(
                V2FIX.canonical_bytes(record) + b"\n"
                for record in journal_records
            ))

        inspection = admission.inspect_floor_holdout_admission_evidence(
            repo_root=root, protocol=protocol, verified_freeze_document=v1,
            freeze_sha256=protocol["freeze"]["sha256"],
            manifest_sha256=manifest_sha256, campaign_run_id=run_id,
            run_relpath=run_relpath, mode="official", cells=cells,
            schedule=schedule, sessions=journal_records,
        )
        expected_receipt = _expected_current_floor_admission_receipt(
            admission_root, campaign_run_id=run_id, run_relpath=run_relpath,
            protocol_sha256=hashlib.sha256(
                (root / M.FLOOR_PROTOCOL_REL).read_bytes()
            ).hexdigest(),
            freeze_sha256=protocol["freeze"]["sha256"],
            manifest_sha256=manifest_sha256,
        )
        assert dict(inspection) == expected_receipt
        reported = spec.get(
            "reported_eligible_for_refreeze",
            inspection.derived_eligible_for_refreeze,
        )
        result["eligible_for_refreeze"] = reported
        result["manifest_sha256"] = manifest_sha256
        result["holdout_admission"] = expected_receipt
        (run_dir / "result.json").write_bytes(V2FIX.canonical_bytes(result))
        (run_dir / "launch_certificate.json").write_bytes(
            V2FIX.canonical_bytes(V2FIX.launch_certificate(
                protocol_sha256=result["protocol_sha256"],
                campaign_run_id=run_id,
            ))
        )
        installed[run_id] = {
            "result_rel": result_rel,
            "run_relpath": run_relpath,
            "manifest_sha256": manifest_sha256,
            "claim_identities": dict(expected_receipt["claim_identities"]),
            "derived_eligible_for_refreeze": (
                inspection.derived_eligible_for_refreeze
            ),
        }

    V2FIX._git(root, "add", "-A")
    V2FIX._git(root, "commit", "-qm", "real floor selection run fixtures")
    fixture["head"] = V2FIX._git(root, "rev-parse", "HEAD")
    return installed


def test_floor_selection_eligibility_uses_derived_bit_not_reported_result(
        tmp_path):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    result_path = root / fixture["result_rel"]
    result = json.loads(result_path.read_bytes())
    result["eligible_for_refreeze"] = False
    result_path.write_bytes(V2FIX.canonical_bytes(result))
    assert _derive_fixture_floor_selection_eligibility(fixture) is True


def test_floor_selection_eligibility_derives_resume_as_ineligible(tmp_path):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    v1, protocol, path_info = _floor_selection_context(fixture)
    admission_root = root / ".git/izanagi/s8b-holdout-admission-v1"
    for claim_path in (admission_root / "claims").glob("*.claim"):
        claim = json.loads(claim_path.read_bytes())
        claim["entry_kind"] = "resume"
        claim_path.write_bytes(V2FIX.canonical_bytes(claim) + b"\n")
    marker = {
        "schema_version": "s8b-refreeze-disqualification/v1",
        "reason": "resume",
        "campaign_run_id": path_info["run_id"],
        "run_relpath": fixture["result_rel"].rsplit("/", 1)[0].removeprefix(
            "output/"
        ),
        "protocol_sha256": hashlib.sha256(
            V2FIX.canonical_bytes(protocol)
        ).hexdigest(),
        "freeze_sha256": T080.HOLDOUT_RAW_SHA256,
    }
    marker_name = hashlib.sha256(path_info["run_id"].encode("utf-8")).hexdigest()
    V2FIX._write(
        root,
        (
            ".git/izanagi/s8b-holdout-admission-v1/"
            f"refreeze-disqualifications/{marker_name}.json"
        ),
        V2FIX.canonical_bytes(marker) + b"\n",
    )

    assert _derive_fixture_floor_selection_eligibility(fixture) is False


@pytest.mark.parametrize(
    "reported_eligible_for_refreeze",
    [True, False, True],
    ids=["min-to-max", "use-reported-eligible", "drop-candidate-selection"],
)
def test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility(
        tmp_path, monkeypatch, reported_eligible_for_refreeze):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    selected_id = fixture["result_rel"].rsplit("/", 2)[-2]
    proto8 = selected_id.rsplit("-", 1)[1]
    earlier_id = f"20260810T235900Z-{proto8}"
    installed = _install_real_floor_selection_runs(fixture, [
        {
            "run_id": earlier_id,
            "reported_eligible_for_refreeze": reported_eligible_for_refreeze,
        },
        {"run_id": selected_id},
    ])
    earlier_rel = installed[earlier_id]["result_rel"]
    selected = json.loads((root / fixture["result_rel"]).read_bytes())
    earlier = json.loads((root / earlier_rel).read_bytes())
    assert selected["floors"] == earlier["floors"]
    assert installed[earlier_id]["derived_eligible_for_refreeze"] is True
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    with pytest.raises(
            M.FreezeError,
            match=(
                r"^floor-selection-rule-mismatch: "
                r"earliest-eligible-official-run-id/v1: .*required_run_id="
                r"20260810T235900Z-"
            )):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


@pytest.mark.parametrize("_mutation_case", [None], ids=["underivable-to-skip"])
def test_v2_candidate_fails_closed_when_earlier_eligibility_is_underivable(
        tmp_path, monkeypatch, _mutation_case):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    selected_id = fixture["result_rel"].rsplit("/", 2)[-2]
    proto8 = selected_id.rsplit("-", 1)[1]
    earlier_id = f"20260810T235900Z-{proto8}"
    installed = _install_real_floor_selection_runs(fixture, [
        {"run_id": earlier_id},
        {"run_id": selected_id},
    ])
    earlier_rel = installed[earlier_id]["result_rel"]
    earlier_claim = next(iter(installed[earlier_id]["claim_identities"].values()))
    earlier_claim_path = (
        root / ".git/izanagi/s8b-holdout-admission-v1"
        / "measurement-generation-claims" / f"{earlier_claim}.claim"
    )
    assert earlier_claim_path.is_file()
    earlier_claim_path.unlink()
    assert not earlier_claim_path.exists()
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    with pytest.raises(
            M.FreezeError,
            match=rf"^floor-selection-eligibility-underivable: {re.escape(earlier_rel)}:"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


def test_v2_candidate_accepts_later_run_after_derived_ineligible_resume(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    selected_id = fixture["result_rel"].rsplit("/", 2)[-2]
    proto8 = selected_id.rsplit("-", 1)[1]
    earlier_id = f"20260810T235900Z-{proto8}"
    installed = _install_real_floor_selection_runs(fixture, [
        {"run_id": earlier_id, "resume": True},
        {"run_id": selected_id},
    ])
    assert installed[earlier_id]["derived_eligible_for_refreeze"] is False
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    document = M.build_v2_g1_candidate(
        floor_result_path=fixture["result_rel"],
        budget_path=fixture["budget_rel"], root=root,
    )
    assert document["floor_source"]["path"] == fixture["result_rel"]


def test_floor_selection_threads_earlier_run_identity_and_manifest_to_derivation(
        tmp_path, monkeypatch):
    from orchestrator.campaign import s8b_holdout_admission as admission

    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    selected_id = fixture["result_rel"].rsplit("/", 2)[-2]
    proto8 = selected_id.rsplit("-", 1)[1]
    earlier_id = f"20260810T235900Z-{proto8}"
    installed = _install_real_floor_selection_runs(fixture, [
        {"run_id": earlier_id},
        {"run_id": selected_id},
    ])
    earlier = installed[earlier_id]
    selected = installed[selected_id]
    assert earlier["result_rel"] != selected["result_rel"]
    assert earlier["run_relpath"] != selected["run_relpath"]
    assert earlier["manifest_sha256"] != selected["manifest_sha256"]

    observed = []
    original = admission.inspect_floor_holdout_admission_evidence

    def inspect_spy(**kwargs):
        observed.append({
            "campaign_run_id": kwargs["campaign_run_id"],
            "run_relpath": kwargs["run_relpath"],
            "manifest_sha256": kwargs["manifest_sha256"],
        })
        return original(**kwargs)

    monkeypatch.setattr(
        admission, "inspect_floor_holdout_admission_evidence", inspect_spy,
    )
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    with pytest.raises(M.FreezeError, match="^floor-selection-rule-mismatch:"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )
    assert observed == [
        {
            "campaign_run_id": selected_id,
            "run_relpath": selected["run_relpath"],
            "manifest_sha256": selected["manifest_sha256"],
        },
        {
            "campaign_run_id": earlier_id,
            "run_relpath": earlier["run_relpath"],
            "manifest_sha256": earlier["manifest_sha256"],
        },
    ]


def test_v2_candidate_rejects_selected_certificate_path_second_mismatch(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    cert_path = (
        root / fixture["result_rel"].rsplit("/", 1)[0]
        / "launch_certificate.json"
    )
    cert = json.loads(cert_path.read_bytes())
    cert["started_utc"] = "2026-08-11T00:00:01+00:00"
    cert_path.write_bytes(V2FIX.canonical_bytes(cert))
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])

    with pytest.raises(
            M.FreezeError,
            match=(
                r"^floor-launch-certificate-invalid: .*started_utc.*"
                r"秒単位で不一致$"
            )):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


def test_v2_candidate_reads_selected_certificate_from_bound_run_dirfd(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    selected_run_dir = root / fixture["result_rel"].rsplit("/", 1)[0]
    anchored_run_dir = selected_run_dir.with_name(
        f"{selected_run_dir.name}-anchored"
    )
    attacker_run_dir = tmp_path / "attacker-selected-run"
    attacker_run_dir.mkdir()
    (attacker_run_dir / "launch_certificate.json").write_bytes(b"{}")
    original = M._capture_regular_nofollow_at
    swaps = []

    def capture_from_bound_dirfd(parent_fd, leaf, *, label, missing_ok=False):
        if label != "floor result launch certificate":
            return original(
                parent_fd, leaf, label=label, missing_ok=missing_ok,
            )
        selected_run_dir.rename(anchored_run_dir)
        selected_run_dir.symlink_to(attacker_run_dir, target_is_directory=True)
        try:
            swaps.append(leaf)
            return original(
                parent_fd, leaf, label=label, missing_ok=missing_ok,
            )
        finally:
            selected_run_dir.unlink()
            anchored_run_dir.rename(selected_run_dir)

    monkeypatch.setattr(
        M, "_capture_regular_nofollow_at", capture_from_bound_dirfd,
    )
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    document = M.build_v2_g1_candidate(
        floor_result_path=fixture["result_rel"],
        budget_path=fixture["budget_rel"], root=root,
    )
    assert swaps == ["launch_certificate.json"]
    assert document["floor_source"]["path"] == fixture["result_rel"]


def test_v2_candidate_enumerates_and_reads_earlier_run_through_bound_dirfds(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    selected_id = fixture["result_rel"].rsplit("/", 2)[-2]
    proto8 = selected_id.rsplit("-", 1)[1]
    earlier_id = f"20260810T235900Z-{proto8}"
    installed = _install_real_floor_selection_runs(fixture, [
        {"run_id": earlier_id},
        {"run_id": selected_id},
    ])
    namespace = root / fixture["result_rel"].rsplit("/", 2)[0]
    anchored_namespace = namespace.with_name(f"{namespace.name}-anchored")
    attacker_namespace = tmp_path / "attacker-namespace"
    attacker_namespace.mkdir()
    earlier_run_dir = root / "output" / installed[earlier_id]["run_relpath"]
    anchored_earlier = earlier_run_dir.with_name(f"{earlier_id}-anchored")
    attacker_run_dir = tmp_path / "attacker-earlier-run"
    attacker_run_dir.mkdir()
    (attacker_run_dir / "result.json").write_bytes(b"{}")
    original_listdir = os.listdir
    original_capture = M._capture_regular_nofollow_at
    observations = []

    def list_bound_namespace(namespace_fd):
        if type(namespace_fd) is not int:
            return original_listdir(namespace_fd)
        namespace.rename(anchored_namespace)
        namespace.symlink_to(attacker_namespace, target_is_directory=True)
        try:
            observations.append("namespace")
            return original_listdir(namespace_fd)
        finally:
            namespace.unlink()
            anchored_namespace.rename(namespace)

    def capture_from_bound_run(parent_fd, leaf, *, label, missing_ok=False):
        if label != "floor selection earlier result":
            return original_capture(
                parent_fd, leaf, label=label, missing_ok=missing_ok,
            )
        earlier_run_dir.rename(anchored_earlier)
        earlier_run_dir.symlink_to(attacker_run_dir, target_is_directory=True)
        try:
            observations.append("earlier-result")
            return original_capture(
                parent_fd, leaf, label=label, missing_ok=missing_ok,
            )
        finally:
            earlier_run_dir.unlink()
            anchored_earlier.rename(earlier_run_dir)

    monkeypatch.setattr(os, "listdir", list_bound_namespace)
    monkeypatch.setattr(M, "_capture_regular_nofollow_at", capture_from_bound_run)
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    with pytest.raises(M.FreezeError, match="^floor-selection-rule-mismatch:"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )
    assert observations == ["namespace", "earlier-result"]


@pytest.mark.parametrize("symlink_kind", ["run", "result"], ids=["run", "result"])
def test_v2_candidate_rejects_earlier_official_symlink(
        tmp_path, monkeypatch, symlink_kind):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    selected_rel = fixture["result_rel"]
    selected_run_id = selected_rel.rsplit("/", 2)[-2]
    proto8 = selected_run_id.rsplit("-", 1)[1]
    selected_run_dir = root / selected_rel.rsplit("/", 1)[0]
    earlier_run_dir = selected_run_dir.with_name(f"20260810T235900Z-{proto8}")
    if symlink_kind == "run":
        earlier_run_dir.symlink_to(selected_run_dir, target_is_directory=True)
    else:
        earlier_run_dir.mkdir()
        (earlier_run_dir / "result.json").symlink_to(root / selected_rel)
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])

    with pytest.raises(M.FreezeError, match="non-symlink"):
        M.build_v2_g1_candidate(
            floor_result_path=selected_rel,
            budget_path=fixture["budget_rel"], root=root,
        )


def test_v2_candidate_ignores_later_official_result_namespace_entry(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    selected_rel = fixture["result_rel"]
    selected_run_id = selected_rel.rsplit("/", 2)[-2]
    proto8 = selected_run_id.rsplit("-", 1)[1]
    later_id = f"20260811T000100Z-{proto8}"
    installed = _install_real_floor_selection_runs(fixture, [
        {"run_id": selected_run_id},
        {"run_id": later_id},
    ])
    later_rel = installed[later_id]["result_rel"]
    assert (root / later_rel).is_file()
    assert (root / later_rel.rsplit("/", 1)[0] / "manifest.json").is_file()
    assert (root / later_rel.rsplit("/", 1)[0] / "journal.jsonl").is_file()
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])

    document = M.build_v2_g1_candidate(
        floor_result_path=selected_rel,
        budget_path=fixture["budget_rel"], root=root,
    )
    assert document["floor_source"]["path"] == selected_rel


def test_v2_candidate_threads_receipt_derived_degraded_mode_to_floor_stats(
        tmp_path, monkeypatch):
    """M7: D の入口が old fixed True へ戻れば、この wiring assertion だけが赤になる。"""
    from orchestrator.campaign import s8b_floor_stats

    fixture = V2FIX.candidate_repository(tmp_path, M)
    _degrade_v2_candidate_repository(fixture)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    original = s8b_floor_stats.verify_floor_artifact_with_live_admission
    received_use_perf = []

    def verify_with_wiring_assertion(*args, **kwargs):
        assert kwargs["expected_use_perf"] is False
        received_use_perf.append(kwargs["expected_use_perf"])
        return original(*args, **kwargs)

    monkeypatch.setattr(
        s8b_floor_stats, "verify_floor_artifact_with_live_admission",
        verify_with_wiring_assertion,
    )

    document = M.build_v2_g1_candidate(
        floor_result_path=fixture["result_rel"],
        budget_path=fixture["budget_rel"],
        root=root,
    )

    assert received_use_perf == [False]
    assert frozenset(document) == M.V2_TOP_LEVEL_KEYS
    assert document["floor"]["by_holdout"]


def test_v2_candidate_rejects_result_manifest_degraded_evidence_mismatch(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    _degrade_v2_candidate_repository(fixture)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    result_path = root / fixture["result_rel"]
    result = json.loads(result_path.read_bytes())
    different_receipt = _perf_unavailable_receipt(marker=b"different-result")
    result["perf_preflight"] = different_receipt
    result["perf_observation"] = _perf_degraded_observation(different_receipt)
    result_path.write_bytes(V2FIX.canonical_bytes(result))

    with pytest.raises(
            M.FreezeError,
            match="^floor-admission-mismatch: result/manifest の perf evidence が不一致$"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )


def test_v2_candidate_budget_approval_compares_canonical_numeric_bytes(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    changed = copy.deepcopy(fixture["budget"])
    changed["total_bench_s"] = float(changed["total_bench_s"])
    (root / fixture["budget_rel"]).write_bytes(V2FIX.canonical_bytes(changed))

    with pytest.raises(
            M.FreezeError, match="budget-approval-budget-canonical-mismatch"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )


@pytest.mark.parametrize("field", ["total_bench_s", "per_holdout_bench_s"])
def test_v2_candidate_rejects_negative_zero_budget_field(
        tmp_path, monkeypatch, field):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    changed = copy.deepcopy(fixture["budget"])
    if field == "total_bench_s":
        changed[field] = -0.0
        reason = r"budget\.total_bench_s が有限非負数でない"
    else:
        holdout_id = sorted(changed[field])[0]
        changed[field][holdout_id] = -0.0
        reason = rf"budget\.per_holdout_bench_s\.{holdout_id} が有限非負数でない"
    (root / fixture["budget_rel"]).write_bytes(V2FIX.canonical_bytes(changed))

    with pytest.raises(M.FreezeError, match=reason):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )


def test_v2_candidate_none_pin_rejects_valid_inputs_without_output(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", None)

    with pytest.raises(M.FreezeError, match="^budget-approval-not-ratified$"):
        M.generate_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )
    assert not (root / M.V2_CANDIDATE_REL).exists()


def test_v2_candidate_rejects_floor_not_eligible_for_refreeze(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    result_path = root / fixture["result_rel"]
    result = json.loads(result_path.read_bytes())
    result["eligible_for_refreeze"] = False
    result_path.write_bytes(V2FIX.canonical_bytes(result))
    for path in (
        root / ".git/izanagi/s8b-holdout-admission-v1/claims"
    ).glob("*.claim"):
        claim = json.loads(path.read_bytes())
        claim["nondefault_seams"] = ["build_fn"]
        path.write_bytes(V2FIX.canonical_bytes(claim) + b"\n")

    with pytest.raises(M.FreezeError, match="eligible_for_refreeze が true でない"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )


def test_v2_candidate_rejects_reported_false_when_live_basis_is_eligible(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    result_path = root / fixture["result_rel"]
    result = json.loads(result_path.read_bytes())
    result["eligible_for_refreeze"] = False
    result_path.write_bytes(V2FIX.canonical_bytes(result))

    with pytest.raises(
        M.FreezeError,
        match="^floor-admission-mismatch: refreeze-eligibility-mismatch$",
    ):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


def test_v2_candidate_rejects_unreachable_floor_admission_root(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    admission_root = root / ".git/izanagi/s8b-holdout-admission-v1"
    admission_root.rename(admission_root.with_name("admission-unavailable"))

    with pytest.raises(M.FreezeError, match="^floor-admission-unverifiable:"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


def test_v2_candidate_rejects_floor_admission_claim_mismatch(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    claims = sorted(
        (root / ".git/izanagi/s8b-holdout-admission-v1/claims").glob("*.claim")
    )
    assert claims
    claims[0].write_bytes(b"{}\n")

    with pytest.raises(M.FreezeError, match="^floor-admission-mismatch:"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


def test_v2_candidate_rejects_reported_true_when_live_basis_is_disqualified(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    claims = sorted(
        (root / ".git/izanagi/s8b-holdout-admission-v1/claims").glob("*.claim")
    )
    assert claims
    for path in claims:
        claim = json.loads(path.read_bytes())
        claim["nondefault_seams"] = ["build_fn"]
        path.write_bytes(V2FIX.canonical_bytes(claim) + b"\n")

    with pytest.raises(
        M.FreezeError,
        match="^floor-admission-mismatch: refreeze-eligibility-mismatch$",
    ):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


def test_v2_candidate_rejects_sibling_manifest_bytes_mismatch(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    manifest_path = root / fixture["result_rel"].rsplit("/", 1)[0] / "manifest.json"
    manifest_path.write_bytes(b'{"changed":true}')

    with pytest.raises(
            M.FreezeError,
            match="^floor-admission-mismatch: result.manifest_sha256"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


def test_v2_candidate_rejects_completed_sessions_without_session_starts(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    run_dir = root / fixture["result_rel"].rsplit("/", 1)[0]
    journal_path = run_dir / "journal.jsonl"
    records = [
        json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines()
    ]
    journal_path.write_bytes(b"".join(
        V2FIX.canonical_bytes(record) + b"\n"
        for record in records if record["event"] != "session-start"
    ))

    with pytest.raises(
            M.FreezeError,
            match="^floor-admission-mismatch: session-start-coverage-mismatch$"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


def test_v2_candidate_rejects_result_only_session_throughput_tamper(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    result_path = root / fixture["result_rel"]
    result = json.loads(result_path.read_bytes())
    result["sessions"][0]["throughputs"][0] += 1.0
    result_path.write_bytes(V2FIX.canonical_bytes(result))

    with pytest.raises(
            M.FreezeError,
            match="^floor-admission-mismatch: journal sessions と result.sessions が不一致$"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


@pytest.mark.parametrize("manifest_kind", ["empty", "v2"])
def test_v2_candidate_rejects_semantically_invalid_manifest_with_consistent_evidence(
        tmp_path, monkeypatch, manifest_kind):
    fixture = V2FIX.candidate_repository(
        tmp_path, M, manifest_kind=manifest_kind,
    )
    root = fixture["root"]
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])

    with pytest.raises(
            M.FreezeError,
            match="^floor-admission-mismatch: sibling-manifest-invalid:"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


def test_v2_candidate_rejects_result_only_binary_and_swo_identity_tamper(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    result_path = root / fixture["result_rel"]
    result = json.loads(result_path.read_bytes())
    cell_id = next(
        key for key, record in result["binaries"].items()
        if record["configuration_id"] == "sort_best"
    )
    record = result["binaries"][cell_id]
    forged_sha256 = "f" * 64
    record["binary_sha256"] = forged_sha256
    record["bin_hash_short"] = forged_sha256[:16]
    record["sort_swo_oracle"]["binary_sha256"] = forged_sha256
    receipt = record["admission_receipt"]
    receipt["subject"]["binary_sha256"] = forged_sha256
    # Keep the result's receipt internally coherent so sibling comparison fires.
    receipt["proof"]["source_protection"]["binary_sha256"] = forged_sha256
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256")
    receipt["receipt_sha256"] = hashlib.sha256(
        V2FIX.canonical_bytes(unsigned)
    ).hexdigest()
    result_path.write_bytes(V2FIX.canonical_bytes(result))

    with pytest.raises(
            M.FreezeError,
            match="^floor-admission-mismatch: result.binaries が sibling manifest と不一致$"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


def test_v2_candidate_rejects_unreachable_sibling_manifest(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"])
    manifest_path = root / fixture["result_rel"].rsplit("/", 1)[0] / "manifest.json"
    manifest_path.rename(manifest_path.with_name("manifest-unavailable.json"))

    with pytest.raises(
            M.FreezeError,
            match="^floor-admission-unverifiable: sibling-manifest-unavailable"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"], root=root,
        )


def test_v2_candidate_rejects_closure_hit_absent_from_captured_head(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    untracked = root / "untracked-holdout.txt"
    untracked.write_bytes(V2FIX._holdout_hit_text(M, "rr80"))

    with pytest.raises(M.FreezeError, match="captured HEAD の blob として存在しない"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )


def test_v2_candidate_rejects_dirty_closure_without_pinned_diagnostic(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    rel = fixture["closure_paths"][0]
    changed = (root / rel).read_bytes() + b"worktree-drift\n"
    (root / rel).write_bytes(changed)

    with pytest.raises(
            M.FreezeError,
            match=r"measurement_closure path が captured HEAD と worktree で不一致"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )


@pytest.mark.parametrize(
    "output",
    [
        "output/s8b-freeze/holdout_freeze.v2.g1.json",
        "../outside.json",
        "/tmp/outside.json",
        "output//s8b-freeze-candidates/holdout_freeze.v2.g1.json",
        "output/s8b-freeze-candidates/../holdout_freeze.v2.g1.json",
    ],
)
def test_v2_candidate_output_gate_rejects_every_nonfixed_raw_path(tmp_path, output):
    root = tmp_path / "repo"
    root.mkdir()

    with pytest.raises(M.FreezeError):
        M._write_v2_candidate_create_only(root, output, b"{}")
    assert not (tmp_path / "outside.json").exists()


def test_v2_candidate_writer_creates_fixed_root_and_preserves_literal_bytes(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()

    assert M._canonical_bytes(_V2_CANONICAL_PROBE_DOCUMENT) == (
        _V2_WRITER_RAW_LITERAL[:-1]
    )
    assert hashlib.sha256(_V2_WRITER_RAW_LITERAL).hexdigest() == (
        _V2_WRITER_SHA256_LITERAL
    )
    assert _V2_WRITER_RAW_LITERAL.endswith(b"\n")
    M._write_v2_candidate_create_only(
        root, M.V2_CANDIDATE_REL, _V2_WRITER_RAW_LITERAL,
    )

    output = root / M.V2_CANDIDATE_REL
    assert output.read_bytes() == _V2_WRITER_RAW_LITERAL
    assert hashlib.sha256(output.read_bytes()).hexdigest() == (
        _V2_WRITER_SHA256_LITERAL
    )


def test_v2_candidate_output_gate_rejects_symlink_parent(tmp_path):
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "output").mkdir()
    (root / "output" / "s8b-freeze-candidates").symlink_to(outside)

    with pytest.raises(M.FreezeError, match="安全に新規作成できない"):
        M._write_v2_candidate_create_only(
            root, M.V2_CANDIDATE_REL, _V2_WRITER_RAW_LITERAL,
        )
    assert list(outside.iterdir()) == []


def test_v2_candidate_output_gate_rejects_existing_leaf_without_overwrite(
        tmp_path):
    root = tmp_path / "repo"
    leaf = root / M.V2_CANDIDATE_REL
    leaf.parent.mkdir(parents=True)
    leaf.write_bytes(b"existing")

    with pytest.raises(M.FreezeError, match="安全に新規作成できない"):
        M._write_v2_candidate_create_only(
            root, M.V2_CANDIDATE_REL, b"replacement",
        )
    assert leaf.read_bytes() == b"existing"


def test_v2_candidate_output_gate_rejects_symlink_parent_and_existing_leaf(tmp_path):
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "output").mkdir()
    (root / "output" / "s8b-freeze-candidates").symlink_to(outside)

    with pytest.raises(M.FreezeError, match="安全に新規作成できない"):
        M._write_v2_candidate_create_only(root, M.V2_CANDIDATE_REL, b"{}")
    assert list(outside.iterdir()) == []

    (root / "output" / "s8b-freeze-candidates").unlink()
    parent = root / "output" / "s8b-freeze-candidates"
    parent.mkdir()
    leaf = root / M.V2_CANDIDATE_REL
    leaf.write_bytes(b"existing")
    with pytest.raises(M.FreezeError, match="安全に新規作成できない"):
        M._write_v2_candidate_create_only(root, M.V2_CANDIDATE_REL, b"replacement")
    assert leaf.read_bytes() == b"existing"

    leaf.unlink()
    outside_leaf = outside / "existing"
    outside_leaf.write_bytes(b"outside")
    leaf.symlink_to(outside_leaf)
    with pytest.raises(M.FreezeError, match="安全に新規作成できない"):
        M._write_v2_candidate_create_only(root, M.V2_CANDIDATE_REL, b"replacement")
    assert outside_leaf.read_bytes() == b"outside"


def test_v2_candidate_cli_surface_has_no_approval_or_root_arguments():
    parser = M._parser()
    accepted = parser.parse_args([
        "generate-v2-candidate",
        "--floor-result", "result.json",
        "--budget", "budget.json",
    ])
    assert accepted.output == M.V2_CANDIDATE_REL
    for forbidden in ("--approver", "--approved-at", "--budget-approval", "--root"):
        with pytest.raises(SystemExit) as caught:
            parser.parse_args([
                "generate-v2-candidate",
                "--floor-result", "result.json",
                "--budget", "budget.json",
                forbidden, "value",
            ])
        assert caught.value.code == 2


from orchestrator.tests.growth_test_holds import enforce_held_functions  # noqa: E402
enforce_held_functions(globals(), __file__, plain_runner="none")
