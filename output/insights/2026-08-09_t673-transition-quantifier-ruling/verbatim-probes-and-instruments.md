# 候補テストと親測定器の逐語凍結
[T-673] wave `dev-wave-t673-transition-pbt-package` / 2026-08-09
実行可能な `.py` は repo へ入れない ([T-627] 先例)。原本は wave の job directory と、
候補テストは probe commit `3912c7fc9a7e13cfcbc2491878767c548cb3cbd1` (branch `worktree-dev-wave-t673-probe`) にある。
**この commit は land 対象 branch の祖先ではない。**

## 候補テスト (段 5、Codex role=author)

### `orchestrator/tests/test_t673_probe_aprime.py`

- 行数 89 / SHA-256 `310d3e748e132aaa747f2b31ccf4765ba6e27553c2944457e8e69f78a9623366`

```python
# -*- coding: utf-8 -*-
"""T-673 A-prime: 手書きの 8-env fixture だけを増量した対抗案。"""
from __future__ import annotations

from types import MappingProxyType

import pytest

from test_env_contract_activation import _chain, _validate, activation


EIGHT_ENV_CATALOG = MappingProxyType({
    "env-000": (
        (1, "0000000000000000000000000000000000000000000000000000000000000000"),
        (2, "1111111111111111111111111111111111111111111111111111111111111111"),
    ),
    "env-001": (
        (1, "2222222222222222222222222222222222222222222222222222222222222222"),
        (2, "3333333333333333333333333333333333333333333333333333333333333333"),
    ),
    "env-002": (
        (1, "4444444444444444444444444444444444444444444444444444444444444444"),
        (2, "5555555555555555555555555555555555555555555555555555555555555555"),
    ),
    "env-003": (
        (1, "6666666666666666666666666666666666666666666666666666666666666666"),
        (2, "7777777777777777777777777777777777777777777777777777777777777777"),
    ),
    "env-004": (
        (1, "8888888888888888888888888888888888888888888888888888888888888888"),
        (2, "9999999999999999999999999999999999999999999999999999999999999999"),
    ),
    "env-005": (
        (1, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
        (2, "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
    ),
    "env-006": (
        (1, "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"),
        (2, "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"),
    ),
    "env-007": (
        (1, "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"),
        (2, "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),
    ),
})


def test_generation_quantifier_rejects_eighth_env_downgrade():
    records, head = _chain(
        (1, 1, 1, 1, 1, 1, 1, 2),
        (2, 2, 2, 2, 2, 2, 2, 1),
        registered_contracts=EIGHT_ENV_CATALOG,
    )
    with pytest.raises(
        activation.ActivationRecordError,
        match=r"exactly \+1.*env-007.*g2 -> g1",
    ):
        _validate(
            records,
            head,
            registered_contracts=EIGHT_ENV_CATALOG,
            predicate=lambda _old, _new: True,
        )


def test_successor_quantifier_rejects_eighth_env_false():
    records, head = _chain(
        (1, 1, 1, 1, 1, 1, 1, 1),
        (2, 2, 2, 2, 2, 2, 2, 2),
        registered_contracts=EIGHT_ENV_CATALOG,
    )
    with pytest.raises(
        activation.ActivationRecordError,
        match=r"successor でない.*env_tag=env-007",
    ):
        _validate(
            records,
            head,
            registered_contracts=EIGHT_ENV_CATALOG,
            predicate=lambda _old, new: new.env_tag != "env-007",
        )


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
```

### `orchestrator/tests/test_t673_probe_b1.py`

- 行数 150 / SHA-256 `c483cea3c560bad7233d3ff81033ae8bc97d61a17bae2b4b6d152d94538348df`

