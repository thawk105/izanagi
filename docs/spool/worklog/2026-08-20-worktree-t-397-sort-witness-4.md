---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: worktree-t-397-sort-witness
seq: 4
title: '[T-397]/[T-410] wave 段8 — dev-wave改善候補2件を新規taskへ束ねて記録した (docsのみ、branch worktree-T-397-sort-witness)'
---

## 本文

- 段8 (`docs/skill-self-improvement.md`) を適用した。dev-wave 3層 docs は既知で予算満杯
  (`dev-wave-docs-compression-breaks-exact-pins` と一致) のため、即時の reference 節統合は
  試みず、候補記録のみに留めユーザー裁定へ返す。

## 次の一手差分

### 新規

- {{T:dev-wave-summary-heading-injection}} **P2・新規**: dev-wave の codex prompt 構築
  (`tools/dev_wave_codex.py`) が、`plan`/`consult`/`author`/`review`/`fix`/`focus` 全 stage の
  prompt へ「## 総括を末尾に置くこと」の instruction を自動注入する機械化を検討する。
  理由: 本 wave で親 (Claude manager) が2回 (段5 unit1、変異matrix裏取りの fix) prompt 本文への
  明記を失念し、`check_codex_output.py` の validator_rc=1 で accepted=false になった
  (実装内容自体は `git diff` で両方とも正しいと確認、親が逐語+見出し補完で採択)。
  F43 は codex 子側の内容欠落を扱うが、本件は親の prompt 作成側の失念であり型が異なる。
  機械化できる対応は機械化を優先する原則 (`docs/failures.md` 運用規則) に沿い、prompt 文言の
  再掲でなく tool 側の自動注入で再発を構造的に防げる可能性が高い。
- {{T:dev-wave-mutation-contract-loader-note}} **P3・新規**: `docs/dev-wave/mutation.md` に、
  変異対象 file が `orchestrator/campaign/campaign_lock.py` の
  `CONTRACT_LOADER_RELATIVE_PATHS` に該当する場合、`ratified_enforcement_source` autouse
  fixture (`orchestrator/tests/conftest.py`) を使う test file を変異matrix runner から
  除外する必要がある旨を追記できるか検討する (詳細は {{F:mutation-contract-loader-contamination}}
  参照)。P2 より優先度を下げるのは、機械検査でなく手順知識の追記であり、
  `docs/dev-wave/mutation.md` の byte 予算次第で reference への統合可否が変わるため。
