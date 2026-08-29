"""Registered axis-1 retrieval runner.

All mutable dependencies (transport, clock, sleeper, request builder, parser)
are injectable.  The production transport is deliberately small and rejects
redirects, non-HTTPS URLs, and hosts outside the registered allow-list.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Protocol
from urllib import error, request as urllib_request
from urllib.parse import urlsplit

from .checkpoint import append_attempt_state, load_checkpoint, write_checkpoint
from .validator import ConditionResult, VerificationResult, evaluate_leaf, evaluate_page


ALLOWED_HOSTS = frozenset({"export.arxiv.org", "api.openalex.org", "dblp.org"})
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
DEFAULT_MINIMUM_INTERVALS = {
    "arxiv": 3.0,
    "openalex": 1.0,
    "dblp": 45.0,
}
QUOTA_RESERVE_CREDITS = 30
DBLP_RESTART_COOLDOWN_S = 45 * 60
EMPTY_BODY_SHA256 = hashlib.sha256(b"").hexdigest()


@dataclass(frozen=True)
class Response:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes
    final_url: str
    elapsed_s: float


class Transport(Protocol):
    def get(self, request: Any) -> Response: ...


class TransportError(RuntimeError):
    pass


class PreflightError(RuntimeError):
    pass


class QuotaPause(RuntimeError):
    pass


class _NoRedirect(urllib_request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


class HTTPSOnlyTransport:
    """urllib transport with redirects disabled and a 16 MiB body ceiling."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
        max_response_bytes: int = MAX_RESPONSE_BYTES,
    ) -> None:
        self._clock = clock
        self._max_response_bytes = max_response_bytes
        self._opener = urllib_request.build_opener(_NoRedirect())

    @staticmethod
    def _validate_request(spec: Any) -> None:
        method = _get(spec, "method")
        scheme = _get(spec, "scheme")
        host = _get(spec, "host")
        encoded_url = _get(spec, "encoded_url")
        if method != "GET":
            raise TransportError("only GET is registered")
        if scheme != "https" or host not in ALLOWED_HOSTS:
            raise TransportError("request must use HTTPS and an exactly allowed host")
        if not isinstance(encoded_url, str):
            raise TransportError("encoded_url is required")
        parsed = urlsplit(encoded_url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != host
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 443)
            or parsed.fragment
        ):
            raise TransportError("encoded_url does not match the registered HTTPS authority")
        if parsed.path != _get(spec, "path"):
            raise TransportError("encoded_url path differs from the registered path")

    def _bounded_read(self, stream: Any) -> bytes:
        body = stream.read(self._max_response_bytes + 1)
        if len(body) > self._max_response_bytes:
            raise TransportError("response exceeds the 16 MiB page limit")
        return body

    def get(self, request: Any) -> Response:
        self._validate_request(request)
        started = self._clock()
        headers = {key: value for key, value in tuple(_get(request, "headers", ()) or ())}
        req = urllib_request.Request(
            _get(request, "encoded_url"),
            headers=headers,
            method="GET",
        )
        try:
            with self._opener.open(req, timeout=float(_get(request, "timeout_s"))) as handle:
                body = self._bounded_read(handle)
                response_headers = tuple((str(key), str(value)) for key, value in handle.headers.items())
                final_url = handle.geturl()
                status = int(handle.status)
        except error.HTTPError as exc:
            # A disabled redirect and ordinary non-2xx status are evidence, not
            # implicit navigation.  Preserve the bounded error body for WAL.
            body = self._bounded_read(exc)
            response_headers = tuple((str(key), str(value)) for key, value in exc.headers.items())
            final_url = exc.geturl()
            status = int(exc.code)
        except (error.URLError, TimeoutError, OSError) as exc:
            raise TransportError(str(exc)) from exc
        elapsed = max(0.0, self._clock() - started)
        final = urlsplit(final_url)
        if final.scheme != "https" or final.hostname != _get(request, "host"):
            raise TransportError("transport returned an unregistered final URL")
        return Response(status, response_headers, body, final_url, elapsed)


