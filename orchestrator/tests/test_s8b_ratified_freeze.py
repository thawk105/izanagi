# -*- coding: utf-8 -*-
"""s8b_ratified_freeze の承認束縛 machinery の攻撃 matrix テスト (F6a、RV-core)。

使い捨て tmp git repo に v1→g1 の承認・activation を組み、各攻撃を注入して fail-closed を
確認する。実 repo の output/s8b-freeze/ には一切書かない (発効の禁止)。pytest 専用
(tmp_path fixture 依存、README allowlist 記載)。
"""
from __future__ import annotations

from orchestrator.tests.s8b_v2_freeze_fixture import in_sealed_fixture_process

from orchestrator.tests.s8b_v2_freeze_fixture import sealed_source_protection_fixture

import contextlib
import dataclasses
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections import UserDict
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_ORCH)
sys.path.insert(0, os.path.dirname(_ORCH))
sys.path.insert(0, _HERE)

from orchestrator.calibrator import schema_v2 as CALIBRATION_V2  # noqa: E402
from orchestrator.calibrator import perf_preflight as PERF_PREFLIGHT  # noqa: E402
from orchestrator.campaign import s8b_ratified_freeze as M  # noqa: E402
from orchestrator.campaign import env_contract as EC  # noqa: E402
from orchestrator.campaign import s8b_floor_campaign as FLOOR  # noqa: E402
from orchestrator.campaign import s8b_floor_contract as FC  # noqa: E402
from orchestrator.campaign import s8b_holdout_freeze as HF  # noqa: E402
from orchestrator.campaign import s8b_oracle_manifest as ORACLE_MANIFEST  # noqa: E402
from orchestrator.campaign import s8b_prediction_runner as PR  # noqa: E402
from orchestrator.campaign.durable_root import DurableRootPolicy  # noqa: E402
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.s1_direct_comparison import PreparedCell  # noqa: E402
from orchestrator.campaign.s8b_freeze_io import VerifiedFreeze  # noqa: E402
from s8b_floor_evidence_fixture import (  # noqa: E402
    build_floor_admission_evidence,
    fake_sort_swo_pass_attempt,
)
import s8b_v2_freeze_fixture as V2FIX  # noqa: E402
from test_schema_v2 import _valid_document as _valid_calibration_v2_document  # noqa: E402

_REAL_V1 = Path(_ROOT) / "output" / "s8b-freeze" / "holdout_freeze.json"

_ATTEMPT_REGISTRY_PROOF_KEYS = (
    "schema", "registry_schema", "freeze_sha256", "protocol_sha256",
    "schedule_sha256", "row_count", "chain_head_sha256",
)


def _mutate_attempt_registry_proof(proof: dict, mutation: str) -> None:
    if mutation == "extra-key":
        proof["unexpected"] = True
        return
    operation, field = mutation.split(":", 1)
    if operation == "missing":
        proof.pop(field)
        return
    if operation != "invalid":
        raise AssertionError(f"unknown proof mutation: {mutation}")
    if field == "schema":
        proof[field] = "s8b-attempt-registry-prefix-proof/unknown"
    elif field == "registry_schema":
        proof[field] = "s8b-attempt-registry/v999"
    elif field == "row_count":
        proof[field] += 1
    else:
        value = proof[field]
        proof[field] = ("0" if value[0] != "0" else "1") + value[1:]


def _perf_receipt(*, available: bool) -> dict:
    events = ["LLC-load-misses", "LLC-loads", "instructions", "cycles"]
    return {
        "schema": "izanagi-perf-preflight/v1",
        "status": "available" if available else "unavailable",
        "available": available,
        "probe_argv": [
            "perf", "stat", "-x,", "-o", "<tmp>/perf.csv",
            "-e", ",".join(events), "--", "/bin/true",
        ],
        "rc": 0 if available else None,
        "parsed_events": events if available else [],
        "reason": "available" if available else "perf-not-found",
        "stderr_sha256": hashlib.sha256(b"ratified-fixture").hexdigest(),
        "candidates": [],
    }


# --------------------------------------------------------------------------
# tmp git repo ヘルパ (test_s8b_holdout_freeze.py の _git/_commit_all を踏襲)
# --------------------------------------------------------------------------

def _git(root: Path, *args: str, stdin: bytes | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, input=stdin,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.decode("utf-8").strip()


def _init_repo(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "config", "commit.gpgsign", "false")


def _commit(root: Path, subject: str, ai_agent: str) -> str:
    """全 add + 単一 commit。message は subject 段落 + `AI-Agent: <ai_agent>` trailer。"""
    _git(root, "add", "-A")
    message = f"{subject}\n\nAI-Agent: {ai_agent}".encode("utf-8")
    _git(root, "commit", "-q", "-F", "-", stdin=message)
    return _git(root, "rev-parse", "HEAD")


def _commit_raw(root: Path, message: str) -> str:
    """message を逐語で commit する (trailer 併記・大小文字違いの注入用)。"""
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-F", "-", stdin=message.encode("utf-8"))
    return _git(root, "rev-parse", "HEAD")


def _commit_verbatim(root: Path, message: str) -> str:
    """message を --cleanup=verbatim で commit する (末尾空白等を byte 単位で保存)。

    git の既定 cleanup (strip/whitespace) は各行の末尾空白を落とすため、末尾空白付き
    trailer (`AI-Agent: none `) を注入する R3 攻撃では verbatim が必須。"""
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "--cleanup=verbatim", "-F", "-",
         stdin=message.encode("utf-8"))
    return _git(root, "rev-parse", "HEAD")


def _write(root: Path, rel: str, raw: bytes) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _gen_raw(number: int, supersedes: str) -> bytes:
    """exact v2 schema を満たす世代 bytes (内容は placeholder、本レーンは内容非検査)。"""
    doc = {key: "x" for key in M.V2_TOP_LEVEL_KEYS}
    doc["schema_version"] = "8b-holdout-freeze/v2"
    doc["generation_number"] = number
    doc["supersedes_sha256"] = supersedes
    doc["measurement_closure"] = []
    return json.dumps(doc, ensure_ascii=False).encode("utf-8")


def _approval_raw(gen_sha: str) -> bytes:
    return M._canonical_bytes({
        "generation_sha256": gen_sha, "approver": "user",
        "approved_at": "2026-07-18T00:00:00Z", "scope": "s8b-holdout",
    })


def _pointer_raw(number: int, path: str, gen_sha: str, parent, approval_sha: str) -> bytes:
    return M._canonical_bytes({
        "generation_number": number, "path": path, "sha256": gen_sha,
        "parent_active_sha256": parent, "approval_sha256": approval_sha,
    })


def _gen_rel(number: int) -> str:
    return f"output/s8b-freeze/holdout_freeze.v2.g{number}.json"


def _base_repo(tmp_path: Path) -> Path:
    """v1 holdout_freeze.json を載せた base commit までを組む。"""
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    if _REAL_V1.is_file():
        _write(root, M.V1_FREEZE_PATH, _REAL_V1.read_bytes())
    _commit(root, "base", "claude-base")
    return root


def _add_generation(root: Path, number: int, supersedes: str):
    """世代 file を導入 commit G (AI trailer) で載せ、(gen_sha, gen_rel) を返す。"""
    rel = _gen_rel(number)
    raw = _gen_raw(number, supersedes)
    _write(root, rel, raw)
    _commit(root, f"candidate g{number}", "claude-opus")
    return _sha(raw), rel


def _approve_and_point(root: Path, number: int, gen_sha: str, gen_rel: str,
                       parent_ptr_sha, *, ai_agent: str = "none"):
    """approval A → active pointer X の 2 commit で載せ、hash の対を返す。"""
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    approval_rel = f"{M.APPROVAL_DIR}/{gen_sha}.json"
    _write(root, approval_rel, approval_raw)
    _commit(root, f"approve g{number}", ai_agent)

    ptr_raw = _pointer_raw(number, gen_rel, gen_sha, parent_ptr_sha, approval_sha)
    ptr_sha = _sha(ptr_raw)
    ptr_rel = f"{M.ACTIVE_DIR}/{ptr_sha}.json"
    _write(root, ptr_rel, ptr_raw)
    _commit(root, f"point g{number}", ai_agent)
    return approval_sha, ptr_sha


def _valid_g1(tmp_path: Path):
    """v1→g1 の正常な承認・activation を組み、root と主要 hash を返す (structural placeholder)。

    世代 document は placeholder (内容非検査) なので resolve_active_generation (structural)
    は通るが load_ratified_freeze (semantics 充填済み) は通らない。意味論の happy path は
    build_valid_semantic_g1 を使う。"""
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_sha, ptr_sha = _approve_and_point(root, 1, gen_sha, gen_rel, None)
    return root, gen_sha, gen_rel, approval_sha, ptr_sha


# --------------------------------------------------------------------------
# 意味論 (V1〜V3) を満たす valid g1 fixture — RV-verify の happy path 共用。
# --------------------------------------------------------------------------

_RR80_PARAMS = b"ycsb_rr" + b"atio=80 ycsb_zipf_skew=0.9 ycsb_rmw=0\n"
_RR20_PARAMS = b"ycsb_rr" + b"atio=20 ycsb_zipf_skew=0.9 ycsb_rmw=0\n"
_RR50_PARAMS = b"ycsb_rratio=50 ycsb_zipf_skew=0.9 ycsb_rmw=0\n"  # 陽性対照
_FLOOR_PROTOCOL_STUB = b'{"floor_protocol": "stub", "n": 1}\n'    # strict parse 可能・holdout params 無し
_FLOOR_SOURCE_STUB_DOCUMENT = {
    "floors": {
        holdout_id: {
            "pairs": {}, "scale_ref": None, "scalar_alt": None,
            "diagnostics": {},
        }
        for holdout_id in ("rr20", "rr80")
    },
}
_FLOOR_SOURCE_STUB = json.dumps(
    _FLOOR_SOURCE_STUB_DOCUMENT, ensure_ascii=False, sort_keys=True,
    separators=(",", ":"), allow_nan=False,
).encode("utf-8")


def _independent_floor_projection(result: dict) -> dict:
    """production projector を使わず result.floors の期待投影を組み立てる。"""
    return {
        "by_holdout": {
            holdout_id: {
                "pairs": json.loads(json.dumps(value["pairs"])),
                "scale_ref": json.loads(json.dumps(value["scale_ref"])),
                "scalar_alt": json.loads(json.dumps(value["scalar_alt"])),
            }
            for holdout_id, value in result["floors"].items()
        },
    }


# --------------------------------------------------------------------------
# E3a: 決定的観測下の production-emitter bytes staged builder
# --------------------------------------------------------------------------

_FIXED_NOW = dt.datetime(2026, 7, 18, 12, 0, tzinfo=dt.timezone.utc)
_FIXED_GIT_ENV = {
    "GIT_AUTHOR_NAME": "s8b fixture",
    "GIT_AUTHOR_EMAIL": "s8b-fixture@example.invalid",
    "GIT_COMMITTER_NAME": "s8b fixture",
    "GIT_COMMITTER_EMAIL": "s8b-fixture@example.invalid",
    "GIT_AUTHOR_DATE": "2026-07-18T12:00:00+0000",
    "GIT_COMMITTER_DATE": "2026-07-18T12:00:00+0000",
    "TZ": "UTC",
}


def _fixed_git(root: Path, *args: str, stdin: bytes | None = None) -> str:
    env = dict(os.environ)
    env.update(_FIXED_GIT_ENV)
    return subprocess.run(
        ["git", "-c", "core.autocrlf=false", *args], cwd=root, check=True,
        input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
    ).stdout.decode("utf-8").strip()


def _init_fixed_repo(root: Path) -> None:
    root.mkdir(parents=True)
    _fixed_git(root, "init", "-q", "--object-format=sha1")
    _fixed_git(root, "config", "user.name", _FIXED_GIT_ENV["GIT_AUTHOR_NAME"])
    _fixed_git(root, "config", "user.email", _FIXED_GIT_ENV["GIT_AUTHOR_EMAIL"])
    _fixed_git(root, "config", "commit.gpgsign", "false")
    _fixed_git(root, "config", "core.autocrlf", "false")
    object_format = _fixed_git(root, "rev-parse", "--show-object-format")
    assert object_format == "sha1"


def _fixed_commit_all(root: Path, subject: str, agent: str) -> str:
    _fixed_git(root, "add", "-A")
    message = f"{subject}\n\nAI-Agent: {agent}".encode("utf-8")
    _fixed_git(root, "commit", "-q", "-F", "-", stdin=message)
    return _fixed_git(root, "rev-parse", "HEAD")


def _commit_exact(root: Path, paths, *, subject: str, agent: str) -> str:
    """指定 path だけを commit し、diff-tree の exact path-set を直後に検査する。"""
    expected = tuple(sorted(set(paths)))
    _fixed_git(root, "add", "-A", "--", *paths)
    staged = tuple(filter(None, _fixed_git(
        root, "diff", "--cached", "--no-renames", "--name-only",
        "--diff-filter=ACDMRTUXB",
    ).splitlines()))
    assert staged == expected, {
        "missing": sorted(set(expected) - set(staged)),
        "extra": sorted(set(staged) - set(expected)),
    }
    commit = _fixed_commit_all_staged(root, subject, agent)
    actual = tuple(filter(None, _fixed_git(
        root, "diff-tree", "--no-commit-id", "--no-renames", "--name-only", "-r", commit,
    ).splitlines()))
    assert actual == expected, (actual, expected)
    return commit


def _fixed_commit_all_staged(root: Path, subject: str, agent: str) -> str:
    message = f"{subject}\n\nAI-Agent: {agent}".encode("utf-8")
    _fixed_git(root, "commit", "-q", "-F", "-", stdin=message)
    return _fixed_git(root, "rev-parse", "HEAD")


def _fixed_mode_map(root: Path, commit: str, paths) -> dict[str, str]:
    modes = {}
    for rel in paths:
        row = _fixed_git(root, "ls-tree", commit, "--", rel)
        assert row, (commit, rel)
        modes[rel] = row.split(" ", 1)[0]
    return modes


def _assert_no_root_bytes(raws, needles) -> None:
    for raw in raws:
        assert all(needle not in raw for needle in needles)


