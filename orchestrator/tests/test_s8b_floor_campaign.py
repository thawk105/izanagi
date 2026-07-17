# -*- coding: utf-8 -*-
"""s8b floor campaign driver (``campaign.s8b_floor_campaign``) の契約テスト。

ccbench submodule はこのマシンに無いため、実ビルド・実 bench は一切呼ばない。
``prepare_fn``/``buildcache.build``/``measure_fn``/``probe_fn``/``sleep_fn``/
``monotonic_fn`` を全て注入し、合成 freeze fixture (holdout rr79/rr23 × 6 構成、
stock_common 含む) で全経路を回す。rr79/rr23 は実在 freeze (``output/s8b-freeze/
holdout_freeze.json`` の rr80/rr20) と records/threads/workload を意図的に変え、
「freeze から来た値」であることをテスト内で判別できるようにしてある — もし
driver がどこかで実freeze を読んでしまえば cell_id や floor 値が食い違って露見する。

floor の式そのものの mutation-killing テストは ``test_s8b_floor_stats.py`` が正本。
本ファイルは driver 側の配線 (schedule 決定性・protocol strict 検証・official 拒否・
session 有効性→retry→floor 伝播・probe 臨界区間・create-only・resume forward-only・
block-tail retry と min_block_gap_s・end-to-end golden) を固定する。
"""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
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

from campaign import s8b_floor_campaign  # noqa: E402
from campaign import s8b_floor_stats  # noqa: E402
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

# 実在 rr80 (records=1000000, threads=48) / rr20 と衝突しない合成値。
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

# 決定的 measure_fn 用の cell 別基準 tps (golden / floor 伝播テストで使う)。
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


def _protocol(*, freeze_sha: str, n_sessions: int, blocks: int,
              replicates_per_block: int, reps: int = 2,
              master_seed: str = "fixture-seed", wired_min_rel_floor: float = 0.05,
              min_block_gap_s: float = 0.0, retry_slots_per_cell: int = 1,
              env_tag: str = ENV_TAG) -> dict:
    return {
        "schema": s8b_floor_campaign.PROTOCOL_SCHEMA,
        "formula": s8b_floor_stats.FORMULA_ID,
        "env_tag": env_tag,
        "ccbench_pin": "0" * 40,
        "freeze": {"path": "output/s8b-freeze/fixture_freeze.json", "sha256": freeze_sha},
        "stock_configuration": _STOCK,
        "n_sessions": n_sessions,
        "reps": reps,
        "blocks": blocks,
        "replicates_per_block": replicates_per_block,
        "min_block_gap_s": min_block_gap_s,
        "master_seed": master_seed,
        "schedule_algorithm": s8b_floor_campaign.SCHEDULE_ALGORITHM,
        "extime_s": 3,
        "wired_min_rel_floor": wired_min_rel_floor,
        "retry_slots_per_cell": retry_slots_per_cell,
        "allowed_excluded_reasons": [
            "competing_process", "launch_failure", "nonfinite_or_partial_output",
        ],
    }


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
    """buildcache.build の代替。実バイナリの代わりに cell_id を刻んだダミーを書く。

    src_token = cell_id (``_fake_prepare`` が仕込む) をディレクトリ名にすることで、
    measure_fn 側が binary path から cell_id を再構成できるようにする。
    """
    def fake_build(genome, ccbench_commit, trace, cache_root="", cc=None, cxx=None,
                   jobs=16, ccbench_dir="", src_token=None):
        assert trace is False, "floor 計測は trace-disabled build (規律1)"
        cell_dir = build_root / src_token.replace("::", "__")
        cell_dir.mkdir(parents=True, exist_ok=True)
        binary_path = cell_dir / "ycsb_fixture.exe"
        payload = f"fixture-binary::{src_token}".encode("utf-8")
        binary_path.write_bytes(payload)
        # A-8: fake も「実際に書いた bytes の実ハッシュ」を返す。bin_hash は bin_sha256[:16]
        # の派生 (BuildResult と同じ契約) — src_token を短縮した別系列にしない。
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


def _make_measure_fn(reps, value_fn, *, raise_for=(), partial_for=(), partial_reps=None):
    raise_for = set(raise_for)
    partial_for = set(partial_for)
    calls: list = []

    def measure_fn(binary, records, threads, workload):
        cell_id = _cell_id_from_binary(binary)
        calls.append(cell_id)
        if cell_id in raise_for:
            raise RuntimeError(f"fixture: 実行不能を模す ({cell_id})")
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


