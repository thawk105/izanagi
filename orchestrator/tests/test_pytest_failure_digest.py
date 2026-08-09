# -*- coding: utf-8 -*-
"""pytest failure digest の byte 会計・consumer・実 relay 結合を固定する。"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest


HERE = Path(__file__).resolve().parent
ORCHESTRATOR = HERE.parent
ROOT = ORCHESTRATOR.parent
START = "=== IZANAGI FAILURE DIGEST v1 BEGIN ==="
END = "=== IZANAGI FAILURE DIGEST v1 END ==="
RELAY_LIMIT = 64 * 1024
DIGEST_BUDGET = RELAY_LIMIT * 3 // 4
EXCERPT_BUDGET = 4 * 1024


def _load_conftest():
    name = "izanagi_failure_digest_conftest"
    spec = importlib.util.spec_from_file_location(name, HERE / "conftest.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


C = _load_conftest()


@pytest.fixture(autouse=True)
def _clear_isolated_failure_stash():
    C._FAILURE_REPORTS.clear()
    yield
    C._FAILURE_REPORTS.clear()


def _report(nodeid: str, source: str, *, failed: bool = True, when: str = "call"):
    return SimpleNamespace(
        nodeid=nodeid,
        longreprtext=source,
        failed=failed,
        when=when,
    )


def _stashed(nodeid: str, source: str, *, category: str = "failed", when: str = "call"):
    return C._StashedFailure(category, _report(nodeid, source, when=when))


def _escape_ascii_oracle(value: str) -> str:
    """production renderer を import しない test-side oracle。"""
    result: list[str] = []
    for char in value:
        codepoint = ord(char)
        if char == "\\":
            result.append(r"\x5c")
        elif 0x20 <= codepoint < 0x7f:
            result.append(char)
        elif codepoint <= 0xff:
            result.append(f"\\x{codepoint:02x}")
        elif codepoint <= 0xffff:
            result.append(f"\\u{codepoint:04x}")
        else:
            result.append(f"\\U{codepoint:08x}")
    return "".join(result)


def _render_failure_lines_oracle(source: str) -> str:
    lines = source.split("\n")
    if source.endswith("\n"):
        lines.pop()
    if not lines:
        lines = [""]
    rendered: list[str] = []
    for line in lines:
        escaped = _escape_ascii_oracle(line)
        if escaped.startswith("FAILED "):
            escaped = "! " + escaped
        rendered.append(f"> {escaped}\n")
    return "".join(rendered)


def _failure_excerpt_oracle(source: str) -> tuple[str, int]:
    used = len("> \n")
    retained_reversed: list[str] = []
    retained_bytes = 0
    have_selected = False
    first_line_prefix = ""
    first_line_neutralized = False
    for char in reversed(source):
        if char == "\n":
            width = len("\n> ") if have_selected else 0
            next_prefix = ""
            next_neutralized = False
        else:
            next_prefix = (char + first_line_prefix)[:len("FAILED ")]
            next_neutralized = next_prefix == "FAILED "
            width = len(_escape_ascii_oracle(char).encode("ascii"))
            if next_neutralized and not first_line_neutralized:
                width += len("! ")
            elif first_line_neutralized and not next_neutralized:
                width -= len("! ")
        if used + width > EXCERPT_BUDGET:
            break
        retained_reversed.append(char)
        retained_bytes += len(char.encode("utf-8"))
        used += width
        have_selected = True
        first_line_prefix = next_prefix
        first_line_neutralized = next_neutralized
    retained_reversed.reverse()
    excerpt = _render_failure_lines_oracle("".join(retained_reversed))
    assert len(excerpt.encode("ascii")) == used
    return excerpt, retained_bytes


def _retained_source_bytes_oracle(source: str) -> int:
    return _failure_excerpt_oracle(source)[1]


_FIELD_RE = re.compile(r"([a-z0-9_]+)=(\"(?:\\.|[^\"])*\"|\S+)")


def _parse_fields(line: str) -> dict[str, str]:
    fields = dict(_FIELD_RE.findall(line))
    if "nodeid" in fields:
        fields["nodeid"] = json.loads(fields["nodeid"])
    return fields


def _extract_digest(stdout: str) -> str:
    start = stdout.index(START)
    end = stdout.index(END, start) + len(END) + 1
    return stdout[start:end]


def _digest_entries(digest: str) -> list[dict[str, str]]:
    return [
        _parse_fields(line)
        for line in digest.splitlines()
        if line.startswith("IZANAGI_FAILURE rank=")
    ]


def _digest_excerpts(digest: str) -> dict[int, str]:
    pattern = re.compile(
        r"^--- IZANAGI FAILURE EXCERPT rank=(\d+) BEGIN ---\n"
        r"(.*?)"
        r"^--- IZANAGI FAILURE EXCERPT rank=\1 END ---\n",
        re.MULTILINE | re.DOTALL,
    )
    excerpts = {int(match.group(1)): match.group(2) for match in pattern.finditer(digest)}
    assert len(excerpts) == len(_digest_entries(digest))
    return excerpts


def _digest_account(digest: str) -> dict[str, str]:
    lines = [
        line for line in digest.splitlines()
        if line.startswith("IZANAGI_FAILURE_DIGEST_ACCOUNT ")
    ]
    assert len(lines) == 1
    return _parse_fields(lines[0])


def _manifest_sha256(expected: list[dict[str, object]]) -> str:
    if not expected:
        return "-"
    ordered = sorted(
        expected,
        key=lambda item: (
            item["nodeid"], item["when"], item["source_bytes"], item["sha256"],
        ),
    )
    canonical = "".join(
        json.dumps(
            {
                "nodeid": item["nodeid"],
                "when": item["when"],
                "source_bytes": item["source_bytes"],
                "sha256": item["sha256"],
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
        for item in ordered
    )
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _expected_item(
    nodeid: str,
    source: str,
    category: str = "failed",
    when: str = "call",
) -> dict[str, object]:
    raw = source.encode("utf-8")
    return {
        "nodeid": nodeid,
        "when": when,
        "category": category,
        "source": source,
        "source_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _assert_full_account_oracle(
    digest: str, expected: list[dict[str, object]], budget: int = DIGEST_BUDGET,
) -> None:
    entries = _digest_entries(digest)
    account = _digest_account(digest)
    expected_by_nodeid = {str(item["nodeid"]): item for item in expected}
    excerpts = _digest_excerpts(digest)
    selected_nodeids = [entry["nodeid"] for entry in entries]
    assert len(selected_nodeids) == len(set(selected_nodeids))
    assert set(selected_nodeids) <= set(expected_by_nodeid)
    selected = [expected_by_nodeid[nodeid] for nodeid in selected_nodeids]
    omitted = [item for item in expected if item["nodeid"] not in selected_nodeids]
    source_bytes = sum(int(item["source_bytes"]) for item in expected)
    retained_bytes = sum(
        _retained_source_bytes_oracle(str(item["source"])) for item in selected
    )
    failed = sum(item["category"] == "failed" for item in expected)
    assertions = {
        "failures": len(expected),
        "failed": failed,
        "errors": len(expected) - failed,
        "selected": len(selected),
        "omitted_failures": len(omitted),
        "source_bytes": source_bytes,
        "retained_bytes": retained_bytes,
        "omitted_bytes": source_bytes - retained_bytes,
        "budget_bytes": budget,
        "rendered_bytes": len(digest.encode("ascii")),
    }
    for field, value in assertions.items():
        assert int(account[field]) == value, (field, account[field], value)
    assert account["omitted_manifest_sha256"] == _manifest_sha256(omitted)
    for entry in entries:
        item = expected_by_nodeid[entry["nodeid"]]
        expected_excerpt, retained = _failure_excerpt_oracle(str(item["source"]))
        assert int(entry["source_bytes"]) == item["source_bytes"]
        assert int(entry["retained_bytes"]) == retained
        assert int(entry["omitted_bytes"]) == int(item["source_bytes"]) - retained
        assert entry["sha256"] == item["sha256"]
        assert excerpts[int(entry["rank"])] == expected_excerpt


def test_failure_digest_contains_nodeid_and_diagnostic_tail():
    sentinel = "truth_summary=末尾\\ok\x1b\r"
    source = "HEAD_ONLY_SENTINEL" + "Z" * 20_000 + "\n" + sentinel
    stashed = [_stashed("orchestrator/tests/test_target.py::test_failure", source)]
    digest = C._build_failure_digest(stashed, DIGEST_BUDGET)

    assert digest.startswith(START + "\n")
    assert digest.endswith(END + "\n")
    assert "orchestrator/tests/test_target.py::test_failure" in digest
    assert _escape_ascii_oracle(sentinel) in digest
    assert "HEAD_ONLY_SENTINEL" not in digest
    assert digest.encode("ascii").decode("ascii") == digest
    assert "\x1b" not in digest
    assert "\r" not in digest
    _assert_full_account_oracle(
        digest,
        [_expected_item("orchestrator/tests/test_target.py::test_failure", source)],
    )


def _finish_wrapper(config) -> None:
    wrapper = C.pytest_unconfigure(config)
    next(wrapper)
    with pytest.raises(StopIteration):
        next(wrapper)


def test_failure_digest_is_silent_for_nonfailures_worker_and_plain_import(
    capsys, tmp_path,
):
    calls: list[str] = []

    def called_loader() -> int:
        calls.append("loader")
        return DIGEST_BUDGET

    def called_builder(_reports, _budget) -> str:
        calls.append("builder")
        return "bad"

    def called_writer(_text) -> None:
        calls.append("writer")

    C._emit_failure_digest(
        [], budget_loader=called_loader, builder=called_builder, writer=called_writer,
    )
    assert calls == []

    # pass / skip / xfail / non-strict xpass と成功 collect を与える。stats は意図的に非空。
    for label in ("passed", "skipped", "xfail", "xpass"):
        C.pytest_runtest_logreport(_report(f"test_green.py::test_{label}", label, failed=False))
    C.pytest_collectreport(_report("test_green.py", "collect", failed=False, when="collect"))
    terminal = SimpleNamespace(stats={"passed": [object()], "skipped": [object()]})
    config = SimpleNamespace(
        pluginmanager=SimpleNamespace(getplugin=lambda _name: terminal),
    )
    _finish_wrapper(config)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    C.pytest_runtest_logreport(_report("test_worker.py::test_bad", "boom"))
    worker = SimpleNamespace(workerinput={}, pluginmanager=config.pluginmanager)
    _finish_wrapper(worker)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    # repo root 外 cwd・PYTHONPATH なしの plain runner で、default loader が
    # ModuleNotFoundError(name="tools") へ入り digest は無言 fail-open する。
    script = (
        "import importlib.util,pathlib,sys,types; "
        f"root=pathlib.Path({str(ROOT)!r}).resolve(); "
        "assert pathlib.Path.cwd().resolve()!=root; "
        "assert all(pathlib.Path(p or '.').resolve()!=root for p in sys.path); "
        f"p={str(HERE / 'conftest.py')!r}; "
        "s=importlib.util.spec_from_file_location('plain_conftest',p); "
        "m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; "
        "s.loader.exec_module(m); "
        "report=types.SimpleNamespace(nodeid='plain.py::test_bad',when='call',"
        "longreprtext='boom'); "
        "stashed=[m._StashedFailure('failed',report)]; "
        "caught=False; "
        "\ntry: m._load_failure_digest_budget()"
        "\nexcept ModuleNotFoundError as exc: caught=exc.name=='tools'"
        "\nassert caught"
        "\nm._emit_failure_digest(stashed)"
    )
    _assert_repo_external(tmp_path)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    returncode, stdout, stderr = _run_bounded_process(
        [sys.executable, "-c", script], env=env, timeout=10, cwd=tmp_path,
    )
    assert returncode == 0, stderr.decode("utf-8", errors="replace")
    assert stdout == b""
    assert stderr == b""


def test_failed_and_collect_reports_are_stashed_independently_of_terminal_stats(capsys):
    run_report = _report("test_custom.py::test_call", "call failed")
    collect_report = _report(
        "test_collect.py", "collection failed", when="collect",
    )
    C.pytest_runtest_logreport(run_report)
    C.pytest_collectreport(collect_report)
    terminal = SimpleNamespace(stats={"custom": [run_report], "passed": [object()]})
    config = SimpleNamespace(
        pluginmanager=SimpleNamespace(getplugin=lambda _name: terminal),
    )

    _finish_wrapper(config)
    digest = capsys.readouterr().out
    account = _digest_account(digest)
    assert int(account["failures"]) == 2
    assert int(account["failed"]) == 1
    assert int(account["errors"]) == 1
    assert "test_custom.py::test_call" in digest
    assert "test_collect.py" in digest
    _assert_full_account_oracle(
        digest,
        [
            _expected_item("test_custom.py::test_call", "call failed"),
            _expected_item(
                "test_collect.py", "collection failed", category="error", when="collect",
            ),
        ],
    )


def test_failure_digest_budget_and_omission_accounting_are_exact():
    expected: list[dict[str, object]] = []
    stashed = []
    specifications = [
        *(('orchestrator/tests/a.py', index, 13_000 + index) for index in range(22)),
        ("orchestrator/tests/b.py", 0, 12_900),
        ("orchestrator/tests/c.py", 0, 12_800),
    ]
    for path, index, size in specifications:
        nodeid = f"{path}::test_case_{index:02d}"
        suffix = f" truth_summary={path}:{index:02d}"
        source = "S" * (size - len(suffix)) + suffix
        stashed.append(_stashed(nodeid, source))
        expected.append(_expected_item(nodeid, source))

    digest = C._build_failure_digest(stashed, DIGEST_BUDGET)
    assert C._build_failure_digest(list(reversed(stashed)), DIGEST_BUDGET) == digest
    entries = _digest_entries(digest)
    selected = {entry["nodeid"] for entry in entries}
    assert 0 < len(entries) < len(expected)
    assert len(digest.encode("ascii")) <= DIGEST_BUDGET
    assert "orchestrator/tests/b.py::test_case_00" in selected
    assert "orchestrator/tests/c.py::test_case_00" in selected
    assert all(int(entry["rendered_excerpt_bytes"]) <= EXCERPT_BUDGET for entry in entries)
    _assert_full_account_oracle(digest, expected)


def test_failure_digest_selection_renders_each_candidate_block_once():
    stashed = [
        _stashed(
            f"orchestrator/tests/many.py::test_case_{index:04d}",
            f"case={index:04d} " + "X" * 8_000,
        )
        for index in range(100)
    ]
    calls: dict[str, int] = {}
    manifest_calls: list[tuple[str, ...]] = []

    def recording_renderer(item, rank):
        calls[item.nodeid] = calls.get(item.nodeid, 0) + 1
        return C._render_failure_block(item, rank)

    def recording_manifest(items):
        manifest_calls.append(tuple(item.nodeid for item in items))
        return C._omitted_manifest_sha256(items)

    digest = C._build_failure_digest(
        stashed,
        DIGEST_BUDGET,
        block_renderer=recording_renderer,
        manifest_renderer=recording_manifest,
    )

    assert START in digest
    assert 1 < len(calls) < len(stashed)
    assert set(calls.values()) == {1}
    assert len(manifest_calls) == 1
    assert len(manifest_calls[0]) == int(
        _digest_account(digest)["omitted_failures"],
    )


def _process_group_exists(process_group: int) -> bool:
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_process_group_gone(process_group: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _process_group_exists(process_group):
            return True
        time.sleep(0.05)
    return not _process_group_exists(process_group)


def _run_bounded_process(
    command: list[str],
    *,
    env: dict[str, str],
    timeout: float,
    cwd: Path = ROOT,
):
    process_env = env.copy()
    process_env["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=process_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        process_group = process.pid
        try:
            os.killpg(process_group, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process_group, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate(timeout=5)
        assert _wait_process_group_gone(process_group, 3), (
            f"timeout cleanup 後も process group {process_group} が残存"
        )
        raise AssertionError(
            f"nested pytest timeout: command={command!r} "
            f"stdout_bytes={len(stdout)} stderr_bytes={len(stderr)}"
        ) from exc
    return process.returncode, stdout, stderr


def _isolated_pytest_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    for name in tuple(env):
        if name.startswith("PYTEST_XDIST_"):
            env.pop(name, None)
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT), pythonpath] if pythonpath else [str(ROOT)],
    )
    return env


def _assert_repo_external(path: Path) -> None:
    resolved = path.resolve()
    repo = ROOT.resolve()
    assert not resolved.is_relative_to(repo), (
        f"一時 root はrepo外でなければならない: {resolved}"
    )


def _copy_real_conftest(directory: Path) -> Path:
    source = HERE / "conftest.py"
    copied = directory / "conftest.py"
    shutil.copyfile(source, copied)
    return copied


def _assert_copied_conftest_matches_real_after_run(copied: Path) -> None:
    assert copied.read_bytes() == (HERE / "conftest.py").read_bytes()


def test_real_pytest_end_states_have_exact_digest_presence(tmp_path):
    directory = tmp_path / "failure-digest-states"
    directory.mkdir()
    _assert_repo_external(directory)
    copied_conftest = _copy_real_conftest(directory)
    green_file = directory / "test_green_states.py"
    strict_xpass_file = directory / "test_strict_xpass.py"
    collect_error_file = directory / "test_collect_error.py"
    empty_directory = directory / "empty"
    empty_directory.mkdir()
    green_file.write_text(
        """\
