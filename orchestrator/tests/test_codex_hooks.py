# -*- coding: utf-8 -*-
"""Codex hook live gate の判定 seam と fail-closed wrapper の単体テスト。"""
from __future__ import annotations

import importlib.util
import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
_CHECKER_PATH = _REPO / "tools" / "check_codex_hooks.py"
_SPEC = importlib.util.spec_from_file_location("check_codex_hooks_for_test", _CHECKER_PATH)
assert _SPEC and _SPEC.loader
CH = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(CH)

_EXPECTED_TRUST_BYPASS_FLAG = "--dangerously-bypass-hook-trust"
_EXPECTED_BLOCKED_MARKER = "Command blocked by PreToolUse hook"
_EXPECTED_HANDLER_MARKERS = {
    "apply_patch": "[guard_write] 拒否:",
    "Bash": "[guard_bash] 拒否:",
}


def _expectations():
    repo = Path("/tmp/codex-hook-seam/repo")
    cwd = repo / "sub" / "deeper"
    return {
        tool: CH._expectation(tool, repo, cwd, "0123456789abcdef")
        for tool in CH.TOOLS
    }


def _argv(expected):
    return CH.build_codex_argv(Path("/opt/codex"), Path(expected.cwd), "probe")


def _stderr(expected):
    return (
        f"{_EXPECTED_BLOCKED_MARKER}: "
        f"{_EXPECTED_HANDLER_MARKERS[expected.tool]} "
        f"{expected.protected_marker} {expected.protected_rel}"
    )


