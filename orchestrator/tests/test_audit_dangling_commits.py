# -*- coding: utf-8 -*-
"""消えたブランチの未 land 作業を検出する監査の controls。"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

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


def _audit(repo: Path, excluded=ADC.DEFAULT_EXCLUDED_PREFIXES):
    return ADC.audit(repo, "main", excluded)


def test_positive_control_deleted_branch_work_is_reported(
    tmp_path: Path, capsys,
) -> None:
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
    tmp_path: Path, capsys,
) -> None:
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


def test_help_discloses_detection_limitations(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        ADC.main(["--help"])

    assert excinfo.value.code == 0
    assert ADC.LIMITATION_NOTICE in capsys.readouterr().out


def test_decode_error_is_execution_failure(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
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


def _run() -> int:
    """pytest fixtures を含む全 node を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