```python
# -*- coding: utf-8 -*-
"""T-673 B1: stdlib 生成器による bounded な遷移量化 probe。"""
from __future__ import annotations

import hashlib
from types import MappingProxyType

import pytest

from test_env_contract_activation import _chain, _validate, activation


ENV_COUNTS = (2, 4, 8, 16, 32, 64)


def _catalog(env_count: int) -> MappingProxyType:
    return MappingProxyType({
        env_tag: tuple(
            (
                generation,
                hashlib.sha256(
                    f"{env_tag}:g{generation}".encode("ascii")
                ).hexdigest(),
            )
            for generation in (1, 2)
        )
        for env_tag in (f"env-{index:03d}" for index in range(env_count))
    })


@pytest.mark.parametrize(
    "env_count",
    ENV_COUNTS,
    ids=["M2", "M4", "M8", "M16", "M32", "M64"],
)
def test_generation_quantifier_rejects_tail_downgrade(env_count: int):
    catalog = _catalog(env_count)
    predecessor = (1,) * (env_count - 1) + (2,)
    successor = (2,) * (env_count - 1) + (1,)
    records, head = _chain(
        predecessor,
        successor,
        registered_contracts=catalog,
    )
    bad_env = f"env-{env_count - 1:03d}"

    with pytest.raises(
        activation.ActivationRecordError,
        match=rf"exactly \+1.*{bad_env}.*g2 -> g1",
    ):
        _validate(
            records,
            head,
            registered_contracts=catalog,
            predicate=lambda _old, _new: True,
        )


@pytest.mark.parametrize(
    "env_count",
    ENV_COUNTS,
    ids=["M2", "M4", "M8", "M16", "M32", "M64"],
)
def test_successor_quantifier_rejects_tail_false(env_count: int):
    catalog = _catalog(env_count)
    records, head = _chain(
        (1,) * env_count,
        (2,) * env_count,
        registered_contracts=catalog,
    )
    bad_env = f"env-{env_count - 1:03d}"

    with pytest.raises(
        activation.ActivationRecordError,
        match=rf"successor でない.*env_tag={bad_env}",
    ):
        _validate(
            records,
            head,
            registered_contracts=catalog,
            predicate=lambda _old, new: new.env_tag != bad_env,
        )


@pytest.mark.parametrize(
    "bad_index",
    (0, 4, 7),
    ids=["first", "middle", "last"],
)
def test_generation_quantifier_rejects_downgrade_at_varied_position(
    bad_index: int,
):
    catalog = _catalog(8)
    predecessor = [1] * 8
    successor = [2] * 8
    predecessor[bad_index] = 2
    successor[bad_index] = 1
    records, head = _chain(
        tuple(predecessor),
        tuple(successor),
        registered_contracts=catalog,
    )
    bad_env = f"env-{bad_index:03d}"

    with pytest.raises(
        activation.ActivationRecordError,
        match=rf"exactly \+1.*{bad_env}.*g2 -> g1",
    ):
        _validate(
            records,
            head,
            registered_contracts=catalog,
            predicate=lambda _old, _new: True,
        )


@pytest.mark.parametrize(
    "bad_index",
    (0, 4, 7),
    ids=["first", "middle", "last"],
)
def test_successor_quantifier_rejects_false_at_varied_position(
    bad_index: int,
):
    catalog = _catalog(8)
    records, head = _chain(
        (1, 1, 1, 1, 1, 1, 1, 1),
        (2, 2, 2, 2, 2, 2, 2, 2),
        registered_contracts=catalog,
    )
    bad_env = f"env-{bad_index:03d}"

    with pytest.raises(
        activation.ActivationRecordError,
        match=rf"successor でない.*env_tag={bad_env}",
    ):
        _validate(
            records,
            head,
            registered_contracts=catalog,
            predicate=lambda _old, new: new.env_tag != bad_env,
        )


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
```

### `orchestrator/tests/test_t673_probe_b2.py`

- 行数 115 / SHA-256 `f38e5fadc59efbc01f2f3ecdb45e18759f5f61c565cb32e6b192f4646ebfcdf7`

```python
# -*- coding: utf-8 -*-
"""T-673 B2: Hypothesis による bounded な遷移量化 property。

Hypothesis 未導入環境では collection 時の ImportError をそのまま失敗にする。
skip や pytest.importorskip への縮退は行わない。
"""
from __future__ import annotations

import hashlib
from types import MappingProxyType

import hypothesis
import pytest
from hypothesis import example, given, settings, strategies as st

from test_env_contract_activation import _chain, _validate, activation


_VERSION_REPORTED = False


def _record_hypothesis_version() -> None:
    global _VERSION_REPORTED
    if not _VERSION_REPORTED:
        print(f"T-673 B2 hypothesis-version={hypothesis.__version__}")
        _VERSION_REPORTED = True


def _catalog(env_count: int) -> MappingProxyType:
    return MappingProxyType({
        env_tag: tuple(
            (
                generation,
                hashlib.sha256(
                    f"{env_tag}:g{generation}".encode("ascii")
                ).hexdigest(),
            )
            for generation in (1, 2)
        )
        for env_tag in (f"env-{index:03d}" for index in range(env_count))
    })


@settings(
    max_examples=64,
    derandomize=True,
    database=None,
    deadline=None,
)
@example(env_count=64)
@given(env_count=st.integers(min_value=2, max_value=64))
def test_generation_quantifier_property_rejects_tail_downgrade(
    env_count: int,
):
    _record_hypothesis_version()
    catalog = _catalog(env_count)
    predecessor = (1,) * (env_count - 1) + (2,)
    successor = (2,) * (env_count - 1) + (1,)
    records, head = _chain(
        predecessor,
        successor,
        registered_contracts=catalog,
    )
    bad_env = f"env-{env_count - 1:03d}"

    with pytest.raises(
        activation.ActivationRecordError,
        match=rf"exactly \+1.*{bad_env}.*g2 -> g1",
    ):
        _validate(
            records,
            head,
            registered_contracts=catalog,
            predicate=lambda _old, _new: True,
        )


@settings(
    max_examples=64,
    derandomize=True,
    database=None,
    deadline=None,
)
@example(env_count=64)
@given(env_count=st.integers(min_value=2, max_value=64))
def test_successor_quantifier_property_rejects_tail_false(
    env_count: int,
):
    _record_hypothesis_version()
    catalog = _catalog(env_count)
    records, head = _chain(
        (1,) * env_count,
        (2,) * env_count,
        registered_contracts=catalog,
    )
    bad_env = f"env-{env_count - 1:03d}"

    with pytest.raises(
        activation.ActivationRecordError,
        match=rf"successor でない.*env_tag={bad_env}",
    ):
        _validate(
            records,
            head,
            registered_contracts=catalog,
            predicate=lambda _old, new: new.env_tag != bad_env,
        )


def _run() -> int:
    return pytest.main([__file__, "-q", "-s"])


if __name__ == "__main__":
    raise SystemExit(_run())
```

