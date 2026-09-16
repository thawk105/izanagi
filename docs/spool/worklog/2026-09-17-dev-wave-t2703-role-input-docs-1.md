---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2703-role-input-docs
seq: 1
title: [T-2703][T-2717][T-2705] 役割入力文書 6 本を実配線へ合わせ適用版を明示し、source pin を追随した (docs + pin 追随 (ledger / originless baseline / adapter)、branch worktree-dev-wave-t2703-role-input-docs、変異 matrix = baseline PASSED・4/4 KILLED 期待 node 完全一致・等価 1 SURVIVED・MISMATCH 0、M2 は login probe)
---

## 本文

- 依頼は D2104 項 4 (第 20 回 /rulings 全件、着手時に main へ着地済み) の実施。「`src/coder-leakproof-context.md` の
  Measurement Setup、critic 役割文書の latency 列挙、手動射影 runbook の `last_delta_pct`、planner / coder の凍結表現を
  実配線へ合わせて直す。射程は入力文書の適用版を明示し凍結済みアーム (K0 / K1 / B-4) には遡及適用しない。role payload
  の schema は上げず、`latency_ns` key と代表 rep は変えない。docs (.md) のみ、実装差分ゼロ。gate・検査の追加は scope 外」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2703-role-input-docs/README.md`。設計判断は
  {{D:role-input-docs-applied-version}}。統合 commit `dd6d0466e` (docs 7 file + ledger + baseline + adapter 4 本の 1 commit)。
- **「docs のみ・実装差分ゼロ」の前提は成立しなかった (段 1 で実測、段 3 両レンズが real)。** 4 role .md の bytes は
  review ledger `SOURCE_FILE_SHA256`・adapter json・originless baseline に pin され、D118 残余 (b) が明記する帰結として
  ledger と baseline の追随 (Codex author) と adapter の再 render (親、D1936 項 25) を伴う。「実装差分ゼロ」は
  「schema・検査規則・受理述語・runtime 挙動の差分ゼロ」と読んだ。pin の第 4 機構 (B-4 receipt の live 比較) は
  再受理対象の receipt 0 件・§5 の prompt / projection 欄未記入で陳腐化する記入済み値なし。
- **親 brief の「手動 runbook の baseline は毎 iteration 同じ値」は両レンズが反証した。** T-2588 の K2 手動 loop は 2 周目の
  `current_perf` へ 1 周目の実測を入れていた。凍結の記述は 8c 自動 trial (D410 決定 1) に限定し、runbook へ凍結規則を
  新設しなかった。段 6 レビュー A が「8c で世代を跨いで届くのは whiteboard だけ」も反証 (第 2 世代以降は
  `critic_feedback`) し、critic の帰属例の「衝突が無くても待つ時間」断定も must-fix にした。両方とも docs 側で直した。
- **verify の一般化 (レンズ B):** 段 4b は legacy 小規模 verify だけだが sort / trigger-gating は legacy + S2。旧文の
  1m / 48 threads / extime 3 は S2 verify 構成の値だった。軸別に書き分けた。
- **D1860 との関係:** runbook の `last_delta_pct` 除去は D1860 (削除せず null) の後続の限定訂正。前提 (planner 例に field が
  在る) は D2064 の wave (4c6f03048) で消滅していた。決定に明記した。
- 実走: 焦点走 15 file (Pegasus 2759 / 2837.nqsv) は統合後・fix 後とも 2084 passed / 5 skipped (環境 skip のみ) / rc=0。
  `-rs` 付きの中間走 (2799.nqsv) は走行中に親が docs を編集して 8 failed (adapter parity drift、自傷、F106 の再発として
  記録) になり合否に使わない。
  `check_codex_agents` は ledger 更新前 rc=1 (drift 拒否)、更新 + render 後 rc=0。`check_docs` 違反なし。
- **変異 matrix (container worktree、`run_tests.py` 2 file、probe と本走で各 6 request)。** 本走は baseline PASSED (48 passed)、
  負例 4 件 (M1 追随 helper の呼出し除去、M1a / M1b / M1c = planner / critic / coder のタプル除去) すべて KILLED で期待 node と
  観測 node が完全一致、等価変異 M0 (Reviewed コメント文言) SURVIVED、MISMATCH 0。M2 (ledger の critic sha を旧値へ) は
  harness 外の login probe: checker rc=1 (`SOURCE_FILE_SHA256 drift`)、pytest collect rc=2 (errors=1、個別 node に到達しない)、
  即時復元・対照 rc=0。役割本文の意味を pin する semantic 防壁は新設していない (D1936 項 24)。
- 残存 (scope 外、記録のみ): `coder-v4-autonomous-trigger-gating.md` 入力例の `leakproof_context` は file inline と書くが 8c は
  `s8c_generation_projection.LEAKPROOF_CONTEXT` の固定短文 (別 drift、{{T:trigger-gating-leakproof-inline-drift}})。
  `coder-v4-autonomous.md` / `-sort.md` / `-k2.md` は誤りの記述が無く触っていない。将来の B-4 receipt は記入時点の
  `critic.md` bytes に束縛される。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 1、focus 1、全段 `gpt-6-astra` / `medium`)。親の実測は
  焦点走 3 本、変異 2 走 + login probe 1 本、checker、render。
- **受入全走**は本記録 commit を含む tip に対して land 前に 1 回だけ投入し、child-green でなければ land しない。
  本エントリの作成時点では未実施である。

- [T-2703] coder-leakproof-context の Measurement Setup を `default_perf()` (100k / 4 / extime 1 / reps 2) と軸別 verify・
  中央値規則に一致させ、適用版を明示した。
- [T-2717] critic / critic-experiment の役割文書から latency の独立指標列挙を外し恒等変換を注記した。`latency_ns` key と
  代表 rep は D2104 項 4 のとおり不変。
- [T-2705] planner / trigger-gating coder の凍結表現を 8c 自動 trial に限定して直し、runbook 2 本から `last_delta_pct` を除いた。

## 次の一手差分

### 完了

- [T-2703] coder-leakproof-context の Measurement Setup を実配線 (`default_perf()`・軸別 verify・中央値規則) に一致させ、
  適用版を明示した。凍結済みアームには遡及しない。
  remaining: none
  base: caa4ef884a46ae7433d2008aa5de4a0b94a0ca2d4921402b2cf50a3a1ac075c4
- [T-2717] critic / critic-experiment の役割文書から latency の独立指標列挙を外した。8c 役割 payload の `latency_ns` key と
  代表 rep (偶数有効 reps で上側中央) は D2104 項 4 が不変と裁定した。
  remaining: none
  base: 8f58b12bdc17fde3e7a08c823c04430bb96039db4edbfcef78e48753b7f37885
- [T-2705] planner の「現行測定値」と trigger-gating coder の「直近実測」を 8c の凍結 snapshot (D410 決定 1) の記述へ直し、
  手動射影 runbook 2 本から実在しない `last_delta_pct` を除いた。
  remaining: none
  base: 323d8250679315ba26aad7faca5a56740459f27c64bc2f70ad172d325e00d502

### 新規

- {{T:trigger-gating-leakproof-inline-drift}} **P3・新規**: `.claude/agents/coder-v4-autonomous-trigger-gating.md` の入力例は
  `leakproof_context` を `src/coder-leakproof-context.md` の inline と書くが、8c 自動 trial が渡すのは
  `orchestrator/campaign/s8c_generation_projection.py` の `LEAKPROOF_CONTEXT` (固定短文) である。手動 runbook (段 8a) では
  file inline。役割文書の例を経路別に書き分けるか据え置くかを決める。直すなら role .md の pin 追随 (ledger / adapter /
  originless baseline) を伴う。
