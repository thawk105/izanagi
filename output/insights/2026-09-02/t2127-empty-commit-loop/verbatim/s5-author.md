## 実装した内容

- persisted COMMIT 全件を同一の `records` 母集合で検証する `admit_persisted_certified_commits()` を追加しました。
- `CertifiedCampaignView` に必須件数 field を追加し、exact `int`、非負、snapshot 内 COMMIT 件数との一致を検査します。
- commit 存在要求を担う `require_certified_commit_evidence()` を追加しました。
- `replay.load_landscape` と `layer3_report.build_accepted_report` の2箇所だけへ配線しました。
- no-commit admission と存在要求を独立に壊せる test、constructor 検査、replay・Layer3 の正負例を追加しました。
- 規律2は不変です。anomaly のある COMMIT は既存単数 helper が直ちに raise し、件数も view も発行されません。

## 受理集合を広げない理由 (述語ごと)

- `require_persisted_certified_commit`: 述語本体を変更していないため、従来拒否した receipt、verify、anomaly、attempt 不整合は引き続き拒否します。
- `admit_persisted_certified_commits`: 各 COMMITへ既存単数 helperを適用し、同じ完全な `records` を渡すため、証拠母集合を狭めず、余分な verify も引き続き検出します。
- `_require_admitted_campaign`: 手書き loopを等価な共通 scanへ置換しただけです。0件は従来どおり admission 成功、1件以上の不正 COMMIT は従来どおり拒否されます。
- `CertifiedCampaignView.__post_init__`: 件数の型・非負・snapshot 整合という追加拒否だけであり、既存の拒否条件を除去していません。
- `require_certified_commit_evidence`: exact view 検査後に件数0だけを追加拒否します。
- `replay.load_landscape`: certified commit 0件だけを追加拒否し、正規 COMMIT 付き E1 landscape は従来経路を維持します。
- `layer3_report.build_accepted_report`: certifying 入力の COMMIT 0件だけを追加拒否し、正規 COMMIT、verify_done、receipt 付き campaign は従来どおり report を生成します。

## 変更した file の全数

変更は8 fileです。

- `orchestrator/campaign/artifact_admission.py` — 共通 scan、件数 fieldと整合検査、存在要求 helper、発行経路の件数投影。
- `orchestrator/campaign/replay.py` — `load_landscape` へ存在要求を配線。
- `orchestrator/campaign/layer3_report.py` — `build_accepted_report` へ存在要求を配線。
- `orchestrator/tests/test_artifact_admission.py` — 0/1/2件投影、private zero-count view、exact int・非負・snapshot 整合 test。
- `orchestrator/tests/test_layer3_report.py` — 指定4 test名を維持し、正規 COMMIT fixtureへ更新。0件拒否 testを追加。
- `orchestrator/tests/test_bench_first_real_wal.py` — replay の正規 E1 正例を維持し、COMMIT 0件 E1負例を追加。
- `orchestrator/tests/commit_receipt_support.py` — shared fixture constructorへ records 由来件数を追加。
- `orchestrator/tests/test_t1286_commit_receipt.py` — constructor 2箇所へ records 由来件数を追加。

`acceptance_duration_ledger.json` は未変更です。新規 nodeの duration は実測禁止の指示に従い、親の測定後追記へ残しました。禁止 file、`docs/`、`tools/`、`hooks/`、`external/`、`output/` に差分はありません。

## 波及の静的列挙

- `CertifiedCampaignView(` は新規 private fixtureを含め全6 call siteを再検索し、すべて必須件数を渡すことをASTで確認しました。
- 既存 constructor fixtureの到達先は `commit_receipt_support.py`、`test_t1286_commit_receipt.py`、`test_artifact_admission.py` です。shared supportの利用先として `test_guided.py` と `test_campaign.py` にも間接波及します。
- 名前検索で届く production 22 fileに、意味的 consumer `orchestrator/verifier/commit_receipt.py` を加えた23 fileを照合対象としました。さらに replay 経由の間接 consumerは `search_baselines.py` と `guided.py` です。
- consumer testへの主な波及候補は `test_autonomous_trial_completeness.py`、`test_backoff_consumers.py`、`test_critic.py`、`test_guided.py`、`test_p3_autonomous_workload_trial.py`、`test_p3_b4_closed_critic.py`、`test_p3_s4_loop.py`、`test_p3_s4_loop_sort.py`、`test_p3_s4_loop_trigger_gating.py`、`test_paper_story_a1_paired.py`、`test_s1_9pair_figure_provenance.py`、`test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py` です。
- decision receiptや保存 schemaへ件数を射影していません。dataclassの比較・hashには件数が加わりますが、正規 viewでは recordsから一意に決まります。
- `artifact_admission.py` と `replay.py` の contract-loader closure、および `layer3_report.py` の generator SHA は変更されるため、親の commit後実測が必要です。

