from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "tools" / "check_branch_landed.py"
SPEC = importlib.util.spec_from_file_location("check_branch_landed", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            **os.environ,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        },
        check=False,
    )
    if check and result.returncode:
        raise AssertionError(
            f"git {' '.join(args)} failed ({result.returncode})\n{result.stdout}\n{result.stderr}"
        )
    return result


def _write(repo: Path, path: str, content: str | bytes, *, mode: int | None = None) -> Path:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        target.write_bytes(content)
    else:
        target.write_text(content, encoding="utf-8")
    if mode is not None:
        target.chmod(mode)
    return target


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "config", "tag.gpgsign", "false")
    _git(repo, "config", "core.hooksPath", "/dev/null")
    _write(repo, "base.txt", "base\n")
    _commit(repo, "base")
    return repo


def _topic(repo: Path, name: str = "topic") -> None:
    _git(repo, "switch", "-c", name)


def _main(repo: Path) -> None:
    _git(repo, "switch", "main")


def _run_tool(
    repo: Path,
    branch: str = "topic",
    *extra: str,
    timeout: float = 30.0,
) -> tuple[int, dict[str, Any], subprocess.CompletedProcess[str]]:
    result = subprocess.run(
        [sys.executable, str(TOOL_PATH), branch, "--repo", str(repo), *extra],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    assert result.stdout.count("\n") == 1, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    return result.returncode, payload, result


def _assert_verdict(
    result: tuple[int, dict[str, Any], subprocess.CompletedProcess[str]],
    verdict: str,
    reason: str,
) -> dict[str, Any]:
    rc, payload, process = result
    expected_rc = {"landed": 0, "not-landed": 1, "indeterminate": 2}[verdict]
    assert rc == expected_rc, process.stdout + process.stderr
    assert payload["decision"] == {
        "verdict": verdict,
        "landed": {"landed": True, "not-landed": False, "indeterminate": None}[verdict],
        "conclusive": verdict != "indeterminate",
        "reason": reason,
    }
    return payload


def _unit(payload: dict[str, Any], *, path: str, reason: str) -> dict[str, Any]:
    matches = [
        unit for unit in payload["proof_units"]
        if unit["path"] == path and unit["decision"]["reason"] == reason
    ]
    assert matches, payload["proof_units"]
    return matches[0]


def _receipt(
    content_sha256: str,
    *,
    authored: str = "2026-08-25",
    wave: str = "topic",
    seq: int = 1,
    allocations: dict[str, str] | None = None,
) -> str:
    return "# Folded\n\n- " + json.dumps(
        {
            "allocations": allocations or {},
            "authored": authored,
            "content_sha256": content_sha256,
            "seq": seq,
            "wave": wave,
        },
        sort_keys=True,
    ) + "\n"


def _receipt_v2(content_sha256: str, *, base: str, tested_tip: str) -> str:
    return "# Folded\n\n- " + json.dumps({
        "allocations": {},
        "authored": "2026-08-25",
        "base": base,
        "content_sha256": content_sha256,
        "seq": 1,
        "tested_tip": tested_tip,
        "wave": "topic",
        "wave_ref": "refs/heads/topic",
    }, sort_keys=True) + "\n"


def _fragment(
    ledger: str,
    body: str,
    *,
    authored: str = "2026-08-25",
    wave: str = "topic",
    seq: int = 1,
    title: str = "Test fragment",
) -> str:
    fields = [
        "---",
        "schema: izanagi-spool-v1",
        f"ledger: {ledger}",
        f"authored: {authored}",
        f"wave: {wave}",
        f"seq: {seq}",
    ]
    if ledger == "worklog":
        fields.append(f"title: {title}")
    return "\n".join([*fields, "---", body.rstrip(), ""])


def _all_outcomes(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "outcome":
                found.append(child)
            found.extend(_all_outcomes(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_all_outcomes(child))
    return found


def _all_values_for_key(value: Any, wanted: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == wanted:
                found.append(child)
            found.extend(_all_values_for_key(child, wanted))
    elif isinstance(value, list):
        for child in value:
            found.extend(_all_values_for_key(child, wanted))
    return found


def test_rehomed_fragment_without_receipt_is_indeterminate_and_probed(tmp_path: Path):
    repo = _init_repo(tmp_path)
    old_fragment = _fragment(
        "decisions",
        "## D568. policy hint\n\nDistinctive canonical decision body.",
        authored="2026-08-19",
        wave="old-wave",
    )
    _topic(repo, "old-wave")
    path = "docs/spool/decisions/2026-08-19-old-wave-1.md"
    _write(repo, path, old_fragment)
    _commit(repo, "old fragment")

    _main(repo)
    _write(repo, "docs/archive/decisions-older.md", "# Decisions\n\n## D568. policy hint\n\nDistinctive canonical decision body.\n")
    rehomed = old_fragment.replace("old-wave", "new-wave")
    rehomed_sha = __import__("hashlib").sha256(rehomed.encode()).hexdigest()
    _write(repo, "docs/spool/FOLDED.md", _receipt(
        rehomed_sha, authored="2026-08-19", wave="new-wave",
    ))
    _commit(repo, "fold rehomed fragment")

    payload = _assert_verdict(
        _run_tool(repo, "old-wave"), "indeterminate", "one-or-more-states-unproven"
    )
    _unit(payload, path=path, reason="folded-receipt-absent")
    probe_layer = payload["observations"]["ledger_probe"]
    assert probe_layer["outcome"] == "not-matched"
    assert probe_layer["signal_strength"] == "weak-positive"
    probes = probe_layer["probes"]
    assert probes and probes[0]["outcome"] == "not-matched"
    assert probes[0]["signal_strength"] == "weak-positive"
    assert probes[0]["identity_unit"] == {
        "kind": "none",
        "value": None,
        "outcome": "not-applicable",
        "reason": "decisions-fragment-has-no-usable-placeholder-heading",
        "hit_targets": [],
    }
    assert probes[0]["matched_unit_count"] == probes[0]["unit_count"]
    assert probes[0]["all_units_matched"] is True
    assert probes[0]["single_file_max_matched_unit_count"] == probes[0]["unit_count"]
    assert {hit["path"] for hit in probes[0]["hits"]} == {"docs/archive/decisions-older.md"}
    assert payload["unresolved_fragment_candidates"] == [{
        "path": path,
        "whole_file_sha256": __import__("hashlib").sha256(old_fragment.encode()).hexdigest(),
        "whole_file_sha256s": [__import__("hashlib").sha256(old_fragment.encode()).hexdigest()],
        "canonical_body_sha256": __import__("hashlib").sha256(
            "## D568. policy hint\n\nDistinctive canonical decision body.".encode()
        ).hexdigest(),
        "receipt_present": False,
        "matched_unit_count": probes[0]["unit_count"],
        "unit_count": probes[0]["unit_count"],
        "signal_strength": "weak-positive",
        "identity_unit": probes[0]["identity_unit"],
        "hit_targets": [{
            "path": "docs/archive/decisions-older.md",
            "matched_units": probes[0]["unit_count"],
            "matched_structural_units": probes[0]["unit_count"],
            "identity_unit_matched": False,
        }],
    }]


def test_receipt_exact_hash_is_landed(tmp_path: Path):
    repo = _init_repo(tmp_path)
    fragment = _fragment("decisions", "## Decision\n\nFold me.")
    path = "docs/spool/decisions/2026-08-25-topic-1.md"
    _topic(repo)
    _write(repo, path, fragment)
    _commit(repo, "fragment")
    _main(repo)
    digest = __import__("hashlib").sha256(fragment.encode()).hexdigest()
    _write(repo, "docs/spool/FOLDED.md", _receipt(digest))
    _commit(repo, "receipt only")

    payload = _assert_verdict(
        _run_tool(repo), "landed", "all-introduced-states-proven"
    )
    unit = _unit(payload, path=path, reason="folded-receipt-exact-hash-and-identity")
    assert unit["evidence"][1]["outcome"] == "matched"
    assert payload["observations"]["ledger_corpus"]["outcome"] == "not-applicable"


def test_v2_receipt_exact_hash_and_identity_is_landed(tmp_path: Path):
    repo = _init_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    fragment = _fragment("decisions", "## Decision\n\nFold with v2 receipt.")
    path = "docs/spool/decisions/2026-08-25-topic-1.md"
    _topic(repo)
    _write(repo, path, fragment)
    topic = _commit(repo, "fragment")
    _main(repo)
    digest = __import__("hashlib").sha256(fragment.encode()).hexdigest()
    _write(repo, "docs/spool/FOLDED.md", _receipt_v2(
        digest, base=base, tested_tip=topic,
    ))
    _commit(repo, "v2 receipt")

    payload = _assert_verdict(
        _run_tool(repo), "landed", "all-introduced-states-proven"
    )
    _unit(payload, path=path, reason="folded-receipt-exact-hash-and-identity")


def test_receipt_missing_fields_make_exact_hash_indeterminate(tmp_path: Path):
    repo = _init_repo(tmp_path)
    fragment = _fragment("decisions", "## Decision\n\nMust not trust a partial receipt.")
    path = "docs/spool/decisions/2026-08-25-topic-1.md"
    _topic(repo)
    _write(repo, path, fragment)
    _commit(repo, "fragment")
    _main(repo)
    digest = __import__("hashlib").sha256(fragment.encode()).hexdigest()
    _write(repo, "docs/spool/FOLDED.md", "- " + json.dumps({
        "content_sha256": digest,
        "wave": "topic",
    }) + "\n")
    _commit(repo, "partial receipt")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    unit = _unit(payload, path=path, reason="folded-receipt-schema-invalid")
    assert unit["evidence"][1]["outcome"] == "error"


def test_receipt_identity_mismatch_does_not_prove_fragment(tmp_path: Path):
    repo = _init_repo(tmp_path)
    fragment = _fragment("decisions", "## Decision\n\nIdentity matters.")
    path = "docs/spool/decisions/2026-08-25-topic-1.md"
    _topic(repo)
    _write(repo, path, fragment)
    _commit(repo, "fragment")
    _main(repo)
    digest = __import__("hashlib").sha256(fragment.encode()).hexdigest()
    _write(repo, "docs/spool/FOLDED.md", _receipt(digest, wave="another-wave"))
    _commit(repo, "wrong identity receipt")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    unit = _unit(payload, path=path, reason="folded-receipt-identity-mismatch")
    assert unit["evidence"][1]["outcome"] == "not-matched"


def test_one_invalid_receipt_bullet_invalidates_registry(tmp_path: Path):
    repo = _init_repo(tmp_path)
    fragment = _fragment("decisions", "## Decision\n\nExact content.")
    path = "docs/spool/decisions/2026-08-25-topic-1.md"
    _topic(repo)
    _write(repo, path, fragment)
    _commit(repo, "fragment")
    _main(repo)
    digest = __import__("hashlib").sha256(fragment.encode()).hexdigest()
    folded = _receipt(digest) + '- {"wave":"x","wave":"y"}\n'
    _write(repo, "docs/spool/FOLDED.md", folded)
    _commit(repo, "duplicate json key")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    _unit(payload, path=path, reason="folded-receipt-duplicate-json-key")


def test_receipted_spool_deletion_is_landed_from_old_blob(tmp_path: Path):
    repo = _init_repo(tmp_path)
    fragment = _fragment("decisions", "## Decision\n\nAlready folded.")
    path = "docs/spool/decisions/2026-08-25-topic-1.md"
    _write(repo, path, fragment)
    _commit(repo, "fragment before branch")
    _topic(repo)
    (repo / path).unlink()
    _commit(repo, "delete folded fragment")
    _main(repo)
    digest = __import__("hashlib").sha256(fragment.encode()).hexdigest()
    _write(repo, "docs/spool/FOLDED.md", _receipt(digest))
    _commit(repo, "receipt fragment")

    payload = _assert_verdict(
        _run_tool(repo), "landed", "all-introduced-states-proven"
    )
    unit = _unit(payload, path=path, reason="folded-receipt-exact-hash-and-identity")
    assert unit["change"] == "D"
    assert unit["required_state"]["object_type"] == "missing"
    assert unit["evidence"][1]["content_sha256"] == digest


def test_main_tip_exact_blob_and_state_is_landed(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write(repo, "f", "base\n")
    _commit(repo, "add f")
    _topic(repo)
    _write(repo, "f", "alpha\nbeta\n")
    _commit(repo, "topic combined")
    _main(repo)
    _write(repo, "f", "alpha\n")
    _commit(repo, "main alpha")
    _write(repo, "f", "alpha\nbeta\n")
    _commit(repo, "main beta")

    payload = _assert_verdict(
        _run_tool(repo), "landed", "all-introduced-states-proven"
    )
    _unit(payload, path="f", reason="exact-state-at-main-tip")


def test_unreachable_commitish_matches_branch_verdict_after_branch_deletion(
    tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    _topic(repo)
    _write(repo, "f", "landed content\n")
    topic_tip = _commit(repo, "topic content")
    _main(repo)
    _write(repo, "f", "landed content\n")
    _commit(repo, "main content")

    branch_payload = _assert_verdict(
        _run_tool(repo, "topic"), "landed", "all-introduced-states-proven"
    )
    _git(repo, "branch", "-D", "topic")
    reachability = _git(
        repo, "merge-base", "--is-ancestor", topic_tip, "main", check=False,
    )
    assert reachability.returncode == 1

    commit_payload = _assert_verdict(
        _run_tool(repo, topic_tip), "landed", "all-introduced-states-proven"
    )
    assert branch_payload["decision"] == commit_payload["decision"]
    assert branch_payload["branch"]["resolved_as"] == "local-branch"
    assert commit_payload["branch"]["resolved_as"] == "commit-ish"
    assert commit_payload["branch"]["tip"] == topic_tip
    assert commit_payload["branch"]["resolution_order"] == [
        "local-branch", "commit-ish",
    ]
    assert commit_payload["branch"]["resolution_candidates"] == {
        "local_branch": None,
        "commit_ish": [topic_tip],
    }
    assert branch_payload["closure"]["commits"] == commit_payload["closure"]["commits"]
    assert [unit["decision"] for unit in branch_payload["proof_units"]] == [
        unit["decision"] for unit in commit_payload["proof_units"]
    ]
    assert [unit["required_state"] for unit in branch_payload["proof_units"]] == [
        unit["required_state"] for unit in commit_payload["proof_units"]
    ]


def test_missing_branch_or_commitish_has_dedicated_indeterminate_issue(
    tmp_path: Path,
):
    repo = _init_repo(tmp_path)

    payload = _assert_verdict(
        _run_tool(repo, "branch-that-does-not-exist"),
        "indeterminate",
        "branch-not-found",
    )
    assert payload["issues"] == [{
        "code": "branch-not-found",
        "scope": "branch",
        "path": None,
        "affects_verdict": True,
        "message": (
            "neither refs/heads/branch-that-does-not-exist nor the commit-ish "
            "'branch-that-does-not-exist' resolves to a commit"
        ),
    }]
    assert payload["branch"]["resolved_as"] is None
    assert payload["branch"]["resolution_candidates"] == {
        "local_branch": None,
        "commit_ish": [],
    }
    assert all(issue["code"] != "git-command-error" for issue in payload["issues"])


def test_branch_named_like_abbreviated_sha_is_fail_closed(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic(repo, "object-source")
    _write(repo, "object-only", "object commit\n")
    object_commit = _commit(repo, "object candidate")
    _main(repo)
    abbreviation = object_commit[:12]
    assert len(abbreviation) < len(object_commit)
    _git(repo, "branch", abbreviation, "main")
    branch_tip = _git(repo, "rev-parse", "main").stdout.strip()

    payload = _assert_verdict(
        _run_tool(repo, abbreviation),
        "indeterminate",
        "ambiguous-branch-commit-ish",
    )
    assert payload["issues"][0]["code"] == "ambiguous-branch-commit-ish"
    assert payload["branch"]["resolved_as"] is None
    assert payload["branch"]["resolution_order"] == ["local-branch", "commit-ish"]
    assert payload["branch"]["resolution_candidates"]["local_branch"] == branch_tip
    assert object_commit in payload["branch"]["resolution_candidates"]["commit_ish"]


def test_exact_state_in_main_history_is_landed(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write(repo, "f", "base\n")
    _commit(repo, "f base")
    _topic(repo)
    _write(repo, "f", "historic payload\n")
    _commit(repo, "topic payload")
    _main(repo)
    _write(repo, "f", "historic payload\n")
    _commit(repo, "main payload")
    _write(repo, "f", "later state\n")
    _commit(repo, "main later")

    payload = _assert_verdict(
        _run_tool(repo), "landed", "all-introduced-states-proven"
    )
    _unit(payload, path="f", reason="exact-state-in-main-history")


def test_originless_replacement_is_indeterminate(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write(repo, "generated.json", '{"opaque":"base"}\n')
    _commit(repo, "generated base")
    _topic(repo)
    _write(repo, "generated.json", '{"opaque":"branch"}\n')
    _commit(repo, "branch regeneration")
    _main(repo)
    _write(repo, "generated.json", '{"opaque":"main"}\n')
    _commit(repo, "main regeneration")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    _unit(payload, path="generated.json", reason="exact-state-not-proven")


def test_true_pure_add_is_not_landed_with_closed_world_reason(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic(repo)
    _write(repo, "unique.txt", "only topic\n")
    _commit(repo, "pure addition")

    payload = _assert_verdict(
        _run_tool(repo), "not-landed", "closed-world-negative-proof"
    )
    _unit(payload, path="unique.txt", reason="pure-add-path-never-present")
    assert payload["branch_delete_authorized"] is False
    assert payload["manual_review_required"] is True
    assert payload["negative_paths"] == ["unique.txt"]
    assert payload["unproven_paths"] == []


def test_intermediate_blob_loss_is_not_landed_as_landed(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write(repo, "f", "base\n")
    _commit(repo, "f base")
    _topic(repo)
    secret_commit = _write(repo, "f", "unique-secret\n")
    assert secret_commit
    secret_oid = _commit(repo, "secret")
    _write(repo, "f", "final\n")
    _commit(repo, "final")
    _main(repo)
    _write(repo, "f", "final\n")
    _commit(repo, "independently final")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    units = [unit for unit in payload["proof_units"] if unit["commit"] == secret_oid]
    assert len(units) == 1
    assert units[0]["decision"]["reason"] == "exact-state-not-proven"
    assert payload["closure"]["commit_count"] == 2
    assert len(payload["proof_units"]) == 2
    assert payload["files"] == [{
        "path": "f",
        "decision": {
            "verdict": "indeterminate",
            "landed": None,
            "conclusive": False,
            "reason": "one-or-more-proof-units-unproven",
        },
        "proof_unit_count": 2,
        "proof_unit_indices": [0, 1],
    }]
    assert payload["summary"]["changed_files"] == 1
    assert payload["summary"]["changed_files_definition"] == (
        "unique-paths-in-all-parent-difference-proof-units"
    )


def test_merge_only_closure_includes_merge_and_side_commit(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write(repo, "f", "base\n")
    base = _commit(repo, "f base")
    _git(repo, "switch", "-c", "side")
    _write(repo, "f", "side-only\n")
    side = _commit(repo, "side only")
    _git(repo, "switch", "-c", "topic", base)
    _git(repo, "merge", "--no-ff", "--no-commit", "side")
    _write(repo, "f", "base\n")
    merge = _commit(repo, "merge side but resolve to base")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    assert {item["sha"] for item in payload["closure"]["commits"]} == {side, merge}
    assert payload["closure"]["merge_commit_count"] == 1
    patch = payload["observations"]["patch_id"]
    assert patch["status"] == "incomplete"
    assert patch["omitted_merge_count"] == 1
    _unit(payload, path="f", reason="exact-state-not-proven")


def test_merge_proof_paths_are_intersection_of_all_parent_differences(tmp_path: Path):
    repo = _init_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _topic(repo)
    _write(repo, "topic.txt", "landed state\n")
    topic_commit = _commit(repo, "topic state")
    _main(repo)
    _write(repo, "topic.txt", "landed state\n")
    _write(repo, "main-only.txt", "from main\n")
    _commit(repo, "main has topic state and another path")
    _git(repo, "switch", "topic")
    _git(repo, "merge", "--no-ff", "main", "-m", "merge main")
    merge = _git(repo, "rev-parse", "HEAD").stdout.strip()
    parents = _git(repo, "show", "-s", "--format=%P", merge).stdout.split()
    edge_paths = [
        set(_git(repo, "diff", "--name-only", parent, merge).stdout.splitlines())
        for parent in parents
    ]
    assert edge_paths == [{"main-only.txt"}, set()]
    assert set.intersection(*edge_paths) == set()

    payload = _assert_verdict(
        _run_tool(repo), "landed", "all-introduced-states-proven"
    )
    assert payload["closure"]["commit_count"] == 2
    assert payload["closure"]["merge_commit_count"] == 1
    assert [(unit["commit"], unit["path"]) for unit in payload["proof_units"]] == [
        (topic_commit, "topic.txt")
    ]
    assert payload["summary"]["changed_files"] == 1
    assert payload["summary"]["tip_net_changed_files"] == 0
    assert base not in {item["sha"] for item in payload["closure"]["commits"]}


def test_merge_edge_provenance_is_separate_from_unique_files(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write(repo, "f", "base\n")
    base = _commit(repo, "f base")
    _git(repo, "switch", "-c", "side")
    _write(repo, "f", "side\n")
    _commit(repo, "side state")
    _git(repo, "switch", "-c", "topic", base)
    _write(repo, "f", "topic\n")
    _commit(repo, "topic state")
    merge_result = _git(repo, "merge", "--no-ff", "--no-commit", "side", check=False)
    assert merge_result.returncode == 1
    _write(repo, "f", "resolved\n")
    merge = _commit(repo, "resolved merge")
    _main(repo)
    for content in ("topic\n", "side\n", "resolved\n", "later\n"):
        _write(repo, "f", content)
        _commit(repo, f"main state {content.strip()}")

    payload = _assert_verdict(
        _run_tool(repo), "landed", "all-introduced-states-proven"
    )
    merge_units = [unit for unit in payload["proof_units"] if unit["commit"] == merge]
    assert len(merge_units) == 2
    assert len({unit["parent"] for unit in merge_units}) == 2
    assert len({unit["required_state"]["oid"] for unit in merge_units}) == 1
    assert len(payload["proof_units"]) == 4
    assert len(payload["files"]) == 1
    assert payload["files"][0]["path"] == "f"
    assert payload["files"][0]["proof_unit_count"] == 4


def test_nonempty_net_empty_closure_is_indeterminate(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic(repo)
    _git(repo, "commit", "--allow-empty", "-m", "branch-only empty commit")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "closure-has-no-introduced-state"
    )
    assert payload["closure"]["commit_count"] == 1
    assert payload["summary"]["changed_files"] == 0
    assert payload["summary"]["proof_units"] == 0


def test_duplicate_section_verbatim_hit_is_only_observation(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write(repo, "config.ini", "[prod]\nenabled=false\n")
    _commit(repo, "config base")
    _topic(repo)
    topic_text = "[prod]\nallow_delete=true\nenabled=false\n"
    _write(repo, "config.ini", topic_text)
    _commit(repo, "topic section")
    _main(repo)
    _write(repo, "config.ini", "[prod]\nenabled=false\n" + topic_text)
    _commit(repo, "duplicate section")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    _unit(payload, path="config.ini", reason="exact-state-not-proven")
    assert payload["observations"]["verbatim"]["outcome"] == "matched"
    observed = [
        item for item in payload["observations"]["verbatim"]["entries"]
        if item["path"] == "config.ini"
    ]
    assert observed and observed[0]["outcome"] == "matched"


def test_same_blob_at_another_path_does_not_match(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic(repo)
    _write(repo, "wanted", "same\n")
    _commit(repo, "wanted path")
    _main(repo)
    _write(repo, "other", "same\n")
    _commit(repo, "other path")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    unit = _unit(payload, path="wanted", reason="exact-object-seen-at-another-path")
    assert unit["evidence"][0]["outcome"] == "not-matched"
    assert unit["evidence"][2]["outcome"] == "matched"
    assert unit["evidence"][2]["decisive"] is False


def test_content_and_mode_from_different_commits_do_not_compose(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write(repo, "tool", "base\n", mode=0o644)
    _commit(repo, "tool base")
    _topic(repo)
    _write(repo, "tool", "payload\n", mode=0o755)
    _commit(repo, "payload executable")
    _main(repo)
    _write(repo, "tool", "payload\n", mode=0o644)
    _commit(repo, "payload non-executable")
    _write(repo, "tool", "other\n", mode=0o755)
    _commit(repo, "other executable")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    unit = _unit(payload, path="tool", reason="exact-state-not-proven")
    assert unit["required_state"]["mode"] == "100755"


def test_same_blob_with_regular_file_instead_of_symlink_does_not_match(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic(repo)
    os.symlink("destination", repo / "link")
    _commit(repo, "topic symlink")
    _main(repo)
    _write(repo, "link", "destination")
    _commit(repo, "main regular file")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    unit = _unit(payload, path="link", reason="exact-state-not-proven")
    assert unit["required_state"]["mode"] == "120000"
    assert unit["required_state"]["object_type"] == "blob"


def test_landed_does_not_override_an_indeterminate_sibling(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write(repo, "a", "base a\n")
    _write(repo, "b", "base b\n")
    _commit(repo, "two bases")
    _topic(repo)
    _write(repo, "a", "landed a\n")
    _write(repo, "b", "unproven b\n")
    _commit(repo, "two changes")
    _main(repo)
    _write(repo, "a", "landed a\n")
    _write(repo, "b", "different b\n")
    _commit(repo, "partial landing")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    assert payload["summary"]["landed"] == 1
    assert payload["summary"]["indeterminate"] == 1


def test_history_candidate_limit_is_indeterminate_not_negative(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write(repo, "f", "zero\n")
    _commit(repo, "f zero")
    _topic(repo)
    _write(repo, "f", "wanted\n")
    _commit(repo, "wanted")
    _main(repo)
    for index in range(3):
        _write(repo, "f", f"main {index}\n")
        _commit(repo, f"main {index}")

    payload = _assert_verdict(
        _run_tool(repo, "topic", "--history-candidates", "1"),
        "indeterminate",
        "one-or-more-states-unproven",
    )
    unit = _unit(payload, path="f", reason="history-candidate-limit-exceeded")
    assert unit["evidence"][0]["outcome"] == "truncated"
    assert unit["evidence"][0]["candidate_limit"] == 1
    assert payload["history_scan"]["scan_limit"] != payload["limits"]["history_candidates"]


def test_history_match_at_candidate_33_wins_before_65_plus_truncation(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write(repo, "f", "base\n")
    _commit(repo, "f base")
    _topic(repo)
    _write(repo, "f", "wanted\n")
    _commit(repo, "topic wanted")
    _main(repo)
    for index in range(67):
        content = "wanted\n" if index == 34 else f"main {index}\n"
        _write(repo, "f", content)
        _commit(repo, f"main history {index}")

    payload = _assert_verdict(
        _run_tool(repo, "topic", "--history-candidates", "64"),
        "landed",
        "all-introduced-states-proven",
    )
    unit = _unit(payload, path="f", reason="exact-state-in-main-history")
    assert unit["evidence"][0]["candidate_count"] == 65
    assert TOOL.DEFAULT_HISTORY_CANDIDATES == 1024


def test_global_timeout_is_indeterminate_json(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic(repo)
    _write(repo, "f", "topic\n")
    _commit(repo, "topic")

    payload = _assert_verdict(
        _run_tool(repo, "topic", "--timeout-seconds", "0.000001"),
        "indeterminate",
        "assessment-timeout",
    )
    assert payload["summary"]["changed_files"] is None
    assert payload["summary"]["files_enumerated"] is False


def test_global_exception_marks_the_active_phase(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    _topic(repo)
    _write(repo, "f", "topic\n")
    _commit(repo, "topic")

    def fail_states(*_args: Any, **_kwargs: Any):
        raise TOOL.AssessmentError("synthetic-proof-error", "synthetic proof failure")

    monkeypatch.setattr(TOOL, "_introduced_states", fail_states)
    payload = TOOL.assess(repo, "topic")
    assert payload["decision"]["verdict"] == "indeterminate"
    assert payload["decision"]["reason"] == "synthetic-proof-error"
    assert payload["phase_outcomes"]["proof"] == "error"


def test_history_scan_limit_is_indeterminate_and_measured(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic(repo)
    _write(repo, "f", "topic\n")
    _commit(repo, "topic")
    _main(repo)
    _write(repo, "main-only", "one\n")
    _commit(repo, "main one")

    payload = _assert_verdict(
        _run_tool(repo, "topic", "--history-scan-commits", "1"),
        "indeterminate",
        "one-or-more-states-unproven",
    )
    assert payload["limits"]["history_scan_commits"] == 1
    assert payload["summary"]["changed_files"] == 1
    assert payload["summary"]["files_enumerated"] is True
    assert payload["history_scan"]["outcome"] == "truncated"
    assert payload["history_scan"]["commits_scanned"] == 2
    assert payload["history_scan"]["scan_limit"] == 1
    assert payload["history_scan"]["complete"] is False
    unit = _unit(payload, path="f", reason="history-scan-limit-exceeded")
    evidence = [
        item for item in unit["evidence"]
        if item["layer"] == "closed-world-history-scan"
    ]
    assert len(evidence) == 1
    assert evidence[0]["outcome"] == "truncated"
    assert evidence[0]["reason"] == "history-scan-limit-exceeded"
    assert evidence[0]["commits_scanned"] > 0
    assert evidence[0]["scan_limit"] > 0
    assert evidence[0]["elapsed_seconds"] > 0


def test_closure_limit_preserves_observed_measurements(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic(repo)
    _write(repo, "one", "1\n")
    _commit(repo, "one")
    _write(repo, "two", "2\n")
    _commit(repo, "two")

    payload = _assert_verdict(
        _run_tool(repo, "topic", "--max-closure-commits", "1"),
        "indeterminate",
        "closure-limit-exceeded",
    )
    closure = payload["closure"]
    assert closure["outcome"] == "truncated"
    assert closure["observed_commit_count"] == 2
    assert closure["limit"] == 1
    assert closure["complete"] is False
    assert closure["elapsed_seconds"] >= 0


def test_receipt_blob_limit_is_reported_on_receipt_evidence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    fragment = _fragment("decisions", "## Decision\n\nBlob exceeds synthetic limit.")
    path = "docs/spool/decisions/2026-08-25-topic-1.md"
    _topic(repo)
    _write(repo, path, fragment)
    _commit(repo, "fragment")
    monkeypatch.setattr(TOOL, "MAX_TEXT_BYTES", 8)

    payload = TOOL.assess(repo, "topic")
    assert payload["decision"]["verdict"] == "indeterminate"
    unit = payload["proof_units"][0]
    assert unit["decision"]["reason"] == "blob-size-limit-exceeded"
    assert unit["evidence"][1]["outcome"] == "truncated"
    assert unit["evidence"][1]["reason"] == "blob-size-limit-exceeded"


def test_positive_proof_does_not_require_complete_history_scan(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic(repo)
    _write(repo, "f", "exact\n")
    _commit(repo, "topic exact")
    _main(repo)
    _write(repo, "f", "exact\n")
    _commit(repo, "main exact")
    _write(repo, "later", "later\n")
    _commit(repo, "later main commit")

    payload = _assert_verdict(
        _run_tool(repo, "topic", "--history-scan-commits", "1"),
        "landed",
        "all-introduced-states-proven",
    )
    assert payload["history_scan"]["outcome"] == "not-applicable"
    assert payload["history_scan"]["commits_scanned"] == 0


def test_empty_closure_does_not_require_complete_history_scan(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic(repo)
    _git(repo, "commit", "--allow-empty", "-m", "topic snapshot")
    _main(repo)
    _git(repo, "merge", "--ff-only", "topic")
    _write(repo, "later", "later\n")
    _commit(repo, "later main commit")

    payload = _assert_verdict(
        _run_tool(repo, "topic", "--history-scan-commits", "1"),
        "landed",
        "branch-closure-empty",
    )
    assert payload["history_scan"]["outcome"] == "not-applicable"


def test_max_files_makes_changed_files_unknown(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic(repo)
    _write(repo, "one", "1\n")
    _write(repo, "two", "2\n")
    _commit(repo, "two additions")

    payload = _assert_verdict(
        _run_tool(repo, "topic", "--max-files", "1"),
        "indeterminate",
        "file-limit-exceeded",
    )
    assert payload["summary"]["changed_files"] is None
    assert payload["summary"]["files_enumerated"] is False


def test_shallow_repository_is_indeterminate(tmp_path: Path):
    repo = _init_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _topic(repo)
    _write(repo, "f", "topic\n")
    _commit(repo, "topic")
    (repo / ".git" / "shallow").write_text(base + "\n", encoding="ascii")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "shallow-repository"
    )
    assert payload["issues"][0]["code"] == "shallow-repository"


def test_replace_ref_is_indeterminate(tmp_path: Path):
    repo = _init_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _topic(repo)
    _write(repo, "f", "topic\n")
    topic = _commit(repo, "topic")
    _git(repo, "update-ref", f"refs/replace/{base}", topic)

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "replace-refs-present"
    )
    assert payload["issues"][0]["code"] == "replace-refs-present"


def test_nonempty_grafts_file_is_indeterminate(tmp_path: Path):
    repo = _init_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _topic(repo)
    _write(repo, "f", "topic\n")
    topic = _commit(repo, "topic")
    grafts = repo / ".git" / "info" / "grafts"
    grafts.parent.mkdir(parents=True, exist_ok=True)
    grafts.write_text(f"{topic} {base}\n", encoding="ascii")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "grafts-present"
    )
    assert payload["issues"][0]["code"] == "grafts-present"


def test_custom_replace_namespace_is_indeterminate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _topic(repo)
    _write(repo, "f", "topic\n")
    topic = _commit(repo, "topic")
    _git(repo, "update-ref", f"refs/custom-replace/{base}", topic)
    monkeypatch.setenv("GIT_REPLACE_REF_BASE", "refs/custom-replace")

    payload = TOOL.assess(repo, "topic")
    assert payload["decision"]["verdict"] == "indeterminate"
    assert payload["decision"]["reason"] == "custom-replace-refs-present"


def test_merge_base_is_not_queried(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    repo = _init_repo(tmp_path)
    _topic(repo)
    _write(repo, "f", "topic\n")
    _commit(repo, "topic")
    _main(repo)
    _write(repo, "f", "topic\n")
    _commit(repo, "main exact")
    original = TOOL.Git.run

    def reject_merge_base(git: Any, args: Any, **kwargs: Any):
        assert args[0] != "merge-base"
        return original(git, args, **kwargs)

    monkeypatch.setattr(TOOL.Git, "run", reject_merge_base)
    payload = TOOL.assess(repo, "topic")
    assert payload["decision"]["verdict"] == "landed"
    assert payload["merge_base"] == {"status": "not-required-for-closure"}


def test_ref_movement_is_indeterminate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    repo = _init_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _topic(repo)
    _write(repo, "f", "topic\n")
    _commit(repo, "topic")
    original = TOOL._resolve_ref
    calls = {"topic": 0}

    def moving_ref(git: Any, name: str) -> str:
        value = original(git, name)
        if name == "topic":
            calls["topic"] += 1
            if calls["topic"] == 2:
                return base
        return value

    monkeypatch.setattr(TOOL, "_resolve_ref", moving_ref)
    payload = TOOL.assess(repo, "topic")
    assert payload["decision"]["verdict"] == "indeterminate"
    assert payload["decision"]["reason"] == "refs-moved"
    assert payload["ref_snapshot"]["matches_start_at_end"] is False
    assert payload["ref_snapshot"]["continuous_stability_proven"] is False
    assert payload["ref_snapshot"]["verdict_bound_to_start_snapshot"] is True
    assert "refs_stable" not in payload
    assert [issue["code"] for issue in payload["issues"]] == ["refs-moved"]


@pytest.mark.parametrize("ledger_path", ["docs/failures.md", "docs/phase3.md"])
def test_task_id_hit_in_failures_and_phase3_does_not_move_verdict(
    tmp_path: Path, ledger_path: str,
):
    repo = _init_repo(tmp_path)
    _write(repo, ledger_path, "# Ledger\n\n- [T-1239] recorded only here\n")
    _commit(repo, "task record")
    _topic(repo, "worktree-t1239-only-record")
    _write(repo, "unique", "not landed\n")
    _commit(repo, "unrelated payload")

    payload = _assert_verdict(
        _run_tool(repo, "worktree-t1239-only-record"),
        "not-landed",
        "closed-world-negative-proof",
    )
    index = payload["observations"]["task_index"]
    assert index["outcome"] == "matched"
    assert index["task_ids"] == ["T-1239"]
    assert {hit["path"] for hit in index["hits"]} == {ledger_path}


def test_exact_receipt_keeps_ledger_corpus_lazy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    fragment = _fragment("decisions", "## Decision\n\nNo probe needed.")
    path = "docs/spool/decisions/2026-08-25-topic-1.md"
    _topic(repo)
    _write(repo, path, fragment)
    _commit(repo, "fragment")
    _main(repo)
    digest = __import__("hashlib").sha256(fragment.encode()).hexdigest()
    _write(repo, "docs/spool/FOLDED.md", _receipt(digest))
    _commit(repo, "receipt")

    def fail_if_built(*_args: Any, **_kwargs: Any):
        raise AssertionError("ledger corpus must stay lazy")

    monkeypatch.setattr(TOOL, "_ledger_corpus", fail_if_built)
    payload = TOOL.assess(repo, "topic")
    assert payload["decision"]["verdict"] == "landed"
    assert payload["observations"]["ledger_corpus"]["outcome"] == "not-applicable"


def test_ledger_corpus_uses_one_cat_file_batch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    _write(repo, "docs/worklog.md", "# Worklog\n")
    _write(repo, "docs/archive/old.md", "# Old\n")
    main_oid = _commit(repo, "ledgers")
    git = TOOL.Git(repo, __import__("time").monotonic() + 30)
    original = TOOL.Git.run
    cat_file_args: list[list[str]] = []

    def recording_run(git_obj: Any, args: Any, **kwargs: Any):
        if args[0] == "cat-file":
            cat_file_args.append(list(args))
        return original(git_obj, args, **kwargs)

    monkeypatch.setattr(TOOL.Git, "run", recording_run)
    corpus = TOOL._ledger_corpus(git, main_oid)
    assert corpus.complete is True
    assert corpus.files_enumerated == 2
    assert corpus.files_read == 2
    assert cat_file_args == [["cat-file", "--batch"]]


def test_probe_failure_does_not_move_exact_verdict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    _topic(repo, "worktree-t1239-exact")
    _write(repo, "f", "same\n")
    _commit(repo, "topic exact")
    _main(repo)
    _write(repo, "f", "same\n")
    _commit(repo, "main exact")

    def fail_corpus(*_args: Any, **_kwargs: Any):
        raise TOOL.AssessmentError("probe-failed", "synthetic probe failure")

    monkeypatch.setattr(TOOL, "_ledger_corpus", fail_corpus)
    payload = TOOL.assess(repo, "worktree-t1239-exact")
    assert payload["decision"]["verdict"] == "landed"
    assert payload["observations"]["ledger_corpus"]["outcome"] == "error"
    assert payload["observations"]["task_index"]["outcome"] == "error"


def test_non_utf8_corpus_is_error_without_moving_exact_verdict(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write(repo, "docs/archive/binary.md", b"\xff\xfe")
    _commit(repo, "non utf8 archive")
    _topic(repo, "worktree-t1239-exact")
    _write(repo, "f", "same\n")
    _commit(repo, "topic exact")
    _main(repo)
    _write(repo, "f", "same\n")
    _commit(repo, "main exact")

    payload = _assert_verdict(
        _run_tool(repo, "worktree-t1239-exact"),
        "landed",
        "all-introduced-states-proven",
    )
    corpus = payload["observations"]["ledger_corpus"]
    assert corpus["outcome"] == "error"
    assert corpus["complete"] is False
    assert corpus["files_enumerated"] == 1
    assert corpus["files_read"] == 0
    assert corpus["skipped"] == 1
    assert corpus["errors"] == [{"path": "docs/archive/binary.md", "code": "ledger-blob-not-utf8"}]
    assert payload["observations"]["task_index"]["outcome"] == "error"


def test_worklog_title_identity_match_is_strong_but_indeterminate(tmp_path: Path):
    repo = _init_repo(tmp_path)
    title = "workload descriptor hint was agreed for roadmap section one"
    fragment = _fragment(
        "worklog",
        "## Branch-only worklog shape\n\nText rewritten during canonical folding.",
        title=title,
    )
    path = "docs/spool/worklog/2026-08-25-topic-1.md"
    _topic(repo)
    _write(repo, path, fragment)
    _commit(repo, "unresolved worklog fragment")
    _main(repo)
    target = "docs/archive/worklog-phase3-0819-710.md"
    _write(
        repo,
        target,
        f"# Worklog archive\n\n## 2026-08-19 (710) — {title}\n\nCanonical body.\n",
    )
    _commit(repo, "canonical worklog entry")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    probe_layer = payload["observations"]["ledger_probe"]
    assert probe_layer["outcome"] == "matched"
    assert probe_layer["signal_strength"] == "strong"
    probe = probe_layer["probes"][0]
    assert probe["outcome"] == "matched"
    assert probe["signal_strength"] == "strong"
    assert probe["identity_unit"] == {
        "kind": "frontmatter-title",
        "value": title,
        "outcome": "matched",
        "reason": "worklog-frontmatter-title",
        "hit_targets": [{"path": target, "count": 1}],
    }
    assert probe["matched_unit_count"] == 0
    assert probe["hit_targets"] == [{
        "path": target,
        "matched_units": 1,
        "matched_structural_units": 0,
        "identity_unit_matched": True,
    }]
    candidate = payload["unresolved_fragment_candidates"][0]
    assert candidate["signal_strength"] == "strong"
    assert candidate["identity_unit"] == probe["identity_unit"]
    assert candidate["hit_targets"] == probe["hit_targets"]
    assert payload["decision"]["verdict"] == "indeterminate"
    strengths = {
        value for value in _all_values_for_key(payload, "signal_strength")
        if value is not None
    }
    assert strengths <= TOOL.PROBE_SIGNAL_STRENGTHS


def test_worklog_title_mismatch_caps_structural_majority_at_weak_positive(
    tmp_path: Path,
):
    repo = _init_repo(tmp_path)
    fragment = _fragment(
        "worklog",
        "## Shared structural heading\n\nShared structural body.\n\nBranch-only tail.",
        title="Expected identity title",
    )
    path = "docs/spool/worklog/2026-08-25-topic-1.md"
    _topic(repo)
    _write(repo, path, fragment)
    _commit(repo, "unresolved worklog fragment")
    _main(repo)
    target = "docs/archive/worklog-other.md"
    _write(
        repo,
        target,
        "# Worklog archive\n\n"
        "## 2026-08-25 (999) — Different identity title\n\n"
        "## Shared structural heading\n\nShared structural body.\n",
    )
    _commit(repo, "coincidental structural units")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    probe = payload["observations"]["ledger_probe"]["probes"][0]
    assert probe["identity_unit"] == {
        "kind": "frontmatter-title",
        "value": "Expected identity title",
        "outcome": "not-matched",
        "reason": "worklog-frontmatter-title",
        "hit_targets": [],
    }
    assert probe["matched_unit_count"] == 2
    assert probe["unit_count"] == 3
    assert probe["single_file_max_matched_unit_count"] == 2
    assert probe["signal_strength"] == "weak-positive"
    assert probe["signal_strength"] != "strong"
    assert probe["outcome"] == "not-matched"
    assert probe["hit_targets"] == [{
        "path": target,
        "matched_units": 2,
        "matched_structural_units": 2,
        "identity_unit_matched": False,
    }]
    candidate = payload["unresolved_fragment_candidates"][0]
    assert candidate["signal_strength"] == "weak-positive"
    assert candidate["hit_targets"] == probe["hit_targets"]


@pytest.mark.parametrize(
    ("ledger", "namespace", "canonical_id", "target"),
    [
        ("decisions", "D", "D900", "docs/decisions.md"),
        ("failures", "F", "F900", "docs/failures.md"),
    ],
)
def test_placeholder_heading_text_is_a_ledger_identity_unit(
    tmp_path: Path,
    ledger: str,
    namespace: str,
    canonical_id: str,
    target: str,
):
    repo = _init_repo(tmp_path)
    heading_text = "Canonical identity heading"
    fragment = _fragment(
        ledger,
        f"## {{{{{namespace}:canonical-identity}}}}. {heading_text}\n\nBranch body.",
    )
    path = f"docs/spool/{ledger}/2026-08-25-topic-1.md"
    _topic(repo)
    _write(repo, path, fragment)
    _commit(repo, "unresolved ledger fragment")
    _main(repo)
    _write(repo, target, f"# Ledger\n\n## {canonical_id}. {heading_text}\n\nCanonical body.\n")
    _commit(repo, "canonical ledger entry")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    probe = payload["observations"]["ledger_probe"]["probes"][0]
    assert probe["identity_unit"] == {
        "kind": "placeholder-heading-text",
        "value": heading_text,
        "outcome": "matched",
        "reason": f"{ledger}-placeholder-heading-text",
        "hit_targets": [{"path": target, "count": 1}],
    }
    assert probe["signal_strength"] == "strong"
    assert probe["outcome"] == "matched"


def test_weak_ledger_hit_reports_coverage_without_moving_verdict(tmp_path: Path):
    repo = _init_repo(tmp_path)
    fragment = _fragment(
        "failures",
        "## Common heading\n\nUnique unit one.\n\nUnique unit two.",
    )
    path = "docs/spool/failures/2026-08-25-topic-1.md"
    _topic(repo)
    _write(repo, path, fragment)
    _commit(repo, "unresolved fragment")
    _main(repo)
    _write(repo, "docs/failures.md", "# Failures\n\n## Common heading\n")
    _commit(repo, "only generic unit")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    probe = payload["observations"]["ledger_probe"]["probes"][0]
    assert probe["outcome"] == "not-matched"
    assert probe["matched_unit_count"] == 1
    assert probe["unit_count"] == 3
    assert probe["all_units_matched"] is False
    assert probe["single_file_max_matched_unit_count"] == 1
    assert probe["signal_strength"] == "weak"
    assert probe["identity_unit"]["outcome"] == "not-applicable"
    candidate = payload["unresolved_fragment_candidates"][0]
    assert candidate["path"] == path
    assert candidate["matched_unit_count"] == 1
    assert candidate["unit_count"] == 3
    assert candidate["signal_strength"] == "weak"
    assert candidate["hit_targets"] == [{
        "path": "docs/failures.md",
        "matched_units": 1,
        "matched_structural_units": 1,
        "identity_unit_matched": False,
    }]
    assert payload["receipt_missing_paths"] == [path]
    assert payload["unproven_paths"] == [path]


def test_hash_mentioned_as_prose_is_not_a_receipt(tmp_path: Path):
    repo = _init_repo(tmp_path)
    fragment = _fragment("worklog", "## Work\n\nBody.")
    path = "docs/spool/worklog/2026-08-25-topic-1.md"
    _topic(repo)
    _write(repo, path, fragment)
    _commit(repo, "fragment")
    digest = __import__("hashlib").sha256(fragment.encode()).hexdigest()
    _main(repo)
    _write(repo, "docs/spool/FOLDED.md", f"# Folded\n\nThe hash was {digest}, maybe.\n")
    _commit(repo, "prose mention")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    _unit(payload, path=path, reason="folded-receipt-absent")


def test_malformed_receipt_is_integrity_indeterminate(tmp_path: Path):
    repo = _init_repo(tmp_path)
    path = "docs/spool/failures/2026-08-25-topic-1.md"
    _topic(repo)
    _write(repo, path, _fragment("failures", "Failure body."))
    _commit(repo, "fragment")
    _main(repo)
    _write(repo, "docs/spool/FOLDED.md", '- {"content_sha256": broken}\n')
    _commit(repo, "malformed receipt")

    payload = _assert_verdict(
        _run_tool(repo), "indeterminate", "one-or-more-states-unproven"
    )
    _unit(payload, path=path, reason="folded-receipt-json-invalid")


def test_json_schema_outcomes_and_all_exit_codes(tmp_path: Path):
    landed_repo = _init_repo(tmp_path / "landed")
    _topic(landed_repo)
    _write(landed_repo, "same", "value\n")
    _commit(landed_repo, "topic same")
    _main(landed_repo)
    _write(landed_repo, "same", "value\n")
    _commit(landed_repo, "main same")
    landed = _assert_verdict(
        _run_tool(landed_repo), "landed", "all-introduced-states-proven"
    )

    negative_repo = _init_repo(tmp_path / "negative")
    _topic(negative_repo)
    _write(negative_repo, "unique", "value\n")
    _commit(negative_repo, "unique")
    _assert_verdict(
        _run_tool(negative_repo), "not-landed", "closed-world-negative-proof"
    )

    uncertain_repo = _init_repo(tmp_path / "uncertain")
    _write(uncertain_repo, "f", "base\n")
    _commit(uncertain_repo, "f base")
    _topic(uncertain_repo)
    _write(uncertain_repo, "f", "branch\n")
    _commit(uncertain_repo, "branch")
    _main(uncertain_repo)
    _write(uncertain_repo, "f", "main\n")
    _commit(uncertain_repo, "main")
    _assert_verdict(
        _run_tool(uncertain_repo), "indeterminate", "one-or-more-states-unproven"
    )

    assert landed["schema"] == "izanagi-branch-landed-v1"
    assert landed["assessment_scope"] == "D720-condition-1-only"
    assert landed["condition2"] == {"status": "not-checked"}
    assert landed["land_authorized"] is False
    assert landed["branch_delete_authorized"] is False
    assert landed["manual_review_required"] is True
    assert landed["summary"]["files_enumerated"] is True
    assert landed["summary"]["changed_files"] == 1
    assert len(landed["files"]) == 1
    assert landed["files"][0]["path"] == "same"
    assert landed["files"][0]["proof_unit_indices"] == [0]
    assert landed["unproven_paths"] == []
    assert landed["negative_paths"] == []
    assert landed["receipt_missing_paths"] == []
    assert landed["branch"]["resolved_as"] == "local-branch"
    assert landed["branch"]["resolution_order"] == ["local-branch", "commit-ish"]
    assert landed["ref_snapshot"]["matches_start_at_end"] is True
    assert landed["ref_snapshot"]["end_resolved_as"] == "local-branch"
    assert landed["ref_snapshot"]["continuous_stability_proven"] is False
    assert "refs_stable" not in landed
    assert set(_all_outcomes(landed)) <= TOOL.OUTCOMES
    assert "auxiliary_evidence" not in landed
    assert "observations" in landed

    syntax = subprocess.run(
        [sys.executable, str(TOOL_PATH)], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert syntax.returncode == 64
    assert syntax.stdout == ""
    help_result = subprocess.run(
        [sys.executable, str(TOOL_PATH), "--help"], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert help_result.returncode == 0
    assert "D720 condition 1" in help_result.stdout
    assert "BRANCH_OR_COMMIT" in help_result.stdout
    assert "commit-ish" in help_result.stdout


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", __file__]))
