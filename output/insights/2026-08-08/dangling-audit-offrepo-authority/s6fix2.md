## 総括

1. [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/orchestrator/tests/test_check_docs.py:318) の `_SYNTHETIC_CLEANUP_COMMAND` 本文だけを現行実ファイルと同期しました。期待値・assert・他ファイルは変更していません。
2. AST から再計算した SHA-256 は `2f97cc2b632bcc180010bdf8f95d5328aacf4a6c44b9043e82bb042d9f4bc440`。実ファイル、fixture、既存期待値の3者が完全一致し、byte 長も双方 `3987` でした。
3. 検査結果:
   - AST 解析・byte 比較・SHA-256 再計算: 成功
   - `python3 tools/check_docs.py`: `check_docs: 違反なし`
   - `git diff --check`: 成功
   - 指定2ファイルのテスト: dispatch infrastructure の `qstat -Q` preflight が rc=16 で失敗し、テスト本体は未実走

実装済み・未実走です。commit は作成していません。