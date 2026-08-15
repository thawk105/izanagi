# -*- coding: utf-8 -*-
"""テストスイート自身の conftest 契約の監査。

- 実 repo / 共有 submodule の xdist group 収集監査と scheduler control
- 一時ディレクトリの置き場ガード (実効 TMPDIR が tmpfs へ戻る退行の検出)
"""
from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import os
import shutil
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
sys.path.insert(0, str(ORCHESTRATOR.parent))
from skiputil import Skip, skip  # noqa: E402


# conftest の付与正本から意図的に重複させる独立 oracle。ここを conftest から
# import / 導出すると、正本の node 増減が付与側と期待側へ同時伝播して恒真化する。
_REAL_REPO_SERIAL_NODES_GOLDEN = frozenset({
    "test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged",
    # snapshot テストの結線監査 meta-テスト (本ファイル)。実 ROOT で builder を実走し
    # repo tree snapshot を取るため writer の patch 窓と同じ競合面 (D63 列挙漏れの補完)。
    "test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root",
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
    "test_s1_known_axes_freeze.py::test_verify_rejects_tampered_source_copy",
    "test_s1_known_axes_freeze.py::test_s1b_pairing_rejects_mismatched_flags",
    "test_s1_known_axes_freeze.py::test_build_document_is_self_consistent_and_detects_tamper",
    "test_s1_known_axes_freeze.py::test_verify_rejects_generator_sha_tamper",
    "test_s1_known_axes_freeze.py::test_verify_rejects_non_ancestor_head",
    "test_s1_known_axes_freeze.py::test_verify_rejects_foreign_ccbench_pin",
    # measurement freeze の fixture 消費 node ([T-066] echo 除去後は実材料 reader)。
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
    "test_s1_measurement_freeze.py::test_recorded_ccbench_pin_hold_and_release_positive_control",
    # prepare_cell が実共有 submodule の linked-worktree 管理領域を更新する writer。
    "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration",
    "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration",
    "test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2",
    "test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding",
    # module fixture が実 repo / 実 submodule を clone source として読む reader。
    "test_codex_reasoning_ab.py::test_parent_numstat_controls_remain_pinned",
    "test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases",
    "test_codex_reasoning_ab.py::test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure",
    "test_codex_reasoning_ab.py::test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested",
    "test_codex_reasoning_ab.py::test_m1_snapshot_head_pin_is_independent",
    "test_codex_reasoning_ab.py::test_m3_snapshot_mode_change",
    "test_codex_reasoning_ab.py::test_m3_symbolic_head_is_required",
    "test_codex_reasoning_ab.py::test_m3_ignored_extra_and_missing",
    "test_codex_reasoning_ab.py::test_m3_focus_artifact_directions",
    "test_codex_reasoning_ab.py::test_snapshot_submodule_object_store_is_recursive",
    "test_codex_reasoning_ab.py::test_pos_neg_submodule_initialization_state_mismatch_is_rejected",
    "test_codex_reasoning_ab.py::test_git_answer_object_reinjection_is_rejected",
    "test_codex_reasoning_ab.py::test_supervisor_launches_pair_and_scrubs_git_environment",
    "test_codex_reasoning_ab.py::test_agent_sandbox_binds_exclude_attempt_receipt_directory",
    "test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment",
    "test_codex_reasoning_ab.py::test_attempt_four_is_rejected_before_launch",
    "test_codex_reasoning_ab.py::test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation",
    # helper が実親 repo と実共有 submodule を clone source として直接読む reader。
    "test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e",
    "test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null",
    "test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing",
    "test_s8b_oracle_driver.py::test_nonnull_floor_without_active_generation_is_refused",
    "test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated",
    "test_s8b_oracle_driver.py::test_tampered_freeze_fails_source_verification",
    "test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused",
    "test_s8b_oracle_driver.py::test_v2_standalone_gate_check_requires_full_floor_validation",
    "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
    "test_s8b_binding_driftguards.py::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal",
    "test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight",
})

# suite で許す xdist group 名の独立 oracle。conftest や marker 定数から導出しない。
_XDIST_GROUP_NAMES_GOLDEN = frozenset({
    "dev-waves-runtime",
    "real-repo",
    "s8c-preregistration-candidate",
})


