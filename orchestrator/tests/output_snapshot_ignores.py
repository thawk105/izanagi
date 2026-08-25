# -*- coding: utf-8 -*-
"""実 repository の ``output/`` snapshot に共通する Git ignore 規則。"""
from __future__ import annotations

import subprocess
from pathlib import Path


def git_ignored_output_prefixes(repo_root: Path) -> tuple[str, ...]:
    """Git が ignore する ``output/`` 配下の path を相対 prefix で返す。"""
    command = (
        "git", "ls-files", "-o", "-i", "--exclude-standard", "--directory",
        "--", "output/",
    )
    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "")
        raise AssertionError(
            "output/ の Git ignore 集合を取得できない: "
            f"{str(detail).strip() or str(exc)}"
        ) from exc

    prefixes: set[str] = set()
    for line in completed.stdout.splitlines():
        normalized = line.rstrip("/")
        if normalized == "output":
            raise AssertionError(
                "output/ 全体が Git ignore 対象のため snapshot 検査を実行できない"
            )
        elif normalized.startswith("output/"):
            prefixes.add(normalized.removeprefix("output/"))
        else:
            raise AssertionError(
                f"git ls-files が output/ 外の path を返した: {line!r}"
            )
    return tuple(sorted(prefixes))


def is_git_ignored_output_path(
        relative: str, ignored_prefixes: tuple[str, ...]) -> bool:
    """相対 path 自身またはその祖先 directory が ignore 対象かを返す。"""
    return any(
        relative == prefix
        or relative.startswith(f"{prefix}/")
        for prefix in ignored_prefixes
    )
