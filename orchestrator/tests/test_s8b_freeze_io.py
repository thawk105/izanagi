# -*- coding: utf-8 -*-
"""中立 leaf ``s8b_freeze_io`` の loader 契約を characterization で固定する。

strictness は現行 (移行前 s8b_oracle_driver.load_verified_freeze) と同値である:
NaN/Infinity 拒否 + expected_hash 束縛 + top-level object 検査のみ。duplicate key
拒否・encoding 追加検査など現行に無い検査は足さない (F6/F7 裁定後の
load_ratified_freeze の責務)。各期待は現行実装が実際に返す/投げるものを実測して
pin している (期待の先決めをしない)。
"""
from __future__ import annotations

import ast
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
from orchestrator.calibrator import schema_v2 as calibration_v2  # noqa: E402
from test_schema_v2 import _valid_document as _valid_calibration_v2_document  # noqa: E402
from s8b_floor_evidence_fixture import fake_sort_swo_pass_attempt  # noqa: E402


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
# env 配線 (F4): ENV_TAG/NUMACTL/CLK は p2_2 直 import でなく registry 経由      #
# --------------------------------------------------------------------------- #

def test_s8b_drivers_no_longer_direct_import_p2_runtime_constants():
    """F4 結線後、S8b driver は p2_2 の runtime 定数を直接 import しない。"""
    from orchestrator.campaign import s8b_floor_campaign as floor
    from orchestrator.campaign import s8b_oracle_driver as oracle

    for module in (floor, oracle):
        tree = ast.parse(
            Path(module.__file__).read_text(encoding="utf-8"),
            filename=str(module.__file__),
        )
        direct_p2_2_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                direct_p2_2_imports.extend(
                    alias.name
                    for alias in node.names
                    if alias.name == "p2_2" or alias.name.endswith(".p2_2")
                )
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                if module_name == "p2_2" or module_name.endswith(".p2_2"):
                    direct_p2_2_imports.extend(
                        f"{module_name}:{alias.name}" for alias in node.names
                    )
                elif any(alias.name == "p2_2" for alias in node.names):
                    # Covers ``from . import p2_2`` and package re-export forms.
                    direct_p2_2_imports.extend(
                        f"{module_name or '.'}:{alias.name}"
                        for alias in node.names
                        if alias.name == "p2_2"
                    )
        assert direct_p2_2_imports == []

    assert not hasattr(floor, "NUMACTL")   # p2_2.NUMA の直 import は削除された
    assert not hasattr(floor, "CLK")       # p2_2.CLK の直 import も削除された
    assert not hasattr(floor, "ENV_TAG")   # machine-pin は site 起点へ分離された
    assert not hasattr(oracle, "MACHINE_ENV_TAG")
    assert floor._env_contract is not None  # env_contract を結線している