### `orchestrator/tests/test_t673_probe_c1.py`

- 行数 149 / SHA-256 `df37b614626dcc85e4c634273b8d47714f2e3f0abf8098830eb1416f61116fee`

```python
# -*- coding: utf-8 -*-
"""T-673 C1: 遷移 gate の direct iterator を pin する AST 検査。

この検査が閉じるのは、対象 loop の直接 slice と、loop 前の Subscript を
使う再束縛・削除である。helper 呼出しや islice、alias の内部、callback の弱化、
caller 側の別量化は閉じない。また変数 rename や無害な iterator wrapper も拒否する。
"""
from __future__ import annotations

import ast

import pytest

from test_env_contract_activation import REPO_ROOT


def _is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _is_predicate_loop_target(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Tuple)
        and len(node.elts) == 2
        and _is_name(node.elts[0], "predecessor")
        and _is_name(node.elts[1], "successor")
    )


def _target_binds_name(node: ast.AST, name: str) -> bool:
    if _is_name(node, name):
        return True
    if isinstance(node, (ast.Tuple, ast.List)):
        return any(_target_binds_name(element, name) for element in node.elts)
    return False


def _subscript_root_name(node: ast.AST) -> str | None:
    while isinstance(node, ast.Subscript):
        node = node.value
    if isinstance(node, ast.Name):
        return node.id
    return None


def _preloop_slice_rebindings_or_deletes(
    function: ast.FunctionDef,
    *,
    name: str,
    loop_lineno: int,
) -> list[str]:
    offenders: list[str] = []
    for node in ast.walk(function):
        if getattr(node, "lineno", loop_lineno) >= loop_lineno:
            continue
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr, ast.AugAssign)):
            targets = [node.target]
            value = node.value
        else:
            targets = []
            value = None
        if targets and value is not None:
            binds_name = any(_target_binds_name(target, name) for target in targets)
            mutates_slice = any(
                isinstance(target, ast.Subscript)
                and _subscript_root_name(target) == name
                for target in targets
            )
            contains_subscript = any(
                isinstance(descendant, ast.Subscript)
                for descendant in ast.walk(value)
            )
            if (binds_name and contains_subscript) or mutates_slice:
                offenders.append(type(node).__name__)
        if isinstance(node, ast.Delete) and any(
            _is_name(target, name)
            or (
                isinstance(target, ast.Subscript)
                and _subscript_root_name(target) == name
            )
            for target in node.targets
        ):
            offenders.append("Delete")
    return offenders


def test_activation_transition_quantifier_loops_are_direct_and_unsliced():
    path = REPO_ROOT / "orchestrator/campaign/env_contract_activation.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "_validate_activation_transition"
    ]
    assert len(matches) == 1, (
        "_validate_activation_transition FunctionDef must be exactly one; "
        f"observed={len(matches)}"
    )
    function = matches[0]

    loops = [node for node in ast.walk(function) if isinstance(node, ast.For)]
    assert len(loops) == 2, (
        "transition quantifier loops must be exactly two; "
        f"observed={len(loops)}"
    )
    generation_loops = [
        loop for loop in loops if _is_name(loop.target, "successor")
    ]
    predicate_loops = [
        loop for loop in loops if _is_predicate_loop_target(loop.target)
    ]
    assert len(generation_loops) == 1, (
        "successor_rows quantifier loop must be exactly one; "
        f"observed={len(generation_loops)}"
    )
    assert len(predicate_loops) == 1, (
        "changed quantifier loop must be exactly one; "
        f"observed={len(predicate_loops)}"
    )

    generation_loop = generation_loops[0]
    predicate_loop = predicate_loops[0]
    assert type(generation_loop.iter) is ast.Name
    assert generation_loop.iter.id == "successor_rows"
    assert type(predicate_loop.iter) is ast.Name
    assert predicate_loop.iter.id == "changed"

    assert _preloop_slice_rebindings_or_deletes(
        function,
        name="successor_rows",
        loop_lineno=generation_loop.lineno,
    ) == []
    assert _preloop_slice_rebindings_or_deletes(
        function,
        name="changed",
        loop_lineno=predicate_loop.lineno,
    ) == []


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
```

