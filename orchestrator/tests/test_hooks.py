# -*- coding: utf-8 -*-
"""H3 hooks (hooks/guard_write.py / guard_bash.py) の単体テスト (machine 非依存)。

hook は .claude/settings.json の PreToolUse から単体スクリプトとして呼ばれるため
package ではない — importlib で直接ロードし、判定核 decide() を叩く。
EVOLVE-BLOCK 構造の検査は tmp に合成した骨格 (template patch と同型) で行い、
実 submodule 側はマーカー適用時のみ検証 (未適用なら skip)。
"""
from __future__ import annotations

from collections import Counter
import errno
import importlib.util
import io
import json
import os
from pathlib import Path
import py_compile
import shutil
import stat
import subprocess
import sys
import tempfile
from unittest.mock import patch

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_ORCH)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import source_digest                               # noqa: E402
from tools.acceptance_shards import _git_common_dir, _validate_shared_root  # noqa: E402
from skiputil import skip, skip_conditional_unrun                # noqa: E402


def _load_source_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    with open(path, "rb") as stream:
        source_bytes = stream.read()
    exec(compile(source_bytes, path, "exec", dont_inherit=True), mod.__dict__)
    return mod


def _load_hook(name: str):
    path = os.path.join(_REPO, "hooks", f"{name}.py")
    return _load_source_module(name, path)


GW = _load_hook("guard_write")
GB = _load_hook("guard_bash")
GR = _load_hook("guard_read")
GA = _load_hook("guard_agent")


def _load_pegasus_registry_loader():
    path = os.path.join(_REPO, "tools", "pegasus_admission_registry.py")
    spec = importlib.util.spec_from_file_location(
        "pegasus_admission_registry_for_test_hooks", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PAR = _load_pegasus_registry_loader()

# template patch (silo-backoff-fixed.patch) と同型の合成骨格。
_SKELETON = """#pragma once
#include "atomic_tool.hh"

class Backoff {
public:
  static void backoff(size_t clocks_per_us) {
    uint64_t start(rdtscp()), stop;
    // EVOLVE-BLOCK-BEGIN silo-backoff-magnitude
    // 説明コメント (骨格の一部)
#if BACKOFF_FIXED >= 0
    double now_backoff = static_cast<double>(BACKOFF_FIXED);
#else
    double now_backoff = Backoff_.load(std::memory_order_acquire);
#endif
    // EVOLVE-BLOCK-END silo-backoff-magnitude
    // spin loop (領域外)
    while (stop - start < clocks_per_us * now_backoff) stop = rdtscp();
  }
};
"""
_PAYLOAD_OLD = "    double now_backoff = static_cast<double>(BACKOFF_FIXED);\n"


def _mk_fixture_repo() -> str:
    """tmp に repo_root を合成 (external/ccbench/include/backoff.hh + output/...)。"""
    root = tempfile.mkdtemp(prefix="izanagi-hooktest-")
    inc = os.path.join(root, "external", "ccbench", "include")
    os.makedirs(inc)
    with open(os.path.join(inc, "backoff.hh"), "w", encoding="utf-8") as f:
        f.write(_SKELETON)
    os.makedirs(os.path.join(root, "external", "ccbench", "cmake"))
    with open(os.path.join(root, "external", "ccbench", "cmake", "Options.cmake"),
              "w", encoding="utf-8") as f:
        f.write('set(CCBENCH_VAL_SIZE 4 CACHE STRING "v")\n')
    hooks = os.path.join(root, "hooks")
    os.makedirs(hooks)
    for name in ("guard_write.py", "guard_bash.py", "codex_guard.sh"):
        with open(os.path.join(hooks, name), "w", encoding="utf-8") as f:
            f.write(f"# fixture {name}\n")
    with open(os.path.join(hooks, "README.md"), "w", encoding="utf-8") as f:
        f.write("fixture README\n")
    return root


def _edit(root, rel, old, new, tool="Edit", replace_all=False):
    return GW.decide(tool, {"file_path": os.path.join(root, rel),
                            "old_string": old, "new_string": new,
                            "replace_all": replace_all}, repo_root=root)


def _patch(root, command, *, cwd=None, tool_input=None):
    payload = {"command": command}
    if tool_input:
        payload.update(tool_input)
    return GW.decide(
        "apply_patch", payload, repo_root=root,
        cwd=root if cwd is None else cwd,
    )


def _guard_main(module, raw: str) -> int:
    with patch.object(module.sys, "stdin", io.StringIO(raw)):
        return module.main()


# ---------- guard_write: 管轄と防護対象 ----------

def test_write_outside_jurisdiction_allowed():
    root = _mk_fixture_repo()
    try:
        ok, _ = GW.decide("Write", {"file_path": os.path.join(root, "docs", "x.md"),
                                    "content": "wal.jsonl の話"}, repo_root=root)
        assert ok, "管轄外 (docs) の Write は素通しであるべき"
    finally:
        shutil.rmtree(root)


def test_wal_campaign_lock_buildcache_denied():
    root = _mk_fixture_repo()
    try:
        for rel in ("output/campaigns/c1/runs/wal.jsonl",
                    "output/campaigns/c1/runs/anything.log",
                    "output/campaigns/c1/campaign.lock",
                    "external/ccbench/build-variants/silo_x_t0/meta.json"):
            ok, why = GW.decide("Write", {"file_path": os.path.join(root, rel),
                                          "content": "x"}, repo_root=root)
            assert not ok, f"{rel} への Write は拒否されるべき"
            assert "規律2" in why
        ok, _ = GW.decide("Edit", {"file_path": os.path.join(
            root, "output/campaigns/c1/runs/wal.jsonl"),
            "old_string": "a", "new_string": "b"}, repo_root=root)
        assert not ok
        # reports/ や insights/ (射影・散文) は防護対象でない
        ok, _ = GW.decide("Write", {"file_path": os.path.join(
            root, "output/campaigns/c1/reports/report.md"),
            "content": "x"}, repo_root=root)
        assert ok
    finally:
        shutil.rmtree(root)


def test_exploration_campaign_wal_and_lock_write_tools_denied():
    """M12: exploration campaign root を guard_write の集合から外す変異を kill する。"""
    root = _mk_fixture_repo()
    try:
        for tool in ("Write", "Edit", "NotebookEdit"):
            path_key = "notebook_path" if tool == "NotebookEdit" else "file_path"
            for rel in (
                "output/exploration/campaigns/c1/runs/wal.jsonl",
                "output/exploration/campaigns/c1/campaign.lock",
            ):
                ok, _ = GW.decide(
                    tool, {path_key: os.path.join(root, rel)}, repo_root=root)
                assert not ok, f"{tool} で exploration proof chain への書込が通った: {rel}"
    finally:
        shutil.rmtree(root)


def test_exploration_namespace_marker_write_tools_denied():
    """M14-W: guard_write の exploration marker 条件を無効化する変異を kill。"""
    root = _mk_fixture_repo()
    try:
        for tool in ("Write", "Edit", "NotebookEdit"):
            path_key = "notebook_path" if tool == "NotebookEdit" else "file_path"
            for rel in (
                "output/exploration/namespace.json",
                "output/exploration/autonomous-trials/t1/namespace.json",
            ):
                marker = os.path.join(root, rel)
                ok, _ = GW.decide(tool, {path_key: marker}, repo_root=root)
                assert not ok, f"{tool} で exploration marker への書込が通った: {rel}"
        for rel in (
            "output/exploration/namespace.json?",
            "output/exploration/autonomous-trials/t1/attempts.jsonl",
            "/tmp/custom/exploration/namespace.json",
        ):
            ok, why = GW.decide(
                "Write", {"file_path": os.path.join(root, rel)}, repo_root=root)
            assert ok, f"marker でない sibling が誤拒否された: {rel} ({why})"
    finally:
        shutil.rmtree(root)


def test_exploration_projection_and_trial_journal_write_tools_allowed():
    """exploration root 全体を誤って guard_write 対象にする過剰拒否を検出する。"""
    root = _mk_fixture_repo()
    try:
        for rel in (
            "output/exploration/campaigns/c1/reports/report.md",
            "output/exploration/campaigns/c1/insights/note.json",
            "output/exploration/autonomous-trials/t1/attempts.jsonl",
        ):
            ok, why = GW.decide(
                "Write", {"file_path": os.path.join(root, rel)}, repo_root=root)
            assert ok, f"proof chain 外の exploration Write が誤拒否された: {rel} ({why})"
    finally:
        shutil.rmtree(root)


def test_s8b_freeze_namespace_denied():
    # F6a (C1-11): output/s8b-freeze/ 配下 (approval/active/revocation/世代 file) への
    # 直接 Write/Edit を拒否 (誤操作抑止)。これは認証防壁ではなく事故防止。
    root = _mk_fixture_repo()
    try:
        for rel in ("output/s8b-freeze/holdout_freeze.v2.g1.json",
                    "output/s8b-freeze/approvals/" + "a" * 64 + ".json",
                    "output/s8b-freeze/active/" + "b" * 64 + ".json",
                    "output/s8b-freeze/revocations/" + "c" * 64 + ".json",
                    "output/s8b-freeze/active-cancellations/" + "d" * 64 + ".json"):
            ok, why = GW.decide("Write", {"file_path": os.path.join(root, rel),
                                          "content": "x"}, repo_root=root)
            assert not ok, f"{rel} への Write は拒否されるべき"
            assert "s8b-freeze" in why or "誤操作抑止" in why
        ok, _ = GW.decide("Edit", {"file_path": os.path.join(
            root, "output/s8b-freeze/approvals/" + "e" * 64 + ".json"),
            "old_string": "a", "new_string": "b"}, repo_root=root)
        assert not ok, "s8b-freeze 配下の Edit も拒否されるべき"
        # namespace 外の output/ (v1 以外の散文) は防護対象でない。
        ok, _ = GW.decide("Write", {"file_path": os.path.join(
            root, "output/insights/note.md"), "content": "x"}, repo_root=root)
        assert ok, "s8b-freeze 外の output/ Write は素通し"
    finally:
        shutil.rmtree(root)


def test_ccbench_surface_limited_to_evolve_sources():
    root = _mk_fixture_repo()
    try:
        for rel in ("external/ccbench/cmake/Options.cmake",       # F1: 人間 template 専有
                    "external/ccbench/silo/transaction.cc",
                    "external/ccbench/include/tuple.h"):
            ok, why = GW.decide("Write", {"file_path": os.path.join(root, rel),
                                          "content": "x"}, repo_root=root)
            assert not ok, f"{rel} は編集面外のはず"
        ok, _ = GW.decide("NotebookEdit", {"notebook_path": os.path.join(
            root, "external/ccbench/include/backoff.hh")}, repo_root=root)
        assert not ok, "ccbench への NotebookEdit は編集面外"
    finally:
        shutil.rmtree(root)


def test_symlinked_evolve_source_denied():
    root = _mk_fixture_repo()
    try:
        hh = os.path.join(root, "external/ccbench/include/backoff.hh")
        os.remove(hh)
        os.symlink(os.path.join(root, "external/ccbench/cmake/Options.cmake"), hh)
        ok, _ = _edit(root, "external/ccbench/include/backoff.hh", "a", "b")
        assert not ok, "symlink で実体を挿げ替えた EVOLVE ソースは realpath で弾く"
    finally:
        shutil.rmtree(root)


def test_symlinked_output_tree_still_protects():
    """3 巡目 (2026-07-04) write-bypass: output/ が別ボリュームへの symlink でも WAL・
    campaign.lock への直接 Write を拒否する (root/camp_root を realpath で揃え fail-open を塞ぐ)。
    root FS 逼迫でデータを別ボリュームへ逃がす運用 (memory: scratch on /home) で現実的トリガ。"""
    root = _mk_fixture_repo()
    real_out = tempfile.mkdtemp(prefix="izanagi-realout-")
    try:
        os.symlink(real_out, os.path.join(root, "output"))    # output/ を symlink 化
        for rel in ("output/campaigns/c/runs/wal.jsonl",
                    "output/campaigns/c/campaign.lock"):
            ok, why = GW.decide("Write", {"file_path": os.path.join(root, rel),
                                          "content": "x"}, repo_root=root)
            assert not ok, f"output/ symlink 経由でも {rel} は拒否 (#5 fail-open): {why}"
    finally:
        shutil.rmtree(root)
        shutil.rmtree(real_out, ignore_errors=True)


def test_notebookedit_decoy_file_path_denied():
    """3 巡目 (2026-07-04) write-bypass: NotebookEdit は notebook_path に書くので、良性 file_path
    decoy を添えても notebook_path 側 (ccbench/WAL) の管轄判定を回避できない (notebook_path 優先)。"""
    root = _mk_fixture_repo()
    try:
        for nb in ("external/ccbench/evil.ipynb",
                   "external/ccbench/include/backoff.hh",       # designated だが NotebookEdit 不可
                   "output/campaigns/c/runs/wal.jsonl"):
            ok, _ = GW.decide("NotebookEdit", {
                "notebook_path": os.path.join(root, nb),
                "file_path": "/tmp/decoy.txt"}, repo_root=root)
            assert not ok, f"NotebookEdit decoy で {nb} への書込が通った (#7)"
    finally:
        shutil.rmtree(root)


# ---------- guard_write: Codex apply_patch adapter ----------

def test_parse_apply_patch_exact_directives_scans_all_blocks():
    command = """*** Begin Patch
*** Add File: docs/a.md
+a
*** End Patch
*** Begin Patch
*** Delete File: docs/b.md
*** End Patch
  *** Update File: output/campaigns/c/runs/anything.log
*** update File: output/campaigns/c/campaign.lock
*** Move to: docs/orphan.md
"""
    assert GW.parse_apply_patch(command) == [
        ("add", "docs/a.md"),
        ("delete", "docs/b.md"),
        ("move_to", "docs/orphan.md"),
    ]


def test_apply_patch_normal_directives_allowed():
    root = _mk_fixture_repo()
    try:
        command = """*** Begin Patch
*** Add File: docs/add.md
+x
*** Update File: docs/update.md
@@
-a
+b
*** Delete File: docs/delete.md
*** Update File: docs/old.md
*** Move to: docs/new.md
*** End Patch
"""
        ok, why = _patch(root, command)
        assert ok, f"通常の apply_patch directive が誤拒否された: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_protected_directive_matrix_denied():
    root = _mk_fixture_repo()
    try:
        commands = {
            "add": "*** Add File: output/campaigns/c/runs/wal.jsonl",
            "update": "*** Update File: output/campaigns/c/campaign.lock",
            "delete": "*** Delete File: build-variants/x/meta.json",
            "move_to": (
                "*** Update File: docs/safe.md\n"
                "*** Move to: output/s8b-freeze/approvals/x.json"
            ),
        }
        for kind, directive in commands.items():
            ok, why = _patch(
                root, f"*** Begin Patch\n{directive}\n*** End Patch\n")
            assert not ok, f"{kind} の防護 path が通った: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_move_both_directions_denied():
    root = _mk_fixture_repo()
    try:
        for source, destination in (
            ("output/campaigns/c/runs/anything.log", "docs/safe.log"),
            ("docs/safe.log", "output/campaigns/c/runs/anything.log"),
        ):
            command = (
                "*** Begin Patch\n"
                f"*** Update File: {source}\n"
                f"*** Move to: {destination}\n"
                "*** End Patch\n"
            )
            ok, why = _patch(root, command)
            assert not ok, f"Move {source} -> {destination} が通った: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_all_paths_composed():
    root = _mk_fixture_repo()
    try:
        command = """*** Begin Patch
*** Update File: docs/safe.md
*** Add File: output/campaigns/c/runs/anything.log
+forged
*** End Patch
"""
        ok, why = _patch(root, command)
        assert not ok, f"後置した防護 path が見落とされた: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_reports_all_denials():
    root = _mk_fixture_repo()
    try:
        wal = "output/campaigns/c/runs/anything.log"
        freeze = "output/s8b-freeze/approvals/x.json"
        command = (
            "*** Begin Patch\n"
            f"*** Update File: {wal}\n"
            f"*** Add File: {freeze}\n"
            "*** End Patch\n"
        )
        ok, why = _patch(root, command)
        assert not ok
        assert wal in why and freeze in why, why
        assert "WAL" in why and "s8b-freeze" in why, why
    finally:
        shutil.rmtree(root)


def test_apply_patch_all_begin_blocks_scanned():
    root = _mk_fixture_repo()
    try:
        command = """*** Begin Patch
*** Add File: docs/safe.md
+safe
*** End Patch
*** Begin Patch
*** Update File: output/campaigns/c/runs/anything.log
*** End Patch
"""
        ok, why = _patch(root, command)
        assert not ok, f"第 2 block の防護 path が見落とされた: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_broken_first_block_does_not_hide_later_protected_path():
    root = _mk_fixture_repo()
    try:
        command = """*** Begin Patch
*** Add File: docs/broken.md
+missing end
*** Begin Patch
*** Update File: output/campaigns/c/runs/anything.log
*** End Patch
"""
        ok, why = _patch(root, command)
        assert not ok, f"壊れた第 1 block の後段が見落とされた: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_body_directive_lookalikes_allowed():
    root = _mk_fixture_repo()
    try:
        protected = "output/campaigns/c/runs/anything.log"
        command = f"""*** Begin Patch
*** Add File: docs/example.md
+*** Update File: {protected}
+本文中の *** Delete File: {protected}
  *** Update File: {protected}
-*** Delete File: {protected}
*** End Patch
"""
        ok, why = _patch(root, command)
        assert ok, f"本文中の directive 風文字列が誤拒否された: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_exact_case_and_whitespace():
    root = _mk_fixture_repo()
    try:
        command = """*** Begin Patch
*** update File: output/campaigns/c/runs/anything.log
*** UPDATE FILE: output/campaigns/c/campaign.lock
  *** Update File: output/s8b-freeze/approvals/x.json
*** End Patch
"""
        ok, why = _patch(root, command)
        assert ok, f"case 違い・行頭空白を directive と誤認した: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_absolute_relative_dotdot():
    root = _mk_fixture_repo()
    subdir = os.path.join(root, "sub")
    os.makedirs(subdir)
    try:
        absolute = os.path.join(root, "output", "campaigns", "c", "runs", "x")
        ok, _ = _patch(root, f"*** Delete File: {absolute}\n", cwd=subdir)
        assert not ok, "absolute の防護 path は拒否されるべき"

        ok, _ = _patch(
            root, "*** Update File: ../output/campaigns/c/runs/x\n", cwd=subdir)
        assert not ok, "cwd から .. 解決した防護 path は拒否されるべき"

        ok, why = _patch(root, "*** Update File: ../docs/safe.md\n", cwd=subdir)
        assert ok, f"cwd から docs へ解決する control が誤拒否された: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_subdirectory_cwd_relative_path_denied():
    root = _mk_fixture_repo()
    cwd = os.path.join(root, "docs", "deeper")
    os.makedirs(cwd)
    try:
        command = "*** Add File: ../../output/campaigns/c/runs/anything.log\n"
        ok, why = _patch(root, command, cwd=cwd)
        assert not ok, f"payload cwd 基準の相対 path が見落とされた: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_relative_path_invalid_cwd_denied():
    root = _mk_fixture_repo()
    try:
        command = "*** Add File: docs/safe.md\n"
        for cwd in ("", "relative/cwd", os.path.join(root, "missing")):
            ok, why = GW.decide(
                "apply_patch", {"command": command}, repo_root=root, cwd=cwd)
            assert not ok, f"cwd={cwd!r} の相対 path が通った"
            assert "payload cwd" in why and "docs/safe.md" in why
    finally:
        shutil.rmtree(root)


def test_apply_patch_absolute_path_does_not_require_cwd():
    root = _mk_fixture_repo()
    try:
        safe = os.path.join(root, "docs", "safe.md")
        ok, why = GW.decide(
            "apply_patch", {"command": f"*** Add File: {safe}\n"},
            repo_root=root, cwd="")
        assert ok, f"absolute path に不要な cwd を要求した: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_component_boundaries():
    root = _mk_fixture_repo()
    try:
        for rel in (
            "build-variants-copy/x/meta.json",
            "output/s8b-freezer/approvals/x.json",
            "output/campaigns/c/campaign.lock.bak",
            "external/ccbenchmark/cmake/Options.cmake",
        ):
            ok, why = _patch(root, f"*** Update File: {rel}\n")
            assert ok, f"component boundary 外が誤拒否された: {rel} ({why})"
    finally:
        shutil.rmtree(root)


def test_apply_patch_file_path_decoy_ignored():
    root = _mk_fixture_repo()
    try:
        command = "*** Update File: output/campaigns/c/runs/anything.log\n"
        ok, why = _patch(
            root, command, tool_input={"file_path": os.path.join(root, "docs", "safe")})
        assert not ok, f"file_path decoy で command 側の防護 path が通った: {why}"
    finally:
        shutil.rmtree(root)


def test_write_tool_command_is_not_parsed_as_apply_patch():
    root = _mk_fixture_repo()
    try:
        command = "*** Update File: output/campaigns/c/runs/anything.log\n"
        ok, why = GW.decide("Write", {"command": command}, repo_root=root)
        assert ok, f"Write の command を apply_patch と誤配送した: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_orphan_move_to_protected_denied():
    root = _mk_fixture_repo()
    try:
        target = "output/s8b-freeze/approvals/x.json"
        ok, why = _patch(root, f"*** Move to: {target}\n")
        assert not ok and target in why, why
    finally:
        shutil.rmtree(root)


def test_apply_patch_protected_leaf_and_neighbor_matrix():
    root = _mk_fixture_repo()
    try:
        protected = (
            "output/campaigns/c/runs/anything.log",
            "output/exploration/campaigns/c/runs/anything.log",
            "output/campaigns/c/campaign.lock",
            "output/exploration/campaigns/c/campaign.lock",
            "build-variants",
            "build-variants/x/meta.json",
            "output/s8b-freeze",
            "output/s8b-freeze/approvals/x.json",
            "output/s8b-freeze/active/x.json",
            "output/s8b-freeze/revocations/x.json",
            "output/exploration/namespace.json",
            "output/exploration/autonomous-trials/t1/namespace.json",
        )
        for rel in protected:
            ok, why = _patch(root, f"*** Update File: {rel}\n")
            assert not ok, f"apply_patch 防護 leaf が通った: {rel} ({why})"

        allowed = (
            "output/campaigns/c/reports/report.md",
            "output/exploration/campaigns/c/insights/note.json",
            "output/exploration/autonomous-trials/t1/attempts.jsonl",
            "output/insights/note.md",
        )
        for rel in allowed:
            ok, why = _patch(root, f"*** Update File: {rel}\n")
            assert ok, f"proof chain 外の neighbor が誤拒否された: {rel} ({why})"
    finally:
        shutil.rmtree(root)


def test_apply_patch_ccbench_surface_and_move_directions():
    root = _mk_fixture_repo()
    try:
        for rel in GW.EVOLVE_BLOCK_SOURCES:
            ok, why = _patch(root, f"*** Update File: external/ccbench/{rel}\n")
            assert ok, f"designated source が誤拒否された: {rel} ({why})"

        for rel in (
            "external/ccbench/cmake/Options.cmake",
            "external/ccbench/include/tuple.h",
            "external/ccbench/cc/silo/other.cc",
        ):
            ok, why = _patch(root, f"*** Update File: {rel}\n")
            assert not ok, f"non-designated ccbench source が通った: {rel} ({why})"

        for source, destination in (
            ("external/ccbench/include/tuple.h", "docs/tuple.h"),
            ("docs/tuple.h", "external/ccbench/include/tuple.h"),
        ):
            command = f"*** Update File: {source}\n*** Move to: {destination}\n"
            ok, why = _patch(root, command)
            assert not ok, f"ccbench Move {source} -> {destination} が通った: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_delete_and_move_source_check_lexical_symlink_entry():
    root = _mk_fixture_repo()
    safe = os.path.join(root, "docs", "safe.txt")
    protected = os.path.join(root, "output", "campaigns", "c", "runs", "ref")
    protected_target = os.path.join(
        root, "output", "campaigns", "c", "runs", "target")
    safe_alias = os.path.join(root, "docs", "protected-target-alias")
    os.makedirs(os.path.dirname(safe))
    os.makedirs(os.path.dirname(protected))
    with open(safe, "w", encoding="utf-8") as f:
        f.write("safe\n")
    with open(protected_target, "w", encoding="utf-8") as f:
        f.write("protected\n")
    os.symlink(safe, protected)
    os.symlink(protected_target, safe_alias)
    try:
        rel = os.path.relpath(protected, root)
        ok, why = _patch(root, f"*** Update File: {rel}\n")
        assert ok, f"通常 Update に Delete/Move の lexical 規則を誤適用した: {why}"

        ok, why = _patch(root, f"*** Delete File: {rel}\n")
        assert not ok, f"protected lexical symlink の Delete が通った: {why}"

        command = f"*** Update File: {rel}\n*** Move to: docs/moved-ref\n"
        ok, why = _patch(root, command)
        assert not ok, f"protected lexical symlink の Move 元が通った: {why}"

        alias_rel = os.path.relpath(safe_alias, root)
        ok, why = _patch(root, f"*** Delete File: {alias_rel}\n")
        assert not ok, f"protected realpath を指す Delete が通った: {why}"
    finally:
        shutil.rmtree(root)


def _mk_apply_patch_ancestor_alias_fixture(root):
    safe = os.path.join(root, "docs", "safe.txt")
    protected_dir = os.path.join(root, "output", "campaigns", "c", "runs")
    os.makedirs(os.path.dirname(safe), exist_ok=True)
    os.makedirs(protected_dir, exist_ok=True)
    with open(safe, "w", encoding="utf-8") as f:
        f.write("safe\n")
    os.symlink("..", os.path.join(root, "docs", "repo-alias"))
    os.symlink("../../../../docs/safe.txt", os.path.join(protected_dir, "ref"))


def test_apply_patch_delete_resolves_ancestors_but_not_final_symlink():
    root = _mk_fixture_repo()
    try:
        _mk_apply_patch_ancestor_alias_fixture(root)
        command = """*** Begin Patch
*** Delete File: docs/repo-alias/output/campaigns/c/runs/ref
*** End Patch
"""
        ok, why = _patch(root, command)
        assert not ok, f"祖先 alias 経由の protected entry Delete が通った: {why}"
    finally:
        shutil.rmtree(root)


def test_apply_patch_move_source_resolves_ancestors_but_not_final_symlink():
    root = _mk_fixture_repo()
    try:
        _mk_apply_patch_ancestor_alias_fixture(root)
        command = """*** Begin Patch
*** Update File: docs/repo-alias/output/campaigns/c/runs/ref
*** Move to: docs/moved-ref
@@
-safe
+moved
*** End Patch
"""
        ok, why = _patch(root, command)
        assert not ok, f"祖先 alias 経由の protected entry Move 元が通った: {why}"
    finally:
        shutil.rmtree(root)


# ---------- T-956: hooks/ self-guard ----------

def _mk_t956_aliases(root):
    os.makedirs(os.path.join(root, "a"), exist_ok=True)
    os.makedirs(os.path.join(root, "subdir"), exist_ok=True)
    os.makedirs(os.path.join(root, "docs"), exist_ok=True)
    os.symlink("../hooks", os.path.join(root, "docs", "hooks-alias"))

    outside = tempfile.mkdtemp(prefix="izanagi-t956-alias-")
    file_alias = os.path.join(outside, "file-alias")
    hardlink = os.path.join(outside, "hardlink")
    os.symlink(os.path.join(root, "hooks", "guard_write.py"), file_alias)
    os.link(os.path.join(root, "hooks", "guard_write.py"), hardlink)

    safe = os.path.join(outside, "safe")
    with open(safe, "w", encoding="utf-8") as stream:
        stream.write("safe\n")
    os.symlink(safe, os.path.join(root, "hooks", "outside-link"))

    base = os.path.join(outside, "base")
    os.makedirs(base)
    os.symlink(os.path.join(root, "subdir"), os.path.join(base, "a"))
    dotdot_alias = os.path.join(base, "a", "..", "hooks", "guard_write.py")
    return outside, file_alias, hardlink, dotdot_alias


def test_t956_guard_write_rejects_r01_through_r08_path_aliases():
    root = _mk_fixture_repo()
    outside, file_alias, hardlink, dotdot_alias = _mk_t956_aliases(root)
    try:
        cases = {
            "R01": "./hooks/guard_write.py",
            "R02": "a/../hooks/guard_write.py",
            "R03": os.path.join(root, "hooks", "guard_write.py"),
            "R04": "docs/hooks-alias/guard_write.py",
            "R05": file_alias,
            "R06": hardlink,
            "R07": "hooks/outside-link",
            "R08": dotdot_alias,
        }
        for case_id, path in cases.items():
            ok, why = GW.decide(
                "Edit", {"file_path": path}, repo_root=root)
            assert not ok, f"{case_id} が通った: {path!r} ({why})"
    finally:
        shutil.rmtree(root)
        shutil.rmtree(outside)


def test_t956_guard_write_keeps_legacy_canonical_denials_f1():
    """F1: raw canonical への移行前に拒否していた 4 形を deny union で維持する。"""
    root = _mk_fixture_repo()
    outside = tempfile.mkdtemp(prefix="izanagi-t956-f1-legacy-")
    try:
        os.makedirs(os.path.join(outside, "inner"))
        os.symlink(os.path.join(outside, "inner"), os.path.join(root, "jump"))
        exploration = os.path.join(
            root, "output", "exploration", "trials", "t1")
        os.makedirs(exploration)
        os.symlink(exploration, os.path.join(root, "alias"))

        cases = {
            "campaign": os.path.join(
                root, "jump", "..", "output", "campaigns", "c", "runs", "x"),
            "freeze": os.path.join(
                root, "jump", "..", "output", "s8b-freeze", "active", "x"),
            "ccbench": os.path.join(
                root, "jump", "..", "external", "ccbench", "cmake", "Options.cmake"),
            "exploration": os.path.join(
                root, "jump", "..", "alias", "namespace.json"),
        }
        for label, path in cases.items():
            ok, why = GW.decide(
                "Write", {"file_path": path, "content": "x"}, repo_root=root)
            assert not ok, f"F1 legacy canonical の {label} が通った: {path!r} ({why})"
    finally:
        shutil.rmtree(root)
        shutil.rmtree(outside)


def test_t956_guard_write_keeps_raw_canonical_denials_f1():
    """F1: legacy canonical だけへ戻して raw 起点の追加拒否を失わない。"""
    root = _mk_fixture_repo()
    outside = tempfile.mkdtemp(prefix="izanagi-t956-f1-raw-")
    try:
        base = os.path.join(outside, "base")
        os.makedirs(base)
        os.makedirs(os.path.join(root, "subdir"))
        os.symlink(os.path.join(root, "subdir"), os.path.join(base, "jump"))
        cases = {
            "campaign": os.path.join(
                base, "jump", "..", "output", "campaigns", "c", "runs", "x"),
            "freeze": os.path.join(
                base, "jump", "..", "output", "s8b-freeze", "active", "x"),
            "ccbench": os.path.join(
                base, "jump", "..", "external", "ccbench", "cmake", "Options.cmake"),
            "exploration": os.path.join(
                base, "jump", "..", "output", "exploration", "namespace.json"),
        }
        for label, path in cases.items():
            ok, why = GW.decide(
                "Write", {"file_path": path, "content": "x"}, repo_root=root)
            assert not ok, f"F1 raw canonical の {label} が通った: {path!r} ({why})"
    finally:
        shutil.rmtree(root)
        shutil.rmtree(outside)


def test_t956_hook_loader_executes_source_bytes_not_matching_pyc():
    root = tempfile.mkdtemp(prefix="izanagi-t956-loader-")
    path = os.path.join(root, "fixture_hook.py")
    try:
        with open(path, "w", encoding="utf-8") as stream:
            stream.write('VALUE = "poison"\n')
        py_compile.compile(path, doraise=True)
        metadata = os.stat(path)
        with open(path, "w", encoding="utf-8") as stream:
            stream.write('VALUE = "source"\n')
        os.utime(path, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))

        module = _load_source_module("t956_source_loader_fixture", path)
        assert module.VALUE == "source", \
            "hook test loader が source bytes でなく matching cache を実行した"
    finally:
        shutil.rmtree(root)


