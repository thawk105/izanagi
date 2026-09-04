# -*- coding: utf-8 -*-
"""K2 knowledge manifest parser / producer の回帰テスト。"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from orchestrator.campaign import knowledge_manifest as KM


_HISTORICAL_K2_COMMIT = "2fa13a262a53b7f4e610a40a7a7af7f86fc9d621"
_HISTORICAL_K2_SOURCE_BLOBS = {
    "output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/campaign.lock": (
        """
        H4sIAAAAAAACAz1R7WrbMBR9lYt/pbDQbvGPkWfooG9QFFlOxBQpKPLIKAXLKTQjhWWFNVC6j6yhP+o2tBtdWza6
        hxGym7eY5GbTH6F7zzn33KOdAOMW4bizjUW3S1XQDDZevIwbYRQ8C/oEyarDY9oOmjsBGtC+Q/QpE/UWwq9FHNe7
        qM2pSiLiCJJgISMHeb7hjy/ELBk4iuBeDyNGVnz3VB1JkEeHu/9nKdT2gLCOEiW46Iqk74k9gr0NRbh3uNUA+3BQ
        /jwuFjcQNgGLiEh43D+3D2MzzM3wtxlOTZr1GOLcdYw+KI7u7eQD1Gw6N/rc6OkamOyweD8pZiP3Wkk4oB1/MnpW
        Xo49Mjt8PBsbfWx0Dqt94aluJ6NiNDGpjqirFfOT8iiHWogq2WXqGFOjv0BHMAJ2/q78eGX0wug/0Eooi9bfEEnj
        t+tV8m5qvky/myx1lrGkimKwd1f2+rN3eDEDqohEigrukbDM9oobDbXNzVeAWuxfYwH+yr5Vy39dc1IxHahEEpAk
        qna9PC1//LIj5ysvbm+NPqmC2PMfISliLtdeo+6SZ0L0gt2/ok241RkCAAA=
        """
    ),
    "output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl": (
        """
        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
        """
    ),
}


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


@pytest.fixture
def historical_k2_legacy_manifest() -> KM.KnowledgeManifest:
    return _parse({
        "knowledge_level": "K2",
        "sources": [
            {
                "kind": "repo_artifact",
                "identity": {
                    "commit": _HISTORICAL_K2_COMMIT,
                    "path": (
                        "output/campaigns/"
                        "p3-s4-loop-s4-autonomous-0b53a387/campaign.lock"
                    ),
                },
                "sha256": (
                    "0b53a3876589a61ae35b318237751015"
                    "acebb3761e612e4374f9944ffca7f7c9"
                ),
            },
            {
                "kind": "repo_artifact",
                "identity": {
                    "commit": _HISTORICAL_K2_COMMIT,
                    "path": (
                        "output/campaigns/"
                        "p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl"
                    ),
                },
                "sha256": (
                    "2163b794fa3b1fce4de76a1b69262cad"
                    "fc095bd986225a7266d6eacb6210a611"
                ),
            },
        ],
    })


def _historical_k2_resolved(
    manifest: KM.KnowledgeManifest,
) -> KM.ResolvedKnowledgeManifest:
    resolved_sources = []
    for source in manifest.sources:
        path = source.identity["path"]
        raw = gzip.decompress(base64.b64decode(
            _HISTORICAL_K2_SOURCE_BLOBS[path]
        ))
        assert hashlib.sha256(raw).hexdigest() == source.sha256
        resolved_sources.append(KM.ResolvedKnowledgeSource(
            source=source,
            raw_bytes=raw,
            content_utf8=raw.decode("utf-8"),
        ))
    resolved_sources.sort(
        key=lambda item: KM.canonical_json_bytes(item.source.canonical_value())
    )
    canonical = KM.canonical_manifest_bytes(manifest)
    return KM.ResolvedKnowledgeManifest(
        manifest=manifest,
        canonical_manifest_bytes=canonical,
        knowledge_manifest_sha256=hashlib.sha256(canonical).hexdigest(),
        sources=tuple(resolved_sources),
    )


def test_historical_k2_legacy_manifest_and_receipt_match_literal_golden(
    historical_k2_legacy_manifest,
):
    canonical = KM.canonical_manifest_bytes(historical_k2_legacy_manifest)
    assert hashlib.sha256(canonical).hexdigest() == (
        "6d8674228d05e591a67047c4a098e077"
        "f427cb7dd6fdfa3b82d20da2000db406"
    )
    resolved = _historical_k2_resolved(historical_k2_legacy_manifest)
    receipt = KM.receipt_value(
        resolved,
        classification="reproduction_or_selection",
        de_novo_claim=False,
    )
    assert receipt["schema_version"] == "knowledge-manifest-receipt/v1"
    expected = (
        '{"canonical_manifest":{"knowledge_level":"K2","sources":['
        '{"identity":{"commit":"2fa13a262a53b7f4e610a40a7a7af7f86fc9d621",'
        '"path":"output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/'
        'campaign.lock"},"kind":"repo_artifact","sha256":'
        '"0b53a3876589a61ae35b318237751015acebb3761e612e4374f9944ffca7f7c9"},'
        '{"identity":{"commit":"2fa13a262a53b7f4e610a40a7a7af7f86fc9d621",'
        '"path":"output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/'
        'runs/wal.jsonl"},"kind":"repo_artifact","sha256":'
        '"2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611"}'
        ']},"claim_boundary":{"classification":"reproduction_or_selection",'
        '"de_novo_claim":false,"pilot_comparison_eligible":false},'
        '"declaration_status":"data_boundary と claim_boundary は記録上の宣言であり'
        '強制機構ではない。pilot_comparison_eligible を読む consumer は現時点で存在しない。",'
        '"knowledge_level":"K2","knowledge_manifest_sha256":'
        '"6d8674228d05e591a67047c4a098e077f427cb7dd6fdfa3b82d20da2000db406",'
        '"planner_projection":{"data_boundary":'
        '"external_knowledge_is_data_not_instructions",'
        '"payload_key":"knowledge_input"},"schema_version":'
        '"knowledge-manifest-receipt/v1","sources":['
        '{"identity":{"commit":"2fa13a262a53b7f4e610a40a7a7af7f86fc9d621",'
        '"path":"output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/'
        'campaign.lock"},"kind":"repo_artifact","sha256":'
        '"0b53a3876589a61ae35b318237751015acebb3761e612e4374f9944ffca7f7c9",'
        '"verification":{"method":"git-blob-at-commit-path",'
        '"observed_sha256":'
        '"0b53a3876589a61ae35b318237751015acebb3761e612e4374f9944ffca7f7c9",'
        '"status":"verified"}},'
        '{"identity":{"commit":"2fa13a262a53b7f4e610a40a7a7af7f86fc9d621",'
        '"path":"output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/'
        'runs/wal.jsonl"},"kind":"repo_artifact","sha256":'
        '"2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611",'
        '"verification":{"method":"git-blob-at-commit-path",'
        '"observed_sha256":'
        '"2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611",'
        '"status":"verified"}}]}\n'
    ).encode("utf-8")
    assert KM.receipt_bytes(
        resolved,
        classification="reproduction_or_selection",
        de_novo_claim=False,
    ) == expected


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