# =========================================================================== #
# 1. manifest 決定性 (schedule は freeze 由来セルのみ、seed で決定論的)          #
# =========================================================================== #

def test_schedule_is_deterministic_by_seed_and_uses_only_freeze_cells():
    freeze = _freeze_document()
    cells = s8b_floor_campaign.enumerate_cells(freeze, stock_configuration=_STOCK)
    assert len(cells) == 12  # 2 holdout × 6 構成
    cell_ids = {c["cell_id"] for c in cells}
    assert cell_ids == {f"{h}::{c}" for h in ("rr79", "rr23") for c in _CONFIGS}
    # 実在 rr80/rr20/rr5/rr50/rr95 は fixture のどこにも現れない (freeze 由来のみ)。
    for forbidden in ("rr80", "rr20", "rr5", "rr50", "rr95"):
        assert not any(forbidden in cid for cid in cell_ids), forbidden

    schedule_a1 = s8b_floor_campaign.build_schedule(
        cells=cells, master_seed="seed-alpha", blocks=2, replicates_per_block=2,
    )
    schedule_a2 = s8b_floor_campaign.build_schedule(
        cells=cells, master_seed="seed-alpha", blocks=2, replicates_per_block=2,
    )
    schedule_b = s8b_floor_campaign.build_schedule(
        cells=cells, master_seed="seed-beta", blocks=2, replicates_per_block=2,
    )
    assert schedule_a1 == schedule_a2  # 同一 seed → 同一 schedule
    assert schedule_a1 != schedule_b  # 別 seed → 別置換

    # schedule の cell_id 集合は freeze 由来 12 セルのみ (行数は blocks×replicates×12)。
    assert len(schedule_a1) == 2 * 2 * 12
    schedule_cell_ids = {row["cell_id"] for row in schedule_a1}
    assert schedule_cell_ids == cell_ids
    for forbidden in ("rr80", "rr20", "rr5", "rr50", "rr95"):
        assert not any(forbidden in row["cell_id"] for row in schedule_a1), forbidden

    # block/replicate 内は 12 セルの置換 (全セルがちょうど1回ずつ)。
    for block in (1, 2):
        for replicate in (0, 1):
            rows = [r for r in schedule_a1 if r["block"] == block and r["replicate"] == replicate]
            assert {r["cell_id"] for r in rows} == cell_ids


def test_build_schedule_golden_pin_for_seed_derivation():
    """build_schedule の (seq, block, replicate, cell_id) 列を固定 master_seed でリテラル固定する。

    目的は ``_permutation_seed`` の sha256 slice (``[:8]``) や区切り文字 (``"/"``) を変える
    mutation を殺すこと (レビュー所見 F2-schedule-seed-no-golden-pin)。値は実際に実行して得た
    ものを検証したうえで焼き込んでいる。**この値は s8b-floor-manifest/v1 の schedule 導出
    (balanced-permutation/v1) の golden pin であり、変わったら seed 導出が変わった証拠**
    (意図した変更なら値を再計算してこのテストを更新する)。
    """
    freeze = _freeze_document()
    cells = s8b_floor_campaign.enumerate_cells(freeze, stock_configuration=_STOCK)
    six_cells = [c for c in cells if c["holdout_id"] == "rr79"]
    assert len(six_cells) == 6

    schedule = s8b_floor_campaign.build_schedule(
        cells=six_cells, master_seed="golden-pin-v1", blocks=2, replicates_per_block=2,
    )
    rows = [(r["seq"], r["block"], r["replicate"], r["cell_id"]) for r in schedule]

    expected = [
        (0, 1, 0, "rr79::stock_common"),
        (1, 1, 0, "rr79::sort_best"),
        (2, 1, 0, "rr79::p2_2_flag_opt"),
        (3, 1, 0, "rr79::ident_all"),
        (4, 1, 0, "rr79::system_gate"),
        (5, 1, 0, "rr79::backoff_fixed_best"),
        (6, 1, 1, "rr79::ident_all"),
        (7, 1, 1, "rr79::stock_common"),
        (8, 1, 1, "rr79::sort_best"),
        (9, 1, 1, "rr79::system_gate"),
        (10, 1, 1, "rr79::p2_2_flag_opt"),
        (11, 1, 1, "rr79::backoff_fixed_best"),
        (12, 2, 0, "rr79::p2_2_flag_opt"),
        (13, 2, 0, "rr79::stock_common"),
        (14, 2, 0, "rr79::sort_best"),
        (15, 2, 0, "rr79::backoff_fixed_best"),
        (16, 2, 0, "rr79::ident_all"),
        (17, 2, 0, "rr79::system_gate"),
        (18, 2, 1, "rr79::sort_best"),
        (19, 2, 1, "rr79::stock_common"),
        (20, 2, 1, "rr79::ident_all"),
        (21, 2, 1, "rr79::p2_2_flag_opt"),
        (22, 2, 1, "rr79::backoff_fixed_best"),
        (23, 2, 1, "rr79::system_gate"),
    ]
    assert rows == expected


