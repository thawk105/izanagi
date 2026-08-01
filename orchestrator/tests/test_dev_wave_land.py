# -*- coding: utf-8 -*-
"""tools/dev_wave_land.py の linked-worktree / race / land 境界テスト。

pytest と ``python3 orchestrator/tests/test_dev_wave_land.py`` の両方で走る。
全 Git mutation は tempfile 配下の合成 repository に限定する。
"""
from __future__ import annotations

import contextlib
import fcntl
import importlib.util
import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = ROOT / "tools" / "dev_wave_land.py"
SPEC = importlib.util.spec_from_file_location("dev_wave_land_under_test", HELPER_PATH)
assert SPEC and SPEC.loader
LAND = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LAND
SPEC.loader.exec_module(LAND)
REAL_GIT = "/usr/bin/git"


def _git(repo: Path, *args: str, check: bool = True) -> str:
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    })
    result = subprocess.run(
        [REAL_GIT, "-C", str(repo), *args],
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if check:
        assert result.returncode == 0, (repo, args, result.stderr)
    return result.stdout.strip()


@contextlib.contextmanager
def _cwd(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class _Repo:
    def __init__(self, *, waves: tuple[tuple[str, str], ...] = (("codex", "one"),)):
        self._tmp = tempfile.TemporaryDirectory(prefix="izanagi-land-test-")
        self.root = Path(self._tmp.name)
        self.main = self.root / "repo"
        subprocess.run(
            [REAL_GIT, "init", "-q", "-b", "main", str(self.main)],
            check=True,
            env={
                **{
                    key: value for key, value in os.environ.items()
                    if not key.startswith("GIT_")
                },
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_SYSTEM": os.devnull,
            },
        )
        _git(self.main, "config", "user.name", "Dev Wave Test")
        _git(self.main, "config", "user.email", "dev-wave@example.invalid")
        (self.main / "base.txt").write_text("base\n", encoding="utf-8")
        handoff = self.main / "docs" / "handoff"
        handoff.mkdir(parents=True)
        (handoff / "README.md").write_text("# handoff\n", encoding="utf-8")
        _git(self.main, "add", "base.txt", "docs/handoff/README.md")
        _git(self.main, "commit", "-qm", "base")
        self.base = _git(self.main, "rev-parse", "HEAD")
        self.waves: dict[str, Path] = {}
        for family, name in waves:
            self.add_wave(family, name)

    def close(self) -> None:
        self._tmp.cleanup()

    def add_wave(self, family: str, name: str) -> Path:
        assert family in {"codex", "claude"}
        container = self.main / f".{family}" / "worktrees"
        container.mkdir(parents=True, exist_ok=True)
        path = container / name
        branch = f"wave/{family}-{name}"
        _git(self.main, "worktree", "add", "-q", "-b", branch, str(path), self.base)
        self.waves[name] = path
        return path

    def commit(self, wave: Path, filename: str, content: str) -> str:
        (wave / filename).write_text(content, encoding="utf-8")
        _git(wave, "add", filename)
        _git(wave, "commit", "-qm", f"add {filename}")
        return _git(wave, "rev-parse", "HEAD")

    def audited(self, base: str, tip: str, wave: Path) -> tuple[str, ...]:
        output = _git(wave, "rev-list", "--reverse", f"{base}..{tip}")
        return tuple(output.splitlines()) if output else ()

    def request(
        self,
        wave: Path,
        *,
        base: str | None = None,
        tip: str | None = None,
        audited: tuple[str, ...] | None = None,
    ):
        tested_base = base or self.base
        tested_tip = tip or _git(wave, "rev-parse", "HEAD")
        commits = (
            audited
            if audited is not None
            else self.audited(tested_base, tested_tip, wave)
        )
        return LAND.LandRequest(
            main_worktree=self.main,
            wave_worktree=wave,
            tested_main_sha=tested_base,
            tested_wave_tip_sha=tested_tip,
            audited_commits=commits,
        )


@contextlib.contextmanager
def _repo(*, waves: tuple[tuple[str, str], ...] = (("codex", "one"),)):
    fixture = _Repo(waves=waves)
    try:
        yield fixture
    finally:
        fixture.close()


def _land(request):
    with _cwd(request.wave_worktree):
        return LAND.land(request)


def _handoff(repo: _Repo, *, state: str = "作業中", name: str = "foreign.md") -> Path:
    path = repo.main / "docs" / "handoff" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# foreign wave\n"
        "- 目的: parallel control plane\n"
        f"- 状態: {state}\n"
        "- 最終更新: 2000-01-01\n"
        f"- 基準コミット: {repo.base}\n"
        "\n"
        "## 完了した中間成果\n\nnone\n"
        "## 未完の作業と次の一手\n\ncontinue\n"
        "## 落とし穴・気づき\n\nnone\n",
        encoding="utf-8",
    )
    return path


def _snapshot(path: Path) -> tuple[bytes, tuple[int, int, int]]:
    metadata = path.lstat()
    return (
        path.read_bytes(),
        (metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode)),
    )


