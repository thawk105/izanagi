# -*- coding: utf-8 -*-
"""s8b floor campaign driver (``campaign.s8b_floor_campaign``) の契約テスト (formula v2)。

実ビルド・実 bench は一切呼ばない。
``prepare_fn``/``buildcache.build``/``measure_fn``/``probe_fn``/``sleep_fn``/
``monotonic_fn``/``now_fn`` を全て注入し、合成 freeze fixture (holdout rr79/rr23 × 6 構成、
stock_common 含む) で全経路を回す。rr79/rr23 は実在 freeze の rr80/rr20 と records/threads/
workload を意図的に変え、「freeze から来た値」であることをテスト内で判別できるようにしてある
(δ-15: 原則 synthetic 軸のみ。固定 seal の consumer replay 1 本だけは実 freeze bytes を読む)。

floor の式そのものの mutation-killing テストは ``test_s8b_floor_stats.py`` が正本。本ファイルは
driver 側の配線 (schedule 決定性・golden + 意図 mutant / protocol 承認凍結値 pin + 版交差拒否 /
official core 拒否 / session 有効性→retry→floor 伝播 / probe 臨界区間 + post-probe finally /
performance_anomaly / machine_anomaly / create-only + 冪等 finalization / resume 状態機械 +
manifest.schedule 権威 + attempt registry / env contract 結線 / duration 台帳) を固定する。
"""
from __future__ import annotations

import ast
import copy
import contextlib
import dataclasses
import datetime as dt
import hashlib
import inspect
import io
import json
import os
import random
import shlex
import shutil
import stat
import subprocess
import sys
import textwrap
import time
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from unittest import mock

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.tests.s8b_v2_freeze_fixture import (
    portable_binary_admission_receipt_fixture,
)

from orchestrator.campaign import env_contract as ec  # noqa: E402
from orchestrator import holdout_observation  # noqa: E402
from orchestrator.campaign import (  # noqa: E402
    attempt_registry_core,
    campaign_claim,
    floor_submit_receipt,
    reservation,
)
from orchestrator.campaign import env_attestation  # noqa: E402
from orchestrator.campaign import s8b_floor_campaign  # noqa: E402
from orchestrator.campaign import s8b_floor_contract  # noqa: E402
from orchestrator.campaign import s8b_floor_stats  # noqa: E402
from orchestrator.campaign import s8b_attempt_profile  # noqa: E402
from orchestrator.campaign import s8b_binary_admission  # noqa: E402
from orchestrator.campaign import s8b_materialization  # noqa: E402
from orchestrator.campaign import s8b_launch_cert  # noqa: E402
from orchestrator.campaign import s8b_oracle_artifacts  # noqa: E402
from orchestrator.campaign import s8b_prediction_runner  # noqa: E402
from orchestrator.campaign import s8b_selector_freeze  # noqa: E402
from orchestrator.campaign import sort_swo_oracle  # noqa: E402
from orchestrator.campaign.build_admission import (  # noqa: E402
    BuildProvenance,
    GeneratorId,
    ReviewId,
    build_run_context,
    derive_build_admission,
    require_build_admission,
)
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.p2_2 import ENV_TAG  # noqa: E402
from orchestrator.campaign.s1_direct_comparison import PreparedCell  # noqa: E402
from orchestrator.campaign.source_digest import SourceEvidence  # noqa: E402
from orchestrator.campaign.s8b_freeze_io import VerifiedFreeze  # noqa: E402
from orchestrator.tests.test_masstree_archive_projection import (  # noqa: E402
    GOLDEN_CANONICAL_DIGEST as _FIXTURE_ARCHIVE_NONDEBUG_SHA256,
    write_masstree_archive as _write_masstree_archive,
)
from orchestrator.calibrator import perf_preflight as calibrator_perf_preflight  # noqa: E402
from orchestrator.calibrator import runner as calibrator_runner  # noqa: E402
from orchestrator.tests import output_snapshot_ignores as output_snapshots  # noqa: E402
from orchestrator.tests.output_snapshot_ignores import (  # noqa: E402
    git_indexed_output_snapshot,
    git_ignored_output_prefixes,
    git_ignored_output_snapshot_rules,
    is_git_ignored_output_path,
)

buildcache = s8b_floor_campaign.buildcache

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_schema_v2 import _valid_document as _valid_calibration_v2_document  # noqa: E402
from s8b_floor_evidence_fixture import (  # noqa: E402
    expected_portable_sort_swo_pass_receipt,
    fake_sort_swo_pass_attempt,
)


# --------------------------------------------------------------------------- #
# 合成 freeze fixture (rr79/rr23、実在 rr80/rr20 と判別可能な値)                #
# --------------------------------------------------------------------------- #

_CONFIGS = (
    "p2_2_flag_opt", "backoff_fixed_best", "sort_best",
    "system_gate", "ident_all", "stock_common",
)
_STOCK = "stock_common"
_FIXTURE_COMPARATOR = (
    "  sort(write_set_.begin(), write_set_.end(),\n"
    "       [](const WriteElement<Tuple>& a, const WriteElement<Tuple>& b) -> bool {\n"
    "         return a.storage_ != b.storage_ ? a.storage_ < b.storage_\n"
    "                                         : b.key_ < a.key_;\n"
    "       });"
)
_FIXTURE_GATE_PREDICATES = {
    "system_gate": (
        "izanagi_gate_pass = "
        "izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;"
    ),
    "ident_all": (
        "izanagi_gate_pass = "
        "izanagi_abort_reason_ == IzanagiAbortReason::kUnset || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked || "
        "izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;"
    ),
}
_HOLDOUT_SHAPE = {
    "rr79": {
        "candidate_id": "H1", "records": 730079, "threads": 17,
        "ycsb": {"ycsb_zipf_skew": "0.42", "ycsb_rratio": "79", "ycsb_rmw": "1"},
    },
    "rr23": {
        "candidate_id": "H2", "records": 230023, "threads": 11,
        "ycsb": {"ycsb_zipf_skew": "0.31", "ycsb_rratio": "23", "ycsb_rmw": "0"},
    },
}

# 決定的 measure_fn 用の cell 別基準 tps。
_BASE_TPS = {
    "rr79::stock_common": 1000.0,
    "rr79::p2_2_flag_opt": 1050.0,
    "rr79::backoff_fixed_best": 1080.0,
    "rr79::sort_best": 1120.0,
    "rr79::system_gate": 1200.0,
    "rr79::ident_all": 900.0,
    "rr23::stock_common": 500.0,
    "rr23::p2_2_flag_opt": 520.0,
    "rr23::backoff_fixed_best": 540.0,
    "rr23::sort_best": 560.0,
    "rr23::system_gate": 600.0,
    "rr23::ident_all": 470.0,
}

_FIXED_NOW = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
_FIXTURE_CELL_BY_TOKEN: dict[str, str] = {}
_FIXTURE_BUILD_DECLARATION_BY_TOKEN: dict[str, tuple[str, str, dict]] = {}


def _fixture_src_token(genome, ccbench_dir) -> str:
    source_root = Path(ccbench_dir or "/fixture/ccbench")
    leaf = source_root.name.replace("__", "::")
    identity = leaf if "::" in leaf else genome.canonical()
    seed = f"{genome.canonical()}\0{identity}".encode("utf-8")
    return hashlib.sha256(seed).hexdigest()


def _fixture_expected_materialization_sha256(declaration) -> str:
    return hashlib.sha256(
        b"fixture-expected-materialization\0"
        + json.dumps(
            declaration, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _fixture_source_evidence(
        genome, ccbench_commit, *, ccbench_dir="", cxx="g++-13",
        sort_oracle_contract_id=None):
    del cxx
    source_root = str(Path(ccbench_dir or "/fixture/ccbench").resolve())
    token = _fixture_src_token(genome, source_root)
    return SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=source_root,
        ccbench_commit=ccbench_commit,
        genome_sha256=hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest(),
        src_token=token,
        source_bytes_sha256=hashlib.sha256(b"fixture-source").hexdigest(),
        tracked_clean=False,
        tracked_diff_sha256=hashlib.sha256(b"fixture-diff").hexdigest(),
        tracked_paths=("include/backoff.hh",),
    )


@pytest.fixture(autouse=True)
def _synthetic_source_evidence_for_materializer_fixtures(monkeypatch, request):
    """Fake PreparedCell 用の source evidence。slow real-build controls は実 resolver を使う。"""
    if request.node.name.startswith("test_slow_real_"):
        return

    monkeypatch.setattr(
        s8b_floor_campaign.source_digest, "resolve_evidence", _fixture_source_evidence,
    )
    monkeypatch.setattr(
        s8b_floor_campaign._perf_preflight, "probe_perf_availability",
        lambda **_kwargs: _perf_receipt(available=True),
    )


@pytest.fixture(autouse=True)
def _synthetic_expected_materialization_for_floor_fixtures(monkeypatch, request):
    """Synthetic PreparedCell を無条 build gate の正例へ明示射影する。"""
    if request.node.name.startswith("test_slow_real_"):
        return

    state = {"digest": None}

    def fixture_expected_materialization(**kwargs):
        digest = _fixture_expected_materialization_sha256(
            kwargs["declaration"]
        )
        state["digest"] = digest
        return digest

    def fixture_exact_materialization(_root, expected):
        assert expected == state["digest"]
        return expected

    def fixture_protect_snapshot(root):
        return (
            s8b_floor_campaign._expected_materialization.
            SnapshotPermissionState(
                root=str(root), modes=(), tree_digest=state["digest"],
            )
        )

    monkeypatch.setattr(
        s8b_floor_campaign._expected_materialization,
        "produce_expected_materialization_from_declaration",
        fixture_expected_materialization,
    )
    monkeypatch.setattr(
        s8b_floor_campaign._expected_materialization,
        "assert_expected_materialization",
        fixture_exact_materialization,
    )
    monkeypatch.setattr(
        s8b_floor_campaign._expected_materialization,
        "make_snapshot_non_writable",
        fixture_protect_snapshot,
    )
    monkeypatch.setattr(
        s8b_floor_campaign._expected_materialization,
        "restore_snapshot_permissions",
        lambda _state: None,
    )


@pytest.fixture(autouse=True)
def _portable_receipts_for_floor_fixtures(monkeypatch, request):
    """Campaign tests exercise portable records; real issuance has bounded coverage."""
    if request.node.name.startswith("test_slow_real_"):
        return
    monkeypatch.setattr(
        s8b_floor_campaign._binary_admission, "issue_binary_admission_receipt",
        portable_binary_admission_receipt_fixture,
    )


def _fixture_toolchain_binding(verified_calibration, *, cc, cxx):
    """登録 receipt と一致済みの gate 結果を模す process-safe fake。"""
    assert isinstance(
        verified_calibration, s8b_floor_campaign.env_attestation.VerifiedCalibration,
    )
    return {
        "cc": {
            "requested": cc,
            "realpath": f"/fixture/toolchain/{cc}",
            "version_first_line": "fixture cc version",
            "version": "fixture cc version\nfixture cc detail",
        },
        "cxx": {
            "requested": cxx,
            "realpath": f"/fixture/toolchain/{cxx}",
            "version_first_line": "fixture cxx version",
            "version": "fixture cxx version\nfixture cxx detail",
        },
        "cmake": {
            "requested": "cmake",
            "realpath": "/fixture/toolchain/cmake",
            "version_first_line": "cmake version fixture",
            "version": "cmake version fixture\nfixture cmake detail",
        },
    }


@pytest.fixture(autouse=True)
def _bind_current_toolchain_for_existing_campaign_tests(monkeypatch, request):
    """既存 campaign fixture を、登録 receipt と一致済みの private gate 結果へ束縛する。"""
    if (request.node.cls is not None
            and request.node.cls.__name__ == "TestFloorToolchainBinding") or (
            request.node.name.startswith(
                "test_production_floor_toolchain_preflight_failure"
            )):
        return

    monkeypatch.setattr(
        s8b_floor_campaign, "_bind_current_toolchain", _fixture_toolchain_binding,
    )


def _holdout_entries(holdout_id: str) -> dict:
    entries = {}
    for i, cfg in enumerate(_CONFIGS):
        entry = {
            "holdout_id": holdout_id,
            "label": f"fixture-{holdout_id}-{cfg}",
            "flags": {"BACK_OFF": i % 2, "NO_WAIT_LOCKING_IN_VALIDATION": (i + 1) % 2},
        }
        if cfg == "sort_best":
            entry["comparator"] = _FIXTURE_COMPARATOR
        elif cfg in _FIXTURE_GATE_PREDICATES:
            entry["gate_predicate"] = _FIXTURE_GATE_PREDICATES[cfg]
        entries[cfg] = entry
    return entries


def _freeze_document() -> dict:
    holdouts = {}
    for holdout_id, shape in _HOLDOUT_SHAPE.items():
        holdouts[holdout_id] = {
            "candidate_id": shape["candidate_id"],
            "records": shape["records"],
            "threads": shape["threads"],
            "ycsb": dict(shape["ycsb"]),
            "variant_binding": {"entries": _holdout_entries(holdout_id)},
        }
    return {
        "schema_version": s8b_floor_campaign.FREEZE_SCHEMA,
        "holdouts": holdouts,
    }


def _freeze_sha(freeze: dict) -> str:
    payload = json.dumps(
        freeze, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verified_freeze(freeze: dict) -> VerifiedFreeze:
    return VerifiedFreeze(document=freeze, sha256=_freeze_sha(freeze))


def _protocol(*, freeze_sha: str, master_seed: str = "fixture-seed",
              wired_min_rel_floor: float = 0.05, env_tag: str = ENV_TAG,
              n_sessions: int = 8, reps: int = 5, retry_slots_per_cell: int = 2,
              session_cv_max: str = "0.10", cell_cv_max: str = "0.15",
              scale_adequacy_rel_tolerance: str = "0.10",
              allowed_excluded_reasons=None, schema: str = None,
              formula: str = None, schedule_algorithm: str = None,
              contract_sha256: str = None) -> dict:
    """承認凍結値をデフォルトで返す (validate_protocol を通す)。個別 field を override して
    pin 拒否・版交差拒否を試験する。contract_sha256 は None のとき登録済み env_tag なら実 contract
    から自動導出し、未登録 env_tag では placeholder (0*64) を置く (未登録拒否経路の試験用)。"""
    if contract_sha256 is None:
        try:
            contract_sha256 = ec.lookup(env_tag).contract_sha256
        except ec.EnvContractError:
            contract_sha256 = "0" * 64
    return {
        "schema": schema if schema is not None else s8b_floor_campaign.PROTOCOL_SCHEMA,
        "formula": formula if formula is not None else s8b_floor_stats.FORMULA_ID,
        "env_tag": env_tag,
        "contract_sha256": contract_sha256,
        "ccbench_pin": "0" * 40,
        "freeze": {
            "path": "output/s8b-freeze/holdout_freeze.json",
            "sha256": freeze_sha,
        },
        "stock_configuration": _STOCK,
        "n_sessions": n_sessions,
        "reps": reps,
        "master_seed": master_seed,
        "schedule_algorithm": (schedule_algorithm if schedule_algorithm is not None
                               else s8b_floor_campaign.SCHEDULE_ALGORITHM),
        "extime_s": 5,
        "wired_min_rel_floor": wired_min_rel_floor,
        "retry_slots_per_cell": retry_slots_per_cell,
        "session_cv_max": session_cv_max,
        "cell_cv_max": cell_cv_max,
        "scale_adequacy_rel_tolerance": scale_adequacy_rel_tolerance,
        "allowed_excluded_reasons": (list(allowed_excluded_reasons)
                                     if allowed_excluded_reasons is not None
                                     else list(s8b_floor_stats.ALLOWED_EXCLUDED_REASONS)),
    }


def _valid_protocol_dict(**overrides) -> dict:
    freeze = _freeze_document()
    return _protocol(freeze_sha=_freeze_sha(freeze), **overrides)


# --------------------------------------------------------------------------- #
# prepare_fn / buildcache.build の fake (実ビルドを一切行わない)                #
# --------------------------------------------------------------------------- #

@contextlib.contextmanager
def _fake_prepare(cell, ccbench_pin, *, cxx):
    import tempfile

    entry = cell["variant"]
    holdout_id = entry["holdout_id"]
    configuration_id = cell["configuration"]
    cell_id = f"{holdout_id}::{configuration_id}"
    genome = Genome("silo", dict(entry.get("flags", {})))
    with tempfile.TemporaryDirectory(prefix="s8b-floor-fixture-") as raw_root:
        ccbench = Path(raw_root) / cell_id.replace("::", "__")
        compiler_input = ccbench / "include" / "fixture.hh"
        compiler_input.parent.mkdir(parents=True)
        compiler_input.write_bytes(
            f"compiler-input:{cell_id}\n".encode("utf-8")
        )
        ccbench_dir = str(ccbench)
        token = _fixture_src_token(genome, ccbench_dir)
        _FIXTURE_CELL_BY_TOKEN[token] = cell_id
        _FIXTURE_BUILD_DECLARATION_BY_TOKEN[token] = (
            ccbench_pin, configuration_id, copy.deepcopy(entry),
        )
        yield PreparedCell(
            genome=genome, src_token=token,
            ccbench_dir=ccbench_dir, cache_root="/fixture/cache",
            oracle_attempt=(
                fake_sort_swo_pass_attempt()
                if configuration_id == "sort_best" else None
            ),
        )


_FIXTURE_DEPENDENCY_RECEIPT = {
    "masstree_head": "a" * 40,
    "config_sha256": hashlib.sha256(
        b"fixture-dependency-config"
    ).hexdigest(),
}
_FIXTURE_ARCHIVE_SHA256 = "c" * 64
_FIXTURE_CAPTURED_POLICY_PINS = (
    ("googletest", "c" * 40),
    ("masstree", _FIXTURE_DEPENDENCY_RECEIPT["masstree_head"]),
    ("mimalloc", "b" * 40),
)

_FIXTURE_TOOLCHAIN_MANIFEST = {
    "cc": {
        "requested": "fixture-cc", "realpath": "/fixture/cc",
        "version_first_line": "fixture cc", "version": "fixture cc\ndetail",
    },
    "cxx": {
        "requested": "fixture-cxx", "realpath": "/fixture/cxx",
        "version_first_line": "fixture cxx", "version": "fixture cxx\ndetail",
    },
    "cmake": {
        "requested": "cmake", "realpath": "/fixture/cmake",
        "version_first_line": "cmake fixture", "version": "cmake fixture\ndetail",
    },
}


def _fixture_toolchain_manifest_sha256(manifest=None) -> str:
    return hashlib.sha256(json.dumps(
        manifest or _FIXTURE_TOOLCHAIN_MANIFEST,
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")).hexdigest()


def _make_fake_build(build_root: Path, *, cached: bool = False):
    def fake_build(genome, ccbench_commit, trace, cache_root="", cc=None, cxx=None,
                   jobs=16, ccbench_dir="", src_token=None, contract=None,
                   source_snapshot_sha256=None,
                   expected_materialization_descriptor=None,
                   timeout_s=None, admission=None, build_context=None,
                   source_evidence=None, expected_toolchain_manifest=None,
                   sort_oracle_contract_id=None,
                   fetchcontent_base_dir="", fetchcontent_dependency_receipt=None,
                   fetchcontent_archive_sha256=None,
                   post_oracle_dependency_binding=None,
                   current_compiler_input_masstree_root=None,
                   masstree_source_dir=None, mimalloc_source_dir=None,
                   googletest_source_dir=None):
        del jobs
        assert admission is not None
        assert admission.provenance_class is BuildProvenance.HUMAN_REVIEWED
        assert source_evidence is not None
        assert require_build_admission(
            admission,
            expected_policy=build_context.policy,
            expected_source=source_evidence,
        ) is admission
        assert trace is False, "floor 計測は trace-disabled build (規律1)"
        assert ccbench_dir, "prepare_cell の隔離 ccbench_dir を build_v2 へ渡す"
        assert timeout_s == 900, "floor v2 build hard timeout を固定する"
        assert expected_toolchain_manifest is not None
        assert source_snapshot_sha256 is None
        assert type(expected_materialization_descriptor) is (
            s8b_floor_campaign._expected_materialization.
            ExpectedMaterializationDescriptor
        )
        expected_pin, expected_configuration, expected_entry = (
            _FIXTURE_BUILD_DECLARATION_BY_TOKEN[src_token]
        )
        assert ccbench_commit == expected_pin
        assert expected_materialization_descriptor.ccbench_commit == expected_pin
        assert expected_materialization_descriptor.configuration == (
            expected_configuration
        )
        assert expected_materialization_descriptor.declaration == expected_entry
        expected_template_patch_path = {
            "p2_2_flag_opt": None,
            "backoff_fixed_best": str(
                ROOT / "patches" / "silo-backoff-fixed.patch"
            ),
            "sort_best": str(ROOT / "patches" / "silo-sort-variant.patch"),
            "system_gate": str(
                ROOT / "patches" / "silo-backoff-trigger-gating-variant.patch"
            ),
            "ident_all": str(
                ROOT / "patches" / "silo-backoff-trigger-gating-variant.patch"
            ),
            "stock_common": None,
        }[expected_configuration]
        assert expected_materialization_descriptor.template_patch_path == (
            expected_template_patch_path
        )
        expected_materialization_sha256 = (
            _fixture_expected_materialization_sha256(expected_entry)
        )
        effective_ccbench = ccbench_dir or "/fixture/ccbench"
        # production と同じく渡された cache_root 配下に実体を置き、command には実 root を
        # 埋め込む（portable projection が未結線でも通る fake にしない）。
        cell_id = _FIXTURE_CELL_BY_TOKEN.get(src_token, src_token)
        cell_dir = Path(cache_root) / "fixture" / cell_id.replace("::", "__")
        cell_dir.mkdir(parents=True, exist_ok=True)
        binary_path = cell_dir / "ycsb_fixture.exe"
        payload = f"fixture-binary::{cell_id}".encode("utf-8")
        binary_path.write_bytes(payload)
        bin_sha256 = hashlib.sha256(payload).hexdigest()
        configure_argv = ["cmake", "-S", effective_ccbench, "-B", str(cell_dir)]
        masstree_source_root_sha256 = ""
        if fetchcontent_base_dir:
            assert fetchcontent_dependency_receipt == _FIXTURE_DEPENDENCY_RECEIPT
            assert fetchcontent_archive_sha256 == _FIXTURE_ARCHIVE_SHA256
            configure_argv.append(
                f"-DFETCHCONTENT_BASE_DIR={fetchcontent_base_dir}"
            )
            masstree_source_root_sha256 = hashlib.sha256(
                str(Path(fetchcontent_base_dir) / "masstree-src").encode("utf-8")
            ).hexdigest()
        if current_compiler_input_masstree_root is not None:
            assert Path(current_compiler_input_masstree_root).name == "masstree-src"
        if post_oracle_dependency_binding is not None:
            configure_argv.append("-DFETCHCONTENT_FULLY_DISCONNECTED=ON")
        compiler_input_rel = "include/fixture.hh"
        compiler_input = Path(effective_ccbench) / compiler_input_rel
        if not compiler_input.is_file():
            compiler_input_rel = "CMakeLists.txt"
            compiler_input = Path(effective_ccbench) / compiler_input_rel
        compiler_input_manifest = {
            "schema_version": "s8b-compiler-input/v2",
            "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
            "target": f"ycsb_{genome.protocol}.exe",
            "depfile_count": 1,
            "inputs": [{
                "root": "snapshot",
                "path": compiler_input_rel,
                "sha256": hashlib.sha256(
                    compiler_input.read_bytes()
                ).hexdigest(),
            }],
        }
        compiler_input_manifest_sha256 = hashlib.sha256(json.dumps(
            compiler_input_manifest, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        source_protection = None  # Consumer fixture; no capability issuance.
        return SimpleNamespace(
            genome=genome, trace=trace, binary=str(binary_path),
            source_protection=source_protection,
            bin_sha256=bin_sha256, bin_hash=bin_sha256[:16],
            build_dir=str(cell_dir), cached=cached,
            configure_cmd=f"# fixture configure {cell_id}",
            build_cmd="# fixture build",
            configure_argv=configure_argv,
            build_argv=["cmake", "--build", str(cell_dir)],
            cache_root=str(cache_root), ccbench_root=effective_ccbench,
            contract_sha256=(contract.contract_sha256 if contract is not None else None),
            toolchain_manifest=dict(expected_toolchain_manifest),
            toolchain_manifest_sha256=_fixture_toolchain_manifest_sha256(
                expected_toolchain_manifest
            ),
            compiler_input_manifest=compiler_input_manifest,
            compiler_input_manifest_sha256=(
                compiler_input_manifest_sha256
            ),
            source_snapshot_sha256=expected_materialization_sha256,
            expected_materialization_sha256=expected_materialization_sha256,
            fetchcontent_base_dir=fetchcontent_base_dir,
            masstree_source_root_sha256=masstree_source_root_sha256,
        )
    return fake_build


def _fixture_dependency_binding(base: Path) -> object:
    return s8b_floor_campaign._FloorOracleDependencyBinding(
        source_root=base / "masstree-src",
        expected_head=_FIXTURE_DEPENDENCY_RECEIPT["masstree_head"],
        observed_head=_FIXTURE_DEPENDENCY_RECEIPT["masstree_head"],
        config_sha256=_FIXTURE_DEPENDENCY_RECEIPT["config_sha256"],
        archive_sha256=_FIXTURE_ARCHIVE_SHA256,
        archive_nondebug_sha256=_FIXTURE_ARCHIVE_NONDEBUG_SHA256,
        expected_toolchain_manifest_sha256=(
            _fixture_toolchain_manifest_sha256()
        ),
        source_st_dev=1,
        source_st_ino=2,
        oracle_root=base / "canonical-masstree",
        canonical_lease_root=base / ".sort-swo-dependency-fixture",
        dependency_manifest_sha256=(
            "8d0151cfaa0b86d1a2753e69f514633ec2fe6ee1077caed819fd3a426b501875"
        ),
        expected_config_sha256=_FIXTURE_DEPENDENCY_RECEIPT["config_sha256"],
        expected_archive_nondebug_sha256=(
            _FIXTURE_ARCHIVE_NONDEBUG_SHA256
        ),
        payload_policy_pin=_FIXTURE_DEPENDENCY_RECEIPT["masstree_head"],
        captured_policy_pins=_FIXTURE_CAPTURED_POLICY_PINS,
    )


def _bind_fixture_payload_policy(repo_root: Path, binding: object) -> object:
    policy_path = (
        repo_root / "tools/pegasus/policies/floor_masstree_payload_v1.json"
    )
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "schema_version": "s8b-floor-masstree-payload/v3",
        "name": "masstree",
        "pin": binding.expected_head,
        "config_sha256": binding.expected_config_sha256,
        "archive_projection": "gnu-ar-elf-nondebug/v1",
        "archive_nondebug_sha256": (
            binding.expected_archive_nondebug_sha256
        ),
    }
    policy_path.write_text(
        json.dumps(document, sort_keys=True) + "\n", encoding="utf-8",
    )
    return dataclasses.replace(
        binding,
        payload_policy_sha256=hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        payload_policy_pin=binding.expected_head,
    )


def _fixture_floor_build_result(**kwargs) -> SimpleNamespace:
    # Dependency-postflight unit tests stop before successful receipt issuance.
    return SimpleNamespace(
        source_protection=None,
        toolchain_manifest=dict(_FIXTURE_TOOLCHAIN_MANIFEST),
        toolchain_manifest_sha256=_fixture_toolchain_manifest_sha256(),
        **kwargs,
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("dependency_manifest_sha256", "0" * 64, "manifest hash"),
        ("dependency_config_sha256", "0" * 64, "config.h hash"),
    ],
)
def test_post_oracle_binding_requires_receipt_to_match_canonical_and_source(
        tmp_path, field, value, message):
    dependency = _fixture_dependency_binding(tmp_path)
    attempt = copy.deepcopy(fake_sort_swo_pass_attempt())
    attempt["oracle_receipt"][field] = value

    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match=message):
        s8b_floor_campaign._post_oracle_dependency_binding(
            attempt, dependency,
        )


def _durable_policy(out_root: Path):
    """tmp output を明示注入するテスト専用 allowlist (production 既定は repo output)。"""
    candidate = Path(out_root).absolute()
    approved = candidate
    while not approved.exists():
        approved = approved.parent
    return s8b_floor_campaign.DurableRootPolicy(
        approved_roots=(approved.resolve(),), forbidden_roots=(),
    )


def _perf_receipt(*, available=True):
    events = ["LLC-load-misses", "LLC-loads", "instructions", "cycles"]
    return {
        "schema": "izanagi-perf-preflight/v1",
        "status": "available" if available else "unavailable",
        "available": available,
        "probe_argv": [
            "perf", "stat", "-x,", "-o", "<tmp>/perf.csv",
            "-e", ",".join(events), "--", "/bin/true",
        ],
        "rc": 0 if available else 2,
        "parsed_events": events if available else [],
        "reason": "available" if available else "nonzero-rc",
        "stderr_sha256": hashlib.sha256(b"").hexdigest(),
        "candidates": [],
    }


def _perf_preflight_journal_record(*, available=True):
    return {
        "event": "perf-preflight",
        "schema": s8b_floor_campaign.JOURNAL_SCHEMA,
        "perf_preflight_receipt": _perf_receipt(available=available),
    }


def _probe_error_perf_receipt():
    receipt = _perf_receipt(available=False)
    receipt.update({
        "status": "probe_error", "rc": None,
        "reason": "probe-timeout", "parsed_events": [],
    })
    return receipt


def _cell_id_from_binary(binary: str) -> str:
    return Path(binary).parent.name.replace("__", "::")


def _test_holdout_authority(out_root: Path, protocol, freeze_doc) -> Path:
    """Resolve tests to a real Git authority without disabling any gate."""

    out_root = Path(out_root)
    authority = out_root.parent / f".{out_root.name}-holdout-authority"
    if authority.exists():
        return authority
    authority.mkdir(parents=True)
    subprocess.run(
        ["git", "-C", str(authority), "init"], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    fixed = authority / "output" / "s8b-freeze"
    fixed.mkdir(parents=True)
    # _protocol() and the callers that prevalidate already supply canonical
    # protocol mappings. Re-resolving through the production historical
    # registry would bypass a test-installed current contract.
    normalized = dict(protocol)
    (fixed / "floor_protocol.json").write_bytes(
        json.dumps(
            normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
    )
    (fixed / "holdout_freeze.json").write_bytes(
        json.dumps(
            freeze_doc.document, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    subprocess.run(
        ["git", "-C", str(authority), "add", "output/s8b-freeze"], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    subprocess.run(
        ["git", "-C", str(authority), "-c", "user.name=fixture", "-c",
         "user.email=fixture@example.invalid", "commit", "-m", "fixture authority"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return authority


def _private_run_campaign(protocol, freeze_doc, **kwargs):
    authority = (
        _test_holdout_authority(kwargs["out_root"], protocol, freeze_doc)
        if "durable_root_policy" in kwargs else ROOT
    )
    if kwargs.get("mode") == "official":
        kwargs.setdefault("confirm_official_floor_run", True)
    return s8b_floor_campaign._run_campaign_core(
        protocol, freeze_doc,
        _holdout_repo_root=authority,
        _holdout_signature_source=freeze_doc.document["holdouts"],
        **kwargs,
    )


def _run_campaign(protocol, freeze_doc, *, out_root, build_root, measure_fn, probe_fn,
                  mode="pilot", resume_dir=None, sleep_fn=None, monotonic_fn=None,
                  now_fn=None, perf_preflight_fn=None, prepare_fn=_fake_prepare):
    fake_build = _make_fake_build(build_root)
    entrypoint = s8b_floor_campaign._run_campaign_core
    extra = (
        {"_floor_preflight_fn": _fixture_floor_preflight}
        if mode == "official" and resume_dir is None else {}
    )
    kwargs = dict(
        out_root=out_root, mode=mode, resume_dir=resume_dir,
        measure_fn=measure_fn, probe_fn=probe_fn,
        sleep_fn=sleep_fn or (lambda s: None),
        monotonic_fn=monotonic_fn or (lambda: 0.0),
        prepare_fn=prepare_fn, now_fn=now_fn or (lambda: _FIXED_NOW),
        durable_root_policy=_durable_policy(Path(out_root)),
        **extra,
    )
    kwargs["_holdout_repo_root"] = _test_holdout_authority(
        Path(out_root), protocol, freeze_doc,
    )
    kwargs["_holdout_signature_source"] = freeze_doc.document["holdouts"]
    if mode == "official":
        kwargs["confirm_official_floor_run"] = True
        official_preflight = (
            perf_preflight_fn or (lambda **_kwargs: _perf_receipt(available=True))
        )
        with mock.patch.object(s8b_floor_campaign.buildcache, "build_v2", fake_build), \
                mock.patch.object(
                    s8b_floor_campaign._perf_preflight,
                    "probe_perf_availability", official_preflight,
                ):
            return entrypoint(protocol, freeze_doc, **kwargs)
    kwargs["perf_preflight_fn"] = (
        perf_preflight_fn or (lambda **_kwargs: _perf_receipt())
    )
    return entrypoint(protocol, freeze_doc, build_fn=fake_build, **kwargs)


def _live_holdout_admission_for_outcome(
        *, protocol, freeze_doc, out_root: Path, outcome: dict) -> dict:
    """artifact 自己申告でなく test authority の live evidence を再検査する。"""
    validated_protocol = s8b_floor_campaign.validate_protocol(protocol)
    cells = s8b_floor_campaign.enumerate_cells(
        freeze_doc.document,
        stock_configuration=validated_protocol["stock_configuration"],
    )
    run_dir = Path(outcome["run_dir"])
    manifest_sha256 = hashlib.sha256(
        (run_dir / "manifest.json").read_bytes()
    ).hexdigest()
    authority = _test_holdout_authority(out_root, protocol, freeze_doc)
    journal_records = [
        json.loads(line)
        for line in (run_dir / "journal.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return s8b_floor_campaign._holdout_admission.inspect_floor_holdout_admission_evidence(
        repo_root=authority,
        protocol=validated_protocol,
        verified_freeze_document=freeze_doc.document,
        freeze_sha256=freeze_doc.sha256,
        manifest_sha256=manifest_sha256,
        campaign_run_id=run_dir.name,
        run_relpath=run_dir.relative_to(out_root).as_posix(),
        mode=outcome["result"]["mode"],
        cells=cells,
        schedule=s8b_floor_campaign.build_schedule(
            cells=cells,
            master_seed=validated_protocol["master_seed"],
            n_sessions=validated_protocol["n_sessions"],
        ),
        sessions=[
            record for record in journal_records
            if record.get("event") in {"session-start", "session"}
        ],
    )


def _fixture_floor_preflight(
        root, *, freeze_path, freeze_sha256, protocol_sha256):
    """prediction 順序以外を検査する private-core テスト用の引数注入 seam。"""
    return {s8b_floor_campaign._HOLDOUT_FREEZE_REL: freeze_sha256}


# --------------------------------------------------------------------------- #
# measure_fn の fake (決定的、reps 本の throughput を返す)                      #
# --------------------------------------------------------------------------- #

class _FakeScalePoint:
    def __init__(self, throughputs, notes, run_cmd, *, rep_observations=None,
                 reps=5, use_perf=None):
        self.throughputs = list(throughputs)
        self.notes = list(notes)
        self.run_cmd = run_cmd
        if use_perf is None:
            use_perf = " perf " in f" {run_cmd} "
        if rep_observations is None:
            raw_values = list(throughputs) + [None] * max(0, reps - len(throughputs))
            perf_raw = (
                {event: index + 1 for index, event in enumerate(
                    s8b_floor_stats.PERF_EVENTS)}
                if use_perf else
                {event: None for event in s8b_floor_stats.PERF_EVENTS}
            )
            status = "complete" if use_perf else "not_required"
            rep_observations = [
                {
                    "rep_index": index, "returncode": 0,
                    "execution_failure": False,
                    "counter_status": status, "missing_perf_events": [],
                    "perf_raw": dict(perf_raw), "throughput": raw_values[index],
                }
                for index in range(reps)
            ]
        self.rep_observations = list(rep_observations)


def _shape_faithful_run_cmd(
        binary, records, threads, workload, *, env_tag=ENV_TAG, extime_s=5,
        use_perf=True) -> str:
    """production repro_command と同じ argv shape の runtime-path fake を返す。"""
    contract = ec.lookup(env_tag)
    argv = list(s8b_floor_campaign.build_portable_run_cmd(
        binary="output/fixture/bench", workload=workload, records=records,
        threads=threads, extime_s=extime_s, clocks_per_us=contract.clocks_per_us,
        numactl=contract.numactl, use_perf=use_perf,
    ))
    binary_index = argv.index("--") + 1 if use_perf else len(contract.numactl)
    argv[binary_index] = str(binary)
    return shlex.join(argv)


def _make_measure_fn(reps, value_fn, *, raise_for=(), partial_for=(), partial_reps=None,
                     reps_fn=None, env_tag=ENV_TAG, extime_s=5, use_perf=True):
    raise_for = set(raise_for)
    partial_for = set(partial_for)
    calls: list = []
    call_details: list = []

    def measure_fn(binary, records, threads, workload):
        cell_id = _cell_id_from_binary(binary)
        calls.append(cell_id)
        call_details.append({
            "cell_id": cell_id,
            "records": records,
            "threads": threads,
            "workload": dict(workload),
        })
        if cell_id in raise_for:
            raise RuntimeError(f"fixture: 実行不能を模す ({cell_id})")
        if reps_fn is not None:
            values = reps_fn(cell_id)
            return _FakeScalePoint(throughputs=list(values), notes=[],
                                   run_cmd=_shape_faithful_run_cmd(
                                       binary, records, threads, workload,
                                       env_tag=env_tag, extime_s=extime_s,
                                       use_perf=use_perf))
        n = reps
        if cell_id in partial_for:
            n = partial_reps if partial_reps is not None else max(reps - 1, 0)
        base = value_fn(cell_id)
        return _FakeScalePoint(
            throughputs=[base] * n, notes=[],
            run_cmd=_shape_faithful_run_cmd(
                binary, records, threads, workload,
                env_tag=env_tag, extime_s=extime_s, use_perf=use_perf,
            ),
        )

    measure_fn.calls = calls
    measure_fn.call_details = call_details
    return measure_fn


def _only_run_dir(out_root: Path) -> Path:
    manifests = list(out_root.rglob("manifest.json"))
    assert len(manifests) == 1, manifests
    return manifests[0].parent


def test_measure_run_cmd_projection_removes_runtime_root_and_rejects_missing_token(tmp_path):
    freeze = _freeze_document()
    protocol = s8b_floor_campaign.validate_protocol(
        _protocol(freeze_sha=_freeze_sha(freeze)))
    cell = next(iter(_HOLDOUT_SHAPE.values()))
    runtime_binary = str(tmp_path / "runtime root" / "bench")
    portable_binary = "env/fixture/binaries/hash/bench"
    raw = _shape_faithful_run_cmd(
        runtime_binary, cell["records"], cell["threads"], cell["ycsb"])
    projected = s8b_floor_campaign._project_measure_run_cmd(
        raw, runtime_binary=runtime_binary, portable_binary=portable_binary,
        workload=cell["ycsb"], records=cell["records"], threads=cell["threads"],
        protocol=protocol, contract=ec.lookup(ENV_TAG),
    )
    assert runtime_binary not in projected
    assert tuple(shlex.split(projected)) == s8b_floor_campaign.build_portable_run_cmd(
        binary=portable_binary, workload=cell["ycsb"], records=cell["records"],
        threads=cell["threads"], extime_s=protocol["extime_s"],
        clocks_per_us=ec.lookup(ENV_TAG).clocks_per_us,
        numactl=ec.lookup(ENV_TAG).numactl,
    )
    missing = shlex.join(shlex.split(raw)[:-1])
    with pytest.raises(s8b_floor_campaign.CampaignAbort, match="不一致"):
        s8b_floor_campaign._project_measure_run_cmd(
            missing, runtime_binary=runtime_binary, portable_binary=portable_binary,
            workload=cell["ycsb"], records=cell["records"], threads=cell["threads"],
            protocol=protocol, contract=ec.lookup(ENV_TAG),
        )


@pytest.mark.parametrize(
    "receipt_available,raw_uses_perf",
    [
        pytest.param(False, True, id="unavailable-rejects-perf-shape"),
        pytest.param(True, False, id="available-rejects-direct-shape"),
    ],
)
def test_measure_run_cmd_rejects_shape_opposite_to_recorded_preflight(
        tmp_path, monkeypatch, receipt_available, raw_uses_perf):
    freeze = _freeze_document()
    protocol = s8b_floor_campaign.validate_protocol(
        _protocol(freeze_sha=_freeze_sha(freeze)))
    cell = next(iter(_HOLDOUT_SHAPE.values()))
    contract = ec.lookup(ENV_TAG)
    runtime_binary = str(tmp_path / "bench")
    portable_binary = "env/fixture/binaries/hash/bench"

    def fixed_shape(binary, *, use_perf):
        argv = list(contract.numactl)
        if use_perf:
            argv.extend([
                "perf", "stat", "-e",
                "LLC-load-misses,LLC-loads,instructions,cycles", "--",
            ])
        argv.extend([
            binary,
            f"-thread_num={cell['threads']}",
            f"-ycsb_tuple_num={cell['records']}",
            f"-extime={protocol['extime_s']}",
            f"-clocks_per_us={contract.clocks_per_us}",
        ])
        argv.extend(f"-{key}={cell['ycsb'][key]}" for key in sorted(cell["ycsb"]))
        return tuple(argv)

    expected_uses_perf = receipt_available
    portable = fixed_shape(portable_binary, use_perf=expected_uses_perf)
    raw = shlex.join(fixed_shape(runtime_binary, use_perf=raw_uses_perf))

    def fixed_portable_builder(**kwargs):
        assert kwargs["use_perf"] is expected_uses_perf
        return portable

    monkeypatch.setattr(
        s8b_floor_campaign, "build_portable_run_cmd", fixed_portable_builder,
    )

    with pytest.raises(s8b_floor_campaign.CampaignAbort, match="不一致"):
        s8b_floor_campaign._project_measure_run_cmd(
            raw, runtime_binary=runtime_binary, portable_binary=portable_binary,
            workload=cell["ycsb"], records=cell["records"], threads=cell["threads"],
            protocol=protocol, contract=contract,
            perf_preflight=_perf_receipt(available=receipt_available), mode="pilot",
        )


def test_measure_run_cmd_accepts_unavailable_receipt_in_official_mode(tmp_path):
    freeze = _freeze_document()
    protocol = s8b_floor_campaign.validate_protocol(
        _protocol(freeze_sha=_freeze_sha(freeze)))
    cell = next(iter(_HOLDOUT_SHAPE.values()))
    contract = ec.lookup(ENV_TAG)
    runtime_binary = str(tmp_path / "bench")
    portable_binary = "env/fixture/binaries/hash/bench"
    direct_raw = _shape_faithful_run_cmd(
        runtime_binary, cell["records"], cell["threads"], cell["ycsb"],
        use_perf=False,
    )

    projected = s8b_floor_campaign._project_measure_run_cmd(
        direct_raw, runtime_binary=runtime_binary, portable_binary=portable_binary,
        workload=cell["ycsb"], records=cell["records"], threads=cell["threads"],
        protocol=protocol, contract=contract,
        perf_preflight=_perf_receipt(available=False),
        mode="official",
    )
    assert tuple(shlex.split(projected)) == s8b_floor_campaign.build_portable_run_cmd(
        binary=portable_binary, workload=cell["ycsb"], records=cell["records"],
        threads=cell["threads"], extime_s=protocol["extime_s"],
        clocks_per_us=contract.clocks_per_us, numactl=contract.numactl,
        use_perf=False,
    )


def test_official_perf_mode_rejects_only_explicit_available_receipt():
    assert s8b_floor_campaign._assert_perf_mode("official", None) is True
    assert s8b_floor_campaign._assert_perf_mode(
        "official", _perf_receipt(available=False),
    ) is False
    with pytest.raises(s8b_floor_campaign.CampaignAbort, match="available"):
        s8b_floor_campaign._assert_perf_mode(
            "official", _perf_receipt(available=True),
        )


def test_probed_official_available_projects_to_legacy_none():
    assert s8b_floor_campaign._project_probed_perf_preflight(
        "official", _perf_receipt(available=True),
    ) is None
    unavailable = s8b_floor_campaign._project_probed_perf_preflight(
        "official", _perf_receipt(available=False),
    )
    assert unavailable == _perf_receipt(available=False)
    assert s8b_floor_campaign._project_probed_perf_preflight(
        "pilot", _perf_receipt(available=True),
    ) == _perf_receipt(available=True)


def test_assemble_manifest_has_independent_official_available_gate(monkeypatch):
    """M6: A を通す seam の下でも manifest producer 自身が available を拒否する。"""
    monkeypatch.setattr(
        s8b_floor_campaign, "_assert_perf_mode", lambda _mode, _receipt: True,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_validate_binaries_cover_cells",
        lambda _built, _cells: None,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_validate_portable_built",
        lambda _built, **_kwargs: {},
    )
    with pytest.raises(s8b_floor_campaign.CampaignAbort, match="official manifest"):
        s8b_floor_campaign.assemble_manifest(
            protocol={
                "freeze": {"path": "freeze.json", "sha256": "3" * 64},
                "env_tag": "fixture-env", "ccbench_pin": "0" * 40,
                "contract_sha256": "1" * 64,
                "stock_configuration": "stock",
                "schedule_algorithm": "round-permutation/v2",
                "master_seed": "seed", "n_sessions": 1, "reps": 1,
                "extime_s": 1, "session_cv_max": "0.1", "cell_cv_max": "0.1",
            },
            protocol_sha256="2" * 64, freeze_sha256="3" * 64,
            cells=[], built={}, schedule=[],
            perf_preflight=_perf_receipt(available=True), mode="official",
        )


def test_perf_unavailable_continues_and_records_one_run_receipt(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    calls = []

    def preflight(**kwargs):
        calls.append(kwargs)
        return _perf_receipt(available=False)

    outcome = _run_campaign(
        protocol, verified, out_root=tmp_path / "out", build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(
            reps=5, value_fn=lambda cid: _BASE_TPS[cid], use_perf=False),
        probe_fn=lambda: (1, "", ""), perf_preflight_fn=preflight,
    )
    assert len(calls) == 1
    assert calls[0]["perf_candidates"]
    run_dir = Path(outcome["run_dir"])
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["perf_preflight"] == outcome["result"]["perf_preflight"]
    assert manifest["perf_preflight"]["available"] is False
    assert "perf_observation" not in manifest
    assert "perf_observation" not in outcome["result"]
    assert all(" perf " not in f" {record['run_cmd']} "
               for record in outcome["result"]["sessions"])
    receipt = outcome["result"]["perf_preflight"]
    receipt_digest = hashlib.sha256(json.dumps(
        receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")).hexdigest()
    perf_lines = [
        line for line in (run_dir / "result.md").read_text(
            encoding="utf-8").splitlines()
        if line.startswith("- perf:")
    ]
    assert perf_lines == [
        f"- perf: mode=disabled, reason=nonzero-rc, "
        f"receipt_sha256=`{receipt_digest}`"
    ]


def test_fresh_build_failure_persists_perf_preflight_journal_receipt(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"

    def raising_build(*_args, **_kwargs):
        raise RuntimeError("fixture build crash")

    monkeypatch.setattr(s8b_floor_campaign, "build_cells", raising_build)
    with pytest.raises(RuntimeError, match="build crash"):
        _run_campaign(
            protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
            measure_fn=_forbid_measure, probe_fn=lambda: (1, "", ""),
            perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
        )

    journals = list(out_root.rglob("journal.jsonl"))
    assert len(journals) == 1
    records = _read_journal_lines(journals[0])
    assert records == [_perf_preflight_journal_record(available=False)]
    assert not (journals[0].parent / "manifest.json").exists()
    assert not (journals[0].parent / "result.json").exists()


def test_pilot_available_build_failure_persists_perf_preflight_journal_receipt(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"

    def raising_build(*_args, **_kwargs):
        raise RuntimeError("fixture available build crash")

    monkeypatch.setattr(s8b_floor_campaign, "build_cells", raising_build)
    with pytest.raises(RuntimeError, match="available build crash"):
        _run_campaign(
            protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
            measure_fn=_forbid_measure, probe_fn=lambda: (1, "", ""),
            perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=True),
        )

    journal_path = next(out_root.rglob("journal.jsonl"))
    assert _read_journal_lines(journal_path) == [
        _perf_preflight_journal_record(available=True)
    ]


def test_fresh_build_failure_persists_perf_preflight_with_external_checkpoint_binding(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    binding = {
        "path": str(tmp_path / "checkpoint.jsonl"),
        "job_id": "fixture-job",
        "nonce": "fixture-nonce",
    }
    checkpoint_calls = []

    monkeypatch.setattr(
        s8b_floor_campaign.floor_job_checkpoint,
        "take_checkpoint_environment",
        lambda _environ: dict(binding),
    )
    monkeypatch.setattr(
        s8b_floor_campaign.floor_job_checkpoint,
        "try_append_checkpoint_bounded",
        lambda **kwargs: checkpoint_calls.append(kwargs),
    )
    monkeypatch.setattr(
        s8b_floor_campaign,
        "build_cells",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("fixture checkpoint build crash")
        ),
    )
    with pytest.raises(RuntimeError, match="checkpoint build crash"):
        _run_campaign(
            protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
            measure_fn=_forbid_measure, probe_fn=lambda: (1, "", ""),
            perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
        )

    assert len(checkpoint_calls) == 1
    assert checkpoint_calls[0]["path"] == binding["path"]
    assert checkpoint_calls[0]["job_id"] == binding["job_id"]
    assert checkpoint_calls[0]["nonce"] == binding["nonce"]
    journal_path = next(out_root.rglob("journal.jsonl"))
    assert _read_journal_lines(journal_path) == [
        _perf_preflight_journal_record(available=False)
    ]


def test_perf_preflight_journal_record_is_outside_certified_artifacts(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    outcome = _run_campaign(
        protocol, verified, out_root=tmp_path / "out", build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(
            reps=5, value_fn=lambda cid: _BASE_TPS[cid], use_perf=False,
        ),
        probe_fn=lambda: (1, "", ""),
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
    )
    run_dir = Path(outcome["run_dir"])
    journal_record = next(
        record for record in _read_journal_lines(run_dir / "journal.jsonl")
        if record.get("event") == "perf-preflight"
    )
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    result = outcome["result"]
    assert set(manifest) == set(s8b_floor_contract.manifest_keys_for_mode(
        "pilot", perf_preflight=manifest.get("perf_preflight"),
    ))
    assert set(result) == set(s8b_floor_contract.result_keys_for_mode(
        "pilot", perf_preflight=result.get("perf_preflight"),
    ))
    assert set(journal_record) != set(manifest)
    assert set(journal_record) != set(result)
    assert "perf_preflight_receipt" not in manifest
    assert "perf_preflight_receipt" not in result
    assert all(
        record.get("event") != "perf-preflight"
        for record in result["wall_ledger"]
    )

    unavailable_observation = calibrator_perf_preflight.build_perf_observation(
        _perf_receipt(available=False), run_cmd=("bench",),
        leading_indicators={"ipc": None, "llc_miss_rate": None},
    )
    assert calibrator_perf_preflight.perf_claim_allowed(
        unavailable_observation, "perf_required", run_cmd=("bench",),
        leading_indicators={"ipc": None, "llc_miss_rate": None},
    ) is False
    available_observation = calibrator_perf_preflight.build_perf_observation(
        _perf_receipt(available=True), run_cmd=("bench",),
        leading_indicators={"ipc": 1.0, "llc_miss_rate": 0.1},
    )
    assert calibrator_perf_preflight.perf_claim_allowed(
        available_observation, "perf_required", run_cmd=("bench",),
        leading_indicators={"ipc": 1.0, "llc_miss_rate": 0.1},
    ) is True
    with pytest.raises(calibrator_perf_preflight.PerfPreflightError):
        calibrator_perf_preflight.perf_claim_allowed(
            journal_record, "perf_required", run_cmd=("bench",),
            leading_indicators={"ipc": None, "llc_miss_rate": None},
        )


def test_perf_preflight_journal_record_is_trace_lane_agnostic(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    build_trace_values = []
    fake_build = _make_fake_build(tmp_path / "bin")

    def build_spy(*args, **kwargs):
        build_trace_values.append(kwargs["trace"])
        return fake_build(*args, **kwargs)

    outcome = _private_run_campaign(
        protocol, verified, out_root=tmp_path / "out", mode="pilot",
        measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
        probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
        monotonic_fn=lambda: 0.0, prepare_fn=_fake_prepare, now_fn=lambda: _FIXED_NOW,
        host_provenance_fn=_fixed_host, process_identity_fn=_fixed_process,
        execution_receipt_fn=_fixed_receipt, build_fn=build_spy,
        durable_root_policy=_durable_policy(tmp_path / "out"),
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=True),
    )
    assert build_trace_values and set(build_trace_values) == {False}
    journal_record = next(
        record for record in _read_journal_lines(Path(outcome["run_dir"]) / "journal.jsonl")
        if record.get("event") == "perf-preflight"
    )
    assert not {"trace", "use_perf", "claim_scope"} & set(journal_record)


def test_perf_preflight_journal_record_has_no_lane_fields_after_success(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    outcome = _private_run_campaign(
        protocol, verified, out_root=out_root, mode="pilot",
        measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
        probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
        monotonic_fn=lambda: 0.0, prepare_fn=_fake_prepare, now_fn=lambda: _FIXED_NOW,
        host_provenance_fn=_fixed_host, process_identity_fn=_fixed_process,
        execution_receipt_fn=_fixed_receipt,
        build_fn=_make_fake_build(tmp_path / "bin"),
        durable_root_policy=_durable_policy(out_root),
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=True),
    )
    journal_record = next(
        record for record in _read_journal_lines(Path(outcome["run_dir"]) / "journal.jsonl")
        if record.get("event") == "perf-preflight"
    )
    assert not {"trace", "use_perf", "claim_scope"} & set(journal_record)


def test_perf_preflight_journal_record_has_no_lane_fields_after_build_failure(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"

    def raising_build(*_args, **_kwargs):
        raise RuntimeError("fixture trace-lane build crash")

    monkeypatch.setattr(s8b_floor_campaign, "build_cells", raising_build)
    with pytest.raises(RuntimeError, match="trace-lane build crash"):
        _run_campaign(
            protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
            measure_fn=_forbid_measure, probe_fn=lambda: (1, "", ""),
            perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
        )
    journal_path = next(out_root.rglob("journal.jsonl"))
    journal_record = next(
        record for record in _read_journal_lines(journal_path)
        if record.get("event") == "perf-preflight"
    )
    assert not {"trace", "use_perf", "claim_scope"} & set(journal_record)


def test_official_unavailable_preflight_reaches_measurement_once(tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    calls = []

    def preflight(**kwargs):
        calls.append(kwargs)
        return _perf_receipt(available=False)

    with _official_test_seam(monkeypatch):
        outcome = _run_campaign(
            protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
            build_root=tmp_path / "bin", mode="official",
            measure_fn=_make_measure_fn(
                reps=5, value_fn=lambda cid: _BASE_TPS[cid], use_perf=False,
            ),
            probe_fn=lambda: (1, "", ""), perf_preflight_fn=preflight,
        )
    assert len(calls) == 1
    manifest = json.loads(
        (Path(outcome["run_dir"]) / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["perf_preflight"] == outcome["result"]["perf_preflight"]
    assert manifest["perf_observation"] == outcome["result"]["perf_observation"]
    assert all(
        " perf " not in f" {record['run_cmd']} "
        for record in outcome["result"]["sessions"]
    )


def test_perf_available_records_receipt_and_preserves_perf_shape(tmp_path):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    outcome = _run_campaign(
        protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
        build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
        probe_fn=lambda: (1, "", ""),
    )
    receipt = outcome["result"]["perf_preflight"]
    assert receipt["available"] is True
    assert all(" perf " in f" {record['run_cmd']} "
               for record in outcome["result"]["sessions"])
    receipt_digest = hashlib.sha256(json.dumps(
        receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")).hexdigest()
    run_dir = Path(outcome["run_dir"])
    perf_lines = [
        line for line in (run_dir / "result.md").read_text(
            encoding="utf-8").splitlines()
        if line.startswith("- perf:")
    ]
    assert perf_lines == [
        f"- perf: mode=enabled, reason=available, "
        f"receipt_sha256=`{receipt_digest}`"
    ]


def test_pilot_default_perf_preflight_delegate_is_resolved_once_at_call_time(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    seen = []

    def preflight_spy(**kwargs):
        seen.append(kwargs)
        return _perf_receipt()

    monkeypatch.setattr(
        s8b_floor_campaign._perf_preflight,
        "probe_perf_availability", preflight_spy,
    )
    outcome = _private_run_campaign(
        protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
        mode="pilot",
        measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
        probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
        monotonic_fn=lambda: 0.0, prepare_fn=_fake_prepare,
        now_fn=lambda: _FIXED_NOW, host_provenance_fn=_fixed_host,
        process_identity_fn=_fixed_process, execution_receipt_fn=_fixed_receipt,
        build_fn=_make_fake_build(tmp_path / "bin"),
        durable_root_policy=_durable_policy(tmp_path / "out"),
    )
    assert outcome["status"] == "completed"
    assert len(seen) == 1
    assert seen[0]["perf_candidates"]


def test_perf_probe_error_aborts_before_build_or_manifest(tmp_path):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="判定不能"):
        _run_campaign(
            protocol, _verified_freeze(freeze), out_root=out_root,
            build_root=tmp_path / "bin", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""),
            perf_preflight_fn=lambda **_kwargs: _probe_error_perf_receipt(),
        )
    assert list(out_root.rglob("manifest.json")) == []
    assert not (tmp_path / "bin").exists()


def test_resume_reuses_manifest_perf_preflight_without_reprobing(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    calls = {"measure": 0, "preflight": 0}

    def preflight(**_kwargs):
        calls["preflight"] += 1
        return _perf_receipt(available=False)

    def crashing_measure(binary, records, threads, workload):
        calls["measure"] += 1
        if calls["measure"] == 2:
            raise _SimulatedCrash("preflight resume fixture")
        cell_id = _cell_id_from_binary(binary)
        return _FakeScalePoint(
            [_BASE_TPS[cell_id]] * 5, [],
            _shape_faithful_run_cmd(
                binary, records, threads, workload, use_perf=False),
        )

    with pytest.raises(_SimulatedCrash):
        _run_campaign(
            protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
            measure_fn=crashing_measure, probe_fn=lambda: (1, "", ""),
            perf_preflight_fn=preflight,
        )
    run_dir = _only_run_dir(out_root)

    def forbid_reprobe(**_kwargs):
        raise AssertionError("既存 manifest resume で再 probe してはいけない")

    outcome = _run_campaign(
        protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(
            reps=5, value_fn=lambda cid: _BASE_TPS[cid], use_perf=False),
        probe_fn=lambda: (1, "", ""), resume_dir=run_dir,
        perf_preflight_fn=forbid_reprobe,
    )
    assert calls["preflight"] == 1
    assert outcome["result"]["perf_preflight"]["available"] is False


def test_resume_allows_pre_measure_v2_journal_transition(tmp_path):
    """P2: session-start/session のない v2 journal は過剰拒否しない。"""
    records = [{
        "event": "campaign-start", "schema": "s8b-floor-journal/v2",
        "protocol_sha256": "p", "freeze_sha256": "f", "manifest_sha256": "m",
    }]
    result = s8b_floor_campaign._verify_resume_journal(
        records, run_dir=tmp_path, mode="pilot",
        schedule=[{"seq": 0, "round": 1, "cell_id": "H::C"}],
        protocol_sha256="p", freeze_sha256="f", manifest_sha256="m",
        resume_state="M-running", expected_use_perf=True,
        retry_slots_per_cell=2,
    )
    assert result is None
    journal = tmp_path / "journal.jsonl"
    journal.write_text(json.dumps(records[0]) + "\n", encoding="utf-8")
    s8b_floor_campaign._transition_pre_measure_journal_to_v3(journal, records)
    assert records[0]["schema"] == s8b_floor_campaign.JOURNAL_SCHEMA
    assert json.loads(journal.read_text(encoding="utf-8"))["schema"] == \
        s8b_floor_campaign.JOURNAL_SCHEMA


@pytest.mark.parametrize("event", ["session-start", "session"])
def test_resume_rejects_v2_once_measurement_event_exists(tmp_path, event):
    records = [
        {
            "event": "campaign-start", "schema": "s8b-floor-journal/v2",
            "protocol_sha256": "p", "freeze_sha256": "f", "manifest_sha256": "m",
        },
        {"event": event},
    ]
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="証跡を復元不能"):
        s8b_floor_campaign._verify_resume_journal(
            records, run_dir=tmp_path, mode="pilot", schedule=[],
            protocol_sha256="p", freeze_sha256="f", manifest_sha256="m",
            resume_state="M-running", expected_use_perf=True,
            retry_slots_per_cell=2,
        )


def test_resume_v3_rejects_session_without_rep_integrity_evidence(tmp_path):
    """M13: v3 session の observation 欠落を count 0 で補わない。"""
    records = [
        {
            "event": "campaign-start", "schema": s8b_floor_campaign.JOURNAL_SCHEMA,
            "protocol_sha256": "p", "freeze_sha256": "f", "manifest_sha256": "m",
        },
        {
            "event": "session-start", "seq": 0, "kind": "planned",
            "cell_id": "H::C", "round": 1, "retry_ordinal": None,
            "attempt_id": "H::C::seq0", "trigger": None,
        },
        {
            "event": "session", "seq": 0, "kind": "planned", "cell_id": "H::C",
            "round": 1, "throughputs": [1, 1, 1, 1, 1], "reps_expected": 5,
            "excluded_reason": None, "run_cmd": "bench",
        },
    ]
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="rep 証跡 key 欠損"):
        s8b_floor_campaign._verify_resume_journal(
            records, run_dir=tmp_path, mode="pilot",
            schedule=[{"seq": 0, "round": 1, "cell_id": "H::C"}],
            protocol_sha256="p", freeze_sha256="f", manifest_sha256="m",
            resume_state="M-running", expected_use_perf=True,
            retry_slots_per_cell=2,
        )


def _resume_records_with_complete_rep_evidence():
    point = _FakeScalePoint(
        [1, 1, 1, 1, 1], [], "numactl bench", use_perf=False,
    )
    return [
        {
            "event": "campaign-start", "schema": s8b_floor_campaign.JOURNAL_SCHEMA,
            "protocol_sha256": "p", "freeze_sha256": "f", "manifest_sha256": "m",
        },
        {
            "event": "session-start", "seq": 0, "kind": "planned",
            "cell_id": "H::C", "round": 1, "retry_ordinal": None,
            "attempt_id": "H::C::seq0", "trigger": None,
        },
        {
            "event": "session", "seq": 0, "kind": "planned",
            "cell_id": "H::C", "holdout_id": "H", "configuration_id": "C",
            "round": 1, "throughputs": [1, 1, 1, 1, 1], "reps_expected": 5,
            "exec_failures": 0, "excluded_reason": None, "retry": False,
            "rep_observations": copy.deepcopy(point.rep_observations),
            "rep_integrity_failures": 0, "exclusion_class": None,
            "run_cmd": "numactl bench", "session_median": 1,
            "valid": True, "probe_before": {"competing": False},
            "probe_after": {"competing": False},
        },
    ]


def test_resume_rejects_exec_failure_count_mismatch(tmp_path):
    records = _resume_records_with_complete_rep_evidence()
    records[-1]["exec_failures"] = 1
    with pytest.raises(
        s8b_floor_campaign.FloorCampaignError,
        match="exec_failures が再導出値と不一致",
    ):
        s8b_floor_campaign._verify_resume_journal(
            records, run_dir=tmp_path, mode="pilot",
            schedule=[{"seq": 0, "round": 1, "cell_id": "H::C"}],
            protocol_sha256="p", freeze_sha256="f", manifest_sha256="m",
            resume_state="M-running", expected_use_perf=False,
            retry_slots_per_cell=2,
        )


def test_resume_rejects_old_six_key_rep_observation(tmp_path):
    records = _resume_records_with_complete_rep_evidence()
    records[-1]["rep_observations"][0].pop("execution_failure")
    with pytest.raises(
        s8b_floor_campaign.FloorCampaignError,
        match="exact key 不一致",
    ):
        s8b_floor_campaign._verify_resume_journal(
            records, run_dir=tmp_path, mode="pilot",
            schedule=[{"seq": 0, "round": 1, "cell_id": "H::C"}],
            protocol_sha256="p", freeze_sha256="f", manifest_sha256="m",
            resume_state="M-running", expected_use_perf=False,
            retry_slots_per_cell=2,
        )


def test_production_use_perf_keyword_call_sites_are_a_closed_set():
    """受理: 名指しした production site だけが use_perf を keyword 伝播する。

    拒否: site の追加だけでなく、登録済み実体の消失も closed-set 不一致にする。
    """
    call_sites = []
    target_functions = {
        "_build_cmd", "repro_command", "build_portable_run_cmd", "measure_point",
        "measure_fn",
    }
    for path in (ROOT / "orchestrator").rglob("*.py"):
        if "tests" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id not in target_functions:
                continue
            if any(keyword.arg == "use_perf" for keyword in node.keywords):
                call_sites.append((
                    path.relative_to(ROOT).as_posix(), ast.unparse(node.func),
                ))
    assert sorted(call_sites) == [
        ("orchestrator/calibrator/runner.py", "_build_cmd"),
        ("orchestrator/calibrator/runner.py", "repro_command"),
        ("orchestrator/campaign/between_run_floor.py", "measure_point"),
        ("orchestrator/campaign/between_run_floor.py", "measure_point"),
        ("orchestrator/campaign/pipeline.py", "measure_point"),
        ("orchestrator/campaign/s8b_floor_campaign.py", "build_portable_run_cmd"),
        ("orchestrator/campaign/s8b_floor_campaign.py", "measure_point"),
        ("orchestrator/campaign/s8b_oracle_n_pilot.py", "measure_fn"),
    ]


def _read_journal_lines(journal_path: Path) -> list:
    return [json.loads(line) for line in journal_path.read_text(encoding="utf-8")
           .splitlines() if line.strip()]


def _walk_entries(output: Path) -> list[tuple]:
    """``rglob`` と同じ entry 集合を symlink 非追跡で列挙する。"""
    entries = []
    stack = [str(output)]
    base = str(output)
    while stack:
        current = stack.pop()
        with os.scandir(current) as iterator:
            items = list(iterator)
        for entry in items:
            rel = os.path.relpath(entry.path, base).replace(os.sep, "/")
            if entry.is_symlink():
                entries.append(("symlink", rel, entry.path))
            elif entry.is_dir(follow_symlinks=False):
                entries.append(("dir", rel, entry.path))
                stack.append(entry.path)
            elif entry.is_file(follow_symlinks=False):
                entries.append(("file", rel, entry.path))
    return entries


def _digest(abspath: str) -> str:
    with open(abspath, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


# 32-worker 実測の file wall は base 42.19s / 4 thread 51.57s / 1 thread 41.78s。
# critical path も 39.34s → 48.9s → 39.19s であり、disk 競合下では逐次 digest が最速だった。
def _real_output_snapshot(
        output: Path = ROOT / "output", *, repo_root: Path = ROOT,
) -> tuple:
    """実 repo の Git-visible な output/ を統合テストが変えないことを固定する。

    旧実装との等価性は、安定しており、root と全 directory が読める通常 POSIX tree
    を定義域とする。
    """
    return git_indexed_output_snapshot(
        output,
        repo_root,
        walk_entries=_walk_entries,
        digest_file=_digest,
    )


def _real_output_snapshot_reference(output: Path = ROOT / "output") -> tuple:
    """最適化版の独立 oracle として保持する ``Path.rglob`` 実装。"""
    if not output.exists():
        return ()
    ignored_prefixes, _ignored_ancestors = git_ignored_output_snapshot_rules(ROOT)
    snapshot = []
    for path in sorted(output.rglob("*"), key=lambda item: item.as_posix()):
        rel = path.relative_to(output).as_posix()
        if is_git_ignored_output_path(rel, ignored_prefixes):
            continue
        if path.is_symlink():
            snapshot.append(("symlink", rel, path.readlink().as_posix()))
        elif path.is_file():
            snapshot.append(("file", rel, hashlib.sha256(path.read_bytes()).hexdigest()))
        elif path.is_dir():
            snapshot.append(("dir", rel))
    return tuple(snapshot)


def test_real_output_snapshot_matches_reference_and_is_deterministic(tmp_path):
    output = tmp_path / "snapshot"
    (output / "empty-dir").mkdir(parents=True)
    (output / "nested" / "deep" / "level-3").mkdir(parents=True)
    (output / "same-size-a").mkdir()
    (output / "same-size-b").mkdir()
    (output / "regular.txt").write_bytes(b"regular contents")
    (output / "empty.bin").write_bytes(b"")
    (output / "same-size-a" / "same.bin").write_bytes(b"ABCD")
    (output / "same-size-b" / "same.bin").write_bytes(b"WXYZ")
    (output / "nested" / "deep" / "level-3" / "leaf.bin").write_bytes(b"leaf")
    (output / "file-link").symlink_to("regular.txt")
    (output / "dir-link").symlink_to("nested", target_is_directory=True)

    actual = _real_output_snapshot(output)
    assert actual == _real_output_snapshot_reference(output)
    assert actual == tuple(sorted(actual, key=lambda row: row[1]))


def test_real_output_snapshot_git_index_fast_path_matches_reference(tmp_path):
    repo = tmp_path / "indexed-output-repo"
    output = repo / "output"
    nested = output / "nested"
    nested.mkdir(parents=True)
    tracked = nested / "tracked.bin"
    original_payload = b"tracked-alpha"
    changed_payload = b"tracked-bravo"
    assert len(original_payload) == len(changed_payload)
    tracked.write_bytes(original_payload)
    (output / "tracked-empty").write_bytes(b"")
    (output / "tracked-link").symlink_to("nested/tracked.bin")
    subprocess.run(
        ["git", "init", "-q"], cwd=repo, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    subprocess.run(
        ["git", "add", "--", "output"], cwd=repo, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    subprocess.run(
        [
            "git", "-c", "user.email=snapshot@example.invalid",
            "-c", "user.name=Snapshot Test", "commit", "-q", "-m",
            "tracked output fixture",
        ],
        cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    def assert_matches_reference_twice() -> tuple:
        expected = _real_output_snapshot_reference(output)
        first = _real_output_snapshot(output, repo_root=repo)
        second = _real_output_snapshot(output, repo_root=repo)
        assert first == second == expected
        return first

    expected_baseline = _real_output_snapshot_reference(output)
    baseline = _real_output_snapshot(output, repo_root=repo)
    assert baseline == expected_baseline
    with mock.patch.object(
            sys.modules[__name__], "_digest", wraps=_digest,
            ) as digest_spy:
        cached = _real_output_snapshot(output, repo_root=repo)
    assert cached == expected_baseline
    digest_spy.assert_not_called()

    tracked.write_bytes(changed_payload)
    changed = assert_matches_reference_twice()
    assert changed != baseline

    tracked.write_bytes(original_payload)
    restored = assert_matches_reference_twice()
    assert restored == baseline

    untracked = output / "untracked.bin"
    untracked.write_bytes(b"untracked payload")
    with_untracked = assert_matches_reference_twice()
    assert with_untracked != restored
    assert any(row[1] == "untracked.bin" for row in with_untracked)

    empty_directory = output / "untracked-empty-directory"
    empty_directory.mkdir()
    with_empty_directory = assert_matches_reference_twice()
    assert with_empty_directory != with_untracked
    assert ("dir", "untracked-empty-directory") in with_empty_directory


def test_real_output_snapshot_git_index_cache_performance_model(tmp_path):
    negative_root_attributes = (
        b"orchestrator/tests/fixtures/**/trace_*.log -text\n"
    )

    def make_repo(
            name: str, *, root_attributes: bytes = negative_root_attributes,
            subtree_attributes: bool = False,
            index_flag: str | None = None,
            autocrlf: str | None = None,
    ) -> tuple[Path, Path, list[tuple[str, str, str]]]:
        repo = tmp_path / name
        output = repo / "output"
        (output / "nested").mkdir(parents=True)
        paths = [
            output / "shared-a.bin",
            output / "shared-b.bin",
            output / "nested" / "distinct.bin",
        ]
        paths[0].write_bytes(b"shared payload\n")
        paths[1].write_bytes(b"shared payload\n")
        paths[2].write_bytes(b"distinct payload\n")
        (repo / ".gitattributes").write_bytes(root_attributes)
        if subtree_attributes:
            subtree_rule = output / "nested" / ".gitattributes"
            subtree_rule.write_bytes(b"*.bin -text\n")
            paths.append(subtree_rule)

        subprocess.run(
            ["git", "init", "-q"], cwd=repo, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        subprocess.run(
            ["git", "add", "--", ".gitattributes", "output"],
            cwd=repo, check=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        subprocess.run(
            [
                "git", "-c", "user.email=snapshot@example.invalid",
                "-c", "user.name=Snapshot Test", "commit", "-q", "-m",
                "synthetic indexed output",
            ],
            cwd=repo, check=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if index_flag is not None:
            subprocess.run(
                [
                    "git", "update-index", f"--{index_flag}", "--",
                    "output/shared-a.bin",
                ],
                cwd=repo, check=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        if autocrlf is not None:
            subprocess.run(
                ["git", "config", "core.autocrlf", autocrlf],
                cwd=repo, check=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        entries = [
            (
                "file",
                path.relative_to(output).as_posix(),
                os.fspath(path),
            )
            for path in paths
        ]
        return repo, output, entries

    def snapshot(
            repo: Path, output: Path, entries: list[tuple[str, str, str]],
    ) -> tuple[tuple[object, ...], ...]:
        def synthetic_walk(requested: Path) -> list[tuple[str, str, str]]:
            assert requested == output
            return list(entries)

        return git_indexed_output_snapshot(
            output, repo, walk_entries=synthetic_walk,
        )

    def snapshot_git_launch_counts(git_spy) -> tuple[int, int]:
        commands = [call.args[1] for call in git_spy.call_args_list]
        return (
            sum(
                command[1:4] == ("ls-files", "-s", "-v")
                for command in commands
            ),
            sum(command[1:2] == ("status",) for command in commands),
        )

    cache = output_snapshots._INDEX_BLOB_SHA256_CACHE
    cache.clear()
    try:
        repo, output, entries = make_repo("fast-path", autocrlf="false")
        observed_reasons: list[tuple[str, ...]] = []
        observed_indexes = []
        real_index = output_snapshots._index_blobs_for_output

        def capture_index(*args, **kwargs):
            result = real_index(*args, **kwargs)
            observed_indexes.append(result)
            observed_reasons.append(result.fallback_reasons)
            return result

        with (
                mock.patch.object(
                    output_snapshots, "_index_blobs_for_output",
                    side_effect=capture_index,
                ) as index_spy,
                mock.patch.object(
                    output_snapshots, "_status_paths_for_output",
                    wraps=output_snapshots._status_paths_for_output,
                ) as status_spy,
                mock.patch.object(
                    output_snapshots, "_run_git_bytes",
                    wraps=output_snapshots._run_git_bytes,
                ) as git_spy,
                mock.patch.object(
                    output_snapshots, "_sha256_file",
                    wraps=output_snapshots._sha256_file,
                ) as digest_spy,
        ):
            first = snapshot(repo, output, entries)
            assert digest_spy.call_count == len(entries)
            second = snapshot(repo, output, entries)
            assert second == first
            assert digest_spy.call_count == len(entries)
            cache.clear()
            restarted = snapshot(repo, output, entries)
            assert restarted == first
            assert digest_spy.call_count == 2 * len(entries)
        assert index_spy.call_count == 3
        assert status_spy.call_count == 3
        assert snapshot_git_launch_counts(git_spy) == (3, 3)
        assert observed_reasons == [(), (), ()]
        assert len(entries) == 3
        assert len({
            entry[1] for entry in observed_indexes[0].blobs.values()
        }) == 2

        fallback_cases = (
            ("assume-unchanged", {"index_flag": "assume-unchanged"}),
            ("skip-worktree", {"index_flag": "skip-worktree"}),
            ("subtree-gitattributes", {"subtree_attributes": True}),
            ("core.autocrlf", {"autocrlf": "true"}),
            (
                "root-gitattributes-conversion",
                {"root_attributes": b"output/** text\n"},
            ),
        )
        for expected_reason, options in fallback_cases:
            cache.clear()
            repo, output, entries = make_repo(expected_reason, **options)
            observed_reasons = []
            real_index = output_snapshots._index_blobs_for_output

            def capture_fallback_index(*args, **kwargs):
                result = real_index(*args, **kwargs)
                observed_reasons.append(result.fallback_reasons)
                return result

            with (
                    mock.patch.object(
                        output_snapshots, "_index_blobs_for_output",
                        side_effect=capture_fallback_index,
                    ) as index_spy,
                    mock.patch.object(
                        output_snapshots, "_status_paths_for_output",
                        wraps=output_snapshots._status_paths_for_output,
                    ) as status_spy,
                    mock.patch.object(
                        output_snapshots, "_run_git_bytes",
                        wraps=output_snapshots._run_git_bytes,
                    ) as git_spy,
                    mock.patch.object(
                        output_snapshots, "_sha256_file",
                        wraps=output_snapshots._sha256_file,
                    ) as digest_spy,
            ):
                first = snapshot(repo, output, entries)
                if expected_reason in {"assume-unchanged", "skip-worktree"}:
                    Path(entries[0][2]).write_bytes(b"mutate payload\n")
                second = snapshot(repo, output, entries)
            if expected_reason in {"assume-unchanged", "skip-worktree"}:
                assert second != first
            else:
                assert second == first
            assert digest_spy.call_count == 2 * len(entries)
            assert index_spy.call_count == 2
            assert status_spy.call_count == 2
            assert snapshot_git_launch_counts(git_spy) == (2, 2)
            assert all(
                expected_reason in reasons for reasons in observed_reasons
            )
    finally:
        cache.clear()


def test_git_snapshot_nul_parsers_fail_closed():
    malformed_outputs = (
        (
            ("git", "ls-files", "-s", "-v", "-z"),
            b"H 100644 deadbeef 0\toutput/truncated",
        ),
        (
            ("git", "status", "--porcelain=v1", "-z"),
            b" M output/truncated",
        ),
    )
    for command, stdout in malformed_outputs:
        with pytest.raises(AssertionError, match="末尾 NUL"):
            output_snapshots._nul_terminated_records(command, stdout)


def test_real_output_snapshot_detects_git_visible_real_output_changes(tmp_path):
    ignored_prefixes = git_ignored_output_prefixes(ROOT)
    assert not is_git_ignored_output_path("visible", ignored_prefixes)
    control = tmp_path / "visible"
    before = _real_output_snapshot(tmp_path)
    before_reference = _real_output_snapshot_reference(tmp_path)
    control.mkdir()
    (control / "nested").mkdir()
    payload = control / "nested" / "payload.bin"
    payload.write_bytes(b"git-visible snapshot positive control")

    after = _real_output_snapshot(tmp_path)
    after_reference = _real_output_snapshot_reference(tmp_path)
    assert after != before
    assert after_reference != before_reference
    assert any(row[1] == control.name for row in after)
    assert any(row[1] == control.name for row in after_reference)
    relative_payload = payload.relative_to(tmp_path).as_posix()
    assert any(row[1] == relative_payload for row in after)
    assert any(row[1] == relative_payload for row in after_reference)


def test_real_output_snapshot_excludes_git_ignored_real_output_changes(tmp_path):
    ignored_prefixes = git_ignored_output_prefixes(ROOT)
    assert "runs" in ignored_prefixes
    before = _real_output_snapshot(tmp_path)
    before_reference = _real_output_snapshot_reference(tmp_path)
    ignored_parent = tmp_path / "runs"
    ignored_parent.mkdir()
    control = ignored_parent / "snapshot-ignored-floor"
    control.mkdir()
    (control / "nested").mkdir()
    (control / "nested" / "payload.bin").write_bytes(
        b"git-ignored snapshot control"
    )

    assert _real_output_snapshot(tmp_path) == before
    assert _real_output_snapshot_reference(tmp_path) == before_reference

    assert not is_git_ignored_output_path("runs-visible", ignored_prefixes)
    visible_before = _real_output_snapshot(tmp_path)
    visible_before_reference = _real_output_snapshot_reference(tmp_path)
    visible = tmp_path / "runs-visible" / "nested"
    visible.mkdir(parents=True)
    (visible / "payload.bin").write_bytes(b"git-visible runs prefix control")
    assert _real_output_snapshot(tmp_path) != visible_before, (
        "rule-derived ignore prefix 'runs' must not hide Git-visible 'runs-visible'"
    )
    assert _real_output_snapshot_reference(tmp_path) != visible_before_reference


def test_real_output_snapshot_default_root_reobserves_dependencies(monkeypatch):
    module = sys.modules[__name__]
    observations = [
        [("file", "first.bin", "/synthetic/first"),
         ("dir", "first-empty", "/synthetic/first-empty")],
        [("file", "second.bin", "/synthetic/second")],
    ]
    digests = {
        "/synthetic/first": "first-digest",
        "/synthetic/second": "second-digest",
    }
    walk_calls = []
    digest_calls = []

    def synthetic_walk(output):
        assert output == ROOT / "output"
        walk_calls.append(output)
        return observations[len(walk_calls) - 1]

    def synthetic_digest(abspath):
        digest_calls.append(abspath)
        return digests[abspath]

    monkeypatch.setattr(module, "_walk_entries", synthetic_walk)
    monkeypatch.setattr(module, "_digest", synthetic_digest)

    assert _real_output_snapshot() == (
        ("dir", "first-empty"),
        ("file", "first.bin", "first-digest"),
    )
    assert _real_output_snapshot() == (
        ("file", "second.bin", "second-digest"),
    )
    assert walk_calls == [ROOT / "output", ROOT / "output"]
    assert digest_calls == ["/synthetic/first", "/synthetic/second"]


def test_real_output_snapshot_propagates_digest_failure(tmp_path, monkeypatch):
    output = tmp_path / "snapshot"
    output.mkdir()
    missing = output / "missing.bin"
    monkeypatch.setattr(
        sys.modules[__name__], "_walk_entries",
        lambda _output: [("file", "missing.bin", str(missing))],
    )

    with pytest.raises(OSError):
        _real_output_snapshot(output)


def test_real_output_snapshot_reference_is_independent(tmp_path, monkeypatch):
    output = tmp_path / "snapshot"
    (output / "a-empty").mkdir(parents=True)
    (output / "b-file.bin").write_bytes(b"reference payload")
    (output / "c-link").symlink_to("b-file.bin")
    expected = (
        ("dir", "a-empty"),
        ("file", "b-file.bin", hashlib.sha256(b"reference payload").hexdigest()),
        ("symlink", "c-link", "b-file.bin"),
    )

    def poison(*_args, **_kwargs):
        raise AssertionError("optimized snapshot dependency was called")

    module = sys.modules[__name__]
    monkeypatch.setattr(module, "_real_output_snapshot", poison)
    monkeypatch.setattr(module, "_walk_entries", poison)
    monkeypatch.setattr(module, "_digest", poison)

    assert _real_output_snapshot_reference(output) == expected


def _tree_snapshot(root: Path) -> tuple:
    if not root.exists():
        return ()
    rows = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows.append(("symlink", rel, path.readlink().as_posix()))
        elif path.is_file():
            rows.append(("file", rel, hashlib.sha256(path.read_bytes()).hexdigest()))
        else:
            rows.append(("dir", rel))
    return tuple(rows)


def _git_stdout(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout


def _assert_sealed_protocol_ccbench_pin(
        source_submodule: Path, ccbench_pin: str,
        held_checks: list[dict[str, object]]) -> None:
    current_head = _git_stdout(source_submodule, "rev-parse", "HEAD").strip()
    if s8b_floor_campaign._freeze_hold.HELD:
        held_checks.append(s8b_floor_campaign._freeze_hold.held_marker(
            "s8b-floor.sealed-protocol-ccbench-pin-current-head",
        ))
    else:
        assert current_head == ccbench_pin


def test_sealed_protocol_ccbench_pin_hold_and_release_positive_control():
    sealed_pin = "d706650cdb31e442bef45b9b4216951d4fb40969"
    current_head = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
    held_checks = []
    with mock.patch.object(
            sys.modules[__name__], "_git_stdout", return_value=current_head):
        _assert_sealed_protocol_ccbench_pin(Path("unused"), sealed_pin, held_checks)
        assert [marker["check_id"] for marker in held_checks] == [
            "s8b-floor.sealed-protocol-ccbench-pin-current-head",
        ]
        with mock.patch.object(s8b_floor_campaign._freeze_hold, "HELD", False):
            with pytest.raises(AssertionError):
                _assert_sealed_protocol_ccbench_pin(
                    Path("unused"), sealed_pin, held_checks=[],
                )


def _clone_committed_head_with_ccbench(
        destination: Path, *, ccbench_pin: str,
        held_checks: list[dict[str, object]]) -> Path:
    """ネットワークを使わず、committed HEAD と初期化済み submodule を複製する。"""
    subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(destination)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    source_submodule = ROOT / "external" / "ccbench"
    assert source_submodule.is_dir()
    _assert_sealed_protocol_ccbench_pin(source_submodule, ccbench_pin, held_checks)
    cloned_submodule = destination / "external" / "ccbench"
    subprocess.run(
        [
            "git", "clone", "--quiet", "--no-hardlinks",
            str(source_submodule), str(cloned_submodule),
        ],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    subprocess.run(
        ["git", "checkout", "--quiet", "--detach", ccbench_pin],
        cwd=cloned_submodule, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    subprocess.run(
        ["git", "add", "--", "external/ccbench"],
        cwd=destination, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    subprocess.run(
        [
            "git", "-c", "user.name=Izanagi Test",
            "-c", "user.email=izanagi-test@example.invalid",
            "commit", "--quiet", "-m", "test: restore historical ccbench gitlink",
        ],
        cwd=destination, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return destination


def _remove_post_seal_floor_protocols_from_replay(
        clone_root: Path, relative_paths: tuple[str, ...]) -> None:
    """seal 後に発行された protocol だけを replay clone の履歴から外す。"""
    assert relative_paths
    assert all(
        relative.startswith(s8b_floor_campaign._FLOOR_PROTOCOLS_REL + "/")
        for relative in relative_paths
    )
    subprocess.run(
        ["git", "rm", "--quiet", "--", *relative_paths],
        cwd=clone_root, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    subprocess.run(
        [
            "git", "-c", "user.name=Izanagi Test",
            "-c", "user.email=izanagi-test@example.invalid",
            "commit", "--quiet", "-m", "test: restore historical protocol namespace",
        ],
        cwd=clone_root, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def _bytes_snapshot(root: Path, relative_paths) -> tuple:
    rows = []
    for relative in sorted(relative_paths):
        path = root / relative
        assert path.is_file() and not path.is_symlink()
        rows.append((relative, path.read_bytes()))
    return tuple(rows)


def _independent_real_seal_rratios(freeze: dict) -> dict[str, str]:
    """enumerate_cells を使わず、seal bytes から cell→rratio を直接射影する。"""
    expected = {}
    for holdout_id, holdout in freeze["holdouts"].items():
        rratio = holdout["ycsb"]["ycsb_rratio"]
        for configuration_id in holdout["variant_binding"]["entries"]:
            expected[f"{holdout_id}::{configuration_id}"] = rratio
    return dict(sorted(expected.items()))


def _independent_constant_tps_floors(
        freeze: dict, *, stock_configuration: str,
        throughput: float, wired_min_rel_floor: float,
) -> dict[str, dict]:
    """全 session 同一 TPS (= noise 0) の floor を stats 実装なしで計算する。"""
    floor = max(0.0, throughput * wired_min_rel_floor)
    expected = {}
    for holdout_id, holdout in freeze["holdouts"].items():
        configurations = sorted(holdout["variant_binding"]["entries"])
        expected[holdout_id] = {
            "pairs": {
                configuration: floor
                for configuration in configurations
                if configuration != stock_configuration
            },
            "scalar_alt": floor,
            "scale_ref": throughput,
        }
    return expected


def _make_real_freeze_prepare(
        freeze: dict, cells: list[dict], *, ccbench_pin: str,
        ccbench_dir: Path, cache_root: Path,
):
    """実 freeze entry を別 snapshot と照合する test-only materializer。"""
    entries = {
        (holdout_id, configuration): entry
        for holdout_id, holdout in freeze["holdouts"].items()
        for configuration, entry in holdout["variant_binding"]["entries"].items()
    }
    entry_bytes = {
        key: json.dumps(
            entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        for key, entry in entries.items()
    }
    expected_cell_ids = {cell["cell_id"] for cell in cells}
    calls = []

    @contextlib.contextmanager
    def prepare(cell, observed_ccbench_pin, *, cxx):
        assert observed_ccbench_pin == ccbench_pin
        assert isinstance(cell, dict) and set(cell) == {"configuration", "variant"}
        configuration = cell["configuration"]
        entry = cell["variant"]
        matches = [key for key, expected in entries.items() if expected is entry]
        assert len(matches) == 1
        holdout_id, expected_configuration = matches[0]
        assert configuration == expected_configuration
        assert entry_bytes[(holdout_id, configuration)] == json.dumps(
            entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        cell_id = f"{holdout_id}::{configuration}"
        assert cell_id in expected_cell_ids
        calls.append((cell_id, observed_ccbench_pin))
        _FIXTURE_CELL_BY_TOKEN[cell_id] = cell_id
        _FIXTURE_BUILD_DECLARATION_BY_TOKEN[cell_id] = (
            observed_ccbench_pin, configuration, copy.deepcopy(entry),
        )
        yield PreparedCell(
            genome=Genome("silo", dict(entry.get("flags", {}))),
            src_token=cell_id,
            ccbench_dir=str(ccbench_dir),
            cache_root=str(cache_root),
            oracle_attempt=(
                fake_sort_swo_pass_attempt()
                if configuration == "sort_best" else None
            ),
        )

    prepare.calls = calls
    return prepare


def _write_floor_submit_receipt(
        repo_root: Path, *, env_tag: str, binding_values: dict[str, str],
        **updates,
) -> Path:
    payload = {
        "schema_version": "pegasus-floor-submit-receipt/v1",
        "source_commit": "1" * 40,
        "job_script_path": "tools/pegasus/floor_campaign.sh",
        "job_script_sha256": binding_values[
            "IZANAGI_RESERVATION_SCRIPT_SHA256"
        ],
        "job_id": binding_values["IZANAGI_RESERVATION_JOB_ID"],
        "nonce": binding_values["IZANAGI_RESERVATION_NONCE"],
        "submitted_at": 1,
        "request": {},
        "preflight": {},
        "dry_run": False,
    }
    payload.update(updates)
    path = floor_submit_receipt.receipt_path(
        repo_root,
        env_tag=env_tag,
        nonce=binding_values["IZANAGI_RESERVATION_NONCE"],
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return path


def _install_real_seal_reservation(
        monkeypatch, *, repo_root: Path, env_tag: str,
) -> dict[str, str]:
    requested_s = 100_000
    started = time.time() - 1.0
    values = {
        "IZANAGI_RESERVATION_JOB_ID": "real-seal-fixture-job",
        "IZANAGI_RESERVATION_REQUESTED_S": str(requested_s),
        "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": str(started),
        "IZANAGI_RESERVATION_DEADLINE_EPOCH": str(started + requested_s),
        "IZANAGI_RESERVATION_HOST": f"{os.uname().nodename}-non-authority",
        "IZANAGI_RESERVATION_BOOT_ID": Path(
            "/proc/sys/kernel/random/boot_id"
        ).read_text(encoding="ascii").strip(),
        "IZANAGI_RESERVATION_SCRIPT_SHA256": "7" * 64,
        "IZANAGI_RESERVATION_NONCE": "e" * 32,
        "PBS_JOBID": "real-seal-fixture-job",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    _write_floor_submit_receipt(
        repo_root, env_tag=env_tag, binding_values=values,
    )
    return values


def _observed(profile):
    raw = env_attestation.profile_to_dict(profile)
    del raw["effective_clock"]["tolerance_pct"]
    return env_attestation.normalize_observed_profile(raw)


def _install_required_contract(
        tmp_path: Path, monkeypatch, *, calibration_transform=None):
    """production calibration/v2 reader + issuer を通す required env fixture。"""
    repo_root = tmp_path / "required-repo"
    repo_root.mkdir()
    document = _valid_calibration_v2_document()
    # U-2/U-3 による current admission の正当な縮小: required fixture は policy と一致させる。
    document["attestation_profile"]["effective_clock"]["tolerance_pct"] = 2.0
    if calibration_transform is not None:
        calibration_transform(document)
    raw = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    calibration_sha256 = hashlib.sha256(raw).hexdigest()
    calibration_relative = Path(
        "output", "env", document["env_tag"], "calibration", "registered",
        f"calibration-{calibration_sha256[:16]}.json",
    )
    calibration_path = repo_root / calibration_relative
    calibration_path.parent.mkdir(parents=True, exist_ok=True)
    calibration_path.write_bytes(raw)
    contract = ec.ExecutionEnvironmentContract(
        env_tag=document["env_tag"], clocks_per_us=document["clocks_per_us"],
        numactl=ec.lookup(ENV_TAG).numactl, attestation_mode="required",
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=False),
        calibration_ref=ec.CalibrationRef(
            path=calibration_relative.as_posix(), sha256=calibration_sha256,
        ),
    )
    monkeypatch.setattr(s8b_floor_campaign._env_contract, "lookup", lambda _tag: contract)
    verified = env_attestation.load_verified_calibration(contract, repo_root)
    monkeypatch.setattr(
        s8b_floor_campaign.env_attestation, "probe",
        lambda: _observed(verified.attestation_profile),
    )

    requested_s = 100_000
    started = time.time() - 1.0
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    binding_values = {
        "IZANAGI_RESERVATION_JOB_ID": "fixture-job",
        "IZANAGI_RESERVATION_REQUESTED_S": str(requested_s),
        "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": str(started),
        "IZANAGI_RESERVATION_DEADLINE_EPOCH": str(started + requested_s),
        "IZANAGI_RESERVATION_HOST": f"{os.uname().nodename}-non-authority",
        "IZANAGI_RESERVATION_BOOT_ID": boot_id,
        "IZANAGI_RESERVATION_SCRIPT_SHA256": "d" * 64,
        "IZANAGI_RESERVATION_NONCE": "d" * 32,
        "PBS_JOBID": "fixture-job",
    }
    for key, value in binding_values.items():
        monkeypatch.setenv(key, value)
    submit_receipt_path = _write_floor_submit_receipt(
        repo_root, env_tag=contract.env_tag, binding_values=binding_values,
    )
    freeze = _freeze_document()
    protocol = _protocol(
        freeze_sha=_freeze_sha(freeze), env_tag=contract.env_tag,
        contract_sha256=contract.contract_sha256,
    )
    return {
        "repo_root": repo_root,
        "contract": contract,
        "verified": verified,
        "freeze": freeze,
        "protocol": protocol,
        "out_root": tmp_path / "required-out",
        "binding_values": binding_values,
        "submit_receipt_path": submit_receipt_path,
    }


def _install_toolchain_bound_required_contract(
        tmp_path, monkeypatch, *, build_argv=None,
        compiler_version="registered-cc Vendor 1.0\nCopyright stable",
        cmake_version="registered-cmake version 3.25.0\nCopyright stable"):
    def transform(document):
        receipt = document["acquisition_receipt"]
        receipt["toolchain"].update({
            "compiler_path": "/tool/cc",
            "compiler_version": compiler_version,
            "cmake_version": cmake_version,
        })
        receipt["ccbench"]["build_argv"] = (
            list(build_argv) if build_argv is not None else [
                "cmake",
                "-DCMAKE_C_COMPILER=/tool/cc",
                "-DCMAKE_CXX_COMPILER=/tool/cxx",
            ])

    return _install_required_contract(
        tmp_path, monkeypatch, calibration_transform=transform,
    )


def _matching_floor_observations():
    return {
        "cc": s8b_floor_campaign._ObservedFloorTool(
            requested="site-cc", realpath="/tool/cc",
            version_first_line="live-cc Vendor 1.0",
            version="live-cc Vendor 1.0\nCopyright stable",
        ),
        "cxx": s8b_floor_campaign._ObservedFloorTool(
            requested="site-cxx", realpath="/tool/cxx",
            version_first_line="live-cxx Vendor 1.0",
            version="live-cxx Vendor 1.0\nCopyright stable",
        ),
        "cmake": s8b_floor_campaign._ObservedFloorTool(
            requested="cmake", realpath="/tool/cmake",
            version_first_line="live-cmake version 3.25.0",
            version="live-cmake version 3.25.0\nCopyright stable",
        ),
    }


class TestFloorToolchainBinding:
    """共通 fake を外し、private 観測 seam への注入値だけで gate を検査する。"""

    def test_live_observer_keeps_stdout_and_stderr_full_text(
            self, monkeypatch):
        monkeypatch.setattr(
            s8b_floor_campaign.shutil, "which", lambda _requested: "/tool/cc",
        )
        monkeypatch.setattr(s8b_floor_campaign.os.path, "isfile", lambda _path: True)
        monkeypatch.setattr(s8b_floor_campaign.os, "access", lambda _path, _mode: True)
        monkeypatch.setattr(
            s8b_floor_campaign.subprocess, "run",
            lambda *_args, **_kwargs: SimpleNamespace(
                returncode=0,
                stdout="live-cc Vendor 1.0\nCopyright stdout\n",
                stderr="Copyright stderr\n",
            ),
        )
        observed = s8b_floor_campaign._observe_floor_tool("site-cc", "cc")
        assert observed.version_first_line == "live-cc Vendor 1.0"
        assert observed.version == (
            "live-cc Vendor 1.0\nCopyright stdout\nCopyright stderr"
        )

    def test_binding_accepts_full_bodies_and_returns_same_observation_manifest(
            self, tmp_path, monkeypatch):
        ctx = _install_toolchain_bound_required_contract(tmp_path, monkeypatch)
        verified = ctx["verified"]
        observations = _matching_floor_observations()
        calls = []

        def observe(requested, role):
            calls.append((requested, role))
            return observations[role]

        monkeypatch.setattr(s8b_floor_campaign, "_observe_floor_tool", observe)
        manifest = s8b_floor_campaign._bind_current_toolchain(
            verified, cc="site-cc", cxx="site-cxx",
        )
        assert calls == [
            ("site-cc", "cc"), ("site-cxx", "cxx"), ("cmake", "cmake"),
        ]
        assert manifest == {
            "cc": {
                "requested": "site-cc",
                "realpath": "/tool/cc",
                "version_first_line": "live-cc Vendor 1.0",
                "version": "live-cc Vendor 1.0\nCopyright stable",
            },
            "cxx": {
                "requested": "site-cxx",
                "realpath": "/tool/cxx",
                "version_first_line": "live-cxx Vendor 1.0",
                "version": "live-cxx Vendor 1.0\nCopyright stable",
            },
            "cmake": {
                "requested": "cmake",
                "realpath": "/tool/cmake",
                "version_first_line": "live-cmake version 3.25.0",
                "version": "live-cmake version 3.25.0\nCopyright stable",
            },
        }

    def test_binding_rejects_drift_only_below_version_first_line(
            self, tmp_path, monkeypatch):
        ctx = _install_toolchain_bound_required_contract(tmp_path, monkeypatch)
        verified = ctx["verified"]
        observations = _matching_floor_observations()
        observations["cc"] = dataclasses.replace(
            observations["cc"],
            version="live-cc Vendor 1.0\nCopyright changed",
        )
        monkeypatch.setattr(
            s8b_floor_campaign, "_observe_floor_tool",
            lambda _requested, role: observations[role],
        )
        with pytest.raises(
                s8b_floor_campaign.FloorCampaignError,
                match="registered calibration receipt と不一致"):
            s8b_floor_campaign._bind_current_toolchain(
                verified, cc="site-cc", cxx="site-cxx",
            )

    def test_binding_rejects_live_cc_realpath_projection_drift(
            self, tmp_path, monkeypatch):
        ctx = _install_toolchain_bound_required_contract(tmp_path, monkeypatch)
        observations = _matching_floor_observations()
        observations["cc"] = dataclasses.replace(
            observations["cc"], realpath="/other/cc",
        )
        monkeypatch.setattr(
            s8b_floor_campaign, "_observe_floor_tool",
            lambda _requested, role: observations[role],
        )
        with pytest.raises(
                s8b_floor_campaign.FloorCampaignError,
                match="registered calibration receipt と不一致"):
            s8b_floor_campaign._bind_current_toolchain(
                ctx["verified"], cc="site-cc", cxx="site-cxx",
            )

    def test_binding_rejects_live_cxx_version_projection_drift(
            self, tmp_path, monkeypatch):
        ctx = _install_toolchain_bound_required_contract(tmp_path, monkeypatch)
        observations = _matching_floor_observations()
        observations["cxx"] = dataclasses.replace(
            observations["cxx"],
            version="live-cxx Vendor 2.0\nCopyright stable",
        )
        monkeypatch.setattr(
            s8b_floor_campaign, "_observe_floor_tool",
            lambda _requested, role: observations[role],
        )
        with pytest.raises(
                s8b_floor_campaign.FloorCampaignError,
                match="registered calibration receipt と不一致"):
            s8b_floor_campaign._bind_current_toolchain(
                ctx["verified"], cc="site-cc", cxx="site-cxx",
            )

    def test_binding_rejects_live_cmake_version_projection_drift(
            self, tmp_path, monkeypatch):
        ctx = _install_toolchain_bound_required_contract(tmp_path, monkeypatch)
        observations = _matching_floor_observations()
        observations["cmake"] = dataclasses.replace(
            observations["cmake"],
            version="live-cmake version 3.25.0\nCopyright changed",
        )
        monkeypatch.setattr(
            s8b_floor_campaign, "_observe_floor_tool",
            lambda _requested, role: observations[role],
        )
        with pytest.raises(
                s8b_floor_campaign.FloorCampaignError,
                match="registered calibration receipt と不一致"):
            s8b_floor_campaign._bind_current_toolchain(
                ctx["verified"], cc="site-cc", cxx="site-cxx",
            )

    @pytest.mark.parametrize("build_argv", [
        ["cmake", "-DCMAKE_CXX_COMPILER=/tool/cxx"],
        [
            "cmake",
            "-DCMAKE_C_COMPILER=/tool/cc",
            "-DCMAKE_C_COMPILER=/other/cc",
            "-DCMAKE_CXX_COMPILER=/tool/cxx",
        ],
    ])
    def test_binding_rejects_missing_or_duplicate_compiler_definition(
            self, tmp_path, monkeypatch, build_argv):
        ctx = _install_toolchain_bound_required_contract(
            tmp_path, monkeypatch, build_argv=build_argv,
        )
        verified = ctx["verified"]
        observations = _matching_floor_observations()
        monkeypatch.setattr(
            s8b_floor_campaign, "_observe_floor_tool",
            lambda _requested, role: observations[role],
        )
        with pytest.raises(
                s8b_floor_campaign.FloorCampaignError,
                match="registered calibration receipt と不一致"):
            s8b_floor_campaign._bind_current_toolchain(
                verified, cc="site-cc", cxx="site-cxx",
            )

    def test_binding_rejects_receiptless_calibration_without_tool_probe(
            self, monkeypatch):
        verified = s8b_floor_campaign.env_attestation.VerifiedCalibration(
            schema_version=s8b_floor_campaign.env_attestation.LEGACY_SCHEMA_VERSION,
            sha256="a" * 64,
            calibration=None,
            attestation_profile_sha256=None,
        )
        monkeypatch.setattr(
            s8b_floor_campaign, "_observe_floor_tool",
            lambda *_args, **_kwargs: pytest.fail("receipt 不在時に tool を読まない"),
        )
        with pytest.raises(
                s8b_floor_campaign.FloorCampaignError,
                match="acquisition receipt がない"):
            s8b_floor_campaign._bind_current_toolchain(
                verified, cc="site-cc", cxx="site-cxx",
            )


def test_build_cells_resolves_site_compilers_and_binding_once_before_cell_loop(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    enumerated = s8b_floor_campaign.enumerate_cells(
        freeze, stock_configuration=_STOCK,
    )
    cells = [
        next(cell for cell in enumerated if cell["configuration_id"] == "stock_common"),
        next(cell for cell in enumerated if cell["configuration_id"] == "sort_best"),
    ]
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    compiler_calls = []
    binding_calls = []
    prepare_cxx = []
    evidence_cxx = []
    evidence_contract_kwargs = []
    build_tools = []
    build_contract_kwargs = []
    expected_manifest = {"sentinel": {"generation": "current"}}
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()

    def compilers():
        compiler_calls.append("resolve")
        return "site-cc", "site-cxx"

    def bind(candidate, *, cc, cxx):
        binding_calls.append((candidate, cc, cxx))
        return expected_manifest

    def evidence(genome, commit, *, ccbench_dir, cxx, **kwargs):
        evidence_cxx.append(cxx)
        evidence_contract_kwargs.append(kwargs)
        return _fixture_source_evidence(
            genome, commit, ccbench_dir=ccbench_dir, cxx=cxx,
        )

    @contextlib.contextmanager
    def prepare(cell, ccbench_pin, *, cxx):
        prepare_cxx.append(cxx)
        with _fake_prepare(cell, ccbench_pin, cxx=cxx) as prepared:
            if cell["configuration"] == "sort_best":
                prepared = dataclasses.replace(
                    prepared,
                    sort_oracle_contract_id=(
                        sort_swo_oracle.ORACLE_CONTRACT_ID
                    ),
                )
            yield prepared

    fake_build = _make_fake_build(tmp_path / "bin")

    def build(genome, **kwargs):
        assert len(list(marker_root.glob("phase-build-*.json"))) == len(build_tools) + 1
        build_contract_kwargs.append({
            key: value for key, value in kwargs.items()
            if key == "sort_oracle_contract_id"
        })
        build_tools.append((
            kwargs["cc"], kwargs["cxx"], kwargs["expected_toolchain_manifest"],
        ))
        return fake_build(genome, **kwargs)

    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "compilers_for_current_site", compilers,
    )
    monkeypatch.setattr(s8b_floor_campaign, "_bind_current_toolchain", bind)
    monkeypatch.setattr(s8b_floor_campaign.source_digest, "resolve_evidence", evidence)
    built = s8b_floor_campaign.build_cells(
        freeze, cells, ccbench_pin="0" * 40,
        out_root=tmp_path / "out", prepare_fn=prepare,
        contract=contract, verified_calibration=verified, build_fn=build,
        phase_marker_root=marker_root,
    )
    assert len(built) == 2
    assert compiler_calls == ["resolve"]
    assert binding_calls == [(verified, "site-cc", "site-cxx")]
    assert prepare_cxx == ["site-cxx", "site-cxx"]
    assert evidence_cxx == ["site-cxx", "site-cxx"]
    assert evidence_contract_kwargs == [
        {},
        {"sort_oracle_contract_id": sort_swo_oracle.ORACLE_CONTRACT_ID},
    ]
    assert build_contract_kwargs == [
        {},
        {"sort_oracle_contract_id": sort_swo_oracle.ORACLE_CONTRACT_ID},
    ]
    assert build_tools == [
        ("site-cc", "site-cxx", expected_manifest),
        ("site-cc", "site-cxx", expected_manifest),
    ]
    assert len(list(marker_root.glob("phase-build-*.json"))) == 2


def test_floor_sort_cell_injects_verified_cxx_and_dependency_into_oracle(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK,
        )
        if cell["configuration_id"] == "sort_best"
    )]
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    fetchcontent_base = tmp_path / "fetchcontent"
    fetchcontent_base.mkdir()
    dependency = _fixture_dependency_binding(fetchcontent_base)
    observed = {}

    @contextlib.contextmanager
    def production_prepare(
            cell, ccbench_pin, *, cxx, oracle_dependency_root,
            oracle_compiler, oracle_phase_marker):
        observed.update({
            "cxx": cxx,
            "oracle_dependency_root": oracle_dependency_root,
            "oracle_compiler": oracle_compiler,
        })
        oracle_phase_marker()
        with _fake_prepare(cell, ccbench_pin, cxx=cxx) as prepared:
            yield prepared

    monkeypatch.setattr(
        s8b_floor_campaign.buildcache,
        "compilers_for_current_site",
        lambda: ("site-cc", "site-cxx"),
    )
    monkeypatch.setattr(
        s8b_floor_campaign,
        "_prepare_floor_oracle_dependency",
        lambda base, **_kwargs: dependency,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_build_dependency",
        lambda _result, _argv, **_kwargs: dependency,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "prepare_cell", production_prepare,
    )
    fake_build = _make_fake_build(tmp_path / "bin")
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "build_v2", fake_build,
    )
    monkeypatch.setenv("CXX", "/ambient/cxx")
    monkeypatch.setenv("IZANAGI_SORT_SWO_CXX", "/ambient/oracle-cxx")
    built = s8b_floor_campaign.build_cells(
        freeze,
        cells,
        ccbench_pin="0" * 40,
        out_root=tmp_path / "out",
        prepare_fn=production_prepare,
        contract=contract,
        verified_calibration=verified,
        build_fn=fake_build,
        fetchcontent_base_dir=fetchcontent_base,
        phase_marker_root=marker_root,
    )
    assert len(built) == 1
    assert observed == {
        "cxx": "site-cxx",
        "oracle_dependency_root": dependency.oracle_root,
        "oracle_compiler": "/fixture/toolchain/site-cxx",
    }
    oracle_markers = list(marker_root.glob("phase-oracle-*.json"))
    assert len(oracle_markers) == 1
    marker = json.loads(oracle_markers[0].read_text(encoding="utf-8"))
    assert marker["compiler"] == "/fixture/toolchain/site-cxx"
    assert marker["dependency_config_sha256"] == dependency.config_sha256
    dependency_attempt = json.loads(
        (marker_root / "sort-swo-oracle-dependency.json").read_text(
            encoding="utf-8"
        )
    )
    assert dependency_attempt["dependency_root"] == str(dependency.source_root)
    assert dependency_attempt["oracle_dependency_root"] == str(
        dependency.oracle_root
    )
    assert dependency_attempt["dependency_manifest_sha256"] == (
        dependency.dependency_manifest_sha256
    )
    assert dependency_attempt["dependency_config_sha256"] == (
        dependency.config_sha256
    )
    assert dependency_attempt["dependency_toolchain_manifest_sha256"] == (
        dependency.expected_toolchain_manifest_sha256
    )


def test_real_floor_prepare_material_oracle_and_capability_series_when_configured(
        tmp_path, monkeypatch):
    configured = os.environ.get("IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT")
    if not configured:
        pytest.skip("IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT is not configured")
    configured_source = Path(configured).resolve(strict=True)
    compiler = shutil.which("g++")
    c_compiler = shutil.which("gcc")
    cmake = shutil.which("cmake")
    if compiler is None or c_compiler is None or cmake is None:
        pytest.skip("real floor series requires gcc, g++, and cmake")

    def tool_entry(requested: str) -> dict[str, str]:
        completed = subprocess.run(
            [requested, "--version"], check=True,
            capture_output=True, text=True,
        )
        version = (completed.stdout + completed.stderr).strip()
        return {
            "requested": requested,
            "realpath": str(Path(requested).resolve(strict=True)),
            "version_first_line": completed.stdout.splitlines()[0],
            "version": version,
        }

    toolchain_manifest = {
        "cc": tool_entry(c_compiler),
        "cxx": tool_entry(compiler),
        "cmake": tool_entry(cmake),
    }
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "compilers_for_current_site",
        lambda: (c_compiler, compiler),
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_bind_current_toolchain",
        lambda *_args, **_kwargs: toolchain_manifest,
    )
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch.resolve()))

    contract = ec.lookup(ENV_TAG)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    reservation_binding = _fixture_floor_reservation_binding()
    payload_root = floor_submit_receipt.receipt_path(
        repo_root, env_tag=contract.env_tag, nonce=reservation_binding.nonce,
    ).parent / "masstree-payload"
    payload_root.mkdir(parents=True)
    shutil.copytree(
        configured_source, payload_root / "masstree-src", symlinks=True,
    )
    pins = {
        "masstree": subprocess.run(
            ["git", "-C", str(configured_source), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip(),
    }
    for name in ("mimalloc", "googletest"):
        pins[name] = _git_fixture_source(payload_root / f"{name}-src")
    config_sha256 = s8b_floor_campaign._sha256_regular_file(
        configured_source / "config.h",
    )
    archive_digests = s8b_floor_campaign._verify_masstree_archive(
        configured_source / "libkohler_masstree_json.a",
    )
    expected_payload = s8b_floor_campaign._LoadedFloorMasstreePayloadPolicy(
        schema_version="s8b-floor-masstree-payload/v3",
        name="masstree",
        pin=pins["masstree"],
        config_sha256=config_sha256,
        archive_projection="gnu-ar-elf-nondebug/v1",
        archive_nondebug_sha256=archive_digests.archive_nondebug_sha256,
        raw_sha256="f" * 64,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_floor_third_party_policy_pins",
        lambda _root: pins,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_load_floor_masstree_payload_policy",
        lambda *_args, **_kwargs: expected_payload,
    )

    @contextlib.contextmanager
    def checkout(_pin, *, base_dir):
        assert base_dir == str(repo_root / "external" / "ccbench")
        yield str((ROOT / "external" / "ccbench").resolve())

    monkeypatch.setattr(s8b_floor_campaign.patchharness, "checkout", checkout)

    prebuild_bases = []

    def prebuild_from_staged_sources(**kwargs):
        base = Path(kwargs["fetchcontent_base_dir"])
        prebuild_bases.append(base)
        for name in ("masstree", "mimalloc", "googletest"):
            assert kwargs[f"{name}_source_dir"] == str(base / f"{name}-src")
        return SimpleNamespace()

    monkeypatch.setattr(
        s8b_floor_campaign.buildcache,
        "prepare_masstree_fetchcontent",
        prebuild_from_staged_sources,
    )

    capability_calls = []

    def exact_build(genome, **kwargs):
        capability = kwargs["post_oracle_dependency_binding"]
        assert set(capability) == {
            "fetchcontent_base_dir", "oracle_dependency_root",
            "dependency_manifest_sha256", "masstree_head",
            "config_sha256", "archive_sha256",
        }
        source = Path(capability["fetchcontent_base_dir"]) / "masstree-src"
        assert Path(capability["oracle_dependency_root"]) != source
        capability_calls.append(dict(capability))
        binary = Path(kwargs["cache_root"]) / "real-floor" / "ycsb_silo.exe"
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(b"real-floor-series-binary")
        binary_sha256 = hashlib.sha256(binary.read_bytes()).hexdigest()
        expected_manifest = dict(kwargs["expected_toolchain_manifest"])
        base = Path(capability["fetchcontent_base_dir"])
        compiler_input = Path(kwargs["ccbench_dir"]) / "CMakeLists.txt"
        compiler_input_manifest = {
            "schema_version": "s8b-compiler-input/v2",
            "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
            "target": f"ycsb_{genome.protocol}.exe",
            "depfile_count": 1,
            "inputs": [{
                "root": "snapshot",
                "path": "CMakeLists.txt",
                "sha256": hashlib.sha256(
                    compiler_input.read_bytes()
                ).hexdigest(),
            }],
        }
        expected_materialization_sha256 = (
            _fixture_expected_materialization_sha256(
                kwargs["expected_materialization_descriptor"].declaration
            )
        )
        source_protection = None  # Consumer fixture; no capability issuance.
        return SimpleNamespace(
            genome=genome,
            source_protection=source_protection,
            trace=False,
            binary=str(binary),
            bin_sha256=binary_sha256,
            bin_hash=binary_sha256[:16],
            build_dir=str(binary.parent),
            cached=False,
            configure_cmd="fixture configure",
            build_cmd="fixture build",
            configure_argv=(
                "cmake", f"-DFETCHCONTENT_BASE_DIR={base}",
                f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={base / 'masstree-src'}",
                f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={base / 'mimalloc-src'}",
                f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={base / 'googletest-src'}",
                "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
            ),
            build_argv=("cmake", "--build", str(binary.parent)),
            cache_root=kwargs["cache_root"],
            ccbench_root=kwargs["ccbench_dir"],
            contract_sha256=kwargs["contract"].contract_sha256,
            toolchain_manifest=expected_manifest,
            toolchain_manifest_sha256=(
                s8b_floor_campaign._floor_toolchain_manifest_sha256(
                    expected_manifest
                )
            ),
            compiler_input_manifest=compiler_input_manifest,
            compiler_input_manifest_sha256=hashlib.sha256(json.dumps(
                compiler_input_manifest, ensure_ascii=True, sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")).hexdigest(),
            source_snapshot_sha256=expected_materialization_sha256,
            expected_materialization_sha256=expected_materialization_sha256,
            fetchcontent_base_dir=str(base),
            masstree_source_root_sha256=hashlib.sha256(
                str(source).encode("utf-8")
            ).hexdigest(),
        )

    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "build_v2", exact_build,
    )
    freeze = json.loads(
        (ROOT / "output/s8b-freeze/holdout_freeze.json").read_text(
            encoding="utf-8"
        )
    )
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration="stock_common",
        )
        if cell["configuration_id"] == "sort_best"
    )]
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    ccbench_pin = subprocess.run(
        ["git", "-C", str(ROOT / "external/ccbench"), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    built = s8b_floor_campaign.build_cells(
        freeze,
        cells,
        ccbench_pin=ccbench_pin,
        out_root=tmp_path / "out",
        prepare_fn=s8b_floor_campaign.prepare_cell,
        contract=contract,
        verified_calibration=verified,
        phase_marker_root=marker_root,
        repo_root=repo_root,
        reservation_binding=reservation_binding,
    )

    assert len(built) == 1
    assert len(prebuild_bases) == 1
    assert len(capability_calls) == 1
    capability = capability_calls[0]
    assert capability["masstree_head"] == (
        "b3c5d054b66b08374d7a6ff5a0faeaf28b041a38"
    )
    assert capability["dependency_manifest_sha256"] == (
        sort_swo_oracle.DEPENDENCY_MANIFEST_SHA256
    )
    oracle_root = Path(capability["oracle_dependency_root"])
    assert oracle_root.name == "canonical"
    assert not oracle_root.parent.exists()
    record = next(iter(built.values()))
    assert record["sort_swo_oracle"]["reason_code"] == "sort-swo-oracle-pass"


def test_dependency_bound_sort_best_rejects_nonexact_builder_before_call(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK,
        )
        if cell["configuration_id"] == "sort_best"
    )]
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    fetchcontent_base = tmp_path / "fetchcontent"
    fetchcontent_base.mkdir()
    dependency = _fixture_dependency_binding(fetchcontent_base)
    build_calls = []

    @contextlib.contextmanager
    def production_prepare(
            cell, ccbench_pin, *, cxx, oracle_dependency_root,
            oracle_compiler, oracle_phase_marker):
        del oracle_compiler
        assert oracle_dependency_root == dependency.oracle_root
        oracle_phase_marker()
        with _fake_prepare(cell, ccbench_pin, cxx=cxx) as prepared:
            yield prepared

    def nonexact_builder(*args, **kwargs):
        build_calls.append((args, kwargs))
        pytest.fail("non-exact builder は呼ばれてはならない")

    monkeypatch.setattr(s8b_floor_campaign, "prepare_cell", production_prepare)
    monkeypatch.setattr(
        s8b_floor_campaign, "_prepare_floor_oracle_dependency",
        lambda _base, **_kwargs: dependency,
    )
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="exact buildcache.build_v2"):
        s8b_floor_campaign.build_cells(
            freeze,
            cells,
            ccbench_pin="0" * 40,
            out_root=tmp_path / "out",
            prepare_fn=production_prepare,
            contract=contract,
            verified_calibration=verified,
            build_fn=nonexact_builder,
            fetchcontent_base_dir=fetchcontent_base,
            phase_marker_root=marker_root,
        )
    assert build_calls == []


def test_dependency_bound_sort_best_default_builder_receives_literal_capability(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK,
        )
        if cell["configuration_id"] == "sort_best"
    )]
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    fetchcontent_base = tmp_path / "fetchcontent"
    fetchcontent_base.mkdir()
    lease = fetchcontent_base / ".sort-swo-dependency-test"
    canonical_root = lease / "canonical"
    canonical_root.mkdir(parents=True)
    dependency = dataclasses.replace(
        _fixture_dependency_binding(fetchcontent_base),
        oracle_root=canonical_root,
        canonical_lease_root=lease,
    )
    canonical_material = (
        s8b_floor_campaign._sort_swo_dependency_material
        .CanonicalDependencyMaterial(
            root=canonical_root,
            lease_root=lease,
            manifest_sha256=dependency.dependency_manifest_sha256,
            config_sha256=dependency.config_sha256,
            files=("PIN", "config.h"),
            source_root=dependency.source_root,
            head=dependency.observed_head,
        )
    )
    fake_build = _make_fake_build(tmp_path / "bin")
    observed = []

    @contextlib.contextmanager
    def production_prepare(
            cell, ccbench_pin, *, cxx, oracle_dependency_root,
            oracle_compiler, oracle_phase_marker):
        del oracle_compiler
        assert oracle_dependency_root == dependency.oracle_root
        oracle_phase_marker()
        with _fake_prepare(cell, ccbench_pin, cxx=cxx) as prepared:
            yield prepared

    def exact_builder(genome, **kwargs):
        observed.append(dict(kwargs))
        return fake_build(genome, **kwargs)

    monkeypatch.setattr(s8b_floor_campaign, "prepare_cell", production_prepare)

    def prebuild(_base, *, _material_sink, **_kwargs):
        _material_sink.append(canonical_material)
        return dependency

    monkeypatch.setattr(
        s8b_floor_campaign, "_prepare_floor_oracle_dependency", prebuild,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_build_dependency",
        lambda _result, _argv, **_kwargs: dependency,
    )
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "build_v2", exact_builder,
    )
    built = s8b_floor_campaign.build_cells(
        freeze,
        cells,
        ccbench_pin="0" * 40,
        out_root=tmp_path / "out",
        prepare_fn=production_prepare,
        contract=contract,
        verified_calibration=verified,
        fetchcontent_base_dir=fetchcontent_base,
        phase_marker_root=marker_root,
    )

    assert len(built) == 1
    assert not lease.exists()
    assert len(observed) == 1
    assert observed[0]["post_oracle_dependency_binding"] == {
        "fetchcontent_base_dir": str(fetchcontent_base.resolve()),
        "oracle_dependency_root": str(dependency.oracle_root),
        "dependency_manifest_sha256": (
            "8d0151cfaa0b86d1a2753e69f514633ec2fe6ee1077caed819fd3a426b501875"
        ),
        "masstree_head": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "config_sha256": (
            "a83df08ab41531df92b7ddc54fcb00b332345d0e9715047f8c75446d0c3855b3"
        ),
        "archive_sha256": (
            "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
        ),
    }


def test_production_floor_requires_staging_before_toolchain_or_oracle_or_build(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK,
        )
        if cell["configuration_id"] == "sort_best"
    )]
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    calls = []

    @contextlib.contextmanager
    def production_prepare(
            cell, ccbench_pin, *, cxx, oracle_dependency_root,
            oracle_compiler, oracle_phase_marker):
        del cell, ccbench_pin, cxx, oracle_dependency_root
        del oracle_compiler, oracle_phase_marker
        calls.append("oracle")
        pytest.fail("staging 拒否後に oracle へ到達してはいけない")
        yield

    def bind(*_args, **_kwargs):
        calls.append("toolchain")
        pytest.fail("staging 拒否後に toolchain preflight へ到達してはいけない")

    def build(*_args, **_kwargs):
        calls.append("build")
        pytest.fail("staging 拒否後に build へ到達してはいけない")

    monkeypatch.delenv("IZANAGI_FLOOR_JOB_STAGING", raising=False)
    monkeypatch.setattr(s8b_floor_campaign, "prepare_cell", production_prepare)
    monkeypatch.setattr(s8b_floor_campaign, "_bind_current_toolchain", bind)
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="floor job staging.*必須"):
        s8b_floor_campaign.build_cells(
            freeze,
            cells,
            ccbench_pin="0" * 40,
            out_root=tmp_path / "out",
            prepare_fn=production_prepare,
            contract=contract,
            verified_calibration=verified,
            build_fn=build,
            fetchcontent_base_dir=tmp_path / "cache",
        )
    assert calls == []


def test_production_floor_preflight_marker_precedes_toolchain_and_dependency_probes(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK,
        )
        if cell["configuration_id"] == "sort_best"
    )]
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    fetchcontent_base = tmp_path / "cache"
    fetchcontent_base.mkdir()
    dependency = _fixture_dependency_binding(fetchcontent_base)
    events = []

    def assert_preflight_marker() -> None:
        markers = list(marker_root.glob("phase-preflight-*.json"))
        assert len(markers) == 1
        payload = json.loads(markers[0].read_text(encoding="utf-8"))
        assert payload["cell"] == cells[0]["cell_id"]
        assert payload["phase"] == "preflight"

    def bind(candidate, *, cc, cxx):
        assert_preflight_marker()
        events.append("toolchain-preflight")
        return _fixture_toolchain_binding(candidate, cc=cc, cxx=cxx)

    def prebuild(configured, **_kwargs):
        assert configured == fetchcontent_base
        assert_preflight_marker()
        events.append("dependency-prebuild")
        return dependency

    @contextlib.contextmanager
    def production_prepare(
            cell, ccbench_pin, *, cxx, oracle_dependency_root,
            oracle_compiler, oracle_phase_marker):
        assert oracle_dependency_root == dependency.oracle_root
        oracle_phase_marker()
        events.append("oracle")
        with _fake_prepare(cell, ccbench_pin, cxx=cxx) as prepared:
            yield prepared

    fake_build = _make_fake_build(tmp_path / "bin")

    def build(genome, **kwargs):
        assert len(list(marker_root.glob("phase-build-*.json"))) == 1
        events.append("build")
        return fake_build(genome, **kwargs)

    monkeypatch.setattr(s8b_floor_campaign, "prepare_cell", production_prepare)
    monkeypatch.setattr(s8b_floor_campaign, "_bind_current_toolchain", bind)
    monkeypatch.setattr(
        s8b_floor_campaign, "_prepare_floor_oracle_dependency", prebuild,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_build_dependency",
        lambda _result, _argv, **_kwargs: dependency,
    )
    monkeypatch.setattr(s8b_floor_campaign.buildcache, "build_v2", build)
    built = s8b_floor_campaign.build_cells(
        freeze,
        cells,
        ccbench_pin="0" * 40,
        out_root=tmp_path / "out",
        prepare_fn=production_prepare,
        contract=contract,
        verified_calibration=verified,
        build_fn=build,
        fetchcontent_base_dir=fetchcontent_base,
        phase_marker_root=marker_root,
    )
    assert len(built) == 1
    assert events == [
        "toolchain-preflight", "dependency-prebuild", "oracle", "build",
    ]


def test_production_floor_prebuilds_one_shared_dependency_and_injects_only_sort(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    all_cells = s8b_floor_campaign.enumerate_cells(
        freeze, stock_configuration=_STOCK,
    )
    holdout_id = "rr79"
    cells = [
        cell for cell in all_cells
        if cell["cell_id"].startswith(f"{holdout_id}::")
    ]
    assert {cell["configuration_id"] for cell in cells} == set(_CONFIGS)
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    base = tmp_path / "fetchcontent"
    base.mkdir()
    dependency = dataclasses.replace(
        _fixture_dependency_binding(base),
        transport_mode="source-dir",
    )
    shared_header = dependency.source_root / "include" / "fixture.hh"
    shared_header.parent.mkdir(parents=True)
    shared_header.write_bytes(b"shared masstree compiler input\n")
    shared_header_sha256 = hashlib.sha256(shared_header.read_bytes()).hexdigest()
    events = []
    build_kwargs = {}
    receipt_roots = {}

    def prebuild(observed_base, **_kwargs):
        assert observed_base == base.resolve()
        events.append("prebuild")
        return dependency

    @contextlib.contextmanager
    def production_prepare(
            cell, ccbench_pin, *, cxx, oracle_dependency_root,
            oracle_compiler, oracle_phase_marker):
        if cell["configuration"] == "sort_best":
            assert oracle_dependency_root == dependency.oracle_root
            oracle_phase_marker()
            events.append("oracle")
        with _fake_prepare(cell, ccbench_pin, cxx=cxx) as prepared:
            yield prepared

    fake_build = _make_fake_build(tmp_path / "bin")

    def build(genome, **kwargs):
        cell_id = _FIXTURE_CELL_BY_TOKEN.get(kwargs["src_token"])
        build_kwargs[cell_id] = dict(kwargs)
        events.append(f"build:{cell_id}")
        result = fake_build(genome, **kwargs)
        snapshot_header = Path(kwargs["ccbench_dir"]) / "include" / "fixture.hh"
        result.compiler_input_manifest = {
            "schema_version": "s8b-compiler-input/v2",
            "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
            "input_policy": "snapshot-and-external-hashes/v1",
            "target": f"ycsb_{genome.protocol}.exe",
            "depfile_count": 1,
            "inputs": [
                {
                    "root": "fetchcontent-masstree",
                    "path": "include/fixture.hh",
                    "sha256": shared_header_sha256,
                },
                {
                    "root": "snapshot",
                    "path": "include/fixture.hh",
                    "sha256": hashlib.sha256(
                        snapshot_header.read_bytes()
                    ).hexdigest(),
                },
            ],
        }
        result.compiler_input_manifest_sha256 = hashlib.sha256(json.dumps(
            result.compiler_input_manifest, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        result.source_protection = None
        return result

    monkeypatch.setattr(s8b_floor_campaign, "prepare_cell", production_prepare)
    monkeypatch.setattr(
        s8b_floor_campaign, "_prepare_floor_oracle_dependency", prebuild,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_build_dependency",
        lambda _result, _argv, **_kwargs: dependency,
    )
    monkeypatch.setattr(s8b_floor_campaign.buildcache, "build_v2", build)
    original_issue = (
        s8b_floor_campaign._binary_admission.issue_binary_admission_receipt
    )

    def issue_spy(**kwargs):
        receipt_roots[kwargs["cell_id"]] = kwargs.get(
            "current_compiler_input_masstree_root"
        )
        return original_issue(**kwargs)

    monkeypatch.setattr(
        s8b_floor_campaign._binary_admission,
        "issue_binary_admission_receipt",
        issue_spy,
    )
    built = s8b_floor_campaign.build_cells(
        freeze, cells, ccbench_pin="0" * 40,
        out_root=tmp_path / "out", prepare_fn=production_prepare,
        contract=contract, verified_calibration=verified, build_fn=build,
        fetchcontent_base_dir=base.resolve(), phase_marker_root=marker_root,
    )
    assert events.count("prebuild") == 1
    assert events.index("prebuild") < events.index("oracle")
    sort_id = next(key for key in built if key.endswith("::sort_best"))
    non_sort_ids = set(built) - {sort_id}
    assert len(built) == len(_CONFIGS)
    assert len(non_sort_ids) == len(_CONFIGS) - 1
    assert build_kwargs[sort_id]["fetchcontent_base_dir"] == str(base.resolve())
    assert build_kwargs[sort_id]["fetchcontent_dependency_receipt"] == (
        _FIXTURE_DEPENDENCY_RECEIPT
    )
    assert build_kwargs[sort_id]["masstree_source_dir"] == str(
        base.resolve() / "masstree-src"
    )
    assert build_kwargs[sort_id]["mimalloc_source_dir"] == str(
        base.resolve() / "mimalloc-src"
    )
    assert build_kwargs[sort_id]["googletest_source_dir"] == str(
        base.resolve() / "googletest-src"
    )
    current_root = str(dependency.source_root)
    # 受理: 同じ relative path と hash の current root なら全 cell で receipt 検証が通る。
    assert {
        cell_id: kwargs["current_compiler_input_masstree_root"]
        for cell_id, kwargs in build_kwargs.items()
    } == {cell_id: current_root for cell_id in built}
    assert receipt_roots == {cell_id: current_root for cell_id in built}
    # 拒否: non-sort には oracle capability を付与しない。
    sort_only_keys = {
        "fetchcontent_base_dir",
        "fetchcontent_dependency_receipt",
        "fetchcontent_archive_sha256",
        "post_oracle_dependency_binding",
        "masstree_source_dir",
        "mimalloc_source_dir",
        "googletest_source_dir",
    }
    assert sort_only_keys <= set(build_kwargs[sort_id])
    for cell_id in non_sort_ids:
        assert sort_only_keys.isdisjoint(build_kwargs[cell_id])
    assert "_fetchcontent_base_dir" in built[sort_id]
    assert all(
        "_fetchcontent_base_dir" not in built[cell_id]
        for cell_id in non_sort_ids
    )
    store_root = tmp_path / "out" / "store"
    s8b_floor_campaign.store_binaries(
        built, store_root, out_root=tmp_path / "out",
        expected_ccbench_pin="0" * 40,
        expected_contract_sha256=contract.contract_sha256,
    )
    portable = s8b_floor_campaign.project_built_records(
        built, out_root=tmp_path / "out",
        expected_ccbench_pin="0" * 40,
        expected_contract_sha256=contract.contract_sha256,
    )
    assert "_fetchcontent_base_dir" not in portable[sort_id]
    assert f"-DFETCHCONTENT_BASE_DIR=${{FETCHCONTENT_BASE_DIR}}" in (
        portable[sort_id]["configure_argv"]
    )
    assert str(base.resolve()) not in json.dumps(portable, sort_keys=True)


def test_floor_dependency_prebuild_uses_pinned_checkout_and_exact_helper_once(
        tmp_path, monkeypatch):
    base = tmp_path / "fetchcontent"
    source = tmp_path / "prebuild-ccbench"
    base.mkdir()
    source.mkdir()
    binding = _fixture_dependency_binding(base)
    events = []
    staged_sources = {
        name: base / f"{name}-src"
        for name in ("masstree", "mimalloc", "googletest")
    }
    manifest = _fixture_toolchain_binding(
        env_attestation.load_verified_calibration(ec.lookup(ENV_TAG), ROOT),
        cc="site-cc", cxx="site-cxx",
    )

    @contextlib.contextmanager
    def checkout(pin, *, base_dir):
        events.append(("checkout", pin, base_dir))
        yield str(source.resolve())

    def prebuild(**kwargs):
        events.append(("prebuild", kwargs))
        return SimpleNamespace()

    def verify(
            observed_base, *, repo_root, expected_head,
            expected_toolchain_manifest_sha256):
        events.append(("verify", observed_base, repo_root, expected_head))
        return dataclasses.replace(
            binding,
            expected_toolchain_manifest_sha256=(
                expected_toolchain_manifest_sha256
            ),
        )

    monkeypatch.setattr(s8b_floor_campaign.patchharness, "checkout", checkout)
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "prepare_masstree_fetchcontent", prebuild,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_pristine_floor_dependency_sources",
        lambda observed_base, **_kwargs: (
            events.append(("pristine", observed_base)) or staged_sources
        ),
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_load_floor_masstree_payload_policy",
        lambda *_args, **_kwargs: (
            s8b_floor_campaign._LoadedFloorMasstreePayloadPolicy(
                schema_version="s8b-floor-masstree-payload/v3",
                name="masstree", pin="a" * 40,
                config_sha256=binding.config_sha256,
                archive_projection="gnu-ar-elf-nondebug/v1",
                archive_nondebug_sha256=(
                    binding.archive_nondebug_sha256
                ),
                raw_sha256="e" * 64,
            )
        ),
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source", verify,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_materialize_floor_oracle_dependency",
        lambda observed, **_kwargs: (
            dataclasses.replace(
                observed,
                oracle_root=base / "canonical-masstree",
                canonical_lease_root=base / ".sort-swo-dependency-fixture",
                dependency_manifest_sha256="8" * 64,
            ),
            SimpleNamespace(),
        ),
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_masstree_policy_pin", lambda _root: "a" * 40,
    )
    observed = s8b_floor_campaign._prepare_floor_oracle_dependency(
        base.resolve(), ccbench_pin="0" * 40,
        expected_toolchain_manifest=manifest,
    )
    assert observed.source_root == binding.source_root
    assert observed.transport_mode == "source-dir"
    assert observed.expected_config_sha256 == binding.config_sha256
    assert observed.expected_archive_nondebug_sha256 == (
        binding.archive_nondebug_sha256
    )
    assert observed.payload_policy_sha256 == "e" * 64
    assert [event[0] for event in events] == [
        "pristine", "checkout", "prebuild", "verify",
    ]
    assert events[2][1]["fetchcontent_base_dir"] == str(base.resolve())
    assert events[2][1]["ccbench_dir"] == str(source.resolve())
    assert events[2][1]["configure_timeout_s"] == 900
    assert events[2][1]["target_timeout_s"] == 900
    assert events[2][1]["masstree_source_dir"] == str(staged_sources["masstree"])
    assert events[2][1]["mimalloc_source_dir"] == str(staged_sources["mimalloc"])
    assert events[2][1]["googletest_source_dir"] == str(staged_sources["googletest"])


def test_floor_dependency_prebuild_captures_shared_policy_pins_once(
        tmp_path, monkeypatch):
    base = tmp_path / "fetchcontent"
    source = tmp_path / "prebuild-ccbench"
    base.mkdir()
    source.mkdir()
    staged_sources = {
        name: base / f"{name}-src"
        for name in ("masstree", "mimalloc", "googletest")
    }
    for path in staged_sources.values():
        path.mkdir()
    pins_a = {
        "masstree": "a" * 40,
        "mimalloc": "b" * 40,
        "googletest": "c" * 40,
    }
    pins_b = {name: "d" * 40 for name in pins_a}
    policy_reads = []
    observations = []

    def capture_policy(_root):
        policy_reads.append(True)
        return pins_a if len(policy_reads) == 1 else pins_b

    def pristine(observed_base, *, expected_pins, **_kwargs):
        observations.append(("pristine", observed_base, dict(expected_pins)))
        return staged_sources

    def load_payload(_root, *, expected_masstree_pin):
        observations.append(("payload", expected_masstree_pin))
        return s8b_floor_campaign._LoadedFloorMasstreePayloadPolicy(
            schema_version="s8b-floor-masstree-payload/v3",
            name="masstree", pin=expected_masstree_pin,
            config_sha256=_FIXTURE_DEPENDENCY_RECEIPT["config_sha256"],
            archive_projection="gnu-ar-elf-nondebug/v1",
            archive_nondebug_sha256=_FIXTURE_ARCHIVE_NONDEBUG_SHA256,
            raw_sha256="f" * 64,
        )

    @contextlib.contextmanager
    def checkout(_pin, *, base_dir):
        del base_dir
        yield str(source.resolve())

    def verify(_base, *, expected_head, **_kwargs):
        observations.append(("binding", expected_head))
        return dataclasses.replace(
            _fixture_dependency_binding(base),
            expected_head=expected_head,
            observed_head=expected_head,
        )

    monkeypatch.setattr(
        s8b_floor_campaign, "_floor_third_party_policy_pins", capture_policy,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_pristine_floor_dependency_sources", pristine,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_load_floor_masstree_payload_policy", load_payload,
    )
    monkeypatch.setattr(s8b_floor_campaign.patchharness, "checkout", checkout)
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "prepare_masstree_fetchcontent",
        lambda **_kwargs: SimpleNamespace(),
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source", verify,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_materialize_floor_oracle_dependency",
        lambda observed, **_kwargs: (
            dataclasses.replace(
                observed,
                oracle_root=base / "canonical-masstree",
                canonical_lease_root=base / ".sort-swo-dependency-fixture",
                dependency_manifest_sha256="8" * 64,
            ),
            SimpleNamespace(),
        ),
    )
    binding = s8b_floor_campaign._prepare_floor_oracle_dependency(
        base.resolve(), ccbench_pin="0" * 40,
        expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
        repo_root=tmp_path,
    )

    assert len(policy_reads) == 1
    assert observations == [
        ("payload", pins_a["masstree"]),
        ("pristine", base.resolve(), pins_a),
        ("binding", pins_a["masstree"]),
    ]
    assert dict(binding.captured_policy_pins) == pins_a
    assert binding.payload_policy_pin == pins_a["masstree"]


def test_floor_dependency_source_dir_reads_and_binds_payload_policy(
        tmp_path, monkeypatch):
    base = (tmp_path / "fetchcontent").resolve()
    base.mkdir()
    source = tmp_path / "prebuild-ccbench"
    source.mkdir()
    pin = "a" * 40
    binding = dataclasses.replace(
        _fixture_dependency_binding(base),
        expected_head=pin,
        observed_head=pin,
    )
    expected = s8b_floor_campaign._LoadedFloorMasstreePayloadPolicy(
        schema_version="s8b-floor-masstree-payload/v3",
        name="masstree",
        pin=pin,
        config_sha256=binding.config_sha256,
        archive_projection="gnu-ar-elf-nondebug/v1",
        archive_nondebug_sha256=binding.archive_nondebug_sha256,
        raw_sha256="f" * 64,
    )
    policy_reads = []
    staged_sources = {
        name: base / f"{name}-src"
        for name in ("masstree", "mimalloc", "googletest")
    }
    for path in staged_sources.values():
        path.mkdir()
    prebuild_calls = []

    @contextlib.contextmanager
    def checkout(_pin, *, base_dir):
        del base_dir
        yield str(source.resolve())

    monkeypatch.setattr(
        s8b_floor_campaign, "_floor_third_party_policy_pins",
        lambda _root: {"masstree": pin, "mimalloc": "b" * 40,
                       "googletest": "c" * 40},
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_load_floor_masstree_payload_policy",
        lambda *_args, **_kwargs: (policy_reads.append(True) or expected),
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_pristine_floor_dependency_sources",
        lambda *_args, **_kwargs: staged_sources,
    )
    monkeypatch.setattr(s8b_floor_campaign.patchharness, "checkout", checkout)
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "prepare_masstree_fetchcontent",
        lambda **kwargs: (prebuild_calls.append(kwargs) or SimpleNamespace()),
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source",
        lambda *_args, **_kwargs: binding,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_materialize_floor_oracle_dependency",
        lambda observed, **_kwargs: (observed, SimpleNamespace()),
    )
    observed = s8b_floor_campaign._prepare_floor_oracle_dependency(
        base,
        ccbench_pin="0" * 40,
        expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
        repo_root=tmp_path,
    )
    assert policy_reads == [True]
    assert observed.transport_mode == "source-dir"
    assert len(prebuild_calls) == 1
    for name in ("masstree", "mimalloc", "googletest"):
        assert prebuild_calls[0][f"{name}_source_dir"] == str(
            staged_sources[name]
        )
    assert observed.expected_config_sha256 == binding.config_sha256
    assert observed.expected_archive_nondebug_sha256 == (
        binding.archive_nondebug_sha256
    )
    assert observed.payload_policy_sha256 == "f" * 64


def test_floor_postflight_gate_rejects_source_override_and_accepts_base_only(
        tmp_path, monkeypatch):
    base = tmp_path / "fetchcontent"
    base.mkdir()
    before = _fixture_dependency_binding(base)
    before = _bind_fixture_payload_policy(tmp_path, before)
    result = _fixture_floor_build_result(
        fetchcontent_base_dir=str(base.resolve()),
        masstree_source_root_sha256=hashlib.sha256(
            str(base.resolve() / "masstree-src").encode("utf-8")
        ).hexdigest(),
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source",
        lambda *_args, **_kwargs: dataclasses.replace(
            before, source_st_dev=9, source_st_ino=10,
        ),
    )
    base_only = ["cmake", f"-DFETCHCONTENT_BASE_DIR={base.resolve()}"]
    after = s8b_floor_campaign._verify_floor_build_dependency(
        result, base_only, fetchcontent_base=base.resolve(), before=before,
        expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
        repo_root=tmp_path,
    )
    assert (after.source_st_dev, after.source_st_ino) == (9, 10)

    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="SOURCE_DIR override"):
        s8b_floor_campaign._verify_floor_build_dependency(
            result,
            base_only + [f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={tmp_path / 'other'}"],
            fetchcontent_base=base.resolve(), before=before, repo_root=tmp_path,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
        )


@pytest.mark.parametrize("cached", [False, True], ids=["fresh", "cache-hit"])
@pytest.mark.parametrize(
    ("mutation", "detail_code"),
    [
        (
            "source-inode",
            "floor-dependency-postflight-source-identity-drift",
        ),
        ("archive", "floor-dependency-postflight-archive-drift"),
    ],
)
def test_floor_strict_postflight_rejects_run_local_dependency_replacement(
        tmp_path, cached, mutation, detail_code):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    base = tmp_path / "fetchcontent"
    source = base / "masstree-src"
    head = _git_fixture_source(source)
    (source / "config.h").write_text("#pragma once\n", encoding="utf-8")
    archive = source / "libkohler_masstree_json.a"
    _write_masstree_archive(archive, text=b"prebuild archive")
    before = s8b_floor_campaign._verify_floor_oracle_dependency_source(
        base, repo_root=repo_root, expected_head=head,
        expected_toolchain_manifest_sha256=(
            _fixture_toolchain_manifest_sha256()
        ),
    )
    before = dataclasses.replace(
        before,
        oracle_root=base / "canonical-masstree",
        canonical_lease_root=base / ".sort-swo-dependency-fixture",
        dependency_manifest_sha256=(
            "8d0151cfaa0b86d1a2753e69f514633ec2fe6ee1077caed819fd3a426b501875"
        ),
        captured_policy_pins=(
            ("googletest", "c" * 40),
            ("masstree", head),
            ("mimalloc", "b" * 40),
        ),
        expected_config_sha256=before.config_sha256,
        expected_archive_nondebug_sha256=(
            before.archive_nondebug_sha256
        ),
        payload_policy_pin=head,
    )
    before = _bind_fixture_payload_policy(repo_root, before)
    if mutation == "source-inode":
        detached = base / "masstree-src-before"
        source.rename(detached)
        shutil.copytree(detached, source)
        assert source.stat().st_ino != before.source_st_ino
    else:
        _write_masstree_archive(
            archive, text=b"same-run archive replacement",
        )
    result = _fixture_floor_build_result(
        cached=cached,
        fetchcontent_base_dir=str(base.resolve()),
        masstree_source_root_sha256=hashlib.sha256(
            str(base.resolve() / "masstree-src").encode("utf-8")
        ).hexdigest(),
    )
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._verify_floor_build_dependency(
            result,
            ["cmake", f"-DFETCHCONTENT_BASE_DIR={base.resolve()}"],
            fetchcontent_base=base.resolve(), before=before,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
            repo_root=repo_root, require_run_local_identity=True,
        )
    assert caught.value.diagnostic.detail_code == detail_code


def test_floor_strict_postflight_rejects_captured_payload_pin_mixture(
        tmp_path):
    base = tmp_path / "fetchcontent"
    base.mkdir()
    before = dataclasses.replace(
        _fixture_dependency_binding(base),
        transport_mode="source-dir",
        payload_policy_pin="d" * 40,
    )
    result = _fixture_floor_build_result(
        cached=False,
        fetchcontent_base_dir=str(base.resolve()),
        masstree_source_root_sha256=hashlib.sha256(
            str(base.resolve() / "masstree-src").encode("utf-8")
        ).hexdigest(),
    )
    argv = [
        "cmake", f"-DFETCHCONTENT_BASE_DIR={base.resolve()}",
        f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={base.resolve() / 'masstree-src'}",
        f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={base.resolve() / 'mimalloc-src'}",
        f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={base.resolve() / 'googletest-src'}",
    ]
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._verify_floor_build_dependency(
            result, argv, fetchcontent_base=base.resolve(), before=before,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
            repo_root=tmp_path, require_run_local_identity=True,
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-postflight-payload-policy-mismatch"
    )


def test_floor_postflight_staged_source_set_and_expected_hash_are_enforced(
        tmp_path, monkeypatch):
    base = tmp_path / "fetchcontent"
    base.mkdir()
    policy_path = tmp_path / "tools/pegasus/policies/floor_masstree_payload_v1.json"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_bytes(b"fixture payload policy v1\n")
    before = dataclasses.replace(
        _fixture_dependency_binding(base),
        config_sha256="b" * 64,
        transport_mode="source-dir",
        expected_config_sha256="b" * 64,
        payload_policy_sha256=hashlib.sha256(policy_path.read_bytes()).hexdigest(),
    )
    result = _fixture_floor_build_result(
        fetchcontent_base_dir=str(base.resolve()),
        cached=False,
        masstree_source_root_sha256=hashlib.sha256(
            str(base.resolve() / "masstree-src").encode("utf-8")
        ).hexdigest(),
    )
    argv = [
        "cmake", f"-DFETCHCONTENT_BASE_DIR={base.resolve()}",
        f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={base.resolve() / 'masstree-src'}",
        f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={base.resolve() / 'mimalloc-src'}",
        f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={base.resolve() / 'googletest-src'}",
    ]
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source",
        lambda *_args, **_kwargs: before,
    )
    assert s8b_floor_campaign._verify_floor_build_dependency(
        result, argv, fetchcontent_base=base.resolve(), before=before,
        expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
        repo_root=tmp_path,
    ).transport_mode == "source-dir"

    bad_expected = dataclasses.replace(
        before, expected_config_sha256="d" * 64,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source",
        lambda *_args, **_kwargs: bad_expected,
    )
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError,
            match="独立 expected hash") as caught:
        s8b_floor_campaign._verify_floor_build_dependency(
            result, argv, fetchcontent_base=base.resolve(), before=bad_expected,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
            repo_root=tmp_path,
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-postflight-config-expected-mismatch"
    )

    policy_path.write_bytes(b"fixture payload policy v2\n")
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source",
        lambda *_args, **_kwargs: before,
    )
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError,
            match="payload policy bytes") as caught:
        s8b_floor_campaign._verify_floor_build_dependency(
            result, argv, fetchcontent_base=base.resolve(), before=before,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
            repo_root=tmp_path,
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-postflight-payload-policy-mismatch"
    )


def test_floor_postflight_cache_hit_uses_content_receipt_not_prior_absolute_root(
        tmp_path, monkeypatch):
    base_a = tmp_path / "fetchcontent-a"
    base_b = tmp_path / "fetchcontent-b"
    base_a.mkdir()
    base_b.mkdir()
    before = _fixture_dependency_binding(base_b.resolve())
    before = _bind_fixture_payload_policy(tmp_path, before)
    argv = ["cmake", f"-DFETCHCONTENT_BASE_DIR={base_b.resolve()}"]
    prior_root_sha256 = hashlib.sha256(
        str(base_a.resolve() / "masstree-src").encode("utf-8")
    ).hexdigest()
    hit = _fixture_floor_build_result(
        cached=True,
        fetchcontent_base_dir=str(base_b.resolve()),
        masstree_source_root_sha256=prior_root_sha256,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source",
        lambda *_args, **_kwargs: before,
    )
    accepted = s8b_floor_campaign._verify_floor_build_dependency(
        hit, argv, fetchcontent_base=base_b.resolve(), before=before,
        expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
        repo_root=tmp_path,
    )
    assert accepted.archive_nondebug_sha256 == before.archive_nondebug_sha256

    fresh = SimpleNamespace(**{**vars(hit), "cached": False})
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="実効 masstree source root"):
        s8b_floor_campaign._verify_floor_build_dependency(
            fresh, argv, fetchcontent_base=base_b.resolve(), before=before,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
            repo_root=tmp_path,
        )


def test_floor_postflight_base_only_rejects_policy_and_projection_drift(
        tmp_path, monkeypatch):
    base = tmp_path / "fetchcontent"
    base.mkdir()
    before = _bind_fixture_payload_policy(
        tmp_path, _fixture_dependency_binding(base),
    )
    result = _fixture_floor_build_result(
        cached=True,
        fetchcontent_base_dir=str(base.resolve()),
        masstree_source_root_sha256="0" * 64,
    )
    argv = ["cmake", f"-DFETCHCONTENT_BASE_DIR={base.resolve()}"]
    changed_projection = dataclasses.replace(
        before, archive_nondebug_sha256="0" * 64,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source",
        lambda *_args, **_kwargs: changed_projection,
    )
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._verify_floor_build_dependency(
            result, argv, fetchcontent_base=base.resolve(), before=before,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
            repo_root=tmp_path,
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-postflight-archive-expected-mismatch"
    )

    policy_path = (
        tmp_path / "tools/pegasus/policies/floor_masstree_payload_v1.json"
    )
    policy_path.write_bytes(policy_path.read_bytes() + b" ")
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source",
        lambda *_args, **_kwargs: before,
    )
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._verify_floor_build_dependency(
            result, argv, fetchcontent_base=base.resolve(), before=before,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
            repo_root=tmp_path,
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-postflight-payload-policy-mismatch"
    )


def test_floor_postflight_gate_rejects_effective_root_and_content_drift(
        tmp_path, monkeypatch):
    base = tmp_path / "fetchcontent"
    base.mkdir()
    before = _bind_fixture_payload_policy(
        tmp_path, _fixture_dependency_binding(base),
    )
    argv = ["cmake", f"-DFETCHCONTENT_BASE_DIR={base.resolve()}"]
    wrong_root = _fixture_floor_build_result(
        fetchcontent_base_dir=str(base.resolve()),
        masstree_source_root_sha256="0" * 64,
    )
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="実効 masstree source root"):
        s8b_floor_campaign._verify_floor_build_dependency(
            wrong_root, argv, fetchcontent_base=base.resolve(), before=before,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
            repo_root=tmp_path,
        )

    result = _fixture_floor_build_result(
        fetchcontent_base_dir=str(base.resolve()),
        masstree_source_root_sha256=hashlib.sha256(
            str(base.resolve() / "masstree-src").encode("utf-8")
        ).hexdigest(),
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source",
        lambda *_args, **_kwargs: dataclasses.replace(
            before, config_sha256="d" * 64,
        ),
    )
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="config.h が変化"):
        s8b_floor_campaign._verify_floor_build_dependency(
            result, argv, fetchcontent_base=base.resolve(), before=before,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
            repo_root=tmp_path,
        )


def test_floor_postflight_gate_classifies_head_drift(tmp_path, monkeypatch):
    base = tmp_path / "fetchcontent"
    base.mkdir()
    before = _bind_fixture_payload_policy(
        tmp_path, _fixture_dependency_binding(base),
    )
    result = _fixture_floor_build_result(
        fetchcontent_base_dir=str(base.resolve()),
        masstree_source_root_sha256=hashlib.sha256(
            str(base.resolve() / "masstree-src").encode("utf-8")
        ).hexdigest(),
    )

    def head_mismatch(*_args, **_kwargs):
        raise s8b_floor_campaign._FloorOraclePreflightError(
            "fixture HEAD mismatch",
            detail_code="floor-dependency-head-mismatch",
            origin="floor-dependency:masstree",
            outcome="invalid-path",
            path=base / "masstree-src",
        )

    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source",
        head_mismatch,
    )
    with pytest.raises(s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._verify_floor_build_dependency(
            result, ["cmake", f"-DFETCHCONTENT_BASE_DIR={base.resolve()}"],
            fetchcontent_base=base.resolve(), before=before, repo_root=tmp_path,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-postflight-head-drift"
    )


def test_floor_postflight_head_drift_outranks_source_stat_failure(
        tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    base = tmp_path / "fetchcontent"
    source = base / "masstree-src"
    head = _git_fixture_source(source)
    (source / "config.h").write_text("#pragma once\n", encoding="utf-8")
    _write_masstree_archive(source / "libkohler_masstree_json.a")
    before = s8b_floor_campaign._verify_floor_oracle_dependency_source(
        base.resolve(), repo_root=repo_root, expected_head=head,
        expected_toolchain_manifest_sha256=(
            _fixture_toolchain_manifest_sha256()
        ),
    )
    before = dataclasses.replace(
        before,
        expected_config_sha256=before.config_sha256,
        expected_archive_nondebug_sha256=before.archive_nondebug_sha256,
        payload_policy_pin=head,
    )
    before = _bind_fixture_payload_policy(repo_root, before)
    (source / "tracked.hh").write_text("// replacement HEAD\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(source), "add", "tracked.hh"], check=True,
    )
    subprocess.run(
        [
            "git", "-C", str(source), "-c", "user.name=Fixture",
            "-c", "user.email=fixture@example.invalid", "commit", "-qm",
            "replacement HEAD",
        ],
        check=True,
    )
    result = _fixture_floor_build_result(
        cached=False,
        fetchcontent_base_dir=str(base.resolve()),
        masstree_source_root_sha256=hashlib.sha256(
            str(source.resolve()).encode("utf-8")
        ).hexdigest(),
    )
    stat_calls = []

    def unavailable_stat(path):
        stat_calls.append(path)
        raise FileNotFoundError("fixture simultaneous stat failure")

    monkeypatch.setattr(
        s8b_floor_campaign, "_stat_floor_dependency_root", unavailable_stat,
    )
    with pytest.raises(s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._verify_floor_build_dependency(
            result, ["cmake", f"-DFETCHCONTENT_BASE_DIR={base.resolve()}"],
            fetchcontent_base=base.resolve(), before=before,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
            repo_root=repo_root,
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-postflight-head-drift"
    )
    assert stat_calls == []


@pytest.mark.parametrize("cached", [False, True], ids=["fresh", "cache-hit"])
@pytest.mark.parametrize(
    ("failure_kind", "detail_code"),
    [
        (
            "object",
            "floor-dependency-postflight-toolchain-manifest-mismatch",
        ),
        ("hash", "floor-dependency-postflight-toolchain-hash-mismatch"),
        (
            "missing",
            "floor-dependency-postflight-toolchain-manifest-mismatch",
        ),
    ],
)
def test_floor_postflight_rejects_build_result_toolchain_mismatch(
        tmp_path, monkeypatch, cached, failure_kind, detail_code):
    base = tmp_path / "fetchcontent"
    base.mkdir()
    before = _fixture_dependency_binding(base)
    kwargs = {
        "cached": cached,
        "fetchcontent_base_dir": str(base.resolve()),
        "masstree_source_root_sha256": hashlib.sha256(
            str(base.resolve() / "masstree-src").encode("utf-8")
        ).hexdigest(),
    }
    result = _fixture_floor_build_result(**kwargs)
    if failure_kind == "object":
        result.toolchain_manifest = {
            **_FIXTURE_TOOLCHAIN_MANIFEST,
            "cxx": {
                **_FIXTURE_TOOLCHAIN_MANIFEST["cxx"],
                "version": "different toolchain",
            },
        }
        result.toolchain_manifest_sha256 = (
            _fixture_toolchain_manifest_sha256(result.toolchain_manifest)
        )
    elif failure_kind == "hash":
        result.toolchain_manifest_sha256 = "0" * 64
    else:
        result.toolchain_manifest = None
        result.toolchain_manifest_sha256 = None
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source",
        lambda *_args, **_kwargs: before,
    )
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._verify_floor_build_dependency(
            result,
            ["cmake", f"-DFETCHCONTENT_BASE_DIR={base.resolve()}"],
            fetchcontent_base=base.resolve(), before=before,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
            repo_root=tmp_path,
        )
    assert caught.value.diagnostic.detail_code == detail_code


def test_floor_postflight_rejects_binding_toolchain_hash_only_mismatch(
        tmp_path):
    base = tmp_path / "fetchcontent"
    base.mkdir()
    before = dataclasses.replace(
        _fixture_dependency_binding(base),
        expected_toolchain_manifest_sha256="0" * 64,
    )
    result = _fixture_floor_build_result(
        cached=False,
        fetchcontent_base_dir=str(base.resolve()),
        masstree_source_root_sha256=hashlib.sha256(
            str(base.resolve() / "masstree-src").encode("utf-8")
        ).hexdigest(),
    )
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._verify_floor_build_dependency(
            result,
            ["cmake", f"-DFETCHCONTENT_BASE_DIR={base.resolve()}"],
            fetchcontent_base=base.resolve(), before=before,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
            repo_root=tmp_path,
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-postflight-toolchain-hash-mismatch"
    )


def test_floor_oracle_preflight_diagnostic_rejects_unknown_detail_code():
    with pytest.raises(ValueError, match="未知の floor oracle preflight"):
        s8b_floor_campaign._FloorOraclePreflightDiagnostic(
            detail_code="floor-preflight-open-ended-error",
            origin="fixture",
            outcome="invalid-path",
        )


def test_floor_canonical_manifest_diagnostic_records_both_hashes_only():
    diagnostic = s8b_floor_campaign._FloorOraclePreflightDiagnostic(
        detail_code="floor-dependency-canonical-manifest-mismatch",
        origin="floor-dependency-canonical:manifest",
        outcome="identity-mismatch",
        generated_manifest_sha256="1" * 64,
        expected_manifest_sha256="2" * 64,
    )
    payload = diagnostic.private_dict()
    assert payload["generated_manifest_sha256"] == "1" * 64
    assert payload["expected_manifest_sha256"] == "2" * 64
    assert set(payload) == {
        "detail_code", "origin", "outcome", "path",
        "generated_manifest_sha256", "expected_manifest_sha256",
    }


def _git_fixture_source(path: Path) -> str:
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    (path / "tracked.hh").write_text("// pinned\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(path), "add", "tracked.hh"], check=True,
    )
    subprocess.run(
        [
            "git", "-C", str(path), "-c", "user.name=Fixture",
            "-c", "user.email=fixture@example.invalid", "commit", "-qm", "pin",
        ],
        check=True,
    )
    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def _fixture_floor_reservation_binding(
        nonce: str = "a" * 32,
) -> reservation.ReservationBinding:
    return reservation.ReservationBinding(
        job_id="fixture-job",
        requested_s=36000,
        scheduler_started_epoch=1.0,
        deadline_epoch=36001.0,
        host="fixture-host",
        boot_id="fixture-boot",
        script_sha256="b" * 64,
        nonce=nonce,
    )


def _fixture_floor_submission_payload(
        repo_root: Path, *, env_tag: str,
        binding: reservation.ReservationBinding, marker: str = "bound",
) -> Path:
    payload_root = floor_submit_receipt.receipt_path(
        repo_root, env_tag=env_tag, nonce=binding.nonce,
    ).parent / "masstree-payload"
    for name in ("masstree", "mimalloc", "googletest"):
        source = payload_root / f"{name}-src"
        (source / ".git").mkdir(parents=True)
        (source / ".git" / "fixture").write_text(
            f"{marker}:{name}\n", encoding="utf-8",
        )
        executable = source / "fixture-tool"
        executable.write_text(f"{marker}:{name}\n", encoding="utf-8")
        executable.chmod(0o751)
        (source / "fixture-link").symlink_to("fixture-tool")
        source.chmod(0o750)
    return payload_root


def _fixture_floor_git_submission_payload(
        repo_root: Path, *, env_tag: str,
        binding: reservation.ReservationBinding,
        dirty_source: str | None = None,
) -> tuple[Path, dict[str, str]]:
    payload_root = floor_submit_receipt.receipt_path(
        repo_root, env_tag=env_tag, nonce=binding.nonce,
    ).parent / "masstree-payload"
    pins = {}
    for name in ("masstree", "mimalloc", "googletest"):
        source = payload_root / f"{name}-src"
        _git_fixture_source(source)
        if name == "masstree":
            (source / "config.h").write_text(
                "#define MASSTREE_CONFIG 1\n", encoding="utf-8",
            )
            _write_masstree_archive(source / "libkohler_masstree_json.a")
            subprocess.run(
                ["git", "-C", str(source), "add", "config.h",
                 "libkohler_masstree_json.a"],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(source), "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@example.invalid", "commit",
                    "-qm", "floor payload",
                ],
                check=True,
            )
        pins[name] = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        if name == dirty_source:
            (source / "dirty.untracked").write_text(
                "dirty\n", encoding="utf-8",
            )
    return payload_root, pins


def test_floor_fetchcontent_default_uses_bound_nonce_and_preserves_copy_semantics(
        tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    contract = ec.lookup(ENV_TAG)
    bound = _fixture_floor_reservation_binding("a" * 32)
    ambient = _fixture_floor_reservation_binding("c" * 32)
    _fixture_floor_submission_payload(
        repo_root, env_tag=contract.env_tag, binding=bound, marker="bound",
    )
    _fixture_floor_submission_payload(
        repo_root, env_tag=contract.env_tag, binding=ambient, marker="ambient",
    )
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch.resolve()))
    monkeypatch.setenv("IZANAGI_SUBMISSION_NONCE", ambient.nonce)
    canonical_receipt_path = floor_submit_receipt.receipt_path
    receipt_calls = []

    def receipt_path_spy(observed_root, *, env_tag, nonce):
        receipt_calls.append((observed_root, env_tag, nonce))
        return canonical_receipt_path(
            observed_root, env_tag=env_tag, nonce=nonce,
        )

    monkeypatch.setattr(
        s8b_floor_campaign.floor_submit_receipt,
        "receipt_path",
        receipt_path_spy,
    )

    staged = s8b_floor_campaign._stage_default_floor_fetchcontent_payload(
        repo_root=repo_root, contract=contract, reservation_binding=bound,
    )

    assert receipt_calls == [(repo_root.resolve(), contract.env_tag, bound.nonce)]
    assert staged == scratch.resolve() / "izanagi-floor-fetchcontent"
    for name in ("masstree", "mimalloc", "googletest"):
        source = staged / f"{name}-src"
        assert source.is_dir() and not source.is_symlink()
        assert stat.S_IMODE(source.stat().st_mode) == 0o750
        assert (source / ".git" / "fixture").read_text(
            encoding="utf-8",
        ) == f"bound:{name}\n"
        assert stat.S_IMODE((source / "fixture-tool").stat().st_mode) == 0o751
        assert (source / "fixture-link").is_symlink()
        assert os.readlink(source / "fixture-link") == "fixture-tool"


def test_floor_fetchcontent_default_rejects_missing_binding_without_ambient_fallback(
        tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    contract = ec.lookup(ENV_TAG)
    ambient = _fixture_floor_reservation_binding("c" * 32)
    _fixture_floor_submission_payload(
        repo_root, env_tag=contract.env_tag, binding=ambient,
    )
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch.resolve()))
    monkeypatch.setenv("IZANAGI_SUBMISSION_NONCE", ambient.nonce)

    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError,
            match="reservation binding がない") as caught:
        s8b_floor_campaign._stage_default_floor_fetchcontent_payload(
            repo_root=repo_root, contract=contract, reservation_binding=None,
        )
    assert caught.value.diagnostic.origin == (
        "reservation-binding:floor-fetchcontent"
    )
    assert not (scratch / "izanagi-floor-fetchcontent").exists()


def test_floor_fetchcontent_default_rejects_symlinked_fixed_prefix_ancestor(
        tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    external_output = tmp_path / "external-output"
    external_output.mkdir()
    (repo_root / "output").symlink_to(external_output, target_is_directory=True)
    contract = ec.lookup(ENV_TAG)
    binding = _fixture_floor_reservation_binding()
    _fixture_floor_submission_payload(
        repo_root, env_tag=contract.env_tag, binding=binding,
    )
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch.resolve()))

    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError,
            match="固定 path component") as caught:
        s8b_floor_campaign._stage_default_floor_fetchcontent_payload(
            repo_root=repo_root, contract=contract,
            reservation_binding=binding,
        )
    assert caught.value.diagnostic.path == repo_root / "output"
    assert not (scratch / "izanagi-floor-fetchcontent").exists()


@pytest.mark.parametrize(
    "failure_kind",
    [
        "payload-symlink", "staging-exists", "staging-symlink",
        "masstree-missing", "mimalloc-missing", "googletest-missing",
        "source-symlink",
    ],
)
def test_floor_fetchcontent_default_rejects_unsafe_layout(
        tmp_path, monkeypatch, failure_kind):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    contract = ec.lookup(ENV_TAG)
    binding = _fixture_floor_reservation_binding()
    payload_root = _fixture_floor_submission_payload(
        repo_root, env_tag=contract.env_tag, binding=binding,
    )
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    staging = scratch / "izanagi-floor-fetchcontent"
    monkeypatch.setenv("TMPDIR", str(scratch.resolve()))

    if failure_kind == "payload-symlink":
        real_payload = payload_root.with_name("payload-real")
        payload_root.rename(real_payload)
        payload_root.symlink_to(real_payload, target_is_directory=True)
    elif failure_kind == "staging-exists":
        staging.mkdir()
    elif failure_kind == "staging-symlink":
        target = tmp_path / "staging-target"
        target.mkdir()
        staging.symlink_to(target, target_is_directory=True)
    elif failure_kind.endswith("-missing"):
        shutil.rmtree(payload_root / f"{failure_kind[:-8]}-src")
    else:
        source = payload_root / "masstree-src"
        real_source = payload_root / "masstree-real"
        source.rename(real_source)
        source.symlink_to(real_source, target_is_directory=True)

    with pytest.raises(s8b_floor_campaign._FloorOraclePreflightError):
        s8b_floor_campaign._stage_default_floor_fetchcontent_payload(
            repo_root=repo_root, contract=contract,
            reservation_binding=binding,
        )


def test_floor_fetchcontent_default_rejects_repo_destination_before_copy(
        tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    contract = ec.lookup(ENV_TAG)
    binding = _fixture_floor_reservation_binding()
    _fixture_floor_submission_payload(
        repo_root, env_tag=contract.env_tag, binding=binding,
    )
    scratch = repo_root / "output" / "job-scratch"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch.resolve()))

    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError,
            match="repo 外") as caught:
        s8b_floor_campaign._stage_default_floor_fetchcontent_payload(
            repo_root=repo_root, contract=contract,
            reservation_binding=binding,
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-base-inside-repository"
    )
    assert not (scratch / "izanagi-floor-fetchcontent").exists()


def test_floor_default_transport_dirty_payload_reaches_pristine_pin_gate(
        tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    contract = ec.lookup(ENV_TAG)
    binding = _fixture_floor_reservation_binding()
    _payload, pins = _fixture_floor_git_submission_payload(
        repo_root, env_tag=contract.env_tag, binding=binding,
        dirty_source="mimalloc",
    )
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch.resolve()))
    staged = s8b_floor_campaign._stage_default_floor_fetchcontent_payload(
        repo_root=repo_root, contract=contract, reservation_binding=binding,
    )
    downstream = []
    fixture_binding = _fixture_dependency_binding(staged)
    expected_payload = s8b_floor_campaign._LoadedFloorMasstreePayloadPolicy(
        schema_version="s8b-floor-masstree-payload/v3",
        name="masstree",
        pin=pins["masstree"],
        config_sha256=fixture_binding.config_sha256,
        archive_projection="gnu-ar-elf-nondebug/v1",
        archive_nondebug_sha256=fixture_binding.archive_nondebug_sha256,
        raw_sha256="f" * 64,
    )
    prebuild_source = tmp_path / "prebuild-ccbench"
    prebuild_source.mkdir()

    @contextlib.contextmanager
    def checkout(_pin, *, base_dir):
        downstream.append(("checkout", base_dir))
        yield str(prebuild_source)

    monkeypatch.setattr(
        s8b_floor_campaign, "_floor_third_party_policy_pins",
        lambda _root: pins,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_load_floor_masstree_payload_policy",
        lambda *_args, **_kwargs: (
            downstream.append("payload-policy") or expected_payload
        ),
    )
    monkeypatch.setattr(
        s8b_floor_campaign.patchharness, "checkout", checkout,
    )
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "prepare_masstree_fetchcontent",
        lambda **_kwargs: downstream.append("prebuild") or SimpleNamespace(),
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_oracle_dependency_source",
        lambda *_args, **_kwargs: (
            downstream.append("binding") or fixture_binding
        ),
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_materialize_floor_oracle_dependency",
        lambda observed, **_kwargs: (
            downstream.append("materialize") or observed,
            SimpleNamespace(),
        ),
    )

    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._prepare_floor_oracle_dependency(
            staged,
            ccbench_pin="0" * 40,
            expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
            repo_root=repo_root,
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-staged-source-dirty"
    )
    assert downstream == ["payload-policy"]


def test_floor_default_transport_passes_three_verified_source_dirs(
        tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    contract = ec.lookup(ENV_TAG)
    reservation_binding = _fixture_floor_reservation_binding()
    _payload, pins = _fixture_floor_git_submission_payload(
        repo_root, env_tag=contract.env_tag, binding=reservation_binding,
    )
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch.resolve()))
    staged = s8b_floor_campaign._stage_default_floor_fetchcontent_payload(
        repo_root=repo_root, contract=contract,
        reservation_binding=reservation_binding,
    )
    masstree_source = staged / "masstree-src"
    config_sha256 = s8b_floor_campaign._sha256_regular_file(
        masstree_source / "config.h",
    )
    archive = s8b_floor_campaign._verify_masstree_archive(
        masstree_source / "libkohler_masstree_json.a",
    )
    expected_payload = s8b_floor_campaign._LoadedFloorMasstreePayloadPolicy(
        schema_version="s8b-floor-masstree-payload/v3",
        name="masstree",
        pin=pins["masstree"],
        config_sha256=config_sha256,
        archive_projection="gnu-ar-elf-nondebug/v1",
        archive_nondebug_sha256=archive.archive_nondebug_sha256,
        raw_sha256="f" * 64,
    )
    ccbench = tmp_path / "prebuild-ccbench"
    ccbench.mkdir()
    prebuild_calls = []

    @contextlib.contextmanager
    def checkout(_pin, *, base_dir):
        assert base_dir == str(repo_root / "external" / "ccbench")
        yield str(ccbench.resolve())

    def prebuild(**kwargs):
        prebuild_calls.append(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(
        s8b_floor_campaign, "_floor_third_party_policy_pins",
        lambda _root: pins,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_load_floor_masstree_payload_policy",
        lambda *_args, **_kwargs: expected_payload,
    )
    monkeypatch.setattr(s8b_floor_campaign.patchharness, "checkout", checkout)
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "prepare_masstree_fetchcontent",
        prebuild,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_materialize_floor_oracle_dependency",
        lambda observed, **_kwargs: (
            dataclasses.replace(
                observed,
                oracle_root=staged / "canonical",
                canonical_lease_root=staged / ".lease",
                dependency_manifest_sha256="8" * 64,
            ),
            SimpleNamespace(),
        ),
    )

    observed = s8b_floor_campaign._prepare_floor_oracle_dependency(
        staged,
        ccbench_pin="0" * 40,
        expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
        repo_root=repo_root,
    )

    assert observed.transport_mode == "source-dir"
    assert dict(observed.captured_policy_pins) == pins
    assert len(prebuild_calls) == 1
    call = prebuild_calls[0]
    assert call["fetchcontent_base_dir"] == str(staged)
    for name in ("masstree", "mimalloc", "googletest"):
        assert call[f"{name}_source_dir"] == str(staged / f"{name}-src")


def test_default_staging_and_claim_seam_basis_keep_raw_argument_separate(
        tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    contract = ec.lookup(ENV_TAG)
    binding = _fixture_floor_reservation_binding()
    _fixture_floor_submission_payload(
        repo_root, env_tag=contract.env_tag, binding=binding,
    )
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch.resolve()))
    staged = s8b_floor_campaign._stage_default_floor_fetchcontent_payload(
        repo_root=repo_root, contract=contract, reservation_binding=binding,
    )
    assert staged.is_dir()
    captured_seams = s8b_floor_campaign._nondefault_campaign_seams()
    assert sorted(captured_seams) == []

    source = textwrap.dedent(inspect.getsource(
        s8b_floor_campaign._run_campaign_core,
    ))
    tree = ast.parse(source)
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name)
            and node.func.id in {"_nondefault_campaign_seams", "build_cells"}
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == "_reserve_floor_holdout_observations_core"
        )
    ]
    classifier = next(
        call for call in calls
        if isinstance(call.func, ast.Name)
        and call.func.id == "_nondefault_campaign_seams"
    )
    classifier_position = (classifier.lineno, classifier.col_offset)
    raw_argument_rebindings = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Store)
        and node.id == "fetchcontent_base_dir"
        and (node.lineno, node.col_offset) < classifier_position
    ]
    assert raw_argument_rebindings == []
    assert ast.unparse(next(
        keyword.value for keyword in classifier.keywords
        if keyword.arg == "fetchcontent_base_dir"
    )) == "fetchcontent_base_dir"
    build_calls = [
        call for call in calls
        if isinstance(call.func, ast.Name) and call.func.id == "build_cells"
    ]
    assert len(build_calls) == 2
    assert classifier.lineno < min(call.lineno for call in build_calls)
    assert all(ast.unparse(next(
        keyword.value for keyword in call.keywords
        if keyword.arg == "fetchcontent_base_dir"
    )) == "fetchcontent_base_dir" for call in build_calls)
    claim = next(
        call for call in calls
        if isinstance(call.func, ast.Attribute)
        and call.func.attr == "_reserve_floor_holdout_observations_core"
    )
    assert ast.unparse(next(
        keyword.value for keyword in claim.keywords
        if keyword.arg == "nondefault_seams"
    )) == "sorted(nondefault_seams)"


def test_floor_oracle_dependency_compares_head_and_hashes_regular_config(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    cache_root = tmp_path / "cache"
    source = cache_root / "masstree-src"
    head = _git_fixture_source(source)
    config = source / "config.h"
    config.write_text("#define MASSTREE_CONFIG 1\n", encoding="utf-8")
    archive = source / "libkohler_masstree_json.a"
    _write_masstree_archive(archive)

    binding = s8b_floor_campaign._verify_floor_oracle_dependency_source(
        cache_root, repo_root=repo_root, expected_head=head,
        expected_toolchain_manifest_sha256=(
            _fixture_toolchain_manifest_sha256()
        ),
    )
    assert binding.source_root == source.resolve()
    assert binding.expected_head == head
    assert binding.observed_head == head
    assert binding.config_sha256 == hashlib.sha256(config.read_bytes()).hexdigest()
    assert binding.archive_nondebug_sha256 == _FIXTURE_ARCHIVE_NONDEBUG_SHA256
    assert binding.expected_toolchain_manifest_sha256 == (
        _fixture_toolchain_manifest_sha256()
    )
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="共有 policy pin と不一致"):
        s8b_floor_campaign._verify_floor_oracle_dependency_source(
            cache_root, repo_root=repo_root, expected_head="0" * 40,
            expected_toolchain_manifest_sha256=(
                _fixture_toolchain_manifest_sha256()
            ),
        )


def test_floor_dependency_binding_records_run_local_archive_sha256(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    cache_root = tmp_path / "cache"
    source = cache_root / "masstree-src"
    head = _git_fixture_source(source)
    (source / "config.h").write_text("#pragma once\n", encoding="utf-8")
    archive = source / "libkohler_masstree_json.a"
    archive_raw = _write_masstree_archive(
        archive, text=b"run-local prebuild archive",
    )

    binding = s8b_floor_campaign._verify_floor_oracle_dependency_source(
        cache_root, repo_root=repo_root, expected_head=head,
        expected_toolchain_manifest_sha256=(
            _fixture_toolchain_manifest_sha256()
        ),
    )

    assert binding.archive_sha256 == hashlib.sha256(
        archive_raw
    ).hexdigest()
    assert binding.archive_nondebug_sha256 != binding.archive_sha256


def test_floor_oracle_dependency_accepts_archive_bytes_changed_by_build_path(
        tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    cache_root = tmp_path / "cache"
    source = cache_root / "masstree-src"
    head = _git_fixture_source(source)
    monkeypatch.setattr(
        s8b_floor_campaign, "_floor_third_party_policy_pins",
        lambda _root: {"masstree": head},
    )
    assert s8b_floor_campaign._verify_pristine_floor_dependency_sources(
        cache_root, repo_root=repo_root, source_names=("masstree",),
    ) == {"masstree": source.resolve()}
    (source / "config.h").write_text("#pragma once\n", encoding="utf-8")
    archive = source / "libkohler_masstree_json.a"
    _write_masstree_archive(
        archive, debug=b"archive from prebuild path",
    )
    before = s8b_floor_campaign._verify_floor_oracle_dependency_source(
        cache_root, repo_root=repo_root, expected_head=head,
        expected_toolchain_manifest_sha256=(
            _fixture_toolchain_manifest_sha256()
        ),
    )
    before = dataclasses.replace(
        before,
        expected_config_sha256=before.config_sha256,
        expected_archive_nondebug_sha256=(
            before.archive_nondebug_sha256
        ),
        payload_policy_pin=head,
    )
    before = _bind_fixture_payload_policy(repo_root, before)

    _write_masstree_archive(
        archive, debug=b"different archive from cell build path",
    )
    result = _fixture_floor_build_result(
        cached=False,
        fetchcontent_base_dir=str(cache_root.resolve()),
        masstree_source_root_sha256=hashlib.sha256(
            str(source.resolve()).encode("utf-8")
        ).hexdigest(),
    )
    after = s8b_floor_campaign._verify_floor_build_dependency(
        result,
        ["cmake", f"-DFETCHCONTENT_BASE_DIR={cache_root.resolve()}"],
        fetchcontent_base=cache_root.resolve(), before=before,
        expected_toolchain_manifest=_FIXTURE_TOOLCHAIN_MANIFEST,
        repo_root=repo_root,
    )
    assert after.config_sha256 == before.config_sha256
    assert after.observed_head == before.observed_head


def test_floor_oracle_dependency_rejects_postbuild_tracked_source_drift(
        tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    cache_root = tmp_path / "cache"
    source = cache_root / "masstree-src"
    head = _git_fixture_source(source)
    monkeypatch.setattr(
        s8b_floor_campaign, "_floor_third_party_policy_pins",
        lambda _root: {"masstree": head},
    )
    (source / "config.h").write_text("#pragma once\n", encoding="utf-8")
    _write_masstree_archive(source / "libkohler_masstree_json.a")
    (source / "tracked.hh").write_text("// build mutation\n", encoding="utf-8")
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._verify_floor_oracle_dependency_source(
            cache_root, repo_root=repo_root, expected_head=head,
            expected_toolchain_manifest_sha256=(
                _fixture_toolchain_manifest_sha256()
            ),
            require_tracked_clean=True,
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-postflight-tracked-source-drift"
    )


@pytest.mark.parametrize(
    ("mutation", "detail_code"),
    [
        (
            "tracked",
            "floor-dependency-postflight-tracked-source-drift",
        ),
        ("archive", "floor-dependency-postflight-archive-drift"),
        (
            "source-inode",
            "floor-dependency-postflight-source-identity-drift",
        ),
    ],
)
def test_build_cells_production_postflight_rejects_dependency_drift(
        tmp_path, monkeypatch, mutation, detail_code):
    freeze = _freeze_document()
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK,
        ) if cell["configuration_id"] == "sort_best"
    )]
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    base = tmp_path / "fetchcontent"
    source = base / "masstree-src"
    head = _git_fixture_source(source)
    (source / "config.h").write_text("#pragma once\n", encoding="utf-8")
    _write_masstree_archive(source / "libkohler_masstree_json.a")
    manifest = _fixture_toolchain_binding(
        verified, cc="site-cc", cxx="site-cxx",
    )
    before = s8b_floor_campaign._verify_floor_oracle_dependency_source(
        base, repo_root=repo_root, expected_head=head,
        expected_toolchain_manifest_sha256=(
            s8b_floor_campaign._floor_toolchain_manifest_sha256(manifest)
        ),
    )
    before = dataclasses.replace(
        before,
        oracle_root=base / "canonical-masstree",
        canonical_lease_root=base / ".sort-swo-dependency-fixture",
        dependency_manifest_sha256=(
            "8d0151cfaa0b86d1a2753e69f514633ec2fe6ee1077caed819fd3a426b501875"
        ),
        captured_policy_pins=(
            ("googletest", "c" * 40),
            ("masstree", head),
            ("mimalloc", "b" * 40),
        ),
        expected_config_sha256=before.config_sha256,
        expected_archive_nondebug_sha256=before.archive_nondebug_sha256,
        payload_policy_pin=head,
    )
    before = _bind_fixture_payload_policy(repo_root, before)
    fixture_policy_path = (
        repo_root / "tools/pegasus/policies/floor_masstree_payload_v1.json"
    )
    monkeypatch.setattr(
        s8b_floor_campaign,
        "_floor_masstree_payload_policy_path",
        lambda _root: fixture_policy_path,
    )

    @contextlib.contextmanager
    def production_prepare(
            cell, ccbench_pin, *, cxx, oracle_dependency_root,
            oracle_compiler, oracle_phase_marker):
        del oracle_compiler
        assert oracle_dependency_root == before.oracle_root
        oracle_phase_marker()
        with _fake_prepare(cell, ccbench_pin, cxx=cxx) as prepared:
            oracle_attempt = copy.deepcopy(prepared.oracle_attempt)
            oracle_attempt["oracle_receipt"][
                "dependency_config_sha256"
            ] = before.config_sha256
            yield dataclasses.replace(
                prepared, oracle_attempt=oracle_attempt,
            )

    fake_build = _make_fake_build(tmp_path / "bin")

    def drifting_build(*args, **kwargs):
        assert kwargs["fetchcontent_dependency_receipt"] == before.cache_receipt()
        assert kwargs["fetchcontent_archive_sha256"] == before.archive_sha256
        kwargs = dict(kwargs)
        kwargs["fetchcontent_dependency_receipt"] = _FIXTURE_DEPENDENCY_RECEIPT
        kwargs["fetchcontent_archive_sha256"] = _FIXTURE_ARCHIVE_SHA256
        result = fake_build(*args, **kwargs)
        if mutation == "tracked":
            (source / "tracked.hh").write_text(
                "// production caller drift\n", encoding="utf-8",
            )
        elif mutation == "archive":
            _write_masstree_archive(
                source / "libkohler_masstree_json.a",
                text=b"production caller archive replacement",
            )
        else:
            detached = base / "masstree-src-before"
            source.rename(detached)
            shutil.copytree(detached, source)
        return result

    monkeypatch.setattr(s8b_floor_campaign, "prepare_cell", production_prepare)
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "compilers_for_current_site",
        lambda: ("site-cc", "site-cxx"),
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_bind_current_toolchain",
        lambda *_args, **_kwargs: manifest,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_prepare_floor_oracle_dependency",
        lambda *_args, **_kwargs: before,
    )
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "build_v2", drifting_build,
    )
    with pytest.raises(sort_swo_oracle.SortSwoOracleUnavailable) as caught:
        s8b_floor_campaign.build_cells(
            freeze, cells, ccbench_pin="0" * 40,
            out_root=tmp_path / "out", prepare_fn=production_prepare,
            contract=contract, verified_calibration=verified,
            build_fn=drifting_build,
            fetchcontent_base_dir=base.resolve(),
            phase_marker_root=marker_root,
        )
    assert caught.value.result.infrastructure.detail_code == detail_code
    payload = json.loads((
        marker_root / s8b_floor_campaign._FLOOR_POSTFLIGHT_FAILURE_FILENAME
    ).read_text(encoding="utf-8"))
    assert payload["infrastructure"]["detail_code"] == detail_code


def test_floor_oracle_dependency_rejects_nonregular_config(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    cache_root = tmp_path / "cache"
    source = cache_root / "masstree-src"
    head = _git_fixture_source(source)
    target = tmp_path / "generated-config.h"
    target.write_text("#pragma once\n", encoding="utf-8")
    (source / "config.h").symlink_to(target)
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="non-symlink regular file"):
        s8b_floor_campaign._verify_floor_oracle_dependency_source(
            cache_root, repo_root=repo_root, expected_head=head,
            expected_toolchain_manifest_sha256=(
                _fixture_toolchain_manifest_sha256()
            ),
        )


def test_floor_oracle_dependency_rejects_missing_config_before_hash(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    cache_root = tmp_path / "cache"
    source = cache_root / "masstree-src"
    head = _git_fixture_source(source)
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="config.h が存在しない"):
        s8b_floor_campaign._verify_floor_oracle_dependency_source(
            cache_root, repo_root=repo_root, expected_head=head,
            expected_toolchain_manifest_sha256=(
                _fixture_toolchain_manifest_sha256()
            ),
        )


def test_floor_oracle_dependency_rejects_missing_archive_before_oracle(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    cache_root = tmp_path / "cache"
    source = cache_root / "masstree-src"
    head = _git_fixture_source(source)
    (source / "config.h").write_text("#pragma once\n", encoding="utf-8")
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="libkohler_masstree_json.a が存在しない"):
        s8b_floor_campaign._verify_floor_oracle_dependency_source(
            cache_root, repo_root=repo_root, expected_head=head,
            expected_toolchain_manifest_sha256=(
                _fixture_toolchain_manifest_sha256()
            ),
        )


def test_floor_oracle_dependency_rejects_nonregular_archive_before_oracle(
        tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    cache_root = tmp_path / "cache"
    source = cache_root / "masstree-src"
    head = _git_fixture_source(source)
    (source / "config.h").write_text("#pragma once\n", encoding="utf-8")
    target = tmp_path / "archive-target"
    target.write_bytes(b"archive")
    (source / "libkohler_masstree_json.a").symlink_to(target)
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._verify_floor_oracle_dependency_source(
            cache_root, repo_root=repo_root, expected_head=head,
            expected_toolchain_manifest_sha256=(
                _fixture_toolchain_manifest_sha256()
            ),
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-archive-not-regular"
    )


def test_floor_pristine_staged_preflight_verifies_three_pins_and_clean_status(
        tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    cache_root = tmp_path / "cache"
    cache_root.mkdir()
    heads = {}
    for name in ("masstree", "mimalloc", "googletest"):
        heads[name] = _git_fixture_source(cache_root / f"{name}-src")
    monkeypatch.setattr(
        s8b_floor_campaign, "_floor_third_party_policy_pins",
        lambda _root: heads,
    )
    verified = s8b_floor_campaign._verify_pristine_floor_dependency_sources(
        cache_root, repo_root=repo_root,
    )
    assert set(verified) == {"masstree", "mimalloc", "googletest"}
    assert all(path == cache_root / f"{name}-src" for name, path in verified.items())

    (cache_root / "mimalloc-src" / "dirty.txt").write_text(
        "dirty\n", encoding="utf-8",
    )
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError,
            match="clean でない") as caught:
        s8b_floor_campaign._verify_pristine_floor_dependency_sources(
            cache_root, repo_root=repo_root,
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-staged-source-dirty"
    )

    dirty_source = cache_root / "mimalloc-src"
    (dirty_source / ".git/info/exclude").write_text(
        "ignored.generated\n", encoding="utf-8",
    )
    (dirty_source / "dirty.txt").unlink()
    (dirty_source / "ignored.generated").write_text(
        "ignored but build-visible\n", encoding="utf-8",
    )
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError) as ignored:
        s8b_floor_campaign._verify_pristine_floor_dependency_sources(
            cache_root, repo_root=repo_root,
        )
    assert ignored.value.diagnostic.detail_code == (
        "floor-dependency-staged-source-dirty"
    )


@pytest.mark.parametrize(
    ("failure_kind", "detail_code", "origin", "outcome"),
    [
        (
            "checkout",
            "floor-dependency-ccbench-checkout-failed",
            "floor-fetchcontent-prebuild:ccbench-checkout",
            "execution-failed",
        ),
        (
            "base",
            "floor-dependency-fetchcontent-base-failed",
            "floor-fetchcontent-prebuild:base",
            "execution-failed",
        ),
        (
            "configure",
            "floor-dependency-fetchcontent-configure-failed",
            "floor-fetchcontent-prebuild:configure",
            "execution-failed",
        ),
        (
            "target",
            "floor-dependency-fetchcontent-target-failed",
            "floor-fetchcontent-prebuild:target",
            "execution-failed",
        ),
        (
            "source-missing",
            "floor-dependency-source-missing",
            "floor-dependency:masstree",
            "missing",
        ),
    ],
    ids=["checkout", "base", "configure", "target", "source-missing"],
)
def test_production_floor_dependency_preflight_failure_persists_private_attempt(
        tmp_path, monkeypatch, failure_kind, detail_code, origin, outcome):
    freeze = _freeze_document()
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK,
        )
        if cell["configuration_id"] == "sort_best"
    )]
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    reservation_binding = _fixture_floor_reservation_binding()
    _payload_root, pins = _fixture_floor_git_submission_payload(
        repo_root, env_tag=contract.env_tag, binding=reservation_binding,
    )
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    legacy_tmpdir = tmp_path / "legacy-tmp"
    legacy_tmpdir.mkdir()
    monkeypatch.setenv("TMPDIR", str(legacy_tmpdir.resolve()))
    fetchcontent_base = legacy_tmpdir / "izanagi-floor-fetchcontent"
    prebuild_source = tmp_path / "prebuild-ccbench"
    prebuild_source.mkdir()
    if failure_kind == "checkout":
        expected_private_path = repo_root / "external" / "ccbench"
    elif failure_kind == "source-missing":
        expected_private_path = fetchcontent_base / "masstree-src"
    else:
        expected_private_path = fetchcontent_base

    downstream_calls = []
    gate_events = []
    assert buildcache is s8b_floor_campaign.buildcache
    prebuild_failure_type = {
        "configure": buildcache.MasstreeFetchContentError,
        "target": buildcache.MasstreeFetchContentError,
        "base": buildcache.BuildCacheError,
    }.get(failure_kind)

    @contextlib.contextmanager
    def production_prepare(
            cell, ccbench_pin, *, cxx, oracle_dependency_root,
            oracle_compiler, oracle_phase_marker):
        del cell, ccbench_pin, cxx, oracle_dependency_root
        del oracle_compiler, oracle_phase_marker
        downstream_calls.append("oracle")
        pytest.fail("dependency preflight 拒否後に oracle へ到達してはいけない")
        yield

    def build(*_args, **_kwargs):
        downstream_calls.append("build")
        pytest.fail("dependency preflight 拒否後に build へ到達してはいけない")

    monkeypatch.setattr(s8b_floor_campaign, "prepare_cell", production_prepare)

    @contextlib.contextmanager
    def checkout(_pin, *, base_dir):
        gate_events.append(("checkout", base_dir))
        yield str(prebuild_source.resolve())

    def fail_checkout(*_args, **_kwargs):
        gate_events.append(("checkout", "failed"))
        raise RuntimeError("fixture checkout failure")

    def prebuild(**_kwargs):
        nonlocal expected_private_path
        if failure_kind != "checkout":
            expected_private_path = Path(_kwargs["fetchcontent_base_dir"])
            if failure_kind == "source-missing":
                expected_private_path /= "masstree-src"
        gate_events.append(("prebuild", failure_kind))
        if failure_kind in {"configure", "target"}:
            failure = buildcache.MasstreeFetchContentError(
                failure_kind, f"fixture {failure_kind} failure",
            )
        elif failure_kind == "base":
            failure = buildcache.BuildCacheError("fixture base failure")
        else:
            shutil.rmtree(Path(_kwargs["masstree_source_dir"]))
            return SimpleNamespace()
        gate_events.append(("prebuild-error", type(failure)))
        raise failure

    monkeypatch.setattr(
        s8b_floor_campaign.patchharness, "checkout",
        fail_checkout if failure_kind == "checkout" else checkout,
    )
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "prepare_masstree_fetchcontent", prebuild,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_floor_third_party_policy_pins",
        lambda _root: pins,
    )
    with pytest.raises(sort_swo_oracle.SortSwoOracleUnavailable) as caught:
        s8b_floor_campaign.build_cells(
            freeze,
            cells,
            ccbench_pin="0" * 40,
            out_root=tmp_path / "out",
            prepare_fn=production_prepare,
            contract=contract,
            verified_calibration=verified,
            build_fn=build,
            fetchcontent_base_dir=None,
            phase_marker_root=marker_root,
            repo_root=repo_root,
            reservation_binding=reservation_binding,
        )

    result = caught.value.result
    assert result is not None
    assert result.status is sort_swo_oracle.OracleStatus.UNAVAILABLE
    assert result.infrastructure is not None
    assert result.infrastructure.phase == "floor-dependency-preflight"
    assert result.infrastructure.detail_code == detail_code
    artifact_path = (
        marker_root / s8b_floor_campaign._FLOOR_PREFLIGHT_FAILURE_FILENAME
    )
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    expected_artifact = sort_swo_oracle.private_attempt_record(result)
    if outcome == "execution-failed":
        expected_artifact["floor_failure_diagnostic"] = {
            "detail_code": detail_code,
            "origin": origin,
            "outcome": outcome,
            "path": str(expected_private_path),
        }
        assert result.infrastructure.environment_resolution is None
    else:
        candidate = artifact["infrastructure"][
            "environment_resolution"
        ]["dependency_candidates"][0]
        assert candidate == {
            "origin": origin,
            "outcome": outcome,
            "path": str(expected_private_path),
        }
    assert artifact == expected_artifact
    assert artifact_path.stat().st_mode & 0o777 == 0o600
    assert artifact_path.stat().st_size <= (
        s8b_floor_campaign._PRIVATE_DIAGNOSTIC_MAX_BYTES
    )
    assert len(list(marker_root.glob("phase-preflight-*.json"))) == 1
    assert not (marker_root / "sort-swo-oracle-dependency.json").exists()
    assert downstream_calls == []
    assert gate_events[0][0] == "checkout"
    if failure_kind != "checkout":
        assert gate_events[1] == ("prebuild", failure_kind)
    if prebuild_failure_type is not None:
        assert gate_events[2] == ("prebuild-error", prebuild_failure_type)


@pytest.mark.parametrize(
    ("race_stage", "detail_code", "origin"),
    [
        (
            "base-stat",
            "floor-dependency-base-unavailable",
            "floor-fetchcontent-base",
        ),
        (
            "source-stat",
            "floor-dependency-source-stat-unavailable",
            "floor-dependency:masstree",
        ),
    ],
    ids=["base-stat", "source-stat"],
)
def test_floor_dependency_disappearance_race_persists_closed_detail_before_oracle(
        tmp_path, monkeypatch, race_stage, detail_code, origin):
    freeze = _freeze_document()
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK,
        ) if cell["configuration_id"] == "sort_best"
    )]
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    reservation_binding = _fixture_floor_reservation_binding()
    _payload_root, pins = _fixture_floor_git_submission_payload(
        repo_root, env_tag=contract.env_tag, binding=reservation_binding,
    )
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    legacy_tmpdir = tmp_path / "legacy-tmp"
    legacy_tmpdir.mkdir()
    monkeypatch.setenv("TMPDIR", str(legacy_tmpdir.resolve()))
    base = legacy_tmpdir / "izanagi-floor-fetchcontent"
    target = base

    if race_stage == "source-stat":
        source = base / "masstree-src"
        prebuild_source = tmp_path / "prebuild-ccbench"
        prebuild_source.mkdir()

        @contextlib.contextmanager
        def checkout(_pin, *, base_dir):
            del base_dir
            yield str(prebuild_source.resolve())

        monkeypatch.setattr(s8b_floor_campaign.patchharness, "checkout", checkout)
        monkeypatch.setattr(
            s8b_floor_campaign.buildcache,
            "prepare_masstree_fetchcontent",
            lambda **_kwargs: SimpleNamespace(),
        )
        target = source

    monkeypatch.setattr(
        s8b_floor_campaign, "_floor_third_party_policy_pins",
        lambda _root: pins,
    )

    original_dependency_stat = s8b_floor_campaign._stat_floor_dependency_root
    injected_sites = []

    def disappearing_dependency_stat(path):
        if path == target:
            injected_sites.append(path)
            raise FileNotFoundError("fixture disappearance race")
        return original_dependency_stat(path)

    monkeypatch.setattr(
        s8b_floor_campaign,
        "_stat_floor_dependency_root",
        disappearing_dependency_stat,
    )
    downstream_calls = []

    @contextlib.contextmanager
    def production_prepare(*_args, **_kwargs):
        downstream_calls.append("oracle")
        pytest.fail("filesystem race の拒否後に oracle を実行しない")
        yield

    monkeypatch.setattr(s8b_floor_campaign, "prepare_cell", production_prepare)
    with pytest.raises(sort_swo_oracle.SortSwoOracleUnavailable) as caught:
        s8b_floor_campaign.build_cells(
            freeze, cells, ccbench_pin="0" * 40,
            out_root=tmp_path / "out", prepare_fn=production_prepare,
            contract=contract, verified_calibration=verified,
            build_fn=lambda *_args, **_kwargs: downstream_calls.append("build"),
            fetchcontent_base_dir=None, phase_marker_root=marker_root,
            repo_root=repo_root, reservation_binding=reservation_binding,
        )
    assert caught.value.result.infrastructure.detail_code == detail_code
    artifact_path = (
        marker_root / s8b_floor_campaign._FLOOR_PREFLIGHT_FAILURE_FILENAME
    )
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["infrastructure"]["detail_code"] == detail_code
    assert artifact["infrastructure"]["environment_resolution"][
        "dependency_candidates"
    ] == [{"origin": origin, "outcome": "missing", "path": str(target)}]
    assert injected_sites == [target]
    assert downstream_calls == []


def test_floor_dependency_head_mismatch_outranks_source_stat_failure_before_oracle(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK,
        ) if cell["configuration_id"] == "sort_best"
    )]
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    reservation_binding = _fixture_floor_reservation_binding()
    _payload_root, pins = _fixture_floor_git_submission_payload(
        repo_root, env_tag=contract.env_tag, binding=reservation_binding,
    )
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    legacy_tmpdir = tmp_path / "legacy-tmp"
    legacy_tmpdir.mkdir()
    monkeypatch.setenv("TMPDIR", str(legacy_tmpdir.resolve()))
    base = legacy_tmpdir / "izanagi-floor-fetchcontent"
    source = base / "masstree-src"
    prebuild_source = tmp_path / "prebuild-ccbench"
    prebuild_source.mkdir()

    @contextlib.contextmanager
    def checkout(_pin, *, base_dir):
        del base_dir
        yield str(prebuild_source.resolve())

    def replace_head_after_pristine(**_kwargs):
        (source / "post-pristine.hh").write_text(
            "// replacement HEAD\n", encoding="utf-8",
        )
        subprocess.run(
            ["git", "-C", str(source), "add", "post-pristine.hh"],
            check=True,
        )
        subprocess.run(
            [
                "git", "-C", str(source), "-c", "user.name=Fixture",
                "-c", "user.email=fixture@example.invalid", "commit",
                "-qm", "post-pristine replacement",
            ],
            check=True,
        )
        return SimpleNamespace()

    monkeypatch.setattr(s8b_floor_campaign.patchharness, "checkout", checkout)
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache,
        "prepare_masstree_fetchcontent",
        replace_head_after_pristine,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_floor_third_party_policy_pins",
        lambda _root: pins,
    )
    target = source
    original_dependency_stat = s8b_floor_campaign._stat_floor_dependency_root
    stat_calls = []

    def unavailable_stat(path):
        if path == target:
            stat_calls.append(path)
            raise FileNotFoundError("fixture simultaneous stat failure")
        return original_dependency_stat(path)

    monkeypatch.setattr(
        s8b_floor_campaign, "_stat_floor_dependency_root", unavailable_stat,
    )
    downstream_calls = []

    @contextlib.contextmanager
    def production_prepare(*_args, **_kwargs):
        downstream_calls.append("oracle")
        pytest.fail("dependency preflight 拒否後に oracle を実行しない")
        yield

    monkeypatch.setattr(s8b_floor_campaign, "prepare_cell", production_prepare)
    with pytest.raises(sort_swo_oracle.SortSwoOracleUnavailable) as caught:
        s8b_floor_campaign.build_cells(
            freeze, cells, ccbench_pin="0" * 40,
            out_root=tmp_path / "out", prepare_fn=production_prepare,
            contract=contract, verified_calibration=verified,
            build_fn=lambda *_args, **_kwargs: downstream_calls.append("build"),
            fetchcontent_base_dir=None, phase_marker_root=marker_root,
            repo_root=repo_root, reservation_binding=reservation_binding,
        )
    assert caught.value.result.infrastructure.detail_code == (
        "floor-dependency-head-mismatch"
    )
    artifact = json.loads((
        marker_root / s8b_floor_campaign._FLOOR_PREFLIGHT_FAILURE_FILENAME
    ).read_text(encoding="utf-8"))
    assert artifact["infrastructure"]["detail_code"] == (
        "floor-dependency-head-mismatch"
    )
    assert artifact["infrastructure"]["environment_resolution"][
        "dependency_candidates"
    ] == [{
        "origin": "floor-dependency:masstree",
        "outcome": "invalid-path",
        "path": str(source.resolve()),
    }]
    assert stat_calls == []
    assert downstream_calls == []


def test_floor_dependency_base_creation_failure_persists_before_oracle_or_build(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK,
        ) if cell["configuration_id"] == "sort_best"
    )]
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    reservation_binding = _fixture_floor_reservation_binding()
    _fixture_floor_submission_payload(
        repo_root, env_tag=contract.env_tag, binding=reservation_binding,
    )
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    job_tmp = tmp_path / "job-tmp"
    job_tmp.mkdir()
    monkeypatch.setenv("TMPDIR", str(job_tmp.resolve()))
    destination = job_tmp.resolve() / "izanagi-floor-fetchcontent"
    original_mkdir = Path.mkdir

    def fail_destination_mkdir(path, *args, **kwargs):
        if path == destination:
            raise OSError("fixture create failure")
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", fail_destination_mkdir)
    calls = []

    @contextlib.contextmanager
    def production_prepare(*_args, **_kwargs):
        calls.append("oracle")
        pytest.fail("base 作成失敗後に oracle を実行しない")
        yield

    monkeypatch.setattr(s8b_floor_campaign, "prepare_cell", production_prepare)
    with pytest.raises(sort_swo_oracle.SortSwoOracleUnavailable) as caught:
        s8b_floor_campaign.build_cells(
            freeze, cells, ccbench_pin="0" * 40,
            out_root=tmp_path / "out", prepare_fn=production_prepare,
            contract=contract, verified_calibration=verified,
            build_fn=lambda *_args, **_kwargs: calls.append("build"),
            phase_marker_root=marker_root,
            repo_root=repo_root,
            reservation_binding=reservation_binding,
        )
    assert caught.value.result.infrastructure.detail_code == (
        "floor-dependency-base-create-failed"
    )
    assert caught.value.result.status is sort_swo_oracle.OracleStatus.UNAVAILABLE
    assert (marker_root / s8b_floor_campaign._FLOOR_PREFLIGHT_FAILURE_FILENAME).is_file()
    assert calls == []


@pytest.mark.parametrize("cached", [False, True], ids=["fresh", "cache-hit"])
def test_floor_postflight_failure_persists_unavailable_before_binary_admission(
        tmp_path, monkeypatch, cached):
    freeze = _freeze_document()
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK,
        ) if cell["configuration_id"] == "sort_best"
    )]
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    base = tmp_path / "fetchcontent"
    base.mkdir()
    dependency = _fixture_dependency_binding(base.resolve())

    @contextlib.contextmanager
    def production_prepare(
            cell, ccbench_pin, *, cxx, oracle_dependency_root,
            oracle_compiler, oracle_phase_marker):
        del oracle_dependency_root, oracle_compiler
        oracle_phase_marker()
        with _fake_prepare(cell, ccbench_pin, cxx=cxx) as prepared:
            yield prepared

    monkeypatch.setattr(s8b_floor_campaign, "prepare_cell", production_prepare)
    monkeypatch.setattr(
        s8b_floor_campaign, "_prepare_floor_oracle_dependency",
        lambda *_args, **_kwargs: dependency,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_verify_floor_build_dependency",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            s8b_floor_campaign._floor_postflight_error(
                "fixture effective root mismatch",
                detail_code="floor-dependency-postflight-effective-root-mismatch",
                outcome="identity-mismatch",
                path=base / "masstree-src",
            )
        ),
    )
    monkeypatch.setattr(
        s8b_floor_campaign._binary_admission,
        "issue_binary_admission_receipt",
        lambda **_kwargs: pytest.fail("postflight 拒否後に admission を発行しない"),
    )
    fake_build = _make_fake_build(tmp_path / "bin", cached=cached)
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "build_v2", fake_build,
    )
    with pytest.raises(sort_swo_oracle.SortSwoOracleUnavailable) as caught:
        s8b_floor_campaign.build_cells(
            freeze, cells, ccbench_pin="0" * 40,
            out_root=tmp_path / "out", prepare_fn=production_prepare,
            contract=contract, verified_calibration=verified,
            build_fn=fake_build,
            fetchcontent_base_dir=base.resolve(), phase_marker_root=marker_root,
        )
    assert caught.value.result.infrastructure.phase == "floor-dependency-postflight"
    assert caught.value.result.status is sort_swo_oracle.OracleStatus.UNAVAILABLE
    artifact = marker_root / s8b_floor_campaign._FLOOR_POSTFLIGHT_FAILURE_FILENAME
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    expected = sort_swo_oracle.private_attempt_record(caught.value.result)
    expected["floor_failure_diagnostic"] = {
        "detail_code": "floor-dependency-postflight-effective-root-mismatch",
        "origin": "floor-dependency-postflight:masstree",
        "outcome": "identity-mismatch",
        "path": str(base / "masstree-src"),
    }
    assert payload == expected


@pytest.mark.parametrize("failure_kind", ["long-surrogate", "str-failure"])
def test_sort_best_build_failure_persists_bounded_exception_diagnostic(
        tmp_path, monkeypatch, failure_kind):
    freeze = _freeze_document()
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK,
        ) if cell["configuration_id"] == "sort_best"
    )]
    contract = ec.lookup(ENV_TAG)
    verified = env_attestation.load_verified_calibration(contract, ROOT)
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    base = tmp_path / "fetchcontent"
    base.mkdir()
    dependency = _fixture_dependency_binding(base.resolve())

    @contextlib.contextmanager
    def production_prepare(
            cell, ccbench_pin, *, cxx, oracle_dependency_root,
            oracle_compiler, oracle_phase_marker):
        del oracle_dependency_root, oracle_compiler
        oracle_phase_marker()
        with _fake_prepare(cell, ccbench_pin, cxx=cxx) as prepared:
            yield prepared

    class BrokenStrError(Exception):
        def __str__(self):
            raise RuntimeError("secondary str failure")

    long_message = "prefix-" + ("x" * 5000) + "-\ud800-tail"

    def fail_build(*_args, **_kwargs):
        if failure_kind == "long-surrogate":
            raise RuntimeError(long_message)
        raise BrokenStrError()

    monkeypatch.setattr(s8b_floor_campaign, "prepare_cell", production_prepare)
    monkeypatch.setattr(
        s8b_floor_campaign, "_prepare_floor_oracle_dependency",
        lambda *_args, **_kwargs: dependency,
    )
    monkeypatch.setattr(
        s8b_floor_campaign._binary_admission,
        "issue_binary_admission_receipt",
        lambda **_kwargs: pytest.fail("build failure 後に admission を発行しない"),
    )
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache, "build_v2", fail_build,
    )
    with pytest.raises(sort_swo_oracle.SortSwoOracleUnavailable) as caught:
        s8b_floor_campaign.build_cells(
            freeze, cells, ccbench_pin="0" * 40,
            out_root=tmp_path / "out", prepare_fn=production_prepare,
            contract=contract, verified_calibration=verified,
            build_fn=fail_build,
            fetchcontent_base_dir=base.resolve(),
            phase_marker_root=marker_root,
        )
    assert caught.value.result.infrastructure.detail_code == (
        "floor-dependency-postflight-build-failed"
    )
    payload = json.loads((
        marker_root / s8b_floor_campaign._FLOOR_POSTFLIGHT_FAILURE_FILENAME
    ).read_text(encoding="utf-8"))
    diagnostic = payload["floor_failure_diagnostic"]
    build_exception = diagnostic["build_exception"]
    assert build_exception["schema_version"] == "s8b-floor-build-exception/v1"
    tail_bytes = build_exception["message_tail"].encode("utf-8")
    assert len(tail_bytes) <= 4096
    assert build_exception["message_tail_sha256"] == hashlib.sha256(
        tail_bytes
    ).hexdigest()
    if failure_kind == "long-surrogate":
        assert build_exception["exception_type"] == "RuntimeError"
        assert build_exception["message_truncated"] is True
        assert build_exception["message_tail"].endswith("-\\ud800-tail")
    else:
        assert build_exception["exception_type"] == "BrokenStrError"
        assert build_exception["message_tail"] == "<exception message unavailable>"
        assert build_exception["message_truncated"] is False
    assert not ({"traceback", "cause", "environment", "stdout"} & set(
        build_exception
    ))
    assert "message_sha256" not in build_exception


def test_floor_build_exception_diagnostic_has_exact_five_key_schema():
    diagnostic = s8b_floor_campaign._floor_build_exception_diagnostic(
        RuntimeError("fixture build failure")
    ).private_dict()
    assert set(diagnostic) == {
        "schema_version", "exception_type", "message_tail",
        "message_tail_sha256", "message_truncated",
    }


@pytest.mark.parametrize(
    ("failure_kind", "detail_code", "outcome"),
    [
        (
            "tool-missing",
            "floor-toolchain-tool-missing",
            "not-found",
        ),
        (
            "version-invalid",
            "floor-toolchain-version-invalid",
            "invalid-path",
        ),
        (
            "receipt-mismatch",
            "floor-toolchain-receipt-mismatch",
            "invalid-path",
        ),
    ],
)
def test_production_floor_toolchain_preflight_failure_persists_private_attempt(
        tmp_path, monkeypatch, failure_kind, detail_code, outcome):
    freeze = _freeze_document()
    cells = [next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK,
        )
        if cell["configuration_id"] == "sort_best"
    )]
    context = _install_toolchain_bound_required_contract(tmp_path, monkeypatch)
    contract = context["contract"]
    verified = context["verified"]
    marker_root = tmp_path / "job-staging"
    marker_root.mkdir()
    calls = []

    @contextlib.contextmanager
    def production_prepare(
            cell, ccbench_pin, *, cxx, oracle_dependency_root,
            oracle_compiler, oracle_phase_marker):
        del cell, ccbench_pin, cxx, oracle_dependency_root
        del oracle_compiler, oracle_phase_marker
        calls.append("oracle")
        pytest.fail("toolchain preflight 拒否後に oracle へ到達してはいけない")
        yield

    def forbid_dependency(*_args, **_kwargs):
        calls.append("dependency")
        pytest.fail("toolchain preflight 拒否後に dependency へ到達してはいけない")

    def forbid_build(*_args, **_kwargs):
        calls.append("build")
        pytest.fail("toolchain preflight 拒否後に build へ到達してはいけない")

    monkeypatch.setattr(s8b_floor_campaign, "prepare_cell", production_prepare)
    monkeypatch.setattr(
        s8b_floor_campaign.buildcache,
        "compilers_for_current_site",
        lambda: ("site-cc", "site-cxx"),
    )
    if failure_kind == "tool-missing":
        monkeypatch.setattr(
            s8b_floor_campaign.shutil, "which", lambda _tool: None,
        )
    elif failure_kind == "version-invalid":
        monkeypatch.setattr(
            s8b_floor_campaign.shutil,
            "which",
            lambda requested: f"/tool/{requested}",
        )
        monkeypatch.setattr(
            s8b_floor_campaign.os.path, "isfile", lambda _path: True,
        )
        monkeypatch.setattr(
            s8b_floor_campaign.os, "access", lambda _path, _mode: True,
        )
        monkeypatch.setattr(
            s8b_floor_campaign.subprocess,
            "run",
            lambda *_args, **_kwargs: SimpleNamespace(
                returncode=1, stdout="", stderr="version failed\n",
            ),
        )
    else:
        observations = _matching_floor_observations()
        observations["cxx"] = dataclasses.replace(
            observations["cxx"],
            version="live-cxx Vendor 2.0\nCopyright stable",
        )
        monkeypatch.setattr(
            s8b_floor_campaign,
            "_observe_floor_tool",
            lambda _requested, role: observations[role],
        )
    monkeypatch.setattr(
        s8b_floor_campaign, "_prepare_floor_oracle_dependency", forbid_dependency,
    )
    with pytest.raises(sort_swo_oracle.SortSwoOracleUnavailable) as caught:
        s8b_floor_campaign.build_cells(
            freeze,
            cells,
            ccbench_pin="0" * 40,
            out_root=tmp_path / "out",
            prepare_fn=production_prepare,
            contract=contract,
            verified_calibration=verified,
            build_fn=forbid_build,
            fetchcontent_base_dir=tmp_path / "cache",
            phase_marker_root=marker_root,
        )

    result = caught.value.result
    assert result is not None
    assert result.infrastructure is not None
    assert result.infrastructure.phase == "floor-toolchain-preflight"
    assert result.infrastructure.detail_code == detail_code
    artifact = json.loads((
        marker_root / s8b_floor_campaign._FLOOR_PREFLIGHT_FAILURE_FILENAME
    ).read_text(encoding="utf-8"))
    assert artifact == sort_swo_oracle.private_attempt_record(result)
    resolution = artifact["infrastructure"]["environment_resolution"]
    assert resolution["compiler_candidates"][0]["outcome"] == outcome
    assert resolution["dependency_candidates"] == [{
        "origin": "floor-preflight:dependency-not-attempted",
        "outcome": "not-configured",
        "path": None,
    }]
    assert len(list(marker_root.glob("phase-preflight-*.json"))) == 1
    assert calls == []


def test_floor_fetchcontent_base_uses_explicit_seam_or_job_unique_tmpdir(
        tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    explicit = tmp_path / "explicit"
    explicit.mkdir()
    assert s8b_floor_campaign._canonical_floor_fetchcontent_base(
        explicit.resolve(), repo_root=repo_root,
    ) == explicit.resolve()

    tmpdir = tmp_path / "job-tmp"
    tmpdir.mkdir()
    monkeypatch.setenv("TMPDIR", str(tmpdir.resolve()))
    first = s8b_floor_campaign._canonical_floor_fetchcontent_base(
        None, repo_root=repo_root,
    )
    second = s8b_floor_campaign._canonical_floor_fetchcontent_base(
        None, repo_root=repo_root,
    )
    assert first.parent == tmpdir.resolve()
    assert second.parent == tmpdir.resolve()
    assert first != second
    monkeypatch.setenv("IZANAGI_PEGASUS_THIRDPARTY_CACHE", str(tmp_path / "ignored"))
    third = s8b_floor_campaign._canonical_floor_fetchcontent_base(
        None, repo_root=repo_root,
    )
    assert third.parent == tmpdir.resolve()


def test_floor_oracle_uses_existing_shared_pin_without_floor_policy_copy():
    pin = s8b_floor_campaign._masstree_policy_pin(ROOT)
    shared = json.loads(
        (ROOT / "tools/pegasus/policy.json").read_text(encoding="utf-8")
    )
    sources = shared["silo_ladder_rung1"]["third_party_sources"]
    assert pin == next(item["pin"] for item in sources if item["name"] == "masstree")
    floor_policy = json.loads(
        (ROOT / "tools/pegasus/policies/floor_v1.json").read_text(encoding="utf-8")
    )
    assert not any("masstree" in key for key in floor_policy)


def test_floor_third_party_pin_snapshot_uses_masstree_seam_without_reread(
        monkeypatch):
    pins_a = {
        "masstree": "a" * 40,
        "mimalloc": "b" * 40,
        "googletest": "c" * 40,
    }
    pins_b = {name: "d" * 40 for name in pins_a}
    policy_reads = []

    def read_policy(_root):
        policy_reads.append(True)
        pins = pins_a if len(policy_reads) == 1 else pins_b
        return [
            {"name": name, "pin": pin}
            for name, pin in pins.items()
        ]

    original_masstree_pin = s8b_floor_campaign._masstree_policy_pin
    seam_snapshots = []

    def masstree_pin(snapshot):
        seam_snapshots.append(snapshot)
        return original_masstree_pin(snapshot)

    monkeypatch.setattr(
        s8b_floor_campaign._silo_ladder, "third_party_policy", read_policy,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_masstree_policy_pin", masstree_pin,
    )
    assert s8b_floor_campaign._floor_third_party_policy_pins(ROOT) == pins_a
    assert policy_reads == [True]
    assert len(seam_snapshots) == 1
    assert isinstance(
        seam_snapshots[0], s8b_floor_campaign._LoadedFloorThirdPartyPolicy,
    )


def test_floor_masstree_runtime_accepts_expected_and_debug_only_projection(
        tmp_path):
    approved_path = tmp_path / "approved.a"
    debug_variant_path = tmp_path / "debug-variant.a"
    approved_raw = _write_masstree_archive(
        approved_path, debug=b"/clone/a/source.cc",
    )
    debug_variant_raw = _write_masstree_archive(
        debug_variant_path, debug=b"/different/root/source.cc",
    )
    approved = s8b_floor_campaign._verify_masstree_archive(approved_path)
    debug_variant = s8b_floor_campaign._verify_masstree_archive(
        debug_variant_path
    )
    assert approved.raw_sha256 != debug_variant.raw_sha256
    assert (
        approved.archive_nondebug_sha256
        == debug_variant.archive_nondebug_sha256
    )
    pin = "a" * 40
    policy_path = tmp_path / "tools/pegasus/policies"
    policy_path.mkdir(parents=True)
    (policy_path / "floor_masstree_payload_v1.json").write_text(
        json.dumps({
            "schema_version": "s8b-floor-masstree-payload/v3",
            "name": "masstree",
            "pin": pin,
            "config_sha256": "b" * 64,
            "archive_projection": "gnu-ar-elf-nondebug/v1",
            "archive_nondebug_sha256": approved.archive_nondebug_sha256,
        }),
        encoding="utf-8",
    )
    expected = s8b_floor_campaign._load_floor_masstree_payload_policy(
        tmp_path, expected_masstree_pin=pin,
    )
    binding = dataclasses.replace(
        _fixture_dependency_binding(tmp_path / "cache"),
        config_sha256="b" * 64,
        archive_sha256=hashlib.sha256(approved_raw).hexdigest(),
        archive_nondebug_sha256=approved.archive_nondebug_sha256,
    )
    accepted = s8b_floor_campaign._bind_expected_floor_masstree_payload(
        binding, expected,
    )
    assert accepted.expected_archive_nondebug_sha256 == (
        approved.archive_nondebug_sha256
    )
    debug_only = dataclasses.replace(
        binding,
        archive_sha256=hashlib.sha256(debug_variant_raw).hexdigest(),
        archive_nondebug_sha256=debug_variant.archive_nondebug_sha256,
    )
    assert s8b_floor_campaign._bind_expected_floor_masstree_payload(
        debug_only, expected,
    ).archive_nondebug_sha256 == approved.archive_nondebug_sha256


def test_floor_masstree_runtime_rejects_expected_archive_nondebug_mismatch(
        tmp_path):
    archive = tmp_path / "changed.a"
    _write_masstree_archive(archive, text=b"changed nondebug bytes")
    changed = s8b_floor_campaign._verify_masstree_archive(archive)
    binding = dataclasses.replace(
        _fixture_dependency_binding(tmp_path / "cache"),
        config_sha256="b" * 64,
        archive_sha256=changed.raw_sha256,
        archive_nondebug_sha256=changed.archive_nondebug_sha256,
    )
    expected = s8b_floor_campaign._LoadedFloorMasstreePayloadPolicy(
        schema_version="s8b-floor-masstree-payload/v3",
        name="masstree",
        pin=binding.expected_head,
        config_sha256="b" * 64,
        archive_projection="gnu-ar-elf-nondebug/v1",
        archive_nondebug_sha256=_FIXTURE_ARCHIVE_NONDEBUG_SHA256,
        raw_sha256="d" * 64,
    )
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._bind_expected_floor_masstree_payload(
            binding, expected,
        )
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-archive-expected-mismatch"
    )


def test_floor_masstree_payload_policy_loader_is_exact_and_shared_pin_bound():
    policy = s8b_floor_campaign._load_floor_masstree_payload_policy(ROOT)
    assert policy.schema_version == "s8b-floor-masstree-payload/v3"
    assert policy.name == "masstree"
    assert policy.pin == s8b_floor_campaign._masstree_policy_pin(ROOT)
    assert len(policy.config_sha256) == 64
    assert policy.archive_projection == "gnu-ar-elf-nondebug/v1"
    assert len(policy.archive_nondebug_sha256) == 64
    assert policy.raw_sha256 == hashlib.sha256(
        s8b_floor_campaign._floor_masstree_payload_policy_path(ROOT).read_bytes()
    ).hexdigest()


def test_floor_masstree_payload_policy_loader_rejects_unknown_key(
        tmp_path, monkeypatch):
    policy_path = tmp_path / "tools/pegasus/policies"
    policy_path.mkdir(parents=True)
    document = {
        "schema_version": "s8b-floor-masstree-payload/v3",
        "name": "masstree",
        "pin": "a" * 40,
        "config_sha256": "b" * 64,
        "archive_projection": "gnu-ar-elf-nondebug/v1",
        "archive_nondebug_sha256": "c" * 64,
        "archive_sha256": "c" * 64,
    }
    (policy_path / "floor_masstree_payload_v1.json").write_text(
        json.dumps(document), encoding="utf-8",
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_masstree_policy_pin", lambda _root: "a" * 40,
    )
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError,
            match="exact key"):
        s8b_floor_campaign._load_floor_masstree_payload_policy(tmp_path)


def test_floor_masstree_payload_policy_loader_rejects_exact_four_key_v2_body(
        tmp_path, monkeypatch):
    policy_path = tmp_path / "tools/pegasus/policies"
    policy_path.mkdir(parents=True)
    document = {
        "schema_version": "s8b-floor-masstree-payload/v2",
        "name": "masstree",
        "pin": "a" * 40,
        "config_sha256": "b" * 64,
    }
    (policy_path / "floor_masstree_payload_v1.json").write_text(
        json.dumps(document), encoding="utf-8",
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_masstree_policy_pin", lambda _root: "a" * 40,
    )
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._load_floor_masstree_payload_policy(tmp_path)
    assert caught.value.diagnostic.detail_code == (
        "floor-dependency-payload-policy-schema-invalid"
    )


@pytest.mark.parametrize(
    ("document", "detail_code"),
    [
        (
            {
                "schema_version": "s8b-floor-masstree-payload/v3",
                "name": "masstree", "pin": "a" * 40,
                "config_sha256": "b" * 64,
                "archive_projection": "gnu-ar-elf-nondebug/v1",
            },
            "floor-dependency-payload-policy-schema-invalid",
        ),
        (
            {
                "schema_version": "s8b-floor-masstree-payload/v3",
                "name": "masstree", "pin": "a" * 40,
                "config_sha256": "malformed",
                "archive_projection": "gnu-ar-elf-nondebug/v1",
                "archive_nondebug_sha256": "c" * 64,
            },
            "floor-dependency-payload-policy-hash-invalid",
        ),
        (
            {
                "schema_version": "s8b-floor-masstree-payload/v3",
                "name": "masstree", "pin": "b" * 40,
                "config_sha256": "c" * 64,
                "archive_projection": "gnu-ar-elf-nondebug/v1",
                "archive_nondebug_sha256": "d" * 64,
            },
            "floor-dependency-payload-policy-pin-mismatch",
        ),
        (
            {
                "schema_version": "s8b-floor-masstree-payload/v3",
                "name": "masstree", "pin": "a" * 40,
                "config_sha256": "b" * 64,
                "archive_projection": "unknown-projection/v1",
                "archive_nondebug_sha256": "c" * 64,
            },
            "floor-dependency-payload-policy-schema-invalid",
        ),
        (
            {
                "schema_version": "s8b-floor-masstree-payload/v3",
                "name": "masstree", "pin": "a" * 40,
                "config_sha256": "b" * 64,
                "archive_projection": "gnu-ar-elf-nondebug/v1",
                "archive_nondebug_sha256": "malformed",
            },
            "floor-dependency-payload-policy-hash-invalid",
        ),
    ],
)
def test_floor_masstree_payload_policy_loader_rejects_missing_malformed_or_pin(
        tmp_path, monkeypatch, document, detail_code):
    policy_path = tmp_path / "tools/pegasus/policies"
    policy_path.mkdir(parents=True)
    (policy_path / "floor_masstree_payload_v1.json").write_text(
        json.dumps(document), encoding="utf-8",
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_masstree_policy_pin", lambda _root: "a" * 40,
    )
    with pytest.raises(
            s8b_floor_campaign._FloorOraclePreflightError) as caught:
        s8b_floor_campaign._load_floor_masstree_payload_policy(tmp_path)
    assert caught.value.diagnostic.detail_code == detail_code


def test_phase_marker_is_create_only_fsynced_private_and_carries_dependency_hash(
        tmp_path):
    staging = tmp_path / "job-staging"
    staging.mkdir()
    dependency = dataclasses.replace(
        _fixture_dependency_binding(tmp_path / "cache"),
        config_sha256="b" * 64,
    )
    marker = s8b_floor_campaign._write_phase_marker(
        staging,
        cell="rr79:sort_best",
        phase="oracle",
        compiler="/fixture/cxx",
        dependency=dependency,
    )
    payload = json.loads(marker.read_text(encoding="utf-8"))
    assert {"cell", "phase", "pid", "started"}.issubset(payload)
    assert payload["cell"] == "rr79:sort_best"
    assert payload["phase"] == "oracle"
    assert payload["dependency_root"] == str(dependency.source_root)
    assert payload["oracle_dependency_root"] == str(dependency.oracle_root)
    assert payload["dependency_manifest_sha256"] == (
        dependency.dependency_manifest_sha256
    )
    assert payload["dependency_config_sha256"] == "b" * 64
    assert payload["dependency_toolchain_manifest_sha256"] == (
        _fixture_toolchain_manifest_sha256()
    )
    assert marker.stat().st_mode & 0o777 == 0o600
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="create-only"):
        s8b_floor_campaign._write_phase_marker(
            staging,
            cell="rr79:sort_best",
            phase="oracle",
            compiler="/fixture/cxx",
            dependency=dependency,
        )
    source = inspect.getsource(s8b_floor_campaign._create_private_json)
    assert "os.O_EXCL" in source
    assert source.count("os.fsync") >= 2


def test_floor_phase_marker_carries_run_local_archive_sha256(tmp_path):
    staging = tmp_path / "job-staging"
    staging.mkdir()
    dependency = _fixture_dependency_binding(tmp_path / "cache")
    marker = s8b_floor_campaign._write_phase_marker(
        staging, cell="rr79:sort_best", phase="build",
        compiler="/fixture/cxx", dependency=dependency,
    )
    payload = json.loads(marker.read_text(encoding="utf-8"))
    assert payload["dependency_archive_sha256"] == _FIXTURE_ARCHIVE_SHA256
    assert payload["dependency_archive_nondebug_sha256"] == (
        _FIXTURE_ARCHIVE_NONDEBUG_SHA256
    )
    assert payload["dependency_expected_archive_nondebug_sha256"] == (
        _FIXTURE_ARCHIVE_NONDEBUG_SHA256
    )


def _provision_claim_root(ctx) -> Path:
    root = ctx["out_root"] / "claims"
    root.mkdir(parents=True, mode=0o700)
    return root


def _floor_claim_subprocess_worker(
        worker_root_raw: str, shared_out_raw: str, barrier_raw: str, label: str,
) -> int:
    """Run the production floor entry through its real claim edge in a child."""
    worker_root = Path(worker_root_raw)
    shared_out = Path(shared_out_raw)
    barrier = Path(barrier_raw)
    worker_root.mkdir(parents=True, exist_ok=True)
    monkeypatch = pytest.MonkeyPatch()
    ctx = _install_required_contract(worker_root, monkeypatch)
    ctx["out_root"] = shared_out
    original_acquire = campaign_claim.acquire_claim
    original_scan = campaign_claim._scan_protocol_conflicts
    scan_calls = 0

    def wait_for(prefix, message):
        deadline = time.monotonic() + 120.0
        while len(list(barrier.glob(f"{prefix}-*"))) != 2:
            if time.monotonic() >= deadline:
                raise RuntimeError(message)
            time.sleep(0.05)

    def synchronized_scan(*args, **kwargs):
        nonlocal scan_calls
        result = original_scan(*args, **kwargs)
        scan_calls += 1
        if scan_calls == 1:
            assert result is None
            (barrier / f"pre-{label}").write_text("ready", encoding="ascii")
            wait_for("pre", "claim subprocess prescan barrier timed out")
        return result

    def synchronized_acquire(claim_root, record):
        try:
            acquired = original_acquire(claim_root, record)
        except Exception:
            (barrier / f"done-{label}").write_text("done", encoding="ascii")
            raise
        (barrier / f"done-{label}").write_text("done", encoding="ascii")
        wait_for("done", "claim subprocess done barrier timed out")
        assert acquired.record.campaign_identity == record.campaign_identity
        raise SystemExit(0)

    started_at = _FIXED_NOW + dt.timedelta(seconds=int(label))
    try:
        with mock.patch.object(
                campaign_claim, "_scan_protocol_conflicts", synchronized_scan), \
                mock.patch.object(
                    campaign_claim, "acquire_claim", synchronized_acquire):
            s8b_floor_campaign._run_campaign_core(
                ctx["protocol"], _verified_freeze(ctx["freeze"]),
                out_root=shared_out, mode="pilot", measure_fn=_forbid_measure,
                probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
                now_fn=lambda: started_at, repo_root=ctx["repo_root"],
                build_fn=_make_fake_build(worker_root / "bin"),
                durable_root_policy=_durable_policy(shared_out),
                _holdout_repo_root=ROOT,
                _holdout_signature_source=ctx["freeze"]["holdouts"],
            )
    except s8b_floor_campaign.FloorCampaignError:
        return 1
    except Exception:
        return 2
    return 2


def test_two_floor_subprocesses_same_protocol_different_runs_never_both_succeed(
        tmp_path):
    """MUT-E1: two real floor subprocesses contend on one durable claim root."""
    shared_out = tmp_path / "shared-out"
    (shared_out / "claims").mkdir(parents=True)
    barrier = tmp_path / "barrier"
    barrier.mkdir()
    test_dir = Path(__file__).resolve().parent
    script = (
        "import sys; "
        f"sys.path.insert(0, {str(test_dir)!r}); "
        "import test_s8b_floor_campaign as target; "
        "sys.exit(target._floor_claim_subprocess_worker(*sys.argv[1:]))"
    )
    processes = [
        subprocess.Popen(
            [
                sys.executable, "-c", script,
                str(tmp_path / f"worker-{label}"), str(shared_out),
                str(barrier), label,
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for label in ("1", "2")
    ]
    deadline = time.monotonic() + 180.0
    try:
        completed = [
            process.communicate(timeout=max(0.1, deadline - time.monotonic()))
            for process in processes
        ]
    except subprocess.TimeoutExpired:
        for process in processes:
            if process.poll() is None:
                process.kill()
        for process in processes:
            process.communicate()
        raise
    returncodes = [process.returncode for process in processes]

    assert set(returncodes) <= {0, 1}, (returncodes, completed)
    assert sum(code == 0 for code in returncodes) <= 1, (returncodes, completed)
    claims = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((shared_out / "claims").glob("*.claim"))
    ]
    assert 1 <= len(claims) <= 2
    assert len({row["campaign_identity"] for row in claims}) == len(claims)
    assert len({row["protocol_digest"] for row in claims}) == 1


@contextlib.contextmanager
def _official_test_seam(monkeypatch, *, clean_digest="d" * 64):
    """承認済み official fixture の clean scan だけを tmp-only stub にする。"""
    with monkeypatch.context() as scoped:
        scoped.setattr(
            s8b_floor_campaign, "clean_scan_digest",
            lambda root, *, freeze_allowlist: clean_digest,
        )
        yield scoped


def _fixed_host(*, now_fn):
    return {
        "hostname": "sentinel-host", "boot_id": "sentinel-boot",
        "job_id": "sentinel-job", "cpuset": "sentinel-cpuset",
        "utc": now_fn().isoformat(),
    }


def _fixed_process():
    return {"pid": 4242, "starttime": 31337, "execution_uuid": "a" * 32}


def _fixed_receipt(contract, *, now_fn):
    return {
        "schema": s8b_floor_campaign.execution_guard.RECEIPT_SCHEMA,
        "env_tag": contract.env_tag,
        "contract_sha256": contract.contract_sha256,
        "attestation": {
            "hostname": "sentinel-receipt-host", "boot_id": "sentinel-receipt-boot",
            "cpuset": "sentinel-receipt-cpuset",
            "captured_utc": now_fn().isoformat(),
        },
    }


def _init_real_clean_repo(repo_root: Path, freeze: dict, protocol: dict) -> None:
    """production clean_scan_digest 用の最小 real git repo（陽性対照は既存生成核を再利用）。"""
    repo_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(repo_root)], check=True)
    ccbench = repo_root / "external" / "ccbench"
    ccbench.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(ccbench)], check=True)
    (ccbench / "anchor.txt").write_text("fixture anchor\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(ccbench), "add", "anchor.txt"], check=True)
    subprocess.run([
        "git", "-C", str(ccbench), "-c", "user.name=fixture",
        "-c", "user.email=fixture@example.invalid", "commit", "-qm", "anchor",
    ], check=True)

    scanner = s8b_floor_campaign._holdout_freeze
    positive_values = {
        "rratio": scanner._POSITIVE_RATIO,
        "skew": scanner._FIXED_SKEW,
        "rmw": scanner._FIXED_RMW,
    }
    positive = " ".join(
        scanner.concrete_axis_encodings(axis, positive_values[axis])[0]
        for axis in ("rratio", "skew", "rmw")
    )
    (repo_root / "positive-control.txt").write_text(positive + "\n", encoding="utf-8")
    freeze_path = repo_root / protocol["freeze"]["path"]
    freeze_path.parent.mkdir(parents=True)
    freeze_path.write_bytes(json.dumps(
        freeze, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8"))
    bounded_freeze_path = repo_root / s8b_floor_campaign._HOLDOUT_FREEZE_REL
    bounded_freeze_path.parent.mkdir(parents=True, exist_ok=True)
    bounded_freeze_path.write_bytes(freeze_path.read_bytes())
    namespace_marker = repo_root / "output/namespace.json"
    namespace_marker.write_bytes(s8b_oracle_artifacts.OFFICIAL_NAMESPACE_BYTES)
    contract = ec.lookup(protocol["env_tag"])
    calibration_path = repo_root / contract.calibration_ref.path
    calibration_path.parent.mkdir(parents=True, exist_ok=True)
    calibration_path.write_bytes((ROOT / contract.calibration_ref.path).read_bytes())
    subprocess.run(
        ["git", "-C", str(repo_root), "add", "positive-control.txt",
         protocol["freeze"]["path"], s8b_floor_campaign._HOLDOUT_FREEZE_REL,
         contract.calibration_ref.path,
         "output/namespace.json",
         "external/ccbench"],
        check=True,
    )


def _deterministic_official_artifacts(base: Path) -> dict:
    """異なる process/root から同じ production-emitter bytes を作る characterization helper。"""
    base.mkdir(parents=True, exist_ok=True)
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    repo_root = base / "repo"
    out_root = base / "out"
    _init_real_clean_repo(repo_root, freeze, protocol)
    fake_build = _make_fake_build(base / "ignored-build-root")

    @contextlib.contextmanager
    def rooted_prepare(cell, ccbench_pin, *, cxx):
        entry = cell["variant"]
        holdout_id = entry["holdout_id"]
        configuration_id = cell["configuration"]
        cell_id = f"{holdout_id}::{configuration_id}"
        genome = Genome("silo", dict(entry.get("flags", {})))
        ccbench = base / "prepared trees Ω" / cell_id.replace("::", "__")
        compiler_input = ccbench / "include" / "fixture.hh"
        compiler_input.parent.mkdir(parents=True)
        compiler_input.write_bytes(f"compiler-input:{cell_id}\n".encode("utf-8"))
        ccbench_dir = str(ccbench)
        token = _fixture_src_token(genome, ccbench_dir)
        _FIXTURE_CELL_BY_TOKEN[token] = cell_id
        _FIXTURE_BUILD_DECLARATION_BY_TOKEN[token] = (
            ccbench_pin, configuration_id, copy.deepcopy(entry),
        )
        yield PreparedCell(
            genome=genome, src_token=token,
            ccbench_dir=ccbench_dir,
            cache_root=str(base / "prepared-cache"),
            oracle_attempt=(
                fake_sort_swo_pass_attempt()
                if configuration_id == "sort_best" else None
            ),
        )

    gate_state = {"digest": None}

    def fixture_expected_materialization(**kwargs):
        digest = _fixture_expected_materialization_sha256(
            kwargs["declaration"]
        )
        gate_state["digest"] = digest
        return digest

    def fixture_exact_materialization(_root, expected):
        assert expected == gate_state["digest"]
        return expected

    def fixture_protect_snapshot(root):
        return (
            s8b_floor_campaign._expected_materialization.
            SnapshotPermissionState(
                root=str(root), modes=(), tree_digest=gate_state["digest"],
            )
        )

    with mock.patch.object(s8b_floor_campaign.buildcache, "build_v2", fake_build), \
            mock.patch.object(
                s8b_floor_campaign, "_bind_current_toolchain",
                _fixture_toolchain_binding,
            ), \
            mock.patch.object(
                s8b_floor_campaign.source_digest, "resolve_evidence",
                _fixture_source_evidence,
            ), \
            mock.patch.object(
                s8b_floor_campaign._expected_materialization,
                "produce_expected_materialization_from_declaration",
                fixture_expected_materialization,
            ), \
            mock.patch.object(
                s8b_floor_campaign._expected_materialization,
                "assert_expected_materialization",
                fixture_exact_materialization,
            ), \
            mock.patch.object(
                s8b_floor_campaign._expected_materialization,
                "make_snapshot_non_writable",
                fixture_protect_snapshot,
            ), \
            mock.patch.object(
                s8b_floor_campaign._expected_materialization,
                "restore_snapshot_permissions",
                lambda _state: None,
            ), \
            mock.patch.object(
                s8b_floor_campaign._perf_preflight, "probe_perf_availability",
                lambda **_kwargs: _perf_receipt(available=False),
            ):
        outcome = _private_run_campaign(
            protocol, verified, out_root=out_root, mode="official",
            measure_fn=_make_measure_fn(
                reps=5, value_fn=lambda cid: _BASE_TPS[cid], use_perf=False,
            ),
            probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
            monotonic_fn=lambda: 0.0, prepare_fn=rooted_prepare,
            now_fn=lambda: _FIXED_NOW, host_provenance_fn=_fixed_host,
            process_identity_fn=_fixed_process, execution_receipt_fn=_fixed_receipt,
            repo_root=repo_root, durable_root_policy=_durable_policy(out_root),
            _floor_preflight_fn=_fixture_floor_preflight,
        )
    run_dir = Path(outcome["run_dir"])
    names = (
        "launch_certificate.json", "manifest.json", "journal.jsonl", "result.json",
    )
    paths = [run_dir / name for name in names]
    scan_paths = paths + [run_dir / "result.md"]
    root_needles = [str(base).encode("utf-8"), str(repo_root).encode("utf-8"),
                    str(out_root).encode("utf-8")]
    assert all(path.is_file() and path.stat().st_size > 0 for path in scan_paths)
    assert all(needle not in path.read_bytes()
               for path in scan_paths for needle in root_needles)
    assert json.loads(paths[0].read_bytes())["schema"] == s8b_floor_campaign.LAUNCH_CERT_SCHEMA
    assert json.loads(paths[1].read_bytes())["schema_version"] == s8b_floor_campaign.MANIFEST_SCHEMA
    assert _read_journal_lines(paths[2])[-1] == {"event": "terminal", "status": "completed"}
    assert json.loads(paths[3].read_bytes())["schema"] == s8b_floor_campaign.RESULT_SCHEMA
    return {
        "run_dir": str(run_dir),
        "sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                   for name, path in zip(names, paths)},
        "inodes": {name: [path.stat().st_dev, path.stat().st_ino]
                   for name, path in zip(names, paths)},
    }


# =========================================================================== #
# 1. schedule 決定性 + freeze 由来セルのみ + golden (独立 reference) + 意図 mutant #
# =========================================================================== #

def test_schedule_is_deterministic_by_seed_and_uses_only_freeze_cells():
    freeze = _freeze_document()
    cells = s8b_floor_campaign.enumerate_cells(freeze, stock_configuration=_STOCK)
    assert len(cells) == 12
    cell_ids = {c["cell_id"] for c in cells}
    assert cell_ids == {f"{h}::{c}" for h in ("rr79", "rr23") for c in _CONFIGS}
    for forbidden in ("rr80", "rr20", "rr5", "rr50", "rr95"):
        assert not any(forbidden in cid for cid in cell_ids), forbidden

    a1 = s8b_floor_campaign.build_schedule(cells=cells, master_seed="seed-alpha", n_sessions=8)
    a2 = s8b_floor_campaign.build_schedule(cells=cells, master_seed="seed-alpha", n_sessions=8)
    b = s8b_floor_campaign.build_schedule(cells=cells, master_seed="seed-beta", n_sessions=8)
    assert a1 == a2                       # 同一 seed → 同一 schedule
    assert a1 != b                        # 別 seed → 別置換

    assert len(a1) == 8 * 12              # 8 round × 12 cell
    assert [r["seq"] for r in a1] == list(range(96))  # seq は 0..95 の通し番号
    assert sorted({r["round"] for r in a1}) == list(range(1, 9))  # round は 1..8 (0-origin でない)
    for row in a1:
        assert set(row) == {"seq", "round", "cell_id"}  # block/replicate は無い
    # 各 round は 12 セルの完全置換 (global shuffle ではない)。
    for r in range(1, 9):
        rows = [row["cell_id"] for row in a1 if row["round"] == r]
        assert len(rows) == 12
        assert set(rows) == cell_ids


def test_build_schedule_is_input_order_independent():
    freeze = _freeze_document()
    cells = s8b_floor_campaign.enumerate_cells(freeze, stock_configuration=_STOCK)
    reversed_cells = list(reversed(cells))
    a = s8b_floor_campaign.build_schedule(cells=cells, master_seed="x", n_sessions=3)
    b = s8b_floor_campaign.build_schedule(cells=reversed_cells, master_seed="x", n_sessions=3)
    assert a == b  # cell_id を sort するので入力順に依存しない


def test_build_schedule_rejects_duplicate_cell_ids():
    dup = [{"cell_id": "c"}, {"cell_id": "c"}]
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="重複"):
        s8b_floor_campaign.build_schedule(cells=dup, master_seed="x", n_sessions=1)


def test_floor_reservation_budget_matches_frozen_formula_exactly():
    cells = [{"cell_id": "a"}, {"cell_id": "b"}]
    schedule = [
        {"cell_id": cell_id}
        for _round in range(3)
        for cell_id in ("a", "b")
    ]
    protocol = {"extime_s": 7, "reps": 4, "retry_slots_per_cell": 2}
    # 2 * (900 + (3 + 2) * (7 * 4 + 120)) = 3280; finalize margin = 600。
    assert s8b_floor_campaign._floor_reservation_budget(
        protocol=protocol, cells=cells, schedule=schedule,
    ) == (3280, 600)


def test_floor_reservation_includes_one_shared_dependency_prebuild_only_for_sort():
    schedule = [{"cell_id": "a"}]
    protocol = {"extime_s": 7, "reps": 4, "retry_slots_per_cell": 0}
    nonsort = [{"cell_id": "a", "configuration_id": "stock"}]
    sort = [{"cell_id": "a", "configuration_id": "sort_best"}]
    without, margin = s8b_floor_campaign._floor_reservation_budget(
        protocol=protocol, cells=nonsort, schedule=schedule,
    )
    with_sort, sort_margin = s8b_floor_campaign._floor_reservation_budget(
        protocol=protocol, cells=sort, schedule=schedule,
    )
    assert with_sort - without == (
        s8b_floor_campaign._FLOOR_DEPENDENCY_CONFIGURE_CAP_S
        + s8b_floor_campaign._FLOOR_DEPENDENCY_TARGET_CAP_S
    )
    assert margin == sort_margin == 600


@pytest.mark.parametrize(
    "schedule,match",
    [
        ([{"cell_id": "a"}, {"cell_id": "missing"}], "未知 cell"),
        ([{"cell_id": "a"}, {"cell_id": "a"}, {"cell_id": "b"}], "不均一"),
    ],
)
def test_floor_reservation_budget_rejects_unknown_or_nonuniform_schedule(
        schedule, match):
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match=match):
        s8b_floor_campaign._floor_reservation_budget(
            protocol={"extime_s": 7, "reps": 4, "retry_slots_per_cell": 2},
            cells=[{"cell_id": "a"}, {"cell_id": "b"}], schedule=schedule,
        )


# --- golden: 独立 reference (production を import しない) で導出した literal ---

# 独立に計算した sha256 hex (別経路: python3 -c 'hashlib.sha256(...)')。
# これらから seed = int.from_bytes(bytes.fromhex(hex)[:8], "big") を spec として再導出する。
# production が区切り "/"・slice [:8]・big-endian・round 起点 1 のいずれかを変えれば不一致。
_GOLDEN_SEED = "golden-pin-v2"
_GOLDEN_SORTED = [
    "rr79::backoff_fixed_best", "rr79::ident_all", "rr79::p2_2_flag_opt",
    "rr79::sort_best", "rr79::stock_common", "rr79::system_gate",
]
_GOLDEN_ROUND_SHA256 = {
    1: "afb43e056e1b3a69ce629f9a231dabe935fcbd5c21285e5eaaaa31c10adb1f67",
    2: "08d1ced78e622f342a644e022acd5ceb8846d9a1ea24779b83b417ca5e253a54",
}

# 固定 seal の master_seed/range(1, 9) を別経路で sha256 した golden。
_REAL_SEAL_MASTER_SEED = "2026-07-18T17:16:12+09:00"
_REAL_SEAL_ROUND_SHA256 = {
    1: "448385cc866b3058921124dc146edd3adb0556fe0da2ebb1503982f07c1d0a0d",
    2: "857cf054e7bf2dbcd6591f78bb08ce44f9bb5dca38fb3465e502e86f3872f812",
    3: "dc64336e50fd9512a14c4db6532165b7d5137d8737678cccf43b6cfd7e5bfdd3",
    4: "ed705f04ca37b12bd32e715b2e535866e98a44c153f50e0906f207b074d2071e",
    5: "d351cc8aca948110e360904a8fdd0ccb7e882832e3595697d17e9eb99a5bbcde",
    6: "e7c917db935ee6691cfd5d3bb733862371f718553a7aca32a464946310730297",
    7: "1a4d6497557bf9f17eb291fc496b491cfa2b80bd503826ef47e69ba571437b7f",
    8: "d8f355434a5608a2bbaaa3fb1b4541673760903574093c731eed4d8d95a3d0a9",
}


def _ref_round_perm(round_no: int) -> list:
    """spec を独立実装: hex → 先頭 8 byte big-endian → Random.shuffle。"""
    digest_hex = _GOLDEN_ROUND_SHA256[round_no]
    seed = int.from_bytes(bytes.fromhex(digest_hex)[:8], "big")
    perm = list(_GOLDEN_SORTED)
    random.Random(seed).shuffle(perm)
    return perm


def _real_seal_schedule_golden(cell_ids) -> list[dict]:
    """固定 seal の hard-coded round SHA から schedule spec を独立導出する。"""
    sorted_cell_ids = sorted(cell_ids)
    rows = []
    for round_no, digest_hex in _REAL_SEAL_ROUND_SHA256.items():
        assert hashlib.sha256(
            f"{_REAL_SEAL_MASTER_SEED}/{round_no}".encode("utf-8")
        ).hexdigest() == digest_hex
        seed = int.from_bytes(bytes.fromhex(digest_hex)[:8], "big")
        permuted = list(sorted_cell_ids)
        random.Random(seed).shuffle(permuted)
        for cell_id in permuted:
            rows.append({
                "seq": len(rows), "round": round_no, "cell_id": cell_id,
            })
    return rows


def test_round_seed_matches_independent_sha256_slice_endian():
    """_round_seed が区切り "/"・先頭 8 byte・big-endian を守ることを独立 hex から固定する。"""
    for round_no, digest_hex in _GOLDEN_ROUND_SHA256.items():
        # 独立確認: hex 自体が spec の payload の sha256 である。
        assert hashlib.sha256(
            f"{_GOLDEN_SEED}/{round_no}".encode("utf-8")).hexdigest() == digest_hex
        expected_seed = int.from_bytes(bytes.fromhex(digest_hex)[:8], "big")
        assert s8b_floor_campaign._round_seed(_GOLDEN_SEED, round_no) == expected_seed


def test_build_schedule_golden_and_mutant_controls():
    freeze = _freeze_document()
    cells = [c for c in s8b_floor_campaign.enumerate_cells(freeze, stock_configuration=_STOCK)
             if c["holdout_id"] == "rr79"]
    assert len(cells) == 6
    schedule = s8b_floor_campaign.build_schedule(
        cells=cells, master_seed=_GOLDEN_SEED, n_sessions=2,
    )
    rows = [(r["seq"], r["round"], r["cell_id"]) for r in schedule]

    # 独立 reference から組んだ期待列 (production 出力の貼付ではない)。
    expected = []
    seq = 0
    for round_no in (1, 2):
        for cell_id in _ref_round_perm(round_no):
            expected.append((seq, round_no, cell_id))
            seq += 1
    assert rows == expected

    # mutant: seed 再利用 (全 round 同一 seed) → round1/round2 の置換が同一になるはず。
    # 実装は round ごとに別 seed を使うので置換は異なる (seed 再利用 mutant を殺す)。
    perm1 = [c for (s, r, c) in rows if r == 1]
    perm2 = [c for (s, r, c) in rows if r == 2]
    assert perm1 != perm2
    # mutant: round 起点 0 → round 値 {0,1} になる。実装は {1,2}。
    assert sorted({r for (s, r, c) in rows}) == [1, 2]


# =========================================================================== #
# 2. protocol strict 検証 + 承認凍結値 pin (β-1) + 版交差拒否 (β-2)             #
# =========================================================================== #

def test_validate_protocol_accepts_approved_and_rejects_unknown_missing():
    doc = _valid_protocol_dict()
    assert s8b_floor_campaign.validate_protocol(doc)["n_sessions"] == 8

    doc2 = _valid_protocol_dict()
    doc2["unexpected_extra_key"] = 1
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="未知"):
        s8b_floor_campaign.validate_protocol(doc2)

    doc3 = _valid_protocol_dict()
    del doc3["wired_min_rel_floor"]
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="欠落"):
        s8b_floor_campaign.validate_protocol(doc3)


def test_validate_protocol_rejects_removed_v1_keys():
    # v1 の blocks / replicates_per_block / min_block_gap_s を混ぜたら未知キーで拒否 (β-2)。
    for legacy in ("blocks", "replicates_per_block", "min_block_gap_s"):
        doc = _valid_protocol_dict()
        doc[legacy] = 2
        with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="未知"):
            s8b_floor_campaign.validate_protocol(doc)


def test_load_protocol_rejects_duplicate_top_level_key(tmp_path):
    text = '{"schema": "s8b-floor-protocol/v2", "schema": "duplicate"}'
    path = tmp_path / "dup.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="duplicate.*key"):
        s8b_floor_campaign.load_protocol(path)


@pytest.mark.parametrize("override,match", [
    ({"schema": "s8b-floor-protocol/v1"}, "schema"),
    ({"schedule_algorithm": "balanced-permutation/v1"}, "schedule_algorithm"),
    ({"formula": "s8b-floor-stats/v1"}, "formula"),
])
def test_validate_protocol_rejects_v1_cross_versions(override, match):
    doc = _valid_protocol_dict(**{})
    doc.update(override)
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match=match):
        s8b_floor_campaign.validate_protocol(doc)


@pytest.mark.parametrize("field,bad", [
    ("n_sessions", 4),
    ("n_sessions", 16),
    ("reps", 3),
    ("retry_slots_per_cell", 1),
    ("retry_slots_per_cell", 0),
    ("session_cv_max", "0.20"),
    ("cell_cv_max", "0.10"),
    ("scale_adequacy_rel_tolerance", "0.05"),
])
def test_validate_protocol_pins_approved_numbers(field, bad):
    doc = _valid_protocol_dict()
    doc[field] = bad
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match=field):
        s8b_floor_campaign.validate_protocol(doc)


def test_validate_protocol_pins_threshold_type_not_float():
    # 閾値は decimal 文字列で凍結 — float 0.10 は型不一致で拒否 (α-9)。
    doc = _valid_protocol_dict()
    doc["session_cv_max"] = 0.10
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="session_cv_max"):
        s8b_floor_campaign.validate_protocol(doc)


@pytest.mark.parametrize("reasons", [
    ["competing_process", "launch_failure", "nonfinite_or_partial_output"],  # 欠落
    ["competing_process", "launch_failure", "nonfinite_or_partial_output",
     "performance_anomaly", "correctness_red"],                              # 余分
    ["launch_failure", "competing_process", "nonfinite_or_partial_output",
     "performance_anomaly"],                                                 # 並べ替え
])
def test_validate_protocol_pins_reasons_exact_order(reasons):
    doc = _valid_protocol_dict()
    doc["allowed_excluded_reasons"] = reasons
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="allowed_excluded_reasons"):
        s8b_floor_campaign.validate_protocol(doc)


def test_validate_protocol_rejects_malformed_freeze_sha256():
    doc = _valid_protocol_dict()
    doc["freeze"] = {"path": doc["freeze"]["path"], "sha256": "not-a-sha256"}
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="SHA-256"):
        s8b_floor_campaign.validate_protocol(doc)


@pytest.mark.parametrize(
    "schema",
    [
        pytest.param("s8b-floor-manifest/v1", id="v1"),
        pytest.param("s8b-floor-manifest/v2", id="v2"),
    ],
)
def test_load_resume_manifest_rejects_legacy_schema(tmp_path, schema):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({
        "schema_version": schema, "protocol_sha256": "x",
        "freeze_sha256": "y", "binaries": {},
    }), encoding="utf-8")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="schema_version"):
        s8b_floor_campaign._load_resume_manifest(
            path, protocol_sha256="x", freeze_sha256="y", out_root=tmp_path,
            protocol={}, cells=[], schedule=[], mode="pilot")


def test_legacy_resume_manifest_without_perf_preflight_is_not_backfilled(tmp_path):
    protocol_sha = "p" * 64
    freeze_sha = "f" * 64
    protocol = {
        "freeze": {"path": "freeze.json", "sha256": freeze_sha},
        "env_tag": "env-x", "ccbench_pin": "1" * 40,
        "stock_configuration": "sort_best", "schedule_algorithm": "algorithm-x",
        "master_seed": "seed", "n_sessions": 1, "reps": 1, "extime_s": 1,
        "session_cv_max": "0.1", "cell_cv_max": "0.1",
    }
    cells = [{
        "cell_id": "cell", "holdout_id": "holdout",
        "configuration_id": "sort_best",
        "records": 1, "threads": 1, "workload": {},
    }]
    built = _honest_portable_built_record(
        tmp_path, configuration_id="sort_best",
    )
    manifest = s8b_floor_campaign.assemble_manifest(
        protocol=protocol, protocol_sha256=protocol_sha,
        freeze_sha256=freeze_sha, cells=cells, built=built, schedule=[],
    )
    path = tmp_path / "manifest.json"
    raw = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(raw)

    loaded, _sha, _artifact, _runtime = s8b_floor_campaign._load_resume_manifest(
        path, protocol_sha256=protocol_sha, freeze_sha256=freeze_sha,
        out_root=tmp_path, protocol=protocol, cells=cells, schedule=[], mode="pilot",
    )
    assert "perf_preflight" not in loaded
    assert s8b_floor_campaign._assert_perf_mode("pilot", None) is True
    assert path.read_bytes() == raw


def test_legacy_resume_manifest_with_perf_preflight_event_is_rejected(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with monkeypatch.context() as scoped:
        scoped.setattr(
            s8b_floor_campaign._Runner, "run",
            lambda self: (_ for _ in ()).throw(_SimulatedCrash("legacy manifest")),
        )
        with pytest.raises(_SimulatedCrash, match="legacy manifest"):
            _run_campaign(
                protocol, _verified_freeze(freeze), out_root=out_root,
                build_root=tmp_path / "bin",
                measure_fn=_make_measure_fn(
                    reps=5, value_fn=lambda cid: _BASE_TPS[cid],
                ),
                probe_fn=lambda: (1, "", ""),
                perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=True),
            )

    run_dir = _only_run_dir(out_root)
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["perf_preflight"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="perf-preflight receipt が manifest と不一致",
    ):
        _run_campaign(
            protocol, _verified_freeze(freeze), out_root=out_root,
            build_root=tmp_path / "bin",
            measure_fn=_make_measure_fn(
                reps=5, value_fn=lambda cid: _BASE_TPS[cid],
            ),
            probe_fn=lambda: (1, "", ""), resume_dir=run_dir,
        )


def test_assemble_manifest_records_official_degraded_observation(tmp_path):
    protocol_sha = "p" * 64
    freeze_sha = "f" * 64
    protocol = {
        "freeze": {"path": "freeze.json", "sha256": freeze_sha},
        "env_tag": "env-x", "ccbench_pin": "1" * 40,
        "stock_configuration": "sort_best", "schedule_algorithm": "algorithm-x",
        "master_seed": "seed", "n_sessions": 1, "reps": 1, "extime_s": 1,
        "session_cv_max": "0.1", "cell_cv_max": "0.1",
    }
    cells = [{
        "cell_id": "cell", "holdout_id": "holdout",
        "configuration_id": "sort_best",
        "records": 1, "threads": 1, "workload": {},
    }]
    manifest = s8b_floor_campaign.assemble_manifest(
        protocol=protocol, protocol_sha256=protocol_sha,
        freeze_sha256=freeze_sha, cells=cells,
        built=_honest_portable_built_record(
            tmp_path, configuration_id="sort_best",
        ),
        schedule=[], perf_preflight=_perf_receipt(available=False),
        mode="official",
    )
    assert set(manifest) == set(s8b_floor_contract._MANIFEST_KEYS) | {
        "perf_preflight", "perf_observation",
    }
    assert manifest["perf_observation"] == {
        "use_perf": False,
        "counter_status": "not_required",
        "missing_leading_indicators": [],
        "preflight": manifest["perf_preflight"],
        "claim_scope": {
            "throughput": "eligible", "perf_required": "unsupported",
        },
    }


def test_official_result_rejects_perf_preflight_receipt_fail_closed(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = s8b_floor_campaign.validate_protocol(
        _protocol(freeze_sha=_freeze_sha(freeze)))
    cells = s8b_floor_campaign.enumerate_cells(
        freeze, stock_configuration=protocol["stock_configuration"],
    )
    outcome = _run_campaign(
        protocol, verified, out_root=tmp_path / "out",
        build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(
            reps=protocol["reps"], value_fn=lambda cid: _BASE_TPS[cid],
        ),
        probe_fn=lambda: (1, "", ""),
    )
    records = _read_journal_lines(Path(outcome["run_dir"]) / "journal.jsonl")

    with pytest.raises(s8b_floor_campaign.CampaignAbort, match="official mode"):
        s8b_floor_campaign.assemble_result(
            protocol=protocol, mode="official", protocol_sha256="p" * 64,
            freeze_sha256="f" * 64, manifest_sha256="m" * 64,
            cells=cells, binaries=outcome["result"]["binaries"], records=records,
            holdout_admission=outcome["result"]["holdout_admission"],
            perf_preflight=_perf_receipt(),
        )

    assembled = s8b_floor_campaign.assemble_result(
        protocol=protocol, mode="pilot", protocol_sha256="p" * 64,
        freeze_sha256="f" * 64, manifest_sha256="m" * 64,
        cells=cells, binaries=outcome["result"]["binaries"], records=records,
        holdout_admission=outcome["result"]["holdout_admission"],
        perf_preflight=_perf_receipt(),
    )
    assert assembled["eligible_for_refreeze"] is False
    official_assembled = s8b_floor_campaign.assemble_result(
        protocol=protocol, mode="official", protocol_sha256="p" * 64,
        freeze_sha256="f" * 64, manifest_sha256="m" * 64,
        cells=cells, binaries=outcome["result"]["binaries"], records=records,
        holdout_admission=outcome["result"]["holdout_admission"],
        perf_preflight=None,
    )
    assert official_assembled["eligible_for_refreeze"] is False


def test_official_degraded_result_records_strict_perf_observation(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = s8b_floor_campaign.validate_protocol(
        _protocol(freeze_sha=_freeze_sha(freeze)))
    cells = s8b_floor_campaign.enumerate_cells(
        freeze, stock_configuration=protocol["stock_configuration"],
    )
    outcome = _run_campaign(
        protocol, verified, out_root=tmp_path / "out",
        build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(
            reps=protocol["reps"], value_fn=lambda cid: _BASE_TPS[cid],
            use_perf=False,
        ),
        probe_fn=lambda: (1, "", ""),
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
    )
    records = _read_journal_lines(Path(outcome["run_dir"]) / "journal.jsonl")
    assembled = s8b_floor_campaign.assemble_result(
        protocol=protocol, mode="official", protocol_sha256="p" * 64,
        freeze_sha256="f" * 64, manifest_sha256="m" * 64,
        cells=cells, binaries=outcome["result"]["binaries"], records=records,
        holdout_admission=outcome["result"]["holdout_admission"],
        perf_preflight=_perf_receipt(available=False),
    )
    assert set(assembled) == set(s8b_floor_contract.result_keys_for_mode(
        "official", perf_preflight=assembled["perf_preflight"],
    ))
    assert assembled["perf_observation"]["preflight"] == assembled["perf_preflight"]
    assert assembled["perf_observation"]["counter_status"] == "not_required"
    assert assembled["perf_observation"]["claim_scope"] == {
        "throughput": "eligible", "perf_required": "unsupported",
    }

    perf_prefixed = copy.deepcopy(records)
    session = next(row for row in perf_prefixed if row.get("event") == "session")
    session["run_cmd"] = f"perf stat -- {session['run_cmd']}"
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="perf stat prefix"):
        s8b_floor_campaign.assemble_result(
            protocol=protocol, mode="official", protocol_sha256="p" * 64,
            freeze_sha256="f" * 64, manifest_sha256="m" * 64,
            cells=cells, binaries=outcome["result"]["binaries"],
            records=perf_prefixed,
            holdout_admission=outcome["result"]["holdout_admission"],
            perf_preflight=_perf_receipt(available=False),
        )


def test_assemble_result_requires_holdout_admission_keyword():
    parameter = inspect.signature(
        s8b_floor_campaign.assemble_result,
    ).parameters["holdout_admission"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty


# =========================================================================== #
# 3. official mode は明示承認必須 — CLI + public + private core (δ-3)           #
# =========================================================================== #

@pytest.mark.parametrize("mode", ["pilot", "official"])
def test_validate_mode_accepts_only_known_modes(mode):
    validated = s8b_floor_campaign._validate_mode(mode)
    assert validated == mode
    assert type(validated) is str


@pytest.mark.parametrize("mode", ["", "PILOT", "pilot/../../escape", None, 1])
def test_validate_mode_rejects_unknown_and_path_traversal(mode, tmp_path):
    out_root = tmp_path / "out"
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError, match="mode は exact"):
        s8b_floor_campaign.run_campaign(
            None, None, out_root=out_root, mode=mode,
        )
    assert not out_root.exists()


def test_validate_mode_rejects_str_subclass_before_side_effects(tmp_path):
    class StatefulMode(str):
        pass

    out_root = tmp_path / "out"
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError, match="mode は exact"):
        s8b_floor_campaign.run_campaign(
            None, None, out_root=out_root, mode=StatefulMode("official"),
        )
    assert not out_root.exists()


def test_validate_mode_directly_rejects_str_subclass():
    class StatefulMode(str):
        pass

    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError, match="mode は exact"):
        s8b_floor_campaign._validate_mode(StatefulMode("official"))


def test_main_official_without_approval_is_refused_before_protocol_load(
        tmp_path, monkeypatch, capsys):
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text("{}", encoding="utf-8")
    protocol_loader = mock.Mock(side_effect=AssertionError("protocol loader reached"))
    monkeypatch.setattr(s8b_floor_campaign, "load_protocol", protocol_loader)
    rc = s8b_floor_campaign.main(["--mode", "official", "--protocol", str(protocol_path)])
    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "refused"
    assert "--confirm-official-floor-run" in payload["reason"]
    assert "§8" not in payload["reason"]
    assert "pilot のみ実行可" not in payload["reason"]
    protocol_loader.assert_not_called()


def test_main_official_with_approval_forwards_exact_bool_to_run_campaign(
        tmp_path, monkeypatch, capsys):
    protocol_path = tmp_path / s8b_floor_campaign._FLOOR_PROTOCOL_REL
    protocol_path.parent.mkdir(parents=True)
    protocol_path.write_text("{}", encoding="utf-8")
    protocol = {"freeze": {"path": "freeze.json", "sha256": "f" * 64}}
    verified = object()
    run_campaign = mock.Mock(return_value={
        "status": "completed", "run_dir": str(tmp_path / "run"),
    })
    monkeypatch.setattr(s8b_floor_campaign, "load_protocol", lambda _path: {})
    monkeypatch.setattr(s8b_floor_campaign, "validate_protocol", lambda _raw: protocol)
    monkeypatch.setattr(
        s8b_floor_campaign, "_load_verified_freeze", lambda *_args, **_kwargs: verified,
    )
    monkeypatch.setattr(s8b_floor_campaign, "repo_output_root", lambda: str(tmp_path))
    monkeypatch.setattr(s8b_floor_campaign, "run_campaign", run_campaign)
    monkeypatch.setattr(s8b_floor_campaign, "ROOT", tmp_path)

    rc = s8b_floor_campaign.main([
        "--mode", "official", "--protocol", str(protocol_path),
        "--confirm-official-floor-run",
    ])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["status"] == "completed"
    assert run_campaign.call_count == 1
    assert run_campaign.call_args.kwargs["confirm_official_floor_run"] is True


def test_main_pilot_rejects_noncanonical_protocol_path_before_loading(tmp_path, capsys):
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text("{}", encoding="utf-8")
    rc = s8b_floor_campaign.main([
        "--mode", "pilot", "--protocol", str(protocol_path),
    ])
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "canonical" in payload["error"]


def _oracle_unavailable_with_private_candidate(tmp_path: Path):
    candidate = sort_swo_oracle.OracleEnvironmentCandidate(
        "argument:dependency-root",
        tmp_path / "private-cache" / "masstree",
        "config-h-missing",
    )
    resolution = sort_swo_oracle.OracleEnvironmentResolutionFailure(
        "oracle-environment-dependency-unresolved",
        (
            sort_swo_oracle.OracleEnvironmentCandidate(
                "argument:compiler", Path(sys.executable), "selected",
            ),
        ),
        (candidate,),
    )
    result = sort_swo_oracle.SortSwoOracleResult(
        sort_swo_oracle.OracleStatus.UNAVAILABLE,
        "a" * 64,
        "b" * 64,
        infrastructure=sort_swo_oracle.OracleInfrastructureFailure(
            sort_swo_oracle.INFRASTRUCTURE_REASON_CODE,
            "environment-resolution",
            resolution.detail_code,
            environment_resolution=resolution,
        ),
    )
    return sort_swo_oracle.SortSwoOracleUnavailable(result)


def test_main_emits_private_structured_oracle_unavailable_and_returns_nonzero(
        tmp_path, monkeypatch, capsys):
    unavailable = _oracle_unavailable_with_private_candidate(tmp_path)
    monkeypatch.setattr(s8b_floor_campaign, "load_protocol", lambda _path: {})
    monkeypatch.setattr(
        s8b_floor_campaign,
        "validate_protocol",
        lambda _raw: {"freeze": {"path": "ignored", "sha256": "f" * 64}},
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_load_verified_freeze",
        lambda *_args, **_kwargs: object(),
    )
    monkeypatch.setattr(s8b_floor_campaign, "repo_output_root", lambda: str(tmp_path))
    monkeypatch.setattr(s8b_floor_campaign, "ROOT", tmp_path)

    def fail_campaign(*_args, **_kwargs):
        raise unavailable

    monkeypatch.setattr(s8b_floor_campaign, "run_campaign", fail_campaign)
    rc = s8b_floor_campaign.main([
        "--mode", "pilot", "--protocol",
        str(tmp_path / s8b_floor_campaign._FLOOR_PROTOCOL_REL),
    ])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["status"] == "error"
    assert payload["error"].startswith("SortSwoOracleUnavailable:")
    assert str(tmp_path / "private-cache" / "masstree") in captured.out
    assert "Traceback" not in captured.out


def test_oracle_unavailable_without_result_records_emission_failure():
    output = io.StringIO()
    error_output = io.StringIO()
    rc = s8b_floor_campaign._emit_sort_swo_unavailable(
        sort_swo_oracle.SortSwoOracleUnavailable(),
        stdout=output,
        stderr=error_output,
    )
    assert rc == 1
    assert error_output.getvalue() == ""
    payload = json.loads(output.getvalue())
    assert payload["error"].startswith("SortSwoOracleUnavailable:")
    assert payload["diagnostic_emission_failure"] == {
        "event": "diagnostic-emission-failed",
        "stage": "payload",
        "detail_code": "oracle-result-missing",
    }


def test_nonserializable_oracle_diagnostic_records_failure_without_hiding_unavailable(
        tmp_path, monkeypatch):
    unavailable = _oracle_unavailable_with_private_candidate(tmp_path)
    monkeypatch.setattr(
        s8b_floor_campaign,
        "private_attempt_record",
        lambda _result: {"not_json": tmp_path},
    )
    output = io.StringIO()
    rc = s8b_floor_campaign._emit_sort_swo_unavailable(
        unavailable, stdout=output, stderr=io.StringIO(),
    )
    assert rc == 1
    payload = json.loads(output.getvalue())
    assert payload["error"].startswith("SortSwoOracleUnavailable:")
    failure = payload["diagnostic_emission_failure"]
    assert failure["event"] == "diagnostic-emission-failed"
    assert failure["stage"] == "payload"
    assert failure["detail_code"] == "diagnostic-payload-TypeError"


def test_stdout_failure_records_diagnostic_emission_failure_on_stderr(tmp_path):
    class BrokenStdout:
        def write(self, _value):
            raise OSError("fixture stdout failure")

        def flush(self):
            raise AssertionError("write failure must stop before flush")

    error_output = io.StringIO()
    rc = s8b_floor_campaign._emit_sort_swo_unavailable(
        _oracle_unavailable_with_private_candidate(tmp_path),
        stdout=BrokenStdout(),
        stderr=error_output,
    )
    assert rc == 1
    payload = json.loads(error_output.getvalue())
    assert payload["error"].startswith("SortSwoOracleUnavailable:")
    assert payload["diagnostic_emission_failure"] == {
        "event": "diagnostic-emission-failed",
        "stage": "stdout-write",
        "detail_code": "diagnostic-write-OSError",
    }


def test_run_campaign_core_rejects_official_materializer_injection_before_side_effects(
        tmp_path):
    """wrapper を通らない core 直呼びでも任意 materializer は official に入れない。"""
    out_root = tmp_path / "out"
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="materializer"):
        s8b_floor_campaign._run_campaign_core(
            None, None, out_root=out_root, mode="official",
            build_fn=lambda *_args, **_kwargs: None,
            confirm_official_floor_run=True,
        )
    assert not out_root.exists()


def test_public_wrapper_rejects_unapproved_official_before_private_core(
        tmp_path, monkeypatch):
    """public gate 削除時は実 authority を通って private core sentinel が発火する。"""
    freeze = _freeze_document()
    out_root = tmp_path / "out"
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    authority = _test_holdout_authority(out_root, protocol, verified)
    private_core = mock.Mock(side_effect=AssertionError("private core reached"))
    monkeypatch.setattr(s8b_floor_campaign, "ROOT", authority)
    monkeypatch.setattr(s8b_floor_campaign, "_run_campaign_core", private_core)

    with pytest.raises(s8b_floor_campaign.FloorCampaignError) as caught:
        s8b_floor_campaign.run_campaign(
            protocol, verified, out_root=out_root, mode="official",
            protocol_path=authority / "output/s8b-freeze/floor_protocol.json",
        )
    assert str(caught.value) == (
        "official mode は明示承認がないため core で拒否する "
        "(--confirm-official-floor-run が必要)"
    )
    private_core.assert_not_called()
    assert not out_root.exists()


def test_public_wrapper_approved_official_forwards_exact_true_to_private_core(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    out_root = tmp_path / "out"
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    authority = _test_holdout_authority(out_root, protocol, verified)
    private_core = mock.Mock(return_value={"status": "sentinel"})
    monkeypatch.setattr(s8b_floor_campaign, "ROOT", authority)
    monkeypatch.setattr(s8b_floor_campaign, "_run_campaign_core", private_core)

    outcome = s8b_floor_campaign.run_campaign(
        protocol, verified, out_root=out_root, mode="official",
        protocol_path=authority / "output/s8b-freeze/floor_protocol.json",
        confirm_official_floor_run=True,
    )
    assert outcome == {"status": "sentinel"}
    assert private_core.call_count == 1
    assert private_core.call_args.kwargs["confirm_official_floor_run"] is True


def test_private_core_rejects_unapproved_official_before_downstream(
        tmp_path, monkeypatch):
    """private core gate 自身の exact 拒否と下流未到達を独立に固定する。"""
    freeze = _freeze_document()
    downstream = mock.Mock(side_effect=AssertionError("downstream reached"))
    monkeypatch.setattr(
        s8b_floor_campaign, "_validate_protocol_against_current", downstream,
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError) as caught:
        s8b_floor_campaign._run_campaign_core(
            _protocol(freeze_sha=_freeze_sha(freeze)), _verified_freeze(freeze),
            out_root=tmp_path / "out", mode="official",
        )
    assert str(caught.value) == (
        "official mode は明示承認がないため core で拒否する "
        "(--confirm-official-floor-run が必要)"
    )
    downstream.assert_not_called()
    assert not (tmp_path / "out").exists()


def test_official_permission_requires_exact_true():
    expected = (
        "official mode は明示承認がないため core で拒否する "
        "(--confirm-official-floor-run が必要)"
    )
    for unapproved in (False, None, 1):
        with pytest.raises(s8b_floor_campaign.FloorCampaignError) as caught:
            s8b_floor_campaign._assert_official_permitted("official", unapproved)
        assert str(caught.value) == expected
    s8b_floor_campaign._assert_official_permitted("official", True)
    s8b_floor_campaign._assert_official_permitted("pilot", 1)


def test_materializer_registry_covers_all_python_build_launches():
    """受理: exact gateway と名指しした非 materializer probe だけを分類する。

    拒否: 未登録 launch と登録済み実体の消失をどちらも registry 不一致にする。
    """
    campaign_root = ROOT / "orchestrator/campaign"
    direct_cmake: set[str] = {
        "orchestrator/campaign/s8b_expected_materialization.py:"
        "produce_expected_materialization_sha256",
    }
    missing_admission: list[str] = []
    seen_gateways: set[str] = set()
    admitted_gateways = {
        "orchestrator/campaign/pipeline.py:"
        "_prepare_evaluation_core._build_one",
        "orchestrator/campaign/s8b_floor_campaign.py:invoke_build",
    }
    explicit_non_materializer_process_sites = Counter({
        # Fixed git -C rev-parse/status metadata probe with a 10-second
        # timeout.  It binds each trace/perf build to the canonical checkout
        # but never names or executes a CCBench binary.
        "orchestrator/campaign/pipeline.py:"
        "_require_canonical_build_source_state._git": 1,
    })
    observed_non_materializer_process_sites: Counter[str] = Counter()
    non_materializer_process_calls: dict[str, ast.Call] = {}

    def static_keyword_names(call, owner) -> set[str]:
        """Direct keyword と呼出し前の単一 literal ``**dict`` だけを静的展開する。"""
        names = {keyword.arg for keyword in call.keywords if keyword.arg is not None}
        if not isinstance(owner, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return names
        for keyword in call.keywords:
            if keyword.arg is not None or not isinstance(keyword.value, ast.Name):
                continue
            bindings = []
            for node in ast.walk(owner):
                if not isinstance(node, ast.Assign) or node.lineno >= call.lineno:
                    continue
                if not any(
                        isinstance(target, ast.Name)
                        and target.id == keyword.value.id
                        for target in node.targets):
                    continue
                if isinstance(node.value, ast.Dict):
                    bindings.append(node.value)
            if len(bindings) != 1:
                continue
            keys = bindings[0].keys
            if all(
                    key is None
                    or (isinstance(key, ast.Constant)
                        and isinstance(key.value, str))
                    for key in keys):
                names.update(key.value for key in keys if key is not None)
        return names

    for path in sorted(campaign_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(ROOT).as_posix()
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node

        for function in (
                node for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
            strings = {
                node.value for node in ast.walk(function)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
            }
            if "--build" in strings and relative != "orchestrator/campaign/buildcache.py":
                direct_cmake.add(f"{relative}:{function.name}")

        for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
            target = call.func
            parts = []
            while isinstance(target, ast.Attribute):
                parts.append(target.attr)
                target = target.value
            if isinstance(target, ast.Name):
                parts.append(target.id)
            qualified = ".".join(reversed(parts))
            owner = call
            while owner in parents and not isinstance(
                    owner, (ast.FunctionDef, ast.AsyncFunctionDef)):
                owner = parents[owner]
            function_name = owner.name if isinstance(
                owner, (ast.FunctionDef, ast.AsyncFunctionDef)) else "<module>"
            site = f"{relative}:{function_name}"
            scopes = []
            scope = owner
            while isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
                scopes.append(scope.name)
                scope = parents.get(scope)
                while scope is not None and not isinstance(
                        scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    scope = parents.get(scope)
            scoped_site = f"{relative}:{'.'.join(reversed(scopes))}"
            if qualified == "subprocess_runner":
                observed_non_materializer_process_sites[scoped_site] += 1
                non_materializer_process_calls[scoped_site] = call
            is_buildcache_call = (
                qualified.endswith("buildcache.build")
                or qualified.endswith("buildcache.build_v2")
            )
            is_floor_materializer_call = (
                qualified == "build_fn"
                and site == "orchestrator/campaign/s8b_floor_campaign.py:invoke_build"
            )
            if not is_buildcache_call and not is_floor_materializer_call:
                continue
            required = {"admission", "build_context", "source_evidence"}
            gateway_site = (
                scoped_site
                if scoped_site in admitted_gateways
                else site
            )
            if gateway_site in admitted_gateways:
                seen_gateways.add(gateway_site)
                if is_floor_materializer_call:
                    keywords = static_keyword_names(call, owner)
                    if not (required | {"expected_toolchain_manifest"}) <= keywords:
                        missing_admission.append(
                            f"{relative}:{call.lineno}:{qualified}"
                        )
                else:
                    binding_owner = parents.get(owner)
                    while binding_owner is not None and not isinstance(
                            binding_owner,
                            (ast.FunctionDef, ast.AsyncFunctionDef)):
                        binding_owner = parents.get(binding_owner)
                    keywords = static_keyword_names(call, binding_owner)
                    if not required <= keywords:
                        missing_admission.append(
                            f"{relative}:{call.lineno}:{qualified}:gateway-preimage"
                        )
                continue
            keywords = static_keyword_names(call, owner)
            if not required <= keywords:
                missing_admission.append(f"{relative}:{call.lineno}:{qualified}")

    assert direct_cmake == set(s8b_materialization.NON_ADMISSIBLE_MATERIALIZERS)
    assert seen_gateways == admitted_gateways
    assert missing_admission == []
    assert (
        observed_non_materializer_process_sites
        == explicit_non_materializer_process_sites
    )

    probe_site = (
        "orchestrator/campaign/pipeline.py:"
        "_require_canonical_build_source_state._git"
    )
    probe_call = non_materializer_process_calls[probe_site]
    assert ast.unparse(probe_call.args[0]) == "['git', '-C', checkout, *args]"
    probe_keywords = {
        keyword.arg: ast.literal_eval(keyword.value)
        for keyword in probe_call.keywords
    }
    assert probe_keywords == {
        "capture_output": True,
        "text": True,
        "timeout": 10.0,
    }

    pipeline_tree = ast.parse(
        (campaign_root / "pipeline.py").read_text(encoding="utf-8"),
        filename=str(campaign_root / "pipeline.py"),
    )
    canonical_gate = next(
        node for node in pipeline_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_require_canonical_build_source_state"
    )
    fixed_git_calls = [
        tuple(ast.literal_eval(argument) for argument in call.args)
        for call in ast.walk(canonical_gate)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "_git"
    ]
    assert fixed_git_calls == [
        ("rev-parse", "--verify", "HEAD^{commit}"),
        ("status", "--porcelain=v1", "--untracked-files=no"),
    ]


@pytest.mark.parametrize("seam_name,seam_value", [
    ("measure_fn", lambda *_args: None),
    ("probe_fn", lambda: (1, "", "")),
    ("sleep_fn", lambda _seconds: None),
    ("monotonic_fn", lambda: 0.0),
    ("prepare_fn", _fake_prepare),
    ("now_fn", lambda: _FIXED_NOW),
    ("host_provenance_fn", _fixed_host),
    ("process_identity_fn", _fixed_process),
    ("execution_receipt_fn", _fixed_receipt),
    ("build_fn", lambda *_args, **_kwargs: None),
    ("repo_root", Path("sentinel-repo-root")),
    ("fetchcontent_base_dir", Path("sentinel-fetchcontent-base")),
    ("after_certificate_issued_fn", lambda _path: None),
    ("durable_root_policy", s8b_floor_campaign.DurableRootPolicy(
        approved_roots=(ROOT.resolve(),), forbidden_roots=())),
    ("perf_preflight_fn", lambda **_kwargs: _perf_receipt()),
])
def test_public_official_rejects_each_nondefault_seam_before_side_effects(
        tmp_path, seam_name, seam_value):
    freeze = _freeze_document()
    out_root = tmp_path / "out"
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match=seam_name):
        s8b_floor_campaign.run_campaign(
            _protocol(freeze_sha=_freeze_sha(freeze)), _verified_freeze(freeze),
            out_root=out_root, mode="official", **{seam_name: seam_value},
        )
    assert not out_root.exists()


@pytest.mark.parametrize("seam_name,seam_value", [
    ("measure_fn", lambda *_args: (_ for _ in ()).throw(AssertionError())),
    ("probe_fn", lambda: (_ for _ in ()).throw(AssertionError())),
    ("sleep_fn", lambda _seconds: (_ for _ in ()).throw(AssertionError())),
    ("monotonic_fn", lambda: (_ for _ in ()).throw(AssertionError())),
    ("prepare_fn", lambda *_args: (_ for _ in ()).throw(AssertionError())),
    ("now_fn", lambda: (_ for _ in ()).throw(AssertionError())),
    ("host_provenance_fn", lambda **_kwargs: (_ for _ in ()).throw(AssertionError())),
    ("process_identity_fn", lambda: (_ for _ in ()).throw(AssertionError())),
    ("execution_receipt_fn", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError())),
    ("build_fn", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError())),
    ("after_certificate_issued_fn", lambda _path: (_ for _ in ()).throw(AssertionError())),
    ("perf_preflight_fn", lambda **_kwargs: (_ for _ in ()).throw(AssertionError())),
])
def test_public_pilot_rejects_effect_capable_seams_without_calling_them(
        tmp_path, seam_name, seam_value):
    freeze = _freeze_document()
    out_root = tmp_path / "out"
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match=seam_name):
        s8b_floor_campaign.run_campaign(
            _protocol(freeze_sha=_freeze_sha(freeze)), _verified_freeze(freeze),
            out_root=out_root, mode="pilot", **{seam_name: seam_value},
        )
    assert not out_root.exists()


def test_refreeze_seam_classifier_covers_and_classifies_every_core_seam():
    excluded = {"out_root", "mode", "resume_dir", "confirm_official_floor_run"}
    core_keyword_only = {
        name for name, parameter in inspect.signature(
            s8b_floor_campaign._run_campaign_core,
        ).parameters.items()
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY
    }
    classifier_keyword_only = {
        name for name, parameter in inspect.signature(
            s8b_floor_campaign._nondefault_campaign_seams,
        ).parameters.items()
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY
    }
    assert core_keyword_only - classifier_keyword_only == excluded
    assert classifier_keyword_only - core_keyword_only == set()
    expected_seams = core_keyword_only - excluded
    assert classifier_keyword_only == expected_seams
    assert expected_seams == (
        s8b_floor_campaign._floor_contract.REFREEZE_DISQUALIFYING_SEAM_NAMES
    )
    for seam_name in sorted(expected_seams):
        sentinel = object()
        assert s8b_floor_campaign._nondefault_campaign_seams(
            **{seam_name: sentinel},
        ) == frozenset({seam_name})


def test_fetchcontent_seam_disqualifies_refreeze_eligibility():
    staged = Path("/tmp/izanagi-floor-fetchcontent")
    seams = s8b_floor_campaign._nondefault_campaign_seams(
        fetchcontent_base_dir=staged,
    )
    assert seams == frozenset({"fetchcontent_base_dir"})
    assert s8b_floor_campaign._derive_refreeze_eligibility(
        mode="official", resume_dir=None, nondefault_seams=seams,
    ) is False
    assert s8b_floor_campaign._derive_refreeze_eligibility(
        mode="official", resume_dir=None, nondefault_seams=frozenset(),
    ) is True


def test_run_campaign_forwards_fetchcontent_base_dir_to_core(tmp_path, monkeypatch):
    core = mock.Mock(return_value={"status": "completed"})
    monkeypatch.setattr(s8b_floor_campaign, "_run_campaign_core", core)
    monkeypatch.setattr(
        s8b_floor_campaign, "_require_supplied_protocol_authority",
        lambda *args, **kwargs: None,
    )
    fetchcontent_base_dir = tmp_path / "fetchcontent"
    outcome = s8b_floor_campaign.run_campaign(
        {}, {}, out_root=tmp_path / "out", mode="pilot",
        fetchcontent_base_dir=fetchcontent_base_dir,
    )
    assert outcome == {"status": "completed"}
    assert core.call_args.kwargs["fetchcontent_base_dir"] == fetchcontent_base_dir


def test_run_campaign_parser_accepts_fetchcontent_base_dir(tmp_path):
    fetchcontent_base_dir = tmp_path / "fetchcontent"
    args = s8b_floor_campaign._parser().parse_args([
        "--mode", "pilot", "--protocol", "protocol.json",
        "--fetchcontent-base-dir", str(fetchcontent_base_dir),
    ])
    assert args.fetchcontent_base_dir == fetchcontent_base_dir


def test_main_forwards_fetchcontent_base_dir_to_run_campaign(tmp_path, monkeypatch):
    protocol = _valid_protocol_dict()
    verified = object()
    run_campaign = mock.Mock(return_value={
        "status": "completed", "run_dir": str(tmp_path / "run"),
    })
    protocol_path = tmp_path / s8b_floor_campaign._FLOOR_PROTOCOL_REL
    fetchcontent_base_dir = tmp_path / "fetchcontent"
    monkeypatch.setattr(s8b_floor_campaign, "load_protocol", mock.Mock(return_value=protocol))
    monkeypatch.setattr(s8b_floor_campaign, "_load_verified_freeze", mock.Mock(return_value=verified))
    monkeypatch.setattr(s8b_floor_campaign, "repo_output_root", lambda: str(tmp_path))
    monkeypatch.setattr(s8b_floor_campaign, "run_campaign", run_campaign)
    monkeypatch.setattr(s8b_floor_campaign, "ROOT", tmp_path)

    assert s8b_floor_campaign.main([
        "--mode", "pilot", "--protocol", str(protocol_path),
        "--fetchcontent-base-dir", str(fetchcontent_base_dir),
    ]) == 0
    assert run_campaign.call_args.kwargs[
        "fetchcontent_base_dir"
    ] == fetchcontent_base_dir


def test_public_official_rejects_fetchcontent_base_dir_before_side_effects(tmp_path):
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="fetchcontent_base_dir",
    ):
        s8b_floor_campaign.run_campaign(
            {}, {}, out_root=tmp_path / "out", mode="official",
            fetchcontent_base_dir=tmp_path / "fetchcontent",
        )
    assert not (tmp_path / "out").exists()


def test_core_passes_fetchcontent_base_dir_to_fresh_and_resume_build_cells():
    source = textwrap.dedent(inspect.getsource(
        s8b_floor_campaign._run_campaign_core,
    ))
    tree = ast.parse(source)
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "build_cells"
    ]
    assert len(calls) == 2
    for call in calls:
        fetchcontent_keyword = next(
            item for item in call.keywords
            if item.arg == "fetchcontent_base_dir"
        )
        assert isinstance(fetchcontent_keyword.value, ast.Name)
        assert fetchcontent_keyword.value.id == "fetchcontent_base_dir"
        repo_keyword = next(
            item for item in call.keywords if item.arg == "repo_root"
        )
        assert isinstance(repo_keyword.value, ast.Name)
        assert repo_keyword.value.id == "repo_root"
        reservation_keyword = next(
            item for item in call.keywords
            if item.arg == "reservation_binding"
        )
        assert isinstance(reservation_keyword.value, ast.Name)
        assert reservation_keyword.value.id == "reservation_binding"


def test_captured_refreeze_seams_are_forwarded_to_claim_reservation_canonically():
    source = textwrap.dedent(inspect.getsource(
        s8b_floor_campaign._run_campaign_core,
    ))
    tree = ast.parse(source)
    reservation_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_reserve_floor_holdout_observations_core"
    ]
    assert len(reservation_calls) == 1
    keyword_names = {
        item.arg for item in reservation_calls[0].keywords
        if item.arg is not None
    }
    assert "irreversible_pilot_approved" not in keyword_names
    keyword = next(
        item for item in reservation_calls[0].keywords
        if item.arg == "nondefault_seams"
    )
    assert isinstance(keyword.value, ast.Call)
    assert isinstance(keyword.value.func, ast.Name)
    assert keyword.value.func.id == "sorted"
    assert len(keyword.value.args) == 1
    assert isinstance(keyword.value.args[0], ast.Name)
    assert keyword.value.args[0].id == "nondefault_seams"


def test_module_limit_keeps_code_substitution_and_offline_boundaries_explicit():
    doc = inspect.getdoc(s8b_floor_campaign) or ""
    assert "create-only" in doc
    assert "resume 後の basis 付替えの検出" in doc
    assert "同一 interpreter 内の code substitution" in doc
    assert "artifact 単体の offline 検証も行わず" in doc


def test_result_markdown_labels_refreeze_bit_as_producer_reported():
    source = inspect.getsource(s8b_floor_campaign._render_result_md)
    assert "eligible_for_refreeze (producer-reported)" in source


def test_refreeze_seam_classifier_defaults_and_core_forwarding_are_exact():
    core_signature = inspect.signature(s8b_floor_campaign._run_campaign_core)
    classifier_signature = inspect.signature(
        s8b_floor_campaign._nondefault_campaign_seams,
    )
    classifier_names = tuple(classifier_signature.parameters)
    for name in classifier_names:
        assert core_signature.parameters[name].default is \
            classifier_signature.parameters[name].default

    source = textwrap.dedent(inspect.getsource(
        s8b_floor_campaign._run_campaign_core,
    ))
    tree = ast.parse(source)
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_nondefault_campaign_seams"
    ]
    assert len(calls) == 1
    call = calls[0]
    assert call.args == []
    assert all(keyword.arg is not None for keyword in call.keywords)
    assert [keyword.arg for keyword in call.keywords] == list(classifier_names)
    for keyword in call.keywords:
        assert isinstance(keyword.value, ast.Name)
        assert keyword.value.id == keyword.arg


def test_refreeze_callable_defaults_survive_time_module_monkeypatch(
        tmp_path, monkeypatch):
    fake_sleep = lambda _seconds: None
    fake_monotonic = lambda: 0.0
    for entrypoint in (
            s8b_floor_campaign.run_campaign,
            s8b_floor_campaign._run_campaign_core,
            s8b_floor_campaign._nondefault_campaign_seams):
        signature = inspect.signature(entrypoint)
        assert signature.parameters["sleep_fn"].default is \
            s8b_floor_campaign._DEFAULT_SLEEP_FN
        assert signature.parameters["monotonic_fn"].default is \
            s8b_floor_campaign._DEFAULT_MONOTONIC_FN
    monkeypatch.setattr(s8b_floor_campaign.time, "sleep", fake_sleep)
    monkeypatch.setattr(s8b_floor_campaign.time, "monotonic", fake_monotonic)
    assert s8b_floor_campaign._nondefault_campaign_seams(
        sleep_fn=fake_sleep,
    ) == frozenset({"sleep_fn"})
    assert s8b_floor_campaign._nondefault_campaign_seams(
        monotonic_fn=fake_monotonic,
    ) == frozenset({"monotonic_fn"})
    for seam_name, seam_value in (
            ("sleep_fn", fake_sleep), ("monotonic_fn", fake_monotonic)):
        out_root = tmp_path / seam_name
        with pytest.raises(
                s8b_floor_campaign.FloorCampaignError, match=seam_name):
            s8b_floor_campaign.run_campaign(
                None, None, out_root=out_root, mode="pilot",
                **{seam_name: seam_value},
            )
        assert not out_root.exists()


def test_core_derives_refreeze_eligibility_at_entry_and_finalizes_without_args():
    source = textwrap.dedent(inspect.getsource(
        s8b_floor_campaign._run_campaign_core,
    ))
    tree = ast.parse(source)
    core = tree.body[0]
    finalizers = [
        node for node in core.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "apply_refreeze_eligibility"
    ]
    assert len(finalizers) == 1
    finalizer = finalizers[0]
    assert finalizer.args.args == []
    assert finalizer.args.posonlyargs == []
    assert finalizer.args.kwonlyargs == []
    assert finalizer.args.vararg is None
    assert finalizer.args.kwarg is None
    assert source.index("eligible_for_refreeze = _derive_refreeze_eligibility(") < source.index(
        "    _assert_official_permitted(mode, confirm_official_floor_run)"
    )
    assert source.index("eligible_for_refreeze = _derive_refreeze_eligibility(") < source.index(
        "    try:\n        runner.run()"
    )

    assembly_pairs = []
    for owner in ast.walk(core):
        for _field, value in ast.iter_fields(owner):
            if not isinstance(value, list):
                continue
            statements = [item for item in value if isinstance(item, ast.stmt)]
            if len(statements) != len(value):
                continue
            for index, statement in enumerate(statements):
                if not isinstance(statement, ast.Assign) or not isinstance(
                        statement.value, ast.Call):
                    continue
                call = statement.value
                if not isinstance(call.func, ast.Name) or call.func.id != "assemble_result":
                    continue
                assert index + 1 < len(statements)
                following = statements[index + 1]
                assert isinstance(following, ast.Expr)
                assert isinstance(following.value, ast.Call)
                assert isinstance(following.value.func, ast.Name)
                assert following.value.func.id == "apply_refreeze_eligibility"
                assert following.value.args == [] and following.value.keywords == []
                assembly_pairs.append((statement.lineno, following.lineno))
    assert len(assembly_pairs) == 2


def test_policy_unit_fresh_official_default_context_is_refreeze_eligible():
    """Policy-unit 正例。core binding と finalizer は独立 AST 契約で固定する。"""
    nondefault_seams = s8b_floor_campaign._nondefault_campaign_seams()
    assert nondefault_seams == frozenset()
    assert s8b_floor_campaign._derive_refreeze_eligibility(
        mode="official", resume_dir=None, nondefault_seams=nondefault_seams,
    ) is True


def test_refreeze_finalizer_is_unconditional_and_independent_of_run_outcomes():
    """P2 の静的等価検査: rep failure を含む runner outcome へ依存させない。"""
    source = textwrap.dedent(inspect.getsource(
        s8b_floor_campaign._run_campaign_core,
    ))
    core = ast.parse(source).body[0]
    finalizer = next(
        node for node in core.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "apply_refreeze_eligibility"
    )

    def eligible_target(node):
        return (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "result"
            and isinstance(node.slice, ast.Constant)
            and node.slice.value == "eligible_for_refreeze"
        )

    assignments = [
        node for node in ast.walk(core)
        if isinstance(node, ast.Assign)
        and any(eligible_target(target) for target in node.targets)
    ]
    assert len(assignments) == 1
    assignment = assignments[0]
    assert assignment in finalizer.body
    assert isinstance(assignment.value, ast.Name)
    assert assignment.value.id == "eligible_for_refreeze"
    loaded_names = {
        node.id for node in ast.walk(finalizer)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    assert loaded_names.isdisjoint({"runner", "excluded", "attempts", "records"})


def test_pilot_default_context_is_not_refreeze_eligible():
    assert s8b_floor_campaign._derive_refreeze_eligibility(
        mode="pilot", resume_dir=None,
        nondefault_seams=s8b_floor_campaign._nondefault_campaign_seams(),
    ) is False


def test_official_resume_is_not_refreeze_eligible_even_without_seams():
    assert s8b_floor_campaign._derive_refreeze_eligibility(
        mode="official", resume_dir=Path("existing-run"),
        nondefault_seams=s8b_floor_campaign._nondefault_campaign_seams(),
    ) is False


def test_assemble_result_caller_cannot_supply_refreeze_eligibility():
    signature = inspect.signature(s8b_floor_campaign.assemble_result)
    assert "eligible_for_refreeze" not in signature.parameters
    with pytest.raises(TypeError):
        signature.bind_partial(eligible_for_refreeze=True)


def test_production_entrypoints_have_no_holdout_gate_disabling_seam():
    forbidden = {
        "_holdout_reserve_fn", "_holdout_finalize_fn",
        "_holdout_assert_fn", "_attempt_consume_fn",
    }
    for entrypoint in (
            s8b_floor_campaign.run_campaign,
            s8b_floor_campaign._run_campaign_core):
        assert forbidden.isdisjoint(inspect.signature(entrypoint).parameters)


def test_holdout_signature_source_seam_is_private_core_only():
    seam = "_holdout_signature_source"
    assert seam in inspect.signature(
        s8b_floor_campaign._run_campaign_core,
    ).parameters
    assert seam not in inspect.signature(s8b_floor_campaign.run_campaign).parameters
    assert seam not in {
        action.dest for action in s8b_floor_campaign._parser()._actions
    }
    assert seam not in inspect.getsource(s8b_floor_campaign.run_campaign)
    for public_leaf in (
            s8b_floor_campaign._holdout_admission.reserve_floor_holdout_observations,
            holdout_observation.protected_signatures_from_verified_freeze):
        assert "_neutral_holdouts" not in inspect.signature(public_leaf).parameters


def test_public_entrypoints_have_no_removed_confirmation_parameter():
    removed = "confirm_irreversible_pilot_holdout"
    assert removed not in inspect.signature(
        s8b_floor_campaign.run_campaign,
    ).parameters
    assert removed not in inspect.signature(
        s8b_floor_campaign._run_campaign_core,
    ).parameters


def test_public_campaign_rejects_noncurrent_supplied_protocol_before_all_effects(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    legacy_protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    authority = _test_holdout_authority(out_root, legacy_protocol, verified)
    supplied_path = authority / s8b_floor_campaign._FLOOR_PROTOCOL_REL

    selected_protocol = copy.deepcopy(legacy_protocol)
    selected_protocol["ccbench_pin"] = "a" * 40
    selected_rel = s8b_floor_campaign._derived_reseal_protocol_relpath(
        selected_protocol["contract_sha256"], selected_protocol["ccbench_pin"],
    )
    selected_path = authority / selected_rel
    selected_path.parent.mkdir(parents=True)
    selected_path.write_bytes(s8b_floor_campaign._canonical_bytes(selected_protocol))
    subprocess.run(
        ["git", "add", selected_rel], cwd=str(authority), check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    subprocess.run(
        [
            "git", "update-index", "--add", "--cacheinfo",
            f"160000,{selected_protocol['ccbench_pin']},external/ccbench",
        ],
        cwd=str(authority), check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    subprocess.run(
        [
            "git", "-c", "user.name=fixture", "-c",
            "user.email=fixture@example.invalid", "commit", "-m",
            "select versioned protocol",
        ],
        cwd=str(authority), check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    shared_admission = (
        s8b_floor_campaign._holdout_admission.shared_admission_root(authority)
    )
    core = mock.Mock(side_effect=AssertionError(
        "authority mismatch must not reach the effect-capable core"
    ))
    monkeypatch.setattr(s8b_floor_campaign, "_run_campaign_core", core)

    with pytest.raises(s8b_floor_campaign.FloorCampaignError) as exc_info:
        s8b_floor_campaign.run_campaign(
            legacy_protocol, verified, out_root=out_root, mode="pilot",
            repo_root=authority, protocol_path=supplied_path,
        )

    message = str(exc_info.value)
    assert str(supplied_path) in message
    assert str(selected_path) in message
    core.assert_not_called()
    assert not out_root.exists()
    assert list(tmp_path.rglob("manifest.json")) == []
    assert list(tmp_path.rglob("binaries")) == []
    assert list(tmp_path.rglob("s8b-floor-pilot")) == []
    assert not shared_admission.exists()


def test_public_campaign_current_supplied_protocol_reaches_core(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    authority = _test_holdout_authority(out_root, protocol, verified)
    supplied_path = authority / s8b_floor_campaign._FLOOR_PROTOCOL_REL
    expected = {"status": "completed", "run_dir": str(tmp_path / "run")}
    core = mock.Mock(return_value=expected)
    monkeypatch.setattr(s8b_floor_campaign, "_run_campaign_core", core)

    outcome = s8b_floor_campaign.run_campaign(
        protocol, verified, out_root=out_root, mode="pilot",
        repo_root=authority, protocol_path=supplied_path,
    )

    assert outcome == expected
    core.assert_called_once()


def test_floor_driver_rejects_removed_confirmation_option():
    with pytest.raises(SystemExit) as exc_info:
        s8b_floor_campaign._parser().parse_args([
            "--mode", "pilot", "--protocol", "protocol.json",
            "--confirm-irreversible-pilot-holdout",
        ])
    assert exc_info.value.code == 2


def test_private_core_claims_only_after_nonmeasurement_preflight(tmp_path):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    authority = _test_holdout_authority(
        out_root, protocol, _verified_freeze(freeze),
    )
    shared = s8b_floor_campaign._holdout_admission.shared_admission_root(authority)
    order = []

    def perf_preflight(**_kwargs):
        order.append("perf")
        assert not (shared / "measurement-generation-claims").exists()
        return _perf_receipt()

    def probe():
        order.append("probe")
        assert len(list((
            shared / "measurement-generation-claims"
        ).iterdir())) == 12
        return (1, "", "")

    measure = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])

    def ordered_measure(*args):
        order.append("measure")
        assert len(list((
            shared / "measurement-generation-claims"
        ).iterdir())) == 12
        return measure(*args)

    _private_run_campaign(
        protocol, _verified_freeze(freeze), out_root=out_root, mode="pilot",
        measure_fn=ordered_measure, probe_fn=probe,
        perf_preflight_fn=perf_preflight, sleep_fn=lambda _seconds: None,
        monotonic_fn=lambda: 0.0, prepare_fn=_fake_prepare,
        now_fn=lambda: _FIXED_NOW, build_fn=_make_fake_build(tmp_path / "bin"),
        durable_root_policy=_durable_policy(out_root),
    )
    assert order[0] == "perf"
    assert order.index("perf") < order.index("probe")
    assert order.index("perf") < order.index("measure")


def test_private_signature_source_keeps_real_claim_ledger_and_tickets(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    authority = _test_holdout_authority(out_root, protocol, verified)
    shared = s8b_floor_campaign._holdout_admission.shared_admission_root(authority)

    _private_run_campaign(
        protocol, verified, out_root=out_root, mode="pilot",
        measure_fn=_make_measure_fn(
            reps=5, value_fn=lambda cid: _BASE_TPS[cid],
        ),
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(),
        probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
        monotonic_fn=lambda: 0.0, prepare_fn=_fake_prepare,
        now_fn=lambda: _FIXED_NOW, build_fn=_make_fake_build(tmp_path / "bin"),
        durable_root_policy=_durable_policy(out_root),
    )

    assert len(list((
        shared / "measurement-generation-claims"
    ).iterdir())) == 12
    assert len(s8b_floor_campaign._holdout_admission._read_ledger(
        shared / "ledger.jsonl",
    )) == 12
    assert len(list((
        shared / "measurement-generation-consumed"
    ).iterdir())) == 12 * 8
    assert len(s8b_floor_campaign._holdout_admission._read_ledger(
        shared / "attempt-ledger.jsonl",
    )) == 12 * 8


def test_resume_absent_journal_is_rejected_before_perf_preflight(tmp_path):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    resume_dir = (
        out_root / "env" / protocol["env_tag"] / "calibration"
        / "s8b-floor-pilot" / "issued-run"
    )
    resume_dir.mkdir(parents=True)
    called = []
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="resume state invalid"):
        _private_run_campaign(
            protocol, _verified_freeze(freeze), out_root=out_root, mode="pilot",
            resume_dir=resume_dir,
            perf_preflight_fn=lambda **_kwargs: called.append("perf"),
            durable_root_policy=_durable_policy(out_root),
        )
    assert called == []


def _forbid_measure(*_a, **_kw):
    raise AssertionError("pin/env/hash の検査より前で measure_fn が呼ばれてはいけない")


# =========================================================================== #
# 4. env contract 結線 (F4) — lookup fail-closed + machine-pin                  #
# =========================================================================== #

def test_run_campaign_rejects_unknown_env_tag(tmp_path):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze), env_tag="pegasus-unknown")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="env 契約"):
        _run_campaign(protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
                      build_root=tmp_path / "bin", measure_fn=_forbid_measure,
                      probe_fn=lambda: (1, "", ""))


def test_machine_env_tag_for_site_uses_required_registry_contract(monkeypatch):
    expected_tags = {
        contract.env_tag
        for contract in ec.REGISTRY.values()
        if contract.attestation_mode == "required"
    }
    assert len(expected_tags) == 1
    monkeypatch.setattr(
        s8b_floor_campaign.site_policy,
        "current_site",
        lambda: s8b_floor_campaign.site_policy.PEGASUS_COMPUTE,
    )
    observed_site = s8b_floor_campaign.site_policy.current_site()
    assert observed_site == s8b_floor_campaign.site_policy.PEGASUS_COMPUTE
    assert s8b_floor_campaign._machine_env_tag_for_site(observed_site) == (
        next(iter(expected_tags))
    )


def test_machine_env_tag_for_site_rejects_zero_required_contracts(monkeypatch):
    monkeypatch.setattr(
        s8b_floor_campaign.site_policy,
        "current_site",
        lambda: s8b_floor_campaign.site_policy.PEGASUS_COMPUTE,
    )
    monkeypatch.setattr(s8b_floor_campaign._env_contract, "REGISTRY", {})
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="required attestation"):
        s8b_floor_campaign._machine_env_tag_for_site(
            s8b_floor_campaign.site_policy.current_site()
        )


def test_machine_env_tag_for_site_rejects_multiple_required_contracts(monkeypatch):
    monkeypatch.setattr(
        s8b_floor_campaign.site_policy,
        "current_site",
        lambda: s8b_floor_campaign.site_policy.PEGASUS_COMPUTE,
    )
    monkeypatch.setattr(
        s8b_floor_campaign._env_contract,
        "REGISTRY",
        {
            "required-first": SimpleNamespace(
                env_tag="fixture-required-first", attestation_mode="required",
            ),
            "required-second": SimpleNamespace(
                env_tag="fixture-required-second", attestation_mode="required",
            ),
        },
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="required attestation"):
        s8b_floor_campaign._machine_env_tag_for_site(
            s8b_floor_campaign.site_policy.current_site()
        )


def test_machine_env_tag_for_site_rejects_required_lookup_exception(monkeypatch):
    monkeypatch.setattr(
        s8b_floor_campaign.site_policy,
        "current_site",
        lambda: s8b_floor_campaign.site_policy.PEGASUS_COMPUTE,
    )

    def fail_required_lookup():
        raise ec.EnvContractError("fixture required lookup failure")

    monkeypatch.setattr(
        s8b_floor_campaign._env_contract,
        "lookup_required_attestation_contract",
        fail_required_lookup,
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="required attestation"):
        s8b_floor_campaign._machine_env_tag_for_site(
            s8b_floor_campaign.site_policy.current_site()
        )


def test_machine_env_tag_for_site_uses_unique_none_registry_contract(monkeypatch):
    expected_tags = {
        contract.env_tag
        for contract in ec.REGISTRY.values()
        if contract.attestation_mode == "none"
    }
    assert len(expected_tags) == 1
    monkeypatch.setattr(
        s8b_floor_campaign.site_policy,
        "current_site",
        lambda: s8b_floor_campaign.site_policy.OTHER,
    )
    observed_site = s8b_floor_campaign.site_policy.current_site()
    assert observed_site == s8b_floor_campaign.site_policy.OTHER
    assert s8b_floor_campaign._machine_env_tag_for_site(observed_site) == (
        next(iter(expected_tags))
    )


def test_machine_env_tag_for_site_rejects_zero_none_contracts(monkeypatch):
    monkeypatch.setattr(
        s8b_floor_campaign.site_policy,
        "current_site",
        lambda: s8b_floor_campaign.site_policy.OTHER,
    )
    monkeypatch.setattr(s8b_floor_campaign._env_contract, "REGISTRY", {})
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="none attestation"):
        s8b_floor_campaign._machine_env_tag_for_site(
            s8b_floor_campaign.site_policy.current_site()
        )


def test_machine_env_tag_for_site_rejects_multiple_none_contracts(monkeypatch):
    monkeypatch.setattr(
        s8b_floor_campaign.site_policy,
        "current_site",
        lambda: s8b_floor_campaign.site_policy.OTHER,
    )
    monkeypatch.setattr(
        s8b_floor_campaign._env_contract,
        "REGISTRY",
        {
            "first": SimpleNamespace(env_tag="fixture-none-first", attestation_mode="none"),
            "second": SimpleNamespace(env_tag="fixture-none-second", attestation_mode="none"),
        },
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="none attestation"):
        s8b_floor_campaign._machine_env_tag_for_site(
            s8b_floor_campaign.site_policy.current_site()
        )


def test_machine_env_tag_for_site_rejects_duplicate_registry_env_tag(monkeypatch):
    monkeypatch.setattr(
        s8b_floor_campaign.site_policy,
        "current_site",
        lambda: s8b_floor_campaign.site_policy.OTHER,
    )
    monkeypatch.setattr(
        s8b_floor_campaign._env_contract,
        "REGISTRY",
        {
            "none": SimpleNamespace(
                env_tag="fixture-duplicate", attestation_mode="none",
            ),
            "required": SimpleNamespace(
                env_tag="fixture-duplicate", attestation_mode="required",
            ),
        },
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="none attestation"):
        s8b_floor_campaign._machine_env_tag_for_site(
            s8b_floor_campaign.site_policy.current_site()
        )


def test_machine_env_tag_for_site_rejects_unhandled_site(monkeypatch):
    monkeypatch.setattr(
        s8b_floor_campaign.site_policy,
        "current_site",
        lambda: s8b_floor_campaign.site_policy.PEGASUS_LOGIN,
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="未対応 site"):
        s8b_floor_campaign._machine_env_tag_for_site(
            s8b_floor_campaign.site_policy.current_site()
        )


def test_run_campaign_machine_pin_rejects_contract_tag_mismatch(tmp_path):
    """契約の env_tag が registry-derived machine tag と一致しなければ拒否する。"""
    freeze = _freeze_document()
    fake_contract = ec.ExecutionEnvironmentContract(
        env_tag="foreign-env", clocks_per_us=2100, numactl=(),
        attestation_mode="none",
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=True),
        calibration_ref=ec.CalibrationRef(path="output/x.json", sha256="0" * 64),
    )
    # validate_protocol の contract_sha256 cross-field 検査を通すため mocked contract の
    # fingerprint を焼く (rejection は後段の machine-pin で起きることを固定する)。
    protocol = _protocol(freeze_sha=_freeze_sha(freeze), env_tag="foreign-env",
                         contract_sha256=fake_contract.contract_sha256)
    verified = s8b_floor_campaign.env_attestation.load_verified_calibration(
        ec.lookup(ENV_TAG), ROOT,
    )
    with mock.patch.object(s8b_floor_campaign._env_contract, "lookup",
                           return_value=fake_contract), mock.patch.object(
            s8b_floor_campaign.env_attestation, "load_verified_calibration",
            return_value=verified):
        with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="machine-pin"):
            _run_campaign(protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
                          build_root=tmp_path / "bin", measure_fn=_forbid_measure,
                          probe_fn=lambda: (1, "", ""))


def test_non_single_process_contract_does_not_require_floor_submit_receipt(
        tmp_path, monkeypatch):
    """POS-7: a non-single-process contract keeps the receipt gate out of path."""
    contract = ec.lookup(ENV_TAG)
    assert contract.isolation_policy.single_process is False

    def receipt_tripwire(*_args, **_kwargs):
        raise AssertionError("non-single-process path must not load a floor receipt")

    monkeypatch.setattr(
        s8b_floor_campaign.floor_submit_receipt,
        "load_floor_submit_receipt",
        receipt_tripwire,
    )
    freeze = _freeze_document()
    outcome = _run_campaign(
        _protocol(freeze_sha=_freeze_sha(freeze)),
        _verified_freeze(freeze),
        out_root=tmp_path / "out", build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
        probe_fn=lambda: (1, "", ""),
    )
    assert outcome["status"] == "completed"


def test_required_binding_missing_rejected_by_production_entry_without_side_effects(
        tmp_path, monkeypatch):
    ctx = _install_required_contract(tmp_path, monkeypatch)
    for key in list(ctx["binding_values"]):
        monkeypatch.delenv(key, raising=False)
    out_root = ctx["out_root"]
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="reservation preflight"):
        _private_run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=out_root, mode="pilot", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, repo_root=ctx["repo_root"],
            build_fn=_make_fake_build(tmp_path / "bin"),
            durable_root_policy=_durable_policy(out_root),
        )
    assert not out_root.exists()


def test_required_script_sha_receipt_mismatch_is_zero_side_effect_production_refusal(
        tmp_path, monkeypatch):
    """MUT-C1 / MUT-E2: production entry must consume the canonical receipt."""
    ctx = _install_required_contract(tmp_path, monkeypatch)
    _provision_claim_root(ctx)
    _write_floor_submit_receipt(
        ctx["repo_root"], env_tag=ctx["contract"].env_tag,
        binding_values=ctx["binding_values"], job_script_sha256="e" * 64,
    )
    before = _tree_snapshot(ctx["out_root"])

    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="submitter receipt preflight.*script hash mismatch"):
        _private_run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, repo_root=ctx["repo_root"],
            build_fn=_make_fake_build(tmp_path / "bin"),
            durable_root_policy=_durable_policy(ctx["out_root"]),
        )

    assert _tree_snapshot(ctx["out_root"]) == before


def test_required_nonce_receipt_mismatch_is_zero_side_effect_refusal(
        tmp_path, monkeypatch):
    """MUT-C2: expected nonce must come from ReservationBinding, not receipt."""
    ctx = _install_required_contract(tmp_path, monkeypatch)
    _provision_claim_root(ctx)
    _write_floor_submit_receipt(
        ctx["repo_root"], env_tag=ctx["contract"].env_tag,
        binding_values=ctx["binding_values"], nonce="e" * 32,
    )
    before = _tree_snapshot(ctx["out_root"])

    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="submitter receipt preflight.*nonce mismatch"):
        _private_run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, repo_root=ctx["repo_root"],
            build_fn=_make_fake_build(tmp_path / "bin"),
            durable_root_policy=_durable_policy(ctx["out_root"]),
        )

    assert _tree_snapshot(ctx["out_root"]) == before


def test_required_v1_receipt_mode_mismatch_rejected_without_side_effects(
        tmp_path, monkeypatch):
    ctx = _install_required_contract(tmp_path, monkeypatch)

    def v1_issuer(contract, _verified, *, now_fn):
        return _fixed_receipt(contract, now_fn=now_fn)

    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="attestation_mode"):
        _private_run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, repo_root=ctx["repo_root"],
            execution_receipt_fn=v1_issuer,
            build_fn=_make_fake_build(tmp_path / "bin"),
            durable_root_policy=_durable_policy(ctx["out_root"]),
        )
    assert not ctx["out_root"].exists()


def test_required_attestation_comparison_failure_has_zero_side_effects(
        tmp_path, monkeypatch):
    ctx = _install_required_contract(tmp_path, monkeypatch)
    observed_expected_shape = dataclasses.replace(
        ctx["verified"].attestation_profile,
        cpu=dataclasses.replace(
            ctx["verified"].attestation_profile.cpu, vendor="DifferentVendor",
        ),
    )
    observed = _observed(observed_expected_shape)
    monkeypatch.setattr(s8b_floor_campaign.env_attestation, "probe", lambda: observed)
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="comparisons failed"):
        _private_run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, repo_root=ctx["repo_root"],
            build_fn=_make_fake_build(tmp_path / "bin"),
            durable_root_policy=_durable_policy(ctx["out_root"]),
        )
    assert not ctx["out_root"].exists()


def test_required_calibration_sha_mismatch_has_zero_side_effects(tmp_path, monkeypatch):
    ctx = _install_required_contract(tmp_path, monkeypatch)
    bad_contract = dataclasses.replace(
        ctx["contract"],
        calibration_ref=dataclasses.replace(
            ctx["contract"].calibration_ref, sha256="0" * 64,
        ),
    )
    monkeypatch.setattr(
        s8b_floor_campaign._env_contract, "lookup", lambda _tag: bad_contract,
    )
    protocol = _protocol(
        freeze_sha=_freeze_sha(ctx["freeze"]), env_tag=bad_contract.env_tag,
        contract_sha256=bad_contract.contract_sha256,
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="sha256 不一致"):
        _private_run_campaign(
            protocol, _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, repo_root=ctx["repo_root"],
            build_fn=_make_fake_build(tmp_path / "bin"),
            durable_root_policy=_durable_policy(ctx["out_root"]),
        )
    assert not ctx["out_root"].exists()


def test_required_existing_claim_reports_owner_and_changes_nothing(
        tmp_path, monkeypatch):
    ctx = _install_required_contract(tmp_path, monkeypatch)
    protocol, _contract = s8b_floor_campaign._validate_protocol_against_current(
        ctx["protocol"],
    )
    identity = s8b_floor_campaign._fresh_run_id(
        s8b_floor_campaign._canonical_sha256(protocol), _FIXED_NOW,
    )
    claim_root = _provision_claim_root(ctx)
    existing = campaign_claim.ClaimRecord(
        campaign_identity=identity,
        protocol_digest=s8b_floor_campaign._canonical_sha256(protocol),
        job_id="existing-job", host="existing-host",
        boot_id=ctx["binding_values"]["IZANAGI_RESERVATION_BOOT_ID"],
        pid=os.getpid(), proc_starttime=campaign_claim.read_proc_starttime(),
        created_utc=_FIXED_NOW.isoformat(),
    )
    campaign_claim.acquire_claim(claim_root, existing)
    before = _tree_snapshot(ctx["out_root"])
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="existing-job"):
        _private_run_campaign(
            protocol, _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, repo_root=ctx["repo_root"],
            build_fn=_make_fake_build(tmp_path / "bin"),
            durable_root_policy=_durable_policy(ctx["out_root"]),
        )
    assert _tree_snapshot(ctx["out_root"]) == before


def test_required_same_protocol_different_run_is_rejected_without_new_side_effects(
        tmp_path, monkeypatch):
    """MUT-C3: floor claim digest is protocol SHA, while identity remains per-run."""
    ctx = _install_required_contract(tmp_path, monkeypatch)
    protocol, _contract = s8b_floor_campaign._validate_protocol_against_current(
        ctx["protocol"],
    )
    protocol_digest = s8b_floor_campaign._canonical_sha256(protocol)
    claim_root = _provision_claim_root(ctx)
    campaign_claim.acquire_claim(
        claim_root,
        campaign_claim.ClaimRecord(
            campaign_identity=f"other-run-{protocol_digest[:8]}",
            protocol_digest=protocol_digest,
            job_id="existing-job", host="existing-host",
            boot_id=ctx["binding_values"]["IZANAGI_RESERVATION_BOOT_ID"],
            pid=os.getpid(), proc_starttime=campaign_claim.read_proc_starttime(),
            created_utc=_FIXED_NOW.isoformat(),
        ),
    )
    before = _tree_snapshot(ctx["out_root"])

    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="同一 protocol"):
        _private_run_campaign(
            protocol, _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, repo_root=ctx["repo_root"],
            build_fn=_make_fake_build(tmp_path / "bin"),
            durable_root_policy=_durable_policy(ctx["out_root"]),
        )

    assert _tree_snapshot(ctx["out_root"]) == before


def test_required_missing_preprovisioned_claim_root_is_side_effect_free(
        tmp_path, monkeypatch):
    ctx = _install_required_contract(tmp_path, monkeypatch)
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="provisioning"):
        _private_run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, repo_root=ctx["repo_root"],
            build_fn=_make_fake_build(tmp_path / "bin"),
            durable_root_policy=_durable_policy(ctx["out_root"]),
        )
    assert not ctx["out_root"].exists()


def test_required_reservation_loss_is_typed_campaign_terminal_with_no_values(
        tmp_path, monkeypatch, _activate_synthetic_env_authority):
    ctx = _install_required_contract(tmp_path, monkeypatch)
    _activate_synthetic_env_authority(
        ctx["contract"], repo_root=ctx["repo_root"],
        authority_dir=tmp_path / "authority",
    )
    _provision_claim_root(ctx)
    ticks = iter((0.0, 200_000.0))
    monotonic_fn = lambda: next(ticks)
    measure = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    with pytest.raises(reservation.ReservationError, match="残時間が不足"):
        _private_run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot", measure_fn=measure,
            perf_preflight_fn=lambda **_kwargs: _perf_receipt(),
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            monotonic_fn=monotonic_fn, now_fn=lambda: _FIXED_NOW,
            repo_root=ctx["repo_root"], build_fn=_make_fake_build(tmp_path / "bin"),
            durable_root_policy=_durable_policy(ctx["out_root"]),
        )
    journals = list(ctx["out_root"].rglob("journal.jsonl"))
    assert len(journals) == 1
    records = _read_journal_lines(journals[0])
    assert records[-1]["status"] == "reservation-lost"
    assert records[-1]["bench_values"] == []
    assert records[-1]["numeric_values_eligible"] is False
    assert not any(record.get("event") == "session" for record in records)
    assert not any(record.get("event") == "session-start" for record in records)
    assert measure.calls == []
    assert not (journals[0].parent / "result.json").exists()


def test_required_recheck_pins_remaining_budget_margin_and_injected_monotonic_clock(
        tmp_path, monkeypatch, _activate_synthetic_env_authority):
    ctx = _install_required_contract(tmp_path, monkeypatch)
    _activate_synthetic_env_authority(
        ctx["contract"], repo_root=ctx["repo_root"],
        authority_dir=tmp_path / "authority",
    )
    _provision_claim_root(ctx)

    class Clock:
        def __init__(self):
            self.values = iter((0.0, 200_000.0))

        def __call__(self):
            return next(self.values)

    clock = Clock()
    captured = []
    original = reservation.ReservationCheck.recheck

    def recheck_spy(self, *, required_s=None, safety_margin_s=None,
                    monotonic_now_fn=time.monotonic):
        captured.append((required_s, safety_margin_s, monotonic_now_fn))
        return original(
            self, required_s=required_s, safety_margin_s=safety_margin_s,
            monotonic_now_fn=monotonic_now_fn,
        )

    with mock.patch.object(reservation.ReservationCheck, "recheck", recheck_spy), \
            pytest.raises(reservation.ReservationError, match="残時間が不足"):
        _private_run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot",
            measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
            perf_preflight_fn=lambda **_kwargs: _perf_receipt(),
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            monotonic_fn=clock, now_fn=lambda: _FIXED_NOW,
            repo_root=ctx["repo_root"], build_fn=_make_fake_build(tmp_path / "bin"),
            durable_root_policy=_durable_policy(ctx["out_root"]),
        )

    cells = s8b_floor_campaign.enumerate_cells(
        ctx["freeze"], stock_configuration=ctx["protocol"]["stock_configuration"],
    )
    schedule = s8b_floor_campaign.build_schedule(
        cells=cells, master_seed=ctx["protocol"]["master_seed"],
        n_sessions=ctx["protocol"]["n_sessions"],
    )
    expected_attempts = len(schedule) + len(cells) * ctx["protocol"]["retry_slots_per_cell"]
    expected_required = expected_attempts * (
        ctx["protocol"]["extime_s"] * ctx["protocol"]["reps"] + 120
    )
    assert captured == [(expected_required, 600, clock)]


def test_required_mode_happy_path_pins_journal_claim_and_receipt_shape(
        tmp_path, monkeypatch, _activate_synthetic_env_authority):
    ctx = _install_required_contract(tmp_path, monkeypatch)
    _activate_synthetic_env_authority(
        ctx["contract"], repo_root=ctx["repo_root"],
        authority_dir=tmp_path / "authority",
    )
    # POS-6: hostname is observation only; receipt authority is job/SHA/nonce.
    assert (
        ctx["binding_values"]["IZANAGI_RESERVATION_HOST"]
        != os.uname().nodename
    )
    claim_root = _provision_claim_root(ctx)
    measure = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])

    outcome = _private_run_campaign(
        ctx["protocol"], _verified_freeze(ctx["freeze"]),
        out_root=ctx["out_root"], mode="pilot", measure_fn=measure,
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(),
        probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
        monotonic_fn=lambda: 0.0, now_fn=lambda: _FIXED_NOW,
        repo_root=ctx["repo_root"], build_fn=_make_fake_build(tmp_path / "bin"),
        durable_root_policy=_durable_policy(ctx["out_root"]),
    )

    assert outcome["status"] == "completed"
    journal = _read_journal_lines(Path(outcome["run_dir"]) / "journal.jsonl")
    preflight = [record for record in journal
                 if record.get("event") == "reservation-preflight"]
    assert preflight == [{
        "event": "reservation-preflight",
        "required_s": 30000,
        "safety_margin_s": 600,
        "formula": s8b_floor_campaign._FLOOR_RESERVATION_FORMULA,
        "build_cap_per_cell_s": 900,
        "shared_dependency_prebuild": True,
        "dependency_configure_cap_s": 900,
        "dependency_target_cap_s": 900,
        "verify_cap_per_attempt_s": 120,
        "finalize_reserve_s": 600,
    }]
    start = next(record for record in journal if record.get("event") == "campaign-start")
    assert s8b_floor_campaign.execution_guard.receipt_matches_contract(
        start["execution_receipt"], env_tag=ctx["contract"].env_tag,
        contract_sha256=ctx["contract"].contract_sha256,
        attestation_mode="required", verified_calibration=ctx["verified"],
    )
    claims = list(claim_root.glob("*.claim"))
    assert len(claims) == 1
    claim_payload = json.loads(claims[0].read_text(encoding="utf-8"))
    assert claim_payload["host"] == ctx["binding_values"]["IZANAGI_RESERVATION_HOST"]
    assert claim_payload["protocol_digest"] == s8b_floor_campaign._canonical_sha256(
        ctx["protocol"],
    )
    assert set(claim_payload) == {
        "campaign_identity", "protocol_digest", "job_id", "host", "boot_id", "pid",
        "proc_starttime", "created_utc",
    }
    assert journal[-1] == {"event": "terminal", "status": "completed"}


def test_floor_legacy_build_fallback_hits_contract_provenance_assert(
        tmp_path, monkeypatch):
    ctx = _install_required_contract(tmp_path, monkeypatch)
    _provision_claim_root(ctx)
    fake_v2_shape = _make_fake_build(tmp_path / "bin")

    def legacy_fallback(genome, **kwargs):
        kwargs.pop("contract")
        return fake_v2_shape(genome, contract=None, **kwargs)

    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="legacy build"):
        _private_run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot", measure_fn=_forbid_measure,
            perf_preflight_fn=lambda **_kwargs: _perf_receipt(),
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, repo_root=ctx["repo_root"],
            build_fn=legacy_fallback,
            durable_root_policy=_durable_policy(ctx["out_root"]),
        )


def test_run_campaign_rejects_freeze_byte_hash_mismatch(tmp_path):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    other = json.dumps({"different": "document"}).encode("utf-8")
    tampered = VerifiedFreeze(document=freeze, sha256=hashlib.sha256(other).hexdigest())
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="bytes-hash pin"):
        _run_campaign(protocol, tampered, out_root=tmp_path / "out",
                      build_root=tmp_path / "bin", measure_fn=_forbid_measure,
                      probe_fn=lambda: (1, "", ""))


def test_measure_fn_default_uses_contract_clocks_and_numactl(tmp_path):
    """measure_fn=None 経路の既定 closure が contract.clocks_per_us / contract.numactl を
    measure_point に渡す (CLK/NUMA の p2_2 直 import 除去, F4)。"""
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    contract = ec.lookup(ENV_TAG)
    seen = {}

    def spy_measure_point(binary, records, threads, clocks_per_us, **kw):
        use_perf = kw.get("use_perf", True)
        seen["clocks_per_us"] = clocks_per_us
        seen["numactl"] = kw.get("numactl")
        seen["use_perf"] = use_perf
        seen["holdout_observation_admission"] = kw.get(
            "holdout_observation_admission"
        )
        return _FakeScalePoint(
            throughputs=[1000.0] * 5, notes=[],
            run_cmd=_shape_faithful_run_cmd(
                binary, records, threads, kw["workload"], use_perf=use_perf,
            ),
        )

    fake_build = _make_fake_build(tmp_path / "bin")
    with mock.patch.object(s8b_floor_campaign.buildcache, "build_v2", fake_build), \
             mock.patch.object(s8b_floor_campaign, "measure_point", spy_measure_point):
        _private_run_campaign(
            protocol, _verified_freeze(freeze), out_root=tmp_path / "out", mode="pilot",
            measure_fn=None, probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            perf_preflight_fn=lambda **_kwargs: _perf_receipt(),
            now_fn=lambda: _FIXED_NOW, monotonic_fn=lambda: 0.0,
            durable_root_policy=_durable_policy(tmp_path / "out"),
        )
    assert seen["clocks_per_us"] == contract.clocks_per_us
    assert seen["numactl"] == list(contract.numactl)
    assert seen["use_perf"] is True
    assert seen["holdout_observation_admission"] is not None
    assert seen["holdout_observation_admission"].permitted_run_once_calls == 5


def test_measure_fn_default_passes_use_perf_false_only_for_unavailable_pilot(
        tmp_path):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    seen = []

    def spy_measure_point(binary, records, threads, clocks_per_us, **kwargs):
        use_perf = kwargs.get("use_perf", True)
        seen.append(use_perf)
        return _FakeScalePoint(
            throughputs=[1000.0] * 5, notes=[],
            run_cmd=_shape_faithful_run_cmd(
                binary, records, threads, kwargs["workload"], use_perf=use_perf,
            ),
        )

    fake_build = _make_fake_build(tmp_path / "bin")
    with mock.patch.object(s8b_floor_campaign.buildcache, "build_v2", fake_build), \
             mock.patch.object(s8b_floor_campaign, "measure_point", spy_measure_point):
        outcome = _private_run_campaign(
            protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
            mode="pilot", measure_fn=None, probe_fn=lambda: (1, "", ""),
            prepare_fn=_fake_prepare,
            perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
            now_fn=lambda: _FIXED_NOW, monotonic_fn=lambda: 0.0,
            durable_root_policy=_durable_policy(tmp_path / "out"),
        )
    assert outcome["status"] == "completed"
    assert seen and set(seen) == {False}


@pytest.mark.parametrize("mutation", ["clean", "nonzero_rc", "missing_cycles", "no_perf"])
def test_rep_integrity_positive_control_default_measure_point(tmp_path, monkeypatch, mutation):
    """M1/M2/P3: default closure で中央 101 の資格だけを機械証跡から決める。"""
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    real_measure_point = calibrator_runner.measure_point
    raw_tps = [100, 100, 101, 103, 103]
    perf_values = {
        "LLC-load-misses": 11, "LLC-loads": 22,
        "instructions": 33, "cycles": 44,
    }

    def production_measure_point(*args, **kwargs):
        rep = {"index": 0}

        def fake_subprocess(argv, **_run_kwargs):
            index = rep["index"]
            rep["index"] += 1
            lines = []
            for event, value in perf_values.items():
                token = "<not counted>" if (
                    mutation == "missing_cycles" and index == 2 and event == "cycles"
                ) else str(value)
                lines.append(f"{token},,{event},0,100.00,,")
            if "-o" in argv:
                Path(argv[argv.index("-o") + 1]).write_text(
                    "\n".join(lines) + "\n", encoding="utf-8",
                )
            stdout = (
                "actual_extime:\t1\nabort_counts_:\t1\ncommit_counts_:\t9\n"
                "maxrss:\t100 kB\nlatency[ns]:\t10\n"
                f"throughput[tps]:\t{raw_tps[index]}\n"
            )
            return SimpleNamespace(
                returncode=7 if mutation == "nonzero_rc" and index == 2 else 0,
                stdout=stdout, stderr="",
            )

        return real_measure_point(*args, **kwargs, subprocess_runner=fake_subprocess)

    fake_build = _make_fake_build(tmp_path / "bin")
    monkeypatch.setattr(s8b_floor_campaign, "measure_point", production_measure_point)
    monkeypatch.setattr(s8b_floor_campaign.buildcache, "build_v2", fake_build)
    outcome = _private_run_campaign(
        protocol, _verified_freeze(freeze), out_root=tmp_path / "out", mode="pilot",
        measure_fn=None, probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(
            available=(mutation != "no_perf")
        ),
        now_fn=lambda: _FIXED_NOW, monotonic_fn=lambda: 0.0,
        durable_root_policy=_durable_policy(tmp_path / "out"),
    )
    session = outcome["result"]["sessions"][0]
    journal_session = next(
        row for row in _read_journal_lines(Path(outcome["run_dir"]) / "journal.jsonl")
        if row.get("event") == "session"
    )
    assert journal_session["rep_observations"] == session["rep_observations"]
    assert journal_session["rep_integrity_failures"] == session["rep_integrity_failures"]
    assert [row["returncode"] for row in session["rep_observations"]] == (
        [0, 0, 7, 0, 0] if mutation == "nonzero_rc" else [0, 0, 0, 0, 0]
    )
    assert session["rep_observations"][0]["perf_raw"] == (
        {event: None for event in perf_values} if mutation == "no_perf" else perf_values
    )
    if mutation in {"clean", "no_perf"}:
        assert session["throughputs"] == [100, 100, 101, 103, 103]
        assert session["rep_integrity_failures"] == 0
        assert session["session_median"] == 101
        assert session["valid"] is True
        assert 101 in outcome["result"]["cells"][session["cell_id"]]["medians"]
        if mutation == "no_perf":
            assert [row["counter_status"] for row in session["rep_observations"]] == [
                "not_required", "not_required", "not_required", "not_required",
                "not_required",
            ]
    else:
        assert session["throughputs"] == [100, 100, 103, 103]
        assert session["rep_integrity_failures"] == 1
        assert session["session_median"] is None
        assert session["valid"] is False
        assert session["exclusion_class"] == "rep_integrity_failure"
        assert 101 not in outcome["result"]["cells"][session["cell_id"]]["medians"]


@pytest.mark.parametrize("missing_event", [
    "LLC-load-misses", "LLC-loads", "instructions", "cycles",
])
def test_rep_integrity_missing_each_perf_event_excludes_session(missing_event):
    """M4: 4 event のどれか 1 件でも欠ければ中央 rep は資格を失う。"""
    observations = _FakeScalePoint(
        [100, 100, 101, 103, 103], [], "numactl perf -- bench",
    ).rep_observations
    observations[2]["perf_raw"][missing_event] = None
    observations[2]["missing_perf_events"] = [missing_event]
    observations[2]["counter_status"] = "incomplete"
    point = _FakeScalePoint(
        [100, 100, 101, 103, 103], [], "numactl perf -- bench",
        rep_observations=observations,
    )
    projected = s8b_floor_campaign._project_scalepoint(
        point, reps=5, expected_use_perf=True,
    )
    assert projected["rep_integrity_failures"] == 1
    assert projected["throughputs"] == [100, 100, 103, 103]


def test_no_perf_rep_integrity_requires_zero_rc_and_marks_counters_not_required():
    """P1: no-perf の counter は不要だが rc 0 は引き続き必須。"""
    point = _FakeScalePoint(
        [100, 100, 101, 103, 103], [], "numactl bench", use_perf=False,
    )
    projected = s8b_floor_campaign._project_scalepoint(
        point, reps=5, expected_use_perf=False,
    )
    assert projected["rep_integrity_failures"] == 0
    assert projected["throughputs"] == [100, 100, 101, 103, 103]
    assert [row["counter_status"] for row in projected["rep_observations"]] == [
        "not_required", "not_required", "not_required", "not_required", "not_required",
    ]
    projected["rep_observations"][2]["returncode"] = 9
    point.rep_observations = projected["rep_observations"]
    rejected = s8b_floor_campaign._project_scalepoint(
        point, reps=5, expected_use_perf=False,
    )
    assert rejected["rep_integrity_failures"] == 1
    assert rejected["throughputs"] == [100, 100, 103, 103]


def test_exec_and_integrity_failures_are_derived_as_distinct_counts():
    """M3/M4: notes でなく flag を読み、nonzero rc を execution へ混ぜない。"""
    notes_only = _FakeScalePoint(
        [100, 101, 102, 103, 104], ["5/5 reps failed to execute"],
        "numactl bench", use_perf=False,
    )
    notes_projection = s8b_floor_campaign._project_scalepoint(
        notes_only, reps=5, expected_use_perf=False,
    )
    assert notes_projection["exec_failures"] == 0
    assert notes_projection["rep_integrity_failures"] == 0

    observations = copy.deepcopy(notes_only.rep_observations)
    observations[2].update({
        "returncode": None,
        "execution_failure": True,
        "throughput": None,
    })
    flag_only = _FakeScalePoint(
        [100, 101, 103, 104], [], "numactl bench", use_perf=False,
        rep_observations=observations,
    )
    flag_projection = s8b_floor_campaign._project_scalepoint(
        flag_only, reps=5, expected_use_perf=False,
    )
    assert flag_projection["exec_failures"] == 1
    assert flag_projection["rep_integrity_failures"] == 1
    assert flag_projection["throughputs"] == [100, 101, 103, 104]

    nonzero_observations = copy.deepcopy(notes_only.rep_observations)
    nonzero_observations[2]["returncode"] = 7
    nonzero = _FakeScalePoint(
        [100, 101, 102, 103, 104], [], "numactl bench", use_perf=False,
        rep_observations=nonzero_observations,
    )
    nonzero_projection = s8b_floor_campaign._project_scalepoint(
        nonzero, reps=5, expected_use_perf=False,
    )
    assert nonzero_projection["exec_failures"] == 0
    assert nonzero_projection["rep_integrity_failures"] == 1
    assert nonzero_projection["throughputs"] == [100, 101, 103, 104]


def test_execution_failure_true_alone_prevents_complete_rep_projection():
    """M6: rc/perf が完備でも捕捉例外 rep は complete にしない。"""
    perf_raw = {
        event: index + 1
        for index, event in enumerate(s8b_floor_stats.PERF_EVENTS)
    }
    observation = {
        "rep_index": 0,
        "returncode": 0,
        "counter_status": "complete",
        "missing_perf_events": [],
        "perf_raw": perf_raw,
        "throughput": None,
        "execution_failure": True,
    }
    point = _FakeScalePoint(
        [], [], "numactl perf -- bench", rep_observations=[observation], reps=1,
    )

    expected_keys = {
        "rep_index", "returncode", "counter_status", "missing_perf_events",
        "perf_raw", "throughput", "execution_failure",
    }
    missing = [
        event for event in s8b_floor_stats.PERF_EVENTS
        if type(perf_raw[event]) is not int or perf_raw[event] < 0
    ]
    derived_status = "complete" if not missing else "incomplete"
    assert set(observation) == expected_keys
    assert type(observation["rep_index"]) is int
    assert observation["rep_index"] == 0
    assert type(observation["returncode"]) is int
    assert observation["returncode"] == 0
    assert observation["counter_status"] == derived_status
    assert observation["missing_perf_events"] == missing
    assert isinstance(perf_raw, Mapping)
    assert set(perf_raw) == set(s8b_floor_stats.PERF_EVENTS)
    assert derived_status in {"complete", "not_required"}
    assert observation["execution_failure"] is True
    assert observation["throughput"] is None

    projected = s8b_floor_campaign._project_scalepoint(
        point, reps=1, expected_use_perf=True,
    )
    assert projected == {
        "throughputs": [],
        "exec_failures": 1,
        "rep_observations": [observation],
        "rep_integrity_failures": 1,
    }

    def project_without_execution_failure_guard(scale_point):
        source_throughputs = list(scale_point.throughputs)
        observations = [dict(row) for row in scale_point.rep_observations]
        observed_tps = [
            row["throughput"] for row in observations
            if row["throughput"] is not None
        ]
        assert observed_tps == source_throughputs

        failures = 0
        qualified_throughputs = []
        for expected_index, row in enumerate(observations):
            row_perf_raw = row["perf_raw"]
            raw_complete = (
                isinstance(row_perf_raw, Mapping)
                and set(row_perf_raw) == set(s8b_floor_stats.PERF_EVENTS)
            )
            row_missing = [
                event for event in s8b_floor_stats.PERF_EVENTS
                if type(row_perf_raw[event]) is not int or row_perf_raw[event] < 0
            ]
            row_status = "complete" if not row_missing else "incomplete"
            complete = (
                set(row) == expected_keys
                and type(row["rep_index"]) is int
                and row["rep_index"] == expected_index
                and type(row["returncode"]) is int
                and row["returncode"] == 0
                and row["counter_status"] == row_status
                and row["missing_perf_events"] == row_missing
                and raw_complete
                and row_status in {"complete", "not_required"}
            )
            if complete:
                if row["throughput"] is not None:
                    qualified_throughputs.append(row["throughput"])
            else:
                failures += 1
        return {
            "throughputs": qualified_throughputs,
            "exec_failures": sum(
                row["execution_failure"] is True for row in observations
            ),
            "rep_integrity_failures": failures,
        }

    assert project_without_execution_failure_guard(point) == {
        "throughputs": [],
        "exec_failures": 1,
        "rep_integrity_failures": 0,
    }


def test_missing_observation_carrier_keeps_execution_failure_unobserved():
    """M5a/M5b: carrier 欠落を False/True/key 欠落のいずれにも捏造しない。"""
    point = SimpleNamespace(
        throughputs=[100, 101, 102, 103, 104],
        notes=["5/5 reps failed to execute"],
        rep_observations=None,
    )
    projection = s8b_floor_campaign._project_scalepoint(
        point, reps=5, expected_use_perf=False,
    )
    assert projection["exec_failures"] == 0
    assert projection["rep_integrity_failures"] == 5
    assert all(
        observation["execution_failure"] is None
        for observation in projection["rep_observations"]
    )


@pytest.mark.parametrize("state,expected_class", [
    ("post_competing", "competing_process"),
    ("launch", "rep_integrity_failure"),
    ("integrity", "rep_integrity_failure"),
])
def test_rep_integrity_precedence_uses_completed_measure_evidence(
        tmp_path, state, expected_class):
    """M7: completed measure の competing/launch は証跡を保ち integrity より優先する。"""
    cell_id = "rr79::stock_common"
    cell = {
        "cell_id": cell_id, "holdout_id": "rr79", "configuration_id": _STOCK,
        "records": 730079, "threads": 17, "workload": _HOLDOUT_SHAPE["rr79"]["ycsb"],
    }
    binary = tmp_path / "bench"
    binary.write_bytes(b"fixture")
    digest = hashlib.sha256(b"fixture").hexdigest()
    observations = _FakeScalePoint(
        [100, 100, 101, 103, 103], [],
        _shape_faithful_run_cmd(binary, cell["records"], cell["threads"], cell["workload"]),
    ).rep_observations
    observations[2]["returncode"] = 7
    notes = ["5/5 reps failed to execute"] if state == "launch" else []
    point = _FakeScalePoint(
        [100, 100, 101, 103, 103], notes,
        _shape_faithful_run_cmd(binary, cell["records"], cell["threads"], cell["workload"]),
        rep_observations=observations,
    )
    probe_calls = {"n": 0}

    def probe():
        probe_calls["n"] += 1
        if state == "post_competing" and probe_calls["n"] % 2 == 0:
            return (0, "777 ycsb_fixture.exe\n", "")
        return (1, "", "")

    protocol = s8b_floor_campaign.validate_protocol(_valid_protocol_dict())
    runner = s8b_floor_campaign._Runner(
        protocol=protocol, contract=ec.lookup(ENV_TAG), cells=[cell],
        cell_by_id={cell_id: cell},
        binaries={cell_id: {"binary": str(binary), "binary_sha256": digest}},
        artifact_binaries={cell_id: {"binary": "output/fixture/bench"}},
        schedule=[], journal_path=tmp_path / f"{state}.jsonl",
        holdout_admissions={cell_id: SimpleNamespace(observation=None)},
        measure_fn=lambda *args: point, probe_fn=probe, sleep_fn=lambda _s: None,
        monotonic_fn=lambda: 0.0, now_fn=lambda: _FIXED_NOW,
        protocol_sha256="p", freeze_sha256="f", manifest_sha256="m",
        perf_preflight=_perf_receipt(), mode="pilot",
        holdout_assert_fn=lambda *_args, **_kwargs: None,
    )
    record = runner._run_session(
        seq=0, round_no=1, cell_id=cell_id, kind="planned",
        retry_ordinal=None, trigger=None,
    )
    assert record["exclusion_class"] == expected_class
    assert record["rep_integrity_failures"] == 1
    if state == "launch":
        assert record["exec_failures"] == 0
    assert len(record["rep_observations"]) == 5
    assert record["valid"] is False
    assert record["session_median"] is None


def test_runner_requires_exact_holdout_admission_mapping(tmp_path):
    cell_id = "rr79::stock_common"
    cell = {
        "cell_id": cell_id, "holdout_id": "rr79", "configuration_id": _STOCK,
        "records": 1, "threads": 1, "workload": _HOLDOUT_SHAPE["rr79"]["ycsb"],
    }
    runner = s8b_floor_campaign._Runner(
        protocol=_valid_protocol_dict(), contract=ec.lookup(ENV_TAG), cells=[cell],
        cell_by_id={cell_id: cell}, binaries={cell_id: {}},
        artifact_binaries={cell_id: {}}, schedule=[],
        journal_path=tmp_path / "journal.jsonl", measure_fn=lambda *_args: None,
        holdout_admissions={}, probe_fn=lambda: (1, "", ""),
        sleep_fn=lambda _seconds: None, monotonic_fn=lambda: 0.0,
        now_fn=lambda: _FIXED_NOW, protocol_sha256="p", freeze_sha256="f",
        manifest_sha256="m", perf_preflight=_perf_receipt(), mode="pilot",
        holdout_assert_fn=lambda *_args, **_kwargs: None,
    )
    with pytest.raises(s8b_floor_campaign.CampaignAbort, match="exactly cover"):
        runner._validate_live_admissions()


def test_rep_integrity_precedes_partial_in_runner_branch_order():
    """M7: partial 分岐を rep integrity より前へ移す変異を構造的に殺す。"""
    runner_class = ast.parse(inspect.getsource(s8b_floor_campaign._Runner)).body[0]
    function = next(
        node for node in runner_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "_run_session"
    )
    precedence = next(
        node for node in function.body
        if isinstance(node, ast.If) and "probe_after" in ast.unparse(node.test)
    )
    tests = []
    branch = precedence
    while isinstance(branch, ast.If):
        tests.append(ast.unparse(branch.test))
        branch = branch.orelse[0] if len(branch.orelse) == 1 else None
    integrity_index = next(
        i for i, test in enumerate(tests) if "rep_integrity_failures" in test
    )
    assert all(
        "_REASON_PARTIAL" not in test and "derived_reason is not None" not in test
        for test in tests[:integrity_index]
    )


def test_floor_default_durable_policy_rejects_external_output_without_side_effects(tmp_path):
    freeze = _freeze_document()
    out_root = tmp_path / "outside-default-approval"
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="durable output root"):
        _private_run_campaign(
            _protocol(freeze_sha=_freeze_sha(freeze)), _verified_freeze(freeze),
            out_root=out_root, mode="pilot", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW,
            build_fn=_make_fake_build(tmp_path / "bin"),
        )
    assert not out_root.exists()


def test_floor_journal_manifest_and_binary_store_open_through_capability(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    out_root = tmp_path / "capability-out"
    calls = []
    real_open = s8b_floor_campaign.open_with_write_capability

    def open_spy(capability, path, mode):
        calls.append((Path(path).name, mode, Path(path)))
        return real_open(capability, path, mode)

    monkeypatch.setattr(s8b_floor_campaign, "open_with_write_capability", open_spy)
    _run_campaign(
        _protocol(freeze_sha=_freeze_sha(freeze)), _verified_freeze(freeze),
        out_root=out_root, build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
        probe_fn=lambda: (1, "", ""),
    )
    assert any(name == "journal.jsonl" and mode == "ab" for name, mode, _ in calls)
    assert any(name.startswith(".") and ".tmp." in name and mode == "xb"
               for name, mode, _ in calls)
    assert any(name.endswith("manifest.json.pending") and mode == "xb"
               for name, mode, _ in calls)
    assert all(path.is_relative_to(out_root) for _, _, path in calls)


# =========================================================================== #
# 5. session 有効性 → retry → floor 未確定の伝播                                #
# =========================================================================== #

def test_partial_reps_invalidates_session_and_burns_retry_then_nulls_pair(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)

    flaky = "rr79::sort_best"
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid],
                                  partial_for={flaky})
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "nonstock",
                            build_root=tmp_path / "nonstock-bin",
                            measure_fn=measure_fn, probe_fn=lambda: (1, "", ""))
    result = outcome["result"]

    flaky_sessions = [s for s in result["sessions"] if s["cell_id"] == flaky]
    # 8 planned (全て partial・無効) + campaign 通算 2 retry (round1 末尾で消化) = 10 本。
    assert len(flaky_sessions) == 8 + 2
    assert all(not s["valid"] for s in flaky_sessions)
    assert all(s["excluded_reason"] == "nonfinite_or_partial_output" for s in flaky_sessions)
    retries = [s for s in flaky_sessions if s["retry"]]
    assert len(retries) == 2
    assert sorted(s["retry_ordinal"] for s in retries) == [1, 2]

    assert result["cells"][flaky]["valid"] is False
    assert result["cells"][flaky]["n_valid"] == 0
    assert result["floors"]["rr79"]["pairs"]["sort_best"] is None
    assert result["floors"]["rr79"]["pairs"]["p2_2_flag_opt"] is not None
    assert result["floors"]["rr79"]["scale_ref"] is not None
    assert result["floors"]["rr79"]["scalar_alt"] is None  # null pair が veto
    for cfg, floor in result["floors"]["rr23"]["pairs"].items():
        assert floor is not None, cfg
    assert result["floors"]["rr23"]["scalar_alt"] is not None


def test_stock_flaky_nulls_entire_holdout_including_scale_ref(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    stock_flaky = "rr79::stock_common"
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid],
                                  partial_for={stock_flaky})
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "stock",
                            build_root=tmp_path / "stock-bin",
                            measure_fn=measure_fn, probe_fn=lambda: (1, "", ""))
    result = outcome["result"]
    assert result["cells"][stock_flaky]["valid"] is False
    for cfg, floor in result["floors"]["rr79"]["pairs"].items():
        assert floor is None, cfg
    assert result["floors"]["rr79"]["scale_ref"] is None
    assert result["floors"]["rr79"]["scalar_alt"] is None
    for cfg, floor in result["floors"]["rr23"]["pairs"].items():
        assert floor is not None, cfg  # 無関係 holdout は無傷


def test_retry_sequence_is_metamorphic_to_other_cells_values(tmp_path):
    """他セルの性能値を変えても、失敗セルの retry 列 (attempt_id/ordinal) は不変 (β-4)。"""
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    flaky = "rr23::ident_all"

    def run(scale):
        def value_fn(cid):
            return _BASE_TPS[cid] * (scale if cid != flaky else 1.0)
        measure_fn = _make_measure_fn(reps=5, value_fn=value_fn, partial_for={flaky})
        outcome = _run_campaign(protocol, verified, out_root=tmp_path / f"run{scale}",
                                build_root=tmp_path / f"bin{scale}",
                                measure_fn=measure_fn, probe_fn=lambda: (1, "", ""))
        return outcome["result"]

    ra = run(1.0)
    rb = run(2.0)  # 他セルの性能値だけ 2 倍

    def flaky_attempts(result):
        return [(s["kind"], s["retry_ordinal"], s["attempt_id"], s["valid"],
                 s["excluded_reason"]) for s in result["sessions"] if s["cell_id"] == flaky]

    assert flaky_attempts(ra) == flaky_attempts(rb)  # retry 列は不変
    # 一方で他セルの medians は実際に変わっている (metamorphic の前提が空回りでない証拠)。
    other = "rr23::system_gate"
    assert ra["cells"][other]["m"] != rb["cells"][other]["m"]


# =========================================================================== #
# 6. probe 臨界区間 (競合 → 無効 + 生出力 / 実行不能 → abort / post-probe finally) #
# =========================================================================== #

def test_probe_competing_invalidates_session_with_raw_stdout_in_journal(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    conflicting = "999 ycsb_fixture.exe -thread_num=1\n"

    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "out",
                            build_root=tmp_path / "bin", measure_fn=measure_fn,
                            probe_fn=lambda: (0, conflicting, ""))
    assert measure_fn.calls == []  # 競合検知は measure の前でスキップ
    result = outcome["result"]
    assert all(not s["valid"] for s in result["sessions"])
    assert all(s["excluded_reason"] == "competing_process" for s in result["sessions"])
    sample = result["sessions"][0]
    assert sample["probe_before"]["stdout"] == conflicting
    assert sample["probe_before"]["competing"]


def test_post_probe_runs_on_launch_error_and_competing_takes_precedence(tmp_path):
    """measure が例外 (全 rep 起動不能) の経路でも post-probe を実行し、post-probe 競合が
    launch_failure より優先される (β-7 の precedence)。"""
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    launch_fail_cell = "rr79::system_gate"

    # pre-probe は常に競合なし (rc=1)、post-probe (2 回目) は競合 (rc=0) を返す。
    calls = {"n": 0}

    def probe_fn():
        calls["n"] += 1
        if calls["n"] % 2 == 1:
            return (1, "", "")           # pre-probe: 競合なし
        return (0, "777 ycsb_fixture.exe\n", "")  # post-probe: 競合

    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid],
                                  raise_for={launch_fail_cell})
    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "out",
                            build_root=tmp_path / "bin", measure_fn=measure_fn,
                            probe_fn=probe_fn)
    result = outcome["result"]
    # 全 planned は post-probe 競合 → competing_process (launch エラーの cell も competing が優先)。
    for s in result["sessions"]:
        assert s["excluded_reason"] == "competing_process"
        assert s["probe_after"] is not None  # 例外経路でも post-probe が走った


@pytest.mark.parametrize("probe_fn, match", [
    # rc>1 (pgrep エラー)・rc==1+付随出力・rc==0+空・rc==1+stderr 非空 (BusyBox 罠) は
    # いずれも共有分類器が CompetingBenchProbeError を投げ、floor が CampaignAbort へ
    # 翻訳する (fail-closed)。stderr 経路は floor が seam で stderr を握り潰していた
    # C4-5 の穴を塞いだ回帰: (rc, stdout, stderr) 3-tuple で実 stderr が分類器へ届く。
    (lambda: (2, "unexpected rc", ""), "確定できない"),
    (lambda: (1, "1234 ycsb_fixture.exe", ""), "確定できない"),   # rc==1+出力 → abort
    (lambda: (0, "", ""), "確定できない"),                        # rc==0+空 → abort
    (lambda: (1, "", "pgrep: unrecognized option '-af'\n"), "確定できない"),  # BusyBox 罠 → abort
    (lambda: (_ for _ in ()).throw(OSError("pgrep 不在を模す")), "OSError"),
    (lambda: (_ for _ in ()).throw(subprocess.TimeoutExpired("pgrep", 120)),
     "有限時間"),
])
def test_probe_unexecutable_or_inconsistent_aborts_campaign(tmp_path, probe_fn, match):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])

    def probe_wrapper():
        return probe_fn()

    out_root = tmp_path / "out"
    with pytest.raises(s8b_floor_campaign.CampaignAbort, match=match):
        _run_campaign(protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                      measure_fn=measure_fn, probe_fn=probe_wrapper)

    run_dir = _only_run_dir(out_root)
    journal = _read_journal_lines(run_dir / "journal.jsonl")
    terminal = [r for r in journal if r.get("event") == "terminal"]
    assert terminal and terminal[-1]["status"] == "aborted"
    assert not (run_dir / "result.json").exists()


def test_default_probe_uses_frozen_verify_timeout(monkeypatch):
    seen = {}

    def run_spy(argv, **kwargs):
        seen["argv"] = argv
        seen["timeout"] = kwargs.get("timeout")
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    monkeypatch.setattr(s8b_floor_campaign.subprocess, "run", run_spy)
    assert s8b_floor_campaign._default_probe_fn() == (1, "", "")
    assert seen == {
        "argv": s8b_floor_campaign._PROBE_ARGV,
        "timeout": s8b_floor_campaign._FLOOR_VERIFY_CAP_PER_ATTEMPT_S,
    }


def test_probe_unparseable_pid_line_invalidates_session_not_abort(tmp_path):
    """rc==0 で先頭 token が PID 形でない行は、共有分類器が fails-closed で競合側に
    残す (素性不明を non-competing 扱いにしない)。floor では abort ではなく
    competing_process による session 無効化になる (共有実装の parse 意味論を継承)。"""
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])

    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "out",
                            build_root=tmp_path / "bin", measure_fn=measure_fn,
                            probe_fn=lambda: (0, "not-a-pid ycsb_fixture.exe\n", ""))
    assert measure_fn.calls == []           # pre-probe 競合検知で measure スキップ
    result = outcome["result"]
    assert all(not s["valid"] for s in result["sessions"])
    assert all(s["excluded_reason"] == "competing_process" for s in result["sessions"])


def test_probe_own_descendant_pid_detected_as_competing_b2(tmp_path):
    """B-2 回帰: floor 側でも子孫除外への逆戻りを検出する。自プロセス (= pytest プロセス)
    の実子 PID を probe が返しても、own-PID-only 縮小の下では競合として検出され session が
    無効化される。子孫除外へ戻ると実子が黙って落ち、session が有効になってしまう。"""
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])

    child = subprocess.Popen(["sleep", "30"])   # 自プロセスの実子 (子孫) を 1 つ起こす
    try:
        line = f"{child.pid} /out/s8b-build-cache/gen0/ycsb_child.exe\n"
        outcome = _run_campaign(protocol, verified, out_root=tmp_path / "out",
                                build_root=tmp_path / "bin", measure_fn=measure_fn,
                                probe_fn=lambda: (0, line, ""))
    finally:
        child.kill()
        child.wait(timeout=180)
    assert measure_fn.calls == []           # 実子が競合検知され measure スキップ
    result = outcome["result"]
    assert all(s["excluded_reason"] == "competing_process" for s in result["sessions"])
    sample = result["sessions"][0]
    assert str(child.pid) in sample["probe_before"]["stdout"]
    assert sample["probe_before"]["competing"]   # 実子が競合として残った


def test_probe_classifier_own_pid_kwarg_is_injectable_and_fail_closed():
    stdout = "4242 self.exe\n5252 other.exe\n"
    assert s8b_floor_campaign.classify_competing_probe(
        0, stdout, "", ["pgrep"], own_pid=4242) == ["5252 other.exe"]
    assert s8b_floor_campaign.classify_competing_probe(
        0, stdout, "", ["pgrep"], own_pid=5252) == ["4242 self.exe"]
    with pytest.raises(s8b_floor_campaign.CompetingBenchProbeError):
        s8b_floor_campaign.classify_competing_probe(
            0, stdout, "", ["pgrep"], own_pid=0)


# =========================================================================== #
# 7. performance_anomaly (session 内 CV>10%) / machine_anomaly (セル間 CV>15%)   #
# =========================================================================== #

def test_performance_anomaly_invalidates_session_and_nulls_pair(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    anomaly = "rr79::ident_all"

    def reps_fn(cid):
        if cid == anomaly:
            return [80.0, 90.0, 100.0, 110.0, 120.0]  # CV=sqrt(250)/100≈15.8% > 10%
        return [_BASE_TPS[cid]] * 5

    measure_fn = _make_measure_fn(reps=5, value_fn=None, reps_fn=reps_fn)
    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "out",
                            build_root=tmp_path / "bin", measure_fn=measure_fn,
                            probe_fn=lambda: (1, "", ""))
    result = outcome["result"]
    anomaly_sessions = [s for s in result["sessions"] if s["cell_id"] == anomaly]
    assert all(s["excluded_reason"] == "performance_anomaly" for s in anomaly_sessions)
    assert all(not s["valid"] for s in anomaly_sessions)
    assert result["cells"][anomaly]["valid"] is False
    assert result["floors"]["rr79"]["pairs"]["ident_all"] is None


def test_machine_anomaly_valid_cell_but_pair_null(tmp_path):
    """セル間 CV>15% のセルは統計的には有効 (n_valid=8) だが当該 pair は machine_anomaly で null。"""
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    noisy = "rr23::sort_best"
    per_cell = {}

    def reps_fn(cid):
        if cid == noisy:
            per_cell[cid] = per_cell.get(cid, 0) + 1
            # 8 session の median を [100×4, 150×4] にしてセル間 CV≈21% > 15%。
            value = 100.0 if per_cell[cid] <= 4 else 150.0
            return [value] * 5  # session 内は一定 (performance_anomaly ではない)
        return [_BASE_TPS[cid]] * 5

    measure_fn = _make_measure_fn(reps=5, value_fn=None, reps_fn=reps_fn)
    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "out",
                            build_root=tmp_path / "bin", measure_fn=measure_fn,
                            probe_fn=lambda: (1, "", ""))
    result = outcome["result"]
    assert result["cells"][noisy]["valid"] is True       # 8 session 全て有効
    assert result["cells"][noisy]["n_valid"] == 8
    assert result["floors"]["rr23"]["pairs"]["sort_best"] is None  # machine_anomaly で null
    diag = result["floors"]["rr23"]["diagnostics"]
    assert noisy in diag["machine_anomaly_cells"]


# =========================================================================== #
# 8. create-only + journal append + 冪等 finalization (β-11)                    #
# =========================================================================== #

def test_create_only_rejects_overwrite_journal_appends(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    out_root = tmp_path / "out"

    outcome = _run_campaign(protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                            measure_fn=measure_fn, probe_fn=lambda: (1, "", ""))
    run_dir = Path(outcome["run_dir"])
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "result.json").exists()
    assert (run_dir / "result.md").exists()

    # 同一 protocol/now_fn で fresh 再実行 → 同一 run_dir 衝突で拒否。
    measure_fn2 = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="既に存在する"):
        _run_campaign(protocol, verified, out_root=out_root, build_root=tmp_path / "bin2",
                      measure_fn=measure_fn2, probe_fn=lambda: (1, "", ""))

    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="既に存在するため上書きしない"):
        s8b_floor_campaign._write_create_only_json(run_dir / "result.json", {"x": 1})

    journal_path = run_dir / "journal.jsonl"
    before = journal_path.read_text(encoding="utf-8")
    s8b_floor_campaign._journal_append(journal_path, {"event": "test-append-marker"})
    after = journal_path.read_text(encoding="utf-8")
    assert after.startswith(before)
    assert len(after) > len(before)


def test_strict_jsonl_rejects_blank_record(tmp_path):
    journal = tmp_path / "journal.jsonl"
    journal.write_text('{"event":"x"}\n\n', encoding="utf-8")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="strict JSONL"):
        s8b_floor_campaign._read_journal(journal)


def test_manifest_atomic_publish_never_exposes_partial_destination(tmp_path, monkeypatch):
    destination = tmp_path / "run" / "manifest.json"
    destination.parent.mkdir()

    def crash_link(_source, _destination):
        raise _SimulatedCrash("manifest publish crash")

    monkeypatch.setattr(s8b_floor_campaign.os, "link", crash_link)
    with pytest.raises(_SimulatedCrash, match="manifest publish"):
        s8b_floor_campaign._atomic_create_only_json(destination, {"sealed": True})
    assert not destination.exists()
    pending = tmp_path / f".{destination.parent.name}.{destination.name}.pending"
    assert pending.is_file() and pending.stat().st_size > 0


def test_idempotent_finalization_after_result_json_crash(tmp_path):
    """completed terminal 後・publish 前 crash を模し、resume は publish だけ完遂する。"""
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                            measure_fn=measure_fn, probe_fn=lambda: (1, "", ""))
    run_dir = Path(outcome["run_dir"])
    original_result = (run_dir / "result.json").read_bytes()

    # crash 状態を再現: completed terminal は最終のまま、publish 済み files だけを消す。
    (run_dir / "result.json").unlink()
    (run_dir / "result.md").unlink()
    journal_path = run_dir / "journal.jsonl"

    # resume: M-finalize-pending なので runner/resume-start を通らず publish のみ補完。
    measure_fn2 = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    outcome2 = _run_campaign(protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                             resume_dir=run_dir, measure_fn=measure_fn2,
                             probe_fn=lambda: (1, "", ""))
    assert outcome2["status"] == "completed"
    assert measure_fn2.calls == []  # 全 session 済みなので新規計測なし
    assert (run_dir / "result.json").read_bytes() == original_result
    assert (run_dir / "result.md").exists()
    journal = _read_journal_lines(journal_path)
    assert journal[-1] == {"event": "terminal", "status": "completed"}
    assert not any(r.get("event") == "resume-start" for r in journal)


def test_official_finalize_pending_resume_reassembles_refreeze_ineligible(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    fake_build = _make_fake_build(tmp_path / "bin")
    common = {
        "out_root": out_root,
        "mode": "official",
        "probe_fn": lambda: (1, "", ""),
        "sleep_fn": lambda _seconds: None,
        "monotonic_fn": lambda: 0.0,
        "prepare_fn": _fake_prepare,
        "now_fn": lambda: _FIXED_NOW,
        "durable_root_policy": _durable_policy(out_root),
    }

    with _official_test_seam(monkeypatch) as scoped:
        scoped.setattr(s8b_floor_campaign.buildcache, "build_v2", fake_build)
        scoped.setattr(
            s8b_floor_campaign, "_bind_current_toolchain",
            _fixture_toolchain_binding,
        )
        scoped.setattr(
            s8b_floor_campaign.source_digest, "resolve_evidence",
            _fixture_source_evidence,
        )
        original_publish = s8b_floor_campaign._publish_finalize_files
        scoped.setattr(
            s8b_floor_campaign, "_publish_finalize_files",
            lambda *_args: (_ for _ in ()).throw(
                _SimulatedCrash("official terminal-after")),
        )
        with pytest.raises(_SimulatedCrash, match="official terminal-after"):
            _private_run_campaign(
                protocol, verified,
                measure_fn=_make_measure_fn(
                    reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
                _floor_preflight_fn=_fixture_floor_preflight,
                **common,
            )
        scoped.setattr(
            s8b_floor_campaign, "_publish_finalize_files", original_publish,
        )
        run_dir = _only_run_dir(out_root)
        resume_measure = _make_measure_fn(
            reps=5, value_fn=lambda cid: _BASE_TPS[cid])
        outcome = _private_run_campaign(
            protocol, verified, resume_dir=run_dir,
            measure_fn=resume_measure, **common,
        )

    assert outcome["status"] == "completed"
    assert outcome["result"]["eligible_for_refreeze"] is False
    assert resume_measure.calls == []


def test_result_json_stays_hidden_when_publish_stops_after_markdown(
        tmp_path, monkeypatch):
    """Default-policy True staging の途中停止でも権威 result を露出しない。"""
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    fake_build = _make_fake_build(tmp_path / "bin")
    real_derive = s8b_floor_campaign._derive_refreeze_eligibility
    real_publish = s8b_floor_campaign._publish_staged_create_only
    published = []
    assert real_derive(
        mode="official", resume_dir=None, nondefault_seams=frozenset(),
    ) is True

    def stop_before_authoritative_result(pending, destination, payload):
        destination = Path(destination)
        if destination.name == "result.json":
            raise _SimulatedCrash("between finalize publishes")
        real_publish(pending, destination, payload)
        if destination.name == "result.md":
            published.append(destination.name)

    with _official_test_seam(monkeypatch) as scoped:
        scoped.setattr(s8b_floor_campaign.buildcache, "build_v2", fake_build)
        scoped.setattr(
            s8b_floor_campaign, "_bind_current_toolchain",
            _fixture_toolchain_binding,
        )
        scoped.setattr(
            s8b_floor_campaign.source_digest, "resolve_evidence",
            _fixture_source_evidence,
        )
        scoped.setattr(
            s8b_floor_campaign, "_derive_refreeze_eligibility",
            # Full-run fixture seams are non-default only to avoid real measurement.
            # Project the already-asserted fresh/default policy value into staged bytes.
            lambda **_kwargs: True,
        )
        scoped.setattr(
            s8b_floor_campaign, "_nondefault_campaign_seams",
            lambda **_kwargs: frozenset(),
        )
        scoped.setattr(
            s8b_floor_campaign, "_publish_staged_create_only",
            stop_before_authoritative_result,
        )
        with pytest.raises(_SimulatedCrash, match="between finalize publishes"):
            _private_run_campaign(
                protocol, verified, out_root=out_root, mode="official",
                measure_fn=_make_measure_fn(
                    reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
                probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
                monotonic_fn=lambda: 0.0, prepare_fn=_fake_prepare,
                now_fn=lambda: _FIXED_NOW,
                durable_root_policy=_durable_policy(out_root),
                _floor_preflight_fn=_fixture_floor_preflight,
            )

        run_dir = _only_run_dir(out_root)
        assert published == ["result.md"]
        assert (run_dir / "result.md").is_file()
        assert not (run_dir / "result.json").exists()
        staged_true = json.loads((run_dir / ".result.json.pending").read_bytes())
        assert staged_true["eligible_for_refreeze"] is True

        scoped.setattr(
            s8b_floor_campaign, "_derive_refreeze_eligibility", real_derive,
        )
        scoped.setattr(
            s8b_floor_campaign, "_publish_staged_create_only", real_publish,
        )
        with pytest.raises(
                s8b_floor_campaign.FloorCampaignError,
                match="staged bytes が再計算と不一致"):
            _private_run_campaign(
                protocol, verified, out_root=out_root, mode="official",
                resume_dir=run_dir, measure_fn=_forbid_measure,
                probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
                monotonic_fn=lambda: 0.0, prepare_fn=_fake_prepare,
                now_fn=lambda: _FIXED_NOW,
                durable_root_policy=_durable_policy(out_root),
            )

    assert not (run_dir / "result.json").exists()


def test_finalize_pending_resume_rejects_tampered_staged_result(tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with monkeypatch.context() as scoped:
        scoped.setattr(
            s8b_floor_campaign, "_publish_finalize_files",
            lambda *_args: (_ for _ in ()).throw(_SimulatedCrash("terminal-after")),
        )
        with pytest.raises(_SimulatedCrash, match="terminal-after"):
            _run_campaign(
                protocol, _verified_freeze(freeze), out_root=out_root,
                build_root=tmp_path / "bin",
                measure_fn=_make_measure_fn(
                    reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
                probe_fn=lambda: (1, "", ""),
            )
    run_dir = _only_run_dir(out_root)
    pending = run_dir / ".result.json.pending"
    pending.write_bytes(pending.read_bytes() + b"tampered")

    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="staged bytes が再計算と不一致"):
        _run_campaign(
            protocol, _verified_freeze(freeze), out_root=out_root,
            build_root=tmp_path / "bin", resume_dir=run_dir,
            measure_fn=_forbid_measure, probe_fn=lambda: (1, "", ""),
        )


def test_finalize_pending_resume_rejects_tampered_published_result(tmp_path):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    outcome = _run_campaign(
        protocol, _verified_freeze(freeze), out_root=out_root,
        build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
        probe_fn=lambda: (1, "", ""),
    )
    run_dir = Path(outcome["run_dir"])
    (run_dir / "result.md").unlink()
    result_path = run_dir / "result.json"
    result_path.write_bytes(result_path.read_bytes() + b"tampered")

    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="publish 済み bytes が再計算と不一致"):
        _run_campaign(
            protocol, _verified_freeze(freeze), out_root=out_root,
            build_root=tmp_path / "bin", resume_dir=run_dir,
            measure_fn=_forbid_measure, probe_fn=lambda: (1, "", ""),
        )


def test_finalize_completed_terminal_recheck_fires_when_called_without_classify(tmp_path):
    journal_path = tmp_path / "journal.jsonl"
    s8b_floor_campaign._journal_append(
        journal_path, {"event": "terminal", "status": "completed"})
    s8b_floor_campaign._journal_append(journal_path, {"event": "late"})
    staged = (
        tmp_path / ".result.json.pending", b"{}\n",
        tmp_path / ".result.md.pending", b"result\n",
    )
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="finalize-pending: completed terminal が一意・最終でない"):
        s8b_floor_campaign._finalize(
            tmp_path, staged, journal_path, terminal_already_completed=True)


@pytest.mark.parametrize("crash_point", [
    "result-write-after", "self-check-after", "terminal-before", "terminal-after",
])
def test_two_phase_finalize_crash_injection_recovers_at_all_four_boundaries(
        tmp_path, monkeypatch, crash_point):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"

    with monkeypatch.context() as scoped:
        if crash_point == "result-write-after":
            original = s8b_floor_campaign._stage_bytes

            def crash_after_result(path, payload, **kwargs):
                original(path, payload, **kwargs)
                if Path(path).name == ".result.json.pending":
                    raise _SimulatedCrash(crash_point)

            scoped.setattr(s8b_floor_campaign, "_stage_bytes", crash_after_result)
        elif crash_point == "self-check-after":
            original = (
                s8b_floor_campaign.s8b_floor_stats
                .verify_floor_artifact_with_live_admission
            )

            def crash_after_self_check(*args, **kwargs):
                problems = original(*args, **kwargs)
                assert problems == []
                raise _SimulatedCrash(crash_point)

            scoped.setattr(
                s8b_floor_campaign.s8b_floor_stats,
                "verify_floor_artifact_with_live_admission",
                crash_after_self_check,
            )
        elif crash_point == "terminal-before":
                scoped.setattr(
                    s8b_floor_campaign, "_append_completed_terminal",
                    lambda _path, **_kwargs: (_ for _ in ()).throw(
                        _SimulatedCrash(crash_point)),
                )
        else:
            scoped.setattr(
                s8b_floor_campaign, "_publish_finalize_files",
                lambda *_args: (_ for _ in ()).throw(_SimulatedCrash(crash_point)),
            )
        with pytest.raises(_SimulatedCrash, match=crash_point):
            _run_campaign(
                protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                measure_fn=_make_measure_fn(
                    reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
                probe_fn=lambda: (1, "", ""),
            )

    run_dir = _only_run_dir(out_root)
    assert not (run_dir / "result.json").exists()
    assert not (run_dir / "result.md").exists()
    before = _read_journal_lines(run_dir / "journal.jsonl")
    has_terminal = any(r.get("event") == "terminal" for r in before)
    assert has_terminal is (crash_point == "terminal-after")

    resume_measure = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(
        protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
        measure_fn=resume_measure, probe_fn=lambda: (1, "", ""), resume_dir=run_dir,
    )
    assert outcome["status"] == "completed"
    assert resume_measure.calls == []
    assert outcome["result"]["eligible_for_refreeze"] is False
    journal = _read_journal_lines(run_dir / "journal.jsonl")
    terminals = [r for r in journal if r.get("event") == "terminal"]
    assert terminals == [{"event": "terminal", "status": "completed"}]
    assert journal[-1] == terminals[0]
    assert any(r.get("event") == "resume-start" for r in journal) is (
        crash_point != "terminal-after")


# =========================================================================== #
# 9. resume: forward-only + hash pin + manifest.schedule 権威 + 状態機械         #
# =========================================================================== #

class _SimulatedCrash(Exception):
    """resume テスト専用: 実クラッシュ (measure_fn を包む except に捕まらない例外) を模す。"""


@pytest.mark.parametrize(
    ("records", "manifest_exists", "expected"),
    [
        pytest.param(
            [
                {"event": "launch-start"},
                _perf_preflight_journal_record(available=False),
            ],
            False, "L", id="official-degraded-L",
        ),
        pytest.param(
            [_perf_preflight_journal_record(available=True)],
            True, "M-prestart", id="pilot-M-prestart",
        ),
        pytest.param(
            [
                {"event": "launch-start"},
                _perf_preflight_journal_record(available=False),
            ],
            True, "M-prestart", id="official-M-prestart",
        ),
    ],
)
def test_classify_journal_resume_state_accepts_valid_perf_preflight_prefix(
        records, manifest_exists, expected):
    assert s8b_floor_campaign._floor_contract.classify_journal_resume_state(
        records, manifest_exists=manifest_exists,
        result_published=False, markdown_published=False,
    ) == expected


@pytest.mark.parametrize("event", [[], {}, 7], ids=["list", "dict", "integer"])
def test_classify_journal_resume_state_rejects_non_string_event(event):
    with pytest.raises(
            s8b_floor_campaign._floor_contract.FloorContractError,
            match="event が文字列でない",
    ):
        s8b_floor_campaign._floor_contract.classify_journal_resume_state(
            [{"event": event}], manifest_exists=True,
            result_published=False, markdown_published=False,
        )


@pytest.mark.parametrize(("records", "result_published", "markdown_published", "reason"), [
    ([{"event": "terminal", "status": "aborted"}], False, False,
     "aborted/artifact-invalid terminal は再開できない"),
    ([{"event": "terminal", "status": "artifact-invalid"}], False, False,
     "aborted/artifact-invalid terminal は再開できない"),
    ([{"event": "terminal", "status": "completed"},
      {"event": "terminal", "status": "completed"}], False, False,
     "resume journal の terminal が重複している"),
    ([{"event": "terminal", "status": "completed"}, {"event": "late"}], False, False,
     "resume journal の terminal が最終 record でない"),
    ([{"event": "terminal", "status": "completed"}], True, True,
     "publish 完了済み campaign は再開できない"),
])
def test_journal_resume_state_rejects_nonresumable_terminals(
        records, result_published, markdown_published, reason):
    with pytest.raises(
            s8b_floor_campaign._floor_contract.FloorContractError, match=reason):
        s8b_floor_campaign._floor_contract.classify_journal_resume_state(
            records, manifest_exists=True,
            result_published=result_published,
            markdown_published=markdown_published,
        )


def test_pilot_pre_manifest_perf_preflight_resume_remains_l_rejected(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    monkeypatch.setattr(
        s8b_floor_campaign,
        "build_cells",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("fixture pilot pre-manifest build crash")
        ),
    )
    with pytest.raises(RuntimeError, match="pre-manifest build crash"):
        _run_campaign(
            protocol, _verified_freeze(freeze), out_root=out_root,
            build_root=tmp_path / "bin", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""),
            perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=True),
        )
    run_dir = next(path.parent for path in out_root.rglob("journal.jsonl"))
    assert _read_journal_lines(run_dir / "journal.jsonl") == [
        _perf_preflight_journal_record(available=True)
    ]
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="manifest 無し journal",
    ):
        _run_campaign(
            protocol, _verified_freeze(freeze), out_root=out_root,
            build_root=tmp_path / "bin", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), resume_dir=run_dir,
        )


def test_pilot_m_prestart_perf_preflight_resume_rebuilds_and_runs(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with monkeypatch.context() as scoped:
        scoped.setattr(
            s8b_floor_campaign._Runner, "run",
            lambda self: (_ for _ in ()).throw(_SimulatedCrash("pilot prestart")),
        )
        with pytest.raises(_SimulatedCrash, match="pilot prestart"):
            _run_campaign(
                protocol, _verified_freeze(freeze), out_root=out_root,
                build_root=tmp_path / "bin",
                measure_fn=_make_measure_fn(
                    reps=5, value_fn=lambda cid: _BASE_TPS[cid],
                ),
                probe_fn=lambda: (1, "", ""),
                perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=True),
            )
    run_dir = _only_run_dir(out_root)
    assert [record["event"] for record in _read_journal_lines(
        run_dir / "journal.jsonl"
    )] == ["perf-preflight"]
    outcome = _run_campaign(
        protocol, _verified_freeze(freeze), out_root=out_root,
        build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
        probe_fn=lambda: (1, "", ""), resume_dir=run_dir,
    )
    journal = _read_journal_lines(run_dir / "journal.jsonl")
    assert outcome["status"] == "completed"
    assert sum(record.get("event") == "campaign-start" for record in journal) == 1
    assert not any(record.get("event") == "resume-start" for record in journal)


@pytest.mark.parametrize("mutation", ["malformed", "duplicate", "manifest-mismatch"])
def test_m_running_rejects_invalid_perf_preflight_event(
        tmp_path, mutation):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    crashing_measure, _ = _crash_at(2)
    with pytest.raises(_SimulatedCrash):
        _run_campaign(
            protocol, _verified_freeze(freeze), out_root=out_root,
            build_root=tmp_path / "bin", measure_fn=crashing_measure,
            probe_fn=lambda: (1, "", ""),
            perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=True),
        )
    run_dir = _only_run_dir(out_root)
    journal_path = run_dir / "journal.jsonl"
    records = _read_journal_lines(journal_path)
    event = next(record for record in records if record.get("event") == "perf-preflight")
    if mutation == "malformed":
        event["perf_preflight_receipt"].pop("available")
        expected_error = "receipt が不正"
    elif mutation == "duplicate":
        records.append(copy.deepcopy(event))
        expected_error = "重複"
    else:
        event["perf_preflight_receipt"] = _perf_receipt(available=False)
        expected_error = "manifest と不一致"
    journal_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match=expected_error):
        _run_campaign(
            protocol, _verified_freeze(freeze), out_root=out_root,
            build_root=tmp_path / "bin", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), resume_dir=run_dir,
        )


def _crash_at(n_crash: int):
    call_count = {"n": 0}

    def measure_fn(binary, records, threads, workload):
        call_count["n"] += 1
        if call_count["n"] == n_crash:
            raise _SimulatedCrash("fixture: session 実行中に死ぬ")
        cell_id = _cell_id_from_binary(binary)
        return _FakeScalePoint(
            throughputs=[_BASE_TPS[cell_id]] * 5, notes=[],
            run_cmd=_shape_faithful_run_cmd(binary, records, threads, workload),
        )
    return measure_fn, call_count


def test_resume_forward_only_skips_completed_and_crashed_seqs(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"

    measure_fn, call_count = _crash_at(4)  # seq0-2 完了、seq3 は start だけ
    with pytest.raises(_SimulatedCrash):
        _run_campaign(protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                      measure_fn=measure_fn, probe_fn=lambda: (1, "", ""))
    assert call_count["n"] == 4

    run_dir = _only_run_dir(out_root)
    assert not (run_dir / "result.json").exists()
    journal_before = _read_journal_lines(run_dir / "journal.jsonl")
    starts_before = [r for r in journal_before if r.get("event") == "session-start"]
    sessions_before = [r for r in journal_before if r.get("event") == "session"]
    assert {r["seq"] for r in starts_before} == {0, 1, 2, 3}
    assert {r["seq"] for r in sessions_before} == {0, 1, 2}
    crashed_cell = next(r["cell_id"] for r in starts_before if r["seq"] == 3)

    # protocol hash 不一致 (master_seed 変更) の resume は拒否される。
    mismatched = dict(protocol)
    mismatched["master_seed"] = "different-seed"
    resume_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="protocol sha256"):
        _run_campaign(mismatched, verified, out_root=out_root, build_root=tmp_path / "bin",
                      resume_dir=run_dir, measure_fn=resume_fn, probe_fn=lambda: (1, "", ""))

    # 正当な resume は forward-only で完了。
    resume_fn2 = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                            resume_dir=run_dir, measure_fn=resume_fn2, probe_fn=lambda: (1, "", ""))
    assert outcome["status"] == "completed"
    assert len(resume_fn2.calls) == 96 - 4  # seq4..95 の 92 本だけ新規実行

    journal_after = _read_journal_lines(run_dir / "journal.jsonl")
    starts_after = [r for r in journal_after if r.get("event") == "session-start"]
    seqs_after = [r["seq"] for r in starts_after]
    assert len(seqs_after) == len(set(seqs_after))          # seq の二重 start が無い
    assert sum(1 for s in seqs_after if s == 3) == 1        # crash seq3 は 1 回だけ
    assert not any(r.get("seq") == 3 and r.get("event") == "session" for r in journal_after)

    # crash したセルは round1 の 1 session を永久に失い n_sessions に届かず invalid。
    result = outcome["result"]
    assert result["cells"][crashed_cell]["n_valid"] < 8
    assert result["cells"][crashed_cell]["valid"] is False


def test_resume_runner_replays_only_admission_proved_cut6_m_plus_a_minus(
    tmp_path, monkeypatch,
):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    original_append = s8b_floor_campaign._holdout_admission._append_ledger
    crashed = {"done": False}

    def crash_after_marker(path, rows):
        if path.name == "attempt-ledger.jsonl" and not crashed["done"]:
            crashed["done"] = True
            raise _SimulatedCrash("fixture: cut6 after consumed marker")
        return original_append(path, rows)

    with monkeypatch.context() as scoped:
        scoped.setattr(
            s8b_floor_campaign._holdout_admission,
            "_append_ledger", crash_after_marker,
        )
        with pytest.raises(_SimulatedCrash, match="cut6"):
            _run_campaign(
                protocol, verified, out_root=out_root,
                build_root=tmp_path / "bin",
                measure_fn=_make_measure_fn(
                    reps=5, value_fn=lambda cid: _BASE_TPS[cid],
                ),
                probe_fn=lambda: (1, "", ""),
            )

    run_dir = _only_run_dir(out_root)
    before = _read_journal_lines(run_dir / "journal.jsonl")
    cut6_start = next(row for row in before if row.get("event") == "session-start")
    assert not any(
        row.get("event") == "session"
        and row.get("attempt_id") == cut6_start["attempt_id"]
        for row in before
    )

    resumed_measure = _make_measure_fn(
        reps=5, value_fn=lambda cid: _BASE_TPS[cid],
    )
    outcome = _run_campaign(
        protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
        resume_dir=run_dir, measure_fn=resumed_measure,
        probe_fn=lambda: (1, "", ""),
    )

    assert outcome["status"] == "completed"
    after = _read_journal_lines(run_dir / "journal.jsonl")
    assert sum(
        row.get("event") == "session-start"
        and row.get("attempt_id") == cut6_start["attempt_id"]
        for row in after
    ) == 1
    assert sum(
        row.get("event") == "session"
        and row.get("attempt_id") == cut6_start["attempt_id"]
        for row in after
    ) == 1
    assert len(resumed_measure.calls) == len(outcome["result"]["sessions"])


def test_certified_cut6_existing_marker_competing_probe_aborts_without_result(
    tmp_path, monkeypatch,
):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    original_append = s8b_floor_campaign._holdout_admission._append_ledger
    crashed = {"done": False}

    def crash_after_marker(path, rows):
        if path.name == "attempt-ledger.jsonl" and not crashed["done"]:
            crashed["done"] = True
            raise _SimulatedCrash("fixture: certified cut6 after marker")
        return original_append(path, rows)

    launcher = s8b_floor_campaign.s8b_floor_attempt_launcher
    monkeypatch.setattr(
        launcher,
        "_owned_post_probe",
        lambda: {"rc": 1, "stdout": "", "stderr": "", "competing": False},
    )
    with monkeypatch.context() as scoped:
        scoped.setattr(
            s8b_floor_campaign._holdout_admission,
            "_append_ledger",
            crash_after_marker,
        )
        with pytest.raises(_SimulatedCrash, match="certified cut6"):
            _run_campaign(
                protocol, verified, out_root=out_root,
                build_root=tmp_path / "bin", measure_fn=None,
                probe_fn=lambda: pytest.fail("legacy probe path was called"),
                perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
            )

    run_dir = _only_run_dir(out_root)
    before = _read_journal_lines(run_dir / "journal.jsonl")
    cut6_start = next(row for row in before if row.get("event") == "session-start")
    authority = _test_holdout_authority(out_root, protocol, verified)
    shared = s8b_floor_campaign._holdout_admission.shared_admission_root(authority)
    assert len(list((shared / "measurement-generation-consumed").iterdir())) == 1
    attempt_ledger = shared / "attempt-ledger.jsonl"
    assert not attempt_ledger.exists() or attempt_ledger.read_bytes() == b""

    measured_probe = {
        "rc": 0,
        "stdout": "resume competitor",
        "stderr": "resume probe stderr",
        "competing": True,
    }
    monkeypatch.setattr(launcher, "_owned_post_probe", lambda: measured_probe)
    with pytest.raises(
        s8b_floor_campaign.CampaignAbort,
        match="^cut6_replay_pre_probe_competing_existing_marker$",
    ):
        _run_campaign(
            protocol, verified, out_root=out_root,
            build_root=tmp_path / "bin", resume_dir=run_dir,
            measure_fn=None,
            probe_fn=lambda: pytest.fail("legacy probe path was called"),
            perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
        )

    after = _read_journal_lines(run_dir / "journal.jsonl")
    assert not any(
        row.get("event") == "session"
        and row.get("attempt_id") == cut6_start["attempt_id"]
        for row in after
    )
    assert not (run_dir / "result.json").exists()
    assert not (run_dir / "result.md").exists()


def test_resume_rejects_tampered_binary_but_succeeds_when_untampered(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    build_root = tmp_path / "bin"

    measure_fn, _ = _crash_at(4)
    with pytest.raises(_SimulatedCrash):
        _run_campaign(protocol, verified, out_root=out_root, build_root=build_root,
                      measure_fn=measure_fn, probe_fn=lambda: (1, "", ""))

    run_dir = _only_run_dir(out_root)
    manifest = json.loads((run_dir / "manifest.json").read_bytes())
    binaries = manifest["binaries"]
    tampered_cell = sorted(binaries)[0]
    binary_path = out_root / binaries[tampered_cell]["binary"]
    original = binary_path.read_bytes()

    binary_path.write_bytes(original + b"-tampered")
    resume_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="バイナリ sha256"):
        _run_campaign(protocol, verified, out_root=out_root, build_root=build_root,
                      resume_dir=run_dir, measure_fn=resume_fn, probe_fn=lambda: (1, "", ""))
    assert resume_fn.calls == []
    assert not (run_dir / "result.json").exists()

    binary_path.write_bytes(original)
    resume_fn2 = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(protocol, verified, out_root=out_root, build_root=build_root,
                            resume_dir=run_dir, measure_fn=resume_fn2, probe_fn=lambda: (1, "", ""))
    assert outcome["status"] == "completed"


def test_resume_rejects_tampered_manifest_schedule(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    build_root = tmp_path / "bin"

    measure_fn, _ = _crash_at(4)
    with pytest.raises(_SimulatedCrash):
        _run_campaign(protocol, verified, out_root=out_root, build_root=build_root,
                      measure_fn=measure_fn, probe_fn=lambda: (1, "", ""))
    run_dir = _only_run_dir(out_root)

    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    # schedule の 1 行の cell_id を別セルに書き換える (権威 schedule の改竄)。
    manifest["schedule"][0]["cell_id"] = manifest["schedule"][1]["cell_id"]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")

    resume_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="schedule"):
        _run_campaign(protocol, verified, out_root=out_root, build_root=build_root,
                      resume_dir=run_dir, measure_fn=resume_fn, probe_fn=lambda: (1, "", ""))


def test_resume_rejects_duplicate_session_start(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    build_root = tmp_path / "bin"

    measure_fn, _ = _crash_at(4)
    with pytest.raises(_SimulatedCrash):
        _run_campaign(protocol, verified, out_root=out_root, build_root=build_root,
                      measure_fn=measure_fn, probe_fn=lambda: (1, "", ""))
    run_dir = _only_run_dir(out_root)

    # journal に seq0 の session-start を二重に足す (状態機械が duplicate start を拒否)。
    journal_path = run_dir / "journal.jsonl"
    dup = next(r for r in _read_journal_lines(journal_path)
               if r.get("event") == "session-start" and r.get("seq") == 0)
    s8b_floor_campaign._journal_append(journal_path, dup)

    resume_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="duplicate start"):
        _run_campaign(protocol, verified, out_root=out_root, build_root=build_root,
                      resume_dir=run_dir, measure_fn=resume_fn, probe_fn=lambda: (1, "", ""))


def test_resume_does_not_reissue_retry_slot_after_retry_start_crash(tmp_path):
    """retry の session-start (authorization) 後・完了前で crash した枠は resume で再発行しない
    (β-5: 枠消費は authorization の fsync 時点)。"""
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    build_root = tmp_path / "bin"
    flaky = "rr79::sort_best"

    # 1 回目: flaky の planned は partial (無効)、flaky の retry 1 回目で crash。
    def first_measure(binary, records, threads, workload):
        cell_id = _cell_id_from_binary(binary)
        if cell_id == flaky:
            # planned は 4 reps (partial)。retry (2 回目以降の flaky 呼び) は crash。
            first_measure.flaky_calls += 1
            if first_measure.flaky_calls == 1:
                return _FakeScalePoint(throughputs=[_BASE_TPS[cell_id]] * 4, notes=[],
                                       run_cmd=_shape_faithful_run_cmd(
                                           binary, records, threads, workload))
            raise _SimulatedCrash("fixture: retry 実行中に死ぬ")
        return _FakeScalePoint(
            throughputs=[_BASE_TPS[cell_id]] * 5, notes=[],
            run_cmd=_shape_faithful_run_cmd(binary, records, threads, workload),
        )
    first_measure.flaky_calls = 0

    with pytest.raises(_SimulatedCrash):
        _run_campaign(protocol, verified, out_root=out_root, build_root=build_root,
                      measure_fn=first_measure, probe_fn=lambda: (1, "", ""))

    run_dir = _only_run_dir(out_root)
    journal_before = _read_journal_lines(run_dir / "journal.jsonl")
    retry_starts = [r for r in journal_before if r.get("event") == "session-start"
                    and r.get("kind") == "retry" and r.get("cell_id") == flaky]
    assert [r["retry_ordinal"] for r in retry_starts] == [1]  # ordinal 1 が authorize 済み

    # 2 回目 (resume): flaky も正常に測れる。ordinal 1 は再発行されず ordinal 2 が使われる。
    resume_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(protocol, verified, out_root=out_root, build_root=build_root,
                            resume_dir=run_dir, measure_fn=resume_fn, probe_fn=lambda: (1, "", ""))
    assert outcome["status"] == "completed"

    journal_after = _read_journal_lines(run_dir / "journal.jsonl")
    retry_starts_after = [r for r in journal_after if r.get("event") == "session-start"
                          and r.get("kind") == "retry" and r.get("cell_id") == flaky]
    ordinals = [r["retry_ordinal"] for r in retry_starts_after]
    assert ordinals == [1, 2]                 # ordinal 1 は 1 回だけ (再発行なし)
    assert len(ordinals) == len(set(ordinals))  # (cell, ordinal) は再利用されない
    # 通算 2 枠を超えていない。
    assert len(ordinals) <= protocol["retry_slots_per_cell"]


# =========================================================================== #
# 10. end-to-end golden floor 値 + verify 改竄検出 + duration 台帳               #
# =========================================================================== #

def test_end_to_end_golden_floor_values_and_tamper_detection(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    wired = 0.05
    protocol = _protocol(freeze_sha=_freeze_sha(freeze), wired_min_rel_floor=wired)
    # 全 session が同一 cell に同一値 → s_c=0, u_noise=0 → floor = wired × m_stock。
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "out",
                            build_root=tmp_path / "bin", measure_fn=measure_fn,
                            probe_fn=lambda: (1, "", ""))
    assert outcome["status"] == "completed"
    result = outcome["result"]

    expected_protocol = s8b_floor_campaign._expected_protocol(
        s8b_floor_campaign.validate_protocol(protocol),
        s8b_floor_campaign.enumerate_cells(freeze, stock_configuration=_STOCK),
    )
    live_admission = _live_holdout_admission_for_outcome(
        protocol=protocol, freeze_doc=verified,
        out_root=tmp_path / "out", outcome=outcome,
    )
    assert s8b_floor_stats.verify_floor_artifact(
        result, expected_protocol,
        expected_holdout_admission=live_admission,
        expected_use_perf=True,
    ) == []

    for holdout_id in ("rr79", "rr23"):
        stock_id = f"{holdout_id}::{_STOCK}"
        m_stock = _BASE_TPS[stock_id]
        expected_floor = wired * m_stock
        floors = result["floors"][holdout_id]
        assert floors["scale_ref"] == m_stock
        for cfg in _CONFIGS:
            if cfg == _STOCK:
                continue
            assert floors["pairs"][cfg] == expected_floor, cfg  # pair キーは configuration_id
        assert floors["scalar_alt"] == expected_floor

    # verify は expected_protocol を必須引数に取る (自己申告だけを信頼根にしない, α-3)。
    tampered = json.loads(json.dumps(result))
    tampered["floors"]["rr79"]["pairs"][_CONFIGS[0]] = 999999.0
    assert s8b_floor_stats.verify_floor_artifact(
        tampered, expected_protocol,
        expected_holdout_admission=live_admission,
        expected_use_perf=True,
    )


def test_result_json_records_per_attempt_duration_and_no_absolute_monotonic(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])

    ticks = {"t": 0.0}

    def monotonic_fn():
        ticks["t"] += 0.5
        return ticks["t"]

    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "out",
                            build_root=tmp_path / "bin", measure_fn=measure_fn,
                            probe_fn=lambda: (1, "", ""), monotonic_fn=monotonic_fn)
    result = outcome["result"]
    # 各 attempt に duration_s が記録される (β-10)。
    for a in result["attempts"]:
        assert isinstance(a["duration_s"], float)
        assert a["duration_s"] >= 0
    # 絶対 monotonic 値は wall_ledger / result に永続化しない (γ-12)。
    for entry in result["wall_ledger"]:
        assert "monotonic" not in entry
    for s in result["sessions"]:
        assert "monotonic" not in s
    # result.md は result JSON からのみ描画され機械読込を要さない (β-9): md が存在し attempt 台帳
    # と machine_anomaly 見出しを含む。
    run_dir = Path(outcome["run_dir"])
    md = (run_dir / "result.md").read_text(encoding="utf-8")
    assert "全 attempt 台帳" in md
    assert "machine_anomaly" in md
    assert "除外 session (理由別件数)" in md


def test_floor_manifest_binary_sha256_matches_real_file_bytes(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "out",
                            build_root=tmp_path / "bin", measure_fn=measure_fn,
                            probe_fn=lambda: (1, "", ""))
    assert outcome["status"] == "completed"
    run_dir = _only_run_dir(tmp_path / "out")
    binaries = json.loads((run_dir / "manifest.json").read_bytes())["binaries"]
    assert binaries
    for cell_id, rec in binaries.items():
        actual = hashlib.sha256(
            (tmp_path / "out" / rec["binary"]).read_bytes()).hexdigest()
        assert rec["binary_sha256"] == actual, cell_id
        assert len(rec["binary_sha256"]) == 64
        assert rec["bin_hash_short"] == rec["binary_sha256"][:16]


@pytest.mark.skipif(
    not ((ROOT / "external" / "ccbench" / ".git").exists()
         and all(shutil.which(tool) for tool in ("cmake", "gcc-13", "g++-13", "nm"))),
    reason="slow real-build canary: initialized ccbench + pinned toolchain が必要",
)
def test_slow_real_prepare_cell_to_buildcache_canary_one_configuration(tmp_path):
    """F19: fake でなく実 prepare_cell→buildcache.build を 1 構成だけ通す canary。"""
    freeze = _freeze_document()
    cell = next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK)
        if cell["configuration_id"] == _STOCK
    )
    pin = subprocess.run(
        ["git", "-C", str(ROOT / "external" / "ccbench"), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    with s8b_floor_campaign._prepared_binding(
            freeze=freeze, holdout_id=cell["holdout_id"],
            configuration_id=cell["configuration_id"], ccbench_pin=pin,
            cxx="g++-13",
            prepare_fn=s8b_floor_campaign.prepare_cell) as (identity, prepared):
        evidence = s8b_floor_campaign.source_digest.resolve_evidence(
            prepared.genome, pin, ccbench_dir=prepared.ccbench_dir,
            cxx=s8b_floor_campaign.buildcache.DEFAULT_CXX,
        )
        context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
        review = s8b_materialization.reviewed_source_capability(
            review_id=ReviewId.S8B_FLOOR, source=evidence,
            input_sha256=identity["entry_sha256"],
        )
        admission = derive_build_admission(context, evidence, review_receipt=review)
        result = s8b_floor_campaign.buildcache.build(
            prepared.genome, ccbench_commit=pin, trace=False,
            cache_root=str(tmp_path / "cache"), ccbench_dir=prepared.ccbench_dir,
            src_token=evidence.src_token, jobs=1, admission=admission,
            build_context=context, source_evidence=evidence,
        )
    assert Path(result.binary).is_file()
    assert s8b_floor_campaign.buildcache.is_full_sha256(result.bin_sha256)
    assert result.configure_argv and result.build_argv


@pytest.mark.skipif(
    not ((ROOT / "external" / "ccbench" / ".git").exists()
         and all(shutil.which(tool) for tool in ("cmake", "gcc-13", "g++-13", "nm"))),
    reason="slow real-build v2 canary: initialized ccbench + pinned toolchain が必要",
)
def test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration(tmp_path):
    """F19 v2: 実 prepare_cell の隔離 tree を build_v2 が直接 build する。"""
    freeze = _freeze_document()
    cell = next(
        cell for cell in s8b_floor_campaign.enumerate_cells(
            freeze, stock_configuration=_STOCK)
        if cell["configuration_id"] == _STOCK
    )
    pin = subprocess.run(
        ["git", "-C", str(ROOT / "external" / "ccbench"), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    contract = ec.lookup(ENV_TAG)
    with s8b_floor_campaign._prepared_binding(
            freeze=freeze, holdout_id=cell["holdout_id"],
            configuration_id=cell["configuration_id"], ccbench_pin=pin,
            cxx="g++-13",
            prepare_fn=s8b_floor_campaign.prepare_cell) as (identity, prepared):
        evidence = s8b_floor_campaign.source_digest.resolve_evidence(
            prepared.genome, pin, ccbench_dir=prepared.ccbench_dir,
            cxx=s8b_floor_campaign.buildcache.DEFAULT_CXX,
        )
        context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
        review = s8b_materialization.reviewed_source_capability(
            review_id=ReviewId.S8B_FLOOR, source=evidence,
            input_sha256=identity["entry_sha256"],
        )
        admission = derive_build_admission(context, evidence, review_receipt=review)
        result = s8b_floor_campaign.buildcache.build_v2(
            prepared.genome, admission=admission, build_context=context,
            source_evidence=evidence,
            contract=contract, ccbench_commit=pin, trace=False,
            cache_root=str(tmp_path / "cache"), ccbench_dir=prepared.ccbench_dir,
            src_token=evidence.src_token, cc=s8b_floor_campaign.buildcache.DEFAULT_CC,
            cxx=s8b_floor_campaign.buildcache.DEFAULT_CXX, timeout_s=900,
        )
    assert Path(result.binary).is_file()
    assert result.contract_sha256 == contract.contract_sha256
    assert Path(result.ccbench_root) == Path(prepared.ccbench_dir).absolute()
    assert s8b_floor_campaign.buildcache.is_full_sha256(result.bin_sha256)


# =========================================================================== #
# V4 — launch certificate (C2-2) / binary receipt (C3-6) / store (C3-7)         #
# =========================================================================== #

def test_launch_certificate_create_only_and_journal_binding(tmp_path):
    cert = s8b_floor_campaign.build_launch_certificate(
        v1_freeze_sha256="a" * 64, clean_digest="b" * 64, protocol_sha256="c" * 64,
        started_utc=_FIXED_NOW.isoformat(), campaign_run_id="run-0001",
    )
    assert cert["schema"] == s8b_floor_campaign.LAUNCH_CERT_SCHEMA
    cert_path = tmp_path / "launch_certificate.json"
    bound_sha = s8b_floor_campaign.issue_launch_certificate(cert_path, cert)
    # journal 束縛値 = 発行 bytes の sha256。
    assert bound_sha == hashlib.sha256(cert_path.read_bytes()).hexdigest()
    # create-only: 再発行は fail-closed (上書きしない)。
    with pytest.raises(s8b_floor_campaign.FloorCampaignError):
        s8b_floor_campaign.issue_launch_certificate(cert_path, cert)


def _clean_report(*, missing=None, dirty=None, positive_hits=1) -> dict:
    holdouts = {
        name: {"conjunction_hits": (["leak.txt"] if name == dirty else [])}
        for name in s8b_floor_campaign._holdout_freeze.HOLDOUTS
        if name != missing
    }
    return {
        "holdouts": holdouts,
        "positive_control": {"hit_count": positive_hits},
    }


def _stub_clean_scan(monkeypatch, *, reports, enumerations) -> None:
    report_iter = iter(reports)
    enumeration_iter = iter(enumerations)
    monkeypatch.setattr(
        s8b_floor_campaign._holdout_freeze, "enumerate_repository_files",
        lambda root: next(enumeration_iter),
    )
    monkeypatch.setattr(
        s8b_floor_campaign._holdout_freeze, "search_repository",
        lambda root, files: next(report_iter),
    )


def _expected_clean_digest(files, allowlist) -> str:
    preimage = {
        "schema": "s8b-clean-scan-digest/v3",
        "repository_files": list(files),
        "freeze_allowlist": [
            {"path": path, "sha256": allowlist[path]}
            for path in sorted(allowlist)
        ],
    }
    return hashlib.sha256(json.dumps(
        preimage, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()


def test_clean_scan_digest_returns_digest_when_clean(tmp_path, monkeypatch):
    files = ("a.py", "b.py")
    _stub_clean_scan(
        monkeypatch, reports=[_clean_report()], enumerations=[files, files],
    )
    digest = s8b_floor_campaign.clean_scan_digest(tmp_path, freeze_allowlist={})
    assert digest == _expected_clean_digest(files, {})


@pytest.mark.parametrize("kind", ["empty", "missing", "dirty", "positive-zero"])
def test_clean_scan_digest_rejects_incomplete_or_failed_search(tmp_path, monkeypatch, kind):
    names = tuple(s8b_floor_campaign._holdout_freeze.HOLDOUTS)
    if kind == "empty":
        report = {"holdouts": {}, "positive_control": {"hit_count": 1}}
    elif kind == "missing":
        report = _clean_report(missing=names[0])
    elif kind == "dirty":
        report = _clean_report(dirty=names[0])
    else:
        report = _clean_report(positive_hits=0)
    files = ("a.py",)
    _stub_clean_scan(monkeypatch, reports=[report], enumerations=[files, files])
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="clean scan"):
        s8b_floor_campaign.clean_scan_digest(tmp_path, freeze_allowlist={})


def test_clean_scan_digest_rejects_file_enumeration_change(tmp_path, monkeypatch):
    _stub_clean_scan(
        monkeypatch, reports=[_clean_report()],
        enumerations=[("a.py",), ("a.py", "appeared.py")],
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="列挙"):
        s8b_floor_campaign.clean_scan_digest(tmp_path, freeze_allowlist={})


def test_clean_scan_digest_rejects_freeze_file_outside_allowlist(tmp_path, monkeypatch):
    rel = "output/s8b-freeze/unlisted.json"
    path = tmp_path / rel
    path.parent.mkdir(parents=True)
    path.write_bytes(b"no holdout hit")
    files = (rel,)
    _stub_clean_scan(
        monkeypatch, reports=[_clean_report()], enumerations=[files, files],
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="未知 file"):
        s8b_floor_campaign.clean_scan_digest(tmp_path, freeze_allowlist={})


def test_clean_scan_digest_accepts_exact_freeze_allowlist(tmp_path, monkeypatch):
    payload = b"approved freeze bytes"
    rel = s8b_floor_campaign._FLOOR_PROTOCOL_REL
    path = tmp_path / rel
    path.parent.mkdir(parents=True)
    path.write_bytes(payload)
    files = (rel,)
    _stub_clean_scan(
        monkeypatch, reports=[_clean_report()], enumerations=[files, files],
    )
    allowlist = {rel: hashlib.sha256(payload).hexdigest()}
    digest = s8b_floor_campaign.clean_scan_digest(
        tmp_path, freeze_allowlist=allowlist,
    )
    assert digest == _expected_clean_digest(files, allowlist)


def test_clean_scan_digest_binds_path_to_sha_not_only_hash_multiset(
        tmp_path, monkeypatch):
    files = (
        s8b_floor_campaign._FLOOR_PROTOCOL_REL,
        s8b_floor_campaign._HOLDOUT_FREEZE_REL,
    )
    roots = (tmp_path / "left", tmp_path / "right")
    payload_pairs = ((b"alpha", b"beta"), (b"beta", b"alpha"))
    allowlists = []
    for root, payloads in zip(roots, payload_pairs):
        allowlist = {}
        for rel, payload in zip(files, payloads):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            allowlist[rel] = hashlib.sha256(payload).hexdigest()
        allowlists.append(allowlist)
    assert sorted(allowlists[0].values()) == sorted(allowlists[1].values())
    _stub_clean_scan(
        monkeypatch, reports=[_clean_report(), _clean_report()],
        enumerations=[files, files, files, files],
    )
    digests = [
        s8b_floor_campaign.clean_scan_digest(root, freeze_allowlist=allowlist)
        for root, allowlist in zip(roots, allowlists)
    ]
    assert digests[0] != digests[1]


def test_clean_scan_digest_rejects_allowlist_entry_deleted_after_construction(
        tmp_path, monkeypatch):
    rel = s8b_floor_campaign._FLOOR_PROTOCOL_REL
    path = tmp_path / rel
    path.parent.mkdir(parents=True)
    path.write_bytes(b"protocol")
    allowlist = {rel: hashlib.sha256(path.read_bytes()).hexdigest()}
    path.unlink()
    _stub_clean_scan(
        monkeypatch, reports=[_clean_report()], enumerations=[(), ()],
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="missing|phantom"):
        s8b_floor_campaign.clean_scan_digest(
            tmp_path, freeze_allowlist=allowlist,
        )


@pytest.mark.parametrize("rel", [
    "/output/s8b-freeze/floor_protocol.json",
    "output/s8b-freeze/../floor_protocol.json",
    "output/s8b-freeze//floor_protocol.json",
    "output/./s8b-freeze/floor_protocol.json",
    "output/s8b-freeze/floor_protocol.json\x00",
    "output/s8b-freeze/floor_protocol.json\x85",
    "output/s8b-freeze/\udcff.json",
])
def test_clean_scan_digest_rejects_noncanonical_allowlist_path(
        tmp_path, monkeypatch, rel):
    _stub_clean_scan(
        monkeypatch, reports=[_clean_report()], enumerations=[(), ()],
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="path"):
        s8b_floor_campaign.clean_scan_digest(
            tmp_path, freeze_allowlist={rel: "a" * 64},
        )


def test_clean_scan_digest_binds_recognized_chain_record_path_and_bytes(
        tmp_path, monkeypatch):
    rel = f"output/s8b-freeze/approvals/{'a' * 64}.json"
    chain_file = tmp_path / rel
    chain_file.parent.mkdir(parents=True)
    chain_file.write_bytes(b"chain-owned")
    files = (rel,)
    _stub_clean_scan(
        monkeypatch, reports=[_clean_report()], enumerations=[files, files],
    )
    assert s8b_floor_campaign.clean_scan_digest(
        tmp_path, freeze_allowlist={},
    ) == _expected_clean_digest(files, {
        rel: hashlib.sha256(chain_file.read_bytes()).hexdigest(),
    })


def test_clean_scan_digest_rejects_unknown_chain_filename(tmp_path, monkeypatch):
    rel = "output/s8b-freeze/approvals/record.json"
    chain_file = tmp_path / rel
    chain_file.parent.mkdir(parents=True)
    chain_file.write_bytes(b"not a named chain record")
    files = (rel,)
    _stub_clean_scan(
        monkeypatch, reports=[_clean_report()], enumerations=[files, files],
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="未知 file"):
        s8b_floor_campaign.clean_scan_digest(tmp_path, freeze_allowlist={})


def test_clean_scan_digest_rejects_symlink_anywhere_in_freeze_namespace(
        tmp_path, monkeypatch):
    target = tmp_path / "target.json"
    target.write_bytes(b"target")
    rel = f"output/s8b-freeze/approvals/{'b' * 64}.json"
    link = tmp_path / rel
    link.parent.mkdir(parents=True)
    link.symlink_to(target)
    files = (rel,)
    _stub_clean_scan(
        monkeypatch, reports=[_clean_report()], enumerations=[files, files],
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="symlink"):
        s8b_floor_campaign.clean_scan_digest(tmp_path, freeze_allowlist={})


def _install_valid_prediction_preflight_fixture(
        root: Path, *, include_journal: bool = True,
        include_resolved_cell: bool = True) -> tuple[str, str, str]:
    freeze_rel = "output/s8b-freeze/holdout_freeze.json"
    source_paths = {
        "holdout_freeze": freeze_rel,
        "builder": "orchestrator/campaign/s8b_selector_input.py",
        "role": ".claude/agents/selector-8b.md",
        "input_schema": "orchestrator/campaign/s8b_selector_catalog.json",
        "output_schema": "orchestrator/campaign/s8b_selector_output_schema.json",
    }
    for relative in source_paths.values():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    parser_rel = s8b_prediction_runner._PARSER_MODULE_PATH.as_posix()
    parser_path = root / parser_rel
    parser_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / parser_rel, parser_path)
    protocol_path = root / s8b_floor_campaign._FLOOR_PROTOCOL_REL
    protocol_path.parent.mkdir(parents=True, exist_ok=True)
    protocol_path.write_bytes(b"canonical-protocol")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run([
        "git", "-C", str(root), "-c", "user.name=fixture",
        "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
        "commit", "-qm", "prediction preflight fixture",
    ], check=True)
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
        text=True, stdout=subprocess.PIPE,
    ).stdout.strip()
    freeze = json.loads((root / freeze_rel).read_bytes())
    jobs = s8b_selector_freeze.build_prediction_jobs(freeze)
    freeze_sha = hashlib.sha256((root / freeze_rel).read_bytes()).hexdigest()
    protocol_sha = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    role_sha = hashlib.sha256((root / source_paths["role"]).read_bytes()).hexdigest()
    binding = s8b_prediction_runner.JournalBinding(
        pre_oracle_head=head,
        protocol_sha256=protocol_sha,
        freeze_sha256=freeze_sha,
        provider_kind=s8b_prediction_runner.PROVIDER_KIND_CLAUDE_HEADLESS,
        role_file_sha256=role_sha,
        parser_module_sha256=hashlib.sha256(parser_path.read_bytes()).hexdigest(),
        claude_executable_path="/fixture/claude",
        claude_executable_sha256="e" * 64,
        known_cells=frozenset(
            (job["target_holdout"], job["arm"]) for job in jobs
        ),
    )
    journal_path = root / s8b_floor_campaign._SELECTOR_JOURNAL_REL
    journal = s8b_prediction_runner.PredictionJournal(journal_path)
    s8b_prediction_runner.ensure_run_header(
        journal, binding=binding, created_at="2026-07-22T00:00:00+00:00",
    )
    resolved = False
    for job in jobs:
        if job["arm"] == "off":
            journal.append({
                "record_type": "static_terminal",
                "target_holdout": job["target_holdout"], "arm": job["arm"],
                "decision_method": s8b_selector_freeze.STATIC_DECISION_METHOD,
                "choice_id": s8b_selector_freeze.STATIC_DEFAULT_CHOICE_ID,
            })
            continue
        payload = s8b_prediction_runner._payload_for_job(freeze, job)
        payload_bytes = s8b_prediction_runner._canonical_json_bytes(payload)
        payload_rel = (
            f"{s8b_floor_campaign._SELECTOR_RUNS_REL}/"
            f"payload_{job['target_holdout']}_{job['arm']}.json"
        )
        (root / payload_rel).write_bytes(payload_bytes)
        journal.append({
            "record_type": "claim",
            "target_holdout": job["target_holdout"], "arm": job["arm"],
            "decision_method": s8b_selector_freeze.AGENT_DECISION_METHOD,
            "input_payload_sha256": job["input_payload_sha256"],
            "payload_path": payload_rel,
            "claimed_at": "2026-07-22T00:00:01+00:00",
        })
        if include_resolved_cell and not resolved:
            envelope_bytes = b'{"fixture":"envelope"}'
            envelope_rel = (
                f"{s8b_floor_campaign._SELECTOR_RUNS_REL}/"
                f"envelope_{job['target_holdout']}_{job['arm']}.json"
            )
            (root / envelope_rel).write_bytes(envelope_bytes)
            journal.append({
                "record_type": "envelope",
                "target_holdout": job["target_holdout"], "arm": job["arm"],
                "envelope_path": envelope_rel,
                "envelope_sha256": hashlib.sha256(envelope_bytes).hexdigest(),
            })
            raw_text = json.dumps({
                "schema_version": "8b-selector-output/v1",
                "choice_id": "c01",
                "rationale": "fixture rationale",
            }, ensure_ascii=False, separators=(",", ":"))
            raw_bytes = raw_text.encode("utf-8")
            raw_rel = (
                f"{s8b_floor_campaign._SELECTOR_RUNS_REL}/"
                f"raw_{job['target_holdout']}_{job['arm']}.txt"
            )
            (root / raw_rel).write_bytes(raw_bytes)
            attempt = s8b_selector_freeze.record_agent_attempt(
                job=job, raw_output=raw_text,
            )
            journal.append({
                "record_type": "invocation",
                "target_holdout": job["target_holdout"], "arm": job["arm"],
                "status": attempt["status"],
                "choice_id": attempt["choice_id"],
                "rationale": attempt["rationale"],
                "parser_error_code": attempt.get("parser_error_code"),
                "raw_response_path": raw_rel,
                "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
                "receipt": {
                    "child_id": "fixture-child",
                    "role_file_sha256": role_sha,
                    "model": "fixture-model",
                    "started_at": "2026-07-22T00:00:01+00:00",
                    "finished_at": "2026-07-22T00:00:02+00:00",
                    "fresh_context": True,
                    "declared_tools": [],
                    "observed_tool_events": [],
                },
            })
            resolved = True
    rows = s8b_prediction_runner.build_rows_from_journal(
        freeze, journal, binding=binding,
    )
    sources = {
        name: {
            "path": relative,
            "sha256": hashlib.sha256((root / relative).read_bytes()).hexdigest(),
        }
        for name, relative in source_paths.items()
    }
    prediction = s8b_selector_freeze.build_prediction_freeze(
        freeze=freeze, rows=rows, generated_at="2026-07-22T00:00:00+00:00",
        pre_oracle_head=head, sources=sources,
        execution_policy={
            "attempts_per_agent_cell": 1, "retry": False,
            "reuse_equal_payload_output": False, "fresh_context": True,
            "declared_tools": [],
        },
    )
    s8b_selector_freeze.write_prediction_freeze(
        root / s8b_floor_campaign._SELECTOR_PREDICTIONS_REL, prediction,
    )
    if not include_journal:
        journal_path.unlink()
    return freeze_rel, freeze_sha, protocol_sha


def test_floor_preflight_allowlist_hashes_verified_prediction_and_selector_run_files(
        tmp_path):
    freeze_rel, freeze_sha, protocol_sha = _install_valid_prediction_preflight_fixture(
        tmp_path,
    )
    prediction_path = tmp_path / s8b_floor_campaign._SELECTOR_PREDICTIONS_REL
    verified_prediction_bytes = prediction_path.read_bytes()
    journal_path = (
        tmp_path / s8b_floor_campaign._SELECTOR_RUNS_REL / "journal.jsonl"
    )
    read_counts: dict[Path, int] = {}

    def read_bytes_once_for_verified_inputs(path: Path) -> bytes:
        path = Path(path)
        read_counts[path] = read_counts.get(path, 0) + 1
        if path in {prediction_path, journal_path} and read_counts[path] > 1:
            raise AssertionError(f"検証済み input を再読した: {path}")
        return path.read_bytes()

    allowlist = s8b_floor_campaign._floor_preflight_freeze_allowlist(
        tmp_path, freeze_path=freeze_rel,
        freeze_sha256=freeze_sha,
        protocol_sha256=protocol_sha,
        _read_bytes=read_bytes_once_for_verified_inputs,
    )
    expected_paths = set(s8b_floor_campaign._PREFLIGHT_FIXED_FILES)
    expected_paths.update(
        path.relative_to(tmp_path).as_posix()
        for path in journal_path.parent.iterdir()
        if path != journal_path
    )
    assert set(allowlist) == expected_paths
    assert all(
        digest == hashlib.sha256((tmp_path / rel).read_bytes()).hexdigest()
        for rel, digest in allowlist.items()
    )
    assert allowlist[s8b_floor_campaign._SELECTOR_PREDICTIONS_REL] == (
        hashlib.sha256(verified_prediction_bytes).hexdigest()
    )
    assert read_counts[prediction_path] == 1
    assert read_counts[journal_path] == 1
    assert all(not rel.endswith("/") for rel in allowlist)
    assert {marker["check_id"] for marker in allowlist.held_checks} == {
        "s8b-floor.protocol-bytes-expected-pin",
    }


def test_floor_protocol_expected_pin_hold_and_release_positive_control(tmp_path):
    freeze_rel, freeze_sha, _protocol_sha = _install_valid_prediction_preflight_fixture(
        tmp_path,
    )
    held = s8b_floor_campaign._floor_preflight_freeze_allowlist(
        tmp_path, freeze_path=freeze_rel, freeze_sha256=freeze_sha,
        protocol_sha256="0" * 64,
    )
    assert "s8b-floor.protocol-bytes-expected-pin" in {
        marker["check_id"] for marker in held.held_checks
    }
    with mock.patch.object(s8b_floor_campaign._freeze_hold, "HELD", False):
        with pytest.raises(
                s8b_floor_campaign.FloorCampaignError,
                match="floor protocol bytes sha256 が expected と不一致"):
            s8b_floor_campaign._floor_preflight_freeze_allowlist(
                tmp_path, freeze_path=freeze_rel, freeze_sha256=freeze_sha,
                protocol_sha256="0" * 64,
            )


def test_floor_protocol_head_bytes_positive_control_fires_during_hold(tmp_path):
    freeze_rel, freeze_sha, _protocol_sha = _install_valid_prediction_preflight_fixture(
        tmp_path,
    )
    protocol_path = tmp_path / s8b_floor_campaign._FLOOR_PROTOCOL_REL
    protocol_path.write_bytes(protocol_path.read_bytes() + b" ")
    drifted_sha = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="pre_oracle_head/worktree で不一致"):
        s8b_floor_campaign._floor_preflight_freeze_allowlist(
            tmp_path, freeze_path=freeze_rel, freeze_sha256=freeze_sha,
            protocol_sha256=drifted_sha,
        )


def test_floor_preflight_requires_prediction_before_allowlist(tmp_path):
    freeze_rel = "output/s8b-freeze/holdout_freeze.json"
    freeze_path = tmp_path / freeze_rel
    freeze_path.parent.mkdir(parents=True)
    shutil.copy2(ROOT / freeze_rel, freeze_path)
    protocol_path = tmp_path / s8b_floor_campaign._FLOOR_PROTOCOL_REL
    protocol_path.write_bytes(b"protocol")
    journal_path = tmp_path / s8b_floor_campaign._SELECTOR_JOURNAL_REL
    journal_path.parent.mkdir()
    journal_path.write_bytes(b"{}\n")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="必須 file"):
        s8b_floor_campaign._floor_preflight_freeze_allowlist(
            tmp_path, freeze_path=freeze_rel,
            freeze_sha256=hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
            protocol_sha256=hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        )


def test_floor_preflight_requires_protocol(tmp_path):
    freeze_rel, freeze_sha, protocol_sha = _install_valid_prediction_preflight_fixture(
        tmp_path,
    )
    (tmp_path / s8b_floor_campaign._FLOOR_PROTOCOL_REL).unlink()
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="floor_protocol"):
        s8b_floor_campaign._floor_preflight_freeze_allowlist(
            tmp_path, freeze_path=freeze_rel, freeze_sha256=freeze_sha,
            protocol_sha256=protocol_sha,
        )


def test_floor_preflight_rejects_prediction_that_fails_verification(tmp_path):
    freeze_rel, freeze_sha, protocol_sha = _install_valid_prediction_preflight_fixture(
        tmp_path,
    )
    prediction_path = tmp_path / s8b_floor_campaign._SELECTOR_PREDICTIONS_REL
    prediction = json.loads(prediction_path.read_bytes())
    prediction["generated_at"] = "tampered"
    prediction_path.write_text(json.dumps(prediction), encoding="utf-8")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="verify 不通過"):
        s8b_floor_campaign._floor_preflight_freeze_allowlist(
            tmp_path, freeze_path=freeze_rel, freeze_sha256=freeze_sha,
            protocol_sha256=protocol_sha,
        )


def test_floor_preflight_requires_selector_journal(tmp_path):
    freeze_rel, freeze_sha, protocol_sha = _install_valid_prediction_preflight_fixture(
        tmp_path, include_journal=False,
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="journal.jsonl"):
        s8b_floor_campaign._floor_preflight_freeze_allowlist(
            tmp_path, freeze_path=freeze_rel, freeze_sha256=freeze_sha,
            protocol_sha256=protocol_sha,
        )


def test_floor_preflight_rejects_undeclared_selector_run_file(tmp_path):
    freeze_rel, freeze_sha, protocol_sha = _install_valid_prediction_preflight_fixture(
        tmp_path,
    )
    rogue = tmp_path / s8b_floor_campaign._SELECTOR_RUNS_REL / "rogue.json"
    rogue.write_bytes(b"undeclared")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="宣言集合"):
        s8b_floor_campaign._floor_preflight_freeze_allowlist(
            tmp_path, freeze_path=freeze_rel, freeze_sha256=freeze_sha,
            protocol_sha256=protocol_sha,
        )


def test_floor_preflight_rejects_duplicate_key_in_prediction(tmp_path):
    freeze_rel, freeze_sha, protocol_sha = _install_valid_prediction_preflight_fixture(
        tmp_path,
    )
    prediction_path = tmp_path / s8b_floor_campaign._SELECTOR_PREDICTIONS_REL
    raw = prediction_path.read_bytes()
    prediction_path.write_bytes(b'{"schema_version":"duplicate",' + raw[1:])
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="duplicate.*key"):
        s8b_floor_campaign._floor_preflight_freeze_allowlist(
            tmp_path, freeze_path=freeze_rel, freeze_sha256=freeze_sha,
            protocol_sha256=protocol_sha,
        )


def test_floor_preflight_rejects_duplicate_key_in_journal(tmp_path):
    freeze_rel, freeze_sha, protocol_sha = _install_valid_prediction_preflight_fixture(
        tmp_path,
    )
    journal_path = tmp_path / s8b_floor_campaign._SELECTOR_JOURNAL_REL
    lines = journal_path.read_bytes().splitlines(keepends=True)
    lines[0] = b'{"record_type":"duplicate",' + lines[0][1:]
    journal_path.write_bytes(b"".join(lines))
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="duplicate key"):
        s8b_floor_campaign._floor_preflight_freeze_allowlist(
            tmp_path, freeze_path=freeze_rel, freeze_sha256=freeze_sha,
            protocol_sha256=protocol_sha,
        )


def test_pilot_does_not_apply_official_freeze_allowlist_scan(tmp_path):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    repo_root = tmp_path / "pilot-repo"
    _init_real_clean_repo(repo_root, freeze, protocol)
    rogue = repo_root / "output" / "s8b-freeze" / "not-allowlisted.txt"
    rogue.write_bytes(b"pilot must not run official preflight")
    out_root = tmp_path / "pilot-out"
    outcome = _private_run_campaign(
        protocol, _verified_freeze(freeze), out_root=out_root, mode="pilot",
        measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(),
        probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
        monotonic_fn=lambda: 0.0, prepare_fn=_fake_prepare,
        now_fn=lambda: _FIXED_NOW, host_provenance_fn=_fixed_host,
        process_identity_fn=_fixed_process, execution_receipt_fn=_fixed_receipt,
        build_fn=_make_fake_build(tmp_path / "pilot-build"), repo_root=repo_root,
        durable_root_policy=_durable_policy(out_root),
    )
    assert outcome["status"] == "completed"
    assert rogue.read_bytes() == b"pilot must not run official preflight"


def test_repo_root_seam_runs_production_clean_scan_on_real_tmp_repo(tmp_path):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    repo_root = tmp_path / "real-repo"
    _init_real_clean_repo(repo_root, freeze, protocol)
    fixed_freeze = repo_root / s8b_floor_campaign._HOLDOUT_FREEZE_REL
    fixed_freeze.write_bytes((repo_root / protocol["freeze"]["path"]).read_bytes())
    bounded_allowlist = {
        s8b_floor_campaign._HOLDOUT_FREEZE_REL: _freeze_sha(freeze),
    }
    repository_files = (
        s8b_floor_campaign._holdout_freeze.enumerate_repository_files(repo_root)
    )
    assert "output/namespace.json" in repository_files
    assert "output/namespace.json" not in bounded_allowlist
    assert subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "--error-unmatch",
         "output/namespace.json"],
        text=True, capture_output=True, check=False,
    ).returncode == 0
    expected = s8b_floor_campaign.clean_scan_digest(
        repo_root, freeze_allowlist=bounded_allowlist,
    )
    assert expected == _expected_clean_digest(repository_files, bounded_allowlist)
    fake_build = _make_fake_build(tmp_path / "ignored")
    with mock.patch.object(s8b_floor_campaign.buildcache, "build_v2", fake_build):
        outcome = _private_run_campaign(
            protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
            mode="official",
            measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
            probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
            monotonic_fn=lambda: 0.0, prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, host_provenance_fn=_fixed_host,
            process_identity_fn=_fixed_process, execution_receipt_fn=_fixed_receipt,
            repo_root=repo_root, durable_root_policy=_durable_policy(tmp_path / "out"),
            _floor_preflight_fn=lambda *args, **kwargs: bounded_allowlist,
        )
    cert = json.loads((Path(outcome["run_dir"]) / "launch_certificate.json").read_bytes())
    assert cert["clean_scan_digest"] == expected


def test_real_seal_protocol_to_floor_official_core_e2e(tmp_path, monkeypatch):
    """固定 seal の consumer replay を official core test seam で通す。

    producer の seal()/provider 実走や commit 作成は行わず、D79(7) の部分閉鎖だけを
    characterization する。R3 の初回捏造と R4 の HOME 盲検境界は残り、closed とはしない。
    journal↔prediction row の直接 assertion は固定 seal の characterization であり、
    resolver が強制する claim=decision_method・invocation=順序/重複の範囲を拡張しない。
    probe fixture は実 calibration + 実 issuer/consumer + fixture observation であって、
    物理 Pegasus の実 attestation ではない。

    verify/resolver/revalidate/receipt-consumer/self-check の call-count spy は、gate が
    呼ばれたことだけを pin する diagnostic invocation pin であり mutation kill ではない。
    gate の teeth (無効入力拒否) は既存 HEAD negative tests が担保する。本テストの新規 kill は、
    workload rratio・floor・build src_token・clean digest の独立期待値 assertion が捕捉する
    受理集合変化に限る。
    """
    seal_commit = "82803d6d245d80a82954d61e065404fb15b3eeab"
    pre_oracle_head = "776640790752a969baee9246b2531b5dde49244d"
    ccbench_pin = "d706650cdb31e442bef45b9b4216951d4fb40969"
    protocol_sha256 = "261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac"
    freeze_sha256 = "315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688"
    prediction_sha256 = "5884c83f010f73914fe121e9eb7b2fe047a4739087a984d17287cfa338fd73f1"
    journal_sha256 = "d41135998cff3047cf792047239a3147a1154929e560b4a2e413e4ac14f9e000"
    calibration_sha256 = (
        "753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49"
    )
    contract_sha256 = (
        "e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01"
    )

    held_checks = []
    clone_root = _clone_committed_head_with_ccbench(
        tmp_path / "committed-head", ccbench_pin=ccbench_pin,
        held_checks=held_checks,
    )
    assert {marker["check_id"] for marker in held_checks} == {
        "s8b-floor.sealed-protocol-ccbench-pin-current-head",
    }
    out_root = tmp_path / "campaign-output"
    claim_root = out_root / "claims"
    build_workspace = tmp_path / "prepared-build-workspace"
    planned_run_root = out_root / "env" / "pegasus" / "calibration" / "s8b-floor-official"
    planned_build_cache = out_root / "s8b-build-cache"
    claim_root.mkdir(parents=True, mode=0o700)
    build_workspace.mkdir()

    # production が作る三つの leaf は sibling scope で、source/clone の外に閉じる。
    generated_roots = (planned_run_root, planned_build_cache, claim_root, build_workspace)
    for generated in generated_roots:
        assert generated.is_relative_to(tmp_path)
        assert not generated.is_relative_to(clone_root)
        assert not generated.is_relative_to(ROOT)
    for left in (planned_run_root, planned_build_cache, claim_root):
        for right in (planned_run_root, planned_build_cache, claim_root):
            if left != right:
                assert not left.is_relative_to(right)

    source_head = _git_stdout(ROOT, "rev-parse", "HEAD").strip()
    assert _git_stdout(clone_root, "rev-parse", "HEAD^").strip() == source_head
    assert _git_stdout(
        clone_root, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD",
    ).splitlines() == ["external/ccbench"]
    seal_protocol_paths = set(_git_stdout(
        clone_root, "ls-tree", "-r", "--name-only", seal_commit, "--",
        s8b_floor_campaign._FLOOR_PROTOCOLS_REL,
    ).splitlines())
    current_protocol_paths = set(_git_stdout(
        clone_root, "ls-tree", "-r", "--name-only", "HEAD", "--",
        s8b_floor_campaign._FLOOR_PROTOCOLS_REL,
    ).splitlines())
    post_seal_protocol_paths = tuple(sorted(
        current_protocol_paths - seal_protocol_paths
    ))
    assert seal_protocol_paths - current_protocol_paths == set()
    assert post_seal_protocol_paths == (
        f"{s8b_floor_campaign._FLOOR_PROTOCOLS_REL}/{contract_sha256}--"
        "511c9538e4e8efa54b45cda62e72389ed3b706ec.json",
    )
    replay_parent = _git_stdout(clone_root, "rev-parse", "HEAD").strip()
    _remove_post_seal_floor_protocols_from_replay(
        clone_root, post_seal_protocol_paths,
    )
    assert _git_stdout(clone_root, "rev-parse", "HEAD^").strip() == replay_parent
    assert [
        tuple(line.split("\t", 1))
        for line in _git_stdout(
            clone_root, "diff-tree", "--no-commit-id", "--name-status", "-r", "HEAD",
        ).splitlines()
    ] == [("D", post_seal_protocol_paths[0])]
    assert not (clone_root / post_seal_protocol_paths[0]).exists()
    assert _git_stdout(clone_root, "rev-parse", "--is-shallow-repository").strip() == "false"
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", seal_commit, "HEAD"],
        cwd=clone_root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert _git_stdout(clone_root, "rev-parse", f"{seal_commit}^").strip() == pre_oracle_head
    gitlink_fields = _git_stdout(
        clone_root, "ls-tree", "HEAD", "external/ccbench",
    ).split()

    def verify_sealed_gitlink_identity():
        if s8b_floor_campaign._freeze_hold.HELD:
            return s8b_floor_campaign._freeze_hold.held_marker(
                "s8b-floor.sealed-protocol-ccbench-pin-current-head",
            )
        assert gitlink_fields[:3] == ["160000", "commit", ccbench_pin]
        return None

    held_gitlink = verify_sealed_gitlink_identity()
    assert held_gitlink is not None
    assert held_gitlink["check_id"] == (
        "s8b-floor.sealed-protocol-ccbench-pin-current-head"
    )
    with mock.patch.object(s8b_floor_campaign._freeze_hold, "HELD", False):
        assert verify_sealed_gitlink_identity() is None
    assert _git_stdout(
        clone_root / "external" / "ccbench", "rev-parse", "HEAD",
    ).strip() == ccbench_pin

    protocol_path = clone_root / s8b_floor_campaign._FLOOR_PROTOCOL_REL
    freeze_path = clone_root / s8b_floor_campaign._HOLDOUT_FREEZE_REL
    prediction_path = clone_root / s8b_floor_campaign._SELECTOR_PREDICTIONS_REL
    journal_path = clone_root / s8b_floor_campaign._SELECTOR_JOURNAL_REL
    protocol_raw = protocol_path.read_bytes()
    protocol = s8b_floor_campaign.load_protocol(protocol_path)
    expected_protocol = {
        "schema": "s8b-floor-protocol/v2",
        "formula": "s8b-floor-stats/v2",
        "env_tag": "pegasus",
        "contract_sha256": contract_sha256,
        "ccbench_pin": ccbench_pin,
        "freeze": {
            "path": "output/s8b-freeze/holdout_freeze.json",
            "sha256": freeze_sha256,
        },
        "stock_configuration": "stock_common",
        "n_sessions": 8,
        "reps": 5,
        "master_seed": "2026-07-18T17:16:12+09:00",
        "schedule_algorithm": "round-permutation/v2",
        "extime_s": 5,
        "wired_min_rel_floor": 0.03,
        "retry_slots_per_cell": 2,
        "session_cv_max": "0.10",
        "cell_cv_max": "0.15",
        "scale_adequacy_rel_tolerance": "0.10",
        "allowed_excluded_reasons": [
            "competing_process", "launch_failure",
            "nonfinite_or_partial_output", "performance_anomaly",
        ],
    }
    assert protocol == expected_protocol
    assert hashlib.sha256(protocol_raw).hexdigest() == protocol_sha256
    assert s8b_floor_campaign._canonical_sha256(protocol) == protocol_sha256
    assert hashlib.sha256(freeze_path.read_bytes()).hexdigest() == freeze_sha256
    assert hashlib.sha256(prediction_path.read_bytes()).hexdigest() == prediction_sha256
    assert hashlib.sha256(journal_path.read_bytes()).hexdigest() == journal_sha256

    freeze = s8b_floor_campaign._load_verified_freeze(
        freeze_path, expected_hash=freeze_sha256,
    )
    prediction = json.loads(prediction_path.read_bytes())
    records = s8b_floor_campaign._parse_selector_journal_bytes(
        journal_path.read_bytes(),
    )
    assert prediction["pre_oracle_head"] == pre_oracle_head
    assert prediction["body_sha256"] == (
        "69c7ad3ea05ee652fc761aa96a6f03ff4f07ba2a50d41d2c0027c215a6e64a5a"
    )
    assert prediction["selector_basis_sha256"] == (
        "779c639649d7013c12e0f509de6cac69ddd6f4fa6f1fc614012ebc2eca591b46"
    )
    record_counts = {
        kind: sum(record["record_type"] == kind for record in records)
        for kind in ("run_header", "claim", "envelope", "invocation", "static_terminal")
    }
    assert len(records) == 15
    assert record_counts == {
        "run_header": 1, "claim": 4, "envelope": 4,
        "invocation": 4, "static_terminal": 2,
    }

    declared_paths = {
        record[field]
        for record in records
        for kind, field in (
            ("claim", "payload_path"),
            ("envelope", "envelope_path"),
            ("invocation", "raw_response_path"),
        )
        if record["record_type"] == kind
    }
    frozen_paths = {
        s8b_floor_campaign._HOLDOUT_FREEZE_REL,
        s8b_floor_campaign._FLOOR_PROTOCOL_REL,
        s8b_floor_campaign._SELECTOR_PREDICTIONS_REL,
        s8b_floor_campaign._SELECTOR_JOURNAL_REL,
        *declared_paths,
    }
    assert len(declared_paths) == 12
    assert len(frozen_paths) == 16
    calibration_rel = ec.lookup("pegasus").calibration_ref.path
    assert hashlib.sha256((clone_root / calibration_rel).read_bytes()).hexdigest() == (
        calibration_sha256
    )
    snapshot_paths = frozen_paths | {calibration_rel}
    source_before = _bytes_snapshot(ROOT, snapshot_paths)
    clone_before = _bytes_snapshot(clone_root, snapshot_paths)
    assert source_before == clone_before

    seal_targets = {
        s8b_floor_campaign._SELECTOR_PREDICTIONS_REL,
        s8b_floor_campaign._SELECTOR_JOURNAL_REL,
        *declared_paths,
    }
    seal_diff = [
        tuple(line.split("\t", 1))
        for line in _git_stdout(
            clone_root, "diff-tree", "--no-commit-id", "--name-status", "-r",
            seal_commit, "--", "output/s8b-freeze",
        ).splitlines()
    ]
    assert len(seal_diff) == 14
    assert {status for status, _path in seal_diff} == {"A"}
    assert {path for _status, path in seal_diff} == seal_targets
    assert _git_stdout(
        clone_root, "diff", "--name-only", f"{seal_commit}..HEAD", "--",
        *sorted(seal_targets),
    ) == ""

    # 固定 seal の追加 characterization。official resolver の enforcement 主張ではない。
    rows_by_cell = {
        (row["target_holdout"], row["arm"]): row for row in prediction["rows"]
    }
    by_type_cell = {
        (record["record_type"], record.get("target_holdout"), record.get("arm")): record
        for record in records[1:]
    }
    for cell, row in rows_by_cell.items():
        if cell[1] == "off":
            static = by_type_cell[("static_terminal", *cell)]
            assert static["decision_method"] == row["decision_method"]
            assert static["choice_id"] == row["choice_id"]
            continue
        claim = by_type_cell[("claim", *cell)]
        envelope_record = by_type_cell[("envelope", *cell)]
        invocation = by_type_cell[("invocation", *cell)]
        assert claim["decision_method"] == row["decision_method"]
        assert claim["input_payload_sha256"] == row["input_payload_sha256"]
        assert hashlib.sha256(
            (clone_root / claim["payload_path"]).read_bytes()
        ).hexdigest() == claim["input_payload_sha256"]
        assert hashlib.sha256(
            (clone_root / invocation["raw_response_path"]).read_bytes()
        ).hexdigest() == invocation["raw_sha256"] == row["raw_sha256"]
        assert {
            key: invocation[key]
            for key in ("status", "choice_id", "rationale", "parser_error_code",
                        "raw_response_path", "raw_sha256")
        } == {
            key: row[key]
            for key in ("status", "choice_id", "rationale", "parser_error_code",
                        "raw_response_path", "raw_sha256")
        }
        assert invocation["receipt"] == row["agent_provenance"]
        envelope_raw = (clone_root / envelope_record["envelope_path"]).read_bytes()
        assert hashlib.sha256(envelope_raw).hexdigest() == envelope_record["envelope_sha256"]
        envelope = json.loads(envelope_raw)
        raw_response = (clone_root / invocation["raw_response_path"]).read_bytes()
        assert envelope["result"].encode("utf-8") == raw_response
        assert envelope["session_id"] == invocation["receipt"]["child_id"]
        parsed_raw = json.loads(raw_response)
        assert parsed_raw["choice_id"] == invocation["choice_id"]
        assert parsed_raw["rationale"] == invocation["rationale"]

    contract = ec.lookup("pegasus")
    assert contract.contract_sha256 == contract_sha256
    verified_calibration = env_attestation.load_verified_calibration(
        contract, clone_root,
    )
    probe_calls = []

    def attestation_probe():
        """calibration 由来の clean な in-tolerance runtime 観測を返す。

        実 calibration・comparator・issuer/consumer は production を通すが、
        これは物理 Pegasus の実 attestation ではない。
        """
        from statistics import median

        probe_calls.append(True)
        calibration_profile = verified_calibration.attestation_profile
        calibration_clock = calibration_profile.effective_clock
        calibration_samples = list(calibration_clock.samples_mhz)
        calibration_median = median(calibration_samples)
        allowed_delta = (
            abs(calibration_median) * calibration_clock.tolerance_pct / 100.0
        )
        lower = calibration_median - allowed_delta
        upper = calibration_median + allowed_delta
        clean_samples = [
            min(max(sample, lower), upper)
            for sample in calibration_samples
        ]
        assert len(clean_samples) == calibration_profile.cores.logical == 48
        assert all(lower <= sample <= upper for sample in clean_samples)
        assert any(sample != calibration_median for sample in clean_samples)
        clean_clock = dataclasses.replace(
            calibration_clock,
            samples_mhz=clean_samples,
        )
        return _observed(dataclasses.replace(
            calibration_profile, effective_clock=clean_clock,
        ))

    monkeypatch.setattr(s8b_floor_campaign.env_attestation, "probe", attestation_probe)
    reservation_values = _install_real_seal_reservation(
        monkeypatch, repo_root=clone_root, env_tag=contract.env_tag,
    )

    def producer_tripwire(*_args, **_kwargs):
        raise AssertionError("consumer replay が producer を呼んだ")

    monkeypatch.setattr(s8b_prediction_runner, "seal", producer_tripwire)
    monkeypatch.setattr(s8b_prediction_runner, "drive_journal", producer_tripwire)
    monkeypatch.setattr(
        s8b_prediction_runner.ClaudeHeadlessProvider, "__call__", producer_tripwire,
    )

    verify_original = s8b_selector_freeze.verify_prediction_freeze
    resolver_original = s8b_prediction_runner.resolve_journal_for_launch
    preflight_original = s8b_floor_campaign._floor_preflight_freeze_allowlist
    clean_original = s8b_floor_campaign.clean_scan_digest
    revalidate_original = s8b_floor_campaign._revalidate_issued_certificate
    receipt_consumer_original = s8b_floor_campaign._validate_execution_receipt
    self_check_original = s8b_floor_stats.verify_floor_artifact_with_live_admission
    verify_calls = []
    resolver_calls = []
    preflight_calls = []
    clean_calls = []
    revalidate_calls = []
    receipt_consumer_calls = []
    self_check_calls = []

    def verify_spy(*args, **kwargs):
        verify_calls.append((args, kwargs))
        return verify_original(*args, **kwargs)

    def resolver_spy(*args, **kwargs):
        resolver_calls.append((args, kwargs))
        return resolver_original(*args, **kwargs)

    def preflight_spy(*args, **kwargs):
        result = preflight_original(*args, **kwargs)
        preflight_calls.append(result)
        return result

    def clean_spy(*args, **kwargs):
        result = clean_original(*args, **kwargs)
        clean_calls.append(result)
        return result

    def revalidate_spy(*args, **kwargs):
        revalidate_calls.append((args, kwargs))
        return revalidate_original(*args, **kwargs)

    def receipt_consumer_spy(*args, **kwargs):
        receipt_consumer_calls.append((args, kwargs))
        return receipt_consumer_original(*args, **kwargs)

    def self_check_spy(*args, **kwargs):
        self_check_calls.append((args, kwargs))
        return self_check_original(*args, **kwargs)

    monkeypatch.setattr(s8b_selector_freeze, "verify_prediction_freeze", verify_spy)
    monkeypatch.setattr(s8b_prediction_runner, "resolve_journal_for_launch", resolver_spy)
    monkeypatch.setattr(
        s8b_floor_campaign, "_floor_preflight_freeze_allowlist", preflight_spy,
    )
    monkeypatch.setattr(s8b_floor_campaign, "clean_scan_digest", clean_spy)
    monkeypatch.setattr(
        s8b_floor_campaign, "_revalidate_issued_certificate", revalidate_spy,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_validate_execution_receipt", receipt_consumer_spy,
    )
    monkeypatch.setattr(
        s8b_floor_stats, "verify_floor_artifact_with_live_admission",
        self_check_spy,
    )

    cells = s8b_floor_campaign.enumerate_cells(
        freeze.document, stock_configuration="stock_common",
    )
    expected_rratios = _independent_real_seal_rratios(freeze.document)
    expected_cell_ids = list(expected_rratios)
    assert {
        cell["cell_id"]: cell["workload"]["ycsb_rratio"]
        for cell in cells
    } == expected_rratios
    prepare = _make_real_freeze_prepare(
        freeze.document, cells, ccbench_pin=ccbench_pin,
        ccbench_dir=clone_root / "external" / "ccbench",
        cache_root=build_workspace,
    )
    build_calls = []
    fake_build = _make_fake_build(build_workspace)

    def recording_build(genome, ccbench_commit, trace, **kwargs):
        assert trace is False
        assert ccbench_commit == ccbench_pin
        build_calls.append({
            "ccbench_commit": ccbench_commit,
            "trace": trace,
            "src_token": kwargs.get("src_token"),
            "ccbench_dir": kwargs.get("ccbench_dir"),
        })
        return fake_build(genome, ccbench_commit, trace, **kwargs)

    measure = _make_measure_fn(
        reps=5, value_fn=lambda _cell_id: 1000.0,
        env_tag="pegasus", extime_s=5,
    )
    monkeypatch.setattr(s8b_floor_campaign.buildcache, "build_v2", recording_build)
    outcome = s8b_floor_campaign._run_campaign_core(
        protocol, freeze, out_root=out_root, mode="official",
        measure_fn=measure, probe_fn=lambda: (1, "", ""),
        sleep_fn=lambda _seconds: None, monotonic_fn=lambda: 0.0,
        prepare_fn=prepare, now_fn=lambda: _FIXED_NOW,
        host_provenance_fn=_fixed_host, process_identity_fn=_fixed_process,
        execution_receipt_fn=None,
        repo_root=clone_root, durable_root_policy=_durable_policy(out_root),
        _floor_preflight_fn=None,
        confirm_official_floor_run=True,
    )

    assert outcome["status"] == "completed"
    assert len(verify_calls) == 1
    assert len(resolver_calls) == 1
    assert len(preflight_calls) == 1
    assert len(revalidate_calls) == 1
    assert len(receipt_consumer_calls) == 1
    assert len(self_check_calls) == 1
    assert len(clean_calls) == 2
    allowlist = preflight_calls[0]
    expected_allowlist = {
        relative: hashlib.sha256((clone_root / relative).read_bytes()).hexdigest()
        for relative in frozen_paths
    }
    expected_clean_digest = _expected_clean_digest(
        s8b_floor_campaign._holdout_freeze.enumerate_repository_files(clone_root),
        expected_allowlist,
    )
    assert allowlist == expected_allowlist
    assert clean_calls == [expected_clean_digest, expected_clean_digest]
    assert probe_calls == [True]

    assert len(prepare.calls) == len(cells) == 12
    assert sorted(cell_id for cell_id, _pin in prepare.calls) == expected_cell_ids
    assert len(build_calls) == 12
    assert sorted(call["src_token"] for call in build_calls) == expected_cell_ids
    assert {call["ccbench_commit"] for call in build_calls} == {ccbench_pin}
    assert {call["trace"] for call in build_calls} == {False}
    assert {
        Path(call["ccbench_dir"]).resolve() for call in build_calls
    } == {(clone_root / "external" / "ccbench").resolve()}
    assert len(measure.call_details) == 12 * 8
    assert all(
        call["workload"]["ycsb_rratio"] == expected_rratios[call["cell_id"]]
        for call in measure.call_details
    )

    run_dir = Path(outcome["run_dir"])
    manifest = json.loads((run_dir / "manifest.json").read_bytes())
    expected_schedule = _real_seal_schedule_golden(expected_cell_ids)
    assert manifest["schedule"] == expected_schedule
    assert manifest["master_seed"] == _REAL_SEAL_MASTER_SEED
    assert manifest["ccbench_pin"] == ccbench_pin
    assert manifest["protocol_sha256"] == protocol_sha256
    assert manifest["freeze_sha256"] == freeze_sha256
    assert {
        cell["cell_id"]: cell["workload"]["ycsb_rratio"]
        for cell in manifest["cells"]
    } == expected_rratios

    result = outcome["result"]
    assert result["eligible_for_refreeze"] is False
    assert result["mode"] == "official"
    assert result["env_tag"] == "pegasus"
    assert result["ccbench_pin"] == ccbench_pin
    assert result["protocol_sha256"] == protocol_sha256
    assert result["freeze_sha256"] == freeze_sha256
    assert result["manifest_sha256"] == hashlib.sha256(
        (run_dir / "manifest.json").read_bytes()
    ).hexdigest()
    assert result["wired_min_rel_floor"] == 0.03
    assert result["config"]["wired_min_rel_floor"] == 0.03
    assert result["n_sessions"] == 8
    assert result["reps"] == 5
    assert all(
        session["throughputs"] == [1000.0] * 5 and session["session_cv"] == 0.0
        for session in result["sessions"]
    )
    assert all(
        session["workload"]["ycsb_rratio"] == expected_rratios[session["cell_id"]]
        for session in result["sessions"]
    )
    expected_floors = _independent_constant_tps_floors(
        freeze.document, stock_configuration="stock_common",
        throughput=1000.0, wired_min_rel_floor=0.03,
    )
    assert {
        holdout_id: {
            "pairs": floor["pairs"],
            "scalar_alt": floor["scalar_alt"],
            "scale_ref": floor["scale_ref"],
        }
        for holdout_id, floor in result["floors"].items()
    } == expected_floors
    assert all(
        floor["scalar_alt"] == 30.0 and floor["scale_ref"] == 1000.0
        and set(floor["pairs"].values()) == {30.0}
        for floor in result["floors"].values()
    )

    journal = _read_journal_lines(run_dir / "journal.jsonl")
    launch = next(record for record in journal if record.get("event") == "launch-start")
    campaign_start = next(
        record for record in journal if record.get("event") == "campaign-start"
    )
    reservation_start = next(
        record for record in journal if record.get("event") == "reservation-preflight"
    )
    certificate_raw = (run_dir / "launch_certificate.json").read_bytes()
    certificate = json.loads(certificate_raw)
    certificate_raw_sha256 = hashlib.sha256(certificate_raw).hexdigest()
    assert certificate["clean_scan_digest"] == expected_clean_digest
    assert certificate["protocol_sha256"] == protocol_sha256
    assert certificate["v1_freeze_sha256"] == freeze_sha256
    assert launch["launch_certificate_sha256"] == certificate_raw_sha256
    assert campaign_start["launch_certificate_sha256"] == certificate_raw_sha256
    assert reservation_start["required_s"] == 30_000
    assert reservation_start["safety_margin_s"] == 600
    assert s8b_floor_campaign.execution_guard.receipt_matches_contract(
        campaign_start["execution_receipt"],
        env_tag="pegasus", contract_sha256=contract_sha256,
        attestation_mode="required", verified_calibration=verified_calibration,
    )
    assert campaign_start["execution_receipt"]["schema"] == (
        s8b_floor_campaign.execution_guard.RECEIPT_SCHEMA_V2
    )
    assert journal[-1] == {"event": "terminal", "status": "completed"}

    claims = list(claim_root.glob("*.claim"))
    assert len(claims) == 1
    claim = json.loads(claims[0].read_bytes())
    assert claim["job_id"] == reservation_values["IZANAGI_RESERVATION_JOB_ID"]
    assert claim["host"] == reservation_values["IZANAGI_RESERVATION_HOST"]
    assert claim["boot_id"] == reservation_values["IZANAGI_RESERVATION_BOOT_ID"]

    assert _bytes_snapshot(ROOT, snapshot_paths) == source_before
    assert _bytes_snapshot(clone_root, snapshot_paths) == clone_before
    assert source_before == clone_before


def test_deterministic_artifacts_across_roots_and_subprocess_environments(tmp_path):
    roots = [
        tmp_path / "短",
        tmp_path / "a much longer root with spaces Ω",
    ]
    environments = [
        {"PYTHONHASHSEED": "1", "LC_ALL": "C", "TZ": "UTC"},
        {"PYTHONHASHSEED": "777", "LC_ALL": "C.UTF-8", "TZ": "Asia/Tokyo"},
    ]
    script = textwrap.dedent(f"""
        import importlib.util, json, pathlib, sys
        from types import SimpleNamespace
        spec = importlib.util.spec_from_file_location("floor_test_helper", {str(Path(__file__))!r})
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.s8b_floor_campaign.site_policy.socket = SimpleNamespace(
            gethostname=lambda: "test-host"
        )
        module.s8b_floor_campaign.site_policy._has_nqsv = lambda: False
        print(json.dumps(module._deterministic_official_artifacts(pathlib.Path(sys.argv[1])), sort_keys=True))
    """)
    observations = []
    for root, delta in zip(roots, environments):
        temp_dir = root / "process-tmp"
        temp_dir.mkdir(parents=True)
        env = dict(os.environ)
        env.update(delta)
        env["TMPDIR"] = str(temp_dir)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            completed = subprocess.run(
                [sys.executable, "-c", script, str(root)], env=env,
                capture_output=True, text=True, check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise AssertionError(
                f"determinism child exited {exc.returncode}\n"
                f"stdout:\n{exc.stdout}\nstderr:\n{exc.stderr}"
            ) from exc
        observations.append(json.loads(completed.stdout))
    assert observations[0]["sha256"] == observations[1]["sha256"]
    for name in observations[0]["inodes"]:
        assert observations[0]["inodes"][name] != observations[1]["inodes"][name]


def test_each_determinism_seam_reaches_its_expected_json_pointer(tmp_path):
    observation = _deterministic_official_artifacts(tmp_path / "sentinel-root")
    run_dir = Path(observation["run_dir"])
    manifest = json.loads((run_dir / "manifest.json").read_bytes())
    result = json.loads((run_dir / "result.json").read_bytes())
    journal = _read_journal_lines(run_dir / "journal.jsonl")
    campaign_start = next(r for r in journal if r.get("event") == "campaign-start")

    # host_provenance_fn / process_identity_fn / execution_receipt_fn の pointer を個別固定。
    assert campaign_start["hostname"] == "sentinel-host"
    assert campaign_start["boot_id"] == "sentinel-boot"
    assert campaign_start["job_id"] == "sentinel-job"
    assert campaign_start["cpuset"] == "sentinel-cpuset"
    assert campaign_start["pid"] == 4242
    assert campaign_start["starttime"] == 31337
    assert campaign_start["execution_uuid"] == "a" * 32
    receipt = campaign_start["execution_receipt"]
    assert receipt["attestation"]["hostname"] == "sentinel-receipt-host"
    assert receipt["attestation"]["boot_id"] == "sentinel-receipt-boot"
    assert receipt["attestation"]["cpuset"] == "sentinel-receipt-cpuset"

    # build_fn は exact PortableBuiltRecord に投影され、result と manifest は同じ artifact view。
    assert result["binaries"] == manifest["binaries"]
    for cell_id, record in manifest["binaries"].items():
        assert set(record) == set(
            s8b_binary_admission.portable_built_keys_for(
                record["configuration_id"],
            )
        ), cell_id
        assert not Path(record["binary"]).is_absolute()
        assert not Path(record["store_path"]).is_absolute()
        assert any("${OUT_ROOT}" in token for token in record["configure_argv"])
        assert any("${CCBENCH_ROOT}" in token for token in record["configure_argv"])
        assert "configure_cmd" not in record and "build_cmd" not in record
    assert result["eligible_for_refreeze"] is False


def test_new_seam_defaults_delegate_to_production_functions(tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    monkeypatch.setattr(
        s8b_floor_campaign.site_policy,
        "current_site",
        lambda: s8b_floor_campaign.site_policy.OTHER,
    )
    repo_root = tmp_path / "default-root"
    _init_real_clean_repo(repo_root, freeze, protocol)
    calls = {name: 0 for name in (
        "calibration", "machine_pin", "host", "process", "receipt", "build", "after",
    )}
    expected_machine_env_tag = "linux-baremetal"
    fake_build = _make_fake_build(tmp_path / "ignored")
    real_load = s8b_floor_campaign.env_attestation.load_verified_calibration
    real_pin = s8b_floor_campaign.execution_guard.assert_machine_pin

    def calibration_spy(contract, root):
        calls["calibration"] += 1
        assert contract.attestation_mode == "none"
        return real_load(contract, root)

    def machine_pin_spy(contract, *, machine_env_tag):
        calls["machine_pin"] += 1
        assert machine_env_tag == expected_machine_env_tag
        return real_pin(contract, machine_env_tag=machine_env_tag)

    def host_spy(*, now_fn):
        calls["host"] += 1
        return _fixed_host(now_fn=now_fn)

    def process_spy():
        calls["process"] += 1
        return _fixed_process()

    def receipt_spy(contract, *, now_fn):
        calls["receipt"] += 1
        return _fixed_receipt(contract, now_fn=now_fn)

    def build_spy(*args, **kwargs):
        calls["build"] += 1
        return fake_build(*args, **kwargs)

    def after_spy(cert_path):
        calls["after"] += 1
        assert cert_path.is_file()

    monkeypatch.setattr(s8b_floor_campaign, "ROOT", repo_root)
    monkeypatch.setattr(
        s8b_floor_campaign.env_attestation, "load_verified_calibration", calibration_spy,
    )
    monkeypatch.setattr(
        s8b_floor_campaign.execution_guard, "assert_machine_pin", machine_pin_spy,
    )
    monkeypatch.setattr(s8b_floor_campaign, "_host_provenance", host_spy)
    monkeypatch.setattr(s8b_floor_campaign, "_process_identity", process_spy)
    monkeypatch.setattr(s8b_floor_campaign.execution_guard, "build_receipt", receipt_spy)
    monkeypatch.setattr(s8b_floor_campaign.buildcache, "build_v2", build_spy)
    monkeypatch.setattr(
        s8b_floor_campaign, "_after_certificate_issued_noop", after_spy)
    outcome = _private_run_campaign(
        protocol, _verified_freeze(freeze), out_root=tmp_path / "out", mode="official",
        measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
        probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
        monotonic_fn=lambda: 0.0, prepare_fn=_fake_prepare, now_fn=lambda: _FIXED_NOW,
        durable_root_policy=_durable_policy(tmp_path / "out"),
        _floor_preflight_fn=_fixture_floor_preflight,
    )
    assert outcome["status"] == "completed"
    assert calls == {
        "calibration": 1, "machine_pin": 1, "host": 1, "process": 1,
        "receipt": 1, "build": 12, "after": 1,
    }


@pytest.mark.parametrize("validator,value", [
    (s8b_floor_campaign._validate_host_provenance,
     {"hostname": "h", "boot_id": None, "job_id": None, "cpuset": None}),
    (s8b_floor_campaign._validate_process_identity,
     {"pid": 1, "starttime": 2}),
])
def test_partial_seam_bundle_is_rejected_by_exact_validator(validator, value):
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="key 集合"):
        validator(value)


def test_partial_execution_receipt_bundle_is_rejected():
    contract = ec.lookup(ENV_TAG)
    receipt = _fixed_receipt(contract, now_fn=lambda: _FIXED_NOW)
    receipt["attestation"].pop("cpuset")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="整合しない"):
        s8b_floor_campaign._validate_execution_receipt(receipt, contract=contract)


def _honest_portable_built_record(
        tmp_path: Path, *, configuration_id: str = "configuration",
) -> dict:
    binary = tmp_path / "honest-portable.bin"
    binary.write_bytes(b"honest portable binary")
    sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    genome_canonical = '{"fixture":"portable"}'
    token = hashlib.sha256(b"portable-token").hexdigest()
    entry_sha = hashlib.sha256(b"portable-entry").hexdigest()
    binding = {
        "genome_canonical": genome_canonical,
        "src_token": token,
        "variant_id": hashlib.sha256(
            f"{genome_canonical}|src={token}".encode("utf-8")
        ).hexdigest()[:12],
        "entry_sha256": entry_sha,
    }
    binding["binding_sha256"] = hashlib.sha256(json.dumps(
        binding, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    source_root = tmp_path / "portable-source"
    source_root.mkdir()
    compiler_input = source_root / "include" / "fixture.hh"
    compiler_input.parent.mkdir()
    compiler_input.write_bytes(b"portable compiler input\n")
    compiler_input_manifest = {
        "schema_version": "s8b-compiler-input/v1",
        "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
        "target": "ycsb_fixture.exe",
        "depfile_count": 1,
        "inputs": [{
            "path": "include/fixture.hh",
            "sha256": hashlib.sha256(compiler_input.read_bytes()).hexdigest(),
        }],
    }
    compiler_input_manifest_sha256 = hashlib.sha256(json.dumps(
        compiler_input_manifest, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    source = SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=str(source_root.resolve()), ccbench_commit="1" * 40,
        genome_sha256=hashlib.sha256(genome_canonical.encode("utf-8")).hexdigest(),
        src_token=token,
        source_bytes_sha256=hashlib.sha256(b"portable-source").hexdigest(),
        tracked_clean=False,
        tracked_diff_sha256=hashlib.sha256(b"portable-diff").hexdigest(),
        tracked_paths=("include/backoff.hh",),
    )
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    review = s8b_materialization.reviewed_source_capability(
        review_id=ReviewId.S8B_FLOOR, source=source, input_sha256=entry_sha,
    )
    admission = derive_build_admission(context, source, review_receipt=review)
    receipt = portable_binary_admission_receipt_fixture(
        admission=admission, expected_policy=context.policy, source=source,
        cell_id="cell", holdout_id="holdout", configuration_id=configuration_id,
        binding=binding, binary=binary, binary_sha256=sha,
        contract_sha256="2" * 64, trace=False,
        source_snapshot_sha256=hashlib.sha256(
            b"portable-expected-materialization"
        ).hexdigest(),
        expected_materialization_sha256=hashlib.sha256(
            b"portable-expected-materialization"
        ).hexdigest(),
        compiler_input_manifest=compiler_input_manifest,
        compiler_input_manifest_sha256=compiler_input_manifest_sha256,
    )
    record = {
            "cell_id": "cell", "holdout_id": "holdout",
            "configuration_id": configuration_id, "binary": "cache/cell/binary.exe",
            "binary_sha256": sha, "bin_hash_short": sha[:16], "binding": binding,
            "configure_argv": ["cmake", "-S", "${CCBENCH_ROOT}"],
            "build_argv": ["cmake", "--build", "${OUT_ROOT}/cache/cell"],
            "cached": False, "store_path": f"store/{sha}",
            "admission_receipt": receipt,
    }
    if configuration_id == "sort_best":
        record["sort_swo_oracle"] = expected_portable_sort_swo_pass_receipt(
            cell_id="cell", holdout_id="holdout",
            configuration_id=configuration_id,
            entry_sha256=entry_sha, binary_sha256=sha,
        )
    return {"cell": record}


@pytest.mark.parametrize("configuration_id", ["stock_common", "sort_best"])
@pytest.mark.parametrize("stored", [False, True])
@pytest.mark.parametrize("fetchcontent", [False, True])
def test_runtime_built_key_helper_is_configuration_conditional(
        configuration_id, stored, fetchcontent):
    expected = set(
        s8b_binary_admission.portable_built_keys_for(configuration_id)
    )
    if not stored:
        expected.remove("store_path")
    expected.add("_ccbench_root")
    if fetchcontent:
        expected.add("_fetchcontent_base_dir")
    assert s8b_floor_campaign._runtime_built_keys_for(
        configuration_id, stored=stored, fetchcontent=fetchcontent,
    ) == frozenset(expected)


def _live_admission_runner(
    tmp_path, *, runtime, built, schedule=(), records=None,
    measure_fn=None, cut6_replay_query_fn=None, retry_trigger_query_fn=None,
):
    cell = {
        "cell_id": "cell", "holdout_id": "holdout",
        "configuration_id": "sort_best", "records": 1, "threads": 1,
        "workload": dict(_HOLDOUT_SHAPE["rr79"]["ycsb"]),
    }
    protocol = _valid_protocol_dict()
    protocol["ccbench_pin"] = "1" * 40
    runner = s8b_floor_campaign._Runner(
        protocol=protocol,
        contract=SimpleNamespace(contract_sha256="2" * 64),
        cells=[cell], cell_by_id={"cell": cell},
        binaries={"cell": runtime}, artifact_binaries=built,
        schedule=list(schedule),
        journal_path=tmp_path / "journal.jsonl",
        measure_fn=measure_fn or (lambda *_args: None),
        holdout_admissions={"cell": SimpleNamespace(observation=None)},
        probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
        monotonic_fn=lambda: 0.0, now_fn=lambda: _FIXED_NOW,
        protocol_sha256="p", freeze_sha256="f", manifest_sha256="m",
        perf_preflight=_perf_receipt(), mode="pilot",
        holdout_assert_fn=lambda *_args, **_kwargs: None,
        records=records, host_provenance_fn=_fixed_host,
        process_identity_fn=_fixed_process,
        cut6_replay_query_fn=cut6_replay_query_fn,
        retry_trigger_query_fn=retry_trigger_query_fn,
    )
    return runner


_FLOOR_TEST_RECOVERY_AUTHORITY = (
    "test-scheduler-authority", "9" * 64,
)


def _write_verified_campaign_recovery_registry(
    *, authority: Path, protocol: dict, schedule: list[dict],
    protocol_sha256: str, trigger_start: dict,
) -> Path:
    """Write one core-valid cut-10 recovery for an actual campaign attempt."""

    authority_id, authority_policy_sha256 = _FLOOR_TEST_RECOVERY_AUTHORITY
    binding = s8b_attempt_profile.S8BAttemptBinding(
        freeze_sha256=protocol["freeze"]["sha256"],
        protocol_sha256=protocol_sha256,
        schedule_sha256=hashlib.sha256(
            attempt_registry_core.canonical_json_bytes(schedule)
        ).hexdigest(),
    )
    profile = s8b_attempt_profile.make_s8b_domain_profile(
        max_consumptions_per_budget_key=(
            protocol["n_sessions"] + protocol["retry_slots_per_cell"]
        ),
        recovery_authority_id=authority_id,
        recovery_authority_policy_sha256=authority_policy_sha256,
    )
    holdout_key, configuration_id = trigger_start["cell_id"].rsplit("::", 1)
    slot_identity = {
        "freeze_holdout_key": holdout_key,
        "configuration_id": configuration_id,
        "repetition": trigger_start["round"] - 1,
        "attempt_ordinal": 0,
    }
    slot = s8b_attempt_profile.S8BAttemptSlot(
        **slot_identity,
        schedule_row_sha256=hashlib.sha256(
            attempt_registry_core.canonical_json_bytes(slot_identity)
        ).hexdigest(),
    )
    slot_id = s8b_attempt_profile.S8B_SLOT_CODEC.slot_id(slot)
    rows = attempt_registry_core.create_attempt_registry_genesis(
        profile=profile, slots=[slot], binding=binding,
    )
    rows = attempt_registry_core.reserve_attempt_slot(
        rows, profile=profile, freeze_id=binding.freeze_sha256,
        slot_id=slot_id, binding=binding,
        run_start_receipt_sha256="8" * 64,
        process_identity={
            "pid": 101, "starttime": "campaign-start",
            "execution_uuid": "campaign-start-uuid",
        },
        started_at="2026-08-25T00:00:00+00:00",
    )
    start = next(row for row in rows if row.get("event") == "start")
    receipt = {
        "schema_version": (
            s8b_attempt_profile.S8B_RECOVERY_RECEIPT_SCHEMA_VERSION
        ),
        "event": s8b_attempt_profile.S8B_RECOVERY_RECEIPT_EVENT,
        "source": s8b_attempt_profile.S8B_RECOVERY_RECEIPT_SOURCE,
        "scheduler_request_id": "campaign-recovery-request",
        "target_start_event_sha256": start["event_sha256"],
        "raw_scheduler_accounting_record_sha256": "7" * 64,
        "authority_id": authority_id,
        "authority_policy_sha256": authority_policy_sha256,
        "failure_reason": "node_failure",
        "collected_at": "2026-08-25T00:00:01+00:00",
    }
    shared = s8b_floor_campaign._holdout_admission.shared_admission_root(
        authority
    )
    receipt_path = (
        s8b_floor_campaign._holdout_admission
        ._scheduler_accounting_receipt_claim_path(shared, receipt)
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_bytes(
        attempt_registry_core.canonical_json_bytes(receipt) + b"\n"
    )
    rows = attempt_registry_core.record_attempt_recovery(
        rows, profile=profile, freeze_id=binding.freeze_sha256,
        slot_id=slot_id, binding=binding,
        scheduler_accounting_receipt=receipt,
        recoverer_process_identity={
            "pid": 202, "starttime": "campaign-recover",
            "execution_uuid": "campaign-recover-uuid",
        },
        recovered_at="2026-08-25T00:00:02+00:00",
    )
    relative = s8b_attempt_profile.S8B_REGISTRY_LAYOUT.registry_path.as_posix().format(
        freeze_sha256=binding.freeze_sha256,
    )
    path = shared.joinpath(*Path(relative).parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(
        attempt_registry_core.canonical_json_bytes(row) + b"\n" for row in rows
    ))
    return path


def test_cut6_replay_rejects_truthy_non_bool_verdict():
    runner = object.__new__(s8b_floor_campaign._Runner)  # noqa: SLF001
    runner.holdout_admissions = {"cell": object()}
    runner.cut6_replay_query_fn = (
        lambda _admission, *, attempt_id: "approved"
    )
    replayed = []
    runner._run_session = lambda **kwargs: replayed.append(kwargs)  # noqa: SLF001
    start = {
        "seq": 0, "round": 1, "cell_id": "cell", "kind": "planned",
        "retry_ordinal": None, "trigger": None, "attempt_id": "cell::seq0",
    }

    with pytest.raises(
        s8b_floor_campaign.CampaignAbort,
        match="cut-6 replay admission returned an invalid verdict",
    ):
        runner._replay_cut6_start(start)  # noqa: SLF001
    assert replayed == []


def test_resume_runner_produces_one_retry_from_admission_selected_recovery(
    tmp_path, monkeypatch,
):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    build_root = tmp_path / "bin"

    class Cut10Crash(BaseException):
        pass

    def crash_after_observation_admission(*_args):
        raise Cut10Crash("fixture: cut10 recovered attempt")

    with pytest.raises(Cut10Crash, match="cut10"):
        _run_campaign(
            protocol, verified, out_root=out_root, build_root=build_root,
            measure_fn=crash_after_observation_admission,
            probe_fn=lambda: (1, "", ""),
        )

    run_dir = _only_run_dir(out_root)
    before = _read_journal_lines(run_dir / "journal.jsonl")
    planned_start = next(
        row for row in before if row.get("event") == "session-start"
    )
    campaign_start = next(
        row for row in before if row.get("event") == "campaign-start"
    )
    manifest = json.loads((run_dir / "manifest.json").read_bytes())
    authority = _test_holdout_authority(out_root, protocol, verified)
    _write_verified_campaign_recovery_registry(
        authority=authority, protocol=protocol, schedule=manifest["schedule"],
        protocol_sha256=campaign_start["protocol_sha256"],
        trigger_start=planned_start,
    )
    monkeypatch.setattr(
        s8b_floor_campaign._holdout_admission,
        "_FLOOR_RECOVERY_AUTHORITIES",
        frozenset({_FLOOR_TEST_RECOVERY_AUTHORITY}),
    )

    original_append = s8b_floor_campaign._holdout_admission._append_ledger

    def crash_retry_after_marker(path, rows):
        if (
            path.name == "attempt-ledger.jsonl"
            and any(str(row.get("attempt_id", "")).endswith("::retry1") for row in rows)
        ):
            raise Cut10Crash("fixture: retry cut6 after consumed marker")
        return original_append(path, rows)

    with monkeypatch.context() as scoped:
        scoped.setattr(
            s8b_floor_campaign._holdout_admission,
            "_append_ledger", crash_retry_after_marker,
        )
        with pytest.raises(Cut10Crash, match="retry cut6"):
            _run_campaign(
                protocol, verified, out_root=out_root, build_root=build_root,
                resume_dir=run_dir,
                measure_fn=_make_measure_fn(
                    reps=5, value_fn=lambda cid: _BASE_TPS[cid],
                ),
                probe_fn=lambda: (1, "", ""),
            )

    cut6_records = _read_journal_lines(run_dir / "journal.jsonl")
    retry_start = next(
        row for row in cut6_records
        if row.get("event") == "session-start" and row.get("kind") == "retry"
    )
    assert retry_start["trigger"] == planned_start["attempt_id"]
    assert not any(
        row.get("event") == "session"
        and row.get("attempt_id") == retry_start["attempt_id"]
        for row in cut6_records
    )

    resumed_measure = _make_measure_fn(
        reps=5, value_fn=lambda cid: _BASE_TPS[cid],
    )
    outcome = _run_campaign(
        protocol, verified, out_root=out_root, build_root=build_root,
        resume_dir=run_dir, measure_fn=resumed_measure,
        probe_fn=lambda: (1, "", ""),
    )

    assert outcome["status"] == "completed"
    after = _read_journal_lines(run_dir / "journal.jsonl")
    retry_starts = [
        row for row in after
        if row.get("event") == "session-start" and row.get("kind") == "retry"
    ]
    retry_sessions = [
        row for row in after
        if row.get("event") == "session" and row.get("kind") == "retry"
    ]
    assert [(row["retry_ordinal"], row["trigger"]) for row in retry_starts] == [
        (1, planned_start["attempt_id"]),
    ]
    assert [row["attempt_id"] for row in retry_sessions] == [
        retry_start["attempt_id"],
    ]
    assert (run_dir / "result.json").is_file()
    assert (run_dir / "result.md").is_file()
    inspection = _live_holdout_admission_for_outcome(
        protocol=protocol, freeze_doc=verified,
        out_root=out_root, outcome=outcome,
    )
    assert inspection["attempt_row_count"] == len(outcome["result"]["sessions"]) + 1


def test_verified_recovery_emits_only_one_invalid_retry_ordinal(tmp_path):
    built = _honest_portable_built_record(
        tmp_path, configuration_id="sort_best",
    )
    runtime = copy.deepcopy(built["cell"])
    runtime["binary"] = str((tmp_path / "honest-portable.bin").resolve())
    runtime["store_path"] = str(
        (tmp_path / "store" / runtime["binary_sha256"]).resolve()
    )
    runtime["_ccbench_root"] = str((tmp_path / "ccbench").resolve())
    planned_id = "cell::seq0"
    records = [
        {"event": "campaign-start"},
        {"event": "round-start", "round": 1},
        {
            "event": "session-start", "seq": 0, "round": 1,
            "kind": "planned", "retry_ordinal": None,
            "cell_id": "cell", "attempt_id": planned_id, "trigger": None,
        },
    ]
    runner = _live_admission_runner(
        tmp_path, runtime=runtime, built=built,
        schedule=[{"seq": 0, "round": 1, "cell_id": "cell"}],
        records=records,
        cut6_replay_query_fn=lambda _admission, *, attempt_id: False,
        retry_trigger_query_fn=lambda _admission, *, round_no: (
            s8b_floor_campaign._holdout_admission.FloorRetryAuthorization(
                trigger_attempt_id=planned_id,
                source="verified-registry-recovery",
            )
        ),
    )
    runner.run()

    retry_starts = [
        row for row in runner.records
        if row.get("event") == "session-start" and row.get("kind") == "retry"
    ]
    retry_sessions = [
        row for row in runner.records
        if row.get("event") == "session" and row.get("kind") == "retry"
    ]
    assert [row["retry_ordinal"] for row in retry_starts] == [1]
    assert len(retry_sessions) == 1
    assert retry_sessions[0]["valid"] is False


@pytest.mark.parametrize("runtime_view", ["fresh", "resolved"])
def test_live_admission_accepts_both_exact_runtime_views(tmp_path, runtime_view):
    built = _honest_portable_built_record(
        tmp_path, configuration_id="sort_best",
    )
    runtime = copy.deepcopy(built["cell"])
    runtime["binary"] = str((tmp_path / "honest-portable.bin").resolve())
    runtime["store_path"] = str(
        (tmp_path / "store" / runtime["binary_sha256"]).resolve()
    )
    if runtime_view == "fresh":
        runtime["_ccbench_root"] = str((tmp_path / "ccbench").resolve())
    runner = _live_admission_runner(tmp_path, runtime=runtime, built=built)
    runner._validate_live_admissions()


@pytest.mark.parametrize("mutation", ["unexpected-key", "missing-sort-receipt"])
def test_live_admission_runtime_exact_keys_fail_closed(tmp_path, mutation):
    built = _honest_portable_built_record(
        tmp_path, configuration_id="sort_best",
    )
    runtime = copy.deepcopy(built["cell"])
    runtime["binary"] = str((tmp_path / "honest-portable.bin").resolve())
    runtime["store_path"] = str(
        (tmp_path / "store" / runtime["binary_sha256"]).resolve()
    )
    runtime["_ccbench_root"] = str((tmp_path / "ccbench").resolve())
    if mutation == "unexpected-key":
        runtime["unexpected"] = "must be rejected"
    else:
        runtime.pop("sort_swo_oracle")
    runner = _live_admission_runner(tmp_path, runtime=runtime, built=built)
    with pytest.raises(
            s8b_floor_campaign.CampaignAbort,
            match="runtime binary record.*exact key"):
        runner._validate_live_admissions()


def test_sort_runtime_record_with_fetchcontent_base_stores_and_projects(tmp_path):
    out_root = tmp_path / "out"
    binary = out_root / "cache" / "cell" / "binary.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"honest portable binary")
    ccbench_root = tmp_path / "ccbench"
    fetchcontent_base = tmp_path / "job-fetchcontent"
    fetchcontent_base.mkdir()
    built = _honest_portable_built_record(
        tmp_path, configuration_id="sort_best",
    )
    runtime = built["cell"]
    issued_receipt = copy.deepcopy(runtime["admission_receipt"])
    runtime.pop("store_path")
    runtime.update({
        "binary": str(binary.resolve()),
        "configure_argv": [
            "cmake", "-S", str(ccbench_root.resolve()),
            f"-DFETCHCONTENT_BASE_DIR={fetchcontent_base.resolve()}",
        ],
        "build_argv": ["cmake", "--build", str(binary.parent.resolve())],
        "_ccbench_root": str(ccbench_root.resolve()),
        "_fetchcontent_base_dir": str(fetchcontent_base.resolve()),
    })

    s8b_floor_campaign.store_binaries(
        built, out_root / "store", out_root=out_root,
        expected_ccbench_pin="1" * 40,
        expected_contract_sha256="2" * 64,
    )
    portable = s8b_floor_campaign.project_built_records(built, out_root=out_root)
    resolved = s8b_floor_campaign.resolve_portable_built(portable, out_root=out_root)
    s8b_floor_campaign._verify_resume_store(resolved, out_root)
    s8b_floor_campaign._verify_resume_binaries(resolved)

    assert portable["cell"]["admission_receipt"] == issued_receipt
    assert resolved["cell"]["admission_receipt"] == issued_receipt
    assert "_fetchcontent_base_dir" not in portable["cell"]
    assert "${FETCHCONTENT_BASE_DIR}" in portable["cell"]["configure_argv"][-1]
    durable_json = json.dumps(portable, sort_keys=True)
    assert str(fetchcontent_base.resolve()) not in durable_json


def test_sort_runtime_record_without_fetchcontent_base_stores_and_projects(tmp_path):
    out_root = tmp_path / "out"
    binary = out_root / "cache" / "cell" / "binary.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"honest portable binary")
    ccbench_root = tmp_path / "ccbench"
    built = _honest_portable_built_record(
        tmp_path, configuration_id="sort_best",
    )
    runtime = built["cell"]
    runtime.pop("store_path")
    runtime.update({
        "binary": str(binary.resolve()),
        "configure_argv": ["cmake", "-S", str(ccbench_root.resolve())],
        "build_argv": ["cmake", "--build", str(binary.parent.resolve())],
        "_ccbench_root": str(ccbench_root.resolve()),
    })

    s8b_floor_campaign.store_binaries(
        built, out_root / "store", out_root=out_root,
        expected_ccbench_pin="1" * 40,
        expected_contract_sha256="2" * 64,
    )
    portable = s8b_floor_campaign.project_built_records(built, out_root=out_root)

    assert portable["cell"]["configuration_id"] == "sort_best"
    assert "_fetchcontent_base_dir" not in portable["cell"]
    assert portable["cell"]["configure_argv"] == [
        "cmake", "-S", "${CCBENCH_ROOT}",
    ]


@pytest.mark.parametrize("entrypoint", ["store", "project"])
def test_fetchcontent_runtime_field_is_rejected_for_non_sort_record(
        tmp_path, entrypoint):
    out_root = tmp_path / "out"
    binary = out_root / "cache" / "cell" / "binary.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"honest portable binary")
    sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    ccbench_root = tmp_path / "ccbench"
    fetchcontent_base = tmp_path / "job-fetchcontent"
    fetchcontent_base.mkdir()
    built = _honest_portable_built_record(tmp_path)
    runtime = built["cell"]
    runtime.update({
        "binary": str(binary.resolve()),
        "binary_sha256": sha,
        "bin_hash_short": sha[:16],
        "configure_argv": [
            "cmake", "-S", str(ccbench_root.resolve()),
            f"-DFETCHCONTENT_BASE_DIR={fetchcontent_base.resolve()}",
        ],
        "build_argv": ["cmake", "--build", str(binary.parent.resolve())],
        "_ccbench_root": str(ccbench_root.resolve()),
        "_fetchcontent_base_dir": str(fetchcontent_base.resolve()),
    })
    if entrypoint == "store":
        runtime.pop("store_path")
        call = lambda: s8b_floor_campaign.store_binaries(
            built, out_root / "store", out_root=out_root,
            expected_ccbench_pin="1" * 40,
            expected_contract_sha256="2" * 64,
        )
    else:
        runtime["store_path"] = str((out_root / "store" / sha).resolve())
        call = lambda: s8b_floor_campaign.project_built_records(
            built, out_root=out_root,
            expected_ccbench_pin="1" * 40,
            expected_contract_sha256="2" * 64,
        )
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="sort_best にだけ許可"):
        call()


def test_portable_projection_rejects_reserved_placeholder_and_exact_key_tamper(tmp_path):
    binary = tmp_path / "out" / "cache" / "binary.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"honest portable binary")
    sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    runtime = _honest_portable_built_record(tmp_path)
    runtime["cell"].update({
        "binary": str(binary), "binary_sha256": sha, "bin_hash_short": sha[:16],
        "configure_argv": ["cmake", "${OUT_ROOT}"],
        "build_argv": ["cmake", "--build", str(binary.parent)],
        "store_path": str(tmp_path / "out" / "store" / sha),
        "_ccbench_root": str(tmp_path / "ccbench"),
    })
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="予約 placeholder"):
        s8b_floor_campaign.project_built_records(runtime, out_root=tmp_path / "out")

    runtime["cell"]["configure_argv"] = ["cmake", "-S", str(tmp_path / "ccbench")]
    portable = s8b_floor_campaign.project_built_records(
        runtime, out_root=tmp_path / "out")
    portable["cell"].pop("cached")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="exact key"):
        s8b_floor_campaign.resolve_portable_built(
            portable, out_root=tmp_path / "out")


@pytest.mark.parametrize(("path", "reason"), [
    ("a/../b", "portable built binary path component が不正"),
    ("a//b", "portable built binary path 文法が不正"),
    ("/abs", "portable built binary path 文法が不正"),
])
@pytest.mark.parametrize("entrypoint", ["validate", "resolve"])
def test_portable_built_rejects_path_traversal_and_noncanonical_paths(
        tmp_path, path, reason, entrypoint):
    built = _honest_portable_built_record(tmp_path)
    built["cell"]["binary"] = path
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match=reason):
        if entrypoint == "validate":
            s8b_floor_campaign._validate_portable_built(built)
        else:
            s8b_floor_campaign.resolve_portable_built(built, out_root=tmp_path)


@pytest.mark.parametrize(("field", "value", "reason"), [
    ("cached", 1, "portable binaries\\[cell\\]\\.cached が bool でない"),
    ("cached", "true", "portable binaries\\[cell\\]\\.cached が bool でない"),
    ("binary_sha256", "not-a-sha",
     "portable binaries\\[cell\\]\\.binary_sha256 が不正"),
    ("bin_hash_short", "b" * 16,
     "portable binaries\\[cell\\]\\.bin_hash_short が不一致"),
    ("binding", [], "portable binaries\\[cell\\]\\.binding が object でない"),
])
def test_portable_built_rejects_wrong_scalar_and_mapping_types(
        tmp_path, field, value, reason):
    built = _honest_portable_built_record(tmp_path)
    built["cell"][field] = value
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match=reason):
        s8b_floor_campaign._validate_portable_built(built)


def test_portable_built_rejects_missing_admission_receipt(tmp_path):
    built = _honest_portable_built_record(tmp_path)
    built["cell"].pop("admission_receipt")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError):
        s8b_floor_campaign._validate_portable_built(built)


def test_store_binaries_preflights_all_records_before_first_write(tmp_path):
    valid = _honest_portable_built_record(tmp_path)["cell"]
    valid["binary"] = str((tmp_path / "honest-portable.bin").resolve())
    valid.pop("store_path")
    valid["_ccbench_root"] = str((tmp_path / "portable-source").resolve())
    invalid = json.loads(json.dumps(valid))
    invalid["cell_id"] = "z-cell"
    invalid["cached"] = "false"
    store_root = tmp_path / "store"
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="cached が bool"):
        s8b_floor_campaign.store_binaries(
            {"cell": valid, "z-cell": invalid}, store_root, out_root=tmp_path,
            expected_ccbench_pin="1" * 40,
            expected_contract_sha256="2" * 64,
        )
    assert not store_root.exists()


@pytest.mark.parametrize("field", ["ccbench_pin", "contract_sha256"])
def test_store_binaries_binds_receipt_to_live_protocol_before_first_write(
        tmp_path, field):
    rec = _honest_portable_built_record(tmp_path)["cell"]
    rec["binary"] = str((tmp_path / "honest-portable.bin").resolve())
    rec.pop("store_path")
    rec["_ccbench_root"] = str((tmp_path / "portable-source").resolve())
    receipt = rec["admission_receipt"]
    if field == "ccbench_pin":
        receipt["admission"]["source"]["ccbench_commit"] = "9" * 40
    else:
        receipt["subject"]["contract_sha256"] = "9" * 64
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256")
    receipt["receipt_sha256"] = s8b_binary_admission._sha256_map(unsigned)
    store_root = tmp_path / "store"
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="外部期待値"):
        s8b_floor_campaign.store_binaries(
            {"cell": rec}, store_root, out_root=tmp_path,
            expected_ccbench_pin="1" * 40,
            expected_contract_sha256="2" * 64,
        )
    assert not store_root.exists()


def _valid_launch_certificate() -> dict:
    return s8b_floor_campaign.build_launch_certificate(
        v1_freeze_sha256="a" * 64,
        clean_digest="b" * 64,
        protocol_sha256="c" * 64,
        started_utc="2026-01-01T00:00:00+00:00",
        campaign_run_id="20260101T000000Z-cccccccc",
    )


def _validate_launch(cert):
    return s8b_floor_campaign.validate_launch_certificate(
        cert,
        expected_v1_freeze_sha256="a" * 64,
        expected_protocol_sha256="c" * 64,
        expected_run_id="20260101T000000Z-cccccccc",
    )


def test_validate_launch_certificate_accepts_valid_document():
    cert = _valid_launch_certificate()
    assert _validate_launch(cert) == cert


@pytest.mark.parametrize("mutation", ["missing", "extra", "schema", "hash", "utc", "run-id"])
def test_validate_launch_certificate_rejects_invalid_document(mutation):
    cert = _valid_launch_certificate()
    if mutation == "missing":
        cert.pop("clean_scan_digest")
    elif mutation == "extra":
        cert["extra"] = True
    elif mutation == "schema":
        cert["schema"] = "s8b-floor-launch-certificate/v0"
    elif mutation == "hash":
        cert["protocol_sha256"] = "A" * 64
    elif mutation == "utc":
        cert["started_utc"] = "2026-01-01T00:00:00+09:00"
    else:
        cert["campaign_run_id"] = "renamed-run"
    with pytest.raises(s8b_floor_campaign.FloorCampaignError):
        _validate_launch(cert)


def test_validate_launch_certificate_rejects_expected_hash_mismatch():
    cert = _valid_launch_certificate()
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="v1_freeze_sha256"):
        s8b_floor_campaign.validate_launch_certificate(
            cert,
            expected_v1_freeze_sha256="0" * 64,
            expected_protocol_sha256="c" * 64,
            expected_run_id="20260101T000000Z-cccccccc",
        )


def test_validate_launch_certificate_translates_leaf_error():
    cert = _valid_launch_certificate()
    cert["protocol_sha256"] = "A" * 64
    with pytest.raises(s8b_floor_campaign.FloorCampaignError) as exc_info:
        _validate_launch(cert)
    assert isinstance(exc_info.value.__cause__, s8b_launch_cert.LaunchCertError)


def test_validate_launch_certificate_strict_rejects_clean_digest_mismatch():
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="clean_scan_digest"):
        s8b_floor_campaign.validate_launch_certificate_strict(
            _valid_launch_certificate(),
            expected_v1_freeze_sha256="a" * 64,
            expected_clean_scan_digest="0" * 64,
            expected_protocol_sha256="c" * 64,
            expected_run_id="20260101T000000Z-cccccccc",
        )


def test_official_preflight_scans_exactly_twice_and_returns_independent_expected(
        tmp_path, monkeypatch):
    calls = []

    def scan(root, *, freeze_allowlist):
        calls.append((Path(root), dict(freeze_allowlist)))
        return "b" * 64

    monkeypatch.setattr(s8b_floor_campaign, "clean_scan_digest", scan)
    cert, expected = s8b_floor_campaign._official_launch_preflight(
        tmp_path,
        v1_freeze_sha256="a" * 64,
        protocol_sha256="c" * 64,
        started_utc="2026-01-01T00:00:00+00:00",
        campaign_run_id="20260101T000000Z-cccccccc",
        freeze_allowlist={s8b_floor_campaign._FLOOR_PROTOCOL_REL: "d" * 64},
    )
    assert len(calls) == 2
    assert calls[0] == calls[1]
    assert cert["clean_scan_digest"] == expected == "b" * 64


def test_official_preflight_rejects_digest_shift_between_independent_scans(
        tmp_path, monkeypatch):
    values = iter(("b" * 64, "d" * 64))
    calls = []

    def scan(root, *, freeze_allowlist):
        calls.append(Path(root))
        return next(values)

    monkeypatch.setattr(s8b_floor_campaign, "clean_scan_digest", scan)
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="clean_scan_digest"):
        s8b_floor_campaign._official_launch_preflight(
            tmp_path,
            v1_freeze_sha256="a" * 64,
            protocol_sha256="c" * 64,
            started_utc="2026-01-01T00:00:00+00:00",
            campaign_run_id="20260101T000000Z-cccccccc",
            freeze_allowlist={},
        )
    assert len(calls) == 2


def test_second_scan_digest_shift_persists_claim_but_issues_no_certificate(
        tmp_path, monkeypatch):
    ctx = _install_required_contract(tmp_path, monkeypatch)
    claim_root = _provision_claim_root(ctx)
    digests = iter(("b" * 64, "d" * 64))
    monkeypatch.setattr(
        s8b_floor_campaign, "clean_scan_digest",
        lambda root, *, freeze_allowlist: next(digests),
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="clean_scan_digest"):
        _private_run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="official", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
            monotonic_fn=lambda: 0.0, prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, host_provenance_fn=_fixed_host,
            process_identity_fn=_fixed_process, repo_root=ctx["repo_root"],
            durable_root_policy=_durable_policy(ctx["out_root"]),
            _floor_preflight_fn=lambda *args, **kwargs: {},
        )
    assert len(list(claim_root.glob("*.claim"))) == 1
    assert not list(ctx["out_root"].rglob("launch_certificate.json"))


def test_revalidate_issued_certificate_accepts_independent_clean_digest(tmp_path):
    cert = _valid_launch_certificate()
    cert_path = tmp_path / "launch_certificate.json"
    s8b_floor_campaign.issue_launch_certificate(cert_path, cert)
    normalized, raw = s8b_floor_campaign._revalidate_issued_certificate(
        cert_path,
        expected_v1_freeze_sha256="a" * 64,
        expected_clean_scan_digest="b" * 64,
        expected_protocol_sha256="c" * 64,
        expected_run_id="20260101T000000Z-cccccccc",
    )
    assert normalized == cert
    assert raw == cert_path.read_bytes()


def test_revalidate_issued_certificate_rejects_tampered_clean_digest(tmp_path):
    cert = _valid_launch_certificate()
    cert["clean_scan_digest"] = "d" * 64
    cert_path = tmp_path / "launch_certificate.json"
    s8b_floor_campaign.issue_launch_certificate(cert_path, cert)
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="clean_scan_digest"):
        s8b_floor_campaign._revalidate_issued_certificate(
            cert_path,
            expected_v1_freeze_sha256="a" * 64,
            expected_clean_scan_digest="b" * 64,
            expected_protocol_sha256="c" * 64,
            expected_run_id="20260101T000000Z-cccccccc",
        )


def test_official_fresh_issues_certificate_and_binds_wall_ledger(tmp_path, monkeypatch):
    repo_before = _real_output_snapshot()
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    with _official_test_seam(monkeypatch):
        outcome = _run_campaign(
            protocol, verified, out_root=tmp_path / "out", build_root=tmp_path / "bin",
            measure_fn=measure_fn, probe_fn=lambda: (1, "", ""), mode="official",
        )
    run_dir = Path(outcome["run_dir"])
    cert_path = run_dir / "launch_certificate.json"
    cert = json.loads(cert_path.read_bytes())
    cert_sha = hashlib.sha256(cert_path.read_bytes()).hexdigest()
    assert cert["campaign_run_id"] == run_dir.name
    assert cert["started_utc"] == _FIXED_NOW.isoformat()
    journal = _read_journal_lines(run_dir / "journal.jsonl")
    assert journal[0] == {
        "event": "launch-start", "schema": s8b_floor_campaign.JOURNAL_SCHEMA,
        "launch_certificate_sha256": cert_sha, "utc": _FIXED_NOW.isoformat(),
    }
    campaign_start = next(r for r in journal if r.get("event") == "campaign-start")
    assert campaign_start["launch_certificate_sha256"] == cert_sha
    wall_start = next(r for r in outcome["result"]["wall_ledger"]
                      if r.get("event") == "campaign-start")
    assert wall_start["launch_certificate_sha256"] == cert_sha
    assert outcome["result"]["eligible_for_refreeze"] is False
    assert repo_before == _real_output_snapshot()


def test_checkpoint_callback_is_after_cert_validation_and_before_launch_start(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    observed = []

    def checkpoint(cert_path):
        observed.append(cert_path)
        assert json.loads(cert_path.read_bytes())["campaign_run_id"] == cert_path.parent.name
        assert not (cert_path.parent / "journal.jsonl").exists()
        raise _SimulatedCrash("checkpoint crash")

    with _official_test_seam(monkeypatch):
        with pytest.raises(_SimulatedCrash, match="checkpoint"):
            _private_run_campaign(
                protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
                mode="official", measure_fn=_forbid_measure,
                probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
                monotonic_fn=lambda: 0.0, prepare_fn=_fake_prepare,
                now_fn=lambda: _FIXED_NOW,
                after_certificate_issued_fn=checkpoint,
                durable_root_policy=_durable_policy(tmp_path / "out"),
                _floor_preflight_fn=_fixture_floor_preflight,
            )
    assert len(observed) == 1
    run_dir = observed[0].parent
    assert {path.name for path in run_dir.iterdir()} == {"launch_certificate.json"}
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="厳密な L"):
        _run_campaign(
            protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
            build_root=tmp_path / "ignored", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), mode="official", resume_dir=run_dir,
        )


def test_checkpoint_raw_hash_recheck_fires_before_launch_start(tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))

    def mutate_cert(cert_path):
        cert_path.write_bytes(cert_path.read_bytes() + b" ")

    with _official_test_seam(monkeypatch):
        with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="raw hash"):
            _private_run_campaign(
                protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
                mode="official", measure_fn=_forbid_measure,
                probe_fn=lambda: (1, "", ""), sleep_fn=lambda _seconds: None,
                monotonic_fn=lambda: 0.0, prepare_fn=_fake_prepare,
                now_fn=lambda: _FIXED_NOW,
                after_certificate_issued_fn=mutate_cert,
                durable_root_policy=_durable_policy(tmp_path / "out"),
                _floor_preflight_fn=_fixture_floor_preflight,
            )
    run_dir = next(path.parent for path in (tmp_path / "out").rglob("launch_certificate.json"))
    assert not (run_dir / "journal.jsonl").exists()


def test_official_scan_rejection_has_zero_filesystem_side_effects(tmp_path, monkeypatch):
    repo_before = _real_output_snapshot()
    freeze = _freeze_document()
    out_root = tmp_path / "out"
    with monkeypatch.context() as scoped:
        def reject_scan(root, *, freeze_allowlist):
            raise s8b_floor_campaign.FloorCampaignError("fixture scan hit")

        scoped.setattr(s8b_floor_campaign, "clean_scan_digest", reject_scan)
        with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="scan hit"):
            _run_campaign(
                _protocol(freeze_sha=_freeze_sha(freeze)), _verified_freeze(freeze),
                out_root=out_root, build_root=tmp_path / "bin",
                measure_fn=_forbid_measure, probe_fn=lambda: (1, "", ""), mode="official",
            )
    assert not out_root.exists()
    assert repo_before == _real_output_snapshot()


def test_official_build_failure_leaves_durable_launch_start(tmp_path, monkeypatch):
    repo_before = _real_output_snapshot()
    freeze = _freeze_document()
    out_root = tmp_path / "out"
    with _official_test_seam(monkeypatch) as scoped:
        scoped.setattr(
            s8b_floor_campaign, "build_cells",
            lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("fixture build crash")),
        )
        with pytest.raises(RuntimeError, match="build crash"):
            _run_campaign(
                _protocol(freeze_sha=_freeze_sha(freeze)), _verified_freeze(freeze),
                out_root=out_root, build_root=tmp_path / "bin",
                measure_fn=_forbid_measure, probe_fn=lambda: (1, "", ""), mode="official",
                perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
            )
    journals = list(out_root.rglob("journal.jsonl"))
    assert len(journals) == 1
    journal = _read_journal_lines(journals[0])
    assert [record["event"] for record in journal] == [
        "launch-start", "perf-preflight",
    ]
    assert (journals[0].parent / "launch_certificate.json").is_file()
    assert not (journals[0].parent / "manifest.json").exists()
    # 厳密 L を同じ cert/run の下で build から再構築する。
    resume_measure = _make_measure_fn(
        reps=5, value_fn=lambda cid: _BASE_TPS[cid], use_perf=False,
    )
    outcome = _run_campaign(
        _protocol(freeze_sha=_freeze_sha(freeze)), _verified_freeze(freeze),
        out_root=out_root, build_root=tmp_path / "bin",
        measure_fn=resume_measure,
        probe_fn=lambda: (1, "", ""), mode="official",
        resume_dir=journals[0].parent,
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
    )
    assert outcome["status"] == "completed"
    assert not any(r.get("event") == "resume-start"
                   for r in _read_journal_lines(journals[0]))
    assert repo_before == _real_output_snapshot()


def test_l_resume_rejects_extra_run_dir_file(tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with _official_test_seam(monkeypatch) as scoped:
        scoped.setattr(
            s8b_floor_campaign, "build_cells",
            lambda *args, **kwargs: (_ for _ in ()).throw(_SimulatedCrash("build")),
        )
        with pytest.raises(_SimulatedCrash):
            _run_campaign(
                protocol, _verified_freeze(freeze), out_root=out_root,
                build_root=tmp_path / "bin", measure_fn=_forbid_measure,
                probe_fn=lambda: (1, "", ""), mode="official",
            )
    run_dir = next(path.parent for path in out_root.rglob("journal.jsonl"))
    (run_dir / "extra.txt").write_text("not permitted\n", encoding="utf-8")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="許可 file 集合"):
        _run_campaign(
            protocol, _verified_freeze(freeze), out_root=out_root,
            build_root=tmp_path / "bin", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), mode="official", resume_dir=run_dir,
        )


def test_l_resume_rejects_symlinked_launch_certificate(tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with _official_test_seam(monkeypatch) as scoped:
        scoped.setattr(
            s8b_floor_campaign, "build_cells",
            lambda *args, **kwargs: (_ for _ in ()).throw(_SimulatedCrash("build")),
        )
        with pytest.raises(_SimulatedCrash, match="build"):
            _run_campaign(
                protocol, _verified_freeze(freeze), out_root=out_root,
                build_root=tmp_path / "bin", measure_fn=_forbid_measure,
                probe_fn=lambda: (1, "", ""), mode="official",
            )
        run_dir = next(path.parent for path in out_root.rglob("journal.jsonl"))
        cert_path = run_dir / "launch_certificate.json"
        cert_copy = tmp_path / "launch_certificate-copy.json"
        cert_copy.write_bytes(cert_path.read_bytes())
        cert_path.unlink()
        cert_path.symlink_to(cert_copy)

        with pytest.raises(
                s8b_floor_campaign.FloorCampaignError,
                match="resume: launch certificate が regular file でない"):
            _run_campaign(
                protocol, _verified_freeze(freeze), out_root=out_root,
                build_root=tmp_path / "bin", measure_fn=_forbid_measure,
                probe_fn=lambda: (1, "", ""), mode="official", resume_dir=run_dir,
            )


def test_m_prestart_resume_starts_runner_fresh_without_resume_start(tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with _official_test_seam(monkeypatch) as scoped:
        scoped.setattr(
            s8b_floor_campaign._Runner, "run",
            lambda self: (_ for _ in ()).throw(_SimulatedCrash("prestart")),
        )
        with pytest.raises(_SimulatedCrash, match="prestart"):
            _run_campaign(
                protocol, _verified_freeze(freeze), out_root=out_root,
                build_root=tmp_path / "bin",
                measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
                probe_fn=lambda: (1, "", ""), mode="official",
                perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
            )
    run_dir = _only_run_dir(out_root)
    assert [r["event"] for r in _read_journal_lines(run_dir / "journal.jsonl")] == [
        "launch-start", "perf-preflight",
    ]
    outcome = _run_campaign(
        protocol, _verified_freeze(freeze), out_root=out_root,
        build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(
            reps=5, value_fn=lambda cid: _BASE_TPS[cid], use_perf=False,
        ),
        probe_fn=lambda: (1, "", ""), mode="official", resume_dir=run_dir,
    )
    journal = _read_journal_lines(run_dir / "journal.jsonl")
    assert outcome["status"] == "completed"
    assert sum(r.get("event") == "campaign-start" for r in journal) == 1
    assert not any(r.get("event") == "resume-start" for r in journal)


def test_official_resume_validates_certificate_and_completes(tmp_path, monkeypatch):
    repo_before = _real_output_snapshot()
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with _official_test_seam(monkeypatch):
        crashing_measure, _ = _crash_at(4)
        with pytest.raises(_SimulatedCrash):
            _run_campaign(
                protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                measure_fn=crashing_measure, probe_fn=lambda: (1, "", ""), mode="official",
            )
        run_dir = _only_run_dir(out_root)
        resume_measure = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
        outcome = _run_campaign(
            protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
            measure_fn=resume_measure, probe_fn=lambda: (1, "", ""), mode="official",
            resume_dir=run_dir,
        )
    assert outcome["status"] == "completed"
    assert outcome["result"]["eligible_for_refreeze"] is False
    assert repo_before == _real_output_snapshot()


def _patch_current_contract_to_synthetic_successor(monkeypatch):
    """実 registry は bootstrap fuse により単一世代のままである。

    この fixture は registry に g1 が残り current が g2 へ進んだ状態を module
    属性の局所差し替えで模すだけで、実際の世代発効を模していない。
    """
    g1_entry = ec.GENERATIONS[ENV_TAG][-1]
    g1 = g1_entry.contract
    g2 = dataclasses.replace(
        g1,
        calibration_ref=ec.CalibrationRef(
            path=g1.calibration_ref.path + ".synthetic-successor",
            sha256="f" * 64,
        ),
    )
    assert ec.is_valid_successor(g1, g2)
    generations = MappingProxyType({
        **ec.GENERATIONS,
        ENV_TAG: (g1_entry, ec.GenerationEntry(generation=2, contract=g2)),
    })
    ec._validate_generations_without_bootstrap_fuse(generations)
    registry = MappingProxyType({
        env_tag: entries[-1].contract
        for env_tag, entries in generations.items()
    })
    index = ec._build_contract_sha256_index(generations)
    monkeypatch.setattr(ec, "GENERATIONS", generations)
    monkeypatch.setattr(ec, "REGISTRY", registry)
    monkeypatch.setattr(ec, "_CONTRACT_SHA256_INDEX", index)
    assert ec.lookup(ENV_TAG) is g2
    assert ec.resolve_by_contract_sha256(g1.contract_sha256).contract is g1
    return g1, g2


def test_public_validate_protocol_resolves_recorded_historical_generation_once(
        monkeypatch):
    """合成 g2 は activation 正例でなく、read-only g1 解決だけを模す。"""
    protocol = _valid_protocol_dict()
    g1, g2 = _patch_current_contract_to_synthetic_successor(monkeypatch)
    assert protocol["contract_sha256"] == g1.contract_sha256
    assert protocol["contract_sha256"] != g2.contract_sha256

    real_resolve = ec.resolve_by_contract_sha256
    historical_resolver = mock.Mock(wraps=real_resolve)
    current_lookup = mock.Mock(
        side_effect=AssertionError("historical 検証から current lookup してはいけない"),
    )
    monkeypatch.setattr(ec, "resolve_by_contract_sha256", historical_resolver)
    monkeypatch.setattr(ec, "lookup", current_lookup)

    assert s8b_floor_campaign.validate_protocol(protocol) == protocol
    historical_resolver.assert_called_once_with(
        g1.contract_sha256, expected_env_tag=ENV_TAG,
    )
    current_lookup.assert_not_called()


def test_protocol_lanes_both_reject_str_subclass_contract_sha256(monkeypatch):
    class HashText(str):
        pass

    protocol = _valid_protocol_dict()
    protocol["contract_sha256"] = HashText(protocol["contract_sha256"])
    historical_resolver = mock.Mock(
        side_effect=AssertionError("exact 型拒否より後へ進んではならない"),
    )
    current_lookup = mock.Mock(
        side_effect=AssertionError("exact 型拒否より後へ進んではならない"),
    )
    monkeypatch.setattr(ec, "resolve_by_contract_sha256", historical_resolver)
    monkeypatch.setattr(ec, "lookup", current_lookup)

    errors = []
    for validator in (
            s8b_floor_campaign.validate_protocol,
            s8b_floor_campaign._validate_protocol_against_current):
        with pytest.raises(s8b_floor_campaign.FloorCampaignError) as caught:
            validator(protocol)
        errors.append(caught.value)

    assert [type(error) for error in errors] == [
        s8b_floor_campaign.FloorCampaignError,
        s8b_floor_campaign.FloorCampaignError,
    ]
    assert str(errors[0]) == str(errors[1])
    historical_resolver.assert_not_called()
    current_lookup.assert_not_called()


@pytest.mark.parametrize("failure", ["unknown", "cross-env", "invalid-return"])
def test_public_validate_protocol_historical_failures_never_fallback_to_current(
        monkeypatch, failure):
    protocol = _valid_protocol_dict()
    other_env = next(env_tag for env_tag in ec.REGISTRY if env_tag != ENV_TAG)
    if failure == "unknown":
        protocol["contract_sha256"] = "0" * 64
        historical_resolver = mock.Mock(wraps=ec.resolve_by_contract_sha256)
    elif failure == "cross-env":
        protocol["contract_sha256"] = ec.lookup(other_env).contract_sha256
        historical_resolver = mock.Mock(wraps=ec.resolve_by_contract_sha256)
    else:
        historical_resolver = mock.Mock(return_value=object())

    current_lookup = mock.Mock(
        side_effect=AssertionError("historical resolver 失敗時に fallback してはいけない"),
    )
    monkeypatch.setattr(ec, "resolve_by_contract_sha256", historical_resolver)
    monkeypatch.setattr(ec, "lookup", current_lookup)

    with pytest.raises(s8b_floor_campaign.FloorCampaignError):
        s8b_floor_campaign.validate_protocol(protocol)

    historical_resolver.assert_called_once_with(
        protocol["contract_sha256"], expected_env_tag=ENV_TAG,
    )
    current_lookup.assert_not_called()


def test_public_validate_protocol_ambiguous_generation_never_falls_back_to_current(
        monkeypatch):
    protocol = _valid_protocol_dict()
    entry = ec.resolve_by_contract_sha256(protocol["contract_sha256"])
    monkeypatch.setattr(
        ec,
        "_CONTRACT_SHA256_INDEX",
        MappingProxyType({protocol["contract_sha256"]: (entry, entry)}),
    )
    current_lookup = mock.Mock(
        side_effect=AssertionError("ambiguous 時に current fallback してはいけない"),
    )
    monkeypatch.setattr(ec, "lookup", current_lookup)

    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="一意"):
        s8b_floor_campaign.validate_protocol(protocol)

    current_lookup.assert_not_called()


def test_main_validates_recorded_g1_with_historical_lane_when_current_is_g2(
        tmp_path, monkeypatch, capsys):
    protocol = _valid_protocol_dict()
    g1, g2 = _patch_current_contract_to_synthetic_successor(monkeypatch)
    assert protocol["contract_sha256"] == g1.contract_sha256
    assert protocol["contract_sha256"] != g2.contract_sha256

    real_resolve = ec.resolve_by_contract_sha256
    historical_resolver = mock.Mock(wraps=real_resolve)
    current_lookup = mock.Mock(
        side_effect=AssertionError("main の read-only 検証を current へ戻せない"),
    )
    load_protocol = mock.Mock(return_value=protocol)
    verified = object()
    load_freeze = mock.Mock(return_value=verified)
    run_campaign = mock.Mock(return_value={
        "status": "completed", "run_dir": str(tmp_path / "run"),
    })
    monkeypatch.setattr(ec, "resolve_by_contract_sha256", historical_resolver)
    monkeypatch.setattr(ec, "lookup", current_lookup)
    monkeypatch.setattr(s8b_floor_campaign, "load_protocol", load_protocol)
    monkeypatch.setattr(s8b_floor_campaign, "_load_verified_freeze", load_freeze)
    monkeypatch.setattr(s8b_floor_campaign, "repo_output_root", lambda: str(tmp_path))
    monkeypatch.setattr(s8b_floor_campaign, "run_campaign", run_campaign)
    monkeypatch.setattr(s8b_floor_campaign, "ROOT", tmp_path)
    protocol_path = tmp_path / s8b_floor_campaign._FLOOR_PROTOCOL_REL

    assert s8b_floor_campaign.main([
        "--mode", "pilot", "--protocol", str(protocol_path),
    ]) == 0

    assert json.loads(capsys.readouterr().out)["status"] == "completed"
    load_protocol.assert_called_once_with(protocol_path)
    historical_resolver.assert_called_once_with(
        g1.contract_sha256, expected_env_tag=ENV_TAG,
    )
    current_lookup.assert_not_called()
    load_freeze.assert_called_once()
    run_campaign.assert_called_once()
    assert run_campaign.call_args.args == (protocol, verified)
    assert run_campaign.call_args.kwargs["protocol_path"] == protocol_path


def test_fresh_run_rejects_recorded_g1_when_current_contract_is_g2_before_io(
        tmp_path, monkeypatch):
    """合成 g2 は activation 正例でなく、fresh current admission 境界だけを模す。"""
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    g1, g2 = _patch_current_contract_to_synthetic_successor(monkeypatch)
    assert protocol["contract_sha256"] == g1.contract_sha256
    assert protocol["contract_sha256"] != g2.contract_sha256

    real_lookup = ec.lookup
    current_lookup = mock.Mock(wraps=real_lookup)
    historical_resolver = mock.Mock(
        side_effect=AssertionError("fresh admission から historical resolver を呼べない"),
    )
    calibration_loader = mock.Mock(
        side_effect=AssertionError("current 不一致時に calibration を読めない"),
    )
    measure_fn = mock.Mock(
        side_effect=AssertionError("current 不一致時に計測してはいけない"),
    )
    monkeypatch.setattr(ec, "lookup", current_lookup)
    monkeypatch.setattr(ec, "resolve_by_contract_sha256", historical_resolver)
    monkeypatch.setattr(
        s8b_floor_campaign.env_attestation,
        "load_verified_calibration",
        calibration_loader,
    )
    out_root = tmp_path / "out"

    with pytest.raises(s8b_floor_campaign.FloorCampaignError):
        _private_run_campaign(
            protocol, _verified_freeze(freeze), out_root=out_root, mode="pilot",
            measure_fn=measure_fn,
            durable_root_policy=_durable_policy(out_root),
        )

    current_lookup.assert_called_once_with(ENV_TAG)
    historical_resolver.assert_not_called()
    calibration_loader.assert_not_called()
    measure_fn.assert_not_called()
    assert not out_root.exists()


def test_current_admission_reuses_exact_contract_across_successful_run(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    contract = ec.lookup(ENV_TAG)
    protocol = _protocol(
        freeze_sha=_freeze_sha(freeze),
        contract_sha256=contract.contract_sha256,
    )
    verified = _verified_freeze(freeze)
    current_lookup = mock.Mock(return_value=contract)
    real_calibration = env_attestation.load_verified_calibration
    real_projection = s8b_floor_campaign._project_measure_run_cmd
    fake_build = _make_fake_build(tmp_path / "bin")
    seen = {
        "calibration": [], "receipt": [], "build": [], "command_receipt": [],
    }

    def calibration_spy(candidate, repo_root):
        seen["calibration"].append(candidate)
        return real_calibration(candidate, repo_root)

    def receipt_spy(candidate, *, now_fn):
        seen["receipt"].append(candidate)
        return _fixed_receipt(candidate, now_fn=now_fn)

    def build_spy(*args, **kwargs):
        seen["build"].append(kwargs["contract"])
        return fake_build(*args, **kwargs)

    def projection_spy(*args, **kwargs):
        seen["command_receipt"].append(kwargs["contract"])
        return real_projection(*args, **kwargs)

    def measure_fn(binary, records, threads, workload):
        argv = list(s8b_floor_campaign.build_portable_run_cmd(
            binary="output/fixture/bench", workload=workload,
            records=records, threads=threads, extime_s=protocol["extime_s"],
            clocks_per_us=contract.clocks_per_us, numactl=contract.numactl,
        ))
        argv[argv.index("--") + 1] = str(binary)
        return _FakeScalePoint(
            throughputs=[1000.0] * protocol["reps"], notes=[],
            run_cmd=shlex.join(argv),
        )

    monkeypatch.setattr(ec, "lookup", current_lookup)
    monkeypatch.setattr(
        s8b_floor_campaign.env_attestation,
        "load_verified_calibration",
        calibration_spy,
    )
    monkeypatch.setattr(
        s8b_floor_campaign, "_project_measure_run_cmd", projection_spy,
    )

    outcome = _private_run_campaign(
        protocol, verified, out_root=tmp_path / "out", mode="pilot",
        measure_fn=measure_fn, probe_fn=lambda: (1, "", ""),
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(),
        sleep_fn=lambda _seconds: None, monotonic_fn=lambda: 0.0,
        prepare_fn=_fake_prepare, now_fn=lambda: _FIXED_NOW,
        execution_receipt_fn=receipt_spy, build_fn=build_spy,
        durable_root_policy=_durable_policy(tmp_path / "out"),
    )

    assert outcome["status"] == "completed"
    # resolver の index 候補絞り込みと admission 本体が各 1 回、現行契約を引く。
    assert current_lookup.call_args_list == [mock.call(ENV_TAG)] * 2
    assert len(seen["calibration"]) == 1
    assert len(seen["receipt"]) == 1
    assert len(seen["build"]) == len(_CONFIGS) * len(_HOLDOUT_SHAPE)
    assert len(seen["command_receipt"]) == (
        len(_CONFIGS) * len(_HOLDOUT_SHAPE) * protocol["n_sessions"]
    )
    assert all(candidate is contract for calls in seen.values() for candidate in calls)


def test_resume_under_unchanged_current_contract_generation_completes(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with _official_test_seam(monkeypatch):
        crashing_measure, _ = _crash_at(2)
        with pytest.raises(_SimulatedCrash):
            _run_campaign(
                protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                measure_fn=crashing_measure, probe_fn=lambda: (1, "", ""),
                mode="official",
            )
        run_dir = _only_run_dir(out_root)
        resume_measure = _make_measure_fn(
            reps=5, value_fn=lambda cid: _BASE_TPS[cid],
        )
        outcome = _run_campaign(
            protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
            measure_fn=resume_measure, probe_fn=lambda: (1, "", ""),
            mode="official", resume_dir=run_dir,
        )

    assert outcome["status"] == "completed"
    assert resume_measure.call_details


def test_resume_rejects_recorded_g1_when_current_contract_is_g2_before_calibration(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with _official_test_seam(monkeypatch) as scoped:
        crashing_measure, _ = _crash_at(2)
        with pytest.raises(_SimulatedCrash):
            _run_campaign(
                protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                measure_fn=crashing_measure, probe_fn=lambda: (1, "", ""),
                mode="official",
            )
        run_dir = _only_run_dir(out_root)
        journal_path = run_dir / "journal.jsonl"
        journal_before = journal_path.read_bytes()
        g1, g2 = _patch_current_contract_to_synthetic_successor(scoped)
        assert protocol["contract_sha256"] == g1.contract_sha256
        assert protocol["contract_sha256"] != g2.contract_sha256

        real_load = s8b_floor_campaign.env_attestation.load_verified_calibration
        calibration_calls = []

        def calibration_spy(*args, **kwargs):
            calibration_calls.append((args, kwargs))
            return real_load(*args, **kwargs)

        scoped.setattr(
            s8b_floor_campaign.env_attestation,
            "load_verified_calibration",
            calibration_spy,
        )
        resume_measure = mock.Mock(
            side_effect=AssertionError("current 不一致の resume で計測してはいけない"),
        )

        with pytest.raises(s8b_floor_campaign.FloorCampaignError):
            _run_campaign(
                protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                measure_fn=resume_measure, probe_fn=lambda: (1, "", ""),
                mode="official", resume_dir=run_dir,
            )

        assert calibration_calls == []
        resume_measure.assert_not_called()
        assert journal_path.read_bytes() == journal_before


def test_official_resume_rejects_tampered_certificate(tmp_path, monkeypatch):
    repo_before = _real_output_snapshot()
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with _official_test_seam(monkeypatch):
        crashing_measure, _ = _crash_at(2)
        with pytest.raises(_SimulatedCrash):
            _run_campaign(
                protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                measure_fn=crashing_measure, probe_fn=lambda: (1, "", ""), mode="official",
            )
        run_dir = _only_run_dir(out_root)
        cert_path = run_dir / "launch_certificate.json"
        cert_path.write_bytes(cert_path.read_bytes() + b" ")
        with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="certificate bytes"):
            _run_campaign(
                protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                measure_fn=_forbid_measure, probe_fn=lambda: (1, "", ""), mode="official",
                resume_dir=run_dir,
            )
    assert repo_before == _real_output_snapshot()


def test_official_resume_rejects_launch_start_utc_not_bound_to_certificate(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with _official_test_seam(monkeypatch):
        crashing_measure, _ = _crash_at(2)
        with pytest.raises(_SimulatedCrash):
            _run_campaign(
                protocol, _verified_freeze(freeze), out_root=out_root,
                build_root=tmp_path / "bin", measure_fn=crashing_measure,
                probe_fn=lambda: (1, "", ""), mode="official",
            )
        run_dir = _only_run_dir(out_root)
        journal_path = run_dir / "journal.jsonl"
        records = _read_journal_lines(journal_path)
        records[0]["utc"] = "2026-01-01T00:00:01+00:00"
        journal_path.write_text(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
            encoding="utf-8",
        )

        with pytest.raises(
                s8b_floor_campaign.FloorCampaignError,
                match="resume: launch-start.utc が certificate.started_utc と不一致"):
            _run_campaign(
                protocol, _verified_freeze(freeze), out_root=out_root,
                build_root=tmp_path / "bin", measure_fn=_forbid_measure,
                probe_fn=lambda: (1, "", ""), mode="official", resume_dir=run_dir,
            )


def test_official_resume_rejects_extra_launch_start_key(tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with _official_test_seam(monkeypatch):
        crashing_measure, _ = _crash_at(2)
        with pytest.raises(_SimulatedCrash):
            _run_campaign(
                protocol, _verified_freeze(freeze), out_root=out_root,
                build_root=tmp_path / "bin", measure_fn=crashing_measure,
                probe_fn=lambda: (1, "", ""), mode="official",
            )
        run_dir = _only_run_dir(out_root)
        journal_path = run_dir / "journal.jsonl"
        records = _read_journal_lines(journal_path)
        records[0]["extra"] = "unexpected"
        journal_path.write_text(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
            encoding="utf-8",
        )

        with pytest.raises(
                s8b_floor_campaign.FloorCampaignError,
                match="resume: launch-start の exact key 集合が不一致"):
            _run_campaign(
                protocol, _verified_freeze(freeze), out_root=out_root,
                build_root=tmp_path / "bin", measure_fn=_forbid_measure,
                probe_fn=lambda: (1, "", ""), mode="official", resume_dir=run_dir,
            )


def test_official_resume_rejects_renamed_run_dir(tmp_path, monkeypatch):
    repo_before = _real_output_snapshot()
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with _official_test_seam(monkeypatch):
        crashing_measure, _ = _crash_at(2)
        with pytest.raises(_SimulatedCrash):
            _run_campaign(
                protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                measure_fn=crashing_measure, probe_fn=lambda: (1, "", ""), mode="official",
            )
        run_dir = _only_run_dir(out_root)
        renamed = run_dir.with_name("renamed-" + run_dir.name)
        run_dir.rename(renamed)
        with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="campaign_run_id"):
            _run_campaign(
                protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                measure_fn=_forbid_measure, probe_fn=lambda: (1, "", ""), mode="official",
                resume_dir=renamed,
            )
    assert repo_before == _real_output_snapshot()


def test_official_resume_rejects_certificate_time_not_bound_to_run_id(
        tmp_path, monkeypatch):
    repo_before = _real_output_snapshot()
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    with _official_test_seam(monkeypatch):
        crashing_measure, _ = _crash_at(2)
        with pytest.raises(_SimulatedCrash):
            _run_campaign(
                protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                measure_fn=crashing_measure, probe_fn=lambda: (1, "", ""),
                mode="official",
            )
        run_dir = _only_run_dir(out_root)
        cert_path = run_dir / "launch_certificate.json"
        cert = json.loads(cert_path.read_bytes())
        cert["started_utc"] = "2026-01-01T00:00:01+00:00"
        cert_path.write_text(
            json.dumps(cert, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        cert_sha = hashlib.sha256(cert_path.read_bytes()).hexdigest()
        journal_path = run_dir / "journal.jsonl"
        records = _read_journal_lines(journal_path)
        for record in records:
            if record.get("event") in {"launch-start", "campaign-start"}:
                record["launch_certificate_sha256"] = cert_sha
        journal_path.write_text(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
            encoding="utf-8",
        )
        with pytest.raises(
                s8b_floor_campaign.FloorCampaignError, match="秒単位で不一致"):
            _run_campaign(
                protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                measure_fn=_forbid_measure, probe_fn=lambda: (1, "", ""),
                mode="official", resume_dir=run_dir,
            )
    assert repo_before == _real_output_snapshot()


@pytest.mark.parametrize("contamination", ["certificate-file", "launch-start", "campaign-key"])
def test_pilot_resume_rejects_launch_certificate_contamination(
        tmp_path, contamination):
    repo_before = _real_output_snapshot()
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    crashing_measure, _ = _crash_at(2)
    with pytest.raises(_SimulatedCrash):
        _run_campaign(
            protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
            measure_fn=crashing_measure, probe_fn=lambda: (1, "", ""),
        )
    run_dir = _only_run_dir(out_root)
    journal_path = run_dir / "journal.jsonl"
    if contamination == "certificate-file":
        (run_dir / "launch_certificate.json").write_text("{}\n", encoding="utf-8")
    elif contamination == "launch-start":
        s8b_floor_campaign._journal_append(journal_path, {"event": "launch-start"})
    else:
        records = _read_journal_lines(journal_path)
        next(record for record in records if record.get("event") == "campaign-start")[
            "launch_certificate_sha256"] = "0" * 64
        journal_path.write_text(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
            encoding="utf-8",
        )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="pilot"):
        _run_campaign(
            protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
            measure_fn=_forbid_measure, probe_fn=lambda: (1, "", ""), resume_dir=run_dir,
        )
    assert repo_before == _real_output_snapshot()


def test_pilot_path_has_no_launch_certificate_changes(tmp_path):
    repo_before = _real_output_snapshot()
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    outcome = _run_campaign(
        protocol, verified, out_root=tmp_path / "out", build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
        probe_fn=lambda: (1, "", ""),
    )
    run_dir = Path(outcome["run_dir"])
    assert not (run_dir / "launch_certificate.json").exists()
    journal = _read_journal_lines(run_dir / "journal.jsonl")
    campaign_start = next(
        record for record in journal if record.get("event") == "campaign-start"
    )
    assert "launch_certificate_sha256" not in campaign_start
    assert all("launch_certificate_sha256" not in record
               for record in outcome["result"]["wall_ledger"])
    assert outcome["result"]["eligible_for_refreeze"] is False
    assert repo_before == _real_output_snapshot()


def test_binary_receipt_mismatch_aborts(tmp_path):
    # 実測直前 hash が build 記録 (binary_sha256) と食い違えば CampaignAbort (C3-6)。
    binf = tmp_path / "bin.exe"
    binf.write_bytes(b"real binary bytes")
    cell_id = "rr79::stock_common"
    cell = {"cell_id": cell_id, "holdout_id": "rr79", "configuration_id": "stock_common",
            "records": 1, "threads": 1, "workload": {"ycsb": {}}}
    binaries = {cell_id: {"binary": str(binf), "binary_sha256": "0" * 64}}  # 記録が偽
    runner = s8b_floor_campaign._Runner(
        protocol=_valid_protocol_dict(), contract=ec.lookup(ENV_TAG),
        cells=[cell], cell_by_id={cell_id: cell},
        binaries=binaries, artifact_binaries={cell_id: {"binary": "output/fixture/bench"}},
        schedule=[], journal_path=tmp_path / "j.jsonl",
        holdout_admissions={cell_id: SimpleNamespace(observation=None)},
        measure_fn=lambda *a: _FakeScalePoint([1.0] * 5, [], "x"),
        probe_fn=lambda: (1, "", ""), sleep_fn=lambda s: None,
        monotonic_fn=lambda: 0.0, now_fn=lambda: _FIXED_NOW,
        protocol_sha256="p", freeze_sha256="f", manifest_sha256="m",
        holdout_assert_fn=lambda *_args, **_kwargs: None,
    )
    with pytest.raises(s8b_floor_campaign.CampaignAbort):
        runner._run_session(seq=0, round_no=0, cell_id=cell_id, kind="planned",
                            retry_ordinal=None, trigger=None)


def test_binary_receipt_recorded_in_session_journal(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "out",
                            build_root=tmp_path / "bin", measure_fn=measure_fn,
                            probe_fn=lambda: (1, "", ""))
    run_dir = _only_run_dir(tmp_path / "out")
    binaries = json.loads((run_dir / "manifest.json").read_bytes())["binaries"]
    for s in outcome["result"]["sessions"]:
        # 実測直前 hash が journal に記録され、build 記録と一致する。
        rec = binaries[s["cell_id"]]
        assert s["binary_sha256_at_measure"] == rec["binary_sha256"]


def test_resume_store_missing_store_path_rejected(tmp_path):
    """store_path 欠落 rec は silent skip でなく fail-closed (正当な消費者のない緩和を置かない)。"""
    built = {"cell-1": {"binary_sha256": "0" * 64}}
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="store_path 欠落"):
        s8b_floor_campaign._verify_resume_store(built, tmp_path)


def test_content_addressed_store_create_only(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    out_root = tmp_path / "out"
    outcome = _run_campaign(protocol, verified, out_root=out_root,
                            build_root=tmp_path / "bin", measure_fn=measure_fn,
                            probe_fn=lambda: (1, "", ""))
    binaries = json.loads((Path(outcome["run_dir"]) / "manifest.json").read_bytes())["binaries"]
    for cell_id, rec in binaries.items():
        store_path = rec.get("store_path")
        assert store_path, cell_id
        stored = out_root / store_path
        assert stored.is_file()
        assert hashlib.sha256(stored.read_bytes()).hexdigest() == rec["binary_sha256"]
        # content-addressed: store 名が sha256 で終わる。
        assert stored.name == rec["binary_sha256"]

    # emitted artifact record を store へ直接戻さず、out_root 基準で runtime view に解決する。
    built = s8b_floor_campaign.resolve_portable_built(binaries, out_root=out_root)
    store_root = stored.parent
    s8b_floor_campaign.store_binaries(
        built, store_root, out_root=out_root,
        expected_ccbench_pin=protocol["ccbench_pin"],
        expected_contract_sha256=protocol["contract_sha256"],
    )  # 例外なし


def test_sort_best_swo_pass_receipt_reaches_manifest_and_result(tmp_path):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    outcome = _run_campaign(
        protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
        build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(
            reps=5, value_fn=lambda cid: _BASE_TPS[cid],
        ),
        probe_fn=lambda: (1, "", ""),
    )
    manifest = json.loads(
        (Path(outcome["run_dir"]) / "manifest.json").read_bytes()
    )
    result = outcome["result"]
    for cell_id, record in manifest["binaries"].items():
        if record["configuration_id"] == "sort_best":
            assert record["sort_swo_oracle"] == (
                result["binaries"][cell_id]["sort_swo_oracle"]
            )
        else:
            assert "sort_swo_oracle" not in record
            assert "sort_swo_oracle" not in result["binaries"][cell_id]


def test_public_artifacts_omit_raw_swo_host_values(tmp_path):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    outcome = _run_campaign(
        protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
        build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(
            reps=5, value_fn=lambda cid: _BASE_TPS[cid],
        ),
        probe_fn=lambda: (1, "", ""),
    )
    run_dir = Path(outcome["run_dir"])
    manifest = json.loads((run_dir / "manifest.json").read_bytes())
    result = json.loads((run_dir / "result.json").read_bytes())
    public_json = json.dumps(
        {"manifest": manifest, "result": result},
        ensure_ascii=False, sort_keys=True,
    )
    assert "/fixture/toolchain/bin/c++" not in public_json
    assert "/fixture/dependencies" not in public_json
    assert "fixture-c++ 1.0 日本語" not in public_json
    for artifact in (manifest, result):
        for record in artifact["binaries"].values():
            receipt = record.get("sort_swo_oracle", {})
            assert "compiler_version" not in receipt
            assert "compiler_realpath" not in receipt
            assert "dependency_root_realpath" not in receipt


def test_configured_marker_root_keeps_raw_swo_attempt_private(tmp_path):
    freeze = _freeze_document()
    cells = s8b_floor_campaign.enumerate_cells(
        freeze, stock_configuration=_STOCK,
    )
    marker_root = tmp_path / "private-markers"
    marker_root.mkdir()
    contract = ec.lookup(ENV_TAG)
    built = s8b_floor_campaign.build_cells(
        freeze, cells, ccbench_pin="0" * 40,
        out_root=tmp_path / "out", prepare_fn=_fake_prepare,
        contract=contract,
        verified_calibration=env_attestation.load_verified_calibration(
            contract, ROOT,
        ),
        build_fn=_make_fake_build(tmp_path / "bin"),
        phase_marker_root=marker_root,
    )
    private_files = sorted(marker_root.glob("sort-swo-oracle-pass-*.json"))
    assert len(private_files) == len(_HOLDOUT_SHAPE)
    for path in private_files:
        document = json.loads(path.read_bytes())
        assert set(document) == {
            "schema", "cell_id", "oracle_attempt", "portable_receipt",
        }
        assert document["schema"] == "s8b-sort-swo-private-evidence/v1"
        assert document["oracle_attempt"]["oracle_receipt"][
            "compiler_realpath"
        ] == "/fixture/toolchain/bin/c++"
        assert document["portable_receipt"] == (
            built[document["cell_id"]]["sort_swo_oracle"]
        )
        assert path.stat().st_mode & 0o777 == 0o600


def test_sort_best_cell_without_swo_receipt_is_rejected(tmp_path):
    @contextlib.contextmanager
    def missing_sort_receipt(cell, ccbench_pin, *, cxx):
        with _fake_prepare(cell, ccbench_pin, cxx=cxx) as prepared:
            if cell["configuration"] == "sort_best":
                prepared = dataclasses.replace(prepared, oracle_attempt=None)
            yield prepared

    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="sort_best cell に SWO PASS receipt がない"):
        _run_campaign(
            protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
            build_root=tmp_path / "bin", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=missing_sort_receipt,
        )


def test_non_sort_cell_with_swo_receipt_is_rejected(tmp_path):
    @contextlib.contextmanager
    def extra_non_sort_receipt(cell, ccbench_pin, *, cxx):
        with _fake_prepare(cell, ccbench_pin, cxx=cxx) as prepared:
            if cell["configuration"] != "sort_best":
                prepared = dataclasses.replace(
                    prepared, oracle_attempt=fake_sort_swo_pass_attempt(),
                )
            yield prepared

    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="non-sort cell に SWO receipt がある"):
        _run_campaign(
            protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
            build_root=tmp_path / "bin", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=extra_non_sort_receipt,
        )


@pytest.mark.parametrize(
    "category,cause",
    [
        pytest.param(
            "unverifiable", "main-ledger-missing", id="missing",
        ),
        pytest.param(
            "mismatch", "main-ledger-row-mismatch", id="mismatch",
        ),
    ],
)
def test_admission_failure_creates_no_result_pending_bytes(
        tmp_path, monkeypatch, category, cause):
    def reject_inspection(**_kwargs):
        raise s8b_floor_campaign._holdout_admission.FloorHoldoutEvidenceError(
            category=category, reason=cause,
        )

    monkeypatch.setattr(
        s8b_floor_campaign._holdout_admission,
        "inspect_floor_holdout_admission_evidence",
        reject_inspection,
    )
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="floor admission evidence が不正"):
        _run_campaign(
            protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
            build_root=tmp_path / "bin",
            measure_fn=_make_measure_fn(
                reps=5, value_fn=lambda cid: _BASE_TPS[cid],
            ),
            probe_fn=lambda: (1, "", ""),
        )
    run_dir = _only_run_dir(tmp_path / "out")
    assert not (run_dir / ".result.json.pending").exists()
    assert not (run_dir / ".result.md.pending").exists()
    assert not (run_dir / "result.json").exists()
    assert not (run_dir / "result.md").exists()
    terminal = _read_journal_lines(run_dir / "journal.jsonl")[-1]
    assert terminal["status"] == "artifact-invalid"
    assert terminal["reason"] == f"floor-admission-{category}"
    assert terminal["cause"] == cause


def test_sort_receipt_identity_transplant_is_rejected(tmp_path):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    outcome = _run_campaign(
        protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
        build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(
            reps=5, value_fn=lambda cid: _BASE_TPS[cid],
        ),
        probe_fn=lambda: (1, "", ""),
    )
    tampered = copy.deepcopy(outcome["result"]["binaries"])
    sort_id = next(
        cell_id for cell_id, record in tampered.items()
        if record["configuration_id"] == "sort_best"
    )
    other_id = next(cell_id for cell_id in tampered if cell_id != sort_id)
    tampered[sort_id]["sort_swo_oracle"]["cell_id"] = other_id
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="receipt.*不正|identity"):
        s8b_floor_campaign._validate_portable_built(
            tampered,
            expected_ccbench_pin=protocol["ccbench_pin"],
            expected_contract_sha256=protocol["contract_sha256"],
        )


@pytest.mark.parametrize(
    "cells,binaries",
    [
        pytest.param(
            [{
                "cell_id": "h::sort_best", "holdout_id": "h",
                "configuration_id": "sort_best",
            }],
            {},
            id="empty-binaries",
        ),
        pytest.param(
            [
                {
                    "cell_id": "h::sort_best", "holdout_id": "h",
                    "configuration_id": "sort_best",
                },
                {
                    "cell_id": "h::stock", "holdout_id": "h",
                    "configuration_id": "stock",
                },
            ],
            {
                "h::sort_best": {
                    "cell_id": "h::sort_best", "holdout_id": "h",
                    "configuration_id": "sort_best",
                },
            },
            id="whole-cell-missing",
        ),
    ],
)
@pytest.mark.parametrize("entrypoint", ["manifest", "result"])
def test_producer_rejects_incomplete_binary_coverage(
        cells, binaries, entrypoint):
    with pytest.raises(
            s8b_floor_campaign.FloorCampaignError,
            match="完全被覆"):
        if entrypoint == "manifest":
            s8b_floor_campaign.assemble_manifest(
                protocol={}, protocol_sha256="p" * 64,
                freeze_sha256="f" * 64, cells=cells, built=binaries,
                schedule=[], mode="pilot",
            )
        else:
            s8b_floor_campaign.assemble_result(
                protocol={}, mode="pilot", protocol_sha256="p" * 64,
                freeze_sha256="f" * 64, manifest_sha256="m" * 64,
                cells=cells, binaries=binaries, records=[],
                holdout_admission={},
            )


@pytest.mark.parametrize(
    "cells,binaries,reason",
    [
        pytest.param([], {}, "非空", id="empty-cells"),
        pytest.param(
            [
                {
                    "cell_id": "h::sort_best", "holdout_id": "h",
                    "configuration_id": "sort_best",
                },
                {
                    "cell_id": "h::sort_best", "holdout_id": "h",
                    "configuration_id": "sort_best",
                },
            ],
            {}, "重複", id="duplicate-cell-id",
        ),
        pytest.param(
            [{
                "cell_id": "h::stock", "holdout_id": "h",
                "configuration_id": "stock",
            }],
            {"h::stock": {
                "cell_id": "h::stock", "holdout_id": "h",
                "configuration_id": "stock",
            }},
            "sort_best", id="sort-best-missing",
        ),
        pytest.param(
            [
                {
                    "cell_id": "h::sort-best-a", "holdout_id": "h",
                    "configuration_id": "sort_best",
                },
                {
                    "cell_id": "h::sort-best-b", "holdout_id": "h",
                    "configuration_id": "sort_best",
                },
            ],
            {}, "sort_best", id="sort-best-duplicate",
        ),
        pytest.param(
            [{
                "cell_id": "h::sort_best", "holdout_id": "h",
                "configuration_id": "sort_best",
            }],
            {"h::sort_best": {
                "cell_id": "h::sort_best", "holdout_id": "other",
                "configuration_id": "sort_best",
            }},
            "対応 cell", id="binary-identity-mismatch",
        ),
    ],
)
def test_producer_binary_coverage_rejects_cell_invariants(
        cells, binaries, reason):
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match=reason):
        s8b_floor_campaign._validate_binaries_cover_cells(binaries, cells)


def test_verify_floor_artifact_binaries_positive_and_negative(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    out_root = tmp_path / "out"
    outcome = _run_campaign(
        protocol, verified, out_root=out_root,
        build_root=tmp_path / "bin", measure_fn=measure_fn,
        probe_fn=lambda: (1, "", ""),
    )
    result = outcome["result"]
    expected_protocol = s8b_floor_campaign._expected_protocol(
        s8b_floor_campaign.validate_protocol(protocol),
        s8b_floor_campaign.enumerate_cells(freeze, stock_configuration=_STOCK),
    )
    # 正例: binaries 整合 + journal receipt (expected_binaries) 突合が空リスト。
    expected_binaries = {cid: rec["binary_sha256"]
                         for cid, rec in result["binaries"].items()}
    live_admission = _live_holdout_admission_for_outcome(
        protocol=protocol, freeze_doc=verified,
        out_root=out_root, outcome=outcome,
    )
    assert s8b_floor_stats.verify_floor_artifact(
        result, expected_protocol, expected_binaries,
        expected_holdout_admission=live_admission,
        expected_use_perf=True,
    ) == []

    # 負例1: bin_hash_short を binary_sha256[:16] と食い違わせる。
    tampered = json.loads(json.dumps(result))
    any_cid = next(iter(tampered["binaries"]))
    tampered["binaries"][any_cid]["bin_hash_short"] = "deadbeefdeadbeef"
    assert s8b_floor_stats.verify_floor_artifact(
        tampered, expected_protocol,
        expected_holdout_admission=live_admission,
        expected_use_perf=True,
    )

    # 負例2: journal receipt (expected_binaries) と binary_sha256 が不一致。
    bad_receipts = dict(expected_binaries)
    bad_receipts[any_cid] = "f" * 64
    assert s8b_floor_stats.verify_floor_artifact(
        result, expected_protocol, bad_receipts,
        expected_holdout_admission=live_admission,
        expected_use_perf=True,
    )

    # 負例3: binaries からセルを欠落させる (完全集合が崩れる)。
    dropped = json.loads(json.dumps(result))
    dropped["binaries"].pop(any_cid)
    assert s8b_floor_stats.verify_floor_artifact(
        dropped, expected_protocol,
        expected_holdout_admission=live_admission,
        expected_use_perf=True,
    )


def test_pilot_cli_broken_freeze_emits_structured_error_not_traceback(tmp_path):
    freeze_path = tmp_path / "freeze.json"
    freeze_path.write_text("{}", encoding="utf-8")
    protocol = _protocol(freeze_sha="0" * 64)
    protocol["freeze"]["path"] = str(freeze_path)
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")

    script = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {str(ORCHESTRATOR.parent)!r})
        from orchestrator.campaign import s8b_floor_campaign as floor
        sys.exit(floor.main(["--mode", "pilot", "--protocol", {str(protocol_path)!r}]))
        """
    )
    proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    assert proc.returncode == 1, (proc.returncode, proc.stdout, proc.stderr)
    assert "Traceback" not in proc.stderr, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "error"
    assert "FloorCampaignError" in payload["error"]
    assert "expected_hash" in payload["error"]


# =========================================================================== #
# 18. certified production launcher / attempt-registry v5 wiring               #
# =========================================================================== #

def _new_certified_attempt_case(tmp_path: Path) -> dict[str, object]:
    """Create real holdout issuer state for one focused production attempt."""

    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = s8b_floor_campaign.validate_protocol(
        _protocol(freeze_sha=_freeze_sha(freeze))
    )
    out_root = tmp_path / "out"
    authority = _test_holdout_authority(out_root, protocol, verified)
    cells = s8b_floor_campaign.enumerate_cells(
        freeze, stock_configuration=protocol["stock_configuration"],
    )
    admission_cells = [
        s8b_floor_campaign._admission_cell(cell) for cell in cells
    ]
    schedule = s8b_floor_campaign.build_schedule(
        cells=cells, master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    protocol_sha256 = s8b_floor_campaign._canonical_sha256(protocol)
    run_id = "certified-focused-run"
    run_relpath = (
        f"env/{protocol['env_tag']}/calibration/s8b-floor-pilot/{run_id}"
    )
    run_dir = out_root / run_relpath
    run_dir.mkdir(parents=True)
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps({
        "schema_version": s8b_floor_campaign.MANIFEST_SCHEMA,
        "protocol_sha256": protocol_sha256,
        "freeze_sha256": _freeze_sha(freeze),
        "reps": protocol["reps"],
    }, sort_keys=True) + "\n", encoding="utf-8")
    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    reservation_state = (
        s8b_floor_campaign._holdout_admission
        ._reserve_floor_holdout_observations_core(
            repo_root=authority, protocol=protocol,
            verified_freeze_document=freeze,
            freeze_sha256=_freeze_sha(freeze),
            cells=admission_cells, schedule=schedule,
            campaign_run_id=run_id, out_root=out_root, run_dir=run_dir,
            run_relpath=run_relpath, mode="pilot", resume=False,
            nondefault_seams=[], _neutral_holdouts=freeze["holdouts"],
        )
    )
    admissions = (
        s8b_floor_campaign._holdout_admission
        .finalize_floor_holdout_admissions(reservation_state)
    )
    cell = cells[0]
    schedule_row = next(
        row for row in schedule if row["cell_id"] == cell["cell_id"]
    )
    attempt_id = s8b_floor_campaign._attempt_id(
        cell["cell_id"], "planned", schedule_row["seq"], None,
    )
    campaign_start = {
        "event": "campaign-start", "schema": s8b_floor_campaign.JOURNAL_SCHEMA,
        "protocol_sha256": protocol_sha256,
        "freeze_sha256": _freeze_sha(freeze),
        "manifest_sha256": manifest_sha256,
        "hostname": "certified-test-host", "boot_id": None,
        "job_id": None, "cpuset": None,
        "utc": "2026-01-01T00:00:00+00:00",
        "pid": 123, "starttime": 456, "execution_uuid": "1" * 32,
    }
    session_start = {
        "event": "session-start", "seq": schedule_row["seq"],
        "kind": "planned", "cell_id": cell["cell_id"],
        "round": schedule_row["round"], "retry_ordinal": None,
        "attempt_id": attempt_id, "trigger": None,
        "started_iso": campaign_start["utc"],
    }
    journal_path = run_dir / "journal.jsonl"
    journal_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in (
            campaign_start, session_start,
        )),
        encoding="utf-8",
    )
    binary = tmp_path / "non-executable-benchmark"
    binary.write_bytes(b"not an executable")
    binary_sha256 = hashlib.sha256(binary.read_bytes()).hexdigest()
    plan = s8b_floor_campaign._build_floor_attempt_registry_plan(
        protocol=protocol, cells=cells, schedule=schedule,
        freeze_sha256=_freeze_sha(freeze), protocol_sha256=protocol_sha256,
    )
    runner = s8b_floor_campaign._Runner(
        protocol=protocol, contract=ec.lookup(protocol["env_tag"]),
        cells=[cell], cell_by_id={cell["cell_id"]: cell},
        binaries={cell["cell_id"]: {
            "binary": str(binary), "binary_sha256": binary_sha256,
        }},
        artifact_binaries={cell["cell_id"]: {"binary": "portable-benchmark"}},
        schedule=schedule, journal_path=journal_path,
        measure_fn=lambda *_args: pytest.fail("legacy measure path was called"),
        holdout_admissions={cell["cell_id"]: admissions[cell["cell_id"]]},
        probe_fn=lambda: pytest.fail("legacy probe path was called"),
        sleep_fn=lambda _seconds: None, monotonic_fn=lambda: 0.0,
        now_fn=lambda: _FIXED_NOW, protocol_sha256=protocol_sha256,
        freeze_sha256=_freeze_sha(freeze), manifest_sha256=manifest_sha256,
        perf_preflight=_perf_receipt(available=False), mode="pilot",
        records=[campaign_start, session_start],
        certified_attempt_context=(
            s8b_floor_campaign._CertifiedFloorAttemptContext(
                repo_root=authority, campaign_run_id=run_id,
                run_relpath=run_relpath, registry_plan=plan,
            )
        ),
    )
    runner._certified_run_start_record = campaign_start
    return {
        "authority": authority, "freeze": freeze, "protocol": protocol,
        "cells": cells, "schedule": schedule, "cell": cell,
        "schedule_row": schedule_row, "attempt_id": attempt_id,
        "manifest_sha256": manifest_sha256, "run_id": run_id,
        "run_relpath": run_relpath, "run_dir": run_dir,
        "journal_path": journal_path, "runner": runner, "plan": plan,
    }


def _run_certified_attempt_case(
        case: Mapping[str, object], monkeypatch, *, competing: bool) -> dict:
    monkeypatch.setattr(
        s8b_floor_campaign.s8b_floor_attempt_launcher,
        "_owned_post_probe",
        lambda: {
            "rc": 0 if competing else 1,
            "stdout": "competitor" if competing else "",
            "stderr": "",
            "competing": competing,
        },
    )
    runner = case["runner"]
    row = case["schedule_row"]
    cell = case["cell"]
    return runner._run_session(
        seq=row["seq"], round_no=row["round"],
        cell_id=cell["cell_id"], kind="planned",
        retry_ordinal=None, trigger=None,
        _cut6_authorization_already_recorded=True,
    )


def _inspect_certified_attempt_case(case: Mapping[str, object]):
    runner = case["runner"]
    return (
        s8b_floor_campaign._holdout_admission
        .inspect_floor_holdout_admission_evidence(
            repo_root=case["authority"], protocol=case["protocol"],
            verified_freeze_document=case["freeze"],
            freeze_sha256=_freeze_sha(case["freeze"]),
            manifest_sha256=case["manifest_sha256"],
            campaign_run_id=case["run_id"], run_relpath=case["run_relpath"],
            mode="pilot", cells=case["cells"], schedule=case["schedule"],
            sessions=[
                record for record in runner.records
                if record.get("event") in {"session-start", "session"}
            ],
        )
    )


def _first_clean_then_competing_probe():
    calls = 0

    def probe():
        nonlocal calls
        calls += 1
        competing = calls > 2
        return {
            "rc": 0 if competing else 1,
            "stdout": "competitor" if competing else "",
            "stderr": "", "competing": competing,
        }

    return probe


def _first_two_clean_then_competing_probe():
    calls = 0

    def probe():
        nonlocal calls
        calls += 1
        competing = calls > 4
        return {
            "rc": 0 if competing else 1,
            "stdout": "competitor" if competing else "",
            "stderr": "", "competing": competing,
        }

    return probe


def test_default_production_attempt_uses_certified_launcher_once(
        tmp_path, monkeypatch):
    case = _new_certified_attempt_case(tmp_path)
    launcher = s8b_floor_campaign.s8b_floor_attempt_launcher
    certified = mock.Mock(wraps=launcher.launch_probed_floor_attempt)
    monkeypatch.setattr(launcher, "launch_probed_floor_attempt", certified)

    record = _run_certified_attempt_case(case, monkeypatch, competing=False)

    assert certified.call_count == 1
    assert record["retry_ordinal"] is None
    rows = launcher.read_floor_attempt_registry(
        case["authority"], case["plan"],
    )
    assert [row["event"] for row in rows].count("terminal") == 1


def test_registry_plan_declares_exact_planned_and_retry_slot_closure():
    freeze = _freeze_document()
    protocol = s8b_floor_campaign.validate_protocol(
        _protocol(freeze_sha=_freeze_sha(freeze))
    )
    cells = s8b_floor_campaign.enumerate_cells(
        freeze, stock_configuration=protocol["stock_configuration"],
    )
    schedule = s8b_floor_campaign.build_schedule(
        cells=cells, master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    plan = s8b_floor_campaign._build_floor_attempt_registry_plan(
        protocol=protocol, cells=cells, schedule=schedule,
        freeze_sha256=_freeze_sha(freeze),
        protocol_sha256=s8b_floor_campaign._canonical_sha256(protocol),
    )
    cell_by_id = {cell["cell_id"]: cell for cell in cells}
    expected = {
        (
            cell_by_id[row["cell_id"]]["holdout_id"],
            cell_by_id[row["cell_id"]]["configuration_id"],
            row["round"] - 1, measurement_ordinal, 0,
        )
        for row in schedule
        for measurement_ordinal in range(protocol["retry_slots_per_cell"] + 1)
    }
    actual = set(
        s8b_floor_campaign.s8b_floor_attempt_launcher
        .floor_attempt_registry_plan_slot_ids(plan)
    )
    assert actual == expected


def test_registry_plan_maps_round_to_zero_based_repetition():
    freeze = _freeze_document()
    protocol = s8b_floor_campaign.validate_protocol(
        _protocol(freeze_sha=_freeze_sha(freeze))
    )
    cells = s8b_floor_campaign.enumerate_cells(
        freeze, stock_configuration=protocol["stock_configuration"],
    )
    schedule = s8b_floor_campaign.build_schedule(
        cells=cells, master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    plan = s8b_floor_campaign._build_floor_attempt_registry_plan(
        protocol=protocol, cells=cells, schedule=schedule,
        freeze_sha256=_freeze_sha(freeze),
        protocol_sha256=s8b_floor_campaign._canonical_sha256(protocol),
    )
    cell = cells[0]
    first_row = next(
        row for row in schedule
        if row["cell_id"] == cell["cell_id"] and row["round"] == 1
    )
    last_row = next(
        row for row in schedule
        if (
            row["cell_id"] == cell["cell_id"]
            and row["round"] == protocol["n_sessions"]
        )
    )
    slot_ids = set(
        s8b_floor_campaign.s8b_floor_attempt_launcher
        .floor_attempt_registry_plan_slot_ids(plan)
    )
    planned_repetitions = sorted(
        repetition
        for holdout_id, configuration_id, repetition,
        measurement_ordinal, attempt_ordinal in slot_ids
        if (
            holdout_id == cell["holdout_id"]
            and configuration_id == cell["configuration_id"]
            and measurement_ordinal == 0
            and attempt_ordinal == 0
        )
    )

    assert 0 in planned_repetitions
    assert protocol["n_sessions"] not in planned_repetitions
    for row, repetition in (
        (first_row, planned_repetitions[0]),
        (last_row, planned_repetitions[-1]),
    ):
        assert repetition == row["round"] - 1


def test_certified_campaign_rejects_unissued_consumption_marker(
        tmp_path, monkeypatch):
    case = _new_certified_attempt_case(tmp_path)
    admission = s8b_floor_campaign._holdout_admission
    monkeypatch.setattr(
        admission, "validate_floor_attempt_consumption_marker",
        lambda *_args, **_kwargs: admission.FloorAttemptConsumptionMarker(),
    )

    with pytest.raises(
        s8b_floor_campaign.CampaignAbort,
        match="floor attempt consumption marker capability was not issued",
    ):
        _run_certified_attempt_case(case, monkeypatch, competing=False)


def test_journal_emits_launcher_terminal_record_byte_identically(
        tmp_path, monkeypatch):
    case = _new_certified_attempt_case(tmp_path)
    launcher = s8b_floor_campaign.s8b_floor_attempt_launcher
    launched_results = []
    original = launcher.launch_probed_floor_attempt

    def certified(*args, **kwargs):
        result = original(*args, **kwargs)
        launched_results.append(result)
        return result

    monkeypatch.setattr(launcher, "launch_probed_floor_attempt", certified)

    _run_certified_attempt_case(case, monkeypatch, competing=False)

    assert len(launched_results) == 1
    launched = launched_results[0]
    journal_line = case["journal_path"].read_bytes().splitlines(keepends=True)[-1]
    assert journal_line == launched.terminal.raw_output_bytes
    assert launched.terminal.campaign_record is case["runner"].records[-1]


def test_default_production_result_is_v5(tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    monkeypatch.setattr(
        s8b_floor_campaign.s8b_floor_attempt_launcher,
        "_owned_post_probe", _first_clean_then_competing_probe(),
    )
    outcome = _run_campaign(
        protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
        build_root=tmp_path / "bin", measure_fn=None,
        probe_fn=lambda: pytest.fail("legacy probe path was called"),
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
    )

    assert outcome["result"]["schema"] == s8b_floor_contract.RESULT_SCHEMA_V5
    assert set(outcome["result"]) == set(
        s8b_floor_contract.result_keys_for_mode(
            "pilot", schema=s8b_floor_contract.RESULT_SCHEMA_V5,
            perf_preflight=outcome["result"].get("perf_preflight"),
        )
    )
    assert outcome["result"]["attempt_registry"]["row_count"] == 6


def test_production_v5_self_check_rejects_prefix_head_mismatch(
        tmp_path, monkeypatch):
    case = _new_certified_attempt_case(tmp_path)
    _run_certified_attempt_case(case, monkeypatch, competing=False)
    proof = s8b_floor_campaign._capture_floor_attempt_registry_prefix(
        case["authority"], case["plan"],
    )
    artifact = {
        "schema": s8b_floor_contract.RESULT_SCHEMA_V5,
        "attempt_registry": {
            **proof,
            "chain_head_sha256": (
                "1" * 64 if proof["chain_head_sha256"] != "1" * 64 else "2" * 64
            ),
        },
        "eligible_for_refreeze": False,
    }

    with pytest.raises(
        s8b_floor_campaign._holdout_admission.FloorHoldoutEvidenceError,
    ) as captured:
        s8b_floor_campaign._verify_result_with_live_admission(
            artifact, {}, {}, repo_root=case["authority"],
            protocol=case["protocol"], freeze=case["freeze"],
            freeze_sha256=_freeze_sha(case["freeze"]),
            manifest_sha256=case["manifest_sha256"],
            campaign_run_id=case["run_id"], run_relpath=case["run_relpath"],
            mode="pilot", cells=case["cells"], schedule=case["schedule"],
            records=case["runner"].records, expected_use_perf=False,
        )
    assert captured.value.reason == "attempt-registry-prefix-head-mismatch"


def test_v5_prefix_covers_every_consumed_non_competing_session(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    launcher = s8b_floor_campaign.s8b_floor_attempt_launcher
    monkeypatch.setattr(
        launcher, "_owned_post_probe", _first_two_clean_then_competing_probe(),
    )

    outcome = _run_campaign(
        protocol, verified, out_root=out_root,
        build_root=tmp_path / "bin", measure_fn=None,
        probe_fn=lambda: pytest.fail("legacy probe path was called"),
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
    )

    validated = s8b_floor_campaign.validate_protocol(protocol)
    cells = s8b_floor_campaign.enumerate_cells(
        freeze, stock_configuration=validated["stock_configuration"],
    )
    schedule = s8b_floor_campaign.build_schedule(
        cells=cells, master_seed=validated["master_seed"],
        n_sessions=validated["n_sessions"],
    )
    plan = s8b_floor_campaign._build_floor_attempt_registry_plan(
        protocol=validated, cells=cells, schedule=schedule,
        freeze_sha256=_freeze_sha(freeze),
        protocol_sha256=s8b_floor_campaign._canonical_sha256(validated),
    )
    authority = _test_holdout_authority(out_root, protocol, verified)
    rows = launcher.read_floor_attempt_registry(authority, plan)
    live = launcher.capture_floor_attempt_registry_prefix(authority, plan)
    proof = outcome["result"]["attempt_registry"]

    assert sum(row.get("event") == "terminal" for row in rows) == 2
    assert proof["row_count"] == len(rows), "result registry row_count is stale"
    assert proof["row_count"] == live["row_count"]
    assert proof["chain_head_sha256"] == live["chain_head_sha256"]


def test_v5_prefix_assertions_kill_first_terminal_stale_result_proof(
        tmp_path, monkeypatch):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    launcher = s8b_floor_campaign.s8b_floor_attempt_launcher
    issued_plans = []
    stale_prefixes = []
    original_prepare = launcher.prepare_floor_attempt_registry_plan
    original_launch = launcher.launch_probed_floor_attempt

    def prepare(*args, **kwargs):
        plan = original_prepare(*args, **kwargs)
        issued_plans.append(plan)
        return plan

    def launch(*args, **kwargs):
        result = original_launch(*args, **kwargs)
        if not stale_prefixes:
            stale_prefixes.append(
                launcher.capture_floor_attempt_registry_prefix(
                    args[0].repo_root, issued_plans[0],
                )
            )
        return result

    monkeypatch.setattr(launcher, "prepare_floor_attempt_registry_plan", prepare)
    monkeypatch.setattr(launcher, "launch_probed_floor_attempt", launch)
    monkeypatch.setattr(
        launcher, "_owned_post_probe", _first_two_clean_then_competing_probe(),
    )
    monkeypatch.setattr(
        s8b_floor_campaign,
        "_capture_floor_attempt_registry_prefix",
        lambda *_args, **_kwargs: dict(stale_prefixes[0]),
    )

    outcome = _run_campaign(
        protocol, verified, out_root=out_root,
        build_root=tmp_path / "bin", measure_fn=None,
        probe_fn=lambda: pytest.fail("legacy probe path was called"),
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
    )
    authority = _test_holdout_authority(out_root, protocol, verified)
    rows = launcher.read_floor_attempt_registry(authority, issued_plans[0])
    proof = outcome["result"]["attempt_registry"]

    assert proof == stale_prefixes[0]
    assert proof["row_count"] < len(rows)
    with pytest.raises(AssertionError, match="result registry row_count is stale"):
        assert proof["row_count"] == len(rows), "result registry row_count is stale"


def test_competing_pre_probe_consumes_no_marker_and_writes_no_registry_row(
        tmp_path, monkeypatch):
    case = _new_certified_attempt_case(tmp_path)
    record = _run_certified_attempt_case(case, monkeypatch, competing=True)
    inspection = _inspect_certified_attempt_case(case)
    shared = (
        s8b_floor_campaign._holdout_admission
        .shared_admission_root(case["authority"])
    )
    attempt_ledger = shared / "attempt-ledger.jsonl"

    actual_probe = {
        "rc": 0, "stdout": "competitor", "stderr": "", "competing": True,
    }
    journal_record = _read_journal_lines(case["journal_path"])[-1]
    assert record["probe_before"] == actual_probe
    assert journal_record["probe_before"] == actual_probe
    assert not attempt_ledger.exists() or attempt_ledger.read_bytes() == b""
    assert list((shared / "floor-attempt-registries").rglob("registry.jsonl")) == []
    assert inspection["attempt_row_count"] == 0


def test_campaign_has_no_indirect_registry_profile_or_core_attributes():
    source = Path(s8b_floor_campaign.__file__).read_text(encoding="utf-8")
    forbidden = {"attempt_registry", "profile8b", "core"}
    references = sorted(
        (node.attr, node.lineno)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Attribute) and node.attr in forbidden
    )
    assert references == []


def test_injected_measurement_core_retains_noncertifying_legacy_path(
        tmp_path):
    freeze = _freeze_document()
    measure = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(
        _protocol(freeze_sha=_freeze_sha(freeze)), _verified_freeze(freeze),
        out_root=tmp_path / "out", build_root=tmp_path / "bin",
        measure_fn=measure, probe_fn=lambda: (1, "", ""),
    )

    assert measure.calls
    assert outcome["result"]["schema"] == s8b_floor_contract.RESULT_SCHEMA
    assert outcome["result"]["schema"] != s8b_floor_contract.RESULT_SCHEMA_V5
    assert "attempt_registry" not in outcome["result"]


def test_finalize_pending_replays_live_v5_prefix(tmp_path, monkeypatch):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    monkeypatch.setattr(
        s8b_floor_campaign.s8b_floor_attempt_launcher,
        "_owned_post_probe", _first_clean_then_competing_probe(),
    )
    captured_prefixes = []
    original_capture = s8b_floor_campaign._capture_floor_attempt_registry_prefix

    def capture_spy(*args, **kwargs):
        proof = original_capture(*args, **kwargs)
        captured_prefixes.append(proof)
        return proof

    monkeypatch.setattr(
        s8b_floor_campaign, "_capture_floor_attempt_registry_prefix", capture_spy,
    )
    with monkeypatch.context() as scoped:
        scoped.setattr(
            s8b_floor_campaign, "_publish_finalize_files",
            lambda *_args: (_ for _ in ()).throw(
                _SimulatedCrash("production-terminal-after")
            ),
        )
        with pytest.raises(_SimulatedCrash, match="production-terminal-after"):
            _run_campaign(
                protocol, verified, out_root=out_root,
                build_root=tmp_path / "bin", measure_fn=None,
                probe_fn=lambda: pytest.fail("legacy probe path was called"),
                perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
            )
    run_dir = _only_run_dir(out_root)
    outcome = _run_campaign(
        protocol, verified, out_root=out_root,
        build_root=tmp_path / "bin", resume_dir=run_dir, measure_fn=None,
        probe_fn=lambda: pytest.fail("finalize-pending ran a probe"),
        perf_preflight_fn=lambda **_kwargs: _perf_receipt(available=False),
    )

    assert outcome["result"]["schema"] == s8b_floor_contract.RESULT_SCHEMA_V5
    assert len(captured_prefixes) == 2
    assert captured_prefixes[0] == captured_prefixes[1]
    assert outcome["result"]["attempt_registry"] == captured_prefixes[-1]


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", str(Path(__file__).resolve())]))
