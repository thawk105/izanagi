"""Independent validation for the axis-1 search evidence contract."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
from typing import Any, Protocol
from urllib.parse import unquote


FROZEN_BASE_COMMIT = "164e2c355"
FROZEN_PREDECESSOR_PATHS = (
    "docs/related-work/claim-survey/2026-08-27-axis1-search-preregistration.md",
    "docs/related-work/claim-survey/2026-08-27-axis1-search-execution.md",
    "output/insights/2026-08-27_t1969-axis1-search-execution",
)
INCOMPLETE_STATES = frozenset(
    {"not_run", "not_started", "paused_quota", "outcome_unknown", "blocked_on_ruling"}
)
AXIS1_UNIMPLEMENTED_SCHEMA_LAYERS = (
    "classification",
    "work_family_ledger",
    "controls",
    "supplemental_search",
    "sensitivity_audit",
)
MAX_STORED_PAGE_BYTES = 16 * 1024 * 1024
_COMPLETE_STATES = frozenset({"pass_complete", "branch_complete", "terminal"})
_UNSET = object()


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
    status: Mapping[str, Any] | None = None


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
        raw = self._run(("ls-tree", "-r", "-z", commit, "--", *paths))
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


def normalize_interpreted_query(index: str, value: str) -> str:
    """Apply only the three registered textual echo normalizations.

    OpenAlex does not use this function for acceptance; its structured ``oqo``
    object is compared instead.  URL decoding is deliberately performed once,
    then whitespace is collapsed.  For arXiv only, the brackets/quotes around a
    ``submittedDate`` range are canonicalized without changing the range body.
    """

    if not isinstance(value, str):
        raise TypeError("interpreted query must be a string")
    normalized = " ".join(unquote(value).split())
    if index == "arxiv":
        import re

        normalized = re.sub(
            r"submittedDate\s*:\s*(?:\[|\"|\()\s*([^\]\"\)]+?)\s*(?:\]|\"|\))",
            lambda match: f"submittedDate:[{' '.join(match.group(1).split())}]",
            normalized,
        )
    return normalized


def evaluate_page(
    page: Any,
    *,
    page_size: int,
    expected_interpreted_query: str | None = None,
    expected_interpreted_structure: Any = _UNSET,
    actual_interpreted_structure: Any = _UNSET,
    expected_position_in: Any = _UNSET,
    expected_page_number: int | None = None,
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

    if index == "openalex" and expected_interpreted_structure is not _UNSET:
        actual_structure = (
            _get(page, "interpreted_query_structure")
            if actual_interpreted_structure is _UNSET
            else actual_interpreted_structure
        )
        query_matches = actual_structure == expected_interpreted_structure
    elif expected_interpreted_query is not None:
        try:
            query_matches = normalize_interpreted_query(
                str(index), str(_get(page, "interpreted_query"))
            ) == normalize_interpreted_query(str(index), expected_interpreted_query)
        except (TypeError, ValueError):
            query_matches = False
    else:
        query_matches = True
    if not query_matches:
        condition1 = _fail(1, "interpreted_query_mismatch", "index query echo differs from the registered query")
    else:
        condition1 = _ok(1, "interpreted query matches")

    if expected_position_in is not _UNSET and position_in != expected_position_in:
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

    expected_page = expected_page_number
    if expected_page is None and occurrences:
        candidate_page = _get(occurrences[0], "page_number")
        expected_page = candidate_page if isinstance(candidate_page, int) else None
    expected_coordinates = (
        [(expected_page, ordinal) for ordinal in range(actual_count)]
        if isinstance(actual_count, int) and actual_count >= 0 and expected_page is not None
        else None
    )
    actual_coordinates = [
        (_get(item, "page_number"), _get(item, "ordinal")) for item in occurrences
    ]

    def date_row_is_legal(item: Any) -> bool:
        raw = _get(item, "raw_date_value")
        interpreted = _get(item, "interpreted_date")
        missing = _get(item, "date_missing_reason")
        if raw is not None and not isinstance(raw, str):
            return False
        if interpreted is None:
            return isinstance(missing, str) and bool(missing)
        if missing is not None or not isinstance(interpreted, str) or not isinstance(raw, str) or not raw:
            return False
        try:
            date.fromisoformat(interpreted)
        except ValueError:
            return False
        return True

    if len(occurrences) != actual_count:
        condition4 = _fail(
            4,
            "occurrence_count_mismatch",
            f"stored {len(occurrences)} occurrences for actual_count={actual_count}",
        )
    elif any(not isinstance(_get(item, "index_work_id"), str) or not _get(item, "index_work_id") for item in occurrences):
        condition4 = _fail(4, "index_work_id_missing", "an occurrence lacks its index-specific work ID")
    elif expected_coordinates is not None and actual_coordinates != expected_coordinates:
        condition4 = _fail(
            4,
            "occurrence_coordinate_mismatch",
            f"stored coordinates {actual_coordinates!r} do not equal {expected_coordinates!r}",
        )
    elif any(not date_row_is_legal(item) for item in occurrences):
        condition4 = _fail(
            4,
            "occurrence_date_matrix_invalid",
            "raw/interpreted/missing-reason fields violate the registered matrix",
        )
    else:
        # Do not deduplicate here: different IDs with one family key remain two
        # retrieval occurrences and are handled by the later family layer.
        condition4 = _ok(4, f"preserved all {len(occurrences)} occurrences")

    condition5 = _ok(
        5,
        "page contribution retained for leaf-wide distinct-ID, shard, and independent-pass evaluation",
    )

    if parse_errors:
        condition6 = _fail(6, "parse_error", "; ".join(str(item) for item in parse_errors))
    elif not response_ok:
        condition6 = _fail(6, "response_not_successful", "transport/status/content requirements failed")
    elif not evidence_complete:
        condition6 = _fail(6, "evidence_incomplete", "required raw response evidence is missing")
    else:
        condition6 = _ok(6, "response terminated normally and evidence is stored")

    return (condition1, condition2, condition3, condition4, condition5, condition6)


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
    page_contexts: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[ConditionResult, ...]:
    """Evaluate an executable leaf, including distinct-ID and shard checks."""

    page_results: list[ConditionResult] = []
    previous_out: str | None = None
    if page_contexts is not None and len(page_contexts) != len(pages):
        raise ValueError("page_contexts must have one entry per page")
    for ordinal, page in enumerate(pages):
        expected_position = previous_out if ordinal else None
        context = dict(page_contexts[ordinal]) if page_contexts is not None else {}
        if page_contexts is not None or ordinal:
            context.setdefault("expected_position_in", expected_position)
        context.setdefault("expected_page_number", ordinal)
        context.setdefault("pagination_kind", pagination_kind)
        if expected_interpreted_query is not None:
            context.setdefault("expected_interpreted_query", expected_interpreted_query)
        results = evaluate_page(
            page,
            page_size=page_size,
            **context,
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
        leaf_total_failure: str | None = None
        for leaf_id, value in items:
            ids = _work_id_set(value)
            declared_leaf_total = _get(value, "declared_total", len(ids))
            if declared_leaf_total != len(ids):
                leaf_total_failure = (
                    f"{leaf_id} has {len(ids)} distinct IDs but declares {declared_leaf_total}"
                )
            duplicate.update(seen.intersection(ids))
            seen.update(ids)
        if leaf_total_failure is not None:
            condition5 = _fail(5, "aggregate_count_mismatch", leaf_total_failure)
        elif duplicate:
            condition5 = _fail(
                5,
                "leaf_work_id_overlap",
                f"work IDs occur in multiple leaves: {sorted(duplicate)}",
            )
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


def _identity_result_map(value: Any, prefix: str) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {f"{prefix}{ordinal}": item for ordinal, item in enumerate(tuple(value or ()))}


def derive_axis_status(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Derive top-level status; never consult a declared ``axis_complete``."""

    leaf_map = _identity_result_map(bundle.get("leaf_results", ()), "leaf-")
    aggregate_map = _identity_result_map(bundle.get("aggregate_results", ()), "aggregate-")
    evaluations = tuple(leaf_map.values()) + tuple(aggregate_map.values())
    expected_leaf_ids_raw = bundle.get("expected_leaf_ids")
    expected_aggregate_ids_raw = bundle.get("expected_aggregate_ids")
    exact_identity = True
    if expected_leaf_ids_raw is not None:
        exact_identity = set(leaf_map) == {str(item) for item in expected_leaf_ids_raw}
    if expected_aggregate_ids_raw is not None:
        exact_identity = exact_identity and set(aggregate_map) == {
            str(item) for item in expected_aggregate_ids_raw
        }

    states_value = bundle.get("states", ())
    if isinstance(states_value, Mapping):
        state_map = {str(key): value for key, value in states_value.items()}
        expected_state_ids = bundle.get("expected_state_ids")
        if expected_state_ids is not None:
            exact_identity = exact_identity and set(state_map) == {
                str(item) for item in expected_state_ids
            }
        allowed_not_applicable = {
            str(item) for item in bundle.get("allowed_not_applicable_ids", ())
        }
        states_legal = all(
            state in _COMPLETE_STATES
            or (state == "not_applicable" and identity in allowed_not_applicable)
            for identity, state in state_map.items()
        )
    else:
        state_sequence = tuple(states_value or ())
        state_map = {f"state-{ordinal}": state for ordinal, state in enumerate(state_sequence)}
        states_legal = not any(state in INCOMPLETE_STATES for state in state_sequence)
    for identity, value in {**leaf_map, **aggregate_map}.items():
        embedded = _get(value, "state")
        if embedded is not None:
            state_map.setdefault(identity, embedded)
            states_legal = states_legal and embedded in _COMPLETE_STATES

    retrieval_complete = (
        bool(evaluations)
        and exact_identity
        and states_legal
        and all(_evaluation_complete(item) for item in evaluations)
    )

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
        "exact_identity_map": exact_identity,
        "states_legal": states_legal,
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
        registered_tree = dict(backend.tree(registration_commit, tuple(frozen_paths)))
        if registered_tree != baseline:
            baseline_paths = set(baseline)
            registered_paths = set(registered_tree)
            changed_paths = sorted(
                path
                for path in baseline_paths & registered_paths
                if baseline[path] != registered_tree[path]
            )
            return VerificationResult(
                False,
                "frozen_registration_tree_mismatch",
                (
                    f"missing={sorted(baseline_paths - registered_paths)}, "
                    f"extra={sorted(registered_paths - baseline_paths)}, "
                    f"changed={changed_paths}"
                ),
            )
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
    if isinstance(raw_entries, list):
        for entry in raw_entries:
            if not isinstance(entry, Mapping) or not isinstance(entry.get("path"), str):
                raise ValueError("manifest contains a malformed file entry")
            if entry["path"] in result:
                raise ValueError(f"manifest contains duplicate path: {entry['path']}")
            result[entry["path"]] = entry
    else:
        raise ValueError("manifest must contain a files/entries collection")
    return result


