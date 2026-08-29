# 段1 brief — [T-1933] 受入 wall を決めている単体処理の同定

- wave: `dev-wave-t1933-wall-unit`
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit`
- base main: `d03855e92`（HEAD 同一、clean、submodule 初期化済み、startup gate rc=0）

## scope

fixed-tip の full 受入 artifact から、**受入の壁時間 (wall) を実際に決めている単体処理**を同定する。
同定は既存 artifact（`/work/1/SFC/tanab/.izanagi-acceptance-shards/<group>/shard-N/{report.json,junit.xml}`、
484 本の full 走）の事後解析で行い、同定のために新しい full 受入測定を積み増さない。
同定が**具体的な処理を 1 つ**指し示した場合にだけ、その処理に閉じた短縮を検討する。
指し示さない場合は負結果として閉じ、短縮案を作らない。

## 確定済みユーザー裁定・既裁定

- D1260: 焦点走の cache hit や worker duration 総和の低下を full wall への因果の代用にしない。
  paired full K=3 中央値の差が 10% 未満なら「変化なし」(D357)。node 秒は仕事量の代理にならない。
- 受入 receipt の argv は完全一致で pin される。**テストを絞る形の短縮案は land できない。**
- 既着地 branch `worktree-dev-wave-t1933-reconciliation` / `-acceptance-longest-node` /
  `worktree-dev-wave-acceptance-fastest` は残骸。取り込まない。
- この wave の成果物は同定まで。

## 不変条件

- skip / deselect / case 縮小 / assertion 変更 / timeout 緩和で受入を短くしない（規律2）。
- 受理集合・観測される値と例外・refusal 文字列を変えない。
- 既存の凍結 artifact bytes、`orchestrator/tests/acceptance_duration_ledger.json` の
  add-only 契約、`orchestrator/tests/growth_test_holds.py` の hold 集合を変えない。
- 解析は既存 artifact の事後読取だけ。計測系へ観測を差し込まない（規律1）。
- 親の解析 script は repo 外（job dir）に置き、repo へ入れない。

## 成果物

`output/insights/2026-08-29_t1933-wall-unit/` に、
(1) 同定の結論（単一処理を指すか、指さないならなぜか）、
(2) 484 走 corpus の壁時間分解表と回帰、
(3) 同定に残る穴と、その穴を埋めるのに必要な最小の観測、
(4) 単一処理を指した場合だけ、その処理に閉じた短縮候補と、結果を見る前に決めた判定式。

## (P1) 親の provisional 裁定 — 攻撃対象

親が既存 artifact 484 走から出した実測（詳細は同 job dir の `measurements.md`）。
以下はすべて「親の provisional 裁定」であり、子は守らずに攻撃すること。

- (P1a) run の wall は shard-0 の wall である。484 走中 470 走 (97.1%)。
- (P1b) shard の wall ≈ 固定オーバーヘッド + 最 busy worker の occupancy。
  pooled OLS で slope 1.018 / intercept 75.2 秒 / r 0.884。`wall - max_occ` の中央値 70.9 秒、
  IQR 65.0–78.4 秒。総仕事量ベースの理想値との相関は r 0.649 と弱く、**総仕事量律速ではない**。
- (P1c) 最 busy worker は item を 2〜5 本しか持たず、最長 1 本がその 8 割以上 (中央 0.85) を占める。
- (P1d) 現行 tip 近傍（K=3、08-28 以降 117 走）で最 busy worker を占めるのは 2 系統だけである。
  `s8c-preregistration-candidate` loadgroup（5 node、occupancy の 100%）と、
  `test_s8b_oracle_driver.py` の T-080 stub-free e2e 系（ungrouped、1 本 100〜190 秒が約 10 本並ぶ）。
- (P1e) **親の暫定結論（もっとも疑わしい）**: 単一 node を短くしても wall は動かない。
  100〜130 秒帯に同じ長さの node が約 10 本あり、1 本を消しても次が critical worker を占める。
  D1260 の +0.37% はこの構造の帰結として説明できる。
  wall の残る単体処理は「テストを 1 本も走らせていない約 75 秒の固定床」であり、
  これは 3 shard 共通・48 worker の process 起動と import と collection である。

## 既知の穴（子が最優先で詰めるところ）

- artifact に **nodeid → worker の対応が無い**。`report.json` は `group_to_workers` と
  `worker_occupancy`（worker→{items,duration_s}）だけを持つ。
  `tools/acceptance_shards.py` の `_REPORT_WORKERS` は計算されているが report へ落ちていない。
  したがって ungrouped node について「critical worker に何が載っていたか」は現状**推定**でしかない。
- corpus は tip も計算ノードの混雑度も揃っていない。同一 node の所要が走間で 1.7 倍動く例がある
  （`test_candidate_freeze_matches_contract_and_generation_chain` が 119.4 秒と 213.8 秒）。
  fixed-tip の主張をするには、同一 collection universe の部分集合へ絞る必要がある。
- 「約 75 秒の固定床」の内訳は未同定。分解した実測はまだ無い。

## 成果物影響 (DW-G05)

放置すると受入 wall は tracked file 数と commit 数に比例して伸び続け、
`growth_test_holds` の hold 対象が増えて受理集合が痩せる（既に 5 node が hold 中）。
同定を誤ると、D1260 と同じ「配線は正しく変異も KILLED だが wall は動かない」機構を再実装する。

## 分割方針

軽量版にしない。段 2 プラン 1 本、段 3 敵対相談 2 本（正しさ・整合レンズと実効性レンズ）を使う。
実装面が生じる場合だけ段 5 で Codex `role=author` を 1 本立てる。親は実装面を直接編集しない。

## 実測環境

- 解析: login node 上の read-only 事後解析だけ。新しい benchmark も campaign も起動しない。
- 受入全走: `tools/dev_wave_wait.py acceptance` 経由（段 6 / 段 9）。計算ノードへ dispatch される。
