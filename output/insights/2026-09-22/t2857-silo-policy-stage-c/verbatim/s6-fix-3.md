## 原因の確認

H1 の推定はコード上の依存関係と一致します。ただし、当該実走の stderr が失われているため、直接原因の確定は再実走待ちです。

- supply は `condition_meaning_gate.py:2386`、meaning は同 `:3248` で owner TU を前処理します。configure だけでは生成 header を供給できません。
- include 連鎖は `transaction.cc:7 → transaction.hh:16 → common.hh:12 → masstree_wrapper.hh:20` で、masstree の `config.h` に到達します（各ファイルは `external/ccbench` 配下）。
- `external/ccbench/cmake/ThirdParty.cmake:58`・`:66` は、masstree source dir の `config.h` を build 時に生成します。
- `s3_mocc_lock_coverage.py:228` と `tools/pegasus/fetch_third_party.py:652` より、依存ソースは job ごとの新しい写しです。同一 job 内の各 case はその写しを共有します。
- 既存 driver は `s3_lock_coverage.py:258`、`s3_mocc_lock_coverage.py:811` で gate なしの stock build を先行させています。

## 直した内容

`orchestrator/campaign/silo_policy_coverage.py:323`・`:699` で supply／meaning／admission の canonical JSON 全体を例外属性と結果 JSON の `condition_gate_evidence` に保存し、拒否時は従来どおり case の build を止めます。
同 `:658`・`:693` で両モード共通の準備用 stock build を case 処理前に1回追加し、受理条件を変更せず、既存 sink・materializer を再利用します。

## 確認の実測

- 編集した3ファイルの `python3 -m py_compile`：終了コード **0**。
- build sink は読み取りで **379行**と確認し、本 wave の pin のみ **373 → 379** に追随。
- AST 読み取りで既存の process/helper 呼出し箇所を確認。

以下はすべて **実装済み・未実走**です。

- `test_silo_policy_coverage.py::test_condition_gate_failure_keeps_complete_receipts_and_stops_build`
- `test_silo_policy_coverage.py::test_main_prepares_dependencies_once_before_gates_in_either_case_order`
- `test_silo_policy_coverage.py::test_condition_gate_rejection_preserves_arm_reasons_in_result_json`
- `test_ccbench_spawn_sites.py::test_production_build_sinks_include_certify_calibration_script`
- `silo_policy_coverage.py::main(coverage)`
- `silo_policy_coverage.py::main(smoke)`

## 変えていないことの根拠

既存 assert・期待値は保持し、既存拒否テストの fixture だけを追加記録に対応させました。spawn test の差分は許可された pin の1箇所だけです。

許可3ファイル外の34,472項目は、変更前後のパス・サイズ・更新時刻の集約値が一致しました。gate 本体、既存 driver、docs、登録簿は編集せず、git コマンドも実行していません。

## 未了と疑問

計算ノードで coverage／smoke と関連テストの再実走が必要です。両モードに準備用 stock build が1回増えるため、その所要時間も未計測です。

## 総括

H1 の証拠保存・依存物準備・追加テストを実装しました。構文確認は成功、実機での解消確認は未了です。