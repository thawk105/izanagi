# -*- coding: utf-8 -*-
"""tools/check_docs.py の恒真ゲート回帰 (F9) + positive control (machine 非依存)。

pytest でも 素の `python3 orchestrator/tests/test_check_docs.py` でも走る。

背景 (F9): LIVING_DOCS の手書き列挙対象が改名/削除で不在になると、旧実装は
`if not doc.exists(): continue` で黙って skip し、その doc への lint が発火せず
「恒真な保証」に化けていた。本テストは positive control =「列挙対象を 1 個わざと
消すと違反が出る」を、合成した最小 repo に対して固定する (規律3 の positive control)。

戦略: 実 check_docs.py を tmp/tools/ へ複製し REPO を tmp に付け替える。check_docs が
読むファイル群を trivial 内容で合成し、baseline が「違反なし」であることを確認した上で、
列挙対象を 1 個消して「不在 = 違反」に変わることを検査する。列挙名は check_docs 本体の
_ENUMERATED_DOCS から導出するので docs の増減で腐らない。
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import time

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_ORCH)
sys.path.insert(0, os.path.join(_REPO, "tools"))

import check_docs  # noqa: E402


_S09_ACCEPTANCE_ORDER_LITERAL = (
    "全 commit・受入結果を固定し、tested main/tip と監査 commit 列を実測して "
    "`DW-O23` を行う。"
)

_SYNTHETIC_ADMISSION_ENTRIES = {
    "tools/pegasus/collect_receipt.py": {
        "class": "unknown",
        "reason": "synthetic unknown",
        "primary_gate": "synthetic deny",
        "evidence": "unmeasured synthetic input",
    },
    "tools/pegasus/fetch_third_party.py": {
        "class": "local-ok",
        "reason": "synthetic measured local path",
        "primary_gate": "synthetic cli",
        "evidence": "runbook §7.0 実測",
    },
    "tools/pegasus/smoke_probe.sh": {
        "class": "dispatch-required",
        "reason": "synthetic job body",
        "primary_gate": "synthetic PBS allocation",
        "evidence": "static job-body classification",
    },
    "tools/pegasus/submit_certify.sh": {
        "class": "local-ok",
        "reason": "synthetic submitter",
        "primary_gate": "synthetic qsub",
        "evidence": "legacy-admitted (未実測)",
    },
    "tools/pegasus/submit_silo_ladder_rung1.sh": {
        "class": "local-ok",
        "reason": "synthetic grandfather warning",
        "primary_gate": "synthetic qsub",
        "evidence": "legacy-admitted (未実測)",
    },
}

_SYNTHETIC_PROJECTION_TABLE = """| path | class | evidence |
|---|---|---|
| `tools/pegasus/collect_receipt.py` | `unknown` | `unmeasured synthetic input` |
| `tools/pegasus/fetch_third_party.py` | `local-ok` | `runbook §7.0 実測` |
| `tools/pegasus/smoke_probe.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/submit_certify.sh` | `local-ok` | `legacy-admitted (未実測)` |
| `tools/pegasus/submit_silo_ladder_rung1.sh` | `local-ok` | `legacy-admitted (未実測)` |"""

_SYNTHETIC_UNKNOWN_TABLE = """| 経路 | なぜ `unknown` か |
|---|---|
| `tools/pegasus/collect_receipt.py` | 入力が未計測 |
| `tools/pegasus/submit_certify.sh` | registry 上は `local-ok` / `legacy-admitted (未実測)` として grandfather 済み |
| `tools/pegasus/submit_silo_ladder_rung1.sh` | registry 上は `local-ok` / `legacy-admitted (未実測)` として grandfather 済み |"""

_SYNTHETIC_MEASURED_TABLE = """| 経路 | 観測ピーク | certified peak | 分類 |
|---|---|---|---|
| `tools/pegasus/fetch_third_party.py fetch` | 10 MiB | 138 MiB | local-ok |
| 同 `fetch` | 9 MiB | 137 MiB | local-ok |"""

_SYNTHETIC_DISPATCH_RUNBOOK = f"""# synthetic Pegasus runbook

## 7. synthetic execution policy

### 7.0 判定基準はディレクトリではなくメモリ量

{_SYNTHETIC_PROJECTION_TABLE}

| task | 子 script |
|---|---|
| `tests` | `tools/run_tests.py` |
| `provenance` | `tools/check_ai_provenance.py` |

{_SYNTHETIC_UNKNOWN_TABLE}

{_SYNTHETIC_MEASURED_TABLE}

### 7.1 synthetic next section

body
"""

_SYNTHETIC_ADMISSION_README = """# synthetic Pegasus tools

## 0. 実行体と admission

| path | 手順上の実行 site | registry class |
|---|---|---|
| `tools/pegasus/collect_receipt.py` | `compute-only` | `unknown` |
| `tools/pegasus/fetch_third_party.py` | `login-direct` | `local-ok` |
| `tools/pegasus/smoke_probe.sh` | `qsub-job-body` | `dispatch-required` |
| `tools/pegasus/submit_certify.sh` | `login-direct` | `local-ok` |

```bash
# admission-site: qsub-job-body
qsub tools/pegasus/smoke_probe.sh
```

```bash
# admission-site: login-direct
python3 tools/pegasus/fetch_third_party.py fetch
tools/pegasus/submit_certify.sh
```

`tools/pegasus/collect_receipt.py` は login では拒否される。
"""

_SYNTHETIC_DISPATCH_SOURCE = """from dataclasses import dataclass

@dataclass(frozen=True)
class _TaskSpec:
    child_script: tuple[str, ...]

TASKS = {
    "tests": _TaskSpec(child_script=("tools", "run_tests.py")),
    "provenance": _TaskSpec(
        child_script=("tools", "check_ai_provenance.py"),
    ),
}
"""


# operations 由来の条件 dispatch key (O07/O15/O21/O22 を除く 19 件)。契約から導出するが、
# exact な外延は test_operation_contract_pins_exact_section_set が literal で pin する。
_OPERATION_CONDITION_KEYS = sorted(
    key
    for key, pairs in check_docs.CONDITION_DISPATCH_CONTRACT.items()
    if any(path == "docs/dev-wave/operations.md" for path, _ in pairs)
)


_PLACEHOLDER_DEBT_WORKLOG = (
    "  repo scan invariant (F34) は本 docs commit 後に再走 <反映>。"
)
_PLACEHOLDER_DEBT_ARCHIVE_ACCEPTANCE = (
    "- **受入**: <受入全走結果を反映> / check_docs / check_ai_provenance (324) / "
    "repo scan invariant (F34) 緑 <反映>。"
)
_PLACEHOLDER_MENTION_WORKLOG_F36 = (
    "- **F36 新設**: 受入・検査の結果欄の `<反映>` プレースホルダが独立 3 wave + insight 1 本で残存し、"
)
_PLACEHOLDER_MENTION_WORKLOG_T094_A = (
    "- **[T-094]**: 機械検出を**採用**し設計も確定 — 検出は `<反映>` / `<受入結果を反映>` /"
)
_PLACEHOLDER_MENTION_WORKLOG_T094_B = (
    "  `<受入全走結果を反映>` の exact 3 文字列、対象は `docs/worklog.md` と verbatim でない"
)
_PLACEHOLDER_DEBT_INSIGHT = (
    "- 受入全走: <受入結果を反映>。check_docs / check_ai_provenance (324) / "
    "repo scan invariant (F34): <反映>。"
)
_PLACEHOLDER_MENTION_INSIGHT_A = (
    "   4件の `<反映>` は F34 恒久対応の実行証拠にならない。`check_docs` も意味的な反映漏れを検出しないと明記する "
    "(`tools/check_docs.py:7-10`)。独立3 wave は族一般化条件を満たす (`docs/dev-wave/core.md:45-48`) ため、"
    "P8 の「新 gate なので見送る」は根拠不足。  "
)
_PLACEHOLDER_MENTION_INSIGHT_B = (
    "  裁定パッケージでは、候補検出対象を少なくとも `<反映>`、`<受入結果を反映>`、"
    "`<受入全走結果を反映>` の exact literal、対象を `docs/worklog.md`、"
    "`docs/archive/worklog-*.md`、非-verbatim の `output/insights/*.md` とし、既存四件は path だけでなく"
    "「含有行 digest + token count」で固定する案を比較すべきである。単なる `<[^>]*反映[^>]*>` は"
    "日本語メタ変数や欠陥説明の引用を誤検出する。"
)
_PLACEHOLDER_ARCHIVE_NAME = "worklog-phase3-0722-0724.md"

_PLACEHOLDER_WORKLOG_ENTRIES = f"""## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 (test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)

{_PLACEHOLDER_DEBT_WORKLOG}

### 次の一手

## 2026-07-25 (3) — [T-068][T-077][T-078] を R 発効により確定的に closure (docs-only・コード 0 byte、branch worktree-dev-wave-e2e-real-seal、計測なし)

{_PLACEHOLDER_MENTION_WORKLOG_F36}

### 次の一手

## 2026-07-25 (4) — /rulings: 裁定待ち 5 件をユーザーが推奨どおり一括裁定 — official 解禁を承認 (D86 起票、計測なし)

{_PLACEHOLDER_MENTION_WORKLOG_T094_A}
{_PLACEHOLDER_MENTION_WORKLOG_T094_B}

### 次の一手
"""

_CLEAN_WORKLOG = f"""# synthetic worklog

## ローテーション

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — second

- [T-001] consumed

### 次の一手
1. [T-002] continue
"""

_CLEAN_PHASE3 = """# synthetic phase

## 見送り台帳 (synthetic)

- [T-900] deferred item

### 裁定・完了記録

- completed item

## 残存リスク

- risk
"""

_SYNTHETIC_CLEANUP_DESCRIPTION = (
    "Safely inventory and clean up merged local Izanagi branches and worktrees "
    "through the shared dispatcher. Use only for an explicit $cleanup-branches "
    "invocation; implicit invocation is disabled."
)
_EXPECTED_CLEANUP_SKILL_SHA256 = (
    "cc3eff8cc6ebebe07b5014c79b2a24aee4a67ab4a55f391e38a9ac82d68ed116"
)
_EXPECTED_CLEANUP_COMMAND_SHA256 = (
    "757d46a3f7f7b4563d5731a931fde73cfd1bbd6364a6af1ee8a2c14279f39c35"
)
_SYNTHETIC_CLEANUP_SKILL = """---
name: cleanup-branches
description: Safely inventory and clean up merged local Izanagi branches and worktrees through the shared dispatcher. Use only for an explicit $cleanup-branches invocation; implicit invocation is disabled.
---

# Cleanup Branches

共通の cleanup dispatcher を読み、その手順を複製せず Codex 固有の安全縮退を重ねて実行する。

## 共通 dispatcher を使う

1. リポジトリ直下の `AGENTS.md` と `CLAUDE.md` を全文読む。`$cleanup-branches` で明示起動された
   掃除だけクラス 2 とし、質問・相談・説明・レビューはクラス 1 の read-only として何も削除しない。
2. `.claude/commands/cleanup-branches.md` を全文読み、棚卸し、削除条件、F26/F51、事後検査、
   引き渡し、自己改善の共通 dispatcher としてそのまま実行する。command が不在または読取不能なら停止する。
3. command の `$ARGUMENTS` は本 Skill に渡された対象限定と読み替える。未指定なら command の全量棚卸し契約に従う。
4. command と本 overlay が衝突する場合は、削除範囲が狭くなる安全側へ縮退して対象と未実行操作を報告する。

## Codex 固有の安全 overlay

- Claude 固有の `ExitWorktree` が使えると仮定しない。cwd を対象外へ固定できなければ F51 とし、
  現在の worktree directory の削除と prune を行わない。
- local `main` と primary worktree は無条件に保持する。
- `/proc/*/cwd` の miss は非使用の証拠に数えない。locked worktree と、この Codex session が作成・
  所有したと証明できない foreign worktree は inventory / report のみにし、unlock、directory 削除、
  prune を行わない。
- 各破壊操作の直前に dispatcher §2 と overlay の全 eligibility（ahead / cherry、clean、HEAD の
  main 包含、recent、lock、canonical path、local `main` / primary、ownership / foreign、
  `/proc/*/cwd` の process residency）を再評価する。unknown、棚卸し後の change、新しい process
  residency のいずれかがあればその操作を停止する。
- `git worktree prune --dry-run --verbose` は報告用 preview としてだけ実行する。Codex は real
  `git worktree prune` を実行せず、preview と残作業を人間へ引き渡す。
- sandbox または shared Git metadata の権限が不足する場合は権限を拡大しない。安全に実行できた操作、
  対象、未実行操作を人間へ返す。

## 境界を守る

Codex には `hooks/README.md` の PreToolUse hook が未配線であるため、hook が発火したと主張せず、
同文書の保護境界を手動で守る。push と remote branch 操作は人間に残す。

今回の実行で記載と実挙動の食い違い、新しい罠、手順不足を実測した場合だけ
`docs/skill-self-improvement.md` の cleanup-branches routing と commit 境界に従う。
"""
_SYNTHETIC_CLEANUP_OPENAI_YAML = """interface:
  display_name: "Cleanup Branches"
  short_description: "Izanagi のマージ済み branch と worktree を安全に整理"
  default_prompt: "Use $cleanup-branches to safely clean up merged local branches and worktrees."

policy:
  allow_implicit_invocation: false
"""
_SYNTHETIC_CLEANUP_COMMAND = """---
description: マージ済みブランチと worktree を安全手順で掃除する (submodule 罠対応、push 系はユーザー引き渡し)
argument-hint: [任意: 削除対象の限定 (ブランチ名/worktree 名)。省略時は全量棚卸しして安全なものだけ削除]
---

ブランチ・worktree の掃除を行う (クラス 2)。削除は不可逆に近いため、安全条件を満たすものだけを
消し、迷ったら残して報告する。対象限定の引数: $ARGUMENTS

## 1. 棚卸し (削除の前に全量を見る)

- `git worktree list` と `git branch -a` を列挙し、各ローカルブランチの `git rev-list --count
  main..<b>` (ahead) / `<b>..main` (behind) を出す
- 各 worktree の `git status --short` を確認する (未コミット差分の有無)
- ahead>0 のブランチは `git cherry main <b>` を出す。rebase / cherry-pick で取り込まれた側は
  ahead>0 のまま残るため、ahead だけでは取り残しの有無を判定できない。`+` 行が真の取り残しで、
  ファイルが main に無ければ取り込み漏れとして §5 で報告する
- `python3 tools/audit_dangling_commits.py` rc0削除/1§5報告・救出判断/2実行不能・削除停止

## 2. 安全条件 (満たさないものは削除せず報告に回す)

- ブランチ: **ahead=0 (main に取り込み済み) のみ削除**。`git branch -d` を使う (`-D` は使わない —
  -d が拒否したら取り込み漏れの兆候なので止まって報告)
- worktree: クリーン (未コミット差分なし) かつ HEAD が main に取り込み済みのもののみ。
  他セッション使用中の可能性 (自分が作っていない・最近更新) は推測せず `/proc/*/cwd` の
  readlink 走査で実測し、滞在プロセスあり・HEAD 直近 (目安 1h) は残す。迷ったらユーザー確認へ
- 自分がその worktree の中で作業している場合は、先に main checkout 側へ抜けてから操作する

## 3. worktree の削除手順 (F26)

submodule の gitlink を含む worktree は `git worktree remove` を使わず、F26 の安全手順を使う:

1. `git -C <worktree> checkout --detach` (ブランチを解放)
2. `git branch -d <branch>` (取り込み済み確認の上で)
3. ディレクトリを削除して `git worktree prune`

**`git submodule deinit` は使わない**。誤って実行した場合は
`git submodule update --init external/ccbench` で復元する。正本は `docs/failures.md` F26。

ExitWorktree の remove を `discard_changes: true` で押し切らない。main が当該 commit を含むことを
`git log` で確認し、`action: keep` で抜け、本節の手動手順で畳む。
cwd 固定の背景セッション (ExitWorktree が no-op・cd 非持続) では、自分が居る
worktree の削除と prune を行わず、detach → branch -d → unlock まで実施して
残りを引き渡す (F51)。

## 4. 事後検査

- `git worktree list` / `git branch` が期待どおりか
- `git submodule status` — main checkout の external/ccbench が `-` prefix なし (初期化済み) で
  pin されたコミットに一致すること
- `git status` がクリーンであること

## 5. ユーザー引き渡し (AI は push しない)

リモートブランチの削除 (`git push origin --delete <b>`) と main の push は行わず、対象を列挙して
ユーザーに提示する。削除しなかったブランチ・worktree はその理由 (ahead>0、dirty 等) と併せて報告する。
記録はセッションの通常規律 (worklog) に従う。

## 6. スキル自己改善 (発火条件つき)

今回の実行でスキル記載と実挙動の食い違い・新しい罠・手順不足を実測した場合だけ発火する。
発火したら `docs/skill-self-improvement.md` を読み、`cleanup-branches` の routing と commit 契約に従う。
発火しなければ本文を変更しない。
"""


def _write(root: str, rel: str, content: str) -> None:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _write_bytes(root: str, rel: str, content: bytes) -> None:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)


def _enumerated_rels() -> list[str]:
    """check_docs 本体の _ENUMERATED_DOCS を実 REPO 相対パスへ落とす (増減に追従)。"""
    return sorted(str(p.relative_to(check_docs.REPO)) for p in check_docs._ENUMERATED_DOCS)


def _write_backlog_docs(
    root: str,
    worklog_text: str = _CLEAN_WORKLOG,
    phase3_text: str = _CLEAN_PHASE3,
) -> None:
    _write(root, os.path.join("docs", "worklog.md"), worklog_text)
    _write(root, os.path.join("docs", "phase3.md"), phase3_text)


def _write_empty_spool_layout(root: str) -> None:
    """validate_spool_tree が受理する pending 0 件の正規 layout を作る。"""

    _write(root, "docs/spool/README.md", "# synthetic spool\n")
    _write(root, "docs/spool/FOLDED.md", "# synthetic folded receipts\n")
    for ledger in ("worklog", "decisions", "failures"):
        _write(
            root,
            f"docs/spool/{ledger}/README.md",
            f"# synthetic {ledger} spool\n",
        )


def _archive_readme(*names: str) -> str:
    all_names = (_PLACEHOLDER_ARCHIVE_NAME, *names)
    return (
        "# archive\n\n## 現在の収容物\n\n"
        + "".join(f"- `{name}`\n" for name in all_names)
    )


def _write_command_guard_docs(root: str) -> None:
    def refs(pairs: set[tuple[str, str]] | frozenset[tuple[str, str]]) -> str:
        grouped: dict[str, list[str]] = {}
        for path, section in sorted(pairs):
            grouped.setdefault(path, []).append(section)
        chunks = []
        for path, sections in grouped.items():
            if path == "docs/skill-self-improvement.md":
                chunks.append(f"`{path}` の全節")
            elif (
                path == "docs/dev-wave/operations.md"
                and sections == [
                    f"DW-O{i:02d}"
                    for i in check_docs._OPERATION_NUMBERS
                ]
            ):
                chunks.append(
                    f"`{path}`: `DW-O01`〜`DW-O06`, `DW-O08`〜`DW-O14`, "
                    "`DW-O16`〜`DW-O20`, `DW-O23`"
                )
            else:
                ids = ", ".join(f"`{section}`" for section in sections)
                chunks.append(f"`{path}`: {ids}")
        return "; ".join(chunks)

    stage_rows = []
    for key, pairs in check_docs.STAGE_DISPATCH_CONTRACT.items():
        display_key = (
            f"{key} preflight" if key in {"段 2", "段 3", "段 8"} else key
        )
        grouped: dict[str, set[tuple[str, str]]] = {}
        for path, section in pairs:
            grouped.setdefault(path, set()).add((path, section))
        for path, path_pairs in sorted(grouped.items()):
            if key == "段 6" and path == "docs/dev-wave/workers.md":
                s05 = {
                    pair for pair in path_pairs
                    if pair[1].startswith("DW-S05-")
                }
                s06 = path_pairs - s05
                stage_rows.append(f"| {display_key} | {refs(s05)} |")
                stage_rows.append(f"| {display_key} | {refs(s06)} |")
            else:
                stage_rows.append(f"| {display_key} | {refs(path_pairs)} |")
    condition_rows = "\n".join(
        f"| {key} | synthetic | {refs(pairs)} |"
        for key, pairs in check_docs.CONDITION_DISPATCH_CONTRACT.items()
    )
    dev_wave = f"""---
description: synthetic dev-wave
argument-hint: [synthetic]
disable-model-invocation: true
---

$ARGUMENTS

条件には最遅読了段がある。`DW-O08`、`DW-O09`、`DW-O10` は段 1 brief 前、
`DW-O13` は段 2 プラン前が期限である。期限後に成立したら成果物を invalidate し、
前者は段 1 brief、後者は段 2 から再実行する。巻き戻し後は段・条件を再評価し、
旧成果物を流用してはならない。

コード・テスト・実行可能資材（以下「実装面」）は軽量版でも
Codex `role=author` が書き、親は実装面を直接編集せず統合する。

## 段 dispatch

| 段 | 参照 |
|---|---|
{chr(10).join(stage_rows)}

段 6 で fix を codex へ再投する子は、`DW-S05-A`、`DW-S05-B`、`DW-S05-C` を
全文継承する。段 6 時点で成立している全条件の `DW-Oxx` も fix 操作の直前に読む。

## 条件 dispatch

| # | 条件 | 参照 |
|---|---|---|
{condition_rows}
"""
    cleanup = _SYNTHETIC_CLEANUP_COMMAND
    rulings = """---
description: synthetic rulings
argument-hint: [synthetic]
---

$ARGUMENTS
docs/skill-self-improvement.md
"""
    _write(root, ".claude/commands/dev-wave.md", dev_wave)
    _write(root, "tools/dev_wave_land.py", "# synthetic land helper\n")
    _write(root, ".claude/commands/cleanup-branches.md", cleanup)
    _write(root, ".claude/commands/rulings.md", rulings)
    codex_skill = """---
name: dev-wave
description: synthetic Codex dev-wave skill
---

# Dev Wave

    """ + "\n".join(check_docs.CODEX_DEV_WAVE_SKILL_LITERALS) + "\n" + (
        check_docs.CODEX_DEV_WAVE_STAGE9_LAND_LITERAL + "\n"
    )
    _write(root, ".agents/skills/dev-wave/SKILL.md", codex_skill)
    _write(
        root,
        ".agents/skills/dev-wave/agents/openai.yaml",
        check_docs.CODEX_DEV_WAVE_OPENAI_YAML,
    )
    codex_rulings_skill = """---
name: rulings
description: synthetic Codex rulings skill
---

# Rulings

""" + "\n".join(check_docs.CODEX_RULINGS_SKILL_LITERALS) + "\n"
    _write(root, ".agents/skills/rulings/SKILL.md", codex_rulings_skill)
    _write(
        root,
        ".agents/skills/rulings/agents/openai.yaml",
        check_docs.CODEX_RULINGS_OPENAI_YAML,
    )
    _write(
        root,
        ".agents/skills/cleanup-branches/SKILL.md",
        _SYNTHETIC_CLEANUP_SKILL,
    )
    _write(
        root,
        ".agents/skills/cleanup-branches/agents/openai.yaml",
        _SYNTHETIC_CLEANUP_OPENAI_YAML,
    )

    for rel, sections in check_docs.REQUIRED_REFERENCE_SECTIONS.items():
        rendered_sections = []
        for section in sorted(sections):
            body = "body"
            if rel == "docs/dev-wave/workers.md" and section == "DW-S02":
                body += "\n\n" + check_docs.DEV_WAVE_DW_S02_REASONING_MAX_LITERAL
            if rel == "docs/dev-wave/workers.md" and section == "DW-S03":
                body += "\n\n" + check_docs.DEV_WAVE_DW_S03_REASONING_MAX_LITERAL
            if rel == "docs/dev-wave/core.md" and section == "DW-S09":
                body += (
                    "\n\n"
                    + _S09_ACCEPTANCE_ORDER_LITERAL
                    + "\n"
                    + check_docs.DEV_WAVE_LAND_UNIQUE_ROUTE_LITERAL
                )
            if rel == "docs/dev-wave/operations.md" and section == "DW-O23":
                body += "\n\n`tools/dev_wave_land.py`"
            rendered_sections.append(f"## {section} — synthetic\n\n{body}")
        text = "# synthetic reference\n\n" + "\n\n".join(rendered_sections) + "\n"
        literals = check_docs.CODEX_FIRST_REFERENCE_LITERALS.get(rel, ())
        if literals:
            text += "\n" + "\n".join(literals) + "\n"
        _write(root, rel, text)

    self_doc = """# synthetic self

