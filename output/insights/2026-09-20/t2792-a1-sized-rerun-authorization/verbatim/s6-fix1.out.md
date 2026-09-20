## 所見への対応

closed は修正と静的確認の完了を示します。実走確認は未完了です。

| 所見 | 状態 | 対応 |
|---|---|---|
| MF1 | closed | helper 修正後、grep と AST で sink を7545行と確認。台帳2箇所を7428→7545へ更新 |
| B-N1 | closed | helper を digest field 除去＋canonical hash 計算だけに縮小。reader の検査は保存 |
| B-N2 | closed | digest 済み正常 JSON に同値の `study_id` を重複挿入。期待 message は維持 |
| A の item case | closed | `item-float`／`2.0` に変更。既存 `_rerun_save` で digest を再計算 |

## 検査結果

- 指定3テストファイルの dispatch を試行。qstat preflight 失敗で **rc=16、`child_started=false`**。pytest 未起動、nodeid 範囲・passed／failed／skipped の集計なし。
- 指定4ファイルの AST parse、`git diff --check` は成功。
- driver／paired test／job_contract を静的確認。job_contract は HEAD と同一 bytes。
- M1〜M14 の anchor は **bytes 変更なし**。`grep -Fxc` の HEAD／修正後件数は、M11 が2／2、M14 が4／4、その他は各1／1。M1 の後続 `return None` も保存。
- M1〜M14 の1理由性は静的に維持。M14 は指定どおり `"b" * 40`。変異本走は未実施。
- lineno 2箇所以外の期待値変更なし。producer namespace `[record]` も保存。

## 総括

**実装済み・未実走です。** 変更は許可された3ファイル、計 +8／−11行。docs 編集・commit はありません。失敗した dispatch の一時生成物は除去済みです。

親による関連テストの実走と、commit 後の non-touch 検査が残ります。