# -*- coding: utf-8 -*-
"""tools/codex_worker_ledger.py の合成 rollout による回帰テスト。"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_LEDGER = _ROOT / "tools" / "codex_worker_ledger.py"
_FIXTURES = Path(__file__).parent / "fixtures" / "codex_ledger"
_SPEC = importlib.util.spec_from_file_location(
    "codex_worker_ledger_under_test", _LEDGER
)
assert _SPEC and _SPEC.loader
LEDGER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = LEDGER
_SPEC.loader.exec_module(LEDGER)


def _case(name: str) -> list[dict[str, Any]]:
    return json.loads(
        (_FIXTURES / "cases" / f"{name}.json").read_text(encoding="utf-8")
    )


def _valid_agent() -> str:
    return "十分な長さを持つ合成成果物です。" * 40 + "\n## 総括\n合成検査を完了しました。"


def _usage(values: list[int]) -> dict[str, int]:
    input_tokens, cached_tokens, output_tokens, total_tokens = values
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": 0,
        "total_tokens": total_tokens,
    }


def _usage_value(value: Any) -> Any:
    return _usage(value) if isinstance(value, list) else value


def _materialize(
    root: Path,
    specs: list[dict[str, Any]],
    *,
    cwd: str = "/synthetic/wave",
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for index, spec in enumerate(specs):
        session_id = spec["id"]
        second = index * 10
        timestamp = f"2026-01-01T00:00:{second:02d}Z"
        path = root / f"rollout-2026-01-01T00-00-{second:02d}-{session_id}.jsonl"
        lines: list[dict[str, Any]] = []
        if not spec.get("omit_meta"):
            meta_session_id = spec.get("meta_id", session_id)
            lines.append(
                {
                    "timestamp": timestamp,
                    "type": "session_meta",
                    "payload": {
                        "session_id": meta_session_id,
                        "timestamp": timestamp,
                        **(
                            {}
                            if spec.get("omit_cwd")
                            else {"cwd": spec.get("cwd", cwd)}
                        ),
                    },
                }
            )
        for extra_meta in spec.get("extra_meta", []):
            lines.append(
                {
                    "timestamp": timestamp,
                    "type": "session_meta",
                    "payload": extra_meta,
                }
            )
        contexts = spec.get("contexts")
        if contexts is None:
            contexts = [
                {
                    "model": spec.get("model", "gpt-synthetic"),
                    "effort": spec.get("effort", "high"),
                }
                for _ in range(spec.get("turn_contexts", 1))
            ]
        for context in contexts:
            context_line = {
                "timestamp": timestamp,
                "type": "turn_context",
                "payload": context.get("payload", {}),
            }
            if context.get("object_level"):
                context_line["model"] = context["model"]
                context_line["effort"] = context["effort"]
                if "collaboration_mode" in context:
                    context_line["collaboration_mode"] = context[
                        "collaboration_mode"
                    ]
            else:
                context_line["payload"] = {
                    "model": context["model"],
                    "effort": context["effort"],
                }
            lines.append(context_line)
        lines.append(
            {
                "timestamp": timestamp,
                "type": "event_msg",
                "payload": {
                    "type": "user_message",
                    "message": spec["prompt"],
                },
            }
        )
        usage_pairs = spec.get("usage_pairs")
        if usage_pairs is None:
            totals = spec.get("totals", [[100, 10, 20, 120]])
            lasts = spec.get("lasts", totals)
            assert len(totals) == len(lasts)
            usage_pairs = [
                {"total": total, "last": last}
                for total, last in zip(totals, lasts)
            ]
        for pair in usage_pairs:
            lines.append(
                {
                    "timestamp": timestamp,
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "total_token_usage": _usage_value(pair["total"]),
                            "last_token_usage": _usage_value(pair["last"]),
                        },
                    },
                }
            )
        if spec.get("null_token_info"):
            lines.append(
                {
                    "timestamp": timestamp,
                    "type": "event_msg",
                    "payload": {"type": "token_count", "info": None},
                }
            )
        for agent in spec.get("agents", []):
            lines.append(
                {
                    "timestamp": timestamp,
                    "type": "event_msg",
                    "payload": {"type": "agent_message", "message": agent},
                }
            )
        agent = spec.get("agent", _valid_agent())
        if agent is not None:
            lines.append(
                {
                    "timestamp": timestamp,
                    "type": "event_msg",
                    "payload": {"type": "agent_message", "message": agent},
                }
            )
        if spec.get("complete", True):
            lines.append(
                {
                    "timestamp": timestamp,
                    "type": "event_msg",
                    "payload": {"type": "task_complete"},
                }
            )
        if spec.get("aborted", False):
            lines.append(
                {
                    "timestamp": timestamp,
                    "type": "event_msg",
                    "payload": {"type": "turn_aborted"},
                }
            )
        for event_type in spec.get("events", []):
            lines.append(
                {
                    "timestamp": timestamp,
                    "type": "event_msg",
                    "payload": {"type": event_type},
                }
            )
        path.write_text(
            "".join(f"{line}\n" for line in spec.get("raw_lines", []))
            + "".join(
                json.dumps(line, ensure_ascii=False, separators=(",", ":")) + "\n"
                for line in lines
            ),
            encoding="utf-8",
        )
    return root


def _run_json(
    capsys: pytest.CaptureFixture[str], root: Path, *args: str
) -> tuple[int, dict[str, Any], str]:
    rc = LEDGER.main(["--sessions-root", str(root), "--json", *args])
    captured = capsys.readouterr()
    return rc, json.loads(captured.out), captured.err


def _healthy_specs() -> list[dict[str, Any]]:
    prompts = [
        "あなたは段2の read-only Codex planner である。",
        "あなたは段3の read-only adversarial consultant である。A",
        "あなたは段3の read-only adversarial consultant である。B",
        "あなたは段5の Codex implementation worker (`role=author`) である。",
        "あなたは段6の Codex fix worker である。A",
        "あなたは段6の fix2 implementation author である。B",
        "あなたは段6の read-only adversarial reviewer である。A",
        "あなたは段6の read-only adversarial reviewer である。B",
        "あなたは段6 fix後の read-only focused reviewer である。A",
        "あなたは段6の fix2後の read-only focused adversarial reviewer である。B",
    ]
    return [
        {
            "id": f"80000000-0000-0000-0000-{index:012d}",
            "prompt": prompt,
        }
        for index, prompt in enumerate(prompts, 1)
    ]


def _write_worklog(path: Path, effort: str) -> Path:
    path.write_text(
        f"# synthetic worklog\n\n## 対象 wave T-179\n\n- {effort}\n\n"
        "### 次の一手\n\n- synthetic\n",
        encoding="utf-8",
    )
    return path


def _manifest_session(
    session_id: str, *, job_id: str = "job-1", attempt_index: int = 1
) -> dict[str, Any]:
    return {
        "job_id": job_id,
        "attempt_index": attempt_index,
        "session_id": session_id,
    }


def _manifest_data(sessions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "wave_id": "wave.synthetic-1",
        "repo_root": "/synthetic/repo",
        "base_commit": "a" * 40,
        "sessions": sessions,
    }


def _write_manifest(
    path: Path, sessions: list[dict[str, Any]]
) -> Path:
    path.write_text(
        json.dumps(
            _manifest_data(sessions),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _manifest_v2_session(
    session_id: str,
    *,
    job_id: str,
    stage: str,
    lane: str | None,
    repo_root: str,
    receipt_path: str,
) -> dict[str, Any]:
    return {
        "job_id": job_id,
        "attempt_index": 1,
        "session_id": session_id,
        "stage": stage,
        "lane": lane,
        "repo_root": repo_root,
        "base_commit": "a" * 40,
        "requested_cwd": repo_root,
        "recorded_cwd": repo_root,
        "sessions_root": "/synthetic/sessions",
        "receipt_path": receipt_path,
        "authority_commit": "b" * 40,
        "authority_digest": "c" * 64,
    }


def _incremental_usage_pairs(
    model_calls: int, cli_reported: int
) -> list[dict[str, list[int]]]:
    quotient, remainder = divmod(cli_reported, model_calls)
    cumulative = 0
    pairs: list[dict[str, list[int]]] = []
    for index in range(model_calls):
        increment = quotient + (index < remainder)
        cumulative += increment
        pairs.append(
            {
                "total": [cumulative, 0, 0, cumulative],
                "last": [increment, 0, 0, increment],
            }
        )
    return pairs


def _t179_frozen_synthetic_specs() -> list[dict[str, Any]]:
    specs = _healthy_specs()
    model_calls = [39, 31, 31, 47, 50, 50, 43, 44, 49, 50]
    cli_reported = [
        224_150,
        196_092,
        196_093,
        171_736,
        302_867,
        302_867,
        272_276,
        272_277,
        409_812,
        409_812,
    ]
    for spec, calls, tokens in zip(
        specs, model_calls, cli_reported, strict=True
    ):
        spec["cwd"] = "/synthetic/t179-frozen-wave"
        spec["usage_pairs"] = _incremental_usage_pairs(calls, tokens)
    return specs


def test_cumulative_usage_stays_canonical_and_metrics_are_explicit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("compaction"))
    rc, output, stderr = _run_json(capsys, root)
    row = output["sessions"][0]
    assert rc == 0
    assert stderr == ""
    assert row["model_calls"] == 2
    assert row["turn_contexts"] == 1
    assert row["input_tokens"] == 160
    assert row["cached_input_tokens"] == 40
    assert row["output_tokens"] == 50
    assert row["reasoning_output_tokens"] == 0
    assert row["cli_reported"] == 170
    assert row["per_turn_sum"] == 240
    assert row["cumulative_minus_per_turn"] == -70
    assert row["total_tokens_raw"] == 210
    assert output["totals"]["cli_reported"] == 170


def test_full_session_ids_do_not_merge_on_eight_hex_collision(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("id_collision"))
    rc, output, _ = _run_json(capsys, root)
    ids = [row["session_id"] for row in output["sessions"]]
    assert rc == 0
    assert output["totals"]["sessions"] == 2
    assert len(set(ids)) == 2
    assert {session_id[:8] for session_id in ids} == {"deadbeef"}


def test_case_normalized_duplicate_is_the_only_strict_failure_m2_prime(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("case_duplicate"))
    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 2
    assert [row["session_id"] for row in output["sessions"]] == [
        "abcdefab-0000-0000-0000-000000000001",
        "abcdefab-0000-0000-0000-000000000001",
    ]
    assert list(output["issues"]) == ["duplicate_session_id"]
    assert "duplicate session_id" in stderr


def test_final_null_cumulative_is_reported_without_erasing_last_valid_usage(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("final_null_usage"))
    rc, output, stderr = _run_json(capsys, root, "--strict")
    row = output["sessions"][0]
    assert rc == 2
    assert row["model_calls"] == 2
    assert row["input_tokens"] == 1000
    assert row["cached_input_tokens"] == 100
    assert row["output_tokens"] == 50
    assert row["reasoning_output_tokens"] == 0
    assert row["cli_reported"] == 950
    assert row["total_tokens_raw"] == 1050
    assert list(output["issues"]) == ["malformed_usage"]
    assert "malformed usage" in stderr


def test_bool_usage_field_is_the_only_strict_failure_m9(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("malformed_usage_type"))
    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 2
    assert output["sessions"][0]["cli_reported"] == 0
    assert list(output["issues"]) == ["malformed_usage"]
    assert len(output["issues"]["malformed_usage"]) == 1
    assert ".input_tokens is not an int" in stderr


@pytest.mark.parametrize("field", LEDGER._USAGE_FIELDS)
@pytest.mark.parametrize("bad_value", [None, 1.5, "1"])
def test_each_usage_field_rejects_null_and_non_int_values(
    field: str,
    bad_value: Any,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    total_usage: dict[str, Any] = {
        "input_tokens": 1,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "total_tokens": 1,
    }
    total_usage[field] = bad_value
    spec = {
        "id": "93100000-0000-0000-0000-000000000001",
        "prompt": "あなたは段2の read-only Codex planner である。",
        "usage_pairs": [{"total": total_usage, "last": [1, 0, 0, 1]}],
    }
    root = _materialize(tmp_path / "sessions", [spec])
    rc, output, _ = _run_json(capsys, root, "--strict")
    assert rc == 2
    assert list(output["issues"]) == ["malformed_usage"]
    assert len(output["issues"]["malformed_usage"]) == 1


@pytest.mark.parametrize("field", LEDGER._REQUIRED_USAGE_FIELDS)
def test_each_usage_field_is_required(
    field: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    total_usage = {
        "input_tokens": 1,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "total_tokens": 1,
    }
    del total_usage[field]
    spec = {
        "id": "93200000-0000-0000-0000-000000000001",
        "prompt": "あなたは段2の read-only Codex planner である。",
        "usage_pairs": [{"total": total_usage, "last": [1, 0, 0, 1]}],
    }
    root = _materialize(tmp_path / "sessions", [spec])
    rc, output, _ = _run_json(capsys, root, "--strict")
    assert rc == 2
    assert list(output["issues"]) == ["malformed_usage"]
    assert len(output["issues"]["malformed_usage"]) == 1


def test_legacy_usage_without_reasoning_and_null_info_passes_strict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("legacy_usage"))
    rc, output, stderr = _run_json(capsys, root, "--strict")
    row = output["sessions"][0]
    assert rc == 0
    assert stderr == ""
    assert output["issues"] == {}
    assert row["model_calls"] == 1
    assert row["reasoning_output_tokens"] == 0
    assert row["cli_reported"] == 110
    assert row["per_turn_sum"] == 110


def test_negative_required_usage_fields_fail_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("negative_usage"))
    rc, output, stderr = _run_json(capsys, root, "--strict")
    details = output["issues"]["malformed_usage"]
    assert rc == 2
    assert list(output["issues"]) == ["malformed_usage"]
    assert len(details) == len(LEDGER._REQUIRED_USAGE_FIELDS)
    assert {
        detail.rsplit(".", 1)[-1].removesuffix(" is negative")
        for detail in details
    } == set(LEDGER._REQUIRED_USAGE_FIELDS)
    assert "malformed usage" in stderr


def test_cached_exceeding_input_is_malformed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = {
        "id": "93300000-0000-0000-0000-000000000001",
        "prompt": "あなたは段2の read-only Codex planner である。",
        "usage_pairs": [
            {
                "total": [100, 200, 1, 101],
                "last": [1, 0, 0, 1],
            }
        ],
    }
    root = _materialize(tmp_path / "sessions", [spec])
    rc, output, stderr = _run_json(capsys, root, "--strict")
    row = output["sessions"][0]
    assert rc == 2
    assert row["cli_reported"] == 0
    assert row["total_tokens_raw"] == 0
    assert list(output["issues"]) == ["usage_cached_exceeds_input"]
    assert len(output["issues"]["usage_cached_exceeds_input"]) == 1
    assert "cached input exceeds input usage" in stderr


def test_non_monotonic_cumulative_and_event_counters_are_exposed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("non_monotonic"))
    rc, output, stderr = _run_json(capsys, root, "--strict")
    row = output["sessions"][0]
    assert rc == 2
    assert row["context_compacted"] == 1
    assert row["thread_rolled_back"] == 1
    assert row["turn_aborted"] == 1
    assert row["outcome"] == "aborted_turn"
    assert row["cumulative_minus_per_turn"] == -80
    assert output["totals"]["context_compacted"] == 1
    assert list(output["issues"]) == ["non_monotonic_cumulative"]
    assert "non-monotonic cumulative usage" in stderr


def test_cli_reported_cumulative_rollback_fails_strict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = {
        **_healthy_specs()[0],
        "usage_pairs": [
            {
                "total": [1_000, 0, 0, 1_000],
                "last": [1_000, 0, 0, 1_000],
            },
            {
                "total": [1_000, 999, 1, 1_001],
                "last": [0, 0, 1, 1],
            },
        ],
    }
    root = _materialize(tmp_path / "sessions", [spec])
    rc, output, stderr = _run_json(capsys, root, "--strict")
    row = output["sessions"][0]
    assert rc == 2
    assert row["cli_reported"] == 2
    assert row["total_tokens_raw"] == 1_001
    assert list(output["issues"]) == ["usage_cumulative_rollback"]
    assert output["issues"]["usage_cumulative_rollback"][0].endswith(
        ": cli_reported decreased"
    )
    assert "cumulative usage rollback" in stderr


def test_unclassified_is_included_and_strict_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("unclassified"))
    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 2
    assert output["totals"]["sessions"] == 1
    assert output["sessions"][0]["stage"] == "unclassified"
    assert "unclassified stage" in stderr


def test_fragment_requires_existing_output_validator_policy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("fragment"))
    _, output, _ = _run_json(capsys, root)
    assert output["sessions"][0]["outcome"] == "fragment"


def test_fenced_summary_does_not_make_fragment_complete(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = {
        "id": "30000000-0000-0000-0000-000000000002",
        "prompt": "あなたは段6の read-only adversarial reviewer である。",
        "agent": "本文" * 200 + "\n````markdown\n## 総括\n````\n",
    }
    root = _materialize(tmp_path / "sessions", [spec])
    _, output, _ = _run_json(capsys, root)
    assert output["sessions"][0]["outcome"] == "fragment"


def test_incomplete_without_task_complete_or_agent_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("incomplete"))
    _, output, _ = _run_json(capsys, root)
    assert output["sessions"][0]["outcome"] == "incomplete"


def test_task_complete_only_missing_with_healthy_message_is_incomplete_m5_prime(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("incomplete_task_only"))
    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 0
    assert stderr == ""
    assert output["sessions"][0]["outcome"] == "incomplete"
    assert output["issues"] == {}


def test_aborted_turn_has_explicit_priority(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = {
        "id": "40000000-0000-0000-0000-000000000002",
        "prompt": "あなたは段5の Codex implementation worker (`role=author`) である。",
        "complete": False,
        "aborted": True,
    }
    root = _materialize(tmp_path / "sessions", [spec])
    _, output, _ = _run_json(capsys, root)
    assert output["sessions"][0]["outcome"] == "aborted_turn"
    assert output["sessions"][0]["turn_aborted"] == 1
    assert output["sessions"][0]["exit_code"] == "unknown"


def test_retry_normalizes_surrounding_and_repeated_whitespace(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # M7 は受理集合を変えない diagnostic sensitivity pin であり、kill ではない。
    root = _materialize(tmp_path / "sessions", _case("retry"))
    _, output, _ = _run_json(capsys, root)
    rows = output["sessions"]
    assert [row["retry_group"] for row in rows] == [1, 1]
    assert [row["retry_index"] for row in rows] == [1, 2]
    assert rows[0]["prompt_hash"] == rows[1]["prompt_hash"]


def test_retry_groups_do_not_cross_cwd_boundaries(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    specs = _case("retry")
    specs[0]["cwd"] = "/synthetic/wave-a"
    specs[1]["cwd"] = "/synthetic/wave-b"
    root = _materialize(tmp_path / "sessions", specs)
    _, output, _ = _run_json(capsys, root)
    assert [row["retry_group"] for row in output["sessions"]] == [None, None]
    assert [row["retry_index"] for row in output["sessions"]] == [0, 0]


def test_healthy_wave_and_matching_worklog_pass_strict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _healthy_specs())
    worklog = _write_worklog(
        tmp_path / "worklog.md",
        "エージェント工数: Codex １０ job "
        "(planner １ / consult ２ / author・fix ３ / review ４)",
    )
    rc, output, stderr = _run_json(
        capsys,
        root,
        "--worklog",
        str(worklog),
        "--worklog-entry",
        "対象 wave",
        "--strict",
    )
    assert rc == 0
    assert stderr == ""
    assert output["issues"] == {}
    assert output["totals"] == {
        "sessions": 10,
        "model_calls": 10,
        "turn_contexts": 10,
        "input_tokens": 1000,
        "cached_input_tokens": 100,
        "output_tokens": 200,
        "reasoning_output_tokens": 0,
        "cli_reported": 1100,
        "per_turn_sum": 1100,
        "cumulative_minus_per_turn": 0,
        "context_compacted": 0,
        "thread_rolled_back": 0,
        "turn_aborted": 0,
    }
    assert [
        (row["stage"], row["model"], row["reasoning"])
        for row in output["sessions"]
    ] == [
        ("plan", "gpt-synthetic", "high"),
        ("consult", "gpt-synthetic", "high"),
        ("consult", "gpt-synthetic", "high"),
        ("author", "gpt-synthetic", "high"),
        ("fix", "gpt-synthetic", "high"),
        ("fix", "gpt-synthetic", "high"),
        ("review", "gpt-synthetic", "high"),
        ("review", "gpt-synthetic", "high"),
        ("focus", "gpt-synthetic", "high"),
        ("focus", "gpt-synthetic", "high"),
    ]


def test_worklog_reports_total_and_review_mismatches_together(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _healthy_specs())
    worklog = _write_worklog(
        tmp_path / "worklog.md",
        "エージェント工数: Codex 9 job "
        "(planner 1 / consult 2 / author・fix 3 / review 3)",
    )
    rc, output, stderr = _run_json(
        capsys,
        root,
        "--worklog",
        str(worklog),
        "--worklog-entry",
        "対象 wave",
        "--strict",
    )
    assert rc == 2
    assert output["totals"]["sessions"] == 10
    assert "worklog mismatch total: expected 9, actual 10" in stderr
    assert "worklog mismatch review: expected 3, actual 4" in stderr
    assert "planner" not in stderr
    assert "author・fix" not in stderr


@pytest.mark.parametrize(
    ("fixture_name", "expected_detail"),
    [
        ("total_only.md", "worklog mismatch total: expected 9, actual 10"),
        ("review_only.md", "worklog mismatch review: expected 3, actual 4"),
    ],
)
def test_worklog_single_reason_mismatch_fixtures_m6a_m6b(
    fixture_name: str,
    expected_detail: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _materialize(tmp_path / "sessions", _healthy_specs())
    worklog = _FIXTURES / "worklogs" / fixture_name
    rc, output, stderr = _run_json(
        capsys,
        root,
        "--worklog",
        str(worklog),
        "--worklog-entry",
        "対象 wave",
        "--strict",
    )
    assert rc == 2
    assert output["issues"] == {"worklog": [expected_detail]}
    assert expected_detail in stderr


def test_worklog_ignores_effort_rows_inside_fences_and_other_entries(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", [_healthy_specs()[0]])
    worklog = tmp_path / "worklog.md"
    worklog.write_text(
        "# synthetic\n\n"
        "## 別 wave\n\n"
        "- エージェント工数: Codex 9 job "
        "(planner 9 / consult 0 / author・fix 0 / review 0)\n\n"
        "## 対象 wave\n\n"
        "```text\n"
        "エージェント工数: Codex 9 job "
        "(planner 9 / consult 0 / author・fix 0 / review 0)\n"
        "```\n"
        "- エージェント工数: Codex 1 job "
        "(planner 1 / consult 0 / author・fix 0 / review 0)\n",
        encoding="utf-8",
    )
    rc, output, stderr = _run_json(
        capsys,
        root,
        "--worklog",
        str(worklog),
        "--worklog-entry",
        "対象 wave",
        "--strict",
    )
    assert rc == 0
    assert stderr == ""
    assert output["issues"] == {}


def test_malformed_json_line_is_counted_without_exception(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", [_healthy_specs()[0]])
    rollout = next(root.glob("rollout-*.jsonl"))
    original = rollout.read_text(encoding="utf-8")
    rollout.write_text("{broken json\n" + original, encoding="utf-8")
    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 2
    assert output["totals"]["sessions"] == 1
    assert len(output["issues"]["malformed_json"]) == 1
    assert "malformed JSON lines" in stderr


@pytest.mark.parametrize("line", ["[]", "null", '"x"', "42"])
def test_schema_valid_non_object_line_is_malformed(
    line: str,
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", [_healthy_specs()[0]])
    rollout = next(root.glob("rollout-*.jsonl"))
    original = rollout.read_text(encoding="utf-8")
    rollout.write_text(line + "\n" + original, encoding="utf-8")
    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 2
    assert output["totals"]["sessions"] == 1
    assert list(output["issues"]) == ["malformed_json"]
    assert len(output["issues"]["malformed_json"]) == 1
    assert "malformed JSON lines" in stderr


def test_malformed_line_in_cwd_filtered_file_does_not_pollute_selection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    specs = _healthy_specs()[:2]
    specs[0]["cwd"] = "/synthetic/target-wave"
    specs[1]["cwd"] = "/synthetic/other-wave"
    root = _materialize(tmp_path / "sessions", specs)
    excluded = next(path for path in root.glob("*") if specs[1]["id"] in path.name)
    excluded.write_text(
        "null\n" + excluded.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    rc, output, stderr = _run_json(
        capsys, root, "--cwd-contains", "target-wave", "--strict"
    )
    assert rc == 0
    assert stderr == ""
    assert output["totals"]["sessions"] == 1
    assert output["issues"] == {}


def test_later_matching_meta_selects_file_and_keeps_its_issues(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("meta_order"))
    rc, output, stderr = _run_json(
        capsys, root, "--cwd-contains", "target-wave", "--strict"
    )
    assert rc == 2
    assert output["totals"]["sessions"] == 1
    assert output["sessions"][0]["cwd"] == "/synthetic/target-wave"
    assert list(output["issues"]) == [
        "malformed_json",
        "multiple_session_meta",
    ]
    assert "malformed JSON lines" in stderr
    assert "multiple session_meta rows" in stderr


def test_meta_unknown_file_is_ignored_only_when_cwd_filter_cannot_select_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("meta_unknown"))
    rc, output, stderr = _run_json(
        capsys, root, "--cwd-contains", "target-wave", "--strict"
    )
    assert rc == 0
    assert stderr == ""
    assert output["totals"]["sessions"] == 1
    assert output["issues"] == {}

    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 2
    assert output["totals"]["sessions"] == 1
    assert list(output["issues"]) == [
        "malformed_json",
        "missing_session_meta",
    ]
    assert "malformed JSON lines" in stderr
    assert "missing session_meta files" in stderr


def test_missing_session_meta_file_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "sessions"
    root.mkdir()
    (root / "rollout-missing-meta.jsonl").write_text(
        '{"type":"event_msg","payload":{"type":"task_complete"}}\n',
        encoding="utf-8",
    )
    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 2
    assert output["totals"]["sessions"] == 0
    assert len(output["issues"]["missing_session_meta"]) == 1
    assert "missing session_meta files" in stderr


def test_missing_session_cwd_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = {**_healthy_specs()[0], "omit_cwd": True}
    root = _materialize(tmp_path / "sessions", [spec])
    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 2
    assert output["totals"]["sessions"] == 1
    assert list(output["issues"]) == ["missing_session_cwd"]
    assert "missing session_meta.cwd" in stderr


def test_multiple_session_meta_rows_are_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = {
        **_healthy_specs()[0],
        "extra_meta": [
            {
                "session_id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
                "timestamp": "2026-01-01T01:00:00Z",
                "cwd": "/synthetic/wave",
            }
        ],
    }
    root = _materialize(tmp_path / "sessions", [spec])
    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 2
    assert output["totals"]["sessions"] == 1
    assert list(output["issues"]) == ["multiple_session_meta"]
    assert "multiple session_meta rows" in stderr


def test_inconsistent_turn_context_fails_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(
        tmp_path / "sessions", _case("turn_context_inconsistent")
    )
    rc, output, stderr = _run_json(capsys, root, "--strict")
    rows = output["sessions"]
    assert rc == 2
    assert [row["turn_contexts"] for row in rows] == [2, 2]
    assert [(row["model"], row["reasoning"]) for row in rows] == [
        ("gpt-first", "high"),
        ("gpt-same", "high"),
    ]
    assert list(output["issues"]) == ["inconsistent_turn_context"]
    assert len(output["issues"]["inconsistent_turn_context"]) == 2
    assert "inconsistent turn_context" in stderr


def test_object_level_turn_context_model_and_effort_are_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    context = {
        "model": "gpt-object-level",
        "effort": "max",
        "object_level": True,
        "payload": {"model": "gpt-object-level", "effort": "max"},
    }
    spec = {
        **_healthy_specs()[0],
        "contexts": [context, dict(context)],
    }
    root = _materialize(tmp_path / "sessions", [spec])
    rc, output, stderr = _run_json(capsys, root, "--strict")
    row = output["sessions"][0]
    assert rc == 0
    assert stderr == ""
    assert output["issues"] == {}
    assert row["turn_contexts"] == 2
    assert row["model"] == "gpt-object-level"
    assert row["reasoning"] == "max"


def test_payload_empty_rejects_top_level_and_collaboration_mode_decoys(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    decoy = {
        "model": "gpt-object-level",
        "effort": "max",
        "object_level": True,
        "payload": {},
        "collaboration_mode": {
            "settings": {"model": "gpt-object-level", "effort": "max"}
        },
    }
    spec = {
        **_healthy_specs()[0],
        "contexts": [decoy, dict(decoy)],
    }
    root = _materialize(tmp_path / "sessions", [spec])
    rc, output, stderr = _run_json(capsys, root, "--strict")
    row = output["sessions"][0]
    assert rc == 2
    assert "missing turn_context payload authority" in stderr
    assert list(output["issues"]) == ["missing_turn_context_authority"]
    assert len(output["issues"]["missing_turn_context_authority"]) == 2
    assert row["turn_contexts"] == 2
    assert row["model"] == ""
    assert row["reasoning"] == ""


def test_same_session_id_in_two_files_fails_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = _healthy_specs()[0]
    left = _materialize(tmp_path / "sessions" / "a", [spec])
    right = tmp_path / "sessions" / "b"
    _materialize(right, [spec])
    assert left != right
    rc, output, stderr = _run_json(capsys, tmp_path / "sessions", "--strict")
    assert rc == 2
    assert output["totals"]["sessions"] == 2
    assert len(output["issues"]["duplicate_session_id"]) == 1
    assert "duplicate session_id" in stderr


def test_manifest_duplicate_rollout_fails_without_strict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = _healthy_specs()[0]
    root = tmp_path / "sessions"
    _materialize(root / "a", [spec])
    _materialize(root / "b", [spec])
    manifest = _write_manifest(
        tmp_path / "manifest.json",
        [_manifest_session(spec["id"], job_id="unique-job")],
    )
    rc, output, stderr = _run_json(
        capsys, root, "--manifest", str(manifest)
    )
    assert rc == 2
    assert output["totals"]["sessions"] == 2
    assert list(output["issues"]) == ["duplicate_session_id"]
    assert len(output["issues"]["duplicate_session_id"]) == 1
    assert "duplicate session_id" in stderr


def test_stage_rules_keep_fix2_author_in_fix_and_focus_specific(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("precedence"))
    _, output, _ = _run_json(capsys, root)
    assert [row["stage"] for row in output["sessions"]] == [
        "fix",
        "focus",
        "focus",
    ]


def test_stage_rules_follow_wave_stage_not_role_words() -> None:
    existing_cases = [
        ("あなたは dev-wave 段2の read-only Codex planner です。", "plan"),
        (
            "あなたは dev-wave 段3の read-only adversarial consultant A です。",
            "consult",
        ),
        (
            "あなたは izanagi dev-wave 段5の Codex implementation worker "
            "(`role=author`) です。",
            "author",
        ),
        ("あなたは dev-wave 段6の Codex fix worker です。", "fix"),
        (
            "あなたは Izanagi dev-wave 段6の fix2 implementation author である。",
            "fix",
        ),
        (
            "あなたは dev-wave 段6の read-only adversarial reviewer A です。",
            "review",
        ),
        (
            "あなたは dev-wave 段6 fix後の read-only focused reviewer です。",
            "focus",
        ),
        (
            "あなたは Izanagi dev-wave 段6 fix2後の read-only focused "
            "adversarial reviewer である。",
            "focus",
        ),
    ]
    focus_whitespace_cases = [
        "あなたは dev-wave 段6 fix後の read-only focused reviewer です。",
        "あなたは dev-wave 段6 fix 後の read-only focused reviewer です。",
        (
            "あなたは Izanagi dev-wave 段6 fix2後の read-only focused "
            "adversarial reviewer である。"
        ),
        (
            "あなたは Izanagi dev-wave 段6 fix2 後の read-only focused "
            "adversarial reviewer である。"
        ),
    ]
    fullwidth_whitespace_cases = [
        "あなたは dev-wave 段6　fix　 後の read-only focused reviewer です。",
        (
            "あなたは Izanagi dev-wave 段6　fix2　　後の read-only focused "
            "adversarial reviewer である。"
        ),
    ]

    assert [
        (LEDGER._classify_stage(prompt)[0], expected)
        for prompt, expected in existing_cases
    ] == [(expected, expected) for _, expected in existing_cases]
    assert [
        LEDGER._classify_stage(prompt)[0] for prompt in focus_whitespace_cases
    ] == ["focus"] * 4
    assert [
        LEDGER._classify_stage(prompt)[0]
        for prompt in fullwidth_whitespace_cases
    ] == ["focus"] * 2


def test_focused_reviewer_without_fix_word_is_focus(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = {
        "id": "61000000-0000-0000-0000-000000000001",
        "prompt": "あなたは段6の read-only focused adversarial reviewer である。",
    }
    root = _materialize(tmp_path / "sessions", [spec])
    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 0
    assert stderr == ""
    assert output["sessions"][0]["stage"] == "focus"


def test_quoted_role_below_leading_line_cannot_hijack_stage_m11(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("stage_hijack"))
    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 0
    assert stderr == ""
    assert output["sessions"][0]["stage"] == "review"
    assert output["issues"] == {}


def test_conflicting_stages_on_leading_line_are_ambiguous(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = {
        "id": "62000000-0000-0000-0000-000000000001",
        "prompt": (
            "あなたは段2の read-only Codex planner である。"
            "あなたは段6の read-only adversarial reviewer である。"
        ),
    }
    root = _materialize(tmp_path / "sessions", [spec])
    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 2
    assert output["sessions"][0]["stage"] == "unclassified"
    assert list(output["issues"]) == ["ambiguous_stage"]
    assert "ambiguous stage" in stderr


def test_stage_map_overrides_rule_and_unknown_id_fails_strict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = _healthy_specs()[0]
    root = _materialize(tmp_path / "sessions", [spec])
    stage_map = json.dumps(
        {spec["id"]: "focus", "ffffffff-ffff-ffff-ffff-ffffffffffff": "review"}
    )
    rc, output, stderr = _run_json(
        capsys, root, "--stage-map", stage_map, "--strict"
    )
    assert rc == 2
    assert output["sessions"][0]["stage"] == "focus"
    assert "stage-map unknown session_id" in stderr


def test_stage_map_classifies_otherwise_unclassified_session(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = _case("unclassified")[0]
    root = _materialize(tmp_path / "sessions", [spec])
    stage_map = json.dumps({spec["id"]: "author"})
    rc, output, stderr = _run_json(
        capsys, root, "--stage-map", stage_map, "--strict"
    )
    assert rc == 0
    assert stderr == ""
    assert output["sessions"][0]["stage"] == "author"


def test_cwd_filters_are_or_and_preserve_timestamp_order(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    specs = _healthy_specs()[:3]
    specs[0]["cwd"] = "/waves/alpha"
    specs[1]["cwd"] = "/waves/ignored"
    specs[2]["cwd"] = "/waves/beta"
    root = _materialize(tmp_path / "sessions", specs)
    _, output, _ = _run_json(
        capsys,
        root,
        "--cwd-contains",
        "alpha",
        "--cwd-contains",
        "beta",
    )
    assert [row["session_id"] for row in output["sessions"]] == [
        specs[0]["id"],
        specs[2]["id"],
    ]


def test_stage_map_key_filtered_out_by_cwd_is_not_unknown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    specs = _healthy_specs()[:2]
    specs[0]["cwd"] = "/waves/selected"
    specs[1]["cwd"] = "/waves/excluded"
    root = _materialize(tmp_path / "sessions", specs)
    stage_map = json.dumps(
        {specs[0]["id"]: "focus", specs[1]["id"]: "review"}
    )
    rc, output, stderr = _run_json(
        capsys,
        root,
        "--cwd-contains",
        "selected",
        "--stage-map",
        stage_map,
        "--strict",
    )
    assert rc == 0
    assert stderr == ""
    assert output["sessions"][0]["stage"] == "focus"
    assert output["issues"] == {}


def test_manifest_missing_session_fails_without_strict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = _healthy_specs()[0]
    missing_id = "81000000-0000-0000-0000-000000000002"
    root = _materialize(tmp_path / "sessions", [spec])
    manifest = _write_manifest(
        tmp_path / "manifest.json",
        [
            _manifest_session(spec["id"], job_id="present-job"),
            _manifest_session(missing_id, job_id="missing-job"),
        ],
    )
    rc, output, stderr = _run_json(
        capsys, root, "--manifest", str(manifest)
    )
    assert rc == 2
    assert output["totals"]["sessions"] == 1
    assert output["issues"]["manifest_missing_session"] == [missing_id]
    assert "manifest session missing from rollout" in stderr


def test_manifest_v2_reads_sibling_worktree_sessions_and_stage_lane(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    specs = _healthy_specs()[:2]
    root = _materialize(tmp_path / "sessions", specs)
    sessions = [
        _manifest_v2_session(
            specs[0]["id"],
            job_id="author-a",
            stage="author",
            lane=None,
            repo_root="/synthetic/worktree-a",
            receipt_path="/synthetic/receipt-a.json",
        ),
        _manifest_v2_session(
            specs[1]["id"],
            job_id="consult-b",
            stage="consult",
            lane="luna",
            repo_root="/synthetic/worktree-b",
            receipt_path="/synthetic/receipt-b.json",
        ),
    ]
    manifest = tmp_path / "manifest-v2.json"
    manifest.write_text(
        json.dumps(
            {"schema_version": 2, "wave_id": "wave-v2", "sessions": sessions},
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    rc, output, stderr = _run_json(
        capsys, root, "--manifest", str(manifest), "--strict"
    )
    assert rc == 0
    assert stderr == ""
    assert [(row["stage"], row["lane"]) for row in output["sessions"]] == [
        ("author", None),
        ("consult", "luna"),
    ]


def test_empty_manifest_is_rc2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "sessions"
    root.mkdir()
    manifest = _write_manifest(tmp_path / "manifest.json", [])
    rc = LEDGER.main(
        [
            "--sessions-root",
            str(root),
            "--manifest",
            str(manifest),
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "manifest.sessions must contain 1..1024 entries" in captured.err


def test_job_count_is_distinct_job_id_under_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    specs = _healthy_specs()[:3]
    specs[1]["prompt"] = "あなたは段2の read-only Codex planner である。retry"
    root = _materialize(tmp_path / "sessions", specs)
    manifest = _write_manifest(
        tmp_path / "manifest.json",
        [
            _manifest_session(
                specs[0]["id"], job_id="planner-job", attempt_index=1
            ),
            _manifest_session(
                specs[1]["id"], job_id="planner-job", attempt_index=2
            ),
            _manifest_session(
                specs[2]["id"], job_id="consult-job", attempt_index=1
            ),
        ],
    )
    worklog = _write_worklog(
        tmp_path / "worklog.md",
        "エージェント工数: Codex 2 job "
        "(planner 1 / consult 1 / author・fix 0 / review 0)",
    )
    rc, output, stderr = _run_json(
        capsys,
        root,
        "--manifest",
        str(manifest),
        "--worklog",
        str(worklog),
        "--worklog-entry",
        "対象 wave",
        "--strict",
    )
    rows = output["sessions"]
    assert rc == 0
    assert stderr == ""
    assert output["issues"] == {}
    assert output["totals"]["sessions"] == 3
    assert [row["job_id"] for row in rows] == [
        "planner-job",
        "planner-job",
        "consult-job",
    ]
    assert [row["attempt_index"] for row in rows] == [1, 2, 1]
    assert [row["retry_group"] for row in rows] == [
        "planner-job",
        "planner-job",
        "consult-job",
    ]
    assert [row["retry_index"] for row in rows] == [1, 2, 1]
    assert [row["prompt_hash"] for row in rows] == [None, None, None]


@pytest.mark.parametrize(
    "mismatch", ["filename", "session_meta", "session_meta_case"]
)
def test_manifest_selector_requires_filename_meta_and_manifest_three_way_match(
    mismatch: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    spec = _healthy_specs()[0]
    if mismatch == "session_meta":
        spec["meta_id"] = "82000000-0000-0000-0000-000000000099"
    elif mismatch == "session_meta_case":
        spec["id"] = "abcdefab-0000-0000-0000-000000000001"
        spec["meta_id"] = spec["id"].upper()
    root = _materialize(tmp_path / "sessions", [spec])
    if mismatch == "filename":
        rollout = next(root.glob("rollout-*.jsonl"))
        rollout.rename(
            rollout.with_name(
                rollout.name.replace(
                    spec["id"], "82000000-0000-0000-0000-000000000098"
                )
            )
        )
    manifest = _write_manifest(
        tmp_path / "manifest.json", [_manifest_session(spec["id"])]
    )
    rc, output, _ = _run_json(capsys, root, "--manifest", str(manifest))
    assert rc == 2
    assert output["totals"]["sessions"] == 0
    assert output["issues"]["manifest_missing_session"] == [spec["id"]]


def test_manifest_exact_meta_is_selected_and_multiple_meta_issue_remains(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = {
        **_healthy_specs()[0],
        "meta_id": "83000000-0000-0000-0000-000000000099",
        "cwd": "/synthetic/foreign",
        "extra_meta": [
            {
                "session_id": _healthy_specs()[0]["id"],
                "timestamp": "2026-01-01T01:02:03Z",
                "cwd": "/synthetic/exact",
            }
        ],
    }
    root = _materialize(tmp_path / "sessions", [spec])
    manifest = _write_manifest(
        tmp_path / "manifest.json",
        [_manifest_session(spec["id"], job_id="exact-job")],
    )
    rc, output, stderr = _run_json(
        capsys, root, "--manifest", str(manifest)
    )
    row = output["sessions"][0]
    assert rc == 0
    assert stderr == ""
    assert row["session_id"] == spec["id"]
    assert row["job_id"] == "exact-job"
    assert row["timestamp"] == "2026-01-01T01:02:03Z"
    assert row["cwd"] == "/synthetic/exact"
    assert list(output["issues"]) == ["multiple_session_meta"]


def test_manifest_and_cwd_contains_are_argparse_incompatible(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = _healthy_specs()[0]
    root = _materialize(tmp_path / "sessions", [spec])
    manifest = _write_manifest(
        tmp_path / "manifest.json", [_manifest_session(spec["id"])]
    )
    with pytest.raises(SystemExit) as raised:
        LEDGER.main(
            [
                "--sessions-root",
                str(root),
                "--manifest",
                str(manifest),
                "--cwd-contains",
                "wave",
            ]
        )
    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert "--manifest と --cwd-contains は同時指定できない" in captured.err


def _invalid_manifest(case: str) -> dict[str, Any]:
    first_id = "abcdefab-0000-0000-0000-000000000001"
    data = _manifest_data([_manifest_session(first_id)])
    if case == "unknown_root":
        data["unknown"] = "x"
    elif case == "missing_root":
        del data["wave_id"]
    elif case == "schema_bool":
        data["schema_version"] = True
    elif case == "bad_wave_id":
        data["wave_id"] = "bad wave"
    elif case == "relative_repo":
        data["repo_root"] = "relative/repo"
    elif case == "uppercase_commit":
        data["base_commit"] = "A" * 40
    elif case == "unknown_session":
        data["sessions"][0]["unknown"] = "x"
    elif case == "attempt_bool":
        data["sessions"][0]["attempt_index"] = True
    elif case == "uppercase_uuid":
        data["sessions"][0]["session_id"] = first_id.upper()
    elif case == "duplicate_attempt":
        data["sessions"].append(
            _manifest_session(
                "84000000-0000-0000-0000-000000000002",
                job_id="job-1",
                attempt_index=1,
            )
        )
    elif case == "duplicate_session":
        data["sessions"].append(
            _manifest_session(first_id, job_id="job-2")
        )
    elif case == "too_many_sessions":
        data["sessions"] = [
            _manifest_session(
                f"84000000-0000-0000-0000-{index:012x}",
                attempt_index=index,
            )
            for index in range(1, 1026)
        ]
    else:
        raise AssertionError(case)
    return data


@pytest.mark.parametrize(
    "case",
    [
        "unknown_root",
        "missing_root",
        "schema_bool",
        "bad_wave_id",
        "relative_repo",
        "uppercase_commit",
        "unknown_session",
        "attempt_bool",
        "uppercase_uuid",
        "duplicate_attempt",
        "duplicate_session",
        "too_many_sessions",
    ],
)
def test_manifest_structural_errors_are_rc2_without_strict(
    case: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "sessions"
    root.mkdir()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(_invalid_manifest(case), separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    rc = LEDGER.main(
        [
            "--sessions-root",
            str(root),
            "--manifest",
            str(manifest),
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert captured.err.startswith("error: ")


def test_manifest_duplicate_json_key_is_rc2_without_strict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "sessions"
    root.mkdir()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"schema_version":1,"schema_version":1,'
        '"wave_id":"wave-1","repo_root":"/synthetic/repo",'
        f'"base_commit":"{"a" * 40}",'
        '"sessions":[{"job_id":"job-1","attempt_index":1,'
        '"session_id":"85000000-0000-0000-0000-000000000001"}]}\n',
        encoding="utf-8",
    )
    rc = LEDGER.main(
        [
            "--sessions-root",
            str(root),
            "--manifest",
            str(manifest),
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "duplicate key" in captured.err


def test_missing_manifest_file_is_rc2_without_strict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "sessions"
    root.mkdir()
    rc = LEDGER.main(
        [
            "--sessions-root",
            str(root),
            "--manifest",
            str(tmp_path / "missing.json"),
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "manifest を読めない" in captured.err


def test_missing_sessions_root_is_an_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "does-not-exist"
    rc = LEDGER.main(["--sessions-root", str(root), "--json", "--strict"])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "sessions root が存在する directory ではない" in captured.err


def test_empty_sessions_root_fails_strict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "empty"
    root.mkdir()
    rc, output, stderr = _run_json(capsys, root, "--strict")
    assert rc == 2
    assert output["totals"]["sessions"] == 0
    assert list(output["issues"]) == ["no_selected_sessions"]
    assert "no selected sessions" in stderr


def test_zero_selected_sessions_is_the_only_strict_failure_m10(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("no_selected"))
    rc, output, stderr = _run_json(
        capsys, root, "--cwd-contains", "target-wave", "--strict"
    )
    assert rc == 2
    assert output["totals"]["sessions"] == 0
    assert list(output["issues"]) == ["no_selected_sessions"]
    assert "no selected sessions" in stderr


def test_last_cumulative_usage_and_non_null_info_define_totals(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = {
        "id": "90000000-0000-0000-0000-000000000001",
        "prompt": "あなたは段2の read-only Codex planner である。",
        "totals": [[50, 10, 5, 55], [300, 100, 80, 380]],
        "lasts": [[50, 10, 5, 55], [250, 90, 75, 325]],
        "null_token_info": True,
    }
    root = _materialize(tmp_path / "sessions", [spec])
    _, output, _ = _run_json(capsys, root)
    row = output["sessions"][0]
    assert row["model_calls"] == 2
    assert row["turn_contexts"] == 1
    assert row["cli_reported"] == 280
    assert row["per_turn_sum"] == 280
    assert row["total_tokens_raw"] == 380


@pytest.mark.parametrize("value", ["1,234", "１，２３４", "1234", "１２３４"])
def test_worklog_numbers_accept_width_and_separator_variants(value: str) -> None:
    assert LEDGER._number(value) == 1234


def test_human_and_json_outputs_use_independent_literal_oracles(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _case("compaction"))
    rc = LEDGER.main(["--sessions-root", str(root)])
    table = capsys.readouterr().out
    assert rc == 0
    _, output, _ = _run_json(capsys, root)
    total_line = next(line for line in table.splitlines() if line.startswith("TOTAL"))
    assert total_line == (
        "TOTAL\tsessions=1\tmodel_calls=2\tturn_contexts=1"
        "\tinput_tokens=160\tcached_input_tokens=40\toutput_tokens=50"
        "\treasoning_output_tokens=0\tcli_reported=170\tper_turn_sum=240"
        "\tcumulative_minus_per_turn=-70\tcontext_compacted=0"
        "\tthread_rolled_back=0\tturn_aborted=0"
    )
    assert output["totals"] == {
        "sessions": 1,
        "model_calls": 2,
        "turn_contexts": 1,
        "input_tokens": 160,
        "cached_input_tokens": 40,
        "output_tokens": 50,
        "reasoning_output_tokens": 0,
        "cli_reported": 170,
        "per_turn_sum": 240,
        "cumulative_minus_per_turn": -70,
        "context_compacted": 0,
        "thread_rolled_back": 0,
        "turn_aborted": 0,
    }


def test_legacy_selector_t179_frozen_golden_without_manifest_p2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(
        tmp_path / "sessions", _t179_frozen_synthetic_specs()
    )
    rc, output, stderr = _run_json(
        capsys,
        root,
        "--cwd-contains",
        "t179-frozen-wave",
        "--strict",
    )
    assert rc == 0
    assert stderr == ""
    assert list(output) == ["issues", "sessions", "totals"]
    assert list(output["issues"]) == []
    assert output["totals"] == {
        "sessions": 10,
        "model_calls": 434,
        "turn_contexts": 10,
        "input_tokens": 2_757_982,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "cli_reported": 2_757_982,
        "per_turn_sum": 2_757_982,
        "cumulative_minus_per_turn": 0,
        "context_compacted": 0,
        "thread_rolled_back": 0,
        "turn_aborted": 0,
    }
    assert [
        (row["stage"], row["model_calls"], row["cli_reported"])
        for row in output["sessions"]
    ] == [
        ("plan", 39, 224_150),
        ("consult", 31, 196_092),
        ("consult", 31, 196_093),
        ("author", 47, 171_736),
        ("fix", 50, 302_867),
        ("fix", 50, 302_867),
        ("review", 43, 272_276),
        ("review", 44, 272_277),
        ("focus", 49, 409_812),
        ("focus", 50, 409_812),
    ]
    assert tuple(output["sessions"][0]) == (
        "cached_input_tokens",
        "cli_reported",
        "context_compacted",
        "cumulative_minus_per_turn",
        "cwd",
        "exit_code",
        "input_tokens",
        "model",
        "model_calls",
        "outcome",
        "output_tokens",
        "path",
        "per_turn_sum",
        "prompt_hash",
        "reasoning",
        "reasoning_output_tokens",
        "retry_group",
        "retry_index",
        "session_id",
        "stage",
        "thread_rolled_back",
        "timestamp",
        "total_tokens_raw",
        "turn_aborted",
        "turn_contexts",
    )

    assert (
        LEDGER.main(
            [
                "--sessions-root",
                str(root),
                "--cwd-contains",
                "t179-frozen-wave",
            ]
        )
        == 0
    )
    table = capsys.readouterr()
    assert table.err == ""
    assert table.out.splitlines()[0] == (
        "timestamp\tsession_id\tstage\toutcome\texit_code\tmodel"
        "\treasoning\tmodel_calls\tturn_contexts\tinput_tokens"
        "\tcached_input_tokens\toutput_tokens\treasoning_output_tokens"
        "\tcli_reported\tper_turn_sum\tcumulative_minus_per_turn"
        "\ttotal_tokens_raw\tcontext_compacted\tthread_rolled_back"
        "\tturn_aborted\tretry_group\tretry_index\tpath"
    )
    assert not any(
        line.startswith("ISSUE\t") for line in table.out.splitlines()
    )


def test_manifest_t179_frozen_synthetic_stage_aggregates(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    specs = _t179_frozen_synthetic_specs()
    root = _materialize(tmp_path / "sessions", specs)
    manifest = _write_manifest(
        tmp_path / "manifest.json",
        [
            _manifest_session(spec["id"], job_id=f"job-{index}")
            for index, spec in enumerate(specs, 1)
        ],
    )
    rc, output, stderr = _run_json(
        capsys, root, "--manifest", str(manifest), "--strict"
    )
    assert rc == 0
    assert stderr == ""
    assert output["issues"] == {}
    assert output["totals"] == {
        "sessions": 10,
        "model_calls": 434,
        "turn_contexts": 10,
        "input_tokens": 2_757_982,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "cli_reported": 2_757_982,
        "per_turn_sum": 2_757_982,
        "cumulative_minus_per_turn": 0,
        "context_compacted": 0,
        "thread_rolled_back": 0,
        "turn_aborted": 0,
    }
    assert {
        stage: (
            sum(row["stage"] == stage for row in output["sessions"]),
            sum(
                row["model_calls"]
                for row in output["sessions"]
                if row["stage"] == stage
            ),
            sum(
                row["cli_reported"]
                for row in output["sessions"]
                if row["stage"] == stage
            ),
        )
        for stage in ("plan", "consult", "author", "review", "fix", "focus")
    } == {
        "plan": (1, 39, 224_150),
        "consult": (2, 62, 392_185),
        "author": (1, 47, 171_736),
        "review": (2, 87, 544_553),
        "fix": (2, 100, 605_734),
        "focus": (2, 99, 819_624),
    }


def test_output_validator_acceptance_is_identical_in_both_directions(
    tmp_path: Path,
) -> None:
    valid = _valid_agent()
    short_with_summary = "短い。\n## 総括\n完了"
    no_summary = "本文だけです。" * 100
    fenced_summary_only = "本文です。" * 100 + "\n```\n## 総括\n```\n"
    oversized = (
        "x" * (LEDGER._VALIDATOR._MAX_READ_BYTES + 1) + "\n## 総括\n完了"
    )
    cases = [
        ("completed", valid, True),
        ("short", short_with_summary, False),
        ("no-summary", no_summary, False),
        ("fenced-only", fenced_summary_only, False),
        ("oversized", oversized, False),
    ]
    heading = LEDGER.re.compile(
        LEDGER._VALIDATOR._DEFAULT_HEADING, LEDGER.re.MULTILINE
    )
    for name, message, expected in cases:
        path = tmp_path / f"{name}.md"
        path.write_bytes(message.encode("utf-8"))
        validator_accepts = not LEDGER._VALIDATOR.check_file(
            path,
            min_bytes=LEDGER._VALIDATOR._DEFAULT_MIN_BYTES,
            heading=heading,
        )
        ledger_accepts = LEDGER._validator_accepts(message)
        assert validator_accepts is expected, name
        assert ledger_accepts is expected, name
        assert ledger_accepts is validator_accepts, name
        record = {
            "turn_aborted": 0,
            "task_complete": True,
            "last_agent_message": message,
        }
        assert LEDGER._classify_outcome(record) == (
            "completed" if expected else "fragment"
        )


def test_output_is_byte_deterministic(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", _healthy_specs())
    assert LEDGER.main(["--sessions-root", str(root), "--json"]) == 0
    first = capsys.readouterr()
    assert LEDGER.main(["--sessions-root", str(root), "--json"]) == 0
    second = capsys.readouterr()
    assert (first.out.encode(), first.err.encode()) == (
        second.out.encode(),
        second.err.encode(),
    )


def test_relative_absolute_and_symlink_roots_produce_identical_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _materialize(tmp_path / "sessions", [_healthy_specs()[0]])
    link = tmp_path / "sessions-link"
    link.symlink_to(root, target_is_directory=True)
    monkeypatch.chdir(tmp_path)
    outputs: list[tuple[str, str]] = []
    for spelling in (Path("sessions"), root, link):
        assert LEDGER.main(
            ["--sessions-root", str(spelling), "--json", "--strict"]
        ) == 0
        captured = capsys.readouterr()
        outputs.append((captured.out, captured.err))
    assert outputs[0] == outputs[1] == outputs[2]


def test_tool_does_not_change_fixture_file_list_or_mtime(
    capsys: pytest.CaptureFixture[str],
) -> None:
    sessions_root = _FIXTURES / "readonly"

    def snapshot() -> list[tuple[str, int]]:
        return [
            (path.relative_to(_FIXTURES).as_posix(), path.stat().st_mtime_ns)
            for path in sorted(_FIXTURES.rglob("*"))
            if path.is_file()
        ]

    before = snapshot()
    rc, output, stderr = _run_json(capsys, sessions_root, "--strict")
    after = snapshot()
    assert rc == 0
    assert stderr == ""
    assert output["totals"]["sessions"] == 1
    assert before == after


def test_tool_import_does_not_create_bytecode_cache(tmp_path: Path) -> None:
    copied_tools = tmp_path / "tools"
    copied_tools.mkdir()
    copied_ledger = shutil.copy2(_LEDGER, copied_tools / _LEDGER.name)
    shutil.copy2(
        _ROOT / "tools" / "check_codex_output.py",
        copied_tools / "check_codex_output.py",
    )
    environment = os.environ.copy()
    environment.pop("PYTHONDONTWRITEBYTECODE", None)
    completed = subprocess.run(
        [
            sys.executable,
            str(copied_ledger),
            "--sessions-root",
            str(_FIXTURES / "readonly"),
            "--strict",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert completed.returncode == 0, completed.stderr
    assert not (copied_tools / "__pycache__").exists()


def test_codex_home_default_is_code_only_and_uses_sessions_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    codex_home = tmp_path / "synthetic-codex-home"
    _materialize(codex_home / "sessions", [_healthy_specs()[0]])
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    rc = LEDGER.main(["--json", "--strict"])
    output = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert output["totals"]["sessions"] == 1


def test_missing_worklog_effort_line_fails_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _materialize(tmp_path / "sessions", [_healthy_specs()[0]])
    worklog = _write_worklog(tmp_path / "worklog.md", "工数記録なし")
    rc, output, stderr = _run_json(
        capsys,
        root,
        "--worklog",
        str(worklog),
        "--worklog-entry",
        "対象 wave",
        "--strict",
    )
    assert rc == 2
    assert "エージェント工数行が見つからない" in stderr
    assert len(output["issues"]["worklog"]) == 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
