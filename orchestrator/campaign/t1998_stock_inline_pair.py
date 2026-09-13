# -*- coding: utf-8 -*-
"""T-1998 balanced stock-inline pair consumer.

The consumer is deliberately narrower than the producer: it accepts only the
pre-registered no-backoff and fixed-5 arms, and it never chooses a point from
the measured values.

The consumer checks equality of the recorded full-version digests across arms.
Because the recovered artifacts read by this consumer (result.json,
reservation.json, and the campaign lock and WAL) omit the full-version manifest,
it does not recompute the digest or verify its cryptographic correspondence to
the recorded identity projection. Replacing both arms' digests with the same
different value therefore cannot be rejected at this layer.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shlex
import stat
import statistics
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Mapping

from . import campaign_lock, env_contract
from .artifact_admission import (
    ArtifactAdmissionError,
    CampaignReadPurpose,
    require_admitted_campaign,
)
from .model import (
    COMMIT_CONTRACT_SHA256_KEY,
    STAGE_ABORT,
    STAGE_BENCH_DONE,
    STAGE_BUILD_DONE,
    STAGE_BUILD_START,
    STAGE_COMMIT,
    STAGE_VERIFY_DONE,
)


ArmName = Literal["baseline", "target"]
RejectionArm = Literal["baseline", "target", "unknown"]

WORKLOAD = "balanced"
TARGET_FIXED_US = 5
EXPECTED_PRODUCER_POINT_COUNT = 8
EXPECTED_SAMPLE_COUNT = 5
BASELINE_FLAGS = MappingProxyType({
    "NO_WAIT_LOCKING_IN_VALIDATION": 1,
    "NO_WAIT_OF_TICTOC": 0,
    "WAL": 0,
    "BACK_OFF": 0,
    "BACKOFF_FIXED": -1,
})
TARGET_FLAGS = MappingProxyType({
    **dict(BASELINE_FLAGS),
    "BACK_OFF": 1,
    "BACKOFF_FIXED": TARGET_FIXED_US,
})
BASELINE_CANONICAL_GENOME = (
    "silo|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,"
    "NO_WAIT_OF_TICTOC=0,WAL=0"
)
TARGET_CANONICAL_GENOME = (
    "silo|BACKOFF_FIXED=5,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,"
    "NO_WAIT_OF_TICTOC=0,WAL=0"
)
T1998_PREREGISTRATION_PATH = (
    "docs/t1998-balanced-stock-inline-preregistration.md"
)
T1998_PREREGISTRATION_SPEC_BEGIN = "<!-- IZANAGI-T1998-SPEC-BEGIN -->"
T1998_PREREGISTRATION_SPEC_END = "<!-- IZANAGI-T1998-SPEC-END -->"
T1998_PREREGISTRATION_SCHEMA_VERSION = (
    "izanagi-t1998-balanced-stock-inline-preregistration/v1"
)
# Binds the preregistration version under which the artifacts were measured.
MEASUREMENT_TIME_PREREGISTRATION_SHA256 = (
    "464e3af59a1ef0f776cad022a52ab87e1fdf2709abfc2062c058203bc813719c"
)
# Binds the preregistration version currently supplied as the analysis rules.
CURRENT_PREREGISTRATION_SHA256 = (
    "464e3af59a1ef0f776cad022a52ab87e1fdf2709abfc2062c058203bc813719c"
)

_SHA256_CHARS = frozenset("0123456789abcdef")
_T1998_PREREGISTRATION_SPEC_RE = re.compile(
    re.escape(T1998_PREREGISTRATION_SPEC_BEGIN)
    + r"[ \t]*\r?\n```json[ \t]*\r?\n(.*?)\r?\n```[ \t]*\r?\n"
    + re.escape(T1998_PREREGISTRATION_SPEC_END),
    re.DOTALL,
)
_PAIR_STAGES = frozenset({
    STAGE_BUILD_START,
    STAGE_BUILD_DONE,
    STAGE_VERIFY_DONE,
    STAGE_BENCH_DONE,
    STAGE_COMMIT,
})


def _is_lower_hex(value: object, width: int) -> bool:
    return (
        type(value) is str
        and len(value) == width
        and set(value) <= _SHA256_CHARS
    )


def _gitlink_matches(expected_full: str, actual: object) -> bool:
    if (
        type(actual) is not str
        or not (7 <= len(actual) <= 40)
        or not _is_lower_hex(actual, len(actual))
    ):
        return False
    if len(actual) == 40:
        return actual == expected_full
    return expected_full.startswith(actual)


def _pair_arm_from_genome(value: object) -> ArmName | None:
    """Return the fixed arm for an exact canonical pair genome."""
    if value == BASELINE_CANONICAL_GENOME:
        return "baseline"
    if value == TARGET_CANONICAL_GENOME:
        return "target"
    return None


def _genome_diagnostic_arm(value: object) -> tuple[bool, RejectionArm]:
    """Return diagnostic-key presence and any pair arm recoverable without it."""
    if type(value) is not str:
        return False, "unknown"
    engine, separator, raw_flags = value.partition("|")
    if separator != "|":
        return False, "unknown"
    flags = raw_flags.split(",")
    diagnostic_flags = [
        flag for flag in flags if flag.partition("=")[0] == "BACKOFF_NOINLINE"
    ]
    if not diagnostic_flags:
        return False, "unknown"
    without_marker_flags = [
        flag for flag in flags
        if flag.partition("=")[0] != "BACKOFF_NOINLINE"
    ]
    without_marker = f"{engine}|{','.join(without_marker_flags)}"
    if without_marker == BASELINE_CANONICAL_GENOME:
        return True, "baseline"
    if without_marker == TARGET_CANONICAL_GENOME:
        return True, "target"
    return True, "unknown"


@dataclass(frozen=True, slots=True)
class T1998CommonPreregisteredIdentity:
    """Identity fields which must be common to both selected arms."""

    repository_commit: str
    ccbench_gitlink_commit: str
    environment_contract_sha256: str
    launcher_script_sha256: str

    def __post_init__(self) -> None:
        if not _is_lower_hex(self.repository_commit, 40):
            raise ValueError("repository_commit must be exact lowercase hex40")
        if not _is_lower_hex(self.ccbench_gitlink_commit, 40):
            raise ValueError("ccbench_gitlink_commit must be exact lowercase hex40")
        if not _is_lower_hex(self.environment_contract_sha256, 64):
            raise ValueError(
                "environment_contract_sha256 must be exact lowercase sha256"
            )
        if not _is_lower_hex(self.launcher_script_sha256, 64):
            raise ValueError("launcher_script_sha256 must be exact lowercase sha256")


@dataclass(frozen=True, slots=True)
class T1998ArmPreregisteredIdentity:
    """Genome-dependent identity; baseline and target normally differ."""

    canonical_genome: str
    source_bytes_sha256: str

    def __post_init__(self) -> None:
        if type(self.canonical_genome) is not str or not self.canonical_genome:
            raise ValueError("canonical_genome must be a non-empty exact string")
        if not _is_lower_hex(self.source_bytes_sha256, 64):
            raise ValueError("source_bytes_sha256 must be exact lowercase sha256")


@dataclass(frozen=True, slots=True)
class T1998PreregisteredIdentity:
    """Prospective seam only; this module contains no pre-registration values."""

    common: T1998CommonPreregisteredIdentity
    baseline: T1998ArmPreregisteredIdentity
    target: T1998ArmPreregisteredIdentity

    def __post_init__(self) -> None:
        if type(self.common) is not T1998CommonPreregisteredIdentity:
            raise TypeError("common must be exact T1998CommonPreregisteredIdentity")
        if type(self.baseline) is not T1998ArmPreregisteredIdentity:
            raise TypeError("baseline must be exact T1998ArmPreregisteredIdentity")
        if type(self.target) is not T1998ArmPreregisteredIdentity:
            raise TypeError("target must be exact T1998ArmPreregisteredIdentity")


def _exact_object(
    value: object,
    keys: set[str],
    *,
    field: str,
) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        observed = sorted(value) if type(value) is dict else type(value).__name__
        raise ValueError(f"{field} key set mismatch: {observed!r}")
    return value


def _parse_preregistration(raw: bytes) -> dict[str, object]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("preregistration document must be UTF-8") from exc
    matches = _T1998_PREREGISTRATION_SPEC_RE.findall(text)
    if (
        len(matches) != 1
        or text.count(T1998_PREREGISTRATION_SPEC_BEGIN) != 1
        or text.count(T1998_PREREGISTRATION_SPEC_END) != 1
    ):
        raise ValueError("preregistration spec block must appear exactly once")
    try:
        value = json.loads(
            matches[0],
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"preregistration spec must be strict JSON: {exc}") from exc
    document = _exact_object(
        value,
        {"schema_version", "common", "baseline", "target"},
        field="preregistration spec",
    )
    if document["schema_version"] != T1998_PREREGISTRATION_SCHEMA_VERSION:
        raise ValueError("preregistration schema_version mismatch")
    common = _exact_object(
        document["common"],
        {
            "ccbench_gitlink_commit",
            "environment_contract_sha256",
            "launcher_script_sha256",
        },
        field="preregistration common",
    )
    baseline = _exact_object(
        document["baseline"],
        {"canonical_genome", "source_bytes_sha256"},
        field="preregistration baseline",
    )
    target = _exact_object(
        document["target"],
        {"canonical_genome", "source_bytes_sha256"},
        field="preregistration target",
    )
    for field, item in (
        ("schema_version", document["schema_version"]),
        ("common.ccbench_gitlink_commit", common["ccbench_gitlink_commit"]),
        (
            "common.environment_contract_sha256",
            common["environment_contract_sha256"],
        ),
        ("common.launcher_script_sha256", common["launcher_script_sha256"]),
        ("baseline.canonical_genome", baseline["canonical_genome"]),
        ("baseline.source_bytes_sha256", baseline["source_bytes_sha256"]),
        ("target.canonical_genome", target["canonical_genome"]),
        ("target.source_bytes_sha256", target["source_bytes_sha256"]),
    ):
        if type(item) is not str:
            raise ValueError(f"preregistration {field} must be an exact string")
    if not _is_lower_hex(common["ccbench_gitlink_commit"], 40):
        raise ValueError("preregistration common.ccbench_gitlink_commit is invalid")
    for field, item in (
        (
            "common.environment_contract_sha256",
            common["environment_contract_sha256"],
        ),
        ("common.launcher_script_sha256", common["launcher_script_sha256"]),
        ("baseline.source_bytes_sha256", baseline["source_bytes_sha256"]),
        ("target.source_bytes_sha256", target["source_bytes_sha256"]),
    ):
        if not _is_lower_hex(item, 64):
            raise ValueError(f"preregistration {field} is not lowercase hex64")
    if not baseline["canonical_genome"] or not target["canonical_genome"]:
        raise ValueError("preregistration canonical_genome must be non-empty")
    return {
        "common": common,
        "baseline": baseline,
        "target": target,
    }


def _identity_from_preregistration(
    raw: bytes,
    repository_commit: str,
) -> T1998PreregisteredIdentity:
    spec = _parse_preregistration(raw)
    common = spec["common"]
    baseline = spec["baseline"]
    target = spec["target"]
    assert type(common) is dict
    assert type(baseline) is dict
    assert type(target) is dict
    return T1998PreregisteredIdentity(
        common=T1998CommonPreregisteredIdentity(
            repository_commit=repository_commit,
            ccbench_gitlink_commit=common["ccbench_gitlink_commit"],
            environment_contract_sha256=common["environment_contract_sha256"],
            launcher_script_sha256=common["launcher_script_sha256"],
        ),
        baseline=T1998ArmPreregisteredIdentity(
            canonical_genome=baseline["canonical_genome"],
            source_bytes_sha256=baseline["source_bytes_sha256"],
        ),
        target=T1998ArmPreregisteredIdentity(
            canonical_genome=target["canonical_genome"],
            source_bytes_sha256=target["source_bytes_sha256"],
        ),
    )


def _read_preregistration_bytes(repo_root: Path) -> bytes:
    path = repo_root / T1998_PREREGISTRATION_PATH
    try:
        info = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ValueError("preregistration document is missing") from exc
    if not stat.S_ISREG(info.st_mode) or resolved != path:
        raise ValueError("preregistration document must be a regular non-symlink")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ValueError("preregistration document is unreadable") from exc


def _read_only_git_env() -> dict[str, str]:
    """Return an environment which cannot redirect read-only Git probes."""
    env = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
    ):
        env.pop(name, None)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def _preregistration_blob(repo_root: Path, repository_commit: str) -> bytes:
    try:
        completed = subprocess.run(
            [
                "git",
                "--no-replace-objects",
                "-C",
                os.fspath(repo_root),
                "show",
                f"{repository_commit}:{T1998_PREREGISTRATION_PATH}",
            ],
            check=False,
            capture_output=True,
            env=_read_only_git_env(),
        )
    except OSError as exc:
        raise ValueError("cannot run git show for preregistration blob") from exc
    if completed.returncode != 0:
        raise ValueError("cannot read preregistration blob from repository commit")
    return completed.stdout


def load_preregistration(
    repo_root: str | Path,
    prereg_commit: str,
) -> T1998PreregisteredIdentity:
    """Load the exact committed T-1998 preregistration identity."""
    if not _is_lower_hex(prereg_commit, 40):
        raise ValueError("prereg_commit must be exact lowercase hex40")
    root = Path(repo_root).resolve()
    try:
        ancestor = subprocess.run(
            [
                "git", "--no-replace-objects", "-C", os.fspath(root),
                "merge-base", "--is-ancestor", prereg_commit, "HEAD",
            ],
            check=False,
            capture_output=True,
            env=_read_only_git_env(),
        )
    except OSError as exc:
        raise ValueError("cannot check prereg_commit ancestry") from exc
    if ancestor.returncode != 0:
        raise ValueError("prereg_commit must be an ancestor of HEAD")
    raw = _read_preregistration_bytes(root)
    blob = _preregistration_blob(root, prereg_commit)
    if raw != blob:
        raise ValueError("working preregistration bytes differ from commit blob")
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != CURRENT_PREREGISTRATION_SHA256:
        raise ValueError("working preregistration sha256 is not the current pin")
    return _identity_from_preregistration(raw, prereg_commit)


class T1998PairRejected(RuntimeError):
    """Structured, arm-attributed fail-closed refusal."""

    def __init__(
        self,
        code: str,
        *,
        field: str,
        expected: object,
        actual: object,
        arm: RejectionArm,
    ) -> None:
        if arm not in {"baseline", "target", "unknown"}:
            raise ValueError("rejection arm must be baseline, target, or unknown")
        self.code = code
        self.field = field
        self.expected = expected
        self.actual = actual
        self.arm = arm
        super().__init__(
            f"{code}: arm={arm} field={field} "
            f"expected={expected!r} actual={actual!r}"
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
            "arm": self.arm,
        }


@dataclass(frozen=True, slots=True)
class T1998ArmDecision:
    arm: ArmName
    canonical_genome: str
    flags: tuple[tuple[str, int], ...]
    variant_id: str
    samples: tuple[float | int, ...]
    median_tps: float | int
    cv: float
    unstable: bool
    performance_binary_sha256: str
    commit_receipt_id: str


@dataclass(frozen=True, slots=True)
class T1998IdentityDecision:
    repository_commit: str
    ccbench_gitlink_commit: str
    campaign_ccbench_gitlink_prefix: str
    wal_ccbench_gitlink_prefixes: tuple[str, ...]
    abbreviated_gitlink_is_full_identity: bool
    environment_contract_sha256: str
    launcher_script_sha256: str
    launcher_binding_scope: str
    submitter_identity_recoverable: bool
    source_digest_binding_required: bool
    explicit_diagnostic_marker_check_is_sufficient: bool
    toolchain_manifest: Mapping[str, Any]
    toolchain_record_sha256: str
    campaign_id: str
    lock_sha256: str
    wal_sha256: str


@dataclass(frozen=True, slots=True)
class T1998StockInlineDecision:
    status: Literal["accepted", "inconclusive"]
    reason: str
    baseline: T1998ArmDecision
    target: T1998ArmDecision
    identity: T1998IdentityDecision
    ratio: float | None
    improvement_percent: float | None


def _reject(
    code: str,
    field: str,
    expected: object,
    actual: object,
    arm: RejectionArm = "baseline",
) -> None:
    raise T1998PairRejected(
        code, field=field, expected=expected, actual=actual, arm=arm,
    )


def _require_equal(
    actual: object,
    expected: object,
    *,
    code: str,
    field: str,
    arm: RejectionArm = "baseline",
) -> None:
    if actual != expected:
        _reject(code, field, expected, actual, arm)


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _read_regular_json(path: Path, *, field: str) -> dict[str, Any]:
    try:
        info = path.lstat()
    except FileNotFoundError:
        _reject("producer-artifact-missing", field, "regular JSON file", "missing")
    if not stat.S_ISREG(info.st_mode):
        _reject(
            "producer-artifact-missing", field, "regular non-symlink JSON file",
            "non-regular-or-symlink",
        )
    try:
        raw = path.read_bytes()
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        _reject("producer-artifact-invalid", field, "valid finite JSON object", str(exc))
    if type(value) is not dict:
        _reject("producer-artifact-invalid", field, "JSON object", type(value).__name__)
    return value


def _freeze_json(value: Any) -> Any:
    if type(value) is dict:
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if type(value) is list:
        return tuple(_freeze_json(item) for item in value)
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _finite_positive(value: object) -> bool:
    return (
        type(value) in {int, float}
        and math.isfinite(value)
        and value > 0
    )


def _command_argv(value: object) -> list[str] | None:
    if type(value) is str:
        try:
            argv = shlex.split(value)
        except ValueError:
            return None
    elif type(value) is list and all(type(token) is str for token in value):
        argv = list(value)
    else:
        return None
    return argv if argv else None


def _cmake_define_values(argv: list[str], name: str) -> list[str]:
    """Return values after normalizing ``-DNAME[:TYPE]=VALUE`` tokens."""
    values: list[str] = []
    for token in argv:
        if not token.startswith("-D"):
            continue
        definition = token[2:]
        key_with_type, separator, value = definition.partition("=")
        if separator != "=" or not key_with_type:
            continue
        key, _type_separator, _cmake_type = key_with_type.partition(":")
        if key == name:
            values.append(value)
    return values


def _build_dir_from_configure(argv: list[str]) -> str | None:
    values: list[str] = []
    for index, token in enumerate(argv):
        if token == "-B" and index + 1 < len(argv):
            values.append(argv[index + 1])
        elif token.startswith("-B") and len(token) > 2:
            values.append(token[2:])
    if len(values) != 1 or not values[0]:
        return None
    return os.path.normpath(values[0])


def _build_dir_from_build(argv: list[str]) -> str | None:
    values: list[str] = []
    for index, token in enumerate(argv):
        if token == "--build" and index + 1 < len(argv):
            values.append(argv[index + 1])
        elif token.startswith("--build="):
            values.append(token[len("--build="):])
    if len(values) != 1 or not values[0]:
        return None
    return os.path.normpath(values[0])


def _bench_execution_target(
    argv: list[str], prefix: tuple[str, ...],
) -> str | None:
    if tuple(argv[:len(prefix)]) != prefix:
        return None
    return argv[len(prefix)] if len(argv) > len(prefix) else None


def _one_record(
    records: tuple[object, ...],
    *,
    variant: str,
    attempt_id: str,
    stage: str,
    arm: ArmName,
) -> object:
    matches = [
        record for record in records
        if record.variant == variant
        and record.stage == stage
        and record.payload.get("build_attempt_id") == attempt_id
    ]
    if len(matches) != 1:
        # Redundant standalone gate: certified admission/finalization rejects
        # missing terminal receipts before this fixed-pair projection can fire.
        _reject(
            "pair-cardinality",
            f"wal.{stage}.count",
            1,
            len(matches),
            arm,
        )
    return matches[0]


def _arm_decision(
    records: tuple[object, ...],
    *,
    start: object,
    arm: ArmName,
    preregistered: T1998ArmPreregisteredIdentity,
    expected_genome: str,
    flags: Mapping[str, int],
    result: Mapping[str, Any],
    environment_contract_sha256: str,
) -> tuple[T1998ArmDecision, Mapping[str, Any], str]:
    _require_equal(
        preregistered.canonical_genome,
        expected_genome,
        code="preregistered-pair-mismatch",
        field=f"preregistered.{arm}.canonical_genome",
        arm=arm,
    )
    attempt_id = start.payload.get("build_attempt_id")
    if type(attempt_id) is not str or not attempt_id:
        _reject(
            "pair-cardinality", "wal.build_start.build_attempt_id",
            "non-empty exact string", attempt_id, arm,
        )
    variant = start.variant
    build_done = _one_record(
        records, variant=variant, attempt_id=attempt_id,
        stage=STAGE_BUILD_DONE, arm=arm,
    )
    verify_done = _one_record(
        records, variant=variant, attempt_id=attempt_id,
        stage=STAGE_VERIFY_DONE, arm=arm,
    )
    bench_done = _one_record(
        records, variant=variant, attempt_id=attempt_id,
        stage=STAGE_BENCH_DONE, arm=arm,
    )
    commit = _one_record(
        records, variant=variant, attempt_id=attempt_id,
        stage=STAGE_COMMIT, arm=arm,
    )
    arm_records = (start, build_done, verify_done, bench_done, commit)
    env_tags = {record.env_tag for record in arm_records}
    if len(env_tags) != 1:
        _reject(
            "environment-identity-mismatch", "wal.env_tag",
            start.env_tag, sorted(env_tags), arm,
        )
    # Redundant standalone gate: certified admission already binds COMMIT's
    # environment digest to the campaign lock.  Retain this projection guard.
    _require_equal(
        commit.payload.get(COMMIT_CONTRACT_SHA256_KEY),
        environment_contract_sha256,
        code="environment-identity-mismatch",
        field="wal.commit.contract_sha256",
        arm=arm,
    )

    build_admission = start.payload.get("build_admission")
    source = (
        build_admission.get("source")
        if type(build_admission) in {dict, MappingProxyType}
        else None
    )
    source_digest = (
        source.get("source_bytes_sha256")
        if type(source) in {dict, MappingProxyType}
        else None
    )
    if source_digest != preregistered.source_bytes_sha256:
        _reject(
            "source-identity-unbound",
            "wal.build_start.build_admission.source.source_bytes_sha256",
            preregistered.source_bytes_sha256,
            source_digest,
            arm,
        )

    configure = _command_argv(build_done.payload.get("perf_configure_cmd"))
    if configure is None:
        _reject(
            "performance-build-not-trace-disabled", "wal.build_done.perf_configure_cmd",
            "non-empty shell command or argv", build_done.payload.get("perf_configure_cmd"),
            arm,
        )
    diagnostic_values = {
        name: values[-1]
        for name in ("CCBENCH_BACKOFF_NOINLINE", "BACKOFF_NOINLINE")
        if (values := _cmake_define_values(configure, name))
    }
    diagnostic_markers = {
        name: value for name, value in diagnostic_values.items() if value == "1"
    }
    if diagnostic_markers:
        _reject(
            "diagnostic-build", "BACKOFF_NOINLINE",
            "not equal to 1", diagnostic_markers, arm,
        )
    trace_values = _cmake_define_values(configure, "CCBENCH_TRACE")
    if trace_values != ["0"]:
        _reject(
            "performance-build-not-trace-disabled",
            "wal.build_done.perf_configure_cmd.CCBENCH_TRACE",
            ["0"], trace_values, arm,
        )
    perf_sha = build_done.payload.get("perf_bin_sha256")
    if not _is_lower_hex(perf_sha, 64):
        _reject(
            "performance-build-not-trace-disabled", "wal.build_done.perf_bin_sha256",
            "exact lowercase sha256", perf_sha, arm,
        )
    build_dir = _build_dir_from_configure(configure)
    build_argv = _command_argv(build_done.payload.get("perf_build_cmd"))
    built_dir = (
        _build_dir_from_build(build_argv) if build_argv is not None else None
    )
    if build_dir is None or built_dir != build_dir:
        _reject(
            "performance-build-not-trace-disabled",
            "wal.build_done.perf_build_cmd.--build",
            build_dir or "one configure -B directory",
            built_dir if build_argv is not None else build_done.payload.get(
                "perf_build_cmd"
            ),
            arm,
        )
    run_argv = _command_argv(bench_done.payload.get("run_cmd"))
    expected_binary = os.path.join(build_dir, "cc", "silo", "ycsb_silo.exe")
    prefix = env_contract.resolve_by_contract_sha256(
        environment_contract_sha256
    ).contract.numactl
    execution_target = (
        _bench_execution_target(run_argv, prefix) if run_argv is not None else None
    )
    if (
        execution_target is None
        or os.path.normpath(execution_target) != expected_binary
    ):
        _reject(
            "performance-build-not-trace-disabled", "wal.bench_done.run_cmd.executable",
            expected_binary,
            bench_done.payload.get("run_cmd"), arm,
        )

    samples = bench_done.payload.get("tps")
    if (
        type(samples) is not tuple
        or len(samples) != EXPECTED_SAMPLE_COUNT
        or not all(_finite_positive(value) for value in samples)
    ):
        _reject(
            "pair-value-mismatch", "wal.bench_done.tps",
            f"{EXPECTED_SAMPLE_COUNT} finite positive samples", samples, arm,
        )
    median = statistics.median(samples)
    _require_equal(
        bench_done.payload.get("median_tps"), median,
        code="pair-value-mismatch", field="wal.bench_done.median_tps", arm=arm,
    )
    _require_equal(
        commit.payload.get("fitness_tps"), median,
        code="pair-value-mismatch", field="wal.commit.fitness_tps", arm=arm,
    )
    cv = bench_done.payload.get("cv")
    if type(cv) not in {int, float} or not math.isfinite(cv) or cv < 0:
        _reject(
            "pair-value-mismatch", "wal.bench_done.cv",
            "finite non-negative number", cv, arm,
        )
    _require_equal(
        commit.payload.get("cv"), cv,
        code="pair-value-mismatch", field="wal.commit.cv", arm=arm,
    )
    bench_unstable = bench_done.payload.get("unstable")
    commit_unstable = commit.payload.get("unstable")
    if type(bench_unstable) is not bool or commit_unstable is not bench_unstable:
        _reject(
            "pair-value-mismatch", "wal.commit.unstable",
            bench_unstable if type(bench_unstable) is bool else "exact bool",
            commit_unstable, arm,
        )

    result_prefix = "no_backoff" if arm == "baseline" else "target"
    _require_equal(
        result.get(f"{result_prefix}_tps"), list(samples),
        code="pair-value-mismatch", field=f"result.{result_prefix}_tps", arm=arm,
    )
    _require_equal(
        result.get(f"{result_prefix}_median_tps"), median,
        code="pair-value-mismatch",
        field=f"result.{result_prefix}_median_tps",
        arm=arm,
    )

    toolchain = build_done.payload.get("toolchain")
    if type(toolchain) not in {dict, MappingProxyType} or not toolchain:
        _reject(
            "toolchain-identity-mismatch", "wal.build_done.toolchain",
            "non-empty object", toolchain, arm,
        )
    toolchain_digest = build_done.payload.get("toolchain_record_sha256")
    if not _is_lower_hex(toolchain_digest, 64):
        _reject(
            "toolchain-identity-mismatch",
            "wal.build_done.toolchain_record_sha256",
            "exact lowercase sha256", toolchain_digest, arm,
        )
    receipt = commit.payload.get("commit_verification_receipt")
    receipt_id = (
        receipt.get("receipt_id")
        if type(receipt) in {dict, MappingProxyType}
        else None
    )
    if type(receipt_id) is not str or not receipt_id:
        # Redundant standalone gate: certified admission rejects a missing
        # receipt first.  Keep this fail-closed persisted-payload projection.
        _reject(
            "producer-rejected-variant",
            "wal.commit.commit_verification_receipt.receipt_id",
            "non-empty exact string", receipt_id, arm,
        )
    return (
        T1998ArmDecision(
            arm=arm,
            canonical_genome=expected_genome,
            flags=tuple(sorted(flags.items())),
            variant_id=variant,
            samples=tuple(samples),
            median_tps=median,
            cv=float(cv),
            unstable=bench_unstable,
            performance_binary_sha256=perf_sha,
            commit_receipt_id=receipt_id,
        ),
        toolchain,
        toolchain_digest,
    )


def consume_balanced_stock_inline_pair(
    producer_root: str | Path,
    *,
    preregistered: T1998PreregisteredIdentity,
    repo_root: str | Path | None = None,
) -> T1998StockInlineDecision:
    """Consume the exact pre-registered balanced no-backoff/fixed-5 pair."""
    if type(preregistered) is not T1998PreregisteredIdentity:
        raise TypeError("preregistered must be exact T1998PreregisteredIdentity")
    root = Path(producer_root)
    result = _read_regular_json(root / "result.json", field="result.json")

    failure_path = Path(os.fspath(root) + ".failure.json")
    if os.path.lexists(failure_path):
        _reject(
            "producer-failure-receipt", "sibling_failure_receipt",
            "absent", os.fspath(failure_path), "baseline",
        )
    reservation = _read_regular_json(
        root / "reservation.json", field="reservation.json",
    )

    for field, expected in (
        ("schema_version", "a5-second-boot-result/v1"),
        ("status", "complete"),
        ("workload", WORKLOAD),
        ("target_fixed_us", TARGET_FIXED_US),
    ):
        _require_equal(
            result.get(field), expected,
            code="result-contract-mismatch", field=f"result.{field}",
        )
    _require_equal(
        reservation.get("schema_version"), "a5-second-boot-reservation/v1",
        code="producer-artifact-binding-mismatch",
        field="reservation.schema_version",
    )
    campaign_id = result.get("campaign_id")
    if (
        type(campaign_id) is not str
        or not campaign_id
        or campaign_id in {".", ".."}
        or "/" in campaign_id
        or "\\" in campaign_id
    ):
        _reject(
            "producer-artifact-binding-mismatch", "result.campaign_id",
            "one path component", campaign_id,
        )
    campaign_path = root / "campaigns" / campaign_id
    try:
        campaign_info = campaign_path.lstat()
    except FileNotFoundError:
        _reject(
            "producer-artifact-missing", "campaign", "real directory", "missing",
        )
    if not stat.S_ISDIR(campaign_info.st_mode):
        _reject(
            "producer-artifact-missing", "campaign", "real non-symlink directory",
            "non-directory-or-symlink",
        )

    try:
        view = require_admitted_campaign(
            campaign_path,
            purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
        )
    except (ArtifactAdmissionError, OSError, UnicodeError, ValueError) as exc:
        _reject(
            "producer-rejected-variant", "certified_campaign_admission",
            "admitted certified campaign", f"{type(exc).__name__}: {exc}",
            "unknown",
        )

    lock_path = Path(view.lock_file)
    wal_path = Path(view.wal_file)
    try:
        lock_sha = _sha256_file(lock_path)
        wal_sha = _sha256_file(wal_path)
    except OSError as exc:
        _reject(
            "producer-artifact-missing", "campaign lock/WAL",
            "readable regular files", str(exc),
        )
    # Redundant standalone TOCTOU gates: the admitted view calculated both
    # digests from these same bytes, so neither comparison fires by itself.
    _require_equal(
        lock_sha, view.decision.campaign_lock_sha256,
        code="producer-artifact-binding-mismatch", field="admission.lock_sha256",
    )
    _require_equal(
        wal_sha, view.decision.wal_sha256,
        code="producer-artifact-binding-mismatch", field="admission.wal_sha256",
    )
    _require_equal(
        result.get("lock_sha256"), view.decision.campaign_lock_sha256,
        code="producer-artifact-binding-mismatch", field="result.lock_sha256",
    )
    _require_equal(
        result.get("wal_sha256"), view.decision.wal_sha256,
        code="producer-artifact-binding-mismatch", field="result.wal_sha256",
    )

    try:
        decoded_lock = campaign_lock.decode_campaign_lock_bytes(lock_path.read_bytes())
    except (OSError, campaign_lock.CampaignLockCodecError) as exc:
        _reject(
            "producer-artifact-invalid", "campaign.lock",
            "valid campaign-lock/v2", f"{type(exc).__name__}: {exc}",
        )
    if not decoded_lock.is_v2 or decoded_lock.authority is None:
        _reject(
            "producer-artifact-invalid", "campaign.lock.schema_version",
            "campaign-lock/v2 with authority", decoded_lock.schema_version,
        )
    common = preregistered.common
    authority = decoded_lock.authority
    _require_equal(
        result.get("repository_commit"), common.repository_commit,
        code="repository-identity-mismatch", field="result.repository_commit",
    )
    _require_equal(
        authority.contract_loader_commit, result.get("repository_commit"),
        code="repository-identity-mismatch",
        field="campaign.lock.authority.contract_loader_commit",
    )
    _require_equal(
        result.get("ccbench_commit"), common.ccbench_gitlink_commit,
        code="gitlink-identity-mismatch", field="result.ccbench_commit",
    )
    source_binding = reservation.get("source_binding")
    if type(source_binding) is not dict:
        _reject(
            "producer-artifact-binding-mismatch", "reservation.source_binding",
            "object", source_binding,
        )
    _require_equal(
        source_binding.get("repository_commit"), common.repository_commit,
        code="repository-identity-mismatch",
        field="reservation.source_binding.repository_commit",
    )
    _require_equal(
        source_binding.get("ccbench_gitlink_commit"),
        common.ccbench_gitlink_commit,
        code="gitlink-identity-mismatch",
        field="reservation.source_binding.ccbench_gitlink_commit",
    )

    lock_gitlink = decoded_lock.identity.get("ccbench_commit")
    if not _gitlink_matches(common.ccbench_gitlink_commit, lock_gitlink):
        _reject(
            "gitlink-identity-mismatch", "campaign.lock.ccbench_commit",
            f"abbreviated prefix of {common.ccbench_gitlink_commit}",
            lock_gitlink,
        )
    starts = [record for record in view.records if record.stage == STAGE_BUILD_START]
    # D1244 limits content inspection to the fixed pair.  Genome key shape is
    # producer provenance, so every build_start is still constrained below.
    for record in starts:
        has_diagnostic_key, arm = _genome_diagnostic_arm(
            record.payload.get("genome")
        )
        if has_diagnostic_key:
            _reject(
                "diagnostic-build", "wal.build_start.genome.BACKOFF_NOINLINE",
                "absent", record.payload.get("genome"), arm,
            )
    pair_starts = [
        (record, pair_arm)
        for record in starts
        if (pair_arm := _pair_arm_from_genome(record.payload.get("genome")))
        is not None
    ]
    wal_gitlinks: set[str] = set()
    # Redundant standalone gate: certified admission binds the WAL source
    # gitlink to the lock first.  Keep the preregistration projection guard.
    for record, arm in pair_starts:
        build_admission = record.payload.get("build_admission")
        source = (
            build_admission.get("source")
            if type(build_admission) in {dict, MappingProxyType}
            else None
        )
        candidate = (
            source.get("ccbench_commit")
            if type(source) in {dict, MappingProxyType}
            else None
        )
        if not _gitlink_matches(common.ccbench_gitlink_commit, candidate):
            _reject(
                "gitlink-identity-mismatch",
                "wal.build_start.build_admission.source.ccbench_commit",
                f"abbreviated prefix of {common.ccbench_gitlink_commit}",
                candidate,
                arm,
            )
        wal_gitlinks.add(candidate)
    _require_equal(
        authority.environment_contract_sha256,
        common.environment_contract_sha256,
        code="environment-identity-mismatch",
        field="campaign.lock.authority.environment_contract_sha256",
    )
    binding = reservation.get("binding")
    if type(binding) is not dict:
        _reject(
            "producer-artifact-binding-mismatch", "reservation.binding",
            "object", binding,
        )
    _require_equal(
        binding.get("script_sha256"), common.launcher_script_sha256,
        code="launcher-script-identity-mismatch",
        field="reservation.binding.script_sha256",
    )

    expected_node = {
        "hostname": result.get("hostname"),
        "fqdn": result.get("fqdn"),
        "boot_id": result.get("boot_id"),
        "boot_epoch": result.get("boot_epoch"),
        "pbs_jobid": result.get("pbs_jobid"),
    }
    _require_equal(
        reservation.get("node_boot_evidence"), expected_node,
        code="producer-artifact-binding-mismatch",
        field="reservation.node_boot_evidence",
    )

    baseline_starts = [
        record for record, arm in pair_starts
        if arm == "baseline"
    ]
    target_starts = [
        record for record, arm in pair_starts
        if arm == "target"
    ]
    # pair-cardinality と producer-rejected-variant は上流 finalizer と
    # require_admitted_campaign が先に拒否するため、単独では発火しない冗長 gate。
    # それでも tampered/synthetic root を fail-closed にするため検査は残す。
    if len(starts) != EXPECTED_PRODUCER_POINT_COUNT:
        _reject(
            "pair-cardinality", "wal.build_start.total_count",
            EXPECTED_PRODUCER_POINT_COUNT, len(starts),
        )
    if len(baseline_starts) != 1:
        _reject(
            "pair-cardinality", "wal.baseline.build_start.count",
            1, len(baseline_starts), "baseline",
        )
    if len(target_starts) != 1:
        _reject(
            "pair-cardinality", "wal.target.build_start.count",
            1, len(target_starts), "target",
        )
    arm_by_variant: dict[str, RejectionArm] = {
        **{record.variant: "baseline" for record in baseline_starts},
        **{record.variant: "target" for record in target_starts},
    }
    known_attempts = {
        (record.variant, attempt_id)
        for record in starts
        if type(attempt_id := record.payload.get("build_attempt_id")) is str
        and attempt_id
    }
    for record in view.records:
        arm = arm_by_variant.get(record.variant, "unknown")
        if "anomalies" in record.payload or record.stage == STAGE_VERIFY_DONE:
            _require_equal(
                record.payload.get("anomalies"),
                0,
                code="producer-rejected-variant",
                field=f"wal.{record.stage}.anomalies",
                arm=arm,
            )
        if "verdict" in record.payload or record.stage == STAGE_VERIFY_DONE:
            _require_equal(
                record.payload.get("verdict"),
                "serializable",
                code="producer-rejected-variant",
                field=f"wal.{record.stage}.verdict",
                arm=arm,
            )
        if record.stage not in {STAGE_VERIFY_DONE, STAGE_BENCH_DONE}:
            continue
        attempt_id = record.payload.get("build_attempt_id")
        if (record.variant, attempt_id) not in known_attempts:
            _reject(
                "producer-rejected-variant",
                f"wal.{record.stage}.build_attempt_id",
                "known build attempt for the same variant",
                attempt_id,
                arm,
            )
    by_variant_stages: dict[str, set[str]] = {}
    for record in view.records:
        by_variant_stages.setdefault(record.variant, set()).add(record.stage)
        if record.stage == STAGE_ABORT:
            arm = (
                "target"
                if record.variant == target_starts[0].variant
                else "baseline"
            )
            # Redundant standalone gate: finalization/admission rejects aborts
            # before this fixed-pair fail-closed projection can fire.
            _reject(
                "producer-rejected-variant", "wal.abort",
                "absent", "present", arm,
            )
    for variant in {record.variant for record in starts}:
        missing = _PAIR_STAGES - by_variant_stages.get(variant, set())
        if missing:
            arm = "target" if variant == target_starts[0].variant else "baseline"
            # Redundant standalone gate: finalization/admission rejects missing
            # stages before this fixed-pair fail-closed projection can fire.
            _reject(
                "producer-rejected-variant", "wal.variant.stages",
                sorted(_PAIR_STAGES), sorted(by_variant_stages.get(variant, set())), arm,
            )

    baseline, baseline_toolchain, baseline_toolchain_digest = _arm_decision(
        view.records,
        start=baseline_starts[0],
        arm="baseline",
        preregistered=preregistered.baseline,
        expected_genome=BASELINE_CANONICAL_GENOME,
        flags=BASELINE_FLAGS,
        result=result,
        environment_contract_sha256=common.environment_contract_sha256,
    )
    target, target_toolchain, target_toolchain_digest = _arm_decision(
        view.records,
        start=target_starts[0],
        arm="target",
        preregistered=preregistered.target,
        expected_genome=TARGET_CANONICAL_GENOME,
        flags=TARGET_FLAGS,
        result=result,
        environment_contract_sha256=common.environment_contract_sha256,
    )
    _require_equal(
        target_toolchain, baseline_toolchain,
        code="toolchain-identity-mismatch", field="target.wal.build_done.toolchain",
        arm="target",
    )
    _require_equal(
        target_toolchain_digest, baseline_toolchain_digest,
        code="toolchain-identity-mismatch",
        field="target.wal.build_done.toolchain_record_sha256",
        arm="target",
    )
    _require_equal(
        result.get("toolchain"), dict(baseline_toolchain),
        code="toolchain-identity-mismatch", field="result.toolchain",
    )

    preregistration_repo_root = (
        Path(__file__).resolve().parents[2]
        if repo_root is None
        else Path(repo_root).resolve()
    )
    try:
        current_preregistration = _read_preregistration_bytes(
            preregistration_repo_root
        )
    except ValueError as exc:
        _reject(
            "current-preregistration-sha-mismatch",
            "preregistration.current.sha256",
            CURRENT_PREREGISTRATION_SHA256,
            str(exc),
            "unknown",
        )
    current_preregistration_sha256 = hashlib.sha256(
        current_preregistration
    ).hexdigest()
    _require_equal(
        current_preregistration_sha256,
        CURRENT_PREREGISTRATION_SHA256,
        code="current-preregistration-sha-mismatch",
        field="preregistration.current.sha256",
        arm="unknown",
    )

    try:
        measurement_preregistration = _preregistration_blob(
            preregistration_repo_root,
            common.repository_commit,
        )
    except ValueError as exc:
        _reject(
            "measurement-preregistration-sha-mismatch",
            "preregistration.measurement.sha256",
            MEASUREMENT_TIME_PREREGISTRATION_SHA256,
            str(exc),
            "unknown",
        )
    measurement_preregistration_sha256 = hashlib.sha256(
        measurement_preregistration
    ).hexdigest()
    _require_equal(
        measurement_preregistration_sha256,
        MEASUREMENT_TIME_PREREGISTRATION_SHA256,
        code="measurement-preregistration-sha-mismatch",
        field="preregistration.measurement.sha256",
        arm="unknown",
    )

    try:
        documented = _identity_from_preregistration(
            measurement_preregistration,
            common.repository_commit,
        )
    except (TypeError, ValueError) as exc:
        _reject(
            "preregistration-identity-mismatch",
            "preregistration.current.spec",
            "one valid exact T-1998 preregistration identity",
            str(exc),
            "unknown",
        )
    for field, actual, expected, arm in (
        (
            "preregistered.common.ccbench_gitlink_commit",
            common.ccbench_gitlink_commit,
            documented.common.ccbench_gitlink_commit,
            "unknown",
        ),
        (
            "preregistered.common.environment_contract_sha256",
            common.environment_contract_sha256,
            documented.common.environment_contract_sha256,
            "unknown",
        ),
        (
            "preregistered.common.launcher_script_sha256",
            common.launcher_script_sha256,
            documented.common.launcher_script_sha256,
            "unknown",
        ),
        (
            "preregistered.baseline.canonical_genome",
            preregistered.baseline.canonical_genome,
            documented.baseline.canonical_genome,
            "baseline",
        ),
        (
            "preregistered.baseline.source_bytes_sha256",
            preregistered.baseline.source_bytes_sha256,
            documented.baseline.source_bytes_sha256,
            "baseline",
        ),
        (
            "preregistered.target.canonical_genome",
            preregistered.target.canonical_genome,
            documented.target.canonical_genome,
            "target",
        ),
        (
            "preregistered.target.source_bytes_sha256",
            preregistered.target.source_bytes_sha256,
            documented.target.source_bytes_sha256,
            "target",
        ),
    ):
        _require_equal(
            actual,
            expected,
            code="preregistration-identity-mismatch",
            field=field,
            arm=arm,
        )

    ratio = target.median_tps / baseline.median_tps
    improvement = (ratio - 1.0) * 100.0
    if not math.isfinite(ratio) or not math.isfinite(improvement):
        _reject(
            "pair-value-mismatch", "computed.ratio",
            "finite", ratio, "target",
        )
    _require_equal(
        result.get("ratio"), ratio,
        code="pair-value-mismatch", field="result.ratio", arm="target",
    )
    _require_equal(
        result.get("improvement_percent"), improvement,
        code="pair-value-mismatch", field="result.improvement_percent", arm="target",
    )

    identity = T1998IdentityDecision(
        repository_commit=common.repository_commit,
        ccbench_gitlink_commit=common.ccbench_gitlink_commit,
        campaign_ccbench_gitlink_prefix=lock_gitlink,
        wal_ccbench_gitlink_prefixes=tuple(sorted(wal_gitlinks)),
        abbreviated_gitlink_is_full_identity=False,
        environment_contract_sha256=common.environment_contract_sha256,
        launcher_script_sha256=common.launcher_script_sha256,
        launcher_binding_scope="job-body-script-sha256-only",
        submitter_identity_recoverable=False,
        source_digest_binding_required=True,
        explicit_diagnostic_marker_check_is_sufficient=False,
        toolchain_manifest=_freeze_json(dict(baseline_toolchain)),
        toolchain_record_sha256=baseline_toolchain_digest,
        campaign_id=campaign_id,
        lock_sha256=view.decision.campaign_lock_sha256,
        wal_sha256=view.decision.wal_sha256,
    )
    if baseline.unstable or target.unstable:
        return T1998StockInlineDecision(
            status="inconclusive",
            reason="unstable-arm",
            baseline=baseline,
            target=target,
            identity=identity,
            ratio=None,
            improvement_percent=None,
        )
    return T1998StockInlineDecision(
        status="accepted",
        reason="preregistered-balanced-stock-inline-pair",
        baseline=baseline,
        target=target,
        identity=identity,
        ratio=ratio,
        improvement_percent=improvement,
    )
