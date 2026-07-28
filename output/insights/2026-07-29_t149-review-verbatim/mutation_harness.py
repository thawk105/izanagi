# -*- coding: utf-8 -*-
"""[T-149] 変異 matrix harness v2 (DW-M01/M04/M05/M07/M08, DW-O19)。

RR-1 fix 後の tracked file を一時変異し、focused pytest の FAILED node を
採取して事前登録の期待集合と突合する。**主張射程は本 focused node 集合内の期待一致**
(段 6 RA-4 の訂正 — 全 suite での挙動は受入全走が別途担う)。
復元は内容比較 (read_text == git show HEAD)。単一走行 guard = flock。cwd = worktree root。
"""
import fcntl
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
assert (ROOT / "orchestrator/campaign/source_digest.py").is_file(), f"cwd が repo root でない: {ROOT}"

NODES = [
    "orchestrator/tests/test_campaign.py::test_edit_surface_constants_exact_relationship",
    "orchestrator/tests/test_campaign.py::test_axis_driver_source_rel_within_edit_surface",
    "orchestrator/tests/test_campaign.py::test_source_digest_allowlist",
    "orchestrator/tests/test_s6_proposal_rounds.py::test_freshness_tracks_live_edit_surface",
    "orchestrator/tests/test_s6_proposal_rounds.py::test_freshness_flags_opened_mismatch",
    "orchestrator/tests/test_s6_proposal_rounds.py::test_freshness_flags_designated_closed",
    "orchestrator/tests/test_s6_proposal_rounds.py::test_s6_frozen_surface_matches_live_edit_surface",
    "orchestrator/tests/test_hooks.py::test_constants_match_source_digest",
    "orchestrator/tests/test_s1_known_axes_freeze.py::test_silo_cmake_rel_matches_source_digest_template",
]

_T1 = "orchestrator/tests/test_campaign.py::test_edit_surface_constants_exact_relationship"
_T3 = "orchestrator/tests/test_campaign.py::test_axis_driver_source_rel_within_edit_surface"
_ALLOW = "orchestrator/tests/test_campaign.py::test_source_digest_allowlist"
_T2A = "orchestrator/tests/test_s6_proposal_rounds.py::test_freshness_tracks_live_edit_surface"
_T2B = "orchestrator/tests/test_s6_proposal_rounds.py::test_freshness_flags_opened_mismatch"
_T2C = "orchestrator/tests/test_s6_proposal_rounds.py::test_freshness_flags_designated_closed"
_HOOK = "orchestrator/tests/test_hooks.py::test_constants_match_source_digest"
_T4 = "orchestrator/tests/test_s1_known_axes_freeze.py::test_silo_cmake_rel_matches_source_digest_template"
_STRUCT = "orchestrator/tests/test_s6_proposal_rounds.py::test_s6_frozen_surface_matches_live_edit_surface"

