# -*- coding: utf-8 -*-
"""P2-4: backoff の spin を分離し、有用 IPC を実測する診断 profile。

``BACKOFF_NOINLINE=1`` で ``Backoff::backoff`` を独立シンボル化し、cycles と
instructions の total と spin 比率を rep ごとに保存する。この診断 build の throughput は
D20 により headline に使えない。

Pegasus では ``dispatch_compute.py --task generic`` から ``balanced`` を明示し、
``output/insights/2026-08-26_b10-balanced-profile/job-body.sh`` の内容を
``/bin/bash -c`` へ渡す。job body は pinned gflags/glog、job 専用 dependency prefix と
build cache を用意してから、この module を起動する。

絶対規律1: perf は trace-disabled build にだけ当てる。
絶対規律4: 単一テナント直列、48 threads、1M records、3 reps、3秒、既存7点を維持する。

  python orchestrator/campaign/backoff_profile.py
  python orchestrator/campaign/backoff_profile.py balanced
"""
from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import math
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from ..calibrator.benchparse import (  # noqa: E402
    abort_rate as parse_abort,
    parse_bench_stdout,
    throughput_tps,
)
from ..holdout_observation import (  # noqa: E402
    assert_holdout_observation_admitted,
)
from . import buildcache, patchharness, pin, source_digest  # noqa: E402
from .build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from .backoff_sweep import _require_backoff_condition_gate  # noqa: E402
from .layout import env_scope_dir  # noqa: E402
from .model import Genome  # noqa: E402
from .p2_2 import (  # noqa: E402
    CLK,
    ENV_TAG,
    EXTIME,
    NUMA,
    RECORDS,
    THREADS,
    _assert_matches_calibration,
    _assert_single_tenant,
    resolve_site_runtime,
)


_BASE = {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0, "WAL": 0}
REPS = 3
BACKOFF_US = [2, 5, 10, 25, 50, 100]
PERF_EVENTS = "cycles,instructions"
CCBENCH_COMMIT = pin.CURRENT_PIN

POINTS = [
    ("write-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"}),
    ("balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}),
]

D20_DIAGNOSTIC_NOTICE = (
    "BACKOFF_NOINLINE=1 diagnostic only; headline throughput に使用不可。"
)
BACKOFF_TIME_NOTICE = "requested us は contract-calibrated であり実時間は未検証。"
DEPENDENCY_IDENTITY_NOTICE = (
    "legacy buildcache.build は dependency prefix を cache identity へ束縛しない。"
    "job 専用 cache root で既存 cache の継承を避ける緩和に留まる。"
)
_COMPARISON_PATH = (
    "output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.json"
)
_CACHE_ROOT_ENV = "IZANAGI_BACKOFF_PROFILE_CACHE_ROOT"
_DEPENDENCY_LOG_ENV = "IZANAGI_BACKOFF_PROFILE_DEPENDENCY_LOG"
_DEPENDENCY_PUBLISH_LOG_ENV = "IZANAGI_BACKOFF_PROFILE_DEPENDENCY_PUBLISH_LOG"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKOFF_PATCH_PATH = _REPO_ROOT / "patches/silo-backoff-fixed.patch"
_CCBENCH_DIR = _REPO_ROOT / "external/ccbench"
_BACKOFF_PATCH_ACTIVE = contextvars.ContextVar(
    "backoff_profile_patch_active", default=False,
)
_BACKOFF_CONDITION_GATE_ACTIVE = contextvars.ContextVar(
    "backoff_profile_condition_gate_active", default=False,
)
_PREBUILT_PROFILE_POINTS = contextvars.ContextVar(
    "backoff_profile_prebuilt_points", default=None,
)


@dataclass(frozen=True)
class _ProfileRuntime:
    """一度解決し、全7点と writer が object identity ごと共有する runtime。"""

    env_tag: str
    clocks_per_us: int
    numactl: tuple[str, ...]
    profiler_executable: str
    cc: str
    cxx: str
    site: str = "legacy-direct"
    contract_sha256: str = ""
    calibration_ref: str = ""
    calibration_sha256: str = ""
    hostname: str = ""
    pbs_jobid: str | None = None
    ccbench_commit: str = ""
    gflags_pin: str = ""
    glog_pin: str = ""
    dependency_prefix: str = ""
    build_cache_root: str = ""
    dependency_build_log: str = ""


@dataclass(frozen=True)
class _BuiltProfilePoint:
    """計測開始前に確定させた 1 点の build 実体。"""

    backoff_us: int | None
    genome: Genome
    result: buildcache.BuildResult


def _policy_path() -> Path:
    return Path(__file__).resolve().parents[2] / "tools/pegasus/policy.json"


def _load_policy_document() -> dict:
    path = _policy_path()
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Pegasus policy を読めない: {path}: {exc}") from exc
    if type(document) is not dict:
        raise RuntimeError("Pegasus policy の top-level は object でなければならない")
    return document


def _resolve_profiler_executable(document=None) -> str:
    """policy 順で最初の absolute regular executable を返し、fallback しない。"""
    if document is None:
        document = _load_policy_document()
    entries = document.get("perf_candidates")
    if type(entries) is not list or not entries:
        raise RuntimeError("Pegasus policy perf_candidates は非空 list でなければならない")
    for candidate in entries:
        if type(candidate) is not str:
            raise RuntimeError("Pegasus policy candidate は str でなければならない")
        path = Path(candidate)
        if not path.is_absolute():
            raise RuntimeError(f"Pegasus policy candidate は absolute path が必要: {candidate!r}")
        if path.is_file() and os.access(path, os.X_OK):
            return str(path.resolve())
    raise RuntimeError("Pegasus policy の候補に実行可能な profiler がない")


def _dependency_pins(document: dict) -> tuple[str, str]:
    first = document.get("gflags_expected_head")
    second = document.get("glog_expected_head")
    pattern = re.compile(r"[0-9a-f]{40}")
    if type(first) is not str or pattern.fullmatch(first) is None:
        raise RuntimeError("Pegasus policy gflags pin が full 40 hex でない")
    if type(second) is not str or pattern.fullmatch(second) is None:
        raise RuntimeError("Pegasus policy glog pin が full 40 hex でない")
    return first, second


