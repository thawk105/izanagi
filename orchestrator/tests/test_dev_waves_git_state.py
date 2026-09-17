"""Temporary-repository tests for the allowlisted dev-wave Git observer."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from tools.dev_waves.git_state import (
    FOLD_AUTHOR_IDENTITY,
    FOLD_COMMIT_MESSAGE,
    GIT_COMMANDS,
    _commit_parents,
    _diff_entries,
    _landed_fold_output_path,
    _parse_commit_parent_batch,
    _parse_commit_parents,
    commit_worker_worktree,
    create_exact_worktree,
    create_isolated_checkout,
    read_child_git_trace,
    resolve_main_worktree,
    resolve_registered_worktree,
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


def test_commit_diff_disables_move_detection_by_contract():
    command = GIT_COMMANDS["commit-diff"]
    safe_short_options = {"-r", "-m", "-z"}
    move_detection_long_prefixes = (
        "--find-renames", "--find-copies",
        "--find-copies-harder", "--break-rewrites",
    )
    assert "--no-renames" in command
    assert not [
        token for token in command
        if token.startswith("-")
        and not token.startswith("--")
        and token not in safe_short_options
    ]
    assert not [
        token for token in command
        if token.startswith(move_detection_long_prefixes)
    ]


def test_landed_diff_commands_pin_merge_and_root_contract():
    commit_diff = GIT_COMMANDS["commit-diff"]
    tree_diff = GIT_COMMANDS["tree-diff"]
    assert "-m" not in commit_diff
    assert "--root" in commit_diff
    assert "--root" not in tree_diff
    for command in (commit_diff, tree_diff):
        assert "--no-renames" in command
        assert not any(token.startswith((
            "--find-renames", "--find-copies", "--find-copies-harder",
            "--break-rewrites",
        )) for token in command)


def test_commit_parent_command_is_one_ordered_batch():
    assert GIT_COMMANDS["commit-parents"] == (
        "rev-list", "--parents", "--no-walk=unsorted",
    )


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


def test_registered_worktree_rejects_stale_entry_pointing_to_main_gitdir_without_update():
    with _fresh() as tmp:
        root = Path(tmp)
        repo = _repo(root)
        base = _git(repo, "rev-parse", "HEAD")
        wave = create_exact_worktree(repo, "stale-main-gitdir", 1, base)
        stale_path = Path(wave.path)
        shutil.rmtree(stale_path)
        stale_path.mkdir(parents=True)
        (stale_path / ".git").write_text(
            f"gitdir: {repo.resolve() / '.git'}\n", encoding="utf-8",
        )

        try:
            resolve_registered_worktree(repo, stale_path)
        except ValueError as exc:
            assert str(exc) == "registered worktree does not belong to this repository"
        else:
            raise AssertionError("main repository gitdir was accepted as a worktree")

        import tools.dev_wave_submodule_init as initializer

        stderr = StringIO()
        with (
            patch.object(initializer, "_REPO_ROOT", repo),
            patch.object(initializer, "update_submodules_no_fetch") as update,
            redirect_stderr(stderr),
        ):
            result = initializer.main(["--worktree", str(stale_path)])

        assert result == 2
        assert "does not belong to this repository" in stderr.getvalue()
        update.assert_not_called()


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


def _repo_with_submodule_urls(
    root: Path, *, declared_url: str, resolved_url: str,
) -> tuple[Path, Path]:
    sub = root / "sub"
    _git(root, "init", "-b", "main", str(sub))
    _git(sub, "config", "user.name", "Test")
    _git(sub, "config", "user.email", "test@example.invalid")
    (sub / "value.txt").write_text("one\n", encoding="utf-8")
    _git(sub, "add", ".")
    _git(sub, "commit", "-m", "sub-base")

    repo = _repo(root)
    _git(repo, "-c", "protocol.file.allow=always", "submodule", "add", str(sub), "vendor/sub")
    (repo / ".gitmodules").write_text(
        '[submodule "vendor/sub"]\n'
        "\tpath = vendor/sub\n"
        f"\turl = {declared_url}\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".gitmodules")
    _git(repo, "commit", "-m", "add submodule")
    _git(repo, "config", "submodule.vendor/sub.url", resolved_url)
    return repo, sub


def test_no_fetch_update_accepts_local_resolved_override_for_nonlocal_declaration():
    with _fresh() as tmp:
        root = Path(tmp)
        repo, _sub = _repo_with_submodule_urls(
            root,
            declared_url="https://example.invalid/x.git",
            resolved_url=str(root / "sub"),
        )
        base = _git(repo, "rev-parse", "HEAD")
        wave = create_exact_worktree(repo, "run-sub-override", 1, base)

        update_submodules_no_fetch(wave.path)

        assert (Path(wave.path) / "vendor/sub/value.txt").read_text(encoding="utf-8") == "one\n"


def test_no_fetch_update_rejects_nonlocal_declaration_and_resolved_override():
    with _fresh() as tmp:
        root = Path(tmp)
        repo, _sub = _repo_with_submodule_urls(
            root,
            declared_url="https://example.invalid/x.git",
            resolved_url="https://example.invalid/override.git",
        )
        base = _git(repo, "rev-parse", "HEAD")
        wave = create_exact_worktree(repo, "run-sub-remote", 1, base)

        try:
            update_submodules_no_fetch(wave.path)
        except DevWavesError as exc:
            assert exc.code is ReasonCode.RUNTIME_IO_FAILURE
            assert exc.detail == {"label": "submodule", "kind": "nonlocal-url"}
        else:
            raise AssertionError("nonlocal resolved submodule URL was accepted")


def test_no_fetch_update_rejects_local_declaration_with_nonlocal_resolved_override():
    with _fresh() as tmp:
        root = Path(tmp)
        repo, _sub = _repo_with_submodule_urls(
            root,
            declared_url=str(root / "sub"),
            resolved_url="https://example.invalid/override.git",
        )
        base = _git(repo, "rev-parse", "HEAD")
        wave = create_exact_worktree(repo, "run-local-remote-override", 1, base)

        try:
            update_submodules_no_fetch(wave.path)
        except DevWavesError as exc:
            assert exc.code is ReasonCode.RUNTIME_IO_FAILURE
            assert exc.detail == {"label": "submodule", "kind": "nonlocal-url"}
        else:
            raise AssertionError("nonlocal resolved override for local declaration was accepted")


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


def _main_fold_merge(repo: Path) -> tuple[str, str, tuple[str, ...]]:
    pending = _seed_pending(repo)
    divergence = _git(repo, "rev-parse", "HEAD")
    _git(repo, "switch", "-c", "wave")
    _code_commit(repo)
    _git(repo, "switch", "main")
    assert _git(repo, "rev-parse", "HEAD") == divergence
    main_fold = _fold_commit(repo, pending)
    _git(repo, "switch", "wave")
    _git(repo, "merge", "--no-ff", "--no-edit", main_fold)
    merge_tip = _git(repo, "rev-parse", "HEAD")
    landed = tuple(
        _git(repo, "rev-list", "--reverse", f"{main_fold}..{merge_tip}").splitlines()
    )
    assert landed[-1] == merge_tip
    return main_fold, merge_tip, landed


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


def test_declared_fold_accepts_rotation_that_git_would_report_as_copy():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        worklog = repo / "docs/worklog.md"
        worklog.parent.mkdir(parents=True, exist_ok=True)
        worklog.write_text(
            "".join(f"worklog line {index:03d}: deterministic source bytes\n" for index in range(128)),
            encoding="utf-8",
        )
        _commit(repo, "seed copy source", "docs/worklog.md")
        tip, pending = _wave_fragment_commit(repo)

        original_worklog = worklog.read_bytes()
        rotation = repo / "docs/archive/worklog-phase3-0803-1.md"
        rotation.parent.mkdir(parents=True, exist_ok=True)
        rotation.write_bytes(original_worklog)
        worklog.write_text("current worklog after deterministic rotation\n", encoding="utf-8")
        _git(repo, "add", "--", "docs/worklog.md", rotation.relative_to(repo).as_posix())
        fold = _fold_commit(repo, pending)

        control = _git(
            repo, "diff-tree", "--root", "-r", "-m", "--no-commit-id",
            "--name-status", "-M", "-C", fold,
        ).splitlines()
        assert any(
            line.startswith("C")
            and line.endswith(
                "\tdocs/worklog.md\tdocs/archive/worklog-phase3-0803-1.md"
            )
            for line in control
        ), control
        assert rotation.read_bytes() == original_worklog

        result = verify_declared_fold_commit(
            repo, fold_commit_sha=fold, landed_main_sha=fold,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert result.ok, result


def test_declared_fold_rejects_two_rotation_archives():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        tip, pending = _wave_fragment_commit(repo)
        rotations = (
            "docs/archive/worklog-phase3-0803-1.md",
            "docs/archive/worklog-phase3-0803-2.md",
        )
        for index, relative in enumerate(rotations, 1):
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"rotation {index}\n", encoding="utf-8")
        _git(repo, "add", "--", *rotations)
        fold = _fold_commit(repo, pending)

        result = verify_declared_fold_commit(
            repo, fold_commit_sha=fold, landed_main_sha=fold,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert (not result.ok) and result.detail == "archive-count", result


def test_declared_fold_rejects_archive_readme_without_rotation():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        readme = repo / "docs/archive/README.md"
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text("# archive\n", encoding="utf-8")
        _commit(repo, "seed archive index", "docs/archive/README.md")
        tip, pending = _wave_fragment_commit(repo)
        readme.write_text("# archive\n\nindex changed without rotation\n", encoding="utf-8")
        _git(repo, "add", "--", "docs/archive/README.md")
        fold = _fold_commit(repo, pending)

        result = verify_declared_fold_commit(
            repo, fold_commit_sha=fold, landed_main_sha=fold,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert (not result.ok) and result.detail == "archive-readme", result


def test_declared_fold_rejects_typechange_status():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        rotation_relative = "docs/archive/worklog-phase3-0803-1.md"
        rotation = repo / rotation_relative
        rotation.parent.mkdir(parents=True, exist_ok=True)
        rotation.write_text("regular rotation\n", encoding="utf-8")
        _commit(repo, "seed regular rotation", rotation_relative)
        tip, pending = _wave_fragment_commit(repo)
        rotation.unlink()
        rotation.symlink_to("rotation-target.md")
        _git(repo, "add", "--", rotation_relative)
        fold = _fold_commit(repo, pending)
        control = _git(
            repo, "diff-tree", "--root", "-r", "-m", "--no-commit-id",
            "--name-status", "--no-renames", fold,
        ).splitlines()
        assert f"T\t{rotation_relative}" in control, control

        result = verify_declared_fold_commit(
            repo, fold_commit_sha=fold, landed_main_sha=fold,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert (not result.ok) and result.detail == "path-status", result


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


def test_all_trusted_chain_accepts_main_fold_merge_without_wave_commit():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo)
        older_parent = _git(repo, "rev-parse", "HEAD")
        main_fold = _fold_commit(repo, pending)
        tree = _git(repo, "rev-parse", f"{main_fold}^{{tree}}")
        merge_tip = _git(
            repo,
            "commit-tree",
            tree,
            "-p", older_parent,
            "-p", main_fold,
            "-m", "catch up to folded main without wave commits",
        )
        _git(repo, "reset", "--hard", merge_tip)

        assert _git(repo, "merge-base", older_parent, main_fold) == older_parent
        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            trusted_main_cutoff_sha=main_fold,
            landed_main_sha=merge_tip,
            landed_commits=(merge_tip,),
            wave_tip=merge_tip,
        )
        assert result.ok, result


def test_all_trusted_chain_rejects_fragment_deleted_by_merge_resolution():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        older_parent = _git(repo, "rev-parse", "HEAD")
        pending = _seed_pending(repo)
        newer_parent = _git(repo, "rev-parse", "HEAD")
        tree = _git(repo, "rev-parse", f"{older_parent}^{{tree}}")
        merge_tip = _git(
            repo,
            "commit-tree",
            tree,
            "-p", older_parent,
            "-p", newer_parent,
            "-m", "delete trusted fragment in merge resolution",
        )
        _git(repo, "reset", "--hard", merge_tip)

        assert not (repo / pending[0]).exists()
        assert _git(repo, "merge-base", older_parent, newer_parent) == older_parent
        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            trusted_main_cutoff_sha=newer_parent,
            landed_main_sha=merge_tip,
            landed_commits=(merge_tip,),
            wave_tip=merge_tip,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"


def test_all_trusted_incomparable_maxima_keep_all_parent_scan():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        folded = repo / "docs/spool/FOLDED.md"
        folded.parent.mkdir(parents=True, exist_ok=True)
        folded.write_text("# folded\n", encoding="utf-8")
        common = _commit(repo, "seed folded receipt", "docs/spool/FOLDED.md")

        _git(repo, "switch", "-c", "trusted-one")
        folded.write_text("# folded\none\n", encoding="utf-8")
        first_parent = _commit(repo, "first trusted parent", "docs/spool/FOLDED.md")
        _git(repo, "switch", "main")
        _git(repo, "switch", "-c", "trusted-two", common)
        folded.write_text("# folded\ntwo\n", encoding="utf-8")
        second_parent = _commit(repo, "second trusted parent", "docs/spool/FOLDED.md")

        first_tree = _git(repo, "rev-parse", f"{first_parent}^{{tree}}")
        cutoff = _git(
            repo,
            "commit-tree",
            first_tree,
            "-p", first_parent,
            "-p", second_parent,
            "-m", "trusted cutoff joins both parents",
        )
        merge_tip = _git(
            repo,
            "commit-tree",
            first_tree,
            "-p", first_parent,
            "-p", second_parent,
            "-m", "ambiguous maximal trusted parents",
        )
        _git(repo, "reset", "--hard", merge_tip)

        assert _git(repo, "merge-base", first_parent, second_parent) == common
        assert _git(repo, "merge-base", first_parent, cutoff) == first_parent
        assert _git(repo, "merge-base", second_parent, cutoff) == second_parent
        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            trusted_main_cutoff_sha=cutoff,
            landed_main_sha=merge_tip,
            landed_commits=(merge_tip,),
            wave_tip=merge_tip,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"


def test_landed_interval_allows_main_fold_merge_from_trusted_cutoff():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        main_fold, merge_tip, landed = _main_fold_merge(repo)
        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            trusted_main_cutoff_sha=main_fold,
            landed_main_sha=merge_tip,
            landed_commits=landed,
            wave_tip=merge_tip,
        )
        assert result.ok, result


def test_proper_ancestor_of_cutoff_is_the_unique_trusted_parent():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo)
        divergence = _git(repo, "rev-parse", "HEAD")
        _git(repo, "switch", "-c", "wave")
        _code_commit(repo)
        _git(repo, "switch", "main")
        assert _git(repo, "rev-parse", "HEAD") == divergence
        trusted_parent = _fold_commit(repo, pending)
        (repo / "cutoff.txt").write_text("cutoff\n", encoding="utf-8")
        cutoff = _commit(repo, "advance trusted cutoff", "cutoff.txt")
        _git(repo, "switch", "wave")
        _git(repo, "merge", "--no-ff", "--no-edit", trusted_parent)
        merge_tip = _git(repo, "rev-parse", "HEAD")

        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            trusted_main_cutoff_sha=cutoff,
            landed_main_sha=merge_tip,
            landed_commits=(merge_tip,),
            wave_tip=merge_tip,
        )
        assert trusted_parent != cutoff
        assert result.ok, result


def test_zero_trusted_merge_scans_signature_visible_only_from_second_parent():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        folded = repo / "docs/spool/FOLDED.md"
        folded.parent.mkdir(parents=True, exist_ok=True)
        folded.write_text("# folded\n", encoding="utf-8")
        cutoff = _commit(repo, "seed folded receipt", "docs/spool/FOLDED.md")

        _git(repo, "switch", "-c", "second-parent")
        pending = _seed_pending(repo)
        second_parent = _git(repo, "rev-parse", "HEAD")
        _git(repo, "switch", "main")
        folded.write_text("# folded\nfirst parent\n", encoding="utf-8")
        first_parent = _commit(repo, "prepare safe first parent", "docs/spool/FOLDED.md")
        tree = _git(repo, "rev-parse", f"{first_parent}^{{tree}}")
        merge_tip = _git(
            repo,
            "commit-tree",
            tree,
            "-p", first_parent,
            "-p", second_parent,
            "-m", "zero trusted merge",
        )
        _git(repo, "reset", "--hard", merge_tip)
        assert not (repo / pending[0]).exists()

        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            trusted_main_cutoff_sha=cutoff,
            landed_main_sha=merge_tip,
            landed_commits=(merge_tip,),
            wave_tip=merge_tip,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"


def test_octopus_with_exactly_one_trusted_parent_is_accepted():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo)
        divergence = _git(repo, "rev-parse", "HEAD")

        _git(repo, "switch", "-c", "side-one")
        (repo / "side-one.txt").write_text("one\n", encoding="utf-8")
        side_one = _commit(repo, "side one", "side-one.txt")
        _git(repo, "switch", "main")
        _git(repo, "switch", "-c", "side-two")
        assert _git(repo, "rev-parse", "HEAD") == divergence
        (repo / "side-two.txt").write_text("two\n", encoding="utf-8")
        side_two = _commit(repo, "side two", "side-two.txt")
        _git(repo, "switch", "main")
        cutoff = _fold_commit(repo, pending)
        tree = _git(repo, "rev-parse", f"{cutoff}^{{tree}}")
        octopus = _git(
            repo,
            "commit-tree",
            tree,
            "-p", cutoff,
            "-p", side_one,
            "-p", side_two,
            "-m", "unique trusted octopus",
        )
        _git(repo, "reset", "--hard", octopus)

        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            trusted_main_cutoff_sha=cutoff,
            landed_main_sha=octopus,
            landed_commits=(octopus,),
            wave_tip=octopus,
        )
        assert result.ok, result


def test_landed_interval_without_cutoff_keeps_all_parent_scan():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        _main_fold, merge_tip, landed = _main_fold_merge(repo)
        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            landed_main_sha=merge_tip,
            landed_commits=landed,
            wave_tip=merge_tip,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"


def test_landed_interval_without_cutoff_rejects_signature_visible_only_from_second_parent():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        folded = repo / "docs/spool/FOLDED.md"
        folded.parent.mkdir(parents=True, exist_ok=True)
        folded.write_text("# folded\n", encoding="utf-8")
        first_parent = _commit(repo, "seed first parent", "docs/spool/FOLDED.md")

        _git(repo, "switch", "-c", "second-parent")
        folded.write_text("# folded\nsecond parent\n", encoding="utf-8")
        second_parent = _commit(repo, "change second parent receipt", "docs/spool/FOLDED.md")
        _git(repo, "switch", "main")
        tree = _git(repo, "rev-parse", f"{first_parent}^{{tree}}")
        merge_tip = _git(
            repo,
            "commit-tree",
            tree,
            "-p", first_parent,
            "-p", second_parent,
            "-m", "second parent signature",
        )
        _git(repo, "reset", "--hard", merge_tip)

        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            landed_main_sha=merge_tip,
            landed_commits=(merge_tip,),
            wave_tip=merge_tip,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"


def test_main_fold_merge_rejects_deleting_fragment_present_on_trusted_main():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo, 2)
        divergence = _git(repo, "rev-parse", "HEAD")
        _git(repo, "switch", "-c", "wave")
        _code_commit(repo)
        _git(repo, "switch", "main")
        assert _git(repo, "rev-parse", "HEAD") == divergence
        main_fold = _fold_commit(repo, pending[:1])
        _git(repo, "switch", "wave")
        _git(repo, "merge", "--no-ff", "--no-commit", main_fold)
        (repo / pending[1]).unlink()
        merge_tip = _commit(repo, "delete trusted main fragment in resolution", pending[1])
        landed = tuple(
            _git(repo, "rev-list", "--reverse", f"{main_fold}..{merge_tip}").splitlines()
        )
        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            trusted_main_cutoff_sha=main_fold,
            landed_main_sha=merge_tip,
            landed_commits=landed,
            wave_tip=merge_tip,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"


def test_main_fold_merge_rejects_folded_resolution_different_from_trusted_main():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo)
        divergence = _git(repo, "rev-parse", "HEAD")
        _git(repo, "switch", "-c", "wave")
        _code_commit(repo)
        _git(repo, "switch", "main")
        assert _git(repo, "rev-parse", "HEAD") == divergence
        main_fold = _fold_commit(repo, pending)
        _git(repo, "switch", "wave")
        _git(repo, "merge", "--no-ff", "--no-commit", main_fold)
        folded = repo / "docs/spool/FOLDED.md"
        folded.write_text(
            folded.read_text(encoding="utf-8") + "resolution\n",
            encoding="utf-8",
        )
        merge_tip = _commit(repo, "change folded receipt in resolution", "docs/spool/FOLDED.md")
        landed = tuple(
            _git(repo, "rev-list", "--reverse", f"{main_fold}..{merge_tip}").splitlines()
        )
        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            trusted_main_cutoff_sha=main_fold,
            landed_main_sha=merge_tip,
            landed_commits=landed,
            wave_tip=merge_tip,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"


def test_merge_without_trusted_parent_rejects_resolution_signature():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo)
        cutoff = _git(repo, "rev-parse", "HEAD")
        _git(repo, "switch", "-c", "side")
        (repo / "side.txt").write_text("side\n", encoding="utf-8")
        _commit(repo, "side branch", "side.txt")
        _git(repo, "switch", "main")
        _git(repo, "switch", "-c", "wave")
        _code_commit(repo)
        _git(repo, "merge", "--no-ff", "--no-commit", "side")
        (repo / pending[0]).unlink()
        merge_tip = _commit(repo, "delete fragment in untrusted merge", pending[0])
        landed = tuple(
            _git(repo, "rev-list", "--reverse", f"{cutoff}..{merge_tip}").splitlines()
        )
        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            trusted_main_cutoff_sha=cutoff,
            landed_main_sha=merge_tip,
            landed_commits=landed,
            wave_tip=merge_tip,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"


def test_octopus_with_multiple_trusted_parents_keeps_all_parent_scan():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        first_trusted = _git(repo, "rev-parse", "HEAD")
        pending = _seed_pending(repo)
        cutoff = _git(repo, "rev-parse", "HEAD")
        _git(repo, "switch", "-c", "wave")
        wave_parent = _code_commit(repo)
        (repo / pending[0]).unlink()
        (repo / "docs/spool/FOLDED.md").unlink()
        signature_tree_commit = _commit(
            repo,
            "prepare octopus result tree",
            pending[0],
            "docs/spool/FOLDED.md",
        )
        tree = _git(repo, "rev-parse", f"{signature_tree_commit}^{{tree}}")
        octopus = _git(
            repo,
            "commit-tree",
            tree,
            "-p", first_trusted,
            "-p", cutoff,
            "-p", wave_parent,
            "-m", "octopus resolution",
        )
        _git(repo, "reset", "--hard", octopus)
        landed = tuple(
            _git(repo, "rev-list", "--reverse", f"{cutoff}..{octopus}").splitlines()
        )
        assert landed[-1] == octopus
        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            trusted_main_cutoff_sha=cutoff,
            landed_main_sha=octopus,
            landed_commits=landed,
            wave_tip=octopus,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"


def test_octopus_with_multiple_trusted_parents_rejects_signature_visible_only_from_untrusted_parent():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        folded = repo / "docs/spool/FOLDED.md"
        folded.parent.mkdir(parents=True, exist_ok=True)
        folded.write_text("# folded\n", encoding="utf-8")
        first_trusted = _commit(repo, "seed trusted receipt", "docs/spool/FOLDED.md")
        (repo / "cutoff.txt").write_text("cutoff\n", encoding="utf-8")
        cutoff = _commit(repo, "advance trusted cutoff", "cutoff.txt")

        _git(repo, "switch", "-c", "untrusted", first_trusted)
        folded.write_text("# folded\nuntrusted parent\n", encoding="utf-8")
        untrusted = _commit(repo, "change untrusted receipt", "docs/spool/FOLDED.md")
        _git(repo, "switch", "main")
        tree = _git(repo, "rev-parse", f"{cutoff}^{{tree}}")
        octopus = _git(
            repo,
            "commit-tree",
            tree,
            "-p", first_trusted,
            "-p", cutoff,
            "-p", untrusted,
            "-m", "untrusted parent signature",
        )
        _git(repo, "reset", "--hard", octopus)

        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=None,
            trusted_main_cutoff_sha=cutoff,
            landed_main_sha=octopus,
            landed_commits=(octopus,),
            wave_tip=octopus,
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


def test_landed_interval_rejects_fragment_rename_reported_as_delete_and_add():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo, 2)
        destination = "docs/outside.md"
        (repo / pending[0]).rename(repo / destination)
        tip = _commit(repo, "wave renames fragment", pending[0], destination)
        fold = _fold_commit(repo, pending[1:])

        result = verify_declared_fold_commit(
            repo, fold_commit_sha=fold, landed_main_sha=fold,
            landed_commits=(tip,), wave_tip=tip,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path", result


def test_landed_interval_rejects_fragment_rename_reported_as_rename_record():
    fragment = f"docs/spool/worklog/2000-01-01-dev-wave-dw-{'a' * 32}-w001-1.md"
    assert _landed_fold_output_path("R100", (fragment, "docs/outside.md"))
    assert not _landed_fold_output_path(
        "R100", ("docs/not-a-fragment.md", "docs/outside.md"),
    )


def test_diff_entries_parses_two_paths_for_rename_and_copy_records():
    raw = (
        b"R100\0docs/old.md\0docs/new.md\0"
        b"C085\0docs/source.md\0docs/copy.md\0"
    )
    entries = _diff_entries(raw)
    assert entries == (
        ("R100", ("docs/old.md", "docs/new.md")),
        ("C085", ("docs/source.md", "docs/copy.md")),
    )
    assert len(entries) == 2
    assert all(len(paths) == 2 for _status, paths in entries)


def test_new_git_output_parsers_fail_closed_on_malformed_or_missing_data():
    commit = "a" * 40
    malformed_parent_outputs = (
        b"",
        f"{commit}\n{commit}\n".encode("ascii"),
        f"{commit} not-a-sha\n".encode("ascii"),
        b"\xff\n",
    )
    for raw in malformed_parent_outputs:
        try:
            _parse_commit_parents(raw, commit)
        except DevWavesError as exc:
            assert exc.code is ReasonCode.INVALID_RUN
        else:
            raise AssertionError("malformed commit parent output was accepted")
    try:
        _diff_entries(b"M\0\xff\0")
    except DevWavesError as exc:
        assert exc.code is ReasonCode.INVALID_RUN
    else:
        raise AssertionError("non-UTF-8 diff path was accepted")
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        try:
            _commit_parents(repo, commit, timeout_s=5)
        except DevWavesError as exc:
            assert exc.code is ReasonCode.INVALID_RUN
        else:
            raise AssertionError("missing commit object was accepted")


def test_commit_parent_batch_parser_rejects_count_order_unknown_and_encoding():
    commit = "a" * 40
    second = "b" * 40
    unknown = "c" * 40
    malformed_parent_batches = (
        f"{commit}\n".encode("ascii"),
        f"{commit}\n{second}\n{unknown}\n".encode("ascii"),
        f"{second}\n{commit}\n".encode("ascii"),
        f"{commit}\n{unknown}\n".encode("ascii"),
        f"{commit}\n{second}\n".encode("ascii") + b"\xff",
    )
    for raw in malformed_parent_batches:
        try:
            _parse_commit_parent_batch(raw, (commit, second))
        except DevWavesError as exc:
            assert exc.code is ReasonCode.INVALID_RUN
        else:
            raise AssertionError("malformed commit parent batch was accepted")


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


def _worker_repo(root: Path) -> tuple[Path, Path]:
    primary = root / "primary"
    _git(root, "init", "-b", "parent", str(primary))
    _git(primary, "config", "user.name", "Worker Test")
    _git(primary, "config", "user.email", "worker@example.invalid")
    for name in ("tracked", "deleted"):
        (primary / name).write_text("base\n", encoding="utf-8")
    _git(primary, "add", "-A")
    _git(primary, "commit", "-m", "base")
    worker = root / "worker"
    _git(primary, "worktree", "add", "-b", "topic", str(worker))
    return primary, worker


def _record_worker(repo: Path, **kwargs: object) -> tuple[str, str | None]:
    return commit_worker_worktree(
        repo, wave="wave", job_id="job", stage="author", launcher_rc=7, **kwargs,
    )


def _worker_trailer(repo: Path) -> tuple[str, str]:
    sys.path.insert(0, str(_ROOT / "tools"))
    import check_ai_provenance

    message = _git(repo, "log", "-1", "--format=%B")
    trailers = [line for line in message.splitlines() if line.startswith("AI-Agent:")]
    assert len(trailers) == 1
    assert message.split("\n\n")[-1] == trailers[0]
    match = check_ai_provenance.AGENT_VALUE.fullmatch(trailers[0].removeprefix("AI-Agent: "))
    assert match is not None, trailers
    assert match["product"] == "codex" and match["role"] == "author"
    assert match["model"] != "none" and match["reasoning"] != "none"
    return match["model"], match["reasoning"]


def test_commit_worker_worktree_records_residue_then_noop():
    with _fresh() as tmp:
        primary, worker = _worker_repo(Path(tmp))
        base = _git(worker, "rev-parse", "HEAD")
        (worker / "tracked").write_text("edited\n", encoding="utf-8")
        (worker / "deleted").unlink()
        (worker / "new").write_bytes(b"new\x00bytes\n")
        _git(worker, "add", "tracked")
        def patch_bytes():
            return subprocess.run(
                ["git", "diff", "--cached", base, "--", "tracked"],
                cwd=worker, check=True, stdout=subprocess.PIPE,
            ).stdout
        before = patch_bytes()
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            status, head = _record_worker(worker)
            assert (status, head) == ("committed", _git(worker, "rev-parse", "HEAD"))
            assert _record_worker(worker) == ("clean", None)
        assert out.getvalue() == f"worktree-commit: committed {head}\nworktree-commit: clean\n"
        assert err.getvalue() == ""
        assert _git(worker, "rev-parse", "HEAD") == head
        assert _git(worker, "rev-list", "--count", f"{base}..HEAD") == "1"
        assert _git(primary, "rev-parse", "HEAD") == base
        assert patch_bytes() == before and before
        assert _git(worker, "ls-tree", "--name-only", "HEAD").splitlines() == ["new", "tracked"]
        assert _git(worker, "status", "--porcelain") == ""
        assert _git(worker, "log", "-1", "--format=%an <%ae>|%cn <%ce>") == (
            "Worker Test <worker@example.invalid>|Worker Test <worker@example.invalid>"
        )
        assert _worker_trailer(worker) == ("unknown", "unknown")


def test_commit_worker_worktree_provenance_values():
    cases = (
        ({"recorded_model": "GPT-6", "requested_model": "fallback", "recorded_effort": "HIGH", "requested_effort": "low"}, ("gpt-6", "high")),
        ({"recorded_model": " ", "requested_model": "GPT-5.6", "requested_effort": "Medium"}, ("gpt-5.6", "medium")),
        (None, ("unknown", "unknown")),
        ({"recorded_model": "NONE", "recorded_effort": "none", "requested_model": "fallback"}, ("unknown", "unknown")),
        ({"recorded_model": "._GPT\n6; X---", "recorded_effort": "..MAX;\n", "outcome": "ok\nAI-Agent: forged;"}, ("gpt-6-x", "max")),
        ("malformed", ("unknown", "unknown")),
    )
    with _fresh() as tmp:
        root = Path(tmp)
        _, worker = _worker_repo(root)
        receipt = root / "receipt.json"
        for index, (payload, expected) in enumerate(cases):
            receipt.unlink(missing_ok=True)
            if payload is not None:
                receipt.write_text("{" if payload == "malformed" else json.dumps(payload))
            (worker / "tracked").write_text(f"change {index}\n")
            assert _record_worker(worker, receipt_path=receipt)[0] == "committed"
            assert _worker_trailer(worker) == expected
            message = _git(worker, "log", "-1", "--format=%B")
            assert "scope: worktree residue at job end" in message
            if isinstance(payload, dict) and "outcome" in payload:
                assert "receipt outcome: okAI-Agent: forged\n" in message


def test_commit_worker_worktree_refuses_detached_protected_primary_root():
    for case, reason in (("detached", "detached-head"), ("main", "protected-branch"),
                         ("master", "protected-branch"), ("primary", "primary-worktree"),
                         ("nested", "root-mismatch")):
        with _fresh() as tmp:
            primary, worker = _worker_repo(Path(tmp))
            if case == "detached":
                _git(worker, "checkout", "--detach")
            elif case in ("main", "master"):
                _git(worker, "branch", "-m", case)
            target = primary if case == "primary" else worker
            (target / "new").write_text("residue\n")
            before_head = _git(target, "rev-parse", "HEAD")
            before_index = Path(_git(target, "rev-parse", "--path-format=absolute", "--git-path", "index")).read_bytes()
            if case == "nested":
                target = worker / "nested"
                target.mkdir()
            out, err = StringIO(), StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                assert _record_worker(target) == ("refused", reason)
            assert out.getvalue() == f"worktree-commit: refused reason={reason}\n"
            assert err.getvalue() == f"NG: worktree-commit refused reason={reason}\n"
            assert _git(target, "rev-parse", "HEAD") == before_head
            assert Path(_git(target, "rev-parse", "--path-format=absolute", "--git-path", "index")).read_bytes() == before_index
            assert ((primary if case == "primary" else worker) / "new").read_text() == "residue\n"


def test_commit_worker_worktree_defers_merge_in_progress():
    with _fresh() as tmp:
        primary, worker = _worker_repo(Path(tmp))
        (primary / "tracked").write_text("parent\n")
        _git(primary, "commit", "-am", "parent")
        (worker / "tracked").write_text("worker\n")
        _git(worker, "commit", "-am", "worker")
        _git(worker, "merge", "parent", ok=(1,))
        before = _git(worker, "ls-files", "--unmerged")
        head = _git(worker, "rev-parse", "HEAD")
        residue = (worker / "tracked").read_bytes()
        assert before
        assert _record_worker(worker) == ("deferred", "operation-in-progress")
        assert _git(worker, "ls-files", "--unmerged") == before
        assert _git(worker, "rev-parse", "HEAD") == head
        assert (worker / "tracked").read_bytes() == residue


def test_commit_worker_worktree_failed_keeps_residue():
    with _fresh() as tmp:
        _, worker = _worker_repo(Path(tmp))
        base = _git(worker, "rev-parse", "HEAD")
        _git(worker, "config", "--unset", "user.name")
        _git(worker, "config", "--unset", "user.email")
        _git(worker, "config", "user.useConfigOnly", "true")
        (worker / "new").write_text("residue\n")
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            assert _record_worker(worker) == ("failed", "commit-file")
        assert out.getvalue() == "worktree-commit: failed reason=commit-file\n"
        assert err.getvalue() == "NG: worktree-commit failed reason=commit-file\n"
        assert _git(worker, "rev-parse", "HEAD") == base
        assert _git(worker, "show", ":new") == "residue"
        assert (worker / "new").read_text() == "residue\n"


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
