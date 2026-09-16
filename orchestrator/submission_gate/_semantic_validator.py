"""独立した受領証 semantic validator (T-338 単位3)。

``_receipt_schema`` が検査するのは JSON の shape だけであり、この module は
shape を通過した受領証から raw artifact を再読して cross-field 条件を再計算する。
producer が書いた ``reason_code``、digest、schedule digest、qsub returncode、
``cmake_cache``、または ``correctness`` の clean 申告を受理の正の根拠にはしない。

この module の保証境界は、呼出し時に指定された repository root とその root に
束縛された ``_PreregBinding``、および受領証が指す raw bytes である。producer の
外側で採取された durable intent、台帳外の投入、raw collector の真正性、
単独性そのものはここでは保証しない。

下位層の parse/schema/safe-I/O/manifest/Git 例外は、原因を失わないよう
``SemanticValidationError`` へ ``raise ... from exc`` で変換する。なお、CCBench
の生ログ形式は T-139 の対象 protocol である silo の
``external/ccbench/cc/silo/util.cc:91-104`` の
``#FLAGS_<name>:\t<value>`` 出力、共通 YCSB driver の
``external/ccbench/include/ycsb.hh:206-211``、および同 silo util の
``external/ccbench/cc/silo/util.cc:162-177`` の
``#ShowOptParameters() ...`` 出力に固定している。
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from contextvars import ContextVar
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import PurePosixPath
import re
import shlex
from typing import Any, Final

from . import _binding, _git
from ._binding import _PreregBinding
from ._manifest import (
    ManifestError,
    PreregistrationRecord,
    _parse_blob_ref,
    _parse_erratum,
)
from ._receipt_io import (
    ReceiptDocument,
    ReceiptParseError,
)
from ._receipt_schema import (
    ReceiptSchema,
    ReceiptSchemaError,
    validate_receipt_shape,
)
from ._safe_io import SafeIOError, read_relative_regular_bytes


_HEX40_RE: Final = re.compile(r"[0-9a-f]{40}\Z")
_HEX64_RE: Final = re.compile(r"[0-9a-f]{64}\Z")
_MAX_POINTER_BYTES: Final = 64 * 1024 * 1024
_A09_SEED: Final = "7df15572d2d88f172bc69bea9bc2dc53eddcbef41211d8ece7b0a592e5b2615d"
_A09_ALGORITHM: Final = "t139-a09-v1"
_PERMUTATIONS: Final = ("SDX", "SXD", "DSX", "DXS", "XSD", "XDS")
_ARM_BY_SYMBOL: Final = {"S": "stock", "D": "mode1", "X": "modeX"}
_ARMS: Final = ("stock", "mode1", "modeX")
_WORKLOADS: Final = ("W1", "W2")
_DEPENDENCIES: Final = frozenset(
    {"gflags", "glog", "masstree", "mimalloc", "googletest"}
)
_CCBENCH_PIN: Final = "d706650cdb31e442bef45b9b4216951d4fb40969"
_EXPECTED_DEPENDENCY_PINS: Final = {
    "gflags": "e171aa2d15ed9eb17054558e0b3a6a413bb01067",
    "glog": "8f9ccfe770add9e4c64e9b25c102658e3c763b73",
    "masstree": "b3c5d054b66b08374d7a6ff5a0faeaf28b041a38",
    "mimalloc": "02a2f5df9d7d46d30263b83832eebeeab62dc5fe",
    "googletest": "f8d7d77c06936315286eb55f8de22cd23c188571",
}
_EXPECTED_MODE_MACROS: Final = {
    "stock": None,
    "mode1": "-DIZANAGI_T139_PC_MODE1=1",
    "modeX": "-DIZANAGI_T139_PC_MODEX=1",
}
_EXPECTED_PATCH_PATH: Final = "tools/pegasus/probes/t139_positive_control.patch"
_EXPECTED_PATCH_SHA256: Final = "3b9cdf1635c2afdbfa24af2b5e84e841773144147fe0d00c8b5e794817051951"
_PREREGISTRATION_KEYS: Final = frozenset(
    {
        "core",
        "addendum_a",
        "addendum_b",
        "fold_commit",
        "errata",
        "approval_manifest",
        "receipt_schema",
        "composed_core_sha256",
    }
)
_PREREGISTRATION_RECORD_FIELDS: Final = (
    "core",
    "addendum_a",
    "addendum_b",
    "fold_commit",
    "errata",
    "approval_manifest",
    "receipt_schema",
    "composed_core_sha256",
    "prereg_commit",
)
_FLAG_ALIASES: Final = {
    "clocks_per_us": "clocks_per_us",
    "epoch_time": "epoch_time",
    "extime": "extime",
    "ycsb_max_ope": "ycsb_max_ope",
    "ycsb_rmw": "ycsb_rmw",
    "ycsb_rratio": "ycsb_rratio",
    "thread_num": "thread_num",
    "ycsb_tuple_num": "ycsb_tuple_num",
    "ycsb_zipf_skew": "ycsb_zipf_skew",
}
_OPT_PARAMETER_KEYS: Final = frozenset(
    {
        "ADD_ANALYSIS",
        "BACK_OFF",
        "KEY_SIZE",
        "MASSTREE_USE",
        "NO_WAIT_LOCKING_IN_VALIDATION",
        "PARTITION_TABLE",
        "PROCEDURE_SORT",
        "SLEEP_READ_PHASE",
        "VAL_SIZE",
        "WAL",
    }
)
_EXPECTED_OPT_PARAMETERS: Final = {
    "ADD_ANALYSIS": 0,
    "BACK_OFF": 0,
    "KEY_SIZE": 8,
    "MASSTREE_USE": 1,
    "NO_WAIT_LOCKING_IN_VALIDATION": 1,
    "PARTITION_TABLE": 0,
    "PROCEDURE_SORT": 0,
    "SLEEP_READ_PHASE": 0,
    "VAL_SIZE": 4,
    "WAL": 0,
}
_OPTIONAL_SILO_OPT_PARAMETERS: Final = frozenset(
    {"INSERT_READ_DELAY_MS", "INSERT_BATCH_DELAY_MS"}
)
_EXPECTED_FLAGS: Final = {
    "W1": {
        "clocks_per_us": 2100,
        "epoch_time": 40,
        "extime": 3,
        "thread_num": 48,
        "ycsb_max_ope": 10,
        "ycsb_rmw": 1,
        "ycsb_rratio": 50,
        "ycsb_tuple_num": 10000,
        "ycsb_zipf_skew": 0.9,
    },
    "W2": {
        "clocks_per_us": 2100,
        "epoch_time": 40,
        "extime": 3,
        "thread_num": 48,
        "ycsb_max_ope": 10,
        "ycsb_rmw": 0,
        "ycsb_rratio": 50,
        "ycsb_tuple_num": 100000,
        "ycsb_zipf_skew": 0.5,
    },
}
_EXPECTED_DRIVER_ARGV: Final = {
    "W1": (
        "-ycsb_rmw=true",
        "-ycsb_zipf_skew=0.9",
        "-ycsb_tuple_num=10000",
        "-ycsb_max_ope=10",
        "-thread_num=48",
        "-extime=3",
    ),
    "W2": (
        "-ycsb_rratio=50",
        "-ycsb_zipf_skew=0.5",
        "-ycsb_tuple_num=100000",
        "-ycsb_max_ope=10",
        "-thread_num=48",
        "-extime=3",
    ),
}
_PERFORMANCE_PHASE_CAPS: Final = {
    "preflight": (180, 150),
    "observation": (10, 10),
    "decision": (5, 5),
    "marker": (5, 5),
    "run": (1920, 1920),
    "teardown": (300, 300),
}
_VERIFICATION_PHASE_CAPS: Final = {
    "staging": (180, 180),
    "build": (1440, 1440),
    "build_post": (360, 360),
    "correctness_run": (360, 360),
    "evidence": (180, 180),
    "teardown": (120, 120),
}
_PERFORMANCE_PHASES: Final = frozenset(_PERFORMANCE_PHASE_CAPS)
_VERIFICATION_PHASES: Final = frozenset(_VERIFICATION_PHASE_CAPS)
_VALIDATION_ROOT_IDENTITY: ContextVar[tuple[int, int] | None] = ContextVar(
    "semantic_validation_root_identity", default=None
)


class SemanticValidationError(ValueError):
    """受領証の semantic 条件を fail-closed で拒否した。"""

    def __init__(self, reason_code: str, message: str) -> None:
        if type(reason_code) is not str or not reason_code:
            raise TypeError("reason_code must be a non-empty string")
        self.reason_code = reason_code
        # ``code`` is kept as a convenient private-consumer spelling.
        self.code = reason_code
        super().__init__(f"{reason_code}: {message}")


@dataclass(frozen=True, slots=True)
class A03Result:
    """raw CPU observation の再計算結果。"""

    malformed_reason: str | None
    busy_core_equivalents: float | None
    failure: bool
    stat_before: tuple[int, ...]
    stat_after: tuple[int, ...]


def _semantic(reason: str, message: str, cause: BaseException | None = None) -> None:
    error = SemanticValidationError(reason, message)
    if cause is None:
        raise error
    raise error from cause


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _semantic("shape", f"{label} must be an object")
    return value  # type: ignore[return-value]


def _exact_keys(value: Mapping[str, Any], expected: Iterable[str], label: str) -> None:
    expected_set = frozenset(expected)
    if frozenset(value) != expected_set:
        _semantic(
            "shape",
            f"{label} key set is not exact: expected={sorted(expected_set)!r} "
            f"actual={sorted(value)!r}",
        )


def _exact_int(value: object, label: str, *, minimum: int | None = None) -> int:
    if type(value) is not int or (minimum is not None and value < minimum):
        _semantic("semantic", f"{label} must be an exact integer")
    return value  # type: ignore[return-value]


def _hex(value: object, label: str, length: int) -> str:
    expression = _HEX40_RE if length == 40 else _HEX64_RE
    if type(value) is not str or expression.fullmatch(value) is None:
        _semantic("semantic", f"{label} must be lowercase hex{length}")
    return value  # type: ignore[return-value]


def _receipt_value(receipt: ReceiptDocument | Mapping[str, Any]) -> Mapping[str, Any]:
    if type(receipt) is ReceiptDocument:
        return receipt.value
    if isinstance(receipt, Mapping):
        return receipt
    _semantic("shape", "receipt must be ReceiptDocument or Mapping")


def _capture_root_identity(
    repository_root: str | os.PathLike[str],
) -> tuple[int, int]:
    """入口時の repository root identity を捕捉する。"""

    try:
        stat_result = os.stat(repository_root)
        return (stat_result.st_dev, stat_result.st_ino)
    except (OSError, TypeError, ValueError) as exc:
        _semantic("authority", "repository root identity cannot be captured", exc)


def _assert_root_identity(
    repository_root: str | os.PathLike[str],
    expected: tuple[int, int] | None = None,
) -> None:
    """authority 検査後の I/O が同じ root snapshot に属することを確認する。"""

    pinned = expected if expected is not None else _VALIDATION_ROOT_IDENTITY.get()
    if pinned is None:
        return
    try:
        stat_result = os.stat(repository_root)
        current = (stat_result.st_dev, stat_result.st_ino)
    except (OSError, TypeError, ValueError) as exc:
        _semantic("authority", "repository root identity cannot be rechecked", exc)
    if current != pinned:
        _semantic(
            "authority",
            "repository root identity changed between authority and artifact I/O",
        )


def _read_file_record(
    repository_root: str | os.PathLike[str],
    record: Mapping[str, object],
    *,
    label: str,
    max_bytes: int = _MAX_POINTER_BYTES,
) -> bytes:
    """fileRecord を単一 fd snapshot で読み、size と SHA-256 を再計算する。"""

    try:
        _exact_keys(record, ("path", "size", "sha256"), label)
        path = record["path"]
        size = record["size"]
        digest = record["sha256"]
        if (
            type(path) is not str
            or not path
            or path.startswith("/")
            or "\x00" in path
            or "\r" in path
            or "\n" in path
        ):
            _semantic("pointer", f"{label}.path is not a strict relative path")
        components = PurePosixPath(path).parts
        if any(part in {"", ".", ".."} for part in components):
            _semantic("pointer", f"{label}.path contains an unsafe component")
        size_int = _exact_int(size, f"{label}.size", minimum=0)
        digest_text = _hex(digest, f"{label}.sha256", 64)
        if type(max_bytes) is not int or max_bytes < 0 or size_int > max_bytes:
            _semantic("pointer", f"{label}.size exceeds the read bound")
    except SemanticValidationError:
        raise
    except (TypeError, ValueError) as exc:
        _semantic("pointer", f"{label} is not a fileRecord", exc)

    _assert_root_identity(repository_root)
    try:
        raw = read_relative_regular_bytes(
            repository_root,
            path,  # type: ignore[arg-type]
            max_bytes=max_bytes,
        )
    except (SafeIOError, ValueError) as exc:
        _semantic("pointer", f"{label} cannot be read safely: {exc}", exc)
    _assert_root_identity(repository_root)
    if len(raw) != size_int:
        _semantic(
            "pointer",
            f"{label}.size does not match the single-fd snapshot: "
            f"declared={size_int} actual={len(raw)}",
        )
    actual = hashlib.sha256(raw).hexdigest()
    if actual != digest_text:
        _semantic(
            "pointer",
            f"{label}.sha256 does not match the single-fd snapshot: "
            f"declared={digest_text} actual={actual}",
        )
    return raw


def _file_record_from_path_record(
    record: Mapping[str, object], *, path_key: str = "path", label: str
) -> Mapping[str, object]:
    if not isinstance(record, Mapping):
        _semantic("pointer", f"{label} is not an object")
    if path_key not in record:
        _semantic("pointer", f"{label} has no {path_key!r}")
    return {
        "path": record[path_key],
        "size": record.get("size"),
        "sha256": record.get("sha256"),
    }


def _strict_json(raw: bytes, *, label: str) -> object:
    """JSON parser with recursive duplicate-key and non-finite rejection."""

    def reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ReceiptParseError(f"duplicate JSON object key: {key!r}")
            result[key] = value
        return result

    def reject_constant(token: str) -> None:
        raise ReceiptParseError(f"non-finite JSON number is forbidden: {token}")

    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=reject_pairs,
            parse_constant=reject_constant,
        )
        # ``parse_constant`` handles NaN/Infinity spellings, but CPython can
        # also produce an infinity from an overflowing exponent (for example
        # ``1e999999``).  That representation is not a valid JSON number and
        # must not reach any semantic comparison.
        def reject_nonfinite(child: object) -> None:
            if isinstance(child, float) and not math.isfinite(child):
                raise ReceiptParseError(
                    f"non-finite JSON number is forbidden in {label}"
                )
            if isinstance(child, Mapping):
                for nested in child.values():
                    reject_nonfinite(nested)
            elif isinstance(child, (list, tuple)):
                for nested in child:
                    reject_nonfinite(nested)

        reject_nonfinite(value)
    except ReceiptParseError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise ReceiptParseError(f"{label} is not strict UTF-8 JSON: {exc}") from exc
    return value


def _parse_number(value: str, *, label: str) -> int | float:
    text = value.strip()
    if re.fullmatch(r"-?[0-9]+", text):
        try:
            return int(text)
        except (TypeError, ValueError) as exc:
            _semantic("run_log", f"{label} is not a representable integer", exc)
    try:
        result = float(text)
    except (TypeError, ValueError, OverflowError) as exc:
        _semantic("run_log", f"{label} is not numeric", exc)
    if not math.isfinite(result):
        _semantic("run_log", f"{label} is not finite")
    return result  # type: ignore[return-value]


def _parse_ccbench_flags(raw: bytes) -> dict[str, int | float]:
    """``displayParameter`` の tab 行から a07 の9 flagだけを抽出する。"""

    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        _semantic("run_log", "CCBench log is not UTF-8", exc)
    if "\r" in text:
        _semantic("run_log", "CCBench log must use LF, not CRLF")
    found: dict[str, int | float] = {}
    for line_number, line in enumerate(text.split("\n"), 1):
        if not line.startswith("#FLAGS_"):
            continue
        match = re.fullmatch(r"#FLAGS_([A-Za-z0-9_]+):\t+(.+)", line)
        if match is None:
            # util.cc also prints a few diagnostic flags without a colon.  They
            # are outside a07; a07 fields themselves must use the fixed form.
            continue
        source_name, value = match.groups()
        target_name = _FLAG_ALIASES.get(source_name)
        if target_name is None:
            continue
        if target_name in found:
            _semantic("run_log", f"duplicate #FLAGS_ field: {target_name}")
        found[target_name] = _parse_number(
            value, label=f"#FLAGS_ line {line_number}"
        )
    return found


def _parse_show_opt_parameters(raw: bytes) -> dict[str, int]:
    """``ShowOptParameters`` の ``: NAME value`` 列を抽出する。"""

    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        _semantic("run_log", "CCBench log is not UTF-8", exc)
    if "\r" in text:
        _semantic("run_log", "CCBench log must use LF, not CRLF")
    found: dict[str, int] = {}
    prefix = "#ShowOptParameters():"
    for line_number, line in enumerate(text.split("\n"), 1):
        if not line.startswith(prefix):
            continue
        rest = line[len(prefix) :]
        for part in rest.split(":"):
            part = part.strip()
            if not part:
                continue
            match = re.fullmatch(r"([A-Z][A-Z0-9_]*)\s+(-?[0-9]+)", part)
            if match is None:
                _semantic(
                    "run_log",
                    f"invalid ShowOptParameters field at line {line_number}",
                )
            name, value = match.groups()
            if name in found:
                _semantic("run_log", f"duplicate ShowOptParameters field: {name}")
            try:
                found[name] = int(value)
            except (TypeError, ValueError) as exc:
                _semantic(
                    "run_log",
                    f"ShowOptParameters {name} is not a representable integer",
                    exc,
                )
    return found


def _parse_ccbench_run_log(raw: bytes) -> tuple[dict[str, int | float], dict[str, int]]:
    """生ログから a07 map と option map を独立に返す。"""

    flags = _parse_ccbench_flags(raw)
    options = _parse_show_opt_parameters(raw)
    if not flags:
        _semantic("run_log", "CCBench log has no #FLAGS_ rows")
    if not options:
        _semantic("run_log", "CCBench log has no #ShowOptParameters() row")
    return flags, options


# Descriptive aliases used by private tests and by the later consumer unit.
_parse_flags_log = _parse_ccbench_flags
_parse_opt_parameters_log = _parse_show_opt_parameters


def _compare_numeric_maps(
    actual: Mapping[str, object],
    expected: Mapping[str, object],
    *,
    label: str,
    integers: bool = False,
) -> None:
    if set(actual) != set(expected):
        _semantic(
            "run_log",
            f"{label} key set mismatch: expected={sorted(expected)!r} "
            f"actual={sorted(actual)!r}",
        )
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if integers:
            numeric = type(actual_value) is int
        else:
            numeric = type(actual_value) in {int, float} and not isinstance(
                actual_value, bool
            )
        if not numeric:
            _semantic("run_log", f"{label}.{key} is not numeric")
        if actual_value != expected_value:
            _semantic(
                "run_log",
                f"{label}.{key} mismatch: expected={expected_value!r} "
                f"actual={actual_value!r}",
            )


def _validate_ccbench_run_log(raw: bytes, *, workload: str) -> None:
    if workload not in _EXPECTED_FLAGS:
        _semantic("run_log", f"unknown workload: {workload!r}")
    try:
        flags, options = _parse_ccbench_run_log(raw)
    except ReceiptParseError as exc:
        _semantic("run_log", "CCBench log JSON/encoding parse failed", exc)
    required_flags = _EXPECTED_FLAGS[workload]
    _compare_numeric_maps(flags, required_flags, label="effective_flags")
    unexpected_options = set(options) - set(_OPT_PARAMETER_KEYS) - set(
        _OPTIONAL_SILO_OPT_PARAMETERS
    )
    if unexpected_options:
        _semantic(
            "run_log",
            "ShowOptParameters contains options outside the silo protocol: "
            f"{sorted(unexpected_options)!r}",
        )
    projected_options = {
        key: options[key] for key in options if key in _OPT_PARAMETER_KEYS
    }
    _compare_numeric_maps(
        projected_options,
        _EXPECTED_OPT_PARAMETERS,
        label="opt_parameters",
        integers=True,
    )


def _parse_preregistration_8key(
    value: object, *, binding: _PreregBinding
) -> PreregistrationRecord:
    """受領証8-key preregistration を内部9-field recordへ adapter する。

    ``_manifest._parse_preregistration_record`` は受領証には存在しない
    ``prereg_commit`` を要求するため、ここではその関数を呼ばない。anchor は
    capability の ``binding.prereg_commit`` だけから注入し、構築後に record の
    9 field 全てを binding record と exact 比較する。
    """

    if type(binding) is not _PreregBinding or getattr(
        binding, "_seal", None
    ) is not _binding._CAPABILITY_TOKEN:
        _semantic("authority", "binding is not the sealed _PreregBinding capability")
    object_value = _mapping(value, "preregistration")
    _exact_keys(object_value, _PREREGISTRATION_KEYS, "preregistration")
    errata_value = object_value["errata"]
    if not isinstance(errata_value, (list, tuple)):
        _semantic("shape", "preregistration.errata must be an array")
    try:
        record = PreregistrationRecord(
            core=_parse_blob_ref(object_value["core"], "core"),
            addendum_a=_parse_blob_ref(object_value["addendum_a"], "addendum_a"),
            addendum_b=(
                None
                if object_value["addendum_b"] is None
                else _parse_blob_ref(object_value["addendum_b"], "addendum_b")
            ),
            fold_commit=object_value["fold_commit"],
            errata=tuple(
                _parse_erratum(item, index)
                for index, item in enumerate(errata_value)
            ),
            approval_manifest=_parse_blob_ref(
                object_value["approval_manifest"], "approval_manifest"
            ),
            receipt_schema=_parse_blob_ref(
                object_value["receipt_schema"], "receipt_schema"
            ),
            composed_core_sha256=object_value["composed_core_sha256"],
            prereg_commit=binding.prereg_commit,
        )
    except (ManifestError, TypeError, ValueError, KeyError) as exc:
        _semantic("preregistration", "8-key preregistration cannot be adapted", exc)

    for field_name in _PREREGISTRATION_RECORD_FIELDS:
        if getattr(record, field_name) != getattr(binding.record, field_name):
            _semantic(
                "preregistration",
                f"preregistration.{field_name} does not exactly match binding.record",
            )
    return record


def _validate_preregistration(
    repository_root: str | os.PathLike[str],
    value: object,
    *,
    binding: _PreregBinding,
) -> PreregistrationRecord:
    record = _parse_preregistration_8key(value, binding=binding)
    try:
        # This is deliberately after construction and the complete nine-field
        # comparison: no adapter-produced value is used before the root-bound
        # capability has rechecked its own Git and root identity invariants.
        binding.assert_intact(repository_root)
    except (_git.GitSupportError, ManifestError) as exc:
        _semantic("authority", "binding.assert_intact rejected the repository", exc)
    return record


def _validate_blob_refs(
    repository_root: str | os.PathLike[str], record: PreregistrationRecord
) -> None:
    try:
        _assert_root_identity(repository_root)
        root = _git.require_git_repository(repository_root)
        _assert_root_identity(repository_root)
    except _git.GitSupportError as exc:
        _semantic("preregistration", "repository cannot be opened for blob verification", exc)
    refs: list[tuple[str, object]] = [
        ("preregistration.core", record.core),
        ("preregistration.addendum_a", record.addendum_a),
        ("preregistration.approval_manifest", record.approval_manifest),
        ("preregistration.receipt_schema", record.receipt_schema),
    ]
    if record.addendum_b is not None:
        refs.append(("preregistration.addendum_b", record.addendum_b))
    refs.extend(
        (
            f"preregistration.errata[{index}]",
            item,
        )
        for index, item in enumerate(record.errata)
    )
    for label, reference in refs:
        try:
            if hasattr(reference, "path"):
                _assert_root_identity(repository_root)
                _git.read_commit_blob(
                    root,
                    commit=reference.commit,
                    path=reference.path,
                    expected_sha256=reference.sha256,
                )
                _assert_root_identity(repository_root)
        except _git.GitSupportError as exc:
            _semantic("preregistration", f"{label} blob cannot be verified", exc)


def _validate_schema_pin(
    record: PreregistrationRecord, binding: _PreregBinding
) -> None:
    if record.receipt_schema != binding.record.receipt_schema:
        _semantic("schema_pin", "receipt_schema is not pinned by binding")


def _a09_key(seed: str, slot: int, workload: str, permutation: str) -> bytes:
    preimage = f"{_A09_ALGORITHM}|{seed}|{slot}|{workload}|{permutation}".encode(
        "ascii"
    )
    return hashlib.sha256(preimage).digest()


def _derive_schedule_rows(seed: str) -> tuple[Mapping[str, object], ...]:
    """a09 の key(j,w,p) から slot 1..13 の 156 block を導出する。"""

    _hex(seed, "schedule_seed", 64)
    rows: list[Mapping[str, object]] = []
    for slot in range(1, 14):
        first = "W2" if slot % 2 else "W1"
        second = "W1" if first == "W2" else "W2"
        for workload in (first, second):
            ordered = tuple(
                sorted(
                    _PERMUTATIONS,
                    key=lambda permutation: (_a09_key(seed, slot, workload, permutation), permutation),
                )
            )
            for block_index, permutation in enumerate(ordered, 1):
                rows.append(
                    {
                        "cluster_slot": slot,
                        "workload": workload,
                        "block_index": block_index,
                        "permutation": permutation,
                    }
                )
    return tuple(rows)


def _canonical_schedule_bytes(seed: str) -> bytes:
    rows = _derive_schedule_rows(seed)
    lines = ["cluster_slot\tworkload\tblock_index\tpermutation"]
    lines.extend(
        f"{row['cluster_slot']}\t{row['workload']}\t{row['block_index']}\t{row['permutation']}"
        for row in rows
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _validate_workload_plans(planned: Mapping[str, Any]) -> None:
    workloads = _mapping(planned.get("workloads"), "planned_execution.workloads")
    _exact_keys(workloads, _WORKLOADS, "planned_execution.workloads")
    for workload in _WORKLOADS:
        plan = _mapping(workloads[workload], f"workloads.{workload}")
        _exact_keys(plan, ("driver_argv", "effective_flags", "opt_parameters"), f"workloads.{workload}")
        argv = plan["driver_argv"]
        if (
            not isinstance(argv, (list, tuple))
            or tuple(argv) != _EXPECTED_DRIVER_ARGV[workload]
            or any(type(item) is not str for item in argv)
        ):
            _semantic("a07", f"workloads.{workload}.driver_argv is not the fixed vector")
        flags = _mapping(plan["effective_flags"], f"workloads.{workload}.effective_flags")
        _compare_numeric_maps(flags, _EXPECTED_FLAGS[workload], label=f"effective_flags.{workload}")
        options = _mapping(plan["opt_parameters"], f"workloads.{workload}.opt_parameters")
        _compare_numeric_maps(
            options,
            _EXPECTED_OPT_PARAMETERS,
            label=f"opt_parameters.{workload}",
            integers=True,
        )


def _validate_schedule(
    repository_root: str | os.PathLike[str], planned: Mapping[str, Any], *, study_stage: str
) -> tuple[Mapping[str, object], ...]:
    """schedule table、digest、cluster slots を raw と seed から再導出する。"""

    _exact_keys(
        planned,
        (
            "workloads",
            "schedule_seed",
            "schedule_algorithm",
            "schedule_table",
            "schedule_sha256",
            "consumed_cluster_slots",
            "cluster_slots",
            "runs",
        ),
        "planned_execution",
    )
    _validate_workload_plans(planned)
    seed = _hex(planned["schedule_seed"], "schedule_seed", 64)
    if seed != _A09_SEED:
        _semantic("schedule", "schedule_seed is not the approved a09 seed")
    if planned["schedule_algorithm"] != _A09_ALGORITHM:
        _semantic("schedule", "schedule_algorithm is not t139-a09-v1")
    consumed = planned["consumed_cluster_slots"]
    if not isinstance(consumed, (list, tuple)) or any(
        type(slot) is not int or not 1 <= slot <= 13 for slot in consumed
    ):
        _semantic("schedule", "consumed_cluster_slots is not an integer subset")
    if len(set(consumed)) != len(consumed) or tuple(consumed) != tuple(sorted(consumed)):
        _semantic("schedule", "consumed_cluster_slots must be sorted and unique")
    if study_stage == "pilot" and list(consumed) != list(range(1, 9)):
        _semantic("schedule", "pilot must consume exactly cluster slots [1..8]")
    if study_stage == "main_run" and not consumed:
        _semantic("schedule", "main_run must consume a non-empty slot subset")

    expected_bytes = _canonical_schedule_bytes(seed)
    table = _mapping(planned["schedule_table"], "planned_execution.schedule_table")
    try:
        actual_bytes = _read_file_record(
            repository_root,
            table,
            label="planned_execution.schedule_table",
        )
    except SemanticValidationError:
        raise
    if actual_bytes != expected_bytes:
        _semantic("schedule", "schedule_table bytes are not the a09 canonical bytes")
    expected_digest = hashlib.sha256(expected_bytes).hexdigest()
    if planned["schedule_sha256"] != expected_digest:
        _semantic("schedule", "schedule_sha256 is only a declaration and is inconsistent")

    rows = planned["cluster_slots"]
    if not isinstance(rows, (list, tuple)) or len(rows) != len(expected_rows := _derive_schedule_rows(seed)):
        _semantic("schedule", "cluster_slots must contain exactly 156 rows")
    for index, (actual, expected) in enumerate(zip(rows, expected_rows)):
        actual_map = _mapping(actual, f"cluster_slots[{index}]")
        _exact_keys(actual_map, ("cluster_slot", "workload", "block_index", "permutation"), f"cluster_slots[{index}]")
        if dict(actual_map) != dict(expected):
            _semantic("schedule", f"cluster_slots[{index}] differs from redriven a09 row")
    return expected_rows


def _planned_rows_for_slot(
    planned: Sequence[Mapping[str, Any]], slot: int
) -> tuple[Mapping[str, Any], ...]:
    selected = [row for row in planned if row.get("cluster_slot") == slot]
    return tuple(selected)


def _arm_for_symbol(symbol: str) -> str:
    try:
        return _ARM_BY_SYMBOL[symbol]
    except KeyError as exc:
        _semantic("schedule", f"unknown arm symbol: {symbol!r}", exc)


def _expected_planned_runs_for_slot(
    schedule_rows: Sequence[Mapping[str, object]], slot: int
) -> tuple[Mapping[str, object], ...]:
    block_rows = [row for row in schedule_rows if row["cluster_slot"] == slot]
    if len(block_rows) != 12:
        _semantic("schedule", f"redriven schedule has no 12 blocks for slot {slot}")
    result: list[Mapping[str, object]] = []
    ordinal = 1
    for block_offset, block in enumerate(block_rows):
        permutation = str(block["permutation"])
        for position, symbol in enumerate(permutation, 1):
            if position == 1:
                predecessor = "START"
                if block_offset == 0:
                    wait_kind, wait_seconds = "none", 0
                elif block["workload"] != block_rows[block_offset - 1]["workload"]:
                    wait_kind, wait_seconds = "workload_switch", 60
                else:
                    wait_kind, wait_seconds = "block_gap", 60
            else:
                predecessor = _arm_for_symbol(permutation[position - 2])
                wait_kind, wait_seconds = "arm_gap", 30
            result.append(
                {
                    "cluster_slot": slot,
                    "workload": block["workload"],
                    "block_index": block["block_index"],
                    "permutation": permutation,
                    "planned_ordinal": ordinal,
                    "position": position,
                    "predecessor_arm": predecessor,
                    "arm": _arm_for_symbol(symbol),
                    "preceding_wait": {"kind": wait_kind, "required_s": wait_seconds},
                }
            )
            ordinal += 1
    return tuple(result)


def _validate_planned_runs(
    planned: Mapping[str, Any], schedule_rows: Sequence[Mapping[str, object]], consumed: Sequence[int]
) -> dict[str, Mapping[str, Any]]:
    runs = planned["runs"]
    if not isinstance(runs, (list, tuple)):
        _semantic("planned_actual", "planned_execution.runs must be an array")
    expected: list[Mapping[str, object]] = []
    for slot in consumed:
        expected.extend(_expected_planned_runs_for_slot(schedule_rows, slot))
    if len(runs) != 36 * len(consumed):
        _semantic("planned_actual", "planned runs must be 36 per consumed cluster slot")
    if len({row.get("run_id") for row in runs if isinstance(row, Mapping)}) != len(runs):
        _semantic("reference", "planned run_id values must be unique")
    by_id: dict[str, Mapping[str, Any]] = {}
    for index, (actual, expected_fields) in enumerate(zip(runs, expected)):
        actual_map = _mapping(actual, f"planned_execution.runs[{index}]")
        _exact_keys(
            actual_map,
            (
                "run_id",
                "cluster_slot",
                "workload",
                "block_index",
                "permutation",
                "planned_ordinal",
                "position",
                "predecessor_arm",
                "arm",
                "preceding_wait",
            ),
            f"planned_execution.runs[{index}]",
        )
        if dict(actual_map) != {**expected_fields, "run_id": actual_map.get("run_id")}:
            for key, expected_value in expected_fields.items():
                if actual_map.get(key) != expected_value:
                    _semantic("planned_actual", f"planned run {index} field {key} differs from schedule")
        run_id = actual_map["run_id"]
        if type(run_id) is not str or not run_id:
            _semantic("reference", f"planned run {index} has an invalid run_id")
        by_id[run_id] = actual_map
    return by_id


def _argv_from_compile_entry(entry: Mapping[str, Any], label: str) -> tuple[str, ...]:
    if "arguments" in entry:
        arguments = entry["arguments"]
        if not isinstance(arguments, (list, tuple)) or any(type(item) is not str for item in arguments):
            _semantic("compile", f"{label}.arguments is not a string vector")
        return tuple(arguments)
    command = entry.get("command")
    if type(command) is not str:
        _semantic("compile", f"{label} has neither arguments nor command")
    try:
        return tuple(shlex.split(command, posix=True))
    except ValueError as exc:
        _semantic("compile", f"{label}.command cannot be tokenized", exc)


def _load_compile_command_entries(
    repository_root: str | os.PathLike[str], record: Mapping[str, object], *, label: str
) -> tuple[tuple[Mapping[str, Any], tuple[str, ...]], ...]:
    raw = _read_file_record(repository_root, record, label=label)
    try:
        document = _strict_json(raw, label=label)
    except ReceiptParseError as exc:
        _semantic("compile", f"{label} cannot be parsed", exc)
    if not isinstance(document, list):
        _semantic("compile", f"{label} root must be an array")
    result: list[tuple[Mapping[str, Any], tuple[str, ...]]] = []
    for index, item in enumerate(document):
        entry = _mapping(item, f"{label}[{index}]")
        result.append(
            (
                entry,
                _argv_from_compile_entry(entry, f"{label}[{index}]"),
            )
        )
    if not result:
        _semantic("compile", f"{label} must not be empty")
    return tuple(result)


def _load_compile_commands(
    repository_root: str | os.PathLike[str], record: Mapping[str, object]
) -> tuple[tuple[str, ...], ...]:
    return tuple(
        argv
        for _, argv in _load_compile_command_entries(
            repository_root, record, label="compile_commands"
        )
    )


def _macro_value(argv: Sequence[str], name: str, *, label: str) -> int:
    prefix = f"-D{name}="
    values = [item[len(prefix) :] for item in argv if item.startswith(prefix)]
    if len(values) != 1 or values[0] not in {"0", "1"}:
        _semantic("compile", f"{label} has no unique {name}=0/1 macro")
    return int(values[0])


def _parse_cmake_cache(raw: bytes) -> dict[str, int]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        _semantic("compile", "CMakeCache.txt is not UTF-8", exc)
    values: dict[str, int] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        match = re.fullmatch(r"(CCBENCH_TRACE|CCBENCH_ADD_ANALYSIS):[^=]*=(.*)", line)
        if match is None:
            continue
        name, value = match.groups()
        normalized = {"ON": 1, "OFF": 0, "TRUE": 1, "FALSE": 0}.get(value.upper())
        if normalized is None and value in {"0", "1"}:
            normalized = int(value)
        if normalized is None:
            _semantic("compile", f"CMakeCache line {line_number} has invalid {name}")
        if name in values:
            _semantic("compile", f"CMakeCache has duplicate {name}")
        values[name] = normalized
    if set(values) != {"CCBENCH_TRACE", "CCBENCH_ADD_ANALYSIS"}:
        _semantic("compile", "CMakeCache does not expose both CCBENCH macro values")
    return values


def _cache_path_for_compile_commands(path: str) -> str:
    posix = PurePosixPath(path)
    parent = posix.parent.as_posix()
    return "CMakeCache.txt" if parent == "." else f"{parent}/CMakeCache.txt"


def _validate_compile_legs(
    repository_root: str | os.PathLike[str],
    compile_record: Mapping[str, Any],
    *,
    expected_trace: int,
    expected_analysis: int,
    label: str = "compile",
) -> None:
    """configure argv・compile_commands 実体・raw sibling CMakeCache を正の3脚にする。

    ``cmake_cache``・``trace_enabled``・``analysis_enabled`` の申告は不一致を
    拒否するだけで、一致から positive verdict を導出しない。
    """

    if not isinstance(compile_record, Mapping):
        _semantic("compile", f"{label} is not an object")
    configure = compile_record.get("configure_argv", compile_record.get("argv"))
    if not isinstance(configure, (list, tuple)) or any(type(item) is not str for item in configure):
        _semantic("compile", f"{label}.configure_argv/argv is not a string vector")
    configure_trace = _macro_value(configure, "CCBENCH_TRACE", label=label)
    configure_analysis = _macro_value(configure, "CCBENCH_ADD_ANALYSIS", label=label)
    if (configure_trace, configure_analysis) != (expected_trace, expected_analysis):
        _semantic("compile", f"{label} configure macro legs disagree")

    compile_commands = _mapping(compile_record.get("compile_commands"), f"{label}.compile_commands")
    command_vectors = _load_compile_commands(repository_root, compile_commands)
    for index, argv in enumerate(command_vectors):
        if _macro_value(argv, "TRACE", label=f"{label}.compile_commands[{index}]") != expected_trace:
            _semantic("compile", f"{label}.compile_commands trace macro differs")
        if _macro_value(argv, "ADD_ANALYSIS", label=f"{label}.compile_commands[{index}") != expected_analysis:
            _semantic("compile", f"{label}.compile_commands analysis macro differs")

    cache_path = compile_record.get("cmake_cache_path")
    if cache_path is None:
        raw_path = compile_commands.get("path")
        if type(raw_path) is not str:
            _semantic("compile", f"{label}.compile_commands.path is invalid")
        cache_path = _cache_path_for_compile_commands(raw_path)
    # The receipt schema has no CMakeCache fileRecord.  For a normal receipt,
    # the sibling is located by the compile_commands path and is read through
    # the same no-follow descriptor layer, but its unpinned metadata is not
    # invented.  Private unit fixtures may provide an explicit sidecar record;
    # those fields are never accepted by shape validation.
    if "cmake_cache_record" in compile_record:
        try:
            cache_raw = _read_file_record(
                repository_root,
                _mapping(compile_record["cmake_cache_record"], f"{label}.cmake_cache_record"),
                label=f"{label}.CMakeCache.txt",
            )
        except SemanticValidationError as exc:
            _semantic("compile", f"{label} CMakeCache sidecar is unavailable", exc)
    else:
        try:
            _assert_root_identity(repository_root)
            cache_raw = read_relative_regular_bytes(
                repository_root,
                cache_path,
                max_bytes=_MAX_POINTER_BYTES,
            )
            _assert_root_identity(repository_root)
        except (SafeIOError, ValueError) as exc:
            _semantic("compile", f"{label} CMakeCache sidecar is unavailable", exc)
    cache = _parse_cmake_cache(cache_raw)
    if cache != {
        "CCBENCH_TRACE": expected_trace,
        "CCBENCH_ADD_ANALYSIS": expected_analysis,
    }:
        _semantic("compile", f"{label} CMakeCache macro legs disagree")

    declared_cache = _mapping(compile_record.get("cmake_cache"), f"{label}.cmake_cache")
    declared_trace = _exact_int(
        declared_cache.get("trace"), f"{label}.cmake_cache.trace", minimum=0
    )
    declared_analysis = _exact_int(
        declared_cache.get("add_analysis"),
        f"{label}.cmake_cache.add_analysis",
        minimum=0,
    )
    if (declared_trace, declared_analysis) != (expected_trace, expected_analysis):
        _semantic("compile", f"{label}.cmake_cache declaration is inconsistent")
    if compile_record.get("trace_enabled") is not (expected_trace == 1):
        _semantic("compile", f"{label}.trace_enabled declaration is inconsistent")
    if compile_record.get("analysis_enabled") is not (expected_analysis == 1):
        _semantic("compile", f"{label}.analysis_enabled declaration is inconsistent")


def _validate_correctness_builds(
    repository_root: str | os.PathLike[str], value: Mapping[str, Any], arms: Mapping[str, Any]
) -> None:
    evidence = value.get("correctness_evidence", ())
    if not isinstance(evidence, (list, tuple)):
        _semantic("correctness", "correctness_evidence must be an array")
    for index, item in enumerate(evidence):
        entry = _mapping(item, f"correctness_evidence[{index}]")
        build = _mapping(entry.get("build"), f"correctness_evidence[{index}].build")
        compile_record = _mapping(build.get("compile"), f"correctness_evidence[{index}].build.compile")
        arm = entry.get("arm")
        if arm not in _ARMS:
            _semantic("correctness", f"correctness_evidence[{index}] has unknown arm")
        arm_record = _mapping(arms.get(arm), f"arms.{arm}")
        performance_compile = _mapping(
            arm_record.get("compile"), f"arms.{arm}.compile"
        )
        if build.get("source") != performance_compile.get("source"):
            _semantic(
                "correctness",
                f"correctness_evidence[{index}].build.source differs from the performance source",
            )
        _validate_compile_legs(
            repository_root,
            compile_record,
            expected_trace=1,
            expected_analysis=1,
            label=f"correctness_evidence[{index}].build.compile",
        )
        performance_binary = _mapping(arm_record.get("binary"), f"arms.{arm}.binary")
        correctness_binary = _mapping(build.get("binary"), f"correctness_evidence[{index}].build.binary")
        if correctness_binary.get("sha256") == performance_binary.get("sha256"):
            _semantic("correctness", f"correctness binary reuses performance binary for {arm}")


def _validate_performance_compile_legs(
    repository_root: str | os.PathLike[str], value: Mapping[str, Any]
) -> None:
    arms = _mapping(value.get("arms"), "arms")
    _exact_keys(arms, _ARMS, "arms")
    for arm in _ARMS:
        arm_value = _mapping(arms[arm], f"arms.{arm}")
        compile_record = _mapping(arm_value.get("compile"), f"arms.{arm}.compile")
        _validate_compile_legs(
            repository_root,
            compile_record,
            expected_trace=0,
            expected_analysis=0,
            label=f"arms.{arm}.compile",
        )


def _tree_object_for_commit(
    repository_root: str | os.PathLike[str], commit: str, *, label: str
) -> str:
    try:
        _assert_root_identity(repository_root)
        root = _git.require_git_repository(repository_root)
        _git.require_commit_object(root, commit)
        result = _git._git(root, ["rev-parse", "--verify", f"{commit}^{{tree}}"])
        _assert_root_identity(repository_root)
    except _git.GitSupportError as exc:
        _semantic("source", f"{label} commit cannot be verified", exc)
    if result.returncode != 0 or not re.fullmatch(rb"[0-9a-f]{40}\n", result.stdout):
        _semantic("source", f"{label} tree object cannot be derived")
    return result.stdout[:-1].decode("ascii")


def _strict_repo_relative_path(value: object, *, label: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.startswith("/")
        or "\x00" in value
        or "\r" in value
        or "\n" in value
    ):
        _semantic("source", f"{label} is not a strict repo-relative path")
    path = PurePosixPath(value)
    if (
        not path.parts
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        _semantic("source", f"{label} is not POSIX-normalized")
    return value


def _compile_command_file_path(
    repository_root: str | os.PathLike[str],
    entry: Mapping[str, Any],
    *,
    label: str,
) -> str:
    raw_file = entry.get("file")
    if type(raw_file) is not str or not raw_file:
        _semantic("source", f"{label}.file is missing or invalid")
    file_path = PurePosixPath(raw_file)
    if any(part in {"..", ""} for part in file_path.parts):
        _semantic("source", f"{label}.file contains an unsafe component")
    root_absolute = PurePosixPath(os.path.abspath(os.fspath(repository_root))).as_posix()
    if file_path.is_absolute():
        if raw_file == root_absolute:
            _semantic("source", f"{label}.file points at the repository directory")
        prefix = root_absolute.rstrip("/") + "/"
        if not raw_file.startswith(prefix):
            _semantic("source", f"{label}.file is outside repository_root")
        candidate = raw_file[len(prefix) :]
    else:
        directory = entry.get("directory", ".")
        if type(directory) is not str or not directory:
            _semantic("source", f"{label}.directory is invalid")
        directory_path = PurePosixPath(directory)
        if directory_path.is_absolute():
            directory_text = directory_path.as_posix()
            prefix = root_absolute.rstrip("/") + "/"
            if not directory_text.startswith(prefix):
                _semantic("source", f"{label}.directory is outside repository_root")
            directory_path = PurePosixPath(directory_text[len(prefix) :])
        candidate = (directory_path / file_path).as_posix()
    normalized = PurePosixPath(candidate).as_posix()
    return _strict_repo_relative_path(normalized, label=f"{label}.file")


def _validate_source_identity(
    repository_root: str | os.PathLike[str],
    value: Mapping[str, Any],
    *,
    measurement_head: str | None = None,
) -> None:
    checkout = _mapping(value.get("measurement_checkout"), "measurement_checkout")
    repository_head = _hex(checkout.get("repository_head"), "measurement_checkout.repository_head", 40)
    ccbench_head = _hex(checkout.get("ccbench_head"), "measurement_checkout.ccbench_head", 40)
    if ccbench_head != _CCBENCH_PIN:
        _semantic("source", "measurement_checkout.ccbench_head is not the approved a08 CCBench pin")
    if measurement_head is not None and repository_head != measurement_head:
        _semantic("source", "measurement_checkout.repository_head is not the binding measurement head")
    if type(value.get("measurement_checkout")) is not dict and not isinstance(value.get("measurement_checkout"), Mapping):
        _semantic("source", "measurement_checkout is not an object")
    for arm in _ARMS:
        arm_value = _mapping(_mapping(value.get("arms"), "arms").get(arm), f"arms.{arm}")
        compile_record = _mapping(arm_value.get("compile"), f"arms.{arm}.compile")
        source = _mapping(compile_record.get("source"), f"arms.{arm}.compile.source")
        source_commit = _hex(source.get("repo_commit"), f"arms.{arm}.source.repo_commit", 40)
        if source_commit != repository_head:
            _semantic("source", f"arms.{arm}.source.repo_commit is not measurement checkout")
        if source.get("ccbench_pin") != ccbench_head:
            _semantic("source", f"arms.{arm}.source.ccbench_pin is not measurement checkout")
        expected_mode = _EXPECTED_MODE_MACROS[arm]
        if compile_record.get("mode_macro") != expected_mode:
            _semantic("source", f"arms.{arm}.compile.mode_macro is not the fixed a08 mode")
        if arm == "stock":
            if source.get("patch_path") is not None or source.get("patch_sha256") is not None:
                _semantic("source", "stock compile must not claim a patch")
        elif (
            source.get("patch_path") != _EXPECTED_PATCH_PATH
            or source.get("patch_sha256") != _EXPECTED_PATCH_SHA256
        ):
            _semantic("source", f"{arm} compile patch identity is not the fixed a08 patch")
        translation_units = _mapping(
            compile_record.get("translation_units"),
            f"arms.{arm}.compile.translation_units",
        )
        if not translation_units:
            _semantic(
                "source",
                f"arms.{arm}.compile.translation_units must not be empty",
            )
        # Reject an unnormalized declaration before consulting any unrelated
        # compile_commands leg so the negative vector remains single-cause.
        for path in translation_units:
            _strict_repo_relative_path(
                path,
                label=f"arms.{arm}.compile.translation_units key",
            )
        compile_commands = _mapping(
            compile_record.get("compile_commands"),
            f"arms.{arm}.compile.compile_commands",
        )
        command_entries = _load_compile_command_entries(
            repository_root,
            compile_commands,
            label=f"arms.{arm}.compile.compile_commands",
        )
        command_by_path: dict[str, tuple[str, ...]] = {}
        for command_index, (entry, argv) in enumerate(command_entries):
            command_path = _compile_command_file_path(
                repository_root,
                entry,
                label=f"arms.{arm}.compile.compile_commands[{command_index}]",
            )
            if command_path in command_by_path:
                _semantic(
                    "source",
                    f"{arm} compile_commands repeats translation unit {command_path!r}",
                )
            command_by_path[command_path] = argv
        declared_paths = {
            _strict_repo_relative_path(
                path,
                label=f"arms.{arm}.compile.translation_units key",
            )
            for path in translation_units
        }
        if declared_paths != set(command_by_path):
            _semantic(
                "source",
                f"{arm} translation_units do not cover compile_commands: "
                f"declared={sorted(declared_paths)!r} "
                f"commands={sorted(command_by_path)!r}",
            )
        for path, unit in translation_units.items():
            normalized_path = _strict_repo_relative_path(
                path,
                label=f"arms.{arm}.compile.translation_units[{path!r}]",
            )
            unit_map = _mapping(unit, f"translation_units[{path!r}]")
            _exact_keys(
                unit_map,
                ("normalized_argv", "sha256"),
                f"translation_units[{path!r}]",
            )
            normalized_argv = unit_map.get("normalized_argv")
            if not isinstance(normalized_argv, (list, tuple)) or any(
                type(argument) is not str for argument in normalized_argv
            ):
                _semantic(
                    "source",
                    f"translation_units[{path!r}].normalized_argv is not a string vector",
                )
            command_argv = command_by_path[normalized_path]
            if tuple(normalized_argv) != command_argv:
                _semantic(
                    "source",
                    f"translation_units[{path!r}].normalized_argv differs from "
                    "compile_commands",
                )
            declared_digest = _hex(
                unit_map.get("sha256"), f"translation_units[{path!r}].sha256", 64
            )
            _assert_root_identity(repository_root)
            try:
                actual_unit_bytes = read_relative_regular_bytes(
                    repository_root,
                    normalized_path,
                    max_bytes=_MAX_POINTER_BYTES,
                )
            except (SafeIOError, ValueError) as exc:
                _semantic(
                    "source",
                    f"arms.{arm}.compile.translation_units[{path!r}] cannot be read",
                    exc,
                )
            _assert_root_identity(repository_root)
            actual_digest = hashlib.sha256(actual_unit_bytes).hexdigest()
            if declared_digest != actual_digest:
                _semantic(
                    "source",
                    f"translation_units[{path!r}].sha256 does not match the "
                    "source or compile_commands entity",
                )
        derived_tree = _tree_object_for_commit(
            repository_root, source_commit, label=f"arms.{arm}.source.repo_commit"
        )
        if source.get("base_tree_sha") != derived_tree:
            _semantic("source", f"arms.{arm}.source.base_tree_sha is not redriven")


def _validate_reference_graph(
    value: Mapping[str, Any], planned_by_id: Mapping[str, Mapping[str, Any]]
) -> None:
    attempts = value.get("attempts")
    allocations = value.get("allocations")
    actual_runs = value.get("actual_runs")
    liveness = value.get("liveness")
    correctness = value.get("correctness_evidence")
    if not all(isinstance(item, (list, tuple)) for item in (attempts, allocations, actual_runs, liveness, correctness)):
        _semantic("reference", "reference-bearing fields must be arrays")
    identifiers: dict[str, set[str]] = {
        "attempt_id": set(),
        "allocation_id": set(),
        "run_id": set(),
    }
    attempt_by_id: dict[str, Mapping[str, Any]] = {}
    allocation_by_id: dict[str, Mapping[str, Any]] = {}
    for field, entries in (("attempt_id", attempts), ("allocation_id", allocations), ("run_id", actual_runs)):
        for index, entry in enumerate(entries):
            item = _mapping(entry, f"{field}[{index}]")
            if field == "attempt_id":
                key = item.get("attempt_id")
            elif field == "allocation_id":
                key = item.get("allocation_id")
            else:
                key = item.get("run_id")
            if type(key) is not str or not key or key in identifiers[field]:
                _semantic("reference", f"{field} is missing, non-string, or duplicate")
            identifiers[field].add(key)
            if field == "attempt_id":
                attempt_by_id[key] = item
            elif field == "allocation_id":
                allocation_by_id[key] = item
    for index, item in enumerate(actual_runs):
        entry = _mapping(item, f"actual_runs[{index}]")
        for field in ("attempt_id", "allocation_id", "run_id"):
            if entry.get(field) not in identifiers[field]:
                _semantic("reference", f"actual_runs[{index}].{field} is dangling")
        attempt = attempt_by_id[entry["attempt_id"]]
        if attempt.get("allocation_id") != entry.get("allocation_id"):
            _semantic("reference", f"actual_runs[{index}] crosses attempt/allocation identities")
    for index, item in enumerate(liveness):
        entry = _mapping(item, f"liveness[{index}]")
        if entry.get("allocation_id") not in identifiers["allocation_id"]:
            _semantic("reference", f"liveness[{index}].allocation_id is dangling")
    for index, item in enumerate(correctness):
        entry = _mapping(item, f"correctness_evidence[{index}]")
        scope = _mapping(entry.get("run_scope"), f"correctness_evidence[{index}].run_scope")
        if scope.get("allocation_id") not in identifiers["allocation_id"]:
            _semantic("reference", f"correctness_evidence[{index}].run_scope.allocation_id is dangling")
        elif allocation_by_id[scope["allocation_id"]].get("allocation_role") != "verification":
            _semantic(
                "reference",
                f"correctness_evidence[{index}] does not use the verification allocation",
            )
    for index, item in enumerate(attempts):
        entry = _mapping(item, f"attempts[{index}]")
        for field in ("replaces_attempt_id", "parent_attempt_id"):
            target = entry.get(field)
            if target is not None and target not in identifiers["attempt_id"]:
                _semantic("reference", f"attempts[{index}].{field} is dangling")
            if target is not None and target == entry.get("attempt_id"):
                _semantic("reference", f"attempts[{index}].{field} cannot self-reference")
        allocation_id = entry.get("allocation_id")
        if allocation_id is not None and allocation_id not in identifiers["allocation_id"]:
            _semantic("reference", f"attempts[{index}].allocation_id is dangling")
        if allocation_id is not None:
            allocation = allocation_by_id[allocation_id]
            slot = entry.get("cluster_slot_or_null")
            allocation_slot = allocation.get("cluster_slot_or_null")
            if slot != allocation_slot:
                _semantic("reference", f"attempts[{index}] crosses slot/allocation identities")
    for start_attempt_id in attempt_by_id:
        visited: set[str] = set()
        current: str | None = start_attempt_id
        while current is not None:
            if current in visited:
                _semantic(
                    "reference",
                    f"replacement chain cycles at attempt {current}",
                )
            visited.add(current)
            target = attempt_by_id[current].get("replaces_attempt_id")
            current = target if type(target) is str else None
    for index, item in enumerate(allocations):
        entry = _mapping(item, f"allocations[{index}]")
        role = entry.get("allocation_role")
        slot = entry.get("cluster_slot_or_null")
        if role == "performance_cluster" and (type(slot) is not int or not 1 <= slot <= 13):
            _semantic("reference", f"performance allocation {index} has no valid slot")
        if role == "verification" and slot is not None:
            _semantic("reference", f"verification allocation {index} must have null slot")
    if sum(
        1
        for entry in allocations
        if isinstance(entry, Mapping) and entry.get("allocation_role") == "verification"
    ) != 1:
        _semantic("reference", "a study stage must contain exactly one verification allocation")
    if set(planned_by_id) != {entry.get("run_id") for entry in value["planned_execution"]["runs"]}:
        _semantic("reference", "planned run graph is inconsistent")


def _validate_cardinality_and_ordinals(value: Mapping[str, Any]) -> None:
    environment = _mapping(value.get("environment"), "environment")
    attestations = environment.get("attestations")
    if not isinstance(attestations, (list, tuple)):
        _semantic("cardinality", "environment.attestations must be an array")
    if sum(item.get("profile_kind") == "expected" for item in attestations if isinstance(item, Mapping)) != 1:
        _semantic("cardinality", "environment must have exactly one expected attestation")
    if sum(item.get("profile_kind") == "observed" for item in attestations if isinstance(item, Mapping)) < 1:
        _semantic("cardinality", "environment must have an observed attestation")
    _require_ordinal_sequence(attestations, "environment.attestations")

    dependency_pins = value.get("dependency_pins")
    if not isinstance(dependency_pins, (list, tuple)) or {
        item.get("name") for item in dependency_pins if isinstance(item, Mapping)
    } != set(_DEPENDENCIES) or len(dependency_pins) != 5:
        _semantic("cardinality", "dependency_pins must cover each dependency exactly once")
    for index, raw_pin in enumerate(dependency_pins):
        pin = _mapping(raw_pin, f"dependency_pins[{index}]")
        name = pin.get("name")
        if name not in _EXPECTED_DEPENDENCY_PINS:
            _semantic("cardinality", f"dependency_pins[{index}] has an unknown dependency")
        if pin.get("commit") != _EXPECTED_DEPENDENCY_PINS[name]:
            _semantic("cardinality", f"dependency_pins[{index}] is not the approved a08 pin")
    _require_ordinal_sequence(value.get("correctness_evidence"), "correctness_evidence")
    _require_ordinal_sequence(value.get("liveness"), "liveness")
    _require_ordinal_sequence(value.get("admission_telemetry"), "admission_telemetry")
    _require_ordinal_sequence(value.get("attempts"), "attempts", field=None)
    liveness = value.get("liveness")
    if not isinstance(liveness, (list, tuple)):
        _semantic("cardinality", "liveness must be an array")
    for index, raw_probe in enumerate(liveness):
        probe = _mapping(raw_probe, f"liveness[{index}]")
        kind = probe.get("probe")
        if kind not in {
            "liveness_run",
            "allocation_alive",
            "driver_heartbeat",
            "filesystem_writable",
        }:
            _semantic("cardinality", f"liveness[{index}] has an unknown probe")
        arm = probe.get("arm_or_null")
        workload = probe.get("workload_or_null")
        if kind == "liveness_run":
            if arm not in _ARMS or workload not in _WORKLOADS:
                _semantic("cardinality", f"liveness[{index}] lacks its run pair")
        elif arm is not None or workload is not None:
            _semantic("cardinality", f"liveness[{index}] has a non-run pair")
    telemetry = value.get("admission_telemetry")
    if not isinstance(telemetry, (list, tuple)):
        _semantic("cardinality", "admission_telemetry must be an array")
    kinds = [item.get("kind") for item in telemetry if isinstance(item, Mapping)]
    if any(
        isinstance(allocation, Mapping)
        and allocation.get("allocation_role") == "performance_cluster"
        for allocation in value.get("allocations", ())
    ):
        if kinds.count("alpha_reservation") != 1:
            _semantic("cardinality", "performance stage must have exactly one alpha reservation")
        if kinds.count("stress_check_simulation") < 1:
            _semantic("cardinality", "performance stage must have a stress simulation")


def _require_ordinal_sequence(
    entries: object, label: str, *, field: str | None = "ordinal"
) -> None:
    if not isinstance(entries, (list, tuple)):
        _semantic("cardinality", f"{label} must be an array")
    if field is None:
        return
    values = [item.get(field) for item in entries if isinstance(item, Mapping)]
    if values != list(range(1, len(values) + 1)):
        _semantic("cardinality", f"{label} ordinals must be a 1-origin sequence")


def _parse_cpu_row(raw: bytes, *, label: str) -> tuple[int, ...] | str:
    try:
        text = raw.decode("ascii", errors="strict")
    except UnicodeDecodeError as exc:
        _semantic("a03", f"{label} is not ASCII / proc-stat text", exc)
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        _semantic("a03", f"{label} has no cpu row")
    fields = lines[0].split()
    if not fields or fields[0] != "cpu":
        _semantic("a03", f"{label} does not begin with aggregate cpu row")
    numbers = fields[1:]
    if len(numbers) < 8:
        return "short_columns"
    if len(numbers) > 8:
        _semantic("a03", f"{label} has more than the allowed eight cpu columns")
    parsed: list[int] = []
    for field in numbers:
        if not re.fullmatch(r"[0-9]+", field):
            _semantic("a03", f"{label} contains a non-negative integer violation")
        parsed.append(int(field))
    return tuple(parsed)


def _derive_a03_failure(
    stat_before_raw: bytes,
    stat_after_raw: bytes,
    *,
    monotonic_start_ns: int,
    monotonic_end_ns: int,
) -> A03Result:
    """a03 の raw counter と窓長を再計算し、申告値を参照しない。"""

    if type(monotonic_start_ns) is not int or monotonic_start_ns < 0:
        _semantic("a03", "monotonic_start_ns must be a non-negative integer")
    if type(monotonic_end_ns) is not int or monotonic_end_ns < 0:
        _semantic("a03", "monotonic_end_ns must be a non-negative integer")

    before = _parse_cpu_row(stat_before_raw, label="stat_before_raw")
    after = _parse_cpu_row(stat_after_raw, label="stat_after_raw")
    if before == "short_columns" or after == "short_columns":
        return A03Result("short_columns", None, True, (), ())
    before_tuple = before  # type: ignore[assignment]
    after_tuple = after  # type: ignore[assignment]
    if any(after_value < before_value for before_value, after_value in zip(before_tuple, after_tuple)):
        return A03Result("negative_delta", None, True, before_tuple, after_tuple)
    deltas = tuple(after_value - before_value for before_value, after_value in zip(before_tuple, after_tuple))
    total = sum(deltas)
    if total <= 0:
        return A03Result("nonpositive_total", None, True, before_tuple, after_tuple)
    elapsed = (monotonic_end_ns - monotonic_start_ns) / 1_000_000_000
    if not 9.9 <= elapsed <= 10.1:
        return A03Result("window_out_of_range", None, True, before_tuple, after_tuple)
    busy = 48.0 * (total - deltas[3]) / total
    return A03Result(None, busy, not 0.0 <= busy <= 1.0, before_tuple, after_tuple)


def _decode_argv_raw(raw: bytes, *, label: str) -> tuple[str, ...]:
    """argv_raw の許容される durable 表現を strict に復元する。"""

    stripped = raw.lstrip()
    if stripped.startswith(b"["):
        try:
            parsed = _strict_json(raw, label=label)
        except ReceiptParseError as exc:
            _semantic("argv", f"{label} JSON argv cannot be parsed", exc)
    else:
        parsed = None
    if isinstance(parsed, list) and all(type(item) is str for item in parsed):
        return tuple(parsed)
    if b"\x00" in raw:
        parts = raw.split(b"\x00")
        if parts and parts[-1] == b"":
            parts.pop()
        try:
            decoded = tuple(part.decode("utf-8", errors="strict") for part in parts)
        except UnicodeDecodeError as exc:
            _semantic("argv", f"{label} is not UTF-8 argv bytes", exc)
        if decoded and all(part != "" for part in decoded):
            return decoded
    try:
        lines = raw.decode("utf-8", errors="strict").splitlines()
    except UnicodeDecodeError as exc:
        _semantic("argv", f"{label} is not UTF-8 argv bytes", exc)
    if lines and all(line != "" for line in lines):
        return tuple(lines)
    _semantic("argv", f"{label} is not a supported argv vector")


def _validate_wait_and_run_logs(
    repository_root: str | os.PathLike[str],
    value: Mapping[str, Any],
    planned_by_id: Mapping[str, Mapping[str, Any]],
) -> None:
    actual_runs = value.get("actual_runs")
    if not isinstance(actual_runs, (list, tuple)):
        _semantic("planned_actual", "actual_runs must be an array")
    seen: set[str] = set()
    arms = _mapping(value.get("arms"), "arms")
    for index, item in enumerate(actual_runs):
        actual = _mapping(item, f"actual_runs[{index}]")
        run_id = actual.get("run_id")
        if run_id in seen:
            _semantic("planned_actual", f"actual_runs[{index}] repeats run_id")
        seen.add(run_id)
        if run_id not in planned_by_id:
            _semantic("planned_actual", f"actual_runs[{index}] references unknown planned run")
        planned = planned_by_id[run_id]
        for field in (
            "cluster_slot",
            "workload",
            "block_index",
            "permutation",
            "position",
            "predecessor_arm",
            "arm",
        ):
            if actual.get(field) != planned.get(field):
                _semantic("planned_actual", f"actual_runs[{index}].{field} differs from planned run")
        wait = _mapping(actual.get("preceding_wait"), f"actual_runs[{index}].preceding_wait")
        planned_wait = _mapping(planned.get("preceding_wait"), f"planned run {run_id}.preceding_wait")
        if wait.get("kind") != planned_wait.get("kind") or wait.get("required_s") != planned_wait.get("required_s"):
            _semantic("wait", f"actual_runs[{index}] wait declaration differs from a02")
        start = _exact_int(wait.get("monotonic_start_ns"), f"actual_runs[{index}].wait.start", minimum=0)
        end = _exact_int(wait.get("monotonic_end_ns"), f"actual_runs[{index}].wait.end", minimum=0)
        if end < start:
            _semantic("wait", f"actual_runs[{index}] wait is not monotonic")
        expected_ns = int(wait["required_s"]) * 1_000_000_000
        if end - start != expected_ns:
            _semantic("wait", f"actual_runs[{index}] uses adaptive/non-exact wait")
        run_start = _exact_int(actual.get("started_at_monotonic_ns"), f"actual_runs[{index}].start", minimum=0)
        run_end = _exact_int(actual.get("ended_at_monotonic_ns"), f"actual_runs[{index}].end", minimum=0)
        if run_end < run_start:
            _semantic("phase", f"actual_runs[{index}] timestamps are not monotonic")
        argv_raw = _read_file_record(
            repository_root,
            _mapping(actual.get("argv_raw"), f"actual_runs[{index}].argv_raw"),
            label=f"actual_runs[{index}].argv_raw",
        )
        argv = _decode_argv_raw(argv_raw, label=f"actual_runs[{index}].argv_raw")
        workload = actual.get("workload")
        if workload not in _EXPECTED_DRIVER_ARGV or argv != _EXPECTED_DRIVER_ARGV[workload]:
            _semantic("argv", f"actual_runs[{index}].argv_raw differs from planned workload argv")
        if actual.get("argv_sha256") != hashlib.sha256(argv_raw).hexdigest():
            _semantic("argv", f"actual_runs[{index}].argv_sha256 is not the raw digest")
        arm = actual.get("arm")
        arm_value = _mapping(arms.get(arm), f"arms.{arm}")
        binary = _mapping(arm_value.get("binary"), f"arms.{arm}.binary")
        if actual.get("binary_sha256") != binary.get("sha256"):
            _semantic("binary", f"actual_runs[{index}].binary_sha256 is not the checked arm binary")
        witness = _mapping(actual.get("exec_witness"), f"actual_runs[{index}].exec_witness")
        for field in ("path", "size", "sha256"):
            if witness.get(field) != binary.get(field):
                _semantic("binary", f"actual_runs[{index}].exec_witness.{field} differs from the checked arm binary")
        run_log = _read_file_record(
            repository_root,
            _mapping(actual.get("run_log"), f"actual_runs[{index}].run_log"),
            label=f"actual_runs[{index}].run_log",
        )
        _validate_ccbench_run_log(run_log, workload=workload)


def _raw_mapping_from_output(raw: bytes, *, label: str) -> Mapping[str, Any] | None:
    if not raw.lstrip().startswith(b"{"):
        return None
    try:
        value = _strict_json(raw, label=label)
    except ReceiptParseError as exc:
        _semantic("correctness", f"{label} JSON output cannot be parsed", exc)
    if isinstance(value, Mapping):
        return value
    return None


def _raw_correctness_has_anomaly(raw: bytes, *, label: str) -> bool:
    """correctness raw bytes から expected/actual の不一致を判定する。

    ``verdict``, ``clean``、``match`` などの申告だけは見ない。比較可能な
    expected/actual payload が raw に存在する場合だけ、その実体を比較する。
    解析不能な bytes、比較対象を持たない JSON、認識不能なテキストは
    ``clean`` として扱わず fail-closed で拒否する。
    """

    def compare_json(value: object) -> tuple[bool, bool]:
        pairs = (
            ("expected", "actual"),
            ("expected_output", "actual_output"),
            ("expected_sha256", "actual_sha256"),
            ("expected_value", "actual_value"),
        )
        if isinstance(value, Mapping):
            anomaly = False
            comparable = False
            for left, right in pairs:
                if left in value and right in value:
                    comparable = True
                    anomaly = (value[left] != value[right]) or anomaly
            for child in value.values():
                child_anomaly, child_comparable = compare_json(child)
                anomaly = child_anomaly or anomaly
                comparable = child_comparable or comparable
            return anomaly, comparable
        if isinstance(value, (list, tuple)):
            anomaly = False
            comparable = False
            for child in value:
                child_anomaly, child_comparable = compare_json(child)
                anomaly = child_anomaly or anomaly
                comparable = child_comparable or comparable
            return anomaly, comparable
        return False, False

    stripped = raw.lstrip()
    if stripped.startswith((b"{", b"[")):
        try:
            parsed = _strict_json(raw, label=label)
        except ReceiptParseError as exc:
            _semantic("correctness", f"{label} JSON output cannot be parsed", exc)
        anomaly, comparable = compare_json(parsed)
        if not comparable:
            _semantic(
                "correctness",
                f"{label} contains no comparable expected/actual raw evidence",
            )
        return anomaly
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        _semantic("correctness", f"{label} is not UTF-8 raw evidence", exc)
    values: dict[str, str] = {}
    for line in text.splitlines():
        match = re.fullmatch(r"\s*(expected|actual)(?:_output|_value)?\s*[:=]\s*(.*?)\s*", line)
        if match:
            values[match.group(1)] = match.group(2)
    if "expected" not in values or "actual" not in values:
        _semantic(
            "correctness",
            f"{label} contains no comparable expected/actual raw evidence",
        )
    return values["expected"] != values["actual"]


def _validate_correctness_raw_evidence(
    repository_root: str | os.PathLike[str], value: Mapping[str, Any]
) -> bool:
    anomaly = False
    evidence = value.get("correctness_evidence", ())
    if not isinstance(evidence, (list, tuple)):
        _semantic("correctness", "correctness_evidence must be an array")
    for index, item in enumerate(evidence):
        entry = _mapping(item, f"correctness_evidence[{index}]")
        outputs = entry.get("outputs")
        if not isinstance(outputs, (list, tuple)):
            _semantic("correctness", f"correctness_evidence[{index}].outputs must be an array")
        for output_index, pointer in enumerate(outputs):
            raw = _read_file_record(
                repository_root,
                _mapping(pointer, f"correctness_evidence[{index}].outputs[{output_index}]"),
                label=f"correctness_evidence[{index}].outputs[{output_index}]",
            )
            anomaly = _raw_correctness_has_anomaly(
                raw, label=f"correctness_evidence[{index}].outputs[{output_index}]"
            ) or anomaly
    return anomaly


def _observation_failure(
    repository_root: str | os.PathLike[str], observation: Mapping[str, Any]
) -> A03Result:
    before_record = _mapping(observation.get("stat_before_raw"), "stat_before_raw")
    after_record = _mapping(observation.get("stat_after_raw"), "stat_after_raw")
    before_raw = _read_file_record(repository_root, before_record, label="stat_before_raw")
    after_raw = _read_file_record(repository_root, after_record, label="stat_after_raw")
    result = _derive_a03_failure(
        before_raw,
        after_raw,
        monotonic_start_ns=_exact_int(observation.get("monotonic_start_ns"), "observation.start", minimum=0),
        monotonic_end_ns=_exact_int(observation.get("monotonic_end_ns"), "observation.end", minimum=0),
    )
    declared_reason = observation.get("malformed_reason")
    if declared_reason != result.malformed_reason:
        _semantic(
            "a03",
            "malformed_reason does not equal the first raw-derived failure",
        )
    if len(result.stat_before) > 0 and tuple(observation.get("stat_before", ())) != result.stat_before:
        _semantic("a03", "stat_before declaration is not the raw stat row")
    if len(result.stat_after) > 0 and tuple(observation.get("stat_after", ())) != result.stat_after:
        _semantic("a03", "stat_after declaration is not the raw stat row")
    return result


def _validate_observations(
    repository_root: str | os.PathLike[str], value: Mapping[str, Any]
) -> dict[str, A03Result]:
    results: dict[str, A03Result] = {}
    for attempt_index, item in enumerate(value.get("attempts", ())):
        attempt = _mapping(item, f"attempts[{attempt_index}]")
        observations = attempt.get("environment_observations")
        if not isinstance(observations, (list, tuple)):
            _semantic("a03", f"attempts[{attempt_index}].environment_observations must be an array")
        actual_runs = _actual_runs_for_attempt(value, attempt.get("attempt_id"))
        if attempt.get("cluster_slot_or_null") is not None:
            if actual_runs:
                expected_observation_count = len(actual_runs)
            elif attempt.get("reason_code") == "post_performance_failure" and observations:
                # The a03-only post-start route has a preflight window but no
                # actual run.  It is the one deliberate zero-run exception to
                # the normal prefix cardinality.
                expected_observation_count = 1
            else:
                expected_observation_count = 0
            if attempt.get("reason_code") == "completed" and len(actual_runs) != 36:
                _semantic("cardinality", "completed performance attempt requires 36 actual runs")
            if len(observations) != expected_observation_count:
                _semantic(
                    "cardinality",
                    f"performance attempt requires {expected_observation_count} observation windows",
                )
            if observations:
                first = _mapping(observations[0], "environment_observations[0]")
                if first.get("scope") != "preflight" or first.get("run_id_or_null") is not None:
                    _semantic("a03", "the first performance observation must be a run-free preflight window")
                expected_pre_run_ids = [item.get("run_id") for item in actual_runs[1:]]
                actual_pre_run_ids = [
                    _mapping(item, "pre_run observation").get("run_id_or_null")
                    for item in observations[1:]
                ]
                if actual_pre_run_ids != expected_pre_run_ids:
                    _semantic("reference", "pre_run observations must cover the strict actual-run suffix")
                if any(
                    _mapping(item, "pre_run observation").get("scope") != "pre_run"
                    for item in observations[1:]
                ):
                    _semantic("a03", "performance observation scopes are not preflight followed by pre_run")
                actual_by_id = {item.get("run_id"): item for item in actual_runs}
                for observation in observations:
                    observation_map = _mapping(observation, "environment_observation")
                    observation_end = _exact_int(
                        observation_map.get("monotonic_end_ns"),
                        "observation.monotonic_end_ns",
                        minimum=0,
                    )
                    run_id = observation_map.get("run_id_or_null")
                    target = actual_runs[0] if run_id is None else actual_by_id.get(run_id)
                    if target is None:
                        _semantic("reference", "observation points to no actual execution")
                    exec_time = _exact_int(
                        target.get("started_at_monotonic_ns"),
                        "actual_run.started_at_monotonic_ns",
                        minimum=0,
                    )
                    if exec_time < observation_end or exec_time - observation_end > 5_000_000_000:
                        _semantic("a03", "observation ended more than five seconds from the corresponding exec")
        for observation_index, raw_observation in enumerate(observations):
            observation = _mapping(
                raw_observation,
                f"attempts[{attempt_index}].environment_observations[{observation_index}]",
            )
            result = _observation_failure(repository_root, observation)
            run_id = observation.get("run_id_or_null")
            if run_id is not None:
                results[run_id] = result
            results[f"attempt:{attempt.get('attempt_id')}:{observation_index}"] = result
    return results


def _actual_runs_for_attempt(value: Mapping[str, Any], attempt_id: object) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        _mapping(item, "actual_run")
        for item in value.get("actual_runs", ())
        if isinstance(item, Mapping) and item.get("attempt_id") == attempt_id
    )


def _attempt_observation_failures(
    observations: Mapping[str, A03Result], attempt_id: object
) -> tuple[A03Result, ...]:
    if type(attempt_id) is not str:
        return ()
    prefix = "attempt:"
    results: list[A03Result] = []
    for key, result in observations.items():
        if not key.startswith(prefix):
            continue
        owner_and_index = key[len(prefix) :]
        owner, separator, index = owner_and_index.rpartition(":")
        if separator and index.isdigit() and owner == attempt_id:
            results.append(result)
    return tuple(results)


def _validate_reason_branches(
    value: Mapping[str, Any], observation_results: Mapping[str, A03Result], *, anomaly: bool
) -> None:
    """reason_code を raw marker/run/a03/correctness facts からだけ評価する。"""

    attempts = value.get("attempts")
    if not isinstance(attempts, (list, tuple)):
        _semantic("reason", "attempts must be an array")
    consumed = tuple(value["planned_execution"]["consumed_cluster_slots"])
    performance_slots: dict[int, int] = {}
    for attempt_index, raw_attempt in enumerate(attempts):
        attempt = _mapping(raw_attempt, f"attempts[{attempt_index}]")
        reason = attempt.get("reason_code")
        attempt_id = attempt.get("attempt_id")
        slot = attempt.get("cluster_slot_or_null")
        actual = _actual_runs_for_attempt(value, attempt_id)
        marker = attempt.get("performance_started_marker")
        failure_evidence = attempt.get("failure_evidence")
        a03_failures = _attempt_observation_failures(observation_results, attempt_id)
        derived_a03_failure = any(result.failure for result in a03_failures)
        replacement = attempt.get("replaces_attempt_id")
        if replacement is not None:
            if replacement == attempt_id:
                _semantic("reason", f"attempt {attempt_id} cannot replace itself")
            if reason != "pre_performance_infra_failure":
                _semantic("reason", f"only pre-performance infra failures may be replaced: {attempt_id}")
            targets = {
                candidate.get("attempt_id"): candidate
                for candidate in attempts
                if isinstance(candidate, Mapping)
            }
            target = targets.get(replacement)
            if target is None or target.get("reason_code") != "pre_performance_infra_failure":
                _semantic("reason", f"replacement target is not a pre-performance infra failure: {replacement}")
            if target.get("cluster_slot_or_null") != slot:
                _semantic("reason", "replacement must reuse the target cluster slot")
        if slot is not None and slot not in consumed:
            _semantic("reason", f"attempt {attempt_id} references an unconsumed slot")
        if reason == "completed":
            if attempt.get("allocation_id") is None:
                _semantic("reason", f"completed attempt {attempt_id} has no allocation")
            if slot is None:
                if marker is not None or actual:
                    _semantic("reason", f"completed verification attempt {attempt_id} has performance facts")
                evidence = [
                    entry
                    for entry in value.get("correctness_evidence", ())
                    if isinstance(entry, Mapping)
                    and _mapping(entry.get("run_scope"), "run_scope").get("allocation_id")
                    == attempt.get("allocation_id")
                ]
                live = [
                    entry
                    for entry in value.get("liveness", ())
                    if isinstance(entry, Mapping)
                    and entry.get("allocation_id") == attempt.get("allocation_id")
                    and entry.get("probe") == "liveness_run"
                ]
                if len(evidence) != 6 or len(live) != 6:
                    _semantic("reason", "completed verification requires six correctness/liveness pairs")
                evidence_pairs = {(entry.get("arm"), entry.get("workload")) for entry in evidence}
                live_pairs = {(entry.get("arm_or_null"), entry.get("workload_or_null")) for entry in live}
                expected_pairs = {(arm, workload) for arm in _ARMS for workload in _WORKLOADS}
                if evidence_pairs != expected_pairs or live_pairs != expected_pairs:
                    _semantic("cardinality", "completed verification does not cover each arm/workload pair exactly once")
            else:
                if marker is None or failure_evidence is not None or not actual:
                    _semantic("reason", f"completed performance attempt {attempt_id} lacks raw completion facts")
                if slot in performance_slots:
                    _semantic("reason", f"slot {slot} has more than one completed performance attempt")
                performance_slots[slot] = attempt_index
                expected_ids = {
                    run_id
                    for run_id, planned in _planned_ids_for_slot(value, slot)
                }
                actual_ids = {entry.get("run_id") for entry in actual}
                if actual_ids != expected_ids or len(actual) != 36:
                    _semantic("planned_actual", f"completed slot {slot} is not a complete 36-run bijection")
            if anomaly:
                # A correctness output with an actual expected/actual mismatch
                # must kill a clean/completed declaration; this is raw evidence,
                # not an enum inversion test.
                _semantic("correctness", "raw correctness evidence contains an anomaly")
        elif reason == "pre_performance_infra_failure":
            if marker is not None or actual or derived_a03_failure or failure_evidence is None:
                _semantic("reason", f"pre-performance failure {attempt_id} has a post-start fact")
        elif reason == "post_performance_failure":
            if failure_evidence is None or (marker is None and not actual and not derived_a03_failure):
                _semantic("reason", f"post-performance failure {attempt_id} lacks one of the three raw routes")
        elif reason == "correctness_anomaly":
            if attempt.get("replaces_attempt_id") is not None:
                _semantic("reason", "correctness_anomaly cannot replace another attempt")
            evidence = _mapping(failure_evidence, f"attempts[{attempt_index}].failure_evidence") if failure_evidence is not None else None
            if evidence is None or evidence.get("kind") != "correctness" or not anomaly:
                _semantic("correctness", "correctness_anomaly requires raw mismatching correctness output")
        else:
            _semantic("reason", f"unsupported reason_code for attempt {attempt_id}")

    # Section 7.1(1) preserves 0-5 entries when verification records a failure;
    # require six pairs when performance completes with no verification outcome.
    # performance_slots passed the loop's raw checks, not just reason_code claims.
    verification_failure_recorded = any(
        isinstance(attempt, Mapping)
        and attempt.get("cluster_slot_or_null") is None
        and attempt.get("reason_code") != "completed"
        for attempt in attempts
    )
    if performance_slots and not verification_failure_recorded:
        evidence = value.get("correctness_evidence", ())
        evidence_pairs = {
            (entry.get("arm"), entry.get("workload"))
            for entry in evidence
            if isinstance(entry, Mapping)
        }
        expected_pairs = {(arm, workload) for arm in _ARMS for workload in _WORKLOADS}
        if len(evidence) != 6 or evidence_pairs != expected_pairs:
            _semantic(
                "correctness",
                "completed performance without a recorded verification failure "
                "requires six correctness arm/workload pairs",
            )


def _planned_ids_for_slot(
    value: Mapping[str, Any], slot: int
) -> tuple[tuple[str, Mapping[str, Any]], ...]:
    rows = []
    for item in value["planned_execution"]["runs"]:
        if isinstance(item, Mapping) and item.get("cluster_slot") == slot:
            rows.append((item.get("run_id"), item))
    return tuple(rows)


def _validate_planned_actual_relationship(
    value: Mapping[str, Any], planned_by_id: Mapping[str, Mapping[str, Any]]
) -> None:
    actual_runs = value.get("actual_runs")
    attempts = value.get("attempts")
    if not isinstance(actual_runs, (list, tuple)) or not isinstance(attempts, (list, tuple)):
        _semantic("planned_actual", "actual_runs and attempts must be arrays")
    by_attempt: dict[object, list[Mapping[str, Any]]] = {}
    for item in actual_runs:
        entry = _mapping(item, "actual_run")
        by_attempt.setdefault(entry.get("attempt_id"), []).append(entry)
    for attempt in attempts:
        entry = _mapping(attempt, "attempt")
        attempt_id = entry.get("attempt_id")
        actual = by_attempt.get(attempt_id, [])
        slot = entry.get("cluster_slot_or_null")
        actual_ordinals = [item.get("actual_ordinal") for item in actual]
        if actual_ordinals != list(range(1, len(actual_ordinals) + 1)):
            _semantic(
                "planned_actual",
                f"attempt {attempt_id} actual ordinal is not a strict sequence",
            )
        if slot is None:
            if actual:
                _semantic("planned_actual", f"verification attempt {attempt_id} has actual performance runs")
            continue
        expected_rows = [
            row for row in value["planned_execution"]["runs"]
            if isinstance(row, Mapping) and row.get("cluster_slot") == slot
        ]
        expected_ids = [row.get("run_id") for row in expected_rows]
        actual_ids = [item.get("run_id") for item in actual]
        if entry.get("reason_code") == "completed":
            if len(actual) != 36 or actual_ids != expected_ids:
                _semantic("planned_actual", f"completed attempt {attempt_id} is not a complete planned bijection")
        else:
            if actual_ids != expected_ids[: len(actual_ids)]:
                _semantic("planned_actual", f"attempt {attempt_id} actual runs are not a planned prefix")


def _phase_cap_table(role: str) -> Mapping[str, tuple[int, int]]:
    if role == "performance_cluster":
        return _PERFORMANCE_PHASE_CAPS
    if role == "verification":
        return _VERIFICATION_PHASE_CAPS
    _semantic("phase", f"unknown allocation role: {role!r}")


def _validate_phase_budget(value: Mapping[str, Any]) -> None:
    for allocation_index, raw_allocation in enumerate(value.get("allocations", ())):
        allocation = _mapping(raw_allocation, f"allocations[{allocation_index}]")
        role = allocation.get("allocation_role")
        caps = _phase_cap_table(role)
        phase_caps = allocation.get("phase_caps")
        phase_events = allocation.get("phase_events")
        if not isinstance(phase_caps, (list, tuple)) or not isinstance(phase_events, (list, tuple)):
            _semantic("phase", f"allocations[{allocation_index}] phase data must be arrays")
        cap_map: dict[str, tuple[int, int]] = {}
        for cap_index, raw_cap in enumerate(phase_caps):
            cap = _mapping(raw_cap, f"phase_caps[{cap_index}]")
            phase = cap.get("phase")
            if phase in cap_map or phase not in caps:
                _semantic("phase", f"allocations[{allocation_index}] has invalid/duplicate phase cap")
            cap_s = _exact_int(cap.get("cap_s"), f"phase_caps[{cap_index}].cap_s", minimum=0)
            sub_cap = cap.get("sub_cap_s_or_null")
            if sub_cap is not None:
                _exact_int(sub_cap, f"phase_caps[{cap_index}].sub_cap_s_or_null", minimum=0)
            if (cap_s, sub_cap) != caps[phase]:
                _semantic("phase", f"phase cap for {phase} is not the a01 fixed value")
            cap_map[phase] = (cap_s, sub_cap)
        if set(cap_map) != set(caps):
            _semantic("phase", f"allocations[{allocation_index}] phase cap set is incomplete")
        event_map: dict[str, list[tuple[str, int]]] = {phase: [] for phase in caps}
        all_times: list[int] = []
        for event_index, raw_event in enumerate(phase_events):
            event = _mapping(raw_event, f"phase_events[{event_index}]")
            phase = event.get("phase")
            if phase not in caps:
                _semantic("phase", f"phase event has invalid phase {phase!r}")
            event_name = event.get("event")
            if event_name not in {"enter", "leave", "term_signal"}:
                _semantic("phase", f"phase event has invalid event kind {event_name!r}")
            timestamp = _exact_int(event.get("monotonic_ns"), f"phase_events[{event_index}].monotonic_ns", minimum=0)
            event_map[phase].append((event_name, timestamp))
            all_times.append(timestamp)
        if all_times != sorted(all_times):
            _semantic("phase", f"allocations[{allocation_index}] phase events are not monotonic")
        entered_phases = [
            event.get("phase")
            for event in phase_events
            if isinstance(event, Mapping) and event.get("event") == "enter"
        ]
        if entered_phases != list(caps):
            _semantic("phase", f"allocations[{allocation_index}] phase order is not the fixed role order")
        for phase, phase_events_for_phase in event_map.items():
            if not phase_events_for_phase or len(phase_events_for_phase) < 2:
                _semantic("phase", f"phase {phase} lacks enter/leave events")
            if phase_events_for_phase[0][0] != "enter" or phase_events_for_phase[-1][0] != "leave":
                _semantic("phase", f"phase {phase} does not have enter-before-leave structure")
            times = [timestamp for _, timestamp in phase_events_for_phase]
            elapsed = max(times) - min(times)
            cap_s = cap_map[phase][0]
            if elapsed > cap_s * 1_000_000_000:
                _semantic("phase", f"phase {phase} exceeds its fixed cap")
            sub_cap_s = cap_map[phase][1]
            if sub_cap_s is not None and elapsed > sub_cap_s * 1_000_000_000:
                _semantic("phase", f"phase {phase} exceeds its fixed sub-cap")
        started = _exact_int(allocation.get("started_at_monotonic_ns"), "allocation.started_at", minimum=0)
        ended = _exact_int(allocation.get("ended_at_monotonic_ns"), "allocation.ended_at", minimum=0)
        if ended < started or any(timestamp < started or timestamp > ended for timestamp in all_times):
            _semantic("phase", "allocation phase event lies outside allocation interval")
        internal_deadline = _exact_int(allocation.get("internal_deadline_s"), "allocation.internal_deadline_s", minimum=1)
        requested = _exact_int(allocation.get("requested_walltime_s"), "allocation.requested_walltime_s", minimum=1)
        if ended - started > internal_deadline * 1_000_000_000:
            _semantic(
                "phase",
                f"allocation {allocation_index} elapsed time exceeds its internal deadline",
            )
        if role == "verification":
            expected_requested, expected_deadline = 3600, 3300
        elif allocation.get("path_choice") == "primary_build_outside":
            expected_requested, expected_deadline = 3600, 3300
        else:
            expected_requested, expected_deadline = 5400, 4800
        if requested != expected_requested or internal_deadline != expected_deadline:
            _semantic("phase", "allocation walltime/deadline does not match fixed a01/a06 budget")
        if role == "performance_cluster":
            serial_phases = ("preflight", "run", "teardown")
        else:
            serial_phases = tuple(caps)
        serial_cap_s = sum(cap_map[phase][0] for phase in serial_phases)
        if serial_cap_s > internal_deadline:
            _semantic("phase", "serial phase budget exceeds the internal deadline")

        allocation_id = allocation.get("allocation_id")
        previous_run_end: int | None = None
        for raw_run in value.get("actual_runs", ()):
            if not isinstance(raw_run, Mapping) or raw_run.get("allocation_id") != allocation_id:
                continue
            wait = _mapping(raw_run.get("preceding_wait"), "actual_run.preceding_wait")
            wait_start = _exact_int(wait.get("monotonic_start_ns"), "actual_run.wait.start", minimum=0)
            wait_end = _exact_int(wait.get("monotonic_end_ns"), "actual_run.wait.end", minimum=0)
            run_start = _exact_int(raw_run.get("started_at_monotonic_ns"), "actual_run.start", minimum=0)
            run_end = _exact_int(raw_run.get("ended_at_monotonic_ns"), "actual_run.end", minimum=0)
            witness = _mapping(raw_run.get("exec_witness"), "actual_run.exec_witness")
            witness_time = _exact_int(witness.get("monotonic_ns"), "actual_run.exec_witness.monotonic_ns", minimum=0)
            if not wait_start <= wait_end <= run_start <= run_end:
                _semantic("phase", "actual run/wait timestamps are not monotonic")
            if previous_run_end is not None and wait_start < previous_run_end:
                _semantic("phase", "actual runs overlap or are out of order")
            previous_run_end = run_end
            run_times = (wait_start, wait_end, run_start, run_end, witness_time)
            if any(timestamp < started or timestamp > ended for timestamp in run_times):
                _semantic("phase", "actual run timestamp lies outside allocation interval")
            if witness_time < run_start or witness_time > run_end:
                _semantic("phase", "exec witness timestamp lies outside the run interval")

        previous_observation_end: int | None = None
        for raw_attempt in value.get("attempts", ()):
            if not isinstance(raw_attempt, Mapping) or raw_attempt.get("allocation_id") != allocation_id:
                continue
            submitted = _exact_int(raw_attempt.get("submitted_at_monotonic_ns"), "attempt.submitted_at", minimum=0)
            if not started <= submitted <= ended:
                _semantic("phase", "attempt submission lies outside allocation interval")
            marker = raw_attempt.get("performance_started_marker")
            if isinstance(marker, Mapping) and marker.get("created_at_monotonic_ns") is not None:
                created = _exact_int(marker.get("created_at_monotonic_ns"), "marker.created_at", minimum=0)
                if not started <= created <= ended:
                    _semantic("phase", "performance marker lies outside allocation interval")
            for raw_observation in raw_attempt.get("environment_observations", ()):
                if not isinstance(raw_observation, Mapping):
                    continue
                observation_start = _exact_int(raw_observation.get("monotonic_start_ns"), "observation.start", minimum=0)
                observation_end = _exact_int(raw_observation.get("monotonic_end_ns"), "observation.end", minimum=0)
                if observation_end < observation_start:
                    _semantic("phase", "environment observation is not monotonic")
                if previous_observation_end is not None and observation_start < previous_observation_end:
                    _semantic("phase", "environment observations overlap or are out of order")
                previous_observation_end = observation_end
                if observation_start < started or observation_end > ended:
                    _semantic("phase", "environment observation lies outside allocation interval")


def _read_pointer(
    repository_root: str | os.PathLike[str], record: object, *, label: str
) -> bytes:
    return _read_file_record(
        repository_root,
        _mapping(record, label),
        label=label,
    )


def _read_artifact_pointer(
    repository_root: str | os.PathLike[str], record: object, *, label: str
) -> bytes:
    value = _mapping(record, label)
    return _read_file_record(
        repository_root,
        {
            "path": value.get("artifact_path"),
            "size": value.get("size"),
            "sha256": value.get("sha256"),
        },
        label=label,
    )


def _read_marker_pointer(
    repository_root: str | os.PathLike[str], record: object, *, label: str
) -> bytes:
    value = _mapping(record, label)
    return _read_file_record(
        repository_root,
        {
            "path": value.get("path"),
            "size": value.get("size"),
            "sha256": value.get("sha256"),
        },
        label=label,
    )


def _validate_all_pointers(
    repository_root: str | os.PathLike[str], value: Mapping[str, Any]
) -> None:
    """既知の全 fileRecord を safe-I/O helper の単一入口で再読する。"""

    def pointer(field: object, label: str) -> None:
        _read_pointer(repository_root, field, label=label)

    environment = _mapping(value.get("environment"), "environment")
    for index, item in enumerate(environment.get("attestations", ())):
        pointer(_mapping(item, "attestation").get("raw"), f"environment.attestations[{index}].raw")
    arms = _mapping(value.get("arms"), "arms")
    for arm in _ARMS:
        arm_value = _mapping(arms[arm], f"arms.{arm}")
        pointer(arm_value.get("binary"), f"arms.{arm}.binary")
        _read_artifact_pointer(
            repository_root,
            arm_value.get("built_outside_allocation"),
            label=f"arms.{arm}.built_outside_allocation",
        )
        compile_record = _mapping(arm_value.get("compile"), f"arms.{arm}.compile")
        pointer(compile_record.get("compile_commands"), f"arms.{arm}.compile.compile_commands")
    planned = _mapping(value.get("planned_execution"), "planned_execution")
    pointer(planned.get("schedule_table"), "planned_execution.schedule_table")
    for index, item in enumerate(value.get("allocations", ())):
        allocation = _mapping(item, f"allocations[{index}]")
        pointer(allocation.get("path_choice_intent"), f"allocations[{index}].path_choice_intent")
        pointer(allocation.get("accounting_trace"), f"allocations[{index}].accounting_trace")
        exclusivity = _mapping(allocation.get("exclusivity"), f"allocations[{index}].exclusivity")
        pointer(exclusivity.get("raw"), f"allocations[{index}].exclusivity.raw")
    for index, item in enumerate(value.get("actual_runs", ())):
        run = _mapping(item, f"actual_runs[{index}]")
        pointer(run.get("argv_raw"), f"actual_runs[{index}].argv_raw")
        pointer(run.get("run_log"), f"actual_runs[{index}].run_log")
    for index, item in enumerate(value.get("correctness_evidence", ())):
        evidence = _mapping(item, f"correctness_evidence[{index}]")
        build = _mapping(evidence.get("build"), f"correctness_evidence[{index}].build")
        pointer(build.get("binary"), f"correctness_evidence[{index}].build.binary")
        compile_record = _mapping(build.get("compile"), f"correctness_evidence[{index}].build.compile")
        pointer(compile_record.get("compile_commands"), f"correctness_evidence[{index}].build.compile.compile_commands")
        for output_index, output in enumerate(evidence.get("outputs", ())):
            pointer(output, f"correctness_evidence[{index}].outputs[{output_index}]")
    for index, item in enumerate(value.get("liveness", ())):
        pointer(_mapping(item, f"liveness[{index}]").get("raw"), f"liveness[{index}].raw")
    for index, item in enumerate(value.get("admission_telemetry", ())):
        pointer(_mapping(item, f"admission_telemetry[{index}]").get("receipt"), f"admission_telemetry[{index}].receipt")
    for index, item in enumerate(value.get("attempts", ())):
        attempt = _mapping(item, f"attempts[{index}]")
        pointer(attempt.get("intent_ref"), f"attempts[{index}].intent_ref")
        pointer(_mapping(attempt.get("qsub_result"), "qsub_result").get("raw"), f"attempts[{index}].qsub_result.raw")
        marker = attempt.get("performance_started_marker")
        if marker is not None:
            _read_marker_pointer(repository_root, marker, label=f"attempts[{index}].performance_started_marker")
        failure = attempt.get("failure_evidence")
        if failure is not None:
            pointer(_mapping(failure, "failure_evidence").get("pointer"), f"attempts[{index}].failure_evidence.pointer")
        for observation_index, raw_observation in enumerate(attempt.get("environment_observations", ())):
            observation = _mapping(raw_observation, "environment_observation")
            pointer(observation.get("stat_before_raw"), f"attempts[{index}].environment_observations[{observation_index}].stat_before_raw")
            pointer(observation.get("stat_after_raw"), f"attempts[{index}].environment_observations[{observation_index}].stat_after_raw")


def _validate_create_only_references(
    repository_root: str | os.PathLike[str], value: Mapping[str, Any]
) -> None:
    seen_intents: dict[str, str] = {}
    seen_markers: dict[str, str] = {}
    for index, raw_attempt in enumerate(value.get("attempts", ())):
        attempt = _mapping(raw_attempt, f"attempts[{index}]")
        intent = _mapping(attempt.get("intent_ref"), f"attempts[{index}].intent_ref")
        path = intent.get("path")
        digest = intent.get("sha256")
        if type(path) is not str or type(digest) is not str:
            _semantic("pointer", f"attempts[{index}].intent_ref is not a fileRecord")
        if path in seen_intents and seen_intents[path] != digest:
            _semantic("intent", "intent_ref path was changed between attempts")
        seen_intents[path] = digest
        marker = attempt.get("performance_started_marker")
        if marker is not None:
            marker_map = _mapping(marker, f"attempts[{index}].performance_started_marker")
            marker_path = marker_map.get("path")
            marker_digest = marker_map.get("sha256")
            if type(marker_path) is not str or type(marker_digest) is not str:
                _semantic("pointer", "performance_started_marker is not a valid pointer")
            if marker_path in seen_markers and seen_markers[marker_path] != marker_digest:
                _semantic("intent", "performance_started_marker path was changed")
            seen_markers[marker_path] = marker_digest


def _validate_allocation_shape_semantics(value: Mapping[str, Any]) -> None:
    for index, raw_allocation in enumerate(value.get("allocations", ())):
        allocation = _mapping(raw_allocation, f"allocations[{index}]")
        role = allocation.get("allocation_role")
        if role not in {"performance_cluster", "verification"}:
            _semantic("allocation", f"invalid allocation role: {role!r}")
        path_choice = allocation.get("path_choice")
        if path_choice not in {"primary_build_outside", "fallback_build_inside"}:
            _semantic("allocation", f"{role} path_choice is invalid")
        slot = allocation.get("cluster_slot_or_null")
        if role == "verification":
            if slot is not None:
                _semantic("allocation", "verification allocation must have a null slot")
        elif type(slot) is not int or slot not in value["planned_execution"]["consumed_cluster_slots"]:
            _semantic("allocation", "performance allocation slot is outside consumed slots")
        start = _exact_int(allocation.get("started_at_monotonic_ns"), "allocation.started_at", minimum=0)
        end = _exact_int(allocation.get("ended_at_monotonic_ns"), "allocation.ended_at", minimum=0)
        if end < start:
            _semantic("allocation", "allocation interval is not monotonic")
    for arm in _ARMS:
        arm_value = _mapping(_mapping(value.get("arms"), "arms")[arm], f"arms.{arm}")
        performance_binary = _mapping(arm_value.get("binary"), f"arms.{arm}.binary")
        artifact = _mapping(arm_value.get("built_outside_allocation"), f"arms.{arm}.built_outside_allocation")
        if performance_binary.get("sha256") != artifact.get("sha256"):
            # The immutable artifact is the verification build output and is
            # expected to be different from the performance binary in the
            # normal design.  Do not use this declaration as an acceptance
            # proof; only reject an impossible missing identity.
            if type(performance_binary.get("sha256")) is not str or type(artifact.get("sha256")) is not str:
                _semantic("allocation", f"arms.{arm} binary identity is malformed")


def _validate_slots_and_counts(value: Mapping[str, Any]) -> None:
    planned = _mapping(value.get("planned_execution"), "planned_execution")
    consumed = planned.get("consumed_cluster_slots")
    if not isinstance(consumed, (list, tuple)) or any(
        type(slot) is not int or not 1 <= slot <= 13 for slot in consumed
    ):
        _semantic("cardinality", "consumed cluster slots are not valid integers")
    if tuple(consumed) != tuple(sorted(set(consumed))):
        _semantic("cardinality", "consumed cluster slots are not a sorted unique subset")
    if value.get("study_stage") == "pilot" and list(consumed) != list(range(1, 9)):
        _semantic("cardinality", "pilot slot count/identity is not exactly eight prefix slots")
    if value.get("study_stage") == "main_run" and not consumed:
        _semantic("cardinality", "main_run has no consumed slots")
    allowed = set(consumed)
    for label, entries, field in (
        ("allocations", value.get("allocations", ()), "cluster_slot_or_null"),
        ("attempts", value.get("attempts", ()), "cluster_slot_or_null"),
        ("actual_runs", value.get("actual_runs", ()), "cluster_slot"),
    ):
        for index, entry in enumerate(entries):
            if not isinstance(entry, Mapping):
                continue
            slot = entry.get(field)
            if slot is not None and slot not in allowed:
                _semantic("cardinality", f"{label}[{index}] references an unconsumed slot")
    actual_by_allocation: dict[object, list[Mapping[str, Any]]] = {}
    for raw_run in value.get("actual_runs", ()):
        if isinstance(raw_run, Mapping):
            actual_by_allocation.setdefault(raw_run.get("allocation_id"), []).append(raw_run)

    arms = _mapping(value.get("arms"), "arms")
    for index, raw_allocation in enumerate(value.get("allocations", ())):
        allocation = _mapping(raw_allocation, f"allocations[{index}]")
        rehashes = allocation.get("binary_rehash")
        if not isinstance(rehashes, (list, tuple)):
            _semantic("cardinality", f"allocations[{index}].binary_rehash must be an array")
        seen: set[tuple[object, object]] = set()
        rehash_by_point: dict[object, set[object]] = {}
        for rehash_index, raw_rehash in enumerate(rehashes):
            rehash = _mapping(raw_rehash, f"binary_rehash[{rehash_index}]")
            key = (rehash.get("point"), rehash.get("arm"))
            if key in seen:
                _semantic("cardinality", "binary_rehash point/arm pair is duplicated")
            seen.add(key)
            if allocation.get("allocation_role") == "verification":
                _semantic("cardinality", "verification allocation must have no binary_rehash entries")
            if rehash.get("point") not in {"after_staging", "before_first_run", "after_last_run"}:
                _semantic("cardinality", "binary_rehash has an unknown point")
            if rehash.get("arm") not in _ARMS:
                _semantic("cardinality", "binary_rehash has an unknown arm")
            _hex(rehash.get("sha256"), "binary_rehash.sha256", 64)
            _exact_int(
                rehash.get("monotonic_ns"),
                "binary_rehash.monotonic_ns",
                minimum=0,
            )
            rehash_by_point.setdefault(rehash.get("point"), set()).add(rehash.get("arm"))
            arm_value = _mapping(arms[rehash.get("arm")], f"arms.{rehash.get('arm')}")
            binary = _mapping(arm_value.get("binary"), f"arms.{rehash.get('arm')}.binary")
            if rehash.get("sha256") != binary.get("sha256"):
                _semantic("cardinality", "binary_rehash does not match the checked performance binary")
        if allocation.get("allocation_role") == "verification" and rehashes:
            _semantic("cardinality", "verification binary_rehash is non-empty")
        if allocation.get("allocation_role") == "performance_cluster":
            actual = actual_by_allocation.get(allocation.get("allocation_id"), [])
            if actual:
                expected_points = {"after_staging", "before_first_run", "after_last_run"}
            elif rehashes:
                expected_points = {"after_staging"}
            else:
                expected_points = set()
            expected_pairs = {
                (point, arm)
                for point in expected_points
                for arm in _ARMS
            }
            if seen != expected_pairs:
                _semantic(
                    "cardinality",
                    "binary_rehash does not match the reached allocation points",
                )
            if any(rehash_by_point.get(point, set()) != set(_ARMS) for point in expected_points):
                _semantic("cardinality", "each reached binary_rehash point must cover all three arms")


def _validate_reject_only(
    repository_root: str | os.PathLike[str], value: Mapping[str, Any]
) -> None:
    """申告値は不一致を reject できるが、一致を受理の根拠にしない。"""

    # The field is intentionally observed only as an intent label.  No branch
    # below treats ``dry`` (or any other value) as a bypass.
    if value.get("declared_use_class") not in {"official", "exploration", "qualification", "dry"}:
        _semantic("reject_only", "declared_use_class is outside the closed intent set")
    telemetry = value.get("admission_telemetry", ())
    for index, raw_item in enumerate(telemetry):
        item = _mapping(raw_item, f"admission_telemetry[{index}]")
        kind = item.get("kind")
        fixed = _mapping(item.get("fixed_inputs"), f"admission_telemetry[{index}].fixed_inputs")
        if kind == "stress_check_simulation":
            if type(fixed.get("B_or_null")) is not int or fixed["B_or_null"] <= 0:
                _semantic("reject_only", "stress simulation B must be a positive integer")
            _hex(fixed.get("seed_or_null"), "stress simulation seed", 64)
        elif fixed.get("B_or_null") is not None or fixed.get("seed_or_null") is not None:
            _semantic("reject_only", f"non-stress telemetry {kind!r} has stress-only fixed inputs")
        raw = _read_pointer(
            repository_root,
            item.get("receipt"),
            label=f"admission_telemetry[{index}].receipt",
        )
        # If the transcript voluntarily exposes its fixed inputs, mismatch is
        # a reject-only check.  Absence of these optional diagnostic keys does
        # not become positive evidence for the producer.
        parsed = _raw_mapping_from_output(raw, label=f"admission_telemetry[{index}].receipt")
        if parsed is not None:
            if "B" in parsed and fixed.get("B_or_null") is not None and parsed["B"] != fixed["B_or_null"]:
                _semantic("reject_only", "stress transcript B differs from declared fixed input")
            if "seed" in parsed and fixed.get("seed_or_null") is not None and parsed["seed"] != fixed["seed_or_null"]:
                _semantic("reject_only", "stress transcript seed differs from declared fixed input")


def _validate_receipt_semantics(
    repository_root: str | os.PathLike[str],
    receipt: ReceiptDocument,
    *,
    schema: ReceiptSchema,
    binding: _PreregBinding,
) -> None:
    root_identity = _capture_root_identity(repository_root)
    token = _VALIDATION_ROOT_IDENTITY.set(root_identity)
    try:
        _validate_receipt_semantics_inner(
            repository_root,
            receipt,
            schema=schema,
            binding=binding,
        )
    finally:
        _VALIDATION_ROOT_IDENTITY.reset(token)


def _validate_receipt_semantics_inner(
    repository_root: str | os.PathLike[str],
    receipt: ReceiptDocument,
    *,
    schema: ReceiptSchema,
    binding: _PreregBinding,
) -> None:
    """shape 合格後も raw 再計算だけで受領証の受理条件を評価する。"""

    value = _receipt_value(receipt)
    if type(schema) is not ReceiptSchema:
        _semantic("schema", "schema must be a ReceiptSchema")
    try:
        validate_receipt_shape(value, schema=schema)
    except ReceiptSchemaError as exc:
        _semantic("shape", "receipt did not pass the Draft-07 shape gate", exc)

    record = _validate_preregistration(
        repository_root,
        value.get("preregistration"),
        binding=binding,
    )
    _validate_schema_pin(record, binding)
    if schema.ref != record.receipt_schema or schema.sha256 != record.receipt_schema.sha256:
        _semantic("schema_pin", "loaded ReceiptSchema is not the binding-pinned schema blob")
    _validate_blob_refs(repository_root, record)

    study_stage = value.get("study_stage")
    if study_stage not in {"pilot", "main_run"}:
        _semantic("semantic", "study_stage is not an accepted stage")
    planned = _mapping(value.get("planned_execution"), "planned_execution")
    schedule_rows = _validate_schedule(
        repository_root,
        planned,
        study_stage=study_stage,
    )
    consumed = tuple(planned["consumed_cluster_slots"])
    planned_by_id = _validate_planned_runs(planned, schedule_rows, consumed)
    _validate_reference_graph(value, planned_by_id)
    _validate_cardinality_and_ordinals(value)
    _validate_source_identity(
        repository_root,
        value,
        measurement_head=binding.measurement_head,
    )
    _validate_allocation_shape_semantics(value)
    _validate_slots_and_counts(value)
    _validate_all_pointers(repository_root, value)
    _validate_create_only_references(repository_root, value)
    _validate_reject_only(repository_root, value)

    _validate_performance_compile_legs(repository_root, value)
    _validate_correctness_builds(repository_root, value, _mapping(value.get("arms"), "arms"))
    _validate_wait_and_run_logs(repository_root, value, planned_by_id)
    observation_results = _validate_observations(repository_root, value)
    anomaly = _validate_correctness_raw_evidence(repository_root, value)
    _validate_planned_actual_relationship(value, planned_by_id)
    _validate_reason_branches(value, observation_results, anomaly=anomaly)
    _validate_phase_budget(value)


def _validate_study_receipts(
    repository_root: str | os.PathLike[str],
    receipts: Sequence[ReceiptDocument],
    *,
    schema: ReceiptSchema,
    binding: _PreregBinding,
) -> None:
    if isinstance(receipts, (str, bytes, bytearray)) or not isinstance(receipts, Sequence):
        _semantic("study", "receipts must be a sequence")
    root_identity = _capture_root_identity(repository_root)
    token = _VALIDATION_ROOT_IDENTITY.set(root_identity)
    try:
        _validate_study_receipts_inner(
            repository_root,
            receipts,
            schema=schema,
            binding=binding,
        )
    finally:
        _VALIDATION_ROOT_IDENTITY.reset(token)


def _validate_study_receipts_inner(
    repository_root: str | os.PathLike[str],
    receipts: Sequence[ReceiptDocument],
    *,
    schema: ReceiptSchema,
    binding: _PreregBinding,
) -> None:
    """同一 study の pilot/main receipt と verification allocation を照合する。"""

    if len(receipts) != 2:
        _semantic(
            "study",
            "a study must be covered by exactly one pilot and one main_run receipt",
        )
    values: list[Mapping[str, Any]] = []
    for receipt in receipts:
        _validate_receipt_semantics(
            repository_root,
            receipt,
            schema=schema,
            binding=binding,
        )
        values.append(_receipt_value(receipt))
    stages = [value.get("study_stage") for value in values]
    if stages != ["pilot", "main_run"]:
        _semantic(
            "study",
            "study receipts must appear once each in pilot then main_run order",
        )
    first = values[0]
    study_id = first.get("study_id")
    series_id = first.get("series_id")
    verification_signatures: list[tuple[object, str, str]] = []
    for value in values:
        if value.get("study_id") != study_id or value.get("series_id") != series_id:
            _semantic("study", "stage receipts do not belong to one study series")
        verification = [
            item
            for item in value.get("allocations", ())
            if isinstance(item, Mapping) and item.get("allocation_role") == "verification"
        ]
        if len(verification) != 1:
            _semantic("study", "each stage must carry exactly one verification allocation")
        allocation = verification[0]
        accounting_raw = _read_file_record(
            repository_root,
            _mapping(allocation.get("accounting_trace"), "verification.accounting_trace"),
            label="verification.accounting_trace",
        )
        exclusivity = _mapping(allocation.get("exclusivity"), "verification.exclusivity")
        exclusivity_raw = _read_file_record(
            repository_root,
            _mapping(exclusivity.get("raw"), "verification.exclusivity.raw"),
            label="verification.exclusivity.raw",
        )
        verification_signatures.append(
            (
                allocation.get("allocation_id"),
                hashlib.sha256(accounting_raw).hexdigest(),
                hashlib.sha256(exclusivity_raw).hexdigest(),
            )
        )
    if any(signature != verification_signatures[0] for signature in verification_signatures[1:]):
        _semantic("study", "verification allocation identity/evidence changed between stages")


# Private consumer-friendly aliases.  The package __init__ intentionally does
# not export any of these until unit 6 wires the public API.
_derive_schedule_bytes = _canonical_schedule_bytes
_validate_planned_actual = _validate_planned_actual_relationship
_validate_correctness_build = _validate_correctness_builds
_validate_wait_and_run = _validate_wait_and_run_logs
_validate_cardinality = _validate_cardinality_and_ordinals
_validate_local_intent_refs = _validate_create_only_references
_validate_receipt = _validate_receipt_semantics
_validate_study = _validate_study_receipts


__all__ = (
    "A03Result",
    "SemanticValidationError",
    "_canonical_schedule_bytes",
    "_derive_a03_failure",
    "_derive_schedule_rows",
    "_parse_ccbench_flags",
    "_parse_ccbench_run_log",
    "_parse_preregistration_8key",
    "_read_file_record",
    "_validate_receipt_semantics",
    "_validate_study_receipts",
)
