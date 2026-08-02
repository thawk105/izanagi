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
    FOLD_AUTHOR_IDENTITY,
    FOLD_COMMIT_MESSAGE,
    GIT_COMMANDS,
    create_exact_worktree,
    create_isolated_checkout,
    read_child_git_trace,
    resolve_main_worktree,
    resolve_repo_identity,
    snapshot_repo,
    supervised_spool_wave_identity,
    supervised_spool_wave_slug,
    trust_root,
    update_submodules_no_fetch,
    verify_declared_fold_commit,
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


def _commit(repo: Path, message: str, *paths: str) -> str:
    _git(repo, "add", "--", *paths)
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _seed_pending(repo: Path, count: int = 1) -> tuple[str, ...]:
    folded = repo / "docs/spool/FOLDED.md"
    folded.parent.mkdir(parents=True, exist_ok=True)
    folded.write_text("# folded\n", encoding="utf-8")
    paths = []
    for index in range(1, count + 1):
        relative = f"docs/spool/worklog/2000-01-01-dev-wave-dw-{'a' * 32}-w001-{index}.md"
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"fragment {index}\n", encoding="utf-8")
        paths.append(relative)
    _commit(repo, "seed pending", "docs/spool/FOLDED.md", *paths)
    return tuple(paths)


def _code_commit(repo: Path, value: str = "wave") -> str:
    (repo / "base.txt").write_text(value + "\n", encoding="utf-8")
    return _commit(repo, "wave code", "base.txt")


def _wave_fragment_commit(repo: Path) -> tuple[str, tuple[str, ...]]:
    folded = repo / "docs/spool/FOLDED.md"
    folded.parent.mkdir(parents=True, exist_ok=True)
    folded.write_text("# folded\n", encoding="utf-8")
    _commit(repo, "seed fold state", "docs/spool/FOLDED.md")
    relative = f"docs/spool/worklog/2000-01-01-dev-wave-dw-{'a' * 32}-w001-1.md"
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("fragment 1\n", encoding="utf-8")
    (repo / "base.txt").write_text("wave\n", encoding="utf-8")
    tip = _commit(repo, "wave adds pending fragment", "base.txt", relative)
    return tip, (relative,)


