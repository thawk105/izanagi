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
import contextlib
import dataclasses
import datetime as dt
import hashlib
import json
import os
import random
import shlex
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from unittest import mock

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign import env_contract as ec  # noqa: E402
from orchestrator.campaign import campaign_claim, reservation  # noqa: E402
from orchestrator.campaign import env_attestation  # noqa: E402
from orchestrator.campaign import s8b_floor_campaign  # noqa: E402
from orchestrator.campaign import s8b_floor_stats  # noqa: E402
from orchestrator.campaign import s8b_materialization  # noqa: E402
from orchestrator.campaign import s8b_launch_cert  # noqa: E402
from orchestrator.campaign import s8b_prediction_runner  # noqa: E402
from orchestrator.campaign import s8b_selector_freeze  # noqa: E402
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_schema_v2 import _valid_document as _valid_calibration_v2_document  # noqa: E402


# --------------------------------------------------------------------------- #
# 合成 freeze fixture (rr79/rr23、実在 rr80/rr20 と判別可能な値)                #
# --------------------------------------------------------------------------- #

_CONFIGS = (
    "p2_2_flag_opt", "backoff_fixed_best", "sort_best",
    "system_gate", "ident_all", "stock_common",
)
_STOCK = "stock_common"
_HOLDOUT_SHAPE = {
    "rr79": {
        "records": 730079, "threads": 17,
        "ycsb": {"ycsb_zipf_skew": "0.42", "ycsb_rratio": "79", "ycsb_rmw": "1"},
    },
    "rr23": {
        "records": 230023, "threads": 11,
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

def _fixture_source_evidence(genome, ccbench_commit, *, ccbench_dir="", cxx="g++-13"):
    del cxx
    source_root = str(Path(ccbench_dir or "/fixture/ccbench").resolve())
    seed = f"{genome.canonical()}\0{source_root}".encode("utf-8")
    token = hashlib.sha256(seed).hexdigest()
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
def _synthetic_source_evidence_for_materializer_seams(monkeypatch, request):
    """Fake PreparedCell 用の source evidence。slow real-build controls は実 resolver を使う。"""
    if request.node.name.startswith("test_slow_real_"):
        return

    monkeypatch.setattr(
        s8b_floor_campaign.source_digest, "resolve_evidence", _fixture_source_evidence,
    )


def _holdout_entries(holdout_id: str) -> dict:
    entries = {}
    for i, cfg in enumerate(_CONFIGS):
        entries[cfg] = {
            "holdout_id": holdout_id,
            "label": f"fixture-{holdout_id}-{cfg}",
            "flags": {"BACK_OFF": i % 2, "NO_WAIT_LOCKING_IN_VALIDATION": (i + 1) % 2},
        }
    return entries


def _freeze_document() -> dict:
    holdouts = {}
    for holdout_id, shape in _HOLDOUT_SHAPE.items():
        holdouts[holdout_id] = {
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
        "freeze": {"path": "output/fixture_freeze.json", "sha256": freeze_sha},
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
def _fake_prepare(cell, ccbench_pin):
    entry = cell["variant"]
    holdout_id = entry["holdout_id"]
    configuration_id = cell["configuration"]
    cell_id = f"{holdout_id}::{configuration_id}"
    genome = Genome("silo", dict(entry.get("flags", {})))
    yield PreparedCell(
        genome=genome, src_token=cell_id,
        ccbench_dir="/fixture/ccbench", cache_root="/fixture/cache",
    )


def _make_fake_build(build_root: Path):
    def fake_build(genome, ccbench_commit, trace, cache_root="", cc=None, cxx=None,
                   jobs=16, ccbench_dir="", src_token=None, contract=None,
                   timeout_s=None, admission=None, build_context=None,
                   source_evidence=None):
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
        effective_ccbench = ccbench_dir or "/fixture/ccbench"
        # production と同じく渡された cache_root 配下に実体を置き、command には実 root を
        # 埋め込む（portable projection が未結線でも通る fake にしない）。
        cell_dir = Path(cache_root) / "fixture" / src_token.replace("::", "__")
        cell_dir.mkdir(parents=True, exist_ok=True)
        binary_path = cell_dir / "ycsb_fixture.exe"
        payload = f"fixture-binary::{src_token}".encode("utf-8")
        binary_path.write_bytes(payload)
        bin_sha256 = hashlib.sha256(payload).hexdigest()
        return SimpleNamespace(
            genome=genome, trace=trace, binary=str(binary_path),
            bin_sha256=bin_sha256, bin_hash=bin_sha256[:16],
            build_dir=str(cell_dir), cached=False,
            configure_cmd=f"# fixture configure {src_token}",
            build_cmd="# fixture build",
            configure_argv=["cmake", "-S", effective_ccbench, "-B", str(cell_dir)],
            build_argv=["cmake", "--build", str(cell_dir)],
            cache_root=str(cache_root), ccbench_root=effective_ccbench,
            contract_sha256=(contract.contract_sha256 if contract is not None else None),
        )
    return fake_build


def _durable_policy(out_root: Path):
    """tmp output を明示注入するテスト専用 allowlist (production 既定は repo output)。"""
    candidate = Path(out_root).absolute()
    approved = candidate
    while not approved.exists():
        approved = approved.parent
    return s8b_floor_campaign.DurableRootPolicy(
        approved_roots=(approved.resolve(),), forbidden_roots=(),
    )


def _cell_id_from_binary(binary: str) -> str:
    return Path(binary).parent.name.replace("__", "::")


def _run_campaign(protocol, freeze_doc, *, out_root, build_root, measure_fn, probe_fn,
                  mode="pilot", resume_dir=None, sleep_fn=None, monotonic_fn=None,
                  now_fn=None):
    fake_build = _make_fake_build(build_root)
    entrypoint = (s8b_floor_campaign._run_campaign_core
                  if mode == "official" else s8b_floor_campaign.run_campaign)
    extra = (
        {"_floor_preflight_fn": _fixture_floor_preflight}
        if mode == "official" and resume_dir is None else {}
    )
    kwargs = dict(
        out_root=out_root, mode=mode, resume_dir=resume_dir,
        measure_fn=measure_fn, probe_fn=probe_fn,
        sleep_fn=sleep_fn or (lambda s: None),
        monotonic_fn=monotonic_fn or (lambda: 0.0),
        prepare_fn=_fake_prepare, now_fn=now_fn or (lambda: _FIXED_NOW),
        durable_root_policy=_durable_policy(Path(out_root)),
        **extra,
    )
    if mode == "official":
        with mock.patch.object(
                s8b_floor_campaign, "_assert_official_permitted", lambda _mode: None), \
                mock.patch.object(s8b_floor_campaign.buildcache, "build_v2", fake_build):
            return entrypoint(protocol, freeze_doc, **kwargs)
    return entrypoint(protocol, freeze_doc, build_fn=fake_build, **kwargs)


def _fixture_floor_preflight(
        root, *, freeze_path, freeze_sha256, protocol_sha256):
    """prediction 順序以外を検査する private-core テスト用の引数注入 seam。"""
    return {s8b_floor_campaign._HOLDOUT_FREEZE_REL: freeze_sha256}


# --------------------------------------------------------------------------- #
# measure_fn の fake (決定的、reps 本の throughput を返す)                      #
# --------------------------------------------------------------------------- #

class _FakeScalePoint:
    def __init__(self, throughputs, notes, run_cmd):
        self.throughputs = list(throughputs)
        self.notes = list(notes)
        self.run_cmd = run_cmd


def _shape_faithful_run_cmd(
        binary, records, threads, workload, *, env_tag=ENV_TAG, extime_s=5) -> str:
    """production repro_command と同じ argv shape の runtime-path fake を返す。"""
    contract = ec.lookup(env_tag)
    argv = list(s8b_floor_campaign.build_portable_run_cmd(
        binary="output/fixture/bench", workload=workload, records=records,
        threads=threads, extime_s=extime_s, clocks_per_us=contract.clocks_per_us,
        numactl=contract.numactl,
    ))
    argv[argv.index("--") + 1] = str(binary)
    return shlex.join(argv)


def _make_measure_fn(reps, value_fn, *, raise_for=(), partial_for=(), partial_reps=None,
                     reps_fn=None, env_tag=ENV_TAG, extime_s=5):
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
                                       env_tag=env_tag, extime_s=extime_s))
        n = reps
        if cell_id in partial_for:
            n = partial_reps if partial_reps is not None else max(reps - 1, 0)
        base = value_fn(cell_id)
        return _FakeScalePoint(
            throughputs=[base] * n, notes=[],
            run_cmd=_shape_faithful_run_cmd(
                binary, records, threads, workload,
                env_tag=env_tag, extime_s=extime_s,
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
def _real_output_snapshot(output: Path = ROOT / "output") -> tuple:
    """統合テストが実 repo の output/ を一切変えないことを bytes まで固定する。

    旧実装との等価性は、安定しており、root と全 directory が読める通常 POSIX tree
    を定義域とする。
    """
    if not output.exists():
        return ()
    entries = _walk_entries(output)
    files = [(rel, abspath) for kind, rel, abspath in entries if kind == "file"]
    digest_by_rel = {}
    for rel, abspath in files:
        digest_by_rel[rel] = _digest(abspath)
    snapshot = []
    for kind, rel, abspath in entries:
        if kind == "symlink":
            snapshot.append(("symlink", rel, Path(abspath).readlink().as_posix()))
        elif kind == "file":
            snapshot.append(("file", rel, digest_by_rel[rel]))
        else:
            snapshot.append(("dir", rel))
    snapshot.sort(key=lambda row: row[1])
    return tuple(snapshot)


def _real_output_snapshot_reference(output: Path = ROOT / "output") -> tuple:
    """並列版の独立 oracle として保持する旧 ``Path.rglob`` 実装。"""
    if not output.exists():
        return ()
    snapshot = []
    for path in sorted(output.rglob("*"), key=lambda item: item.as_posix()):
        rel = path.relative_to(output).as_posix()
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


def _clone_committed_head_with_ccbench(destination: Path, *, ccbench_pin: str) -> Path:
    """ネットワークを使わず、committed HEAD と初期化済み submodule を複製する。"""
    subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(destination)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    source_submodule = ROOT / "external" / "ccbench"
    assert source_submodule.is_dir()
    assert _git_stdout(source_submodule, "rev-parse", "HEAD").strip() == ccbench_pin
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
    return destination


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
    def prepare(cell, observed_ccbench_pin):
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
        yield PreparedCell(
            genome=Genome("silo", dict(entry.get("flags", {}))),
            src_token=cell_id,
            ccbench_dir=str(ccbench_dir),
            cache_root=str(cache_root),
        )

    prepare.calls = calls
    return prepare


def _install_real_seal_reservation(monkeypatch) -> dict[str, str]:
    requested_s = 100_000
    started = time.time() - 1.0
    values = {
        "IZANAGI_RESERVATION_JOB_ID": "real-seal-fixture-job",
        "IZANAGI_RESERVATION_REQUESTED_S": str(requested_s),
        "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": str(started),
        "IZANAGI_RESERVATION_DEADLINE_EPOCH": str(started + requested_s),
        "IZANAGI_RESERVATION_HOST": "real-seal-fixture-host",
        "IZANAGI_RESERVATION_BOOT_ID": Path(
            "/proc/sys/kernel/random/boot_id"
        ).read_text(encoding="ascii").strip(),
        "IZANAGI_RESERVATION_SCRIPT_SHA256": "7" * 64,
        "IZANAGI_RESERVATION_NONCE": "real-seal-fixture-nonce",
        "PBS_JOBID": "real-seal-fixture-job",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return values


def _observed(profile):
    raw = env_attestation.profile_to_dict(profile)
    del raw["effective_clock"]["tolerance_pct"]
    return env_attestation.normalize_observed_profile(raw)


def _install_required_contract(tmp_path: Path, monkeypatch):
    """production calibration/v2 reader + issuer を通す required env fixture。"""
    repo_root = tmp_path / "required-repo"
    repo_root.mkdir()
    document = _valid_calibration_v2_document()
    # U-2/U-3 による current admission の正当な縮小: required fixture は policy と一致させる。
    document["attestation_profile"]["effective_clock"]["tolerance_pct"] = 2.0
    raw = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    (repo_root / "calibration.json").write_bytes(raw)
    contract = ec.ExecutionEnvironmentContract(
        env_tag=document["env_tag"], clocks_per_us=document["clocks_per_us"],
        numactl=ec.lookup(ENV_TAG).numactl, attestation_mode="required",
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=False),
        calibration_ref=ec.CalibrationRef(
            path="calibration.json", sha256=hashlib.sha256(raw).hexdigest(),
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
        "IZANAGI_RESERVATION_HOST": "fixture-host",
        "IZANAGI_RESERVATION_BOOT_ID": boot_id,
        "IZANAGI_RESERVATION_SCRIPT_SHA256": "d" * 64,
        "IZANAGI_RESERVATION_NONCE": "fixture-nonce",
        "PBS_JOBID": "fixture-job",
    }
    for key, value in binding_values.items():
        monkeypatch.setenv(key, value)
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
    }


def _provision_claim_root(ctx) -> Path:
    root = ctx["out_root"] / "claims"
    root.mkdir(parents=True, mode=0o700)
    return root


@contextlib.contextmanager
def _official_test_seam(monkeypatch, *, clean_digest="d" * 64):
    """production official 拒否を局所 scope だけで外し、clean scan を tmp-only test stub にする。"""
    with monkeypatch.context() as scoped:
        scoped.setattr(s8b_floor_campaign, "_assert_official_permitted", lambda mode: None)
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
    contract = ec.lookup(protocol["env_tag"])
    calibration_path = repo_root / contract.calibration_ref.path
    calibration_path.parent.mkdir(parents=True, exist_ok=True)
    calibration_path.write_bytes((ROOT / contract.calibration_ref.path).read_bytes())
    subprocess.run(
        ["git", "-C", str(repo_root), "add", "positive-control.txt",
         protocol["freeze"]["path"], s8b_floor_campaign._HOLDOUT_FREEZE_REL,
         contract.calibration_ref.path,
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
    def rooted_prepare(cell, ccbench_pin):
        entry = cell["variant"]
        holdout_id = entry["holdout_id"]
        configuration_id = cell["configuration"]
        cell_id = f"{holdout_id}::{configuration_id}"
        genome = Genome("silo", dict(entry.get("flags", {})))
        yield PreparedCell(
            genome=genome, src_token=cell_id,
            ccbench_dir=str(base / "prepared trees Ω" / cell_id.replace("::", "__")),
            cache_root=str(base / "prepared-cache"),
        )

    with mock.patch.object(
            s8b_floor_campaign, "_assert_official_permitted", lambda _mode: None), \
            mock.patch.object(s8b_floor_campaign.buildcache, "build_v2", fake_build), \
            mock.patch.object(
                s8b_floor_campaign.source_digest, "resolve_evidence",
                _fixture_source_evidence,
            ):
        outcome = s8b_floor_campaign._run_campaign_core(
            protocol, verified, out_root=out_root, mode="official",
            measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
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


def test_load_resume_manifest_rejects_v1_schema(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({
        "schema_version": "s8b-floor-manifest/v1", "protocol_sha256": "x",
        "freeze_sha256": "y", "binaries": {},
    }), encoding="utf-8")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="schema_version"):
        s8b_floor_campaign._load_resume_manifest(
            path, protocol_sha256="x", freeze_sha256="y", out_root=tmp_path)


# =========================================================================== #
# 3. official mode は常に拒否 (§8 未裁定) — CLI + core 直接 (δ-3)               #
# =========================================================================== #

@pytest.mark.parametrize("mode", ["pilot", "official"])
def test_validate_mode_accepts_only_known_modes(mode):
    assert s8b_floor_campaign._validate_mode(mode) == mode


@pytest.mark.parametrize("mode", ["", "PILOT", "pilot/../../escape", None, 1])
def test_validate_mode_rejects_unknown_and_path_traversal(mode, tmp_path):
    out_root = tmp_path / "out"
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="mode"):
        s8b_floor_campaign.run_campaign(
            None, None, out_root=out_root, mode=mode,
        )
    assert not out_root.exists()


def test_main_official_mode_always_refused(tmp_path, capsys):
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text("{}", encoding="utf-8")
    rc = s8b_floor_campaign.main(["--mode", "official", "--protocol", str(protocol_path)])
    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "refused"
    assert "§8" in payload["reason"]


def test_run_campaign_core_rejects_official_materializer_injection_before_side_effects(
        tmp_path):
    """wrapper を通らない core 直呼びでも任意 materializer は official に入れない。"""
    out_root = tmp_path / "out"
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="materializer"):
        s8b_floor_campaign._run_campaign_core(
            None, None, out_root=out_root, mode="official",
            build_fn=lambda *_args, **_kwargs: None,
        )
    assert not out_root.exists()


def test_run_campaign_core_rejects_official_with_zero_side_effects(tmp_path):
    """production wrapper は default official も従来どおり拒否し副作用 0。"""
    freeze = _freeze_document()
    out_root = tmp_path / "out"

    def forbid_build(*a, **k):
        raise AssertionError("official 拒否より前に build してはいけない")

    with mock.patch.object(s8b_floor_campaign.buildcache, "build", forbid_build):
        with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="official"):
            s8b_floor_campaign.run_campaign(
                _protocol(freeze_sha=_freeze_sha(freeze)), _verified_freeze(freeze),
                out_root=out_root, mode="official",
            )
    assert not out_root.exists()  # 書き込み 0 回


def test_materializer_registry_covers_all_python_build_launches():
    """Direct CMake は deny registry、buildcache caller は U1/U2 gateway 引数を必須化する。"""
    campaign_root = ROOT / "orchestrator/campaign"
    direct_cmake: set[str] = set()
    missing_admission: list[str] = []
    seen_gateways: set[str] = set()
    admitted_gateways = {
        "orchestrator/campaign/pipeline.py:evaluate",
        "orchestrator/campaign/s8b_floor_campaign.py:build_cells",
    }

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
                    isinstance(key, ast.Constant) and isinstance(key.value, str)
                    for key in keys):
                names.update(key.value for key in keys)
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
            is_buildcache_call = (
                qualified.endswith("buildcache.build")
                or qualified.endswith("buildcache.build_v2")
            )
            is_floor_materializer_call = (
                qualified == "build_fn"
                and site == "orchestrator/campaign/s8b_floor_campaign.py:build_cells"
            )
            if not is_buildcache_call and not is_floor_materializer_call:
                continue
            required = {"admission", "build_context", "source_evidence"}
            if site in admitted_gateways:
                seen_gateways.add(site)
                if is_floor_materializer_call:
                    keywords = static_keyword_names(call, owner)
                    if not required <= keywords:
                        missing_admission.append(
                            f"{relative}:{call.lineno}:{qualified}"
                        )
                elif site.endswith(":evaluate"):
                    function_strings = {
                        node.value for node in ast.walk(owner)
                        if isinstance(node, ast.Constant) and isinstance(node.value, str)
                    }
                    if not required <= function_strings:
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
    ("after_certificate_issued_fn", lambda _path: None),
    ("durable_root_policy", s8b_floor_campaign.DurableRootPolicy(
        approved_roots=(ROOT.resolve(),), forbidden_roots=())),
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


def test_run_campaign_machine_pin_rejects_contract_tag_mismatch(tmp_path):
    """契約の env_tag が実行機の p2_2.ENV_TAG と一致しなければ拒否する (暫定 machine-pin)。"""
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


def test_required_binding_missing_rejected_by_production_entry_without_side_effects(
        tmp_path, monkeypatch):
    ctx = _install_required_contract(tmp_path, monkeypatch)
    for key in list(ctx["binding_values"]):
        monkeypatch.delenv(key, raising=False)
    out_root = ctx["out_root"]
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="reservation preflight"):
        s8b_floor_campaign.run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=out_root, mode="pilot", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, repo_root=ctx["repo_root"],
            build_fn=_make_fake_build(tmp_path / "bin"),
            durable_root_policy=_durable_policy(out_root),
        )
    assert not out_root.exists()


