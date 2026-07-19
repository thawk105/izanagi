# -*- coding: utf-8 -*-
"""実 repo / 共有 submodule の xdist group 収集監査と scheduler control。"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from collections import Counter
from importlib import metadata
from pathlib import Path
from unittest import mock

from packaging.version import InvalidVersion, Version

HERE = Path(__file__).resolve().parent
ORCHESTRATOR = HERE.parent
ROOT = ORCHESTRATOR.parent

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ORCHESTRATOR))
from skiputil import Skip, skip  # noqa: E402


# conftest の付与正本から意図的に重複させる独立 oracle。ここを conftest から
# import / 導出すると、正本の node 増減が付与側と期待側へ同時伝播して恒真化する。
_REAL_REPO_SERIAL_NODES_GOLDEN = frozenset({
    "test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged",
    "test_p3_s4_loop.py::test_drive_iteration_checkpoint_survives_across_calls",
    "test_p3_s4_loop_sort.py::test_drive_iteration_checkpoint_survives_across_calls",
    "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_writes_entry_and_checkpoint",
    "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_entry_failure_blocks_checkpoint",
    "test_campaign.py::test_source_digest_parse_options_defaults",
    "test_campaign.py::test_source_digest_stock_roundtrip",
    "test_campaign.py::test_source_digest_fixed_variant_distinct",
    "test_campaign.py::test_source_digest_failsclosed_on_missing_define",
    "test_campaign.py::test_source_digest_semantic_comment_vs_behavior",
    "test_campaign.py::test_evolve_block_markers_structure_and_inert",
    "test_hooks.py::test_real_submodule_payload_edit",
    "test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control",
    "test_s1_known_axes_freeze.py::test_generate_selects_registered_expected_points",
    "test_s1_known_axes_freeze.py::test_generate_refuses_existing_freeze",
    "test_s1_known_axes_freeze.py::test_verify_rejects_one_byte_freeze_tamper",
    # 意図的な over-approximation: 現行 freeze の source 順では先行する不一致で
    # 止まるが、source 順の変更時は共有 submodule source に到達し得るため保持する。
    "test_s1_known_axes_freeze.py::test_verify_rejects_tampered_source_copy",
    "test_s1_known_axes_freeze.py::test_s1b_pairing_rejects_mismatched_flags",
    "test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null",
    "test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing",
    "test_s8b_oracle_driver.py::test_nonnull_floor_without_active_generation_is_refused",
    "test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated",
    "test_s8b_oracle_driver.py::test_tampered_freeze_fails_source_verification",
    "test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused",
    "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
    "test_s8b_binding_driftguards.py::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal",
})


def _load_suite_conftest():
    spec = importlib.util.spec_from_file_location(
        "izanagi_test_suite_conftest", HERE / "conftest.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_subprocess(argv, *, cwd, env=None):
    return subprocess.run(
        argv, cwd=str(cwd), env=env, capture_output=True, text=True,
    )


def _require_pytest() -> None:
    try:
        __import__("pytest")
    except ImportError:
        skip("pytest 不在 — pytest 依存検査を実行できない")


def test_real_repo_group_collection_exactly_matches_canonical_nodes():
    """real-repo marker の収集結果は正本 node 集合と過不足なく一致する。"""
    _require_pytest()
    with tempfile.TemporaryDirectory(prefix="izanagi-real-repo-collect-") as raw_tmp:
        tmp = Path(raw_tmp)
        report_path = tmp / "markers.json"
        plugin_path = tmp / "real_repo_collection_plugin.py"
        plugin_path.write_text(
            textwrap.dedent(
                """
                import json
                import os
                from pathlib import Path

                def pytest_collection_finish(session):
                    report = []
                    for item in session.items:
                        marks = list(item.iter_markers(name="xdist_group"))
                        function = (getattr(item, "originalname", None)
                                    or item.name.split("[", 1)[0])
                        node = f"{item.path.name}::{function}"
                        report.append({
                            "nodeid": item.nodeid,
                            "canonical_node": node,
                            "marks": [
                                {"args": list(mark.args),
                                 "kwargs": dict(mark.kwargs)}
                                for mark in marks
                            ],
                        })
                    Path(os.environ["IZANAGI_REAL_REPO_MARK_REPORT"]).write_text(
                        json.dumps(report, sort_keys=True), encoding="utf-8",
                    )
                """
            ),
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["IZANAGI_REAL_REPO_MARK_REPORT"] = str(report_path)
        env["PYTHONPATH"] = os.pathsep.join(
            part for part in (str(tmp), env.get("PYTHONPATH", "")) if part
        )
        proc = _run_subprocess(
            [
                sys.executable, "-m", "pytest", "--collect-only", "-q",
                "-p", "real_repo_collection_plugin", str(HERE),
            ],
            cwd=ROOT,
            env=env,
        )
        assert proc.returncode == 0, (
            f"collection subprocess failed:\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))

    golden = set(_REAL_REPO_SERIAL_NODES_GOLDEN)
    configured = set(_load_suite_conftest().REAL_REPO_SERIAL_NODES)
    assert configured == golden, (
        "conftest.REAL_REPO_SERIAL_NODES が独立 golden と不一致: "
        f"missing={sorted(golden - configured)} "
        f"extra={sorted(configured - golden)}"
    )
    nodeids = [entry["nodeid"] for entry in report]
    assert len(nodeids) == len(set(nodeids)), (
        "collection report の item.nodeid が重複している"
    )

    exact_mark = [{"args": ["real-repo"], "kwargs": {}}]
    collected_counts = Counter()
    marked_counts = Counter()
    for entry in report:
        nodeid = entry["nodeid"]
        canonical = entry["canonical_node"]
        marks = entry["marks"]
        collected_counts[canonical] += 1
        real_repo_marks = [
            mark for mark in marks if "real-repo" in mark["args"]
        ]
        if canonical in golden:
            assert marks == exact_mark, (
                f"{nodeid} の xdist_group は real-repo 1 個だけでなければならない: "
                f"{marks!r}"
            )
            marked_counts[canonical] += 1
        else:
            assert not real_repo_marks, (
                f"golden 外 instance {nodeid} に real-repo marker がある: "
                f"{marks!r}"
            )

    for canonical in sorted(golden):
        assert collected_counts[canonical] > 0, (
            f"golden node が収集されなかった: {canonical}"
        )
        assert collected_counts[canonical] == marked_counts[canonical], (
            f"{canonical} の collected/marked instance 数が不一致: "
            f"collected={collected_counts[canonical]} "
            f"marked={marked_counts[canonical]}"
        )


def test_protocol_builder_repo_tree_guard_is_wired_to_real_root():
    """SUT が repo-tree helper を実 ROOT に結線していることを実行時に監査する。"""
    _require_pytest()
    from tests import repo_tree_util
    from tests import test_s8b_protocol_builder as sut

    helper_calls = []
    builder_actions = []
    writer_actions = []
    state = {"in_guard_action": False, "action": None}
    original_guard = repo_tree_util.assert_repo_tree_unchanged
    original_builder = sut._build_golden
    original_writer = sut.fc.write_protocol_document

    def recording_wrapper(root, action):
        helper_calls.append((root, action))

        def guarded_action():
            assert not state["in_guard_action"], "repo-tree guard action が入れ子になった"
            state["in_guard_action"] = True
            state["action"] = action
            try:
                return action()
            finally:
                state["action"] = None
                state["in_guard_action"] = False

        return original_guard(root, guarded_action)

    def recording_builder(*args, **kwargs):
        assert state["in_guard_action"], (
            "_build_golden が repo-tree guard action 外で実行された"
        )
        builder_actions.append(state["action"])
        return original_builder(*args, **kwargs)

    def recording_writer(*args, **kwargs):
        assert state["in_guard_action"], (
            "write_protocol_document が repo-tree guard action 外で実行された"
        )
        writer_actions.append(state["action"])
        return original_writer(*args, **kwargs)

    with tempfile.TemporaryDirectory(prefix="izanagi-guard-wiring-") as raw_tmp:
        with mock.patch.object(
                repo_tree_util, "assert_repo_tree_unchanged", recording_wrapper,
        ), mock.patch.object(
                sut, "_build_golden", side_effect=recording_builder,
        ), mock.patch.object(
                sut.fc, "write_protocol_document", side_effect=recording_writer,
        ):
            sut.test_build_and_write_leave_repo_tree_unchanged(
                Path(raw_tmp), Path("protocol.json"),
            )

    assert len(helper_calls) == 1, (
        "protocol builder SUT の repo-tree helper 呼出しは厳密に 1 回でなければならない: "
        f"actual={len(helper_calls)}"
    )
    assert helper_calls[0][0] == ROOT == sut.ROOT, (
        "repo-tree helper の第一引数が実 repo ROOT でない: "
        f"actual={helper_calls[0][0]!r} expected={ROOT!r}"
    )
    guarded_action = helper_calls[0][1]
    assert builder_actions == [guarded_action], (
        "_build_golden は同一 guard action 内で厳密に 1 回実行されなければならない: "
        f"actual={builder_actions!r}"
    )
    assert len(writer_actions) == 2, (
        "write_protocol_document は guard action 内で厳密に 2 回でなければならない: "
        f"actual={len(writer_actions)}"
    )
    assert all(action is guarded_action for action in writer_actions), (
        "2 回の write_protocol_document が同一 guard action 内で実行されていない"
    )


def _require_loadgroup_capability() -> None:
    _require_pytest()
    try:
        version = metadata.version("pytest-xdist")
    except metadata.PackageNotFoundError:
        skip("pytest-xdist 不在 — live loadgroup scheduler control を実行できない")
    try:
        supported = Version(version) >= Version("2.5")
    except InvalidVersion:
        supported = False
    if not supported:
        skip(f"pytest-xdist {version} は loadgroup 非対応 (<2.5)")


def _worker_evidence(path: Path) -> tuple[str, str]:
    return (
        (path / "a.worker").read_text(encoding="utf-8"),
        (path / "b.worker").read_text(encoding="utf-8"),
    )


def test_loadgroup_scheduler_keeps_same_group_on_one_worker_and_control_detects_absence():
    """loadgroup の同一 worker 証拠と、option 無しなら歯が発火する対照を実走する。"""
    _require_loadgroup_capability()
    with tempfile.TemporaryDirectory(prefix="izanagi-loadgroup-live-") as raw_tmp:
        tmp = Path(raw_tmp)
        suite = tmp / "test_group_probe.py"
        suite.write_text(
            textwrap.dedent(
                """
                import os
                from pathlib import Path
                import pytest

                def _record(name):
                    out = Path(os.environ["IZANAGI_GROUP_PROBE_OUT"])
                    out.mkdir(parents=True, exist_ok=True)
                    (out / f"{name}.worker").write_text(
                        os.environ["PYTEST_XDIST_WORKER"], encoding="utf-8",
                    )

                @pytest.mark.xdist_group("probe")
                def test_group_a():
                    _record("a")

                @pytest.mark.xdist_group("probe")
                def test_group_b():
                    _record("b")
                """
            ),
            encoding="utf-8",
        )

        grouped_out = tmp / "grouped"
        grouped_env = os.environ.copy()
        grouped_env["IZANAGI_GROUP_PROBE_OUT"] = str(grouped_out)
        grouped = _run_subprocess(
            [
                sys.executable, "-m", "pytest", "-q", "-n", "2",
                "--dist", "loadgroup", str(suite),
            ],
            cwd=tmp,
            env=grouped_env,
        )
        assert grouped.returncode == 0, (
            f"loadgroup probe failed:\nstdout={grouped.stdout}\nstderr={grouped.stderr}"
        )
        grouped_workers = _worker_evidence(grouped_out)
        assert grouped_workers[0] == grouped_workers[1], grouped_workers

        # Negative control: --dist loadgroup だけを外す。同じ 2 node が別 worker に
        # 分かれ、worker 証拠比較が実際に不一致を検出できることを固定する。
        control_out = tmp / "control"
        control_env = os.environ.copy()
        control_env["IZANAGI_GROUP_PROBE_OUT"] = str(control_out)
        control = _run_subprocess(
            [sys.executable, "-m", "pytest", "-q", "-n", "2", str(suite)],
            cwd=tmp,
            env=control_env,
        )
        assert control.returncode == 0, (
            f"load scheduler control failed:\nstdout={control.stdout}\n"
            f"stderr={control.stderr}"
        )
        control_workers = _worker_evidence(control_out)
        assert control_workers[0] != control_workers[1], (
            "negative control が worker 分離を検出しなかった: "
            f"{control_workers!r}"
        )


def _run() -> int:
    passed = failed = skipped = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"PASS {name}")
            passed += 1
        except Skip as exc:
            print(f"SKIP {name}: {exc}")
            skipped += 1
        except AssertionError as exc:
            print(f"FAIL {name}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {name}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
