## 変更の要約

`_validate_journal` に指定の docstring を追加し、binding は記録内の整合情報であり PBS job の外部認証ではないと明記しました。

差分は変更前 0 行 → 変更後 1 file・6 行追加・削除なしです。

## 挙動不変の根拠

差分は docstring の追加だけです。既存 comment、定数、分岐、reason / cause、detail 文字列、test は変更していません。

## 検査結果

- AST 検査：`AST_OK`、終了コード 0。
- `__doc__` 取得：追加全文を確認、終了コード 0。bytecode 書込みを抑止して実行。
- `git diff --check`：終了コード 0。
- pytest：指示どおり未実行。

## 総括

RA-2 / RB-3 の修正を完了しました。commit は作らず、差分を working tree に残しています。