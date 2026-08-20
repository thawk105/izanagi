---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t1310-formal-noncertifying-admission
seq: 1
---

## {{D:formal-noncertifying-admission-d510-integration}}. 正式 non-certifying launch admission mode は D510 の attempt registry へ完全統合する

**決定:** `trial_registry.py` に新設した `registered-formal-non-certifying` launch admission mode
(12 predicate 全部 SATISFIED の `EffectivePreregistration` を要求せず、`validate_condition_freeze_at()`
だけで凍結文書の生存を確認する) は、D510 の事前割当 attempt registry (genesis slot・
pre-observation classification・lifecycle) を **既存の `registered-effective` と共有する形で
完全に消費する。** certifying 用・non-certifying 用でslot poolを分離する設計は採らない —
`create_attempt_registry_genesis()` は manifest 単位で1回だけ生成され admission mode とは
独立した層にあるため、分離は構造的に不要である。

**理由:**
- 段3 敵対相談2レンズが、当初の親 provisional 裁定 (P1: 新モードは D510 の attempt registry を
  消費しない) を独立に refuted と判定した。D510 決定4は `certifying` フラグを適用条件にしておらず、
  `certifying=False` というラベルだけで事前割当・時点証明・pre-observation classification を
  回避する設計は、ラベルで正しさゲートを迂回する reward hacking 形であり CLAUDE.md 規律2 に
  抵触する (レンズA)。
- 同じ設計は技術的にも成立しない。「binding は持つが attempt slot は消費しない」状態は、
  run-start 生成・`_finish_trial()` が無条件に `attempt_slot.slot_id` を参照する既存前提と
  衝突し、admission 後の実行が構造的にクラッシュする (レンズB)。
- genesis の生成単位 (manifest 単位・1回限り) を実測した結果、certifying/non-certifying 間で
  slot pool を分離する新設計は不要と判明した。non-certifying 測定も観測である以上、その構成の
  slot を消費する — これは D510 の「観測済み値の差し替えを拒否する」規律と整合する
  (non-certifying で先に測った構成を、後で certifying として再測定することはできない)。

**却下した選択肢:**
- (P1) D510 の attempt registry を消費しない設計のまま実装する — 段3 2レンズが独立に
  reward hacking 懸念と実行時クラッシュの両方を指摘し refuted。
- certifying 用・non-certifying 用に別の attempt registry (別 freeze_id・別 genesis) を新設する —
  genesis が manifest 単位・admission mode 非依存の層にあることが判明し、分離の必要性が
  技術的根拠を失った。

正本 = `output/insights/2026-08-18_t1333-t1310-workload-profile/README.md` の R-01。
段4 裁定パッケージ・両レンズ所見の詳細は job dir
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1310-formal-noncertifying-admission/` の
`stage3-lensA-output.md` / `stage3-lensB-output.md` に保全済み。
