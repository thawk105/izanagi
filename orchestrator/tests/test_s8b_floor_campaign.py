# -*- coding: utf-8 -*-
"""s8b floor campaign driver (``campaign.s8b_floor_campaign``) の契約テスト (formula v2)。

ccbench submodule はこのマシンに無いため、実ビルド・実 bench は一切呼ばない。
``prepare_fn``/``buildcache.build``/``measure_fn``/``probe_fn``/``sleep_fn``/
``monotonic_fn``/``now_fn`` を全て注入し、合成 freeze fixture (holdout rr79/rr23 × 6 構成、
stock_common 含む) で全経路を回す。rr79/rr23 は実在 freeze の rr80/rr20 と records/threads/
workload を意図的に変え、「freeze から来た値」であることをテスト内で判別できるようにしてある
(δ-15: 新規テストは synthetic 軸のみ。holdout 実軸 literal を新規に書かない)。

floor の式そのものの mutation-killing テストは ``test_s8b_floor_stats.py`` が正本。本ファイルは
driver 側の配線 (schedule 決定性・golden + 意図 mutant / protocol 承認凍結値 pin + 版交差拒否 /
official core 拒否 / session 有効性→retry→floor 伝播 / probe 臨界区間 + post-probe finally /
performance_anomaly / machine_anomaly / create-only + 冪等 finalization / resume 状態機械 +
manifest.schedule 権威 + attempt registry / env contract 結線 / duration 台帳) を固定する。
"""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import random
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
sys.path.insert(0, str(ORCHESTRATOR))

from campaign import env_contract as ec  # noqa: E402
from campaign import s8b_floor_campaign  # noqa: E402
from campaign import s8b_floor_stats  # noqa: E402
from campaign import s8b_launch_cert  # noqa: E402
from campaign.model import Genome  # noqa: E402
from campaign.p2_2 import ENV_TAG  # noqa: E402
from campaign.s1_direct_comparison import PreparedCell  # noqa: E402
from campaign.s8b_freeze_io import VerifiedFreeze  # noqa: E402


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
        "freeze": {"path": "output/s8b-freeze/fixture_freeze.json", "sha256": freeze_sha},
        "stock_configuration": _STOCK,
        "n_sessions": n_sessions,
        "reps": reps,
        "master_seed": master_seed,
        "schedule_algorithm": (schedule_algorithm if schedule_algorithm is not None
                               else s8b_floor_campaign.SCHEDULE_ALGORITHM),
        "extime_s": 3,
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
                   jobs=16, ccbench_dir="", src_token=None):
        assert trace is False, "floor 計測は trace-disabled build (規律1)"
        cell_dir = build_root / src_token.replace("::", "__")
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
        )
    return fake_build


def _cell_id_from_binary(binary: str) -> str:
    return Path(binary).parent.name.replace("__", "::")


def _run_campaign(protocol, freeze_doc, *, out_root, build_root, measure_fn, probe_fn,
                  mode="pilot", resume_dir=None, sleep_fn=None, monotonic_fn=None,
                  now_fn=None):
    fake_build = _make_fake_build(build_root)
    with mock.patch.object(s8b_floor_campaign.buildcache, "build", fake_build):
        return s8b_floor_campaign.run_campaign(
            protocol, freeze_doc, out_root=out_root, mode=mode, resume_dir=resume_dir,
            measure_fn=measure_fn, probe_fn=probe_fn,
            sleep_fn=sleep_fn or (lambda s: None),
            monotonic_fn=monotonic_fn or (lambda: 0.0),
            prepare_fn=_fake_prepare, now_fn=now_fn or (lambda: _FIXED_NOW),
        )


# --------------------------------------------------------------------------- #
# measure_fn の fake (決定的、reps 本の throughput を返す)                      #
# --------------------------------------------------------------------------- #

class _FakeScalePoint:
    def __init__(self, throughputs, notes, run_cmd):
        self.throughputs = list(throughputs)
        self.notes = list(notes)
        self.run_cmd = run_cmd


def _make_measure_fn(reps, value_fn, *, raise_for=(), partial_for=(), partial_reps=None,
                     reps_fn=None):
    raise_for = set(raise_for)
    partial_for = set(partial_for)
    calls: list = []

    def measure_fn(binary, records, threads, workload):
        cell_id = _cell_id_from_binary(binary)
        calls.append(cell_id)
        if cell_id in raise_for:
            raise RuntimeError(f"fixture: 実行不能を模す ({cell_id})")
        if reps_fn is not None:
            values = reps_fn(cell_id)
            return _FakeScalePoint(throughputs=list(values), notes=[],
                                   run_cmd=f"./fixture {cell_id}")
        n = reps
        if cell_id in partial_for:
            n = partial_reps if partial_reps is not None else max(reps - 1, 0)
        base = value_fn(cell_id)
        return _FakeScalePoint(
            throughputs=[base] * n, notes=[], run_cmd=f"./fixture {cell_id}",
        )

    measure_fn.calls = calls
    return measure_fn


