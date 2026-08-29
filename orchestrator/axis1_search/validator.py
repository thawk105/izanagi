"""Independent validation for the axis-1 search evidence contract."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
from typing import Any, Protocol


FROZEN_BASE_COMMIT = "343b8f5a5"
FROZEN_PREDECESSOR_PATHS = (
    "docs/related-work/claim-survey/2026-08-27-axis1-search-preregistration.md",
    "docs/related-work/claim-survey/2026-08-27-axis1-search-execution.md",
    "output/insights/2026-08-27_t1969-axis1-search-execution",
)
INCOMPLETE_STATES = frozenset(
    {"not_run", "not_started", "paused_quota", "outcome_unknown", "blocked_on_ruling"}
)


@dataclass(frozen=True)
class ConditionResult:
    condition: int
    passed: bool
    reason_code: str | None
    detail: str

    def __post_init__(self) -> None:
        if self.condition not in range(1, 7):
            raise ValueError("condition must be in 1..6")
        if self.passed and self.reason_code is not None:
            raise ValueError("a passing condition cannot have a failure reason")
        if not self.passed and not self.reason_code:
            raise ValueError("a failing condition must have a reason code")


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    reason_code: str | None
    detail: str


class GitBackend(Protocol):
    def head(self) -> str: ...

    def status(self, paths: Sequence[str]) -> bytes: ...

    def blob(self, commit: str, path: str) -> bytes: ...

    def tree(self, commit: str, paths: Sequence[str]) -> Mapping[str, tuple[str, str]]: ...


class SubprocessGit:
    """Minimal Git adapter.  Tests inject a fake and never launch a subprocess."""

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
            message = completed.stderr.decode("utf-8", "replace").strip()
            raise ValueError(f"git {' '.join(args)} failed: {message}")
        return completed.stdout

    def head(self) -> str:
        return self._run(("rev-parse", "HEAD")).decode("ascii").strip()

    def status(self, paths: Sequence[str]) -> bytes:
        return self._run(("status", "--porcelain=v1", "--untracked-files=all", "--", *paths))

    def blob(self, commit: str, path: str) -> bytes:
        return self._run(("show", f"{commit}:{path}"))

    def tree(self, commit: str, paths: Sequence[str]) -> Mapping[str, tuple[str, str]]:
        raw = self._run(("ls-tree", "-rz", commit, "--", *paths))
        result: dict[str, tuple[str, str]] = {}
        for record in raw.split(b"\0"):
            if not record:
                continue
            metadata, raw_path = record.split(b"\t", 1)
            mode, object_type, object_id = metadata.decode("ascii").split()
            if object_type != "blob":
                continue
            result[raw_path.decode("utf-8", "surrogateescape")] = (mode, object_id)
        return result


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _ok(condition: int, detail: str = "condition satisfied") -> ConditionResult:
    return ConditionResult(condition, True, None, detail)


def _fail(condition: int, code: str, detail: str) -> ConditionResult:
    return ConditionResult(condition, False, code, detail)


def _position_as_offset(position: Any) -> int | None:
    if position is None:
        return 0
    try:
        return int(position)
    except (TypeError, ValueError):
        return None


def evaluate_page(
    page: Any,
    *,
    page_size: int,
    expected_interpreted_query: str | None = None,
    expected_position_in: str | None = None,
    pagination_kind: str | None = None,
    terminal: bool | None = None,
    response_ok: bool = True,
    evidence_complete: bool = True,
) -> tuple[ConditionResult, ...]:
    """Evaluate page-level portions of all six completion conditions.

    Conditions are returned separately so callers cannot accidentally turn a
    reason-specific failure into one undifferentiated boolean.
    """

    if page_size <= 0:
        raise ValueError("page_size must be positive")
    actual_count = _get(page, "actual_count")
    declared_total = _get(page, "declared_total")
    capacity_echo = _get(page, "capacity_echo")
    position_in = _get(page, "position_in")
    position_out = _get(page, "position_out")
    index = _get(page, "index")
    occurrences = tuple(_get(page, "occurrences", ()) or ())
    parse_errors = tuple(_get(page, "parse_errors", ()) or ())
    is_terminal = position_out is None if terminal is None else terminal
    kind = pagination_kind or ("cursor" if index == "openalex" else "offset")

    if (
        expected_interpreted_query is not None
        and _get(page, "interpreted_query") != expected_interpreted_query
    ):
        condition1 = _fail(1, "interpreted_query_mismatch", "index query echo differs from the registered query")
    else:
        condition1 = _ok(1, "interpreted query matches")

    if expected_position_in is not None and position_in != expected_position_in:
        condition2 = _fail(2, "position_mismatch", "page position does not continue the preceding page")
    elif not is_terminal and isinstance(actual_count, int) and actual_count < page_size:
        condition2 = _fail(2, "silent_truncation", "a non-terminal page contains fewer elements than requested")
    elif _get(page, "cursor_parent_matches", True) is False:
        condition2 = _fail(2, "cursor_parent_mismatch", "cursor is not bound to the preceding stored response")
    else:
        condition2 = _ok(2, "page position is continuous")

    if not isinstance(actual_count, int) or actual_count < 0:
        condition3 = _fail(3, "actual_count_invalid", "parser actual_count is not a nonnegative integer")
    elif not isinstance(declared_total, int) or declared_total < 0:
        condition3 = _fail(3, "declared_total_missing", "a stable nonnegative declared total is required")
    elif index in {"arxiv", "openalex"} and capacity_echo != page_size:
        condition3 = _fail(3, "capacity_echo_mismatch", "capacity echo differs from the registered page size")
    elif index == "dblp" and capacity_echo != actual_count:
        condition3 = _fail(3, "capacity_echo_mismatch", "DBLP @sent differs from the parsed hit count")
    elif kind == "offset":
        offset = _position_as_offset(position_in)
        expected_count = None if offset is None else min(page_size, max(declared_total - offset, 0))
        if expected_count is None or actual_count != expected_count:
            condition3 = _fail(
                3,
                "actual_count_mismatch",
                f"offset page has {actual_count} elements; expected {expected_count}",
            )
        else:
            condition3 = _ok(3, "actual element count matches the offset formula")
    elif kind == "cursor":
        valid = actual_count <= page_size if is_terminal else actual_count == page_size
        if not valid:
            condition3 = _fail(
                3,
                "actual_count_mismatch",
                "cursor page actual_count violates terminal/non-terminal cardinality",
            )
        else:
            condition3 = _ok(3, "actual element count matches cursor cardinality")
    else:
        condition3 = _fail(3, "pagination_kind_unknown", f"unsupported pagination kind: {kind!r}")

    if len(occurrences) != actual_count:
        condition4 = _fail(
            4,
            "occurrence_count_mismatch",
            f"stored {len(occurrences)} occurrences for actual_count={actual_count}",
        )
    elif any(not isinstance(_get(item, "index_work_id"), str) or not _get(item, "index_work_id") for item in occurrences):
        condition4 = _fail(4, "index_work_id_missing", "an occurrence lacks its index-specific work ID")
    else:
        # Do not deduplicate here: different IDs with one family key remain two
        # retrieval occurrences and are handled by the later family layer.
        condition4 = _ok(4, f"preserved all {len(occurrences)} occurrences")

    if parse_errors:
        condition6 = _fail(6, "parse_error", "; ".join(str(item) for item in parse_errors))
    elif not response_ok:
        condition6 = _fail(6, "response_not_successful", "transport/status/content requirements failed")
    elif not evidence_complete:
        condition6 = _fail(6, "evidence_incomplete", "required raw response evidence is missing")
    else:
        condition6 = _ok(6, "response terminated normally and evidence is stored")

    return (condition1, condition2, condition3, condition4, condition6)


def _first_failure(results: Iterable[ConditionResult], condition: int) -> ConditionResult | None:
    for result in results:
        if result.condition == condition and not result.passed:
            return result
    return None


def _all_occurrences(pages: Sequence[Any]) -> tuple[Any, ...]:
    return tuple(
        occurrence
        for page in pages
        for occurrence in tuple(_get(page, "occurrences", ()) or ())
    )


def evaluate_leaf(
    pages: Sequence[Any],
    *,
    page_size: int,
    expected_interpreted_query: str | None = None,
    pagination_kind: str | None = None,
    shard_lower: str | None = None,
    shard_upper: str | None = None,
    state: str = "branch_complete",
    second_pass_required: bool = False,
    second_pass_digest_matches: bool | None = None,
) -> tuple[ConditionResult, ...]:
    """Evaluate an executable leaf, including distinct-ID and shard checks."""

    page_results: list[ConditionResult] = []
    previous_out: str | None = None
    for ordinal, page in enumerate(pages):
        expected_position = previous_out if ordinal else None
        results = evaluate_page(
            page,
            page_size=page_size,
            expected_interpreted_query=expected_interpreted_query,
            expected_position_in=expected_position,
            pagination_kind=pagination_kind,
        )
        page_results.extend(results)
        previous_out = _get(page, "position_out")

    combined: list[ConditionResult] = []
    for condition in (1, 2, 3, 4):
        failure = _first_failure(page_results, condition)
        combined.append(failure or _ok(condition, "all pages satisfy this condition"))

    occurrences = _all_occurrences(pages)
    work_ids = {_get(item, "index_work_id") for item in occurrences if _get(item, "index_work_id")}
    declared = [_get(page, "declared_total") for page in pages]
    stable_totals = {item for item in declared if isinstance(item, int)}

    if not pages:
        condition5 = _fail(5, "no_pages", "an executable leaf has no terminal page evidence")
    elif len(stable_totals) != 1 or len(declared) != len([item for item in declared if isinstance(item, int)]):
        condition5 = _fail(5, "declared_total_drift", "page totals are missing or not stable")
    elif len(work_ids) != next(iter(stable_totals)):
        condition5 = _fail(
            5,
            "distinct_work_id_total_mismatch",
            f"{len(work_ids)} distinct work IDs do not equal declared total {next(iter(stable_totals))}",
        )
    else:
        lower = date.fromisoformat(shard_lower) if shard_lower else None
        upper = date.fromisoformat(shard_upper) if shard_upper else None
        outside: list[str] = []
        invalid_dates: list[str] = []
        missing_dates = 0
        for occurrence in occurrences:
            interpreted = _get(occurrence, "interpreted_date")
            if interpreted is None:
                missing_dates += 1
                continue
            try:
                parsed_date = date.fromisoformat(interpreted)
            except (TypeError, ValueError):
                invalid_dates.append(str(_get(occurrence, "index_work_id")))
                continue
            if (lower and parsed_date < lower) or (upper and parsed_date > upper):
                outside.append(str(_get(occurrence, "index_work_id")))
        if invalid_dates:
            condition5 = _fail(
                5,
                "interpreted_date_invalid",
                f"records have invalid interpreted dates: {invalid_dates}",
            )
        elif outside:
            condition5 = _fail(5, "record_outside_shard", f"records outside registered date shard: {outside}")
        elif second_pass_required and second_pass_digest_matches is not True:
            condition5 = _fail(5, "second_pass_digest_mismatch", "required independent-pass digest does not match")
        elif _get(pages[0], "index") == "arxiv" and next(iter(stable_totals)) > 10000:
            condition5 = _fail(5, "result_window_exceeded", "arXiv leaf declared total exceeds 10,000")
        else:
            condition5 = _ok(5, f"distinct IDs match stable total; {missing_dates} records remain for date ruling")
    combined.append(condition5)

    page_condition6 = _first_failure(page_results, 6)
    if state in INCOMPLETE_STATES:
        condition6 = _fail(6, "incomplete_state", f"leaf state {state!r} is false-side")
    elif state not in {"pass_complete", "branch_complete", "terminal"}:
        condition6 = _fail(6, "nonterminal_state", f"leaf state {state!r} is not complete")
    else:
        condition6 = page_condition6 or _ok(6, "all attempts terminated with complete evidence")
    combined.append(condition6)
    return tuple(combined)


def _condition_results(value: Any) -> tuple[ConditionResult, ...]:
    if isinstance(value, Mapping):
        candidate = value.get("condition_results", value.get("results", ()))
    else:
        candidate = getattr(value, "condition_results", getattr(value, "results", ()))
    return tuple(item for item in candidate if isinstance(item, ConditionResult))


def _work_id_set(value: Any) -> set[str]:
    direct = _get(value, "work_ids", _get(value, "distinct_work_ids"))
    if direct is not None:
        return {str(item) for item in direct}
    pages = _get(value, "pages")
    if pages is not None:
        return {
            str(_get(item, "index_work_id"))
            for item in _all_occurrences(tuple(pages))
            if _get(item, "index_work_id")
        }
    if isinstance(value, (set, frozenset)) and all(isinstance(item, str) for item in value):
        return set(value)
    return set()


def evaluate_aggregate(
    leaves: Mapping[str, Any] | Sequence[Any],
    *,
    expected_leaf_ids: Iterable[str] | None = None,
    state: str = "branch_complete",
    second_pass_required: bool = False,
    second_pass_digest_matches: bool | None = None,
) -> tuple[ConditionResult, ...]:
    """Evaluate a sharded aggregate without family-key deduplication."""

    if isinstance(leaves, Mapping):
        items = list(leaves.items())
    else:
        items = [(str(index), value) for index, value in enumerate(leaves)]
    actual_ids = {leaf_id for leaf_id, _ in items}
    expected_ids = set(expected_leaf_ids) if expected_leaf_ids is not None else actual_ids

    combined: list[ConditionResult] = []
    for condition in (1, 2, 3, 4):
        failure: ConditionResult | None = None
        for _, value in items:
            failure = _first_failure(_condition_results(value), condition)
            if failure:
                break
        combined.append(failure or _ok(condition, "all registered leaves satisfy this condition"))

    if not items:
        condition5 = _fail(5, "no_leaves", "a sharded aggregate has no leaf evidence")
    elif actual_ids != expected_ids:
        condition5 = _fail(
            5,
            "leaf_set_mismatch",
            f"missing={sorted(expected_ids - actual_ids)}, extra={sorted(actual_ids - expected_ids)}",
        )
    else:
        seen: set[str] = set()
        duplicate: set[str] = set()
        total = 0
        for _, value in items:
            ids = _work_id_set(value)
            duplicate.update(seen.intersection(ids))
            seen.update(ids)
            total += len(ids)
        if duplicate:
            condition5 = _fail(
                5,
                "leaf_work_id_overlap",
                f"work IDs occur in multiple leaves: {sorted(duplicate)}",
            )
        elif len(seen) != total:
            condition5 = _fail(5, "aggregate_count_mismatch", "aggregate distinct count differs from leaf sum")
        elif second_pass_required and second_pass_digest_matches is not True:
            condition5 = _fail(5, "second_pass_digest_mismatch", "aggregate independent-pass digest differs")
        else:
            condition5 = _ok(5, "leaf work-ID sets are pairwise disjoint and sum exactly")
    combined.append(condition5)

    leaf_failure = next(
        (
            failure
            for _, value in items
            if (failure := _first_failure(_condition_results(value), 6)) is not None
        ),
        None,
    )
    if state in INCOMPLETE_STATES:
        condition6 = _fail(6, "incomplete_state", f"aggregate state {state!r} is false-side")
    elif state not in {"branch_complete", "terminal"}:
        condition6 = _fail(6, "nonterminal_state", f"aggregate state {state!r} is not complete")
    else:
        condition6 = leaf_failure or _ok(6, "all leaves have normal terminal evidence")
    combined.append(condition6)
    return tuple(combined)


def _evaluation_complete(value: Any) -> bool:
    results = _condition_results(value)
    if not results and isinstance(value, (tuple, list)):
        results = tuple(item for item in value if isinstance(item, ConditionResult))
    by_number = {item.condition: item.passed for item in results}
    return set(by_number) == set(range(1, 7)) and all(by_number.values())


def derive_axis_status(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Derive top-level status; never consult a declared ``axis_complete``."""

    leaf_values = bundle.get("leaf_results", ())
    aggregate_values = bundle.get("aggregate_results", ())
    if isinstance(leaf_values, Mapping):
        leaf_values = tuple(leaf_values.values())
    if isinstance(aggregate_values, Mapping):
        aggregate_values = tuple(aggregate_values.values())
    evaluations = tuple(leaf_values) + tuple(aggregate_values)
    states = tuple(bundle.get("states", ())) + tuple(
        state
        for value in evaluations
        if (state := _get(value, "state")) is not None
    )
    retrieval_complete = bool(evaluations) and all(
        _evaluation_complete(item) for item in evaluations
    ) and not any(state in INCOMPLETE_STATES for state in states)

    components = {
        "controls_valid": bundle.get("controls_valid") is True,
        "supplemental_complete": bundle.get("supplemental_complete") is True,
        "sensitivity_complete": bundle.get("sensitivity_complete") is True,
        "classification_complete": bundle.get("classification_complete") is True,
        "family_ledger_complete": bundle.get("family_ledger_complete") is True,
    }
    layers = bundle.get("unimplemented_schema_layers", 1)
    if isinstance(layers, int):
        unimplemented_count = max(layers, 0)
    elif isinstance(layers, (list, tuple, set, frozenset, dict)):
        unimplemented_count = len(layers)
    else:
        unimplemented_count = 1
    axis_complete = retrieval_complete and all(components.values()) and unimplemented_count == 0
    return {
        "retrieval_complete": retrieval_complete,
        **components,
        "unimplemented_schema_layer_count": unimplemented_count,
        "axis_complete": axis_complete,
    }


