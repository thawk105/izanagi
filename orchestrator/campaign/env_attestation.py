# -*- coding: utf-8 -*-
"""実行環境の strict attestation と calibration admission。

runtime probe と calibrator は ``calibrator.schema_v2`` の凍結 dataclass を共有する。
必須観測の欠落・曖昧さは fatal とし、best-effort や設定値 fallback は持たない。
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Optional, Protocol, Sequence

if __package__ == "orchestrator.campaign":
    from ..calibrator import schema_v2 as _schema_v2
    from ..calibrator import effective_clock_policy
    from ..calibrator import tsc as _tsc
else:  # top-level ``campaign`` compatibility
    from calibrator import schema_v2 as _schema_v2
    from calibrator import effective_clock_policy
    from calibrator import tsc as _tsc
from . import calibration_verify as _calibration_verify
from . import env_contract as _env_contract


GRANDFATHERED_V1_SHA256 = _calibration_verify.GRANDFATHERED_V1_SHA256
PROBE_METHOD = "strict-sysfs-procfs"
PROBE_VERSION = "1"
PEGASUS_PROBE_OUTPUT_V1 = "pegasus-probe-output/v1"
PEGASUS_PROBE_OUTPUT_V2 = "pegasus-probe-output/v2"
LEGACY_SCHEMA_VERSION = _calibration_verify.LEGACY_SCHEMA_VERSION
EFFECTIVE_CLOCK_ALPHA_K = 5
EFFECTIVE_CLOCK_ALPHA_INTERVAL_NS = 50_000_000
EFFECTIVE_CLOCK_ALPHA_RULE_ID = "sysfs-affinity-intersection-evenly-spaced-v1"
EFFECTIVE_CLOCK_METHOD = (
    f"proc-cpuinfo-rotating-min/k{EFFECTIVE_CLOCK_ALPHA_K}"
    f"/interval-ns{EFFECTIVE_CLOCK_ALPHA_INTERVAL_NS}"
    f"/{EFFECTIVE_CLOCK_ALPHA_RULE_ID}"
)

_CPU_DIR_RE = re.compile(r"cpu([0-9]+)")
_INDEX_DIR_RE = re.compile(r"index([0-9]+)")
_NODE_DIR_RE = re.compile(r"node([0-9]+)")
_SIZE_RE = re.compile(r"([0-9]+)([KMGT]?)", re.IGNORECASE)
_FREQUENCY_SUFFIX_RE = re.compile(
    r"(?:\s*@?\s*[0-9]+(?:\.[0-9]+)?\s*[KMGT]?Hz)\s*$", re.IGNORECASE,
)


AttestationError = _calibration_verify.AttestationError


class HardwareProbe(Protocol):
    def __call__(self) -> _schema_v2.ObservedAttestationProfile: ...


class CpuinfoSamplingRuntime(Protocol):
    """方式 alpha が使う OS/read 境界。集約済み値は注入しない。"""

    def get_affinity(self) -> set[int]: ...

    def set_affinity(self, cpus: set[int]) -> None: ...

    def current_processor(self, proc_root: Path) -> int: ...

    def read_cpuinfo(
        self, path: Path,
    ) -> tuple[dict[str, object], dict[int, float]]: ...

    def monotonic_ns(self) -> int: ...

    def sleep(self, seconds: float) -> None: ...


@dataclass(frozen=True)
class ProbeRoots:
    """:func:`probe` が読む filesystem root。fixture tree 用に注入可能。"""

    proc: Path = Path("/proc")
    sys_cpu: Path = Path("/sys/devices/system/cpu")
    sys_node: Path = Path("/sys/devices/system/node")

    def __post_init__(self) -> None:
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, Path) or not value.is_absolute():
                raise AttestationError(f"ProbeRoots.{field.name} は absolute Path でなければならない")


DEFAULT_PROBE_ROOTS = ProbeRoots()


@dataclass(frozen=True)
class ParsedProbeOutput:
    """Strict probe document with its hash-projection schema bound by parsing."""

    schema_version: str
    ok: bool
    observed_epoch: int
    profile: Optional[_schema_v2.ObservedAttestationProfile]
    error: Optional[dict[str, str]]


VerifiedCalibration = _calibration_verify.VerifiedCalibration
profile_sha256 = _calibration_verify.profile_sha256


def normalize_cpu_model_name(value: str) -> str:
    """等値比較に使う canonical CPU model name を返す。

    正規化は意図的に狭く順序固定である。``(R)`` / ``(TM)`` を除去し、末尾の周波数表記を
    1 個だけ除去してから、空白列を ASCII space 1 個へ畳む。他の marketing name 書換えはしない。
    """
    if type(value) is not str or not value.strip():
        raise AttestationError("CPU model name がない")
    normalized = value.replace("(R)", "").replace("(TM)", "")
    normalized = _FREQUENCY_SUFFIX_RE.sub("", normalized)
    normalized = " ".join(normalized.split())
    if not normalized:
        raise AttestationError("CPU model name が正規化後に空になった")
    return normalized


def _read_text(path: Path, *, field: str) -> str:
    try:
        value = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AttestationError(f"必須 {field} を読めない: {path}: {exc}") from exc
    value = value.strip()
    if not value:
        raise AttestationError(f"必須 {field} が空: {path}")
    return value


def _parse_int(value: str, *, field: str) -> int:
    try:
        result = int(value, 10)
    except ValueError as exc:
        raise AttestationError(f"{field} が 10 進整数でない: {value!r}") from exc
    if result < 0:
        raise AttestationError(f"{field} が負: {result}")
    return result


def _parse_float(value: str, *, field: str) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise AttestationError(f"{field} が数値でない: {value!r}") from exc
    if not math.isfinite(result) or result <= 0.0:
        raise AttestationError(f"{field} が正の有限値でない: {value!r}")
    return result


def _parse_cpu_list(value: str, *, field: str) -> list[int]:
    cpus: set[int] = set()
    for token in value.split(","):
        token = token.strip()
        if not token:
            raise AttestationError(f"{field} に空の CPU-list 要素がある")
        if "-" in token:
            parts = token.split("-")
            if len(parts) != 2:
                raise AttestationError(f"{field} の range が不正: {token!r}")
            first = _parse_int(parts[0], field=field)
            last = _parse_int(parts[1], field=field)
            if last < first:
                raise AttestationError(f"{field} の range が降順: {token!r}")
            cpus.update(range(first, last + 1))
        else:
            cpus.add(_parse_int(token, field=field))
    if not cpus:
        raise AttestationError(f"{field} が空")
    return sorted(cpus)


def _parse_cache_bytes(value: str, *, field: str) -> int:
    match = _SIZE_RE.fullmatch(value.strip())
    if match is None:
        raise AttestationError(f"{field} の size 表記が未対応: {value!r}")
    multiplier = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3,
                  "T": 1024**4}[match.group(2).upper()]
    result = int(match.group(1)) * multiplier
    if result <= 0:
        raise AttestationError(f"{field} が正でない")
    return result


def _cpu_directories(root: Path) -> list[tuple[int, Path]]:
    try:
        children = list(root.iterdir())
    except OSError as exc:
        raise AttestationError(f"CPU sysfs root を列挙できない: {root}: {exc}") from exc
    result = []
    for child in children:
        match = _CPU_DIR_RE.fullmatch(child.name)
        if match is not None and child.is_dir():
            result.append((int(match.group(1)), child))
    result.sort()
    if not result:
        raise AttestationError(f"{root} 配下に cpuN directory がない")
    return result


def _parse_cpuinfo(path: Path) -> tuple[dict[str, object], dict[int, float]]:
    text = _read_text(path, field="/proc/cpuinfo")
    blocks = [block for block in re.split(r"\n\s*\n", text) if block.strip()]
    if not blocks:
        raise AttestationError("/proc/cpuinfo に processor block がない")
    required = ("processor", "vendor_id", "cpu family", "model", "model name", "cpu MHz")
    identities = []
    raw_names = []
    mhz_by_cpu: dict[int, float] = {}
    for index, block in enumerate(blocks):
        fields: dict[str, str] = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key, value = key.strip(), value.strip()
            if key in fields:
                raise AttestationError(f"cpuinfo block {index} duplicates {key!r}")
            fields[key] = value
        missing = [key for key in required if not fields.get(key)]
        if missing:
            raise AttestationError(f"cpuinfo block {index} lacks required fields: {missing}")
        cpu_id = _parse_int(fields["processor"], field="cpuinfo.processor")
        if cpu_id in mhz_by_cpu:
            raise AttestationError(f"cpuinfo duplicates processor {cpu_id}")
        identity = (
            fields["vendor_id"],
            _parse_int(fields["cpu family"], field="cpuinfo.cpu family"),
            _parse_int(fields["model"], field="cpuinfo.model"),
            normalize_cpu_model_name(fields["model name"]),
        )
        identities.append(identity)
        raw_names.append(fields["model name"])
        mhz_by_cpu[cpu_id] = _parse_float(fields["cpu MHz"], field="cpuinfo.cpu MHz")
    if any(identity != identities[0] for identity in identities[1:]):
        raise AttestationError("logical CPU 間で cpuinfo identity field が不一致")
    vendor, family, model, normalized_name = identities[0]
    return {
        "vendor": vendor,
        "family": family,
        "model": model,
        "model_name_raw": raw_names[0],
        "model_name_normalized": normalized_name,
    }, mhz_by_cpu


def _current_processor(proc_root: Path) -> int:
    """呼出し thread の ``/proc`` stat から processor field を返す。"""
    stat = _read_text(proc_root / "thread-self/stat", field="/proc/thread-self/stat")
    comm_end = stat.rfind(")")
    if comm_end < 1:
        raise AttestationError("/proc/thread-self/stat の comm field が不正")
    fields_after_comm = stat[comm_end + 1:].split()
    processor_offset = 39 - 3
    if len(fields_after_comm) <= processor_offset:
        raise AttestationError("/proc/thread-self/stat に processor field がない")
    return _parse_int(
        fields_after_comm[processor_offset], field="/proc/thread-self/stat.processor",
    )


@dataclass(frozen=True)
class _LinuxCpuinfoSamplingRuntime:
    def get_affinity(self) -> set[int]:
        return set(os.sched_getaffinity(0))

    def set_affinity(self, cpus: set[int]) -> None:
        os.sched_setaffinity(0, cpus)

    def current_processor(self, proc_root: Path) -> int:
        return _current_processor(proc_root)

    def read_cpuinfo(
        self, path: Path,
    ) -> tuple[dict[str, object], dict[int, float]]:
        return _parse_cpuinfo(path)

    def monotonic_ns(self) -> int:
        return time.monotonic_ns()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


DEFAULT_CPUINFO_RUNTIME: CpuinfoSamplingRuntime = _LinuxCpuinfoSamplingRuntime()


def _select_evenly_spaced_cpu_ids(
    cpus: set[int], count: int, rule_id: str,
) -> list[int]:
    if rule_id != EFFECTIVE_CLOCK_ALPHA_RULE_ID:
        raise AttestationError(f"未知の effective-clock target 選択規則: {rule_id!r}")
    if type(count) is not int or count < 2:
        raise AttestationError("effective-clock target 数は 2 以上の整数でなければならない")
    if any(type(cpu) is not int or cpu < 0 for cpu in cpus):
        raise AttestationError("effective-clock target 候補に不正な CPU ID がある")
    ordered = sorted(cpus)
    if len(ordered) < count:
        raise AttestationError(
            f"方式 alpha に必要な affinity CPU が不足: required={count} "
            f"observed={len(ordered)}"
        )
    targets = [
        ordered[round(index * (len(ordered) - 1) / (count - 1))]
        for index in range(count)
    ]
    if len(set(targets)) != count:
        raise AttestationError("effective-clock target 選択が distinct CPU を返さなかった")
    return targets


def _reduce_cpuinfo_reads(
    reads: Sequence[tuple[Mapping[str, object], Mapping[int, float]]],
    expected_cpu_ids: set[int],
) -> tuple[dict[str, object], dict[int, float]]:
    """K snapshot を CPU ごとの最小 MHz へ集約し、集合・identity drift を拒否する。"""
    if len(reads) != EFFECTIVE_CLOCK_ALPHA_K:
        raise AttestationError(
            f"方式 alpha の cpuinfo read 数が不正: required={EFFECTIVE_CLOCK_ALPHA_K} "
            f"observed={len(reads)}"
        )
    if not expected_cpu_ids:
        raise AttestationError("方式 alpha の expected CPU 集合が空")
    first_identity = dict(reads[0][0])
    minima = {cpu_id: math.inf for cpu_id in expected_cpu_ids}
    for read_index, (identity, mhz_by_cpu) in enumerate(reads):
        observed_cpu_ids = set(mhz_by_cpu)
        if observed_cpu_ids != expected_cpu_ids:
            raise AttestationError(
                f"cpuinfo processor 集合が read {read_index} で drift: "
                f"expected={sorted(expected_cpu_ids)} observed={sorted(observed_cpu_ids)}"
            )
        if dict(identity) != first_identity:
            raise AttestationError(f"cpuinfo identity が read {read_index} で drift")
        for cpu_id in expected_cpu_ids:
            value = mhz_by_cpu[cpu_id]
            if type(value) not in {int, float} or not math.isfinite(value) or value <= 0.0:
                raise AttestationError(
                    f"cpuinfo read {read_index} の cpu{cpu_id} MHz が正の有限値でない"
                )
            minima[cpu_id] = min(minima[cpu_id], float(value))
    return first_identity, minima


def _runtime_monotonic_ns(runtime: CpuinfoSamplingRuntime) -> int:
    try:
        value = runtime.monotonic_ns()
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        raise AttestationError(f"monotonic clock を取得できない: {exc}") from exc
    if type(value) is not int or value < 0:
        raise AttestationError("monotonic clock が非負整数 nanoseconds でない")
    return value


def _wait_until_ns(runtime: CpuinfoSamplingRuntime, deadline_ns: int) -> None:
    while True:
        now_ns = _runtime_monotonic_ns(runtime)
        if now_ns >= deadline_ns:
            return
        try:
            runtime.sleep((deadline_ns - now_ns) / 1_000_000_000)
        except (AttributeError, OSError, TypeError, ValueError) as exc:
            raise AttestationError(f"effective-clock interval 待機に失敗: {exc}") from exc


def _collect_rotating_cpuinfo(
    path: Path,
    proc_root: Path,
    expected_cpu_ids: set[int],
    runtime: CpuinfoSamplingRuntime,
) -> tuple[dict[str, object], dict[int, float], int]:
    """affinity 巡回、K read、元 affinity の exact 復元を一つの境界に閉じる。"""
    try:
        original_affinity = frozenset(runtime.get_affinity())
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        raise AttestationError(f"sched_getaffinity を利用できない: {exc}") from exc
    if not original_affinity:
        raise AttestationError("sched_getaffinity が空の CPU 集合を返した")
    if any(type(cpu) is not int or cpu < 0 for cpu in original_affinity):
        raise AttestationError("sched_getaffinity が不正な CPU ID を返した")
    targets = _select_evenly_spaced_cpu_ids(
        expected_cpu_ids & set(original_affinity),
        EFFECTIVE_CLOCK_ALPHA_K,
        EFFECTIVE_CLOCK_ALPHA_RULE_ID,
    )
    reads: list[tuple[dict[str, object], dict[int, float]]] = []
    previous_read_started_ns: Optional[int] = None
    primary_error: Optional[Exception] = None
    restore_errors: list[str] = []
    try:
        for read_index, target in enumerate(targets):
            try:
                runtime.set_affinity({target})
            except (AttributeError, OSError, TypeError, ValueError) as exc:
                raise AttestationError(
                    f"effective-clock read {read_index} の cpu{target} pin に失敗: {exc}"
                ) from exc

            deadline_ns = None
            if previous_read_started_ns is not None:
                deadline_ns = previous_read_started_ns + EFFECTIVE_CLOCK_ALPHA_INTERVAL_NS
                _wait_until_ns(runtime, deadline_ns)

            try:
                pinned_affinity = set(runtime.get_affinity())
            except (AttributeError, OSError, TypeError, ValueError) as exc:
                raise AttestationError(
                    f"effective-clock read {read_index} の affinity 再取得に失敗: {exc}"
                ) from exc
            if pinned_affinity != {target}:
                raise AttestationError(
                    f"effective-clock read {read_index} の pin mask が不一致: "
                    f"target={target} observed={sorted(pinned_affinity)}"
                )

            try:
                pre_processor = runtime.current_processor(proc_root)
            except (AttributeError, OSError, TypeError, ValueError) as exc:
                raise AttestationError(
                    f"effective-clock read {read_index} の pre processor を取得できない: {exc}"
                ) from exc
            if pre_processor != target:
                raise AttestationError(
                    f"effective-clock read {read_index} の pre processor が不一致: "
                    f"target={target} observed={pre_processor}"
                )

            read_started_ns = _runtime_monotonic_ns(runtime)
            if deadline_ns is not None and read_started_ns < deadline_ns:
                raise AttestationError(
                    f"effective-clock read {read_index} が interval deadline より前に開始した"
                )
            previous_read_started_ns = read_started_ns
            try:
                identity, mhz_by_cpu = runtime.read_cpuinfo(path)
            except (AttestationError, OSError, TypeError, ValueError) as exc:
                raise AttestationError(
                    f"effective-clock read {read_index} の cpuinfo 取得に失敗: {exc}"
                ) from exc

            try:
                post_processor = runtime.current_processor(proc_root)
            except (AttributeError, OSError, TypeError, ValueError) as exc:
                raise AttestationError(
                    f"effective-clock read {read_index} の post processor を取得できない: {exc}"
                ) from exc
            if post_processor != target:
                raise AttestationError(
                    f"effective-clock read {read_index} の post processor が不一致: "
                    f"target={target} observed={post_processor}"
                )
            reads.append((identity, mhz_by_cpu))
    except Exception as exc:
        primary_error = exc
    finally:
        try:
            runtime.set_affinity(set(original_affinity))
        except Exception as exc:
            restore_errors.append(f"元 affinity の復元設定に失敗: {exc}")
        try:
            restored_affinity = set(runtime.get_affinity())
        except Exception as exc:
            restore_errors.append(f"元 affinity の復元後再取得に失敗: {exc}")
        else:
            try:
                if restored_affinity != set(original_affinity):
                    restore_errors.append(
                        f"元 affinity の復元が不一致: expected={sorted(original_affinity)} "
                        f"observed={sorted(restored_affinity)}"
                    )
            except Exception as exc:
                restore_errors.append(f"元 affinity の復元検証に失敗: {exc}")
    if primary_error is not None:
        if restore_errors:
            raise AttestationError(
                f"{primary_error}; 復元時の追加失敗: {'; '.join(restore_errors)}"
            ) from primary_error
        raise primary_error
    if restore_errors:
        raise AttestationError("; ".join(restore_errors))
    identity, minima = _reduce_cpuinfo_reads(reads, expected_cpu_ids)
    return identity, minima, len(original_affinity)


def _cache_topology(cpus: list[tuple[int, Path]]) -> list[_schema_v2.CacheTopologyEntry]:
    unique: dict[tuple, _schema_v2.CacheTopologyEntry] = {}
    expected_indexes: Optional[list[int]] = None
    logical_cpu_ids = {cpu_id for cpu_id, _ in cpus}
    for cpu_id, cpu_path in cpus:
        cache_root = cpu_path / "cache"
        try:
            children = list(cache_root.iterdir())
        except OSError as exc:
            raise AttestationError(f"cpu{cpu_id} の cache topology を列挙できない: {exc}") from exc
        indexed = []
        for child in children:
            match = _INDEX_DIR_RE.fullmatch(child.name)
            if match is not None and child.is_dir():
                indexed.append((int(match.group(1)), child))
        indexed.sort()
        if not indexed or [number for number, _ in indexed] != list(range(indexed[-1][0] + 1)):
            raise AttestationError(f"cpu{cpu_id} cache index directories are missing or non-contiguous")
        index_numbers = [number for number, _ in indexed]
        if expected_indexes is None:
            expected_indexes = index_numbers
        elif index_numbers != expected_indexes:
            raise AttestationError(
                f"cpu{cpu_id} cache index 集合が不一致: expected={expected_indexes} "
                f"observed={index_numbers}"
            )
        seen_this_cpu = set()
        for number, path in indexed:
            prefix = f"cpu{cpu_id}.cache.index{number}"
            entry = _schema_v2.CacheTopologyEntry(
                level=_parse_int(_read_text(path / "level", field=f"{prefix}.level"),
                                 field=f"{prefix}.level"),
                type=_read_text(path / "type", field=f"{prefix}.type"),
                bytes=_parse_cache_bytes(
                    _read_text(path / "size", field=f"{prefix}.size"), field=f"{prefix}.size",
                ),
                line=_parse_int(
                    _read_text(path / "coherency_line_size", field=f"{prefix}.line"),
                    field=f"{prefix}.line",
                ),
                shared_cpus=_parse_cpu_list(
                    _read_text(path / "shared_cpu_list", field=f"{prefix}.shared_cpu_list"),
                    field=f"{prefix}.shared_cpu_list",
                ),
            )
            if cpu_id not in entry.shared_cpus or not set(entry.shared_cpus) <= logical_cpu_ids:
                raise AttestationError(
                    f"{prefix}.shared_cpu_list が列挙済み CPU を表していない"
                )
            if entry.canonical_key() in seen_this_cpu:
                raise AttestationError(f"cpu{cpu_id} has duplicate canonical cache indexes")
            seen_this_cpu.add(entry.canonical_key())
            unique[entry.canonical_key()] = entry
    return [unique[key] for key in sorted(unique)]


def _numa_topology(root: Path, logical_cpus: set[int]) -> list[_schema_v2.NumaNode]:
    try:
        children = list(root.iterdir())
    except OSError as exc:
        raise AttestationError(f"NUMA sysfs root を列挙できない: {root}: {exc}") from exc
    nodes = []
    for child in children:
        match = _NODE_DIR_RE.fullmatch(child.name)
        if match is None or not child.is_dir():
            continue
        node_id = int(match.group(1))
        nodes.append(_schema_v2.NumaNode(
            node_id=node_id,
            cpulist=_parse_cpu_list(
                _read_text(child / "cpulist", field=f"node{node_id}.cpulist"),
                field=f"node{node_id}.cpulist",
            ),
        ))
    nodes.sort(key=lambda item: item.node_id)
    if not nodes:
        raise AttestationError(f"{root} 配下に nodeN directory がない")
    covered = {cpu for node in nodes for cpu in node.cpulist}
    flattened = [cpu for node in nodes for cpu in node.cpulist]
    if covered != logical_cpus or len(flattened) != len(covered):
        raise AttestationError(
            f"NUMA cpulist が logical CPU を完全被覆しない: expected={sorted(logical_cpus)} "
            f"observed={sorted(covered)}"
        )
    return nodes


def _measure_tsc_profile() -> _schema_v2.TscProfile:
    """``calibrator.tsc`` の raw 5 sample API を fallback なしで使う。"""
    try:
        measured = _tsc.measure_tsc(rounds=5)
    except (OSError, subprocess.SubprocessError) as exc:
        raise AttestationError(f"TSC 測定失敗。fallback 禁止: {exc}") from exc
    if measured is None:
        raise AttestationError("TSC 測定不能。fallback 禁止")
    if len(measured.raw_samples_mhz) != 5:
        raise AttestationError("TSC probe が raw sample を正確に 5 個返さなかった")
    try:
        return _schema_v2.TscProfile(
            raw_samples_mhz=list(measured.raw_samples_mhz),
            median_mhz=measured.median_mhz,
            clocks_per_us_int=measured.clocks_per_us_int,
            source=measured.source,
        )
    except _schema_v2.CalibrationSchemaError as exc:
        raise AttestationError(f"TSC measurement is internally inconsistent: {exc}") from exc


def _visibility(proc_root: Path) -> _schema_v2.VisibilityProfile:
    """proc visibility と host PID namespace の運用指標を取得する。

    ``/proc/2/comm == kthreadd`` は Pegasus の非 root 環境で使える指標だが、comm は
    namespace 内 process が詐称し得るため暗号学的な host namespace 証明ではない。
    hidepid、scheduler reservation、単独性検査と組み合わせる既知限界を持つ。
    """
    mounts = _read_text(proc_root / "mounts", field="/proc/mounts")
    candidates = []
    for line in mounts.splitlines():
        parts = line.split()
        if len(parts) < 4:
            raise AttestationError(f"/proc/mounts の行が不正: {line!r}")
        if parts[1] in {"/proc", str(proc_root)} and parts[2] == "proc":
            candidates.append(parts[3].split(","))
    if len(candidates) != 1:
        raise AttestationError("procfs mount option を一意に決定できない")
    hidepid_values = [option.split("=", 1)[1] for option in candidates[0]
                      if option.startswith("hidepid=")]
    if len(set(hidepid_values)) > 1:
        raise AttestationError("conflicting hidepid mount options")
    hidepid = hidepid_values[0] if hidepid_values else "0"
    if hidepid != "0":
        raise AttestationError(f"必須 process visibility が hidepid={hidepid} で隠されている")
    try:
        proc2_comm = (proc_root / "2/comm").read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        shared_with_host = False
    except (OSError, UnicodeError) as exc:
        raise AttestationError(f"PID namespace 指標 /proc/2/comm を読めない: {exc}") from exc
    else:
        shared_with_host = proc2_comm == "kthreadd"
    return _schema_v2.VisibilityProfile(
        hidepid=hidepid,
        pid_ns_shared_with_host=shared_with_host,
        pid_ns_method=_schema_v2.PID_NS_METHOD,
    )


def probe(
    roots: ProbeRoots = DEFAULT_PROBE_ROOTS,
    *,
    cpuinfo_runtime: CpuinfoSamplingRuntime = DEFAULT_CPUINFO_RUNTIME,
) -> _schema_v2.ObservedAttestationProfile:
    """現在 hardware を strict に観測する。部分読取りは probe 全体を拒否する。"""
    if not isinstance(roots, ProbeRoots):
        raise AttestationError("roots は ProbeRoots でなければならない")
    cpus = _cpu_directories(roots.sys_cpu)
    cpu_ids = {cpu_id for cpu_id, _ in cpus}
    cpu_identity, mhz_by_cpu, affinity_visible = _collect_rotating_cpuinfo(
        roots.proc / "cpuinfo", roots.proc, cpu_ids, cpuinfo_runtime,
    )
    core_ids = set()
    governors = set()
    for cpu_id, cpu_path in cpus:
        core_ids.add(_parse_int(
            _read_text(cpu_path / "topology/core_id", field=f"cpu{cpu_id}.core_id"),
            field=f"cpu{cpu_id}.core_id",
        ))
        governors.add(_read_text(
            cpu_path / "cpufreq/scaling_governor", field=f"cpu{cpu_id}.scaling_governor",
        ))
    if len(governors) != 1:
        raise AttestationError(f"CPU 間で scaling governor が異なる: {sorted(governors)}")

    # 方式 alpha の affinity 復元完了後だけ TSC 測定へ進む。
    tsc_profile = _measure_tsc_profile()
    try:
        return _schema_v2.ObservedAttestationProfile(
            cpu=_schema_v2.CpuProfile(**cpu_identity),
            cores=_schema_v2.CoreProfile(
                physical=len(core_ids), logical=len(cpus),
                smt_active=(len(cpus) > len(core_ids)),
                affinity_visible=affinity_visible,
            ),
            cache_topology=_cache_topology(cpus),
            numa=_numa_topology(roots.sys_node, cpu_ids),
            tsc=tsc_profile,
            effective_clock=_schema_v2.ObservedEffectiveClockProfile(
                samples_mhz=[mhz_by_cpu[cpu_id] for cpu_id in sorted(cpu_ids)],
                method=EFFECTIVE_CLOCK_METHOD,
                governor=next(iter(governors)),
            ),
            visibility=_visibility(roots.proc),
        )
    except _schema_v2.CalibrationSchemaError as exc:
        raise AttestationError(f"observed profile が calibration/v2 型に違反: {exc}") from exc


probe_hardware = probe


def normalize_profile(raw: Mapping[str, object]) -> _schema_v2.AttestationProfile:
    """expected-side schema mapping を検証し、CPU name 正規化を適用する。"""
    if not isinstance(raw, Mapping):
        raise AttestationError("raw profile が Mapping でない")

    def exact(value: object, keys: set[str], field: str) -> Mapping[str, object]:
        if not isinstance(value, Mapping) or set(value) != keys:
            raise AttestationError(f"{field} の schema key 集合が exact でない")
        return value

    profile_keys = {"cpu", "cores", "cache_topology", "numa", "tsc",
                    "effective_clock", "visibility"}
    exact(raw, profile_keys, "profile")
    cpu = exact(raw["cpu"], {"vendor", "family", "model", "model_name_raw",
                             "model_name_normalized"}, "profile.cpu")
    normalized_name = normalize_cpu_model_name(cpu["model_name_raw"])  # type: ignore[arg-type]
    if cpu["model_name_normalized"] != normalized_name:
        raise AttestationError("profile.cpu の normalized name が raw name と不一致")
    cores = exact(raw["cores"], {"physical", "logical", "smt_active",
                                 "affinity_visible"}, "profile.cores")
    try:
        caches_raw = raw["cache_topology"]
        numa_raw = raw["numa"]
        if type(caches_raw) is not list or type(numa_raw) is not list:
            raise AttestationError("profile cache_topology/numa は list でなければならない")
        caches = [
            _schema_v2.CacheTopologyEntry(**dict(exact(
                item, {"level", "type", "bytes", "line", "shared_cpus"},
                f"profile.cache_topology[{index}]",
            )))
            for index, item in enumerate(caches_raw)
        ]
        nodes = [
            _schema_v2.NumaNode(**dict(exact(
                item, {"node_id", "cpulist"}, f"profile.numa[{index}]",
            )))
            for index, item in enumerate(numa_raw)
        ]
        tsc = exact(raw["tsc"], {"raw_samples_mhz", "median_mhz",
                                 "clocks_per_us_int", "source"}, "profile.tsc")
        clock = exact(raw["effective_clock"], {"samples_mhz", "method", "governor",
                                               "tolerance_pct"}, "profile.effective_clock")
        visibility = exact(raw["visibility"],
                           {"hidepid", "pid_ns_shared_with_host", "pid_ns_method"},
                           "profile.visibility")
        return _schema_v2.AttestationProfile(
            cpu=_schema_v2.CpuProfile(**dict(cpu)),
            cores=_schema_v2.CoreProfile(**dict(cores)),
            cache_topology=caches,
            numa=nodes,
            tsc=_schema_v2.TscProfile(**dict(tsc)),
            effective_clock=_schema_v2.EffectiveClockProfile(**dict(clock)),
            visibility=_schema_v2.VisibilityProfile(**dict(visibility)),
        )
    except (_schema_v2.CalibrationSchemaError, TypeError) as exc:
        raise AttestationError(f"raw profile が calibration/v2 型に違反: {exc}") from exc


def normalize_observed_profile(
    raw: Mapping[str, object],
) -> _schema_v2.ObservedAttestationProfile:
    """tolerance-free observed mapping を exact shape で検証する。"""
    if not isinstance(raw, Mapping):
        raise AttestationError("raw observed profile が Mapping でない")
    profile_keys = {
        "cpu", "cores", "cache_topology", "numa", "tsc",
        "effective_clock", "visibility",
    }
    if set(raw) != profile_keys:
        raise AttestationError("observed profile の schema key 集合が exact でない")
    clock = raw.get("effective_clock")
    if not isinstance(clock, Mapping) or set(clock) != {
        "samples_mhz", "method", "governor",
    }:
        raise AttestationError("observed profile.effective_clock の schema key 集合が exact でない")

    # Reuse the expected parser for every shared field.  The synthetic value is
    # local validation material only and is never present in the observed type.
    expected_shape = dict(raw)
    expected_shape["effective_clock"] = {**dict(clock), "tolerance_pct": 1.0}
    expected = normalize_profile(expected_shape)
    return _schema_v2.ObservedAttestationProfile(
        cpu=expected.cpu,
        cores=expected.cores,
        cache_topology=expected.cache_topology,
        numa=expected.numa,
        tsc=expected.tsc,
        effective_clock=_schema_v2.ObservedEffectiveClockProfile(**dict(clock)),
        visibility=expected.visibility,
    )


def parse_probe_output(raw: bytes | str) -> ParsedProbeOutput:
    """Parse v1/v2 probe JSON once, rejecting duplicates and shape drift."""
    if not isinstance(raw, (bytes, str)):
        raise AttestationError("probe output は bytes または str でなければならない")
    try:
        document = json.loads(raw, object_pairs_hook=_duplicate_object)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise AttestationError(f"probe output JSON を parse できない: {exc}") from exc
    if type(document) is not dict:
        raise AttestationError("probe output top-level が object でない")
    schema = document.get("schema_version")
    if schema not in {PEGASUS_PROBE_OUTPUT_V1, PEGASUS_PROBE_OUTPUT_V2}:
        raise AttestationError(f"未知の probe output schema: {schema!r}")
    ok = document.get("ok")
    epoch = document.get("observed_epoch")
    if type(ok) is not bool:
        raise AttestationError("probe output ok が bool でない")
    if type(epoch) is not int or epoch < 1:
        raise AttestationError("probe output observed_epoch が正の int でない")
    if ok:
        if set(document) != {"schema_version", "ok", "observed_epoch", "profile"}:
            raise AttestationError("successful probe output の key 集合が exact でない")
        profile_raw = document["profile"]
        if not isinstance(profile_raw, Mapping):
            raise AttestationError("probe output profile が object でない")
        clock = profile_raw.get("effective_clock")
        if not isinstance(clock, Mapping):
            raise AttestationError("probe output effective_clock が object でない")
        if schema == PEGASUS_PROBE_OUTPUT_V1:
            if set(clock) != {"samples_mhz", "method", "governor", "tolerance_pct"}:
                raise AttestationError("v1 effective_clock の key 集合が exact でない")
            tolerance = clock.get("tolerance_pct")
            if type(tolerance) is not float or tolerance != 100.0:
                raise AttestationError("v1 tolerance sentinel は float 100.0 でなければならない")
            projected_raw = dict(profile_raw)
            projected_raw["effective_clock"] = {
                key: value for key, value in clock.items() if key != "tolerance_pct"
            }
            profile = normalize_observed_profile(projected_raw)
        else:
            profile = normalize_observed_profile(profile_raw)
        return ParsedProbeOutput(schema, True, epoch, profile, None)

    if set(document) != {"schema_version", "ok", "observed_epoch", "error"}:
        raise AttestationError("failed probe output の key 集合が exact でない")
    error = document["error"]
    if not isinstance(error, Mapping) or set(error) != {"stage", "type", "message"}:
        raise AttestationError("probe output error の key 集合が exact でない")
    normalized_error: dict[str, str] = {}
    for key in ("stage", "type", "message"):
        value = error[key]
        if type(value) is not str or not value:
            raise AttestationError(f"probe output error.{key} が非空文字列でない")
        normalized_error[key] = value
    return ParsedProbeOutput(schema, False, epoch, None, normalized_error)


def profile_to_dict(profile: _schema_v2.AttestationProfile) -> dict:
    if not isinstance(profile, _schema_v2.AttestationProfile):
        raise AttestationError("profile が AttestationProfile でない")
    return dataclasses.asdict(profile)


def observed_profile_to_dict(profile: _schema_v2.ObservedAttestationProfile) -> dict:
    if not isinstance(profile, _schema_v2.ObservedAttestationProfile):
        raise AttestationError("profile が ObservedAttestationProfile でない")
    return dataclasses.asdict(profile)


def observed_profile_projection(parsed: ParsedProbeOutput) -> dict:
    """Return the source-schema-specific hash preimage for a parsed success."""
    if not isinstance(parsed, ParsedProbeOutput) or not parsed.ok or parsed.profile is None:
        raise AttestationError("successful ParsedProbeOutput が必要")
    projection = observed_profile_to_dict(parsed.profile)
    if parsed.schema_version == PEGASUS_PROBE_OUTPUT_V1:
        projection["effective_clock"]["tolerance_pct"] = 100.0
    elif parsed.schema_version != PEGASUS_PROBE_OUTPUT_V2:
        raise AttestationError(f"未知の projection schema: {parsed.schema_version!r}")
    return projection


def observed_profile_sha256(parsed: ParsedProbeOutput) -> str:
    raw = json.dumps(
        observed_profile_projection(parsed),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _clock_value(profile: _schema_v2.AttestationProfile) -> dict:
    return {
        "samples_mhz": list(profile.effective_clock.samples_mhz),
        "tolerance_pct": profile.effective_clock.tolerance_pct,
    }


def _common_comparison_values(
    profile: _schema_v2.AttestationProfile | _schema_v2.ObservedAttestationProfile,
    *, effective_clock_samples: dict,
) -> dict:
    values = {
        "cpu.vendor": profile.cpu.vendor,
        "cpu.family": profile.cpu.family,
        "cpu.model": profile.cpu.model,
        "cpu.model_name_raw": profile.cpu.model_name_raw,
        "cpu.model_name_normalized": profile.cpu.model_name_normalized,
        "cores.physical": profile.cores.physical,
        "cores.logical": profile.cores.logical,
        "cores.smt_active": profile.cores.smt_active,
        "cores.affinity_visible": profile.cores.affinity_visible,
        "cache_topology": [dataclasses.asdict(item) for item in profile.cache_topology],
        "numa": [dataclasses.asdict(item) for item in profile.numa],
        "tsc.raw_samples_mhz": list(profile.tsc.raw_samples_mhz),
        "tsc.median_mhz": profile.tsc.median_mhz,
        "tsc.clocks_per_us_int": profile.tsc.clocks_per_us_int,
        "tsc.source": profile.tsc.source,
        "effective_clock.samples_mhz": effective_clock_samples,
        "effective_clock.method": profile.effective_clock.method,
        "effective_clock.governor": profile.effective_clock.governor,
        "visibility.hidepid": profile.visibility.hidepid,
        "visibility.pid_ns_shared_with_host": profile.visibility.pid_ns_shared_with_host,
        "visibility.pid_ns_method": profile.visibility.pid_ns_method,
    }
    return values


def expected_comparison_values(profile: _schema_v2.AttestationProfile) -> dict:
    """receipt/v2 が使う canonical expected-side 値を返す。"""
    if not isinstance(profile, _schema_v2.AttestationProfile):
        raise AttestationError("profile が AttestationProfile でない")
    return _common_comparison_values(
        profile, effective_clock_samples=_clock_value(profile),
    )


def observed_comparison_values(profile: _schema_v2.ObservedAttestationProfile) -> dict:
    """receipt/v2 が使う canonical observed-side 値を返す。"""
    if not isinstance(profile, _schema_v2.ObservedAttestationProfile):
        raise AttestationError("profile が ObservedAttestationProfile でない")
    return _common_comparison_values(
        profile,
        effective_clock_samples={
            "samples_mhz": list(profile.effective_clock.samples_mhz),
        },
    )


def _recorded_verdict(field: str, expected: object, observed: object) -> str:
    try:
        if field == "cpu.model_name_raw":
            passed = normalize_cpu_model_name(expected) == normalize_cpu_model_name(observed)  # type: ignore[arg-type]
        elif field in {"tsc.raw_samples_mhz", "tsc.median_mhz"}:
            if field == "tsc.raw_samples_mhz":
                expected_median = statistics.median(expected)  # type: ignore[arg-type]
                observed_median = statistics.median(observed)  # type: ignore[arg-type]
            else:
                expected_median = float(expected)  # type: ignore[arg-type]
                observed_median = float(observed)  # type: ignore[arg-type]
            passed = round(expected_median) == round(observed_median)
        elif field == "effective_clock.samples_mhz":
            expected_map = expected if isinstance(expected, Mapping) else {}
            observed_map = observed if isinstance(observed, Mapping) else {}
            expected_samples = expected_map.get("samples_mhz")
            observed_samples = observed_map.get("samples_mhz")
            tolerance = expected_map.get("tolerance_pct")
            if (set(expected_map) != {"samples_mhz", "tolerance_pct"}
                    or set(observed_map) != {"samples_mhz"}
                    or type(expected_samples) is not list
                    or type(observed_samples) is not list
                    or not expected_samples or not observed_samples
                    or type(tolerance) not in (int, float)
                    or tolerance
                    != effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT):
                passed = False
            else:
                expected_median = float(statistics.median(expected_samples))
                allowed_delta = (
                    abs(expected_median)
                    * effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT
                    / 100.0
                )
                lower = expected_median - allowed_delta
                upper = expected_median + allowed_delta
                passed = all(
                    lower <= float(sample) <= upper
                    for sample in observed_samples
                )
        else:
            passed = expected == observed
    except (TypeError, ValueError, statistics.StatisticsError, AttestationError):
        passed = False
    return "pass" if passed else "fail"


def compare_profiles(
    expected: _schema_v2.AttestationProfile,
    observed: _schema_v2.ObservedAttestationProfile,
    *,
    now_fn: Callable[[], object],
) -> list[dict]:
    """field ごとの決定的 verdict を返す。不一致自体では例外にしない。

    ``hostname`` is not present in either hardware profile and is intentionally
    excluded.  Every observed effective-clock sample must lie within the band
    around the expected median frozen by the calibration tolerance.
    """
    if not isinstance(expected, _schema_v2.AttestationProfile):
        raise AttestationError("expected が AttestationProfile でない")
    if not isinstance(observed, _schema_v2.ObservedAttestationProfile):
        raise AttestationError("observed が ObservedAttestationProfile でない")
    if not callable(now_fn):
        raise AttestationError("now_fn は callable でなければならない")
    now_fn()  # acquisition-time seam; receipt/v2 has no timestamp field in W0.
    expected_values = expected_comparison_values(expected)
    observed_values = observed_comparison_values(observed)
    return [
        {
            "field": field,
            "expected": expected_values[field],
            "observed": observed_values[field],
            "verdict": _recorded_verdict(
                field, expected_values[field], observed_values[field],
            ),
        }
        for field in expected_values
    ]


def _duplicate_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise AttestationError(f"calibration JSON has duplicate key: {key!r}")
        result[key] = value
    return result


def load_verified_calibration(
    contract: _env_contract.ExecutionEnvironmentContract, repo_root: Path,
) -> VerifiedCalibration:
    """契約型を確認し、素の値を calibration admission leaf へ委譲する。"""
    if not isinstance(contract, _env_contract.ExecutionEnvironmentContract):
        raise AttestationError("contract の型が不正")
    return _calibration_verify.load_verified_calibration(
        env_tag=contract.env_tag,
        clocks_per_us=contract.clocks_per_us,
        attestation_mode=contract.attestation_mode,
        calibration_path=contract.calibration_ref.path,
        calibration_sha256=contract.calibration_ref.sha256,
        repo_root=repo_root,
    )
