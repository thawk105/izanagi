# -*- coding: utf-8 -*-
"""後続段 4 diff 検疫層 (4a) の単体テスト + positive control (machine 非依存)。

pytest でも 素の `python3 orchestrator/tests/test_diff_quarantine.py` でも走る。

positive control = 「gate が確実に赤を返す」攻撃 diff 群 (規律2)。行封じ込め (主 gate)
とマーカー内容検査 (二次) の両方を、**git が実際に生成する diff** で検証する
(手書き diff が git の出力形と乖離する罠を避ける)。加えて parse の edge (複数ファイル・
CRLF・no-newline) を合成 diff で固定する。
"""
from __future__ import annotations

import atexit
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign.diff_quarantine import (DiffQuarantine,             # noqa: E402
                                      DiffRejectSubtype,
                                      TemplateMarker, parse_diff,
                                      parse_template_file)
from orchestrator.campaign.diff_quarantine import _same_file as _sf            # noqa: E402

# 実 backoff.hh の EVOLVE-BLOCK 骨格を写した fixture (フレーム = BEGIN/コメント/#if/#else/
# stock 枝/#endif/END、hole = #if と #else の間の 1 行)。
_TEMPLATE = """#pragma once
#include "atomic_tool.hh"

class Backoff {
 public:
  static void backoff(size_t clocks_per_us) {
    uint64_t start(rdtscp()), stop;
    // EVOLVE-BLOCK-BEGIN silo-backoff-magnitude
    // izanagi Phase 3: この骨格だけが coder の編集面 (合成枝の中身のみ)。
#if BACKOFF_FIXED >= 0
    double now_backoff = static_cast<double>(BACKOFF_FIXED);
#else
    double now_backoff = Backoff_.load(std::memory_order_acquire);
#endif
    // EVOLVE-BLOCK-END silo-backoff-magnitude
    while (stop - start < clocks_per_us * now_backoff) stop = rdtscp();
  }
};
"""
_FILE_REL = "include/backoff.hh"
_HOLE_ORIG = "    double now_backoff = static_cast<double>(BACKOFF_FIXED);"


def _git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args],
                          check=True, capture_output=True, text=True)


def _mk_git_repo():
    """tmp に git repo を作り、テンプレを include/backoff.hh に commit する。"""
    repo = tempfile.mkdtemp(prefix="izanagi_diffq_")
    atexit.register(shutil.rmtree, repo, ignore_errors=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    inc = os.path.join(repo, "include")
    os.makedirs(inc)
    with open(os.path.join(inc, "backoff.hh"), "w", encoding="utf-8") as f:
        f.write(_TEMPLATE)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "template")
    return repo


def _marker(repo):
    m = parse_template_file(os.path.join(repo, "include", "backoff.hh"),
                            "silo-backoff-magnitude")
    assert m is not None, "テンプレ parse が None"
    m.source_rel = _FILE_REL           # orchestrator が正確な rel を差し替える想定
    return m


def _edit_file(repo, new_content):
    with open(os.path.join(repo, "include", "backoff.hh"), "w", encoding="utf-8") as f:
        f.write(new_content)


def _diff(repo):
    return _git(repo, "diff", "HEAD", "--", _FILE_REL).stdout


def _run_after_edit(repo, new_content):
    m = _marker(repo)                  # マーカーは pristine テンプレ (HEAD) から parse
    _edit_file(repo, new_content)
    res = DiffQuarantine(m, _diff(repo), head_text=_TEMPLATE).validate()
    # commit されていない編集を巻き戻して repo を再利用可能に。
    _git(repo, "checkout", "--", _FILE_REL)
    return res


def _assert_hole_escape(res, branch):
    """HOLE_ESCAPE の型と非逐語 evidence schema を branch ごとに固定する。"""
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.HOLE_ESCAPE, res.digest
    assert res.digest is not None
    evidence = res.digest["evidence"]
    assert f"branch={branch}" in evidence, evidence
    assert "anchor_line=" in evidence, evidence
    assert re.search(r"\bbyte_length=\d+\b", evidence), evidence
    assert re.search(r"\bsha256_12=[0-9a-f]{12}\b", evidence), evidence


# ===== parse_template_file =====

