from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
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
    HTTPSOnlyTransport,
    PreflightError,
    QuotaObservation,
    Response,
    TransportError,
    _independent_pass_required,
    _load_completed_prefix,
    _merge_quota,
    _minimum_interval,
    _persist_quota,
    _resume_from_checkpoint_for_test,
    _run_leaf_for_test,
    finalize_bundle,
    observe_quota,
    control_leaf_query_id,
    run_leaf,
)
from orchestrator.axis1_search.validator import (
    FROZEN_BASE_COMMIT,
    FROZEN_PREDECESSOR_PATHS,
    ConditionResult,
    SubprocessGit,
    VerificationResult,
    derive_axis_status,
    evaluate_aggregate,
    evaluate_leaf,
    evaluate_page,
    _production_axis_status,
    _manifest_entries,
    verify_registration,
    verify_bundle,
)
from tools import run_axis1_search as run_axis1_search_cli
from tools.run_axis1_search import build_parser


ROOT = Path(__file__).resolve().parents[2]


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
    independent_pass_required: bool = False
    expected_oqo: Any = None

    def logical_query(self, query_id: str) -> Any:
        return type(
            "LogicalQuery",
            (),
            {
                "query_id": query_id,
                "kind": "leaf",
                "shard_lower": None,
                "shard_upper": None,
                "independent_pass_required": self.independent_pass_required,
                "expected_oqo": self.expected_oqo,
            },
        )()


def _condition(results: tuple[ConditionResult, ...], number: int) -> ConditionResult:
    return next(item for item in results if item.condition == number)


