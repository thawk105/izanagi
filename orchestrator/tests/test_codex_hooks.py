# -*- coding: utf-8 -*-
"""Codex hook live gate の判定 seam と fail-closed wrapper の単体テスト。"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
_CHECKER_PATH = _REPO / "tools" / "check_codex_hooks.py"
_SPEC = importlib.util.spec_from_file_location("check_codex_hooks_for_test", _CHECKER_PATH)
assert _SPEC and _SPEC.loader
CH = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(CH)


def _expectations():
    repo = Path("/tmp/codex-hook-seam/repo")
    cwd = repo / "sub" / "deeper"
    return {
        tool: CH._expectation(tool, repo, cwd, "0123456789abcdef")
        for tool in CH.TOOLS
    }


def _argv(expected):
    return CH.build_codex_argv(Path("/opt/codex"), Path(expected.cwd), "probe")


def _events(expected, *, final_only=False, omit_protected=False):
    refusal = (
        f"{CH.BLOCKED_MARKER}: {CH.HANDLER_MARKERS[expected.tool]} test denial"
    )
    if final_only:
        return (
            {
                "type": "item.completed",
                "item": {"id": "final", "type": "agent_message", "text": refusal},
            },
            {"type": "turn.completed", "usage": {}},
        )
    if expected.tool == "apply_patch":
        allowed_item = {
            "id": "allowed-call",
            "type": "file_change",
            "changes": [{"path": expected.allowed_path, "kind": "add"}],
        }
        protected_item = {
            "id": "protected-call",
            "type": "file_change",
            "changes": [{"path": expected.protected_path, "kind": "add"}],
        }
    else:
        allowed_item = {
            "id": "allowed-call",
            "type": "command_execution",
            "command": CH._bash_probe_command(expected, protected=False),
        }
        protected_item = {
            "id": "protected-call",
            "type": "command_execution",
            "command": CH._bash_probe_command(expected, protected=True),
        }
    completed = dict(allowed_item)
    completed["status"] = "completed"
    if expected.tool == "Bash":
        completed["exit_code"] = 0
    events = [
        {"type": "item.started", "item": allowed_item},
        {"type": "item.completed", "item": completed},
    ]
    if not omit_protected:
        events.append({"type": "item.started", "item": protected_item})
    events.extend((
        {"type": "error", "message": refusal},
        {"type": "turn.completed", "usage": {}},
    ))
    return tuple(events)


def _result(expected, *, final_only=False, omit_protected=False, failure=None):
    argv = _argv(expected)
    return CH.ProbeResult(
        tool=expected.tool,
        argv=argv,
        returncode=0,
        failure=failure,
        events=_events(
            expected, final_only=final_only, omit_protected=omit_protected
        ),
        stderr="",
        allowed_bytes=(expected.allowed_marker + "\n").encode(),
        protected_exists=False,
    )


def _bundle():
    expected = _expectations()
    argv = {tool: _argv(item) for tool, item in expected.items()}
    results = {tool: _result(item) for tool, item in expected.items()}
    return expected, argv, results


def _rc(expected, argv, results, *, config_valid=True):
    return CH.decision_rc(
        config_valid=config_valid,
        expectations=expected,
        results=results,
        argv_by_tool=argv,
    )


def test_complete_live_evidence_is_the_only_positive_control():
    expected, argv, results = _bundle()
    assert _rc(expected, argv, results) == 0


def test_config_presence_alone_is_nonzero():
    expected, argv, _ = _bundle()
    assert _rc(expected, argv, {}) != 0


def test_protected_absence_alone_is_nonzero():
    expected, argv, results = _bundle()
    empty = {
        tool: result._replace(
            events=({"type": "turn.completed", "usage": {}},),
            protected_exists=False,
        )
        for tool, result in results.items()
    }
    assert _rc(expected, argv, empty) != 0


def test_final_message_refusal_alone_is_nonzero():
    expected, argv, _ = _bundle()
    results = {
        tool: _result(item, final_only=True) for tool, item in expected.items()
    }
    assert _rc(expected, argv, results) != 0


def test_one_tool_only_is_nonzero():
    expected, argv, results = _bundle()
    assert _rc(expected, argv, {"apply_patch": results["apply_patch"]}) != 0


def test_tool_untried_is_nonzero():
    expected, argv, results = _bundle()
    results["Bash"] = _result(expected["Bash"], omit_protected=True)
    assert _rc(expected, argv, results) != 0


def test_bash_diagnostic_spoof_command_is_nonzero():
    expected, argv, results = _bundle()
    bash_expected = expected["Bash"]
    spoof = (
        f"printf '%s\\n' '{CH.BLOCKED_MARKER}: "
        f"{CH.HANDLER_MARKERS['Bash']}'; : # "
        f"{bash_expected.protected_rel} {bash_expected.protected_marker}"
    )
    events = list(results["Bash"].events)
    protected_index = next(
        index for index, event in enumerate(events)
        if event.get("type") == "item.started"
        and event.get("item", {}).get("id") == "protected-call"
    )
    event = dict(events[protected_index])
    item = dict(event["item"])
    item["command"] = spoof
    event["item"] = item
    events[protected_index] = event
    results["Bash"] = results["Bash"]._replace(events=tuple(events))
    assert _rc(expected, argv, results) != 0


def test_diagnostic_outside_protected_window_is_nonzero():
    for placement in ("before", "after"):
        expected, argv, results = _bundle()
        events = list(results["Bash"].events)
        diagnostic = next(event for event in events if event.get("type") == "error")
        events.remove(diagnostic)
        protected_index = next(
            index for index, event in enumerate(events)
            if event.get("type") == "item.started"
            and event.get("item", {}).get("id") == "protected-call"
        )
        if placement == "before":
            events.insert(protected_index, diagnostic)
        else:
            events.append(diagnostic)
        results["Bash"] = results["Bash"]._replace(events=tuple(events))
        assert _rc(expected, argv, results) != 0, placement


def test_unexpected_tool_call_is_nonzero():
    expected, argv, results = _bundle()
    events = list(results["Bash"].events)
    events.insert(2, {
        "type": "item.started",
        "item": {"id": "unexpected", "type": "command_execution", "command": "true"},
    })
    results["Bash"] = results["Bash"]._replace(events=tuple(events))
    assert _rc(expected, argv, results) != 0


def test_auth_quota_and_timeout_are_each_nonzero():
    for failure in ("auth", "quota", "timeout"):
        expected, argv, results = _bundle()
        results["apply_patch"] = results["apply_patch"]._replace(
            failure=failure,
            returncode=None if failure == "timeout" else 0,
        )
        assert _rc(expected, argv, results) != 0, failure


def test_production_argv_trust_bypass_mutation_is_nonzero():
    expected, argv, results = _bundle()
    mutated = list(argv["apply_patch"])
    mutated.insert(-1, CH.TRUST_BYPASS_FLAG)
    argv["apply_patch"] = tuple(mutated)
    results["apply_patch"] = results["apply_patch"]._replace(
        argv=tuple(mutated)
    )
    assert _rc(expected, argv, results) != 0


def test_config_preflight_cannot_be_replaced_by_live_evidence():
    expected, argv, results = _bundle()
    assert _rc(expected, argv, results, config_valid=False) != 0


def test_codex_guard_maps_only_zero_and_two_to_themselves():
    bash = shutil.which("bash")
    assert bash, "bash が必要"
    source = _REPO / "hooks" / "codex_guard.sh"
    with tempfile.TemporaryDirectory(prefix="codex-guard-test-") as temp_name:
        hooks = Path(temp_name) / "hooks"
        hooks.mkdir()
        wrapper = hooks / "codex_guard.sh"
        shutil.copy2(source, wrapper)
        guard = hooks / "guard_write.py"
        for source_rc, expected_rc in ((0, 0), (2, 2), (1, 2), (3, 2), (70, 2)):
            guard.write_text(
                f"import sys\nsys.stdin.read()\nraise SystemExit({source_rc})\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [bash, os.fspath(wrapper), "write"],
                input="{}", text=True, capture_output=True, check=False,
            )
            assert completed.returncode == expected_rc, (
                source_rc, completed.returncode, completed.stderr
            )
        assert subprocess.run(
            [bash, os.fspath(wrapper), "unknown"],
            input="{}", text=True, capture_output=True, check=False,
        ).returncode == 2
        assert subprocess.run(
            [bash, os.fspath(wrapper), "bash"],
            input="{}", text=True, capture_output=True, check=False,
        ).returncode == 2
        assert subprocess.run(
            [bash, os.fspath(wrapper), "write"],
            input="{}", text=True, capture_output=True, check=False,
            env={"PATH": ""},
        ).returncode == 2


def test_bootstrap_maps_git_present_bash_missing_to_two():
    shell = shutil.which("sh")
    assert shell, "POSIX sh が必要"
    with tempfile.TemporaryDirectory(prefix="codex-bootstrap-test-") as temp_name:
        root = Path(temp_name) / "repo"
        hooks = root / "hooks"
        bin_dir = Path(temp_name) / "bin"
        hooks.mkdir(parents=True)
        bin_dir.mkdir()
        (hooks / "codex_guard.sh").write_text("", encoding="utf-8")
        fake_git = bin_dir / "git"
        fake_git.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$FAKE_REPO_ROOT\"\n",
            encoding="utf-8",
        )
        fake_git.chmod(0o755)
        assert shutil.which("git", path=os.fspath(bin_dir)) == os.fspath(fake_git)
        config = json.loads((_REPO / ".codex" / "hooks.json").read_text())
        commands = [
            hook["command"]
            for entry in config["hooks"]["PreToolUse"]
            for hook in entry["hooks"]
        ]
        assert len(commands) == 2
        env = {"PATH": os.fspath(bin_dir), "FAKE_REPO_ROOT": os.fspath(root)}
        for command in commands:
            completed = subprocess.run(
                [shell, "-c", command], cwd=root, env=env,
                text=True, capture_output=True, check=False,
            )
            assert completed.returncode == 2, (command, completed.stderr)


def _run():
    functions = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for function in functions:
        try:
            function()
            print(f"PASS {function.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {function.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())
