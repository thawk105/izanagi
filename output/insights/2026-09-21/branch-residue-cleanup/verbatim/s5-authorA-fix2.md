## 変更一覧

- [tools/dev_wave_cleanup.py:313](/work/1/SFC/tanab/izanagi/.codex/worktrees/branch-residue-author-a/tools/dev_wave_cleanup.py:313): bundle argv を full branch refname に限定し、形式を検証。
- 同ファイル:1858・1947: positive 側を `proof.branch` に変更。detached は bundle を省略し、receipt に理由を記録。:19 に reflog 消失の説明を追加。
- [test_dev_wave_cleanup.py:562](/work/1/SFC/tanab/izanagi/.codex/worktrees/branch-residue-author-a/orchestrator/tests/test_dev_wave_cleanup.py:562): 所有 path 一致の detached 非祖先を撤去する正例を追加。
- 同ファイル:2442: argv 正例を更新し、bare SHA・不正 ref・`^` 欠落の拒否例を追加。

## 静的検査

- 所有2ファイルの `ast.parse`: 成功。
- `git diff --check`: 成功。
- pytest: 指示どおり未実走。

## 総括

実装済み・未実走です。変更は所有2ファイルのみです。
受理集合・専用 `-D`・処理順序・既存テストの期待値は維持しました。
commit・branch 操作・push は行っていません。