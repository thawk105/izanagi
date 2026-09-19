---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-mocc-witlight-results
seq: 1
title: mocc 軽量 witness 4 arm × 60 走 (entry 1696) の単独 results 稿を一次資料から書き、README の results 表へ 1 行足した (docs-only、branch worktree-dev-wave-mocc-witlight-results)
---

## 本文

- ユーザー依頼 (2026-09-20): entry 1696 の 4 arm × 60 走について「この診断で何を識別できたか」を書く単独 results 稿
  `docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md` (docs のみ、台帳 ID 未起票、[T-2611] / [T-2674] の型、限定を最初に置く、
  README の results 表へ 1 行、段 6 は独立 read-only レビュー 1 本、新規計測・gate・台帳の追加は scope 外、規律 2 は緩めない)。
  一次資料 = job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/` の原本 (走ごとの JSON・`summary.json`・`parent-accounting.json`・
  事前登録 `s4-ruling.md`・検査 log・dispatch log) と `output/insights/2026-09-19/mocc-witlight-arm-run/README.md` の逐語、hook commit W `5b02546f` の git object。
  軽量版 (段 2・3 省略、実装面差分ゼロで Codex author 不要、変異 matrix は免除、受入全走は免除しない)。専用 handoff は job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-results/HANDOFF.md`。
- brief 前に job dir 原本 240 走 + smoke 4 走を独立集計し、統計 (CP・片側 Fisher・検出力) を二項 / 超幾何分布の直接計算で再計算して記録 insight と丸め精度で一致。
  補正・開示した事実 3 つ: (a) 記録 insight §6 の「on の曝露量は off の約 86%」は BACK_OFF=0 側の値 (0.8636) で、BACK_OFF=1 は 0.8450 → 稿では 2 値を分けた。
  (b) 事前登録 file `s4-ruling.md` の mtime は 2026-09-19 22:48:34 JST で本走の開始後・終了前 (§2 項 1 への amend 後 OID の反映) → §3〜§4 の不変性は file からは
  検証できないと稿 §4 項 1 に開示 (確定 22:16 JST は前 wave の handoff 記録、段 3 レンズ B 22:12 JST の独立再計算が傍証)。
  (c) 記録 insight §7 の「5 request の投入元が相互に異なる」は誤記 — 原本の `bindings.base_dir` では smoke と W1 が同じ投入元 (事前登録 B-M4 どおり) で、投入元は 4 つ。
  段 6 レビューが検出し、稿 §4 項 2 に明記した。記録 insight 自体は本 wave の scope 外で改めていない (erratum は稿の記述が担う)。
- 段 6 レビュー 1 本 (codex gpt-6-astra medium、read-only、14 call、受理): NO-GO → must-fix 4 (M1 投入元の数、M2 configure の arm 間 BACK_OFF 差、M3 検出力表の
  部分抑制行の出所「同上」の誤参照、M4 byte 数 39,378 / 31,698 と [T-2774] heavyweight commit 数の一次出所)、should 1 (§2.8 の集計単位)、nit 2 (field 名、smoke 時刻の階層)。
  全件 real・採用し親が docs を修正 (数値の変更なし)。refuted 8 (結果数値の転記誤り、G2 詳細の要約依存、検出力の誤算・実測への読み替え、smoke 合格集合の緩和、
  mtime 開示の不整合、W / SHA の転記誤り、認証・性能・根因への過大主張、README 行・書式)。**§2 の主要数値・統計再計算値・§5.1 の sha256 20 件は不一致 0 件。**
  焦点再レビュー 1 本 (focus、read-only、受理) は GO — 所見 7 件すべて closed、partial / regressed 0、新規 must-fix / should / nit 0。fix 子 0 (docs のみの修正)。
- 受入全走は最終 tip に対して land 前に 1 回投入し、結果は受領証 (`acceptance-receipt-green.json`) に束縛する。
- 素材: 稿は「識別できた / できなかった」を 1 表 (§2.8) に分け、on 0/60・0/60、off 1/60・1/60、片側 Fisher p=0.500 (両比較)、discriminator 発火 0 件 (問い (ii) は
  識別対象 0 件で未到達)、検出力 0.105 は off 率 0.0417 ([T-2779] 通常 arm 5/120) 対 0 の完全抑制・片側 α=.05・K=60 の条件付き計算で上限 (「80%」は率 0.119 の
  条件付き計算、K=56 で 0.812)、曝露量 on/off 0.864 / 0.845 (性能主張ではない)、限定 11 件 (同等性・効果なし・G2 不在の証明でない、非 certifying・TRACE=1 観測専用、
  昇格・pin 前進・変異探索は認可されていない、規律 7 の旧束縛保持) を先頭に置いた。最新版 (2026-09-19) の「観測 3 件」「根因未同定」「第 2 成功例とは書かない」は不変。
- 工数: codex 2 本 (review 1、focus 1)、計算ノード job = 受入 1 走 (login の collect-only warm 1 回)。

## 次の一手差分
