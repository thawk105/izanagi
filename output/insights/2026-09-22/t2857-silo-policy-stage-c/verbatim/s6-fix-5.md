## 直した内容

- limit 側の変異・対照を `retry` に変更。conflict 側は `abort0` を維持。
- `target_exit` を維持し、retry を選ぶ理由をコメントに記載。
- 集約判定に、`focus/retry` と方策・workload が一致し、`limit_aborts > 0` である条件を追加。`judge` の再計算にも適用。
- 到達あり・なし、方策・workload 不一致、証拠欠落を確認するテストを追加。

## 確認の実測

- 指定2ファイルの `python3 -m py_compile`：終了コード 0。
- `git diff --check`：指摘なし。
- テスト・driver・build は未実行。

## 変えていないことの根拠

差分は指定2ファイルのみ。既存 assert は方策名の許可された追随以外変更なし。trace-timeout、対照の certified、必須集合の完全一致を維持しました。build sink・subprocess の行番号は変わらず、pin 更新は不要でした。docs 編集・git 書き込み操作は行っていません。

## 未了と疑問

テスト実行と計算ノードでの coverage 再測定が未了です。修正後の実測合格は未確認です。

## 総括

J1 は実装済み・未実走です。構文確認を通過し、変更は未コミットで親に引き渡せる状態です。