# -*- coding: utf-8 -*-
"""skip を pytest でも素の runner でも「skip」として可視化する。

print + return の疑似スキップは対象未検証でも PASS に数えられ、カバレッジ蒸発
(fresh clone で load-bearing テストが空虚に緑) を隠す (audit §3)。pytest 配下
(PYTEST_CURRENT_TEST) では pytest.skip、素の runner では Skip 例外を投げ、
各テストファイルの _run() が SKIP として数える。

依存物不在は ``skip``、repo 内の前提を受入 suite では開けない条件付き未実走は
``skip_conditional_unrun`` として別分類にする。
"""
from __future__ import annotations

import os


CONDITIONAL_UNRUN = "条件付き未実走"
_CONDITIONAL_UNRUN_POINTER = (
    "repo 内の前提で満たせるが受入 suite では窓を開けない — "
    "分類と理由は `orchestrator/tests/README.md`"
)


class Skip(Exception):
    """素の runner 用 skip 例外。_run() が捕まえて SKIP として数える。"""


def skip(reason: str) -> None:
    if os.environ.get("PYTEST_CURRENT_TEST"):
        import pytest
        pytest.skip(reason)
    raise Skip(reason)


def skip_conditional_unrun(reason: str) -> None:
    """repo 内の前提を開けない条件付き未実走として理由付き skip を送出する。"""
    skip(f"{CONDITIONAL_UNRUN}: {reason} — {_CONDITIONAL_UNRUN_POINTER}")
