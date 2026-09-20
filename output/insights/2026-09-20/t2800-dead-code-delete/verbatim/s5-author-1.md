## 変更 (git status --porcelain と git diff --cached --stat の逐語)

両コマンドとも出力なし。変更はありません。

`git rm --` は rc=128 で失敗しました。

```text
fatal: Unable to create '/work/1/SFC/tanab/izanagi/.git/worktrees/t2800-unit-delete/index.lock': Read-only file system
```

## 実走

未実装・未実走。Git index の書込みが拒否されたため、削除・4行追随・静的検査・pytest は実施していません。

## 所有外への波及 (grep の結果)

README の指定3 test に対する検索結果：

```text
138:- test_insights_date_layout.py
```

残る2 test は該当なし。削除後の全域参照検索は未実施です。

## 親への申し送り

この環境では共通 Git 管理領域が読取り専用です。上記 `index.lock` を作成できる環境で再実行が必要です。

親が削除すべき README 行は138行目の `- test_insights_date_layout.py`。README は変更していません。

## 総括

13 file 削除・4行追随は未完了です。  
`git rm` が Git index の書込み制限で失敗しました。  
scope 内外とも変更なし、commit なし、実走なしです。