def _load_suite_conftest():
    spec = importlib.util.spec_from_file_location(
        "izanagi_test_suite_conftest", HERE / "conftest.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- 一時ディレクトリの置き場ガード -------------------------------------------------
#
# tmpfs (``/dev/shm`` 等) の使用量はユーザーの memory cgroup へほぼ 1:1 で課金される。
# Pegasus ログインノードのユーザーメモリ枠は 16 GiB (cgroup v2 ``memory.max`` =
# 17179869184) で、受入全走 1 回の tmpfs peak 7.39 GiB (bnode033、request 874750 実測)
# なら 2 回で使い切る。conftest はもう TMPDIR を設定しないが、将来また tmpfs へ
# 向いたらここで赤くなる。skip するのは (a) mountinfo を読めず判定不能なとき、
# (b) TMPDIR 未設定で環境既定 (/tmp) が tmpfs なとき — (b) はユーザーも本 repo も
# 何も選んでいない無過失の赤を避けるため (段 6 レビュー W2 の裁定)。source 上の
# 結線検査 (find_tmpfs_tmpdir_wiring) は環境に依らず常に赤にできる方の歯である。

_TMPFS_FSTYPES = frozenset({"tmpfs", "ramfs", "devtmpfs", "hugetlbfs"})

# TMPDIR へ代入されたら退行と見なす tmpfs 族の慣用パス。実 mount 表を引けない
# source 検査 (find_tmpfs_tmpdir_wiring) 側の判定に使う。
_TMPFS_PATH_ROOTS = (
    "/dev/shm", "/run/shm", "/var/run/shm", "/run/user", "/var/run/user",
)


def _unescape_mountinfo_field(field: str) -> str:
    r"""mountinfo の 8 進エスケープ (\040 空白 / \011 tab / \012 改行 / \134 backslash) を戻す。"""
    out: list[str] = []
    index = 0
    size = len(field)
    while index < size:
        char = field[index]
        if (char == "\\" and index + 3 < size
                and all(c in "01234567" for c in field[index + 1:index + 4])):
            out.append(chr(int(field[index + 1:index + 4], 8)))
            index += 4
            continue
        out.append(char)
        index += 1
    return "".join(out)


def _path_is_within(path: str, mount_point: str) -> bool:
    base = mount_point.rstrip("/")
    return path == mount_point or path == base or path.startswith(base + "/")


def _fs_type(path: str, mountinfo_text: str | None = None,
             *, resolve: bool = True) -> str | None:
    """``path`` を含む mount の fstype を返す。判定不能なら None。

    Python の ``os.statvfs`` は ``f_type`` を公開しないので ``/proc/self/mountinfo``
    を最長前方一致で引く。``mountinfo_text`` を渡すと合成 mount 表で検査できる
    (positive/negative control 用)。``resolve`` は realpath の適用可否で、既定の
    True が本番経路 — symlink 越しに tmpfs を掴むのを取り逃さないために要る。

    campaign/durable_root.py にも mountinfo parser があるが、あちらは mount ID 境界の
    fail-closed 検査専用で fstype を持たない。テスト用ガードのために production の
    契約を広げないので、ここでは読み取り専用の小さな parser を別に置く。
    """
    if mountinfo_text is None:
        try:
            with open("/proc/self/mountinfo", encoding="utf-8") as handle:
                mountinfo_text = handle.read()
        except OSError:
            return None
    target = os.path.realpath(path) if resolve else os.path.abspath(path)
    best_length = -1
    best_type = None
    for line in mountinfo_text.splitlines():
        fields = line.split()
        if "-" not in fields:
            continue
        separator = fields.index("-")
        # 必須 6 field の後に optional field が並び、単独の "-" が終端になる。
        if separator < 6 or separator + 1 >= len(fields):
            continue
        mount_point = _unescape_mountinfo_field(fields[4])
        if not _path_is_within(target, mount_point):
            continue
        # 同じ mount point への overmount では後勝ちなので >= で更新する。
        if len(mount_point) >= best_length:
            best_length = len(mount_point)
            best_type = _unescape_mountinfo_field(fields[separator + 1])
    return best_type


def _tmpdir_verdict(path: str, mountinfo_text: str | None = None,
                    *, resolve: bool = True) -> tuple[str, str | None]:
    """``(status, fstype)`` を返す。status は "ok" / "tmpfs" / "unknown"。"""
    fstype = _fs_type(path, mountinfo_text, resolve=resolve)
    if fstype is None:
        return ("unknown", None)
    if fstype in _TMPFS_FSTYPES:
        return ("tmpfs", fstype)
    return ("ok", fstype)


def _effective_tmpdir_candidates() -> list[tuple[str, bool]]:
    """一時ファイルが実際に落ちる場所と、それが明示 ``TMPDIR`` 由来かの対。

    自プロセス (``tempfile.gettempdir()``) と、env を継承する subprocess (``TMPDIR``)
    の両方を見る。第 2 要素 True は「ユーザーが ``TMPDIR`` で明示的に選んだ場所」で、
    tmpfs なら退行として赤にする。False は環境既定 (``/tmp`` 等) で、ユーザーが何も
    選んでいないので tmpfs でも赤にはせず skip へ倒す (段 6 レビュー W2 の裁定)。
    """
    default_tmpdir = tempfile.gettempdir()
    env_tmpdir = os.environ.get("TMPDIR") or None
    candidates = [(default_tmpdir, env_tmpdir is not None and default_tmpdir == env_tmpdir)]
    if env_tmpdir is not None and env_tmpdir != default_tmpdir:
        candidates.append((env_tmpdir, True))
    return candidates


def _is_tmpfs_path_literal(text: object) -> bool:
    if not isinstance(text, str) or not text.startswith("/"):
        return False
    normalized = os.path.normpath(text)
    return any(normalized == root or normalized.startswith(root + "/")
               for root in _TMPFS_PATH_ROOTS)


def _static_str(node: ast.AST | None, constants: dict[str, str]) -> str | None:
    """AST node から静的に決まる文字列 (前方一致に足る接頭辞) を best-effort で取り出す。"""
    if node is None:
        return None
    if node.__class__.__name__ == "Index":  # Python 3.8 以前の subscript
        return _static_str(node.value, constants)  # type: ignore[attr-defined]
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                break  # 動的部分より手前の接頭辞だけで判定する
        return "".join(parts) or None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _static_str(node.left, constants)
    if isinstance(node, ast.Call):
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name in ("join", "expanduser", "normpath", "realpath", "abspath") and node.args:
            return _static_str(node.args[0], constants)
    return None


def _string_constants(tree: ast.AST) -> dict[str, str]:
    """``_SHM = "/dev/shm"`` 形の module 定数を解決表にする (literal 直書き以外を殺すため)。"""
    constants: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        value = node.value
        if (isinstance(target, ast.Name) and isinstance(value, ast.Constant)
                and isinstance(value.value, str)):
            constants[target.id] = value.value
    return constants


def _is_tmpdir_environ_subscript(node: ast.AST, constants: dict[str, str]) -> bool:
    if not isinstance(node, ast.Subscript):
        return False
    container = node.value
    name = (container.attr if isinstance(container, ast.Attribute)
            else getattr(container, "id", None))
    if name != "environ":
        return False
    return _static_str(node.slice, constants) == "TMPDIR"


def _is_tempfile_tempdir_target(node: ast.AST) -> bool:
    """``tempfile.tempdir`` への代入 target か (env を経由しない in-process 結線)。

    ``os.environ["TMPDIR"]`` 系だけを見ていると、``tempfile.tempdir = "/dev/shm"``
    という一行で ``tmp_path`` と in-process の ``tempfile.*`` (= tmpfs peak 7.39 GiB の
    主因) がまるごと tmpfs へ戻るのを取り逃す。撤去前の conftest 自身が
    ``tempfile.tempdir = None`` を使っていたので、「速度を戻す」編集が最も自然に
    触る属性でもある (段 6 レビュー N2 が変異で実証)。

    ``import tempfile as tf`` の alias を取り逃さないよう属性名だけで判定する。
    tmpfs リテラル代入だけを hit にするので、無関係な ``x.tempdir`` の誤検出面は
    「tmpfs パスを tempdir 名の属性へ代入する」形に限られる。

    **実行時の ``tempfile.tempdir`` の値では判定してはいけない。** CPython の
    ``gettempdir()`` は初回呼出しで ``tempfile.tempdir`` へ既定値を書き込む
    (CPython 3.10.12 実測で ``None`` → ``/tmp``) ため、明示指定と既定値を実行時の値では
    区別できない。だから source 側で捕まえる。
    """
    return isinstance(node, ast.Attribute) and node.attr == "tempdir"


def find_tmpfs_tmpdir_wiring(source: str) -> list[tuple[int, str]]:
    """source 内で一時領域を tmpfs へ結線している箇所を ``(行, パス)`` で返す。

    対象は ``os.environ["TMPDIR"]`` 系 (subprocess へ継承される env 経路) と
    ``tempfile.tempdir`` 系 (自プロセスの ``tmp_path`` / ``tempfile.*`` を移す
    in-process 経路) の両方。

    単なる文字列 grep ではなく AST を見る — docstring やコメントで ``/dev/shm`` に
    言及するだけの行を誤検出せず、``_SHM = "/dev/shm"`` を経由する間接代入
    (撤去前の conftest が使っていた形) を取り逃さないため。
    """
    tree = ast.parse(source)
    constants = _string_constants(tree)
    hits: set[tuple[int, str]] = set()

    def record(node: ast.AST, value_node: ast.AST | None) -> None:
        text = _static_str(value_node, constants)
        if _is_tmpfs_path_literal(text):
            hits.add((node.lineno, str(text)))

    def is_tmpdir_target(node: ast.AST) -> bool:
        return (_is_tmpdir_environ_subscript(node, constants)
                or _is_tempfile_tempdir_target(node))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if is_tmpdir_target(target):
                    record(node, node.value)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            if is_tmpdir_target(node.target):
                record(node, node.value)
        elif isinstance(node, ast.Call):
            func = node.func
            name = (func.attr if isinstance(func, ast.Attribute)
                    else getattr(func, "id", None))
            if name in ("setdefault", "putenv") and len(node.args) >= 2:
                if _static_str(node.args[0], constants) == "TMPDIR":
                    record(node, node.args[1])
            elif name == "update":
                for argument in node.args:
                    if not isinstance(argument, ast.Dict):
                        continue
                    for key, value in zip(argument.keys, argument.values):
                        if _static_str(key, constants) == "TMPDIR":
                            record(node, value)
                for keyword in node.keywords:
                    if keyword.arg == "TMPDIR":
                        record(node, keyword.value)
    return sorted(hits)


def _run_subprocess(argv, *, cwd, env=None):
    return subprocess.run(
        argv, cwd=str(cwd), env=env, capture_output=True, text=True,
    )


def _require_pytest() -> None:
    try:
        __import__("pytest")
    except ImportError:
        skip("pytest 不在 — pytest 依存検査を実行できない")


def _collect_xdist_group_report(
    target: Path, *, cwd: Path, collection_options: tuple[str, ...] = (),
    lastfailed_nodeids: tuple[str, ...] = (),
    cached_nodeids: tuple[str, ...] = (),
) -> list[dict]:
    """temp plugin で collection 後の全 xdist_group marker を取得する。"""
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

                def shared_fixture_closure(item):
                    fixtureinfo = getattr(item, "_fixtureinfo", None)
                    if fixtureinfo is None:
                        raise TypeError(f"{item.nodeid}: item._fixtureinfo がない")
                    names = getattr(fixtureinfo, "names_closure", None)
                    definitions = getattr(fixtureinfo, "name2fixturedefs", None)
                    if not isinstance(names, (list, tuple)):
                        raise TypeError(
                            f"{item.nodeid}: names_closure の型が不正: {type(names)!r}"
                        )
                    if not isinstance(definitions, dict):
                        raise TypeError(
                            f"{item.nodeid}: name2fixturedefs の型が不正: "
                            f"{type(definitions)!r}"
                        )
                    closure = set()
                    for name in names:
                        if not isinstance(name, str):
                            raise TypeError(
                                f"{item.nodeid}: fixture 名の型が不正: {type(name)!r}"
                            )
                        fixturedefs = definitions.get(name)
                        if fixturedefs is None:
                            continue
                        if not isinstance(fixturedefs, (list, tuple)) or not fixturedefs:
                            raise TypeError(
                                f"{item.nodeid}: {name} の fixturedefs が不正: "
                                f"{type(fixturedefs)!r}"
                            )
                        fixturedef = fixturedefs[-1]
                        scope = getattr(fixturedef, "scope", None)
                        baseid = getattr(fixturedef, "baseid", None)
                        argname = getattr(fixturedef, "argname", None)
                        if not all(isinstance(value, str) for value in (scope, baseid, argname)):
                            raise TypeError(
                                f"{item.nodeid}: {name} の FixtureDef 属性が不正"
                            )
                        # function scope は node 間で instance を共有しない。空 baseid の
                        # pytest/plugin 組込み fixture も repo 固有の共有 fixture ではない。
                        if scope != "function" and baseid:
                            closure.add(f"{baseid}::{argname}[{scope}]")
                    return sorted(closure)

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
                            "fixture_closure": shared_fixture_closure(item),
                            "real_repo_stamps": (
                                [["real_repo_serial_node", getattr(
                                    item, "_izanagi_real_repo_serial_node",
                                )]]
                                if hasattr(item, "_izanagi_real_repo_serial_node")
                                else []
                            ),
                            "marks": [
                                {"args": list(mark.args),
                                 "kwargs": dict(mark.kwargs)}
                                for mark in marks
                            ],
                        })
                    consumers = {}
                    for entry in report:
                        for fixture in entry["fixture_closure"]:
                            consumers.setdefault(fixture, set()).add(
                                entry["canonical_node"]
                            )
                    if report:
                        report[0]["fixture_consumers"] = {
                            fixture: sorted(nodes)
                            for fixture, nodes in sorted(consumers.items())
                        }
                    Path(os.environ["IZANAGI_REAL_REPO_MARK_REPORT"]).write_text(
                        json.dumps(report, sort_keys=True), encoding="utf-8",
                    )
                """
            ),
            encoding="utf-8",
        )
        cache_dir = tmp / "pytest-cache"
        cache_values = cache_dir / "v" / "cache"
        if lastfailed_nodeids or cached_nodeids:
            cache_values.mkdir(parents=True)
        if lastfailed_nodeids:
            (cache_values / "lastfailed").write_text(
                json.dumps(dict.fromkeys(lastfailed_nodeids, True)),
                encoding="utf-8",
            )
        if cached_nodeids:
            (cache_values / "nodeids").write_text(
                json.dumps(list(cached_nodeids)), encoding="utf-8",
            )
        env = os.environ.copy()
        env["IZANAGI_REAL_REPO_MARK_REPORT"] = str(report_path)
        env["PYTHONPATH"] = os.pathsep.join(
            part for part in (str(tmp), env.get("PYTHONPATH", "")) if part
        )
        proc = _run_subprocess(
            [
                sys.executable, "-m", "pytest", "--collect-only", "-q",
                "-o", f"cache_dir={cache_dir}",
                *collection_options,
                "-p", "real_repo_collection_plugin", str(target),
            ],
            cwd=cwd,
            env=env,
        )
        assert proc.returncode == 0, (
            f"collection subprocess failed:\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
        return json.loads(report_path.read_text(encoding="utf-8"))


def _assert_xdist_group_contract(
    report: list[dict], expected_group_names: set[str] | frozenset[str],
) -> None:
    """全 collected item の marker 個数・表記・group 名閉包を検査する。"""
    actual_group_names = set()
    for entry in report:
        marks = entry["marks"]
        assert len(marks) <= 1, (
            "xdist_group marker は 1 node につき最大 1 個でなければならない: "
            f"nodeid={entry['nodeid']} marks={marks!r}"
        )
        if not marks:
            continue
        mark = marks[0]
        args = mark["args"]
        kwargs = mark["kwargs"]
        assert (
            len(args) == 1
            and isinstance(args[0], str)
            and not kwargs
        ), (
            "xdist_group 名は positional 引数 1 個で与えなければならない: "
            f"nodeid={entry['nodeid']} mark={mark!r}"
        )
        actual_group_names.add(args[0])
    assert actual_group_names == set(expected_group_names), (
        "xdist_group 名集合が独立 golden と不一致: "
        f"missing={sorted(set(expected_group_names) - actual_group_names)} "
        f"extra={sorted(actual_group_names - set(expected_group_names))}"
    )


def _fixture_consumers_from_report(report: list[dict]) -> dict[str, set[str]]:
    """per-item closure と subprocess 側 consumer 集約を相互検査する。"""
    actual: dict[str, set[str]] = {}
    declarations = []
    for entry in report:
        canonical = entry["canonical_node"]
        closure = entry.get("fixture_closure")
        assert isinstance(closure, list) and all(
            isinstance(fixture, str) for fixture in closure
        ), f"fixture_closure の型が不正: node={canonical!r} value={closure!r}"
        for fixture in closure:
            actual.setdefault(fixture, set()).add(canonical)
        if "fixture_consumers" in entry:
            declarations.append(entry["fixture_consumers"])
    assert len(declarations) == 1, (
        f"fixture consumer 集約は report に 1 個必要: count={len(declarations)}"
    )
    declared_raw = declarations[0]
    assert isinstance(declared_raw, dict), "fixture consumer 集約が dict でない"
    declared = {}
    for fixture, consumers in declared_raw.items():
        assert isinstance(fixture, str) and isinstance(consumers, list)
        assert all(isinstance(node, str) for node in consumers)
        declared[fixture] = set(consumers)
    assert declared == actual, (
        "fixture consumer 集約が per-item closure と不一致: "
        f"declared={declared!r} actual={actual!r}"
    )
    return actual


def _assert_fixture_closure_complete(
    report: list[dict], canonical_nodes: set[str] | frozenset[str],
) -> None:
    """正本を seed とする共有 fixture consumer 閉包が欠けていないことを検査する。"""
    consumers = _fixture_consumers_from_report(report)
    assert consumers, "fixture consumer 導出結果が空 — detector 退行の疑い"
    for filename, fixture_name in (
        ("test_s1_measurement_freeze.py", "real_known_axes_doc"),
        ("test_codex_reasoning_ab.py", "benchmark_snapshots"),
    ):
        literal = f"{filename}::{fixture_name}[module]"
        matches = [
            nodes for fixture, nodes in consumers.items()
            if fixture.endswith(literal)
        ]
        assert len(matches) == 1, (
            f"既知の共有 fixture literal が導出結果に一意に実在しない: {literal!r}"
        )
        assert len(matches[0]) >= 2, (
            f"既知の共有 fixture consumer が 2 未満: {literal!r} "
            f"consumers={sorted(matches[0])!r}"
        )
    seeded = {
        fixture for fixture, nodes in consumers.items()
        if nodes & set(canonical_nodes)
    }
    missing = {
        fixture: sorted(consumers[fixture] - set(canonical_nodes))
        for fixture in seeded
        if consumers[fixture] - set(canonical_nodes)
    }
    assert not missing, (
        "REAL_REPO_SERIAL_NODES が共有 fixture consumer について閉じていない: "
        f"missing={missing!r}"
    )


def _assert_no_direct_xdist_group_decorators(
    canonical_nodes: set[str] | frozenset[str], sources: dict[str, str],
) -> None:
    """canonical node の関数に手書き xdist_group decorator がないこと。"""
    assert canonical_nodes, "canonical node 集合が空では provenance を監査できない"
    nodes_by_file: dict[str, set[str]] = {}
    for canonical in canonical_nodes:
        filename, separator, function_name = canonical.partition("::")
        assert separator and filename and function_name, (
            f"canonical node が file::function 形でない: {canonical!r}"
        )
        nodes_by_file.setdefault(filename, set()).add(function_name)

    missing_sources = set(nodes_by_file) - set(sources)
    assert not missing_sources, (
        f"canonical node の source がない: {sorted(missing_sources)}"
    )
    missing_functions = []
    handwritten = []
    for filename, function_names in sorted(nodes_by_file.items()):
        module = ast.parse(sources[filename], filename=filename)
        functions = {
            node.name: node
            for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for function_name in sorted(function_names):
            function = functions.get(function_name)
            if function is None:
                missing_functions.append(f"{filename}::{function_name}")
                continue
            for decorator in function.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                target = decorator.func
                is_xdist_group = (
                    isinstance(target, ast.Attribute)
                    and target.attr == "xdist_group"
                ) or (
                    isinstance(target, ast.Name)
                    and target.id == "xdist_group"
                )
                if is_xdist_group:
                    handwritten.append(
                        f"{filename}::{function_name}:{decorator.lineno}"
                    )

    assert not missing_functions, (
        f"canonical node の関数定義が source にない: {missing_functions}"
    )
    assert not handwritten, (
        "REAL_REPO_SERIAL_NODES の xdist_group は hook 由来でなければならず、"
        f"手書き decorator を許さない: {handwritten}"
    )


def _assert_real_repo_collection_order(report: list[dict]) -> None:
    """実 collection の先頭 literal と writer/barrier 関係を検査する。"""
    expected_priority = (
        "test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused",
        "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
    )
    suite_conftest = _load_suite_conftest()
    assert tuple(suite_conftest.REAL_REPO_EXECUTION_PRIORITY) == expected_priority, (
        "conftest の real-repo priority が独立 literal と不一致"
    )
    real_repo_order = [
        entry["canonical_node"]
        for entry in report
        if entry["marks"] == [{"args": ["real-repo"], "kwargs": {}}]
    ]
    priority_positions = {
        node: [
            index for index, actual in enumerate(real_repo_order)
            if actual == node
        ]
        for node in expected_priority
    }
    assert all(priority_positions.values()), (
        "collection 後の real-repo priority node が欠落した: "
        f"positions={priority_positions!r}"
    )
    assert max(priority_positions[expected_priority[0]]) < min(
        priority_positions[expected_priority[1]]
    ), (
        "全 CLI instance が全 cache barrier instance より前でなければならない: "
        f"positions={priority_positions!r}"
    )
    writers = (
        "test_p3_s4_loop.py::test_drive_iteration_checkpoint_survives_across_calls",
        "test_p3_s4_loop_sort.py::test_drive_iteration_checkpoint_survives_across_calls",
        "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_writes_entry_and_checkpoint",
        "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_entry_failure_blocks_checkpoint",
    )
    barrier_index = real_repo_order.index(expected_priority[1])
    assert all(real_repo_order.index(writer) > barrier_index for writer in writers), (
        "実 submodule writer が CLI / cache barrier より前にある: "
        f"order={real_repo_order!r}"
    )


def test_real_repo_group_collection_exactly_matches_canonical_nodes():
    """全 group marker と real-repo node 集合を独立 golden で監査する。"""
    _require_pytest()
    report = _collect_xdist_group_report(HERE, cwd=ROOT)
    _assert_xdist_group_contract(report, _XDIST_GROUP_NAMES_GOLDEN)

    golden = set(_REAL_REPO_SERIAL_NODES_GOLDEN)
    configured = set(_load_suite_conftest().REAL_REPO_SERIAL_NODES)
    assert configured == golden, (
        "conftest.REAL_REPO_SERIAL_NODES が独立 golden と不一致: "
        f"missing={sorted(golden - configured)} "
        f"extra={sorted(configured - golden)}"
    )
    _assert_fixture_closure_complete(report, golden)

    # 系統 1 / 3 の各 fan-out から 1 node を落とすと、正本 seed の閉包検査が赤になる。
    for removed in (
        "test_s1_measurement_freeze.py::test_recorded_ccbench_pin_hold_and_release_positive_control",
        "test_codex_reasoning_ab.py::test_parent_numstat_controls_remain_pinned",
    ):
        try:
            _assert_fixture_closure_complete(report, golden - {removed})
        except AssertionError as exc:
            assert removed in str(exc), (
                f"欠落 control が意図した node を報告しなかった: {exc}"
            )
        else:
            raise AssertionError(f"共有 fixture consumer 欠落を検出しなかった: {removed}")

    # detector 自身の control: subprocess 側集約が最初の consumer だけを保存する
    # 退行を偽 report で注入し、per-item closure との相互検査が必ず赤になることを示す。
    consumers = _fixture_consumers_from_report(report)
    system1 = (
        "test_s1_measurement_freeze.py::"
        "test_recorded_ccbench_pin_hold_and_release_positive_control"
    )
    fanout_fixture = next(
        fixture for fixture, nodes in consumers.items()
        if system1 in nodes and len(nodes) > 1
    )
    fake_report = json.loads(json.dumps(report))
    declaration = next(
        entry["fixture_consumers"]
        for entry in fake_report if "fixture_consumers" in entry
    )
    declaration[fanout_fixture] = declaration[fanout_fixture][:1]
    try:
        _assert_fixture_closure_complete(fake_report, golden)
    except AssertionError as exc:
        assert "consumer 集約" in str(exc), (
            f"集約 detector control が意図した不変条件で赤にならなかった: {exc}"
        )
    else:
        raise AssertionError("最初の consumer しか保存しない偽 report を拒否しなかった")

    # detector 自身の control: 全 item の closure と集約を空へ壊した偽 report でも、
    # 既知 fixture の独立 control が必ず赤になることを示す。
    empty_report = json.loads(json.dumps(report))
    for entry in empty_report:
        entry["fixture_closure"] = []
        if "fixture_consumers" in entry:
            entry["fixture_consumers"] = {}
    try:
        _assert_fixture_closure_complete(empty_report, golden)
    except AssertionError as exc:
        assert "導出結果が空" in str(exc), (
            f"空 closure control が意図した不変条件で赤にならなかった: {exc}"
        )
    else:
        raise AssertionError("全 item の空 closure 退行を拒否しなかった")

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
        stamps = entry["real_repo_stamps"]
        collected_counts[canonical] += 1
        group_name = marks[0]["args"][0] if marks else None
        if canonical in golden:
            assert stamps == [["real_repo_serial_node", canonical]], (
                f"{nodeid} の runtime guard 印が正本由来の 1 個でない: {stamps!r}"
            )
            assert marks == exact_mark, (
                f"{nodeid} の xdist_group は real-repo 1 個だけでなければならない: "
                f"{marks!r}"
            )
            marked_counts[canonical] += 1
        else:
            assert stamps == [], (
                f"golden 外 instance {nodeid} に runtime guard 印がある: {stamps!r}"
            )
            assert group_name != "real-repo", (
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
    _assert_real_repo_collection_order(report)


def test_xdist_group_audit_rejects_synthetic_negative_controls():
    """kwargs・二重 marker の shape 負例が監査を必ず赤にする。"""
    _require_pytest()
    with tempfile.TemporaryDirectory(prefix="izanagi-xdist-mark-negative-") as raw_tmp:
        tmp = Path(raw_tmp)
        suite = tmp / "test_synthetic_xdist_groups.py"
        suite.write_text(
            textwrap.dedent(
                """
                import pytest

                @pytest.mark.xdist_group("real-repo", name="real_repo")
                def test_kwargs_name():
                    pass

                @pytest.mark.xdist_group("real-repo")
                @pytest.mark.xdist_group("real-repo")
                def test_duplicate_markers():
                    pass
                """
            ),
            encoding="utf-8",
        )
        report = _collect_xdist_group_report(suite, cwd=tmp)

    entries = {entry["canonical_node"]: entry for entry in report}
    controls = (
        (
            ("test_synthetic_xdist_groups.py::test_kwargs_name",),
            {"real-repo"},
            "positional 引数 1 個",
        ),
        (
            ("test_synthetic_xdist_groups.py::test_duplicate_markers",),
            {"real-repo"},
            "最大 1 個",
        ),
    )
    for canonicals, expected_names, expected_error in controls:
        try:
            _assert_xdist_group_contract(
                [entries[canonical] for canonical in canonicals], expected_names,
            )
        except AssertionError as exc:
            assert expected_error in str(exc), (
                f"{canonicals!r} が意図した不変条件で拒否されなかった: {exc}"
            )
        else:
            raise AssertionError(f"合成負例が監査を通過した: {canonicals!r}")


def test_xdist_group_name_set_audit_rejects_isolated_negative_controls():
    """集合だけが不正な underscore・missing-only・extra-only を拒否する。"""
    _require_pytest()
    with tempfile.TemporaryDirectory(prefix="izanagi-xdist-name-negative-") as raw_tmp:
        tmp = Path(raw_tmp)
        suite = tmp / "test_synthetic_xdist_group_names.py"
        suite.write_text(
            textwrap.dedent(
                """
                import pytest

                @pytest.mark.xdist_group("real_repo")
                def test_underscore_name():
                    pass

                @pytest.mark.xdist_group("real-repo")
                def test_missing_only_actual():
                    pass

                @pytest.mark.xdist_group("real-repo")
                def test_extra_only_expected():
                    pass

                @pytest.mark.xdist_group("unexpected-group")
                def test_extra_only_unexpected():
                    pass
                """
            ),
            encoding="utf-8",
        )
        report = _collect_xdist_group_report(suite, cwd=tmp)

    entries = {entry["canonical_node"]: entry for entry in report}
    for entry in entries.values():
        assert len(entry["marks"]) == 1, entry
        mark = entry["marks"][0]
        assert (
            len(mark["args"]) == 1
            and isinstance(mark["args"][0], str)
            and mark["kwargs"] == {}
        ), f"集合負例が marker shape まで壊している: {entry!r}"

    controls = (
        (
            ("test_synthetic_xdist_group_names.py::test_underscore_name",),
            {"real-repo"},
            "missing=['real-repo'] extra=['real_repo']",
        ),
        (
            ("test_synthetic_xdist_group_names.py::test_missing_only_actual",),
            {"missing-group", "real-repo"},
            "missing=['missing-group'] extra=[]",
        ),
        (
            (
                "test_synthetic_xdist_group_names.py::test_extra_only_expected",
                "test_synthetic_xdist_group_names.py::test_extra_only_unexpected",
            ),
            {"real-repo"},
            "missing=[] extra=['unexpected-group']",
        ),
    )
    for canonicals, expected_names, expected_error in controls:
        try:
            _assert_xdist_group_contract(
                [entries[canonical] for canonical in canonicals], expected_names,
            )
        except AssertionError as exc:
            assert expected_error in str(exc), (
                f"{canonicals!r} が集合 assertion だけで拒否されなかった: {exc}"
            )
        else:
            raise AssertionError(f"集合の合成負例が監査を通過した: {canonicals!r}")


def test_canonical_real_repo_nodes_have_no_handwritten_xdist_group_decorator():
    """canonical node の real-repo marker は conftest hook だけが付与する。"""
    configured = set(_load_suite_conftest().REAL_REPO_SERIAL_NODES)
    filenames = {canonical.partition("::")[0] for canonical in configured}
    sources = {
        filename: (HERE / filename).read_text(encoding="utf-8")
        for filename in filenames
    }
    _assert_no_direct_xdist_group_decorators(configured, sources)


def test_handwritten_xdist_group_decorator_control_is_rejected():
    """canonical node への手書き decorator を AST 監査が実際に拒否する。"""
    canonical = "test_synthetic_canonical.py::test_canonical"
    source = textwrap.dedent(
        """
        import pytest

        @pytest.mark.xdist_group("real-repo")
        def test_canonical():
            pass
        """
    )
    try:
        _assert_no_direct_xdist_group_decorators(
            {canonical}, {"test_synthetic_canonical.py": source},
        )
    except AssertionError as exc:
        assert "手書き decorator を許さない" in str(exc), exc
    else:
        raise AssertionError("手書き xdist_group decorator の合成負例が監査を通過した")


def test_real_repo_priority_order_is_literal_and_writers_follow_barrier():
    """通常・ff・nf の hook chain 後にも priority と barrier 順を保つ。"""
    _require_pytest()
    report = _collect_xdist_group_report(HERE, cwd=ROOT)
    _assert_real_repo_collection_order(report)
    nodeids = {
        entry["canonical_node"]: entry["nodeid"] for entry in report
    }
    cli = "test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused"
    barrier = (
        "test_s8b_binding_driftguards.py::"
        "test_run_block_broken_binding_manifest_refuses_and_writes_nothing"
    )
    controls = (
        (("--ff",), (nodeids[barrier],), ()),
        (("--nf",), (), (nodeids[cli],)),
    )
    for collection_options, lastfailed_nodeids, cached_nodeids in controls:
        report = _collect_xdist_group_report(
            HERE, cwd=ROOT, collection_options=collection_options,
            lastfailed_nodeids=lastfailed_nodeids,
            cached_nodeids=cached_nodeids,
        )
        _assert_real_repo_collection_order(report)

    # priority node が parameterize されても、raw 先頭 2 item ではなく
    # canonical node ごとの全 instance 境界で受理する。
    exact_mark = [{"args": ["real-repo"], "kwargs": {}}]
    writers = (
        "test_p3_s4_loop.py::test_drive_iteration_checkpoint_survives_across_calls",
        "test_p3_s4_loop_sort.py::test_drive_iteration_checkpoint_survives_across_calls",
        "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_writes_entry_and_checkpoint",
        "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_entry_failure_blocks_checkpoint",
    )
    canonical_nodes = (cli, cli, barrier, barrier, *writers)
    report = [
        {
            "nodeid": f"{canonical}[case-{index}]",
            "canonical_node": canonical,
            "marks": exact_mark,
        }
        for index, canonical in enumerate(canonical_nodes)
    ]
    _assert_real_repo_collection_order(report)


def test_protocol_builder_repo_tree_guard_is_wired_to_real_root():
    """SUT が repo-tree helper を実 ROOT に結線していることを実行時に監査する。"""
    _require_pytest()
    from orchestrator.tests import repo_tree_util
    from orchestrator.tests import test_s8b_protocol_builder as sut

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


def test_ratified_memo_has_a_real_resolution_payer():
    """active 世代解決の実走を毎 session 保証する正本 payer が memo を使わない ([T-117])。

    `real_repo_ratified_memo` は実 repo の `load_ratified_freeze` (git 39 本・4.4 秒) を
    process 内 1 回へ畳む。畳んだ node が増えても「解決失敗 → freeze-ratify refusal」の
    実走査を必ず 1 node が担う、という不変条件をここで固定する。全 node が memo へ
    移る退行 (= 実履歴走査が node 順序次第でしか走らなくなる) を殺す。
    """
    _require_pytest()
    from orchestrator.tests import test_s8b_binding_driftguards as driftguard_tests
    from orchestrator.tests import test_s8b_oracle_driver as driver_tests

    payer = driver_tests.test_nonnull_floor_without_active_generation_is_refused
    payer_source = inspect.getsource(payer)
    for token in ("ratified_memo", "patch_ratified_loader"):
        assert token not in payer_source, (
            f"正本 payer {payer.__name__} が active 世代 memo を使っている: {token}"
        )
    assert "root=ROOT" in payer_source, (
        f"正本 payer {payer.__name__} が実 repo root を渡していない"
    )

    opted_in = (
        driver_tests.test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing,
        driver_tests.test_active_resolution_and_manifest_structure_refusals_are_aggregated,
        driftguard_tests.test_run_block_broken_binding_manifest_refuses_and_writes_nothing,
        driftguard_tests.test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal,
    )
    for function in opted_in:
        assert "patch_ratified_loader" in inspect.getsource(function), (
            f"opt-in 面 {function.__name__} が memo を使っていない (配線の取り残し)"
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
                    out = Path(os.environ["IZANAGI_GROUP_PROBE_OUT"])
                    (out / "fifo.sentinel").write_text("a", encoding="utf-8")

                @pytest.mark.xdist_group("probe")
                def test_group_b():
                    out = Path(os.environ["IZANAGI_GROUP_PROBE_OUT"])
                    if os.environ.get("IZANAGI_ENFORCE_GROUP_FIFO"):
                        assert (out / "fifo.sentinel").read_text(
                            encoding="utf-8",
                        ) == "a"
                    _record("b")
                """
            ),
            encoding="utf-8",
        )

        grouped_out = tmp / "grouped"
        grouped_env = os.environ.copy()
        grouped_env["IZANAGI_GROUP_PROBE_OUT"] = str(grouped_out)
        grouped_env["IZANAGI_ENFORCE_GROUP_FIFO"] = "1"
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
        control_env.pop("IZANAGI_ENFORCE_GROUP_FIFO", None)
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


