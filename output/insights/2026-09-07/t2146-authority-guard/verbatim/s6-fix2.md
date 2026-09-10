## F1 の直し方

[test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1196) を修正しました。

- `walk.call_args_list` の root を `realpath` で正規化し、`Counter` で個別検査。
- `guard_write`: `{hooks root: 1}`、総数 1。
- `guard_bash`: `{hooks root: 1, authority root: 1}`、総数 2。
- テストが守る性質を docstring に明記。

## F2 で足したテスト

- `perf`: 3 option 形 × authority、末端、official/exploration campaign、namespace、hooks、ccbench を拒否。`/tmp` は許可。
- builder: 既存 build-variants は許可、authority 配下は拒否。
- fallback: 両 guard で exact authority は rc=2、`-copy`／`2` 兄弟は rc=0。
- filesystem root: `rm -rf /` 系を拒否し、`/tmp`、兄弟、別 job dir、別 worktreeを許可。

## 直接呼び出しと反実仮想の実測

`py_compile`: rc=0。

module import 後、以下の6関数を直接呼び出してすべて PASS:

- `test_t956_hardlink_inode_index_is_built_once_per_decide`
- `test_t2146_guard_bash_perf_output_keeps_all_protected_trees_denied`
- `test_t2146_guard_bash_builder_exception_excludes_authority_tree`
- `test_t2146_guard_bash_filesystem_root_ancestor_and_siblings`
- `test_t2146_both_guard_mains_fail_closed_on_authority_internal_errors`
- `test_t2146_both_guard_error_fallbacks_allow_authority_siblings`

runtime monkeypatch による反実仮想はすべて期待どおり AssertionError になりました。

- F1: `{hooks: 2, authority: 0}` は総数2でも赤化。
- F2-1: perf の既存 tree 判定除去で WAL ケースが赤化。
- builder の authority 分離除去、fallback の部分文字列化、filesystem-root 特例除去も赤化。
- 生き残った変異はありません。

pytest は指示どおり未実走です。

## メタテストの被覆

追加・変更した5関数が `test_` discovery 集合に含まれることを introspection で確認しました。`_run()` が既存の `orchestrator/tests/test_hooks.py` 全体を pytest に渡すことも、`pytest.main` を mock して確認済みです。新しい test file は増やしていません。

`git diff --check` も rc=0です。

## 波及可能性

静的な波及先は次のとおりです。

- production consumer: `guard_bash.decide()` の perf、builder、祖先判定と両 guard の `main()` fallback。
- 共有 fixture/helper: `_mk_fixture_repo`、`_mk_t956_aliases`、`_patch`、`_guard_main`、`_t2146_assert_denied`。
- `os.walk`／`decide` の monkeypatch は context manager で復元され、他テストへ状態を残しません。
- production signature、hooks、docs、他の既存期待値には変更ありません。

## 総括

F1/F2 は実装済み・pytest未実走です。変更は `orchestrator/tests/test_hooks.py` だけで、`hooks/`・docs は未変更です。`git add`、`git commit`、`git merge` は実行していません。