def test_parse_template_line_numbers():
    repo = _mk_git_repo()
    m = _marker(repo)
    assert m.begin_line == 8, m.begin_line
    assert m.if_line == 10, m.if_line
    assert m.else_line == 12, m.else_line
    assert m.endif_line == 14, m.endif_line
    assert m.end_line == 15, m.end_line
    assert m.hole_first == 11 and m.hole_last == 11
    assert m.in_hole(11) and not m.in_hole(10) and not m.in_hole(12)
    # stock 枝 (13) と #endif (14) はフレーム、hole (11) はフレームでない
    assert 13 in m.frame_text and 14 in m.frame_text
    assert 11 not in m.frame_text


def test_parse_missing_marker_returns_none():
    repo = _mk_git_repo()
    p = os.path.join(repo, "include", "backoff.hh")
    assert parse_template_file(p, "no-such-marker") is None


def test_template_hole_trusted_line_comment_passes():
    """実 sort テンプレ形の `// coder 編集面` は行内で閉じる信頼済み原文として許可。"""
    d = tempfile.mkdtemp(prefix="izanagi_diffq_template_line_comment_")
    atexit.register(shutil.rmtree, d, ignore_errors=True)
    p = os.path.join(d, "backoff.hh")
    template = _TEMPLATE.replace(_HOLE_ORIG, _HOLE_ORIG + "  // coder 編集面")
    with open(p, "w", encoding="utf-8") as f:
        f.write(template)
    m = parse_template_file(p, "silo-backoff-magnitude")
    assert m is not None
    m.source_rel = _FILE_REL
    # 自律ループの head_text 経路と、parse 済み hole_text を使う縮退経路の双方を固定する。
    for route, head_text in (("head_text", template), ("hole_text", None)):
        res = DiffQuarantine(m, "", head_text=head_text).validate()
        assert res.passed, f"route={route}: {res.digest}"


def test_template_hole_context_leak_delimiters_and_splice_fail_closed():
    """テンプレ原文の block comment 文脈/splice は空 diff でも拒否する。"""
    cases = (
        (_HOLE_ORIG + " /* note", "template-hole-comment-delimiter"),
        (_HOLE_ORIG + " */", "template-hole-comment-delimiter"),
        (_HOLE_ORIG + " " + "\\", "template-hole-line-splice"),
    )
    d = tempfile.mkdtemp(prefix="izanagi_diffq_template_invariant_")
    atexit.register(shutil.rmtree, d, ignore_errors=True)
    p = os.path.join(d, "backoff.hh")
    for hole_line, branch in cases:
        with open(p, "w", encoding="utf-8") as f:
            f.write(_TEMPLATE.replace(_HOLE_ORIG, hole_line))
        m = parse_template_file(p, "silo-backoff-magnitude")
        assert m is not None
        m.source_rel = _FILE_REL
        template = _TEMPLATE.replace(_HOLE_ORIG, hole_line)
        # production の head_text 経路を先に、parse 済み hole_text の縮退経路も続けて固定する。
        for route, head_text in (("head_text", template), ("hole_text", None)):
            res = DiffQuarantine(m, "", head_text=head_text).validate()
            assert not res.passed, f"route={route} hole_line={hole_line!r}"
            assert res.subtype is DiffRejectSubtype.MALFORMED, res.digest
            assert f"branch={branch}" in res.digest["evidence"], res.digest


# ===== 正常系 (PASS) =====

def test_legit_hole_edit_passes():
    repo = _mk_git_repo()
    new = _TEMPLATE.replace(_HOLE_ORIG, "    double now_backoff = 10.0;")
    res = _run_after_edit(repo, new)
    assert res.passed, res.digest


def test_legit_multiline_hole_edit_passes():
    repo = _mk_git_repo()
    payload = ("    double base = static_cast<double>(BACKOFF_FIXED);\n"
               "    double now_backoff = base > 0.0 ? base : 1.0;")
    new = _TEMPLATE.replace(_HOLE_ORIG, payload)
    res = _run_after_edit(repo, new)
    assert res.passed, res.digest


def test_empty_diff_passes():
    repo = _mk_git_repo()
    res = DiffQuarantine(_marker(repo), "", head_text=_TEMPLATE).validate()
    assert res.passed


# ===== positive control: frame-altered =====

def test_stock_branch_change_rejected():
    repo = _mk_git_repo()
    new = _TEMPLATE.replace("Backoff_.load(std::memory_order_acquire)", "0.0")
    res = _run_after_edit(repo, new)
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.FRAME_ALTERED, res.digest


