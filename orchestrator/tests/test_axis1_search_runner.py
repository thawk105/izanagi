from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from orchestrator.axis1_search.checkpoint import (
    CheckpointError,
    append_attempt_state,
    recover_attempts,
    validate_checkpoint,
    write_checkpoint,
)
from orchestrator.axis1_search.runner import (
    HostLimiter,
    PreflightError,
    Response,
    run_leaf,
)
from orchestrator.axis1_search.validator import (
    ConditionResult,
    derive_axis_status,
    evaluate_aggregate,
    evaluate_leaf,
    evaluate_page,
    verify_registration,
)
from tools.run_axis1_search import build_parser


# These are deliberately local fakes of the stage-4 fixed interface.  The tests
# do not create or import author A's catalog/parser implementation.
@dataclass(frozen=True)
class RequestSpec:
    request_id: str
    leaf_query_id: str
    logical_query_id: str
    index: str
    method: str
    scheme: str
    host: str
    path: str
    query_parameters: tuple[tuple[str, str], ...]
    encoded_url: str
    headers: tuple[tuple[str, str], ...]
    timeout_s: float
    page_number: int
    position_in: str | None
    expected_interpreted_query: str


@dataclass(frozen=True)
class Occurrence:
    index_work_id: str
    page_number: int
    ordinal: int
    raw_date_value: str | None = None
    interpreted_date: str | None = None
    date_missing_reason: str | None = None
    family_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParsedPage:
    index: str
    declared_total: int | None
    capacity_echo: int | None
    actual_count: int
    interpreted_query: str
    position_in: str | None
    position_out: str | None
    occurrences: tuple[Occurrence, ...]
    parse_errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class Catalog:
    registration_epoch: str
    index_policies: dict[str, dict[str, Any]]


def _condition(results: tuple[ConditionResult, ...], number: int) -> ConditionResult:
    return next(item for item in results if item.condition == number)


def _occurrences(count: int, *, prefix: str = "W", page: int = 0, family: str | None = None) -> tuple[Occurrence, ...]:
    return tuple(
        Occurrence(
            f"{prefix}{number}",
            page,
            number,
            family_keys=((family,) if family else ()),
        )
        for number in range(count)
    )


def _page(
    *,
    index: str = "arxiv",
    total: int = 2,
    capacity: int = 2,
    actual: int = 2,
    position_in: str | None = "0",
    position_out: str | None = None,
    occurrences: tuple[Occurrence, ...] | None = None,
) -> ParsedPage:
    return ParsedPage(
        index=index,
        declared_total=total,
        capacity_echo=capacity,
        actual_count=actual,
        interpreted_query="registered query",
        position_in=position_in,
        position_out=position_out,
        occurrences=_occurrences(actual) if occurrences is None else occurrences,
    )


def _all_pass() -> tuple[ConditionResult, ...]:
    return tuple(ConditionResult(number, True, None, "ok") for number in range(1, 7))


def test_condition3_rejects_capacity_echo_as_actual_count() -> None:
    page = _page(total=100, capacity=100, actual=99, occurrences=_occurrences(99))
    results = evaluate_page(page, page_size=100, pagination_kind="offset")
    result = _condition(results, 3)
    assert not result.passed
    assert result.reason_code == "actual_count_mismatch"


def test_condition4_preserves_two_work_ids_with_one_family_key() -> None:
    occurrences = (
        Occurrence("https://openalex.org/W1", 0, 0, family_keys=("doi:10.1/shared",)),
        Occurrence("https://openalex.org/W2", 0, 1, family_keys=("doi:10.1/shared",)),
    )
    page = _page(index="openalex", occurrences=occurrences)
    result = _condition(evaluate_page(page, page_size=2, pagination_kind="cursor"), 4)
    assert result.passed
    assert "2 occurrences" in result.detail


def test_condition5_compares_distinct_work_ids_not_rows() -> None:
    repeated = (
        Occurrence("W1", 0, 0),
        Occurrence("W1", 0, 1),
    )
    page = _page(total=2, actual=2, occurrences=repeated)
    result = _condition(evaluate_leaf((page,), page_size=2), 5)
    assert not result.passed
    assert result.reason_code == "distinct_work_id_total_mismatch"


