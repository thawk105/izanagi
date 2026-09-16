## 所見の対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| A・B：旧 pin の proof source 不整合 | partial | 両 fixture の発行区間で helper の pin を統一。実装済み・未実走 |
| B：import 時の proof context | partial | 旧 pin 設定後に context を再生成し、一時差し替え。実装済み・未実走 |

closed と判定した所見はありません。

## file:line ごとの変更

- [test_artifact_admission.py:62](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2125-fix1/orchestrator/tests/test_artifact_admission.py:62)：`receipt_support.CURRENT_PIN` と `_PROOF_BUILD_CONTEXT` を発行区間だけ差し替え。
- [test_layer3_report.py:1900](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2125-fix1/orchestrator/tests/test_layer3_report.py:1900)：実際の呼出先 `support.receipt_support` に同じ修正。

計 12 行追加。context は policy を保持するため、pin 変更後の再生成が必要です。両方とも `monkeypatch.context()` 終了時に復元され、読取側は現行 policy を使います。

## テスト (nodeid と実走結果)

次の範囲を一括指定しました。

```text
python3 tools/run_tests.py orchestrator/tests/test_artifact_admission.py orchestrator/tests/test_build_admission.py orchestrator/tests/test_layer3_report.py
```

**結果：rc=16、`qstat -Q` preflight 失敗、`child_started=false`。全件未実走です。**

対象範囲には以下の nodeid が含まれます。

- `orchestrator/tests/test_artifact_admission.py::test_historical_policy_version_reads_recorded_v2[pin]`
- `orchestrator/tests/test_layer3_report.py::test_historical_policy_version_report_schema`
- 同 artifact ファイルの structure・trigger・bytes・pre-T733 epoch 検査全件

`git diff --check` は成功。AST 比較コマンドは hook に拒否され、未実行です。期待値不変更は差分で確認しました。

## 波及の静的列挙

- `recorded_policy_campaign("pin")` を使う親報告の 13 ケースと、Layer3 schema の 1 ケースが直接対象です。
- `current`・`generator`・`review` 分岐と `_new_schema_campaign` 本体は変更していません。
- 共有 `commit_receipt_support.py` は無変更。campaign、verifier、critic、S1、S8、P3 等の所有外 caller に対する既定値は維持されます。
- `test_autonomous_trial_completeness.py` と `test_p3_autonomous_workload_trial.py` の `admitted-new-schema` 期待値は変更していません。両ファイルは未実走です。
- production consumer の配線・受理条件は無変更です。

## 残った不確実性

修正後の赤 14 件の解消、指定 3 ファイルの全件成功、変異検出は未確認です。レビュー B の M2 単一理由性問題は今回の修正対象外です。

補助検索で `orchestrator/verifier.py` は存在せず読めませんでした。必読ファイルはすべて読取可能でした。

## 総括

指定の fixture 不整合だけを修正しました。共有 helper・production・既存期待値・docs は無変更、commit は作成していません。**実装済み・未実走として親の検証待ちです。**