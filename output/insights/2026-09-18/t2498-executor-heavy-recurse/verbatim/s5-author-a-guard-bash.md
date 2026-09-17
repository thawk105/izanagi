## 現行版への同期

[hooks/guard_bash.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2498-guard-impl/hooks/guard_bash.py) を現行版に同期し、実装前に `cmp` 完全一致を確認しました。

- base blob: `3b5f6b65018b130702060b9aabc780ff06f1bc89`
- 完成版 SHA256: `619bcf48ff2b7ea4ec6c526e889f8d3ab83efc8d59d8434193a4900d5e862f48`

追加・変更箇所だけをメモリ上で取り除き、現行版と全 byte が一致することも確認済みです。

## 実装した内容

- `_script_executor_arguments` で既存 option 表の選択を共有。
- `_script_executor_program` で内側の `(kind, value, rest)` を抽出。
- shell 再帰直後・sanctioned 早期許可前に、同じ `raw_head` を使う再帰を追加。
- module 名検証、multi-target 除外、help・report・coverage 副命令の境界を実装。
- 再帰の深さ制限なし。密着形では生 token 数が増えるため、docstring は**正規形の token 数が減る**根拠を記載。

既存 option 表への追加はありません。`_script_executor_targets` は初期部分の共通化だけで、以降の処理は不変です。

## 実測 (decide 直呼び、§2 全行の表)

`repo_root` は指定 worktree の絶対パス。以下は `PEGASUS_LOGIN`、A＝ALLOW、D＝DENY です。

| コマンド | 現行 | 修正後 |
|---|---|---|
| `python3 -m pytest -q` | D | D |
| `python3 -m cProfile -m pytest -q` | A | D |
| `python3 -mcProfile -mpytest -q` | A | D |
| `python3 -m cProfile -o /tmp/p.out -m pytest -q orchestrator/tests/test_hooks.py` | A | D |
| `python3 -m profile -m pytest -q` | A | D |
| `python3 -m coverage run -m pytest -q` | A | D |
| `python3 -m pdb -m pytest -q` | A | D |
| `python3 -m trace --trace --module pytest -q` | A | D |
| `python3 -m runpy pytest -q` | A | D |
| `python3 -m cProfile -m cProfile -m pytest -q` | A | D |
| `python3 -m cProfile -m cmake --build build` | A | D |
| `python3 -m cProfile -m pytest --collect-only` | A | A |
| `python3 -m cProfile -m pytest --help` | A | A |
| `python3 -m cProfile tools/run_tests.py` | A | A |
| `python3 -m cProfile /tmp/safe.py` | A | A |
| `python3 -m cProfile --help tools/pegasus/exec_calibrate.py` | A | A |
| `python3 -m trace --report -f /tmp/counts tools/pegasus/exec_calibrate.py` | A | A |
| `python3 -m runpy tools/pegasus/exec_calibrate.py` | A | A |
| `python3 -m timeit tools/pegasus/exec_calibrate.py` | A | A |
| `python3 -m cProfile tools/pegasus/exec_calibrate.py` | D | D |
| `python3 -m pydoc tools/pegasus/collect_receipt.py` | D | D |

非 refusing site は、指示された代表3形を両 site で確認しました。

| コマンド | OTHER 現行→修正後 | PEGASUS_COMPUTE 現行→修正後 |
|---|---|---|
| `python3 -m cProfile -m pytest -q` | A→A | A→A |
| `python3 -m coverage run -m pytest -q` | A→A | A→A |
| `python3 -m cProfile -m cProfile -m pytest -q` | A→A | A→A |

追加確認結果：

- `compile()` による構文検査、`git diff --check`：成功。
- 既存対象抽出の現行比較：5,302件一致。
- 合成 round-trip：2,198件一致。
- 現行テストから抽出した静的文字列245件：判定変更0件、DENY→ALLOW 0件。動的生成コマンドを網羅する検査ではありません。
- 綴り差・20重 wrapper 等の追加15形：確認済み。

