#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H3 hook: Edit/Write の書き込み時点防壁 — 方針 A の最小第二防壁 (規律2, phase3.md タスク3)。

PreToolUse (Write|Edit|MultiEdit|NotebookEdit) で発火し、対象パスが管轄内なら
書き込み**前**に検査して exit 2 (拒否, stderr が Claude に返る) / exit 0 (許可)。

管轄 = **明白な直接書き込みの拒否、この 3 本だけ** (方針 A, D30/D33。これ以外のパスは
即許可 — 通常の開発作業を妨げない):
1. **成果物の proof chain (規律2):** official / exploration campaign の `runs/`
   (WAL)・`campaign.lock` と `build-variants/` への Edit/Write を拒否する。また、
   exploration namespace marker への直接書き込みも拒否する。COMMIT/fitness を書く
   唯一の経路は pipeline.evaluate() (phase3.md)。verifier を迂回した成果物更新を塞ぐ。
2. **designated ソース外への Write (D23/D24):** `external/ccbench/` 内は EVOLVE-BLOCK
   ソース (source_digest.EVOLVE_BLOCK_SOURCES) だけ書き込み可。`Options.cmake` 等は
   人間 template 専有 — template 改訂は patches/ + git apply (Bash) 経由で行う。
3. **hook 実行面:** `hooks/` subtree 自身への直接変更を拒否する。文書更新用の exact
   `hooks/README.md` だけは、現物が regular non-symlink かつ単一 link の場合に許可する。

**旧設計 (payload/skeleton のテキスト検査) は方針 A で削除した (D33):** #ifdef・build 時
マクロ・TRACE 混入の保証は、テキスト検査の完全性 (GW2R-1 の backslash-newline splice が
原理的限界を実証) ではなく一次防壁が担う — identity は source_digest の preprocess 後
ハッシュ + #include 行 HEAD 固定 + build 出口の TOCTOU 再照合、観測者効果 (規律1) は
diff-of-diffs (source_digest.assert_trace_diff_matches_head、build 出口で発火)。
designated ソース内の書き込み内容はここでは検査しない — 何を書いても identity が正直に
変わり (偽 cache hit しない)、TRACE 条件付き挙動差は build 出口で fails-closed になる。
意味的な逸脱 (骨格破壊・領域外編集) の判定は auditor / 人間レビュー領域。

