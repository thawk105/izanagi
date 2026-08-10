# -*- coding: utf-8 -*-
"""中立 leaf ``s8b_freeze_io`` の loader 契約を characterization で固定する。

strictness は現行 (移行前 s8b_oracle_driver.load_verified_freeze) と同値である:
NaN/Infinity 拒否 + expected_hash 束縛 + top-level object 検査のみ。duplicate key
拒否・encoding 追加検査など現行に無い検査は足さない (F6/F7 裁定後の
load_ratified_freeze の責務)。各期待は現行実装が実際に返す/投げるものを実測して
pin している (期待の先決めをしない)。
"""
from __future__ import annotations

import hashlib
import shlex
import json
import pathlib
import subprocess
import sys
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parent.parent
if str(ORCHESTRATOR.parent) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign import s8b_freeze_io as fio  # noqa: E402


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# 受理拒否行列 (characterization)                                               #
# --------------------------------------------------------------------------- #

def test_accepts_wellformed_object_and_returns_byte_sha256(tmp_path):
    doc = {"floor": None, "budget": None, "x": 1}
    path = _write(tmp_path / "ok.json", json.dumps(doc))
    expected = hashlib.sha256(path.read_bytes()).hexdigest()

    verified = fio.load_verified_freeze(path)
    assert isinstance(verified, fio.VerifiedFreeze)
    assert verified.document == doc
    assert verified.sha256 == expected


def test_expected_hash_match_accepts_mismatch_rejects(tmp_path):
    path = _write(tmp_path / "ok.json", json.dumps({"a": 1}))
    expected = hashlib.sha256(path.read_bytes()).hexdigest()

    assert fio.load_verified_freeze(path, expected_hash=expected).sha256 == expected

    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(path, expected_hash="0" * 64)
    assert "expected_hash" in str(exc.value)


def test_rejects_nan_constant(tmp_path):
    path = _write(tmp_path / "nan.json", '{"x": NaN}')
    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(path)
    assert "非数値定数" in str(exc.value) and "NaN" in str(exc.value)


def test_rejects_infinity_constant(tmp_path):
    path = _write(tmp_path / "inf.json", '{"x": Infinity}')
    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(path)
    assert "非数値定数" in str(exc.value) and "Infinity" in str(exc.value)


def test_rejects_malformed_json(tmp_path):
    path = _write(tmp_path / "mal.json", "{not json")
    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(path)
    assert "strict parse できない" in str(exc.value)


def test_rejects_non_utf8_bytes(tmp_path):
    path = tmp_path / "bin.json"
    path.write_bytes(b"\xff\xfe{}")
    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(path)
    # decode は strict parse ブロック内で起きるため strict parse 経路の message になる。
    assert "strict parse できない" in str(exc.value)


def test_rejects_missing_file(tmp_path):
    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(tmp_path / "absent.json")
    assert "読めない" in str(exc.value)


def test_rejects_non_object_top_level(tmp_path):
    path = _write(tmp_path / "arr.json", "[1, 2, 3]")
    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(path)
    assert "top-level が object でない" in str(exc.value)


def test_duplicate_key_is_accepted_not_rejected(tmp_path):
    """characterization: 現行 loader は duplicate key を拒否しない (last-wins)。

    F6/F7 裁定後の load_ratified_freeze が dup-key 拒否を持つべきで、本 leaf には
    追加しない。この受理は「strictness を勝手に上げていない」ことの機械固定である。
    """
    path = _write(tmp_path / "dup.json", '{"a": 1, "a": 2}')
    verified = fio.load_verified_freeze(path)
    assert verified.document == {"a": 2}


# --------------------------------------------------------------------------- #
# 単一 read の positive control                                                 #
# --------------------------------------------------------------------------- #

def test_reads_bytes_exactly_once(tmp_path, monkeypatch):
    path = _write(tmp_path / "ok.json", json.dumps({"a": 1}))
    real_read_bytes = pathlib.Path.read_bytes
    calls: list[Path] = []

    def counting_read_bytes(self):
        calls.append(Path(self))
        return real_read_bytes(self)

    monkeypatch.setattr(pathlib.Path, "read_bytes", counting_read_bytes)
    fio.load_verified_freeze(path)
    assert calls == [path]


# --------------------------------------------------------------------------- #
# import-edge 負テスト (手順 0 と同じ subprocess 方式)                          #
# --------------------------------------------------------------------------- #