def test_required_v1_receipt_mode_mismatch_rejected_without_side_effects(
        tmp_path, monkeypatch):
    ctx = _install_required_contract(tmp_path, monkeypatch)

    def v1_issuer(contract, _verified, *, now_fn):
        return _fixed_receipt(contract, now_fn=now_fn)

    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="attestation_mode"):
        s8b_floor_campaign.run_campaign(
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
        s8b_floor_campaign.run_campaign(
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
        s8b_floor_campaign.run_campaign(
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
        campaign_identity=identity, job_id="existing-job", host="existing-host",
        boot_id="existing-boot", pid=999, proc_starttime=123,
        created_utc=_FIXED_NOW.isoformat(),
    )
    campaign_claim.acquire_claim(claim_root, existing)
    before = _tree_snapshot(ctx["out_root"])
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="existing-job"):
        s8b_floor_campaign.run_campaign(
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
        s8b_floor_campaign.run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot", measure_fn=_forbid_measure,
            probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, repo_root=ctx["repo_root"],
            build_fn=_make_fake_build(tmp_path / "bin"),
            durable_root_policy=_durable_policy(ctx["out_root"]),
        )
    assert not ctx["out_root"].exists()


def test_required_reservation_loss_is_typed_campaign_terminal_with_no_values(
        tmp_path, monkeypatch):
    ctx = _install_required_contract(tmp_path, monkeypatch)
    _provision_claim_root(ctx)
    ticks = iter((0.0, 200_000.0))
    monotonic_fn = lambda: next(ticks)
    measure = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    with pytest.raises(reservation.ReservationError, match="残時間が不足"):
        s8b_floor_campaign.run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot", measure_fn=measure,
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
        tmp_path, monkeypatch):
    ctx = _install_required_contract(tmp_path, monkeypatch)
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
        s8b_floor_campaign.run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot",
            measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
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
        tmp_path, monkeypatch):
    ctx = _install_required_contract(tmp_path, monkeypatch)
    claim_root = _provision_claim_root(ctx)
    measure = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])

    outcome = s8b_floor_campaign.run_campaign(
        ctx["protocol"], _verified_freeze(ctx["freeze"]),
        out_root=ctx["out_root"], mode="pilot", measure_fn=measure,
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
        "required_s": 28200,
        "safety_margin_s": 600,
        "formula": s8b_floor_campaign._FLOOR_RESERVATION_FORMULA,
        "build_cap_per_cell_s": 900,
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
    assert set(json.loads(claims[0].read_text(encoding="utf-8"))) == {
        "campaign_identity", "job_id", "host", "boot_id", "pid",
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
        s8b_floor_campaign.run_campaign(
            ctx["protocol"], _verified_freeze(ctx["freeze"]),
            out_root=ctx["out_root"], mode="pilot", measure_fn=_forbid_measure,
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
        seen["clocks_per_us"] = clocks_per_us
        seen["numactl"] = kw.get("numactl")
        return _FakeScalePoint(
            throughputs=[1000.0] * 5, notes=[],
            run_cmd=_shape_faithful_run_cmd(binary, records, threads, kw["workload"]),
        )

    fake_build = _make_fake_build(tmp_path / "bin")
    with mock.patch.object(s8b_floor_campaign.buildcache, "build_v2", fake_build), \
             mock.patch.object(s8b_floor_campaign, "measure_point", spy_measure_point):
        s8b_floor_campaign.run_campaign(
            protocol, _verified_freeze(freeze), out_root=tmp_path / "out", mode="pilot",
            measure_fn=None, probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, monotonic_fn=lambda: 0.0,
            durable_root_policy=_durable_policy(tmp_path / "out"),
        )
    assert seen["clocks_per_us"] == contract.clocks_per_us
    assert seen["numactl"] == list(contract.numactl)


def test_floor_default_durable_policy_rejects_external_output_without_side_effects(tmp_path):
    freeze = _freeze_document()
    out_root = tmp_path / "outside-default-approval"
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="durable output root"):
        s8b_floor_campaign.run_campaign(
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
        child.wait(timeout=5)
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
            original = s8b_floor_campaign.s8b_floor_stats.verify_floor_artifact

            def crash_after_self_check(*args, **kwargs):
                problems = original(*args, **kwargs)
                assert problems == []
                raise _SimulatedCrash(crash_point)

            scoped.setattr(
                s8b_floor_campaign.s8b_floor_stats, "verify_floor_artifact",
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
    assert s8b_floor_stats.verify_floor_artifact(result, expected_protocol) == []

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
    assert s8b_floor_stats.verify_floor_artifact(tampered, expected_protocol)


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
    outcome = s8b_floor_campaign.run_campaign(
        protocol, _verified_freeze(freeze), out_root=out_root, mode="pilot",
        measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
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
    expected = s8b_floor_campaign.clean_scan_digest(
        repo_root, freeze_allowlist=bounded_allowlist,
    )
    fake_build = _make_fake_build(tmp_path / "ignored")
    with mock.patch.object(
            s8b_floor_campaign, "_assert_official_permitted", lambda _mode: None), \
            mock.patch.object(s8b_floor_campaign.buildcache, "build_v2", fake_build):
        outcome = s8b_floor_campaign._run_campaign_core(
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

    clone_root = _clone_committed_head_with_ccbench(
        tmp_path / "committed-head", ccbench_pin=ccbench_pin,
    )
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
    assert _git_stdout(clone_root, "rev-parse", "HEAD").strip() == source_head
    assert _git_stdout(clone_root, "rev-parse", "--is-shallow-repository").strip() == "false"
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", seal_commit, "HEAD"],
        cwd=clone_root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert _git_stdout(clone_root, "rev-parse", f"{seal_commit}^").strip() == pre_oracle_head
    gitlink_fields = _git_stdout(
        clone_root, "ls-tree", "HEAD", "external/ccbench",
    ).split()
    assert gitlink_fields[:3] == ["160000", "commit", ccbench_pin]
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
    reservation_values = _install_real_seal_reservation(monkeypatch)

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
    self_check_original = s8b_floor_stats.verify_floor_artifact
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
    monkeypatch.setattr(s8b_floor_stats, "verify_floor_artifact", self_check_spy)

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
    monkeypatch.setattr(s8b_floor_campaign, "_assert_official_permitted", lambda _mode: None)
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
    assert result["eligible_for_refreeze"] is True
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
    assert reservation_start["required_s"] == 28_200
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
        spec = importlib.util.spec_from_file_location("floor_test_helper", {str(Path(__file__))!r})
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(json.dumps(module._deterministic_official_artifacts(pathlib.Path(sys.argv[1])), sort_keys=True))
    """)
    observations = []
    for root, delta in zip(roots, environments):
        temp_dir = root / "process-tmp"
        temp_dir.mkdir(parents=True)
        env = dict(os.environ)
        env.update(delta)
        env["TMPDIR"] = str(temp_dir)
        completed = subprocess.run(
            [sys.executable, "-c", script, str(root)], env=env,
            capture_output=True, text=True, check=True,
        )
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
        assert set(record) == set(s8b_floor_campaign._PORTABLE_BUILT_KEYS), cell_id
        assert not Path(record["binary"]).is_absolute()
        assert not Path(record["store_path"]).is_absolute()
        assert any("${OUT_ROOT}" in token for token in record["configure_argv"])
        assert any("${CCBENCH_ROOT}" in token for token in record["configure_argv"])
        assert "configure_cmd" not in record and "build_cmd" not in record
    assert result["eligible_for_refreeze"] is True


def test_new_seam_defaults_delegate_to_production_functions(tmp_path, monkeypatch):
    freeze = _freeze_document()
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    repo_root = tmp_path / "default-root"
    _init_real_clean_repo(repo_root, freeze, protocol)
    calls = {name: 0 for name in (
        "calibration", "machine_pin", "host", "process", "receipt", "build", "after",
    )}
    fake_build = _make_fake_build(tmp_path / "ignored")
    real_load = s8b_floor_campaign.env_attestation.load_verified_calibration
    real_pin = s8b_floor_campaign.execution_guard.assert_machine_pin

    def calibration_spy(contract, root):
        calls["calibration"] += 1
        assert contract.attestation_mode == "none"
        return real_load(contract, root)

    def machine_pin_spy(contract, *, machine_env_tag):
        calls["machine_pin"] += 1
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
    with mock.patch.object(
            s8b_floor_campaign, "_assert_official_permitted", lambda _mode: None):
        outcome = s8b_floor_campaign._run_campaign_core(
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


def test_portable_projection_rejects_reserved_placeholder_and_exact_key_tamper(tmp_path):
    binary = tmp_path / "out" / "cache" / "binary.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"binary")
    sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    runtime = {
        "cell": {
            "cell_id": "cell", "holdout_id": "h", "configuration_id": "c",
            "binary": str(binary), "binary_sha256": sha, "bin_hash_short": sha[:16],
            "binding": {}, "configure_argv": ["cmake", "${OUT_ROOT}"],
            "build_argv": ["cmake", "--build", str(binary.parent)],
            "cached": False, "store_path": str(tmp_path / "out" / "store" / sha),
            "_ccbench_root": str(tmp_path / "ccbench"),
        },
    }
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="予約 placeholder"):
        s8b_floor_campaign.project_built_records(runtime, out_root=tmp_path / "out")

    runtime["cell"]["configure_argv"] = ["cmake", "-S", str(tmp_path / "ccbench")]
    portable = s8b_floor_campaign.project_built_records(
        runtime, out_root=tmp_path / "out")
    portable["cell"].pop("cached")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="exact key"):
        s8b_floor_campaign.resolve_portable_built(
            portable, out_root=tmp_path / "out")


def _valid_portable_built_record() -> dict:
    sha = "a" * 64
    return {
        "cell": {
            "cell_id": "cell", "holdout_id": "holdout",
            "configuration_id": "configuration", "binary": "cache/cell/binary.exe",
            "binary_sha256": sha, "bin_hash_short": sha[:16], "binding": {},
            "configure_argv": ["cmake", "-S", "${CCBENCH_ROOT}"],
            "build_argv": ["cmake", "--build", "${OUT_ROOT}/cache/cell"],
            "cached": False, "store_path": f"store/{sha}",
        },
    }


@pytest.mark.parametrize(("path", "reason"), [
    ("a/../b", "portable built binary path component が不正"),
    ("a//b", "portable built binary path 文法が不正"),
    ("/abs", "portable built binary path 文法が不正"),
])
@pytest.mark.parametrize("entrypoint", ["validate", "resolve"])
def test_portable_built_rejects_path_traversal_and_noncanonical_paths(
        tmp_path, path, reason, entrypoint):
    built = _valid_portable_built_record()
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
def test_portable_built_rejects_wrong_scalar_and_mapping_types(field, value, reason):
    built = _valid_portable_built_record()
    built["cell"][field] = value
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match=reason):
        s8b_floor_campaign._validate_portable_built(built)


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
    with mock.patch.object(
            s8b_floor_campaign, "_assert_official_permitted", lambda _mode: None):
        with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="clean_scan_digest"):
            s8b_floor_campaign._run_campaign_core(
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
    assert outcome["result"]["eligible_for_refreeze"] is True
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
            s8b_floor_campaign._run_campaign_core(
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
            s8b_floor_campaign._run_campaign_core(
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
        scoped.setattr(s8b_floor_campaign, "_assert_official_permitted", lambda mode: None)

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
            )
    journals = list(out_root.rglob("journal.jsonl"))
    assert len(journals) == 1
    journal = _read_journal_lines(journals[0])
    assert [record["event"] for record in journal] == ["launch-start"]
    assert (journals[0].parent / "launch_certificate.json").is_file()
    assert not (journals[0].parent / "manifest.json").exists()
    # 厳密 L を同じ cert/run の下で build から再構築する。
    resume_measure = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(
        _protocol(freeze_sha=_freeze_sha(freeze)), _verified_freeze(freeze),
        out_root=out_root, build_root=tmp_path / "bin",
        measure_fn=resume_measure, probe_fn=lambda: (1, "", ""), mode="official",
        resume_dir=journals[0].parent,
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
            )
    run_dir = _only_run_dir(out_root)
    assert [r["event"] for r in _read_journal_lines(run_dir / "journal.jsonl")] == [
        "launch-start"]
    outcome = _run_campaign(
        protocol, _verified_freeze(freeze), out_root=out_root,
        build_root=tmp_path / "bin",
        measure_fn=_make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid]),
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
    protocol_path = tmp_path / "protocol.json"

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
        s8b_floor_campaign.run_campaign(
            protocol, _verified_freeze(freeze), out_root=out_root, mode="pilot",
            measure_fn=measure_fn,
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

    outcome = s8b_floor_campaign.run_campaign(
        protocol, verified, out_root=tmp_path / "out", mode="pilot",
        measure_fn=measure_fn, probe_fn=lambda: (1, "", ""),
        sleep_fn=lambda _seconds: None, monotonic_fn=lambda: 0.0,
        prepare_fn=_fake_prepare, now_fn=lambda: _FIXED_NOW,
        execution_receipt_fn=receipt_spy, build_fn=build_spy,
        durable_root_policy=_durable_policy(tmp_path / "out"),
    )

    assert outcome["status"] == "completed"
    current_lookup.assert_called_once_with(ENV_TAG)
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
    assert journal[0]["event"] == "campaign-start"
    assert "launch_certificate_sha256" not in journal[0]
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
        measure_fn=lambda *a: _FakeScalePoint([1.0] * 5, [], "x"),
        probe_fn=lambda: (1, "", ""), sleep_fn=lambda s: None,
        monotonic_fn=lambda: 0.0, now_fn=lambda: _FIXED_NOW,
        protocol_sha256="p", freeze_sha256="f", manifest_sha256="m",
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
    s8b_floor_campaign.store_binaries(built, store_root, out_root=out_root)  # 例外なし


def test_verify_floor_artifact_binaries_positive_and_negative():
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        outcome = _run_campaign(protocol, verified, out_root=Path(td) / "out",
                                build_root=Path(td) / "bin", measure_fn=measure_fn,
                                probe_fn=lambda: (1, "", ""))
    result = outcome["result"]
    expected_protocol = s8b_floor_campaign._expected_protocol(
        s8b_floor_campaign.validate_protocol(protocol),
        s8b_floor_campaign.enumerate_cells(freeze, stock_configuration=_STOCK),
    )
    # 正例: binaries 整合 + journal receipt (expected_binaries) 突合が空リスト。
    expected_binaries = {cid: rec["binary_sha256"]
                         for cid, rec in result["binaries"].items()}
    assert s8b_floor_stats.verify_floor_artifact(
        result, expected_protocol, expected_binaries) == []

    # 負例1: bin_hash_short を binary_sha256[:16] と食い違わせる。
    tampered = json.loads(json.dumps(result))
    any_cid = next(iter(tampered["binaries"]))
    tampered["binaries"][any_cid]["bin_hash_short"] = "deadbeefdeadbeef"
    assert s8b_floor_stats.verify_floor_artifact(tampered, expected_protocol)

    # 負例2: journal receipt (expected_binaries) と binary_sha256 が不一致。
    bad_receipts = dict(expected_binaries)
    bad_receipts[any_cid] = "f" * 64
    assert s8b_floor_stats.verify_floor_artifact(result, expected_protocol, bad_receipts)

    # 負例3: binaries からセルを欠落させる (完全集合が崩れる)。
    dropped = json.loads(json.dumps(result))
    dropped["binaries"].pop(any_cid)
    assert s8b_floor_stats.verify_floor_artifact(dropped, expected_protocol)


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