def test_effective_tempdir_is_not_tmpfs():
    """実効一時ディレクトリが tmpfs 族に無いこと (tmpfs はメモリ枠を直接食う)。

    ``tempfile.gettempdir()`` は自プロセス (pytest の ``tmp_path`` を含む) の置き場、
    ``TMPDIR`` は env を継承する subprocess の置き場。片方だけ健全でも足りない。
    fstype を 1 つも判定できないときだけ skip する (skip 条件を反転させない)。

    tmpfs を掴んだときの倒し方を 2 つに分ける (段 6 レビュー W2 の裁定):

    - **明示 ``TMPDIR`` が tmpfs → 赤。** ユーザーまたは結線が選んだ結果なので退行。
    - **``TMPDIR`` 未設定で環境既定が tmpfs → skip。** ``/tmp`` が tmpfs な distro
      (systemd 既定構成) では本 repo が何もしなくてもそうなる。無過失の赤にしない。

    **この分岐で落ちる検出力 (正直な記述)**: ``TMPDIR`` 未設定の環境では、既定の
    一時領域が tmpfs でも本 node は赤にならない。つまり「conftest が TMPDIR を
    設定しない」という本 repo の選択が、そういう distro で結果的にメモリ枠を
    食う構成になる事象は、本 node では捕まえられず skip 理由として出るだけである。
    捕まえるのは (1) 明示 ``TMPDIR`` が tmpfs な場合と、(2) source 上の結線
    (``test_suite_conftest_does_not_wire_tmpdir_to_tmpfs``、こちらは環境に依らず
    常に赤にできる) の 2 面で、M1 (conftest 末尾に ``setdefault("TMPDIR", "/dev/shm")``)
    のような結線退行は (2) が環境非依存で殺す。
    """
    checked = []
    offenders = []
    default_tmpfs = []
    for path, explicit in _effective_tmpdir_candidates():
        status, fstype = _tmpdir_verdict(path)
        if status == "unknown":
            continue
        checked.append((path, fstype))
        if status != "tmpfs":
            continue
        if explicit:
            offenders.append((path, fstype))
        else:
            default_tmpfs.append((path, fstype))
    if not checked:
        skip("/proc/self/mountinfo から実効一時ディレクトリの fstype を判定できない")
    assert not offenders, (
        "明示された TMPDIR が tmpfs 族にある — 使用量がユーザーの memory cgroup へ "
        "1:1 で課金される (Pegasus ログインノードの枠は 16 GiB、受入全走 1 回の "
        f"tmpfs peak は 7.39 GiB 実測): offenders={offenders!r} checked={checked!r}"
    )
    if default_tmpfs:
        detail = ", ".join(
            f"{path} (realpath={os.path.realpath(path)}, fstype={fstype})"
            for path, fstype in default_tmpfs
        )
        skip(
            "環境既定の一時領域が tmpfs である。ディスク上の TMPDIR を明示せよ "
            f"(tmpfs はユーザーの memory cgroup へ 1:1 で課金される): {detail}"
        )