# =========================================================================== #
# 2. protocol strict 検証                                                       #
# =========================================================================== #

def _valid_protocol_dict() -> dict:
    # formula v1 は 2 block 固定 (validate_protocol が blocks==2 を要求する) なので blocks=2 を使う。
    freeze = _freeze_document()
    return _protocol(freeze_sha=_freeze_sha(freeze), n_sessions=2, blocks=2,
                     replicates_per_block=1)


def test_validate_protocol_rejects_unknown_key():
    doc = _valid_protocol_dict()
    doc["unexpected_extra_key"] = 1
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="未知"):
        s8b_floor_campaign.validate_protocol(doc)


def test_validate_protocol_rejects_missing_key():
    doc = _valid_protocol_dict()
    del doc["wired_min_rel_floor"]
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="欠落"):
        s8b_floor_campaign.validate_protocol(doc)


def test_load_protocol_rejects_duplicate_top_level_key(tmp_path):
    text = '{"schema": "s8b-floor-protocol/v1", "schema": "duplicate"}'
    path = tmp_path / "dup.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="duplicate key"):
        s8b_floor_campaign.load_protocol(path)


def test_validate_protocol_rejects_formula_mismatch():
    doc = _valid_protocol_dict()
    doc["formula"] = "s8b-floor-stats/v0-wrong"
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="formula"):
        s8b_floor_campaign.validate_protocol(doc)


def test_validate_protocol_rejects_malformed_freeze_sha256():
    doc = _valid_protocol_dict()
    doc["freeze"] = {"path": doc["freeze"]["path"], "sha256": "not-a-sha256"}
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="SHA-256"):
        s8b_floor_campaign.validate_protocol(doc)


def test_validate_protocol_rejects_blocks_times_replicates_mismatch():
    doc = _valid_protocol_dict()
    doc["n_sessions"] = 99  # blocks(1) * replicates_per_block(1) = 1 != 99
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="n_sessions"):
        s8b_floor_campaign.validate_protocol(doc)


def test_validate_protocol_rejects_blocks_not_two():
    """formula v1 は 2 block 固定 (block_medians[1]/[2] 直接添字参照)。blocks!=2 は
    blocks*replicates_per_block==n_sessions を満たしていても拒否する
    (レビュー所見 F1-blocks-not-pinned-to-2)。"""
    doc = _valid_protocol_dict()
    doc["blocks"] = 3
    doc["replicates_per_block"] = 1
    doc["n_sessions"] = 3
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="2-block"):
        s8b_floor_campaign.validate_protocol(doc)


def _forbid_measure(*_a, **_kw):
    raise AssertionError("hash/env の pin 検査より前で measure_fn が呼ばれてはいけない")


def test_run_campaign_rejects_freeze_byte_hash_mismatch(tmp_path):
    freeze = _freeze_document()
    # formula v1 は 2 block 固定 (validate_protocol が blocks==2 を要求する) なので blocks=2 を使う。
    protocol = _protocol(freeze_sha=_freeze_sha(freeze), n_sessions=2, blocks=2,
                         replicates_per_block=1)
    # freeze_doc の sha256 は正しい形式だが protocol.freeze.sha256 と値が食い違う。
    other_bytes = json.dumps({"different": "document"}).encode("utf-8")
    tampered = VerifiedFreeze(document=freeze, sha256=hashlib.sha256(other_bytes).hexdigest())
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="bytes-hash pin"):
        _run_campaign(protocol, tampered, out_root=tmp_path / "out",
                     build_root=tmp_path / "bin", measure_fn=_forbid_measure,
                     probe_fn=lambda: (1, ""))


def test_run_campaign_rejects_env_tag_mismatch(tmp_path):
    freeze = _freeze_document()
    # formula v1 は 2 block 固定 (validate_protocol が blocks==2 を要求する) なので blocks=2 を使う。
    protocol = _protocol(freeze_sha=_freeze_sha(freeze), n_sessions=2, blocks=2,
                         replicates_per_block=1, env_tag="some-other-env")
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="env_tag"):
        _run_campaign(protocol, _verified_freeze(freeze), out_root=tmp_path / "out",
                     build_root=tmp_path / "bin", measure_fn=_forbid_measure,
                     probe_fn=lambda: (1, ""))


