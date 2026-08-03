---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-03
wave: dev-wave-t363-deadline
seq: 1
title: [T-363] 順番待ちが dispatch の実行監視予算を削る欠陥を塞ぐ — 修正射程は rc=0 の RUN 初観測経路に限る (コード + docs、branch worktree-dev-wave-t363-deadline)
---

## 本文

- **欠陥の実体。** `tools/pegasus/dispatch_compute.py` の総デッドラインは qsub 応答時刻
  (`submitted_at`) 起点で `walltime + overall_grace` を張っていた。順番待ちには
  `queue_wait_timeout_s` (既定 900 秒) という独立の上界が既にあるのに、その経過が RUN 観測後の
  監視予算からも二重に差し引かれ、超過時は except 節の `_best_effort_qdel` が**走行中ジョブを
  qdel** していた。D130 決定 (3) 項目 4 が挙げた [T-360] の前提の 1 つ
- **修正。** qstat が rc=0 で当該 request を含み、パーサが最初に RUN と判定した観測時刻から
  `walltime + overall_grace` へ**一度だけ**張り直す。張り直し latch は `run_seen` から分離した
  (`run_deadline_rebased`)。`run_seen` / `queue_wait_s` / `queue_wait_observed` /
  `state_history` / receipt schema は不変。pre-RUN の上界
  (`min(submitted + queue_wait_timeout, submitted + walltime + grace)`) は保存した
- **修正射程は限定される (段 6 レビューの must-fix)。** 次は**未解決**であり、
  **T-363 の完了は D131 前提 6 の完了を意味しない** — 同前提は
  「`total_deadline` の修正**と** active job に対する qdel の禁止」の連言である
  - rc≠0 の qstat stdout に RUN が含まれるだけでは張り直さない (後続の rc=0 RUN で回復する)
  - RUN 未観測・UNKNOWN のまま実際は走行中のジョブ、poll 粒度で RUN を見逃す経路
  - `pre-running` と実 RUN 開始の差 (起点は実開始でなく親の初観測)
  - infra error 時に走行中ジョブへ飛ぶ qdel 経路そのもの
- **段 1 brief の主張を段 3 の敵対相談が 4 点訂正した** (逐語は insight へ凍結)
  - 走行中の早期 qdel の成立条件は「順番待ち > grace」ではなく概ね `Q < W+G < Q+D`
    (Q=順番待ち、W=walltime、G=grace、D=実行時間)。`Q > G` は必要条件の一部にすぎない
  - fake scheduler と実 scheduler の差は「状態の観測粒度だけ」ではない。qsub/qstat の実所要、
    `_run` の 30 秒 timeout、poll overshoot も deadline 算術に入る
  - **「試行が台帳から欠落する」は現行 consumer では不正確。** 正しくは receipt が
    `outcome.kind="infra"` / `reason="overall-timeout"`、task-run 台帳が `exit_status=16`、
    変異台帳が当該 record を `PARSE_ERROR` にして `summary.completed` が増えない
  - dispatcher は開発用 harness 専用 (`TASKS` は `tests` / `provenance` の 2 種) であり、
    **certified 選択・材料レポートの値を直接変える caller は今日は存在しない**。
    ただし受入全走そのものが既定 (walltime 30 分 / grace 300 秒 / queue 上限 900 秒) で
    `Q < W+G < Q+D` を満たしうる実経路であり、dev-wave の受入証拠が infra 失敗へ倒れる
- **段 6 で親の実装案に穴が見つかった。** 最初の実装は `run_seen` を rc gate より先に立てていたため、
  rc≠0 の偽 RUN が latch を潰し、**その後に正常な RUN が来ても予算を張り直せない**状態が残っていた。
  レビュー 1 が must-fix として摘出し、latch 分離で閉じた ({{F:untrusted-run-latch-poisoning}})
- **焦点再レビューが変異登録の 2 件を差し戻した。** (a) 猶予項を落とす変異が受理集合を変えず
  診断値だけの赤になっていた → 正例テストを 1 本足して意味のある kill にした、
  (b) 期待赤 node 集合が主検出先だけだった → 変異ハーネスは失敗 node 集合の完全一致を要求するため
  全赤集合を登録し直した。**この 2 件はコード欠陥ではなく親の変異設計の欠陥である**
