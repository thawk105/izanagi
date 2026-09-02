# -*- coding: utf-8 -*-
"""K2 知識 manifest の parser と producer。

``planner_projection`` と ``claim_boundary`` は、投入条件と主張境界を
受領証へ残すための記録上の宣言である。source 本文の解釈、比較集合からの除外、
de novo 分類を強制する機構ではない。受理・拒否の consumer 正本は、この module
ではなく campaign verifier epoch に束縛された :mod:`wal` に置く。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit


KNOWLEDGE_LEVEL = "K2"
RECEIPT_FILENAME = "knowledge_manifest_receipt.json"
RECEIPT_SCHEMA_VERSION = "knowledge-manifest-receipt/v1"
DATA_BOUNDARY = "external_knowledge_is_data_not_instructions"
CLAIM_CLASSIFICATIONS = frozenset({
    "de_novo",
    "known_result_conditioned_derivative",
    "reproduction_or_selection",
})
DECLARATION_STATUS = (
    "data_boundary と claim_boundary は記録上の宣言であり強制機構ではない。"
    "pilot_comparison_eligible を読む consumer は現時点で存在しない。"
)

_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_UTC_SECONDS = re.compile(
    r"(?:[0-9]{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z\Z"
)


class KnowledgeManifestError(ValueError):
    """manifest、source 解決、受領証生成の fail-closed エラー。"""


class DuplicateKnowledgeManifestKeyError(KnowledgeManifestError):
    """JSON object 内に duplicate key がある。"""


@dataclass(frozen=True)
class KnowledgeSource:
    kind: str
    identity: Mapping[str, str]
    sha256: str

    def canonical_value(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "identity": dict(self.identity),
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class KnowledgeManifest:
    knowledge_level: str
    sources: tuple[KnowledgeSource, ...]

    def canonical_value(self) -> dict[str, Any]:
        ordered = sorted(
            (source.canonical_value() for source in self.sources),
            key=canonical_json_bytes,
        )
        return {
            "knowledge_level": self.knowledge_level,
            "sources": ordered,
        }


@dataclass(frozen=True)
class ResolvedKnowledgeSource:
    source: KnowledgeSource
    raw_bytes: bytes
    content_utf8: str


@dataclass(frozen=True)
class ResolvedKnowledgeManifest:
    manifest: KnowledgeManifest
    canonical_manifest_bytes: bytes
    knowledge_manifest_sha256: str
    sources: tuple[ResolvedKnowledgeSource, ...]


def _reject_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKnowledgeManifestKeyError(
                "knowledge manifest JSON に duplicate key がある: %r" % key
            )
        value[key] = item
    return value


def _reject_json_constant(value: str):
    raise KnowledgeManifestError(
        "knowledge manifest JSON に非有限値は使えない: %s" % value
    )


def _exact_keys(value: object, expected: set[str], path: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise KnowledgeManifestError(f"{path} は object でなければならない")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise KnowledgeManifestError(
            f"{path} の key 集合が不正: missing={missing!r} unknown={unknown!r}"
        )
    return value


def _require_sha256(value: object, path: str) -> str:
    if type(value) is not str or _HEX64.fullmatch(value) is None:
        raise KnowledgeManifestError(
            f"{path} は lowercase 64 hex SHA-256 でなければならない"
        )
    return value


def _repo_identity(value: object, path: str) -> dict[str, str]:
    identity = _exact_keys(value, {"commit", "path"}, path)
    commit = identity["commit"]
    source_path = identity["path"]
    if type(commit) is not str or _HEX40.fullmatch(commit) is None:
        raise KnowledgeManifestError(
            f"{path}.commit は lowercase 40 hex でなければならない"
        )
    if type(source_path) is not str or not source_path:
        raise KnowledgeManifestError(f"{path}.path は空でない string が必要")
    segments = source_path.split("/")
    if (
        source_path.startswith("/")
        or "\\" in source_path
        or "\x00" in source_path
        or any(segment in {"", ".", ".."} for segment in segments)
    ):
        raise KnowledgeManifestError(
            f"{path}.path は canonical な repo-relative POSIX path が必要"
        )
    return {"commit": commit, "path": source_path}


def _web_identity(value: object, path: str) -> dict[str, str]:
    identity = _exact_keys(value, {"url", "retrieved_at"}, path)
    url = identity["url"]
    retrieved_at = identity["retrieved_at"]
    if type(url) is not str:
        raise KnowledgeManifestError(f"{path}.url は string が必要")
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
    except ValueError as exc:
        raise KnowledgeManifestError(f"{path}.url が不正") from exc
    if parsed.scheme not in {"http", "https"} or not hostname:
        raise KnowledgeManifestError(
            f"{path}.url は host を持つ absolute http/https URL が必要"
        )
    if type(retrieved_at) is not str or _UTC_SECONDS.fullmatch(retrieved_at) is None:
        raise KnowledgeManifestError(
            f"{path}.retrieved_at は UTC 秒精度 YYYY-MM-DDTHH:MM:SSZ が必要"
        )
    try:
        datetime.strptime(retrieved_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise KnowledgeManifestError(f"{path}.retrieved_at が実在する UTC 日時でない") from exc
    return {"url": url, "retrieved_at": retrieved_at}


def _parse_value(value: object) -> KnowledgeManifest:
    top = _exact_keys(value, {"knowledge_level", "sources"}, "$")
    if top["knowledge_level"] != KNOWLEDGE_LEVEL:
        raise KnowledgeManifestError("$.knowledge_level は literal 'K2' だけを受理する")
    source_values = top["sources"]
    if type(source_values) is not list or not source_values:
        raise KnowledgeManifestError("$.sources は 1 件以上の array が必要")

    parsed_sources: list[KnowledgeSource] = []
    identities: set[tuple[str, tuple[tuple[str, str], ...]]] = set()
    for index, raw_source in enumerate(source_values):
        path = f"$.sources[{index}]"
        source = _exact_keys(raw_source, {"kind", "identity", "sha256"}, path)
        kind = source["kind"]
        if kind == "repo_artifact":
            identity = _repo_identity(source["identity"], path + ".identity")
        elif kind == "web":
            identity = _web_identity(source["identity"], path + ".identity")
        else:
            raise KnowledgeManifestError(
                f"{path}.kind は 'repo_artifact' または 'web' が必要"
            )
        sha256 = _require_sha256(source["sha256"], path + ".sha256")
        identity_key = (kind, tuple(sorted(identity.items())))
        if identity_key in identities:
            raise KnowledgeManifestError(f"{path}.identity が重複または競合している")
        identities.add(identity_key)
        parsed_sources.append(KnowledgeSource(kind, identity, sha256))
    return KnowledgeManifest(KNOWLEDGE_LEVEL, tuple(parsed_sources))


def parse_manifest_bytes(data: bytes) -> KnowledgeManifest:
    """UTF-8 JSON bytes を duplicate-aware に parse して strict schema を返す。"""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise KnowledgeManifestError("knowledge manifest は strict UTF-8 が必要") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise KnowledgeManifestError("knowledge manifest JSON が不正") from exc
    return _parse_value(value)


def parse_manifest(path: str | os.PathLike[str]) -> KnowledgeManifest:
    """path から manifest を読み、strict schema を返す。"""
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise KnowledgeManifestError("knowledge manifest を読めない") from exc
    return parse_manifest_bytes(data)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_manifest_bytes(manifest: KnowledgeManifest) -> bytes:
    if type(manifest) is not KnowledgeManifest:
        raise TypeError("manifest は exact KnowledgeManifest が必要")
    return canonical_json_bytes(manifest.canonical_value())


def manifest_sha256(manifest: KnowledgeManifest) -> str:
    return hashlib.sha256(canonical_manifest_bytes(manifest)).hexdigest()


def _git(repo_root: Path, *args: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise KnowledgeManifestError("Git object database を読めない") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise KnowledgeManifestError(
            "Git object を解決できない" + (f": {detail}" if detail else "")
        )
    return completed.stdout


def _resolve_repo_source(source: KnowledgeSource, repo_root: Path) -> bytes:
    commit = source.identity["commit"]
    source_path = source.identity["path"]
    commit_type = _git(repo_root, "cat-file", "-t", commit).strip()
    if commit_type != b"commit":
        raise KnowledgeManifestError("identity.commit が commit object でない")
    object_spec = f"{commit}:{source_path}"
    object_type = _git(repo_root, "cat-file", "-t", object_spec).strip()
    if object_type != b"blob":
        raise KnowledgeManifestError("identity.path が当該 commit の blob を指していない")
    raw = _git(repo_root, "cat-file", "blob", object_spec)
    observed = hashlib.sha256(raw).hexdigest()
    if observed != source.sha256:
        raise KnowledgeManifestError(
            "repo artifact の raw bytes SHA-256 が manifest と不一致"
        )
    return raw


def resolve_live_sources(
    manifest: KnowledgeManifest,
    *,
    repo_root: str | os.PathLike[str],
) -> ResolvedKnowledgeManifest:
    """repo commit の blob bytes を解決する。web は副作用前に fail-closed。"""
    if type(manifest) is not KnowledgeManifest:
        raise TypeError("manifest は exact KnowledgeManifest が必要")
    if any(source.kind == "web" for source in manifest.sources):
        raise KnowledgeManifestError(
            "web source の live 解決は未配線であり receipt/config/WAL 作成前に停止する"
        )
    root = Path(repo_root)
    resolved: list[ResolvedKnowledgeSource] = []
    for source in manifest.sources:
        raw = _resolve_repo_source(source, root)
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise KnowledgeManifestError(
                "repo artifact は planner 投影用に strict UTF-8 が必要"
            ) from exc
        resolved.append(ResolvedKnowledgeSource(source, raw, content))
    ordered = tuple(
        sorted(resolved, key=lambda item: canonical_json_bytes(item.source.canonical_value()))
    )
    canonical = canonical_manifest_bytes(manifest)
    return ResolvedKnowledgeManifest(
        manifest=manifest,
        canonical_manifest_bytes=canonical,
        knowledge_manifest_sha256=hashlib.sha256(canonical).hexdigest(),
        sources=ordered,
    )


def load_and_resolve_manifest(
    path: str | os.PathLike[str],
    *,
    repo_root: str | os.PathLike[str],
) -> ResolvedKnowledgeManifest:
    return resolve_live_sources(parse_manifest(path), repo_root=repo_root)


def planner_projection(resolved: ResolvedKnowledgeManifest) -> dict[str, Any]:
    """検証済み本文を含む planner 用の記録可能な data projection を返す。"""
    if type(resolved) is not ResolvedKnowledgeManifest:
        raise TypeError("resolved は exact ResolvedKnowledgeManifest が必要")
    return {
        # この data_boundary は記録上の宣言であり、本文解釈の強制機構ではない。
        "data_boundary": DATA_BOUNDARY,
        "knowledge_level": resolved.manifest.knowledge_level,
        "knowledge_manifest_sha256": resolved.knowledge_manifest_sha256,
        "sources": [
            {
                **item.source.canonical_value(),
                "content_utf8": item.content_utf8,
            }
            for item in resolved.sources
        ],
    }


def receipt_value(
    resolved: ResolvedKnowledgeManifest,
    *,
    classification: str,
    de_novo_claim: bool,
) -> dict[str, Any]:
    """呼び手が宣言した分類を使い、決定論的な受領証 value を生成する。

    ``classification`` の wire literal と日本語分類の対応は、``de_novo`` が
    「de novo」、``known_result_conditioned_derivative`` が
    「既知結果に条件づけられた派生」、``reproduction_or_selection`` が
    「再現・選択」である。
    """
    if type(resolved) is not ResolvedKnowledgeManifest:
        raise TypeError("resolved は exact ResolvedKnowledgeManifest が必要")
    if (type(classification) is not str
            or classification not in CLAIM_CLASSIFICATIONS):
        raise KnowledgeManifestError(
            "classification は定義済みの 3 literal のいずれかが必要"
        )
    if type(de_novo_claim) is not bool:
        raise KnowledgeManifestError("de_novo_claim は exact bool が必要")
    if de_novo_claim and classification != "de_novo":
        raise KnowledgeManifestError(
            "de_novo_claim=true は de_novo 分類以外の受領証を作成・上書きできない"
        )
    sources = []
    for item in resolved.sources:
        source = item.source.canonical_value()
        sources.append({
            **source,
            "verification": {
                "method": "git-blob-at-commit-path",
                "status": "verified",
                "observed_sha256": hashlib.sha256(item.raw_bytes).hexdigest(),
            },
        })
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "knowledge_level": resolved.manifest.knowledge_level,
        "knowledge_manifest_sha256": resolved.knowledge_manifest_sha256,
        "canonical_manifest": resolved.manifest.canonical_value(),
        "sources": sources,
        "declaration_status": DECLARATION_STATUS,
        # 以下 2 object は記録上の宣言であり、入力解釈や比較除外の強制機構ではない。
        "planner_projection": {
            "payload_key": "knowledge_input",
            "data_boundary": DATA_BOUNDARY,
        },
        "claim_boundary": {
            "classification": classification,
            "de_novo_claim": de_novo_claim,
            "pilot_comparison_eligible": False,
        },
    }


def receipt_bytes(
    resolved: ResolvedKnowledgeManifest,
    *,
    classification: str,
    de_novo_claim: bool,
) -> bytes:
    return canonical_json_bytes(receipt_value(
        resolved,
        classification=classification,
        de_novo_claim=de_novo_claim,
    )) + b"\n"


def write_receipt(
    campaign_root: str | os.PathLike[str],
    resolved: ResolvedKnowledgeManifest,
    *,
    classification: str,
    de_novo_claim: bool,
) -> Path:
    """create-only atomic publish。既存 bytes が一致するときだけ冪等成功する。"""
    root = Path(campaign_root)
    target = root / RECEIPT_FILENAME
    body = receipt_bytes(
        resolved,
        classification=classification,
        de_novo_claim=de_novo_claim,
    )
    try:
        existing = target.read_bytes()
    except FileNotFoundError:
        existing = None
    except OSError as exc:
        raise KnowledgeManifestError("既存 knowledge receipt を読めない") from exc
    if existing is not None:
        if existing != body:
            raise KnowledgeManifestError(
                "既存 knowledge receipt の bytes が入力と一致せず上書きできない"
            )
        return target

    root.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        fd, raw_temp = tempfile.mkstemp(prefix=".knowledge-receipt-", dir=root)
        temp_path = Path(raw_temp)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(body)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temp_path, target)
            except FileExistsError:
                if target.read_bytes() != body:
                    raise KnowledgeManifestError(
                        "knowledge receipt publish が既存の異なる bytes と衝突した"
                    )
            directory_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
    except KnowledgeManifestError:
        raise
    except OSError as exc:
        raise KnowledgeManifestError("knowledge receipt を atomic publish できない") from exc
    return target