# =========================================================================== #
# 3. official mode は常に拒否 (§8 未裁定)                                       #
# =========================================================================== #

def test_main_official_mode_always_refused(tmp_path, capsys):
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text("{}", encoding="utf-8")  # official 拒否は内容を読む前に効く
    rc = s8b_floor_campaign.main(["--mode", "official", "--protocol", str(protocol_path)])
    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "refused"
    assert "§8" in payload["reason"]


def test_pilot_cli_broken_freeze_emits_structured_error_not_traceback(tmp_path):
    """境界欠陥是正の固定: pilot CLI が壊れた freeze (byte hash 不一致) で落ちるとき、
    loader 例外は境界 adapter で FloorCampaignError へ変換され、既存の構造化 error
    JSON 経路 (rc 1) に乗る (traceback で漏れない)。

    移行前は loader が OracleDriverError を投げ、CLI の except FloorCampaignError に
    捕捉されず traceback として stderr へ漏れていた。本テストはその是正を subprocess
    で固定する。
    """
    freeze_path = tmp_path / "freeze.json"
    # 実 sha256 は protocol.freeze.sha256 ("0"*64) と一致しない (hash 不一致で拒否)。
    freeze_path.write_text("{}", encoding="utf-8")
    protocol = _protocol(freeze_sha="0" * 64, n_sessions=2, blocks=2,
                         replicates_per_block=1)
    protocol["freeze"]["path"] = str(freeze_path)  # 絶対 path は resolve 素通し。
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
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
    )
    assert proc.returncode == 1, (proc.returncode, proc.stdout, proc.stderr)
    assert "Traceback" not in proc.stderr, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "error"
    assert "FloorCampaignError" in payload["error"]
    assert "expected_hash" in payload["error"]


# =========================================================================== #
# 4. session 有効性 → retry → floor 未確定の伝播                                #
# =========================================================================== #

def test_partial_reps_invalidates_session_and_surviving_retry_failure_nulls_floor(tmp_path):
    freeze = _freeze_document()
    freeze_sha = _freeze_sha(freeze)
    verified = _verified_freeze(freeze)

    # --- 非 stock セルが flaky (4/5 reps) → retry も失敗 → 当該 pair のみ null ---
    # formula v1 は 2 block 固定 (block_medians[1]/[2] を直接参照) なので blocks=2 を使う
    # (n_sessions=1 の 1 block では stdev が要る 2 点が集まらず holdout_floors が壊れる)。
    flaky = "rr79::sort_best"
    measure_fn = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid],
                                  partial_for={flaky})
    protocol = _protocol(freeze_sha=freeze_sha, n_sessions=2, blocks=2,
                         replicates_per_block=1, reps=5, retry_slots_per_cell=1)
    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "nonstock",
                            build_root=tmp_path / "nonstock-bin",
                            measure_fn=measure_fn, probe_fn=lambda: (1, ""))
    result = outcome["result"]

    flaky_sessions = [s for s in result["sessions"] if s["cell_id"] == flaky]
    # retry_slots_per_cell はセル単位の campaign 全体予算 (block ごとではない) — block1 の
    # planned+retry で 1 枠を使い切り、block2 は planned のみで retry を持てない。
    assert len(flaky_sessions) == 3
    assert all(not s["valid"] for s in flaky_sessions)
    assert all(s["excluded_reason"] == "nonfinite_or_partial_output" for s in flaky_sessions)

    assert result["cells"][flaky]["valid"] is False
    assert result["cells"][flaky]["n_valid"] == 0
    assert result["floors"]["rr79"]["pairs"][flaky] is None
    other = "rr79::p2_2_flag_opt"
    assert result["floors"]["rr79"]["pairs"][other] is not None
    assert result["floors"]["rr79"]["scale_ref"] is not None  # stock は valid
    assert result["floors"]["rr79"]["scalar_alt"] is None  # null pair が veto する
    for cid, floor in result["floors"]["rr23"]["pairs"].items():
        assert floor is not None, cid  # rr23 holdout は無関係で全確定
    assert result["floors"]["rr23"]["scalar_alt"] is not None

    # --- stock セルが flaky → 当該 holdout の floor は全 pair + scale_ref が null ---
    stock_flaky = "rr79::stock_common"
    measure_fn2 = _make_measure_fn(reps=5, value_fn=lambda cid: _BASE_TPS[cid],
                                   partial_for={stock_flaky})
    outcome2 = _run_campaign(protocol, verified, out_root=tmp_path / "stock",
                             build_root=tmp_path / "stock-bin",
                             measure_fn=measure_fn2, probe_fn=lambda: (1, ""))
    result2 = outcome2["result"]
    assert result2["cells"][stock_flaky]["valid"] is False
    for cid, floor in result2["floors"]["rr79"]["pairs"].items():
        assert floor is None, cid
    assert result2["floors"]["rr79"]["scale_ref"] is None
    assert result2["floors"]["rr79"]["scalar_alt"] is None
    for cid, floor in result2["floors"]["rr23"]["pairs"].items():
        assert floor is not None, cid  # 無関係 holdout は無傷


