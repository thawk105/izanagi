# 8c 自律 trial を 1 allocation で完遂させる予算設計 (2026-08-01)

`authority: none` / `default_effect: no-state-change`

可変状態の正本ではない。設計メモ + ユーザー裁定パッケージである。実装は行っていない
(理由は §6)。可変状態の正本は `docs/worklog.md` 末尾と `docs/phase3.md`。

## 0. 問い

> 1 allocation で完遂する budget 設計。Pegasus は `allow_resume=False`、supervisor 側も
> crash resume は MVP 範囲外。`--max-wall-seconds` を gen_S の walltime 内に収め、途中 kill 時は
> WAL を証拠として残す前提で世代数を決める。ベンチは排他実行なので並列に何本も回して稼げない —
> 8c の予算第一単位がベンチ実時間 (秒) でトークンでないのはこのため。回すなら「1 本を長く」。

この設計が izanagi の CC 合成に必要か、必要ならどう作るかを、実測と既存の凍結先例から決める。

## 1. 実測した前提

### 1.1 1 iteration の実コスト (既存 campaign WAL、n=51 variant)

`output/campaigns/*/runs/wal.jsonl` の `build_start` → `build_done` → `verify_done` → `bench_done`
の ts 差。`jq` + `awk` で集計 (`python3` は `guard_bash` が WAL 経路で拒否する — F63 と同型)。

| 段 | min | p50 | p90 | max |
|---|---:|---:|---:|---:|
| build (cache hit 込み) | 0.0 | 0.3 | 45.2 | 46.7 |
| verify (legacy+S2) | 10.1 | 12.9 | 24.1 | 26.6 |
| **bench** | 2.4 | **120.1** | **159.3** | **334.8** |
| build+verify+bench | 29.4 | 147.0 | 193.3 | 406.3 |

**実測 bench wall は名目 `extime × reps` を大きく上回る** (process 起動・settle・直前競合検査・retry を
含むため)。これは 8b floor protocol の相談で既出の指摘 (B4'、
`output/insights/2026-07-16_s8b-floor-protocol-consultations.md` §4) と同じ現象を、別 campaign 群で
独立に再現したものである。予算式の bench 項に名目値を使ってはいけない。

### 1.2 LLM role 呼び出しの上限

`CLAUDE_TIMEOUT_S = 1200` (`orchestrator/campaign/s8b_prediction_runner.py:71`)。8c の
`claude_projected_provider.py` も同一定数を import して `timeout=` に渡す。
1 generation あたり planner / coder / auditor / critic の **4 回**。

### 1.3 gen_S の walltime 上限

`qstat -Qf gen_S` 実測 (2026-08-01):

```
(Per-Req) Elapse Time Limit = Max: 86400S Warn: 86400S Std: 86400S
```

**1 リクエストあたり 86400 秒 = 24 時間**。`debug` は最大 1 時間、`interactive` は最大 24 時間
(runbook §「キュー」)。したがって「1 本を長く」の上限は 24 時間である。

### 1.4 停止判定が入っている位置 (= 現在の弱さ)

- 8c supervisor: workload 先頭と generation 先頭の 2 箇所だけ
  (`p3_autonomous_workload_trial.py:908`, `:656`、`worktree-dev-wave-t207-p3-trial-adopt` 版)
- 安全 loop: `p3_s4_loop.check_stop()` も iteration 入口だけ。`MAX_ITER = 10` /
  `MAX_WALLTIME_S = 3600` は**モジュール定数**で CLI から動かせない (`p3_s4_loop.py:80-81`)

いずれも「次の境界で開始を止める閾値」であって hard wall ではない。**期限を 1 秒過ぎて generation に
入ると、最悪 4×1200 + build + verify + bench を新規に開始する。**

## 2. 既存の凍結先例 — 新発明しない

「1 allocation で完遂する予算」の部品は **すでに main に実装され、正式系列が消費している**。

