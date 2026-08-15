---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1132-model-routing-luna
seq: 1
title: codex model routing (sol→luna) 再検討 — 段2/5拡張の「下流検査で安全」論法はD207で不成立、実装せず裁定パッケージへ返す (docs のみ、branch worktree-dev-wave-t1132-model-routing-luna)
---

## 本文

- 起点はユーザー依頼「gpt-5.6-sol 使用箇所を luna max へ、品質がほとんど変わらないなら置換」。
  2026-08-08 の D241/D242/D243 とほぼ同一だが、今回は段2(plan)・段5(author) を含む新 scope
  (D241 は段3限定)。
- 段2プラン (codex sol, reasoning=max, read-only) が I3 (段2/5と段6の model 分離) を解く実装案を
  file:line 粒度で提示。段3敵対2レンズ (codex sol/luna, reasoning=max, read-only) は
  **独立に NO-GO で一致**。
- **核心の反論 (両レンズ独立到達)**: 「段2/5は下流 (段3敵対相談・段6敵対レビュー+変異matrix+
  受入全走) で独立再検査されるから、証拠なしでも model を変えて安全」という brief の論法は、
  D207 が段2プラン起草の effort 引き下げ提案を却下した論法と同型
  (「起草物は後段が必ず攻撃するので安全に見えるが、弱い起草が must-fix と fix 巡回を増やし、
  消費と正しさが同時に悪化する経路を排除できない」)。「検出力を下げる変更は規律2の対象」という
  D207 の一般原則は model 軸にも及ぶ。sol→luna の品質同等性を示す証拠は段2・段3・段5のいずれにも
  無い (認証済み A/B は段6 focused review の high 対 max だけで model 比較ではない)。
- 手続き上も、段4 (親裁定) には D241 の該当部分 (段2/5/6=sol の明示固定) を supersede する権限が
  無いとレンズが指摘 (`DW-S04` の裁定権限は real/refuted と scope 裁定、scope外real所見の
  裁定パッケージ化まで)。
- 段4裁定 (親): **「実装しない」(4→7→8→9)**。段2/5のmodel変更はscope外real所見として
  裁定パッケージ化しユーザーへ返す。段6 effortのhigh→max案・flip trick案 (docs 1行の近道に
  見えたが145箇所のlane呼び出しの意味逆転footgunがあり既存check_docs pinにも拒否される) は
  いずれも不採用 (両レンズ一致)。
- brief自身の「T-184/T-189がともに未着手」は不正確と両レンズが独立に指摘 (refuted部分)。T-184は
  reasoning軸を採用済みで resource/retry軸だけ残る。未着手なのは T-189 (model-routing の妥当な
  比較実験の設計) だけ。正確な記述は「段2/5の品質同等性を示す証拠が無い」。
- 材料の正本 = `output/insights/2026-08-16_t1132-model-routing-luna/` (brief・段2プラン・
  段3レンズ2本の逐語、裁定パッケージの択も記載)。
- エージェント工数: codex 子 3 本 (plan 1・consult 2)、すべて `check_codex_output` 受理。
  3 本とも read-only sandbox で pytest 非実走を正しく申告。I1/I2 の実在と段5 effort が
  意図的に unbound (pin なし) であることは、親が `tools/dev_waves/launch_authority.py:385-404` と
  `orchestrator/tests/test_dev_wave_launch_authority.py:90-109` を直接読んで実測確認した。
  編集は一切していない (worktree clean)。

## 次の一手差分

### 新規

- {{T:model-routing-luna-scope-ruling}} **P2・要裁定**: 段2(plan)・段5(author)のcodex model を
  証拠なしでsol→luna (reasoning は現状維持) へ変更してよいか。択は (a) T-189 を正式起票し
  妥当な比較実験 (held-out複数task・paired・blind・事前登録済み非劣性margin) を先に設計・実行する
  (親の推奨)、(b) 証拠なしで段2/5限定・既存effort維持のmodel-only swap実装waveを明示指示する
  (D241の段2/5部分を supersede するユーザー裁定として扱う。実装は
  `tools/dev_waves/launch_authority.py` の v1/v2 分割 (legacy receipt 互換込み)・
  `tools/check_docs.py` pin更新・`DW-M01` 変異7カテゴリ拡充が要る中規模実装wave)、
  (c) 現状維持。詳細は `output/insights/2026-08-16_t1132-model-routing-luna/README.md`。
  成果物影響 = 未裁定でも現状動作に影響なし (段3/段6のmodelは今回のいずれの案でも不変)。

- {{T:land-lacks-stage6-evidence-gate}} **P3・新規 (副産物)**: `tools/dev_wave_land.py` の
  受入判定 (`dev_wave_land.py:66`, `:123`) は acceptance receipt と provenance だけを見ており、
  段6敵対レビュー・変異matrixが実施された証拠 (review/focus receipt、所見裁定、mutation ledger)
  をland APIが要求しない。今wave固有の穴ではなく既存の手続依存だが、記録が無かったため新規登録。
  成果物影響 = 未対処でも即時の被害はないが、段6実施を経ずにlandする経路が機械的には塞がれていない。
