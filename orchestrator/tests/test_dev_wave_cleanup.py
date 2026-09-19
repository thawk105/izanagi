"""land 後 cleanup CLI の破壊安全性と再入状態を固定する。"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path

import pytest


_REPO = Path(__file__).resolve().parents[2]
_TOOL = _REPO / "tools" / "dev_wave_cleanup.py"
sys.path.insert(0, os.fspath(_REPO / "tools"))
_SPEC = importlib.util.spec_from_file_location("dev_wave_cleanup_under_test", _TOOL)
assert _SPEC is not None and _SPEC.loader is not None
cleanup = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = cleanup
_SPEC.loader.exec_module(cleanup)


@dataclass(frozen=True)
class Repo:
    main: Path
    wave: Path
    branch: str
    base: str
    tip: str


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "-C", os.fspath(cwd), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"git {args!r} rc={result.returncode}: "
            f"{result.stderr.decode('utf-8', 'replace')}"
        )
    return result


def _sha(cwd: Path, expression: str = "HEAD") -> str:
    return _git(cwd, "rev-parse", expression).stdout.decode().strip()


def _make_repo(
    tmp_path: Path,
    monkeypatch,
    *,
    locked: bool = False,
    landed: bool = True,
) -> Repo:
    main = tmp_path / "main"
    wave = main / ".claude" / "worktrees" / "wave"
    subprocess.run(
        ["git", "init", "-b", "main", os.fspath(main)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    _git(main, "config", "user.name", "Cleanup Test")
    _git(main, "config", "user.email", "cleanup@example.invalid")
    (main / "tracked.txt").write_text("base\n", encoding="utf-8")
    _git(main, "add", "tracked.txt")
    _git(main, "commit", "-m", "base")
    base = _sha(main)
    wave.parent.mkdir(parents=True)
    _git(main, "worktree", "add", "-b", "wave", os.fspath(wave))
    (wave / "tracked.txt").write_text("wave\n", encoding="utf-8")
    _git(wave, "commit", "-am", "wave")
    tip = _sha(wave)
    if landed:
        _git(main, "merge", "--ff-only", "wave")
    if locked:
        _git(main, "worktree", "lock", "--reason", "synthetic", os.fspath(wave))
    monkeypatch.setattr(cleanup, "_REPO", main)
    return Repo(main, wave, "wave", base, tip)


@dataclass(frozen=True)
class ChildRepo:
    repo: Repo
    child: Path
    manifest: Path
    evidence: Path
    admin: Path
    head: str


def _make_child_repo(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path, monkeypatch)
    child = tmp_path / 'child'
    _git(repo.main, 'worktree', 'add', '-b', 'author', str(child), repo.base)
    (child / 'tracked.txt').write_text('integrated\n')
    (child / '.gitignore').write_text('ignored.bin\n')
    _git(child, 'add', 'tracked.txt', '.gitignore')
    _git(child, 'commit', '-m', 'author implementation')
    (child / 'author-result.md').write_text('terminal report\n')
    _git(child, 'add', 'author-result.md')
    _git(child, 'commit', '-m', 'author result')
    head = _sha(child)
    (repo.main / 'tracked.txt').write_text('integrated\n')
    _git(repo.main, 'commit', '-am', 'integrate owned file separately')
    assert _git(repo.main, 'merge-base', '--is-ancestor', head, 'main', check=False).returncode == 1
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'schema': 'izanagi-dev-wave-child-worktrees/v1',
        'wave_worktree': str(repo.wave), 'entries': [{'path': str(child), 'purpose': 'author',
        'branch': 'refs/heads/author', 'owned_paths': ['tracked.txt']}]}))
    admin = Path(_git(child, 'rev-parse', '--git-dir').stdout.decode().strip())
    return ChildRepo(repo, child, manifest, tmp_path / 'evidence', admin, head)


def _child_argv(case):
    return ['remove-child', '--main-worktree', str(case.repo.main), '--manifest', str(case.manifest),
            '--child-worktree', str(case.child), '--evidence-dir', str(case.evidence)]


def _edit_child_manifest(case, **fields):
    data = json.loads(case.manifest.read_text())
    data['entries'][0].update(fields)
    case.manifest.write_text(json.dumps(data))


def _file_snapshot(root):
    if not root.exists():
        return None
    return {str(path.relative_to(root)): ('link', os.readlink(path)) if path.is_symlink()
            else ('file', path.read_bytes(), path.stat().st_mode) for path in root.rglob('*')
            if path.is_symlink() or path.is_file()}


def _child_rejected(case, monkeypatch, phase, rc=20, argv=None, reason=None):
    before = (_file_snapshot(case.child), _file_snapshot(case.admin), _file_snapshot(case.evidence),
              _sha(case.repo.main, 'refs/heads/author'))
    calls = []
    original_git, original_remove = cleanup._git, cleanup._remove_verified_tree

    def spy_git(cwd, *args):
        if args[:2] in {('worktree', 'unlock'), ('checkout', '--detach')}:
            calls.append(args)
        return original_git(cwd, *args)

    def spy_remove(*args):
        calls.append(('rmtree',))
        return original_remove(*args)

    monkeypatch.setattr(cleanup, '_git', spy_git)
    monkeypatch.setattr(cleanup, '_remove_verified_tree', spy_remove)
    with pytest.raises(cleanup.CleanupFailure) as caught:
        cleanup.run(argv or _child_argv(case))
    assert (caught.value.rc, caught.value.phase) == (rc, phase), str(caught.value)
    if reason:
        assert reason in caught.value.reason
    assert not calls
    assert before == (_file_snapshot(case.child), _file_snapshot(case.admin), _file_snapshot(case.evidence),
                      _sha(case.repo.main, 'refs/heads/author'))


def test_remove_child_archives_dirty_integrated_author_and_keeps_branch(tmp_path, monkeypatch, capsys):
    case = _make_child_repo(tmp_path, monkeypatch)
    (case.child / 'tracked.txt').write_text('staged\n')
    _git(case.child, 'add', 'tracked.txt')
    (case.child / 'tracked.txt').write_text('unstaged\n')
    (case.child / 'scratch.txt').write_bytes(b'scratch\x00bytes')
    (case.child / 'ignored.bin').write_bytes(b'ignored\xff')
    (case.child / 'scratch-link').symlink_to('scratch.txt')
    expected = _file_snapshot(case.child)
    expected.pop('.git')
    wave_before = _file_snapshot(case.repo.wave)
    main_head, wave_head = _sha(case.repo.main), _sha(case.repo.wave)
    main_status = _git(case.repo.main, 'status', '--porcelain').stdout
    original_git = cleanup._git

    def keep_branch(cwd, *args):
        assert args[:2] != ('branch', '-d')
        return original_git(cwd, *args)

    monkeypatch.setattr(cleanup, '_git', keep_branch)
    original_run = cleanup.run
    results = []

    def capture_run(argv):
        result = original_run(argv)
        results.append(result)
        return result

    monkeypatch.setattr(cleanup, 'run', capture_run)
    assert cleanup.main(_child_argv(case)) == 0
    assert capsys.readouterr().out.splitlines()[0] == 'removed'
    result, = results
    assert result.outcome == 'removed'
    assert len(result.occupancy) == 2
    assert not case.child.exists() and not case.admin.exists()
    assert cleanup._record_for(cleanup._worktree_records(case.repo.main), case.child) is None
    assert _sha(case.repo.main, 'refs/heads/author') == case.head
    assert (_sha(case.repo.main), _sha(case.repo.wave)) == (main_head, wave_head)
    assert _file_snapshot(case.repo.wave) == wave_before
    assert (case.repo.main / 'tracked.txt').read_bytes() == b'integrated\n'
    assert _git(case.repo.main, 'status', '--porcelain').stdout == main_status
    receipt = json.loads((case.evidence / 'removed.json').read_text())
    assert set(receipt['files']) == {'committed.patch', 'dirty.tar.gz', 'tracked.patch', 'index.patch', 'status.txt', 'head-sha.txt', 'branch.txt'}
    assert (case.evidence / 'head-sha.txt').read_text().strip() == case.head
    assert (case.evidence / 'branch.txt').read_text().strip() == 'refs/heads/author'
    assert b'!! ignored.bin\x00' in (case.evidence / 'status.txt').read_bytes()
    committed = (case.evidence / 'committed.patch').read_bytes()
    assert b'diff --git a/author-result.md b/author-result.md\n' in committed
    assert b'@@ -0,0 +1 @@\n+terminal report\n' in committed
    restored = tmp_path / 'restored'
    _git(case.repo.main, 'worktree', 'add', '--detach', str(restored), case.head)
    _git(restored, 'apply', '--cached', str(case.evidence / 'index.patch'))
    assert _git(restored, 'show', ':tracked.txt').stdout == b'staged\n'
    _git(restored, 'apply', str(case.evidence / 'tracked.patch'))
    with tarfile.open(case.evidence / 'dirty.tar.gz') as archive:
        archive.extractall(restored, filter='data')
    actual = _file_snapshot(restored)
    actual.pop('.git')
    assert actual == expected


def test_remove_child_rejects_unregistered_path(tmp_path, monkeypatch):
    case = _make_child_repo(tmp_path, monkeypatch)
    _edit_child_manifest(case, path=str(tmp_path / 'different'))
    _child_rejected(case, monkeypatch, 'manifest')


def test_remove_child_rejects_live_process_cwd(tmp_path, monkeypatch):
    case = _make_child_repo(tmp_path, monkeypatch)
    process = subprocess.Popen(
        [sys.executable, '-c', 'import sys; sys.stdin.buffer.read(1)'],
        cwd=case.child, stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        _child_rejected(case, monkeypatch, 'occupancy', 21)
    finally:
        assert process.stdin is not None
        process.stdin.write(b'x')
        process.stdin.close()
        assert process.wait(timeout=10) == 0


def test_remove_child_rejects_unintegrated_author_commit(tmp_path, monkeypatch):
    case = _make_child_repo(tmp_path, monkeypatch)
    (case.child / 'tracked.txt').write_text('not integrated\n')
    _git(case.child, 'commit', '-am', 'unintegrated')
    _child_rejected(case, monkeypatch, 'integration', reason='tracked.txt')


def test_remove_child_empty_owned_paths_requires_ancestry(tmp_path, monkeypatch):
    case = _make_child_repo(tmp_path, monkeypatch)
    _edit_child_manifest(case, owned_paths=[])
    _child_rejected(case, monkeypatch, 'integration', reason='empty owned_paths')


def test_remove_child_rejects_nonempty_evidence_dir(tmp_path, monkeypatch):
    case = _make_child_repo(tmp_path, monkeypatch)
    case.evidence.mkdir()
    (case.evidence / 'sentinel').write_bytes(b'keep')
    _child_rejected(case, monkeypatch, 'evidence')


@pytest.mark.parametrize('target', ['wave', 'primary'])
def test_remove_child_rejects_wave_root_and_primary(tmp_path, monkeypatch, target):
    case = _make_child_repo(tmp_path, monkeypatch)
    path = case.repo.wave if target == 'wave' else case.repo.main
    branch = 'wave' if target == 'wave' else 'main'
    _edit_child_manifest(case, path=str(path), branch='refs/heads/' + branch)
    argv = _child_argv(case)
    argv[6] = str(path)
    before = _file_snapshot(path)
    _child_rejected(case, monkeypatch, 'preflight', argv=argv)
    assert _file_snapshot(path) == before


def test_remove_child_rejects_branch_mismatch(tmp_path, monkeypatch):
    case = _make_child_repo(tmp_path, monkeypatch)
    _edit_child_manifest(case, branch='refs/heads/different')
    _child_rejected(case, monkeypatch, 'preflight')


def test_remove_child_rejects_unreachable_reflog_history(tmp_path, monkeypatch):
    case = _make_child_repo(tmp_path, monkeypatch)
    (case.child / 'lost.txt').write_text('unreachable after reset')
    _git(case.child, 'add', 'lost.txt')
    _git(case.child, 'commit', '-m', 'lost history')
    _git(case.child, 'reset', '--hard', case.head)
    _child_rejected(case, monkeypatch, 'integration', reason='unreachable')


def test_remove_child_rejects_skip_worktree_flag(tmp_path, monkeypatch):
    case = _make_child_repo(tmp_path, monkeypatch)
    _git(case.child, 'update-index', '--skip-worktree', 'tracked.txt')
    (case.child / 'tracked.txt').write_text('hidden dirt')
    _child_rejected(case, monkeypatch, 'backup-precheck')


@pytest.mark.parametrize('driver', ['x', 'unspecified'], ids=['named-x', 'named-unspecified'])
def test_remove_child_rejects_clean_filter(tmp_path, monkeypatch, driver):
    case = _make_child_repo(tmp_path, monkeypatch)
    (case.child / '.gitattributes').write_text(f'* filter={driver}\n')
    command = 'tr a-z A-Z' if driver == 'unspecified' else 'cat'
    _git(case.child, 'config', f'filter.{driver}.clean', command)
    _git(case.child, 'add', '.gitattributes')
    _git(case.child, 'commit', '-m', 'clean filter')
    if driver == 'unspecified':
        # The wildcard filter also applies to the fixture's other tracked files.
        _git(case.child, 'add', '--renormalize', '.')
        _git(case.child, 'commit', '-m', 'apply clean filter')
    expected_blob = b'INTEGRATED\n' if driver == 'unspecified' else b'integrated\n'
    assert _git(case.child, 'show', 'HEAD:tracked.txt').stdout == expected_blob
    assert (case.child / 'tracked.txt').read_bytes() == b'integrated\n'
    assert _git(case.child, 'status', '--porcelain').stdout == b''
    _child_rejected(case, monkeypatch, 'backup-precheck', reason='conversion attributes')


@pytest.mark.parametrize('surface', ['argv', 'manifest'])
def test_child_modes_reject_noncanonical_path(tmp_path, monkeypatch, surface):
    case = _make_child_repo(tmp_path, monkeypatch)
    alias = tmp_path / 'alias'
    alias.symlink_to(case.child, target_is_directory=True)
    argv = _child_argv(case)
    if surface == 'argv':
        argv[6] = str(alias)
    else:
        data = json.loads(case.manifest.read_text())
        data['wave_worktree'] = str(alias)
        case.manifest.write_text(json.dumps(data))
    _child_rejected(case, monkeypatch, surface, 2 if surface == 'argv' else 20, argv=argv)


def test_remove_child_admin_binding_change_is_partial(tmp_path, monkeypatch):
    case = _make_child_repo(tmp_path, monkeypatch)
    original = cleanup._remove_verified_tree

    def change_binding(verified, common):
        original(verified, common)
        binding = case.admin / 'gitdir'
        backup = case.admin / 'gitdir-old'
        binding.rename(backup)
        binding.write_bytes(backup.read_bytes())
        backup.unlink()

    monkeypatch.setattr(cleanup, '_remove_verified_tree', change_binding)
    with pytest.raises(cleanup.CleanupFailure) as caught:
        cleanup.run(_child_argv(case))
    assert (caught.value.rc, caught.value.phase) == (30, 'admin-recheck')
    assert case.admin.exists()
    assert _sha(case.repo.main, 'refs/heads/author') == case.head
    assert (case.evidence / 'dirty.tar.gz').exists()
    assert not (case.evidence / 'removed.json').exists()


def test_remove_child_main_advance_during_removal_is_partial(tmp_path, monkeypatch):
    case = _make_child_repo(tmp_path, monkeypatch)
    original = cleanup._remove_verified_tree

    def advance_main(verified, common):
        original(verified, common)
        _git(case.repo.main, 'commit', '--allow-empty', '-m', 'main advanced')

    monkeypatch.setattr(cleanup, '_remove_verified_tree', advance_main)
    with pytest.raises(cleanup.CleanupFailure) as caught:
        cleanup.run(_child_argv(case))
    assert (caught.value.rc, caught.value.phase) == (30, 'admin-recheck')
    assert 'main changed since integration proof' in caught.value.reason
    assert not case.child.exists()
    assert case.admin.exists()
    assert _sha(case.repo.main, 'refs/heads/author') == case.head
    for name in ('committed.patch', 'dirty.tar.gz', 'tracked.patch', 'index.patch',
                 'status.txt', 'head-sha.txt', 'branch.txt'):
        assert (case.evidence / name).exists()
    assert not (case.evidence / 'removed.json').exists()


def test_remove_child_already_clean_with_receipt(tmp_path, monkeypatch):
    case = _make_child_repo(tmp_path, monkeypatch)
    assert cleanup.run(_child_argv(case)).outcome == 'removed'
    before = _file_snapshot(case.evidence)
    assert cleanup.run(_child_argv(case)).outcome == 'already-clean'
    assert _file_snapshot(case.evidence) == before
    assert _sha(case.repo.main, 'refs/heads/author') == case.head


@pytest.mark.parametrize('defect', [
    'unknown-key', 'duplicate-key', 'duplicate-path', 'wrong-type', 'relative-path',
    'absolute-owned', 'dot-dot-owned', 'git-owned', 'glob-owned', 'directory-owned',
])
def test_remove_child_manifest_is_closed(tmp_path, monkeypatch, defect):
    case = _make_child_repo(tmp_path, monkeypatch)
    data = json.loads(case.manifest.read_text())
    entry = data['entries'][0]
    if defect == 'unknown-key':
        entry['extra'] = True
    elif defect == 'duplicate-key':
        case.manifest.write_text(case.manifest.read_text().replace('"purpose":', '"purpose": "first", "purpose":'))
    elif defect == 'duplicate-path':
        data['entries'].append(dict(entry))
    elif defect == 'wrong-type':
        entry['purpose'] = 3
    elif defect == 'relative-path':
        entry['path'] = 'child'
    else:
        (case.child / 'directory').mkdir()
        entry['owned_paths'] = [{'absolute-owned': '/tmp/file', 'dot-dot-owned': '../file',
            'git-owned': '.git/config', 'glob-owned': '*.txt', 'directory-owned': 'directory'}[defect]]
    if defect != 'duplicate-key':
        case.manifest.write_text(json.dumps(data))
    _child_rejected(case, monkeypatch, 'manifest')


@pytest.mark.parametrize('state', ['clean', 'dirty', 'ignored', 'reflog', 'pin-mismatch', 'local-only-pin'])
def test_remove_child_checks_initialized_submodule(tmp_path, monkeypatch, state):
    case = _make_child_repo(tmp_path, monkeypatch)
    # Keep the source tip fixed while main commits its own submodule registration.
    _git(case.repo.main, 'branch', 'module-source')
    _git(case.repo.main, '-c', 'protocol.file.allow=always', 'submodule', 'add',
         '-b', 'module-source', str(case.repo.main), 'module')
    _git(case.repo.main, 'commit', '-am', 'primary module pin')
    _git(case.repo.main, '-c', 'protocol.file.allow=always', 'submodule', 'update', '--init')
    # Clone at the pin directly, without recording main's newer tip in HEAD reflog.
    _git(case.child, 'clone', '--branch', 'module-source', str(case.repo.main), 'module')
    _git(case.child, '-c', 'protocol.file.allow=always', 'submodule', 'add',
         '-b', 'module-source', str(case.repo.main), 'module')
    _git(case.child, 'submodule', 'absorbgitdirs', 'module')
    _git(case.child, 'commit', '-am', 'module pin')
    module = case.child / 'module'
    pin = _sha(module)
    assert pin == _sha(case.repo.main / 'module')
    _git(module, 'config', 'user.name', 'Cleanup Test')
    _git(module, 'config', 'user.email', 'cleanup@example.invalid')
    if state == 'dirty':
        (module / 'scratch').write_text('untracked')
    elif state == 'ignored':
        (module / 'ignored').write_text('ignored bytes')
        gitdir = Path(_git(module, 'rev-parse', '--absolute-git-dir').stdout.decode().strip())
        (gitdir / 'info' / 'exclude').write_text('ignored\n')
    elif state in {'reflog', 'pin-mismatch', 'local-only-pin'}:
        (module / 'tracked.txt').write_text('local history')
        _git(module, 'commit', '-am', 'local module commit')
        if state == 'reflog':
            _git(module, 'reset', '--hard', pin)
        elif state == 'local-only-pin':
            _git(case.child, 'add', 'module')
            _git(case.child, 'commit', '-m', 'local-only module pin')
    if state == 'clean':
        head = _sha(case.child)
        assert cleanup.run(_child_argv(case)).outcome == 'removed'
        assert not case.child.exists() and not case.admin.exists()
        assert _sha(case.repo.main, 'refs/heads/author') == head
    else:
        _child_rejected(case, monkeypatch, 'backup-precheck')


def test_remove_child_detached_ancestry_and_empty_backup(tmp_path, monkeypatch):
    case = _make_child_repo(tmp_path, monkeypatch)
    # A fresh detached child has only main-reachable HEAD reflog history.
    detached = tmp_path / 'detached'
    _git(case.repo.main, 'worktree', 'add', '--detach', str(detached), 'main')
    data = json.loads(case.manifest.read_text())
    data['entries'] = [{'path': str(detached), 'purpose': 'container', 'branch': None, 'owned_paths': []}]
    case.manifest.write_text(json.dumps(data))
    argv = _child_argv(case)
    argv[6] = str(detached)
    assert cleanup.run(argv).outcome == 'removed'
    assert (case.evidence / 'branch.txt').read_text() == 'detached\n'
    for name in ('status.txt', 'tracked.patch', 'index.patch', 'committed.patch'):
        assert (case.evidence / name).read_bytes() == b''
    with tarfile.open(case.evidence / 'dirty.tar.gz') as archive:
        assert archive.getnames() == []


def _argv(repo: Repo, **overrides: str) -> list[str]:
    values = {
        "main": os.fspath(repo.main),
        "wave": os.fspath(repo.wave),
        "branch": repo.branch,
        "tip": repo.tip,
    }
    values.update(overrides)
    argv = [
        "--main-worktree", values["main"],
        "--wave-worktree", values["wave"],
        "--wave-branch", values["branch"],
        "--tested-wave-tip-sha", values["tip"],
    ]
    landing_tip = values.get("landing_tip")
    if landing_tip is not None:
        argv.extend(("--landing-wave-tip-sha", landing_tip))
    return argv


def _run(repo: Repo, capsys, **overrides: str) -> tuple[int, str, str]:
    rc = cleanup.main(_argv(repo, **overrides))
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


def _unoccupied_payload(path: Path) -> dict[str, object]:
    return {
        "status": "unoccupied",
        "occupants": [],
        "issues": [],
        "scanned": 1,
        "same_uid_cwd_unreachable": [],
        "unreachable": {"cwd_permission": 0},
        "worktree": os.fspath(path),
    }


def _indeterminate_payload(path: Path, issues: object) -> dict[str, object]:
    payload = _unoccupied_payload(path)
    payload.update({"status": "indeterminate", "issues": issues})
    return payload


def _stub_unoccupied(monkeypatch) -> None:
    monkeypatch.setattr(
        cleanup,
        "_occupancy_payload",
        lambda path: (cleanup.occupancy.UNOCCUPIED_RC, _unoccupied_payload(path)),
    )


def _assert_success_output(
    result: tuple[int, str, str],
    outcome: str,
    *,
    occupancy_phases: tuple[str, ...],
) -> None:
    rc, stdout, stderr = result
    assert (rc, stdout) == (0, f"{outcome}\n")
    lines = stderr.splitlines()
    assert len(lines) == len(occupancy_phases)
    for line, phase in zip(lines, occupancy_phases, strict=True):
        assert line.startswith(
            f"dev-wave-cleanup: diagnostic=occupancy phase={phase} cwd_permission="
        )
        assert " same_uid_cwd_unreachable=" in line


def _record_bytes(repo: Repo) -> bytes:
    return _git(repo.main, "worktree", "list", "--porcelain").stdout


def _snapshot(repo: Repo) -> tuple[bool, bytes, str | None, str | None, bytes | None]:
    exists = repo.wave.is_dir()
    branch_result = _git(repo.main, "rev-parse", "--verify", f"refs/heads/{repo.branch}", check=False)
    branch = branch_result.stdout.decode().strip() if branch_result.returncode == 0 else None
    head = _sha(repo.wave) if exists else None
    gitfile = (repo.wave / ".git").read_bytes() if exists else None
    return exists, _record_bytes(repo), branch, head, gitfile


def _assert_preserved(repo: Repo, before) -> None:
    assert _snapshot(repo) == before


def _assert_removed(repo: Repo) -> None:
    assert not os.path.lexists(repo.wave)
    assert os.fsencode(repo.wave) not in _record_bytes(repo)
    assert _git(
        repo.main,
        "rev-parse", "--verify", f"refs/heads/{repo.branch}",
        check=False,
    ).returncode != 0


def _prepare_state(repo: Repo, state: str) -> None:
    if state in {"b", "c", "d", "e"}:
        _git(repo.wave, "checkout", "--detach")
    if state in {"c", "d", "e"}:
        shutil.rmtree(repo.wave)
    if state in {"d", "e"}:
        _git(repo.main, "worktree", "prune", "--expire=now")
    if state == "e":
        _git(repo.main, "branch", "-d", "--", repo.branch)


@pytest.mark.parametrize("locked", (False, True), ids=("unlocked", "locked"))
def test_landed_attached_worktree_is_removed(tmp_path, monkeypatch, capsys, locked):
    repo = _make_repo(tmp_path, monkeypatch, locked=locked)
    _stub_unoccupied(monkeypatch)
    _assert_success_output(
        _run(repo, capsys),
        "removed",
        occupancy_phases=("preflight", "recheck"),
    )
    _assert_removed(repo)


@pytest.mark.parametrize(
    "pass_optional_tip",
    (False, True),
    ids=("derived", "asserted"),
)
def test_forward_merged_landing_tip_is_used_for_cleanup(
    tmp_path,
    monkeypatch,
    capsys,
    pass_optional_tip,
):
    repo = _make_repo(tmp_path, monkeypatch, landed=False)
    _stub_unoccupied(monkeypatch)
    tested_tip = repo.tip
    (repo.main / "main-after.txt").write_text("main advance\n", encoding="utf-8")
    _git(repo.main, "add", "main-after.txt")
    _git(repo.main, "commit", "-m", "main advance")
    incorporated_main = _sha(repo.main)
    _git(repo.wave, "merge", "--no-ff", "--no-edit", incorporated_main)
    landing_tip = _sha(repo.wave)
    assert landing_tip != tested_tip
    _git(repo.main, "merge", "--ff-only", landing_tip)

    overrides = {"landing_tip": landing_tip} if pass_optional_tip else {}
    _assert_success_output(
        _run(repo, capsys, **overrides),
        "removed",
        occupancy_phases=("preflight", "recheck"),
    )
    _assert_removed(repo)


def test_optional_landing_tip_must_match_derived_wave_head(
    tmp_path,
    monkeypatch,
    capsys,
):
    repo = _make_repo(tmp_path, monkeypatch)
    _assert_rejected_preserving(repo, capsys, landing_tip=repo.base)


@pytest.mark.parametrize("state", ("a", "b", "c", "d", "e"))
def test_reentry_states_run_only_remaining_cleanup(tmp_path, monkeypatch, capsys, state):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)
    _prepare_state(repo, state)
    calls: list[tuple[str, ...]] = []
    original = cleanup._git

    def spy(cwd, *args):
        calls.append(tuple(args))
        return original(cwd, *args)

    monkeypatch.setattr(cleanup, "_git", spy)
    expected = "already-clean\n" if state == "e" else "removed\n"
    occupancy_phases = ("preflight", "recheck") if state in {"a", "b"} else ()
    _assert_success_output(
        _run(repo, capsys),
        expected.rstrip("\n"),
        occupancy_phases=occupancy_phases,
    )
    _assert_removed(repo)
    assert (("checkout", "--detach") in calls) is (state == "a")
    assert not any(call[:2] == ("worktree", "prune") for call in calls)
    assert not (repo.main / ".git" / "worktrees" / "wave").exists()
    assert any(call[:2] == ("branch", "-d") for call in calls) is (state != "e")


def test_rejects_stale_record_bound_to_a_different_branch(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch)
    admin = Path(
        (repo.wave / ".git").read_text(encoding="utf-8").removeprefix("gitdir: ").strip()
    )
    _git(repo.main, "branch", "other", repo.tip)
    (admin / "HEAD").write_text("ref: refs/heads/other\n", encoding="utf-8")
    shutil.rmtree(repo.wave)
    _assert_rejected_preserving(repo, capsys)


@pytest.mark.parametrize("appeared", ("path", "record", "ref"))
def test_already_clean_rechecks_each_absence_before_success(
    tmp_path, monkeypatch, capsys, appeared,
):
    repo = _make_repo(tmp_path, monkeypatch)
    _prepare_state(repo, "e")
    if appeared == "path":
        original_lexists = cleanup.os.path.lexists
        target_calls = 0

        def path_appears(path):
            nonlocal target_calls
            if Path(path) == repo.wave:
                target_calls += 1
                if target_calls == 2:
                    return True
            return original_lexists(path)

        monkeypatch.setattr(cleanup.os.path, "lexists", path_appears)
    elif appeared == "record":
        original_records = cleanup._worktree_records
        record_calls = 0

        def record_appears(main):
            nonlocal record_calls
            records = original_records(main)
            record_calls += 1
            if record_calls == 2:
                records.append(cleanup.WorktreeRecord(
                    os.fsencode(repo.wave), repo.wave, repo.tip, None, True, False, True,
                ))
            return records

        monkeypatch.setattr(cleanup, "_worktree_records", record_appears)
    elif appeared == "ref":
        original_resolve = cleanup._resolve_commit
        ref_calls = 0

        def ref_appears(main, expression):
            nonlocal ref_calls
            if expression == f"refs/heads/{repo.branch}^{{commit}}":
                ref_calls += 1
                if ref_calls == 2:
                    return repo.tip
            return original_resolve(main, expression)

        monkeypatch.setattr(cleanup, "_resolve_commit", ref_appears)
    else:  # pragma: no cover - parameter list is the registry
        raise AssertionError(appeared)

    rc, stdout, stderr = _run(repo, capsys)
    assert (rc, stdout) == (20, "")
    assert "status=rejected phase=preflight" in stderr


def _assert_rejected_preserving(repo: Repo, capsys, *, expected_rc=20, **overrides):
    before = _snapshot(repo)
    rc, stdout, stderr = _run(repo, capsys, **overrides)
    assert rc == expected_rc
    assert stdout == ""
    assert stderr.startswith("dev-wave-cleanup: status=rejected phase=")
    assert stderr.count("\n") == 1
    assert len(stderr.encode("utf-8")) < 600
    _assert_preserved(repo, before)


def test_occupancy_payload_maps_invalid_target_status(tmp_path):
    rc, payload = cleanup._occupancy_payload(tmp_path / "missing-worktree")

    assert rc == cleanup.occupancy.INDETERMINATE_RC
    assert payload["status"] == "invalid-target"
    assert payload["issues"][0]["source"] == "worktree"


def test_assert_unoccupied_accepts_empty_same_uid_cwd_unreachable(
    tmp_path,
    monkeypatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    monkeypatch.setattr(
        cleanup,
        "_occupancy_payload",
        lambda path: (
            cleanup.occupancy.UNOCCUPIED_RC,
            _unoccupied_payload(path),
        ),
    )

    diagnostics = cleanup._assert_unoccupied(target)

    assert type(diagnostics.same_uid_cwd_unreachable) is list
    assert diagnostics.same_uid_cwd_unreachable == []


def test_assert_unoccupied_accepts_real_empty_proc_scan_payload(
    tmp_path,
    monkeypatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    proc_root = tmp_path / "proc"
    proc_root.mkdir()
    original_scan = cleanup.occupancy.scan_worktree_occupancy

    def scan_empty_proc(path, **kwargs):
        return original_scan(
            path,
            proc_root=proc_root,
            parent_pid=-1,
            **kwargs,
        )

    monkeypatch.setattr(
        cleanup.occupancy,
        "scan_worktree_occupancy",
        scan_empty_proc,
    )

    diagnostics = cleanup._assert_unoccupied(target)

    assert type(diagnostics.same_uid_cwd_unreachable) is list
    assert diagnostics.same_uid_cwd_unreachable == []


def test_assert_unoccupied_requires_same_uid_cwd_unreachable_field(
    tmp_path,
    monkeypatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    payload = _unoccupied_payload(target)
    del payload["same_uid_cwd_unreachable"]
    monkeypatch.setattr(
        cleanup,
        "_occupancy_payload",
        lambda path: (cleanup.occupancy.UNOCCUPIED_RC, payload),
    )

    with pytest.raises(cleanup.CleanupFailure) as caught:
        cleanup._assert_unoccupied(target)

    assert caught.value.rc == cleanup.RC_OCCUPANCY_INDETERMINATE
    assert caught.value.reason == (
        "occupancy payload lacks required fields; attempts=1 retry_count=0"
    )


def test_rejects_non_ancestor_without_mutation(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch, landed=False, locked=True)
    _assert_rejected_preserving(repo, capsys)


def test_preflight_ancestry_gate_rejects_before_any_removal(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, landed=False, locked=True)
    # Isolate the direct branch-tip gate from the separate reflog ancestry gate.
    monkeypatch.setattr(cleanup, "_assert_reflog_commits_reachable", lambda *args: None)
    before = _snapshot(repo)
    tracked = repo.wave / "tracked.txt"
    tracked_before = tracked.read_bytes()
    gitfile_before = (repo.wave / ".git").read_bytes()
    administrative = Path(
        gitfile_before.decode("utf-8").removeprefix("gitdir: ").strip()
    )
    administrative_head_before = (administrative / "HEAD").read_bytes()
    lock_before = (administrative / "locked").read_bytes()

    rc, stdout, stderr = _run(repo, capsys)

    assert (rc, stdout) == (20, "")
    assert stderr.startswith("dev-wave-cleanup: status=rejected phase=preflight ")
    assert "status=partial" not in stderr
    assert repo.wave.is_dir()
    assert tracked.is_file()
    assert tracked.read_bytes() == tracked_before
    assert (repo.wave / ".git").read_bytes() == gitfile_before
    assert administrative.is_dir()
    assert (administrative / "HEAD").read_bytes() == administrative_head_before
    assert (administrative / "locked").read_bytes() == lock_before
    _assert_preserved(repo, before)


@pytest.mark.parametrize("kind", ("tracked", "untracked"))
def test_rejects_dirty_worktree_without_mutation(tmp_path, monkeypatch, capsys, kind):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    if kind == "tracked":
        (repo.wave / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    else:
        (repo.wave / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    _assert_rejected_preserving(repo, capsys)


@pytest.mark.parametrize(
    ("signal", "expected"),
    (
        ("rc-occupied", 21),
        ("status-occupied", 21),
        ("occupants", 21),
        ("indeterminate-occupants", 21),
        ("rc-indeterminate", 22),
        ("issues", 22),
        ("mixed-issues", 22),
    ),
)
def test_rejects_occupancy_payload_failures_without_mutation(
    tmp_path, monkeypatch, capsys, signal, expected,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    rc = 0
    payload = {
        "status": "unoccupied",
        "occupants": [],
        "issues": [],
        "scanned": 1,
        "same_uid_cwd_unreachable": [],
        "unreachable": {"cwd_permission": 0},
        "worktree": os.fspath(repo.wave),
    }
    if signal == "rc-occupied":
        rc = 1
    elif signal == "status-occupied":
        payload["status"] = "occupied"
    elif signal == "occupants":
        payload["occupants"] = [{"pid": 1}]
    elif signal == "indeterminate-occupants":
        rc = 2
        payload["status"] = "indeterminate"
        payload["occupants"] = [{"pid": 1}]
        payload["issues"] = [{"error": "missing", "pid": 2, "source": "cwd"}]
    elif signal == "rc-indeterminate":
        rc = 2
    elif signal == "issues":
        payload["issues"] = [{"error": "x"}]
    elif signal == "mixed-issues":
        rc = 2
        payload["status"] = "indeterminate"
        payload["issues"] = [
            {"error": "missing", "pid": 2, "source": "cwd"},
            {"error": "permission", "pid": 3, "source": "cmdline"},
        ]
    else:  # pragma: no cover - parameter list is the registry
        raise AssertionError(signal)
    calls = 0

    def occupancy_result(path):
        nonlocal calls
        calls += 1
        return rc, payload

    monkeypatch.setattr(cleanup, "_occupancy_payload", occupancy_result)
    _assert_rejected_preserving(repo, capsys, expected_rc=expected)
    assert calls == (3 if signal == "mixed-issues" else 1)


def test_retries_disappeared_pid_issue_then_removes(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    transient = _unoccupied_payload(repo.wave)
    transient.update({
        "status": "indeterminate",
        "issues": [{"error": "missing", "pid": 1234, "source": "cwd"}],
    })
    calls = 0

    def occupancy_sequence(path):
        nonlocal calls
        calls += 1
        if calls == 1:
            return cleanup.occupancy.INDETERMINATE_RC, transient
        return cleanup.occupancy.UNOCCUPIED_RC, _unoccupied_payload(path)

    monkeypatch.setattr(cleanup, "_occupancy_payload", occupancy_sequence)

    result = _run(repo, capsys)

    _assert_success_output(
        result,
        "removed",
        occupancy_phases=("preflight", "recheck"),
    )
    assert calls == 3
    diagnostic_lines = result[2].splitlines()
    assert "phase=preflight " in diagnostic_lines[0]
    assert "retry_count=1" in diagnostic_lines[0]
    assert "phase=recheck " in diagnostic_lines[1]
    assert "retry_count=0" in diagnostic_lines[1]
    _assert_removed(repo)


def test_retries_transient_nonmissing_issue_then_removes(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    transient = _indeterminate_payload(
        repo.wave,
        [{"error": "os-error", "pid": 2345, "source": "stat"}],
    )
    calls = 0

    def occupancy_sequence(path):
        nonlocal calls
        calls += 1
        if calls == 1:
            return cleanup.occupancy.INDETERMINATE_RC, transient
        return cleanup.occupancy.UNOCCUPIED_RC, _unoccupied_payload(path)

    monkeypatch.setattr(cleanup, "_occupancy_payload", occupancy_sequence)

    result = _run(repo, capsys)

    _assert_success_output(
        result,
        "removed",
        occupancy_phases=("preflight", "recheck"),
    )
    assert calls == 3
    diagnostic_lines = result[2].splitlines()
    assert "phase=preflight " in diagnostic_lines[0]
    assert "retry_count=1" in diagnostic_lines[0]
    assert "phase=recheck " in diagnostic_lines[1]
    assert "retry_count=0" in diagnostic_lines[1]
    _assert_removed(repo)


def test_three_nonmissing_issue_scans_remain_indeterminate(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    persistent = _indeterminate_payload(
        repo.wave,
        [{"error": "pid-reused", "pid": 3456, "source": "stat"}],
    )
    calls = 0

    def always_indeterminate(path):
        nonlocal calls
        calls += 1
        return cleanup.occupancy.INDETERMINATE_RC, persistent

    monkeypatch.setattr(cleanup, "_occupancy_payload", always_indeterminate)
    before = _snapshot(repo)

    rc, stdout, stderr = _run(repo, capsys)

    assert (rc, stdout) == (22, "")
    assert calls == 3
    assert "status=rejected phase=occupancy" in stderr
    assert "attempts=3 retry_count=2" in stderr
    _assert_preserved(repo, before)


def test_three_disappeared_pid_issue_scans_remain_indeterminate(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    transient = _unoccupied_payload(repo.wave)
    transient.update({
        "status": "indeterminate",
        "issues": [{"error": "missing", "pid": 1234, "source": "cmdline"}],
    })
    calls = 0

    def always_has_issue(path):
        nonlocal calls
        calls += 1
        rc = (
            cleanup.occupancy.INDETERMINATE_RC
            if calls < cleanup._OCCUPANCY_MAX_SCANS
            else cleanup.occupancy.UNOCCUPIED_RC
        )
        if calls == cleanup._OCCUPANCY_MAX_SCANS:
            transient["status"] = "unoccupied"
        return rc, transient

    monkeypatch.setattr(cleanup, "_occupancy_payload", always_has_issue)
    before = _snapshot(repo)

    rc, stdout, stderr = _run(repo, capsys)

    assert (rc, stdout) == (22, "")
    assert calls == 3
    assert "status=rejected phase=occupancy" in stderr
    assert "attempts=3 retry_count=2" in stderr
    _assert_preserved(repo, before)


def test_indeterminate_issue_summary_is_json_and_includes_fields(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    issue = {"error": "os/error;]", "source": "cwd;]", "pid": 4567}
    payload = _indeterminate_payload(repo.wave, [issue])
    monkeypatch.setattr(
        cleanup,
        "_occupancy_payload",
        lambda path: (cleanup.occupancy.INDETERMINATE_RC, payload),
    )
    before = _snapshot(repo)

    rc, stdout, stderr = _run(repo, capsys)

    assert (rc, stdout) == (22, "")
    assert "issues_total=1" in stderr
    encoded_items = stderr.partition(" issues=")[2].partition(" issues_omitted=")[0]
    assert json.loads(encoded_items) == [{
        "error": "os/error;]",
        "source": "cwd;]",
        "pid": "4567",
    }]
    assert "issues_omitted=0" in stderr
    assert stderr.count("\n") == 1
    assert len(stderr.encode("utf-8")) < 600
    _assert_preserved(repo, before)


def test_indeterminate_issue_summary_limits_items_and_reports_omitted(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    issues = [
        {"error": "os-error", "source": "cwd", "pid": pid}
        for pid in (5101, 5102, 5103, 5104)
    ]
    payload = _indeterminate_payload(repo.wave, issues)
    monkeypatch.setattr(
        cleanup,
        "_occupancy_payload",
        lambda path: (cleanup.occupancy.INDETERMINATE_RC, payload),
    )

    rc, stdout, stderr = _run(repo, capsys)

    assert (rc, stdout) == (22, "")
    assert "issues_total=4" in stderr
    encoded_items = stderr.partition(" issues=")[2].partition(" issues_omitted=")[0]
    summarized = json.loads(encoded_items)
    assert [item["pid"] for item in summarized] == ["5101", "5102", "5103"]
    assert "5104" not in stderr
    assert "issues_omitted=1" in stderr
    assert stderr.count("\n") == 1
    assert len(stderr.encode("utf-8")) < 600


def test_indeterminate_issue_summary_limits_each_field_to_24_utf8_bytes(
    tmp_path, monkeypatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    payload = _indeterminate_payload(
        target,
        [{"error": "界" * 20, "source": "s" * 40, "pid": "9" * 40}],
    )
    monkeypatch.setattr(
        cleanup,
        "_occupancy_payload",
        lambda path: (cleanup.occupancy.INDETERMINATE_RC, payload),
    )

    with pytest.raises(cleanup.CleanupFailure) as caught:
        cleanup._assert_unoccupied(target)

    encoded_items = caught.value.reason.partition(" issues=")[2].partition(
        " issues_omitted=",
    )[0]
    item = json.loads(encoded_items)[0]
    assert item == {"error": "界" * 8, "source": "s" * 24, "pid": "9" * 24}
    assert all(len(value.encode("utf-8")) <= 24 for value in item.values())


def test_indeterminate_issue_summary_falls_back_to_readable_counts(
    tmp_path, monkeypatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    issues = [
        {"error": "\x01" * 24, "source": "\x01" * 24, "pid": "\x01" * 24}
        for _ in range(3)
    ]
    payload = _indeterminate_payload(target, issues)
    monkeypatch.setattr(
        cleanup,
        "_occupancy_payload",
        lambda path: (cleanup.occupancy.INDETERMINATE_RC, payload),
    )

    with pytest.raises(cleanup.CleanupFailure) as caught:
        cleanup._assert_unoccupied(target)

    reason = caught.value.reason
    summary = reason[reason.index("issues_total="):]
    assert summary == "issues_total=3 issues=[] issues_omitted=3"
    assert len(summary.encode("utf-8")) <= cleanup._OCCUPANCY_ISSUE_SUMMARY_BYTES
    assert len(reason.encode("utf-8")) <= 500
    assert cleanup._sanitize(reason) == reason


@pytest.mark.parametrize(
    "issues",
    (
        "not-a-list",
        ["not-a-dict"],
        [{"error": "os-error"}],
        [{"error": 1, "source": [], "pid": {}}],
    ),
    ids=("not-list", "not-dict", "missing-fields", "nonstr-fields"),
)
def test_malformed_indeterminate_issues_still_return_rc22(
    tmp_path, monkeypatch, capsys, issues,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    payload = _indeterminate_payload(repo.wave, issues)
    monkeypatch.setattr(
        cleanup,
        "_occupancy_payload",
        lambda path: (cleanup.occupancy.INDETERMINATE_RC, payload),
    )

    before = _snapshot(repo)
    rc, stdout, stderr = _run(repo, capsys)

    assert (rc, stdout) == (22, "")
    assert "status=rejected phase=occupancy" in stderr
    assert "issues_total=1" in stderr
    assert "unspecified" in stderr
    assert stderr.count("\n") == 1
    assert len(stderr.encode("utf-8")) < 600
    _assert_preserved(repo, before)


@pytest.mark.parametrize(
    "diagnostics",
    (
        {
            "same_uid_cwd_unreachable": [],
            "unreachable": {"cwd_permission": 2030},
        },
        {
            "same_uid_cwd_unreachable": [
                {"pid": 7, "comm": "sshd"},
                {"pid": 8, "comm": "ssh-agent"},
                {"pid": 9, "comm": "(sd-pam)"},
                {"pid": 10, "comm": "systemd"},
            ],
            "unreachable": {"cwd_permission": 2030},
        },
        {
            "same_uid_cwd_unreachable": [],
            "unreachable": {"cwd_permission": 0, "cwd_deleted": 2},
        },
    ),
    ids=("cwd-permission", "same-uid-cwd", "cwd-deleted"),
)
def test_accepts_nonblocking_occupancy_diagnostics(
    tmp_path, monkeypatch, capsys, diagnostics,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    payload = {
        "status": "unoccupied",
        "occupants": [],
        "issues": [],
        "scanned": 2035,
        "worktree": os.fspath(repo.wave),
        **diagnostics,
    }
    monkeypatch.setattr(cleanup, "_occupancy_payload", lambda path: (0, payload))

    result = _run(repo, capsys)
    _assert_success_output(
        result,
        "removed",
        occupancy_phases=("preflight", "recheck"),
    )
    assert result[2].count(
        f"cwd_permission={diagnostics['unreachable']['cwd_permission']}"
    ) == 2
    assert result[2].count(
        f"cwd_deleted={diagnostics['unreachable'].get('cwd_deleted', 0)}"
    ) == 2
    _assert_removed(repo)


def test_accepts_arbitrary_same_uid_unreachable_process_with_diagnostics(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    payload = {
        "status": "unoccupied",
        "occupants": [],
        "issues": [],
        "scanned": 1,
        "same_uid_cwd_unreachable": [{"pid": 7, "comm": "nqs_shpd"}],
        "unreachable": {"cwd_permission": 2030},
        "worktree": os.fspath(repo.wave),
    }
    monkeypatch.setattr(cleanup, "_occupancy_payload", lambda path: (0, payload))
    result = _run(repo, capsys)
    _assert_success_output(
        result,
        "removed",
        occupancy_phases=("preflight", "recheck"),
    )
    assert result[2].count("nqs_shpd") == 2
    assert result[2].count('"pid": 7') == 2
    _assert_removed(repo)


def test_real_occupancy_scan_rejects_live_process_cwd(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    process = subprocess.Popen(
        [sys.executable, "-c", "import sys; sys.stdin.buffer.read(1)"],
        cwd=repo.wave,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        assert process.poll() is None
        _assert_rejected_preserving(repo, capsys, expected_rc=21)
    finally:
        assert process.stdin is not None
        process.stdin.write(b"x")
        process.stdin.close()
        assert process.wait(timeout=10) == 0


def test_rejects_cwd_inside_target_without_mutation(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    before = _snapshot(repo)
    monkeypatch.chdir(repo.wave)
    monkeypatch.setenv("PWD", os.fspath(repo.wave))
    rc, stdout, stderr = _run(repo, capsys)
    assert (rc, stdout) == (20, "")
    assert "status=rejected" in stderr
    _assert_preserved(repo, before)


def test_rejects_primary_as_wave_without_mutation(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    _assert_rejected_preserving(repo, capsys, wave=os.fspath(repo.main))


def test_rejects_wave_from_different_common_dir(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path / "one", monkeypatch, locked=True)
    other = _make_repo(tmp_path / "two", monkeypatch)
    monkeypatch.setattr(cleanup, "_REPO", other.main)
    before = _snapshot(repo)
    rc = cleanup.main(_argv(repo, main=os.fspath(other.main)))
    captured = capsys.readouterr()
    assert rc == 20 and captured.out == "" and "status=rejected" in captured.err
    _assert_preserved(repo, before)


def test_rejects_branch_tip_mismatch_without_mutation(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    tree = _sha(repo.main, f"{repo.base}^{{tree}}")
    unrelated_tested_tip = _git(
        repo.main,
        "commit-tree",
        tree,
        "-p",
        repo.base,
        "-m",
        "unrelated tested tip",
    ).stdout.decode().strip()
    _assert_rejected_preserving(repo, capsys, tip=unrelated_tested_tip)


@pytest.mark.parametrize("spelling", ("symlink", "dotdot", "trailing"))
def test_rejects_unsafe_raw_path_spellings(tmp_path, monkeypatch, capsys, spelling):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    if spelling == "symlink":
        link = tmp_path / "wave-link"
        link.symlink_to(repo.wave, target_is_directory=True)
        raw = os.fspath(link)
    elif spelling == "dotdot":
        raw = os.fspath(repo.wave.parent / "unused" / ".." / repo.wave.name)
    else:
        raw = os.fspath(repo.wave) + "/"
    _assert_rejected_preserving(repo, capsys, expected_rc=2, wave=raw)


def test_rejects_malformed_porcelain_without_mutation(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    original = cleanup._git

    def malformed(cwd, *args):
        if args == ("worktree", "list", "--porcelain"):
            raw = (
                b"worktree " + os.fsencode(repo.main) + b"\n"
                b"HEAD " + repo.tip.encode() + b"\n"
                b"mystery x\n\n"
            )
            return subprocess.CompletedProcess(args, 0, raw, b"")
        return original(cwd, *args)

    monkeypatch.setattr(cleanup, "_git", malformed)
    _assert_rejected_preserving(repo, capsys)


def test_rejects_porcelain_record_with_newline_in_target_path_without_mutation(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    original = cleanup._git

    def newline_path(cwd, *args):
        result = original(cwd, *args)
        if args == ("worktree", "list", "--porcelain"):
            result = subprocess.CompletedProcess(
                result.args,
                result.returncode,
                result.stdout.replace(
                    b"worktree " + os.fsencode(repo.wave) + b"\n",
                    b"worktree " + os.fsencode(repo.wave) + b"\ncontinued\n",
                ),
                result.stderr,
            )
        return result

    monkeypatch.setattr(cleanup, "_git", newline_path)
    _assert_rejected_preserving(repo, capsys)


def test_rejects_active_fold_state_without_mutation(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    common = Path(_git(repo.main, "rev-parse", "--git-common-dir").stdout.decode().strip())
    if not common.is_absolute():
        common = repo.main / common
    (common / "izanagi-spool-fold-state.json").write_text("{}\n", encoding="utf-8")
    _assert_rejected_preserving(repo, capsys)


def test_rejects_reflog_only_unreachable_commit_without_mutation(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    _git(repo.main, "worktree", "unlock", os.fspath(repo.wave))
    admin = Path(
        (repo.wave / ".git").read_text(encoding="utf-8").removeprefix("gitdir: ").strip()
    )
    _git(repo.wave, "checkout", "--detach")
    (repo.wave / "tracked.txt").write_text("unreachable\n", encoding="utf-8")
    _git(repo.wave, "commit", "-am", "unreachable reflog entry")
    unreachable = _sha(repo.wave)
    _git(repo.wave, "reset", "--hard", repo.tip)
    branch_reflog = _git(
        repo.main, "rev-list", "--walk-reflogs", f"refs/heads/{repo.branch}",
    ).stdout.decode().splitlines()
    assert unreachable not in branch_reflog
    assert unreachable.encode() in (admin / "logs" / "HEAD").read_bytes()
    _git(repo.main, "worktree", "lock", "--reason", "synthetic", os.fspath(repo.wave))
    _assert_rejected_preserving(repo, capsys)


@pytest.mark.parametrize("mode", ("empty", "fatal"))
def test_rejects_uninspectable_branch_reflog_without_mutation(
    tmp_path, monkeypatch, capsys, mode,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    original = cleanup._git

    def uninspectable(cwd, *args):
        if args == ("rev-list", "--walk-reflogs", f"refs/heads/{repo.branch}"):
            return subprocess.CompletedProcess(
                args,
                0 if mode == "empty" else 128,
                b"",
                b"" if mode == "empty" else b"fatal: synthetic missing reflog\n",
            )
        return original(cwd, *args)

    monkeypatch.setattr(cleanup, "_git", uninspectable)
    _assert_rejected_preserving(repo, capsys)


@pytest.mark.parametrize("stale", (False, True), ids=("live", "stale"))
def test_cleanup_preserves_foreign_stale_admin(tmp_path, monkeypatch, capsys, stale):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)
    other = repo.wave.parent / "other"
    _git(repo.main, "worktree", "add", "-b", "other", os.fspath(other))
    admin = repo.main / ".git" / "worktrees" / "other"
    if stale:
        shutil.rmtree(other)
    before = _admin_tree_state(admin)
    _assert_success_output(_run(repo, capsys), "removed",
                           occupancy_phases=("preflight", "recheck"))
    _assert_removed(repo)
    assert other.is_dir() is (not stale)
    assert _admin_tree_state(admin) == before
    assert _sha(repo.main, "refs/heads/other") == repo.tip


def _admin_tree_state(path):
    return {str(p.relative_to(path)): (p.lstat().st_dev, p.lstat().st_ino,
                                      p.read_bytes() if p.is_file() else None)
            for p in [path, *path.rglob("*")]}


def _add_shared_admin_objects(repo, tmp_path):
    admin = repo.main / ".git" / "worktrees" / "wave"
    for relative in ("modules/sub", "modules/sub/modules/nested"):
        directory = admin / relative
        directory.mkdir(parents=True)
        for name, raw in (("HEAD", b"ref: refs/heads/main\n"), ("config", b"[core]\n")):
            path = directory / name
            path.write_bytes(raw)
            assert path.stat().st_nlink == 1
    objects = (
        ("modules/sub/objects/ab/" + "1" * 38, b"loose object\n"),
        ("modules/sub/objects/pack/pack-" + "2" * 40 + ".pack", b"pack object\n"),
        ("modules/sub/objects/pack/pack-" + "2" * 40 + ".idx", b"pack index\n"),
        ("modules/sub/modules/nested/objects/cd/" + "3" * 38, b"nested object\n"),
    )
    aliases = []
    for index, (relative, raw) in enumerate(objects):
        path = admin / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        alias = tmp_path / f"object-alias-{index}"
        os.link(path, alias)
        assert path.stat().st_nlink == alias.stat().st_nlink == 2
        aliases.append((alias, raw))
    return aliases


def test_admin_shared_objects_are_removed(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)
    aliases = _add_shared_admin_objects(repo, tmp_path)
    _assert_success_output(
        _run(repo, capsys), "removed", occupancy_phases=("preflight", "recheck"),
    )
    _assert_removed(repo)
    assert not (repo.main / ".git" / "worktrees" / "wave").exists()
    for alias, raw in aliases:
        assert alias.read_bytes() == raw
        assert alias.stat().st_nlink == 1


@pytest.mark.parametrize(
    "target",
    ["gitdir", "submodule-config", "ref-named-objects", "submodule-named-objects",
     "ref-shaped-object", "reflog-shaped-object"],
    ids=["gitdir", "submodule-config", "ref-named-objects", "submodule-named-objects",
         "ref-shaped-object", "reflog-shaped-object"],
)
def test_admin_nonobject_hardlink_is_rejected(tmp_path, monkeypatch, capsys, target):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)
    # Keep git status's optional index refresh out of the inode comparison.
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "0")
    admin = repo.main / ".git" / "worktrees" / "wave"
    if target == "gitdir":
        path = admin / "gitdir"
    elif target == "submodule-config":
        _add_shared_admin_objects(repo, tmp_path)
        path = admin / "modules" / "sub" / "config"
    elif target == "ref-named-objects":
        path = admin / "modules" / "sub" / "refs" / "objects" / "topic"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"a" * 40 + b"\n")
    elif target == "ref-shaped-object":
        path = admin / "modules/sub/refs/heads/objects/ab" / ("1" * 38)
        path.parent.mkdir(parents=True)
        path.write_bytes(b"a" * 40 + b"\n")
    elif target == "reflog-shaped-object":
        path = admin / "modules/sub/logs/refs/heads/objects/ab" / ("1" * 38)
        path.parent.mkdir(parents=True)
        path.write_bytes(b"0" * 40 + b" " + b"a" * 40 + b" x <x@x> 0 +0000\tcommit: x\n")
    else:
        path = admin / "modules" / "objects" / "config"
        path.parent.mkdir(parents=True)
        (path.parent / "HEAD").write_bytes(b"ref: refs/heads/main\n")
        path.write_bytes(b"[core]\n")
    raw = path.read_bytes()
    alias = tmp_path / "registry-alias"
    os.link(path, alias)
    before = _admin_tree_state(admin)
    if target == "gitdir":
        fd = os.open(admin, os.O_RDONLY | os.O_DIRECTORY)
        try:
            with pytest.raises(ValueError, match="admin entry is not a single regular file"):
                cleanup._admin_snapshot(fd)
        finally:
            os.close(fd)
    rc, out, err = _run(repo, capsys)
    assert (rc, out) == (20, "")
    assert "admin entry is not a single regular file" in err
    assert _admin_tree_state(admin) == before
    assert _sha(repo.main, "refs/heads/wave") == repo.tip
    assert alias.read_bytes() == raw
    assert alias.stat().st_nlink == 2


@pytest.mark.parametrize("kind", ["object", "registry"])
def test_admin_read_link_race(tmp_path, monkeypatch, kind):
    path = tmp_path / "entry"
    raw = b"unchanged bytes\n"
    path.write_bytes(raw)
    metadata = path.stat()
    assert metadata.st_nlink == 1
    target = (metadata.st_dev, metadata.st_ino)
    alias = tmp_path / "alias"
    original = cleanup.os.fstat
    injected = False

    def link_after_stat(child):
        nonlocal injected
        result = original(child)
        if (result.st_dev, result.st_ino) == target and not injected:
            injected = True
            os.link(path, alias)
        return result

    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(cleanup.os, "fstat", link_after_stat)
            if kind == "object":
                assert cleanup._read_admin_file(fd, path.name, allow_shared_object=True) == raw
            else:
                with pytest.raises(ValueError, match="admin entry changed while reading"):
                    cleanup._read_admin_file(fd, path.name)
    finally:
        os.close(fd)
    assert injected
    assert path.read_bytes() == alias.read_bytes() == raw
    assert path.stat().st_nlink == alias.stat().st_nlink == 2


@pytest.mark.parametrize("removed", ("HEAD", "gitdir", "admin-directory"))
@pytest.mark.parametrize("tamper", (None, "lock", "bytes", "inode"))
def test_cleanup_partial_admin_removal_reenters(tmp_path, monkeypatch, capsys, request, removed, tamper):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)
    aliases = (_add_shared_admin_objects(repo, tmp_path)
               if removed == "gitdir" and tamper is None else [])
    other = repo.wave.parent / "other"
    _git(repo.main, "worktree", "add", "-b", "other", os.fspath(other))
    foreign = repo.main / ".git" / "worktrees" / "other"
    shutil.rmtree(other)
    before = _admin_tree_state(foreign)
    original = cleanup.os.unlink
    original_rmdir = cleanup.os.rmdir
    admin = repo.main / ".git" / "worktrees" / "wave"
    held = os.open(admin, os.O_RDONLY | os.O_DIRECTORY)
    request.addfinalizer(lambda: os.close(held))

    def die_after_unlink(name, *args, **kwargs):
        original(name, *args, **kwargs)
        fd = kwargs.get("dir_fd")
        if name == removed and fd is not None and os.fstat(fd).st_ino == admin.stat().st_ino:
            raise KeyboardInterrupt("death after admin unlink")

    def die_after_rmdir(name, *args, **kwargs):
        original_rmdir(name, *args, **kwargs)
        if removed == "admin-directory" and name == "wave" and kwargs.get("dir_fd") is not None:
            raise KeyboardInterrupt("death after admin rmdir")

    with monkeypatch.context() as patch:
        patch.setattr(cleanup.os, "unlink", die_after_unlink)
        patch.setattr(cleanup.os, "rmdir", die_after_rmdir)
        rc, out, err = _run(repo, capsys)
    assert (rc, out) == (30, "")
    assert "phase=admin-remove" in err
    assert not (admin if removed == "admin-directory" else admin / removed).exists()
    for alias, _ in aliases:
        assert alias.stat().st_nlink == 2
    assert _sha(repo.main, "refs/heads/wave") == repo.tip
    assert _admin_tree_state(foreign) == before
    if tamper is not None:
        if removed == "admin-directory":
            admin.mkdir()
        elif tamper == "lock":
            (admin / "index.lock").touch()
        elif tamper == "bytes":
            (admin / "index").write_bytes(b"changed")
        else:
            saved = tmp_path / "saved-admin"
            admin.rename(saved)
            shutil.copytree(saved, admin)
        rc, out, err = _run(repo, capsys)
        assert (rc, out) == (20, "")
        assert "phase=preflight" in err
        assert _sha(repo.main, "refs/heads/wave") == repo.tip
        assert _admin_tree_state(foreign) == before
        return
    _assert_success_output(_run(repo, capsys), "removed", occupancy_phases=())
    _assert_removed(repo)
    assert not admin.exists()
    assert _admin_tree_state(foreign) == before
    for alias, raw in aliases:
        assert alias.read_bytes() == raw
        assert alias.stat().st_nlink == 1


@pytest.mark.parametrize("change", (
    "locked", "index.lock", "HEAD.lock", "HEAD", "reflog", "backpointer",
    "commondir", "binding-inode", "admin-inode", "symlink", "wave-symlink",
))
def test_admin_removal_rechecks_real_registry(tmp_path, monkeypatch, capsys, change):
    repo = _make_repo(tmp_path, monkeypatch)
    _prepare_state(repo, "c")
    admin = repo.main / ".git" / "worktrees" / "wave"
    original = cleanup._recheck_admin
    injected = False

    def change_before_recheck(*args):
        nonlocal injected
        if not injected:
            injected = True
            if change in {"locked", "index.lock", "HEAD.lock"}:
                (admin / change).write_text("busy\n")
            elif change == "HEAD":
                (admin / "HEAD").write_text(repo.base + "\n")
            elif change == "reflog":
                tree = _sha(repo.main, "HEAD^{tree}")
                unreachable = _git(repo.main, "commit-tree", tree, "-m", "unreachable").stdout.strip()
                with (admin / "logs" / "HEAD").open("ab") as stream:
                    stream.write(repo.tip.encode() + b" " + unreachable + b" Test <test@example.invalid> 1 +0000\tchange\n")
            elif change == "backpointer":
                (admin / "gitdir").write_text(str(repo.wave.parent / "other" / ".git") + "\n")
            elif change == "commondir":
                (admin / "commondir").write_text("../../../elsewhere\n")
            elif change == "binding-inode":
                original_binding = admin / "gitdir.saved"
                (admin / "gitdir").rename(original_binding)
                (admin / "gitdir").write_bytes(original_binding.read_bytes())
            elif change == "admin-inode":
                saved = tmp_path / "saved-admin"
                admin.rename(saved)
                shutil.copytree(saved, admin)
            elif change == "symlink":
                (admin / "index").unlink()
                (admin / "index").symlink_to(repo.main / ".git" / "index")
            else:
                repo.wave.symlink_to(repo.main, target_is_directory=True)
        return original(*args)

    monkeypatch.setattr(cleanup, "_recheck_admin", change_before_recheck)
    rc, out, err = _run(repo, capsys)
    assert injected
    assert (rc, out) == (30, "")
    assert "phase=admin-recheck" in err
    assert admin.is_dir()
    assert _sha(repo.main, "refs/heads/wave") == repo.tip


@pytest.mark.parametrize("state", ("a", "b", "c"))
@pytest.mark.parametrize("change", ("bytes", "inode"))
def test_admin_baseline_rejects_index_change(tmp_path, monkeypatch, capsys, state, change):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)
    _prepare_state(repo, state)
    admin = repo.main / ".git" / "worktrees" / "wave"
    original = cleanup._recheck_admin
    changed = None

    def change_before_first_recheck(*args):
        nonlocal changed
        if changed is None:
            index = admin / "index"
            if change == "bytes":
                index.write_bytes(index.read_bytes() + b"changed")
            else:
                replacement = tmp_path / "replacement-index"
                replacement.write_bytes(index.read_bytes())
                assert replacement.stat().st_ino != index.stat().st_ino
                replacement.replace(index)
            changed = _admin_tree_state(admin)
        return original(*args)

    monkeypatch.setattr(cleanup, "_recheck_admin", change_before_first_recheck)
    rc, out, err = _run(repo, capsys)
    assert (rc, out) == (30, "")
    assert "phase=admin-recheck" in err
    assert "snapshot changed since safety check" in err
    assert changed is not None and _admin_tree_state(admin) == changed
    assert _sha(repo.main, "refs/heads/wave") == repo.tip


@pytest.mark.parametrize("point", ("write", "publish", "linked"))
def test_unpublished_admin_journal_reenters(tmp_path, monkeypatch, capsys, point):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)
    aliases = _add_shared_admin_objects(repo, tmp_path) if point == "linked" else []
    common = repo.main / ".git"
    admin = common / "worktrees" / "wave"
    final = common / cleanup._journal_name(repo.wave)
    original_open = cleanup.os.open
    original_unlink = cleanup.os.unlink

    def die_after_link(name, *args, **kwargs):
        if str(name).startswith(final.name + ".tmp-"):
            assert (common / name).samefile(final)
            assert final.stat().st_nlink == 2
            raise KeyboardInterrupt("death after journal link")
        return original_unlink(name, *args, **kwargs)

    def die_after_create(name, *args, **kwargs):
        fd = original_open(name, *args, **kwargs)
        if str(name).startswith(final.name + ".tmp-"):
            os.close(fd)
            raise KeyboardInterrupt("death before journal write")
        return fd

    def die_before_publish(fd, temporary, name):
        assert not final.exists()
        data = json.loads((common / temporary).read_bytes())
        index = data["snapshot"]["index"][2]
        assert set(index) == {"length", "sha256"}
        assert index == cleanup._admin_content((admin / "index").read_bytes())
        raise KeyboardInterrupt("death before journal publish")

    with monkeypatch.context() as patch:
        if point == "write":
            patch.setattr(cleanup.os, "open", die_after_create)
        elif point == "linked":
            patch.setattr(cleanup.os, "unlink", die_after_link)
        else:
            patch.setattr(cleanup, "_rename_journal", die_before_publish)
        rc, out, err = _run(repo, capsys)
    assert (rc, out) == (30, "")
    assert "phase=admin-remove" in err
    if point == "linked":
        assert final.exists()
        assert final.stat().st_nlink == 2
        for alias, _ in aliases:
            assert alias.stat().st_nlink == 2
    else:
        assert not final.exists()
    remnants = list(common.glob(final.name + ".tmp-*"))
    assert remnants
    assert admin.is_dir()
    assert _sha(repo.main, "refs/heads/wave") == repo.tip
    _assert_success_output(_run(repo, capsys), "removed", occupancy_phases=())
    _assert_removed(repo)
    if point == "linked":
        assert not final.exists()
        assert all(not path.exists() for path in remnants)
    for alias, raw in aliases:
        assert alias.read_bytes() == raw
        assert alias.stat().st_nlink == 1


def test_admin_journal_unrelated_temporary_does_not_allow_hardlink(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch)
    _prepare_state(repo, "c")
    common = repo.main / ".git"
    admin = common / "worktrees" / "wave"
    final = common / cleanup._journal_name(repo.wave)
    final.touch(mode=0o600)
    final.write_bytes(b"{}")
    alias = common / "unrelated-hardlink"
    os.link(final, alias)
    temporary = common / (final.name + ".tmp-unpublished")
    temporary.write_bytes(final.read_bytes())
    assert not temporary.samefile(final)
    before = _admin_tree_state(admin)
    for _ in range(2):
        rc, out, err = _run(repo, capsys)
        assert (rc, out) == (20, "")
        assert "admin entry is not a single regular file" in err
        assert final.stat().st_nlink == 2
        assert alias.samefile(final)
        assert temporary.read_bytes() == b"{}"
        assert _admin_tree_state(admin) == before
        assert _sha(repo.main, "refs/heads/wave") == repo.tip


def test_incomplete_final_admin_journal_rejected(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch)
    _prepare_state(repo, "c")
    admin = repo.main / ".git" / "worktrees" / "wave"
    journal = repo.main / ".git" / cleanup._journal_name(repo.wave)
    journal.touch(mode=0o600)
    before = _admin_tree_state(admin)
    rc, out, err = _run(repo, capsys)
    assert (rc, out) == (20, "")
    assert "invalid admin recovery journal: incomplete or malformed JSON" in err
    assert _admin_tree_state(admin) == before
    assert _sha(repo.main, "refs/heads/wave") == repo.tip


def test_admin_journal_publication_never_overwrites_final(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)
    common = repo.main / ".git"
    admin = common / "worktrees" / "wave"
    original = cleanup._rename_journal
    before = None

    def competing_final(fd, temporary, final):
        nonlocal before
        before = _admin_tree_state(admin)
        (common / final).write_bytes(b"existing journal")
        original(fd, temporary, final)

    monkeypatch.setattr(cleanup, "_rename_journal", competing_final)
    rc, out, err = _run(repo, capsys)
    assert (rc, out) == (30, "")
    assert "phase=admin-remove" in err
    assert "File exists" in err
    assert (common / cleanup._journal_name(repo.wave)).read_bytes() == b"existing journal"
    assert _admin_tree_state(admin) == before
    assert _sha(repo.main, "refs/heads/wave") == repo.tip


@pytest.mark.parametrize("state", ("a", "c"))
def test_admin_binding_must_be_unique_for_live_and_stale(tmp_path, monkeypatch, capsys, state):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)
    _prepare_state(repo, state)
    admin = repo.main / ".git" / "worktrees" / "wave"
    duplicate = admin.with_name("duplicate")
    shutil.copytree(admin, duplicate)
    before = (_admin_tree_state(admin), _admin_tree_state(duplicate))
    rc, out, err = _run(repo, capsys)
    assert (rc, out) == (20, "")
    assert "phase=preflight" in err
    assert (_admin_tree_state(admin), _admin_tree_state(duplicate)) == before
    assert _sha(repo.main, "refs/heads/wave") == repo.tip


def test_recordless_admin_without_recovery_journal_is_rejected(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch)
    _prepare_state(repo, "c")
    admin = repo.main / ".git" / "worktrees" / "wave"
    (admin / "HEAD").unlink()
    before = _admin_tree_state(admin)
    rc, out, err = _run(repo, capsys)
    assert (rc, out) == (20, "")
    assert "phase=preflight" in err
    assert _admin_tree_state(admin) == before
    assert _sha(repo.main, "refs/heads/wave") == repo.tip


def test_forbidden_git_verbs_absent_from_source_calls_and_runtime_allowlist(monkeypatch):
    tree = ast.parse(_TOOL.read_text(encoding="utf-8"))
    forbidden = {("worktree", "prune"), ("worktree", "remove"), ("submodule", "deinit"), ("branch", "-D")}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "id", None)
        if name not in {"_git", "_must_git"}:
            continue
        constants = tuple(
            arg.value for arg in node.args[1:3]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
        )
        assert constants not in forbidden

    calls = []
    monkeypatch.setattr(cleanup.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    for verb in forbidden:
        with pytest.raises(RuntimeError):
            cleanup._git(Path("/tmp"), *verb)
    assert calls == []


@pytest.mark.parametrize(
    "argv",
    (
        ("worktree", "prune", "--dry-run", "--verbose", "--expire=now"),
        ("worktree", "prune", "--expire=now"),
        ("worktree", "remove", "--force"),
        ("worktree", "remove"),
        ("worktree", "remove", "--force", "--", "x"),
        ("submodule", "deinit", "-f", "--", "external/ccbench"),
        ("submodule", "deinit"),
        ("branch", "-D", "--", "x"),
        ("branch", "-D", "x"),
    ),
)
def test_git_argv_validator_directly_rejects_forbidden_commands(argv):
    with pytest.raises(RuntimeError, match="git argv is not allowlisted"):
        cleanup._validate_git_argv(argv)


@pytest.mark.parametrize(
    "argv",
    (
        ("branch", "-d", "-f", "--", "wave"),
        ("branch", "-f", "-d", "--", "wave"),
        ("branch", "-d", "--force", "--", "wave"),
        ("branch", "--force", "-d", "--", "wave"),
        ("branch", "-d", "--", "wave", "-f"),
    ),
)
def test_git_argv_schema_rejects_force_delete_permutations(monkeypatch, argv):
    calls = []
    monkeypatch.setattr(
        cleanup.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    with pytest.raises(RuntimeError):
        cleanup._git(Path("/tmp"), *argv)
    assert calls == []


@pytest.mark.parametrize(
    "allowed",
    (
        ("cat-file", "-e", "a" * 40 + "^{commit}"),
        ("check-ref-format", "--branch", "wave"),
        ("merge-base", "--is-ancestor", "a" * 40, "refs/heads/main"),
        ("merge-base", "--is-ancestor", "a" * 40, "b" * 40),
        ("rev-list", "--walk-reflogs", "refs/heads/wave"),
        ("rev-parse", "--git-common-dir"),
        ("rev-parse", "--git-dir"),
        ("rev-parse", "--git-path", "izanagi-spool-fold-state.json"),
        ("rev-parse", "--verify", "refs/heads/wave^{commit}"),
        ("status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none"),
        ("symbolic-ref", "--quiet", "HEAD"),
        ("worktree", "list", "--porcelain"),
        ("worktree", "unlock", "/tmp/wave"),
        ("checkout", "--detach"),
        ("branch", "-d", "--", "wave"),
    ),
)
def test_git_argv_schema_rejects_trailing_arguments_for_every_allowed_form(
    monkeypatch, allowed,
):
    calls = []
    monkeypatch.setattr(
        cleanup.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    with pytest.raises(RuntimeError):
        cleanup._git(Path("/tmp"), *allowed, "--force")
    assert calls == []


def test_git_argv_spy_sees_only_allowlisted_cleanup_commands(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)
    calls: list[tuple[str, ...]] = []
    original = cleanup._git

    def spy(cwd, *args):
        calls.append(tuple(args))
        return original(cwd, *args)

    monkeypatch.setattr(cleanup, "_git", spy)
    _assert_success_output(
        _run(repo, capsys),
        "removed",
        occupancy_phases=("preflight", "recheck"),
    )
    assert calls
    assert ("worktree", "list", "--porcelain") in calls
    assert all("-z" not in call for call in calls if call[:2] == ("worktree", "list"))
    assert any(call[:2] == ("rev-list", "--walk-reflogs") for call in calls)
    assert all("--not" not in call for call in calls if call[:2] == ("rev-list", "--walk-reflogs"))
    assert all(
        call[:2] not in {("worktree", "remove"), ("submodule", "deinit"), ("branch", "-D")}
        for call in calls
    )


@pytest.mark.parametrize(
    ("phase", "state"),
    (
        ("unlock", "a-locked"),
        ("detach", "a"),
        ("recheck", "a"),
        ("remove-directory", "a"),
        ("admin-recheck", "c"),
        ("admin-remove", "c"),
        ("registry", "c"),
        ("branch-recheck", "d"),
        ("branch-delete", "d"),
        ("postcondition", "d"),
    ),
)
def test_each_mutation_phase_failure_is_partial_and_calls_nothing_afterward(
    tmp_path, monkeypatch, capsys, phase, state,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=(state == "a-locked"))
    _stub_unoccupied(monkeypatch)
    if state in {"c", "d"}:
        _prepare_state(repo, state)
    failed = False

    def boom():
        nonlocal failed
        failed = True
        raise RuntimeError(f"injected {phase}")

    original_git = cleanup._git

    def no_git_after_failure(cwd, *args):
        assert not failed, f"git called after injected {phase}: {args}"
        return original_git(cwd, *args)

    monkeypatch.setattr(cleanup, "_git", no_git_after_failure)

    if phase in {"unlock", "detach"}:
        original_must = cleanup._must_git

        def fail_selected(cwd, *args):
            selected = (
                (phase == "unlock" and args[:2] == ("worktree", "unlock"))
                or (phase == "detach" and args[:2] == ("checkout", "--detach"))
            )
            if selected:
                boom()
            return original_must(cwd, *args)

        monkeypatch.setattr(cleanup, "_must_git", fail_selected)
    elif phase == "recheck":
        original = cleanup._assert_clean_and_head
        count = 0

        def fail_second(*args):
            nonlocal count
            count += 1
            if count == 2:
                boom()
            return original(*args)

        monkeypatch.setattr(cleanup, "_assert_clean_and_head", fail_second)
    elif phase == "remove-directory":
        monkeypatch.setattr(cleanup, "_remove_verified_tree", lambda *args: boom())
    elif phase == "admin-recheck":
        monkeypatch.setattr(cleanup, "_recheck_admin", lambda *args: boom())
    elif phase == "admin-remove":
        monkeypatch.setattr(cleanup, "_remove_admin", lambda *args: boom())
    elif phase == "registry":
        monkeypatch.setattr(cleanup, "_verify_record_state", lambda *args, **kwargs: boom())
    elif phase == "branch-recheck":
        original = cleanup._resolve_commit
        ref_calls = 0

        def fail_second_ref(cwd, expression):
            nonlocal ref_calls
            if expression == f"refs/heads/{repo.branch}^{{commit}}":
                ref_calls += 1
                if ref_calls == 2:
                    boom()
            return original(cwd, expression)

        monkeypatch.setattr(cleanup, "_resolve_commit", fail_second_ref)
    elif phase == "branch-delete":
        monkeypatch.setattr(cleanup, "_delete_branch", lambda *args: boom())
    elif phase == "postcondition":
        monkeypatch.setattr(cleanup, "_verify_record_state", lambda *args, **kwargs: boom())
    else:  # pragma: no cover - parameter list is the registry
        raise AssertionError(phase)

    rc, stdout, stderr = _run(repo, capsys)
    assert failed, (
        f"injection did not fire: phase={phase} state={state} "
        f"rc={rc} stdout={stdout!r} stderr={stderr!r}"
    )
    assert rc == 30 and stdout == ""
    assert f"status=partial phase={phase}" in stderr
    assert stderr.count("\n") == 1


def test_keyboard_interrupt_after_mutation_start_reports_partial(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)

    def interrupt(*args):
        raise KeyboardInterrupt

    monkeypatch.setattr(cleanup, "_remove_verified_tree", interrupt)
    rc, stdout, stderr = _run(repo, capsys)
    assert (rc, stdout) == (30, "")
    assert "status=partial phase=remove-directory" in stderr
    assert stderr.count("\n") == 1
    assert repo.wave.is_dir()
    assert _sha(repo.main, f"refs/heads/{repo.branch}") == repo.tip


def test_keyboard_interrupt_during_preflight_is_not_partial(tmp_path, monkeypatch, capsys):
    main = tmp_path / "main"
    main.mkdir()
    wave = tmp_path / "wave"
    monkeypatch.setattr(
        cleanup,
        "_preflight",
        lambda *args: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    with pytest.raises(KeyboardInterrupt):
        cleanup.main([
            "--main-worktree", os.fspath(main),
            "--wave-worktree", os.fspath(wave),
            "--wave-branch", "wave",
            "--tested-wave-tip-sha", "a" * 40,
        ])
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", "")


def test_argv_requires_each_option_once_and_full_lowercase_sha(capsys):
    cases = (
        [],
        ["--main-worktree", "/tmp/a"] * 4,
        [
            "--main-worktree", "/tmp/a",
            "--wave-worktree", "/tmp/b",
            "--wave-branch", "wave",
            "--tested-wave-tip-sha", "A" * 40,
        ],
        [
            "--main-worktree", "/tmp/a",
            "--wave-worktree", "/tmp/b",
            "--wave-branch", "wave",
            "--tested-wave-tip-sha", "a" * 40,
            "--landing-wave-tip-sha", "B" * 40,
        ],
    )
    for argv in cases:
        rc = cleanup.main(argv)
        captured = capsys.readouterr()
        assert rc == 2 and captured.out == ""
        assert captured.err.startswith("dev-wave-cleanup: status=rejected phase=argv reason=")
        assert captured.err.count("\n") == 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