def _occurrences(count: int, *, prefix: str = "W", page: int = 0, family: str | None = None) -> tuple[Occurrence, ...]:
    return tuple(
        Occurrence(
            f"{prefix}{number}",
            page,
            number,
            raw_date_value="2026-01-01",
            interpreted_date="2026-01-01",
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


def test_registered_text_echo_normalizations_are_narrow() -> None:
    page = _page(total=0, capacity=200, actual=0, occurrences=())
    page = ParsedPage(
        **{
            **page.__dict__,
            "interpreted_query": "arXiv%20Query:%20submittedDate:%22199101010000%20TO%20199112312359%22",
        }
    )
    accepted = evaluate_page(
        page,
        page_size=200,
        expected_interpreted_query="arXiv Query:   submittedDate:[199101010000 TO 199112312359]",
    )
    assert _condition(accepted, 1).passed
    rejected = evaluate_page(
        page,
        page_size=200,
        expected_interpreted_query="arXiv Query: extra submittedDate:[199101010000 TO 199112312359]",
    )
    assert _condition(rejected, 1).reason_code == "interpreted_query_mismatch"


def test_openalex_condition1_compares_structured_oqo_not_oql_text() -> None:
    page = _page(index="openalex", total=0, capacity=200, actual=0, occurrences=())
    page = ParsedPage(**{**page.__dict__, "interpreted_query": "different formatting"})
    structure = {
        "get_rows": "works",
        "filter_rows": [{"column_id": "to_publication_date", "value": "2026-12-31"}],
    }
    accepted = evaluate_page(
        page,
        page_size=200,
        expected_interpreted_structure=structure,
        actual_interpreted_structure=structure,
        pagination_kind="cursor",
    )
    assert _condition(accepted, 1).passed
    rejected = evaluate_page(
        page,
        page_size=200,
        expected_interpreted_structure=structure,
        actual_interpreted_structure={"get_rows": "works", "filter_rows": []},
        pagination_kind="cursor",
    )
    assert _condition(rejected, 1).reason_code == "interpreted_query_mismatch"


def test_condition4_preserves_two_work_ids_with_one_family_key() -> None:
    occurrences = (
        Occurrence("https://openalex.org/W1", 0, 0, "2026", "2026-01-01", None, ("doi:10.1/shared",)),
        Occurrence("https://openalex.org/W2", 0, 1, "2026", "2026-01-01", None, ("doi:10.1/shared",)),
    )
    page = _page(index="openalex", occurrences=occurrences)
    result = _condition(evaluate_page(page, page_size=2, pagination_kind="cursor"), 4)
    assert result.passed
    assert "2 occurrences" in result.detail


def test_condition4_requires_exact_page_ordinal_coordinates() -> None:
    records = (
        Occurrence("W1", 1, 0, "2026", "2026-01-01", None, ()),
        Occurrence("W2", 0, 1, "2026", "2026-01-01", None, ()),
    )
    result = _condition(
        evaluate_page(_page(occurrences=records), page_size=2, expected_page_number=1),
        4,
    )
    assert not result.passed
    assert result.reason_code == "occurrence_coordinate_mismatch"


def test_condition4_rejects_illegal_date_missing_matrix() -> None:
    record = Occurrence("W1", 0, 0, None, None, None, ())
    result = _condition(
        evaluate_page(
            _page(total=1, capacity=1, actual=1, occurrences=(record,)),
            page_size=1,
            expected_page_number=0,
        ),
        4,
    )
    assert not result.passed
    assert result.reason_code == "occurrence_date_matrix_invalid"


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
        "leaf-a": {"work_ids": {"W1", "W2"}, "declared_total": 2, "condition_results": _all_pass()},
        "leaf-b": {"work_ids": {"W2", "W3"}, "declared_total": 2, "condition_results": _all_pass()},
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


def _production_status_with_declaration(declaration: dict[str, Any]) -> dict[str, Any]:
    query = type(
        "LogicalQuery",
        (),
        {"query_id": "leaf", "kind": "leaf"},
    )()
    catalog = type("StatusCatalog", (), {"logical_queries": (query,)})()
    return _production_axis_status(
        catalog=catalog,
        leaf_results={"leaf": {"condition_results": _all_pass(), "state": "branch_complete"}},
        aggregate_results={},
        states={"leaf": "branch_complete"},
        declared_bundle=declaration,
    )


def test_bundle_status_ignores_declared_unimplemented_layers() -> None:
    status = _production_status_with_declaration({"unimplemented_schema_layers": 0})
    assert status["retrieval_complete"] is True
    assert status["unimplemented_schema_layer_count"] == 5
    assert status["axis_complete"] is False


def test_bundle_status_ignores_declared_component_flags() -> None:
    status = _production_status_with_declaration(
        {
            "controls_valid": True,
            "supplemental_complete": True,
            "sensitivity_complete": True,
            "classification_complete": True,
            "family_ledger_complete": True,
        }
    )
    assert status["controls_valid"] is False
    assert status["classification_complete"] is False
    assert status["axis_complete"] is False


def test_axis_status_requires_exact_identity_and_legal_state_maps() -> None:
    status = derive_axis_status(
        {
            "leaf_results": {"leaf-a": _all_pass()},
            "aggregate_results": {},
            "expected_leaf_ids": {"leaf-a", "leaf-b"},
            "expected_aggregate_ids": set(),
            "states": {"leaf-a": "not_applicable"},
            "expected_state_ids": {"leaf-a", "leaf-b"},
            "allowed_not_applicable_ids": set(),
            "controls_valid": True,
            "supplemental_complete": True,
            "sensitivity_complete": True,
            "classification_complete": True,
            "family_ledger_complete": True,
            "unimplemented_schema_layers": 0,
        }
    )
    assert status["exact_identity_map"] is False
    assert status["states_legal"] is False
    assert status["retrieval_complete"] is False
    assert status["axis_complete"] is False


def test_production_status_requires_all_263_leaves_and_3_aggregates() -> None:
    from orchestrator.axis1_search.catalog import load_catalog

    catalog = load_catalog(
        str(ROOT / "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json")
    )
    one_leaf = next(query.query_id for query in catalog.logical_queries if query.kind == "leaf")
    status = _production_axis_status(
        catalog=catalog,
        leaf_results={one_leaf: {"condition_results": _all_pass(), "state": "branch_complete"}},
        aggregate_results={},
        states={one_leaf: "branch_complete"},
    )
    assert status["exact_identity_map"] is False
    assert status["retrieval_complete"] is False


@pytest.mark.parametrize(
    ("index", "leaf_query_id"),
    (
        ("arxiv", "AX1-20260829-E1-Q1@arxiv"),
        ("openalex", "AX1-20260829-E1-Q1@openalex"),
        ("dblp", "AX1-20260829-E1-T01@dblp"),
    ),
)
def test_real_catalog_leaf_resolves_every_runner_field(
    index: str, leaf_query_id: str
) -> None:
    from orchestrator.axis1_search import runner as runner_module
    from orchestrator.axis1_search import validator as validator_module
    from orchestrator.axis1_search.catalog import build_request, load_catalog

    catalog_path = (
        ROOT
        / "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json"
    )
    schema_path = ROOT / "orchestrator/schemas/axis1_search_catalog.schema.json"
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    catalog = load_catalog(str(catalog_path))

    catalog_fields = {
        "registration_epoch",
        "index_policies",
        "logical_queries",
        "controls",
    }
    policy_fields = {
        "content_types",
        "minimum_interval_s",
        "page_size",
        "pagination_kind",
        "retry_delays_s",
    }
    query_fields = {
        "query_id",
        "kind",
        "index",
        "branch",
        "parent_id",
        "shard_lower",
        "shard_upper",
        "independent_pass_required",
        "expected_openalex_oqo",
    }
    request_fields = {
        "request_id",
        "leaf_query_id",
        "logical_query_id",
        "index",
        "method",
        "scheme",
        "host",
        "path",
        "query_parameters",
        "encoded_url",
        "headers",
        "timeout_s",
        "page_number",
        "position_in",
        "expected_interpreted_query",
    }

    assert catalog_fields <= document.keys()
    assert catalog_fields <= schema["properties"].keys()
    assert catalog_fields <= set(schema["required"])
    assert policy_fields <= document["index_policies"][index].keys()
    assert policy_fields <= schema["definitions"]["index_policy"]["properties"].keys()
    assert policy_fields <= set(schema["definitions"]["index_policy"]["required"])
    raw_query = next(
        item for item in document["logical_queries"] if item["query_id"] == leaf_query_id
    )
    assert query_fields <= raw_query.keys()
    assert query_fields <= schema["definitions"]["logical_query"]["properties"].keys()
    assert query_fields <= set(schema["definitions"]["logical_query"]["required"])
    assert {"control_id", "indexes"} <= document["controls"][0].keys()
    assert {"control_id", "indexes"} <= schema["definitions"]["control"]["properties"].keys()
    assert {"control_id", "indexes"} <= set(
        schema["definitions"]["control"]["required"]
    )

    query = runner_module._logical_query(catalog, leaf_query_id)
    request = build_request(catalog, leaf_query_id, 0, None)
    assert query.query_id == leaf_query_id
    assert query.index == index
    assert request_fields == set(request.__dict__)
    assert (
        runner_module._independent_pass_required(catalog, leaf_query_id)
        is query.independent_pass_required
    )
    assert runner_module._registered_content_types(catalog, index) == frozenset(
        document["index_policies"][index]["content_types"]
    )
    assert runner_module._minimum_interval(catalog, index) >= float(
        document["index_policies"][index]["minimum_interval_s"]
    )
    assert (
        runner_module._page_size(catalog, index)
        == document["index_policies"][index]["page_size"]
    )
    assert (
        runner_module._pagination_kind(catalog, index)
        == document["index_policies"][index]["pagination_kind"]
    )
    assert runner_module._retry_delays(catalog, index) == tuple(
        document["index_policies"][index]["retry_delays_s"]
    )
    if index == "openalex":
        assert query.expected_openalex_oqo is not None
        assert (
            runner_module._expected_openalex_oqo(catalog, leaf_query_id)
            == query.expected_openalex_oqo
        )
        assert (
            validator_module._expected_openalex_structure(query)
            == query.expected_openalex_oqo
        )


@pytest.mark.parametrize(
    ("index", "fixture_name"),
    (
        ("arxiv", "f1_arxiv_terminal.xml"),
        ("openalex", "f2_openalex_terminal.json"),
        ("dblp", "f6_dblp_terminal.json"),
    ),
)
def test_registered_parser_output_fields_match_evidence_schema(
    index: str, fixture_name: str
) -> None:
    from orchestrator.axis1_search import parsers

    parser = {
        "arxiv": parsers.parse_arxiv_page,
        "openalex": parsers.parse_openalex_page,
        "dblp": parsers.parse_dblp_page,
    }[index]
    body = (ROOT / "orchestrator/tests/fixtures/axis1_search" / fixture_name).read_bytes()
    page = parser(body, 0)
    schema = json.loads(
        (
            ROOT / "orchestrator/schemas/axis1_search_page_evidence.schema.json"
        ).read_text(encoding="utf-8")
    )
    parse_fields = schema["definitions"]["parse"]["properties"].keys()
    occurrence_fields = schema["definitions"]["occurrence"]["properties"].keys()

    assert page.index == index
    assert set(parse_fields) == set(schema["definitions"]["parse"]["required"])
    assert set(occurrence_fields) == set(
        schema["definitions"]["occurrence"]["required"]
    )
    assert set(page.__dict__) == set(parse_fields) | {"index", "occurrences"}
    assert page.occurrences
    assert set(page.occurrences[0].__dict__) == set(occurrence_fields)


def test_page_evidence_fields_read_during_resume_exist_in_schema() -> None:
    schema = json.loads(
        (
            ROOT / "orchestrator/schemas/axis1_search_page_evidence.schema.json"
        ).read_text(encoding="utf-8")
    )
    definitions = schema["definitions"]
    expected = {
        "page_evidence": {
            "document_type",
            "identity",
            "failure",
            "parse",
            "request",
            "response",
        },
        "identity": {
            "leaf_query_id",
            "pass_number",
            "page_number",
            "attempt_number",
            "index",
        },
        "request": {"expected_interpreted_query", "position_in", "encoded_url"},
        "response": {"status", "content_type", "final_url", "body_path"},
    }
    for definition, fields in expected.items():
        assert fields <= definitions[definition]["properties"].keys()
        assert fields <= set(definitions[definition]["required"])


def test_manifest_files_mapping_is_not_accepted() -> None:
    with pytest.raises(ValueError, match="files/entries collection"):
        _manifest_entries({"files": {"raw/page.gz": {"sha256": "0" * 64}}})


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
        "canonical_runner_argv": ["python3", "tools/run_axis1_search.py", "--checkpoint", "bundle/checkpoints/000001.json"],
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
            "path": "ledgers/leaf.json",
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


def test_control_cli_has_only_registered_descriptor_and_index_surface() -> None:
    args = build_parser().parse_args(
        [
            "--registration-commit",
            "0" * 40,
            "--catalog",
            "catalog.json",
            "--bundle",
            "bundle",
            "--run-id",
            "run-1",
            "--control-id",
            "C-OP-1",
            "--control-index",
            "arxiv",
        ]
    )
    assert args.control_id == "C-OP-1"
    assert not {"url", "header", "filter"}.intersection(vars(args))


def test_registered_control_resolves_to_catalog_leaf() -> None:
    from orchestrator.axis1_search.catalog import load_catalog

    catalog = load_catalog(
        str(ROOT / "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json")
    )
    query_id = control_leaf_query_id(catalog, "C-OP-1", "arxiv")
    query = catalog.logical_query(query_id)
    assert query.kind == "leaf"
    assert query.index == "arxiv"


def test_control_execution_fails_closed_before_http(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    transport = _FakeTransport([])
    monkeypatch.setattr(
        run_axis1_search_cli,
        "verify_registration",
        lambda *args, **kwargs: VerificationResult(True, None, "ok"),
    )
    monkeypatch.setattr(run_axis1_search_cli, "_load_catalog", lambda path: object())
    result = run_axis1_search_cli.main(
        [
            "--registration-commit",
            "0" * 40,
            "--catalog",
            str(
                ROOT
                / "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json"
            ),
            "--bundle",
            str(ROOT / "unused-control-bundle"),
            "--run-id",
            "control-run",
            "--control-id",
            "C-OP-1",
            "--control-index",
            "arxiv",
        ],
        transport=transport,
    )
    assert result != 0
    assert transport.calls == []
    output = json.loads(capsys.readouterr().out)
    assert output["reason_code"] == "control_request_unregistered_for_epoch"
    assert "no registered executable request for controls" in output["detail"]


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


class _HeadTreeMismatchGit(_FakeGit):
    def tree(self, commit: str, paths: tuple[str, ...]) -> dict[str, tuple[str, str]]:
        object_id = "baseline-object" if commit == FROZEN_BASE_COMMIT else "head-object"
        return {"frozen.txt": ("100644", object_id)}


def test_preflight_rejects_frozen_tree_changed_in_registration_commit(
    tmp_path: Path,
) -> None:
    (tmp_path / "catalog.json").write_bytes(b"registered catalog")
    (tmp_path / "frozen.txt").write_bytes(b"base bytes")
    result = verify_registration(
        "0" * 40,
        "catalog.json",
        ("catalog.json",),
        repo_root=tmp_path,
        git_backend=_HeadTreeMismatchGit(b"registered catalog", b"base bytes"),
        frozen_paths=("frozen.txt",),
    )
    assert not result.passed
    assert result.reason_code == "frozen_registration_tree_mismatch"


def test_preflight_rejects_mutation_with_real_subprocess_git_and_all_128_paths(
    tmp_path: Path,
) -> None:
    backend = SubprocessGit(ROOT)
    baseline = backend.tree(FROZEN_BASE_COMMIT, FROZEN_PREDECESSOR_PATHS)
    assert len(baseline) == 128
    stable_catalog = FROZEN_PREDECESSOR_PATHS[0]
    regular_paths: list[Path] = []
    for relative, (mode, _object_id) in baseline.items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = backend.blob(FROZEN_BASE_COMMIT, relative)
        if mode == "120000":
            target.symlink_to(raw.decode("utf-8", "surrogateescape"))
        else:
            target.write_bytes(raw)
            target.chmod(0o755 if mode == "100755" else 0o644)
            regular_paths.append(target)
    accepted = verify_registration(
        backend.head(),
        stable_catalog,
        (stable_catalog,),
        repo_root=tmp_path,
        git_backend=backend,
    )
    assert accepted.passed, (accepted.reason_code, accepted.detail)
    regular_paths[-1].write_bytes(regular_paths[-1].read_bytes() + b"mutation")
    rejected = verify_registration(
        backend.head(),
        stable_catalog,
        (stable_catalog,),
        repo_root=tmp_path,
        git_backend=backend,
    )
    assert not rejected.passed
    assert rejected.reason_code == "frozen_bytes_mismatch"


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
    responses = [
        Response(200, (("Content-Type", "application/json"),), b"{}", "https://dblp.org/search/publ/api?position=0", 0.1),
        Response(200, (("Content-Type", "application/json"),), b"{}", "https://dblp.org/search/publ/api?position=2", 0.1),
    ]
    transport = _FakeTransport(responses)
    waits: list[float] = []
    result = _run_leaf_for_test(
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


def test_dblp_minimum_interval_uses_real_catalog_and_floor() -> None:
    from orchestrator.axis1_search.catalog import load_catalog

    real = load_catalog(
        str(ROOT / "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json")
    )
    low = Catalog("AX1-20260829-E1", {"dblp": {"minimum_interval_s": 0}})
    assert _minimum_interval(real, "dblp") == 45.0
    assert _minimum_interval(low, "dblp") == 45.0


def test_host_limiter_pacing_persists_across_sessions(tmp_path: Path) -> None:
    state = tmp_path / "bundle" / "state" / "runtime.json"
    waits: list[float] = []
    HostLimiter(clock=lambda: 0.0, sleeper=waits.append, state_path=state).acquire(
        "dblp.org", 45.0
    )
    HostLimiter(clock=lambda: 0.0, sleeper=waits.append, state_path=state).acquire(
        "dblp.org", 45.0
    )
    assert waits == [45.0]


def test_dblp_restart_budget_persists_across_sessions(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text("{}", encoding="utf-8")
    catalog = Catalog(
        "AX1-20260829-E1",
        {"dblp": {"page_size": 100, "minimum_interval_s": 45, "retry_delays_s": []}},
    )
    failure = Response(
        503,
        (("Content-Type", "application/json"),),
        b"{}",
        "https://dblp.org/search/publ/api?position=0",
        0.1,
    )
    waits: list[float] = []
    first_transport = _FakeTransport([failure, failure])
    first = _run_leaf_for_test(
        catalog,
        "leaf",
        run_id="run-1",
        registration_commit="0" * 40,
        catalog_path=str(catalog_path),
        bundle_root=tmp_path / "bundle",
        transport=first_transport,
        preflight=True,
        request_builder=_builder("dblp"),
        parser=lambda body: None,
        clock=lambda: 0.0,
        sleeper=waits.append,
    )
    assert first.state == "outcome_unknown"
    assert len(first_transport.calls) == 2
    second_transport = _FakeTransport([failure])
    second = _run_leaf_for_test(
        catalog,
        "leaf",
        run_id="run-1",
        registration_commit="0" * 40,
        catalog_path=str(catalog_path),
        bundle_root=tmp_path / "bundle",
        transport=second_transport,
        preflight=True,
        request_builder=_builder("dblp"),
        parser=lambda body: None,
        clock=lambda: 0.0,
        sleeper=waits.append,
    )
    assert second.state == "outcome_unknown"
    assert len(second_transport.calls) == 1
    assert waits.count(45 * 60) == 1


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
        _run_leaf_for_test(
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


def test_production_transport_rejects_unregistered_path_header_and_query() -> None:
    registered = RequestSpec(
        request_id="leaf#p0",
        leaf_query_id="leaf",
        logical_query_id="logical",
        index="openalex",
        method="GET",
        scheme="https",
        host="api.openalex.org",
        path="/works",
        query_parameters=(("per-page", "200"), ("cursor", "*")),
        encoded_url="https://api.openalex.org/works?per-page=200&cursor=%2A",
        headers=(("Accept", "application/json"),),
        timeout_s=30.0,
        page_number=0,
        position_in="*",
        expected_interpreted_query="registered",
    )
    HTTPSOnlyTransport._validate_request(registered)
    for changed in (
        {"path": "/anything", "encoded_url": "https://api.openalex.org/anything?per-page=200&cursor=%2A"},
        {"headers": (("Accept", "application/json"), ("Authorization", "secret"))},
        {"encoded_url": "https://api.openalex.org/works?cursor=%2A&per-page=200"},
    ):
        candidate = RequestSpec(**{**registered.__dict__, **changed})
        with pytest.raises(TransportError):
            HTTPSOnlyTransport._validate_request(candidate)


def test_production_transport_rejects_query_not_registered_in_catalog() -> None:
    from orchestrator.axis1_search.catalog import build_request, load_catalog

    catalog = load_catalog(
        str(ROOT / "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json")
    )
    query = next(
        item
        for item in catalog.logical_queries
        if item.kind == "leaf" and item.index == "openalex"
    )
    registered = build_request(catalog, query.query_id, 0, None)
    candidate = replace(
        registered,
        query_parameters=registered.query_parameters + (("unregistered", "value"),),
        encoded_url=registered.encoded_url + "&unregistered=value",
    )
    # The URL and ordered pairs are internally consistent; only the catalog
    # binding can reject this otherwise valid transport request.
    HTTPSOnlyTransport._validate_request(candidate)
    with pytest.raises(TransportError, match="registered catalog request"):
        HTTPSOnlyTransport._validate_request(candidate, catalog=catalog)


def test_public_runner_has_no_arbitrary_request_injection() -> None:
    parameters = inspect.signature(run_leaf).parameters
    assert "request_builder" not in parameters
    assert "initial_request" not in parameters
    assert "parser" not in parameters


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
        expected_oqo={"get_rows": "works"},
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
            ("Content-Type", "application/json"),
            ("x-ratelimit-limit", "1000"),
            ("x-ratelimit-remaining", "35"),
            ("x-ratelimit-credits-used", "10"),
            ("x-ratelimit-reset", "80000"),
        ),
        json.dumps(
            {
                "meta": {
                    "cost_usd": 0.001,
                    "x_query": {"oqo": {"get_rows": "authors"}},
                }
            }
        ).encode(),
        "https://api.openalex.org/works?position=*",
        0.1,
    )
    transport = _FakeTransport([response])
    result = _run_leaf_for_test(
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
    generated = json.loads(Path(result.checkpoint_path).read_text(encoding="utf-8"))
    assert set(generated["requests"]) >= {"continue_cursor", "start_independent_pass"}
    assert "--checkpoint" in generated["canonical_runner_argv"]
    assert "--query-id" not in generated["canonical_runner_argv"]
    page_evidence = json.loads(
        next((tmp_path / "bundle" / "pages").glob("*.json")).read_text(encoding="utf-8")
    )
    condition1 = next(item for item in page_evidence["completion"] if item["condition"] == 1)
    assert condition1["passed"] is False
    assert condition1["reason_code"] == "interpreted_query_mismatch"


def test_quota_reserve_persists_across_leaf_sessions(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text("{}", encoding="utf-8")
    catalog = Catalog(
        "AX1-20260829-E1",
        {"openalex": {"page_size": 2, "minimum_interval_s": 1, "retry_delays_s": []}},
    )
    page = _page(
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
            ("Content-Type", "application/json"),
            ("x-ratelimit-remaining", "35"),
            ("x-ratelimit-credits-used", "10"),
        ),
        b"{}",
        "https://api.openalex.org/works?position=*",
        0.1,
    )
    first_transport = _FakeTransport([response])
    first = _run_leaf_for_test(
        catalog,
        "leaf-a",
        run_id="run-1",
        registration_commit="0" * 40,
        catalog_path=str(catalog_path),
        bundle_root=tmp_path / "bundle",
        transport=first_transport,
        preflight=True,
        request_builder=_builder("openalex"),
        parser=lambda body: page,
        clock=lambda: 0.0,
        sleeper=lambda seconds: None,
    )
    assert first.state == "paused_quota"
    second_transport = _FakeTransport([])
    second = _run_leaf_for_test(
        catalog,
        "leaf-b",
        run_id="run-1",
        registration_commit="0" * 40,
        catalog_path=str(catalog_path),
        bundle_root=tmp_path / "bundle",
        transport=second_transport,
        preflight=True,
        request_builder=_builder("openalex"),
        parser=lambda body: page,
        clock=lambda: 0.0,
        sleeper=lambda seconds: None,
    )
    assert second.state == "paused_quota"
    assert second_transport.calls == []


def test_resume_merges_digest_verified_prefix_with_real_openalex_parser(tmp_path: Path) -> None:
    from orchestrator.axis1_search.catalog import build_request, load_catalog

    relative_catalog = Path(
        "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json"
    )
    real = load_catalog(str(ROOT / relative_catalog))
    original = next(
        query
        for query in real.logical_queries
        if query.kind == "leaf" and query.index == "openalex" and query.shard_lower is None
    )
    structure = original.expected_openalex_oqo
    query = SimpleNamespace(
        **{
            **original.__dict__,
            "independent_pass_required": False,
        }
    )
    catalog = replace(real, logical_queries=(query,))
    first_request = build_request(catalog, query.query_id, 0, None)
    fixture_templates = [
        json.loads(
            (
                ROOT
                / f"orchestrator/tests/fixtures/axis1_search/f3_openalex_adjacent_page_{page}.json"
            ).read_text(encoding="utf-8")
        )["results"][0]
        for page in (0, 1)
    ]

    def body(request: Any, start: int, count: int, next_cursor: str | None) -> bytes:
        results = []
        for ordinal in range(count):
            result = dict(fixture_templates[request.page_number])
            result["id"] = f"https://openalex.org/W{start + ordinal + 1}"
            result["publication_date"] = "2026-01-01"
            results.append(result)
        return json.dumps(
            {
                "meta": {
                    "count": 201,
                    "per_page": 200,
                    "page": request.page_number + 1,
                    "next_cursor": next_cursor,
                    "x_query": {
                        "oql": "multiline formatting deliberately differs",
                        "oqo": structure,
                        "url": f"/works?cursor={request.position_in}",
                    },
                },
                "results": results,
            }
        ).encode()

    first_body = body(first_request, 0, 200, "CURSOR2")
    bundle = tmp_path / "bundle"
    first = _run_leaf_for_test(
        catalog,
        query.query_id,
        run_id="run-resume",
        registration_commit="0" * 40,
        catalog_path=relative_catalog.as_posix(),
        bundle_root=bundle,
        transport=_FakeTransport(
            [
                Response(
                    200,
                    (
                        ("Content-Type", "application/json"),
                        ("x-ratelimit-remaining", "35"),
                        ("x-ratelimit-credits-used", "10"),
                    ),
                    first_body,
                    first_request.encoded_url,
                    0.1,
                )
            ]
        ),
        preflight=True,
        clock=lambda: 0.0,
        sleeper=lambda seconds: None,
    )
    assert first.state == "paused_quota"
    assert first.checkpoint_path is not None
    checkpoint = json.loads(Path(first.checkpoint_path).read_text(encoding="utf-8"))
    prefix_ledger = bundle / checkpoint["completed_ledger"]["path"]
    assert hashlib.sha256(prefix_ledger.read_bytes()).hexdigest() == checkpoint["completed_ledger"]["ledger_sha256"]

    _persist_quota(
        bundle / "state" / "runtime.json",
        "openalex",
        QuotaObservation(
            "2026-08-30T00:00:00Z",
            "2026-08-30T09:00:00+09:00",
            1000,
            100,
            10,
            80000,
            "window-2-anchor",
            0.001,
            (),
        ),
    )
    second_request = build_request(catalog, query.query_id, 1, "CURSOR2")
    second_body = body(second_request, 200, 1, None)
    resumed = _resume_from_checkpoint_for_test(
        first.checkpoint_path,
        catalog,
        transport=_FakeTransport(
            [
                Response(
                    200,
                    (
                        ("Content-Type", "application/json"),
                        ("x-ratelimit-remaining", "90"),
                        ("x-ratelimit-credits-used", "10"),
                    ),
                    second_body,
                    second_request.encoded_url,
                    0.1,
                )
            ]
        ),
        preflight=True,
        clock=lambda: 1.0,
        sleeper=lambda seconds: None,
    )
    assert resumed.state == "branch_complete"
    assert len(resumed.pages) == 2
    final_ledger = max(
        (json.loads(path.read_text(encoding="utf-8")) for path in bundle.glob("ledgers/*.json")),
        key=lambda value: value["occurrence_count"],
    )
    assert final_ledger["occurrence_count"] == 201
    assert final_ledger["distinct_index_work_id_count"] == 201
    assert final_ledger["occurrences"][0]["page_number"] == 0
    assert final_ledger["occurrences"][-1]["page_number"] == 1
    verification = verify_bundle(
        bundle,
        catalog=catalog,
        catalog_path=ROOT / relative_catalog,
    )
    assert verification.passed, (verification.reason_code, verification.detail)


def test_resume_prefix_marks_unregistered_content_type_response_not_ok(
    tmp_path: Path,
) -> None:
    leaf_query_id = "leaf-resume-content-type"
    bundle = tmp_path / "bundle"
    ledger_path = bundle / "ledgers" / "prefix.json"
    page_path = bundle / "pages" / "prefix.json"
    ledger_path.parent.mkdir(parents=True)
    page_path.parent.mkdir(parents=True)

    ledger = {
        "document_type": "record_occurrence_ledger",
        "leaf_query_id": leaf_query_id,
        "occurrences": [],
    }
    ledger_raw = json.dumps(ledger, sort_keys=True).encode("utf-8")
    ledger_path.write_bytes(ledger_raw)
    encoded_url = "https://dblp.org/search/publ/api?q=registered"
    page_path.write_text(
        json.dumps(
            {
                "document_type": "page_evidence",
                "identity": {
                    "leaf_query_id": leaf_query_id,
                    "pass_number": 1,
                    "page_number": 0,
                    "attempt_number": 1,
                    "index": "dblp",
                },
                "failure": None,
                "parse": {
                    "declared_total": 0,
                    "capacity_echo": 0,
                    "actual_count": 0,
                    "interpreted_query": "registered",
                    "position_in": "0",
                    "position_out": None,
                    "parse_errors": [],
                },
                "request": {
                    "expected_interpreted_query": "registered",
                    "position_in": "0",
                    "encoded_url": encoded_url,
                },
                "response": {
                    "status": 200,
                    "content_type": "application/x-unregistered",
                    "final_url": encoded_url,
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    checkpoint = {
        "leaf_query_id": leaf_query_id,
        "completed_ledger": {
            "path": ledger_path.relative_to(bundle).as_posix(),
            "ledger_sha256": hashlib.sha256(ledger_raw).hexdigest(),
            "primary_key_digest": hashlib.sha256(b"").hexdigest(),
        },
    }
    catalog = Catalog(
        "AX1-20260829-E1",
        {"dblp": {"content_types": ["application/json"]}},
    )

    pages, occurrences, contexts = _load_completed_prefix(
        checkpoint,
        bundle,
        catalog=catalog,
        leaf_query_id=leaf_query_id,
        pass_number=1,
        next_page_number=1,
    )

    assert len(pages) == 1
    assert occurrences == []
    assert contexts[0]["response_ok"] is False
    condition6 = _condition(
        evaluate_page(pages[0], page_size=100, **contexts[0]), 6
    )
    assert not condition6.passed
    assert condition6.reason_code == "response_not_successful"


def test_429_pauses_quota_but_503_is_service_failure(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text("{}", encoding="utf-8")
    catalog = Catalog(
        "AX1-20260829-E1",
        {"openalex": {"page_size": 2, "minimum_interval_s": 1, "retry_delays_s": [0]}},
    )
    response_429 = Response(
        429,
        (("Content-Type", "application/json"), ("x-ratelimit-remaining", "0")),
        b"{}",
        "https://api.openalex.org/works?position=*",
        0.1,
    )
    paused_transport = _FakeTransport([response_429])
    paused = _run_leaf_for_test(
        catalog,
        "leaf-429",
        run_id="run-1",
        registration_commit="0" * 40,
        catalog_path=str(catalog_path),
        bundle_root=tmp_path / "bundle-429",
        transport=paused_transport,
        preflight=True,
        request_builder=_builder("openalex"),
        parser=lambda body: None,
        clock=lambda: 0.0,
        sleeper=lambda seconds: None,
    )
    assert paused.state == "paused_quota"
    assert len(paused_transport.calls) == 1

    response_503 = Response(
        503,
        (("Content-Type", "application/json"),),
        b"{}",
        "https://api.openalex.org/works?position=*",
        0.1,
    )
    failed_transport = _FakeTransport([response_503, response_503])
    failed = _run_leaf_for_test(
        catalog,
        "leaf-503",
        run_id="run-1",
        registration_commit="0" * 40,
        catalog_path=str(catalog_path),
        bundle_root=tmp_path / "bundle-503",
        transport=failed_transport,
        preflight=True,
        request_builder=_builder("openalex"),
        parser=lambda body: None,
        clock=lambda: 0.0,
        sleeper=lambda seconds: None,
    )
    assert failed.state == "outcome_unknown"
    assert len(failed_transport.calls) == 2


def test_failure_without_quota_headers_preserves_known_values() -> None:
    previous_response = Response(
        200,
        (("x-ratelimit-remaining", "50"), ("x-ratelimit-credits-used", "10")),
        b"{}",
        "https://api.openalex.org/works",
        0.1,
    )
    previous = observe_quota(previous_response, "request-1", 0.0)
    failure = observe_quota(
        Response(503, (), b"{}", "https://api.openalex.org/works", 0.1),
        "request-2",
        1.0,
    )
    merged = _merge_quota(previous, failure)
    assert merged.remaining == 50
    assert merged.credits_per_request == 10


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


def test_positive_p1_real_f1_fixture_uses_page_specific_registered_echoes(tmp_path: Path) -> None:
    import xml.etree.ElementTree as ET
    import xml.sax.saxutils

    from orchestrator.axis1_search.catalog import build_request, load_catalog

    relative_catalog = Path(
        "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json"
    )
    real = load_catalog(str(ROOT / relative_catalog))
    original = next(
        query
        for query in real.logical_queries
        if query.kind == "leaf" and query.index == "arxiv" and query.branch == "Q1"
    )
    query = SimpleNamespace(**{**original.__dict__, "independent_pass_required": False})
    catalog = replace(real, logical_queries=(query,))
    requests = [build_request(catalog, query.query_id, page, None) for page in range(3)]

    def full_page(request: Any, start: int, count: int) -> bytes:
        entries = "".join(
            "<entry>"
            f"<id>http://arxiv.org/abs/2601.{start + ordinal:05d}</id>"
            "<published>2026-01-01T00:00:00Z</published>"
            "</entry>"
            for ordinal in range(count)
        )
        return (
            '<feed xmlns="http://www.w3.org/2005/Atom" '
            'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
            f"<title>{xml.sax.saxutils.escape(request.expected_interpreted_query)}</title>"
            "<opensearch:totalResults>505</opensearch:totalResults>"
            f"<opensearch:startIndex>{start}</opensearch:startIndex>"
            "<opensearch:itemsPerPage>200</opensearch:itemsPerPage>"
            f"{entries}</feed>"
        ).encode()

    terminal_root = ET.fromstring(
        (ROOT / "orchestrator/tests/fixtures/axis1_search/f1_arxiv_terminal.xml").read_bytes()
    )
    terminal_root.find("{http://www.w3.org/2005/Atom}title").text = requests[2].expected_interpreted_query
    terminal = ET.tostring(terminal_root, encoding="utf-8")
    bodies = [full_page(requests[0], 0, 200), full_page(requests[1], 200, 200), terminal]
    transport = _FakeTransport(
        [
            Response(
                200,
                (("Content-Type", "application/atom+xml"),),
                body,
                request.encoded_url,
                0.1,
            )
            for request, body in zip(requests, bodies)
        ]
    )
    bundle = tmp_path / "bundle"
    result = _run_leaf_for_test(
        catalog,
        query.query_id,
        run_id="run-p1",
        registration_commit="0" * 40,
        catalog_path=relative_catalog.as_posix(),
        bundle_root=bundle,
        transport=transport,
        preflight=True,
        clock=lambda: 0.0,
        sleeper=lambda seconds: None,
    )
    assert result.state == "branch_complete"
    assert len(result.pages) == 3
    verification = verify_bundle(
        bundle,
        catalog=catalog,
        catalog_path=ROOT / relative_catalog,
    )
    assert verification.passed, (verification.reason_code, verification.detail)


def test_positive_p2_distinct_work_ids_same_family_remain_complete() -> None:
    records = (
        Occurrence("W1", 0, 0, "2026", "2026-01-01", None, ("doi:shared",)),
        Occurrence("W2", 0, 1, "2026", "2026-01-01", None, ("doi:shared",)),
    )
    assert all(item.passed for item in evaluate_leaf((_page(occurrences=records),), page_size=2))


def test_positive_p3_dblp_terminal_page_is_accepted() -> None:
    page = _page(index="dblp", total=36, capacity=36, actual=36, occurrences=_occurrences(36))
    assert all(item.passed for item in evaluate_leaf((page,), page_size=100, pagination_kind="offset"))


def test_positive_p3_real_dblp_parser_echo_content_and_evidence(tmp_path: Path) -> None:
    from orchestrator.axis1_search.catalog import build_request, load_catalog

    relative_catalog = Path(
        "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json"
    )
    real = load_catalog(str(ROOT / relative_catalog))
    original = next(
        query for query in real.logical_queries if query.kind == "leaf" and query.index == "dblp"
    )
    query = SimpleNamespace(**{**original.__dict__, "independent_pass_required": False})
    catalog = replace(real, logical_queries=(query,))
    requests = [build_request(catalog, query.query_id, page, None) for page in (0, 1)]
    terminal_value = json.loads(
        (
            ROOT / "orchestrator/tests/fixtures/axis1_search/f6_dblp_terminal.json"
        ).read_text(encoding="utf-8")
    )
    terminal_value["result"]["query"] = requests[1].expected_interpreted_query
    template_hit = terminal_value["result"]["hits"]["hit"][0]
    first_hits = []
    for ordinal in range(100):
        hit = json.loads(json.dumps(template_hit))
        hit["info"]["key"] = f"journals/example/W{ordinal + 1}"
        first_hits.append(hit)
    first_value = {
        "result": {
            "query": requests[0].expected_interpreted_query,
            "hits": {
                "@total": "136",
                "@sent": "100",
                "@first": "0",
                "hit": first_hits,
            },
        }
    }
    bodies = [json.dumps(first_value).encode(), json.dumps(terminal_value).encode()]
    bundle = tmp_path / "bundle"
    result = _run_leaf_for_test(
        catalog,
        query.query_id,
        run_id="run-p3",
        registration_commit="0" * 40,
        catalog_path=relative_catalog.as_posix(),
        bundle_root=bundle,
        transport=_FakeTransport(
            [
                Response(
                    200,
                    (("Content-Type", "application/json"),),
                    body,
                    request.encoded_url,
                    0.1,
                )
                for request, body in zip(requests, bodies)
            ]
        ),
        preflight=True,
        clock=lambda: 0.0,
        sleeper=lambda seconds: None,
    )
    assert result.state == "branch_complete"
    assert len(result.pages) == 2
    assert list(bundle.glob("pages/*.json"))
    assert list(bundle.glob("ledgers/*.json"))
    verification = verify_bundle(
        bundle,
        catalog=catalog,
        catalog_path=ROOT / relative_catalog,
    )
    assert verification.passed, (verification.reason_code, verification.detail)


def test_positive_p4_empty_leaf_is_accepted() -> None:
    page = _page(total=0, capacity=200, actual=0, occurrences=())
    assert all(item.passed for item in evaluate_leaf((page,), page_size=200, pagination_kind="offset"))


def test_positive_p4_schema_valid_empty_bundle_is_accepted(tmp_path: Path) -> None:
    from orchestrator.axis1_search.catalog import build_request, load_catalog

    relative_catalog = Path(
        "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json"
    )
    real = load_catalog(str(ROOT / relative_catalog))
    original = next(
        query
        for query in real.logical_queries
        if query.kind == "leaf" and query.index == "arxiv" and query.branch == "Q1"
    )
    query = SimpleNamespace(**{**original.__dict__, "independent_pass_required": False})
    catalog = replace(real, logical_queries=(query,))
    request = build_request(catalog, query.query_id, 0, None)
    import xml.sax.saxutils

    body = (
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
        f"<title>{xml.sax.saxutils.escape(request.expected_interpreted_query)}</title>"
        "<opensearch:totalResults>0</opensearch:totalResults>"
        "<opensearch:startIndex>0</opensearch:startIndex>"
        "<opensearch:itemsPerPage>200</opensearch:itemsPerPage>"
        "</feed>"
    ).encode()
    transport = _FakeTransport(
        [
            Response(
                200,
                (("Content-Type", "application/atom+xml"),),
                body,
                request.encoded_url,
                0.1,
            )
        ]
    )
    bundle = tmp_path / "bundle"
    result = _run_leaf_for_test(
        catalog,
        query.query_id,
        run_id="run-p4",
        registration_commit="0" * 40,
        catalog_path=relative_catalog.as_posix(),
        bundle_root=bundle,
        transport=transport,
        preflight=True,
        clock=lambda: 0.0,
        sleeper=lambda seconds: None,
    )
    assert result.state == "branch_complete"
    verification = verify_bundle(
        bundle,
        catalog=catalog,
        catalog_path=ROOT / relative_catalog,
    )
    assert verification.passed, (verification.reason_code, verification.detail)
    assert verification.status is not None
    assert verification.status["retrieval_complete"] is True
    assert verification.status["axis_complete"] is False
    raw_path = next(bundle.glob("raw/*.gz"))
    raw_path.write_bytes(__import__("gzip").compress(b"changed", mtime=0))
    finalize_bundle(
        bundle,
        registration_epoch=catalog.registration_epoch,
        registration_commit="0" * 40,
        catalog_sha256=hashlib.sha256((ROOT / relative_catalog).read_bytes()).hexdigest(),
    )
    rejected = verify_bundle(
        bundle,
        catalog=catalog,
        catalog_path=ROOT / relative_catalog,
    )
    assert not rejected.passed
    assert rejected.reason_code == "raw_body_digest_mismatch"


@pytest.mark.parametrize(
    "content_type",
    ("application/atom+xml", "application/xml", "text/xml"),
)
def test_arxiv_accepts_every_catalog_registered_content_type(
    tmp_path: Path, content_type: str
) -> None:
    import xml.sax.saxutils

    from orchestrator.axis1_search.catalog import build_request, load_catalog

    relative_catalog = Path(
        "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json"
    )
    real = load_catalog(str(ROOT / relative_catalog))
    original = next(
        query
        for query in real.logical_queries
        if query.kind == "leaf" and query.index == "arxiv" and query.branch == "Q1"
    )
    query = SimpleNamespace(**{**original.__dict__, "independent_pass_required": False})
    catalog = replace(real, logical_queries=(query,))
    request = build_request(catalog, query.query_id, 0, None)
    body = (
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
        f"<title>{xml.sax.saxutils.escape(request.expected_interpreted_query)}</title>"
        "<opensearch:totalResults>0</opensearch:totalResults>"
        "<opensearch:startIndex>0</opensearch:startIndex>"
        "<opensearch:itemsPerPage>200</opensearch:itemsPerPage>"
        "</feed>"
    ).encode()
    bundle = tmp_path / "bundle"
    result = _run_leaf_for_test(
        catalog,
        query.query_id,
        run_id="run-arxiv-content-type",
        registration_commit="0" * 40,
        catalog_path=relative_catalog.as_posix(),
        bundle_root=bundle,
        transport=_FakeTransport(
            [
                Response(
                    200,
                    (("Content-Type", content_type),),
                    body,
                    request.encoded_url,
                    0.1,
                )
            ]
        ),
        preflight=True,
        clock=lambda: 0.0,
        sleeper=lambda seconds: None,
    )
    assert result.state == "branch_complete"
    verification = verify_bundle(
        bundle,
        catalog=catalog,
        catalog_path=ROOT / relative_catalog,
    )
    assert verification.passed, (verification.reason_code, verification.detail)


def _write_json_document(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _refinalize_test_bundle(bundle: Path, catalog: Any, catalog_path: Path) -> None:
    finalize_bundle(
        bundle,
        registration_epoch=catalog.registration_epoch,
        registration_commit="0" * 40,
        catalog_sha256=hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
    )


def _build_two_page_dblp_bundle(
    tmp_path: Path,
) -> tuple[Path, Any, Path, list[tuple[Path, dict[str, Any]]]]:
    from orchestrator.axis1_search.catalog import build_request, load_catalog

    relative_catalog = Path(
        "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json"
    )
    catalog_path = ROOT / relative_catalog
    real = load_catalog(str(catalog_path))
    original = next(
        query for query in real.logical_queries if query.kind == "leaf" and query.index == "dblp"
    )
    query = SimpleNamespace(**{**original.__dict__, "independent_pass_required": False})
    catalog = replace(real, logical_queries=(query,))
    requests = [build_request(catalog, query.query_id, page, None) for page in (0, 1)]
    fixture = json.loads(
        (ROOT / "orchestrator/tests/fixtures/axis1_search/f6_dblp_terminal.json").read_text(
            encoding="utf-8"
        )
    )
    template_hit = fixture["result"]["hits"]["hit"][0]

    def hit(number: int) -> dict[str, Any]:
        value = json.loads(json.dumps(template_hit))
        value["info"]["key"] = f"journals/example/W{number}"
        return value

    bodies = []
    for request, first, count in (
        (requests[0], 0, 100),
        (requests[1], 100, 1),
    ):
        bodies.append(
            json.dumps(
                {
                    "result": {
                        "query": request.expected_interpreted_query,
                        "hits": {
                            "@total": "101",
                            "@sent": str(count),
                            "@first": str(first),
                            "hit": [
                                hit(number)
                                for number in range(first + 1, first + count + 1)
                            ],
                        },
                    }
                }
            ).encode()
        )
    bundle = tmp_path / "bundle"
    result = _run_leaf_for_test(
        catalog,
        query.query_id,
        run_id="run-chain",
        registration_commit="0" * 40,
        catalog_path=relative_catalog.as_posix(),
        bundle_root=bundle,
        transport=_FakeTransport(
            [
                Response(
                    200,
                    (("Content-Type", "application/json"),),
                    body,
                    request.encoded_url,
                    0.1,
                )
                for request, body in zip(requests, bodies)
            ]
        ),
        preflight=True,
        clock=lambda: 0.0,
        sleeper=lambda seconds: None,
    )
    assert result.state == "branch_complete"
    page_documents = [
        (path, json.loads(path.read_text(encoding="utf-8")))
        for path in bundle.glob("pages/*.json")
    ]
    page_documents.sort(key=lambda item: item[1]["identity"]["page_number"])
    return bundle, catalog, catalog_path, page_documents


def test_bundle_rejects_broken_parent_response_digest_chain(tmp_path: Path) -> None:
    bundle, catalog, catalog_path, pages = _build_two_page_dblp_bundle(tmp_path)
    second_path, second = pages[1]
    second["request"]["parent_response_sha256"] = "0" * 64
    _write_json_document(second_path, second)
    _refinalize_test_bundle(bundle, catalog, catalog_path)
    result = verify_bundle(bundle, catalog=catalog, catalog_path=catalog_path)
    assert not result.passed
    assert result.reason_code == "page_chain_parent_digest_mismatch"


def test_bundle_rejects_broken_page_position_chain(tmp_path: Path) -> None:
    import gzip

    bundle, catalog, catalog_path, pages = _build_two_page_dblp_bundle(tmp_path)
    first_path, first = pages[0]
    raw_path = bundle / first["response"]["body_path"]
    body_value = json.loads(gzip.decompress(raw_path.read_bytes()))
    body_value["result"]["hits"]["@total"] = "100"
    changed_body = json.dumps(body_value).encode()
    raw_path.write_bytes(gzip.compress(changed_body, mtime=0))
    changed_digest = hashlib.sha256(changed_body).hexdigest()
    first["response"]["sha256"] = changed_digest
    first["response"]["byte_count"] = len(changed_body)
    first["parse"]["declared_total"] = 100
    first["parse"]["position_out"] = None
    _write_json_document(first_path, first)
    second_path, second = pages[1]
    second["request"]["parent_response_sha256"] = changed_digest
    _write_json_document(second_path, second)
    _refinalize_test_bundle(bundle, catalog, catalog_path)
    result = verify_bundle(bundle, catalog=catalog, catalog_path=catalog_path)
    assert not result.passed
    assert result.reason_code == "page_chain_position_mismatch"


def test_bundle_rejects_extra_row_in_final_ledger(tmp_path: Path) -> None:
    bundle, catalog, catalog_path, pages = _build_two_page_dblp_bundle(tmp_path)
    ledger_path = bundle / pages[-1][1]["records"]["occurrence_ledger_path"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    extra = dict(ledger["occurrences"][-1])
    extra.update(
        {
            "index_work_id": "journals/example/EXTRA",
            "page_number": 99,
            "ordinal": 0,
        }
    )
    ledger["occurrences"].append(extra)
    ledger["occurrence_count"] += 1
    ledger["distinct_index_work_id_count"] += 1
    _write_json_document(ledger_path, ledger)
    _refinalize_test_bundle(bundle, catalog, catalog_path)
    result = verify_bundle(bundle, catalog=catalog, catalog_path=catalog_path)
    assert not result.passed
    assert result.reason_code == "occurrence_ledger_extra_row"


def test_bundle_rejects_missing_row_from_final_ledger(tmp_path: Path) -> None:
    bundle, catalog, catalog_path, pages = _build_two_page_dblp_bundle(tmp_path)
    ledger_path = bundle / pages[-1][1]["records"]["occurrence_ledger_path"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    del ledger["occurrences"][0]
    ledger["occurrence_count"] -= 1
    ledger["distinct_index_work_id_count"] -= 1
    _write_json_document(ledger_path, ledger)
    _refinalize_test_bundle(bundle, catalog, catalog_path)
    result = verify_bundle(bundle, catalog=catalog, catalog_path=catalog_path)
    assert not result.passed
    assert result.reason_code == "occurrence_ledger_missing_row"


def test_bundle_rejects_duplicate_page_evidence(tmp_path: Path) -> None:
    bundle, catalog, catalog_path, pages = _build_two_page_dblp_bundle(tmp_path)
    duplicate = bundle / "pages" / "duplicate.json"
    duplicate.write_bytes(pages[0][0].read_bytes())
    _refinalize_test_bundle(bundle, catalog, catalog_path)
    result = verify_bundle(bundle, catalog=catalog, catalog_path=catalog_path)
    assert not result.passed
    assert result.reason_code == "duplicate_page_evidence"


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


def test_production_path_passes_real_catalog_shard_bounds(tmp_path: Path) -> None:
    import xml.sax.saxutils

    from orchestrator.axis1_search.catalog import build_request, load_catalog

    relative_catalog = Path(
        "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json"
    )
    real = load_catalog(str(ROOT / relative_catalog))
    original = next(
        query
        for query in real.logical_queries
        if query.kind == "leaf"
        and query.index == "arxiv"
        and query.branch == "Q6"
        and query.shard_lower == "1991-01-01"
    )
    query = SimpleNamespace(**{**original.__dict__, "independent_pass_required": True})
    catalog = replace(real, logical_queries=(query,))
    request = build_request(catalog, query.query_id, 0, None)
    body = (
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
        f"<title>{xml.sax.saxutils.escape(request.expected_interpreted_query)}</title>"
        "<opensearch:totalResults>1</opensearch:totalResults>"
        "<opensearch:startIndex>0</opensearch:startIndex>"
        "<opensearch:itemsPerPage>200</opensearch:itemsPerPage>"
        "<entry><id>http://arxiv.org/abs/2601.99999</id>"
        "<published>2026-01-01T00:00:00Z</published></entry>"
        "</feed>"
    ).encode()
    result = _run_leaf_for_test(
        catalog,
        query.query_id,
        run_id="run-shard-negative",
        registration_commit="0" * 40,
        catalog_path=relative_catalog.as_posix(),
        bundle_root=tmp_path / "bundle",
        transport=_FakeTransport(
            [
                Response(
                    200,
                    (("Content-Type", "application/atom+xml"),),
                    body,
                    request.encoded_url,
                    0.1,
                )
            ]
        ),
        preflight=True,
        clock=lambda: 0.0,
        sleeper=lambda seconds: None,
    )
    assert result.state == "blocked_on_ruling"
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


def test_checkpoint_rejects_not_applicable_for_unfinished_pass() -> None:
    checkpoint = _checkpoint()
    checkpoint["state"] = "pass_complete"
    checkpoint["resume_action"] = "not_applicable"
    with pytest.raises(CheckpointError, match="illegal state/resume_action"):
        validate_checkpoint(checkpoint)


def test_independent_pass_requirement_comes_only_from_logical_query() -> None:
    ordinary = Catalog("AX1-20260829-E1", {}, independent_pass_required=False)
    sharded = Catalog("AX1-20260829-E1", {}, independent_pass_required=True)
    assert _independent_pass_required(ordinary, "leaf") is False
    assert _independent_pass_required(sharded, "leaf") is True


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