def _read_dependency_pins(
    directory: str, document: dict, dependency_prefix: str, cache_root: str,
) -> tuple[str, str]:
    """job body が記録した実 checkout を読み、policy と一致するときだけ返す。"""
    path = Path(directory) / "dependency-provenance.json"
    try:
        recorded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"dependency provenance を読めない: {path}: {exc}") from exc
    if type(recorded) is not dict:
        raise RuntimeError("dependency provenance の top-level は object が必要")

    expected = _dependency_pins(document)
    keys = ("gflags_pin", "glog_pin")
    pattern = re.compile(r"[0-9a-f]{40}")
    actual = tuple(recorded.get(key) for key in keys)
    if any(type(value) is not str or pattern.fullmatch(value) is None
           for value in actual):
        raise RuntimeError("dependency provenance の実 checkout が full 40 hex でない")
    if actual != expected:
        raise RuntimeError(
            "dependency checkout が policy pin と不一致: "
            f"actual={actual!r} expected={expected!r}"
        )
    bindings = (
        ("dependency_prefix", dependency_prefix),
        ("ccbench_cache_root", cache_root),
    )
    mismatches = [
        key for key, value in bindings if recorded.get(key) != value
    ]
    if mismatches:
        raise RuntimeError(
            f"dependency provenance の path binding が不一致: {mismatches}"
        )
    return actual


def _checkout_git_dir(checkout: Path) -> Path:
    marker = checkout / ".git"
    if marker.is_dir():
        return marker.resolve()
    try:
        text = marker.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"ccbench gitdir を読めない: {marker}: {exc}") from exc
    prefix = "gitdir: "
    if not text.startswith(prefix):
        raise RuntimeError(f"ccbench .git marker が不正: {marker}")
    return (checkout / text[len(prefix):]).resolve()


def _resolve_full_ccbench_commit() -> str:
    checkout = Path(__file__).resolve().parents[2] / "external/ccbench"
    git_dir = _checkout_git_dir(checkout)
    try:
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"ccbench HEAD を読めない: {exc}") from exc
    if head.startswith("ref: "):
        ref = head[5:]
        loose = git_dir / ref
        if loose.is_file():
            head = loose.read_text(encoding="utf-8").strip()
        else:
            packed = git_dir / "packed-refs"
            try:
                records = packed.read_text(encoding="utf-8").splitlines()
            except OSError as exc:
                raise RuntimeError(f"ccbench ref を解決できない: {ref}: {exc}") from exc
            matches = [
                line.split(" ", 1)[0]
                for line in records
                if line and not line.startswith(("#", "^")) and line.endswith(f" {ref}")
            ]
            if len(matches) != 1:
                raise RuntimeError(f"ccbench ref を一意に解決できない: {ref}")
            head = matches[0]
    if re.fullmatch(r"[0-9a-f]{40}", head) is None:
        raise RuntimeError(f"ccbench HEAD が full 40 hex でない: {head!r}")
    if not head.startswith(CCBENCH_COMMIT):
        raise RuntimeError(
            f"ccbench HEAD が current pin と不一致: {head} != {CCBENCH_COMMIT}"
        )
    return head


def _default_runtime() -> _ProfileRuntime:
    cc, cxx = buildcache.compilers_for_current_site()
    return _ProfileRuntime(
        env_tag=ENV_TAG,
        clocks_per_us=CLK,
        numactl=tuple(NUMA),
        profiler_executable="perf",
        cc=cc,
        cxx=cxx,
        dependency_prefix=os.environ.get("CMAKE_PREFIX_PATH", ""),
        build_cache_root=os.environ.get(_CACHE_ROOT_ENV, ""),
        dependency_build_log=os.environ.get(
            _DEPENDENCY_PUBLISH_LOG_ENV,
            os.environ.get(_DEPENDENCY_LOG_ENV, ""),
        ),
    )


def _build_profile_runtime(site, contract, loaded, document: dict) -> _ProfileRuntime:
    dependency_prefix = os.environ.get("CMAKE_PREFIX_PATH", "")
    cache_root = os.environ.get(_CACHE_ROOT_ENV, "")
    dependency_log_source = os.environ.get(_DEPENDENCY_LOG_ENV, "")
    dependency_log = os.environ.get(_DEPENDENCY_PUBLISH_LOG_ENV, "")
    if contract.attestation_mode == "required":
        if not dependency_prefix:
            raise RuntimeError("Pegasus profile は job 専用 CMAKE_PREFIX_PATH が必要")
        if not cache_root or not os.path.isabs(cache_root):
            raise RuntimeError("Pegasus profile は absolute な job 専用 cache root が必要")
        if not dependency_log_source or not os.path.isabs(dependency_log_source):
            raise RuntimeError("Pegasus profile は dependency build log path が必要")
        if not dependency_log or not os.path.isabs(dependency_log):
            raise RuntimeError("Pegasus profile は dependency publish log path が必要")
    first, second = _read_dependency_pins(
        dependency_log_source, document, dependency_prefix, cache_root,
    )
    cc, cxx = buildcache.compilers_for_current_site()
    return _ProfileRuntime(
        site=site,
        env_tag=contract.env_tag,
        clocks_per_us=contract.clocks_per_us,
        numactl=tuple(contract.numactl),
        profiler_executable=_resolve_profiler_executable(document),
        cc=cc,
        cxx=cxx,
        contract_sha256=contract.contract_sha256,
        calibration_ref=contract.calibration_ref.path,
        calibration_sha256=loaded.verified.sha256,
        hostname=socket.gethostname(),
        pbs_jobid=os.environ.get("PBS_JOBID"),
        ccbench_commit=_resolve_full_ccbench_commit(),
        gflags_pin=first,
        glog_pin=second,
        dependency_prefix=dependency_prefix,
        build_cache_root=cache_root,
        dependency_build_log=dependency_log,
    )


