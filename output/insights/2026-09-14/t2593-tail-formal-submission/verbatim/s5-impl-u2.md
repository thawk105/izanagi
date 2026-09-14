## 実装内容

所有3ファイルに限定して実装しました。

- 新種別の入力検査を scratch・出力作成前に追加。
- 指定どおりの新 driver argv と stage を追加。
- 8種類の commit と execution receipt を確認する finalizer 分岐を追加。
- 新規テスト9関数・69ケースを記述。既存テストは回数2→3と理由コメントだけ変更。

旧3系列の受理条件・呼出し列・完走条件は維持しています。commit・Git操作による状態変更はしていません。

## 検証結果

**実装済み・未実走です。closed とは申告しません。**

`tools/run_tests.py` で次を指定しましたが、`qstat -Q` preflight が失敗しました。rc=16、`child_started=false`、実走 nodeid **0件**です。

- `orchestrator/tests/test_b10_backoff_grid_job.py`
- `orchestrator/tests/test_plain_runner_coverage.py` — 検索で発見した自走 harness の meta-test

Python AST parse と `git diff --check` は成功しました。既存テスト・変異検査は未実走です。Bash DEBUG trace の表記に依存する順序検査、shell断片の到達性、finalizer全ケースは実行確認が残っています。

runner が生成した診断ファイルは `/tmp/t2593-u2-dispatch-69400c139cc934bfefd67f1d669f8d08` へ移しました。

## 所有外への波及

- caller：別担当の submit script に新2環境変数の転送が必要です。job変更に伴い script SHA も変わります。
- 共有 fixture：変更なし。新規 fixture は新テスト内に閉じています。
- consumer test：既存 sweep の逐語 pin、formal driver のCLI・成果物契約、hooks の登録検査が関連します。統合実走は未確認です。
- 必読ファイルはすべて読めました。追加検索の一部 glob・推測パスは存在しませんでした。

`bash -n` も `guard_bash` により、対象が dispatch-required のため拒否されました。

## 総括

- **実装した内容：** 親裁定 §4 の #2・#5・#6 を実装。docs・driver・caller は未編集です。
- **実走したもの：** テスト0件。新規69ケース、meta-test、既存関連テスト、変異検査は未実走です。
- **裁定との差異：** 実装上の意図的な差異はありません。実行環境の拒否により、要求された緑・変異の赤は確認できていません。