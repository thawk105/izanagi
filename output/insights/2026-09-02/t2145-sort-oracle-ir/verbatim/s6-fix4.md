## 修正内容

- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix2/orchestrator/campaign/p3_s4_loop.py:241) から `preserve_indent` 引数と記述を完全撤去し、sort 再挿入を既定呼び出しへ戻しました。
- [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix2/orchestrator/tests/test_p3_s4_loop.py:1427) は byte 完全一致を維持しつつ、正準化一致と全行の harness indent を検査します。
- 指定された effect-scanner テスト、`docs/`、role adapter、権威集合などは禁止対象は変更していません。
- commit は作成していません。

## 検査

指定コマンドを間隔を置いて 3 回実行しました。

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_s4_loop.py orchestrator/tests/test_p3_s4_loop_sort.py orchestrator/tests/test_sort_swo_oracle.py -q -p no:randomly
```

全 3 走とも `qstat -Q preflight rc=1`、`child_started=false` による `rc=16` でした。テスト件数は取得不能です。

`git diff --check` は成功し、`preserve_indent` の残存参照はありません。

## 未実走・残赤

指定 3 ファイルはテスト本体が一度も起動せず、passed・failed・skipped 件数は取得不能です。実走による失敗 nodeid はありません。焦点 node の解消も未確認です。

## 総括

1. `preserve_indent` seam を撤去し、sort を indent 保持の正準再挿入へ戻しました。  
2. 指定検査は 3 回とも `rc=16` で、件数は取得不能です。  
3. 実走済みテストと確認済み残赤はなく、焦点 node は未検証です。  
4. 変更波及は `render_hole` と指定 G2 テストだけで、禁止対象への追加波及はありません。