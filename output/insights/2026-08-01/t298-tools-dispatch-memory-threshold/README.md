# [T-298] 実行場所判定のメモリ量移行 — 変異台帳と回帰帰属の生証拠 (2026-08-01)

worklog (105) と D117 の一次資料。本 directory は凍結する (訂正注記のみ追記可)。

## 変異本走

harness は親が段 6 で使った一回限りの計測器具であり、実行可能ファイルとしては凍結しない
(`docs/ai-provenance.md` の実装面 Codex author 契約を迂回しないため)。逐語を下の
「変異 harness の逐語」に残すので、そこから復元できる。各変異は tracked file への単一置換で、
復元は `git checkout --` を正本とし内容比較で検査する。kill 判定は
`python3 tools/check_docs.py` の rc と finding 本文で測る。

- `mutation-ledger-registered-8.json` — 段 4 で事前登録した 8 件 (M-1〜M-8)。**8/8 KILL**。
  anchor = fix2 commit `b8376bb`。無変異の正例が緑であることも同時に記録している。
- `mutation-ledger-review-derived-3.json` — 段 6 焦点再レビューが「すり抜ける」と指摘した
  3 件 (M-10 alias 経由 drift / M-11 外周 pipe 省略の 3 行目 / M-12 `dict.update(TASKS, ...)`)。
  **3/3 KILL**。blocker 所見が実際に閉じたことの裏取り。

合計 **11/11 KILL + 正例 1 件**。全件で注入実在と復元を確認した。

## 受入全走の赤の帰属

受入全走 (Pegasus gen_S request `877168`) が 40 failed を返したが、本 wave の編集面
(`tools/check_docs.py`、`orchestrator/tests/test_check_docs.py`、docs) から
`orchestrator/tests/test_s8b_oracle_driver.py` への import 経路は無い。

- `s8b-failures-branch.txt` — wave branch での単独再走 (request `877170`) の失敗集合。
- `s8b-failures-baseline-d2ac13e.txt` — **本 wave の差分を一切含まない base commit `d2ac13e`**
  を別 worktree に checkout して走らせた baseline (request `877171`) の失敗集合。

両者は `diff` で完全一致 (40 件、`IDENTICAL`)。したがってこの 40 件は local main の既存赤であり、
本 wave による回帰ではない。起票先は [T-299]。

最終受入 (request `877178`) では 41 failed となったが、増分 1 件
(`test_codex_worker_launch.py::test_check_receipt_detects_executable_identity_change`) は
単独再走 (request `877186`) で **58 passed / rc=0** となり再現しなかった。
`DW-O18` に従いフレークとして扱い、実装差分へ帰属しない。

## 実行環境の実測 (D117 の根拠)

- per-user cgroup `user-31609.slice`: `memory.max` = 17179869184 (16 GiB)、`memory.swap.max` = 0。
- `memory.events`: `high 456` / `max 3719307` / `oom 426` / `oom_kill 189`。
  kill 189 件は全て `session-1909.scope` (68 プロセス、全て Claude Code) に計上。
  **ただし victim ≠ trigger** — cgroup OOM killer は badness の高いプロセスを選ぶのであって
  上限を超えさせた張本人を殺すとは限らない。帰属は victim scope の確認までに留める。
- **`memory.peak` はこの kernel (5.15) に存在しない** (実測確認)。
- `systemd-run --user --scope -q -p MemoryAccounting=yes` は動作し、専用 scope の
  `memory.current` を読めることを PoC で確認 (試験値 5,222,400 bytes)。

## 変異 harness の逐語

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[T-298] 変異本走 harness。

事前登録した変異を 1 件ずつ tracked file へ適用し、対象検査が赤くなるか (kill) を測る。
復元は git checkout -- を正本とし (DW-O19)、各変異後に内容比較で復元を検査する (DW-M05)。
kill 判定は「受理集合が期待方向へ変わったか」で行う (DW-M03) — ここでは
`python3 tools/check_docs.py` の rc と finding 本文で測る。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t294-tools-dispatch-oom")
RUNBOOK = REPO / "docs/pegasus-runbook.md"
DISPATCH = REPO / "tools/pegasus/dispatch_compute.py"
TOOLS_README = REPO / "tools/README.md"