def test_suite_conftest_does_not_wire_tmpdir_to_tmpfs():
    """conftest が一時領域を tmpfs へ結線していないこと (撤去した誘導の再発検出)。

    ``TMPDIR`` (env、subprocess へ継承) と ``tempfile.tempdir`` (in-process、``tmp_path``
    と ``tempfile.*``) の両方を見る。後者は env に出ないので実効 fstype 検査からは
    「環境既定」に見えてしまい、source 検査だけが殺せる (段 6 レビュー N2)。
    """
    source = (HERE / "conftest.py").read_text(encoding="utf-8")
    hits = find_tmpfs_tmpdir_wiring(source)
    assert not hits, (
        "conftest.py が一時領域を tmpfs へ向けている (メモリ枠へ課金される): "
        f"{hits!r}"
    )


def test_tmpdir_fstype_lookup_positive_and_negative_control():
    """合成 mount 表で ``_tmpdir_verdict`` の正負両方向と realpath 依存を固定する。

    合成表だけでは ``mountinfo_text`` を必ず明示で渡すため、実 ``/proc/self/mountinfo``
    を読む枝 (``mountinfo_text is None``) に一度も対照が掛からない。その枝が壊れると
    実効 fstype 検査は赤ではなく skip へ化けるので、実経路の対照を先に置く (段 6 MX2)。
    """
    # 実経路の対照: Linux では `/` の fstype は必ず判定できる。ここが None に落ちる
    # 実装は、実効 fstype 検査を「判定不能 → skip」で無言に通してしまう。
    if sys.platform.startswith("linux"):
        assert _fs_type("/") is not None, (
            "実 /proc/self/mountinfo 経路が判定不能に落ちている — この状態では "
            "test_effective_tempdir_is_not_tmpfs が赤ではなく skip へ化ける"
        )
    # 実経路の tmpfs 正例 (段 6 レビュー N3)。上の "None でない" 対照は、実読取枝が
    # tmpfs 行だけを落とす部分劣化を素通りする — 最長前方一致が `/` の実ディスクへ
    # 落ちるので "unknown" にすらならず、明示 tmpfs TMPDIR が偽緑で通る。
    if os.path.isdir("/dev/shm"):
        assert _fs_type("/dev/shm") in _TMPFS_FSTYPES, (
            "実 /proc/self/mountinfo 経路が tmpfs を tmpfs と判定できていない — "
            "この状態では明示 tmpfs TMPDIR が偽緑で通る: "
            f"actual={_fs_type('/dev/shm')!r}"
        )
    mountinfo = textwrap.dedent(
        """\
        30 1 9:0 / / rw,relatime shared:1 - xfs /dev/md0 rw,noquota
        26 30 0:5 / /dev rw,nosuid - devtmpfs devtmpfs rw,size=4096k
        32 26 0:27 / /dev/shm rw,nosuid,nodev shared:4 - tmpfs tmpfs rw,inode64
        41 26 0:33 / /dev/hugepages rw,relatime shared:17 - hugetlbfs hugetlbfs rw,pagesize=2M
        44 28 0:44 / /run/user/31609 rw,nosuid,nodev - tmpfs tmpfs rw,size=13421772k
        55 30 0:55 / /odd\\040name rw - tmpfs tmpfs rw
        60 30 0:60 / /scr rw,relatime - xfs /dev/sdb1 rw
        """
    )
    # 赤にできること (tmpfs 族を実際に検出する)。最長前方一致と 8 進エスケープ込み。
    tmpfs_cases = (
        ("/dev/shm", "tmpfs"),
        ("/dev/shm/sub/dir", "tmpfs"),
        ("/run/user/31609/x", "tmpfs"),
        ("/dev", "devtmpfs"),
        # 計算ノード bnode041 に実在する hugetlbfs (/dev/hugepages)。これもメモリ実体。
        ("/dev/hugepages/x", "hugetlbfs"),
        ("/odd name/x", "tmpfs"),
    )
    for path, expected in tmpfs_cases:
        assert _tmpdir_verdict(path, mountinfo, resolve=False) == ("tmpfs", expected), path
    # 過剰拒否しないこと (実ディスクを tmpfs と誤判定しない)。
    disk_cases = (
        ("/tmp", "xfs"),
        ("/scr/874750", "xfs"),
        ("/home/u/x", "xfs"),
        ("/dev-shm", "xfs"),
        ("/run/user-data", "xfs"),
        ("/odd nameish", "xfs"),
    )
    for path, expected in disk_cases:
        assert _tmpdir_verdict(path, mountinfo, resolve=False) == ("ok", expected), path
    # 判定不能は "unknown" (ここでだけ skip してよい状態)。
    assert _tmpdir_verdict("/tmp", "not a mountinfo table") == ("unknown", None)
    assert _tmpdir_verdict("/tmp", "") == ("unknown", None)

    # realpath が load-bearing であることの対照: symlink 越しの tmpfs を取り逃さない。
    base = os.path.realpath(tempfile.mkdtemp(prefix="izanagi-fstype-control-"))
    try:
        real = os.path.join(base, "real")
        link = os.path.join(base, "link")
        os.mkdir(real)
        os.symlink(real, link)
        synthetic = (
            f"70 1 0:70 / {base} rw - xfs /dev/sdc1 rw\n"
            f"71 70 0:71 / {real} rw - tmpfs tmpfs rw\n"
        )
        assert _tmpdir_verdict(link, synthetic) == ("tmpfs", "tmpfs")
        assert _tmpdir_verdict(link, synthetic, resolve=False) == ("ok", "xfs")
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_tmpfs_tmpdir_wiring_scanner_positive_and_negative_control():
    """``find_tmpfs_tmpdir_wiring`` が結線を実際に捕まえ、無関係な記述を誤検出しない。"""
    # 赤にできること。撤去前の conftest が使っていた「定数経由の間接代入」を含む。
    positives = (
        'import os\nos.environ["TMPDIR"] = "/dev/shm"\n',
        'import os\nos.environ.setdefault("TMPDIR", "/dev/shm")\n',
        'import os\n_SHM = "/dev/shm"\nos.environ["TMPDIR"] = _SHM\n',
        'import os\nos.environ["TMPDIR"] = "/run/user/31609/izanagi"\n',
        'import os\nos.putenv("TMPDIR", "/run/shm")\n',
        'import os\nos.environ.update({"TMPDIR": "/dev/shm"})\n',
        'import os\nos.environ.update(TMPDIR="/dev/shm")\n',
        'import os\njob = "1"\nos.environ["TMPDIR"] = f"/dev/shm/izanagi-{job}"\n',
        'from os import environ\nenviron["TMPDIR"] = "/dev/shm"\n',
        # env を経由しない in-process 結線 (段 6 レビュー N2)。これを見ないと
        # tmp_path と tempfile.* がまるごと tmpfs へ戻る変異が全緑で通る。
        'import tempfile\ntempfile.tempdir = "/dev/shm"\n',
        'import tempfile as tf\ntf.tempdir = "/run/shm"\n',
        'import tempfile\n_SHM = "/dev/shm"\ntempfile.tempdir = _SHM\n',
        'import tempfile\ntempfile.tempdir: str = "/dev/shm/izanagi"\n',
    )
    for source in positives:
        assert find_tmpfs_tmpdir_wiring(source), source
    # 過剰拒否しないこと。
    negatives = (
        '"""/dev/shm へは向けない、という説明だけの docstring。"""\n',
        'import os\n# os.environ["TMPDIR"] = "/dev/shm"  # 撤去済み\n',
        'import os\nos.environ["TMPDIR"] = "/scr/874750"\n',
        'import os\nos.environ["OTHER"] = "/dev/shm"\n',
        'import os\nshm = os.environ.get("TMPDIR", "/dev/shm")\n',
        'import os\nos.environ.setdefault("TMPDIR", "/tmp")\n',
        # 撤去前の conftest が実際に使っていた形。既定へ戻すだけなので hit にしない。
        'import tempfile\ntempfile.tempdir = None\n',
        'import tempfile\ntempfile.tempdir = "/scr/874750"\n',
        'import tempfile\nsaved = tempfile.tempdir\n',
    )
    for source in negatives:
        assert find_tmpfs_tmpdir_wiring(source) == [], source
    # 現行 conftest は negative 側であること (本番 source での対照)。
    # test_suite_conftest_does_not_wire_tmpdir_to_tmpfs と検査内容は重なるが、あちらは
    # 「conftest が汚れたら赤」、こちらは「scanner が本番 source で誤検出しない」の対照。
    conftest_hits = find_tmpfs_tmpdir_wiring(
        (HERE / "conftest.py").read_text(encoding="utf-8"))
    assert conftest_hits == [], (
        "本番 source (conftest.py) に対する scanner の対照が hit した — conftest が "
        "TMPDIR を tmpfs へ結線したか、scanner が誤検出している: "
        f"{conftest_hits!r}"
    )