_SYNTHETIC_ACCEPTANCE = r"""
import json
import os
import subprocess
import sys

git, tested_main, tested_tip, tested_tree = sys.argv[1:]

def run(*args):
    completed = subprocess.run(
        [git, "-C", os.getcwd(), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.stderr or f"git rc={completed.returncode}")
    return completed.stdout.strip()

observed_tip = run("rev-parse", "--verify", "HEAD")
observed_tree = run("rev-parse", "--verify", "HEAD^{tree}")
if observed_tip != tested_tip or observed_tree != tested_tree:
    raise SystemExit("acceptance HEAD/tree mismatch")
if subprocess.run(
    [git, "-C", os.getcwd(), "merge-base", "--is-ancestor",
     tested_main, tested_tip],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    check=False,
).returncode != 0:
    raise SystemExit("tested main is not an ancestor of tested tip")
if run("status", "--porcelain=v1", "--ignore-submodules=none"):
    raise SystemExit("acceptance worktree is dirty")
for relative, expected in (
    ("winner.txt", "winner\n"),
    ("loser.txt", "loser\n"),
):
    with open(relative, encoding="utf-8") as stream:
        if stream.read() != expected:
            raise SystemExit(f"{relative} content mismatch")
print(json.dumps({
    "tested_main": tested_main,
    "tested_tip": observed_tip,
    "tested_tree": observed_tree,
}, sort_keys=True))
"""


def _run_synthetic_acceptance(
    wave: Path, *, tested_main: str, tested_tip: str, tested_tree: str
) -> dict[str, str]:
    """再同期 tip の内容・tree・cleanliness を実行して receipt を返す。"""
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _SYNTHETIC_ACCEPTANCE,
            REAL_GIT,
            tested_main,
            tested_tip,
            tested_tree,
        ],
        cwd=wave,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    receipt = json.loads(completed.stdout)
    assert set(receipt) == {"tested_main", "tested_tip", "tested_tree"}
    return receipt


def test_basic_land_accepts_registered_claude_and_codex_children() -> None:
    """M10/M11: valid foreign handoff と両 container は正例である。"""
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        handoff = _handoff(repo, state="計測中")
        watched = {
            handoff: _snapshot(handoff),
            repo.waves["foreign"] / ".git": _snapshot(repo.waves["foreign"] / ".git"),
        }
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (0, "landed"), result
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        assert (repo.main / "author.txt").read_text() == "author\n"
        assert {path: _snapshot(path) for path in watched} == watched


def test_handoff_all_states_and_stale_are_accepted() -> None:
    """freshness は診断に限り、三状態と stale date をすべて許可する。"""
    for state in ("作業中", "計測中", "中断"):
        with _repo() as repo:
            wave = repo.waves["one"]
            _handoff(repo, state=state)
            result = _land(repo.request(wave, tip=repo.base, audited=()))
            assert (result.rc, result.status) == (0, "already-landed"), (state, result)


def test_colliding_untracked_rejected_without_main_or_foreign_artifact_change() -> None:
    """M4: land target と衝突する untracked は拒否し main を変更しない。"""
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        handoff = _handoff(repo)
        collision = repo.main / "author.txt"
        collision.write_text("foreign untracked\n", encoding="utf-8")
        watched = {
            handoff: _snapshot(handoff),
            repo.waves["foreign"] / ".git": _snapshot(repo.waves["foreign"] / ".git"),
            collision: _snapshot(collision),
        }
        before = _git(repo.main, "rev-parse", "HEAD")
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_DIRT and result.status == "rejected", result
        assert _git(repo.main, "rev-parse", "HEAD") == before
        assert {path: _snapshot(path) for path in watched} == watched


def test_noncolliding_foreign_session_untracked_does_not_block_land() -> None:
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        foreign = repo.main / "foreign-session.txt"
        foreign.write_text("foreign untracked\n", encoding="utf-8")
        watched = _snapshot(foreign)
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        assert _snapshot(foreign) == watched


def test_safe_child_name_rule_rejects_only_dangerous_names() -> None:
    for name in (b".", b"..", b"a/b", b"nul\x00child"):
        assert LAND._SAFE_CHILD_RE.fullmatch(name) is None, name
    for name in (b".izanagi-test-dispatch", b"ordinary-name"):
        assert LAND._SAFE_CHILD_RE.fullmatch(name) is not None, name


def test_tracked_and_staged_main_dirt_are_rejected() -> None:
    """M3: worktree と index のどちらの tracked dirt も拒否する。"""
    for staged in (False, True):
        with _repo() as repo:
            wave = repo.waves["one"]
            tip = repo.commit(wave, "wave.txt", "wave\n")
            (repo.main / "base.txt").write_text("dirty\n", encoding="utf-8")
            if staged:
                _git(repo.main, "add", "base.txt")
            result = _land(repo.request(wave, tip=tip))
            assert result.rc == LAND.RC_DIRT, (staged, result)
            assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_malformed_symlink_and_nonregular_handoff_are_rejected() -> None:
    """M5: path の型と schema の両方を positive-control 付きで固定する。"""
    for kind in ("malformed", "symlink", "fifo"):
        with _repo() as repo:
            wave = repo.waves["one"]
            tip = repo.commit(wave, "wave.txt", "wave\n")
            path = repo.main / "docs" / "handoff" / "foreign.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            if kind == "malformed":
                path.write_text("# missing schema\n", encoding="utf-8")
            elif kind == "symlink":
                path.symlink_to(repo.main / "base.txt")
            else:
                os.mkfifo(path)
            before = _git(repo.main, "rev-parse", "HEAD")
            result = _land(repo.request(wave, tip=tip))
            assert result.rc in (LAND.RC_CONTROL_PLANE, LAND.RC_DIRT), (kind, result)
            assert _git(repo.main, "rev-parse", "HEAD") == before


