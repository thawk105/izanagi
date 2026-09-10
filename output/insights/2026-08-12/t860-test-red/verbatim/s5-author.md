## 総括

- [orchestrator/tests/test_spool_fold.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/orchestrator/tests/test_spool_fold.py:2948) のみ変更しました。commit・docs・production の変更はありません。
- `_copy_real_canonical_family` は従来の固定 11 path、現在の `docs/archive/worklog-*.md` 318 files に加え、`tools/dev_waves/` の source/schema 15 filesを再帰的に byte-exact 複製します。生成物の `__pycache__` / `.pyc` は模型へ混入させません。現時点の合計は 344 files です。
- `_fixture_tools_imports` context manager を追加しました。入場時に既存の `dev_waves` / `dev_waves.*` 登録を退避・除去し、fixture 自身の `tools/` を `sys.path[0]` に置きます。`try/finally` により正常・例外経路とも `sys.path` の内容と既存 module object を復元し、区間内で新規登録された `dev_waves` 系 module も除去します。
- 指定された 4 test の fold 呼出しだけを context manager で囲みました。既存 assert、期待値、golden、実行条件は変更していません。

現行は、実 canonical fixture の 4 test が正しい golden 判定へ到達する前に、呼出し元 session の import 状態次第で `No module named 'dev_waves'` と fail-closed します。変更後は fixture 内の正しい import 閉包で fold を実行しますが、`spool_fold` の受理・拒否条件そのもの、および不正入力時の fail-closed は変わりません。

静的な波及確認では、`_copy_real_canonical_family` と新 context manager の caller は指定された同じ 4 test のみでした。他の test、共有 synthetic fixture、`tools/check_docs.py`、`tools/spool_fold.py`、その他 consumer には変更がありません。将来 `tools/dev_waves/` に source/schema fileが追加された場合のみ、この実 canonical fixture も追随します。

`git diff --check`、Python AST 構文解析、AST による caller 集合照合は成功しています。指示どおり pytest は実行しておらず、状態は「実装済み・未実走」です。

判断点は package 一式に実行時キャッシュを含めるかでした。忠実な source fixture と stale bytecode 回避を優先し、追跡対象となる source/schema はすべてコピーし、`__pycache__` / `.pyc` のみ除外しました。