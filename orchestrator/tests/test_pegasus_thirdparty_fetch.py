# -*- coding: utf-8 -*-
"""Pegasus third-party fetch helper を local Git fixture だけで検証する。"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


REPO = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO / "tools" / "pegasus" / "fetch_third_party.py"
NAMES = ("masstree", "mimalloc", "googletest")
ALL_NAMES = (*NAMES, "gflags", "glog")
STAGING_RELATIVE = Path(
    "output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src"
)


def _load_tool():
    spec = importlib.util.spec_from_file_location("fetch_third_party", TOOL_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class GitFixture:
    repo: Path
    cache: Path
    upstream_root: Path
    global_config: Path
    pins: dict[str, str]
    urls: dict[str, str]
    dependencies: dict[str, Path]
    dependency_pins: dict[str, str]


def _git_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ALLOW_PROTOCOL": "file",
        }
    )
    return env


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=_git_env(),
    )


def _make_repo(path: Path, *, ignored_fixture: bool = False) -> str:
    path.mkdir(parents=True)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "-q", str(path)],
        check=True,
        env=_git_env(),
    )
    _git(path, "config", "user.email", "fixture@example.invalid")
    _git(path, "config", "user.name", "Fixture")
    (path / "tracked.txt").write_text(f"fixture:{path.name}\n", encoding="utf-8")
    if ignored_fixture:
        (path / ".gitignore").write_text("*.a\n/config.h\n", encoding="utf-8")
    _git(path, "add", ".")
    _git(path, "commit", "-qm", "fixture")
    return _git(path, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def git_fixture(tmp_path: Path) -> GitFixture:
    repo = tmp_path / "repo"
    policy_dir = repo / "tools" / "pegasus"
    cmake_dir = repo / "external" / "ccbench" / "cmake"
    policy_dir.mkdir(parents=True)
    cmake_dir.mkdir(parents=True)
    upstream_root = tmp_path / "upstreams"
    upstream_root.mkdir()
    pins: dict[str, str] = {}
    urls: dict[str, str] = {}
    sources: list[dict[str, str]] = []
    cmake_lines: list[str] = []
    for name in NAMES:
        upstream = upstream_root / f"{name}.git"
        pins[name] = _make_repo(upstream, ignored_fixture=name == "masstree")
        urls[name] = f"https://github.com/fixture/{name}.git"
        sources.append(
            {
                "name": name,
                "source_name": name,
                "url": urls[name],
                "fetchcontent_ref": pins[name],
                "pin": pins[name],
            }
        )
        prefix = f"CCBENCH_{name.upper()}"
        cmake_lines.extend(
            [
                f'set({prefix}_REPO "{urls[name]}")',
                f'set({prefix}_TAG "{pins[name]}")',
            ]
        )
    dependencies: dict[str, Path] = {}
    dependency_pins: dict[str, str] = {}
    for name in ("gflags", "glog"):
        dependencies[name] = upstream_root / f"{name}.git"
        dependency_pins[name] = _make_repo(dependencies[name])
        pins[name] = dependency_pins[name]
        urls[name] = f"https://github.com/fixture/{name}.git"
    policy = {
        "gflags_source_url": urls["gflags"],
        "gflags_expected_head": dependency_pins["gflags"],
        "glog_source_url": urls["glog"],
        "glog_expected_head": dependency_pins["glog"],
        "silo_ladder_rung1": {
            "dependency_pins": dependency_pins,
            "third_party_sources": sources,
        },
    }
    (policy_dir / "policy.json").write_text(
        json.dumps(policy, indent=2) + "\n", encoding="utf-8"
    )
    (cmake_dir / "ThirdParty.cmake").write_text(
        "\n".join(cmake_lines) + "\n", encoding="utf-8"
    )
    global_config = tmp_path / "fixture.gitconfig"
    global_config.write_text(
        '[url "' + upstream_root.as_uri() + '/"]\n'
        "\tinsteadOf = https://github.com/fixture/\n",
        encoding="utf-8",
    )
    return GitFixture(
        repo=repo,
        cache=tmp_path / "cache",
        upstream_root=upstream_root,
        global_config=global_config,
        pins=pins,
        urls=urls,
        dependencies=dependencies,
        dependency_pins=dependency_pins,
    )


def _enable_local_fetch(tool, fixture: GitFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    original = tool._git_environment

    def local_environment(protocol: str) -> dict[str, str]:
        env = original(protocol)
        if protocol == "https":
            env["GIT_CONFIG_GLOBAL"] = str(fixture.global_config)
            env["GIT_ALLOW_PROTOCOL"] = "file"
        return env

    monkeypatch.setattr(tool, "_git_environment", local_environment)


def _prepare_cache(tool, fixture: GitFixture, monkeypatch: pytest.MonkeyPatch):
    _enable_local_fetch(tool, fixture, monkeypatch)
    sources, dependencies, _ = tool._load_policy(fixture.repo)
    sources += dependencies
    records = tool._fetch(fixture.cache, sources)
    assert [item["name"] for item in records] == list(ALL_NAMES)
    return sources


def _main(
    tool,
    fixture: GitFixture,
    capsys: pytest.CaptureFixture[str],
    operation: str,
    *,
    cache: Path | None = None,
) -> tuple[int, str, str]:
    rc = tool.main(
        [
            operation,
            "--repo-root",
            str(fixture.repo),
            "--cache-root",
            str(cache or fixture.cache),
        ]
    )
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


def _expected_source_records(
    fixture: GitFixture, root: Path,
) -> list[dict[str, str]]:
    return [
        {
            "name": name,
            "pin": fixture.pins[name],
            "resolved_path": str((root / name).resolve(strict=True)),
            "head": fixture.pins[name],
        }
        for name in ALL_NAMES
    ]


def test_m01_policy_cmake_drift_is_rejected_before_acquisition(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    _enable_local_fetch(tool, git_fixture, monkeypatch)
    cmake = git_fixture.repo / "external" / "ccbench" / "cmake" / "ThirdParty.cmake"
    cmake.write_text(
        cmake.read_text(encoding="utf-8").replace(git_fixture.pins["masstree"], "0" * 40),
        encoding="utf-8",
    )
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "fetch")
    assert not git_fixture.cache.exists()
    assert rc == 2
    assert stdout == ""
    assert "policy/ThirdParty.cmake drift" in stderr


def test_m02_hydrate_fresh_clone_excludes_ignored_cache_artifact(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    (git_fixture.cache / "masstree" / "poison.a").write_bytes(b"not-from-pin")
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "hydrate")
    assert rc == 0, stderr
    payload = json.loads(stdout)
    assert payload["operation"] == "hydrate"
    source_root = Path(payload["source_root"])
    assert source_root == git_fixture.repo / STAGING_RELATIVE
    assert not (source_root / "masstree" / "poison.a").exists()
    assert (git_fixture.cache / "masstree" / "poison.a").is_file()


def test_m14_real_hydrate_uses_explicit_staging_root(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    staging_root = git_fixture.repo.parent / "job-private" / "thirdparty-src"

    rc = tool.main(
        [
            "hydrate",
            "--repo-root",
            str(git_fixture.repo),
            "--cache-root",
            str(git_fixture.cache),
            "--staging-root",
            str(staging_root),
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0, captured.err
    payload = json.loads(captured.out)
    resolved_root = staging_root.resolve(strict=True)
    assert payload["source_root"] == str(resolved_root)
    assert payload["sources"] == _expected_source_records(git_fixture, resolved_root)
    assert not (git_fixture.repo / STAGING_RELATIVE).exists()


def test_m03_shallow_cache_is_rejected(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    (git_fixture.cache / "masstree" / ".git" / "shallow").write_text("", encoding="ascii")
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "verify")
    assert (rc, stdout) == (1, "")
    assert "shallow repository" in stderr


def test_m04_alternates_cache_is_rejected(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    alternates = git_fixture.cache / "masstree" / ".git" / "objects" / "info" / "alternates"
    alternates.write_text("", encoding="ascii")
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "verify")
    assert (rc, stdout) == (1, "")
    assert "alternates" in stderr


def test_m05_replace_refs_are_rejected(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    source = git_fixture.cache / "masstree"
    original = git_fixture.pins["masstree"]
    (source / "tracked.txt").write_text("replacement\n", encoding="utf-8")
    _git(source, "add", "tracked.txt")
    _git(
        source, "-c", "user.email=fixture@example.invalid", "-c",
        "user.name=Fixture", "commit", "-qm", "replacement",
    )
    replacement = _git(source, "rev-parse", "HEAD").stdout.strip()
    _git(source, "reset", "--hard", original)
    _git(source, "replace", original, replacement)
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "verify")
    assert (rc, stdout) == (1, "")
    assert "replace refs" in stderr


def test_m06_untracked_dirty_requires_explicit_all_mode(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    source = git_fixture.cache / "masstree"
    _git(source, "config", "status.showUntrackedFiles", "no")
    payload = source / "untracked" / "payload"
    payload.parent.mkdir(parents=True)
    payload.write_text("untracked\n", encoding="utf-8")
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "verify")
    assert (rc, stdout) == (1, "")
    assert "not clean" in stderr


def test_m07_head_mismatch_is_rejected(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    source = git_fixture.cache / "masstree"
    (source / "tracked.txt").write_text("new commit\n", encoding="utf-8")
    _git(source, "add", "tracked.txt")
    _git(
        source, "-c", "user.email=fixture@example.invalid", "-c",
        "user.name=Fixture", "commit", "-qm", "new",
    )
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "verify")
    assert (rc, stdout) == (1, "")
    assert "HEAD does not match" in stderr


def test_m08_origin_url_substitution_is_rejected(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    source = git_fixture.cache / "masstree"
    _git(source, "config", "remote.origin.url", "https://github.com/fixture/other.git")
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "verify")
    assert (rc, stdout) == (1, "")
    assert "origin URL" in stderr


def test_m09_final_component_symlink_is_rejected(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    source = git_fixture.cache / "masstree"
    actual = git_fixture.cache / "masstree-real"
    source.rename(actual)
    source.symlink_to(actual, target_is_directory=True)
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "verify")
    assert (rc, stdout) == (1, "")
    assert "real directory" in stderr


def test_m10_publish_reservation_never_replaces_existing_empty_directory(
    tmp_path: Path,
) -> None:
    tool = _load_tool()
    stage = tmp_path / "stage"
    destination = tmp_path / "destination"
    stage.mkdir()
    (stage / "payload").write_text("stage\n", encoding="utf-8")
    destination.mkdir()
    destination_inode = destination.stat().st_ino
    with pytest.raises(tool.OperationalError, match="already exists"):
        tool._publish_create_only(stage, destination)
    assert destination.stat().st_ino == destination_inode
    assert list(destination.iterdir()) == []
    assert (stage / "payload").is_file()


def test_publish_rename_failure_removes_own_empty_reservation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_tool()
    stage = tmp_path / "stage"
    destination = tmp_path / "destination"
    stage.mkdir()
    (stage / "payload").write_text("stage\n", encoding="utf-8")

    def fail_rename(source, target):
        raise OSError("injected rename failure")

    monkeypatch.setattr(tool.os, "rename", fail_rename)
    with pytest.raises(tool.OperationalError, match="publish rename failed"):
        tool._publish_create_only(stage, destination)
    assert not destination.exists()
    assert (stage / "payload").is_file()


def test_publish_rename_failure_never_removes_a_replaced_inode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_tool()
    stage = tmp_path / "stage"
    destination = tmp_path / "destination"
    replacement = tmp_path / "replacement"
    stage.mkdir()
    replacement.mkdir()
    replacement_inode = replacement.stat().st_ino
    real_rename = os.rename

    def replace_then_fail(source, target):
        os.rmdir(target)
        real_rename(replacement, target)
        raise OSError("injected inode replacement")

    monkeypatch.setattr(tool.os, "rename", replace_then_fail)
    with pytest.raises(tool.OperationalError, match="publish rename failed"):
        tool._publish_create_only(stage, destination)
    assert destination.stat().st_ino == replacement_inode
    assert list(destination.iterdir()) == []


def test_m11_existing_cache_never_runs_clone_fetch_pull_or_checkout(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_tool()
    sources = _prepare_cache(tool, git_fixture, monkeypatch)
    original = tool._git
    commands: list[tuple[str, ...]] = []

    def recording_git(args, *, protocol, check=True):
        commands.append(tuple(args))
        return original(args, protocol=protocol, check=check)

    monkeypatch.setattr(tool, "_git", recording_git)
    tool._fetch(git_fixture.cache, sources)
    flattened = [token for command in commands for token in command]
    assert not {"clone", "fetch", "pull", "checkout"}.intersection(flattened)


def test_git_environment_has_hardened_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_tool()
    upstream = tmp_path / "upstream.git"
    _make_repo(upstream)
    home = tmp_path / "home"
    home.mkdir()
    (home / ".gitconfig").write_text(
        '[url "' + upstream.as_uri() + '"]\n'
        "\tinsteadOf = https://github.com/hostile/repo.git\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/tmp/hostile-global")
    monkeypatch.setenv("GIT_ALLOW_PROTOCOL", "file:ssh")
    monkeypatch.setenv("GIT_ASKPASS", "/tmp/askpass")
    monkeypatch.setenv("SSH_ASKPASS", "/tmp/ssh-askpass")
    env = tool._git_environment("https")
    assert env["GIT_CONFIG_GLOBAL"] == os.devnull
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["GIT_ALLOW_PROTOCOL"] == "https"
    assert env["GIT_NO_LAZY_FETCH"] == "1"
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert "GIT_ASKPASS" not in env
    assert "SSH_ASKPASS" not in env


def test_m12_host_global_insteadof_is_behaviorally_ignored(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_tool()
    upstream = tmp_path / "upstream.git"
    _make_repo(upstream)
    home = tmp_path / "home"
    home.mkdir()
    (home / ".gitconfig").write_text(
        '[url "' + upstream.as_uri() + '"]\n'
        "\tinsteadOf = https://github.com/hostile/repo.git\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(home))
    result = tool._git(
        ["ls-remote", "https://github.com/hostile/repo.git"],
        protocol="file",
        check=False,
    )
    assert result.returncode != 0
    assert result.stdout == ""


def test_m13_cache_root_inside_repo_is_rejected(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    _enable_local_fetch(tool, git_fixture, monkeypatch)
    inside = git_fixture.repo / "cache"
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "fetch", cache=inside)
    assert not inside.exists()
    assert (rc, stdout) == (2, "")
    assert "outside the repository" in stderr


@pytest.mark.parametrize(
    "dangerous",
    [
        "[core]\nfsmonitor = /tmp/cmd\n",
        "[core]\nsshCommand = /tmp/cmd\n",
        "[core]\nhooksPath = /tmp/hooks\n",
        '[filter "x"]\nclean = /tmp/cmd\n',
        "[include]\npath = /tmp/config\n",
        '[includeIf "gitdir:/tmp/"]\npath = /tmp/config\n',
        '[url "file:///tmp/"]\ninsteadOf = https://github.com/\n',
        '[remote "origin"]\nuploadpack = /tmp/cmd\n',
        '[remote "origin"]\nreceivepack = /tmp/cmd\n',
        "[FiLtEr.EvIl]\nclean = /tmp/cmd\n",
        "[ remote.origin ]\nuploadpack = /tmp/cmd\n",
        "[url.file]\ninsteadOf = https://github.com/\n",
        "[core]\nbenign = value\\\n[filter \"x\"]\nclean = /tmp/cmd\n",
        "[core]\nbenign = value\\\\\n[filter \"x\"]\nclean = /tmp/cmd\n",
        "[core] # comment \\\n[filter \"x\"]\nclean = /tmp/cmd\n",
    ],
)
def test_m14_dangerous_cache_config_is_rejected_before_git(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    dangerous: str,
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    config = git_fixture.cache / "masstree" / ".git" / "config"
    with config.open("a", encoding="utf-8") as stream:
        stream.write(dangerous)
    calls: list[tuple[str, ...]] = []

    def recording_git(args, *, protocol, check=True):
        calls.append(tuple(args))
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(tool, "_git", recording_git)
    rc, stdout, _ = _main(tool, git_fixture, capsys, "verify")
    assert calls == []
    assert (rc, stdout) == (1, "")


def test_m15_publish_is_reverified_before_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_tool()
    repo = tmp_path / "repo"
    cache = tmp_path / "cache"
    cache_source = cache / "masstree"
    cache_source.mkdir(parents=True)
    staging_relative = Path("staging")
    destination = repo / staging_relative / "masstree"
    source = {
        "name": "masstree",
        "source_name": "masstree",
        "url": "https://github.com/fixture/masstree.git",
        "pin": "a" * 40,
    }

    def fake_checkout(clone_args, stage, pin, *, protocol):
        stage.mkdir()
        (stage / "payload").write_text("complete\n", encoding="utf-8")

    def fake_verify(path, **kwargs):
        if Path(path) == destination:
            raise tool.SourceVerificationError("post-publish mutation")
        return {
            "name": kwargs["name"],
            "pin": kwargs["pin"],
            "resolved_path": str(path),
            "head": kwargs["pin"],
        }

    monkeypatch.setattr(tool, "_checkout_stage", fake_checkout)
    monkeypatch.setattr(tool, "_verify_source", fake_verify)
    with pytest.raises(tool.SourceVerificationError) as exc_info:
        tool._hydrate(repo, cache, [source], staging_relative)
    assert not destination.exists()
    assert str(exc_info.value) == "post-publish mutation"


@pytest.mark.parametrize(
    "mutation,expected",
    [
        ("promisor", "partial/promisor"),
        ("partialclone", "partial/promisor"),
        ("grafts", "grafts"),
        ("gitfile", ".git must be"),
        ("sparse-config", "sparse checkout"),
        ("sparse-file", "sparse checkout"),
        ("assume-unchanged", "index bit"),
        ("skip-worktree", "index bit"),
    ],
)
def test_hardened_metadata_matrix_is_fail_closed(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mutation: str,
    expected: str,
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    source = git_fixture.cache / "masstree"
    git_dir = source / ".git"
    if mutation == "promisor":
        _git(source, "config", "remote.origin.promisor", "true")
    elif mutation == "partialclone":
        _git(source, "config", "extensions.partialclone", "origin")
    elif mutation == "grafts":
        (git_dir / "info" / "grafts").write_text("", encoding="ascii")
    elif mutation == "gitfile":
        moved = source / ".git-real"
        git_dir.rename(moved)
        git_dir.write_text("gitdir: .git-real\n", encoding="ascii")
    elif mutation == "sparse-config":
        _git(source, "config", "core.sparseCheckout", "true")
    elif mutation == "sparse-file":
        (git_dir / "info" / "sparse-checkout").write_text("*\n", encoding="ascii")
    elif mutation == "assume-unchanged":
        _git(source, "update-index", "--assume-unchanged", "tracked.txt")
    else:
        _git(source, "update-index", "--skip-worktree", "tracked.txt")
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "verify")
    assert (rc, stdout) == (1, "")
    assert expected in stderr


@pytest.mark.parametrize(
    "mutation,expected",
    [
        ("commondir", "commondir"),
        ("config-worktree", "worktree Git config"),
        ("worktree-config-extension", "worktree Git config"),
    ],
)
def test_git_metadata_indirection_is_rejected_before_git(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mutation: str,
    expected: str,
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    git_dir = git_fixture.cache / "masstree" / ".git"
    if mutation == "commondir":
        (git_dir / "commondir").write_text(".\n", encoding="ascii")
    elif mutation == "config-worktree":
        (git_dir / "config.worktree").write_text("[core]\n", encoding="ascii")
    else:
        with (git_dir / "config").open("a", encoding="utf-8") as stream:
            stream.write("[extensions]\nworktreeConfig = true\n")
    calls: list[tuple[str, ...]] = []

    def recording_git(args, *, protocol, check=True):
        calls.append(tuple(args))
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(tool, "_git", recording_git)
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "verify")
    assert calls == []
    assert (rc, stdout) == (1, "")
    assert expected in stderr


def test_existing_hydrate_rejects_ignored_artifacts(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    rc, _, stderr = _main(tool, git_fixture, capsys, "hydrate")
    assert rc == 0, stderr
    ignored = git_fixture.repo / STAGING_RELATIVE / "masstree" / "poison.a"
    ignored.write_bytes(b"ignored build artifact")
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "hydrate")
    assert (rc, stdout) == (1, "")
    assert "ignored artifacts" in stderr


def test_benign_git_config_section_comments_are_accepted(tmp_path: Path) -> None:
    tool = _load_tool()
    config = tmp_path / "config"
    config.write_text(
        "[core] # benign comment\n"
        "benign = value\\\\\n"
        "bare = false ; another benign comment\n"
        '[remote "origin"] ; benign comment\n'
        "url = https://github.com/fixture/repo.git\n",
        encoding="utf-8",
    )
    tool._inspect_cache_config(config)


def test_fetch_verify_and_hydrate_emit_one_versioned_json_document(
    git_fixture: GitFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    _enable_local_fetch(tool, git_fixture, monkeypatch)
    for operation in ("fetch", "verify", "hydrate"):
        rc, stdout, stderr = _main(tool, git_fixture, capsys, operation)
        assert rc == 0, stderr
        assert stdout.count("\n") == 1
        payload = json.loads(stdout)
        expected = {
            "schema_version": "pegasus-thirdparty-fetch/v1",
            "operation": operation,
            "cache_root": str(git_fixture.cache),
            "sources": _expected_source_records(
                git_fixture,
                git_fixture.repo / STAGING_RELATIVE
                if operation == "hydrate" else git_fixture.cache,
            ),
        }
        if operation == "hydrate":
            expected["source_root"] = str(git_fixture.repo / STAGING_RELATIVE)
        assert payload == expected


def test_argument_failure_is_one_stderr_line_and_rc2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    tool = _load_tool()
    rc = tool.main(["unknown"])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert captured.err.count("\n") == 1


def test_driver_import_removes_only_its_temporary_sys_path_entry() -> None:
    script = """