def _make_fixed_ccbench(root: Path) -> str:
    sub = root / "external" / "ccbench"
    _init_fixed_repo(sub)
    (sub / ".gitattributes").write_text("* -text\n", encoding="utf-8")
    (sub / "fixture.txt").write_text("deterministic ccbench fixture\n", encoding="utf-8")
    commit = _fixed_commit_all(sub, "ccbench fixture", "fixture")
    assert _fixed_git(sub, "rev-parse", "--show-object-format") == "sha1"
    return commit


def _emitter_protocol(*, ccbench_pin: str, master_seed: str = "fixture-seed") -> dict:
    contract = EC.lookup("linux-baremetal")
    return FLOOR.validate_protocol({
        "schema": FC.PROTOCOL_SCHEMA,
        "formula": FC.FORMULA_ID,
        "env_tag": contract.env_tag,
        "contract_sha256": contract.contract_sha256,
        "ccbench_pin": ccbench_pin,
        "freeze": {"path": M.V1_FREEZE_PATH, "sha256": M.V1_FREEZE_SHA256},
        "stock_configuration": "stock_common",
        "n_sessions": 8,
        "reps": 5,
        "master_seed": master_seed,
        "schedule_algorithm": FC.SCHEDULE_ALGORITHM,
        "extime_s": 5,
        "wired_min_rel_floor": 0.9,
        "retry_slots_per_cell": 2,
        "session_cv_max": "0.10",
        "cell_cv_max": "0.15",
        "scale_adequacy_rel_tolerance": "0.10",
        "allowed_excluded_reasons": list(FC._APPROVED_REASONS),
    })


def _fixed_host(*, now_fn):
    return {
        "hostname": "fixture-host", "boot_id": "fixture-boot",
        "job_id": None, "cpuset": "/fixture", "utc": now_fn().isoformat(),
    }


def _fixed_process():
    return {"pid": 4242, "starttime": 31337, "execution_uuid": "a" * 32}


def _fixed_receipt(contract, *, now_fn):
    return {
        "schema": FLOOR.execution_guard.RECEIPT_SCHEMA,
        "env_tag": contract.env_tag,
        "contract_sha256": contract.contract_sha256,
        "attestation": {
            "hostname": "fixture-receipt-host", "boot_id": "fixture-receipt-boot",
            "cpuset": "/fixture", "captured_utc": now_fn().isoformat(),
        },
    }


def _verified_calibration_v2_fixture():
    """acquisition receipt 付きの synthetic v2 calibration を返す。"""
    document = _valid_calibration_v2_document()
    document["env_tag"] = "linux-baremetal"
    document["attestation_profile"]["effective_clock"]["tolerance_pct"] = 2.0
    document["acquisition_receipt"]["toolchain"].update({
        "compiler_path": "/fixture/toolchain/cc",
        "compiler_version": "fixture-cc 13.0\nfixture detail",
        "cmake_version": "fixture-cmake version 3.28\nfixture detail",
    })
    document["acquisition_receipt"]["ccbench"]["build_argv"] = [
        "cmake",
        "-DCMAKE_C_COMPILER=/fixture/toolchain/cc",
        "-DCMAKE_CXX_COMPILER=/fixture/toolchain/cxx",
    ]
    calibration = CALIBRATION_V2.validate_calibration_v2(document)
    raw = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return FLOOR.env_attestation.VerifiedCalibration(
        schema_version=CALIBRATION_V2.SCHEMA_VERSION,
        sha256=_sha(raw),
        calibration=calibration,
        attestation_profile_sha256=FLOOR.env_attestation.profile_sha256(
            calibration.attestation_profile,
        ),
    )


def _fixture_toolchain_manifest(*, cc: str, cxx: str) -> dict[str, dict[str, str]]:
    return {
        "cc": {
            "requested": cc,
            "realpath": "/fixture/toolchain/cc",
            "version_first_line": "live-cc 13.0",
            "version": "live-cc 13.0\nfixture detail",
        },
        "cxx": {
            "requested": cxx,
            "realpath": "/fixture/toolchain/cxx",
            "version_first_line": "live-cxx 13.0",
            "version": "live-cxx 13.0\nfixture detail",
        },
        "cmake": {
            "requested": "cmake",
            "realpath": "/fixture/toolchain/cmake",
            "version_first_line": "live-cmake version 3.28",
            "version": "live-cmake version 3.28\nfixture detail",
        },
    }


def _fixture_observe_floor_tool(requested: str, role: str):
    assert requested == {
        "cc": "fixture-cc", "cxx": "fixture-cxx", "cmake": "cmake",
    }[role]
    entry = _fixture_toolchain_manifest(
        cc="fixture-cc", cxx="fixture-cxx",
    )[role]
    return FLOOR._ObservedFloorTool(
        requested=entry["requested"], realpath=entry["realpath"],
        version_first_line=entry["version_first_line"], version=entry["version"],
    )


@contextlib.contextmanager
def _fixed_prepare(cell, ccbench_pin, *, cxx):
    assert cxx == "fixture-cxx"
    entry = cell["variant"]
    configuration = cell["configuration"]
    flags = dict(entry.get("flags", {}))
    genome = Genome("silo", flags)
    token = hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest()
    yield PreparedCell(
        genome=genome, src_token=token,
        ccbench_dir=_fixed_prepare.ccbench_dir,
        cache_root=_fixed_prepare.cache_root,
        oracle_attempt=(
            fake_sort_swo_pass_attempt()
            if configuration == "sort_best" else None
        ),
    )


def _make_emitter_build(*, compiler_input_rel="fixture.txt"):
    def build(genome, ccbench_commit, trace, cache_root="", cc=None, cxx=None,
              jobs=16, ccbench_dir="", src_token=None, contract=None,
              timeout_s=None, admission=None, build_context=None,
              source_evidence=None, expected_toolchain_manifest=None):
        assert admission is not None
        assert build_context is not None
        assert source_evidence is not None
        assert expected_toolchain_manifest == _fixture_toolchain_manifest(
            cc=cc, cxx=cxx,
        )
        assert trace is False
        assert ccbench_dir == _fixed_prepare.ccbench_dir
        assert timeout_s == 900
        cell_dir = Path(cache_root) / "fixture" / hashlib.sha256(
            src_token.encode("utf-8")).hexdigest()[:16]
        cell_dir.mkdir(parents=True, exist_ok=True)
        binary = cell_dir / "ycsb_fixture.exe"
        payload = f"fixture-binary::{genome.canonical()}::{src_token}".encode("utf-8")
        binary.write_bytes(payload)
        sha = _sha(payload)
        source_root = ccbench_dir or _fixed_prepare.ccbench_dir
        compiler_input = Path(source_root) / compiler_input_rel
        compiler_input_manifest = {
            "schema_version": "s8b-compiler-input/v1",
            "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
            "target": f"ycsb_{genome.protocol}.exe",
            "depfile_count": 1,
            "inputs": [{
                "path": compiler_input_rel,
                "sha256": _sha(compiler_input.read_bytes()),
            }],
        }
        compiler_input_manifest_sha256 = _sha(json.dumps(
            compiler_input_manifest, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"))
        source_protection = sealed_source_protection_fixture(
            source=source_evidence, binary_sha256=sha,
            compiler_input_manifest_sha256=compiler_input_manifest_sha256,
        )
        expected_materialization_sha256 = (
            source_protection.expected_materialization_sha256
        )
        return SimpleNamespace(
            source_protection=source_protection,
            genome=genome, trace=False, binary=str(binary), bin_sha256=sha,
            bin_hash=sha[:16], build_dir=str(cell_dir), cached=False,
            configure_argv=["cmake", "-S", str(source_root), "-B", str(cell_dir)],
            build_argv=["cmake", "--build", str(cell_dir)],
            cache_root=str(cache_root), ccbench_root=str(source_root),
            contract_sha256=contract.contract_sha256,
            compiler_input_manifest=compiler_input_manifest,
            compiler_input_manifest_sha256=compiler_input_manifest_sha256,
            source_snapshot_sha256=expected_materialization_sha256,
            expected_materialization_sha256=expected_materialization_sha256,
        )
    return build


class _EmitterScalePoint:
    def __init__(self, run_cmd: str, *, use_perf: bool = True):
        self.throughputs = [1000.0] * 5
        self.notes = []
        self.run_cmd = run_cmd
        self.rep_observations = [
            {
                "rep_index": index, "returncode": 0,
                "execution_failure": False,
                "counter_status": "complete" if use_perf else "not_required",
                "missing_perf_events": [],
                "perf_raw": {
                    "LLC-load-misses": 1 if use_perf else None,
                    "LLC-loads": 2 if use_perf else None,
                    "instructions": 3 if use_perf else None,
                    "cycles": 4 if use_perf else None,
                },
                "throughput": 1000.0,
            }
            for index in range(5)
        ]


def _emitter_measure_for_perf(binary, records, threads, workload, *, use_perf: bool):
    contract = EC.lookup("linux-baremetal")
    argv = list(FC.build_portable_run_cmd(
        binary="output/portable/bench", workload=workload, records=records,
        threads=threads, extime_s=5, clocks_per_us=contract.clocks_per_us,
        numactl=contract.numactl,
        use_perf=use_perf,
    ))
    binary_index = argv.index("--") + 1 if use_perf else len(contract.numactl)
    argv[binary_index] = str(binary)
    return _EmitterScalePoint(shlex.join(argv), use_perf=use_perf)


def _emitter_measure(binary, records, threads, workload):
    return _emitter_measure_for_perf(
        binary, records, threads, workload, use_perf=True,
    )


def _emitter_measure_degraded(binary, records, threads, workload):
    return _emitter_measure_for_perf(
        binary, records, threads, workload, use_perf=False,
    )


def _json_bytes(document) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


_JSON_STRING_TOKEN = re.compile(rb'"(?:\\.|[^"\\])*"')


def _json_bytes_with_escaped_strings(document) -> bytes:
    """同じ JSON content の全 string token を Unicode escape で表す scan-neutral bytes。"""
    raw = _json_bytes(document)

    def escape_token(match: re.Match[bytes]) -> bytes:
        value = json.loads(match.group().decode("utf-8"))
        units = []
        for char in value:
            codepoint = ord(char)
            if codepoint <= 0xFFFF:
                units.append(f"\\u{codepoint:04x}")
            else:
                codepoint -= 0x10000
                units.append(f"\\u{0xD800 + (codepoint >> 10):04x}")
                units.append(f"\\u{0xDC00 + (codepoint & 0x3FF):04x}")
        return ('"' + "".join(units) + '"').encode("ascii")

    escaped = _JSON_STRING_TOKEN.sub(escape_token, raw)
    assert json.loads(escaped) == document
    return escaped


def _jsonl_bytes(records) -> bytes:
    return b"".join((json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ) + "\n").encode() for record in records)


def _prepare_emitter_base(
        root: Path, *, selector_valid_cell: bool = False,
        selector_extra_files=(), selector_payload_hit: bool = False,
        master_seed: str = "fixture-seed",
) -> tuple[dict, str, str, bytes, bytes]:
    _init_fixed_repo(root)
    ccbench_pin = _make_fixed_ccbench(root)
    v1_raw = _REAL_V1.read_bytes()
    v1 = json.loads(v1_raw)
    _write(root, M.V1_FREEZE_PATH, v1_raw)
    calibration_path = EC.lookup("linux-baremetal").calibration_ref.path
    _write(root, calibration_path, _real_bytes(calibration_path))
    known_path = v1["known_axes_freeze"]["path"]
    _write(root, known_path, _real_bytes(known_path))
    design_path = v1["design_source"]["path"]
    generator_path = v1["generator"]["path"]
    design_raw = b"# deterministic design source fixture\n"
    generator_raw = b"# deterministic generator fixture\n"
    _write(root, design_path, design_raw)
    _write(root, generator_path, generator_raw)
    _write(root, "positive_control.txt", _RR50_PARAMS)
    _write(root, ".gitattributes", b"* -text\n")
    _write(root, "README.md", b"production-emitter fixture\n")
    for relative in _PREDICTION_SOURCE_PATHS.values():
        destination = root / relative
        if destination.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((Path(_ROOT) / relative).read_bytes())
    parser_destination = root / _PREDICTION_PARSER_PATH
    parser_destination.parent.mkdir(parents=True, exist_ok=True)
    parser_destination.write_bytes((Path(_ROOT) / _PREDICTION_PARSER_PATH).read_bytes())
    protocol_raw = FLOOR._canonical_bytes(
        _emitter_protocol(ccbench_pin=ccbench_pin, master_seed=master_seed)
    )
    _write(root, FLOOR._FLOOR_PROTOCOL_REL, protocol_raw)
    protocol_hits = HF.holdout_conjunction_hits({
        FLOOR._FLOOR_PROTOCOL_REL: protocol_raw.decode("utf-8"),
    })
    assert all(not paths for paths in protocol_hits.values()), protocol_hits
    # official preflight の prediction 必須化 (protocol → prediction → floor の機構強制)
    # を満たす封印一式を base commit に含める。pre_oracle_head の commit pin は実在
    # commit を要求するため、seed commit を先に切って参照する (namespace clean 検査は
    # untracked の selector 証拠を dirty とみなすので、base の外に置けない)。
    seed = _fixed_commit_all(root, "emitter fixture seed", "fixture")
    _install_emitter_selector_prediction(
        root, pre_oracle_head=seed, production_valid=selector_valid_cell,
        selector_payload_hit=selector_payload_hit,
    )
    base = _fixed_commit_all(root, "emitter fixture base", "fixture")
    assert _fixed_git(root, "status", "--porcelain") == ""
    return v1, ccbench_pin, base, design_raw, generator_raw


_PREDICTION_SOURCE_PATHS = {
    "holdout_freeze": "output/s8b-freeze/holdout_freeze.json",
    "builder": "orchestrator/campaign/s8b_selector_input.py",
    "role": ".claude/agents/selector-8b.md",
    "input_schema": "orchestrator/campaign/s8b_selector_catalog.json",
    "output_schema": "orchestrator/campaign/s8b_selector_output_schema.json",
}
_PREDICTION_PARSER_PATH = "orchestrator/campaign/s8b_selector_output.py"


def _install_emitter_selector_prediction(
        root: Path, *, pre_oracle_head: str, production_valid: bool = False,
        selector_payload_hit: bool = False,
) -> None:
    """official preflight の prediction 必須化を満たす hermetic 封印一式を注入する。

    all-missing の 6 行文書 (agent 4 行 = missing・provenance null、off 2 行 = static c06)
    と journal (run_header + 4 claim + 2 static_terminal) を実 API で組む。この封印一式は
    production seal 由来ではないが、合成 protocol の canonical bytes を seed tree に置き、
    protocol commit→seal と同じ topology を模倣する。official preflight の受理集合検査専用であり、
    production protocol の実 pin は oracle 結線 wave の E2E が別途担う。
    注入済み root では no-op (g2 追記 builder と両立)。
    """
    predictions_path = root / "output/s8b-freeze/selector_predictions.json"
    if predictions_path.exists():
        return
    from orchestrator.campaign import s8b_selector_freeze as SF

    for relative in _PREDICTION_SOURCE_PATHS.values():
        destination = root / relative
        if destination.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((Path(_ROOT) / relative).read_bytes())
    freeze = json.loads(
        (root / _PREDICTION_SOURCE_PATHS["holdout_freeze"]).read_bytes()
    )
    sources = {
        name: {
            "path": rel,
            "sha256": hashlib.sha256((root / rel).read_bytes()).hexdigest(),
        }
        for name, rel in _PREDICTION_SOURCE_PATHS.items()
    }
    journal_path = root / "output/s8b-freeze/selector-runs/journal.jsonl"
    journal = PR.PredictionJournal(journal_path)
    jobs = SF.build_prediction_jobs(freeze)
    binding = PR.JournalBinding(
        pre_oracle_head=pre_oracle_head,
        protocol_sha256=hashlib.sha256(
            (root / FLOOR._FLOOR_PROTOCOL_REL).read_bytes()
        ).hexdigest(),
        freeze_sha256=hashlib.sha256(
            (root / _PREDICTION_SOURCE_PATHS["holdout_freeze"]).read_bytes()
        ).hexdigest(),
        provider_kind=(
            PR.PROVIDER_KIND_CLAUDE_HEADLESS if production_valid else "emitter-fixture"
        ),
        role_file_sha256=sources["role"]["sha256"],
        parser_module_sha256=hashlib.sha256(
            (root / _PREDICTION_PARSER_PATH).read_bytes()
        ).hexdigest(),
        claude_executable_path="/fixture/claude",
        claude_executable_sha256=hashlib.sha256(b"emitter fixture claude").hexdigest(),
        known_cells=frozenset(
            (job["target_holdout"], job["arm"]) for job in jobs
        ),
    )
    PR.ensure_run_header(
        journal, binding=binding, created_at="2026-07-22T00:00:00+00:00",
    )
    if production_valid:
        class FakeEnvelopeRunner:
            def __init__(self):
                self.calls = 0

            def __call__(self, argv, **kwargs):
                self.calls += 1
                rationale = (
                    _RR80_PARAMS.decode("utf-8").strip()
                    if self.calls == 1 else "descriptor と機構を比較した"
                )
                raw_result = json.dumps({
                    "schema_version": "8b-selector-output/v1",
                    "choice_id": "c01",
                    "rationale": rationale,
                }, ensure_ascii=False, separators=(",", ":"))
                envelope = {
                    "type": "result", "subtype": "success", "is_error": False,
                    "num_turns": 1, "permission_denials": [], "result": raw_result,
                    "session_id": f"emitter-session-{self.calls}",
                    "modelUsage": {
                        "claude-opus-fixture": {"inputTokens": 10, "outputTokens": 5},
                    },
                    "usage": {"server_tool_use": {"web_search_requests": 0}},
                    "duration_ms": 1, "duration_api_ms": 1, "total_cost_usd": 0,
                    "stop_reason": "end_turn", "uuid": f"fixture-{self.calls}",
                    "errors": [], "structured_output": None, "input_tokens": 10,
                    "output_tokens": 5, "cache_read_input_tokens": 0,
                    "future_cli_field": {"unknown": "allowed"},
                }
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps(
                        envelope, ensure_ascii=False, separators=(",", ":"),
                    ).encode("utf-8"),
                    stderr=b"",
                )

        provider = PR.ClaudeHeadlessProvider(
            artifact_root=journal_path.parent,
            role_file=root / _PREDICTION_SOURCE_PATHS["role"],
            role_bytes=(root / _PREDICTION_SOURCE_PATHS["role"]).read_bytes(),
            repository_root=root, executable=sys.executable,
            runner=FakeEnvelopeRunner(), environ={"HOME": "/fixture/home"},
        )
        binding = dataclasses.replace(
            binding,
            role_file_sha256=provider.role_file_sha256,
            claude_executable_path=provider.executable,
            claude_executable_sha256=provider.executable_sha256,
        )
        # header は provider の実測値で作る必要があるため、初期 header を作り直す。
        journal_path.unlink()
        journal = PR.PredictionJournal(journal_path)
        PR.ensure_run_header(
            journal, binding=binding, created_at="2026-07-22T00:00:00+00:00",
        )
        PR.drive_journal(
            freeze=freeze, journal=journal, artifact_root=journal_path.parent,
            root=root, binding=binding, provider=provider,
        )
        document = PR.materialize_predictions(
            freeze=freeze, journal=journal, predictions_path=predictions_path,
            generated_at="2026-07-22T00:10:00+00:00",
            pre_oracle_head=pre_oracle_head, sources=sources,
            execution_policy={
                "attempts_per_agent_cell": 1, "retry": False,
                "reuse_equal_payload_output": False, "fresh_context": True,
                "declared_tools": [],
            }, binding=binding,
        )
        (journal_path.parent / ".lock").unlink()
        if selector_payload_hit:
            payload_rel = "output/s8b-freeze/selector-runs/payload_rr20_on.json"
            payload_sha = hashlib.sha256(_RR80_PARAMS).hexdigest()
            (root / payload_rel).write_bytes(_RR80_PARAMS)
            records = journal.read_records()
            claim = next(record for record in records if (
                record["record_type"] == "claim"
                and record["target_holdout"] == "rr20"
                and record["arm"] == "on"
            ))
            claim["input_payload_sha256"] = payload_sha
            journal_path.write_bytes(_jsonl_bytes(records))
            row = next(row for row in document["rows"] if (
                row["target_holdout"] == "rr20" and row["arm"] == "on"
            ))
            row["input_payload_sha256"] = payload_sha
            document["body_sha256"] = SF._canonical_sha256({
                key: value for key, value in document.items() if key != "body_sha256"
            })
            predictions_path.write_bytes(_json_bytes(document))
            journal = PR.PredictionJournal(journal_path)
        PR._assert_selector_run_declarations(
            root=root, journal=journal, binding=binding,
        )
        assert len(document["rows"]) == 6
        return

    rows = []
    for job in jobs:
        if job["arm"] == "off":
            rows.append({
                **job, "status": "valid", "rationale": None,
                "raw_response_path": None, "raw_sha256": None,
                "parser_error_code": None, "agent_provenance": None,
            })
            journal.append({
                "record_type": "static_terminal",
                "target_holdout": job["target_holdout"],
                "arm": job["arm"],
                "decision_method": job["decision_method"],
                "choice_id": job["choice_id"],
            })
            continue
        rows.append({
            **job, "status": "missing", "choice_id": None, "rationale": None,
            "raw_response_path": None, "raw_sha256": None,
            "parser_error_code": None, "agent_provenance": None,
        })
        payload_path = (
            "output/s8b-freeze/selector-runs/"
            f"payload_{job['target_holdout']}_{job['arm']}.json"
        )
        payload_raw = PR._canonical_json_bytes(PR._payload_for_job(freeze, job))
        assert hashlib.sha256(payload_raw).hexdigest() == job["input_payload_sha256"]
        _write(root, payload_path, payload_raw)
        journal.append({
            "record_type": "claim",
            "target_holdout": job["target_holdout"],
            "arm": job["arm"],
            "decision_method": job["decision_method"],
            "input_payload_sha256": job["input_payload_sha256"],
            "payload_path": payload_path,
            "claimed_at": "2026-07-22T00:01:00+00:00",
        })
    document = SF.build_prediction_freeze(
        freeze=freeze, rows=rows, generated_at="2026-07-22T00:00:00+00:00",
        pre_oracle_head=pre_oracle_head, sources=sources,
        execution_policy={
            "attempts_per_agent_cell": 1, "retry": False,
            "reuse_equal_payload_output": False, "fresh_context": True,
            "declared_tools": [],
        },
    )
    SF.write_prediction_freeze(predictions_path, document)
    records = journal.read_records()
    assert sum(record["record_type"] == "run_header" for record in records) == 1
    assert sum(record["record_type"] == "claim" for record in records) == 4
    assert sum(record["record_type"] == "static_terminal" for record in records) == 2
    statuses = PR.resolve_journal(records, binding=binding)
    assert sum(status.kind == "claimed_missing" for status in statuses.values()) == 4
    assert sum(status.kind == "static" for status in statuses.values()) == 2


