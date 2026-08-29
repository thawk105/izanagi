"""Registered axis-1 retrieval runner.

All mutable dependencies (transport, clock, sleeper, request builder, parser)
are injectable.  The production transport is deliberately small and rejects
redirects, non-HTTPS URLs, and hosts outside the registered allow-list.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timedelta, timezone
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Protocol
from urllib import error, request as urllib_request
from urllib.parse import quote_plus, urlencode, urlsplit

from .checkpoint import append_attempt_state, load_checkpoint, write_checkpoint
from .validator import ConditionResult, VerificationResult, evaluate_leaf, evaluate_page


ALLOWED_HOSTS = frozenset({"export.arxiv.org", "api.openalex.org", "dblp.org"})
REGISTERED_ENDPOINTS = {
    "export.arxiv.org": ("/api/query", "application/atom+xml"),
    "api.openalex.org": ("/works", "application/json"),
    "dblp.org": ("/search/publ/api", "application/json"),
}
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
DEFAULT_MINIMUM_INTERVALS = {
    "arxiv": 3.0,
    "openalex": 1.0,
    "dblp": 45.0,
}
QUOTA_RESERVE_CREDITS = 30
DBLP_RESTART_COOLDOWN_S = 45 * 60
EMPTY_BODY_SHA256 = hashlib.sha256(b"").hexdigest()
_UNSET_VALUE = object()


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
        registered_path, registered_accept = REGISTERED_ENDPOINTS[host]
        if parsed.path != registered_path or _get(spec, "path") != registered_path:
            raise TransportError("request path is not the registered path for this host")
        parameters = tuple(_get(spec, "query_parameters", ()) or ())
        if any(
            not isinstance(pair, (list, tuple))
            or len(pair) != 2
            or not all(isinstance(item, str) for item in pair)
            for pair in parameters
        ):
            raise TransportError("query_parameters must be ordered string pairs")
        expected_query = urlencode(parameters, doseq=False, quote_via=quote_plus)
        if parsed.query != expected_query:
            raise TransportError("encoded_url query differs from the registered ordered parameters")
        if tuple(_get(spec, "headers", ()) or ()) != (("Accept", registered_accept),):
            raise TransportError("only the registered Accept header is permitted")

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
        state_path: str | os.PathLike[str] | None = None,
    ) -> None:
        self._clock = clock
        self._sleeper = sleeper
        self._last_issued: dict[str, float] = {}
        self._logical_now = float("-inf")
        self._state_path = Path(state_path) if state_path is not None else None

    def acquire(self, host: str, minimum_interval_s: float) -> float:
        if minimum_interval_s < 0:
            raise ValueError("minimum interval cannot be negative")
        if self._state_path is None:
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

        def update(state: dict[str, Any]) -> float:
            hosts = state.setdefault("hosts", {})
            observed = float(self._clock())
            previous_value = _get(hosts.get(host, {}), "last_issued")
            previous = float(previous_value) if isinstance(previous_value, (int, float)) else None
            wait_s = 0.0 if previous is None else max(
                0.0, previous + minimum_interval_s - observed
            )
            if wait_s:
                self._sleeper(wait_s)
            hosts[host] = {"last_issued": observed + wait_s}
            return wait_s

        return _locked_runtime_update(self._state_path, update)


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


@dataclass(frozen=True)
class _PageRecord:
    page: Any
    request: Any
    response: Response
    raw_path: Path
    conditions: tuple[ConditionResult, ...]


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


def _logical_query(catalog: Any, query_id: str) -> Any:
    resolver = _get(catalog, "logical_query")
    if callable(resolver):
        return resolver(query_id)
    for query in tuple(_get(catalog, "logical_queries", ()) or ()):
        if _get(query, "query_id") == query_id:
            return query
    raise ValueError(f"catalog lacks logical query {query_id!r}")


def control_leaf_query_id(catalog: Any, control_id: str, index: str) -> str:
    """Resolve a registered control descriptor to a deterministic executable probe.

    The request remains a catalog-built leaf request; callers cannot supply a
    filter, URL, or header.  Block controls select their corresponding branch,
    while operational controls use Q1 as the smallest common probe.
    """

    controls = tuple(_get(catalog, "controls", ()) or ())
    descriptor = next(
        (item for item in controls if _get(item, "control_id") == control_id), None
    )
    if descriptor is None or index not in tuple(_get(descriptor, "indexes", ()) or ()):
        raise ValueError("control/index pair is not registered")
    branch = {
        "C-BLK-T": "Q1",
        "C-BLK-M": "Q2",
        "C-BLK-O": "Q4",
        "C-BLK-V": "Q5",
        "C-BLK-W": "Q6",
    }.get(control_id, "Q1")
    candidates = sorted(
        (
            query
            for query in tuple(_get(catalog, "logical_queries", ()) or ())
            if _get(query, "kind") == "leaf"
            and _get(query, "index") == index
            and _get(query, "branch") == branch
        ),
        key=lambda item: str(_get(item, "query_id")),
    )
    if not candidates:
        raise ValueError("registered control has no executable leaf probe")
    return str(_get(candidates[0], "query_id"))


def _independent_pass_required(catalog: Any, leaf_query_id: str) -> bool:
    query = _logical_query(catalog, leaf_query_id)
    registered = _get(query, "independent_pass_required")
    if not isinstance(registered, bool):
        raise ValueError("logical query lacks registered independent_pass_required")
    return registered


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


def _parse_registered_page(parser: Callable[..., Any], body: bytes, page_number: int) -> Any:
    """Pass request context to the registered parser (with transition fallback)."""

    try:
        return parser(body, page_number)
    except TypeError as exc:
        # Kept only so an author-B checkout remains diagnosable while fix-A is
        # being integrated.  The registered production parsers use two args.
        try:
            return parser(body)
        except TypeError:
            raise exc


def _openalex_oqo(body: bytes) -> Any:
    try:
        value = json.loads(body)
        return value["meta"]["x_query"]["oqo"]
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, KeyError):
        return None


def _expected_openalex_oqo(catalog: Any, leaf_query_id: str) -> Any:
    query = _logical_query(catalog, leaf_query_id)
    for field in (
        "expected_interpreted_query_structure",
        "expected_x_query_oqo",
        "expected_oqo",
    ):
        value = _get(query, field, _UNSET_VALUE)
        if value is not _UNSET_VALUE:
            return value
    raise ValueError("OpenAlex logical query lacks registered meta.x_query.oqo expectation")


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


def _attempt_counts(wal_path: Path) -> dict[str, int]:
    if not wal_path.exists():
        return {}
    result: dict[str, int] = {}
    for line in wal_path.read_bytes().splitlines():
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PreflightError("existing WAL is malformed") from exc
        request_id = _get(value, "request_id")
        attempt = _get(value, "attempt_number")
        if isinstance(request_id, str) and isinstance(attempt, int):
            result[request_id] = max(result.get(request_id, 0), attempt)
    return result


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


def _atomic_replace(path: Path, payload: bytes) -> None:
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
        os.replace(temporary, path)
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


def _runtime_default() -> dict[str, Any]:
    return {
        "schema_version": "izanagi-axis1-search-runtime-state/v1",
        "hosts": {},
        "quota": {},
        "dblp_restart_count": 0,
    }


def _locked_runtime_update(path: Path, operation: Callable[[dict[str, Any]], Any]) -> Any:
    """Serialize bundle-wide pacing, quota, and DBLP restart observations."""

    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.lseek(fd, 0, os.SEEK_SET)
        raw = b""
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            raw += chunk
        if raw:
            try:
                state = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError("bundle runtime state is malformed") from exc
            if not isinstance(state, dict) or state.get("schema_version") != _runtime_default()["schema_version"]:
                raise ValueError("bundle runtime state has an unsupported schema")
        else:
            state = _runtime_default()
        result = operation(state)
        payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
        return result
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _quota_from_mapping(value: Mapping[str, Any] | None) -> QuotaObservation | None:
    if not value or not value.get("observed_request_id"):
        return None
    return QuotaObservation(
        observed_at_utc=str(value["observed_at_utc"]),
        observed_at_jst=str(value["observed_at_jst"]),
        limit=value.get("limit"),
        remaining=value.get("remaining"),
        credits_per_request=value.get("credits_per_request"),
        reset_seconds=value.get("reset_seconds"),
        observed_request_id=str(value["observed_request_id"]),
        cost_usd=value.get("cost_usd"),
        header_evidence=tuple(tuple(item) for item in value.get("header_evidence", ())),
    )


def _merge_quota(
    previous: QuotaObservation | None, current: QuotaObservation
) -> QuotaObservation:
    """Keep the newest evidence while never replacing a known numeric value by absence."""

    return QuotaObservation(
        observed_at_utc=current.observed_at_utc,
        observed_at_jst=current.observed_at_jst,
        limit=current.limit if current.limit is not None else (previous.limit if previous else None),
        remaining=(
            current.remaining if current.remaining is not None else (previous.remaining if previous else None)
        ),
        credits_per_request=(
            current.credits_per_request
            if current.credits_per_request is not None
            else (previous.credits_per_request if previous else None)
        ),
        reset_seconds=(
            current.reset_seconds
            if current.reset_seconds is not None
            else (previous.reset_seconds if previous else None)
        ),
        observed_request_id=current.observed_request_id,
        cost_usd=current.cost_usd if current.cost_usd is not None else (previous.cost_usd if previous else None),
        header_evidence=current.header_evidence or (previous.header_evidence if previous else ()),
    )


def _load_persisted_quota(path: Path, index: str) -> QuotaObservation | None:
    return _locked_runtime_update(
        path,
        lambda state: _quota_from_mapping(_get(state.get("quota", {}), index)),
    )


def _persist_quota(path: Path, index: str, observation: QuotaObservation) -> None:
    def update(state: dict[str, Any]) -> None:
        state.setdefault("quota", {})[index] = {
            **asdict(observation),
            "header_evidence": [list(item) for item in observation.header_evidence],
        }

    _locked_runtime_update(path, update)


def _reserve_dblp_restart(path: Path) -> bool:
    def update(state: dict[str, Any]) -> bool:
        count = state.get("dblp_restart_count", 0)
        if not isinstance(count, int) or count < 0:
            raise ValueError("invalid persistent DBLP restart count")
        if count >= 1:
            return False
        state["dblp_restart_count"] = count + 1
        return True

    return _locked_runtime_update(path, update)


def _store_raw_body(bundle: Path, request_id: str, attempt_number: int, body: bytes) -> Path:
    relative = Path("raw") / f"{_safe_component(request_id)}.a{attempt_number:02d}.body.gz"
    _atomic_create(bundle / relative, gzip.compress(body, compresslevel=9, mtime=0))
    return relative


def _read_stored_raw(path: Path) -> bytes:
    with gzip.open(path, "rb") as handle:
        body = handle.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise PreflightError("stored raw response exceeds the 16 MiB limit")
    return body


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


def _write_ledger(
    bundle: Path,
    leaf_query_id: str,
    pass_number: int,
    occurrences: Sequence[Any],
    *,
    registration_epoch: str,
    registration_commit: str,
    catalog_sha256: str,
    run_id: str,
    logical_query_id: str,
    index: str,
) -> tuple[str, str, str, int, int]:
    occurrence_values = [_occurrence_dict(item) for item in occurrences]
    work_ids = [
        str(_get(item, "index_work_id"))
        for item in occurrences
        if _get(item, "index_work_id")
    ]
    value = {
        "schema_version": "izanagi-axis1-search-record-occurrence-ledger/v1",
        "document_type": "record_occurrence_ledger",
        "registration_epoch": registration_epoch,
        "registration_commit": registration_commit,
        "catalog_sha256": catalog_sha256,
        "run_id": run_id,
        "logical_query_id": logical_query_id,
        "leaf_query_id": leaf_query_id,
        "index": index,
        "primary_key_kind": "index_work_id",
        "occurrence_count": len(occurrence_values),
        "distinct_index_work_id_count": len(set(work_ids)),
        "occurrences": occurrence_values,
    }
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    digest_suffix = hashlib.sha256(payload).hexdigest()[:12]
    relative = Path("ledgers") / f"{_safe_component(leaf_query_id)}.pass{pass_number}.{digest_suffix}.json"
    target = bundle / relative
    if not target.exists():
        _atomic_create(target, payload)
    elif target.read_bytes() != payload:
        raise FileExistsError(target)
    primary_payload = "".join(f"{item}\n" for item in sorted(set(work_ids))).encode("utf-8")
    return (
        relative.as_posix(),
        hashlib.sha256(payload).hexdigest(),
        hashlib.sha256(primary_payload).hexdigest(),
        len(occurrences),
        len(set(work_ids)),
    )


def _content_type(headers: Sequence[tuple[str, str]]) -> str | None:
    raw = _header_map(headers).get("content-type")
    return raw.split(";", 1)[0].strip().lower() if raw else None


def _response_context(
    catalog: Any,
    request: Any,
    response: Response,
    raw_path: Path,
    *,
    actual_structure: Any = _UNSET_VALUE,
) -> dict[str, Any]:
    index = str(_get(request, "index"))
    expected_type = REGISTERED_ENDPOINTS[str(_get(request, "host"))][1]
    actual_type = _content_type(response.headers)
    stored = raw_path.suffix == ".gz"
    context: dict[str, Any] = {
        "expected_interpreted_query": str(_get(request, "expected_interpreted_query")),
        "expected_position_in": _get(request, "position_in"),
        "expected_page_number": int(_get(request, "page_number")),
        "pagination_kind": _pagination_kind(catalog, index),
        "response_ok": (
            response.status == 200
            and actual_type == expected_type
            and response.final_url == str(_get(request, "encoded_url"))
        ),
        "evidence_complete": stored,
    }
    if index == "openalex":
        context["expected_interpreted_structure"] = _expected_openalex_oqo(
            catalog, str(_get(request, "leaf_query_id"))
        )
        context["actual_interpreted_structure"] = (
            _openalex_oqo(response.body)
            if actual_structure is _UNSET_VALUE
            else actual_structure
        )
    return context


def _safe_response_headers(headers: Sequence[tuple[str, str]]) -> list[list[str]]:
    allowed = {
        "content-type",
        "x-ratelimit-limit",
        "x-ratelimit-remaining",
        "x-ratelimit-credits-used",
        "x-ratelimit-reset",
        "x-ratelimit-cost-usd",
    }
    seen: set[tuple[str, str]] = set()
    values: list[list[str]] = []
    for key, value in headers:
        if key.lower() in allowed and (key.lower(), value) not in seen:
            seen.add((key.lower(), value))
            values.append([key, value])
    return values


def _condition_documents(results: Sequence[ConditionResult]) -> list[dict[str, Any]]:
    return [
        {
            "condition": item.condition,
            "passed": item.passed,
            "reason_code": item.reason_code,
            "detail": item.detail,
        }
        for item in results
    ]


def _schema_node(root: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    reference = node.get("$ref")
    if isinstance(reference, str) and reference.startswith("#/definitions/"):
        return root["definitions"][reference.rsplit("/", 1)[-1]]
    return node


def _condition_for_schema(
    root: Mapping[str, Any], node: Mapping[str, Any], result: ConditionResult
) -> Any:
    node = _schema_node(root, node)
    if node.get("type") == "boolean":
        return result.passed
    properties = node.get("properties", {})
    if not isinstance(properties, Mapping):
        properties = {}
    required = set(node.get("required", ()))
    allowed = set(properties) if node.get("additionalProperties") is False else {
        "condition",
        "passed",
        "reason_code",
        "detail",
    }
    values: dict[str, Any] = {}
    for key in allowed | required:
        if key in {"condition", "condition_number", "number"}:
            values[key] = result.condition
        elif key == "passed":
            values[key] = result.passed
        elif key == "reason_code":
            values[key] = result.reason_code
        elif key == "detail":
            values[key] = result.detail
        elif key == "status":
            status_schema = _schema_node(root, properties.get(key, {}))
            enum = status_schema.get("enum", ())
            values[key] = (
                "passed"
                if result.passed and "passed" in enum
                else "failed"
                if not result.passed and "failed" in enum
                else result.passed
            )
    return values


def _completion_for_schema(
    root: Mapping[str, Any], node: Mapping[str, Any], results: Sequence[ConditionResult]
) -> Any:
    node = _schema_node(root, node)
    if node.get("type") == "array" or "items" in node:
        item_schema = node.get("items", {})
        return [_condition_for_schema(root, item_schema, result) for result in results]
    properties = node.get("properties", {})
    required = set(node.get("required", ()))
    if not isinstance(properties, Mapping):
        properties = {}
    value: dict[str, Any] = {}
    for key in set(properties) | required:
        child = _schema_node(root, properties.get(key, {}))
        if key in {"conditions", "condition_results", "results"}:
            value[key] = _completion_for_schema(root, child, results)
        elif key in {"all_passed", "passed"}:
            value[key] = all(result.passed for result in results)
        else:
            import re

            match = re.search(r"([1-6])$", key)
            if match:
                result = next(item for item in results if item.condition == int(match.group(1)))
                value[key] = _condition_for_schema(root, child, result)
    if not required.issubset(value):
        raise ValueError("unsupported completion schema shape")
    return value


def _write_page_evidence(
    bundle: Path,
    *,
    catalog: Any,
    request: Any,
    response: Response,
    parsed: Any,
    raw_path: Path,
    ledger_path: str,
    registration_commit: str,
    catalog_path: str,
    catalog_sha256: str,
    run_id: str,
    pass_number: int,
    window_number: int,
    attempt_number: int,
    parent_response_sha256: str | None,
    quota: QuotaObservation | None,
    wal_times: Mapping[str, str | None],
    conditions: Sequence[ConditionResult],
    failure: Mapping[str, Any] | None,
) -> Path:
    occurrences = tuple(_get(parsed, "occurrences", ()) or ())
    work_ids = [str(_get(item, "index_work_id")) for item in occurrences if _get(item, "index_work_id")]
    primary = "".join(f"{item}\n" for item in sorted(set(work_ids))).encode("utf-8")
    observed = quota if str(_get(request, "index")) == "openalex" else None
    value: dict[str, Any] = {
        "schema_version": "izanagi-axis1-search-page-evidence/v1",
        "document_type": "page_evidence",
        "identity": {
            "registration_epoch": str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
            "registration_commit": registration_commit,
            "catalog_path": catalog_path,
            "catalog_sha256": catalog_sha256,
            "run_id": run_id,
            "pass_number": pass_number,
            "window_number": window_number,
            "logical_query_id": str(_get(request, "logical_query_id")),
            "leaf_query_id": str(_get(request, "leaf_query_id")),
            "request_id": str(_get(request, "request_id")),
            "attempt_number": attempt_number,
            "page_number": int(_get(request, "page_number")),
            "index": str(_get(request, "index")),
        },
        "request": {
            "method": str(_get(request, "method")),
            "scheme": str(_get(request, "scheme")),
            "host": str(_get(request, "host")),
            "path": str(_get(request, "path")),
            "query_parameters": [list(item) for item in tuple(_get(request, "query_parameters", ()))],
            "encoded_url": str(_get(request, "encoded_url")),
            "headers": [list(item) for item in tuple(_get(request, "headers", ()))],
            "timeout_s": float(_get(request, "timeout_s")),
            "position_in": _get(request, "position_in"),
            "expected_interpreted_query": str(_get(request, "expected_interpreted_query")),
            "parent_response_sha256": parent_response_sha256,
        },
        "wal": {
            "state": "terminal" if wal_times["terminal"] is not None else "issued",
            "prepared_at": wal_times["prepared"],
            "issued_at": wal_times["issued"],
            "response_stored_at": wal_times["response_stored"],
            "parsed_at": wal_times["parsed"],
            "terminal_at": wal_times["terminal"],
        },
        "response": {
            "status": response.status,
            "safe_headers": _safe_response_headers(response.headers),
            "content_type": _content_type(response.headers) or "application/octet-stream",
            "final_url": response.final_url,
            "body_path": raw_path.as_posix(),
            "byte_count": len(response.body),
            "sha256": hashlib.sha256(response.body).hexdigest(),
            "redirect_chain": [],
            "elapsed_s": response.elapsed_s,
        },
        "quota": {
            "limit": observed.limit if observed else None,
            "remaining": observed.remaining if observed else None,
            "credits_used": observed.credits_per_request if observed else None,
            "cost_usd": observed.cost_usd if observed else None,
            "reset_observation": str(observed.reset_seconds) if observed and observed.reset_seconds is not None else None,
            "observed_at": observed.observed_at_utc if observed else None,
        },
        "parse": {
            "interpreted_query": str(_get(parsed, "interpreted_query", "")),
            "declared_total": _get(parsed, "declared_total"),
            "capacity_echo": _get(parsed, "capacity_echo"),
            "actual_count": int(_get(parsed, "actual_count", 0)),
            "position_in": _get(parsed, "position_in"),
            "position_out": _get(parsed, "position_out"),
            "parse_errors": list(tuple(_get(parsed, "parse_errors", ()) or ())),
        },
        "records": {
            "index_work_ids": work_ids,
            "index_work_id_digest": hashlib.sha256(primary).hexdigest(),
            "occurrence_count": len(occurrences),
            "duplicate_occurrences": len(work_ids) - len(set(work_ids)),
            "occurrence_ledger_path": ledger_path,
        },
        "failure": dict(failure) if failure is not None else None,
    }
    # fix-A owns the page-evidence schema.  During parallel integration it adds
    # the six-condition field; emit it exactly when that schema advertises it.
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "axis1_search_page_evidence.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        page_definition = schema["definitions"]["page_evidence"]
        if "completion" in page_definition.get("required", ()):
            value["completion"] = _completion_for_schema(
                schema,
                page_definition["properties"]["completion"],
                conditions,
            )
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError):
        pass
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    relative = Path("pages") / (
        f"{_safe_component(str(_get(request, 'request_id')))}.a{attempt_number:02d}.json"
    )
    target = bundle / relative
    if target.exists():
        if target.read_bytes() != payload:
            raise FileExistsError(target)
    else:
        _atomic_create(target, payload)
    return relative


def finalize_bundle(
    bundle_root: str | os.PathLike[str],
    *,
    registration_epoch: str,
    registration_commit: str,
    catalog_sha256: str,
) -> Path:
    """Publish the exact-set manifest and its self digest after durable artifacts."""

    root = Path(bundle_root)
    excluded = {"manifest.json", "MANIFEST.sha256", "README.md"}
    regular: list[str] = []
    for current_root, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(current_root)
        if any((current / name).is_symlink() for name in dirnames):
            raise ValueError("bundle contains a symlinked directory")
        for filename in filenames:
            path = current / filename
            if path.is_symlink() or not path.is_file():
                raise ValueError("bundle contains a non-regular file")
            relative = path.relative_to(root).as_posix()
            if relative not in excluded:
                regular.append(relative)
    regular.sort()
    entries = []
    for relative in regular:
        raw = (root / relative).read_bytes()
        entries.append({"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    manifest = {
        "schema_version": "izanagi-axis1-search-bundle-manifest/v1",
        "document_type": "bundle_manifest",
        "registration_epoch": registration_epoch,
        "registration_commit": registration_commit,
        "catalog_sha256": catalog_sha256,
        "bundle_root": ".",
        "path_set_rule": "manifest paths == bundle regular files - {manifest.json, MANIFEST.sha256, README.md}",
        "excluded_paths": ["manifest.json", "MANIFEST.sha256", "README.md"],
        "regular_file_paths": regular,
        "files": entries,
    }
    payload = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    target = root / "manifest.json"
    _atomic_replace(target, payload)
    digest = hashlib.sha256(payload).hexdigest().encode("ascii") + b"  manifest.json\n"
    _atomic_replace(root / "MANIFEST.sha256", digest)
    return target


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


def _load_completed_prefix(
    previous: str | os.PathLike[str] | Mapping[str, Any] | None,
    bundle_root: Path,
    *,
    leaf_query_id: str,
    pass_number: int,
    next_page_number: int,
) -> tuple[list[Any], list[Any], list[dict[str, Any]]]:
    checkpoint = _previous_checkpoint_value(previous)
    if checkpoint is None or checkpoint.get("leaf_query_id") != leaf_query_id:
        return [], [], []
    completed = checkpoint.get("completed_ledger")
    if not isinstance(completed, Mapping):
        raise PreflightError("checkpoint lacks completed ledger metadata")
    relative = Path(str(completed.get("path", "")))
    if relative.is_absolute() or ".." in relative.parts:
        raise PreflightError("checkpoint ledger path is unsafe")
    target = bundle_root / relative
    raw = target.read_bytes()
    if hashlib.sha256(raw).hexdigest() != completed.get("ledger_sha256"):
        raise PreflightError("checkpoint completed ledger digest mismatch")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PreflightError("checkpoint completed ledger is malformed") from exc
    if not isinstance(value, dict) or value.get("document_type") != "record_occurrence_ledger":
        raise PreflightError("checkpoint completed ledger is not a ledger object")
    if value.get("leaf_query_id") != leaf_query_id:
        raise PreflightError("checkpoint completed ledger names another leaf")
    occurrences_value = value.get("occurrences")
    if not isinstance(occurrences_value, list):
        raise PreflightError("checkpoint completed ledger occurrences are malformed")
    primary = "".join(
        f"{item}\n"
        for item in sorted(
            {
                str(row.get("index_work_id"))
                for row in occurrences_value
                if isinstance(row, Mapping) and row.get("index_work_id")
            }
        )
    ).encode("utf-8")
    if hashlib.sha256(primary).hexdigest() != completed.get("primary_key_digest"):
        raise PreflightError("checkpoint primary-key digest mismatch")

    pages: list[Any] = []
    contexts: list[dict[str, Any]] = []
    pages_dir = bundle_root / "pages"
    if pages_dir.is_dir():
        selected: dict[int, Mapping[str, Any]] = {}
        for path in pages_dir.glob("*.json"):
            try:
                evidence = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            identity = _get(evidence, "identity", {})
            if (
                _get(evidence, "document_type") == "page_evidence"
                and _get(identity, "leaf_query_id") == leaf_query_id
                and _get(identity, "pass_number") == pass_number
                and isinstance(_get(identity, "page_number"), int)
                and _get(identity, "page_number") < next_page_number
                and _get(evidence, "failure") is None
            ):
                page_number = int(_get(identity, "page_number"))
                attempt = int(_get(identity, "attempt_number", 0))
                if attempt >= int(_get(_get(selected.get(page_number, {}), "identity", {}), "attempt_number", -1)):
                    selected[page_number] = evidence
        for page_number in sorted(selected):
            evidence = selected[page_number]
            parse_value = dict(_get(evidence, "parse", {}))
            page_occurrences = [
                dict(item)
                for item in occurrences_value
                if isinstance(item, Mapping) and item.get("page_number") == page_number
            ]
            parse_value.update(
                {
                    "index": _get(_get(evidence, "identity", {}), "index"),
                    "occurrences": tuple(page_occurrences),
                }
            )
            pages.append(parse_value)
            request_value = _get(evidence, "request", {})
            response_value = _get(evidence, "response", {})
            context: dict[str, Any] = {
                "expected_interpreted_query": _get(request_value, "expected_interpreted_query"),
                "expected_position_in": _get(request_value, "position_in"),
                "expected_page_number": page_number,
                "response_ok": (
                    _get(response_value, "status") == 200
                    and _get(response_value, "content_type")
                    == REGISTERED_ENDPOINTS[str(_get(request_value, "host"))][1]
                    and _get(response_value, "final_url") == _get(request_value, "encoded_url")
                ),
                "evidence_complete": True,
            }
            if _get(_get(evidence, "identity", {}), "index") == "openalex":
                raw_relative = Path(str(_get(response_value, "body_path")))
                try:
                    body = _read_stored_raw(bundle_root / raw_relative)
                except (OSError, gzip.BadGzipFile, PreflightError) as exc:
                    raise PreflightError("checkpoint prefix raw evidence is unreadable") from exc
                context["actual_interpreted_structure"] = _openalex_oqo(body)
            contexts.append(context)
    if len(pages) != next_page_number:
        raise PreflightError("checkpoint prefix page evidence is incomplete")
    return pages, [dict(item) for item in occurrences_value], contexts


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
        bundle_root,
        leaf,
        pass_number,
        occurrences,
        registration_epoch=str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
        registration_commit=registration_commit,
        catalog_sha256=catalog_sha256,
        run_id=run_id,
        logical_query_id=str(_get(current_request, "logical_query_id")),
        index=index,
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
        "canonical_runner_argv": [
            "python3",
            "tools/run_axis1_search.py",
            "--registration-commit",
            registration_commit,
            "--catalog",
            catalog_path,
            "--bundle",
            os.fspath(bundle_root),
            "--run-id",
            run_id,
            "--checkpoint",
            "{checkpoint_path}",
        ],
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
            "canonicalization": "canonical JSON object v1; primary digest is sorted unique index_work_id lines",
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


def _run_leaf_impl(
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
    runtime_state_path = bundle / "state" / "runtime.json"
    host_limiter = limiter or HostLimiter(
        clock=clock, sleeper=sleeper, state_path=runtime_state_path
    )
    request = initial_request or builder(catalog, leaf_query_id, 0, None)
    index = str(_get(request, "index"))
    if index not in DEFAULT_MINIMUM_INTERVALS:
        raise ValueError(f"unsupported index: {index}")
    parse = parser or _default_parser(index)
    page_size = _page_size(catalog, index)
    pagination_kind = _pagination_kind(catalog, index)
    retry_delays = _retry_delays(catalog, index)
    logical_query = _logical_query(catalog, leaf_query_id)
    shard_lower = _get(logical_query, "shard_lower")
    shard_upper = _get(logical_query, "shard_upper")
    requires_independent = _independent_pass_required(catalog, leaf_query_id)
    wal_path = bundle / "wal" / f"{_safe_component(leaf_query_id)}.jsonl"
    if initial_request is not None and int(_get(initial_request, "page_number")) > 0:
        pages, occurrences, page_contexts = _load_completed_prefix(
            previous_checkpoint,
            bundle,
            leaf_query_id=leaf_query_id,
            pass_number=pass_number,
            next_page_number=int(_get(initial_request, "page_number")),
        )
    else:
        pages, occurrences, page_contexts = [], [], []
    if index == "openalex":
        expected_structure = _expected_openalex_oqo(catalog, leaf_query_id)
        for context in page_contexts:
            context["expected_interpreted_structure"] = expected_structure
    request_count = 0
    attempts_by_request = _attempt_counts(wal_path)
    latest_quota = _load_persisted_quota(runtime_state_path, index) if index == "openalex" else None
    previous_value = _previous_checkpoint_value(previous_checkpoint)
    parent_response_sha = (
        _get(_get(previous_value, "cursor_state", {}), "parent_response_sha256")
        if pages and previous_value is not None
        else None
    )
    checkpoint_path: str | None = None

    while True:
        if max_pages is not None and len(pages) >= max_pages:
            break
        registered_request = builder(
            catalog,
            leaf_query_id,
            int(_get(request, "page_number")),
            _get(request, "position_in"),
        )
        if not _requests_identical(request, registered_request):
            raise PreflightError("issuance request differs from the registered catalog request")
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
                second_pass_required=requires_independent,
            )
            checkpoint = write_checkpoint(bundle / "checkpoints", payload)
            finalize_bundle(
                bundle,
                registration_epoch=str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
                registration_commit=registration_commit,
                catalog_sha256=catalog_sha256,
            )
            return RunResult("paused_quota", request_count, tuple(pages), (), os.fspath(checkpoint), latest_quota, "quota_reserve")

        response: Response | None = None
        failure: str | None = None
        raw_path: Path | None = None
        request_id = str(_get(request, "request_id"))
        for retry_ordinal in range(len(retry_delays) + 1):
            raw_path = None
            if index == "openalex":
                latest_quota = _load_persisted_quota(runtime_state_path, index) or latest_quota
                if latest_quota is not None and not latest_quota.permits_next():
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
                        state="paused_quota",
                        resume_action="continue_cursor",
                        occurrences=occurrences,
                        quota=latest_quota,
                        canonical_runner_argv=canonical_runner_argv,
                        previous_checkpoint=previous_checkpoint,
                        last_attempt={
                            "state": "terminal",
                            "request_id": latest_quota.observed_request_id,
                            "attempt_number": attempts_by_request.get(latest_quota.observed_request_id, 0),
                            "failure": "quota_reserve",
                            "raw_evidence_path": None,
                        },
                        parent_response_sha256=parent_response_sha,
                        second_pass_required=requires_independent,
                    )
                    checkpoint = write_checkpoint(bundle / "checkpoints", payload)
                    finalize_bundle(
                        bundle,
                        registration_epoch=str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
                        registration_commit=registration_commit,
                        catalog_sha256=catalog_sha256,
                    )
                    return RunResult(
                        "paused_quota",
                        request_count,
                        tuple(pages),
                        (),
                        os.fspath(checkpoint),
                        latest_quota,
                        "quota_reserve",
                    )
            attempt_number = attempts_by_request.get(request_id, 0) + 1
            attempts_by_request[request_id] = attempt_number
            wal_times: dict[str, str | None] = {
                "prepared": None,
                "issued": None,
                "response_stored": None,
                "parsed": None,
                "terminal": None,
            }
            wal_times["prepared"] = append_attempt_state(
                wal_path, request_id, attempt_number, "prepared", clock=clock
            )["at"]
            host_limiter.acquire(str(_get(request, "host")), _minimum_interval(catalog, index))
            wal_times["issued"] = append_attempt_state(
                wal_path, request_id, attempt_number, "issued", clock=clock
            )["at"]
            request_count += 1
            try:
                response = transport.get(request)
                raw_path = _store_raw_body(bundle, request_id, attempt_number, response.body)
                wal_times["response_stored"] = append_attempt_state(
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
                )["at"]
                if index == "openalex":
                    observed_quota = observe_quota(response, request_id, clock())
                    has_quota_evidence = any(
                        value is not None
                        for value in (
                            observed_quota.limit,
                            observed_quota.remaining,
                            observed_quota.credits_per_request,
                            observed_quota.reset_seconds,
                            observed_quota.cost_usd,
                        )
                    )
                    if response.status == 200 or has_quota_evidence:
                        latest_quota = _merge_quota(latest_quota, observed_quota)
                        _persist_quota(runtime_state_path, index, latest_quota)
                if response.status == 200:
                    failure = None
                    break
                failure = f"http_status_{response.status}"
                wal_times["parsed"] = append_attempt_state(wal_path, request_id, attempt_number, "parsed", payload={"parse_skipped": True}, clock=clock)["at"]
                wal_times["terminal"] = append_attempt_state(wal_path, request_id, attempt_number, "terminal", payload={"outcome": "retryable_failure", "reason_code": failure}, clock=clock)["at"]
                if response.status == 429:
                    break
            except Exception as exc:  # transport boundary; issued remains durable
                if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                    raise
                response = None
                failure = "transport_exception"
                raw_path = _store_raw_body(bundle, request_id, attempt_number, b"")
                failed_page = {
                    "index": index,
                    "declared_total": None,
                    "capacity_echo": None,
                    "actual_count": 0,
                    "interpreted_query": "",
                    "position_in": _get(request, "position_in"),
                    "position_out": None,
                    "occurrences": (),
                    "parse_errors": ("transport_error",),
                }
                failed_results = evaluate_page(
                    failed_page,
                    page_size=page_size,
                    expected_interpreted_query=str(_get(request, "expected_interpreted_query")),
                    expected_position_in=_get(request, "position_in"),
                    expected_page_number=int(_get(request, "page_number")),
                    pagination_kind=pagination_kind,
                    response_ok=False,
                    evidence_complete=True,
                )
                ledger_path, *_ = _write_ledger(
                    bundle,
                    leaf_query_id,
                    pass_number,
                    occurrences,
                    registration_epoch=str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
                    registration_commit=registration_commit,
                    catalog_sha256=catalog_sha256,
                    run_id=run_id,
                    logical_query_id=str(_get(request, "logical_query_id")),
                    index=index,
                )
                synthetic = Response(
                    599,
                    (("Content-Type", "application/octet-stream"),),
                    b"",
                    str(_get(request, "encoded_url")),
                    0.0,
                )
                _write_page_evidence(
                    bundle,
                    catalog=catalog,
                    request=request,
                    response=synthetic,
                    parsed=failed_page,
                    raw_path=raw_path,
                    ledger_path=ledger_path,
                    registration_commit=registration_commit,
                    catalog_path=catalog_path,
                    catalog_sha256=catalog_sha256,
                    run_id=run_id,
                    pass_number=pass_number,
                    window_number=window_number,
                    attempt_number=attempt_number,
                    parent_response_sha256=parent_response_sha,
                    quota=latest_quota,
                    wal_times=wal_times,
                    conditions=failed_results,
                    failure={"reason_code": "transport_error", "detail": str(exc) or "transport error"},
                )
            if retry_ordinal < len(retry_delays):
                sleeper(retry_delays[retry_ordinal])

        if response is None or response.status != 200:
            first = builder(catalog, leaf_query_id, 0, None)
            if response is not None and raw_path is not None:
                failed_page = {
                    "index": index,
                    "declared_total": None,
                    "capacity_echo": None,
                    "actual_count": 0,
                    "interpreted_query": "",
                    "position_in": _get(request, "position_in"),
                    "position_out": None,
                    "occurrences": (),
                    "parse_errors": (failure or "status_not_200",),
                }
                failed_results = evaluate_page(
                    failed_page,
                    page_size=page_size,
                    expected_interpreted_query=str(_get(request, "expected_interpreted_query")),
                    expected_position_in=_get(request, "position_in"),
                    expected_page_number=int(_get(request, "page_number")),
                    pagination_kind=pagination_kind,
                    response_ok=False,
                    evidence_complete=True,
                )
                ledger_path, *_ = _write_ledger(
                    bundle,
                    leaf_query_id,
                    pass_number,
                    occurrences,
                    registration_epoch=str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
                    registration_commit=registration_commit,
                    catalog_sha256=catalog_sha256,
                    run_id=run_id,
                    logical_query_id=str(_get(request, "logical_query_id")),
                    index=index,
                )
                _write_page_evidence(
                    bundle,
                    catalog=catalog,
                    request=request,
                    response=response,
                    parsed=failed_page,
                    raw_path=raw_path,
                    ledger_path=ledger_path,
                    registration_commit=registration_commit,
                    catalog_path=catalog_path,
                    catalog_sha256=catalog_sha256,
                    run_id=run_id,
                    pass_number=pass_number,
                    window_number=window_number,
                    attempt_number=attempts_by_request[request_id],
                    parent_response_sha256=parent_response_sha,
                    quota=latest_quota,
                    wal_times=wal_times,
                    conditions=failed_results,
                    failure={"reason_code": "status_not_200", "detail": failure or "non-200 response"},
                )
            paused_429 = response is not None and response.status == 429
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
                state="paused_quota" if paused_429 else "outcome_unknown",
                resume_action="continue_cursor" if paused_429 else "restart_branch",
                occurrences=occurrences,
                quota=latest_quota,
                canonical_runner_argv=canonical_runner_argv,
                previous_checkpoint=previous_checkpoint,
                last_attempt={"state": "issued" if response is None else "terminal", "request_id": request_id, "attempt_number": attempts_by_request[request_id], "failure": failure, "raw_evidence_path": raw_path.as_posix() if raw_path else None},
                parent_response_sha256=parent_response_sha,
                second_pass_required=requires_independent,
            )
            checkpoint = write_checkpoint(bundle / "checkpoints", payload)
            checkpoint_path = os.fspath(checkpoint)
            restart_dblp = index == "dblp" and _reserve_dblp_restart(runtime_state_path)
            finalize_bundle(
                bundle,
                registration_epoch=str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
                registration_commit=registration_commit,
                catalog_sha256=catalog_sha256,
            )
            if restart_dblp:
                sleeper(DBLP_RESTART_COOLDOWN_S)
                pages.clear()
                occurrences.clear()
                page_contexts.clear()
                parent_response_sha = None
                previous_checkpoint = checkpoint
                request = first
                continue
            return RunResult(
                "paused_quota" if paused_429 else "outcome_unknown",
                request_count,
                tuple(pages),
                (),
                checkpoint_path,
                latest_quota,
                "http_status_429" if paused_429 else failure,
            )

        try:
            parsed = _parse_registered_page(
                parse, response.body, int(_get(request, "page_number"))
            )
        except Exception as exc:
            wal_times["parsed"] = append_attempt_state(wal_path, request_id, attempts_by_request[request_id], "parsed", payload={"parse_error": str(exc)}, clock=clock)["at"]
            wal_times["terminal"] = append_attempt_state(wal_path, request_id, attempts_by_request[request_id], "terminal", payload={"outcome": "failed", "reason_code": "parse_error"}, clock=clock)["at"]
            failed_page = {
                "index": index,
                "declared_total": None,
                "capacity_echo": None,
                "actual_count": 0,
                "interpreted_query": "",
                "position_in": _get(request, "position_in"),
                "position_out": None,
                "occurrences": (),
                "parse_errors": (f"parse_error:{exc}",),
            }
            failed_results = evaluate_page(
                failed_page,
                page_size=page_size,
                expected_interpreted_query=str(_get(request, "expected_interpreted_query")),
                expected_position_in=_get(request, "position_in"),
                expected_page_number=int(_get(request, "page_number")),
                pagination_kind=pagination_kind,
                response_ok=True,
                evidence_complete=True,
            )
            ledger_path, *_ = _write_ledger(
                bundle,
                leaf_query_id,
                pass_number,
                occurrences,
                registration_epoch=str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
                registration_commit=registration_commit,
                catalog_sha256=catalog_sha256,
                run_id=run_id,
                logical_query_id=str(_get(request, "logical_query_id")),
                index=index,
            )
            _write_page_evidence(
                bundle,
                catalog=catalog,
                request=request,
                response=response,
                parsed=failed_page,
                raw_path=raw_path,
                ledger_path=ledger_path,
                registration_commit=registration_commit,
                catalog_path=catalog_path,
                catalog_sha256=catalog_sha256,
                run_id=run_id,
                pass_number=pass_number,
                window_number=window_number,
                attempt_number=attempts_by_request[request_id],
                parent_response_sha256=parent_response_sha,
                quota=latest_quota,
                wal_times=wal_times,
                conditions=failed_results,
                failure={"reason_code": "parse_error", "detail": str(exc) or "parse error"},
            )
            finalize_bundle(
                bundle,
                registration_epoch=str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
                registration_commit=registration_commit,
                catalog_sha256=catalog_sha256,
            )
            return RunResult("outcome_unknown", request_count, tuple(pages), (), checkpoint_path, latest_quota, "parse_error")

        wal_times["parsed"] = append_attempt_state(wal_path, request_id, attempts_by_request[request_id], "parsed", clock=clock)["at"]
        page_context = _response_context(catalog, request, response, raw_path)
        page_results = evaluate_page(
            parsed,
            page_size=page_size,
            **page_context,
        )
        failure_result = next((item for item in page_results if not item.passed), None)
        wal_times["terminal"] = append_attempt_state(
            wal_path,
            request_id,
            attempts_by_request[request_id],
            "terminal",
            payload={"outcome": "success" if failure_result is None else "failed", "reason_code": failure_result.reason_code if failure_result else None},
            clock=clock,
        )["at"]
        pages.append(parsed)
        occurrences.extend(tuple(_get(parsed, "occurrences", ()) or ()))
        page_contexts.append(page_context)
        ledger_path, *_ = _write_ledger(
            bundle,
            leaf_query_id,
            pass_number,
            occurrences,
            registration_epoch=str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
            registration_commit=registration_commit,
            catalog_sha256=catalog_sha256,
            run_id=run_id,
            logical_query_id=str(_get(request, "logical_query_id")),
            index=index,
        )
        _write_page_evidence(
            bundle,
            catalog=catalog,
            request=request,
            response=response,
            parsed=parsed,
            raw_path=raw_path,
            ledger_path=ledger_path,
            registration_commit=registration_commit,
            catalog_path=catalog_path,
            catalog_sha256=catalog_sha256,
            run_id=run_id,
            pass_number=pass_number,
            window_number=window_number,
            attempt_number=attempts_by_request[request_id],
            parent_response_sha256=parent_response_sha,
            quota=latest_quota,
            wal_times=wal_times,
            conditions=page_results,
            failure=(
                {"reason_code": failure_result.reason_code, "detail": failure_result.detail}
                if failure_result is not None
                and failure_result.reason_code
                in {
                    "parse_error",
                    "actual_count_mismatch",
                    "capacity_echo_mismatch",
                    "interpreted_query_mismatch",
                    "silent_truncation",
                    "missing_index_work_id",
                }
                else {"reason_code": "parse_error", "detail": failure_result.detail}
                if failure_result is not None
                else None
            ),
        )
        parent_response_sha = hashlib.sha256(response.body).hexdigest()
        if failure_result is not None:
            finalize_bundle(
                bundle,
                registration_epoch=str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
                registration_commit=registration_commit,
                catalog_sha256=catalog_sha256,
            )
            return RunResult("blocked_on_ruling", request_count, tuple(pages), tuple(page_results), checkpoint_path, latest_quota, failure_result.reason_code)
        position_out = _get(parsed, "position_out")
        if position_out is None:
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
                pagination_kind=pagination_kind,
                shard_lower=shard_lower,
                shard_upper=shard_upper,
                state="branch_complete",
                second_pass_required=requires_independent and pass_number > 1,
                second_pass_digest_matches=digest_matches,
                page_contexts=page_contexts,
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
                finalize_bundle(
                    bundle,
                    registration_epoch=str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
                    registration_commit=registration_commit,
                    catalog_sha256=catalog_sha256,
                )
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
            finalize_bundle(
                bundle,
                registration_epoch=str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
                registration_commit=registration_commit,
                catalog_sha256=catalog_sha256,
            )
            return RunResult(state, request_count, tuple(pages), tuple(leaf_results), checkpoint_path, latest_quota, reason)
        request = builder(catalog, leaf_query_id, int(_get(request, "page_number")) + 1, str(position_out))

    leaf_results = evaluate_leaf(
        pages,
        page_size=page_size,
        pagination_kind=pagination_kind,
        shard_lower=shard_lower,
        shard_upper=shard_upper,
        state="paused_quota",
        page_contexts=page_contexts,
    )
    finalize_bundle(
        bundle,
        registration_epoch=str(_get(catalog, "registration_epoch", "AX1-20260829-E1")),
        registration_commit=registration_commit,
        catalog_sha256=catalog_sha256,
    )
    return RunResult("paused_quota", request_count, tuple(pages), tuple(leaf_results), checkpoint_path, latest_quota, "page_limit")


def _resume_from_checkpoint_impl(
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
    return _run_leaf_impl(
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
    clock: Callable[[], float] = time.time,
    sleeper: Callable[[float], None] = time.sleep,
    limiter: HostLimiter | None = None,
    pass_number: int = 1,
    window_number: int = 1,
    canonical_runner_argv: Sequence[str] = ("tools/run_axis1_search.py",),
    previous_checkpoint: str | os.PathLike[str] | Mapping[str, Any] | None = None,
    max_pages: int | None = None,
) -> RunResult:
    """Production leaf path; requests and parsers come only from the catalog."""

    return _run_leaf_impl(
        catalog,
        leaf_query_id,
        run_id=run_id,
        registration_commit=registration_commit,
        catalog_path=catalog_path,
        bundle_root=bundle_root,
        transport=transport,
        preflight=preflight,
        clock=clock,
        sleeper=sleeper,
        limiter=limiter,
        pass_number=pass_number,
        window_number=window_number,
        canonical_runner_argv=canonical_runner_argv,
        previous_checkpoint=previous_checkpoint,
        max_pages=max_pages,
    )


def _run_leaf_for_test(
    catalog: Any,
    leaf_query_id: str,
    **kwargs: Any,
) -> RunResult:
    """Internal deterministic seam for fixture transports/builders/parsers."""

    return _run_leaf_impl(catalog, leaf_query_id, **kwargs)


def resume_from_checkpoint(
    checkpoint_path: str | os.PathLike[str],
    catalog: Any,
    *,
    transport: Transport,
    preflight: bool | VerificationResult | Callable[[], Any],
    clock: Callable[[], float] = time.time,
    sleeper: Callable[[float], None] = time.sleep,
    limiter: HostLimiter | None = None,
    canonical_runner_argv: Sequence[str] = ("tools/run_axis1_search.py",),
) -> RunResult:
    """Production resume path bound to the checkpoint and registered catalog."""

    return _resume_from_checkpoint_impl(
        checkpoint_path,
        catalog,
        transport=transport,
        preflight=preflight,
        clock=clock,
        sleeper=sleeper,
        limiter=limiter,
        canonical_runner_argv=canonical_runner_argv,
    )


def _resume_from_checkpoint_for_test(
    checkpoint_path: str | os.PathLike[str],
    catalog: Any,
    **kwargs: Any,
) -> RunResult:
    return _resume_from_checkpoint_impl(checkpoint_path, catalog, **kwargs)


__all__ = [
    "ALLOWED_HOSTS",
    "DBLP_RESTART_COOLDOWN_S",
    "DEFAULT_MINIMUM_INTERVALS",
    "HTTPSOnlyTransport",
    "HostLimiter",
    "MAX_RESPONSE_BYTES",
    "PreflightError",
    "QUOTA_RESERVE_CREDITS",
    "REGISTERED_ENDPOINTS",
    "QuotaObservation",
    "Response",
    "RunResult",
    "Transport",
    "TransportError",
    "control_leaf_query_id",
    "finalize_bundle",
    "observe_quota",
    "resume_from_checkpoint",
    "run_leaf",
]
