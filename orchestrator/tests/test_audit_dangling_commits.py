# -*- coding: utf-8 -*-
"""消えたブランチの未 land 作業を検出する監査の controls。"""

from __future__ import annotations

import errno
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


_ROOT = Path(__file__).resolve().parents[2]
_TOOL = _ROOT / "tools" / "audit_dangling_commits.py"
_SPEC = importlib.util.spec_from_file_location("audit_dangling_under_test", _TOOL)
assert _SPEC and _SPEC.loader
ADC = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = ADC
_SPEC.loader.exec_module(ADC)


def _git(repo: Path, *args: str) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(
        {
            "GIT_AUTHOR_NAME": "fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        }
    )
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, (args, completed.stderr)
    return completed.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(repo, "commit", "-qm", "base")
    return repo


def _commit_files(repo: Path, branch: str, files: dict[str, str]) -> str:
    _git(repo, "checkout", "-q", "-b", branch)
    for relpath, content in files.items():
        target = repo / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        _git(repo, "add", relpath)
    _git(repo, "commit", "-qm", f"work on {branch}")
    return _git(repo, "rev-parse", "HEAD")


def _delete_branch(repo: Path, branch: str) -> None:
    _git(repo, "checkout", "-q", "main")
    _git(repo, "branch", "-D", branch)


def _commit_executable(repo: Path, branch: str, relpath: str, content: str) -> str:
    _git(repo, "checkout", "-q", "-b", branch)
    target = repo / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    target.chmod(0o755)
    _git(repo, "add", relpath)
    _git(repo, "commit", "-qm", f"work on {branch}")
    return _git(repo, "rev-parse", "HEAD")


def _external_file(
    root: Path,
    relpath: str,
    content: str,
    *,
    executable: bool = False,
) -> Path:
    target = root / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    target.chmod(0o755 if executable else 0o644)
    return target.resolve()


def _landed_reference(repo: Path, *paths: Path) -> None:
    target = repo / "docs" / "landed-copy.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "landed references\n" + "\n".join(str(path) for path in paths) + "\n",
        encoding="utf-8",
    )
    _git(repo, "add", "docs/landed-copy.md")
    _git(repo, "commit", "-qm", "record external copy")


def _grep_patterns(args: tuple[str, ...]) -> tuple[str, ...]:
    assert args[:4] == ("grep", "-F", "-l", "-z")
    assert args[-1] == "--"
    patterns: list[str] = []
    index = 4
    while index < len(args) - 2:
        assert args[index] == "-e"
        patterns.append(args[index + 1])
        index += 2
    assert index == len(args) - 2
    return tuple(patterns)


def _audit(repo: Path, excluded=ADC.DEFAULT_EXCLUDED_PREFIXES):
    return ADC.audit(repo, "main", excluded)