# tmpfs 回帰ガード node と、その node 内で load-bearing な token。関数の外に置くのは
# 自己適用を恒真にしないため — 関数内の dict リテラルだと、自分自身の token 検査が
# 「dict にその文字列が書いてあるから通る」だけになる。
_TMPFS_GUARD_TOKENS = {
    "test_effective_tempdir_is_not_tmpfs": (
        "_tmpdir_verdict(", "assert not offenders",
    ),
    "test_suite_conftest_does_not_wire_tmpdir_to_tmpfs": (
        "find_tmpfs_tmpdir_wiring(", "assert not hits",
    ),
    "test_tmpdir_fstype_lookup_positive_and_negative_control": (
        # '_fs_type("/dev/shm")' は実 mountinfo 経路の tmpfs 正例 (段 6 レビュー N3)。
        # "None でない" だけの対照は tmpfs 行を落とす部分劣化を素通りする。
        "_tmpdir_verdict(", '_fs_type("/")', '_fs_type("/dev/shm")',
    ),
    "test_tmpfs_tmpdir_wiring_scanner_positive_and_negative_control": (
        # "tempfile.tempdir" は env を経由しない in-process 結線の対照 (段 6 レビュー N2)。
        "find_tmpfs_tmpdir_wiring(", "tempfile.tempdir",
    ),
    # 自己適用: この node 自身が「述語を実行する positive control」を持つこと。
    # "PYTEST_CURRENT_TEST" は分類器の対照 (段 6 レビュー N1) — これを失うと本 node が
    # pytest 下で無言に SKIP へ化け、以降の control が自動経路で一度も走らなくなる。
    "test_tmpdir_guards_are_present_and_load_bearing": (
        "_run_and_classify(", "_patched_module_attr(", "PYTEST_CURRENT_TEST",
    ),
}


