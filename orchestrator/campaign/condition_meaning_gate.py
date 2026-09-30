# -*- coding: utf-8 -*-
"""Call-scoped define supply/effectuation and bounded meaning gates.

The generic API produces two independent terminal records.  The supply arm
configures a real target and preprocesses its owner TU from the emitted compile
command.  The meaning arm evaluates a declared witness, or records that no
witness is established.  The older BACKOFF_FIXED assertions remain as strict
compatibility wrappers for the F707/F718 contracts.
The two arms may share an immutable pair of configured owner-TU commands, but
never share a verdict, evidence record, or reason code.

Claim boundary: the supply domain contains the 75 patch-derived defines.  The
legacy runtime-meaning witness remains exclusive to ``BACKOFF_FIXED``.  Fifty-seven
registered macros additionally have a bounded compile-time witness: it
preprocesses an instrumented copy of the complete owner TU with the real
compile-command context and proves that the declared conditional selects its
guarded branches for value 1 and omits them for value 0 (or an undefined
contrast for declared #ifdef witnesses).  It
does not prove the branch body's semantics, dynamic reachability, an expected
runtime anomaly, or correctness.  Supply preprocessing separately proves that
a define changes the selected owner TU's compile-command input.
A declared multi-site witness observes exactly the N verbatim directive lines
its DefineSpec patch adds; conditionals added by overlay patches (for example
the diagnostic composite ``#if BACKOFF_TRIGGER_GATING && TRACE``) and ``#ifndef``
supply guards are outside the claim.
Companion-file evidence is limited to the declared owner TU and the current
configure's include context; it makes no claim about other TUs using the header.
``driver_integration`` on the legacy evidence remains ``"none"``.
Compiler and CMake path snapshots narrow identity drift around invocations,
but do not attest a same-UID adversarial process, delegated processes, the
network, or a sandbox.
"""
from __future__ import annotations

import argparse
import contextlib
import dataclasses
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import stat
import struct
import subprocess
import tempfile
from dataclasses import dataclass, field
from itertools import zip_longest
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Iterator, Mapping, Sequence

from . import source_digest
from .evolve_block import extract_materialized_evolve_block
from .model import Genome


ROUTE_CMAKE_CACHE = "cmake-cache-option"
ROUTE_CMAKE_CXX_FLAGS = "cmake-cxx-flags"


@dataclass(frozen=True, slots=True)
class DefineSpec:
    """Patch-derived interface declaration, independent of mapping success."""

    route: str
    owner_tus: tuple[str, ...]
    target: str
    patch_rel: str
    companion_defines: tuple[tuple[str, str], ...] = ()
    inert_values: tuple[str, ...] = ()


_SILO_OWNER = ("cc/silo/transaction.cc",)
_SS2PL_OWNER = ("cc/ss2pl/transaction.cc",)
_MOCC_OWNER = ("cc/mocc/transaction.cc",)
_SI_OWNER = ("cc/si/transaction.cc",)
_CICADA_OWNER = ("cc/cicada/transaction.cc",)
_CICADA_YCSB_OWNER = ("cc/cicada/ycsb_cicada.cc",)
_DEFINE_SPECS = {
    "IZANAGI_CICADA_RO_GCFLAG": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_OWNER, "ycsb_cicada.exe",
        "patches/cicada-ro-gcflag-variant.patch", inert_values=("0",),
    ),
    "IZANAGI_CICADA_RO_GCFLAG_COUNT": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_OWNER, "ycsb_cicada.exe",
        "patches/cicada-ro-gcflag-variant.patch",
        companion_defines=(("IZANAGI_CICADA_RO_GCFLAG", "1"),), inert_values=("0",),
    ),
    "IZANAGI_CICADA_ROGC_WORKLOAD": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_YCSB_OWNER, "ycsb_cicada.exe",
        "patches/cicada-ro-gcflag-workload.patch", inert_values=("0",),
    ),
    "IZANAGI_CICADA_VLIFE": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_OWNER, "ycsb_cicada.exe",
        "patches/instr-cicada-version-lifetime.patch", inert_values=("0",),
    ),
    "IZANAGI_CICADA_LONGTX": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_OWNER, "ycsb_cicada.exe",
        "patches/instr-cicada-version-lifetime.patch", inert_values=("0",),
    ),
    "SILO_POLICY_VARIANT": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/silo-function-policy-variant.patch",
        inert_values=("0",),
    ),
    "IZANAGI_SILO_POLICY_PROBE": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/instr-silo-function-policy-probe.patch",
    ),
    "IZANAGI_BREAK_SILO_POLICY": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-policy-no-commit-hook.patch",
    ),
    "BACKOFF_FIXED": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/silo-backoff-fixed.patch",
        inert_values=("-1",),
    ),
    "BACKOFF_INCR_MILLI": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/cicada-adaptive-params.patch",
        inert_values=("100000",),
    ),
    "BACKOFF_MAX_US": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/cicada-adaptive-params.patch",
        inert_values=("1000",),
    ),
    "BACKOFF_COUNT_WINDOW": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/cicada-adaptive-dynamic.patch",
        inert_values=("0",),
    ),
    "BACKOFF_COUNT_CAP_US": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/cicada-adaptive-dynamic.patch",
        inert_values=(),
    ),
    "BACKOFF_STEP_ADAPT": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/cicada-adaptive-dynamic.patch",
        inert_values=("0",),
    ),
    "BACKOFF_STEP_MIN_MILLI": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/cicada-adaptive-dynamic.patch",
        inert_values=(),
    ),
    "BACKOFF_STEP_MAX_MILLI": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/cicada-adaptive-dynamic.patch",
        inert_values=(),
    ),
    "BACKOFF_DYN_CEILING": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/cicada-adaptive-dynamic.patch",
        inert_values=("0",),
    ),
    "BACKOFF_TRACE": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/cicada-adaptive-dynamic.patch",
        inert_values=("0",),
    ),
    "BACKOFF_TRACE_TERMINAL_US": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/cicada-adaptive-counterfactual.patch",
        inert_values=("0",),
    ),
    "BACKOFF_STEP_POLICY": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/cicada-adaptive-counterfactual.patch",
        inert_values=("0",),
    ),
    "BACKOFF_STEP_POLICY_SEED": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/cicada-adaptive-counterfactual.patch",
        inert_values=(),
    ),
    "BACKOFF_NOINLINE": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/silo-backoff-fixed.patch",
    ),
    "BACKOFF_REQUESTED_US": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/silo-backoff-requested-us.patch",
    ),
    "BACKOFF_TRIGGER_GATING": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/silo-backoff-trigger-gating-variant.patch",
    ),
    "BACKOFF_UPDATE_US": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/cicada-adaptive-params.patch",
        inert_values=("10",),
    ),
    "MOCC_TEMP_PREDICATE": DefineSpec(
        ROUTE_CMAKE_CACHE, _MOCC_OWNER, "ycsb_mocc.exe",
        "patches/mocc-temperature-predicate-variant.patch",
        inert_values=("0",),
    ),
    "SORT_VARIANT": DefineSpec(
        ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe",
        "patches/silo-sort-variant.patch",
    ),
    "SS2PL_LOCK_IMPL": DefineSpec(
        ROUTE_CMAKE_CACHE, _SS2PL_OWNER, "ycsb_ss2pl.exe",
        "patches/ss2pl-lock-protocol-study.patch",
    ),
    "SS2PL_LOCK_KIND": DefineSpec(
        ROUTE_CMAKE_CACHE, _SS2PL_OWNER, "ycsb_ss2pl.exe",
        "patches/ss2pl-lock-protocol-study.patch",
        (("SS2PL_LOCK_IMPL", "1"),),
    ),
    "SS2PL_DLR": DefineSpec(
        ROUTE_CMAKE_CACHE, _SS2PL_OWNER, "ycsb_ss2pl.exe",
        "patches/ss2pl-lock-protocol-study.patch",
    ),
    "SS2PL_WFG_DIAG": DefineSpec(
        ROUTE_CMAKE_CACHE, _SS2PL_OWNER, "ycsb_ss2pl.exe",
        "patches/ss2pl-lock-protocol-study.patch",
    ),
    "IZANAGI_BREAK_PERMUTATION": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-permutation-erase.patch",
    ),
    "IZANAGI_BREAK_PERMUTATION_SWAP": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-permutation-swap.patch",
    ),
    "IZANAGI_BREAK_LOCK_COVERAGE": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-lockskip-validation.patch",
    ),
    "IZANAGI_BREAK_EARLY_UNLOCK": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-early-unlock-validation.patch",
    ),
    "IZANAGI_BREAK_MOCC_LOCK_COVERAGE": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _MOCC_OWNER, "ycsb_mocc.exe",
        "patches/broken-mocc-lockskip-validation.patch",
    ),
    "IZANAGI_BREAK_MOCC_PERMUTATION": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _MOCC_OWNER, "ycsb_mocc.exe",
        "patches/broken-mocc-permutation-erase.patch",
    ),
    "IZANAGI_BREAK_MOCC_EARLY_UNLOCK": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _MOCC_OWNER, "ycsb_mocc.exe",
        "patches/broken-mocc-early-unlock.patch",
    ),
    "IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _MOCC_OWNER, "ycsb_mocc.exe",
        "patches/broken-mocc-hot-update-unlock.patch",
    ),
    "IZANAGI_BREAK_MOCC_SKIP_CANONICAL_RESTORE": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _MOCC_OWNER, "ycsb_mocc.exe",
        "patches/broken-mocc-skip-canonical-restore.patch",
    ),
    "IZANAGI_BREAK_MOCC_NEGATED_TEMPERATURE_PREDICATE": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _MOCC_OWNER, "ycsb_mocc.exe",
        "patches/control-mocc-negated-temperature-predicate.patch",
    ),
    "IZANAGI_BREAK_SI_FIRST_UPDATER_WINS": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SI_OWNER, "ycsb_si.exe",
        "patches/broken-si-first-updater-wins.patch",
    ),
    "IZANAGI_BREAK_SI_READ_UNCOMMITTED_VERSION": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SI_OWNER, "ycsb_si.exe",
        "patches/broken-si-read-uncommitted-version.patch",
    ),
    "CICADA_FWD_ENABLE": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_OWNER, "ycsb_cicada.exe",
        "patches/cicada-forwarding-variant.patch",
    ),
    "CICADA_VHASH_K": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_OWNER, "ycsb_cicada.exe",
        "patches/cicada-vhash-hot-block-variant.patch",
    ),
    "CICADA_VHASH_COUNT": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_OWNER, "ycsb_cicada.exe",
        "patches/cicada-vhash-hot-block-variant.patch",
        companion_defines=(("CICADA_VHASH_K", "1"),),
    ),
    "CICADA_VHASH_WL": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_OWNER, "ycsb_cicada.exe",
        "patches/cicada-vhash-hot-block-variant.patch",
    ),
    "CICADA_FWD_COUNT": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_OWNER, "ycsb_cicada.exe",
        "patches/cicada-forwarding-variant.patch",
        companion_defines=(("CICADA_FWD_ENABLE", "1"),),
    ),
    "CICADA_LONGTX": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_YCSB_OWNER, "ycsb_cicada.exe",
        "patches/cicada-forwarding-variant.patch",
    ),
    "CICADA_GC_SAFEPOINT": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_OWNER, "ycsb_cicada.exe",
        "patches/cicada-forwarding-gc.patch",
        companion_defines=(("CICADA_FWD_ENABLE", "1"),),
    ),
    "CICADA_GC_WAIT": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_YCSB_OWNER, "ycsb_cicada.exe",
        "patches/cicada-forwarding-gc.patch",
        companion_defines=(("CICADA_GC_SAFEPOINT", "1"),
                           ("CICADA_FWD_ENABLE", "1"), ("CICADA_LONGTX", "1")),
    ),
    "CICADA_GC_COUNT": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _CICADA_OWNER, "ycsb_cicada.exe",
        "patches/cicada-forwarding-gc.patch",
    ),
    "IZANAGI_BREAK_NOREAD_VALIDATION": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-norw-validation.patch",
    ),
    "IZANAGI_BREAK_HIGHKEY_VALIDATION": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-highkey-validation.patch",
    ),
    "IZANAGI_BREAK_WRITE_INTENT_ERASE": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-write-intent-erase.patch",
    ),
    "IZANAGI_BREAK_WRITE_INTENT_FORGE": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-write-intent-forge.patch",
    ),
    "IZANAGI_BREAK_WRITE_INTENT_OPSWAP": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-write-intent-opswap.patch",
    ),
    "IZANAGI_BREAK_WRITE_INTENT_PTRSWAP": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-write-intent-ptrswap.patch",
    ),
    "IZANAGI_BREAK_TRIGGER_MISATTR": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-trigger-misattr.patch",
    ),
    "IZANAGI_BREAK_READ_LOCK_CHECK": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-read-lock-check.patch",
    ),
    "IZANAGI_BREAK_NO_WRITE_TID_MAX": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-no-write-tid-max.patch",
    ),
    "IZANAGI_BREAK_FIXED_COMMIT_VERSION": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-fixed-commit-version.patch",
    ),
    "IZANAGI_BREAK_PUBLISHED_VERSION_MISMATCH": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-published-version-mismatch.patch",
    ),
    "IZANAGI_BREAK_TAIL_COMMIT_OMISSION": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-tail-commit-omission.patch",
    ),
    "IZANAGI_BREAK_NO_READ_TID_MAX": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-no-read-tid-max.patch",
    ),
    "IZANAGI_BREAK_STALE_READ_PAYLOAD": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-stale-read-payload.patch",
    ),
    "IZANAGI_BREAK_CORRUPT_WRITE_PAYLOAD": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-corrupt-write-payload.patch",
    ),
    "IZANAGI_BREAK_SKIP_NODE_VALIDATION": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-skip-node-validation.patch",
    ),
    "IZANAGI_BREAK_STALE_READ_OWN_WRITE": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-stale-read-own-write.patch",
    ),
    "IZANAGI_BREAK_REPEAT_UPDATE_BUFFER": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/broken-silo-repeat-update-buffer.patch",
    ),
    "IZANAGI_BREAK_DOUBLE_ABORT_BACKOFF": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/control-silo-double-abort-backoff.patch",
    ),
    "IZANAGI_BREAK_REVERSE_WRITE_ORDER": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/control-silo-reverse-write-order.patch",
    ),
    "IZANAGI_BREAK_CONSERVATIVE_ABORT": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/control-silo-conservative-abort.patch",
    ),
    "IZANAGI_SILO_LADDER_RUNG1": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe",
        "patches/silo_ladder_rung1.patch",
    ),
    "IZANAGI_SILO_LADDER_RUNG1_REPORT": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, ("cc/silo/ycsb_silo.cc",), "ycsb_silo.exe",
        "patches/silo_ladder_rung1.patch",
        (("IZANAGI_SILO_LADDER_RUNG1", "1"),),
    ),
}
DEFINE_SPECS: Mapping[str, DefineSpec] = MappingProxyType(_DEFINE_SPECS)
_MOCC_BACKOFF_SPEC = DefineSpec(
    ROUTE_CMAKE_CACHE, _MOCC_OWNER, "ycsb_mocc.exe",
    "patches/silo-backoff-fixed.patch", inert_values=("-1",),
)


def _request_spec(request: DefineRequest) -> DefineSpec:
    if request.macro == "BACKOFF_FIXED" and request.owner_tu in _MOCC_OWNER:
        return _MOCC_BACKOFF_SPEC
    return DEFINE_SPECS[request.macro]
SUPPLY_DOMAIN_MACROS = frozenset(DEFINE_SPECS)
_CONDITIONAL_BRANCH_WITNESSES = {
    "IZANAGI_CICADA_RO_GCFLAG": (
        "cc/cicada/transaction.cc", "#if IZANAGI_CICADA_RO_GCFLAG",
    ),
    "IZANAGI_CICADA_RO_GCFLAG_COUNT": (
        "cc/cicada/transaction.cc", "#if IZANAGI_CICADA_RO_GCFLAG_COUNT",
    ),
    "IZANAGI_CICADA_ROGC_WORKLOAD": (
        "cc/cicada/ycsb_cicada.cc", "#if IZANAGI_CICADA_ROGC_WORKLOAD",
    ),
    "IZANAGI_CICADA_VLIFE": (
        "cc/cicada/transaction.cc", "#if IZANAGI_CICADA_VLIFE",
    ),
    "IZANAGI_CICADA_LONGTX": (
        "cc/cicada/transaction.cc", "#if IZANAGI_CICADA_LONGTX",
    ),
    "SILO_POLICY_VARIANT": (
        "cc/silo/transaction.cc", "#if SILO_POLICY_VARIANT",
    ),
    "IZANAGI_SILO_POLICY_PROBE": (
        "cc/silo/transaction.cc", "#if IZANAGI_SILO_POLICY_PROBE",
    ),
    "IZANAGI_BREAK_SILO_POLICY": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_SILO_POLICY",
    ),
    "BACKOFF_NOINLINE": (
        "include/backoff.hh", "#if BACKOFF_NOINLINE",
    ),
    "IZANAGI_BREAK_PERMUTATION": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_PERMUTATION",
    ),
    "IZANAGI_BREAK_PERMUTATION_SWAP": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_PERMUTATION_SWAP",
    ),
    "IZANAGI_BREAK_LOCK_COVERAGE": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_LOCK_COVERAGE",
    ),
    "IZANAGI_BREAK_EARLY_UNLOCK": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_EARLY_UNLOCK",
    ),
    "IZANAGI_BREAK_MOCC_LOCK_COVERAGE": (
        "cc/mocc/transaction.cc", "#if IZANAGI_BREAK_MOCC_LOCK_COVERAGE",
    ),
    "IZANAGI_BREAK_MOCC_PERMUTATION": (
        "cc/mocc/transaction.cc", "#if IZANAGI_BREAK_MOCC_PERMUTATION",
    ),
    "IZANAGI_BREAK_MOCC_EARLY_UNLOCK": (
        "cc/mocc/transaction.cc", "#if IZANAGI_BREAK_MOCC_EARLY_UNLOCK",
    ),
    "IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK": (
        "cc/mocc/transaction.cc", "#if IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK",
    ),
    "IZANAGI_BREAK_MOCC_SKIP_CANONICAL_RESTORE": (
        "cc/mocc/transaction.cc", "#if IZANAGI_BREAK_MOCC_SKIP_CANONICAL_RESTORE",
    ),
    "IZANAGI_BREAK_MOCC_NEGATED_TEMPERATURE_PREDICATE": (
        "cc/mocc/transaction.cc", "#if IZANAGI_BREAK_MOCC_NEGATED_TEMPERATURE_PREDICATE",
    ),
    "IZANAGI_BREAK_SI_FIRST_UPDATER_WINS": (
        "cc/si/transaction.cc", "#if IZANAGI_BREAK_SI_FIRST_UPDATER_WINS",
    ),
    "IZANAGI_BREAK_SI_READ_UNCOMMITTED_VERSION": (
        "cc/si/transaction.cc", "#if IZANAGI_BREAK_SI_READ_UNCOMMITTED_VERSION",
    ),
    "CICADA_FWD_ENABLE": (
        "cc/cicada/transaction.cc", "#if CICADA_FWD_ENABLE",
    ),
    "CICADA_VHASH_K": (
        "cc/cicada/transaction.cc", "#if CICADA_VHASH_K",
    ),
    "CICADA_VHASH_COUNT": (
        "cc/cicada/transaction.cc", "#if CICADA_VHASH_COUNT",
    ),
    "CICADA_VHASH_WL": (
        "cc/cicada/transaction.cc", "#if CICADA_VHASH_WL",
    ),
    "CICADA_FWD_COUNT": (
        "cc/cicada/transaction.cc", "#if CICADA_FWD_COUNT",
    ),
    "CICADA_LONGTX": (
        "cc/cicada/ycsb_cicada.cc", "#if CICADA_LONGTX",
    ),
    "CICADA_GC_SAFEPOINT": (
        "cc/cicada/transaction.cc", "#if CICADA_GC_SAFEPOINT",
    ),
    "CICADA_GC_WAIT": (
        "cc/cicada/ycsb_cicada.cc", "#if CICADA_GC_WAIT",
    ),
    "CICADA_GC_COUNT": (
        "cc/cicada/transaction.cc", "#if CICADA_GC_COUNT",
    ),
    "IZANAGI_BREAK_WRITE_INTENT_ERASE": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_WRITE_INTENT_ERASE",
    ),
    "IZANAGI_BREAK_WRITE_INTENT_FORGE": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_WRITE_INTENT_FORGE",
    ),
    "IZANAGI_BREAK_WRITE_INTENT_OPSWAP": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_WRITE_INTENT_OPSWAP",
    ),
    "IZANAGI_BREAK_WRITE_INTENT_PTRSWAP": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_WRITE_INTENT_PTRSWAP",
    ),
    "IZANAGI_BREAK_NOREAD_VALIDATION": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_NOREAD_VALIDATION",
    ),
    "IZANAGI_BREAK_HIGHKEY_VALIDATION": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_HIGHKEY_VALIDATION",
    ),
    "MOCC_TEMP_PREDICATE": (
        "cc/mocc/transaction.cc", "#if MOCC_TEMP_PREDICATE // file-scope helper",
    ),
    "SORT_VARIANT": (
        "cc/silo/transaction.cc", "#if SORT_VARIANT",
    ),
    "IZANAGI_SILO_LADDER_RUNG1_REPORT": (
        "cc/silo/ycsb_silo.cc",
        "#if IZANAGI_SILO_LADDER_RUNG1 && IZANAGI_SILO_LADDER_RUNG1_REPORT",
    ),
    "IZANAGI_BREAK_TRIGGER_MISATTR": (
        "cc/silo/transaction.cc", "#ifdef IZANAGI_BREAK_TRIGGER_MISATTR",
    ),
    "IZANAGI_BREAK_READ_LOCK_CHECK": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_READ_LOCK_CHECK",
    ),
    "IZANAGI_BREAK_NO_WRITE_TID_MAX": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_NO_WRITE_TID_MAX",
    ),
    "IZANAGI_BREAK_FIXED_COMMIT_VERSION": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_FIXED_COMMIT_VERSION",
    ),
    "IZANAGI_BREAK_PUBLISHED_VERSION_MISMATCH": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_PUBLISHED_VERSION_MISMATCH",
    ),
    "IZANAGI_BREAK_TAIL_COMMIT_OMISSION": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_TAIL_COMMIT_OMISSION",
    ),
    "IZANAGI_BREAK_NO_READ_TID_MAX": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_NO_READ_TID_MAX",
    ),
    "IZANAGI_BREAK_STALE_READ_PAYLOAD": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_STALE_READ_PAYLOAD",
    ),
    "IZANAGI_BREAK_CORRUPT_WRITE_PAYLOAD": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_CORRUPT_WRITE_PAYLOAD",
    ),
    "IZANAGI_BREAK_SKIP_NODE_VALIDATION": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_SKIP_NODE_VALIDATION",
    ),
    "IZANAGI_BREAK_STALE_READ_OWN_WRITE": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_STALE_READ_OWN_WRITE",
    ),
    "IZANAGI_BREAK_REPEAT_UPDATE_BUFFER": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_REPEAT_UPDATE_BUFFER",
    ),
    "IZANAGI_BREAK_DOUBLE_ABORT_BACKOFF": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_DOUBLE_ABORT_BACKOFF",
    ),
    "IZANAGI_BREAK_REVERSE_WRITE_ORDER": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_REVERSE_WRITE_ORDER",
    ),
    "IZANAGI_BREAK_CONSERVATIVE_ABORT": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_CONSERVATIVE_ABORT",
    ),
    "IZANAGI_SILO_LADDER_RUNG1": (
        "cc/silo/transaction.cc", "#if IZANAGI_SILO_LADDER_RUNG1",
    ),
    "BACKOFF_TRIGGER_GATING": (
        "cc/silo/transaction.cc", "#if BACKOFF_TRIGGER_GATING",
    ),
    "BACKOFF_REQUESTED_US": (
        "cc/silo/transaction.cc", "#if BACKOFF_REQUESTED_US",
    ),
}
_CONDITIONAL_BRANCH_SITE_COUNTS = {
    "IZANAGI_CICADA_VLIFE": 44,
    "IZANAGI_CICADA_LONGTX": 3,
    "SILO_POLICY_VARIANT": 15,
    "IZANAGI_SILO_POLICY_PROBE": 21,
    "IZANAGI_SILO_LADDER_RUNG1": 2,
    "BACKOFF_TRIGGER_GATING": 12,
    "BACKOFF_REQUESTED_US": 2,
    "IZANAGI_BREAK_READ_LOCK_CHECK": 4,
    "IZANAGI_BREAK_NO_WRITE_TID_MAX": 5,
    "IZANAGI_BREAK_FIXED_COMMIT_VERSION": 4,
    "IZANAGI_BREAK_PUBLISHED_VERSION_MISMATCH": 4,
    "IZANAGI_BREAK_TAIL_COMMIT_OMISSION": 3,
    "IZANAGI_BREAK_NO_READ_TID_MAX": 5,
    "IZANAGI_BREAK_STALE_READ_PAYLOAD": 4,
    "IZANAGI_BREAK_CORRUPT_WRITE_PAYLOAD": 4,
    "IZANAGI_BREAK_SKIP_NODE_VALIDATION": 4,
    "IZANAGI_BREAK_STALE_READ_OWN_WRITE": 4,
    "IZANAGI_BREAK_REPEAT_UPDATE_BUFFER": 4,
    "IZANAGI_BREAK_DOUBLE_ABORT_BACKOFF": 4,
    "IZANAGI_BREAK_REVERSE_WRITE_ORDER": 4,
    "IZANAGI_BREAK_CONSERVATIVE_ABORT": 4,
    "IZANAGI_BREAK_MOCC_SKIP_CANONICAL_RESTORE": 5,
    "IZANAGI_BREAK_MOCC_NEGATED_TEMPERATURE_PREDICATE": 9,
    "IZANAGI_BREAK_SI_FIRST_UPDATER_WINS": 7,
    "IZANAGI_BREAK_SI_READ_UNCOMMITTED_VERSION": 5,
    "IZANAGI_CICADA_RO_GCFLAG": 1,
    "IZANAGI_CICADA_RO_GCFLAG_COUNT": 3,
    "IZANAGI_CICADA_ROGC_WORKLOAD": 2,
    "CICADA_FWD_ENABLE": 11,
    "CICADA_VHASH_K": 9,
    "CICADA_VHASH_COUNT": 19,
    "CICADA_VHASH_WL": 4,
    "CICADA_FWD_COUNT": 4,
    "CICADA_LONGTX": 4,
    "CICADA_GC_SAFEPOINT": 3,
    "CICADA_GC_WAIT": 2,
    "CICADA_GC_COUNT": 7,
}
_CONDITIONAL_BRANCH_COMPANION_SITES = {
    "CICADA_VHASH_K": (("cc/cicada/include/tuple.hh", "#if CICADA_VHASH_K", 3),),
    "CICADA_VHASH_COUNT": (("cc/cicada/include/transaction.hh", "#if CICADA_VHASH_COUNT", 1),),
    "CICADA_VHASH_WL": (("cc/cicada/include/transaction.hh", "#if CICADA_VHASH_WL", 1),),
    "IZANAGI_CICADA_ROGC_WORKLOAD": (
        ("include/ycsb.hh", "#if IZANAGI_CICADA_ROGC_WORKLOAD", 7),
    ),
    "IZANAGI_CICADA_VLIFE": (
        ("cc/cicada/include/transaction.hh", "#if IZANAGI_CICADA_VLIFE", 12),
    ),
    "IZANAGI_CICADA_LONGTX": (),
    "BACKOFF_REQUESTED_US": (("include/backoff.hh", "#if BACKOFF_REQUESTED_US", 2),),
}


