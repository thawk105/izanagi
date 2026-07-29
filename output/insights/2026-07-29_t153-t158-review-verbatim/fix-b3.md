変更 file:line: [orchestrator/tests/test_check_codex_output.py:103](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/orchestrator/tests/test_check_codex_output.py:103)

- fixture を非 NUL 本文と有効な `## 総括` 見出しで構成し、厳密に `10 * 1024 * 1024 + 1` bytes 化。
- docstring に20MB変異時は `rc=0` となり赤化することを明記。
- 実装定数の import なし。docs 編集・commit なし。

実行結果:

- 指定 pytest: `18 passed in 0.14s`
- V11単体: `1 passed in 0.09s`
  - nodeid: `orchestrator/tests/test_check_codex_output.py::test_read_limit_rejects_file_larger_than_ten_megabytes`
- 20MB変異注入: `rc=0` により V11 が赤化することを確認
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `git diff --check`: 問題なし

## 総括

V11 fixture をサイズ超過だけが失敗理由となる形へ単一理由化し、20MB上限変異を捕捉できる状態に修正しました。