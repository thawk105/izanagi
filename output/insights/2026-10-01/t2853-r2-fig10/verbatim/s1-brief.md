# 段 1 brief — [T-2853] R2 fig10 (2026-10-01 JST、親)

- 研究前進: 再現パッケージ (VLDB EA&B 投稿時に要る) の R2 単位のうち fig10 (B-7 fixed 5 µs × 3 workload) を現行 driver で測り直し、原 attempt と並べた表と同じ生成器の R2 図を残す。完了判定 = 3 request の完走/未完走の事実・certification・表・図 (または生成器の拒否の事実) が insight にあること。
- 確定済みユーザー裁定: D2305 項 9 (fig10 の 3.40 node 時間を承認、1 図 1 タスク、生成器対照の本走を追い越さない)。
- scope: 本題の再実行と記録だけ。driver・policy・生成器・既存図・原 attempt 成果物は編集しない。他の図に進まない。gate・検査・台帳・一般化を足さない。
- 不変条件: 規律 1 (正しさは trace 有効 build の別走、性能は trace 無効 build)、規律 2 (anomaly の cell は即 reject、検査を緩めて描かない)、規律 7 (原 attempt は凍結物のまま、R2 と合成しない)。
- 既存被覆: 前例 fig11 (`output/insights/2026-09-29/t2853-r2-fig11/`)・fig6 (`.../t2853-r2-fig6/`) の形をそのまま使う。fig10 は workload 3 本 (3 request)、生成器 `plot_b7_fixed5_regression.py` が attempt id と結果稿から写した床値判定を定数で持つ点が前例と違う。
- 実測した前提: CCBench pin `6810666` に static backoff patch が当たる (precheck rc 0)、third-party 5 本 pin 一致、待ち行列に izs4loop 無し (10:29 JST)、原 attempt は 5 node × 3 request・Elapse 386/841/1,218 s・pin `511c953`・source `c18a80967`。
- 成果物: `output/insights/2026-10-01/t2853-r2-fig10/README.md` (§0 は投入前 commit `e92aeea8f`)、verbatim/、figures/ (R2 図・provenance・対照表)、spool fragment。
- 分割: 計測 (親、driver) と描画 wrapper (Codex author 1 本、repo 外へ退避する使い捨て)。段 2・3 は省く (形は前例と §0 で固定済み、設計択一は (P1) だけで段 6 レビューで攻撃させる)。段 6 は read-only レビュー 2 本 (一次資料照合・正しさ境界 / 過剰・削除)。
- (P1) 親の provisional 裁定・攻撃対象: R2 の「記録された判定」は、親が collect 後に certification の effects と pin された floor 3 file から生成器とは別の計算で出し、insight dir の小さな JSON (`r2-recorded-judgment.json`) に記録して wrapper へ渡す。wrapper は入力から判定を計算して定数にしない (自己照合にしない)。
- (P2) 親の provisional 裁定: R2 の certification / raw-manifest の sha256 は collect 後に親が insight に記録した値を wrapper の CLI 引数で渡す (入力 file から wrapper が自己計算しない)。
- 受入・実測環境: 計測 = Pegasus gen_S (driver の既存経路)。受入全走 1 回 (DW-S04、縮小不可なら全走)。変異 matrix は repo の実装面差分 0 なら免除 (DW-S04)。