def test_aggregate_requires_pairwise_disjoint_leaf_work_ids() -> None:
    leaves = {
        "leaf-a": {"work_ids": {"W1", "W2"}, "condition_results": _all_pass()},
        "leaf-b": {"work_ids": {"W2", "W3"}, "condition_results": _all_pass()},
    }
    result = _condition(evaluate_aggregate(leaves), 5)
    assert not result.passed
    assert result.reason_code == "leaf_work_id_overlap"


def test_axis_status_is_derived_not_declared() -> None:
    complete = _all_pass()
    bundle = {
        "axis_complete": True,
        "leaf_results": (complete,),
        "aggregate_results": (complete,),
        "controls_valid": False,
        "supplemental_complete": True,
        "sensitivity_complete": True,
        "classification_complete": True,
        "family_ledger_complete": True,
        "unimplemented_schema_layers": 0,
    }
    assert derive_axis_status(bundle)["axis_complete"] is False
    bundle["axis_complete"] = False
    bundle["controls_valid"] = True
    assert derive_axis_status(bundle)["axis_complete"] is True


def _complete_request(role: str) -> dict[str, Any]:
    return {
        "request_id": "leaf#p0",
        "leaf_query_id": "leaf",
        "logical_query_id": "logical",
        "index": "openalex",
        "request_role": role,
        "executable": role == "continue_cursor",
        "method": "GET",
        "scheme": "https",
        "host": "api.openalex.org",
        "path": "/works",
        "query_parameters": [["cursor", "*"]],
        "encoded_url": "https://api.openalex.org/works?cursor=*",
        "headers": [["Accept", "application/json"]],
        "empty_body_sha256": hashlib.sha256(b"").hexdigest(),
        "timeout_s": 30.0,
        "page_number": 0,
        "position_in": "*",
        "expected_interpreted_query": "registered query",
        "target_run_id": "run-1",
        "target_pass_number": 1 if role != "start_independent_pass" else 2,
        "target_window_number": 1,
        "parent_response_sha256": None,
        "catalog_template_sha256": "1" * 64,
    }


def _checkpoint() -> dict[str, Any]:
    return {
        "schema_version": "izanagi-axis1-search-checkpoint/v2",
        "checkpoint_id": "000001",
        "previous_checkpoint": {
            "path": "output/insights/2026-08-27_t1969-axis1-search-execution/checkpoints/0001.json",
            "bytes": 1,
            "sha256": "2" * 64,
        },
        "registration_epoch": "AX1-20260829-E1",
        "registration_commit": "0" * 40,
        "catalog_path": "catalog.json",
        "catalog_sha256": "3" * 64,
        "bundle_root": "bundle",
        "canonical_runner_argv": ["python3", "tools/run_axis1_search.py"],
        "query_id": "logical",
        "leaf_query_id": "leaf",
        "index": "openalex",
        "run_id": "run-1",
        "pass_number": 1,
        "window_number": 1,
        "state": "paused_quota",
        "resume_action": "continue_cursor",
        "requests": {
            "continue_cursor": _complete_request("continue_cursor"),
            "start_independent_pass": _complete_request("start_independent_pass"),
            "restart_branch": _complete_request("restart_branch"),
        },
        "cursor_state": {
            "previous_request_id": "leaf#p0",
            "parent_response_sha256": "4" * 64,
            "position_in": "*",
            "position_out": "cursor-2",
            "page_number": 0,
            "leaf_ordinal": 0,
        },
        "completed_ledger": {
            "path": "ledgers/leaf.jsonl",
            "primary_key_kind": "index_work_id",
            "row_count": 1,
            "distinct_count": 1,
            "canonicalization": "sorted unique IDs",
            "ledger_sha256": "5" * 64,
            "primary_key_digest": "6" * 64,
        },
        "second_pass": {
            "required": True,
            "state": "not_started",
            "ledger_path": None,
            "primary_key_digest": None,
            "first_primary_key_digest": "6" * 64,
            "matches_first": None,
            "accepted": None,
        },
        "waiting_ruling_ids": [],
        "quota": {
            "index": "openalex",
            "observed_at_utc": "2026-08-29T01:00:00Z",
            "observed_at_jst": "2026-08-29T10:00:00+09:00",
            "limit": 1000,
            "remaining": 40,
            "credits_per_request": 10,
            "reset_seconds": 80000,
            "observed_request_id": "leaf#p0",
            "cost_usd": 0.001,
            "header_evidence": [],
        },
        "last_attempt": {
            "state": "terminal",
            "request_id": "leaf#p0",
            "attempt_number": 1,
            "failure": None,
            "raw_evidence_path": "raw/leaf.gz",
        },
    }


