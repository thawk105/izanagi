# 段 6 閉じの裁定 — 焦点再レビュー 1 (focus-review-1.md、NO-GO)

2026-09-30 01:12 JST / 親。対象 tip d109d4078。

- 既存所見 (review-a-1・review-b-1 の全所見、focus-1 の赤 2、focus-2 の赤 1、smoke1 の gate 拒否): 焦点再レビューが全件 closed (A1/B2 は refuted 維持、A3/B5 は partial = 下の新所見)。
- 新所見「trace job の見積りが 2 job の走数の和でなく max × 2 (driver:145-155, 183-185)」: **real だが nit へ降格 (DW-G05)**。
  - 向きは過大見積り (保守側)。smoke2 (bnode001、36606.nqsv) の trace 1 走 (build 除く、判定込み) = 16.52 s、走数は 14 と 5。
  - 現行式の合計 2,432.3 node 秒、裁定 §4 の式 (和) なら 2,432.3 − 9 × 16.52 ≈ 2,283.6 node 秒。どちらも閾値 7,200 を大きく下回り、選ばれる計画は同じ (6 round × 12 cell × 5 腕、縮小なし)。この wave の成果物 (図・表・受理集合) は変わらない。
  - 一次資料に式のずれと両方の値を書く。修正は後続 (この driver を次に使う wave) の backlog。
- よって段 6 の fix は閉じ、本走 (build1 → perf 3 / count 1 / trace 2) へ進む。受入の取り直しと変異 matrix は本走の結果を記録した後の tip で行う。
