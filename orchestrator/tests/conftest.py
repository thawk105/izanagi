"""orchestrator/tests 共通 pytest 設定 — TMPDIR は設定しない。

かつてここは TMPDIR を tmpfs (``/dev/shm``) へ向けていたが撤去した。tmpfs の
使用量はユーザーの memory cgroup へほぼ 1:1 で課金され、Pegasus ログインノード
のユーザーメモリ枠 16 GiB (cgroup v2 ``memory.max`` = 17179869184) を直接削る。
受入全走 1 回の tmpfs peak は 7.39 GiB (計算ノード bnode033、request 874750 実測)
なので、ログインノードで 2 回走らせれば枠を使い切る。

代替の TMPDIR 注入は置かない。TMPDIR 未設定なら環境既定 (``/tmp``) を使う。
実ディスクにした代償は場所で大きく違う。断定を避けて実測値を分けて書く。

- **計算ノードでは小さい。** 300 回の write+fsync が ``/tmp`` で 0.026 秒、
  ``/dev/shm`` で 0.001 秒、Lustre (``/home``) で 0.42 秒 (bnode021、loadavg 0.29、
  3 走同値)。計算ノード bnode041 の ``/tmp`` の fstype は xfs (magic 58465342)
- **ログインノード直叩きでは大きい。** 共有・loadavg 高の pegasus02 では 300 回の
  write+fsync が ``/tmp`` 8.7〜9.4 秒、``/dev/shm`` 0.002 秒、``/home`` (Lustre)
  0.435〜0.447 秒。テストスイート実測でも ``orchestrator/tests/test_campaign.py``
  (168 node) が ``TMPDIR=/dev/shm`` で 2.21 秒、``TMPDIR=/tmp`` で 12.33 秒 (5.6 倍)

fsync を呼ぶコード経路は変えていない (検査は弱めない) — tmpfs 上で no-op だった
バリアが実バリアに戻るだけである。上の 168 node 実測でも fsync 回数は両方とも
620 回で完全に一致した。遅さが気になる場所ではディスク上の速い TMPDIR を明示せよ。

- 明示的な TMPDIR はユーザー指定として尊重し、ここでは何もしない (元から不干渉)
- 一時 dir を速い局所ディスクへ置きたい場合は TMPDIR を明示的に与える。ただし
  tmpfs を選んではいけない — 実効 TMPDIR の fstype は
  ``test_real_repo_serialization.py`` の回帰ガードが検査して赤にする
- 素の python3 実行 (二重 runner) は元から conftest を経由しない
"""
import os

import pytest


# 単一 pytest runner invocation 内で、親 repo status と共有 ccbench worktree の
# reader/writer を同じ xdist loadgroup に閉じ込める正本。値は
# ``test_file.py::test_function``（parametrize suffix なし）で固定する。
REAL_REPO_SERIAL_NODES = frozenset({
    # 親 working tree の tracked + untracked snapshot。
    "test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged",
    # 上記 snapshot テストの結線監査 meta-テスト。実 ROOT で builder を実走し repo tree
    # snapshot を取るため、writer の patch 窓と同じ競合面にある (D63 列挙漏れの補完)。
    "test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root",

    # 実 external/ccbench に patch を apply/revert する writer。
    "test_p3_s4_loop.py::test_drive_iteration_checkpoint_survives_across_calls",
    "test_p3_s4_loop_sort.py::test_drive_iteration_checkpoint_survives_across_calls",
    "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_writes_entry_and_checkpoint",
    "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_entry_failure_blocks_checkpoint",

    # writer の patch 窓にある実 source を読む reader。
    "test_campaign.py::test_source_digest_parse_options_defaults",
    "test_campaign.py::test_source_digest_stock_roundtrip",
    "test_campaign.py::test_source_digest_fixed_variant_distinct",
    "test_campaign.py::test_source_digest_failsclosed_on_missing_define",
    "test_campaign.py::test_source_digest_semantic_comment_vs_behavior",
    "test_campaign.py::test_evolve_block_markers_structure_and_inert",
    "test_hooks.py::test_real_submodule_payload_edit",
    "test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control",

    # known-axes の生成/検証が実 ccbench source path を読む reader。
    "test_s1_known_axes_freeze.py::test_generate_selects_registered_expected_points",
    "test_s1_known_axes_freeze.py::test_generate_refuses_existing_freeze",
    "test_s1_known_axes_freeze.py::test_verify_rejects_one_byte_freeze_tamper",
    "test_s1_known_axes_freeze.py::test_verify_rejects_tampered_source_copy",
    "test_s1_known_axes_freeze.py::test_s1b_pairing_rejects_mismatched_flags",
    "test_s1_known_axes_freeze.py::test_build_document_is_self_consistent_and_detects_tamper",
    "test_s1_known_axes_freeze.py::test_verify_rejects_generator_sha_tamper",
    "test_s1_known_axes_freeze.py::test_verify_rejects_non_ancestor_head",
    "test_s1_known_axes_freeze.py::test_verify_rejects_foreign_ccbench_pin",

    # measurement freeze は module fixture で実 known-axes 材料 (共有 submodule source
    # 含む) から K.build_document を実走する reader ([T-066] echo 除去後)。
    "test_s1_measurement_freeze.py::test_generate_builds_registered_cells_comparisons_and_schedule",
    "test_s1_measurement_freeze.py::test_generate_refuses_existing_freeze",
    "test_s1_measurement_freeze.py::test_verify_rejects_one_byte_freeze_tamper",
    "test_s1_measurement_freeze.py::test_verify_rejects_one_byte_workload_flag_tamper",
    "test_s1_measurement_freeze.py::test_verify_rejects_stats_implementation_tamper",
    "test_s1_measurement_freeze.py::test_verify_rejects_known_axes_material_tamper",
    "test_s1_measurement_freeze.py::test_schedule_is_balanced_and_reproducible",
    "test_s1_measurement_freeze.py::test_s1b_pairing_rejects_mismatched_flags",
    "test_s1_measurement_freeze.py::test_receipt_exists_but_measurement_verify_stays_legacy_strict",
    "test_s1_measurement_freeze.py::test_build_document_rejects_tampered_known_axes_semantics",

    # root=実 repo の oracle gate が known-axes verify を間接呼出しする reader。
    "test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null",
    "test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing",
    "test_s8b_oracle_driver.py::test_nonnull_floor_without_active_generation_is_refused",
    "test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated",
    "test_s8b_oracle_driver.py::test_tampered_freeze_fails_source_verification",
    "test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused",
    "test_s8b_oracle_driver.py::test_v2_standalone_gate_check_requires_full_floor_validation",
    "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
    "test_s8b_binding_driftguards.py::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal",
})

