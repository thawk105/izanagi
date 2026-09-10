対象 fixture の修正は完了しました。ただし対象 pytest は基盤エラーで未実走のため、判定は `partial` です。

| 所見 | 対応 | 根拠 |
|---|---|---|
| 下位行 drift が identity 比較で先に拒否される | partial（実装済み・未実走） | 複数行 helper を追加し、drift 後の実出力を 2 行完全一致で assert |

変更箇所:

- [_write_multiline_tool](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_buildcache_v2.py:152): 各行を別々の引数として `printf '%s\n'` に渡します。
- [対象テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_buildcache_v2.py:430): stable/changed の双方で先頭引数を `"cc version A"` に固定し、changed 側の実出力が正確に2行であることも確認します。
- `match="version 全文"` は維持しています。
- helper 単体 probe、`py_compile`、`git diff --check` は成功しました。
- 対象 pytest は `tools/run_tests.py` が `qstat -Q preflight rc=1`、終了コード16となったため未実走です。
- docs、production、既存 `_write_tool`、既存呼び出し側は編集していません。commit も作成していません。

## 総括

- 対応: partial（実装済み・対象 pytest 未実走）
- helper: `_write_multiline_tool`。各行を `printf` の独立引数として出力
- 先頭行保証: stable/changed とも `"cc version A"`、changed 実出力も完全一致 assert
- `match="version 全文"` 維持: yes
- 既存呼び出し側への波及: なし