## 未実走の明記と親が走らせる nodeid

実装済み・pytest未実走です。緑は主張しません。AST parse、production import smoke、ledger JSON parse、`git diff --check`、constructor全数検査、禁止文字不在は確認済みです。

親が最低限走らせるべき焦点 selectorです。

- `orchestrator/tests/test_artifact_admission.py::test_certified_acceptance_admits_exact_e1_fixture`
- `orchestrator/tests/test_artifact_admission.py::test_persisted_commit_gate_accepts`
- `orchestrator/tests/test_artifact_admission.py::test_persisted_commit_gate_rejects`
- `orchestrator/tests/test_artifact_admission.py::test_certified_view_checks_every_commit`
- `orchestrator/tests/test_artifact_admission.py::test_certified_commit_evidence_rejects_no_commit_campaign`
- `orchestrator/tests/test_artifact_admission.py::test_certified_view_rejects_non_exact_commit_count`
- `orchestrator/tests/test_artifact_admission.py::test_certified_view_rejects_negative_commit_count`
- `orchestrator/tests/test_artifact_admission.py::test_certified_view_rejects_commit_count_snapshot_mismatch`
- `orchestrator/tests/test_bench_first_real_wal.py::test_real_wal_replay_landscape_requires_commit`
- `orchestrator/tests/test_bench_first_real_wal.py::test_real_wal_replay_landscape_rejects_e1_without_commit`
- `orchestrator/tests/test_layer3_report.py::test_accepted_report_requires_e1_and_records_epoch`
- `orchestrator/tests/test_layer3_report.py::test_accepted_report_rejects_no_commit_campaign`
- `orchestrator/tests/test_layer3_report.py::test_certified_report_omits_current_verifier_conformance`
- `orchestrator/tests/test_layer3_report.py::test_render_accepted_persists_certifying_report`
- `orchestrator/tests/test_layer3_report.py::test_render_and_render_accepted_race_rejects_second_writer`
- `orchestrator/tests/test_t1286_commit_receipt.py::test_caller_built_serialized_receipt_cannot_become_replay_evidence`
- `orchestrator/tests/test_t1286_commit_receipt.py::test_cmd_evaluate_rejects_receiptless_result_from_exact_source_view`

duration ledgerへ親が追加する新規 collected nodeは次の7件です。

- `orchestrator/tests/test_artifact_admission.py::test_certified_commit_evidence_rejects_no_commit_campaign`
- `orchestrator/tests/test_artifact_admission.py::test_certified_view_checks_every_commit[both-commits-valid]`
- `orchestrator/tests/test_artifact_admission.py::test_certified_view_rejects_commit_count_snapshot_mismatch`
- `orchestrator/tests/test_artifact_admission.py::test_certified_view_rejects_negative_commit_count`
- `orchestrator/tests/test_artifact_admission.py::test_certified_view_rejects_non_exact_commit_count`
- `orchestrator/tests/test_bench_first_real_wal.py::test_real_wal_replay_landscape_rejects_e1_without_commit`
- `orchestrator/tests/test_layer3_report.py::test_accepted_report_rejects_no_commit_campaign`

## 裁定との食い違い

ありません。段2プランの外部 consumer 共通化案は裁定で不採用のため実装せず、裁定節9の2 consumer配線だけを実装しました。ledgerの duration未記入も、推定禁止と親実測指定に従ったものです。

## 総括

裁定どおり、全称保証を持つ admission viewと、commit存在保証を要求する consumer境界を分離しました。証拠母集合、anomaly即時拒否、epoch・overlay・token・exact型境界は維持されています。差分は未commitのまま作業ツリーに残しています。