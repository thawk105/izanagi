## 変更

- [test_growth_test_holds_contract.py:1092](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:1092)
  - subprocess 環境へ repo root を `PYTHONPATH` の先頭に追加できる `repo_on_pythonpath` オプションを追加。
  - 親環境の既存 `PYTHONPATH` は保持。
- [test_growth_test_holds_contract.py:1548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:1548)
  - 新規 synthetic subprocess test 3 件すべてで同オプションを有効化。
  - 拒否 token、非ゼロ終了、`BODY_RAN` 不在などの既存期待値は変更していない。

## 検証

- 対象 2 ファイルの `compile(..., "exec")` と AST parse: 成功。
- 追加 3 test が各 1 回の `_run_subprocess` 呼出で `repo_on_pythonpath=True` を指定することを AST で確認。
- registry: `count=59`。
- `key_sha256=30e646a80e6dfc7c04ec2e249462789ac7cb10f1afaa6979491a3312d5d6508c`。
- held file: 13。
- `git diff --check`: 成功。
- 指示どおり pytest は未実走。緑・passed・closed は申告しない。

## 波及

`tmp_path` に synthetic module を作る subprocess test を全件確認した。今回追加された call-only 3 件はすべて repo import path を明示した。既存の opt-in test は `python -m pytest` と `cwd=ROOT` の組み合わせであり、絶対パスの script 直接実行とは異なる。参考指定された plain pytest delegating testには触れていない。

今回の fix では contract test 以外を編集していない。docs、tools、登録済み held file、既存の未追跡 insight は未変更で、commit も作成していない。

## 総括

直接 `__main__` 実行の性質を維持したまま repo import path を明示した。  
module import 失敗ではなく、本来の call-only 拒否を検査できる形に修正した。  
追加された synthetic subprocess test 3 件を同じ条件へ統一した。  
registry 59 件、digest、held file 13 は不変。  
静的確認済み、pytest 未実走。