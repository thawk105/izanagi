from __future__ import annotations

from dataclasses import replace
import hashlib
import inspect
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import jsonschema
import pytest

from orchestrator.axis_b5_search import catalog as catalog_module
from orchestrator.axis_b5_search import preflight as preflight_module
from orchestrator.axis_b5_search.parsers import JsonObject, Occurrence, ParsedPage
from orchestrator.axis_b5_search.preflight import (
    CATALOG_PATH,
    LookupResponse,
    LookupResult,
    _evaluate_live_preflight_for_test,
    build_lookup_request,
    classify_lookup_response,
    load_anchor_registry,
    run_live_preflight,
    verify_registration,
)
from orchestrator.axis_b5_search.runner import (
    RETRY_DELAYS_S,
    LeafDefinition,
    LeafResolutionError,
    PageEvidence,
    PreflightError,
    StoredResponse,
    UnregisteredRunPolicyError,
    build_expected_openalex_ast,
    build_page_evidence,
    build_request,
    evaluate_leaf,
    issue_run_request,
    normalize_interpreted_query,
    openalex_ast_matches,
    resolve_leaf,
    run_leaf,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "orchestrator/tests/fixtures/axis_b5_search"
COMMIT = "1234567890abcdef1234567890abcdef12345678"


def _catalog() -> dict[str, Any]:
    return json.loads((ROOT / CATALOG_PATH).read_text(encoding="utf-8"))


def _fixture(name: str) -> bytes:
    return (FIXTURES / "synthetic" / name).read_bytes()


def _arxiv_leaf(query: str) -> LeafDefinition:
    encoded = query.replace(" ", "%20")
    template = (
        "https://export.arxiv.org/api/query?search_query="
        f"{encoded}&start={{POS}}&max_results=200"
    )
    return LeafDefinition(
        "B5-TEST@arxiv",
        "query",
        "arxiv",
        template,
        template.replace("{POS}", "0"),
        (),
        {},
        "2026-12-31",
    )


def _stored(body: bytes, url: str, content_type: str) -> StoredResponse:
    return StoredResponse(
        200,
        (("Content-Type", content_type), ("X-Test", "one"), ("X-Test", "two")),
        body,
        url,
    )


def _condition(result: Any, number: int) -> Any:
    return next(
        item for item in result.completion.condition_results if item.condition == number
    )


def _page(
    *,
    page_number: int,
    declared_total: int,
    actual_count: int,
    position: int,
    work_ids: Sequence[str],
) -> PageEvidence:
    occurrences = tuple(
        Occurrence(work_id, page_number, ordinal, None, None, False)
        for ordinal, work_id in enumerate(work_ids)
    )
    parsed = ParsedPage(
        "arxiv",
        page_number,
        declared_total,
        200,
        actual_count,
        position,
        None,
        "q",
        None,
        occurrences,
        (),
    )
    url = (
        "https://export.arxiv.org/api/query?search_query=q&start="
        f"{page_number * 200}&max_results=200"
    )
    return PageEvidence(
        "B5-TEST@arxiv",
        "query",
        "arxiv",
        page_number,
        url,
        page_number * 200,
        200,
        (("Content-Type", "application/atom+xml"),),
        "application/atom+xml",
        "application/atom+xml",
        url,
        2,
        hashlib.sha256(b"{}").hexdigest(),
        parsed,
    )


class _FakeGit:
    def __init__(self, files: Mapping[str, bytes]) -> None:
        self.files = dict(files)
        self.entries = {
            path: ("100644", hashlib.sha1(raw).hexdigest())
            for path, raw in self.files.items()
        }

    def head(self) -> str:
        return COMMIT

    def status(self, paths: Sequence[str]) -> bytes:
        assert "orchestrator/tests/test_axis_b5_search_executor.py" not in paths
        return b""

    def blob(self, commit: str, path: str) -> bytes:
        assert commit == COMMIT
        return self.files[path]

    def tree(
        self, commit: str, paths: Sequence[str]
    ) -> Mapping[str, tuple[str, str]]:
        assert commit == COMMIT
        return {
            path: value
            for path, value in self.entries.items()
            if any(
                path == prefix or path.startswith(prefix.rstrip("/") + "/")
                for prefix in paths
            )
        }


def _worktree_git() -> _FakeGit:
    fixed = (
        "docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md",
        "docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md",
        "docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md",
        CATALOG_PATH,
    )
    paths = {ROOT / relative for relative in fixed}
    for relative_root in (
        "orchestrator/axis_b5_search",
        "orchestrator/tests/fixtures/axis_b5_search",
    ):
        paths.update(
            path
            for path in (ROOT / relative_root).rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        )
    paths.update(
        path
        for path in (ROOT / "orchestrator/schemas").glob(
            "axis_b5_search_*.schema.json"
        )
        if path.is_file()
    )
    return _FakeGit(
        {
            path.relative_to(ROOT).as_posix(): path.read_bytes()
            for path in paths
        }
    )


def _registration_repo(tmp_path: Path) -> tuple[Path, _FakeGit]:
    documents = (
        "docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md",
        "docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md",
        "docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md",
    )
    files: dict[str, bytes] = {path: f"registered:{path}\n".encode() for path in documents}
    files[CATALOG_PATH] = catalog_module.render_catalog_json()
    for name in (
        "axis_b5_search_page_evidence.schema.json",
        "axis_b5_search_live_preflight.schema.json",
        "axis_b5_search_registration_seal.schema.json",
    ):
        relative = f"orchestrator/schemas/{name}"
        files[relative] = (ROOT / relative).read_bytes()
    files["orchestrator/axis_b5_search/registered.py"] = b"REGISTERED = True\n"
    files["orchestrator/tests/fixtures/axis_b5_search/sample.body"] = b"sample\n"
    for relative, raw in files.items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    return tmp_path, _FakeGit(files)


def _minimal_seal() -> dict[str, Any]:
    return {
        "schema_version": "izanagi-axis-b5-registration-seal/v1",
        "document_type": "registration_seal",
        "registration_commit": COMMIT,
        "catalog_sha256": "7eb8385e35bd24edac8a227a72ba5bc6b568ca8bc7cac2c8250af8b4ea4c346f",
        "seal_scope": {
            "kind": "leaf-executor-provisional",
            "provisional": True,
            "includes": [
                "registration-preflight",
                "anchor-lookup-preflight",
                "leaf-response-evaluator",
            ],
            "excludes": [
                "checkpoint",
                "resume",
                "axis-aggregate",
                "control-firing",
                "supplemental-anchor-stream-execution",
            ],
            "renewal_trigger": "runner-bytes-change-for-checkpoint-or-resume",
        },
        "files": [
            {
                "path": "orchestrator/axis_b5_search/runner.py",
                "git_blob": "1111111111111111111111111111111111111111",
                "mode": "100644",
                "bytes": 1,
                "sha256": "2d711642b726b04401627ca9fbac32f5da7e5c8530fb1903cc4db02258717921",
            }
        ],
    }


MEMBERS = (
    ("G1-01", "openalex"),
    ("G2-01", "openalex"),
    ("G2-02", "openalex"),
    ("G2-03", "openalex"),
    ("G2-04", "openalex"),
    ("G2-05", "openalex"),
    ("G2-06", "openalex"),
    ("G2-07", "openalex"),
    ("G2-08", "openalex"),
    ("G3-01", "openalex"),
    ("G3-02", "openalex"),
    ("G3-03", "openalex"),
    ("G3-04", "openalex"),
    ("G3-05", "openalex"),
    ("G3-06", "openalex"),
    ("G3-07", "openalex"),
    ("G2-08", "arxiv"),
    ("G1-01", "dblp"),
    ("G2-04", "dblp"),
    ("G2-05", "dblp"),
    ("G2-06", "dblp"),
    ("G2-07", "dblp"),
    ("G2-08", "dblp"),
    ("G3-01", "dblp"),
    ("G3-02", "dblp"),
    ("G3-03", "dblp"),
    ("G3-04", "dblp"),
    ("G3-05", "dblp"),
    ("G3-06", "dblp"),
    ("G3-07", "dblp"),
)


def _lookup_result(anchor_id: str, index: str, classification: str) -> LookupResult:
    host = {
        "openalex": "api.openalex.org",
        "arxiv": "export.arxiv.org",
        "dblp": "dblp.org",
    }[index]
    return LookupResult(
        anchor_id,
        index,
        f"https://{host}/registered",
        classification,
        200 if classification != "不達" else None,
        (("Content-Type", "application/json"),),
        "application/json",
        2,
        hashlib.sha256(b"{}").hexdigest(),
        f"https://{host}/registered" if classification != "不達" else None,
        None if classification != "不達" else "timeout",
        "W1000000000" if index == "openalex" else None,
        "W9999999999" if index == "openalex" else "record-key",
        {
            "arxiv_entry_count": None,
            "arxiv_total_results": None,
            "dblp_total": None,
            "dblp_matching_doi_count": None,
            "json_root_type": None,
            "parse_error": None,
        },
    )


def _run_successful_live_preflight(
    tmp_path: Path,
) -> tuple[dict[str, Any], Path, list[tuple[str, str, str]]]:
    anchors = {anchor.anchor_id: anchor for anchor in load_anchor_registry()}
    issued: list[tuple[str, str, str]] = []

    class Transport:
        def get(self, spec: Any) -> LookupResponse:
            issued.append((spec.anchor_id, spec.index, spec.url))
            anchor = anchors[spec.anchor_id]
            if spec.index == "openalex":
                content_type = "application/json; charset=utf-8"
                body = json.dumps(
                    {"id": f"https://openalex.org/{anchor.openalex_work_id}"}
                ).encode("utf-8")
            elif spec.index == "arxiv":
                content_type = "application/atom+xml; charset=utf-8"
                body = (
                    '<feed xmlns="http://www.w3.org/2005/Atom" '
                    'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
                    '<opensearch:totalResults>1</opensearch:totalResults>'
                    f"<entry><id>http://arxiv.org/abs/{anchor.arxiv_id}v1</id></entry>"
                    "</feed>"
                ).encode("utf-8")
            else:
                content_type = "application/json"
                body = json.dumps(
                    {
                        "result": {
                            "hits": {
                                "@total": "1",
                                "hit": [
                                    {
                                        "info": {
                                            "key": f"test/{anchor.anchor_id}",
                                            "doi": anchor.doi,
                                        }
                                    }
                                ],
                            }
                        }
                    }
                ).encode("utf-8")
            return LookupResponse(
                200,
                (("Content-Type", content_type),),
                body,
                spec.url,
            )

    created: list[Mapping[str, Any]] = []

    def factory(**kwargs: Any) -> Transport:
        created.append(kwargs)
        return Transport()

    output = tmp_path / "live-preflight.json"
    record = run_live_preflight(
        COMMIT,
        repo_root=ROOT,
        output_path=output,
        timeout_s=11,
        user_agent="axis-b5-test/contact@example.invalid",
        request_interval_s=0.25,
        git_backend=_worktree_git(),
        _transport_factory=factory,
        _sleeper=lambda _delay: None,
    )
    assert created == [
        {
            "timeout_s": 11,
            "user_agent": "axis-b5-test/contact@example.invalid",
        }
    ]
    return record, output, issued


def test_worktree_scan_excludes_pycache_and_pyc(tmp_path: Path) -> None:
    relative_root = "orchestrator/axis_b5_search"
    source_directory = tmp_path / relative_root
    source_directory.mkdir(parents=True)
    (source_directory / "registered.py").write_bytes(b"REGISTERED = True\n")
    (source_directory / "standalone.pyc").write_bytes(b"ignored bytecode")
    cache_directory = source_directory / "__pycache__"
    cache_directory.mkdir()
    (cache_directory / "registered.cpython-312.pyc").write_bytes(
        b"ignored cached bytecode"
    )

    assert preflight_module._walk_files(tmp_path, relative_root) == {
        "orchestrator/axis_b5_search/registered.py"
    }


def test_registration_accepts_exact_commit_tree_and_returns_schema_valid_seal() -> None:
    head = preflight_module.SubprocessGit(ROOT).head()
    result = verify_registration(head, repo_root=ROOT)
    assert result.passed is True
    assert result.reason_code is None
    assert result.seal_record is not None
    assert result.seal_record["seal_scope"]["kind"] == "leaf-executor-provisional"
    assert "checkpoint" in result.seal_record["seal_scope"]["excludes"]
    assert "seal_sha256" not in result.seal_record
    sealed_paths = {item["path"] for item in result.seal_record["files"]}
    assert {
        "orchestrator/axis_b5_search/catalog.py",
        "orchestrator/axis_b5_search/parsers.py",
        "orchestrator/axis_b5_search/preflight.py",
        "orchestrator/axis_b5_search/runner.py",
    }.issubset(sealed_paths)


def test_registration_rejects_invalid_or_non_head_commit(tmp_path: Path) -> None:
    repo, backend = _registration_repo(tmp_path)
    invalid = verify_registration("ABC", repo_root=repo, git_backend=backend)
    assert invalid.reason_code == "registration_commit_invalid"
    mismatch = verify_registration("0" * 40, repo_root=repo, git_backend=backend)
    assert mismatch.reason_code == "head_mismatch"


def test_registration_rejects_path_module_mode_and_byte_mismatches(
    tmp_path: Path,
) -> None:
    repo, backend = _registration_repo(tmp_path / "extra")
    extra = repo / "orchestrator/axis_b5_search/unregistered_extra.py"
    extra.write_text("EXTRA = True\n", encoding="utf-8")
    path_mismatch = verify_registration(COMMIT, repo_root=repo, git_backend=backend)
    assert path_mismatch.passed is False
    assert path_mismatch.reason_code == "registered_path_set_mismatch"
    assert "unregistered_extra.py" in path_mismatch.detail

    fake_repo, fake_backend = _registration_repo(tmp_path / "module")
    module_mismatch = verify_registration(
        COMMIT, repo_root=fake_repo, git_backend=fake_backend
    )
    assert module_mismatch.passed is False
    assert module_mismatch.reason_code == "module_path_mismatch"

    repo, backend = _registration_repo(tmp_path / "dirty")
    backend.status = lambda paths: b" M orchestrator/axis_b5_search/registered.py\n"  # type: ignore[method-assign]
    dirty = verify_registration(COMMIT, repo_root=repo, git_backend=backend)
    assert dirty.reason_code == "registration_paths_dirty"

    repo, backend = _registration_repo(tmp_path / "mode")
    backend.entries["orchestrator/axis_b5_search/registered.py"] = (
        "100755",
        backend.entries["orchestrator/axis_b5_search/registered.py"][1],
    )
    mode = verify_registration(COMMIT, repo_root=repo, git_backend=backend)
    assert mode.reason_code == "registered_mode_mismatch"

    repo, backend = _registration_repo(tmp_path / "bytes")
    (repo / "orchestrator/axis_b5_search/registered.py").write_bytes(b"changed\n")
    changed = verify_registration(COMMIT, repo_root=repo, git_backend=backend)
    assert changed.reason_code == "registered_bytes_mismatch"


def test_failed_registration_returns_before_live_transport_creation(tmp_path: Path) -> None:
    created = 0

    def factory(**kwargs: Any) -> object:
        nonlocal created
        created += 1
        return object()

    with pytest.raises(ValueError, match="registration preflight failed"):
        run_live_preflight(
            "not-a-commit",
            repo_root=tmp_path,
            output_path=tmp_path / "live.json",
            timeout_s=5,
            user_agent="network-zero-test",
            request_interval_s=1,
            _transport_factory=factory,
        )
    assert created == 0
    assert not (tmp_path / "live.json").exists()


def test_registry_has_frozen_members_and_g208_doi_primary_key() -> None:
    anchors = load_anchor_registry()
    g208 = next(item for item in anchors if item.anchor_id == "G2-08")
    observed = {
        item.anchor_id: (
            item.slot,
            item.doi,
            item.arxiv_id,
            item.openalex_work_id,
            item.first_author_id,
            item.last_author_id,
            item.member_indexes,
        )
        for item in anchors
    }
    assert observed == {
        "G1-01": ("G1-CICADA", "10.1145/3035918.3064015", None, "W2613970404", "A5050218314", "A5085479490", ("openalex", "dblp")),
        "G2-01": ("G2-SA", "10.1214/aoms/1177729586", None, "W1994616650", "A5110883277", "A5065560698", ("openalex",)),
        "G2-02": ("G2-SA", "10.1214/aoms/1177729392", None, "W2009797711", "A5110860590", "A5049527866", ("openalex",)),
        "G2-03": ("G2-SA", "10.1214/aoms/1177706705", None, "W1996235804", "A5082829165", "A5082829165", ("openalex",)),
        "G2-04": ("G2-SA", "10.1109/9.119632", None, "W2124289529", "A5066890566", "A5066890566", ("openalex", "dblp")),
        "G2-05": ("G2-SA", "10.1109/7.705889", None, "W2128452997", "A5066890566", "A5066890566", ("openalex", "dblp")),
        "G2-06": ("G2-SA", "10.1137/0803045", None, "W2065450730", "A5059841305", "A5039659947", ("openalex", "dblp")),
        "G2-07": ("G2-SA", "10.1007/s10107-012-0572-5", None, "W2061570747", "A5110661221", "A5032317649", ("openalex", "dblp")),
        "G2-08": ("G2-SA", "10.1137/17M1154679", "1710.11258", "W2766854590", "A5083156016", "A5081856145", ("openalex", "arxiv", "dblp")),
        "G3-01": ("G3-STM", "10.1145/872035.872048", None, "W2105055683", "A5086347882", "A5066189979", ("openalex", "dblp")),
        "G3-02": ("G3-STM", "10.1145/1073814.1073861", None, "W1988800505", "A5066189979", "A5079254515", ("openalex", "dblp")),
        "G3-03": ("G3-STM", "10.1007/11561927_23", None, "W1759214032", "A5049321288", "A5015726068", ("openalex", "dblp")),
        "G3-04": ("G3-STM", "10.1145/1073814.1073863", None, "W2106871513", "A5049321288", "A5015726068", ("openalex", "dblp")),
        "G3-05": ("G3-STM", "10.1145/1378533.1378564", None, "W2165791323", "A5023107016", "A5072539515", ("openalex", "dblp")),
        "G3-06": ("G3-STM", "10.1145/1504176.1504199", None, "W2122621236", "A5017374713", "A5079254515", ("openalex", "dblp")),
        "G3-07": ("G3-STM", "10.1145/1582716.1582725", None, "W2036987653", "A5070096854", "A5001418143", ("openalex", "dblp")),
    }
    assert len(anchors) == 16
    assert sum(len(item.member_indexes) for item in anchors) == 30
    assert g208.doi == "10.1137/17M1154679"
    assert g208.arxiv_id == "1710.11258"


def test_lookup_builder_emits_only_registered_three_forms() -> None:
    anchors = {item.anchor_id: item for item in load_anchor_registry()}
    assert build_lookup_request(anchors["G1-01"], "openalex").url == (
        "https://api.openalex.org/works/https://doi.org/10.1145/3035918.3064015"
        "?select=id,doi,title,publication_year,ids,authorships,referenced_works_count"
    )
    assert build_lookup_request(anchors["G2-08"], "arxiv").url == (
        "https://export.arxiv.org/api/query?id_list=1710.11258&max_results=1"
    )
    assert build_lookup_request(anchors["G1-01"], "dblp").url == (
        "https://dblp.org/search/publ/api?q=10.1145%2F3035918.3064015&format=json&h=5"
    )
    with pytest.raises(ValueError, match="not a registered member"):
        build_lookup_request(anchors["G1-01"], "arxiv")


def test_openalex_404_is_nonrecorded_before_content_type_check() -> None:
    anchor = load_anchor_registry()[0]
    result = classify_lookup_response(
        anchor,
        "openalex",
        LookupResponse(
            404,
            (("Content-Type", "text/html; charset=utf-8"),),
            b"<html>not found</html>",
            build_lookup_request(anchor, "openalex").url,
        ),
    )
    assert result.classification == "非収録"
    assert result.content_type == "text/html"


def test_openalex_200_json_id_is_recorded() -> None:
    anchor = load_anchor_registry()[0]
    request_url = build_lookup_request(anchor, "openalex").url
    result = classify_lookup_response(
        anchor,
        "openalex",
        LookupResponse(
            200,
            (("Content-Type", "application/json; charset=utf-8"),),
            b'{"id":"https://openalex.org/W2613970404"}',
            request_url,
        ),
    )
    assert result.classification == "収録"
    assert result.observed_index_work_id == "W2613970404"


def test_arxiv_media_type_parameters_are_ignored_and_malformed_is_unreachable() -> None:
    anchor = next(item for item in load_anchor_registry() if item.anchor_id == "G2-08")
    body = (
        b'<feed xmlns="http://www.w3.org/2005/Atom" '
        b'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
        b'<opensearch:totalResults>1</opensearch:totalResults>'
        b'<entry><id>http://arxiv.org/abs/1710.11258v1</id></entry></feed>'
    )
    recorded = classify_lookup_response(
        anchor,
        "arxiv",
        LookupResponse(
            200,
            (("Content-Type", "application/atom+xml; charset=utf-8"),),
            body,
            build_lookup_request(anchor, "arxiv").url,
        ),
    )
    malformed = classify_lookup_response(
        anchor,
        "arxiv",
        LookupResponse(
            200,
            (("Content-Type", "application/atom+xml"),),
            b"not xml",
            build_lookup_request(anchor, "arxiv").url,
        ),
    )
    assert recorded.classification == "収録"
    assert malformed.classification == "不達"


def test_dblp_matching_doi_is_recorded_but_unknown_json_shape_is_unclassified() -> None:
    anchor = load_anchor_registry()[0]
    request_url = build_lookup_request(anchor, "dblp").url
    hit = json.dumps(
        {
            "result": {
                "hits": {
                    "@total": "1",
                    "hit": [
                        {
                            "info": {
                                "key": "conf/sigmod/LimKA17",
                                "doi": "10.1145/3035918.3064015",
                            }
                        }
                    ],
                }
            }
        }
    ).encode()
    unknown = b'{"result":{"hits":{"@total":"1","hit":[]}}}'
    recorded = classify_lookup_response(
        anchor,
        "dblp",
        LookupResponse(200, (("Content-Type", "application/json"),), hit, request_url),
    )
    unclassified = classify_lookup_response(
        anchor,
        "dblp",
        LookupResponse(
            200,
            (("Content-Type", "application/json; charset=UTF-8"),),
            unknown,
            request_url,
        ),
    )
    assert recorded.classification == "収録"
    assert recorded.observed_index_work_id == "conf/sigmod/LimKA17"
    assert unclassified.classification == "unclassified"
    assert unclassified.observed_shape["dblp_total"] == 1


def test_dblp_zero_total_is_nonrecorded() -> None:
    anchor = load_anchor_registry()[0]
    request_url = build_lookup_request(anchor, "dblp").url
    result = classify_lookup_response(
        anchor,
        "dblp",
        LookupResponse(
            200,
            (("Content-Type", "application/json"),),
            b'{"result":{"hits":{"@total":"0","hit":[]}}}',
            request_url,
        ),
    )
    assert result.classification == "非収録"


def test_live_preflight_29_recorded_plus_one_unreachable_cannot_start() -> None:
    for final_classification in ("不達", "非収録"):
        results = [
            _lookup_result(anchor_id, index, "収録")
            for anchor_id, index in MEMBERS[:-1]
        ] + [_lookup_result("G3-07", "dblp", final_classification)]
        record = _evaluate_live_preflight_for_test(
            results,
            registration_seal=_minimal_seal(),
            timeout_s=17,
            user_agent="axis-b5-test/contact@example.invalid",
            request_interval_s=2.5,
        )
        assert record["exact_member_set"] is True
        assert record["passed"] is False
        assert record["axis_status"] == "未完走"
        assert record["may_start_run"] is False
        assert record["transport_policy"]["timeout_s"] == 17
        assert record["transport_policy"]["request_interval_s"] == 2.5


def test_live_preflight_accepts_exact_30_and_wid_drift_is_evidence_only(
    tmp_path: Path,
) -> None:
    results = [_lookup_result(anchor_id, index, "収録") for anchor_id, index in MEMBERS]
    record = _evaluate_live_preflight_for_test(
        results,
        registration_seal=_minimal_seal(),
        timeout_s=9,
        user_agent="literal-user-agent",
        request_interval_s=1,
    )
    assert record["passed"] is True
    assert record["may_start_run"] is True
    first_openalex = next(item for item in record["lookups"] if item["index"] == "openalex")
    assert first_openalex["registered_openalex_work_id"] == "W1000000000"
    assert first_openalex["observed_index_work_id"] == "W9999999999"

    live_record, output, issued = _run_successful_live_preflight(tmp_path)
    assert len(issued) == 30
    assert {(anchor_id, index) for anchor_id, index, _url in issued} == set(MEMBERS)
    assert {url.split("/", 3)[2] for _anchor_id, _index, url in issued} == {
        "api.openalex.org",
        "export.arxiv.org",
        "dblp.org",
    }
    assert live_record["passed"] is True
    assert live_record["may_start_run"] is True
    assert json.loads(output.read_text(encoding="utf-8")) == live_record


def test_live_preflight_has_no_defaults_for_caller_policy_values() -> None:
    signature = inspect.signature(run_live_preflight)
    assert signature.parameters["timeout_s"].default is inspect.Parameter.empty
    assert signature.parameters["user_agent"].default is inspect.Parameter.empty
    assert signature.parameters["request_interval_s"].default is inspect.Parameter.empty
    assert "evaluate_live_preflight" not in preflight_module.__all__
    assert not hasattr(preflight_module, "evaluate_live_preflight")


def test_resolve_leaf_accepts_one_location_and_rejects_duplicate_or_wrong_host() -> None:
    document = _catalog()
    leaf = resolve_leaf(document, "B5-Q10@dblp/T01-O01")
    assert leaf.kind == "query"
    assert leaf.index == "dblp"
    duplicate = json.loads(json.dumps(document))
    duplicate["controls"].append(
        {
            "control_id": "B5-Q10@dblp/T01-O01",
            "index": "dblp",
            "term_groups": [["T01"], ["O01"]],
            "request_template": leaf.request_template,
            "first_page_url": leaf.first_page_url,
            "shares_request_with": None,
        }
    )
    with pytest.raises(LeafResolutionError, match="exactly once"):
        resolve_leaf(duplicate, "B5-Q10@dblp/T01-O01")
    wrong = json.loads(json.dumps(document))
    wrong["queries"][0]["request_template"] = wrong["queries"][0][
        "request_template"
    ].replace("export.arxiv.org", "api.openalex.org")
    with pytest.raises(LeafResolutionError, match="host/path"):
        resolve_leaf(wrong, "B5-Q1@arxiv")


def test_openalex_initial_cursor_is_literal_star_and_continuation_is_encoded() -> None:
    leaf = resolve_leaf(_catalog(), "B5-Q1@openalex")
    first = build_request(leaf, 0, None)
    second = build_request(leaf, 1, "cursor-token:2/+==")
    assert first.url.endswith("&cursor=*")
    assert "%2A" not in first.url
    assert second.url.endswith("&cursor=cursor-token%3A2%2F%2B%3D%3D")
    with pytest.raises(ValueError, match="page 0 cursor"):
        build_request(leaf, 0, "%2A")

    terminal = build_page_evidence(
        leaf,
        0,
        None,
        _stored(_fixture("openalex_cursor_page_2.json"), first.url, "application/json"),
    )
    terminal_result = evaluate_leaf(
        leaf, [terminal], expected_content_types=("application/json",)
    )
    assert terminal.parsed.next_cursor is None
    assert _condition(terminal_result, 3).passed is True
    nonterminal = replace(
        terminal,
        parsed=replace(terminal.parsed, next_cursor="unexpected-continuation"),
    )
    nonterminal_result = evaluate_leaf(
        leaf, [nonterminal], expected_content_types=("application/json",)
    )
    assert _condition(nonterminal_result, 3).reason_code == "cursor_not_terminal"


def test_offset_request_uses_fixed_step_and_rejects_actual_count_style_position() -> None:
    leaf = resolve_leaf(_catalog(), "B5-Q10@dblp/T01-O01")
    second = build_request(leaf, 1, 100)
    assert second.url.endswith("&f=100")
    with pytest.raises(ValueError, match="fixed step"):
        build_request(leaf, 1, 1)


def test_text_echo_normalization_decodes_once_and_does_not_accept_parentheses() -> None:
    assert normalize_interpreted_query("dblp", "a%2520b") == "a%20b"
    assert normalize_interpreted_query(
        "arxiv", "submittedDate:%5B1991%20TO%202026%5D"
    ) == "submittedDate:[1991 TO 2026]"
    assert normalize_interpreted_query(
        "arxiv", 'submittedDate:"1991 TO 2026"'
    ) == "submittedDate:[1991 TO 2026]"
    assert normalize_interpreted_query(
        "arxiv", "submittedDate:(1991 TO 2026)"
    ) == "submittedDate:(1991 TO 2026)"
    assert normalize_interpreted_query(
        "arxiv", 'submittedDate:[1991 TO 2026"'
    ) != "submittedDate:[1991 TO 2026]"
    assert normalize_interpreted_query(
        "arxiv", 'submittedDate:"1991 TO 2026]'
    ) != "submittedDate:[1991 TO 2026]"


def test_openalex_ast_preserves_multiplicity_but_ignores_sibling_order() -> None:
    control = resolve_leaf(_catalog(), "B5-CTL-AND2023@openalex")
    frozen_control_ast = {
        "get_rows": "200",
        "filter_rows": [
            {
                "join": "and",
                "filters": [
                    {
                        "join": "or",
                        "filters": [
                            {
                                "column_id": "title_and_abstract.search",
                                "value": "backoff",
                            }
                        ],
                    },
                    {
                        "join": "or",
                        "filters": [
                            {
                                "column_id": "title_and_abstract.search",
                                "value": "update interval",
                            }
                        ],
                    },
                    {
                        "column_id": "to_publication_date",
                        "value": "2023-12-31",
                    },
                ],
            }
        ],
    }
    assert openalex_ast_matches(
        frozen_control_ast, build_expected_openalex_ast(control)
    ) is True

    leaf = LeafDefinition(
        "B5-TEST@openalex",
        "query",
        "openalex",
        "https://api.openalex.org/works?filter=x&per-page=200&cursor={CUR}",
        "https://api.openalex.org/works?filter=x&per-page=200&cursor=*",
        (("M01", "M01"),),
        {"M01": "backoff"},
        "2026-12-31",
    )
    expected = build_expected_openalex_ast(leaf)
    single_leaf = replace(leaf, term_groups=(("M01",),))
    missing_occurrence = build_expected_openalex_ast(single_leaf)
    assert openalex_ast_matches(expected, expected) is True
    assert openalex_ast_matches(expected, missing_occurrence) is False


def test_openalex_ast_rejects_unknown_key_join_and_get_rows_type() -> None:
    valid = {
        "get_rows": "200",
        "filter_rows": [
            {
                "join": "and",
                "filters": [
                    {
                        "join": "or",
                        "filters": [
                            {
                                "column_id": "title_and_abstract.search",
                                "value": "backoff",
                            }
                        ],
                    },
                    {
                        "column_id": "to_publication_date",
                        "value": "2026-12-31",
                    },
                ],
            }
        ],
    }
    reordered = {
        "filter_rows": [
            {
                "filters": [
                    {
                        "column_id": "to_publication_date",
                        "value": "2026-12-31",
                    },
                    {
                        "filters": [
                            {
                                "value": "backoff",
                                "column_id": "title_and_abstract.search",
                            }
                        ],
                        "join": "or",
                    },
                ],
                "join": "and",
            }
        ],
        "get_rows": "200",
    }
    assert openalex_ast_matches(valid, reordered) is True
    assert openalex_ast_matches(valid, {**valid, "future": 1}) is False
    assert openalex_ast_matches(valid, {**valid, "get_rows": 200}) is False
    bad_join = json.loads(json.dumps(valid))
    bad_join["filter_rows"][0]["join"] = "xor"
    assert openalex_ast_matches(valid, bad_join) is False
    duplicate_root = JsonObject(
        (
            ("get_rows", "200"),
            ("get_rows", "200"),
            ("filter_rows", (JsonObject((("join", "and"), ("filters", ()))),)),
        )
    )
    assert openalex_ast_matches(valid, duplicate_root) is False


def test_condition3_uses_actual_count_not_capacity_echo() -> None:
    leaf = _arxiv_leaf("short page query")
    request = build_request(leaf, 0, None)
    evidence = build_page_evidence(
        leaf,
        0,
        None,
        _stored(
            _fixture("arxiv_nonfinal_short.xml"),
            request.url,
            "application/atom+xml; charset=utf-8",
        ),
    )
    final = _page(
        page_number=1,
        declared_total=400,
        actual_count=200,
        position=200,
        work_ids=tuple(f"final-{number}" for number in range(200)),
    )
    result = evaluate_leaf(
        leaf, [evidence, final], expected_content_types=("application/atom+xml",)
    )
    assert evidence.parsed.capacity_echo == 200
    assert evidence.parsed.actual_count == 1
    assert _condition(result, 3).passed is False
    assert _condition(result, 3).reason_code == "actual_count_mismatch"


def test_condition3_accepts_normal_partial_final_despite_capacity_echo() -> None:
    leaf = _arxiv_leaf("final page query")
    request = build_request(leaf, 0, None)
    evidence = build_page_evidence(
        leaf,
        0,
        None,
        _stored(_fixture("arxiv_final.xml"), request.url, "application/atom+xml"),
    )
    result = evaluate_leaf(
        leaf, [evidence], expected_content_types=("application/atom+xml",)
    )
    assert evidence.parsed.capacity_echo == 2
    assert evidence.parsed.actual_count == 1
    assert _condition(result, 3).passed is True

    integrated = build_page_evidence(
        leaf,
        0,
        None,
        _stored(
            _fixture("arxiv_partial_final_valid.xml"),
            request.url,
            "application/atom+xml; charset=utf-8",
        ),
    )
    integrated_result = evaluate_leaf(
        leaf, [integrated], expected_content_types=("application/atom+xml",)
    )
    assert integrated.parsed.capacity_echo == 200
    assert integrated.parsed.actual_count == 1
    assert tuple(
        condition.passed
        for condition in integrated_result.completion.condition_results
    ) == (True, True, True, True, True, True)
    assert integrated_result.passed is True


def test_condition2_checks_position_only_not_short_page_count() -> None:
    leaf = _arxiv_leaf("short page query")
    request = build_request(leaf, 0, None)
    evidence = build_page_evidence(
        leaf,
        0,
        None,
        _stored(_fixture("arxiv_nonfinal_short.xml"), request.url, "application/atom+xml"),
    )
    result = evaluate_leaf(
        leaf, [evidence], expected_content_types=("application/atom+xml",)
    )
    assert _condition(result, 2).passed is True
    assert _condition(result, 3).passed is False


def test_declared_total_drift_is_not_accepted_from_final_page_value() -> None:
    leaf = _arxiv_leaf("q")
    first = _page(
        page_number=0,
        declared_total=2,
        actual_count=1,
        position=0,
        work_ids=("id-1",),
    )
    final = _page(
        page_number=1,
        declared_total=3,
        actual_count=2,
        position=200,
        work_ids=("id-2", "id-3"),
    )
    result = evaluate_leaf(
        leaf,
        [first, final],
        expected_content_types=("application/atom+xml",),
    )
    assert _condition(result, 5).passed is False
    assert _condition(result, 5).reason_code == "declared_total_drift"
    assert result.rerun_requested is True
    assert result.rerun_performed is False


def test_drift_allows_exactly_one_page_zero_rerun() -> None:
    leaf = _arxiv_leaf("q")
    first_run = [
        _page(page_number=0, declared_total=1, actual_count=0, position=0, work_ids=()),
        _page(page_number=1, declared_total=0, actual_count=0, position=200, work_ids=()),
    ]
    second_run = [
        _page(page_number=0, declared_total=0, actual_count=0, position=0, work_ids=())
    ]
    result = evaluate_leaf(
        leaf,
        first_run,
        expected_content_types=("application/atom+xml",),
        rerun_pages=second_run,
    )
    assert result.rerun_performed is True
    assert result.rerun_requested is False
    assert _condition(result, 5).passed is True
    with pytest.raises(ValueError, match="only after"):
        evaluate_leaf(
            leaf,
            second_run,
            expected_content_types=("application/atom+xml",),
            rerun_pages=second_run,
        )


def test_duplicate_occurrence_is_rejected_but_retained_in_ledger() -> None:
    leaf = _arxiv_leaf("q")
    page = _page(
        page_number=0,
        declared_total=2,
        actual_count=2,
        position=0,
        work_ids=("same-id", "same-id"),
    )
    result = evaluate_leaf(
        leaf, [page], expected_content_types=("application/atom+xml",)
    )
    assert _condition(result, 4).reason_code == "duplicate_index_work_id"
    assert result.duplicate_occurrences == (("same-id", 0, 1),)
    assert [item.index_work_id for item in page.parsed.occurrences] == [
        "same-id",
        "same-id",
    ]


def test_dblp_cutoff_fields_flow_without_dropping_raw_occurrences() -> None:
    leaf = LeafDefinition(
        "B5-TEST@dblp",
        "query",
        "dblp",
        "https://dblp.org/search/publ/api?q=transaction%20backoff&format=json&h=100&f={POS}",
        "https://dblp.org/search/publ/api?q=transaction%20backoff&format=json&h=100&f=0",
        (("T01",), ("M01",)),
        {"T01": "transaction", "M01": "backoff"},
        "2026-12-31",
    )
    request = build_request(leaf, 0, None)
    evidence = build_page_evidence(
        leaf,
        0,
        None,
        _stored(_fixture("dblp_cutoff.json"), request.url, "application/json"),
    )
    assert evidence.parsed.actual_count == 4
    assert tuple(item.included_by_cutoff for item in evidence.parsed.occurrences) == (
        True,
        False,
        None,
        None,
    )
    assert tuple(item.requires_ruling for item in evidence.parsed.occurrences) == (
        False,
        False,
        True,
        True,
    )
    assert len(evidence.to_record()["occurrences"]) == 4


def test_condition6_accepts_media_parameter_and_rejects_wrong_type() -> None:
    body = (
        b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" '
        b'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
        b'<title>q</title><opensearch:totalResults>0</opensearch:totalResults>'
        b'<opensearch:itemsPerPage>200</opensearch:itemsPerPage>'
        b'<opensearch:startIndex>0</opensearch:startIndex></feed>'
    )
    leaf = _arxiv_leaf("q")
    request = build_request(leaf, 0, None)
    accepted = build_page_evidence(
        leaf,
        0,
        None,
        _stored(body, request.url, "application/atom+xml; charset=utf-8"),
    )
    accepted_result = evaluate_leaf(
        leaf, [accepted], expected_content_types=("application/atom+xml",)
    )
    assert accepted_result.passed is True
    rejected = replace(
        accepted, content_type="text/html", media_type="text/html"
    )
    rejected_result = evaluate_leaf(
        leaf, [rejected], expected_content_types=("application/atom+xml",)
    )
    assert _condition(rejected_result, 6).reason_code == "content_type_mismatch"
    assert accepted.to_record()["response"]["headers"][-2:] == [
        ["X-Test", "one"],
        ["X-Test", "two"],
    ]


def test_main_run_issuance_fails_closed_with_all_six_unregistered_fields(
    tmp_path: Path,
) -> None:
    leaf = resolve_leaf(_catalog(), "B5-Q1@arxiv")
    request = build_request(leaf, 0, None)
    with pytest.raises(UnregisteredRunPolicyError) as captured:
        issue_run_request(request)
    assert captured.value.as_record() == {
        "error_code": "unregistered_run_policy",
        "unregistered_fields": [
            "expected_content_types",
            "timeout_s",
            "user_agent",
            "request_interval_s",
            "retryable_failures",
            "redirect_policy",
        ],
    }

    _record, live_path, _issued = _run_successful_live_preflight(tmp_path)
    with pytest.raises(UnregisteredRunPolicyError) as production_captured:
        run_leaf(
            "B5-Q1@arxiv",
            registration_commit=COMMIT,
            repo_root=ROOT,
            live_preflight_path=live_path,
            _git_backend=_worktree_git(),
        )
    assert production_captured.value.as_record() == captured.value.as_record()

    pristine = json.loads(live_path.read_text(encoding="utf-8"))
    mutations = (
        ("arxiv", "status", 404),
        ("openalex", "content_type", "text/html"),
        ("dblp", "transport_error", "timeout"),
        ("arxiv", "arxiv_entry_count", 0),
        ("openalex", "json_root_type", "list"),
        ("dblp", "dblp_matching_doi_count", 0),
    )
    for index, field, replacement in mutations:
        inconsistent = json.loads(json.dumps(pristine))
        lookup = next(
            item for item in inconsistent["lookups"] if item["index"] == index
        )
        if field in lookup["observed_shape"]:
            lookup["observed_shape"][field] = replacement
        else:
            lookup[field] = replacement
        live_path.write_text(
            json.dumps(inconsistent, ensure_ascii=False), encoding="utf-8"
        )
        with pytest.raises(
            PreflightError, match="inconsistent with its observation"
        ):
            run_leaf(
                "B5-Q1@arxiv",
                registration_commit=COMMIT,
                repo_root=ROOT,
                live_preflight_path=live_path,
                _git_backend=_worktree_git(),
            )


def test_retry_delays_are_the_frozen_tuple() -> None:
    """Freeze the registered delay tuple; this is not an effective retry test."""

    assert RETRY_DELAYS_S == (3.0, 6.0, 12.0)


def test_page_and_leaf_records_are_draft07_schema_valid() -> None:
    body = (
        b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" '
        b'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
        b'<title>q</title><opensearch:totalResults>0</opensearch:totalResults>'
        b'<opensearch:itemsPerPage>200</opensearch:itemsPerPage>'
        b'<opensearch:startIndex>0</opensearch:startIndex></feed>'
    )
    leaf = _arxiv_leaf("q")
    request = build_request(leaf, 0, None)
    evidence = build_page_evidence(
        leaf, 0, None, _stored(body, request.url, "application/atom+xml")
    )
    evaluation = evaluate_leaf(
        leaf, [evidence], expected_content_types=("application/atom+xml",)
    )
    schema = json.loads(
        (ROOT / "orchestrator/schemas/axis_b5_search_page_evidence.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.Draft7Validator.check_schema(schema)
    jsonschema.validate(evidence.to_record(), schema)
    jsonschema.validate(evaluation.to_record(), schema)
    assert "control_firing" not in evaluation.to_record()
    invalid = evidence.to_record()
    del invalid["response"]["body_sha256"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid, schema)


def test_live_record_is_schema_valid_and_unclassified_is_false_side() -> None:
    results = [_lookup_result(anchor_id, index, "収録") for anchor_id, index in MEMBERS]
    results[-1] = _lookup_result("G3-07", "dblp", "unclassified")
    record = _evaluate_live_preflight_for_test(
        results,
        registration_seal=_minimal_seal(),
        timeout_s=5,
        user_agent="schema-test",
        request_interval_s=1,
    )
    schema = json.loads(
        (ROOT / "orchestrator/schemas/axis_b5_search_live_preflight.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.Draft7Validator.check_schema(schema)
    jsonschema.validate(record, schema)
    assert record["passed"] is False
    assert record["may_start_run"] is False

    standalone_schema = json.loads(
        (
            ROOT
            / "orchestrator/schemas/axis_b5_search_registration_seal.schema.json"
        ).read_text(encoding="utf-8")
    )
    jsonschema.validate(record["registration_seal"], standalone_schema)
    invalid_seal = json.loads(json.dumps(record["registration_seal"]))
    invalid_seal["seal_scope"]["includes"].append("unregistered-layer")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid_seal, standalone_schema)
    invalid_record = json.loads(json.dumps(record))
    invalid_record["registration_seal"] = invalid_seal
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid_record, schema)


def test_live_missing_member_is_schema_valid_and_false_side() -> None:
    results = [
        _lookup_result(anchor_id, index, "収録")
        for anchor_id, index in MEMBERS[:-1]
    ]
    record = _evaluate_live_preflight_for_test(
        results,
        registration_seal=_minimal_seal(),
        timeout_s=5,
        user_agent="schema-test",
        request_interval_s=1,
    )
    schema = json.loads(
        (ROOT / "orchestrator/schemas/axis_b5_search_live_preflight.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.validate(record, schema)
    assert record["exact_member_set"] is False
    assert record["passed"] is False


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