def _genome(backoff_us):
    """backoff_us=None は無 backoff、それ以外は静的固定 + noinline 診断。"""
    if backoff_us is None:
        return Genome(
            "silo",
            {**_BASE, "BACK_OFF": 0, "BACKOFF_FIXED": -1, "BACKOFF_NOINLINE": 1},
        )
    return Genome(
        "silo",
        {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": backoff_us,
         "BACKOFF_NOINLINE": 1},
    )


def _require_condition_gate_before_measurement(
        source_root: str, *, stock_root: str,
        amounts: list[int | None], cxx: str,
):
    """Gate the fixed amount and diagnostic noinline define independently."""
    return _require_backoff_condition_gate(
        source_root,
        stock_root=stock_root,
        driver_id="orchestrator/campaign/backoff_profile.py",
        macro_values={
            "BACKOFF_FIXED": tuple(
                -1 if amount is None else amount for amount in amounts
            ),
            "BACKOFF_NOINLINE": (1,),
        },
        cxx=cxx,
        use_class="raw-measurement",
    )


@contextlib.contextmanager
def _applied_backoff_patch():
    """同一 workload 内では一度だけ backoff patch を apply/revert する。"""
    if _BACKOFF_PATCH_ACTIVE.get():
        yield
        return
    with patchharness.applied(
        str(_BACKOFF_PATCH_PATH), CCBENCH_COMMIT, str(_CCBENCH_DIR),
    ):
        token = _BACKOFF_PATCH_ACTIVE.set(True)
        try:
            yield
        finally:
            _BACKOFF_PATCH_ACTIVE.reset(token)


@contextlib.contextmanager
def _condition_gate_scope(runtime: _ProfileRuntime, amounts: list[int | None]):
    """Run the family once before the enclosing scope can build or measure."""
    if _BACKOFF_CONDITION_GATE_ACTIVE.get():
        yield
        return
    with patchharness.checkout(
            CCBENCH_COMMIT, base_dir=str(_CCBENCH_DIR),
    ) as stock_root:
        _require_condition_gate_before_measurement(
            str(_CCBENCH_DIR),
            stock_root=stock_root,
            amounts=amounts,
            cxx=runtime.cxx,
        )
        token = _BACKOFF_CONDITION_GATE_ACTIVE.set(True)
        try:
            yield
        finally:
            _BACKOFF_CONDITION_GATE_ACTIVE.reset(token)


def _point_label(backoff_us) -> str:
    return "none" if backoff_us is None else f"{backoff_us}us"


def _assert_distinct_backoff_binary_hashes(
    built_points: list[_BuiltProfilePoint],
) -> None:
    """全7点の BuildResult が相異なる binary hash を持つことを検査する。"""
    expected = [None, *BACKOFF_US]
    observed = [point.backoff_us for point in built_points]
    if observed != expected:
        raise RuntimeError(
            f"backoff build grid が凍結7点と不一致: {observed!r} != {expected!r}"
        )

    by_hash: dict[str, list[int | None]] = {}
    for point in built_points:
        digest = point.result.bin_sha256
        if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise RuntimeError(
                "backoff build の binary hash が sha256 でない: "
                f"point={_point_label(point.backoff_us)} hash={digest!r}"
            )
        by_hash.setdefault(digest, []).append(point.backoff_us)

    collisions = [
        f"sha256={digest} points=[{', '.join(map(_point_label, points))}]"
        for digest, points in by_hash.items()
        if len(points) > 1
    ]
    if collisions:
        raise RuntimeError(
            "backoff build の binary hash が点間で衝突: " + "; ".join(collisions)
        )


def _elf_slice(raw: bytes, offset: int, size: int, label: str) -> bytes:
    end = offset + size
    if offset < 0 or size < 0 or end < offset or end > len(raw):
        raise RuntimeError(
            f"ELF {label} が file 範囲外: offset={offset} size={size}"
        )
    return raw[offset:end]


def _elf_string(table: bytes, offset: int, label: str) -> bytes:
    if offset < 0 or offset >= len(table):
        raise RuntimeError(f"ELF {label} の文字列 offset が範囲外: {offset}")
    end = table.find(b"\0", offset)
    if end < 0:
        raise RuntimeError(f"ELF {label} の文字列が NUL 終端されていない")
    return table[offset:end]


def _itanium_nested_name_components(symbol: str) -> tuple[str, ...] | None:
    """単純な Itanium nested-name の length-prefixed component を返す。"""
    if not symbol.startswith("_ZN"):
        return None
    cursor = 3
    while cursor < len(symbol) and symbol[cursor] in "KVRrO":
        cursor += 1
    components = []
    while cursor < len(symbol) and symbol[cursor] != "E":
        length_start = cursor
        while cursor < len(symbol) and symbol[cursor].isdigit():
            cursor += 1
        if length_start == cursor:
            return None
        length = int(symbol[length_start:cursor])
        if length <= 0 or cursor + length > len(symbol):
            return None
        components.append(symbol[cursor:cursor + length])
        cursor += length
    if cursor >= len(symbol) or symbol[cursor] != "E" or cursor + 1 >= len(symbol):
        return None
    return tuple(components)


def _is_backoff_function_symbol(symbol: str) -> bool:
    components = _itanium_nested_name_components(symbol)
    return components is not None and components[-2:] == ("Backoff", "backoff")


def _elf_section_label(index: int, name: str, section_type: int) -> str:
    if name:
        return name
    type_name = {
        2: "SHT_SYMTAB",
        3: "SHT_STRTAB",
        11: "SHT_DYNSYM",
    }.get(section_type, f"type={section_type}")
    return f"section[{index}]({type_name})"