def _declared_site_count(macro: str) -> int:
    return _CONDITIONAL_BRANCH_SITE_COUNTS.get(macro, 1)


def _declared_branch_files(macro: str) -> tuple[tuple[str, str, int], ...]:
    source_rel, directive = CONDITIONAL_BRANCH_WITNESSES[macro]
    return (
        (source_rel, directive, _declared_site_count(macro)),
        *_CONDITIONAL_BRANCH_COMPANION_SITES.get(macro, ()),
    )


def _declared_total_site_count(macro: str) -> int:
    return sum(count for _, _, count in _declared_branch_files(macro))


def _declared_contrast_is_undefined(macro: str) -> bool:
    registered = CONDITIONAL_BRANCH_WITNESSES.get(macro)
    return registered is not None and registered[1].startswith("#ifdef ")


CONDITIONAL_BRANCH_WITNESSES: Mapping[str, tuple[str, str]] = MappingProxyType(
    _CONDITIONAL_BRANCH_WITNESSES,
)
MEANING_SUPPORTED_MACROS = frozenset(
    {"BACKOFF_FIXED", *CONDITIONAL_BRANCH_WITNESSES},
)
RELATED_DEFINE_DECODE_MACROS = frozenset({
    "BACKOFF_FIXED", "BACKOFF_NOINLINE", "BACKOFF_REQUESTED_US",
    "MOCC_TEMP_PREDICATE", "BACKOFF_TRIGGER_GATING", "SORT_VARIANT", "SS2PL_LOCK_IMPL",
    "SS2PL_LOCK_KIND", "SS2PL_DLR", "SS2PL_WFG_DIAG",
})
SOURCE_REL = "include/backoff.hh"
OPTIONS_REL = "cmake/Options.cmake"
PROTOCOL = "silo"
PROTOCOL_CMAKE_REL = "cc/silo/CMakeLists.txt"
MARKER_ID = "silo-backoff-magnitude"
MACRO = "BACKOFF_FIXED"
RESULT_IDENTIFIER = "now_backoff"
CONTEXT_STARTS = (1, 2)
PROCESS_TIMEOUT_SECONDS = 120.0
DRIVER_INTEGRATION = "none"
SUPPLY_PROOF_KIND = "cmake-source-owner-resolved-cache-to-tu-define"
MEANING_PROOF_KIND = (
    "compiler-evaluated-captured-applied-source-decoder-standalone-tu-"
    "finite-pointwise-witness"
)
BRANCH_MEANING_PROOF_KIND = (
    "compiler-preprocessed-materialized-conditional-selected-branch-witness"
)
COMPILE_TIME_BRANCH_SELECTION_PROOF_KIND = (
    "compiler-preprocessed-instrumented-owner-tu-declared-compile-time-"
    "conditional-branch-selection-witness"
)
STOCK_ADAPTIVE_BRANCH = "stock-adaptive-backoff"
SYNTHESIZED_BACKOFF_BRANCH = "synthesized-backoff"
_COMPILE_TIME_SELECTED_MARKER = "IZANAGI_COMPILE_TIME_BRANCH_SELECTED"
_COMPILE_TIME_COMPLETED_MARKER = "IZANAGI_COMPILE_TIME_BRANCH_COMPLETED"
_COMPILE_TIME_SELECTED_OUTPUT = "IZANAGI_COMPILE_TIME_BRANCH_SELECTED_OBSERVED"
_COMPILE_TIME_COMPLETED_OUTPUT = "IZANAGI_COMPILE_TIME_BRANCH_COMPLETED_OBSERVED"
_COMPILE_TIME_SITE_SELECTED_MARKER = "IZANAGI_COMPILE_TIME_BRANCH_SITE_SELECTED"
_COMPILE_TIME_SITE_COMPLETED_MARKER = "IZANAGI_COMPILE_TIME_BRANCH_SITE_COMPLETED"
_COMPILE_TIME_SITE_DEFINES = tuple(
    f"-D{marker}(k)={marker}_OBSERVED_##k"
    for marker in (_COMPILE_TIME_SITE_SELECTED_MARKER, _COMPILE_TIME_SITE_COMPLETED_MARKER)
)
_BITS_RE = re.compile(r"[0-9a-f]{16}\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_ROW_RE = re.compile(rb"([0-9]+) ([0-9]+) ([0-9a-f]{16})\Z")


class ConditionMeaningGateError(RuntimeError):
    """Structured fail-closed rejection from exactly one arm."""

    def __init__(
        self,
        reason_code: str,
        detail: str,
        *,
        define_value: int | None = None,
        context_index: int | None = None,
        expected: str | None = None,
        observed: str | None = None,
    ) -> None:
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = reason_code
        self.detail = detail
        self.define_value = define_value
        self.context_index = context_index
        self.expected = expected
        self.observed = observed


@dataclass(frozen=True, slots=True)
class RegularFileIdentity:
    """Portable regular-file identity fields used by capture evidence."""

    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int


@dataclass(frozen=True, slots=True)
class CapturedFileEvidence:
    """Identity and content hash of one input held open during capture."""

    relative_path: str
    before: RegularFileIdentity
    after: RegularFileIdentity
    path_after: RegularFileIdentity
    sha256: str


@dataclass(frozen=True, slots=True)
class CapturedBackoffFixedInputs:
    """One dirfd-anchored read of the three code-owned inputs."""

    root: str
    source_bytes: bytes
    options_text: str
    protocol_cmake_text: str
    source_sha256: str
    options_sha256: str
    protocol_cmake_sha256: str
    input_files: tuple[CapturedFileEvidence, ...]


@dataclass(frozen=True, slots=True)
class SupplyObservation:
    define_value: int
    cache_name: str
    effective_value: str


@dataclass(frozen=True, slots=True)
class SupplyEvidence:
    proof_kind: str
    driver_integration: str
    source_sha256: str
    options_sha256: str
    protocol_cmake_sha256: str
    source_rel: str
    owner_protocol: str
    input_files: tuple[CapturedFileEvidence, ...]
    observations: tuple[SupplyObservation, ...]


@dataclass(frozen=True, slots=True)
class MeaningCase:
    """One pointwise decoder case or one inert selected-branch case."""

    define_value: int
    expected_float64_bits_by_context: tuple[str, str] | None
    expected_selected_branch: str | None = None

    def __post_init__(self) -> None:
        if type(self.define_value) is not int:
            raise ValueError("meaning define value must be an exact integer")
        if self.expected_selected_branch is not None:
            if self.define_value != -1 \
                    or self.expected_float64_bits_by_context is not None \
                    or self.expected_selected_branch != STOCK_ADAPTIVE_BRANCH:
                raise ValueError(
                    "selected-branch meaning is only declared for "
                    "BACKOFF_FIXED=-1 stock adaptive backoff"
                )
            return
        _validate_define_value(self.define_value)
        if type(self.expected_float64_bits_by_context) is not tuple \
                or len(self.expected_float64_bits_by_context) != len(CONTEXT_STARTS):
            raise ValueError("expected bits must be an exact two-item tuple")
        for bits in self.expected_float64_bits_by_context:
            if type(bits) is not str or _BITS_RE.fullmatch(bits) is None:
                raise ValueError("expected float64 bits must be 16 lowercase hex digits")
            if not math.isfinite(_float_from_bits(bits)):
                raise ValueError("expected float64 bits must encode a finite value")


@dataclass(frozen=True, slots=True)
class MeaningObservation:
    define_value: int
    context_index: int
    start: int
    expected_bits: str
    observed_bits: str


@dataclass(frozen=True, slots=True)
class MeaningEvidence:
    """Finite witness evidence with bounded, portable compiler snapshots."""

    proof_kind: str
    driver_integration: str
    source_sha256: str
    options_sha256: str
    protocol_cmake_sha256: str
    hole_sha256: str
    compiler_path: str
    compiler_version: str
    compiler_argv: tuple[str, ...]
    run_argv: tuple[str, ...]
    input_files: tuple[CapturedFileEvidence, ...]
    compiler_identities: tuple["CompilerFileEvidence", ...]
    observations: tuple[MeaningObservation, ...]


@dataclass(frozen=True, slots=True)
class BranchMeaningEvidence:
    """Compiler observation of the branch selected by materialized source."""

    proof_kind: str
    source_sha256: str
    conditional_sha256: str
    stock_branch_sha256: str
    define_value: int
    expected_branch: str
    observed_branch: str
    compiler_path: str
    compiler_version: str
    preprocess_argv: tuple[str, ...]
    compiler_identities: tuple["CompilerFileEvidence", ...]


@dataclass(frozen=True, slots=True)
class CompileTimeBranchSelectionObservation:
    """One requested or default/contrast observation of the declared branch."""

    define_value: str | None
    selected_count: int
    completed_count: int
    preprocess_argv: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompileTimeBranchSelectionEvidence:
    """Bounded owner-TU proof that one preprocessor branch distinguishes 1/0.

    ``requested`` contains the requested-value observation.  ``default``
    contains the default-value observation, or the opposite-value contrast
    when the requested value is itself the default.

    Configure argv fields are the exact outer argv this gate executed; they do
    not claim to observe argv inside a delegating CMake wrapper.
    """

    proof_kind: str
    source_rel: str
    start_directive: str
    source_sha256: str
    source_file: CapturedFileEvidence
    requested: CompileTimeBranchSelectionObservation
    default: CompileTimeBranchSelectionObservation
    compiler_path: str
    compiler_version: str
    compiler_identities: tuple["CompilerFileEvidence", ...]
    cmake_path: str
    requested_configure_argv: tuple[str, ...]
    default_configure_argv: tuple[str, ...]
    requested_cmake_identities: tuple["CMakeFileEvidence", ...]
    default_cmake_identities: tuple["CMakeFileEvidence", ...]


@dataclass(frozen=True, slots=True)
class CompilerFileEvidence:
    """One compiler path identity/hash snapshot at a declared phase."""

    phase: str
    identity: RegularFileIdentity
    sha256: str


@dataclass(frozen=True, slots=True)
class CMakeFileEvidence:
    """One CMake path identity/hash snapshot at a declared phase."""

    phase: str
    identity: RegularFileIdentity
    sha256: str


@dataclass(frozen=True, slots=True)
class CapturedDefineInputs:
    """Stable roots and configure arguments used to collect live evidence."""

    source_root: str
    stock_root: str | None
    configure_args: tuple[str, ...]
    source_root_identity: RegularFileIdentity
    stock_root_identity: RegularFileIdentity | None


@dataclass(frozen=True, slots=True)
class DefineRequest:
    """One driver request against a patch-derived define interface."""

    driver_id: str
    macro: str
    route: str
    requested_value: int | str
    default_value: int | str | None
    owner_tu: str
    target: str
    companion_defines: tuple[tuple[str, int | str], ...] = ()
    stock_comparison: bool = False


@dataclass(frozen=True, slots=True)
class _ConfiguredOwnerCompileCommand:
    """One owner-TU command and the outer configure argv this gate executed."""

    directory: str
    argv: tuple[str, ...]
    owner: str
    source_root: str
    build_root: str
    define_value: str | None
    cmake_path: str
    configure_argv: tuple[str, ...]
    cmake_identities: tuple[CMakeFileEvidence, ...]


@dataclass(frozen=True, slots=True)
class _CMakeConfigureResult:
    """Command database and evidence for the argv this gate executed."""

    commands: tuple[dict[str, Any], ...]
    cmake_path: str
    configure_argv: tuple[str, ...]
    cmake_identities: tuple[CMakeFileEvidence, ...]


@dataclass(frozen=True, slots=True)
class _ConfiguredDefineCompileCommands:
    """Requested/control owner commands shared without sharing an arm verdict."""

    captured: CapturedDefineInputs
    request_digest: str
    compiler_path: str | None
    cmake_path: str | None
    requested: _ConfiguredOwnerCompileCommand | None
    control: _ConfiguredOwnerCompileCommand | None
    failure_reason: str | None = None
    failure_detail: str | None = None
    failure_expected: object | None = None
    failure_observed: object | None = None
    failure_define_value: object | None = None
    failure_context_index: object | None = None
    _issuer_capability: object | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )


@dataclass(frozen=True, slots=True)
class MeaningWitnessDeclaration:
    """Finite runtime-meaning declaration for one meaning-supported macro."""

    macro: str
    cases: tuple[MeaningCase, ...]
    witness_id: str = "backoff-fixed-finite-pointwise"

    def __post_init__(self) -> None:
        if type(self.macro) is not str or self.macro != MACRO:
            raise ValueError("meaning declaration macro has no runtime witness support")
        if type(self.cases) is not tuple \
                or any(type(case) is not MeaningCase for case in self.cases):
            raise ValueError("meaning declaration cases must be an exact tuple of MeaningCase")
        if len({case.define_value for case in self.cases}) != len(self.cases):
            raise ValueError("meaning declaration values must be unique")
        if type(self.witness_id) is not str or not self.witness_id:
            raise ValueError("meaning declaration witness_id must be non-empty")


@dataclass(frozen=True, slots=True)
class ConditionalBranchMeaningDeclaration:
    """Exact declaration of one registry-owned compile-time branch witness."""

    macro: str
    source_rel: str
    start_directive: str
    witness_id: str = "owner-tu-compile-time-conditional-branch-selection"

    def __post_init__(self) -> None:
        if type(self.macro) is not str:
            raise ValueError("conditional branch declaration macro must be an exact string")
        registered = CONDITIONAL_BRANCH_WITNESSES.get(self.macro)
        if registered is None \
                or type(self.source_rel) is not str \
                or type(self.start_directive) is not str \
                or (self.source_rel, self.start_directive) != registered:
            raise ValueError("conditional branch declaration is not registry-owned")
        if type(self.witness_id) is not str or not self.witness_id:
            raise ValueError("conditional branch witness_id must be non-empty")


@dataclass(frozen=True, slots=True)
class ConditionArmRecord:
    """Canonical terminal evidence for exactly one gate arm."""

    record_id: str
    record_digest: str
    arm: str
    terminal_status: str
    reason_code: str
    driver_id: str
    macro: str
    request_digest: str
    evidence: Mapping[str, Any]
    _issuer_capability: object | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
        metadata={"canonical": False},
    )

    def canonical_json(self) -> str:
        return _canonical_json(self)


@dataclass(frozen=True, slots=True)
class ConditionFamilyAdmission:
    """Combined decision that references, but never embeds, arm records."""

    admission_id: str
    admission_digest: str
    use_class: str
    admitted: bool
    record_ids: tuple[str, ...]
    # None means that meaning was not examined.  An empty tuple means that it
    # was examined and every record is established within its proof_kind boundary.
    unestablished_meaning_macros: tuple[str, ...] | None

    def __post_init__(self) -> None:
        names = self.unestablished_meaning_macros
        if names is not None and (
            type(names) is not tuple
            or any(type(name) is not str or name not in SUPPLY_DOMAIN_MACROS
                   for name in names)
            or tuple(sorted(set(names))) != names
        ):
            raise ValueError(
                "unestablished meaning macros must be an exact sorted unique tuple",
            )

    def canonical_json(self) -> str:
        return _canonical_json(self)


@dataclass(frozen=True, slots=True)
class _PreprocessResult:
    """Preprocess result bound to the configure argv this gate executed."""

    preprocessed_bytes: bytes
    digest: str
    byte_length: int
    replay_argv: tuple[str, ...]
    comparable_argv: tuple[str, ...]
    owner_tu: str
    dependency_closure: tuple[tuple[str, str], ...]
    dependency_closure_digest: str
    root_dependent_builtin_paths: tuple[str, ...]
    compiler_path: str
    compiler_version: str
    compiler_identities: tuple[CompilerFileEvidence, ...]
    cmake_path: str
    configure_argv: tuple[str, ...]
    cmake_identities: tuple[CMakeFileEvidence, ...]


def canonical_float64_bits(value: float) -> str:
    """Return canonical lowercase bits for one finite binary64 value."""
    if type(value) is not float or not math.isfinite(value):
        raise ValueError("value must be an exact finite float")
    return struct.pack(">d", value).hex()


def _float_from_bits(bits: str) -> float:
    return struct.unpack(">d", bytes.fromhex(bits))[0]