## 発火 gate

body

## routing

body

## command 入口の編集条件

body

## command 別の終端

### dev-wave

body

### cleanup-branches

body

### rulings

body

## 検査と commit 境界

body
"""
    _write(root, "docs/skill-self-improvement.md", self_doc)

    provenance_entry = """# synthetic provenance entry

## 条件 dispatch

| key | 発火条件 | 読む節 |
|---|---|---|
| correction | 固定 target の forward correction を扱う | `docs/provenance/correction.md`: `PR-C01`, `PR-C02`, `PR-C03` |
| message-file | commit 前に message を検査する | `docs/provenance/audit.md`: `PR-A01` |
| history | commit 後・別 range の履歴を監査する | `docs/provenance/audit.md`: `PR-A02`; `docs/provenance/correction.md`: `PR-C03` |
| analysis | provenance を比較や改善判断に使う | `docs/provenance/audit.md`: `PR-A03` |
"""
    correction = """# synthetic correction reference

## PR-C01 — synthetic

body

## PR-C02 — synthetic

body

## PR-C03 — synthetic

body
"""
    audit = """# synthetic audit reference

## PR-A01 — synthetic

body

## PR-A02 — synthetic

body

## PR-A03 — synthetic

body
"""
    _write(root, "docs/ai-provenance.md", provenance_entry)
    _write(root, "docs/provenance/correction.md", correction)
    _write(root, "docs/provenance/audit.md", audit)


def _write_dispatch_inventory_fixture(root: str) -> None:
    _write(root, "docs/pegasus-runbook.md", _SYNTHETIC_DISPATCH_RUNBOOK)
    _write(
        root,
        "tools/pegasus/dispatch_compute.py",
        _SYNTHETIC_DISPATCH_SOURCE,
    )
    shutil.copy(
        check_docs.REPO / "tools" / "pegasus_admission_registry.py",
        os.path.join(root, "tools", "pegasus_admission_registry.py"),
    )
    registry = {
        "schema_version": "pegasus-admission-registry/v1",
        "entries": _SYNTHETIC_ADMISSION_ENTRIES,
    }
    _write(
        root,
        "tools/pegasus/admission_registry.json",
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
    )
    _write(root, "tools/pegasus/README.md", _SYNTHETIC_ADMISSION_README)


def _assert_violation(root: str, *needles: str) -> subprocess.CompletedProcess:
    res = _run_check(root)
    assert res.returncode == 1, f"違反 fixture が赤にならなかった:\n{res.stdout}\n{res.stderr}"
    for needle in needles:
        assert needle in res.stdout, f"{needle!r} が finding にない:\n{res.stdout}"
    return res


def _build_min_repo() -> str:
    """check_docs が『違反なし』を返す最小合成 repo を tmp に作り、root を返す。

    trivial 内容 (行番号参照/現況再掲/pin literal/D 参照/パス参照をどれも含まない) と、
    保存則を満たす最小 worklog / 見送り台帳を用意し、baseline を違反なしにする。
    """
    root = tempfile.mkdtemp(prefix="izanagi_checkdocs_")
    # 実 check_docs.py を複製 — REPO は __file__ 由来なので tmp/tools/ に置くと tmp を指す。
    _dst = os.path.join(root, "tools", "check_docs.py")
    os.makedirs(os.path.dirname(_dst))
    shutil.copy(check_docs.__file__, _dst)
    shutil.copy(check_docs.REPO / "tools" / "spool_fold.py", os.path.dirname(_dst))
    _write_empty_spool_layout(root)

    # 手書き列挙 doc (LIVING_DOCS の glob 前スナップショット) を trivial 内容で用意。
    for rel in _enumerated_rels():
        _write(root, rel, "# placeholder living doc\n")

    # check_docs が main() 内で無条件に read するファイル群。
    _write(root, os.path.join("orchestrator", "campaign", "pin.py"),
           'CURRENT_PIN = "abc1234def5678"\n')
    _write(root, os.path.join("docs", "decisions.md"),
           "## D1 placeholder decision\n\n本文。\n")
    _write(root, os.path.join("docs", "archive", "README.md"),
           _archive_readme())
    _write(
        root,
        os.path.join("docs", "archive", _PLACEHOLDER_ARCHIVE_NAME),
        "# synthetic archive\n\n"
        "## 2026-07-24 (4) — 統合 E2E: 実 seal を official floor 経路に通す (D79(7) 部分閉鎖、branch worktree-dev-wave-e2e-real-seal、計測なし)\n\n"
        f"{_PLACEHOLDER_DEBT_ARCHIVE_ACCEPTANCE}\n"
        "\n"
        "## 2026-07-24 (5) — [T-086] PKG-2: FROZEN_MANIFEST exact key-set 暫定 assert (test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)\n\n"
        f"{_PLACEHOLDER_DEBT_WORKLOG}\n\n"
        "### 次の一手\n\n"
        f"{_PLACEHOLDER_WORKLOG_ENTRIES}",
    )
    _write(
        root,
        os.path.join("output", "insights", "2026-07-24_e2e-real-seal.md"),
        f"{_PLACEHOLDER_DEBT_INSIGHT}\n",
    )
    _write(
        root,
        os.path.join(
            "output",
            "insights",
            "2026-07-25_t068-t077-t078-closure-verbatim.md",
        ),
        f"{_PLACEHOLDER_MENTION_INSIGHT_A}\n"
        f"{_PLACEHOLDER_MENTION_INSIGHT_B}\n",
    )
    # backlog guard の必須構造。phase3.md は上の列挙 placeholder を上書きする。
    _write_backlog_docs(root)
    _write_command_guard_docs(root)
    _write_dispatch_inventory_fixture(root)
    return root


def _run_check(root: str, *, timeout: float | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, os.path.join(root, "tools", "check_docs.py")],
        capture_output=True, text=True,
        timeout=timeout,
    )


def _violation_count(res: subprocess.CompletedProcess) -> int:
    match = re.search(r"^check_docs: (\d+) 件の違反$", res.stdout, re.MULTILINE)
    assert match is not None, f"違反件数 header を解析できない:\n{res.stdout}"
    return int(match.group(1))


def _finding_set(res: subprocess.CompletedProcess) -> set[str]:
    return {
        line.removeprefix("  - ")
        for line in res.stdout.splitlines()
        if line.startswith("  - ")
    }


def _admission_findings(res: subprocess.CompletedProcess) -> list[str]:
    prefix = check_docs._ADMISSION_PREFIX
    return [
        line.removeprefix("  - ")
        for line in res.stdout.splitlines()
        if line.startswith(f"  - {prefix}")
    ]


def _assert_admission_count(
    root: str,
    expected: int,
    *needles: str,
) -> subprocess.CompletedProcess:
    res = _run_check(root)
    admission = _admission_findings(res)
    assert len(admission) == expected, (
        f"admission finding 件数が不一致: expected={expected}, "
        f"actual={admission}\nstdout={res.stdout}\nstderr={res.stderr}"
    )
    for finding in admission:
        assert finding.startswith(check_docs._ADMISSION_PREFIX)
    for needle in needles:
        assert any(needle in finding for finding in admission), (
            f"{needle!r} が admission finding にない: {admission}"
        )
    if expected:
        assert res.returncode == 1, res.stdout
    assert "Traceback" not in res.stdout + res.stderr
    return res


def _assert_admission_exact(
    root: str,
    *details: str,
) -> subprocess.CompletedProcess:
    res = _run_check(root)
    expected = {check_docs._ADMISSION_PREFIX + detail for detail in details}
    actual = set(_admission_findings(res))
    assert actual == expected, (
        f"admission finding 集合が不一致: expected={sorted(expected)}, "
        f"actual={sorted(actual)}\nstdout={res.stdout}\nstderr={res.stderr}"
    )
    assert len(_admission_findings(res)) == len(expected), (
        f"admission finding に重複がある: {_admission_findings(res)}"
    )
    assert res.returncode == (1 if expected else 0), res.stdout
    assert "Traceback" not in res.stdout + res.stderr
    return res


def _rewrite_registry(root: str, mutate) -> None:
    rel = "tools/pegasus/admission_registry.json"
    with open(os.path.join(root, rel), encoding="utf-8") as stream:
        document = json.load(stream)
    mutate(document)
    _write(
        root,
        rel,
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
    )


# ===== baseline: 合成 repo は違反なし (positive control の土台) =====

def test_synthetic_repo_baseline_clean():
    root = _build_min_repo()
    try:
        res = _run_check(root)
        assert res.returncode == 0, f"baseline が違反ありになった:\n{res.stdout}\n{res.stderr}"
        assert "違反なし" in res.stdout, res.stdout
        assert _admission_findings(res) == []
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_registry_load_failures_are_one_fail_closed_finding():
    cases = {
        "json missing": lambda root: os.remove(
            os.path.join(root, "tools/pegasus/admission_registry.json")
        ),
        "loader missing": lambda root: os.remove(
            os.path.join(root, "tools/pegasus_admission_registry.py")
        ),
        "invalid schema": lambda root: _rewrite_registry(
            root,
            lambda document: document.__setitem__("schema_version", "broken"),
        ),
        "unknown class": lambda root: _rewrite_registry(
            root,
            lambda document: document["entries"][
                "tools/pegasus/collect_receipt.py"
            ].__setitem__("class", "mystery"),
        ),
    }
    for label, mutate in cases.items():
        root = _build_min_repo()
        try:
            mutate(root)
            _assert_admission_count(root, 1, "canonical registry を確定できない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_loader_executes_source_even_with_unchecked_stale_pyc():
    """unchecked pyc が失敗しても、現 source の正常動作を採る。"""
    root = _build_min_repo()
    try:
        rel = "tools/pegasus_admission_registry.py"
        loader = os.path.join(root, rel)
        source = _read(root, rel)
        _write(root, rel, "raise SystemExit(0)\n")
        py_compile.compile(
            loader,
            doraise=True,
            invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
        )
        _write(root, rel, source)

        result = _run_check(root)
        assert result.returncode == 0, (
            f"unchecked stale pyc が source より優先された:\n"
            f"{result.stdout}\n{result.stderr}"
        )
        assert "違反なし" in result.stdout, result.stdout
        assert _admission_findings(result) == []
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_loader_system_exit_never_evaporates_checker():
    loaders = {
        "top level": "raise SystemExit(0)\n",
        "function": (
            "def load_admission_registry(repo_root):\n"
            "    raise SystemExit(0)\n"
        ),
    }
    for label, source in loaders.items():
        root = _build_min_repo()
        try:
            _write(root, "tools/pegasus_admission_registry.py", source)
            result = _assert_admission_count(
                root,
                1,
                "canonical registry を確定できない",
                "SystemExit",
            )
            assert result.returncode == 1, f"{label}: {result.stdout}"
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_poisoned_exception_string_never_evaporates_checker():
    root = _build_min_repo()
    try:
        _write(
            root,
            "tools/pegasus_admission_registry.py",
            "class Poisoned(BaseException):\n"
            "    def __str__(self):\n"
            "        raise SystemExit(0)\n\n"
            "def load_admission_registry(repo_root):\n"
            "    raise Poisoned()\n",
        )
        _assert_admission_exact(
            root,
            "canonical registry を確定できない — Poisoned",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_outer_wrapper_fail_closed_on_poisoned_subchecker():
    root = _build_min_repo()
    try:
        checker = "tools/check_docs.py"
        source = _read(root, checker)
        needle = "def _check_admission_runbook(\n"
        replacement = (
            "def _check_admission_runbook(\n"
            "    text: str,\n"
            "    registry: dict[str, dict[str, str]],\n"
            "    findings: list[str],\n"
            ") -> None:\n"
            "    class Poisoned(BaseException):\n"
            "        def __str__(self):\n"
            "            raise SystemExit(0)\n"
            "    raise Poisoned()\n\n"
            "def _disabled_check_admission_runbook(\n"
        )
        assert source.count(needle) == 1
        _write(root, checker, source.replace(needle, replacement, 1))
        _assert_admission_exact(
            root,
            "admission checker 内部失敗を fail-closed 化 — Poisoned",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_projection_mutations_each_have_one_primary_finding():
    collect_row = (
        "| `tools/pegasus/collect_receipt.py` | `unknown` | "
        "`unmeasured synthetic input` |"
    )
    smoke_row = (
        "| `tools/pegasus/smoke_probe.sh` | `dispatch-required` | "
        "`static job-body classification` |"
    )
    extra_row = "| `tools/pegasus/extra.py` | `unknown` | `unmeasured` |"
    cases = {
        "row deletion": lambda text: text.replace(collect_row + "\n", "", 1),
        "row addition": lambda text: text.replace(smoke_row, smoke_row + "\n" + extra_row, 1),
        "class change": lambda text: text.replace(
            collect_row,
            collect_row.replace("`unknown`", "`local-ok`"),
            1,
        ),
        "evidence change": lambda text: text.replace(
            collect_row,
            collect_row.replace("unmeasured synthetic input", "changed evidence"),
            1,
        ),
        "duplicate": lambda text: text.replace(collect_row, collect_row + "\n" + collect_row, 1),
        "malformed": lambda text: text.replace(collect_row, "| `tools/pegasus/collect_receipt.py` | `unknown` |", 1),
        "malformed header": lambda text: text.replace(
            "| path | class | evidence |",
            "| path | class |",
            1,
        ),
        "malformed separator": lambda text: text.replace(
            "|---|---|---|",
            "|---|--|---|",
            1,
        ),
        "escaped pipe": lambda text: text.replace(
            collect_row,
            collect_row.replace("synthetic input", "synthetic \\| input"),
            1,
        ),
        "broken code span": lambda text: text.replace(
            collect_row,
            collect_row.replace("`unmeasured synthetic input`", "`unmeasured synthetic input"),
            1,
        ),
        "moved section": lambda text: text.replace(
            _SYNTHETIC_PROJECTION_TABLE + "\n\n",
            "",
            1,
        ).replace("### 7.1 synthetic next section", "### 7.1 synthetic next section\n\n" + _SYNTHETIC_PROJECTION_TABLE, 1),
        "fenced hidden": lambda text: text.replace(
            _SYNTHETIC_PROJECTION_TABLE,
            "```text\n" + _SYNTHETIC_PROJECTION_TABLE + "\n```",
            1,
        ),
        "comment hidden": lambda text: text.replace(
            _SYNTHETIC_PROJECTION_TABLE,
            "<!--\n" + _SYNTHETIC_PROJECTION_TABLE + "\n-->",
            1,
        ),
    }
    for label, mutate in cases.items():
        root = _build_min_repo()
        try:
            rel = "docs/pegasus-runbook.md"
            _write(root, rel, mutate(_read(root, rel)))
            _assert_admission_count(root, 1)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_registry_mutations_have_exact_attributed_finding_sets():
    cases = {
        "class": (
            lambda document: document["entries"][
                "tools/pegasus/collect_receipt.py"
            ].__setitem__("class", "local-ok"),
            {
                "runbook §7.0 投影表が registry と集合完全一致しない — "
                "registry_only=[('tools/pegasus/collect_receipt.py', 'local-ok', "
                "'unmeasured synthetic input')], "
                "runbook_only=[('tools/pegasus/collect_receipt.py', 'unknown', "
                "'unmeasured synthetic input')]",
                "unknown 表の admission 説明が registry と不整合 — "
                "tools/pegasus/collect_receipt.py",
                "Pegasus README 宣言表の class が registry と不一致 — "
                "tools/pegasus/collect_receipt.py",
            },
        ),
        "evidence": (
            lambda document: document["entries"][
                "tools/pegasus/submit_certify.sh"
            ].__setitem__("evidence", "runbook §7.0 実測"),
            {
                "runbook §7.0 投影表が registry と集合完全一致しない — "
                "registry_only=[('tools/pegasus/submit_certify.sh', 'local-ok', "
                "'runbook §7.0 実測')], "
                "runbook_only=[('tools/pegasus/submit_certify.sh', 'local-ok', "
                "'legacy-admitted (未実測)')]",
                "unknown 表の admission 説明が registry と不整合 — "
                "tools/pegasus/submit_certify.sh",
                "runbook §7.0 実測表の path 集合が registry と不一致 — "
                "registry=['tools/pegasus/fetch_third_party.py', "
                "'tools/pegasus/submit_certify.sh'], "
                "runbook=['tools/pegasus/fetch_third_party.py']",
            },
        ),
    }
    for label, (mutate, expected) in cases.items():
        root = _build_min_repo()
        try:
            _rewrite_registry(root, mutate)
            _assert_admission_exact(root, *sorted(expected))
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_unknown_table_rejects_non_unknown_and_incomplete_legacy_rows():
    collect = "| `tools/pegasus/collect_receipt.py` | 入力が未計測 |"
    legacy = (
        "| `tools/pegasus/submit_certify.sh` | registry 上は `local-ok` / "
        "`legacy-admitted (未実測)` として grandfather 済み |"
    )
    cases = {
        "dispatch required": lambda text: text.replace(
            collect,
            "| `tools/pegasus/smoke_probe.sh` | 入力が未計測 |",
            1,
        ),
        "missing local-ok": lambda text: text.replace(
            legacy,
            legacy.replace("`local-ok` / ", ""),
            1,
        ),
        "missing exact evidence": lambda text: text.replace(
            legacy,
            legacy.replace("`legacy-admitted (未実測)`", "legacy entry"),
            1,
        ),
    }
    for label, mutate in cases.items():
        root = _build_min_repo()
        try:
            rel = "docs/pegasus-runbook.md"
            _write(root, rel, mutate(_read(root, rel)))
            _assert_admission_count(root, 1, "unknown 表")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_unknown_table_requires_grandfather_warning_golden():
    row = (
        "| `tools/pegasus/submit_silo_ladder_rung1.sh` | registry 上は "
        "`local-ok` / `legacy-admitted (未実測)` として grandfather 済み |"
    )
    cases = {
        "deleted": (
            lambda text: text.replace(row + "\n", "", 1),
            "unknown 表に必須 grandfather 警告がない — "
            "missing=['tools/pegasus/submit_silo_ladder_rung1.sh']",
        ),
        "empty": (
            lambda text: re.sub(
                r"(?ms)(\| 経路 \| なぜ `unknown` か \|\n\|---\|---\|)\n.*?"
                r"(?=\n\n\| 経路 \| 観測ピーク)",
                r"\1",
                text,
                count=1,
            ),
            "unknown 表に必須 grandfather 警告がない — "
            "missing=['tools/pegasus/submit_silo_ladder_rung1.sh']",
        ),
        "double slash": (
            lambda text: text.replace(
                row,
                row.replace(
                    "tools/pegasus/submit_silo_ladder_rung1.sh",
                    "tools//pegasus/submit_silo_ladder_rung1.sh",
                ),
                1,
            ),
            "unknown 表に非 canonical Pegasus path がある — "
            "['tools//pegasus/submit_silo_ladder_rung1.sh']",
        ),
        "case change": (
            lambda text: text.replace(
                row,
                row.replace(
                    "tools/pegasus/submit_silo_ladder_rung1.sh",
                    "tools/Pegasus/submit_silo_ladder_rung1.sh",
                ),
                1,
            ),
            "unknown 表に非 canonical Pegasus path がある — "
            "['tools/Pegasus/submit_silo_ladder_rung1.sh']",
        ),
        "fullwidth slash": (
            lambda text: text.replace(
                row,
                row.replace(
                    "tools/pegasus/submit_silo_ladder_rung1.sh",
                    "tools／pegasus／submit_silo_ladder_rung1.sh",
                ),
                1,
            ),
            "unknown 表に非 canonical Pegasus path がある — "
            "['tools／pegasus／submit_silo_ladder_rung1.sh']",
        ),
    }
    for label, (mutate, expected) in cases.items():
        root = _build_min_repo()
        try:
            rel = "docs/pegasus-runbook.md"
            _write(root, rel, mutate(_read(root, rel)))
            _assert_admission_exact(root, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_measured_table_requires_exact_registry_path_set():
    first = "| `tools/pegasus/fetch_third_party.py fetch` | 10 MiB | 138 MiB | local-ok |"
    inherited = "| 同 `fetch` | 9 MiB | 137 MiB | local-ok |"
    cases = {
        "missing": (
            lambda text: text.replace(first + "\n" + inherited, "", 1),
            "runbook §7.0 実測表の path 集合が registry と不一致 — "
            "registry=['tools/pegasus/fetch_third_party.py'], runbook=[]",
        ),
        "extra": (
            lambda text: text.replace(
                inherited,
                inherited + "\n| `tools/pegasus/smoke_probe.sh run` | 1 MiB | 129 MiB | local-ok |",
                1,
            ),
            "runbook §7.0 実測表の path 集合が registry と不一致 — "
            "registry=['tools/pegasus/fetch_third_party.py'], "
            "runbook=['tools/pegasus/fetch_third_party.py', 'tools/pegasus/smoke_probe.sh']",
        ),
        "non local classification": (
            lambda text: text.replace(
                first,
                first.replace("local-ok", "unknown"),
                1,
            ),
            "runbook §7.0 実測表に非 local-ok 行がある",
        ),
    }
    for label, (mutate, expected) in cases.items():
        root = _build_min_repo()
        try:
            rel = "docs/pegasus-runbook.md"
            _write(root, rel, mutate(_read(root, rel)))
            _assert_admission_exact(root, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_runbook_orphan_pipe_row_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        text = _read(root, rel).replace(
            "\n### 7.1 synthetic next section",
            "\n\n| orphan row |\n\n### 7.1 synthetic next section",
            1,
        )
        _write(root, rel, text)
        _assert_admission_count(root, 1, "orphan row")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_readme_declaration_and_fenced_target_mutations_are_rejected():
    collect = "| `tools/pegasus/collect_receipt.py` | `compute-only` | `unknown` |"
    fetch = "| `tools/pegasus/fetch_third_party.py` | `login-direct` | `local-ok` |"
    smoke = "| `tools/pegasus/smoke_probe.sh` | `qsub-job-body` | `dispatch-required` |"
    submit = "| `tools/pegasus/submit_certify.sh` | `login-direct` | `local-ok` |"
    cases = {
        "coverage deletion": lambda text: text.replace(collect + "\n", "", 1),
        "login direct non-local": lambda text: text.replace(
            smoke,
            smoke.replace("`qsub-job-body`", "`login-direct`"),
            1,
        ),
        "qsub local": lambda text: text.replace(
            submit,
            submit.replace("`login-direct`", "`qsub-job-body`"),
            1,
        ),
        "unregistered path": lambda text: text.replace(
            fetch,
            fetch + "\n| `tools/pegasus/unregistered.py` | `compute-only` | `unknown` |",
            1,
        ),
        "variable target": lambda text: text.replace(
            "qsub tools/pegasus/smoke_probe.sh",
            "qsub tools/pegasus/smoke_probe.sh\nqsub \"$P/pegasus/smoke_probe.sh\"",
            1,
        ),
        "invalid site": lambda text: text.replace(
            collect,
            collect.replace("`compute-only`", "`somewhere`"),
            1,
        ),
        "class mismatch": lambda text: text.replace(
            collect,
            collect.replace("`unknown`", "`dispatch-required`"),
            1,
        ),
        "duplicate": lambda text: text.replace(fetch, fetch + "\n" + fetch, 1),
        "malformed": lambda text: text.replace(fetch, "| `tools/pegasus/fetch_third_party.py` | `login-direct` |", 1),
        "hidden": lambda text: text.replace(
            "| path | 手順上の実行 site | registry class |\n|---|---|---|",
            "```text\n| path | 手順上の実行 site | registry class |\n|---|---|---|",
            1,
        ).replace(submit, submit + "\n```", 1),
    }
    for label, mutate in cases.items():
        root = _build_min_repo()
        try:
            rel = "tools/pegasus/README.md"
            _write(root, rel, mutate(_read(root, rel)))
            _assert_admission_count(root, 1)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_readme_site_tags_and_three_site_values_are_exact():
    qsub_tag = "# admission-site: qsub-job-body"
    qsub_command = "qsub tools/pegasus/smoke_probe.sh"
    login_tag = "# admission-site: login-direct"
    collect_row = "| `tools/pegasus/collect_receipt.py` | `compute-only` | `unknown` |"
    smoke_row = "| `tools/pegasus/smoke_probe.sh` | `qsub-job-body` | `dispatch-required` |"
    cases = {
        "missing tag": (
            lambda text: text.replace(qsub_tag + "\n", "", 1),
            lambda line: (
                "Pegasus README の registry 実行体を含む fenced command に "
                f"admission-site tag がない — line={line}"
            ),
        ),
        "duplicate tag": (
            lambda text: text.replace(qsub_tag, qsub_tag + "\n" + qsub_tag, 1),
            lambda line: (
                "Pegasus README の fenced block に admission-site tag が重複 — "
                f"line={line}"
            ),
        ),
        "tag not first": (
            lambda text: text.replace(qsub_tag, "\n" + qsub_tag, 1),
            lambda line: (
                "Pegasus README の admission-site tag が fenced block の先頭行でない — "
                f"line={line}"
            ),
        ),
        "unknown tag": (
            lambda text: text.replace(qsub_tag, "# admission-site: nowhere", 1),
            lambda line: "Pegasus README の admission-site tag が閉集合外 — nowhere",
        ),
        "qsub path is not qsub argument": (
            lambda text: text.replace(qsub_command, qsub_command.replace("qsub", "bash"), 1),
            lambda line: (
                "Pegasus README の qsub-job-body 実行体が qsub 引数でない — "
                "tools/pegasus/smoke_probe.sh"
            ),
        ),
        "qsub declaration has no qsub argument": (
            lambda text: text.replace(qsub_command + "\n", "", 1),
            lambda line: (
                "Pegasus README の qsub-job-body 宣言集合が qsub 引数集合と不一致 — "
                "declaration=['tools/pegasus/smoke_probe.sh'], qsub=[]"
            ),
        ),
        "site swap": (
            lambda text: text.replace(
                collect_row,
                collect_row.replace("`compute-only`", "`qsub-job-body`"),
                1,
            ).replace(
                smoke_row,
                smoke_row.replace("`qsub-job-body`", "`compute-only`"),
                1,
            ),
            lambda line: (
                "Pegasus README の fenced command site が宣言表と不一致 — "
                "path=tools/pegasus/smoke_probe.sh, tag=qsub-job-body, "
                "declaration=compute-only"
            ),
        ),
        "compute path in login block": (
            lambda text: text.replace(
                login_tag,
                login_tag + "\npython3 tools/pegasus/collect_receipt.py",
                1,
            ),
            lambda line: (
                "Pegasus README の fenced command site が宣言表と不一致 — "
                "path=tools/pegasus/collect_receipt.py, tag=login-direct, "
                "declaration=compute-only"
            ),
        ),
    }
    for label, (mutate, expected_for_line) in cases.items():
        root = _build_min_repo()
        try:
            rel = "tools/pegasus/README.md"
            original = _read(root, rel)
            first_line = original[:original.index("```bash")].count("\n") + 2
            _write(root, rel, mutate(original))
            _assert_admission_exact(root, expected_for_line(first_line))
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_readme_rejects_empty_and_noncanonical_path_surfaces():
    table_rows = "\n".join(
        line
        for line in _SYNTHETIC_ADMISSION_README.splitlines()
        if line.startswith("| `tools/pegasus/")
    )
    command = "qsub tools/pegasus/smoke_probe.sh"
    cases = {
        "empty declaration": (
            lambda text: text.replace(table_rows + "\n", "", 1),
            "Pegasus README 宣言表が空である",
        ),
        "double slash": (
            lambda text: text.replace(command, command.replace("tools/", "tools//"), 1),
            "Pegasus README に非 canonical Pegasus path がある — "
            "['tools//pegasus/smoke_probe.sh']",
        ),
        "case change": (
            lambda text: text.replace(command, command.replace("pegasus", "Pegasus"), 1),
            "Pegasus README に非 canonical Pegasus path がある — "
            "['tools/Pegasus/smoke_probe.sh']",
        ),
        "fullwidth slash": (
            lambda text: text.replace(
                command,
                command.replace("tools/pegasus/", "tools／pegasus／"),
                1,
            ),
            "Pegasus README に非 canonical Pegasus path がある — "
            "['tools／pegasus／smoke_probe.sh']",
        ),
    }
    for label, (mutate, expected) in cases.items():
        root = _build_min_repo()
        try:
            rel = "tools/pegasus/README.md"
            _write(root, rel, mutate(_read(root, rel)))
            _assert_admission_exact(root, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_readme_positive_command_and_negative_prose_controls_are_clean():
    root = _build_min_repo()
    try:
        text = _read(root, "tools/pegasus/README.md")
        assert "qsub tools/pegasus/smoke_probe.sh" in text
        assert "python3 tools/pegasus/fetch_third_party.py fetch" in text
        assert "login では拒否される" in text
        text += """

