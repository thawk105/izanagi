# -*- coding: utf-8 -*-
"""消えたブランチの未 land 作業を検出する監査の controls。"""

from __future__ import annotations

import errno
import hashlib
import importlib.util
import io
import os
import subprocess
import sys
import threading
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


@pytest.fixture(autouse=True)
def _clear_offrepo_scan_workers(monkeypatch):
    monkeypatch.delenv("IZANAGI_AUDIT_SCAN_WORKERS", raising=False)


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


def _commit_bytes_path(
    repo: Path,
    branch: str,
    raw_relpath: bytes,
    content: bytes = b"raw path\n",
) -> tuple[str, str]:
    _git(repo, "checkout", "-q", "-b", branch)
    raw_target = os.fsencode(repo) + b"/" + raw_relpath
    raw_parent = raw_target.rsplit(b"/", 1)[0]
    os.makedirs(raw_parent, exist_ok=True)
    descriptor = os.open(raw_target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(descriptor, content)
    finally:
        os.close(descriptor)
    _git(repo, "add", "--all")
    _git(repo, "commit", "-qm", f"raw path on {branch}")
    return _git(repo, "rev-parse", "HEAD"), os.fsdecode(raw_relpath)


class _RecordingInput(io.BytesIO):
    def close(self) -> None:
        self.flush()


class _FakeCatProcess:
    def __init__(self, stdout: bytes, *, returncode: int = 0, stderr: bytes = b""):
        self.stdin = _RecordingInput()
        self.stdout = io.BytesIO(stdout)
        self.stderr = io.BytesIO(stderr)
        self.returncode = returncode
        self.communicate_calls = 0
        self.terminate_calls = 0
        self.kill_calls = 0
        self.wait_calls = 0

    def communicate(self, timeout):
        self.communicate_calls += 1
        self.stdin.close()
        return self.stdout.read(), self.stderr.read()

    def terminate(self) -> None:
        self.terminate_calls += 1

    def kill(self) -> None:
        self.kill_calls += 1

    def wait(self) -> int:
        self.wait_calls += 1
        return self.returncode


def _fake_oid(label: str) -> str:
    return hashlib.sha1(label.encode("utf-8")).hexdigest()


def _fake_ls_tree_result(
    args: tuple[str, ...],
    contents_by_path: dict[str, bytes],
) -> subprocess.CompletedProcess[bytes]:
    assert args[:5] == (
        "--literal-pathspecs",
        "ls-tree",
        "-z",
        "-l",
        "--full-tree",
    )
    assert args[6] == "--"
    records = []
    for path in args[7:]:
        content = contents_by_path[path]
        records.append(
            f"100644 blob {_fake_oid(path)} {len(content)}\t".encode()
            + os.fsencode(path)
            + b"\0"
        )
    return subprocess.CompletedProcess(args, 0, b"".join(records), b"")


def _fake_cat_stdout(contents_by_path: dict[str, bytes]) -> bytes:
    by_oid = {
        _fake_oid(path): content for path, content in contents_by_path.items()
    }
    return b"".join(
        oid.encode() + f" blob {len(content)}\n".encode() + content + b"\n"
        for oid, content in sorted(by_oid.items())
    )


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


def _report(findings=()) -> ADC.AuditReport:
    return ADC.AuditReport(
        findings=list(findings),
        suppressions=[],
        unreferenced_copies=[],
        requested_roots=(),
        accepted_roots=(),
        rejected_roots=(),
        scan_performed=False,
        blob_failures=0,
        scan_failures=0,
        oversize_blobs=(),
        reference_failure=None,
        regenerable_excluded_pairs=0,
        regenerable_only_commits=(),
    )


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
    output = capsys.readouterr().out
    assert ADC.LIMITATION_NOTICE in output
    assert f"{ADC.AUDIT_ELAPSED_LIMIT_SECONDS:.3f} 秒" in output
    assert "--include-regenerable-artifacts" in output


@pytest.mark.parametrize(
    ("findings", "expected_rc"),
    (((), 0), ((("c" * 40, "subject", ["lost.py"]),), 1)),
)
def test_cli_progress_flush_order_and_elapsed_without_rc_change(
    monkeypatch, capsys, findings, expected_rc,
) -> None:
    import builtins

    real_print = builtins.print
    print_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def record_print(*args, **kwargs):
        print_calls.append((args, kwargs))
        return real_print(*args, **kwargs)

    def fake_audit(*_args, progress=None, **_kwargs):
        assert progress is not None
        progress("fsck 開始")
        progress("fsck 完了 elapsed_seconds=1.000 commits=1")
        return _report(findings)

    monotonic_values = iter((10.0, 12.0))
    monkeypatch.setattr(ADC, "audit_with_offrepo", fake_audit)
    monkeypatch.setattr(ADC.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(builtins, "print", record_print)

    assert ADC.main(["--repo", "/tmp/fake-progress-repo"]) == expected_rc
    output = capsys.readouterr().out
    progress_calls = [
        kwargs
        for args, kwargs in print_calls
        if args and str(args[0]).startswith("audit_dangling_commits: 進捗 ")
    ]
    assert progress_calls
    assert all(kwargs.get("flush") is True for kwargs in progress_calls)
    assert output.index("進捗 fsck 開始") < output.index("repo 外の同一実体")
    assert output.rstrip().endswith("audit_dangling_commits: elapsed_seconds=2.000")


def test_cli_elapsed_is_reported_on_execution_failure(
    monkeypatch, capsys,
) -> None:
    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("synthetic failure")

    monotonic_values = iter((3.0, 4.5))
    monkeypatch.setattr(ADC, "audit_with_offrepo", fail_audit)
    monkeypatch.setattr(ADC.time, "monotonic", lambda: next(monotonic_values))

    assert ADC.main(["--repo", "/tmp/fake-failure-repo"]) == 2
    captured = capsys.readouterr()
    assert "synthetic failure" in captured.err
    assert captured.out.rstrip().endswith(
        "audit_dangling_commits: elapsed_seconds=1.500"
    )


def test_cli_argparse_usage_error_precedes_audit_and_has_no_elapsed(
    capsys,
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        ADC.main(["--definitely-not-a-valid-option"])

    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err
    assert "elapsed_seconds=" not in captured.out
    assert "elapsed_seconds=" not in captured.err


def test_cli_progress_preserves_existing_report_line_order(
    monkeypatch, capsys,
) -> None:
    commit = "9" * 40
    external = Path("/fixed/external.py")
    report = ADC.AuditReport(
        findings=[(commit, "subject", ["tools/lost.py"])],
        suppressions=[(commit, "tools/copied.py", external)],
        unreferenced_copies=[],
        requested_roots=(Path("/fixed/root"),),
        accepted_roots=(Path("/fixed/root"),),
        rejected_roots=(),
        scan_performed=True,
        blob_failures=0,
        scan_failures=0,
        oversize_blobs=((commit, "tools/large.py", ADC.MAX_BLOB_SIZE + 1),),
        reference_failure=None,
        regenerable_excluded_pairs=1,
        regenerable_only_commits=(("8" * 40, "generated", 1),),
    )

    def fake_audit(*_args, progress=None, **_kwargs):
        progress("fsck 開始")
        return report

    monotonic_values = iter((0.0, 1.0))
    monkeypatch.setattr(ADC, "audit_with_offrepo", fake_audit)
    monkeypatch.setattr(ADC.time, "monotonic", lambda: next(monotonic_values))

    assert ADC.main(["--repo", "/tmp/fake-order-repo"]) == 1
    output = capsys.readouterr().out
    ordered_fragments = (
        "audit_dangling_commits: 進捗 fsck 開始",
        "audit_dangling_commits: 再生成可能物として除外",
        "audit_dangling_commits: repo 外の同一実体の探索根",
        "oversize (抑止せず)",
        "audit_dangling_commits: repo 外の同一実体で抑止",
        "audit_dangling_commits: 要確認の到達不能変更",
        "audit_dangling_commits: elapsed_seconds=",
    )
    positions = [output.index(fragment) for fragment in ordered_fragments]
    assert positions == sorted(positions)


@pytest.mark.parametrize("findings", ((), (("d" * 40, "subject", ["lost.py"]),)))
def test_cli_elapsed_limit_overrun_is_disclosed_without_rc_change(
    monkeypatch, capsys, findings,
) -> None:
    monkeypatch.setattr(ADC, "audit_with_offrepo", lambda *_a, **_kw: _report(findings))
    monotonic_values = iter((0.0, ADC.AUDIT_ELAPSED_LIMIT_SECONDS + 1.0))
    monkeypatch.setattr(ADC.time, "monotonic", lambda: next(monotonic_values))

    expected_rc = 1 if findings else 0
    assert ADC.main(["--repo", "/tmp/fake-overrun-repo"]) == expected_rc
    output = capsys.readouterr().out
    assert "audit_dangling_commits: 所要上限超過" in output
    assert f"limit_seconds={ADC.AUDIT_ELAPSED_LIMIT_SECONDS:.3f}" in output
    assert output.rstrip().endswith(
        f"audit_dangling_commits: elapsed_seconds={ADC.AUDIT_ELAPSED_LIMIT_SECONDS + 1.0:.3f}"
    )


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


def test_bulk_commit_records_preserve_all_path_block_shapes_and_octopus(
    tmp_path: Path, monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    parent_one = _commit_files(
        repo,
        "parent-one",
        {"resolved.txt": "parent one\n", "inherited.txt": "one\n"},
    )
    _git(repo, "checkout", "-q", "main")
    parent_two = _commit_files(
        repo, "parent-two", {"resolved.txt": "parent two\n"}
    )
    _git(repo, "checkout", "-q", "main")
    parent_three = _commit_files(
        repo, "parent-three", {"resolved.txt": "parent three\n"}
    )
    _git(repo, "checkout", "-q", "parent-one")
    (repo / "resolved.txt").write_text("resolved differently\n", encoding="utf-8")
    _git(repo, "add", "resolved.txt")
    tree = _git(repo, "write-tree")
    merge = _git(
        repo,
        "commit-tree",
        tree,
        "-p",
        parent_one,
        "-p",
        parent_two,
        "-m",
        "two parent merge",
    )
    octopus = _git(
        repo,
        "commit-tree",
        tree,
        "-p",
        parent_one,
        "-p",
        parent_two,
        "-p",
        parent_three,
        "-m",
        "three parent merge",
    )
    parent_one_tree = _git(repo, "rev-parse", f"{parent_one}^{{tree}}")
    empty_merge = _git(
        repo,
        "commit-tree",
        parent_one_tree,
        "-p",
        parent_one,
        "-p",
        parent_two,
        "-m",
        "empty combined merge",
    )
    _git(repo, "commit", "-qm", "single parent normal")
    single_parent = _git(repo, "rev-parse", "HEAD")
    _git(repo, "commit", "--allow-empty", "-qm", "empty single parent")
    empty_single_parent = _git(repo, "rev-parse", "HEAD")
    real_bulk = ADC._git_bytes_input
    argv_seen: list[tuple[str, ...]] = []
    outputs_seen: list[bytes] = []

    def record_bulk(repo_path, args, input_bytes):
        argv_seen.append(tuple(args))
        completed = real_bulk(repo_path, args, input_bytes)
        outputs_seen.append(completed.stdout)
        return completed

    monkeypatch.setattr(ADC, "_git_bytes_input", record_bulk)
    records = ADC.bulk_commit_records(
        repo,
        (
            single_parent,
            merge,
            octopus,
            empty_merge,
            empty_single_parent,
        ),
    )

    assert records[single_parent].paths == ("resolved.txt",)
    assert records[merge].paths == ("resolved.txt",)
    assert records[octopus].paths == ("resolved.txt",)
    assert records[empty_merge].paths == ()
    assert records[empty_single_parent].paths == ()
    assert "inherited.txt" not in records[merge].paths
    assert "inherited.txt" not in records[octopus].paths
    assert len(records[single_parent].parents) == 1
    assert len(records[merge].parents) == 2
    assert len(records[octopus].parents) == 3
    assert len(records[empty_merge].parents) == 2
    assert len(records[empty_single_parent].parents) == 1
    assert len(argv_seen) == 1
    assert len(outputs_seen) == 1
    assert argv_seen[0].index("-c") > argv_seen[0].index("-m")
    assert b"single parent normal\0\nresolved.txt\0" in outputs_seen[0]
    assert b"two parent merge\0\0resolved.txt\0" in outputs_seen[0]
    assert b"empty combined merge\0\0" in outputs_seen[0]
    assert outputs_seen[0].endswith(b"empty single parent\0")


def test_bulk_commit_records_accept_allow_empty_single_parent(
    tmp_path: Path, monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    _git(repo, "commit", "--allow-empty", "-qm", "empty single parent")
    empty_single_parent = _git(repo, "rev-parse", "HEAD")
    real_bulk = ADC._git_bytes_input
    outputs_seen: list[bytes] = []

    def record_bulk(repo_path, args, input_bytes):
        completed = real_bulk(repo_path, args, input_bytes)
        outputs_seen.append(completed.stdout)
        return completed

    monkeypatch.setattr(ADC, "_git_bytes_input", record_bulk)
    records = ADC.bulk_commit_records(repo, (empty_single_parent,))

    assert records[empty_single_parent].paths == ()
    assert len(records[empty_single_parent].parents) == 1
    assert len(outputs_seen) == 1
    assert outputs_seen[0].endswith(b"empty single parent\0")
    assert not outputs_seen[0].endswith(b"empty single parent\0\n")
    assert not outputs_seen[0].endswith(b"empty single parent\0\0")


def test_bulk_commit_records_preserve_root_and_single_parent(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    root_commit = _git(repo, "rev-list", "--max-parents=0", "main")
    (repo / "child.txt").write_text("child\n", encoding="utf-8")
    _git(repo, "add", "child.txt")
    _git(repo, "commit", "-qm", "single parent")
    child = _git(repo, "rev-parse", "HEAD")

    records = ADC.bulk_commit_records(repo, (root_commit, child))

    assert records[root_commit].paths == ("base.txt",)
    assert records[child].paths == ("child.txt",)


def _assert_raw_path_is_reported(tmp_path: Path, raw_path: bytes) -> None:
    repo = _repo(tmp_path)
    lost, decoded_path = _commit_bytes_path(repo, "doomed", raw_path)
    _delete_branch(repo, "doomed")
    assert _audit(repo) == [(lost, "raw path on doomed", [decoded_path])]


def test_bulk_path_preserves_invalid_utf8_name(tmp_path: Path) -> None:
    _assert_raw_path_is_reported(tmp_path, b"tools/invalid-\xff.py")


def test_bulk_path_preserves_leading_lf_name(tmp_path: Path) -> None:
    _assert_raw_path_is_reported(tmp_path, b"\nleading-lf.py")


def test_bulk_path_preserves_leading_colon_name(tmp_path: Path) -> None:
    _assert_raw_path_is_reported(tmp_path, b":leading-colon.py")


def test_bulk_path_preserves_literal_glob_name(tmp_path: Path) -> None:
    _assert_raw_path_is_reported(tmp_path, b"tools/literal[*?].py")


def test_bulk_path_preserves_valid_non_ascii_name(tmp_path: Path) -> None:
    _assert_raw_path_is_reported(tmp_path, "tools/監査.py".encode("utf-8"))


@pytest.mark.parametrize("hex_length", (40, 64))
def test_bulk_path_preserves_oid_shaped_hex_filename(
    tmp_path: Path, hex_length: int,
) -> None:
    _assert_raw_path_is_reported(tmp_path, b"a" * hex_length)


def test_bulk_path_preserves_record_marker_like_name(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    lost = _commit_files(repo, "doomed", {"before.py": "one\n", "R": "two\n"})
    _delete_branch(repo, "doomed")
    assert _audit(repo) == [
        (lost, "work on doomed", ["R", "before.py"])
    ]


def _fake_bulk_output(
    records: tuple[tuple[str, tuple[str, ...], str, tuple[bytes, ...]], ...]
) -> bytes:
    output = bytearray()
    for commit, parents, subject, paths in records:
        output.extend(ADC._BULK_LOG_RECORD_MARKER)
        output.extend(commit.encode())
        output.extend(b"\0")
        output.extend(" ".join(parents).encode())
        output.extend(b"\0")
        output.extend(subject.encode())
        if paths:
            output.extend(b"\0\n")
            for path in paths:
                output.extend(path + b"\0")
        else:
            output.extend(b"\0\0")
    return bytes(output)


def test_bulk_log_preserves_zero_path_records_in_all_batch_positions() -> None:
    first = "1" * 40
    consecutive = "2" * 64
    before_middle = "3" * 40
    middle = "4" * 40
    after_middle = "5" * 64
    last = "6" * 40
    raw_records = (
        (first, (), "zero first", ()),
        (consecutive, (first,), "zero consecutive", ()),
        (before_middle, (), "path before middle", (b"before.py",)),
        (middle, (), "zero middle", ()),
        (after_middle, (), "path after middle", (b"after.py",)),
        (last, (), "zero last", ()),
    )
    output = _fake_bulk_output(raw_records)

    records = ADC._parse_bulk_commit_records(
        output, tuple(record[0] for record in raw_records)
    )

    assert records[first].paths == ()
    assert records[consecutive].paths == ()
    assert records[before_middle].paths == ("before.py",)
    assert records[middle].paths == ()
    assert records[after_middle].paths == ("after.py",)
    assert records[last].paths == ()
    assert records[consecutive].parents == (first,)
    assert b"zero first\0\0" + ADC._BULK_LOG_RECORD_MARKER in output
    assert output.endswith(b"zero last\0\0")


def _fake_bulk_delimiter_free_zero_path_record(
    commit: str, subject: str
) -> bytes:
    return (
        ADC._BULK_LOG_RECORD_MARKER
        + commit.encode()
        + b"\0\0"
        + subject.encode()
        + b"\0"
    )


@pytest.mark.parametrize("record_position", ("nonterminal", "terminal"))
def test_bulk_log_preserves_delimiter_free_zero_paths_at_all_positions(
    tmp_path: Path, monkeypatch, record_position: str,
) -> None:
    first = "1" * 40
    second = "2" * 40
    first_valid = _fake_bulk_output(
        ((first, (), "first", (b"first.py",)),)
    )
    second_valid = _fake_bulk_output(
        ((second, (), "second", (b"second.py",)),)
    )
    if record_position == "nonterminal":
        output = (
            _fake_bulk_delimiter_free_zero_path_record(first, "first")
            + second_valid
        )
    else:
        output = (
            first_valid
            + _fake_bulk_delimiter_free_zero_path_record(second, "second")
        )

    def fake_bulk(_repo, _args, _input):
        return subprocess.CompletedProcess((), 0, output, b"")

    monkeypatch.setattr(ADC, "_git_bytes_input", fake_bulk)
    records = ADC.bulk_commit_records(tmp_path, (first, second))

    if record_position == "nonterminal":
        assert records[first].paths == ()
        assert records[second].paths == ("second.py",)
    else:
        assert records[first].paths == ("first.py",)
        assert records[second].paths == ()


@pytest.mark.parametrize("malformed_suffix", (b"path.py\0", b"\npath.py"))
@pytest.mark.parametrize("record_position", ("nonterminal", "terminal"))
def test_bulk_log_path_block_requires_leading_lf_and_terminal_nul(
    tmp_path: Path,
    monkeypatch,
    capsys,
    malformed_suffix: bytes,
    record_position: str,
) -> None:
    first = "1" * 40
    second = "2" * 40
    first_valid = _fake_bulk_output(
        ((first, (), "first", (b"first.py",)),)
    )
    second_valid = _fake_bulk_output(
        ((second, (), "second", (b"second.py",)),)
    )
    if record_position == "nonterminal":
        output = (
            _fake_bulk_delimiter_free_zero_path_record(first, "first")
            + malformed_suffix
            + second_valid
        )
    else:
        output = (
            first_valid
            + _fake_bulk_delimiter_free_zero_path_record(second, "second")
            + malformed_suffix
        )

    def fake_bulk(_repo, _args, _input):
        return subprocess.CompletedProcess((), 0, output, b"")

    def invoke_bulk(*_args, **_kwargs):
        ADC.bulk_commit_records(tmp_path, (first, second))
        raise AssertionError("malformed bulk path block was not rejected")

    monkeypatch.setattr(ADC, "_git_bytes_input", fake_bulk)
    monkeypatch.setattr(ADC, "audit_with_offrepo", invoke_bulk)

    assert ADC.main(["--repo", str(tmp_path)]) == 2
    captured = capsys.readouterr()
    assert "header/path 境界が不正" in captured.err
    assert captured.out.splitlines()[-1].startswith(
        "audit_dangling_commits: elapsed_seconds="
    )


def test_bulk_log_nonzero_git_rc_rejects_partial_output(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    first = "1" * 40
    second = "2" * 40
    partial = _fake_bulk_output(((first, (), "first", (b"one",)),))

    def fake_bulk(_repo, _args, _input):
        return subprocess.CompletedProcess((), 128, partial, b"bad object")

    def invoke_bulk(*_args, **_kwargs):
        ADC.bulk_commit_records(tmp_path, (first, second))
        raise AssertionError("bulk completeness failure was not raised")

    monkeypatch.setattr(ADC, "_git_bytes_input", fake_bulk)
    monkeypatch.setattr(ADC, "audit_with_offrepo", invoke_bulk)

    assert ADC.main(["--repo", str(tmp_path)]) == 2
    captured = capsys.readouterr()
    assert "実行できません" in captured.err
    assert "bulk git log に失敗した (rc=128)" in captured.err
    assert "elapsed_seconds=" in captured.out


def test_bulk_log_missing_complete_record_is_execution_failure(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    first = "1" * 40
    second = "2" * 40
    first_only = _fake_bulk_output(((first, (), "first", (b"one",)),))

    def fake_bulk(_repo, _args, _input):
        return subprocess.CompletedProcess((), 0, first_only, b"")

    def invoke_bulk(*_args, **_kwargs):
        ADC.bulk_commit_records(tmp_path, (first, second))
        raise AssertionError("bulk completeness failure was not raised")

    monkeypatch.setattr(ADC, "_git_bytes_input", fake_bulk)
    monkeypatch.setattr(ADC, "audit_with_offrepo", invoke_bulk)

    assert ADC.main(["--repo", str(tmp_path)]) == 2
    captured = capsys.readouterr()
    assert "bulk log の完全性検査に失敗した" in captured.err
    assert captured.out.splitlines()[-1].startswith(
        "audit_dangling_commits: elapsed_seconds="
    )


def test_audit_invokes_one_bulk_log_for_all_unreachable_commits(
    tmp_path: Path, monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    _commit_files(repo, "doomed", {"first.py": "first\n"})
    (repo / "second.py").write_text("second\n", encoding="utf-8")
    _git(repo, "add", "second.py")
    _git(repo, "commit", "-qm", "second unreachable")
    _delete_branch(repo, "doomed")
    unreachable = ADC.unreachable_commits(repo)
    assert len(unreachable) == 2
    real_bulk = ADC._git_bytes_input
    calls: list[tuple[tuple[str, ...], bytes]] = []

    def count_bulk(repo_path, args, input_bytes):
        calls.append((tuple(args), input_bytes))
        return real_bulk(repo_path, args, input_bytes)

    monkeypatch.setattr(ADC, "_git_bytes_input", count_bulk)
    findings = _audit(repo)

    assert len(findings) == 2
    assert len(calls) == 1
    assert calls[0][0][0] == "log"
    assert sorted(calls[0][1].decode().splitlines()) == unreachable


@pytest.mark.parametrize(
    "stdout",
    (
        f"unreachable commit {'a' * 40}",
        "unreachable commit\n",
        "unreachable commit not-an-object-id\n",
        f"unreachable commit {'b' * 40} extra\n",
    ),
)
def test_fsck_malformed_commit_lines_are_execution_failure(
    tmp_path: Path, monkeypatch, capsys, stdout: str,
) -> None:
    def fake_git(_repo, *_args):
        return subprocess.CompletedProcess((), 0, stdout, "")

    def invoke_fsck(*_args, **_kwargs):
        ADC.unreachable_commits(tmp_path)
        raise AssertionError("malformed fsck output was not rejected")

    monkeypatch.setattr(ADC, "_git", fake_git)
    monkeypatch.setattr(ADC, "audit_with_offrepo", invoke_fsck)

    assert ADC.main(["--repo", str(tmp_path)]) == 2
    captured = capsys.readouterr()
    assert "git fsck" in captured.err
    assert captured.out.splitlines()[-1].startswith(
        "audit_dangling_commits: elapsed_seconds="
    )


def test_fsck_accepts_complete_sha256_commit_line(monkeypatch) -> None:
    commit = "c" * 64

    def fake_git(_repo, *_args):
        return subprocess.CompletedProcess(
            (), 0, f"unreachable blob {'d' * 64}\nunreachable commit {commit}\n", ""
        )

    monkeypatch.setattr(ADC, "_git", fake_git)

    assert ADC.unreachable_commits(Path("/tmp/fake-sha256-fsck-repo")) == [commit]


def test_fsck_emits_internal_rate_limited_heartbeat(monkeypatch) -> None:
    commit = "e" * 40

    class FakeFsckProcess:
        def __init__(self):
            self.returncode = 0
            self.calls = 0

        def communicate(self, timeout):
            self.calls += 1
            if self.calls == 1:
                raise subprocess.TimeoutExpired("git fsck", timeout)
            return f"unreachable commit {commit}\n", ""

    process = FakeFsckProcess()
    monotonic_values = iter((1.0, 17.0))
    monkeypatch.setattr(ADC.subprocess, "Popen", lambda *_a, **_kw: process)
    monkeypatch.setattr(ADC.time, "monotonic", lambda: next(monotonic_values))
    progress: list[str] = []

    assert ADC.unreachable_commits(
        Path("/tmp/fake-fsck-repo"), progress=progress.append
    ) == [commit]
    assert len(progress) == 1
    assert progress[0].startswith("fsck heartbeat elapsed_seconds=")


def test_git_heartbeat_zero_interval_has_bounded_poll_count(monkeypatch) -> None:
    class FakeFsckProcess:
        def __init__(self):
            self.returncode = 0
            self.calls = 0
            self.waited = 0.0

        def communicate(self, timeout):
            self.calls += 1
            if self.calls > 4:
                raise AssertionError("zero-interval poll count is unbounded")
            self.waited += timeout
            if self.waited < ADC.POLL_FLOOR_SECONDS * 2.5:
                raise subprocess.TimeoutExpired("git fsck", timeout)
            return "", ""

    process = FakeFsckProcess()
    monkeypatch.setattr(ADC.subprocess, "Popen", lambda *_a, **_kw: process)
    monkeypatch.setattr(ADC, "HEARTBEAT_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(ADC.time, "monotonic", lambda: 0.0)
    progress: list[str] = []

    completed = ADC._git_with_heartbeat(
        Path("/tmp/fake-zero-interval-repo"),
        ("fsck",),
        stage="fsck",
        progress=progress.append,
    )

    assert completed.returncode == 0
    assert process.calls == 3
    assert len(progress) == 2


def test_offrepo_walk_emits_internal_rate_limited_heartbeat(
    tmp_path: Path, monkeypatch,
) -> None:
    root = tmp_path / "offrepo"
    root.mkdir()
    candidate = ADC._BlobMetadata(
        "f" * 40, "tools/missing.py", "missing.py", False, "1" * 40, 4
    )
    monkeypatch.setattr(ADC, "HEARTBEAT_INTERVAL_SECONDS", 0.0)
    progress: list[str] = []

    possible, failures, scanned = ADC._enumerate_offrepo_candidates(
        (root,), (candidate,), progress=progress.append
    )

    assert possible == {}
    assert failures == 0
    assert scanned is True
    assert any(line.startswith("repo 外走査 heartbeat ") for line in progress)


def test_flat_offrepo_filename_loop_emits_heartbeat(
    tmp_path: Path, monkeypatch,
) -> None:
    root = tmp_path / "offrepo"
    _external_file(root, "missing.py", "same")
    candidate = ADC._BlobMetadata(
        "f" * 40, "tools/missing.py", "missing.py", False, "1" * 40, 4
    )
    monotonic_values = iter((0.0, 0.5, 2.0))
    monkeypatch.setattr(ADC, "HEARTBEAT_INTERVAL_SECONDS", 1.0)
    monkeypatch.setattr(ADC.time, "monotonic", lambda: next(monotonic_values))
    progress: list[str] = []

    possible, failures, scanned = ADC._enumerate_offrepo_candidates(
        (root,), (candidate,), progress=progress.append
    )

    assert set(possible) == {candidate.object_id}
    assert failures == 0
    assert scanned is True
    assert progress == ["repo 外走査 heartbeat directories=1 files=1"]


def test_candidate_comparison_emits_file_and_read_chunk_heartbeats(
    tmp_path: Path, monkeypatch,
) -> None:
    root = tmp_path / "offrepo"
    external = _external_file(root, "same.py", "same")
    alias = root / "alias" / "same.py"
    alias.parent.mkdir()
    os.link(external, alias)
    alias = alias.resolve()
    metadata = ADC._BlobMetadata(
        "c" * 40, "tools/same.py", "same.py", False, "1" * 40, 4
    )
    possible, failures, scanned = ADC._enumerate_offrepo_candidates(
        (root,), (metadata,)
    )
    assert failures == 0
    assert scanned is True

    class FakeCat:
        def read_blob(self, object_id: str, size: int) -> bytes:
            assert (object_id, size) == (metadata.object_id, metadata.size)
            return b"same"

    monkeypatch.setattr(ADC, "HEARTBEAT_INTERVAL_SECONDS", 0.0)
    progress: list[str] = []
    matches, failed_keys, comparison_failures = ADC._compare_offrepo_candidates(
        FakeCat(), possible, progress=progress.append
    )

    assert matches == {
        (metadata.commit, metadata.path): sorted(
            (
                ADC._ExternalMatch(external, root),
                ADC._ExternalMatch(alias, root),
            ),
            key=lambda item: (str(item.path), str(item.root)),
        ),
    }
    assert failed_keys == set()
    assert comparison_failures == 0
    assert any(line.startswith("候補比較 heartbeat files=1") for line in progress)
    assert any("read_chunks=1" in line for line in progress)


def test_stage_instrumentation_reports_separate_cost_surfaces(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    progress: list[str] = []

    report = ADC.audit_with_offrepo(repo, progress=progress.append)

    assert report.findings == []
    for stage in (
        "fsck",
        "bulk log",
        "main・tip tree",
        "blob metadata",
        "repo 外走査の列挙",
        "候補比較",
        "landed 参照",
    ):
        assert any(line.startswith(f"{stage} 開始") for line in progress)
        assert any(line.startswith(f"{stage} 完了") for line in progress)


def test_stage_instrumentation_covers_root_suppression_and_final_report(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    repo = _repo(tmp_path)
    progress: list[str] = []

    report = ADC.audit_with_offrepo(repo, progress=progress.append)

    assert report.findings == []
    for stage in ("root 検証", "抑止集約"):
        assert any(line.startswith(f"{stage} 開始") for line in progress)
        assert any(line.startswith(f"{stage} 完了") for line in progress)

    monkeypatch.setattr(ADC, "audit_with_offrepo", lambda *_a, **_kw: _report())
    assert ADC.main(["--repo", str(repo)]) == 0
    output = capsys.readouterr().out
    assert "進捗 最終報告 開始" in output
    assert "進捗 最終報告 完了 elapsed_seconds=" in output


def test_candidate_session_materialization_is_inside_comparison_stage(
    monkeypatch,
) -> None:
    events: list[str] = []

    class ObservedPossible(dict):
        def values(self):
            events.append("session keys materialized")
            return super().values()

    monkeypatch.setattr(ADC, "_checked_git", lambda *_a, **_kw: "a" * 40)
    monkeypatch.setattr(
        ADC,
        "_audit_snapshot",
        lambda *_a, **_kw: ADC._CoreAudit([], 0, ()),
    )
    monkeypatch.setattr(
        ADC,
        "_enumerate_offrepo_candidates",
        lambda *_a, **_kw: (ObservedPossible(), 0, True),
    )

    report = ADC.audit_with_offrepo(
        Path("/repo"),
        offrepo_roots=(Path("/offrepo"),),
        progress=events.append,
    )

    assert report.findings == []
    comparison_start = events.index("候補比較 開始")
    session_materialized = events.index("session keys materialized")
    comparison_complete = next(
        index
        for index, event in enumerate(events)
        if event.startswith("候補比較 完了")
    )
    assert comparison_start < session_materialized < comparison_complete


def test_parallel_offrepo_scan_preserves_enumeration(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "offrepo"
    direct = _external_file(root, "direct.py", "same")
    shared = _external_file(root, "a/same.py", "same")
    nested = _external_file(root, "a/nested/nested.py", "same")
    for name in ("b", "c", "d", "e", "z"):
        (root / name).mkdir()
    os.link(shared, root / "b/same.py")
    os.link(shared, root / "b/other.py")
    last = _external_file(root, "z/last.py", "same")
    _external_file(root, "c/same.py", "longer")
    _external_file(root, "d/same.py", "same", executable=True)
    (root / "e/same.py").symlink_to(shared)
    target = tmp_path / "target"
    _external_file(target, "hidden.py", "same")
    (root / "link").symlink_to(target, target_is_directory=True)
    (root / "a/link").symlink_to(target, target_is_directory=True)
    names = ("direct.py", "same.py", "other.py", "nested.py", "last.py", "hidden.py")
    metadata = {
        name: ADC._BlobMetadata("commit", "src/" + name, name, False,
                                "shared" if name in ("same.py", "other.py") else name, 4)
        for name in names
    }

    def expected_group(path, item, owners, aliases):
        st = path.lstat()
        return {(st.st_dev, st.st_ino): (
            path, root, item, sorted(owners), sorted(aliases),
            (st.st_dev, st.st_ino, st.st_mode, st.st_size),
        )}

    expected = {
        "direct.py": expected_group(direct, metadata["direct.py"],
            [("commit", "src/direct.py")], [(direct, root)]),
        "shared": expected_group(shared, metadata["same.py"],
            [("commit", "src/same.py"), ("commit", "src/other.py")],
            [(shared, root), (shared, root / "a"),
             (root / "b/same.py", root), (root / "b/other.py", root)]),
        "nested.py": expected_group(nested, metadata["nested.py"],
            [("commit", "src/nested.py")], [(nested, root), (nested, root / "a")]),
        "last.py": expected_group(last, metadata["last.py"],
            [("commit", "src/last.py")], [(last, root)]),
    }
    observed = []
    for workers in (1, 4):
        monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", str(workers))
        possible, failures, scanned = ADC._enumerate_offrepo_candidates(
            (root, root / "a"), tuple(metadata.values())
        )
        canonical = {
            oid: {identity: (
                group.external.path, group.external.root, group.metadata,
                sorted(group.owners), sorted((a.path, a.root) for a in group.aliases),
                (group.external.initial_stat.st_dev, group.external.initial_stat.st_ino,
                 group.external.initial_stat.st_mode, group.external.initial_stat.st_size),
            ) for identity, group in groups.items()}
            for oid, groups in possible.items()
        }
        assert (canonical, failures, scanned) == (expected, 0, True)
        observed.append(canonical)
    assert observed[0] == observed[1]


def _parallel_scan_fixture(tmp_path: Path):
    root = tmp_path / "offrepo"
    paths = [_external_file(root, f"{name}/same.py", "same") for name in ("a", "b")]
    candidate = ADC._BlobMetadata("commit", "src/same.py", "same.py", False, "oid", 4)
    return root, paths, candidate


def test_parallel_offrepo_scan_preserves_report(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "offrepo"
    saved = _external_file(root, "a/saved.py", "same")
    copy = _external_file(root, "b/copy.py", "same")
    denied = root / "denied"
    denied.mkdir()
    findings = [("commit", "subject", ["src/saved.py", "src/copy.py", "src/missing.py"])]
    candidates = [ADC._BlobMetadata("commit", "src/" + name, name, False, name, 4)
                  for name in ("saved.py", "copy.py", "missing.py")]
    roots = (root, denied)
    monkeypatch.setattr(ADC, "_checked_git", lambda *_a, **_kw: "main-oid")
    monkeypatch.setattr(ADC, "_audit_snapshot", lambda *_a, **_kw: ADC._CoreAudit(findings, 0, ()))
    monkeypatch.setattr(ADC, "_load_blob_metadata", lambda *_a: (candidates, 0, ()))
    monkeypatch.setattr(ADC, "_landed_reference_matches",
                        lambda *_a, **_kw: ({("commit", "src/saved.py"): [saved]}, None))

    class FakeCat:
        def __init__(self, *_a, **_kw):
            pass

        def read_blob(self, oid, size):
            assert oid in ("saved.py", "copy.py") and size == 4
            return b"same"

        def close(self):
            return None

    monkeypatch.setattr(ADC, "_CatFileBatch", FakeCat)
    real_scandir = os.scandir

    def scandir(path):
        if Path(path) == denied:
            raise PermissionError("denied fixture")
        return real_scandir(path)

    monkeypatch.setattr(ADC.os, "scandir", scandir)
    expected = ADC.AuditReport(
        findings=[("commit", "subject", ["src/copy.py", "src/missing.py"])],
        suppressions=[("commit", "src/saved.py", saved)],
        unreferenced_copies=[("commit", "src/copy.py", copy)],
        requested_roots=roots, accepted_roots=roots, rejected_roots=(),
        scan_performed=True, blob_failures=0, scan_failures=2,
        oversize_blobs=(), reference_failure=None,
        regenerable_excluded_pairs=0, regenerable_only_commits=(),
    )
    reports = []
    denied.chmod(0)
    try:
        for workers in (1, 4):
            monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", str(workers))
            reports.append(ADC.audit_with_offrepo(tmp_path / "repo", offrepo_roots=roots))
            assert reports[-1] == expected
    finally:
        denied.chmod(0o755)
    assert reports[0] == reports[1]


def test_parallel_offrepo_scan_uses_multiple_threads(tmp_path: Path, monkeypatch) -> None:
    root, _, candidate = _parallel_scan_fixture(tmp_path)
    real_worker = ADC._scan_offrepo_directory
    barrier = threading.Barrier(2, timeout=10)
    identities = set()
    lock = threading.Lock()

    def worker(*args):
        if args[0] == root:
            return real_worker(*args)
        with lock:
            identities.add(threading.get_ident())
        barrier.wait()
        return real_worker(*args)

    monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", "4")
    monkeypatch.setattr(ADC, "_scan_offrepo_directory", worker)
    possible, failures, scanned = ADC._enumerate_offrepo_candidates((root,), (candidate,))
    assert len(identities) >= 2
    assert len(possible["oid"]) == 2 and failures == 0 and scanned


def test_parallel_offrepo_scan_preserves_failure_counts(tmp_path: Path, monkeypatch) -> None:
    root, paths, candidate = _parallel_scan_fixture(tmp_path)
    denied = [root / "a" / f"deny{i}" for i in range(5)]
    for path in denied:
        path.mkdir()
        path.chmod(0)
    real_scandir = os.scandir
    real_lstat = Path.lstat
    errors_by_worker = {}
    error_lock = threading.Lock()

    def scandir(path):
        try:
            return real_scandir(path)
        except PermissionError:
            with error_lock:
                ident = threading.get_ident()
                errors_by_worker[ident] = errors_by_worker.get(ident, 0) + 1
            raise

    def lstat(path, *args, **kwargs):
        if path == paths[0]:
            raise OSError("injected candidate failure")
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(ADC.os, "scandir", scandir)
    monkeypatch.setattr(Path, "lstat", lstat)
    try:
        for workers in (1, 4):
            errors_by_worker.clear()
            monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", str(workers))
            possible, failures, scanned = ADC._enumerate_offrepo_candidates(
                (root, root / "a"), (candidate,)
            )
            if os.geteuid() != 0:
                assert failures == 12  # Five walk errors + one lstat error, twice.
                assert max(errors_by_worker.values()) >= 2
            assert scanned is True and len(possible["oid"]) == 1
            assert next(iter(possible["oid"].values())).external.path == paths[1]
    finally:
        for path in denied:
            path.chmod(0o700)

    class PartialScandir:
        def __init__(self, path):
            self.entries = real_scandir(path)
            self.yielded = False

        def __enter__(self):
            self.entries.__enter__()
            return self

        def __exit__(self, *args):
            return self.entries.__exit__(*args)

        def __iter__(self):
            return self

        def __next__(self):
            if self.yielded:
                raise OSError("after one entry")
            self.yielded = True
            return next(self.entries)

    monkeypatch.setattr(ADC.os, "scandir", PartialScandir)
    for workers in (1, 4):
        monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", str(workers))
        assert ADC._enumerate_offrepo_candidates((root,), (candidate,)) == ({}, 1, True)


def test_parallel_offrepo_scan_preserves_first_seen(tmp_path: Path, monkeypatch) -> None:
    root, paths, candidate = _parallel_scan_fixture(tmp_path)
    direct = _external_file(root, "same.py", "same")
    os.link(direct, root / "b/alias.py")
    os.link(paths[0], root / "b/other.py")
    aliases = [ADC._BlobMetadata("alias", "src/" + name, name, False, "oid", 4)
               for name in ("alias.py", "other.py")]
    earlier_oid = ADC._BlobMetadata("commit", "src/early.py", "early.py", False, "early", 4)
    later_oid = ADC._BlobMetadata("commit", "src/late.py", "late.py", False, "late", 4)
    _external_file(root, "a/early.py", "same")
    _external_file(root, "b/late.py", "same")
    candidates = (candidate, *aliases, earlier_oid, later_oid)
    monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", "1")
    sequential, _, _ = ADC._enumerate_offrepo_candidates((root,), candidates)
    real_worker = ADC._scan_offrepo_directory
    later_finished = threading.Event()
    completion = []

    def worker(subtree, *args):
        if subtree == root:
            return real_worker(subtree, *args)
        if subtree.name == "a":
            assert later_finished.wait(10)
        result = real_worker(subtree, *args)
        completion.append(subtree.name)
        if subtree.name == "b":
            later_finished.set()
        return result

    monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", "4")
    monkeypatch.setattr(ADC, "_scan_offrepo_directory", worker)
    possible, failures, scanned = ADC._enumerate_offrepo_candidates(
        (root,), candidates
    )
    assert completion == ["b", "a"]
    assert failures == 0 and scanned is True
    groups = list(possible["oid"].values())
    assert [g.external.path for g in groups] == [direct, paths[0], paths[1]]
    assert [g.metadata for g in groups] == [candidate, candidate, candidate]
    assert list(possible["oid"]) == [(p.stat().st_dev, p.stat().st_ino)
                                     for p in (direct, *paths)]
    assert list(possible) == list(sequential) == ["oid", "early", "late"]
    assert list(possible["oid"]) == list(sequential["oid"])
    assert possible == sequential

    # One worker sees B first at b, then A and B at the earlier DFS path.
    tied_root = tmp_path / "tied"
    earlier = _external_file(tied_root, "a/deep/same.py", "same")
    later = tied_root / "b/other.py"
    later.parent.mkdir()
    os.link(earlier, later)
    blockers = [tied_root / f"z{i}" for i in range(3)]
    for path in blockers:
        path.mkdir()
    tied_candidates = (
        ADC._BlobMetadata("commit", "src/same.py", "same.py", False, "A", 4),
        ADC._BlobMetadata("commit", "src/same.py", "same.py", False, "B", 4),
        ADC._BlobMetadata("commit", "src/other.py", "other.py", False, "B", 4),
    )
    parked = threading.Barrier(4, timeout=10)
    earlier_finished = threading.Event()
    local_order = []

    def ordered_worker(directory, *args):
        if directory in blockers:
            parked.wait()
            assert earlier_finished.wait(10)
        if directory == later.parent:
            parked.wait()  # All other workers stay parked until deep completes.
        result = real_worker(directory, *args)
        if directory in (later.parent, earlier.parent):
            local_order.append((directory, threading.get_ident()))
        if directory == earlier.parent:
            earlier_finished.set()
        return result

    monkeypatch.setattr(ADC, "_scan_offrepo_directory", ordered_worker)
    possible, failures, scanned = ADC._enumerate_offrepo_candidates(
        (tied_root,), tied_candidates
    )
    assert failures == 0 and scanned is True
    assert [directory for directory, _ in local_order] == [later.parent, earlier.parent]
    assert len({ident for _, ident in local_order}) == 1
    assert next(iter(possible["B"].values())).external.path == earlier
    assert list(possible) == ["A", "B"]


def _canonical_offrepo_candidates(possible):
    return [
        (oid, [(identity, group.external, group.metadata,
                group.owners, group.aliases) for identity, group in groups.items()])
        for oid, groups in possible.items()
    ]


def test_parallel_offrepo_scan_handles_deep_and_wide_trees(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "offrepo"
    directories = {root}
    for relative in ["big/" + str(i) for i in range(300)] + [
        "small" + str(i) for i in range(20)
    ] + ["/".join(["deep"] * 10)]:
        file = _external_file(root, relative + "/same.py", "same")
        directories.update(p for p in file.parents if p == root or root in p.parents)
    candidate = ADC._BlobMetadata("commit", "src/same.py", "same.py", False, "oid", 4)
    real_task = ADC._scan_offrepo_directory
    visited = []
    lock = threading.Lock()

    def task(directory, *args):
        with lock:
            visited.append(directory)
        return real_task(directory, *args)

    monkeypatch.setattr(ADC, "_scan_offrepo_directory", task)
    monkeypatch.setattr(ADC, "HEARTBEAT_INTERVAL_SECONDS", 0.0)
    observed = []
    for workers in (1, 4):
        monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", str(workers))
        progress = []
        possible, failures, scanned = ADC._enumerate_offrepo_candidates(
            (root,), (candidate,), progress=progress.append
        )
        assert failures == 0 and scanned
        assert progress[-1] == f"repo 外走査 heartbeat directories={len(directories)} files=321"
        observed.append((_canonical_offrepo_candidates(possible), failures, scanned))
    assert observed[0] == observed[1]
    assert set(visited) == directories
    assert len(visited) == len(directories)


def test_parallel_offrepo_scan_symlink_directory_is_listed_not_entered(
    tmp_path: Path, monkeypatch,
) -> None:
    root, _, candidate = _parallel_scan_fixture(tmp_path)
    target = tmp_path / "target"
    _external_file(target, "hidden.py", "same")
    links = [root / "link", root / "a/link"]
    for link in links:
        link.symlink_to(target, target_is_directory=True)
    hidden = ADC._BlobMetadata("commit", "src/hidden.py", "hidden.py", False, "hidden", 4)
    real_iteration = ADC._process_offrepo_iteration
    listed = []

    def iteration(*args, **kwargs):
        directory, dirnames, _ = args[1]
        listed.extend(Path(directory) / name for name in dirnames if name == "link")
        return real_iteration(*args, **kwargs)

    monkeypatch.setattr(ADC, "_process_offrepo_iteration", iteration)
    monkeypatch.setattr(ADC, "HEARTBEAT_INTERVAL_SECONDS", 0.0)
    observed = []
    for workers in (1, 4):
        listed.clear()
        progress = []
        monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", str(workers))
        possible, failures, scanned = ADC._enumerate_offrepo_candidates(
            (root,), (candidate, hidden), progress=progress.append
        )
        assert sorted(listed) == sorted(links)
        assert "hidden" not in possible
        assert failures == 0 and scanned
        assert progress[-1] == "repo 外走査 heartbeat directories=3 files=2"
        observed.append(_canonical_offrepo_candidates(possible))
    assert observed[0] == observed[1]


def test_parallel_offrepo_scan_propagates_worker_exception(tmp_path: Path, monkeypatch) -> None:
    root, _, candidate = _parallel_scan_fixture(tmp_path)
    class WorkerError(Exception):
        pass

    injected = WorkerError("t2637 injected")
    real_worker = ADC._scan_offrepo_directory
    before = threading.active_count()
    processing = threading.Barrier(2, timeout=10)
    delayed_finished = threading.Event()

    def worker(*args):
        if args[0] == root:
            return real_worker(*args)
        processing.wait()
        if args[0] == root / "a":
            raise injected
        # Keep this worker processing after its peer raises.
        threading.Event().wait(0.3)
        result = real_worker(*args)
        delayed_finished.set()
        return result

    monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", "4")
    monkeypatch.setattr(ADC, "_scan_offrepo_directory", worker)
    with pytest.raises(WorkerError, match="t2637 injected") as caught:
        ADC._enumerate_offrepo_candidates((root,), (candidate,))
    assert caught.value is injected
    assert delayed_finished.is_set()
    assert threading.active_count() == before


def test_parallel_offrepo_scan_heartbeat_runs_on_caller(tmp_path: Path, monkeypatch) -> None:
    root, _, candidate = _parallel_scan_fixture(tmp_path)
    monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", "4")
    monkeypatch.setattr(ADC, "HEARTBEAT_INTERVAL_SECONDS", 0.0)
    caller = threading.get_ident()
    progress = []
    timeouts = []
    real_wait = ADC.threading.Event.wait

    def wait(event, timeout=None):
        if threading.get_ident() == caller and timeout is not None:
            assert timeout > 0
            timeouts.append(timeout)
        return real_wait(event, timeout)

    def callback(message):
        assert threading.get_ident() == caller
        progress.append(message)

    monkeypatch.setattr(ADC.threading.Event, "wait", wait)
    _, failures, scanned = ADC._enumerate_offrepo_candidates(
        (root,), (candidate,), progress=callback
    )
    assert failures == 0 and scanned is True
    assert timeouts
    assert progress[-1] == "repo 外走査 heartbeat directories=3 files=2"
    counts = [tuple(int(field.split("=")[1]) for field in line.split()[-2:])
              for line in progress]
    assert all(a[0] <= b[0] and a[1] <= b[1] for a, b in zip(counts, counts[1:]))


def test_offrepo_scan_worker_configuration(tmp_path: Path, monkeypatch) -> None:
    root, _, candidate = _parallel_scan_fixture(tmp_path)
    assert ADC.OFFREPO_SCAN_WORKERS == 16
    assert ADC._offrepo_scan_workers() == 16
    real_thread = ADC.threading.Thread
    created = []

    def thread(*args, **kwargs):
        assert kwargs["daemon"] is False
        created.append(1)
        return real_thread(*args, **kwargs)

    monkeypatch.setattr(ADC.threading, "Thread", thread)
    for raw, expected in ((None, 16), ("1", 1), ("4", 4)):
        if raw is None:
            monkeypatch.delenv("IZANAGI_AUDIT_SCAN_WORKERS", raising=False)
        else:
            monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", raw)
        assert ADC._offrepo_scan_workers() == expected
        created.clear()
        assert ADC._enumerate_offrepo_candidates((root,), (candidate,))[1:] == (0, True)
        assert len(created) == (0 if expected == 1 else expected)
    for invalid in ("", "abc", "0", "-3"):
        monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", invalid)
        with pytest.raises(RuntimeError, match="positive integer"):
            ADC._enumerate_offrepo_candidates((root,), (candidate,))


def test_empty_offrepo_candidates_touch_neither_filesystem_nor_pool(monkeypatch) -> None:
    def trap(*_args, **_kwargs):
        raise AssertionError("empty candidates touched filesystem, pool or environment")

    with monkeypatch.context() as patch:
        patch.setattr(ADC.os, "walk", trap)
        patch.setattr(ADC.os, "scandir", trap)
        patch.setattr(Path, "lstat", trap)
        patch.setattr(ADC.threading, "Thread", trap)
        patch.setattr(ADC.queue, "Queue", trap)
        patch.setattr(ADC.os.environ, "get", trap)
        assert ADC._enumerate_offrepo_candidates((Path("/unused"),), ()) == ({}, 0, False)


def test_parallel_offrepo_scan_unreadable_subdirectory(tmp_path: Path, monkeypatch) -> None:
    if os.geteuid() == 0:
        pytest.skip("root bypasses child directory permissions")
    root, _, candidate = _parallel_scan_fixture(tmp_path)
    denied = root / "a"
    denied.chmod(0)
    try:
        for workers in (1, 4):
            monkeypatch.setenv("IZANAGI_AUDIT_SCAN_WORKERS", str(workers))
            possible, failures, scanned = ADC._enumerate_offrepo_candidates((root,), (candidate,))
            assert failures == 1 and scanned is True
            assert len(possible["oid"]) == 1
    finally:
        denied.chmod(0o755)


def test_removed_changed_files_api_cannot_reintroduce_per_commit_fork() -> None:
    assert not hasattr(ADC, "changed_files")


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

    cache_only = _commit_files(
        repo,
        "cache-only-after-fold",
        {"output/s8b-build-cache/cache.bin": "generated\n"},
    )
    _delete_branch(repo, "cache-only-after-fold")
    assert cache_only not in {commit for commit, _subject, _paths in _audit(repo, excluded=())}


def test_negative_regenerable_build_cache_is_excluded_by_default(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    cache_only = _commit_files(
        repo,
        "cache-only",
        {"output/s8b-build-cache/only.bin": "generated\n"},
    )
    _delete_branch(repo, "cache-only")
    mixed = _commit_files(
        repo,
        "cache-and-source",
        {
            "output/s8b-build-cache/mixed.bin": "generated\n",
            "tools/handwritten.py": "keep me\n",
        },
    )
    _delete_branch(repo, "cache-and-source")

    assert _audit(repo) == [
        (mixed, "work on cache-and-source", ["tools/handwritten.py"])
    ]
    expected_with_regenerable = [
        (
            cache_only,
            "work on cache-only",
            ["output/s8b-build-cache/only.bin"],
        ),
        (
            mixed,
            "work on cache-and-source",
            [
                "output/s8b-build-cache/mixed.bin",
                "tools/handwritten.py",
            ],
        ),
    ]
    assert ADC.audit(
        repo,
        "main",
        ADC.DEFAULT_EXCLUDED_PREFIXES,
        (),
    ) == sorted(expected_with_regenerable)


def test_regenerable_prefix_does_not_exclude_sibling_path(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    sibling_path = "output/s8b-build-cacheX/sibling.bin"
    lost = _commit_files(
        repo,
        "cache-sibling",
        {sibling_path: "handwritten sibling\n"},
    )
    _delete_branch(repo, "cache-sibling")

    assert _audit(repo) == [
        (lost, "work on cache-sibling", [sibling_path])
    ]


def test_regenerable_exclusion_discloses_pairs_and_cache_only_commit(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    lost = _commit_files(
        repo,
        "cache-only",
        {
            "output/s8b-build-cache/one.bin": "one\n",
            "output/s8b-build-cache/two.bin": "two\n",
        },
    )
    _delete_branch(repo, "cache-only")

    assert ADC.main(["--repo", str(repo)]) == 0
    output = capsys.readouterr().out
    assert "再生成可能物として除外 2 (commit, path) 対" in output
    assert f"commit {lost} (work on cache-only)" in output
    assert "除外 path 2 件" in output


@pytest.mark.parametrize(
    ("include_fold", "include_regenerable", "expected_paths"),
    (
        (False, False, ()),
        (True, False, ("docs/spool/worklog/fragment.md",)),
        (False, True, ("output/s8b-build-cache/cache.bin",)),
        (
            True,
            True,
            (
                "docs/spool/worklog/fragment.md",
                "output/s8b-build-cache/cache.bin",
            ),
        ),
    ),
)
def test_cli_include_regenerable_artifacts_is_independent_from_fold_flag(
    tmp_path: Path,
    monkeypatch,
    capsys,
    include_fold: bool,
    include_regenerable: bool,
    expected_paths: tuple[str, ...],
) -> None:
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    repo = _repo(tmp_path)
    _commit_files(
        repo,
        "doomed",
        {
            "docs/spool/worklog/fragment.md": "fold\n",
            "output/s8b-build-cache/cache.bin": "generated\n",
        },
    )
    _delete_branch(repo, "doomed")
    argv = ["--repo", str(repo)]
    if include_fold:
        argv.append("--include-fold-trees")
    if include_regenerable:
        argv.append("--include-regenerable-artifacts")

    expected_rc = 1 if expected_paths else 0
    assert ADC.main(argv) == expected_rc
    output = capsys.readouterr().out
    for path in expected_paths:
        assert f"main・全 local branch tip に不在: {path}" in output
    all_paths = {
        "docs/spool/worklog/fragment.md",
        "output/s8b-build-cache/cache.bin",
    }
    for path in all_paths - set(expected_paths):
        assert f"main・全 local branch tip に不在: {path}" not in output


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


@pytest.mark.parametrize(
    ("content", "pattern"),
    (
        (b"/offrepo/w/a.py\n", b"/offrepo/w/a.py"),
        (b"/offrepo/w/a.py.backup\n", b"/offrepo/w/a.py"),
        (b"/offrepo/w/a.py+backup\n", b"/offrepo/w/a.py"),
        (b"/other/offrepo/w/a.py\n", b"/offrepo/w/a.py"),
        ("/offrepo/w/a.py。\n".encode(), b"/offrepo/w/a.py"),
        (
            b"/offrepo/w/a.py+backup\n/offrepo/w/a.py\n",
            b"/offrepo/w/a.py",
        ),
    ),
    ids=(
        "bounded",
        "prefix-collision",
        "plus-suffix",
        "left-boundary-collision",
        "non-ascii-suffix",
        "valid-after-invalid",
    ),
)
def test_bounded_path_reference_single_scan_matches_legacy_boundary_semantics(
    content: bytes,
    pattern: bytes,
) -> None:
    found = ADC._bounded_path_reference_matches(
        content,
        {pattern},
        {b"/offrepo"},
    )

    assert (pattern in found) is ADC._has_bounded_path_reference(content, pattern)


def test_bounded_path_reference_single_scan_matches_ancestor_directory() -> None:
    root = Path("/offrepo")
    match = ADC._ExternalMatch(root / "wave/nested/file.py", root)
    patterns = {os.fsencode(pattern) for pattern in ADC._reference_patterns(match)}
    ancestor = os.fsencode(str(root / "wave/nested"))

    found = ADC._bounded_path_reference_matches(
        b"landed: /offrepo/wave/nested\n",
        patterns,
        {os.fsencode(root)},
    )

    assert found == {ancestor}


def test_bounded_path_reference_single_scan_rejects_search_root() -> None:
    root = Path("/offrepo")
    match = ADC._ExternalMatch(root / "wave/file.py", root)
    patterns = {os.fsencode(pattern) for pattern in ADC._reference_patterns(match)}
    encoded_root = os.fsencode(root)

    found = ADC._bounded_path_reference_matches(
        b"landed: /offrepo\n",
        patterns,
        {encoded_root},
    )

    assert encoded_root not in patterns
    assert found == set()


def test_bounded_path_reference_single_scan_finds_multiple_tokens() -> None:
    root = Path("/offrepo")
    first = os.fsencode(str(root / "one/a.py"))
    second = os.fsencode(str(root / "two"))
    not_bounded = os.fsencode(str(root / "three/c.py"))
    patterns = {
        os.fsencode(pattern)
        for match in (
            ADC._ExternalMatch(root / "one/a.py", root),
            ADC._ExternalMatch(root / "two/b.py", root),
            ADC._ExternalMatch(root / "three/c.py", root),
        )
        for pattern in ADC._reference_patterns(match)
    }

    # Positive: space and quotes are D248 boundaries, so both distinct tokens match.
    # Negative: "=" extends the path left, so /offrepo/three/c.py does not match.
    # Negative: the exploration root /offrepo alone is not reference evidence.
    found = ADC._bounded_path_reference_matches(
        b"first /offrepo/one/a.py second='/offrepo/two' "
        b"negative=/offrepo/three/c.py ignored=/offrepo\n",
        patterns,
        {os.fsencode(root)},
    )

    assert found == {first, second}
    assert not_bounded not in found


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


def test_ls_tree_path_batches_pin_argv_byte_limit_shape() -> None:
    repo = Path("/tmp/ls-tree-batch-repo")
    commit = "a" * 40
    over_budget = "x" * 80
    paths = ("aa", "bbb", over_budget, "c", "dd")
    byte_budget = ADC._ls_tree_argv_size(repo, commit, paths[:2])

    batches = ADC._ls_tree_path_batches(
        repo,
        commit,
        paths,
        max_paths_per_batch=100,
        max_argv_bytes=byte_budget,
    )

    assert tuple(path for batch in batches for path in batch) == paths
    multi_element_batches = [batch for batch in batches if len(batch) > 1]
    assert multi_element_batches
    assert all(
        ADC._ls_tree_argv_size(repo, commit, batch) <= byte_budget
        for batch in multi_element_batches
    )
    overlong_singletons = [
        batch
        for batch in batches
        if len(batch) == 1
        and ADC._ls_tree_argv_size(repo, commit, batch) > byte_budget
    ]
    assert overlong_singletons == [(over_budget,)]
    for batch, next_batch in zip(batches, batches[1:]):
        candidate = batch + (next_batch[0],)
        assert (
            len(candidate) > 100
            or ADC._ls_tree_argv_size(repo, commit, candidate) > byte_budget
        )


def test_ls_tree_batches_are_literal_and_complete(monkeypatch) -> None:
    commit = "b" * 40
    paths = ("literal[*?].py", "plain.py")
    calls: list[tuple[str, ...]] = []

    def empty_tree(_repo, *args):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, b"", b"")

    monkeypatch.setattr(ADC, "_git_bytes", empty_tree)
    metadata, failures, oversize = ADC._load_blob_metadata(
        Path("/tmp/literal-tree-repo"), [(commit, "subject", list(paths))]
    )

    assert metadata == []
    assert failures == 0
    assert oversize == ()
    assert calls
    assert tuple(path for args in calls for path in args[7:]) == paths
    assert all(args[0] == "--literal-pathspecs" for args in calls)


def test_blob_contents_are_loaded_only_after_basename_size_mode_prefilter(
    tmp_path: Path,
) -> None:
    root = tmp_path / "offrepo"
    positive_path = _external_file(root, "positive.py", "same")
    _external_file(root, "other-name.py", "same")
    _external_file(root, "wrong-size.py", "longer")
    _external_file(root, "wrong-mode.py", "same")
    positive_oid = "1" * 40
    candidates = [
        ADC._BlobMetadata("c-pos", "src/positive.py", "positive.py", False, positive_oid, 4),
        ADC._BlobMetadata("c-name", "src/wanted-name.py", "wanted-name.py", False, "2" * 40, 4),
        ADC._BlobMetadata("c-size", "src/wrong-size.py", "wrong-size.py", False, "3" * 40, 4),
        ADC._BlobMetadata("c-mode", "src/wrong-mode.py", "wrong-mode.py", True, "4" * 40, 4),
    ]

    possible, failures, scan_performed = ADC._enumerate_offrepo_candidates(
        (root,), candidates
    )

    assert failures == 0
    assert scan_performed is True
    assert set(possible) == {positive_oid}

    class FakeCat:
        def __init__(self):
            self.requests: list[tuple[str, int]] = []

        def read_blob(self, object_id: str, size: int) -> bytes:
            self.requests.append((object_id, size))
            return b"same"

    cat_file = FakeCat()
    matches, failed_keys, comparison_failures = ADC._compare_offrepo_candidates(
        cat_file, possible
    )
    assert cat_file.requests == [(positive_oid, 4)]
    assert failed_keys == set()
    assert comparison_failures == 0
    assert matches == {("c-pos", "src/positive.py"): [ADC._ExternalMatch(positive_path, root)]}


def test_comparison_mode_check_rejects_post_prefilter_mode_change(
    tmp_path: Path,
) -> None:
    root = tmp_path / "offrepo"
    external = _external_file(root, "mode.py", "same")
    metadata = ADC._BlobMetadata(
        "c" * 40, "src/mode.py", "mode.py", False, "1" * 40, 4
    )
    possible, failures, scanned = ADC._enumerate_offrepo_candidates(
        (root,), (metadata,)
    )
    assert failures == 0
    assert scanned is True
    external.chmod(0o755)

    class FakeCat:
        def read_blob(self, object_id: str, size: int) -> bytes:
            assert (object_id, size) == (metadata.object_id, metadata.size)
            return b"same"

    matches, failed_keys, comparison_failures = ADC._compare_offrepo_candidates(
        FakeCat(), possible
    )

    assert matches == {}
    assert failed_keys == set()
    assert comparison_failures == 1


def test_same_oid_external_file_is_compared_once_and_fanned_out(
    tmp_path: Path, monkeypatch,
) -> None:
    root = tmp_path / "offrepo"
    external = _external_file(root, "same.py", "same")
    alias = root / "alias" / "same.py"
    alias.parent.mkdir()
    os.link(external, alias)
    alias = alias.resolve()
    object_id = "1" * 40
    candidates = (
        ADC._BlobMetadata(
            "a" * 40, "one/same.py", "same.py", False, object_id, 4
        ),
        ADC._BlobMetadata(
            "b" * 40, "two/same.py", "same.py", False, object_id, 4
        ),
    )
    possible, failures, scanned = ADC._enumerate_offrepo_candidates(
        (root,), candidates
    )
    assert failures == 0
    assert scanned is True
    assert len(possible[object_id]) == 1

    class FakeCat:
        def __init__(self):
            self.requests = 0

        def read_blob(self, requested_oid: str, size: int) -> bytes:
            assert (requested_oid, size) == (object_id, 4)
            self.requests += 1
            return b"same"

    real_compare = ADC._compare_regular_candidate
    compare_calls = 0

    def count_compare(*args, **kwargs):
        nonlocal compare_calls
        compare_calls += 1
        return real_compare(*args, **kwargs)

    def reject_second_file_pass(*_args, **_kwargs):
        raise AssertionError("external file was rewound for a second pass")

    cat_file = FakeCat()
    monkeypatch.setattr(ADC, "_compare_regular_candidate", count_compare)
    monkeypatch.setattr(ADC.os, "lseek", reject_second_file_pass)
    matches, failed_keys, comparison_failures = ADC._compare_offrepo_candidates(
        cat_file, possible
    )

    expected_match = sorted(
        (
            ADC._ExternalMatch(external, root),
            ADC._ExternalMatch(alias, root),
        ),
        key=lambda item: (str(item.path), str(item.root)),
    )
    assert matches == {
        (candidates[0].commit, candidates[0].path): expected_match,
        (candidates[1].commit, candidates[1].path): expected_match,
    }
    assert cat_file.requests == 1
    assert compare_calls == 1
    assert failed_keys == set()
    assert comparison_failures == 0


def test_distinct_same_bytes_external_files_are_all_fanned_out(
    tmp_path: Path,
) -> None:
    root = tmp_path / "offrepo"
    first = _external_file(root, "first/same.py", "same")
    second = _external_file(root, "second/same.py", "same")
    metadata = ADC._BlobMetadata(
        "a" * 40, "tools/same.py", "same.py", False, "1" * 40, 4
    )
    possible, failures, scanned = ADC._enumerate_offrepo_candidates(
        (root,), (metadata,)
    )
    assert failures == 0
    assert scanned is True
    assert len(possible[metadata.object_id]) == 2

    class FakeCat:
        def __init__(self):
            self.requests = 0

        def read_blob(self, object_id: str, size: int) -> bytes:
            assert (object_id, size) == (metadata.object_id, metadata.size)
            self.requests += 1
            return b"same"

    cat_file = FakeCat()
    matches, failed_keys, comparison_failures = ADC._compare_offrepo_candidates(
        cat_file, possible
    )

    assert matches == {
        (metadata.commit, metadata.path): sorted(
            (
                ADC._ExternalMatch(first, root),
                ADC._ExternalMatch(second, root),
            ),
            key=lambda item: (str(item.path), str(item.root)),
        ),
    }
    assert cat_file.requests == 1
    assert failed_keys == set()
    assert comparison_failures == 0


class _ShortReadBuffer(io.BytesIO):
    def __init__(self, initial_bytes: bytes, chunk_sizes: tuple[int, ...]):
        super().__init__(initial_bytes)
        self._chunk_sizes = chunk_sizes
        self._read_index = 0

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            return super().read(size)
        limit = self._chunk_sizes[self._read_index % len(self._chunk_sizes)]
        self._read_index += 1
        return super().read(min(size, limit))


class _EmptyMidstreamBuffer(io.BytesIO):
    def __init__(self, initial_bytes: bytes):
        super().__init__(initial_bytes)
        self._content_reads = 0

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            return super().read(size)
        self._content_reads += 1
        if self._content_reads == 1:
            return super().read(min(size, 1))
        if self._content_reads == 2:
            return b""
        return super().read(size)


def test_cat_file_batch_accepts_positive_short_reads_and_drains_concurrently(
    monkeypatch,
) -> None:
    requested = "a" * 40
    stdout = f"{requested} blob 6\n".encode() + b"abcdef\n"
    process = _FakeCatProcess(stdout, stderr=b"diagnostic" * 1000)
    process.stdout = _ShortReadBuffer(stdout, (1, 2, 3))
    monkeypatch.setattr(ADC, "_start_cat_file_batch", lambda _repo: process)
    batch = ADC._CatFileBatch(Path("/tmp/fake-short-read-repo"))

    assert batch.read_blob(requested, 6) == b"abcdef"
    assert batch.close() is None
    assert process.communicate_calls == 1
    assert process.wait_calls == 0


def test_cat_file_batch_rejects_empty_midstream_read_and_aborts_child(
    monkeypatch,
) -> None:
    requested = "a" * 40
    stdout = f"{requested} blob 3\n".encode() + b"abc\n" + b"x" * 1000
    process = _FakeCatProcess(stdout, stderr=b"fatal" * 1000)
    process.stdout = _EmptyMidstreamBuffer(stdout)
    monkeypatch.setattr(ADC, "_start_cat_file_batch", lambda _repo: process)
    batch = ADC._CatFileBatch(Path("/tmp/fake-empty-read-repo"))

    with pytest.raises(RuntimeError, match="途中で切れた"):
        batch.read_blob(requested, 3)
    assert batch.close() is not None
    assert process.terminate_calls == 1
    assert process.communicate_calls == 1
    assert process.wait_calls == 0


def test_cat_file_batch_close_timeout_terminates_then_kills(monkeypatch) -> None:
    requested = "a" * 40
    stdout = f"{requested} blob 3\n".encode() + b"abc\n"

    class TimeoutProcess(_FakeCatProcess):
        def communicate(self, timeout):
            self.communicate_calls += 1
            if self.communicate_calls <= 2:
                raise subprocess.TimeoutExpired("git cat-file", timeout)
            self.stdin.close()
            return self.stdout.read(), self.stderr.read()

    process = TimeoutProcess(stdout)
    monkeypatch.setattr(ADC, "_start_cat_file_batch", lambda _repo: process)
    batch = ADC._CatFileBatch(Path("/tmp/fake-timeout-repo"))

    assert batch.read_blob(requested, 3) == b"abc"
    failure = batch.close()

    assert failure is not None
    assert "timeout" in failure
    assert process.terminate_calls == 1
    assert process.kill_calls == 1
    assert process.communicate_calls == 3
    assert process.wait_calls == 0


@pytest.mark.parametrize(
    ("failure_mode", "returncode"),
    (
        ("oid-mismatch", 0),
        ("type-mismatch", 0),
        ("size-mismatch", 0),
        ("bad-terminator", 0),
        ("mid-response", 128),
        ("trailing-output", 0),
        ("nonzero-after-response", 9),
    ),
)
def test_cat_file_batch_rejects_protocol_and_exit_failures(
    monkeypatch, failure_mode: str, returncode: int,
) -> None:
    requested = "a" * 40
    echoed = "b" * 40 if failure_mode == "oid-mismatch" else requested
    if failure_mode == "mid-response":
        stdout = f"{echoed} blob 3\n".encode() + b"ab"
    else:
        object_type = "tree" if failure_mode == "type-mismatch" else "blob"
        size = 4 if failure_mode == "size-mismatch" else 3
        terminator = b"X" if failure_mode == "bad-terminator" else b"\n"
        trailing = b"extra" if failure_mode == "trailing-output" else b""
        stdout = (
            f"{echoed} {object_type} {size}\n".encode()
            + b"abc"
            + terminator
            + trailing
        )
    process = _FakeCatProcess(stdout, returncode=returncode, stderr=b"fatal")
    monkeypatch.setattr(ADC, "_start_cat_file_batch", lambda _repo: process)
    batch = ADC._CatFileBatch(Path("/tmp/fake-cat-repo"))

    if failure_mode in {"nonzero-after-response", "trailing-output"}:
        assert batch.read_blob(requested, 3) == b"abc"
        failure = batch.close()
        assert failure is not None
        expected = "非 0 終了" if failure_mode == "nonzero-after-response" else "余分な stdout"
        assert expected in failure
    else:
        with pytest.raises(RuntimeError):
            batch.read_blob(requested, 3)
        assert batch.close() is not None


def test_blob_batch_failure_keeps_all_affected_findings(
    tmp_path: Path, monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    lost = _commit_files(
        repo,
        "doomed",
        {"tools/a.py": "shared\n", "tools/b.py": "shared\n"},
    )
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    _external_file(root, "wave/a.py", "shared\n")
    _external_file(root, "wave/b.py", "shared\n")
    object_id = _git(repo, "rev-parse", f"{lost}:tools/a.py")
    process = _FakeCatProcess(
        f"{object_id} blob 7\n".encode() + b"sha",
        returncode=128,
    )
    monkeypatch.setattr(ADC, "_start_cat_file_batch", lambda _repo: process)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == [
        (lost, "work on doomed", ["tools/a.py", "tools/b.py"])
    ]
    assert report.suppressions == []
    assert report.blob_failures == 2
    assert process.stdin.getvalue() == (object_id + "\n").encode()


def test_cat_file_nonzero_after_all_responses_keeps_findings_integration(
    tmp_path: Path, monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/recovered.py"
    lost = _commit_files(repo, "doomed", {relpath: "recovered\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/recovered.py", "recovered\n")
    _landed_reference(repo, external)
    candidate_oid = _git(repo, "rev-parse", f"{lost}:{relpath}")
    landed_path = "docs/landed-copy.md"
    landed_oid = _git(repo, "rev-parse", f"main:{landed_path}")
    candidate_content = b"recovered\n"
    landed_content = (repo / landed_path).read_bytes()
    stdout = (
        f"{candidate_oid} blob {len(candidate_content)}\n".encode()
        + candidate_content
        + b"\n"
        + f"{landed_oid} blob {len(landed_content)}\n".encode()
        + landed_content
        + b"\n"
    )
    process = _FakeCatProcess(stdout, returncode=9, stderr=b"late failure")
    monkeypatch.setattr(ADC, "_start_cat_file_batch", lambda _repo: process)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert report.findings == [(lost, "work on doomed", [relpath])]
    assert report.suppressions == []
    assert report.unreferenced_copies == []
    assert report.blob_failures == 1
    assert report.reference_failure is not None
    assert "非 0 終了" in report.reference_failure
    assert process.communicate_calls == 1


def test_cat_file_close_is_inside_landed_stage_before_completion(
    tmp_path: Path, monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/recovered.py"
    _commit_files(repo, "doomed", {relpath: "recovered\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/recovered.py", "recovered\n")
    _landed_reference(repo, external)
    events: list[str] = []
    real_close = ADC._CatFileBatch.close

    def record_close(self):
        events.append("cat-file close")
        return real_close(self)

    monkeypatch.setattr(ADC._CatFileBatch, "close", record_close)

    report = ADC.audit_with_offrepo(
        repo, offrepo_roots=(root,), progress=events.append
    )

    assert report.findings == []
    close_index = events.index("cat-file close")
    landed_complete_index = next(
        index
        for index, event in enumerate(events)
        if event.startswith("landed 参照 完了")
    )
    assert close_index < landed_complete_index


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
    assert _grep_patterns(grep_calls[0]) == (str(root),)


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


def test_pattern_owners_preserve_first_seen_order_and_deduplicate(
    monkeypatch,
) -> None:
    root = Path("/offrepo")
    first = ADC._ExternalMatch(root / "wave/first.py", root)
    second = ADC._ExternalMatch(root / "wave/second.py", root)
    first_key = ("commit-first", "tools/first.py")
    second_key = ("commit-second", "tools/second.py")
    matches = {
        first_key: [first, first, second],
        second_key: [first],
    }
    monkeypatch.setattr(ADC, "HEARTBEAT_INTERVAL_SECONDS", 0.0)
    progress: list[str] = []

    pattern_owners, processed_matches, generated_patterns = (
        ADC._build_pattern_owners(matches, progress=progress.append)
    )

    assert pattern_owners[str(root / "wave")] == [
        (first_key, first.path),
        (first_key, second.path),
        (second_key, first.path),
    ]
    assert pattern_owners[str(first.path)] == [
        (first_key, first.path),
        (second_key, first.path),
    ]
    assert processed_matches == 4
    assert generated_patterns == 8
    assert progress[-1] == (
        "landed 参照 heartbeat pattern_owners "
        "processed_matches=4 generated_patterns=8"
    )


def test_pattern_owners_complete_for_large_shared_ancestor_population() -> None:
    root = Path("/offrepo")
    key = ("commit", "tools/shared.py")
    population = 50_000
    matches = {
        key: [
            ADC._ExternalMatch(root / "wave" / f"copy-{index}.py", root)
            for index in range(population)
        ]
    }

    pattern_owners, processed_matches, generated_patterns = (
        ADC._build_pattern_owners(matches)
    )

    # list membership 版は共有 ancestor だけで N(N-1)/2、すなわち
    # 1,249,975,000 回の owner 比較になる規模である。
    shared_owners = pattern_owners[str(root / "wave")]
    assert len(shared_owners) == population
    assert shared_owners[0] == (key, matches[key][0].path)
    assert shared_owners[-1] == (key, matches[key][-1].path)
    assert processed_matches == population
    assert generated_patterns == population * 2


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
    tree_batches: list[tuple[str, ...]] = []
    real_read_blob = ADC._CatFileBatch.read_blob
    cat_requests: list[str] = []

    def record_split_calls(repo_path, *args):
        if args and args[0] == "grep":
            grep_batches.append(_grep_patterns(args))
        elif args and args[0] == "--literal-pathspecs":
            tree_batches.append(tuple(args[7:]))
        return real_git_bytes(repo_path, *args)

    def record_cat_request(self, object_id, expected_size):
        cat_requests.append(object_id)
        return real_read_blob(self, object_id, expected_size)

    monkeypatch.setattr(ADC, "_git_bytes", record_split_calls)
    monkeypatch.setattr(ADC._CatFileBatch, "read_blob", record_cat_request)
    split, split_failure = ADC._landed_reference_matches(
        repo,
        main_commit,
        matches,
        max_patterns_per_batch=1,
        max_argv_bytes=1024 * 1024,
    )

    assert split_failure is None
    assert split == single == expected
    assert grep_batches == [(str(root),)]
    assert tree_batches == [("docs/landed-copy.md",)]
    assert len(cat_requests) == 1


def test_root_prefilter_and_full_pattern_prefilter_return_same_suppressions(
    tmp_path: Path, monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    root = tmp_path / "offrepo"
    first = ADC._ExternalMatch(root / "one/first.py", root)
    second = ADC._ExternalMatch(root / "two/second.py", root)
    absent = ADC._ExternalMatch(root / "three/absent.py", root)
    matches = {
        ("commit-first", "tools/first.py"): [first],
        ("commit-second", "tools/second.py"): [second],
        ("commit-absent", "tools/absent.py"): [absent],
    }
    _landed_reference(repo, first.path, second.path.parent)
    main_commit = _git(repo, "rev-parse", "main")
    expected = {
        ("commit-first", "tools/first.py"): [first.path],
        ("commit-second", "tools/second.py"): [second.path],
    }

    root_prefiltered, root_failure = ADC._landed_reference_matches(
        repo, main_commit, matches
    )

    exact_patterns = sorted(
        {
            pattern
            for external_matches in matches.values()
            for match in external_matches
            for pattern in ADC._reference_patterns(match)
        }
    )
    real_batches = ADC._git_grep_pattern_batches

    def full_pattern_batches(repo_path, ref, _roots, **limits):
        return real_batches(repo_path, ref, exact_patterns, **limits)

    monkeypatch.setattr(
        ADC, "_git_grep_pattern_batches", full_pattern_batches
    )
    full_prefiltered, full_failure = ADC._landed_reference_matches(
        repo, main_commit, matches
    )

    assert root_failure is full_failure is None
    assert root_prefiltered == full_prefiltered == expected


def test_root_prefilter_superset_file_does_not_add_suppression(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    root = tmp_path / "offrepo"
    external = ADC._ExternalMatch(root / "wave/target.py", root)
    key = ("commit-target", "tools/target.py")
    _landed_reference(repo, root.resolve())
    main_commit = _git(repo, "rev-parse", "main")
    stats = ADC._LandedReferenceStats()

    referenced, failure = ADC._landed_reference_matches(
        repo, main_commit, {key: [external]}, stats=stats
    )

    assert failure is None
    assert referenced == {}
    assert stats.grep_batches == 1
    assert stats.contents_read == 1
    assert stats.bytes_read == (repo / "docs/landed-copy.md").stat().st_size


def test_landed_grep_batch_count_depends_on_roots_not_exact_patterns(
    monkeypatch,
) -> None:
    repo = Path("/tmp/fake-root-prefilter-repo")
    main_ref = "root-prefilter-snapshot"
    root = Path("/offrepo")
    match = ADC._ExternalMatch(root / "candidate.py", root)
    matches = {("commit", "tools/candidate.py"): [match]}
    exact_pattern_count = 36_102
    pattern_owners = {
        f"{root}/generated-{index}": []
        for index in range(exact_pattern_count)
    }
    grep_batches: list[tuple[str, ...]] = []
    stats = ADC._LandedReferenceStats()

    monkeypatch.setattr(
        ADC,
        "_build_pattern_owners",
        lambda _matches, progress=None: (
            pattern_owners,
            1,
            exact_pattern_count,
        ),
    )

    def no_landed_hits(_repo_path, *args):
        grep_batches.append(_grep_patterns(args))
        return subprocess.CompletedProcess(args, 1, b"", b"")

    monkeypatch.setattr(ADC, "_git_bytes", no_landed_hits)

    referenced, failure = ADC._landed_reference_matches(
        repo, main_ref, matches, stats=stats
    )

    assert failure is None
    assert referenced == {}
    assert stats.patterns == exact_pattern_count
    assert stats.grep_batches == 1
    assert grep_batches == [(str(root),)]


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
    tree_path = "docs/late-hit.md"
    contents_by_path = {tree_path: f"{late_hit}\n".encode()}
    process = _FakeCatProcess(_fake_cat_stdout(contents_by_path))

    def miss_miss_hit(_repo_path, *args):
        if args[0] == "grep":
            batch = _grep_patterns(args)
            grep_batches.append(batch)
            if batch != (str(root),):
                return subprocess.CompletedProcess(args, 1, b"", b"")
            return subprocess.CompletedProcess(
                args, 0, f"{main_ref}:{tree_path}\0".encode(), b""
            )
        assert args[0] == "--literal-pathspecs"
        return _fake_ls_tree_result(args, contents_by_path)

    monkeypatch.setattr(ADC, "_git_bytes", miss_miss_hit)
    monkeypatch.setattr(ADC, "_start_cat_file_batch", lambda _repo: process)

    referenced, failure = ADC._landed_reference_matches(
        repo,
        main_ref,
        matches,
        max_patterns_per_batch=1,
        max_argv_bytes=1024 * 1024,
    )

    assert failure is None
    assert referenced == {("commit-c", "tools/c.py"): [late_hit]}
    assert grep_batches == [(str(root),)]
    assert process.stdin.getvalue() == (_fake_oid(tree_path) + "\n").encode()


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
    contents_by_path = {
        first_tree_path: b"unrelated\n",
        second_tree_path: f"{external}\n".encode(),
    }
    process = _FakeCatProcess(_fake_cat_stdout(contents_by_path))
    tree_batches: list[tuple[str, ...]] = []

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
        assert args[0] == "--literal-pathspecs"
        tree_batches.append(tuple(args[7:]))
        return _fake_ls_tree_result(args, contents_by_path)

    monkeypatch.setattr(ADC, "_git_bytes", same_basename_hits)
    monkeypatch.setattr(ADC, "_start_cat_file_batch", lambda _repo: process)

    referenced, failure = ADC._landed_reference_matches(
        repo, main_ref, matches
    )

    assert failure is None
    assert referenced == {("commit-target", "tools/target.py"): [external]}
    assert tree_batches == [(first_tree_path, second_tree_path)]
    assert set(process.stdin.getvalue().decode().splitlines()) == {
        _fake_oid(first_tree_path),
        _fake_oid(second_tree_path),
    }


def test_landed_reference_matches_emits_rate_limited_heartbeats(
    tmp_path: Path, monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    root = tmp_path / "offrepo"
    external = root / "wave/target.py"
    matches = {
        ("commit-target", "tools/target.py"): [
            ADC._ExternalMatch(external, root)
        ],
    }
    _landed_reference(repo, external)
    main_commit = _git(repo, "rev-parse", "main")
    progress: list[str] = []
    monkeypatch.setattr(ADC, "HEARTBEAT_INTERVAL_SECONDS", 0.0)

    referenced, failure = ADC._landed_reference_matches(
        repo,
        main_commit,
        matches,
        progress=progress.append,
    )

    assert failure is None
    assert referenced == {("commit-target", "tools/target.py"): [external]}
    assert any(
        line.startswith("landed 参照 heartbeat grep_batches=")
        for line in progress
    )
    assert any(
        line.startswith("landed 参照 heartbeat contents=")
        for line in progress
    )
    assert any(
        line.startswith("landed 参照 heartbeat scanned_bytes=")
        for line in progress
    )


def test_stage_diagnostics_report_candidate_and_landed_scale(
    tmp_path: Path, monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    relpath = "tools/shared.py"
    lost = _commit_files(repo, "doomed", {relpath: "same bytes\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    first = _external_file(root, "one/shared.py", "same bytes\n")
    _external_file(root, "two/shared.py", "same bytes\n")
    _landed_reference(repo, first)
    landed_bytes = (repo / "docs" / "landed-copy.md").stat().st_size
    monkeypatch.setattr(ADC, "HEARTBEAT_INTERVAL_SECONDS", 0.0)
    progress: list[str] = []

    report = ADC.audit_with_offrepo(
        repo, offrepo_roots=(root,), progress=progress.append
    )

    assert report.findings == []
    assert report.suppressions == [(lost, relpath, first)]
    comparison_complete = next(
        line for line in progress if line.startswith("候補比較 完了")
    )
    comparison_fields = set(comparison_complete.split())
    assert {
        "matched_keys=1",
        "external_files=2",
        "external_matches=2",
        "max_matches_per_key=2",
    } <= comparison_fields
    landed_complete = next(
        line for line in progress if line.startswith("landed 参照 完了")
    )
    landed_fields = set(landed_complete.split())
    assert {
        "matches=1",
        "match_keys=1",
        "external_matches=2",
        "patterns=4",
        "generated_patterns=4",
        "grep_batches=1",
        "metadata_batches=1",
        "contents_read=1",
        f"bytes_read={landed_bytes}",
    } <= landed_fields
    assert any(
        line.startswith(
            "landed 参照 heartbeat pattern_owners processed_matches="
        )
        for line in progress
    )
    assert any(
        "landed 参照 heartbeat grep_batches=1/1 phase=start" in line
        for line in progress
    )
    assert any(
        "landed 参照 heartbeat grep_batches=1/1 phase=complete" in line
        for line in progress
    )
    assert any(
        "landed 参照 heartbeat ls_tree_batches=1/1 phase=start" in line
        for line in progress
    )
    assert any(
        "landed 参照 heartbeat ls_tree_batches=1/1 phase=complete" in line
        for line in progress
    )


@pytest.mark.parametrize(
    ("failure_mode", "expected_tree_calls", "failure_fragment"),
    (
        ("later-grep-rc", 0, "batch 2/2 rc=2"),
        ("later-invalid-prefix", 0, "path 出力を解釈できない"),
        ("metadata-rc", 1, "metadata 確認不能"),
        ("cat-mid-response", 1, "landed file の参照確認不能"),
    ),
    ids=(
        "later-grep-rc",
        "later-invalid-prefix",
        "metadata-rc",
        "cat-mid-response",
    ),
)
def test_negative_landed_reference_matches_discard_all_on_later_batch_failure(
    monkeypatch,
    failure_mode: str,
    expected_tree_calls: int,
    failure_fragment: str,
) -> None:
    repo = Path("/tmp/fake-repo")
    main_ref = "immutable-snapshot"
    first_root = Path("/offrepo-a")
    second_root = Path("/offrepo-b")
    first = first_root / "a-hit"
    second = second_root / "b-hit"
    matches = {
        ("commit-a", "tools/a.py"): [
            ADC._ExternalMatch(first, first_root)
        ],
        ("commit-b", "tools/b.py"): [
            ADC._ExternalMatch(second, second_root)
        ],
    }
    grep_calls = 0
    tree_calls = 0
    contents_by_path = {
        "docs/one": f"{first}\n".encode(),
        "docs/two": f"{second}\n".encode(),
    }
    if failure_mode == "cat-mid-response":
        ordered = sorted(
            (_fake_oid(path), content)
            for path, content in contents_by_path.items()
        )
        first_oid, first_content = ordered[0]
        second_oid, second_content = ordered[1]
        cat_stdout = (
            f"{first_oid} blob {len(first_content)}\n".encode()
            + first_content
            + b"\n"
            + f"{second_oid} blob {len(second_content)}\n".encode()
            + second_content[:1]
        )
        process = _FakeCatProcess(cat_stdout, returncode=128)
    else:
        process = _FakeCatProcess(_fake_cat_stdout(contents_by_path))

    def fail_later(_repo_path, *args):
        nonlocal grep_calls, tree_calls
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
        assert args[0] == "--literal-pathspecs"
        tree_calls += 1
        if failure_mode == "metadata-rc":
            return subprocess.CompletedProcess(args, 128, b"partial", b"tree failed")
        return _fake_ls_tree_result(args, contents_by_path)

    monkeypatch.setattr(ADC, "_git_bytes", fail_later)
    monkeypatch.setattr(ADC, "_start_cat_file_batch", lambda _repo: process)

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
    assert tree_calls == expected_tree_calls


def test_positive_landed_reference_matches_runs_batched_over_oversized_population(
    monkeypatch,
) -> None:
    repo = Path("/tmp/fake-oversized-repo")
    main_ref = "oversized-population-snapshot"
    population = ADC.GIT_GREP_BATCH_MAX_PATTERNS + 1
    roots = tuple(
        Path(f"/offrepo-{index:04d}") for index in range(population)
    )
    patterns = tuple(str(root) for root in roots)
    assert len(patterns) > ADC.GIT_GREP_BATCH_MAX_PATTERNS
    matches = {
        (f"commit-{index:04d}", f"tools/{index:04d}.py"): [
            ADC._ExternalMatch(root / "candidate.py", root)
        ]
        for index, root in enumerate(roots)
    }
    grep_batches: list[tuple[str, ...]] = []
    tree_path = "docs/landed"
    contents_by_path = {
        tree_path: (
            "\n".join(
                str(external_matches[0].path)
                for external_matches in matches.values()
            )
            + "\n"
        ).encode()
    }
    process = _FakeCatProcess(_fake_cat_stdout(contents_by_path))
    tree_calls = 0

    def fake_git_bytes(_repo_path, *args):
        nonlocal tree_calls
        if args[0] == "grep":
            grep_batches.append(_grep_patterns(args))
            return subprocess.CompletedProcess(
                args, 0, f"{main_ref}:{tree_path}\0".encode(), b""
            )
        assert args[0] == "--literal-pathspecs"
        tree_calls += 1
        return _fake_ls_tree_result(args, contents_by_path)

    monkeypatch.setattr(ADC, "_git_bytes", fake_git_bytes)
    monkeypatch.setattr(ADC, "_start_cat_file_batch", lambda _repo: process)

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
    assert tree_calls == 1
    assert process.stdin.getvalue() == (_fake_oid(tree_path) + "\n").encode()


def test_positive_landed_reference_matches_executes_all_five_batches(
    monkeypatch,
) -> None:
    repo = Path("/tmp/fake-five-batch-repo")
    main_ref = "five-batch-snapshot"
    roots = tuple(Path(f"/offrepo-{index}") for index in range(5))
    patterns = tuple(str(root) for root in roots)
    matches = {
        (f"commit-{index}", f"tools/{index}.py"): [
            ADC._ExternalMatch(root / "candidate.py", root)
        ]
        for index, root in enumerate(roots)
    }
    external_by_root = {
        str(external_matches[0].root): str(external_matches[0].path)
        for external_matches in matches.values()
    }
    grep_batches: list[tuple[str, ...]] = []
    contents_by_tree: dict[str, bytes] = {}
    process_holder: list[_FakeCatProcess] = []
    tree_batches: list[tuple[str, ...]] = []

    def distinct_tree_per_batch(_repo_path, *args):
        if args[0] == "grep":
            batch = _grep_patterns(args)
            grep_batches.append(batch)
            tree_path = f"docs/batch-{len(grep_batches)}.md"
            contents_by_tree[tree_path] = (
                "\n".join(external_by_root[root] for root in batch) + "\n"
            ).encode()
            return subprocess.CompletedProcess(
                args, 0, f"{main_ref}:{tree_path}\0".encode(), b""
            )
        assert args[0] == "--literal-pathspecs"
        tree_batches.append(tuple(args[7:]))
        return _fake_ls_tree_result(args, contents_by_tree)

    def start_cat(_repo):
        process = _FakeCatProcess(_fake_cat_stdout(contents_by_tree))
        process_holder.append(process)
        return process

    monkeypatch.setattr(ADC, "_git_bytes", distinct_tree_per_batch)
    monkeypatch.setattr(ADC, "_start_cat_file_batch", start_cat)

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
    assert tree_batches == [
        tuple(f"docs/batch-{index}.md" for index in range(1, 6))
    ]
    assert len(process_holder) == 1
    assert len(process_holder[0].stdin.getvalue().splitlines()) == 5
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
    first_root = tmp_path / "offrepo-first"
    second_root = tmp_path / "offrepo-second"
    first = _external_file(first_root, "one/first.py", "first\n")
    second = _external_file(second_root, "two/second.py", "second\n")
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
    real_audit_snapshot = ADC._audit_snapshot
    real_landed_reference_matches = ADC._landed_reference_matches
    real_git_bytes = ADC._git_bytes
    symbolic_resolution_results: list[str] = []
    audit_main_refs: list[str] = []
    landed_main_refs: list[str] = []
    grep_refs: list[str] = []
    tree_refs: list[str] = []

    def record_checked_git(repo_path, *args):
        result = real_checked_git(repo_path, *args)
        if args == ("rev-parse", "--verify", "main^{commit}"):
            symbolic_resolution_results.append(result.strip())
        return result

    def record_audit_snapshot(
        repo_path,
        ref,
        excluded_prefixes,
        regenerable_prefixes,
        **kwargs,
    ):
        audit_main_refs.append(ref)
        return real_audit_snapshot(
            repo_path,
            ref,
            excluded_prefixes,
            regenerable_prefixes,
            **kwargs,
        )

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
        if args[0] == "--literal-pathspecs":
            tree_refs.append(args[5])
        return real_git_bytes(repo_path, *args)

    monkeypatch.setattr(ADC, "_checked_git", record_checked_git)
    monkeypatch.setattr(ADC, "_audit_snapshot", record_audit_snapshot)
    monkeypatch.setattr(
        ADC, "_landed_reference_matches", record_landed_reference_matches
    )
    monkeypatch.setattr(ADC, "_git_bytes", move_main_after_first_grep)

    report = ADC.audit_with_offrepo(
        repo, "main", offrepo_roots=(first_root, second_root)
    )

    assert symbolic_resolution_results == [snapshot_commit]
    assert audit_main_refs == landed_main_refs == [snapshot_commit]
    assert len(grep_refs) >= 2
    assert tree_refs
    assert set(grep_refs) == {snapshot_commit}
    assert set(tree_refs) == {snapshot_commit, lost}
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
    real_start_cat = ADC._start_cat_file_batch
    grep_calls = 0
    show_calls = 0
    cat_sessions = 0

    def count_grep(repo_path, *args):
        nonlocal grep_calls, show_calls
        if args and args[0] == "grep":
            grep_calls += 1
        if args and args[0] == "show":
            show_calls += 1
        return real_git_bytes(repo_path, *args)

    def count_cat_session(repo_path):
        nonlocal cat_sessions
        cat_sessions += 1
        return real_start_cat(repo_path)

    monkeypatch.setattr(ADC, "_git_bytes", count_grep)
    monkeypatch.setattr(ADC, "_start_cat_file_batch", count_cat_session)

    report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,))

    assert grep_calls == 1
    assert show_calls == 0
    assert cat_sessions == 1
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


def _mode_fixture(tmp_path):
    """到達不能 commit と landed 参照付きの外部 copy を用意する。"""
    repo = _repo(tmp_path)
    lost = _commit_files(repo, "doomed", {"tools/copy.py": "copy\n"})
    _delete_branch(repo, "doomed")
    root = tmp_path / "offrepo"
    external = _external_file(root, "wave/copy.py", "copy\n")
    _landed_reference(repo, external)
    return repo, root, lost, external


def _forbid_offrepo_io(*args, **kwargs):
    raise AssertionError("off must not touch offrepo I/O")


def test_explicit_off_ignores_env_and_preserves_core(tmp_path, monkeypatch, capsys):
    repo, root, lost, _ = _mode_fixture(tmp_path)
    monkeypatch.setenv(ADC.OFFREPO_ROOT_ENV, str(root))
    core = ADC.audit_with_offrepo(repo)
    report = ADC.audit_with_offrepo(repo, offrepo_scan="off")
    from dataclasses import replace
    assert core.findings and core.findings[0][0] == lost
    assert report == replace(core, offrepo_scan="off")
    real_get = os.environ.get

    def guarded_get(key, default=None):
        if key == ADC.OFFREPO_ROOT_ENV:
            raise AssertionError("off read the root environment key")
        return real_get(key, default)

    # Trap only this key; unrelated environment access remains real.
    monkeypatch.setattr(os.environ, "get", guarded_get)
    assert ADC.main(["--repo", str(repo), "--offrepo-scan", "off"]) == 1
    assert lost in capsys.readouterr().out


def test_explicit_off_touches_no_offrepo_io(tmp_path, monkeypatch):
    repo, root, _, _ = _mode_fixture(tmp_path)
    core = ADC.audit_with_offrepo(repo)
    assert core.findings
    for name in ("_validate_offrepo_roots", "_load_blob_metadata",
                 "_enumerate_offrepo_candidates", "_start_cat_file_batch"):
        monkeypatch.setattr(ADC, name, _forbid_offrepo_io)
    with monkeypatch.context() as patches:
        patches.setattr(ADC.os, "walk", _forbid_offrepo_io)
        patches.setattr(ADC.os, "scandir", _forbid_offrepo_io)
        report = ADC.audit_with_offrepo(repo, offrepo_roots=(root,), offrepo_scan="off")
    from dataclasses import replace
    assert report == replace(core, offrepo_scan="off")


def test_explicit_off_disclosure_is_distinct_from_missing_root(tmp_path, monkeypatch, capsys):
    repo, root, _, _ = _mode_fixture(tmp_path)
    monkeypatch.setenv(ADC.OFFREPO_ROOT_ENV, str(root))
    assert ADC.main(["--repo", str(repo), "--offrepo-scan", "off"]) == 1
    output = capsys.readouterr().out
    assert output.count("repo 外走査は明示 off") == 1
    assert "IZANAGI_DEV_WAVE_JOBS_DIR の指定も無視" in output
    assert "repo 外の同一実体は未確認" in output
    assert "findings は full なら抑止されうる (commit, path) 対を含みうる" in output
    assert "救出 triage は --offrepo-scan full --offrepo-root <root> を指定して単独実行する" in output
    assert "探索を未実施" not in output and "が未指定" not in output
    assert "repo 外の同一実体で抑止 0" in output
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV)
    assert ADC.main(["--repo", str(repo)]) == 1
    output = capsys.readouterr().out
    assert "探索を未実施" in output and "が未指定" in output
    assert "repo 外走査は明示 off" not in output


def test_explicit_full_suppresses_copy_that_off_reports(tmp_path):
    repo, root, lost, external = _mode_fixture(tmp_path)
    full = ADC.audit_with_offrepo(repo, offrepo_roots=(root,), offrepo_scan="full")
    off = ADC.audit_with_offrepo(repo, offrepo_roots=(root,), offrepo_scan="off")
    assert full.findings == []
    assert full.suppressions == [(lost, "tools/copy.py", external)]
    assert len(off.findings) == 1 and off.suppressions == []
    # Add an unsuppressed path and repeat against the same new snapshot.
    other = _commit_files(repo, "unrecovered", {"tools/remains.py": "unique\n"})
    _delete_branch(repo, "unrecovered")
    core = ADC.audit_with_offrepo(repo)
    full = ADC.audit_with_offrepo(repo, offrepo_roots=(root,), offrepo_scan="full")
    off = ADC.audit_with_offrepo(repo, offrepo_roots=(root,), offrepo_scan="off")
    def pairs(report):
        return {(commit, path) for commit, _, paths in report.findings for path in paths}
    assert pairs(full) == {(other, "tools/remains.py")}
    assert pairs(full) < pairs(off) == pairs(core)
    assert full.suppressions == [(lost, "tools/copy.py", external)]
    assert off.suppressions == [] and off.unreferenced_copies == []


@pytest.mark.parametrize("source", ["cli", "env"])
def test_explicit_full_matches_legacy_root_report(tmp_path, monkeypatch, capsys, source):
    repo, root, _, _ = _mode_fixture(tmp_path)
    assert ADC.audit_with_offrepo(repo, offrepo_roots=(root,)) == ADC.audit_with_offrepo(
        repo, offrepo_roots=(root,), offrepo_scan="full")
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    argv = ["--repo", str(repo)]
    if source == "cli":
        argv += ["--offrepo-root", str(root)]
    else:
        monkeypatch.setenv(ADC.OFFREPO_ROOT_ENV, str(root))
    assert ADC.main(argv) == 0
    legacy = capsys.readouterr().out
    assert ADC.main(argv + ["--offrepo-scan", "full"]) == 0
    explicit = capsys.readouterr().out
    def stable(output):
        return [line for line in output.splitlines()
                if "進捗" not in line and "elapsed_seconds=" not in line]
    assert stable(explicit) == stable(legacy)


@pytest.mark.parametrize("has_env", [False, True], ids=["no-env", "env"])
def test_explicit_off_with_cli_root_is_usage_error(tmp_path, monkeypatch, capsys, has_env):
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    if has_env:
        monkeypatch.setenv(ADC.OFFREPO_ROOT_ENV, str(tmp_path))
    monkeypatch.setattr(ADC, "audit_with_offrepo", _forbid_offrepo_io)
    with pytest.raises(SystemExit) as exc:
        ADC.main(["--offrepo-scan", "off", "--offrepo-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exc.value.code == 2 and "usage:" in captured.err
    assert "elapsed_seconds=" not in captured.out


@pytest.mark.parametrize("env_value", [None, ""], ids=["absent", "empty"])
def test_explicit_full_without_root_is_execution_failure(tmp_path, monkeypatch, capsys, env_value):
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    if env_value is not None:
        monkeypatch.setenv(ADC.OFFREPO_ROOT_ENV, env_value)
    monkeypatch.setattr(ADC, "_audit_snapshot", _forbid_offrepo_io)
    monkeypatch.setattr(ADC, "_checked_git", _forbid_offrepo_io)
    assert ADC.main(["--repo", str(tmp_path), "--offrepo-scan", "full"]) == 2
    captured = capsys.readouterr()
    assert "実行できません" in captured.err
    assert "--offrepo-scan full には --offrepo-root または IZANAGI_DEV_WAVE_JOBS_DIR が必要です" in captured.err
    assert sum(line.startswith("audit_dangling_commits: elapsed_seconds=")
               for line in captured.out.splitlines()) == 1
    assert "要確認" not in captured.out


def test_explicit_full_missing_root_preserves_elapsed_overrun(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)
    ticks = iter([0.0, ADC.AUDIT_ELAPSED_LIMIT_SECONDS + 1])
    monkeypatch.setattr(ADC.time, "monotonic", lambda: next(ticks))
    assert ADC.main(["--repo", str(tmp_path), "--offrepo-scan", "full"]) == 2
    lines = capsys.readouterr().out.splitlines()
    assert lines[-2].startswith("audit_dangling_commits: 所要上限超過 ")
    assert lines[-1].startswith("audit_dangling_commits: elapsed_seconds=")


def _run() -> int:
    """pytest fixtures を含む全 node を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
