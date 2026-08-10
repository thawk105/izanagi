# -*- coding: utf-8 -*-
"""`test_dev_waves_integration.py` の隔離契約と直列契約を機械検査する meta-test。

[T-132] で 1 file 1 xdist group を外した。全 node を同時実行に開くと、socket・serve thread・
実 daemon プロセスといった**プロセス外の資源**を持つ node が他ファイルの node と worker を
共有する。そこで、それらに (helper 経由も含めて) 触れる node だけを 1 つの group に残す。
この構成は「各 node が自分の一時ディレクトリと自分のプロセス資源に閉じている」ことに依存するが、
壊したときに必ず赤くなる検査が無かった (敵対相談 2 本が独立に blocker として指摘)。

**この検査が守らないもの**: 時間境界に依存する node のフレーク ([T-136])。内部締切は
`_supervisor()` / `_request()` を通じて 40/41 の node が持つため直列化では隔離できず、
実際に group あり構成でも load 11 で赤が出る。時間依存の解決は [T-136] の射程である。
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
_REPO_ROOT = _ORCHESTRATOR.parent
for _path in (str(_HERE), str(_REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from skiputil import skip  # noqa: E402  (二重 runner 契約: _run が Skip を捕捉する)

_TARGET = _HERE / "test_dev_waves_integration.py"
_GROUP = "dev-waves-runtime"

# プロセス外の資源を掴む呼び出しの語彙。ここに載る名前を (helper 経由でも) 使う test 関数は、
# 他 node と同時に走らせない。語彙を増やすときは「なぜ同時実行で壊れるか」を 1 行で書けること。
_RUNTIME_VOCABULARY = re.compile(
    r"bind_repo_socket|threading\.Thread|subprocess\.Popen|Popen\(|SIGKILL|daemon_mod"
    # socket.socket: 本番実装を通さず生の AF_UNIX を bind する node がある ([T-138] の
    # capability probe)。同時実行すると同じ runtime dir の socket path を奪い合い、
    # socket module を差し替える mock が同 worker の他 node へ漏れる。
    r"|socket\.socket"
)


def _module() -> ast.Module:
    return ast.parse(_TARGET.read_text(encoding="utf-8"), filename=str(_TARGET))


def _source_lines() -> list[str]:
    return _TARGET.read_text(encoding="utf-8").splitlines()


def _functions(module: ast.Module) -> dict[str, ast.FunctionDef]:
    return {
        node.name: node for node in module.body if isinstance(node, ast.FunctionDef)
    }


def _called_local_names(function: ast.FunctionDef, known: dict[str, ast.FunctionDef]) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        callee = node.func
        name = callee.id if isinstance(callee, ast.Name) else getattr(callee, "attr", "")
        if name in known:
            names.add(name)
    return names


def _runtime_touching(module: ast.Module) -> set[str]:
    """module 内の呼び出しを推移的に辿り、プロセス外資源へ到達する関数名を返す。"""
    functions = _functions(module)
    lines = _source_lines()
    tainted = {
        name for name, node in functions.items()
        if _RUNTIME_VOCABULARY.search("\n".join(lines[node.lineno - 1:node.end_lineno]))
    }
    changed = True
    while changed:
        changed = False
        for name, node in functions.items():
            if name in tainted:
                continue
            if _called_local_names(node, functions) & tainted:
                tainted.add(name)
                changed = True
    return tainted


def _group_names(function: ast.FunctionDef) -> list[str]:
    names: list[str] = []
    for decorator in function.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        target = decorator.func
        if (isinstance(target, ast.Attribute) and target.attr == "xdist_group"
                and decorator.args and isinstance(decorator.args[0], ast.Constant)):
            names.append(decorator.args[0].value)
    return names


def test_every_node_that_touches_process_external_resources_stays_serialised() -> None:
    """socket / thread / 実 daemon を掴む node だけが直列 group を持つこと。

    marker を落とすと当該 node は他ファイルの node と worker を共有し、serve thread や
    socket FD が次の node へ残り得る。逆に marker を増やすと黙って直列化が広がり wall が伸びる。
    どちらも実行時には静かに通るため、構文から導出して突き合わせる。
    """
    module = _module()
    functions = _functions(module)
    tests = {name for name in functions if name.startswith("test_")}
    expected = _runtime_touching(module) & tests
    # 語彙が何にもマッチしなければこの検査は恒真になる (F9 型) ため、下限を固定する。
    assert len(expected) >= 5, (
        f"runtime 語彙が {len(expected)} 個にしか届いていない。語彙かファイル構造が変わった: "
        f"{sorted(expected)}"
    )
    actual = {name for name in tests if _group_names(functions[name])}
    assert actual == expected, (
        f"直列 group の過不足: 余分={sorted(actual - expected)} 欠落={sorted(expected - actual)}"
    )
    for name in sorted(actual):
        # xdist は複数 group 名を結合するため、2 個目を足すと別 group になり排他が壊れる。
        assert _group_names(functions[name]) == [_GROUP], (
            f"{name} の xdist_group は {_GROUP} 1 個だけ: {_group_names(functions[name])}"
        )


def _real_repo_serial_nodes() -> frozenset[str]:
    """conftest の正本を読む。pytest 不在の素の runner では検査を skip する。"""
    try:
        from orchestrator.tests.conftest import REAL_REPO_SERIAL_NODES
    except ImportError as exc:
        if exc.name == "pytest":
            skip(f"pytest 不在のため conftest を import できない ({exc})")
        raise
    return frozenset(REAL_REPO_SERIAL_NODES)


def test_no_module_wide_group_and_no_overlap_with_the_real_repo_group() -> None:
    """module 一括 group が復活していないこと、real-repo 正本と重ならないこと。"""
    module = _module()
    assert not any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "pytestmark"
                for target in node.targets)
        for node in module.body
    ), "module 全体を 1 group にする pytestmark は [T-132] で外した"

    overlap = {node for node in _real_repo_serial_nodes()
               if node.startswith("test_dev_waves_integration.py::")}
    assert overlap == set(), (
        "このファイルの node が real-repo 正本に入ると conftest の自動付与と marker が"
        f"二重になり排他が壊れる: {sorted(overlap)}"
    )


def test_no_test_function_hands_the_repository_root_to_a_rooted_helper() -> None:
    """各 node の作業根が repo 本体になっていないこと (隔離の positive control)。

    これが破れると node は自分の一時ディレクトリではなく作業中の repo へ書き、並列実行時に
    他 node と衝突する。低負荷の全走反復では衝突しないまま緑になりうるため構文で固定する。
    """
    module = _module()
    rooted = {"_temporary_repo", "_isolated_process_environment"}
    violations: list[str] = []
    for name, function in _functions(module).items():
        if not name.startswith("test_"):
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            callee = node.func
            called = callee.id if isinstance(callee, ast.Name) else getattr(callee, "attr", "")
            if called not in rooted:
                continue
            first = node.args[0]
            if isinstance(first, ast.Name) and first.id in {"_REPO", "_BOOTSTRAP_REPO"}:
                violations.append(f"{name}:{node.lineno} が {called}({first.id}, ...)")
    assert violations == [], (
        "node は自分の一時ディレクトリを作業根にすること: " + "; ".join(violations)
    )


def _run() -> int:
    """pytest 不在でも `python3 test_dev_waves_isolation_contract.py` で走る二重 runner。"""
    from skiputil import Skip

    passed = failed = skipped = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"PASS {name}")
            passed += 1
        except Skip as exc:
            print(f"SKIP {name}: {exc}")
            skipped += 1
        except AssertionError as exc:
            print(f"FAIL {name}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {name}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
