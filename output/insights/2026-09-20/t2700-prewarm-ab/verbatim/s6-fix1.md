## 総括

`orchestrator/tests/test_pegasus_dispatch_compute.py` の `test_early_memo_environment_request_and_child_overlay` 内だけを修正しました。

- dispatch の request 検査を維持し、overlay 検査には別の `job/request.json`（v2）を作成。
- token／empty の2ケース・id・既存assertを維持。`result.json` の削除はしていません。
- AST構文検査：成功。対象関数外に変更がないことも確認。
- `tools/run_tests.py` 経由で `-k 'allowlist or environment'` を試行しましたが、`qstat -Q preflight rc=1` により終了コード16。pytestは起動せず、修正後の2ケースは未実走です。親の焦点走での確認が必要です。