# 修正結果

許可されたテスト 2 ファイルだけを修正しました。

- `test_p3_s4_loop.py`: perf preflight 代用を `(None, True)` に変更しました。実 `pipeline.evaluate` が許容する receipt なし・`use_perf=True` の経路へ進みます。候補側の初回だけ意図的に例外を発生させる条件を維持し、その時点が候補 checkout 内かつ claim 取得後である assert を追加しました。stock 側は正常な戻り値を受け取ります。
- `test_p3_s4_loop_job_contract.py`: `fixture` pin を fixture 分岐内の receipt 引数に限定しました。`fixture-status-capture` は `--value` と終了コード捕捉を引き続き担当します。無変異の shell には両断片が存在し、片方の削除が他方を欠落させないことを手で照合しました。単独欠落の期待値は変更不要です。

`py_compile`、`git diff --check`、両ファイルの Unicode NFC 確認は成功しました。

## 総括

perf preflight 代用の不整合と fixture 断片の重複依存を修正しました。実評価・認可・reservation・claim・layout・campaign lock・WAL の結合は維持しています。両 outcome、rc 0、両 variant の全指定 WAL stage、claim 取得 1 回・record 不変、候補 checkpoint 不変の assert は弱めていません。

**実装済み・未実走です。** pytest は実行していません。production・job body・docs・所有外テストは未変更で、`git add`／`git commit` も実行していません。