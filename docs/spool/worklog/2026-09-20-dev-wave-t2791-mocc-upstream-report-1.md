---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2791-mocc-upstream-report
seq: 1
title: [T-2791] mocc G2 観測の上流 (ccbench 本家) 向け報告案 — 英語 issue 本文案と各文の一次資料対応表を output/insights に置いた。送信・PR は人間手番 (docs のみ、branch worktree-dev-wave-t2791-mocc-upstream-report)
---

## 本文

- **成果物:** `output/insights/2026-09-20/t2791-mocc-upstream-report/` — `report-draft.md` (英語 GitHub issue 本文案、文ごとに `[S-01]`〜`[S-63]`)、
  `evidence-map.md` (各文 → 一次資料 path と SHA-256、repo tracked 17 file・ccbench submodule の blob / commit 6 件・job dir 原本 6 種 + 本 wave の再計算)、
  README (位置づけ・還元判断: ユーザー確認待ち・送信者への注意)、`verbatim/` (レビュー 3 本と prompt、対応表、brief、裁定、再計算 log)。
  D2148 項 13 のとおり観測事実と限界だけを書き、根因確定・修正提案・不在証明・同等性・性能値・「同一 binary」を書いていない。hook / verifier 仮定の分岐が
  未分離である点 (S-04 / S-25 / S-44) と witness on の読み値の出所照合が未達である点 (S-28 / S-45) を明記した。**AI は送信しない。修正 PR は見送り (裁定どおり)。**
- **依頼文との差 1 点:** 依頼の「`BACK_OFF=0` かつ witness off でだけ再現」は一次資料と食い違う ([T-2779] の `BACK_OFF=1` witness off arm 2/120、軽量 witness の
  off-bo1 1/60)。一次資料に合わせ「witness off でだけ、`BACK_OFF` は 0 / 1 の両方」と書いた (F1 の型: docs / 依頼文は一次資料と一致するまで根拠にしない)。
- **一次資料の再抽出で分かった 3 点 (draft に反映済み):** (1) signal 走 21 件 (5 + 7 + 7 + 2) の commit 版は同 epoch 21/21 だが tid 差 1 は 20 件で、[T-2779] B2/069 は差 2
  (`v_ver` (59,2577) / (59,2575))。results 稿 §3.4 の表から読める値で、稿の本文はこれを主張していない。(2) verifier の `integrity.clean` は 21 件中 true 16 / false 5 —
  false は [T-2774] の計装 patch 無し 2 arm の 5 走で、11 個の違反 counter は全 21 走で 0 だが `Integrity.clean()` (model.py) が X/P の text evidence の存在も要求する。
  true 16 には [T-1892] の計装なし 5 走が含まれ、これは X/P evidence 要件の導入 `e4c949f08` (09-03) より前の verifier 出力なので、archive された flag は単一 verifier 版の
  再評価ではない。(3) [T-2774] README §3 の (ii) の前提「相手の read key を自分の write set に含めない」は同 wave の段 2 plan 逐語 (`verbatim/s2-plan.md` 24 行)
  の「互いの read key」と表現が違い、字義どおりだと操作指定 (W は x を書く、R は x を読む) と矛盾する。draft は文言でなく plan の操作指定 (24〜27・34 行) から
  条件付きに再構成した例を書き、evidence-map に不一致を記録した。
- **上流 master との差の静的検算 (新規測定ではない):** local mirror の `origin/master` = `50c7946d` (commit 2026-06-28、fetch 日は未記録) と `e9e477ca` の
  `cc/mocc/transaction.cc` の diff は +141/−0 で、非空の追加行は全部 `#if TRACE` 内 (job dir `artifacts/mocc-transaction-master-to-e9e477ca.diff`、sha256 `17c5e497…`)。
  上流 master そのもので走った走は無い、と draft に明記。
- **軽量版 (DW-C00):** 段 2・3 省略、段 5 なし、実装差分ゼロ (probe・runner・verifier・patch に触れていない)、変異 matrix は DW-S04 で免除。段 6 = read-only レビュー 1 本
  (must-fix 8・should 5・nit 1、NO-GO) → 親が本文を直す → 焦点再レビュー 1 巡目 (closed 11 / partial 3 / regressed 1、残 must-fix 2、NO-GO: S-55 の前提を「同義の英訳」と
  確定できない、S-40 の「true 16 = 計装あり」が誤りで再計算 script が counter を検査していない) → script v2 と本文訂正 → 焦点再レビュー 2 巡目 (closed 4、残 0、**GO**)。
  1 巡目の所見は全件 real (依頼文の BACK_OFF 表現の誤りを含む)。Codex 子 3 本 (review 1 + focus 2、gpt-6-astra、read-only、各 3〜6 分、全部 rc=0 受理)。
- **親の所有逸脱の記録 (D95 / R20):** DW-O16 の派生値検算のため、親が read-only の再計算 script (`recheck_21_cycles.py`、約 90 行、21 走の verifier.json を集計) と
  evidence-map の行差し替え script 3 本を job dir (repo 外) に書いた。いずれも repo に入れず、log (`verbatim/recheck_21_cycles.log`) と sha256 だけを insight に置いた。
  Codex author の sandbox は job dir へ書けないため (T-2773 の実測)、親が書いた。
- **検査:** `python3 tools/check_docs.py` 違反なし (2 回)。三軸語走査 (`s8b_holdout_freeze search`) は本 wave の新規 file に hit 0。**同走査は既存 tracked 4 file
  (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/{journal.jsonl,manifest.json,result.json}`、`output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`)
  に rr80 / rr20 の conjunction hit を出す (rc=1)。** これらは凍結 v2 g1 chain の着地 (`4d8fb93b7` / `cc82edc8c`、entry 1716) で main に入った file で、
  `orchestrator/tests/test_s8b_repo_scan_invariant.py` の `KNOWN_CONJUNCTION_HITS` (空) と食い違うが、同 test は growth hold で skip されている。本 wave の scope 外
  (実装面) なので触れず、観測として残す。verbatim の `s6-review-1.md` は末尾空白 15 行を可逆最小正規化 (`verbatim/NORMALIZATION.md` に原文 sha256・byte 数・復元法)。
- **受入:** docs-only でも land は受入 receipt を要求するので、本 commit の後に `tools/dev_wave_wait.py acceptance` を門番 (他 wave の leader ≤ 1 ∧ load < 60) 経由で投入する。
  結果は job dir の `acceptance-receipt-final-<n>.json` と land の receipt が権威 (本 fragment には書かない)。
- **後続 (起票しない):** D2174 項 7 (T-2798 見送り) の再訪条件「上流報告への返答」は、人間が本文案を送った後に始まる。送信前の注意 (commit の公開状態、master の進み) は
  README §4。
- 工数: Codex 子 3 本 (read-only)。計算ノード job は受入のみ。

## 次の一手差分

### 完了

- [T-2791] 上流向け報告案 (英語 issue 本文案 + 各文の一次資料対応表) を `output/insights/2026-09-20/t2791-mocc-upstream-report/` に置いた。段 6 レビュー 3 巡で GO。
  送信・PR は人間手番のまま (D2148 項 13)。診断 patch の取り込み・pin 前進・certified 昇格は変更していない。
  remaining: none
  base: 0f84fc041332ec6537b205c37757a484dd7b0966d7e24cd44f42cea0ddaf3b73
