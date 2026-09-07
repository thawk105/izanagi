## 台帳の更新内容

更新器は rc=0 でしたが、許可された 4 件ではなく 206 件を追加したため、変更を破棄しました。

- 更新前: `nodeid_count=19517`
- 一時更新後: `nodeid_count=19723`
- 復元後: `nodeid_count=19517`
- 最終的な追加: 0 件

対象 4 件に更新器が算出した値:

- `orchestrator/tests/test_s8c_cli_entrypoints.py::test_cli_entrypoint_matches_library_report[prereg-path]`: `0.26`
- `...::test_cli_entrypoint_matches_library_report[prereg-module]`: `0.13`
- `...::test_cli_entrypoint_matches_library_report[gate-path]`: `0.13`
- `...::test_cli_entrypoint_matches_library_report[gate-module]`: `0.13`

対象外の追加がさらに 202 件ありました。

## 既存 entry 不変の確認

更新前後の JSON を比較し、以下を確認しました。

- 既存 entry の欠落: 0 件
- 既存値の変更: 0 件
- 追加 206 行を除去し `nodeid_count` のみ戻した byte 列が更新前スナップショットと完全一致
- SHA-256 は双方とも `fcf32fea491c9746be156af22664f71393aa311356d61db2e106f32aa8bc1ece`

復元後も同じ SHA-256 で、対象ファイルの最終 diff は 0 行です。一時差分は `+207/-1` でした。

## 実走結果 (nodeid と rc)

- 台帳更新器: rc=0、`added=206`
- `orchestrator/tests/test_update_acceptance_duration_ledger.py`: 実装済み・未実走
- `orchestrator/tests/test_acceptance_schedule_order.py`: 実装済み・未実走

差分要件を満たさなかったため、手順 3 で復元して停止しました。

## 残った懸念・親へ返す判断

`focus1.xml` は 1262 testcase を含み、現台帳に未登録の対象外 node が 202 件あります。この XML を指定コマンドへそのまま渡す限り、4 件だけの追加にはなりません。

親側で対象 4 testcase だけを含む実測 JUnit XMLを用意するか、対象外 202 件の扱いを再裁定する必要があります。

## 総括

要件外の大量追加を検出したため安全側に停止しました。台帳は更新前へ完全復元済みで、作業ツリーには本作業による変更を残していません。