# -*- coding: utf-8 -*-
"""tools/dev_wave_land.py の linked-worktree / race / land 境界テスト。

pytest と ``python3 orchestrator/tests/test_dev_wave_land.py`` の両方で走る。
全 Git mutation は tempfile 配下の合成 repository に限定する。
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import importlib.util
import json
import os
import re
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


def _git_env() -> dict[str, str]:
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    })
    return env


def _git(repo: Path, *args: str, check: bool = True) -> str:
    env = _git_env()
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


@contextlib.contextmanager
def _campaign_import_scope():
    """Campaign imports may edit sys.path; restore the complete list on exit."""
    saved_sys_path = sys.path[:]
    try:
        orchestrator_path = str(ROOT / "orchestrator")
        if orchestrator_path not in sys.path:
            sys.path.insert(0, orchestrator_path)
        yield
    finally:
        sys.path[:] = saved_sys_path


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
        spool = self.main / "docs" / "spool"
        spool.mkdir()
        (spool / "README.md").write_text("# spool\n", encoding="utf-8")
        (spool / "FOLDED.md").write_text("# receipts\n", encoding="utf-8")
        for ledger in LAND._FOLD_LEDGERS:
            directory = spool / ledger
            directory.mkdir()
            (directory / "README.md").write_text(f"# {ledger}\n", encoding="utf-8")
        tools = self.main / "tools"
        tools.mkdir()
        (tools / "check_docs.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        _git(self.main, "add", "base.txt", "docs", "tools/check_docs.py")
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


def _handoff_text(repo: _Repo, *, state: str = "作業中", base: str | None = None) -> str:
    return (
        "# foreign wave\n"
        "- 目的: parallel control plane\n"
        f"- 状態: {state}\n"
        "- 最終更新: 2000-01-01\n"
        f"- 基準コミット: {repo.base if base is None else base}\n"
        "\n"
        "## 完了した中間成果\n\nnone\n"
        "## 未完の作業と次の一手\n\ncontinue\n"
        "## 落とし穴・気づき\n\nnone\n"
    )


def _handoff(repo: _Repo, *, state: str = "作業中", name: str = "foreign.md") -> Path:
    path = repo.main / "docs" / "handoff" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_handoff_text(repo, state=state), encoding="utf-8")
    return path


def _snapshot(path: Path) -> tuple[bytes, tuple[int, int, int]]:
    metadata = path.lstat()
    return (
        path.read_bytes(),
        (metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode)),
    )


def _artifact_snapshot(path: Path) -> tuple[object, tuple[object, ...]]:
    """型を問わず foreign artifact の中身と identity を採取する。

    ``_snapshot`` は regular file 専用なので、symlink / fifo / directory /
    読めない file でも「land が一切触っていない」ことを主張できる形へ広げる。
    """
    metadata = path.lstat()
    identity = (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        metadata.st_nlink,
        metadata.st_size,
    )
    if stat.S_ISLNK(metadata.st_mode):
        payload: object = os.readlink(path)
    elif stat.S_ISDIR(metadata.st_mode):
        payload = sorted(os.listdir(path))
    elif stat.S_ISREG(metadata.st_mode):
        try:
            payload = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            payload = f"unreadable:{exc.errno}"
    else:
        payload = None
    return payload, identity


# T-220 択 (a): docs/handoff/ 直下の型・名前・大きさ・link 数・encoding・schema は
# land の受理集合に入らない。旧実装が per-file の大域拒否を出していた 15 形を列挙する。
_FOREIGN_HANDOFF_KINDS = (
    "malformed",
    "symlink",
    "fifo",
    "directory",
    "non-md-suffix",
    "editor-swap",
    "editor-backup",
    "non-ascii-name",
    "oversize",
    "hard-link",
    "unreadable",
    "empty",
    "non-utf8",
    "unknown-state",
    "empty-base-commit",
)


def _make_foreign_handoff(repo: _Repo, kind: str) -> Path:
    """docs/handoff 直下に kind に対応する異形エントリを 1 つ作る。"""
    handoff = repo.main / "docs" / "handoff"
    handoff.mkdir(parents=True, exist_ok=True)
    if kind == "malformed":
        path = handoff / "malformed.md"
        path.write_text("# missing schema\n", encoding="utf-8")
    elif kind == "symlink":
        path = handoff / "symlink.md"
        path.symlink_to(repo.main / "base.txt")
    elif kind == "fifo":
        path = handoff / "fifo.md"
        os.mkfifo(path)
    elif kind == "directory":
        path = handoff / "archive"
        path.mkdir()
        (path / "old.md").write_text(_handoff_text(repo), encoding="utf-8")
    elif kind == "non-md-suffix":
        path = handoff / "notes.txt"
        path.write_text("scratch notes\n", encoding="utf-8")
    elif kind == "editor-swap":
        path = handoff / ".foo.md.swp"
        path.write_bytes(b"b0VIM 8.0\x00\x00")
    elif kind == "editor-backup":
        path = handoff / "foo.md~"
        path.write_text(_handoff_text(repo), encoding="utf-8")
    elif kind == "non-ascii-name":
        path = handoff / "引き継ぎ.md"
        path.write_text(_handoff_text(repo), encoding="utf-8")
    elif kind == "oversize":
        path = handoff / "oversize.md"
        path.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
    elif kind == "hard-link":
        path = handoff / "linked.md"
        peer = repo.root / "handoff-hardlink-peer.md"
        peer.write_text(_handoff_text(repo), encoding="utf-8")
        os.link(peer, path)
    elif kind == "unreadable":
        path = handoff / "sealed.md"
        path.write_text(_handoff_text(repo), encoding="utf-8")
        path.chmod(0o000)
    elif kind == "empty":
        path = handoff / "empty.md"
        path.write_bytes(b"")
    elif kind == "non-utf8":
        path = handoff / "binary.md"
        path.write_bytes(b"# \xff\xfe not utf-8\n")
    elif kind == "unknown-state":
        path = handoff / "unknown-state.md"
        path.write_text(_handoff_text(repo, state="完了"), encoding="utf-8")
    elif kind == "empty-base-commit":
        # 旧 _validate_handoff_at:572 は "".split()[0] で IndexError を投げ、
        # rc 契約外の素の例外が land() を貫通していた形。
        path = handoff / "empty-base.md"
        path.write_text(_handoff_text(repo, base=""), encoding="utf-8")
    else:  # pragma: no cover - 列挙漏れの自己検査
        raise AssertionError(f"unknown foreign handoff kind: {kind}")
    return path


def _make_all_foreign_handoffs(repo: _Repo) -> dict[str, Path]:
    entries = {kind: _make_foreign_handoff(repo, kind) for kind in _FOREIGN_HANDOFF_KINDS}
    assert len(entries) == len(_FOREIGN_HANDOFF_KINDS) == 15
    assert len({path.name for path in entries.values()}) == 15
    return entries


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


def test_handoff_state_vocabulary_is_not_a_land_gate() -> None:
    """[意図した挙動変更] 状態語彙も stale date も land の gate ではない。

    旧 test は三状態だけを ``already-landed`` で確認していた。T-220 択 (a) 後は
    語彙外の値でも受理されるので期待値を反転し、さらに merge を伴う実 land
    (``landed``) で確認する。語彙の検出は check_docs の非阻害 warning へ降格した。
    """
    for state in ("作業中", "計測中", "中断", "完了", "", "arbitrary text"):
        with _repo() as repo:
            wave = repo.waves["one"]
            tip = repo.commit(wave, "wave.txt", "wave\n")
            handoff = _handoff(repo, state=state)
            watched = _artifact_snapshot(handoff)
            result = _land(repo.request(wave, tip=tip))
            assert (result.rc, result.status) == (LAND.RC_OK, "landed"), (state, result)
            assert _git(repo.main, "rev-parse", "HEAD") == tip
            assert _artifact_snapshot(handoff) == watched, state


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
    """N26/M3: 既存 dirty 防壁は worktree/index のどちらも拒否する。"""
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


def test_foreign_handoff_of_any_shape_does_not_block_land() -> None:
    """[意図した挙動変更] どの形の foreign handoff も land 全体を止めない。

    旧 test (malformed / symlink / fifo) は per-file の大域拒否を固定していた。
    T-220 択 (a) 後は 15 形すべてが同時に存在しても ``landed`` であり、かつ
    land は foreign artifact の中身にも inode にも一切触れない。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        entries = _make_all_foreign_handoffs(repo)
        watched = {path: _artifact_snapshot(path) for path in entries.values()}
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        assert (repo.main / "author.txt").read_text(encoding="utf-8") == "author\n"
        assert {
            path: _artifact_snapshot(path) for path in entries.values()
        } == watched