def test_t956_load_hook_executes_source_bytes_not_matching_pyc():
    """G2: public test-loader wiring itself must bypass a matching stale pyc."""
    root = tempfile.mkdtemp(prefix="izanagi-t956-load-hook-")
    hooks = os.path.join(root, "hooks")
    os.makedirs(hooks)
    path = os.path.join(hooks, "fixture_hook.py")
    try:
        with open(path, "w", encoding="utf-8") as stream:
            stream.write('VALUE = "poison"\n')
        py_compile.compile(path, doraise=True)
        metadata = os.stat(path)
        with open(path, "w", encoding="utf-8") as stream:
            stream.write('VALUE = "source"\n')
        os.utime(path, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))

        with patch.dict(_load_hook.__globals__, {"_REPO": root}):
            module = _load_hook("fixture_hook")
        assert module.VALUE == "source", \
            "_load_hook が source bytes でなく matching cache を実行した"
    finally:
        shutil.rmtree(root)


def test_t956_guard_write_rejects_r09_through_r16_patch_directives():
    root = _mk_fixture_repo()
    outside, _, hardlink, _ = _mk_t956_aliases(root)
    main = tempfile.mkdtemp(prefix="izanagi-t956-main-")
    worktree = os.path.join(main, ".claude", "worktrees", "t956")
    os.makedirs(os.path.dirname(worktree))
    shutil.copytree(root, worktree, symlinks=True)
    try:
        cases = {
            "R09": (root, root, "*** Add File: hooks/new_guard.py"),
            "R10": (root, root, "*** Update File: hooks/guard_bash.py"),
            "R11": (root, root, "*** Delete File: hooks/codex_guard.sh"),
            "R12": (root, root,
                    "*** Update File: hooks/guard_write.py\n"
                    "*** Move to: docs/guard_write.py"),
            "R13": (root, root,
                    "*** Update File: docs/helper.py\n"
                    "*** Move to: hooks/helper.py"),
            "R14": (root, root, "*** Delete File: hooks/outside-link"),
            "R15": (root, root, f"*** Update File: {hardlink}"),
            "R16": (worktree, main,
                    "*** Update File: .claude/worktrees/t956/hooks/guard_write.py"),
        }
        for case_id, (repo_root, cwd, command) in cases.items():
            ok, why = _patch(repo_root, command, cwd=cwd)
            assert not ok, f"{case_id} が通った: {command!r} ({why})"
    finally:
        shutil.rmtree(root)
        shutil.rmtree(outside)
        shutil.rmtree(main)


def test_t956_guard_write_rejects_r59_through_r61_hook_artifacts():
    root = _mk_fixture_repo()
    try:
        cases = {
            "R59": "hooks/__pycache__/guard_write.cpython-310.pyc",
            "R60": "hooks/json.pyc",
            "R61": "hooks/json.so",
            "direct-meta": "hooks/*.py",
        }
        for case_id, path in cases.items():
            ok, why = GW.decide(
                "Write", {"file_path": path, "content": "poison"},
                repo_root=root)
            assert not ok, f"{case_id} が通った: {path!r} ({why})"
    finally:
        shutil.rmtree(root)


def test_t956_guard_write_rejects_apply_patch_literal_hooks_meta_name():
    """F2: apply_patch は glob 展開せず hooks/ 内に `*.py` を実作成する。"""
    root = _mk_fixture_repo()
    try:
        ok, why = _patch(root, "*** Add File: hooks/*.py")
        assert not ok, f"F2 hooks/*.py の literal Add File が通った: {why}"
    finally:
        shutil.rmtree(root)


def test_t956_guard_write_rejects_r62_and_r64_decoded_payload_strings():
    for case_id, raw in (
        ("R62", '{"tool_name":"apply_patch","tool_input":'
                '{"command":["\\u0068ooks/guard_write.py"]}}'),
        ("R64", '{"tool_name":"apply_patch","tool_input":'
                '{"command":["hooks"]}}'),
    ):
        assert _guard_main(GW, raw) == 2, \
            f"{case_id} の decode 後 hooks token が fail-open"


def test_t956_guard_write_readme_exception_is_exact_and_inode_safe():
    root = _mk_fixture_repo()
    readme = os.path.join(root, "hooks", "README.md")
    try:
        ok, why = GW.decide("Edit", {"file_path": "hooks/README.md"}, repo_root=root)
        assert ok, f"A01 regular README が誤拒否された: {why}"
        for case_id, directive in (
            ("A02", "*** Update File: hooks/README.md"),
            ("A03", "*** Delete File: hooks/README.md"),
        ):
            ok, why = _patch(root, directive)
            assert ok, f"{case_id} regular README が誤拒否された: {why}"

        os.link(readme, os.path.join(root, "README-hardlink"))
        ok, _ = GW.decide("Edit", {"file_path": readme}, repo_root=root)
        assert not ok, "st_nlink > 1 の README 例外が通った"
        os.unlink(os.path.join(root, "README-hardlink"))

        os.unlink(readme)
        os.symlink("../docs/readme-target", readme)
        ok, _ = GW.decide("Edit", {"file_path": readme}, repo_root=root)
        assert not ok, "final component が symlink の README 例外が通った"

        os.unlink(readme)
        ok, why = GW.decide("Edit", {"file_path": readme}, repo_root=root)
        assert ok, f"存在しない exact README の新規作成が誤拒否された: {why}"
    finally:
        shutil.rmtree(root)


def test_t956_guard_write_readme_conditions_have_independent_detectors():
    """README 例外の lexical/canonical/regular/non-symlink を一理由ずつ発火。"""
    root = _mk_fixture_repo()
    outside = tempfile.mkdtemp(prefix="izanagi-t956-readme-conditions-")
    readme = os.path.join(root, "hooks", "README.md")
    try:
        # lexical exact だけを外す: ancestor alias の実体は exact README、現物条件は全て真。
        os.symlink("hooks", os.path.join(root, "hooks-alias"))
        alias = os.path.join(root, "hooks-alias", "README.md")
        ok, _ = GW.decide("Edit", {"file_path": alias}, repo_root=root)
        assert not ok, "lexical exact 条件を外した README alias が通った"

        # raw canonical exact だけを外す: abspath 後は exact、OS 解決後は repo 外の regular。
        os.makedirs(os.path.join(outside, "inner"))
        os.makedirs(os.path.join(outside, "hooks"))
        outside_readme = os.path.join(outside, "hooks", "README.md")
        with open(outside_readme, "w", encoding="utf-8") as stream:
            stream.write("outside\n")
        os.symlink(os.path.join(outside, "inner"), os.path.join(root, "jump"))
        canonical_mismatch = os.path.join(
            root, "jump", "..", "hooks", "README.md")
        ok, _ = GW.decide(
            "Edit", {"file_path": canonical_mismatch}, repo_root=root)
        assert not ok, "raw canonical exact 条件を外した README path が通った"

        # regular だけを外す: FIFO は exact・non-symlink・st_nlink == 1。
        os.unlink(readme)
        os.mkfifo(readme)
        metadata = os.lstat(readme)
        assert not stat.S_ISREG(metadata.st_mode)
        assert not stat.S_ISLNK(metadata.st_mode) and metadata.st_nlink == 1
        ok, _ = GW.decide("Edit", {"file_path": readme}, repo_root=root)
        assert not ok, "regular 条件を外した FIFO README が通った"

        # non-symlink は S_ISREG に隠れるため、regular だけを synthetic に真へ固定する。
        symlink_metadata = type(
            "SymlinkMetadata", (), {"st_mode": stat.S_IFLNK, "st_nlink": 1})()
        synthetic_path = os.path.join(outside, "synthetic-symlink")
        real_lstat = os.lstat

        def synthetic_lstat(path, *args, **kwargs):
            if os.fspath(path) == synthetic_path:
                return symlink_metadata
            return real_lstat(path, *args, **kwargs)

        with patch.object(GW.os, "lstat", side_effect=synthetic_lstat), \
                patch.object(GW.stat, "S_ISREG", return_value=True):
            assert not GW._readme_exception_allowed(
                synthetic_path, readme, readme, root), \
                "non-symlink 条件を外した synthetic README が通った"
    finally:
        shutil.rmtree(root)
        shutil.rmtree(outside)


def test_t956_guard_write_accepts_a04_a05_and_a25_through_a27():
    root = _mk_fixture_repo()
    other = tempfile.mkdtemp(prefix="izanagi-t956-other-")
    try:
        cases = {
            "A04": GW.decide(
                "Edit", {"file_path": "docs/t956-note.md"}, repo_root=root),
            "A05": GW.decide(
                "Edit", {"file_path": os.path.join(
                    other, "hooks", "guard_write.py")}, repo_root=root),
            "A25": _patch(root, "*** Add File: ~/hooks/x.py"),
            "A27": _patch(root, "*** Add File: hook{,s}/x.py"),
        }
        for case_id, (ok, why) in cases.items():
            assert ok, f"{case_id} が誤拒否された: {why}"
    finally:
        shutil.rmtree(root)
        shutil.rmtree(other)


def test_t956_guard_bash_rejects_adopted_literal_writer_matrix():
    root = _mk_fixture_repo()
    outside, file_alias, hardlink, dotdot_alias = _mk_t956_aliases(root)
    os.symlink("hooks", os.path.join(root, "Hooks"))
    try:
        cases = {
            "R17": "printf pwn > ./hooks/guard_write.py",
            "R18": "printf pwn > a/../hooks/guard_write.py",
            "R19": f"printf pwn > {root}/hooks/guard_write.py",
            "R21": f"printf pwn > {file_alias}",
            "R22": f"printf pwn > {hardlink}",
            "R25": "printf pwn > Hooks/guard_write.py",
            "R26": "rm -rf hooks/",
            "R27": "rm -f hooks/*",
            "R34": f"printf pwn > {dotdot_alias}",
            "R35": "tar -xf /tmp/payload.tar -C hooks",
            "R36": 'printf x > hooks/guard_write.py "$(date)"',
            "R37": "printf x > hooks/guard_write.py `date`",
            "R38": "cat <(printf x) > hooks/guard_write.py",
            "R39": "eval 'printf x > hooks/guard_write.py'",
            "R40": "printf x | xargs -I{} sh -c 'printf {} > hooks/guard_write.py'",
            "R41": "printf x > 'hooks/guard_write.py",
            "R45": "find hooks -delete",
            "R59": ("cp /tmp/poison.pyc "
                    "hooks/__pycache__/guard_write.cpython-310.pyc"),
            "R60": "cp /tmp/poison.pyc hooks/json.pyc",
            "R61": "cp /tmp/poison.so hooks/json.so",
        }
        for case_id, command in cases.items():
            ok, why = GB.decide(command, repo_root=root)
            assert not ok, f"{case_id} が通った: {command!r} ({why})"

        expanded = f"{root}/hooks/guard_write.py"
        original_expanduser = os.path.expanduser
        with patch.object(
                GB.os.path, "expanduser",
                side_effect=lambda value: (
                    expanded if value == "~/t956-repo/hooks/guard_write.py"
                    else original_expanduser(value))):
            ok, why = GB.decide(
                "printf pwn > ~/t956-repo/hooks/guard_write.py", repo_root=root)
        assert not ok, f"R20 が通った: {why}"
    finally:
        shutil.rmtree(root)
        shutil.rmtree(outside)


def test_t956_guard_bash_rejects_r57_and_r58_as_single_reason_cases():
    root = _mk_fixture_repo()
    outside, _, hardlink, _ = _mk_t956_aliases(root)
    try:
        ok, why = GB.decide(f"printf bad > {hardlink}", repo_root=root)
        assert not ok, f"R57 external hardlink alias が通った: {why}"

        command = "ln -sfn ../.codex/hooks.json hooks/README.md"
        ok, why = GB.decide(command, repo_root=root)
        assert not ok, f"R58 README entry replacement が通った: {why}"
    finally:
        shutil.rmtree(root)
        shutil.rmtree(outside)


def _assert_t956_inode_scan_failure_denied(module, root, target):
    def failing_walk(_path, *, followlinks=False, onerror=None):
        assert followlinks is False and onerror is not None
        onerror(PermissionError("synthetic hooks listing failure"))
        return iter(())

    with patch.object(module.os, "walk", side_effect=failing_walk):
        if module is GW:
            ok, why = module.decide(
                "Edit", {"file_path": target}, repo_root=root)
        else:
            ok, why = module.decide(
                f"printf bad > {target}", repo_root=root)
    assert not ok, f"{module.__name__} が hooks listing error で fail-open: {why}"


def _assert_t956_inode_stat_failure_denied(module, root, target):
    failed_entry = os.path.join(root, "hooks", "guard_write.py")
    real_stat = os.stat

    def failing_stat(path, *args, **kwargs):
        if os.fspath(path) == failed_entry:
            raise PermissionError("synthetic hooks entry stat failure")
        return real_stat(path, *args, **kwargs)

    with patch.object(module.os, "stat", side_effect=failing_stat):
        if module is GW:
            ok, why = module.decide(
                "Edit", {"file_path": target}, repo_root=root)
        else:
            ok, why = module.decide(
                f"printf bad > {target}", repo_root=root)
    assert not ok, f"{module.__name__} が hooks stat error で fail-open: {why}"


def test_t956_hardlink_inode_scan_errors_fail_closed_in_both_guards():
    root = _mk_fixture_repo()
    target = os.path.join(root, "docs", "ordinary.txt")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as stream:
        stream.write("ordinary\n")
    try:
        for module in (GW, GB):
            _assert_t956_inode_scan_failure_denied(module, root, target)
            _assert_t956_inode_stat_failure_denied(module, root, target)
    finally:
        shutil.rmtree(root)


def test_t956_missing_hooks_root_allows_ordinary_writes_in_both_guards():
    """G1: absent hooks/ means an empty inode index, not a failed scan."""
    root = tempfile.mkdtemp(prefix="izanagi-t956-no-hooks-")
    target = os.path.join(root, "docs", "ordinary.txt")
    os.makedirs(os.path.dirname(target))
    with open(target, "w", encoding="utf-8") as stream:
        stream.write("ordinary\n")
    try:
        cases = {
            "Write": GW.decide(
                "Write", {"file_path": target, "content": "replacement"},
                repo_root=root),
            "Edit": GW.decide(
                "Edit", {"file_path": target, "old_string": "ordinary",
                         "new_string": "replacement"}, repo_root=root),
            "apply_patch": _patch(root, "*** Update File: docs/ordinary.txt"),
            "Bash": GB.decide(f"cp /tmp/new {target}", repo_root=root),
        }
        for surface, (ok, why) in cases.items():
            assert ok, f"hooks/ 不在時に通常 {surface} が誤拒否された: {why}"
    finally:
        shutil.rmtree(root)


def test_t956_hardlink_inode_index_is_built_once_per_decide():
    """Each lazy inode index scans its own root at most once per decide()."""
    root = _mk_fixture_repo()
    outside, _, hardlink, _ = _mk_t956_aliases(root)
    real_walk = os.walk
    hooks_root = os.path.realpath(os.path.join(root, "hooks"))
    authority_root = os.path.realpath(GB._AUTHORITY_ROOT)
    try:
        command = (
            f"*** Update File: {hardlink}\n"
            f"*** Delete File: {hardlink}\n"
        )
        with patch.object(GW.os, "walk", wraps=real_walk) as walk:
            ok, _ = _patch(root, command)
        write_roots = Counter(
            os.path.realpath(os.fspath(call.args[0]))
            for call in walk.call_args_list)
        assert not ok
        assert walk.call_count == 1 and write_roots == Counter({hooks_root: 1}), \
            (f"guard_write inode scans={dict(write_roots)} "
             f"count={walk.call_count}")

        with patch.object(GB.os, "walk", wraps=real_walk) as walk:
            ok, _ = GB.decide(
                f"printf bad > {hardlink} && rm -f {hardlink}", repo_root=root)
        bash_roots = Counter(
            os.path.realpath(os.fspath(call.args[0]))
            for call in walk.call_args_list)
        assert not ok
        assert walk.call_count == 2 and bash_roots == Counter({
            hooks_root: 1,
            authority_root: 1,
        }), (f"guard_bash inode scans={dict(bash_roots)} "
             f"count={walk.call_count}")
    finally:
        shutil.rmtree(root)
        shutil.rmtree(outside)


def test_t956_guard_bash_rejects_r63_decoded_payload_string():
    raw = ('{"tool_input":{"command":'
           '["\\u0068ooks/guard_write.py"]}}')
    assert _guard_main(GB, raw) == 2, \
        "R63 の decode 後 hooks token が fail-open"


def test_t956_guard_bash_rejects_readme_writes_a17_through_a19():
    root = _mk_fixture_repo()
    try:
        for case_id, command in {
            "A17": "sed -i 's/old/new/' hooks/README.md",
            "A18": "printf '%s\\n' note > hooks/README.md",
            "A19": "rm hooks/README.md",
        }.items():
            ok, why = GB.decide(command, repo_root=root)
            assert not ok, f"{case_id} は裁定 §3 で reject: {why}"
    finally:
        shutil.rmtree(root)


def test_t956_guard_bash_accepts_a06_through_a16_reads():
    root = _mk_fixture_repo()
    outside, file_alias, _, _ = _mk_t956_aliases(root)
    try:
        cases = {
            "A06": "cat hooks/guard_write.py",
            "A07": "grep -n classify_path hooks/guard_write.py",
            "A08": f"cat {file_alias}",
            "A09": "cat hooks/*",
            "A10": "git diff -- hooks/guard_write.py",
            "A11": "dd if=hooks/guard_write.py of=/tmp/copy",
            "A12": "find hooks -type f -print",
            "A13": "sort hooks/guard_write.py",
            "A14": "awk '{print}' hooks/guard_write.py",
            "A15": "python3 hooks/guard_bash.py",
            "A16": ("python3 -m py_compile hooks/guard_bash.py "
                    "tools/check_ai_provenance.py"),
        }
        for case_id, command in cases.items():
            ok, why = GB.decide(command, repo_root=root)
            assert ok, f"{case_id} が誤拒否された: {command!r} ({why})"
    finally:
        shutil.rmtree(root)
        shutil.rmtree(outside)


def test_t956_guard_bash_accepts_a20_through_a24_component_boundaries():
    root = _mk_fixture_repo()
    try:
        cases = {
            "A20": "printf '%s\\n' note > docs/t956-note.md",
            "A21": "rm -f hooks-copy/guard_write.py",
            "A22": "rm -f myhooks/guard_write.py",
            "A23": "rm -f Hooks/guard_write.py",
            "A24": "rm -f $'hoo\u0301ks/guard_write.py'",
        }
        for case_id, command in cases.items():
            ok, why = GB.decide(command, repo_root=root)
            assert ok, f"{case_id} が誤拒否された: {command!r} ({why})"
    finally:
        shutil.rmtree(root)


# ---------- T-2146: acceptance issuer authority subtree ----------

_T2146_AUTHORITY_ROOT = "/work/1/SFC/tanab/dev-wave-authority"
_T2146_AUTHORITY_PUBLIC_KEY = os.path.join(
    _T2146_AUTHORITY_ROOT, "acceptance-issuer-public-key.pem")
_T2146_AUTHORITY_FUTURE = os.path.join(
    _T2146_AUTHORITY_ROOT, "t2146-do-not-create.pem")


def _t2146_assert_denied(result, label):
    ok, why = result
    assert not ok, f"T-2146 authority write が通った [{label}]: {why}"
    assert why, f"T-2146 authority deny に理由が無い [{label}]"


def test_t2146_guard_write_rejects_authority_root_and_descendants_for_all_tools():
    root = _mk_fixture_repo()
    try:
        assert GW._AUTHORITY_ROOT == GB._AUTHORITY_ROOT == _T2146_AUTHORITY_ROOT
        assert not os.path.lexists(_T2146_AUTHORITY_FUTURE), \
            "T-2146 未存在 path fixture が既に存在する"
        targets = (
            _T2146_AUTHORITY_ROOT,
            _T2146_AUTHORITY_PUBLIC_KEY,
            _T2146_AUTHORITY_FUTURE,
        )
        for tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            path_key = "notebook_path" if tool == "NotebookEdit" else "file_path"
            for target in targets:
                _t2146_assert_denied(
                    GW.decide(tool, {path_key: target}, repo_root=root),
                    f"{tool}:{target}",
                )
    finally:
        shutil.rmtree(root)


def test_t2146_guard_write_rejects_every_authority_apply_patch_directive():
    root = _mk_fixture_repo()
    try:
        future = _T2146_AUTHORITY_FUTURE
        assert not os.path.lexists(future), \
            "T-2146 未存在 apply_patch path fixture が既に存在する"
        cases = {
            "add": f"*** Add File: {future}\n+t2146\n",
            "update": f"*** Update File: {_T2146_AUTHORITY_PUBLIC_KEY}\n",
            "delete": f"*** Delete File: {_T2146_AUTHORITY_PUBLIC_KEY}\n",
            "move-out": (
                f"*** Update File: {_T2146_AUTHORITY_PUBLIC_KEY}\n"
                "*** Move to: /tmp/t2146-public-key.pem\n"
            ),
            "move-in": (
                "*** Update File: /tmp/t2146-public-key.pem\n"
                f"*** Move to: {future}\n"
            ),
        }
        for label, directives in cases.items():
            command = f"*** Begin Patch\n{directives}*** End Patch\n"
            _t2146_assert_denied(_patch(root, command), label)
    finally:
        shutil.rmtree(root)


def test_t2146_guard_bash_rejects_authority_redirect_spellings():
    root = _mk_fixture_repo()
    target = _T2146_AUTHORITY_FUTURE
    try:
        assert not os.path.lexists(target), \
            "T-2146 未存在 redirect path fixture が既に存在する"
        for label, command in (
            ("gt", f"printf t2146 > {target}"),
            ("append", f"printf t2146 >> {target}"),
            ("fd-and-file", f"printf t2146 >& {target}"),
            ("both", f"printf t2146 &> {target}"),
        ):
            _t2146_assert_denied(
                GB.decide(command, repo_root=root), f"redirect-{label}")
    finally:
        shutil.rmtree(root)


def test_t2146_guard_bash_rejects_authority_tree_ancestor_and_partial_glob():
    root = _mk_fixture_repo()
    authority_parent = os.path.dirname(_T2146_AUTHORITY_ROOT)
    partial_glob = _T2146_AUTHORITY_ROOT[:-1] + "?"
    try:
        for label, command in (
            ("root", f"rm -rf {_T2146_AUTHORITY_ROOT}"),
            ("ancestor", f"rm -rf {authority_parent}"),
            ("partial-glob", f"rm -rf {partial_glob}"),
        ):
            _t2146_assert_denied(
                GB.decide(command, repo_root=root), f"tree-{label}")
    finally:
        shutil.rmtree(root)


def test_t2146_guard_bash_rejects_argument_writers_and_relative_cd_delete():
    root = _mk_fixture_repo()
    target = _T2146_AUTHORITY_FUTURE
    try:
        assert not os.path.lexists(target), \
            "T-2146 未存在 writer path fixture が既に存在する"
        cases = {
            "cp": f"cp /tmp/t2146-source {target}",
            "mv": f"mv /tmp/t2146-source {target}",
            "install": f"install /tmp/t2146-source {target}",
            "tee": f"tee {target}",
            "truncate": f"truncate -s 0 {_T2146_AUTHORITY_PUBLIC_KEY}",
            "relative-cd-rm": (
                f"cd {_T2146_AUTHORITY_ROOT} && "
                "rm acceptance-issuer-public-key.pem"
            ),
        }
        for label, command in cases.items():
            _t2146_assert_denied(
                GB.decide(command, repo_root=root), f"writer-{label}")
    finally:
        shutil.rmtree(root)


def test_t2146_guard_bash_perf_output_keeps_all_protected_trees_denied():
    """perf output parsing must retain every existing tree and authority denial."""
    root = _mk_fixture_repo()
    try:
        protected_targets = {
            "authority": _T2146_AUTHORITY_ROOT,
            "leaf": os.path.join(
                root, "output", "campaigns", "c", "runs", "wal.jsonl"),
            "official-campaign": os.path.join(
                root, "output", "campaigns", "c"),
            "exploration-campaign": os.path.join(
                root, "output", "exploration", "campaigns", "c"),
            "namespace-marker": os.path.join(
                root, "output", "exploration", "namespace.json"),
            "hooks": os.path.join(root, "hooks", "guard_bash.py"),
            "ccbench": os.path.join(root, "external", "ccbench"),
        }
        spellings = (
            lambda target: f"perf stat -o {target} -- true",
            lambda target: f"perf stat --output {target} -- true",
            lambda target: f"perf stat --output={target} -- true",
        )
        for label, target in protected_targets.items():
            for spelling in spellings:
                command = spelling(target)
                _t2146_assert_denied(
                    GB.decide(command, repo_root=root),
                    f"perf-{label}:{command}",
                )
        for spelling in spellings:
            command = spelling("/tmp/t2146-perf-output.txt")
            ok, why = GB.decide(command, repo_root=root)
            assert ok, f"T-2146 unrelated perf output が誤拒否された: {command} ({why})"
    finally:
        shutil.rmtree(root)


def test_t2146_guard_bash_builder_exception_excludes_authority_tree():
    """The build-variants builder exception must not extend into authority."""
    root = _mk_fixture_repo()
    try:
        legacy_build = os.path.join(
            root, "external", "ccbench", "build-variants", "silo-t2146")
        authority_build = os.path.join(
            _T2146_AUTHORITY_ROOT, "build-variants", "silo-t2146")
        ok, why = GB.decide(
            f"cmake --build {legacy_build}", repo_root=root)
        assert ok, f"T-2146 existing build-variants builder が誤拒否された: {why}"
        _t2146_assert_denied(
            GB.decide(f"cmake --build {authority_build}", repo_root=root),
            "builder-authority",
        )
    finally:
        shutil.rmtree(root)


def test_t2146_guard_bash_filesystem_root_ancestor_and_siblings():
    """Filesystem root is protected as an ancestor without catching siblings."""
    root = _mk_fixture_repo()
    try:
        for command in ("rm -rf /", "rm -rf --no-preserve-root /"):
            _t2146_assert_denied(
                GB.decide(command, repo_root=root), f"filesystem-root:{command}")
        allowed = (
            "/tmp",
            _T2146_AUTHORITY_ROOT + "-copy",
            _T2146_AUTHORITY_ROOT + "2",
            "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2146-authority-guard",
            _REPO,
        )
        for target in allowed:
            command = f"rm -rf {target}"
            ok, why = GB.decide(command, repo_root=root)
            assert ok, f"T-2146 non-ancestor が誤拒否された: {command} ({why})"
    finally:
        shutil.rmtree(root)