import pytest

def test_pass():
    pass

def test_skip():
    pytest.skip("expected")

@pytest.mark.xfail(reason="expected")
def test_xfail():
    assert False

@pytest.mark.xfail(reason="non-strict")
def test_non_strict_xpass():
    pass
""",
        encoding="utf-8",
    )
    strict_xpass_file.write_text(
        """\
import pytest

@pytest.mark.xfail(reason="strict", strict=True)
def test_strict_xpass():
    pass
""",
        encoding="utf-8",
    )
    collect_error_file.write_text(
        "raise RuntimeError('collect boom')\n",
        encoding="utf-8",
    )
    env = _isolated_pytest_env()
    basetemp = tmp_path / "failure-digest-states-basetemp"
    _assert_repo_external(basetemp)

    def run(arguments: list[str]) -> tuple[int, bytes, bytes]:
        return _run_bounded_process(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                f"--rootdir={directory}",
                f"--basetemp={basetemp}",
                *arguments,
            ],
            env=env,
            timeout=12,
        )

    silent_runs = [
        (run([str(green_file)]), 0, "pass/skip/xfail/xpass"),
        (run([str(empty_directory)]), 5, "0 collected"),
        (run(["--collect-only", str(green_file)]), 0, "collect-only success"),
    ]
    digest_runs = [
        (run([str(strict_xpass_file)]), 1, "strict xpass"),
        (run(["--collect-only", str(collect_error_file)]), 2, "collect error"),
    ]

    marker = START.encode("ascii")
    error_marker = b"=== IZANAGI FAILURE DIGEST v1 ERROR"
    for (returncode, stdout, stderr), expected_rc, label in silent_runs:
        assert returncode == expected_rc, (label, returncode, stderr[-2000:])
        assert marker not in stdout, label
        assert marker not in stderr, label
        assert error_marker not in stdout, label
        assert error_marker not in stderr, label
    for (returncode, stdout, stderr), expected_rc, label in digest_runs:
        assert returncode == expected_rc, (label, returncode, stderr[-2000:])
        # marker の出現が、コピーした実 conftest hook の pytest による
        # 自動 discovery と実行を示す behavioral proof である。
        assert stdout.count(marker) == 1, label
        assert END.encode("ascii") in stdout, label
        assert marker not in stderr, label
    _assert_copied_conftest_matches_real_after_run(copied_conftest)


def _e2e_message(case: int) -> str:
    sentinel = f"truth_summary case={case:02d} sentinel=TAIL_OK_{case:02d}"
    prefix = f"case={case:02d} diagnostic="
    padding = 16 * 1024 - len((prefix + "\n" + sentinel).encode("utf-8"))
    assert padding >= 0
    message = prefix + "D" * padding + "\n" + sentinel
    assert len(message.encode("utf-8")) == 16 * 1024
    return message


@dataclass(frozen=True)
class _E2EResult:
    stdout: str
    stderr: str
    digest: str
    expected: list[dict[str, object]]


@pytest.fixture(scope="module")
def failure_digest_e2e(tmp_path_factory) -> _E2EResult:
    case_count = 24
    directory = tmp_path_factory.mktemp("failure-digest-e2e")
    _assert_repo_external(directory)
    copied_conftest = _copy_real_conftest(directory)
    test_file = directory / "test_many_failures.py"
    sidecar = tmp_path_factory.mktemp("failure-digest-sidecar")
    _assert_repo_external(sidecar)
    source = f'''\
import json
import os
from pathlib import Path
import sys

import pytest

PAYLOAD_BYTES = 16 * 1024


def _message(case):
    sentinel = f"truth_summary case={{case:02d}} sentinel=TAIL_OK_{{case:02d}}"
    prefix = f"case={{case:02d}} diagnostic="
    padding = PAYLOAD_BYTES - len((prefix + "\\n" + sentinel).encode("utf-8"))
    message = prefix + "D" * padding + "\\n" + sentinel
    assert len(message.encode("utf-8")) == PAYLOAD_BYTES
    return message


@pytest.mark.parametrize("case", range({case_count}))
def test_many_failures(case, request):
    worker = request.config.workerinput
    record = {{
        "case": case,
        "workerid": worker["workerid"],
        "sysplatform": sys.platform,
        "version_info": list(sys.version_info[:3]),
        "executable": sys.executable,
    }}
    (Path(os.environ["IZANAGI_E2E_SIDECAR"]) / f"{{case:02d}}.json").write_text(
        json.dumps(record, sort_keys=True), encoding="utf-8",
    )
    print("C" * 8192 + f" captured={{case:02d}}")
    pytest.fail(_message(case), pytrace=False)
'''
    test_file.write_text(source, encoding="utf-8")
    basetemp = tmp_path_factory.mktemp("failure-digest-inner") / "basetemp"
    _assert_repo_external(basetemp)
    env = _isolated_pytest_env()
    env["IZANAGI_E2E_SIDECAR"] = str(sidecar)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-n",
        "2",
        "--dist",
        "loadgroup",
        "-p",
        "no:cacheprovider",
        "--color=no",
        f"--rootdir={directory}",
        f"--basetemp={basetemp}",
        str(test_file),
    ]
    returncode, stdout_raw, stderr_raw = _run_bounded_process(
        command, env=env, timeout=15,
    )
    _assert_copied_conftest_matches_real_after_run(copied_conftest)

    stdout = stdout_raw.decode("utf-8", errors="replace")
    stderr = stderr_raw.decode("utf-8", errors="replace")
    assert returncode == 1, (
        f"inner rc={returncode} stdout_bytes={len(stdout_raw)} "
        f"stderr_bytes={len(stderr_raw)} stderr_tail={stderr[-2000:]}"
    )
    # digest marker は、`-p` なしでコピーした実 conftest hook が
    # pytest の自動 discovery 経由で走った behavioral proof である。
    assert stdout.count(START) == 1
    assert stdout.count(END) == 1
    digest = _extract_digest(stdout)
    relative = test_file.relative_to(directory).as_posix()
    records = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(sidecar.glob("*.json"))
    ]
    assert [record["case"] for record in records] == list(range(case_count))
    expected = [
        _expected_item(
            f"{relative}::test_many_failures[{record['case']}]",
            (
                f"[{record['workerid']}] {record['sysplatform']} -- Python "
                f"{'.'.join(str(part) for part in record['version_info'])} "
                f"{record['executable']}\n{_e2e_message(record['case'])}"
            ),
        )
        for record in records
    ]
    for record, item in zip(records, expected):
        assert re.fullmatch(r"gw[0-9]+", record["workerid"])
        assert re.fullmatch(r"[^\r\n]+", record["sysplatform"])
        assert (
            isinstance(record["version_info"], list)
            and len(record["version_info"]) == 3
            and all(type(part) is int for part in record["version_info"])
        )
        assert re.fullmatch(r"[^\r\n]+", record["executable"])
        banner = str(item["source"]).split("\n", 1)[0]
        assert re.fullmatch(
            r"\[gw[0-9]+\] [^\r\n]+ -- Python [0-9]+\.[0-9]+\.[0-9]+ [^\r\n]+",
            banner,
        )
    return _E2EResult(stdout, stderr, digest, expected)


def test_e2e_real_conftest_digest_has_real_failures_and_exact_account(
    failure_digest_e2e,
):
    result = failure_digest_e2e
    stdout_bytes = result.stdout.encode("utf-8")
    digest_bytes = result.digest.encode("ascii")
    start_offset = stdout_bytes.index(START.encode("ascii"))
    entries = _digest_entries(result.digest)

    assert start_offset > RELAY_LIMIT
    assert 0 < len(entries) < len(result.expected)
    real_nodeids = {item["nodeid"] for item in result.expected}
    assert all(entry["nodeid"] in real_nodeids for entry in entries)
    for entry in entries:
        case = int(re.search(r"\[(\d+)\]$", entry["nodeid"]).group(1))
        assert f"truth_summary case={case:02d} sentinel=TAIL_OK_{case:02d}" in result.digest
    assert len(digest_bytes) <= DIGEST_BUDGET
    assert len(stdout_bytes[start_offset:]) < RELAY_LIMIT
    assert result.stdout.endswith(END + "\n")
    assert "short test summary info" in result.stdout[:start_offset]
    _assert_full_account_oracle(result.digest, result.expected)


def test_failure_digest_budget_is_bound_to_dispatch_limit(monkeypatch):
    from tools.pegasus import dispatch_compute

    DEFAULT_FAILURE_RELAY_LIMIT_BYTES = dispatch_compute.DEFAULT_FAILURE_RELAY_LIMIT_BYTES
    assert DEFAULT_FAILURE_RELAY_LIMIT_BYTES == 64 * 1024
    assert C._load_failure_digest_budget() == DEFAULT_FAILURE_RELAY_LIMIT_BYTES * 3 // 4
    assert C._load_failure_digest_budget() == 49_152
    # loader に引数 seam はなく、実 module 定数との動的な導出関係を検査するには
    # module attribute の一時差し替えが唯一の非ファイル変更 seam である。
    alternate_limit = DEFAULT_FAILURE_RELAY_LIMIT_BYTES + 4 * 1024
    monkeypatch.setattr(
        dispatch_compute, "DEFAULT_FAILURE_RELAY_LIMIT_BYTES", alternate_limit,
    )
    assert C._load_failure_digest_budget() == alternate_limit * 3 // 4


def test_failure_digest_exception_boundaries_preserve_pytest_outcome(capsys):
    stashed = [_stashed("test_failure.py::test_bad", "boom")]
    writes: list[str] = []

    # wrapper の通常経路が実 writer まで結線されていることを固定する。
    C._FAILURE_REPORTS.extend(stashed)
    _finish_wrapper(SimpleNamespace())
    captured = capsys.readouterr()
    assert captured.out.startswith(START + "\n")
    assert captured.out.endswith(END + "\n")
    assert captured.err == ""

    def runtime_builder(_reports, _budget):
        raise RuntimeError("volatile payload must not be copied")

    C._emit_failure_digest(stashed, builder=runtime_builder, writer=writes.append)
    assert writes == [
        "=== IZANAGI FAILURE DIGEST v1 ERROR exception=RuntimeError ===\n"
    ]

    def missing_tools():
        raise ModuleNotFoundError("tools unavailable", name="tools")

    writes.clear()
    C._emit_failure_digest(stashed, budget_loader=missing_tools, writer=writes.append)
    assert writes == []

    def missing_internal_dependency():
        raise ModuleNotFoundError("internal unavailable", name="relay_dependency")

    C._emit_failure_digest(
        stashed, budget_loader=missing_internal_dependency, writer=writes.append,
    )
    assert writes == [
        "=== IZANAGI FAILURE DIGEST v1 ERROR exception=ModuleNotFoundError ===\n"
    ]

    def broken_internal_import():
        raise ImportError("dispatch_compute import broke")

    writes.clear()
    C._emit_failure_digest(
        stashed, budget_loader=broken_internal_import, writer=writes.append,
    )
    assert writes == [
        "=== IZANAGI FAILURE DIGEST v1 ERROR exception=ImportError ===\n"
    ]

    def broken_budget_loader():
        raise ValueError("bad budget")

    writes.clear()
    C._emit_failure_digest(
        stashed, budget_loader=broken_budget_loader, writer=writes.append,
    )
    assert writes == [
        "=== IZANAGI FAILURE DIGEST v1 ERROR exception=ValueError ===\n"
    ]

    def broken_writer(_text):
        raise OSError("closed")

    C._emit_failure_digest(stashed, writer=broken_writer)

    class SentinelBase(BaseException):
        pass

    sentinel_base = SentinelBase()

    def base_builder(_reports, _budget):
        raise sentinel_base

    with pytest.raises(SentinelBase) as raised:
        C._emit_failure_digest(stashed, builder=base_builder)
    assert raised.value is sentinel_base

    class InnerSentinel(Exception):
        pass

    for config in (SimpleNamespace(), SimpleNamespace(workerinput={})):
        C._FAILURE_REPORTS.clear()
        wrapper = C.pytest_unconfigure(config)
        next(wrapper)
        sentinel = InnerSentinel()
        with pytest.raises(InnerSentinel) as raised:
            wrapper.throw(sentinel)
        assert raised.value is sentinel


def test_inner_hook_exception_wins_over_emitter_baseexception_via_pluggy():
    import pluggy

    hookspec = pluggy.HookspecMarker("pytest")
    hookimpl = pluggy.HookimplMarker("pytest")

    class Spec:
        @hookspec
        def pytest_unconfigure(self, config):
            """Minimal pytest hook specification for wrapper ordering."""

    class InnerSentinel(Exception):
        pass

    class EmitterSentinel(BaseException):
        pass

    inner_sentinel = InnerSentinel()
    emitter_sentinel = EmitterSentinel()

    class InnerPlugin:
        @hookimpl
        def pytest_unconfigure(self, config):
            raise inner_sentinel

    class ExplodingReport:
        nodeid = "test_failure.py::test_bad"
        when = "call"

        @property
        def longreprtext(self):
            raise emitter_sentinel

    manager = pluggy.PluginManager("pytest")
    manager.add_hookspecs(Spec)
    manager.register(C, name="failure-digest")
    manager.register(InnerPlugin(), name="inner")
    C._FAILURE_REPORTS.append(C._StashedFailure("failed", ExplodingReport()))

    with pytest.raises(InnerSentinel) as raised:
        manager.hook.pytest_unconfigure(config=SimpleNamespace())
    assert raised.value is inner_sentinel
    assert C._FAILURE_REPORTS == []


def test_nested_pytest_main_currently_clears_outer_failure_stash(tmp_path, capsys):
    inner_test = tmp_path / "test_inner_green.py"
    inner_test.write_text("def test_inner_green():\n    pass\n", encoding="utf-8")
    C.pytest_runtest_logreport(
        _report("test_outer.py::test_outer_failure", "outer failure"),
    )
    assert len(C._FAILURE_REPORTS) == 1

    returncode = pytest.main(
        ["-q", "-p", "no:cacheprovider", str(inner_test)],
        plugins=[C],
    )

    assert returncode == pytest.ExitCode.OK
    assert C._FAILURE_REPORTS == []
    captured = capsys.readouterr()
    assert START not in captured.out
    assert START not in captured.err


def _relay_prefix(output: str, depth: int) -> str:
    prefix = "| " * depth
    return "".join(prefix + line for line in output.splitlines(keepends=True))


def test_digest_excerpt_cannot_inject_mutation_failed_nodes():
    from tools.mutation_harness import _failed_nodes

    actual = "orchestrator/tests/actual.py::test_real"
    decoy = "orchestrator/tests/decoy.py::test_fake"
    source = "héader\x00\\\nFAILED " + decoy
    digest = C._build_failure_digest(
        [_stashed("orchestrator/tests/source.py::test_source", source)],
        DIGEST_BUDGET,
    )
    assert "\n> h\\xe9ader\\x00\\x5c\n> ! FAILED " + decoy + "\n" in digest
    _assert_full_account_oracle(
        digest,
        [_expected_item("orchestrator/tests/source.py::test_source", source)],
    )
    output = f"FAILED {actual} - AssertionError\n" + digest
    expected = [actual]
    for depth in (0, 1, 2):
        assert _failed_nodes(_relay_prefix(output, depth), ROOT) == expected


def test_real_dispatch_relay_preserves_complete_e2e_digest(
    failure_digest_e2e, capsys,
):
    from tools.pegasus import dispatch_compute

    result = failure_digest_e2e
    stdout_bytes = result.stdout.encode("utf-8")
    record = {
        "path": "/scheduler/stdout",
        "size": len(stdout_bytes),
        "omitted_bytes": 0,
        "tail": result.stdout,
    }
    dispatch_compute._relay_scheduler_logs(
        record,
        None,
        request_id="failure-digest-e2e",
        successful=False,
    )
    relayed = capsys.readouterr().out
    start = relayed.index("| " + START)
    end = relayed.index("| " + END, start) + len("| " + END) + 1
    relayed_digest = relayed[start:end]
    unprefixed = "".join(
        line[2:] if line.startswith("| ") else line
        for line in relayed_digest.splitlines(keepends=True)
    )
    producer_digest_bytes = len(result.digest.encode("ascii"))
    prefixed_digest_bytes = len(relayed_digest.encode("utf-8"))
    relay_display_bytes = len(relayed.encode("utf-8"))
    assert unprefixed == result.digest, (
        f"producer_stdout_bytes={len(stdout_bytes)} "
        f"producer_digest_bytes={producer_digest_bytes} "
        f"prefixed_digest_bytes={prefixed_digest_bytes} "
        f"relay_display_bytes={relay_display_bytes}"
    )
    assert prefixed_digest_bytes == (
        producer_digest_bytes + 2 * len(result.digest.splitlines())
    )
    assert relay_display_bytes > prefixed_digest_bytes
    assert relayed.count("| " + START) == 1
    assert relayed.count("| " + END) == 1


def test_real_dispatch_relay_tail_boundaries_and_post_digest_loss(capsys):
    from tools.pegasus import dispatch_compute

    def relay_once(text: str, request_id: str) -> tuple[str, str]:
        raw = text.encode("utf-8")
        dispatch_compute._relay_scheduler_logs(
            {
                "path": "/scheduler/stdout",
                "size": len(raw),
                "omitted_bytes": 0,
                "tail": text,
            },
            None,
            request_id=request_id,
            successful=False,
        )
        captured = capsys.readouterr()
        assert captured.err == ""
        begin_end = captured.out.index("\n") + 1
        end_frame = f"[Pegasus dispatch] request {request_id} child stdout end\n"
        assert captured.out.endswith(end_frame)
        prefixed = captured.out[begin_end:-len(end_frame)]
        unprefixed = "".join(
            line[2:] if line.startswith("| ") else line
            for line in prefixed.splitlines(keepends=True)
        )
        return captured.out, unprefixed

    exact = "E" * (RELAY_LIMIT - 1) + "\n"
    exact_relay, exact_unprefixed = relay_once(exact, "exact-limit")
    assert len(exact.encode("ascii")) == RELAY_LIMIT
    assert "omitted_bytes=" not in exact_relay.splitlines()[0]
    assert exact_unprefixed == exact

    boundary_digest = START + "\n> boundary payload\n" + END + "\n"
    head = "H" * 101
    for delta in (-1, 0, 1):
        after_size = RELAY_LIMIT - len(boundary_digest.encode("ascii")) + delta
        after = "T" * (after_size - 1) + "\n"
        source = head + boundary_digest + after
        _relayed, unprefixed = relay_once(source, f"boundary-{delta}")
        assert unprefixed == source.encode("ascii")[-RELAY_LIMIT:].decode("ascii")
        if delta <= 0:
            assert START in unprefixed
            assert END in unprefixed
        else:
            assert START not in unprefixed
            assert END in unprefixed

    post_digest = boundary_digest + "Z" * (RELAY_LIMIT - 1) + "\n"
    _relayed, post_unprefixed = relay_once(post_digest, "post-digest")
    assert post_unprefixed == post_digest[-RELAY_LIMIT:]
    assert START not in post_unprefixed
    assert END not in post_unprefixed


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
