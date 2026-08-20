from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.pegasus.probes.t1403_walltime_sigterm_probe import (
    NO_SIGNAL_OBSERVED_SIGKILLED,
    SIGTERM_CAUGHT_CLEAN_EXIT,
    SIGTERM_CAUGHT_THEN_KILLED,
    VerdictObservation,
    append_checkpoint_line,
    compute_verdict,
    ensure_off_repo_path,
    parse_nqsv_output,
    read_checkpoint_record,
    reconcile_observation,
    render_pbs_directives,
    write_final_receipt,
)


def _observation(**overrides: float) -> VerdictObservation:
    values: dict[str, float] = {
        "job_started_at": 100.0,
        "warn_boundary": 102.0,
        "max_boundary": 103.0,
    }
    values.update(overrides)
    return VerdictObservation(**values)


def test_verdict_sigterm_before_max_clean_exit_reports_grace() -> None:
    result = compute_verdict(
        _observation(sigterm_received_at=102.0, clean_exit_at=102.5)
    )

    assert result.classification == SIGTERM_CAUGHT_CLEAN_EXIT
    assert result.grace_seconds == pytest.approx(0.5)


def test_verdict_sigterm_then_max_death_reports_grace() -> None:
    result = compute_verdict(
        _observation(sigterm_received_at=102.0, death_confirmed_at=103.0)
    )

    assert result.classification == SIGTERM_CAUGHT_THEN_KILLED
    assert result.grace_seconds == pytest.approx(1.0)


def test_verdict_no_term_checkpoint_and_confirmed_death_has_no_inferred_grace() -> None:
    result = compute_verdict(_observation(death_confirmed_at=103.0))

    assert result.classification == NO_SIGNAL_OBSERVED_SIGKILLED
    assert result.grace_seconds is None


def test_nqsv_postmortem_extracts_explicit_signal_and_accounting() -> None:
    text = """\
%NQSV(INFO): Batch job received signal SIGKILL. (Exceeded per-req elapse time limit)
Request ID: 882048.nqsv
Elapse: 184S
Remaining Elapse: 0S
"""

    analysis = parse_nqsv_output(text)

    assert analysis["signals"] == ["SIGKILL"]
    assert analysis["elapsed_seconds"] == pytest.approx(184.0)
    assert analysis["remaining_elapsed_seconds"] == pytest.approx(0.0)


def test_off_repo_guard_rejects_repository_path(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()

    with pytest.raises(ValueError, match="inside repository"):
        ensure_off_repo_path(repository / "output" / "receipt.json", repository)


def test_pbs_directives_pin_mitigation_syntax() -> None:
    directives = render_pbs_directives("00:03:00", "00:02:00")

    assert '#PBS -l elapstim_req="00:03:00,00:02:00"' in directives
    assert "#PBS --warning-signal=elapstim:SIGTERM" in directives
    assert "#PBS --accept-sigterm=yes" in directives


def test_final_receipt_is_schema_versioned_and_external(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    evidence = tmp_path / "evidence"
    repository.mkdir()
    verdict = compute_verdict(
        _observation(sigterm_received_at=102.0, clean_exit_at=102.5)
    )
    analysis = parse_nqsv_output("Elapse: 3S\nRemaining Elapse: 0S\n")

    path = write_final_receipt(
        evidence / "receipt.json",
        verdict,
        analysis,
        repository_root=repository,
        observation=_observation(sigterm_received_at=102.0, clean_exit_at=102.5),
        job_id="882048.nqsv",
    )

    assert path.parent == evidence
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "t1403-walltime-sigterm-probe/v1"
    assert payload["verdict"]["classification"] == SIGTERM_CAUGHT_CLEAN_EXIT


def test_reconcile_checkpoint_and_final_stdout_reports_clean_exit() -> None:
    observation = reconcile_observation(
        checkpoint_record={
            "event": "SIGTERM_RECEIVED",
            "job_started_epoch": 100.0,
            "received_epoch": 102.0,
        },
        nqsv_analysis={"elapsed_seconds": 2.5},
        warn_seconds=2.0,
        max_seconds=3.0,
        final_stdout_observed=True,
    )

    result = compute_verdict(observation)

    assert result.classification == SIGTERM_CAUGHT_CLEAN_EXIT
    assert result.grace_seconds == pytest.approx(0.5)


def test_reconcile_checkpoint_without_final_stdout_reports_killed_after_term() -> None:
    observation = reconcile_observation(
        checkpoint_record={
            "event": "SIGTERM_RECEIVED",
            "job_started_epoch": 100.0,
            "received_epoch": 102.0,
        },
        nqsv_analysis={"elapsed_seconds": 3.0},
        warn_seconds=2.0,
        max_seconds=3.0,
        final_stdout_observed=False,
    )

    result = compute_verdict(observation)

    assert result.classification == SIGTERM_CAUGHT_THEN_KILLED
    assert result.grace_seconds == pytest.approx(1.0)


def test_reconcile_without_checkpoint_reports_no_signal_killed() -> None:
    observation = reconcile_observation(
        checkpoint_record=None,
        nqsv_analysis={"elapsed_seconds": 3.0},
        warn_seconds=2.0,
        max_seconds=3.0,
        final_stdout_observed=False,
    )

    result = compute_verdict(observation)

    assert result.classification == NO_SIGNAL_OBSERVED_SIGKILLED
    assert result.grace_seconds is None


def test_checkpoint_record_round_trips_one_jsonl_line(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.jsonl"
    record = {
        "event": "SIGTERM_RECEIVED",
        "job_started_epoch": 100.0,
        "received_epoch": 102.0,
    }

    append_checkpoint_line(checkpoint, record)

    assert read_checkpoint_record(checkpoint) == record


def _run() -> int:
    """pytest fixtures と parametrize を含む全 node を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