def test_if_predicate_change_rejected():
    repo = _mk_git_repo()
    new = _TEMPLATE.replace("#if BACKOFF_FIXED >= 0", "#if BACKOFF_FIXED >= 1")
    res = _run_after_edit(repo, new)
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.FRAME_ALTERED, res.digest


def test_begin_marker_change_rejected():
    repo = _mk_git_repo()
    new = _TEMPLATE.replace("EVOLVE-BLOCK-BEGIN silo-backoff-magnitude",
                            "EVOLVE-BLOCK-BEGIN silo-backoff-hacked")
    res = _run_after_edit(repo, new)
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.FRAME_ALTERED, res.digest


def test_endif_removal_rejected():
    repo = _mk_git_repo()
    # #endif を消す (フレーム破壊)。
    new = _TEMPLATE.replace("#endif\n", "", 1)
    res = _run_after_edit(repo, new)
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.FRAME_ALTERED, res.digest


# ===== positive control: outside-region =====

def test_spin_loop_change_rejected():
    repo = _mk_git_repo()
    new = _TEMPLATE.replace("while (stop - start < clocks_per_us * now_backoff) stop = rdtscp();",
                            "while (stop - start < clocks_per_us * now_backoff * 2) stop = rdtscp();")
    res = _run_after_edit(repo, new)
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.OUTSIDE_REGION, res.digest


def test_include_added_at_top_rejected():
    repo = _mk_git_repo()
    new = _TEMPLATE.replace('#include "atomic_tool.hh"\n',
                            '#include "atomic_tool.hh"\n#include <cstdlib>\n')
    res = _run_after_edit(repo, new)
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.OUTSIDE_REGION, res.digest


# ===== positive control: hole-escape (二次検査) =====

def test_directive_injection_in_hole_rejected():
    repo = _mk_git_repo()
    payload = ("    double now_backoff = 10.0;\n"
               "#define SNEAK 1")
    new = _TEMPLATE.replace(_HOLE_ORIG, payload)
    res = _run_after_edit(repo, new)
    _assert_hole_escape(res, "content-directive")


def test_include_injection_in_hole_rejected():
    repo = _mk_git_repo()
    payload = ("#include <cstdlib>\n"
               "    double now_backoff = 10.0;")
    new = _TEMPLATE.replace(_HOLE_ORIG, payload)
    res = _run_after_edit(repo, new)
    _assert_hole_escape(res, "content-directive")


def test_marker_string_in_hole_rejected():
    repo = _mk_git_repo()
    payload = ('    const char* marker = "EVOLVE-BLOCK-END demo";\n'
               "    double now_backoff = 10.0;")
    new = _TEMPLATE.replace(_HOLE_ORIG, payload)
    res = _run_after_edit(repo, new)
    _assert_hole_escape(res, "content-marker")


def test_digraph_directive_in_hole_rejected():
    repo = _mk_git_repo()
    # C++ digraph "%:" == "#"。行頭 %: は preprocess で指令になる。
    payload = ("    double now_backoff = 10.0;\n"
               "%:define SNEAK 1")
    new = _TEMPLATE.replace(_HOLE_ORIG, payload)
    res = _run_after_edit(repo, new)
    _assert_hole_escape(res, "content-directive")


def test_line_comment_delimiter_in_hole_rejected():
    repo = _mk_git_repo()
    new = _TEMPLATE.replace(_HOLE_ORIG, "    double now_backoff = 10.0; // note")
    res = _run_after_edit(repo, new)
    _assert_hole_escape(res, "content-comment-line")


def test_block_comment_open_delimiter_in_hole_rejected():
    repo = _mk_git_repo()
    new = _TEMPLATE.replace(_HOLE_ORIG, "    double now_backoff = 10.0; /* note */")
    res = _run_after_edit(repo, new)
    _assert_hole_escape(res, "content-comment-block")


def test_line_ending_backslash_in_hole_rejected():
    repo = _mk_git_repo()
    payload = "    double now_backoff = 10.0; " + "\\"
    new = _TEMPLATE.replace(_HOLE_ORIG, payload)
    res = _run_after_edit(repo, new)
    _assert_hole_escape(res, "content-line-splice")


