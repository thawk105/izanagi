from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest


_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from orchestrator.codex_roles.events import (  # noqa: E402
    EventValidationError,
    parse_jsonl,
)
from tools.codex_worker_launch import (  # noqa: E402
    AttemptState,
    RolloutState,
    _drain_stdout,
    _recompute_attempt_metering,
    _recorded_summary,
    _tail_rollout,
)


MODEL = "test-model"
REASONING = "high"
CWD = "/test/repo"


def _jsonl(*events: dict[str, Any], ending: bytes = b"\n") -> bytes:
    return b"".join(
        json.dumps(event, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        + ending
        for event in events
    )


def _attempt_state(tmp_path: Path, stdout: bytes) -> AttemptState:
    stdout_path = tmp_path / "stdout.jsonl"
    stderr_path = tmp_path / "stderr.txt"
    output_path = tmp_path / "output.md"
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(b"")
    output_path.write_bytes(b"")
    return AttemptState(
        attempt_index=1,
        started_ns=0,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        output_path=output_path,
    )


def _rollout_events(session_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        {
            "type": "session_meta",
            "payload": {"session_id": session_id, "cwd": CWD},
        },
        {
            "type": "turn_context",
            "payload": {"model": MODEL, "effort": REASONING},
        },
    )


def _sealed_attempt(
    tmp_path: Path, *, stdout_ending: bytes, rollout_ending: bytes
) -> dict[str, Any]:
    session_id = str(uuid.uuid4())
    state = _attempt_state(
        tmp_path,
        _jsonl(
            {"type": "thread.started", "thread_id": session_id},
            ending=stdout_ending,
        ),
    )
    rollout_path = tmp_path / "rollout.jsonl"
    rollout_raw = _jsonl(
        *_rollout_events(session_id),
        ending=rollout_ending,
    )
    rollout_path.write_bytes(rollout_raw)
    return {
        "attempt_index": state.attempt_index,
        "stdout_path": str(state.stdout_path),
        "stderr_path": str(state.stderr_path),
        "output_path": str(state.output_path),
        "session_ids": [session_id],
        "rollouts": [
            {
                "session_id": session_id,
                "path": str(rollout_path),
                "bytes": len(rollout_raw),
            }
        ],
    }


@pytest.mark.parametrize(
    "separator",
    ["\u0085", "\u2028", "\u2029"],
    ids=["u0085", "u2028", "u2029"],
)
def test_parse_jsonl_accepts_unicode_line_separators(separator: str) -> None:
    expected = {"type": "probe", "value": f"before{separator}after"}
    raw = json.dumps(expected, ensure_ascii=False) + "\n"

    assert parse_jsonl(raw) == (expected,)


def test_parse_jsonl_still_rejects_malformed_and_oversized_lines() -> None:
    valid = json.dumps(
        {"value": "x"}, ensure_ascii=False, separators=(",", ":")
    )
    max_line_bytes = len(valid.encode("utf-8"))
    assert parse_jsonl(
        valid + "\n",
        max_bytes=1024,
        max_line_bytes=max_line_bytes,
    ) == ({"value": "x"},)

    oversized = json.dumps(
        {"value": "xx"}, ensure_ascii=False, separators=(",", ":")
    )
    invalid_inputs = (
        (
            oversized + "\n",
            {"max_bytes": 1024, "max_line_bytes": max_line_bytes},
        ),
        ("[]\n", {}),
        ('{"key":1,"key":2}\n', {}),
        ('{"ok":true}\nnot-json\n', {}),
    )
    for raw, options in invalid_inputs:
        with pytest.raises(EventValidationError):
            parse_jsonl(raw, **options)


@pytest.mark.parametrize(
    "separator",
    ["\u0085", "\u2028", "\u2029"],
    ids=["u0085", "u2028", "u2029"],
)
def test_drain_stdout_accepts_unicode_line_separators(
    tmp_path: Path, separator: str
) -> None:
    session_id = str(uuid.uuid4())
    state = _attempt_state(
        tmp_path,
        _jsonl(
            {
                "type": "thread.started",
                "thread_id": session_id,
                "note": f"before{separator}after",
            }
        ),
    )

    _drain_stdout(state)

    assert state.stdout_invalid is False
    assert state.session_ids == [session_id]


def test_drain_stdout_rejects_crlf_terminated_event(tmp_path: Path) -> None:
    session_id = str(uuid.uuid4())
    state = _attempt_state(
        tmp_path,
        _jsonl(
            {"type": "thread.started", "thread_id": session_id},
            ending=b"\r\n",
        ),
    )

    _drain_stdout(state)

    assert state.stdout_invalid is True
    assert state.session_ids == []


def test_tail_rollout_rejects_crlf_terminated_event(tmp_path: Path) -> None:
    event = {
        "type": "turn_context",
        "payload": {"model": MODEL, "effort": REASONING},
    }
    crlf_path = tmp_path / "crlf-rollout.jsonl"
    crlf_path.write_bytes(_jsonl(event, ending=b"\r\n"))
    crlf = RolloutState(session_id=str(uuid.uuid4()), path=crlf_path)

    _tail_rollout(crlf, model=MODEL, reasoning=REASONING, cwd=CWD)

    assert crlf.invalid is True
    assert crlf.context_count == 0

    lf_path = tmp_path / "lf-rollout.jsonl"
    lf_path.write_bytes(_jsonl(event))
    lf = RolloutState(session_id=str(uuid.uuid4()), path=lf_path)

    _tail_rollout(lf, model=MODEL, reasoning=REASONING, cwd=CWD)

    assert lf.invalid is False
    assert lf.context_count == 1


def test_recorded_summary_skips_crlf_terminated_event(tmp_path: Path) -> None:
    session_id = str(uuid.uuid4())
    session_meta, turn_context = _rollout_events(session_id)
    crlf_path = tmp_path / "crlf-recorded.jsonl"
    crlf_raw = _jsonl(session_meta) + _jsonl(
        turn_context, ending=b"\r\n"
    )
    crlf_path.write_bytes(crlf_raw)

    assert _recorded_summary(
        [{"rollouts": [{"path": str(crlf_path), "bytes": len(crlf_raw)}]}]
    ) == (None, None, 0, CWD)

    lf_path = tmp_path / "lf-recorded.jsonl"
    lf_raw = _jsonl(session_meta, turn_context)
    lf_path.write_bytes(lf_raw)

    assert _recorded_summary(
        [{"rollouts": [{"path": str(lf_path), "bytes": len(lf_raw)}]}]
    ) == (MODEL, REASONING, 1, CWD)


def test_recompute_metering_stdout_rejects_crlf_terminated_event(
    tmp_path: Path,
) -> None:
    invalid, _, _, _ = _recompute_attempt_metering(
        _sealed_attempt(tmp_path, stdout_ending=b"\r\n", rollout_ending=b"\n"),
        model=MODEL,
        reasoning=REASONING,
        cwd=CWD,
    )
    assert invalid == "invalid"

    complete_path = tmp_path / "complete"
    complete_path.mkdir()
    complete, _, _, _ = _recompute_attempt_metering(
        _sealed_attempt(
            complete_path, stdout_ending=b"\n", rollout_ending=b"\n"
        ),
        model=MODEL,
        reasoning=REASONING,
        cwd=CWD,
    )
    assert complete == "complete"


def test_recompute_metering_rollout_rejects_crlf_terminated_event(
    tmp_path: Path,
) -> None:
    invalid_attempt = _sealed_attempt(
        tmp_path, stdout_ending=b"\n", rollout_ending=b"\n"
    )
    rollout_record = invalid_attempt["rollouts"][0]
    rollout_path = Path(rollout_record["path"])
    session_meta, turn_context = _rollout_events(
        rollout_record["session_id"]
    )
    rollout_raw = _jsonl(session_meta) + _jsonl(
        turn_context, ending=b"\r\n"
    )
    rollout_path.write_bytes(rollout_raw)
    rollout_record["bytes"] = len(rollout_raw)

    invalid, _, _, _ = _recompute_attempt_metering(
        invalid_attempt,
        model=MODEL,
        reasoning=REASONING,
        cwd=CWD,
    )
    assert invalid == "invalid"

    complete_path = tmp_path / "complete"
    complete_path.mkdir()
    complete, _, _, _ = _recompute_attempt_metering(
        _sealed_attempt(
            complete_path, stdout_ending=b"\n", rollout_ending=b"\n"
        ),
        model=MODEL,
        reasoning=REASONING,
        cwd=CWD,
    )
    assert complete == "complete"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