### `orchestrator/tests/test_t673_probe_c3.py`

- 行数 59 / SHA-256 `fdc448ced7ff2edf85f2fb710f5eda9b79197759b81218ebe031cea18a0f013d`

```python
# -*- coding: utf-8 -*-
"""T-673 C3: successor_rows の slice を runtime sentinel で拒否する。

successor_rows は引数なので量化点 G へ sentinel を注入できる。一方 changed は
関数内で構築される list であり、この probe は量化点 P を閉じない。
"""
from __future__ import annotations

import pytest

from test_env_contract_activation import activation


class _SliceAccessError(AssertionError):
    pass


class _SliceForbiddenTuple(tuple):
    def __getitem__(self, index):
        if isinstance(index, slice):
            raise _SliceAccessError("successor_rows was sliced")
        return super().__getitem__(index)


def _transition_rows():
    predecessor_rows = (
        activation.ActiveContract("env-a", 1, "1" * 64),
        activation.ActiveContract("env-b", 1, "3" * 64),
    )
    successor_rows = _SliceForbiddenTuple((
        activation.ActiveContract("env-a", 2, "2" * 64),
        activation.ActiveContract("env-b", 2, "4" * 64),
    ))
    return predecessor_rows, successor_rows


def test_successor_rows_sentinel_rejects_slice_access():
    _predecessor_rows, successor_rows = _transition_rows()
    with pytest.raises(_SliceAccessError, match="successor_rows was sliced"):
        successor_rows[:1]


def test_transition_gate_iterates_successor_rows_without_slicing():
    predecessor_rows, successor_rows = _transition_rows()
    result = activation._validate_activation_transition(
        predecessor_rows,
        successor_rows,
        activation_serial=2,
        is_valid_registered_successor=lambda _old, _new: True,
    )
    assert result is None


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
```

## 親の測定器 (repo 外。実行可能原本は job directory)

### `parent_probe_ast_precedent.py` — 既存 AST 先例が [:N] を全 N 殺すかを測る

- 行数 53 / SHA-256 `7e1f3ab9590f3ef30f395629dce20fed95f028ae93b0c95d7ae9279b3a38ab15`

```python
#!/usr/bin/env python3
"""親の測定器: 既存 AST 先例が `[:N]` truncation を N によらず殺すかを確かめる。

対象は orchestrator/tests/test_campaign.py::test_evaluate_commit_writes_are_syntactically_verify_gated
が使う判定式そのもの (`isinstance(n.iter, ast.Name) and n.iter.id == "passes"`)。
production を編集せず、source 文字列を in-memory で変異させて判定式の挙動だけを見る。
"""
import ast
import sys
from pathlib import Path

REPO = Path(sys.argv[1])
SRC = REPO / "orchestrator" / "campaign" / "pipeline.py"
ANCHOR = "    for tag, workload, fullscale_isolated in passes:\n"

original = SRC.read_text(encoding="utf-8")
assert original.count(ANCHOR) == 1, "anchor が一意でない"


def precedent_predicate_finds_loop(source: str) -> bool:
    """先例テストと同じ判定式。見つからなければ StopIteration = テスト赤。"""
    tree = ast.parse(source)
    evaluate_node = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "evaluate"
    )
    try:
        next(
            n for n in ast.walk(evaluate_node)
            if isinstance(n, ast.For)
            and isinstance(n.iter, ast.Name) and n.iter.id == "passes"
        )
    except StopIteration:
        return False
    return True


print(f"baseline(unmutated): finds_loop={precedent_predicate_finds_loop(original)}")
for n in (1, 2, 3, 4, 8, 63, 64, 1000, 10**9):
    mutated = original.replace(
        ANCHOR,
        f"    for tag, workload, fullscale_isolated in passes[:{n}]:\n",
    )
    assert mutated != original
    print(f"  passes[:{n}]: finds_loop={precedent_predicate_finds_loop(mutated)}")

# 意味保存 refactor に対する偽陽性も同時に測る (レンズ A/B の争点)。
for label, repl in (
    ("tuple(passes)", "    for tag, workload, fullscale_isolated in tuple(passes):\n"),
    ("rename passes->ps", "    for tag, workload, fullscale_isolated in ps:\n"),
):
    mutated = original.replace(ANCHOR, repl)
    print(f"  refactor {label}: finds_loop={precedent_predicate_finds_loop(mutated)}")
```

### `parent_probe_c1_controls.py` — C1 の負制御 (何を殺し何を見逃し何を誤検出するか)

- 行数 134 / SHA-256 `00e2f09f2cf3b482c2f880dfccb43d579765846d58f7760171fbf9d70a8b00c2`