def test_split_block_comment_via_line_splice_rejected():
    repo = _mk_git_repo()
    payload = ("    /" + "\\" + "\n"
               "    * note */\n"
               "    double now_backoff = 10.0;")
    new = _TEMPLATE.replace(_HOLE_ORIG, payload)
    res = _run_after_edit(repo, new)
    _assert_hole_escape(res, "content-line-splice")


def test_url_string_comment_delimiter_rejected_conservatively():
    # 文字列リテラル内でも `//` は誤 reject ではなく、意図した保守性として拒否する。
    repo = _mk_git_repo()
    payload = ('    const char* u = "https://example.invalid/a";\n'
               "    double now_backoff = 10.0;")
    new = _TEMPLATE.replace(_HOLE_ORIG, payload)
    res = _run_after_edit(repo, new)
    _assert_hole_escape(res, "content-comment-line")


def test_hole_escape_evidence_does_not_repeat_payload():
    sentinel = "QPROBE_7f3a4"
    splice_line = f"    double {sentinel} = 10.0; " + "\\"
    cases = (
        (f"#define {sentinel} 1\n    double now_backoff = 10.0;",
         "content-directive", f"#define {sentinel} 1"),
        (f'    const char* marker = "EVOLVE-BLOCK-END {sentinel}";\n'
         "    double now_backoff = 10.0;",
         "content-marker", f'    const char* marker = "EVOLVE-BLOCK-END {sentinel}";'),
        (f"    double now_backoff = 10.0; // {sentinel}",
         "content-comment-line", f"    double now_backoff = 10.0; // {sentinel}"),
        (f"    double now_backoff = 10.0; /* {sentinel} */",
         "content-comment-block", f"    double now_backoff = 10.0; /* {sentinel} */"),
        (splice_line, "content-line-splice", splice_line),
    )
    for payload, branch, rejected_line in cases:
        repo = _mk_git_repo()
        new = _TEMPLATE.replace(_HOLE_ORIG, payload)
        res = _run_after_edit(repo, new)
        _assert_hole_escape(res, branch)
        assert sentinel not in (res.reason or "")
        assert sentinel not in res.digest["reason"]
        assert sentinel not in res.digest["evidence"]
        assert sentinel not in str(res.digest)
        assert sentinel not in str(res.violations)
        line_bytes = rejected_line.encode("utf-8")
        expected_sha = hashlib.sha256(line_bytes).hexdigest()[:12]
        assert f"byte_length={len(line_bytes)}" in res.digest["evidence"]
        assert f"sha256_12={expected_sha}" in res.digest["evidence"]


# ===== rejection digest の構造 (REAL finding #1: explicit reason field) =====

def test_digest_carries_explicit_reason():
    repo = _mk_git_repo()
    new = _TEMPLATE.replace("Backoff_.load(std::memory_order_acquire)", "0.0")
    res = _run_after_edit(repo, new)
    assert not res.passed
    d = res.digest
    for k in ("rejection_type", "subtype", "reason", "diff_region",
              "template_diff_id", "evidence"):
        assert k in d and d[k], f"digest に {k} が欠落: {d}"
    assert d["rejection_type"] == "diff-quarantine"
    assert d["template_diff_id"] == "silo-backoff-magnitude"


# ===== parse edge cases (合成 diff) =====

def test_other_file_change_is_outside_region():
    m = _fixed_marker()
    diff = (
        "diff --git a/include/other.hh b/include/other.hh\n"
        "--- a/include/other.hh\n"
        "+++ b/include/other.hh\n"
        "@@ -1,2 +1,2 @@\n"
        " int x = 1;\n"
        "-int y = 2;\n"
        "+int y = 3;\n"
    )
    res = DiffQuarantine(m, diff).validate()
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.OUTSIDE_REGION, res.digest


def test_parse_handles_crlf_and_no_newline():
    # CRLF 混在 + "\ No newline at end of file" を parse が落ちずに扱う。
    diff = (
        "+++ b/include/backoff.hh\r\n"
        "@@ -11 +11 @@\r\n"
        "-    double now_backoff = static_cast<double>(BACKOFF_FIXED);\r\n"
        "+    double now_backoff = 10.0;\r\n"
        "\\ No newline at end of file\r\n"
    )
    pd = parse_diff(diff)
    assert not pd.malformed, pd.reason
    assert len(pd.hunks) == 1
    prefixes = [p for p, _ in pd.hunks[0].lines]
    assert prefixes == ['-', '+'], prefixes
    assert pd.hunks[0].file_rel.endswith("backoff.hh")