# =========================================================================== #
# 5. probe 臨界区間 (競合 → session 無効 + journal に生出力、実行不能 → abort)   #
# =========================================================================== #

def test_probe_competing_invalidates_session_with_raw_stdout_in_journal(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    # formula v1 は 2 block 固定 (validate_protocol が blocks==2 を要求する) なので blocks=2 を使う。
    protocol = _protocol(freeze_sha=_freeze_sha(freeze), n_sessions=2, blocks=2,
                         replicates_per_block=1, reps=2, retry_slots_per_cell=0)
    measure_fn = _make_measure_fn(reps=2, value_fn=lambda cid: _BASE_TPS[cid])
    conflicting_stdout = "999 ycsb_fixture.exe -thread_num=1\n"

    outcome = _run_campaign(
        protocol, verified, out_root=tmp_path / "out", build_root=tmp_path / "bin",
        measure_fn=measure_fn, probe_fn=lambda: (0, conflicting_stdout),
    )
    assert measure_fn.calls == []  # 競合検知は measure の前でスキップする
    result = outcome["result"]
    assert all(not s["valid"] for s in result["sessions"])
    assert all(s["excluded_reason"] == "competing_process" for s in result["sessions"])
    sample = result["sessions"][0]
    assert sample["probe_before"]["stdout"] == conflicting_stdout
    assert sample["probe_before"]["competing"]  # 生の競合行が journal に残る


@pytest.mark.parametrize("probe_fn, match", [
    (lambda: (2, "unexpected rc"), "rc"),
    (lambda: (_ for _ in ()).throw(OSError("pgrep 不在を模す")), "OSError"),
    (lambda: (0, "not-a-pid ycsb_fixture.exe"), "parse"),
])
def test_probe_unexecutable_or_unparseable_aborts_campaign(tmp_path, probe_fn, match):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    # formula v1 は 2 block 固定 (validate_protocol が blocks==2 を要求する) なので blocks=2 を使う。
    protocol = _protocol(freeze_sha=_freeze_sha(freeze), n_sessions=2, blocks=2,
                         replicates_per_block=1, reps=2, retry_slots_per_cell=0)
    measure_fn = _make_measure_fn(reps=2, value_fn=lambda cid: _BASE_TPS[cid])

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
    assert not (run_dir / "result.json").exists()  # abort 時は artifact を書かない


# =========================================================================== #
# 6. create-only (manifest/result) と journal の append                        #
# =========================================================================== #

def test_create_only_rejects_overwrite_journal_appends(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze), n_sessions=2, blocks=2,
                         replicates_per_block=1, reps=2)
    measure_fn = _make_measure_fn(reps=2, value_fn=lambda cid: _BASE_TPS[cid])
    out_root = tmp_path / "out"

    outcome = _run_campaign(protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                            measure_fn=measure_fn, probe_fn=lambda: (1, ""))
    run_dir = Path(outcome["run_dir"])
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "result.json").exists()

    # 同一 protocol/now_fn で fresh run を再実行 → 同一 run_dir に衝突して拒否。
    measure_fn2 = _make_measure_fn(reps=2, value_fn=lambda cid: _BASE_TPS[cid])
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="既に存在する"):
        _run_campaign(protocol, verified, out_root=out_root, build_root=tmp_path / "bin2",
                      measure_fn=measure_fn2, probe_fn=lambda: (1, ""))

    # create-only の直接検査: 既存 result.json への上書きは常に拒否。
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="既に存在するため上書きしない"):
        s8b_floor_campaign._write_create_only_json(run_dir / "result.json", {"x": 1})

    # journal は append-only で伸びる。
    journal_path = run_dir / "journal.jsonl"
    before = journal_path.read_text(encoding="utf-8")
    s8b_floor_campaign._journal_append(journal_path, {"event": "test-append-marker"})
    after = journal_path.read_text(encoding="utf-8")
    assert after.startswith(before)
    assert len(after) > len(before)