def _emitter_artifact_paths(run_dir: Path, root: Path) -> dict[str, str]:
    rel_dir = run_dir.relative_to(root).as_posix()
    return {
        "protocol": f"{rel_dir}/protocol.json",
        "cert": f"{rel_dir}/launch_certificate.json",
        "journal": f"{rel_dir}/journal.jsonl",
        "manifest": f"{rel_dir}/manifest.json",
        "result": f"{rel_dir}/result.json",
        "result_md": f"{rel_dir}/result.md",
        "closure80": f"{rel_dir}/closure80.txt",
        "closure20": f"{rel_dir}/closure20.txt",
    }


def _run_official_fixture_campaign(
        protocol, verified, *, build_fn, verified_calibration,
        perf_receipt=None, **kwargs) -> dict:
    """official-shaped bytes を作る pytest 専用入口。

    materializer は production core の引数 seam へ渡さず、既定 gateway の局所パッチとして
    fixture 内に閉じる。これにより production の ``official + build_fn`` 拒否集合へ fixture
    専用の例外を追加しない。
    """
    def fixture_evidence(genome, ccbench_commit, *, ccbench_dir="", **_ignored):
        source_root = str(Path(ccbench_dir).resolve())
        source_sha = hashlib.sha256(
            f"{ccbench_commit}\0{genome.canonical()}".encode("utf-8")
        ).hexdigest()
        return FLOOR.source_digest.SourceEvidence(
            schema_version=FLOOR.source_digest.SOURCE_EVIDENCE_SCHEMA,
            source_root=source_root,
            ccbench_commit=ccbench_commit,
            genome_sha256=hashlib.sha256(
                genome.canonical().encode("utf-8")
            ).hexdigest(),
            src_token=hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest(),
            source_bytes_sha256=source_sha,
            tracked_clean=True,
            tracked_diff_sha256=FLOOR.source_digest.EMPTY_TRACKED_DIFF_SHA256,
            tracked_paths=(),
        )

    expected_repo_root = Path(kwargs["repo_root"])

    def fixture_calibration_loader(contract, repo_root):
        assert contract == EC.lookup("linux-baremetal")
        assert Path(repo_root) == expected_repo_root
        assert isinstance(
            verified_calibration, FLOOR.env_attestation.VerifiedCalibration,
        )
        assert verified_calibration.calibration is not None
        assert verified_calibration.calibration.acquisition_receipt is not None
        return verified_calibration

    with mock.patch.object(FLOOR.buildcache, "build_v2", build_fn), \
            mock.patch.object(
                FLOOR.buildcache, "compilers_for_current_site",
                return_value=("fixture-cc", "fixture-cxx"),
            ), \
            mock.patch.object(
                FLOOR.env_attestation, "load_verified_calibration",
                side_effect=fixture_calibration_loader,
            ), \
            mock.patch.object(
                FLOOR, "_observe_floor_tool", side_effect=_fixture_observe_floor_tool,
            ), \
            mock.patch.object(
                FLOOR.source_digest, "resolve_evidence", fixture_evidence,
            ), \
            mock.patch.object(
                FLOOR._perf_preflight, "probe_perf_availability",
                return_value=(_perf_receipt(available=True)
                              if perf_receipt is None else perf_receipt),
            ):
        return FLOOR._run_campaign_core(
            protocol, verified, mode="official",
            confirm_official_floor_run=True, **kwargs,
        )


