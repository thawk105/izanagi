## 変更の要約

R2・R3・R4・R10 を指定7ファイルに実装しました。**実装済み・テスト未実走**です。commit はしていません。

v2 の `HISTORICAL_RAW` だけ記録 policy を読み、receipt SHA と stock pin の比較先を変更します。generator／review 登録と coder authority は現行のままです。

## file:line ごとの変更

- [build_admission.py:260](orchestrator/campaign/build_admission.py#L260)：独立 literal、別型、歴史 decoder を追加。`:733` で検査本体を共有し、`:832` に歴史 receipt 入口を追加。
- [wal.py:2122](orchestrator/campaign/wal.py#L2122)：現行 exact 型 gate を保持。`:2136` に歴史 topology 入口、`:2150` に共有本体を追加。
- [artifact_admission.py:1002](orchestrator/campaign/artifact_admission.py#L1002)：exact purpose による policy 分岐。`:1463` で新 classification と既存の非認証 status を投影。
- [layer3_schema.json:15](orchestrator/campaign/layer3_schema.json#L15)：certifying 側を従来2分類に限定。`:298` に歴史分類を追加。
- 既存テスト3ファイルへ11関数・33ケースを追加。既存テスト本文は変更していません。

変更前 topology 呼出しは訂正資料どおり **1368行**です。WAL 第2照合は変更前2767行→現在2793行で、内容は不変です。

## テスト (nodeid と実走結果)

すべて `tools/run_tests.py` 経由で試行しました。

| 試行範囲 | 結果 |
|---|---|
| 変更前：`orchestrator/tests/test_artifact_admission.py::test_valid_v2_campaign_is_admitted`、`::test_certified_acceptance_admits_exact_e1_fixture`、`test_build_admission.py` 全体 | rc=16、本体未起動 |
| 変更後：`test_artifact_admission.py`、`test_build_admission.py`、`test_layer3_report.py` 全体 | rc=16、本体未起動 |
| 同3ファイルの `--collect-only` | rc=16、収集未実行 |

原因はいずれも **`qstat -Q preflight rc=1`** です。

追加 nodeid は、以下のファイル名と関数名を `::` で結んだものです。全件 **実装済み・未実走**です。

| ファイル（`orchestrator/tests/` 配下） | 関数名 |
|---|---|
| `test_artifact_admission.py` | `test_historical_policy_version_reads_recorded_v2` |
| 同上 | `test_current_policy_campaign_unchanged_for_both_purposes` |
| 同上 | `test_historical_policy_shape_is_exact` |
| 同上 | `test_historical_policy_drift_preserves_structure_checks` |
| 同上 | `test_historical_policy_drift_rechecks_bytes` |
| 同上 | `test_historical_policy_drift_preserves_trigger_checks` |
| 同上 | `test_historical_policy_version_preserves_pre_t733_epoch` |
| `test_build_admission.py` | `test_policy_shape_literal_matches_current_schema` |
| 同上 | `test_historical_policy_cannot_enter_current_consumers` |
| 同上 | `test_receipt_rejects_invalid_current_comparison` |
| `test_layer3_report.py` | `test_historical_policy_version_report_schema` |

実行できた確認は、構文解析、`git diff --check`、`check_codex_agents.py`、`check_docs.py`。すべて通過しました。AST 比較で、共有検査本体は指定した比較先・receipt 呼出し以外が同一と確認しました。

## 現行の受理・拒否挙動との差

変更前は policy 不一致の v2 を両 purpose とも拒否していました。変更後は、既存検査を満たす歴史閲覧だけを受理する実装です。

certified と `classify_campaign` の不一致拒否文言、v1／overlay 分岐、epoch、exact view gate、recovery、第2照合は保持しています。認証受理集合の不変は静的確認までで、実走検証は未完了です。

## 波及の静的列挙

- 歴史 caller：critic digest／online digest、p2_2 report、Layer3 admission、B10 exploration、replay discovery。
- 維持する認証 caller：Layer3・autonomous completeness の再 admission、`replay.load_landscape`、B10 certified。
- 共有 fixture：既存 `_new_schema_campaign`、`campaign_lock_test_support`、`commit_receipt_support` に依存。本文は未変更です。
- consumer test：上記 consumer 群と WAL／`test_p3_s4_loop.py` の回帰実走が残ります。
- critic digest への classification 追加投影、旧 grammar の Layer3 投影、`plot_s1_9pair.py` の回復は成果に含めません。

## 残った不確実性

baseline 緑・変更後テスト・変異検査は未確認です。親資料の「停止中レポート0件、DW-G04未充足」を覆す外部実測は行っていません。

保証は記録 policy と receipt の内的整合までです。記録 policy の真正性は保証しません。

runner が指定編集面外の `output/pegasus-dispatch/` に診断 receipt を3件自動生成しました。手動編集は指定7ファイルのみです。

## 総括

実装と静的確認を終えました。テスト基盤の復旧後に実走検証が必要であり、完了判定にはしていません。