def _patched_module_attr(name: str, replacement):
    """本 module の属性を差し替える (ガード node が参照する述語の注入口)。"""
    return mock.patch.object(sys.modules[__name__], name, replacement)


def _skip_exception_types() -> tuple[type[BaseException], ...]:
    """``skiputil.skip`` が投げうる例外型を実行環境に応じて集める。

    ``skiputil.skip`` は ``PYTEST_CURRENT_TEST`` があると ``pytest.skip`` を呼ぶ。その
    ``_pytest.outcomes.Skipped`` の MRO は ``Skipped → OutcomeException → BaseException``
    で **``Exception`` 派生ではない**。``except Skip`` にも ``except Exception`` にも
    掛からないので、捕り漏らすと注入した control の skip が呼出し側を貫通し、
    **ガード node 自身が pytest 下で必ず SKIP へ化ける** (= control (2) 以降が自動経路で
    一度も走らない)。段 6 レビュー N1 が受入全走の 4202/19 → 4201/20 で実証した退行。

    pytest 不在環境 (素の runner) でも壊れないよう遅延 import で解決し、無ければ
    ``Skip`` だけを対象にする。
    """
    types: list[type[BaseException]] = [Skip]
    try:
        import pytest
    except ImportError:
        return tuple(types)
    skipped = getattr(pytest.skip, "Exception", None)
    if isinstance(skipped, type) and issubclass(skipped, BaseException):
        types.append(skipped)
    return tuple(types)