def test_checkpoint_requires_both_complete_requests() -> None:
    checkpoint = _checkpoint()
    del checkpoint["requests"]["start_independent_pass"]
    with pytest.raises(CheckpointError, match="start_independent_pass"):
        validate_checkpoint(checkpoint)


def test_cli_rejects_mode_contradicting_checkpoint() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(
            [
                "--registration-commit",
                "0" * 40,
                "--catalog",
                "catalog.json",
                "--bundle",
                "bundle",
                "--run-id",
                "run-1",
                "--checkpoint",
                "000001.json",
                "--mode",
                "start",
            ]
        )


class _FakeGit:
    def __init__(self, catalog: bytes, frozen: bytes) -> None:
        self.catalog = catalog
        self.frozen = frozen

    def head(self) -> str:
        return "0" * 40

    def status(self, paths: tuple[str, ...]) -> bytes:
        return b""

    def blob(self, commit: str, path: str) -> bytes:
        return self.catalog if path == "catalog.json" else self.frozen

    def tree(self, commit: str, paths: tuple[str, ...]) -> dict[str, tuple[str, str]]:
        return {"frozen.txt": ("100644", "unused-git-object-id")}


def test_preflight_rejects_mutated_frozen_predecessor(tmp_path: Path) -> None:
    (tmp_path / "catalog.json").write_bytes(b"registered catalog")
    (tmp_path / "frozen.txt").write_bytes(b"mutated after base")
    result = verify_registration(
        "0" * 40,
        "catalog.json",
        ("catalog.json",),
        repo_root=tmp_path,
        git_backend=_FakeGit(b"registered catalog", b"base bytes"),
        frozen_paths=("frozen.txt",),
    )
    assert not result.passed
    assert result.reason_code == "frozen_bytes_mismatch"


class _FakeTransport:
    def __init__(self, responses: list[Response]) -> None:
        self.responses = list(responses)
        self.calls: list[RequestSpec] = []

    def get(self, request: RequestSpec) -> Response:
        self.calls.append(request)
        return self.responses.pop(0)


def _builder(index: str):
    host = {"arxiv": "export.arxiv.org", "openalex": "api.openalex.org", "dblp": "dblp.org"}[index]

    def build(catalog: Catalog, leaf: str, page: int, position: str | None) -> RequestSpec:
        actual_position = ("*" if index == "openalex" else "0") if position is None else position
        return RequestSpec(
            request_id=f"{leaf}#p{page}",
            leaf_query_id=leaf,
            logical_query_id="logical",
            index=index,
            method="GET",
            scheme="https",
            host=host,
            path="/works" if index == "openalex" else "/search/publ/api",
            query_parameters=(("position", actual_position),),
            encoded_url=f"https://{host}/{'works' if index == 'openalex' else 'search/publ/api'}?position={actual_position}",
            headers=(("Accept", "application/json"),),
            timeout_s=30.0,
            page_number=page,
            position_in=actual_position,
            expected_interpreted_query="registered query",
        )

    return build


