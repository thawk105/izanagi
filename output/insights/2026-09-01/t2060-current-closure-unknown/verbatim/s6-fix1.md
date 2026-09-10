## 所見対応表 (closed / partial / regressed)

| 所見 | 状態 | 対応 |
|---|---|---|
| PF-01 | closed | 保存済み側に field が無い場合だけ両側から除外し、存在時は byte 比較を維持 |
| PF-02 | closed | producer liveness と consumer fail-closed を別 node に分割 |
| PF-03 | closed | 既定値なしの `pop` に変更し、field 欠落時は失敗 |
| regressed | なし | certified の受理集合や schema 条件は変更なし |

## 直した内容 (file:line)

- [autonomous_trial_completeness.py:4687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/autonomous_trial_completeness.py:4687)
  - `include_current_verifier_conformance` flag を既存 projection 機構へ追加。
  - 保存済み側の key 実在を [5012 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/autonomous_trial_completeness.py:5012) で直接判定。
  - 欠落時だけ両側から除外し、存在時は値を残して厳密比較。
- [layer3_report.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:707)
  - PF-03 指定の 1 行だけを `report.pop("current_verifier_conformance")` に変更。

## 追加したテスト (node 名と意図)

- `test_campaign_chain_reads_legacy_layer3_without_current_verifier_conformance`
  - field のない保存済み report と fresh rebuild の比較が通る正例。
- `test_campaign_chain_rejects_persisted_current_verifier_conformance_mutation`
  - 保存済み側に field がある場合、値の変更を canonical byte 比較が拒否する負例。
- `test_certified_report_omits_current_verifier_conformance`
  - certified producer が field を除去する liveness node。
- `test_certified_schema_forbids_current_verifier_conformance`
  - schema を通る certified report へ field を注入すると拒否する consumer node。

既定値付き `getattr`、`.get` で成立させたテストはありません。

## 実走結果 (nodeid と範囲、赤の内訳)

次の 4 node を共通 runner へ投入しましたが、`qstat -Q preflight rc=1`、runner `rc=16`、`child_started=false` で pytest 開始前に停止しました。

- `orchestrator/tests/test_autonomous_trial_completeness.py::test_campaign_chain_reads_legacy_layer3_without_current_verifier_conformance`
- `orchestrator/tests/test_autonomous_trial_completeness.py::test_campaign_chain_rejects_persisted_current_verifier_conformance_mutation`
- `orchestrator/tests/test_layer3_report.py::test_certified_report_omits_current_verifier_conformance`
- `orchestrator/tests/test_layer3_report.py::test_certified_schema_forbids_current_verifier_conformance`

したがって、pytest は実装済み・未実走です。assertion 赤は 0 件、infra failure は 1 件です。

静的確認は以下が通過しました。

- 変更 4 Python file の AST parse
- PF-01 projection の欠落時同値化と存在時差分保持の runtime probe
- 新規 node 名の一意性検査
- `git diff --check`
- 結合文字 U+0300〜U+036F が差分中 0 件

runner が自動生成した dispatch receipt は保存済み成果物と混同しないよう `/tmp/t2060-fix-dispatch-receipt-0d85467a74bfe585eae6c1fd81faf399` へ退避し、`output/` には残していません。既存 report と既存 receipt は変更していません。

## 変異事前登録との整合

- M1: [artifact_admission.py:963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:963) の historical early return はそのまま成立。
- M2: [artifact_admission.py:967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:967) の capture `try/except` 全体削除変異はそのまま成立。
- D1: [artifact_admission.py:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:394) の戻り値変更はそのまま成立。
- D2: [layer3_report.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:614) の投影行削除はそのまま成立。
- C1: [layer3_schema.json:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:22) の top-level `required` 追加変異はそのまま成立。
- C2: [layer3_schema.json:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:13) の禁止句削除はそのまま成立。検出 node は分割後の consumer node。
- L1: exact old 逐語は不成立。PF-03 により `pop("current_verifier_conformance", None)` から [既定値なしの形](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:707) へ変わったため、親で anchor の再登録が必要です。除去行削除という変異内容と producer node の帰属は維持されています。

## 波及可能性

- 所有外 caller: `p3_autonomous_workload_trial.py`、`trial_registry.py`。どちらも Layer 3 chain または `build_report` を経由します。
- 共有 fixture: `_layer3_campaign`、`_campaign_report`、`_campaign`、`_certifying_receipt_for`、`commit_receipt_support.py`、`campaign_lock_test_support.py`。
- 直接 consumer test: `test_autonomous_trial_completeness.py`、`test_layer3_report.py`、`test_trial_registry.py`、`test_t126_qualification_artifacts.py`、`test_s8c_preregistration_predicates.py`。
- 裁定で指定された波及候補: `test_official_perf_closure.py`、`test_s1_known_axes_freeze.py`、`test_s8b_oracle_driver.py`、Layer 3 admission、S-1、oracle、replay 系 test、および AST closure meta-test。

## 未実走・未確認

- 新規 4 node、変更した 2 test file の全走、上記 consumer test は未実走。
- mutation harness は未実走。
- 実成果物 7 件を入力した統合走は未実施。保存済み成果物自体は変更していません。

## 総括

must-fix 3 件だけを、指定された 4 file に限定して修正しました。段 5 の `artifact_admission.py`、`layer3_schema.json`、`test_artifact_admission.py` には触れていません。

既存テストの期待値、assert、raises、skip、parametrize は一つも変更・緩和・削除していません。変更した node 名は PF-02 の分割対象だけです。`CERTIFIED_ACCEPTANCE` の受理集合も広げていません。

`git add`、commit、stash、checkout、merge、rebase は実行していません。