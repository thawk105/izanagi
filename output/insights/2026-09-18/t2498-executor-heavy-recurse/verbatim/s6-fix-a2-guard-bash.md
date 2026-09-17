## 実装した内容

[hooks/guard_bash.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2498-guard-impl/hooks/guard_bash.py:1250) の executor 層剥きを反復へ変更しました。

- `peel_executors=True` の入口だけで層を剥き、各層は `peel_executors=False` で全 gate を検査。
- 合成 segment を `_heavy_head_and_args` で再解釈して次層へ進行。
- 深さ上限なし。正規形 token 数の厳密減少と、executor 検査の追加 stack 深さが 1 である根拠を docstring に記載。
- shell block 直後・sanctioned 早期許可前の位置を維持。

parser の処理、option 表、targets の返り値、`main()` は変更していません。

## 実測 (decide 直呼び)

`compile()` による構文検査と `git diff --check` は成功。検証コードは [/tmp/t2498_fix_probe.py](/tmp/t2498_fix_probe.py) です。pytest は実行していません。

以下、A＝ALLOW、D＝DENY。`repo_root` は指定 worktree の絶対パスです。

**v1 §2 全行**：LOGIN は全件期待どおり。OTHER／PEGASUS_COMPUTE でも全行を確認しました。

| command | LOGIN | OTHER | COMPUTE |
|---|---|---|---|
| `python3 -m pytest -q` | D | A | A |
| `python3 -m cProfile -m pytest -q` | D | A | A |
| `python3 -mcProfile -mpytest -q` | D | A | A |
| `python3 -m cProfile -o /tmp/p.out -m pytest -q orchestrator/tests/test_hooks.py` | D | A | A |
| `python3 -m profile -m pytest -q` | D | A | A |
| `python3 -m coverage run -m pytest -q` | D | A | A |
| `python3 -m pdb -m pytest -q` | D | A | A |
| `python3 -m trace --trace --module pytest -q` | D | A | A |
| `python3 -m runpy pytest -q` | D | A | A |
| `python3 -m cProfile -m cProfile -m pytest -q` | D | A | A |
| `python3 -m cProfile -m cmake --build build` | D | A | A |
| `python3 -m cProfile -m pytest --collect-only` | A | A | A |
| `python3 -m cProfile -m pytest --help` | A | A | A |
| `python3 -m cProfile tools/run_tests.py` | A | A | A |
| `python3 -m cProfile /tmp/safe.py` | A | A | A |
| `python3 -m cProfile --help tools/pegasus/exec_calibrate.py` | A | A | A |
| `python3 -m trace --report -f /tmp/counts tools/pegasus/exec_calibrate.py` | A | A | A |
| `python3 -m runpy tools/pegasus/exec_calibrate.py` | A | A | A |
| `python3 -m timeit tools/pegasus/exec_calibrate.py` | A | A | A |
| `python3 -m cProfile tools/pegasus/exec_calibrate.py` | D | A | A |
| `python3 -m pydoc tools/pegasus/collect_receipt.py` | D | A | A |

**深い入力**：`"python3 " + "-m cProfile " * N + tail`、site は LOGIN。すべて例外なし。

| N | tail | 結果 | 拒否理由 |
|---:|---|---|---|
| 1100 | `-m json.tool ; pytest -q` | D | `pytest による test 実行` |
| 1100 | `-m pytest -q` | D | baseline 重量対象 `pytest` |
| 1100 | `-m json.tool /tmp/a.json` | A | — |
| 300 | `-m json.tool ; pytest -q` | D | `pytest による test 実行` |

**一致対 7 組**：包み形＝`python3 -m cProfile `＋suffix、直接形＝`python3 `＋suffix。site は LOGIN。

| suffix | 包み形 | 直接形 |
|---|---|---|
| `-- -m pytest` | D | D |
| `/tmp/safe.py -mpytest` | D | D |
| `-- -W pytest` | D | D |
| `/tmp/safe.py` | A | A |
| `-m pytest --collect-only` | A | A |
| `-m json.tool /tmp/a.json` | A | A |
| `-m pytest -q` | D | D |

