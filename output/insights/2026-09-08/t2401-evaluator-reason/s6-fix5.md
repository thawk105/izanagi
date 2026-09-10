## 直した内容

2 件の子 process で `P.main()` の返り値を受け取り、一時ファイルへ記録してから `SystemExit(rc)` するよう修正しました。

テスト側では記録ファイルの実在と内容 `"1"` を追加検査しています。既存の stdout・returncode・stderr assertion は維持しました。

## guard を狭めると落ちることの実測

- `except ZeroDivisionError`、harness rc=1
  - `test_main_keeps_stdout_and_exit_value_when_stderr_write_raises_oserror`
  - `test_main_keeps_stdout_and_exit_value_when_stderr_write_raises_value_error`
- `except OSError`、harness rc=1
  - `test_main_keeps_stdout_and_exit_value_when_stderr_write_raises_value_error`

いずれも返り値記録ファイルが存在しない assertion で失敗しました。

## production を元に戻したことの確認

`git diff -- orchestrator/campaign/s8c_preregistration.py` は出力なしでした。production の一時変更は残っていません。

`git diff --check` も rc=0 です。

## 実走した nodeid と結果

`PYTHONPATH=. python3 orchestrator/tests/test_s8c_cli_entrypoints.py`

- 最終結果: rc=0、20 passed
- 上記 2 nodeid を含むファイル全体を自走 harness で実行しました。

## 未了・懸念

なし。

## 総括

最終差分は `orchestrator/tests/test_s8c_cli_entrypoints.py` のみです。guard が働かず `main()` から例外が漏れた場合を、返り値記録の欠落として確実に検出します。commit、add、push は行っていません。