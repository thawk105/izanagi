## 監査結果

- base 19,745、wave 19,948、main 19,761、merged 19,964 entry。
- merged は両親の完全な和集合。欠落、値相違、余分な entry は各 0。
- wave の追加 203、main の追加 16・変更 0。集合の重複は 0。
- 親間の値不一致は 0。`schema_version=1`、`unit=seconds`、`nodeid_count=19,964` も正常。
- 両親が共に触った file は台帳のみでした。

## 起草結果

[docs/merge-message-gitbatch.txt](/work/1/SFC/tanab/izanagi/.codex/worktrees/gitbatch-author/docs/merge-message-gitbatch.txt) を新規作成しました。実装 file、git、commit、merge、checkout は変更していません。

## 総括

合成は正しく、両側の追加を保持しています。  
指定形式の merge message を起草済みです。  
pytest は依頼どおり実行していません。