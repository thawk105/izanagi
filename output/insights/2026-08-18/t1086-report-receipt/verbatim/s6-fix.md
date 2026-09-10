## 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F-1 | `partial` | root 不在・読込不能を `missing` に変更。字句違反・symlink・非 regular leaf の hard-fail は維持。実装済み・未実走。 |
| F-2 | `partial` | `os.open` 注入点で stat/open 間の parent/leaf 交換を再現する対照を追加。実装済み・未実走。 |
| F-3 | `partial` | `orchestrator/` 全 production moduleへ走査を拡張し、module-level、同期・非同期関数、別名・相対 import を解決。実装済み・未実走。 |

## 編集ファイル

- [s8b_oracle_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_report.py:1823)
  - output root 不在・読込不能を `actual_sha256=None` に落とすよう修正。
- [test_s8b_oracle_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/tests/test_s8b_oracle_report.py:1665)
  - F-1 対照、parent/leaf race 対照、production caller pin 拡張を実装。
- [test_s8b_oracle_manifest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/tests/test_s8b_oracle_manifest.py:61)
  - 独立 golden の report SHA と raw spec SHA を再同期。

既存テストの期待値は変更していません。docs、worklog、insight は編集せず、commit も作成していません。

## 追加テスト nodeid

すべて実装済み・未実走です。

- `orchestrator/tests/test_s8b_oracle_report.py::test_official_missing_output_root_reports_missing_and_judges_indeterminate`
- `orchestrator/tests/test_s8b_oracle_report.py::test_store_reverification_parent_nofollow_blocks_stat_open_race`
- `orchestrator/tests/test_s8b_oracle_report.py::test_store_reverification_leaf_nofollow_blocks_stat_open_race`

既存の `test_build_observations_production_caller_is_main_only` も拡張しました。

## 静的な波及範囲

- production caller: `s8b_oracle_report.main()` 1 件。
- production consumer: `s8b_oracle_judge.py` が receipt を検証し、間接的に `s8b_verdict.py` へ伝播。
- 共有 fixture: `_ratified_cli_manifest`、`_reverified_store_fixture`、`_judge`。
- consumer tests: `test_s8b_oracle_driver.py`、`test_s8b_oracle_judge.py`、`test_s8b_verdict.py`、`test_s8b_oracle_manifest.py`、`test_s8b_binding_driftguards.py`、`test_s8b_materialization.py`、`test_official_perf_closure.py`、`test_s8b_oracle_manifest_contract.py`、`test_s8b_oracle_artifacts.py`。
- 既存 staged 差分のうち、上記3ファイル以外は触れていません。

## PIN_GATE_SPEC 更新後3値

- report SHA-256: `cd599cc7ac7f518bb64585127588e716311727c6e1063e7aac1d51c4373a39bd`
- judge SHA-256: `0e6276ddcb6cde6e38f781bdbb8df1289520cfcce9653330d2c83a1db20784d3`
- `PIN_GATE_SPEC_SHA256`: `05adc052288f64bb67da3295591212c3aea8e56dc3bca68c04802da68e9b1989`

production serializer は使用していません。AST から `PIN_GATE_SPEC_RAW` literal を取得し、`hashlib.sha256` で再計算しました。

## 検査と未完事項

`git diff --check`、編集3ファイルの AST parse、PIN raw hash 自己整合を確認済みです。pytest は指定された sandbox 制約に従って実走しておらず、緑や `closed` は申告しません。実装できなかった項目はありませんが、動的な成立確認は親の焦点走・受入走に残ります。

## 総括

F-1からF-3までのコード・テスト実装を完了しました。  
root 不在は hard-fail せず、全 cell が `missing` になる設計です。  
judge はその receipt を `indeterminate` に倒します。  
parent と leaf の race 対照は `O_NOFOLLOW` の実効性を直接検査します。  
caller pin は production 全域と全実行スコープを走査します。  
既存期待値、docs、worklog、insight は変更していません。  
PIN golden の3値は最終 production bytes に同期済みです。  
pytest は未実走のため、3所見はいずれも `partial` と報告します。