# (id, 対象 file, old 逐語, new 逐語, 期待 kill, 単一理由の根拠)
MUTATIONS = [
    ("M-1", RUNBOOK,
     "| `provenance` | `tools/check_ai_provenance.py` |\n", "",
     "drift: 表側に無い task", "表を読む検査は他に無い"),
    ("M-2", DISPATCH,
     '}\nDEFAULT_TASK = "tests"',
     '    "bogus": _TaskSpec(\n'
     '        child_script=("tools", "bogus.py"),\n'
     '        env_allowlist=frozenset(),\n'
     '        probe_imports=(),\n'
     '    ),\n}\nDEFAULT_TASK = "tests"',
     "drift: TASKS 側にしか無い task", "CLI choices は docs を見ない"),
    ("M-3", RUNBOOK,
     "| `tests` | `tools/run_tests.py` |",
     "| `tests` | `tools/run_tests_moved.py` |",
     "drift: child_script 不一致", "写像比較の証拠 (集合一致では通る)"),
    ("M-4", RUNBOOK,
     "### 7.0 判定基準はディレクトリではなくメモリ量 (2026-08-01 ユーザー裁定)",
     "### 7.0x 判定基準はディレクトリではなくメモリ量 (2026-08-01 ユーザー裁定)",
     "節不在を黙って skip しない", "F9 恒真ゲート再発防止"),
    ("M-5", TOOLS_README, None, None,
     "LIVING_DOCS 不在検査", "列挙対象の不在は違反"),
    ("M-6", TOOLS_README, None, None,
     "byte 予算超過", "TextLimit 登録の証拠"),
    ("M-7", DISPATCH,
     'DEFAULT_TASK = "tests"',
     'DEFAULT_TASK = "tests"\nTASKS.update({})',
     "定義後の TASKS 書き込みを拒否", "所見 1 (blocker) の証拠"),
    ("M-8", RUNBOOK,
     "### 7.0 判定基準はディレクトリではなくメモリ量 (2026-08-01 ユーザー裁定)",
     "## 7.0 判定基準はディレクトリではなくメモリ量 (2026-08-01 ユーザー裁定)",
     "親節 ## 7 の検証", "所見 2 (major) の証拠"),
]


def run_check() -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "tools/check_docs.py"],
        cwd=str(REPO), capture_output=True, text=True, timeout=300,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def restore(path: Path) -> None:
    rel = path.relative_to(REPO)
    subprocess.run(["git", "checkout", "--", str(rel)],
                   cwd=str(REPO), check=True, capture_output=True)


def main() -> int:
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO),
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        print(f"ABORT: tree が clean ではない:\n{dirty}")
        return 2

    base_rc, base_out = run_check()
    if base_rc != 0:
        print(f"ABORT: 変異前 baseline が赤 (rc={base_rc}):\n{base_out}")
        return 2
    print(f"baseline: rc={base_rc} (緑)  ← 正例 M-9 (無変異) = 過剰拒否なしの証拠")

    results = []
    for mid, path, old, new, expect, reason in MUTATIONS:
        original = path.read_text(encoding="utf-8")
        if mid == "M-5":
            path.unlink()
        elif mid == "M-6":
            path.write_text(original + ("\nx" * 2000), encoding="utf-8")
        else:
            n = original.count(old)
            if n != 1:
                print(f"{mid}: ABORT 置換対象が一意でない ({n} 件) — DW-M04")
                results.append({"id": mid, "status": "ABORT-not-unique", "count": n})
                continue
            path.write_text(original.replace(old, new), encoding="utf-8")

        # 注入実在の確認 (DW-M04)
        if mid != "M-5":
            injected = path.read_text(encoding="utf-8") != original
        else:
            injected = not path.exists()

        rc, out = run_check()
        killed = rc != 0
        drift_hit = "dispatch inventory drift" in out
        readme_hit = "tools/README.md" in out

        restore(path)
        restored_ok = path.read_text(encoding="utf-8") == original

        results.append({
            "id": mid, "file": str(path.relative_to(REPO)), "expect": expect,
            "reason": reason, "injected": injected, "rc": rc,
            "killed": killed, "drift_finding": drift_hit,
            "readme_finding": readme_hit, "restored": restored_ok,
            "finding": next((l for l in out.splitlines()
                             if "drift" in l or "tools/README" in l), out.splitlines()[0] if out.splitlines() else ""),
        })
        mark = "KILL" if killed else "SURVIVED"
        print(f"{mid}: {mark} rc={rc} injected={injected} restored={restored_ok} — {expect}")
        if not killed:
            print(f"     SURVIVED 詳細: {out[:400]}")

    post_rc, _ = run_check()
    print(f"\n復元後 baseline: rc={post_rc} (0 なら全復元 OK)")
    killed_n = sum(1 for r in results if r.get("killed"))
    print(f"kill: {killed_n}/{len(MUTATIONS)}  + 正例 1 件 (無変異で緑)")
    Path(sys.argv[1]).write_text(
        json.dumps({"baseline_rc": base_rc, "post_rc": post_rc,
                    "killed": killed_n, "total": len(MUTATIONS),
                    "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return 0 if (killed_n == len(MUTATIONS) and post_rc == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
```
