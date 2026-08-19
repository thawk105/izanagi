---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-test-bottleneck
seq: 1
title: 受入テストのボトルネック調査 — P3 4node除外はNO-GO、real-repo group帰属の実測法を是正した (docsのみ、branch worktree-dev-wave-test-bottleneck)
---

## 本文

- ユーザー依頼 (テスト全走のボトルネック解析・並列改善) を受け [T-989] の残件 (受入 wall への
  real-repo group 帰属未確定) を継続調査した。段2 codex plan (`REAL_REPO_SERIAL_NODES` の
  P3 loop 4node除外) を段3 敵対相談 2レンズ (正しさ境界・実効性) にかけた結果、両レンズとも
  独立に refuted/NO-GO — 除外の safety 前提 (temporary repo のみに触れる) 自体が誤りで、
  かつ親の実測 (`T_group=114.92s`) は critical path でなく単純 duration 合計 (S_group) だった
  (makespan の算術矛盾で発覚)。
- **実装しない。** D258 (2026-08-10) および D358 (2026-08-13、「real-repo 排他機構の変更で受入を
  速くする路線を閉じる」) が既に同じ結論に達しており、本 wave は独立な追加証拠として収束した。
- 詳細・一次資料は `output/insights/2026-08-19_test-bottleneck-real-repo-group/package.md`。
- codex 工数: 段2 plan 1本 + 段3 consult 4本 (書式不備で2本再投入、内容は不変)、
  合計 model_calls 約 190、wall_clock 合計 約 45分。

## 次の一手差分

### 更新

- [T-989] **P1・real-repoグループ部分除外はNO-GO (2026-08-19 追加調査)**: `_build_snapshot_base`
  の pack-objects 化 (2026-08-16) に続き、受入 wall への real-repo group 帰属を再調査した。
  P3 loop 4node の group除外案は段3敵対相談2レンズで独立に NO-GO
  (正しさ: 除外対象が実は親 repo に触れる。実効性: 親の測定法自体が critical path を測れていない)。
  D258/D358 が既に「排他機構の変更では受入は速くならない」と裁定済みであることとも整合する。
  **残件は変わらず未解決** — 真の worker-span 実測には一時診断の実装が要るが、D358 の先行実測
  (排他丸ごと無効化でも予測利得に届かない) を踏まえると投資対効果は不明。次に着手するなら
  worker_id/nodeid/start/finish の一時診断実装から。詳細は
  `output/insights/2026-08-19_test-bottleneck-real-repo-group/package.md`。
  base: 678123f34b580906d143aca643dfc750c67c9f5ce9b96919527be734a69bf352
