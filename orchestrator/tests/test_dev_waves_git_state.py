"""Temporary-repository tests for the allowlisted dev-wave Git observer."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from tools.dev_waves.git_state import (
    GIT_COMMANDS,
    create_exact_worktree,
    create_isolated_checkout,
    read_child_git_trace,
    resolve_main_worktree,
    resolve_repo_identity,
    snapshot_repo,
    trust_root,
    update_submodules_no_fetch,
    verify_ff_chain,
)
from tools.dev_waves.schema import DevWavesError, ReasonCode


def _git(repo: Path, *args: str, ok: tuple[int, ...] = (0,)) -> str:
    env = dict(os.environ)
    env.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull})
    result = subprocess.run(
        ["git", *args], cwd=repo, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert result.returncode in ok, (args, result.stderr)
    return result.stdout.strip()


def _repo(root: Path) -> Path:
    repo = root / "repo"
    _git(root, "init", "-b", "main", str(repo))
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    (repo / ".gitignore").write_text("output/dev-wave-supervisor/runtime/\n", encoding="utf-8")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    (repo / "tools").mkdir()
    (repo / "tools" / "check_docs.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    (repo / "orchestrator" / "tests").mkdir(parents=True)
    (repo / "orchestrator" / "tests" / "test_pin.py").write_text("def test_pin(): pass\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    return repo


def _fresh() -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix="test-dev-waves-git-")


def test_git_command_table_has_no_forbidden_mutating_verb():
    forbidden = {"push", "merge", "rebase", "reset", "fetch", "deinit", "remove"}
    flattened = {token for command in GIT_COMMANDS.values() for token in command}
    assert forbidden.isdisjoint(flattened)
    assert "--no-fetch" in GIT_COMMANDS["submodule-update"]


def test_identity_main_resolution_and_inherited_git_environment_are_ignored():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        identity = resolve_repo_identity(repo)
        assert identity.main_worktree == str(repo.resolve())
        assert resolve_main_worktree(repo).branch == "main"
        os.environ["GIT_DIR"] = "/definitely/not/the/repository"
        os.environ["GIT_WORK_TREE"] = "/also/wrong"
        try:
            observed = snapshot_repo(repo)
        finally:
            os.environ.pop("GIT_DIR", None)
            os.environ.pop("GIT_WORK_TREE", None)
        assert observed.branch == "main" and not observed.main_dirty


def test_exact_base_worktree_uses_runtime_namespace_and_requested_branch():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        base = _git(repo, "rev-parse", "HEAD")
        wave = create_exact_worktree(repo, "run-123", 7, base)
        assert wave.path == str(repo / "output/dev-wave-supervisor/runtime/run-123/worktrees/w007")
        observed = snapshot_repo(wave.path)
        assert observed.head_sha == base and observed.branch == "dev-wave/run-123/w007"
        assert not (repo / ".claude/worktrees").exists()


def test_main_dirty_and_submodule_dirty_are_separate_facts_and_no_fetch_update_works():
    with _fresh() as tmp:
        root = Path(tmp)
        sub = root / "sub"
        _git(root, "init", "-b", "main", str(sub))
        _git(sub, "config", "user.name", "Test")
        _git(sub, "config", "user.email", "test@example.invalid")
        (sub / "value.txt").write_text("one\n")
        _git(sub, "add", ".")
        _git(sub, "commit", "-m", "sub-base")
        repo = _repo(root)
        _git(repo, "-c", "protocol.file.allow=always", "submodule", "add", str(sub), "vendor/sub")
        _git(repo, "commit", "-am", "add submodule")
        base = _git(repo, "rev-parse", "HEAD")
        wave = create_exact_worktree(repo, "run-sub", 1, base)
        update_submodules_no_fetch(wave.path)
        (Path(wave.path) / "vendor/sub/value.txt").write_text("dirty\n")
        observed = snapshot_repo(wave.path)
        assert observed.submodule_dirty is True
        assert observed.main_dirty is False
        (Path(wave.path) / "ordinary.txt").write_text("untracked\n")
        observed = snapshot_repo(wave.path)
        assert observed.main_dirty is True and observed.submodule_dirty is True


def test_shallow_and_replace_refs_are_rejected():
    with _fresh() as tmp:
        root = Path(tmp)
        repo = _repo(root)
        head = _git(repo, "rev-parse", "HEAD")
        _git(repo, "replace", head, head)
        try:
            snapshot_repo(repo)
        except DevWavesError as exc:
            assert exc.code is ReasonCode.INVALID_RUN
        else:
            raise AssertionError("replace refs were accepted")
        _git(repo, "replace", "-d", head)
        shallow = root / "shallow"
        _git(root, "clone", "--depth=1", f"file://{repo}", str(shallow))
        try:
            snapshot_repo(shallow)
        except DevWavesError as exc:
            assert exc.code is ReasonCode.INVALID_RUN
        else:
            raise AssertionError("shallow repository was accepted")


def test_verify_ff_chain_requires_exact_order_and_noncompleted_main_unchanged():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        before = _git(repo, "rev-parse", "HEAD")
        commits = []
        for value in ("one", "two"):
            (repo / "base.txt").write_text(value + "\n")
            _git(repo, "add", "base.txt")
            _git(repo, "commit", "-m", value)
            commits.append(_git(repo, "rev-parse", "HEAD"))
        after = commits[-1]
        assert verify_ff_chain(repo, before, after, commits, completed=True).ok
        mismatch = verify_ff_chain(repo, before, after, reversed(commits), completed=True)
        assert mismatch.reason is ReasonCode.COMMIT_MISMATCH
        assert verify_ff_chain(repo, before, before, (), completed=False).ok
        assert verify_ff_chain(repo, before, after, (), completed=False).reason is ReasonCode.MAIN_MOVED


def test_trust_root_and_isolated_checkout_are_bound_to_audited_sha():
    with _fresh() as tmp:
        root = Path(tmp)
        repo = _repo(root)
        before = _git(repo, "rev-parse", "HEAD")
        pin = trust_root(repo, before)
        (repo / "base.txt").write_text("after\n")
        _git(repo, "commit", "-am", "unrelated")
        after = _git(repo, "rev-parse", "HEAD")
        assert trust_root(repo, after) == pin
        checkout = root / "isolated"
        create_isolated_checkout(repo, before, checkout, timeout_s=5)
        assert _git(checkout, "rev-parse", "HEAD") == before
        assert (checkout / "base.txt").read_text() == "base\n"


def test_structured_git_trace_detects_push_and_malformed_tail():
    with _fresh() as tmp:
        root = Path(tmp)
        trace = root / "trace.jsonl"
        trace.write_text(json.dumps({"event": "child_start", "argv": ["git", "status"]}) + "\n")
        assert read_child_git_trace(trace).push_attempted is False
        trace.write_text(json.dumps({"event": "child_start", "argv": ["git", "push", "origin"]}) + "\n")
        assert read_child_git_trace(trace).push_attempted is True
        trace.write_bytes(b'{"event":"child_start"}')
        assert read_child_git_trace(trace).malformed is True


def _run():
    functions = [value for name, value in sorted(globals().items())
                 if name.startswith("test_") and callable(value)]
    passed = failed = errors = 0
    for function in functions:
        try:
            function()
            passed += 1
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {function.__name__}: {exc}")
        except Exception:
            errors += 1
            print(f"ERROR {function.__name__}:")
            traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed, {errors} errors (of {len(functions)})")
    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
