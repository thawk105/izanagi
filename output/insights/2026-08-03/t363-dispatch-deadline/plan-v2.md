# [T-363] 段 4 裁定と plan v2

段 3 の 2 レンズ (`stage3/lens-a.md`, `stage3/lens-b.md`) の所見を real/refuted・採否・scope で裁定した。

## 裁定表

| # | 所見 (出典) | 判定 | 採否 |
|---|---|---|---|
| A1 | 一回限りの張り直しなら RUN 後の上界は消えない | REFUTED (攻撃不成立) | 実装形を維持。ただし「一度だけ」を変異と post-RUN テストで固定する |
| A2 | first RUN 分岐が期限判定より前にあるため、pre-RUN 期限切れ後に観測した RUN を救う | REAL | **意図した意味論として採用**。RUN を観測した以上は実行予算を与えるのが本 wave の目的。テストで固定する |
| A3 | RUN 証拠が qstat rc に束縛されていない (rc≠0 の stdout でも張り直す) | REAL | **最小形で採用** — 張り直しだけを `rc == 0` に束縛する。`run_seen` / `queue_wait_s` の意味は変えない (それは scope 外) |
| A4 | deadline の起点は「実 RUN 開始」でなく「RUN 初観測」。brief の「差は観測粒度だけ」は誤り | REAL | 採用 (brief・記録を訂正、変数名を `run_observed_at` に)。挙動は不変 |
| A5 | `NaN` / `inf` / 巨大 poll を受理し上界が消える | REAL | **scope 外 → 裁定パッケージ + 新規タスク起票**。T-363 とは別の欠陥型 (入力検証)、受理集合を縮小する変更は未裁定 |
| A6 | 走行中ジョブへの qdel 経路は多数残り、D131 前提 6 の後半を満たさない | REAL | **scope 外 → 裁定パッケージ**。T-363 の完了を D131 前提 6 の完了と混同しない |
| A7 | brief の逐語・一般化・成果物帰属に誤り (except 行、300s 一般化、台帳欠落) | REAL | 採用 (下記「brief 訂正」) |
| B1 | 既存 2 テストは (P1) 後も緑 | REFUTED (攻撃不成立) | 親の独立追跡とも一致。実装形を維持 |
| B2 | 未被覆なのは遷移ではなく deadline 算術の数値境界。テスト設計案 | REAL・限定 | 採用 (テスト設計をそのまま採る) |
| B3 | pre-RUN の実効上界は `min(queue_timeout, W+G)` であり「queue timeout 単独」ではない | REAL | 採用 (不変条件 2 を訂正) |
| B4 | consumer 改修は不要。commit 後に新規台帳を作る/旧台帳へ resume しない | CONDITIONAL | 採用 (手順) |
| B5 | D130 本文は歴史として残し、新しい記録で「既知 RUN 経路のみ修正」と書く | REAL | 採用 (段 7 記録方針) |
| B6 | UNKNOWN のまま走行中のジョブへの同型 qdel は残る。任意 UNKNOWN の RUN 扱いは採らない | REAL | **scope 外 → 裁定パッケージ** (A6 と同じ束) |
| B7 | login node で pytest を走らせてはならない (runbook §7)。dispatch mode は自己参照 | REAL・限定 | 採用 — **(P3) を改訂**。下記「実行形」 |
| B8 | DW-G05 の成果物影響が過大。certified 選択への現行 caller は無い | REAL | 採用 (下記「成果物影響 (改)」) |

## brief 訂正 (A4 / A7 / B3 / B8)

- except 節は `:1361`、qdel 呼び出しは `:1381-1386` (brief の「1358-1385」は不正確)
- 走行中の早期 qdel の成立条件は `Q > G` ではなく概ね `Q < W+G < Q+D` (Q=順番待ち、W=walltime、
  G=grace、D=実行時間)。`Q > G` は必要条件の一部にすぎない
- fake scheduler と実 scheduler の差は観測粒度だけではない。qsub/qstat の実所要、`_run` の
  30 秒 timeout、poll overshoot も deadline 算術に入る
- pre-RUN の実効上界は `min(submitted+queue_wait_timeout_s, submitted+W+G)`
- 「試行が台帳から欠落」は現行 consumer では不正確。正しくは **receipt が `outcome.kind="infra"`
  / `reason="overall-timeout"`、task-run 台帳が `exit_status=16`、変異台帳が当該 record を
  `PARSE_ERROR` として記録し `completed` が増えない**。欠落するのは後続予定試行と、
  将来 harness 自身が計算ノード内にいる束ね形で harness ごと殺された場合
- 「束ねでは発火確率が上がる」は実測に支えられない。正しくは「束ね runtime が要求 walltime の
  余裕を使い切る場合、1 回あたりの被害が大きくなりうる。確率は未測定」

## 成果物影響 (改、DW-G05)