def build_production_emitter_g1(
        tmp_path: Path, *, mutate=None, mutate_g1=None, extra_closure=None,
        journal_manifest_before_g=False, executable_role=None,
        cert_at_generation=False, generation_strings_escaped=False, now=_FIXED_NOW,
        selector_valid_cell=False, selector_extra_files=(),
        selector_payload_hit=False, perf_available=True,
        result_schema=FC.LEGACY_RESULT_SCHEMA, mutate_attempt_registry=None,
        receipt_root: Path | None = None, compiler_input_rel="fixture.txt"):
    """決定的観測下の production-emitter bytes で base→C→G→A→X を構築する。

    build/measure/provenance は固定 seam であり、実 build・実測の代表 bytes ではない。
    public/core の official materializer 拒否は変更せず、pytest 専用入口だけを使う。
    emitter on-disk bytes と再直列化 bytes の byte-identity を検証するのは cert のみ。
    manifest/journal/result は parse 後の content 級 fixture として扱う。
    """
    if result_schema not in {
        FC.LEGACY_RESULT_SCHEMA, FC.RESULT_SCHEMA_V5,
    }:
        raise ValueError(f"unknown result_schema: {result_schema}")
    if mutate_attempt_registry is not None and result_schema != FC.RESULT_SCHEMA_V5:
        raise ValueError("attempt registry mutation requires result v5")
    root = tmp_path / "repo" if receipt_root is None else Path(receipt_root)
    if receipt_root is None:
        v1, ccbench_pin, base, design_raw, generator_raw = _prepare_emitter_base(
            root, selector_valid_cell=selector_valid_cell,
            selector_extra_files=selector_extra_files,
            selector_payload_hit=selector_payload_hit,
        )
    else:
        # T-080 R already exists. Preserve its basis, source closure and ccbench pin.
        # All acceptance inputs must come from this shared-base copy, never the
        # live parent repo. Check before installing selector evidence so its
        # ordinary-fixture fallback cannot run on the receipt connection path.
        calibration_path = EC.lookup("linux-baremetal").calibration_ref.path
        for relative in (calibration_path, *_PREDICTION_SOURCE_PATHS.values(),
                         _PREDICTION_PARSER_PATH):
            assert (root / relative).is_file(), f"receipt base missing input: {relative}"
        assert not (root / _gen_rel(1)).exists()
        assert not (root / "output/s8b-freeze/selector_predictions.json").exists()
        v1 = json.loads((root / M.V1_FREEZE_PATH).read_bytes())
        ccbench_pin = _fixed_git(root / "external/ccbench", "rev-parse", "HEAD")
        compiler_input_entry = _fixed_git(
            root / "external/ccbench", "ls-tree", ccbench_pin, "--", compiler_input_rel,
        )
        assert compiler_input_entry.split("\t")[-1] == compiler_input_rel
        assert compiler_input_entry.split()[0] in {"100644", "100755"}
        assert compiler_input_entry.split()[1] == "blob"
        design_raw = (root / v1["design_source"]["path"]).read_bytes()
        generator_raw = (root / v1["generator"]["path"]).read_bytes()
        _write(root, calibration_path, (root / calibration_path).read_bytes())
        _write(root, FLOOR._FLOOR_PROTOCOL_REL, FLOOR._canonical_bytes(
            _emitter_protocol(ccbench_pin=ccbench_pin),
        ))
        seed = _fixed_commit_all(root, "receipt emitter seed", "fixture")
        _install_emitter_selector_prediction(root, pre_oracle_head=seed)
        base = _fixed_commit_all(root, "receipt emitter base", "fixture")
    protocol = _emitter_protocol(ccbench_pin=ccbench_pin)
    verified = VerifiedFreeze(document=v1, sha256=M.V1_FREEZE_SHA256)
    out_root = root / "output"
    _fixed_prepare.ccbench_dir = str(root / "external" / "ccbench")
    _fixed_prepare.cache_root = str(out_root / "prepared-cache")
    checkpoint = {}

    def commit_certificate(cert_path: Path):
        rel = cert_path.relative_to(root).as_posix()
        if cert_at_generation:
            checkpoint["C"] = base
            return
        checkpoint["C"] = _commit_exact(
            root, [rel], subject="launch certificate", agent="fixture",
        )

    def payload_hit_preflight(repo_root: Path, **_kwargs) -> dict[str, str]:
        paths = set(FLOOR._PREFLIGHT_FIXED_FILES)
        paths.update(
            path.relative_to(repo_root).as_posix()
            for path in (repo_root / FLOOR._SELECTOR_RUNS_REL).iterdir()
            if path.is_file() and not path.is_symlink()
        )
        return {
            rel: hashlib.sha256((repo_root / rel).read_bytes()).hexdigest()
            for rel in paths
        }

    outcome = _run_official_fixture_campaign(
        protocol, verified, out_root=out_root,
        measure_fn=(_emitter_measure if perf_available else _emitter_measure_degraded),
        perf_receipt=_perf_receipt(available=perf_available),
        probe_fn=lambda: (1, "", ""),
        sleep_fn=lambda _seconds: None, monotonic_fn=lambda: 0.0,
        prepare_fn=_fixed_prepare, now_fn=lambda: now,
        host_provenance_fn=_fixed_host, process_identity_fn=_fixed_process,
        execution_receipt_fn=_fixed_receipt,
        build_fn=_make_emitter_build(compiler_input_rel=compiler_input_rel),
        verified_calibration=_verified_calibration_v2_fixture(),
        repo_root=root, after_certificate_issued_fn=commit_certificate,
        durable_root_policy=DurableRootPolicy(
            approved_roots=(root.resolve(),), forbidden_roots=(),
        ),
        _floor_preflight_fn=(payload_hit_preflight if selector_payload_hit else None),
    )
    selector_mutation_paths = []
    for relative, raw in selector_extra_files:
        _write(root, relative, raw)
        selector_mutation_paths.append(relative)
    run_dir = Path(outcome["run_dir"])
    paths = _emitter_artifact_paths(run_dir, root)
    state = {
        "protocol": protocol,
        "cert": json.loads((root / paths["cert"]).read_bytes()),
        "manifest": json.loads((root / paths["manifest"]).read_bytes()),
        "journal": [json.loads(line) for line in
                    (root / paths["journal"]).read_text(encoding="utf-8").splitlines()],
        "result": json.loads((root / paths["result"]).read_bytes()),
        "paths": paths,
    }
    admission_cells = json.loads(json.dumps(state["manifest"]["cells"]))
    admission_schedule = json.loads(json.dumps(state["manifest"]["schedule"]))
    admission_sessions = json.loads(json.dumps([
        row for row in state["journal"] if row.get("event") == "session"
    ]))
    # Consumer topology fixture は producer core の publish 判定を試すものではない。
    # downstream の accepted artifact を明示的に組み立て、seam 注入の有無から切り離す。
    state["result"]["eligible_for_refreeze"] = True
    original_cert = _json_bytes(state["cert"])
    assert original_cert == (root / paths["cert"]).read_bytes()
    if mutate is not None:
        mutate(state)
        if state.get("repair_manifest"):
            manifest_sha = _sha(_json_bytes(state["manifest"]))
            campaign = next(r for r in state["journal"] if r["event"] == "campaign-start")
            campaign["manifest_sha256"] = manifest_sha
            state["result"]["manifest_sha256"] = manifest_sha
            wall = next(r for r in state["result"]["wall_ledger"]
                        if r["event"] == "campaign-start")
            wall["manifest_sha256"] = manifest_sha

    protocol_raw = _json_bytes(state["protocol"])
    cert_raw = _json_bytes(state["cert"])
    manifest_raw = _json_bytes(state["manifest"])
    journal_raw = _jsonl_bytes(state["journal"])
    registry_fixture = None
    if result_schema == FC.LEGACY_RESULT_SCHEMA:
        admission_root = root / ".git/izanagi/s8b-holdout-admission-v1"
        if admission_root.exists():
            shutil.rmtree(admission_root)
        evidence = build_floor_admission_evidence(
            admission_root, protocol=state["protocol"], freeze=v1,
            freeze_sha256=M.V1_FREEZE_SHA256,
            manifest_sha256=_sha(manifest_raw), campaign_run_id=run_dir.name,
            run_relpath=run_dir.relative_to(out_root).as_posix(), mode="official",
            cells=admission_cells, schedule=admission_schedule,
            sessions=admission_sessions,
        )
        state["result"]["holdout_admission"] = evidence.expected_receipt
    else:
        registry_fixture = V2FIX.attach_v5_attempt_registry(
            root=root, freeze=v1, protocol=state["protocol"],
            cells=admission_cells, schedule=admission_schedule,
            result=state["result"], manifest_raw=manifest_raw,
            run_dir=run_dir.relative_to(root).as_posix(),
            journal_records=state["journal"],
        )
        if mutate_attempt_registry is not None:
            mutate_attempt_registry(state["result"]["attempt_registry"])
    result_record_raw = _json_bytes(state["result"])
    result_raw = result_record_raw + state.get("post_hash_result_suffix", b"")
    _write(root, paths["protocol"], protocol_raw)
    _write(root, paths["manifest"], manifest_raw)
    _write(root, paths["journal"], journal_raw)
    _write(root, paths["result"], result_raw)
    _write(root, paths["closure80"], _RR80_PARAMS)
    _write(root, paths["closure20"], _RR20_PARAMS)
    cert_changed = cert_raw != original_cert
    if cert_changed:
        _write(root, paths["cert"], cert_raw)
    if executable_role is not None:
        target = root / paths[executable_role]
        target.chmod(target.stat().st_mode | 0o111)

    result_md_raw = (root / paths["result_md"]).read_bytes()
    result_md_hits = HF.holdout_conjunction_hits({
        paths["result_md"]: result_md_raw.decode("utf-8"),
    })
    result_md_hit = any(result_md_hits[name] for name in result_md_hits)

    closure_records = [
        {"canonical_path": paths["closure80"], "sha256": _sha(_RR80_PARAMS)},
        {"canonical_path": paths["closure20"], "sha256": _sha(_RR20_PARAMS)},
    ]
    extra_paths = []
    for rel, raw in (extra_closure or []):
        _write(root, rel, raw)
        closure_records.append({"canonical_path": rel, "sha256": _sha(raw)})
        extra_paths.append(rel)
    if result_md_hit:
        closure_records.append({
            "canonical_path": paths["result_md"], "sha256": _sha(result_md_raw),
        })

    if journal_manifest_before_g:
        j_paths = [paths["journal"], paths["manifest"]]
        j_commit = _commit_exact(
            root, j_paths, subject="sealed journal and manifest", agent="fixture",
        )
        frozen = j_commit
    else:
        j_commit = None
        frozen = checkpoint["C"]

    g1 = dict(v1)
    g1.update({
        "schema_version": "8b-holdout-freeze/v2",
        "frozen_at_head": frozen,
        "generation_number": 1,
        "supersedes_sha256": M.V1_FREEZE_SHA256,
        "design_source": {"path": v1["design_source"]["path"], "sha256": _sha(design_raw)},
        "generator": {"path": v1["generator"]["path"], "sha256": _sha(generator_raw)},
        "env_tag": protocol["env_tag"],
        "floor_protocol": {"path": paths["protocol"], "sha256": _sha(protocol_raw)},
        "floor_source": {"path": paths["result"], "sha256": _sha(result_record_raw)},
        "floor": _independent_floor_projection(state["result"]),
        "measurement_closure": closure_records,
    })
    if mutate_g1 is not None:
        mutate_g1(g1)
    gen_path = _gen_rel(1)
    gen_raw = (_json_bytes_with_escaped_strings(g1)
               if generation_strings_escaped else _json_bytes(g1))
    _write(root, gen_path, gen_raw)

    g_paths = [paths["protocol"], paths["result"], paths["closure80"],
               paths["closure20"], gen_path, *extra_paths, *selector_mutation_paths]
    if not journal_manifest_before_g:
        g_paths.extend([paths["journal"], paths["manifest"]])
    if result_md_hit:
        g_paths.append(paths["result_md"])
    if cert_at_generation or cert_changed:
        g_paths.append(paths["cert"])
    g_commit = _commit_exact(
        root, g_paths, subject="generation artifacts", agent="fixture",
    )
    gen_sha = _sha(gen_raw)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    approval_path = f"{M.APPROVAL_DIR}/{gen_sha}.json"
    _write(root, approval_path, approval_raw)
    a_commit = _commit_exact(
        root, [approval_path], subject="approve generation", agent="none",
    )
    pointer_raw = _pointer_raw(1, gen_path, gen_sha, None, approval_sha)
    pointer_sha = _sha(pointer_raw)
    pointer_path = f"{M.ACTIVE_DIR}/{pointer_sha}.json"
    _write(root, pointer_path, pointer_raw)
    x_commit = _commit_exact(
        root, [pointer_path], subject="activate generation", agent="none",
    )
    topology = {
        **state, "base": base, "C": checkpoint["C"], "J": j_commit,
        "G": g_commit, "A": a_commit, "X": x_commit, "H": x_commit,
        "generation_path": gen_path, "generation_raw": gen_raw,
        "generation_sha": gen_sha, "approval_path": approval_path,
        "approval_raw": approval_raw, "pointer_path": pointer_path,
        "pointer_raw": pointer_raw, "result_md_hit": result_md_hit,
        "g_paths": tuple(sorted(g_paths)), "a_paths": (approval_path,),
    }
    if registry_fixture is not None:
        topology.update(registry_fixture)
    bound_mode_paths = [paths[key] for key in
                        ("protocol", "cert", "journal", "manifest", "result",
                         "closure80", "closure20")]
    if result_md_hit:
        bound_mode_paths.append(paths["result_md"])
    topology["mode_map"] = _fixed_mode_map(root, x_commit, [
        *bound_mode_paths, gen_path, approval_path, pointer_path,
    ])
    needles = (str(tmp_path).encode(), str(root).encode(), str(out_root).encode())
    _assert_no_root_bytes(
        (cert_raw, manifest_raw, journal_raw, result_raw, gen_raw,
         approval_raw, pointer_raw),
        needles,
    )
    return root, gen_sha, gen_path, g1, topology


def load_emitter_g1(tmp_path: Path, **kwargs):
    root, _sha256, _rel, _g1, topology = build_production_emitter_g1(tmp_path, **kwargs)
    return root, M.load_ratified_freeze(root), topology