def _only_run_dir(out_root: Path) -> Path:
    manifests = list(out_root.rglob("manifest.json"))
    assert len(manifests) == 1, manifests
    return manifests[0].parent


def _read_journal_lines(journal_path: Path) -> list:
    return [json.loads(line) for line in journal_path.read_text(encoding="utf-8")
           .splitlines() if line.strip()]


def _real_output_snapshot() -> tuple:
    """統合テストが実 repo の output/ を一切変えないことを bytes まで固定する。"""
    output = ROOT / "output"
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


def _ref_round_perm(round_no: int) -> list:
    """spec を独立実装: hex → 先頭 8 byte big-endian → Random.shuffle。"""
    digest_hex = _GOLDEN_ROUND_SHA256[round_no]
    seed = int.from_bytes(bytes.fromhex(digest_hex)[:8], "big")
    perm = list(_GOLDEN_SORTED)
    random.Random(seed).shuffle(perm)
    return perm


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
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="duplicate key"):
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
        s8b_floor_campaign._load_resume_manifest(path, protocol_sha256="x", freeze_sha256="y")


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


def test_run_campaign_core_rejects_official_with_zero_side_effects(tmp_path):
    """core run_campaign 自体が official を無条件拒否し build/measure/write を 0 回にする (δ-3)。"""
    freeze = _freeze_document()
    out_root = tmp_path / "out"

    def forbid_build(*a, **k):
        raise AssertionError("official 拒否より前に build してはいけない")

    with mock.patch.object(s8b_floor_campaign.buildcache, "build", forbid_build):
        with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="official"):
            s8b_floor_campaign.run_campaign(
                _protocol(freeze_sha=_freeze_sha(freeze)), _verified_freeze(freeze),
                out_root=out_root, mode="official",
                measure_fn=_forbid_measure, probe_fn=lambda: (1, "", ""),
                prepare_fn=_fake_prepare, now_fn=lambda: _FIXED_NOW,
            )
    assert not out_root.exists()  # 書き込み 0 回


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
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=True),
        calibration_ref=ec.CalibrationRef(path="output/x.json", sha256="0" * 64),
    )
    # validate_protocol の contract_sha256 cross-field 検査を通すため mocked contract の
    # fingerprint を焼く (rejection は後段の machine-pin で起きることを固定する)。
    protocol = _protocol(freeze_sha=_freeze_sha(freeze), env_tag="foreign-env",
                         contract_sha256=fake_contract.contract_sha256)
    with mock.patch.object(s8b_floor_campaign._env_contract, "lookup",
                           return_value=fake_contract):
        with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="machine-pin"):
            _run_campaign(protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
                          build_root=tmp_path / "bin", measure_fn=_forbid_measure,
                          probe_fn=lambda: (1, "", ""))


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
        return _FakeScalePoint(throughputs=[1000.0] * 5, notes=[], run_cmd="./x")

    fake_build = _make_fake_build(tmp_path / "bin")
    with mock.patch.object(s8b_floor_campaign.buildcache, "build", fake_build), \
         mock.patch.object(s8b_floor_campaign, "measure_point", spy_measure_point):
        s8b_floor_campaign.run_campaign(
            protocol, _verified_freeze(freeze), out_root=tmp_path / "out", mode="pilot",
            measure_fn=None, probe_fn=lambda: (1, "", ""), prepare_fn=_fake_prepare,
            now_fn=lambda: _FIXED_NOW, monotonic_fn=lambda: 0.0,
        )
    assert seen["clocks_per_us"] == contract.clocks_per_us
    assert seen["numactl"] == list(contract.numactl)


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