| 部品 | 実体 | consumer |
|---|---|---|
| scheduler reservation の束縛と残時間検査 | `orchestrator/campaign/reservation.py` (277 行) | `s8b_floor_campaign.py:2775-2790`, `s8b_oracle_driver.py:800-804` |
| 計測直前の再検査 | `s8b_floor_campaign.py:2002-2036` (`_recheck_reservation_before_measurement`) | 同 |
| walltime envelope の凍結式 | `s8b_floor_campaign.py:165-175`, `:640-678` | 同 |
| ベンチ秒台帳 (事前一括 reservation) | `s8b_budget.py` (625 行) | `s8b_oracle_driver.py:1141-1470` |

`reservation.py` は `IZANAGI_RESERVATION_*` 環境変数から
`{job_id, requested_s, scheduler_started_epoch, deadline_epoch, host, boot_id, script_sha256, nonce}`
を strict に読み、`check_reservation(required_s=, safety_margin_s=)` で

- 現在の `PBS_JOBID` が binding と一致するか
- 現在の `boot_id` が binding と一致するか (= 同じ node の同じ起動か)
- **残時間 ≥ required_s + safety_margin_s** か

を検査し、以後使う **monotonic deadline** を返す。`is_reservation_required()` は
`isolation_policy.single_process` から導出する。

floor の凍結式 (`_FLOOR_RESERVATION_FORMULA`) は次のとおりで、**cap を積んだ上界**を予約する。

```
required_s = cell_count * (build_cap_per_cell_s
             + (scheduled_attempts_per_cell + retry_slots_per_cell)
               * (bench_extime_s * reps + verify_cap_per_attempt_s))
safety_margin_s = finalize_reserve_s
```

定数は `build_cap = 900s` / `verify_cap = 120s` / `finalize_reserve = 600s`
(`s8b_floor_campaign.py:168-170`)。finalize reserve は terminal/result の fsync と
rejection forensic の退避枠である。

> **runbook の記述は古い。** `docs/pegasus-runbook.md` の env contract 登録段は
> 「残 walltime の事前予約検査 / WAL・成果物の永続領域 allowlist / build cache の
> contract_sha256 namespace 分離 / 実環境 attestation」を **wave3 時点で未実装**と記録しているが、
> 2026-08-01 時点では `reservation.py` / `durable_root.py` / `buildcache.py` の
> `contract_sha256` / `env_attestation.py` が実装され floor・oracle が消費している。
> **Pegasus entry 自体も `env_contract.py:180-193` に登録済み**
> (`clocks_per_us=2100`、`numactl=()`、`attestation_mode="required"`、
> `single_process=True` / `allow_resume=False`、calibration
> `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`)。

## 3. 8c 版の予算式 (提案)

floor の凍結式族をそのまま 8c へ移す。8c の「cell」は workload、「attempt」は generation であり、
役割呼び出しが 1 世代 4 回・retry なし (D106 決定 4) である点だけが異なる。

```
per_generation_s = role_cap_s * 4                         # planner/coder/auditor/critic
                 + build_cap_per_generation_s             # floor と同じ 900
                 + bench_cap_s + verify_cap_per_attempt_s # bench は実測上界、verify は 120

required_s      = workload_count * generations * per_generation_s
safety_margin_s = finalize_reserve_s                      # floor と同じ 600
```

**bench_cap は名目 `extime × reps` ではなく実測上界を使う** (§1.1)。n=51 の観測 max が 334.8 秒
なので、当面 `bench_cap_s = 400` を提案する (観測 max の約 1.2 倍)。

### 3.1 世代数の導出 (item 3 の本体)

上式を世代数について解く。

```
G_max = floor( (remaining_s - finalize_reserve_s) / (workload_count * per_generation_s) )
```

gen_S の 24 時間 (86400s)、workload = YCSB A/B/C の 3 本で数値を入れる。

| role_cap | per_generation_s | 3 workload × 1 世代 | **G_max (24h)** |
|---:|---:|---:|---:|
| 1200 (現行) | 6220 | 18660 | **4** |
| 600 | 3820 | 11460 | **7** |
| 300 | 2620 | 7860 | **10** (`MAX_GENERATIONS` の上限に到達) |

### 3.2 この表が示す最重要の設計事実

**最悪ケース envelope の 77% は LLM role の timeout であって bench ではない**
(現行 role_cap で 4800 / 6220)。したがって:

- 予算の**計上単位** (accounting) は phase3 §419 のとおり **ベンチ実時間 (秒)** で正しい。
  ベンチは排他実行で並列回収できない、真に希少な資源である
- しかし予算の**予約量** (envelope) を支配するのは role timeout である。
  「1 allocation で何世代回せるか」を増やす最短経路は、ベンチを速くすることではなく
  **role_cap を下げること**である

この 2 つは矛盾しない。別の量なので、設計上も別の名前で分けて扱う必要がある。

## 4. 途中 kill 時の証拠 (G12)

Pegasus の `isolation_policy` は `single_process=True` / `allow_resume=False`
(`env_contract.py:185`)。runbook の G12 は「campaign を単一 allocation/node/process で完遂。
walltime 不足・途中 kill は **WAL を証拠として保存した上で全数値を不採用**」と定める。

したがって本設計の停止は **「測定を短縮する」ではなく「開始しない」**でなければならない (規律 2)。
走り始めた bench を打ち切って部分値を採ることは、正しさゲートの緩和と同型の reward hack である。
具体的には:

- 残時間が次の step の envelope を満たさないなら、その step を**開始せず** clean stop する
- 停止理由は「どの step で、残 wall がいくつ、必要量がいくつだったか」を構造化して journal と
  report に残す (規律 3 — pass/fail でなく理由を返す)
- `finalize_reserve` を必ず残し、report と journal の fsync を完了させてから終了する

## 5. 構造的 blocker — 現状 8c は gen_S allocation の中で走れない

item 3 の前提「`--max-wall-seconds` を gen_S の walltime 内に収める」は、**8c supervisor が
gen_S ジョブの中で走ること**を仮定している。これは現状成立しない。

### B1. 計算ノードは外部 network 不可 (決定的)

`docs/pegasus-runbook.md` §7 に「**計算ノードは外部 network 不可**。github への DNS 解決不能を
2026-07-29 に request `873903` / `873904` で **2 回実測**」と記録されている。
8c supervisor は 1 世代あたり 4 回 `claude -p` を呼ぶため、計算ノード上では動作しない。

一方でベンチ・ビルド・テストをログインノードで走らせることは runbook §8 の投入前チェックリストが
明示的に禁じている。両者を繋ぐ正規経路 `tools/pegasus/dispatch_compute.py` の `TASKS` は
**`tests` と `provenance` の 2 種だけの閉じた enum** (`:56`, `:68`) で、任意 command 化は
D103 決定 5 と正面衝突すると同ファイルが明記する。

→ **supervisor (network 側) と bench (計算ノード側) を 1 つの gen_S ジョブに同居させられない。**

### B2. 8c が駆動する driver は env 定数をハードコードしている

`p3_s4_loop_trigger_gating.py:76-78` は `ENV_TAG = "linux-baremetal"` / `CLK = 1800` /
`NUMA = ["numactl","--interleave=all"]` を持つ (`p3_s4_loop.py:70-71` にも同じ複製)。
これは `env_contract.py` の `linux-baremetal` entry の値の**複製**であり、同 registry の docstring が
「env 固有 literal はこの関数の内部にのみ現れる」と宣言している契約に反する。
Pegasus entry は `numactl=()` / `clocks_per_us=2100` なので、この driver 族は現状 Pegasus を選べない。

### B3. 帰結 — `DW-G04` により「gen_S 由来の世代数決定」は実装しない

dev-wave の `DW-G04` は「条件付き機能は、発火条件を満たす既存 artifact path か計測 ID を brief に
書ける場合だけ実装する。書けなければ設計メモに留める」と定める。B1 が解けるまで
「gen_S の残 walltime から世代数を決める」機能の発火条件を書けない。よって本メモに留める。

## 6. 実装しなかった理由 (2 つ)

1. **B3 (上記)** — gen_S 由来の deadline 導出は発火条件を書けない
2. **所有** — マシン非依存部分 (hard wall 化・ベンチ秒計上) の対象である
   `orchestrator/campaign/p3_autonomous_workload_trial.py` は **main に存在しない**。
   別セッションの wave [T-207] が branch `worktree-dev-wave-t207-p3-trial-adopt` で取り込み中で、
   本メモ執筆時点で稼働していた。`DW-STOP` の「所有が不整合」に該当するため触れていない