def test_positive_control_deleted_branch_work_is_reported(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    lost = _commit_files(
        repo,
        "doomed",
        {"tools/lost_implementation.py": "lost work\n"},
    )
    _delete_branch(repo, "doomed")

    findings = _audit(repo)

    assert findings == [
        (lost, "work on doomed", ["tools/lost_implementation.py"]),
    ]
    assert ADC.main(["--repo", str(repo)]) == 1
    output = capsys.readouterr().out
    assert "要確認の到達不能変更" in output
    assert lost in output
    assert "tools/lost_implementation.py" in output


def test_negative_main_reachable_commit_is_not_reported(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    transient = repo / "transient.txt"
    transient.write_text("reachable history\n", encoding="utf-8")
    _git(repo, "add", "transient.txt")
    _git(repo, "commit", "-qm", "reachable addition")
    transient.unlink()
    _git(repo, "add", "transient.txt")
    _git(repo, "commit", "-qm", "reachable deletion")

    assert _audit(repo) == []
    assert ADC.main(["--repo", str(repo)]) == 0
    output = capsys.readouterr().out
    assert ADC.LIMITATION_NOTICE in output


def test_help_discloses_detection_limitations(monkeypatch, capsys) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    with pytest.raises(SystemExit) as excinfo:
        ADC.main(["--help"])

    assert excinfo.value.code == 0
    assert ADC.LIMITATION_NOTICE in capsys.readouterr().out


def test_decode_error_is_execution_failure(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)

    def fail_decode(*_args, **_kwargs):
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr(ADC, "_git", fail_decode)

    assert ADC.main(["--repo", str(repo)]) == 2
    assert "実行できません" in capsys.readouterr().err


def test_negative_path_already_in_main_is_not_reported(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _commit_files(repo, "doomed", {"tools/landed.py": "same work\n"})
    _delete_branch(repo, "doomed")
    landed = repo / "tools" / "landed.py"
    landed.parent.mkdir(parents=True, exist_ok=True)
    landed.write_text("same work\n", encoding="utf-8")
    _git(repo, "add", "tools/landed.py")
    _git(repo, "commit", "-qm", "land via another route")

    assert _audit(repo) == []


def test_negative_path_on_live_branch_tip_is_not_reported(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _commit_files(repo, "live-wave", {"orchestrator/in_flight.py": "live\n"})
    _git(repo, "checkout", "-q", "-b", "doomed")
    target = repo / "orchestrator" / "in_flight.py"
    target.write_text("unreachable revision\n", encoding="utf-8")
    _git(repo, "add", "orchestrator/in_flight.py")
    _git(repo, "commit", "-qm", "discarded revision")
    _delete_branch(repo, "doomed")

    assert _audit(repo) == []


def test_negative_main_side_of_unreachable_merge_is_not_reported(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "-b", "doomed")
    (repo / "base.txt").write_text("branch revision\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(repo, "commit", "-qm", "branch work")

    _git(repo, "checkout", "-q", "main")
    main_side = repo / "main-side.txt"
    main_side.write_text("main side\n", encoding="utf-8")
    _git(repo, "add", "main-side.txt")
    _git(repo, "commit", "-qm", "main side addition")

    _git(repo, "checkout", "-q", "doomed")
    _git(repo, "merge", "-q", "--no-ff", "-m", "merge main", "main")
    merge_commit = _git(repo, "rev-parse", "HEAD")

    _git(repo, "checkout", "-q", "main")
    main_side.unlink()
    _git(repo, "add", "main-side.txt")
    _git(repo, "commit", "-qm", "main side deletion")
    (repo / "base.txt").write_text("main anchor\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(repo, "commit", "-qm", "main anchor")
    _git(repo, "branch", "-D", "doomed")

    assert merge_commit in ADC.unreachable_commits(repo)
    assert _audit(repo) == []


def test_negative_fold_managed_paths_are_excluded_by_default(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    lost = _commit_files(
        repo,
        "doomed",
        {
            "docs/spool/worklog/fragment.md": "spool\n",
            "docs/archive/old-fragment.md": "archive\n",
        },
    )
    _delete_branch(repo, "doomed")

    assert _audit(repo) == []
    assert _audit(repo, excluded=()) == [
        (
            lost,
            "work on doomed",
            ["docs/archive/old-fragment.md", "docs/spool/worklog/fragment.md"],
        )
    ]


def test_positive_landed_referenced_offrepo_copy_is_suppressed(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    relpath = "output/insights/wave/probe_g2_consumers.py"
    lost = _commit_files(repo, "doomed", {relpath: "probe\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "different-wave/probe_g2_consumers.py", "probe\n")
    _landed_reference(repo, external)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == []
    assert report.suppressions == [(lost, relpath, external)]
    assert report.unreferenced_copies == []


def test_positive_suppression_is_disclosed_at_rc0(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    relpath = "tools/recovered.py"
    lost = _commit_files(repo, "doomed", {relpath: "recovered\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/recovered.py", "recovered\n")
    _landed_reference(repo, external)

    assert ADC.main(["--repo", str(repo), "--offrepo-root", str(root)]) == 0
    output = capsys.readouterr().out
    assert "repo 外の同一実体で抑止 1" in output
    assert lost in output
    assert relpath in output
    assert str(external) in output
    assert "要確認 0 件" in output


def test_negative_offrepo_copy_without_landed_reference_is_reported_with_note(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    relpath = "tools/unlanded.py"
    lost = _commit_files(repo, "doomed", {relpath: "same bytes\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/unlanded.py", "same bytes\n")

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))
    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []
    assert report.unreferenced_copies == [(lost, relpath, external)]

    assert ADC.main(["--repo", str(repo), "--offrepo-root", str(root)]) == 1
    output = capsys.readouterr().out
    assert "repo 外に同一 bytes の実体あり (landed 参照なし)" in output
    assert str(external) in output


def test_negative_offrepo_same_size_different_bytes_is_reported(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/same_size.py"
    lost = _commit_files(repo, "doomed", {relpath: "abcd\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/same_size.py", "wxyz\n")
    _landed_reference(repo, external)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []
    assert report.unreferenced_copies == []


def test_negative_offrepo_mode_mismatch_is_reported(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/executable.py"
    lost = _commit_executable(repo, "doomed", relpath, "#!/bin/sh\n")
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/executable.py", "#!/bin/sh\n")
    _landed_reference(repo, external)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []


def test_negative_offrepo_root_containing_worktree_is_rejected(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    relpath = "tools/ancestor.py"
    lost = _commit_files(repo, "doomed", {relpath: "ancestor\n"})
    _delete_branch(repo, "doomed")
    external = _external_file(
        tmp_path, "copies/ancestor.py", "ancestor\n"
    )
    _landed_reference(repo, external)

    assert ADC.main(["--repo", str(repo), "--offrepo-root", str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert lost in output
    assert "探索根を拒否" in output
    assert "対象 worktree の祖先" in output
    assert "repo 外の同一実体で抑止 0" in output


def test_positive_cli_roots_override_environment(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    repo = _repo(tmp_path)
    paths = {
        "tools/from_cli.py": "cli copy\n",
        "tools/from_env.py": "env copy\n",
    }
    lost = _commit_files(repo, "doomed", paths)
    _delete_branch(repo, "doomed")
    cli_root = tmp_path / "cli-root"
    cli_second = tmp_path / "cli-second"
    env_root = tmp_path / "env-root"
    cli_external = _external_file(cli_root, "wave/from_cli.py", "cli copy\n")
    cli_second.mkdir()
    env_external = _external_file(env_root, "wave/from_env.py", "env copy\n")
    _landed_reference(repo, cli_external, env_external)
    monkeypatch.setenv("IZANAGI_DEV_WAVE_JOBS_DIR", str(env_root))

    assert ADC.main(
        [
            "--repo",
            str(repo),
            "--offrepo-root",
            str(cli_root),
            "--offrepo-root",
            str(cli_second),
        ]
    ) == 1
    output = capsys.readouterr().out
    assert f"commit {lost}: tools/from_cli.py" in output
    assert "main・全 local branch tip に不在: tools/from_env.py" in output
    assert str(cli_external) in output
    assert str(cli_second.resolve()) in output
    assert str(env_root.resolve()) not in output


def test_cli_include_fold_trees_reaches_audit_through_wrapper(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    relpath = "docs/spool/worklog/fragment.md"
    lost = _commit_files(repo, "doomed", {relpath: "fold data\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/fragment.md", "fold data\n")
    _landed_reference(repo, external)

    assert ADC.main(
        [
            "--repo",
            str(repo),
            "--offrepo-root",
            str(root),
            "--include-fold-trees",
        ]
    ) == 0
    output = capsys.readouterr().out
    assert f"commit {lost}: {relpath}" in output
    assert str(external) in output


def test_negative_unreachable_symlink_is_not_suppressed(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/link.py"
    _git(repo, "checkout", "-q", "-b", "doomed")
    target = repo / relpath
    target.parent.mkdir(parents=True)
    target.symlink_to("payload")
    _git(repo, "add", relpath)
    _git(repo, "commit", "-qm", "work on doomed")
    lost = _git(repo, "rev-parse", "HEAD")
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/link.py", "payload")
    _landed_reference(repo, external)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []
    assert report.scan_performed is False


def test_negative_root_unspecified_discloses_skip(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    relpath = "tools/no_root.py"
    lost = _commit_files(repo, "doomed", {relpath: "copy\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    _external_file(root, "wave/no_root.py", "copy\n")

    assert ADC.main(["--repo", str(repo)]) == 1
    output = capsys.readouterr().out
    assert lost in output
    assert "探索を未実施" in output
    assert "repo 外の同一実体で抑止 0" in output


def test_positive_offrepo_environment_default_is_used(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/from_environment.py"
    _commit_files(repo, "doomed", {relpath: "environment\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/from_environment.py", "environment\n")
    _landed_reference(repo, external)
    monkeypatch.setenv("IZANAGI_DEV_WAVE_JOBS_DIR", str(root))

    assert ADC.main(["--repo", str(repo)]) == 0
    output = capsys.readouterr().out
    assert str(external) in output
    assert "repo 外の同一実体で抑止 1" in output


def test_partial_offrepo_suppression_keeps_remaining_finding_and_rc1(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    lost = _commit_files(
        repo,
        "doomed",
        {"tools/copied.py": "copied\n", "tools/still_lost.py": "lost\n"},
    )
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/copied.py", "copied\n")
    _landed_reference(repo, external)

    assert ADC.main(["--repo", str(repo), "--offrepo-root", str(root)]) == 1
    output = capsys.readouterr().out
    assert f"commit {lost}: tools/copied.py" in output
    assert "main・全 local branch tip に不在: tools/still_lost.py" in output


def test_negative_offrepo_same_basename_different_size_is_reported(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/different_size.py"
    lost = _commit_files(repo, "doomed", {relpath: "short\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/different_size.py", "much longer\n")
    _landed_reference(repo, external)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []


def test_negative_offrepo_same_bytes_different_basename_is_reported(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/original_name.py"
    lost = _commit_files(repo, "doomed", {relpath: "identical\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/other_name.py", "identical\n")
    _landed_reference(repo, external)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []


def test_negative_offrepo_root_inside_worktree_is_rejected_without_suppression(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    relpath = "tools/inside.py"
    lost = _commit_files(repo, "doomed", {relpath: "inside\n"})
    _delete_branch(repo, "doomed")
    root = repo / "untracked-copies"
    external = _external_file(root, "wave/inside.py", "inside\n")
    _landed_reference(repo, external)

    assert ADC.main(["--repo", str(repo), "--offrepo-root", str(root)]) == 1
    output = capsys.readouterr().out
    assert lost in output
    assert "対象 worktree の子孫" in output
    assert "repo 外の同一実体で抑止 0" in output


@pytest.mark.parametrize("kind", ["symlink", "fifo"])
def test_negative_offrepo_candidate_kind_is_not_external_copy(
    tmp_path: Path, monkeypatch, kind: str,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/special.py"
    lost = _commit_files(repo, "doomed", {relpath: "special\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    candidate = root / "wave" / "special.py"
    candidate.parent.mkdir(parents=True)
    if kind == "symlink":
        target = root / "payload"
        target.write_text("special\n", encoding="utf-8")
        candidate.symlink_to(target)
    else:
        os.mkfifo(candidate)
        real_open = ADC.os.open

        def fail_if_fifo(path, flags, *args, **kwargs):
            if Path(path) == candidate:
                raise AssertionError("FIFO must be rejected before os.open")
            return real_open(path, flags, *args, **kwargs)

        monkeypatch.setattr(ADC.os, "open", fail_if_fifo)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []


def test_negative_offrepo_read_error_keeps_finding_and_is_not_rc2(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    relpath = "tools/unreadable.py"
    lost = _commit_files(repo, "doomed", {relpath: "unreadable\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/unreadable.py", "unreadable\n")
    _landed_reference(repo, external)
    real_open = ADC.os.open

    def deny_candidate(path, flags, *args, **kwargs):
        if Path(path) == external:
            raise PermissionError("test read denial")
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(ADC.os, "open", deny_candidate)

    assert ADC.main(["--repo", str(repo), "--offrepo-root", str(root)]) == 1
    output = capsys.readouterr().out
    assert lost in output
    assert "repo 外候補の確認不能 1 件 (抑止せず)" in output


def test_offrepo_scan_is_skipped_without_candidate_basenames(
    tmp_path: Path, monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    root = tmp_path / "offrepo"
    root.mkdir()

    def fail_walk(*_args, **_kwargs):
        raise AssertionError("os.walk must not run without candidate basenames")

    monkeypatch.setattr(ADC.os, "walk", fail_walk)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == []
    assert report.scan_performed is False


def test_negative_unreadable_offrepo_root_keeps_finding(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    relpath = "tools/root_denied.py"
    lost = _commit_files(repo, "doomed", {relpath: "denied\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    _external_file(root, "wave/root_denied.py", "denied\n")
    root.chmod(0)
    try:
        assert ADC.main(["--repo", str(repo), "--offrepo-root", str(root)]) == 1
    finally:
        root.chmod(0o755)
    output = capsys.readouterr().out
    assert lost in output
    assert "repo 外候補の確認不能 1 件 (抑止せず)" in output


def test_negative_oversize_blob_is_reported_without_scan(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    assert ADC.MAX_BLOB_SIZE == 32 * 1024 * 1024
    monkeypatch.setattr(ADC, "MAX_BLOB_SIZE", 4)
    repo = _repo(tmp_path)
    relpath = "tools/oversize.py"
    lost = _commit_files(repo, "doomed", {relpath: "12345"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/oversize.py", "12345")
    _landed_reference(repo, external)

    assert ADC.main(["--repo", str(repo), "--offrepo-root", str(root)]) == 1
    output = capsys.readouterr().out
    assert lost in output
    assert "oversize (抑止せず)" in output
    assert "照合可能な候補 basename 0 件のため走査省略" in output


def test_negative_filesystem_root_is_rejected(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    relpath = "tools/root.py"
    lost = _commit_files(repo, "doomed", {relpath: "root\n"})
    _delete_branch(repo, "doomed")

    assert ADC.main(["--repo", str(repo), "--offrepo-root", os.sep]) == 1
    output = capsys.readouterr().out
    assert lost in output
    assert "filesystem root は探索範囲が広すぎる" in output


def test_positive_landed_reference_to_descendant_directory_suppresses(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/directory_reference.py"
    lost = _commit_files(repo, "doomed", {relpath: "directory ref\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(
        root, "wave/nested/directory_reference.py", "directory ref\n"
    )
    _landed_reference(repo, external.parent)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == []
    assert report.suppressions == [(lost, relpath, external)]


def test_negative_reference_to_search_root_itself_does_not_suppress(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/root_reference.py"
    lost = _commit_files(repo, "doomed", {relpath: "root ref\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "root_reference.py", "root ref\n")
    _landed_reference(repo, root.resolve())

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []
    assert report.unreferenced_copies == [(lost, relpath, external)]


def test_negative_landed_reference_check_failure_keeps_finding(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    relpath = "tools/grep_failure.py"
    lost = _commit_files(repo, "doomed", {relpath: "grep failure\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/grep_failure.py", "grep failure\n")
    _landed_reference(repo, external)
    real_git_bytes = ADC._git_bytes

    def fail_grep(repo_path, *args):
        if args and args[0] == "grep":
            return subprocess.CompletedProcess(args, 2, b"", b"grep failed")
        return real_git_bytes(repo_path, *args)

    monkeypatch.setattr(ADC, "_git_bytes", fail_grep)

    assert ADC.main(["--repo", str(repo), "--offrepo-root", str(root)]) == 1
    output = capsys.readouterr().out
    assert lost in output
    assert "landed 参照確認不能 (抑止せず)" in output
    assert "repo 外の同一実体で抑止 0" in output


def test_negative_landed_reference_prefix_collision_does_not_suppress(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    lost = _commit_files(
        repo,
        "doomed",
        {"tools/a.py": "first\n", "tools/a.py.backup": "backup\n"},
    )
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    first = _external_file(root, "w/a.py", "first\n")
    backup = _external_file(root, "w/a.py.backup", "backup\n")
    _landed_reference(repo, backup)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == [(lost, "work on doomed", ["tools/a.py"])]
    assert report.suppressions == [(lost, "tools/a.py.backup", backup)]
    assert report.unreferenced_copies == [(lost, "tools/a.py", first)]


def test_negative_landed_reference_plus_suffix_collision_does_not_suppress(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/a.py"
    lost = _commit_files(repo, "doomed", {relpath: "plus suffix\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "w/a.py", "plus suffix\n")
    _landed_reference(repo, Path(str(external) + "+backup"))

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []
    assert report.unreferenced_copies == [(lost, relpath, external)]


def test_negative_landed_reference_non_ascii_suffix_does_not_suppress(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/a.py"
    lost = _commit_files(repo, "doomed", {relpath: "non-ASCII suffix\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "w/a.py", "non-ASCII suffix\n")
    _landed_reference(repo, Path(str(external) + "。"))

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []
    assert report.unreferenced_copies == [(lost, relpath, external)]


def test_positive_landed_reference_found_after_invalid_occurrence(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/a.py"
    lost = _commit_files(repo, "doomed", {relpath: "later valid reference\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "w/a.py", "later valid reference\n")
    _landed_reference(repo, Path(str(external) + "+backup"), external)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == []
    assert report.suppressions == [(lost, relpath, external)]
    assert report.unreferenced_copies == []


def test_negative_landed_reference_left_boundary_collision_does_not_suppress(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/a.py"
    lost = _commit_files(repo, "doomed", {relpath: "left boundary\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "w/a.py", "left boundary\n")
    extended_absolute_path = Path("/other" + str(external))
    _landed_reference(repo, extended_absolute_path)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []
    assert report.unreferenced_copies == [(lost, relpath, external)]


def test_negative_external_file_changed_during_comparison_is_not_suppressed(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/changing.py"
    lost = _commit_files(repo, "doomed", {relpath: "stable bytes\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/changing.py", "stable bytes\n")
    _landed_reference(repo, external)
    external_stat = external.lstat()
    real_fstat = ADC.os.fstat
    target_fstat_calls = 0

    def changed_after_comparison(descriptor):
        nonlocal target_fstat_calls
        current = real_fstat(descriptor)
        if (
            current.st_dev != external_stat.st_dev
            or current.st_ino != external_stat.st_ino
        ):
            return current
        target_fstat_calls += 1
        if target_fstat_calls == 2:
            return SimpleNamespace(
                st_dev=current.st_dev,
                st_ino=current.st_ino,
                st_mode=current.st_mode,
                st_size=current.st_size,
                st_mtime_ns=current.st_mtime_ns + 1,
                st_ctime_ns=current.st_ctime_ns,
            )
        return current

    monkeypatch.setattr(ADC.os, "fstat", changed_after_comparison)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert target_fstat_calls == 2
    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []
    assert report.scan_failures == 1
    ADC._print_offrepo_report(report)
    assert "repo 外候補の確認不能 1 件 (抑止せず)" in capsys.readouterr().out


def test_negative_external_file_ctime_change_during_comparison_is_not_suppressed(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/changing_ctime.py"
    lost = _commit_files(repo, "doomed", {relpath: "stable bytes\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/changing_ctime.py", "stable bytes\n")
    _landed_reference(repo, external)
    external_stat = external.lstat()
    real_fstat = ADC.os.fstat
    target_fstat_calls = 0

    def changed_after_comparison(descriptor):
        nonlocal target_fstat_calls
        current = real_fstat(descriptor)
        if (
            current.st_dev != external_stat.st_dev
            or current.st_ino != external_stat.st_ino
        ):
            return current
        target_fstat_calls += 1
        if target_fstat_calls == 2:
            return SimpleNamespace(
                st_dev=current.st_dev,
                st_ino=current.st_ino,
                st_mode=current.st_mode,
                st_size=current.st_size,
                st_mtime_ns=current.st_mtime_ns,
                st_ctime_ns=current.st_ctime_ns + 1,
            )
        return current

    monkeypatch.setattr(ADC.os, "fstat", changed_after_comparison)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert target_fstat_calls == 2
    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []
    assert report.scan_failures == 1
    ADC._print_offrepo_report(report)
    assert "repo 外候補の確認不能 1 件 (抑止せず)" in capsys.readouterr().out


def test_git_grep_pattern_batches_pin_count_limit_shape() -> None:
    repo = Path("/tmp/repo-for-count-limit")
    main_ref = "count-limit-snapshot"
    patterns = ("p0", "p1", "p2", "p3", "p4")
    assert len(patterns) == 5
    byte_budget = 1_000_000

    batches = ADC._git_grep_pattern_batches(
        repo,
        main_ref,
        patterns,
        max_patterns_per_batch=2,
        max_argv_bytes=byte_budget,
    )

    assert batches == (("p0", "p1"), ("p2", "p3"), ("p4",))
    assert tuple(pattern for batch in batches for pattern in batch) == patterns


def test_git_grep_pattern_batches_pin_argv_byte_limit_shape(monkeypatch) -> None:
    repo = Path("/tmp/repo-for-byte-limit")
    main_ref = "byte-limit-snapshot"
    over_budget = "x" * 40
    patterns = ("aa", "bbb", over_budget, "c", "dd")
    byte_budget = ADC._git_grep_argv_size(repo, main_ref, patterns[:2])

    batches = ADC._git_grep_pattern_batches(
        repo,
        main_ref,
        patterns,
        max_patterns_per_batch=100,
        max_argv_bytes=byte_budget,
    )

    assert batches == (("aa", "bbb"), (over_budget,), ("c", "dd"))
    assert tuple(pattern for batch in batches for pattern in batch) == patterns
    assert ADC._git_grep_argv_size(repo, main_ref, (over_budget,)) > byte_budget
    for batch, next_batch in zip(batches, batches[1:]):
        candidate = batch + (next_batch[0],)
        assert (
            len(candidate) > 100
            or ADC._git_grep_argv_size(repo, main_ref, candidate) > byte_budget
        )

    with pytest.raises(ValueError):
        ADC._git_grep_pattern_batches(
            repo,
            main_ref,
            patterns,
            max_patterns_per_batch=0,
            max_argv_bytes=byte_budget,
        )
    with pytest.raises(ValueError):
        ADC._git_grep_pattern_batches(
            repo,
            main_ref,
            patterns,
            max_patterns_per_batch=100,
            max_argv_bytes=0,
        )

    root = Path("/offrepo")
    external = root / over_budget
    matches = {
        ("commit", "tools/over-budget.py"): [
            ADC._ExternalMatch(external, root)
        ]
    }
    grep_calls: list[tuple[str, ...]] = []
    sentinel = OSError(errno.E2BIG, "synthetic executor limit")

    def raise_from_executor(_repo_path, *args):
        grep_calls.append(args)
        raise sentinel

    monkeypatch.setattr(ADC, "_git_bytes", raise_from_executor)
    with pytest.raises(OSError) as excinfo:
        ADC._landed_reference_matches(
            repo,
            main_ref,
            matches,
            max_patterns_per_batch=100,
            max_argv_bytes=1,
        )
    assert excinfo.value is sentinel
    assert len(grep_calls) == 1
    assert _grep_patterns(grep_calls[0]) == (str(external),)


def test_git_grep_argv_size_matches_independently_computed_argv() -> None:
    repo = Path("/tmp/非ASCII-repo")
    main_ref = "0123456789abcdef-snapshot"
    patterns = ("/tmp/plain path", "/tmp/波/参照.py")
    argv = [
        "git",
        "-C",
        str(repo),
        "grep",
        "-F",
        "-l",
        "-z",
        "-e",
        "/tmp/plain path",
        "-e",
        "/tmp/波/参照.py",
        "0123456789abcdef-snapshot",
        "--",
    ]
    encoded_payload_bytes = sum(len(os.fsencode(argument)) for argument in argv)
    expected = encoded_payload_bytes + len(argv)

    assert ADC._git_grep_argv_size(repo, main_ref, patterns) == expected
    assert expected > encoded_payload_bytes
    assert len(os.fsencode(patterns[1])) > len(patterns[1])


def test_positive_git_grep_batches_survive_env_derived_e2big_population() -> None:
    """当該 host の空 environment・/bin/true に対する母集合真正性を固定する。"""
    arg_max = int(os.sysconf("SC_ARG_MAX"))
    assert arg_max > 0
    pattern_length = 96
    population = arg_max // (pattern_length + 1) + 1
    patterns = tuple(
        f"{index:0{pattern_length}d}" for index in range(population)
    )
    assert all(len(pattern) == pattern_length for pattern in patterns)
    assert sum(len(os.fsencode(pattern)) + 1 for pattern in patterns) > arg_max
    assert len(patterns) > ADC.GIT_GREP_BATCH_MAX_PATTERNS

    with pytest.raises(OSError) as excinfo:
        subprocess.run(["/bin/true", *patterns], env={}, check=False)
    assert excinfo.value.errno == errno.E2BIG

    repo = Path("/tmp/repo-for-e2big-control")
    main_ref = "e2big-control-snapshot"
    batches = ADC._git_grep_pattern_batches(repo, main_ref, patterns)

    assert batches
    assert len(batches) >= 2
    assert tuple(pattern for batch in batches for pattern in batch) == patterns
    assert all(
        len(batch) <= ADC.GIT_GREP_BATCH_MAX_PATTERNS
        and ADC._git_grep_argv_size(repo, main_ref, batch)
        <= ADC.GIT_GREP_BATCH_MAX_ARGV_BYTES
        for batch in batches
    )


def test_positive_landed_reference_matches_batches_merge_like_single_grep(
    tmp_path: Path, monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    root = tmp_path / "offrepo"
    first = root / "a-hit"
    middle = root / "b-miss"
    last = root / "c-hit"
    matches = {
        ("commit-a", "tools/a.py"): [ADC._ExternalMatch(first, root)],
        ("commit-b", "tools/b.py"): [ADC._ExternalMatch(middle, root)],
        ("commit-c", "tools/c.py"): [ADC._ExternalMatch(last, root)],
    }
    _landed_reference(repo, first, last)
    main_commit = _git(repo, "rev-parse", "main")
    expected = {
        ("commit-a", "tools/a.py"): [first],
        ("commit-c", "tools/c.py"): [last],
    }

    single, single_failure = ADC._landed_reference_matches(
        repo,
        main_commit,
        matches,
        max_patterns_per_batch=100,
        max_argv_bytes=1024 * 1024,
    )
    assert single_failure is None

    real_git_bytes = ADC._git_bytes
    grep_batches: list[tuple[str, ...]] = []
    show_calls = 0

    def record_split_calls(repo_path, *args):
        nonlocal show_calls
        if args and args[0] == "grep":
            grep_batches.append(_grep_patterns(args))
        elif args and args[0] == "show":
            show_calls += 1
        return real_git_bytes(repo_path, *args)

    monkeypatch.setattr(ADC, "_git_bytes", record_split_calls)
    split, split_failure = ADC._landed_reference_matches(
        repo,
        main_commit,
        matches,
        max_patterns_per_batch=1,
        max_argv_bytes=1024 * 1024,
    )

    assert split_failure is None
    assert split == single == expected
    assert grep_batches == [(str(first),), (str(middle),), (str(last),)]
    assert show_calls == 1


def test_positive_landed_reference_matches_keeps_hit_after_two_leading_misses(
    monkeypatch,
) -> None:
    repo = Path("/tmp/fake-leading-misses-repo")
    main_ref = "leading-misses-snapshot"
    root = Path("/offrepo")
    first_miss = root / "a-miss"
    second_miss = root / "b-miss"
    late_hit = root / "c-hit"
    matches = {
        ("commit-a", "tools/a.py"): [ADC._ExternalMatch(first_miss, root)],
        ("commit-b", "tools/b.py"): [ADC._ExternalMatch(second_miss, root)],
        ("commit-c", "tools/c.py"): [ADC._ExternalMatch(late_hit, root)],
    }
    grep_batches: list[tuple[str, ...]] = []
    show_calls: list[str] = []

    def miss_miss_hit(_repo_path, *args):
        if args[0] == "grep":
            batch = _grep_patterns(args)
            grep_batches.append(batch)
            if batch != (str(late_hit),):
                return subprocess.CompletedProcess(args, 1, b"", b"")
            return subprocess.CompletedProcess(
                args, 0, f"{main_ref}:docs/late-hit.md\0".encode(), b""
            )
        assert args[0] == "show"
        show_calls.append(args[1])
        return subprocess.CompletedProcess(
            args, 0, f"{late_hit}\n".encode(), b""
        )

    monkeypatch.setattr(ADC, "_git_bytes", miss_miss_hit)

    referenced, failure = ADC._landed_reference_matches(
        repo,
        main_ref,
        matches,
        max_patterns_per_batch=1,
        max_argv_bytes=1024 * 1024,
    )

    assert failure is None
    assert referenced == {("commit-c", "tools/c.py"): [late_hit]}
    assert grep_batches == [
        (str(first_miss),),
        (str(second_miss),),
        (str(late_hit),),
    ]
    assert show_calls == [f"{main_ref}:docs/late-hit.md"]


def test_positive_landed_reference_matches_keeps_same_basename_tree_paths(
    monkeypatch,
) -> None:
    repo = Path("/tmp/fake-same-basename-repo")
    main_ref = "same-basename-snapshot"
    root = Path("/offrepo")
    external = root / "target"
    matches = {
        ("commit-target", "tools/target.py"): [
            ADC._ExternalMatch(external, root)
        ],
    }
    first_tree_path = "docs/first/config.md"
    second_tree_path = "docs/second/config.md"
    show_calls: list[str] = []

    def same_basename_hits(_repo_path, *args):
        if args[0] == "grep":
            return subprocess.CompletedProcess(
                args,
                0,
                (
                    f"{main_ref}:{first_tree_path}\0"
                    f"{main_ref}:{second_tree_path}\0"
                ).encode(),
                b"",
            )
        assert args[0] == "show"
        show_calls.append(args[1])
        if args[1] == f"{main_ref}:{first_tree_path}":
            return subprocess.CompletedProcess(args, 0, b"unrelated\n", b"")
        assert args[1] == f"{main_ref}:{second_tree_path}"
        return subprocess.CompletedProcess(
            args, 0, f"{external}\n".encode(), b""
        )

    monkeypatch.setattr(ADC, "_git_bytes", same_basename_hits)

    referenced, failure = ADC._landed_reference_matches(
        repo, main_ref, matches
    )

    assert failure is None
    assert referenced == {("commit-target", "tools/target.py"): [external]}
    assert show_calls == [
        f"{main_ref}:{first_tree_path}",
        f"{main_ref}:{second_tree_path}",
    ]


@pytest.mark.parametrize(
    ("failure_mode", "expected_show_calls", "failure_fragment"),
    (
        ("later-grep-rc", 0, "batch 2/2 rc=2"),
        ("later-invalid-prefix", 0, "path 出力を解釈できない"),
        ("first-show", 1, "landed file の参照確認不能"),
        ("second-show", 2, "landed file の参照確認不能"),
    ),
    ids=(
        "later-grep-rc",
        "later-invalid-prefix",
        "first-show",
        "second-show",
    ),
)
def test_negative_landed_reference_matches_discard_all_on_later_batch_failure(
    monkeypatch,
    failure_mode: str,
    expected_show_calls: int,
    failure_fragment: str,
) -> None:
    repo = Path("/tmp/fake-repo")
    main_ref = "immutable-snapshot"
    root = Path("/offrepo")
    first = root / "a-hit"
    second = root / "b-hit"
    matches = {
        ("commit-a", "tools/a.py"): [ADC._ExternalMatch(first, root)],
        ("commit-b", "tools/b.py"): [ADC._ExternalMatch(second, root)],
    }
    grep_calls = 0
    show_calls = 0

    def fail_later(_repo_path, *args):
        nonlocal grep_calls, show_calls
        if args[0] == "grep":
            grep_calls += 1
            if grep_calls == 1:
                return subprocess.CompletedProcess(
                    args, 0, f"{main_ref}:docs/one\0".encode(), b""
                )
            if failure_mode == "later-grep-rc":
                return subprocess.CompletedProcess(args, 2, b"partial", b"fatal")
            if failure_mode == "later-invalid-prefix":
                return subprocess.CompletedProcess(
                    args, 0, b"different-ref:docs/two\0", b""
                )
            return subprocess.CompletedProcess(
                args, 0, f"{main_ref}:docs/two\0".encode(), b""
            )
        assert args[0] == "show"
        show_calls += 1
        if failure_mode == "first-show" and show_calls == 1:
            return subprocess.CompletedProcess(
                args, 128, f"{first}\n".encode(), b""
            )
        if failure_mode == "second-show" and show_calls == 2:
            return subprocess.CompletedProcess(args, 128, b"", b"show failed")
        return subprocess.CompletedProcess(
            args, 0, f"{first}\n{second}\n".encode(), b""
        )

    monkeypatch.setattr(ADC, "_git_bytes", fail_later)

    referenced, failure = ADC._landed_reference_matches(
        repo,
        main_ref,
        matches,
        max_patterns_per_batch=1,
        max_argv_bytes=1024 * 1024,
    )

    assert referenced == {}
    assert failure is not None
    assert failure_fragment in failure
    if failure_mode == "later-grep-rc":
        assert "fatal" in failure
        assert "partial" in failure
    assert show_calls == expected_show_calls


def test_positive_landed_reference_matches_runs_batched_over_oversized_population(
    monkeypatch,
) -> None:
    repo = Path("/tmp/fake-oversized-repo")
    main_ref = "oversized-population-snapshot"
    root = Path("/offrepo")
    population = ADC.GIT_GREP_BATCH_MAX_PATTERNS + 1
    patterns = tuple(str(root / f"pattern-{index:04d}") for index in range(population))
    assert len(patterns) > ADC.GIT_GREP_BATCH_MAX_PATTERNS
    matches = {
        (f"commit-{index:04d}", f"tools/{index:04d}.py"): [
            ADC._ExternalMatch(Path(pattern), root)
        ]
        for index, pattern in enumerate(patterns)
    }
    grep_batches: list[tuple[str, ...]] = []
    show_calls = 0

    def fake_git_bytes(_repo_path, *args):
        nonlocal show_calls
        if args[0] == "grep":
            grep_batches.append(_grep_patterns(args))
            return subprocess.CompletedProcess(
                args, 0, f"{main_ref}:docs/landed\0".encode(), b""
            )
        assert args[0] == "show"
        show_calls += 1
        return subprocess.CompletedProcess(
            args, 0, ("\n".join(patterns) + "\n").encode(), b""
        )

    monkeypatch.setattr(ADC, "_git_bytes", fake_git_bytes)

    referenced, failure = ADC._landed_reference_matches(repo, main_ref, matches)

    assert failure is None
    assert grep_batches
    assert len(grep_batches) == 2
    assert tuple(pattern for batch in grep_batches for pattern in batch) == patterns
    assert all(
        len(batch) <= ADC.GIT_GREP_BATCH_MAX_PATTERNS
        and ADC._git_grep_argv_size(repo, main_ref, batch)
        <= ADC.GIT_GREP_BATCH_MAX_ARGV_BYTES
        for batch in grep_batches
    )
    assert referenced == {
        key: [external_matches[0].path]
        for key, external_matches in matches.items()
    }
    assert show_calls == 1


def test_positive_landed_reference_matches_executes_all_five_batches(
    monkeypatch,
) -> None:
    repo = Path("/tmp/fake-five-batch-repo")
    main_ref = "five-batch-snapshot"
    root = Path("/offrepo")
    patterns = tuple(str(root / f"pattern-{index}") for index in range(5))
    matches = {
        (f"commit-{index}", f"tools/{index}.py"): [
            ADC._ExternalMatch(Path(pattern), root)
        ]
        for index, pattern in enumerate(patterns)
    }
    grep_batches: list[tuple[str, ...]] = []
    show_calls: list[str] = []
    contents_by_tree: dict[str, bytes] = {}

    def distinct_tree_per_batch(_repo_path, *args):
        if args[0] == "grep":
            batch = _grep_patterns(args)
            grep_batches.append(batch)
            tree_path = f"docs/batch-{len(grep_batches)}.md"
            contents_by_tree[f"{main_ref}:{tree_path}"] = (
                "\n".join(batch) + "\n"
            ).encode()
            return subprocess.CompletedProcess(
                args, 0, f"{main_ref}:{tree_path}\0".encode(), b""
            )
        assert args[0] == "show"
        show_calls.append(args[1])
        return subprocess.CompletedProcess(
            args, 0, contents_by_tree[args[1]], b""
        )

    monkeypatch.setattr(ADC, "_git_bytes", distinct_tree_per_batch)

    referenced, failure = ADC._landed_reference_matches(
        repo,
        main_ref,
        matches,
        max_patterns_per_batch=1,
        max_argv_bytes=1024 * 1024,
    )

    assert failure is None
    assert len(grep_batches) == 5
    assert grep_batches == [(pattern,) for pattern in patterns]
    assert tuple(pattern for batch in grep_batches for pattern in batch) == patterns
    assert show_calls == [
        f"{main_ref}:docs/batch-{index}.md" for index in range(1, 6)
    ]
    assert referenced == {
        key: [external_matches[0].path]
        for key, external_matches in matches.items()
    }


def test_positive_landed_reference_matches_pins_main_ref_to_single_commit(
    tmp_path: Path, monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    lost = _commit_files(
        repo,
        "doomed",
        {"tools/first.py": "first\n", "tools/second.py": "second\n"},
    )
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    first = _external_file(root, "one/first.py", "first\n")
    second = _external_file(root, "two/second.py", "second\n")
    _landed_reference(repo, first)
    snapshot_commit = _git(repo, "rev-parse", "main")

    _git(repo, "checkout", "-q", "-b", "future")
    landed = repo / "docs" / "landed-copy.md"
    landed.write_text(f"landed references\n{second}\n", encoding="utf-8")
    _git(repo, "add", "docs/landed-copy.md")
    _git(repo, "commit", "-qm", "move landed reference")
    future_commit = _git(repo, "rev-parse", "future")

    real_batches = ADC._git_grep_pattern_batches

    def force_singleton_batches(repo_path, ref, patterns, **_limits):
        return real_batches(
            repo_path,
            ref,
            patterns,
            max_patterns_per_batch=1,
            max_argv_bytes=ADC.GIT_GREP_BATCH_MAX_ARGV_BYTES,
        )

    monkeypatch.setattr(
        ADC, "_git_grep_pattern_batches", force_singleton_batches
    )
    real_checked_git = ADC._checked_git
    real_audit = ADC.audit
    real_landed_reference_matches = ADC._landed_reference_matches
    real_git_bytes = ADC._git_bytes
    symbolic_resolution_results: list[str] = []
    audit_main_refs: list[str] = []
    landed_main_refs: list[str] = []
    grep_refs: list[str] = []
    show_refs: list[str] = []

    def record_checked_git(repo_path, *args):
        result = real_checked_git(repo_path, *args)
        if args == ("rev-parse", "--verify", "main^{commit}"):
            symbolic_resolution_results.append(result.strip())
        return result

    def record_audit(repo_path, ref, excluded_prefixes):
        audit_main_refs.append(ref)
        return real_audit(repo_path, ref, excluded_prefixes)

    def record_landed_reference_matches(repo_path, ref, found_matches, **limits):
        landed_main_refs.append(ref)
        return real_landed_reference_matches(
            repo_path, ref, found_matches, **limits
        )

    def move_main_after_first_grep(repo_path, *args):
        if args[0] == "grep":
            grep_refs.append(args[-2])
            result = real_git_bytes(repo_path, *args)
            if len(grep_refs) == 1:
                _git(repo, "branch", "-f", "main", future_commit)
            return result
        if args[0] == "show":
            show_refs.append(args[1].split(":", 1)[0])
        return real_git_bytes(repo_path, *args)

    monkeypatch.setattr(ADC, "_checked_git", record_checked_git)
    monkeypatch.setattr(ADC, "audit", record_audit)
    monkeypatch.setattr(
        ADC, "_landed_reference_matches", record_landed_reference_matches
    )
    monkeypatch.setattr(ADC, "_git_bytes", move_main_after_first_grep)

    report = ADC.audit_with_offrepo(repo, "main", offrepo_roots=(root,))

    assert symbolic_resolution_results == [snapshot_commit]
    assert audit_main_refs == landed_main_refs == [snapshot_commit]
    assert len(grep_refs) >= 2
    assert show_refs
    assert set(grep_refs) == {snapshot_commit}
    assert set(show_refs) == {snapshot_commit}
    assert _git(repo, "rev-parse", "main") == future_commit
    assert report.findings == [(lost, "work on doomed", ["tools/second.py"])]
    assert report.suppressions == [(lost, "tools/first.py", first)]
    assert report.unreferenced_copies == [(lost, "tools/second.py", second)]


def test_git_grep_batch_limits_stay_within_policy_bounds() -> None:
    assert ADC.GIT_GREP_BATCH_MAX_PATTERNS == 512
    assert ADC.GIT_GREP_BATCH_MAX_ARGV_BYTES == 128 * 1024
    assert ADC.GIT_GREP_BATCH_MAX_PATTERNS <= 512
    assert ADC.GIT_GREP_BATCH_MAX_ARGV_BYTES <= 128 * 1024


def test_landed_reference_git_grep_runs_once_for_all_bytes_matches(
    tmp_path: Path, monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    lost = _commit_files(
        repo,
        "doomed",
        {"tools/first.py": "first\n", "tools/second.py": "second\n"},
    )
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    first = _external_file(root, "one/first.py", "first\n")
    second = _external_file(root, "two/second.py", "second\n")
    _landed_reference(repo, first, second)
    real_git_bytes = ADC._git_bytes
    grep_calls = 0

    def count_grep(repo_path, *args):
        nonlocal grep_calls
        if args and args[0] == "grep":
            grep_calls += 1
        return real_git_bytes(repo_path, *args)

    monkeypatch.setattr(ADC, "_git_bytes", count_grep)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert grep_calls == 1
    assert report.findings == []
    assert report.suppressions == [
        (lost, "tools/first.py", first),
        (lost, "tools/second.py", second),
    ]


def test_positive_executable_mode_match_is_suppressed(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/executable_match.py"
    lost = _commit_executable(repo, "doomed", relpath, "#!/bin/sh\n")
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(
        root, "wave/executable_match.py", "#!/bin/sh\n", executable=True
    )
    _landed_reference(repo, external)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == []
    assert report.suppressions == [(lost, relpath, external)]


def test_negative_unreachable_deletion_is_not_suppressed(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/deleted.py"
    added = _commit_files(repo, "doomed", {relpath: "deleted later\n"})
    target = repo / relpath
    target.unlink()
    _git(repo, "add", relpath)
    _git(repo, "commit", "-qm", "delete on doomed")
    deletion = _git(repo, "rev-parse", "HEAD")
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/deleted.py", "deleted later\n")
    _landed_reference(repo, external)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert (added, relpath, external) in report.suppressions
    assert (deletion, "delete on doomed", [relpath]) in report.findings


def test_negative_offrepo_root_equal_worktree_is_rejected(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    relpath = "tools/equal_root.py"
    lost = _commit_files(repo, "doomed", {relpath: "equal\n"})
    _delete_branch(repo, "doomed")

    assert ADC.main(["--repo", str(repo), "--offrepo-root", str(repo)]) == 1
    output = capsys.readouterr().out
    assert lost in output
    assert "対象 worktree と同一" in output


def _run() -> int:
    """pytest fixtures を含む全 node を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
