# -*- coding: utf-8 -*-
"""calibration/v2 の共有データ契約と strict validator。

calibrator (writer) と campaign (reader) が同じ exact schema を使うための stdlib-only
leaf。hostname は取得 provenance であり、ハード仕様の equality 検査対象にはしない。
JSON text を渡した場合は ``object_pairs_hook`` で全階層の duplicate key を parse 時に
拒否する。既に parse 済みの dict からは重複という情報が失われているため、file 境界の
reader は raw text/bytes をこの validator へ渡さなければならない。
"""
from __future__ import annotations

import json
import math
import re
import statistics
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Union


SCHEMA_VERSION = "calibration/v2"
PID_NS_METHOD = "proc2-kthreadd"

_HEX40_RE = re.compile(r"[0-9a-f]{40}")
_HEX64_RE = re.compile(r"[0-9a-f]{64}")
_SLUG_RE = re.compile(r"[a-z0-9][a-z0-9._-]*")
_KNOWN_VALUES_SOURCE = "pegasus-runbook §1"


class CalibrationSchemaError(ValueError):
    """calibration/v2 の型・構造・値が exact schema に一致しない。"""


def _fail(message: str) -> None:
    raise CalibrationSchemaError(message)


def _object(value: object, *, field: str) -> dict:
    if type(value) is not dict:
        _fail(f"{field} は object でなければならない")
    return value


def _exact(value: object, keys: set[str], *, field: str) -> dict:
    obj = _object(value, field=field)
    actual = set(obj)
    if actual != keys:
        _fail(
            f"{field} の key 集合が不一致 "
            f"(欠落={sorted(keys - actual)} 未知={sorted(actual - keys, key=repr)})"
        )
    return obj


def _text(value: object, *, field: str) -> str:
    if type(value) is not str or not value:
        _fail(f"{field} は非空 str でなければならない")
    return value


def _normalized_text(value: object, *, field: str) -> str:
    text = _text(value, field=field)
    if text != " ".join(text.split()):
        _fail(f"{field} は空白を canonical 化した str でなければならない")
    return text


def _bool(value: object, *, field: str) -> bool:
    if type(value) is not bool:
        _fail(f"{field} は bool でなければならない")
    return value


