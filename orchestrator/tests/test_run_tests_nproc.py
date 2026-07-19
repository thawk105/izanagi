# -*- coding: utf-8 -*-
"""tools/run_tests.py の並列度自動追従ロジックの回帰 + positive control。

`_default_nproc` は環境 (使えるコア数) に自動追従し、上限 `_NPROC_CAP` で頭打ち、
環境変数 IZANAGI_TEST_NPROC で上書きできる。恒真化 (何を渡しても同じ値) に化けて
いないことを、入力ごとに異なる期待値を pin して固定する。
pytest でも 素の `python3 orchestrator/tests/test_run_tests_nproc.py` でも走る。
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_RUNNER = _REPO / "tools" / "run_tests.py"
_spec = importlib.util.spec_from_file_location("run_tests", _RUNNER)
assert _spec and _spec.loader
RT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RT)


def _with_env(monkeypatch_value):
    if monkeypatch_value is None:
        os.environ.pop("IZANAGI_TEST_NPROC", None)
    else:
        os.environ["IZANAGI_TEST_NPROC"] = monkeypatch_value


def _restore(saved):
    if saved is None:
        os.environ.pop("IZANAGI_TEST_NPROC", None)
    else:
        os.environ["IZANAGI_TEST_NPROC"] = saved


def test_available_cpus_positive_and_affinity_bounded():
    n = RT._available_cpus()
    assert n >= 1
    # affinity 尊重: 使えるコア数は物理総数を超えない
    assert n <= (os.cpu_count() or n)


def test_default_is_available_capped():
    saved = os.environ.get("IZANAGI_TEST_NPROC")
    try:
        _with_env(None)
        assert RT._default_nproc() == max(1, min(RT._available_cpus(), RT._NPROC_CAP))
        # 上限を超えない
        assert RT._default_nproc() <= RT._NPROC_CAP
    finally:
        _restore(saved)


def test_env_max_removes_cap():
    saved = os.environ.get("IZANAGI_TEST_NPROC")
    try:
        for token in ("max", "all", "MAX"):
            _with_env(token)
            assert RT._default_nproc() == max(1, RT._available_cpus())
    finally:
        _restore(saved)


def test_env_numeric_override_wins_over_cap():
    saved = os.environ.get("IZANAGI_TEST_NPROC")
    try:
        # 上限より大きい明示値もそのまま採用 (ユーザーの明示上書きが最優先)
        _with_env(str(RT._NPROC_CAP + 9))
        assert RT._default_nproc() == RT._NPROC_CAP + 9
        _with_env("3")
        assert RT._default_nproc() == 3
    finally:
        _restore(saved)


def test_env_garbage_falls_back_to_default():
    saved = os.environ.get("IZANAGI_TEST_NPROC")
    try:
        expected = max(1, min(RT._available_cpus(), RT._NPROC_CAP))
        for token in ("", "  ", "abc", "0", "-4", "3.5"):
            _with_env(token)
            assert RT._default_nproc() == expected, token
    finally:
        _restore(saved)


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as exc:
                fails += 1
                print(f"FAIL {name}: {exc}")
    raise SystemExit(1 if fails else 0)
