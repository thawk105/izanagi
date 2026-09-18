---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2746-k2-loop-round2
seq: 1
title: [T-2746] K2 ループを 2 巡目へ進めた — proposal-2 (value 25) を 1 評価 (certified、687508.5 tps、anomalies 0) し、実測を planner-3 / coder-3 へ戻して proposal-3 (value 20、既知値の再提案) を保存、同巡の agent 出力を機序仮説層 v3 (`runs/agent_outputs.jsonl` + `mechanism_hypotheses`) で永続化した (コード + テスト + docs、branch worktree-dev-wave-t2746-k2-loop-round2、変異 matrix = baseline PASSED・負例 12/12 KILLED 期待 node 完全一致 (166 node)・等価 M0 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「[T-2746] (D2120 項 1、ユーザー裁定 2026-09-17) K2 ループ次巡を 1 巡だけ実走する — 保存済み proposal-2 (`double now_backoff = 25;`) を
  既存経路で 1 評価し、実測を planner-3 / coder-3 へ還流して proposal-3 を保存する (評価しない)。予算 = 評価 job 1・critic 1・planner/coder 各 1、
  再投入・再抽選・比較 arm なし。submit-tree は現行 main で新規に切る (旧 tree d97c423bd は使わない)。(中略) 同巡で agent 出力が生まれるので、凍結済み
  機序仮説層 v3 (B-9(c)) の適用と材料保存を同じ予算内で行う (追加評価・追加 role 呼出しは足さない)。anomaly ≥ 1 は即 reject、3 巡目へ進まない。
  改善の実証とは書かない。規律 2 を緩めない。本題の実走だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた。** 一次資料は `output/insights/2026-09-18/t2746-k2-loop-round2/README.md`。設計判断は {{D:layer3-mechanism-layer-v3-agent-outputs}}、
  失敗は {{F:evidence-dir-prewritten-by-parent}} と F570 の再発追記。
- **実走 (scope A):** 投入 2 本・評価 1 本。attempt-0001 `4947.nqsv` は親の操作ミス (evidence dir へ `qstat -f` の写しを先に置いた) で job body の
  preflight 拒否 (7 秒、driver 未起動、campaign 未接触)。attempt-0002 `4954.nqsv` = `driver_rc=0`、variant `3dec27291054` (BACKOFF_FIXED=25)、
  serializable / certified / anomalies 0 (commits 445394 / aborts 71877)、median 687508.5 tps ([692403, 682614]、CV 1.0068%、settled)、abort 7.4%
  (T-2702 集約)、llc/ipc 欠測 (perf 不在)、`1 committed`、停止判定 `continue`、Elapse 432 秒。critic-2 (帰属不能、recommend decrease/large 候補 10、
  逆方向なし → `prior_critic_reverse=false`) → planner-3 (decrease/medium) → coder-3 (**value 20 = 既知値の再提案**、再抽選なし)。proposal-3 は検査 3 本緑、
  未評価。「同機体 2 点で delta_pct を書ける」は誤り (`_DELTA_PCT_LIVE=False`、whiteboard は本 campaign の 1 件) — 段 2/3 が独立に指摘し brief を訂正。
  1 巡目との差 −4.4% は非同時刻比較で読まない。
- **v3 (scope B、[T-2681] の着手条件成立):** Codex author 3 単位 (A0 共有 module `agent_outputs.py` / A1 harness の live 追記 + 取込み口 /
  A2 renderer + schema) + fix 3 巡。着手時の新事実 = 現行 renderer は `verify_done` の `commit_witness` / `proof_surfaces` を schema に持たず
  現行 loop 型 campaign を描画できなかった (F570 再発、D829/D828 で optional 追加)。段 6 レビュー 2 本の must-fix 5 件 (抽出規則不一致・code block
  偽見出し・variant 条件不一致・provenance の主張限定・D830 閉包の update 経路) と既知の赤 2 件、B-4 静的 inventory の `.start` heuristic /
  module 数 pin 46→47、入力側防壁テストの receipt 衝突を fix で閉じ、焦点再レビューは新規 must-fix なし。本巡の 4 event (planner-2 / critic-2 /
  planner-3 / coder-3。coder-2 は 1 巡目の実入力が未保存で取込み不能) を取込み口で書き、材料レポート `layer3_report.json` は
  `mechanism_hypotheses` 1 件・`source_refs` 10 (wal 5 + wb 1 + ao 4)・双射通過・admitted・`certifying_input=false`。
- **裁定パッケージ候補 3 件 (本 wave は判定しない):** (1) attempt-0002 の事後承認 (「再投入なし」からの逸脱、評価は 1 本)、(2) 層 3 v1 全文 reader
  (既存 v1 artifact 1 件は変更前から不一致)、(3) 保存済み report と fresh 比較 consumer (`autonomous_trial_completeness.py`) の整合。
  収集先: 次の一手の新規項と repo 外 `dev-wave-jobs/rulings-inbox/2026-09-18-k2-loop-round2-followups.md`。
- **主張しない:** 改善の実証、新 CC 構造、候補間の certified 選択、K2 因果、critic 診断の機械還流 (critic の候補 10 に対し coder は 20 を出した =
  経路限界の実例)、B-4 適格、`mechanism_hypotheses` が機序の証拠であること。
- 実走: Pegasus job 2 本 (投入)、焦点走 7 走 (計算ノード dispatch / bounded local、うち 1 走は queue 待ち timeout で rc=16 → D612 上書きで再投入)、
  dogfood 3 回 (複製 campaign 2 回 + 本物 1 回)、変異 matrix 2 走 (probe + final、各 14 run、計算ノード)、受入全走 (記録 commit 後の最終 tip、結果は land の受領証)。
- 工数: codex 子 10 本 (plan 1、consult 2、author 3、review 2、fix 3、focus 1、全段 `gpt-6-astra` / `medium`)、Claude role 3 本 (critic / planner-v4 /
  coder-v4-autonomous-k2、各 1 回)。

## 次の一手差分

### 完了

- [T-2746] proposal-2 を 1 評価し proposal-3 を保存した。v3 (T-2681) も同 wave で実装・適用した。3 巡目へ進んでいない。
  remaining: none
  base: e3b128fc964f2d95b1bf1c4f818a926f1a229eef8588e31b492ece1dcefd5b6e
- [T-2681] 層 3 機序仮説層 v3 を実装し ({{D:layer3-mechanism-layer-v3-agent-outputs}})、本巡 campaign の材料レポートで `mechanism_hypotheses` を
  非空・双射通過で出した (`output/insights/2026-09-18/t2746-k2-loop-round2/layer3_report.json`)。着手条件 (agent 出力を生む loop 再走) は
  D2120 項 1 の 2 巡目で成立した。
  remaining: none
  base: ea5b46a9c5404fef95ca513998d28e06091821c80f689eb8b80d0dd2a45e2d50

### 新規

- {{T:k2-round2-resubmit-ratification}} **P1・ユーザー裁定待ち**: K2 2 巡目の attempt-0002 (`4954.nqsv`) を D2120 項 1 の「再投入なし」からの逸脱として
  事後承認するか。attempt-0001 は親の操作ミスによる preflight 拒否 (評価未実施) で、評価は 1 本 (`output/insights/2026-09-18/t2746-k2-loop-round2/README.md`)。
  preflight 失敗を予算外とする一般規則は提案しない。
- {{T:k2-loop-round3-scope}} **P1・ユーザー裁定待ち**: K2 ループ 3 巡目の扱い。proposal-3 は既知値 20 の再提案 (未評価) で、critic-2 の候補 10 は coder に届かない
  (経路限界)。択: (a) proposal-3 を既存経路で 1 評価する、(b) critic 診断を次生成の型付き入力へ渡す最小経路 (run-card の固定入力契約の改訂) を先に裁定する、
  (c) 止める。同機体・同 job 内の stock 対照 (critic R0) の要否も併せて。
- {{T:layer3-v1-reader-and-fresh-compare}} **P3・ユーザー裁定待ち**: 層 3 の (1) v1 全文 reader (既存 v1 artifact `p3-s8a-trigger-loop-…3f72ecd5` は
  変更前から 6 種の不一致) と (2) 保存済み report と fresh 比較 consumer (`autonomous_trial_completeness.py` 4652〜4721) の整合 (generator sha と
  新 optional 区画で不一致になりうる)。旧 report の再生成・sha 差替えはしない。