def test_foreign_handoff_of_any_shape_is_protected_from_target_collision() -> None:
    """N1/N2: 15 形すべてが incoming target との衝突では拒否され続ける。

    「大域拒否をやめたついでに protected からも落ちた」を赤にする。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        entries = _make_all_foreign_handoffs(repo)
        watched = {path: _artifact_snapshot(path) for path in entries.values()}
        for kind, path in entries.items():
            relative = path.relative_to(repo.main).as_posix()
            target = f"{relative}/incoming.md" if kind == "directory" else relative
            _git(wave, "reset", "-q", "--hard", repo.base)
            destination = wave / target
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text("tracked replacement\n", encoding="utf-8")
            _git(wave, "add", "--", target)
            _git(wave, "commit", "-qm", f"add {kind} collision")
            tip = _git(wave, "rev-parse", "HEAD")
            result = _land(repo.request(wave, tip=tip))
            assert result.rc == LAND.RC_CONTROL_PLANE, (kind, result)
            assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert {
            path: _artifact_snapshot(path) for path in entries.values()
        } == watched


def test_nested_untracked_under_foreign_handoff_directory() -> None:
    """N2: handoff 配下の nested untracked は大域拒否せず、衝突時だけ拒否する。

    衝突側の rc を判別するのは、776 の前方一致を素の ``in`` に戻すと
    同じ入力が 791 の RC_DIRT へ落ちて「拒否されたから緑」になるため。
    """
    for colliding in (False, True):
        with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
            wave = repo.waves["author"]
            nested = repo.main / "docs" / "handoff" / "archive" / "a.md"
            nested.parent.mkdir(parents=True, exist_ok=True)
            nested.write_text("nested foreign note\n", encoding="utf-8")
            watched = _artifact_snapshot(nested)
            relative = "docs/handoff/archive/a.md" if colliding else "author.txt"
            destination = wave / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text("incoming\n", encoding="utf-8")
            _git(wave, "add", "--", relative)
            _git(wave, "commit", "-qm", f"add {relative}")
            tip = _git(wave, "rev-parse", "HEAD")
            result = _land(repo.request(wave, tip=tip))
            if colliding:
                assert result.rc == LAND.RC_CONTROL_PLANE, result
                assert _git(repo.main, "rev-parse", "HEAD") == repo.base
            else:
                assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
                assert _git(repo.main, "rev-parse", "HEAD") == tip
            assert _artifact_snapshot(nested) == watched, colliding


def test_handoff_readme_remains_a_landable_target() -> None:
    """tracked な docs/handoff/README.md は foreign handoff があっても land できる。

    README skip を落とすと 9 commit の変更実績がある target が恒久的に
    着地不能になる。この回帰を赤にする test は従来 0 本だった。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        foreign = _handoff(repo)
        watched = _artifact_snapshot(foreign)
        payload = "# handoff\n\nupdated by the wave\n"
        readme = wave / "docs" / "handoff" / "README.md"
        readme.write_text(payload, encoding="utf-8")
        _git(wave, "add", "--", "docs/handoff/README.md")
        _git(wave, "commit", "-qm", "update handoff README")
        tip = _git(wave, "rev-parse", "HEAD")
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        assert (repo.main / "docs" / "handoff" / "README.md").read_text(
            encoding="utf-8"
        ) == payload
        assert _artifact_snapshot(foreign) == watched


def test_untracked_handoff_readme_colliding_with_target_is_rejected() -> None:
    """docs/handoff/ 面でも「incoming と衝突する未知 untracked」は拒否し続ける。

    README.md は名前集合から除かれる唯一の直下エントリなので、776 を無条件
    ``continue`` へ緩めた退行を判別できる唯一の入力でもある (rc=20 vs rc=24)。
    """
    with _repo() as repo:
        wave = repo.waves["one"]
        _handoff(repo)
        _git(wave, "rm", "-q", "docs/handoff/README.md")
        _git(wave, "commit", "-qm", "drop tracked handoff README")
        first_tip = _git(wave, "rev-parse", "HEAD")
        first = _land(repo.request(wave, tip=first_tip))
        assert (first.rc, first.status) == (LAND.RC_OK, "landed"), first
        assert not (repo.main / "docs" / "handoff" / "README.md").exists()

        untracked = repo.main / "docs" / "handoff" / "README.md"
        untracked.write_text("# foreign untracked readme\n", encoding="utf-8")
        watched = _artifact_snapshot(untracked)
        readme = wave / "docs" / "handoff" / "README.md"
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text("# reinstated by the wave\n", encoding="utf-8")
        _git(wave, "add", "--", "docs/handoff/README.md")
        _git(wave, "commit", "-qm", "reinstate handoff README")
        second_tip = _git(wave, "rev-parse", "HEAD")
        result = _land(repo.request(
            wave,
            base=first_tip,
            tip=second_tip,
            audited=repo.audited(first_tip, second_tip, wave),
        ))
        assert result.rc == LAND.RC_DIRT, result
        assert _git(repo.main, "rev-parse", "HEAD") == first_tip
        assert _artifact_snapshot(untracked) == watched


