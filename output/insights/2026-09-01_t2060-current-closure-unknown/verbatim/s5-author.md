## 現行の受理・拒否挙動

- v2 の記録 closure は、purpose 判定前に記録 commit の blob と照合されます。[artifact_admission.py:888](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:888)
- `HISTORICAL_RAW` は記録済み E0/E1 をそのまま返し、現行 closure を読みません。[artifact_admission.py:957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:957)
- `CERTIFIED_ACCEPTANCE` は E0 を拒否し、E1 では現行 closure を取得します。取得失敗は exact `E1-stale/current-closure-unavailable` に変換されます。[artifact_admission.py:965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:965)
- その後の全 COMMIT 永続認証、certified token 発行、exact `CertifiedCampaignView` 拒否も維持されています。[artifact_admission.py:1268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1268)、[artifact_admission.py:1315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1315)

## 実装した内容 (file:line)

- [artifact_admission.py:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:392): `HistoricalCampaignView.current_verifier_conformance` property を追加し、exact `"unknown"` を返すようにしました。
- [layer3_report.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:614): 歴史 report の top-level へ直接属性アクセスで投影しました。
- [layer3_report.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:707): certified 昇格時に同 field を除去します。
- [layer3_schema.json:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:13): `certifying_input=true` で top-level field を禁止しました。
- [layer3_schema.json:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:242): optional property として exact `"unknown"` を定義しました。top-level `required` と nested epoch は変更していません。

## 新設したテスト (node 名と意図)

- `test_historical_raw_with_dirty_current_closure_preserves_recorded_view_structure`: (a) dirty closure でも exact historical view と記録 E1 を維持。[test_artifact_admission.py:1578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:1578)
- `test_historical_view_reports_unknown_current_verifier_conformance`: (b) property の直接値検査。[test_artifact_admission.py:1599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:1599)
- `test_certified_acceptance_rejects_dirty_current_closure_with_exact_diagnostic`: (c) exact 例外型、state、reason を検査。[test_artifact_admission.py:1613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:1613)
- `test_historical_build_report_projects_unknown_current_verifier_conformance`: (d) 歴史 report の top-level 投影。[test_layer3_report.py:1331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1331)
- `test_saved_report_without_current_verifier_conformance_remains_readable[v2|v3]`: (e) field を欠く保存済み両版の互換性。[test_layer3_report.py:1498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1498)
- `test_certified_report_omits_and_schema_forbids_current_verifier_conformance`: (f) 正規 certified report の field 不在と、注入時の schema 拒否。[test_layer3_report.py:1847](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1847)

(a)〜(c) は `_committed_closure_repo` と `_REPO_ROOT` のみを利用し、取得器自体は差し替えていません。

## 実走結果 (nodeid と範囲、赤の内訳)

pytest の実走 node は 0 件です。

新規 7 node と meta-test `test_p3_build_authority_cli.py::test_tracked_python_coder_authority_ast_closure_is_exact` を `tools/run_tests.py` へ投入しましたが、2 回とも `qstat -Q preflight rc=1`、runner `rc=16`、`child_started=false` で pytest 開始前に停止しました。assertion 赤は観測していません。

静的検査結果:

- Python 4 file の AST parse: 成功
- schema JSON parse、Draft 7 schema 検査: 成功
- certified conditional の通過・拒否 probe: 成功
- `git diff --check`: 成功
- 禁止された結合文字: 0 件

## 変異事前登録との整合

- M1: historical early return [artifact_admission.py:963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:963) は無変更で、2 行削除の exact 変異が成立します。
- M2: certified capture/catch [artifact_admission.py:967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:967) は無変更で、try/except 全体削除の exact 変異が成立します。
- C1: top-level `required` に field を加える exact 変異が成立し、v2/v3 互換 node が検出対象です。
- C2: schema line 13 の禁止句削除が exact 変異として成立します。
- D1: property の戻り値変更が exact 変異として成立します。
- D2: report 投影行削除が exact 変異として成立します。
- L1: line 707 の除去行削除が exact 変異として成立します。

再登録が必要な位置はありません。

## 波及可能性 (所有外 caller・共有 fixture・consumer test)

- 所有外 caller: `autonomous_trial_completeness.py`、`s1_report.py` は `build_report` の追加 top-level key の影響候補です。`replay.py`、`guided.py`、`search_baselines.py`、`s8b_oracle_report.py` の purpose 分類は変更していません。
- admission 直接 consumer: `p2_2_report.py`、`p3_autonomous_workload_trial.py`、`p3_b4_closed_critic.py`、`p3_b4_wiring_probe.py`、`p3_s4_loop*.py`、`p3_s4_red.py`、`replay.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`。property は dataclass field ではないため既存 projection は変わりません。
- schema consumer: `s1_known_axes_freeze.py`、`s1_measurement_freeze.py`、`silo_ladder_rung1.py`、`t080_freeze_migration.py`、`t810_preregistration.py`。
- 共有 fixture: `commit_receipt_support.py`、`campaign_lock_test_support.py`、`_committed_closure_repo`、`_new_schema_campaign`、`_campaign`、`_historical_admitted_campaign`、`_certifying_receipt_for`。
- consumer test 候補: 裁定 §6 の 12 fileに加え、静的参照から `test_autonomous_trial_completeness.py`、`test_trial_registry.py`、`test_t126_qualification_artifacts.py`、`test_official_perf_closure.py`、`test_s1_known_axes_freeze.py`、`test_s8b_oracle_driver.py`、AST closure meta-test を確認しました。

## 未実走・未確認

- 新規 7 node、変更した 2 test file の全走、裁定 §6 の焦点 test 群、上記 consumer test は実装済み・未実走です。
- 実 repository root を使う certified node の期待赤は、pytest 未開始のため assertion 本文では確認できていません。
- mutation harness は未実走です。
- runner の失敗した dispatch が ignored receipt を `output/pegasus-dispatch/c56f01ecd680cfab0203f2b08ac3b3e4/` と `output/pegasus-dispatch/83b27aebbd9946b7e53b691227084582/` に自動生成しました。手動編集や追跡差分はありません。
- commit 後の閉包整合状態は親の commit 後に確認が必要です。

## 総括

裁定 §2 の範囲だけを許可された 5 file に実装しました。production gate、certified 受理集合、nested epoch、reason enum は無変更です。

全差分は追加のみで、削除行は 0 件です。既存テストの期待値、assert、raises、skip、node 名は一つも変更していません。`git add`、commit、stash、checkout、merge、rebase は実行していません。pytest が未実走のため、状態は「実装済み・未実走」です。