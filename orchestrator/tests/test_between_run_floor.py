# -*- coding: utf-8 -*-
"""between_run_floor の単一テナント admission が F3 強化 (path 非依存 pgrep) の
波及を受けることを確認する (レーン B 付録3、machine 非依存・モックのみ)。

between_run_floor.py は `_assert_single_tenant` を campaign.p2_2 から素通しで使う
(自身に admission ロジックを持たない)。p2_2._assert_single_tenant は内部で
calibrator.runner.competing_bench_pids を呼ぶ一本道なので、runner 側の検知強化は
between_run_floor 側のコード変更なしに効く — それをここで固定する。
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.calibrator import runner                          # noqa: E402
from orchestrator.campaign import between_run_floor                 # noqa: E402
from orchestrator.campaign.genome import space_for                  # noqa: E402
from orchestrator.campaign.p2_2 import _assert_single_tenant         # noqa: E402


def _floor_result():
    return {
        "genome": "silo:BACK_OFF=0",
        "records": 1_000_000,
        "threads": 48,
        "clocks_per_us": 1800,
        "abort_rate": 0.0,
        "run_cmd": "/fixture/benchmark",
        "within_run": {
            "reps": 10, "cv": 0.01, "median": 100.0, "mean": 100.0,
        },
        "between_run": {
            "sessions": 8, "reps_per_session": 5, "cv": 0.02,
            "median": 100.0, "mean": 100.0, "stdev": 2.0,
            "session_throughputs": [100.0] * 8,
            "high_variance": False, "notes": [],
        },
    }


def _restore_env(name, previous):
    if previous is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = previous


def test_between_run_floor_uses_p2_2_assert_single_tenant():
    """between_run_floor モジュールが campaign.p2_2._assert_single_tenant を
    そのまま import して使っていること (between_run_floor 独自の admission 経路が
    無いこと) を固定する — F3 強化は runner.competing_bench_pids 一箇所を直せば
    between_run_floor にも波及する、という設計前提の裏付け。"""
    assert between_run_floor._assert_single_tenant is _assert_single_tenant


def test_between_run_floor_admission_detects_s8b_build_cache_orphan_via_runner_fix():
    """**配線 (routing) の固定**: competing_bench_pids が非空を返したとき、
    between_run_floor が呼ぶ p2_2._assert_single_tenant がその結果を素通しで受け取り
    拒否まで波及することを確認する。

    ここでは competing_bench_pids そのものを fake で置換しているため、F3 の
    path 非依存パターンによる**実検知**は検証しない (fixture の orphan_line は
    「s8b-build-cache 配下の孤児が返った」状況を模した入力にすぎない)。実 pgrep
    越しの検知は test_calibrator.py::
    test_competing_bench_pids_real_orphan_under_s8b_build_cache_detected が担い、
    本テストは between-run floor の admission 経路がその検知結果に依存して
    fails-closed する配線だけを固定する (検知強化を 1 箇所直せば floor driver にも
    波及する、という設計前提の裏付け)。"""
    orphan_line = "31415 /out/env/pegasus/s8b-build-cache/gen3/ycsb_orphan.exe"

    def fake_competing_bench_pids():
        return [orphan_line]

    orig = runner.competing_bench_pids
    runner.competing_bench_pids = fake_competing_bench_pids
    try:
        raised = False
        try:
            between_run_floor._assert_single_tenant()
        except RuntimeError as e:
            raised = True
            assert orphan_line in str(e)
        assert raised, ("competing_bench_pids の非空結果が "
                        "between_run_floor の admission (拒否) まで波及しなかった")
    finally:
        runner.competing_bench_pids = orig


def test_between_run_floor_admission_passes_when_no_competitor():
    """競合なしなら between_run_floor 側の admission も通過する (回帰確認)。"""
    orig = runner.competing_bench_pids
    runner.competing_bench_pids = lambda: []
    try:
        between_run_floor._assert_single_tenant()   # 例外を出さないこと
    finally:
        runner.competing_bench_pids = orig


def test_selected_env_tag_rejects_unknown_value():
    previous = os.environ.get(between_run_floor.ENV_TAG_OVERRIDE)
    os.environ[between_run_floor.ENV_TAG_OVERRIDE] = "unsupported-site"
    try:
        try:
            between_run_floor._selected_env_tag()
        except ValueError as caught:
            assert between_run_floor.ENV_TAG_OVERRIDE in str(caught)
        else:
            assert False, "不正な env tag を受理した"
    finally:
        _restore_env(between_run_floor.ENV_TAG_OVERRIDE, previous)


def test_selected_env_tag_defaults_to_linux_baremetal_profile():
    previous = os.environ.get(between_run_floor.ENV_TAG_OVERRIDE)
    os.environ.pop(between_run_floor.ENV_TAG_OVERRIDE, None)
    try:
        selected = between_run_floor._selected_env_tag()
        assert selected == between_run_floor.DEFAULT_ENV_TAG
        assert selected == "linux-baremetal"
    finally:
        _restore_env(between_run_floor.ENV_TAG_OVERRIDE, previous)


def test_pegasus_measurement_profile_uses_2100_without_numactl():
    assert between_run_floor._measurement_profile(
        between_run_floor.PEGASUS_ENV_TAG,
    ) == (2100, [])


def test_write_out_uses_selected_pegasus_environment_path():
    result = _floor_result()
    workload = {
        "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0",
    }
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp_dir = Path(raw_tmp)
        seen = []
        original_scope_dir = between_run_floor.env_scope_dir
        between_run_floor.env_scope_dir = (
            lambda env_tag: seen.append(env_tag) or str(tmp_dir / env_tag)
        )
        try:
            path = between_run_floor._write_out(
                "read-heavy", workload, result,
                env_tag=between_run_floor.PEGASUS_ENV_TAG, log=lambda *_args: None,
            )
        finally:
            between_run_floor.env_scope_dir = original_scope_dir

        output_path = Path(path)
        assert seen == [between_run_floor.PEGASUS_ENV_TAG]
        assert output_path.parent == (
            tmp_dir / between_run_floor.PEGASUS_ENV_TAG / "calibration"
        )
        assert "registered" not in output_path.parts


def test_protocol_output_stem_preserves_silo_and_names_mocc():
    workload = {
        "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0",
    }
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp_dir = Path(raw_tmp)
        original_scope_dir = between_run_floor.env_scope_dir
        between_run_floor.env_scope_dir = lambda _env_tag: str(tmp_dir)
        try:
            silo_path = Path(between_run_floor._write_out(
                "read-heavy", workload, _floor_result(), protocol="silo",
                log=lambda *_args: None,
            ))
            mocc_path = Path(between_run_floor._write_out(
                "read-heavy", workload, {
                    **_floor_result(),
                    "genome": between_run_floor.BASELINES["mocc"].canonical(),
                }, protocol="mocc", log=lambda *_args: None,
            ))
        finally:
            between_run_floor.env_scope_dir = original_scope_dir
    assert silo_path.name == "between_run_noise_t48_skew0p9_rr95_rmw0.json"
    assert mocc_path.name == "between_run_noise_mocc_t48_skew0p9_rr95_rmw0.json"


def test_write_out_is_create_only_and_preserves_existing_bytes():
    workload = {
        "ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0",
    }
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp_dir = Path(raw_tmp)
        calibration = tmp_dir / "calibration"
        calibration.mkdir()
        existing = calibration / "between_run_noise_t48_skew0p9_rr50_rmw0.json"
        existing.write_bytes(b"historical-floor-bytes\n")
        original_scope_dir = between_run_floor.env_scope_dir
        between_run_floor.env_scope_dir = lambda _env_tag: str(tmp_dir)
        try:
            try:
                between_run_floor._write_out(
                    "balanced", workload, _floor_result(), protocol="silo",
                    log=lambda *_args: None,
                )
            except FileExistsError as caught:
                assert "create-only" in str(caught)
            else:
                assert False, "既存 between-run floor を上書き可能だった"
        finally:
            between_run_floor.env_scope_dir = original_scope_dir
        assert existing.read_bytes() == b"historical-floor-bytes\n"
        assert not existing.with_suffix(".md").exists()


def test_write_out_rolls_back_json_when_markdown_creation_fails():
    workload = {
        "ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0",
    }
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp_dir = Path(raw_tmp)
        original_scope_dir = between_run_floor.env_scope_dir
        original_open = open

        def fail_markdown_creation(path, mode="r", *args, **kwargs):
            if mode == "x" and str(path).endswith(".md"):
                raise OSError("injected second-file creation failure")
            return original_open(path, mode, *args, **kwargs)

        between_run_floor.env_scope_dir = lambda _env_tag: str(tmp_dir)
        between_run_floor.open = fail_markdown_creation
        try:
            try:
                between_run_floor._write_out(
                    "balanced", workload, _floor_result(), protocol="silo",
                    log=lambda *_args: None,
                )
            except OSError as caught:
                assert "second-file" in str(caught)
            else:
                assert False, "Markdown 作成失敗を無視した"
        finally:
            between_run_floor.env_scope_dir = original_scope_dir
            del between_run_floor.open
        assert list((tmp_dir / "calibration").iterdir()) == []


def test_trace_hook_admission_is_bound_to_source_facts():
    assert between_run_floor._protocol_source_has_trace_hook_evidence_only("silo")
    assert not between_run_floor._protocol_source_has_trace_hook_evidence_only("mocc")
    assert not between_run_floor._protocol_source_has_trace_hook_evidence_only("tictoc")


def test_trace_hook_admission_requires_readable_cmake_sources():
    with tempfile.TemporaryDirectory() as raw_tmp:
        root = Path(raw_tmp)
        protocol_dir = root / "cc" / "mocc"
        protocol_dir.mkdir(parents=True)
        (protocol_dir / "transaction.cc").write_text(
            '#include "../../include/trace.hh"\n'
            "#if TRACE\n"
            "izanagi_trace::emit_abort(1);\n"
            "#endif\n",
            encoding="utf-8",
        )
        assert not between_run_floor._protocol_source_has_trace_hook_evidence_only(
            "mocc", root,
        )


def test_trace_hook_admission_ignores_uncompiled_source():
    with tempfile.TemporaryDirectory() as raw_tmp:
        root = Path(raw_tmp)
        protocol_dir = root / "cc" / "mocc"
        protocol_dir.mkdir(parents=True)
        (protocol_dir / "CMakeLists.txt").write_text(
            "ccbench_add_protocol(mocc\n"
            "  SOURCES transaction.cc\n"
            "  WORKLOADS ycsb\n"
            ")\n",
            encoding="utf-8",
        )
        (protocol_dir / "transaction.cc").write_text(
            "void compiled_without_trace() {}\n", encoding="utf-8",
        )
        (protocol_dir / "decoy.cc").write_text(
            '#include "../../include/trace.hh"\n'
            "#if TRACE\n"
            "izanagi_trace::emit_abort(1);\n"
            "#endif\n",
            encoding="utf-8",
        )
        assert not between_run_floor._protocol_source_has_trace_hook_evidence_only(
            "mocc", root,
        )


def test_trace_hook_admission_accepts_listed_source():
    with tempfile.TemporaryDirectory() as raw_tmp:
        root = Path(raw_tmp)
        protocol_dir = root / "cc" / "mocc"
        protocol_dir.mkdir(parents=True)
        (protocol_dir / "CMakeLists.txt").write_text(
            "ccbench_add_protocol(mocc\n"
            "  SOURCES transaction.cc\n"
            "  WORKLOADS ycsb\n"
            ")\n",
            encoding="utf-8",
        )
        (protocol_dir / "transaction.cc").write_text(
            '#include "../../include/trace.hh"\n'
            "#if TRACE\n"
            "izanagi_trace::emit_abort(1);\n"
            "#endif\n",
            encoding="utf-8",
        )
        assert between_run_floor._protocol_source_has_trace_hook_evidence_only(
            "mocc", root,
        )


def test_trace_hook_admission_preserves_parent_relative_cmake_source():
    """D1373 accepted ``../`` CMake sources before the shared scanner."""
    with tempfile.TemporaryDirectory() as raw_tmp:
        root = Path(raw_tmp)
        protocol_dir = root / "cc/mocc"
        protocol_dir.mkdir(parents=True)
        (protocol_dir / "CMakeLists.txt").write_text(
            "ccbench_add_protocol(mocc SOURCES ../shared.cc WORKLOADS ycsb)\n",
            encoding="utf-8",
        )
        (root / "cc/shared.cc").write_text(
            '#include "../include/trace.hh"\n'
            "#if TRACE\n"
            "izanagi_trace::emit_abort(1);\n"
            "#endif\n",
            encoding="utf-8",
        )
        assert between_run_floor._protocol_source_has_trace_hook_evidence_only(
            "mocc", root,
        )


def test_trace_hook_admission_preserves_absolute_cmake_source():
    """D1373 accepted absolute CMake sources before the shared scanner."""
    with tempfile.TemporaryDirectory() as raw_tmp:
        root = Path(raw_tmp)
        protocol_dir = root / "cc/mocc"
        protocol_dir.mkdir(parents=True)
        source = root / "absolute.cc"
        source.write_text(
            '#include "include/trace.hh"\n'
            "#if TRACE\n"
            "izanagi_trace::emit_abort(1);\n"
            "#endif\n",
            encoding="utf-8",
        )
        (protocol_dir / "CMakeLists.txt").write_text(
            f"ccbench_add_protocol(mocc SOURCES {source} WORKLOADS ycsb)\n",
            encoding="utf-8",
        )
        assert between_run_floor._protocol_source_has_trace_hook_evidence_only(
            "mocc", root,
        )


def test_trace_hook_admission_rejects_commented_out_hook():
    with tempfile.TemporaryDirectory() as raw_tmp:
        root = Path(raw_tmp)
        protocol_dir = root / "cc" / "mocc"
        protocol_dir.mkdir(parents=True)
        (protocol_dir / "CMakeLists.txt").write_text(
            "ccbench_add_protocol(mocc SOURCES transaction.cc WORKLOADS ycsb)\n",
            encoding="utf-8",
        )
        (protocol_dir / "transaction.cc").write_text(
            '#include "../../include/trace.hh"\n'
            "#if TRACE\n"
            "// izanagi_trace::emit_abort(1);\n"
            "#endif\n",
            encoding="utf-8",
        )
        assert not between_run_floor._protocol_source_has_trace_hook_evidence_only(
            "mocc", root,
        )


def test_trace_hook_admission_rejects_hook_only_in_if_zero():
    with tempfile.TemporaryDirectory() as raw_tmp:
        root = Path(raw_tmp)
        protocol_dir = root / "cc" / "mocc"
        protocol_dir.mkdir(parents=True)
        (protocol_dir / "CMakeLists.txt").write_text(
            "ccbench_add_protocol(mocc SOURCES transaction.cc WORKLOADS ycsb)\n",
            encoding="utf-8",
        )
        (protocol_dir / "transaction.cc").write_text(
            '#include "../../include/trace.hh"\n'
            "#if TRACE\n"
            "#if 0\n"
            "izanagi_trace::emit_abort(1);\n"
            "#endif\n"
            "#endif\n",
            encoding="utf-8",
        )
        assert not between_run_floor._protocol_source_has_trace_hook_evidence_only(
            "mocc", root,
        )


def test_trace_hook_admission_rejects_hook_after_nested_if_inside_if_zero():
    with tempfile.TemporaryDirectory() as raw_tmp:
        root = Path(raw_tmp)
        protocol_dir = root / "cc" / "mocc"
        protocol_dir.mkdir(parents=True)
        (protocol_dir / "CMakeLists.txt").write_text(
            "ccbench_add_protocol(mocc SOURCES transaction.cc WORKLOADS ycsb)\n",
            encoding="utf-8",
        )
        (protocol_dir / "transaction.cc").write_text(
            '#include "../../include/trace.hh"\n'
            "#if TRACE\n"
            "void trace_guard_marker() {}\n"
            "#endif\n"
            "#if 0\n"
            "#if TRACE\n"
            "void nested_dead_code() {}\n"
            "#endif\n"
            "izanagi_trace::emit_abort(1);\n"
            "#endif\n",
            encoding="utf-8",
        )
        assert not between_run_floor._protocol_source_has_trace_hook_evidence_only(
            "mocc", root,
        )


def test_mocc_floor_rejected_before_build_or_measure_without_trace_hook():
    calls = []
    originals = {
        "tenant": between_run_floor._assert_single_tenant,
        "context": between_run_floor.build_run_context,
        "evidence": between_run_floor.source_digest.resolve_evidence,
        "admission": between_run_floor.derive_build_admission,
        "build": between_run_floor.buildcache.build,
        "measure": between_run_floor.measure_point_floor,
        "write": between_run_floor._write_out,
    }
    between_run_floor._assert_single_tenant = lambda: calls.append("tenant")
    between_run_floor.build_run_context = lambda **_kwargs: object()
    between_run_floor.source_digest.resolve_evidence = (
        lambda *_args, **_kwargs: object()
    )
    between_run_floor.derive_build_admission = lambda *_args: object()
    between_run_floor.buildcache.build = lambda *_args, **_kwargs: (
        calls.append("build") or SimpleNamespace(cached=True, binary="/fixture/mocc")
    )
    between_run_floor.measure_point_floor = lambda *_args, **_kwargs: (
        calls.append("measure") or {
            "abort_rate": 0.0,
            "within_run": {"cv": 0.01},
            "between_run": {"cv": 0.02},
        }
    )
    between_run_floor._write_out = lambda *_args, **_kwargs: calls.append("write")
    try:
        try:
            between_run_floor.main(["prog", "read-heavy", "--protocol", "mocc"])
        except ValueError as caught:
            assert "trace hook" in str(caught)
        else:
            assert False, "trace hook のない mocc floor が受理された"
    finally:
        between_run_floor._assert_single_tenant = originals["tenant"]
        between_run_floor.build_run_context = originals["context"]
        between_run_floor.source_digest.resolve_evidence = originals["evidence"]
        between_run_floor.derive_build_admission = originals["admission"]
        between_run_floor.buildcache.build = originals["build"]
        between_run_floor.measure_point_floor = originals["measure"]
        between_run_floor._write_out = originals["write"]
    assert calls == []


def test_hook_bearing_source_routes_mocc_baseline_through_main():
    calls = {"build": [], "measure": [], "write": []}
    originals = {
        "root": between_run_floor.CCBENCH_ROOT,
        "tenant": between_run_floor._assert_single_tenant,
        "context": between_run_floor.build_run_context,
        "evidence": between_run_floor.source_digest.resolve_evidence,
        "admission": between_run_floor.derive_build_admission,
        "build": between_run_floor.buildcache.build,
        "measure": between_run_floor.measure_point_floor,
        "write": between_run_floor._write_out,
    }
    with tempfile.TemporaryDirectory() as raw_tmp:
        root = Path(raw_tmp)
        protocol_dir = root / "cc" / "mocc"
        protocol_dir.mkdir(parents=True)
        (protocol_dir / "CMakeLists.txt").write_text(
            "ccbench_add_protocol(mocc SOURCES transaction.cc WORKLOADS ycsb)\n",
            encoding="utf-8",
        )
        (protocol_dir / "transaction.cc").write_text(
            '#include "../../include/trace.hh"\n'
            "#if TRACE\n"
            "izanagi_trace::emit_abort(1);\n"
            "#endif\n",
            encoding="utf-8",
        )
        between_run_floor.CCBENCH_ROOT = root
        between_run_floor._assert_single_tenant = lambda: None
        between_run_floor.build_run_context = lambda **_kwargs: object()
        between_run_floor.source_digest.resolve_evidence = (
            lambda *_args, **_kwargs: object()
        )
        between_run_floor.derive_build_admission = lambda *_args: object()

        def fake_build(candidate, **_kwargs):
            calls["build"].append(candidate)
            return SimpleNamespace(cached=True, binary="/fixture/mocc")

        def fake_measure(_binary, _workload, *, baseline, **_kwargs):
            calls["measure"].append(baseline)
            return {
                "abort_rate": 0.0,
                "within_run": {"cv": 0.01},
                "between_run": {"cv": 0.02},
            }

        between_run_floor.buildcache.build = fake_build
        between_run_floor.measure_point_floor = fake_measure
        between_run_floor._write_out = (
            lambda *_args, **kwargs: calls["write"].append(kwargs["protocol"])
        )
        try:
            assert between_run_floor.main(
                ["prog", "read-heavy", "--protocol", "mocc"]
            ) == 0
        finally:
            between_run_floor.CCBENCH_ROOT = originals["root"]
            between_run_floor._assert_single_tenant = originals["tenant"]
            between_run_floor.build_run_context = originals["context"]
            between_run_floor.source_digest.resolve_evidence = originals["evidence"]
            between_run_floor.derive_build_admission = originals["admission"]
            between_run_floor.buildcache.build = originals["build"]
            between_run_floor.measure_point_floor = originals["measure"]
            between_run_floor._write_out = originals["write"]
    expected = between_run_floor.BASELINES["mocc"]
    assert calls == {"build": [expected], "measure": [expected], "write": ["mocc"]}


def test_pegasus_build_passes_site_aware_compilers():
    previous = os.environ.get(between_run_floor.ENV_TAG_OVERRIDE)
    os.environ[between_run_floor.ENV_TAG_OVERRIDE] = between_run_floor.PEGASUS_ENV_TAG
    calls = {"compiler": 0, "evidence": [], "build": []}
    originals = {
        "assert_single_tenant": between_run_floor._assert_single_tenant,
        "build_run_context": between_run_floor.build_run_context,
        "resolve_evidence": between_run_floor.source_digest.resolve_evidence,
        "derive_build_admission": between_run_floor.derive_build_admission,
        "compilers": between_run_floor.buildcache.compilers_for_current_site,
        "build": between_run_floor.buildcache.build,
        "measure": between_run_floor.measure_point_floor,
        "write": between_run_floor._write_out,
    }

    def fake_compilers():
        calls["compiler"] += 1
        return "pegasus-cc", "pegasus-cxx"

    def fake_evidence(*args, **kwargs):
        calls["evidence"].append((args, kwargs))
        return object()

    def fake_build(*args, **kwargs):
        calls["build"].append((args, kwargs))
        return SimpleNamespace(cached=True, binary="/fixture/pegasus-binary")

    between_run_floor._assert_single_tenant = lambda: None
    between_run_floor.build_run_context = lambda **_kwargs: object()
    between_run_floor.source_digest.resolve_evidence = fake_evidence
    between_run_floor.derive_build_admission = lambda *_args: object()
    between_run_floor.buildcache.compilers_for_current_site = fake_compilers
    between_run_floor.buildcache.build = fake_build
    between_run_floor.measure_point_floor = (
        lambda *_args, **_kwargs: _floor_result()
    )
    between_run_floor._write_out = lambda *_args, **_kwargs: None
    try:
        assert between_run_floor.main(["prog", "read-heavy"]) == 0
    finally:
        between_run_floor._assert_single_tenant = originals["assert_single_tenant"]
        between_run_floor.build_run_context = originals["build_run_context"]
        between_run_floor.source_digest.resolve_evidence = originals["resolve_evidence"]
        between_run_floor.derive_build_admission = originals["derive_build_admission"]
        between_run_floor.buildcache.compilers_for_current_site = originals["compilers"]
        between_run_floor.buildcache.build = originals["build"]
        between_run_floor.measure_point_floor = originals["measure"]
        between_run_floor._write_out = originals["write"]
        _restore_env(between_run_floor.ENV_TAG_OVERRIDE, previous)

    assert calls["compiler"] == 1
    assert len(calls["evidence"]) == 1
    assert calls["evidence"][0][1]["cxx"] == "pegasus-cxx"
    assert len(calls["build"]) == 1
    assert calls["build"][0][1]["cc"] == "pegasus-cc"
    assert calls["build"][0][1]["cxx"] == "pegasus-cxx"


def test_pegasus_main_disables_perf_for_floor_measurement():
    previous = os.environ.get(between_run_floor.ENV_TAG_OVERRIDE)
    os.environ[between_run_floor.ENV_TAG_OVERRIDE] = between_run_floor.PEGASUS_ENV_TAG
    calls = {"measure": [], "write": []}
    originals = {
        "assert_single_tenant": between_run_floor._assert_single_tenant,
        "build_run_context": between_run_floor.build_run_context,
        "resolve_evidence": between_run_floor.source_digest.resolve_evidence,
        "derive_build_admission": between_run_floor.derive_build_admission,
        "compilers": between_run_floor.buildcache.compilers_for_current_site,
        "build": between_run_floor.buildcache.build,
        "measure": between_run_floor.measure_point_floor,
        "write": between_run_floor._write_out,
    }

    def fake_measure(*args, **kwargs):
        calls["measure"].append((args, kwargs))
        return _floor_result()

    between_run_floor._assert_single_tenant = lambda: None
    between_run_floor.build_run_context = lambda **_kwargs: object()
    between_run_floor.source_digest.resolve_evidence = lambda *_args, **_kwargs: object()
    between_run_floor.derive_build_admission = lambda *_args: object()
    between_run_floor.buildcache.compilers_for_current_site = (
        lambda: ("pegasus-cc", "pegasus-cxx")
    )
    between_run_floor.buildcache.build = lambda *_args, **_kwargs: SimpleNamespace(
        cached=True, binary="/fixture/pegasus-binary"
    )
    between_run_floor.measure_point_floor = fake_measure
    between_run_floor._write_out = lambda *args, **kwargs: calls["write"].append(
        (args, kwargs)
    )
    try:
        assert between_run_floor.main(["prog", "read-heavy"]) == 0
    finally:
        between_run_floor._assert_single_tenant = originals["assert_single_tenant"]
        between_run_floor.build_run_context = originals["build_run_context"]
        between_run_floor.source_digest.resolve_evidence = originals["resolve_evidence"]
        between_run_floor.derive_build_admission = originals["derive_build_admission"]
        between_run_floor.buildcache.compilers_for_current_site = originals["compilers"]
        between_run_floor.buildcache.build = originals["build"]
        between_run_floor.measure_point_floor = originals["measure"]
        between_run_floor._write_out = originals["write"]
        _restore_env(between_run_floor.ENV_TAG_OVERRIDE, previous)

    assert len(calls["measure"]) == 1
    assert calls["measure"][0][1].get("use_perf") is False


def test_main_rejects_extra_arguments_before_campaign_work():
    calls = []
    originals = {
        "assert_single_tenant": between_run_floor._assert_single_tenant,
        "build_run_context": between_run_floor.build_run_context,
        "resolve_evidence": between_run_floor.source_digest.resolve_evidence,
        "derive_build_admission": between_run_floor.derive_build_admission,
        "build": between_run_floor.buildcache.build,
        "measure": between_run_floor.measure_point_floor,
        "write": between_run_floor._write_out,
    }

    def record(name, result=None):
        def fake(*_args, **_kwargs):
            calls.append(name)
            return result
        return fake

    between_run_floor._assert_single_tenant = record("admission")
    between_run_floor.build_run_context = record("build_context", object())
    between_run_floor.source_digest.resolve_evidence = record("evidence", object())
    between_run_floor.derive_build_admission = record("build_admission", object())
    between_run_floor.buildcache.build = record(
        "build", SimpleNamespace(cached=True, binary="/fixture/binary"))
    between_run_floor.measure_point_floor = record(
        "measure", {
            "abort_rate": 0.0,
            "within_run": {"cv": 0.01},
            "between_run": {"cv": 0.02},
        })
    between_run_floor._write_out = record("write")
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stderr(stderr):
            result = between_run_floor.main(["prog", "write-heavy", "extra"])
    finally:
        between_run_floor._assert_single_tenant = originals["assert_single_tenant"]
        between_run_floor.build_run_context = originals["build_run_context"]
        between_run_floor.source_digest.resolve_evidence = originals["resolve_evidence"]
        between_run_floor.derive_build_admission = originals["derive_build_admission"]
        between_run_floor.buildcache.build = originals["build"]
        between_run_floor.measure_point_floor = originals["measure"]
        between_run_floor._write_out = originals["write"]

    assert result == 2
    assert "usage:" in stderr.getvalue()
    assert calls == []


def test_main_accepts_one_known_point_without_running_real_campaign():
    written = []
    result_data = {
        "abort_rate": 0.0,
        "within_run": {"cv": 0.01},
        "between_run": {"cv": 0.02},
    }
    originals = {
        "assert_single_tenant": between_run_floor._assert_single_tenant,
        "build_run_context": between_run_floor.build_run_context,
        "resolve_evidence": between_run_floor.source_digest.resolve_evidence,
        "derive_build_admission": between_run_floor.derive_build_admission,
        "build": between_run_floor.buildcache.build,
        "measure": between_run_floor.measure_point_floor,
        "write": between_run_floor._write_out,
    }
    between_run_floor._assert_single_tenant = lambda: None
    between_run_floor.build_run_context = lambda **_kwargs: object()
    between_run_floor.source_digest.resolve_evidence = lambda *_args, **_kwargs: object()
    between_run_floor.derive_build_admission = lambda *_args, **_kwargs: object()
    between_run_floor.buildcache.build = lambda *_args, **_kwargs: SimpleNamespace(
        cached=True, binary="/fixture/binary")
    between_run_floor.measure_point_floor = (
        lambda _binary, _workload, *, baseline: result_data
    )
    between_run_floor._write_out = (
        lambda tag, workload, result, *, protocol: written.append(
            (tag, workload, result, protocol)
        ))
    try:
        result = between_run_floor.main(["prog", "write-heavy"])
    finally:
        between_run_floor._assert_single_tenant = originals["assert_single_tenant"]
        between_run_floor.build_run_context = originals["build_run_context"]
        between_run_floor.source_digest.resolve_evidence = originals["resolve_evidence"]
        between_run_floor.derive_build_admission = originals["derive_build_admission"]
        between_run_floor.buildcache.build = originals["build"]
        between_run_floor.measure_point_floor = originals["measure"]
        between_run_floor._write_out = originals["write"]

    assert result == 0
    assert len(written) == 1 and written[0][0] == "write-heavy"


def test_measure_point_floor_returns_versioned_receipt_with_mock_measurements():
    class Stats:
        cv = 0.01
        median = 100.0
        mean = 101.0
        stdev = 1.0
        throughputs = [100.0, 101.0]
        sessions = 8
        reps_per_session = 5
        session_throughputs = [100.0, 101.0]
        high_variance = False
        notes = []

    class Point:
        abort_rate = 0.2
        run_cmd = "/fixture/benchmark"
        throughputs = [100.0, 101.0]
        throughput = 100.0

    original_measure = between_run_floor.measure_point
    original_noise_floor = between_run_floor.noise_floor
    original_between = between_run_floor.between_run_noise_floor
    between_run_floor.measure_point = lambda *_args, **_kwargs: Point()
    between_run_floor.noise_floor = lambda _throughputs: Stats()

    def fake_between(measure_session, *, settle_fn, sessions):
        assert settle_fn is between_run_floor._assert_single_tenant
        assert sessions == between_run_floor.SESSIONS
        [measure_session() for _ in range(sessions)]
        return Stats()

    between_run_floor.between_run_noise_floor = fake_between
    try:
        result = between_run_floor.measure_point_floor(
            "/fixture/binary", {"ycsb_rratio": "50", "ycsb_zipf_skew": "0.9",
                                "ycsb_rmw": "0"}, log=lambda *_args: None)
    finally:
        between_run_floor.measure_point = original_measure
        between_run_floor.noise_floor = original_noise_floor
        between_run_floor.between_run_noise_floor = original_between

    assert "schema_version" in result
    assert result["schema_version"] == "between-run-noise-floor/v1"


def test_main_build_failure_does_not_write_success_json():
    expected = RuntimeError("fixture build failure")
    writes = []
    originals = {
        "assert_single_tenant": between_run_floor._assert_single_tenant,
        "build_run_context": between_run_floor.build_run_context,
        "resolve_evidence": between_run_floor.source_digest.resolve_evidence,
        "derive_build_admission": between_run_floor.derive_build_admission,
        "build": between_run_floor.buildcache.build,
        "measure": between_run_floor.measure_point_floor,
        "write": between_run_floor._write_out,
    }
    between_run_floor._assert_single_tenant = lambda: None
    between_run_floor.build_run_context = lambda **_kwargs: object()
    between_run_floor.source_digest.resolve_evidence = lambda *_args, **_kwargs: object()
    between_run_floor.derive_build_admission = lambda *_args, **_kwargs: object()
    between_run_floor.buildcache.build = lambda *_args, **_kwargs: (_ for _ in ()).throw(expected)
    between_run_floor.measure_point_floor = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("measurement reached after build failure"))
    between_run_floor._write_out = lambda *args, **kwargs: writes.append((args, kwargs))
    try:
        try:
            between_run_floor.main(["prog", "write-heavy"])
        except RuntimeError as caught:
            assert caught is expected
        else:
            assert False, "build exception was swallowed"
    finally:
        between_run_floor._assert_single_tenant = originals["assert_single_tenant"]
        between_run_floor.build_run_context = originals["build_run_context"]
        between_run_floor.source_digest.resolve_evidence = originals["resolve_evidence"]
        between_run_floor.derive_build_admission = originals["derive_build_admission"]
        between_run_floor.buildcache.build = originals["build"]
        between_run_floor.measure_point_floor = originals["measure"]
        between_run_floor._write_out = originals["write"]
    assert writes == []


def test_main_measurement_failure_does_not_write_success_json():
    expected = RuntimeError("fixture measurement failure")
    writes = []
    originals = {
        "assert_single_tenant": between_run_floor._assert_single_tenant,
        "build_run_context": between_run_floor.build_run_context,
        "resolve_evidence": between_run_floor.source_digest.resolve_evidence,
        "derive_build_admission": between_run_floor.derive_build_admission,
        "build": between_run_floor.buildcache.build,
        "measure": between_run_floor.measure_point_floor,
        "write": between_run_floor._write_out,
    }
    between_run_floor._assert_single_tenant = lambda: None
    between_run_floor.build_run_context = lambda **_kwargs: object()
    between_run_floor.source_digest.resolve_evidence = lambda *_args, **_kwargs: object()
    between_run_floor.derive_build_admission = lambda *_args, **_kwargs: object()
    between_run_floor.buildcache.build = lambda *_args, **_kwargs: SimpleNamespace(
        cached=True, binary="/fixture/binary")
    between_run_floor.measure_point_floor = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        expected)
    between_run_floor._write_out = lambda *args, **kwargs: writes.append((args, kwargs))
    try:
        try:
            between_run_floor.main(["prog", "write-heavy"])
        except RuntimeError as caught:
            assert caught is expected
        else:
            assert False, "measurement exception was swallowed"
    finally:
        between_run_floor._assert_single_tenant = originals["assert_single_tenant"]
        between_run_floor.build_run_context = originals["build_run_context"]
        between_run_floor.source_digest.resolve_evidence = originals["resolve_evidence"]
        between_run_floor.derive_build_admission = originals["derive_build_admission"]
        between_run_floor.buildcache.build = originals["build"]
        between_run_floor.measure_point_floor = originals["measure"]
        between_run_floor._write_out = originals["write"]
    assert writes == []


def test_t2760_baselines_are_points_of_their_registered_genome_space():
    assert set(between_run_floor.BASELINES) == {"silo", "mocc", "tictoc"}
    for protocol, baseline in between_run_floor.BASELINES.items():
        assert baseline.protocol == protocol
        assert baseline in space_for(protocol).enumerate()


def test_t2760_tictoc_baseline_matches_ccbench_cmake_cache_defaults_at_pin():
    text = (between_run_floor.CCBENCH_ROOT / "cmake" / "Options.cmake").read_text(
        encoding="utf-8",
    )
    flags = between_run_floor.BASELINES["tictoc"].flags
    assert len(flags) == 5
    for axis in flags:
        match = re.search(rf"^\s*set\(CCBENCH_{axis}\s+(\d+)\s+CACHE\b", text, re.MULTILINE)
        assert match is not None, axis
        assert int(match.group(1)) == flags[axis], axis


def test_t2760_parse_cli_args_accepts_tictoc_and_rejects_unregistered_protocol():
    assert between_run_floor._parse_cli_args(
        ["prog", "--protocol", "tictoc"]
    ) == (None, "tictoc")
    assert between_run_floor._parse_cli_args(
        ["prog", "read-heavy", "--protocol=tictoc"]
    ) == ("read-heavy", "tictoc")
    try:
        between_run_floor._parse_cli_args(["prog", "--protocol", "cicada"])
    except ValueError as caught:
        assert "unknown protocol" in str(caught)
        assert "'cicada'" in str(caught)
    else:
        assert False, "baseline のない cicada が受理された"


def test_t2760_protocol_output_stem_names_tictoc_without_colliding():
    workload = {
        "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0",
    }
    originals = {"scope_dir": between_run_floor.env_scope_dir}
    with tempfile.TemporaryDirectory() as raw_tmp:
        between_run_floor.env_scope_dir = lambda _env_tag: raw_tmp
        try:
            paths = {}
            for protocol in ("silo", "mocc", "tictoc"):
                paths[protocol] = Path(between_run_floor._write_out(
                    "read-heavy", workload, {
                        **_floor_result(),
                        "genome": between_run_floor.BASELINES[protocol].canonical(),
                    }, protocol=protocol, log=lambda *_args: None,
                ))
            assert paths["tictoc"].name == "between_run_noise_tictoc_t48_skew0p9_rr95_rmw0.json"
            assert len({path.name for path in paths.values()}) == 3
            assert between_run_floor.BASELINES["tictoc"].canonical() in (
                paths["tictoc"].with_suffix(".md").read_text(encoding="utf-8")
            )
        finally:
            between_run_floor.env_scope_dir = originals["scope_dir"]


def test_t2760_tictoc_floor_rejected_before_build_or_measure_without_trace_hook():
    calls = []
    originals = {
        "tenant": between_run_floor._assert_single_tenant,
        "context": between_run_floor.build_run_context,
        "evidence": between_run_floor.source_digest.resolve_evidence,
        "admission": between_run_floor.derive_build_admission,
        "build": between_run_floor.buildcache.build,
        "measure": between_run_floor.measure_point_floor,
        "write": between_run_floor._write_out,
    }
    between_run_floor._assert_single_tenant = lambda: calls.append("tenant")
    between_run_floor.build_run_context = lambda **_kwargs: object()
    between_run_floor.source_digest.resolve_evidence = (
        lambda *_args, **_kwargs: object()
    )
    between_run_floor.derive_build_admission = lambda *_args: object()
    between_run_floor.buildcache.build = lambda *_args, **_kwargs: (
        calls.append("build") or SimpleNamespace(cached=True, binary="/fixture/tictoc")
    )
    between_run_floor.measure_point_floor = lambda *_args, **_kwargs: (
        calls.append("measure") or {
            "abort_rate": 0.0,
            "within_run": {"cv": 0.01},
            "between_run": {"cv": 0.02},
        }
    )
    between_run_floor._write_out = lambda *_args, **_kwargs: calls.append("write")
    try:
        try:
            between_run_floor.main(["prog", "read-heavy", "--protocol", "tictoc"])
        except ValueError as caught:
            assert "trace hook" in str(caught)
            assert "'tictoc'" in str(caught)
        else:
            assert False, "trace hook のない tictoc floor が受理された"
    finally:
        between_run_floor._assert_single_tenant = originals["tenant"]
        between_run_floor.build_run_context = originals["context"]
        between_run_floor.source_digest.resolve_evidence = originals["evidence"]
        between_run_floor.derive_build_admission = originals["admission"]
        between_run_floor.buildcache.build = originals["build"]
        between_run_floor.measure_point_floor = originals["measure"]
        between_run_floor._write_out = originals["write"]
    assert calls == []


def test_t2760_hook_bearing_source_routes_tictoc_baseline_through_main():
    calls = {"build": [], "measure": [], "write": []}
    originals = {
        "root": between_run_floor.CCBENCH_ROOT,
        "tenant": between_run_floor._assert_single_tenant,
        "context": between_run_floor.build_run_context,
        "evidence": between_run_floor.source_digest.resolve_evidence,
        "admission": between_run_floor.derive_build_admission,
        "build": between_run_floor.buildcache.build,
        "measure": between_run_floor.measure_point_floor,
        "write": between_run_floor._write_out,
    }
    with tempfile.TemporaryDirectory() as raw_tmp:
        root = Path(raw_tmp)
        protocol_dir = root / "cc" / "tictoc"
        protocol_dir.mkdir(parents=True)
        (protocol_dir / "CMakeLists.txt").write_text(
            "ccbench_add_protocol(tictoc SOURCES transaction.cc WORKLOADS ycsb)\n",
            encoding="utf-8",
        )
        (protocol_dir / "transaction.cc").write_text(
            '#include "../../include/trace.hh"\n'
            "#if TRACE\n"
            "izanagi_trace::emit_abort(1);\n"
            "#endif\n",
            encoding="utf-8",
        )
        between_run_floor.CCBENCH_ROOT = root
        between_run_floor._assert_single_tenant = lambda: None
        between_run_floor.build_run_context = lambda **_kwargs: object()
        between_run_floor.source_digest.resolve_evidence = (
            lambda *_args, **_kwargs: object()
        )
        between_run_floor.derive_build_admission = lambda *_args: object()

        def fake_build(candidate, **_kwargs):
            calls["build"].append(candidate)
            return SimpleNamespace(cached=True, binary="/fixture/tictoc")

        def fake_measure(_binary, _workload, *, baseline, **_kwargs):
            calls["measure"].append(baseline)
            return {
                "abort_rate": 0.0,
                "within_run": {"cv": 0.01},
                "between_run": {"cv": 0.02},
            }

        between_run_floor.buildcache.build = fake_build
        between_run_floor.measure_point_floor = fake_measure
        between_run_floor._write_out = (
            lambda *_args, **kwargs: calls["write"].append(kwargs["protocol"])
        )
        try:
            assert between_run_floor.main(
                ["prog", "read-heavy", "--protocol", "tictoc"]
            ) == 0
        finally:
            between_run_floor.CCBENCH_ROOT = originals["root"]
            between_run_floor._assert_single_tenant = originals["tenant"]
            between_run_floor.build_run_context = originals["context"]
            between_run_floor.source_digest.resolve_evidence = originals["evidence"]
            between_run_floor.derive_build_admission = originals["admission"]
            between_run_floor.buildcache.build = originals["build"]
            between_run_floor.measure_point_floor = originals["measure"]
            between_run_floor._write_out = originals["write"]
    expected = between_run_floor.BASELINES["tictoc"]
    assert calls == {"build": [expected], "measure": [expected], "write": ["tictoc"]}


# ---- 素の runner (pytest 無しでも) ----

def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
