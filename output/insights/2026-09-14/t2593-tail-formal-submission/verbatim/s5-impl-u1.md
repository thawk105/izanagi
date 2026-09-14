## 実装

所有する submit script と新規テストだけを編集しました。新系列の入力検査、3 job への転送、旧系列 argv・receipt、負例、文書 argv と driver CLI の対応を実装しています。既存 output-parent 検査と指定の逐語 pin は保持しました。

`--help` は指定どおり全引数位置で優先します。従来拒否していた「未知 flag の後」「値の位置」も rc=0 になります。

## 検証と残件

- `bash -n` と Python AST 構文検査：成功。
- 新規テスト：11 関数・展開上90ケース、**未実走**。
- `test_plain_runner_coverage.py`（3件）と既存 `test_b10_run_kind_routes_t2266_only_by_opt_in_and_binds_all_receipts` / `test_b10_run_kind_routes_t2418_through_job_submit_and_finalizer`：実行を試みましたが未実走。

runner は2回とも `qstat -Q` の socket 作成拒否で rc=16、`child_started=false`。pytest 実走は **0件**です。生成された失敗記録は `/tmp/t2593-u1-*-dispatch-failure-*` に退避しました。

赤の可能性が残る箇所は、stub と Python 3.10 の実環境での接続、文書抽出から CLI への引渡し、別実装者の job 編集との組合せです。所有外への波及面は job 側 consumer、既存 shell consumer test、hooks 登録、共有 `tmp_path` fixture です。

補助探索した dispatch module 候補3パスは不存在でした。必読ファイルはすべて読めています。

## 総括

- **実装した内容：** 新系列の受理・検査・転送と90ケースのテスト。docs・既存テスト・Git状態の変更、commit は行っていません。
- **実走したもの：** 構文検査のみ成功。pytest nodeid の実走は0件で、**実装済み・未実走**です。
- **裁定との差異：** 必要な挙動検証を実走で閉じられていません。`--help` の全位置優先は今回の明示指示に従っています。