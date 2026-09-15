## 現行の受理・拒否挙動

変更前は R の staging・policy・clean を検査し、qsub は投入元 C で起動していました。相対 script・attempts は C 基準です。

不正な ratio／protocol、欠損 staging／script／policy、dirty tree を拒否し、preflight 失敗は rc=3、qsub 失敗はその rc を返す既存処理を維持しました。

## 実装

所有する 2 ファイルだけを変更しました。

- qsub を `( cd -- "$REPO_ROOT" && … )` で起動。リダイレクトは括弧の外側。
- 相対 job-script だけを投入元 cwd 基準で絶対化。
- 既存 dry-run wrapper の引数・返却値・既定動作を維持。
- schema・option 構成・export spec は変更なし。commit は未作成。

## テスト

`orchestrator/tests/test_pegasus_calibration_workload.py` に以下の 6 ケースを追加しました。

- `test_submitter_runs_qsub_in_repo_root[repo]`
- `test_submitter_runs_qsub_in_repo_root[outside]`
- `test_submitter_keeps_relative_attempts_in_caller`
- `test_submitter_keeps_relative_job_script_bytes_from_caller[original]`
- `test_submitter_keeps_relative_job_script_bytes_from_caller[changed]`
- `test_submitter_preserves_qsub_failure_and_captures`

fake qsub が実 cwd・argv・script bytes/hash を記録します。既存 42 テスト関数は AST 比較で変更なしを確認しました。

## 実走結果

通過した検査：

- Bash 構文、Python AST 構文
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

**pytest の実走 nodeid は 0 件です。** 対象ファイル全体と consumer・meta-test を `tools/run_tests.py` 経由で試行しましたが、dispatch の `qstat -Q` が socket 作成権限エラーとなり、rc=16・`child_started=false` で終了しました。

## 波及の静的列挙

- 共有 fixture：既存 dry-run テストが切り出した作成 helper を使用。
- consumer：`test_pegasus_tools.py` の構文・policy・dry-run 契約。
- meta-test：収集設定、所要時間台帳、全収集に対する台帳被覆率。
- job：`certify_calibration.sh` の `PBS_O_WORKDIR` による木の選択。
- hooks・docs・registry：分類と参照 path は維持。他 submit の参照は出典コメント。
- 相対 PATH、CDPATH、任意 attempts の job 側配送は裁定どおり scope 外。

## 残る赤と未実走

実装済み・未実走です。追加 6 ケース、既存 consumer、meta-test、M1〜M5 の変異検証、親の受入全走が残っています。テスト由来の赤は未観測で、実行基盤の rc=16 が残っています。

実 scheduler・計算ノード・認定本走は実行していません。

## 総括

指定範囲の実装とテスト追加は完了しました。静的検査は通過しましたが、動作検証は実行環境の制約で未完了です。