**sanctioned 早期許可との順序**：site は LOGIN。

| command | 結果 |
|---|---|
| `python3 -m cProfile tools/run_tests.py -m pytest -q` | D |
| `python3 -m profile -o /tmp/p tools/run_tests.py -m pytest -q` | D |

## 反実仮想

メモリ内の複製で入口を `if False and peel_executors:` に変更しました。

v1 §2 の **ALLOW → DENY 全10件が ALLOW に復帰**しました。変異 module を破棄し、通常 module で10件すべて DENY に戻ることを再確認しました。実ファイルの内容一致も確認済みです。

## 変異 anchor (M0〜M9)

以下は修正後の逐語 old 文字列です。期待は事前登録であり、M1 以外の変異実行結果ではありません。

**M0 — 798行、docstring のみ変更。SURVIVED 期待。**

```text
    各層で executor module token と program token を必ず消費し、rest は
```

**M1 — 1298行、入口を恒偽化。KILLED 期待。**

```python
    if peel_executors:
```

**M2／M6 — 847行。**

```python
    if kind == "module" and not _PYTHON_MODULE_RE.fullmatch(value):
```

M2 は `if kind == "module":` に変更して module 形を `None` に落とす。M6 は条件を恒偽化して検査を外す。ともに KILLED 期待。M6 は既存 test と冗長で、新規検出力には数えません。

**M3 — `_script_executor_program` 内808行、coverage 経路を落とす。KILLED 期待。**

```python
    parsed = _script_executor_arguments(module, args)
    if parsed is None:
```

条件へ `or module in {"coverage", "coverage.__main__"}` を追加する位置です。

**M4 — 1309行、`*rest` を除去。KILLED 期待。**

```python
                inner_seg = [inner_raw_head, "-m", value, *rest]
```

過剰拒否と二重 wrapper 素通しの **2 理由**。単独理由の証拠には数えません。

**M5 — 849行、script の場合だけ `None` を返す。KILLED 期待。**

```python
    return kind, value, rest
```

**M7 — 805行、multi-target 除外を恒偽化。KILLED 期待。**

```python
    if module in _MULTI_TARGET_EXECUTOR_MODULES:
```

既存 test が守る面で、新規検出力には数えません。

**M8 — 1298〜1318行の層剥き block 全体を移動。KILLED 期待。**

開始 anchor：

```python
    if peel_executors:
```

終了 anchor：

```python
            inner_raw_head, inner_head, inner_args = _heavy_head_and_args(inner_seg)
```

移動先は、次の sanctioned 早期許可 block の直後です。

```python
    if (not _provenance_script_borrow(head, args)
            and _is_sanctioned(raw_head, head, args, repo_root)):
        return None
```

識別入力は上記 `tools/run_tests.py -m pytest -q` の2形です。

**M9 — 1318行を `break` に置換し、1層で打切り。KILLED 期待。**

```python
            inner_raw_head, inner_head, inner_args = _heavy_head_and_args(inner_seg)
```

二重 wrapper と深い pytest 入力が検出対象です。

## 所見対応表 (closed / partial / regressed)

| 所見 | 状態 | 根拠 |
|---|---|---|
| A1：深い入れ子の RecursionError | closed | 反復化。1100層で後続 pytest 拒否・内側 pytest 拒否・軽量形 ALLOW を確認 |
| A2：script 形の期待値 | closed（実装・直呼び範囲） | v2 裁定どおり直接形の保守的判定を維持。7組すべて一致。恒久テスト追加は別単位 |

## 総括

修正と指定の直呼び検証を完了しました。worktree の変更は `hooks/guard_bash.py` のみです。docs・テスト・`guard_write.py` の編集、git add／commit／merge／checkout、pytest 実行はしていません。

完成版 SHA256：

```text
59798a82be2df76c17ee0ec75d659793a4c9adb053e07be8195a51cefdf0e532
```