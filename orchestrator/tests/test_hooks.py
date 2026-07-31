# -*- coding: utf-8 -*-
"""H3 hooks (hooks/guard_write.py / guard_bash.py) の単体テスト (machine 非依存)。

hook は .claude/settings.json の PreToolUse から単体スクリプトとして呼ばれるため
package ではない — importlib で直接ロードし、判定核 decide() を叩く。
EVOLVE-BLOCK 構造の検査は tmp に合成した骨格 (template patch と同型) で行い、
実 submodule 側はマーカー適用時のみ検証 (未適用なら skip)。
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_ORCH)
sys.path.insert(0, _ORCH)

from campaign import source_digest                               # noqa: E402
from skiputil import Skip, skip                                  # noqa: E402


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


def _site_observer(hostname, pbs_job_id=None, affinity=range(8)):
    observation = GB.pegasus_policy.classify_site(
        hostname, pbs_job_id, affinity)
    return lambda: observation


_LOGIN_SITE = _site_observer("pegasus01")
_COMPUTE_SITE = _site_observer("bnode114", "0:874129.nqsv")
_OTHER_SITE = _site_observer("dev-workstation")


def test_bash_imports_canonical_pegasus_policy():
    assert GB.pegasus_policy.__name__ == "pegasus_policy"
    assert sys.modules["pegasus_policy"] is GB.pegasus_policy
    assert os.path.realpath(GB.pegasus_policy.__file__) == os.path.realpath(
        os.path.join(_REPO, "tools", "pegasus_policy.py"))


def test_bash_pegasus_login_direct_heavy_commands_denied():
    for cmd in (
        "pytest -q",
        "python -m pytest orchestrator/tests/test_hooks.py",
        "python3 -B -m pytest -q",
        "cmake --build build",
        f"cmake --build {_BV}/silo_x_t0",
        "make -j16",
        "ninja -C build",
        "ctest --test-dir build",
    ):
        ok, why = GB.decide(cmd, site_observer=_LOGIN_SITE)
        assert not ok, f"Pegasus login の直接heavy commandが通った: {cmd!r}"
        assert "Pegasus login node" in why


def test_bash_compute_and_other_keep_direct_heavy_behavior():
    commands = (
        "pytest -q",
        "python3 -m pytest -q",
        "cmake --build build",
        "make -j16",
        "ninja -C build",
        "ctest --test-dir build",
        "env -S 'pytest -q'",
        "env --split-string='ninja -C build'",
        "env --split-string 'ctest --test-dir build'",
    )
    for observer in (_COMPUTE_SITE, _OTHER_SITE):
        for cmd in commands:
            ok, why = GB.decide(cmd, site_observer=observer)
            assert ok, f"非loginの既存挙動を変えてはならない: {cmd!r} ({why})"


def test_bash_login_sanctioned_and_read_only_commands_allowed():
    calls = []

    def observer():
        calls.append("called")
        return _LOGIN_SITE()

    for cmd in (
        "python3 tools/run_tests.py orchestrator/tests/test_hooks.py",
        "python3 tools/run_tests.py -m pytest",
        "./tools/run_tests.py --help",
        "python3 tools/pegasus/submit_tests.py --help",
        "python3 tools/pegasus/submit_tests.py -m pytest",
        "./tools/pegasus/submit_tests.py --help",
        "qsub /tmp/test-job.sh",
        "cmake -S . -B build",
        "cmake -B build .",
        "git status --short",
        "ls -la",
    ):
        ok, why = GB.decide(cmd, site_observer=observer)
        assert ok, f"正規entry/read-only commandが誤拒否された: {cmd!r} ({why})"
    assert calls == [], "非heavy commandではsite観測を行わない"


def test_bash_login_wrapped_compound_and_one_shell_c_denied():
    for cmd in (
        "timeout 30 pytest -q",
        "timeout --signal TERM 30 pytest -q",
        "taskset -c 0 python3 -m pytest -q",
        "env PYTHONWARNINGS=default ninja -C build",
        "env -u PYTEST_ADDOPTS ctest --test-dir build",
        "echo ready && ctest --test-dir build",
        "true; cmake --build build",
        "bash -c 'pytest -q'",
        "sh -lc 'make -j2'",
    ):
        ok, _ = GB.decide(cmd, site_observer=_LOGIN_SITE)
        assert not ok, f"wrapper/compound/shell-cのheavy commandが通った: {cmd!r}"


def test_bash_login_env_split_string_heavy_denied():
    """env split payload を実 classifier で再tokenizeし、既知heavy headへ到達する。"""
    commands = (
        "env -S 'pytest -q'",
        "env --split-string='ninja -C build'",
        "env --split-string 'ctest --test-dir build'",
        "timeout 30 env -S 'python3 -m pytest -q'",
        "echo ready && env --split-string='cmake --build build'",
        "env -S \"bash -lc 'make -j2'\"",
    )
    calls = []

    def observer():
        calls.append("called")
        return _LOGIN_SITE()

    for cmd in commands:
        ok, why = GB.decide(cmd, site_observer=observer)
        assert not ok, f"env split-stringのheavy bypassが通った: {cmd!r}"
        assert "Pegasus login node" in why
    assert len(calls) == len(commands), \
        "各env split payloadがheavy classifierからsite gateへ到達するべき"


def test_bash_login_env_split_string_sanctioned_forms_allowed():
    """再tokenize後もrunner/submitter/qsub/configureと非heavy shell-cは許可する。"""
    calls = []

    def observer():
        calls.append("called")
        return _LOGIN_SITE()

    for cmd in (
        "env -S 'python3 tools/run_tests.py -q'",
        "env --split-string='python3 tools/pegasus/submit_tests.py --help'",
        "env --split-string 'qsub /tmp/test-job.sh'",
        "env -S 'cmake -S . -B build'",
        "echo ready && env -S 'python3 tools/run_tests.py -q'",
        "env -S \"bash -lc 'python3 tools/run_tests.py -q'\"",
    ):
        ok, why = GB.decide(cmd, site_observer=observer)
        assert ok, f"env split-stringの正規形が誤拒否された: {cmd!r} ({why})"
    assert calls == [], "再tokenize後に非heavyならsite観測を行わない"


def test_bash_login_invalid_env_split_string_fails_closed():
    """外側shellはvalidでもpayloadが不正/欠落ならloginで曖昧実行を止める。"""
    commands = (
        "env -S",
        "env --split-string",
        """env -S '"pytest -q'""",
        """env '--split-string="ninja -C build'""",
        r"env -S 'pytest\_-q'",
        r"env --split-string='pytest\c ignored'",
    )
    for cmd in commands:
        ok, why = GB.decide(cmd, site_observer=_LOGIN_SITE)
        assert not ok, f"不正env split payloadがloginで通った: {cmd!r}"
        assert "invalid payload" in why and "Pegasus login node" in why

    for observer in (_COMPUTE_SITE, _OTHER_SITE):
        for cmd in commands:
            ok, why = GB.decide(cmd, site_observer=observer)
            assert ok, f"非loginの不正payload挙動をhookが変えた: {cmd!r} ({why})"


def test_bash_heavy_policy_failure_is_scoped_fail_closed():
    calls = []

    def broken_observer():
        calls.append("called")
        raise GB.pegasus_policy.SitePolicyError("ambiguous fixture")

    ok, why = GB.decide("pytest -q", site_observer=broken_observer)
    assert not ok
    assert "site観測が不成立" in why and "fails-closed" in why
    assert calls == ["called"]

    ok, why = GB.decide("make -j16", site_observer=lambda: object())
    assert not ok
    assert "site observer returned an invalid observation" in why

    calls.clear()
    for cmd in ("echo pytest", "cmake -S . -B build", "git status"):
        ok, why = GB.decide(cmd, site_observer=broken_observer)
        assert ok, f"非heavy commandをsite観測失敗で拒否してはならない: {cmd!r} ({why})"
    assert calls == [], "非heavy commandでは失敗するsite seamを呼ばない"


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
        ok, why = GB.decide(cmd, site_observer=_OTHER_SITE)
        assert ok, f"計測層の正当コマンドが誤拒否された (F-FP): {cmd!r} ({why})"


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


def test_bash_hook_direct_execution_imports_policy_in_isolated_mode():
    """hook直接実行が外部PYTHONPATHなしでもcanonical policyをimportできる。"""
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "ls"},
    })
    r = subprocess.run(
        [sys.executable, "-I", "-B",
         os.path.join(_REPO, "hooks", "guard_bash.py")],
        input=payload,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = skipped = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except Skip as e:
            print(f"SKIP {fn.__name__}: {e}")
            skipped += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