# =========================================================================== #
# 7. resume: forward-only 再入、protocol/freeze hash pin                       #
# =========================================================================== #

class _SimulatedCrash(Exception):
    """resume テスト専用: 実クラッシュ (measure_fn を包む except に捕まらない例外) を模す。"""


def test_resume_forward_only_skips_completed_and_crashed_seqs(tmp_path):
    freeze = _freeze_document()
    freeze_sha = _freeze_sha(freeze)
    verified = _verified_freeze(freeze)
    # formula v1 は 2 block 固定なので blocks=2 (単一 block では stdev が壊れる、上の
    # test_partial_reps... 参照)。schedule = blocks(2) × replicates(1) × 12 cells = 24 行。
    protocol = _protocol(freeze_sha=freeze_sha, n_sessions=2, blocks=2,
                         replicates_per_block=1, reps=2, retry_slots_per_cell=1)
    out_root = tmp_path / "out"

    call_count = {"n": 0}

    def crashing_measure_fn(binary, records, threads, workload):
        call_count["n"] += 1
        if call_count["n"] == 4:
            raise _SimulatedCrash("fixture: プロセスが session 実行中に死ぬ")
        cell_id = _cell_id_from_binary(binary)
        return _FakeScalePoint(throughputs=[_BASE_TPS[cell_id]] * 2, notes=[], run_cmd="./x")

    with pytest.raises(_SimulatedCrash):
        _run_campaign(protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                     measure_fn=crashing_measure_fn, probe_fn=lambda: (1, ""))
    assert call_count["n"] == 4

    run_dir = _only_run_dir(out_root)
    assert not (run_dir / "result.json").exists()
    journal_before = _read_journal_lines(run_dir / "journal.jsonl")
    starts_before = [r for r in journal_before if r.get("event") == "session-start"]
    sessions_before = [r for r in journal_before if r.get("event") == "session"]
    assert {r["seq"] for r in starts_before} == {0, 1, 2, 3}
    assert {r["seq"] for r in sessions_before} == {0, 1, 2}  # seq3 は start だけ残る
    crashed_cell_id = next(r["cell_id"] for r in starts_before if r["seq"] == 3)

    # protocol/freeze hash が不一致な resume は拒否される。
    mismatched_protocol = dict(protocol)
    mismatched_protocol["reps"] = protocol["reps"] + 1
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="protocol sha256"):
        _run_campaign(mismatched_protocol, verified, out_root=out_root,
                     build_root=tmp_path / "bin", resume_dir=run_dir,
                     measure_fn=crashing_measure_fn, probe_fn=lambda: (1, ""))

    resuming_measure_fn = _make_measure_fn(reps=2, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
                            resume_dir=run_dir, measure_fn=resuming_measure_fn,
                            probe_fn=lambda: (1, ""))
    assert outcome["status"] == "completed"
    # 完了済み seq0-2、crash した seq3 は forward-only で再実行しない (seq3 の cell の
    # *別 block* の occurrence は別 seq の別行なので、そちらは resume で普通に実行される)。
    assert len(resuming_measure_fn.calls) == 20  # seq4..23 の 20 本だけ新規実行

    journal_after = _read_journal_lines(run_dir / "journal.jsonl")
    starts_after = [r for r in journal_after if r.get("event") == "session-start"]
    seqs_after = [r["seq"] for r in starts_after]
    assert len(seqs_after) == len(set(seqs_after)) == 24  # seq の二重 start が無い
    assert sum(1 for r in starts_after if r["seq"] == 3) == 1  # crash した seq3 は 1 回だけ

    # crash したセルは crash した block 分の有効 session を永久に失い (retry も効かない
    # forward-only 仕様)、n_sessions(2) に届かず invalid のまま伝播する。
    result = outcome["result"]
    assert result["cells"][crashed_cell_id]["n_valid"] < 2
    assert result["cells"][crashed_cell_id]["valid"] is False
    assert not any(r.get("seq") == 3 and r.get("event") == "session" for r in journal_after)


