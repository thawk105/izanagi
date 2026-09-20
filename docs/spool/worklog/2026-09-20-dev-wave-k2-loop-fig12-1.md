---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-k2-loop-fig12
seq: 1
title: K2 手動 loop 3 巡のデータフロー図 fig12 (稿 2026-09-20 の説明図、値なし) を生成器・流れ JSON・test・README と共に着地する (コード + docs、branch worktree-dev-wave-k2-loop-fig12)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数、台帳 ID 未起票) の範囲で 1 wave: 稿 `results/2026-09-20-k2-manual-loop-three-rounds.md` (B-6 の材料) の 3 巡
  (提案 → 評価 → critic、実測の還流 2 回・診断の還流 1 回) のデータフローを、役割と遮断の所在、親が射影する入力 key、評価経路、還流の矢印、規律 6 の検査点だけの
  1 枚の説明図 fig12 にし、稿を caption_source として SHA-256 束縛する (F36 の形)。性能値は描かず、3 走を比較せず、知識・診断の因果効果を主張せず、B-6 の充足を
  判定しない。一次資料は `output/insights/2026-09-20/k2-loop-fig12/README.md`、図の正本は `docs/paper-story/figures/README.md` の fig12 節。
- **依頼文との差 (段 1 で実測、段 4 で確定):** 依頼の「役割 (planner-v4 / coder-v4-autonomous-k2 / critic、tool なしの構造遮断)」のうち critic は Bash を持つ
  legacy role (稿 §1.4・限定 3、B-4 非適格の理由)。図は planner / coder だけを「tools: [] の構造遮断 (tool access に限る)」、critic を「legacy with Bash」と区別して
  描き、生成器が role 定義の frontmatter を読んで JSON の宣言と一致することを検査する。
- 軽量版 (段 2・3 省略)。段 5 は Codex author 1 本 (生成器 + 流れ JSON + test、実データ生成 rc=0)。段 6 はレビュー 2 本 (A: 過剰・削除 + P1、NO-GO must 1 /
  B: 稿との逐語照合 50 + 7 + caption と正しさ境界、NO-GO must 3、不一致は提案日の「記録による」留保の脱落 1 件) → fix1 → 焦点再レビュー (closed 20 / partial 3 /
  regressed 0、NO-GO must 2 = caption の「3 回」誤読・検出 true 時の caption と凡例) → fix2 (caption の還流の文を固定、凍結図の矢印 7 組を定数で束縛、規律 6 の
  自己申告を typed bool に束縛)。全所見 real・採用、refuted 0。3 巡目の fix はしない (DW-O16)。
- (P1) 提案の backoff literal (20 / 25 / 20 / 10) と job id は識別子として描く。レビュー A の判定 (b) を採り、値は proposal cell に 1 度だけ `backoff literal <v>`
  として出し、caption で「literal であって結果ではない」と言う。
- 焦点走 (計算ノード dispatch): author 後 161 passed / 1 failed (期待赤 = 未着地 T9)、fix1 後 194 / 1 (job `12722`)、fix2 + docs 着地後 **309 passed / 0 failed**
  (job `12833`、README consumer test 2 本込み)。図は login (pegasus02、計測機の外) で生成 (15:02 JST、rc=0)。
- 変異 11 群 14 変異 + positive 1 (登録 worktree `mut-k2fig12`、docs 着地 commit `4e6e10ac1` に anchor、DW-M05 正本経路、dispatch 本走): **baseline PASSED、
  m0 SURVIVED、14/14 KILLED、期待 node 完全一致 14/14、MISMATCH / PARSE_ERROR / TIMEOUT 0** (計算ノード job 12855〜12958 の 17 本)。期待 node は
  login の probe (fix2 anchor) で集めた。M7 (publisher の layout 検査削除) の kill は T6 の 3 種だけで単一理由。等価変異 0。
- near miss 2 件 (逸脱台帳には載せない): (1) 焦点走 focus-3 は `run_tests.py` の login bounded local 試行中に親が `output/insights/` へ untracked file を作って
  作業木 digest が変わり、dispatch fallback を拒否 (rc=16、再投入 1 回で緑)。(2) 変異 probe 1 回目の node 抽出 regex がこの repo の failure digest 形式に合わず
  0 件 (regex を直して再 probe)。final 1 回目は非 ASCII param の nodeid escape で preflight 中止、collection の表記に直して final2。
- 工数: codex 6 本 (author 1、review 2、fix 2、focus 1)、計算ノード job = 焦点走 3 + 変異 (final2 の baseline + 15) + 受入。local main 4726b6493 を固定 SHA で
  前方 merge した (docs のみ)。

## 次の一手差分

### 新規

- {{T:fig12-successor-after-stock-control}} **P3・新規**: [T-2795] (同 job stock 対照) が裁定・実装され K2 手動 loop の次の巡が実走したら、
  fig12 の流れ JSON を上書きせず新 JSON + 別 filename の後継図 (`fig12b_`) で「同 job stock 対照あり」の巡を描く。稿 (凍結) と fig12 の bytes は不変。
  裁定前は起動しない。