def test_untracked_nested_repository_record_collides_with_target() -> None:
    """N10 (M4): nested repo は ``?? path/`` の 1 レコードで返る。

    ``-uall`` でも collapsed なので、末尾スラッシュを正規化しないと配下 target が
    衝突検査を素通りする。git がこの形で返すこと自体を positive control で固定する。
    """
    with _repo() as repo:
        wave = repo.waves["one"]
        nested = repo.main / "vendor" / "nested"
        nested.mkdir(parents=True)
        subprocess.run(
            [REAL_GIT, "init", "-q", "-b", "main", str(nested)],
            check=True,
            env=_git_env(),
        )
        payload = nested / "payload.txt"
        payload.write_text("foreign nested repo\n", encoding="utf-8")
        raw = subprocess.run(
            [
                REAL_GIT, "-C", str(repo.main), "status", "--porcelain=v1", "-z",
                "--untracked-files=all", "--ignore-submodules=none",
            ],
            check=True,
            env=_git_env(),
            stdout=subprocess.PIPE,
        ).stdout
        assert b"?? vendor/nested/\x00" in raw, raw

        target = wave / "vendor" / "nested" / "payload.txt"
        target.parent.mkdir(parents=True)
        target.write_text("incoming\n", encoding="utf-8")
        _git(wave, "add", "--", "vendor/nested/payload.txt")
        _git(wave, "commit", "-qm", "add target under a nested repository")
        tip = _git(wave, "rev-parse", "HEAD")
        watched = _artifact_snapshot(payload)
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_DIRT, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert _artifact_snapshot(payload) == watched


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

def once(marker_env):
    marker = os.environ[marker_env]
    if os.path.exists(marker):
        return False
    open(marker, "wb").close()
    return True

def edit_handoff_in_place():
    # production の handoff 更新 (Path.write_text) と同型に inode を保存して
    # bytes だけ書き換える。既存 replace_target は inode しか動かせない。
    if not once("DEV_WAVE_EDIT_MARKER"):
        return
    payload = os.environ["DEV_WAVE_EDIT_PAYLOAD"].encode("utf-8")
    fd = os.open(os.environ["DEV_WAVE_EDIT_TARGET"], os.O_WRONLY | os.O_TRUNC)
    try:
        os.write(fd, payload)
    finally:
        os.close(fd)

def create_handoff():
    if not once("DEV_WAVE_CREATE_MARKER"):
        return
    with open(os.environ["DEV_WAVE_CREATE_PATH"], "w", encoding="utf-8") as stream:
        stream.write(os.environ["DEV_WAVE_CREATE_PAYLOAD"])

def remove_handoff():
    # 他セッションが正常終了して handoff を回収する形。運用最頻の消失方向。
    if not once("DEV_WAVE_REMOVE_MARKER"):
        return
    os.unlink(os.environ["DEV_WAVE_REMOVE_PATH"])

def dirty_tracked():
    # merge 後に main の tracked file を書き換える。post-land の縮約検査
    # (_verify_main_no_tracked_dirt) だけがこの入力を見る。
    with open(os.environ["DEV_WAVE_DIRTY_PATH"], "w", encoding="utf-8") as stream:
        stream.write(os.environ["DEV_WAVE_DIRTY_PAYLOAD"])

def swap_directory():
    # 子エントリを名前ごと保存したまま dir 自身を差し替える。名前集合が
    # 変わらないので、dir identity を落とした実装だけがこれを見逃す。
    if not once("DEV_WAVE_SWAP_MARKER"):
        return
    target = os.environ["DEV_WAVE_SWAP_TARGET"]
    backup = os.environ["DEV_WAVE_SWAP_BACKUP"]
    names = sorted(os.listdir(target))
    os.rename(target, backup)
    os.mkdir(target)
    for name in names:
        os.link(os.path.join(backup, name), os.path.join(target, name))

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
if mode == "edit-handoff" and "status" in args:
    completed = subprocess.run([real, *args], check=False)
    edit_handoff_in_place()
    raise SystemExit(completed.returncode)
if mode == "create-handoff" and "status" in args:
    completed = subprocess.run([real, *args], check=False)
    create_handoff()
    raise SystemExit(completed.returncode)
if mode == "remove-handoff" and "status" in args:
    completed = subprocess.run([real, *args], check=False)
    remove_handoff()
    raise SystemExit(completed.returncode)
if mode == "swap-handoff-dir" and "status" in args:
    completed = subprocess.run([real, *args], check=False)
    swap_directory()
    raise SystemExit(completed.returncode)
if mode == "handoff-after-merge" and "status" in args:
    completed = subprocess.run([real, *args], check=False)
    if os.path.exists(os.environ["DEV_WAVE_MERGED"]):
        create_handoff()
        edit_handoff_in_place()
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
if mode == "handoff-after-merge" and completed.returncode == 0:
    open(os.environ["DEV_WAVE_MERGED"], "wb").close()
if mode == "dirty-after-merge" and completed.returncode == 0:
    dirty_tracked()
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


@contextlib.contextmanager
def _patched_land_attr(name: str, value):
    previous = getattr(LAND, name)
    setattr(LAND, name, value)
    try:
        yield
    finally:
        setattr(LAND, name, previous)


def _fake_pending_fragment(
    repo: _Repo,
    wave: Path,
    *,
    wave_slug: str = "test-wave",
) -> tuple[str, Path, str]:
    relative = f"docs/spool/worklog/2000-01-01-{wave_slug}-1.md"
    path = wave / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "synthetic pending fragment\n"
    path.write_text(content, encoding="utf-8")
    _git(wave, "add", "--", relative)
    _git(wave, "commit", "-qm", "add synthetic pending fragment")
    return relative, path, content


class _FakeFoldPlan:
    status = "planned"

    def __init__(
        self,
        gc_path: str,
        *,
        targets: tuple[object, ...] = (),
        fragments: tuple[object, ...] = (),
    ):
        self.gc_paths = (gc_path,)
        self.targets = targets
        self.fragments = fragments


