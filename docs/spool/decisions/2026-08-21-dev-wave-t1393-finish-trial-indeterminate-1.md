---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t1393-finish-trial-indeterminate
seq: 1
---

## {{D:t1393-lifecycle-terminal-status-non-raise}}. registered trial の crash は raise ではなく report フィールドで indeterminate を表現する

**決定:** `_finish_trial` の workload/critic exception 経路 (`orchestrator/campaign/
p3_autonomous_workload_trial.py`) で、registered trial (`launch_admission.binding is not
None`) が budget-tracked flow 外で crash した場合、既存の `budget_ledger_path is not None:
raise AutonomousTrialError(...)` (2箇所、無改修) とは別に、`report["lifecycle_terminal_status"]
= "indeterminate"` を条件付きで追加する非 raise 方式を採用する。`report["status"]` は
"partial" のまま変更しない。`trial_registry.forbid_trial_restart` はこの新分岐から呼ばない。

**理由:**
- `run_origin_trial` は「never raises failures」契約で `run_trial` の例外を捕捉し、
  `run_root/"report.json"` を disk から読んで `OriginPartialTrialReport` を返す。`_finish_trial`
  が raise で早期離脱すると report.json 書込み (`_write_json_atomic`) 前に離脱してしまい、
  `outcome.report is not None` という既存契約 (`test_origin_public_result_distinguishes_partial_
  from_completed`) を壊す。registered trial は origin 経路と共存しうるため、既存の
  budget-tracked crash の raise パターンをそのまま複製できない。
- `report["status"]` を "partial" のまま保つのは、既存の `_budget_indeterminate_report`
  (budget-insufficient 早期return、`status="partial"` + `lifecycle_terminal_status=
  "indeterminate"` の組) と同じ二層フィールド規約に倣うためであり、新しい status 語彙を
  増やさない。
- `forbid_trial_restart` を呼ばない判断は、`trial_registry.record_trial_start_once` の
  start-once 検査 (`append_start`) が trial_id 単位の再 start を既に無条件拒否すること、
  および `forbid_trial_restart` 自身の docstring が「durable な start/indeterminate terminal
  row が cross-process の再走拒否証拠であり、この関数は in-process capability flag に過ぎない」
  と明記していることに基づく。
- C04 (`docs/phase3-8c-preregistration.md` §6条件4、凍結 §1-4/6/7 は無変更) の機械評価器
  `_evaluate_c04` は `mark_experiment_indeterminate`/`forbid_trial_restart` の declared-call
  reachability だけを見る静的検査であり、既存の budget-tracked crash 経路で既に到達可能なため
  本決定による verdict の変化はない。本決定の価値は評価器の verdict を動かすことではなく、
  実際の runtime 挙動を C04 の prose 要求 (crash → 実験全体 indeterminate・再走差別化) に
  合わせることにある。

**却下した選択肢:**
- 既存の budget-tracked crash と同じ raise + `mark_experiment_indeterminate` 方式を registered
  trial 全体へ拡張する — origin 境界の report.json 依存契約を壊すため不採用。
- `report["status"]` 自体を "indeterminate" に変更する — 既存の二層フィールド規約 (status は
  producer/public 境界の表現、lifecycle_terminal_status は運用終端) から外れ、"partial" を
  期待する既存 assertion 群を反転させる必要が生じるため不採用。

**scope 境界 (裁定待ち・裁定不要それぞれ):**
- provider-init 失敗 (`run_trial` 自身の except が `_finish_trial` 呼出し前に `fatal_error` を
  事前セットする経路) は本決定の対象外とした。ユーザー裁定待ち。
- `autonomous_trial_completeness.py` の `_check_launch_admission_projection`/
  `_check_arm_digest_chain` が `registered-formal-non-certifying` モードを認識しない既存の別問題
  (T-1310 commit c1295565 が既に scope外・既知事項として記録済み) は、本決定の production 差分と
  無関係のため対応しない。新設テストは既存の同モードテストと同じ monkeypatch でこれを回避した。
