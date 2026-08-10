# -*- coding: utf-8 -*-
"""T-143 RuleOps v1 の read-only / fail-closed 境界。

M1〜M12 は production 定数から期待外延を導出せず、各 test の literal pin と
単一の positive control で固定する。このファイルは pytest-only。
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "orchestrator"))
from tests import repo_tree_util  # noqa: E402

_TOOL = _REPO / "tools" / "ruleops.py"
_SPEC = importlib.util.spec_from_file_location("ruleops_test_target", _TOOL)
assert _SPEC and _SPEC.loader
R = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = R
_SPEC.loader.exec_module(R)
_RUN_TESTS_TOOL = _REPO / "tools" / "run_tests.py"
_RUN_TESTS_SPEC = importlib.util.spec_from_file_location(
    "ruleops_run_tests_target",
    _RUN_TESTS_TOOL,
)
assert _RUN_TESTS_SPEC and _RUN_TESTS_SPEC.loader
RT = importlib.util.module_from_spec(_RUN_TESTS_SPEC)
sys.modules[_RUN_TESTS_SPEC.name] = RT
_RUN_TESTS_SPEC.loader.exec_module(RT)

_ROOT_KEYS = {
    "schema_version", "authority", "default_effect", "candidates",
}
_TEST_CANDIDATE_KEYS = {
    "path", "kind", "target_blob", "rationale", "test_evidence",
}
_TEST_EVIDENCE_KEYS = {
    "replacement_guards", "replacement_nodes", "semantic_queries",
    "observed_hits", "pickaxe_events", "mutation_receipts",
}
_CHECK_OUTPUT_KEYS = {
    "structurally_valid", "candidate_count", "human_approved",
}
_INVENTORY_ROOT_KEYS = {
    "schema_version", "head", "object_format", "items", "skipped_non_utf8",
}
_INVENTORY_ITEM_KEYS = {
    "path", "kind", "mode", "blob", "bytes", "last_change_commit",
    "last_changed_at", "artifact_format", "authority_marker",
    "default_effect_marker",
}
_TYPED_MARKER = (
    '<!-- ruleops-insight: {"authority":"none",'
    '"default_effect":"no-state-change",'
    '"schema_version":"ruleops-insight/v1"} -->\n'
)
_PROCESS_DIAGNOSTIC_CHARS = 16_384


def _diagnostic_stream(value: str | bytes | None) -> str:
    if value is None:
        return "<not captured>"
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace")
    else:
        text = value
    if len(text) <= _PROCESS_DIAGNOSTIC_CHARS:
        return text
    omitted = len(text) - _PROCESS_DIAGNOSTIC_CHARS
    return (
        text[:_PROCESS_DIAGNOSTIC_CHARS]
        + f"\n... <truncated {omitted} characters from end>"
    )


def _run_checked(command, **kwargs):
    assert "check" not in kwargs
    result = subprocess.run(command, check=False, **kwargs)
    assert result.returncode == 0, (
        "child process failed\n"
        f"rc: {result.returncode}\n"
        f"command: {list(command)!r}\n"
        f"stdout:\n{_diagnostic_stream(result.stdout)}\n"
        f"stderr:\n{_diagnostic_stream(result.stderr)}"
    )
    return result


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run_checked(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        errors="replace",
        text=True,
    )


def _canonical(value) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_bytes(repo: Path, rel: str, payload: bytes) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _write_json(repo: Path, rel: str, value) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical(value))


def _commit(repo: Path, message: str = "fixture") -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _blob(repo: Path, rel: str) -> str:
    return _git(repo, "rev-parse", f"HEAD:{rel}").stdout.strip()


def _base_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "ruleops@example.invalid")
    _git(repo, "config", "user.name", "RuleOps Test")
    _write(
        repo,
        "orchestrator/tests/test_candidate.py",
        "def test_candidate_obsolete_sentinel():\n    assert True\n",
    )
    _write(
        repo,
        "orchestrator/tests/test_guard.py",
        "def test_guard():\n    assert 'obsolete sentinel'\n",
    )
    _write(
        repo,
        "orchestrator/tests/nested/test_hidden.py",
        "def test_hidden():\n    assert True\n",
    )
    _write(
        repo,
        "output/insights/source.md",
        _TYPED_MARKER + "# source\n",
    )
    _write(
        repo,
        "output/insights/report.md",
        _TYPED_MARKER + "# report\n\n"
        "derived from output/insights/source.md\n",
    )
    _write(
        repo,
        "output/insights/nested/note.md",
        _TYPED_MARKER + "# nested\n",
    )
    _write(repo, "output/reports/report.md", "# formal report, outside RuleOps\n")
    _write(repo, "output/campaigns/campaign.lock", "locked\n")
    _write(repo, "output/s8b-freeze/generation.json", "{}\n")
    _commit(repo)
    return repo


@pytest.fixture
def inventory_encoding_matrix_repo(tmp_path):
    repo = _base_repo(tmp_path)
    latin1_test = (
        b"# -*- coding: latin-1 -*-\n"
        b"label = 'caf\xe9'\n\n"
        b"def test_cell_amber():\n"
        b"    assert label\n"
    )
    rejected = {
        "orchestrator/tests/test_cell_amber.py": latin1_test,
        "output/insights/inventory-cells/alpha.py": b"\xff\n",
        "output/insights/inventory-cells/bravo.md": b"\xfe\xfe\n",
        "output/insights/inventory-cells/charlie.json": b"\x80abc\n",
        "output/insights/inventory-cells/delta.raw": b"abc\xc3\x28\n",
        "output/insights/inventory-cells/echo.sh": b"\xed\xa0\x80\n",
    }
    controls = {
        "orchestrator/tests/test_cell_cobalt.py": (
            b"def test_cell_cobalt():\n    assert True\n",
            "test",
            "python",
        ),
        "output/insights/inventory-cells/foxtrot.py": (
            b"def broken(:\n", "insight", "python",
        ),
        "output/insights/inventory-cells/golf.md": (
            b"# note\n", "insight", "markdown",
        ),
        "output/insights/inventory-cells/hotel.json": (
            b'\xef\xbb\xbf{"note":"bom"}\n', "insight", "json",
        ),
        "output/insights/inventory-cells/india.raw": (
            b"opaque\x00payload\n", "insight", "other",
        ),
        "output/insights/inventory-cells/kilo.md": (
            b"# memo\x00detail\n", "insight", "markdown",
        ),
        "output/insights/inventory-cells/juliet.sh": (
            b"", "insight", "shell",
        ),
    }
    assert len(set(rejected.values())) == len(rejected)
    for path, payload in rejected.items():
        with pytest.raises(UnicodeDecodeError):
            payload.decode("utf-8", "strict")
        _write_bytes(repo, path, payload)
    compile(latin1_test, "test_cell_amber.py", "exec")
    for path, (payload, _, _) in controls.items():
        payload.decode("utf-8", "strict")
        _write_bytes(repo, path, payload)
    _commit(repo, "encoding matrix")
    return {
        "repo": repo,
        "rejected": frozenset(rejected),
        "controls": {
            path: (kind, artifact_format)
            for path, (_, kind, artifact_format) in controls.items()
        },
        "inspect_target": "orchestrator/tests/test_cell_amber.py",
        "bom_json_control": "output/insights/inventory-cells/hotel.json",
        "nul_control": "output/insights/inventory-cells/india.raw",
        "nul_markdown_control": "output/insights/inventory-cells/kilo.md",
    }


def _empty_ledger():
    return {
        "authority": "none",
        "candidates": [],
        "default_effect": "no-state-change",
        "schema_version": "ruleops-candidates/v1",
    }


def _reviewed(rows):
    return [
        {**row, "rationale": "human review signal classified", "review": "relevant"}
        for row in rows
    ]


def _receipt(
    repo: Path,
    candidate_path: str,
    *,
    receipt_path: str = "output/insights/candidate-ruleops-receipt.json",
    guard_path: str = "orchestrator/tests/test_guard.py",
    nodeid: str = "orchestrator/tests/test_guard.py::test_guard",
) -> tuple[str, str]:
    document = {
        "advisory_only": True,
        "authority": "none",
        "baseline_rc": 0,
        "candidate_blob": _blob(repo, candidate_path),
        "candidate_excluded": True,
        "candidate_path": candidate_path,
        "default_effect": "no-state-change",
        "head": _git(repo, "rev-parse", "HEAD").stdout.strip(),
        "human_review_required": True,
        "mutants": [
            {
                "failed_nodes": [nodeid],
                "guard_path": guard_path,
                "status": "KILLED",
            },
        ],
        "restored_rc": 0,
        "review_state": "reviewed",
        "schema_version": "ruleops-mutation-receipt/v1",
    }
    _write_json(repo, receipt_path, document)
    _commit(repo, "receipt")
    return receipt_path, _blob(repo, receipt_path)


def _valid_test_ledger(
    repo: Path,
    *,
    commit_ledger: bool = False,
    receipt_path: str = "output/insights/candidate-ruleops-receipt.json",
):
    candidate_path = "orchestrator/tests/test_candidate.py"
    receipt_path, receipt_blob = _receipt(
        repo,
        candidate_path,
        receipt_path=receipt_path,
    )
    base_commit = _git(
        repo,
        "rev-list",
        "--max-parents=0",
        "HEAD",
    ).stdout.strip()
    candidate = {
        "kind": "test",
        "path": candidate_path,
        "rationale": "guard is duplicated and requires human ruling",
        "target_blob": _blob(repo, candidate_path),
        "test_evidence": {
            "mutation_receipts": [
                {"blob": receipt_blob, "path": receipt_path},
            ],
            "observed_hits": [
                {
                    "blob": _blob(repo, "orchestrator/tests/test_guard.py"),
                    "line": 2,
                    "path": "orchestrator/tests/test_guard.py",
                    "query": "obsolete sentinel",
                    "rationale": "literal fixture review",
                    "review": "relevant",
                },
            ],
            "pickaxe_events": [
                {
                    "commit": base_commit,
                    "query": "obsolete sentinel",
                    "rationale": "literal fixture history review",
                    "review": "relevant",
                },
            ],
            "replacement_guards": [
                {
                    "blob": _blob(repo, "orchestrator/tests/test_guard.py"),
                    "path": "orchestrator/tests/test_guard.py",
                },
            ],
            "replacement_nodes": [
                {
                    "blob": _blob(repo, "orchestrator/tests/test_guard.py"),
                    "nodeid": "orchestrator/tests/test_guard.py::test_guard",
                },
            ],
            "semantic_queries": ["obsolete sentinel"],
        },
    }
    ledger = _empty_ledger()
    ledger["candidates"] = [candidate]
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    if commit_ledger:
        _commit(repo, "candidate ledger")
    return ledger


def _valid_insight_ledger(repo: Path):
    candidate = {
        "kind": "insight",
        "path": "output/insights/report.md",
        "rationale": "literal derived-report fixture for human ruling",
        "target_blob": _blob(repo, "output/insights/report.md"),
        "insight_evidence": {
            "artifact_class": "derived-report",
            "observed_hits": [],
            "pickaxe_events": [],
            "source_artifacts": [
                {
                    "blob": _blob(repo, "output/insights/source.md"),
                    "path": "output/insights/source.md",
                },
            ],
        },
    }
    ledger = _empty_ledger()
    ledger["candidates"] = [candidate]
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    return ledger


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(_TOOL), *args, "--repo", str(repo)],
        capture_output=True,
    )


def test_checked_git_failure_reports_command_rc_stdout_and_stderr(
    tmp_path, monkeypatch,
):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_git = bin_dir / "git"
    fake_git.write_text(
        "#!/usr/bin/env python3\n"
        "import os\n"
        "os.write(1, b'diagnostic stdout sentinel: \\xff\\n')\n"
        "os.write(2, b'diagnostic stderr sentinel: \\xfe\\n')\n"
        "raise SystemExit(23)\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    monkeypatch.setenv(
        "PATH",
        str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
    )

    with pytest.raises(AssertionError) as caught:
        _git(tmp_path, "diagnostic-command-sentinel")

    message = str(caught.value)
    normalized_message = "\n".join(
        line.strip() for line in message.splitlines()
    )
    expected_command = [
        "git", "-C", str(tmp_path), "diagnostic-command-sentinel",
    ]
    assert "\nrc: 23\n" in normalized_message
    assert f"\ncommand: {expected_command!r}\n" in normalized_message
    assert (
        "\nstdout:\ndiagnostic stdout sentinel: \ufffd\n"
        in normalized_message
    )
    assert (
        "\nstderr:\ndiagnostic stderr sentinel: \ufffd\n"
        in normalized_message
    )
    assert "\ufffd" in message

    truncated = _diagnostic_stream(
        "stderr reason at head\n" + "x" * _PROCESS_DIAGNOSTIC_CHARS,
    )
    assert truncated.startswith("stderr reason at head\n")
    assert "<truncated " in truncated


def test_m1_m2_inventory_literal_scope_and_exact_keys(tmp_path):
    repo = _base_repo(tmp_path)
    inventory = R.build_inventory(repo)
    assert set(inventory) == _INVENTORY_ROOT_KEYS
    assert [item["path"] for item in inventory["items"]] == [
        "orchestrator/tests/test_candidate.py",
        "orchestrator/tests/test_guard.py",
        "output/insights/nested/note.md",
        "output/insights/report.md",
        "output/insights/source.md",
    ]
    assert all(set(item) == _INVENTORY_ITEM_KEYS for item in inventory["items"])
    assert {item["kind"] for item in inventory["items"]} == {"test", "insight"}
    assert not any("campaign" in item["path"] for item in inventory["items"])
    assert not any("s8b-freeze" in item["path"] for item in inventory["items"])
    assert not any("output/reports" in item["path"] for item in inventory["items"])


def test_inventory_ignores_symlink_and_gitlink_in_scope(tmp_path):
    repo = _base_repo(tmp_path)
    os.symlink("source.md", repo / "output/insights/link.md")
    _git(repo, "add", "output/insights/link.md")
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(
        repo,
        "update-index",
        "--add",
        "--cacheinfo",
        f"160000,{head},output/insights/gitlink",
    )
    _git(repo, "commit", "-qm", "nonregular scope entries")
    paths = [item["path"] for item in R.build_inventory(repo)["items"]]
    assert "output/insights/link.md" not in paths
    assert "output/insights/gitlink" not in paths


def test_inventory_non_utf8_skip_matrix_and_utf8_formats(
    inventory_encoding_matrix_repo,
):
    fixture = inventory_encoding_matrix_repo
    inventory = R.build_inventory(fixture["repo"])
    assert set(inventory) == _INVENTORY_ROOT_KEYS
    assert inventory["schema_version"] == "ruleops-inventory/v2"
    assert type(inventory["skipped_non_utf8"]) is int
    assert inventory["skipped_non_utf8"] == 6
    assert all(set(item) == _INVENTORY_ITEM_KEYS for item in inventory["items"])

    items = {item["path"]: item for item in inventory["items"]}
    assert fixture["rejected"].isdisjoint(items)
    assert set(fixture["controls"]) <= set(items)
    for path, (kind, artifact_format) in fixture["controls"].items():
        assert (items[path]["kind"], items[path]["artifact_format"]) == (
            kind,
            artifact_format,
        )
    bom_json = items[fixture["bom_json_control"]]
    assert (bom_json["authority_marker"], bom_json["default_effect_marker"]) == (
        None,
        None,
    )
    assert fixture["nul_control"] in items
    assert fixture["nul_markdown_control"] in items
    typed_insight = items["output/insights/source.md"]
    assert (
        typed_insight["authority_marker"],
        typed_insight["default_effect_marker"],
    ) == ("none", "no-state-change")


def test_inventory_non_utf8_counter_respects_selected_kind(
    inventory_encoding_matrix_repo,
):
    repo = inventory_encoding_matrix_repo["repo"]
    inventories = {
        kind: R.build_inventory(repo, kind=kind)
        for kind in ("all", "test", "insight")
    }
    assert {
        kind: inventory["skipped_non_utf8"]
        for kind, inventory in inventories.items()
    } == {"all": 6, "test": 1, "insight": 5}
    assert {
        item["kind"] for item in inventories["test"]["items"]
    } == {"test"}
    assert {
        item["kind"] for item in inventories["insight"]["items"]
    } == {"insight"}


def test_inventory_non_utf8_counter_tracks_same_path_content_transition(tmp_path):
    repo = _base_repo(tmp_path)
    path = "output/insights/transitions/quartz.raw"
    _write_bytes(repo, path, b"start\xff\n")
    _commit(repo, "opaque transition")

    opaque = R.build_inventory(repo)
    opaque_paths = {item["path"] for item in opaque["items"]}
    selected_count = len(opaque["items"]) + opaque["skipped_non_utf8"]
    assert opaque["skipped_non_utf8"] == 1
    assert path not in opaque_paths

    _write_bytes(repo, path, b"readable\x00control\n")
    _commit(repo, "readable transition")
    readable = R.build_inventory(repo)
    readable_paths = {item["path"] for item in readable["items"]}
    assert len(readable["items"]) + readable["skipped_non_utf8"] == selected_count
    assert readable["skipped_non_utf8"] == 0
    assert path in readable_paths

    _write_bytes(repo, path, b"end\xfe\n")
    _commit(repo, "opaque transition again")
    opaque_again = R.build_inventory(repo)
    opaque_again_paths = {item["path"] for item in opaque_again["items"]}
    assert (
        len(opaque_again["items"]) + opaque_again["skipped_non_utf8"]
        == selected_count
    )
    assert opaque_again["skipped_non_utf8"] == 1
    assert path not in opaque_again_paths


def test_inventory_non_utf8_counter_excludes_out_of_scope_and_nonregular(tmp_path):
    repo = _base_repo(tmp_path)
    assert R.build_inventory(repo)["skipped_non_utf8"] == 0

    _write_bytes(repo, "docs/quartz.bin", b"\xff\n")
    _write_bytes(repo, "output/campaigns/quartz.bin", b"\xfe\n")
    link_path = "output/insights/quartz-link.md"
    link_target = b"../quartz-\xff"
    with pytest.raises(UnicodeDecodeError):
        link_target.decode("utf-8", "strict")
    os.symlink(link_target, os.fsencode(repo / link_path))
    _git(repo, "add", "docs/quartz.bin", "output/campaigns/quartz.bin")
    _git(repo, "add", link_path)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(
        repo,
        "update-index",
        "--add",
        "--cacheinfo",
        f"160000,{head},output/insights/quartz-gitlink",
    )
    _git(repo, "commit", "-qm", "outside scope and nonregular entries")
    assert _run_checked(
        ["git", "-C", str(repo), "cat-file", "blob", f"HEAD:{link_path}"],
        capture_output=True,
    ).stdout == link_target
    inventory = R.build_inventory(repo)
    assert link_path not in {item["path"] for item in inventory["items"]}
    assert inventory["skipped_non_utf8"] == 0


def test_inventory_retains_oversize_valid_utf8_blob(tmp_path):
    repo = _base_repo(tmp_path)
    path = "output/insights/archive/sierra.json"
    payload = b'{"note":"' + (b"a" * R.MAX_LEDGER_BYTES) + b'"}\n'
    assert len(payload) > R.MAX_LEDGER_BYTES
    payload.decode("utf-8", "strict")
    json.loads(payload)
    _write_bytes(repo, path, payload)
    _commit(repo, "large inventory cell")

    inventory = R.build_inventory(repo)
    items = {item["path"]: item for item in inventory["items"]}
    assert path in items
    assert items[path]["bytes"] == len(payload)
    assert inventory["skipped_non_utf8"] == 0


def test_inventory_all_selected_non_utf8_succeeds_and_counts_paths(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "ruleops@example.invalid")
    _git(repo, "config", "user.name", "RuleOps Test")
    shared = b"same\xff\n"
    _write_bytes(repo, "output/insights/sample/amber.raw", shared)
    _write_bytes(repo, "output/insights/sample/cobalt.raw", shared)
    _write_bytes(
        repo,
        "orchestrator/tests/test_quartz_cell.py",
        b"# -*- coding: latin-1 -*-\nvalue = '\xe9'\n",
    )
    _commit(repo, "all selected opaque")
    assert _blob(repo, "output/insights/sample/amber.raw") == _blob(
        repo,
        "output/insights/sample/cobalt.raw",
    )

    result = _run_cli(repo, "inventory")
    assert result.returncode == 0
    inventory = json.loads(result.stdout)
    assert inventory["items"] == []
    assert inventory["skipped_non_utf8"] == 3
    assert inventory["schema_version"] == "ruleops-inventory/v2"


def test_inspect_non_utf8_target_fails_closed_without_traceback(
    inventory_encoding_matrix_repo,
):
    fixture = inventory_encoding_matrix_repo
    result = _run_cli(fixture["repo"], "inspect", fixture["inspect_target"])
    assert result.returncode == 2
    assert result.stdout == b""
    assert b"non-utf8" in result.stderr
    assert b"Traceback" not in result.stderr


def test_m3_dirty_worktree_does_not_change_head_inventory(tmp_path):
    repo = _base_repo(tmp_path)
    before = _canonical(R.build_inventory(repo))
    candidate_path = "orchestrator/tests/test_candidate.py"
    target = repo / candidate_path
    head_blob = _run_checked(
        ["git", "-C", str(repo), "cat-file", "blob", f"HEAD:{candidate_path}"],
        capture_output=True,
    ).stdout
    dirty_bytes = b"dirty worktree replacement\n"
    assert dirty_bytes != head_blob
    assert len(dirty_bytes) != len(head_blob)
    target.write_bytes(dirty_bytes)
    after = _canonical(R.build_inventory(repo))
    assert after == before


def test_inventory_is_byte_identical_and_path_sorted(tmp_path):
    repo = _base_repo(tmp_path)
    first = _canonical(R.build_inventory(repo))
    second = _canonical(R.build_inventory(repo))
    assert first == second
    parsed = json.loads(first)
    paths = [item["path"] for item in parsed["items"]]
    assert paths == sorted(paths)


def test_m4_exact_root_candidate_and_nested_key_literals(tmp_path):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo)
    assert set(ledger) == _ROOT_KEYS
    assert set(ledger["candidates"][0]) == _TEST_CANDIDATE_KEYS
    assert (
        set(ledger["candidates"][0]["test_evidence"])
        == _TEST_EVIDENCE_KEYS
    )
    invalid = copy.deepcopy(ledger)
    invalid["safe"] = False
    _write_json(repo, "docs/ruleops-candidates.json", invalid)
    with pytest.raises(R.RuleOpsError, match="unknown=.*safe"):
        R.validate_candidate_ledger(repo)


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        (
            b'{"authority":"none","authority":"none","candidates":[],"default_effect":"no-state-change","schema_version":"ruleops-candidates/v1"}\n',
            "duplicate-key",
        ),
        (b"\xff\n", "non-utf8"),
        (_canonical({**_empty_ledger(), "approved": False}), "schema-keys"),
    ],
)
def test_duplicate_nonutf8_unknown_ledger_fail_closed_without_traceback(
    tmp_path, raw, reason,
):
    repo = _base_repo(tmp_path)
    path = repo / "docs/ruleops-candidates.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    result = _run_cli(repo, "check", "--ledger", str(path))
    assert result.returncode == 2
    assert reason.encode() in result.stderr
    assert b"Traceback" not in result.stderr


def test_pretty_json_is_accepted_but_oversize_ledger_is_rejected(tmp_path):
    repo = _base_repo(tmp_path)
    _write(
        repo,
        "docs/ruleops-candidates.json",
        json.dumps(_empty_ledger(), indent=2) + "\n",
    )
    assert R.validate_candidate_ledger(repo)["candidate_count"] == 0
    (repo / "docs/ruleops-candidates.json").write_bytes(
        b" " * (1_048_576 + 1),
    )
    with pytest.raises(R.RuleOpsError, match="1048576"):
        R.validate_candidate_ledger(repo)


def test_oversize_ledger_and_receipt_reject_before_payload_read(
    tmp_path, monkeypatch,
):
    ledger = tmp_path / "oversize-ledger.json"
    with ledger.open("wb") as stream:
        stream.truncate(1_048_577)
    repo = _base_repo(tmp_path / "receipt")
    snapshot = R._capture_snapshot(repo)
    monkeypatch.setattr(
        R.os,
        "read",
        lambda *_args: (_ for _ in ()).throw(AssertionError("payload read")),
    )
    with pytest.raises(R.RuleOpsError) as caught:
        R._read_regular_file_bounded(
            ledger,
            label="oversize-ledger",
            max_bytes=1_048_576,
        )
    assert caught.value.reason == "oversize-json"

    fake_entry = R.TreeEntry(
        "100644",
        "blob",
        "0" * 40,
        262_145,
        "output/insights/oversize-receipt.json",
    )
    with pytest.raises(R.RuleOpsError) as caught:
        R._receipt_document(snapshot, fake_entry)
    assert caught.value.reason == "oversize-json"


@pytest.mark.parametrize(
    "ledger_rel",
    [
        "docs/ruleops-candidates.json",
        "docs/custom-ruleops-candidates.json",
    ],
)
def test_dirty_small_ledger_rejects_oversize_head_blob_before_blob_read(
    tmp_path, monkeypatch, ledger_rel,
):
    repo = _base_repo(tmp_path)
    oversized = repo / ledger_rel
    oversized.parent.mkdir(parents=True, exist_ok=True)
    with oversized.open("wb") as stream:
        stream.truncate(1_048_577)
    _commit(repo, "oversize tracked ledger blob")
    oversized.write_bytes(_canonical(_empty_ledger()))
    monkeypatch.setattr(
        R,
        "_blob",
        lambda *_args: (_ for _ in ()).throw(AssertionError("HEAD payload read")),
    )
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo, ledger_rel)
    assert caught.value.reason == "oversize-json"


def test_signal_and_candidate_cardinality_overflow_have_explicit_reasons(
    tmp_path, monkeypatch,
):
    repo = _base_repo(tmp_path)
    rows = [
        {
            "blob": _blob(repo, "orchestrator/tests/test_guard.py"),
            "line": index + 1,
            "path": "orchestrator/tests/test_guard.py",
            "query": "overflow",
        }
        for index in range(129)
    ]
    monkeypatch.setattr(R, "_observed_hits", lambda *_a, **_kw: (rows, []))
    monkeypatch.setattr(R, "_pickaxe", lambda *_a, **_kw: ([], []))
    with pytest.raises(R.RuleOpsError) as caught:
        R.inspect_target(repo, "orchestrator/tests/test_candidate.py", draft=True)
    assert caught.value.reason == "evidence-overflow"

    candidate = {
        "kind": "insight",
        "path": "output/insights/report.md",
        "rationale": "bounded cardinality",
        "target_blob": _blob(repo, "output/insights/report.md"),
        "insight_evidence": {
            "artifact_class": "derived-report",
            "observed_hits": [],
            "pickaxe_events": [],
            "source_artifacts": [],
        },
    }
    ledger = _empty_ledger()
    ledger["candidates"] = [copy.deepcopy(candidate) for _ in range(9)]
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == "candidate-limit"


def test_pickaxe_raw_history_is_cached_by_snapshot_token_before_control_filter(
    tmp_path, monkeypatch,
):
    repo = _base_repo(tmp_path)
    snapshot = R._capture_snapshot(repo)
    guard_path = "orchestrator/tests/test_guard.py"
    guard_entry = snapshot.entries[guard_path]
    calls = []
    original = R._git_read

    def recording(repo_path, subcommand, *args, **kwargs):
        if subcommand == "log" and any(
            isinstance(arg, str) and arg.startswith("-S")
            for arg in args
        ):
            calls.append(args)
        return original(repo_path, subcommand, *args, **kwargs)

    monkeypatch.setattr(R, "_git_read", recording)
    first, first_excluded = R._pickaxe(snapshot, ["obsolete sentinel"], {})
    second, second_excluded = R._pickaxe(
        snapshot,
        ["obsolete sentinel"],
        {guard_path: guard_entry.oid},
    )
    assert len(calls) == 1
    assert first and not first_excluded
    assert not second and second_excluded


def test_global_signal_token_budget_rejects_before_pickaxe_history(
    tmp_path, monkeypatch,
):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo)
    monkeypatch.setattr(R, "MAX_SIGNAL_TOKENS", 2)
    monkeypatch.setattr(
        R,
        "_pickaxe",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("history query must not run"),
        ),
    )
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == "signal-token-limit"


@pytest.mark.parametrize(
    ("ledger_name", "reason"),
    [("/tmp/outside.json", "unsafe-ledger"), ("../outside.json", "unsafe-path")],
)
def test_ledger_path_traversal_and_absolute_outside_rejected(
    tmp_path, ledger_name, reason,
):
    repo = _base_repo(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_bytes(_canonical(_empty_ledger()))
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo, ledger_name)
    assert caught.value.reason == reason


def test_symlink_ledger_rejected(tmp_path):
    repo = _base_repo(tmp_path)
    outside = repo / "outside.json"
    outside.write_bytes(_canonical(_empty_ledger()))
    ledger = repo / "docs/ruleops-candidates.json"
    ledger.parent.mkdir(parents=True)
    ledger.symlink_to(outside)
    with pytest.raises(R.RuleOpsError, match="symlink"):
        R.validate_candidate_ledger(repo)


def test_symlink_and_gitlink_candidate_targets_rejected(tmp_path):
    repo = _base_repo(tmp_path)
    os.symlink("source.md", repo / "output/insights/link.md")
    _git(repo, "add", "output/insights/link.md")
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(
        repo,
        "update-index",
        "--add",
        "--cacheinfo",
        f"160000,{head},output/insights/gitlink",
    )
    _git(repo, "commit", "-qm", "nonregular candidates")
    for path in ("output/insights/link.md", "output/insights/gitlink"):
        candidate = {
            "insight_evidence": {
                "artifact_class": "derived-report",
                "observed_hits": [],
                "pickaxe_events": [],
                "source_artifacts": [],
            },
            "kind": "insight",
            "path": path,
            "rationale": "must fail at target regular-file gate",
            "target_blob": _blob(repo, path),
        }
        ledger = _empty_ledger()
        ledger["candidates"] = [candidate]
        _write_json(repo, "docs/ruleops-candidates.json", ledger)
        with pytest.raises(R.RuleOpsError) as caught:
            R.validate_candidate_ledger(repo)
        assert caught.value.reason == "non-regular"


def test_blob_drift_and_kind_drift_each_rejected(tmp_path):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo)
    drift = copy.deepcopy(ledger)
    drift["candidates"][0]["target_blob"] = "0" * 40
    _write_json(repo, "docs/ruleops-candidates.json", drift)
    with pytest.raises(R.RuleOpsError, match="blob drift"):
        R.validate_candidate_ledger(repo)
    wrong_kind = copy.deepcopy(ledger)
    wrong_kind["candidates"][0]["kind"] = "insight"
    wrong_kind["candidates"][0]["insight_evidence"] = wrong_kind[
        "candidates"
    ][0].pop("test_evidence")
    _write_json(repo, "docs/ruleops-candidates.json", wrong_kind)
    with pytest.raises(R.RuleOpsError, match="kind/path"):
        R.validate_candidate_ledger(repo)


def test_m5_committed_nonempty_package_excludes_only_ledger_and_receipt(tmp_path):
    repo = _base_repo(tmp_path)
    _valid_test_ledger(repo, commit_ledger=True)
    result = R.validate_candidate_ledger(repo)
    assert result == {
        "candidate_count": 1,
        "human_approved": False,
        "structurally_valid": True,
    }
    inspected = R.inspect_target(
        repo,
        "orchestrator/tests/test_candidate.py",
        queries=["obsolete sentinel"],
        draft=True,
    )
    excluded_paths = {
        hit["path"]
        for hit in inspected["excluded_hits"]["observed_hits"]
    }
    assert "docs/ruleops-candidates.json" in excluded_paths
    assert "output/insights/candidate-ruleops-receipt.json" in excluded_paths


def test_inspect_draft_to_committed_receipt_and_nonempty_check_journey(tmp_path):
    repo = _base_repo(tmp_path)
    candidate_path = "orchestrator/tests/test_candidate.py"
    inspected = R.inspect_target(
        repo,
        candidate_path,
        queries=["obsolete sentinel"],
        draft=True,
    )
    root_commit = _git(
        repo,
        "rev-list",
        "--max-parents=0",
        "HEAD",
    ).stdout.strip()
    literal_observed = [
        {
            "blob": _blob(repo, "orchestrator/tests/test_guard.py"),
            "line": 2,
            "path": "orchestrator/tests/test_guard.py",
            "query": "obsolete sentinel",
        },
    ]
    literal_pickaxe = [
        {"commit": root_commit, "query": "obsolete sentinel"},
    ]
    assert inspected["observed_hits"] == literal_observed
    assert inspected["pickaxe_events"] == literal_pickaxe
    receipt = inspected["mutation_receipt_draft"]
    assert set(receipt) == {
        "advisory_only",
        "authority",
        "baseline_rc",
        "candidate_blob",
        "candidate_excluded",
        "candidate_path",
        "default_effect",
        "head",
        "human_review_required",
        "mutants",
        "restored_rc",
        "review_state",
        "schema_version",
    }
    receipt["review_state"] = "reviewed"
    receipt["mutants"] = [
        {
            "failed_nodes": ["orchestrator/tests/test_guard.py::test_guard"],
            "guard_path": "orchestrator/tests/test_guard.py",
            "status": "KILLED",
        },
    ]
    receipt_path = "output/insights/inspect-draft-receipt.json"
    _write_json(repo, receipt_path, receipt)
    _commit(repo, "committed advisory receipt")

    candidate = inspected["candidate_draft"]
    candidate["rationale"] = "inspect-derived draft completed by a human"
    evidence = candidate["test_evidence"]
    evidence["mutation_receipts"] = [
        {"blob": _blob(repo, receipt_path), "path": receipt_path},
    ]
    evidence["replacement_guards"] = [
        {
            "blob": _blob(repo, "orchestrator/tests/test_guard.py"),
            "path": "orchestrator/tests/test_guard.py",
        },
    ]
    evidence["replacement_nodes"] = [
        {
            "blob": _blob(repo, "orchestrator/tests/test_guard.py"),
            "nodeid": "orchestrator/tests/test_guard.py::test_guard",
        },
    ]
    evidence["observed_hits"] = _reviewed(literal_observed)
    evidence["pickaxe_events"] = _reviewed(literal_pickaxe)
    ledger = _empty_ledger()
    ledger["candidates"] = [candidate]
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    _commit(repo, "committed nonempty candidate package")
    result = _run_cli(repo, "check")
    assert result.returncode == 0, result.stderr.decode()
    assert json.loads(result.stdout) == {
        "candidate_count": 1,
        "human_approved": False,
        "structurally_valid": True,
    }


def test_ordinary_blob_reference_is_not_control_excluded(tmp_path):
    repo = _base_repo(tmp_path)
    _write(
        repo,
        "docs/consumer.md",
        "uses orchestrator/tests/test_candidate.py as a live consumer\n",
    )
    _commit(repo, "ordinary consumer")
    _valid_test_ledger(repo)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == "unresolved-observed-hit"


def test_m6_ledger_wide_candidate_cycle_rejected_before_signal_review(tmp_path):
    repo = _base_repo(tmp_path)
    _write(repo, "orchestrator/tests/test_other.py", "def test_other():\n    pass\n")
    _write(
        repo,
        "orchestrator/tests/test_second_guard.py",
        "def test_second_guard():\n    assert 'second sentinel'\n",
    )
    second_commit = _commit(repo, "independent second candidate material")
    first_path = "orchestrator/tests/test_candidate.py"
    second_path = "orchestrator/tests/test_other.py"
    second_node = second_path + "::test_other"
    first_receipt_path, first_receipt_blob = _receipt(
        repo,
        first_path,
        nodeid=second_node,
    )
    first_receipt_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    second_receipt_path, second_receipt_blob = _receipt(
        repo,
        second_path,
        receipt_path="output/insights/second-ruleops-receipt.json",
        guard_path="orchestrator/tests/test_second_guard.py",
        nodeid="orchestrator/tests/test_second_guard.py::test_second_guard",
    )
    base_commit = _git(
        repo,
        "rev-list",
        "--max-parents=0",
        "HEAD",
    ).stdout.strip()
    first = {
        "kind": "test",
        "path": first_path,
        "rationale": "independently valid first candidate",
        "target_blob": _blob(repo, first_path),
        "test_evidence": {
            "mutation_receipts": [
                {"blob": first_receipt_blob, "path": first_receipt_path},
            ],
            "observed_hits": [
                {
                    "blob": _blob(repo, "orchestrator/tests/test_guard.py"),
                    "line": 2,
                    "path": "orchestrator/tests/test_guard.py",
                    "query": "obsolete sentinel",
                    "rationale": "literal first candidate hit",
                    "review": "relevant",
                },
            ],
            "pickaxe_events": [
                {
                    "commit": base_commit,
                    "query": "obsolete sentinel",
                    "rationale": "literal first candidate history",
                    "review": "relevant",
                },
            ],
            "replacement_guards": [
                {
                    "blob": _blob(repo, "orchestrator/tests/test_guard.py"),
                    "path": "orchestrator/tests/test_guard.py",
                },
            ],
            "replacement_nodes": [
                {"blob": _blob(repo, second_path), "nodeid": second_node},
            ],
            "semantic_queries": ["obsolete sentinel"],
        },
    }
    second = {
        "kind": "test",
        "path": second_path,
        "rationale": "independently valid second candidate",
        "target_blob": _blob(repo, second_path),
        "test_evidence": {
            "mutation_receipts": [
                {"blob": second_receipt_blob, "path": second_receipt_path},
            ],
            "observed_hits": [
                {
                    "blob": first_receipt_blob,
                    "line": 1,
                    "path": first_receipt_path,
                    "query": "orchestrator/tests/test_other.py",
                    "rationale": "literal cross-candidate target reference",
                    "review": "relevant",
                },
                {
                    "blob": first_receipt_blob,
                    "line": 1,
                    "path": first_receipt_path,
                    "query": "test_other.py",
                    "rationale": "literal cross-candidate basename reference",
                    "review": "relevant",
                },
                {
                    "blob": _blob(repo, "orchestrator/tests/test_second_guard.py"),
                    "line": 2,
                    "path": "orchestrator/tests/test_second_guard.py",
                    "query": "second sentinel",
                    "rationale": "literal second candidate hit",
                    "review": "relevant",
                },
            ],
            "pickaxe_events": [
                {
                    "commit": first_receipt_commit,
                    "query": "orchestrator/tests/test_other.py",
                    "rationale": "literal cross-candidate target history",
                    "review": "relevant",
                },
                {
                    "commit": first_receipt_commit,
                    "query": "test_other.py",
                    "rationale": "literal cross-candidate basename history",
                    "review": "relevant",
                },
                {
                    "commit": second_commit,
                    "query": "second sentinel",
                    "rationale": "literal second candidate history",
                    "review": "relevant",
                },
            ],
            "replacement_guards": [
                {
                    "blob": _blob(repo, "orchestrator/tests/test_second_guard.py"),
                    "path": "orchestrator/tests/test_second_guard.py",
                },
            ],
            "replacement_nodes": [
                {
                    "blob": _blob(repo, "orchestrator/tests/test_second_guard.py"),
                    "nodeid": (
                        "orchestrator/tests/test_second_guard.py::test_second_guard"
                    ),
                },
            ],
            "semantic_queries": ["second sentinel"],
        },
    }
    ledger = _empty_ledger()
    ledger["candidates"] = [first, second]
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    snapshot = R._capture_snapshot(repo)
    for candidate in ledger["candidates"]:
        R._validate_test_evidence(
            candidate,
            snapshot,
            candidate_paths=frozenset(),
            ledger_path="docs/ruleops-candidates.json",
            ledger_controls={},
            ledger_receipt_paths=frozenset({
                first_receipt_path,
                second_receipt_path,
            }),
        )
    with pytest.raises(R.RuleOpsError, match="candidate を replacement"):
        R.validate_candidate_ledger(repo)


def test_candidate_cannot_be_source_or_control_artifact(tmp_path):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo)
    candidate = ledger["candidates"][0]
    candidate["test_evidence"]["mutation_receipts"][0] = {
        "blob": candidate["target_blob"],
        "path": candidate["path"],
    }
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    with pytest.raises(R.RuleOpsError, match="candidate を receipt"):
        R.validate_candidate_ledger(repo)


def test_m7_unresolved_observed_hit_is_single_rejection(tmp_path):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo)
    hits = ledger["candidates"][0]["test_evidence"]["observed_hits"]
    assert hits
    hits.pop()
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == "unresolved-observed-hit"


def test_unresolved_pickaxe_event_is_single_rejection(tmp_path):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo)
    events = ledger["candidates"][0]["test_evidence"]["pickaxe_events"]
    assert events
    events.pop()
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == "unresolved-pickaxe-event"


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda receipt: receipt.__setitem__("candidate_excluded", False), "receipt-target"),
        (lambda receipt: receipt.__setitem__("baseline_rc", 99), "receipt-guard-result"),
        (
            lambda receipt: receipt["mutants"][0].__setitem__("status", "SURVIVED"),
            "receipt-guard-result",
        ),
        (lambda receipt: receipt.__setitem__("advisory_only", False), "receipt-overclaim"),
    ],
)
def test_receipt_target_and_guard_observations_are_independently_required(
    tmp_path, mutation, reason,
):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo)
    receipt_path = repo / "output/insights/candidate-ruleops-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    mutation(receipt)
    _write_json(repo, "output/insights/candidate-ruleops-receipt.json", receipt)
    _commit(repo, "invalid advisory observation")
    ledger["candidates"][0]["test_evidence"]["mutation_receipts"][0]["blob"] = _blob(
        repo, "output/insights/candidate-ruleops-receipt.json",
    )
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == reason


def test_m8_duplicate_basename_is_not_a_hard_signal(tmp_path):
    repo = _base_repo(tmp_path)
    _write(
        repo,
        "output/insights/other/note.md",
        _TYPED_MARKER + "# other\n",
    )
    _write(
        repo,
        "docs/basename-consumer.md",
        "ambiguous basename note.md must not become a signal\n",
    )
    _commit(repo, "duplicate basename")
    inspected = R.inspect_target(repo, "output/insights/nested/note.md")
    assert not any(hit["query"] == "note.md" for hit in inspected["observed_hits"])
    assert not any(event["query"] == "note.md" for event in inspected["pickaxe_events"])


def test_resolved_relative_markdown_link_is_observed_signal(tmp_path):
    repo = _base_repo(tmp_path)
    _write(
        repo,
        "output/insights/consumer.md",
        "# consumer\n\n[derived report](report.md)\n",
    )
    _commit(repo, "relative link consumer")
    inspected = R.inspect_target(repo, "output/insights/report.md")
    assert any(
        hit["query"] == "output/insights/report.md"
        and hit["path"] == "output/insights/consumer.md"
        for hit in inspected["observed_hits"]
    )


def test_insight_source_pin_marker_and_residual_reference_are_structural(tmp_path):
    repo = _base_repo(tmp_path)
    ledger = _valid_insight_ledger(repo)
    assert R.validate_candidate_ledger(repo)["candidate_count"] == 1
    bad = copy.deepcopy(ledger)
    bad["candidates"][0]["insight_evidence"]["source_artifacts"][0]["blob"] = "0" * 40
    _write_json(repo, "docs/ruleops-candidates.json", bad)
    with pytest.raises(R.RuleOpsError, match="blob drift"):
        R.validate_candidate_ledger(repo)


@pytest.mark.parametrize(
    "invalid_prefix",
    [
        "# leading garbage\n",
        "> ",
        "```json\n",
    ],
)
def test_typed_insight_marker_must_start_at_byte_zero(
    tmp_path, invalid_prefix,
):
    repo = _base_repo(tmp_path)
    report = repo / "output/insights/report.md"
    report.write_text(
        invalid_prefix + _TYPED_MARKER + "output/insights/source.md\n",
        encoding="utf-8",
    )
    _commit(repo, "invalid marker position")
    _valid_insight_ledger(repo)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == "authority-marker"


def test_typed_insight_marker_rejects_duplicate_and_non_strict_json(tmp_path):
    cases = [
        _TYPED_MARKER + _TYPED_MARKER,
        (
            '<!-- ruleops-insight: {"authority":"none","authority":"none",'
            '"default_effect":"no-state-change",'
            '"schema_version":"ruleops-insight/v1"} -->\n'
        ),
        (
            '<!-- ruleops-insight: {"authority": "none",'
            '"default_effect":"no-state-change",'
            '"schema_version":"ruleops-insight/v1"} -->\n'
        ),
    ]
    for index, marker in enumerate(cases):
        case_root = tmp_path / f"case-{index}"
        repo = _base_repo(case_root)
        _write(
            repo,
            "output/insights/report.md",
            marker + "output/insights/source.md\n",
        )
        _commit(repo, "invalid strict marker")
        _valid_insight_ledger(repo)
        with pytest.raises(R.RuleOpsError) as caught:
            R.validate_candidate_ledger(repo)
        assert caught.value.reason == "authority-marker"


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("rationale", " \t ", "control-character"),
        ("rationale", "   ", "empty-text"),
        ("query", "  ", "empty-text"),
        ("query", "bad\nquery", "control-character"),
    ],
)
def test_human_rationale_and_query_require_stripped_control_free_text(
    tmp_path, field, value, reason,
):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo)
    candidate = ledger["candidates"][0]
    if field == "rationale":
        candidate["rationale"] = value
    else:
        candidate["test_evidence"]["semantic_queries"][0] = value
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == reason


def test_missing_replacement_symbol_is_rejected_by_ast(tmp_path):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo)
    ledger["candidates"][0]["test_evidence"]["replacement_nodes"][0]["nodeid"] = (
        "orchestrator/tests/test_guard.py::does_not_exist"
    )
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == "node-missing"


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (
            lambda receipt: receipt["mutants"][0].__setitem__(
                "guard_path", "tools/check_docs.py",
            ),
            "receipt-guard-mismatch",
        ),
        (
            lambda receipt: receipt["mutants"][0].__setitem__(
                "failed_nodes",
                ["orchestrator/tests/test_guard.py::other_node"],
            ),
            "receipt-node-mismatch",
        ),
        (
            lambda receipt: receipt.__setitem__("review_state", "pending"),
            "receipt-review",
        ),
        (
            lambda receipt: receipt.__setitem__(
                "candidate_path", "orchestrator/tests/test_guard.py",
            ),
            "receipt-target",
        ),
    ],
)
def test_receipt_is_cross_checked_with_candidate_evidence(
    tmp_path, mutation, reason,
):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo)
    receipt_rel = "output/insights/candidate-ruleops-receipt.json"
    receipt = json.loads((repo / receipt_rel).read_text(encoding="utf-8"))
    mutation(receipt)
    _write_json(repo, receipt_rel, receipt)
    _commit(repo, "receipt mismatch")
    ledger["candidates"][0]["test_evidence"]["mutation_receipts"][0]["blob"] = _blob(
        repo,
        receipt_rel,
    )
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == reason


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("missing", "receipt-head-missing"),
        ("non-ancestor", "receipt-head-non-ancestor"),
        ("candidate-blob", "receipt-candidate-blob"),
        ("later-unrelated", "receipt-epoch-path"),
    ],
)
def test_receipt_head_epoch_rejects_each_invalid_boundary(
    tmp_path, case, reason,
):
    repo = _base_repo(tmp_path)
    original_branch = _git(
        repo,
        "rev-parse",
        "--abbrev-ref",
        "HEAD",
    ).stdout.strip()
    root = _git(repo, "rev-parse", "HEAD").stdout.strip()
    unrelated_head = None
    if case == "non-ancestor":
        _git(repo, "checkout", "-qb", "unrelated-receipt-head", root)
        _write(repo, "sibling.txt", "sibling history\n")
        unrelated_head = _commit(repo, "unrelated sibling")
        _git(repo, "checkout", "-q", original_branch)
    if case == "candidate-blob":
        _write(
            repo,
            "orchestrator/tests/test_candidate.py",
            "def test_candidate_obsolete_sentinel():\n    assert 1 == 1\n",
        )
        _commit(repo, "candidate blob changed before receipt")
    ledger = _valid_test_ledger(repo)
    receipt_rel = "output/insights/candidate-ruleops-receipt.json"
    if case == "later-unrelated":
        _write(repo, "unrelated-after-receipt.txt", "not receipt or ledger\n")
        _commit(repo, "unrelated change after receipt head")
    else:
        receipt = json.loads((repo / receipt_rel).read_text(encoding="utf-8"))
        if case == "missing":
            receipt["head"] = "f" * 40
        elif case == "non-ancestor":
            assert unrelated_head is not None
            receipt["head"] = unrelated_head
        else:
            receipt["head"] = root
        _write_json(repo, receipt_rel, receipt)
        _commit(repo, f"{case} receipt head")
        ledger["candidates"][0]["test_evidence"]["mutation_receipts"][0]["blob"] = (
            _blob(repo, receipt_rel)
        )
        _write_json(repo, "docs/ruleops-candidates.json", ledger)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == reason


def test_receipt_epoch_rejects_changed_then_restored_unrelated_path(tmp_path):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo)
    (repo / "docs/ruleops-candidates.json").unlink()
    unrelated = repo / "unrelated-between-receipt-and-ledger.txt"
    unrelated.write_text("temporary unrelated bytes\n", encoding="utf-8")
    _commit(repo, "unrelated path changed")
    unrelated.unlink()
    _commit(repo, "unrelated path restored")
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    _commit(repo, "receipt package ledger")

    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == "receipt-epoch-path"


def test_receipt_epoch_path_union_exposes_rename_copy_and_merge(tmp_path):
    repo = _base_repo(tmp_path)
    receipt_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    old_path = repo / "output/reports/report.md"
    renamed_path = repo / "output/reports/renamed.md"
    copied_path = repo / "output/reports/copied.md"
    old_path.rename(renamed_path)
    _commit(repo, "rename unrelated epoch path")
    shutil.copy2(renamed_path, copied_path)
    _commit(repo, "copy unrelated epoch path")
    original_branch = _git(
        repo,
        "rev-parse",
        "--abbrev-ref",
        "HEAD",
    ).stdout.strip()
    _git(repo, "checkout", "-qb", "receipt-epoch-side")
    _write(repo, "merge-only-unrelated.txt", "side branch epoch bytes\n")
    _commit(repo, "side branch unrelated epoch path")
    _git(repo, "checkout", "-q", original_branch)
    _git(repo, "merge", "--no-ff", "-qm", "merge epoch side", "receipt-epoch-side")

    snapshot = R._capture_snapshot(repo)
    changed = R._receipt_epoch_changed_paths(snapshot, receipt_head)
    assert {
        "output/reports/report.md",
        "output/reports/renamed.md",
        "output/reports/copied.md",
        "merge-only-unrelated.txt",
    } <= changed


def test_m9_check_output_exact_keys_and_forbidden_claims_absent(tmp_path):
    repo = _base_repo(tmp_path)
    _write_json(repo, "docs/ruleops-candidates.json", _empty_ledger())
    result = _run_cli(
        repo,
        "check",
        "--ledger",
        str(repo / "docs/ruleops-candidates.json"),
    )
    assert result.returncode == 0, result.stderr.decode()
    output = json.loads(result.stdout)
    assert set(output) == _CHECK_OUTPUT_KEYS
    assert output == {
        "candidate_count": 0,
        "human_approved": False,
        "structurally_valid": True,
    }
    assert not ({"safe", "eligible", "approved"} & set(output))


@pytest.mark.parametrize("command", ["delete", "move", "apply", "archive"])
def test_m11_cli_command_closed_set(command, tmp_path):
    repo = _base_repo(tmp_path)
    result = subprocess.run(
        [sys.executable, str(_TOOL), command, "--repo", str(repo)],
        capture_output=True,
    )
    assert result.returncode == 2
    assert result.stderr.startswith(b"ruleops: cli-args: ")
    assert b"Traceback" not in result.stderr


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["inspect"],
        ["inventory", "--kind", "unknown"],
        ["check", "--unknown-option"],
    ],
)
def test_all_argparse_failures_use_stable_cli_args_envelope(argv):
    result = subprocess.run(
        [sys.executable, str(_TOOL), *argv],
        capture_output=True,
    )
    assert result.returncode == 2
    assert result.stderr.startswith(b"ruleops: cli-args: ")
    assert b"Traceback" not in result.stderr


def test_git_read_closed_set_and_environment_scrub(tmp_path, monkeypatch):
    repo = _base_repo(tmp_path)
    poison = tmp_path / "poison"
    poison.mkdir()
    monkeypatch.setenv("GIT_DIR", str(poison))
    monkeypatch.setenv("GIT_WORK_TREE", str(poison))
    monkeypatch.setenv("GIT_NO_LAZY_FETCH", "0")
    assert R.build_inventory(repo)["items"]
    assert R._git_env()["GIT_NO_LAZY_FETCH"] == "1"
    with pytest.raises(R.RuleOpsError, match="closed set"):
        R._git_read(repo, "status", "--short")


def test_missing_promised_head_blob_fails_without_fetch_or_git_mutation(
    tmp_path,
    monkeypatch,
):
    repo = _base_repo(tmp_path)
    promised_path = "orchestrator/tests/test_candidate.py"
    promised_blob = _blob(repo, promised_path)
    sentinel = tmp_path / "promisor-helper-ran"
    helper = repo / "poison-promisor-helper.sh"
    helper.write_text(
        f"#!/bin/sh\n: > '{sentinel}'\nexit 91\n",
        encoding="utf-8",
    )
    helper.chmod(0o755)
    _git(repo, "config", "remote.origin.url", f"ext::{helper}")
    _git(repo, "config", "remote.origin.promisor", "true")
    _git(repo, "config", "remote.origin.partialclonefilter", "blob:none")
    _git(repo, "config", "extensions.partialClone", "origin")
    _git(repo, "config", "protocol.ext.allow", "always")
    loose_blob = repo / ".git" / "objects" / promised_blob[:2] / promised_blob[2:]
    assert not (repo / ".git/shallow").exists()
    assert loose_blob.is_file()
    loose_blob.unlink()
    head_entry = _git(repo, "ls-tree", "HEAD", "--", promised_path).stdout
    assert head_entry == f"100644 blob {promised_blob}\t{promised_path}\n"

    def git_state():
        state = {}
        git_dir = repo / ".git"
        for path in sorted(git_dir.rglob("*")):
            relative = path.relative_to(git_dir).as_posix()
            if path.is_symlink():
                state[relative] = ("symlink", os.readlink(path))
            elif path.is_file():
                state[relative] = ("file", path.read_bytes())
            elif path.is_dir():
                state[relative] = ("dir", None)
        return state

    monkeypatch.setenv("GIT_NO_LAZY_FETCH", "0")
    before = git_state()
    with pytest.raises(R.RuleOpsError) as caught:
        R.build_inventory(repo)
    after = git_state()

    assert caught.value.reason in {"bad-integer", "git-failed"}
    assert not sentinel.exists()
    assert after == before
    assert not loose_blob.exists()


def test_poisoned_local_git_signature_diff_textconv_and_recurse_helpers_never_run(
    tmp_path,
):
    repo = _base_repo(tmp_path)
    sentinel = tmp_path / "poison-helper-ran"
    helper = tmp_path / "poison-helper.sh"
    helper.write_text(
        f"#!/bin/sh\n: > '{sentinel}'\nexit 91\n",
        encoding="utf-8",
    )
    helper.chmod(0o755)
    _write(repo, ".gitattributes", "* diff=poison\n")
    _commit(repo, "poison attributes")
    tree = _git(repo, "rev-parse", "HEAD^{tree}").stdout.strip()
    parent = _git(repo, "rev-parse", "HEAD").stdout.strip()
    commit_raw = (
        f"tree {tree}\n"
        f"parent {parent}\n"
        "author RuleOps Test <ruleops@example.invalid> 1 +0000\n"
        "committer RuleOps Test <ruleops@example.invalid> 1 +0000\n"
        "gpgsig -----BEGIN PGP SIGNATURE-----\n"
        " fake-signature\n"
        " -----END PGP SIGNATURE-----\n"
        "\npoisoned local config fixture\n"
    ).encode("ascii")
    signed = _run_checked(
        ["git", "-C", str(repo), "hash-object", "-t", "commit", "-w", "--stdin"],
        input=commit_raw,
        capture_output=True,
    ).stdout.decode("ascii").strip()
    _git(repo, "update-ref", "HEAD", signed)
    for key, value in (
        ("log.showSignature", "true"),
        ("gpg.program", str(helper)),
        ("diff.external", str(helper)),
        ("diff.poison.command", str(helper)),
        ("diff.poison.textconv", str(helper)),
        ("submodule.recurse", "true"),
        ("grep.recurseSubmodules", "true"),
    ):
        _git(repo, "config", key, value)
    inspected = R.inspect_target(
        repo,
        "orchestrator/tests/test_candidate.py",
        queries=["obsolete sentinel"],
    )
    assert inspected["observed_hits"]
    assert not sentinel.exists()


def test_all_epoch_queries_use_captured_oid_not_head_literal(tmp_path, monkeypatch):
    repo = _base_repo(tmp_path)
    captured = _git(repo, "rev-parse", "HEAD").stdout.strip()
    calls = []
    original = R._git_read

    def recording(repo_path, subcommand, *args, **kwargs):
        calls.append((subcommand, args))
        return original(repo_path, subcommand, *args, **kwargs)

    monkeypatch.setattr(R, "_git_read", recording)
    R.inspect_target(
        repo,
        "orchestrator/tests/test_candidate.py",
        queries=["obsolete sentinel"],
    )
    epoch_calls = [
        (subcommand, args)
        for subcommand, args in calls
        if subcommand in {"ls-tree", "grep", "log"}
    ]
    assert epoch_calls
    for subcommand, args in epoch_calls:
        assert captured in args, (subcommand, args)
        assert "HEAD" not in args, (subcommand, args)


def test_head_movement_before_emit_fails_closed(tmp_path, monkeypatch):
    repo = _base_repo(tmp_path)
    original = R._git_text
    seen = 0

    def moving(repo_path, subcommand, *args):
        nonlocal seen
        value = original(repo_path, subcommand, *args)
        if subcommand == "rev-parse" and args == ("HEAD",):
            seen += 1
            if seen == 2:
                return "f" * 40
        return value

    monkeypatch.setattr(R, "_git_text", moving)
    with pytest.raises(R.RuleOpsError) as caught:
        R.build_inventory(repo)
    assert caught.value.reason == "head-moved"


@pytest.mark.parametrize(
    ("boundary_call", "changed_value", "reason"),
    [
        (
            ("rev-parse", "--is-shallow-repository"),
            "true",
            "shallow-repo",
        ),
        (
            ("for-each-ref", "--format=%(refname)", "refs/replace/"),
            "refs/replace/mid-query",
            "replace-refs",
        ),
    ],
)
def test_history_boundary_change_before_emit_fails_with_unchanged_head(
    tmp_path, monkeypatch, boundary_call, changed_value, reason,
):
    repo = _base_repo(tmp_path)
    original = R._git_text
    seen = 0

    def changing(repo_path, subcommand, *args):
        nonlocal seen
        value = original(repo_path, subcommand, *args)
        if (subcommand, *args) == boundary_call:
            seen += 1
            if seen == 2:
                return changed_value
        return value

    monkeypatch.setattr(R, "_git_text", changing)
    with pytest.raises(R.RuleOpsError) as caught:
        R.build_inventory(repo)
    assert caught.value.reason == reason
    assert seen == 2


def test_graft_created_before_emit_fails_with_unchanged_head(
    tmp_path, monkeypatch,
):
    repo = _base_repo(tmp_path)
    original = R._git_text
    seen = 0

    def changing(repo_path, subcommand, *args):
        nonlocal seen
        value = original(repo_path, subcommand, *args)
        if (subcommand, *args) == ("rev-parse", "--git-path", "info/grafts"):
            seen += 1
            if seen == 2:
                grafts = repo / ".git/info/grafts"
                grafts.parent.mkdir(parents=True, exist_ok=True)
                grafts.write_text(
                    _git(repo, "rev-parse", "HEAD").stdout.strip() + "\n",
                    encoding="ascii",
                )
        return value

    monkeypatch.setattr(R, "_git_text", changing)
    with pytest.raises(R.RuleOpsError) as caught:
        R.build_inventory(repo)
    assert caught.value.reason == "grafts"
    assert seen == 2


def test_metacharacter_control_path_is_literal_and_does_not_hide_neighbor(
    tmp_path,
):
    repo = _base_repo(tmp_path)
    metachar_receipt = "output/insights/receipt[?]*.json"
    _write(
        repo,
        "output/insights/receipta.json",
        "ordinary consumer: orchestrator/tests/test_candidate.py\n",
    )
    _commit(repo, "neighbor matching a glob-shaped control path")
    ledger = _valid_test_ledger(repo, receipt_path=metachar_receipt)
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == "unresolved-observed-hit"


def test_control_path_old_noncontrol_history_remains_review_required(tmp_path):
    repo = _base_repo(tmp_path)
    receipt_path = "output/insights/candidate-ruleops-receipt.json"
    _write(repo, receipt_path, "obsolete sentinel\n")
    _commit(repo, "ordinary predecessor at future control path")
    _valid_test_ledger(repo)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == "unresolved-pickaxe-event"


def test_ledger_candidate_alias_is_rejected_before_control_privilege(tmp_path):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo)
    alias = "orchestrator/tests/test_candidate.py"
    (repo / alias).write_bytes(_canonical(ledger))
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo, alias)
    assert caught.value.reason == "ledger-candidate-alias"


@pytest.mark.parametrize("evidence_kind", ["receipt", "guard", "node", "source"])
def test_dirty_custom_ledger_cannot_alias_any_evidence_path(
    tmp_path, evidence_kind,
):
    repo = _base_repo(tmp_path)
    if evidence_kind == "source":
        ledger = _valid_insight_ledger(repo)
        alias = "output/insights/source.md"
    else:
        if evidence_kind == "node":
            node_module = "orchestrator/tests/test_replacement_node.py"
            _write(
                repo,
                node_module,
                "def test_replacement_node():\n    assert True\n",
            )
            _commit(repo, "separate replacement node module")
        ledger = _valid_test_ledger(repo)
        evidence = ledger["candidates"][0]["test_evidence"]
        if evidence_kind == "receipt":
            alias = evidence["mutation_receipts"][0]["path"]
        elif evidence_kind == "guard":
            alias = evidence["replacement_guards"][0]["path"]
        else:
            alias = node_module
            nodeid = node_module + "::test_replacement_node"
            evidence["replacement_nodes"] = [
                {"blob": _blob(repo, node_module), "nodeid": nodeid},
            ]
            receipt_rel = evidence["mutation_receipts"][0]["path"]
            receipt = json.loads((repo / receipt_rel).read_text(encoding="utf-8"))
            receipt["mutants"][0]["failed_nodes"] = [nodeid]
            _write_json(repo, receipt_rel, receipt)
            _commit(repo, "receipt pins separate replacement node")
            evidence["mutation_receipts"][0]["blob"] = _blob(repo, receipt_rel)
    _write_json(repo, alias, ledger)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo, alias)
    assert caught.value.reason == "ledger-evidence-alias"


def test_separate_dirty_custom_ledger_remains_valid_positive_control(tmp_path):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo)
    custom = "docs/custom-ruleops-candidates.json"
    _write_json(repo, custom, ledger)
    assert R.validate_candidate_ledger(repo, custom) == {
        "candidate_count": 1,
        "human_approved": False,
        "structurally_valid": True,
    }


def test_dirty_tracked_ledger_is_not_a_control_artifact(tmp_path):
    repo = _base_repo(tmp_path)
    ledger = _valid_test_ledger(repo, commit_ledger=True)
    ledger["candidates"][0]["rationale"] += " dirty draft"
    _write_json(repo, "docs/ruleops-candidates.json", ledger)
    with pytest.raises(R.RuleOpsError) as caught:
        R.validate_candidate_ledger(repo)
    assert caught.value.reason == "unresolved-observed-hit"


def test_m12_replace_ref_rejected(tmp_path):
    repo = _base_repo(tmp_path)
    _write(repo, "extra.txt", "second\n")
    second = _commit(repo, "second")
    first = _git(repo, "rev-parse", "HEAD^").stdout.strip()
    _git(repo, "replace", first, second)
    with pytest.raises(R.RuleOpsError) as caught:
        R.build_inventory(repo)
    assert caught.value.reason == "replace-refs"


def test_m12_grafts_rejected(tmp_path):
    repo = _base_repo(tmp_path)
    grafts = repo / ".git/info/grafts"
    grafts.parent.mkdir(parents=True, exist_ok=True)
    grafts.write_text(_git(repo, "rev-parse", "HEAD").stdout.strip() + "\n", encoding="ascii")
    with pytest.raises(R.RuleOpsError) as caught:
        R.build_inventory(repo)
    assert caught.value.reason == "grafts"


def test_m12_shallow_repo_rejected(tmp_path):
    source = _base_repo(tmp_path / "source")
    _write(source, "second.txt", "second\n")
    _commit(source, "second")
    shallow = tmp_path / "shallow"
    _run_checked(
        ["git", "clone", "-q", "--depth", "1", source.as_uri(), str(shallow)],
        capture_output=True,
    )
    with pytest.raises(R.RuleOpsError) as caught:
        R.build_inventory(shallow)
    assert caught.value.reason == "shallow-repo"


def test_real_checkout_independent_maximum_package_and_runner_preflight(
    tmp_path,
):
    def inventory_action():
        inventory_run = _run_checked(
            [
                sys.executable,
                str(_TOOL),
                "inventory",
                "--repo",
                str(_REPO),
            ],
            capture_output=True,
        )
        inventory = json.loads(inventory_run.stdout)
        assert set(inventory) == _INVENTORY_ROOT_KEYS
        assert inventory["items"]
        assert any(
            item["path"] == "orchestrator/tests/test_plain_runner_coverage.py"
            for item in inventory["items"]
        )
        assert all(
            item["kind"] == "test"
            if item["path"].startswith("orchestrator/tests/")
            else item["kind"] == "insight"
            for item in inventory["items"]
        )

    # uall snapshot は既存 untracked dir 内の追加も拒否し、受理集合を狭める D63 強化。
    repo_tree_util.assert_repo_tree_unchanged(_REPO, inventory_action)

    checkout = tmp_path / "real-checkout"
    _run_checked(
        ["git", "clone", "-q", "--no-local", str(_REPO), str(checkout)],
        capture_output=True,
    )
    _git(checkout, "config", "user.email", "ruleops@example.invalid")
    _git(checkout, "config", "user.name", "RuleOps Test")
    (checkout / "tools").mkdir(exist_ok=True)
    shutil.copy2(_TOOL, checkout / "tools/ruleops.py")
    controlled = []
    for index in range(2):
        candidate_path = (
            f"orchestrator/tests/test_ruleops_e2e_candidate_{index}.py"
        )
        query = f"ruleops-e2e-independent-signal-{index}"
        _write(
            checkout,
            candidate_path,
            f'CONTROLLED_SIGNAL = "{query}"\n\n'
            f"def test_ruleops_e2e_candidate_{index}():\n"
            "    assert CONTROLLED_SIGNAL\n",
        )
        controlled.append((candidate_path, query))
    candidate_commit = _commit(
        checkout,
        "controlled RuleOps candidates and production tool",
    )
    target_blobs = {
        path: _blob(checkout, path)
        for path, _query in controlled
    }
    first_path, first_query = controlled[0]
    grep = _git(
        checkout,
        "grep",
        "-n",
        "-F",
        first_query,
        "HEAD",
        "--",
        first_path,
    ).stdout
    assert grep == f"HEAD:{first_path}:1:CONTROLLED_SIGNAL = \"{first_query}\"\n"
    independent_observed = [{
        "blob": target_blobs[first_path],
        "line": 1,
        "path": first_path,
        "query": first_query,
    }]
    history = _git(
        checkout,
        "log",
        "--format=%H",
        f"-S{first_query}",
        "HEAD",
        "--",
        first_path,
    ).stdout.splitlines()
    assert history == [candidate_commit]
    independent_pickaxe = [{
        "commit": candidate_commit,
        "query": first_query,
    }]
    inspected = json.loads(
        _run_checked(
            [
                sys.executable,
                str(checkout / "tools/ruleops.py"),
                "inspect",
                first_path,
                "--query",
                first_query,
                "--draft",
                "--repo",
                str(checkout),
            ],
            capture_output=True,
        ).stdout
    )
    assert inspected["target"]["blob"] == target_blobs[first_path]
    assert inspected["observed_hits"] == independent_observed
    assert inspected["pickaxe_events"] == independent_pickaxe

    node_module = "orchestrator/tests/test_check_docs.py"
    nodeid = node_module + "::test_synthetic_repo_baseline_clean"
    guard_path = "tools/check_docs.py"
    receipt_paths = []
    for index, (candidate_path, _query) in enumerate(controlled):
        receipt_rel = (
            f"output/insights/real-checkout-ruleops-receipt-{index}.json"
        )
        receipt_paths.append(receipt_rel)
        _write_json(
            checkout,
            receipt_rel,
            {
                "advisory_only": True,
                "authority": "none",
                "baseline_rc": 0,
                "candidate_blob": target_blobs[candidate_path],
                "candidate_excluded": True,
                "candidate_path": candidate_path,
                "default_effect": "no-state-change",
                "head": candidate_commit,
                "human_review_required": True,
                "mutants": [{
                    "failed_nodes": [nodeid],
                    "guard_path": guard_path,
                    "status": "KILLED",
                }],
                "restored_rc": 0,
                "review_state": "reviewed",
                "schema_version": "ruleops-mutation-receipt/v1",
            },
        )
    _commit(checkout, "ledger-wide advisory receipts")

    candidates = []
    for index, (candidate_path, query) in enumerate(controlled):
        candidates.append({
            "kind": "test",
            "path": candidate_path,
            "rationale": "independent controlled real-checkout package",
            "target_blob": target_blobs[candidate_path],
            "test_evidence": {
                "mutation_receipts": [{
                    "blob": _blob(checkout, receipt_paths[index]),
                    "path": receipt_paths[index],
                }],
                "observed_hits": _reviewed([{
                    "blob": target_blobs[candidate_path],
                    "line": 1,
                    "path": candidate_path,
                    "query": query,
                }]),
                "pickaxe_events": _reviewed([{
                    "commit": candidate_commit,
                    "query": query,
                }]),
                "replacement_guards": [{
                    "blob": _blob(checkout, guard_path),
                    "path": guard_path,
                }],
                "replacement_nodes": [{
                    "blob": _blob(checkout, node_module),
                    "nodeid": nodeid,
                }],
                "semantic_queries": [query],
            },
        })
    ledger = _empty_ledger()
    ledger["candidates"] = candidates
    _write_json(checkout, "docs/ruleops-candidates.json", ledger)
    _commit(checkout, "real checkout maximum candidate ledger")
    literal_signal_tokens = {
        token
        for candidate_path, query in controlled
        for token in (candidate_path, Path(candidate_path).name, query)
    }
    assert len(candidates) == 2
    assert all(len(row["test_evidence"]["semantic_queries"]) == 1 for row in candidates)
    assert len(literal_signal_tokens) == 6
    assert R.MAX_CANDIDATES == 2
    assert R.MAX_QUERY_COUNT == 1
    assert R.MAX_SIGNAL_TOKENS == 6
    started = time.monotonic()
    assert RT._preflight_ruleops([], checkout) == 0
    elapsed = time.monotonic() - started
    print(f"RULEOPS_MAX_PACKAGE_PREFLIGHT_SECONDS={elapsed:.3f}")
    assert elapsed < 60
