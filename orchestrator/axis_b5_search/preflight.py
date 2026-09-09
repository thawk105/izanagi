"""Registration and anchor-lookup preflights for the Axis B5 leaf executor.

The registration preflight is network-zero.  The live preflight is a separate
operation and creates its transport only after registration has succeeded.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import time
from typing import Any, Callable, Mapping, Protocol, Sequence
from urllib import error, request as urllib_request
from urllib.parse import quote, urlsplit
import xml.etree.ElementTree as ET

from . import catalog


CATALOG_PATH = (
    "docs/related-work/claim-survey/"
    "2026-09-08-backoff-axis-b5-search-catalog.json"
)
CATALOG_SHA256 = (
    "7eb8385e35bd24edac8a227a72ba5bc6b568ca8bc7cac2c8250af8b4ea4c346f"
)
REGISTRATION_SCHEMA_PATH = (
    "orchestrator/schemas/axis_b5_search_registration_seal.schema.json"
)
LIVE_PREFLIGHT_SCHEMA_PATH = (
    "orchestrator/schemas/axis_b5_search_live_preflight.schema.json"
)
ANCHOR_REGISTRY_PATH = "orchestrator/axis_b5_search/anchor_registry.json"

_REGISTERED_DOCUMENTS = (
    "docs/related-work/claim-survey/"
    "2026-09-07-backoff-axis-b5-search-preregistration.md",
    "docs/related-work/claim-survey/"
    "2026-09-08-backoff-axis-b5-closure-preregistration.md",
    "docs/related-work/claim-survey/"
    "2026-09-08-backoff-axis-b5-closure-record.md",
    CATALOG_PATH,
)
_REGISTERED_DIRECTORIES = (
    "orchestrator/axis_b5_search",
    "orchestrator/tests/fixtures/axis_b5_search",
)
_REGISTERED_SCHEMAS = (
    "orchestrator/schemas/axis_b5_search_page_evidence.schema.json",
    LIVE_PREFLIGHT_SCHEMA_PATH,
    REGISTRATION_SCHEMA_PATH,
)
_SEAL_EXCLUDED_LAYERS = (
    "checkpoint",
    "resume",
    "axis-aggregate",
    "control-firing",
    "supplemental-anchor-stream-execution",
)
_OPENSEARCH = "http://a9.com/-/spec/opensearch/1.1/"
_ATOM = "http://www.w3.org/2005/Atom"


@dataclass(frozen=True)
class RegistrationResult:
    passed: bool
    reason_code: str | None
    detail: str
    seal_record: Mapping[str, Any] | None = None

    @property
    def seal(self) -> Mapping[str, Any] | None:
        return self.seal_record


@dataclass(frozen=True)
class Anchor:
    anchor_id: str
    slot: str
    doi: str
    arxiv_id: str | None
    openalex_work_id: str
    first_author_id: str
    last_author_id: str
    member_indexes: tuple[str, ...]


@dataclass(frozen=True)
class LookupRequest:
    anchor_id: str
    index: str
    url: str


@dataclass(frozen=True)
class LookupResponse:
    status: int | None
    headers: tuple[tuple[str, str], ...]
    body: bytes
    final_url: str | None
    transport_error: str | None = None


@dataclass(frozen=True)
class LookupResult:
    anchor_id: str
    index: str
    request_url: str
    classification: str
    status: int | None
    response_headers: tuple[tuple[str, str], ...]
    content_type: str | None
    response_byte_count: int
    body_sha256: str
    final_url: str | None
    transport_error: str | None
    registered_openalex_work_id: str | None
    observed_index_work_id: str | None
    observed_shape: Mapping[str, Any]


class GitBackend(Protocol):
    def head(self) -> str: ...

    def status(self, paths: Sequence[str]) -> bytes: ...

    def blob(self, commit: str, path: str) -> bytes: ...

    def tree(
        self, commit: str, paths: Sequence[str]
    ) -> Mapping[str, tuple[str, str]]: ...


class SubprocessGit:
    """Small Git adapter; it has no network-capable operation."""

    def __init__(self, repo_root: str | os.PathLike[str]) -> None:
        self.repo_root = Path(repo_root)

    def _run(self, args: Sequence[str]) -> bytes:
        completed = subprocess.run(
            ["git", "-C", os.fspath(self.repo_root), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode:
            detail = completed.stderr.decode("utf-8", "replace").strip()
            raise ValueError(f"git {' '.join(args)} failed: {detail}")
        return completed.stdout

    def head(self) -> str:
        return self._run(("rev-parse", "HEAD")).decode("ascii").strip()

    def status(self, paths: Sequence[str]) -> bytes:
        return self._run(
            ("status", "--porcelain=v1", "--untracked-files=all", "--", *paths)
        )

    def blob(self, commit: str, path: str) -> bytes:
        return self._run(("show", f"{commit}:{path}"))

    def tree(
        self, commit: str, paths: Sequence[str]
    ) -> Mapping[str, tuple[str, str]]:
        raw = self._run(("ls-tree", "-r", "-z", commit, "--", *paths))
        result: dict[str, tuple[str, str]] = {}
        for record in raw.split(b"\0"):
            if not record:
                continue
            metadata, raw_path = record.split(b"\t", 1)
            mode, object_type, object_id = metadata.decode("ascii").split()
            if object_type == "blob":
                result[raw_path.decode("utf-8", "surrogateescape")] = (
                    mode,
                    object_id,
                )
        return result


def _failure(code: str, detail: str) -> RegistrationResult:
    return RegistrationResult(False, code, detail)


def _worktree_mode(path: Path) -> str:
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        return "120000"
    if not stat.S_ISREG(mode):
        raise ValueError(f"registered path is not a regular file or symlink: {path}")
    return "100755" if mode & 0o111 else "100644"


def _worktree_bytes(path: Path) -> bytes:
    if path.is_symlink():
        return os.readlink(path).encode("utf-8", "surrogateescape")
    return path.read_bytes()


def _walk_files(repo_root: Path, relative_root: str) -> set[str]:
    absolute_root = repo_root / relative_root
    result: set[str] = set()
    if not absolute_root.is_dir() or absolute_root.is_symlink():
        return result
    for current_root, dirnames, filenames in os.walk(
        absolute_root, followlinks=False
    ):
        current = Path(current_root)
        for dirname in tuple(dirnames):
            candidate = current / dirname
            if candidate.is_symlink():
                result.add(candidate.relative_to(repo_root).as_posix())
                dirnames.remove(dirname)
        for filename in filenames:
            result.add((current / filename).relative_to(repo_root).as_posix())
    return result


def _worktree_registered_paths(repo_root: Path) -> set[str]:
    result = {
        path
        for path in _REGISTERED_DOCUMENTS + _REGISTERED_SCHEMAS
        if (repo_root / path).is_file() or (repo_root / path).is_symlink()
    }
    for directory in _REGISTERED_DIRECTORIES:
        result.update(_walk_files(repo_root, directory))
    schema_root = repo_root / "orchestrator/schemas"
    if schema_root.is_dir():
        result.update(
            path.relative_to(repo_root).as_posix()
            for path in schema_root.glob("axis_b5_search_*.schema.json")
            if path.is_file() or path.is_symlink()
        )
    return result


def _registered_tree(
    backend: GitBackend, registration_commit: str
) -> dict[str, tuple[str, str]]:
    prefixes = _REGISTERED_DOCUMENTS + _REGISTERED_DIRECTORIES
    result = dict(backend.tree(registration_commit, prefixes))
    schema_tree = backend.tree(
        registration_commit, ("orchestrator/schemas",)
    )
    for path, value in schema_tree.items():
        if (
            path.startswith("orchestrator/schemas/axis_b5_search_")
            and path.endswith(".schema.json")
        ):
            result[path] = value
    return result


def _validate_schema(schema: Mapping[str, Any], value: Any) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - repository env provides it
        raise ValueError("jsonschema is required for preflight records") from exc
    jsonschema.Draft7Validator.check_schema(schema)
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.path) or "<root>"
        raise ValueError(f"{location}: {first.message}")


def verify_registration(
    registration_commit: str,
    *,
    repo_root: str | os.PathLike[str],
    git_backend: GitBackend | None = None,
) -> RegistrationResult:
    """Compare the registered commit tree, worktree modes, and worktree bytes."""

    if (
        len(registration_commit) != 40
        or any(character not in "0123456789abcdef" for character in registration_commit)
    ):
        return _failure(
            "registration_commit_invalid",
            "registration_commit must be 40 lowercase hexadecimal digits",
        )
    root = Path(repo_root).resolve()
    backend = git_backend or SubprocessGit(root)
    status_paths = (
        _REGISTERED_DOCUMENTS + _REGISTERED_DIRECTORIES + _REGISTERED_SCHEMAS
    )
    try:
        if backend.head() != registration_commit:
            return _failure("head_mismatch", "HEAD is not registration_commit")
        if backend.status(status_paths).strip():
            return _failure(
                "registration_paths_dirty",
                "a registered path is modified, deleted, or untracked",
            )

        tree = _registered_tree(backend, registration_commit)
        required_fixed = set(_REGISTERED_DOCUMENTS + _REGISTERED_SCHEMAS)
        if not required_fixed.issubset(tree):
            return _failure(
                "registered_path_set_mismatch",
                f"missing={sorted(required_fixed - set(tree))}, extra=[]",
            )
        registered_schemas = {
            path
            for path in tree
            if path.startswith("orchestrator/schemas/axis_b5_search_")
            and path.endswith(".schema.json")
        }
        if registered_schemas != set(_REGISTERED_SCHEMAS):
            return _failure(
                "registered_path_set_mismatch",
                (
                    f"missing={sorted(set(_REGISTERED_SCHEMAS) - registered_schemas)}, "
                    f"extra={sorted(registered_schemas - set(_REGISTERED_SCHEMAS))}"
                ),
            )
        worktree_paths = _worktree_registered_paths(root)
        if worktree_paths != set(tree):
            return _failure(
                "registered_path_set_mismatch",
                (
                    f"missing={sorted(set(tree) - worktree_paths)}, "
                    f"extra={sorted(worktree_paths - set(tree))}"
                ),
            )

        entries: list[dict[str, Any]] = []
        for relative in sorted(tree):
            expected_mode, git_blob = tree[relative]
            absolute = root / relative
            actual_mode = _worktree_mode(absolute)
            if actual_mode != expected_mode:
                return _failure(
                    "registered_mode_mismatch",
                    f"{relative}: worktree={actual_mode}, commit={expected_mode}",
                )
            current = _worktree_bytes(absolute)
            committed = backend.blob(registration_commit, relative)
            if current != committed:
                return _failure(
                    "registered_bytes_mismatch",
                    f"worktree bytes differ from commit blob: {relative}",
                )
            entries.append(
                {
                    "path": relative,
                    "git_blob": git_blob,
                    "mode": expected_mode,
                    "bytes": len(current),
                    "sha256": hashlib.sha256(current).hexdigest(),
                }
            )

        catalog_bytes = (root / CATALOG_PATH).read_bytes()
        if hashlib.sha256(catalog_bytes).hexdigest() != CATALOG_SHA256:
            return _failure(
                "catalog_sha256_mismatch", "catalog file SHA-256 is not registered"
            )
        if catalog_bytes != catalog.render_catalog_json():
            return _failure(
                "catalog_render_mismatch",
                "catalog bytes differ from catalog.render_catalog_json()",
            )

        seal: dict[str, Any] = {
            "schema_version": "izanagi-axis-b5-registration-seal/v1",
            "document_type": "registration_seal",
            "registration_commit": registration_commit,
            "catalog_sha256": CATALOG_SHA256,
            "seal_scope": {
                "kind": "leaf-executor-provisional",
                "provisional": True,
                "includes": [
                    "registration-preflight",
                    "anchor-lookup-preflight",
                    "leaf-response-evaluator",
                ],
                "excludes": list(_SEAL_EXCLUDED_LAYERS),
                "renewal_trigger": "runner-bytes-change-for-checkpoint-or-resume",
            },
            "files": entries,
        }
        schema = json.loads(
            (root / REGISTRATION_SCHEMA_PATH).read_text(encoding="utf-8")
        )
        _validate_schema(schema, seal)
    except (OSError, UnicodeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return _failure("registration_check_error", str(exc))
    return RegistrationResult(
        True,
        None,
        "HEAD, exact path set, modes, bytes, catalog digest, and catalog render match",
        seal,
    )


def load_anchor_registry(
    path: str | os.PathLike[str] | None = None,
) -> tuple[Anchor, ...]:
    source = Path(path) if path is not None else Path(__file__).with_name(
        "anchor_registry.json"
    )
    value = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != (
        "izanagi-axis-b5-anchor-registry/v1"
    ):
        raise ValueError("anchor registry has an unsupported schema_version")
    raw_anchors = value.get("anchors")
    if not isinstance(raw_anchors, list):
        raise ValueError("anchor registry lacks anchors")
    anchors: list[Anchor] = []
    for item in raw_anchors:
        if not isinstance(item, dict) or set(item) != {
            "anchor_id",
            "slot",
            "doi",
            "arxiv_id",
            "openalex_work_id",
            "first_author_id",
            "last_author_id",
            "member_indexes",
        }:
            raise ValueError("anchor registry entry has unknown or missing fields")
        indexes = item["member_indexes"]
        if (
            not isinstance(indexes, list)
            or len(indexes) != len(set(indexes))
            or any(index not in {"arxiv", "openalex", "dblp"} for index in indexes)
        ):
            raise ValueError("anchor registry member_indexes are invalid")
        anchors.append(
            Anchor(
                anchor_id=str(item["anchor_id"]),
                slot=str(item["slot"]),
                doi=str(item["doi"]),
                arxiv_id=(
                    str(item["arxiv_id"])
                    if item["arxiv_id"] is not None
                    else None
                ),
                openalex_work_id=str(item["openalex_work_id"]),
                first_author_id=str(item["first_author_id"]),
                last_author_id=str(item["last_author_id"]),
                member_indexes=tuple(str(index) for index in indexes),
            )
        )
    if len(anchors) != 16 or len({anchor.anchor_id for anchor in anchors}) != 16:
        raise ValueError("anchor registry must contain exactly 16 unique anchors")
    members = {
        (anchor.anchor_id, index)
        for anchor in anchors
        for index in anchor.member_indexes
    }
    expected_openalex = {(anchor.anchor_id, "openalex") for anchor in anchors}
    expected_arxiv = {("G2-08", "arxiv")}
    expected_dblp_ids = {
        "G1-01",
        "G2-04",
        "G2-05",
        "G2-06",
        "G2-07",
        "G2-08",
        "G3-01",
        "G3-02",
        "G3-03",
        "G3-04",
        "G3-05",
        "G3-06",
        "G3-07",
    }
    expected_dblp = {(anchor_id, "dblp") for anchor_id in expected_dblp_ids}
    if members != expected_openalex | expected_arxiv | expected_dblp:
        raise ValueError("anchor registry does not encode the exact 30 members")
    g208 = next(anchor for anchor in anchors if anchor.anchor_id == "G2-08")
    if g208.doi != "10.1137/17M1154679" or g208.arxiv_id != "1710.11258":
        raise ValueError("G2-08 DOI primary key or arXiv lookup key is invalid")
    return tuple(anchors)


def _coerce_anchor(anchor: Anchor | Mapping[str, Any]) -> Anchor:
    if isinstance(anchor, Anchor):
        return anchor
    return Anchor(
        anchor_id=str(anchor["anchor_id"]),
        slot=str(anchor["slot"]),
        doi=str(anchor["doi"]),
        arxiv_id=(
            str(anchor["arxiv_id"]) if anchor.get("arxiv_id") is not None else None
        ),
        openalex_work_id=str(anchor["openalex_work_id"]),
        first_author_id=str(anchor["first_author_id"]),
        last_author_id=str(anchor["last_author_id"]),
        member_indexes=tuple(str(item) for item in anchor["member_indexes"]),
    )


def build_lookup_request(
    anchor: Anchor | Mapping[str, Any], index: str
) -> LookupRequest:
    """Build exactly one of the three registered anchor lookup URL forms."""

    value = _coerce_anchor(anchor)
    if index not in value.member_indexes:
        raise ValueError("anchor/index pair is not a registered member")
    if index == "openalex":
        url = (
            "https://api.openalex.org/works/https://doi.org/"
            f"{value.doi}?select=id,doi,title,publication_year,ids,authorships,"
            "referenced_works_count"
        )
    elif index == "arxiv":
        if value.arxiv_id is None:
            raise ValueError("registered arXiv member lacks an arXiv lookup key")
        url = (
            "https://export.arxiv.org/api/query?id_list="
            f"{value.arxiv_id}&max_results=1"
        )
    elif index == "dblp":
        encoded_doi = quote(value.doi, safe="-_.~")
        url = (
            "https://dblp.org/search/publ/api?q="
            f"{encoded_doi}&format=json&h=5"
        )
    else:
        raise ValueError("unsupported lookup index")
    return LookupRequest(value.anchor_id, index, url)


def _media_type(headers: Sequence[tuple[str, str]]) -> str | None:
    values = [
        value
        for key, value in headers
        if key.strip().lower() == "content-type"
    ]
    if not values:
        return None
    return values[-1].split(";", 1)[0].strip().lower()


def _json_body(body: bytes) -> Any:
    return json.loads(body)


def _normalize_doi(value: str) -> str:
    normalized = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            break
    return normalized.rstrip("/.,; ")


def _strings(value: Any) -> Sequence[str]:
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, list):
        for item in value:
            found.extend(_strings(item))
    elif isinstance(value, dict):
        for item in value.values():
            found.extend(_strings(item))
    return found


def _dblp_hits(value: Any) -> tuple[list[Any], int | None]:
    try:
        hits = value["result"]["hits"]
        raw_total = hits["@total"]
        total = int(raw_total)
        raw_hit = hits.get("hit", [])
    except (KeyError, TypeError, ValueError):
        return [], None
    if raw_hit is None:
        records: list[Any] = []
    elif isinstance(raw_hit, list):
        records = raw_hit
    elif isinstance(raw_hit, dict):
        records = [raw_hit]
    else:
        return [], None
    return records, total


def classify_lookup_response(
    anchor: Anchor | Mapping[str, Any],
    index: str,
    response: LookupResponse,
) -> LookupResult:
    """Classify a saved response without rounding unknown shapes to three values."""

    value = _coerce_anchor(anchor)
    request = build_lookup_request(value, index)
    media_type = _media_type(response.headers)
    shape: dict[str, Any] = {
        "arxiv_entry_count": None,
        "arxiv_total_results": None,
        "dblp_total": None,
        "dblp_matching_doi_count": None,
        "json_root_type": None,
        "parse_error": None,
    }
    classification = "unclassified"
    observed_id: str | None = None

    if response.transport_error is not None or response.status is None:
        classification = "不達"
    elif index == "openalex":
        # The registered absent shape is status-only.  Its observed content type
        # is HTML, so this branch must precede media-type validation.
        if response.status == 404:
            classification = "非収録"
        elif response.status != 200:
            classification = "不達"
        elif media_type != "application/json":
            classification = "不達"
        else:
            try:
                payload = _json_body(response.body)
                shape["json_root_type"] = type(payload).__name__
            except (UnicodeDecodeError, json.JSONDecodeError):
                shape["parse_error"] = "invalid_json"
                classification = "不達"
            else:
                raw_id = payload.get("id") if isinstance(payload, dict) else None
                if isinstance(raw_id, str) and raw_id.startswith(
                    "https://openalex.org/W"
                ):
                    observed_id = raw_id.rsplit("/", 1)[-1]
                    classification = "収録"
    elif index == "arxiv":
        if response.status != 200:
            classification = "不達"
        elif media_type != "application/atom+xml":
            classification = "不達"
        else:
            try:
                root = ET.fromstring(response.body)
                entries = list(root.findall(f"{{{_ATOM}}}entry"))
                raw_total = root.findtext(f"{{{_OPENSEARCH}}}totalResults")
                total = int(raw_total) if raw_total is not None else None
            except (ET.ParseError, UnicodeError, TypeError, ValueError):
                shape["parse_error"] = "invalid_atom"
                classification = "不達"
            else:
                shape["arxiv_entry_count"] = len(entries)
                shape["arxiv_total_results"] = total
                if len(entries) == 1:
                    observed_id = entries[0].findtext(f"{{{_ATOM}}}id")
                    classification = "収録"
                elif len(entries) == 0 and total == 0:
                    classification = "非収録"
    elif index == "dblp":
        if response.status != 200:
            classification = "不達"
        elif media_type != "application/json":
            classification = "不達"
        else:
            try:
                payload = _json_body(response.body)
                shape["json_root_type"] = type(payload).__name__
            except (UnicodeDecodeError, json.JSONDecodeError):
                shape["parse_error"] = "invalid_json"
                classification = "不達"
            else:
                hits, total = _dblp_hits(payload)
                matches = [
                    hit
                    for hit in hits
                    if any(
                        _normalize_doi(candidate) == _normalize_doi(value.doi)
                        for candidate in _strings(hit)
                    )
                ]
                shape["dblp_total"] = total
                shape["dblp_matching_doi_count"] = len(matches)
                if matches:
                    try:
                        raw_key = matches[0]["info"]["key"]
                        observed_id = raw_key if isinstance(raw_key, str) else None
                    except (KeyError, TypeError):
                        observed_id = None
                    classification = "収録"
                elif total == 0:
                    classification = "非収録"
    else:
        raise ValueError("unsupported lookup index")

    return LookupResult(
        anchor_id=value.anchor_id,
        index=index,
        request_url=request.url,
        classification=classification,
        status=response.status,
        response_headers=response.headers,
        content_type=media_type,
        response_byte_count=len(response.body),
        body_sha256=hashlib.sha256(response.body).hexdigest(),
        final_url=response.final_url,
        transport_error=response.transport_error,
        registered_openalex_work_id=(
            value.openalex_work_id if index == "openalex" else None
        ),
        observed_index_work_id=observed_id,
        observed_shape=shape,
    )


def _seal_digest(seal: Mapping[str, Any]) -> str:
    payload = json.dumps(
        seal, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _lookup_record(result: LookupResult) -> dict[str, Any]:
    return {
        "anchor_id": result.anchor_id,
        "index": result.index,
        "control_id": f"B5-ANC-{result.anchor_id}@{result.index}",
        "request_url": result.request_url,
        "classification": result.classification,
        "status": result.status,
        "response_headers": [list(item) for item in result.response_headers],
        "content_type": result.content_type,
        "response_byte_count": result.response_byte_count,
        "body_sha256": result.body_sha256,
        "final_url": result.final_url,
        "transport_error": result.transport_error,
        "registered_openalex_work_id": result.registered_openalex_work_id,
        "observed_index_work_id": result.observed_index_work_id,
        "observed_shape": dict(result.observed_shape),
    }


def evaluate_live_preflight(
    results: Sequence[LookupResult],
    *,
    registration_seal: Mapping[str, Any],
    timeout_s: int | float,
    user_agent: str,
    request_interval_s: int | float,
) -> dict[str, Any]:
    """Evaluate the immutable 30-member lookup set and preserve caller policy."""

    anchors = load_anchor_registry()
    expected = {
        (anchor.anchor_id, index)
        for anchor in anchors
        for index in anchor.member_indexes
    }
    identities = [(result.anchor_id, result.index) for result in results]
    actual = set(identities)
    duplicate = len(identities) != len(actual)
    exact_members = not duplicate and actual == expected and len(identities) == 30
    all_recorded = exact_members and all(
        result.classification == "収録" for result in results
    )
    passed = bool(all_recorded)
    ordered = sorted(results, key=lambda item: (item.index, item.anchor_id))
    return {
        "schema_version": "izanagi-axis-b5-live-preflight/v1",
        "document_type": "live_preflight",
        "registration_commit": registration_seal["registration_commit"],
        "registration_seal_sha256": _seal_digest(registration_seal),
        "registration_seal": dict(registration_seal),
        "transport_policy": {
            "timeout_s": timeout_s,
            "user_agent": user_agent,
            "request_interval_s": request_interval_s,
            "redirect_policy": "do-not-follow",
        },
        "expected_member_count": 30,
        "exact_member_set": exact_members,
        "lookups": [_lookup_record(result) for result in ordered],
        "passed": passed,
        "axis_status": "未完走" if not passed else "preflight-passed",
        "may_start_run": passed,
    }


class _NoRedirect(urllib_request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Any,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


class _LiveTransport:
    def __init__(self, *, timeout_s: int | float, user_agent: str) -> None:
        self.timeout_s = timeout_s
        self.user_agent = user_agent
        self.opener = urllib_request.build_opener(_NoRedirect())

    def get(self, spec: LookupRequest) -> LookupResponse:
        request = urllib_request.Request(
            spec.url, headers={"User-Agent": self.user_agent}, method="GET"
        )
        try:
            with self.opener.open(request, timeout=self.timeout_s) as handle:
                raw_items = getattr(handle.headers, "raw_items", handle.headers.items)
                headers = tuple((str(key), str(value)) for key, value in raw_items())
                return LookupResponse(
                    int(handle.status), headers, handle.read(), handle.geturl()
                )
        except error.HTTPError as exc:
            raw_items = getattr(exc.headers, "raw_items", exc.headers.items)
            headers = tuple((str(key), str(value)) for key, value in raw_items())
            return LookupResponse(
                int(exc.code), headers, exc.read(), exc.geturl()
            )
        except (error.URLError, TimeoutError, OSError) as exc:
            return LookupResponse(None, (), b"", None, str(exc))


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def run_live_preflight(
    registration_commit: str,
    *,
    repo_root: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    timeout_s: int | float,
    user_agent: str,
    request_interval_s: int | float,
    git_backend: GitBackend | None = None,
    _transport_factory: Callable[..., Any] | None = None,
    _sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Run all 30 live lookups after the network-zero registration gate."""

    registration = verify_registration(
        registration_commit, repo_root=repo_root, git_backend=git_backend
    )
    if not registration.passed or registration.seal_record is None:
        raise ValueError(
            f"registration preflight failed: {registration.reason_code}: "
            f"{registration.detail}"
        )
    if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)):
        raise ValueError("timeout_s must be an explicit positive number")
    if timeout_s <= 0:
        raise ValueError("timeout_s must be positive")
    if not isinstance(user_agent, str) or not user_agent:
        raise ValueError("user_agent must be an explicit nonempty string")
    if (
        isinstance(request_interval_s, bool)
        or not isinstance(request_interval_s, (int, float))
        or request_interval_s < 0
    ):
        raise ValueError("request_interval_s must be an explicit nonnegative number")

    # No transport object exists before registration succeeds.
    factory = _transport_factory or _LiveTransport
    transport = factory(timeout_s=timeout_s, user_agent=user_agent)
    results: list[LookupResult] = []
    requests_issued = 0
    for anchor in load_anchor_registry():
        for index in anchor.member_indexes:
            if requests_issued:
                _sleeper(request_interval_s)
            spec = build_lookup_request(anchor, index)
            response = transport.get(spec)
            results.append(classify_lookup_response(anchor, index, response))
            requests_issued += 1
    record = evaluate_live_preflight(
        results,
        registration_seal=registration.seal_record,
        timeout_s=timeout_s,
        user_agent=user_agent,
        request_interval_s=request_interval_s,
    )
    root = Path(repo_root).resolve()
    schema = json.loads(
        (root / LIVE_PREFLIGHT_SCHEMA_PATH).read_text(encoding="utf-8")
    )
    _validate_schema(schema, record)
    _atomic_write_json(Path(output_path), record)
    return record


__all__ = [
    "ANCHOR_REGISTRY_PATH",
    "Anchor",
    "CATALOG_PATH",
    "CATALOG_SHA256",
    "GitBackend",
    "LIVE_PREFLIGHT_SCHEMA_PATH",
    "LookupRequest",
    "LookupResponse",
    "LookupResult",
    "RegistrationResult",
    "SubprocessGit",
    "build_lookup_request",
    "classify_lookup_response",
    "evaluate_live_preflight",
    "load_anchor_registry",
    "run_live_preflight",
    "verify_registration",
]
