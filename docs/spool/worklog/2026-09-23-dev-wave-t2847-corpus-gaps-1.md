---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: dev-wave-t2847-corpus-gaps
seq: 1
title: [T-2847] 残り (1) — 小履歴コーパスの未被覆 F03・F06 と B06 の分類 G1c を手導出の期待値の test にした。3 test とも現行 verifier で緑 (欠陥なし)、変異 9 / 9 が期待と一致し、新 test だけが検出したのは B06 の分類の壊れ方 1 件 (F03・F06 型の 5 形は既存 test も検出) (test + insight、branch worktree-dev-wave-t2847-corpus-gaps)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = `output/insights/2026-09-23/t2847-corpus-gaps/verbatim/request.md`): 設計 `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` §3・§3.1 の未被覆 2 案と B06 の分類 assert を、新規 test file の合成 trace で実装する。記録 = `output/insights/2026-09-23/t2847-corpus-gaps/README.md`。
- 起点 = local main `cadaf3805` (fresh worktree、開始 gate rc 0)。verifier・既存 test・fixture は触らず test を足すだけで受理集合も変わらないので、DW-C00 の軽量版 (段 2・3 と段 6 review 子を省く) で進めた。実装は Codex author 1 本 (gpt-6-astra/medium、13 call、約 4 分)、実装 commit `d0ed93bab`。
- 結果: 3 test とも現行 verifier で緑。期待と合わない箇所は無く、欠陥の記録は無い。
- 変異 (段 4 で M0〜M4 を事前登録、login probe 1 巡目で M1〜M4 が既存 `test_verifier.py` にも捕まったので DW-M08 に従い M5・M6・M8・M9 へ再照準): 計算ノードの本走 (独立 clone の固定 commit `d0ed93bab`) で 9 / 9 が期待 node と完全一致、基準走 PASSED。**新 test だけが検出したのは M5 (wr だけの巡回を G1c にしない分類器) の 1 件。** F03・F06 型の 5 形は既存の凍結 hash・実データ fixture・同じ key を違う版で読む境界 test (辺の隣接を具体値で固定) も検出した。設計書が別の意味と数えた境界 test が、試した壊れ方の範囲では F06 型の壊れ方を捕まえる (insight §1 項 4)。
- 計算: 変異本走の runner 時間 293.4 秒 (10 run) と collection の dispatch 1 回。受入全走は本記録の commit の後に行い、結果は land の受領証に残る。login: test_verifier.py の自走 14 回 (各約 8 秒) と新 test の自走。
- 並走: (2) は `t2847-patch-verify`、(3) は容量実測の wave が担当 (依頼どおりの分割)。T-2847 の項目の更新は、land の前に相手の着地を見て base を取り直す。

## 次の一手差分

### 更新

- [T-2847] **P1・設計済み (VLDB 差分分析 P0: 検証の意味と容量)**: 計算なしの設計を insight `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` に記録した — 判定の範囲 (§2)、小履歴コーパス 27 案 (§3)、CC 変異 34 と無改変 si 1 の検出期待表 (§4、族 26・変更機構 22)、既存 broken patch 16 本の現行 pin への適用可否と記録 (§5.1)、si の v1 拒否 (§5.3)、容量評価の計画と [T-2351] との関係 (§6)、論文用の射程文 (§7、済)。(1) コーパスの未被覆 2 案 (F03・F06) と B06 の分類 `G1c` の test は済 (`orchestrator/tests/test_verifier_corpus_gaps.py`、記録 = `output/insights/2026-09-23/t2847-corpus-gaps/README.md`。新 test だけが検出した変異は B06 の分類の 1 件)。
  残り = (2) 変異の実走 (§4。既存 16 本は既存 driver、新規は D16 第 3 類の out-of-tree patch)。(3) 容量の実測 (§6.3。まず VLDB の実験が検証する trace の長さを計算なしで決め、既存の実測範囲 = write-heavy / balanced 10 s・read-heavy 6 s・巡回 0 の外だけを測る)。(4) si の emitter の v2 化 ([T-2854] の実装単位 (12) に相乗り)。完了 = 検出表の実測と容量の実測表。
  計算: (2)・(3) はいずれも、同じタスクで投げる job の合計 (開発の検査を含む) が 2 node 時間以上なら投入前に見積りを示してユーザー確認 (D2212 項 4、D2219 項 1)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P0。
  base: a591c8df658eb81a100c16de9c5f4801e339822022da6a90b3cea9efbb46c95c
