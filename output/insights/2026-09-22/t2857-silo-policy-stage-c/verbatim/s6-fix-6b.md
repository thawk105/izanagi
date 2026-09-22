## 直した内容

指定テストだけを変更しました。

- build 数：`assert len(builds) == 23` を case 表から計算する式へ変更。現在は負例6＋focus 4＋非共有対照4＋変異9＋共有TRACE=0の1＝24件。数え方を1行コメントに記載し、24は固定していません。
- patch：両出口で同じ patch を期待する assert を、conflict は `broken-silo-policy-no-prefix-unlock.patch`、limit は `broken-silo-policy-no-prefix-unlock-limit.patch` を期待する形へ変更。両者が異なることの assert も追加しました。

対照の観測共有、出口別の case・方策・target_exit、合格判定の既存 assert は維持しました。

## 確認の実測

- `python3 -m py_compile`：終了コード0。キャッシュは `/tmp` 配下へ出力。
- `git diff --check`：終了コード0。
- 差分確認：指定ファイルの指定テスト内だけの変更。
- pytest・build は未実行。docs 編集、index・履歴への書き込みなし。

## 総括

承認された期待値2点の追随を完了しました。構文確認は成功し、テストの動的合格は未確認です。