class _FakeFoldFragment:
    def __init__(self, wave: str):
        self.wave = wave


class _FakeFoldTarget:
    def __init__(self, path: str, *, before_exists: bool = True):
        self.path = path
        self.before_exists = before_exists


class _FakeFoldModule:
    def __init__(self, plan, apply, *, active=False):
        self._plan = plan
        self._apply = apply
        self._active = active

    def load_active_plan(self, repo: Path):
        assert repo.is_dir()
        return self._plan if self._active else None

    def validate_spool_layout(self, repo: Path):
        assert repo.is_dir()
        return []

    def plan_fold(self, repo: Path, *, fold_date: str):
        assert repo.is_dir()
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", fold_date)
        return self._plan

    def _state_path(self, repo: Path) -> Path:
        return repo / ".git" / LAND._FOLD_STATE_NAME

    def apply_fold(self, repo: Path, plan) -> None:
        assert plan is self._plan
        self._apply(repo, plan)


def _land_main_fold_for_resync(repo: _Repo, winner: Path) -> str:
    (repo.main / ".git" / "info" / "exclude").write_text(
        ".codex/worktrees/\n.claude/worktrees/\n",
        encoding="utf-8",
    )
    relative, _fragment, _content = _fake_pending_fragment(
        repo, winner, wave_slug="resync-main",
    )
    winner_tip = _git(winner, "rev-parse", "HEAD")

    def apply(repo_path: Path, _plan) -> None:
        (repo_path / relative).unlink()
        receipt = {
            "allocations": {},
            "authored": "2000-01-01",
            "content_sha256": hashlib.sha256(_content.encode("utf-8")).hexdigest(),
            "seq": 1,
            "wave": "resync-main",
        }
        folded = repo_path / "docs/spool/FOLDED.md"
        folded.write_text(
            folded.read_text(encoding="utf-8")
            + "- "
            + json.dumps(
                receipt,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    module = _FakeFoldModule(
        _FakeFoldPlan(
            relative,
            targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
        ),
        apply,
    )
    with (
        _patched_land_attr("_load_spool_fold", lambda: module),
        _patched_land_attr("_preflight_fold_message", lambda *_args: None),
    ):
        result = _land(repo.request(winner, tip=winner_tip))
    assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
    assert result.fold_commit_sha == result.main_after
    assert result.fold_commit_sha is not None
    assert LAND._load_spool_fold().validate_spool_layout(repo.main) == []
    return result.fold_commit_sha


def test_zero_fragment_preserves_land_result_and_commit_graph_bit_for_bit() -> None:
    """P03: fragment 0 件では既存 landed/already-landed を bit 単位で固定する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        tip = repo.commit(wave, "wave.txt", "wave\n")

        first = _land(repo.request(wave, tip=tip))
        second = _land(repo.request(wave, tip=tip))

        assert first == LAND.LandResult(
            LAND.RC_OK,
            "landed",
            "main fast-forwarded to the tested wave tip",
            repo.base,
            tip,
            tip,
        )
        assert second == LAND.LandResult(
            LAND.RC_OK,
            "already-landed",
            "another lander reached the tested tip first",
            tip,
            tip,
            tip,
        )
        assert _git(repo.main, "rev-list", "--count", f"{repo.base}..HEAD") == "1"
        assert _git(repo.main, "status", "--porcelain=v1") == ""


def test_zero_fragment_still_rejects_missing_spool_layout_before_ff() -> None:
    """F-5: pending 0 でも layout 防壁を削除した候補を no-op 扱いしない。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        shutil.rmtree(wave / "docs" / "spool")
        _git(wave, "add", "-A", "docs/spool")
        _git(wave, "commit", "-qm", "remove spool layout")
        tip = _git(wave, "rev-parse", "HEAD")

        result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_FOLD_FAILED, "fold-failed")
        assert "docs/spool" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_candidate_fold_plan_failure_happens_before_ff() -> None:
    """F-2: candidate tree の plan が赤なら main を 1 commit も進めない。"""

    class FailingPlanModule(_FakeFoldModule):
        def plan_fold(self, repo: Path, *, fold_date: str):
            raise RuntimeError("synthetic plan failure")

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        module = FailingPlanModule(_FakeFoldPlan("docs/spool/worklog/missing.md"), lambda *_args: None)

        with _patched_land_attr("_load_spool_fold", lambda: module):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_FOLD_FAILED, "fold-failed")
        assert "synthetic plan failure" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_fold_is_called_under_land_lock_and_committed_with_message_file() -> None:
    """N23: lock 内 fold 呼出しを削除すると pending の GC/commit が消えて赤になる。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _wave_fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")
        lock_observed = False

        def apply(repo_path: Path, _plan) -> None:
            nonlocal lock_observed
            contender = os.open(
                repo.main / ".git" / "dev-wave-land.lock",
                os.O_RDWR | os.O_NOFOLLOW,
            )
            try:
                try:
                    fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    lock_observed = True
                else:
                    raise AssertionError("fold ran outside the cooperative land lock")
            finally:
                os.close(contender)
            (repo_path / relative).unlink()
            folded = repo_path / "docs/spool/FOLDED.md"
            folded.write_text(folded.read_text(encoding="utf-8") + "- folded\n", encoding="utf-8")

        module = _FakeFoldModule(
            _FakeFoldPlan(
                relative,
                targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
            ),
            apply,
        )
        wrapper = _wrapper(repo.root)
        record = repo.root / "fold-git-calls.jsonl"
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
            _patched_git(wrapper, {
                "DEV_WAVE_REAL_GIT": REAL_GIT,
                "DEV_WAVE_WRAPPER_MODE": "record",
                "DEV_WAVE_RECORD": str(record),
            }),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert lock_observed
        assert result.main_after != tip
        assert result.fold_commit_sha == result.main_after
        assert _git(repo.main, "rev-parse", f"{result.main_after}^") == tip
        assert not (repo.main / relative).exists()
        assert _git(repo.main, "status", "--porcelain=v1") == ""
        message = _git(repo.main, "show", "-s", "--format=%B", result.main_after)
        assert message == LAND._FOLD_MESSAGE.rstrip("\n")
        assert _git(repo.main, "show", "-s", "--format=%an <%ae>", result.main_after) == (
            LAND.FOLD_AUTHOR_IDENTITY
        )
        calls = [
            json.loads(line)
            for line in record.read_text(encoding="utf-8").splitlines()
        ]
        commit_calls = [args for args in calls if "commit" in args]
        assert len(commit_calls) == 1, calls
        commit_args = commit_calls[0]
        commit_index = commit_args.index("commit")
        assert commit_args[commit_index:commit_index + 3] == [
            "commit", "--no-gpg-sign", "-F",
        ]
        assert "-m" not in commit_args and "--no-edit" not in commit_args


def test_land_folds_rotation_inside_lock() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        rotate_limit = 900
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        historic_body = "- " + ("historic rotation bytes " * 90) + "\n"
        worklog = (
            "# worklog\n\n## ローテーション\n\n---\n\n"
            "## 2026-08-01 (1) — old entry large enough to rotate\n\n"
            f"{historic_body}\n### 次の一手\n\n- [T-001] historic task\n\n"
            "## 2026-08-02 (2) — current entry\n\n- current body\n\n"
            "### 次の一手\n\n- [T-001] current task\n"
        )
        canonical = {
            "docs/worklog.md": worklog,
            "docs/decisions.md": (
                "# decisions\n\n## D1. seed (2026-08-01)\n\n**決定:** seed\n"
            ),
            "docs/failures.md": (
                "# failures\n\n## エントリ\n\n### F1. seed [手順漏れ]\n"
                "- 事象: seed\n- 根本原因: seed\n- 恒久対応: seed\n- 再発検知: seed\n"
            ),
            "docs/phase3.md": (
                "# phase3\n\n## 見送り台帳\n\n### プロセス文書系\n\n"
                "- [T-050] 既存見送り — 理由: seed\n\n"
                "### 研究・計測系\n\n- [T-051] 既存見送り — 理由: seed\n\n"
                "### 裁定・完了記録\n\n- [T-052] 完了済み\n"
            ),
            "docs/archive/README.md": "# archive\n\n## 現在の収容物\n",
            "tools/check_docs.py": f"WORKLOG_ROTATE_BYTES = {rotate_limit}\n",
        }
        for relative, content in canonical.items():
            path = wave / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
        fragment_relative = "docs/spool/worklog/2026-08-03-test-wave-1.md"
        (wave / fragment_relative).write_text(
            "---\n"
            "schema: izanagi-spool-v1\n"
            "ledger: worklog\n"
            "authored: 2026-08-03\n"
            "wave: test-wave\n"
            "seq: 1\n"
            "title: rotation land\n"
            "---\n"
            "## 本文\n\n- folded under the land lock\n\n"
            "## 次の一手差分\n\n### carry\n\n- [T-001]\n",
            encoding="utf-8",
            newline="\n",
        )
        _git(wave, "add", "-A")
        _git(wave, "commit", "-qm", "add rotating fold fixture")
        tip = _git(wave, "rev-parse", "HEAD")
        request = repo.request(wave, tip=tip)
        real_fold = LAND._load_spool_fold()

        class ObservedFold:
            def __init__(self):
                self.lock_observed = False
                self.rotation_path: str | None = None

            def __getattr__(self, name: str):
                return getattr(real_fold, name)

            def plan_fold(self, repo_path: Path, *, fold_date: str):
                plan = real_fold.plan_fold(repo_path, fold_date=fold_date)
                assert plan.rotation_path is not None, plan
                self.rotation_path = plan.rotation_path
                return plan

            def apply_fold(self, repo_path: Path, plan):
                contender = os.open(
                    repo.main / ".git" / "dev-wave-land.lock",
                    os.O_RDWR | os.O_NOFOLLOW,
                )
                try:
                    try:
                        fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        self.lock_observed = True
                    else:
                        raise AssertionError("rotation fold ran outside the land lock")
                finally:
                    os.close(contender)
                return real_fold.apply_fold(repo_path, plan)

        observed = ObservedFold()
        with (
            _patched_land_attr("_load_spool_fold", lambda: observed),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        ):
            result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert observed.lock_observed
        assert observed.rotation_path is not None
        assert (repo.main / observed.rotation_path).is_file()
        rotation_name = Path(observed.rotation_path).name
        archive_readme = (repo.main / "docs/archive/README.md").read_text(
            encoding="utf-8",
        )
        assert rotation_name in archive_readme
        assert (repo.main / "docs/worklog.md").stat().st_size <= rotate_limit
        assert result.fold_commit_sha == result.main_after
        declared = LAND.verify_declared_fold_commit(
            repo.main,
            fold_commit_sha=result.fold_commit_sha,
            landed_main_sha=result.main_after,
            landed_commits=request.audited_commits,
            wave_tip=tip,
        )
        assert declared.ok, declared


def test_p06_supervised_branch_slug_with_matching_fragments_can_fold() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n", encoding="utf-8",
        )
        run_id = "dw-" + "a" * 32
        _git(wave, "branch", "-m", f"dev-wave/{run_id}/w001")
        slug = f"dev-wave-{run_id}-w001"
        relative, _wave_fragment, _content = _fake_pending_fragment(
            repo, wave, wave_slug=slug,
        )
        tip = _git(wave, "rev-parse", "HEAD")

        def apply(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            folded = repo_path / "docs/spool/FOLDED.md"
            folded.write_text(
                folded.read_text(encoding="utf-8") + "- folded\n",
                encoding="utf-8",
            )

        plan = _FakeFoldPlan(
            relative,
            targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
            fragments=(_FakeFoldFragment(slug),),
        )
        module = _FakeFoldModule(plan, apply)
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.fold_commit_sha == result.main_after


def test_land_accepts_its_fold_commit_with_repository_commit_encoding() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n", encoding="utf-8",
        )
        _git(repo.main, "config", "i18n.commitEncoding", "ISO-8859-1")
        relative, _wave_fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")

        def apply(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            folded = repo_path / "docs/spool/FOLDED.md"
            folded.write_text(
                folded.read_text(encoding="utf-8") + "- folded\n",
                encoding="utf-8",
            )

        module = _FakeFoldModule(
            _FakeFoldPlan(
                relative,
                targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
            ),
            apply,
        )
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        commit_object = "\n" + _git(repo.main, "cat-file", "commit", result.main_after)
        assert "\nencoding ISO-8859-1\n" in commit_object


def test_n35_supervised_branch_rejects_fragment_from_another_slug_before_ff() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n", encoding="utf-8",
        )
        run_id = "dw-" + "a" * 32
        _git(wave, "branch", "-m", f"dev-wave/{run_id}/w001")
        slug = f"dev-wave-{run_id}-w001"
        relative, _wave_fragment, _content = _fake_pending_fragment(
            repo, wave, wave_slug=slug,
        )
        tip = _git(wave, "rev-parse", "HEAD")
        plan = _FakeFoldPlan(
            relative,
            fragments=(_FakeFoldFragment("dev-wave-dw-" + "b" * 32 + "-w001"),),
        )
        module = _FakeFoldModule(
            plan,
            lambda *_args: (_ for _ in ()).throw(AssertionError("apply must not run")),
        )
        with _patched_land_attr("_load_spool_fold", lambda: module):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_FOLD_FAILED, "fold-failed")
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_fold_failure_rolls_back_ff_and_never_returns_landed() -> None:
    """N24/F-2: fold 失敗は実装 commit を含めて ff 前へ戻す。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _wave_fragment, content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")

        def fail_after_gc(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            raise RuntimeError("synthetic fold failure")

        module = _FakeFoldModule(_FakeFoldPlan(relative), fail_after_gc)
        with _patched_land_attr("_load_spool_fold", lambda: module):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_FOLD_FAILED, "fold-failed"), result
        assert "synthetic fold failure" in result.reason
        assert result.status not in {"landed", "already-landed"}
        assert result.main_after == repo.base
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert not (repo.main / relative).exists()
        assert _git(repo.main, "status", "--porcelain=v1") == ""
        assert _git(repo.main, "rev-list", "--count", f"{repo.base}..HEAD") == "0"


