from __future__ import annotations

from pathlib import Path

import pytest

from tools import check_ai_provenance as provenance
from tools import mutation_harness as harness
from tools.pegasus import dispatch_compute


QUEUE_ENV = "IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE"
GRACE_ENV = "IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE"


def _parser_outcome(parser, environ: dict[str, str]) -> tuple[str, object]:
    try:
        return "accepted", parser(environ=environ)
    except (TypeError, ValueError):
        return "rejected", None


@pytest.mark.parametrize(
    ("environ", "expected"),
    [
        ({}, ("accepted", {})),
        ({QUEUE_ENV: "", GRACE_ENV: ""}, ("accepted", {})),
        (
            {QUEUE_ENV: "1800", GRACE_ENV: "600.5"},
            (
                "accepted",
                {"queue_wait_timeout_s": 1800.0, "overall_grace_s": 600.5},
            ),
        ),
        (
            {QUEUE_ENV: "0", GRACE_ENV: "+0"},
            (
                "accepted",
                {"queue_wait_timeout_s": 0.0, "overall_grace_s": 0.0},
            ),
        ),
        ({QUEUE_ENV: "nan"}, ("rejected", None)),
        ({GRACE_ENV: "inf"}, ("rejected", None)),
        ({QUEUE_ENV: "-1"}, ("rejected", None)),
        ({GRACE_ENV: "-0"}, ("rejected", None)),
    ],
)
def test_harness_and_provenance_timeout_parsers_are_equivalent(
    environ: dict[str, str],
    expected: tuple[str, object],
) -> None:
    harness_outcome = _parser_outcome(harness._dispatch_timeout_overrides, environ)
    provenance_outcome = _parser_outcome(
        provenance._dispatch_timeout_overrides, environ
    )

    assert harness_outcome == provenance_outcome == expected


def _runner_command(repo: Path) -> list[str]:
    return [
        "/usr/bin/python3",
        str(repo / "tools" / "run_tests.py"),
        "orchestrator/tests/test_example.py",
        "-qq",
    ]


def test_mutation_collection_forwards_both_d612_overrides_in_actual_argv(
    tmp_path: Path,
) -> None:
    command = harness._collection_command(
        tmp_path,
        _runner_command(tmp_path),
        "dispatch",
        outer_timeout_s=2400.0,
        environ={QUEUE_ENV: "1800", GRACE_ENV: "600"},
    )

    assert command == [
        "/usr/bin/python3",
        str(tmp_path / "tools" / "pegasus" / "dispatch_compute.py"),
        "--task",
        "tests",
        "--queue-wait-timeout",
        "1800.0",
        "--overall-grace",
        "600.0",
        "--",
        "orchestrator/tests/test_example.py",
        "-n",
        "0",
        "--collect-only",
        "-q",
    ]


def test_mutation_collection_unset_overrides_preserve_dispatch_defaults(
    tmp_path: Path,
) -> None:
    command = harness._collection_command(
        tmp_path,
        _runner_command(tmp_path),
        "dispatch",
        outer_timeout_s=1.0,
        environ={},
    )

    assert "--queue-wait-timeout" not in command
    assert "--overall-grace" not in command
    assert command[1] == str(
        tmp_path / "tools" / "pegasus" / "dispatch_compute.py"
    )
    assert command[-5:] == [
        "orchestrator/tests/test_example.py",
        "-n",
        "0",
        "--collect-only",
        "-q",
    ]


@pytest.mark.parametrize("invalid", ["nan", "inf", "-1", "-0"])
def test_mutation_collection_rejects_invalid_overrides_before_launch(
    tmp_path: Path,
    invalid: str,
) -> None:
    with pytest.raises(harness.HarnessError, match="D612 dispatch timeout"):
        harness._collection_command(
            tmp_path,
            _runner_command(tmp_path),
            "dispatch",
            outer_timeout_s=2400.0,
            environ={QUEUE_ENV: invalid},
        )


def test_mutation_collection_rejects_short_outer_watchdog_before_launch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    launched = False

    monkeypatch.setenv(QUEUE_ENV, "1800")
    monkeypatch.setenv(GRACE_ENV, "600")
    monkeypatch.setattr(harness, "_assert_only_expected_dirt", lambda *args: None)
    monkeypatch.setattr(harness, "_dispatch_orphan_stop", lambda *args, **kwargs: None)

    def unexpected_launch(*args, **kwargs):
        nonlocal launched
        launched = True
        raise AssertionError("collection process must not launch")

    monkeypatch.setattr(harness, "_run_tests", unexpected_launch)
    spec = harness.MutationSpec(
        mutations=(),
        estimated_run_seconds=1.0,
        timeout_seconds=2399.0,
        hang_timeout_seconds=1.0,
    )

    with pytest.raises(harness.HarnessError, match="外側 timeout"):
        harness._collect_expected_nodes(
            tmp_path,
            spec,
            _runner_command(tmp_path),
            "dispatch",
            head="0" * 40,
            spec_sha256="1" * 64,
            runner_sha256="2" * 64,
            tool_sha256="3" * 64,
        )
    assert launched is False


def test_provenance_dispatch_forwards_both_d612_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(provenance._PROVENANCE_OUTER_DEADLINE_ENV, raising=False)
    observed: dict[str, object] = {}

    monkeypatch.setenv(QUEUE_ENV, "1800")
    monkeypatch.setenv(GRACE_ENV, "600")

    def capture_dispatch(argv, **kwargs):
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return 0

    monkeypatch.setattr(dispatch_compute, "dispatch", capture_dispatch)

    assert provenance._default_dispatch(["--range", "base..HEAD"]) == 0
    assert observed["argv"] == ["--range", "base..HEAD"]
    assert observed["kwargs"] == {
        "task": "provenance",
        "repo_root": provenance.REPO,
        "queue_wait_timeout_s": 1800.0,
        "overall_grace_s": 600.0,
    }


def test_provenance_dispatch_omits_both_overrides_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(provenance._PROVENANCE_OUTER_DEADLINE_ENV, raising=False)
    observed: dict[str, object] = {}

    monkeypatch.delenv(QUEUE_ENV, raising=False)
    monkeypatch.delenv(GRACE_ENV, raising=False)

    def capture_dispatch(argv, **kwargs):
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return 0

    monkeypatch.setattr(dispatch_compute, "dispatch", capture_dispatch)

    assert provenance._default_dispatch([]) == 0
    assert observed["argv"] == []
    assert observed["kwargs"] == {
        "task": "provenance",
        "repo_root": provenance.REPO,
    }


@pytest.mark.parametrize("invalid", ["nan", "inf", "-1", "-0"])
def test_provenance_dispatch_rejects_invalid_overrides_before_launch(
    monkeypatch: pytest.MonkeyPatch,
    invalid: str,
) -> None:
    launched = False

    monkeypatch.setenv(QUEUE_ENV, invalid)
    monkeypatch.delenv(GRACE_ENV, raising=False)

    def unexpected_dispatch(*args, **kwargs):
        nonlocal launched
        launched = True
        raise AssertionError("dispatcher must not launch")

    monkeypatch.setattr(dispatch_compute, "dispatch", unexpected_dispatch)

    assert provenance._invoke_dispatch(None, []) == provenance.PEGASUS_DISPATCH_RC
    assert launched is False


def _run() -> int:
    """Keep this test file in the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
