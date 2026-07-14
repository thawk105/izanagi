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
AGENT_VALUE = re.compile(
    rf"^product=(?P<product>{IDENT}); "
    rf"model=(?P<model>{IDENT}); "
    rf"reasoning=(?P<reasoning>{IDENT}); "
    rf"role=(?P<role>{'|'.join(ROLES)})$"
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


def validate_message(label: str, message: str) -> list[str]:
    values = _ai_agent_values(message)
    if not values:
        return [f"{label}: AI-Agent trailer がない"]

    if "none" in values:
        if values != ["none"]:
            return [f"{label}: AI-Agent: none は唯一の AI-Agent trailer でなければならない"]
        return []

    findings: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            findings.append(f"{label}: 同一 AI-Agent trailer の重複: {value}")
            continue
        seen.add(value)
        match = AGENT_VALUE.fullmatch(value)
        if not match:
            findings.append(
                f"{label}: AI-Agent の形式違反: {value!r} — "
                "product/model/reasoning/role の順と許可値を確認する"
            )
            continue
        if match.group("product") in RESERVED_PRODUCTS:
            findings.append(
                f"{label}: product={match.group('product')} は AI 製品識別子として使えない"
            )
        if match.group("model") == "none" or match.group("reasoning") == "none":
            findings.append(
                f"{label}: model/reasoning に none は使えない — "
                "not-exposed または unknown を使う"
            )
    return findings


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
            findings = validate_message(args.message_file, _read_message(args.message_file))
            checked = 1
        else:
            commits = _commit_range(args.rev_range)
            findings = []
            for commit in commits:
                subject = _git("show", "-s", "--format=%s", commit).strip()
                message = _git("show", "-s", "--format=%B", commit)
                findings.extend(validate_message(f"{commit[:12]} {subject}", message))
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