def _safe_bundle_relative(value: Any) -> Path:
    if not isinstance(value, str):
        raise ValueError("bundle path must be a string")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts or candidate.as_posix() != value:
        raise ValueError(f"unsafe bundle path: {value!r}")
    return candidate


def _schema_error(schema: Mapping[str, Any], value: Any) -> str | None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - repository test env provides it
        raise ValueError("jsonschema is required for bundle verification") from exc
    validator = jsonschema.Draft7Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    if not errors:
        return None
    error = errors[0]
    location = "/".join(str(item) for item in error.absolute_path) or "<root>"
    return f"{location}: {error.message}"


def _parser_for_index(index: str) -> Any:
    from .parsers import parse_arxiv_page, parse_dblp_page, parse_openalex_page

    return {
        "arxiv": parse_arxiv_page,
        "openalex": parse_openalex_page,
        "dblp": parse_dblp_page,
    }[index]


def _parse_stored_page(parser: Any, body: bytes, page_number: int) -> Any:
    try:
        return parser(body, page_number)
    except TypeError as exc:
        try:
            return parser(body)
        except TypeError:
            raise exc


def _logical_query(catalog: Any, query_id: str) -> Any:
    resolver = _get(catalog, "logical_query")
    if callable(resolver):
        return resolver(query_id)
    for query in tuple(_get(catalog, "logical_queries", ()) or ()):
        if _get(query, "query_id") == query_id:
            return query
    raise ValueError(f"catalog lacks logical query {query_id!r}")


