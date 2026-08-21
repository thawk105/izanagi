---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1393-finish-trial-indeterminate
seq: 1
title: '[T-1393] _finish_trial の crash 経路を registered trial 全体で indeterminate に統一した (コード+テスト、branch worktree-dev-wave-t1393-finish-trial-indeterminate、変異matrix = baseline PASSED・6/6 KILLED・SURVIVED 0・MISMATCH 0、受入 verdict=child-green)'
---

## 本文

- `_finish_trial` の workload/critic exception 経路が budget-tracked cell だけを indeterminate
  化し、それ以外の registered trial (budget 追跡なしの registered-effective、または
  registered-formal-non-certifying) は crash しても `status="partial"` のまま trial_registry へ
  記録され続けていた問題を、C04 (`docs/phase3-8c-preregistration.md` §6条件4、読むだけで無変更) の
  要求どおり一貫させた。設計判断は {{D:t1393-lifecycle-terminal-status-non-raise}}。
- 段3 敵対相談2レンズ (sol=正しさ境界、luna=整合/実効性/scope) が段2 codex plan の
  「formal acceptance 経路への影響は対応不要」という結論を強すぎると指摘し、新設テスト
  (indeterminate/not-consumed な report が formal acceptance で fail-closed することを確認する)
  の採用に至った。
- 段6 敵対レビュー2レンズと親の直接実走 (Codex 子は sandbox の socket 制約で pytest 実走不能、
  親が代行) により、新設テスト2件の初期実装に3件の設定ミス (attempt registry 直接 byte 書換えに
  よる event_sha256 チェーン破壊、registered-formal-non-certifying admission の
  condition-freeze 前提欠落、同モードの completeness/digest-chain 検査が未対応という既存の別問題
  ([T-1310] commit c1295565 が既に「明示されたscope境界でありbugではない」と記録済み) を
  発見し fix 3巡で解消した。
- 変異matrix (M1-M6、`docs/spool/decisions/2026-08-21-dev-wave-t1393-finish-trial-indeterminate-1.md`
  参照) は baseline PASSED・6/6 KILLED・matches_expectation=true 全件一致。受入全走は
  `verdict=child-green`、red/flake nodeids ともに0件。
- provider-init 失敗 (`run_trial` 自身の except が `_finish_trial` 呼出し前に `fatal_error` を
  事前セットする経路) は command 引数が明示する「`_finish_trial` の Exception 経路」の文字どおりの
  範囲外のため対象外とした。C04 の crash 解釈を provider-init まで広げるかはユーザー裁定へ返す。

## 次の一手差分

### 完了

- [T-1393] `_finish_trial` の crash 経路 (workload/critic exception) を registered trial 全体で
  indeterminate に統一するコード+テストを実装し commit `10b04fa3` として記録した。受入
  verdict=child-green、変異matrix 6/6 KILLED。
  remaining: none
  base: 1062e61e61194893fee634d395c4d7880f735761f61afcc600320a24d39a30f2

### 新規

- {{T:t1393-provider-init-indeterminate-scope}} **P1・ユーザー裁定待ち**: C04 の「crash 時の扱い」
  が provider-init 失敗 (`run_trial` 自身の except、`_finish_trial` 呼出し前に `fatal_error` を
  事前セットする経路。`test_m26_manifest_binding_survives_provider_init_and_supervisor_failures`
  の `provider_report` 側) も含むと解釈すべきかを裁定する。含めるなら
  `_finish_trial` の Exception 経路に限定した本 wave (T-1393) の scope を拡張する後続 wave が要る。
- {{T:formal-noncertifying-completeness-support}} **P2・新規**: `orchestrator/campaign/
  autonomous_trial_completeness.py` の `_check_launch_admission_projection`/
  `_check_arm_digest_chain` が `registered-formal-non-certifying` モードを認識せず、
  completeness/digest-chain 検査を有効にした状態で同モードを実走すると必ず失敗する。
  [T-1310] が既に scope外・既知事項として記録済みだが (commit c1295565)、正式対応する
  後続 wave が未着手。
