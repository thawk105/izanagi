指定4ファイルへ局所合成し、[author-result.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2515-recovery-author/author-result.md)へ記録しました。

- exact受理集合を `{5,20,50,80,95}` へ拡張
- smoke済み`CALIBRATE_PYTHON`を条件関門へ使用
- T-2535/T-2536の既存要件を維持
- 親の`tools/pegasus/README.md`は未編集
- `check_codex_agents.py`、`check_docs.py`、`git diff --check`は成功
- pytestは2回とも`qstat -Q`によるdispatch失敗で未起動

状態は「実装済み・未実走」です。Git操作や性能測定は実施していません。