def test_t2146_authority_hardlink_alias_is_denied_in_both_guards(tmp_path):
    assert os.path.isfile(_T2146_AUTHORITY_PUBLIC_KEY), \
        "T-2146 hardlink fixture の authority public key が実在しない"
    assert GW._HooksInodeIndex(_T2146_AUTHORITY_ROOT).protects(
        _T2146_AUTHORITY_PUBLIC_KEY), \
        "guard_write が実 authority root の inode 集合を構築できない"
    assert GB._HooksInodeIndex(_T2146_AUTHORITY_ROOT).protects(
        _T2146_AUTHORITY_PUBLIC_KEY), \
        "guard_bash が実 authority root の inode 集合を構築できない"
    alias_root = os.fspath(tmp_path)
    same_device_root = None
    alias_parent = alias_root
    main_repo = _git_common_dir(Path(_REPO)).parent
    shared_root = (main_repo.parent / ".izanagi-t2146-hardlink").resolve()
    _validate_shared_root(Path(_REPO), main_repo, shared_root)
    if os.stat(alias_root).st_dev != os.stat(_T2146_AUTHORITY_PUBLIC_KEY).st_dev:
        # pytest tmp が別 device の環境でも、tmp_path 配下の lexical alias を入口にして
        # hardlink entry 自体は repo と main checkout の外、main checkout の親直下の
        # .izanagi-t2146-hardlink に置く。同じ workspace filesystem なので
        # authority と同じ device に留まる。
        shared_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        same_device_root = tempfile.mkdtemp(prefix="t2146-hardlink-", dir=shared_root)
        assert Path(same_device_root).parent == shared_root
        alias_parent = os.path.join(alias_root, "same-device")
        os.symlink(same_device_root, alias_parent)
    alias = os.path.join(alias_parent, "authority-public-key-hardlink")
    physical_alias = (
        os.path.join(same_device_root, "authority-public-key-hardlink")
        if same_device_root is not None else alias)
    authority_root = _T2146_AUTHORITY_ROOT
    authority_file = _T2146_AUTHORITY_PUBLIC_KEY
    synthetic_authority = None
    try:
        os.link(authority_file, physical_alias)
    except OSError as exc:
        if exc.errno not in {errno.EXDEV, errno.EPERM, errno.EACCES}:
            raise
        # Managed sandbox は read-only authority mount と writable worktree mount を
        # 別 mount として見せる。その exact 制約時だけ同じ実装関数へ synthetic root を
        # 与え、inode detector 自体の歯を直接確認する。通常環境では上の実 file を使う。
        if same_device_root is not None:
            os.unlink(alias_parent)
            os.rmdir(same_device_root)
            same_device_root = None
        alias_parent = alias_root
        alias = os.path.join(alias_parent, "authority-public-key-hardlink")
        physical_alias = alias
        fixture_parent = alias_root
        authority_root = os.path.join(fixture_parent, "synthetic-authority")
        synthetic_authority = authority_root
        os.makedirs(authority_root)
        authority_file = os.path.join(authority_root, "public-key.pem")
        with open(authority_file, "w", encoding="utf-8") as stream:
            stream.write("t2146 inode fixture\n")
        os.link(authority_file, physical_alias)
    source_stat = os.stat(authority_file)
    alias_stat = os.stat(alias)
    assert (source_stat.st_dev, source_stat.st_ino) == \
        (alias_stat.st_dev, alias_stat.st_ino), \
        "T-2146 fixture が同一 inode の hardlink alias でない"
    assert not os.path.realpath(alias).startswith(
        os.path.realpath(authority_root) + os.sep), \
        "hardlink test が canonical path 判定でも拒否できる fixture になった"
    try:
        with patch.object(GW, "_AUTHORITY_ROOT", authority_root), \
                patch.object(GB, "_AUTHORITY_ROOT", authority_root):
            _t2146_assert_denied(
                GW.decide("Write", {"file_path": alias}, repo_root=_REPO),
                "guard_write-hardlink",
            )
            _t2146_assert_denied(
                GB.decide(f"printf t2146 > {alias}", repo_root=_REPO),
                "guard_bash-hardlink",
            )
    finally:
        os.unlink(alias)
        if synthetic_authority is not None:
            shutil.rmtree(synthetic_authority)
        if same_device_root is not None:
            os.unlink(alias_parent)
            os.rmdir(same_device_root)


def test_t2146_authority_canonical_symlink_alias_is_denied_in_both_guards(
        tmp_path):
    alias = tmp_path / "authority-alias"
    alias.symlink_to(_T2146_AUTHORITY_ROOT, target_is_directory=True)
    target = alias / "t2146-new.pem"
    assert not target.exists(), "canonical alias の未存在 target 前提が崩れた"
    _t2146_assert_denied(
        GW.decide("Write", {"file_path": os.fspath(target)}, repo_root=_REPO),
        "guard_write-canonical",
    )
    _t2146_assert_denied(
        GB.decide(f"cp /tmp/t2146-source {target}", repo_root=_REPO),
        "guard_bash-canonical",
    )


def test_t2146_authority_lexical_side_rejects_a_future_path_independently(
        tmp_path):
    authority = tmp_path / "synthetic-authority"
    outside = tmp_path / "outside"
    authority.mkdir()
    outside.mkdir()
    (authority / "escape").symlink_to(outside, target_is_directory=True)
    target = authority / "escape" / "future.pem"
    assert not target.exists(), "lexical detector の未存在 target 前提が崩れた"
    assert not os.path.realpath(target).startswith(
        os.path.realpath(authority) + os.sep), \
        "canonical 側から独立した lexical fixture になっていない"

    with patch.object(GW, "_AUTHORITY_ROOT", os.fspath(authority)):
        _t2146_assert_denied(
            GW.decide("Write", {"file_path": os.fspath(target)}, repo_root=_REPO),
            "guard_write-lexical-future",
        )
    with patch.object(GB, "_AUTHORITY_ROOT", os.fspath(authority)):
        _t2146_assert_denied(
            GB.decide(f"cp /tmp/t2146-source {target}", repo_root=_REPO),
            "guard_bash-lexical-future",
        )


def test_t2146_authority_component_boundaries_and_unrelated_paths_remain_allowed():
    root = _mk_fixture_repo()
    siblings = (
        _T2146_AUTHORITY_ROOT + "-copy",
        _T2146_AUTHORITY_ROOT + "2",
        os.path.join(os.path.dirname(_T2146_AUTHORITY_ROOT), "t2146-unrelated"),
    )
    job_path = os.path.join(
        "/work/1/SFC/tanab/dev-wave-jobs",
        "dev-wave-t2146-authority-guard", "safe.txt")
    worktree_path = os.path.join(_REPO, "t2146-safe.txt")
    try:
        for target_root in (*siblings, job_path, worktree_path):
            target = (os.path.join(target_root, "safe.txt")
                      if target_root in siblings else target_root)
            ok, why = GW.decide(
                "Write", {"file_path": target}, repo_root=root)
            assert ok, f"T-2146 unrelated Write が誤拒否された: {target} ({why})"
            ok, why = _patch(root, f"*** Add File: {target}\n+t2146\n")
            assert ok, f"T-2146 unrelated apply_patch が誤拒否された: {target} ({why})"
            for command in (f"printf t2146 > {target}", f"rm -rf {target}"):
                ok, why = GB.decide(command, repo_root=root)
                assert ok, f"T-2146 unrelated Bash が誤拒否された: {command} ({why})"
    finally:
        shutil.rmtree(root)


def test_t2146_authority_reads_remain_allowed():
    root = _mk_fixture_repo()
    try:
        for command in (
            f"cat {_T2146_AUTHORITY_PUBLIC_KEY}",
            f"grep -n BEGIN {_T2146_AUTHORITY_PUBLIC_KEY}",
            f"sha256sum {_T2146_AUTHORITY_PUBLIC_KEY}",
            f"stat {_T2146_AUTHORITY_PUBLIC_KEY}",
        ):
            ok, why = GB.decide(command, repo_root=root)
            assert ok, f"T-2146 authority read が誤拒否された: {command} ({why})"
    finally:
        shutil.rmtree(root)


def test_t2146_authority_symlink_entry_unlink_and_move_remain_allowed(tmp_path):
    alias = tmp_path / "authority-unlink-alias"
    alias.symlink_to(_T2146_AUTHORITY_ROOT, target_is_directory=True)
    destination = tmp_path / "moved-alias"
    for directives in (
        f"*** Delete File: {alias}\n",
        f"*** Update File: {alias}\n*** Move to: {destination}\n",
    ):
        ok, why = _patch(_REPO, directives, cwd=_REPO)
        assert ok, f"T-2146 authority symlink entry 操作が誤拒否された: {why}"
    for command in (f"rm {alias}", f"mv {alias} {destination}"):
        ok, why = GB.decide(command, repo_root=_REPO)
        assert ok, f"T-2146 authority symlink entry が誤拒否された: {command} ({why})"


def test_t2146_both_guard_mains_fail_closed_on_authority_internal_errors():
    write_payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": _T2146_AUTHORITY_PUBLIC_KEY},
    })
    bash_payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": f"cat {_T2146_AUTHORITY_PUBLIC_KEY}"},
    })
    with patch.object(GW, "decide", side_effect=RuntimeError("t2146 rule bug")):
        assert _guard_main(GW, write_payload) == 2
    with patch.object(GB, "decide", side_effect=RuntimeError("t2146 rule bug")):
        assert _guard_main(GB, bash_payload) == 2


def test_t2146_both_guard_error_fallbacks_allow_authority_siblings():
    """Fallback matching stays component-exact for -copy and numeric siblings."""
    for sibling in (
        _T2146_AUTHORITY_ROOT + "-copy",
        _T2146_AUTHORITY_ROOT + "2",
    ):
        write_payload = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": os.path.join(sibling, "key.pem")},
        })
        bash_payload = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": f"printf t2146 > {sibling}/key.pem"},
        })
        with patch.object(
                GW, "decide", side_effect=RuntimeError("t2146 rule bug")):
            assert _guard_main(GW, write_payload) == 0
        with patch.object(
                GB, "decide", side_effect=RuntimeError("t2146 rule bug")):
            assert _guard_main(GB, bash_payload) == 0


def test_t2146_authority_guards_run_as_subprocess_smoke():
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cases = (
        ("guard_write", {
            "tool_name": "Write",
            "tool_input": {"file_path": _T2146_AUTHORITY_PUBLIC_KEY},
        }, 2),
        ("guard_write", {
            "tool_name": "apply_patch", "cwd": _REPO,
            "tool_input": {"command":
                f"*** Add File: {_T2146_AUTHORITY_FUTURE}\n"},
        }, 2),
        ("guard_bash", {
            "tool_name": "Bash",
            "tool_input": {"command":
                f"printf t2146 > {_T2146_AUTHORITY_FUTURE}"},
        }, 2),
        ("guard_bash", {
            "tool_name": "Bash",
            "tool_input": {"command": f"cat {_T2146_AUTHORITY_PUBLIC_KEY}"},
        }, 0),
    )
    for name, payload, expected in cases:
        result = subprocess.run(
            [sys.executable, os.path.join(_REPO, "hooks", f"{name}.py")],
            input=json.dumps(payload), capture_output=True, text=True, env=env,
        )
        assert result.returncode == expected, \
            (f"T-2146 {name} subprocess rc={result.returncode} "
             f"(期待 {expected}) stderr={result.stderr[:200]}")


# ---------- guard_write: designated ソースは内容非検査 (方針 A, D30/D33) ----------
# 旧 EVOLVE-BLOCK 領域検査 (payload/skeleton のテキスト検査) は方針 A で hook から
# 削除された。#ifdef TRACE 混入・生指令・#include 追加・偽 cache hit の担保は、
# テキスト検査の完全性 (GW2R-1 の backslash-newline splice が原理的限界を実証) ではなく
# 一次防壁 = source_digest に委譲された。その一次防壁の網羅は test_campaign.py が固定する:
#   - #include 追加/差し替え       → test_source_digest_* の assert_includes_match_head 系
#   - #if TRACE の挙動差混入 (GW2R-1) → test_trace_diff_of_diffs_allows_stock_hook_catches_inner_edit
#   - TRACE 条件付きコードの追加     → test_trace_diff_of_diffs_predicate
#   - resolve→build 間の TOCTOU 汚染 → test_buildcache_recheck_detects_toctou
# hook 側 (下記) が担うのは「designated ソースかどうか」の面 (surface) 判定のみ。

def test_designated_source_edits_allowed_content_not_inspected():
    """方針 A: designated ソース (EVOLVE_BLOCK_SOURCES) 内の Edit/Write は内容を検査せず許可。

    旧設計 (方針 B) で payload 外・骨格・マーカー削除・生指令・TRACE 混入・markerless として
    拒否していたケースは、いずれも hook では止めない (identity の正直さと観測者効果は
    source_digest の一次防壁が build/resolve 出口で捕える。上のコメント参照)。hook が
    これらを再び拒否し始めたら、方針 A で放棄した単一障害点 (payload テキスト検査) の
    復活 = 回帰なので固定する。"""
    root = _mk_fixture_repo()
    hh = "external/ccbench/include/backoff.hh"
    try:
        # payload のみ (旧 test_payload_edit_allowed)
        ok, why = _edit(root, hh, _PAYLOAD_OLD, "    double now_backoff = 10.0;\n")
        assert ok, f"payload の変更は許可されるべき: {why}"
        new_full = _SKELETON.replace(_PAYLOAD_OLD, "    double now_backoff = 5.0;\n")
        ok, why = GW.decide("Write", {"file_path": os.path.join(root, hh),
                                      "content": new_full}, repo_root=root)
        assert ok, f"payload 差し替えの Write は許可されるべき: {why}"
        # 旧 method で拒否していた内容も、方針 A では hook を通す (一次防壁に委譲)。
        for old, new in [
            # 領域外 (spin loop) — 意味的逸脱は auditor/人間レビュー領域
            ("while (stop - start < clocks_per_us * now_backoff) stop = rdtscp();",
             "for (;;) {}"),
            # stock 枝 (#else)
            ("Backoff_.load(std::memory_order_acquire)", "0.0"),
            # 骨格 #if 行 — 変えれば preprocess が動き src_token が変わる (偽 hit しない)
            ("#if BACKOFF_FIXED >= 0", "#if BACKOFF_FIXED >= 1"),
            # 生指令・予約識別子・TRACE — diff-of-diffs / preprocess ハッシュが build 出口で捕える
            (_PAYLOAD_OLD, "#include <ctime>\n    double now_backoff = __DATE__[0];\n"),
            (_PAYLOAD_OLD, "    double now_backoff = 1.0; // TRACE\n#define TRACE 1\n"),
        ]:
            ok, why = _edit(root, hh, old, new)
            assert ok, f"designated ソース内は hook を通すべき (方針 A): {old[:40]!r} ({why})"
        # markerless (template 未適用) でも designated ソースなら hook は通す
        with open(os.path.join(root, hh), "w", encoding="utf-8") as f:
            f.write("class Backoff { /* stock */ };\n")
        ok, why = _edit(root, hh, "stock", "hacked")
        assert ok, f"markerless の designated ソースも hook は通す (方針 A): {why}"
    finally:
        shutil.rmtree(root)


def test_constants_match_source_digest():
    assert tuple(GW.EVOLVE_BLOCK_SOURCES) == tuple(source_digest.EVOLVE_BLOCK_SOURCES), \
        "hook と source_digest の EVOLVE_BLOCK_SOURCES がドリフト"


def test_real_submodule_payload_edit():
    """実 submodule にマーカー適用済みなら、実ファイルで payload 編集が通ることを確認。"""
    hh = os.path.join(_REPO, "external", "ccbench", "include", "backoff.hh")
    if not os.path.exists(hh):
        skip("submodule 未 init")
    with open(hh, encoding="utf-8") as f:
        text = f.read()
    if "EVOLVE-BLOCK-BEGIN" not in text:
        skip_conditional_unrun("template patch 未適用: backoff.hh に EVOLVE-BLOCK marker 無し")
    ok, why = GW.decide("Edit", {
        "file_path": hh,
        "old_string": "    double now_backoff = static_cast<double>(BACKOFF_FIXED);",
        "new_string": "    double now_backoff = 7.0;"})
    assert ok, f"実 template の payload 編集が拒否された: {why}"


# ---------- guard_bash ----------

_WAL = "output/campaigns/c/runs/wal.jsonl"
_LOCK = "output/campaigns/c/campaign.lock"
_BV = "external/ccbench/build-variants"
_EXPLORATION_CAMPAIGN = "output/exploration/campaigns/c"
_EXPLORATION_WAL = f"{_EXPLORATION_CAMPAIGN}/runs/wal.jsonl"
_EXPLORATION_MARKER = "output/exploration/namespace.json"


# [T-1025] cases-t1025.tsv の 93 行を repo 内へ固定する。外部の job artifact は
# テスト実行時には参照しない。
_T1025_DENY_CASES = (
    ("awk-gt-wal", f"awk 'BEGIN {{ print \"x\" > \"{_WAL}\" }}' /dev/null"),
    ("awk-append-wal", f"awk 'BEGIN {{ print \"x\" >> \"{_WAL}\" }}' /dev/null"),
    ("awk-printf-wal", f"awk 'BEGIN {{ printf \"x\" > \"{_WAL}\" }}' /dev/null"),
    ("gawk-gt-hook", "gawk 'BEGIN { print \"x\" > \"hooks/guard_write.py\" }' /dev/null"),
    ("mawk-gt-lock", f"mawk 'BEGIN {{ print \"x\" > \"{_LOCK}\" }}' /dev/null"),
    ("awk-gt-explwal", f"awk 'BEGIN {{ print \"x\" > \"{_EXPLORATION_WAL}\" }}' /dev/null"),
    ("awk-gt-marker", f"awk 'BEGIN {{ print \"x\" > \"{_EXPLORATION_MARKER}\" }}' /dev/null"),
    ("awk-pipe-wal", f"awk 'BEGIN {{ print \"x\" | \"cat > {_WAL}\" }}' /dev/null"),
    ("awk-system-wal", f"awk 'BEGIN {{ system(\"rm {_WAL}\") }}' /dev/null"),
    ("awk-progfile-wal", f"awk -f /tmp/prog.awk {_WAL}"),
    ("gawk-profile-hook", "gawk --profile=hooks/guard_write.py '{print}' /dev/null"),
    ("gawk-load-wal", f"gawk -l /tmp/evil.so '{{print}}' {_WAL}"),
    ("sed-w-wal", f"sed -n 'w {_WAL}' /etc/hostname"),
    ("sed-sw-wal", f"sed -n 's/a/b/w {_WAL}' /etc/hostname"),
    ("sed-w-hook", "sed -n 'w hooks/guard_write.py' /etc/hostname"),
    ("sed-e-wal", f"sed -n 'e cat {_WAL}' /etc/hostname"),
    ("sed-scriptfile-wal", f"sed -n -f /tmp/prog.sed {_WAL}"),
    ("git-diff-output-eq", f"git diff --output={_WAL}"),
    ("git-diff-output-sep", f"git diff --output {_WAL}"),
    ("git-log-output", f"git log --output={_WAL}"),
    ("git-show-output", f"git show --output={_WAL}"),
    ("git-diff-output-hook", "git diff --output=hooks/guard_write.py"),
    ("git-grep-O", f"git grep -O{_WAL} COMMIT"),
    ("git-diff-extdiff", f"git diff --ext-diff -- {_WAL}"),
    ("git-diff-textconv", f"git diff --textconv -- {_WAL}"),
    ("git-c-pager", f"git -c core.pager=tee log -- {_WAL}"),
    ("git-paginate", f"git --paginate log -- {_WAL}"),
    ("git-catfile-filters", f"git cat-file --filters HEAD:{_WAL}"),
    ("sort-T-wal", f"sort -T {_WAL} /etc/hostname"),
    ("sort-T-attached", f"sort -T{_WAL} /etc/hostname"),
    ("sort-tempdir-long", f"sort --temporary-directory={_WAL} /etc/hostname"),
    ("sort-compress-prog", f"sort --compress-program=/tmp/w {_WAL}"),
    ("find-fls-wal", f"find . -maxdepth 1 -fls {_WAL}"),
    ("find-fls-hook", "find . -maxdepth 1 -fls hooks/guard_write.py"),
    ("xxd-r-out", f"xxd -r /etc/hostname {_WAL}"),
    ("xxd-out", f"xxd /etc/hostname {_WAL}"),
    ("xxd-out-hook", "xxd /etc/hostname hooks/guard_write.py"),
    ("file-compile", f"file -C -m {_WAL}"),
    ("nm-plugin", f"nm --plugin=/tmp/evil.so {_BV}/silo_x/ycsb_silo.exe"),
    ("rg-pre", f"rg --pre=/tmp/writer COMMIT {_WAL}"),
    ("less-o-attached", f"less -o{_WAL} /etc/hostname"),
    ("less-logfile-long", f"less --log-file={_WAL} /etc/hostname"),
    ("zless-o", f"zless -o{_WAL} /etc/hostname"),
    ("dd-of-hook", "dd if=/etc/hostname of=hooks/guard_write.py"),
    ("yq-inplace", f"yq -i '.a=1' {_WAL}"),
    ("ag-pager", f"ag --pager=tee COMMIT {_WAL}"),
    ("most-wal", f"most {_WAL}"),
    ("dd-of-wal", f"dd if=/etc/hostname of={_WAL}"),
    ("sed-i-wal", f"sed -i s/a/b/ {_WAL}"),
    ("awk-i-inplace", f"awk -i inplace '{{print}}' {_WAL}"),
    ("perl-i-wal", f"perl -i -pe s/a/b/ {_WAL}"),
    ("echo-append-wal", f"echo x >> {_WAL}"),
    ("rm-wal", f"rm -f {_WAL}"),
    ("sort-o-wal", f"sort -o {_WAL} {_WAL}"),
    ("find-delete", "find output/campaigns/c/runs -name '*.jsonl' -delete"),
    ("find-fprintf", f"find . -maxdepth 1 -fprintf {_WAL} %p"),
    ("rm-hook", "rm -f hooks/guard_write.py"),
    ("tee-hook", "tee hooks/guard_write.py"),
)

_T1025_ALLOW_CASES = (
    ("awk-plain-hook", "awk '{print}' hooks/guard_write.py"),
    ("awk-field-wal", f"awk '{{print $1}}' {_WAL}"),
    ("awk-count-wal", f"awk '/COMMIT/ {{ n++ }} END {{ print n }}' {_WAL}"),
    ("sed-n-1p", f"sed -n 1p {_WAL}"),
    ("sed-n-range", f"sed -n '1,200p' {_WAL}"),
    ("sed-n-warn", f"sed -n '/warn/p' {_WAL}"),
    ("sed-n-sp", f"sed -n 's/x/y/p' {_WAL}"),
    ("git-diff-path", "git diff -- hooks/guard_write.py"),
    ("git-log-oneline", f"git log --oneline -- {_WAL}"),
    ("git-lstree", f"git ls-tree HEAD {_WAL}"),
    ("git-blame-contents", f"git blame --contents {_WAL} HEAD"),
    ("git-add-wal", f"git add {_WAL}"),
    ("git-commit-msg", f"git commit -m 'campaign: {_WAL} を追加'"),
    ("sort-plain-hook", "sort hooks/guard_write.py"),
    ("sort-u-wal", f"sort -u {_WAL}"),
    ("find-name", "find output/campaigns -name '*.jsonl'"),
    ("find-type-f", "find hooks -type f -print"),
    ("xxd-plain", f"xxd {_WAL}"),
    ("xxd-len", f"xxd -l 16 {_WAL}"),
    ("dd-if-wal", f"dd if={_WAL} of=/tmp/copy"),
    ("nm-C", f"nm -C {_BV}/silo_x/ycsb_silo.exe"),
    ("file-plain", f"file {_WAL}"),
    ("rg-plain", f"rg COMMIT {_WAL}"),
    ("less-plain", f"less {_WAL}"),
    ("cat-wal", f"cat {_WAL}"),
    ("grep-wal", f"grep -c COMMIT {_WAL}"),
    ("jq-wal", f"jq .fitness {_WAL}"),
    ("head-wal", f"head -5 {_WAL}"),
    ("wc-wal", f"wc -l {_WAL}"),
    ("python-script", f"python3 orchestrator/campaign/p2_2_report.py {_WAL}"),
    ("od-second-positional", f"od -c /etc/hostname {_WAL}"),
    ("stat-printf", f"stat --printf=x {_WAL}"),
    ("date-f", f"date -f {_WAL}"),
    ("ls-bv", f"ls {_BV}"),
    ("reports-write", "echo '# report' > output/campaigns/c/reports/r.md"),
)


@pytest.mark.parametrize(
    ("label", "command"),
    _T1025_DENY_CASES,
    ids=[label for label, _ in _T1025_DENY_CASES],
)
def test_t1025_expectation_table_denies(label, command):
    ok, why = GB.decide(command)
    assert not ok, f"T-1025 deny が通った [{label}]: {command!r} ({why})"


@pytest.mark.parametrize(
    ("label", "command"),
    _T1025_ALLOW_CASES,
    ids=[label for label, _ in _T1025_ALLOW_CASES],
)
def test_t1025_expectation_table_allows(label, command):
    ok, why = GB.decide(command)
    assert ok, f"T-1025 allow が誤拒否された [{label}]: {command!r} ({why})"


_T1025_PROTECTED_TARGETS = (
    ("wal", _WAL),
    ("lock", _LOCK),
    ("build-variants", f"{_BV}/silo_x/meta.json"),
    ("exploration-marker", _EXPLORATION_MARKER),
    ("exploration-wal", _EXPLORATION_WAL),
    ("hook", "hooks/guard_write.py"),
)


@pytest.mark.parametrize(
    ("label", "target"),
    _T1025_PROTECTED_TARGETS,
    ids=[label for label, _ in _T1025_PROTECTED_TARGETS],
)
def test_t1025_sed_writer_denied_across_protected_targets(label, target):
    command = f"sed -n 'w {target}' /etc/hostname"
    ok, why = GB.decide(command)
    assert not ok, f"保護対象への sed writer が通った [{label}]: {command!r} ({why})"


# ccbench source は末端層が保護しない範囲で、`echo >` を含む全 writer が同様に通る
# 既存の境界。[T-1025] の scope 外なので、deny 直積ではなく残余限界を allow で固定する。
def test_t1025_ccbench_source_writer_remains_out_of_scope():
    command = "sed -n 'w external/ccbench/include/backoff.hh' /etc/hostname"
    ok, why = GB.decide(command)
    assert ok, f"T-1025 scope 外の ccbench source writer が拒否された: {command!r} ({why})"


_T1025_ADDITIONAL_DENY_CASES = (
    ("awk-pipe-both", f"awk 'BEGIN {{ print \"x\" |& \"cat > {_WAL}\" }}' /dev/null"),
    ("awk-close", f"awk 'BEGIN {{ close(\"{_WAL}\") }}' {_WAL}"),
    ("awk-file-long", f"awk --file /tmp/prog.awk {_WAL}"),
    ("awk-file-long-eq", f"awk --file=/tmp/prog.awk {_WAL}"),
    ("gawk-o-attached", f"gawk -o{_WAL} '{{print}}' /dev/null"),
    ("gawk-pretty-eq", f"gawk --pretty-print={_WAL} '{{print}}' /dev/null"),
    ("gawk-p-attached", f"gawk -p{_WAL} '{{print}}' /dev/null"),
    ("gawk-debug-attached", f"gawk -D{_WAL} '{{print}}' /dev/null"),
    ("gawk-debug-long", f"gawk --debug={_WAL} '{{print}}' /dev/null"),
    ("gawk-dump-vars", f"gawk --dump-variables={_WAL} '{{print}}' /dev/null"),
    ("gawk-gen-pot", f"gawk --gen-pot={_WAL} '{{print}}' /dev/null"),
    ("gawk-load-long", f"gawk --load=/tmp/evil.so '{{print}}' {_WAL}"),
    ("sed-W", f"sed -n 'W {_WAL}' /etc/hostname"),
    ("sed-sub-e", f"sed -n 's/a/b/e' {_WAL}"),
    ("sed-ambiguous-script", f"sed -n 's/a/b' {_WAL}"),
    ("sed-file-long", f"sed -n --file /tmp/prog.sed {_WAL}"),
    ("sed-file-long-eq", f"sed -n --file=/tmp/prog.sed {_WAL}"),
    ("sort-tempdir-sep", f"sort --temporary-directory {_WAL} /etc/hostname"),
    ("sort-compress-sep", f"sort --compress-program /tmp/w {_WAL}"),
    ("git-c-attached", f"git -ccore.pager=tee log -- {_WAL}"),
    ("git-config-env-sep", f"git --config-env core.pager=PAGER log -- {_WAL}"),
    ("git-config-env-eq", f"git --config-env=core.pager=PAGER log -- {_WAL}"),
    ("git-p-short", f"git -p log -- {_WAL}"),
    ("git-diff-out-abbrev", f"git diff --out={_WAL}"),
    ("git-whatchanged-output", f"git whatchanged --output={_WAL}"),
    ("git-log-ext-diff", f"git log --ext-diff -- {_WAL}"),
    ("git-show-textconv", f"git show --textconv -- {_WAL}"),
    ("git-grep-O-sep", f"git grep -O {_WAL} COMMIT"),
    ("git-grep-pager-long", f"git grep --open-files-in-pager={_WAL} COMMIT"),
    ("git-grep-textconv", f"git grep --textconv COMMIT {_WAL}"),
    ("git-catfile-textconv", f"git cat-file --textconv HEAD:{_WAL}"),
    ("file-compile-long", f"file --compile -m {_WAL}"),
    ("nm-plugin-sep", f"nm --plugin /tmp/evil.so {_BV}/silo_x/ycsb_silo.exe"),
    ("rg-pre-sep", f"rg --pre /tmp/writer COMMIT {_WAL}"),
    ("rg-hostname-bin", f"rg --hostname-bin=/tmp/writer COMMIT {_WAL}"),
    ("rg-hostname-bin-sep", f"rg --hostname-bin /tmp/writer COMMIT {_WAL}"),
    ("less-o-sep", f"less -o {_WAL} /etc/hostname"),
    ("less-O-attached", f"less -O{_WAL} /etc/hostname"),
    ("less-logfile-sep", f"less --log-file {_WAL} /etc/hostname"),
    ("less-LOG-FILE", f"less --LOG-FILE={_WAL} /etc/hostname"),
    ("zless-O-sep", f"zless -O {_WAL} /etc/hostname"),
    ("xxd-ambiguous-option", f"xxd -Z {_WAL}"),
)