def _expected_openalex_structure(query: Any) -> Any:
    marker = object()
    for field in (
        "expected_interpreted_query_structure",
        "expected_x_query_oqo",
        "expected_oqo",
    ):
        value = _get(query, field, marker)
        if value is not marker:
            return value
    raise ValueError("OpenAlex logical query lacks structured echo expectation")


def _openalex_structure(body: bytes) -> Any:
    try:
        value = json.loads(body)
        return value["meta"]["x_query"]["oqo"]
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, KeyError):
        return None


def _registered_content_types(catalog: Any, index: str) -> frozenset[str]:
    policy = _get(catalog, "index_policies")[index]
    raw = _get(policy, "content_types")
    if not isinstance(raw, (list, tuple)) or not raw:
        raise ValueError(f"catalog index policy {index!r} lacks registered content_types")
    values = frozenset(
        item.strip().lower() for item in raw if isinstance(item, str) and item.strip()
    )
    if len(values) != len(raw):
        raise ValueError(f"catalog index policy {index!r} has invalid content_types")
    return values


def _occurrence_counter(rows: Iterable[Mapping[str, Any]]) -> Counter[str]:
    return Counter(
        json.dumps(dict(row), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for row in rows
    )


def _read_stored_raw(path: Path) -> bytes:
    with gzip.open(path, "rb") as handle:
        body = handle.read(MAX_STORED_PAGE_BYTES + 1)
    if len(body) > MAX_STORED_PAGE_BYTES:
        raise ValueError("stored raw response exceeds the 16 MiB limit")
    return body


def _page_from_evidence(
    evidence: Mapping[str, Any], ledger: Mapping[str, Any]
) -> dict[str, Any]:
    identity = evidence["identity"]
    page_number = identity["page_number"]
    parsed = dict(evidence["parse"])
    parsed.update(
        {
            "index": identity["index"],
            "occurrences": tuple(
                dict(item)
                for item in ledger["occurrences"]
                if item.get("page_number") == page_number
            ),
        }
    )
    return parsed


def _completion_claims(value: Any) -> dict[int, tuple[bool | None, str | None]]:
    claims: dict[int, tuple[bool | None, str | None]] = {}
    if isinstance(value, list):
        for ordinal, item in enumerate(value, 1):
            if isinstance(item, bool):
                claims[ordinal] = (item, None)
            elif isinstance(item, Mapping):
                number = item.get(
                    "condition", item.get("condition_number", item.get("number", ordinal))
                )
                passed = item.get("passed")
                if passed is None and item.get("status") in {"passed", "failed"}:
                    passed = item["status"] == "passed"
                if isinstance(number, int) and isinstance(passed, bool):
                    claims[number] = (passed, item.get("reason_code"))
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if key in {"conditions", "condition_results", "results"}:
                claims.update(_completion_claims(item))
                continue
            import re

            match = re.search(r"([1-6])$", str(key))
            if not match:
                continue
            number = int(match.group(1))
            if isinstance(item, bool):
                claims[number] = (item, None)
            elif isinstance(item, Mapping):
                passed = item.get("passed")
                if passed is None and item.get("status") in {"passed", "failed"}:
                    passed = item["status"] == "passed"
                if isinstance(passed, bool):
                    claims[number] = (passed, item.get("reason_code"))
    return claims


def _production_axis_status(
    *,
    catalog: Any,
    leaf_results: Mapping[str, Any],
    aggregate_results: Mapping[str, Any],
    states: Mapping[str, str],
    declared_bundle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    # Kept as an explicit parameter so tests can prove declarations are ignored.
    del declared_bundle
    queries = tuple(_get(catalog, "logical_queries", ()) or ())
    expected_leaf_ids = {
        str(_get(query, "query_id")) for query in queries if _get(query, "kind") == "leaf"
    }
    expected_aggregate_ids = {
        str(_get(query, "query_id"))
        for query in queries
        if _get(query, "kind") == "aggregate"
    }
    exclusions = {
        str(_get(query, "query_id"))
        for query in queries
        if _get(query, "kind") == "exclusion"
    }
    return derive_axis_status(
        {
            "leaf_results": dict(leaf_results),
            "aggregate_results": dict(aggregate_results),
            "expected_leaf_ids": expected_leaf_ids,
            "expected_aggregate_ids": expected_aggregate_ids,
            "states": dict(states),
            "expected_state_ids": {
                str(_get(query, "query_id")) for query in queries
            },
            "allowed_not_applicable_ids": exclusions,
            # These are implementation facts.  No bundle declaration is read.
            "controls_valid": False,
            "supplemental_complete": False,
            "sensitivity_complete": False,
            "classification_complete": False,
            "family_ledger_complete": False,
            "unimplemented_schema_layers": AXIS1_UNIMPLEMENTED_SCHEMA_LAYERS,
        }
    )


def verify_bundle(
    bundle_root: str | os.PathLike[str],
    *,
    catalog: Any | None = None,
    catalog_path: str | os.PathLike[str] | None = None,
    page_schema_path: str | os.PathLike[str] | None = None,
    checkpoint_schema_path: str | os.PathLike[str] | None = None,
) -> VerificationResult:
    """Recompute the complete offline evidence gate without HTTP access."""

    root = Path(bundle_root)
    repo_root = Path(__file__).resolve().parents[2]
    registered_catalog_path = Path(catalog_path) if catalog_path is not None else (
        repo_root
        / "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json"
    )
    page_schema_file = Path(page_schema_path) if page_schema_path is not None else (
        repo_root / "orchestrator/schemas/axis1_search_page_evidence.schema.json"
    )
    checkpoint_schema_file = (
        Path(checkpoint_schema_path)
        if checkpoint_schema_path is not None
        else repo_root / "orchestrator/schemas/axis1_search_checkpoint.schema.json"
    )
    manifest_path = root / "manifest.json"
    digest_path = root / "MANIFEST.sha256"
    try:
        if catalog is None:
            from .catalog import load_catalog

            catalog = load_catalog(os.fspath(registered_catalog_path))
        catalog_sha = hashlib.sha256(registered_catalog_path.read_bytes()).hexdigest()
        page_schema = json.loads(page_schema_file.read_text(encoding="utf-8"))
        checkpoint_schema = json.loads(checkpoint_schema_file.read_text(encoding="utf-8"))
        manifest_bytes = manifest_path.read_bytes()
        value = json.loads(manifest_bytes)
        error = _schema_error(page_schema, value)
        if error:
            return VerificationResult(False, "manifest_schema_invalid", error)
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
        if set(entries) != expected or set(value.get("regular_file_paths", ())) != expected:
            return VerificationResult(
                False,
                "manifest_path_set_mismatch",
                f"missing={sorted(expected - set(entries))}, extra={sorted(set(entries) - expected)}",
            )
        for relative, metadata in entries.items():
            candidate = _safe_bundle_relative(relative)
            raw = (root / candidate).read_bytes()
            if metadata.get("sha256") != hashlib.sha256(raw).hexdigest():
                return VerificationResult(False, "manifest_digest_mismatch", relative)
            if "bytes" in metadata and metadata["bytes"] != len(raw):
                return VerificationResult(False, "manifest_size_mismatch", relative)
        recorded_digest = digest_path.read_text(encoding="ascii").strip().split()[0]
        if recorded_digest != hashlib.sha256(manifest_bytes).hexdigest():
            return VerificationResult(False, "manifest_self_digest_mismatch", "MANIFEST.sha256 is stale")

        documents: dict[str, Mapping[str, Any]] = {}
        ledgers: dict[str, Mapping[str, Any]] = {}
        pages: list[Mapping[str, Any]] = []
        for relative in sorted(entries):
            if relative.endswith(".jsonl"):
                if not relative.startswith("wal/"):
                    return VerificationResult(False, "unregistered_jsonl_document", relative)
                from .checkpoint import recover_attempts

                recover_attempts(root / relative)
                continue
            if relative.endswith(".gz"):
                if not relative.startswith("raw/"):
                    return VerificationResult(False, "unregistered_gzip_document", relative)
                continue
            if not relative.endswith(".json"):
                return VerificationResult(False, "unregistered_bundle_file", relative)
            document = json.loads((root / relative).read_text(encoding="utf-8"))
            if not isinstance(document, Mapping):
                return VerificationResult(False, "document_not_object", relative)
            document_type = document.get("document_type")
            if document_type in {"page_evidence", "record_occurrence_ledger"}:
                error = _schema_error(page_schema, document)
                if error:
                    return VerificationResult(False, "document_schema_invalid", f"{relative}: {error}")
                if document_type == "page_evidence":
                    pages.append(document)
                else:
                    ledgers[relative] = document
            elif relative.startswith("checkpoints/"):
                error = _schema_error(checkpoint_schema, document)
                if error:
                    return VerificationResult(False, "checkpoint_schema_invalid", f"{relative}: {error}")
                from .checkpoint import validate_checkpoint

                validate_checkpoint(document)
            elif relative == "state/runtime.json":
                if document.get("schema_version") != "izanagi-axis1-search-runtime-state/v1":
                    return VerificationResult(False, "runtime_state_invalid", relative)
            else:
                return VerificationResult(False, "unregistered_json_document", relative)
            documents[relative] = document

        referenced_raw = {
            str(evidence["response"]["body_path"]) for evidence in pages
        }
        stored_raw = {
            relative for relative in entries if relative.startswith("raw/") and relative.endswith(".gz")
        }
        if referenced_raw != stored_raw:
            return VerificationResult(
                False,
                "raw_path_set_mismatch",
                f"missing={sorted(referenced_raw - stored_raw)}, extra={sorted(stored_raw - referenced_raw)}",
            )

        from .catalog import build_request

        accepted_pages: dict[tuple[str, int], list[tuple[Mapping[str, Any], Any, dict[str, Any]]]] = {}
        seen_request_ids: set[tuple[str, int, str]] = set()
        seen_page_identities: set[tuple[str, int, int]] = set()
        for evidence in pages:
            identity = evidence["identity"]
            request_id = identity["request_id"]
            request_identity = (
                identity["leaf_query_id"], identity["pass_number"], request_id
            )
            page_identity = (
                identity["leaf_query_id"],
                identity["pass_number"],
                identity["page_number"],
            )
            if (
                request_identity in seen_request_ids
                or page_identity in seen_page_identities
            ):
                return VerificationResult(
                    False, "duplicate_page_evidence", request_id
                )
            seen_request_ids.add(request_identity)
            seen_page_identities.add(page_identity)
            if identity["catalog_sha256"] != catalog_sha:
                return VerificationResult(False, "catalog_digest_mismatch", identity["request_id"])
            ledger_relative = evidence["records"]["occurrence_ledger_path"]
            ledger = ledgers.get(ledger_relative)
            if ledger is None:
                return VerificationResult(False, "occurrence_ledger_missing", ledger_relative)
            raw_relative = _safe_bundle_relative(evidence["response"]["body_path"])
            try:
                body = _read_stored_raw(root / raw_relative)
            except gzip.BadGzipFile:
                return VerificationResult(False, "raw_gzip_invalid", raw_relative.as_posix())
            response_doc = evidence["response"]
            if (
                hashlib.sha256(body).hexdigest() != response_doc["sha256"]
                or len(body) != response_doc["byte_count"]
            ):
                return VerificationResult(False, "raw_body_digest_mismatch", raw_relative.as_posix())
            request = build_request(
                catalog,
                identity["leaf_query_id"],
                identity["page_number"],
                evidence["request"]["position_in"],
            )
            request_fields = {
                "method": _get(request, "method"),
                "scheme": _get(request, "scheme"),
                "host": _get(request, "host"),
                "path": _get(request, "path"),
                "query_parameters": [list(item) for item in _get(request, "query_parameters")],
                "encoded_url": _get(request, "encoded_url"),
                "headers": [list(item) for item in _get(request, "headers")],
                "timeout_s": _get(request, "timeout_s"),
                "position_in": _get(request, "position_in"),
                "expected_interpreted_query": _get(request, "expected_interpreted_query"),
            }
            if any(evidence["request"].get(key) != expected_value for key, expected_value in request_fields.items()):
                return VerificationResult(False, "request_registration_mismatch", identity["request_id"])
            parsed = _parse_stored_page(
                _parser_for_index(identity["index"]), body, identity["page_number"]
            )
            if evidence.get("failure") is not None:
                continue
            parsed_fields = {
                "interpreted_query": _get(parsed, "interpreted_query"),
                "declared_total": _get(parsed, "declared_total"),
                "capacity_echo": _get(parsed, "capacity_echo"),
                "actual_count": _get(parsed, "actual_count"),
                "position_in": _get(parsed, "position_in"),
                "position_out": _get(parsed, "position_out"),
                "parse_errors": list(tuple(_get(parsed, "parse_errors", ()) or ())),
            }
            if evidence["parse"] != parsed_fields:
                return VerificationResult(False, "stored_parse_mismatch", identity["request_id"])
            parsed_occurrences = [
                {
                    key: _get(item, key)
                    for key in (
                        "index_work_id",
                        "page_number",
                        "ordinal",
                        "raw_date_value",
                        "interpreted_date",
                        "date_missing_reason",
                        "family_keys",
                    )
                }
                for item in tuple(_get(parsed, "occurrences", ()) or ())
            ]
            ledger_occurrences = [
                dict(item)
                for item in ledger["occurrences"]
                if item["page_number"] == identity["page_number"]
            ]
            for item in parsed_occurrences:
                item["family_keys"] = list(item["family_keys"])
            if parsed_occurrences != ledger_occurrences:
                return VerificationResult(False, "stored_occurrence_mismatch", identity["request_id"])
            page = _page_from_evidence(evidence, ledger)
            expected_types = _registered_content_types(catalog, identity["index"])
            context: dict[str, Any] = {
                "expected_interpreted_query": _get(request, "expected_interpreted_query"),
                "expected_position_in": _get(request, "position_in"),
                "expected_page_number": identity["page_number"],
                "pagination_kind": (
                    "cursor" if identity["index"] == "openalex" else "offset"
                ),
                "response_ok": (
                    response_doc["status"] == 200
                    and response_doc["content_type"].split(";", 1)[0].strip().lower()
                    in expected_types
                    and response_doc["final_url"] == _get(request, "encoded_url")
                ),
                "evidence_complete": True,
            }
            if identity["index"] == "openalex":
                context["expected_interpreted_structure"] = _expected_openalex_structure(
                    _logical_query(catalog, identity["leaf_query_id"])
                )
                context["actual_interpreted_structure"] = _openalex_structure(body)
            results = evaluate_page(page, page_size=int(_get(_get(catalog, "index_policies")[identity["index"]], "page_size")), **context)
            completion = evidence.get("completion")
            if completion is not None:
                claims = _completion_claims(completion)
                expected_claims = {
                    item.condition: (item.passed, item.reason_code) for item in results
                }
                if claims != expected_claims:
                    return VerificationResult(
                        False, "stored_completion_mismatch", identity["request_id"]
                    )
            if evidence.get("failure") is None and not all(item.passed for item in results):
                failure = next(item for item in results if not item.passed)
                return VerificationResult(False, failure.reason_code, identity["request_id"])
            accepted_pages.setdefault(
                (identity["leaf_query_id"], identity["pass_number"]), []
            ).append((evidence, page, context))

        queries = tuple(_get(catalog, "logical_queries", ()) or ())
        leaves = [query for query in queries if _get(query, "kind") == "leaf"]
        aggregates = [query for query in queries if _get(query, "kind") == "aggregate"]
        leaf_results: dict[str, Any] = {}
        states: dict[str, str] = {
            str(_get(query, "query_id")): "not_applicable"
            for query in queries
            if _get(query, "kind") == "exclusion"
        }
        for query in leaves:
            leaf_id = str(_get(query, "query_id"))
            registered_required = _get(query, "independent_pass_required")
            if not isinstance(registered_required, bool):
                return VerificationResult(False, "independent_pass_registration_missing", leaf_id)
            pass_numbers = (1, 2) if registered_required else (1,)
            pass_evaluations: list[tuple[ConditionResult, ...]] = []
            pass_digests: list[str] = []
            final_work_ids: set[str] = set()
            for pass_number in pass_numbers:
                values = accepted_pages.get((leaf_id, pass_number), [])
                if not values:
                    return VerificationResult(False, "leaf_page_evidence_missing", f"{leaf_id}:pass{pass_number}")
                values.sort(key=lambda item: item[0]["identity"]["page_number"])
                page_numbers = [
                    item[0]["identity"]["page_number"] for item in values
                ]
                if page_numbers != list(range(len(values))):
                    return VerificationResult(
                        False,
                        "page_chain_number_mismatch",
                        f"{leaf_id}:pass{pass_number}:{page_numbers}",
                    )
                if values[0][0]["request"].get("parent_response_sha256") is not None:
                    return VerificationResult(
                        False,
                        "page_chain_parent_digest_mismatch",
                        f"{leaf_id}:pass{pass_number}:page0",
                    )
                for previous, current in zip(values, values[1:]):
                    previous_evidence, previous_page, _previous_context = previous
                    current_evidence, current_page, _current_context = current
                    if (
                        _get(previous_page, "position_out") is None
                        or _get(previous_page, "position_out")
                        != _get(current_page, "position_in")
                    ):
                        return VerificationResult(
                            False,
                            "page_chain_position_mismatch",
                            current_evidence["identity"]["request_id"],
                        )
                    if (
                        current_evidence["request"].get("parent_response_sha256")
                        != previous_evidence["response"]["sha256"]
                    ):
                        return VerificationResult(
                            False,
                            "page_chain_parent_digest_mismatch",
                            current_evidence["identity"]["request_id"],
                        )
                page_values = [item[1] for item in values]
                contexts = [item[2] for item in values]
                final_ledger = ledgers[values[-1][0]["records"]["occurrence_ledger_path"]]
                reparsed_occurrences = [
                    dict(occurrence)
                    for page in page_values
                    for occurrence in tuple(_get(page, "occurrences", ()) or ())
                ]
                final_ledger_occurrences = [
                    dict(item) for item in final_ledger["occurrences"]
                ]
                reparsed_counter = _occurrence_counter(reparsed_occurrences)
                ledger_counter = _occurrence_counter(final_ledger_occurrences)
                extra_rows = ledger_counter - reparsed_counter
                missing_rows = reparsed_counter - ledger_counter
                if extra_rows and not missing_rows:
                    return VerificationResult(
                        False,
                        "occurrence_ledger_extra_row",
                        f"{leaf_id}:pass{pass_number}",
                    )
                if missing_rows and not extra_rows:
                    return VerificationResult(
                        False,
                        "occurrence_ledger_missing_row",
                        f"{leaf_id}:pass{pass_number}",
                    )
                if extra_rows or missing_rows:
                    return VerificationResult(
                        False,
                        "occurrence_ledger_row_mismatch",
                        f"{leaf_id}:pass{pass_number}",
                    )
                work_ids = {
                    str(item["index_work_id"])
                    for item in final_ledger["occurrences"]
                    if item.get("index_work_id")
                }
                digest = hashlib.sha256(
                    "".join(f"{item}\n" for item in sorted(work_ids)).encode("utf-8")
                ).hexdigest()
                pass_digests.append(digest)
                final_work_ids = work_ids
                evaluation = evaluate_leaf(
                    page_values,
                    page_size=int(_get(_get(catalog, "index_policies")[_get(query, "index")], "page_size")),
                    pagination_kind=("cursor" if _get(query, "index") == "openalex" else "offset"),
                    shard_lower=_get(query, "shard_lower"),
                    shard_upper=_get(query, "shard_upper"),
                    state="branch_complete",
                    second_pass_required=registered_required and pass_number == 2,
                    second_pass_digest_matches=(
                        pass_digests[0] == digest if pass_number == 2 else None
                    ),
                    page_contexts=contexts,
                )
                pass_evaluations.append(evaluation)
            final_evaluation = pass_evaluations[-1]
            leaf_results[leaf_id] = {
                "condition_results": final_evaluation,
                "work_ids": final_work_ids,
                "state": "branch_complete" if all(item.passed for item in final_evaluation) else "blocked_on_ruling",
            }
            states[leaf_id] = leaf_results[leaf_id]["state"]

        aggregate_results: dict[str, Any] = {}
        for aggregate in aggregates:
            aggregate_id = str(_get(aggregate, "query_id"))
            child_ids = {
                str(_get(query, "query_id"))
                for query in leaves
                if _get(query, "parent_id") == aggregate_id
            }
            evaluation = evaluate_aggregate(
                {child: leaf_results[child] for child in child_ids},
                expected_leaf_ids=child_ids,
                state="branch_complete",
            )
            aggregate_results[aggregate_id] = {
                "condition_results": evaluation,
                "state": "branch_complete" if all(item.passed for item in evaluation) else "blocked_on_ruling",
            }
            states[aggregate_id] = aggregate_results[aggregate_id]["state"]

        status = _production_axis_status(
            catalog=catalog,
            leaf_results=leaf_results,
            aggregate_results=aggregate_results,
            states=states,
        )
        if not status["retrieval_complete"]:
            return VerificationResult(False, "retrieval_incomplete", "exact leaf/aggregate gate is false", status)
    except (OSError, ValueError, json.JSONDecodeError, IndexError, KeyError, TypeError) as exc:
        return VerificationResult(False, "bundle_check_error", str(exc))
    return VerificationResult(
        True,
        None,
        "bundle schemas, raw reparse, six conditions, leaves, aggregates, and exact status map pass",
        status,
    )


__all__ = [
    "AXIS1_UNIMPLEMENTED_SCHEMA_LAYERS",
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
    "normalize_interpreted_query",
    "verify_bundle",
    "verify_registration",
]