def _assert_backoff_symbol_present(binary: str) -> None:
    """ELF symbol table を直接読み、定義済み Backoff::backoff を要求する。"""
    path = Path(binary)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RuntimeError(f"backoff binary を読めない: {path}: {exc}") from exc
    if len(raw) < 16 or raw[:4] != b"\x7fELF":
        raise RuntimeError(f"backoff binary が ELF でない: {path}")

    elf_class = raw[4]
    data_encoding = raw[5]
    if data_encoding == 1:
        byte_order = "<"
        endian_label = "little"
    elif data_encoding == 2:
        byte_order = ">"
        endian_label = "big"
    else:
        raise RuntimeError(f"ELF data encoding が未対応: {data_encoding}")
    if elf_class == 1:
        class_label = "32"
        header_format = byte_order + "HHIIIIIHHHHHH"
        section_format = byte_order + "IIIIIIIIII"
        symbol_format = byte_order + "IIIBBH"
    elif elf_class == 2:
        class_label = "64"
        header_format = byte_order + "HHIQQQIHHHHHH"
        section_format = byte_order + "IIQQQQIIQQ"
        symbol_format = byte_order + "IBBHQQ"
    else:
        raise RuntimeError(f"ELF class が未対応: {elf_class}")

    header_size = struct.calcsize(header_format)
    _elf_slice(raw, 16, header_size, "header")
    header = struct.unpack_from(header_format, raw, 16)
    section_offset = header[5]
    section_entry_size = header[10]
    section_count = header[11]
    section_names_index = header[12]
    required_section_size = struct.calcsize(section_format)
    if section_entry_size < required_section_size:
        raise RuntimeError(
            "ELF section header size が不足: "
            f"{section_entry_size} < {required_section_size}"
        )

    section_zero = None
    if section_count == 0 or section_names_index == 0xffff:
        _elf_slice(raw, section_offset, required_section_size, "section header 0")
        section_zero = struct.unpack_from(section_format, raw, section_offset)
    if section_count == 0:
        section_count = section_zero[5]
    if section_names_index == 0xffff:
        section_names_index = section_zero[6]
    if section_count <= 0:
        raise RuntimeError("ELF section header がない")

    sections = []
    for index in range(section_count):
        offset = section_offset + index * section_entry_size
        _elf_slice(raw, offset, required_section_size, f"section header {index}")
        sections.append(struct.unpack_from(section_format, raw, offset))

    section_names = ["" for _ in sections]
    section_name_errors = []
    if section_names_index >= section_count:
        section_name_errors.append(
            "section-name table index が範囲外: "
            f"{section_names_index} >= {section_count}"
        )
    else:
        names_section = sections[section_names_index]
        try:
            section_names_data = _elf_slice(
                raw, names_section[4], names_section[5], "section-name table",
            )
        except RuntimeError as exc:
            section_name_errors.append(str(exc))
        else:
            for index, section in enumerate(sections):
                try:
                    name_bytes = _elf_string(
                        section_names_data, section[0], f"section {index} name",
                    )
                    section_names[index] = name_bytes.decode("ascii")
                except (RuntimeError, UnicodeDecodeError) as exc:
                    section_name_errors.append(f"section {index}: {exc}")

    # section 名を判定条件にしない。SHT_SYMTAB と SHT_DYNSYM を sh_link で辿る。
    symbol_table_indexes = [
        index for index, section in enumerate(sections)
        if section[1] in {2, 11}
    ]

    required_symbol_size = struct.calcsize(symbol_format)
    referenced_sections = []
    parse_errors = []
    symbol_count = 0
    ackoff_count = 0
    ackoff_names = []
    for symbol_table_index in symbol_table_indexes:
        symbol_table = sections[symbol_table_index]
        string_index = symbol_table[6]
        table_label = _elf_section_label(
            symbol_table_index,
            section_names[symbol_table_index],
            symbol_table[1],
        )
        if string_index >= section_count:
            referenced_sections.append(f"{table_label} -> <範囲外:{string_index}>")
            parse_errors.append(
                f"{table_label} の string table index が範囲外: {string_index}"
            )
            continue
        strings_section = sections[string_index]
        strings_label = _elf_section_label(
            string_index, section_names[string_index], strings_section[1],
        )
        referenced_sections.append(f"{table_label} -> {strings_label}")
        if strings_section[1] != 3:
            parse_errors.append(
                f"{table_label} の参照先が SHT_STRTAB でない: {strings_label}"
            )
            continue
        try:
            strings = _elf_slice(
                raw, strings_section[4], strings_section[5],
                f"{strings_label} symbol string table",
            )
        except RuntimeError as exc:
            parse_errors.append(str(exc))
            continue
        entry_size = symbol_table[9]
        if (
            entry_size < required_symbol_size
            or symbol_table[5] % entry_size
        ):
            parse_errors.append(f"{table_label} entry size が不正")
            continue
        try:
            symbols = _elf_slice(
                raw, symbol_table[4], symbol_table[5], f"{table_label} symbol table",
            )
        except RuntimeError as exc:
            parse_errors.append(str(exc))
            continue
        for offset in range(0, len(symbols), entry_size):
            entry = struct.unpack_from(symbol_format, symbols, offset)
            if elf_class == 1:
                name_offset, symbol_info, section_index = entry[0], entry[3], entry[5]
            else:
                name_offset, symbol_info, section_index = entry[0], entry[1], entry[3]
            try:
                name_bytes = _elf_string(strings, name_offset, "symbol name")
                symbol = name_bytes.decode("ascii")
            except (RuntimeError, UnicodeDecodeError) as exc:
                parse_errors.append(f"{table_label} symbol offset {offset}: {exc}")
                continue
            if not symbol:
                continue
            symbol_count += 1
            if "ackoff" in symbol.casefold():
                ackoff_count += 1
                if len(ackoff_names) < 20:
                    ackoff_names.append(symbol)
            if section_index == 0 or symbol_info & 0x0f != 2:
                continue
            if _is_backoff_function_symbol(symbol):
                return

    symtab_indexes = [
        index for index, section in enumerate(sections) if section[1] == 2
    ]
    symtab_found = bool(symtab_indexes)
    strtab_found = any(
        sections[index][6] < section_count
        and sections[sections[index][6]][1] == 3
        for index in symtab_indexes
    )
    referenced = ", ".join(referenced_sections) if referenced_sections else "0 件"
    if ackoff_names:
        ackoff_detail = (
            f"{ackoff_count} 件"
            + (" (先頭 20 件)" if ackoff_count > 20 else "")
            + ": " + ", ".join(ackoff_names)
        )
    else:
        ackoff_detail = "0 件"
    details = [
        f"backoff binary に Backoff::backoff symbol がない: {path}",
        f"binary size={len(raw)} bytes; ELF class={class_label}; endian={endian_label}",
        f"解析できた symbol の総数={symbol_count}",
        f"参照した section={referenced}",
        f".symtab found={'yes' if symtab_found else 'no'}; "
        f".strtab found={'yes' if strtab_found else 'no'}",
        f"ackoff 候補={ackoff_detail}",
    ]
    if not symtab_found or not strtab_found:
        listed_names = [name for name in section_names if name][:40]
        if not listed_names:
            listed_names = ["<名前を解決できた section は 0 件>"]
        details.append("section 一覧 (最大 40)=" + ", ".join(listed_names))
    if section_name_errors:
        details.append("section 名解決エラー=" + "; ".join(section_name_errors[:20]))
    if parse_errors:
        details.append("symbol 解析エラー=" + "; ".join(parse_errors[:20]))
    raise RuntimeError("\n".join(details))