## 1. 非 admission の履歴資料

<!--
| path | 手順上の実行 site | registry class |
|---|---|---|
| historical | only | row |
-->

`tools/pegasus/smoke_probe.sh` は code span の参照であり command ではない。
https://example.invalid/tools/pegasus/smoke_probe.sh

```bash
tools/pegasus/collect_receipt.py はログインで実行してはならない
```

```text
過去事故の逐語: qsub tools/pegasus/smoke_probe.sh
```

```diff
- qsub tools/pegasus/smoke_probe.sh
+ python3 tools/pegasus/collect_receipt.py
```
"""
        _write(root, "tools/pegasus/README.md", text)
        runbook = _read(root, "docs/pegasus-runbook.md").replace(
            "### 7.1 synthetic next section",
            "<!--\n| unrelated | hidden |\n|---|---|\n| data | only |\n-->\n\n"
            "### 7.1 synthetic next section",
            1,
        )
        _write(root, "docs/pegasus-runbook.md", runbook)
        result = _assert_admission_count(root, 0)
        assert result.returncode == 0, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_main_call_cannot_be_removed_without_evaporation_control_failing():
    root = _build_min_repo()
    try:
        checker = "tools/check_docs.py"
        source = _read(root, checker)
        call = "    _check_pegasus_admission_docs(findings)\n"
        assert source.count(call) == 1
        _write(root, checker, source.replace(call, "", 1))
        runbook = "docs/pegasus-runbook.md"
        text = _read(root, runbook).replace(
            "`unmeasured synthetic input`",
            "`changed evidence`",
            1,
        )
        _write(root, runbook, text)
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
        assert _admission_findings(result) == []
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_main_rejects_schema_violation():
    """N19: main() の spool guard 呼出しを消す変異を schema 違反で殺す。"""

    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/spool/worklog/2026-08-02-wave-1.md",
            "---\n"
            "schema: broken-schema\n"
            "ledger: worklog\n"
            "authored: 2026-08-02\n"
            "wave: wave\n"
            "seq: 1\n"
            "title: synthetic\n"
            "---\n"
            "## 本文\n\nbody\n\n## 次の一手差分\n",
        )
        res = _assert_violation(root, "spool schema", "broken-schema")
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_import_failure_is_finding_without_traceback():
    """spool_fold import 失敗を握り潰さず fail-closed finding にする。"""

    root = _build_min_repo()
    try:
        os.remove(os.path.join(root, "tools", "spool_fold.py"))
        res = _assert_violation(root, "spool schema guard の import 失敗")
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_n20_spool_guard_rejects_active_transaction_in_git_repo():
    """N20: 実 Git worktree の transaction state 残存を必ず finding にする。"""

    root = _build_min_repo()
    try:
        subprocess.run(
            ["git", "-C", root, "init", "-q"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        resolved = subprocess.run(
            ["git", "-C", root, "rev-parse", "--git-path", "izanagi-spool-fold-state.json"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        state_path = resolved if os.path.isabs(resolved) else os.path.join(root, resolved)
        _write_bytes(root, os.path.relpath(state_path, root), b"{}\n")
        _assert_violation(root, "spool transaction-active", "fold transaction が active")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_git_marker_with_broken_rev_parse_fails_closed():
    """`.git` があるのに admin path を解決できない repo 候補は非 Git 扱いしない。"""

    root = _build_min_repo()
    try:
        _write(root, ".git", "gitdir: missing-admin-dir\n")
        _assert_violation(root, "spool transaction-state", "Git admin path を解決できない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_preservation_rule_still_rejects_implicit_drop():
    """N21: 既存 D70 保存則を弱める変異を active ID の暗黙脱落で殺す。"""

    root = _build_min_repo()
    try:
        worklog = _read(root, "docs/worklog.md")
        _write(
            root,
            "docs/worklog.md",
            worklog.replace("- [T-001] consumed\n\n", "", 1),
        )
        _assert_violation(root, "次の一手 ID [T-001]", "見送り台帳にもない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_raised_doc_budgets_still_reject_each_new_limit_and_aggregate():
    """N22: 引き上げ後の個別・合計予算を 1 byte 超える入力で gate 生存を固定する。"""

    assert check_docs.REFERENCE_LIMITS["docs/dev-wave/core.md"].max_bytes == 9_600
    assert check_docs.REFERENCE_LIMITS["docs/dev-wave/operations.md"].max_bytes == 8_400
    assert check_docs.DEV_WAVE_AGGREGATE_BYTES == 25_200
    assert check_docs.COMMAND_LIMITS[".claude/commands/rulings.md"].max_bytes == 5_000

    individual_cases = (
        ("docs/dev-wave/core.md", 9_601, "予算 9600 bytes"),
        ("docs/dev-wave/operations.md", 8_401, "予算 8400 bytes"),
        (".claude/commands/rulings.md", 5_001, "予算 5000 bytes"),
    )
    for rel, size, needle in individual_cases:
        root = _build_min_repo()
        try:
            _pad_to_bytes(root, rel, size)
            _assert_violation(root, rel, needle)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        aggregate_sizes = {
            "docs/dev-wave/core.md": 9_600,
            "docs/dev-wave/workers.md": 5_000,
            "docs/dev-wave/mutation.md": 3_750,
            "docs/dev-wave/operations.md": 6_851,
        }
        assert sum(aggregate_sizes.values()) == 25_201
        for rel, size in aggregate_sizes.items():
            _pad_to_bytes(root, rel, size)
        _assert_violation(root, "合計 25201 bytes", "hard ceiling 25200 bytes")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_empty_layout_is_clean():
    """pending 0 件の正規 spool layout は check_docs を塞がない。"""

    root = _build_min_repo()
    try:
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_valid_pending_fragment_is_clean():
    """正しい pending fragment の存在自体は finding にしない。"""

    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/spool/decisions/2026-08-02-wave-1.md",
            "---\n"
            "schema: izanagi-spool-v1\n"
            "ledger: decisions\n"
            "authored: 2026-08-02\n"
            "wave: wave\n"
            "seq: 1\n"
            "---\n"
            "## {{D:synthetic-decision}}. synthetic decision\n\nbody\n",
        )
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_unresolved_reference_propagates_to_main():
    """未解決 spool 参照は main() の rc=1 へ伝播する。"""

    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/spool/decisions/2026-08-02-wave-1.md",
            "---\n"
            "schema: izanagi-spool-v1\n"
            "ledger: decisions\n"
            "authored: 2026-08-02\n"
            "wave: wave\n"
            "seq: 1\n"
            "---\n"
            "## {{D:synthetic-decision}}. {{T:missing-task}} remains\n\nbody\n",
        )
        _assert_violation(root, "spool symbol-undefined", "{{T:missing-task}}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_missing_layout_is_finding():
    """docs/spool 自体の不在を黙って skip しない。"""

    root = _build_min_repo()
    try:
        shutil.rmtree(os.path.join(root, "docs", "spool"))
        _assert_violation(root, "docs/spool:1: spool spool-layout")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_symlink_and_unexpected_members_fail_closed():
    """spool 内の symlink・想定外 member を受理せず、finding 順も固定する。"""

    root = _build_min_repo()
    try:
        folded = os.path.join(root, "docs", "spool", "FOLDED.md")
        os.remove(folded)
        os.symlink("README.md", folded)
        _assert_violation(root, "spool regular-file", "symlink/非 regular file は不可")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        _write(root, "docs/spool/z-extra.md", "z\n")
        _write(root, "docs/spool/a-extra.md", "a\n")
        res = _assert_violation(root, "spool-member", "a-extra.md", "z-extra.md")
        assert res.stdout.index("a-extra.md") < res.stdout.index("z-extra.md")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_unexpected_validator_exception_is_finding():
    """validator の予期しない例外も traceback を漏らさず fail-closed にする。"""

    root = _build_min_repo()
    try:
        _write(
            root,
            "tools/spool_fold.py",
            "def validate_spool_tree(repo):\n"
            "    raise RuntimeError('synthetic validator crash')\n",
        )
        res = _assert_violation(
            root,
            "spool schema guard の実行失敗",
            "RuntimeError: synthetic validator crash",
        )
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_tree_is_excluded_from_all_legacy_doc_scans():
    """docs/spool/** は LIVING/placeholder/archive/handoff scan の対象外に保つ。"""

    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/spool/README.md",
            "# spool legacy-scan bait\n\n"
            "docs/README.md:999\n"
            "現在は Phase 999\n"
            "<反映>\n",
        )
        _write(
            root,
            "docs/spool/FOLDED.md",
            "# folded legacy-scan bait\n\n"
            "handoff 状態 header は意図的に置かない。\n",
        )
        _write(
            root,
            "docs/spool/worklog/README.md",
            "# archive scan bait\n\n## archive 形式でない H2\n",
        )
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "違反なし" in res.stdout
        assert "件の警告" not in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reference_limits_pin_adjudicated_caps():
    assert check_docs.REFERENCE_LIMITS == {
        "docs/dev-wave/core.md": check_docs.TextLimit(9_600),
        "docs/dev-wave/workers.md": check_docs.TextLimit(5_000),
        "docs/dev-wave/mutation.md": check_docs.TextLimit(3_750),
        "docs/dev-wave/operations.md": check_docs.TextLimit(8_400),
    }


def test_dev_wave_reference_budget_pins_cap_sum():
    assert sum(
        limit.max_bytes for limit in check_docs.REFERENCE_LIMITS.values()
    ) == 26_750


def test_dev_wave_reference_budget_pins_aggregate_ceiling():
    assert check_docs.DEV_WAVE_AGGREGATE_BYTES == 25_200
    assert check_docs.DEV_WAVE_REFERENCE_CAP_SUM_MAX_PERCENT == 110


def test_dev_wave_reference_cap_sum_rejects_above_110_percent():
    root = _build_min_repo()
    try:
        rel = "tools/check_docs.py"
        original = '"docs/dev-wave/core.md": TextLimit(9_600),'
        replacement = '"docs/dev-wave/core.md": TextLimit(10_571),'
        source = _read(root, rel)
        assert source.count(original) == 1
        _write(root, rel, source.replace(original, replacement, 1))

        _assert_findings(
            root,
            "docs/dev-wave/**: 個別 cap 総和 27721 bytes > aggregate ceiling "
            "25200 bytes の 1.10 倍 (27720 bytes)",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _dispatch_inventory_findings(
    result: subprocess.CompletedProcess,
) -> set[str]:
    return {
        finding
        for finding in _finding_set(result)
        if "dispatch inventory drift" in finding
    }


def _assert_tasks_source_mutation_rejected(suffix: str, needle: str) -> None:
    findings: list[str] = []
    inventory = check_docs._dispatch_inventory_from_source(
        _SYNTHETIC_DISPATCH_SOURCE + suffix,
        findings,
    )
    assert inventory is None
    assert len(findings) == 1, findings
    assert "TASKS 写像を静的に確定できない" in findings[0]
    assert needle in findings[0]


def test_dispatch_inventory_rejects_post_definition_assign():
    """定義後の ``TASKS = replacement`` 再束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected("\nTASKS = {}\n", "束縛/削除")


def test_dispatch_inventory_rejects_post_definition_annassign():
    """定義後の注釈付き ``TASKS: dict = ...`` 再束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected("\nTASKS: dict = {}\n", "束縛/削除")


def test_dispatch_inventory_rejects_post_definition_augassign():
    """定義後の ``TASKS |= replacement`` 変更変異を殺す。"""
    _assert_tasks_source_mutation_rejected("\nTASKS |= {}\n", "束縛/削除")


def test_dispatch_inventory_rejects_post_definition_subscript_assign():
    """定義後の ``TASKS[key] = spec`` 変更変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        '\nTASKS["extra"] = _TaskSpec(child_script=("tools", "extra.py"))\n',
        "要素/属性への書込み",
    )


def test_dispatch_inventory_rejects_post_definition_del():
    """定義後の ``del TASKS[key]`` 削除変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        '\ndel TASKS["tests"]\n',
        "要素/属性への書込み",
    )


def test_dispatch_inventory_rejects_post_definition_update():
    """定義後の ``TASKS.update(...)`` 変更変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        '\nTASKS.update({"extra": _TaskSpec(child_script=("tools", "extra.py"))})\n',
        "TASKS.update()",
    )


def test_dispatch_inventory_rejects_post_definition_pop():
    """定義後の ``TASKS.pop(...)`` 変更変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        '\nTASKS.pop("tests")\n',
        "TASKS.pop()",
    )


def test_dispatch_inventory_rejects_post_definition_for_binding():
    """定義後の ``for TASKS in ...`` 束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\nfor TASKS in ():\n    pass\n",
        "束縛/削除",
    )


def test_dispatch_inventory_rejects_post_definition_with_binding():
    """定義後の ``with ... as TASKS`` 束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\nwith context() as TASKS:\n    pass\n",
        "束縛/削除",
    )


def test_dispatch_inventory_rejects_post_definition_comprehension_binding():
    """定義後の comprehension target ``TASKS`` 束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\nshadow = [TASKS for TASKS in ()]\n",
        "束縛/削除",
    )


def test_dispatch_inventory_rejects_post_definition_import_binding():
    """定義後の import による ``TASKS`` 再束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\nfrom replacement import mapping as TASKS\n",
        "import による TASKS 再束縛",
    )


def test_dispatch_inventory_rejects_post_definition_globals_write():
    """定義後の ``globals()[\"TASKS\"] = ...`` 再束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        '\nglobals()["TASKS"] = {}\n',
        "動的 namespace 経由の書込み",
    )


def test_dispatch_inventory_rejects_tasks_alias_subscript_write():
    """``alias = TASKS; alias[key] = spec`` alias 書込み変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\nalias = TASKS\n"
        'alias["tests"] = _TaskSpec(child_script=("tools", "extra.py"))\n',
        "TASKS の alias 束縛",
    )


def test_dispatch_inventory_rejects_dict_update_through_tasks_alias():
    """``dict.update(alias, ...)`` による TASKS alias 変更変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\nalias = TASKS\n"
        "dict.update(alias, {"
        '"extra": _TaskSpec(child_script=("tools", "extra.py"))})\n',
        "TASKS の alias 束縛",
    )


def test_dispatch_inventory_rejects_tasks_as_mutating_call_argument():
    """``dict.update(TASKS, ...)`` 実引数 escape 変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\ndict.update(TASKS, {"
        '"extra": _TaskSpec(child_script=("tools", "extra.py"))})\n',
        "TASKS の実引数渡し",
    )


def test_dispatch_inventory_accepts_real_dispatcher_tasks_reads():
    """添字・membership・``tuple(TASKS)`` を alias と誤認する変異を殺す。"""
    source = (check_docs.REPO / "tools/pegasus/dispatch_compute.py").read_text()
    findings: list[str] = []
    assert check_docs._dispatch_inventory_from_source(source, findings) == {
        "tests": "tools/run_tests.py",
        "provenance": "tools/check_ai_provenance.py",
    }
    assert findings == []


def test_dispatch_inventory_raw_html_section_is_rejected():
    """§7.0 見出しと表を raw ``pre`` block 内へ移す変異を殺す。"""
    text = _SYNTHETIC_DISPATCH_RUNBOOK.replace(
        "### 7.0 判定基準はディレクトリではなくメモリ量\n",
        "<pre>\n### 7.0 判定基準はディレクトリではなくメモリ量\n",
        1,
    ).replace(
        "\n### 7.1 synthetic next section",
        "\n</pre>\n\n### 7.1 synthetic next section",
        1,
    )
    findings: list[str] = []
    assert check_docs._dispatch_inventory_from_runbook(text, findings) is None
    assert findings == [
        "tools/check_docs.py: dispatch inventory drift — "
        "docs/pegasus-runbook.md の `### 7.0` 節が 0 件"
    ]


def test_dispatch_inventory_wrong_parent_section_is_rejected():
    """§7.0 を無関係な親 ``## 8`` の配下へ移す変異を殺す。"""
    text = _SYNTHETIC_DISPATCH_RUNBOOK.replace(
        "### 7.0 判定基準はディレクトリではなくメモリ量",
        "## 8. unrelated\n\n### 7.0 判定基準はディレクトリではなくメモリ量",
        1,
    )
    findings: list[str] = []
    assert check_docs._dispatch_inventory_from_runbook(text, findings) is None
    assert findings == [
        "tools/check_docs.py: dispatch inventory drift — "
        "docs/pegasus-runbook.md の `### 7.0` が親 `## 7` の直下でない"
    ]


def test_dispatch_inventory_accepts_equivalent_markdown_spacing():
    """有効な見出し字下げと表セル空白を拒む過剰拒否変異を殺す。"""
    text = _SYNTHETIC_DISPATCH_RUNBOOK.replace(
        "## 7. synthetic execution policy",
        "  ## 7. synthetic execution policy",
        1,
    ).replace(
        "### 7.0 判定基準はディレクトリではなくメモリ量",
        "   ### 7.0　判定基準はディレクトリではなくメモリ量",
        1,
    ).replace(
        "| task | 子 script |",
        "|task      |子 script|",
        1,
    )
    findings: list[str] = []
    assert check_docs._dispatch_inventory_from_runbook(text, findings) == {
        "tests": "tools/run_tests.py",
        "provenance": "tools/check_ai_provenance.py",
    }
    assert findings == []


def test_dispatch_inventory_outer_pipe_less_added_row_is_rejected():
    """外周 pipe のない3行目を表終端として無視する変異を殺す。"""
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        text = _read(root, rel).replace(
            "| `provenance` | `tools/check_ai_provenance.py` |\n",
            "| `provenance` | `tools/check_ai_provenance.py` |\n"
            "`extra` | `tools/extra.py`\n",
            1,
        )
        _write(root, rel, text)
        result = _run_check(root)
        assert result.returncode == 1, result.stdout
        assert _dispatch_inventory_findings(result) == {
            "tools/check_docs.py: dispatch inventory drift — "
            "{task: child_script} が不一致 — TASKS_only=[], "
            "runbook_only=['extra'], child_script={}"
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_shared_top_level_items_are_unchanged_by_raw_html_prefix():
    """raw HTML block mask を共有トップレベル項目 scanner へ戻す変異を殺す。"""
    body = "- [T-001] visible item\n"
    prefix = "<x = >\n<x>\n"
    assert check_docs._top_level_ids(prefix + body) == check_docs._top_level_ids(body)


def test_shared_provenance_sections_are_unchanged_by_raw_html_prefix():
    """raw HTML block mask を共有 provenance scanner へ戻す変異を殺す。"""
    text = "## PR-A01 — visible\n\nbody\n"
    baseline = check_docs._visible_markdown_text(text)
    prefixed = check_docs._visible_markdown_text("<x = >\n<x>\n" + text)
    assert check_docs._reference_id_sections(prefixed, "PR-A01") == (
        check_docs._reference_id_sections(baseline, "PR-A01")
    )


def test_shared_condition_dispatch_is_unchanged_by_raw_html_prefix():
    """raw HTML block mask を共有 condition dispatch scanner へ戻す変異を殺す。"""
    text = """## 条件 dispatch

| key | 発火条件 | 読む節 |
|---|---|---|
| history | condition | `docs/provenance/audit.md`: `PR-A02` |
"""
    prefixed = "<x = >\n<x>\n" + text
    assert check_docs._condition_dispatch_table(prefixed, "条件 dispatch") == (
        check_docs._condition_dispatch_table(text, "条件 dispatch")
    )


def test_dispatch_inventory_current_mapping_has_no_findings():
    root = _build_min_repo()
    try:
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
        assert _dispatch_inventory_findings(result) == set()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_deleted_table_row_is_rejected():
    root = _build_min_repo()
    try:
        _rewrite_matching_lines(
            root,
            "docs/pegasus-runbook.md",
            lambda line: line.startswith("| `provenance` |"),
            lambda _line: "",
        )
        result = _assert_violation(root, "dispatch inventory drift")
        assert "TASKS_only=['provenance']" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reference_cap_sum_accepts_exactly_110_percent():
    root = _build_min_repo()
    try:
        rel = "tools/check_docs.py"
        original = '"docs/dev-wave/core.md": TextLimit(9_600),'
        replacement = '"docs/dev-wave/core.md": TextLimit(10_570),'
        source = _read(root, rel)
        assert source.count(original) == 1
        _write(root, rel, source.replace(original, replacement, 1))

        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_added_tasks_entry_is_rejected():
    root = _build_min_repo()
    try:
        rel = "tools/pegasus/dispatch_compute.py"
        source = _read(root, rel)
        _write(
            root,
            rel,
            source.replace(
                "}\n",
                '    "extra": _TaskSpec(child_script=("tools", "extra.py")),\n}\n',
                1,
            ),
        )
        result = _assert_violation(root, "dispatch inventory drift")
        assert "TASKS_only=['extra']" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_child_script_change_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                "`tools/run_tests.py`", "`tools/other_tests.py`", 1
            ),
        )
        result = _assert_violation(root, "dispatch inventory drift")
        assert "child_script={'tests':" in result.stdout
        assert "tools/other_tests.py" in result.stdout
        assert "tools/run_tests.py" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_missing_table_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                "| task | 子 script |", "| command | implementation |", 1
            ),
        )
        result = _assert_violation(root, "dispatch inventory drift")
        assert "exact task 表 header が 0 件" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_empty_table_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        text = _read(root, rel)
        text = re.sub(
            r"^\| `(?:tests|provenance)` \|.*\n",
            "",
            text,
            flags=re.MULTILINE,
        )
        _write(root, rel, text)
        result = _assert_violation(root, "dispatch inventory drift")
        assert "exact task 表が 0 行" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_missing_section_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        _write(
            root,
            rel,
            _read(root, rel).replace("### 7.0 ", "### 6.9 ", 1),
        )
        result = _assert_violation(root, "dispatch inventory drift")
        assert "`### 7.0` 節が 0 件" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


_DEV_WAVE_REFERENCE_MEMBER_LIMITS = (
    ("docs/dev-wave/core.md", 9_600),
    ("docs/dev-wave/workers.md", 5_000),
    ("docs/dev-wave/mutation.md", 3_750),
    ("docs/dev-wave/operations.md", 8_400),
)


@pytest.mark.parametrize(("rel", "limit"), _DEV_WAVE_REFERENCE_MEMBER_LIMITS)
def test_dev_wave_reference_limit_accepts_exact_boundary(rel, limit):
    root = _build_min_repo()
    try:
        _pad_to_bytes(root, rel, limit)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_duplicate_task_row_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        duplicate = "| `tests` | `tools/run_tests.py` |\n"
        _write(
            root,
            rel,
            _read(root, rel).replace(duplicate, duplicate + duplicate, 1),
        )
        result = _assert_violation(root, "dispatch inventory drift")
        assert "task 行が重複 — ['tests']" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_ignores_table_outside_7_0_section():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        decoy = """## unrelated

| task | 子 script |
|---|---|
| `decoy` | `tools/decoy.py` |

"""
        _write(root, rel, decoy + _read(root, rel))
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
        assert _dispatch_inventory_findings(result) == set()
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(("rel", "limit"), _DEV_WAVE_REFERENCE_MEMBER_LIMITS)
def test_dev_wave_reference_limit_rejects_plus_one(rel, limit):
    root = _build_min_repo()
    try:
        _pad_to_bytes(root, rel, limit + 1)
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1
        assert (
            f"{rel}: {limit + 1} bytes > 予算 {limit} bytes" in res.stdout
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_tools_readme_is_enumerated_and_budgeted():
    assert "tools/README.md" in _enumerated_rels()
    assert check_docs.TOOLS_README_LIMITS == {
        "tools/README.md": check_docs.TextLimit(3_000),
    }


def test_tools_readme_missing_is_rejected():
    root = _build_min_repo()
    try:
        os.remove(os.path.join(root, "tools", "README.md"))
        result = _assert_violation(root, "tools/README.md")
        assert "LIVING_DOCS の列挙対象が不在" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_tools_readme_budget_overrun_is_rejected():
    root = _build_min_repo()
    try:
        _pad_to_bytes(root, "tools/README.md", 3_001)
        result = _assert_violation(
            root,
            "tools/README.md: 3001 bytes > 予算 3000 bytes",
        )
        assert _violation_count(result) == 1, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_family_contract_pins_exact_surface():
    assert check_docs.PROVENANCE_LIMITS == {
        "docs/ai-provenance.md": check_docs.TextLimit(6_300),
    }
    assert check_docs.PROVENANCE_REFERENCE_LIMITS == {
        "docs/provenance/correction.md": check_docs.TextLimit(1_600),
        "docs/provenance/audit.md": check_docs.TextLimit(1_600),
    }
    assert check_docs.PROVENANCE_FAMILY_BYTES == 9_000
    assert check_docs.REQUIRED_PROVENANCE_REFERENCE_SECTIONS == {
        "docs/provenance/correction.md": {
            "PR-C01", "PR-C02", "PR-C03",
        },
        "docs/provenance/audit.md": {
            "PR-A01", "PR-A02", "PR-A03",
        },
    }
    assert check_docs.PROVENANCE_DISPATCH_CONTRACT == {
        "correction": (
            "固定 target の forward correction を扱う",
            frozenset({
                ("docs/provenance/correction.md", "PR-C01"),
                ("docs/provenance/correction.md", "PR-C02"),
                ("docs/provenance/correction.md", "PR-C03"),
            }),
        ),
        "message-file": (
            "commit 前に message を検査する",
            frozenset({
                ("docs/provenance/audit.md", "PR-A01"),
            }),
        ),
        "history": (
            "commit 後・別 range の履歴を監査する",
            frozenset({
                ("docs/provenance/audit.md", "PR-A02"),
                ("docs/provenance/correction.md", "PR-C03"),
            }),
        ),
        "analysis": (
            "provenance を比較や改善判断に使う",
            frozenset({
                ("docs/provenance/audit.md", "PR-A03"),
            }),
        ),
    }
    assert check_docs.PROVENANCE_SHARED_DISPATCH_PAIRS == {
        ("docs/provenance/correction.md", "PR-C03"): frozenset({
            "correction", "history",
        }),
    }


def test_provenance_family_is_enumerated_and_not_dispatch_allowlisted():
    family = {
        "docs/ai-provenance.md",
        "docs/provenance/correction.md",
        "docs/provenance/audit.md",
    }
    assert family <= set(_enumerated_rels())
    assert not (
        set(check_docs.PROVENANCE_LIMITS)
        & check_docs.NORMATIVE_DISPATCH_ALLOWLIST
    )
    assert not (
        set(check_docs.PROVENANCE_REFERENCE_LIMITS)
        & check_docs.NORMATIVE_DISPATCH_ALLOWLIST
    )


_PROVENANCE_MEMBER_LIMITS = (
    ("docs/ai-provenance.md", 6_300),
    ("docs/provenance/correction.md", 1_600),
    ("docs/provenance/audit.md", 1_600),
)


def _pad_provenance_family(root: str, target: int) -> None:
    limits = dict(_PROVENANCE_MEMBER_LIMITS)
    current = sum(
        len(_read(root, rel).encode("utf-8")) for rel in limits
    )
    assert current <= target
    remaining = target - current
    for rel, limit in limits.items():
        size = len(_read(root, rel).encode("utf-8"))
        grow = min(remaining, limit - size)
        if grow:
            _pad_to_bytes(root, rel, size + grow)
            remaining -= grow
    assert remaining == 0
    sizes = {
        rel: len(_read(root, rel).encode("utf-8")) for rel in limits
    }
    assert sum(sizes.values()) == target
    assert all(sizes[rel] <= limit for rel, limit in limits.items())


def _assert_findings(root: str, *expected: str) -> subprocess.CompletedProcess:
    res = _run_check(root)
    assert res.returncode == 1, f"違反 fixture が赤にならなかった:\n{res.stdout}"
    assert _finding_set(res) == set(expected), res.stdout
    assert _violation_count(res) == len(expected), res.stdout
    return res


@pytest.mark.parametrize(("rel", "limit"), _PROVENANCE_MEMBER_LIMITS)
def test_provenance_member_limit_accepts_exact_boundary(rel, limit):
    root = _build_min_repo()
    try:
        _pad_to_bytes(root, rel, limit)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(("rel", "limit"), _PROVENANCE_MEMBER_LIMITS)
def test_provenance_member_limit_rejects_plus_one(rel, limit):
    root = _build_min_repo()
    try:
        _pad_to_bytes(root, rel, limit + 1)
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1
        assert (
            f"{rel}: {limit + 1} bytes > 予算 {limit} bytes" in res.stdout
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_family_accepts_exactly_9000_bytes():
    root = _build_min_repo()
    try:
        _pad_provenance_family(root, 9_000)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_family_rejects_9001_bytes():
    root = _build_min_repo()
    try:
        _pad_provenance_family(root, 9_001)
        _assert_findings(
            root,
            "docs/ai-provenance.md + docs/provenance/**: "
            "合計 9001 bytes > hard ceiling 9000 bytes",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_unregistered_reference_is_rejected():
    root = _build_min_repo()
    try:
        _write(root, "docs/provenance/extra.md", "# escaped\n")
        _assert_findings(
            root,
            "docs/provenance/extra.md: docs/provenance/** の予算未登録実体 — "
            "規範 detail を family 閉包外へ逃がしてはならない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_registered_provenance_reference_deletion_is_rejected():
    root = _build_min_repo()
    try:
        os.remove(os.path.join(root, "docs/provenance/audit.md"))
        _assert_findings(
            root,
            "docs/provenance/audit.md: 登録済み provenance reference が不在 — "
            "入口 dispatch が到達不能",
            "docs/ai-provenance.md:8: 実在しないパス参照: "
            "'docs/provenance/audit.md'",
            "docs/ai-provenance.md:9: 実在しないパス参照: "
            "'docs/provenance/audit.md'",
            "docs/ai-provenance.md:10: 実在しないパス参照: "
            "'docs/provenance/audit.md'",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_registered_provenance_reference_symlink_is_rejected():
    root = _build_min_repo()
    external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_provenance_")
    try:
        rel = "docs/provenance/audit.md"
        member = os.path.join(root, rel)
        external_member = os.path.join(external, "audit.md")
        _write(external, "audit.md", _read(root, rel))
        os.remove(member)
        os.symlink(external_member, member)
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        prefix = (
            "docs/provenance/audit.md: symlink または regular file 以外 — "
            "予算・interface 検査対象として受理しない "
            "(symlink を含む path は読まない: "
        )
        findings = _finding_set(res)
        normalized_findings = set()
        for finding in findings:
            if finding.startswith(prefix) and finding.endswith(")"):
                reported_path = finding.removeprefix(prefix).removesuffix(")")
                if os.path.isabs(reported_path):
                    finding = prefix + "<absolute path>)"
            normalized_findings.add(finding)
        assert normalized_findings == {
            "docs/provenance/audit.md: symlink または regular file 以外 — "
            "予算・interface 検査対象として受理しない "
            "(symlink を含む path は読まない: <absolute path>)"
        }, res.stdout
        assert _violation_count(res) == 1, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(external, ignore_errors=True)


@pytest.mark.parametrize("mutation", ["missing", "duplicate"])
def test_provenance_required_h2_multiplicity_is_rejected(mutation):
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        heading = "## PR-A02 — synthetic"
        assert text.count(heading) == 1
        if mutation == "missing":
            text = text.replace(heading, "### PR-A02 — synthetic", 1)
        else:
            text += f"\n{heading}\n\nbody\n"
        _write(root, rel, text)
        count = 0 if mutation == "missing" else 2
        _assert_findings(
            root,
            f"{rel}: H2 見出し PR-A02 が {count} 件 — "
            "provenance dispatch 先は一意でなければならない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_orphan_reference_h2_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        _write(root, rel, _read(root, rel) + "\n## PR-A99 — orphan\n\nbody\n")
        _assert_findings(
            root,
            f"{rel}: provenance dispatch 契約にない孤児 H2 — ['PR-A99']",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _dispatch_row(text: str, key: str) -> str:
    matches = [line for line in text.splitlines(keepends=True)
               if line.startswith(f"| {key} |")]
    assert len(matches) == 1, (key, matches)
    return matches[0]


def test_provenance_dispatch_row_deletion_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        _write(root, rel, text.replace(_dispatch_row(text, "history"), "", 1))
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の "
            "row count が不一致 — actual=0, expected=1",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_duplicate_row_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        row = _dispatch_row(text, "history")
        _write(root, rel, text + row)
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の "
            "row count が不一致 — actual=2, expected=1",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize("replacement", ["", "常に監査する", "決して監査しない"])
def test_provenance_dispatch_condition_literal_change_is_rejected(replacement):
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        old = "commit 後・別 range の履歴を監査する"
        assert text.count(old) == 1
        row = _dispatch_row(text, "history")
        changed = row.replace(old, replacement, 1)
        _write(root, rel, text.replace(row, changed, 1))
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の発火条件が不一致 — "
            f"actual={[replacement]!r}, expected={[old]!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_conditions_cannot_be_swapped_between_keys():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        history = "commit 後・別 range の履歴を監査する"
        analysis = "provenance を比較や改善判断に使う"
        sentinel = "__SWAPPED_CONDITION__"
        changed = text.replace(history, sentinel, 1)
        changed = changed.replace(analysis, history, 1).replace(sentinel, analysis, 1)
        _write(root, rel, changed)
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'analysis' の発火条件が不一致 — "
            f"actual={[history]!r}, expected={[analysis]!r}",
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の発火条件が不一致 — "
            f"actual={[analysis]!r}, expected={[history]!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_missing_pair_is_rejected_independently():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        row = _dispatch_row(text, "history")
        removed = "; `docs/provenance/correction.md`: `PR-C03`"
        assert row.count(removed) == 1
        _write(root, rel, text.replace(row, row.replace(removed, "", 1), 1))
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の参照集合が不一致 — "
            "missing=[('docs/provenance/correction.md', 'PR-C03')], extra=[]",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_condition_token_smuggling_is_diagnostic_sensitivity():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        row = _dispatch_row(text, "history")
        replacement = (
            "| history | commit 後・別 range の履歴を監査する "
            "`docs/provenance/audit.md`: `PR-A02` | |\n"
        )
        _write(root, rel, text.replace(row, replacement, 1))
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の発火条件が不一致 — "
            "actual=['commit 後・別 range の履歴を監査する "
            "`docs/provenance/audit.md`: `PR-A02`'], "
            "expected=['commit 後・別 range の履歴を監査する']",
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の参照集合が不一致 — "
            "missing=[('docs/provenance/audit.md', 'PR-A02'), "
            "('docs/provenance/correction.md', 'PR-C03')], extra=[]",
            "docs/ai-provenance.md: diagnostic sensitivity — provenance 条件 "
            "dispatch 'history' の条件セルに reference token="
            "['`PR-A02`', '`docs/provenance/audit.md`']",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    ("mutation", "detail"),
    [
        ("header-missing", "header '| key | 発火条件 | 読む節 |' が 0 件"),
        ("header-hidden", "header '| key | 発火条件 | 読む節 |' が 0 件"),
        ("header-renamed", "header '| key | 発火条件 | 読む節 |' が 0 件"),
        ("header-duplicate", "header '| key | 発火条件 | 読む節 |' が 2 件"),
        ("separator-missing", "3列 separator が 0 件"),
        ("separator-duplicate", "3列 separator が 2 件"),
        ("separator-displaced", "separator が header 直後にない"),
        (
            "four-columns",
            "data row が3列・外周 delimiter 高々1個でない — "
            "leading=1, trailing=1, cells=4",
        ),
        (
            "two-columns",
            "data row が3列・外周 delimiter 高々1個でない — "
            "leading=1, trailing=1, cells=2",
        ),
        (
            "double-leading",
            "data row が3列・外周 delimiter 高々1個でない — "
            "leading=2, trailing=1, cells=4",
        ),
        (
            "double-trailing",
            "data row が3列・外周 delimiter 高々1個でない — "
            "leading=1, trailing=2, cells=4",
        ),
    ],
)
def test_provenance_dispatch_table_structure_is_exact(mutation, detail):
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        header = "| key | 発火条件 | 読む節 |"
        separator = "|---|---|---|"
        row = _dispatch_row(text, "history")
        if mutation == "header-missing":
            changed = text.replace(header + "\n", "", 1)
        elif mutation == "header-hidden":
            changed = text.replace(header, f"<!-- {header} -->", 1)
        elif mutation == "header-renamed":
            changed = text.replace(header, "| key | 発火条件 | 任意欄 |", 1)
        elif mutation == "header-duplicate":
            changed = text.replace(header, header + "\n" + header, 1)
        elif mutation == "separator-missing":
            changed = text.replace(separator + "\n", "", 1)
        elif mutation == "separator-duplicate":
            changed = text.replace(separator, separator + "\n" + separator, 1)
        elif mutation == "separator-displaced":
            changed = text.replace(
                header + "\n" + separator,
                header + "\n\n" + separator,
                1,
            )
        elif mutation == "four-columns":
            changed = text.replace(row, row.rstrip("\n")[:-1] + "| extra |\n", 1)
        elif mutation == "two-columns":
            condition = "commit 後・別 range の履歴を監査する"
            changed = text.replace(row, f"| history | {condition} |\n", 1)
        elif mutation == "double-leading":
            changed = text.replace(row, "|" + row, 1)
        else:
            changed = text.replace(row, row.rstrip("\n") + "|\n", 1)
        _write(root, rel, changed)
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 表の構造が不一致 — "
            f"{[detail]!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_data_row_outer_delimiters_are_optional():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        row = _dispatch_row(text, "history")
        changed = row.strip().removeprefix("|").removesuffix("|").strip() + "\n"
        _write(root, rel, text.replace(row, changed, 1))
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_registry_outside_path_is_diagnostic_sensitivity():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        row = _dispatch_row(text, "history")
        changed = row.replace(
            "docs/provenance/audit.md", "docs/dev-wave/core.md", 1
        )
        _write(root, rel, text.replace(row, changed, 1))
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の参照集合が不一致 — "
            "missing=[('docs/provenance/audit.md', 'PR-A02')], "
            "extra=[('docs/dev-wave/core.md', 'PR-A02')]",
            "docs/ai-provenance.md: diagnostic sensitivity — provenance 条件 "
            "dispatch 'history' の第3列に registry 外 path=['docs/dev-wave/core.md']",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_html_commented_provenance_dispatch_table_is_not_visible():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        marker = "## 条件 dispatch\n"
        assert text.count(marker) == 1
        _write(root, rel, text.replace(marker, "<!--\n" + marker, 1) + "-->\n")
        _assert_findings(
            root,
            "docs/ai-provenance.md: 条件 dispatch 表を一意に抽出できない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_fenced_provenance_h2_is_not_visible():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        heading = "## PR-A01 — synthetic"
        assert text.count(heading) == 1
        _write(
            root,
            rel,
            text.replace(heading, f"```markdown\n{heading}\n```", 1),
        )
        _assert_findings(
            root,
            f"{rel}: H2 見出し PR-A01 が 0 件 — provenance dispatch 先は"
            "一意でなければならない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_inline_code_comment_delimiter_is_rejected_fail_closed():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        lineno = len(text.splitlines()) + 2
        _write(root, rel, text + "\n`<!--`\n## PR-A99 — visible\n`-->`\n")
        _assert_findings(
            root,
            f"{rel}: provenance Markdown の曖昧構文を受理しない — "
            f"{[f'line {lineno}: inline code 内の HTML comment delimiter']!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_unclosed_provenance_fence_is_rejected_fail_closed():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        lineno = len(text.splitlines()) + 2
        _write(root, rel, text + "\n```markdown\n## PR-A99 — masked\n")
        _assert_findings(
            root,
            f"{rel}: provenance Markdown の曖昧構文を受理しない — "
            f"{[f'line {lineno}: 未閉じ code fence']!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_mismatched_provenance_fence_is_rejected_fail_closed():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        opener = len(text.splitlines()) + 2
        closer = opener + 2
        _write(root, rel, text + "\n```markdown\n## PR-A99 — masked\n~~~\n")
        _assert_findings(
            root,
            f"{rel}: provenance Markdown の曖昧構文を受理しない — "
            f"{[f'line {closer}: 異種 fence closer', f'line {opener}: 未閉じ code fence']!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_fence_inside_html_comment_does_not_mask_following_h2():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        _write(
            root,
            rel,
            text + "\n<!--\n```markdown\n-->\n## PR-A99 — visible orphan\n",
        )
        _assert_findings(
            root,
            f"{rel}: provenance dispatch 契約にない孤児 H2 — ['PR-A99']",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_invalid_backtick_fence_info_string_is_rejected_fail_closed():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        lineno = len(text.splitlines()) + 2
        _write(root, rel, text + "\n```info`bad\n## PR-A99 — over-masked\n")
        _assert_findings(
            root,
            f"{rel}: provenance Markdown の曖昧構文を受理しない — "
            f"{[f'line {lineno}: 無効な backtick fence info string']!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_references_inherit_land_helper_location_lint():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        _write(root, rel, _read(root, rel) + "\n`tools/dev_wave_land.py`\n")
        _assert_findings(
            root,
            f"{rel}: land helper path は DW-S09 / DW-O23 だけに置く",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _load_fixture_checker(root: str):
    module_name = f"_check_docs_fixture_{id(root)}"
    path = os.path.join(root, "tools", "check_docs.py")
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _run_loaded_checker(module) -> subprocess.CompletedProcess:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        returncode = module.main()
    return subprocess.CompletedProcess([], returncode, output.getvalue(), "")


def test_provenance_registry_three_faces_asymmetry_is_rejected(monkeypatch):
    root = _build_min_repo()
    try:
        module = _load_fixture_checker(root)
        rel = "docs/provenance/extra.md"
        path = module.REPO / rel
        _write(root, rel, "# registered only in budget face\n")
        monkeypatch.setattr(
            module,
            "PROVENANCE_REFERENCE_LIMITS",
            {
                **module.PROVENANCE_REFERENCE_LIMITS,
                rel: module.TextLimit(1_600),
            },
        )
        monkeypatch.setattr(
            module, "LIVING_DOCS", [*module.LIVING_DOCS, path]
        )
        monkeypatch.setattr(
            module, "_ENUMERATED_DOCS", module._ENUMERATED_DOCS | {path}
        )
        res = _run_loaded_checker(module)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1, res.stdout
        assert "provenance registry 三面の path 集合が不一致" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_pair_multiple_key_ownership_is_rejected(
    monkeypatch,
):
    root = _build_min_repo()
    try:
        module = _load_fixture_checker(root)
        contract = dict(module.PROVENANCE_DISPATCH_CONTRACT)
        condition, pairs = contract["history"]
        duplicate = ("docs/provenance/audit.md", "PR-A01")
        contract["history"] = (condition, pairs | {duplicate})
        monkeypatch.setattr(module, "PROVENANCE_DISPATCH_CONTRACT", contract)

        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        row = _dispatch_row(text, "history")
        changed = row.replace("`PR-A02`", "`PR-A01`, `PR-A02`", 1)
        _write(root, rel, text.replace(row, changed, 1))

        res = _run_loaded_checker(module)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1, res.stdout
        assert "provenance dispatch pair の key 所有が不一致" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _placeholder_findings(root: str) -> list[str]:
    module = _load_fixture_checker(root)
    findings: list[str] = []
    module._check_literal_placeholder_guard(findings)
    return findings


def _assert_placeholder_violation(root: str, *needles: str) -> list[str]:
    findings = _placeholder_findings(root)
    assert findings, "placeholder 違反 fixture が赤にならなかった"
    rendered = "\n".join(findings)
    for needle in needles:
        assert needle in rendered, f"{needle!r} が finding にない:\n{rendered}"
    return findings


def _assert_other_checkers_clean(root: str) -> None:
    module = _load_fixture_checker(root)
    module._check_literal_placeholder_guard = lambda findings: set()
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        rc = module.main()
    assert rc == 0, output.getvalue()


def test_placeholder_guard_each_literal_independently_fires():
    literals = (
        "<反映>",
        "<受入結果を反映>",
        "<受入全走結果を反映>",
    )
    for literal in literals:
        root = _build_min_repo()
        try:
            _write(
                root,
                "output/insights/independent.md",
                f"independent control: {literal}\n",
            )
            findings = _assert_placeholder_violation(
                root, "未許可のリテラル placeholder", repr(literal)
            )
            assert len(findings) == 1, findings
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_main_propagates_finding_to_rc():
    root = _build_min_repo()
    try:
        rel = "output/insights/2026-07-24_e2e-real-seal.md"
        _write(root, rel, _read(root, rel) + "main wiring control: <反映>\n")
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "check_docs: 1 件の違反" in res.stdout, res.stdout
        assert "未許可のリテラル placeholder" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_new_literal_is_violation_in_each_family():
    cases = (
        ("docs/worklog.md", "worklog control: <反映>\n"),
        (
            "docs/archive/worklog-phase3-0722-0724.md",
            "archive control: <受入結果を反映>\n",
        ),
        (
            "output/insights/2026-07-24_e2e-real-seal.md",
            "insight control: <受入全走結果を反映>\n",
        ),
    )
    for rel, addition in cases:
        root = _build_min_repo()
        try:
            _write(root, rel, _read(root, rel) + addition)
            findings = _assert_placeholder_violation(
                root, rel, "未許可のリテラル placeholder"
            )
            assert len(findings) == 1, findings
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_detects_new_family_member():
    cases = (
        (
            "docs/archive/worklog-new.md",
            "# new archive\n\n"
            "## 2025-12-30 (1) — new archive\n\n"
            "new archive member: <反映>\n\n"
            "### 次の一手\n"
            "1. legacy item\n",
        ),
        (
            "output/insights/new-insight.md",
            "new insight member: <反映>\n",
        ),
    )
    for rel, content in cases:
        root = _build_min_repo()
        try:
            _write(root, rel, content)
            if rel.startswith("docs/archive/"):
                readme_rel = "docs/archive/README.md"
                _write(
                    root,
                    readme_rel,
                    _read(root, readme_rel) + "- `worklog-new.md`\n",
                )
            _assert_other_checkers_clean(root)
            findings = _assert_placeholder_violation(
                root, rel, "未許可のリテラル placeholder"
            )
            assert len(findings) == 1, findings
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_registered_line_removal_is_violation():
    root = _build_min_repo()
    try:
        rel = "output/insights/2026-07-24_e2e-real-seal.md"
        _write(root, rel, _read(root, rel).replace(
            _PLACEHOLDER_DEBT_INSIGHT + "\n", "", 1
        ))
        findings = _assert_placeholder_violation(
            root,
            rel,
            "KNOWN_PLACEHOLDER_DEBTS",
            "expected=1, actual=0",
        )
        assert len(findings) == 1, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_registered_line_content_change_is_violation():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        changed = _PLACEHOLDER_DEBT_WORKLOG.replace("repo scan", "Repo scan", 1)
        _write(
            root,
            rel,
            _read(root, rel).replace(_PLACEHOLDER_DEBT_WORKLOG, changed, 1),
        )
        findings = _assert_placeholder_violation(
            root,
            rel,
            "未許可のリテラル placeholder",
            "KNOWN_PLACEHOLDER_DEBTS",
            "expected=1, actual=0",
        )
        assert len(findings) == 2, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_registered_line_duplication_is_violation():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        original = f"{heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
        duplicated = (
            f"{heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
            f"{_PLACEHOLDER_DEBT_WORKLOG}\n"
        )
        text = _read(root, rel)
        assert original in text
        _write(root, rel, text.replace(original, duplicated, 1))
        findings = _assert_placeholder_violation(
            root,
            "worklog-entry:4926160d0e41c9e972953e535dcce8cc1744eff78b13277cc91d722dc06129f2",
            "37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0",
            "expected=1, actual=2",
        )
        assert len(findings) == 1, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_same_file_record_replay_is_violation():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        source_heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        target_heading = (
            "## 2026-07-25 (4) — /rulings: 裁定待ち 5 件をユーザーが推奨どおり"
            "一括裁定 — official 解禁を承認 (D86 起票、計測なし)"
        )
        text = _read(root, rel)
        source = f"{source_heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
        target = f"{target_heading}\n\n"
        assert source in text and target in text
        text = text.replace(source, f"{source_heading}\n", 1)
        text = text.replace(
            target,
            f"{target_heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n",
            1,
        )
        _write(root, rel, text)
        findings = _assert_placeholder_violation(
            root,
            rel,
            "未許可のリテラル placeholder",
            "worklog-entry:4926160d0e41c9e972953e535dcce8cc1744eff78b13277cc91d722dc06129f2",
            "expected=1, actual=0",
        )
        assert len(findings) == 2, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_duplicate_worklog_h2_is_violation():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        text = _read(root, rel)
        assert text.count(heading) == 1
        _write(root, rel, text + f"\n{heading}\n")
        findings = _placeholder_findings(root)
        assert len(findings) == 1, findings
        rendered = findings[0]
        assert "worklog 族の H2 raw bytes が重複" in rendered
        assert heading in rendered
        assert rendered.count(rel) == 2, rendered
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        tab_heading = "##\t2026-07-30 (1) — tab-separated duplicate"
        _write(
            root,
            rel,
            _read(root, rel)
            + f"\n{tab_heading}\n\nbody\n\n{tab_heading}\n",
        )
        findings = _placeholder_findings(root)
        assert len(findings) == 1, findings
        rendered = findings[0]
        assert "worklog 族の H2 raw bytes が重複" in rendered
        assert repr(tab_heading) in rendered
        assert rendered.count(rel) == 2, rendered
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_h2_collision_replay_is_violation():
    root = _build_min_repo()
    try:
        source_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        replay_rel = "docs/archive/worklog-h2-collision.md"
        heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        source = _read(root, source_rel)
        registered = f"{heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
        assert registered in source
        _write(
            root,
            source_rel,
            source.replace(
                registered,
                f"{heading}\n",
                1,
            ),
        )
        _write(
            root,
            replay_rel,
            f"# collision replay\n\n{heading}\n\n"
            f"{_PLACEHOLDER_DEBT_WORKLOG}\n\n### 次の一手\n",
        )
        findings = _placeholder_findings(root)
        assert len(findings) == 1, findings
        rendered = findings[0]
        assert "worklog 族の H2 raw bytes が重複" in rendered
        assert source_rel in rendered and replay_rel in rendered
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        source_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        replay_rel = "docs/archive/worklog-tab-scope-replay.md"
        heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        source = _read(root, source_rel)
        registered = f"{heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
        assert registered in source
        _write(
            root,
            source_rel,
            source.replace(registered, f"{heading}\n", 1),
        )
        tab_heading = heading.replace("## ", "##\t", 1)
        _write(
            root,
            replay_rel,
            f"# tab scope replay\n\n{tab_heading}\n\n"
            f"{_PLACEHOLDER_DEBT_WORKLOG}\n\n### 次の一手\n",
        )
        findings = _placeholder_findings(root)
        rendered = "\n".join(findings)
        assert len(findings) == 2, findings
        assert "未許可のリテラル placeholder" in rendered
        assert "expected=1, actual=0" in rendered
        assert "worklog 族の H2 raw bytes が重複" not in rendered
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_entry_rotation_keeps_ledger_green():
    registered_heading = (
        "## 2026-07-25 (4) — /rulings: 裁定待ち 5 件をユーザーが推奨どおり"
        "一括裁定 — official 解禁を承認 (D86 起票、計測なし)"
    )
    first_current_heading = "## 2026-08-01 (1) — first"
    original_first_heading = (
        "## 2026-07-24 (4) — 統合 E2E: 実 seal を official floor 経路に通す "
        "(D79(7) 部分閉鎖、branch worktree-dev-wave-e2e-real-seal、計測なし)"
    )

    def place_registered_entry_in_current(root: str) -> str:
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        worklog_rel = "docs/worklog.md"
        archive = _read(root, archive_rel)
        start = archive.index(registered_heading)
        entry = archive[start:]
        _write(root, archive_rel, archive[:start])

        assert entry.rstrip().endswith("### 次の一手")
        entry = entry.rstrip() + "\n1. [T-099] rotation handoff\n\n"
        worklog = _read(root, worklog_rel)
        marker = first_current_heading
        assert marker in worklog
        worklog = worklog.replace(
            first_current_heading,
            f"{first_current_heading}\n\n- [T-099] rotation sink",
            1,
        )
        _write(
            root,
            worklog_rel,
            worklog.replace(first_current_heading, entry + first_current_heading, 1),
        )
        baseline = _run_check(root)
        current_res = baseline
        assert current_res.returncode == 0, current_res.stdout
        return entry

    # H2 を現行 worklog に残し、登録行だけを後続 H2 へ移す対は赤。
    root = _build_min_repo()
    try:
        entry = place_registered_entry_in_current(root)
        worklog = _read(root, "docs/worklog.md")
        assert entry in worklog
        worklog = worklog.replace(
            _PLACEHOLDER_MENTION_WORKLOG_T094_A + "\n",
            "",
            1,
        )
        worklog = worklog.replace(
            first_current_heading,
            f"{first_current_heading}\n\n{_PLACEHOLDER_MENTION_WORKLOG_T094_A}",
            1,
        )
        _write(root, "docs/worklog.md", worklog)

        # baseline にない archive member と README 索引を作り、非空遷移も成立させる。
        new_name = "worklog-rotation-prelude.md"
        _write(
            root,
            f"docs/archive/{new_name}",
            "# rotation prelude\n\n"
            "## 2026-07-23 (1) — rotation prelude\n\n"
            "### 次の一手\n"
            "1. [T-098] archive boundary control\n",
        )
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        archive = _read(root, archive_rel)
        assert original_first_heading in archive
        _write(
            root,
            archive_rel,
            archive.replace(
                original_first_heading,
                f"{original_first_heading}\n\n- [T-098] archive boundary sink",
                1,
            ).replace(
                "## 2026-07-24 (5) — [T-086] PKG-2:",
                "### 次の一手\n\n## 2026-07-24 (5) — [T-086] PKG-2:",
                1,
            ),
        )
        _write(root, "docs/archive/README.md", _archive_readme(new_name))
        _assert_other_checkers_clean(root)
        replay_res = _run_check(root)
        assert replay_res.returncode == 1, replay_res.stdout
        assert "未許可のリテラル placeholder" in replay_res.stdout
        assert "expected=1, actual=0" in replay_res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # H2 + 本文の全体を新規 archive member へ移す対は緑。
    root = _build_min_repo()
    try:
        entry = place_registered_entry_in_current(root)
        worklog = _read(root, "docs/worklog.md")
        assert entry in worklog
        _write(root, "docs/worklog.md", worklog.replace(entry, "", 1))
        new_name = "worklog-rotation-new.md"
        _write(root, f"docs/archive/{new_name}", "# rotation\n\n" + entry)
        _write(root, "docs/archive/README.md", _archive_readme(new_name))
        rotated_res = _run_check(root)
        assert rotated_res.returncode == 0, rotated_res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_allowlist_is_path_bound():
    root = _build_min_repo()
    try:
        source = "output/insights/2026-07-24_e2e-real-seal.md"
        moved = "output/insights/moved.md"
        _write(root, source, _read(root, source).replace(
            _PLACEHOLDER_DEBT_INSIGHT + "\n", "", 1
        ))
        _write(root, moved, _PLACEHOLDER_DEBT_INSIGHT + "\n")
        findings = _assert_placeholder_violation(
            root,
            source,
            moved,
            "未許可のリテラル placeholder",
            "expected=1, actual=0",
        )
        assert len(findings) == 2, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_backticked_literal_is_still_detected():
    root = _build_min_repo()
    try:
        rel = "output/insights/markdown-context.md"
        _write(
            root,
            rel,
            "inline `<反映>` control\n"
            "```text\n"
            "<受入結果を反映>\n"
            "```\n",
        )
        findings = _assert_placeholder_violation(
            root, rel, "未許可のリテラル placeholder"
        )
        assert len(findings) == 2, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_verbatim_named_file_is_not_exempt():
    root = _build_min_repo()
    try:
        rel = "output/insights/new-verbatim.md"
        _write(root, rel, "verbatim suffix control: <反映>\n")
        findings = _assert_placeholder_violation(
            root, rel, "未許可のリテラル placeholder"
        )
        assert len(findings) == 1, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_ledger_size_is_pinned():
    root = _build_min_repo()
    try:
        module = _load_fixture_checker(root)
        debts = sum(
            count
            for entries in module.KNOWN_PLACEHOLDER_DEBTS.values()
            for count in entries.values()
        )
        mentions = sum(
            count
            for entries in module.KNOWN_PLACEHOLDER_MENTIONS.values()
            for count in entries.values()
        )
        assert debts == 4
        assert mentions == 5
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_ledger_entries_are_pinned_exactly():
    expected = {
        (
            "KNOWN_PLACEHOLDER_DEBTS",
            "worklog-entry:4926160d0e41c9e972953e535dcce8cc1744eff78b13277cc91d722dc06129f2",
            "37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_DEBTS",
            "worklog-entry:0885598e3ddffd2a6a5c0424c3e6a65ba24f67048374cf3eefc064247e746eb7",
            "3beb84d709104086993083d461c6b511b63ffd595f2037c28f5c5ae91e046327",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_DEBTS",
            "worklog-entry:be893df535111cf91c64c141d38afa482dbca6f0a8a829a55b36ac72d8dc79bc",
            "37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_DEBTS",
            "insights-path:output/insights/2026-07-24_e2e-real-seal.md",
            "c022f2e9ee8cfaf2237eafa5c30e0c772a368c953e5ccf03a29233028bbe52fd",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "worklog-entry:1241aea6de50f3519f1cb497ff8b0fc07d4b4c2b76f35047d091bfb893aa685a",
            "abdbb38938a76268b5cf63c13309339f58f0cc996deaa13db39c3786e2f3b866",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "worklog-entry:825788c80a8f458dd12f5682450f134950c37fb0ea6ebbdaddfb26d9f9e95511",
            "80101b39632c395324f424bc9929db7a5c5b76c66b21d61e30afd52434f097ce",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "worklog-entry:825788c80a8f458dd12f5682450f134950c37fb0ea6ebbdaddfb26d9f9e95511",
            "9162d9fc17d08b52b54c4f4b1adb96a3b614ed4d944ac955de27bb0ea5b539e5",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "insights-path:output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md",
            "90d8e1f6a7f7229085d78f91ddc7bc91155bbe1ec39b44aaae2b2809daaaf5d9",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "insights-path:output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md",
            "c66c4f6e14de10c369167108971c74fd0d1462b6a4489792efae907c5d02875c",
        ): 1,
    }
    actual = {}
    for ledger_name, ledger in (
        ("KNOWN_PLACEHOLDER_DEBTS", check_docs.KNOWN_PLACEHOLDER_DEBTS),
        ("KNOWN_PLACEHOLDER_MENTIONS", check_docs.KNOWN_PLACEHOLDER_MENTIONS),
    ):
        for scope, entries in ledger.items():
            for digest, count in entries.items():
                actual[(ledger_name, scope, digest)] = count
    assert actual == expected


def test_placeholder_guard_digest_line_boundary_contract():
    root = _build_min_repo()
    try:
        module = _load_fixture_checker(root)
        base = "digest プレースホルダ <反映>".encode("utf-8")
        lf_line = module._placeholder_logical_lines(
            (base + b"\n").decode("utf-8")
        )[0]
        crlf_line = module._placeholder_logical_lines(
            (base + b"\r\n").decode("utf-8")
        )[0]
        variants = (
            base + b" ",
            b"\xef\xbb\xbf" + base,
            "digest プレースホルダ <反映>".encode("utf-8"),
            base + b"\x0b" + "追記".encode("utf-8"),
        )
        baseline_digest = module._placeholder_line_digest(lf_line)
        assert module._placeholder_line_digest(crlf_line) == baseline_digest
        for variant in variants:
            logical = module._placeholder_logical_lines(
                variant.decode("utf-8")
            )
            assert len(logical) == 1
            assert module._placeholder_line_digest(logical[0]) != baseline_digest

        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        archive_bytes = _read(root, archive_rel).encode("utf-8")
        _write_bytes(root, archive_rel, archive_bytes.replace(b"\n", b"\r\n"))
        assert _placeholder_findings(root) == []
    finally:
        shutil.rmtree(root, ignore_errors=True)

    mutations = (
        _PLACEHOLDER_MENTION_WORKLOG_F36 + " ",
        "\ufeff" + _PLACEHOLDER_MENTION_WORKLOG_F36,
        _PLACEHOLDER_MENTION_WORKLOG_F36.replace(
            "プレースホルダ", "プレースホルダ", 1
        ),
        _PLACEHOLDER_MENTION_WORKLOG_F36 + "\v追記",
    )
    for changed in mutations:
        root = _build_min_repo()
        try:
            rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
            text = _read(root, rel)
            assert _PLACEHOLDER_MENTION_WORKLOG_F36 in text
            _write(
                root,
                rel,
                text.replace(_PLACEHOLDER_MENTION_WORKLOG_F36, changed, 1),
            )
            findings = _assert_placeholder_violation(
                root,
                "未許可のリテラル placeholder",
                "expected=1, actual=0",
            )
            assert len(findings) == 2, findings
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_missing_target_family_is_violation():
    cases = (
        ("output/insights", "output/insights: placeholder 検査の対象 directory が不在"),
        (
            "docs/archive/worklog-phase3-0722-0724.md",
            "docs/archive/worklog-*.md: placeholder 検査の対象族に実体がない",
        ),
    )
    for rel, expected in cases:
        root = _build_min_repo()
        try:
            path = os.path.join(root, rel)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            _assert_placeholder_violation(root, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        shutil.rmtree(os.path.join(root, "docs", "archive"))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert (
            "docs/archive: placeholder 検査の対象 directory が不在"
            in res.stdout
        ), res.stdout
        assert "docs/archive/README.md: ファイルが不在" in res.stdout, res.stdout
        assert "Traceback" not in res.stderr, res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_read_failures_are_aggregated_without_traceback():
    cases = ("worklog-directory", "archive-invalid-utf8")
    for case in cases:
        root = _build_min_repo()
        try:
            if case == "worklog-directory":
                path = os.path.join(root, "docs", "worklog.md")
                os.remove(path)
                os.mkdir(path)
                expected = (
                    "docs/worklog.md: placeholder 検査の列挙対象が regular file でない"
                )
            else:
                rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
                _write_bytes(root, rel, b"\xff")
                expected = f"{rel}: placeholder 検査の読取失敗"
            res = _run_check(root)
            assert res.returncode == 1, (case, res.stdout, res.stderr)
            assert re.search(
                r"^check_docs: \d+ 件の違反$", res.stdout, re.MULTILINE
            ), res.stdout
            assert expected in res.stdout, res.stdout
            assert res.stdout.count(expected) == 1, res.stdout
            assert "KNOWN_PLACEHOLDER_DEBTS の登録 digest" not in res.stdout
            assert "KNOWN_PLACEHOLDER_MENTIONS の登録 digest" not in res.stdout
            assert "Traceback" not in res.stdout, res.stdout
            assert "Traceback" not in res.stderr, res.stderr
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_unreadable_insight_does_not_mask_worklog_mismatch():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        archive = _read(root, rel)
        registered = f"{_PLACEHOLDER_DEBT_WORKLOG}\n"
        assert archive.count(registered) == 2
        _write(
            root,
            rel,
            archive.replace(registered, registered * 2, 1),
        )
        _write_bytes(root, "output/insights/unrelated.md", b"\xff")
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "output/insights/unrelated.md: placeholder 検査の読取失敗" in res.stdout
        assert "insights-path scope の台帳照合を停止" in res.stdout
        assert "KNOWN_PLACEHOLDER_DEBTS の登録 digest" in res.stdout
        assert "expected=1, actual=2" in res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_safe_reader_dependency_failures_do_not_emit_derived_findings():
    # decisions.md: 正当な D1 参照を「実在しない D」と派生誤判定しない。
    root = _build_min_repo()
    try:
        _write(root, "README.md", "# living\n\nD1 を参照する。\n")
        _write_bytes(root, "docs/decisions.md", b"\xff")
        res = _run_check(root)
        prefix = "docs/decisions.md: D 見出し検査の読取失敗"
        assert res.returncode == 1, res.stdout
        assert res.stdout.count(prefix) == 1, res.stdout
        assert "実在しない D 参照" not in res.stdout, res.stdout
        assert "検査を停止" in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # 通常経路では、実在しない D 参照の本来の finding が発火する。
    root = _build_min_repo()
    try:
        _write(root, "README.md", "# living\n\nD999 を参照する。\n")
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "実在しない D 参照: 'D999'" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # phase3.md: ledger だけが sink の T-001 を消失扱いしない。
    root = _build_min_repo()
    try:
        worklog = _read(root, "docs/worklog.md")
        _write(
            root,
            "docs/worklog.md",
            worklog.replace("- [T-001] consumed\n", "", 1),
        )
        _write_bytes(root, "docs/phase3.md", b"\xff")
        res = _run_check(root)
        prefix = "docs/phase3.md: living docs 検査の読取失敗"
        assert res.returncode == 1, res.stdout
        assert res.stdout.count(prefix) == 1, res.stdout
        assert "次の一手 ID [T-001]" not in res.stdout, res.stdout
        assert "検査を停止" in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # 通常の見送り台帳構造では、sink にない遷移の本来の finding が発火する。
    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/worklog.md",
            _CLEAN_WORKLOG.replace("[T-001] carry", "[T-777] carry", 1),
        )
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "次の一手 ID [T-777]" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # 見送り台帳の構造抽出失敗は空集合でなく未知状態として遷移検査を止める。
    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/worklog.md",
            _CLEAN_WORKLOG.replace("[T-001] carry", "[T-777] carry", 1),
        )
        _write(
            root,
            "docs/phase3.md",
            _CLEAN_PHASE3.replace("## 見送り台帳 (synthetic)", "## broken ledger"),
        )
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "見送り台帳 sink の構造抽出失敗" in res.stdout, res.stdout
        assert "見送り台帳に依存する worklog 遷移検査を停止" in res.stdout
        assert "次の一手 ID [T-777]" not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # archive 1 件が不明なら、読めた非隣接 archive 同士を比較しない。
    root = _build_min_repo()
    try:
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        archive = _read(root, archive_rel)
        assert archive.rstrip().endswith("### 次の一手")
        _write(
            root,
            archive_rel,
            archive.rstrip() + "\n1. [T-777] unreadable middle sink\n",
        )
        unreadable_name = "worklog-archive-unreadable.md"
        later_name = "worklog-archive-later.md"
        _write_bytes(root, f"docs/archive/{unreadable_name}", b"\xff")
        _write(
            root,
            f"docs/archive/{later_name}",
            "# later archive\n\n"
            "## 2026-07-27 (1) — later archive\n\n"
            "### 次の一手\n",
        )
        _write(
            root,
            "docs/archive/README.md",
            _archive_readme(unreadable_name, later_name),
        )
        res = _run_check(root)
        prefix = (
            f"docs/archive/{unreadable_name}: "
            "placeholder 検査の読取失敗"
        )
        assert res.returncode == 1, res.stdout
        assert res.stdout.count(prefix) == 1, res.stdout
        assert "次の一手 ID [T-777]" not in res.stdout, res.stdout
        assert "検査を停止" in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # 通常の archive 構造では、archive 境界遷移の本来の finding が発火する。
    root = _build_min_repo()
    try:
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        later_name = "worklog-archive-structure-later.md"
        _write(
            root,
            archive_rel,
            _read(root, archive_rel).rstrip()
            + "\n1. [T-778] archive positive control\n",
        )
        _write(
            root,
            f"docs/archive/{later_name}",
            "# later archive\n\n"
            "## 2026-07-27 (1) — later archive\n\n"
            "### 次の一手\n",
        )
        _write(root, "docs/archive/README.md", _archive_readme(later_name))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "次の一手 ID [T-778]" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # archive entry の構造抽出失敗時は、読めた非隣接 archive を比較しない。
    root = _build_min_repo()
    try:
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        malformed_name = "worklog-archive-structure-malformed.md"
        later_name = "worklog-archive-structure-later.md"
        _write(
            root,
            archive_rel,
            _read(root, archive_rel).rstrip()
            + "\n1. [T-778] archive positive control\n",
        )
        _write(
            root,
            f"docs/archive/{malformed_name}",
            "# readable but no worklog H2\n",
        )
        _write(
            root,
            f"docs/archive/{later_name}",
            "# later archive\n\n"
            "## 2026-07-27 (1) — later archive\n\n"
            "### 次の一手\n",
        )
        _write(
            root,
            "docs/archive/README.md",
            _archive_readme(malformed_name, later_name),
        )
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "archive entry の構造抽出失敗" in res.stdout, res.stdout
        assert "archive 族全体に依存する順序・境界遷移検査を停止" in res.stdout
        assert "次の一手 ID [T-778]" not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_safe_reader_rejects_worklog_symlink_and_fifo_without_hang():
    root = _build_min_repo()
    external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_")
    try:
        worklog = os.path.join(root, "docs", "worklog.md")
        external_rel = "external-worklog.md"
        _write(
            external,
            external_rel,
            "# external\n\n"
            "## EXTERNAL-SENTINEL\n\n"
            "external unauthorized: <受入結果を反映>\n",
        )
        os.remove(worklog)
        os.symlink(os.path.join(external, external_rel), worklog)
        res = _run_check(root, timeout=5)
        assert res.returncode == 1, res.stdout
        assert re.search(r"^check_docs: \d+ 件の違反$", res.stdout, re.MULTILINE)
        assert "docs/worklog.md" in res.stdout
        assert "次の一手の保存則を停止" in res.stdout
        assert "EXTERNAL-SENTINEL" not in res.stdout, res.stdout
        assert "未許可のリテラル placeholder" not in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(external, ignore_errors=True)

    root = _build_min_repo()
    try:
        worklog = os.path.join(root, "docs", "worklog.md")
        os.remove(worklog)
        os.mkfifo(worklog)
        res = _run_check(root, timeout=5)
        assert res.returncode == 1, res.stdout
        assert re.search(r"^check_docs: \d+ 件の違反$", res.stdout, re.MULTILINE)
        assert "docs/worklog.md" in res.stdout
        assert "regular file" in res.stdout
        assert "次の一手の保存則を停止" in res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # placeholder 列挙を経由しない decisions.md で safe-reader 単独の拒否を固定する。
    root = _build_min_repo()
    external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_")
    try:
        decisions = os.path.join(root, "docs", "decisions.md")
        _write(
            external,
            "external-decisions.md",
            "## D4242 EXTERNAL-SAFE-READER-SENTINEL\n"
            "## D4242 EXTERNAL-SAFE-READER-SENTINEL\n",
        )
        os.remove(decisions)
        os.symlink(
            os.path.join(external, "external-decisions.md"),
            decisions,
        )
        res = _run_check(root, timeout=5)
        assert res.returncode == 1, res.stdout
        assert "docs/decisions.md: D 見出し検査の読取失敗" in res.stdout
        assert "symlink を含む path は読まない" in res.stdout
        assert "D4242 の見出しが重複" not in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(external, ignore_errors=True)

    root = _build_min_repo()
    try:
        decisions = os.path.join(root, "docs", "decisions.md")
        os.remove(decisions)
        os.mkfifo(decisions)
        res = _run_check(root, timeout=5)
        assert res.returncode == 1, res.stdout
        assert "docs/decisions.md: D 見出し検査の読取失敗" in res.stdout
        assert "regular file でないため読まない" in res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_rejects_symlinked_target_directories():
    cases = (
        (
            "docs/archive",
            _PLACEHOLDER_ARCHIVE_NAME,
            "",
            "docs/archive: placeholder 検査の対象 directory が symlink",
        ),
        (
            "output/insights",
            "2026-07-24_e2e-real-seal.md",
            _PLACEHOLDER_DEBT_INSIGHT + "\n",
            "output/insights: placeholder 検査の対象 directory が symlink",
        ),
    )
    for rel, member, content, expected in cases:
        root = _build_min_repo()
        external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_")
        try:
            if rel == "docs/archive":
                content = _read(
                    root, f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
                )
                _write(
                    external,
                    "README.md",
                    "# EXTERNAL-ARCHIVE-README-SENTINEL\n\n"
                    "## 現在の収容物\n",
                )
            _write(external, member, content)
            external_marker = (
                "worklog-external-unapproved.md"
                if rel == "docs/archive"
                else "external-unapproved.md"
            )
            _write(
                external,
                external_marker,
                "# external\n\n## EXTERNAL-DIRECTORY-SENTINEL\n\n"
                "external unauthorized: <受入結果を反映>\n",
            )
            path = os.path.join(root, rel)
            shutil.rmtree(path)
            os.symlink(external, path)
            findings = _assert_placeholder_violation(root, expected)
            assert findings
            res = _run_check(root, timeout=5)
            assert res.returncode == 1, res.stdout
            assert expected in res.stdout, res.stdout
            assert external_marker not in res.stdout, res.stdout
            assert "EXTERNAL-DIRECTORY-SENTINEL" not in res.stdout, res.stdout
            assert "EXTERNAL-ARCHIVE-README-SENTINEL" not in res.stdout, res.stdout
            assert "未許可のリテラル placeholder" not in res.stdout, res.stdout
            assert "Traceback" not in res.stdout + res.stderr
        finally:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(external, ignore_errors=True)


def test_placeholder_guard_rejects_symlinked_and_non_regular_members():
    cases = (
        (
            f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}",
            "archive-symlink",
        ),
        (
            "output/insights/2026-07-24_e2e-real-seal.md",
            "insight-symlink",
        ),
        (
            f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}",
            "archive-directory",
        ),
        (
            "output/insights/2026-07-24_e2e-real-seal.md",
            "insight-directory",
        ),
        (
            f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}",
            "archive-fifo",
        ),
        (
            "output/insights/2026-07-24_e2e-real-seal.md",
            "insight-fifo",
        ),
    )
    for rel, case in cases:
        root = _build_min_repo()
        external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_")
        try:
            content = _read(root, rel)
            path = os.path.join(root, rel)
            os.remove(path)
            if case.endswith("symlink"):
                target = os.path.join(external, "registered.md")
                _write(
                    external,
                    "registered.md",
                    content + "\nexternal unauthorized: <受入結果を反映>\n",
                )
                os.symlink(target, path)
            elif case.endswith("fifo"):
                os.mkfifo(path)
            else:
                os.mkdir(path)
            findings = _assert_placeholder_violation(
                root,
                rel,
                "placeholder 検査の対象 member が regular file でない",
            )
            assert findings
            res = _run_check(root, timeout=5)
            assert res.returncode == 1, res.stdout
            assert rel in res.stdout, res.stdout
            assert (
                "placeholder 検査の対象 member が regular file でない"
                in res.stdout
            ), res.stdout
            assert "未許可のリテラル placeholder" not in res.stdout, res.stdout
            assert "Traceback" not in res.stdout + res.stderr
        finally:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(external, ignore_errors=True)


def test_placeholder_guard_non_exact_literals_are_not_detected():
    """exact 3 文字列は確定裁定であり、意味的に同じ別表記・HTML entity・
    予測値の先書きは本 gate の射程外である (裁定パッケージ [T-100])。
    """

    root = _build_min_repo()
    try:
        _write(
            root,
            "output/insights/non-exact.md",
            "<結果を反映>\n"
            "<反映済み>\n"
            "&lt;反映&gt;\n"
            "受入結果を反映\n"
            "検査は 123 passed と予測する\n",
        )
        assert _placeholder_findings(root) == []
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _read(root: str, rel: str) -> str:
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return f.read()


def _pad_to_bytes(root: str, rel: str, target: int) -> None:
    text = _read(root, rel)
    current = len(text.encode("utf-8"))
    assert current <= target
    _write(root, rel, text + ("\n" * (target - current)))


def _rewrite_matching_lines(
    root: str,
    rel: str,
    predicate,
    rewrite,
    expected: int = 1,
) -> None:
    lines = _read(root, rel).splitlines(keepends=True)
    matched = sum(1 for line in lines if predicate(line))
    assert matched == expected, (rel, matched, expected)
    _write(
        root,
        rel,
        "".join(
            rewrite(line) if predicate(line) else line
            for line in lines
        ),
    )


def _mutate_command_guard(root: str, case: str) -> None:
    if case == "command_byte_over":
        _pad_to_bytes(
            root,
            ".claude/commands/rulings.md",
            check_docs.COMMAND_LIMITS[
                ".claude/commands/rulings.md"
            ].max_bytes + 1,
        )
    elif case == "reference_byte_over":
        _pad_to_bytes(
            root,
            "docs/dev-wave/mutation.md",
            check_docs.REFERENCE_LIMITS[
                "docs/dev-wave/mutation.md"
            ].max_bytes + 1,
        )
    elif case == "self_byte_over":
        _pad_to_bytes(
            root,
            "docs/skill-self-improvement.md",
            check_docs.SELF_LIMITS[
                "docs/skill-self-improvement.md"
            ].max_bytes + 1,
        )
    elif case == "long_line":
        rel = ".claude/commands/rulings.md"
        _write(root, rel, _read(root, rel) + ("x" * 181) + "\n")
    elif case == "unregistered_command":
        _write(root, ".claude/commands/extra.md", "# extra\n")
    elif case == "registered_command_deleted":
        os.remove(os.path.join(root, ".claude/commands/rulings.md"))
    elif case == "arguments_missing":
        rel = ".claude/commands/rulings.md"
        _write(root, rel, _read(root, rel).replace("$ARGUMENTS", "arguments"))
    elif case == "frontmatter_key_changed":
        rel = ".claude/commands/rulings.md"
        _write(root, rel, _read(root, rel).replace(
            "argument-hint:", "argument-hint-renamed:", 1
        ))
    elif case == "frontmatter_duplicate":
        rel = ".claude/commands/rulings.md"
        _write(root, rel, _read(root, rel).replace(
            "description: synthetic rulings",
            "description: synthetic rulings\ndescription: duplicate",
            1,
        ))
    elif case == "frontmatter_malformed":
        rel = ".claude/commands/rulings.md"
        _write(root, rel, _read(root, rel).replace("---", "not-frontmatter", 1))
    elif case == "disable_value_changed":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel).replace(
            "disable-model-invocation: true",
            "disable-model-invocation: false",
            1,
        ))
    elif case == "reference_section_deleted":
        rel = "docs/dev-wave/mutation.md"
        _write(root, rel, _read(root, rel).replace(
            "## DW-M05 — synthetic", "### removed DW-M05", 1
        ))
    elif case == "reference_section_duplicated":
        rel = "docs/dev-wave/mutation.md"
        _write(root, rel, _read(root, rel) + "\n## DW-M05 — duplicate\n")
    elif case == "stage2_operations_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 2 preflight |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: "",
        )
    elif case == "stage3_o13_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 3 preflight |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: line.replace(", `DW-O13`", ""),
        )
    elif case == "stage6_s05_inheritance_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 6 |")
            and "`DW-S05-A`" in line,
            lambda line: "",
        )
    elif case == "stage6_all_operations_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 6 |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: "",
        )
    elif case == "stage8_operations_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 8 preflight |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: "",
        )
    elif case == "stage8_self_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 8 preflight |")
            and "`docs/skill-self-improvement.md`" in line,
            lambda line: "",
        )
    elif case == "stage9_land_operation_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 9 |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: "",
        )
    elif case == "condition_o13_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 13 |"),
            lambda line: "",
        )
    elif case == "condition_all_operations_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: any(
                line.startswith(f"| {key} |")
                for key in _OPERATION_CONDITION_KEYS
            ),
            lambda line: "",
            expected=len(_OPERATION_CONDITION_KEYS),
        )
    elif case == "condition_supervisor_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 22 |"),
            lambda line: "",
        )
    elif case == "condition_land_operation_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 23 |"),
            lambda line: "",
        )
    elif case == "self_heading_deleted":
        rel = "docs/skill-self-improvement.md"
        _write(root, rel, _read(root, rel).replace(
            "## routing\n", "", 1
        ))
    elif case == "self_h3_deleted":
        rel = "docs/skill-self-improvement.md"
        _write(root, rel, _read(root, rel).replace(
            "### cleanup-branches\n", "", 1
        ))
    elif case == "self_long_line":
        rel = "docs/skill-self-improvement.md"
        _write(root, rel, _read(root, rel) + ("x" * 101) + "\n")
    elif case == "self_reference_deleted":
        rel = ".claude/commands/rulings.md"
        _write(root, rel, _read(root, rel).replace(
            "docs/skill-self-improvement.md", "self contract omitted", 1
        ))
    elif case == "reference_orphan_h2":
        rel = "docs/dev-wave/operations.md"
        _write(root, rel, _read(root, rel) + "\n## DW-X99 — orphan\n\nbody\n")
    elif case == "dispatch_heading_duplicated":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel) + "\n## 段 dispatch\n\n")
    elif case == "dispatch_heading_missing":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel).replace(
            "## 条件 dispatch", "## 条件 dispatch omitted", 1
        ))
    elif case == "d2_rollback_body_deleted":
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        changed = re.sub(
            r"条件には最遅読了段がある。.*?旧成果物を流用してはならない。\n\n",
            "",
            text,
            count=1,
            flags=re.DOTALL,
        )
        assert changed != text
        _write(root, rel, changed)
    elif case == "d4_inheritance_body_deleted":
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        changed = re.sub(
            r"段 6 で fix を codex へ再投する子は、.*?"
            r"fix 操作の直前に読む。\n\n",
            "",
            text,
            count=1,
            flags=re.DOTALL,
        )
        assert changed != text
        _write(root, rel, changed)
    elif case == "codex_command_contract_deleted":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel).replace(
            "Codex `role=author`", "Claude `role=author`", 1,
        ))
    elif case == "codex_core_contract_deleted":
        rel = "docs/dev-wave/core.md"
        _write(root, rel, _read(root, rel).replace(
            "親は直接編集しない", "親も直接編集できる", 1,
        ))
    elif case == "codex_worker_contract_deleted":
        rel = "docs/dev-wave/workers.md"
        _write(root, rel, _read(root, rel).replace(
            "親が直接直さない", "親が直接直す", 1,
        ))
    elif case == "s09_land_route_deleted":
        rel = "docs/dev-wave/core.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                check_docs.DEV_WAVE_LAND_UNIQUE_ROUTE_LITERAL,
                "land route omitted",
                1,
            ),
        )
    elif case == "s09_acceptance_order_deleted":
        rel = "docs/dev-wave/core.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                _S09_ACCEPTANCE_ORDER_LITERAL,
                "acceptance order omitted",
                1,
            ),
        )
    elif case == "core_land_helper_outside_s09":
        rel = "docs/dev-wave/core.md"
        _write(root, rel, _read(root, rel) + "\ntools/dev_wave_land.py\n")
    elif case == "o23_land_helper_deleted":
        rel = "docs/dev-wave/operations.md"
        sections = check_docs._reference_id_sections(_read(root, rel), "DW-O23")
        assert len(sections) == 1
        _write(
            root,
            rel,
            _read(root, rel).replace(
                sections[0],
                sections[0].replace("`tools/dev_wave_land.py`", "helper omitted", 1),
                1,
            ),
        )
    elif case == "operations_land_helper_outside_o23":
        rel = "docs/dev-wave/operations.md"
        _write(root, rel, _read(root, rel) + "\ntools/dev_wave_land.py\n")
    elif case == "codex_skill_deleted":
        os.remove(os.path.join(
            root, ".agents", "skills", "dev-wave", "SKILL.md"
        ))
    elif case == "codex_skill_extra_file":
        _write(root, ".agents/skills/dev-wave/README.md", "# extra\n")
    elif case == "codex_skill_name_changed":
        rel = ".agents/skills/dev-wave/SKILL.md"
        _write(root, rel, _read(root, rel).replace(
            "name: dev-wave", "name: dev-wave-renamed", 1,
        ))
    elif case == "codex_skill_adapter_deleted":
        rel = ".agents/skills/dev-wave/SKILL.md"
        literal = check_docs.CODEX_DEV_WAVE_SKILL_LITERALS[0]
        _write(root, rel, _read(root, rel).replace(
            literal, "common dispatcher omitted", 1,
        ))
    elif case == "codex_skill_stage9_land_literal_deleted":
        rel = ".agents/skills/dev-wave/SKILL.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                check_docs.CODEX_DEV_WAVE_STAGE9_LAND_LITERAL,
                "Stage 9 Codex land contract omitted.",
                1,
            ),
        )
    elif case == "codex_skill_openai_changed":
        rel = ".agents/skills/dev-wave/agents/openai.yaml"
        _write(root, rel, _read(root, rel).replace(
            "display_name: \"Dev Wave\"",
            "display_name: \"Changed\"",
            1,
        ))
    elif case == "codex_skill_land_helper_duplicated":
        rel = ".agents/skills/dev-wave/SKILL.md"
        _write(root, rel, _read(root, rel) + "\ntools/dev_wave_land.py\n")
    elif case == "command_land_helper_duplicated":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel) + "\ntools/dev_wave_land.py\n")
    elif case == "command_alternate_land_helper":
        rel = ".claude/commands/dev-wave.md"
        _write(
            root, rel,
            _read(root, rel)
            + "\n```sh\n$ python3 tools/alternate_land.py --main main\n```\n",
        )
    elif case == "skill_alternate_land_helper":
        rel = ".agents/skills/dev-wave/SKILL.md"
        _write(
            root, rel,
            _read(root, rel)
            + "\n```sh\n$ python3 tools/alternate_land.py --main main\n```\n",
        )
    elif case == "command_direct_main_ff":
        rel = ".claude/commands/dev-wave.md"
        _write(
            root, rel,
            _read(root, rel) + "\n```sh\n$ git merge --ff-only deadbeef\n```\n",
        )
    elif case == "skill_direct_main_ff":
        rel = ".agents/skills/dev-wave/SKILL.md"
        _write(
            root, rel,
            _read(root, rel) + "\n```sh\n$ git merge --ff-only deadbeef\n```\n",
        )
    elif case == "codex_rulings_skill_deleted":
        os.remove(os.path.join(
            root, ".agents", "skills", "rulings", "SKILL.md"
        ))
    elif case == "codex_rulings_skill_extra_file":
        _write(root, ".agents/skills/rulings/README.md", "# extra\n")
    elif case == "codex_rulings_skill_name_changed":
        rel = ".agents/skills/rulings/SKILL.md"
        _write(root, rel, _read(root, rel).replace(
            "name: rulings", "name: rulings-renamed", 1,
        ))
    elif case == "codex_rulings_skill_adapter_deleted":
        rel = ".agents/skills/rulings/SKILL.md"
        literal = check_docs.CODEX_RULINGS_SKILL_LITERALS[0]
        _write(root, rel, _read(root, rel).replace(
            literal, "repository entry omitted", 1,
        ))
    elif case == "codex_rulings_skill_openai_changed":
        rel = ".agents/skills/rulings/agents/openai.yaml"
        _write(root, rel, _read(root, rel).replace(
            "display_name: \"Rulings\"",
            "display_name: \"Changed\"",
            1,
        ))
    elif case == "fifth_reference":
        _write(root, "docs/dev-wave/extra.md", "# extra\n")
    elif case == "nested_reference":
        _write(root, "docs/dev-wave/appendix/extra.md", "# extra\n")
    elif case == "non_md_reference":
        _write(root, "docs/dev-wave/extra.txt", "extra\n")
    elif case == "aggregate_over":
        for rel, limit in check_docs.REFERENCE_LIMITS.items():
            _pad_to_bytes(root, rel, limit.max_bytes - 1)
    elif case == "invalid_utf8":
        path = os.path.join(root, "docs/dev-wave/core.md")
        with open(path, "wb") as f:
            f.write(b"\xff")
    elif case == "symlink":
        path = os.path.join(root, "docs/dev-wave/core.md")
        os.remove(path)
        os.symlink("workers.md", path)
    elif case == "non_regular":
        path = os.path.join(root, "docs/dev-wave/mutation.md")
        os.remove(path)
        os.mkfifo(path)
    elif case == "registered_reference_deleted":
        os.remove(os.path.join(root, "docs/dev-wave/operations.md"))
    elif case == "dispatch_allowlist":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| wave 開始 |"),
            lambda line: line.removesuffix(" |\n")
            + "; `docs/failures.md` |\n",
        )
    else:
        raise AssertionError(f"unknown case: {case}")


_COMMAND_GUARD_CASES = [
    "command_byte_over",
    "reference_byte_over",
    "self_byte_over",
    "long_line",
    "unregistered_command",
    "registered_command_deleted",
    "arguments_missing",
    "frontmatter_key_changed",
    "frontmatter_duplicate",
    "frontmatter_malformed",
    "disable_value_changed",
    "reference_section_deleted",
    "reference_section_duplicated",
    "stage2_operations_deleted",
    "stage3_o13_deleted",
    "stage6_s05_inheritance_deleted",
    "stage6_all_operations_deleted",
    "stage8_operations_deleted",
    "stage8_self_deleted",
    "stage9_land_operation_deleted",
    "condition_o13_deleted",
    "condition_all_operations_deleted",
    "condition_supervisor_deleted",
    "condition_land_operation_deleted",
    "self_heading_deleted",
    "self_h3_deleted",
    "self_long_line",
    "self_reference_deleted",
    "reference_orphan_h2",
    "dispatch_heading_duplicated",
    "dispatch_heading_missing",
    "d2_rollback_body_deleted",
    "d4_inheritance_body_deleted",
    "codex_command_contract_deleted",
    "codex_core_contract_deleted",
    "codex_worker_contract_deleted",
    "s09_land_route_deleted",
    "s09_acceptance_order_deleted",
    "core_land_helper_outside_s09",
    "o23_land_helper_deleted",
    "operations_land_helper_outside_o23",
    "codex_skill_deleted",
    "codex_skill_extra_file",
    "codex_skill_name_changed",
    "codex_skill_adapter_deleted",
    "codex_skill_stage9_land_literal_deleted",
    "codex_skill_openai_changed",
    "codex_skill_land_helper_duplicated",
    "command_land_helper_duplicated",
    "command_alternate_land_helper",
    "skill_alternate_land_helper",
    "command_direct_main_ff",
    "skill_direct_main_ff",
    "codex_rulings_skill_deleted",
    "codex_rulings_skill_extra_file",
    "codex_rulings_skill_name_changed",
    "codex_rulings_skill_adapter_deleted",
    "codex_rulings_skill_openai_changed",
    "fifth_reference",
    "nested_reference",
    "non_md_reference",
    "aggregate_over",
    "invalid_utf8",
    "symlink",
    "non_regular",
    "registered_reference_deleted",
    "dispatch_allowlist",
]

_COMMAND_GUARD_NEEDLES = {
    "command_byte_over": "bytes > 予算",
    "reference_byte_over": "bytes > 予算",
    "self_byte_over": "bytes > 予算",
    "long_line": "最長行予算",
    "unregistered_command": "command byte予算が未登録",
    "registered_command_deleted": "予算登録済み command が不在",
    "arguments_missing": "$ARGUMENTS が 0 件",
    "frontmatter_key_changed": "frontmatter key 集合が契約と不一致",
    "frontmatter_duplicate": "frontmatter key 重複",
    "frontmatter_malformed": "frontmatter を一意に解析できない",
    "disable_value_changed": "disable-model-invocation は 'true' 必須",
    "reference_section_deleted": "H2 見出し DW-M05 が 0 件",
    "reference_section_duplicated": "H2 見出し DW-M05 が 2 件",
    "stage2_operations_deleted": "段 dispatch '段 2' が契約と不一致",
    "stage3_o13_deleted": "段 dispatch '段 3' が契約と不一致",
    "stage6_s05_inheritance_deleted": "段 dispatch '段 6' が契約と不一致",
    "stage6_all_operations_deleted": "段 dispatch '段 6' が契約と不一致",
    "stage8_operations_deleted": "段 dispatch '段 8' が契約と不一致",
    "stage8_self_deleted": "段 dispatch '段 8' が契約と不一致",
    "stage9_land_operation_deleted": "段 dispatch '段 9' が契約と不一致",
    "condition_o13_deleted": "条件 dispatch '13' が契約と不一致",
    "condition_all_operations_deleted": "条件 dispatch '01' が契約と不一致",
    "condition_supervisor_deleted": "条件 dispatch '22' が契約と不一致",
    "condition_land_operation_deleted": "条件 dispatch '23' が契約と不一致",
    "self_heading_deleted": "H2 見出し 'routing' が 0 件",
    "self_h3_deleted": "H3 見出し 'cleanup-branches' が 0 件",
    "self_long_line": "最長行予算",
    "self_reference_deleted": "docs/skill-self-improvement.md への到達性がない",
    "reference_orphan_h2": "dispatch 契約にない孤児 H2",
    "dispatch_heading_duplicated": "段/条件 dispatch 表を一意に抽出できない",
    "dispatch_heading_missing": "段/条件 dispatch 表を一意に抽出できない",
    "d2_rollback_body_deleted": "D2 巻き戻し構造",
    "d4_inheritance_body_deleted": "D4 fix 子の段5全文継承",
    "codex_command_contract_deleted": "Codex-first 実装境界",
    "codex_core_contract_deleted": "Codex-first 実装契約がない",
    "codex_worker_contract_deleted": "Codex-first 実装契約がない",
    "s09_land_route_deleted": "DW-S09 の helper 唯一経路 literal",
    "s09_acceptance_order_deleted": "DW-S09 の acceptance/O23 順序 literal",
    "core_land_helper_outside_s09": "path-section外=1",
    "o23_land_helper_deleted": "land helper path は全体で exact 1 件",
    "operations_land_helper_outside_o23": "land helper path は全体で exact 1 件",
    "codex_skill_deleted": "Codex dev-wave Skill の必須 file が不在",
    "codex_skill_extra_file": "Codex dev-wave Skill の予算未登録実体",
    "codex_skill_name_changed": "name は 'dev-wave' 必須",
    "codex_skill_adapter_deleted": "Codex adapter 契約がない",
    "codex_skill_stage9_land_literal_deleted": "exact adapter literal が 0 件",
    "codex_skill_openai_changed": "生成済み Skill interface 契約と不一致",
    "codex_skill_land_helper_duplicated": "共通 dispatcher の leaf path を重複 pin",
    "command_land_helper_duplicated": "land helper path は DW-S09 / DW-O23 だけ",
    "command_alternate_land_helper": "alternate land helper command",
    "skill_alternate_land_helper": "alternate land helper command",
    "command_direct_main_ff": "direct git merge --ff-only main mutation",
    "skill_direct_main_ff": "direct git merge --ff-only main mutation",
    "codex_rulings_skill_deleted": "Codex rulings Skill の必須 file が不在",
    "codex_rulings_skill_extra_file": "Codex rulings Skill の予算未登録実体",
    "codex_rulings_skill_name_changed": "name は 'rulings' 必須",
    "codex_rulings_skill_adapter_deleted": "Codex adapter 契約がない",
    "codex_rulings_skill_openai_changed": "生成済み Skill interface 契約と不一致",
    "fifth_reference": "docs/dev-wave/** の予算未登録実体",
    "nested_reference": "docs/dev-wave/** の予算未登録実体",
    "non_md_reference": "docs/dev-wave/** の予算未登録実体",
    "aggregate_over": "hard ceiling",
    "invalid_utf8": "invalid UTF-8",
    "symlink": "symlink または regular file 以外",
    "non_regular": "symlink または regular file 以外",
    "registered_reference_deleted": "登録済み dev-wave reference が不在",
    "dispatch_allowlist": "規範 dispatch の参照先が allowlist 外",
}
_COMMAND_GUARD_EXPECTED_COUNTS = {
    case: 1 for case in _COMMAND_GUARD_CASES
}
_COMMAND_GUARD_EXPECTED_COUNTS["condition_all_operations_deleted"] = len(
    _OPERATION_CONDITION_KEYS
)


def test_operation_contract_pins_exact_section_set():
    """operations 契約の外延と配線を literal で固定する (O15 削除後の 19 節)。

    checker とテスト fixture は同じ `_OPERATION_NUMBERS` から導出される (F9 型の
    自己整合面)。fixture の literal range 表記が単純な縮小・拡大を先に赤くし、
    本 pin は誤配線と外延の完全性を固定する — 二つの独立面の役割分担であり、
    どちらも単独の oracle ではない。
    """
    operations = "docs/dev-wave/operations.md"
    expected = {
        "DW-O01", "DW-O02", "DW-O03", "DW-O04", "DW-O05", "DW-O06",
        "DW-O08", "DW-O09", "DW-O10", "DW-O11", "DW-O12", "DW-O13",
        "DW-O14", "DW-O16", "DW-O17", "DW-O18", "DW-O19", "DW-O20",
        "DW-O23",
    }
    assert check_docs.REQUIRED_REFERENCE_SECTIONS[operations] == expected
    assert check_docs._ALL_OPERATIONS == frozenset(
        (operations, section) for section in expected
    )
    for section in sorted(expected):
        key = section.removeprefix("DW-O")
        operations_pairs = {
            pair
            for pair in check_docs.CONDITION_DISPATCH_CONTRACT[key]
            if pair[0] == operations
        }
        assert operations_pairs == {(operations, section)}, (
            f"条件 {key} の operations 配線が {section} 単独でない"
        )
    assert check_docs.CONDITION_DISPATCH_CONTRACT["15"] == {
        ("docs/dev-wave/mutation.md", "DW-M07")
    }
    assert _OPERATION_CONDITION_KEYS == sorted(
        section.removeprefix("DW-O") for section in expected
    )
    for stage in ("段 5", "段 6"):
        assert check_docs._ALL_OPERATIONS <= (
            check_docs.STAGE_DISPATCH_CONTRACT[stage]
        ), f"{stage} が operations 全節を消費していない"
    assert (
        "docs/dev-wave/operations.md", "DW-O23"
    ) in check_docs.STAGE_DISPATCH_CONTRACT["段 9"]
    assert check_docs.DEV_WAVE_LAND_HELPER == "tools/dev_wave_land.py"
    assert check_docs.DEV_WAVE_LAND_UNIQUE_ROUTE_LITERAL == (
        "`tools/dev_wave_land.py` は local main を変更する唯一の通常 land 経路"
    )
    assert check_docs.DEV_WAVE_S09_ACCEPTANCE_ORDER_LITERAL == (
        _S09_ACCEPTANCE_ORDER_LITERAL
    )
    assert check_docs.CODEX_DEV_WAVE_STAGE9_LAND_LITERAL == (
        "段 9 は dispatcher が指定する共通 land 契約だけに従い、"
        "Codex 固有の取り込み手順を重ねない。"
    )


def _replace_workers_section_literal(text, section_id, replacement):
    match = re.search(
        rf"^## {re.escape(section_id)}(?:\s+—[^\n]*)?\s*$\n.*?(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    section = match.group(0)
    literal = {
        "DW-S02": check_docs.DEV_WAVE_DW_S02_REASONING_MAX_LITERAL,
        "DW-S03": check_docs.DEV_WAVE_DW_S03_REASONING_MAX_LITERAL,
    }[section_id]
    changed_section = section.replace(literal, replacement, 1)
    assert changed_section != section
    return text[:match.start()] + changed_section + text[match.end():]


def _mutated_workers_text(root, section_id, replacement):
    target = os.path.join(root, "workers.md")
    shutil.copyfile(
        os.path.join(_REPO, "docs", "dev-wave", "workers.md"),
        target,
    )
    with open(target, encoding="utf-8") as stream:
        text = stream.read()
    _write(
        root,
        "workers.md",
        _replace_workers_section_literal(text, section_id, replacement),
    )
    return _read(root, "workers.md")


def _reasoning_effort_pin_findings(workers_text):
    findings = []
    check_docs._check_dev_wave_reasoning_effort_pins(workers_text, findings)
    return findings


def test_dev_wave_reasoning_effort_pins_accept_current_workers_contract():
    workers = os.path.join(_REPO, "docs", "dev-wave", "workers.md")
    with open(workers, encoding="utf-8") as stream:
        assert _reasoning_effort_pin_findings(stream.read()) == []


def test_dev_wave_reasoning_effort_pin_rejects_dw_s02_high():
    root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
    try:
        text = _mutated_workers_text(root, "DW-S02", "`reasoning=high`")
        assert _reasoning_effort_pin_findings(text) == [
            check_docs.DEV_WAVE_DW_S02_REASONING_MAX_FINDING
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_dw_s03_high():
    root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
    try:
        text = _mutated_workers_text(root, "DW-S03", "`reasoning=high`")
        assert _reasoning_effort_pin_findings(text) == [
            check_docs.DEV_WAVE_DW_S03_REASONING_MAX_FINDING
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_missing_dw_s02_value():
    root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
    try:
        text = _mutated_workers_text(root, "DW-S02", "")
        assert _reasoning_effort_pin_findings(text) == [
            check_docs.DEV_WAVE_DW_S02_REASONING_MAX_FINDING
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_missing_dw_s03_value():
    root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
    try:
        text = _mutated_workers_text(root, "DW-S03", "")
        assert _reasoning_effort_pin_findings(text) == [
            check_docs.DEV_WAVE_DW_S03_REASONING_MAX_FINDING
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _assert_reasoning_effort_decoys_rejected(section_id, finding):
    replacements = (
        "`reasoning=high` <!-- `reasoning=max` -->",
        "`reasoning=high`\n\n```\n`reasoning=max`\n```\ncontinuation",
        "`reasoning=high`\n\n> `reasoning=max`\n\ncontinuation",
        "`reasoning=max` and `reasoning=high`",
        "`reasoning=max` and `reasoning=max`",
    )
    for replacement in replacements:
        root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
        try:
            text = _mutated_workers_text(root, section_id, replacement)
            assert _reasoning_effort_pin_findings(text) == [finding]
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_dw_s02_decoys_and_duplicates():
    _assert_reasoning_effort_decoys_rejected(
        "DW-S02",
        check_docs.DEV_WAVE_DW_S02_REASONING_MAX_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_rejects_dw_s03_decoys_and_duplicates():
    _assert_reasoning_effort_decoys_rejected(
        "DW-S03",
        check_docs.DEV_WAVE_DW_S03_REASONING_MAX_FINDING,
    )


def _assert_reasoning_effort_real_keys_and_quotes_rejected(section_id, finding):
    replacements = (
        '`model_reasoning_effort="high"`（例: `reasoning=max`）',
        '`model_reasoning_effort="high"`',
        "`model_reasoning_effort='high'`",
        '`reasoning_effort=high` and `reasoning=max`',
        '`reasoning=max`\n\n> `reasoning=high`\n\ncontinuation',
        '`model_reasoning_effort="high"` <!-- `reasoning=max` -->',
    )
    for replacement in replacements:
        root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
        try:
            text = _mutated_workers_text(root, section_id, replacement)
            assert _reasoning_effort_pin_findings(text) == [finding]
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_dw_s02_real_keys_and_quotes():
    _assert_reasoning_effort_real_keys_and_quotes_rejected(
        "DW-S02",
        check_docs.DEV_WAVE_DW_S02_REASONING_MAX_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_rejects_dw_s03_real_keys_and_quotes():
    _assert_reasoning_effort_real_keys_and_quotes_rejected(
        "DW-S03",
        check_docs.DEV_WAVE_DW_S03_REASONING_MAX_FINDING,
    )


def test_dev_wave_reasoning_effort_pins_ignore_comment_and_fence_examples():
    replacements = (
        '`reasoning=max` <!-- `model_reasoning_effort="high"` -->',
        '`reasoning=max`\n\n```\n`reasoning_effort=high`\n```\ncontinuation',
        (
            '`reasoning=max` and `pre_model_reasoning_effort=high` and '
            '`reasoning_effort_extra=high`'
        ),
    )
    for section_id in ("DW-S02", "DW-S03"):
        for replacement in replacements:
            root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
            try:
                text = _mutated_workers_text(root, section_id, replacement)
                assert _reasoning_effort_pin_findings(text) == []
            finally:
                shutil.rmtree(root, ignore_errors=True)


def _assert_reasoning_effort_production_path_rejects(section_id, finding):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/workers.md"
        _write(
            root,
            rel,
            _replace_workers_section_literal(
                _read(root, rel),
                section_id,
                "`reasoning=high`",
            ),
        )
        res = _run_check(root)
        assert res.returncode != 0, res.stdout
        assert finding in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s02_high():
    _assert_reasoning_effort_production_path_rejects(
        "DW-S02",
        check_docs.DEV_WAVE_DW_S02_REASONING_MAX_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s03_high():
    _assert_reasoning_effort_production_path_rejects(
        "DW-S03",
        check_docs.DEV_WAVE_DW_S03_REASONING_MAX_FINDING,
    )


def _assert_reasoning_effort_real_key_production_path_rejects(
    section_id,
    finding,
):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/workers.md"
        _write(
            root,
            rel,
            _replace_workers_section_literal(
                _read(root, rel),
                section_id,
                '`model_reasoning_effort="high"`（例: `reasoning=max`）',
            ),
        )
        res = _run_check(root)
        assert res.returncode != 0, res.stdout
        assert finding in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s02_real_key():
    _assert_reasoning_effort_real_key_production_path_rejects(
        "DW-S02",
        check_docs.DEV_WAVE_DW_S02_REASONING_MAX_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s03_real_key():
    _assert_reasoning_effort_real_key_production_path_rejects(
        "DW-S03",
        check_docs.DEV_WAVE_DW_S03_REASONING_MAX_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_findings_are_time_invariant():
    expected_suffix = (
        "現行 adoption pin と不一致 — 変更には paired・blind・非劣性 A/B に基づく"
        "採用裁定と pin の同時更新が必要"
    )
    assert check_docs.DEV_WAVE_DW_S02_REASONING_MAX_FINDING == (
        "docs/dev-wave/workers.md: DW-S02 の `reasoning=max` は D207 に基づく"
        + expected_suffix
    )
    assert check_docs.DEV_WAVE_DW_S03_REASONING_MAX_FINDING == (
        "docs/dev-wave/workers.md: DW-S03 の `reasoning=max` は D207 に基づく"
        + expected_suffix
    )


def test_codex_dev_wave_skill_contract_pins_exact_surface():
    """checker と合成 fixture の同時縮小で adapter 義務が消えないよう外延を固定する。"""

    assert check_docs.CODEX_DEV_WAVE_SKILL_FILES == {
        ".agents/skills/dev-wave/SKILL.md",
        ".agents/skills/dev-wave/agents/openai.yaml",
    }
    assert check_docs.CODEX_DEV_WAVE_SKILL_LITERALS == (
        ".claude/commands/dev-wave.md",
        "docs/skill-self-improvement.md",
        "docs/dev-wave/workers.md",
        "docs/dev-wave/operations.md",
        "manager は実装面を直接編集しない",
        "codex exec",
        "collaboration child",
        ".codex/role-adapters/*.json",
        "hooks/README.md",
        "supervised manifest",
        "段 1〜9",
        "local main",
    )
    assert check_docs.CODEX_DEV_WAVE_OPENAI_YAML == (
        'interface:\n'
        '  display_name: "Dev Wave"\n'
        '  short_description: "Izanagi の開発 wave を共通契約に従って実行"\n'
        '  default_prompt: "Use $dev-wave to run one Izanagi development wave '
        'for the specified task."\n'
    )


def test_codex_rulings_skill_contract_pins_exact_surface():
    """checker と合成 fixture の同時縮小で adapter 義務が消えないよう外延を固定する。"""

    assert check_docs.CODEX_RULINGS_SKILL_FILES == {
        ".agents/skills/rulings/SKILL.md",
        ".agents/skills/rulings/agents/openai.yaml",
    }
    assert check_docs.CODEX_RULINGS_SKILL_LITERALS == (
        "AGENTS.md",
        "CLAUDE.md",
        ".claude/commands/rulings.md",
        "$ARGUMENTS",
        "$rulings",
        "docs/worklog.md",
        "docs/skill-self-improvement.md",
        "hooks/README.md",
        "クラス 1",
        "クラス 2",
        "それ以外ではファイルを編集しない",
        "push と remote branch 操作は人間に残す",
    )
    assert check_docs.CODEX_RULINGS_OPENAI_YAML == (
        'interface:\n'
        '  display_name: "Rulings"\n'
        '  short_description: "Izanagi の裁定待ちを索引・詳説して判断を補佐"\n'
        '  default_prompt: "Use $rulings to list and explain the Izanagi '
        'decisions awaiting my ruling."\n'
    )


def test_codex_cleanup_branches_skill_contract_pins_exact_surface():
    """checker と test fixture の whole-file pin を独立 literal で固定する。"""

    assert check_docs.CODEX_CLEANUP_BRANCHES_SKILL_FILES == {
        ".agents/skills/cleanup-branches/SKILL.md",
        ".agents/skills/cleanup-branches/agents/openai.yaml",
    }
    assert check_docs.CODEX_CLEANUP_BRANCHES_SKILL_LIMITS == {
        ".agents/skills/cleanup-branches/SKILL.md":
            check_docs.TextLimit(3_100, 210),
        ".agents/skills/cleanup-branches/agents/openai.yaml":
            check_docs.TextLimit(300, 110),
    }
    assert check_docs.CODEX_CLEANUP_BRANCHES_DESCRIPTION == (
        _SYNTHETIC_CLEANUP_DESCRIPTION
    )
    assert check_docs.CODEX_CLEANUP_BRANCHES_OPENAI_YAML == (
        _SYNTHETIC_CLEANUP_OPENAI_YAML
    )
    assert check_docs.CODEX_CLEANUP_BRANCHES_SKILL_SHA256 == (
        _EXPECTED_CLEANUP_SKILL_SHA256
    )
    assert check_docs.CLEANUP_COMMAND_SHA256 == (
        _EXPECTED_CLEANUP_COMMAND_SHA256
    )
    assert hashlib.sha256(
        _SYNTHETIC_CLEANUP_SKILL.encode("utf-8")
    ).hexdigest() == _EXPECTED_CLEANUP_SKILL_SHA256
    assert hashlib.sha256(
        _SYNTHETIC_CLEANUP_COMMAND.encode("utf-8")
    ).hexdigest() == _EXPECTED_CLEANUP_COMMAND_SHA256


def test_command_docs_guard_rejects_symlinked_commands_directory():
    root = _build_min_repo()
    external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_commands_")
    try:
        command_dir = os.path.join(root, ".claude", "commands")
        shutil.copytree(command_dir, external, dirs_exist_ok=True)
        _write(
            external,
            "EXTERNAL-COMMAND-SENTINEL.md",
            "# EXTERNAL-COMMAND-SENTINEL\n",
        )
        shutil.rmtree(command_dir)
        os.symlink(external, command_dir)
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert re.search(
            r"^check_docs: \d+ 件の違反$", res.stdout, re.MULTILINE
        ), res.stdout
        assert ".claude/commands: command directory が symlink" in res.stdout
        assert "EXTERNAL-COMMAND-SENTINEL" not in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(external, ignore_errors=True)


@pytest.mark.parametrize("case", _COMMAND_GUARD_CASES)
def test_command_docs_guard_positive_controls(case):
    """各 finding 分岐は baseline からケース別の期待件数だけ増える。"""

    root = _build_min_repo()
    try:
        baseline = _run_check(root)
        assert baseline.returncode == 0, baseline.stdout
        _mutate_command_guard(root, case)
        res = _run_check(root)
        assert res.returncode == 1, (
            f"{case}: positive control が赤にならなかった:\n{res.stdout}\n{res.stderr}"
        )
        assert _violation_count(res) == _COMMAND_GUARD_EXPECTED_COUNTS[case], (
            f"{case}: baseline との差分件数が期待値と違う:\n{res.stdout}"
        )
        assert _COMMAND_GUARD_NEEDLES[case] in res.stdout, (
            f"{case}: 対応する finding 分岐が発火していない:\n{res.stdout}"
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _assert_cleanup_digest_violation(root: str, rel: str) -> None:
    res = _run_check(root)
    assert res.returncode == 1, res.stdout
    assert _violation_count(res) == 1, res.stdout
    assert f"{rel}: whole-file SHA-256 が契約と不一致" in res.stdout


def test_cleanup_skill_one_byte_change_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".agents/skills/cleanup-branches/SKILL.md"
        original = _read(root, rel)
        changed = original.replace("cleanup dispatcher", "cleanvp dispatcher", 1)
        assert len(changed.encode("utf-8")) == len(original.encode("utf-8"))
        assert sum(a != b for a, b in zip(
            changed.encode("utf-8"), original.encode("utf-8")
        )) == 1
        _write(root, rel, changed)
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_command_one_byte_change_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        original = _read(root, rel)
        changed = original.replace("(クラス 2)", "(クラス 3)", 1)
        assert len(changed.encode("utf-8")) == len(original.encode("utf-8"))
        assert sum(a != b for a, b in zip(
            changed.encode("utf-8"), original.encode("utf-8")
        )) == 1
        _write(root, rel, changed)
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_skill_additional_h2_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".agents/skills/cleanup-branches/SKILL.md"
        _write(root, rel, _read(root, rel) + "\n## destructive override\n")
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_command_closing_hash_h2_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        _write(root, rel, _read(root, rel).replace(
            "## 4. 事後検査", "## 4. 事後検査 ##", 1
        ))
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_command_leading_space_h2_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        _write(root, rel, _read(root, rel).replace(
            "## 4. 事後検査", " ## 4. 事後検査", 1
        ))
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_command_setext_h2_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        _write(root, rel, _read(root, rel).replace(
            "## 4. 事後検査", "4. 事後検査\n------------", 1
        ))
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_command_invalid_backtick_info_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        _write(root, rel, _read(root, rel) + "\n```x`x\n## x\n```\n")
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_metadata_policy_change_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".agents/skills/cleanup-branches/agents/openai.yaml"
        _write(root, rel, _read(root, rel).replace(
            "allow_implicit_invocation: false",
            "allow_implicit_invocation: true",
            1,
        ))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1, res.stdout
        assert "生成済み Skill interface 契約と不一致" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_land_route_guard_does_not_overmatch_ordinary_prose():
    root = _build_min_repo()
    try:
        additions = {
            ".claude/commands/dev-wave.md": (
                "\n通常の説明では `tools/alternate_land.py` や "
                "`python ./tools/alternate_land.py`、"
                "`git -C <main> merge deadbeef --ff-only` "
                "という文字列を引用できる。\n"
            ),
            ".agents/skills/dev-wave/SKILL.md": (
                "\n通常の説明として alternate land helper と "
                "`python3 tools/alternate_land.py`、"
                "`git merge --no-edit deadbeef --ff-only` "
                "を論じても実行経路ではない。\n"
            ),
        }
        for rel, prose in additions.items():
            _write(root, rel, _read(root, rel) + prose)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_land_route_guard_rejects_command_syntax_variants_independently():
    cases = (
        (
            ".claude/commands/dev-wave.md",
            "python tools/alternate_land.py --main main",
            "alternate land helper command",
        ),
        (
            ".agents/skills/dev-wave/SKILL.md",
            "$ python3 ./tools/alternate_land.py --main main",
            "alternate land helper command",
        ),
        (
            ".claude/commands/dev-wave.md",
            "$ python ./tools/second_land.py --main main",
            "alternate land helper command",
        ),
        (
            ".agents/skills/dev-wave/SKILL.md",
            "python3 tools/second_land.py --main main",
            "alternate land helper command",
        ),
        (
            ".claude/commands/dev-wave.md",
            "git merge deadbeef --ff-only",
            "direct git merge --ff-only main mutation",
        ),
        (
            ".agents/skills/dev-wave/SKILL.md",
            "$ git -C <main> merge deadbeef --ff-only",
            "direct git merge --ff-only main mutation",
        ),
        (
            ".claude/commands/dev-wave.md",
            "git -C /tmp/main merge --no-edit --ff-only deadbeef",
            "direct git merge --ff-only main mutation",
        ),
        (
            ".agents/skills/dev-wave/SKILL.md",
            "$ git merge --no-edit deadbeef --ff-only",
            "direct git merge --ff-only main mutation",
        ),
        (
            ".claude/commands/dev-wave.md",
            "python3 -u tools/alternate_land.py",
            "alternate land helper command",
        ),
        (
            ".agents/skills/dev-wave/SKILL.md",
            "python -B -W ignore ./tools/alternate_land.py",
            "alternate land helper command",
        ),
        (
            ".claude/commands/dev-wave.md",
            "git --no-pager -C main merge --ff-only T",
            "direct git merge --ff-only main mutation",
        ),
        (
            ".agents/skills/dev-wave/SKILL.md",
            "git -c advice.detachedHead=false -C main merge T --ff-only",
            "direct git merge --ff-only main mutation",
        ),
    )
    for rel, command, needle in cases:
        root = _build_min_repo()
        try:
            _write(root, rel, _read(root, rel) + f"\n```sh\n{command}\n```\n")
            res = _run_check(root)
            assert res.returncode == 1, (
                f"{rel}: variant was accepted: {command!r}\n{res.stdout}"
            )
            assert needle in res.stdout, (command, res.stdout)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_land_route_guard_allows_non_land_and_non_ff_commands():
    root = _build_min_repo()
    try:
        additions = {
            ".claude/commands/dev-wave.md": (
                "\n```sh\n"
                "python3 -u tools/alternate_plan.py\n"
                "git --no-pager -C main merge T\n"
                "```\n"
            ),
            ".agents/skills/dev-wave/SKILL.md": (
                "\n```sh\n"
                "python -B -W ignore ./tools/report.py\n"
                "git -c advice.detachedHead=false merge --no-ff T\n"
                "```\n"
            ),
        }
        for rel, commands in additions.items():
            _write(root, rel, _read(root, rel) + commands)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== positive control: 列挙対象を 1 個消すと違反が出る (F9 の核心) =====

def test_missing_enumerated_doc_is_violation():
    root = _build_min_repo()
    try:
        rels = _enumerated_rels()
        assert rels, "列挙対象が空 — _ENUMERATED_DOCS の抽出に失敗している"
        governed = {
            *check_docs.REFERENCE_LIMITS,
            *check_docs.SELF_LIMITS,
            *check_docs.PROVENANCE_LIMITS,
        }
        candidates = [rel for rel in rels if rel not in governed]
        assert candidates, "command guard 外の LIVING_DOCS 対象がない"
        victim = candidates[len(candidates) // 2]
        os.remove(os.path.join(root, victim))
        res = _run_check(root)
        assert res.returncode == 1, f"列挙対象不在なのに fail しなかった:\n{res.stdout}"
        assert "列挙対象が不在" in res.stdout, res.stdout
        assert victim in res.stdout, f"消した {victim} が finding に出ていない:\n{res.stdout}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_missing_enumerated_doc_only_fires_own_finding():
    # 不在検査だけが増える (他の検査を巻き添えにしない) ことを固定 — baseline との差分は 1 件。
    root = _build_min_repo()
    try:
        rels = _enumerated_rels()
        victim = rels[0]
        os.remove(os.path.join(root, victim))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1, (
            f"不在検査以外も発火している:\n{res.stdout}"
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== T-143: RuleOps living doc の独立 literal pin / 行番号参照 positive control =====

def test_ruleops_doc_is_literal_pinned_as_enumerated_living_doc():
    assert "docs/ruleops.md" in _enumerated_rels()


def test_ruleops_line_reference_is_own_violation():
    root = _build_min_repo()
    try:
        baseline = _run_check(root)
        assert baseline.returncode == 0, baseline.stdout
        _write(
            root,
            os.path.join("docs", "ruleops.md"),
            "# synthetic RuleOps\n\n`ruleops.md:12` を参照する。\n",
        )
        result = _run_check(root)
        assert result.returncode == 1, result.stdout
        assert _violation_count(result) == 1, result.stdout
        assert "docs の行番号参照 (腐敗する)" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== V19a: output の生きた README を検査網へ固定 =====

def test_output_readmes_are_enumerated_and_valid_fixture_is_clean():
    expected = {"output/README.md", "output/task-runs/README.md"}
    assert expected <= set(_enumerated_rels())
    root = _build_min_repo()
    try:
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_broken_reference_in_task_runs_readme_is_positive_control():
    """対象を列挙しただけの恒真化を防ぎ、本文 lint が実際に発火することを固定。"""

    root = _build_min_repo()
    try:
        victim = "output/task-runs/README.md"
        _write(root, victim, "# task-runs\n\n壊れた参照: tools/definitely-missing.py\n")
        res = _run_check(root)
        assert res.returncode == 1, f"壊れた参照が赤にならなかった:\n{res.stdout}"
        assert victim in res.stdout, res.stdout
        assert "実在しないパス参照" in res.stdout, res.stdout
        assert "tools/definitely-missing.py" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_missing_task_runs_readme_is_violation():
    root = _build_min_repo()
    try:
        victim = "output/task-runs/README.md"
        os.remove(os.path.join(root, victim))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert victim in res.stdout, res.stdout
        assert "列挙対象が不在" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== backlog guard: fail-closed の全構造分岐 =====

def test_backlog_guard_missing_worklog_is_violation():
    root = _build_min_repo()
    try:
        os.remove(os.path.join(root, "docs", "worklog.md"))
        _assert_violation(root, "docs/worklog.md: ファイルが不在")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_missing_phase3_is_violation():
    root = _build_min_repo()
    try:
        os.remove(os.path.join(root, "docs", "phase3.md"))
        _assert_violation(root, "docs/phase3.md: ファイルが不在")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_rotation_heading_must_be_unique():
    fixtures = {
        "zero": _CLEAN_WORKLOG.replace("## ローテーション\n", ""),
        "multiple": _CLEAN_WORKLOG.replace(
            "## ローテーション\n", "## ローテーション\n\n## ローテーション (duplicate)\n", 1
        ),
    }
    for name, worklog in fixtures.items():
        root = _build_min_repo()
        try:
            _write_backlog_docs(root, worklog_text=worklog)
            expected = "`## ローテーション` が 0 件" if name == "zero" else "`## ローテーション` が 2 件"
            _assert_violation(root, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_entry_title_must_fullmatch():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "## 2026-08-02 (2) — second", "## 補助見出し (entry ではない)"
        )
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "worklog entry title に full-match しない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_zero_entries_is_violation():
    root = _build_min_repo()
    try:
        _write_backlog_docs(root, worklog_text="# worklog\n\n## ローテーション\n")
        _assert_violation(root, "worklog エントリが 0 件")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_next_action_section_must_be_unique():
    fixtures = {
        "zero": _CLEAN_WORKLOG.replace("### 次の一手\n1. [T-001] carry\n", "本文だけ。\n", 1),
        "multiple": _CLEAN_WORKLOG.replace(
            "### 次の一手\n1. [T-001] carry\n",
            "### 次の一手\n1. [T-001] carry\n\n### 次の一手 (duplicate)\n1. [T-003] duplicate\n",
            1,
        ),
    }
    for name, worklog in fixtures.items():
        root = _build_min_repo()
        try:
            _write_backlog_docs(root, worklog_text=worklog)
            count = "0 件" if name == "zero" else "2 件"
            _assert_violation(root, "`### 次の一手`", count, "source を一意に抽出できない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_deferred_ledger_section_must_be_unique():
    fixtures = {
        "zero": _CLEAN_PHASE3.replace("## 見送り台帳 (synthetic)", "## 別の台帳"),
        "multiple": _CLEAN_PHASE3.replace(
            "### 裁定・完了記録",
            "## 見送り台帳 (duplicate)\n\n- duplicate\n\n### 裁定・完了記録",
        ),
    }
    for name, phase3 in fixtures.items():
        root = _build_min_repo()
        try:
            _write_backlog_docs(root, phase3_text=phase3)
            count = "0 件" if name == "zero" else "2 件"
            _assert_violation(root, "`## 見送り台帳`", count, "sink を一意に抽出できない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_completion_record_section_must_be_unique():
    fixtures = {
        "zero": _CLEAN_PHASE3.replace("### 裁定・完了記録", "### 別の記録"),
        "multiple": _CLEAN_PHASE3.replace(
            "## 残存リスク",
            "### 裁定・完了記録 (duplicate)\n\n- duplicate\n\n## 残存リスク",
        ),
    }
    for name, phase3 in fixtures.items():
        root = _build_min_repo()
        try:
            _write_backlog_docs(root, phase3_text=phase3)
            count = "0 件" if name == "zero" else "2 件"
            _assert_violation(root, "`### 裁定・完了記録`", count, "終端を一意に抽出できない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_completion_record_must_follow_ledger():
    root = _build_min_repo()
    try:
        phase3 = """# phase

### 裁定・完了記録

- completed

## 見送り台帳

- [T-900] deferred
"""
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "`### 裁定・完了記録` が `## 見送り台帳` より後にない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_zero_entries_with_valid_ids_is_violation():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("[T-001]", "legacy", 2).replace("[T-002]", "legacy")
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "有効 ID を持つエントリが 1 件もない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_latest_item_requires_id():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("1. [T-002] continue", "1. missing ID")
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "末尾エントリ", "項目先頭に有効な [T-NNN] ID がない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_latest_next_action_rejects_duplicate_ids():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "1. [T-002] continue", "1. [T-002] first\n2. [T-002] duplicate"
        )
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "`### 次の一手` 内で ID [T-002] が重複")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_id_bearing_middle_entry_requires_ids_on_all_items():
    root = _build_min_repo()
    try:
        worklog = """# worklog

## ローテーション

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — second

- [T-001] consumed

### 次の一手
1. missing ID

## 2026-08-03 (3) — third

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(
            root,
            "エントリ '2026-08-02 (2) — second'",
            "項目先頭に有効な [T-NNN] ID がない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_id_bearing_middle_entry_rejects_duplicate_ids():
    root = _build_min_repo()
    try:
        worklog = """# worklog

## ローテーション

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — second

- [T-001] consumed

### 次の一手
1. [T-002] first
2. [T-002] duplicate

## 2026-08-03 (3) — third

- [T-002] consumed

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(
            root,
            "エントリ '2026-08-02 (2) — second'",
            "`### 次の一手` 内で ID [T-002] が重複",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ledger_rejects_invalid_id_format():
    root = _build_min_repo()
    try:
        phase3 = _CLEAN_PHASE3.replace("[T-900]", "[T-01]")
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "見送り台帳の項目先頭 ID '[T-01]' が不正形式")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ledger_rejects_duplicate_ids():
    root = _build_min_repo()
    try:
        phase3 = _CLEAN_PHASE3.replace(
            "- [T-900] deferred item", "- [T-900] first\n- [T-900] duplicate"
        )
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "見送り台帳の ID [T-900] が重複")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ledger_live_item_requires_id():
    root = _build_min_repo()
    try:
        phase3 = _CLEAN_PHASE3.replace("- [T-900] deferred item", "- deferred item")
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "見送り台帳の生存項目先頭に有効な [T-NNN] ID がない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ledger_struck_item_rejects_id():
    root = _build_min_repo()
    try:
        phase3 = _CLEAN_PHASE3.replace(
            "### 裁定・完了記録",
            "- ~~[T-901] retired item~~\n\n### 裁定・完了記録",
        )
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "見送り台帳の取り消し線項目に ID '[T-901]' がある")
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== backlog guard: 保存則の正例 =====

def test_backlog_guard_carried_id_in_next_action_is_clean():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "- [T-001] consumed\n\n### 次の一手\n1. [T-002] continue",
            "本文。\n\n### 次の一手\n1. [T-001] continue",
        )
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_id_only_item_is_source_and_sink():
    """ID 単独 source も D70 の対象とし、次 entry での脱落を具体 finding にする。"""

    id_only_source = _CLEAN_WORKLOG.replace("1. [T-001] carry", "- [T-001]")
    root = _build_min_repo()
    try:
        id_only_sink = id_only_source.replace("- [T-001] consumed", "- [T-001]")
        _write_backlog_docs(root, worklog_text=id_only_sink)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        dropped = id_only_source.replace("- [T-001] consumed", "本文。")
        _write_backlog_docs(root, worklog_text=dropped)
        _assert_violation(
            root,
            "次の一手 ID [T-001]",
            "後続エントリ",
            "見送り台帳にもない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_consumed_id_in_body_is_clean():
    root = _build_min_repo()
    try:
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_deferred_id_in_ledger_is_clean():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed\n\n", "本文。\n\n")
        phase3 = _CLEAN_PHASE3.replace("[T-900]", "[T-001]")
        _write_backlog_docs(root, worklog_text=worklog, phase3_text=phase3)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_pre_id_transition_is_not_applicable():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("1. [T-001] carry", "1. legacy item").replace(
            "- [T-001] consumed\n\n", "本文。\n\n"
        )
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_source_is_only_next_action_in_three_entry_chain():
    root = _build_min_repo()
    try:
        worklog = """# worklog

## ローテーション

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — second

- [T-001] consumed

### 次の一手
1. [T-002] carry

## 2026-08-03 (3) — third

- [T-002] consumed

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_four_digit_id_is_clean():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("[T-002]", "[T-1000]")
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== backlog guard: 保存則の負例 =====

def test_backlog_guard_dropped_id_is_violation():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed\n\n", "本文。\n\n")
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "次の一手 ID [T-001]", "後続エントリ")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_prose_and_html_comment_do_not_satisfy_sink():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "- [T-001] consumed",
            "本文で [T-001] に言及する。\n\n<!-- [T-001] はここにあるだけ -->",
        )
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "次の一手 ID [T-001]", "後続エントリ")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_fences_and_multiline_comment_do_not_satisfy_sink():
    hidden_sinks = {
        "backtick fence": "```text\n- [T-001] dummy\n```",
        "tilde fence": "~~~text\n- [T-001] dummy\n~~~",
        "HTML comment": "<!--\n- [T-001] dummy\n-->",
    }
    for name, hidden_sink in hidden_sinks.items():
        root = _build_min_repo()
        try:
            worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed", hidden_sink)
            _write_backlog_docs(root, worklog_text=worklog)
            _assert_violation(root, "次の一手 ID [T-001]", "後続エントリ")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_hidden_ledger_items_do_not_satisfy_sink():
    hidden_sinks = {
        "backtick fence": "```text\n- [T-001] dummy\n```",
        "tilde fence": "~~~text\n- [T-001] dummy\n~~~",
        "HTML comment": "<!--\n- [T-001] dummy\n-->",
    }
    for name, hidden_sink in hidden_sinks.items():
        root = _build_min_repo()
        try:
            worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed\n\n", "本文。\n\n")
            phase3 = _CLEAN_PHASE3.replace(
                "- [T-900] deferred item",
                f"- [T-900] deferred item\n\n{hidden_sink}",
            )
            _write_backlog_docs(root, worklog_text=worklog, phase3_text=phase3)
            _assert_violation(root, "次の一手 ID [T-001]", "見送り台帳にもない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_hidden_ledger_items_are_not_live_items():
    hidden_items = {
        "backtick fence": "```text\n- missing ID\n```",
        "tilde fence": "~~~text\n- missing ID\n~~~",
        "HTML comment": "<!--\n- missing ID\n-->",
    }
    for name, hidden_item in hidden_items.items():
        root = _build_min_repo()
        try:
            phase3 = _CLEAN_PHASE3.replace(
                "- [T-900] deferred item",
                f"- [T-900] deferred item\n\n{hidden_item}",
            )
            _write_backlog_docs(root, phase3_text=phase3)
            res = _run_check(root)
            assert res.returncode == 0, f"{name}:\n{res.stdout}"
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_rejects_redundant_zero_padding():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("[T-002]", "[T-0001]")
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "項目先頭 ID '[T-0001]' が不正形式")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_completion_record_does_not_satisfy_sink():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed\n\n", "本文。\n\n")
        phase3 = _CLEAN_PHASE3.replace("- completed item", "- [T-001] completed item")
        _write_backlog_docs(root, worklog_text=worklog, phase3_text=phase3)
        _assert_violation(root, "次の一手 ID [T-001]", "見送り台帳にもない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_all_adjacent_transitions():
    root = _build_min_repo()
    try:
        worklog = """# worklog

## ローテーション

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] dropped in middle

## 2026-08-02 (2) — second

- [T-900] unrelated

### 次の一手
1. [T-002] carried

## 2026-08-03 (3) — third

- [T-002] consumed

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        res = _assert_violation(root, "次の一手 ID [T-001]")
        assert "次の一手 ID [T-002]" not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_latest_archive_rotation_boundary():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-08-02 (2) — current first

### 次の一手
1. [T-002] current
"""
        archive_name = "worklog-synthetic-latest.md"
        archive = """# archive

## 2026-08-01 (1) — archive last

### 次の一手
1. [T-001] lost at rotation
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", archive_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(archive_name),
        )
        _assert_violation(root, archive_name, "次の一手 ID [T-001]", "current first")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_archive_internal_transitions():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-08-03 (3) — current

- [T-002] consumed

### 次の一手
1. [T-003] current
"""
        archive_name = "worklog-synthetic.md"
        archive = """# archive

## 2026-08-01 (1) — archive first

### 次の一手
1. [T-001] lost inside archive

## 2026-08-02 (2) — archive second

### 次の一手
1. [T-002] carried to current
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", archive_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(archive_name),
        )
        _assert_violation(root, archive_name, "次の一手 ID [T-001]", "archive second")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_id_bearing_archive_entry_requires_ids_on_all_items():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-08-03 (3) — current

### 次の一手
1. [T-003] current
"""
        archive_name = "worklog-synthetic.md"
        archive = """# archive

## 2026-08-01 (1) — archive first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — archive second

- [T-001] consumed

### 次の一手
1. missing ID
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", archive_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(archive_name),
        )
        _assert_violation(
            root,
            archive_name,
            "エントリ '2026-08-02 (2) — archive second'",
            "項目先頭に有効な [T-NNN] ID がない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_boundaries_between_all_archives():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-08-03 (3) — current

- [T-002] consumed

### 次の一手
1. [T-003] current
"""
        first_name = "worklog-first.md"
        second_name = "worklog-second.md"
        first = """# first archive

## 2026-08-01 (1) — first archive last

### 次の一手
1. [T-001] lost between archives
"""
        second = """# second archive

## 2026-08-02 (2) — second archive first

### 次の一手
1. [T-002] carried to current
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", first_name), first)
        _write(root, os.path.join("docs", "archive", second_name), second)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(first_name, second_name),
        )
        _assert_violation(root, first_name, "次の一手 ID [T-001]", "second archive first")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_latest_archive_is_selected_by_entry_date():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-09-02 (2) — current

### 次の一手
1. [T-002] current
"""
        older_name = "worklog-zz-older.md"
        newer_name = "worklog-aa-newer.md"
        older = """# older

## 2025-12-31 (1) — older

### 次の一手
1. legacy item
"""
        newer = """# newer

## 2026-09-01 (1) — newer

### 次の一手
1. [T-001] lost from chronologically latest archive
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", older_name), older)
        _write(root, os.path.join("docs", "archive", newer_name), newer)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(older_name, newer_name),
        )
        res = _assert_violation(root, newer_name, "次の一手 ID [T-001]")
        assert older_name not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_same_day_archives_use_entry_ordinal_not_filename():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-09-02 (3) — current

- [T-002] consumed

### 次の一手
1. [T-003] current
"""
        early_name = "worklog-z-early.md"
        late_name = "worklog-a-late.md"
        early = """# early

## 2026-09-01 (1) — early

### 次の一手
1. [T-001] carry across archive boundary
"""
        late = """# late

## 2026-09-01 (2) — late

- [T-001] consumed

### 次の一手
1. [T-002] carry to current
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", early_name), early)
        _write(root, os.path.join("docs", "archive", late_name), late)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(late_name, early_name),
        )
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ambiguous_same_day_archive_order_is_violation():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-09-02 (2) — current

- [T-001] consumed

### 次の一手
1. [T-002] current
"""
        first_name = "worklog-a.md"
        second_name = "worklog-z.md"
        archive = """# archive

## 2026-09-01 (1) — same ordinal

### 次の一手
1. [T-001] carry
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", first_name), archive)
        _write(root, os.path.join("docs", "archive", second_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(first_name, second_name),
        )
        _assert_violation(
            root,
            "archive worklog の順序を一意に決定できない",
            first_name,
            second_name,
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_latest_archive_structure_is_fail_closed():
    fixtures = {
        "zero entries": ("# archive\n", "日付付き worklog entry が 0 件"),
        "invalid H2": (
            "# archive\n\n## 9999-12-31 malformed entry\n",
            "entry title に full-match しない",
        ),
        "zero next": (
            "# archive\n\n## 2026-08-01 (1) — last\n\n本文。\n",
            "`### 次の一手` が 0 件",
        ),
        "multiple next": (
            "# archive\n\n## 2026-08-01 (1) — last\n\n"
            "### 次の一手\n1. [T-001] first\n\n"
            "### 次の一手 (duplicate)\n1. [T-002] second\n",
            "`### 次の一手` が 2 件",
        ),
    }
    for name, (archive, expected) in fixtures.items():
        root = _build_min_repo()
        try:
            archive_name = "worklog-synthetic-latest.md"
            _write(root, os.path.join("docs", "archive", archive_name), archive)
            _write(
                root,
                os.path.join("docs", "archive", "README.md"),
                _archive_readme(archive_name),
            )
            _assert_violation(root, archive_name, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_real_repo_clean():
    res = subprocess.run(
        [sys.executable, os.path.join(_REPO, "tools", "check_docs.py")],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"実 repo で違反が出た:\n{res.stdout}\n{res.stderr}"
    assert "違反なし" in res.stdout, res.stdout
    assert _admission_findings(res) == []


# ===== handoff 48h stale + schema 検査 (S2, dev-wave 段5 U2, 段4裁定 B4) =====
# 48h stale 判定と handoff schema (4 行ヘッダ書式・状態語彙・基準コミット形) は所有者を
# 判別できないため非阻害の warning とする (rc に算入しない)。「状態:」行の欠落だけは
# 自己修復可能な finding のまま残す (択一 4)。既存被覆はゼロだったため以下は全て純増。


def _well_formed_handoff_text(
    *,
    state: str = "作業中",
    base: str | None = None,
    purpose: str = "テスト目的",
    updated: str = "2026-08-01",
) -> str:
    """4 行ヘッダ契約 (# タイトル + 直後 4 行。書式検査は check_docs.py の非阻害 warning が唯一の経路) を満たす最小 handoff。"""
    if base is None:
        base = "a" * 40
    return (
        "# synthetic handoff\n"
        f"- 目的: {purpose}\n"
        f"- 状態: {state}\n"
        f"- 最終更新: {updated}\n"
        f"- 基準コミット: {base}\n"
        "\n"
        "## 本文\n"
        "trivial body\n"
    )


def _write_handoff(
    root: str, name: str, text: str, *, age_hours: float | None = None
) -> str:
    rel = os.path.join("docs", "handoff", name)
    _write(root, rel, text)
    path = os.path.join(root, rel)
    if age_hours is not None:
        ts = time.time() - age_hours * 3600
        os.utime(path, (ts, ts))
    return path


def _assert_warning_not_finding(root: str, *needles: str) -> subprocess.CompletedProcess:
    res = _run_check(root)
    assert res.returncode == 0, f"警告のはずが rc!=0 になった:\n{res.stdout}\n{res.stderr}"
    assert "違反なし" in res.stdout, f"warning のはずが finding 扱いになった:\n{res.stdout}"
    for needle in needles:
        assert needle in res.stdout, f"{needle!r} が警告出力にない:\n{res.stdout}"
    return res


def _assert_no_warnings(root: str) -> subprocess.CompletedProcess:
    res = _run_check(root)
    assert res.returncode == 0, f"rc!=0:\n{res.stdout}\n{res.stderr}"
    assert "違反なし" in res.stdout, res.stdout
    assert "件の警告" not in res.stdout, f"警告が出てはいけないのに出た:\n{res.stdout}"
    return res


def test_stale_active_handoff_does_not_make_check_docs_red():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-stale.md",
            _well_formed_handoff_text(state="作業中"),
            age_hours=49,
        )
        _assert_warning_not_finding(
            root,
            "2026-07-01-stale.md",
            "状態が稼働中のまま 48h 以上未更新",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_fresh_active_handoff_emits_no_stale_warning():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-fresh.md",
            _well_formed_handoff_text(state="作業中"),
            age_hours=47,
        )
        res = _assert_no_warnings(root)
        assert "48h" not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_handoff_without_status_header_is_still_a_finding():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-nostatus.md",
            "# broken handoff\n\nno header fields at all.\n",
        )
        _assert_violation(root, "ヘッダ定型 (状態:) がない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_unknown_state_value_is_a_warning_not_a_finding():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-unknownstate.md",
            _well_formed_handoff_text(state="完了"),
        )
        _assert_warning_not_finding(
            root,
            "既知の 3 値 (作業中/計測中/中断) のいずれでもない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_malformed_four_line_header_is_a_warning_not_a_finding():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-malformed.md",
            "# malformed header handoff\n"
            "\n"
            "- 状態: 作業中\n"
            "- 最終更新: 2026-08-01\n"
            "- 基準コミット: " + "a" * 40 + "\n",
        )
        _assert_warning_not_finding(
            root,
            "4 行ヘッダ",
            "書式が",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_short_base_commit_is_a_warning_not_a_finding():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-shortsha.md",
            _well_formed_handoff_text(base="abc1234"),
        )
        _assert_warning_not_finding(
            root,
            "40 桁または 64 桁の hex ではない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_repo_with_only_a_well_formed_handoff_has_zero_warnings():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-wellformed.md",
            _well_formed_handoff_text(),
        )
        _assert_no_warnings(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        if fn is test_command_docs_guard_positive_controls:
            calls = [(case, (case,)) for case in _COMMAND_GUARD_CASES]
        else:
            calls = [(fn.__name__, ())]
        for label, args in calls:
            display = (
                f"{fn.__name__}[{label}]"
                if args else fn.__name__
            )
            try:
                fn(*args)
                print(f"PASS {display}")
                passed += 1
            except AssertionError as e:
                print(f"FAIL {display}: {e}")
                failed += 1
            except Exception as e:  # noqa: BLE001
                print(f"ERROR {display}: {type(e).__name__}: {e}")
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