def _fold_commit(repo: Path, fragments: tuple[str, ...], *, extra_path: str | None = None) -> str:
    for relative in fragments:
        (repo / relative).unlink()
    folded = repo / "docs/spool/FOLDED.md"
    folded.write_text(folded.read_text(encoding="utf-8") + "fold\n", encoding="utf-8")
    paths = ["docs/spool/FOLDED.md", *fragments]
    if extra_path is not None:
        (repo / extra_path).write_text("outside\n", encoding="utf-8")
        paths.append(extra_path)
    _git(repo, "add", "-A", "--", *paths)
    name, email = FOLD_AUTHOR_IDENTITY.rsplit(" <", 1)
    env = dict(os.environ)
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_AUTHOR_NAME": name,
        "GIT_AUTHOR_EMAIL": email[:-1],
    })
    result = subprocess.run(
        ["git", "commit", "--no-gpg-sign", "--cleanup=verbatim", "-F", "-"],
        cwd=repo, env=env, input=FOLD_COMMIT_MESSAGE.decode("ascii"), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert result.returncode == 0, result.stderr
    return _git(repo, "rev-parse", "HEAD")


def test_declared_fold_accepts_exact_direct_child_shape_without_plan_comparison():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        tip, pending = _wave_fragment_commit(repo)
        fold = _fold_commit(repo, pending)
        result = verify_declared_fold_commit(
            repo, fold_commit_sha=fold, landed_main_sha=fold,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert result.ok, result


def test_n31_landed_interval_cannot_hide_an_earlier_fold():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo, 2)
        tip = _code_commit(repo)
        first_fold = _fold_commit(repo, pending[:1])
        second_fold = _fold_commit(repo, pending[1:])
        result = verify_declared_fold_commit(
            repo, fold_commit_sha=second_fold, landed_main_sha=second_fold,
            landed_commits=(tip, first_fold), wave_tip=first_fold,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"


def test_n32_null_declared_fold_rejects_pending_fragment():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        _seed_pending(repo)
        tip = _code_commit(repo)
        result = verify_declared_fold_commit(
            repo, fold_commit_sha=None, landed_main_sha=tip,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert (not result.ok) and result.detail == "null-pending-fragment"


def test_p07_null_declared_fold_accepts_zero_pending_fragments():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        tip = _code_commit(repo)
        result = verify_declared_fold_commit(
            repo, fold_commit_sha=None, landed_main_sha=tip,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert result.ok, result


def test_n33_merge_fold_is_rejected_by_the_parent_count_gate():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo)
        tip = _code_commit(repo)
        valid_fold = _fold_commit(repo, pending)
        tree = _git(repo, "rev-parse", f"{valid_fold}^{{tree}}")
        tip_tree = _git(repo, "rev-parse", f"{tip}^{{tree}}")
        extra = _git(repo, "commit-tree", tip_tree, "-p", f"{tip}^", "-m", "same tree parent")
        name, email = FOLD_AUTHOR_IDENTITY.rsplit(" <", 1)
        env = dict(os.environ)
        env.update({
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email[:-1],
        })
        made = subprocess.run(
            ["git", "commit-tree", tree, "-p", tip, "-p", extra], cwd=repo, env=env,
            input=FOLD_COMMIT_MESSAGE.decode("ascii"), text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        assert made.returncode == 0, made.stderr
        merge_fold = made.stdout.strip()
        _git(repo, "reset", "--hard", merge_fold)
        result = verify_declared_fold_commit(
            repo, fold_commit_sha=merge_fold, landed_main_sha=merge_fold,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert (not result.ok) and result.detail == "header"


def test_fold_commit_with_encoding_header_is_accepted():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo)
        tip = _code_commit(repo)
        _git(repo, "config", "i18n.commitEncoding", "ISO-8859-1")
        fold = _fold_commit(repo, pending)
        commit_object = "\n" + _git(repo, "cat-file", "commit", fold)
        assert "\nencoding ISO-8859-1\n" in commit_object
        result = verify_declared_fold_commit(
            repo, fold_commit_sha=fold, landed_main_sha=fold,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert result.ok, result


def test_landed_interval_allows_every_non_signature_document_path():
    allowed = (
        "docs/worklog.md",
        "docs/decisions.md",
        "docs/failures.md",
        "docs/archive/worklog-phase1-2.md",
        "docs/archive/worklog-phase3-0702-0713.md",
        "docs/archive/README.md",
        "docs/phase3.md",
        "docs/spool/worklog/2000-01-01-wave-add-1.md",
    )
    for relative in allowed:
        with _fresh() as tmp:
            repo = _repo(Path(tmp))
            pending = _seed_pending(repo)
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("wave document change\n", encoding="utf-8")
            tip = _commit(repo, "wave changes allowed document", relative)
            fold = _fold_commit(repo, pending)
            result = verify_declared_fold_commit(
                repo, fold_commit_sha=fold, landed_main_sha=fold,
                landed_commits=(tip,), wave_tip=tip,
            )
            assert result.ok, (relative, result)


def test_landed_interval_allows_folded_receipt_creation():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        folded = repo / "docs/spool/FOLDED.md"
        folded.parent.mkdir(parents=True, exist_ok=True)
        folded.write_text("# folded\n", encoding="utf-8")
        relative = f"docs/spool/worklog/2000-01-01-dev-wave-dw-{'a' * 32}-w001-1.md"
        fragment = repo / relative
        fragment.parent.mkdir(parents=True, exist_ok=True)
        fragment.write_text("fragment 1\n", encoding="utf-8")
        tip = _commit(repo, "introduce spool mechanism", "docs/spool/FOLDED.md", relative)
        fold = _fold_commit(repo, (relative,))
        result = verify_declared_fold_commit(
            repo, fold_commit_sha=fold, landed_main_sha=fold,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert result.ok, result


def test_landed_interval_rejects_fragment_deletion_signature():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo, 2)
        (repo / pending[0]).unlink()
        tip = _commit(repo, "wave deletes fragment", pending[0])
        fold = _fold_commit(repo, pending[1:])
        result = verify_declared_fold_commit(
            repo, fold_commit_sha=fold, landed_main_sha=fold,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"


def test_landed_interval_allows_fragment_modification():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo)
        fragment = repo / pending[0]
        fragment.write_text("wave modifies fragment\n", encoding="utf-8")
        tip = _commit(repo, "wave modifies fragment", pending[0])
        fold = _fold_commit(repo, pending)
        result = verify_declared_fold_commit(
            repo, fold_commit_sha=fold, landed_main_sha=fold,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert result.ok, result


def test_landed_interval_rejects_folded_receipt_signature():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo)
        folded = repo / "docs/spool/FOLDED.md"
        folded.write_text(folded.read_text(encoding="utf-8") + "wave\n", encoding="utf-8")
        tip = _commit(repo, "wave changes folded receipt", "docs/spool/FOLDED.md")
        fold = _fold_commit(repo, pending)
        result = verify_declared_fold_commit(
            repo, fold_commit_sha=fold, landed_main_sha=fold,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"


def test_n34_fold_rejects_a_path_outside_the_closed_shape():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo)
        tip = _code_commit(repo)
        fold = _fold_commit(repo, pending, extra_path="outside.txt")
        result = verify_declared_fold_commit(
            repo, fold_commit_sha=fold, landed_main_sha=fold,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert (not result.ok) and result.detail == "added-path"


def test_n35_supervised_slug_mapping_rejects_noncanonical_inputs_and_is_injective():
    run_id = "dw-" + "a" * 32
    slug = supervised_spool_wave_slug(run_id, 1)
    assert slug == f"dev-wave-{run_id}-w001"
    assert supervised_spool_wave_identity(slug) == (run_id, 1)
    invalid = (
        ("dev-wave/a-b", 1),
        ("dw-" + "A" * 32, 1),
        (run_id, 0),
    )
    for bad_run, bad_wave in invalid:
        try:
            supervised_spool_wave_slug(bad_run, bad_wave)
        except ValueError:
            pass
        else:
            raise AssertionError("noncanonical supervised identity was accepted")
    try:
        supervised_spool_wave_identity(f"dev-wave-{run_id}-w0001")
    except ValueError:
        pass
    else:
        raise AssertionError("noncanonical slug was accepted")


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