def _run_and_classify(function) -> str:
    """テスト関数を実行し ``"pass"`` / ``"fail"`` / ``"skip"`` のどれかを返す。"""
    try:
        function()
    except _skip_exception_types():
        return "skip"
    except AssertionError:
        return "fail"
    return "pass"


def test_tmpdir_guards_are_present_and_load_bearing():
    """tmpfs 回帰ガードが実際に赤くできることを、述語を注入して実行し固定する。

    文字列 pin だけでは意味的な骨抜きを通す — 要求 token を全部残したまま
    ``offenders.append`` を殺すと 5 node 全緑のまま実効ガードだけが死ぬ (段 6 レビューが
    変異ハーネスで実証、MX3)。そこで tmpfs を返す述語を注入してガード node を実際に
    実行し、赤 (明示 TMPDIR) と skip (環境既定、W2 の分岐) に倒れることを検査する。
    文字列 pin は削除・素朴な恒真化を早期に名指しするための補助として残す。

    自己適用: 本 node 自身も ``_TMPFS_GUARD_TOKENS`` に載せ、positive control を捨てて
    文字列 pin だけへ戻す退行を検出する。ただし 5 node を**同時に**全部消す変異は、
    検出する側もろとも消えるのでここでは捕まえられない
    (``test_plain_runner_coverage.py`` の自己適用 node と同じ限界)。
    """
    source_text = Path(__file__).resolve().read_text(encoding="utf-8")
    for name, tokens in sorted(_TMPFS_GUARD_TOKENS.items()):
        function = globals().get(name)
        assert callable(function), f"tmpfs 回帰ガード node が消えている: {name}"
        assert f"def {name}(" in source_text, (
            f"tmpfs 回帰ガード node が本ファイルの定義として存在しない: {name}"
        )
        source = inspect.getsource(function)
        for token in tokens:
            assert token in source, (
                f"{name} の load-bearing な検査が失われている (恒真化): {token!r}"
            )
    # skip 条件の反転禁止: 判定不能のときだけ skip する形であること。
    effective = inspect.getsource(globals()["test_effective_tempdir_is_not_tmpfs"])
    assert 'status == "unknown"' in effective and "if not checked:" in effective, (
        "実効 fstype 検査の skip 条件が『判定不能のときだけ』でなくなっている"
    )

    # --- 述語を実行する positive control (文字列 pin では殺せない骨抜き用) -------------
    # (0) 分類器そのものの対照。(1)〜(4) は注入した述語が ``skiputil.skip`` を呼ぶ経路を
    #     通るが、pytest 下ではそれが ``Exception`` 派生でない ``Skipped`` になる。
    #     ``_run_and_classify`` が捕り漏らすと本 node 自身が SKIP へ化け、以降の control が
    #     一度も実行されない (段 6 レビュー N1 が受入全走で実証)。ここで先に殺す。
    def raises_suite_skip():
        skip("classifier control")

    try:
        import pytest as pytest_for_control
    except ImportError:
        pytest_for_control = None
    if pytest_for_control is not None:
        with mock.patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "control (call)"}):
            try:
                outcome = _run_and_classify(raises_suite_skip)
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException as exc:  # noqa: BLE001
                # 貫通をここで捕らえて赤へ変換する。捕らえないと本 node ごと SKIP へ
                # 化けて退行が無言になる (N1 の退行そのものの再現になってしまう)。
                outcome = f"escaped:{type(exc).__name__}"
        assert outcome == "skip", (
            "_run_and_classify が pytest 経路の skip を skip として分類できていない — "
            "この状態では本 node が pytest 下で必ず SKIP になり、以下の control が "
            f"自動経路で一度も実行されない: {outcome}"
        )

    def tmpfs_verdict(*args, **kwargs):
        return ("tmpfs", "tmpfs")

    def disk_verdict(*args, **kwargs):
        return ("ok", "xfs")

    def wiring_hit(source):
        return [(1, "/dev/shm")]

    def wiring_clean(source):
        return []

    # (1) 明示 TMPDIR が tmpfs 判定 → 赤。offenders 収集や assert を殺すとここが落ちる。
    with mock.patch.dict(os.environ, {"TMPDIR": "/dev/shm"}), \
            _patched_module_attr("_tmpdir_verdict", tmpfs_verdict):
        outcome = _run_and_classify(test_effective_tempdir_is_not_tmpfs)
    assert outcome == "fail", (
        f"実効 fstype 検査が明示 TMPDIR の tmpfs 入力で赤にならない (恒真化): {outcome}"
    )

    # (2) TMPDIR 未設定 + 環境既定が tmpfs → skip (W2 の分岐が生きていること)。
    with mock.patch.dict(os.environ), \
            _patched_module_attr("_tmpdir_verdict", tmpfs_verdict):
        os.environ.pop("TMPDIR", None)
        outcome = _run_and_classify(test_effective_tempdir_is_not_tmpfs)
    assert outcome == "skip", (
        f"環境既定が tmpfs のとき W2 の skip 分岐が働いていない: {outcome}"
    )

    # (3) 実ディスク判定なら緑 (恒真に赤くして「検出している」と見せる形の排除)。
    with mock.patch.dict(os.environ, {"TMPDIR": "/scr/izanagi"}), \
            _patched_module_attr("_tmpdir_verdict", disk_verdict):
        outcome = _run_and_classify(test_effective_tempdir_is_not_tmpfs)
    assert outcome == "pass", (
        f"実効 fstype 検査が実ディスクの入力で緑にならない (過剰拒否): {outcome}"
    )

    # (4) conftest 結線検査: hit があれば赤、無ければ緑。hits 判定を殺すと (4a) が落ちる。
    with _patched_module_attr("find_tmpfs_tmpdir_wiring", wiring_hit):
        outcome = _run_and_classify(test_suite_conftest_does_not_wire_tmpdir_to_tmpfs)
    assert outcome == "fail", (
        f"conftest 結線検査が hit 入力で赤にならない (恒真化): {outcome}"
    )
    with _patched_module_attr("find_tmpfs_tmpdir_wiring", wiring_clean):
        outcome = _run_and_classify(test_suite_conftest_does_not_wire_tmpdir_to_tmpfs)
    assert outcome == "pass", (
        f"conftest 結線検査が hit 無しの入力で緑にならない (過剰拒否): {outcome}"
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