def test_deleted_line_starting_with_dashes_not_misparsed():
    # 削除行内容が "-- " で始まっても (カウントベース parse で) ファイルヘッダと誤認しない。
    diff = (
        "+++ b/include/backoff.hh\n"
        "@@ -10,3 +10,3 @@\n"
        " #if BACKOFF_FIXED >= 0\n"
        "--- legacy trailing comment\n"        # 削除行 (content='-- legacy...')
        "+    double now_backoff = 10.0;\n"
        " #else\n"
    )
    pd = parse_diff(diff)
    assert not pd.malformed, pd.reason
    assert len(pd.hunks) == 1
    prefixes = [p for p, _ in pd.hunks[0].lines]
    assert prefixes == [' ', '-', '+', ' '], prefixes


# ===== 敵対 red-team 2026-07-07 回帰: 行番号詐称・fails-open・path over-match =====
# これらは rawdiff (攻撃者が diff テキスト全体を制御) 経由でのみ到達可能なクラスだが、
# fails-closed ゲート (規律2) が自己申告オフセットを信じ不正 diff で fails-OPEN しないよう封鎖。

def _fixed_marker():
    return TemplateMarker(marker_id="silo-backoff-magnitude", source_rel=_FILE_REL,
                          begin_line=8, if_line=10, else_line=12, endif_line=14, end_line=15)


def test_lying_hunk_header_rejected_by_head_anchor():
    # フレーム行 (#if, 実 10 行目) 削除を src=11 (hole) と詐称。HEAD アンカーで不一致 → MALFORMED。
    m = _fixed_marker()
    diff = ("@@ -11,1 +11,1 @@\n"
            "-#if BACKOFF_FIXED >= 0\n"
            "+#if TAMPERED\n")
    res = DiffQuarantine(m, diff, head_text=_TEMPLATE).validate()
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.MALFORMED, res.digest


def test_stock_deletion_via_lying_header_rejected():
    # stock 枝 (実 13 行目) 削除+置換を src=11 と詐称 (line-shift 攻撃)。HEAD アンカーで捕捉。
    m = _fixed_marker()
    diff = ("@@ -11,1 +11,1 @@\n"
            "-    double now_backoff = Backoff_.load(std::memory_order_acquire);\n"
            "+    double now_backoff = STOCK_REPLACED;\n")
    res = DiffQuarantine(m, diff, head_text=_TEMPLATE).validate()
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.MALFORMED, res.digest


def test_unparseable_hunk_header_fails_closed():
    # `@@ --5,1 +11,1 @@` は _HUNK_RE 不一致 → 未パース。空 diff と取り違えず fails-closed。
    m = _fixed_marker()
    diff = ("@@ --5,1 +11,1 @@\n"
            "-#if BACKOFF_FIXED >= 0\n"
            "+#if TAMPERED\n")
    res = DiffQuarantine(m, diff, head_text=_TEMPLATE).validate()
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.MALFORMED, res.digest


def test_bare_backslash_desync_fails_closed():
    # bare `\` 行 (no-newline マーカー以外) でカウントを desync → truncated → MALFORMED。
    m = _fixed_marker()
    diff = ("@@ -10,5 +10,4 @@\n"
            "\\ skip line for #if\n"
            "\\ skip line for hole\n"
            " #else\n"
            "-    double now_backoff = Backoff_.load(std::memory_order_acquire);\n"
            "+    double now_backoff = STOCK_REPLACED_BY_ATTACKER;\n"
            " #endif\n")
    res = DiffQuarantine(m, diff, head_text=_TEMPLATE).validate()
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.MALFORMED, res.digest


def test_bare_cr_line_fails_closed():
    # 本体途中の bare `\r` (空行様) 行で早期終端 → truncated → MALFORMED。
    m = _fixed_marker()
    diff = ("@@ -10,5 +10,5 @@\n"
            " #if BACKOFF_FIXED >= 0\n"
            "-    double now_backoff = static_cast<double>(BACKOFF_FIXED);\n"
            "+    double now_backoff = 7.0;\n"
            "\r\n"
            "-#endif\n")
    res = DiffQuarantine(m, diff, head_text=_TEMPLATE).validate()
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.MALFORMED, res.digest