def _worktree_mode(path: Path) -> str:
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        return "120000"
    if not stat.S_ISREG(mode):
        raise ValueError(f"frozen path is not a regular file or symlink: {path}")
    return "100755" if mode & 0o111 else "100644"


def _worktree_bytes(path: Path) -> bytes:
    if path.is_symlink():
        return os.readlink(path).encode("utf-8", "surrogateescape")
    return path.read_bytes()


def _working_frozen_paths(repo_root: Path, prefixes: Sequence[str]) -> set[str]:
    result: set[str] = set()
    for prefix in prefixes:
        absolute = repo_root / prefix
        if absolute.is_symlink() or absolute.is_file():
            result.add(prefix)
        elif absolute.is_dir():
            for root, dirnames, filenames in os.walk(absolute, followlinks=False):
                root_path = Path(root)
                for dirname in tuple(dirnames):
                    candidate = root_path / dirname
                    if candidate.is_symlink():
                        result.add(candidate.relative_to(repo_root).as_posix())
                        dirnames.remove(dirname)
                for filename in filenames:
                    result.add((root_path / filename).relative_to(repo_root).as_posix())
    return result


def verify_registration(
    registration_commit: str,
    catalog_path: str | os.PathLike[str],
    registration_paths: Sequence[str],
    *,
    repo_root: str | os.PathLike[str] = ".",
    git_backend: GitBackend | None = None,
    frozen_base_commit: str = FROZEN_BASE_COMMIT,
    frozen_paths: Sequence[str] = FROZEN_PREDECESSOR_PATHS,
) -> VerificationResult:
    """Run the four stage-4 registration preflight checks."""

    if len(registration_commit) != 40 or any(ch not in "0123456789abcdef" for ch in registration_commit):
        return VerificationResult(False, "registration_commit_invalid", "commit must be 40 lowercase hex digits")
    root = Path(repo_root).resolve()
    backend = git_backend or SubprocessGit(root)
    try:
        if backend.head() != registration_commit:
            return VerificationResult(False, "head_mismatch", "HEAD is not the registration commit")
        if backend.status(tuple(registration_paths)).strip():
            return VerificationResult(False, "registration_paths_dirty", "a registered path is modified or untracked")

        catalog = Path(catalog_path)
        catalog_absolute = catalog if catalog.is_absolute() else root / catalog
        try:
            catalog_relative = catalog_absolute.resolve().relative_to(root).as_posix()
        except ValueError:
            return VerificationResult(False, "catalog_outside_repo", "catalog path is outside the repository")
        working_catalog = catalog_absolute.read_bytes()
        registered_catalog = backend.blob(registration_commit, catalog_relative)
        if hashlib.sha256(working_catalog).digest() != hashlib.sha256(registered_catalog).digest():
            return VerificationResult(False, "catalog_blob_mismatch", "catalog bytes differ from the registered blob")

        baseline = dict(backend.tree(frozen_base_commit, tuple(frozen_paths)))
        working_paths = _working_frozen_paths(root, tuple(frozen_paths))
        if working_paths != set(baseline):
            return VerificationResult(
                False,
                "frozen_path_set_mismatch",
                f"missing={sorted(set(baseline) - working_paths)}, extra={sorted(working_paths - set(baseline))}",
            )
        for relative, (expected_mode, _object_id) in baseline.items():
            absolute = root / relative
            current = _worktree_bytes(absolute)
            registered = backend.blob(frozen_base_commit, relative)
            if _worktree_mode(absolute) != expected_mode:
                return VerificationResult(False, "frozen_mode_mismatch", relative)
            current_sha = hashlib.sha256(current).hexdigest()
            registered_sha = hashlib.sha256(registered).hexdigest()
            if current != registered or current_sha != registered_sha:
                return VerificationResult(False, "frozen_bytes_mismatch", relative)
    except (OSError, ValueError) as exc:
        return VerificationResult(False, "registration_check_error", str(exc))
    return VerificationResult(True, None, "HEAD, clean paths, catalog blob, and frozen predecessor match")