```python
#!/usr/bin/env python3
"""親の測定器: C1 (AST 構造検査) の負制御を in-memory で測る。

C1 の判定コードは probe commit の逐語をそのまま exec し、読む対象のソース文字列だけを
差し替える。したがって「親が書き直した近似」ではなく C1 そのものを測っている。
"""
import ast
import subprocess
import sys
import textwrap

REPO = "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package"
PROBE_COMMIT = "3912c7fc9a7e13cfcbc2491878767c548cb3cbd1"
PROD = "orchestrator/campaign/env_contract_activation.py"

G_OLD = "    for successor in successor_rows:\n"
P_OLD = "    for predecessor, successor in changed:\n"


def git_show(ref: str, path: str) -> str:
    return subprocess.run(
        ["git", "-C", REPO, "show", f"{ref}:{path}"],
        check=True, capture_output=True, text=True,
    ).stdout


c1_src = git_show(PROBE_COMMIT, "orchestrator/tests/test_t673_probe_c1.py")
production = git_show(PROBE_COMMIT, PROD)

# sibling import と file 読みだけを差し替え、判定本体は逐語で残す。
c1_src = c1_src.replace("from test_env_contract_activation import REPO_ROOT\n", "")
c1_src = c1_src.replace("import pytest\n", "")
c1_src = c1_src.replace(
    '    path = REPO_ROOT / "orchestrator/campaign/env_contract_activation.py"\n'
    '    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))\n',
    "    tree = ast.parse(SOURCE)\n",
)
c1_src = c1_src.split("def _run()")[0]

namespace: dict = {"ast": ast}


def c1_verdict(source: str) -> str:
    """C1 を走らせて 'RED' (検査が赤 = 検出) か 'GREEN' (素通り) を返す。"""
    namespace["SOURCE"] = source
    exec(compile(c1_src, "<c1>", "exec"), namespace)
    try:
        namespace["test_activation_transition_quantifier_loops_are_direct_and_unsliced"]()
    except AssertionError:
        return "RED"
    except Exception as exc:  # noqa: BLE001
        return f"RED({type(exc).__name__})"
    return "GREEN"


print("baseline (unmutated):", c1_verdict(production))
print()

print("== 直接 slice 変異 (C1 が殺すべきもの) ==")
for name, old in (("successor_rows", G_OLD), ("changed", P_OLD)):
    for n in (1, 4, 64, 10**6):
        mutated = production.replace(old, old.replace(f"in {name}:", f"in {name}[:{n}]:"))
        assert mutated != production
        print(f"  {name}[:{n}]: {c1_verdict(mutated)}")
print()

print("== 等価な縮退 (C1 が殺せるか) ==")
controls = {
    "事前 slice 再束縛 (changed = changed[:4])":
        (P_OLD, "    changed = changed[:4]\n" + P_OLD),
    "del changed[4:]":
        (P_OLD, "    del changed[4:]\n" + P_OLD),
    "decoy loop を足して実 loop を切る":
        (P_OLD,
         "    for _decoy in changed:\n        pass\n"
         + P_OLD.replace("in changed:", "in changed[:4]:")),
    "別名へ slice して loop 名は据置 (alias)":
        (P_OLD,
         "    limited = changed[:4]\n"
         + P_OLD
         + "        if (predecessor, successor) not in limited:\n            continue\n"),
    "islice で実効集合を縮める":
        (P_OLD,
         "    import itertools\n"
         "    changed_view = itertools.islice(changed, 4)\n"
         + P_OLD.replace("in changed:", "in changed_view:")),
    "冒頭 return で 2 loop を到達不能にする":
        ("    predecessor_by_env = {row.env_tag: row for row in predecessor_rows}\n",
         "    return None\n"
         "    predecessor_by_env = {row.env_tag: row for row in predecessor_rows}\n"),
}
for label, (old, new) in controls.items():
    assert production.count(old) == 1, label
    print(f"  {label}: {c1_verdict(production.replace(old, new))}")
print()

print("== 意味保存 refactor (C1 の偽陽性) ==")


def rename_changed(source: str) -> str:
    """local 変数 `changed` を定義側も含めて `pending` へ改名する (意味保存)。

    段 6 焦点再レビューの指摘: loop 側だけ書き換えると NameError になり、
    意味保存 refactor ではなく壊れた変更を測ってしまう。
    """
    pairs = [
        ("    changed: list[tuple[ActiveContract, ActiveContract]] = []\n",
         "    pending: list[tuple[ActiveContract, ActiveContract]] = []\n"),
        ("        changed.append((predecessor, successor))\n",
         "        pending.append((predecessor, successor))\n"),
        ("    if not changed:\n", "    if not pending:\n"),
        (P_OLD, P_OLD.replace("in changed:", "in pending:")),
    ]
    out = source
    for old, new in pairs:
        assert out.count(old) == 1, f"rename anchor が一意でない: {old!r}"
        out = out.replace(old, new)
    assert "changed" not in out.split("def _validate_activation_transition")[1].split(
        "\ndef ")[0], "rename 漏れがある"
    return out


false_positives = {
    "tuple(changed) 化": production.replace(
        P_OLD, P_OLD.replace("in changed:", "in tuple(changed):")),
    "変数 rename (定義側も含む、意味保存)": rename_changed(production),
    "診断用 loop の追加": production.replace(
        P_OLD, "    for _row in successor_rows:\n        pass\n" + P_OLD),
    "コメント行の追加 (無害の対照)": production.replace(
        P_OLD, "    # 診断用のコメント\n" + P_OLD),
}
for label, mutated in false_positives.items():
    assert mutated != production, label
    print(f"  {label}: {c1_verdict(mutated)}")
```