# 意図的な除外（正本リストの境界）:
# - test_s1_measurement_freeze.py のうち fixture 非利用 3 node (AST import 検査 +
#   hermetic seam 2 件) は実 repo / 共有 submodule を読まない。fixture 消費 node は
#   [T-066] echo 除去後は実材料 reader なので上記に列挙済み。
# - test_campaign.py::test_patchharness_* は tmp repo、slow oracle canary は
#   patchharness の隔離 worktree を使い、共有 submodule worktree を patch しない。
# - source_digest allowlist は subprocess を fake 化しており、lock-path gate は実 output
#   だけを読む。実 output / snapshot 系もこの reader/writer 競合面には含めない。


@pytest.fixture(autouse=True)
def _isolate_task_run_recording_env(monkeypatch):
    """外側 run が task-run 記録付きでも、テスト自身は記録 env を観測しない。

    wrapper (tools/run_tests.py) は pytest 起動前に env を読むため記録は影響を受けない。
    テストが記録経路を検査するときは自分で env を設定する (dogfooding で実測した汚染の隔離)。
    """
    for name in (
        "IZANAGI_TASK_RUN_ID",
        "IZANAGI_TASK_RUNS_ROOT",
        "IZANAGI_TASK_RUN_SIDECAR",
        "IZANAGI_TEST_TRIGGER",
    ):
        monkeypatch.delenv(name, raising=False)


def _real_repo_node_id(item) -> str:
    """Collected item を正本の ``module::function`` 形へ正規化する。"""
    function = getattr(item, "originalname", None) or item.name.split("[", 1)[0]
    return f"{os.path.basename(str(item.path))}::{function}"


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items) -> None:
    """正本 node に real-repo group を一度だけ付ける。"""
    for item in items:
        if _real_repo_node_id(item) not in REAL_REPO_SERIAL_NODES:
            continue
        # xdist は複数 group 名を結合するため、二個目を足すと別 group になり排他が壊れる。
        # 既存 marker があれば上書きせず、収集監査の完全一致を赤くして人間へ返す。
        if list(item.iter_markers(name="xdist_group")):
            continue
        item.add_marker(pytest.mark.xdist_group("real-repo"))


def pytest_collection_finish(session) -> None:
    """Opt-in task-run stats collection; observation must never affect pytest."""
    if not os.environ.get("IZANAGI_TASK_RUN_SIDECAR"):
        return
    try:
        from tools.task_runs import pytest_stats

        pytest_stats.note_collection(session)
    except Exception:
        pass


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_node_collection_finished(node, ids) -> None:
    """Collect controller-visible node IDs without persisting their names."""
    if not os.environ.get("IZANAGI_TASK_RUN_SIDECAR"):
        return
    try:
        from tools.task_runs import pytest_stats

        pytest_stats.note_xdist_collection(node, ids)
    except Exception:
        pass


def pytest_sessionfinish(session, exitstatus) -> None:
    """Create the private aggregate sidecar on the controller only."""
    if not os.environ.get("IZANAGI_TASK_RUN_SIDECAR"):
        return
    try:
        from tools.task_runs import pytest_stats

        pytest_stats.write_session_stats(session)
    except Exception:
        pass