# 事前登録 V1〜V9 (段 4 登録 + 段 6 裁定での拡張。走行前に node 粒度で確定)
MUTATIONS = [
    {
        "id": "V1-ebs-extend",
        "file": "orchestrator/campaign/source_digest.py",
        "old": 'EVOLVE_BLOCK_SOURCES = ("include/backoff.hh", "cc/silo/transaction.cc")',
        "new": 'EVOLVE_BLOCK_SOURCES = ("include/backoff.hh", "cc/silo/transaction.cc", "cc/silo/zzz_t149_fake.cc")',
        "expect": {_T1, _T2A, _T2B, _T2C, _HOOK, _STRUCT},
    },
    {
        "id": "V2-allowlist-drop-options",
        "file": "orchestrator/campaign/source_digest.py",
        "old": 'ALLOWLIST = frozenset({"cmake/Options.cmake", "include/backoff.hh", "cc/silo/transaction.cc"})',
        "new": 'ALLOWLIST = frozenset({"include/backoff.hh", "cc/silo/transaction.cc"})',
        "expect": {_T1, _ALLOW},
    },
    {
        "id": "V3-s6-ebs-drop-transaction",
        "file": "orchestrator/campaign/s6_proposal_rounds.py",
        "old": '    ebs = {"include/backoff.hh", "cc/silo/transaction.cc"}',
        "new": '    ebs = {"include/backoff.hh"}',
        "expect": {_T2A, _T2B, _T2C, _STRUCT},
    },
    {
        "id": "V4-s6-regen-drop-backoff",
        "file": "orchestrator/campaign/s6_proposal_rounds.py",
        "old": '        + ["include/backoff.hh"]',
        "new": '        + []',
        "expect": {_T2A, _T2B, _T2C},
    },
    {
        "id": "V5-loop-source-rel-escape",
        "file": "orchestrator/campaign/p3_s4_loop.py",
        "old": 'SOURCE_REL = "include/backoff.hh"',
        "new": 'SOURCE_REL = "cc/silo/util.cc"',
        "expect": {_T3},
    },
    {
        "id": "V6-protocol-cmake-typo",
        "file": "orchestrator/campaign/source_digest.py",
        "old": '_PROTOCOL_CMAKE = "cc/{protocol}/CMakeLists.txt"',
        "new": '_PROTOCOL_CMAKE = "cc/{protocol}/CMakeList.txt"',
        "expect": {_T4},
    },
    {
        "id": "V7-ebs-shrink",
        "file": "orchestrator/campaign/source_digest.py",
        "old": 'EVOLVE_BLOCK_SOURCES = ("include/backoff.hh", "cc/silo/transaction.cc")',
        "new": 'EVOLVE_BLOCK_SOURCES = ("include/backoff.hh",)',
        "expect": {_T1, _HOOK, _T2A, _T2B, _T2C, _T3, _STRUCT},
    },
    {
        "id": "V8-s6-predicate-one-directional",
        "file": "orchestrator/campaign/s6_proposal_rounds.py",
        "old": '        if e["opened"] != (e["region"] in ebs):',
        "new": '        if e["opened"] and e["region"] not in ebs:',
        "expect": {_T2C},
    },
    {
        "id": "V9-sort-axis-mixup",
        "file": "orchestrator/campaign/p3_s4_loop_sort.py",
        "old": 'SOURCE_REL = "cc/silo/transaction.cc"',
        "new": 'SOURCE_REL = "include/backoff.hh"',
        "expect": {_T3},
    },
]

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run_focused() -> tuple[int, set]:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-rf", "-q", "--no-header", *NODES],
        capture_output=True, text=True, timeout=300, cwd=ROOT,
    )
    text = ANSI.sub("", r.stdout + r.stderr)
    failed = set()
    for line in text.splitlines():
        if line.startswith("FAILED "):
            node = line[len("FAILED "):].split(" - ")[0].strip()
            failed.add(node)
    return r.returncode, failed


def git_show_head(rel: str) -> str:
    r = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, f"git show HEAD:{rel} 失敗"
    return r.stdout


def main() -> int:
    lock = open("/home/SFC/tanab/.claude/jobs/35817947/tmp/t149-wave/mutation.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("ABORT: 単一走行 lock を取得できない (別 harness が走行中)")
        return 2

    results = []
    rc, failed = run_focused()
    print(f"baseline: rc={rc} failed={sorted(failed)}")
    if rc != 0 or failed:
        print("ABORT: baseline (無変異) が緑でない — 変異走行を開始しない")
        return 2
    results.append({"id": "baseline", "rc": rc, "failed": [], "verdict": "GREEN"})

    for m in MUTATIONS:
        path = ROOT / m["file"]
        original = path.read_text(encoding="utf-8")
        head_content = git_show_head(m["file"])
        assert original == head_content, f"{m['file']} が commit 済み内容と一致しない (開始前)"
        n = original.count(m["old"])
        assert n == 1, f"{m['id']}: anchor が一意でない (count={n}) — 停止"
        mutated = original.replace(m["old"], m["new"])
        assert mutated != original, f"{m['id']}: 注入が空"
        try:
            path.write_text(mutated, encoding="utf-8")
            stat = subprocess.run(["git", "diff", "--stat"], capture_output=True, text=True, cwd=ROOT).stdout
            changed = [ln.split("|")[0].strip() for ln in stat.splitlines() if "|" in ln]
            assert changed == [m["file"]], f"{m['id']}: 意図外の diff {changed}"
            rc, failed = run_focused()
        finally:
            path.write_text(original, encoding="utf-8")
        assert path.read_text(encoding="utf-8") == head_content, f"{m['id']}: 復元失敗"
        ok = failed == m["expect"]
        verdict = "KILLED(期待一致)" if ok and failed else (
            "SURVIVED" if not failed else "KILLED(期待外れ)")
        results.append({"id": m["id"], "rc": rc, "failed": sorted(failed),
                        "expected": sorted(m["expect"]), "verdict": verdict})
        print(f"{m['id']}: rc={rc} verdict={verdict}")
        if not ok:
            print(f"  expected={sorted(m['expect'])}")
            print(f"  observed={sorted(failed)}")

    for m in MUTATIONS:
        assert (ROOT / m["file"]).read_text(encoding="utf-8") == git_show_head(m["file"])

    out = Path("/home/SFC/tanab/.claude/jobs/35817947/tmp/t149-wave/mutation-results-v2.json")
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = [r for r in results[1:] if "期待一致" not in r["verdict"]]
    print(f"\nsummary: {len(results)-1} 変異中 {len(results)-1-len(bad)} 件 期待一致")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
