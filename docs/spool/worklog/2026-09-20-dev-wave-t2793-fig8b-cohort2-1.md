---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2793-fig8b-cohort2
seq: 1
title: [T-2793] fig8 の再現欄付き後継図 fig8b (主結果 cohort 1 + 独立再現 cohort 2 を縦 2 block で併記) を生成器の --reproduction-cohort 2 経路で作り、3 成果物と README 節を着地した (コード + docs、branch worktree-dev-wave-t2793-fig8b-cohort2)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数の逐語は insight `verbatim/T-2793-origin.md`) の範囲で 1 wave。一次資料は
  `output/insights/2026-09-20/t2793-fig8b-cohort2/README.md` (brief・plan・裁定・相談/レビュー/fix の逐語・変異台帳・走記録)、
  設計判断は {{D:fig8b-reproduction-column-two-blocks}}。専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2793-fig8b-cohort2/HANDOFF.md`。
- 起点 local main `b7f970dfa`。brief 前の実測: repo 外の両 cohort 6 file の SHA-256 が両稿 §4.1 と全件一致、現行 loader に定数を差し替えると
  cohort 2 を受理 (verdict・24 cell・job・比 0.445 / 0.484 / 0.398・18/18 declining・L 0.2782〜0.3732 が cohort2 稿 §2.2 / §2.3 と一致)。
- 段 2 plan は親起草 (file:line、行番号は誤りが多く consult が現物アンカー表で訂正)。段 3 consult 1 本 (2 レンズ) は must-fix 5 / should 6 /
  nit 4 を出し全件採用 (refuted 0): v2 caption の行説明 (A1)、v1 の受理集合不変 = 図番号の英字 suffix は v2 経路だけ (A2)、publish 経路の
  caption 切替 (B1)、block 見出しの panel 侵入検査 (B2)、変異ごとの独立した根拠 (B3)。CLI は `--cohort 2` から `--reproduction-cohort 2` へ変更。
- 段 5 は Codex author 1 本 (生成器 +163 行、test +242 行、新 test 12 本)。段 6 レビュー 2 本 (A: 正しさ境界・言い方、B: 過剰・削除) は
  **must-fix 0 / GO ×2** (nit 2)。fix1 (Codex) は nit 3 件 (未使用定数、v2 CLI test の production pin 拒否 assert、下 block 見出しの余白) を
  closed。nit-only のため焦点再レビュー子は起動せず、親の test 再走・実データ再生成・PNG 目視で閉じた。既存 25 test の期待値は不変。
- 実装 commit `22b9deb58`、成果物 commit `864d7135e`。fig8b の 3 file は login node (pegasus02、08:00 JST) で生成し、provenance (schema v2) の
  generator SHA-256 は commit の生成器と一致。**凍結 fig8 の 3 file は生成前後で SHA-256 不変** (png `24eab2e8…`、pdf `11071b72…`、
  provenance `3ccdb0aa…`)。caption の値は両稿と一致 (cohort 1: 比 0.444 / 0.481 / 0.400、L 0.2738〜0.3704。cohort 2: 比 0.445 / 0.484 / 0.398、
  L 0.2782〜0.3732)。
- 検査: 自走 harness 37/37 (着地 test は fig8 / fig8b とも PASS)、計算ノード焦点走 (request 11883.nqsv、変更 test file + `test_plain_runner_coverage`)
  39 passed / 1 skipped (skip は着地前の fig8b 着地 test)、`check_docs` 違反なし、三軸語走査 holdout hit 0 (fig8b provenance は rr50 正例側の一般 hit)、
  `git diff --check` 緑、wave 区間の provenance 監査違反なし。
- 変異 matrix (等価対照 1 + 負例 11、独立 clone @864d7135e、計算ノード dispatch): probe2 (全件 SURVIVED 登録) で観測 node を集め、final で **baseline 緑・11/11 KILLED (期待 node 完全一致)・M0 SURVIVED・MISMATCH 0**。M3 (verdict の受理拡大)・M7 (見出し侵入検査)・M9 (下 block の取り違え)・M11 (位置 (cohort, role) 対検査) は単一 node で殺した。詳細は insight §5。
- 限界・言わないこと: 「1 ページに入る」は主張しない (描画寸法 7.2 × 10.6 in、掲載寸法の可読性は投稿テンプレートで確かめる)。closure v2 は
  provenance の自己再投影であって reps からの再計算ではない (実 root test が担う)。2 つの cohort の近さを一致度として評価しない。
  第 3 cohort の実施・地位は定めない。B-10 は閉じない。版 `2026-09-19.md`・results 稿・事前登録は変えていない (凍結)。
- 事故: 変異 probe の初回は spec `timeout_seconds=2700` が dispatch の待機契約 (queue 3600 + grace 600) より短く harness の preflight で中止
  (走行ゼロ、5400 / 3000 に直して再投入)。段 6 レビューの初回起動は launcher の `--reasoning` 指定が review 段で rc=2 (DW-C01 どおり、launcher を分けて再投入)。
- 工数: codex 5 本 (consult 1、author 1、review 2、fix 1)、計算ノード job = 焦点走 1 + provenance 監査 1 + 変異 (probe + final) + 受入。

## 次の一手差分

### 完了

- [T-2793] fig8 の再現欄付き後継図 `fig8b_b10_static_tail_cohort2` (3 成果物 + `figures/README.md` の節 + `tools/plotting/README.md`) を
  生成器の `--reproduction-cohort 2` 経路で着地した。主結果 cohort 1 と独立再現 cohort 2 は縦 2 block で区別して併記し、合成・プール・
  統合 verdict は無い。fig8 の bytes は不変。
  remaining: none
  base: 666d84c7ef587a9b57a18b17f9e96c0263e52bca267097394d0c1bc9c3fdebce
