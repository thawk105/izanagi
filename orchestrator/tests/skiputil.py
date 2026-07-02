# -*- coding: utf-8 -*-
"""依存物不在時の skip を pytest でも素の runner でも「skip」として可視化する。

print + return の疑似スキップは対象未検証でも PASS に数えられ、カバレッジ蒸発
(fresh clone で load-bearing テストが空虚に緑) を隠す (audit §3)。pytest 配下
(PYTEST_CURRENT_TEST) では pytest.skip、素の runner では Skip 例外を投げ、
各テストファイルの _run() が SKIP として数える。
"""
from __future__ import annotations

import os


class Skip(Exception):
    """素の runner 用 skip 例外。_run() が捕まえて SKIP として数える。"""


def skip(reason: str) -> None:
    if os.environ.get("PYTEST_CURRENT_TEST"):
        import pytest
        pytest.skip(reason)
    raise Skip(reason)