def append_production_emitter_g2(root: Path, g1: dict, g1_sha: str,
                                 topology: dict):
    """同じ履歴へ新 C2 + 新 run artifacts を持つ otherwise-valid g2 を積む。"""
    scan_root = root.parent / "g2 clean scan Ω"
    _scan_v1, scan_pin, _scan_base, _design, _generator = _prepare_emitter_base(
        scan_root, master_seed="fixture-seed-g2",
    )
    assert scan_pin == _fixed_git(root / "external" / "ccbench", "rev-parse", "HEAD")
    protocol = _emitter_protocol(ccbench_pin=scan_pin, master_seed="fixture-seed-g2")
    v1 = json.loads(_REAL_V1.read_bytes())
    verified = VerifiedFreeze(document=v1, sha256=M.V1_FREEZE_SHA256)
    out_root = root / "output"
    _fixed_prepare.ccbench_dir = str(root / "external" / "ccbench")
    _fixed_prepare.cache_root = str(out_root / "prepared-cache-g2")
    checkpoint = {}

    def commit_certificate(cert_path: Path):
        rel = cert_path.relative_to(root).as_posix()
        checkpoint["C2"] = _commit_exact(
            root, [rel], subject="generation two launch certificate", agent="fixture",
        )

    now = _FIXED_NOW + dt.timedelta(minutes=2)
    outcome = _run_official_fixture_campaign(
        protocol, verified, out_root=out_root,
        measure_fn=_emitter_measure, probe_fn=lambda: (1, "", ""),
        sleep_fn=lambda _seconds: None, monotonic_fn=lambda: 0.0,
        prepare_fn=_fixed_prepare, now_fn=lambda: now,
        host_provenance_fn=_fixed_host, process_identity_fn=_fixed_process,
        execution_receipt_fn=_fixed_receipt, build_fn=_make_emitter_build(),
        verified_calibration=_verified_calibration_v2_fixture(),
        repo_root=scan_root, after_certificate_issued_fn=commit_certificate,
        durable_root_policy=DurableRootPolicy(
            approved_roots=(root.resolve(),), forbidden_roots=(),
        ),
    )
    run_dir = Path(outcome["run_dir"])
    paths = _emitter_artifact_paths(run_dir, root)
    manifest_raw = (root / paths["manifest"]).read_bytes()
    manifest = json.loads(manifest_raw)
    journal = [
        json.loads(line)
        for line in (root / paths["journal"]).read_text(
            encoding="utf-8",
        ).splitlines()
    ]
    result = json.loads((root / paths["result"]).read_bytes())
    admission_root = root / ".git/izanagi/s8b-holdout-admission-v1"
    if admission_root.exists():
        shutil.rmtree(admission_root)
    evidence = build_floor_admission_evidence(
        admission_root, protocol=protocol, freeze=v1,
        freeze_sha256=M.V1_FREEZE_SHA256,
        manifest_sha256=_sha(manifest_raw), campaign_run_id=run_dir.name,
        run_relpath=run_dir.relative_to(out_root).as_posix(), mode="official",
        cells=manifest["cells"], schedule=manifest["schedule"],
        sessions=[row for row in journal if row.get("event") == "session"],
    )
    result["holdout_admission"] = evidence.expected_receipt
    # Consumer topology fixture は producer core の publish 判定に依存させない。
    # g2 の accepted result と floor_source hash を同じ bytes から再構成する。
    result["eligible_for_refreeze"] = True
    result_raw = _json_bytes(result)
    _write(root, paths["result"], result_raw)
    protocol_raw = _json_bytes(protocol)
    _write(root, paths["protocol"], protocol_raw)
    _write(root, paths["closure80"], _RR80_PARAMS)
    _write(root, paths["closure20"], _RR20_PARAMS)
    result_md_raw = (root / paths["result_md"]).read_bytes()
    result_md_hits = HF.holdout_conjunction_hits({
        paths["result_md"]: result_md_raw.decode("utf-8"),
    })
    result_md_hit = any(result_md_hits[name] for name in result_md_hits)
    g2 = dict(g1)
    g2.update({
        "frozen_at_head": checkpoint["C2"],
        "generation_number": 2,
        "supersedes_sha256": g1_sha,
        "floor_protocol": {"path": paths["protocol"], "sha256": _sha(protocol_raw)},
        "floor_source": {"path": paths["result"], "sha256": _sha(result_raw)},
        "measurement_closure": [
            {"canonical_path": paths["closure80"], "sha256": _sha(_RR80_PARAMS)},
            {"canonical_path": paths["closure20"], "sha256": _sha(_RR20_PARAMS)},
        ],
    })
    if result_md_hit:
        g2["measurement_closure"].append({
            "canonical_path": paths["result_md"], "sha256": _sha(result_md_raw),
        })
    gen_path = _gen_rel(2)
    gen_raw = _json_bytes(g2)
    _write(root, gen_path, gen_raw)
    g_paths = [
        paths["protocol"], paths["result"], paths["journal"], paths["manifest"],
        paths["closure80"], paths["closure20"], gen_path,
    ]
    if result_md_hit:
        g_paths.append(paths["result_md"])
    # active g2 の full scan を g1 run artifact の残存 hit に依存させない。g1 の governance
    # record は履歴に残し、現 worktree の旧 run artifact だけを G2 で退役させる。
    old_run_paths = set(topology["paths"].values()) & set(topology["g_paths"])
    retired_candidates = sorted(old_run_paths)
    for path in retired_candidates:
        (root / path).unlink()
    retired_g1_paths = tuple(filter(None, _fixed_git(
        root, "diff", "--name-only", "--diff-filter=D", "--", *retired_candidates,
    ).splitlines()))
    g_paths.extend(retired_g1_paths)
    g2_commit = _commit_exact(
        root, g_paths, subject="generation two artifacts", agent="fixture",
    )
    g2_sha = _sha(gen_raw)
    approval_raw = _approval_raw(g2_sha)
    approval_sha = _sha(approval_raw)
    approval_path = f"{M.APPROVAL_DIR}/{g2_sha}.json"
    _write(root, approval_path, approval_raw)
    parent_pointer_sha = _sha(topology["pointer_raw"])
    pointer_raw = _pointer_raw(2, gen_path, g2_sha, parent_pointer_sha, approval_sha)
    pointer_sha = _sha(pointer_raw)
    pointer_path = f"{M.ACTIVE_DIR}/{pointer_sha}.json"
    _write(root, pointer_path, pointer_raw)
    a2 = _commit_exact(
        root, [approval_path], subject="approve generation two", agent="none",
    )
    x2 = _commit_exact(
        root, [pointer_path], subject="activate generation two", agent="none",
    )
    return M.load_ratified_freeze(root), {
        "C2": checkpoint["C2"], "G2": g2_commit, "A2": a2, "X2": x2,
        "paths": paths, "g2": g2, "g2_sha": g2_sha,
        "retired_g1_paths": retired_g1_paths,
    }


def _real_bytes(rel: str) -> bytes:
    return (Path(_ROOT) / rel).read_bytes()


def _make_ccbench_submodule(root: Path) -> None:
    """external/ccbench 入れ子 git repo を作る (enumerate_repository_files の submodule 枝用)。"""
    sub = root / "external" / "ccbench"
    sub.mkdir(parents=True)
    _init_repo(sub)
    (sub / "ccbench.txt").write_text("ccbench fixture (no ycsb params)\n", encoding="utf-8")
    _git(sub, "add", "-A")
    _git(sub, "commit", "-q", "-F", "-", stdin=b"ccbench base\n\nAI-Agent: fixture")


def build_valid_semantic_g1(tmp_path: Path, *, mutate_g1=None, extra_closure=None,
                            floor_source_bytes=None):
    """V1 (source blob + G^==frozen_at_head + closure) / V2 (transition) / V3 (層1/層2) を
    すべて満たす v1→g1 を tmp git repo に組む。(root, gen_sha, gen_rel, g1) を返す。

    mutate_g1(g1) が与えられれば直列化前に g1 dict を破壊できる (負例注入用)。
    extra_closure = [(path, bytes), ...] は base コミットに載せた上で measurement_closure に
    正しい sha で追加する (V1d を満たす追加 closure 経由の負例用)。
    floor_source_bytes を与えると floor_source の blob 内容をそれで差し替える (既定は
    ``_FLOOR_SOURCE_STUB``)。oracle W4 が floor_source を「binaries section を持つ floor
    artifact」として消費するため、その正例を組む拡張点。ycsb params を含まない bytes に
    限る (含むと未申告 hit で launch_validate が落ちる)。

    実 v1 freeze bytes を trust root に据え (sha == V1_FREEZE_SHA256)、g1 は v1 doc から
    protected field を継承しつつ allowed field (schema_version/frozen_at_head/design_source.sha256/
    generator.sha256/env_tag/floor_protocol/floor_source/measurement_closure/header) を書く。
    closure 2 本 (rr80/rr20 params) は search で各 holdout に conjunction hit し、closure 導出と
    完全一致する。陽性対照 (rr50) と protocol/source stub も置く。"""
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)

    v1_raw = _REAL_V1.read_bytes()
    v1_doc = json.loads(v1_raw)
    _write(root, M.V1_FREEZE_PATH, v1_raw)

    ka_path = v1_doc["known_axes_freeze"]["path"]      # protected (実 bytes が v1 sha と一致)
    _write(root, ka_path, _real_bytes(ka_path))
    ds_path = v1_doc["design_source"]["path"]
    gen_path = v1_doc["generator"]["path"]
    ds_bytes = b"# design source stub (g1 overrides sha)\n"
    gen_bytes = b"# generator stub (g1 overrides sha)\n"
    _write(root, ds_path, ds_bytes)
    _write(root, gen_path, gen_bytes)

    f80 = "output/env/floor/rr80.json"
    f20 = "output/env/floor/rr20.json"
    fp = "output/env/floor/protocol.json"
    fs = "output/env/floor/source.py"
    fs_bytes = _FLOOR_SOURCE_STUB if floor_source_bytes is None else floor_source_bytes
    _write(root, f80, _RR80_PARAMS)
    _write(root, f20, _RR20_PARAMS)
    _write(root, fp, _FLOOR_PROTOCOL_STUB)
    _write(root, fs, fs_bytes)
    _write(root, "positive_control.txt", _RR50_PARAMS)
    (root / "README.md").write_text("fixture\n", encoding="utf-8")

    for extra_path, extra_bytes in (extra_closure or []):
        _write(root, extra_path, extra_bytes)

    # external/ccbench 入れ子 git repo (search_repository の enumerate 対象。params 無し)。
    _make_ccbench_submodule(root)

    frozen = _commit(root, "base (frozen_at_head)", "claude-base")

    g1 = dict(v1_doc)
    g1["schema_version"] = "8b-holdout-freeze/v2"
    g1["frozen_at_head"] = frozen
    g1["generation_number"] = 1
    g1["supersedes_sha256"] = M.V1_FREEZE_SHA256
    g1["design_source"] = {"path": ds_path, "sha256": _sha(ds_bytes)}
    g1["generator"] = {"path": gen_path, "sha256": _sha(gen_bytes)}
    g1["env_tag"] = "linux-baremetal"
    g1["floor_protocol"] = {"path": fp, "sha256": _sha(_FLOOR_PROTOCOL_STUB)}
    g1["floor_source"] = {"path": fs, "sha256": _sha(fs_bytes)}
    g1["floor"] = _independent_floor_projection(json.loads(fs_bytes))
    g1["measurement_closure"] = [
        {"canonical_path": f80, "sha256": _sha(_RR80_PARAMS)},
        {"canonical_path": f20, "sha256": _sha(_RR20_PARAMS)},
    ]
    for extra_path, extra_bytes in (extra_closure or []):
        g1["measurement_closure"].append(
            {"canonical_path": extra_path, "sha256": _sha(extra_bytes)}
        )
    if mutate_g1 is not None:
        mutate_g1(g1)
    g1_raw = json.dumps(g1, ensure_ascii=False).encode("utf-8")
    _write(root, _gen_rel(1), g1_raw)
    _commit(root, "candidate g1", "claude-opus")     # G, parent == frozen
    gen_sha = _sha(g1_raw)
    _approve_and_point(root, 1, gen_sha, _gen_rel(1), None)
    return root, gen_sha, _gen_rel(1), g1


# --------------------------------------------------------------------------
# 正常系
# --------------------------------------------------------------------------

@pytest.mark.parametrize("missing", [
    EC.lookup("linux-baremetal").calibration_ref.path,
    *_PREDICTION_SOURCE_PATHS.values(), _PREDICTION_PARSER_PATH,
])
def test_receipt_emitter_requires_copied_inputs(tmp_path, missing):
    calibration_path = EC.lookup("linux-baremetal").calibration_ref.path
    for relative in (calibration_path, *_PREDICTION_SOURCE_PATHS.values(),
                     _PREDICTION_PARSER_PATH):
        if relative != missing:
            _write(tmp_path, relative, b"copied input\n")
    with pytest.raises(AssertionError) as caught:
        build_production_emitter_g1(tmp_path, receipt_root=tmp_path)
    assert str(caught.value).startswith(f"receipt base missing input: {missing}")


@in_sealed_fixture_process
def test_launch_token_retains_immutable_scan_and_root(tmp_path):
    from orchestrator.campaign import t080_freeze_migration as migration
    root, ratified, _topology = load_emitter_g1(tmp_path)
    token = M.launch_validate(ratified, root)
    assert token.validation_root == root.resolve()
    assert token.search_digest == M._enumeration_digest(root)
    assert set(token.search_report["holdouts"]) == {"rr80", "rr20"}
    for name in HF.HOLDOUTS:
        row = token.search_report["holdouts"][name]
        assert row["candidate_id"] == HF.HOLDOUTS[name]["candidate_id"]
        assert row["conjunction_hits"]
        assert isinstance(row["conjunction_hits"], tuple)
        with pytest.raises(TypeError):
            row["expressions"]["unexpected"] = "changed"
    with pytest.raises(TypeError):
        token.search_report["match_convention"] = "changed"
    historical = M.ReverifiedFreeze(**vars(token))
    assert migration._holdout_layer2_delegation(
        root=root, validation_head=token.activation_head, launch_validated=historical,
    ) is None


@in_sealed_fixture_process
def test_happy_path_resolves_and_loads(tmp_path):
    if not _REAL_V1.is_file():
        pytest.fail("実 v1 freeze が無い (trust root 不在 — skip すると攻撃 matrix が緑化する。failures F9 型)")
    root, gen_sha, gen_rel, _g1, topology = build_production_emitter_g1(tmp_path)
    res = M.resolve_active_generation(root)
    assert res.generation_number == 1
    assert res.generation_sha256 == gen_sha
    assert res.generation_path == gen_rel
    assert res.activation_head == _git(root, "rev-parse", "HEAD")
    assert topology["A"] != topology["X"]
    assert M._parents_of(topology["X"], root) == (topology["A"],)

    freeze = M.load_ratified_freeze(root)
    assert isinstance(freeze, M.RatifiedFreeze)
    assert freeze.generation_number == 1
    assert freeze.sha256 == gen_sha
    assert freeze.activation_head == res.activation_head
    assert freeze.document["schema_version"] == "8b-holdout-freeze/v2"
    assert freeze.holdouts == freeze.document["holdouts"]
    assert {
        name: entry["candidate_id"]
        for name, entry in freeze.holdouts.items()
    } == {name: frozen["candidate_id"] for name, frozen in HF.HOLDOUTS.items()}
    with pytest.raises(TypeError):
        freeze.holdouts["rr80"] = {}  # type: ignore[index]
    with pytest.raises(TypeError):
        freeze.holdouts["rr80"]["candidate_id"] = "H2"  # type: ignore[index]
    assert topology["result"]["eligible_for_refreeze"] is True
    assert topology["result"]["schema"] == FC.LEGACY_RESULT_SCHEMA
    assert "attempt_registry" not in topology["result"]
    assert set(topology["manifest"]) == set(M._MANIFEST_KEYS)
    assert set(topology["result"]) == set(FC.result_keys_for_mode("official"))
    assert "perf_preflight" not in topology["manifest"]
    assert "perf_observation" not in topology["result"]
    contract = EC.lookup("linux-baremetal")
    for record in topology["result"]["sessions"]:
        tokens = shlex.split(record["run_cmd"])
        assert tokens[len(contract.numactl):len(contract.numactl) + 2] == ["perf", "stat"]
        assert M._run_cmd_matches_portable_session(
            record, protocol=topology["protocol"],
            binaries=topology["manifest"]["binaries"], contract=contract,
            expected_use_perf=True,
        )
    assert isinstance(M.launch_validate(freeze, root), M.LaunchValidatedFreeze)


