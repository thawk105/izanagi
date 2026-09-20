---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-p24-static-backoff-sweep-results
seq: 1
title: 旧 linux-baremetal 環境の P2-4 静的 backoff sweep 3 campaign (論文 §8 exact claim (性能) の出所、+38.3 / +11.3 / −6.6%) の単独 results 稿を一次資料から書き、README の results 表へ 1 行を足した (docs のみ、台帳 ID 未起票、branch worktree-dev-wave-p24-static-backoff-sweep-results)
---

## 本文

- ユーザー依頼 (2026-09-20) に基づく 1 wave。着手時 local main `947fd160a` から fresh worktree、専用 handoff は repo 外 job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-p24-static-backoff-sweep-results/HANDOFF.md`。実装差分ゼロ (Codex 実装子なし)、軽量版 (段 2・3 省略、
  `DW-C00` の「一次資料から事実を再抽出する docs-only」につき段 6 read-only レビュー 1 本 + 焦点再レビュー 1 本)。成果物は
  `docs/paper-story/results/2026-09-20-p24-static-backoff-sweep-linux-baremetal.md` (531 行、限定 15 件、図は無い) と
  `docs/paper-story/README.md` の results 行 1 本。記録は `output/insights/2026-09-20/p24-static-backoff-sweep-results-doc/README.md`。
- 素材: fig2b の provenance が入力として指す 3 campaign (`493813a7` / `484c663e` / `610004b9`) の `campaign.lock`・WAL・`.dat`・材料レポート、
  fig2b provenance JSON、同環境の較正記録 4 本、profile JSON (headline でない +38.5% の出所)、D19 / D20 / D496 / D497 / D1100 / D1506 / D1525 /
  D1631 / D1993 項 4・6 / D2120 項 15 と 2026-09-20 版 §8 の exact claim。値は WAL の `median_tps` / `tps` / `cv` / `abort_rate`、provenance の
  `facts` / `baselines`、較正 JSON から逐語で取り、利得の未丸め値 (38.32880387859468 / 11.268232226265873 / −6.642987662951915%) は A-3 と同じ式で再計算して
  A-3 の再計算表と一致。SHA-256 24 件・5 反復 24・abort 24・commits 24・median 24・binary hash 16・provenance 値 16・command 17 件を grep -F の
  集合比較で機械照合 (初稿の profile md の 1 桁誤りを検出・是正)。
- 実測で見つけた既存記述との差 2 点 (どちらも稿に書き、既存物は直さない): (1) `6f169f90` の `reports/` には 2026-09-16 に層 3 screening 射影の
  回帰 pin `layer3_report.json` が足されており、A-3 insight (08-25) の「reports/ 無」は当時の事実。(2) sweep の 24 走もすべて `perf stat` 下
  (figures/README の 2026-08-26 訂正のとおり) — 稿は「絶対 tps を headline の出所にしない」「比は同一 harness 内」と書き、+38.5% を採らない
  理由は D20 の利用方針であって効果量差の実証ではない、と A-3 の言い方を保った。
- 素材: 8 genome の `trace_bin` / `perf_bin` hash は 3 campaign で同一 (balanced / read-heavy は build cache 再利用、WAL `perf_cached: true`) —
  3 workload は同じ binary を `-ycsb_rratio` だけ変えて測っている。campaign 成果物は host / kernel / boot を持たず、host = cygnus は較正記録の
  `host.node` と D1525 による (稿 §4.1 の欠落として開示)。
- 段 6 レビュー 1 本 (gpt-6-astra / medium、15 call、349 秒): NO-GO、所見 5 (must-fix 1 / should-fix 2 / nit 2)、real 4 / refuted 1。must-fix は
  §3 限定 11 が別図 (`t2187_stage2_thread_axis`) の `not_certified` / `NOT CERTIFIED` を fig2b に誤帰属 (親も段 5 の自己点検で検出済み) →
  fig2b の provenance の実 field (`HISTORICAL_RAW` / epoch `E0`) を根拠に書き直し。should-fix は §5.1 の「既存台帳と一致」を収載 14 件へ狭める、
  「導出索引を出所にしない」を論文値と測定数値に限定し参考値の引用元と再計算していない範囲を §5.4 へ明記。refuted は (P1)〜(P4) への攻撃
  (現状維持)。fix commit `0228673fa`。焦点再レビュー 1 本 (8 call、153 秒): GO、4 件 closed、新規所見なし (DW-O16 の 3 巡上限に対し 2 巡)。
- 受入結果と land は専用 handoff へ集約する。dev-wave 改善候補は段 8 で 0 件。

## 次の一手差分
