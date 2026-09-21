---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2807-b8-effective
seq: 2
title: [T-2807] B-8 事前登録 v1 を発効し (D2194 項 1)、校正 3 job → 本走 6 job (extime 10 s、独立 8 反復 × 3 workload = 24 verify) を Pegasus で走らせて 3 値判定 `pass` を得た — 判定集合 30 枠すべて serializable・certified・anomaly 0、未完走・bench 失敗・規約不適合・再検証はいずれも 0 件、実消費 9,280 S ≤ 14,400 s (docs + insight、実装面 0 行、branch worktree-dev-wave-t2807-b8-effective)
---

## 本文

- 依頼 (D2194 項 1 の承認) を軽量版 9 段で処理した。段 3 相談 1 本 (high 1 / mid 5) → 段 4 裁定 (全件採用) → 発効 commit →
  校正 → 本走 → 判定 → 段 6 レビュー 1 本 (GO、must-fix 0 / should 2 / nit 1) → 記録。実装面 (repo 内のコード・テスト) の差分は 0 で、
  変異 matrix は `DW-S04` により免除。設計判断は {{D:b8-effective-and-longrun-verify}}、実測と逐語は
  `output/insights/2026-09-21/t2807-b8-effective/README.md`。
- **発効:** 事前登録 v1 (raw sha256 `6ccb18c7…`、bytes 不変) を発効 commit `624c84986` で発効した。発効束 JSON は前 wave の draft の
  実験構成値を維持し `status` だけを `effective` に置換したもの (sha256 `059536a7…`)。発効直前に pin・gitlink・patch・事前登録・
  verifier 9 file・`pipeline.py` の sha256 を HEAD の実体と照合して 15 項目一致 (NG 0)。**発効前に校正・本走は走らせていない。**
- **校正 (段 A、3 job、08:45〜09:11 JST、request 14640–14642):** 6 行すべて完走・`serializable`・certified・anomaly 0、
  verifier wall は最大 491.4 s (適格の上限 1800 s の内側)。適格集合は 3 workload とも {6, 10}、共通部分の最大 = **extime 10 s**。
  B(10) = 9,289.3 s ≤ 14,400 s で段下げ無し、`stage_B_allowed` = true。D2160 の校正 (案 B) では 10 s が未完走だったが、案 A は 3 workload とも
  10 s まで完走した (対象も verifier の版も違うので比較はしない)。
- **本走 (段 B、6 job、09:17〜10:13 JST、request 14686–14691):** 24 枠すべてが bench 完走・保全済み・verifier 完走・`serializable`・
  certified・anomaly 0・identity 一致。打ち切り・再投入・`--resume`・`reverify` は 0 回。verifier wall は write-heavy 295.3 s /
  balanced 219.2 s / read-heavy 496.4 s (平均)。trace は zstd で 22.924 GiB 保全 (本走前の外挿 22.833 GiB とほぼ一致)。
- **判定:** `summarize` の 3 値判定は **`pass`**。判定集合 30 枠 (本走 24 + 校正完走 6)、anomaly 0・失格 0・規約不適合 0・未完走 0・
  `not_run` 0。30 record すべてが規則 file と発効束の sha256 を持つ。費用は dispatch Elapse の和で段 B 9,280 S ≤ 14,400 s、段 A は別欄 1,920 S。
  **これで B-8 の 3 要件 (対象 = S-1 最終候補 / 種 = 独立 process の自己シード / 長時間 = extime 10 s) が揃った。**
  `pass` は規則の機械適用の出力であって研究の成功宣告ではなく、S-1 (iv 付属) の充足でもない。性能値は含まない。
- 成果物: 結果稿 `docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md` (限定 11 件)、insight (発効・校正・本走・判定・
  限定・レビュー対応)、論文ストーリー入口の stale 注記 (項目 3) と results 系列表の 1 行。日付版は凍結物なので編集していない。
  D2186 項 1 (2) が命じた仕分け (2) の限定 (「独立 process の自己シード」、seed 値は記録しない) は入口の stale 注記と insight §2 に書いた。
- 段 6 レビューは校正 6 record・本走 24 record・9 job を直接走査し、平均・範囲・保全量・予算・Elapse を独立に再計算して GO。
  should 2 (保全量の単位混在、集計 JSON の sha256 欠落) と nit 1 (入口の表現) を反映した。レビューが照合できなかった 2 点
  (本走前の `df` の生出力、submit-tree 再利用の直前確認の逐語出力を保存していない) は限界として insight §7.2 に残した。
- 工数: codex 子 2 本 (consult 1、review 1、いずれも read-only `gpt-6-astra`)、計算ノード job 9 本 (校正 3 + 本走 6、Pegasus gen_S、
  1 job 1 node、submit-tree 6 本)、親の login 実走は docs 検査 5 回・provenance 監査 1 回 (12,266 件・新規違反なし)。
  wave の壁時計は開始 gate 08:33 JST (`startup-gate.log`) から記録 commit まで。
- 受入全走と land の結果は本 entry には書けない (fold 後に確定するため insight に追記)。

## 次の一手差分

### 完了

- [T-2807] B-8 事前登録 v1 を発効し、校正 → 本走 → 3 値判定 (`pass`) まで運び、結果稿と論文ストーリー入口へ反映した。
  remaining: none
  base: d18ddaa7ab088fd7d4a60235c9c27426513db7df768f6fc3c4cfd858c947643f
