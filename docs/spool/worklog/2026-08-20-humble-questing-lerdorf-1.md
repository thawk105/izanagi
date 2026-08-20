---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: humble-questing-lerdorf
seq: 1
title: "[T-189] model routing 比較実験の事前登録文書を作成した — D514後の exploratory pilot として設計、段3敵対相談2レンズ+段6敵対レビューが計33件の所見 (blocker15・major14・新規4) を検出、fix で全件反映した (docsのみ、branch worktree-humble-questing-lerdorf)"
---

## 本文

- command 引数は D423 (2026-08-16、「codex の plan/author 段の model を sol→luna へ証拠なしで
  変更しない、まず T-189 を正式起票し比較実験を設計してから判断する」) を前提としていたが、
  段1 brief 時点の実測で **D514 (2026-08-18) により dev-wave 全段が既に `gpt-5.6-luna@max` へ
  統一済み**(ユーザー裁定 T-1132/T-1133/T-1134、[T-1146] 裁定 (c) の「運用選好」ルートを経由、
  「品質同等性の証拠ではない」と D514 自身が明記) という新事実を発見した。D423 の原則自体は
  否定されていないが (D514 は D423 の rollback 条件と別ルートで先行しただけ)、T-189 の位置づけを
  「事前判断のための実験」から「既に先行した全 luna 化の品質リスクを事後検証する実験」へ更新し、
  この経緯を事前登録文書の目的節に明記した。decisions.md への新規記録はしていない —
  D423 の内容自体は書き換えておらず、既存決定が求める成果物 (妥当な比較実験の設計) を
  提出しただけである。
- 段2 codex プラン起草 (1本) が7要素 (paired/blind/held-out/独立oracle/block randomization/
  cache分離/価格version/margin) を満たす初稿を作った。段3 敵対相談2レンズ (統計的妥当性・
  運用実現性、計2本) が16件の real 所見 (blocker7・major9) を検出した。特に統計レンズが
  「20 positive task でも coverage margin -0.05 を検出できない」ことを二項信頼区間の算術で示し、
  運用レンズが「現実的な held-out task 候補は8〜10 task-stage程度で当初目標の24×2に届かない」
  「T-181装置 (`tools/codex_reasoning_ab.py`) の model 軸拡張は14箇所の軽微な変更ではなく
  横断的 refactor」「custodian 隔離・cache 制御は現行装置では実現不能」と file:line 実測で
  裏付けた。段4 で全16件を real・採用と裁定し、文書を「confirmatory」から「exploratory pilot」
  へ格下げする方針を確定した。
- 段4裁定を反映した文書を段6 敵対レビュー (1本) にかけたところ NO-GO で、旧版の設計 (same-owner
  や cache 未制御の結果でも quality/false-finding/fix gate を評価し rollback 材料として使える
  構造) が「探索的結果が事実上の品質証拠として一人歩きする抜け道」になっていると指摘した
  (blocker4件の中核)。他に blocker4件・major5件・新規所見4件 (計17件) を検出。
  `routing_evidence_status` を `confirmatory-go`/`confirmatory-no-go`/`inconclusive` の3値に
  限定し、same-owner・cache未制御の結果は別ラベル `apparatus_diagnostic` に隔離して routing
  判断・rollback材料に使わせない設計へ全面的に書き換えて fix した (§12 判定表が中心)。
  fix 後に親が通し読みで自己点検し、誤字1件 (簡体字混入) と用語不統一2箇所を追加修正した。
  2巡目のレビューは投げず (17件全件対応済み、自己点検でも新たな重大な矛盾なし)、ここで打ち切った。
- 成果物は新規 `docs/phase3-t189-model-routing-preregistration.md` (737行)。実験の実走・
  `qsub`・production の model routing 変更は D87 によりこの wave の scope 外であり、装置改修・
  downstream replayer 実装・custodian 実現・cache 制御実測・task catalog 実データ作成・
  price snapshot 実データ取得を「未解決点」として文書内に明示し、後続タスクへ引き継いだ。
  `python3 tools/check_docs.py` は違反なし。
- エージェント工数: codex 子4本 (段2 plan 1、段3 consult 2、段6 review 1)。計算ノード dispatch
  なし (docs-only のため受入全走・変異 matrix は対象外、DW-S04)。

## 次の一手差分

### 完了

- [T-189] model routing 比較実験の事前登録文書 (`docs/phase3-t189-model-routing-preregistration.md`)
  を exploratory pilot として作成した。段3敵対相談2レンズ+段6敵対レビューが計33件の所見を検出し
  全件を fix で反映した。実装・実走は {{T:model-routing-ab-pilot-implementation}} へ引き継いだ。
  remaining: none
  base: 0a7903d128351c3133843a2e38c45fca85c00be6173d552d398dc4bfc9ea290f

### 新規

- {{T:model-routing-ab-pilot-implementation}} **P1・[T-189] 事前登録文書の実装・実走**:
  `docs/phase3-t189-model-routing-preregistration.md` が明示する7つの未解決点
  (power simulation の実施と `N_positive_min`/`N_negative_min`/margin の最終 lock、独立
  custodian の実現方式確定、provider cache 制御可能性の実測、T-181 装置
  (`tools/codex_reasoning_ab.py`) の横断的 refactor、stage2/stage5 downstream replayer の
  実装、task catalog の実データ作成と独立分類者2名の確保、price snapshot の実データ取得) を
  満たしたうえで、D87 に従い qsub 等の人間手番で実験を実走する。