未修正のまま放置すると、順番待ちを挟んだ dispatch は walltime 満了前に走行中ジョブを qdel し、
**(a)** dispatch receipt が `outcome.kind="infra"` / `reason="overall-timeout"` になる、
**(b)** task-run 台帳が実 child rc でなく `exit_status=16` を記録する、
**(c)** 変異台帳が当該 record を `PARSE_ERROR` にして `summary.completed` が増えない。
現行 `TASKS` は `tests` / `provenance` のみで certification submitter を置換しないため、
**certified 選択・材料レポートの値を直接変える caller は今日は存在しない**。
受入全走 (既定 walltime 30 分、grace 300 秒、queue 待ち上限 900 秒) は
`Q < W+G < Q+D` を満たしうる実経路であり、dev-wave の受入証拠自体が infra 失敗へ倒れる。

## plan v2 (実装指示)

### 1. `tools/pegasus/dispatch_compute.py`

`:1215-1217` の RUN 初観測分岐で、**qstat が成功した RUN 観測のときだけ**実行予算を
張り直す。pre-RUN の初期 deadline (`:1182`) は残す。張り直しは一度だけ。

- 同じ `now` を使い、`clock()` を二度呼ばない
- `run_observed_at` 相当の変数を持ち、意味 (RUN 初**観測**時刻であって実 RUN 開始ではない) を
  コメントで明示する
- `run_seen` / `queue_wait_s` / `queue_wait_observed` / `state_history` / receipt schema は変えない

### 2. `orchestrator/tests/test_pegasus_dispatch_compute.py` (新規 3 本)

- **T1 (主回帰・正例)**: states `("QUE","QUE","RUN","RUN","DONE")`、walltime `"00:00:02"`、
  grace 1、poll 1、queue timeout 10、accounting grace 0。旧 deadline は 3 で `t=3` に timeout。
  修正後は `t=2` の RUN 初観測で deadline 5 へ張り直し `t=4` の END まで走る。
  assert は `rc == 0`、**qdel が 1 度も発行されていないこと**、`queue_wait_s == 2.0`、
  `queue_wait_observed is True` に絞る (receipt 全体や会計 payload は固定しない)
- **T2 (post-RUN 上界)**: RUN を観測した後に未知状態が続く列で、張り直し後の上界が実際に効いて
  `overall-timeout` + qdel になることを固定する
- **T3 (信頼できない RUN 証拠)**: qstat が rc≠0 で stdout に `Request State = RUN` を含む場合、
  deadline を**延長しない**ことを固定する

### 3. 変異事前登録 (DW-M01)

| ID | 位置 | 変異 | 期待 kill テスト |
|---|---|---|---|
| V1 | 張り直し行 | `now` → `submitted_at` (旧欠陥の再現) | T1 |
| V2 | 張り直し行 | 張り直しを削除 (no-op 化) | T1 |
| V3 | `and not run_seen` 相当 | RUN 観測ごとに張り直す | T2 (+ 既存 `test_overall_walltime_plus_grace_bound_qdels_running_job`) |
| V4 | `rc == 0` gate | gate を恒真化 | T3 |
| P1 | `:1221` `if now >= total_deadline` | `if False` (正例/上界の実効性) | 既存 2 本 + T2 |

各変異は位置が一意であること、手前に同じ入力を拒否する検査がないこと、赤理由が一つに絞れることを
注入時に確認する。T1 は「承認外の過剰拒否 (= 正常に走るジョブを殺す) を検出する正例」を兼ねる。

### 4. 実行形 ((P3) 改訂、B7)

- **login node で pytest を走らせない** (runbook §7)。実装子にも pytest を走らせない
- 受入全走・変異 matrix はいずれも `tools/run_tests.py` / `mutation_harness.py` 経由で
  **計算ノードへ dispatch** する (sanctioned transport)
- 変異 matrix は `--runner-mode dispatch`。**自己参照 (dispatcher を変異させて dispatcher で走らせる)**
  になるため、台帳へ caveat を明記し、`PARSE_ERROR` が出た変異は kill と数えない
  (`--runner-mode local` は計算ノードを外側で確保する経路が未整備 = D131 前提 3 が未充足のため採らない)
- 変異は統合 commit 後 (DW-O19)、clean tree で回す。旧台帳へ `--resume` しない

## 裁定パッケージ候補 (ユーザーへ返す、本 wave では実装しない)

1. **active job への qdel 禁止 (D131 前提 6 の後半)** — `active` は qsub 成功で立ち、scheduler の
   QUE/RUN を表さない。infra error 時の自動 qdel を `run_seen` 後は禁止するか、
   fresh な rc=0 qstat が QUE/HLD/STG を示したときだけ取り消すか、の設計択一
2. **UNKNOWN のまま走行中のジョブの保護** — 任意 UNKNOWN を RUN 扱いする案は採らない。
   scheduler の権威ある証拠 (started timestamp 等) で RUN を確認する案の可否
3. **timeout 群の入力検証** — `NaN` / `inf` / 巨大 poll interval を拒否する (受理集合の縮小)

**T-363 の完了は D131 前提 6 の完了を意味しない**ことを記録に明記する。
