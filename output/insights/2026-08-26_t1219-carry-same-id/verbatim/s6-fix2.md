## 修正した内容

[orchestrator/tests/test_check_docs.py:11175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11175)

- `needle` を分類用 `category_label` と carry 固有 `detail` に分離。
- carry finding は source path:line、task ID、target 番号、固有 detail で照合。
- `tools/check_docs.py` は変更していない。

## 検出力が落ちていない根拠

missing、none、empty の各ケースで、自分類のラベルと detail を個別に要求しています。さらに、他2分類のラベルと detail が findings に含まれないことも否定 assertion で固定しています。assertion の削除、緩和、skip 化はありません。

## 実走した検査

- `git diff --check -- orchestrator/tests/test_check_docs.py`: 成功
- 焦点テスト: 未実走
  - `tools/run_tests.py` 経由で試行したが、`qstat -Q` preflight が `rc=1`
  - dispatch infrastructure failure、child 未起動、runner `rc=16`

## 総括

指定テストだけを最小修正しました。  
3分類の相互区別はラベルと detail の両面で維持しています。  
production、docs、禁止指定されたテストは変更していません。  
commit、add、stash、checkout、reset、branch 操作は実行していません。