def test_unregistered_alias_child_is_rejected() -> None:
    """M6: 正規 child の .git bytes を複製しても admin backpointer 不一致で拒否する。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        alias = repo.main / ".codex" / "worktrees" / "alias"
        alias.mkdir()
        (alias / ".git").write_bytes((wave / ".git").read_bytes())
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_CONTROL_PLANE, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_ignored_registered_container_and_unrelated_cache_are_accepted() -> None:
    """collapsed ignored dir 内でも既存物の sibling target は受理する。"""
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        exclude = repo.main / ".git" / "info" / "exclude"
        exclude.write_text(
            ".codex/worktrees/\n.claude/worktrees/\ncache/\n",
            encoding="utf-8",
        )
        cache = repo.main / "cache" / "pre-existing.bin"
        cache.parent.mkdir()
        cache.write_bytes(b"ignored cache\n")
        (wave / "cache").mkdir()
        (wave / "cache" / "new.txt").write_text(
            "tracked sibling\n", encoding="utf-8"
        )
        _git(wave, "add", "-f", "cache/new.txt")
        _git(wave, "commit", "-qm", "add tracked cache sibling")
        tip = _git(wave, "rev-parse", "HEAD")
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (0, "landed"), result
        assert cache.read_bytes() == b"ignored cache\n"
        assert (repo.main / "cache" / "new.txt").read_text() == "tracked sibling\n"


def test_ignored_unregistered_container_child_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        alias = repo.main / ".codex" / "worktrees" / "alias"
        alias.mkdir()
        (alias / ".git").write_bytes((wave / ".git").read_bytes())
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_CONTROL_PLANE, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_target_collision_with_existing_ignored_path_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            "cache/\n",
            encoding="utf-8",
        )
        collision = repo.main / "cache" / "collision.txt"
        collision.parent.mkdir()
        collision.write_text("foreign cache\n", encoding="utf-8")
        target = wave / "cache" / "collision.txt"
        target.parent.mkdir()
        target.write_text("wave target\n", encoding="utf-8")
        _git(wave, "add", "-f", "cache/collision.txt")
        _git(wave, "commit", "-qm", "add ignored collision")
        tip = _git(wave, "rev-parse", "HEAD")
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_DIRT, result
        assert collision.read_text(encoding="utf-8") == "foreign cache\n"
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_target_collision_with_existing_ignored_ancestor_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            "cache\n",
            encoding="utf-8",
        )
        collision = repo.main / "cache"
        collision.write_text("foreign cache file\n", encoding="utf-8")
        target = wave / "cache" / "new.txt"
        target.parent.mkdir()
        target.write_text("wave target\n", encoding="utf-8")
        _git(wave, "add", "-f", "cache/new.txt")
        _git(wave, "commit", "-qm", "add target below ignored ancestor")
        tip = _git(wave, "rev-parse", "HEAD")
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_DIRT, result
        assert collision.read_text(encoding="utf-8") == "foreign cache file\n"
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_target_collision_with_foreign_control_artifact_is_rejected() -> None:
    for kind in ("handoff", "worktree"):
        with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
            wave = repo.waves["author"]
            if kind == "handoff":
                foreign = _handoff(repo)
                relative = "docs/handoff/foreign.md"
                target = wave / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("tracked replacement\n", encoding="utf-8")
            else:
                foreign = repo.waves["foreign"] / ".git"
                relative = ".claude/worktrees/foreign/payload.txt"
                target = wave / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("tracked collision\n", encoding="utf-8")
            watched = _snapshot(foreign)
            _git(wave, "add", relative)
            _git(wave, "commit", "-qm", f"add {kind} collision")
            tip = _git(wave, "rev-parse", "HEAD")
            result = _land(repo.request(wave, tip=tip))
            assert result.rc == LAND.RC_CONTROL_PLANE, (kind, result)
            assert _snapshot(foreign) == watched
            assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_unsafe_container_child_bytes_are_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        container = os.fsencode(repo.main / ".codex" / "worktrees")
        os.mkdir(container + b"/bad\nrecord")
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_CONTROL_PLANE, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_shallow_graft_replace_filter_and_promisor_are_rejected() -> None:
    """M7 と filter 外部実行面を main mutation 前に拒否する。"""
    cases = (
        "shallow", "graft", "replace", "filter", "promisor",
        "included_filter", "worktree_filter",
    )
    for case in cases:
        with _repo() as repo:
            wave = repo.waves["one"]
            tip = repo.commit(wave, "wave.txt", "wave\n")
            common = repo.main / ".git"
            if case == "shallow":
                (common / "shallow").write_text(repo.base + "\n", encoding="ascii")
            elif case == "graft":
                (common / "info" / "grafts").write_text(
                    f"{tip} {repo.base}\n", encoding="ascii"
                )
            elif case == "replace":
                _git(repo.main, "replace", tip, repo.base)
            elif case == "filter":
                _git(repo.main, "config", "filter.evil.smudge", "touch escaped")
            elif case == "promisor":
                _git(repo.main, "config", "remote.origin.promisor", "true")
            elif case == "included_filter":
                (common / "land-include").write_text(
                    "[filter \"evil\"]\n\tsmudge = touch escaped\n",
                    encoding="utf-8",
                )
                _git(repo.main, "config", "--local", "include.path", "land-include")
            else:
                _git(repo.main, "config", "extensions.worktreeConfig", "true")
                _git(
                    repo.main, "config", "--worktree",
                    "filter.evil.process", "touch escaped",
                )
            result = _land(repo.request(wave, tip=tip))
            assert result.rc == LAND.RC_AUDIT, (case, result)
            assert _git(repo.main, "rev-parse", "HEAD") == repo.base
            assert not (repo.main / "escaped").exists()


def test_hooks_and_fsmonitor_are_disabled_for_land() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        hook_marker = repo.root / "hook-ran"
        fsmonitor_marker = repo.root / "fsmonitor-ran"
        hook = repo.main / ".git" / "hooks" / "post-merge"
        hook.write_text(
            f"#!/bin/sh\nprintf ran > {hook_marker}\n",
            encoding="utf-8",
        )
        hook.chmod(0o755)
        fsmonitor = repo.root / "fsmonitor"
        fsmonitor.write_text(
            f"#!/bin/sh\nprintf ran > {fsmonitor_marker}\nexit 1\n",
            encoding="utf-8",
        )
        fsmonitor.chmod(0o755)
        _git(repo.main, "config", "core.fsmonitor", str(fsmonitor))
        _git(repo.main, "config", "merge.autoStash", "true")
        _git(repo.main, "config", "maintenance.auto", "true")
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (0, "landed"), result
        assert not hook_marker.exists()
        assert not fsmonitor_marker.exists()


def test_gitlink_change_lands_but_cannot_report_success_before_d16_sync() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        submodule = repo.root / "submodule-source"
        subprocess.run(
            [REAL_GIT, "init", "-q", "-b", "main", str(submodule)],
            check=True,
        )
        _git(submodule, "config", "user.name", "Dev Wave Test")
        _git(submodule, "config", "user.email", "dev-wave@example.invalid")
        (submodule / "sub.txt").write_text("sub\n", encoding="utf-8")
        _git(submodule, "add", "sub.txt")
        _git(submodule, "commit", "-qm", "submodule base")
        old_submodule_tip = _git(submodule, "rev-parse", "HEAD")
        (submodule / "sub.txt").write_text("sub updated\n", encoding="utf-8")
        _git(submodule, "commit", "-qam", "submodule target")
        expected_submodule_tip = _git(submodule, "rev-parse", "HEAD")
        _git(
            wave, "-c", "protocol.file.allow=always",
            "submodule", "add", "-q", str(submodule), "vendor/submodule",
        )
        _git(wave, "commit", "-qm", "change gitlink")
        tip = _git(wave, "rev-parse", "HEAD")
        result = _land(repo.request(wave, tip=tip))
        assert (
            result.rc,
            result.status,
        ) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), result
        assert "D16" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        request = repo.request(wave, tip=tip)

        uninitialized = _land(request)
        assert (
            uninitialized.rc,
            uninitialized.status,
        ) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), uninitialized

        _git(
            repo.main, "-c", "protocol.file.allow=always",
            "submodule", "update", "--init", "--recursive",
        )
        main_submodule = repo.main / "vendor" / "submodule"
        assert _git(main_submodule, "rev-parse", "HEAD") == expected_submodule_tip
        _git(main_submodule, "checkout", "-q", old_submodule_tip)
        mismatched = _land(request)
        assert mismatched.rc != LAND.RC_OK, mismatched

        _git(main_submodule, "checkout", "-q", expected_submodule_tip)
        synchronized = _land(request)
        assert (
            synchronized.rc,
            synchronized.status,
        ) == (LAND.RC_OK, "already-landed"), synchronized


def test_deleted_gitlink_recovery_requires_worktree_and_nested_metadata_absent() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        submodule = repo.root / "submodule-source"
        subprocess.run(
            [REAL_GIT, "init", "-q", "-b", "main", str(submodule)],
            check=True,
        )
        _git(submodule, "config", "user.name", "Dev Wave Test")
        _git(submodule, "config", "user.email", "dev-wave@example.invalid")
        (submodule / "sub.txt").write_text("sub\n", encoding="utf-8")
        _git(submodule, "add", "sub.txt")
        _git(submodule, "commit", "-qm", "submodule base")
        _git(
            wave, "-c", "protocol.file.allow=always",
            "submodule", "add", "-q", str(submodule), "vendor/submodule",
        )
        _git(wave, "commit", "-qm", "add gitlink")
        tested_main = _git(wave, "rev-parse", "HEAD")
        _git(repo.main, "merge", "--ff-only", tested_main)
        _git(
            repo.main, "-c", "protocol.file.allow=always",
            "submodule", "update", "--init", "--recursive",
        )
        _git(wave, "rm", "-qf", "vendor/submodule")
        _git(wave, "commit", "-qm", "remove gitlink")
        tested_tip = _git(wave, "rev-parse", "HEAD")
        audited = repo.audited(tested_main, tested_tip, wave)
        request = repo.request(
            wave,
            base=tested_main,
            tip=tested_tip,
            audited=audited,
        )

        landed = _land(request)
        assert (landed.rc, landed.status) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), landed
        assert _git(repo.main, "rev-parse", "HEAD") == tested_tip

        residual_worktree = repo.main / "vendor" / "submodule"
        residual_metadata = repo.main / ".git" / "modules" / "vendor" / "submodule"
        assert residual_worktree.exists()
        assert residual_metadata.exists()
        residual = _land(request)
        assert residual.rc != LAND.RC_OK, residual

        shutil.rmtree(residual_worktree)
        metadata_only = _land(request)
        assert metadata_only.rc != LAND.RC_OK, metadata_only

        shutil.rmtree(residual_metadata)
        synchronized = _land(request)
        assert (synchronized.rc, synchronized.status) == (
            LAND.RC_OK,
            "already-landed",
        ), synchronized
        assert request.tested_main_sha == tested_main
        assert request.tested_wave_tip_sha == tested_tip
        assert request.audited_commits == audited


def test_gitlink_to_normal_tree_recovery_preserves_target_entry() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        submodule = repo.root / "submodule-source"
        subprocess.run(
            [REAL_GIT, "init", "-q", "-b", "main", str(submodule)],
            check=True,
        )
        _git(submodule, "config", "user.name", "Dev Wave Test")
        _git(submodule, "config", "user.email", "dev-wave@example.invalid")
        (submodule / "sub.txt").write_text("sub\n", encoding="utf-8")
        _git(submodule, "add", "sub.txt")
        _git(submodule, "commit", "-qm", "submodule base")
        _git(
            wave, "-c", "protocol.file.allow=always",
            "submodule", "add", "-q", str(submodule), "vendor/submodule",
        )
        _git(wave, "commit", "-qm", "add gitlink")
        tested_main = _git(wave, "rev-parse", "HEAD")
        _git(repo.main, "merge", "--ff-only", tested_main)
        _git(
            repo.main, "-c", "protocol.file.allow=always",
            "submodule", "update", "--init", "--recursive",
        )

        _git(wave, "rm", "-qf", "vendor/submodule")
        replacement = wave / "vendor" / "submodule" / "replacement.txt"
        replacement.parent.mkdir(parents=True)
        replacement.write_text("normal tree\n", encoding="utf-8")
        _git(wave, "add", "vendor/submodule/replacement.txt")
        _git(wave, "commit", "-qm", "replace gitlink with normal tree")
        tested_tip = _git(wave, "rev-parse", "HEAD")
        audited = repo.audited(tested_main, tested_tip, wave)
        request = repo.request(
            wave,
            base=tested_main,
            tip=tested_tip,
            audited=audited,
        )

        landed = _land(request)
        assert (landed.rc, landed.status) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), landed
        assert _git(repo.main, "rev-parse", "HEAD") == tested_tip

        main_replacement = repo.main / "vendor" / "submodule"
        residual_metadata = repo.main / ".git" / "modules" / "vendor" / "submodule"
        assert (main_replacement / "replacement.txt").read_text(
            encoding="utf-8"
        ) == "normal tree\n"
        assert (main_replacement / ".git").exists()
        assert residual_metadata.exists()
        residual_identity = _land(request)
        assert residual_identity.rc != LAND.RC_OK, residual_identity

        for child in main_replacement.iterdir():
            if child.name == "replacement.txt":
                continue
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()

        metadata_only = _land(request)
        assert metadata_only.rc != LAND.RC_OK, metadata_only

        shutil.rmtree(residual_metadata)
        synchronized = _land(request)
        assert (synchronized.rc, synchronized.status) == (
            LAND.RC_OK,
            "already-landed",
        ), synchronized
        assert (main_replacement / "replacement.txt").read_text(
            encoding="utf-8"
        ) == "normal tree\n"
        assert request.tested_main_sha == tested_main
        assert request.tested_wave_tip_sha == tested_tip
        assert request.audited_commits == audited


def test_gitlink_to_normal_blob_recovery_preserves_target_entry() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        submodule = repo.root / "submodule-source"
        subprocess.run(
            [REAL_GIT, "init", "-q", "-b", "main", str(submodule)],
            check=True,
        )
        _git(submodule, "config", "user.name", "Dev Wave Test")
        _git(submodule, "config", "user.email", "dev-wave@example.invalid")
        (submodule / "sub.txt").write_text("sub\n", encoding="utf-8")
        _git(submodule, "add", "sub.txt")
        _git(submodule, "commit", "-qm", "submodule base")
        _git(
            wave, "-c", "protocol.file.allow=always",
            "submodule", "add", "-q", str(submodule), "vendor/submodule",
        )
        _git(wave, "commit", "-qm", "add gitlink")
        tested_main = _git(wave, "rev-parse", "HEAD")
        _git(repo.main, "merge", "--ff-only", tested_main)
        _git(
            repo.main, "-c", "protocol.file.allow=always",
            "submodule", "update", "--init", "--recursive",
        )

        _git(wave, "rm", "-qf", "vendor/submodule")
        replacement = wave / "vendor" / "submodule"
        replacement.write_text("normal blob\n", encoding="utf-8")
        _git(wave, "add", "vendor/submodule")
        _git(wave, "commit", "-qm", "replace gitlink with normal blob")
        tested_tip = _git(wave, "rev-parse", "HEAD")
        audited = repo.audited(tested_main, tested_tip, wave)
        request = repo.request(
            wave,
            base=tested_main,
            tip=tested_tip,
            audited=audited,
        )

        landed = _land(request)
        assert (landed.rc, landed.status) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), landed
        assert _git(repo.main, "rev-parse", "HEAD") == tested_tip
        main_replacement = repo.main / "vendor" / "submodule"
        assert main_replacement.read_text(encoding="utf-8") == "normal blob\n"

        residual_metadata = repo.main / ".git" / "modules" / "vendor" / "submodule"
        assert residual_metadata.exists()
        metadata_only = _land(request)
        assert metadata_only.rc != LAND.RC_OK, metadata_only

        shutil.rmtree(residual_metadata)
        synchronized = _land(request)
        assert (synchronized.rc, synchronized.status) == (
            LAND.RC_OK,
            "already-landed",
        ), synchronized
        assert main_replacement.read_text(encoding="utf-8") == "normal blob\n"
        assert request.tested_main_sha == tested_main
        assert request.tested_wave_tip_sha == tested_tip
        assert request.audited_commits == audited


def test_audited_sequence_and_moved_wave_tip_are_exact() -> None:
    """M8 および audited A..T 列の省略を拒否する。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        first = repo.commit(wave, "one.txt", "one\n")
        tip = repo.commit(wave, "two.txt", "two\n")
        audited = repo.audited(repo.base, tip, wave)
        assert audited == (first, tip)
        omitted = _land(repo.request(wave, tip=tip, audited=(tip,)))
        assert omitted.rc == LAND.RC_AUDIT, omitted
        moved = repo.commit(wave, "three.txt", "three\n")
        result = _land(repo.request(wave, tip=tip, audited=audited))
        assert moved != tip
        assert result.rc == LAND.RC_AUDIT, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_audited_sequence_reverse_order_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        repo.commit(wave, "one.txt", "one\n")
        tip = repo.commit(wave, "two.txt", "two\n")
        audited = repo.audited(repo.base, tip, wave)
        result = _land(repo.request(wave, tip=tip, audited=tuple(reversed(audited))))
        assert result.rc == LAND.RC_AUDIT, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_audited_sequence_extra_commit_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "one.txt", "one\n")
        audited = repo.audited(repo.base, tip, wave)
        result = _land(
            repo.request(wave, tip=tip, audited=audited + (repo.base,))
        )
        assert result.rc == LAND.RC_AUDIT, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_audited_sequence_same_length_wrong_commit_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        repo.commit(wave, "one.txt", "one\n")
        tip = repo.commit(wave, "two.txt", "two\n")
        audited = repo.audited(repo.base, tip, wave)
        wrong = (repo.base, audited[1])
        assert len(wrong) == len(audited) and wrong != audited
        result = _land(repo.request(wave, tip=tip, audited=wrong))
        assert result.rc == LAND.RC_AUDIT, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_nonblocking_common_lock_reports_lock_busy() -> None:
    """M2: concurrent lock holder がいると待機・mergeせず lock-busy。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        lock_path = repo.main / ".git" / "dev-wave-land.lock"
        lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            started = time.monotonic()
            result = _land(repo.request(wave, tip=tip))
            elapsed = time.monotonic() - started
        finally:
            os.close(lock_fd)
        assert (result.rc, result.status) == (LAND.RC_LOCK_BUSY, "lock-busy"), result
        assert elapsed < 2.0
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


_WRAPPER = """#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time