これは第二防壁であり sandbox ではない。Bash 経由の書き込みは guard_bash.py が、
identity 整合は source_digest (fails-closed) が担う。
"""
from __future__ import annotations

import json
import os
import stat
import sys

# source_digest.EVOLVE_BLOCK_SOURCES の写し (hook は単体で動く必要があるため import
# しない)。ドリフトは orchestrator/tests/test_hooks.py が両者の一致を assert して防ぐ。
EVOLVE_BLOCK_SOURCES = (
    "include/backoff.hh", "cc/silo/transaction.cc", "cc/mocc/transaction.cc")


def _repo_root() -> str:
    # hooks/guard_write.py = <repo>/hooks/guard_write.py
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _protected_artifact(rp: str, camp_roots: tuple[str, ...]) -> str:
    """proof-chain 成果物なら理由ラベル、そうでなければ空文字。

    camp_roots は official / exploration の閉じた二要素集合。rp と各 root は同じ
    resolution mode に揃えるため、realpath 判定でも lexical entry 判定でも片側だけが
    symlink 解決されて照合を外すことがない。"""
    for camp_root in camp_roots:
        camp = camp_root + os.sep
        if rp.startswith(camp):
            parts = rp[len(camp):].split(os.sep)
            if len(parts) >= 2 and parts[1] == "runs":
                return "WAL (campaigns/*/runs/)"
            if len(parts) == 2 and parts[1] == "campaign.lock":
                return "campaign.lock (identity の正準 pre-image)"
    # campaign root に依存しない leaf 条件は root loop の外に一度だけ置く。
    if os.sep + "build-variants" + os.sep in rp or rp.endswith(
            os.sep + "build-variants"):
        return "build-variants (ビルドキャッシュ)"
    return ""


def _inside(path: str, tree: str) -> bool:
    return path == tree or path.startswith(tree + os.sep)


class _HooksInodeIndex:
    """1 回の decide 内で共有する hooks regular-file inode 集合。

    target 自体が存在しない場合は hardlink alias ではない。hooks subtree の列挙または
    entry stat が一部でも失敗した場合だけは「一致なし」と区別し、既存 regular target を
    局所的に拒否する。
    """

    def __init__(self, hooks_root: str):
        self.hooks_root = hooks_root
        self._loaded = False
        self._identities = set()
        self._scan_failed = False

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True

        try:
            os.stat(self.hooks_root)
        except FileNotFoundError:
            # hooks/ 自体が無い repo には共有 inode も無い。走査失敗ではない。
            return
        except OSError:
            # root が存在するか確認不能なら、列挙不能と同じく局所 deny。
            self._scan_failed = True
            return

        def record_error(_error) -> None:
            self._scan_failed = True

        try:
            for directory, _, filenames in os.walk(
                    self.hooks_root, followlinks=False, onerror=record_error):
                for filename in filenames:
                    try:
                        candidate = os.stat(os.path.join(directory, filename))
                    except OSError:
                        self._scan_failed = True
                        continue
                    if stat.S_ISREG(candidate.st_mode):
                        self._identities.add((candidate.st_dev, candidate.st_ino))
        except OSError:
            self._scan_failed = True

    def protects(self, path: str) -> bool:
        try:
            target = os.stat(path)
        except OSError:
            return False
        if not stat.S_ISREG(target.st_mode):
            return False
        self._load()
        return (self._scan_failed
                or (target.st_dev, target.st_ino) in self._identities)


def _readme_exception_allowed(
    raw_path: str,
    lexical_path: str,
    canonical_path: str,
    root: str,
) -> bool:
    """exact README が regular・非 symlink・単一 link なら例外許可する。"""
    lexical_readme = os.path.abspath(os.path.join(root, "hooks", "README.md"))
    canonical_readme = os.path.realpath(os.path.join(root, "hooks", "README.md"))
    if lexical_path != lexical_readme or canonical_path != canonical_readme:
        return False
    try:
        metadata = os.lstat(raw_path)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return (stat.S_ISREG(metadata.st_mode)
            and not stat.S_ISLNK(metadata.st_mode)
            and metadata.st_nlink == 1)


def _protected_hooks(
    raw_path: str,
    lexical_path: str,
    canonical_path: str,
    root: str,
    hooks_index: _HooksInodeIndex,
) -> bool:
    """hooks subtree、その file alias、または走査不能な既存 target なら True。"""
    lexical_root = os.path.abspath(os.path.join(root, "hooks"))
    canonical_root = os.path.realpath(os.path.join(root, "hooks"))
    if _readme_exception_allowed(
            raw_path, lexical_path, canonical_path, root):
        return False
    if (_inside(lexical_path, lexical_root)
            or _inside(canonical_path, canonical_root)):
        return True
    return hooks_index.protects(raw_path)


def _string_values(value):
    """JSON decode 済み payload の string value を再帰走査する。"""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _string_values(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from _string_values(nested)


_APPLY_PATCH_DIRECTIVES = (
    ("add", "*** Add File: "),
    ("update", "*** Update File: "),
    ("delete", "*** Delete File: "),
    ("move_to", "*** Move to: "),
)


def parse_apply_patch(command: str) -> list[tuple[str, str]]:
    """Codex apply_patch の exact directive を最後まで抽出する。

    block の妥当性は許可根拠にしない。壊れた block や orphan Move to があっても
    後続を含む全行を走査し、見つかった候補は拒否を増やすためだけに使う。
    """
    operations = []
    for line in command.splitlines():
        for kind, prefix in _APPLY_PATCH_DIRECTIVES:
            if line.startswith(prefix):
                operations.append((kind, line[len(prefix):]))
                break
    return operations


def _canonical_path(path: str, lexical_path: str, resolve_final: bool) -> str:
    if resolve_final:
        return os.path.realpath(path)
    return os.path.join(
        os.path.realpath(os.path.dirname(path)), os.path.basename(lexical_path))


def classify_path(
    abs_path: str,
    root: str,
    *,
    resolve_final: bool = True,
    hooks_index=None,
) -> tuple[bool, str]:
    """path を hooks と既存 artifact / namespace / freeze / ccbench 核で判定する。

    legacy canonical = ``realpath(abspath(raw))`` と raw canonical =
    ``realpath(raw)`` を両方保持し、既存 4 判定は deny union にする。hooks 判定は
    lexical + raw canonical を使う。``resolve_final=False`` は Delete / Move 元の
    directory entry 用で、両 canonical とも最終要素そのものは解決しない。
    """
    root = os.path.realpath(root)
    lexical_path = os.path.abspath(abs_path)
    legacy_canonical = _canonical_path(
        lexical_path, lexical_path, resolve_final)
    raw_canonical = _canonical_path(abs_path, lexical_path, resolve_final)
    canonical_paths = tuple(dict.fromkeys((legacy_canonical, raw_canonical)))

    index = hooks_index or _HooksInodeIndex(
        os.path.realpath(os.path.join(root, "hooks")))
    if _protected_hooks(
            abs_path, lexical_path, raw_canonical, root, index):
        return False, (
            "hooks/ subtree への直接書き込みは拒否。exact hooks/README.md は regular "
            "non-symlink かつ st_nlink == 1 の場合だけ Write 系ツールで更新可能")

    camp_roots = (
        os.path.realpath(os.path.join(root, "output", "campaigns")),
        os.path.realpath(os.path.join(root, "output", "exploration", "campaigns")),
    )
    for canonical in canonical_paths:
        label = _protected_artifact(canonical, camp_roots)
        if label:
            return False, (
                f"{label} への直接書き込みは拒否 (規律2)。COMMIT/fitness を書く唯一の"
                "経路は pipeline.evaluate()。verifier を迂回した成果物の更新は不可")

    exploration_root = os.path.realpath(
        os.path.join(root, "output", "exploration"))
    lexical_exploration_root = os.path.abspath(
        os.path.join(root, "output", "exploration"))
    if (os.path.basename(lexical_path) == "namespace.json"
            and (lexical_path.startswith(lexical_exploration_root + os.sep)
                 or any(_inside(canonical, exploration_root)
                        for canonical in canonical_paths))):
        return False, (
            "output/exploration/ 配下の namespace.json への直接書き込みは"
            "拒否。exploration 成果物を official と誤受理させないための "
            "namespace marker は変更不可")

    # s8b-freeze namespace (承認 record / active pointer / revocation / 世代 file) への
    # 直接 Write/Edit を拒否する (F6a、C1-11)。これは誤操作抑止であって認証防壁ではない。
    freeze_root = os.path.realpath(os.path.join(root, "output", "s8b-freeze"))
    if any(_inside(canonical, freeze_root) for canonical in canonical_paths):
        return False, (
            "output/s8b-freeze/ 配下への直接書き込みは拒否 (F6a 誤操作抑止)。approval/"
            "active pointer/revocation/世代 file の発効は人間 commit + s8b_ratified_freeze "
            "検証を経る (これは認証防壁ではなく誤操作抑止)")

    sub = os.path.realpath(os.path.join(root, "external", "ccbench"))
    for canonical in canonical_paths:
        if _inside(canonical, sub):
            rel = os.path.relpath(canonical, sub)
            if rel not in EVOLVE_BLOCK_SOURCES:
                return False, (
                    f"external/ccbench の編集面は EVOLVE-BLOCK ソース "
                    f"{EVOLVE_BLOCK_SOURCES} のみ ({rel} は不可)。Options.cmake 等は人間 "
                    "template 専有 — template 改訂は patches/ + git apply で (F1/D24)")
    # designated ソース内は内容非検査。どちらの canonical にも拒否が無ければ許可する。
    return True, ""


def _decide_apply_patch(
    tool_input: dict,
    root: str,
    cwd: str,
    hooks_index: _HooksInodeIndex,
) -> tuple[bool, str]:
    operations = parse_apply_patch(tool_input.get("command") or "")
    cwd_valid = bool(cwd) and os.path.isabs(cwd) and os.path.isdir(cwd)
    denials = []

    for index, (kind, raw_path) in enumerate(operations):
        if not os.path.isabs(raw_path) and not cwd_valid:
            denials.append(
                f"{raw_path!r}: 相対 path の基準となる payload cwd が空・非絶対・不在")
            continue

        candidate_path = (
            raw_path if os.path.isabs(raw_path) else os.path.join(cwd, raw_path))
        reasons = []
        allow, reason = classify_path(
            candidate_path, root, hooks_index=hooks_index)
        if not allow:
            reasons.append(reason)

        is_move_source = (
            kind == "update"
            and index + 1 < len(operations)
            and operations[index + 1][0] == "move_to"
        )
        if kind == "delete" or is_move_source:
            lexical_allow, lexical_reason = classify_path(
                candidate_path, root, resolve_final=False,
                hooks_index=hooks_index)
            if not lexical_allow and lexical_reason not in reasons:
                reasons.append(lexical_reason)

        if reasons:
            denials.append(f"{raw_path!r}: {' / '.join(reasons)}")

    if denials:
        return False, "apply_patch の拒否対象: " + "; ".join(denials)
    return True, ""


def decide(
    tool_name: str,
    tool_input: dict,
    repo_root: str = "",
    cwd: str = "",
) -> tuple:
    """(allow: bool, reason: str)。reason は拒否時のみ。"""
    root = os.path.realpath(repo_root or _repo_root())
    hooks_index = _HooksInodeIndex(
        os.path.realpath(os.path.join(root, "hooks")))
    if tool_name == "apply_patch":
        return _decide_apply_patch(tool_input, root, cwd, hooks_index)

    # NotebookEdit の実書込先は notebook_path。file_path decoy より優先する。
    if tool_name == "NotebookEdit":
        path = tool_input.get("notebook_path") or tool_input.get("file_path") or ""
    else:
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not path:
        return True, ""
    candidate_path = path if os.path.isabs(path) else os.path.join(root, path)
    allow, reason = classify_path(
        candidate_path, root, hooks_index=hooks_index)
    if tool_name == "NotebookEdit":
        lexical_path = os.path.abspath(candidate_path)
        canonical_paths = (
            os.path.realpath(lexical_path), os.path.realpath(candidate_path))
        sub = os.path.realpath(os.path.join(root, "external", "ccbench"))
        if any(_inside(canonical, sub) for canonical in canonical_paths):
            return False, "external/ccbench への NotebookEdit は編集面外 (D24)"
    return allow, reason


def main() -> int:
    raw = sys.stdin.read()
    tool_name = ""
    payload = None
    try:
        payload = json.loads(raw)
        tool_name = payload.get("tool_name", "")
        tool_input = payload.get("tool_input") or {}
        allow, reason = decide(
            tool_name, tool_input, cwd=payload.get("cwd") or "")
    except Exception as exc:  # noqa: BLE001 — 管轄 token が無ければ可用性優先。
        protected_tokens = (
            "external/ccbench", "wal.jsonl", "campaign.lock",
            "build-variants", "output/s8b-freeze",
            "output/exploration/", "namespace.json",
        )
        if tool_name == "apply_patch":
            protected_tokens += ("output/campaigns/", "/runs/", "runs/")
        decoded_values = tuple(_string_values(payload)) if payload is not None else ()
        raw_protected = any(token in raw for token in protected_tokens)
        decoded_protected = any(
            any(token in value for token in protected_tokens)
            for value in decoded_values)
        hooks_protected = (
            "hooks/" in raw or '"hooks"' in raw
            or any(value == "hooks" or "hooks/" in value
                   for value in decoded_values))
        if raw_protected or decoded_protected or hooks_protected:
            print(
                f"guard_write hook 内部エラー ({type(exc).__name__}: {exc}) — 管轄パスを"
                "含むため fails-closed で拒否", file=sys.stderr)
            return 2
        return 0
    if not allow:
        print(f"[guard_write] 拒否: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
