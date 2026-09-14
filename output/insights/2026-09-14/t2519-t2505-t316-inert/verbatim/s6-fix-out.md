## 変更した内容

- [probe](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2519-impl/tools/pegasus/probes/t316_sandbox_backend_probe.py:1967) 1967–1985 行：診断失敗時も従来の `RuntimeError` を送出し、出力障害は `__cause__` に保持。
- [test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2519-impl/orchestrator/tests/test_t316_sandbox_probe.py:89) 89–137 行：実 CMake・実 gate を通し、stderr の `write()` が `OSError`・`ValueError`・`RuntimeError` を投げる３ケースを追加。拒否文面の完全一致と実 configure の witness を検査します。

## 例外捕捉の範囲と理由

診断処理だけで `Exception` を捕捉します。任意の出力障害に対応しつつ、`KeyboardInterrupt`・`SystemExit` 等の `BaseException` 直系は捕捉しません。障害は例外連鎖に残すため、完全には握り潰しません。

## 受理・拒否挙動の変化

受理集合・通常の拒否・拒否メッセージは不変です。診断障害時だけ、出力例外への置換を防ぎます。受理経路・gate 本体・receipt schema は変更していません。

## nit への対応

両方据え置きました。既存テストの期待値変更禁止を優先しています。

## 実走結果

試したコマンド：

```bash
python3 tools/run_tests.py orchestrator/tests/test_t316_sandbox_probe.py orchestrator/tests/test_skip_classification.py orchestrator/tests/test_pytest_collection_config.py
```

**rc=16、child_started=false。実走した nodeid はありません。** 構造・収集関連の検査も未実走です。

runner が内部で禁止対象の `qstat -Q` preflight を試みました。起動前の確認不足です。以後の起動は停止しました。

`git diff --check` は rc=0 でした。

## 波及可能性の静的列挙

- `_execute_ccbench_build`：拒否による build 停止を維持。
- S6 エラー収集：`_error()` は型と文面だけを記録するため、診断障害時も条件関門の拒否情報を保持。
- traceback consumer：出力障害が cause として追加されます。
- 共有 fixture：原本は変更せず、一時コピーだけに CMake の失敗を設定。
- consumer test：既存期待値は不変。追加テストの stderr 差替えは context 終了時に復元。

## 総括

**実装済み・未実走です。closed とは申告しません。** ソース変更は指定の２ファイルのみで、docs 編集・commit・push は行っていません。