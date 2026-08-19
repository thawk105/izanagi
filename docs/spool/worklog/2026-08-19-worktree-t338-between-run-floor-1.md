---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: worktree-t338-between-run-floor
seq: 1
title: '[T-338] 投入gate 単位1(manifest/binding/Git基盤)・単位2(受領証IO/schema)を実装した (コード + テスト、branch worktree-t338-between-run-floor、変異 matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 一次資料は `output/insights/2026-08-19_t338-submission-gate-unit12/package.md`。
- 段2 codexプラン起草・段3敵対相談2レンズ (正しさ境界・整合実効性) を経て、段4で親裁定した。
  両レンズが独立に、D550型の二段束縛 (anchor commit) を構築する入力経路が計画に無いこと、
  schema loaderがcaller-selectableな`ref`を受け取る形になっていること、fd相対IOのpath
  traversal防御が計画に明記されていないこと、`blobref.py`のwrapper化が既存monkeypatchベース
  testと例外契約を壊しうることを収束して指摘した。プランv2をこれらの修正込みで確定した。
- 段5 (2並列codex author、専用worktree) で単位1・単位2を実装 (production 2,040行・test 945行)。
  段6敵対レビュー2本 (裁定準拠監査・独立コードレビュー) がreal所見11件を検出し、fix1で解消した。
  fix後の焦点再レビューが、fix1自身の作った新規regression (受領証の再帰凍結がjsonschemaの
  exact型判定と衝突し正当な受領証まで拒否される機能回帰、FIFO負例テストのhangリスク) を検出し、
  fix2で解消した (実測: 66 passed, 0 failed)。設計判断は {{D:t338-gate-unit12-opaque-capability}}
  を参照。
- 変異事前登録7件はいずれも実コードとの照合でparametrize test の実node ID・複数testでの
  同時検出が判明し、spec を2回補正した (単一理由性の検証としては正しく機能した — 想定より
  広く効く2件はいずれも多重防御の確認であり、SURVIVED (真の見逃し) は最終的に0件)。

## 次の一手差分

### 更新

- [T-338] **P1・単位1/2実装済み → 単位3以降が残る**: Q-A/Q-B/Q-Cは全問確定済み (archive
  worklog-phase3-0819-676)。本waveでD509決定(7)の依存順序 (`1||2 → 3,4 → 5 → 6`) に従い、
  依存のない単位1(manifest/binding/Git基盤)・単位2(受領証IO/schema) を実装した。
  単位3(semantic validator+申告値拒否専用化)・単位4(全履歴検査+attempt authority)・
  単位5(writer+conformance vectors)・単位6(統合+4名前export) は依存未充足のため本wave対象外。
  Q-B(必須kill3件はvalidator/consumer段の責務)・Q-C(B1は単位3のreject-onlyで閉じる) を
  単位1/2のインターフェース・docstringへ先取りしてある ({{D:t338-gate-unit12-opaque-capability}})。
  次wave以降は単位3・単位4の実装から着手する。
  base: 2e067cbc59c13094965c392b09439eefdc607c400af0a1cf478180b25186e0a7
