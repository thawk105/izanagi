## MF1 の原因と直し方

原因を実測で確認しました。`perf` の出力値を後段の `_tree_violation()` から除外した結果、既存 tree 防護が失われています。

修正案は、出力値を除外する前に既存の leaf・campaign tree・namespace marker・hooks subtree・ccbench 判定と発行主体判定へ通すものです。ただし `apply_patch` が自己防護に拒否されたため、未適用です。

## MF2 の原因と直し方

`_inside(path, "/")` が `path.startswith("//")` を評価するため、filesystem root を祖先として認識しません。

修正案は `tree == os.sep` の場合に絶対 path を内包すると判定するものです。これも未適用です。

## 反転検査 (変更前 vs fix 後)

fix 前の赤を実測しました。

- 20 ケースを変更前版と現行版へ投入
- `deny → allow`: 6 件
- 指定例 2 件を再現
- campaign tree、namespace marker、hooks subtree、ccbench の `perf -o` で退化を確認
- leaf、引数、redirect の既存拒否は維持
- 無関係な `perf` 3 形は allow のまま

fix を適用できなかったため、fix 後の反転 0 件検査は未実施です。

## 発行主体防護の歯の再確認

MF2 の fix 前挙動を直呼びで確認しました。

- `rm -rf /`: allow
- `rm -rf --no-preserve-root /`: allow
- `/` の移動・展開: allow
- `/tmp`、兄弟 prefix、別 job、別 worktree: allow

fix 後の redirect / 引数 / tree / 祖先 / glob / inode / canonical / lexical / fast path / fallback 再確認は未実施です。

## 波及可能性

静的な consumer は以下です。

- `.claude/settings.json`
- `.codex/hooks.json` → `hooks/codex_guard.sh`
- `tools/check_codex_hooks.py`
- `tools/codex_worker_launch.py`
- `orchestrator/tests/test_hooks.py`
- `orchestrator/tests/test_codex_hooks.py`
- `orchestrator/tests/test_codex_worker_launch.py`

## 総括

作業ツリーは clean のままです。現在の HEAD `dea46c20e` には A2 の hooks 自己防護が既に入り、許可された `apply_patch` が `hooks/guard_bash.py` を拒否しました。`guard_write.py` の編集・巻き戻しや別手段での書込みは行っていません。構文検査・fix 後検査・pytest・commit も未実施です。

再開には、親側で A1 commit `840f4e31a` 時点の編集可能な worktreeを用意し、MF1/MF2 fix を A2 より前に適用する必要があります。