def test_pending_fragment_postcondition_failure_is_fold_failure() -> None:
    """N25: apply 後 pending=0 検査を削除すると残件ありで landed になって赤になる。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _wave_fragment, content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")
        module = _FakeFoldModule(_FakeFoldPlan(relative), lambda *_args: None)

        with _patched_land_attr("_load_spool_fold", lambda: module):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_FOLD_FAILED, "fold-failed"), result
        assert "pending fragment postcondition failed" in result.reason
        assert result.main_after == repo.base
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert not (repo.main / relative).exists()
        assert _git(repo.main, "status", "--porcelain=v1") == ""


def test_generated_canonical_validation_failure_rolls_back_ff() -> None:
    """F-3: apply 後の docs gate が赤なら fold commit も wave tip も残さない。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _wave_fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")

        def apply(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()

        module = _FakeFoldModule(_FakeFoldPlan(relative), apply)
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr(
                "_validate_generated_docs",
                lambda *_args: (_ for _ in ()).throw(RuntimeError("synthetic check_docs failure")),
            ),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_FOLD_FAILED, "fold-failed")
        assert "synthetic check_docs failure" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert _git(repo.main, "status", "--porcelain=v1") == ""


def test_failed_cas_rollback_has_distinct_rc_and_status() -> None:
    """F-2: main を戻せない異常を通常の fold-failed と混同しない。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _wave_fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")

        def fail_after_gc(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            raise RuntimeError("synthetic fold failure")

        module = _FakeFoldModule(_FakeFoldPlan(relative), fail_after_gc)
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_rollback_fold", lambda *_args, **_kwargs: ["synthetic CAS refusal"]),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (
            LAND.RC_FOLD_ROLLBACK_FAILED,
            "fold-rollback-failed",
        )
        assert "rollback incomplete" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_active_transaction_resumes_before_main_dirty_gate() -> None:
    """F-6: partial canonical dirt があっても stored plan を通常 land から完遂する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _wave_fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")
        _git(repo.main, "merge", "--ff-only", tip)
        receipt_rel = "docs/spool/FOLDED.md"
        (repo.main / receipt_rel).write_text("partial canonical\n", encoding="utf-8")

        def resume(repo_path: Path, _plan) -> None:
            (repo_path / receipt_rel).write_text("# receipts\n- resumed\n", encoding="utf-8")
            (repo_path / relative).unlink()

        plan = _FakeFoldPlan(
            relative,
            targets=(_FakeFoldTarget(receipt_rel),),
        )
        module = _FakeFoldModule(plan, resume, active=True)
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.main_after != tip
        assert _git(repo.main, "rev-parse", f"{result.main_after}^") == tip
        assert _git(repo.main, "status", "--porcelain=v1") == ""


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
    """[意図した挙動変更] 差し替えの拒否は worktree 面に残り、handoff 面では消える。

    ``file`` = foreign handoff を同 bytes・別 inode へ差し替える形。per-entry
    identity を捨てたので期待値を ``landed`` へ反転する (assert は削除せず反転)。
    ``directory`` = 登録済み foreign worktree の差し替えで、負例として不変。
    """
    expectations = {
        "file": (LAND.RC_OK, "landed"),
        "directory": (LAND.RC_CONTROL_PLANE, "rejected"),
    }
    for kind, expected in expectations.items():
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
            assert (result.rc, result.status) == expected, (kind, result)
            assert marker.exists(), kind
            assert _git(repo.main, "rev-parse", "HEAD") == (
                tip if kind == "file" else repo.base
            ), kind