real = os.environ["DEV_WAVE_REAL_GIT"]
args = sys.argv[1:]
mode = os.environ.get("DEV_WAVE_WRAPPER_MODE", "")

def replace_target():
    marker = os.environ["DEV_WAVE_MARKER"]
    if os.path.exists(marker):
        return
    target = os.environ["DEV_WAVE_REPLACE_TARGET"]
    backup = os.environ["DEV_WAVE_REPLACE_BACKUP"]
    kind = os.environ["DEV_WAVE_REPLACE_KIND"]
    if kind == "file":
        with open(target, "rb") as stream:
            payload = stream.read()
        os.replace(target, backup)
        with open(target, "wb") as stream:
            stream.write(payload)
    else:
        with open(os.path.join(target, ".git"), "rb") as stream:
            payload = stream.read()
        os.replace(target, backup)
        os.mkdir(target)
        with open(os.path.join(target, ".git"), "wb") as stream:
            stream.write(payload)
    open(marker, "wb").close()

if mode == "record":
    with open(os.environ["DEV_WAVE_RECORD"], "a", encoding="utf-8") as stream:
        stream.write(json.dumps(args) + "\\n")
if (
    mode == "hide-head"
    and os.path.exists(os.environ["DEV_WAVE_MARKER"])
    and "rev-parse" in args
    and "HEAD" in args
):
    raise SystemExit(92)