def test_resume_rejects_tampered_binary_but_succeeds_when_untampered(tmp_path):
    """resume は manifest 記録の binary_sha256 を disk 上バイナリと再照合する (所見
    F3-resume-binary-hash-not-enforced)。フル run を途中 crash させ、バイナリ file の内容を
    書き換えてから resume すると FloorCampaignError で拒否され、書き換えを戻せば resume が
    成功することを確認する (crash-resume fixture は
    ``test_resume_forward_only_skips_completed_and_crashed_seqs`` と同型)。
    """
    freeze = _freeze_document()
    freeze_sha = _freeze_sha(freeze)
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=freeze_sha, n_sessions=2, blocks=2,
                         replicates_per_block=1, reps=2, retry_slots_per_cell=1)
    out_root = tmp_path / "out"
    build_root = tmp_path / "bin"

    call_count = {"n": 0}

    def crashing_measure_fn(binary, records, threads, workload):
        call_count["n"] += 1
        if call_count["n"] == 4:
            raise _SimulatedCrash("fixture: プロセスが session 実行中に死ぬ")
        cell_id = _cell_id_from_binary(binary)
        return _FakeScalePoint(throughputs=[_BASE_TPS[cell_id]] * 2, notes=[], run_cmd="./x")

    with pytest.raises(_SimulatedCrash):
        _run_campaign(protocol, verified, out_root=out_root, build_root=build_root,
                     measure_fn=crashing_measure_fn, probe_fn=lambda: (1, ""))

    run_dir = _only_run_dir(out_root)
    manifest = json.loads((run_dir / "manifest.json").read_bytes())
    binaries = manifest["binaries"]
    tampered_cell_id = sorted(binaries)[0]
    tampered_binary_path = Path(binaries[tampered_cell_id]["binary"])
    original_bytes = tampered_binary_path.read_bytes()

    # --- バイナリ内容を書き換える → resume は binary sha256 不一致で拒否される ---
    tampered_binary_path.write_bytes(original_bytes + b"-tampered")
    resuming_measure_fn = _make_measure_fn(reps=2, value_fn=lambda cid: _BASE_TPS[cid])
    with pytest.raises(s8b_floor_campaign.FloorCampaignError, match="バイナリ sha256"):
        _run_campaign(protocol, verified, out_root=out_root, build_root=build_root,
                     resume_dir=run_dir, measure_fn=resuming_measure_fn,
                     probe_fn=lambda: (1, ""))
    assert resuming_measure_fn.calls == []  # hash 不一致検出は measure より前で効く
    assert not (run_dir / "result.json").exists()

    # --- 書き換えを戻す → resume は成功する ---
    tampered_binary_path.write_bytes(original_bytes)
    resuming_measure_fn2 = _make_measure_fn(reps=2, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(protocol, verified, out_root=out_root, build_root=build_root,
                            resume_dir=run_dir, measure_fn=resuming_measure_fn2,
                            probe_fn=lambda: (1, ""))
    assert outcome["status"] == "completed"


# =========================================================================== #
# 8. block-tail retry のラベル保持 + min_block_gap_s (実 sleep なし)             #
# =========================================================================== #

class _FakeClock:
    def __init__(self):
        self.t = 0.0
        self.sleep_calls: list = []

    def monotonic(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.sleep_calls.append(seconds)
        self.t += seconds


def test_block_tail_retry_preserves_block_label_and_honors_min_block_gap(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze), n_sessions=2, blocks=2,
                         replicates_per_block=1, reps=2, retry_slots_per_cell=1,
                         min_block_gap_s=3.0)
    flaky = "rr79::sort_best"
    per_cell_calls: dict = {}

    def measure_fn(binary, records, threads, workload):
        cell_id = _cell_id_from_binary(binary)
        per_cell_calls[cell_id] = per_cell_calls.get(cell_id, 0) + 1
        if cell_id == flaky and per_cell_calls[cell_id] == 1:
            # block1 の planned だけ 1/2 reps で無効、retry と block2 は正常。
            return _FakeScalePoint(throughputs=[_BASE_TPS[cell_id]], notes=[], run_cmd="./x")
        return _FakeScalePoint(throughputs=[_BASE_TPS[cell_id]] * 2, notes=[], run_cmd="./x")

    clock = _FakeClock()
    out_root = tmp_path / "out"
    with mock.patch("time.sleep", side_effect=AssertionError("実 sleep を呼んではいけない")):
        outcome = _run_campaign(
            protocol, verified, out_root=out_root, build_root=tmp_path / "bin",
            measure_fn=measure_fn, probe_fn=lambda: (1, ""),
            sleep_fn=clock.sleep, monotonic_fn=clock.monotonic,
        )
    assert outcome["status"] == "completed"

    # min_block_gap_s=3.0 は sleep_fn 経由で守られる (実 sleep 呼び出しゼロ)。
    assert clock.sleep_calls == [1.0, 1.0, 1.0]
    assert sum(clock.sleep_calls) == pytest.approx(3.0)

    run_dir = Path(outcome["run_dir"])
    journal = _read_journal_lines(run_dir / "journal.jsonl")
    flaky_sessions = [r for r in journal if r.get("event") == "session" and r["cell_id"] == flaky]
    assert len(flaky_sessions) == 3  # block1 planned(無効) + block1 retry(有効) + block2 planned
    planned_b1 = [s for s in flaky_sessions if s["kind"] == "planned" and s["block"] == 1][0]
    retry_b1 = [s for s in flaky_sessions if s["kind"] == "retry"][0]
    planned_b2 = [s for s in flaky_sessions if s["kind"] == "planned" and s["block"] == 2][0]
    assert planned_b1["valid"] is False
    assert retry_b1["valid"] is True
    assert retry_b1["block"] == 1  # block 末尾 retry は元の block ラベルを保つ
    assert planned_b2["valid"] is True
    assert planned_b2["block"] == 2

    assert outcome["result"]["cells"][flaky]["valid"] is True  # retry で n_sessions を満たす


# =========================================================================== #
# 9. end-to-end golden (小さい n) + verify_floor_artifact の改竄検出            #
# =========================================================================== #

def test_end_to_end_golden_floor_values_and_tamper_detection(tmp_path):
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    wired = 0.05
    protocol = _protocol(freeze_sha=_freeze_sha(freeze), n_sessions=4, blocks=2,
                         replicates_per_block=2, reps=3, wired_min_rel_floor=wired,
                         retry_slots_per_cell=1)
    # 全 session が同一 cell に対し同一値を返す決定的 measure_fn
    # (block 間対比 delta=0, u_noise=0 になるよう作為 — floor = wired × m_stock に一致)。
    measure_fn = _make_measure_fn(reps=3, value_fn=lambda cid: _BASE_TPS[cid])

    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "out",
                            build_root=tmp_path / "bin", measure_fn=measure_fn,
                            probe_fn=lambda: (1, ""))
    assert outcome["status"] == "completed"
    result = outcome["result"]

    assert s8b_floor_stats.verify_floor_artifact(result) == []

    for holdout_id in ("rr79", "rr23"):
        stock_id = f"{holdout_id}::{_STOCK}"
        m_stock = _BASE_TPS[stock_id]
        expected_floor = wired * m_stock
        floors = result["floors"][holdout_id]
        assert floors["scale_ref"] == m_stock
        for cfg in _CONFIGS:
            if cfg == _STOCK:
                continue
            cell_id = f"{holdout_id}::{cfg}"
            assert floors["pairs"][cell_id] == expected_floor, cell_id
        assert floors["scalar_alt"] == expected_floor

    # 改竄検出: floor 値を 1 つ書き換えると verify_floor_artifact が非空になる。
    tampered = json.loads(json.dumps(result))  # 深いコピー
    tampered["floors"]["rr79"]["pairs"][f"rr79::{_CONFIGS[0]}"] = 999999.0
    problems = s8b_floor_stats.verify_floor_artifact(tampered)
    assert problems  # 齟齬が検出される (空でない)