import importlib.util
from pathlib import Path
import sys

tool_path = Path(sys.argv[1])
repo = str(Path(sys.argv[2]))
orchestrator = str(Path(repo) / "orchestrator")
spec = importlib.util.spec_from_file_location("fetch_third_party_fresh", tool_path)
assert spec is not None and spec.loader is not None
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
expected = [
    "izanagi-test-sys-path-sentinel",
    *(entry for entry in sys.path if entry not in {repo, orchestrator}),
]
sys.path[:] = expected
tool._driver_module()
assert sys.path == expected, (expected, sys.path)
"""

    result = subprocess.run(
        [sys.executable, "-c", script, str(TOOL_PATH), str(REPO)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_hydrate_clone_is_offline_no_hardlinks_and_never_copytree() -> None:
    source = TOOL_PATH.read_text(encoding="utf-8")
    assert '["--no-hardlinks", "--no-checkout", "--", str(cache_source)]' in source
    assert "copytree" not in source
    assert 'protocol="file"' in source


def test_fetch_protocol_is_https_and_offline_operations_are_file_only() -> None:
    tool = _load_tool()
    calls: list[str] = []

    def fake_run(command, **kwargs):
        calls.append(kwargs["env"]["GIT_ALLOW_PROTOCOL"])
        return subprocess.CompletedProcess(command, 0, "", "")

    original_run = subprocess.run
    try:
        subprocess.run = fake_run
        tool._git(["version"], protocol="https")
        tool._git(["version"], protocol="file")
    finally:
        subprocess.run = original_run
    assert calls == ["https", "file"]


@pytest.mark.parametrize("name", ["gflags", "glog"])
@pytest.mark.parametrize("operation", ["fetch", "hydrate", "verify"])
@pytest.mark.parametrize(
    "mutation,expected",
    [("head", "HEAD"), ("dirty", "not clean"), ("shallow", "shallow"),
     ("origin", "origin URL")],
)
def test_build_dependencies_reject_mutated_cache(
    git_fixture, monkeypatch, capsys, name, operation, mutation, expected,
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    source = git_fixture.cache / name
    if mutation == "head":
        _git(source, "-c", "user.name=Fixture", "-c",
             "user.email=fixture@example.invalid", "commit", "--allow-empty", "-qm", "changed")
    elif mutation == "dirty":
        (source / "tracked.txt").write_text("changed\n", encoding="utf-8")
    elif mutation == "shallow":
        (source / ".git" / "shallow").write_text(
            git_fixture.pins[name] + "\n", encoding="ascii")
    else:
        _git(source, "remote", "set-url", "origin", "https://github.com/other/source.git")
    rc, stdout, stderr = _main(tool, git_fixture, capsys, operation)
    assert (rc, stdout) == (1, "")
    assert expected in stderr


@pytest.mark.parametrize("name", ["gflags", "glog"])
@pytest.mark.parametrize(
    "key,value",
    [("source_url", "https://github.com/fixture/source"),
     ("source_url", "http://github.com/fixture/source.git"),
     ("source_url", "https://example.invalid/source.git"),
     ("source_url", ""), ("source_url", None),
     ("expected_head", "a" * 39), ("expected_head", "a" * 41),
     ("expected_head", "x" + "a" * 40), ("expected_head", "a" * 40 + "\n"),
     ("expected_head", "A" * 40), ("expected_head", ""),
     ("expected_head", None)],
)
def test_build_dependency_policy_rejects_invalid_url_and_pin(
    git_fixture, monkeypatch, capsys, name, key, value,
) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    # 実 Git source は正常。policy 変異だけで拒否する層を特定する。
    tool._verify_source(git_fixture.cache / name, name=name,
                        pin=git_fixture.pins[name], expected_url=git_fixture.urls[name])
    path = git_fixture.repo / "tools/pegasus/policy.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document[f"{name}_{key}"] = value
    path.write_text(json.dumps(document), encoding="utf-8")
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "verify")
    assert (rc, stdout) == (2, "")
    assert "build dependency source policy is invalid" in stderr


def test_build_dependency_records_have_exact_shape(git_fixture) -> None:
    tool = _load_tool()
    sources, dependencies, staging = tool._load_policy(git_fixture.repo)
    sources += dependencies
    assert [item["name"] for item in sources] == list(ALL_NAMES)
    assert staging == STAGING_RELATIVE
    assert sources[-2:] == tuple(
        {"name": name, "source_name": name,
         "url": git_fixture.urls[name], "pin": git_fixture.pins[name]}
        for name in ("gflags", "glog")
    )


def test_removed_verify_deps_command_is_rejected(capsys) -> None:
    assert _load_tool().main(["verify-deps"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid choice" in captured.err


def test_default_verify_requires_all_five_sources(git_fixture, monkeypatch, capsys) -> None:
    tool = _load_tool()
    _prepare_cache(tool, git_fixture, monkeypatch)
    (git_fixture.cache / "gflags").rename(git_fixture.cache / "missing-gflags")
    rc, stdout, stderr = _main(tool, git_fixture, capsys, "verify")
    assert (rc, stdout) == (1, "")
    assert "gflags" in stderr


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    sys.exit(_run())