def _manifest_entries(value: Any) -> dict[str, Mapping[str, Any]]:
    if isinstance(value, Mapping):
        raw_entries = value.get("files", value.get("entries"))
    else:
        raw_entries = None
    result: dict[str, Mapping[str, Any]] = {}
    if isinstance(raw_entries, Mapping):
        for path, metadata in raw_entries.items():
            result[str(path)] = metadata if isinstance(metadata, Mapping) else {"sha256": metadata}
    elif isinstance(raw_entries, list):
        for entry in raw_entries:
            if not isinstance(entry, Mapping) or not isinstance(entry.get("path"), str):
                raise ValueError("manifest contains a malformed file entry")
            if entry["path"] in result:
                raise ValueError(f"manifest contains duplicate path: {entry['path']}")
            result[entry["path"]] = entry
    else:
        raise ValueError("manifest must contain a files/entries collection")
    return result


def verify_bundle(bundle_root: str | os.PathLike[str]) -> VerificationResult:
    """Verify exact-set membership and byte digests without any HTTP access."""

    root = Path(bundle_root)
    manifest_path = root / "manifest.json"
    digest_path = root / "MANIFEST.sha256"
    try:
        manifest_bytes = manifest_path.read_bytes()
        value = json.loads(manifest_bytes)
        entries = _manifest_entries(value)
        regular: set[str] = set()
        for current_root, dirnames, filenames in os.walk(root, followlinks=False):
            current = Path(current_root)
            if any((current / name).is_symlink() for name in dirnames):
                return VerificationResult(False, "bundle_symlink", "bundle contains a symlinked directory")
            for filename in filenames:
                path = current / filename
                if path.is_symlink() or not path.is_file():
                    return VerificationResult(False, "bundle_nonregular_file", path.relative_to(root).as_posix())
                regular.add(path.relative_to(root).as_posix())
        expected = regular - {"manifest.json", "MANIFEST.sha256", "README.md"}
        if set(entries) != expected:
            return VerificationResult(
                False,
                "manifest_path_set_mismatch",
                f"missing={sorted(expected - set(entries))}, extra={sorted(set(entries) - expected)}",
            )
        for relative, metadata in entries.items():
            candidate = Path(relative)
            if candidate.is_absolute() or ".." in candidate.parts or candidate.as_posix() != relative:
                return VerificationResult(False, "manifest_path_unsafe", relative)
            raw = (root / candidate).read_bytes()
            if metadata.get("sha256") != hashlib.sha256(raw).hexdigest():
                return VerificationResult(False, "manifest_digest_mismatch", relative)
            if "bytes" in metadata and metadata["bytes"] != len(raw):
                return VerificationResult(False, "manifest_size_mismatch", relative)
        recorded_digest = digest_path.read_text(encoding="ascii").strip().split()[0]
        if recorded_digest != hashlib.sha256(manifest_bytes).hexdigest():
            return VerificationResult(False, "manifest_self_digest_mismatch", "MANIFEST.sha256 is stale")
    except (OSError, ValueError, json.JSONDecodeError, IndexError) as exc:
        return VerificationResult(False, "bundle_check_error", str(exc))
    return VerificationResult(True, None, "bundle manifest exact-set and all digests match")


__all__ = [
    "ConditionResult",
    "FROZEN_BASE_COMMIT",
    "FROZEN_PREDECESSOR_PATHS",
    "GitBackend",
    "INCOMPLETE_STATES",
    "SubprocessGit",
    "VerificationResult",
    "derive_axis_status",
    "evaluate_aggregate",
    "evaluate_leaf",
    "evaluate_page",
    "verify_bundle",
    "verify_registration",
]