def _validate_define_value(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("BACKOFF_FIXED must be a non-negative exact integer")
    return value


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file_identity(value: os.stat_result) -> RegularFileIdentity:
    return RegularFileIdentity(
        device=value.st_dev,
        inode=value.st_ino,
        size=value.st_size,
        mtime_ns=value.st_mtime_ns,
        ctime_ns=value.st_ctime_ns,
    )


def _canonical_value(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {
            field.name: _canonical_value(getattr(value, field.name))
            for field in dataclasses.fields(value)
            if field.metadata.get("canonical", True)
        }
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda row: str(row[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, Path):
        return os.fspath(value)
    if value is None or type(value) in {bool, int, float, str}:
        return value
    raise TypeError(f"value is not canonical-JSON encodable: {type(value).__name__}")


def _canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical_value(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    )


def _canonical_digest(value: Any) -> str:
    return _sha256(_canonical_json(value).encode("ascii"))


def _root_identity(root: Path) -> RegularFileIdentity:
    try:
        observed = root.stat()
    except OSError as exc:
        raise ConditionMeaningGateError(
            "input-capture-failed", f"source root is unavailable: {root}",
        ) from exc
    if not stat.S_ISDIR(observed.st_mode):
        raise ConditionMeaningGateError(
            "input-capture-failed", f"source root is not a directory: {root}",
        )
    return _file_identity(observed)


def capture_define_inputs(
    source_root: str | os.PathLike[str],
    *,
    stock_root: str | os.PathLike[str] | None = None,
    configure_args: Sequence[str] = (),
) -> CapturedDefineInputs:
    """Capture real source roots without accepting precomputed witness bytes."""
    if type(configure_args) not in {tuple, list} \
            or any(type(arg) is not str or not arg for arg in configure_args):
        raise ConditionMeaningGateError(
            "input-capture-failed", "configure_args must be non-empty strings",
        )
    cxx_flag_args = [
        arg for arg in configure_args if arg.startswith("-DCMAKE_CXX_FLAGS=")
    ]
    if len(cxx_flag_args) > 1:
        raise ConditionMeaningGateError(
            "input-capture-failed",
            "configure_args contains duplicate CMAKE_CXX_FLAGS values",
        )
    try:
        source = Path(source_root).resolve(strict=True)
        stock = Path(stock_root).resolve(strict=True) if stock_root is not None else None
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise ConditionMeaningGateError(
            "input-capture-failed", "source roots cannot be resolved",
        ) from exc
    source_identity = _root_identity(source)
    stock_identity = _root_identity(stock) if stock is not None else None
    if stock is not None and stock == source:
        raise ConditionMeaningGateError(
            "input-capture-failed", "stock root must be distinct from patched root",
        )
    return CapturedDefineInputs(
        source_root=os.fspath(source),
        stock_root=os.fspath(stock) if stock is not None else None,
        configure_args=tuple(configure_args),
        source_root_identity=source_identity,
        stock_root_identity=stock_identity,
    )


def make_define_request(
    *,
    driver_id: str,
    macro: str,
    requested_value: int | str,
    default_value: int | str | None,
    stock_comparison: bool = False,
    protocol: str = "silo",
) -> DefineRequest:
    """Construct a request from the independently declared 75-macro supply domain."""
    try:
        if protocol not in ("silo", "mocc") or (protocol == "mocc" and macro != "BACKOFF_FIXED"):
            raise KeyError(protocol)
        spec = _MOCC_BACKOFF_SPEC if protocol == "mocc" else DEFINE_SPECS[macro]
    except (KeyError, TypeError) as exc:
        raise ConditionMeaningGateError(
            "request-contract-invalid", f"macro is outside the 75-macro domain: {macro!r}",
        ) from exc
    if len(spec.owner_tus) != 1:
        raise ConditionMeaningGateError(
            "request-contract-invalid", f"macro owner is not unique: {macro}",
        )
    return DefineRequest(
        driver_id=driver_id,
        macro=macro,
        route=spec.route,
        requested_value=requested_value,
        default_value=default_value,
        owner_tu=spec.owner_tus[0],
        target=spec.target,
        companion_defines=spec.companion_defines,
        stock_comparison=stock_comparison,
    )


def _define_scalar(value: object, field: str) -> str:
    if type(value) is int:
        return str(value)
    if type(value) is str and value and not any(character.isspace() for character in value):
        return value
    raise ConditionMeaningGateError(
        "request-contract-invalid", f"{field} must be an exact int or non-space string",
    )


def _effective_companions(request: DefineRequest, spec: DefineSpec) -> tuple[tuple[str, str], ...]:
    combined: dict[str, str] = dict(spec.companion_defines)
    seen: set[str] = set()
    if type(request.companion_defines) is not tuple:
        raise ConditionMeaningGateError(
            "request-contract-invalid", "companion_defines must be an exact tuple",
        )
    for row in request.companion_defines:
        if type(row) is not tuple or len(row) != 2 or type(row[0]) is not str:
            raise ConditionMeaningGateError(
                "request-contract-invalid", "companion define row is invalid",
            )
        if row[0] in seen or row[0] not in combined:
            raise ConditionMeaningGateError(
                "request-contract-invalid",
                f"companion define is duplicate or undeclared: {row[0]}",
            )
        seen.add(row[0])
        value = _define_scalar(row[1], f"companion {row[0]}")
        if row[0] in combined and combined[row[0]] != value:
            raise ConditionMeaningGateError(
                "request-contract-invalid",
                f"required companion {row[0]} must equal {combined[row[0]]}",
            )
        combined[row[0]] = value
    return tuple(sorted(combined.items()))


def _validate_define_request(request: DefineRequest) -> tuple[DefineSpec, str, str | None, tuple[tuple[str, str], ...]]:
    if type(request) is not DefineRequest:
        raise ConditionMeaningGateError(
            "request-contract-invalid", "request has the wrong exact type",
        )
    if type(request.driver_id) is not str or not request.driver_id:
        raise ConditionMeaningGateError(
            "request-contract-invalid", "driver_id must be a non-empty string",
        )
    try:
        spec = _request_spec(request)
    except KeyError as exc:
        raise ConditionMeaningGateError(
            "request-contract-invalid", "macro is outside the 75-macro domain",
        ) from exc
    if request.route != spec.route:
        raise ConditionMeaningGateError(
            "request-contract-invalid", "request route disagrees with patch interface",
        )
    if request.owner_tu not in spec.owner_tus or request.target != spec.target:
        raise ConditionMeaningGateError(
            "request-contract-invalid", "request owner/target disagrees with patch declaration",
        )
    requested = _define_scalar(request.requested_value, "requested_value")
    default = None if request.default_value is None \
        else _define_scalar(request.default_value, "default_value")
    inert = _is_inert_value(spec, requested=requested, default=default)
    if request.stock_comparison and not inert:
        raise ConditionMeaningGateError(
            "request-contract-invalid",
            "stock comparison requires a requested default or declared inert value",
        )
    return spec, requested, default, _effective_companions(request, spec)


def declare_define_runtime_meaning(
    request: DefineRequest,
) -> ConditionalBranchMeaningDeclaration | None:
    """Declare the registry witness only for its exact requested/default pair."""
    spec, requested, default, _companions = _validate_define_request(request)
    registered = CONDITIONAL_BRANCH_WITNESSES.get(request.macro)
    if registered is None:
        return None
    source_rel, start_directive = registered
    if request.macro == "BACKOFF_NOINLINE":
        if requested not in {"0", "1"} or default != "0" \
                or source_rel != "include/backoff.hh":
            return None
    elif _declared_contrast_is_undefined(request.macro):
        if requested != "1" or default is not None or source_rel not in spec.owner_tus:
            return None
    elif requested != "1" or default != "0" \
            or source_rel not in spec.owner_tus:
        return None
    return ConditionalBranchMeaningDeclaration(
        macro=request.macro,
        source_rel=source_rel,
        start_directive=start_directive,
    )


def _is_inert_value(
    spec: DefineSpec,
    *,
    requested: str,
    default: str | None,
) -> bool:
    """Classify only explicit default equality or a spec-declared inert value."""
    return (default is not None and requested == default) \
        or requested in spec.inert_values


def _request_digest(
    request: DefineRequest,
    companions: tuple[tuple[str, str], ...],
) -> str:
    return _canonical_digest({
        "driver_id": request.driver_id,
        "macro": request.macro,
        "route": request.route,
        "requested_value": request.requested_value,
        "default_value": request.default_value,
        "owner_tu": request.owner_tu,
        "target": request.target,
        "companion_defines": companions,
        "stock_comparison": request.stock_comparison,
    })


_RECORD_ISSUER_CAPABILITY = object()
_CONFIGURED_COMMANDS_ISSUER_CAPABILITY = object()


def _arm_record(
    *,
    arm: str,
    terminal_status: str,
    reason_code: str,
    request: DefineRequest,
    request_digest: str,
    evidence: Mapping[str, Any],
) -> ConditionArmRecord:
    """Build canonical public fields without granting evaluator issuance."""
    if arm not in {"supply-effectuation", "runtime-meaning"}:
        raise ValueError("unknown condition gate arm")
    if terminal_status not in {"green", "red", "unestablished"}:
        raise ValueError("unknown terminal status")
    if arm == "supply-effectuation" and terminal_status == "unestablished":
        raise ValueError("supply/effectuation cannot be unestablished")
    payload = {
        "arm": arm,
        "terminal_status": terminal_status,
        "reason_code": reason_code,
        "driver_id": request.driver_id,
        "macro": request.macro,
        "request_digest": request_digest,
        "evidence": evidence,
    }
    digest = _canonical_digest(payload)
    return ConditionArmRecord(
        record_id=f"condition-gate/{arm}/{digest}",
        record_digest=digest,
        arm=arm,
        terminal_status=terminal_status,
        reason_code=reason_code,
        driver_id=request.driver_id,
        macro=request.macro,
        request_digest=request_digest,
        evidence=MappingProxyType(dict(sorted(evidence.items()))),
    )


def _issue_arm_record(
    *,
    arm: str,
    terminal_status: str,
    reason_code: str,
    request: DefineRequest,
    request_digest: str,
    evidence: Mapping[str, Any],
) -> ConditionArmRecord:
    """Issue a record after its complete arm-specific structure is valid.

    The capability is intentionally absent from canonical JSON.  A receipt can
    preserve what an evaluator observed, but deserializing public fields does
    not turn that receipt back into an admissible in-process evaluation result.
    """
    record = _arm_record(
        arm=arm,
        terminal_status=terminal_status,
        reason_code=reason_code,
        request=request,
        request_digest=request_digest,
        evidence=evidence,
    )
    _validate_arm_record_integrity(record, require_issuer=False)
    object.__setattr__(record, "_issuer_capability", _RECORD_ISSUER_CAPABILITY)
    return record


def _nofollow_flags() -> int:
    if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise ConditionMeaningGateError(
            "input-capture-failed",
            "this Python platform cannot enforce dirfd no-symlink capture",
        )
    return getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW


def _open_relative_nofollow(root_descriptor: int, relative: str) -> int:
    """Open a code-owned relative file via no-symlink component traversal."""
    parts = Path(relative).parts
    invalid_component = any(part in {"", ".", ".."} for part in parts)
    if not parts or Path(relative).is_absolute() or invalid_component:
        raise ConditionMeaningGateError(
            "input-capture-failed", f"captured input path is invalid: {relative!r}",
        )
    nofollow = _nofollow_flags()
    current = os.dup(root_descriptor)
    try:
        for component in parts[:-1]:
            following = os.open(
                component, os.O_RDONLY | os.O_DIRECTORY | nofollow, dir_fd=current,
            )
            try:
                opened = os.fstat(following)
            except OSError:
                os.close(following)
                raise
            if not stat.S_ISDIR(opened.st_mode):
                os.close(following)
                raise OSError(f"non-directory path component {component!r}")
            os.close(current)
            current = following
        descriptor = os.open(parts[-1], os.O_RDONLY | nofollow, dir_fd=current)
        try:
            opened = os.fstat(descriptor)
        except OSError:
            os.close(descriptor)
            raise
        if not stat.S_ISREG(opened.st_mode):
            os.close(descriptor)
            raise OSError(f"non-regular captured input {relative!r}")
        return descriptor
    except OSError as exc:
        raise ConditionMeaningGateError(
            "input-capture-failed",
            f"cannot open captured input without symlinks: {relative!r}",
        ) from exc
    finally:
        os.close(current)


def _read_descriptor(
    descriptor: int,
    relative: str,
) -> tuple[bytes, RegularFileIdentity, RegularFileIdentity]:
    try:
        before = _file_identity(os.fstat(descriptor))
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = _file_identity(os.fstat(descriptor))
    except OSError as exc:
        raise ConditionMeaningGateError(
            "input-capture-failed", f"cannot read captured input {relative!r}",
        ) from exc
    value = b"".join(chunks)
    if before != after or len(value) != after.size:
        raise ConditionMeaningGateError(
            "input-capture-failed", f"captured input changed while reading: {relative!r}",
        )
    return value, before, after


def capture_backoff_fixed_inputs(
    ccbench_root: str | os.PathLike[str],
) -> CapturedBackoffFixedInputs:
    """Open all three inputs first, then read them from a no-symlink dirfd walk."""
    root_descriptor: int | None = None
    try:
        root = Path(ccbench_root).resolve(strict=True)
        nofollow = _nofollow_flags()
        root_path_identity = _file_identity(os.stat(root, follow_symlinks=False))
        root_descriptor = os.open(
            root, os.O_RDONLY | os.O_DIRECTORY | nofollow,
        )
        root_fd_identity = _file_identity(os.fstat(root_descriptor))
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        if root_descriptor is not None:
            os.close(root_descriptor)
        raise ConditionMeaningGateError(
            "input-capture-failed", "ccbench root cannot be resolved",
        ) from exc
    if root_path_identity != root_fd_identity:
        os.close(root_descriptor)
        raise ConditionMeaningGateError(
            "input-capture-failed", "ccbench root changed while opening",
        )
    relatives = (SOURCE_REL, OPTIONS_REL, PROTOCOL_CMAKE_REL)
    descriptors: dict[str, int] = {}
    try:
        for relative in relatives:
            descriptors[relative] = _open_relative_nofollow(root_descriptor, relative)
        values: dict[str, bytes] = {}
        files: list[CapturedFileEvidence] = []
        pending: list[tuple[str, bytes, RegularFileIdentity, RegularFileIdentity]] = []
        for relative in relatives:
            value, before, after = _read_descriptor(descriptors[relative], relative)
            pending.append((relative, value, before, after))
        for relative, value, before, after in pending:
            path_descriptor = _open_relative_nofollow(root_descriptor, relative)
            try:
                path_after = _file_identity(os.fstat(path_descriptor))
            finally:
                os.close(path_descriptor)
            if path_after != after:
                raise ConditionMeaningGateError(
                    "input-capture-failed",
                    f"captured input path changed during capture: {relative!r}",
                )
            values[relative] = value
            files.append(CapturedFileEvidence(
                relative_path=relative,
                before=before,
                after=after,
                path_after=path_after,
                sha256=_sha256(value),
            ))
        if _file_identity(os.stat(root, follow_symlinks=False)) != root_fd_identity:
            raise ConditionMeaningGateError(
                "input-capture-failed", "ccbench root path changed during capture",
            )
    except ConditionMeaningGateError:
        raise
    except OSError as exc:
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured input namespace changed during capture",
        ) from exc
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(root_descriptor)

    source_bytes = values[SOURCE_REL]
    options_bytes = values[OPTIONS_REL]
    protocol_bytes = values[PROTOCOL_CMAKE_REL]
    try:
        options_text = options_bytes.decode("utf-8")
        protocol_text = protocol_bytes.decode("utf-8")
        source_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured inputs must be UTF-8",
        ) from exc
    return CapturedBackoffFixedInputs(
        root=os.fspath(root),
        source_bytes=source_bytes,
        options_text=options_text,
        protocol_cmake_text=protocol_text,
        source_sha256=_sha256(source_bytes),
        options_sha256=_sha256(options_bytes),
        protocol_cmake_sha256=_sha256(protocol_bytes),
        input_files=tuple(files),
    )


def _requested_values(values: Iterable[int]) -> tuple[int, ...]:
    try:
        requested = tuple(values)
    except TypeError as exc:
        raise ConditionMeaningGateError(
            "supply-contract-invalid", "requested values are not iterable",
        ) from exc
    if not requested:
        raise ConditionMeaningGateError(
            "supply-contract-invalid", "at least one requested value is required",
        )
    try:
        checked = tuple(_validate_define_value(value) for value in requested)
    except ValueError as exc:
        raise ConditionMeaningGateError("supply-contract-invalid", str(exc)) from exc
    if len(set(checked)) != len(checked):
        raise ConditionMeaningGateError(
            "supply-contract-invalid", "requested values must be unique",
        )
    return checked


def _validate_captured(captured: CapturedBackoffFixedInputs) -> None:
    if type(captured) is not CapturedBackoffFixedInputs:
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured input has the wrong exact type",
        )
    hashes = (
        (captured.source_bytes, captured.source_sha256),
        (captured.options_text.encode("utf-8"), captured.options_sha256),
        (captured.protocol_cmake_text.encode("utf-8"), captured.protocol_cmake_sha256),
    )
    if any(_sha256(value) != expected for value, expected in hashes):
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured input hashes are inconsistent",
        )
    expected_files = {
        SOURCE_REL: captured.source_sha256,
        OPTIONS_REL: captured.options_sha256,
        PROTOCOL_CMAKE_REL: captured.protocol_cmake_sha256,
    }
    if len(captured.input_files) != len(expected_files):
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured input evidence is incomplete",
        )
    if any(type(entry) is not CapturedFileEvidence for entry in captured.input_files):
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured input evidence has the wrong type",
        )
    observed_files = {entry.relative_path: entry for entry in captured.input_files}
    if set(observed_files) != set(expected_files):
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured input paths are inconsistent",
        )
    for relative, expected_sha256 in expected_files.items():
        entry = observed_files[relative]
        if (entry.before != entry.after
                or entry.after != entry.path_after
                or entry.sha256 != expected_sha256):
            raise ConditionMeaningGateError(
                "input-capture-failed",
                f"captured input identity evidence is inconsistent: {relative!r}",
            )


def assert_backoff_fixed_supply(
    captured: CapturedBackoffFixedInputs,
    requested_values: Iterable[int],
) -> SupplyEvidence:
    """Independently require exact cache-to-TU supply for every value."""
    _validate_captured(captured)
    values = _requested_values(requested_values)
    observations: list[SupplyObservation] = []
    for value in values:
        try:
            resolution = source_digest.resolve_effective_defines_from_cmake_sources(
                SOURCE_REL,
                Genome(PROTOCOL, {MACRO: value}),
                options_text=captured.options_text,
                protocol_cmake_text=captured.protocol_cmake_text,
            )
        except (RuntimeError, TypeError, ValueError) as exc:
            raise ConditionMeaningGateError(
                "supply-set-unavailable", "effective CMake supply cannot be rederived",
                define_value=value,
            ) from exc
        cache_name = resolution.cache_name(MACRO)
        if MACRO not in resolution.supplied_macros:
            raise ConditionMeaningGateError(
                "macro-not-supplied", "BACKOFF_FIXED cache-to-TU mapping is absent",
                define_value=value,
            )
        effective = resolution.effective_value(MACRO)
        if cache_name != MACRO or effective != str(value):
            route = "bare define without a cache mapping" if cache_name is None \
                else f"CCBENCH_{cache_name}"
            if cache_name != MACRO:
                route += f", not CCBENCH_{MACRO}"
            raise ConditionMeaningGateError(
                "supply-value-mismatch",
                f"BACKOFF_FIXED maps through {route}, to {effective!r}",
                define_value=value,
                expected=str(value),
                observed=effective,
            )
        observations.append(SupplyObservation(value, cache_name, effective))
    return SupplyEvidence(
        proof_kind=SUPPLY_PROOF_KIND,
        driver_integration=DRIVER_INTEGRATION,
        source_sha256=captured.source_sha256,
        options_sha256=captured.options_sha256,
        protocol_cmake_sha256=captured.protocol_cmake_sha256,
        source_rel=SOURCE_REL,
        owner_protocol=resolution.owner_protocol,
        input_files=captured.input_files,
        observations=tuple(observations),
    )


def _validated_cases(cases: Sequence[MeaningCase]) -> tuple[MeaningCase, ...]:
    if type(cases) not in {tuple, list} or not cases:
        raise ConditionMeaningGateError(
            "meaning-contract-invalid", "cases must be a non-empty tuple or list",
        )
    values = tuple(case.define_value for case in cases if type(case) is MeaningCase)
    if len(values) != len(cases):
        raise ConditionMeaningGateError(
            "meaning-contract-invalid", "every case must be an exact MeaningCase",
        )
    if len(set(values)) != len(values):
        raise ConditionMeaningGateError(
            "meaning-contract-invalid", "define values must be unique",
        )
    if any(case.expected_selected_branch is not None for case in cases):
        raise ConditionMeaningGateError(
            "meaning-contract-invalid",
            "selected-branch cases require the materialized branch witness",
        )
    return tuple(cases)


def _render_evaluation_tu(hole: str, cases: Sequence[MeaningCase]) -> str:
    rows: list[str] = []
    for case_index, case in enumerate(cases):
        for context_index, start in enumerate(CONTEXT_STARTS):
            rows.extend([
                "  {",
                f"#define {MACRO} {case.define_value}",
                f"    [[maybe_unused]] std::uint64_t start = {start}ULL;",
                hole,
                f"#undef {MACRO}",
                "    std::uint64_t observed_bits = 0;",
                f"    static_assert(std::is_same_v<decltype({RESULT_IDENTIFIER}), double>);",
                f"    static_assert(sizeof({RESULT_IDENTIFIER}) == sizeof(observed_bits));",
                f"    std::memcpy(&observed_bits, &{RESULT_IDENTIFIER}, sizeof(observed_bits));",
                f'    std::printf("{case_index} {context_index} %016llx\\n",',
                "                static_cast<unsigned long long>(observed_bits));",
                "  }",
            ])
    return "\n".join([
        "#include <cstdint>",
        "#include <cstdio>",
        "#include <cstring>",
        "#include <type_traits>",
        "int main() {",
        *rows,
        "  return 0;",
        "}",
        "",
    ])


def _resolve_compiler(cxx: str) -> Path:
    if type(cxx) is not str or not cxx:
        raise ConditionMeaningGateError("compiler-failed", "compiler name is invalid")
    candidate = shutil.which(cxx) if os.sep not in cxx else cxx
    if candidate is None:
        raise ConditionMeaningGateError("compiler-failed", "compiler was not found")
    try:
        compiler = Path(candidate).resolve(strict=True)
        mode = compiler.stat().st_mode
    except (OSError, RuntimeError) as exc:
        raise ConditionMeaningGateError("compiler-failed", "compiler cannot be resolved") from exc
    if not stat.S_ISREG(mode) or not os.access(compiler, os.X_OK):
        raise ConditionMeaningGateError("compiler-failed", "compiler is not executable")
    return compiler


