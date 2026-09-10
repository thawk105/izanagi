# [T-363] 段 1 brief — dispatch 総デッドラインが順番待ちを実行予算から差し引く欠陥

基準: worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline`
(branch `worktree-dev-wave-t363-deadline`, HEAD = local main 1a3604b, clean)。

## scope

`tools/pegasus/dispatch_compute.py` の実行監視 deadline を **RUN 初観測時点で張り直す**。
併せて `orchestrator/tests/test_pegasus_dispatch_compute.py` へ回帰テストを足す。
`TASKS`、runbook §7.0 の task 表、receipt schema、他 task の挙動には触れない。

## 確定済みユーザー裁定

D130 決定 (3) 項目 4 = 本件。「今日の dispatch 経路にもある潜在欠陥」であり [T-360]
(変異本走の計算ノード束ね) 着手の 4 前提の 1 つ。**裁定は「欠陥を塞ぐ」までで実装形は未裁定** —
下記 (P1) は親の provisional 裁定であり攻撃対象。

## 欠陥の逐語 (前提の実測: file:line で確定)

- `:1181-1182` `queue_started = submitted_at` / `total_deadline = submitted_at + walltime_s + overall_grace_s`
- `:1215-1217` RUN 初観測で `run_seen = True`、`receipt["queue_wait_s"]` を記録
- `:1219` `not run_seen` の間だけ `queue_wait_timeout_s` (既定 900s) が独立に守る
- `:1221` `now >= total_deadline` → `DispatchError("overall-timeout")`
- `:1358-1385` except 節が `active` の間 `_best_effort_qdel` を打つ = **走行中ジョブを qdel**
- 既定 `overall_grace_s = 300.0` → **順番待ち > 300s で walltime 満了前の qdel 余地が生じる**

数値再現は段 5 実装子が期待赤 (fix 前に赤、fix 後に緑) として実測する。親は実装面 probe を
書かない (凍結境界)。模擬は fake scheduler + 注入 clock で、実 scheduler との差は
「状態文字列の観測粒度」だけであり、deadline 算術には影響しない。

## 既存テストの被覆 (純増検出力)

- `test_overall_walltime_plus_grace_bound_qdels_running_job` (:1308) = RUN 継続時の上界
- `test_unknown_scheduler_state_remains_bounded_by_overall_timeout` (:1334) = 未知状態の上界
- **順番待ちを挟んでから RUN する経路の deadline は未被覆** = 新テストの純増検出力

## 不変条件

1. 既存テストの期待値を変更しない (上記 2 本は緑のまま通る)
2. 上界を必ず残す: RUN 未観測は `queue_wait_timeout_s`、RUN 後は `walltime_s + overall_grace_s`
3. receipt の既存 field 名・意味を変えない (`queue_wait_s` / `queue_wait_observed` / `state_history`)
4. 実装面は Codex `role=author` が書く (D95)。親は docs のみ
5. 変異 matrix は `--runner-mode local` (dispatch mode は dispatcher 自身を変異させる自己参照)

## 成果物影響 (DW-G05)

未修正のまま放置すると、順番待ちが 300s を超えた計測 dispatch は walltime 満了前に
走行中ジョブを qdel され `rc=INFRA_RC` になる。→ **その試行が台帳から欠落し (試行欠落)**、
receipt には `"overall-timeout"` と記録されて原因がジョブ側へ誤帰属する。数値・certified 選択は
「欠測を含む台帳」を根拠にすることになる。[T-360] の束ね (数時間 walltime) では発火確率が上がる。

## provisional 裁定 (攻撃対象)

- **(P1) 修正形は (A)**: RUN 初観測時に `total_deadline = now + walltime_s + overall_grace_s` へ
  張り直す。pre-RUN の初期 deadline は現状のまま残す。(B) 「pre-RUN 段を `queue_wait_timeout_s`
  単独へ委ねる」案は不変条件 1 (既存テスト期待) を破るため採らない
- **(P2) 未知状態 (UNRECOGNIZED) のまま実は走行中のジョブに対する同型の qdel 余地は scope 外**。
  RUN 検出の拡張は受理集合を別方向へ広げるため、real なら裁定パッケージへ返す
- **(P3) 変異は `--runner-mode local` + 対象 test file の関連 node** に限る

## 成果物の形・分割

統合 commit 1 本 (コード + テスト) → 変異台帳 JSON (`output/insights/`) → worklog fragment。
実装単位は 1 (所有 = `tools/pegasus/dispatch_compute.py` と
`orchestrator/tests/test_pegasus_dispatch_compute.py`)。段 6 のレビューは read-only 2 本並列。