@pytest.mark.parametrize(
    ("label", "command"),
    _T1025_ADDITIONAL_DENY_CASES,
    ids=[label for label, _ in _T1025_ADDITIONAL_DENY_CASES],
)
def test_t1025_spec_writer_spellings_denied(label, command):
    ok, why = GB.decide(command)
    assert not ok, f"T-1025 の writer 綴りが通った [{label}]: {command!r} ({why})"


_T1025_ADDITIONAL_ALLOW_CASES = (
    ("git-status-short", "git status --short"),
    ("ldd-build-variant", f"ldd {_BV}/silo_x/ycsb_silo.exe"),
    # v3 A5: 比較演算は redirection ではない。
    ("awk-comparison", f"awk '$1 > 5 {{print}}' {_WAL}"),
    # gawk の任意引数長 option は `=` でしか値を取らない。`=` 形は deny 側で固定する。
    ("gawk-pretty-sep", f"gawk --pretty-print {_WAL} '{{print}}' /dev/null"),
)


@pytest.mark.parametrize(
    ("label", "command"),
    _T1025_ADDITIONAL_ALLOW_CASES,
    ids=[label for label, _ in _T1025_ADDITIONAL_ALLOW_CASES],
)
def test_t1025_spec_readers_remain_allowed(label, command):
    ok, why = GB.decide(command)
    assert ok, f"T-1025 の reader が誤拒否された [{label}]: {command!r} ({why})"


# [T-1025] cases-t1025-v2.tsv の追加 42 行も外部 artifact に依存せず固定する。
_T1025_V2_DENY_CASES = (
    ("sed-i-after-script", f"sed 'p' -i {_WAL}"),
    ("sed-inplace-long-eq", f"sed 'p' --in-place={_WAL}"),
    ("sort-cluster-uo", f"sort -uo{_WAL} /etc/hostname"),
    ("sort-cluster-uT", f"sort -uT {_WAL} /etc/hostname"),
    ("file-cluster-Cm", f"file -Cm {_WAL}"),
    ("less-cluster-NO", f"less -NO{_WAL} /etc/hostname"),
    ("sort-abbrev-ou", f"sort --ou={_WAL} /etc/hostname"),
    ("sort-abbrev-te", f"sort --te={_WAL} /etc/hostname"),
    ("sort-abbrev-co", f"sort --co=/tmp/writer {_WAL}"),
    ("git-diff-abbrev-ou", f"git diff --ou={_WAL}"),
    ("git-grep-abbrev-ope", f"git grep --ope=/tmp/pager COMMIT {_WAL}"),
    ("git-catfile-abbrev-fi", f"git cat-file --fi HEAD:{_WAL}"),
    ("file-abbrev-com", f"file --com -m {_WAL}"),
    ("nm-abbrev-plu", f"nm --plu=/tmp/evil.so {_BV}/silo_x/ycsb_silo.exe"),
    ("awk-redirect-nonliteral", f"awk 'BEGIN {{ print \"x\" > outvar }}' {_WAL}"),
    ("rg-pre-tmp", f"rg --pre=/tmp/writer COMMIT {_WAL}"),
    ("nm-plugin-tmp", f"nm --plugin=/tmp/evil.so {_BV}/silo_x/ycsb_silo.exe"),
    ("git-textconv-tmp", f"git diff --textconv -- {_WAL}"),
    ("git-extdiff-tmp", f"git diff --ext-diff -- {_WAL}"),
    ("awk-system-tmp", f"awk 'BEGIN {{ system(\"echo x\") }}' {_WAL}"),
)

_T1025_V2_ALLOW_CASES = (
    ("git-diff-cached-patch", "git diff --cached --output=/tmp/guard.patch -- hooks/guard_bash.py"),
    ("sed-w-to-tmp", f"sed -n 'w /tmp/copy' {_WAL}"),
    ("sort-T-tmp", f"sort -T /tmp {_WAL}"),
    ("find-fls-tmp", "find output/campaigns/c/runs -fls /tmp/list"),
    ("xxd-out-tmp", f"xxd {_WAL} /tmp/copy"),
    ("less-o-tmp", f"less -o/tmp/log {_WAL}"),
    ("gawk-profile-tmp", f"gawk --profile=/tmp/prof '{{print}}' {_WAL}"),
    ("file-compile-tmp", f"file -C -m /tmp/magic {_WAL}"),
    ("dd-of-tmp2", f"dd if={_WAL} of=/tmp/copy2"),
    ("sed-bundled-ne", f"sed -ne '1p' {_WAL}"),
    ("sed-relative-range", f"sed -n '1,+2p' {_WAL}"),
    ("xxd-long-seek", f"xxd -seek 0 {_WAL}"),
    ("xxd-long-cols", f"xxd -cols 16 {_WAL}"),
    ("awk-regex-alternation", f"awk '/COMMIT|ABORT/ {{ print }}' {_WAL}"),
    ("awk-string-pipe", f"awk '{{ if ($1 == \"a|b\") print }}' {_WAL}"),
    ("awk-comparison", f"awk '$1 > 5 {{ print }}' {_WAL}"),
    ("awk-redirect-tmp-literal", f"awk 'BEGIN {{ print \"x\" > \"/tmp/out\" }}' {_WAL}"),
    ("git-diff-ddash-pathspec", f"git diff -- --output={_WAL}"),
    ("sort-ddash", f"sort -- --temporary-directory {_WAL}"),
    ("file-ddash", f"file -- -C {_WAL}"),
    ("less-ddash", f"less -- -o {_WAL}"),
    ("rg-ddash", f"rg -- --pre {_WAL}"),
)


@pytest.mark.parametrize(
    ("label", "command"),
    _T1025_V2_DENY_CASES,
    ids=[label for label, _ in _T1025_V2_DENY_CASES],
)
def test_t1025_v2_expectation_table_denies(label, command):
    ok, why = GB.decide(command)
    assert not ok, f"T-1025 v2 deny が通った [{label}]: {command!r} ({why})"


@pytest.mark.parametrize(
    ("label", "command"),
    _T1025_V2_ALLOW_CASES,
    ids=[label for label, _ in _T1025_V2_ALLOW_CASES],
)
def test_t1025_v2_expectation_table_allows(label, command):
    ok, why = GB.decide(command)
    assert ok, f"T-1025 v2 allow が誤拒否された [{label}]: {command!r} ({why})"


def test_bash_fast_path_and_reads_allowed():
    for cmd in ("ls -la",
                "echo hi > /tmp/x",
                f"cat {_WAL}",
                f"grep -c COMMIT {_WAL} | head",
                f"jq .fitness {_WAL} > /tmp/f",
                f"sed -n 1p {_WAL}",
                f"tail -5 {_WAL}",
                f"dd if={_WAL} of=/tmp/copy",
                f"git log --oneline -- {_WAL}",
                f"git add {_WAL}",
                f"git commit -m 'campaign: {_WAL} を追加'",      # FP-heredoc の非 heredoc 版
                f'grep -rn "build-variants\\|BUILD" f | head',  # FP-quote-split
                f"grep -cE 'COMMIT|ABORT' {_WAL}",              # FP-quote-split
                f"python3 orchestrator/campaign/p2_2_report.py {_WAL}",
                f"ls {_BV}",
                f"find output/campaigns -name '*.jsonl'",       # find 読み取り (delete 無し)
                f"cat {_WAL} | grep COMMIT | wc -l",
                "ls output/campaigns/c/reports/"):              # 祖先だが read
        ok, why = GB.decide(cmd)
        assert ok, f"読み取り/管轄外コマンドが誤って拒否された: {cmd!r} ({why})"


def test_bash_reports_write_allowed():
    """祖先 (campaign dir) 配下でも reports/insights への書き込みは通る (破壊系でない)。"""
    for cmd in ("echo '# report' > output/campaigns/c/reports/r.md",
                "cp /tmp/plot.png output/campaigns/c/reports/",
                "python3 gen_report.py output/campaigns/c/reports/"):
        ok, why = GB.decide(cmd)
        assert ok, f"reports/ への正当書き込みが拒否された: {cmd!r} ({why})"


def test_bash_exploration_campaign_tree_destruction_denied():
    """M13: leaf 名に依存せず exploration campaign tree の破壊を拒否する。"""
    for cmd in (
        f"rm -rf {_EXPLORATION_CAMPAIGN}",
        f"mv {_EXPLORATION_CAMPAIGN} /tmp/",
        f"truncate -s 0 {_EXPLORATION_CAMPAIGN}",
        f"tee {_EXPLORATION_CAMPAIGN}",
        f"echo x > {_EXPLORATION_CAMPAIGN}",
    ):
        ok, _ = GB.decide(cmd)
        assert not ok, f"exploration campaign tree の破壊が通った: {cmd!r}"


def test_bash_exploration_reads_and_projection_writes_allowed():
    """exploration の非 proof-chain projection の過剰拒否を検出する。"""
    for cmd in (
        f"echo report > {_EXPLORATION_CAMPAIGN}/reports/report.md",
        f"cp /tmp/insight.json {_EXPLORATION_CAMPAIGN}/insights/",
    ):
        ok, why = GB.decide(cmd)
        assert ok, f"exploration の read/projection Write が誤拒否された: {cmd!r} ({why})"


def test_bash_exploration_wal_reads_allowed():
    """M16: `_is_read_only` で exploration WAL read だけ拒否する変異を kill。"""
    for cmd in (
        f"cat {_EXPLORATION_WAL}",
        f"grep -c COMMIT {_EXPLORATION_WAL}",
        f"jq .fitness {_EXPLORATION_WAL}",
    ):
        ok, why = GB.decide(cmd)
        assert ok, f"exploration WAL read が誤拒否された: {cmd!r} ({why})"


def test_bash_exploration_namespace_marker_protected_but_readable():
    """M14-B: marker 判定関数の無効化を delete/move/write で kill。"""
    trial_marker = "output/exploration/autonomous-trials/t1/namespace.json"
    for cmd in (
        f"echo '{{}}' > {_EXPLORATION_MARKER}",
        f"tee {_EXPLORATION_MARKER}",
        f"truncate -s 0 {_EXPLORATION_MARKER}",
        f"rm {_EXPLORATION_MARKER}",
        f"mv {_EXPLORATION_MARKER} /tmp/namespace.json",
        f"mv /tmp/namespace.json {_EXPLORATION_MARKER}",
        f"rm {trial_marker}",
        "rm output/exploration/namespace.*",
        "rm output/exploration/name*.json",
        "rm output/exploration/{namespace,other}.json",
        "cd output/exploration && rm namespace.json",
    ):
        ok, _ = GB.decide(cmd)
        assert not ok, f"exploration namespace marker の破壊が通った: {cmd!r}"
    for cmd in (
        f"cat {_EXPLORATION_MARKER}",
        f"grep exploration {_EXPLORATION_MARKER}",
        f"jq .namespace {_EXPLORATION_MARKER}",
        f"cat {trial_marker}",
        "rm output/exploration/namespace.json?",
        "rm /tmp/custom/exploration/namespace.json",
    ):
        ok, why = GB.decide(cmd)
        assert ok, f"exploration namespace marker の read が誤拒否された: {cmd!r} ({why})"


def test_bash_official_campaign_root_direct_writers_keep_legacy_acceptance():
    """F2: exploration だけの追加拒否で official の旧正例を縮小しない。"""
    for cmd in (
        "echo x > output/campaigns/c",
        "tee output/campaigns/c",
        "truncate -s 0 output/campaigns/c",
    ):
        ok, why = GB.decide(cmd)
        assert ok, f"official campaign root の旧正例が誤拒否された: {cmd!r} ({why})"


def test_bash_exploration_autonomous_trial_journal_write_allowed():
    """journal は proof chain ではないため exploration campaign tree 防護へ含めない。"""
    journal = "output/exploration/autonomous-trials/t1/attempts.jsonl"
    for cmd in (
        f"echo '{{}}' >> {journal}",
        f"tee -a {journal}",
        "mv output/exploration/autonomous-trials/t1/attempt.tmp " + journal,
    ):
        ok, why = GB.decide(cmd)
        assert ok, f"autonomous trial journal の Write が誤拒否された: {cmd!r} ({why})"


def test_bash_direct_writes_denied():
    for cmd in (f"echo '{{}}' >> {_WAL}",
                f"echo x > {_BV}/silo_x/meta.json",
                f"echo y > {_LOCK}",
                f"cp /tmp/x {_WAL}",
                f"mv {_WAL} /tmp/",
                f"rm -rf {_BV}",
                f"sed -i s/a/b/ {_WAL}",
                f"cat x | tee -a {_WAL}",
                f"truncate -s 0 {_WAL}",
                f"dd if=/dev/zero of={_WAL}",
                f"ln -sf /tmp/evil {_WAL}",
                f"git checkout -- {_WAL}",
                f"timeout 5 rm {_WAL}"):
        ok, _ = GB.decide(cmd)
        assert not ok, f"防護対象への書き込みが通った: {cmd!r}"


def test_bash_opaque_with_protected_fails_closed():
    for cmd in (f"echo $(hostname) >> {_WAL}",
                f"grep -l x output/campaigns/c/runs/a.log | xargs rm",
                f"python3 -c \"open('{_WAL}','a').write('x')\"",
                f"bash -c 'echo x > {_WAL}'",
                f"cat <(echo x) > {_WAL}",
                f"echo hi >> '{_WAL}"):   # 引用符不整合
        ok, _ = GB.decide(cmd)
        assert not ok, f"不透明構文 + 防護対象が通った: {cmd!r}"


def test_bash_finding_bypasses_all_denied():
    """敵対検証 2026-07-02 の確定 bypass finding を回帰固定する。"""
    cases = {
        # F-BASH-1: サブシェル / グループ / 制御構文で head を隠す
        "F-BASH-1 subshell": f"( cp /tmp/evil {_WAL} )",
        "F-BASH-1 group": f"{{ cp /tmp/evil {_WAL} ; }}",
        "F-BASH-1 if": f"if true; then cp /tmp/evil {_WAL}; fi",
        "F-BASH-1 for": f"for f in a; do cp x {_WAL}; done",
        "F-BASH-1 subshell rm": f"( rm -rf {_BV} )",
        "F-BASH-1 subshell sed": f"( sed -i s/C/A/ {_WAL} )",
        "F-BASH-1 subshell git": f"( git checkout -- {_WAL} )",
        "F-BASH-1 subshell tee": f"( tee {_WAL} )",
        # F-BASH-2: sed 長形式 in-place
        "F-BASH-2 sed --in-place=": f"sed --in-place=.bak 's/C/A/' {_WAL}",
        "F-BASH-2 sed --in-place= empty": f"sed --in-place= s/a/b/ {_WAL}",
        # F-BASH-3: awk / perl in-place
        "F-BASH-3 awk -i inplace": f"awk -i inplace '{{print}}' {_WAL}",
        "F-BASH-3 gawk -i inplace": f"gawk -i inplace '{{print}}' {_WAL}",
        "F-BASH-3 perl -i -pe": f"perl -i -pe 's/C/A/' {_WAL}",
        "F-BASH-3 perl -pi -e": f"perl -pi -e 's/C/A/' {_WAL}",
        # F-BASH-4: クォート分割
        "F-BASH-4 quote lock": 'echo COMMIT > output/campaigns/c/campaign"."lock',
        "F-BASH-4 quote lock 2": "echo COMMIT > output/campaigns/c/campaign'.'lock",
        # F-BASH-5: >& リダイレクト
        "F-BASH-5 >&": f"echo x >& {_WAL}",
        "F-BASH-5 >& read-head": f"cat /tmp/x >& {_WAL}",
        "F-BASH-5 &>>": f"echo x &>> {_WAL}",
        # F2: find -delete / -exec
        "F2 find -delete": f"find output/campaigns/c/runs -name '*.jsonl' -delete",
        "F2 find -exec": f"find output/campaigns/c/runs -name x -exec rm {{}} +",
        # F3: git mv
        "F3 git mv": f"git mv {_WAL} /tmp/x",
        "F3 git mv reverse": f"git mv /tmp/x {_WAL}",
        # F4: ex / ed / sponge / sort -o
        "F4 ex": f"ex -sc wq {_WAL}",
        "F4 ed": f"ed {_WAL}",
        "F4 sponge": f"cat /tmp/x | sponge {_WAL}",
        "F4 sort -o": f"sort -o {_WAL} {_WAL}",
        # F6: chmod / chattr (DoS)
        "F6 chmod": f"chmod 000 {_WAL}",
        "F6 chattr": f"chattr +i {_WAL}",
        # BYP-parent: 親ディレクトリ破壊
        "BYP rm campaign dir": f"rm -rf output/campaigns/c",
        "BYP rm ccbench": f"rm -rf external/ccbench",
        "BYP git clean": f"git clean -fd output/",
        "BYP tar extract": f"tar -xf /tmp/e.tar -C output/campaigns/c/runs",
        # wrapper で head を隠す
        "wrapper taskset rm": f"taskset -c 0-47 rm {_WAL}",
        "wrapper env": f"env FOO=1 rm {_WAL}",
        "wrapper nice": f"nice -n 5 rm {_WAL}",
        "wrapper sudo sudo": f"sudo sudo rm {_WAL}",
        # self-probe 由来: 祖先の親を名指す削除・別表記
        "BYP rm external": "rm -rf external",           # ccbench の親 (build-variants 消える)
        "BYP rm ./campaign": "rm -rf ./output/campaigns/c",
        "BYP rm trailing/": "rm -rf output/campaigns/c/",
        "BYP rm tree root": "rm -rf output/campaigns",
        "install to WAL": f"install -m 644 evil {_WAL}",
        "dd of= reorder": f"dd of={_WAL} if=/dev/zero",
        "truncate stuck": f"truncate -s0 {_WAL}",
        "ex +wq": f"ex +wq {_WAL}",
        "perl -ni": f"perl -ni -e ';' {_WAL}",
        "cat read-head redirect": f"cat evil > {_WAL}",
        "fd-numbered redirect": f"echo x 1> {_WAL}",
        "mv multiarg": f"mv a b {_WAL}",
        "git -C clean": f"git -C . clean -fd output/",
    }
    for label, cmd in cases.items():
        ok, _ = GB.decide(cmd)
        assert not ok, f"確定 bypass finding が再発した [{label}]: {cmd!r}"


def test_bash_round2_bypasses_denied():
    """2 巡目敵対検証 (2026-07-03) の bypass finding GB2-1〜4 を回帰固定する。"""
    _BVBIN = f"{_BV}/silo_x_t0/ycsb_silo.exe"
    cases = {
        # GB2-1: 防護ツリー root 以上への glob 削除 (リテラル prefix で重なり判定)
        "GB2-1 rm campaigns/*": "rm -rf output/campaigns/*",
        "GB2-1 rm output/*": "rm -rf output/*",
        "GB2-1 mv campaigns glob": "mv output/campaigns/* /tmp/",
        # GB2-2: here-string で inline 実行 (opaque = fails-closed)
        "GB2-2 bash <<<": "bash <<< 'rm -rf output/campaigns'",
        "GB2-2 python3 - <<<": f"python3 - <<< 'open(\"{_WAL}\").read()'",
        # GB2-3: pipe 終端の bare interpreter で leaf を洗浄する
        "GB2-3 echo|python3": f"echo 'open(\"{_WAL}\",\"a\").write(\"x\")' | python3",
        "GB2-3 cat|bash": f"cat {_WAL} | bash",
        # GB2-4: git config -f <protected> は書き込み invocation
        "GB2-4 git config -f lock": f"git config -f {_LOCK} k v",
        "GB2-4 git config --file wal": f"git config --file {_WAL} a.b c",
        # 3 巡目 (2026-07-04) real: 絶対パス/~ の rm が防護ツリーを素通り
        "abs rm campaigns": f"rm -rf {_REPO}/output/campaigns/c",
        "abs rm ccbench": f"rm -rf {_REPO}/external/ccbench",
        "abs mv campaigns": f"mv {_REPO}/output/campaigns/c /tmp/",
        # 3 巡目 real: 改行がセグメント境界にならず先頭 read-only head が後続 writer を隠蔽
        "newline cat->cp": f"cat {_WAL}\ncp /tmp/evil {_WAL}",
        "newline ls->rm": f"ls\nrm -rf {_BV}",
        "newline true->tee": f"true\ntee {_WAL}",
        "newline echo->sh": f"echo start\nsh -c 'rm {_WAL}'",
        # 3 巡目 real: heredoc << 経由の bare interpreter (GB2-2 の << 綴り取り残し)
        "heredoc python": f"python3 <<EOF\nopen('{_WAL}','a').write('x')\nEOF",
        "heredoc bash rm": f"bash <<EOF\nrm -rf {_BV}\nEOF",
        "heredoc perl": f"perl <<EOF\nunlink '{_WAL}'\nEOF",
    }
    for label, cmd in cases.items():
        ok, _ = GB.decide(cmd)
        assert not ok, f"2/3 巡目 bypass が再発した [{label}]: {cmd!r}"


def test_bash_false_positive_fixes_allowed():
    """2 巡目の過剰拒否 F-FP-1〜4 の解消を固定する (計測層を巻き込まない)。"""
    _BVBIN = f"{_BV}/silo_x_t0/ycsb_silo.exe"
    for cmd in (
        # F-FP-1: build-variants 配下バイナリの実行 (書き込みでない = 計測の正道)
        f"{_BVBIN} -w YCSB",
        f"perf stat -- {_BVBIN} -w YCSB",
        f"perf stat -e cycles -- numactl -N 0 {_BVBIN}",
        f"numactl -N 0 taskset -c 0-47 {_BVBIN}",
        f"cmake --build {_BV}/silo_x_t0",              # ビルドシステムの生成は正当
        f"make -C {_BV}/silo_x_t0",
        # F-FP-2: campaign dir 配下の proof-chain でない reports/ の mv/rm
        "mv output/campaigns/c/reports/a.png output/campaigns/c/reports/b.png",
        "rm output/campaigns/c/reports/old.png",
        "rm -rf output/campaigns/c/reports/tmp",
        # F-FP-3: taskset/numactl の CPU リスト・マスクを skip して実 head を見る
        f"taskset -c 0-47 cat {_WAL}",
        f"numactl -C 0,2,4-6 grep COMMIT {_WAL}",
        f"taskset 0xff grep -c ABORT {_WAL}",
        # F-FP-4: 防護対象パス字面なしの mention 語 + 不透明構文は拒否しない
        "perf stat --output=/tmp/o.txt -- true",
        "cmake -DCCBENCH_BUILD=ON /tmp/src && echo done",
        "echo external deps: $(nproc) cores",
        # 3 巡目 (2026-07-04) false-positive: バイナリ/シンボル検査 (規律1 の nm 手検証)
        f"nm -C {_BVBIN}",
        f"objdump -d {_BVBIN}",
        f"readelf -a {_BVBIN}",
        f"ldd {_BVBIN}",
        f"size {_BVBIN}",
        # 3 巡目 false-positive: du (ディスク使用量) の純読み
        f"du -sh {_WAL}",
        f"du -sh {_BV}",
        "du -sh output/campaigns/c/runs",
        # 3 巡目 false-positive: tar/rsync の backup (防護ツリーを読む方向) は通す。
        # ただし末端 (build-variants/WAL) を tar が触る形は archive 上書きリスクゆえ末端層で
        # 拒否したまま (cp -r/nm で代替) — ここで通すのは campaign dir/reports 等ツリーの backup。
        "tar czf /tmp/backup.tgz output/campaigns/c",
        "tar -czf /tmp/r.tgz output/campaigns/c/reports",
        "rsync -a output/campaigns/c /tmp/backup/",
    ):
        ok, why = GB.decide(cmd)
        assert ok, f"計測層の正当コマンドが誤拒否された (F-FP): {cmd!r} ({why})"


def test_bash_other_keeps_legacy_acceptance_bits():
    """site=None と OTHER は既存 guard の許可/拒否を 1 bit も変えない。"""
    cases = {
        "ls -la": True,
        f"cat {_WAL}": True,
        f"echo x >> {_WAL}": False,
        f"rm -rf {_BV}": False,
        f"python3 -c \"open('{_WAL}','a').write('x')\"": False,
        f"{_BV}/silo_x_t0/ycsb_silo.exe -w YCSB": True,
        "pytest -q": True,
        "python3 -m pytest -q": True,
        "python3 -mpytest -q": True,
        "python3 -mtools.pegasus.exec_calibrate argv.json": True,
        "python3 -qm pytest -q": True,
        "cmake --build build": True,
        "make -j48": True,
        "ninja -C build": True,
        "ctest": True,
        "perf stat -- ./ycsb_silo.exe": True,
        "bash -xec 'pytest -q'": True,
        "sh -euxc 'cmake --build build'": True,
        "python3 tools/run_tests.py && pytest -q": True,
    }
    for cmd, expected in cases.items():
        default = GB.decide(cmd)
        explicit_other = GB.decide(cmd, site="OTHER")
        assert default == explicit_other, \
            f"site=None と OTHER が不一致: {cmd!r}: {default} != {explicit_other}"
        assert default[0] is expected, \
            f"既存受理 bit が変化した: {cmd!r}: {default[0]} != {expected}"


