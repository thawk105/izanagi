#!/usr/bin/env python3
"""orchestrator テストの推奨実行ランナー。

pytest-xdist が無ければユーザーローカル (`pip install --user`) へ自動導入してから
`-n 8` で並列実行する (並列度の根拠は worklog 2026-07-17)。導入に失敗した環境
(オフライン等) では直列で回す — テスト自体は xdist に依存しない。

使い方:
    python3 tools/run_tests.py                 # スイート全体を -n 8 で
    python3 tools/run_tests.py path/to/test_x.py  # 対象を指定 (pytest へそのまま渡す)
    python3 tools/run_tests.py -n 4            # 並列度を上書き

共有マシンでは全コアを掴む -n auto を使わない (orchestrator/tests/README.md)。
"""
from __future__ import annotations

import os
import subprocess
import sys
from importlib import metadata

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_TARGET = os.path.join(_REPO, "orchestrator", "tests")
_DEFAULT_NPROC = "8"


def _xdist_installed() -> bool:
    # find_spec("xdist") はアンインストール残骸 (空 dir = namespace package) に騙される。
    # pytest の plugin 発見と同じ実体 = dist メタデータ (entry points) の有無で判定する
    try:
        metadata.distribution("pytest-xdist")
        return True
    except metadata.PackageNotFoundError:
        return False


def _ensure_xdist() -> bool:
    if _xdist_installed():
        return True
    print("pytest-xdist 未導入 — pip install --user で自動導入します", flush=True)
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "--quiet", "pytest-xdist"],
            timeout=120,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return r.returncode == 0 and _xdist_installed()


def _is_target(token: str) -> bool:
    # オプションの値 (例: -n の「4」) を対象指定と誤認して既定ターゲットを外すと、
    # pytest が repo 全体を無指定収集してしまう。実在パスか test id だけを対象と数える
    return "::" in token or os.path.exists(token)


def main() -> int:
    args = sys.argv[1:]
    cmd = [sys.executable, "-m", "pytest"]
    if not any(_is_target(a) for a in args):
        cmd.append(_DEFAULT_TARGET)
    if _ensure_xdist():
        if "-n" not in args:
            cmd += ["-n", _DEFAULT_NPROC]
    else:
        print("pytest-xdist を導入できない環境 — 直列で実行します", flush=True)
    return subprocess.call(cmd + args)


if __name__ == "__main__":
    sys.exit(main())