if mode == "replace-control" and "status" in args:
    completed = subprocess.run([real, *args], check=False)
    replace_target()
    raise SystemExit(completed.returncode)
if mode == "replace-after-collision" and "check-ignore" in args:
    completed = subprocess.run([real, *args], check=False)
    replace_target()
    raise SystemExit(completed.returncode)
if "merge" not in args:
    os.execv(real, [real, *args])
if mode == "audit-fds":
    targets = {}
    for name in os.listdir("/proc/self/fd"):
        try:
            targets[name] = os.readlink("/proc/self/fd/" + name)
        except OSError:
            pass
    with open(os.environ["DEV_WAVE_FD_RECORD"], "w", encoding="utf-8") as stream:
        json.dump(targets, stream)
if mode == "not-landed":
    raise SystemExit(91)
if mode == "partial":
    with open(os.environ["DEV_WAVE_PARTIAL_PATH"], "w", encoding="utf-8") as stream:
        stream.write("partial mutation\\n")
    raise SystemExit(91)
if mode in {"hold", "hold-dirty"}:
    dirty_path = os.environ.get("DEV_WAVE_DIRTY_PATH")
    if dirty_path:
        with open(dirty_path, "rb") as stream:
            original = stream.read()
        with open(dirty_path, "wb") as stream:
            stream.write(b"transient merge dirt\\n")
    open(os.environ["DEV_WAVE_READY"], "wb").close()
    while not os.path.exists(os.environ["DEV_WAVE_RELEASE"]):
        time.sleep(0.01)
    if dirty_path:
        with open(dirty_path, "wb") as stream:
            stream.write(original)
    os.execv(real, [real, *args])