def test_bash_login_blocks_python_module_pytest_variants():
    # M8: -m pytest 判定を python3.10 限定へ戻す変異を kill する。
    for cmd in (
        "python3 -m pytest -q",
        "python -m pytest -q",
        "python3.10 -m pytest -q",
        "/usr/bin/python3 -m pytest -q",
        ".venv/bin/python -m pytest -q",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"任意 python 実体の -m pytest が login で通った: {cmd!r}"


def test_bash_login_blocks_attached_and_bundled_python_modules():
    for cmd in (
        "python3 -mpytest -q",
        "python3 -qmpytest -q",
        "python3 -qm pytest -q",
        "python3 -Om pytest -q",
        "python3 -mtools.pegasus.exec_calibrate argv.json",
        "python3 -qm tools.pegasus.exec_calibrate argv.json",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"密着/結合した Python -m の重量実行が通った: {cmd!r}"


def test_bash_login_python_module_option_boundaries_allowed():
    for cmd in (
        "python3 -mpytest --collect-only",
        "python3 -qm pytest --help",
        "python3 -mtools.run_tests --collect-only",
        "python3 -qm tools.run_tests --collect-only",
        "python3 -Wmodule -q script.py",
        "python3 -Xmodule -q script.py",
        "python3 -c 'print(\"module\")'",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"Python -m 境界の非重量形が過剰拒否された: {cmd!r} ({why})"


def test_bash_login_module_identity_and_borrow_matrix():
    """module identity は綴り・結合形・interpreter 版に依存させない。"""
    for cmd in (
        "python3 -m pytest.__main__ tools/run_tests.py",
        "python3 -mpytest.__main__ tools/pegasus/fetch_third_party.py",
        "python3 -qm _pytest.main tools/pegasus/dispatch_compute.py",
        "python3 -qmpytest tools/run_tests.py",
        "python3 -Bmpytest tools/pegasus/submit_certify.sh",
        "python3.10 -Bm pytest.__main__ tools/run_tests.py",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"module 実行体が sanctioned data path を借用した: {cmd!r}"


def test_bash_login_script_executor_modules_classify_their_target():
    for cmd in (
        "python3 -m cProfile tools/pegasus/exec_calibrate.py",
        "python3 -mcProfile -o /tmp/profile.out "
        "tools/pegasus/certify_calibration.sh",
        "python3.10 -Bmprofile -s cumulative "
        "tools/pegasus/exec_calibrate.py",
        "python3 -mpdb -c continue tools/pegasus/exec_calibrate.py",
        "python3 -mtrace --trace tools/pegasus/exec_calibrate.py",
        "python3 -mrunpy tools.pegasus.exec_calibrate",
        "python3 -m coverage run tools/pegasus/exec_calibrate.py",
        "python3 -BmcProfile -- tools/pegasus/exec_calibrate.py --help",
        "python3.10 -Bmtrace --trace -- "
        "tools/pegasus/exec_calibrate.py --report",
        "python3 -mcProfile tools/pegasus/exec_calibrate.py --help",
        "env FOO=1 nice -n 0 python3.10 -BmcProfile -- "
        "tools/pegasus/exec_calibrate.py --help",
        "bash -lc 'python3 -Bmtrace --trace -- "
        "tools/pegasus/exec_calibrate.py --report'",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"script 実行 module が target の admission を迂回した: {cmd!r}"


def test_bash_login_closes_additional_executor_module_spellings():
    absolute = os.path.join(_REPO, "tools/pegasus/collect_receipt.py")
    commands = (
        "python3 -m pydoc tools/pegasus/collect_receipt.py",
        "python3 -mpydoc -- tools/pegasus/collect_receipt.py",
        "python3.10 -Bmpydoc -- ./tools/pegasus/collect_receipt.py",
        f"python3.10 -Bmpydoc -- {absolute}",
        "python3.10 -Bmdoctest tools/pegasus/collect_receipt.py",
        "python3.10 -Bmunittest tools/pegasus/collect_receipt.py",
        "python3 -m pydoc /tmp/safe.py tools/pegasus/collect_receipt.py",
        "python3 -m doctest /tmp/safe.py tools/pegasus/collect_receipt.py",
        "python3 -m unittest /tmp/safe.py tools/pegasus/collect_receipt.py",
        "python3 -m trace --trace --module tools.pegasus.exec_calibrate",
        "env FOO=1 nice -n 0 python3.10 -Bmpydoc -- "
        "tools/pegasus/collect_receipt.py",
        "bash -lc 'python3 -m doctest tools/pegasus/collect_receipt.py'",
    )
    for cmd in commands:
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"追加 executor module の実行対象が通った: {cmd!r}"
    for cmd in (
        "python3 -m pydoc /tmp/safe.py",
        "python3 -m doctest /tmp/safe.py",
        "python3 -m unittest /tmp/safe.py",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"Pegasus 外の executor target が誤拒否された: {cmd!r} ({why})"


def test_bash_login_executor_nonexecuting_modes_restore_baseline_allow():
    for cmd in (
        "python3 -m timeit tools/pegasus/exec_calibrate.py",
        "python3.10 -B -m timeit tools/pegasus/exec_calibrate.py",
        "python3 -m runpy tools/pegasus/exec_calibrate.py",
        "env FOO=1 python3 -B -m runpy tools/pegasus/exec_calibrate.py",
        "python3 -m trace --report -f /tmp/counts "
        "tools/pegasus/exec_calibrate.py",
        "bash -lc 'python3 -m trace --report -f /tmp/counts "
        "tools/pegasus/exec_calibrate.py'",
        "python3 -m cProfile --help tools/pegasus/exec_calibrate.py",
        "python3 -B -m cProfile --help tools/pegasus/exec_calibrate.py",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"module の非 file 実行 mode が過剰拒否された: {cmd!r} ({why})"


def test_bash_login_executor_output_cannot_overwrite_admission_paths():
    commands = (
        "python3 -BmcProfile -o tools/pegasus/exec_calibrate.py /tmp/safe.py",
        "python3 -BmcProfile -otools/pegasus/exec_calibrate.py /tmp/safe.py",
        "python3.10 -Bmprofile "
        "--outfile=tools/pegasus/collect_receipt.py /tmp/safe.py",
        "env FOO=1 nice -n 0 python3 -BmcProfile "
        "--outfile tools/pegasus/fetch_third_party.py /tmp/safe.py",
        "python3 -BmcProfile -o tools/run_tests.py -- /tmp/safe.py",
    )
    for cmd in commands:
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"executor が admission path を出力先にできた: {cmd!r}"

    for cmd in (
        "python3 -BmcProfile -o /tmp/profile.out /tmp/safe.py",
        "python3 -m cProfile -o tools/pegasus/exec_calibrate.py "
        "--help /tmp/safe.py",
        "python3 -BmcProfile -- /tmp/safe.py "
        "-o tools/pegasus/exec_calibrate.py",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"program argv の出力 option 字面が誤拒否された: {cmd!r} ({why})"


def test_bash_login_executor_recursion_module_denied():
    for cmd in (
        "python3 -m cProfile -m pytest -q",
        "python3 -mcProfile -mpytest -q",
        "python3 -m cProfile -o /tmp/p.out -m pytest -q "
        "orchestrator/tests/test_hooks.py",
        "python3 -m profile -m pytest -q",
        "python3 -m pdb -m pytest -q",
        "python3 -m trace --trace --module pytest -q",
        "python3 -m runpy pytest -q",
        "python3 -m cProfile -m cProfile -m pytest -q",
        "python3 -m cProfile -m cmake --build build",
        "python3.10 -Bm profile -s cumulative -m pytest",
        "python3 -m pdb -m _pytest.main",
        "env FOO=1 nice -n 0 python3 -m cProfile -m pytest",
        "bash -lc 'python3 -m cProfile -m pytest -q'",
        "python3 -m cProfile -m pytest tools/check_ai_provenance.py",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"executor 越しの重量実行が login で通った: {cmd!r}"


def test_bash_login_executor_recursion_coverage_denied():
    for cmd in (
        "python3 -m coverage run -m pytest -q",
        "python3 -m coverage run --branch -m pytest",
        "python3 -m coverage run -m pytest.__main__",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"executor 越しの重量実行が login で通った: {cmd!r}"


def test_bash_login_executor_recursion_script_denied():
    for cmd in (
        "python3 -m cProfile pytest -q",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"executor 越しの重量実行が login で通った: {cmd!r}"


def test_bash_login_executor_recursion_nonexecuting_and_light_allowed():
    for cmd in (
        "python3 -m cProfile -m pytest --collect-only",
        "python3 -m cProfile -m pytest --help",
        "python3 -m coverage run -m pytest --collect-only",
        "python3 -m cProfile /tmp/safe.py",
        "python3 -m cProfile -- /tmp/safe.py --version",
        "python3 -m runpy tools/pegasus/exec_calibrate.py",
        "python3 -m cProfile -m timeit x",
        "python3 -m cProfile -m json.tool /tmp/a.json",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"executor の非実行形・非重量が誤拒否された: {cmd!r} ({why})"


def test_bash_login_executor_recursion_nonrefusing_sites_unchanged():
    for site in ("OTHER", "PEGASUS_COMPUTE"):
        for cmd in (
            "python3 -m cProfile -m pytest -q",
            "python3 -m coverage run -m pytest -q",
            "python3 -m cProfile pytest -q",
        ):
            ok, why = GB.decide(cmd, site=site)
            assert ok, f"非 refusing site で誤拒否された: {site} {cmd!r} ({why})"


def test_bash_login_executor_recursion_existing_denials_preserved():
    for cmd in (
        "python3 -m pytest -q",
        "python3 -m cProfile tools/pegasus/exec_calibrate.py",
        "python3 -qmcProfile -m pytest",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"既存の重量実行・admission 拒否が壊れた: {cmd!r}"


def test_bash_login_executor_recursion_deep_nesting_has_no_stack_limit():
    prefix = "python3 " + "-m cProfile " * 1100
    for tail in (
        "-m json.tool ; pytest -q",
        "-m pytest -q",
    ):
        cmd = prefix + tail
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"深い executor 越しの重量実行が login で通った: {tail!r} ({why})"
        assert "pytest" in why, f"pytest 以外の理由で拒否された: {tail!r} ({why})"

    cmd = prefix + "-m json.tool /tmp/a.json"
    ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
    assert ok, f"深い executor の軽量形が誤拒否された: {why}"


def test_bash_login_executor_recursion_precedes_sanctioned_allow():
    for cmd in (
        "python3 -m cProfile tools/run_tests.py -m pytest -q",
        "python3 -m profile -o /tmp/p tools/run_tests.py -m pytest -q",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"sanctioned 早期許可で内側の重量実行が通った: {cmd!r} ({why})"


def test_bash_login_executor_recursion_matches_direct_form():
    for wrapped, direct in (
        ("python3 -m cProfile -- -m pytest", "python3 -- -m pytest"),
        ("python3 -m cProfile /tmp/safe.py -mpytest",
         "python3 /tmp/safe.py -mpytest"),
        ("python3 -m cProfile -- -W pytest", "python3 -- -W pytest"),
        ("python3 -m cProfile /tmp/safe.py", "python3 /tmp/safe.py"),
        ("python3 -m cProfile -m pytest --collect-only",
         "python3 -m pytest --collect-only"),
        ("python3 -m cProfile -m json.tool /tmp/a.json",
         "python3 -m json.tool /tmp/a.json"),
        ("python3 -m cProfile -m pytest -q", "python3 -m pytest -q"),
    ):
        wrapped_ok, wrapped_why = GB.decide(wrapped, site="PEGASUS_LOGIN")
        direct_ok, direct_why = GB.decide(direct, site="PEGASUS_LOGIN")
        assert wrapped_ok == direct_ok, (
            f"包み形と直接形の判定が不一致: "
            f"wrapped={wrapped!r}, ok={wrapped_ok}, reason={wrapped_why!r}; "
            f"direct={direct!r}, ok={direct_ok}, reason={direct_why!r}"
        )


def test_bash_login_pydoc_server_and_write_modes_do_not_execute_positionals():
    commands = (
        "python3 -Bmpydoc -n localhost tools/pegasus/exec_calibrate.py",
        "python3.10 -Bmpydoc -p 8080 tools/pegasus/exec_calibrate.py",
        "python3 -m pydoc -b tools/pegasus/exec_calibrate.py",
        "python3 -m pydoc -w tools/pegasus/exec_calibrate.py",
        "env FOO=1 nice -n 0 python3.10 -Bmpydoc "
        "-n localhost -- tools/pegasus/exec_calibrate.py",
        "bash -lc 'python3 -B -m pydoc -w tools/pegasus/exec_calibrate.py'",
    )
    for cmd in commands:
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"pydoc 非実行 mode が位置引数を実行体扱いした: {cmd!r} ({why})"


def test_bash_login_static_reader_modules_keep_paths_as_data():
    for cmd in (
        "python3 -m py_compile tools/pegasus/exec_calibrate.py",
        "python3 -B -m py_compile tools/pegasus/collect_receipt.py",
        "python3 -B -m py_compile tools/pegasus/certify_calibration.sh",
        "python3.10 -m json.tool tools/pegasus/policy.json",
        "python3 -m compileall tools/pegasus",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"静的 reader module が data path を実行体扱いした: {cmd!r} ({why})"


def test_bash_login_interpreter_prefix_value_options_reveal_scripts():
    for cmd in (
        "python3 -W ignore tools/pegasus/exec_calibrate.py",
        "python3 -Wignore tools/pegasus/exec_calibrate.py",
        "python3 -X faulthandler tools/pegasus/exec_calibrate.py",
        "python3 -Xfaulthandler tools/pegasus/exec_calibrate.py",
        "python3 -- tools/pegasus/exec_calibrate.py",
        "bash -O extglob tools/pegasus/certify_calibration.sh",
        "bash -Oextglob tools/pegasus/certify_calibration.sh",
        "bash -o errexit tools/pegasus/certify_calibration.sh",
        "bash --rcfile /tmp/bashrc tools/pegasus/certify_calibration.sh",
        "bash -- tools/pegasus/certify_calibration.sh",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"interpreter option 値が実 script を隠した: {cmd!r}"

    # baseline が最初の非 option token とみなした重量 path/綴りは fail-closed。
    for cmd in (
        "python3 -c 'print(1)' -m pytest",
        "python3 --help tools/pegasus/collect_receipt.py",
        "python3 -Z tools/pegasus/collect_receipt.py",
        "env FOO=1 python3.10 -Z tools/pegasus/collect_receipt.py",
        "bash -s tools/pegasus/certify_calibration.sh",
        "python3 -mpy_compile tools/pegasus/collect_receipt.py",
        "python3 -mrunpy tools/pegasus/exec_calibrate.py",
        "python3.10 -Bmtimeit tools/pegasus/exec_calibrate.py",
        "python3 -mcProfile --help tools/pegasus/exec_calibrate.py",
        "python3 -Bmpy_compile tools/pegasus/certify_calibration.sh",
        "python3.10 -mjson.tool tools/pegasus/policy.json",
        "python3 -W tools/pegasus/exec_calibrate.py /tmp/safe.py",
        "bash -O tools/pegasus/certify_calibration.sh /tmp/safe.sh",
        "bash -lc 'python3 --help tools/pegasus/collect_receipt.py'",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"interpreter の baseline 実行体が fail-open した: {cmd!r}"

    for cmd in (
        "python3 -c 'print(1)' tools/pegasus/exec_calibrate.py",
        "python3.10 -Bc 'print(1)' tools/pegasus/exec_calibrate.py",
        "env FOO=1 python3 -c 'print(1)' tools/pegasus/exec_calibrate.py",
        "bash -c 'true' tools/pegasus/certify_calibration.sh",
        "bash -xc 'true' tools/pegasus/certify_calibration.sh",
        "python3 -c 'print(1)' /tmp/plain-data",
        "python3 --help /tmp/plain-data",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"interpreter の data argv が誤拒否された: {cmd!r} ({why})"


def test_bash_login_shell_startup_files_are_execution_targets():
    path = "tools/pegasus/certify_calibration.sh"
    absolute = os.path.join(_REPO, path)
    for cmd in (
        f"bash --rcfile {path} -i",
        f"bash --rcfile ./{path} -i",
        f"bash --init-file={absolute} -i",
        f"env FOO=1 nice -n 0 bash --rcfile={path} -i",
        f"qstat; bash --init-file {path} -i",
        f"bash -lc 'bash --rcfile {absolute} -i'",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"shell startup file の実行対象が通った: {cmd!r}"
    ok, why = GB.decide("bash --rcfile /tmp/bashrc -i", site="PEGASUS_LOGIN")
    assert ok, f"Pegasus 外の shell startup file が誤拒否された: {why}"

    for cmd in (
        f"bash --rcfile {path} -c 'true'",
        f"bash --init-file={path} -c 'true'",
        f"env FOO=1 nice -n 0 bash --rcfile={path} -c 'true'",
        f"bash -lc \"bash --rcfile {path} -c 'true'\"",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"非対話 shell の未使用 startup file が誤拒否された: {cmd!r} ({why})"

    for cmd in (
        f"bash --rcfile {path} -ic 'true'",
        f"bash --init-file={path} -i -c 'true'",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"対話指定付き shell startup file が通った: {cmd!r}"


def test_bash_nonrefusing_sites_allow_module_and_prefix_matrix():
    commands = (
        "python3 -m pytest.__main__ orchestrator/tests/test_hooks.py",
        "python3 -mpytest tools/run_tests.py",
        "python3 -m cProfile tools/pegasus/exec_calibrate.py",
        "python3 -mpdb tools/pegasus/exec_calibrate.py",
        "python3 -m py_compile tools/pegasus/exec_calibrate.py",
        "python3 -W ignore tools/pegasus/exec_calibrate.py",
        "bash -O extglob tools/pegasus/certify_calibration.sh",
        "bash --rcfile tools/pegasus/certify_calibration.sh -i",
        "python3.10 -Bmpydoc -- tools/pegasus/collect_receipt.py",
        "python3 -c 'print(1)' -m pytest",
        "python3 -m timeit tools/pegasus/exec_calibrate.py",
    )
    for site in ("OTHER", "PEGASUS_COMPUTE"):
        for cmd in commands:
            ok, why = GB.decide(cmd, site=site)
            assert ok, f"{site} で parser matrix の受理 bit が変化した: {cmd!r} ({why})"


def test_bash_login_wrapper_values_reveal_actual_head():
    # M9: wrapper の option 値 skip を削除する変異を kill する。
    for cmd in (
        "sudo -u tanab pytest -q",
        "env -u PYTHONPATH pytest -q",
        "env FOO=1 pytest -q",
        "nice -n 5 pytest -q",
        "timeout 5 pytest -q",
        "taskset -c 0-47 pytest -q",
        "numactl -C 0,2 pytest -q",
        "time -f %E pytest -q",
        "nohup pytest -q",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"wrapper 内の pytest が login で通った: {cmd!r}"


def test_bash_login_retokenizes_env_split_and_skips_exec_argv0():
    for cmd in (
        "env -S 'pytest -q'",
        "env --split-string='python3 -m pytest -q'",
        "env -S 'python3 -m tools.pegasus.exec_calibrate argv.json'",
        "sudo env -S 'pytest -q'",
        "exec -a harmless pytest -q",
        "exec -a harmless python3 -m tools.pegasus.exec_calibrate argv.json",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"wrapper が隠した実 head が login で通った: {cmd!r}"
    for cmd in (
        "env -S 'git status'",
        "exec -a harmless git status",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"wrapper 内の非重量 command が過剰拒否された: {cmd!r} ({why})"


def test_bash_login_recurses_into_shell_command_strings():
    # M10: -lc / shell 再帰を削除する変異を kill する。
    for cmd in (
        "bash -lc 'pytest -q'",
        "sh -c 'cmake --build b'",
        "zsh -ic 'python3 -m pytest -q'",
        "bash -lc \"sh -c 'pytest -q'\"",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"shell -c 系の内側にある重い処理が通った: {cmd!r}"


def test_bash_login_recurses_into_bundled_shell_command_options():
    for cmd in (
        "bash -xec 'pytest -q'",
        "sh -euxc 'cmake --build build'",
        "zsh -lxc 'python3 -mpytest -q'",
        "bash -ce 'pytest -q'",
        "bash -xec \"sh -lc 'pytest -q'\"",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"結合 shell option の c 内にある重い処理が通った: {cmd!r}"


def test_bash_login_shell_without_command_option_stays_allowed():
    for cmd in (
        "bash script.sh",
        "bash -xe script.sh",
        "sh -eux script.sh",
        "zsh -l script.zsh",
        "bash --norc script.sh",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"-c を持たない shell script 実行が過剰拒否された: {cmd!r} ({why})"


def test_bash_import_failure_fallback_refuses_login():
    # M12: site_policy import 失敗 fallback を allow に変える変異を kill する。
    fallback = GB._runtime_site(policy=None, hostname="pegasus02.example")
    assert fallback == "PEGASUS_LOGIN"
    ok, _ = GB.decide("pytest -q", site=fallback)
    assert not ok, "policy import 失敗時も pegasus02 は LOGIN 相当で拒否すべき"

    other = GB._runtime_site(policy=None, hostname="worker.example")
    assert other == "OTHER"
    ok, why = GB.decide("pytest -q", site=other)
    assert ok, f"非 Pegasus fallback は既存挙動を維持すべき: {why}"


def test_bash_fallback_regex_matches_site_policy_login_classification():
    """fallback regex と U1 classify_site の LOGIN 集合を機械照合する。"""
    assert GB.site_policy is not None, "repo-root bootstrap 後も site_policy を import できない"
    assert GB._BOOTSTRAP_ROOT in sys.path
    assert GB._LOGIN_FALLBACK_RE.pattern == GB.site_policy.LOGIN_FALLBACK_RE.pattern
    for suffix in range(1, 10):
        hostname = f"pegasus0{suffix}"
        assert GB._LOGIN_FALLBACK_RE.fullmatch(hostname)
        actual = GB.site_policy.classify_site(hostname, {}, True)
        assert actual == GB.site_policy.PEGASUS_LOGIN, \
            f"fallback が拾う {hostname} を U1 が LOGIN に分類しない: {actual}"


def test_bash_login_blocks_direct_heavy_forms_and_segments():
    for cmd in (
        "pytest -q",
        ".venv/bin/pytest -q",
        ".venv/bin/py.test -q",
        "cmake --build build",
        "make -j48",
        "make --jobs=48",
        "ninja -C build",
        "ctest",
        "perf stat -- ./ycsb_silo.exe",
        "perf record -- ./ycsb_silo.exe",
        "./ycsb_silo.exe -w YCSB",
        "external/ccbench/build-variants/silo/ycsb_silo.exe -w YCSB",
        "python3 tools/run_tests.py && pytest -q",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"login の重い直接実行が通った: {cmd!r}"


def test_bash_suspect_blocks_but_compute_allows_heavy_forms():
    for cmd in ("pytest -q", "cmake --build build", "ninja -C build"):
        ok, _ = GB.decide(cmd, site="PEGASUS_SUSPECT")
        assert not ok, f"SUSPECT site で重い処理が通った: {cmd!r}"
        ok, why = GB.decide(cmd, site="PEGASUS_COMPUTE")
        assert ok, f"COMPUTE site の重い処理を第二防壁が拒否した: {cmd!r} ({why})"


@pytest.mark.parametrize("site", ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"))
def test_bash_refusing_sites_block_raw_systemd_run(site):
    assert "systemd-run" not in GB._WRAPPERS
    command = "systemd-run --user --scope -- /bin/true"
    ok, why = GB.decide(command, site=site)
    assert not ok, f"{site} で raw systemd-run が通った"
    assert "systemd-run" in why


def test_bash_refusing_sites_block_command_p_systemd_run():
    command = "command -p systemd-run --user --scope -- /bin/true"
    for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
        ok, why = GB.decide(command, site=site)
        assert not ok, f"{site} で command -p の systemd-run が通った"
        assert "systemd-run" in why


def test_bash_refusing_sites_allow_command_v_systemd_run():
    command = "command -v systemd-run"
    for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
        ok, why = GB.decide(command, site=site)
        assert ok, f"{site} で command -v の問い合わせが拒否された: {why}"


def test_bash_refusing_sites_allow_command_capital_v_systemd_run():
    command = "command -V systemd-run"
    for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
        ok, why = GB.decide(command, site=site)
        assert ok, f"{site} で command -V の問い合わせが拒否された: {why}"


def test_bash_refusing_sites_reveal_systemd_run_behind_wrappers():
    commands = (
        "sudo systemd-run --user --scope -- /bin/true",
        "env FOO=bar systemd-run --user --scope -- /bin/true",
        "nohup systemd-run --user --scope -- /bin/true",
        "timeout 60 systemd-run --user --scope -- /bin/true",
        "nice systemd-run --user --scope -- /bin/true",
    )
    for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
        for command in commands:
            ok, _ = GB.decide(command, site=site)
            assert not ok, f"{site} で wrapper 内の systemd-run が通った: {command!r}"


def test_bash_other_allows_systemd_run():
    command = "systemd-run --user --scope -- /bin/true"
    ok, why = GB.decide(command, site="OTHER")
    assert ok, f"OTHER の systemd-run 受理 bit が変化した: {why}"


def test_bash_systemd_run_change_never_expands_acceptance_corpus():
    """G6 前の代表 bit と比較し、拒否から許可への反転が 0 件であることを固定する。"""
    pre_g6_bits = {
        "git status --short": True,
        "qstat 12345": True,
        "pytest --collect-only": True,
        "pytest -q": False,
        "env FOO=bar pytest -q": False,
        "python3 tools/pegasus/exec_calibrate.py argv.json": False,
        "systemd-run --user --scope -- /bin/true": True,
        "command -v systemd-run": True,
        "command -V systemd-run": True,
        "env command -v systemd-run": True,
        "command -pv systemd-run": True,
        "command -p -V systemd-run": True,
        "command systemd-run --user --scope -- /bin/true": True,
        "command -p systemd-run --user --scope -- /bin/true": True,
        "command -- systemd-run --user --scope -- /bin/true": True,
        "command -v pytest": False,
        "command -V pytest": False,
        "command -v systemd-run; pytest -q": False,
        "sudo systemd-run --user --scope -- /bin/true": True,
        "env FOO=bar systemd-run --user --scope -- /bin/true": True,
        "nohup systemd-run --user --scope -- /bin/true": True,
        "timeout 60 systemd-run --user --scope -- /bin/true": True,
        "nice systemd-run --user --scope -- /bin/true": True,
    }
    for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
        newly_allowed = [
            command
            for command, was_allowed in pre_g6_bits.items()
            if GB.decide(command, site=site)[0] and not was_allowed
        ]
        assert newly_allowed == [], \
            f"{site} で G6 が受理集合を拡大した: {newly_allowed}"


def test_bash_command_reader_fix_only_reopens_pre_a12_corpus():
    """A#12 直前の代表 bit から問い合わせ形以外を新規許可しない。"""
    pre_a12_bits = {
        "git status --short": True,
        "pytest --collect-only": True,
        "command -v systemd-run": False,
        "command -V systemd-run": False,
        "env command -v systemd-run": False,
        "command -pv systemd-run": False,
        "command -p -V systemd-run": False,
        "command systemd-run --user --scope -- /bin/true": False,
        "command -p systemd-run --user --scope -- /bin/true": False,
        "command -- systemd-run --user --scope -- /bin/true": False,
        "command -v pytest": False,
        "command -V pytest": False,
        "command -v systemd-run; pytest -q": False,
        "command -v systemd-run && systemd-run --user --scope -- /bin/true": False,
        "systemd-run --user --scope -- /bin/true": False,
        "sudo systemd-run --user --scope -- /bin/true": False,
    }
    expected_newly_allowed = [
        "command -v systemd-run",
        "command -V systemd-run",
        "env command -v systemd-run",
        "command -pv systemd-run",
        "command -p -V systemd-run",
    ]
    for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
        newly_allowed = [
            command
            for command, was_allowed in pre_a12_bits.items()
            if GB.decide(command, site=site)[0] and not was_allowed
        ]
        assert newly_allowed == expected_newly_allowed, \
            f"{site} で A#12 の受理集合差分が逸脱した: {newly_allowed}"


def test_bash_login_nonexecuting_forms_allowed():
    # M14: introspection / dry-run まで拒否する過剰縮小変異を kill する。
    for cmd in (
        "ninja -t targets",
        "ninja -t graph",
        "ninja -t query target",
        "ninja -t deps",
        "ninja -t compdb",
        "ninja --tool targets",
        "ninja --help",
        "ninja --version",
        "make -n -j48",
        "make --dry-run --jobs=48",
        "ctest -N",
        "ctest --show-only",
        "ctest --show-only=json-v1",
        "ctest --help",
        "ctest --version",
        "cmake --help",
        "cmake --version",
        "pytest --collect-only",
        "pytest --help",
        "pytest --version",
        "python3 -m pytest --collect-only",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"非実行/introspection 形が過剰拒否された: {cmd!r} ({why})"


def test_bash_login_rejects_mutating_or_unknown_ninja_tools():
    for cmd in (
        "ninja -t clean",
        "ninja -t cleandead",
        "ninja -t recompact",
        "ninja -t restat",
        "ninja -t future-unknown-tool",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"読み取り専用でない ninja tool が login で通った: {cmd!r}"


_FETCH_THIRD_PARTY_SANCTIONED_SPELLINGS = (
    "python3 tools/pegasus/fetch_third_party.py fetch",
    "python3 ./tools/pegasus/fetch_third_party.py hydrate",
    "./tools/pegasus/fetch_third_party.py verify",
)


_PEGASUS_EXPECTED_CLASSES = {
    "tools/claude_session_ledger.py": "unknown",
    "tools/pegasus/a5_second_boot_backoff_sweep.sh": "dispatch-required",
    "tools/pegasus/acceptance_nproc_study.sh": "dispatch-required",
    "tools/pegasus/b10_backoff_grid.sh": "dispatch-required",
    "tools/pegasus/b10_backoff_shape_campaign.sh": "dispatch-required",
    "tools/pegasus/certify_calibration.sh": "dispatch-required",
    "tools/pegasus/collect_receipt.py": "unknown",
    "tools/pegasus/collect_t126_qualification.py": "unknown",
    "tools/pegasus/dispatch_compute.py": "local-ok",
    "tools/pegasus/exec_calibrate.py": "dispatch-required",
    "tools/pegasus/fetch_third_party.py": "local-ok",
    "tools/pegasus/floor_campaign.sh": "dispatch-required",
    "tools/pegasus/floor_pair_campaign.sh": "dispatch-required",
    "tools/pegasus/floor_scoping.sh": "dispatch-required",
    "tools/pegasus/generate_floor_masstree_payload_policy.py": "unknown",
    "tools/pegasus/make_acquisition_receipt.py": "dispatch-required",
    "tools/pegasus/mocc_trace_pilot.sh": "dispatch-required",
    "tools/pegasus/oracle_n_pilot.sh": "dispatch-required",
    "tools/pegasus/p3_s4_loop_pegasus.sh": "dispatch-required",
    "tools/pegasus/paper_story_a1_paired.sh": "dispatch-required",
    "tools/pegasus/paper_story_a2_certification.sh": "dispatch-required",
    "tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs": "dispatch-required",
    "tools/pegasus/probes/t1259_qsub_env_delivery_probe.py": "dispatch-required",
    "tools/pegasus/probes/t139_positive_control_probe.pbs": "unknown",
    "tools/pegasus/probes/t139_positive_control_probe.sh": "unknown",
    "tools/pegasus/probes/t139_r4_env_probe.pbs": "dispatch-required",
    "tools/pegasus/probes/t139_r4_env_probe.py": "dispatch-required",
    "tools/pegasus/probes/t139_r4_env_probe.sh": "dispatch-required",
    "tools/pegasus/probes/t1403_walltime_sigterm_probe.pbs": "unknown",
    "tools/pegasus/probes/t1403_walltime_sigterm_probe.py": "unknown",
    "tools/pegasus/probes/t1683_rr5_cost_probe.pbs": "dispatch-required",
    "tools/pegasus/probes/t1683_rr5_cost_probe.py": "dispatch-required",
    "tools/pegasus/probes/t2187_adaptive_const_probe.pbs": "dispatch-required",
    "tools/pegasus/probes/t2187_adaptive_const_probe.py": "dispatch-required",
    "tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs": "dispatch-required",
    "tools/pegasus/probes/t2228_driver_gate_liveness_probe.py": "dispatch-required",
    "tools/pegasus/probes/t293_perf_site_probe.pbs": "unknown",
    "tools/pegasus/probes/t293_perf_site_probe.py": "unknown",
    "tools/pegasus/probes/t316_sandbox_backend_probe.pbs": "dispatch-required",
    "tools/pegasus/probes/t316_sandbox_backend_probe.py": "dispatch-required",
    "tools/pegasus/probes/t419_probe_causality.pbs": "unknown",
    "tools/pegasus/probes/t419_probe_causality.py": "unknown",
    "tools/pegasus/probes/t503_restore_durability_probe.pbs": "unknown",
    "tools/pegasus/probes/t503_restore_durability_probe.py": "unknown",
    "tools/pegasus/probes/t503_restore_durability_recover.pbs": "unknown",
    "tools/pegasus/probes/t503_restore_durability_verdict.pbs": "unknown",
    "tools/pegasus/run_acceptance_nproc_study.py": "dispatch-required",
    "tools/pegasus/run_probe.py": "dispatch-required",
    "tools/pegasus/run_ss2pl_lock_study.py": "dispatch-required",
    "tools/pegasus/run_t139_a12_stress_check.py": "dispatch-required",
    "tools/pegasus/silo_ladder_rung1.sh": "dispatch-required",
    "tools/pegasus/smoke_probe.sh": "dispatch-required",
    "tools/pegasus/ss2pl_lock_study.sh": "dispatch-required",
    "tools/pegasus/submit_a5_second_boot_backoff_sweep.sh": "local-ok",
    "tools/pegasus/submit_b10_backoff_grid.sh": "local-ok",
    "tools/pegasus/submit_b10_backoff_shape.sh": "local-ok",
    "tools/pegasus/submit_certify.sh": "local-ok",
    "tools/pegasus/submit_floor.sh": "local-ok",
    "tools/pegasus/submit_floor_pair.sh": "local-ok",
    "tools/pegasus/submit_mocc_trace.sh": "local-ok",
    "tools/pegasus/submit_oracle_n_pilot.sh": "local-ok",
    "tools/pegasus/submit_paper_story_a2_certification.sh": "local-ok",
    "tools/pegasus/submit_silo_ladder_rung1.sh": "local-ok",
    "tools/pegasus/submit_t126_qualification.sh": "unknown",
    "tools/pegasus/submit_t1998_balanced_stock_inline.sh": "local-ok",
    "tools/pegasus/submit_t2417_backoff_policy_performance.sh": "local-ok",
    "tools/pegasus/t126_qualification.sh": "dispatch-required",
    "tools/pegasus/t139_a12_stress_check.pbs": "dispatch-required",
    "tools/pegasus/t141_region_profile.sh": "dispatch-required",
    "tools/pegasus/t810_budget.py": "unknown",
    "tools/pegasus/t810_coordinator.py": "unknown",
    "tools/pegasus/t810_guard.py": "unknown",
    "tools/pegasus/t810_harness_schema.py": "unknown",
    "tools/pegasus/t810_pbs_wrapper.py": "unknown",
    "tools/pegasus/t810_runner_policy.py": "unknown",
    "tools/pegasus/validate_t810.py": "unknown",
}
_PEGASUS_EXPECTED_ENTRIES = {
    "tools/claude_session_ledger.py": {
        "class": "unknown",
        "reason": "inputs are hard-capped; isolated-scope and cap-boundary measurements are unavailable",
        "primary_gate": "hook deny pending isolated-scope admission evidence",
        "evidence": "compute-node shared-service cgroup delta sampling at commit 04d85f93 (not runbook 7.0 isolated-scope evidence; non-certifying); default --json argv, 25 of 1045 files read, 4728545 bytes, limit_reached; 5 positive-delta samples of 6, all command rc=2; max +19.7 MiB, +128 MiB margin = 147.7 MiB"
    },
    "tools/pegasus/a5_second_boot_backoff_sweep.sh": {
        "class": "dispatch-required",
        "reason": "PBS A-5 second-boot backoff sweep measurement job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/acceptance_nproc_study.sh": {
        "class": "dispatch-required",
        "reason": "PBS acceptance nproc measurement job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/b10_backoff_grid.sh": {
        "class": "dispatch-required",
        "reason": "PBS B-10 extended backoff measurement job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/b10_backoff_shape_campaign.sh": {
        "class": "dispatch-required",
        "reason": "PBS B10 backoff-shape measurement campaign job body",
        "primary_gate": "PBS allocation and job-body compute-host preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/certify_calibration.sh": {
        "class": "dispatch-required",
        "reason": "PBS calibration job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/collect_receipt.py": {
        "class": "unknown",
        "reason": "input caps and capped-input measurement are incomplete",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured; unbounded input surfaces remain"
    },
    "tools/pegasus/collect_t126_qualification.py": {
        "class": "unknown",
        "reason": "input caps and capped-input measurement are incomplete",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured; unbounded input surfaces remain"
    },
    "tools/pegasus/dispatch_compute.py": {
        "class": "local-ok",
        "reason": "login-side compute dispatcher with a self-gated job mode",
        "primary_gate": "dispatch_compute --job-run site gate",
        "evidence": "legacy-admitted (未実測)"
    },
    "tools/pegasus/exec_calibrate.py": {
        "class": "dispatch-required",
        "reason": "arbitrary exec trampoline used inside compute jobs",
        "primary_gate": "compute allocation owned by the caller",
        "evidence": "static arbitrary-exec classification"
    },
    "tools/pegasus/fetch_third_party.py": {
        "class": "local-ok",
        "reason": "login-side third-party acquisition workflow",
        "primary_gate": "fetch_third_party CLI validation",
        "evidence": "runbook §7.0 実測"
    },
    "tools/pegasus/floor_campaign.sh": {
        "class": "dispatch-required",
        "reason": "PBS floor campaign job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/floor_pair_campaign.sh": {
        "class": "dispatch-required",
        "reason": "PBS floor-pair window and finalize job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/floor_scoping.sh": {
        "class": "dispatch-required",
        "reason": "PBS floor scoping job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/generate_floor_masstree_payload_policy.py": {
        "class": "unknown",
        "reason": "input caps and capped-input measurement are incomplete",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured; unbounded input surfaces remain"
    },
    "tools/pegasus/make_acquisition_receipt.py": {
        "class": "dispatch-required",
        "reason": "receipt helper invoked from the calibration compute job",
        "primary_gate": "compute allocation owned by certify_calibration.sh",
        "evidence": "static compute-side call-site classification"
    },
    "tools/pegasus/mocc_trace_pilot.sh": {
        "class": "dispatch-required",
        "reason": "PBS Mocc trace pilot job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/oracle_n_pilot.sh": {
        "class": "dispatch-required",
        "reason": "PBS oracle n pilot job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/p3_s4_loop_pegasus.sh": {
        "class": "dispatch-required",
        "reason": "PBS P3 stage 4 loop build, verification, and benchmark job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/paper_story_a1_paired.sh": {
        "class": "dispatch-required",
        "reason": "PBS paper-story A-1 paired measurement job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/paper_story_a2_certification.sh": {
        "class": "dispatch-required",
        "reason": "PBS paper-story A-2/A-6 policy-selected certification job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs": {
        "class": "dispatch-required",
        "reason": "PBS T-1259 qsub environment delivery observation job body",
        "primary_gate": "PBS allocation and job-body compute-host, repository, and scratch-path validation",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/probes/t1259_qsub_env_delivery_probe.py": {
        "class": "dispatch-required",
        "reason": "compute-side T-1259 qsub environment delivery and official CLI refusal observer",
        "primary_gate": "compute allocation owned by t1259_qsub_env_delivery_probe.pbs",
        "evidence": "static compute-side call-site classification"
    },
    "tools/pegasus/probes/t139_positive_control_probe.pbs": {
        "class": "unknown",
        "reason": "probe artifact has no login admission ruling",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured probe artifact"
    },
    "tools/pegasus/probes/t139_positive_control_probe.sh": {
        "class": "unknown",
        "reason": "probe artifact has no login admission ruling",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured probe artifact"
    },
    "tools/pegasus/probes/t139_r4_env_probe.pbs": {
        "class": "dispatch-required",
        "reason": "gen_S environment-probe PBS job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/probes/t139_r4_env_probe.py": {
        "class": "dispatch-required",
        "reason": "compute-side benchmark/window sampler",
        "primary_gate": "compute allocation owned by t139_r4_env_probe.pbs",
        "evidence": "static compute-side call-site classification"
    },
    "tools/pegasus/probes/t139_r4_env_probe.sh": {
        "class": "dispatch-required",
        "reason": "compute-side CCBench build and measurement driver",
        "primary_gate": "compute allocation owned by t139_r4_env_probe.pbs",
        "evidence": "static compute-side call-site classification"
    },
    "tools/pegasus/probes/t1403_walltime_sigterm_probe.pbs": {
        "class": "unknown",
        "reason": "probe artifact has no login admission ruling",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured probe artifact"
    },
    "tools/pegasus/probes/t1403_walltime_sigterm_probe.py": {
        "class": "unknown",
        "reason": "probe artifact has no login admission ruling",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured probe artifact"
    },
    "tools/pegasus/probes/t1683_rr5_cost_probe.pbs": {
        "class": "dispatch-required",
        "reason": "PBS rr5 full-scale trace and verifier cost measurement job body",
        "primary_gate": "PBS allocation and job-body compute-host validation",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/probes/t1683_rr5_cost_probe.py": {
        "class": "dispatch-required",
        "reason": "compute-side rr5 full-scale trace and verifier cost measurement driver",
        "primary_gate": "compute allocation owned by t1683_rr5_cost_probe.pbs",
        "evidence": "static compute-side call-site classification"
    },
    "tools/pegasus/probes/t2187_adaptive_const_probe.pbs": {
        "class": "dispatch-required",
        "reason": "PBS Cicada adaptive-backoff performance measurement and correctness certification job body",
        "primary_gate": "PBS allocation and job-body compute-host validation",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/probes/t2187_adaptive_const_probe.py": {
        "class": "dispatch-required",
        "reason": "compute-side Cicada adaptive-backoff performance measurement and correctness certification driver",
        "primary_gate": "compute allocation owned by t2187_adaptive_const_probe.pbs",
        "evidence": "static compute-side call-site classification"
    },
    "tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs": {
        "class": "dispatch-required",
        "reason": "PBS T-2228 condition-meaning-gate driver liveness measurement job body",
        "primary_gate": "PBS allocation and job-body compute-host, repository, log-path, and evidence-path validation",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/probes/t2228_driver_gate_liveness_probe.py": {
        "class": "dispatch-required",
        "reason": "compute-side T-2228 condition-meaning-gate liveness measurement driver",
        "primary_gate": "compute allocation owned by t2228_driver_gate_liveness_probe.pbs",
        "evidence": "static compute-side call-site classification"
    },
    "tools/pegasus/probes/t293_perf_site_probe.pbs": {
        "class": "unknown",
        "reason": "probe artifact has no login admission ruling",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured probe artifact"
    },
    "tools/pegasus/probes/t293_perf_site_probe.py": {
        "class": "unknown",
        "reason": "probe artifact has no login admission ruling",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured probe artifact"
    },
    "tools/pegasus/probes/t316_sandbox_backend_probe.pbs": {
        "class": "dispatch-required",
        "reason": "gen_S sandbox-backend measurement PBS job body",
        "primary_gate": "PBS allocation and job-body environment validation",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/probes/t316_sandbox_backend_probe.py": {
        "class": "dispatch-required",
        "reason": "compute-side sandbox and performance measurement probe",
        "primary_gate": "PBS_JOBID and compute allocation owned by t316_sandbox_backend_probe.pbs",
        "evidence": "static compute-side call-site classification"
    },
    "tools/pegasus/probes/t419_probe_causality.pbs": {
        "class": "unknown",
        "reason": "probe artifact has no login admission ruling",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured probe artifact"
    },
    "tools/pegasus/probes/t419_probe_causality.py": {
        "class": "unknown",
        "reason": "probe artifact has no login admission ruling",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured probe artifact"
    },
    "tools/pegasus/probes/t503_restore_durability_probe.pbs": {
        "class": "unknown",
        "reason": "probe artifact has no login admission ruling",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured probe artifact"
    },
    "tools/pegasus/probes/t503_restore_durability_probe.py": {
        "class": "unknown",
        "reason": "probe artifact has no login admission ruling",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured probe artifact"
    },
    "tools/pegasus/probes/t503_restore_durability_recover.pbs": {
        "class": "unknown",
        "reason": "probe artifact has no login admission ruling",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured probe artifact"
    },
    "tools/pegasus/probes/t503_restore_durability_verdict.pbs": {
        "class": "unknown",
        "reason": "probe artifact has no login admission ruling",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured probe artifact"
    },
    "tools/pegasus/run_acceptance_nproc_study.py": {
        "class": "dispatch-required",
        "reason": "compute-side acceptance shard nproc measurement driver",
        "primary_gate": "compute allocation owned by acceptance_nproc_study.sh",
        "evidence": "static compute-side call-site classification"
    },
    "tools/pegasus/run_probe.py": {
      "class": "dispatch-required",
      "reason": "probe semantics require a compute allocation",
      "primary_gate": "compute-node environment attestation",
      "evidence": "static semantic-site classification"
    },
    "tools/pegasus/run_ss2pl_lock_study.py": {
        "class": "dispatch-required",
        "reason": "compute-side CCBench build and SS2PL benchmark driver",
        "primary_gate": "compute allocation owned by ss2pl_lock_study.sh",
        "evidence": "static compute-side call-site classification"
    },
    "tools/pegasus/run_t139_a12_stress_check.py": {
      "class": "dispatch-required",
      "reason": "compute-side T139 A12 stress-check simulation runner",
      "primary_gate": "compute allocation owned by t139_a12_stress_check.pbs",
      "evidence": "compute-node full run: 48 workers / 5.32 seconds; tens of MB per worker"
    },
    "tools/pegasus/silo_ladder_rung1.sh": {
        "class": "dispatch-required",
        "reason": "PBS silo ladder job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/smoke_probe.sh": {
      "class": "dispatch-required",
      "reason": "PBS smoke probe job body",
      "primary_gate": "PBS allocation and job-body site preflight",
      "evidence": "static job-body classification"
    },
    "tools/pegasus/ss2pl_lock_study.sh": {
        "class": "dispatch-required",
        "reason": "PBS SS2PL lock study job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/submit_a5_second_boot_backoff_sweep.sh": {
      "class": "local-ok",
      "reason": "login-side PBS A-5 two-workload fan-out submitter",
      "primary_gate": "qsub submission; compute work stays in independent job bodies",
      "evidence": "static login-side submitter classification"
    },
    "tools/pegasus/submit_b10_backoff_grid.sh": {
      "class": "local-ok",
      "reason": "login-side PBS B-10 three-workload submitter",
      "primary_gate": "qsub submission; compute work stays in independent job bodies",
      "evidence": "static login-side submitter classification"
    },
    "tools/pegasus/submit_b10_backoff_shape.sh": {
      "class": "local-ok",
      "reason": "login-side PBS B10 backoff-shape campaign submitter",
      "primary_gate": "qsub submission; compute work stays in job body",
      "evidence": "static login-side submitter classification"
    },
    "tools/pegasus/submit_certify.sh": {
      "class": "local-ok",
      "reason": "login-side PBS certification submitter",
      "primary_gate": "qsub submission; compute work stays in job body",
      "evidence": "legacy-admitted (未実測)"
    },
    "tools/pegasus/submit_floor.sh": {
        "class": "local-ok",
        "reason": "login-side PBS floor submitter",
        "primary_gate": "qsub submission; compute work stays in job body",
        "evidence": "legacy-admitted (未実測)"
    },
    "tools/pegasus/submit_floor_pair.sh": {
        "class": "local-ok",
        "reason": "login-side PBS floor-pair submitter",
        "primary_gate": "qsub submission; compute work stays in job body",
        "evidence": "static login-side submitter classification"
    },
    "tools/pegasus/submit_mocc_trace.sh": {
        "class": "local-ok",
        "reason": "login-side PBS Mocc trace pilot submitter",
        "primary_gate": "qsub submission; compute work stays in job body",
        "evidence": "static login-side submitter classification"
    },
    "tools/pegasus/submit_oracle_n_pilot.sh": {
      "class": "local-ok",
      "reason": "login-side PBS oracle n pilot submitter",
      "primary_gate": "qsub submission; compute work stays in job body",
      "evidence": "login-side submitter; compute work stays in job body (未実測)"
    },
    "tools/pegasus/submit_paper_story_a2_certification.sh": {
      "class": "local-ok",
      "reason": "login-side PBS paper-story A-2/A-6 policy-selected submitter and finisher",
      "primary_gate": "policy-scoped precheck then qsub fan-out; compute work stays in independent job bodies",
      "evidence": "static login-side submitter classification"
    },
    "tools/pegasus/submit_silo_ladder_rung1.sh": {
        "class": "local-ok",
        "reason": "login-side PBS silo ladder submitter",
        "primary_gate": "qsub submission; compute work stays in job body",
        "evidence": "legacy-admitted (未実測)"
    },
    "tools/pegasus/submit_t126_qualification.sh": {
        "class": "unknown",
        "reason": "input caps and capped-input measurement are incomplete",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured; preflight input surfaces remain"
    },
    "tools/pegasus/submit_t1998_balanced_stock_inline.sh": {
      "class": "local-ok",
      "reason": "login-side PBS T-1998 balanced-only submitter",
      "primary_gate": "qsub submission; compute work stays in existing A-5 job body",
      "evidence": "static login-side submitter classification"
    },
    "tools/pegasus/submit_t2417_backoff_policy_performance.sh": {
      "class": "local-ok",
      "reason": "login-side PBS T-2417 policy-arm performance submitter",
      "primary_gate": "qsub submission; compute work stays in job body",
      "evidence": "static login-side submitter classification"
    },
    "tools/pegasus/t126_qualification.sh": {
        "class": "dispatch-required",
        "reason": "PBS T126 qualification job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/t139_a12_stress_check.pbs": {
        "class": "dispatch-required",
        "reason": "PBS T139 A12 stress-check job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/t141_region_profile.sh": {
        "class": "dispatch-required",
        "reason": "PBS T141 profiling job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification"
    },
    "tools/pegasus/t810_budget.py": {
        "class": "unknown",
        "reason": "input caps and capped-input measurement are incomplete",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured; unbounded input surfaces remain"
    },
    "tools/pegasus/t810_coordinator.py": {
        "class": "unknown",
        "reason": "input caps and capped-input measurement are incomplete",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured; unbounded input surfaces remain"
    },
    "tools/pegasus/t810_guard.py": {
        "class": "unknown",
        "reason": "input caps and capped-input measurement are incomplete",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured; unbounded input surfaces remain"
    },
    "tools/pegasus/t810_harness_schema.py": {
        "class": "unknown",
        "reason": "input caps and capped-input measurement are incomplete",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured; unbounded input surfaces remain"
    },
    "tools/pegasus/t810_pbs_wrapper.py": {
        "class": "unknown",
        "reason": "input caps and capped-input measurement are incomplete",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured; unbounded input surfaces remain"
    },
    "tools/pegasus/t810_runner_policy.py": {
        "class": "unknown",
        "reason": "input caps and capped-input measurement are incomplete",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured; unbounded input surfaces remain"
    },
    "tools/pegasus/validate_t810.py": {
        "class": "unknown",
        "reason": "input caps and capped-input measurement are incomplete",
        "primary_gate": "hook deny pending admission evidence",
        "evidence": "unmeasured; unbounded input surfaces remain"
    }
}

_PEGASUS_DIRECT_COMMANDS = {
    path: f"python3 {path}" if path.endswith(".py") else path
    for path in _PEGASUS_EXPECTED_CLASSES
}

_PEGASUS_REGISTRY_FAILURES = (
    "json-missing",
    "json-empty",
    "json-invalid",
    "json-duplicate-key",
    "json-wrong-type",
    "json-unknown-class",
    "json-bom",
    "json-schema-version",
    "loader-missing",
    "loader-system-exit",
    "loader-none",
    "loader-list",
    "loader-scalar-entry",
    "loader-raising-mapping",
    "loader-outside-local-ok",
    "loader-missing-field",
    "loader-extra-field",
    "loader-empty-field",
    "loader-unknown-class",
)

_LOCAL_OK_NORMALIZED_SPELLINGS = (
    ("dispatch-dot", "./tools/pegasus/dispatch_compute.py", True),
    ("dispatch-double", "tools//pegasus/dispatch_compute.py", True),
    ("dispatch-trailing-slash",
     "tools/pegasus/dispatch_compute.py/", True),
    ("dispatch-absolute",
     f"{_REPO}/tools/pegasus/dispatch_compute.py", True),
    ("dispatch-python",
     "python3 tools/pegasus/dispatch_compute.py", True),
    ("fetch-dot", "./tools/pegasus/fetch_third_party.py", True),
    ("fetch-double", "tools//pegasus/fetch_third_party.py", True),
    ("fetch-trailing-slash", "tools/pegasus/fetch_third_party.py/", True),
    ("fetch-absolute",
     f"{_REPO}/tools/pegasus/fetch_third_party.py", True),
    ("fetch-python",
     "python3 tools/pegasus/fetch_third_party.py", True),
    ("certify-dot", "./tools/pegasus/submit_certify.sh", True),
    ("certify-double", "tools//pegasus/submit_certify.sh", True),
    ("certify-trailing-slash", "tools/pegasus/submit_certify.sh/", True),
    ("certify-absolute",
     f"{_REPO}/tools/pegasus/submit_certify.sh", True),
    ("certify-bash", "bash tools/pegasus/submit_certify.sh", True),
    ("floor-dot", "./tools/pegasus/submit_floor.sh", True),
    ("floor-double", "tools//pegasus/submit_floor.sh", True),
    ("floor-trailing-slash", "tools/pegasus/submit_floor.sh/", True),
    ("floor-absolute", f"{_REPO}/tools/pegasus/submit_floor.sh", True),
    ("floor-bash", "bash tools/pegasus/submit_floor.sh", True),
    ("silo-dot", "./tools/pegasus/submit_silo_ladder_rung1.sh", True),
    ("silo-double", "tools//pegasus/submit_silo_ladder_rung1.sh", True),
    ("silo-trailing-slash",
     "tools/pegasus/submit_silo_ladder_rung1.sh/", True),
    ("silo-absolute",
     f"{_REPO}/tools/pegasus/submit_silo_ladder_rung1.sh", True),
    ("silo-bash",
     "bash tools/pegasus/submit_silo_ladder_rung1.sh", True),
)


def _canonical_registry_bytes(document):
    return (json.dumps(
        document, ensure_ascii=False, indent=2, allow_nan=False
    ) + "\n").encode("utf-8")


_SYNTHETIC_VALID_ENTRY = {
    "class": "local-ok",
    "reason": "synthetic valid reason",
    "primary_gate": "synthetic valid gate",
    "evidence": "synthetic valid evidence",
}


def _synthetic_registry_document(
        path="tools/pegasus/dispatch_compute.py", entry=None):
    return {
        "schema_version": "pegasus-admission-registry/v1",
        "entries": {path: dict(entry or _SYNTHETIC_VALID_ENTRY)},
    }


def _negative_registry_bytes(case):
    document = _synthetic_registry_document()
    path = next(iter(document["entries"]))
    entry = document["entries"][path]

    if case == "root-order":
        document = {
            "entries": document["entries"],
            "schema_version": document["schema_version"],
        }
    elif case == "path-order":
        document["entries"] = {
            "tools/pegasus/fetch_third_party.py": dict(entry),
            "tools/pegasus/dispatch_compute.py": dict(entry),
        }
    elif case == "field-order":
        document["entries"][path] = {
            "reason": entry["reason"],
            "class": entry["class"],
            "primary_gate": entry["primary_gate"],
            "evidence": entry["evidence"],
        }
    elif case == "four-space-indent":
        return (json.dumps(
            document, ensure_ascii=False, indent=4, allow_nan=False
        ) + "\n").encode("utf-8")
    elif case == "missing-final-newline":
        return _canonical_registry_bytes(document)[:-1]
    elif case == "extra-final-newline":
        return _canonical_registry_bytes(document) + b"\n"
    elif case == "empty-entries":
        document["entries"] = {}
    elif case in {
            "outside-path", "absolute-path", "parent-path", "double-slash",
            "nul-path", "control-path"}:
        replacement = {
            "outside-path": "tools/not-pegasus/dispatch_compute.py",
            "absolute-path": "/tools/pegasus/dispatch_compute.py",
            "parent-path": "tools/pegasus/../dispatch_compute.py",
            "double-slash": "tools/pegasus//dispatch_compute.py",
            "nul-path": "tools/pegasus/bad\x00.py",
            "control-path": "tools/pegasus/bad\x1f.py",
        }[case]
        document["entries"] = {replacement: entry}
    elif case == "missing-field":
        entry.pop("evidence")
    elif case == "extra-field":
        entry["extra"] = "unexpected"
    elif case == "empty-field":
        entry["evidence"] = ""
    else:
        raise AssertionError(f"unknown negative registry case: {case}")
    return _canonical_registry_bytes(document)


_NEGATIVE_REGISTRY_CASES = (
    "root-order",
    "path-order",
    "field-order",
    "four-space-indent",
    "missing-final-newline",
    "extra-final-newline",
    "empty-entries",
    "outside-path",
    "absolute-path",
    "parent-path",
    "double-slash",
    "missing-field",
    "extra-field",
    "empty-field",
    "nul-path",
    "control-path",
)


def _registry_bytes_for_failure(failure):
    source = os.path.join(
        _REPO, "tools", "pegasus", "admission_registry.json")
    with open(source, "rb") as stream:
        healthy = stream.read()
    if failure == "json-empty":
        return b""
    if failure == "json-invalid":
        return b"{"
    if failure == "json-duplicate-key":
        line = b'  "schema_version": "pegasus-admission-registry/v1",\n'
        return healthy.replace(line, line + line, 1)
    if failure == "json-bom":
        return b"\xef\xbb\xbf" + healthy

    document = json.loads(healthy)
    if failure == "json-wrong-type":
        document["entries"] = []
    elif failure == "json-one-entry":
        entry = document["entries"]["tools/pegasus/dispatch_compute.py"]
        document["entries"] = {
            "tools/pegasus/dispatch_compute.py": entry,
        }
    elif failure == "json-unknown-class":
        document["entries"]["tools/pegasus/dispatch_compute.py"]["class"] = \
            "future-class"
    elif failure == "json-schema-version":
        document["schema_version"] = "pegasus-admission-registry/v0"
    else:
        raise AssertionError(f"unknown JSON failure fixture: {failure}")
    return _canonical_registry_bytes(document)


_LOADER_FIXTURE_SOURCES = {
    "loader-top-level-system-exit": "raise SystemExit(0)\n",
    "loader-top-level-keyboard-interrupt": "raise KeyboardInterrupt()\n",
    "loader-system-exit": (
        "def load_admission_registry(repo_root):\n"
        "    raise SystemExit(0)\n"
    ),
    "loader-keyboard-interrupt": (
        "def load_admission_registry(repo_root):\n"
        "    raise KeyboardInterrupt()\n"
    ),
    "loader-none": (
        "def load_admission_registry(repo_root):\n"
        "    return None\n"
    ),
    "loader-list": (
        "def load_admission_registry(repo_root):\n"
        "    return []\n"
    ),
    "loader-empty": (
        "def load_admission_registry(repo_root):\n"
        "    return {}\n"
    ),
    "loader-scalar-entry": (
        "def load_admission_registry(repo_root):\n"
        "    return {'tools/pegasus/dispatch_compute.py': 1}\n"
    ),
    "loader-raising-mapping": (
        "class RaisingMapping(dict):\n"
        "    def items(self):\n"
        "        raise RuntimeError('broken mapping')\n"
        "def load_admission_registry(repo_root):\n"
        "    return RaisingMapping()\n"
    ),
    "loader-entry-getitem": (
        "class RaisingEntry(dict):\n"
        "    def __getitem__(self, key):\n"
        "        raise RuntimeError('broken entry getitem')\n"
        "def load_admission_registry(repo_root):\n"
        "    return {'tools/pegasus/dispatch_compute.py': RaisingEntry({\n"
        "        'class': 'local-ok', 'reason': 'r',\n"
        "        'primary_gate': 'g', 'evidence': 'e'})}\n"
    ),
    "loader-sanctioned-derivation": (
        "import builtins\n"
        "def load_admission_registry(repo_root):\n"
        "    original_frozenset = builtins.frozenset\n"
        "    def raising_frozenset(*args, **kwargs):\n"
        "        builtins.frozenset = original_frozenset\n"
        "        raise RuntimeError('broken sanctioned derivation')\n"
        "    builtins.frozenset = raising_frozenset\n"
        "    return {'tools/pegasus/dispatch_compute.py': {\n"
        "        'class': 'local-ok', 'reason': 'r',\n"
        "        'primary_gate': 'g', 'evidence': 'e'}}\n"
    ),
    "loader-cleanup-system-exit": (
        "import sys\n"
        "class RaisingModules:\n"
        "    def pop(self, *args, **kwargs):\n"
        "        raise RuntimeError('cleanup trap')\n"
        "sys.modules = RaisingModules()\n"
        "raise SystemExit(0)\n"
    ),
    "loader-outside-local-ok": (
        "def load_admission_registry(repo_root):\n"
        "    return {'pytest': {'class': 'local-ok', 'reason': 'r',\n"
        "        'primary_gate': 'g', 'evidence': 'e'}}\n"
    ),
    "loader-sanctioned-non-local": (
        "def load_admission_registry(repo_root):\n"
        "    return {'tools/run_tests.py': {'class': 'unknown',\n"
        "        'reason': 'r', 'primary_gate': 'g', 'evidence': 'e'}}\n"
    ),
    "loader-missing-field": (
        "def load_admission_registry(repo_root):\n"
        "    return {'tools/pegasus/dispatch_compute.py': {\n"
        "        'class': 'local-ok', 'reason': 'r', 'primary_gate': 'g'}}\n"
    ),
    "loader-extra-field": (
        "def load_admission_registry(repo_root):\n"
        "    return {'tools/pegasus/dispatch_compute.py': {\n"
        "        'class': 'local-ok', 'reason': 'r', 'primary_gate': 'g',\n"
        "        'evidence': 'e', 'extra': 'x'}}\n"
    ),
    "loader-empty-field": (
        "def load_admission_registry(repo_root):\n"
        "    return {'tools/pegasus/dispatch_compute.py': {\n"
        "        'class': 'local-ok', 'reason': '', 'primary_gate': 'g',\n"
        "        'evidence': 'e'}}\n"
    ),
    "loader-unknown-class": (
        "def load_admission_registry(repo_root):\n"
        "    return {'tools/pegasus/dispatch_compute.py': {\n"
        "        'class': 'future', 'reason': 'r', 'primary_gate': 'g',\n"
        "        'evidence': 'e'}}\n"
    ),
}


def _prepare_guard_fixture(tmp_path, failure):
    hooks = tmp_path / "hooks"
    tools = tmp_path / "tools"
    registry_dir = tools / "pegasus"
    hooks.mkdir()
    registry_dir.mkdir(parents=True)
    shutil.copyfile(
        os.path.join(_REPO, "hooks", "guard_bash.py"),
        hooks / "guard_bash.py",
    )

    loader = tools / "pegasus_admission_registry.py"
    if failure in _LOADER_FIXTURE_SOURCES:
        loader.write_text(_LOADER_FIXTURE_SOURCES[failure], encoding="utf-8")
    elif failure != "loader-missing":
        shutil.copyfile(
            os.path.join(_REPO, "tools", "pegasus_admission_registry.py"),
            loader,
        )

    if (failure != "json-missing" and failure != "loader-missing"
            and failure not in _LOADER_FIXTURE_SOURCES):
        (registry_dir / "admission_registry.json").write_bytes(
            _registry_bytes_for_failure(failure))
    return hooks / "guard_bash.py"


def _install_login_site_policy(tmp_path):
    campaign = tmp_path / "orchestrator" / "campaign"
    campaign.mkdir(parents=True)
    (tmp_path / "orchestrator" / "__init__.py").write_text(
        "", encoding="utf-8")
    (campaign / "__init__.py").write_text("", encoding="utf-8")
    (campaign / "site_policy.py").write_text(
        "import re\n"
        "LOGIN_FALLBACK_RE = re.compile(r'^pegasus0[1-9]$')\n"
        "PEGASUS_LOGIN = 'PEGASUS_LOGIN'\n"
        "def current_site():\n"
        "    return PEGASUS_LOGIN\n"
        "def refuses_heavy_work(site):\n"
        "    return site == PEGASUS_LOGIN\n"
        "def heavy_work_refusal(site, what):\n"
        "    return what\n",
        encoding="utf-8",
    )


def _run_guard_subprocess(
        hook, tmp_path,
        command="python3 tools/pegasus/dispatch_compute.py --help",
        timeout=3):
    _install_login_site_policy(tmp_path)
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
    })
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(hook)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
        timeout=timeout,
    )


def _load_guard_fixture(tmp_path, failure):
    path = _prepare_guard_fixture(tmp_path, failure)
    module_name = f"_guard_bash_admission_failure_{failure.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    previous_dont_write_bytecode = sys.dont_write_bytecode
    try:
        spec.loader.exec_module(module)
    finally:
        assert sys.dont_write_bytecode is previous_dont_write_bytecode
        while str(tmp_path) in sys.path:
            sys.path.remove(str(tmp_path))
    assert not (tmp_path / "tools" / "__pycache__").exists(), \
        "loader exact-path import が __pycache__ を書いた"
    return module


def _assert_failed_registry_is_closed(module):
    assert module._PEGASUS_ADMISSION_REGISTRY == {}
    assert module._PEGASUS_ADMISSION_DIAGNOSTIC
    assert module._SANCTIONED_PATHS == {
        "tools/run_tests.py", "tools/check_ai_provenance.py"}
    for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
        for path, command in _PEGASUS_DIRECT_COMMANDS.items():
            ok, why = module.decide(command, site=site)
            assert not ok, \
                f"{site} の registry 異常時に Pegasus direct が通った: {path} ({why})"
        for command in (
            "python3 tools/run_tests.py orchestrator/tests/test_hooks.py -q",
            "python3 tools/check_ai_provenance.py --range A..B",
        ):
            ok, why = module.decide(command, site=site)
            assert ok, \
                f"{site} の registry 異常が非 Pegasus sanctioned を落とした: {why}"


def test_bash_pegasus_registry_schema_and_fixed_classes():
    assert GB._PEGASUS_ADMISSION_REGISTRY == _PEGASUS_EXPECTED_ENTRIES, \
        "admission registry の entry × 4 field が literal golden と不一致"
    assert set(GB._PEGASUS_ADMISSION_REGISTRY) == set(_PEGASUS_EXPECTED_CLASSES)
    for path, expected_class in _PEGASUS_EXPECTED_CLASSES.items():
        entry = GB._PEGASUS_ADMISSION_REGISTRY[path]
        assert set(entry) == {"class", "reason", "primary_gate", "evidence"}
        assert entry["class"] == expected_class, \
            f"Pegasus class が固定期待値から変化した: {path}"
        for field in ("reason", "primary_gate", "evidence"):
            assert isinstance(entry[field], str) and entry[field], \
                f"Pegasus admission の {field} が空: {path}"

    expected_local_evidence = {
        "tools/pegasus/dispatch_compute.py": "legacy-admitted (未実測)",
        "tools/pegasus/fetch_third_party.py": "runbook §7.0 実測",
        "tools/pegasus/submit_a5_second_boot_backoff_sweep.sh":
            "static login-side submitter classification",
        "tools/pegasus/submit_t1998_balanced_stock_inline.sh":
            "static login-side submitter classification",
        "tools/pegasus/submit_b10_backoff_grid.sh":
            "static login-side submitter classification",
        "tools/pegasus/submit_b10_backoff_shape.sh":
            "static login-side submitter classification",
        "tools/pegasus/submit_certify.sh": "legacy-admitted (未実測)",
        "tools/pegasus/submit_floor.sh": "legacy-admitted (未実測)",
        "tools/pegasus/submit_floor_pair.sh": "static login-side submitter classification",
        "tools/pegasus/submit_mocc_trace.sh": "static login-side submitter classification",
        "tools/pegasus/submit_oracle_n_pilot.sh":
            "login-side submitter; compute work stays in job body (未実測)",
        "tools/pegasus/submit_paper_story_a2_certification.sh":
            "static login-side submitter classification",
        "tools/pegasus/submit_silo_ladder_rung1.sh":
            "legacy-admitted (未実測)",
        "tools/pegasus/submit_t2417_backoff_policy_performance.sh":
            "static login-side submitter classification",
    }
    actual = {
        path: entry["evidence"]
        for path, entry in GB._PEGASUS_ADMISSION_REGISTRY.items()
        if entry["class"] == "local-ok"
    }
    assert actual == expected_local_evidence, \
        "local-ok の実測/legacy 証拠状態を偽ってはならない"


@pytest.mark.parametrize("failure", _PEGASUS_REGISTRY_FAILURES)
def test_bash_pegasus_registry_failures_close_all_direct_entries(
        tmp_path, failure):
    """registry/loader 異常は Pegasus direct だけを全拒否へ縮退させる。"""
    module = _load_guard_fixture(tmp_path, failure)
    _assert_failed_registry_is_closed(module)


def test_bash_pegasus_loader_accepts_nonempty_schema_without_exact_count(tmp_path):
    """production validator に healthy registry の exact 件数を持ち込ませない。"""
    module = _load_guard_fixture(tmp_path, "json-one-entry")
    assert module._PEGASUS_ADMISSION_REGISTRY == {
        "tools/pegasus/dispatch_compute.py": {
            "class": "local-ok",
            "reason": "login-side compute dispatcher with a self-gated job mode",
            "primary_gate": "dispatch_compute --job-run site gate",
            "evidence": "legacy-admitted (未実測)",
        },
    }
    assert module._PEGASUS_ADMISSION_DIAGNOSTIC == ""


def test_bash_pegasus_wrapper_rejects_empty_loader_registry(tmp_path):
    """wrapper も空 registry を diagnostic 付き縮退として拒否する。"""
    module = _load_guard_fixture(tmp_path, "loader-empty")
    _assert_failed_registry_is_closed(module)


@pytest.mark.parametrize("failure", (
    "loader-none",
    "loader-list",
    "loader-scalar-entry",
    "loader-raising-mapping",
    "loader-top-level-system-exit",
    "loader-top-level-keyboard-interrupt",
    "loader-system-exit",
    "loader-keyboard-interrupt",
    "loader-entry-getitem",
    "loader-sanctioned-derivation",
    "loader-cleanup-system-exit",
))
def test_bash_pegasus_loader_failures_are_denied_by_real_subprocess(
        tmp_path, failure):
    """module 初期化障害が hook rc=0 の fail-open にならない。"""
    hook = _prepare_guard_fixture(tmp_path, failure)
    result = _run_guard_subprocess(hook, tmp_path, timeout=3)
    assert result.returncode == 2, \
        f"{failure} で hook が fail-open: stderr={result.stderr[:200]}"


@pytest.mark.parametrize("failure", (
    "loader-outside-local-ok",
    "loader-missing-field",
    "loader-extra-field",
    "loader-empty-field",
    "loader-unknown-class",
))
def test_bash_pegasus_wrapper_postcondition_fails_closed_in_subprocess(
        tmp_path, failure):
    """loader が validator 契約を破っても wrapper 自身が再検証する。"""
    hook = _prepare_guard_fixture(tmp_path, failure)
    command = "pytest -q" if failure == "loader-outside-local-ok" else \
        "python3 tools/pegasus/dispatch_compute.py --help"
    result = _run_guard_subprocess(
        hook, tmp_path, command=command, timeout=3)
    assert result.returncode == 2, \
        f"{failure} が wrapper postcondition を迂回: {result.stderr[:200]}"


def test_pegasus_registry_loader_accepts_canonical_non_pegasus_path(tmp_path):
    registry_dir = tmp_path / "tools" / "pegasus"
    registry_dir.mkdir(parents=True)
    document = _synthetic_registry_document(
        path="tools/claude_session_ledger.py",
        entry={
            "class": "unknown",
            "reason": "r",
            "primary_gate": "g",
            "evidence": "e",
        },
    )
    (registry_dir / "admission_registry.json").write_bytes(
        _canonical_registry_bytes(document))
    assert PAR.load_admission_registry(tmp_path) == document["entries"]


def test_pegasus_registry_loader_rejects_non_pegasus_local_ok(tmp_path):
    registry_dir = tmp_path / "tools" / "pegasus"
    registry_dir.mkdir(parents=True)
    document = _synthetic_registry_document(path="tools/local_ok.py")
    (registry_dir / "admission_registry.json").write_bytes(
        _canonical_registry_bytes(document))
    with pytest.raises(PAR.AdmissionRegistryError):
        PAR.load_admission_registry(tmp_path)


def test_bash_pegasus_entry_lookup_rejects_registry_keys_outside_subtree():
    """非 Pegasus local-ok は admission allow に使わず deny sentinel にする。"""
    malicious = {
        "pytest": {
            "class": "local-ok",
            "reason": "r",
            "primary_gate": "g",
            "evidence": "e",
        },
    }
    with patch.object(GB, "_PEGASUS_ADMISSION_REGISTRY", malicious):
        assert GB._pegasus_admission_entry("pytest") is GB._PEGASUS_UNREGISTERED


def test_bash_non_pegasus_local_ok_corruption_cannot_borrow_sanctioned_allow():
    path = "pytest"
    malicious = {
        path: {
            "class": "local-ok",
            "reason": "r",
            "primary_gate": "g",
            "evidence": "e",
        },
    }
    with patch.object(GB, "_PEGASUS_ADMISSION_REGISTRY", malicious):
        with patch.object(GB, "_SANCTIONED_PATHS", GB._SANCTIONED_PATHS | {path}):
            for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
                ok, why = GB.decide("pytest -q", site=site)
                assert not ok, f"{site} で二重汚染 local-ok が通った"
                assert "未登録 admission 実行体" in why
            ok, why = GB.decide("pytest -q", site="OTHER")
            assert ok, f"OTHER を過剰拒否した: {why}"


@pytest.mark.parametrize("case", _NEGATIVE_REGISTRY_CASES)
def test_pegasus_registry_negative_corpus_is_rejected_by_loader(tmp_path, case):
    """canonical bytes・path・field schema の各独立条件を loader で固定する。"""
    registry_dir = tmp_path / "tools" / "pegasus"
    registry_dir.mkdir(parents=True)
    (registry_dir / "admission_registry.json").write_bytes(
        _negative_registry_bytes(case))
    with pytest.raises(PAR.AdmissionRegistryError):
        PAR.load_admission_registry(tmp_path)


@pytest.mark.parametrize("case", _NEGATIVE_REGISTRY_CASES)
def test_pegasus_registry_negative_corpus_closes_real_hook(tmp_path, case):
    """同じ negative corpus が production hook でも exact rc=2 になる。"""
    hook = _prepare_guard_fixture(tmp_path, "json-one-entry")
    registry = tmp_path / "tools" / "pegasus" / "admission_registry.json"
    registry.write_bytes(_negative_registry_bytes(case))
    result = _run_guard_subprocess(hook, tmp_path, timeout=3)
    assert result.returncode == 2, \
        f"{case} が実 hook で fail-open: {result.stderr[:200]}"


@pytest.mark.parametrize("kind", (
    "final-symlink",
    "directory",
    "oversize",
    "fifo-no-writer",
    "permission-denied",
))
def test_pegasus_registry_file_boundary_closes_real_hook(tmp_path, kind):
    """NOFOLLOW・regular・size cap・NONBLOCK・permission error を実 fd で固定する。"""
    hook = _prepare_guard_fixture(tmp_path, "json-one-entry")
    registry = tmp_path / "tools" / "pegasus" / "admission_registry.json"
    if kind == "final-symlink":
        target = tmp_path / "attacker-registry.json"
        target.write_bytes(_canonical_registry_bytes(
            _synthetic_registry_document()))
        registry.unlink()
        registry.symlink_to(target)
    elif kind == "directory":
        registry.unlink()
        registry.mkdir()
    elif kind == "oversize":
        document = _synthetic_registry_document()
        path = next(iter(document["entries"]))
        document["entries"][path]["evidence"] = "x" * (1024 * 1024)
        raw = _canonical_registry_bytes(document)
        assert len(raw) > 1024 * 1024
        registry.write_bytes(raw)
    elif kind == "fifo-no-writer":
        registry.unlink()
        os.mkfifo(registry)
    elif kind == "permission-denied":
        registry.chmod(0)
    else:
        raise AssertionError(kind)

    result = _run_guard_subprocess(hook, tmp_path, timeout=3)
    assert result.returncode == 2, \
        f"{kind} が実 hook で fail-open: {result.stderr[:200]}"


def test_pegasus_loader_regular_file_check_has_an_independent_detector(
        tmp_path):
    registry_dir = tmp_path / "tools" / "pegasus"
    registry_dir.mkdir(parents=True)
    raw = _canonical_registry_bytes(_synthetic_registry_document())
    (registry_dir / "admission_registry.json").write_bytes(raw)

    class DirectoryMetadata:
        st_mode = stat.S_IFDIR
        st_size = len(raw)

    with patch.object(PAR.os, "fstat", return_value=DirectoryMetadata()), \
            patch.object(PAR.os, "read", side_effect=(raw, b"")):
        with pytest.raises(PAR.AdmissionRegistryError):
            PAR.load_admission_registry(tmp_path)


def test_pegasus_loader_stat_size_cap_has_an_independent_detector(tmp_path):
    registry_dir = tmp_path / "tools" / "pegasus"
    registry_dir.mkdir(parents=True)
    raw = _canonical_registry_bytes(_synthetic_registry_document())
    (registry_dir / "admission_registry.json").write_bytes(raw)

    class OversizeMetadata:
        st_mode = stat.S_IFREG
        st_size = 1024 * 1024 + 1

    with patch.object(PAR.os, "fstat", return_value=OversizeMetadata()):
        with pytest.raises(PAR.AdmissionRegistryError):
            PAR.load_admission_registry(tmp_path)


def test_pegasus_loader_bounded_read_has_an_independent_detector(tmp_path):
    registry_dir = tmp_path / "tools" / "pegasus"
    registry_dir.mkdir(parents=True)
    path = registry_dir / "admission_registry.json"
    path.write_bytes(_canonical_registry_bytes(_synthetic_registry_document()))
    document = _synthetic_registry_document()
    entry_path = next(iter(document["entries"]))
    document["entries"][entry_path]["evidence"] = "x" * (1024 * 1024)
    oversize = _canonical_registry_bytes(document)
    assert len(oversize) > 1024 * 1024

    class SmallRegularMetadata:
        st_mode = stat.S_IFREG
        st_size = 1

    with patch.object(PAR.os, "fstat", return_value=SmallRegularMetadata()), \
            patch.object(PAR.os, "read", side_effect=(oversize, b"")):
        with pytest.raises(PAR.AdmissionRegistryError):
            PAR.load_admission_registry(tmp_path)


def test_pegasus_loader_cleanup_exception_is_normalized(tmp_path):
    registry_dir = tmp_path / "tools" / "pegasus"
    registry_dir.mkdir(parents=True)
    (registry_dir / "admission_registry.json").write_bytes(
        _canonical_registry_bytes(_synthetic_registry_document()))
    real_close = PAR.os.close

    def close_then_interrupt(descriptor):
        real_close(descriptor)
        raise KeyboardInterrupt()

    with patch.object(PAR.os, "close", side_effect=close_then_interrupt):
        with pytest.raises(PAR.AdmissionRegistryError):
            PAR.load_admission_registry(tmp_path)


def _synthetic_loader_source(classification):
    entry = dict(_SYNTHETIC_VALID_ENTRY)
    entry["class"] = classification
    return (
        "def load_admission_registry(repo_root):\n"
        f"    return {{'tools/pegasus/dispatch_compute.py': {entry!r}}}\n"
    )


def test_bash_pegasus_loader_executes_source_even_with_unchecked_stale_pyc(
        tmp_path):
    """unchecked pyc が local-ok でも、現 source の dispatch-required を採る。"""
    hook = _prepare_guard_fixture(tmp_path, "json-one-entry")
    loader = tmp_path / "tools" / "pegasus_admission_registry.py"
    loader.write_text(_synthetic_loader_source("local-ok"), encoding="utf-8")
    py_compile.compile(
        str(loader),
        doraise=True,
        invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
    )
    loader.write_text(
        _synthetic_loader_source("dispatch-required"), encoding="utf-8")

    result = _run_guard_subprocess(hook, tmp_path, timeout=3)
    assert result.returncode == 2, \
        f"unchecked stale pyc が source より優先された: {result.stderr[:200]}"


@pytest.mark.parametrize(
    "_label,command,expected",
    _LOCAL_OK_NORMALIZED_SPELLINGS,
    ids=[row[0] for row in _LOCAL_OK_NORMALIZED_SPELLINGS],
)
def test_bash_local_ok_normalized_spelling_bits_are_literal_golden(
        _label, command, expected):
    """変更前 local-ok 5本の正規化綴り acceptance bit を固定する。"""
    for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
        ok, why = GB.decide(command, site=site)
        assert ok is expected, \
            f"{site} の正規化綴り bit が変化した: {command!r} ({why})"


def test_bash_pegasus_registry_login_and_suspect_bits_are_pinned():
    for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
        for path, expected_class in _PEGASUS_EXPECTED_CLASSES.items():
            ok, why = GB.decide(_PEGASUS_DIRECT_COMMANDS[path], site=site)
            expected = expected_class == "local-ok"
            assert ok is expected, \
                f"{site} の受理 bit が不正: {path}: {ok} ({why})"


def test_bash_other_and_compute_keep_all_pegasus_entry_bits():
    for site in ("OTHER", "PEGASUS_COMPUTE"):
        for path, command in _PEGASUS_DIRECT_COMMANDS.items():
            ok, why = GB.decide(command, site=site)
            assert ok, f"{site} の既存 ALLOW bit が変化した: {path} ({why})"


def test_bash_registered_non_pegasus_unknown_site_matrix():
    command = "python3 tools/claude_session_ledger.py --scan"
    for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
        ok, why = GB.decide(command, site=site)
        assert not ok, f"{site} で登録済み非 Pegasus unknown が通った"
        assert "admission unknown 実行体" in why
    for site in ("OTHER", "PEGASUS_COMPUTE"):
        ok, why = GB.decide(command, site=site)
        assert ok, f"{site} の既存 allow が縮んだ: {why}"


def test_bash_unregistered_non_pegasus_path_remains_allowed():
    command = "python3 tools/unregistered_for_admission.py"
    for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT", "OTHER", "PEGASUS_COMPUTE"):
        ok, why = GB.decide(command, site=site)
        assert ok, f"{site} で未登録非 Pegasus path が過剰拒否された: {why}"


def test_bash_non_pegasus_fallback_set_matches_registry_projection():
    expected = {
        path for path in GB._PEGASUS_ADMISSION_REGISTRY
        if not path.startswith("tools/pegasus/")
    }
    assert GB._NON_PEGASUS_ADMISSION_FALLBACK_PATHS == expected


def test_bash_non_pegasus_raw_mention_detector_covers_fallback_spellings():
    for path in GB._NON_PEGASUS_ADMISSION_FALLBACK_PATHS:
        directory, name = path.rsplit("/", 1)
        spellings = (
            path,
            f"./{path}",
            f"{directory}//{name}",
            f"{directory}/./{name}",
            path[:-3].replace("/", "."),
        )
        for spelling in spellings:
            assert GB._NON_PEGASUS_ADMISSION_RAW_MENTION_RE.search(spelling), \
                f"fallback raw mention の綴り漏れ: {path}: {spelling}"


def test_bash_non_pegasus_registry_keys_exist_as_regular_files():
    paths = {
        path for path in GB._PEGASUS_ADMISSION_REGISTRY
        if not path.startswith("tools/pegasus/")
    }
    assert paths, "非 Pegasus registry key の実在検査が恒真になった"
    for path in paths:
        metadata = os.stat(os.path.join(_REPO, path))
        assert stat.S_ISREG(metadata.st_mode), f"regular file でない: {path}"


def test_bash_non_local_registry_entry_overrides_sanctioned_path(tmp_path):
    module = _load_guard_fixture(tmp_path, "loader-sanctioned-non-local")
    path = "tools/run_tests.py"
    command = f"python3 {path} -q"
    assert path not in module._SANCTIONED_PATHS
    with patch.object(
            module, "_SANCTIONED_PATHS", module._SANCTIONED_PATHS | {path}):
        for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
            ok, why = module.decide(command, site=site)
            assert not ok, f"{site} で非 local entry より sanctioned が優先された"
            assert "admission unknown 実行体" in why
        ok, why = module.decide(command, site="OTHER")
        assert ok, f"OTHER を過剰拒否した: {why}"


def test_bash_login_rejects_unregistered_nested_pegasus_entry():
    for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
        ok, _ = GB.decide(
            "python3 tools/pegasus/future/nested_entry.py", site=site)
        assert not ok, f"{site} で未登録 nested Pegasus entry が通った"


def test_bash_pegasus_execution_inventory_is_synchronized():
    """保証するのは再帰 execution inventory と registry key の同期だけである。

    class の正しさ、資源証拠の妥当性、runtime admission の実効性は保証しない。
    """
    root = os.path.join(_REPO, "tools", "pegasus")
    inventory = set()
    for directory, _, filenames in os.walk(root):
        for filename in filenames:
            absolute = os.path.join(directory, filename)
            if not os.path.isfile(absolute):
                continue
            mode = os.stat(absolute).st_mode
            with open(absolute, "rb") as candidate:
                has_shebang = candidate.read(2) == b"#!"
            if (filename.endswith((".py", ".sh", ".pbs"))
                    or mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    or has_shebang):
                inventory.add(os.path.relpath(absolute, _REPO))
    registry = {
        path for path in GB._PEGASUS_ADMISSION_REGISTRY
        if path.startswith("tools/pegasus/")
    }
    assert inventory == registry, \
        ("保証するのは execution inventory 同期だけ: "
         f"registry 欠落={sorted(inventory - registry)}, "
         f"実体欠落={sorted(registry - inventory)}")


def test_bash_login_pbs_shebang_entries_remain_unknown_and_denied():
    for path in (
        "tools/pegasus/probes/t293_perf_site_probe.pbs",
        "tools/pegasus/probes/t419_probe_causality.pbs",
    ):
        assert GB._PEGASUS_ADMISSION_REGISTRY[path]["class"] == "unknown"
        ok, _ = GB.decide(f"bash {path}", site="PEGASUS_LOGIN")
        assert not ok, f"unknown の PBS job body が login で通った: {path}"


def test_bash_study_entries_require_compute_dispatch():
    commands = {
        "tools/pegasus/paper_story_a2_certification.sh":
            "bash tools/pegasus/paper_story_a2_certification.sh",
        "tools/pegasus/run_ss2pl_lock_study.py":
            "python3 tools/pegasus/run_ss2pl_lock_study.py",
        "tools/pegasus/ss2pl_lock_study.sh":
            "bash tools/pegasus/ss2pl_lock_study.sh",
    }
    for path, command in commands.items():
        assert GB._PEGASUS_ADMISSION_REGISTRY[path]["class"] == \
            "dispatch-required"
        for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT"):
            ok, why = GB.decide(command, site=site)
            assert not ok, \
                f"{site} で study compute entry が通った: {path} ({why})"


def test_bash_sanctioned_pegasus_paths_are_derived_from_registry():
    expected = {
        path for path, expected_class in _PEGASUS_EXPECTED_CLASSES.items()
        if expected_class == "local-ok"
    }
    actual = {
        path for path in GB._SANCTIONED_PATHS
        if path.startswith("tools/pegasus/")
    }
    assert actual == expected


def test_bash_login_allows_fetch_third_party_sanctioned_spellings():
    """exact path 1 本が 4 つの local-ok subcommand を受理することを守る。"""
    for cmd in _FETCH_THIRD_PARTY_SANCTIONED_SPELLINGS:
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"sanctioned な third-party 取得経路が拒否された: {cmd!r} ({why})"


def test_bash_login_fetch_third_party_entry_is_exact():
    """sanctioned な受理集合が repo 内の実在する exact path 1 本であることを守る。"""
    assert "tools/pegasus/fetch_third_party.py" in GB._SANCTIONED_PATHS
    assert os.path.isfile(os.path.join(
        _REPO, "tools", "pegasus", "fetch_third_party.py"))


def test_bash_login_fetch_third_party_does_not_sanction_siblings():
    """collect_receipt.py は login 手順なので未裁定の拒否を pin しない。
    control は login 手順にない計算ノード側 job script から選ぶ。"""
    for cmd in (
        "bash tools/pegasus/certify_calibration.sh",
        "python3 tools/pegasus/run_probe.py",
    ):
        ok, _ = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert not ok, f"非 sanctioned な Pegasus 兄弟が login で通った: {cmd!r}"


def test_bash_compute_allows_fetch_third_party_spellings():
    """login 用 sanctioned 追加が compute の既存受理集合を縮小しないことを守る。"""
    for cmd in _FETCH_THIRD_PARTY_SANCTIONED_SPELLINGS:
        ok, why = GB.decide(cmd, site="PEGASUS_COMPUTE")
        assert ok, f"compute の third-party 取得経路が拒否された: {cmd!r} ({why})"


_PROVENANCE_SANCTIONED_SPELLINGS = (
    "python3 tools/check_ai_provenance.py --range 72849d3..HEAD",
    "python3 ./tools/check_ai_provenance.py --range 72849d3..HEAD",
    "./tools/check_ai_provenance.py --range 72849d3..HEAD",
    "python3 -m tools.check_ai_provenance --range 72849d3..HEAD",
)

# 拒否側の綴り。checker 自身の site gate (第一層) を通らない経路だけを列挙する。
_PROVENANCE_NONSANCTIONED_SPELLINGS = (
    ("outside-repo-copy", "python3 /tmp/copy/check_ai_provenance.py --range A..B"),
    ("outside-repo-copy-direct", "/tmp/copy/check_ai_provenance.py --range A..B"),
    ("home-relative-copy", "~/copy-of-izanagi/tools/check_ai_provenance.py --range A..B"),
    ("cwd-relative", "python3 check_ai_provenance.py --range A..B"),
    ("parent-relative", "python3 ../izanagi/tools/check_ai_provenance.py --range A..B"),
    ("shell-command-string",
     "bash -lc 'cd /tmp && python3 ../izanagi/tools/check_ai_provenance.py --range A..B'"),
    # sanctioned 追加が `_script_target` の第 1 非 option 引数候補を通して許可へ
    # 反転させないための positive control (現状も拒否)。
    ("dash-m-pytest", "python3 -mpytest tools/check_ai_provenance.py"),
)


def test_bash_login_sanctioned_entries_are_exact():
    assert "tools/check_ai_provenance.py" in GB._SANCTIONED_PATHS
    assert os.path.isfile(os.path.join(_REPO, "tools", "check_ai_provenance.py"))
    for cmd in (
        "python3 tools/run_tests.py -q",
        "python3 ./tools/pegasus/dispatch_compute.py --help",
        *_PROVENANCE_SANCTIONED_SPELLINGS,
        "tools/pegasus/submit_certify.sh",
        "bash tools/pegasus/submit_floor.sh",
        "sh tools/pegasus/submit_silo_ladder_rung1.sh",
        "qsub job.sh",
        "qdel 12345",
        "qstat 12345",
        "git status",
        "python3 tools/check_docs.py",
        "rg pytest orchestrator/tests",
        "cat AGENTS.md",
        "codex exec review-this-diff",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"sanctioned/純読み取り形が拒否された: {cmd!r} ({why})"

    ok, _ = GB.decide(
        "python3 tools/pegasus/exec_calibrate.py argv.json",
        site="PEGASUS_LOGIN")
    assert not ok, "tools/pegasus/* の glob 許可で汎用 exec trampoline を通してはならない"


@pytest.mark.parametrize(
    "inner_argv",
    (
        "pytest -q",
    ),
    ids=("pytest",),
)
def test_bash_login_allows_exact_generic_compute_gateway(inner_argv):
    """現行 hook が exact compute gateway の pytest 実行形を許可する。"""
    command = (
        "python3 tools/pegasus/dispatch_compute.py --task generic -- "
        + inner_argv
    )
    ok, why = GB.decide(command, site="PEGASUS_LOGIN")
    assert ok, f"exact generic compute gateway が拒否された: {command!r} ({why})"


@pytest.mark.parametrize(
    "command",
    (
        "python3 tools/pegasus/exec_calibrate.py argv.json",
        "python3 -m pytest -q",
    ),
    ids=(
        "direct-trampoline",
        "direct-python-m-pytest",
    ),
)
def test_bash_login_rejects_nonexact_generic_gateway_boundaries(command):
    """generic の例外を exact top-level compute gateway の外へ貸さない。"""
    ok, _ = GB.decide(command, site="PEGASUS_LOGIN")
    assert not ok, f"generic gateway の境界外が login で通った: {command!r}"


def test_bash_login_pins_current_unbounded_gateway_behavior_not_desirability():
    """望ましい仕様の主張ではなく、現行の境界なし gateway 挙動を pin する。"""
    allowed_commands = (
        "python3 tools/pegasus/dispatch_compute.py "
        "--task generic -- pytest -q",
        "python3 tools/pegasus/dispatch_compute.py "
        "--task unknown -- pytest -q",
        "python3 tools/pegasus/dispatch_compute.py "
        "--task any-arbitrary-name -- cmake --build build -j 48",
    )
    for command in allowed_commands:
        ok, why = GB.decide(command, _REPO, site="PEGASUS_LOGIN")
        assert ok, f"現行で許可される gateway argv が拒否された: {command!r} ({why})"

    rejected_command = (
        "python3 tools/pegasus/dispatch_compute.py "
        "--task generic -- python3.10 -m pytest -q"
    )
    ok, _ = GB.decide(rejected_command, _REPO, site="PEGASUS_LOGIN")
    assert not ok, "現行の interpreter residual 拒否が消えた"


@pytest.mark.parametrize(
    "command",
    [command for _, command in _PROVENANCE_NONSANCTIONED_SPELLINGS],
    ids=[name for name, _ in _PROVENANCE_NONSANCTIONED_SPELLINGS],
)
def test_bash_login_blocks_nonsanctioned_provenance_entrypoints(command):
    """M13 期待赤: provenance 分岐を _is_sanctioned の後ろへ移すと dash-m-pytest が通る。"""
    ok, _ = GB.decide(command, site="PEGASUS_LOGIN")
    assert not ok, f"非 sanctioned な provenance 履歴監査が login で通った: {command!r}"
    ok, _ = GB.decide(command, site="PEGASUS_SUSPECT")
    assert not ok, f"非 sanctioned な provenance 履歴監査が SUSPECT で通った: {command!r}"


def test_bash_login_allows_nonexecuting_provenance_flags():
    """受理集合の過剰縮小 (重くない呼び方まで拒否) を検出する正例。"""
    for cmd in (
        "python3 tools/check_ai_provenance.py --message-file /tmp/msg",
        "python3 /tmp/copy/check_ai_provenance.py --message-file /tmp/msg",
        "python3 /tmp/copy/check_ai_provenance.py --message-file=/tmp/msg",
        "/tmp/copy/check_ai_provenance.py --help",
        "python3 -mpytest tools/check_ai_provenance.py --collect-only",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"重くない provenance 呼出が過剰拒否された: {cmd!r} ({why})"


def test_bash_compute_allows_provenance_forms():
    for cmd in (
        *_PROVENANCE_SANCTIONED_SPELLINGS,
        *[value for _, value in _PROVENANCE_NONSANCTIONED_SPELLINGS],
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_COMPUTE")
        assert ok, f"計算ノードの provenance 実行を第二防壁が拒否した: {cmd!r} ({why})"


def test_bash_login_allows_static_module_reads_of_provenance_script():
    """段 6 MF-1 の再発防止: checker を **実行しない** `-m <module>` 形は通す。

    `python3 -m py_compile tools/check_ai_provenance.py` は AGENTS.md が
    ログインノードで明示許可する唯一の静的検査であり、hook が拒否すると
    このファイルの検証手段が消える。引数順で受理集合が変わらないことも固定する
    (`-m py_compile a.py <checker>` は同じ形の言い換えにすぎない)。
    """
    for cmd in (
        "python3 -m py_compile tools/check_ai_provenance.py",
        "python3 -m py_compile hooks/guard_bash.py tools/check_ai_provenance.py",
        "python3 -m py_compile tools/check_ai_provenance.py hooks/guard_bash.py",
        "python3 -m json.tool tools/check_ai_provenance.py",
        "python3 -m compileall -q tools/check_ai_provenance.py",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"checker を実行しない静的 module 起動が拒否された: {cmd!r} ({why})"


def test_provenance_script_borrow_does_not_lend_sanctioned_status():
    """`-m <他 module>` の位置引数に sanctioned 判定を借りさせない (引数順非依存)。

    借用抑止が第 1 非 option 引数だけを見ると、sanctioned path を先に置くだけで
    pytest 判定を飛び越えられる。ここが M13 の穴と同根なので単体でも固定する。
    """
    assert GB._provenance_script_borrow(
        "python3", ["-m", "py_compile", "tools/check_ai_provenance.py"])
    assert GB._provenance_script_borrow(
        "python3", ["-m", "py_compile", "hooks/guard_bash.py",
                    "tools/check_ai_provenance.py"])
    # checker 自身を module として起動する形は借用ではない (sanctioned 綴り)。
    assert not GB._provenance_script_borrow(
        "python3", ["-m", "tools.check_ai_provenance", "--range", "A..B"])
    assert not GB._provenance_script_borrow(
        "python3", ["tools/check_ai_provenance.py", "--range", "A..B"])
    assert not GB._provenance_script_borrow("cat", ["tools/check_ai_provenance.py"])

    ok, _ = GB.decide(
        "python3 -mpytest tools/pegasus/dispatch_compute.py "
        "tools/check_ai_provenance.py",
        site="PEGASUS_LOGIN")
    assert not ok, "sanctioned path を先頭に置くだけで pytest 実行が許可された"


def test_bash_login_provenance_branch_does_not_capture_readers():
    """引数で checker を名指しするだけの読み取り・別 entry point を巻き込まない。"""
    for cmd in (
        "cat tools/check_ai_provenance.py",
        "rg IMPLEMENTATION_POLICY tools/check_ai_provenance.py",
        "git show HEAD:tools/check_ai_provenance.py",
        "wc -c tools/check_ai_provenance.py",
        "python3 tools/run_tests.py orchestrator/tests/test_check_ai_provenance.py",
        "python3 tools/check_docs.py",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"provenance 分岐が無関係な形を巻き込んだ: {cmd!r} ({why})"

    # 逆向き: checker を pytest へ引き渡す実行形は従来どおり拒否のまま。
    ok, _ = GB.decide(
        "python3 -m pytest orchestrator/tests/test_check_ai_provenance.py",
        site="PEGASUS_LOGIN",
    )
    assert not ok, "pytest 実行の既存拒否を provenance 分岐で緩めてはならない"


def test_bash_login_keeps_required_session_commands_available():
    assert GB.site_policy is not None
    for cmd in (
        "python3 tools/run_tests.py -q",
        "python3 tools/check_docs.py",
        "git status --short",
        "codex exec review-this-diff",
        "qsub job.sh",
        "rg TODO .",
        "cat AGENTS.md",
    ):
        ok, why = GB.decide(cmd, site="PEGASUS_LOGIN")
        assert ok, f"LOGIN の通常 Bash 操作が規則で停止した: {cmd!r} ({why})"
        payload = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": cmd},
        })
        with patch.object(
                GB.site_policy, "current_site",
                return_value=GB.site_policy.PEGASUS_LOGIN):
            with patch.object(GB.sys, "stdin", io.StringIO(payload)):
                assert GB.main() == 0, \
                    f"production main が LOGIN の通常 Bash 操作を停止した: {cmd!r}"


@pytest.mark.parametrize("fault_type", (RuntimeError, SystemExit, KeyboardInterrupt))
def test_bash_main_rule_error_is_scoped_to_protected_commands(fault_type):
    cases = (
        ("git status --short", 0),
        (f"cat {_WAL}", 2),
        ("python3 tools/pegasus/dispatch_compute.py --help", 2),
        ("python3 -m tools.pegasus.dispatch_compute --help", 2),
    )
    for cmd, expected in cases:
        payload = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": cmd},
        })
        with patch.object(GB, "decide", side_effect=fault_type("rule bug")):
            with patch.object(GB.sys, "stdin", io.StringIO(payload)):
                actual = GB.main()
                assert actual == expected, \
                    f"規則エラーの影響範囲が不正: {cmd!r} rc={actual}"


def test_bash_main_internal_error_conservatively_rejects_pegasus_mentions():
    """これは意図した保守的挙動であり、内部例外時にだけ発火する。"""
    mention = "rg tools/pegasus/README.md"
    unrelated = "rg TODO ."

    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": mention},
    })
    with patch.object(GB, "decide", return_value=(True, "")):
        with patch.object(GB.sys, "stdin", io.StringIO(payload)):
            assert GB.main() == 0

    for command, expected in ((mention, 2), (unrelated, 0)):
        payload = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": command},
        })
        with patch.object(GB, "decide", side_effect=RuntimeError("rule bug")):
            with patch.object(GB.sys, "stdin", io.StringIO(payload)):
                assert GB.main() == expected


def test_bash_main_internal_error_conservatively_rejects_non_pegasus_admission_mentions(
        tmp_path):
    commands = []
    for path in sorted(GB._NON_PEGASUS_ADMISSION_FALLBACK_PATHS):
        directory, name = path.rsplit("/", 1)
        commands.extend((
            f"python3 {path} --scan",
            f"python3 ./{path} --scan",
            f"python3 {directory}//{name} --scan",
            f"python3 {directory}/./{name} --scan",
            f"python3 -m {path[:-3].replace('/', '.')} --scan",
        ))

    for index, command in enumerate(commands):
        root = tmp_path / f"mention-{index}"
        root.mkdir()
        hook = _prepare_guard_fixture(root, "json-one-entry")
        source = hook.read_text(encoding="utf-8")
        needle = "def decide(command: str, repo_root: str = \"\", *, site=None) -> tuple:\n"
        replacement = (
            "def decide(command: str, repo_root: str = \"\", *, site=None) -> tuple:\n"
            "    raise RuntimeError('synthetic rule failure')\n\n"
            "def _disabled_decide(\n"
            "        command: str, repo_root: str = \"\", *, site=None) -> tuple:\n"
        )
        assert source.count(needle) == 1
        hook.write_text(source.replace(needle, replacement, 1), encoding="utf-8")

        result = _run_guard_subprocess(hook, root, command=command)
        assert result.returncode == 2, \
            f"非 Pegasus admission mention が fail-open: {command}: {result.stderr[:200]}"


def test_bash_login_resolves_python_modules_to_exact_repo_paths():
    for interpreter in ("python3", "/usr/bin/python3", ".venv/bin/python"):
        ok, _ = GB.decide(
            f"{interpreter} -m tools.pegasus.exec_calibrate argv.json",
            site="PEGASUS_LOGIN",
        )
        assert not ok, \
            f"module 形式の非 sanctioned trampoline が通った: {interpreter}"

    ok, why = GB.decide(
        "python3 -m tools.run_tests --collect-only",
        site="PEGASUS_LOGIN",
    )
    assert ok, f"exact sanctioned module 実体が拒否された: {why}"

    ok, _ = GB.decide("python3 -m pytest -q", site="PEGASUS_LOGIN")
    assert not ok, "既存の -m pytest 拒否を module path 解決で壊してはならない"


def test_bash_main_injects_live_login_site():
    """F21 期待赤: orchestrator/tests/test_hooks.py::test_bash_main_injects_live_login_site。"""
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "pytest -q"},
    })
    assert GB.site_policy is not None
    with patch.object(
            GB.site_policy, "current_site",
            return_value=GB.site_policy.PEGASUS_LOGIN):
        with patch.object(GB.sys, "stdin", io.StringIO(payload)):
            assert GB.main() == 2, \
                "main() が live current_site を decide() へ注入していない"


# ---------- 配線 (settings.json) と hook 実行体 ----------

# ---------- guard_read: コンテキスト衛生 (D35) ----------

def _mk_read_fixture() -> str:
    """tmp に repo_root を合成 (docs/output に閾値の上下のファイルを置く)。"""
    root = tempfile.mkdtemp(prefix="izanagi-readtest-")
    os.makedirs(os.path.join(root, "docs"))
    os.makedirs(os.path.join(root, "output", "insights"))
    os.makedirs(os.path.join(root, "orchestrator"))
    big = "x" * (GR.THRESHOLD_BYTES + 1)
    for rel, content in (("docs/big.md", big),
                         ("docs/small.md", "x" * 1000),
                         ("docs/big.png", big),
                         ("output/insights/big.json", big),
                         ("orchestrator/big.py", big)):
        with open(os.path.join(root, rel), "w", encoding="utf-8") as f:
            f.write(content)
    return root


def _read(root, rel_or_abs, **extra):
    path = rel_or_abs if os.path.isabs(rel_or_abs) else os.path.join(root, rel_or_abs)
    return GR.decide("Read", {"file_path": path, **extra}, repo_root=root)


def test_read_small_outside_or_missing_allowed():
    root = _mk_read_fixture()
    try:
        ok, _ = _read(root, "docs/small.md")
        assert ok, "閾値以下の docs は素通しであるべき"
        ok, _ = _read(root, "orchestrator/big.py")
        assert ok, "docs/output 外は大きくても管轄外"
        ok, _ = _read(root, "docs/no-such.md")
        assert ok, "実在しないパスはツール側が報告する (管轄外)"
        ok, _ = _read(root, "docs/big.png")
        assert ok, "バイナリ族は offset の概念がないので管轄外"
        ok, _ = GR.decide("Grep", {"file_path": os.path.join(root, "docs/big.md")},
                          repo_root=root)
        assert ok, "Read 以外のツールは管轄外"
    finally:
        shutil.rmtree(root)


def test_read_large_guarded_without_range_denied():
    root = _mk_read_fixture()
    try:
        for rel in ("docs/big.md", "output/insights/big.json"):
            ok, why = _read(root, rel)
            assert not ok, f"{rel} の無指定全読は拒否されるべき"
            assert "offset" in why and "D35" in why, f"誘導が不十分: {why}"
    finally:
        shutil.rmtree(root)


def test_read_large_with_explicit_range_allowed():
    root = _mk_read_fixture()
    try:
        for extra in ({"offset": 100}, {"limit": 200}, {"offset": 0},
                      {"offset": 1, "limit": 50}, {"pages": "1-5"}):
            ok, why = _read(root, "docs/big.md", **extra)
            assert ok, f"明示 {extra} の部分読みは通すべき: {why}"
    finally:
        shutil.rmtree(root)


def test_read_symlink_into_docs_still_guarded():
    root = _mk_read_fixture()
    try:
        link = os.path.join(root, "alias.md")
        os.symlink(os.path.join(root, "docs", "big.md"), link)
        ok, _ = _read(root, link)
        assert not ok, "symlink 経由でも realpath 照合で管轄内 (guard_write と同系)"
    finally:
        shutil.rmtree(root)


# ---------- guard_agent (モデル経済衛生) ----------

def _agent(tool_input, repo_root=""):
    return GA.decide("Agent", tool_input, repo_root=repo_root)


def _mk_agents_fixture():
    root = tempfile.mkdtemp(prefix="ga_")
    d = os.path.join(root, ".claude", "agents")
    os.makedirs(d)
    with open(os.path.join(d, "pinned.md"), "w", encoding="utf-8") as f:
        f.write("---\nname: pinned\nmodel: sonnet\neffort: low\n---\n本文\n")
    with open(os.path.join(d, "unpinned.md"), "w", encoding="utf-8") as f:
        f.write("---\nname: unpinned\n---\n本文の model: opus はピンではない\n")
    with open(os.path.join(d, "no-frontmatter.md"), "w", encoding="utf-8") as f:
        f.write("model: opus\n")        # 先頭が --- でない = frontmatter 無し
    # 敵対レビュー反映分 (2026-07-18): パーサ忠実度の固定
    with open(os.path.join(d, "spacey.md"), "w", encoding="utf-8") as f:
        f.write("---\nmodel : sonnet\n---\n")   # コロン前空白は YAML として正当なピン
    with open(os.path.join(d, "bom.md"), "w", encoding="utf-8") as f:
        f.write("\ufeff---\nmodel: sonnet\n---\n")  # BOM 付きでもピンはピン
    with open(os.path.join(d, "docend.md"), "w", encoding="utf-8") as f:
        f.write("---\nname: docend\n...\nmodel: opus は本文\n")  # ... は終端
    return root


def test_agent_adhoc_without_model_denied():
    root = _mk_agents_fixture()
    try:
        for ti in ({}, {"prompt": "x", "description": "y"},
                   {"subagent_type": "general-purpose"},
                   {"subagent_type": "Explore"},
                   {"model": ""}, {"model": "   "}, {"model": None},
                   {"subagent_type": "unpinned"},
                   {"subagent_type": "no-frontmatter"},
                   {"subagent_type": "ghost"}):       # 定義ファイル自体が無い
            ok, why = _agent(ti, repo_root=root)
            assert not ok, f"暗黙継承 (model 無し) は拒否すべき: {ti}"
            assert "model" in why, why
    finally:
        shutil.rmtree(root)


def test_agent_explicit_model_allowed():
    # 値は問わない (fable 明示も可視・意図的な選択なので通す — 適否は規律領分)
    for m in ("sonnet", "opus", "haiku", "fable"):
        ok, why = _agent({"model": m, "prompt": "x"}, repo_root="/nonexistent")
        assert ok, f"model 明示 {m} は通すべき: {why}"


def test_agent_pinned_role_and_fork_allowed():
    root = _mk_agents_fixture()
    try:
        ok, why = _agent({"subagent_type": "pinned"}, repo_root=root)
        assert ok, f"frontmatter ピンのある named role は通すべき: {why}"
        ok, why = _agent({"subagent_type": "fork"}, repo_root=root)
        assert ok, "fork は親モデル構造固定 (override 無効) なので通す"
    finally:
        shutil.rmtree(root)


def test_agent_role_name_traversal_denied():
    root = _mk_agents_fixture()
    try:
        # agents dir の外に「ピン付き」定義を置いても ../ では参照させない
        with open(os.path.join(root, ".claude", "evil.md"), "w",
                  encoding="utf-8") as f:
            f.write("---\nmodel: sonnet\n---\n")
        ok, _ = _agent({"subagent_type": "../evil"}, repo_root=root)
        assert not ok, "path traversal な subagent_type をピン証明に使わせない"
        ok, _ = _agent({"subagent_type": ".claude/../.claude/agents/pinned"},
                       repo_root=root)
        assert not ok, "セパレータ入り subagent_type も同様"
    finally:
        shutil.rmtree(root)


def test_agent_frontmatter_parser_fidelity():
    """敵対レビュー反映: YAML が認めるピンは認め、本文の model: 行は誤検出しない。"""
    root = _mk_agents_fixture()
    try:
        ok, why = _agent({"subagent_type": "spacey"}, repo_root=root)
        assert ok, f"`model :` (コロン前空白) も正当なピン: {why}"
        ok, why = _agent({"subagent_type": "bom"}, repo_root=root)
        assert ok, f"BOM 付き frontmatter のピンも認める: {why}"
        ok, _ = _agent({"subagent_type": "docend"}, repo_root=root)
        assert not ok, "YAML doc-end `...` 以降の本文 model: をピン扱いしない"
    finally:
        shutil.rmtree(root)


def test_agent_dir_priority_first_definition_wins():
    """敵対レビュー反映: 同名 role の衝突では最初に定義を見つけた dir で確定する
    (harness の同名解決と同じ)。project 側 unpinned + user 側 pinned の組で
    user 側ピンを理由に許可すると、実際に spawn される project 側 role の
    暗黙継承を素通ししてしまう。"""
    base = tempfile.mkdtemp(prefix="ga_dirs_")
    proj = os.path.join(base, "proj")
    user = os.path.join(base, "user")
    os.makedirs(proj)
    os.makedirs(user)
    with open(os.path.join(proj, "collide.md"), "w", encoding="utf-8") as f:
        f.write("---\nname: collide\n---\n")            # project 側: 定義あり・ピン無し
    with open(os.path.join(user, "collide.md"), "w", encoding="utf-8") as f:
        f.write("---\nmodel: opus\n---\n")              # user 側: 同名でピンあり
    with open(os.path.join(user, "useronly.md"), "w", encoding="utf-8") as f:
        f.write("---\nmodel: opus\n---\n")              # user 側にしか無い role
    orig = GA._agents_dirs
    GA._agents_dirs = lambda root: [proj, user]
    try:
        ok, _ = GA.decide("Agent", {"subagent_type": "collide"}, repo_root=base)
        assert not ok, "project 側が unpinned で定義する role は user 側ピンで通さない"
        ok, why = GA.decide("Agent", {"subagent_type": "useronly"}, repo_root=base)
        assert ok, f"project 側に定義が無ければ user 側ピンで許可: {why}"
    finally:
        GA._agents_dirs = orig
        shutil.rmtree(base)


def test_agent_non_agent_tool_ignored():
    ok, _ = GA.decide("Read", {"file_path": "x"}, repo_root="/nonexistent")
    assert ok, "Agent 以外のツールは管轄外"


def test_agent_all_project_roles_pinned():
    """方針の悉皆 gate: project の全 named role は frontmatter に model と effort の
    両ピンを持つ (ピン無し role は guard_agent の許可経路に乗らず、model 無し起動が
    拒否されるようになる — role を足すならピンも足すことをここで強制する)。"""
    d = os.path.join(_REPO, ".claude", "agents")
    roles = sorted(f for f in os.listdir(d) if f.endswith(".md"))
    assert roles, "project roles が見つからない"

    def _fm_has(md, key):
        with open(md, encoding="utf-8") as f:
            if f.readline().strip() != "---":
                return False
            for line in f:
                if line.strip() == "---":
                    return False
                if line.startswith(key + ":") and line[len(key) + 1:].strip():
                    return True
        return False

    missing = [f for f in roles
               if not (_fm_has(os.path.join(d, f), "model")
                       and _fm_has(os.path.join(d, f), "effort"))]
    assert not missing, f"model/effort ピンの無い role: {missing}"
    for f in roles:
        ok, why = GA.decide("Agent", {"subagent_type": f[:-3]})
        assert ok, f"{f}: ピン済み role が拒否された: {why}"


# ---------- 配線と煙テスト ----------

def _assert_settings_json_wires_all_hooks(cfg):
    assert "hooks" in cfg, (
        "hooks 配線が消えている: 実装・配線状態の正本 hooks/README.md に反する"
    )
    pre = cfg["hooks"]["PreToolUse"]
    cmds = " ".join(h["command"] for e in pre for h in e["hooks"])
    matchers = [e["matcher"] for e in pre]
    assert "guard_write.py" in cmds and "guard_bash.py" in cmds
    assert "guard_read.py" in cmds
    # SPEC-3 (2026-07-03): substring 'Write'+'Edit' だけでは MultiEdit/NotebookEdit 欠落を
    # 見逃す (恒真寄り)。guard_write.decide は 4 tool すべてを管轄するので、matcher が
    # 4 tool 全部を含むことを要求する (config 一致だけでは足りない = 実配線を gate)。
    write_toks = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
    assert any(write_toks <= set(m.split("|")) for m in matchers), \
        f"Write matcher は {write_toks} を全て含むべき (SPEC-3): {matchers}"
    assert any(m == "Bash" for m in matchers)
    assert any(m == "Read" for m in matchers), "guard_read の Read matcher が未配線"
    assert "guard_agent.py" in cmds
    assert any(m == "Agent" for m in matchers), "guard_agent の Agent matcher が未配線"


def test_settings_json_wires_all_hooks():
    p = os.path.join(_REPO, ".claude", "settings.json")
    with open(p, encoding="utf-8") as f:
        cfg = json.load(f)
    _assert_settings_json_wires_all_hooks(cfg)


def test_settings_json_missing_hooks_is_assertion_failure():
    try:
        _assert_settings_json_wires_all_hooks({})
    except AssertionError as exc:
        reason = str(exc)
        assert "配線が消えている" in reason
        assert "hooks/README.md" in reason
    else:
        raise AssertionError("hooks key 欠落が assert failure にならなかった")


def test_hook_scripts_run_as_subprocess():
    """settings.json が呼ぶ形 (stdin JSON → exit code) の煙テスト。"""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # guard_read の煙テストは実物 decisions.md を使う — 閾値前提が崩れたら恒真化する
    # のでここで前提を明示 gate する
    decisions = os.path.join(_REPO, "docs", "decisions.md")
    assert os.path.getsize(decisions) > GR.THRESHOLD_BYTES, \
        "前提崩れ: decisions.md が閾値以下になった — 煙テストの対象を差し替えること"
    for name, payload, want in (
        ("guard_write", {"tool_name": "Write", "tool_input": {
            "file_path": "/tmp/free.txt", "content": "x"}}, 0),
        ("guard_write", {"tool_name": "Write", "tool_input": {
            "file_path": os.path.join(_REPO, "output/campaigns/c/runs/wal.jsonl"),
            "content": "x"}}, 2),
        ("guard_write", {"tool_name": "apply_patch", "cwd": _REPO,
                         "tool_input": {"command":
                             "*** Add File: docs/codex-safe.md\n+x\n"}}, 0),
        ("guard_write", {"tool_name": "apply_patch", "cwd": _REPO,
                         "tool_input": {"command":
                             "*** Add File: output/campaigns/c/runs/anything.log\n"}}, 2),
        ("guard_write", {"tool_name": "apply_patch", "cwd": _REPO,
                         "tool_input": {"command":
                             "*** Update File: output/campaigns/c/campaign.lock\n"}}, 2),
        ("guard_write", {"tool_name": "apply_patch", "cwd": _REPO,
                         "tool_input": {"command":
                             "*** Delete File: build-variants/x/meta.json\n"}}, 2),
        ("guard_write", {"tool_name": "apply_patch", "cwd": _REPO,
                         "tool_input": {"command":
                             "*** Move to: output/s8b-freeze/approvals/x.json\n"}}, 2),
        ("guard_write", {"tool_name": "apply_patch",
                         "cwd": os.path.join(_REPO, "docs"),
                         "tool_input": {"command":
                             "*** Add File: ../output/campaigns/c/runs/anything.log\n"}}, 2),
        ("guard_write", {"tool_name": "apply_patch", "tool_input": {"command":
                             "*** Add File: docs/cwd-required.md\n"}}, 2),
        ("guard_write", {"tool_name": "apply_patch", "cwd": _REPO,
                         "tool_input": {"command": [
                             "output/campaigns/c/runs/anything.log"]}}, 2),
        ("guard_write", {"tool_name": "Write", "tool_input": {"command":
                             "*** Update File: output/campaigns/c/runs/anything.log\n"}}, 0),
        ("guard_bash", {"tool_name": "Bash", "tool_input": {
            "command": "ls"}}, 0),
        ("guard_bash", {"tool_name": "Bash", "tool_input": {
            "command": "echo x >> output/campaigns/c/runs/wal.jsonl"}}, 2),
        ("guard_bash", {"tool_name": "Bash", "tool_input": {}}, 0),   # command 欠落
        ("guard_write", "壊れた json wal.jsonl", 2),                  # 不正入力 fails-closed
        ("guard_write", "壊れた json", 0),                            # 管轄 token 無しは従来どおり
        ("guard_read", {"tool_name": "Read", "tool_input": {
            "file_path": decisions}}, 2),                             # 無指定全読は拒否
        ("guard_read", {"tool_name": "Read", "tool_input": {
            "file_path": decisions, "offset": 100, "limit": 50}}, 0),  # 部分読みは許可
        ("guard_read", "壊れた json", 0),                             # 衛生層は fail-open
        ("guard_agent", {"tool_name": "Agent", "tool_input": {
            "description": "x", "prompt": "y",
            "subagent_type": "general-purpose"}}, 2),                 # 暗黙継承は拒否
        ("guard_agent", {"tool_name": "Agent", "tool_input": {
            "description": "x", "prompt": "y", "model": "sonnet"}}, 0),  # 明示は許可
        ("guard_agent", {"tool_name": "Agent", "tool_input": {
            "description": "x", "prompt": "y",
            "subagent_type": "verifier"}}, 0),                        # 実 role のピンで許可
        ("guard_agent", "壊れた json", 0),                            # 経済衛生層は fail-open
    ):
        raw = payload if isinstance(payload, str) else json.dumps(payload)
        r = subprocess.run(
            [sys.executable, os.path.join(_REPO, "hooks", f"{name}.py")],
            input=raw, capture_output=True, text=True, env=env)
        assert r.returncode == want, \
            f"{name} rc={r.returncode} (期待 {want}) stderr={r.stderr[:200]}"


def _run() -> int:
    """parametrize node を含む同一 node 集合を素の runner からも実行する。

    自前 loop に戻してはいけない: 引数を取る node を skip すると M13 の期待赤
    (`test_bash_login_blocks_nonsanctioned_provenance_entrypoints[dash-m-pytest]`)
    が `python3 orchestrator/tests/test_hooks.py` では 1 件も走らなくなる
    (段 6 レビュー A/B の nit)。委譲する以上 pytest は本ファイルの必須依存であり、
    未導入環境で ImportError になるのは偽緑より安全側 —
    test_check_ai_provenance.py と同型。
    """
    return int(pytest.main(["-q", os.path.abspath(__file__)]))


if __name__ == "__main__":
    sys.exit(_run())
