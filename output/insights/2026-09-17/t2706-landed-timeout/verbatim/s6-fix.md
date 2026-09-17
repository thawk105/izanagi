- `tools/check_branch_landed.py:38–40`：定数を **30.0 → 45.0 秒**へ変更。直前のコメント 2 行は `value-decision.md` と逐語一致を確認。他の製品コードは変更していません。
- `orchestrator/tests/test_check_branch_landed.py:1031,1079,1097,1105`：実例外の timeout 値を記録・検証する 4 行のみ追加。既存 test の期待値は変更していません。
- 指定ファイル全 node 対象の pytest は起動前に拒否されました。実行 0 件、成功・失敗とも未判定です。docs 編集・commit・git add はしていません。

## 総括

RB1・RA2 は実装済みです。
差分と指定コメントの一致を確認しました。
テストは未実走のため、親による計算ノードでの実走が必要です。

PreToolUse の `guard_bash` が、Pegasus ログインノードでの pytest 直接実行を禁止する規則により、指定コマンドを拒否しました。