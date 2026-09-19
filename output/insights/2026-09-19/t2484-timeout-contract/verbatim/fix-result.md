## 総括

**partial：実装済み・未実走です。** closedにはしていません。回帰の有無は未確認です。

- `orchestrator/tests/test_mutation_worktree.py`のみ変更（23行追加・1行削除、上限内）。
- 疑似dispatcherにimport guard、実dispatcherと同じ期限定数・walltime parserを追加しました。
- AST比較でCLI本体の不変、定数・parserの実体との一致、既存テスト・期待値の不変を確認。`git diff --check`も通過しました。

現状の正例2件はrc125でした。修正は従来期待rc0、正常実行・変異検出・receipt移設・resume・sidecarの意味を維持するものです。不正ledger・証拠束縛不一致の拒否処理は変更していません。

対象2nodeは`tools/run_tests.py`経由で起動しましたが、`qstat -Q preflight rc=1`、rc16、`child_started=false`で停止しました。**緑の実走nodeidはありません。M16も未実走**です。

影響先は同ファイルの共有fixtureが生成する`run_tests.py`／`dispatch_compute.py`と、実harness・worktree wrapperです。所有外変更はありません。テスト新設・改名なし。関連するT2337 parser同値、flaky登録node、duration ledger網羅率のmeta-testを特定しましたが、未実走です。

docs・stage・commit・子起動・追加レポート作成は行っていません。