def test_control_plane_replacement_after_collision_inspection_is_rejected() -> None:
    """[意図した挙動変更] land 直前 (:1343) の再観測も handoff の内容/inode を見ない。

    ``directory`` は負例として不変。``file`` は 764/766 と同じ理由で ``landed`` へ
    反転する — この 2 窓は同じ ``_ControlSnapshot`` 比較なので同時に閉じる。
    """
    expectations = {
        "file": (LAND.RC_OK, "landed"),
        "directory": (LAND.RC_CONTROL_PLANE, "rejected"),
    }
    for kind, expected in expectations.items():
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
            assert (result.rc, result.status) == expected, (kind, result)
            assert marker.exists(), kind
            assert _git(repo.main, "rev-parse", "HEAD") == (
                tip if kind == "file" else repo.base
            ), kind


def test_foreign_handoff_edited_in_place_around_status_does_not_block_land() -> None:
    """P4 の正例: 他セッションが handoff を in-place 更新しても land は落ちない。

    運用ルール (節目ごと + 10 分おきに育てる) の書き込みは inode を保存して
    bytes を変える。identities へ内容 sha256 を戻すとこの test が赤になる。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        handoff = _handoff(repo)
        inode_before = handoff.lstat().st_ino
        updated = _handoff_text(repo, state="中断") + "\n節目の追記\n"
        wrapper = _wrapper(repo.root)
        marker = repo.root / "handoff-edited"
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "edit-handoff",
            "DEV_WAVE_EDIT_MARKER": str(marker),
            "DEV_WAVE_EDIT_TARGET": str(handoff),
            "DEV_WAVE_EDIT_PAYLOAD": updated,
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert marker.exists()
        assert handoff.lstat().st_ino == inode_before
        assert handoff.read_text(encoding="utf-8") == updated
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_foreign_handoff_appearing_mid_flight_is_still_rejected() -> None:
    """N3: status を跨いで新しい名前の handoff が現れたら拒否し続ける。"""
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        _handoff(repo)
        appearing = repo.main / "docs" / "handoff" / "appearing.md"
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "create-handoff",
            "DEV_WAVE_CREATE_MARKER": str(repo.root / "handoff-created"),
            "DEV_WAVE_CREATE_PATH": str(appearing),
            "DEV_WAVE_CREATE_PAYLOAD": _handoff_text(repo),
        }):
            result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_CONTROL_PLANE, result
        assert appearing.exists()
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_foreign_handoff_disappearing_mid_flight_is_still_rejected() -> None:
    """N3 の消失方向: 他セッションが正常終了して handoff を回収しても拒否する。

    出現方向 (``create-handoff``) だけでは名前集合の片側しか押さえられない。
    他セッションの正常終了 (handoff の回収) は「名前集合が縮む」形であり、
    出現だけを拒否して消失を見逃す実装をここで赤にする。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        disappearing = _handoff(repo, name="disappearing.md")
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "remove-handoff",
            "DEV_WAVE_REMOVE_MARKER": str(repo.root / "handoff-removed"),
            "DEV_WAVE_REMOVE_PATH": str(disappearing),
        }):
            result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_CONTROL_PLANE, result
        assert not disappearing.exists()
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_handoff_directory_replacement_around_status_is_still_rejected() -> None:
    """N4: docs/handoff 自身の差し替えは拒否し続ける。

    子エントリを名前ごと保存して差し替えるので、名前集合は一致する。
    dir identity を落とした実装だけがこれを見逃す。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        handoff_dir = repo.main / "docs" / "handoff"
        _handoff(repo)
        inode_before = handoff_dir.lstat().st_ino
        names_before = sorted(path.name for path in handoff_dir.iterdir())
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "swap-handoff-dir",
            "DEV_WAVE_SWAP_MARKER": str(repo.root / "handoff-dir-swapped"),
            "DEV_WAVE_SWAP_TARGET": str(handoff_dir),
            "DEV_WAVE_SWAP_BACKUP": str(repo.root / "handoff-dir-backup"),
        }):
            result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_CONTROL_PLANE, result
        assert sorted(path.name for path in handoff_dir.iterdir()) == names_before
        assert handoff_dir.lstat().st_ino != inode_before
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_post_land_is_not_failed_by_foreign_handoff_activity() -> None:
    """P3: merge 後の foreign handoff 活動を自分の land の failure にしない。

    post-land で control-plane を再観測すると、他セッションの正常な handoff
    作成・更新が非再試行の RC_LANDED_POSTCONDITION_FAILED になる。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        handoff = _handoff(repo)
        appearing = repo.main / "docs" / "handoff" / "post-land.md"
        updated = _handoff_text(repo, state="中断") + "\nland 後の追記\n"
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "handoff-after-merge",
            "DEV_WAVE_MERGED": str(repo.root / "merged"),
            "DEV_WAVE_CREATE_MARKER": str(repo.root / "post-land-created"),
            "DEV_WAVE_CREATE_PATH": str(appearing),
            "DEV_WAVE_CREATE_PAYLOAD": _handoff_text(repo),
            "DEV_WAVE_EDIT_MARKER": str(repo.root / "post-land-edited"),
            "DEV_WAVE_EDIT_TARGET": str(handoff),
            "DEV_WAVE_EDIT_PAYLOAD": updated,
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert appearing.exists()
        assert handoff.read_text(encoding="utf-8") == updated
        assert _git(repo.main, "rev-parse", "HEAD") == tip


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


