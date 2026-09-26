## 変更

J2 のみ修正しました。`verifier_digest` の `anomaly_count` を、返された witness 配列の件数を表す `witness_count` に改名し、全 cycle 数は `total_cycles` のまま維持しました。変更は指定の 2 ファイルだけです。commit はしていません。

## 確認の実走

`py_compile`、該当テスト関数の直接呼び出し、`git diff --check` はすべて成功しました。pytest は未実走です。

## 総括

J2 の改名を完了しました。J1 と他の挙動は変更していません。