def _capture_compiler_identity(compiler: Path, phase: str) -> CompilerFileEvidence:
    """Capture one regular compiler path before or after an invocation.

    This is a deliberate injection seam for deterministic drift tests. It is a
    path snapshot, not proof of which executable image a hostile process ran.
    """
    reason = "compiler-failed" if phase == "before-version" else "compiler-identity-drift"
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(compiler, flags)
    except OSError as exc:
        raise ConditionMeaningGateError(reason, f"compiler path is unavailable at {phase}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ConditionMeaningGateError(reason, f"compiler is not regular at {phase}")
        if not os.access(compiler, os.X_OK):
            raise ConditionMeaningGateError(reason, f"compiler is not executable at {phase}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    except OSError as exc:
        raise ConditionMeaningGateError(reason, f"compiler cannot be read at {phase}") from exc
    finally:
        os.close(descriptor)
    content = b"".join(chunks)
    before_identity = _file_identity(before)
    after_identity = _file_identity(after)
    try:
        path_identity = _file_identity(os.stat(compiler, follow_symlinks=False))
    except OSError as exc:
        raise ConditionMeaningGateError(reason, f"compiler path disappeared at {phase}") from exc
    if (before_identity != after_identity
            or after_identity != path_identity
            or len(content) != after_identity.size):
        raise ConditionMeaningGateError(reason, f"compiler changed during {phase} capture")
    return CompilerFileEvidence(
        phase=phase,
        identity=after_identity,
        sha256=_sha256(content),
    )


def _require_same_compiler(
    baseline: CompilerFileEvidence,
    observed: CompilerFileEvidence,
) -> None:
    if baseline.identity != observed.identity or baseline.sha256 != observed.sha256:
        raise ConditionMeaningGateError(
            "compiler-identity-drift",
            f"compiler path identity/content changed by {observed.phase}",
        )


def _capture_cmake_identity(cmake: Path, phase: str) -> CMakeFileEvidence:
    """Capture the CMake path before or after one configure invocation.

    This records a path snapshot, not the identity of a process to which CMake
    may delegate. The phase names describe the argv this gate executed.
    """
    reason = "configure-failed" if phase == "before-configure" \
        else "cmake-identity-drift"
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(cmake, flags)
    except OSError as exc:
        raise ConditionMeaningGateError(
            reason, f"CMake path is unavailable at {phase}",
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ConditionMeaningGateError(reason, f"CMake is not regular at {phase}")
        if not os.access(cmake, os.X_OK):
            raise ConditionMeaningGateError(reason, f"CMake is not executable at {phase}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    except OSError as exc:
        raise ConditionMeaningGateError(
            reason, f"CMake cannot be read at {phase}",
        ) from exc
    finally:
        os.close(descriptor)
    content = b"".join(chunks)
    before_identity = _file_identity(before)
    after_identity = _file_identity(after)
    try:
        path_identity = _file_identity(os.stat(cmake, follow_symlinks=False))
    except OSError as exc:
        raise ConditionMeaningGateError(
            reason, f"CMake path disappeared at {phase}",
        ) from exc
    if (before_identity != after_identity
            or after_identity != path_identity
            or len(content) != after_identity.size):
        raise ConditionMeaningGateError(
            reason, f"CMake changed during {phase} capture",
        )
    return CMakeFileEvidence(
        phase=phase,
        identity=after_identity,
        sha256=_sha256(content),
    )


def _require_same_cmake(
    baseline: CMakeFileEvidence,
    observed: CMakeFileEvidence,
) -> None:
    if baseline.identity != observed.identity or baseline.sha256 != observed.sha256:
        raise ConditionMeaningGateError(
            "cmake-identity-drift",
            f"CMake path identity/content changed by {observed.phase}",
        )


_PROCESS_ARGV_DETAIL_LIMIT_BYTES = 500
_PROCESS_ARGV_DETAIL_UNAVAILABLE = "<argv detail unavailable>"


def _bounded_process_argv_detail(argv: Sequence[str]) -> str:
    try:
        rendered = shlex.join(argv)
        encoded = rendered.encode("utf-8", errors="backslashreplace")
        if len(encoded) <= _PROCESS_ARGV_DETAIL_LIMIT_BYTES:
            return rendered
        marker = (
            "...<argv truncated; "
            f"limit={_PROCESS_ARGV_DETAIL_LIMIT_BYTES} bytes; "
            f"original={len(encoded)} bytes; "
            f"sha256={_sha256(encoded)}>"
        ).encode("ascii")
        prefix = encoded[:_PROCESS_ARGV_DETAIL_LIMIT_BYTES - len(marker)]
        return (prefix + marker).decode("utf-8", errors="ignore")
    except Exception:
        return _PROCESS_ARGV_DETAIL_UNAVAILABLE


def _run_process(
    argv: Sequence[str],
    *,
    timeout_reason: str,
    failure_reason: str,
    cwd: str | os.PathLike[str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    run_kwargs: dict[str, Any] = {
        "capture_output": True,
        "timeout": PROCESS_TIMEOUT_SECONDS,
        "check": False,
    }
    if cwd is not None:
        run_kwargs["cwd"] = os.fspath(cwd)
    run_argv = list(argv)
    try:
        completed = subprocess.run(run_argv, **run_kwargs)
    except subprocess.TimeoutExpired as exc:
        detail = (
            "process exceeded 120 seconds; "
            f"argv={_bounded_process_argv_detail(run_argv)}"
        )
        raise ConditionMeaningGateError(timeout_reason, detail) from exc
    except (OSError, subprocess.SubprocessError) as exc:
        detail = (
            "process could not be executed; "
            f"argv={_bounded_process_argv_detail(run_argv)}"
        )
        raise ConditionMeaningGateError(failure_reason, detail) from exc
    if completed.returncode != 0:
        raise ConditionMeaningGateError(
            failure_reason,
            f"process returned rc={completed.returncode}; "
            f"stderr={completed.stderr[-500:]!r}; "
            f"argv={_bounded_process_argv_detail(run_argv)}",
        )
    if completed.stderr:
        raise ConditionMeaningGateError(
            failure_reason,
            f"successful process wrote stderr={completed.stderr[-500:]!r}; "
            f"argv={_bounded_process_argv_detail(run_argv)}",
        )
    return completed


def _resolve_executable(value: str, reason: str) -> Path:
    if type(value) is not str or not value:
        raise ConditionMeaningGateError(reason, "executable name is invalid")
    candidate = shutil.which(value) if os.sep not in value else value
    if candidate is None:
        raise ConditionMeaningGateError(reason, "executable was not found")
    try:
        resolved = Path(candidate).resolve(strict=True)
        observed = resolved.stat()
    except (OSError, RuntimeError) as exc:
        raise ConditionMeaningGateError(reason, "executable cannot be resolved") from exc
    if not stat.S_ISREG(observed.st_mode) or not os.access(resolved, os.X_OK):
        raise ConditionMeaningGateError(reason, "executable is not executable")
    return resolved


def _validate_captured_define_inputs(captured: CapturedDefineInputs) -> None:
    if type(captured) is not CapturedDefineInputs:
        raise ConditionMeaningGateError(
            "input-capture-failed", "captured define inputs have the wrong exact type",
        )
    source = Path(captured.source_root)
    if _root_identity(source) != captured.source_root_identity:
        raise ConditionMeaningGateError(
            "input-capture-failed", "source root identity changed after capture",
        )
    if captured.stock_root is None:
        if captured.stock_root_identity is not None:
            raise ConditionMeaningGateError(
                "input-capture-failed", "stock root evidence is inconsistent",
            )
    else:
        if _root_identity(Path(captured.stock_root)) != captured.stock_root_identity:
            raise ConditionMeaningGateError(
                "input-capture-failed", "stock root identity changed after capture",
            )


def _configure_defines(
    request: DefineRequest,
    value: str | None,
    companions: tuple[tuple[str, str], ...],
    *,
    base_cxx_flags: str = "",
) -> tuple[str, ...]:
    rows = list(companions)
    if value is not None:
        rows.append((request.macro, value))
    if request.route == ROUTE_CMAKE_CACHE:
        return tuple(f"-DCCBENCH_{name}={item}" for name, item in rows)
    flags = " ".join((
        *(part for part in (base_cxx_flags.strip(),) if part),
        *(f"-D{name}={item}" for name, item in rows),
    ))
    return (f"-DCMAKE_CXX_FLAGS={flags}",)


def _configure_compile_commands(
    *,
    captured: CapturedDefineInputs,
    request: DefineRequest,
    source_root: Path,
    build_root: Path,
    value: str | None,
    companions: tuple[tuple[str, str], ...],
    compiler: Path,
    cmake: Path,
) -> _CMakeConfigureResult:
    cxx_flag_prefix = "-DCMAKE_CXX_FLAGS="
    base_cxx_flags = ""
    configure_args: list[str] = []
    for argument in captured.configure_args:
        if request.route == ROUTE_CMAKE_CXX_FLAGS \
                and argument.startswith(cxx_flag_prefix):
            base_cxx_flags = argument[len(cxx_flag_prefix):]
        else:
            configure_args.append(argument)
    argv = (
        os.fspath(cmake), "-S", os.fspath(source_root), "-B", os.fspath(build_root),
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        f"-DCMAKE_CXX_COMPILER={compiler}",
        *configure_args,
        *_configure_defines(
            request, value, companions, base_cxx_flags=base_cxx_flags,
        ),
    )
    before = _capture_cmake_identity(cmake, "before-configure")
    _run_process(
        argv, timeout_reason="configure-timeout", failure_reason="configure-failed",
    )
    after = _capture_cmake_identity(cmake, "after-configure")
    _require_same_cmake(before, after)
    commands_path = build_root / "compile_commands.json"
    try:
        raw = commands_path.read_bytes()
        decoded = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConditionMeaningGateError(
            "compile-command-unavailable", "compile_commands.json is unavailable or invalid",
        ) from exc
    if type(decoded) is not list or any(type(entry) is not dict for entry in decoded):
        raise ConditionMeaningGateError(
            "compile-command-unavailable", "compile command database has the wrong shape",
        )
    return _CMakeConfigureResult(
        commands=tuple(decoded),
        cmake_path=os.fspath(cmake),
        configure_argv=argv,
        cmake_identities=(before, after),
    )


def _entry_argv(entry: Mapping[str, Any]) -> tuple[str, ...]:
    arguments = entry.get("arguments")
    command = entry.get("command")
    if type(arguments) is list and arguments \
            and all(type(argument) is str and argument for argument in arguments):
        return tuple(arguments)
    if type(command) is str and command:
        try:
            parsed = tuple(shlex.split(command, posix=True))
        except ValueError as exc:
            raise ConditionMeaningGateError(
                "compile-command-unavailable", "compile command cannot be parsed",
            ) from exc
        if parsed:
            return parsed
    raise ConditionMeaningGateError(
        "compile-command-unavailable", "compile command lacks argv",
    )


def _entry_source(entry: Mapping[str, Any]) -> Path:
    directory = entry.get("directory")
    source = entry.get("file")
    if type(directory) is not str or type(source) is not str:
        raise ConditionMeaningGateError(
            "compile-command-unavailable", "compile command lacks directory/file",
        )
    try:
        path = Path(source)
        return (Path(directory) / path).resolve(strict=True) if not path.is_absolute() \
            else path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ConditionMeaningGateError(
            "compile-command-unavailable", "compile command source cannot be resolved",
        ) from exc


def _select_owner_entry(
    commands: Sequence[Mapping[str, Any]],
    *,
    source_root: Path,
    request: DefineRequest,
) -> tuple[Mapping[str, Any], Path]:
    try:
        owner = (source_root / request.owner_tu).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ConditionMeaningGateError(
            "owner-tu-unresolved", "declared owner TU is unavailable",
        ) from exc
    matches: list[Mapping[str, Any]] = []
    for entry in commands:
        if _entry_source(entry) != owner:
            continue
        argv = _entry_argv(entry)
        output = entry.get("output")
        target_markers = (
            f"CMakeFiles/{request.target}.dir/",
            f"CMakeFiles/{request.target.removesuffix('.exe')}.dir/",
        )
        target_surface = " ".join((*argv, output if type(output) is str else ""))
        if any(marker in target_surface for marker in target_markers):
            matches.append(entry)
    if len(matches) != 1:
        raise ConditionMeaningGateError(
            "owner-tu-unresolved",
            f"owner TU compile entry is not unique for target: count={len(matches)}",
        )
    return matches[0], owner


def _configured_owner_command(
    entry: Mapping[str, Any],
    *,
    configure: _CMakeConfigureResult,
    owner: Path,
    source_root: Path,
    build_root: Path,
    define_value: str | None,
) -> _ConfiguredOwnerCompileCommand:
    directory = entry.get("directory")
    if type(directory) is not str or not directory:
        raise ConditionMeaningGateError(
            "compile-command-unavailable", "compile command lacks its directory",
        )
    return _ConfiguredOwnerCompileCommand(
        directory=directory,
        argv=_entry_argv(entry),
        owner=os.fspath(owner),
        source_root=os.fspath(source_root),
        build_root=os.fspath(build_root),
        define_value=define_value,
        cmake_path=configure.cmake_path,
        configure_argv=configure.configure_argv,
        cmake_identities=configure.cmake_identities,
    )


def _issue_configured_commands(
    configured: _ConfiguredDefineCompileCommands,
) -> _ConfiguredDefineCompileCommands:
    object.__setattr__(
        configured, "_issuer_capability", _CONFIGURED_COMMANDS_ISSUER_CAPABILITY,
    )
    return configured


@contextlib.contextmanager
def _configured_define_compile_commands(
    captured: CapturedDefineInputs,
    *,
    request: DefineRequest,
    cxx: str,
    cmake: str,
) -> Iterator[_ConfiguredDefineCompileCommands | None]:
    """Keep the supply-derived owner commands alive for both arm evaluators."""
    if type(captured) is not CapturedDefineInputs or type(request) is not DefineRequest:
        # The arm evaluators retain the canonical exact-type rejection.  This
        # context only owns optional shared infrastructure, not that verdict.
        yield None
        return
    _validate_captured_define_inputs(captured)
    spec, requested, default, companions = _validate_define_request(request)
    request_digest = _request_digest(request, companions)
    source_root = Path(captured.source_root)
    stock_identity = _is_inert_value(
        spec, requested=requested, default=default,
    )
    control_root = Path(captured.stock_root) \
        if stock_identity and captured.stock_root is not None else source_root
    control_value = None if stock_identity else default
    with tempfile.TemporaryDirectory(prefix="izanagi_condition_supply_") as temporary:
        try:
            if stock_identity and captured.stock_root is None:
                raise ConditionMeaningGateError(
                    "stock-tree-unavailable",
                    "inert supply requires a distinct pinned-clean stock root",
                )
            compiler = _resolve_compiler(cxx)
            cmake_path = _resolve_executable(cmake, "configure-failed")
            base = Path(temporary)
            requested_build = base / "requested"
            shared_branch_build = (
                not stock_identity
                and request.route == ROUTE_CMAKE_CXX_FLAGS
                and request.macro in CONDITIONAL_BRANCH_WITNESSES
            )
            # CMAKE_CXX_FLAGS registry entries must share a build root so the
            # two raw meaning argv differ only in the tested define.  Cache
            # entries retain the ordinary separate requested/default roots.
            control_build = requested_build if shared_branch_build else \
                base / ("stock" if stock_identity else "default")
            requested_configure = _configure_compile_commands(
                captured=captured, request=request, source_root=source_root,
                build_root=requested_build, value=requested,
                companions=companions, compiler=compiler, cmake=cmake_path,
            )
            control_configure = _configure_compile_commands(
                captured=captured, request=request, source_root=control_root,
                build_root=control_build, value=control_value,
                companions=companions, compiler=compiler, cmake=cmake_path,
            )
            _require_same_cmake(
                requested_configure.cmake_identities[0],
                control_configure.cmake_identities[0],
            )
            requested_entry, requested_owner = _select_owner_entry(
                requested_configure.commands, source_root=source_root, request=request,
            )
            control_entry, control_owner = _select_owner_entry(
                control_configure.commands, source_root=control_root, request=request,
            )
            configured = _ConfiguredDefineCompileCommands(
                captured=captured,
                request_digest=request_digest,
                compiler_path=os.fspath(compiler),
                cmake_path=os.fspath(cmake_path),
                requested=_configured_owner_command(
                    requested_entry, configure=requested_configure,
                    owner=requested_owner,
                    source_root=source_root, build_root=requested_build,
                    define_value=requested,
                ),
                control=_configured_owner_command(
                    control_entry, configure=control_configure,
                    owner=control_owner,
                    source_root=control_root, build_root=control_build,
                    define_value=control_value,
                ),
            )
        except ConditionMeaningGateError as exc:
            configured = _ConfiguredDefineCompileCommands(
                captured=captured,
                request_digest=request_digest,
                compiler_path=None,
                cmake_path=None,
                requested=None,
                control=None,
                failure_reason=exc.reason_code,
                failure_detail=exc.detail,
                failure_expected=exc.expected,
                failure_observed=exc.observed,
                failure_define_value=exc.define_value,
                failure_context_index=exc.context_index,
            )
        yield _issue_configured_commands(configured)


def _validate_configured_define_compile_commands(
    configured: _ConfiguredDefineCompileCommands,
    *,
    captured: CapturedDefineInputs,
    request: DefineRequest,
    companions: tuple[tuple[str, str], ...],
    cxx: str,
    cmake: str,
) -> tuple[Path, _ConfiguredOwnerCompileCommand, _ConfiguredOwnerCompileCommand]:
    if type(configured) is not _ConfiguredDefineCompileCommands \
            or configured._issuer_capability \
            is not _CONFIGURED_COMMANDS_ISSUER_CAPABILITY:
        raise ConditionMeaningGateError(
            "compile-command-unavailable",
            "configured owner commands were not issued by this evaluator",
        )
    if configured.captured != captured \
            or configured.request_digest != _request_digest(request, companions):
        raise ConditionMeaningGateError(
            "compile-command-drift",
            "configured owner commands do not match this capture and request",
        )
    if configured.failure_reason is not None:
        raise ConditionMeaningGateError(
            configured.failure_reason,
            configured.failure_detail or "owner compile commands are unavailable",
            expected=configured.failure_expected,
            observed=configured.failure_observed,
            define_value=configured.failure_define_value,
            context_index=configured.failure_context_index,
        )
    compiler = _resolve_compiler(cxx)
    cmake_path = _resolve_executable(cmake, "configure-failed")
    if configured.compiler_path != os.fspath(compiler) \
            or configured.cmake_path != os.fspath(cmake_path) \
            or type(configured.requested) is not _ConfiguredOwnerCompileCommand \
            or type(configured.control) is not _ConfiguredOwnerCompileCommand:
        raise ConditionMeaningGateError(
            "compile-command-drift",
            "configured owner commands use a different toolchain or shape",
        )
    for command in (configured.requested, configured.control):
        if command.cmake_path != configured.cmake_path \
                or type(command.configure_argv) is not tuple \
                or not command.configure_argv \
                or any(type(argument) is not str or not argument
                       for argument in command.configure_argv) \
                or command.configure_argv[0] != command.cmake_path \
                or type(command.cmake_identities) is not tuple \
                or len(command.cmake_identities) != 2 \
                or any(type(row) is not CMakeFileEvidence
                       for row in command.cmake_identities):
            raise ConditionMeaningGateError(
                "compile-command-drift",
                "configured owner command lacks exact CMake execution evidence",
            )
        if tuple(row.phase for row in command.cmake_identities) != (
            "before-configure", "after-configure",
        ):
            raise ConditionMeaningGateError(
                "compile-command-drift",
                "configured owner command has non-exact CMake capture phases",
            )
        _require_same_cmake(
            command.cmake_identities[0], command.cmake_identities[1],
        )
    _require_same_cmake(
        configured.requested.cmake_identities[0],
        configured.control.cmake_identities[0],
    )
    return compiler, configured.requested, configured.control


def _configured_entry(
    command: _ConfiguredOwnerCompileCommand,
) -> Mapping[str, Any]:
    return {
        "arguments": list(command.argv),
        "directory": command.directory,
    }


def _compile_defines(argv: Sequence[str]) -> dict[str, str]:
    observed: dict[str, str] = {}
    index = 1
    while index < len(argv):
        argument = argv[index]
        value: str | None = None
        if argument == "-D" and index + 1 < len(argv):
            value = argv[index + 1]
            index += 1
        elif argument.startswith("-D") and len(argument) > 2:
            value = argument[2:]
        if value is not None:
            name, separator, item = value.partition("=")
            if name:
                if name in observed:
                    raise ConditionMeaningGateError(
                        "compile-command-invalid", f"duplicate compile define: {name}",
                    )
                observed[name] = item if separator else "1"
        index += 1
    return observed


def _canonical_compile_arg(argument: str, *, source_root: Path, build_root: Path) -> str:
    source_text = os.fspath(source_root)
    build_text = os.fspath(build_root)
    return argument.replace(build_text, "{BUILD_ROOT}").replace(source_text, "{SOURCE_ROOT}")


def _preprocess_argv(
    compile_argv: Sequence[str],
    *,
    source_root: Path,
    build_root: Path,
    dependency_path: Path,
    allowed_defines: frozenset[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    unsupported = (
        "-include-pch", "-Winvalid-pch", "-fmodules", "-fmodule-file",
        "-fmodule-map-file", "-fpch-preprocess",
    )
    if any(argument.startswith("@") or argument.endswith((".gch", ".pch"))
           or any(argument.startswith(prefix) for prefix in unsupported)
           for argument in compile_argv[1:]):
        raise ConditionMeaningGateError(
            "preprocess-unsupported-input", "response file, PCH, or module option is unsupported",
        )
    kept: list[str] = [compile_argv[0]]
    comparable: list[str] = [compile_argv[0]]
    takes_value = {"-o", "-MF", "-MT", "-MQ", "-MJ", "--serialize-diagnostics"}
    drop_single = {"-c", "-MD", "-MMD", "-MP", "-MG", "-E", "-P"}
    index = 1
    while index < len(compile_argv):
        argument = compile_argv[index]
        if argument in takes_value:
            index += 2
            continue
        if argument in drop_single:
            index += 1
            continue
        if any(argument.startswith(prefix) and argument != prefix
               for prefix in ("-o", "-MF", "-MT", "-MQ", "-MJ")):
            index += 1
            continue
        define_name: str | None = None
        consume = 1
        if argument == "-D" and index + 1 < len(compile_argv):
            define_name = compile_argv[index + 1].partition("=")[0]
            consume = 2
        elif argument.startswith("-D") and len(argument) > 2:
            define_name = argument[2:].partition("=")[0]
        if define_name in allowed_defines:
            kept.extend(compile_argv[index:index + consume])
            index += consume
            continue
        kept.append(argument)
        comparable.append(_canonical_compile_arg(
            argument, source_root=source_root, build_root=build_root,
        ))
        index += 1
    kept.extend(("-E", "-P", "-MD", "-MF", os.fspath(dependency_path)))
    comparable.extend(("-E", "-P"))
    return tuple(kept), tuple(comparable)


def _parse_dependency_file(value: bytes) -> tuple[str, ...]:
    try:
        text = value.decode("utf-8").replace("\\\n", " ")
    except UnicodeError as exc:
        raise ConditionMeaningGateError(
            "dependency-closure-invalid", "dependency output is not UTF-8",
        ) from exc
    separator = text.find(":")
    if separator < 0:
        raise ConditionMeaningGateError(
            "dependency-closure-invalid", "dependency output lacks a target separator",
        )
    try:
        dependencies = tuple(shlex.split(text[separator + 1:], posix=True))
    except ValueError as exc:
        raise ConditionMeaningGateError(
            "dependency-closure-invalid", "dependency output cannot be parsed",
        ) from exc
    if not dependencies:
        raise ConditionMeaningGateError(
            "dependency-closure-invalid", "dependency closure is empty",
        )
    return dependencies


def _dependency_closure(
    dependencies: Sequence[str],
    *,
    cwd: Path,
    source_root: Path,
    build_root: Path,
) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...]]:
    rows: dict[str, str] = {}
    volatile = (b"__DATE__", b"__TIME__", b"__TIMESTAMP__")
    root_dependent = (b"__FILE__", b"__BASE_FILE__")
    root_dependent_paths: set[str] = set()
    for item in dependencies:
        try:
            path = Path(item)
            resolved = ((cwd / path) if not path.is_absolute() else path).resolve(strict=True)
            observed = resolved.stat()
            content = resolved.read_bytes()
        except (OSError, RuntimeError) as exc:
            raise ConditionMeaningGateError(
                "dependency-closure-invalid", f"dependency is unavailable: {item!r}",
            ) from exc
        if not stat.S_ISREG(observed.st_mode):
            raise ConditionMeaningGateError(
                "dependency-closure-invalid", f"dependency is not regular: {item!r}",
            )
        try:
            relative = resolved.relative_to(source_root)
            identity = f"source/{relative.as_posix()}"
            code_owned = True
        except ValueError:
            try:
                relative = resolved.relative_to(build_root)
                identity = f"build/{relative.as_posix()}"
                code_owned = True
            except ValueError:
                identity = os.fspath(resolved)
                code_owned = False
        if code_owned and any(token in content for token in volatile):
            raise ConditionMeaningGateError(
                "preprocess-nondeterministic-builtin",
                f"code-owned dependency uses a time-dependent builtin: {identity}",
            )
        if code_owned and any(token in content for token in root_dependent):
            root_dependent_paths.add(identity)
        digest = _sha256(content)
        if identity in rows and rows[identity] != digest:
            raise ConditionMeaningGateError(
                "dependency-closure-invalid", f"dependency identity is ambiguous: {identity}",
            )
        rows[identity] = digest
    return tuple(sorted(rows.items())), tuple(sorted(root_dependent_paths))


def _patch_changed_paths(spec: DefineSpec) -> frozenset[str]:
    patch_path = Path(__file__).resolve().parents[2] / spec.patch_rel
    try:
        lines = patch_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ConditionMeaningGateError(
            "owner-tu-unresolved", f"patch declaration is unavailable: {spec.patch_rel}",
        ) from exc
    paths: set[str] = set()
    for line in lines:
        match = re.fullmatch(r"diff --git a/(.+) b/(.+)", line)
        if match is not None and match.group(1) == match.group(2):
            paths.add(match.group(2))
    if not paths:
        raise ConditionMeaningGateError(
            "owner-tu-unresolved", f"patch has no changed paths: {spec.patch_rel}",
        )
    return frozenset(paths)


def _collect_preprocess(
    *,
    entry: Mapping[str, Any],
    owner: Path,
    source_root: Path,
    build_root: Path,
    request: DefineRequest,
    spec: DefineSpec,
    companions: tuple[tuple[str, str], ...],
    expected_value: str | None,
    stock_identity: bool,
    compiler: Path,
    cmake_path: str,
    configure_argv: tuple[str, ...],
    cmake_identities: tuple[CMakeFileEvidence, ...],
) -> _PreprocessResult:
    compile_argv = _entry_argv(entry)
    entry_compiler = _resolve_executable(compile_argv[0], "compile-command-invalid")
    if entry_compiler != compiler:
        raise ConditionMeaningGateError(
            "compiler-identity-drift", "compile command uses a different compiler",
        )
    observed_defines = _compile_defines(compile_argv)
    if expected_value is not None:
        if request.macro not in observed_defines:
            raise ConditionMeaningGateError(
                "macro-not-supplied", f"{request.macro} is absent from the owner compile command",
            )
        if observed_defines[request.macro] != expected_value:
            raise ConditionMeaningGateError(
                "supply-value-mismatch",
                f"{request.macro} compile value differs from the request",
                expected=expected_value, observed=observed_defines[request.macro],
            )
    if expected_value is None and not stock_identity \
            and _declared_contrast_is_undefined(request.macro) \
            and request.macro in observed_defines:
        raise ConditionMeaningGateError(
            "supply-value-mismatch",
            f"{request.macro} compile value differs from the request",
            expected=None, observed=observed_defines[request.macro],
        )
    for name, value in companions:
        if observed_defines.get(name) != value:
            raise ConditionMeaningGateError(
                "companion-define-mismatch",
                f"required companion {name}={value} is absent or different",
                expected=value, observed=observed_defines.get(name),
            )
    dependency_path = build_root / "condition-gate.d"
    allowed_names = {request.macro, *(name for name, _ in companions)}
    if stock_identity:
        allowed_names.update(
            name for name, related in DEFINE_SPECS.items()
            if related.patch_rel == spec.patch_rel
        )
    allowed = frozenset(allowed_names)
    preprocess_argv, comparable = _preprocess_argv(
        compile_argv, source_root=source_root, build_root=build_root,
        dependency_path=dependency_path, allowed_defines=allowed,
    )
    before = _capture_compiler_identity(compiler, "before-preprocess")
    version_argv = (os.fspath(compiler), "--version")
    version_result = _run_process(
        version_argv, timeout_reason="preprocess-timeout", failure_reason="preprocess-failed",
    )
    result = _run_process(
        preprocess_argv, timeout_reason="preprocess-timeout",
        failure_reason="preprocess-failed", cwd=entry["directory"],
    )
    after = _capture_compiler_identity(compiler, "after-preprocess")
    _require_same_compiler(before, after)
    try:
        version_lines = version_result.stdout.decode("utf-8").splitlines()
        dependency_bytes = dependency_path.read_bytes()
    except (OSError, UnicodeError) as exc:
        raise ConditionMeaningGateError(
            "dependency-closure-invalid", "compiler/dependency evidence cannot be read",
        ) from exc
    if not version_lines or not version_lines[0]:
        raise ConditionMeaningGateError("preprocess-failed", "compiler identity is empty")
    dependencies = _parse_dependency_file(dependency_bytes)
    if not result.stdout:
        raise ConditionMeaningGateError(
            "preprocess-output-empty", "owner TU preprocessing produced no bytes",
        )
    closure, root_dependent_paths = _dependency_closure(
        dependencies, cwd=Path(entry["directory"]), source_root=source_root,
        build_root=build_root,
    )
    changed = _patch_changed_paths(spec)
    code_dependencies = {
        identity.removeprefix("source/")
        for identity, _ in closure if identity.startswith("source/")
    }
    if request.owner_tu not in code_dependencies:
        raise ConditionMeaningGateError(
            "owner-tu-unresolved", "dependency closure omits the declared owner TU",
        )
    if not changed.intersection(code_dependencies):
        raise ConditionMeaningGateError(
            "owner-tu-unresolved",
            "owner compile dependency closure does not intersect the patch edit surface",
        )
    return _PreprocessResult(
        preprocessed_bytes=result.stdout,
        digest=_sha256(result.stdout),
        byte_length=len(result.stdout),
        replay_argv=preprocess_argv,
        comparable_argv=comparable,
        owner_tu=os.fspath(owner.relative_to(source_root)),
        dependency_closure=closure,
        dependency_closure_digest=_canonical_digest(closure),
        root_dependent_builtin_paths=root_dependent_paths,
        compiler_path=os.fspath(compiler),
        compiler_version=version_lines[0],
        compiler_identities=(before, after),
        cmake_path=cmake_path,
        configure_argv=configure_argv,
        cmake_identities=cmake_identities,
    )


def _preprocess_evidence(
    requested: _PreprocessResult,
    control: _PreprocessResult,
    *,
    comparison: str,
) -> dict[str, Any]:
    requested_owner_digest = dict(requested.dependency_closure)[
        f"source/{requested.owner_tu}"
    ]
    control_owner_digest = dict(control.dependency_closure)[
        f"source/{control.owner_tu}"
    ]
    return {
        "comparison": comparison,
        "requested_digest": requested.digest,
        "requested_byte_length": requested.byte_length,
        "requested_replay_argv": requested.replay_argv,
        "control_digest": control.digest,
        "control_byte_length": control.byte_length,
        "control_replay_argv": control.replay_argv,
        "owner_tu": requested.owner_tu,
        "requested_owner_tu_sha256": requested_owner_digest,
        "control_owner_tu_sha256": control_owner_digest,
        "compiler_path": requested.compiler_path,
        "compiler_version": requested.compiler_version,
        "requested_compiler_identities": requested.compiler_identities,
        "control_compiler_identities": control.compiler_identities,
        "cmake_path": requested.cmake_path,
        "requested_configure_argv": requested.configure_argv,
        "control_configure_argv": control.configure_argv,
        "requested_cmake_identities": requested.cmake_identities,
        "control_cmake_identities": control.cmake_identities,
        "requested_dependency_closure": requested.dependency_closure,
        "requested_dependency_closure_digest": requested.dependency_closure_digest,
        "control_dependency_closure": control.dependency_closure,
        "control_dependency_closure_digest": control.dependency_closure_digest,
        "requested_root_dependent_builtin_paths": requested.root_dependent_builtin_paths,
        "control_root_dependent_builtin_paths": control.root_dependent_builtin_paths,
    }


def _classify_stock_inert_root_location_difference(
    requested: bytes,
    control: bytes,
    *,
    requested_source_root: bytes,
    control_source_root: bytes,
    requested_dependency_identities: frozenset[str],
    requested_root_dependent_builtin_paths: tuple[str, ...],
    control_root_dependent_builtin_paths: tuple[str, ...],
) -> tuple[bool, int, int, bool]:
    """Classify an inert mismatch using only closure-bound source paths."""
    invalid_root = any(
        separator in root
        for root in (requested_source_root, control_source_root)
        for separator in (b"\n", b"\r")
    ) or not requested_source_root or not control_source_root
    if invalid_root:
        differing_line_count = sum(
            requested_line != control_line
            for requested_line, control_line in zip_longest(
                requested.split(b"\n"), control.split(b"\n"), fillvalue=None,
            )
        )
        return False, differing_line_count, 0, True

    requested_lines = requested.split(b"\n")
    control_lines = control.split(b"\n")
    differing_line_count = sum(
        requested_line != control_line
        for requested_line, control_line in zip_longest(
            requested_lines, control_lines, fillvalue=None,
        )
    )
    source_prefix = requested_source_root + b"/"
    path_bytes = frozenset(b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                           b"abcdefghijklmnopqrstuvwxyz._+-/")
    replacement_count = 0
    has_residual = False
    for requested_line, control_line in zip_longest(
        requested_lines, control_lines, fillvalue=None,
    ):
        if requested_line is None or control_line is None:
            has_residual = True
            continue
        if requested_line == control_line:
            continue

        transformed = bytearray()
        index = 0
        while index < len(requested_line):
            if requested_line.startswith(source_prefix, index) \
                    and (index == 0 or requested_line[index - 1] not in path_bytes):
                relative_start = index + len(source_prefix)
                relative_end = relative_start
                while relative_end < len(requested_line) \
                        and requested_line[relative_end] in path_bytes:
                    relative_end += 1
                relative_bytes = requested_line[relative_start:relative_end]
                components: list[bytes] = []
                escapes_root = False
                for component in relative_bytes.split(b"/"):
                    if component in {b"", b"."}:
                        continue
                    if component == b"..":
                        if not components:
                            escapes_root = True
                            break
                        components.pop()
                    else:
                        components.append(component)
                if not escapes_root:
                    relative = b"/".join(components).decode("ascii")
                    if f"source/{relative}" in requested_dependency_identities:
                        transformed.extend(control_source_root)
                        index += len(requested_source_root)
                        replacement_count += 1
                        continue
            transformed.append(requested_line[index])
            index += 1
        if bytes(transformed) != control_line:
            has_residual = True

    has_root_dependent_builtin = bool(
        requested_root_dependent_builtin_paths
        or control_root_dependent_builtin_paths
    )
    location_only = (
        not has_residual
        and replacement_count >= 1
        and has_root_dependent_builtin
    )
    return (
        location_only,
        differing_line_count,
        replacement_count,
        has_residual,
    )


def _collect_supply_preprocess_pair(
    configured: _ConfiguredDefineCompileCommands,
    *,
    captured: CapturedDefineInputs,
    request: DefineRequest,
    spec: DefineSpec,
    companions: tuple[tuple[str, str], ...],
    requested_value: str,
    control_value: str | None,
    source_root: Path,
    control_root: Path,
    stock_identity: bool,
    cxx: str,
    cmake: str,
) -> tuple[_PreprocessResult, _PreprocessResult]:
    compiler, requested_command, control_command = \
        _validate_configured_define_compile_commands(
            configured, captured=captured, request=request,
            companions=companions, cxx=cxx, cmake=cmake,
        )
    expected_requested_owner = source_root / request.owner_tu
    expected_control_owner = control_root / request.owner_tu
    if requested_command.source_root != os.fspath(source_root) \
            or control_command.source_root != os.fspath(control_root) \
            or requested_command.owner != os.fspath(expected_requested_owner) \
            or control_command.owner != os.fspath(expected_control_owner) \
            or requested_command.define_value != requested_value \
            or control_command.define_value != control_value:
        raise ConditionMeaningGateError(
            "compile-command-drift",
            "configured owner command pair differs from the supply request",
        )
    requested_build = Path(requested_command.build_root)
    control_build = Path(control_command.build_root)
    if requested_build == control_build \
            and request.macro not in CONDITIONAL_BRANCH_WITNESSES:
        raise ConditionMeaningGateError(
            "compile-command-drift",
            "requested and control unexpectedly share a build root",
        )
    requested_result = _collect_preprocess(
        entry=_configured_entry(requested_command),
        owner=Path(requested_command.owner),
        source_root=source_root,
        build_root=requested_build,
        request=request,
        spec=spec,
        companions=companions,
        expected_value=requested_value,
        stock_identity=stock_identity,
        compiler=compiler,
        cmake_path=requested_command.cmake_path,
        configure_argv=requested_command.configure_argv,
        cmake_identities=requested_command.cmake_identities,
    )
    control_result = _collect_preprocess(
        entry=_configured_entry(control_command),
        owner=Path(control_command.owner),
        source_root=control_root,
        build_root=control_build,
        request=request,
        spec=spec,
        companions=companions,
        expected_value=None if stock_identity else control_value,
        stock_identity=stock_identity,
        compiler=compiler,
        cmake_path=control_command.cmake_path,
        configure_argv=control_command.configure_argv,
        cmake_identities=control_command.cmake_identities,
    )
    return requested_result, control_result


def evaluate_define_supply_effectuation(
    captured: CapturedDefineInputs,
    *,
    request: DefineRequest,
    cxx: str,
    cmake: str,
    configured_commands: _ConfiguredDefineCompileCommands | None = None,
) -> ConditionArmRecord:
    """Evaluate real owner-TU supply and effectuation without a hash seam."""
    _validate_captured_define_inputs(captured)
    spec, requested_value, default_value, companions = _validate_define_request(request)
    request_digest = _request_digest(request, companions)
    source_root = Path(captured.source_root)
    stock_identity = _is_inert_value(
        spec, requested=requested_value, default=default_value,
    )
    if stock_identity:
        if captured.stock_root is None:
            return _issue_arm_record(
                arm="supply-effectuation", terminal_status="red",
                reason_code="stock-tree-unavailable", request=request,
                request_digest=request_digest,
                evidence={
                    "detail": "inert supply requires a distinct pinned-clean stock root",
                },
            )
        control_root = Path(captured.stock_root)
        control_value = None
    else:
        control_root = source_root
        control_value = default_value

    def collect_pair(
        configured: _ConfiguredDefineCompileCommands,
    ) -> tuple[_PreprocessResult, _PreprocessResult]:
        return _collect_supply_preprocess_pair(
            configured,
            captured=captured,
            request=request,
            spec=spec,
            companions=companions,
            requested_value=requested_value,
            control_value=control_value,
            source_root=source_root,
            control_root=control_root,
            stock_identity=stock_identity,
            cxx=cxx,
            cmake=cmake,
        )

    try:
        if configured_commands is None:
            with _configured_define_compile_commands(
                captured, request=request, cxx=cxx, cmake=cmake,
            ) as configured:
                requested_result, control_result = collect_pair(configured)
        else:
            configured = configured_commands
            requested_result, control_result = collect_pair(configured)
    except ConditionMeaningGateError as exc:
        return _issue_arm_record(
            arm="supply-effectuation", terminal_status="red",
            reason_code=exc.reason_code, request=request, request_digest=request_digest,
            evidence={
                "detail": exc.detail,
                "expected": exc.expected,
                "observed": exc.observed,
            },
        )
    evidence = _preprocess_evidence(
        requested_result, control_result,
        comparison="stock-inert-identity" if stock_identity
        else "requested-default-difference",
    )
    if requested_result.compiler_path != control_result.compiler_path \
            or requested_result.compiler_version != control_result.compiler_version:
        return _issue_arm_record(
            arm="supply-effectuation", terminal_status="red",
            reason_code="compiler-identity-drift", request=request,
            request_digest=request_digest, evidence=evidence,
        )
    if requested_result.comparable_argv != control_result.comparable_argv:
        return _issue_arm_record(
            arm="supply-effectuation", terminal_status="red",
            reason_code="compile-command-drift", request=request,
            request_digest=request_digest, evidence=evidence,
        )
    if not stock_identity:
        root_builtin_paths = (
            requested_result.root_dependent_builtin_paths
            + control_result.root_dependent_builtin_paths
        )
        assert configured.requested is not None and configured.control is not None
        requested_build = Path(configured.requested.build_root)
        control_build = Path(configured.control.build_root)
        root_needles = [
            (os.fsencode(requested_build), requested_result.preprocessed_bytes),
            (os.fsencode(control_build), control_result.preprocessed_bytes),
        ]
        unsafe_root_builtin = bool(root_builtin_paths) and any(
            needle in output for needle, output in root_needles
        )
        if unsafe_root_builtin:
            return _issue_arm_record(
                arm="supply-effectuation", terminal_status="red",
                reason_code="preprocess-root-dependent-builtin", request=request,
                request_digest=request_digest, evidence=evidence,
            )
        if requested_result.dependency_closure != control_result.dependency_closure:
            return _issue_arm_record(
                arm="supply-effectuation", terminal_status="red",
                reason_code="dependency-closure-drift", request=request,
                request_digest=request_digest, evidence=evidence,
            )
        if requested_result.preprocessed_bytes == control_result.preprocessed_bytes:
            return _issue_arm_record(
                arm="supply-effectuation", terminal_status="red",
                reason_code="preprocess-bytes-identical", request=request,
                request_digest=request_digest, evidence=evidence,
            )
        return _issue_arm_record(
            arm="supply-effectuation", terminal_status="green",
            reason_code="requested-default-preprocess-different", request=request,
            request_digest=request_digest, evidence=evidence,
        )
    if requested_result.preprocessed_bytes == control_result.preprocessed_bytes:
        return _issue_arm_record(
            arm="supply-effectuation", terminal_status="green",
            reason_code="stock-inert-preprocess-identical", request=request,
            request_digest=request_digest, evidence=evidence,
        )
    location_only, line_count, replacement_count, has_residual = \
        _classify_stock_inert_root_location_difference(
            requested_result.preprocessed_bytes,
            control_result.preprocessed_bytes,
            requested_source_root=os.fsencode(source_root),
            control_source_root=os.fsencode(control_root),
            requested_dependency_identities=frozenset(
                identity for identity, _digest
                in requested_result.dependency_closure
            ),
            requested_root_dependent_builtin_paths=(
                requested_result.root_dependent_builtin_paths
            ),
            control_root_dependent_builtin_paths=(
                control_result.root_dependent_builtin_paths
            ),
        )
    evidence.update({
        "root_diff_line_count": line_count,
        "root_diff_replacement_count": replacement_count,
        "root_diff_source_roots": (
            os.fspath(source_root), os.fspath(control_root),
        ),
        "root_diff_has_residual": has_residual,
    })
    if location_only:
        evidence["comparison"] = "stock-inert-root-location-only"
        return _issue_arm_record(
            arm="supply-effectuation", terminal_status="green",
            reason_code="stock-inert-preprocess-root-location-only", request=request,
            request_digest=request_digest, evidence=evidence,
        )
    return _issue_arm_record(
        arm="supply-effectuation", terminal_status="red",
        reason_code="stock-inert-mismatch", request=request,
        request_digest=request_digest, evidence=evidence,
    )


def _instrument_materialized_branches(
    conditional: str,
) -> tuple[str, str]:
    """Add branch identity tokens without replacing the materialized predicate."""
    synthesized_marker = "IZANAGI_CONDITION_SELECTED_SYNTHESIZED_BACKOFF"
    stock_marker = "IZANAGI_CONDITION_SELECTED_STOCK_ADAPTIVE_BACKOFF"
    if synthesized_marker in conditional or stock_marker in conditional:
        raise ConditionMeaningGateError(
            "materialized-branch-invalid", "branch identity token already exists in source",
        )
    lines = conditional.splitlines(keepends=True)
    if_lines = [
        index for index, line in enumerate(lines)
        if re.match(r"^\s*#\s*if(?:def|ndef)?\b", line)
    ]
    else_lines = [
        index for index, line in enumerate(lines)
        if re.match(r"^\s*#\s*else\b", line)
    ]
    endif_lines = [
        index for index, line in enumerate(lines)
        if re.match(r"^\s*#\s*endif\b", line)
    ]
    if len(if_lines) != 1 or len(else_lines) != 1 or len(endif_lines) != 1 \
            or not if_lines[0] < else_lines[0] < endif_lines[0]:
        raise ConditionMeaningGateError(
            "materialized-branch-invalid", "materialized branch shape is not unique",
        )
    stock_source = "".join(lines[else_lines[0] + 1:endif_lines[0]])
    instrumented: list[str] = []
    for index, line in enumerate(lines):
        instrumented.append(line)
        if index == if_lines[0]:
            instrumented.append(synthesized_marker + "\n")
        elif index == else_lines[0]:
            instrumented.append(stock_marker + "\n")
    return "".join(instrumented), stock_source


def _assert_backoff_fixed_branch_meaning(
    captured: CapturedBackoffFixedInputs,
    case: MeaningCase,
    *,
    cxx: str,
) -> BranchMeaningEvidence:
    """Observe the selected materialized branch independently of branch bytes."""
    _validate_captured(captured)
    if type(case) is not MeaningCase \
            or case.expected_selected_branch != STOCK_ADAPTIVE_BRANCH \
            or case.define_value != -1:
        raise ConditionMeaningGateError(
            "meaning-contract-invalid", "inert branch case is not declared exactly",
        )
    try:
        source_text = captured.source_bytes.decode("utf-8")
        block = extract_materialized_evolve_block(source_text, MARKER_ID)
    except (UnicodeError, ValueError) as exc:
        raise ConditionMeaningGateError(
            "materialized-branch-invalid", "unique BACKOFF_FIXED conditional is unavailable",
        ) from exc
    probe, stock_source = _instrument_materialized_branches(block.conditional)
    compiler = _resolve_compiler(cxx)
    identities = [_capture_compiler_identity(compiler, "before-version")]
    version_argv = (os.fspath(compiler), "--version")
    version_result = _run_process(
        version_argv,
        timeout_reason="branch-preprocess-timeout",
        failure_reason="branch-preprocess-failed",
    )
    identities.append(_capture_compiler_identity(compiler, "after-version"))
    _require_same_compiler(identities[0], identities[-1])
    try:
        version_lines = version_result.stdout.decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise ConditionMeaningGateError(
            "branch-preprocess-failed", "compiler identity is not UTF-8",
        ) from exc
    if not version_lines or not version_lines[0]:
        raise ConditionMeaningGateError(
            "branch-preprocess-failed", "compiler identity is empty",
        )
    with tempfile.TemporaryDirectory(prefix="izanagi_condition_branch_") as temporary:
        source_path = Path(temporary) / "materialized-conditional.cc"
        source_path.write_text(probe, encoding="utf-8")
        preprocess_argv = (
            os.fspath(compiler), "-E", "-P", "-x", "c++",
            f"-D{MACRO}={case.define_value}", os.fspath(source_path),
        )
        result = _run_process(
            preprocess_argv,
            timeout_reason="branch-preprocess-timeout",
            failure_reason="branch-preprocess-failed",
        )
    identities.append(_capture_compiler_identity(compiler, "after-branch-preprocess"))
    _require_same_compiler(identities[0], identities[-1])
    try:
        output = result.stdout.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ConditionMeaningGateError(
            "selected-branch-observation-invalid",
            "compiler branch observation is not UTF-8",
        ) from exc
    markers = {
        SYNTHESIZED_BACKOFF_BRANCH:
            "IZANAGI_CONDITION_SELECTED_SYNTHESIZED_BACKOFF",
        STOCK_ADAPTIVE_BRANCH:
            "IZANAGI_CONDITION_SELECTED_STOCK_ADAPTIVE_BACKOFF",
    }
    selected = [
        branch for branch, marker in markers.items()
        if len(re.findall(rf"(?m)^\s*{re.escape(marker)}\s*$", output)) == 1
    ]
    absent_or_duplicate = any(
        len(re.findall(rf"(?m)^\s*{re.escape(marker)}\s*$", output)) not in {0, 1}
        for marker in markers.values()
    )
    if len(selected) != 1 or absent_or_duplicate:
        raise ConditionMeaningGateError(
            "selected-branch-observation-invalid",
            "compiler output does not identify exactly one materialized branch",
        )
    observed_branch = selected[0]
    if observed_branch != case.expected_selected_branch:
        raise ConditionMeaningGateError(
            "selected-branch-mismatch",
            "materialized conditional selected a different runtime branch",
            define_value=case.define_value,
            expected=case.expected_selected_branch,
            observed=observed_branch,
        )
    stock_statement = re.compile(
        r"\s*double\s+now_backoff\s*=\s*Backoff_\s*\.\s*load\s*"
        r"\(\s*std\s*::\s*memory_order_acquire\s*\)\s*;\s*\Z"
    )
    if stock_statement.fullmatch(stock_source) is None:
        raise ConditionMeaningGateError(
            "stock-branch-body-mismatch",
            "selected stock branch is not the materialized adaptive Backoff_.load branch",
            define_value=case.define_value,
            expected="Backoff_.load(std::memory_order_acquire)",
        )
    return BranchMeaningEvidence(
        proof_kind=BRANCH_MEANING_PROOF_KIND,
        source_sha256=captured.source_sha256,
        conditional_sha256=_sha256(block.conditional.encode("utf-8")),
        stock_branch_sha256=_sha256(stock_source.encode("utf-8")),
        define_value=case.define_value,
        expected_branch=case.expected_selected_branch,
        observed_branch=observed_branch,
        compiler_path=os.fspath(compiler),
        compiler_version=version_lines[0],
        preprocess_argv=preprocess_argv,
        compiler_identities=tuple(identities),
    )


def _capture_compile_time_branch_source(
    captured: CapturedDefineInputs,
    source_rel: str,
) -> tuple[str, CapturedFileEvidence]:
    """Capture one registry-owned source through the existing no-follow boundary."""
    root_descriptor: int | None = None
    source_descriptor: int | None = None
    try:
        root = Path(captured.source_root)
        nofollow = _nofollow_flags()
        root_path_identity = _file_identity(os.stat(root, follow_symlinks=False))
        root_descriptor = os.open(
            root, os.O_RDONLY | os.O_DIRECTORY | nofollow,
        )
        root_fd_identity = _file_identity(os.fstat(root_descriptor))
        if root_path_identity != root_fd_identity \
                or root_fd_identity != captured.source_root_identity:
            raise ConditionMeaningGateError(
                "input-capture-failed", "source root changed while opening branch source",
            )
        source_descriptor = _open_relative_nofollow(root_descriptor, source_rel)
        value, before, after = _read_descriptor(source_descriptor, source_rel)
        os.close(source_descriptor)
        source_descriptor = None
        path_descriptor = _open_relative_nofollow(root_descriptor, source_rel)
        try:
            path_after = _file_identity(os.fstat(path_descriptor))
        finally:
            os.close(path_descriptor)
        if path_after != after \
                or _file_identity(os.stat(root, follow_symlinks=False)) != root_fd_identity:
            raise ConditionMeaningGateError(
                "input-capture-failed", "branch source path changed during capture",
            )
    except ConditionMeaningGateError:
        raise
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise ConditionMeaningGateError(
            "input-capture-failed", "branch source cannot be captured",
        ) from exc
    finally:
        if source_descriptor is not None:
            os.close(source_descriptor)
        if root_descriptor is not None:
            os.close(root_descriptor)
    try:
        source_text = value.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ConditionMeaningGateError(
            "input-capture-failed", "branch source is not UTF-8",
        ) from exc
    return source_text, CapturedFileEvidence(
        relative_path=source_rel,
        before=before,
        after=after,
        path_after=path_after,
        sha256=_sha256(value),
    )


def _instrument_declared_owner_source(
    source_text: str,
    declaration: ConditionalBranchMeaningDeclaration,
    *,
    source_rel: str | None = None,
) -> str:
    """Insert a compiler-evaluated probe at every exact declared site."""
    source_rel = declaration.source_rel if source_rel is None else source_rel
    files = _declared_branch_files(declaration.macro)
    file_index, (_, start_directive, count) = next(
        (index, row) for index, row in enumerate(files) if row[0] == source_rel
    )
    multifile = bool(_CONDITIONAL_BRANCH_COMPANION_SITES.get(declaration.macro))
    lines = source_text.splitlines(keepends=True)
    starts = [
        index for index, line in enumerate(lines)
        if line.rstrip("\r\n") == start_directive
    ]
    if len(starts) != count and (count != 1 or multifile):
        raise ConditionMeaningGateError(
            "compile-time-branch-site-count-mismatch",
            "declared start directive count differs from its declared site count"
            + (f": {source_rel}" if multifile else ""),
            expected=str(count), observed=str(len(starts)),
        )
    if len(starts) != count:
        raise ConditionMeaningGateError(
            "compile-time-branch-start-not-unique",
            "declared start directive must occur exactly once in its owner file",
        )
    if _COMPILE_TIME_SELECTED_OUTPUT in source_text \
            or _COMPILE_TIME_COMPLETED_OUTPUT in source_text \
            or (multifile and any(marker in source_text for marker in (
                _COMPILE_TIME_SITE_SELECTED_MARKER, _COMPILE_TIME_SITE_COMPLETED_MARKER,
            ))):
        raise ConditionMeaningGateError(
            "compile-time-branch-marker-collision",
            "compile-time branch output marker already exists in source",
        )
    for site_index, start in enumerate(starts):
        site_key = f"f{file_index}s{site_index}"
        directive = lines[start]
        if not directive.endswith(("\n", "\r")):
            directive += "\n"
        lines[start] = "".join((
            directive,
            f"{_COMPILE_TIME_SELECTED_MARKER}()\n",
            f"{_COMPILE_TIME_SITE_SELECTED_MARKER}({site_key})\n" if multifile else "",
            "#endif\n",
            f"{_COMPILE_TIME_COMPLETED_MARKER}()\n",
            f"{_COMPILE_TIME_SITE_COMPLETED_MARKER}({site_key})\n" if multifile else "",
            directive,
        ))
    return "".join(lines)


def _write_shadow_owner_source(
    source_root: Path,
    source_rel: str,
    instrumented_source: str,
    shadow_root: Path,
    *,
    owner_tu: str,
    instrumented_sources: Mapping[str, str] | None = None,
) -> Path:
    """Write an instrumented source and return the shadow owner-TU operand."""
    relative = Path(source_rel)
    sources = {source_rel: instrumented_source} if instrumented_sources is None \
        else instrumented_sources
    try:
        if source_rel == owner_tu and len(sources) == 1:
            original_directory = source_root
            shadow_directory = shadow_root
            for component in relative.parent.parts:
                shadow_directory.mkdir()
                for child in original_directory.iterdir():
                    if child.name != component:
                        (shadow_directory / child.name).symlink_to(
                            child, target_is_directory=child.is_dir(),
                        )
                original_directory /= component
                shadow_directory /= component
            shadow_directory.mkdir()
            for child in original_directory.iterdir():
                if child.name != relative.name:
                    (shadow_directory / child.name).symlink_to(
                        child, target_is_directory=child.is_dir(),
                    )
            instrumented_path = shadow_directory / relative.name
            instrumented_path.write_text(sources[source_rel], encoding="utf-8")
            return instrumented_path

        def traversal_failed(error: OSError) -> None:
            raise error

        shadow_root.mkdir()
        for original_text, directory_names, file_names in os.walk(
            source_root, topdown=True, onerror=traversal_failed,
            followlinks=False,
        ):
            original_directory = Path(original_text)
            tree_relative = original_directory.relative_to(source_root)
            shadow_directory = shadow_root / tree_relative
            for name in tuple(directory_names):
                original = original_directory / name
                shadow = shadow_directory / name
                if original.is_symlink() or name == ".git":
                    shadow.symlink_to(original, target_is_directory=True)
                    directory_names.remove(name)
                else:
                    shadow.mkdir()
            for name in file_names:
                original = original_directory / name
                file_relative = tree_relative / name
                if file_relative.as_posix() not in sources:
                    (shadow_directory / name).symlink_to(
                        original, target_is_directory=False,
                    )
        for file_rel, text in sources.items():
            (shadow_root / file_rel).write_text(text, encoding="utf-8")
        return shadow_root / owner_tu
    except (OSError, RuntimeError) as exc:
        raise ConditionMeaningGateError(
            "compile-time-branch-instrumentation-failed",
            "instrumented owner TU shadow cannot be created",
        ) from exc


def _replace_owner_compile_input(
    entry: Mapping[str, Any],
    owner: Path,
    instrumented_owner: Path,
    *,
    source_root: Path,
    instrumented_root: Path,
) -> tuple[str, ...]:
    """Replace only the owner source operand in a captured compile command."""
    compile_argv = list(_entry_argv(entry))
    directory = Path(entry["directory"])
    matches: list[int] = []
    for index, argument in enumerate(compile_argv[1:], start=1):
        try:
            candidate = Path(argument)
            resolved = (directory / candidate).resolve(strict=True) \
                if not candidate.is_absolute() else candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if resolved == owner:
            matches.append(index)
    if len(matches) != 1:
        raise ConditionMeaningGateError(
            "compile-command-unavailable",
            f"owner TU compile operand is not unique: count={len(matches)}",
        )
    compile_argv[matches[0]] = os.fspath(instrumented_owner)
    compile_argv.extend((
        f"-ffile-prefix-map={instrumented_root}={source_root}",
        f"-D{_COMPILE_TIME_SELECTED_MARKER}()={_COMPILE_TIME_SELECTED_OUTPUT}",
        f"-D{_COMPILE_TIME_COMPLETED_MARKER}()={_COMPILE_TIME_COMPLETED_OUTPUT}",
    ))
    return tuple(compile_argv)


def _compile_time_observation(
    *,
    entry: Mapping[str, Any],
    owner: Path,
    instrumented_owner: Path,
    instrumented_root: Path,
    source_root: Path,
    build_root: Path,
    request: DefineRequest,
    companions: tuple[tuple[str, str], ...],
    define_value: str | None,
    compiler: Path,
    dependency_path: Path,
) -> tuple[CompileTimeBranchSelectionObservation, tuple[str, ...], str]:
    """Preprocess one instrumented owner TU through its actual compile argv."""
    compile_argv = _replace_owner_compile_input(
        entry, owner, instrumented_owner, source_root=source_root,
        instrumented_root=instrumented_root,
    )
    if _CONDITIONAL_BRANCH_COMPANION_SITES.get(request.macro):
        compile_argv += _COMPILE_TIME_SITE_DEFINES
    if _resolve_executable(compile_argv[0], "compile-command-invalid") != compiler:
        raise ConditionMeaningGateError(
            "compiler-identity-drift", "compile command uses a different compiler",
        )
    observed_defines = _compile_defines(compile_argv)
    if observed_defines.get(request.macro) != define_value:
        raise ConditionMeaningGateError(
            "supply-value-mismatch",
            f"{request.macro} compile value differs from the meaning request",
            expected=define_value, observed=observed_defines.get(request.macro),
        )
    for name, value in companions:
        if observed_defines.get(name) != value:
            raise ConditionMeaningGateError(
                "companion-define-mismatch",
                f"required companion {name}={value} is absent or different",
                expected=value, observed=observed_defines.get(name),
            )
    preprocess_argv, comparable = _preprocess_argv(
        compile_argv, source_root=source_root, build_root=build_root,
        dependency_path=dependency_path, allowed_defines=frozenset({request.macro}),
    )
    result = _run_process(
        preprocess_argv,
        timeout_reason="compile-time-branch-preprocess-timeout",
        failure_reason="compile-time-branch-preprocess-failed",
        cwd=entry["directory"],
    )
    try:
        output = result.stdout.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ConditionMeaningGateError(
            "compile-time-branch-observation-invalid",
            "compiler branch observation is not UTF-8",
        ) from exc
    return CompileTimeBranchSelectionObservation(
        define_value=define_value,
        selected_count=_compile_time_marker_count(
            output, _COMPILE_TIME_SELECTED_OUTPUT,
        ),
        completed_count=_compile_time_marker_count(
            output, _COMPILE_TIME_COMPLETED_OUTPUT,
        ),
        preprocess_argv=preprocess_argv,
    ), comparable, output


def _compile_time_marker_count(output: str, marker: str) -> int:
    return len(re.findall(rf"(?m)^\s*{re.escape(marker)}\s*$", output))


def _assert_compile_time_branch_selection(
    captured: CapturedDefineInputs,
    request: DefineRequest,
    declaration: ConditionalBranchMeaningDeclaration,
    *,
    cxx: str,
    cmake: str,
    configured_commands: _ConfiguredDefineCompileCommands | None = None,
) -> tuple[CompileTimeBranchSelectionEvidence, dict[str, Any]]:
    """Observe requested/contrast selection in the complete instrumented owner TU."""
    _validate_captured_define_inputs(captured)
    _spec, requested, default, companions = _validate_define_request(request)
    expected_declaration = declare_define_runtime_meaning(request)
    if type(declaration) is not ConditionalBranchMeaningDeclaration \
            or expected_declaration is None \
            or declaration != expected_declaration \
            or (default is None and not _declared_contrast_is_undefined(request.macro)):
        raise ConditionMeaningGateError(
            "meaning-contract-invalid",
            "compile-time branch declaration does not match the request registry",
        )
    source_text, source_file = _capture_compile_time_branch_source(
        captured, declaration.source_rel,
    )
    instrumented_source = _instrument_declared_owner_source(source_text, declaration)
    instrumented_sources = {declaration.source_rel: instrumented_source}
    companion_sources = []
    for source_rel, directive, count in _CONDITIONAL_BRANCH_COMPANION_SITES.get(request.macro, ()):
        text, captured_file = _capture_compile_time_branch_source(captured, source_rel)
        instrumented_sources[source_rel] = _instrument_declared_owner_source(
            text, declaration, source_rel=source_rel,
        )
        companion_sources.append({
            "source_rel": source_rel, "start_directive": directive, "site_count": count,
            "source_sha256": captured_file.sha256, "source_file": captured_file,
        })
    comparison = "1" if requested == "0" else default
    configured_pair: tuple[
        _ConfiguredOwnerCompileCommand, _ConfiguredOwnerCompileCommand,
    ] | None = None
    if configured_commands is None:
        compiler = _resolve_compiler(cxx)
        cmake_path = _resolve_executable(cmake, "configure-failed")
    else:
        compiler, requested_command, control_command = \
            _validate_configured_define_compile_commands(
                configured_commands, captured=captured, request=request,
                companions=companions, cxx=cxx, cmake=cmake,
            )
        source_root = Path(captured.source_root)
        expected_owner = source_root / request.owner_tu
        if requested_command.source_root != os.fspath(source_root) \
                or control_command.source_root != os.fspath(source_root) \
                or requested_command.owner != os.fspath(expected_owner) \
                or control_command.owner != os.fspath(expected_owner) \
                or requested_command.define_value != requested \
                or control_command.define_value != comparison:
            raise ConditionMeaningGateError(
                "compile-command-drift",
                "configured owner command pair differs from the meaning request",
            )
        configured_pair = (requested_command, control_command)
        cmake_path = None
    identities = [_capture_compiler_identity(compiler, "before-version")]
    version_result = _run_process(
        (os.fspath(compiler), "--version"),
        timeout_reason="compile-time-branch-preprocess-timeout",
        failure_reason="compile-time-branch-preprocess-failed",
    )
    identities.append(_capture_compiler_identity(compiler, "after-version"))
    _require_same_compiler(identities[0], identities[-1])
    try:
        version_lines = version_result.stdout.decode("utf-8", errors="strict").splitlines()
    except UnicodeError as exc:
        raise ConditionMeaningGateError(
            "compile-time-branch-preprocess-failed", "compiler identity is not UTF-8",
        ) from exc
    if not version_lines or not version_lines[0]:
        raise ConditionMeaningGateError(
            "compile-time-branch-preprocess-failed", "compiler identity is empty",
        )

    outputs: list[str] = []
    observations: list[CompileTimeBranchSelectionObservation] = []
    configure_evidence: list[
        _CMakeConfigureResult | _ConfiguredOwnerCompileCommand
    ] = []
    with tempfile.TemporaryDirectory(prefix="izanagi_compile_time_branch_") as temporary:
        base = Path(temporary)
        source_root = Path(captured.source_root)
        build_root = base / "build"
        instrumented_root = base / "instrumented-source"
        instrumented_owner = _write_shadow_owner_source(
            source_root, declaration.source_rel, instrumented_source,
            instrumented_root, owner_tu=request.owner_tu,
            instrumented_sources=instrumented_sources,
        )
        entries: list[tuple[str, Mapping[str, Any], Path, Path]] = []
        if configured_pair is None:
            assert cmake_path is not None
            for label, value in (("requested", requested), ("default", comparison)):
                configure = _configure_compile_commands(
                    captured=captured, request=request, source_root=source_root,
                    build_root=build_root, value=value, companions=companions,
                    compiler=compiler, cmake=cmake_path,
                )
                configure_evidence.append(configure)
                entry, owner = _select_owner_entry(
                    configure.commands, source_root=source_root, request=request,
                )
                entries.append((label, entry, owner, build_root))
        else:
            for label, command in zip(
                ("requested", "default"), configured_pair, strict=True,
            ):
                entries.append((
                    label, _configured_entry(command), Path(command.owner),
                    Path(command.build_root),
                ))
                configure_evidence.append(command)
        requested_configure, default_configure = configure_evidence
        if requested_configure.cmake_path != default_configure.cmake_path:
            raise ConditionMeaningGateError(
                "cmake-identity-drift",
                "requested/default configure commands used different CMake paths",
            )
        _require_same_cmake(
            requested_configure.cmake_identities[0],
            default_configure.cmake_identities[0],
        )
        comparables: list[tuple[str, ...]] = []
        for (label, entry, owner, entry_build_root), value in zip(
            entries, (requested, comparison), strict=True,
        ):
            observation, comparable, output = _compile_time_observation(
                entry=entry, owner=owner, instrumented_owner=instrumented_owner,
                instrumented_root=instrumented_root,
                source_root=source_root, build_root=entry_build_root, request=request,
                companions=companions, define_value=value, compiler=compiler,
                dependency_path=base / "condition-meaning.d",
            )
            outputs.append(output)
            observations.append(observation)
            comparables.append(comparable)
            identities.append(_capture_compiler_identity(
                compiler, f"after-{label}-preprocess",
            ))
            _require_same_compiler(identities[0], identities[-1])
        if comparables[0] != comparables[1]:
            raise ConditionMeaningGateError(
                "compile-command-drift",
                "requested/default owner compile commands differ beyond the tested define",
            )

    requested_observation, default_observation = observations
    requested_counts = (
        requested_observation.selected_count,
        requested_observation.completed_count,
    )
    default_counts = (
        default_observation.selected_count,
        default_observation.completed_count,
    )
    count = _declared_total_site_count(request.macro)
    requested_expected = (count * int(requested), count)
    default_expected = (count * int(comparison or "0"), count)
    expected_observations = (
        f"requested=({requested_expected[0]},{requested_expected[1]}),"
        f"default=({default_expected[0]},{default_expected[1]})"
    )
    if requested_counts == default_counts:
        raise ConditionMeaningGateError(
            "compile-time-branch-selection-not-discriminating",
            "requested and default values produced the same branch observation",
            expected=expected_observations,
            observed=f"requested={requested_counts},default={default_counts}",
        )
    if requested_counts != requested_expected \
            or default_counts != default_expected:
        raise ConditionMeaningGateError(
            "compile-time-branch-selection-mismatch",
            "requested/default branch observations do not match the declaration",
            expected=expected_observations,
            observed=f"requested={requested_counts},default={default_counts}",
        )
    companion_payload: dict[str, Any] = {}
    if companion_sources:
        site_observations = []
        for file_index, (source_rel, _, site_count) in enumerate(_declared_branch_files(request.macro)):
            for site_index in range(site_count):
                key = f"f{file_index}s{site_index}"
                counts = tuple(
                    _compile_time_marker_count(output, f"{marker}_OBSERVED_{key}")
                    for output in outputs
                    for marker in (_COMPILE_TIME_SITE_SELECTED_MARKER, _COMPILE_TIME_SITE_COMPLETED_MARKER)
                )
                expected = (int(requested), 1, int(comparison or "0"), 1)
                if counts != expected:
                    raise ConditionMeaningGateError(
                        "compile-time-branch-site-observation-mismatch",
                        "declared site observations do not match the declaration",
                        expected=f"{key}={expected}", observed=f"{key}={counts}",
                    )
                site_observations.append(dict(zip(
                    ("source_rel", "site_index", "requested_selected", "requested_completed",
                     "default_selected", "default_completed"),
                    (source_rel, site_index, *counts), strict=True,
                )))
        totals = tuple(sum(row[name] for row in site_observations) for name in (
            "requested_selected", "requested_completed", "default_selected", "default_completed",
        ))
        if totals != (*requested_counts, *default_counts):
            raise ConditionMeaningGateError(
                "compile-time-branch-site-observation-mismatch",
                "declared site observation sums differ from total observations",
                expected=str((*requested_counts, *default_counts)), observed=str(totals),
            )
        companion_payload = {
            "companion_sources": tuple(companion_sources),
            "site_observations": tuple(site_observations),
        }
    return CompileTimeBranchSelectionEvidence(
        proof_kind=COMPILE_TIME_BRANCH_SELECTION_PROOF_KIND,
        source_rel=declaration.source_rel,
        start_directive=declaration.start_directive,
        source_sha256=source_file.sha256,
        source_file=source_file,
        requested=requested_observation,
        default=default_observation,
        compiler_path=os.fspath(compiler),
        compiler_version=version_lines[0],
        compiler_identities=tuple(identities),
        cmake_path=requested_configure.cmake_path,
        requested_configure_argv=requested_configure.configure_argv,
        default_configure_argv=default_configure.configure_argv,
        requested_cmake_identities=requested_configure.cmake_identities,
        default_cmake_identities=default_configure.cmake_identities,
    ), companion_payload


def evaluate_define_runtime_meaning(
    captured: CapturedDefineInputs,
    *,
    request: DefineRequest,
    declaration: MeaningWitnessDeclaration | ConditionalBranchMeaningDeclaration | None,
    cxx: str,
    cmake: str = "cmake",
    configured_commands: _ConfiguredDefineCompileCommands | None = None,
) -> ConditionArmRecord:
    """Evaluate a declared meaning witness, preserving undeclared as a third state."""
    _validate_captured_define_inputs(captured)
    _spec, requested_value, _default_value, companions = _validate_define_request(request)
    request_digest = _request_digest(request, companions)
    if declaration is None:
        return _issue_arm_record(
            arm="runtime-meaning", terminal_status="unestablished",
            reason_code="meaning-witness-undeclared", request=request,
            request_digest=request_digest,
            evidence={"witness_declared": False},
        )
    if type(declaration) is ConditionalBranchMeaningDeclaration:
        expected_declaration = declare_define_runtime_meaning(request)
        if expected_declaration is None or declaration != expected_declaration:
            return _issue_arm_record(
                arm="runtime-meaning", terminal_status="unestablished",
                reason_code="meaning-witness-undeclared", request=request,
                request_digest=request_digest,
                evidence={"witness_declared": False},
            )
        try:
            compile_time_observed, companion_payload = _assert_compile_time_branch_selection(
                captured, request, declaration, cxx=cxx, cmake=cmake,
                configured_commands=configured_commands,
            )
        except ConditionMeaningGateError as exc:
            return _issue_arm_record(
                arm="runtime-meaning", terminal_status="red",
                reason_code=exc.reason_code, request=request,
                request_digest=request_digest,
                evidence={
                    "witness_id": declaration.witness_id,
                    "detail": exc.detail,
                    "expected": exc.expected,
                    "observed": exc.observed,
                    "define_value": exc.define_value,
                    "context_index": exc.context_index,
                },
            )
        return _issue_arm_record(
            arm="runtime-meaning", terminal_status="green",
            reason_code="declared-compile-time-branch-selection-observed",
            request=request,
            request_digest=request_digest,
            evidence={
                "witness_id": declaration.witness_id,
                "proof_kind": compile_time_observed.proof_kind,
                **companion_payload,
                "source_rel": compile_time_observed.source_rel,
                "start_directive": compile_time_observed.start_directive,
                "source_sha256": compile_time_observed.source_sha256,
                "source_file": compile_time_observed.source_file,
                "requested": compile_time_observed.requested,
                "default": compile_time_observed.default,
                "compiler_path": compile_time_observed.compiler_path,
                "compiler_version": compile_time_observed.compiler_version,
                "compiler_identities": compile_time_observed.compiler_identities,
                "cmake_path": compile_time_observed.cmake_path,
                "requested_configure_argv": (
                    compile_time_observed.requested_configure_argv
                ),
                "default_configure_argv": compile_time_observed.default_configure_argv,
                "requested_cmake_identities": (
                    compile_time_observed.requested_cmake_identities
                ),
                "default_cmake_identities": (
                    compile_time_observed.default_cmake_identities
                ),
            },
        )
    if type(declaration) is not MeaningWitnessDeclaration \
            or declaration.macro != request.macro \
            or request.macro != MACRO:
        return _issue_arm_record(
            arm="runtime-meaning", terminal_status="unestablished",
            reason_code="meaning-witness-undeclared", request=request,
            request_digest=request_digest,
            evidence={"witness_declared": False},
        )
    matching = tuple(
        case for case in declaration.cases
        if type(case) is MeaningCase and str(case.define_value) == requested_value
    )
    if len(matching) != 1:
        return _issue_arm_record(
            arm="runtime-meaning", terminal_status="unestablished",
            reason_code="meaning-value-undeclared", request=request,
            request_digest=request_digest,
            evidence={"witness_id": declaration.witness_id},
        )
    try:
        legacy_captured = capture_backoff_fixed_inputs(captured.source_root)
        if matching[0].expected_selected_branch is not None:
            observed: MeaningEvidence | BranchMeaningEvidence = \
                _assert_backoff_fixed_branch_meaning(
                    legacy_captured, matching[0], cxx=cxx,
                )
        else:
            observed = assert_backoff_fixed_meaning(
                legacy_captured, matching, cxx=cxx,
            )
    except ConditionMeaningGateError as exc:
        return _issue_arm_record(
            arm="runtime-meaning", terminal_status="red",
            reason_code=exc.reason_code, request=request, request_digest=request_digest,
            evidence={
                "witness_id": declaration.witness_id,
                "detail": exc.detail,
                "expected": exc.expected,
                "observed": exc.observed,
                "define_value": exc.define_value,
                "context_index": exc.context_index,
            },
        )
    evidence: dict[str, Any] = {
        "witness_id": declaration.witness_id,
        "proof_kind": observed.proof_kind,
        "source_sha256": observed.source_sha256,
        "compiler_path": observed.compiler_path,
        "compiler_version": observed.compiler_version,
        "compiler_identities": observed.compiler_identities,
    }
    if isinstance(observed, BranchMeaningEvidence):
        evidence.update({
            "conditional_sha256": observed.conditional_sha256,
            "stock_branch_sha256": observed.stock_branch_sha256,
            "define_value": observed.define_value,
            "expected_branch": observed.expected_branch,
            "observed_branch": observed.observed_branch,
            "preprocess_argv": observed.preprocess_argv,
        })
    else:
        evidence.update({
            "hole_sha256": observed.hole_sha256,
            "compiler_argv": observed.compiler_argv,
            "run_argv": observed.run_argv,
            "input_files": observed.input_files,
            "observations": observed.observations,
        })
    return _issue_arm_record(
        arm="runtime-meaning", terminal_status="green",
        reason_code="declared-meaning-observed", request=request,
        request_digest=request_digest,
        evidence=evidence,
    )


_RAW_USE_CLASSES = frozenset({"raw", "raw-measurement"})
_PROMOTION_USE_CLASSES = frozenset({
    "certified-selection", "floor", "oracle", "paper",
})


def _invalid_record(detail: str) -> None:
    raise ConditionMeaningGateError("admission-contract-invalid", detail)


def _require_record_sha256(value: object, field_name: str) -> None:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _invalid_record(f"{field_name} must be a lowercase SHA-256 digest")


def _require_record_argv(value: object, field_name: str) -> tuple[str, ...]:
    if type(value) is not tuple or not value \
            or any(type(argument) is not str or not argument for argument in value):
        _invalid_record(f"{field_name} must be a non-empty exact argv tuple")
    return value


def _validate_record_file_identity(value: object, field_name: str) -> None:
    if type(value) is not RegularFileIdentity:
        _invalid_record(f"{field_name} has the wrong file-identity type")
    integers = (
        value.device, value.inode, value.size,
        value.mtime_ns, value.ctime_ns,
    )
    if any(type(item) is not int or item < 0 for item in integers) or value.size == 0:
        _invalid_record(f"{field_name} has an empty or invalid file identity")


def _validate_record_compiler_identities(
    value: object,
    field_name: str,
) -> tuple[CompilerFileEvidence, ...]:
    if type(value) is not tuple or len(value) < 2 \
            or any(type(row) is not CompilerFileEvidence for row in value):
        _invalid_record(f"{field_name} must contain compiler identity observations")
    phases: set[str] = set()
    for index, row in enumerate(value):
        if type(row.phase) is not str or not row.phase or row.phase in phases:
            _invalid_record(f"{field_name} has an empty or duplicate phase")
        phases.add(row.phase)
        _validate_record_file_identity(row.identity, f"{field_name}[{index}].identity")
        _require_record_sha256(row.sha256, f"{field_name}[{index}].sha256")
    baseline = (value[0].identity, value[0].sha256)
    if any((row.identity, row.sha256) != baseline for row in value[1:]):
        _invalid_record(f"{field_name} records compiler identity drift")
    return value


def _validate_record_cmake_identities(
    value: object,
    field_name: str,
) -> tuple[CMakeFileEvidence, CMakeFileEvidence]:
    if type(value) is not tuple or len(value) != 2 \
            or any(type(row) is not CMakeFileEvidence for row in value):
        _invalid_record(f"{field_name} must contain exact CMake identity observations")
    if tuple(row.phase for row in value) != (
        "before-configure", "after-configure",
    ):
        _invalid_record(f"{field_name} has non-exact configure phases")
    for index, row in enumerate(value):
        _validate_record_file_identity(row.identity, f"{field_name}[{index}].identity")
        _require_record_sha256(row.sha256, f"{field_name}[{index}].sha256")
    if (value[0].identity, value[0].sha256) \
            != (value[1].identity, value[1].sha256):
        _invalid_record(f"{field_name} records CMake identity drift")
    return value


def _validate_record_configure_argv(
    value: object,
    field_name: str,
    *,
    cmake_path: str,
) -> tuple[str, ...]:
    argv = _require_record_argv(value, field_name)
    if argv[0] != cmake_path:
        _invalid_record(f"{field_name} is not bound to cmake_path")
    return argv


def _validate_record_dependency_closure(
    value: object,
    digest: object,
    field_name: str,
) -> dict[str, str]:
    if type(value) is not tuple or not value:
        _invalid_record(f"{field_name} must be a non-empty exact tuple")
    rows: dict[str, str] = {}
    for row in value:
        if type(row) is not tuple or len(row) != 2 \
                or type(row[0]) is not str or not row[0]:
            _invalid_record(f"{field_name} contains an invalid file row")
        _require_record_sha256(row[1], f"{field_name} file digest")
        if row[0] in rows:
            _invalid_record(f"{field_name} contains a duplicate file identity")
        rows[row[0]] = row[1]
    if value != tuple(sorted(value)):
        _invalid_record(f"{field_name} is not canonically ordered")
    _require_record_sha256(digest, f"{field_name}_digest")
    if digest != _canonical_digest(value):
        _invalid_record(f"{field_name} digest does not bind its file rows")
    return rows


def _validate_supply_green_evidence(record: ConditionArmRecord) -> None:
    evidence = record.evidence
    required = {
        "comparison", "requested_digest", "requested_byte_length",
        "requested_replay_argv", "control_digest", "control_byte_length",
        "control_replay_argv", "owner_tu", "requested_owner_tu_sha256",
        "control_owner_tu_sha256", "compiler_path", "compiler_version",
        "requested_compiler_identities", "control_compiler_identities",
        "cmake_path", "requested_configure_argv", "control_configure_argv",
        "requested_cmake_identities", "control_cmake_identities",
        "requested_dependency_closure", "requested_dependency_closure_digest",
        "control_dependency_closure", "control_dependency_closure_digest",
        "requested_root_dependent_builtin_paths",
        "control_root_dependent_builtin_paths",
    }
    root_location_only = (
        record.reason_code == "stock-inert-preprocess-root-location-only"
    )
    if root_location_only:
        required.update({
            "root_diff_line_count",
            "root_diff_replacement_count",
            "root_diff_source_roots",
            "root_diff_has_residual",
        })
    missing = required - set(evidence)
    unexpected = set(evidence) - required
    if missing or unexpected:
        _invalid_record(
            "green supply evidence schema differs: "
            f"missing={sorted(missing)!r} unexpected={sorted(unexpected)!r}",
        )
    spec = _MOCC_BACKOFF_SPEC if (record.macro == "BACKOFF_FIXED"
                                  and evidence.get("owner_tu") in _MOCC_OWNER) else DEFINE_SPECS[record.macro]
    owner_tu = evidence["owner_tu"]
    if type(owner_tu) is not str or not owner_tu or owner_tu not in spec.owner_tus:
        _invalid_record("green supply evidence does not name a declared owner TU")
    compiler_path = evidence["compiler_path"]
    compiler_version = evidence["compiler_version"]
    if type(compiler_path) is not str or not compiler_path \
            or type(compiler_version) is not str or not compiler_version:
        _invalid_record("green supply evidence has an empty compiler identity")
    requested_argv = _require_record_argv(
        evidence["requested_replay_argv"], "requested_replay_argv",
    )
    control_argv = _require_record_argv(
        evidence["control_replay_argv"], "control_replay_argv",
    )
    if requested_argv[0] != compiler_path or control_argv[0] != compiler_path:
        _invalid_record("green supply replay argv is not bound to the compiler path")
    cmake_path = evidence["cmake_path"]
    if type(cmake_path) is not str or not cmake_path:
        _invalid_record("green supply evidence has an empty CMake path")
    requested_configure_argv = _validate_record_configure_argv(
        evidence["requested_configure_argv"],
        "requested_configure_argv",
        cmake_path=cmake_path,
    )
    control_configure_argv = _validate_record_configure_argv(
        evidence["control_configure_argv"],
        "control_configure_argv",
        cmake_path=cmake_path,
    )
    requested_cmake = _validate_record_cmake_identities(
        evidence["requested_cmake_identities"], "requested_cmake_identities",
    )
    control_cmake = _validate_record_cmake_identities(
        evidence["control_cmake_identities"], "control_cmake_identities",
    )
    cmake_identity = (requested_cmake[0].identity, requested_cmake[0].sha256)
    if (control_cmake[0].identity, control_cmake[0].sha256) != cmake_identity:
        _invalid_record("green supply arms used different CMake identities")
    requested_compilers = _validate_record_compiler_identities(
        evidence["requested_compiler_identities"], "requested_compiler_identities",
    )
    control_compilers = _validate_record_compiler_identities(
        evidence["control_compiler_identities"], "control_compiler_identities",
    )
    compiler_identity = (requested_compilers[0].identity, requested_compilers[0].sha256)
    if (control_compilers[0].identity, control_compilers[0].sha256) != compiler_identity:
        _invalid_record("green supply arms used different compiler identities")
    requested_files = _validate_record_dependency_closure(
        evidence["requested_dependency_closure"],
        evidence["requested_dependency_closure_digest"],
        "requested_dependency_closure",
    )
    control_files = _validate_record_dependency_closure(
        evidence["control_dependency_closure"],
        evidence["control_dependency_closure_digest"],
        "control_dependency_closure",
    )
    owner_identity = f"source/{owner_tu}"
    for prefix, files in (("requested", requested_files), ("control", control_files)):
        digest_field = f"{prefix}_owner_tu_sha256"
        _require_record_sha256(evidence[digest_field], digest_field)
        if files.get(owner_identity) != evidence[digest_field]:
            _invalid_record(f"{digest_field} does not bind the owner TU file")
    for prefix in ("requested", "control"):
        _require_record_sha256(evidence[f"{prefix}_digest"], f"{prefix}_digest")
        length = evidence[f"{prefix}_byte_length"]
        if type(length) is not int or length <= 0:
            _invalid_record(f"{prefix}_byte_length must be a positive exact integer")
        builtin_paths = evidence[f"{prefix}_root_dependent_builtin_paths"]
        if type(builtin_paths) is not tuple \
                or any(type(path) is not str or not path for path in builtin_paths):
            _invalid_record(
                f"{prefix}_root_dependent_builtin_paths has the wrong exact type",
            )
    if root_location_only:
        line_count = evidence["root_diff_line_count"]
        if type(line_count) is not int or line_count < 1:
            _invalid_record("root_diff_line_count must be a positive exact integer")
        replacement_count = evidence["root_diff_replacement_count"]
        if type(replacement_count) is not int or replacement_count < 1:
            _invalid_record(
                "root_diff_replacement_count must be a positive exact integer",
            )
        source_roots = evidence["root_diff_source_roots"]
        if type(source_roots) is not tuple or len(source_roots) != 2 \
                or any(type(root) is not str or not root for root in source_roots) \
                or source_roots[0] == source_roots[1]:
            _invalid_record(
                "root_diff_source_roots must contain two distinct non-empty strings",
            )
        if evidence["root_diff_has_residual"] is not False:
            _invalid_record("root_diff_has_residual must be exact false")
        if not (
            evidence["requested_root_dependent_builtin_paths"]
            or evidence["control_root_dependent_builtin_paths"]
        ):
            _invalid_record(
                "root-location-only evidence lacks a root-dependent builtin",
            )
        if len(requested_configure_argv) < 3 \
                or len(control_configure_argv) < 3 \
                or requested_configure_argv[1] != "-S" \
                or control_configure_argv[1] != "-S":
            _invalid_record(
                "root-location-only configure argv lacks an exact -S source root",
            )
        if source_roots != (
            requested_configure_argv[2], control_configure_argv[2],
        ):
            _invalid_record(
                "root_diff_source_roots is not bound to configure argv",
            )
    status_contract = {
        "requested-default-preprocess-different": (
            "requested-default-difference", False,
        ),
        "stock-inert-preprocess-identical": (
            "stock-inert-identity", True,
        ),
        "stock-inert-preprocess-root-location-only": (
            "stock-inert-root-location-only", False,
        ),
    }
    expected = status_contract.get(record.reason_code)
    if expected is None or evidence["comparison"] != expected[0]:
        _invalid_record("green supply reason and comparison vocabulary disagree")
    digests_equal = evidence["requested_digest"] == evidence["control_digest"]
    if digests_equal is not expected[1]:
        _invalid_record("green supply digest relation disagrees with its comparison")


def _validate_record_input_files(value: object, source_sha256: str) -> None:
    if type(value) is not tuple or not value \
            or any(type(row) is not CapturedFileEvidence for row in value):
        _invalid_record("meaning input_files must contain captured file evidence")
    paths: set[str] = set()
    for index, row in enumerate(value):
        if type(row.relative_path) is not str or not row.relative_path \
                or row.relative_path in paths:
            _invalid_record("meaning input_files has an empty or duplicate path")
        paths.add(row.relative_path)
        _validate_record_file_identity(row.before, f"input_files[{index}].before")
        _validate_record_file_identity(row.after, f"input_files[{index}].after")
        _validate_record_file_identity(row.path_after, f"input_files[{index}].path_after")
        if row.before != row.after or row.after != row.path_after:
            _invalid_record("meaning input file identity changed during capture")
        _require_record_sha256(row.sha256, f"input_files[{index}].sha256")
    source_rows = [row for row in value if row.relative_path == SOURCE_REL]
    if len(source_rows) != 1 or source_rows[0].sha256 != source_sha256:
        _invalid_record("meaning source digest does not bind its captured source file")


def _validate_meaning_observations(value: object) -> None:
    if type(value) is not tuple or len(value) != len(CONTEXT_STARTS) \
            or any(type(row) is not MeaningObservation for row in value):
        _invalid_record("green meaning evidence lacks exact pointwise observations")
    define_values: set[int] = set()
    contexts: set[int] = set()
    for row in value:
        if type(row.define_value) is not int or row.define_value < 0 \
                or type(row.context_index) is not int \
                or row.context_index not in range(len(CONTEXT_STARTS)) \
                or type(row.start) is not int \
                or row.start != CONTEXT_STARTS[row.context_index]:
            _invalid_record("green meaning observation coordinates are invalid")
        if type(row.expected_bits) is not str \
                or type(row.observed_bits) is not str \
                or _BITS_RE.fullmatch(row.expected_bits) is None \
                or _BITS_RE.fullmatch(row.observed_bits) is None \
                or row.expected_bits != row.observed_bits:
            _invalid_record("green meaning observation does not match its declaration")
        define_values.add(row.define_value)
        contexts.add(row.context_index)
    if len(define_values) != 1 or contexts != set(range(len(CONTEXT_STARTS))):
        _invalid_record("green meaning observations do not cover one declared value")


def _validate_compile_time_branch_observation(
    value: object,
    field_name: str,
    *,
    compiler_path: str,
    macro: str,
    define_value: str | None,
    selected_count: int,
    completed_count: int = 1,
) -> CompileTimeBranchSelectionObservation:
    if type(value) is not CompileTimeBranchSelectionObservation:
        _invalid_record(f"{field_name} has the wrong exact observation type")
    if value.define_value != define_value \
            or type(value.selected_count) is not int \
            or type(value.completed_count) is not int \
            or value.selected_count != selected_count \
            or value.completed_count != completed_count:
        _invalid_record(f"{field_name} does not encode the exact branch observation")
    argv = _require_record_argv(value.preprocess_argv, f"{field_name}.preprocess_argv")
    try:
        observed_defines = _compile_defines(argv)
    except ConditionMeaningGateError:
        _invalid_record(f"{field_name} argv has invalid compile defines")
    if argv[0] != compiler_path \
            or observed_defines.get(macro) != define_value \
            or observed_defines.get(f"{_COMPILE_TIME_SELECTED_MARKER}()") \
            != _COMPILE_TIME_SELECTED_OUTPUT \
            or observed_defines.get(f"{_COMPILE_TIME_COMPLETED_MARKER}()") \
            != _COMPILE_TIME_COMPLETED_OUTPUT \
            or "-E" not in argv \
            or "-P" not in argv:
        _invalid_record(f"{field_name} argv is not bound to the declared macro value")
    return value


def _validate_meaning_green_evidence(record: ConditionArmRecord) -> None:
    evidence = record.evidence
    common = {
        "witness_id", "proof_kind", "source_sha256", "compiler_path",
        "compiler_version", "compiler_identities",
    }
    missing = common - set(evidence)
    if missing:
        _invalid_record(f"green meaning evidence is missing fields: {sorted(missing)!r}")
    if record.macro not in MEANING_SUPPORTED_MACROS:
        _invalid_record("green meaning record names a macro without meaning support")
    if type(evidence["witness_id"]) is not str \
            or not evidence["witness_id"]:
        _invalid_record("green meaning record lacks a declared witness identity")
    _require_record_sha256(evidence["source_sha256"], "meaning source_sha256")
    compiler_path = evidence["compiler_path"]
    compiler_version = evidence["compiler_version"]
    if type(compiler_path) is not str or not compiler_path \
            or type(compiler_version) is not str or not compiler_version:
        _invalid_record("green meaning evidence has an empty compiler identity")
    _validate_record_compiler_identities(
        evidence["compiler_identities"], "meaning compiler_identities",
    )
    if evidence["proof_kind"] != COMPILE_TIME_BRANCH_SELECTION_PROOF_KIND \
            and record.reason_code != "declared-meaning-observed":
        _invalid_record("green legacy meaning record has an unknown reason code")
    if evidence["proof_kind"] == MEANING_PROOF_KIND:
        if record.macro != MACRO:
            _invalid_record("green pointwise meaning proof is not BACKOFF_FIXED")
        required = {"hole_sha256", "compiler_argv", "run_argv", "input_files", "observations"}
        missing = required - set(evidence)
        unexpected = set(evidence) - common - required
        if missing or unexpected:
            _invalid_record(
                "green pointwise meaning evidence schema differs: "
                f"missing={sorted(missing)!r} unexpected={sorted(unexpected)!r}",
            )
        _require_record_sha256(evidence["hole_sha256"], "meaning hole_sha256")
        compiler_argv = _require_record_argv(evidence["compiler_argv"], "compiler_argv")
        _require_record_argv(evidence["run_argv"], "run_argv")
        if compiler_argv[0] != compiler_path:
            _invalid_record("green meaning compiler argv is not bound to compiler_path")
        _validate_record_input_files(evidence["input_files"], evidence["source_sha256"])
        _validate_meaning_observations(evidence["observations"])
        return
    if evidence["proof_kind"] == BRANCH_MEANING_PROOF_KIND:
        if record.macro != MACRO:
            _invalid_record("green selected-branch meaning proof is not BACKOFF_FIXED")
        required = {
            "conditional_sha256", "stock_branch_sha256", "define_value",
            "expected_branch", "observed_branch", "preprocess_argv",
        }
        missing = required - set(evidence)
        unexpected = set(evidence) - common - required
        if missing or unexpected:
            _invalid_record(
                "green branch meaning evidence schema differs: "
                f"missing={sorted(missing)!r} unexpected={sorted(unexpected)!r}",
            )
        _require_record_sha256(evidence["conditional_sha256"], "conditional_sha256")
        _require_record_sha256(evidence["stock_branch_sha256"], "stock_branch_sha256")
        preprocess_argv = _require_record_argv(
            evidence["preprocess_argv"], "preprocess_argv",
        )
        if preprocess_argv[0] != compiler_path \
                or type(evidence["define_value"]) is not int \
                or evidence["define_value"] != -1 \
                or evidence["expected_branch"] != STOCK_ADAPTIVE_BRANCH \
                or evidence["observed_branch"] != STOCK_ADAPTIVE_BRANCH:
            _invalid_record("green branch meaning observation is invalid")
        return
    if evidence["proof_kind"] == COMPILE_TIME_BRANCH_SELECTION_PROOF_KIND:
        if record.reason_code \
                != "declared-compile-time-branch-selection-observed":
            _invalid_record("green compile-time branch record has a broad reason code")
        required = {
            "source_rel", "start_directive", "source_file",
            "requested", "default",
            "cmake_path", "requested_configure_argv", "default_configure_argv",
            "requested_cmake_identities", "default_cmake_identities",
        }
        companion_declarations = _CONDITIONAL_BRANCH_COMPANION_SITES.get(record.macro, ())
        if companion_declarations:
            required |= {"companion_sources", "site_observations"}
        missing = required - set(evidence)
        unexpected = set(evidence) - common - required
        if missing or unexpected:
            _invalid_record(
                "green compile-time branch evidence schema differs: "
                f"missing={sorted(missing)!r} unexpected={sorted(unexpected)!r}",
            )
        cmake_path = evidence["cmake_path"]
        if type(cmake_path) is not str or not cmake_path:
            _invalid_record("green compile-time branch evidence has an empty CMake path")
        _validate_record_configure_argv(
            evidence["requested_configure_argv"],
            "requested_configure_argv",
            cmake_path=cmake_path,
        )
        _validate_record_configure_argv(
            evidence["default_configure_argv"],
            "default_configure_argv",
            cmake_path=cmake_path,
        )
        requested_cmake = _validate_record_cmake_identities(
            evidence["requested_cmake_identities"],
            "requested_cmake_identities",
        )
        default_cmake = _validate_record_cmake_identities(
            evidence["default_cmake_identities"],
            "default_cmake_identities",
        )
        cmake_identity = (requested_cmake[0].identity, requested_cmake[0].sha256)
        if (default_cmake[0].identity, default_cmake[0].sha256) != cmake_identity:
            _invalid_record(
                "green compile-time requested/default used different CMake identities",
            )
        registered = CONDITIONAL_BRANCH_WITNESSES.get(record.macro)
        if registered is None \
                or (evidence["source_rel"], evidence["start_directive"]) != registered:
            _invalid_record("green compile-time branch evidence is not registry-bound")
        source_file = evidence["source_file"]
        if type(source_file) is not CapturedFileEvidence \
                or source_file.relative_path != evidence["source_rel"] \
                or source_file.sha256 != evidence["source_sha256"]:
            _invalid_record("green compile-time branch source file is not digest-bound")
        _validate_record_file_identity(source_file.before, "source_file.before")
        _validate_record_file_identity(source_file.after, "source_file.after")
        _validate_record_file_identity(source_file.path_after, "source_file.path_after")
        _require_record_sha256(source_file.sha256, "source_file.sha256")
        if source_file.before != source_file.after \
                or source_file.after != source_file.path_after:
            _invalid_record("green compile-time branch source changed during capture")
        requested_value = "1"
        undefined_contrast = _declared_contrast_is_undefined(record.macro)
        default_value = None if undefined_contrast else "0"
        count = _declared_total_site_count(record.macro)
        if record.macro == "BACKOFF_NOINLINE":
            raw_requested = evidence["requested"]
            raw_default = evidence["default"]
            if type(raw_requested) is not CompileTimeBranchSelectionObservation \
                    or type(raw_default) is not CompileTimeBranchSelectionObservation \
                    or raw_requested.define_value not in {"0", "1"} \
                    or raw_default.define_value != (
                        "1" if raw_requested.define_value == "0" else "0"
                    ):
                _invalid_record(
                    "green compile-time noinline observations do not bind opposite values",
                )
            requested_value = raw_requested.define_value
            default_value = raw_default.define_value
        requested = _validate_compile_time_branch_observation(
            evidence["requested"], "requested", compiler_path=compiler_path,
            macro=record.macro, define_value=requested_value,
            selected_count=count * int(requested_value), completed_count=count,
        )
        default = _validate_compile_time_branch_observation(
            evidence["default"], "default", compiler_path=compiler_path,
            macro=record.macro, define_value=default_value,
            selected_count=count * int(default_value or "0"), completed_count=count,
        )
        if companion_declarations:
            rows = evidence["companion_sources"]
            if type(rows) is not tuple or len(rows) != len(companion_declarations):
                _invalid_record("green companion sources do not match registry")
            for row, (source_rel, directive, site_count) in zip(rows, companion_declarations, strict=True):
                if not isinstance(row, Mapping) or set(row) != {
                    "source_rel", "start_directive", "site_count", "source_sha256", "source_file",
                }:
                    _invalid_record("green companion source row schema differs")
                if row["source_rel"] != source_rel or row["start_directive"] != directive \
                        or type(row["site_count"]) is not int or row["site_count"] != site_count:
                    _invalid_record("green companion source is not registry-bound")
                source_file = row["source_file"]
                _require_record_sha256(row["source_sha256"], "companion.source_sha256")
                if type(source_file) is not CapturedFileEvidence \
                        or source_file.relative_path != source_rel \
                        or source_file.sha256 != row["source_sha256"]:
                    _invalid_record("green companion source file is not digest-bound")
                for phase in ("before", "after", "path_after"):
                    _validate_record_file_identity(getattr(source_file, phase), f"companion.{phase}")
                _require_record_sha256(source_file.sha256, "companion.source_file.sha256")
                if source_file.before != source_file.after or source_file.after != source_file.path_after:
                    _invalid_record("green companion source changed during capture")
            sites = evidence["site_observations"]
            expected_sites = tuple(
                (source_rel, index)
                for source_rel, _, n in _declared_branch_files(record.macro)
                for index in range(n)
            )
            if type(sites) is not tuple or len(sites) != len(expected_sites):
                _invalid_record("green site observations do not match registry")
            count_keys = ("requested_selected", "requested_completed", "default_selected", "default_completed")
            for row, (source_rel, index) in zip(sites, expected_sites, strict=True):
                if not isinstance(row, Mapping) or set(row) != {"source_rel", "site_index", *count_keys}:
                    _invalid_record("green site observation row schema differs")
                if row["source_rel"] != source_rel or type(row["site_index"]) is not int \
                        or row["site_index"] != index:
                    _invalid_record("green site observation is not registry-bound")
                if any(type(row[key]) is not int for key in count_keys) \
                        or tuple(row[key] for key in count_keys) != (int(requested_value), 1, 0, 1):
                    _invalid_record("green site observation counts differ")
            if tuple(sum(row[key] for row in sites) for key in count_keys) != (
                requested.selected_count, requested.completed_count,
                default.selected_count, default.completed_count,
            ):
                _invalid_record("green site observation sums differ")
            for observation in (requested, default):
                if not all(define in observation.preprocess_argv for define in _COMPILE_TIME_SITE_DEFINES):
                    _invalid_record("green site marker defines are missing")
        if undefined_contrast:
            requested_argv = iter(requested.preprocess_argv)
            normalized = []
            for argument in requested_argv:
                if argument == f"-D{record.macro}=1":
                    continue
                if argument == "-D":
                    operand = next(requested_argv, None)
                    if operand is None:
                        _invalid_record("green compile-time requested argv has a dangling -D")
                    if operand != f"{record.macro}=1":
                        normalized.extend((argument, operand))
                else:
                    normalized.append(argument)
            normalized_requested_argv = tuple(normalized)
            normalized_default_argv = default.preprocess_argv
        else:
            normalized_requested_argv = tuple(
                "<TESTED_DEFINE>" if argument in {
                    f"-D{record.macro}={requested.define_value}",
                    f"{record.macro}={requested.define_value}",
                } else argument
                for argument in requested.preprocess_argv
            )
            normalized_default_argv = tuple(
                "<TESTED_DEFINE>" if argument in {
                    f"-D{record.macro}={default.define_value}",
                    f"{record.macro}={default.define_value}",
                } else argument
                for argument in default.preprocess_argv
            )
        if normalized_requested_argv != normalized_default_argv:
            _invalid_record(
                "green compile-time observations differ beyond the tested define",
            )
        phases = tuple(row.phase for row in evidence["compiler_identities"])
        if phases != (
            "before-version", "after-version", "after-requested-preprocess",
            "after-default-preprocess",
        ):
            _invalid_record("green compile-time compiler phases are not exact")
        return
    _invalid_record("green meaning proof_kind is not supported")


def _validate_arm_record_integrity(
    record: ConditionArmRecord,
    *,
    require_issuer: bool = True,
) -> None:
    if type(record) is not ConditionArmRecord:
        _invalid_record("arm record has the wrong exact type")
    if type(record.arm) is not str \
            or record.arm not in {"supply-effectuation", "runtime-meaning"}:
        _invalid_record("arm record has an unknown arm")
    terminal_statuses = {"green", "red", "unestablished"}
    if type(record.terminal_status) is not str \
            or record.terminal_status not in terminal_statuses:
        _invalid_record("arm record has an unknown terminal status")
    if record.arm == "supply-effectuation" \
            and record.terminal_status == "unestablished":
        _invalid_record("supply/effectuation cannot be unestablished")
    if type(record.reason_code) is not str or not record.reason_code \
            or type(record.driver_id) is not str or not record.driver_id \
            or type(record.macro) is not str or record.macro not in SUPPLY_DOMAIN_MACROS:
        _invalid_record("arm record has empty or invalid identity fields")
    _require_record_sha256(record.request_digest, "request_digest")
    _require_record_sha256(record.record_digest, "record_digest")
    if not isinstance(record.evidence, Mapping) or not record.evidence \
            or any(type(key) is not str or not key for key in record.evidence):
        _invalid_record("arm record evidence must be a non-empty string-keyed mapping")
    if record.terminal_status == "green":
        if record.arm == "supply-effectuation":
            _validate_supply_green_evidence(record)
        else:
            _validate_meaning_green_evidence(record)
    payload = {
        "arm": record.arm,
        "terminal_status": record.terminal_status,
        "reason_code": record.reason_code,
        "driver_id": record.driver_id,
        "macro": record.macro,
        "request_digest": record.request_digest,
        "evidence": record.evidence,
    }
    expected = _canonical_digest(payload)
    if record.record_digest != expected \
            or record.record_id != f"condition-gate/{record.arm}/{expected}":
        _invalid_record("arm record canonical digest/id is invalid")
    if require_issuer and record._issuer_capability is not _RECORD_ISSUER_CAPABILITY:
        _invalid_record("arm record was not issued by a production evaluator")


def require_condition_gate_family(
    supply_records: Sequence[ConditionArmRecord],
    meaning_records: Sequence[ConditionArmRecord],
    *,
    use_class: str,
) -> ConditionFamilyAdmission:
    """Require green supply and non-red meaning, preserving unestablished names."""
    if use_class not in _RAW_USE_CLASSES | _PROMOTION_USE_CLASSES:
        raise ConditionMeaningGateError(
            "admission-contract-invalid", f"unknown use class: {use_class!r}",
        )
    if type(supply_records) not in {tuple, list} \
            or type(meaning_records) not in {tuple, list}:
        raise ConditionMeaningGateError(
            "admission-contract-invalid", "record collections must be tuples or lists",
        )
    records = tuple(supply_records) + tuple(meaning_records)
    if not records or any(type(record) is not ConditionArmRecord for record in records):
        raise ConditionMeaningGateError(
            "admission-contract-invalid", "arm records are missing or invalid",
        )
    if any(record.arm != "supply-effectuation" for record in supply_records) \
            or any(record.arm != "runtime-meaning" for record in meaning_records):
        raise ConditionMeaningGateError(
            "admission-contract-invalid", "arm record was placed in the wrong collection",
        )
    for record in records:
        _validate_arm_record_integrity(record)
    supply_by_request = {record.request_digest: record for record in supply_records}
    meaning_by_request = {record.request_digest: record for record in meaning_records}
    if len(supply_by_request) != len(supply_records) \
            or len(meaning_by_request) != len(meaning_records) \
            or set(supply_by_request) != set(meaning_by_request):
        raise ConditionMeaningGateError(
            "admission-contract-invalid", "each request needs exactly one record from each arm",
        )
    supply_green = all(record.terminal_status == "green" for record in supply_records)
    meaning_not_red = all(
        record.terminal_status in {"green", "unestablished"}
        for record in meaning_records
    )
    admitted = supply_green and meaning_not_red
    unestablished_meaning_macros = tuple(sorted({
        record.macro
        for record in meaning_records
        if record.terminal_status == "unestablished"
    }))
    record_ids = tuple(record.record_id for record in records)
    payload = {
        "use_class": use_class,
        "admitted": admitted,
        "record_ids": record_ids,
        "unestablished_meaning_macros": unestablished_meaning_macros,
    }
    digest = _canonical_digest(payload)
    return ConditionFamilyAdmission(
        admission_id=f"condition-gate/admission/{digest}",
        admission_digest=digest,
        use_class=use_class,
        admitted=admitted,
        record_ids=record_ids,
        unestablished_meaning_macros=unestablished_meaning_macros,
    )


def _cli_scalar(value: str | None) -> int | str | None:
    if value is None:
        return None
    if re.fullmatch(r"-?[0-9]+", value):
        return int(value)
    return value


def _cli_meaning_cases(values: Sequence[str]) -> tuple[MeaningCase, ...]:
    cases: list[MeaningCase] = []
    for value in values:
        parts = value.split(":")
        if len(parts) != 3 or re.fullmatch(r"-?[0-9]+", parts[0]) is None:
            raise ConditionMeaningGateError(
                "cli-contract-invalid",
                "--meaning-case must be VALUE:START1_BITS:START2_BITS or "
                "VALUE:branch:stock-adaptive-backoff",
            )
        try:
            if parts[1] == "branch":
                cases.append(MeaningCase(int(parts[0]), None, parts[2]))
            else:
                cases.append(MeaningCase(int(parts[0]), (parts[1], parts[2])))
        except ValueError as exc:
            raise ConditionMeaningGateError(
                "cli-contract-invalid", "--meaning-case is invalid",
            ) from exc
    return tuple(cases)


def condition_gate_cli(argv: Sequence[str] | None = None) -> int:
    """Thin shell-driver entry point over the same production family API."""
    parser = argparse.ArgumentParser(prog="condition-meaning-gate")
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--stock-root")
    parser.add_argument("--driver-id", required=True)
    parser.add_argument("--macro", required=True, choices=sorted(SUPPLY_DOMAIN_MACROS))
    parser.add_argument("--requested-value", required=True)
    parser.add_argument("--default-value")
    parser.add_argument("--stock-comparison", action="store_true")
    parser.add_argument("--configure-arg", action="append", default=[])
    parser.add_argument("--meaning-case", action="append", default=[])
    parser.add_argument("--cxx", required=True)
    parser.add_argument("--cmake", default="cmake")
    parser.add_argument(
        "--use-class", default="raw-measurement",
        choices=sorted(_RAW_USE_CLASSES | _PROMOTION_USE_CLASSES),
    )
    namespace = parser.parse_args(list(argv) if argv is not None else None)
    try:
        captured = capture_define_inputs(
            namespace.source_root, stock_root=namespace.stock_root,
            configure_args=namespace.configure_arg,
        )
        request = make_define_request(
            driver_id=namespace.driver_id,
            macro=namespace.macro,
            requested_value=_cli_scalar(namespace.requested_value),
            default_value=_cli_scalar(namespace.default_value),
            stock_comparison=namespace.stock_comparison,
        )
        cases = _cli_meaning_cases(namespace.meaning_case)
        if cases and request.macro != MACRO:
            raise ConditionMeaningGateError(
                "cli-contract-invalid",
                f"legacy meaning cases are unsupported for macro: {request.macro}",
            )
        declaration: MeaningWitnessDeclaration \
            | ConditionalBranchMeaningDeclaration | None
        declaration = MeaningWitnessDeclaration(request.macro, cases) if cases \
            else declare_define_runtime_meaning(request)
        supply = evaluate_define_supply_effectuation(
            captured, request=request, cxx=namespace.cxx, cmake=namespace.cmake,
        )
        meaning = evaluate_define_runtime_meaning(
            captured, request=request, declaration=declaration, cxx=namespace.cxx,
            cmake=namespace.cmake,
        )
        admission = require_condition_gate_family(
            [supply], [meaning], use_class=namespace.use_class,
        )
    except ConditionMeaningGateError as exc:
        parser.error(f"{exc.reason_code}: {exc.detail}")
    print(supply.canonical_json())
    print(meaning.canonical_json())
    print(admission.canonical_json())
    return 0 if admission.admitted else 2


def _parse_observed_rows(
    stdout: bytes,
    cases: Sequence[MeaningCase],
) -> dict[tuple[int, int], str]:
    expected_rows = {
        (case_index, context_index)
        for case_index in range(len(cases))
        for context_index in range(len(CONTEXT_STARTS))
    }
    observed: dict[tuple[int, int], str] = {}
    for raw_line in stdout.splitlines():
        match = _ROW_RE.fullmatch(raw_line)
        if match is None:
            raise ConditionMeaningGateError(
                "compiler-output-invalid", f"malformed output row {raw_line!r}",
            )
        try:
            identity = (int(match.group(1)), int(match.group(2)))
        except ValueError as exc:
            raise ConditionMeaningGateError(
                "compiler-output-invalid", "output row index is not a bounded Python integer",
            ) from exc
        if identity not in expected_rows or identity in observed:
            raise ConditionMeaningGateError(
                "compiler-output-invalid", f"unknown or duplicate output row {identity!r}",
            )
        bits = match.group(3).decode("ascii")
        if not math.isfinite(_float_from_bits(bits)):
            raise ConditionMeaningGateError(
                "decoded-output-nonfinite", f"non-finite output at row {identity!r}",
                define_value=(cases[identity[0]].define_value
                              if identity[0] < len(cases) else None),
                context_index=identity[1],
                observed=bits,
            )
        observed[identity] = bits
    if set(observed) != expected_rows:
        missing = sorted(expected_rows - set(observed))
        raise ConditionMeaningGateError(
            "compiler-output-invalid", f"missing output rows {missing!r}",
        )
    return observed


def assert_backoff_fixed_meaning(
    captured: CapturedBackoffFixedInputs,
    cases: Sequence[MeaningCase],
    *,
    cxx: str,
) -> MeaningEvidence:
    """Compile captured decoder bytes and require pointwise binary64 meaning."""
    _validate_captured(captured)
    checked_cases = _validated_cases(cases)
    try:
        source_text = captured.source_bytes.decode("utf-8")
        block = extract_materialized_evolve_block(source_text, MARKER_ID)
    except (UnicodeError, ValueError) as exc:
        raise ConditionMeaningGateError(
            "materialized-decoder-invalid", "unique BACKOFF_FIXED decoder hole is unavailable",
        ) from exc
    if not block.hole.strip():
        raise ConditionMeaningGateError(
            "materialized-decoder-invalid", "captured decoder hole is empty",
        )
    hole_sha256 = _sha256(block.hole.encode("utf-8"))
    tu = _render_evaluation_tu(block.hole, checked_cases)
    compiler = _resolve_compiler(cxx)
    compiler_identities = [
        _capture_compiler_identity(compiler, "before-version"),
    ]

    version_argv = (os.fspath(compiler), "--version")
    version_result = _run_process(
        version_argv, timeout_reason="compiler-timeout", failure_reason="compiler-failed",
    )
    compiler_identities.append(_capture_compiler_identity(compiler, "after-version"))
    _require_same_compiler(compiler_identities[0], compiler_identities[-1])
    try:
        version_lines = version_result.stdout.decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise ConditionMeaningGateError(
            "compiler-failed", "compiler identity is not UTF-8",
        ) from exc
    if not version_lines or not version_lines[0]:
        raise ConditionMeaningGateError("compiler-failed", "compiler identity is empty")

    with tempfile.TemporaryDirectory(prefix="izanagi_condition_meaning_") as temporary:
        source_path = Path(temporary) / "decoder.cc"
        binary_path = Path(temporary) / "decoder"
        source_path.write_text(tu, encoding="utf-8")
        compiler_argv = (
            os.fspath(compiler), *source_digest.BUILD_FLAGS,
            "-Wall", "-Wextra", "-Werror", "-x", "c++",
            os.fspath(source_path), "-o", os.fspath(binary_path),
        )
        _run_process(
            compiler_argv,
            timeout_reason="compiler-timeout",
            failure_reason="compiler-failed",
        )
        compiler_identities.append(_capture_compiler_identity(compiler, "after-compile"))
        _require_same_compiler(compiler_identities[0], compiler_identities[-1])
        run_argv = (os.fspath(binary_path),)
        run_result = _run_process(
            run_argv,
            timeout_reason="decoder-run-timeout",
            failure_reason="decoder-run-failed",
        )
        observed = _parse_observed_rows(run_result.stdout, checked_cases)

    observations: list[MeaningObservation] = []
    for case_index, case in enumerate(checked_cases):
        for context_index, start in enumerate(CONTEXT_STARTS):
            expected_bits = case.expected_float64_bits_by_context[context_index]
            observed_bits = observed[(case_index, context_index)]
            if observed_bits != expected_bits:
                raise ConditionMeaningGateError(
                    "decoded-meaning-mismatch",
                    "captured decoder result differs from declared pointwise meaning",
                    define_value=case.define_value,
                    context_index=context_index,
                    expected=expected_bits,
                    observed=observed_bits,
                )
            observations.append(MeaningObservation(
                define_value=case.define_value,
                context_index=context_index,
                start=start,
                expected_bits=expected_bits,
                observed_bits=observed_bits,
            ))
    return MeaningEvidence(
        proof_kind=MEANING_PROOF_KIND,
        driver_integration=DRIVER_INTEGRATION,
        source_sha256=captured.source_sha256,
        options_sha256=captured.options_sha256,
        protocol_cmake_sha256=captured.protocol_cmake_sha256,
        hole_sha256=hole_sha256,
        compiler_path=os.fspath(compiler),
        compiler_version=version_lines[0],
        compiler_argv=compiler_argv,
        run_argv=run_argv,
        input_files=captured.input_files,
        compiler_identities=tuple(compiler_identities),
        observations=tuple(observations),
    )


__all__ = [
    "BRANCH_MEANING_PROOF_KIND", "COMPILE_TIME_BRANCH_SELECTION_PROOF_KIND",
    "CONDITIONAL_BRANCH_WITNESSES", "CONTEXT_STARTS", "DEFINE_SPECS",
    "DRIVER_INTEGRATION", "MEANING_PROOF_KIND", "MEANING_SUPPORTED_MACROS",
    "PROCESS_TIMEOUT_SECONDS", "RELATED_DEFINE_DECODE_MACROS", "ROUTE_CMAKE_CACHE",
    "ROUTE_CMAKE_CXX_FLAGS", "STOCK_ADAPTIVE_BRANCH", "SUPPLY_DOMAIN_MACROS",
    "SUPPLY_PROOF_KIND", "SYNTHESIZED_BACKOFF_BRANCH",
    "BranchMeaningEvidence", "CapturedBackoffFixedInputs", "CapturedDefineInputs",
    "CapturedFileEvidence", "CompileTimeBranchSelectionEvidence",
    "CompileTimeBranchSelectionObservation", "ConditionalBranchMeaningDeclaration",
    "CompilerFileEvidence", "ConditionArmRecord", "ConditionFamilyAdmission",
    "ConditionMeaningGateError", "DefineRequest", "DefineSpec", "MeaningCase",
    "MeaningEvidence", "MeaningObservation", "MeaningWitnessDeclaration",
    "RegularFileIdentity", "SupplyEvidence", "SupplyObservation",
    "assert_backoff_fixed_meaning", "assert_backoff_fixed_supply",
    "canonical_float64_bits", "capture_backoff_fixed_inputs", "capture_define_inputs",
    "condition_gate_cli", "declare_define_runtime_meaning",
    "evaluate_define_runtime_meaning", "evaluate_define_supply_effectuation",
    "make_define_request", "require_condition_gate_family",
]


if __name__ == "__main__":
    raise SystemExit(condition_gate_cli())