def test_floor_alone_does_not_import_oracle_driver():
    """G-9: floor 単独 import が oracle_driver を巻き込まないこと。

    移行前は floor が oracle_driver から NUMACTL/VerifiedFreeze/load_verified_freeze
    を import していたため、この assert は赤だった (中立 leaf 化前の positive control)。
    """
    script = (
        f"import sys; sys.path.insert(0, {str(ORCHESTRATOR.parent)!r}); "
        "import orchestrator.campaign.s8b_floor_campaign; "
        "sys.exit(0 if 'orchestrator.campaign.s8b_oracle_driver' not in sys.modules else 1)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
    )
    assert proc.returncode == 0, (proc.returncode, proc.stdout, proc.stderr)


def test_oracle_alone_still_imports():
    """oracle_driver 単独 import は健全 (leaf を経由して loader を得る)。"""
    script = (
        f"import sys; sys.path.insert(0, {str(ORCHESTRATOR.parent)!r}); "
        "import orchestrator.campaign.s8b_oracle_driver as d; "
        "import orchestrator.campaign.s8b_freeze_io as fio; "
        "sys.exit(0 if d._freeze_io is fio else 1)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
    )
    assert proc.returncode == 0, (proc.returncode, proc.stdout, proc.stderr)


# --------------------------------------------------------------------------- #
# 実再エクスポート排除                                                          #
# --------------------------------------------------------------------------- #

def test_driver_does_not_re_export_loader_names():
    from orchestrator.campaign import s8b_oracle_driver as driver
    assert not hasattr(driver, "VerifiedFreeze")
    assert not hasattr(driver, "load_verified_freeze")


def test_floor_does_not_re_export_loader_names():
    from orchestrator.campaign import s8b_floor_campaign as floor
    assert not hasattr(floor, "VerifiedFreeze")
    assert not hasattr(floor, "load_verified_freeze")


# --------------------------------------------------------------------------- #
# class identity は単一 (dataclass を二重定義しない)                            #
# --------------------------------------------------------------------------- #

def test_verified_freeze_class_identity_is_single():
    from orchestrator.campaign import s8b_oracle_driver as driver
    from orchestrator.campaign import s8b_floor_campaign as floor
    assert driver._freeze_io.VerifiedFreeze is fio.VerifiedFreeze
    assert floor._freeze_io.VerifiedFreeze is fio.VerifiedFreeze


# --------------------------------------------------------------------------- #
# env 配線 (F4): NUMACTL/CLK は p2_2 直 import でなく env_contract 経由           #
# --------------------------------------------------------------------------- #

def test_floor_no_longer_direct_imports_clk_or_numactl():
    """F4 結線後、floor は CLK/NUMA を p2_2 から直 import しない (env_contract 経由)。

    旧 wave の ``floor.NUMACTL is p2_2.NUMA`` identity は contract 化で消える。ENV_TAG のみ
    machine-pin 用に残す。"""
    from orchestrator.campaign import s8b_floor_campaign as floor
    assert not hasattr(floor, "NUMACTL")   # p2_2.NUMA の直 import は削除された
    assert not hasattr(floor, "CLK")       # p2_2.CLK の直 import も削除された
    assert hasattr(floor, "ENV_TAG")       # machine-pin 用にのみ残す
    assert floor._env_contract is not None  # env_contract を結線している


