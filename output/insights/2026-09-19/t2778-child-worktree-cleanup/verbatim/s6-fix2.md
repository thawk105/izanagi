## 総括

fixture 修正を完了しました。変更は [test_dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2778-author/orchestrator/tests/test_dev_wave_cleanup.py:417) の417–427行・431行のみです。main の primary store を作り、子と同じ pin に固定しました。実装・他 node・期待値は変更していません。

`tempfile.mkdtemp()` による直接呼出し結果：

| parameter | 結果 |
|---|---|
| clean | PASS：`removed` |
| dirty | PASS：rc20／`backup-precheck` |
| ignored | PASS：rc20／`backup-precheck` |
| reflog | PASS：rc20／`backup-precheck` |
| pin-mismatch | PASS：rc20／`backup-precheck` |
| local-only-pin | PASS：rc20／`backup-precheck` |

反実仮想では、メモリ上で A2 だけを無効化すると `local-only-pin` が `removed` となり、拒否を期待するテストが失敗しました（変異 KILLED）。A2 は復元済みで、実装ファイルは変更していません。

`git diff --check` は成功。pytest・正式 mutation harness・全体 checker は未実走です。作業 repo の commit・stage・stash・checkout、報告ファイル作成は行っていません。