def test_tracked_dirt_appearing_after_successful_merge_is_postcondition_failed() -> None:
    """N6 の post-land 面: main が T に達した後の tracked dirt を成功に潰さない。

    ``_verify_main_no_tracked_dirt`` の**成功経路**を守る唯一の入力である。
    pre-land の ``_verify_main_clean`` は merge 前にしか走らず、
    ``_postcondition`` 成功枝の先行検査 (symbolic HEAD / ref sha / wave 三点)
    はいずれも main の worktree dirt を観測しない。つまりこの入力を拒否できる
    位置は ``_postcondition`` 成功枝の ``_verify_main_no_tracked_dirt``
    1 箇所しかない (DW-M01)。
    """
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        dirt = "merge 後に現れた tracked dirt\n"
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "dirty-after-merge",
            "DEV_WAVE_DIRTY_PATH": str(repo.main / "base.txt"),
            "DEV_WAVE_DIRTY_PAYLOAD": dirt,
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (
            result.rc,
            result.status,
        ) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), result
        # 成功枝 (main_after == tested tip) を通ったことを固定する。失敗枝の
        # _main_tracked_or_index_dirty との取り違えをここで排除する。
        assert (result.main_before, result.main_after) == (repo.base, tip), result
        assert result.reason == "main tracked/index/submodule dirt is forbidden", result
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        assert (repo.main / "base.txt").read_text(encoding="utf-8") == dirt


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


def test_main_fold_resync_reaches_no_fold_and_declared_fold_consumers() -> None:
    """main-side fold を merge した wave が land の両 cutoff 配線を通る。"""

    for declared_fold in (False, True):
        with _repo(waves=(("codex", "winner"), ("claude", "loser"))) as repo:
            winner = repo.waves["winner"]
            loser = repo.waves["loser"]
            main_fold = _land_main_fold_for_resync(repo, winner)

            if declared_fold:
                relative, _fragment, _content = _fake_pending_fragment(
                    repo, loser, wave_slug="resync-loser",
                )
            else:
                repo.commit(loser, "loser.txt", "loser\n")
                relative = None
            _git(loser, "merge", "--no-edit", "main")
            resynced_tip = _git(loser, "rev-parse", "HEAD")
            audited = repo.audited(main_fold, resynced_tip, loser)
            assert main_fold not in audited
            assert audited[-1] == resynced_tip

            if relative is None:
                result = _land(
                    repo.request(
                        loser,
                        base=main_fold,
                        tip=resynced_tip,
                        audited=audited,
                    )
                )
            else:
                def apply(repo_path: Path, _plan) -> None:
                    (repo_path / relative).unlink()
                    folded = repo_path / "docs/spool/FOLDED.md"
                    folded.write_text(
                        folded.read_text(encoding="utf-8") + "- loser fold\n",
                        encoding="utf-8",
                    )

                module = _FakeFoldModule(
                    _FakeFoldPlan(
                        relative,
                        targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
                    ),
                    apply,
                )
                with (
                    _patched_land_attr("_load_spool_fold", lambda: module),
                    _patched_land_attr("_preflight_fold_message", lambda *_args: None),
                ):
                    result = _land(
                        repo.request(
                            loser,
                            base=main_fold,
                            tip=resynced_tip,
                            audited=audited,
                        )
                    )

            assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
            assert _git(repo.main, "merge-base", "--is-ancestor", main_fold, "HEAD") == ""


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