## 7. ユーザー裁定に返す設計択一

### 裁定 1. 8c を Pegasus で回すための transport (B1 の解き方)

| 案 | 内容 | 「1 allocation で完遂」との整合 | コスト |
|---|---|---|---|
| **(a) login controller + compute worker (共有 FS 経由)** | 1 本の gen_S ジョブが計算ノードで worker loop を張り、共有 filesystem 上の proposal ファイルを待って build/verify/bench し結果を書く。login 側 supervisor が `claude -p` を呼びファイル交換する | **満たす。** allocation は 1 本を保持し続け、campaign 自体は計算ノードの単一 process で完遂する (G12 適合) | 中。worker protocol と、`dispatch_compute.py` の閉じた enum に新 task を足す裁定が要る |
| (b) 世代ごとに qsub | 1 世代 = 1 allocation。login 側が世代ごとにジョブを投げる | **満たさない。** campaign が複数 process に跨り `single_process=True` に反する | 小 |
| (c) Pegasus では回さない | 8c は linux-baremetal のまま。予算設計は「1 プロセスを落とさず完遂する」意味に縮小 | PBS の意味では非該当。ただし hard wall と bench 計上の価値は残る | 最小 |

**推奨は (a)。** ただし `DW-G01` (生死実験先行) に従い、本格実装の前に 100 行以内の使い捨て worker で
「計算ノードの worker が共有 FS 経由で login からの指示を受けて 1 回 build/bench し結果を返せるか」を
最安で確認すること。この確認前に専用機構を作らない。

### 裁定 2. role_cap を下げるか

§3.2 のとおり、1 allocation あたりの世代数を増やす最短経路は role_cap の低減である
(1200 → 600 で G_max が 4 → 7)。ただし role_cap は打ち切り = `role-invalid` を意味し、
cell がその場で停止する (D106 決定 4)。**打ち切り率を上げてまで世代数を買うか**は、
証拠の質に関わる裁定でありユーザーに返す。

参考: 実測が要る。既存の 8c dry-run
(`output/insights/2026-07-29_t178-autonomous-ycsb-abc-dry-run.md`) は 12/12 valid だが、
**role ごとの実所要時間を計測していない**。role_cap の裁定にはまずこの実測が要る。

### 裁定 3. 名目 bench 項を実測上界へ置き換えるか (floor 側にも波及)

§1.1 の実測は floor の凍結式が使う `bench_extime_s * reps` が実 bench wall の下界でしかないことを
別 campaign 群で再現した。8c で `bench_cap_s` を実測上界にするのは本メモの提案だが、
**同じ問題が floor の凍結式にもある**。floor 側は凍結済みなので変更は別裁定・別手続 (D96) になる。
`DW-G03` (族一般化には独立 2 例) の観点では、8b consultations の B4' と本メモの n=51 で
**独立 2 例が揃っている**。

## 8. 実装しないと成果物がどう変わるか (`DW-G05`)

- **裁定 1 が (a) または (b) で解かれない限り、8c は Pegasus で 1 回も走らない。** 現在の 8c は
  linux-baremetal 専用であり、Pegasus の計算資源は 8c に対して未使用のままになる
- **hard wall 化しないまま長い無人走行を始めると、期限超過後に開始した generation が最大
  4×1200s + build + bench を追加消費する。** Pegasus では PBS kill → `allow_resume=False` により
  **その allocation の全数値が不採用**になり、試行台帳にその allocation 分の欠落が残る。
  linux-baremetal では kill されないが、排他ベンチロックを想定外に長く保持する
- ベンチ実時間の独立計上がないままだと、phase3 §419 が定める「予算の第一単位」を
  8c は測っていないことになる。予算消費の実績が report に出ないため、次の allocation の
  世代数を実績から決められない

## 9. 還元判断

CCBench 本体への還元は無し (本メモは orchestrator 側の設計)。
**裁定 1〜3 はユーザー確認待ち。**