### `make_specs.py` — A の変異事前登録を生成する

- 行数 86 / SHA-256 `2fadfcc011aaa5791fda9850db87bbc3b1ce7646eeccfbc675ae0b9837e92d3a`

```python
#!/usr/bin/env python3
"""親の測定器: 段 4 裁定 §3 の変異事前登録を spec JSON として書き出す。

matrix 1 = focal 4 node (frontier と帰属)
matrix 2 = full-file、生存側だけ (A の真の検出天井)
"""
import json
from pathlib import Path

OUT = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package")
FILE = "orchestrator/campaign/env_contract_activation.py"
T = "orchestrator/tests/test_env_contract_activation.py"

G_OLD = "    for successor in successor_rows:\n"
P_OLD = "    for predecessor, successor in changed:\n"

D4 = f"{T}::test_transition_rejects_fourth_env_downgrade"
P2 = f"{T}::test_transition_rejects_when_second_changed_env_successor_is_false"
P3 = f"{T}::test_transition_rejects_when_third_changed_env_successor_is_false"
P4 = f"{T}::test_transition_rejects_when_fourth_changed_env_successor_is_false"

NS = (1, 2, 3, 4, 8, 63, 64)
SURVIVOR_NS = (4, 8, 63, 64)

# 段 4 裁定 §3 matrix 1 の期待表。G は changed の母集合を縮めるため P 系 node も落とす。
FOCAL_KILLED = {
    ("G", 1): [D4, P2, P3, P4],
    ("G", 2): [D4, P3, P4],
    ("G", 3): [D4, P4],
    ("P", 1): [P2, P3, P4],
    ("P", 2): [P3, P4],
    ("P", 3): [P4],
}


def mutation(site: str, n: int, expected_nodes: list[str], status: str) -> dict:
    old = G_OLD if site == "G" else P_OLD
    name = "successor_rows" if site == "G" else "changed"
    new = old.replace(f"in {name}:", f"in {name}[:{n}]:")
    assert new != old
    return {
        "id": f"{site}-N{n}",
        "category": "negative",
        "replacements": [{"file": FILE, "old": old, "new": new}],
        "expected_nodes": sorted(expected_nodes),
        "expected_status": status,
        "hang_risk": False,
    }


def spec(mutations: list[dict], estimated: float) -> dict:
    return {
        "schema": "izanagi-dev-wave-mutation-spec/v1",
        "estimated_run_seconds": estimated,
        "timeout_seconds": 3600,
        "hang_timeout_seconds": 600,
        "mutations": mutations,
    }


matrix1 = []
for site in ("G", "P"):
    for n in NS:
        key = (site, n)
        if key in FOCAL_KILLED:
            matrix1.append(mutation(site, n, FOCAL_KILLED[key], "KILLED"))
        else:
            matrix1.append(mutation(site, n, [], "SURVIVED"))

matrix2 = [
    mutation(site, n, [], "SURVIVED")
    for site in ("G", "P")
    for n in SURVIVOR_NS
]

# estimated_run_seconds は 1 run あたりの見積り。T-627 実績 26.9〜42.3 秒に余裕を見る。
for name, doc, est in (
    ("mutation-spec-A-focal.json", spec(matrix1, 60), None),
    ("mutation-spec-A-fullfile-survivors.json", spec(matrix2, 90), None),
):
    path = OUT / name
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")
    import hashlib
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"{name}: {len(doc['mutations'])} mutations sha256={digest}")
```

### `make_candidate_specs.py` — 候補 5 種の変異事前登録を生成する

- 行数 126 / SHA-256 `748934b1044f55514e0fb9e0481951591a455316749f3b6a39444aae8cc7af3c`