def _assert_profile_point_backoff_symbol(built_point: _BuiltProfilePoint) -> None:
    """backoff 有効点だけ、独立した backoff 関数 symbol を要求する。"""
    if built_point.backoff_us is None:
        return
    _assert_backoff_symbol_present(built_point.result.binary)


def _flags(workload, clocks_per_us=CLK):
    flags = [
        f"-thread_num={THREADS}",
        f"-ycsb_tuple_num={RECORDS}",
        f"-extime={EXTIME}",
        f"-clocks_per_us={clocks_per_us}",
    ]
    for key, value in workload.items():
        flags.append(f"-{key}={value}")
    return flags


def _parse_perf_report(report_text):
    """report から event total と Backoff::backoff entry の比率を取る。"""
    totals = {}
    spin_pct = {}
    current = None
    for line in report_text.splitlines():
        match = re.search(r"of event '([^']+)'", line)
        if match:
            current = match.group(1)
            continue
        match = re.search(r"Event count \(approx\.\):\s*(\d+)", line)
        if match and current:
            totals[current] = int(match.group(1))
            continue
        if current:
            match = re.match(
                r"\s*([\d.]+)%\s+.*?\[[^]]+\]\s+(.+?)\s*$", line,
            )
            if match and match.group(2) == "Backoff::backoff":
                spin_pct[current] = float(match.group(1))
    return totals, spin_pct


