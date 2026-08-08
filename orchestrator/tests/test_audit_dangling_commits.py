# -*- coding: utf-8 -*-
"""消えたブランチの未 land 作業を検出する監査の controls。"""

from __future__ import annotations

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