- **実行形の制約 (段 3 で判明)。** runbook §7 は login node での pytest を**部分走も**禁じている。
  実装子・レビュー子には pytest を走らせず、受入全走・provenance 監査・変異 matrix はすべて
  計算ノードへ dispatch した。実装子の「緑」は 1 度も採らず、親の dispatch 実測だけを証拠にした
- **変異 matrix は dispatch mode の自己参照になる** (dispatcher を変異させて dispatcher で走らせる)。
  `--runner-mode local` は計算ノードを外側で確保する経路が未整備 (D131 前提 3) のため採らなかった。
  `PARSE_ERROR` は kill に数えない方針を台帳へ明記した
- **変異 matrix (dispatch mode、統合 commit `aa79e3f` を anchor):** 登録 6 / KILLED 6 /
  MISMATCH 0 / SURVIVED 0 / PARSE_ERROR 0 / TIMEOUT 0、baseline PASSED。期待赤 node 集合は
  全 6 件で完全一致した。台帳と spec、子成果物の逐語は
  `output/insights/2026-08-03_t363-dispatch-deadline/`
- **親の手順ミスで matrix が 1 度止まった (実害なし)。** 5 件目まで走った時点で親が
  `docs/spool/` の fragment を書き、ハーネスが「実行前に untracked file を検出」で fail-closed 停止した
  (`DW-O19` の「変異中は clean tree」を親が破った)。fragment を repo 外へ退避し、
  同じ HEAD と spec sha へ束縛された `--resume` で残り 1 件を完走させた。防壁は設計どおり働いており、
  変異結果の汚染はない
- **並行 wave:** `dev-wave-t361-362-probes` が同時刻に [T-361]/[T-362] の probe を実行していた。
  land は `dev_wave_land.py` の lock で直列化される
- 子の内訳: 段 3 敵対相談 2 本、段 5 実装 1 本、段 6 敵対レビュー 2 本 + fix 2 本 + 焦点再レビュー 1 本
  (いずれも codex `gpt-5.6-sol`)。段 2 のプラン起草は親が file:line 粒度の方針を持っていたため省いた

## 次の一手差分

### 完了

- [T-363] `total_deadline` の起点を rc=0 の RUN 初観測へ移し、走行中ジョブの早期 qdel 経路を塞いだ。
  受入全走 5268 passed / 19 skipped (計算ノード dispatch)、変異 6 件登録。
  射程限定と残る未解決経路は {{D:run-observation-deadline}} に記録した。
  remaining: none
  base: 2aad2f2babe8f1e182922d020ee4e93be7b07f9a1975b7ade2455e7da5f00d52

### 新規

- {{T:active-job-qdel-prohibition}} **P1・ユーザー裁定待ち**: infra error 時に**走行中ジョブへ
  qdel を打たない**方針への転換 (D131 前提 6 の後半)。`active` は qsub 成功で立ち scheduler の
  QUE/RUN を表さないため、現在は immediate qstat の permission error / request 不在、
  外側 except (queue/overall timeout・signal・収集例外)、compute marker 不在の 4 経路が
  走行中を殺しうる。択一は **(a)** `run_seen` 後の自動 qdel を禁止し scheduler walltime と
  人間 handoff に委ねる / **(b)** fresh な rc=0 qstat が QUE/HLD/STG を示したときだけ
  取り消しを許し UNKNOWN・error では殺さない。**推奨は (b)** — (a) は孤児ジョブを増やす。
  [T-360] の前提であり、本 wave では実装していない
- {{T:running-job-state-evidence}} **P2・新規**: UNKNOWN のまま実際は走行中のジョブを保護する。
  任意の UNKNOWN を RUN 扱いする案は採らない (scheduler の schema drift と malformed 出力を
  長時間受理するため)。scheduler の権威ある証拠 (started timestamp 等) で RUN を確認する案の可否を
  設計する。{{T:active-job-qdel-prohibition}} と同じ束
- {{T:dispatch-timeout-input-validation}} **P2・新規**: `queue_wait_timeout_s` /
  `overall_grace_s` / `accounting_grace_s` / `poll_interval_s` が `NaN` / `inf` / 巨大有限値を
  受理し、監視ループの上界が消える。CLI は `type=float` なので `nan` / `inf` が通る。
  `math.isfinite` 検査と poll の上限を入れる (受理集合の縮小のため過剰拒否の正例も要る)