def _profile_run(binary, workload, tmp, runtime, backoff_us):
    """1 run record/report し、complete な生値を返す。"""
    data = os.path.join(tmp, "perf.data")
    cmd = list(runtime.numactl) + [
        runtime.profiler_executable,
        "record",
        "-o",
        data,
        "-e",
        PERF_EVENTS,
        "--",
        binary,
    ] + _flags(workload, runtime.clocks_per_us)
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp, timeout=180)
    if proc.returncode != 0 or not os.path.exists(data):
        raise RuntimeError(
            f"perf record failed (rc={proc.returncode}, "
            f"perf.data={'有' if os.path.exists(data) else '無'}): "
            f"{proc.stderr[-400:]}"
        )
    metrics = parse_bench_stdout(proc.stdout)
    if not metrics:
        raise RuntimeError(f"ccbench produced no metrics. stderr={proc.stderr[-300:]}")
    tps = throughput_tps(metrics)
    abort = parse_abort(metrics)
    rep = subprocess.run(
        [runtime.profiler_executable, "report", "-i", data, "--stdio",
         "--percent-limit", "0"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if rep.returncode != 0:
        raise RuntimeError(
            f"perf report failed (rc={rep.returncode}): {rep.stderr[-300:]}"
        )
    totals, spin = _parse_perf_report(rep.stdout)
    events = ("cycles", "instructions")
    missing_totals = [event for event in events
                      if type(totals.get(event)) is not int or totals[event] <= 0]
    if missing_totals:
        raise RuntimeError(f"perf report total が欠落: {missing_totals}")
    missing_symbols = [event for event in events if event not in spin]
    if backoff_us is not None and missing_symbols:
        raise RuntimeError(
            "backoff 有効点で Backoff::backoff entry が欠落: "
            f"{missing_symbols}"
        )
    return {
        "tps": tps,
        "abort": abort,
        "cycles": totals["cycles"],
        "instructions": totals["instructions"],
        "spin_cyc_pct": spin.get("cycles", 0.0),
        "spin_instr_pct": spin.get("instructions", 0.0),
    }


def _median(xs):
    values = sorted(value for value in xs if value is not None)
    return values[len(values) // 2] if values else None


def _derive_rep(run):
    cycles = run["cycles"]
    instructions = run["instructions"]
    spin_cycles = run["spin_cyc_pct"] / 100.0
    spin_instructions = run["spin_instr_pct"] / 100.0
    total_ipc = (instructions / cycles) if cycles and instructions else None
    useful_cycles = cycles * (1 - spin_cycles) if cycles else None
    useful_instructions = instructions * (1 - spin_instructions) if instructions else None
    useful_ipc = (
        useful_instructions / useful_cycles
        if useful_cycles and useful_instructions else None
    )
    tps = run["tps"]
    abort = run["abort"]
    k_total = (
        tps / ((1 - abort) * total_ipc)
        if tps and abort is not None and total_ipc else None
    )
    k_useful = (
        tps / ((1 - abort) * useful_ipc)
        if tps and abort is not None and useful_ipc else None
    )
    return {
        "tps": tps,
        "abort": abort,
        "cycles": cycles,
        "instructions": instructions,
        "spin_cyc_pct": run["spin_cyc_pct"],
        "spin_instr_pct": run["spin_instr_pct"],
        "total_ipc": total_ipc,
        "useful_ipc": useful_ipc,
        "k_total": k_total,
        "k_useful": k_useful,
    }


def _build_profile_point_in_patch(backoff_us, runtime) -> _BuiltProfilePoint:
    """適用済み patch scope 内で 1 backoff 量を build する。"""
    genome = _genome(backoff_us)
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_PROFILE)
    evidence = source_digest.resolve_evidence(
        genome, CCBENCH_COMMIT, cxx=runtime.cxx,
    )
    capability = attest_generator_output(
        build_context,
        evidence,
        generator_input_sha256=hashlib.sha256(
            f"backoff-profile/v1|{genome.canonical()}".encode("utf-8")
        ).hexdigest(),
    )
    built = buildcache.build(
        genome,
        ccbench_commit=CCBENCH_COMMIT,
        trace=False,
        cache_root=runtime.build_cache_root,
        cc=runtime.cc,
        cxx=runtime.cxx,
        admission=derive_build_admission(
            build_context, evidence, generator_receipt=capability,
        ),
        build_context=build_context,
        source_evidence=evidence,
    )
    return _BuiltProfilePoint(backoff_us, genome, built)


def _measure_built_profile_point(
    built_point, workload_snapshot, log, runtime,
):
    """全 build gate 通過後の 1 点を profile する。"""
    backoff_us = built_point.backoff_us
    genome = built_point.genome
    binary = built_point.result.binary
    _assert_single_tenant()
    runs = []
    for _ in range(REPS):
        tmp = tempfile.mkdtemp(prefix="izanagi_prof_")
        try:
            runs.append(
                _profile_run(binary, workload_snapshot, tmp, runtime, backoff_us)
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    tps_median = _median([run["tps"] for run in runs])
    representative = min(
        (run for run in runs if run["tps"] is not None),
        key=lambda run: abs(run["tps"] - tps_median),
        default=runs[-1],
    )
    derived = _derive_rep(representative)
    abort = representative["abort"]
    k_total = (
        tps_median / ((1 - abort) * derived["total_ipc"])
        if tps_median and abort is not None and derived["total_ipc"] else None
    )
    k_useful = (
        tps_median / ((1 - abort) * derived["useful_ipc"])
        if tps_median and abort is not None and derived["useful_ipc"] else None
    )
    row = {
        "backoff_us": backoff_us if backoff_us is not None else 0,
        "is_none": backoff_us is None,
        "genome": genome.canonical(),
        "tps_median": tps_median,
        "abort": abort,
        "total_ipc": derived["total_ipc"],
        "useful_ipc": derived["useful_ipc"],
        "spin_cyc_pct": representative["spin_cyc_pct"],
        "spin_instr_pct": representative["spin_instr_pct"],
        "k_total": k_total,
        "k_useful": k_useful,
        "tps_all": [run["tps"] for run in runs],
        "reps": [_derive_rep(run) for run in runs],
    }
    log(
        f"  backoff={row['backoff_us']:>4}us  tps={tps_median:>12,.0f}  "
        f"abort={abort * 100:5.1f}%  spin_cyc={row['spin_cyc_pct']:5.1f}%  "
        f"total_ipc={row['total_ipc']:.3f}  useful_ipc={row['useful_ipc']:.3f}  "
        f"K_useful={k_useful:,.0f}"
    )
    return row


def profile_point(backoff_us, workload, log=print, *, runtime=None):
    """1 backoff 量を REPS 回 profile し、有用 IPC を含む集計を返す。"""
    workload_snapshot = dict(workload)
    clock = runtime.clocks_per_us if runtime is not None else CLK
    assert_holdout_observation_admitted(
        gflags=tuple(_flags(workload_snapshot, clock)), admission=None,
    )
    if runtime is None:
        runtime = _default_runtime()
    with _applied_backoff_patch():
        with _condition_gate_scope(runtime, [backoff_us]):
            prebuilt = _PREBUILT_PROFILE_POINTS.get()
            if prebuilt is None:
                built_point = _build_profile_point_in_patch(backoff_us, runtime)
                _assert_profile_point_backoff_symbol(built_point)
            else:
                try:
                    built_point = prebuilt[backoff_us]
                except KeyError as exc:
                    raise RuntimeError(
                        f"prebuilt backoff point がない: {_point_label(backoff_us)}"
                    ) from exc
            return _measure_built_profile_point(
                built_point, workload_snapshot, log, runtime,
            )


def profile_workload(tag, workload, log=print, *, runtime=None):
    effective = runtime
    if effective is None:
        effective = _default_runtime()
    log(f"\n=== backoff profile  workload={tag}  ({workload}) ===")
    log(
        f"  {'pt':>6} {'tps':>14} {'abort':>7} {'spin_cyc':>9} "
        f"{'tot_ipc':>8} {'use_ipc':>8} {'K_useful':>12}"
    )
    workload_snapshot = dict(workload)
    assert_holdout_observation_admitted(
        gflags=tuple(_flags(workload_snapshot, effective.clocks_per_us)),
        admission=None,
    )
    amounts = [None, *BACKOFF_US]
    with _applied_backoff_patch():
        with _condition_gate_scope(effective, amounts):
            built_points = [
                _build_profile_point_in_patch(amount, effective) for amount in amounts
            ]
            _assert_distinct_backoff_binary_hashes(built_points)
            for built_point in built_points:
                _assert_profile_point_backoff_symbol(built_point)
            token = _PREBUILT_PROFILE_POINTS.set({
                point.backoff_us: point for point in built_points
            })
            try:
                rows = [
                    profile_point(
                        amount, workload_snapshot, log, runtime=effective,
                    )
                    for amount in amounts
                ]
            finally:
                _PREBUILT_PROFILE_POINTS.reset(token)
    return rows


def _spread(values):
    return (
        (max(values) - min(values)) / (sum(values) / len(values))
        if values else None
    )


def _comparison_receipt() -> dict[str, str]:
    path = Path(__file__).resolve().parents[2] / _COMPARISON_PATH
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RuntimeError(f"比較対象を読めない: {_COMPARISON_PATH}: {exc}") from exc
    return {"path": _COMPARISON_PATH, "sha256": hashlib.sha256(raw).hexdigest()}


def _finite_positive(value) -> bool:
    return (
        type(value) in {int, float}
        and math.isfinite(value)
        and value > 0
    )


def _evaluation_band(rows):
    required = ((0, True), (2, False), (5, False), (10, False))
    grouped = {
        key: [
            row for row in rows
            if (row.get("backoff_us"), row.get("is_none")) == key
        ]
        for key in required
    }
    missing = [key for key, entries in grouped.items() if len(entries) != 1]
    if missing:
        return None, None, (
            "評価帯 S の凍結4点 (none, 2, 5, 10us) が一意に揃わない: "
            f"{missing}"
        )
    ordered = [grouped[key][0] for key in required]
    invalid_useful = [
        key for key, row in zip(required, ordered)
        if not _finite_positive(row.get("useful_ipc"))
    ]
    if invalid_useful:
        return None, None, (
            "評価帯 S の useful_ipc が有限の正値でない: "
            f"{invalid_useful}"
        )
    invalid_total = [
        key for key, row in zip(required, ordered)
        if not _finite_positive(row.get("total_ipc"))
    ]
    if invalid_total:
        return None, None, (
            "評価帯 S の total_ipc が有限の正値でないため判定不能: "
            f"{invalid_total}"
        )
    return (
        [row["useful_ipc"] for row in ordered],
        [row["total_ipc"] for row in ordered],
        None,
    )


def _format_spread(value) -> str:
    return "N/A" if value is None else f"{value * 100:.1f}%"


def _publish_pair(staged_json: Path, staged_md: Path, final_json: Path, final_md: Path):
    """両 staging file 完成後に publish し、途中失敗なら片残りを戻す。"""
    if final_json.exists() != final_md.exists():
        raise RuntimeError("既存成果物 pair が片方だけであり、安全に更新できない")
    previous_json = staged_json.with_name("previous.json")
    previous_md = staged_md.with_name("previous.md")
    had_previous = final_json.exists()
    if had_previous:
        shutil.copy2(final_json, previous_json)
        shutil.copy2(final_md, previous_md)
    published = []
    try:
        os.replace(staged_json, final_json)
        published.append(final_json)
        os.replace(staged_md, final_md)
        published.append(final_md)
    except BaseException:
        if had_previous:
            if final_json in published:
                os.replace(previous_json, final_json)
            if final_md in published:
                os.replace(previous_md, final_md)
        else:
            for path in published:
                path.unlink(missing_ok=True)
        raise


def _write_out(tag, workload, rows, env_tag, runtime, log=print):
    """JSON/MD を同じ runtime provenance で書く。env_tag に default は持たない。"""
    if env_tag != runtime.env_tag:
        raise RuntimeError(
            f"writer env_tag が runtime と不一致: {env_tag!r} != {runtime.env_tag!r}"
        )
    out_dir = os.path.join(env_scope_dir(env_tag), "profile")
    os.makedirs(out_dir, exist_ok=True)
    workload_name = (
        f"skew{workload['ycsb_zipf_skew'].replace('.', 'p')}_"
        f"rr{workload['ycsb_rratio']}"
    )
    stem = os.path.join(out_dir, f"backoff_profile_t{THREADS}_{workload_name}")
    useful_all = [row["useful_ipc"] for row in rows
                  if _finite_positive(row.get("useful_ipc"))]
    total_all = [row["total_ipc"] for row in rows
                 if _finite_positive(row.get("total_ipc"))]
    useful_band, total_band, inconclusive_reason = _evaluation_band(rows)
    useful_band_spread = _spread(useful_band)
    total_band_spread = _spread(total_band)
    condition_met = (
        inconclusive_reason is None
        and useful_band_spread <= total_band_spread
        and useful_band_spread <= 0.044
    )
    decision_status = (
        "inconclusive"
        if inconclusive_reason is not None or not condition_met
        else "condition-met"
    )
    workload_claim = f"{tag} の headline 利得そのものを説明したとは言わない。"
    comparison_limitation = (
        "既存 +11.3% は別環境かつ別 ccbench source の値である。"
        if tag == "balanced"
        else f"{tag} の既存比較値は別環境または別 source と交絡しうる。"
    )
    comparison = _comparison_receipt()
    payload = {
        "workload": workload,
        "tag": tag,
        "threads": THREADS,
        "records": RECORDS,
        "site": runtime.site,
        "contract_sha256": runtime.contract_sha256,
        "calibration_ref": runtime.calibration_ref,
        "calibration_sha256": runtime.calibration_sha256,
        "hostname": runtime.hostname,
        "pbs_jobid": runtime.pbs_jobid,
        "ccbench_commit": runtime.ccbench_commit,
        "gflags_pin": runtime.gflags_pin,
        "glog_pin": runtime.glog_pin,
        "dependency_prefix": runtime.dependency_prefix,
        "build_cache_root": runtime.build_cache_root,
        "dependency_build_log": runtime.dependency_build_log,
        "perf_executable": runtime.profiler_executable,
        "clocks_per_us": runtime.clocks_per_us,
        "env_tag": env_tag,
        "use_perf": True,
        "diagnostic_only": True,
        "headline_eligible": False,
        "diagnostic_notice": D20_DIAGNOSTIC_NOTICE,
        "backoff_time_live_verified": False,
        "backoff_time_notice": BACKOFF_TIME_NOTICE,
        "dependency_prefix_cache_identity_bound": False,
        "dependency_identity_notice": DEPENDENCY_IDENTITY_NOTICE,
        "comparison": comparison,
        "comparison_confounds": ["environment", "ccbench_commit"],
        "preregistered_decision": {
            "evaluation_band": "backoff_us <= 10",
            "evaluation_band_source": "existing write-heavy profile",
            "spread_definition": "(max - min) / mean",
            "replication_bar": 0.044,
            "claim_condition": (
                "spread(useful_ipc,S) <= spread(total_ipc,S) and "
                "spread(useful_ipc,S) <= 0.044"
            ),
            "inconclusive_if_condition_not_met": True,
            "headline_gain_explained": False,
        },
        "decision": {
            "status": decision_status,
            "inconclusive_reason": inconclusive_reason,
            "useful_ipc_spread": useful_band_spread,
            "total_ipc_spread": total_band_spread,
            "spin_dilution_condition_met": (
                condition_met if inconclusive_reason is None else None
            ),
            "headline_gain_explained": False,
        },
        "remaining_limitations": [
            comparison_limitation,
            "BACKOFF_NOINLINE=1 の診断 build は headline に使えない。",
            "同一 env/source の stock-inline 対照をこの wave では取らない。",
            BACKOFF_TIME_NOTICE,
            DEPENDENCY_IDENTITY_NOTICE,
        ],
        "rows": rows,
    }
    verdict = (
        f"評価帯が不完全なため判定を出さない。inconclusive: {inconclusive_reason}"
        if inconclusive_reason is not None
        else (
            f"事前登録した判定2の条件を満たす。{tag} の total IPC 低下は "
            "spin 希釈で説明できる。"
            if condition_met
            else "この走では事前登録した判定2に到達しない。"
                 "反証ではなく inconclusive とする。"
        )
    )
    lines = [
        f"# backoff profile — {env_tag} / {tag} ({workload_name})",
        "",
        f"> {D20_DIAGNOSTIC_NOTICE}",
        "",
        "## provenance と限界",
        "",
        f"- site: `{runtime.site}`",
        f"- contract_sha256: `{runtime.contract_sha256}`",
        f"- calibration_ref: `{runtime.calibration_ref}`",
        f"- calibration_sha256: `{runtime.calibration_sha256}`",
        f"- hostname: `{runtime.hostname}`",
        f"- pbs_jobid: `{runtime.pbs_jobid}`",
        f"- ccbench_commit: `{runtime.ccbench_commit}`",
        f"- gflags_pin: `{runtime.gflags_pin}`",
        f"- glog_pin: `{runtime.glog_pin}`",
        f"- dependency_prefix: `{runtime.dependency_prefix}`",
        f"- build_cache_root: `{runtime.build_cache_root}`",
        f"- dependency_build_log: `{runtime.dependency_build_log}`",
        f"- perf_executable: `{runtime.profiler_executable}`",
        f"- clocks_per_us: `{runtime.clocks_per_us}`",
        f"- comparison: `{comparison['path']}` sha256 `{comparison['sha256']}`",
        "- comparison_confounds: `environment`, `ccbench_commit`",
        f"- backoff_time_live_verified: `false` — {BACKOFF_TIME_NOTICE}",
        "- dependency_prefix_cache_identity_bound: `false` — "
        f"{DEPENDENCY_IDENTITY_NOTICE}",
        "",
        "## 事前登録した判定",
        "",
        "- 評価帯 S: `backoff_us <= 10`。既存 write-heavy 成果物から固定し、この実測から選ばない。",
        "- 散布: `(max - min) / mean`。replication bar は `0.044`。",
        f"- total_ipc の散布 (S) = **{_format_spread(total_band_spread)}**",
        f"- useful_ipc の散布 (S) = **{_format_spread(useful_band_spread)}**",
        f"- 判定: {verdict}",
        f"- {workload_claim}",
        "",
        "## 有用 IPC と spin",
        "",
        f"- total_ipc の散布 (全域) = **{_format_spread(_spread(total_all))}**",
        f"- useful_ipc の散布 (全域) = **{_format_spread(_spread(useful_all))}**",
        "",
        "| backoff us | tps (median) | abort% | spin cyc% | spin instr% | "
        "total IPC | useful IPC | K_total | K_useful |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['backoff_us']}{'(none)' if row['is_none'] else ''} | "
            f"{row['tps_median']:,.0f} | {row['abort'] * 100:.1f} | "
            f"{row['spin_cyc_pct']:.1f} | {row['spin_instr_pct']:.1f} | "
            f"{row['total_ipc']:.3f} | {row['useful_ipc']:.3f} | "
            f"{(row['k_total'] or 0):,.0f} | {(row['k_useful'] or 0):,.0f} |"
        )
    lines += [
        "",
        "残るもの: 既存値との環境/source 交絡、同一 env/source の stock-inline 対照、"
        "実効 TSC の live 検証、dependency prefix の cache identity 束縛。",
        "",
        f"> {D20_DIAGNOSTIC_NOTICE}",
        "",
    ]
    json_text = json.dumps(payload, indent=2, ensure_ascii=False)
    markdown_text = "\n".join(lines)
    final_json = Path(stem + ".json")
    final_md = Path(stem + ".md")
    staging = Path(tempfile.mkdtemp(prefix=f".{Path(stem).name}.", dir=out_dir))
    staged_json = staging / final_json.name
    staged_md = staging / final_md.name
    try:
        staged_json.write_text(json_text, encoding="utf-8")
        staged_md.write_text(markdown_text, encoding="utf-8")
        _publish_pair(staged_json, staged_md, final_json, final_md)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    log(
        f"  wrote {stem}.json / .md  "
        f"(useful_ipc 散布 {_format_spread(_spread(useful_all))} vs "
        f"total_ipc {_format_spread(_spread(total_all))})"
    )
    return str(final_json)


def main(argv):
    sel = argv[1] if len(argv) > 1 else "write-heavy"
    points = POINTS if sel == "all" else [point for point in POINTS if point[0] == sel]
    if not points:
        print(f"unknown point: {sel} (選択肢: {[point[0] for point in POINTS]} / all)")
        return 2

    site, contract, _authorization = resolve_site_runtime()
    loaded = _assert_matches_calibration(contract)
    runtime = _build_profile_runtime(site, contract, loaded, _load_policy_document())
    _assert_single_tenant()

    measured = []
    for tag, workload in points:
        measured.append((tag, workload, profile_workload(
            tag, workload, runtime=runtime,
        )))
    for tag, workload, rows in measured:
        _write_out(tag, workload, rows, runtime.env_tag, runtime)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
