## 変更した assertion

- 注入断片の逐語 bytes `b'{"unterminated"'` が台帳にないことを検査。
- 台帳が改行で終わることを追加。
- 再読後の `fragment_discarded is False` を維持。
- history が厳密に 3 件で、1 件目、修復 event、2 件目の順であることを検査。
- 修復 event の `attempt_id is None`、issue code が `IO_ERROR` であることを検査。

## 検査が強くなったことの説明

修復 event の文言に含まれる単語ではなく、実際に注入した断片の不在を検査します。さらに改行終端、event 数、順序、各 rejection の内容、修復 event の内容まで確認するため、既存検査を弱めていません。

## 実走の有無

焦点テストの起動を試みましたが、Pegasus の `qstat -Q` preflight が失敗し、rc=16、`child_started=false` でした。pytest は開始されていません。

**実装済み・未実走**です。`git diff --check` は通過しています。

## 契約から外れた点

ありません。対象テスト関数以外、production code、docs、他のテストは変更していません。commit、add、merge、rebase、push も実行していません。

## 総括

指定された assertion 修正を実装しました。  
変更は対象ファイルの対象テスト関数内だけです。  
実測は dispatch infrastructure failure のため親での実施が必要です。