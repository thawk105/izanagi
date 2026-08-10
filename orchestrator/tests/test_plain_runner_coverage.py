# -*- coding: utf-8 -*-
"""メタテスト: 全 test_*.py が『自走 harness を持つ』か『pytest 専用 allowlist に載る』か
のいずれかであることを機械強制する (独立レビュー所見 B の再発防止)。

`__main__` ブロックを持たないテストファイルは `python3 file.py` で 0 件実行・exit 0 の
偽緑になる (test_s1_known_axes_freeze で顕在化、audit 2026-06-30 §3 と同型)。新規ファイルが
無自覚にこの状態へ落ちるのを検出する。allowlist の正本は orchestrator/tests/README.md の
`PYTEST_ONLY_ALLOWLIST_{START,END}` マーカー間 (docs 二重管理を避ける)。
"""
from __future__ import annotations

import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from skiputil import Skip  # noqa: E402  (二重 runner 契約: _run が捕捉する)

_README = os.path.join(_HERE, "README.md")
_SELF = "test_plain_runner_coverage.py"

# __main__ ブロック内でテストを実際に走らせる signal。空 `__main__: pass` の偽緑を弾く。
_HARNESS_SIGNALS = ("_run(", "pytest.main", "_pytest.main",
                    'startswith("test_")', "startswith('test_')")


def _read(name: str) -> str:
    with open(os.path.join(_HERE, name), encoding="utf-8") as f:
        return f.read()


def _self_runnable(src: str) -> bool:
    """`python3 file.py` で実際にテストが走る harness を持つか。`__main__` があり、その本体が
    テスト実行 signal を含むときだけ True (`__main__: pass` の空 harness は False)。"""
    if "__main__" not in src:
        return False
    tail = src.split("__main__", 1)[1]
    return any(sig in tail for sig in _HARNESS_SIGNALS)


def _test_files() -> list[str]:
    return sorted(n for n in os.listdir(_HERE)
                  if n.startswith("test_") and n.endswith(".py"))


def _read_allowlist() -> set[str]:
    src = _read("README.md")
    m = re.search(r"PYTEST_ONLY_ALLOWLIST_START -->(.*?)<!-- PYTEST_ONLY_ALLOWLIST_END",
                  src, re.DOTALL)
    assert m, "README.md に PYTEST_ONLY_ALLOWLIST マーカーが無い"
    names = re.findall(r"^-\s*(test_[\w.]+\.py)\s*$", m.group(1), re.MULTILINE)
    allow = set(names)
    assert len(allow) == len(names), f"allowlist に重複エントリ: {names}"
    return allow


def test_every_test_file_is_self_runnable_or_allowlisted():
    """偽緑ガードの本体: 自走 harness も allowlist 記載も無い test_*.py を検出する。"""
    allow = _read_allowlist()
    offenders = []
    for name in _test_files():
        if name == _SELF:
            continue
        if _self_runnable(_read(name)):
            continue
        if name in allow:
            continue
        offenders.append(name)
    assert not offenders, (
        "素の runner で 0 件実行の偽緑になりうる (自走 harness も pytest 専用 allowlist "
        f"記載も無い): {offenders}. _run()/__main__ を足すか README の allowlist に追加せよ")


def test_allowlist_has_no_stale_or_self_runnable_entries():
    """allowlist の陳腐化検出: 存在しないファイル、または自走 harness を後付けしたのに
    allowlist に残ったファイルを弾く (allowlist が偽緑を覆い隠すのを防ぐ)。"""
    allow = _read_allowlist()
    present = set(_test_files())
    missing = sorted(allow - present)
    assert not missing, f"allowlist に実在しないファイル (削除漏れ): {missing}"
    wrongly = sorted(n for n in allow if _self_runnable(_read(n)))
    assert not wrongly, (
        f"自走 harness を持つのに pytest 専用 allowlist に載っている (allowlist から外せ): {wrongly}")


def test_this_metatest_is_itself_self_runnable():
    """メタテスト自身が偽緑にならないこと (自己適用) — 自走 harness を持ち、allowlist に
    逃げていない。"""
    assert _self_runnable(_read(_SELF))
    assert _SELF not in _read_allowlist()


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = skipped = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except Skip as e:
            print(f"SKIP {fn.__name__}: {e}")
            skipped += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