def _int(value: object, *, field: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        _fail(f"{field} は {minimum} 以上の int でなければならない")
    return value


def _number(value: object, *, field: str, positive: bool = False) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        _fail(f"{field} は有限の数値でなければならない")
    result = float(value)
    if positive and result <= 0.0:
        _fail(f"{field} は正の有限数でなければならない")
    return result


def _optional_number(value: object, *, field: str) -> Union[float, None]:
    if value is None:
        return None
    return _number(value, field=field)


def _list(value: object, *, field: str) -> list:
    if type(value) is not list:
        _fail(f"{field} は list でなければならない")
    return value


def _text_list(value: object, *, field: str, allow_empty: bool = True) -> List[str]:
    values = _list(value, field=field)
    if not allow_empty and not values:
        _fail(f"{field} は空でない list でなければならない")
    return [_text(item, field=f"{field}[{index}]") for index, item in enumerate(values)]


def _hex(value: object, *, field: str, pattern: re.Pattern[str]) -> str:
    if type(value) is not str or pattern.fullmatch(value) is None:
        _fail(f"{field} は {pattern.pattern} に一致しなければならない")
    return value


@dataclass(frozen=True)
class CpuProfile:
    """CPU identity。raw 名は証拠、normalized 名は canonical 比較値。"""

    vendor: str
    family: int
    model: int
    model_name_raw: str
    model_name_normalized: str

    def __post_init__(self) -> None:
        _text(self.vendor, field="cpu.vendor")
        _int(self.family, field="cpu.family")
        _int(self.model, field="cpu.model")
        _text(self.model_name_raw, field="cpu.model_name_raw")
        _normalized_text(self.model_name_normalized, field="cpu.model_name_normalized")


@dataclass(frozen=True)
class CoreProfile:
    """物理・論理 core 数と affinity から見える論理 CPU 数。"""

    physical: int
    logical: int
    smt_active: bool
    affinity_visible: int

    def __post_init__(self) -> None:
        _int(self.physical, field="cores.physical", minimum=1)
        _int(self.logical, field="cores.logical", minimum=1)
        _bool(self.smt_active, field="cores.smt_active")
        _int(self.affinity_visible, field="cores.affinity_visible", minimum=1)
        if self.logical < self.physical or self.affinity_visible > self.logical:
            _fail("cores の physical/logical/affinity_visible の大小関係が不正")
        if self.smt_active != (self.logical > self.physical):
            _fail("cores.smt_active が physical/logical と不整合")


@dataclass(frozen=True)
class CacheTopologyEntry:
    """sysfs cache 1 instance の canonical topology。"""

    level: int
    type: str
    bytes: int
    line: int
    shared_cpus: List[int]

    def __post_init__(self) -> None:
        _int(self.level, field="cache.level", minimum=1)
        _text(self.type, field="cache.type")
        _int(self.bytes, field="cache.bytes", minimum=1)
        _int(self.line, field="cache.line", minimum=1)
        cpus = _list(self.shared_cpus, field="cache.shared_cpus")
        if not cpus:
            _fail("cache.shared_cpus は空でない list でなければならない")
        parsed = [_int(cpu, field="cache.shared_cpus[]") for cpu in cpus]
        if parsed != sorted(set(parsed)):
            _fail("cache.shared_cpus は昇順かつ重複なしでなければならない")

    def canonical_key(self) -> tuple:
        return (self.level, self.type, self.bytes, self.line, tuple(self.shared_cpus))


@dataclass(frozen=True)
class NumaNode:
    """NUMA node ID と canonical cpulist。"""

    node_id: int
    cpulist: List[int]

    def __post_init__(self) -> None:
        _int(self.node_id, field="numa.node_id")
        cpus = _list(self.cpulist, field="numa.cpulist")
        if not cpus:
            _fail("numa.cpulist は空でない list でなければならない")
        parsed = [_int(cpu, field="numa.cpulist[]") for cpu in cpus]
        if parsed != sorted(set(parsed)):
            _fail("numa.cpulist は昇順かつ重複なしでなければならない")


@dataclass(frozen=True)
class TscProfile:
    """TSC MHz の生 5 標本、median、nearest-even 整数値。"""

    raw_samples_mhz: List[float]
    median_mhz: float
    clocks_per_us_int: int
    source: str

    def __post_init__(self) -> None:
        samples = _list(self.raw_samples_mhz, field="tsc.raw_samples_mhz")
        if len(samples) != 5:
            _fail("tsc.raw_samples_mhz は 5 標本でなければならない")
        parsed = [_number(v, field="tsc.raw_samples_mhz[]", positive=True) for v in samples]
        median = _number(self.median_mhz, field="tsc.median_mhz", positive=True)
        clocks = _int(self.clocks_per_us_int, field="tsc.clocks_per_us_int", minimum=1)
        _text(self.source, field="tsc.source")
        actual_median = float(statistics.median(parsed))
        if not math.isclose(median, actual_median, rel_tol=1e-12, abs_tol=1e-9):
            _fail("tsc.median_mhz が raw_samples_mhz の median と不一致")
        if clocks != round(median):
            _fail("tsc.clocks_per_us_int が median_mhz の nearest-even int と不一致")


@dataclass(frozen=True)
class EffectiveClockProfile:
    """pinned load 下の実効クロック分布と測定条件。"""

    samples_mhz: List[float]
    method: str
    governor: str
    tolerance_pct: float

    def __post_init__(self) -> None:
        samples = _list(self.samples_mhz, field="effective_clock.samples_mhz")
        if not samples:
            _fail("effective_clock.samples_mhz は空でない list でなければならない")
        for sample in samples:
            _number(sample, field="effective_clock.samples_mhz[]", positive=True)
        _text(self.method, field="effective_clock.method")
        _text(self.governor, field="effective_clock.governor")
        tolerance = _number(
            self.tolerance_pct, field="effective_clock.tolerance_pct", positive=True,
        )
        if tolerance >= 100.0:
            _fail("effective_clock.tolerance_pct は 100 未満でなければならない")


@dataclass(frozen=True)
class ObservedEffectiveClockProfile:
    """runtime probe が観測した、policy を持たない実効クロック分布。"""

    samples_mhz: List[float]
    method: str
    governor: str

    def __post_init__(self) -> None:
        samples = _list(self.samples_mhz, field="observed_effective_clock.samples_mhz")
        if not samples:
            _fail("observed_effective_clock.samples_mhz は空でない list でなければならない")
        for sample in samples:
            _number(sample, field="observed_effective_clock.samples_mhz[]", positive=True)
        _text(self.method, field="observed_effective_clock.method")
        _text(self.governor, field="observed_effective_clock.governor")


@dataclass(frozen=True)
class VisibilityProfile:
    """PID visibility と host PID namespace の観測結果・判定方法。"""

    hidepid: str
    pid_ns_shared_with_host: bool
    pid_ns_method: str

    def __post_init__(self) -> None:
        _text(self.hidepid, field="visibility.hidepid")
        _bool(self.pid_ns_shared_with_host, field="visibility.pid_ns_shared_with_host")
        if self.pid_ns_method != PID_NS_METHOD:
            _fail(f"visibility.pid_ns_method は {PID_NS_METHOD!r} でなければならない")


@dataclass(frozen=True)
class AttestationProfile:
    """calibration が持つ expected-side strict hardware profile。"""

    cpu: CpuProfile
    cores: CoreProfile
    cache_topology: List[CacheTopologyEntry]
    numa: List[NumaNode]
    tsc: TscProfile
    effective_clock: EffectiveClockProfile
    visibility: VisibilityProfile

    def __post_init__(self) -> None:
        if not isinstance(self.cpu, CpuProfile) or not isinstance(self.cores, CoreProfile):
            _fail("attestation_profile.cpu/cores の型が不正")
        caches = _list(self.cache_topology, field="attestation_profile.cache_topology")
        if not caches or not all(isinstance(item, CacheTopologyEntry) for item in caches):
            _fail("attestation_profile.cache_topology の型または値が不正")
        cache_keys = [item.canonical_key() for item in caches]
        if cache_keys != sorted(cache_keys) or len(set(cache_keys)) != len(cache_keys):
            _fail("attestation_profile.cache_topology は canonical 順かつ重複なしでなければならない")
        nodes = _list(self.numa, field="attestation_profile.numa")
        if not nodes or not all(isinstance(item, NumaNode) for item in nodes):
            _fail("attestation_profile.numa の型または値が不正")
        node_ids = [item.node_id for item in nodes]
        if node_ids != sorted(set(node_ids)):
            _fail("attestation_profile.numa は node_id 昇順かつ重複なしでなければならない")
        if not isinstance(self.tsc, TscProfile):
            _fail("attestation_profile.tsc の型が不正")
        if not isinstance(self.effective_clock, EffectiveClockProfile):
            _fail("attestation_profile.effective_clock の型が不正")
        if not isinstance(self.visibility, VisibilityProfile):
            _fail("attestation_profile.visibility の型が不正")


@dataclass(frozen=True)
class ObservedAttestationProfile:
    """runtime probe が返す tolerance-free strict hardware profile。"""

    cpu: CpuProfile
    cores: CoreProfile
    cache_topology: List[CacheTopologyEntry]
    numa: List[NumaNode]
    tsc: TscProfile
    effective_clock: ObservedEffectiveClockProfile
    visibility: VisibilityProfile

    def __post_init__(self) -> None:
        if not isinstance(self.cpu, CpuProfile) or not isinstance(self.cores, CoreProfile):
            _fail("observed_attestation_profile.cpu/cores の型が不正")
        caches = _list(self.cache_topology, field="observed_attestation_profile.cache_topology")
        if not caches or not all(isinstance(item, CacheTopologyEntry) for item in caches):
            _fail("observed_attestation_profile.cache_topology の型または値が不正")
        cache_keys = [item.canonical_key() for item in caches]
        if cache_keys != sorted(cache_keys) or len(set(cache_keys)) != len(cache_keys):
            _fail("observed_attestation_profile.cache_topology は canonical 順かつ重複なしでなければならない")
        nodes = _list(self.numa, field="observed_attestation_profile.numa")
        if not nodes or not all(isinstance(item, NumaNode) for item in nodes):
            _fail("observed_attestation_profile.numa の型が不正")
        node_ids = [item.node_id for item in nodes]
        if node_ids != sorted(set(node_ids)):
            _fail("observed_attestation_profile.numa は node_id 昇順かつ重複なしでなければならない")
        if not isinstance(self.tsc, TscProfile):
            _fail("observed_attestation_profile.tsc の型が不正")
        if not isinstance(self.effective_clock, ObservedEffectiveClockProfile):
            _fail("observed_attestation_profile.effective_clock の型が不正")
        if not isinstance(self.visibility, VisibilityProfile):
            _fail("observed_attestation_profile.visibility の型が不正")


@dataclass(frozen=True)
class QsubReceipt:
    request_id: str
    submit_epoch: int
    queue: str
    project: str
    nodes: int
    elapstim_req_s: int

    def __post_init__(self) -> None:
        _text(self.request_id, field="qsub.request_id")
        _int(self.submit_epoch, field="qsub.submit_epoch", minimum=1)
        _text(self.queue, field="qsub.queue")
        _text(self.project, field="qsub.project")
        _int(self.nodes, field="qsub.nodes", minimum=1)
        _int(self.elapstim_req_s, field="qsub.elapstim_req_s", minimum=1)


def normalize_request_id(value: str) -> str:
    """Pegasus の subrequest index ``0:`` だけを比較用に一度除去する。

    receipt に保存する raw ID は変更しない。``1:`` など他の prefix は同一視しない。
    """
    _text(value, field="request_id")
    return value[2:] if value.startswith("0:") else value


@dataclass(frozen=True)
class AllocationReceipt:
    pbs_jobid: str
    assigned_host_qstat: str
    hostname_observed: str
    cpuset_size: int
    ht_off: bool

    def __post_init__(self) -> None:
        _text(self.pbs_jobid, field="allocation.pbs_jobid")
        _text(self.assigned_host_qstat, field="allocation.assigned_host_qstat")
        _text(self.hostname_observed, field="allocation.hostname_observed")
        _int(self.cpuset_size, field="allocation.cpuset_size", minimum=1)
        _bool(self.ht_off, field="allocation.ht_off")


@dataclass(frozen=True)
class ToolchainReceipt:
    module_list: List[str]
    compiler_path: str
    compiler_version: str
    cmake_version: str

    def __post_init__(self) -> None:
        _text_list(self.module_list, field="toolchain.module_list", allow_empty=False)
        _text(self.compiler_path, field="toolchain.compiler_path")
        _text(self.compiler_version, field="toolchain.compiler_version")
        _text(self.cmake_version, field="toolchain.cmake_version")


@dataclass(frozen=True)
class CcbenchReceipt:
    head_sha: str
    pinned_clean: bool
    build_argv: List[str]
    binary_sha256: str

    def __post_init__(self) -> None:
        _hex(self.head_sha, field="ccbench.head_sha", pattern=_HEX40_RE)
        _bool(self.pinned_clean, field="ccbench.pinned_clean")
        _text_list(self.build_argv, field="ccbench.build_argv", allow_empty=False)
        _hex(self.binary_sha256, field="ccbench.binary_sha256", pattern=_HEX64_RE)


@dataclass(frozen=True)
class WalltimeReceipt:
    formula: str
    required_s: int
    reserve_s: int

    def __post_init__(self) -> None:
        _text(self.formula, field="walltime.formula")
        _int(self.required_s, field="walltime.required_s", minimum=1)
        _int(self.reserve_s, field="walltime.reserve_s", minimum=1)
        if self.reserve_s >= self.required_s:
            _fail("walltime.reserve_s は required_s 未満でなければならない")


@dataclass(frozen=True)
class KnownValuesCheck:
    expected_cpu_model: str
    expected_cores: int
    source: str
    passed: bool

    def __post_init__(self) -> None:
        _text(self.expected_cpu_model, field="known_values_check.expected_cpu_model")
        _int(self.expected_cores, field="known_values_check.expected_cores", minimum=1)
        if self.source != _KNOWN_VALUES_SOURCE:
            _fail(f"known_values_check.source は {_KNOWN_VALUES_SOURCE!r} でなければならない")
        _bool(self.passed, field="known_values_check.passed")


@dataclass(frozen=True)
class AcquisitionReceipt:
    """qsub から binary までを calibration JSON 内で束縛する provenance。"""

    qsub: QsubReceipt
    allocation: AllocationReceipt
    toolchain: ToolchainReceipt
    ccbench: CcbenchReceipt
    job_script_sha256: str
    walltime: WalltimeReceipt
    known_values_check: KnownValuesCheck

    def __post_init__(self) -> None:
        expected = (
            (self.qsub, QsubReceipt, "qsub"),
            (self.allocation, AllocationReceipt, "allocation"),
            (self.toolchain, ToolchainReceipt, "toolchain"),
            (self.ccbench, CcbenchReceipt, "ccbench"),
            (self.walltime, WalltimeReceipt, "walltime"),
            (self.known_values_check, KnownValuesCheck, "known_values_check"),
        )
        for value, cls, field in expected:
            if not isinstance(value, cls):
                _fail(f"acquisition_receipt.{field} の型が不正")
        _hex(self.job_script_sha256, field="job_script_sha256", pattern=_HEX64_RE)


@dataclass(frozen=True)
class QualityVerdict:
    status: str
    reasons: List[str]

    def __post_init__(self) -> None:
        if self.status not in {"accepted", "rejected"}:
            _fail("quality.status は 'accepted' または 'rejected' でなければならない")
        reasons = _text_list(self.reasons, field="quality.reasons")
        if self.status == "rejected" and not reasons:
            _fail("quality.status=rejected の reasons は空であってはならない")


@dataclass(frozen=True)
class CalibrationV2:
    """既存 result_to_dict 形と v2 attestation/provenance の同居表現。"""

    schema_version: str
    env_tag: str
    threads: int
    clocks_per_us: int
    saturation: Union[dict, None]
    noise_floor: dict
    scale_sensitivity: Union[str, dict]
    sweep: List[dict]
    workload: Dict[str, str]
    host: Dict[str, str]
    notes: List[str]
    attestation_profile: AttestationProfile
    acquisition_receipt: AcquisitionReceipt
    genome: Union[str, None]
    quality: QualityVerdict

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            _fail(f"schema_version は {SCHEMA_VERSION!r} でなければならない")
        if type(self.env_tag) is not str or _SLUG_RE.fullmatch(self.env_tag) is None:
            _fail("env_tag は canonical slug でなければならない")
        _int(self.threads, field="threads", minimum=1)
        _int(self.clocks_per_us, field="clocks_per_us", minimum=1)
        if not isinstance(self.attestation_profile, AttestationProfile):
            _fail("attestation_profile の型が不正")
        if not isinstance(self.acquisition_receipt, AcquisitionReceipt):
            _fail("acquisition_receipt の型が不正")
        if not isinstance(self.quality, QualityVerdict):
            _fail("quality の型が不正")
        if self.clocks_per_us != self.attestation_profile.tsc.clocks_per_us_int:
            _fail("clocks_per_us と attestation_profile.tsc が不一致")
        if self.threads != self.attestation_profile.cores.affinity_visible:
            _fail("threads と attestation_profile.cores.affinity_visible が不一致")
        if self.quality.status == "accepted":
            if not self.acquisition_receipt.known_values_check.passed:
                _fail("accepted calibration の known_values_check.passed が false")
            if not self.acquisition_receipt.ccbench.pinned_clean:
                _fail("accepted calibration の ccbench.pinned_clean が false")
            if not self.acquisition_receipt.allocation.ht_off:
                _fail("accepted calibration の allocation.ht_off が false")
            if self.saturation is None:
                _fail("accepted calibration の saturation が null")
            if not self.sweep or not self.noise_floor["throughputs"]:
                _fail("accepted calibration の sweep/noise_floor が空")
            if (normalize_request_id(self.acquisition_receipt.qsub.request_id)
                    != normalize_request_id(
                        self.acquisition_receipt.allocation.pbs_jobid)):
                _fail("accepted calibration の qsub ID と PBS_JOBID が不一致")
            if (self.acquisition_receipt.walltime.required_s
                    > self.acquisition_receipt.qsub.elapstim_req_s):
                _fail("accepted calibration の必要 walltime が qsub 要求を超過")
            if (self.acquisition_receipt.allocation.cpuset_size
                    != self.attestation_profile.cores.affinity_visible):
                _fail("accepted calibration の cpuset_size と affinity_visible が不一致")
            if (self.acquisition_receipt.known_values_check.expected_cores
                    != self.attestation_profile.cores.physical):
                _fail("accepted calibration の expected_cores と physical cores が不一致")


_CPU_KEYS = {"vendor", "family", "model", "model_name_raw", "model_name_normalized"}
_CORE_KEYS = {"physical", "logical", "smt_active", "affinity_visible"}
_CACHE_KEYS = {"level", "type", "bytes", "line", "shared_cpus"}
_NUMA_KEYS = {"node_id", "cpulist"}
_TSC_KEYS = {"raw_samples_mhz", "median_mhz", "clocks_per_us_int", "source"}
_CLOCK_KEYS = {"samples_mhz", "method", "governor", "tolerance_pct"}
_VISIBILITY_KEYS = {"hidepid", "pid_ns_shared_with_host", "pid_ns_method"}
_PROFILE_KEYS = {"cpu", "cores", "cache_topology", "numa", "tsc", "effective_clock", "visibility"}
_QSUB_KEYS = {"request_id", "submit_epoch", "queue", "project", "nodes", "elapstim_req_s"}
_ALLOCATION_KEYS = {"pbs_jobid", "assigned_host_qstat", "hostname_observed", "cpuset_size", "ht_off"}
_TOOLCHAIN_KEYS = {"module_list", "compiler_path", "compiler_version", "cmake_version"}
_CCBENCH_KEYS = {"head_sha", "pinned_clean", "build_argv", "binary_sha256"}
_WALLTIME_KEYS = {"formula", "required_s", "reserve_s"}
_KNOWN_KEYS = {"expected_cpu_model", "expected_cores", "source", "passed"}
_ACQUISITION_KEYS = {"qsub", "allocation", "toolchain", "ccbench", "job_script_sha256", "walltime", "known_values_check"}
_QUALITY_KEYS = {"status", "reasons"}
_TOP_KEYS = {
    "schema_version", "env_tag", "threads", "clocks_per_us", "saturation",
    "noise_floor", "scale_sensitivity", "sweep", "workload", "host", "notes",
    "attestation_profile", "acquisition_receipt", "quality",
}
_TOP_KEYS_WITH_GENOME = _TOP_KEYS | {"genome"}
_POINT_KEYS = {
    "records", "threads", "llc_load_misses", "llc_loads", "llc_miss_rate",
    "throughput_median_tps", "throughputs", "walltime_s", "notes",
}
_SAT_KEYS = {
    "records", "saturated", "lower_bound_selected", "threshold", "miss_rate_at",
    "cache_floor_warning", "l3_bytes", "l3_multiple", "working_set_ratio", "series", "notes",
}
_NOISE_KEYS = {"kind", "throughputs", "mean", "median", "stdev", "cv", "high_variance", "notes"}
_SCALE_KEYS = {
    "small", "medium", "small_per_thread", "medium_per_thread", "efficiency_ratio",
    "scale_suspect", "notes",
}


def _profile(value: object) -> AttestationProfile:
    obj = _exact(value, _PROFILE_KEYS, field="attestation_profile")
    cpu = _exact(obj["cpu"], _CPU_KEYS, field="attestation_profile.cpu")
    cores = _exact(obj["cores"], _CORE_KEYS, field="attestation_profile.cores")
    cache_values = _list(obj["cache_topology"], field="attestation_profile.cache_topology")
    caches = []
    for index, raw in enumerate(cache_values):
        item = _exact(raw, _CACHE_KEYS, field=f"attestation_profile.cache_topology[{index}]")
        caches.append(CacheTopologyEntry(**item))
    numa_values = _list(obj["numa"], field="attestation_profile.numa")
    nodes = []
    for index, raw in enumerate(numa_values):
        item = _exact(raw, _NUMA_KEYS, field=f"attestation_profile.numa[{index}]")
        nodes.append(NumaNode(**item))
    tsc = _exact(obj["tsc"], _TSC_KEYS, field="attestation_profile.tsc")
    clock = _exact(obj["effective_clock"], _CLOCK_KEYS, field="attestation_profile.effective_clock")
    visibility = _exact(obj["visibility"], _VISIBILITY_KEYS, field="attestation_profile.visibility")
    return AttestationProfile(
        cpu=CpuProfile(**cpu),
        cores=CoreProfile(**cores),
        cache_topology=caches,
        numa=nodes,
        tsc=TscProfile(**tsc),
        effective_clock=EffectiveClockProfile(**clock),
        visibility=VisibilityProfile(**visibility),
    )


def _acquisition(value: object) -> AcquisitionReceipt:
    obj = _exact(value, _ACQUISITION_KEYS, field="acquisition_receipt")
    qsub = _exact(obj["qsub"], _QSUB_KEYS, field="acquisition_receipt.qsub")
    allocation = _exact(obj["allocation"], _ALLOCATION_KEYS, field="acquisition_receipt.allocation")
    toolchain = _exact(obj["toolchain"], _TOOLCHAIN_KEYS, field="acquisition_receipt.toolchain")
    ccbench = _exact(obj["ccbench"], _CCBENCH_KEYS, field="acquisition_receipt.ccbench")
    walltime = _exact(obj["walltime"], _WALLTIME_KEYS, field="acquisition_receipt.walltime")
    known = _exact(obj["known_values_check"], _KNOWN_KEYS, field="acquisition_receipt.known_values_check")
    return AcquisitionReceipt(
        qsub=QsubReceipt(**qsub),
        allocation=AllocationReceipt(**allocation),
        toolchain=ToolchainReceipt(**toolchain),
        ccbench=CcbenchReceipt(**ccbench),
        job_script_sha256=obj["job_script_sha256"],
        walltime=WalltimeReceipt(**walltime),
        known_values_check=KnownValuesCheck(**known),
    )


def _point(value: object, *, field: str) -> dict:
    obj = _exact(value, _POINT_KEYS, field=field)
    _int(obj["records"], field=f"{field}.records", minimum=1)
    _int(obj["threads"], field=f"{field}.threads", minimum=1)
    for key in ("llc_load_misses", "llc_loads"):
        if obj[key] is not None:
            _int(obj[key], field=f"{field}.{key}")
    for key in ("llc_miss_rate", "throughput_median_tps", "walltime_s"):
        _optional_number(obj[key], field=f"{field}.{key}")
    throughputs = _list(obj["throughputs"], field=f"{field}.throughputs")
    for index, item in enumerate(throughputs):
        _number(item, field=f"{field}.throughputs[{index}]", positive=True)
    _text_list(obj["notes"], field=f"{field}.notes")
    return dict(obj)


def _saturation(value: object) -> Union[dict, None]:
    if value is None:
        return None
    obj = _exact(value, _SAT_KEYS, field="saturation")
    _int(obj["records"], field="saturation.records", minimum=1)
    _bool(obj["saturated"], field="saturation.saturated")
    _bool(obj["lower_bound_selected"], field="saturation.lower_bound_selected")
    _number(obj["threshold"], field="saturation.threshold")
    _optional_number(obj["miss_rate_at"], field="saturation.miss_rate_at")
    _bool(obj["cache_floor_warning"], field="saturation.cache_floor_warning")
    if obj["l3_bytes"] is not None:
        _int(obj["l3_bytes"], field="saturation.l3_bytes", minimum=1)
    for key in ("l3_multiple", "working_set_ratio"):
        _optional_number(obj[key], field=f"saturation.{key}")
    series = _list(obj["series"], field="saturation.series")
    for index, raw in enumerate(series):
        item = _object(raw, field=f"saturation.series[{index}]")
        allowed = {"records", "miss_rate", "delta", "maxrss_kb"}
        required = {"records", "miss_rate"}
        if not required.issubset(item) or not set(item).issubset(allowed):
            _fail(f"saturation.series[{index}] の key 集合が不正")
        _number(item["records"], field=f"saturation.series[{index}].records", positive=True)
        _number(item["miss_rate"], field=f"saturation.series[{index}].miss_rate")
        for key in ("delta", "maxrss_kb"):
            if key in item and item[key] is not None:
                _number(item[key], field=f"saturation.series[{index}].{key}")
    _text_list(obj["notes"], field="saturation.notes")
    return dict(obj)


def _noise(value: object) -> dict:
    obj = _exact(value, _NOISE_KEYS, field="noise_floor")
    if obj["kind"] != "within-run":
        _fail("noise_floor.kind は 'within-run' でなければならない")
    throughputs = _list(obj["throughputs"], field="noise_floor.throughputs")
    for item in throughputs:
        _number(item, field="noise_floor.throughputs[]", positive=True)
    for key in ("mean", "median", "stdev", "cv"):
        _optional_number(obj[key], field=f"noise_floor.{key}")
    _bool(obj["high_variance"], field="noise_floor.high_variance")
    _text_list(obj["notes"], field="noise_floor.notes")
    return dict(obj)


def _scale(value: object) -> Union[str, dict]:
    if value == "not-measured":
        return value
    obj = _exact(value, _SCALE_KEYS, field="scale_sensitivity")
    _point(obj["small"], field="scale_sensitivity.small")
    _point(obj["medium"], field="scale_sensitivity.medium")
    for key in ("small_per_thread", "medium_per_thread", "efficiency_ratio"):
        _optional_number(obj[key], field=f"scale_sensitivity.{key}")
    _bool(obj["scale_suspect"], field="scale_sensitivity.scale_suspect")
    _text_list(obj["notes"], field="scale_sensitivity.notes")
    return dict(obj)


def _string_map(value: object, *, field: str) -> Dict[str, str]:
    obj = _object(value, field=field)
    for key, item in obj.items():
        _text(key, field=f"{field}.key")
        _text(item, field=f"{field}[{key!r}]")
    return dict(obj)


def _duplicate_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            _fail(f"JSON に duplicate key がある: {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str) -> None:
    _fail(f"JSON に非有限数値がある: {token}")


def _parse_input(obj: dict) -> dict:
    if type(obj) is dict:
        return obj
    if type(obj) in (str, bytes, bytearray):
        try:
            parsed = json.loads(
                obj,
                object_pairs_hook=_duplicate_object,
                parse_constant=_reject_constant,
            )
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise CalibrationSchemaError(f"calibration/v2 JSON を parse できない: {exc}") from exc
        return _object(parsed, field="calibration/v2 top-level")
    _fail("calibration/v2 入力は dict または raw JSON text/bytes でなければならない")


def _canonical_genome(value: object) -> str:
    encoded = _text(value, field="genome")
    if encoded.count("|") != 1:
        _fail("genome は protocol|A=1,B=0 形でなければならない")
    protocol, body = encoded.split("|", 1)
    if not protocol or not body:
        _fail("genome の protocol と body は非空でなければならない")
    flags: Dict[str, int] = {}
    for assignment in body.split(","):
        if assignment.count("=") != 1:
            _fail("genome の flag assignment が不正")
        name, raw_value = assignment.split("=", 1)
        if not name or name in flags:
            _fail("genome の flag 名が空または重複している")
        if name == "TRACE":
            _fail("genome の TRACE は予約名である")
        try:
            flags[name] = int(raw_value)
        except ValueError as exc:
            raise CalibrationSchemaError("genome の flag 値は整数でなければならない") from exc
    canonical = protocol + "|" + ",".join(
        f"{name}={flags[name]}" for name in sorted(flags)
    )
    if canonical != encoded:
        _fail("genome が canonical 文字列でない")
    return encoded


def validate_calibration_v2(obj: dict) -> CalibrationV2:
    """calibration/v2 を exact・fail-closed 検証して型付き契約を返す。

    duplicate key を検出可能にするため、reader は dict 化前の raw JSON text/bytes を渡す。
    signature の dict は既存の writer/fixture が直接検証する主経路を表す。
    """
    parsed = _parse_input(obj)
    actual_keys = set(parsed)
    if actual_keys == _TOP_KEYS:
        value = _exact(parsed, _TOP_KEYS, field="calibration/v2")
        genome = None
    elif actual_keys == _TOP_KEYS_WITH_GENOME:
        value = _exact(parsed, _TOP_KEYS_WITH_GENOME, field="calibration/v2")
        genome = _canonical_genome(value["genome"])
    else:
        expected = _TOP_KEYS_WITH_GENOME if "genome" in actual_keys else _TOP_KEYS
        value = _exact(parsed, expected, field="calibration/v2")
        raise AssertionError("unreachable")
    profile = _profile(value["attestation_profile"])
    acquisition = _acquisition(value["acquisition_receipt"])
    quality_obj = _exact(value["quality"], _QUALITY_KEYS, field="quality")
    saturation = _saturation(value["saturation"])
    noise = _noise(value["noise_floor"])
    scale = _scale(value["scale_sensitivity"])
    sweep_values = _list(value["sweep"], field="sweep")
    sweep = [_point(item, field=f"sweep[{index}]") for index, item in enumerate(sweep_values)]
    workload = _string_map(value["workload"], field="workload")
    host = _string_map(value["host"], field="host")
    notes = _text_list(value["notes"], field="notes")
    return CalibrationV2(
        schema_version=value["schema_version"],
        env_tag=value["env_tag"],
        threads=value["threads"],
        clocks_per_us=value["clocks_per_us"],
        saturation=saturation,
        noise_floor=noise,
        scale_sensitivity=scale,
        sweep=sweep,
        workload=workload,
        host=host,
        notes=notes,
        attestation_profile=profile,
        acquisition_receipt=acquisition,
        genome=genome,
        quality=QualityVerdict(**quality_obj),
    )
