## 総括

1. 対応表

   - module collection 時の `ec.authorize()`：削除
   - function-scope の autouse fixture：各 test 実行前に current receipt と contract を再取得
   - `_AUTHORIZATION` / `_AUTH_CONTRACT`：同一 receipt から毎 test 更新
   - production・期待値・`/tmp/.git` 関連：変更なし

2. 変更ファイルと行数

   - [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_campaign.py:83)
   - 今回分：+10 / -2
   - HEAD 比：+12 / -2（既存の `pytest` import 差分を含む）
   - `conftest.py`、production、docs は未変更。commit なし。

3. 走らせた検査と結果

   - AST 全 nodeid 走査：262 test、全件一意
   - authority 参照走査：196 load、collection 時 0
   - `ec.authorize()` 走査：7 call、collection 時 0
   - import 中の `authorize()` 禁止検査：成功、呼出し 0
   - cache 再初期化後の fixture refresh：成功
   - `py_compile`：成功
   - pyflakes：未定義名・未 import・fixture 未解決なし。既存の unused 警告4件のみ
   - `git diff --check`：成功
   - `check_codex_agents.py`：成功
   - `check_docs.py`：成功

4. 未実走・未達

   - pytest は未実走です。
   - 全 file collection と代表 nodeid の双方を `tools/run_tests.py` 経由で試しましたが、実行前に `qstat -Q preflight rc=1` で停止しました。緑は主張しません。
   - `/tmp/.git` 起因の5件には触れていません。

5. 親への申し送り

   - 計算ノードで `orchestrator/tests/test_campaign.py` 全体、または指定3ファイルの受入再走をお願いします。
   - 既存の `test_p3_s4_loop_trigger_gating.py`／`test_screening_driver.py` 差分は保持しています。