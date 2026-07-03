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


# ---------- guard_write: EVOLVE-BLOCK 領域検査 ----------

def test_payload_edit_allowed():
    root = _mk_fixture_repo()
    try:
        ok, why = _edit(root, "external/ccbench/include/backoff.hh",
                        _PAYLOAD_OLD, "    double now_backoff = 10.0;\n")
        assert ok, f"payload のみの変更は許可されるべき: {why}"
        # Write (全文) でも payload だけの差なら許可
        new_full = _SKELETON.replace(_PAYLOAD_OLD, "    double now_backoff = 5.0;\n")
        ok, why = GW.decide("Write", {"file_path": os.path.join(
            root, "external/ccbench/include/backoff.hh"), "content": new_full},
            repo_root=root)
        assert ok, f"payload のみ差し替えの Write は許可されるべき: {why}"
    finally:
        shutil.rmtree(root)


def test_outside_region_and_skeleton_edits_denied():
    root = _mk_fixture_repo()
    try:
        cases = [
            # 領域外 (spin loop)
            ("while (stop - start < clocks_per_us * now_backoff) stop = rdtscp();",
             "for (;;) {}"),
            # stock 枝 (#else) は不可触
            ("Backoff_.load(std::memory_order_acquire)", "0.0"),
            # 骨格 #if 行の改変
            ("#if BACKOFF_FIXED >= 0", "#if BACKOFF_FIXED >= 1"),
            # マーカー行の削除
            ("    // EVOLVE-BLOCK-END silo-backoff-magnitude\n", ""),
        ]
        for old, new in cases:
            ok, _ = _edit(root, "external/ccbench/include/backoff.hh", old, new)
            assert not ok, f"payload 外の変更は拒否されるべき: {old[:40]!r}"
    finally:
        shutil.rmtree(root)


def test_payload_bans_directives_builtins_trace():
    root = _mk_fixture_repo()
    try:
        bad_payloads = [
            "#ifdef NDEBUG\n    double now_backoff = 1.0;\n#endif\n",   # 生指令 (F2)
            "    double now_backoff = __LINE__;\n",                     # 予約識別子
            "    double now_backoff = __builtin_expect(1, 1);\n",
            "    double now_backoff = NDEBUG ? 1.0 : 2.0;\n",
            "    double now_backoff = 1.0; izanagi_trace::emit();\n",   # 規律1
            "    double now_backoff = 1.0; // ok\n#include <ctime>\n",
            "    // EVOLVE-BLOCK-END silo-backoff-magnitude\n    double now_backoff = 1.0;\n",
        ]
        for p in bad_payloads:
            ok, _ = _edit(root, "external/ccbench/include/backoff.hh",
                          _PAYLOAD_OLD, p)
            assert not ok, f"禁止 payload が通った: {p[:50]!r}"
        # コメント内の散文 (生トークン無し) は許可される (F4: 行頭アンカー走査)
        ok, why = _edit(root, "external/ccbench/include/backoff.hh", _PAYLOAD_OLD,
                        "    // 条件指令 (if 系) は禁止、という説明コメント\n"
                        "    double now_backoff = 2.5;\n")
        assert ok, f"コメント散文だけの payload が誤検出された: {why}"
    finally:
        shutil.rmtree(root)


def test_payload_comment_hiding_denied():
    """GW-1 回帰: `// ... /*` の陰に実コードを隠す攻撃。左優先 tokenizer で防ぐ。"""
    root = _mk_fixture_repo()
    try:
        # // 行コメント内の /* は C++ では inert。次の */ (別 // 行に隠す) までの
        # 実コードを「ブロックコメント」と誤認させ検査から消そうとする攻撃。
        attacks = [
            "    double x = 1.0; // open /*\n"
            "#include <ctime>\n"
            "    double now_backoff = 2.0;\n"
            "    // close */\n",
            "    double x = 1.0; // /*\n"
            "    double now_backoff = __DATE__[0];\n"
            "    // */\n",
            "    double x = 1.0; // /*\n"
            "#define TRACE 1\n"
            "    double now_backoff = 2.0; // */\n",
        ]
        for p in attacks:
            ok, _ = _edit(root, "external/ccbench/include/backoff.hh", _PAYLOAD_OLD, p)
            assert not ok, f"コメント隠蔽攻撃が通った (GW-1): {p[:60]!r}"
        # 文字列リテラル内の // は誤ってコメント開始扱いしない (tokenizer 健全性)
        ok, why = _edit(root, "external/ccbench/include/backoff.hh", _PAYLOAD_OLD,
                        '    const char* s = "a//b"; double now_backoff = 3.0;\n')
        assert ok, f"文字列内 // で誤検出 (GW-1 tokenizer): {why}"
    finally:
        shutil.rmtree(root)


def test_payload_digraph_directive_denied():
    """F1 回帰: C++ digraph `%:` は g++ が # と解釈する。行頭走査で捕える。"""
    root = _mk_fixture_repo()
    try:
        for p in ("%:ifdef Linux\n    double now_backoff = 5.0;\n%:else\n"
                  "    double now_backoff = 500.0;\n%:endif\n",
                  "%:include <ctime>\n    double now_backoff = 1.0;\n",
                  "%:define EVIL 7\n    double now_backoff = 1.0;\n"):
            ok, _ = _edit(root, "external/ccbench/include/backoff.hh", _PAYLOAD_OLD, p)
            assert not ok, f"digraph 指令が通った (F1): {p[:40]!r}"
    finally:
        shutil.rmtree(root)


def test_markerless_file_denies_all_edits():
    root = _mk_fixture_repo()
    try:
        hh = os.path.join(root, "external/ccbench/include/backoff.hh")
        with open(hh, "w", encoding="utf-8") as f:
            f.write("class Backoff { /* stock, template 未適用 */ };\n")
        ok, _ = _edit(root, "external/ccbench/include/backoff.hh", "stock", "hacked")
        assert not ok, "マーカー無し (patch 未適用) の EVOLVE ソースは全編集拒否"
    finally:
        shutil.rmtree(root)


def test_unresolvable_edit_fails_closed():
    root = _mk_fixture_repo()
    try:
        ok, _ = _edit(root, "external/ccbench/include/backoff.hh",
                      "そんな文字列は無い", "x")
        assert not ok, "old_string 不一致は fails-closed で拒否"
        ok, _ = _edit(root, "external/ccbench/include/backoff.hh",
                      "double now_backoff", "x")           # 2 箇所に出現・replace_all 無し
        assert not ok, "old_string 非一意は fails-closed で拒否"
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


# ---------- 配線 (settings.json) と hook 実行体 ----------

def test_settings_json_wires_both_hooks():
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
    assert any("Write" in m and "Edit" in m for m in matchers)
    assert any(m == "Bash" for m in matchers)


def test_hook_scripts_run_as_subprocess():
    """settings.json が呼ぶ形 (stdin JSON → exit code) の煙テスト。"""
    env = dict(os.environ)
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
    ):
        raw = payload if isinstance(payload, str) else json.dumps(payload)
        r = subprocess.run(
            [sys.executable, os.path.join(_REPO, "hooks", f"{name}.py")],
            input=raw, capture_output=True, text=True, env=env)
        assert r.returncode == want, \
            f"{name} rc={r.returncode} (期待 {want}) stderr={r.stderr[:200]}"


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