```python
#!/usr/bin/env python3
"""親の測定器: 候補 (A' / B1 / B2 / C1 / C3) の変異事前登録を書き出す。

期待集合は親が probe 本文を読んで導出した。導出規則:
  G 変異 = successor_rows[:N]  (loop 1 = exactly +1 判定の走査範囲)
  P 変異 = changed[:N]         (loop 2 = successor 述語の適用範囲)
  末尾に不正がある M env fixture は、G では N < M、P では N < M のとき見逃す。
  位置可変 fixture (M=8, 不正 index i) は N <= i のとき見逃す。
  G 変異は loop 1 を切るため changed の母集合も縮み、P 側の witness も同時に消す。
  P 変異は loop 1 に触れないので、downgrade を loop 1 で捕まえる node には影響しない。
"""
import hashlib
import json
from pathlib import Path

OUT = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package")
FILE = "orchestrator/campaign/env_contract_activation.py"
G_OLD = "    for successor in successor_rows:\n"
P_OLD = "    for predecessor, successor in changed:\n"
NS = (1, 2, 3, 4, 8, 63, 64)
MS = (2, 4, 8, 16, 32, 64)
POS = {"first": 0, "middle": 4, "last": 7}


def nid(stem: str, name: str, param: str | None = None) -> str:
    suffix = f"[{param}]" if param else ""
    return f"orchestrator/tests/test_t673_probe_{stem}.py::{name}{suffix}"


def b1_failures(site: str, n: int) -> list[str]:
    out: list[str] = []
    for m in MS:
        if n < m:
            out.append(nid("b1", "test_successor_quantifier_rejects_tail_false", f"M{m}"))
            if site == "G":
                out.append(
                    nid("b1", "test_generation_quantifier_rejects_tail_downgrade", f"M{m}")
                )
    for label, index in POS.items():
        if n <= index:
            out.append(
                nid("b1", "test_successor_quantifier_rejects_false_at_varied_position", label)
            )
            if site == "G":
                out.append(
                    nid(
                        "b1",
                        "test_generation_quantifier_rejects_downgrade_at_varied_position",
                        label,
                    )
                )
    return out


def b2_failures(site: str, n: int) -> list[str]:
    # @example(env_count=64) が M=64 を必ず通すため、N<64 なら必ず失敗する。
    if n >= 64:
        return []
    out = [nid("b2", "test_successor_quantifier_property_rejects_tail_false")]
    if site == "G":
        out.append(nid("b2", "test_generation_quantifier_property_rejects_tail_downgrade"))
    return out


def aprime_failures(site: str, n: int) -> list[str]:
    if n >= 8:
        return []
    out = [nid("aprime", "test_successor_quantifier_rejects_eighth_env_false")]
    if site == "G":
        out.append(nid("aprime", "test_generation_quantifier_rejects_eighth_env_downgrade"))
    return out


def c1_failures(_site: str, _n: int) -> list[str]:
    # AST 検査は N に依存せず、両量化点のどちらを切っても発火する。
    return [nid("c1", "test_activation_transition_quantifier_loops_are_direct_and_unsliced")]


def c3_failures(site: str, _n: int) -> list[str]:
    # sentinel は引数 successor_rows にしか注入できない → P は閉じない。
    if site != "G":
        return []
    return [nid("c3", "test_transition_gate_iterates_successor_rows_without_slicing")]


CANDIDATES = {
    "b1": (b1_failures, 90),
    "b2": (b2_failures, 180),
    "aprime": (aprime_failures, 60),
    "c1": (c1_failures, 60),
    "c3": (c3_failures, 60),
}

for stem, (fn, est) in CANDIDATES.items():
    mutations = []
    for site in ("G", "P"):
        old = G_OLD if site == "G" else P_OLD
        name = "successor_rows" if site == "G" else "changed"
        for n in NS:
            failures = sorted(set(fn(site, n)))
            mutations.append({
                "id": f"{site}-N{n}",
                "category": "negative",
                "replacements": [{
                    "file": FILE,
                    "old": old,
                    "new": old.replace(f"in {name}:", f"in {name}[:{n}]:"),
                }],
                "expected_nodes": failures,
                "expected_status": "KILLED" if failures else "SURVIVED",
                "hang_risk": False,
            })
    doc = {
        "schema": "izanagi-dev-wave-mutation-spec/v1",
        "estimated_run_seconds": est,
        "timeout_seconds": 3600,
        "hang_timeout_seconds": 600,
        "mutations": mutations,
    }
    path = OUT / f"mutation-spec-{stem}.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")
    killed = sum(1 for m in mutations if m["expected_status"] == "KILLED")
    print(f"mutation-spec-{stem}.json: {len(mutations)} mutations "
          f"(KILLED={killed}, SURVIVED={len(mutations) - killed}) "
          f"sha256={hashlib.sha256(path.read_bytes()).hexdigest()}")
```

### `summarize.py` — 全台帳から frontier 表を作る

- 行数 52 / SHA-256 `47ea14f9e7a30501b919a2170ad8d42e6775c8b54c3a00366572d2f1833fcb23`

