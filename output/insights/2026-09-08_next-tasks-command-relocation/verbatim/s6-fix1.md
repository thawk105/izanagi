4箇所の期待値を更新しました。

- `_known_violation_group_stdout(53, 2)` → `(53, 3)`
- 旧 literal の残存なし
- standalone の `55` や他の post-baseline 件数 pin はなし
- baseline の53件 oracle と明示的な既知 commit 部分集合は見つかりましたが、意図どおり変更していません
- 指定のレジストリ読取は例外なく完了し、`len(r)` は `55`
- `git diff --check`: 問題なし
- `git diff --stat`: `1 file changed, 4 insertions(+), 4 deletions(-)`

## 総括

変更ファイルは [test_check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/orchestrator/tests/test_check_ai_provenance.py:3455) のみ、4行を置換しました。pytest は契約どおり起動しておらず、実装済み・未実走です。