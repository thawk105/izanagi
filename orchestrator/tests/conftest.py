"""orchestrator/tests 共通 pytest 設定 — 一時ディレクトリを tmpfs へ向ける。

campaign 系 (wal / freeze / budget / marker) は耐久性のため書き込みごとに
flush+fsync する。ジャーナリング FS 上の一時 dir ではその 1 回 1 回が実ディスク
バリアになり、スイートが I/O 律速で数百倍遅くなる (実測は worklog 2026-07-17)。
tmpfs では fsync がほぼ無償なので、fsync を呼ぶコード経路はそのまま保たれ
(検査は弱めない)、物理バリアだけが消える。

- 明示的な TMPDIR はユーザー指定として尊重し、何もしない (従来動作へ戻す口)
- /dev/shm が無い・書けない・空きが小さい環境では何もしない (従来動作)。容量
  ガードは、tmpfs が数十 MB しかない環境 (コンテナの既定 shm 等) で TMPDIR を
  読む大容量経路 (patchharness / calibrator runner / trace 生成) が誤誘導的な
  ENOSPC に落ちるのを防ぐ (敵対レビュー所見、insights 2026-07-17)
- pytest の tmp_path も、テスト内の tempfile.* 直接使用も、テストが env を継承
  して起動する subprocess も影響を受ける (いずれも TMPDIR 由来)。素の python3
  実行 (二重 runner) は conftest を経由しない — 必要なら TMPDIR=/dev/shm を手で
  与える (tests/README.md「一時ディレクトリと速度」)
"""
import os
import tempfile

import pytest

_SHM = "/dev/shm"
_MIN_FREE_BYTES = 1 << 30  # 1 GiB 未満の tmpfs (コンテナ既定 shm=64MB 等) は採用しない


def _shm_usable() -> bool:
    if not (os.path.isdir(_SHM) and os.access(_SHM, os.W_OK | os.X_OK)):
        return False
    try:
        st = os.statvfs(_SHM)
    except OSError:
        return False
    return st.f_bavail * st.f_frsize >= _MIN_FREE_BYTES


if "TMPDIR" not in os.environ and _shm_usable():
    os.environ["TMPDIR"] = _SHM
    # gettempdir() は初回呼び出し結果をキャッシュする — 破棄して TMPDIR を再評価させる
    tempfile.tempdir = None


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
    # 意図的な over-approximation: 現行 freeze の source 順では先行する不一致で
    # 止まるが、source 順の変更時は共有 submodule source に到達し得るため保持する。
    "test_s1_known_axes_freeze.py::test_verify_rejects_tampered_source_copy",
    "test_s1_known_axes_freeze.py::test_s1b_pairing_rejects_mismatched_flags",

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
# - test_s1_measurement_freeze.py 全 8 node 等、git object / HEAD だけを読むものは
#   mutable worktree の patch 窓を読まない。
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