@in_sealed_fixture_process
def test_launch_accepts_live_v5_registry_prefix_with_later_append(tmp_path):
    root, freeze, topology = load_emitter_g1(
        tmp_path, result_schema=FC.RESULT_SCHEMA_V5,
    )

    validated = M.launch_validate(freeze, root)

    proof = topology["result"]["attempt_registry"]
    assert isinstance(validated, M.LaunchValidatedFreeze)
    assert topology["result"]["schema"] == FC.RESULT_SCHEMA_V5
    assert frozenset(proof) == frozenset(_ATTEMPT_REGISTRY_PROOF_KEYS)
    assert proof["row_count"] >= 3
    assert topology["live_row_count"] > proof["row_count"]
    live_lines = topology["registry_path"].read_bytes().splitlines()
    assert len(live_lines) == topology["live_row_count"]
    pinned_row = json.loads(live_lines[proof["row_count"] - 1])
    assert pinned_row["event_sha256"] == proof["chain_head_sha256"]


@pytest.mark.parametrize("schema", [[], {}], ids=["list", "object"])
@in_sealed_fixture_process
def test_launch_rejects_unhashable_result_schema_with_controlled_error(
        tmp_path, schema):
    def mutate(state):
        state["result"]["schema"] = schema

    root, freeze, _topology = load_emitter_g1(tmp_path, mutate=mutate)

    with pytest.raises(M.RatifiedFreezeError) as error:
        M.launch_validate(freeze, root)
    assert error.value.reason == "floor-artifact-invalid"

    document = {
        key: None for key in FC.result_keys_for_mode("official")
    }
    document["schema"] = schema
    with pytest.raises(M.RatifiedFreezeError) as local_error:
        M._validate_result(
            document, protocol={}, cells=[], binaries={}, journal={},
            contract=EC.lookup("linux-baremetal"),
        )
    assert local_error.value.reason == "floor-artifact-invalid"
    assert local_error.value.cause == "result-schema"


@pytest.mark.parametrize(
    "mutation",
    [
        *(f"missing:{field}" for field in _ATTEMPT_REGISTRY_PROOF_KEYS),
        "extra-key",
        *(f"invalid:{field}" for field in _ATTEMPT_REGISTRY_PROOF_KEYS),
    ],
)
@in_sealed_fixture_process
def test_launch_rejects_invalid_v5_registry_proof(tmp_path, mutation):
    root, freeze, _topology = load_emitter_g1(
        tmp_path, result_schema=FC.RESULT_SCHEMA_V5,
        mutate_attempt_registry=lambda proof: (
            _mutate_attempt_registry_proof(proof, mutation)
        ),
    )

    with pytest.raises(M.RatifiedFreezeError):
        M.launch_validate(freeze, root)


@pytest.mark.parametrize(
    ("ledger_mutation", "expected_cause"),
    (
        ("missing", "attempt-registry-read-unavailable"),
        ("tampered", "attempt-registry-replay-invalid"),
        ("shortened", "attempt-registry-prefix-too-short"),
    ),
)
@in_sealed_fixture_process
def test_launch_rejects_invalid_live_v5_registry(
        tmp_path, ledger_mutation, expected_cause):
    root, freeze, topology = load_emitter_g1(
        tmp_path, result_schema=FC.RESULT_SCHEMA_V5,
    )
    registry_path = topology["registry_path"]
    lines = registry_path.read_bytes().splitlines()
    if ledger_mutation == "missing":
        registry_path.unlink()
    elif ledger_mutation == "tampered":
        row = json.loads(lines[1])
        digest = row["event_sha256"]
        row["event_sha256"] = ("0" if digest[0] != "0" else "1") + digest[1:]
        registry_path.write_bytes(b"\n".join((
            lines[0], V2FIX.canonical_bytes(row), *lines[2:],
        )) + b"\n")
    else:
        registry_path.write_bytes(lines[0] + b"\n")

    with pytest.raises(M.RatifiedFreezeError) as error:
        M.launch_validate(freeze, root)
    assert error.value.cause == expected_cause


@in_sealed_fixture_process
def test_loader_rejects_floor_source_projection_mismatch(tmp_path):
    def mutate_g1(g1):
        holdout_id = sorted(g1["floor"]["by_holdout"])[0]
        g1["floor"]["by_holdout"][holdout_id]["scalar_alt"] = 123456.0

    root, *_ = build_production_emitter_g1(
        tmp_path, mutate_g1=mutate_g1,
    )
    with pytest.raises(M.RatifiedFreezeError) as caught:
        M.load_ratified_freeze(root)
    assert caught.value.reason == "floor-source-projection-mismatch"
    assert caught.value.cause == "floor-source-projection"


@in_sealed_fixture_process
def test_degraded_launch_threads_expected_use_perf_to_every_consumer(tmp_path):
    """M8: journal/stats/result/axis の一箇所でも旧 True へ戻れば拒否する。"""
    root, freeze, topology = load_emitter_g1(tmp_path, perf_available=False)
    manifest = topology["manifest"]
    result = topology["result"]
    assert PERF_PREFLIGHT.use_perf_from_receipt(manifest["perf_preflight"]) is False
    assert result["perf_preflight"] == manifest["perf_preflight"]
    assert result["perf_observation"] == manifest["perf_observation"]

    with mock.patch.object(
            M, "_validate_journal", wraps=M._validate_journal) as journal_spy, \
            mock.patch.object(
                M._floor_stats, "verify_floor_artifact_with_live_admission",
                wraps=M._floor_stats.verify_floor_artifact_with_live_admission,
            ) as stats_spy, \
            mock.patch.object(
                M, "_validate_result", wraps=M._validate_result,
            ) as result_spy, \
            mock.patch.object(
                M, "_validate_axis_occurrences", wraps=M._validate_axis_occurrences,
            ) as axis_spy:
        validated = M.launch_validate(freeze, root)

    assert isinstance(validated, M.LaunchValidatedFreeze)
    for spy in (journal_spy, stats_spy, result_spy, axis_spy):
        assert spy.call_count == 1
        assert spy.call_args.kwargs["expected_use_perf"] is False
    contract = EC.lookup("linux-baremetal")
    for record in result["sessions"]:
        tokens = shlex.split(record["run_cmd"])
        assert tokens[len(contract.numactl)] != "perf"


@pytest.mark.parametrize(
    ("mutation", "expected_cause"),
    (
        ("missing-receipt-field", "perf-preflight-receipt"),
        ("extra-event-key", "schema-keys"),
    ),
)
@in_sealed_fixture_process
def test_ratified_journal_rejects_invalid_perf_preflight_event(
        tmp_path, mutation, expected_cause,
):
    """perf-preflight の外側・内側 schema を ratified journal でも閉じる。"""
    root, _freeze, topology = load_emitter_g1(tmp_path, perf_available=False)
    records = [dict(record) for record in topology["journal"]]
    event_index = next(
        index for index, record in enumerate(records)
        if record.get("event") == "perf-preflight"
    )
    event = records[event_index]
    if mutation == "missing-receipt-field":
        receipt = dict(event["perf_preflight_receipt"])
        receipt.pop("status")
        event["perf_preflight_receipt"] = receipt
    else:
        event["unexpected"] = True

    manifest = topology["manifest"]
    with pytest.raises(M.RatifiedFreezeError) as error:
        M._validate_journal(
            tuple(records), protocol=topology["protocol"],
            schedule=manifest["schedule"], cells=manifest["cells"],
            binaries=manifest["binaries"],
            cert_sha256=_sha((root / topology["paths"]["cert"]).read_bytes()),
            manifest_sha256=_sha((root / topology["paths"]["manifest"]).read_bytes()),
            root=root, contract=EC.lookup("linux-baremetal"), expected_use_perf=False,
        )
    assert error.value.reason == "journal-state-invalid"
    assert error.value.cause == expected_cause


def _degraded_portable_record():
    contract = EC.lookup("linux-baremetal")
    holdout = HF.HOLDOUTS["rr80"]
    binary = "output/portable/fixture.exe"
    record = {
        "cell_id": "rr80::stock_common",
        "records": holdout["records"],
        "threads": holdout["threads"],
        "workload": holdout["ycsb"],
    }
    expected = FC.build_portable_run_cmd(
        binary=binary, workload=record["workload"], records=record["records"],
        threads=record["threads"], extime_s=5,
        clocks_per_us=contract.clocks_per_us, numactl=contract.numactl,
        use_perf=False,
    )
    record["run_cmd"] = shlex.join(expected)
    binaries = {record["cell_id"]: {"binary": binary}}
    return contract, record, binaries, expected


def test_degraded_axis_occurrence_uses_false_portable_projection():
    """M8 axis: scanner 内の consumer だけ旧 True へ戻る変異を殺す。"""
    contract, record, binaries, _expected = _degraded_portable_record()
    record["event"] = "session"
    raw = _jsonl_bytes([record])
    hits = M._validate_axis_occurrences(
        artifacts=(("output/run/journal.jsonl", (record,), raw),),
        protocol={"extime_s": 5}, binaries=binaries, contract=contract,
        expected_use_perf=False,
    )
    assert hits["rr80"] == ["output/run/journal.jsonl"]


def test_degraded_result_observation_is_exactly_bound_to_manifest():
    receipt = _perf_receipt(available=False)
    observation = {
        "use_perf": False,
        "counter_status": "not_required",
        "missing_leading_indicators": [],
        "preflight": receipt,
        "claim_scope": {
            "throughput": "eligible",
            "perf_required": "unsupported",
        },
    }
    result = {
        key: None for key in FC.result_keys_for_mode(
            "official", perf_preflight=receipt,
        )
    }
    result["perf_preflight"] = receipt
    result["perf_observation"] = json.loads(json.dumps(observation))
    assert result["schema"] is None
    M._validate_result_top_level_keys(
        result, expected_use_perf=False,
        expected_perf_preflight=receipt,
        expected_perf_observation=observation,
    )
    result["perf_observation"]["claim_scope"]["throughput"] = "unsupported"
    with pytest.raises(M.RatifiedFreezeError) as error:
        M._validate_result_top_level_keys(
            result, expected_use_perf=False,
            expected_perf_preflight=receipt,
            expected_perf_observation=observation,
        )
    assert error.value.reason == "binding-chain-mismatch"
    assert error.value.cause == "result-manifest-perf-observation"


def test_degraded_portable_projection_passes_use_perf_explicitly():
    """M9: build_portable_run_cmd の既定 True 復活を call kwargs で直接殺す。"""
    contract, record, binaries, expected = _degraded_portable_record()
    with mock.patch.object(
            FC, "build_portable_run_cmd", wraps=FC.build_portable_run_cmd) as build_spy:
        M._run_cmd_matches_portable_session(
            record, protocol={"extime_s": 5}, binaries=binaries,
            contract=contract, expected_use_perf=False,
        )
    assert build_spy.call_count == 1
    assert build_spy.call_args.kwargs.get("use_perf") is False
    assert tuple(shlex.split(record["run_cmd"])) == expected
    assert expected[len(contract.numactl)] != "perf"


def _emitter_observation(tmp_path: Path) -> dict:
    root, freeze, topology = load_emitter_g1(tmp_path)
    validated = M.launch_validate(freeze, root)
    artifact_names = ("cert", "manifest", "journal", "result")
    artifact_sha = {
        name: _sha((root / topology["paths"][name]).read_bytes())
        for name in artifact_names
    }
    blob_sha256 = {
        "generation": _sha(topology["generation_raw"]),
        "approval": _sha(topology["approval_raw"]),
        "pointer": _sha(topology["pointer_raw"]),
    }
    blob_oids = {
        name: _fixed_git(root, "rev-parse", f"{topology['X']}:{topology[path_key]}")
        for name, path_key in (
            ("generation", "generation_path"),
            ("approval", "approval_path"),
            ("pointer", "pointer_path"),
        )
    }
    commits = {name: topology[name] for name in ("base", "C", "G", "A", "X")}
    trees = {name: _fixed_git(root, "rev-parse", f"{commit}^{{tree}}")
             for name, commit in commits.items()}
    return {
        "artifact_sha": artifact_sha,
        "blob_sha256": blob_sha256,
        "blob_oids": blob_oids,
        "commits": commits,
        "trees": trees,
        "mode_map": topology["mode_map"],
        "result_md_hit": topology["result_md_hit"],
        "g_paths": topology["g_paths"],
        "validated_sha": validated.floor_artifact.sha256,
    }


@in_sealed_fixture_process
def test_production_emitter_staged_builder_is_git_deterministic_across_roots(tmp_path):
    """長さ・空白・非 ASCII の異なる root でも bytes/blob/tree/commit/mode が一致する。"""
    observations = [
        _emitter_observation(tmp_path / "短"),
        _emitter_observation(tmp_path / "a much longer root with spaces Ω"),
    ]
    assert observations[0] == observations[1]
    assert observations[0]["result_md_hit"] is False
    assert observations[0]["validated_sha"] == observations[0]["artifact_sha"]["result"]
    g_paths = observations[0]["g_paths"]
    assert not any("s8b-build-cache" in path or "/binaries/" in path for path in g_paths)
    assert not any(path.endswith("result.md") for path in g_paths)


def test_commit_exact_rejects_an_extra_pre_staged_path(tmp_path):
    root = tmp_path / "exact-negative"
    _init_fixed_repo(root)
    _write(root, "README.md", b"base\n")
    _fixed_commit_all(root, "base", "fixture")
    _write(root, "expected.txt", b"expected\n")
    _write(root, "extra.txt", b"extra\n")
    _fixed_git(root, "add", "extra.txt")
    with pytest.raises(AssertionError):
        _commit_exact(
            root, ["expected.txt"],
            subject="must not commit", agent="fixture",
        )


def test_root_bytes_scan_rejects_a_leaked_root() -> None:
    needle = b"/tmp/root with spaces"
    with pytest.raises(AssertionError):
        _assert_no_root_bytes([b"prefix:" + needle], [needle])


