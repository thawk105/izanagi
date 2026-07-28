#!/usr/bin/env python3
"""AI 作業 provenance の commit trailer を決定的に監査する。

既定では docs/ai-provenance.md を最初に追加した commit から HEAD までを検査する。
任意範囲は --range、commit 前の message は --message-file で検査できる。
hook には配線しない。Izanagi の hook 2 本限定を維持しつつ、欠落を明示的に監査するための
独立した lint である。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
POLICY_PATH = "docs/ai-provenance.md"
ROLES = ("author", "reviewer", "researcher", "manager", "integrator")
IDENT = r"[a-z0-9][a-z0-9._-]*"
RESERVED_PRODUCTS = {"none", "unknown", "not-exposed", "human"}
IMPLEMENTATION_POLICY_NEEDLE = (
    "実装面を変更する AI 関与 commit は Codex author を必須"
)
IMPLEMENTATION_PREFIXES = (
    "orchestrator/", "tools/", "hooks/", ".github/", ".codex/", "external/",
)
IMPLEMENTATION_SUFFIXES = (
    ".py", ".sh", ".bash", ".c", ".cc", ".cpp", ".cxx",
    ".h", ".hh", ".hpp", ".hxx", ".cmake", ".patch", ".diff",
)
IMPLEMENTATION_BASENAMES = {
    "CMakeLists.txt", "Makefile", "GNUmakefile", "pyproject.toml",
}
AGENT_VALUE = re.compile(
    rf"^product=(?P<product>{IDENT}); "
    rf"model=(?P<model>{IDENT}); "
    rf"reasoning=(?P<reasoning>{IDENT}); "
    rf"role=(?P<role>{'|'.join(ROLES)})"
    rf"(?:; scope=(?P<scope>{IDENT}))?$"
)


def _git(*args: str, input_text: str | None = None) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout


def _ai_agent_values(message: str) -> list[str]:
    """Git 自身が trailer と認識した AI-Agent の値だけを返す。"""
    parsed = _git("interpret-trailers", "--parse", input_text=message)
    values: list[str] = []
    for line in parsed.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip().lower() == "ai-agent":
            values.append(value.strip())
    return values


def validate_message(label: str, message: str) -> tuple[list[str], list[str]]:
    """(findings, scope_findings) を返す。

    scope_findings は「同じ role が複数行あるのに scope がない」違反。scope 規則の
    導入 commit より前の履歴には遡及しないため、呼び出し側が適用可否を判定する。
    """
    values = _ai_agent_values(message)
    if not values:
        return [f"{label}: AI-Agent trailer がない"], []

    if "none" in values:
        if values != ["none"]:
            return [f"{label}: AI-Agent: none は唯一の AI-Agent trailer でなければならない"], []
        return [], []

    findings: list[str] = []
    seen: set[str] = set()
    by_role: dict[str, list[tuple[str, bool]]] = {}
    for value in values:
        if value in seen:
            findings.append(f"{label}: 同一 AI-Agent trailer の重複: {value}")
            continue
        seen.add(value)
        match = AGENT_VALUE.fullmatch(value)
        if not match:
            findings.append(
                f"{label}: AI-Agent の形式違反: {value!r} — "
                "product/model/reasoning/role (任意で scope) の順と許可値を確認する"
            )
            continue
        by_role.setdefault(match.group("role"), []).append(
            (value, match.group("scope") is not None)
        )
        if match.group("product") in RESERVED_PRODUCTS:
            findings.append(
                f"{label}: product={match.group('product')} は AI 製品識別子として使えない"
            )
        if match.group("model") == "none" or match.group("reasoning") == "none":
            findings.append(
                f"{label}: model/reasoning に none は使えない — "
                "not-exposed または unknown を使う"
            )

    scope_findings: list[str] = []
    for role, entries in by_role.items():
        if len(entries) < 2:
            continue
        for value, has_scope in entries:
            if not has_scope:
                scope_findings.append(
                    f"{label}: role={role} が複数行あるのに scope がない: {value}"
                )
    return findings, scope_findings


def _scope_policy_commit() -> str | None:
    """scope 規則を docs/ai-provenance.md へ導入した commit を内容検出する (SHA 非依存)。"""
    commits = _git(
        "log", "--reverse", "--format=%H", "-S", "scope=", "--", POLICY_PATH
    ).splitlines()
    return commits[0] if commits else None


def _implementation_policy_commit() -> str | None:
    """Codex author 契約を導入した commit を内容検出する。"""
    commits = _git(
        "log", "--reverse", "--format=%H", "-S", IMPLEMENTATION_POLICY_NEEDLE,
        "--", POLICY_PATH,
    ).splitlines()
    return commits[0] if commits else None


def _is_descendant(ancestor: str, commit: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, commit],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def _is_implementation_path(path: str) -> bool:
    """Git 相対 path が実装面なら True。所在・拡張子の契約を一か所で判定する。"""
    normalized = path.removeprefix("./")
    basename = normalized.rsplit("/", 1)[-1]
    if basename in IMPLEMENTATION_BASENAMES:
        return True
    if normalized.endswith(IMPLEMENTATION_SUFFIXES):
        return True
    if normalized.startswith("patches/"):
        return False
    return (
        normalized.startswith(IMPLEMENTATION_PREFIXES)
        and not normalized.endswith((".md", ".rst"))
    )


def validate_implementation_author(
    label: str, message: str, paths: list[str],
) -> list[str]:
    """AI 関与の実装面 commit に Codex author がいることを検査する。"""
    implementation = sorted(path for path in paths if _is_implementation_path(path))
    if not implementation:
        return []
    values = _ai_agent_values(message)
    if not values or values == ["none"]:
        return []
    for value in values:
        match = AGENT_VALUE.fullmatch(value)
        if (
            match is not None
            and match.group("product") == "codex"
            and match.group("role") == "author"
        ):
            return []
    sample = ", ".join(implementation[:3])
    if len(implementation) > 3:
        sample += f", ... ({len(implementation)} paths)"
    return [
        f"{label}: 実装面に Codex role=author がない — paths={sample}"
    ]


def _commit_paths(commit: str) -> list[str]:
    raw = _git(
        "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-z", commit,
    )
    return [path for path in raw.split("\0") if path]


def _staged_paths() -> list[str]:
    raw = _git(
        "diff", "--cached", "--name-only", "--diff-filter=ACMRDTUXB", "-z",
    )
    return [path for path in raw.split("\0") if path]


def _policy_commit() -> str:
    commits = _git(
        "log", "--diff-filter=A", "--format=%H", "--", POLICY_PATH
    ).splitlines()
    if not commits:
        raise RuntimeError(
            f"{POLICY_PATH} の導入 commit が履歴にない。"
            "commit 前は --message-file で検査すること"
        )
    return commits[-1]


def _commit_range(rev_range: str | None) -> list[str]:
    if rev_range is None:
        policy = _policy_commit()
        descendants = _git(
            "rev-list", "--reverse", "--ancestry-path", f"{policy}..HEAD"
        ).splitlines()
        return [policy, *descendants]
    return _git("rev-list", "--reverse", rev_range).splitlines()


def _read_message(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--range", dest="rev_range", help="検査する git revision range")
    group.add_argument(
        "--message-file",
        help="commit 前の message ファイルを検査する。標準入力は -",
    )
    args = parser.parse_args()

    try:
        if args.message_file is not None:
            message = _read_message(args.message_file)
            base, scoped = validate_message(
                args.message_file, message
            )
            implementation = validate_implementation_author(
                args.message_file, message, _staged_paths(),
            )
            findings = [*base, *scoped, *implementation]
            checked = 1
        else:
            commits = _commit_range(args.rev_range)
            scope_epoch = _scope_policy_commit()
            implementation_epoch = _implementation_policy_commit()
            findings = []
            for commit in commits:
                subject = _git("show", "-s", "--format=%s", commit).strip()
                message = _git("show", "-s", "--format=%B", commit)
                label = f"{commit[:12]} {subject}"
                base, scoped = validate_message(label, message)
                findings.extend(base)
                if scoped and scope_epoch is not None and _is_descendant(scope_epoch, commit):
                    findings.extend(scoped)
                if (
                    implementation_epoch is not None
                    and _is_descendant(implementation_epoch, commit)
                ):
                    findings.extend(validate_implementation_author(
                        label, message, _commit_paths(commit),
                    ))
            checked = len(commits)
    except (OSError, RuntimeError, UnicodeError) as exc:
        print(f"check_ai_provenance: 実行不能: {exc}", file=sys.stderr)
        return 2

    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        print(
            f"check_ai_provenance: {checked} 件中 {len(findings)} 違反",
            file=sys.stderr,
        )
        return 1

    print(f"check_ai_provenance: {checked} 件、違反なし")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