def test_measure_fn_closure_passes_contract_numactl_to_measure_point(tmp_path):
    """``measure_fn=None`` 経路の既定 closure が ``measure_point`` へ ``numactl`` /
    ``clocks_per_us`` を **contract から** 渡すことを実引数 spy で固定する (γ-14: closure ソース
    文字列検査でなく挙動検査)。"""
    import contextlib
    from types import SimpleNamespace
    from unittest import mock

    from orchestrator.campaign import env_contract as ec
    from orchestrator.campaign import s8b_floor_campaign as floor
    from orchestrator.campaign.model import Genome
    from orchestrator.campaign.p2_2 import ENV_TAG
    from orchestrator.campaign.s1_direct_comparison import PreparedCell

    configs = ("stock_common", "alt_a")
    shape = {"records": 730079, "threads": 17,
             "ycsb": {"ycsb_zipf_skew": "0.42", "ycsb_rratio": "79", "ycsb_rmw": "1"}}
    entries = {c: {"holdout_id": "rrX", "label": f"fx-{c}", "flags": {"BACK_OFF": i}}
               for i, c in enumerate(configs)}
    freeze = {"schema_version": floor.FREEZE_SCHEMA,
              "holdouts": {"rrX": {**shape, "variant_binding": {"entries": entries}}}}
    freeze_sha = hashlib.sha256(json.dumps(
        freeze, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    protocol = {
        "schema": floor.PROTOCOL_SCHEMA, "formula": floor.s8b_floor_stats.FORMULA_ID,
        "env_tag": ENV_TAG, "ccbench_pin": "0" * 40,
        "freeze": {"path": "output/s8b-freeze/fx.json", "sha256": freeze_sha},
        "stock_configuration": "stock_common", "n_sessions": 8, "reps": 5,
        "master_seed": "seed", "schedule_algorithm": floor.SCHEDULE_ALGORITHM,
        "extime_s": 5, "wired_min_rel_floor": 0.05, "retry_slots_per_cell": 2,
        "session_cv_max": "0.10", "cell_cv_max": "0.15",
        "scale_adequacy_rel_tolerance": "0.10",
        "allowed_excluded_reasons": list(floor.s8b_floor_stats.ALLOWED_EXCLUDED_REASONS),
        "contract_sha256": ec.lookup(ENV_TAG).contract_sha256,
    }
    verified = fio.VerifiedFreeze(document=freeze, sha256=freeze_sha)
    contract = ec.lookup(ENV_TAG)

    @contextlib.contextmanager
    def fake_prepare(cell, ccbench_pin):
        cell_id = f"{cell['variant']['holdout_id']}::{cell['configuration']}"
        yield PreparedCell(genome=Genome("silo", {}), src_token=cell_id,
                           ccbench_dir="/fx/ccbench", cache_root="/fx/cache")

    def fake_build(genome, ccbench_commit, trace, cache_root="", cc=None, cxx=None,
                   jobs=16, ccbench_dir="", src_token=None, contract=None,
                   timeout_s=None, admission=None, build_context=None,
                   source_evidence=None):
        assert admission is not None
        assert build_context is not None
        assert source_evidence is not None
        assert ccbench_dir == "/fx/ccbench"
        assert timeout_s == 900
        d = Path(cache_root) / "fixture" / src_token.replace("::", "__")
        d.mkdir(parents=True, exist_ok=True)
        b = d / "ycsb.exe"
        payload = src_token.encode()
        b.write_bytes(payload)
        sha = hashlib.sha256(payload).hexdigest()
        return SimpleNamespace(binary=str(b), bin_sha256=sha, bin_hash=sha[:16],
                               configure_cmd="#", build_cmd="#", cached=False,
                               configure_argv=[
                                   "cmake", "-S", "/fx/ccbench", "-B", str(d)],
                               build_argv=["cmake", "--build", str(d)],
                               ccbench_root="/fx/ccbench",
                               contract_sha256=contract.contract_sha256)

    seen = {}

    def fixture_evidence(genome, ccbench_commit, *, ccbench_dir="", **_ignored):
        source_sha = hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest()
        return floor.source_digest.SourceEvidence(
            schema_version=floor.source_digest.SOURCE_EVIDENCE_SCHEMA,
            source_root=str(Path(ccbench_dir).resolve()),
            ccbench_commit=ccbench_commit,
            genome_sha256=source_sha,
            src_token=source_sha,
            source_bytes_sha256=source_sha,
            tracked_clean=True,
            tracked_diff_sha256=floor.source_digest.EMPTY_TRACKED_DIFF_SHA256,
            tracked_paths=(),
        )

    def spy_measure_point(binary, records, threads, clocks_per_us, **kw):
        seen["clocks_per_us"] = clocks_per_us
        seen["numactl"] = kw.get("numactl")
        argv = list(floor.build_portable_run_cmd(
            binary="output/fixture/bench", workload=kw["workload"], records=records,
            threads=threads, extime_s=kw["extime"], clocks_per_us=clocks_per_us,
            numactl=kw.get("numactl")))
        argv[argv.index("--") + 1] = str(binary)
        return SimpleNamespace(throughputs=[1000.0] * 5, notes=[],
                               run_cmd=shlex.join(argv))

    with mock.patch.object(floor.buildcache, "build_v2", fake_build), \
         mock.patch.object(floor.source_digest, "resolve_evidence", fixture_evidence), \
         mock.patch.object(floor, "measure_point", spy_measure_point):
        floor.run_campaign(protocol, verified, out_root=tmp_path / "out", mode="pilot",
                           measure_fn=None, probe_fn=lambda: (1, "", ""),
                           prepare_fn=fake_prepare, now_fn=lambda: __import__("datetime")
                           .datetime(2026, 1, 1, tzinfo=__import__("datetime").timezone.utc),
                           monotonic_fn=lambda: 0.0,
                           durable_root_policy=floor.DurableRootPolicy(
                               approved_roots=(tmp_path.resolve(),), forbidden_roots=()))
    assert seen["clocks_per_us"] == contract.clocks_per_us
    assert seen["numactl"] == list(contract.numactl)


if __name__ == "__main__":
    # 自走 harness: `python3 test_s8b_freeze_io.py` で実際に pytest を回す (素の runner
    # による 0 件実行の偽緑を防ぐ。test_plain_runner_coverage の契約)。
    sys.exit(pytest.main([__file__, "-q"]))
