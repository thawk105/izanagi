# -*- coding: utf-8 -*-
"""K2 knowledge manifest parser / producer の回帰テスト。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from orchestrator.campaign import knowledge_manifest as KM


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


@pytest.fixture
def source_repo(tmp_path: Path) -> dict[str, object]:
    repo = tmp_path / "source-repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.name", "Izanagi Test")
    _git(repo, "config", "user.email", "izanagi-test@example.invalid")
    (repo / "a.txt").write_bytes("alpha\n".encode("utf-8"))
    (repo / "nested").mkdir()
    (repo / "nested" / "b.txt").write_bytes("日本語 beta\n".encode("utf-8"))
    (repo / "binary.bin").write_bytes(b"\xff\x00")
    _git(repo, "add", "--", "a.txt", "nested/b.txt", "binary.bin")
    _git(repo, "commit", "--quiet", "-m", "fixture sources")
    commit = _git(repo, "rev-parse", "HEAD").decode("ascii").strip()
    return {
        "repo": repo,
        "commit": commit,
        "a": b"alpha\n",
        "b": "日本語 beta\n".encode("utf-8"),
        "binary": b"\xff\x00",
    }


def _repo_source(commit: str, path: str, raw: bytes) -> dict[str, object]:
    return {
        "kind": "repo_artifact",
        "identity": {"commit": commit, "path": path},
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _manifest(*sources: dict[str, object]) -> dict[str, object]:
    return {"knowledge_level": "K2", "sources": list(sources)}


def _declared_scope(selector: str = "output/insights/2026-09-03_*") -> dict:
    return {
        "retrieval": [{"kind": "repo_artifact", "selector": selector}],
        "injection": [{
            "kind": "repo_artifact",
            "selector": "all-successfully-retrieved-sources",
        }],
    }


def _extended_manifest(
    *sources: dict[str, object],
    selector: str = "output/insights/2026-09-03_*",
    status: str = "completed_empty",
    result_count: int = 0,
) -> dict[str, object]:
    return {
        "knowledge_level": "K2",
        "declared_scope": _declared_scope(selector),
        "retrieval_result": {
            "status": status,
            "result_count": result_count,
        },
        "sources": list(sources),
    }


def _parse(value: object) -> KM.KnowledgeManifest:
    return KM.parse_manifest_bytes(json.dumps(
        value, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8"))


@pytest.mark.parametrize(
    "raw",
    (
        b'{"knowledge_level":"K2","knowledge_level":"K2","sources":[]}',
        b'{"knowledge_level":"K2","sources":[{"kind":"repo_artifact",'
        b'"kind":"repo_artifact","identity":{"commit":"0000000000000000000000000000000000000000",'
        b'"path":"a"},"sha256":"0000000000000000000000000000000000000000000000000000000000000000"}]}',
        b'{"knowledge_level":"K2","sources":[{"kind":"repo_artifact",'
        b'"identity":{"commit":"0000000000000000000000000000000000000000",'
        b'"commit":"0000000000000000000000000000000000000000","path":"a"},'
        b'"sha256":"0000000000000000000000000000000000000000000000000000000000000000"}]}',
    ),
)
def test_duplicate_json_keys_are_rejected_at_every_object_level(raw):
    with pytest.raises(KM.DuplicateKnowledgeManifestKeyError, match="duplicate key"):
        KM.parse_manifest_bytes(raw)


@pytest.mark.parametrize("layer", ("top", "source", "identity"))
def test_unknown_keys_are_rejected_at_every_schema_layer(source_repo, layer):
    source = _repo_source(
        source_repo["commit"], "a.txt", source_repo["a"],
    )
    value = _manifest(source)
    if layer == "top":
        value["unknown"] = True
    elif layer == "source":
        source["unknown"] = True
    else:
        source["identity"]["unknown"] = True
    with pytest.raises(KM.KnowledgeManifestError, match="unknown"):
        _parse(value)


def test_only_k2_and_nonempty_sources_are_accepted(source_repo):
    source = _repo_source(
        source_repo["commit"], "a.txt", source_repo["a"],
    )
    for level in ("K0", "K1", "k2", None):
        with pytest.raises(KM.KnowledgeManifestError, match="K2"):
            _parse({"knowledge_level": level, "sources": [source]})
    with pytest.raises(KM.KnowledgeManifestError, match="1 件以上"):
        _parse({"knowledge_level": "K2", "sources": []})


@pytest.mark.parametrize(
    "path",
    ("", "/absolute", "a//b", "a/./b", "a/../b", "a\\b", "a/"),
)
def test_noncanonical_repo_paths_are_rejected(source_repo, path):
    source = _repo_source(source_repo["commit"], path, source_repo["a"])
    with pytest.raises(KM.KnowledgeManifestError, match="path"):
        _parse(_manifest(source))


def test_noncanonical_commit_and_sha_are_rejected(source_repo):
    source = _repo_source(
        source_repo["commit"].upper(), "a.txt", source_repo["a"],
    )
    with pytest.raises(KM.KnowledgeManifestError, match="40 hex"):
        _parse(_manifest(source))
    source = _repo_source(
        source_repo["commit"], "a.txt", source_repo["a"],
    )
    source["sha256"] = source["sha256"].upper()
    with pytest.raises(KM.KnowledgeManifestError, match="lowercase"):
        _parse(_manifest(source))


def test_duplicate_or_conflicting_source_identity_is_rejected(source_repo):
    first = _repo_source(
        source_repo["commit"], "a.txt", source_repo["a"],
    )
    second = json.loads(json.dumps(first))
    second["sha256"] = "0" * 64
    with pytest.raises(KM.KnowledgeManifestError, match="重複または競合"):
        _parse(_manifest(first, second))


def test_canonical_manifest_ignores_source_and_key_order(source_repo):
    a = _repo_source(source_repo["commit"], "a.txt", source_repo["a"])
    b = _repo_source(
        source_repo["commit"], "nested/b.txt", source_repo["b"],
    )
    first = _parse(_manifest(a, b))
    second_value = {
        "sources": [
            {"sha256": b["sha256"], "identity": b["identity"], "kind": b["kind"]},
            {"identity": a["identity"], "kind": a["kind"], "sha256": a["sha256"]},
        ],
        "knowledge_level": "K2",
    }
    second = _parse(second_value)
    assert KM.canonical_manifest_bytes(first) == KM.canonical_manifest_bytes(second)
    assert KM.manifest_sha256(first) == KM.manifest_sha256(second)


def test_completed_empty_retrieval_is_accepted_and_recorded(source_repo):
    """Rejects an empty legacy manifest without scope and a completed result. Accepts and records a declared completed-empty retrieval through resolution and a v2 receipt."""
    with pytest.raises(KM.KnowledgeManifestError, match="declared_scope"):
        _parse(_manifest())

    parsed = _parse(_extended_manifest())
    resolved = KM.resolve_live_sources(parsed, repo_root=source_repo["repo"])
    receipt = KM.receipt_value(
        resolved,
        classification="reproduction_or_selection",
        de_novo_claim=False,
    )

    assert resolved.sources == ()
    assert KM.planner_projection(resolved)["sources"] == []
    assert receipt["schema_version"] == KM.EXTENDED_RECEIPT_SCHEMA_VERSION
    assert receipt["canonical_manifest"]["declared_scope"] == _declared_scope()
    assert receipt["canonical_manifest"]["retrieval_result"] == {
        "status": "completed_empty",
        "result_count": 0,
    }
    assert "呼び手の宣言" in receipt["declaration_status"]
    assert "強制しない" in receipt["declaration_status"]


@pytest.mark.parametrize(
    "mutation",
    (
        "missing-scope",
        "missing-result",
        "empty-retrieval-scope",
        "empty-injection-scope",
        "unknown-status",
        "empty-with-nonempty-result",
        "empty-status-with-positive-count",
    ),
)
def test_empty_sources_require_declared_scope_and_completed_empty_result(
    mutation, source_repo,
):
    """Rejects each partial or contradictory empty-source declaration. Accepts a valid completed-empty declaration and a nonempty retrieval count independent of injected-source length."""
    invalid = _extended_manifest()
    if mutation == "missing-scope":
        del invalid["declared_scope"]
    elif mutation == "missing-result":
        del invalid["retrieval_result"]
    elif mutation == "empty-retrieval-scope":
        invalid["declared_scope"]["retrieval"] = []
    elif mutation == "empty-injection-scope":
        invalid["declared_scope"]["injection"] = []
    elif mutation == "unknown-status":
        invalid["retrieval_result"]["status"] = "failed"
    elif mutation == "empty-with-nonempty-result":
        invalid["retrieval_result"] = {
            "status": "completed_nonempty", "result_count": 1,
        }
    else:
        invalid["retrieval_result"]["result_count"] = 1
    with pytest.raises(KM.KnowledgeManifestError):
        _parse(invalid)

    source = _repo_source(
        source_repo["commit"], "a.txt", source_repo["a"],
    )
    accepted = _parse(_extended_manifest(
        source, status="completed_nonempty", result_count=7,
    ))
    assert len(accepted.sources) == 1
    assert accepted.retrieval_result.result_count == 7


def test_extended_manifest_digest_binds_scope_and_retrieval_result(source_repo):
    """Rejects canonicalization that drops either scope or retrieval-result differences from the digest. Accepts reordered but equivalent scope entries as the same canonical manifest."""
    source = _repo_source(
        source_repo["commit"], "a.txt", source_repo["a"],
    )
    base = _parse(_extended_manifest(
        source, status="completed_nonempty", result_count=5,
    ))
    changed_scope = _parse(_extended_manifest(
        source,
        selector="output/insights/another-*",
        status="completed_nonempty",
        result_count=5,
    ))
    changed_result = _parse(_extended_manifest(
        source, status="completed_nonempty", result_count=8,
    ))
    assert len({
        KM.manifest_sha256(base),
        KM.manifest_sha256(changed_scope),
        KM.manifest_sha256(changed_result),
    }) == 3

    reordered_value = _extended_manifest(
        source, status="completed_nonempty", result_count=5,
    )
    reordered_value["declared_scope"] = {
        "injection": [
            {"selector": "all-successfully-retrieved-sources", "kind": "repo_artifact"}
        ],
        "retrieval": [
            {"selector": "output/insights/2026-09-03_*", "kind": "repo_artifact"}
        ],
    }
    assert KM.manifest_sha256(_parse(reordered_value)) == KM.manifest_sha256(base)


def test_receipt_version_is_v1_for_legacy_and_v2_for_extended(source_repo):
    """Rejects unconditional receipt-version promotion that would change legacy bytes. Accepts v1 for the old two-key manifest and v2 only when an extension field is present."""
    source = _repo_source(
        source_repo["commit"], "a.txt", source_repo["a"],
    )
    legacy = KM.resolve_live_sources(
        _parse(_manifest(source)), repo_root=source_repo["repo"],
    )
    extended = KM.resolve_live_sources(
        _parse(_extended_manifest(
            source, status="completed_nonempty", result_count=4,
        )),
        repo_root=source_repo["repo"],
    )
    legacy_receipt = KM.receipt_value(
        legacy, classification="de_novo", de_novo_claim=True,
    )
    extended_receipt = KM.receipt_value(
        extended, classification="de_novo", de_novo_claim=True,
    )
    assert legacy_receipt["schema_version"] == KM.RECEIPT_SCHEMA_VERSION
    assert legacy_receipt["declaration_status"] == KM.DECLARATION_STATUS
    assert set(legacy_receipt["canonical_manifest"]) == {
        "knowledge_level", "sources",
    }
    assert extended_receipt["schema_version"] == (
        KM.EXTENDED_RECEIPT_SCHEMA_VERSION
    )


def test_nonempty_extended_manifest_fields_are_independently_optional(source_repo):
    """Rejects treating either extension field as universally required for nonempty sources. Accepts scope-only and retrieval-result-only manifests as v2 while retaining their exact present-field set."""
    source = _repo_source(
        source_repo["commit"], "a.txt", source_repo["a"],
    )
    scope_only_value = _manifest(source)
    scope_only_value["declared_scope"] = _declared_scope()
    result_only_value = _manifest(source)
    result_only_value["retrieval_result"] = {
        "status": "completed_nonempty",
        "result_count": 9,
    }
    for value, expected_extension in (
        (scope_only_value, "declared_scope"),
        (result_only_value, "retrieval_result"),
    ):
        resolved = KM.resolve_live_sources(
            _parse(value), repo_root=source_repo["repo"],
        )
        receipt = KM.receipt_value(
            resolved,
            classification="reproduction_or_selection",
            de_novo_claim=False,
        )
        assert receipt["schema_version"] == KM.EXTENDED_RECEIPT_SCHEMA_VERSION
        assert set(receipt["canonical_manifest"]) == {
            "knowledge_level", "sources", expected_extension,
        }


def test_repo_source_uses_commit_blob_not_working_tree_and_projects_exact_bytes(
    source_repo,
):
    repo = source_repo["repo"]
    manifest = _parse(_manifest(_repo_source(
        source_repo["commit"], "a.txt", source_repo["a"],
    )))
    (repo / "a.txt").write_text("working tree replacement\n", encoding="utf-8")
    resolved = KM.resolve_live_sources(manifest, repo_root=repo)
    projection = KM.planner_projection(resolved)
    assert resolved.sources[0].raw_bytes == source_repo["a"]
    assert projection["sources"][0]["content_utf8"] == "alpha\n"
    assert projection["data_boundary"] == KM.DATA_BOUNDARY


@pytest.mark.parametrize("failure", ("missing-commit", "missing-path", "tree", "sha"))
def test_repo_source_resolution_fails_closed_for_each_identity_failure(
    source_repo, failure,
):
    commit = source_repo["commit"]
    path = "a.txt"
    raw = source_repo["a"]
    if failure == "missing-commit":
        commit = "0" * 40
    elif failure == "missing-path":
        path = "absent.txt"
    elif failure == "tree":
        path = "nested"
        raw = b"not-a-blob"
    elif failure == "sha":
        raw = b"different expected bytes"
    parsed = _parse(_manifest(_repo_source(commit, path, raw)))
    with pytest.raises(KM.KnowledgeManifestError):
        KM.resolve_live_sources(parsed, repo_root=source_repo["repo"])


def test_source_sha_mismatch_has_no_other_rejection_layer(source_repo):
    source = _repo_source(
        source_repo["commit"], "a.txt", b"wrong but schema-valid bytes",
    )
    parsed = _parse(_manifest(source))
    assert parsed.sources[0].identity["path"] == "a.txt"
    with pytest.raises(KM.KnowledgeManifestError, match="SHA-256.*不一致"):
        KM.resolve_live_sources(parsed, repo_root=source_repo["repo"])


def test_non_utf8_repo_blob_is_rejected_after_digest_verification(source_repo):
    parsed = _parse(_manifest(_repo_source(
        source_repo["commit"], "binary.bin", source_repo["binary"],
    )))
    with pytest.raises(KM.KnowledgeManifestError, match="strict UTF-8"):
        KM.resolve_live_sources(parsed, repo_root=source_repo["repo"])


def test_web_schema_parses_but_live_resolution_stops_before_receipt(source_repo):
    web = {
        "kind": "web",
        "identity": {
            "url": "https://example.invalid/source?a=1",
            "retrieved_at": "2026-09-02T12:34:56Z",
        },
        "sha256": "1" * 64,
    }
    parsed = _parse(_manifest(web))
    assert parsed.sources[0].kind == "web"
    with pytest.raises(KM.KnowledgeManifestError, match="web source"):
        KM.resolve_live_sources(parsed, repo_root=source_repo["repo"])


@pytest.mark.parametrize(
    "identity",
    (
        {"url": "relative/path", "retrieved_at": "2026-09-02T12:34:56Z"},
        {"url": "https://example.invalid/x", "retrieved_at": "2026-09-02T12:34Z"},
    ),
)
def test_web_identity_requires_absolute_url_and_utc_seconds(identity):
    with pytest.raises(KM.KnowledgeManifestError):
        _parse(_manifest({"kind": "web", "identity": identity, "sha256": "2" * 64}))


def test_receipt_is_canonical_create_only_and_claims_are_caller_inputs(
    source_repo, tmp_path,
):
    resolved = KM.resolve_live_sources(_parse(_manifest(_repo_source(
        source_repo["commit"], "a.txt", source_repo["a"],
    ))), repo_root=source_repo["repo"])
    root = tmp_path / "campaign"
    path = KM.write_receipt(
        root,
        resolved,
        classification="known_result_conditioned_derivative",
        de_novo_claim=False,
    )
    first = path.read_bytes()
    assert first.endswith(b"\n") and not first.endswith(b"\n\n")
    decoded = json.loads(first)
    assert decoded["claim_boundary"] == {
        "classification": "known_result_conditioned_derivative",
        "de_novo_claim": False,
        "pilot_comparison_eligible": False,
    }
    assert decoded["planner_projection"] == {
        "payload_key": "knowledge_input",
        "data_boundary": KM.DATA_BOUNDARY,
    }
    assert decoded["declaration_status"] == (
        "data_boundary と claim_boundary は記録上の宣言であり強制機構ではない。"
        "pilot_comparison_eligible を読む consumer は現時点で存在しない。"
    )
    canonical = KM.canonical_json_bytes(decoded) + b"\n"
    assert first == canonical
    assert KM.write_receipt(
        root,
        resolved,
        classification="known_result_conditioned_derivative",
        de_novo_claim=False,
    ).read_bytes() == first

    with pytest.raises(KM.KnowledgeManifestError, match="上書き"):
        KM.write_receipt(
            root,
            resolved,
            classification="reproduction_or_selection",
            de_novo_claim=True,
        )
    assert path.read_bytes() == first


def test_receipt_canonical_manifest_rederives_digest_and_source_identity(
    source_repo, tmp_path,
):
    source = _repo_source(
        source_repo["commit"], "nested/b.txt", source_repo["b"],
    )
    resolved = KM.resolve_live_sources(
        _parse(_manifest(source)), repo_root=source_repo["repo"],
    )
    path = KM.write_receipt(
        tmp_path,
        resolved,
        classification="reproduction_or_selection",
        de_novo_claim=False,
    )
    receipt = json.loads(path.read_bytes())
    canonical = KM.canonical_json_bytes(receipt["canonical_manifest"])
    assert hashlib.sha256(canonical).hexdigest() == receipt[
        "knowledge_manifest_sha256"
    ]
    assert receipt["canonical_manifest"]["sources"] == [source]


@pytest.mark.parametrize(
    ("classification", "de_novo_claim"),
    (
        ("de_novo", True),
        ("known_result_conditioned_derivative", False),
        ("reproduction_or_selection", False),
    ),
)
def test_receipt_accepts_exactly_the_three_declared_classifications(
    source_repo, classification, de_novo_claim,
):
    resolved = KM.resolve_live_sources(_parse(_manifest(_repo_source(
        source_repo["commit"], "a.txt", source_repo["a"],
    ))), repo_root=source_repo["repo"])
    receipt = KM.receipt_value(
        resolved,
        classification=classification,
        de_novo_claim=de_novo_claim,
    )
    assert receipt["claim_boundary"]["classification"] == classification
    assert receipt["claim_boundary"]["de_novo_claim"] is de_novo_claim


def test_receipt_rejects_unknown_classification_as_only_failure(source_repo):
    resolved = KM.resolve_live_sources(_parse(_manifest(_repo_source(
        source_repo["commit"], "a.txt", source_repo["a"],
    ))), repo_root=source_repo["repo"])
    with pytest.raises(KM.KnowledgeManifestError, match="3 literal"):
        KM.receipt_value(
            resolved,
            classification="unregistered_classification",
            de_novo_claim=False,
        )


def test_receipt_rejects_de_novo_claim_for_non_de_novo_classification(
    source_repo,
):
    resolved = KM.resolve_live_sources(_parse(_manifest(_repo_source(
        source_repo["commit"], "a.txt", source_repo["a"],
    ))), repo_root=source_repo["repo"])
    with pytest.raises(KM.KnowledgeManifestError, match="de_novo 分類以外"):
        KM.receipt_value(
            resolved,
            classification="reproduction_or_selection",
            de_novo_claim=True,
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