@in_sealed_fixture_process
def test_journal_manifest_may_precede_generation_and_executable_mode_is_accepted(tmp_path):
    """C→J(journal+manifest)→G→A→X と 100755 は裁定どおり受理される。"""
    root, freeze, topology = load_emitter_g1(
        tmp_path, journal_manifest_before_g=True, executable_role="manifest",
    )
    assert topology["C"] != topology["J"] != topology["G"] != topology["A"] != topology["X"]
    j_paths = tuple(filter(None, _fixed_git(
        root, "diff-tree", "--no-commit-id", "--name-only", "-r", topology["J"],
    ).splitlines()))
    assert j_paths == tuple(sorted((topology["paths"]["journal"],
                                    topology["paths"]["manifest"])))
    assert topology["mode_map"][topology["paths"]["manifest"]] == "100755"
    assert isinstance(M.launch_validate(freeze, root), M.LaunchValidatedFreeze)


def test_legacy_freeze_binds_v1_by_constant(tmp_path):
    if not _REAL_V1.is_file():
        pytest.fail("実 v1 freeze が無い (trust root 不在 — skip すると攻撃 matrix が緑化する。failures F9 型)")
    root = _base_repo(tmp_path)
    legacy = M.load_legacy_freeze(root)
    assert isinstance(legacy, M.LegacyFreeze)
    assert legacy.sha256 == M.V1_FREEZE_SHA256
    # v2 型ではない (candidate/legacy を実走 v2 経路へ流せない型分離)。
    assert not isinstance(legacy, M.RatifiedFreeze)


def test_legacy_freeze_rejects_wrong_bytes(tmp_path):
    root = tmp_path / "r"
    root.mkdir()
    _init_repo(root)
    _write(root, M.V1_FREEZE_PATH, b"{\"tampered\": true}")
    _commit(root, "v1 tamper", "claude")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.load_legacy_freeze(root)
    assert ei.value.reason == "legacy-hash"


# --------------------------------------------------------------------------
# approval / pointer / hash の不整合
# --------------------------------------------------------------------------

def test_missing_approval_no_active(tmp_path):
    # candidate 世代のみ (approval/pointer 無し) → active なし (consumer に渡せない型分離)。
    root = _base_repo(tmp_path)
    _add_generation(root, 1, M.V1_FREEZE_SHA256)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "no-active"