def test_measure_fn_closure_passes_contract_numactl_to_measure_point(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_measure_fn_closure_passes_contract_numactl_to_measure_point"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_measure_fn_closure_passes_contract_numactl_to_measure_point(tmp_path):
    """``measure_fn=None`` 経路の既定 closure が ``measure_point`` へ ``numactl`` /
    ``clocks_per_us`` を **contract から** 渡すことを実引数 spy で固定する (γ-14: closure ソース
    文字列検査でなく挙動検査)。"""
    from orchestrator.tests.s8b_v2_freeze_fixture import sealed_source_protection_fixture

    import contextlib
    from types import SimpleNamespace
    from unittest import mock

    from orchestrator.campaign import env_contract as ec
    from orchestrator.campaign import s8b_floor_campaign as floor
    from orchestrator.campaign.model import Genome
    from orchestrator.campaign.p2_2 import ENV_TAG
    from orchestrator.campaign.s1_direct_comparison import PreparedCell

    configs = ("stock_common", "sort_best")
    holdouts = {}
    for holdout_id, candidate_id, ratio in (
            ("rr80", "H1", "80"), ("rr20", "H2", "20")):
        entries = {
            c: {
                "holdout_id": holdout_id, "label": f"fx-{holdout_id}-{c}",
                "flags": {"BACK_OFF": i},
                **({
                    "comparator": (
                        "  sort(write_set_.begin(), write_set_.end(),\n"
                        "       [](const WriteElement<Tuple>& a, "
                        "const WriteElement<Tuple>& b) -> bool {\n"
                        "         return a.storage_ != b.storage_ ? "
                        "a.storage_ < b.storage_\n"
                        "                                         : "
                        "b.key_ < a.key_;\n"
                        "       });"
                    ),
                } if c == "sort_best" else {}),
            }
            for i, c in enumerate(configs)
        }
        holdouts[holdout_id] = {
            "candidate_id": candidate_id, "records": 730079, "threads": 17,
            "ycsb": {
                "ycsb_zipf_skew": "0.42", "ycsb_rratio": ratio,
                "ycsb_rmw": "1",
            },
            "variant_binding": {"entries": entries},
        }
    freeze = {"schema_version": floor.FREEZE_SCHEMA, "holdouts": holdouts}
    freeze_sha = hashlib.sha256(json.dumps(
        freeze, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    protocol = {
        "schema": floor.PROTOCOL_SCHEMA, "formula": floor.s8b_floor_stats.FORMULA_ID,
        "env_tag": ENV_TAG, "ccbench_pin": "0" * 40,
        "freeze": {
            "path": "output/s8b-freeze/holdout_freeze.json",
            "sha256": freeze_sha,
        },
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
    calibration_document = _valid_calibration_v2_document()
    calibration_document["env_tag"] = ENV_TAG
    calibration_document["acquisition_receipt"]["toolchain"].update({
        "compiler_path": "/fixture/toolchain/cc",
        "compiler_version": "fixture-cc 13.0\nfixture detail",
        "cmake_version": "fixture-cmake version 3.28\nfixture detail",
    })
    calibration_document["acquisition_receipt"]["ccbench"]["build_argv"] = [
        "cmake",
        "-DCMAKE_C_COMPILER=/fixture/toolchain/cc",
        "-DCMAKE_CXX_COMPILER=/fixture/toolchain/cxx",
    ]
    calibration = calibration_v2.validate_calibration_v2(calibration_document)
    calibration_raw = json.dumps(
        calibration_document, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    verified_calibration = floor.env_attestation.VerifiedCalibration(
        schema_version=calibration_v2.SCHEMA_VERSION,
        sha256=hashlib.sha256(calibration_raw).hexdigest(),
        calibration=calibration,
        attestation_profile_sha256=floor.env_attestation.profile_sha256(
            calibration.attestation_profile,
        ),
    )
    toolchain_manifest = {
        "cc": {
            "requested": "fixture-cc", "realpath": "/fixture/toolchain/cc",
            "version_first_line": "live-cc 13.0",
            "version": "live-cc 13.0\nfixture detail",
        },
        "cxx": {
            "requested": "fixture-cxx", "realpath": "/fixture/toolchain/cxx",
            "version_first_line": "live-cxx 13.0",
            "version": "live-cxx 13.0\nfixture detail",
        },
        "cmake": {
            "requested": "cmake", "realpath": "/fixture/toolchain/cmake",
            "version_first_line": "live-cmake version 3.28",
            "version": "live-cmake version 3.28\nfixture detail",
        },
    }

    def fixture_calibration_loader(observed_contract, _repo_root):
        assert observed_contract == contract
        return verified_calibration

    def fixture_observe_floor_tool(requested, role):
        assert requested == {
            "cc": "fixture-cc", "cxx": "fixture-cxx", "cmake": "cmake",
        }[role]
        entry = toolchain_manifest[role]
        return floor._ObservedFloorTool(
            requested=entry["requested"], realpath=entry["realpath"],
            version_first_line=entry["version_first_line"], version=entry["version"],
        )

    snapshot_base = tmp_path / "ccbench-snapshots"
    compiler_input_rel = "include/fixture.hh"
    fixture_cache_root = tmp_path / "cache"

    @contextlib.contextmanager
    def fake_prepare(cell, ccbench_pin, *, cxx):
        assert cxx == "fixture-cxx"
        cell_id = f"{cell['variant']['holdout_id']}::{cell['configuration']}"
        snapshot_root = snapshot_base / cell_id.replace("::", "__")
        compiler_input = snapshot_root / compiler_input_rel
        compiler_input.parent.mkdir(parents=True)
        compiler_input.write_bytes(
            f"compiler-input:{cell_id}\n".encode("utf-8")
        )
        yield PreparedCell(genome=Genome("silo", {}), src_token=cell_id,
                           ccbench_dir=str(snapshot_root),
                           cache_root=str(fixture_cache_root),
                           oracle_attempt=(
                               fake_sort_swo_pass_attempt()
                               if cell["configuration"] == "sort_best" else None
                           ))

    def fake_build(genome, ccbench_commit, trace, cache_root="", cc=None, cxx=None,
                   jobs=16, ccbench_dir="", src_token=None, contract=None,
                   expected_materialization_descriptor=None,
                   timeout_s=None, admission=None, build_context=None,
                   source_evidence=None, expected_toolchain_manifest=None):
        assert admission is not None
        assert build_context is not None
        assert source_evidence is not None
        assert expected_toolchain_manifest == toolchain_manifest
        expected_snapshot_root = snapshot_base / src_token.replace("::", "__")
        assert ccbench_dir == str(expected_snapshot_root)
        assert timeout_s == 900
        assert type(expected_materialization_descriptor) is (
            floor._expected_materialization.ExpectedMaterializationDescriptor
        )
        compiler_input = Path(ccbench_dir) / compiler_input_rel
        d = Path(cache_root) / "fixture" / src_token.replace("::", "__")
        d.mkdir(parents=True, exist_ok=True)
        b = d / "ycsb.exe"
        payload = src_token.encode()
        b.write_bytes(payload)
        sha = hashlib.sha256(payload).hexdigest()
        compiler_input_manifest = {
            "schema_version": "s8b-compiler-input/v1",
            "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
            "target": f"ycsb_{genome.protocol}.exe",
            "depfile_count": 1,
            "inputs": [{
                "path": compiler_input_rel,
                "sha256": hashlib.sha256(compiler_input.read_bytes()).hexdigest(),
            }],
        }
        compiler_input_manifest_sha256 = hashlib.sha256(json.dumps(
            compiler_input_manifest, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        # Measurement wiring needs an admitted binary; no compile is claimed.
        source_protection = sealed_source_protection_fixture(
            source=source_evidence, binary_sha256=sha,
            compiler_input_manifest_sha256=compiler_input_manifest_sha256,
        )
        expected_materialization_sha256 = (
            source_protection.expected_materialization_sha256
        )
        return SimpleNamespace(source_protection=source_protection,
                               binary=str(b), bin_sha256=sha, bin_hash=sha[:16],
                               configure_cmd="#", build_cmd="#", cached=False,
                               configure_argv=[
                                   "cmake", "-S", ccbench_dir, "-B", str(d)],
                               build_argv=["cmake", "--build", str(d)],
                               ccbench_root=ccbench_dir,
                               contract_sha256=contract.contract_sha256,
                               compiler_input_manifest=compiler_input_manifest,
                               compiler_input_manifest_sha256=(
                                   compiler_input_manifest_sha256
                               ),
                               source_snapshot_sha256=(
                                   expected_materialization_sha256
                               ),
                               expected_materialization_sha256=(
                                   expected_materialization_sha256
                               ))

    seen = {}

    def fixture_perf_preflight(**_kwargs):
        events = ["LLC-load-misses", "LLC-loads", "instructions", "cycles"]
        return {
            "schema": "izanagi-perf-preflight/v1", "status": "available",
            "available": True,
            "probe_argv": [
                "perf", "stat", "-x,", "-o", "<tmp>/perf.csv",
                "-e", ",".join(events), "--", "/bin/true",
            ],
            "rc": 0, "parsed_events": events, "reason": "available",
            "stderr_sha256": hashlib.sha256(b"").hexdigest(),
            "candidates": [],
        }

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

    authority = tmp_path / "holdout-authority"
    authority.mkdir()
    subprocess.run(
        ["git", "-C", str(authority), "init"], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    fixed = authority / "output/s8b-freeze"
    fixed.mkdir(parents=True)
    normalized_protocol = floor.validate_protocol(protocol)
    (fixed / "floor_protocol.json").write_text(
        json.dumps(
            normalized_protocol, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ), encoding="utf-8",
    )
    (fixed / "holdout_freeze.json").write_text(
        json.dumps(
            freeze, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ), encoding="utf-8",
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

    with mock.patch.object(
            floor, "_machine_env_tag_for_site", return_value=contract.env_tag), \
         mock.patch.object(
            floor.env_attestation, "load_verified_calibration",
            side_effect=fixture_calibration_loader), \
         mock.patch.object(
             floor.buildcache, "compilers_for_current_site",
             return_value=("fixture-cc", "fixture-cxx")), \
         mock.patch.object(
             floor, "_observe_floor_tool", side_effect=fixture_observe_floor_tool), \
         mock.patch.object(floor.buildcache, "build_v2", fake_build), \
         mock.patch.object(floor.source_digest, "resolve_evidence", fixture_evidence), \
         mock.patch.object(floor, "measure_point", spy_measure_point):
        floor._run_campaign_core(
            protocol, verified, out_root=tmp_path / "out", mode="pilot",
            measure_fn=None, probe_fn=lambda: (1, "", ""),
            perf_preflight_fn=fixture_perf_preflight,
            prepare_fn=fake_prepare, now_fn=lambda: __import__("datetime")
            .datetime(2026, 1, 1, tzinfo=__import__("datetime").timezone.utc),
            monotonic_fn=lambda: 0.0,
            durable_root_policy=floor.DurableRootPolicy(
                approved_roots=(tmp_path.resolve(),), forbidden_roots=()),
            _holdout_repo_root=authority,
            _holdout_signature_source=holdouts,
        )
    assert seen["clocks_per_us"] == contract.clocks_per_us
    assert seen["numactl"] == list(contract.numactl)


if __name__ == "__main__":
    # 自走 harness: `python3 test_s8b_freeze_io.py` で実際に pytest を回す (素の runner
    # による 0 件実行の偽緑を防ぐ。test_plain_runner_coverage の契約)。
    sys.exit(pytest.main([__file__, "-q"]))