def test_floor_manifest_binary_sha256_matches_real_file_bytes(tmp_path):
    """A-8/A-4: manifest.binaries に記録した binary_sha256 が disk 上バイナリの実 sha256 と
    一致する。build_cells が result.bin_sha256 を単一ソースにし record 時の再ハッシュをやめても
    byte 整合が保たれること、および bin_hash_short が binary_sha256[:16] の派生であることを固定。
    fake build は「実際に書いた bytes の実ハッシュ」を返すので、期待値は本番経路と独立。"""
    freeze = _freeze_document()
    verified = _verified_freeze(freeze)
    protocol = _protocol(freeze_sha=_freeze_sha(freeze), n_sessions=2, blocks=2,
                         replicates_per_block=1, reps=2, retry_slots_per_cell=1)
    measure_fn = _make_measure_fn(reps=2, value_fn=lambda cid: _BASE_TPS[cid])
    outcome = _run_campaign(protocol, verified, out_root=tmp_path / "out",
                            build_root=tmp_path / "bin", measure_fn=measure_fn,
                            probe_fn=lambda: (1, ""))
    assert outcome["status"] == "completed"
    run_dir = _only_run_dir(tmp_path / "out")
    binaries = json.loads((run_dir / "manifest.json").read_bytes())["binaries"]
    assert binaries
    for cell_id, rec in binaries.items():
        actual = hashlib.sha256(Path(rec["binary"]).read_bytes()).hexdigest()
        assert rec["binary_sha256"] == actual, cell_id       # 実ファイル byte と一致
        assert len(rec["binary_sha256"]) == 64
        assert rec["bin_hash_short"] == rec["binary_sha256"][:16]  # 派生関係