def test_idempotent_finalization_after_result_json_crash(tmp_path):
    """result.json 作成後・md/terminal 前で crash した状態を模し、resume が既存 result.json を
    hash 検証 + 欠落 md/terminal のみ補完することを固定する (β-11)。"""
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze))
    out_root = tmp_path / "out"
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                            measure_fn=measure_fn, probe_fn=lambda: (1, "", ""))
    run_dir = Path(outcome["run_dir"])
    original_result = (run_dir / "result.json").read_bytes()

    # crash 状態を再現: result.md を消し、journal から terminal completed 行を除去する。
    (run_dir / "result.md").unlink()
    journal_path = run_dir / "journal.jsonl"
    kept = [ln for ln in journal_path.read_text(encoding="utf-8").splitlines()
            if ln.strip() and json.loads(ln).get("event") != "terminal"]
    journal_path.write_text("\n".join(kept) + "\n", encoding="utf-8")

    # resume: 既存 result.json はそのまま (hash 一致で skip)、md/terminal を補完。
    measure_fn2 = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid])
    outcome2 = _run_campaign(protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                             resume_dir=run_dir, measure_fn=measure_fn2,
                             probe_fn=lambda: (1, "", ""))
    assert outcome2["status"] == "completed"
    assert measure_fn2.calls == []  # 全 session 済みなので新規計測なし
    assert (run_dir / "result.json").read_bytes() == original_result  # 上書きされない
    assert (run_dir / "result.md").exists()  # 欠落 md が補完された
    journal = _read_journal_lines(journal_path)
    assert any(r.get("event") == "terminal" and r.get("status") == "completed" for r in journal)


# =========================================================================== #
# 9. resume: forward-only + hash pin + manifest.schedule 権威 + 状態機械         #
# =========================================================================== #

class _SimulatedCrash(Exception):
    """resume テスト専用: 実クラッシュ (measure_fn を包む except に捕まらない例外) を模す。"""


def _crash_at(n_crash: int):
    call_count = {"n": 0}

    def measure_fn(binary, records, threads, workload):
        call_count["n"] += 1
        if call_count["n"] == n_crash:
            raise _SimulatedCrash("fixture: session 実行中に死ぬ")
        cell_id = _cell_id_from_binary(binary)
        return _FakeScalePoint(throughputs=[_BASE_TPS[cell_id]] * 5, notes=[], run_cmd="./x")
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
    binary_path = Path(binaries[tampered_cell]["binary"])
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
                                       run_cmd="./x")
            raise _SimulatedCrash("fixture: retry 実行中に死ぬ")
        return _FakeScalePoint(throughputs=[_BASE_TPS[cell_id]] * 5, notes=[], run_cmd="./x")
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
        actual = hashlib.sha256(Path(rec["binary"]).read_bytes()).hexdigest()
        assert rec["binary_sha256"] == actual, cell_id
        assert len(rec["binary_sha256"]) == 64
        assert rec["bin_hash_short"] == rec["binary_sha256"][:16]


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


def test_clean_scan_digest_returns_digest_when_clean(tmp_path, monkeypatch):
    files = ("a.py", "b.py")
    _stub_clean_scan(
        monkeypatch, reports=[_clean_report()], enumerations=[files, files],
    )
    digest = s8b_floor_campaign.clean_scan_digest(tmp_path, freeze_allowlist={})
    assert digest == hashlib.sha256("a.py\nb.py".encode("utf-8")).hexdigest()


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
    freeze_dir = tmp_path / "output" / "s8b-freeze"
    freeze_dir.mkdir(parents=True)
    (freeze_dir / "unlisted.json").write_bytes(b"no holdout hit")
    files = ("output/s8b-freeze/unlisted.json",)
    _stub_clean_scan(
        monkeypatch, reports=[_clean_report()], enumerations=[files, files],
    )
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="allowlist"):
        s8b_floor_campaign.clean_scan_digest(tmp_path, freeze_allowlist={})


def test_clean_scan_digest_accepts_exact_freeze_allowlist(tmp_path, monkeypatch):
    payload = b"approved freeze bytes"
    rel = "output/s8b-freeze/approved.json"
    path = tmp_path / rel
    path.parent.mkdir(parents=True)
    path.write_bytes(payload)
    files = (rel,)
    _stub_clean_scan(
        monkeypatch, reports=[_clean_report()], enumerations=[files, files],
    )
    digest = s8b_floor_campaign.clean_scan_digest(
        tmp_path, freeze_allowlist={rel: hashlib.sha256(payload).hexdigest()},
    )
    assert digest == hashlib.sha256(rel.encode("utf-8")).hexdigest()


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
    assert repo_before == _real_output_snapshot()


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
    assert repo_before == _real_output_snapshot()


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
        protocol=_valid_protocol_dict(), cells=[cell], cell_by_id={cell_id: cell},
        binaries=binaries, schedule=[], journal_path=tmp_path / "j.jsonl",
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

    # store_binaries は冪等 (既存 store は hash 照合のみ、上書きしない)。
    built = {cid: dict(rec) for cid, rec in binaries.items()}
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
        sys.path.insert(0, {str(ORCHESTRATOR)!r})
        from campaign import s8b_floor_campaign as floor
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