def test_exploration_external_root_keeps_wave_clean() -> None:
    """F98 正例: fake evaluator の exploration campaign は wave 外だけを汚す。"""
    with _campaign_import_scope():
        from types import SimpleNamespace
        from campaign import env_contract, layout as layout_module, loop, pipeline, wal
        from campaign.build_admission import GeneratorId, build_run_context
        from campaign.model import (
            CampaignConfig, Genome, STAGE_ABORT, STAGE_BUILD_START,
        )
        from campaign.pipeline import EvalResult, PerfConfig

    env_name = layout_module._EXPLORATION_OUTPUT_ROOT_ENV
    sentinel = object()
    saved_env = os.environ.get(env_name, sentinel)
    saved_repo_output_root = layout_module.repo_output_root
    saved_evaluate = loop.evaluate
    saved_source_digest = loop.source_digest
    fake_variant = {}
    layout_module._reset_exploration_output_root_pin_for_tests()
    try:
        with _repo() as repo:
            wave = repo.waves["one"]
            external = repo.root / "external-output"
            external.mkdir()
            os.environ[env_name] = str(external)
            layout_module.repo_output_root = lambda: str(wave / "output")
            loop.source_digest = SimpleNamespace(
                resolve_evidence=lambda *_args, **_kwargs: SimpleNamespace(
                    src_token="stock",
                ),
            )

            def fake_evaluate(
                genome, layout, env_tag, _commit, _perf, _clocks, **kwargs,
            ):
                variant = pipeline.variant_id(genome, kwargs["src_token"])
                attempt_id = "f98-valid-prebuild-abort"
                fake_variant["value"] = variant
                wal.log(
                    layout, variant, STAGE_BUILD_START, env_tag,
                    {
                        "genome": genome.canonical(),
                        "build_attempt_id": attempt_id,
                    },
                )
                wal.log(
                    layout, variant, STAGE_ABORT, env_tag,
                    {
                        "reason": "f98-fixture-prebuild-abort",
                        "build_attempt_id": attempt_id,
                    },
                )
                return EvalResult(
                    genome=genome, variant=variant, certified=False,
                    aborted=True,
                )

            loop.evaluate = fake_evaluate
            cfg = CampaignConfig(
                spec_slug="f98", search_tag="external",
                spec_content="f98 external-root acceptance",
                ccbench_commit="deadbeef",
            )
            context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
            authorization = env_contract.authorize("linux-baremetal")
            contract = authorization.contract
            summary = loop.run_campaign(
                cfg, [Genome("silo", {"BACK_OFF": 1})],
                PerfConfig(records=1, threads=1), contract.env_tag,
                contract.clocks_per_us, numactl=contract.numactl,
                do_bench=False, log=lambda *_args: None,
                authorization_contract=authorization,
                build_context=context, campaign_namespace="exploration",
            )
            campaign_root = Path(summary.layout_root)
            assert campaign_root.is_relative_to(external)
            assert (external / "exploration" / "namespace.json").read_bytes() == (
                b'{"namespace":"exploration"}\n'
            )
            assert (campaign_root / "campaign.lock").is_file()
            assert (campaign_root / "runs" / "wal.jsonl").is_file()
            replayed = wal.replay(
                layout_module.ExplorationCampaignLayout(root=str(campaign_root)),
                admission_policy=context.policy,
            )
            assert replayed[fake_variant["value"]].aborted
            assert _git(wave, "status", "--porcelain=v1", "--untracked-files=all") == ""

            request = repo.request(wave)
            with _cwd(wave):
                repository = LAND._verify_repository(request)
                try:
                    LAND._verify_wave_clean(repository)
                finally:
                    repository.close()
    finally:
        loop.evaluate = saved_evaluate
        loop.source_digest = saved_source_digest
        layout_module.repo_output_root = saved_repo_output_root
        layout_module._reset_exploration_output_root_pin_for_tests()
        if saved_env is sentinel:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = saved_env


def test_exploration_default_root_stops_before_wave_dirt() -> None:
    """M6/F98 負例: wave-local default は ensure gate で作成前に拒否する。"""
    with _campaign_import_scope():
        from campaign import layout as layout_module

    env_name = layout_module._EXPLORATION_OUTPUT_ROOT_ENV
    sentinel = object()
    saved_env = os.environ.get(env_name, sentinel)
    saved_repo_output_root = layout_module.repo_output_root
    layout_module._reset_exploration_output_root_pin_for_tests()
    try:
        for family in ("codex", "claude"):
            with _repo(waves=((family, "one"),)) as repo:
                wave = repo.waves["one"]
                local_output = wave / "output"
                os.environ.pop(env_name, None)
                layout_module.repo_output_root = lambda: str(local_output)
                campaign = layout_module.exploration_campaign_layout("f98-default")
                assert campaign.root == str(
                    local_output / "exploration" / "campaigns" / "f98-default"
                )
                try:
                    campaign.ensure()
                    assert False, "wave-local exploration root を拒否すべき"
                except ValueError as exc:
                    message = str(exc)
                    assert "worktree container" in message
                    assert env_name in message
                    assert "絶対 path" in message
                    assert "job 専用" in message
                    assert "base は exploration/ 自体ではない" in message
                assert not local_output.exists()
                assert _git(
                    wave, "status", "--porcelain=v1", "--untracked-files=all",
                ) == ""
    finally:
        layout_module.repo_output_root = saved_repo_output_root
        layout_module._reset_exploration_output_root_pin_for_tests()
        if saved_env is sentinel:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = saved_env


def test_verify_wave_clean_rejects_plain_untracked_file_as_dirt() -> None:
    """RC_DIRT 対照は campaign tree に依存しない plain untracked file とする。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        (wave / "plain-untracked.txt").write_text("dirt\n", encoding="utf-8")
        with _cwd(wave):
            repository = LAND._verify_repository(repo.request(wave))
            try:
                try:
                    LAND._verify_wave_clean(repository)
                    assert False, "plain untracked file を RC_DIRT で拒否すべき"
                except LAND._Reject as exc:
                    assert exc.rc == LAND.RC_DIRT
                    assert exc.reason == "wave worktree must be completely clean"
            finally:
                repository.close()


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