class HostLimiter:
    """One pacing state per host, shared by controls, branches, and retries."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._clock = clock
        self._sleeper = sleeper
        self._last_issued: dict[str, float] = {}
        self._logical_now = float("-inf")

    def acquire(self, host: str, minimum_interval_s: float) -> float:
        if minimum_interval_s < 0:
            raise ValueError("minimum interval cannot be negative")
        observed = float(self._clock())
        now = max(observed, self._logical_now)
        previous = self._last_issued.get(host)
        wait_s = 0.0 if previous is None else max(0.0, previous + minimum_interval_s - now)
        if wait_s:
            self._sleeper(wait_s)
        issued = now + wait_s
        self._logical_now = issued
        self._last_issued[host] = issued
        return wait_s


@dataclass(frozen=True)
class QuotaObservation:
    observed_at_utc: str
    observed_at_jst: str
    limit: int | None
    remaining: int | None
    credits_per_request: int | None
    reset_seconds: int | None
    observed_request_id: str
    cost_usd: float | None
    header_evidence: tuple[tuple[str, str], ...]

    def permits_next(self, reserve: int = QUOTA_RESERVE_CREDITS) -> bool:
        if self.remaining is None or self.credits_per_request is None:
            return False
        return self.remaining - reserve >= self.credits_per_request


@dataclass(frozen=True)
class RunResult:
    state: str
    request_count: int
    pages: tuple[Any, ...]
    condition_results: tuple[ConditionResult, ...]
    checkpoint_path: str | None
    quota: QuotaObservation | None
    reason_code: str | None = None


@dataclass(frozen=True)
class _StoredRequest:
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


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _policy(catalog: Any, index: str) -> Mapping[str, Any]:
    policies = _get(catalog, "index_policies", {})
    if isinstance(policies, Mapping):
        value = policies.get(index, {})
        if isinstance(value, Mapping):
            return value
        if value is not None:
            return {
                key: getattr(value, key)
                for key in dir(value)
                if not key.startswith("_") and not callable(getattr(value, key))
            }
    return {}


def _minimum_interval(catalog: Any, index: str) -> float:
    policy = _policy(catalog, index)
    raw = policy.get("minimum_interval_s", policy.get("minimum_interval_seconds"))
    if raw is None:
        raw = DEFAULT_MINIMUM_INTERVALS[index]
    value = float(raw)
    # Registered values may be stricter, never weaker than the stage-4 floors.
    return max(value, DEFAULT_MINIMUM_INTERVALS[index])


def _page_size(catalog: Any, index: str) -> int:
    policy = _policy(catalog, index)
    value = policy.get("page_size", policy.get("page_capacity"))
    if value is None:
        value = 100 if index == "dblp" else 200
    return int(value)


def _pagination_kind(catalog: Any, index: str) -> str:
    policy = _policy(catalog, index)
    return str(policy.get("pagination_kind", "cursor" if index == "openalex" else "offset"))


def _retry_delays(catalog: Any, index: str) -> tuple[float, ...]:
    policy = _policy(catalog, index)
    raw = policy.get("retry_delays_s", policy.get("retry_delays"))
    if raw is None:
        raw = (3.0, 6.0, 12.0)
    return tuple(float(value) for value in raw)


def _independent_pass_required(catalog: Any, index: str, window_number: int) -> bool:
    registered = _policy(catalog, index).get("independent_pass_required")
    return bool(registered) if registered is not None else window_number > 1


def _default_request_builder(catalog: Any, leaf: str, page: int, position: str | None) -> Any:
    from .catalog import build_request

    return build_request(catalog, leaf, page, position)


def _default_parser(index: str) -> Callable[[bytes], Any]:
    from .parsers import parse_arxiv_page, parse_dblp_page, parse_openalex_page

    return {
        "arxiv": parse_arxiv_page,
        "openalex": parse_openalex_page,
        "dblp": parse_dblp_page,
    }[index]


def _header_map(headers: Sequence[tuple[str, str]]) -> dict[str, str]:
    return {key.lower(): value.strip() for key, value in headers}


def _as_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _cost_usd(body: bytes) -> float | None:
    try:
        value = json.loads(body)
        cost = value.get("meta", {}).get("cost_usd")
        return None if cost is None else float(cost)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError, AttributeError):
        return None


def observe_quota(response: Response, request_id: str, observed_epoch: float) -> QuotaObservation:
    headers = _header_map(response.headers)
    utc = datetime.fromtimestamp(observed_epoch, timezone.utc)
    jst = utc.astimezone(timezone(timedelta(hours=9)))
    selected = tuple(
        (key, value)
        for key, value in response.headers
        if key.lower()
        in {
            "x-ratelimit-limit",
            "x-ratelimit-remaining",
            "x-ratelimit-credits-used",
            "x-ratelimit-reset",
            "x-ratelimit-cost-usd",
        }
    )
    body_cost = _cost_usd(response.body)
    header_cost = headers.get("x-ratelimit-cost-usd")
    return QuotaObservation(
        observed_at_utc=utc.isoformat().replace("+00:00", "Z"),
        observed_at_jst=jst.isoformat(),
        limit=_as_int(headers.get("x-ratelimit-limit")),
        remaining=_as_int(headers.get("x-ratelimit-remaining")),
        credits_per_request=_as_int(headers.get("x-ratelimit-credits-used")),
        reset_seconds=_as_int(headers.get("x-ratelimit-reset")),
        observed_request_id=request_id,
        cost_usd=body_cost if body_cost is not None else (float(header_cost) if header_cost else None),
        header_evidence=selected,
    )


def _safe_component(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_.@" else "_" for ch in value)
    return safe[:180] or "request"


def _atomic_create(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = -1
        os.link(temporary, path, follow_symlinks=False)
        temporary.unlink()
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _store_raw_body(bundle: Path, request_id: str, attempt_number: int, body: bytes) -> Path:
    relative = Path("raw") / f"{_safe_component(request_id)}.a{attempt_number:02d}.body.gz"
    _atomic_create(bundle / relative, gzip.compress(body, compresslevel=9, mtime=0))
    return relative


def _occurrence_dict(occurrence: Any) -> dict[str, Any]:
    if is_dataclass(occurrence):
        return asdict(occurrence)
    if isinstance(occurrence, Mapping):
        return dict(occurrence)
    return {
        field: _get(occurrence, field)
        for field in (
            "index_work_id",
            "page_number",
            "ordinal",
            "raw_date_value",
            "interpreted_date",
            "date_missing_reason",
            "family_keys",
        )
    }


def _write_ledger(bundle: Path, leaf_query_id: str, pass_number: int, occurrences: Sequence[Any]) -> tuple[str, str, str, int, int]:
    lines = [
        json.dumps(_occurrence_dict(item), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for item in occurrences
    ]
    payload = (("\n".join(lines) + "\n") if lines else "").encode("utf-8")
    digest_suffix = hashlib.sha256(payload).hexdigest()[:12]
    relative = Path("ledgers") / f"{_safe_component(leaf_query_id)}.pass{pass_number}.{digest_suffix}.jsonl"
    target = bundle / relative
    if not target.exists():
        _atomic_create(target, payload)
    elif target.read_bytes() != payload:
        raise FileExistsError(target)
    work_ids = [str(_get(item, "index_work_id")) for item in occurrences if _get(item, "index_work_id")]
    primary_payload = "".join(f"{item}\n" for item in sorted(set(work_ids))).encode("utf-8")
    return (
        relative.as_posix(),
        hashlib.sha256(payload).hexdigest(),
        hashlib.sha256(primary_payload).hexdigest(),
        len(occurrences),
        len(set(work_ids)),
    )


def _request_template_sha(request: Any) -> str:
    value = {
        key: _get(request, key)
        for key in (
            "leaf_query_id",
            "logical_query_id",
            "index",
            "method",
            "scheme",
            "host",
            "path",
            "query_parameters",
            "headers",
            "timeout_s",
            "expected_interpreted_query",
        )
    }
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=list).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _complete_request(
    request: Any,
    *,
    role: str,
    executable: bool,
    run_id: str,
    pass_number: int,
    window_number: int,
    parent_response_sha256: str | None,
) -> dict[str, Any]:
    return {
        "request_id": str(_get(request, "request_id")),
        "leaf_query_id": str(_get(request, "leaf_query_id")),
        "logical_query_id": str(_get(request, "logical_query_id")),
        "index": str(_get(request, "index")),
        "request_role": role,
        "executable": executable,
        "method": str(_get(request, "method")),
        "scheme": str(_get(request, "scheme")),
        "host": str(_get(request, "host")),
        "path": str(_get(request, "path")),
        "query_parameters": [list(item) for item in tuple(_get(request, "query_parameters", ()))],
        "encoded_url": str(_get(request, "encoded_url")),
        "headers": [list(item) for item in tuple(_get(request, "headers", ()))],
        "empty_body_sha256": EMPTY_BODY_SHA256,
        "timeout_s": float(_get(request, "timeout_s")),
        "page_number": int(_get(request, "page_number")),
        "position_in": _get(request, "position_in"),
        "expected_interpreted_query": str(_get(request, "expected_interpreted_query")),
        "target_run_id": run_id,
        "target_pass_number": pass_number,
        "target_window_number": window_number,
        "parent_response_sha256": parent_response_sha256,
        "catalog_template_sha256": _request_template_sha(request),
    }


def _previous_checkpoint(value: str | os.PathLike[str] | Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return dict(value)
    path = Path(value)
    raw = path.read_bytes()
    return {"path": os.fspath(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _previous_checkpoint_value(
    value: str | os.PathLike[str] | Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, Mapping) and "completed_ledger" in value:
        return value
    if isinstance(value, (str, os.PathLike)):
        return load_checkpoint(value)
    return None


def _first_pass_digest(
    previous: str | os.PathLike[str] | Mapping[str, Any] | None,
) -> str | None:
    value = _previous_checkpoint_value(previous)
    if value is None:
        return None
    if value.get("pass_number") == 1:
        return _get(_get(value, "completed_ledger", {}), "primary_key_digest")
    return _get(_get(value, "second_pass", {}), "first_primary_key_digest")


def _quota_dict(index: str, quota: QuotaObservation | None) -> dict[str, Any]:
    if quota is None:
        return {
            "index": index,
            "observed_at_utc": None,
            "observed_at_jst": None,
            "limit": None,
            "remaining": None,
            "credits_per_request": None,
            "reset_seconds": None,
            "observed_request_id": None,
            "cost_usd": None,
            "header_evidence": [],
        }
    return {
        **asdict(quota),
        "header_evidence": [list(item) for item in quota.header_evidence],
        "index": index,
    }


def _checkpoint_payload(
    *,
    catalog: Any,
    request_builder: Callable[[Any, str, int, str | None], Any],
    current_request: Any,
    continuation_request: Any,
    registration_commit: str,
    catalog_path: str,
    catalog_sha256: str,
    bundle_root: Path,
    run_id: str,
    pass_number: int,
    window_number: int,
    state: str,
    resume_action: str,
    occurrences: Sequence[Any],
    quota: QuotaObservation | None,
    canonical_runner_argv: Sequence[str],
    previous_checkpoint: str | os.PathLike[str] | Mapping[str, Any] | None,
    last_attempt: Mapping[str, Any],
    parent_response_sha256: str | None,
    waiting_ruling_ids: Sequence[str] = (),
    second_pass_required: bool = False,
    second_pass_matches: bool | None = None,
) -> dict[str, Any]:
    leaf = str(_get(current_request, "leaf_query_id"))
    index = str(_get(current_request, "index"))
    first = request_builder(catalog, leaf, 0, None)
    ledger_path, ledger_sha, primary_digest, row_count, distinct_count = _write_ledger(
        bundle_root, leaf, pass_number, occurrences
    )
    continue_object = _complete_request(
        continuation_request,
        role="continue_cursor",
        executable=resume_action == "continue_cursor",
        run_id=run_id,
        pass_number=pass_number,
        window_number=window_number + (1 if state == "paused_quota" else 0),
        parent_response_sha256=parent_response_sha256,
    )
    independent_object = _complete_request(
        first,
        role="start_independent_pass",
        executable=resume_action == "start_independent_pass",
        run_id=run_id,
        pass_number=pass_number + 1,
        window_number=1,
        parent_response_sha256=None,
    )
    restart_object = _complete_request(
        first,
        role="restart_branch",
        executable=resume_action == "restart_branch",
        run_id=run_id,
        pass_number=1,
        window_number=1,
        parent_response_sha256=None,
    )
    return {
        "schema_version": "izanagi-axis1-search-checkpoint/v2",
        "registration_epoch": str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
        "registration_commit": registration_commit,
        "catalog_path": catalog_path,
        "catalog_sha256": catalog_sha256,
        "bundle_root": os.fspath(bundle_root),
        "canonical_runner_argv": list(canonical_runner_argv),
        "previous_checkpoint": _previous_checkpoint(previous_checkpoint),
        "query_id": str(_get(current_request, "logical_query_id")),
        "leaf_query_id": leaf,
        "index": index,
        "run_id": run_id,
        "pass_number": pass_number,
        "window_number": window_number,
        "state": state,
        "resume_action": resume_action,
        "requests": {
            "continue_cursor": continue_object,
            "start_independent_pass": independent_object,
            "restart_branch": restart_object,
        },
        "cursor_state": {
            "previous_request_id": str(_get(current_request, "request_id")),
            "parent_response_sha256": parent_response_sha256,
            "position_in": _get(current_request, "position_in"),
            "position_out": _get(continuation_request, "position_in"),
            "page_number": int(_get(current_request, "page_number")),
            "leaf_ordinal": int(_get(current_request, "page_number")),
        },
        "completed_ledger": {
            "path": ledger_path,
            "primary_key_kind": "index_work_id",
            "row_count": row_count,
            "distinct_count": distinct_count,
            "canonicalization": "utf8-jsonl-v1; primary digest is sorted unique index_work_id lines",
            "ledger_sha256": ledger_sha,
            "primary_key_digest": primary_digest,
        },
        "second_pass": {
            "required": second_pass_required,
            "state": "in_progress" if pass_number > 1 else "not_started",
            "ledger_path": None,
            "primary_key_digest": None,
            "first_primary_key_digest": (
                _first_pass_digest(previous_checkpoint)
                if pass_number > 1
                else primary_digest if second_pass_required else None
            ),
            "matches_first": second_pass_matches,
            "accepted": second_pass_matches if pass_number > 1 else None,
        },
        "waiting_ruling_ids": list(waiting_ruling_ids),
        "quota": _quota_dict(index, quota),
        "last_attempt": dict(last_attempt),
    }


def _preflight_passed(preflight: bool | VerificationResult | Callable[[], Any]) -> bool:
    result = preflight() if callable(preflight) else preflight
    if isinstance(result, bool):
        return result
    return bool(_get(result, "passed", False))


def _stored_request(value: Mapping[str, Any], *, logical_query_id: str, index: str) -> _StoredRequest:
    return _StoredRequest(
        request_id=str(value["request_id"]),
        leaf_query_id=str(value["leaf_query_id"]),
        logical_query_id=str(value.get("logical_query_id", logical_query_id)),
        index=str(value.get("index", index)),
        method=str(value["method"]),
        scheme=str(value["scheme"]),
        host=str(value["host"]),
        path=str(value["path"]),
        query_parameters=tuple(tuple(item) for item in value["query_parameters"]),
        encoded_url=str(value["encoded_url"]),
        headers=tuple(tuple(item) for item in value["headers"]),
        timeout_s=float(value["timeout_s"]),
        page_number=int(value["page_number"]),
        position_in=value.get("position_in"),
        expected_interpreted_query=str(value["expected_interpreted_query"]),
    )


def _requests_identical(left: Any, right: Any) -> bool:
    fields = (
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
    )
    for field in fields:
        left_value = _get(left, field)
        right_value = _get(right, field)
        if field in {"query_parameters", "headers"}:
            left_value = tuple(tuple(item) for item in left_value)
            right_value = tuple(tuple(item) for item in right_value)
        if left_value != right_value:
            return False
    return True


def run_leaf(
    catalog: Any,
    leaf_query_id: str,
    *,
    run_id: str,
    registration_commit: str,
    catalog_path: str,
    bundle_root: str | os.PathLike[str],
    transport: Transport,
    preflight: bool | VerificationResult | Callable[[], Any],
    request_builder: Callable[[Any, str, int, str | None], Any] | None = None,
    parser: Callable[[bytes], Any] | None = None,
    clock: Callable[[], float] = time.time,
    sleeper: Callable[[float], None] = time.sleep,
    limiter: HostLimiter | None = None,
    pass_number: int = 1,
    window_number: int = 1,
    canonical_runner_argv: Sequence[str] = ("tools/run_axis1_search.py",),
    previous_checkpoint: str | os.PathLike[str] | Mapping[str, Any] | None = None,
    initial_request: Any | None = None,
    max_pages: int | None = None,
) -> RunResult:
    """Run one registered executable leaf.

    A failed preflight returns by exception before the first limiter or transport
    call, making the zero-HTTP property easy to audit and test.
    """

    if not _preflight_passed(preflight):
        raise PreflightError("registration preflight failed before HTTP issuance")
    if len(registration_commit) != 40:
        raise ValueError("registration_commit must contain the full 40 hex digits")
    builder = request_builder or _default_request_builder
    bundle = Path(bundle_root)
    bundle.mkdir(parents=True, exist_ok=True)
    catalog_bytes = Path(catalog_path).read_bytes()
    catalog_sha256 = hashlib.sha256(catalog_bytes).hexdigest()
    host_limiter = limiter or HostLimiter(clock=clock, sleeper=sleeper)
    request = initial_request or builder(catalog, leaf_query_id, 0, None)
    index = str(_get(request, "index"))
    if index not in DEFAULT_MINIMUM_INTERVALS:
        raise ValueError(f"unsupported index: {index}")
    parse = parser or _default_parser(index)
    page_size = _page_size(catalog, index)
    pagination_kind = _pagination_kind(catalog, index)
    retry_delays = _retry_delays(catalog, index)
    wal_path = bundle / "wal" / f"{_safe_component(leaf_query_id)}.jsonl"
    pages: list[Any] = []
    occurrences: list[Any] = []
    request_count = 0
    attempts_by_request: dict[str, int] = {}
    latest_quota: QuotaObservation | None = None
    parent_response_sha: str | None = None
    restarted_dblp = False
    checkpoint_path: str | None = None

    while True:
        if max_pages is not None and len(pages) >= max_pages:
            break
        if index == "openalex" and latest_quota is not None and not latest_quota.permits_next():
            next_request = request
            payload = _checkpoint_payload(
                catalog=catalog,
                request_builder=builder,
                current_request=request,
                continuation_request=next_request,
                registration_commit=registration_commit,
                catalog_path=catalog_path,
                catalog_sha256=catalog_sha256,
                bundle_root=bundle,
                run_id=run_id,
                pass_number=pass_number,
                window_number=window_number,
                state="paused_quota",
                resume_action="continue_cursor",
                occurrences=occurrences,
                quota=latest_quota,
                canonical_runner_argv=canonical_runner_argv,
                previous_checkpoint=previous_checkpoint,
                last_attempt={"state": "terminal", "request_id": latest_quota.observed_request_id, "attempt_number": attempts_by_request.get(latest_quota.observed_request_id, 1), "failure": None, "raw_evidence_path": None},
                parent_response_sha256=parent_response_sha,
                second_pass_required=True,
            )
            checkpoint = write_checkpoint(bundle / "checkpoints", payload)
            return RunResult("paused_quota", request_count, tuple(pages), (), os.fspath(checkpoint), latest_quota, "quota_reserve")

        response: Response | None = None
        failure: str | None = None
        raw_path: Path | None = None
        request_id = str(_get(request, "request_id"))
        for retry_ordinal in range(len(retry_delays) + 1):
            attempt_number = attempts_by_request.get(request_id, 0) + 1
            attempts_by_request[request_id] = attempt_number
            append_attempt_state(wal_path, request_id, attempt_number, "prepared", clock=clock)
            host_limiter.acquire(str(_get(request, "host")), _minimum_interval(catalog, index))
            append_attempt_state(wal_path, request_id, attempt_number, "issued", clock=clock)
            request_count += 1
            try:
                response = transport.get(request)
                raw_path = _store_raw_body(bundle, request_id, attempt_number, response.body)
                append_attempt_state(
                    wal_path,
                    request_id,
                    attempt_number,
                    "response_stored",
                    payload={
                        "status": response.status,
                        "body_path": raw_path.as_posix(),
                        "body_sha256": hashlib.sha256(response.body).hexdigest(),
                        "final_url": response.final_url,
                    },
                    clock=clock,
                )
                if index == "openalex":
                    latest_quota = observe_quota(response, request_id, clock())
                if response.status == 200:
                    failure = None
                    break
                failure = f"http_status_{response.status}"
                append_attempt_state(wal_path, request_id, attempt_number, "parsed", payload={"parse_skipped": True}, clock=clock)
                append_attempt_state(wal_path, request_id, attempt_number, "terminal", payload={"outcome": "retryable_failure", "reason_code": failure}, clock=clock)
            except Exception as exc:  # transport boundary; issued remains durable
                if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                    raise
                response = None
                failure = "transport_exception"
            if retry_ordinal < len(retry_delays):
                sleeper(retry_delays[retry_ordinal])

        if response is None or response.status != 200:
            first = builder(catalog, leaf_query_id, 0, None)
            payload = _checkpoint_payload(
                catalog=catalog,
                request_builder=builder,
                current_request=request,
                continuation_request=request,
                registration_commit=registration_commit,
                catalog_path=catalog_path,
                catalog_sha256=catalog_sha256,
                bundle_root=bundle,
                run_id=run_id,
                pass_number=pass_number,
                window_number=window_number,
                state="outcome_unknown",
                resume_action="restart_branch",
                occurrences=occurrences,
                quota=latest_quota,
                canonical_runner_argv=canonical_runner_argv,
                previous_checkpoint=previous_checkpoint,
                last_attempt={"state": "issued" if response is None else "terminal", "request_id": request_id, "attempt_number": attempts_by_request[request_id], "failure": failure, "raw_evidence_path": raw_path.as_posix() if raw_path else None},
                parent_response_sha256=parent_response_sha,
                second_pass_required=_independent_pass_required(catalog, index, window_number) or pass_number > 1,
            )
            checkpoint = write_checkpoint(bundle / "checkpoints", payload)
            checkpoint_path = os.fspath(checkpoint)
            if index == "dblp" and not restarted_dblp:
                sleeper(DBLP_RESTART_COOLDOWN_S)
                restarted_dblp = True
                pages.clear()
                occurrences.clear()
                parent_response_sha = None
                previous_checkpoint = checkpoint
                request = first
                continue
            return RunResult("outcome_unknown", request_count, tuple(pages), (), checkpoint_path, latest_quota, failure)

        try:
            parsed = parse(response.body)
        except Exception as exc:
            append_attempt_state(wal_path, request_id, attempts_by_request[request_id], "parsed", payload={"parse_error": str(exc)}, clock=clock)
            append_attempt_state(wal_path, request_id, attempts_by_request[request_id], "terminal", payload={"outcome": "failed", "reason_code": "parse_error"}, clock=clock)
            return RunResult("outcome_unknown", request_count, tuple(pages), (), checkpoint_path, latest_quota, "parse_error")

        append_attempt_state(wal_path, request_id, attempts_by_request[request_id], "parsed", clock=clock)
        page_results = evaluate_page(
            parsed,
            page_size=page_size,
            expected_interpreted_query=str(_get(request, "expected_interpreted_query")),
            pagination_kind=pagination_kind,
        )
        failure_result = next((item for item in page_results if not item.passed), None)
        append_attempt_state(
            wal_path,
            request_id,
            attempts_by_request[request_id],
            "terminal",
            payload={"outcome": "success" if failure_result is None else "failed", "reason_code": failure_result.reason_code if failure_result else None},
            clock=clock,
        )
        pages.append(parsed)
        occurrences.extend(tuple(_get(parsed, "occurrences", ()) or ()))
        parent_response_sha = hashlib.sha256(response.body).hexdigest()
        if failure_result is not None:
            return RunResult("blocked_on_ruling", request_count, tuple(pages), tuple(page_results), checkpoint_path, latest_quota, failure_result.reason_code)
        position_out = _get(parsed, "position_out")
        if position_out is None:
            requires_independent = (
                _independent_pass_required(catalog, index, window_number)
                or pass_number > 1
            )
            current_ids = sorted(
                {
                    str(_get(item, "index_work_id"))
                    for item in occurrences
                    if _get(item, "index_work_id")
                }
            )
            current_digest = hashlib.sha256(
                "".join(f"{item}\n" for item in current_ids).encode("utf-8")
            ).hexdigest()
            first_digest = _first_pass_digest(previous_checkpoint) if pass_number > 1 else None
            digest_matches = (
                current_digest == first_digest
                if pass_number > 1 and first_digest is not None
                else None
            )
            leaf_results = evaluate_leaf(
                pages,
                page_size=page_size,
                expected_interpreted_query=str(_get(request, "expected_interpreted_query")),
                pagination_kind=pagination_kind,
                state="branch_complete",
                second_pass_required=requires_independent and pass_number > 1,
                second_pass_digest_matches=digest_matches,
            )
            if pass_number == 1 and requires_independent and all(item.passed for item in leaf_results):
                payload = _checkpoint_payload(
                    catalog=catalog,
                    request_builder=builder,
                    current_request=request,
                    continuation_request=request,
                    registration_commit=registration_commit,
                    catalog_path=catalog_path,
                    catalog_sha256=catalog_sha256,
                    bundle_root=bundle,
                    run_id=run_id,
                    pass_number=pass_number,
                    window_number=window_number,
                    state="pass_complete",
                    resume_action="start_independent_pass",
                    occurrences=occurrences,
                    quota=latest_quota,
                    canonical_runner_argv=canonical_runner_argv,
                    previous_checkpoint=previous_checkpoint,
                    last_attempt={
                        "state": "terminal",
                        "request_id": request_id,
                        "attempt_number": attempts_by_request[request_id],
                        "failure": None,
                        "raw_evidence_path": raw_path.as_posix() if raw_path else None,
                    },
                    parent_response_sha256=parent_response_sha,
                    second_pass_required=True,
                )
                checkpoint = write_checkpoint(bundle / "checkpoints", payload)
                return RunResult(
                    "pass_complete",
                    request_count,
                    tuple(pages),
                    tuple(leaf_results),
                    os.fspath(checkpoint),
                    latest_quota,
                )
            state = "branch_complete" if all(item.passed for item in leaf_results) else "blocked_on_ruling"
            reason = next((item.reason_code for item in leaf_results if not item.passed), None)
            return RunResult(state, request_count, tuple(pages), tuple(leaf_results), checkpoint_path, latest_quota, reason)
        request = builder(catalog, leaf_query_id, int(_get(request, "page_number")) + 1, str(position_out))

    leaf_results = evaluate_leaf(
        pages,
        page_size=page_size,
        expected_interpreted_query=str(_get(request, "expected_interpreted_query")),
        pagination_kind=pagination_kind,
        state="paused_quota",
    )
    return RunResult("paused_quota", request_count, tuple(pages), tuple(leaf_results), checkpoint_path, latest_quota, "page_limit")


def resume_from_checkpoint(
    checkpoint_path: str | os.PathLike[str],
    catalog: Any,
    *,
    transport: Transport,
    preflight: bool | VerificationResult | Callable[[], Any],
    request_builder: Callable[[Any, str, int, str | None], Any] | None = None,
    parser: Callable[[bytes], Any] | None = None,
    clock: Callable[[], float] = time.time,
    sleeper: Callable[[float], None] = time.sleep,
    limiter: HostLimiter | None = None,
    canonical_runner_argv: Sequence[str] = ("tools/run_axis1_search.py",),
) -> RunResult:
    """Resume strictly from the checkpoint's registered ``resume_action``."""

    checkpoint = load_checkpoint(checkpoint_path)
    action = checkpoint["resume_action"]
    if action in {"blocked_on_ruling", "not_applicable"}:
        raise PreflightError(f"checkpoint resume_action {action!r} is not executable")
    selected = checkpoint["requests"][action]
    if not selected.get("executable"):
        raise PreflightError(f"checkpoint-selected request {action!r} is not executable")
    initial = _stored_request(
        selected,
        logical_query_id=checkpoint["query_id"],
        index=checkpoint["index"],
    )
    catalog_bytes = Path(checkpoint["catalog_path"]).read_bytes()
    if hashlib.sha256(catalog_bytes).hexdigest() != checkpoint["catalog_sha256"]:
        raise PreflightError("checkpoint catalog digest does not match current catalog bytes")
    builder = request_builder or _default_request_builder
    registered = builder(
        catalog,
        checkpoint["leaf_query_id"],
        initial.page_number,
        initial.position_in,
    )
    if not _requests_identical(initial, registered):
        raise PreflightError("checkpoint-selected request differs from the registered catalog request")
    return run_leaf(
        catalog,
        checkpoint["leaf_query_id"],
        run_id=selected["target_run_id"],
        registration_commit=checkpoint["registration_commit"],
        catalog_path=checkpoint["catalog_path"],
        bundle_root=checkpoint["bundle_root"],
        transport=transport,
        preflight=preflight,
        request_builder=builder,
        parser=parser,
        clock=clock,
        sleeper=sleeper,
        limiter=limiter,
        pass_number=selected["target_pass_number"],
        window_number=selected["target_window_number"],
        canonical_runner_argv=canonical_runner_argv,
        previous_checkpoint=checkpoint_path,
        initial_request=initial,
    )


__all__ = [
    "ALLOWED_HOSTS",
    "DBLP_RESTART_COOLDOWN_S",
    "DEFAULT_MINIMUM_INTERVALS",
    "HTTPSOnlyTransport",
    "HostLimiter",
    "MAX_RESPONSE_BYTES",
    "PreflightError",
    "QUOTA_RESERVE_CREDITS",
    "QuotaObservation",
    "Response",
    "RunResult",
    "Transport",
    "TransportError",
    "observe_quota",
    "resume_from_checkpoint",
    "run_leaf",
]