**補足:** §4で対象から除外された `python3 -m cProfile -o /tmp/x -- -m pytest` は A→D になります。抽出は script `-m`、合成は `python3 -- -m pytest` と正しく round-trip しますが、既存 residual 判定が `pytest` を拒否します。この追加拒否まで「不変」とは報告できません。別の判定変更は加えていません。

pytest は実行していません。検証コードは [/tmp/t2498_guard_probe.py](/tmp/t2498_guard_probe.py) にあります。

## 反実仮想

追加再帰への入口を、メモリ上の複製で `if False and invocation is not None:` に変更しました。

§2の A→D **全10件が A に復帰**しました。復帰しない行はありません。実ファイルには変異を書き込まず、検証後も内容一致を確認しています。

## 変異 anchor (M0〜M8)

行番号は完成版。old 文字列は逐語です。

| ID | 行 | old 文字列 | 変異・確認 |
|---|---:|---|---|
| M0 | 798 | `    再帰は executor 一層を必ず消費する。密着 option を分離した正規形では` | docstring のみ変更。等価対照 |
| M1 | 1298 | `    if invocation is not None:` | この再帰入口を恒偽化。全10件で効力確認 |
| M2 | 847 | `    if kind == "module" and not _PYTHON_MODULE_RE.fullmatch(value):` | `if kind == "module":` に変更。module 形が A に反転 |
| M3 | 808 | `    if parsed is None:` | **`_script_executor_program` 内限定**で coverage 条件を追加し `None` に落とす。coverage 負例が A に反転 |
| M4 | 1303 | `                inner_seg = [raw_head, "-m", value, *rest]` | `*rest` を除去。collect-only 正例が D に反転 |
| M5 | 849 | `    return kind, value, rest` | script の場合だけ `None`。`cProfile pytest` が A に反転 |
| M6 | 847 | `    if kind == "module" and not _PYTHON_MODULE_RE.fullmatch(value):` | 条件を恒偽化。不正 runpy module の正例が D に反転 |
| M7 | 805 | `    if module in _MULTI_TARGET_EXECUTOR_MODULES:` | 除外を恒偽化。下記の単一理由で識別可能 |
| M8 | 1297 | `    invocation = _python_module_invocation(head, args)` | 1297〜1309行の再帰 block 全体を sanctioned 早期許可後へ移動 |

M7 は **非等価**です。`python3 -m pydoc -w tools/pegasus/exec_calibrate.py` が A→D に反転しました。既存 `test_bash_login_pydoc_server_and_write_modes_do_not_execute_positionals` の「非実行 positional を実行対象扱いした」という一つの赤理由で登録できます。

M8 は静的245文字列＋§2＋追加15形では差分0件。**この corpus に対する SURVIVED 対照**が適切です。全入力での等価性は主張しません。

以上は直呼びによる変異確認であり、pytest matrix の KILLED 実測ではありません。

## 波及可能性

- `_script_executor_targets` の既存呼び出し元は `_script_targets`。そこから admission、sanctioned、互換 `_script_target` に波及します。
- `decide()` の既存 pin は、executor admission、出力先上書き拒否、runpy 不正 module、help/report、pydoc 非実行 mode、直接 pytest、provenance、shell 再帰が関連します。
- `_mk_fixture_repo` は模擬 hooks を作成しますが、今回 fixture は変更していません。module 実体解決は各テストの repo_root に依存します。
- `test_codex_hooks.py` と `test_codex_worker_launch.py` は guard の配置・内容・信頼検査に依存します。guard 内容変更に伴う統合確認が必要です。
- `test_plain_runner_coverage` と、古い worktree には存在しない `test_ccbench_spawn_sites.py` の実測は親側に残ります。

## 総括

現行版への完全同期と再帰実装を完了しました。§2は全件期待どおりで、既存拒否の緩和は確認されていません。除外 script 形の追加拒否は上記のとおり明示しました。

worktree の変更は `hooks/guard_bash.py` のみです。docs・テスト・`guard_write.py` は未変更。git add／commit／merge／checkout、pytest は実行していません。