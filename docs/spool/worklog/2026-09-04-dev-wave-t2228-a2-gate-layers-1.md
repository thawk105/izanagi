---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2228-a2-gate-layers
seq: 1
title: [T-2228] A-2 経路で関門の 2 層目以降が実体で発火した — その先の identity 判定が新しい層として出て、既完走 4-cell は fixed backoff を測っていなかった (テスト + insight、branch worktree-dev-wave-t2228-a2-gate-layers、変異 7/7 KILLED + 旧 HEAD 6 SURVIVED)
---

## 本文

- ユーザー依頼は「A-2 経路で関門の 2 層目以降が一度も実行されていない件を直し、実体を名指しした正例・負例で確かめ、
  既完走 4-cell (reject) への影響を報告する。稼働中の T-2226 と編集面が重なるなら着手前に報告する」。
  起動時に T-2226 (同じ inert 経路) と重なると判定して報告し、着地 (95a3f02ae) を待って local main 396dc8988 から始めた。
- **関門は最後まで発火した。** production 入口から attempt `t2228-20260904a` を投入し、両 workload で cell-1 の腕・family 判定・
  admission・receipts・campaign (2 cell、anomaly 0) が実体で走った。record 単位の reason code は driver が campaign 後に落ちたため
  残っておらず、段 2 の静的予測は予測として凍結した。
- **関門の先で新しい層が出て、裁定へ返した。** `_raw_cell_from_wal` の canonical 判定は adopted cell の src_token を `stock` 前提に
  しており、patch が効いている木では必ず赤になる (両 workload とも `driver_rc=2`)。受理集合と proof 参照に触るため実装せず、
  推奨 (pin + patch に束縛した src_token を canonical にする) を裁定パッケージに書いた。
- **既完走 4-cell (T-2022 attempt c) は fixed backoff を測っていなかった。** 当時の driver は patch 無しの木を渡し、adopted の
  `BACKOFF_FIXED` は無視され、`BACK_OFF=1` (内蔵指数 backoff) だけが効いていた (当時の WAL の src_token が adopted でも `stock`)。
  F707 の再発として記録した。規律 7 に従い bytes は変えず、追記による訂正を裁定 2 として返した。今回 patch 済みで測った adopted は
  stock より速い (rr5 +53.8%、rr50 +10.5%) が、raw 化に失敗した attempt の campaign log 値であり certified ではない。
- 実装は test 1 file (Codex author)、production 差分ゼロ。段 3 相談 2 本は「(P4) の『admission 未実行』は誤り (cell-0 の family
  判定は旧経路でも実行されていた)」を含む real 所見を出し、brief を訂正した。段 6 review A の must-fix 4 件はすべて変異登録の
  再照準 (既存テストでも落ちる変異) で、コード fix はゼロ。review B は must-fix 0。
- main の取り込みで T-2227 (同じ test file と driver の関門文脈) と競合した。clean な wave 木で Codex fix 子に
  「main 版 + 新 test (T-2227 追随)」の最終形を書かせ、親が固定 SHA の merge 内で採用した。merge 後の焦点走は緑、
  最終 tip の変異は 7/7 KILLED、旧 HEAD 版は M1〜M6 SURVIVED (新 test だけが検出)。
- 計算ノード: A-2 attempt 2 job (各 約 52 分)、焦点走 3 回、provenance 監査、変異 probe 4 回 (3 回は queue 待ち 900 s で rc=16) と
  本走 2 回 + 旧 HEAD 版 2 回。gen_S の混雑 (QUE 250〜300) で約 8 時間待った。詳細は `output/insights/2026-09-04_t2228-a2-gate-layers/`。
- 段 8 の改善候補 3 件: (a) 隔離 session の guard は計測投入・Monitor ループにも `.sh` 外出しを要する、
  (b) 変異登録時に既存テストが同じ変異を捕まえるかを静的に見る、(c) harness の collection 段と provenance checker に
  D612 の上書きが届かない。(a)(b) は L1 / L1.5 の byte 予算で docs へ入れず memory へ寄せ、(c) は実装面なので
  裁定パッケージの裁定 4 へ送った。

## 次の一手差分

### 更新

- [T-2228] **P2・進行中**: A-2 経路は関門を通ることを実測で確認した (attempt `t2228-20260904a`)。残りは
  `backoff_sweep` / `backoff_repro` / `s1_direct_comparison` の inert 経路が driver ごとに実際に通るかの実測。
  base: bbefddbf9776c8a9564b9b97f47932606729b39b4a45abdf084d543118c05fd8

### 新規

- {{T:a2-canonical-variant-src-token}} **P1・ユーザー裁定待ち**: A-2 の `_raw_cell_from_wal` が adopted cell の canonical
  variant を src_token `stock` 前提で計算し、patch が効いている木では必ず赤になる。pin + patch に束縛した src_token を
  canonical にして raw / report に記録する案 (推奨) を含む 3 案を裁定パッケージに出した。実装後に A-2 を取り直す。
  裁定 3 (receipts の campaign 前保存) も同梱するかを決める。
- {{T:t2022-a2-reject-addendum}} **P1・ユーザー裁定待ち**: T-2022 attempt `t2022-20260828c` の reject は patch 無しの木で
  `BACK_OFF=1` vs `BACK_OFF=0` を測ったもの (F707 再発)。規律 7 に従い、当該 insight に測定条件の実体を追記し、
  論文素材から A-2 の結論を取り直しまで外す案を裁定パッケージに出した。