def test_manifest_cli_maps_only_no_active_and_creates_no_output(
        tmp_path, monkeypatch, capsys):
    root = _base_repo(tmp_path)
    monkeypatch.setattr(ORACLE_MANIFEST, "ROOT", root)
    output = (
        f"{ORACLE_MANIFEST.MANIFEST_CANDIDATE_DIR}/manifest.json"
    )

    assert ORACLE_MANIFEST.main([
        "build-approved", "--output", output,
    ]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "refused: no-active-ratified-freeze\n"
    assert not (root / ORACLE_MANIFEST.MANIFEST_CANDIDATE_DIR).exists()


def test_manifest_cli_does_not_round_namespace_dirty_to_no_active(
        tmp_path, monkeypatch, capsys):
    root = _base_repo(tmp_path)
    _write(root, f"{M.FREEZE_DIR}/untracked.json", b"{}")
    monkeypatch.setattr(ORACLE_MANIFEST, "ROOT", root)
    output = (
        f"{ORACLE_MANIFEST.MANIFEST_CANDIDATE_DIR}/manifest.json"
    )

    assert ORACLE_MANIFEST.main([
        "build-approved", "--output", output,
    ]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "refused: namespace-dirty\n"
    assert not (root / ORACLE_MANIFEST.MANIFEST_CANDIDATE_DIR).exists()


def test_pointer_references_absent_approval(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    # pointer は存在しない approval_sha を参照 (approval file を載せない)。
    bogus_approval = "a" * 64
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, bogus_approval)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    _commit(root, "point only", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "pointer-approval"


def test_approval_filename_hash_mismatch(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_raw = _approval_raw(gen_sha)
    # filename を別 hash にする (内容 generation_sha256 と不一致)。
    _write(root, f"{M.APPROVAL_DIR}/{'b' * 64}.json", approval_raw)
    _commit(root, "bad approval name", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "approval-filename"


def test_pointer_content_hash_mismatch(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_sha, _ = _approve_and_point(root, 1, gen_sha, gen_rel, None)
    # 別世代 file を足すが pointer.sha256 は g1 のまま → path/sha 突き合わせで検出させる。
    # ここでは pointer.sha256 を壊した第二世代を作らず、pointer が指す sha を改ざん。
    # 直接 pointer の sha256 を別値にした pointer を第二 genesis 代わりに載せると型が変わるため、
    # 単純に「pointer.sha256 が世代 bytes hash と不一致」を作る。
    wrong = "c" * 64
    ptr_raw = _pointer_raw(1, gen_rel, wrong, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    _commit(root, "wrong sha pointer", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason in ("pointer-generation", "pointer-fork", "genesis-count")


# --------------------------------------------------------------------------
# 導入 commit / trailer / topology (C1-4/C1-6)
# --------------------------------------------------------------------------

def test_non_ancestry_user_commit_rejected(tmp_path):
    root, *_ = _valid_g1(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    # 別ブランチに未 merge の none commit を作る。
    _git(root, "checkout", "-q", "-b", "sidebranch")
    (root / "side.txt").write_text("s\n", encoding="utf-8")
    side = _commit(root, "side", "none")
    _git(root, "checkout", "-q", head)
    graph = M._commit_graph(head, root)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._assert_user_commit(side, graph, root)
    assert ei.value.reason == "user-commit-ancestry"


def test_approval_commit_with_ai_trailer_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    # approval commit を AI trailer にする (人間 commit でない)。
    with pytest.raises(M.RatifiedFreezeError) as ei:
        _approve_and_point(root, 1, gen_sha, gen_rel, None, ai_agent="claude-opus")
        M.resolve_active_generation(root)
    assert ei.value.reason == "user-commit-trailer"


def test_trailer_both_none_and_structured_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    _commit_raw(root, "approve\n\nAI-Agent: none\nAI-Agent: claude-opus\n")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "user-commit-trailer"


def test_trailer_case_or_space_variant_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    # 小文字 key は逐語 `AI-Agent: none` でないため拒否。
    _commit_raw(root, "approve\n\nai-agent: none\n")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "user-commit-trailer"


def test_trailer_none_trailing_space_rejected(tmp_path):
    # R3: approval commit の trailer 行が `AI-Agent: none ` (末尾空白 1 個)。
    # git interpret-trailers --parse は空白を丸めて "none" を返すため parse 側検査だけでは
    # 素通りする。_is_none_commit の raw 行 byte-for-byte 検査 (== "AI-Agent: none") のみが
    # これを拒否できる。この raw 検査を startswith 化する変異はこのテストで殺せる。
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    # 末尾空白付き trailer を verbatim で保存する (既定 cleanup は空白を落とす)。
    commit = _commit_verbatim(root, "approve\n\nAI-Agent: none \n")
    # 前提: raw に末尾空白が保存され、parse 側は "none" に丸める (両立で初めて攻撃が成立)。
    assert M._raw_ai_agent_lines(M._commit_message(commit, root)) == ["AI-Agent: none "]
    assert M._parsed_ai_agent_values(M._commit_message(commit, root), root) == ["none"]
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "user-commit-trailer"


def test_approval_commit_with_extra_file_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    (root / "extra.txt").write_text("sneaky\n", encoding="utf-8")  # 余分ファイル
    _commit(root, "approve+extra", "none")
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    _commit(root, "point", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "approval-commit-diff"


def test_pointer_commit_with_extra_file_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    _commit(root, "approve", "none")
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    (root / "extra.txt").write_text("sneaky\n", encoding="utf-8")
    _commit(root, "point+extra", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "pointer-commit-diff"


def test_pointer_parent_must_be_selected_approval_commit(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    _commit(root, "approve", "none")
    (root / "intervening.txt").write_text("intervening\n", encoding="utf-8")
    _commit(root, "intervening", "none")
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    _commit(root, "point", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "pointer-approval-parent"


def test_approval_and_pointer_same_commit_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    _commit(root, "approve and point", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "approval-pointer-same-commit"


def test_generation_and_approval_same_commit_rejected(tmp_path):
    # 世代 + approval + pointer を一つの none commit に入れる (C1-4 単一 commit 迂回)。
    # 世代を none commit で導入した時点で provenance 虚偽として拒否される。
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = "", _gen_rel(1)
    gen_raw = _gen_raw(1, M.V1_FREEZE_SHA256)
    gen_sha = _sha(gen_raw)
    _write(root, gen_rel, gen_raw)
    approval_raw = _approval_raw(gen_sha)
    approval_sha = _sha(approval_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", approval_raw)
    ptr_raw = _pointer_raw(1, gen_rel, gen_sha, None, approval_sha)
    ptr_sha = _sha(ptr_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr_sha}.json", ptr_raw)
    _commit(root, "all-in-one", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "generation-commit-none"


def test_generation_introduced_in_none_commit_rejected(tmp_path):
    # 世代を単独 none commit で導入 (AI 生成物を人間 commit に混ぜる)。
    root = _base_repo(tmp_path)
    gen_raw = _gen_raw(1, M.V1_FREEZE_SHA256)
    _write(root, _gen_rel(1), gen_raw)
    _commit(root, "gen in human commit", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "generation-commit-none"


# --------------------------------------------------------------------------
# 履歴不変条件 (C1-5) — helper 直叩き + merge 統合
# --------------------------------------------------------------------------

def _blob_oid(root: Path, path: str) -> str:
    return _git(root, "rev-parse", f"HEAD:{path}")


def test_history_allows_delete_then_same_bytes_recreate(tmp_path):
    root = _base_repo(tmp_path)
    rel = f"{M.APPROVAL_DIR}/{'d' * 64}.json"
    raw = _approval_raw("d" * 64)
    _write(root, rel, raw)
    _commit(root, "add", "none")
    (root / rel).unlink()
    _commit(root, "delete", "none")
    _write(root, rel, raw)  # 同一 bytes 再作成
    head = _commit(root, "readd", "none")
    graph = M._commit_graph(head, root)
    oid = _blob_oid(root, rel)
    intro = M._immutable_introductions(graph, rel, oid, root)
    assert len(intro) == 2, "削除→同一 bytes 再作成は不変条件を破らず 2 導入"


def test_history_rejects_delete_then_different_bytes(tmp_path):
    root = _base_repo(tmp_path)
    rel = f"{M.APPROVAL_DIR}/{'e' * 64}.json"
    _write(root, rel, _approval_raw("e" * 64))
    _commit(root, "add", "none")
    _write(root, rel, _approval_raw("f" * 64))  # 別 bytes に改変
    head = _commit(root, "mutate", "none")
    graph = M._commit_graph(head, root)
    oid = _blob_oid(root, rel)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M._immutable_introductions(graph, rel, oid, root)
    assert ei.value.reason == "history-mutated"


def test_merge_add_add_yields_multiple_introductions(tmp_path):
    # 両親で同一 path/bytes を導入し merge (history simplification 攻撃)。全 DAG 走査で
    # 両導入を検出し、governance record では multiple-introduction で拒否する。
    root = _base_repo(tmp_path)
    base = _git(root, "rev-parse", "HEAD")
    rel = f"{M.APPROVAL_DIR}/{'1' * 64}.json"
    raw = _approval_raw("1" * 64)

    _git(root, "checkout", "-q", "-b", "b1")
    _write(root, rel, raw)
    _commit(root, "add on b1", "none")

    _git(root, "checkout", "-q", base)
    _git(root, "checkout", "-q", "-b", "b2")
    _write(root, rel, raw)
    _commit(root, "add on b2", "none")

    _git(root, "checkout", "-q", "b1")
    _git(root, "merge", "-q", "--no-edit", "b2")  # add/add 同一 bytes → 競合なし
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "multiple-introduction"


def test_path_later_mutation_rejected(tmp_path):
    root, gen_sha, gen_rel, approval_sha, ptr_sha = _valid_g1(tmp_path)
    # approval を後日別 bytes に改変して再 commit。
    approval_rel = f"{M.APPROVAL_DIR}/{gen_sha}.json"
    _write(root, approval_rel, _approval_raw("9" * 64))
    _commit(root, "mutate approval", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "history-mutated"


# --------------------------------------------------------------------------
# revocation / cancellation
# --------------------------------------------------------------------------

def _revocation_raw(gen_sha: str) -> bytes:
    return M._canonical_bytes({
        "generation_sha256": gen_sha, "revoked_by": "user",
        "revoked_at": "2026-07-18T00:00:00Z", "reason": "test",
    })


def _cancel_raw(ptr_sha: str) -> bytes:
    return M._canonical_bytes({
        "pointer_sha256": ptr_sha, "cancelled_by": "user",
        "cancelled_at": "2026-07-18T00:00:00Z", "reason": "test",
    })


def test_valid_revocation_yields_no_active(tmp_path):
    root, gen_sha, *_ = _valid_g1(tmp_path)
    _write(root, f"{M.REVOCATION_DIR}/{gen_sha}.json", _revocation_raw(gen_sha))
    _commit(root, "revoke g1", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "tip-revoked"


def test_revocation_with_ai_trailer_is_error_not_ignored(tmp_path):
    root, gen_sha, *_ = _valid_g1(tmp_path)
    _write(root, f"{M.REVOCATION_DIR}/{gen_sha}.json", _revocation_raw(gen_sha))
    _commit(root, "revoke g1 (ai)", "claude-opus")  # 無効 record
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "user-commit-trailer"


# --------------------------------------------------------------------------
# pointer 連鎖 / fork / genesis / 連番
# --------------------------------------------------------------------------

def test_second_genesis_rejected(tmp_path):
    root, gen_sha, gen_rel, approval_sha, ptr_sha = _valid_g1(tmp_path)
    # 第二の parent-null pointer を足す (同じ g1・approval を指す別 pointer は不可なので、
    # 別世代 g2 を作ってその genesis pointer を載せる)。
    gen2_sha, gen2_rel = _add_generation(root, 2, gen_sha)
    approval2_raw = _approval_raw(gen2_sha)
    approval2_sha = _sha(approval2_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen2_sha}.json", approval2_raw)
    _commit(root, "approve second genesis", "none")
    ptr2_raw = _pointer_raw(2, gen2_rel, gen2_sha, None, approval2_sha)  # parent null = 第二 genesis
    ptr2_sha = _sha(ptr2_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr2_sha}.json", ptr2_raw)
    _commit(root, "point second genesis", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    # 第二 genesis (pointer.generation_number=2 だが parent=null) → number-gap または genesis-count。
    assert ei.value.reason in ("genesis-count", "pointer-number-gap")


def test_generation_number_jump_g999_rejected(tmp_path):
    root, gen_sha, gen_rel, approval_sha, ptr_sha = _valid_g1(tmp_path)
    # g999 を child pointer で足す (親世代 g998 が無いため連鎖に穴)。
    gen999_sha, gen999_rel = _add_generation(root, 999, gen_sha)
    approval999_raw = _approval_raw(gen999_sha)
    approval999_sha = _sha(approval999_raw)
    _write(root, f"{M.APPROVAL_DIR}/{gen999_sha}.json", approval999_raw)
    _commit(root, "approve g999", "none")
    ptr999_raw = _pointer_raw(999, gen999_rel, gen999_sha, ptr_sha, approval999_sha)
    ptr999_sha = _sha(ptr999_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr999_sha}.json", ptr999_raw)
    _commit(root, "point g999", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "generation-chain-gap"


def _build_chain_g2(root: Path, g1_sha: str, g1_rel: str, ptr1_sha: str):
    """g1 の上に g2 と child pointer (parent=ptr1) を積む。(g2_sha, g2_rel, ptr2_sha) を返す。"""
    g2_sha, g2_rel = _add_generation(root, 2, g1_sha)
    approval2_sha, ptr2_sha = _approve_and_point(root, 2, g2_sha, g2_rel, ptr1_sha)
    return g2_sha, g2_rel, ptr2_sha


def test_pointer_fork_and_cancellation_recovery(tmp_path):
    root, g1_sha, g1_rel, approval1_sha, ptr1_sha = _valid_g1(tmp_path)
    # g2 (child of ptr1) と g3 (child of ptr1) の 2 本 → fork。
    g2_sha, g2_rel, ptr2_sha = _build_chain_g2(root, g1_sha, g1_rel, ptr1_sha)
    g3_sha, g3_rel = _add_generation(root, 3, g2_sha)
    approval3_raw = _approval_raw(g3_sha)
    approval3_sha = _sha(approval3_raw)
    _write(root, f"{M.APPROVAL_DIR}/{g3_sha}.json", approval3_raw)
    _commit(root, "approve fork g3", "none")
    ptr3_raw = _pointer_raw(3, g3_rel, g3_sha, ptr1_sha, approval3_sha)  # 同じ parent=ptr1 → fork
    ptr3_sha = _sha(ptr3_raw)
    _write(root, f"{M.ACTIVE_DIR}/{ptr3_sha}.json", ptr3_raw)
    _commit(root, "point fork g3", "none")

    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "pointer-fork"

    # ptr3 を cancellation tombstone で取消 → fork 回復 → active = g2。
    _write(root, f"{M.ACTIVE_CANCEL_DIR}/{ptr3_sha}.json", _cancel_raw(ptr3_sha))
    _commit(root, "cancel ptr3", "none")
    res = M.resolve_active_generation(root)
    assert res.generation_number == 2
    assert res.generation_sha256 == g2_sha


def test_cancellation_with_ai_trailer_is_error(tmp_path):
    root, g1_sha, g1_rel, approval1_sha, ptr1_sha = _valid_g1(tmp_path)
    _write(root, f"{M.ACTIVE_CANCEL_DIR}/{ptr1_sha}.json", _cancel_raw(ptr1_sha))
    _commit(root, "cancel (ai)", "claude-opus")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "user-commit-trailer"


# --------------------------------------------------------------------------
# strict parse / schema
# --------------------------------------------------------------------------

def test_generation_with_nan_rejected(tmp_path):
    root = _base_repo(tmp_path)
    raw = b'{"schema_version": "8b-holdout-freeze/v2", "floor": NaN}'
    _write(root, _gen_rel(1), raw)
    _commit(root, "nan gen", "claude-opus")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "json-nan"


def test_approval_duplicate_key_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    dup = b'{"generation_sha256": "%s", "generation_sha256": "%s", "approver": "u", "approved_at": "t", "scope": "s"}' % (
        gen_sha.encode(), gen_sha.encode())
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", dup)
    _commit(root, "dup approval", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "json-duplicate-key"


def test_non_canonical_approval_rejected(tmp_path):
    root = _base_repo(tmp_path)
    gen_sha, gen_rel = _add_generation(root, 1, M.V1_FREEZE_SHA256)
    pretty = json.dumps({
        "generation_sha256": gen_sha, "approver": "u",
        "approved_at": "t", "scope": "s",
    }, indent=2).encode("utf-8")  # canonical でない (空白入り)
    _write(root, f"{M.APPROVAL_DIR}/{gen_sha}.json", pretty)
    _commit(root, "pretty approval", "none")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "not-canonical"


def test_generation_with_approval_field_rejected(tmp_path):
    root = _base_repo(tmp_path)
    doc = {key: "x" for key in M.V2_TOP_LEVEL_KEYS}
    doc["schema_version"] = "8b-holdout-freeze/v2"
    doc["generation_number"] = 1
    doc["supersedes_sha256"] = M.V1_FREEZE_SHA256
    doc["approved_by"] = "user"  # 世代に現れてはならない approval 系 field
    raw = json.dumps(doc, ensure_ascii=False).encode("utf-8")
    _write(root, _gen_rel(1), raw)
    _commit(root, "gen with approval field", "claude-opus")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "generation-approval-field"


def test_generation_supersedes_mismatch_rejected(tmp_path):
    root = _base_repo(tmp_path)
    _add_generation(root, 1, "0" * 64)  # v1 hash でない supersedes (承認なしでも chain 検査で落ちる)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "generation-supersedes"


# --------------------------------------------------------------------------
# 深い不変性 / shallow / dirty / 型分離 / static
# --------------------------------------------------------------------------

def _direct_ratified_freeze(document: dict) -> M.RatifiedFreeze:
    return M.RatifiedFreeze(
        document=document,
        sha256="a" * 64,
        generation_number=1,
        activation_head="b" * 40,
        generation_commit="c" * 40,
    )


def _direct_holdouts_document() -> dict:
    return {
        "holdouts": {
            name: {"candidate_id": frozen["candidate_id"]}
            for name, frozen in HF.HOLDOUTS.items()
        }
    }


@pytest.mark.parametrize(
    ("case", "expected_reason"),
    [
        ("missing", "holdouts-schema"),
        ("non-mapping", "holdouts-schema"),
        ("entry-non-mapping", "holdout-entry"),
        ("candidate-id-swap", "holdout-entry"),
    ],
)
def test_ratified_freeze_holdouts_property_rejects_invalid_projection(
    case: str, expected_reason: str,
) -> None:
    document = _direct_holdouts_document()
    if case == "missing":
        del document["holdouts"]
    elif case == "non-mapping":
        document["holdouts"] = []
    elif case == "entry-non-mapping":
        document["holdouts"]["rr80"] = []
    elif case == "candidate-id-swap":
        document["holdouts"]["rr80"]["candidate_id"] = "H2"
        document["holdouts"]["rr20"]["candidate_id"] = "H1"
    else:  # pragma: no cover - parameter values are exhaustive
        raise AssertionError(case)

    with pytest.raises(M.RatifiedFreezeError) as error:
        _direct_ratified_freeze(document).holdouts
    assert error.value.reason == expected_reason


def test_ratified_freeze_holdouts_property_freezes_direct_mutable_document() -> None:
    document = {
        "holdouts": {
            name: {
                "candidate_id": frozen["candidate_id"],
                "metadata": {"tags": [name]},
            }
            for name, frozen in HF.HOLDOUTS.items()
        }
    }
    projection = _direct_ratified_freeze(document).holdouts

    with pytest.raises(TypeError):
        projection["rr80"]["candidate_id"] = "mutated"  # type: ignore[index]
    with pytest.raises(TypeError):
        projection["rr80"]["metadata"]["tags"] = ()  # type: ignore[index]
    assert document["holdouts"]["rr80"]["candidate_id"] == "H1"

    document["holdouts"]["rr80"]["candidate_id"] = "changed-after-read"
    assert projection["rr80"]["candidate_id"] == "H1"


def test_ratified_freeze_holdouts_property_normalizes_non_dict_mappings() -> None:
    document = {
        "holdouts": UserDict(
            {
                name: UserDict(
                    {
                        "candidate_id": frozen["candidate_id"],
                        "metadata": {"tags": [name]},
                    }
                )
                for name, frozen in HF.HOLDOUTS.items()
            }
        )
    }
    projection = _direct_ratified_freeze(document).holdouts

    with pytest.raises(TypeError):
        projection["rr80"]["candidate_id"] = "mutated"  # type: ignore[index]
    with pytest.raises(TypeError):
        projection["rr80"]["metadata"]["tags"] = ()  # type: ignore[index]
    assert projection["rr80"]["metadata"]["tags"] == ("rr80",)


def test_ratified_freeze_deep_immutability(tmp_path):
    if not _REAL_V1.is_file():
        pytest.fail("実 v1 freeze が無い (trust root 不在 — skip すると攻撃 matrix が緑化する。failures F9 型)")
    root, *_ = build_valid_semantic_g1(tmp_path)
    freeze = M.load_ratified_freeze(root)
    with pytest.raises((TypeError, AttributeError)):
        freeze.document["schema_version"] = "mutated"       # top-level 再代入不可
    # ネストした list も tuple 化されている。
    assert isinstance(freeze.document["measurement_closure"], tuple)


def test_shallow_repo_rejected(tmp_path):
    root, *_ = _valid_g1(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    (root / ".git" / "shallow").write_text(head + "\n", encoding="utf-8")
    assert _git(root, "rev-parse", "--is-shallow-repository") == "true"
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "shallow-repo"


def test_namespace_dirty_rejected(tmp_path):
    root, gen_sha, gen_rel, *_ = _valid_g1(tmp_path)
    # namespace 内の tracked file を worktree で改変 (未 commit)。
    (root / gen_rel).write_bytes((root / gen_rel).read_bytes() + b"\n")
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "namespace-dirty"


def _has_hardening_pair(cmd) -> bool:
    """argv に `-c core.useReplaceRefs=false` の連続対が含まれるか。"""
    return any(
        cmd[i] == "-c" and cmd[i + 1] == "core.useReplaceRefs=false"
        for i in range(len(cmd) - 1)
    )


def test_git_hardening_reaches_argv(tmp_path, monkeypatch):
    # R7: _GIT_HARDEN の構造 pin + 実効検査。全 git 呼出しが
    # `-c core.useReplaceRefs=false` を前置し、replace refs による object 解決の
    # out-of-band 差替えを封じる。定数を空 tuple 化する変異はこのテストで殺せる。
    root = _base_repo(tmp_path)

    # 構造 pin: 定数そのものが hardening 対を持つ。
    assert M._GIT_HARDEN == ("-c", "core.useReplaceRefs=false")

    # 実効検査: subprocess.run を捕捉し、実 git 呼出しの argv に対が届いているか。
    real_run = M.subprocess.run
    captured: list = []

    def _spy(cmd, *args, **kwargs):
        captured.append(list(cmd))
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(M.subprocess, "run", _spy)
    M._capture_head(root)  # _git 経由で複数の git query を発行する

    git_calls = [cmd for cmd in captured if cmd and cmd[0] == "git"]
    assert git_calls, "git 呼出しが捕捉されていない"
    assert all(_has_hardening_pair(cmd) for cmd in git_calls), (
        "git 呼出しに core.useReplaceRefs=false hardening が欠けている: "
        f"{[cmd for cmd in git_calls if not _has_hardening_pair(cmd)]}"
    )


def test_replace_ref_rejected(tmp_path):
    # refs/replace/* は cat-file/rev-list を out-of-band に書換え履歴検証を無効化し得る。
    # 存在自体を fail-closed 拒否する (shallow と非対称にしない)。
    root, *_ = _valid_g1(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    _git(root, "replace", "--graft", head)  # refs/replace/<head> を生成
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "replace-refs"


def test_replace_ref_cannot_forge_history(tmp_path):
    # replace object で過去 commit の governance blob を別 bytes に差し替えても、
    # core.useReplaceRefs=false により object 解決は追従しない (検出が空振りしない)。
    # ここでは capture 段の replace 拒否より前に history 検証が効くことは要求せず、
    # 「replace が存在すれば必ず拒否に倒れる」ことを確認する (無効化されない)。
    root, gen_sha, gen_rel, approval_sha, ptr_sha = _valid_g1(tmp_path)
    # approval commit を別 blob へ replace-graft しても resolve は fail-closed のまま。
    approval_rel = f"{M.APPROVAL_DIR}/{gen_sha}.json"
    approval_commit = _git(root, "log", "-n", "1", "--format=%H", "--", approval_rel)
    _git(root, "replace", "--graft", approval_commit)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "replace-refs"


def test_grafts_file_rejected(tmp_path):
    # .git/info/grafts は rev-list の親関係を out-of-band に書換える。存在を fail-closed 拒否。
    root, *_ = _valid_g1(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    grafts = root / ".git" / "info" / "grafts"
    grafts.parent.mkdir(parents=True, exist_ok=True)
    grafts.write_text(head + "\n", encoding="utf-8")  # HEAD を root 化する graft
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.resolve_active_generation(root)
    assert ei.value.reason == "grafts"


def test_candidate_generation_not_loadable(tmp_path):
    # 未承認 candidate を load_ratified_freeze から取得できない (型分離)。
    root = _base_repo(tmp_path)
    _add_generation(root, 1, M.V1_FREEZE_SHA256)
    with pytest.raises(M.RatifiedFreezeError) as ei:
        M.load_ratified_freeze(root)
    assert ei.value.reason == "no-active"


def test_no_production_module_constructs_ratified_freeze_directly():
    # RatifiedFreeze( の直接構築は loader 内限定 (公開 API から昇格不能, C1-7)。
    campaign_dir = Path(_ORCH) / "campaign"
    offenders = []
    for path in sorted(campaign_dir.glob("*.py")):
        if path.name == "s8b_ratified_freeze.py":
            continue  # loader 自身は許可
        text = path.read_text(encoding="utf-8")
        if "RatifiedFreeze(" in text:
            offenders.append(path.name)
    assert not offenders, f"loader 外で RatifiedFreeze を直接構築: {offenders}"