def test_same_file_path_traversal_rejected():
    # ../../etc/include/backoff.hh を target と誤認しない (path traversal 拒否)。
    m = _fixed_marker()
    diff = ("+++ b/../../etc/include/backoff.hh\n"
            "@@ -11,1 +11,1 @@\n"
            "-    double now_backoff = static_cast<double>(BACKOFF_FIXED);\n"
            "+    double now_backoff = 3.0;\n")
    res = DiffQuarantine(m, diff, head_text=_TEMPLATE).validate()
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.OUTSIDE_REGION, res.digest


def test_same_file_reporoot_basename_not_overmatched():
    # repo-root の "backoff.hh" は "include/backoff.hh" と別ファイル (endswith 過剰一致の回帰)。
    assert not _sf("backoff.hh", "include/backoff.hh")
    assert not _sf("../../etc/include/backoff.hh", "include/backoff.hh")
    assert not _sf("silo/transaction.cc", "include/backoff.hh")
    assert _sf("include/backoff.hh", "include/backoff.hh")
    assert _sf("b/include/backoff.hh", "include/backoff.hh")
    assert _sf("./include/backoff.hh", "include/backoff.hh")


def test_headerless_body_lines_fail_closed():
    # ヘッダ (@@) 無しの裸 body 行 (-#else 削除) を「空 diff」と誤認せず MALFORMED。
    m = _fixed_marker()
    diff = ("-#else\n"
            "+#if EVIL\n")
    res = DiffQuarantine(m, diff, head_text=_TEMPLATE).validate()
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.MALFORMED, res.digest


def test_count_overflow_body_fail_closed():
    # 宣言カウント (1/1) を超える後続変更行 (末尾 #else 削除) が黙って破棄されず MALFORMED。
    m = _fixed_marker()
    diff = ("@@ -11,1 +11,1 @@\n"
            "-    double now_backoff = static_cast<double>(BACKOFF_FIXED);\n"
            "+    double now_backoff = 5.0;\n"
            "-#else\n")
    res = DiffQuarantine(m, diff, head_text=_TEMPLATE).validate()
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.MALFORMED, res.digest


def test_incidental_marker_mention_in_hole_passes():
    # 通常文字列が bare "EVOLVE-BLOCK" を含んでも BEGIN/END 指令でなければ通す
    # (bare 部分文字列一致による誤 reject の回帰。marker 偽装は BEGIN/END のみ弾く)。
    repo = _mk_git_repo()
    payload = ('    const char* label = "EVOLVE-BLOCK region";\n'
               "    double now_backoff = 10.0;")
    new = _TEMPLATE.replace(_HOLE_ORIG, payload)
    res = _run_after_edit(repo, new)
    assert res.passed, res.digest


def test_content_check_conservative_by_design():
    # 内容検査は行頭 # を C++ raw string 文脈でも保守的に弾く = 設計通りの安全側倒し
    # (D33: text 検査の文脈認識化は不可能かつ罠)。coder は hole 行を # で始めない規約。
    # これは「誤 reject でなく意図した保守性」であることを固定する回帰。
    repo = _mk_git_repo()
    payload = ('    const char* directive = R"raw(\n'
               "#define LOOKS_LIKE_DIRECTIVE 1\n"
               ')raw";\n'
               "    double now_backoff = 10.0;")
    new = _TEMPLATE.replace(_HOLE_ORIG, payload)
    res = _run_after_edit(repo, new)
    _assert_hole_escape(res, "content-directive")


# ===== 二重 runner (pytest 非依存) =====

def _run():
    import traceback
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    npass = nfail = nerr = 0
    for fn in fns:
        try:
            fn()
            npass += 1
        except AssertionError as e:
            nfail += 1
            print(f"FAIL {fn.__name__}: {e}")
        except Exception:  # noqa: BLE001
            nerr += 1
            print(f"ERROR {fn.__name__}:")
            traceback.print_exc()
    print(f"\n{npass} passed, {nfail} failed, {nerr} errors (of {len(fns)})")
    return 0 if (nfail == 0 and nerr == 0) else 1


def test_policy_reject_subtypes_are_distinct_from_existing_subtypes():
    assert DiffRejectSubtype.POLICY_GRAMMAR.value == 'policy-grammar'
    assert DiffRejectSubtype.POLICY_COMPILE.value == 'policy-compile'
    assert DiffRejectSubtype.POLICY_GRAMMAR is not DiffRejectSubtype.HOST_EFFECT


if __name__ == "__main__":
    sys.exit(_run())