def test_dblp_limiter_enforces_registered_minimum_interval(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text("{}", encoding="utf-8")
    catalog = Catalog(
        "AX1-20260829-E1",
        {"dblp": {"page_size": 2, "minimum_interval_s": 45, "retry_delays_s": []}},
    )
    pages = [
        _page(index="dblp", total=4, actual=2, position_in="0", position_out="2", occurrences=_occurrences(2, prefix="A")),
        _page(index="dblp", total=4, actual=2, position_in="2", position_out=None, occurrences=_occurrences(2, prefix="B", page=1)),
    ]
    response = Response(200, (), b"{}", "https://dblp.org/search/publ/api", 0.1)
    transport = _FakeTransport([response, response])
    waits: list[float] = []
    result = run_leaf(
        catalog,
        "leaf",
        run_id="run-1",
        registration_commit="0" * 40,
        catalog_path=str(catalog_path),
        bundle_root=tmp_path / "bundle",
        transport=transport,
        preflight=True,
        request_builder=_builder("dblp"),
        parser=lambda body: pages.pop(0),
        clock=lambda: 0.0,
        sleeper=waits.append,
    )
    assert result.state == "branch_complete"
    assert waits == [45.0]


def test_issued_without_stored_response_recovers_outcome_unknown(tmp_path: Path) -> None:
    wal = tmp_path / "attempts.wal"
    append_attempt_state(wal, "request-1", 1, "prepared", clock=lambda: 0.0)
    append_attempt_state(wal, "request-1", 1, "issued", clock=lambda: 0.0)
    recovered = recover_attempts(wal)
    assert recovered[0]["state"] == "outcome_unknown"
    assert recovered[0]["resume_action"] == "restart_branch"
    assert recovered[0]["reason_code"] == "issued_without_stored_response"


def test_preflight_failure_causes_zero_transport_calls(tmp_path: Path) -> None:
    transport = _FakeTransport([])
    with pytest.raises(PreflightError):
        run_leaf(
            Catalog("AX1-20260829-E1", {}),
            "leaf",
            run_id="run-1",
            registration_commit="0" * 40,
            catalog_path=str(tmp_path / "missing-catalog.json"),
            bundle_root=tmp_path / "bundle",
            transport=transport,
            preflight=False,
            request_builder=_builder("arxiv"),
            parser=lambda body: None,
            clock=lambda: 0.0,
            sleeper=lambda seconds: None,
        )
    assert transport.calls == []


def test_accounting_complete_does_not_imply_retrieval_complete() -> None:
    incomplete = list(_all_pass())
    incomplete[-1] = ConditionResult(6, False, "incomplete_state", "paused_quota")
    status = derive_axis_status(
        {
            "accounting_complete": True,
            "leaf_results": (tuple(incomplete),),
            "aggregate_results": (_all_pass(),),
            "controls_valid": True,
            "supplemental_complete": True,
            "sensitivity_complete": True,
            "classification_complete": True,
            "family_ledger_complete": True,
            "unimplemented_schema_layers": 0,
        }
    )
    assert status["retrieval_complete"] is False
    assert status["axis_complete"] is False


def test_quota_reserve_stops_before_exhaustion(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text("{}", encoding="utf-8")
    catalog = Catalog(
        "AX1-20260829-E1",
        {"openalex": {"page_size": 2, "minimum_interval_s": 1, "retry_delays_s": []}},
    )
    first_page = _page(
        index="openalex",
        total=4,
        capacity=2,
        actual=2,
        position_in="*",
        position_out="cursor-2",
        occurrences=_occurrences(2),
    )
    response = Response(
        200,
        (
            ("x-ratelimit-limit", "1000"),
            ("x-ratelimit-remaining", "35"),
            ("x-ratelimit-credits-used", "10"),
            ("x-ratelimit-reset", "80000"),
        ),
        json.dumps({"meta": {"cost_usd": 0.001}}).encode(),
        "https://api.openalex.org/works",
        0.1,
    )
    transport = _FakeTransport([response])
    result = run_leaf(
        catalog,
        "leaf",
        run_id="run-1",
        registration_commit="0" * 40,
        catalog_path=str(catalog_path),
        bundle_root=tmp_path / "bundle",
        transport=transport,
        preflight=True,
        request_builder=_builder("openalex"),
        parser=lambda body: first_page,
        clock=lambda: 0.0,
        sleeper=lambda seconds: None,
    )
    assert result.state == "paused_quota"
    assert result.reason_code == "quota_reserve"
    assert len(transport.calls) == 1
    assert result.checkpoint_path is not None


def test_condition2_rejects_silent_truncation() -> None:
    page = _page(
        index="openalex",
        total=10,
        capacity=5,
        actual=4,
        position_in="*",
        position_out="next",
        occurrences=_occurrences(4),
    )
    result = _condition(evaluate_page(page, page_size=5, pagination_kind="cursor"), 2)
    assert not result.passed
    assert result.reason_code == "silent_truncation"


def test_positive_p1_arxiv_terminal_page_and_leaf_complete() -> None:
    pages = (
        _page(total=505, capacity=200, actual=200, position_in="0", position_out="200", occurrences=_occurrences(200, prefix="A")),
        _page(total=505, capacity=200, actual=200, position_in="200", position_out="400", occurrences=_occurrences(200, prefix="B", page=1)),
        _page(total=505, capacity=200, actual=105, position_in="400", position_out=None, occurrences=_occurrences(105, prefix="C", page=2)),
    )
    assert all(item.passed for item in evaluate_leaf(pages, page_size=200, pagination_kind="offset"))


def test_positive_p2_distinct_work_ids_same_family_remain_complete() -> None:
    records = (
        Occurrence("W1", 0, 0, family_keys=("doi:shared",)),
        Occurrence("W2", 0, 1, family_keys=("doi:shared",)),
    )
    assert all(item.passed for item in evaluate_leaf((_page(occurrences=records),), page_size=2))


def test_positive_p3_dblp_terminal_page_is_accepted() -> None:
    page = _page(index="dblp", total=36, capacity=36, actual=36, occurrences=_occurrences(36))
    assert all(item.passed for item in evaluate_leaf((page,), page_size=100, pagination_kind="offset"))


def test_positive_p4_empty_leaf_is_accepted() -> None:
    page = _page(total=0, capacity=200, actual=0, occurrences=())
    assert all(item.passed for item in evaluate_leaf((page,), page_size=200, pagination_kind="offset"))


def test_checkpoint_writer_is_create_only_and_six_digit(tmp_path: Path) -> None:
    checkpoint = _checkpoint()
    path = write_checkpoint(tmp_path, checkpoint)
    assert path.name == "000001.json"
    with pytest.raises(FileExistsError):
        write_checkpoint(path, checkpoint)


def test_leaf_rejects_record_outside_registered_shard() -> None:
    record = Occurrence("W1", 0, 0, raw_date_value="2025", interpreted_date="2025-12-31")
    page = _page(total=1, capacity=1, actual=1, occurrences=(record,))
    result = _condition(
        evaluate_leaf(
            (page,),
            page_size=1,
            shard_lower="2026-01-01",
            shard_upper="2026-12-31",
        ),
        5,
    )
    assert not result.passed
    assert result.reason_code == "record_outside_shard"


def test_leaf_keeps_missing_date_as_ruling_item() -> None:
    record = Occurrence("W1", 0, 0, date_missing_reason="dblp_year_missing")
    page = _page(total=1, capacity=1, actual=1, occurrences=(record,))
    result = _condition(
        evaluate_leaf(
            (page,),
            page_size=1,
            shard_lower="2026-01-01",
            shard_upper="2026-12-31",
        ),
        5,
    )
    assert result.passed
    assert "1 records remain for date ruling" in result.detail


def test_checkpoint_rejects_not_applicable_for_unstarted_branch() -> None:
    checkpoint = _checkpoint()
    checkpoint["state"] = "not_started"
    checkpoint["resume_action"] = "not_applicable"
    checkpoint["pass_number"] = 0
    checkpoint["window_number"] = 0
    with pytest.raises(CheckpointError, match="illegal state/resume_action"):
        validate_checkpoint(checkpoint)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
