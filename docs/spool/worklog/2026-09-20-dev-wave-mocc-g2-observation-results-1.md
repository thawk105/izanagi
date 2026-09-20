---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-mocc-g2-observation-results
seq: 1
title: stock mocc の G2 観測条件の分離 ([T-2779] の観測、通常 5/120・診断 0/120・BACK_OFF=1 2/120) の単独 results 稿を 1 試行の一次資料全体から書き、README の results 表へ 1 行足した — 限定を先頭に置く非 certifying の観測記録、独立 read-only レビュー 1 本が must-fix 1 (thread id は生 trace にある) を出し全件反映 (docs のみ、台帳 ID 未起票、branch worktree-dev-wave-mocc-g2-observation-results)
---

## 本文

- ユーザー依頼は「mocc G2 観測条件の分離 ([T-2779]) の単独 results 稿 `docs/paper-story/results/2026-09-20-mocc-g2-observation-conditions.md` を書く
  (docs のみ、台帳 ID 未起票、backoff 診断を本体論文へ載せる材料)。着手直前の local main から fresh worktree。一次資料は [T-2779] insight と repo 外 job dir
  (runner v5・走ごとの JSON・G2 走の生 trace) — 生 trace を含む必要資料の充足を段 1 で実測し、欠けるものは『成果物に無い』と稿に区別して書く。
  限定を最初に置く (非 certifying・TRACE=1 観測専用・pin 前進なし D2159、頻度差から backoff の抑制効果や正しさを結論しない、G2 signal の再現を
  根因確定としない = [T-2791] の限定)。[T-2611] / [T-2674] の型。README の results 表へ 1 行、README は owned-path に入れない。段 6 は独立 read-only
  レビュー 1 本 (D2148 項 11)。規律 2 を緩めない。本題の稿だけ」。
- **稿を作成した。** 成果物は `docs/paper-story/results/2026-09-20-mocc-g2-observation-conditions.md` (results 系列の凍結物、§0.1 に限定 10 項を先頭配置、
  §5 に 8 項、§4 に「成果物に無い / 束縛の範囲 / 本稿で未照合」13 項目、図は無い) と `docs/paper-story/README.md` の results 表 1 行。
  記録 insight は `output/insights/2026-09-20/mocc-g2-observation-results-doc/README.md` (一次資料の実測表・sha256 照合表・機械照合・レビュー逐語)。
  **新しい測定は 0 件。凍結物 ([T-2779] insight・job dir・段 4 裁定) の bytes は 1 byte も変えていない。**
- 段 1 で親が一次資料の現物を全部読んだ: 4 block の `result.json` (completed・90 走ずつ・ordinal 重複なし・sha256 は `summary.json.inputs` と一致)、
  360 走の verifier / discriminator 記録 (353 走 no-g2・certified、7 走 g2・non-serializable、integrity clean 360/360、discriminator 全走 not-run)、
  G2 7 走の生 trace 336 file (1,981,789,619 byte) の sha256 を manifest と再照合して 336/336 一致、非 G2 353 走の生 trace は不保持 (成果物に無い)、
  k / m・CP 区間・Fisher p を独立再計算して全桁一致、4 block + smoke の bindings 照合 (binary だけ block ごとに異なる)、`s4-ruling.md` の mtime
  15:26:11 JST が smoke 投入 15:36:29 より前。活動を止める裁定は 0 件 (D2148 項 13、D2150 項 1、D2159 は限定として取り込む側)。
- 素材: 結果節の書き方は稿 §3.6 — 「witness off に固定した同一 cell で、各 block 内に 3 arm を回転配置した 4 block (各 arm 合計 120 走) について、
  通常 5/120 (CP 95% [1.37%, 9.46%])、診断 0/120 ([0%, 3.03%])、`BACK_OFF=1` 2/120 ([0.20%, 5.89%])、片側 Fisher (未調整) は診断 0.0300 / backoff 0.2231。
  前者は固定条件で 2 変更を束ねた介入と検出率低下が整合するという材料まで、後者はこの標本・条件では低下を検出できない」。「診断 patch が G2 を止めた」
  「backoff は影響しない / 抑える」「有意」「G2 が無い」「根因」は書かない。
- 素材: `BACK_OFF=1` の 2 件は B2 に集中 (B1 / B3 / B4 は 0/30)。7 件の cycle は全件 G2・長さ 2・両辺 rw で、txid・key・`[epoch, tid]` を稿 §3.4 に書写した。
  thread id は verifier JSON に無いが生 trace の C 行にある (B1/082 は thread 33 と 0)。7 走 14 txid の対応表は作っていない (稿 §4 項 12、scope 外)。
- 段 6 (read-only codex 1 本、`gpt-6-astra` / `medium`、2 レンズを 1 本で): **must-fix 1 / should-fix 4 / nit 1、「着地は止める」。全件 real として反映した。**
  最重要 3 件: (1) 「thread id は成果物に無い」は誤り — 生 trace の C 行 (`C <txid> <thid> …`) にある (親が現物確認)。(2) 検出力の追加値 0.30 / 0.70 と基準率の
  由来 7/120・2/40 は事前登録本文でなく記録 insight §4 にある — 出所表を逐語 / 親の設計説明 / 本稿の再計算に分けた。(3) 「現行 pin の checkout では D1373 の
  関門で拒否される状態のまま」は未検査の現況断定 — 「生成可否を検査も変更もしていない」へ。ほか (P1) results 系列への配置根拠を A-1 類推から
  「段 4 裁定で固定した単一の観測 protocol の完走」へ、§3.6 の例文を 4 block と読めるように、`observational_only` の 1 文。
  焦点再レビュー 1 本 (`DW-O16` の対応表): closed 5 / partial 1 / regressed 0、新規 nit 2 (逐語の空白整形、`0.058 = 7/120` は等式でない) → 反映済み、「着地は止めない」。
- 親の機械照合 (job dir の使い捨て script、稿の hex 59 token と全数値を一次資料から再抽出して突き合わせ) が **B2〜B4 の `result.json` の started / finished
  を推定で書いた 1 件を捕まえ**、実値へ直した (F1 の near-miss 再発、failures fragment)。レビュー子の指摘どおり、機械照合は散文の正確さ (所見 1・3) までは
  保証しない。
- 変異 matrix は実装面差分ゼロで免除 (`DW-S04`)。三軸語走査 (holdout) hit 0。`check_docs.py` 違反なし。fold `--dry-run` planned。受入全走は免除せず、
  本 fragment の commit 後に同一 tip で投入する (結果は land の受領証と job dir に残し、fragment には書かない)。
- 工数: codex 2 本 (read-only review 1、focus 1)。計算ノード job = 受入のみ。

## 次の一手差分