completed = subprocess.run([real, *args], check=False)
if mode == "hide-head" and completed.returncode == 0:
    open(os.environ["DEV_WAVE_MARKER"], "wb").close()
if mode == "move-wave" and completed.returncode == 0:
    subprocess.run(
        [real, "-C", os.environ["DEV_WAVE_MOVE_REPO"], "update-ref",
         os.environ["DEV_WAVE_MOVE_REF"], os.environ["DEV_WAVE_MOVE_TO"]],
        check=True,
    )
raise SystemExit(completed.returncode)
"""


def _wrapper(root: Path) -> Path:
    path = root / "git-wrapper"
    path.write_text(_WRAPPER, encoding="utf-8")
    path.chmod(0o755)
    return path


@contextlib.contextmanager
def _patched_git(executable: Path, env: dict[str, str]):
    previous_git = LAND._GIT_EXE
    previous_env = {key: os.environ.get(key) for key in env}
    LAND._GIT_EXE = str(executable)
    os.environ.update(env)
    try:
        yield
    finally:
        LAND._GIT_EXE = previous_git
        for key, value in previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_not_landed_is_distinct_from_postcondition_failure() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "not-landed",
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_NOT_LANDED, "not-landed")
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_partial_merge_mutation_is_nonretryable_postcondition_failure() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "partial",
            "DEV_WAVE_PARTIAL_PATH": str(repo.main / "base.txt"),
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (
            result.rc,
            result.status,
        ) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert (repo.main / "base.txt").read_text() == "partial mutation\n"


def test_unobservable_post_merge_head_is_nonretryable_failure() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        wrapper = _wrapper(repo.root)
        marker = repo.root / "merged"
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "hide-head",
            "DEV_WAVE_MARKER": str(marker),
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (
            result.rc,
            result.status,
        ) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), result
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_control_plane_replacement_around_status_is_rejected() -> None:
    for kind in ("file", "directory"):
        with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
            wave = repo.waves["author"]
            tip = repo.commit(wave, "wave.txt", "wave\n")
            target = (
                _handoff(repo)
                if kind == "file"
                else repo.waves["foreign"]
            )
            wrapper = _wrapper(repo.root)
            marker = repo.root / f"replaced-{kind}"
            backup = repo.root / f"replacement-backup-{kind}"
            with _patched_git(wrapper, {
                "DEV_WAVE_REAL_GIT": REAL_GIT,
                "DEV_WAVE_WRAPPER_MODE": "replace-control",
                "DEV_WAVE_MARKER": str(marker),
                "DEV_WAVE_REPLACE_TARGET": str(target),
                "DEV_WAVE_REPLACE_BACKUP": str(backup),
                "DEV_WAVE_REPLACE_KIND": kind,
            }):
                result = _land(repo.request(wave, tip=tip))
            assert result.rc == LAND.RC_CONTROL_PLANE, (kind, result)
            assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_control_plane_replacement_after_collision_inspection_is_rejected() -> None:
    for kind in ("file", "directory"):
        with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
            wave = repo.waves["author"]
            tip = repo.commit(wave, "base.txt", "wave replacement\n")
            target = (
                _handoff(repo)
                if kind == "file"
                else repo.waves["foreign"]
            )
            wrapper = _wrapper(repo.root)
            marker = repo.root / f"collision-replaced-{kind}"
            backup = repo.root / f"collision-replacement-backup-{kind}"
            with _patched_git(wrapper, {
                "DEV_WAVE_REAL_GIT": REAL_GIT,
                "DEV_WAVE_WRAPPER_MODE": "replace-after-collision",
                "DEV_WAVE_MARKER": str(marker),
                "DEV_WAVE_REPLACE_TARGET": str(target),
                "DEV_WAVE_REPLACE_BACKUP": str(backup),
                "DEV_WAVE_REPLACE_KIND": kind,
            }):
                result = _land(repo.request(wave, tip=tip))
            assert result.rc == LAND.RC_CONTROL_PLANE, (kind, result)
            assert marker.exists()
            assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_git_operation_surface_is_read_only_except_sha_ff_merge() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        wrapper = _wrapper(repo.root)
        record = repo.root / "git-calls.jsonl"
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "record",
            "DEV_WAVE_RECORD": str(record),
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (0, "landed"), result
        calls = [
            json.loads(line)
            for line in record.read_text(encoding="utf-8").splitlines()
        ]
        merge_calls = [args for args in calls if "merge" in args]
        assert len(merge_calls) == 1, calls
        merge = merge_calls[0]
        index = merge.index("merge")
        assert merge[index:] == [
            "merge", "--ff-only", "--no-stat", "--no-progress", tip,
        ]
        forbidden = {
            "push", "fetch", "pull", "rebase", "reset", "checkout", "stash",
            "branch", "switch", "remote", "update-ref", "worktree",
        }
        for args in calls:
            assert forbidden.isdisjoint(args), args
            if "config" in args:
                assert "--get-regexp" in args and "--includes" in args, args


def test_merge_child_inherits_only_explicit_lock_not_other_parent_fd() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        wrapper = _wrapper(repo.root)
        fd_record = repo.root / "fd-record.json"
        sentinel_path = repo.root / "sentinel"
        sentinel_fd = os.open(sentinel_path, os.O_RDWR | os.O_CREAT, 0o600)
        os.set_inheritable(sentinel_fd, True)
        try:
            with _patched_git(wrapper, {
                "DEV_WAVE_REAL_GIT": REAL_GIT,
                "DEV_WAVE_WRAPPER_MODE": "audit-fds",
                "DEV_WAVE_FD_RECORD": str(fd_record),
            }):
                result = _land(repo.request(wave, tip=tip))
        finally:
            os.close(sentinel_fd)
        assert (result.rc, result.status) == (0, "landed"), result
        targets = json.loads(fd_record.read_text(encoding="utf-8"))
        inherited = set(targets.values())
        assert str(sentinel_path) not in inherited, targets
        lock_targets = [
            target for target in inherited
            if target.endswith("/dev-wave-land.lock")
        ]
        assert len(lock_targets) == 1, targets


def test_wave_move_after_merge_is_landed_postcondition_failed() -> None:
    """M9: main は T に達したが wave ref が動いた事実を retryable failureへ潰さない。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        tree = _git(wave, "rev-parse", f"{tip}^{{tree}}")
        moved = _git(wave, "commit-tree", tree, "-p", tip, "-m", "moved tip")
        wave_ref = _git(wave, "symbolic-ref", "HEAD")
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "move-wave",
            "DEV_WAVE_MOVE_REPO": str(wave),
            "DEV_WAVE_MOVE_REF": wave_ref,
            "DEV_WAVE_MOVE_TO": moved,
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (
            result.rc,
            result.status,
        ) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), result
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        assert _git(wave, "rev-parse", "HEAD") == moved


