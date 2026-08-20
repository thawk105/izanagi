---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1420-c01-holdouts
seq: 2
---

## {{D:c01-holdouts-dormant-check}}. C06 holdout集合cross-checkは現状非実行到達のまま先行実装する

**決定:** `p3_autonomous_workload_trial.py`の`_prepare_s8c_budget_inputs`に追加した
ratified freezeとC05 scheduleのholdout ID集合cross-check (`ratified_freeze.holdouts`の
genuine dot-attribute消費) は、`_load_s8c_schedule_authority`(C05、未実装のため常時raise)
より後段にあり現行実行では到達しない。この非到達性を解消する再配置・C05実装の前倒しは
行わず、静的到達性のみを要求するC01契約 (`static_only_note`: "no run output is required")
を満たす先行実装として受け入れる。

**理由:**
- 同じ関数内で既に確立している`.sha256`消費 (`manifest.sha256`等) も、同じ
  `load_ratified_freeze()`呼び出し (repo全体でv2世代が未活性のため常に
  `RatifiedFreezeError("no-active", ...)`で失敗する) より後段にあり、同じ意味で
  現状非実行到達である。新設コードだけを特別扱いして再配置する理由がない。
- `_load_s8c_schedule_authority`のdocstring「C05の schedule 正本を要求する。未実装の
  hashは推測しない。」が示すとおり、C06予算経路全体が意図的な staged scaffolding であり、
  この一部分だけを実行到達させるための変更はC05側の別waveの scope。
- cross-check自体はdecorativeではない — 到達すれば`AutonomousTrialError`を実際に送出し
  `reserve_all_cells`への到達を止める。`candidate_id`をexact一致で検証する
  `.holdouts`propertyと組み合わせることで、`{H1,H2}`集合比較が恒真にならない
  (段6敵対レビュー2レンズが独立に指摘、fixで解消)。

**却下した選択肢:**
- schedule検証の前に配置する — `load_ratified_freeze()`自体が repo 全体で現状必ず
  失敗するため、位置を変えても「現状非到達」は解消しない。
- `_load_s8c_schedule_authority`を本waveで実装する — C05は別条件・別waveの scope
  (command引数が明示的に除外)。
- cross-checkの追加自体を見送る — 契約JSON
  (`s8c_preregistration_evidence_contract.v1.json`condition_number=1)の
  `required_evidence[1].field_paths`が`load_ratified_freeze().holdouts`を明記しており、
  genuine attributeとして露出・消費しないとC01のgapが閉じない。
