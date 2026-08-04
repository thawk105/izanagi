[対象テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_pegasus_thirdparty_fetch.py:570) を `_fetch()` から実際の変異対象 `_hydrate()` 経路へ変更しました。正式 destination の rollback 状態を例外内容より先に検査します。共有 fixture・他テスト・実装コードは変更していません。

M15 注入時は `assert not destination.exists()`（606行目）が、destination 残存により失敗します。

確認済み: `git diff --check`、`python3 -m py_compile` は rc=0。`pegasus02` はログインノードのため pytest・変異本走は実行していません。commit/add/stash も未実行です。

## 総括

対象テストファイル1本のみ変更しました。  
M15 の消失挙動である rollback を状態として直接検出します。