def test_merge_child_inherits_lock_fd_if_helper_is_killed() -> None:
    """winner が transient dirt を持っていても loser は先に lock-busy。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        wrapper = _wrapper(repo.root)
        ready = repo.root / "ready"
        release = repo.root / "release"
        code = (
            "import importlib.util,sys;"
            f"p={str(HELPER_PATH)!r};"
            "s=importlib.util.spec_from_file_location('land_child',p);"
            "m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;"
            "s.loader.exec_module(m);"
            f"m._GIT_EXE={str(wrapper)!r};"
            "raise SystemExit(m.main(sys.argv[1:]))"
        )
        argv = [
            sys.executable, "-c", code,
            "--main-worktree", str(repo.main),
            "--wave-worktree", str(wave),
            "--tested-main-sha", repo.base,
            "--tested-wave-tip-sha", tip,
        ]
        for commit in request.audited_commits:
            argv.extend(("--audited-commit", commit))
        env = dict(os.environ)
        env.update({
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "hold-dirty",
            "DEV_WAVE_READY": str(ready),
            "DEV_WAVE_RELEASE": str(release),
            "DEV_WAVE_DIRTY_PATH": str(repo.main / "base.txt"),
        })
        process = subprocess.Popen(
            argv,
            cwd=wave,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            assert ready.exists(), "merge wrapper did not start"
            os.kill(process.pid, signal.SIGKILL)
            process.wait(timeout=2)
            result = _land(request)
            assert (result.rc, result.status) == (
                LAND.RC_LOCK_BUSY,
                "lock-busy",
            ), result
        finally:
            release.touch()
        deadline = time.monotonic() + 5
        while _git(repo.main, "rev-parse", "HEAD") != tip and time.monotonic() < deadline:
            time.sleep(0.02)
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_same_base_two_wave_winner_stale_resync_loser_land_e2e() -> None:
    """M1/M13: winner→stale loser→merge/reaccept→loser land の一続きの E2E。"""
    with _repo(waves=(("codex", "winner"), ("claude", "loser"))) as repo:
        winner = repo.waves["winner"]
        loser = repo.waves["loser"]
        winner_tip = repo.commit(winner, "winner.txt", "winner\n")
        loser_tip = repo.commit(loser, "loser.txt", "loser\n")
        handoff = _handoff(repo, state="中断")
        foreign = winner / ".git"
        watched_before = {handoff: _snapshot(handoff), foreign: _snapshot(foreign)}

        first = _land(repo.request(winner, tip=winner_tip))
        assert (first.rc, first.status) == (0, "landed"), first
        stale = _land(repo.request(loser, tip=loser_tip))
        assert (stale.rc, stale.status) == (LAND.RC_STALE_MAIN, "stale-main"), stale
        assert _git(repo.main, "rev-parse", "HEAD") == winner_tip

        _git(loser, "merge", "--no-edit", "main")
        resynced_tip = _git(loser, "rev-parse", "HEAD")
        resynced_tree = _git(loser, "rev-parse", f"{resynced_tip}^{{tree}}")
        acceptance = _run_synthetic_acceptance(
            loser,
            tested_main=winner_tip,
            tested_tip=resynced_tip,
            tested_tree=resynced_tree,
        )
        assert acceptance["tested_tree"] == resynced_tree
        audited = repo.audited(winner_tip, resynced_tip, loser)
        assert audited == tuple(
            _git(
                loser, "rev-list", "--reverse",
                f"{winner_tip}..{resynced_tip}",
            ).splitlines()
        )
        assert winner_tip not in audited
        assert loser_tip in audited and resynced_tip in audited
        second = _land(
            repo.request(
                loser,
                base=acceptance["tested_main"],
                tip=acceptance["tested_tip"],
                audited=audited,
            )
        )
        assert (second.rc, second.status) == (0, "landed"), second
        assert _git(repo.main, "rev-parse", "HEAD") == resynced_tip
        assert (repo.main / "winner.txt").read_text() == "winner\n"
        assert (repo.main / "loser.txt").read_text() == "loser\n"
        assert {path: _snapshot(path) for path in watched_before} == watched_before

        foreign_untracked = repo.main / "unknown-after.txt"
        foreign_untracked.write_text("foreign session\n", encoding="utf-8")
        foreign_untracked_before = _snapshot(foreign_untracked)
        already = _land(
            repo.request(
                loser,
                base=winner_tip,
                tip=resynced_tip,
                audited=audited,
            )
        )
        assert (already.rc, already.status) == (LAND.RC_OK, "already-landed"), already
        assert _git(repo.main, "rev-parse", "HEAD") == resynced_tip
        assert _snapshot(foreign_untracked) == foreign_untracked_before
        assert {path: _snapshot(path) for path in watched_before} == watched_before


def test_cli_emits_json_and_uses_only_sha_target_ff() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        argv = [
            sys.executable,
            str(HELPER_PATH),
            "--main-worktree", str(repo.main),
            "--wave-worktree", str(wave),
            "--tested-main-sha", repo.base,
            "--tested-wave-tip-sha", tip,
        ]
        for commit in request.audited_commits:
            argv.extend(("--audited-commit", commit))
        completed = subprocess.run(
            argv,
            cwd=wave,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert payload["status"] == "landed"
        assert payload["main_after"] == tip
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def _run() -> int:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
