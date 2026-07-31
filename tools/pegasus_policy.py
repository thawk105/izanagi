"""Fail-closed Pegasus site classification and test-worker policy.

This module is intentionally stdlib-only and is imported canonically as
``pegasus_policy`` after callers add ``<repo>/tools`` to ``sys.path``.
Operating-system observation is confined to :func:`observe_site`; the
classification and worker-policy functions consume only explicit values.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
import os
import re
import socket


class SitePolicyError(ValueError):
    """The observed identity is invalid, ambiguous, or unsafe to use."""


class SiteKind(str, Enum):
    PEGASUS_LOGIN = "PEGASUS_LOGIN"
    PEGASUS_COMPUTE = "PEGASUS_COMPUTE"
    OTHER = "OTHER"


PEGASUS_LOGIN = SiteKind.PEGASUS_LOGIN
PEGASUS_COMPUTE = SiteKind.PEGASUS_COMPUTE
OTHER = SiteKind.OTHER

_PEGASUS_DOMAIN = "ccs.tsukuba.ac.jp"
_LOGIN_SHORT_NAMES = frozenset({"pegasus01", "pegasus02", "pegasus03"})
_COMPUTE_SHORT_RE = re.compile(r"bnode[0-9]{3}\Z", re.ASCII)
_PBS_JOB_ID_RE = re.compile(r"(?:0:)?([0-9]+)\.nqsv\Z", re.ASCII)
_HOST_LABEL_RE = re.compile(
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z",
    re.ASCII,
)

_ERR_HOSTNAME = "hostname must be a non-empty ASCII DNS name"
_ERR_AFFINITY = (
    "CPU affinity must be a non-empty set of unique non-negative integers"
)
_ERR_PBS = "PBS_JOBID must be an NQSV job ID"
_ERR_LOGIN_PBS = "Pegasus login host must not have PBS_JOBID"
_ERR_COMPUTE_PBS = "Pegasus compute host requires an NQSV PBS_JOBID"
_ERR_UNKNOWN_NQSV = "NQSV PBS_JOBID is inconsistent with hostname"
_ERR_UNKNOWN_DOMAIN = "Pegasus domain hostname is not recognized"
_ERR_SIMILAR_HOST = "Pegasus-like hostname is not recognized"
_ERR_LOGIN_WORKERS = "test workers cannot be resolved on a Pegasus login host"
_ERR_WORKERS = (
    "test worker count must be auto, logical, or an integer greater than or "
    "equal to zero"
)
_ERR_OVERSUBSCRIBE = "test worker count exceeds compute CPU affinity"


class _AffinityUnavailable(Exception):
    """The operating system has no usable process-affinity API."""


@dataclass(frozen=True, slots=True)
class SiteObservation:
    """An immutable, normalized snapshot of the values used by this policy."""

    hostname_raw: str
    hostname_canonical: str
    pbs_job_id_raw: str | None
    pbs_job_id_normalized: str | None
    affinity_cpus: tuple[int, ...]
    site_kind: SiteKind

    def __post_init__(self) -> None:
        try:
            canonical = _canonicalize_hostname(self.hostname_raw)
            normalized_affinity = _normalize_affinity(self.affinity_cpus)
        except SitePolicyError:
            raise
        if canonical != self.hostname_canonical:
            raise SitePolicyError("site observation hostname fields are inconsistent")
        if normalized_affinity != self.affinity_cpus:
            raise SitePolicyError("site observation affinity field is not canonical")
        if not isinstance(self.site_kind, SiteKind):
            raise SitePolicyError("site observation has an invalid site kind")
        if self.site_kind is OTHER:
            if self.pbs_job_id_raw is None:
                if self.pbs_job_id_normalized is not None:
                    raise SitePolicyError(
                        "site observation PBS fields are inconsistent"
                    )
            else:
                if (
                    not isinstance(self.pbs_job_id_raw, str)
                    or not self.pbs_job_id_raw
                    or self.pbs_job_id_normalized is not None
                    or _PBS_JOB_ID_RE.fullmatch(self.pbs_job_id_raw) is not None
                ):
                    raise SitePolicyError(
                        "site observation PBS fields are inconsistent"
                    )
        elif self.pbs_job_id_raw is None:
            if self.pbs_job_id_normalized is not None:
                raise SitePolicyError("site observation PBS fields are inconsistent")
        else:
            normalized_pbs = _normalize_pbs_job_id(self.pbs_job_id_raw)
            if normalized_pbs != self.pbs_job_id_normalized:
                raise SitePolicyError("site observation PBS fields are inconsistent")

    @property
    def raw_hostname(self) -> str:
        """Compatibility spelling for callers that lead with ``raw``."""

        return self.hostname_raw

    @property
    def hostname(self) -> str:
        """The canonical hostname."""

        return self.hostname_canonical

    @property
    def normalized_hostname(self) -> str:
        """Compatibility spelling for the canonical hostname."""

        return self.hostname_canonical

    @property
    def raw_pbs_job_id(self) -> str | None:
        """Compatibility spelling for callers that lead with ``raw``."""

        return self.pbs_job_id_raw

    @property
    def pbs_job_id(self) -> str | None:
        """The normalized PBS job ID."""

        return self.pbs_job_id_normalized

    @property
    def normalized_pbs_job_id(self) -> str | None:
        """Compatibility spelling for the normalized PBS job ID."""

        return self.pbs_job_id_normalized

    @property
    def site(self) -> SiteKind:
        """Compatibility spelling for the classified site kind."""

        return self.site_kind

    @property
    def available_cpu_count(self) -> int:
        return len(self.affinity_cpus)


def _canonicalize_hostname(raw_hostname: object) -> str:
    if not isinstance(raw_hostname, str) or not raw_hostname:
        raise SitePolicyError(_ERR_HOSTNAME)
    try:
        raw_hostname.encode("ascii")
    except UnicodeEncodeError:
        raise SitePolicyError(_ERR_HOSTNAME) from None

    canonical = raw_hostname.lower()
    if canonical.endswith("."):
        canonical = canonical[:-1]
    if not canonical or len(canonical) > 253:
        raise SitePolicyError(_ERR_HOSTNAME)
    labels = canonical.split(".")
    if any(not _HOST_LABEL_RE.fullmatch(label) for label in labels):
        raise SitePolicyError(_ERR_HOSTNAME)
    return canonical


def _normalize_affinity(raw_affinity: object) -> tuple[int, ...]:
    if isinstance(raw_affinity, (str, bytes, bytearray, bool)):
        raise SitePolicyError(_ERR_AFFINITY)
    try:
        values = tuple(raw_affinity)  # type: ignore[arg-type]
    except Exception:
        raise SitePolicyError(_ERR_AFFINITY) from None
    if not values:
        raise SitePolicyError(_ERR_AFFINITY)
    if any(
        not isinstance(cpu, int) or isinstance(cpu, bool) or cpu < 0
        for cpu in values
    ):
        raise SitePolicyError(_ERR_AFFINITY)
    if len(set(values)) != len(values):
        raise SitePolicyError(_ERR_AFFINITY)
    return tuple(sorted(values))


def _normalize_pbs_job_id(raw_pbs_job_id: object) -> str:
    if not isinstance(raw_pbs_job_id, str) or not raw_pbs_job_id:
        raise SitePolicyError(_ERR_PBS)
    match = _PBS_JOB_ID_RE.fullmatch(raw_pbs_job_id)
    if match is None:
        raise SitePolicyError(_ERR_PBS)
    return f"{match.group(1)}.nqsv"


def _short_name_for_known_host(hostname: str) -> str | None:
    suffix = f".{_PEGASUS_DOMAIN}"
    if hostname.endswith(suffix):
        return hostname[: -len(suffix)]
    if "." not in hostname:
        return hostname
    return None


def classify_site(
    hostname: object,
    pbs_job_id: object,
    affinity: Iterable[int] | object,
) -> SiteObservation:
    """Classify already-observed values without performing OS or DNS access."""

    canonical_hostname = _canonicalize_hostname(hostname)
    affinity_cpus = _normalize_affinity(affinity)
    short_name = _short_name_for_known_host(canonical_hostname)

    if short_name in _LOGIN_SHORT_NAMES:
        if pbs_job_id is not None:
            raise SitePolicyError(_ERR_LOGIN_PBS)
        return SiteObservation(
            hostname_raw=hostname,
            hostname_canonical=canonical_hostname,
            pbs_job_id_raw=None,
            pbs_job_id_normalized=None,
            affinity_cpus=affinity_cpus,
            site_kind=PEGASUS_LOGIN,
        )

    if short_name is not None and _COMPUTE_SHORT_RE.fullmatch(short_name):
        if pbs_job_id is None:
            raise SitePolicyError(_ERR_COMPUTE_PBS)
        normalized_pbs = _normalize_pbs_job_id(pbs_job_id)
        return SiteObservation(
            hostname_raw=hostname,
            hostname_canonical=canonical_hostname,
            pbs_job_id_raw=pbs_job_id,
            pbs_job_id_normalized=normalized_pbs,
            affinity_cpus=affinity_cpus,
            site_kind=PEGASUS_COMPUTE,
        )

    if (
        canonical_hostname == _PEGASUS_DOMAIN
        or canonical_hostname.endswith(f".{_PEGASUS_DOMAIN}")
    ):
        raise SitePolicyError(_ERR_UNKNOWN_DOMAIN)

    first_label = canonical_hostname.split(".", 1)[0]
    if first_label.startswith(("pegasus", "bnode")):
        raise SitePolicyError(_ERR_SIMILAR_HOST)

    normalized_pbs = None
    if pbs_job_id is not None:
        if not isinstance(pbs_job_id, str) or not pbs_job_id:
            raise SitePolicyError(_ERR_PBS)
        if _PBS_JOB_ID_RE.fullmatch(pbs_job_id) is not None:
            raise SitePolicyError(_ERR_UNKNOWN_NQSV)

    return SiteObservation(
        hostname_raw=hostname,
        hostname_canonical=canonical_hostname,
        pbs_job_id_raw=pbs_job_id,
        pbs_job_id_normalized=normalized_pbs,
        affinity_cpus=affinity_cpus,
        site_kind=OTHER,
    )


def _system_affinity(pid: int) -> Iterable[int]:
    getter = getattr(os, "sched_getaffinity", None)
    if getter is None:
        raise _AffinityUnavailable
    try:
        return getter(pid)
    except NotImplementedError:
        raise _AffinityUnavailable from None


def _system_cpu_count() -> object:
    return os.cpu_count()


def observe_site(
    *,
    hostname_fn: Callable[[], object] = socket.gethostname,
    environ: Mapping[str, object] | None = None,
    affinity_fn: Callable[[int], object] = _system_affinity,
    cpu_count_fn: Callable[[], object] = _system_cpu_count,
) -> SiteObservation:
    """Observe the local site through injectable, independently-failing seams."""

    try:
        hostname = hostname_fn()
    except Exception:
        raise SitePolicyError("hostname observation failed") from None

    source_environ = os.environ if environ is None else environ
    try:
        pbs_job_id = source_environ.get("PBS_JOBID")
    except Exception:
        raise SitePolicyError("PBS_JOBID observation failed") from None

    try:
        affinity = affinity_fn(0)
    except _AffinityUnavailable:
        try:
            identity = classify_site(hostname, pbs_job_id, (0,))
        except SitePolicyError:
            raise
        if identity.site_kind is not OTHER:
            raise SitePolicyError("CPU affinity observation failed") from None
        try:
            cpu_count = cpu_count_fn()
        except Exception:
            raise SitePolicyError("CPU affinity observation failed") from None
        if (
            not isinstance(cpu_count, int)
            or isinstance(cpu_count, bool)
            or cpu_count <= 0
        ):
            raise SitePolicyError("CPU affinity observation failed")
        affinity = range(cpu_count)
    except Exception:
        raise SitePolicyError("CPU affinity observation failed") from None

    return classify_site(hostname, pbs_job_id, affinity)


def default_pytest_workers(observation: SiteObservation) -> int:
    """Return the default pytest worker count for a classified non-login site."""

    if not isinstance(observation, SiteObservation):
        raise SitePolicyError("site observation is required")
    if observation.site_kind is PEGASUS_LOGIN:
        raise SitePolicyError(_ERR_LOGIN_WORKERS)
    if observation.site_kind is PEGASUS_COMPUTE:
        return len(observation.affinity_cpus)
    if observation.site_kind is OTHER:
        return min(len(observation.affinity_cpus), 32)
    raise SitePolicyError("site observation has an invalid site kind")


def resolve_test_workers(
    explicit_workers: int | str | None,
    observation: SiteObservation,
) -> int | str:
    """Resolve pytest workers without widening the build-jobs contract.

    ``auto`` and ``logical`` remain symbolic on OTHER so pytest-xdist retains
    its existing interpretation.  On compute they resolve to the affinity
    ceiling, while integer zero remains the explicit serial spelling.
    """

    if not isinstance(observation, SiteObservation):
        raise SitePolicyError("site observation is required")
    if observation.site_kind is PEGASUS_LOGIN:
        raise SitePolicyError(_ERR_LOGIN_WORKERS)
    if explicit_workers is None:
        return default_pytest_workers(observation)
    if isinstance(explicit_workers, str):
        if explicit_workers not in {"auto", "logical"}:
            raise SitePolicyError(_ERR_WORKERS)
        if observation.site_kind is PEGASUS_COMPUTE:
            return len(observation.affinity_cpus)
        if observation.site_kind is OTHER:
            return explicit_workers
        raise SitePolicyError("site observation has an invalid site kind")
    if not isinstance(explicit_workers, int) or isinstance(explicit_workers, bool):
        raise SitePolicyError(_ERR_WORKERS)
    if explicit_workers < 0:
        raise SitePolicyError(_ERR_WORKERS)
    if (
        observation.site_kind is PEGASUS_COMPUTE
        and explicit_workers > len(observation.affinity_cpus)
    ):
        raise SitePolicyError(_ERR_OVERSUBSCRIBE)
    return explicit_workers


__all__ = [
    "OTHER",
    "PEGASUS_COMPUTE",
    "PEGASUS_LOGIN",
    "SiteKind",
    "SiteObservation",
    "SitePolicyError",
    "classify_site",
    "default_pytest_workers",
    "observe_site",
    "resolve_test_workers",
]
