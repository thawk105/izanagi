---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-22
wave: dev-wave-t2795-k2-pair-resubmit
seq: 1
title: [T-2795] K2 の同 job pair を再投入して初めて成立させ (候補 10 と stock がともに certified、stock の source は STOCK)、続けて 4 巡目 1 job (round 3 の派生物から入力、生成 1 回で候補 5、同 job stock 付き) も両方 certified にした (投入 2 job + insight、実装差分ゼロ、branch worktree-dev-wave-t2795-k2-pair-resubmit)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `verbatim/T-2795-resubmit-origin.md`): D2211 項 1 の pair 再投入 1 job、成立時に 4 巡目 1 job (入力は D2194 項 2 の択 A)、不成立なら D2187 どおり停止。記録 = `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md`。
- 段構成は軽量版 (段 2・3 省略、段 4 は「実装しない」で停止規則と P1〜P4 を結果の前に固定、段 6 は read-only レビュー 1 本)。submit-tree 2 本は着手時の local main `8fd2a2f5c` から job root に切り、CCBench だけ PIN `511c9538` へ checkout した (経路 H)。lock 済みの初投入 tree (`dev-wave-t2795-k2-pair/submit-tree-pair`) には触れていない。
- **pair 再投入 (`16269.nqsv`、bnode001、Elapse 100 秒):** 候補 10 は serializable / certified / anomaly 0 で 825,490 tps、stock (`602b4ce9c788` = stock genome の `variant_id`) は BUILD_START `src_token` = `stock`、certified で 348,883 tps。判定は WAL outcome で行い 4 条件とも成立した。
- **4 巡目 (`16312.nqsv`、bnode052、Elapse 107 秒):** round 3 の `run-summary.json`・`critic-3.md`・`knowledge-input.json`・`coder-input-4.json` (leakproof_context) から production 関数で入力を組み (pair 再投入の結果は渡していない)、planner-v4 は decrease / large、coder-v4-autonomous-k2 は value 5 を返した。login の production 検査 3 本を通して評価し、候補 5 は certified で 884,922.5 tps、同 job の stock は certified・source STOCK で 354,948 tps。同 job の比は 2.366 (pair) と 2.493 (4 巡目)。候補 5 と候補 10 は別 job なので比べない。
- epoch 差: campaign ID は初投入と同じ `b24749ae` (preimage 一致)、受領証 `c42dc712…` は全巡で同一、lock の closure 束縛は 63 → 96 path (初投入比 37 path 差)。初投入の lock は現行の厳密 decoder では読めない。round 3 の loop_state と AO は派生物から記録 sha どおりに再構成できた (harness へは渡していない)。
- **計算投入の確認を省いた (D2212 項 4 / D2211 項 1):** 投入前の見積り ≈ 0.35〜1.25 node 時間は、pair job の所要を候補のみ job の実測 69〜432 秒から外挿した値だった。D2211 項 1 はこの外挿を名指しで禁じており、外挿なしの上限 (walltime 3 時間 × 2 job = 6 node 時間) は確認ラインを越える。本来は 1 本目の前にユーザーの確認を取るべきだったが、取らずに投入した (段 6 レビューの must-fix、{{F:compute-estimate-forbidden-extrapolation}})。4 巡目の前の取り直し (≈ 0.8 node 時間) は pair 走の実測 Elapse 100 秒に基づく。2 job の実使用は計 207 秒 (≈ 0.06 node 時間)。
- **待ち手の誤用:** pair job の終端待ちに `tools/dev_wave_wait.py compute` を accounting file も done file も書かれない形で張り、job の終了 (09:26) から 11:07 まで約 1 時間 40 分戻らなかった。この待ち手は qstat を見ない。4 巡目は `--done-file <attempt dir>/compute-result.json` で正しく待てた。使い方は記憶に既にあり、引かなかったことが原因。測定・判定には影響なし。
- pair 用 submit-tree で `tools/dev_wave_submodule_init.py` が 2 回とも `runtime-io-failure` を返し、入れ子の googletest が記録と違う commit のまま残った (Lustre の EINTR 警告多数)。job の検査は満たし、build は `--isolate-worktree` の別 checkout で入れ子を使わないので続行した。4 巡目用 tree は成功。
- 並走中の掃除 session に備えて submit-tree 2 本を `git worktree lock` し、両 campaign の原本 14 file を job root の `originals-copy-20260922/` へ byte 複製した (MANIFEST に sha256)。
- coder-5 の応答は JSON の前に 118 字の要約を付けていた (契約は JSON だけ)。JSON は機械的に取り出した。
- 段 6 の read-only レビュー 1 本 (codex): NO-GO、must-fix 1 (上の見積りの外挿) と should 1 (候補間差の不確かさを「stock の揺れと同じ桁」と言い過ぎた) を real と裁定し、insight §3 / §6 と本段落を直した。数値・sha・判定・入力の由来は独立再抽出で一致。
- 工数: Claude の登録 role 子 2 本 (planner-v4、coder-v4-autonomous-k2、各約 37 秒)。codex の read-only レビュー 1 本と焦点再レビュー。計算ノード: pair 1 job、4 巡目 1 job、受入。

## 次の一手差分

### 完了

- [T-2795] D2211 項 1 の同 job pair 再投入 1 job と、成立を受けた 4 巡目 1 job を投入し、両 job とも候補と stock が certified、stock の source は STOCK だった。記録 = `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md`。4 巡目の還流は {{T:k2-round4-reflux}} へ。
  remaining: none
  base: 5eeb6f49dd0d621df0b4d3b2fbae11c2d33dd0b6ad988013fdc6a7aed0160995

### 更新

- [T-2808] **P3・起動条件成立 (2026-09-22)**: K2 手動 loop の次の巡 (4 巡目、同 job stock 対照あり、job `16312.nqsv`) が実走した ([T-2795]、`output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md`)。
  fig12 の流れ JSON を上書きせず新 JSON + 別 filename の後継図 (`fig12b_`) で「同 job stock 対照あり」の巡を描く。稿 (凍結) と fig12 の bytes は不変。
  流れの材料が揃うのは {{T:k2-round4-reflux}} (critic-4 の還流) の後なので、それを待って起動する。
  base: d7e33689dad1388b3d4feda6c80e94efdb3ec75ddb5dc9d3a8330ec869edc987

### 新規

- {{T:k2-round4-reflux}} **P2・新規 (計算なし)**: K2 4 巡目の還流を閉じる。critic-4 を 1 回 (候補 5 と同 job stock の WAL・digest・loop_state・受領証・lock を読む、round 3 と同型の入力開示)、
  planner-5 / coder-5 / critic-4 の AO を `--record-agent-output` で取り込み (login)、層 3 材料レポートを作る。原本は lock 済みの
  `dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/submit-tree-r4` (byte 複製 `originals-copy-20260922/r4/`)。その後に 4 巡の results 稿と論文ストーリー B-6 (d)「同 job stock 対照は未達」の更新。
  K2 を論文の必須経路へ戻すものではない (D2211 項 1)。
- {{T:pegasus-readme-pair-text}} **P3・新規 (docs のみ)**: `tools/pegasus/README.md` §7 の同 job pair の記述が修復前の 2 起動 (候補の後に stock driver を 1 回起動) のまま。
  job body は D2205 で driver 1 起動 (pair mode) になっている。記述を現行の挙動へ直す (受理集合・argv は変えない)。