```python
#!/usr/bin/env python3
"""親の測定器: 全 ledger を読み、frontier とコストの表を作る。"""
import json
from pathlib import Path

D = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package")

LEDGERS = [
    ("A (focal 4 node)", "mutation-ledger-A-focal-run.json"),
    ("A (full file)", "mutation-ledger-A-full-run.json"),
    ("A' (8 env 手書き)", "mutation-ledger-cand-aprime.json"),
    ("B1 (stdlib 掃引)", "mutation-ledger-cand-b1.json"),
    ("B2 (hypothesis)", "mutation-ledger-cand-b2.json"),
    ("C1 (AST 構造)", "mutation-ledger-cand-c1.json"),
    ("C3 (sentinel)", "mutation-ledger-cand-c3.json"),
]

print(f"{'option':22s} {'summary':38s} {'baseline_s':>10s} {'mut_med_s':>10s}")
print("-" * 84)
rows = {}
for label, name in LEDGERS:
    path = D / name
    if not path.is_file():
        print(f"{label:22s} (ledger 不在)")
        continue
    d = json.loads(path.read_text())
    s = d["summary"]
    durations = sorted(m["duration_s"] for m in d["mutations"])
    med = durations[len(durations) // 2] if durations else float("nan")
    summ = (f"K={s['KILLED']} S={s['SURVIVED']} MIS={s['MISMATCH']} "
            f"match={s['matching']}/{s['registered']}")
    print(f"{label:22s} {summ:38s} {d['baseline']['duration_s']:10.1f} {med:10.1f}")
    rows[label] = {m["id"]: m for m in d["mutations"]}

print()
print("frontier (site x N -> status)")
ids = [f"{site}-N{n}" for site in ("G", "P") for n in (1, 2, 3, 4, 8, 63, 64)]
print(f"{'option':22s} " + " ".join(f"{i:7s}" for i in ids))
for label in rows:
    cells = []
    for i in ids:
        m = rows[label].get(i)
        if m is None:
            cells.append("  -    ")
        else:
            mark = "K" if m["status"] == "KILLED" else ("S" if m["status"] == "SURVIVED" else "?")
            if not m["matches_expectation"]:
                mark += "!"
            cells.append(f"{mark:7s}")
    print(f"{label:22s} " + " ".join(cells))
print()
print("K=KILLED (検出), S=SURVIVED (見逃し), ! = 事前登録と不一致")
```

### `extract_cost.py` — 台帳の baseline stdout から pytest 秒と node 数を取る

- 行数 35 / SHA-256 `680326df85098c2336b808d7e453398bdc11bd914867b946846546b7bfc76b3d`

```python
#!/usr/bin/env python3
"""親の測定器: ledger の baseline stdout から pytest の実時間と node 数を取り出す。"""
import json
import re
from pathlib import Path

D = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package")
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
SUMMARY = re.compile(r"(\d+) passed.*?in ([\d.]+)s")

LEDGERS = [
    ("A (focal 4 node)", "mutation-ledger-A-focal-run.json"),
    ("A (full file)", "mutation-ledger-A-full-run.json"),
    ("A' (8 env)", "mutation-ledger-cand-aprime.json"),
    ("B1 (stdlib)", "mutation-ledger-cand-b1.json"),
    ("B2 (hypothesis)", "mutation-ledger-cand-b2.json"),
    ("C1 (AST)", "mutation-ledger-cand-c1.json"),
    ("C3 (sentinel)", "mutation-ledger-cand-c3.json"),
]

print(f"{'option':22s} {'node':>5s} {'pytest_s':>9s}")
print("-" * 40)
for label, name in LEDGERS:
    path = D / name
    if not path.is_file():
        continue
    d = json.loads(path.read_text())
    stdout = ANSI.sub("", d["baseline"]["artifact"].get("stdout", "") or "")
    hits = SUMMARY.findall(stdout)
    if hits:
        nodes, secs = hits[-1]
        print(f"{label:22s} {nodes:>5s} {secs:>9s}")
    else:
        tail = " / ".join(line for line in stdout.splitlines()[-4:] if line.strip())
        print(f"{label:22s} (summary 行を抽出できない: {tail[:70]})")
```

### `compute_base.py` — spool fragment の base digest を正本経路で算出する

- 行数 29 / SHA-256 `37be1b05f3c8f60cd2432028f460170ee0356a50e138b4c6c99883fb5d068a9b`

```python
#!/usr/bin/env python3
"""親の測定器: spool fragment の `base:` digest を spool_fold の正本経路で算出する。

memory: base は「見た目の行の sha256」ではなく carry 解決後の item digest である。
算出は spool_fold の _extract_latest_active / _digest 経路だけが正しい。
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package")
spec = importlib.util.spec_from_file_location("spool_fold", REPO / "tools" / "spool_fold.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["spool_fold"] = mod
spec.loader.exec_module(mod)

worklog = (REPO / "docs" / "worklog.md").read_text(encoding="utf-8")
archives = {
    p.name: p.read_text(encoding="utf-8")
    for p in sorted((REPO / "docs" / "archive").glob("worklog-*.md"))
}
ordinal, active = mod._extract_latest_active(worklog, archives)
print("latest ordinal:", ordinal)
wanted = set(sys.argv[1:]) or {"T-673"}
for item in active:
    if item.task_id in wanted or item.task_id.strip("[]") in wanted:
        print(f"{item.task_id}  base={item.substantive_digest}")
        print("---- body ----")
        print(item.block)
```
