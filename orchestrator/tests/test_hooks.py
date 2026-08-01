# -*- coding: utf-8 -*-
"""H3 hooks (hooks/guard_write.py / guard_bash.py) の単体テスト (machine 非依存)。

hook は .claude/settings.json の PreToolUse から単体スクリプトとして呼ばれるため
package ではない — importlib で直接ロードし、判定核 decide() を叩く。
EVOLVE-BLOCK 構造の検査は tmp に合成した骨格 (template patch と同型) で行い、
実 submodule 側はマーカー適用時のみ検証 (未適用なら skip)。
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_ORCH)
sys.path.insert(0, _ORCH)

from campaign import source_digest                               # noqa: E402
from skiputil import skip                                        # noqa: E402


def _load_hook(name: str):
    path = os.path.join(_REPO, "hooks", f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GW = _load_hook("guard_write")
GB = _load_hook("guard_bash")
GR = _load_hook("guard_read")
GA = _load_hook("guard_agent")

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
    return root


def _edit(root, rel, old, new, tool="Edit", replace_all=False):
    return GW.decide(tool, {"file_path": os.path.join(root, rel),
                            "old_string": old, "new_string": new,
                            "replace_all": replace_all}, repo_root=root)


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
        skip("template patch 未適用 (marker 無し)。適用後に有効化される")
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


def test_bash_main_rule_error_is_scoped_to_protected_commands():
    cases = (
        ("git status --short", 0),
        (f"cat {_WAL}", 2),
    )
    for cmd, expected in cases:
        payload = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": cmd},
        })
        with patch.object(GB, "decide", side_effect=RuntimeError("rule bug")):
            with patch.object(GB.sys, "stdin", io.StringIO(payload)):
                actual = GB.main()
                assert actual == expected, \
                    f"規則エラーの影響範囲が不正: {cmd!r} rc={actual}"


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

def test_settings_json_wires_all_hooks():
    p = os.path.join(_REPO, ".claude", "settings.json")
    with open(p, encoding="utf-8") as f:
        cfg = json.load(f)
    if "hooks" not in cfg:
        skip("hooks 未配線 (方針 A で最小防壁へ再設計中、D30)。"
             "settings.json に PreToolUse を配線する step で自動再有効化される")
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


def test_hook_scripts_run_as_subprocess():
    """settings.json が呼ぶ形 (stdin JSON → exit code) の煙テスト。"""
    env = dict(os.environ)
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
        ("guard_bash", {"tool_name": "Bash", "tool_input": {
            "command": "ls"}}, 0),
        ("guard_bash", {"tool_name": "Bash", "tool_input": {
            "command": "echo x >> output/campaigns/c/runs/wal.jsonl"}}, 2),
        ("guard_bash", {"tool_name": "Bash", "tool_input": {}}, 0),   # command 欠落
        ("guard_write", "壊れた json wal.jsonl", 2),                  # 不正入力 fails-closed
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
