M7 を検出する回帰テストを追加しました。docs・実装・commit は変更していません。

## 総括

- 変更ファイル: [test_claude_session_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/tests/test_claude_session_ledger.py:345)
  - `root=2 / sidechain=1 / max_files=2` の固定 fixture を追加。
  - JSON の `file_allocation` を `root_selected=1 / sidechain_selected=1` で厳密比較。
  - 既定テキストの配分行 `1/1 (基準枠 1/1; 未使用枠は再配分)` も完全一致で確認。
- 追加 node:
  - `test_reserved_balanced_quota_precedes_reassignment_when_candidates_compete`
  - M7 では配分が `2/0` になるため、JSON 配分・集計値・テキスト配分の期待に反して KILLED になります。
- 実装側: [claude_session_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/claude_session_ledger.py:226) は変更なし。現行ロジックは予約枠を再配分より先に適用しており正しいためです。
- 検査:
  - `git diff --check`: 成功
  - `python3 -m py_compile` 対象2ファイル: 成功
  - `python3 tools/check_codex_agents.py`: 成功
  - `python3 tools/check_docs.py`: 成功
  - pytest、既存33テスト、meta-test、M7再走: `pegasus02` ログインノードのため未実走。実装済み・未実走です。
- 波及可能性:
  - production の受理集合・JSON・テキスト出力は不変。
  - `_discover_paths` 経由の CLI 配分を新規テストが固定します。
  - 共有 helper や既存 fixture、既存テスト期待値は変更していません。
  - 変更はテスト1ファイルの64行追加のみで、docs 編集・commit はありません。