def _events(
    expected, *, final_only=False, protected_started=False,
    bash_wrapper=False,
):
    refusal = (
        f"{_EXPECTED_BLOCKED_MARKER}: "
        f"{_EXPECTED_HANDLER_MARKERS[expected.tool]} test denial"
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
        allowed_command = CH._bash_probe_command(expected, protected=False)
        if bash_wrapper:
            allowed_command = f"/bin/bash -lc {json.dumps(allowed_command)}"
        allowed_item = {
            "id": "allowed-call",
            "type": "command_execution",
            "command": allowed_command,
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
    if protected_started:
        events.append({"type": "item.started", "item": protected_item})
    events.append({"type": "turn.completed", "usage": {}})
    return tuple(events)


def _result(
    expected, *, final_only=False, protected_started=False, failure=None,
    stderr=None, bash_wrapper=False,
):
    argv = _argv(expected)
    return CH.ProbeResult(
        tool=expected.tool,
        argv=argv,
        returncode=0,
        failure=failure,
        events=_events(
            expected,
            final_only=final_only,
            protected_started=protected_started,
            bash_wrapper=bash_wrapper,
        ),
        stderr=_stderr(expected) if stderr is None else stderr,
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


def test_observed_bash_wrapper_reaches_evaluator_and_decision_positive():
    expected, argv, results = _bundle()
    results["Bash"] = _result(expected["Bash"], bash_wrapper=True)
    kwargs = {
        "config_valid": True,
        "expectations": expected,
        "results": results,
        "argv_by_tool": argv,
    }
    assert CH.evaluate_evidence(**kwargs) == []
    assert CH.decision_rc(**kwargs) == 0


def test_protected_side_effect_is_the_only_rejection_reason():
    expected, argv, results = _bundle()
    results["Bash"] = results["Bash"]._replace(protected_exists=True)
    kwargs = {
        "config_valid": True,
        "expectations": expected,
        "results": results,
        "argv_by_tool": argv,
    }
    assert CH.evaluate_evidence(**kwargs) == [
        "Bash: protected file が作成された"
    ]
    assert CH.decision_rc(**kwargs) != 0


@pytest.mark.parametrize(
    "allowed_bytes",
    (None, b"wrong allowed bytes\n"),
    ids=("missing", "mismatch"),
)
def test_allowed_bytes_failure_is_the_only_rejection_reason(allowed_bytes):
    expected, argv, results = _bundle()
    results["apply_patch"] = results["apply_patch"]._replace(
        allowed_bytes=allowed_bytes
    )
    kwargs = {
        "config_valid": True,
        "expectations": expected,
        "results": results,
        "argv_by_tool": argv,
    }
    assert CH.evaluate_evidence(**kwargs) == [
        "apply_patch: allowed side effect の bytes が一致しない"
    ]
    assert CH.decision_rc(**kwargs) != 0


def test_protected_event_absent_expected_stderr_absent_is_nonzero():
    expected, argv, results = _bundle()
    results = {
        tool: result._replace(stderr="") for tool, result in results.items()
    }
    assert _rc(expected, argv, results) != 0


def test_protected_event_absent_expected_stderr_present_is_zero():
    expected, argv, results = _bundle()
    assert _rc(expected, argv, results) == 0


def test_pre_turn_trust_warning_items_do_not_count_as_started_tools():
    expected, argv, results = _bundle()
    warning = {
        "type": "item.completed",
        "item": {"id": "warning", "type": "error", "message": "trust warning"},
    }
    results = {
        tool: result._replace(events=(warning,) + result.events)
        for tool, result in results.items()
    }
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
        tool: _result(item, final_only=True, stderr="")
        for tool, item in expected.items()
    }
    assert _rc(expected, argv, results) != 0


def test_one_tool_only_is_nonzero():
    expected, argv, results = _bundle()
    assert _rc(expected, argv, {"apply_patch": results["apply_patch"]}) != 0


def test_tool_untried_is_nonzero():
    expected, argv, results = _bundle()
    results["Bash"] = _result(expected["Bash"], stderr="")
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
    allowed_index = next(
        index for index, event in enumerate(events)
        if event.get("type") == "item.started"
        and event.get("item", {}).get("id") == "allowed-call"
    )
    event = dict(events[allowed_index])
    item = dict(event["item"])
    item["command"] = spoof
    event["item"] = item
    events[allowed_index] = event
    results["Bash"] = results["Bash"]._replace(events=tuple(events))
    assert _rc(expected, argv, results) != 0


def test_stderr_refusal_requires_exact_marker_nonce_and_relative_path():
    for mutation in (
        lambda item: item.replace(CH.BLOCKED_MARKER, "blocked", 1),
        lambda item: item.replace(CH.HANDLER_MARKERS["Bash"], "[other]", 1),
        lambda item: item.replace("IZANAGI_CODEX_HOOK_", "OTHER_", 1),
        lambda item: item.replace("../../output/", "../output/", 1),
        lambda item: item + "\n" + CH.BLOCKED_MARKER,
    ):
        expected, argv, results = _bundle()
        results["Bash"] = results["Bash"]._replace(
            stderr=mutation(results["Bash"].stderr)
        )
        assert _rc(expected, argv, results) != 0


def test_protected_started_item_is_fail_closed():
    expected, argv, results = _bundle()
    results["Bash"] = _result(expected["Bash"], protected_started=True)
    assert _rc(expected, argv, results) != 0


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


def test_probe_builder_option_region_has_exactly_one_trust_bypass():
    expected = _expectations()["apply_patch"]
    assert CH.TRUST_BYPASS_FLAG == _EXPECTED_TRUST_BYPASS_FLAG
    assert _argv(expected)[:-1].count(_EXPECTED_TRUST_BYPASS_FLAG) == 1


def test_live_handler_markers_match_independent_contract_literals():
    assert CH.BLOCKED_MARKER == _EXPECTED_BLOCKED_MARKER
    assert CH.HANDLER_MARKERS == _EXPECTED_HANDLER_MARKERS
    for tool, expected in _expectations().items():
        assert _EXPECTED_HANDLER_MARKERS[tool] in _stderr(expected)


def test_probe_argv_rejects_missing_duplicate_and_assignment_trust_bypass():
    expected = _expectations()["apply_patch"]
    baseline = list(_argv(expected))
    option_index = baseline.index(CH.TRUST_BYPASS_FLAG)
    mutations = (
        baseline[:option_index] + baseline[option_index + 1:],
        baseline[:option_index] + [CH.TRUST_BYPASS_FLAG] + baseline[option_index:],
        baseline[:option_index]
        + [CH.TRUST_BYPASS_FLAG + "=true"]
        + baseline[option_index + 1:],
    )
    for mutated in mutations:
        assert CH.validate_production_argv(mutated, expected.cwd)


def test_prompt_trust_flag_does_not_satisfy_option_requirement():
    expected = _expectations()["apply_patch"]
    mutated = list(_argv(expected))
    mutated.remove(CH.TRUST_BYPASS_FLAG)
    mutated[-1] += " " + CH.TRUST_BYPASS_FLAG
    assert any(
        "trust bypass が exact 1 件でない" in finding
        for finding in CH.validate_production_argv(mutated, expected.cwd)
    )


def test_probe_argv_rejects_sandbox_bypass_in_options_or_prompt():
    expected = _expectations()["apply_patch"]
    baseline = list(_argv(expected))
    option_mutation = baseline[:-1] + [CH.SANDBOX_BYPASS_FLAG, baseline[-1]]
    prompt_mutation = baseline[:-1] + [baseline[-1] + CH.SANDBOX_BYPASS_FLAG]
    for mutated in (option_mutation, prompt_mutation):
        assert CH.validate_production_argv(mutated, expected.cwd)


def test_bash_accepts_only_raw_or_observed_exact_wrapper():
    expected = _expectations()["Bash"]
    command = CH._bash_probe_command(expected, protected=False)
    assert CH._bash_command_matches(command, command)
    assert CH._bash_command_matches(
        f"/bin/bash -lc {json.dumps(command)}", command
    )


def test_bash_rejects_unobserved_wrapper_shapes():
    expected = _expectations()["Bash"]
    command = CH._bash_probe_command(expected, protected=False)
    for candidate in (
        f"bash -lc {json.dumps(command)}",
        f"/bin/bash -c {json.dumps(command)}",
        f"/bin/bash --noprofile -lc {json.dumps(command)}",
        f"/bin/bash -lc {json.dumps(command)} extra",
    ):
        assert not CH._bash_command_matches(candidate, command)


def _fake_clone(_source, parent):
    repo = parent / "repo"
    repo.mkdir()
    return repo


def test_projected_probe_installation_is_validated_before_live_run():
    validated = []
    run_calls = []

    def validator(root):
        validated.append(root)
        return [] if len(validated) == 1 else ["projected drift"]

    findings = CH.check(
        Path("/source"), Path("/opt/codex"), 1,
        clone_factory=_fake_clone,
        probe_runner=lambda *args, **kwargs: run_calls.append((args, kwargs)),
        validator=validator,
    )
    assert findings == ["projected drift"] and not run_calls


def test_invalid_probe_argv_never_reaches_probe_runner():
    run_calls = []
    findings = CH.check(
        Path("/source"), Path(CH.SANDBOX_BYPASS_FLAG), 1,
        clone_factory=_fake_clone,
        probe_runner=lambda *args, **kwargs: run_calls.append((args, kwargs)),
        validator=lambda _root: [],
    )
    assert findings and not run_calls


def test_check_production_defaults_are_the_real_functions():
    parameters = inspect.signature(CH.check).parameters
    assert parameters["clone_factory"].default is CH._make_disposable_clone
    assert parameters["probe_runner"].default is CH.run_probe
    assert parameters["validator"].default is CH.validate_installation


def test_config_preflight_cannot_be_replaced_by_live_evidence():
    expected, argv, results = _bundle()
    assert _rc(expected, argv, results, config_valid=False) != 0


def test_installation_requires_all_hook_sources_as_regular_files():
    with tempfile.TemporaryDirectory(prefix="codex-hook-install-test-") as name:
        root = Path(name) / "repo"
        CH._project_current_files(_REPO, root)
        assert CH.validate_installation(root) == []
        for relative in (
            Path("hooks/codex_guard.sh"),
            Path("hooks/guard_write.py"),
            Path("hooks/guard_bash.py"),
        ):
            target = root / relative
            target.unlink()
            assert any(
                os.fspath(relative) in finding
                for finding in CH.validate_installation(root)
            )
            target.write_bytes((_REPO / relative).read_bytes())
            target.unlink()
            target.symlink_to(_REPO / relative)
            assert any(
                os.fspath(relative) in finding
                for finding in CH.validate_installation(root)
            )
            target.unlink()
            target.write_bytes((_REPO / relative).read_bytes())


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
