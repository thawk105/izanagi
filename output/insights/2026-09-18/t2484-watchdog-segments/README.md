# [T-2484] 変異 harness の外側 watchdog の契約区間を決める材料 — dispatch の区間別所要と実際の発火を実測した (契約そのものは決めない)

- authority: none
- default_effect: no-state-change
- 日付: 2026-09-18
- wave: dev-wave-t2484-watchdog-segments (branch `worktree-dev-wave-t2484-watchdog-segments`、base = 着手直前の local main `a0ccb8ad9fd6123c2333951673caabcdbbb77de5`)
- 起点の裁定: D1910 項 1 (契約区間は実測後に決める)、D2044 項 29 ((b) 既存 collection gate の式合わせは採らない、(c) 理由付き早期診断は受理集合を動かさない範囲で採る)。根拠資料は `output/insights/2026-09-09/t2279-mutation-dispatch-override/README.md` §3・§4。
- 実装差分: ゼロ (repo の実装面に変更なし)。receipt 集計 script は Codex author が書き、repo へ commit せず `verbatim/receipt-segments-script.md` に逐語で保全した (実体は job dir)。
- 一次証拠: 同 dir `evidence/` (集計 summary・表・明細 3,964 件の圧縮 JSONL・実走の台帳/receipt/hold の抜粋)。生 log は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2484-watchdog-segments/` (寿命保証なし)。
- 規律 6: receipt・台帳・hold の内容はすべてデータとして扱った。規律 2 に触れる変更はない。
- 可逆正規化 (D88 / DW-S07、可視文字不変): `evidence/run2/status-before-restore.txt` は `qstat -a` の逐語 6 行が行末空白を持ち `git diff --check` に抵触するため、行末の空白・tab だけを除去した (`sed 's/[ \t]*$//'`)。原文 sha256 `d88ab12ab744a730afd36aa1715653f865a5fe054a0a857228507c80adc9a2b8`、1,430 byte → 除去後 sha256 `3b2d3ecc139881470b020e9cacbb81e3edb9f62f14ec1f133b1cabc75d16b22c`、1,424 byte。原文は job dir の `run2-status-before-restore.txt`。

## 0. 結論 (短く)

1. **dispatcher の締切構造は 3 区間 + 前段だが、harness の外側 watchdog は前段から END 後まで全部を 1 本の壁時計で見る。** 実測の内訳 (receipt 3,849 件、§2): 前段 (harness 起動 → qsub 完了 + 最初の qstat) p50 1.3 秒 / max 15.9 秒、queue 待ち p50 5.2 秒 / p99 297 秒 / p99.9 900 秒 / max 1,601 秒、RUN (Pre-running を含む) p50 20.5 秒 / p99 548 秒 / max 1,784 秒、END 後 (回収 + cleanup + receipt 書出し) p50 5.2 秒 / max 36.5 秒。
2. **外側 watchdog がどの区間で発火するかで帰結が違う (receipt 15 件の infra 記録、§3)。** queue 待ち中 (QUE) に外側 watchdog (SIGTERM) が発火すると dispatcher は fresh-qstat gate で 0.15〜0.26 秒で qdel に成功し `job_may_remain=false` で閉じる (4/4)。RUN 中 (scheduler の Pre-running を dispatcher は RUN と分類する) に発火すると gate が `state-not-cancellable` で qdel せず `job_may_remain=true` → orphan hold (receipt 6/6 + 本 wave の実走 1)。dispatcher 自身の queue-wait-timeout (Q=900 秒) は 4 件で、qdel は 3 件が 0.15〜0.26 秒で成功、今朝 08:33 の 1 件は Staging 状態で 10.5 秒かかり `job_may_remain=true` だった。
3. **既存 artifact (t2195 spec、timeout 3,600 / hang 900) を今日の混雑下で走らせても発火しなかった (§4)。** gen_S は QUE 67 / RUN 35 だったが自分の 3 dispatch はいずれも queue 待ち 5.2 秒で、M9 (hang_risk) は 27 秒で KILLED。**gen_S の QUE 数は自分の queue 待ちの予測にならない** (QUE 9 で 902 秒待ち、QUE 67 で 5 秒。§2 の bucket 表も単調でない)。
4. 外側 timeout を X 秒に置いたとき、過去の dispatch 3,849 件のうち X 秒を超えた割合 (§2.3): 300 秒で 4.6% (うち queue 待ち中 37 件 / RUN 中 141 件)、600 秒で 1.4%、900 秒で 0.55% (5 / 16)、1,200 秒で 0.26% (1 / 9)、1,800 秒以上で 0 件。hang_risk 変異の `hang_timeout_seconds=900` は 0.55% の確率で発火し、そのうち 3/4 は RUN 中 (= orphan hold) である。
5. **契約 (a) は決めない** (D1910 項 1 のとおり)。実測値と候補契約の対応は §6 の裁定パッケージに置き、索引へ戻す。

## 1. 何を測ったか

| 実測 | 道具 | 対象 |
| --- | --- | --- |
| A. 区間別所要 | `tools/pegasus/dispatch_compute.py` が書く `receipt.json` (`state_history` の `elapsed_s`、`queue_wait_s`、`qdel.cleanup_elapsed_s`、`preflight.qstat_Q`) を集計 script で読む | main checkout + `.claude/worktrees/*` + `.codex/worktrees/*` + `/work/1/SFC/tanab/dev-wave-jobs/**` (harness の `.dispatch-evidence` 複製を含む) の receipt 3,964 件。request_id の重複は 2 件 |
| B. 履歴の発火 | receipt の `outcome.kind=infra` と `qdel` 記録、`docs/failures.md` の F 台帳 | infra 15 件 (§3.1)、F185 再発 4 件・F529・F612・F762・F901・F990 (§3.2) |
| C. 実走 | `tools/mutation_harness.py` (dispatch mode、D612 上書き Q=3000 / G=600) を専用 container worktree (`.codex/worktrees/t2484-mutcontainer`、a0ccb8ad9) に当てる | t2195 spec の subset (baseline + M9 hang_risk) 原本 timeout のまま (§4)、続けて hang_timeout を 4 秒に縮めた派生 spec で発火の機構を観測 (§5。20 秒の run3 は §5.2 の理由で実施しない) |

模擬と実の差: §4 は原本 spec の変異 bytes・timeout と同一で、集合だけ 22 → 1 (M9) に縮めた (発火は `hang_timeout_seconds` と queue 待ちだけで決まり、変異の個数に依らない)。§5 は timeout 値を変えた派生 spec であり、原本の発火確率を示すものではない (発火したときに何が起きるかの機構だけを示す)。

## 2. 実測 A — 区間別所要 (receipt 3,849 件)

出典: `evidence/receipt-segments.summary.json`、`evidence/receipt-segments.table.md`、明細 `evidence/receipt-segments.records.jsonl.gz`。集計 script は `verbatim/receipt-segments-script.md`。receipt 3,964 件のうち 115 件は `state_history` が空で集計から除いた (全件 `DispatchError: qstat -Q preflight rc=1` = scheduler に届く前の infra 失敗、投入なし)。

### 2.1 dispatcher の締切構造 (現行 `tools/pegasus/dispatch_compute.py`)

- 前段: dispatcher 起動 → 準備 → `qsub` → 最初の `qstat -f`。harness の壁時計はこの前に `tools/run_tests.py` の起動を含む。
- queue 待ち: `now - queue_started >= queue_wait_timeout_s` (Q、既定 900) で `queue-wait-timeout`。RUN を初観測するまで。**scheduler の `Pre-running` は RUN に分類される** (`orchestrator/scheduler_nqsv.py` の `gate_state_value`: `"pre-running" → "RUN"`)。
- RUN 後: `run_observed_at + walltime_s + overall_grace_s` (既定 3,600 + 300) で `overall-timeout`。
- END 後: 回収 (`accounting_grace_s` 60 秒) と cleanup (`cleanup_budget_s` 90 秒)。
- SIGTERM 受信時: qsub 後なら fresh-qstat gate を通し、直前 snapshot が cancellable (QUE) なら qdel、RUN なら `state-not-cancellable` で qdel せず `job_may_remain=true`。qsub 前は `pending-qsub` の hold を latch する (正常時も qsub 前に latch し終端証拠後に消す。§4 で一時的に観測)。

### 2.2 区間別の分布 (秒、nearest-rank)

| 区間 | n | min | p50 | p90 | p99 | p99.9 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 前段 `t_first_qstat_s` | 3,849 | 1.1 | 1.3 | 1.4 | — | — | 15.9 |
| queue 待ち (observed + derived) | 3,849 | 0.1 | 5.2 | 5.3 | 296.8 | 900.2 | 1,601.0 |
| RUN (`run_s`、Pre-running 含む) | 3,835 | 10.2 | 20.5 | 92.3 | 547.8 | 1,203.9 | 1,783.5 |
| END 観測までの合計 `t_last_s` | 3,849 | — | 26.9 | 134.3 | 680.2 | 1,492.9 | — |
| END 後 `post_end_s` (worktree 現物 485 件のみ) | 478 | 0.5 | 5.2 | 6.0 | — | — | 36.5 |
| qdel cleanup `cleanup_elapsed_s` | 15 | 0.1 | 0.2 | 0.3 | — | — | 10.5 |

`post_end_s` は file mtime による近似で、`cp` 複製された receipt では mtime が揃い負値になるため worktree 現物 (`evidence/receipt-segments.table-worktrees-only.md`) だけで読む。

**Pre-running の分離 (receipt の RUN は Pre-running を含む)。** dispatcher は `Pre-running` を RUN と分類する (§2.1) ので、receipt の `run_s` には「node は割り当てられたが job がまだ始まっていない」時間が混ざる。job が node で始まった時刻は submission dir の `compute-visible.json` (計算ノード自身が書く marker) の mtime で取れる。現物が残る 3,755 件で `Pre-running ≈ compute-visible.json の mtime − (dispatch.sh の mtime + 最初の RUN 観測 elapsed)`、`実 RUN ≈ END 観測 − (compute-visible.json の mtime − dispatch.sh の mtime)` を取ると:

| 区間 | n | min | p50 | p90 | p99 | max | ≥300 秒 | ≥600 秒 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pre-running (node 割当後、job 開始前) | 3,755 | 1.4 | 3.6 | 25.6 | 397.6 | 794.6 | 83 (2.2%) | 14 (0.37%) |
| 実 RUN (job 開始 → END 観測) | 3,755 | 5.3 | 13.7 | 54.5 | 207.2 | 1,120.9 | — | — |

つまり receipt が RUN と記録する時間の長い側は Pre-running が支配する (p99 398 秒 vs 実 RUN p99 207 秒)。§5 の実走でも collection dispatch (5441.nqsv) が Pre-running に 676 秒 (09:45:50 → 09:57:03、bnode054) 留まり、job 本体は 1.6 秒だった。**この区間の発火は dispatcher の gate では `state-not-cancellable` (RUN 扱い) になり qdel されないが、job はまだ何も実行していない。**

queue 待ちの閾値超え: ≥300 秒 37 + derived 5 件 (1.1%)、≥600 秒 19 + 4 (0.6%)、≥900 秒 5 + 4 (0.23%)、≥1,200 秒 1 件、≥3,000 秒 0 件。derived は dispatcher が RUN を見ずに終わった件の下限 (timeout / SIGTERM)。

投入時の gen_S QUE 数 bucket と queue 待ち: 0〜9 (n=2,293) p90 5.3 / max 1,601 / ≥900 が 4 件、10〜49 (777) p90 10.3 / max 875、50〜99 (672) p90 5.3 / max 902 / ≥900 が 1 件、100 以上 (107) p90 51.1 / max 830 / ≥900 は 0 件。**単調でない。** 900 秒超は QUE 0〜9 に集中しており、QUE 数は自分の待ちの予測子にならない (receipt の preflight は `qstat -Q` しか持たず、node の空きや自分の稼働 job 数は記録されない)。

### 2.3 外側 timeout を X 秒に置いたときの発火率 (過去の dispatch に当てはめた反実仮想)

harness の壁時計 ≈ 前段 + queue 待ち + RUN + END 後。`t_last_s` (END 観測) を近似に使う。

| X 秒 | `t_last_s ≥ X` | 割合 | うち queue 待ち中 (`queue_wait ≥ X`、cancellable) | うち RUN / Pre-running 中 (orphan hold) |
| --- | --- | --- | --- | --- |
| 60 | 839 | 21.8% | 100 | 739 |
| 120 | 400 | 10.4% | 75 | 325 |
| 180 | 313 | 8.1% | 59 | 254 |
| 300 | 178 | 4.6% | 37 | 141 |
| 600 | 55 | 1.4% | 19 | 36 |
| 900 | 21 | 0.55% | 5 | 16 |
| 1,200 | 10 | 0.26% | 1 | 9 |
| 1,800 | 0 | 0% | 0 | 0 |

注意: 母集団は受入 shard・焦点走・変異走行など全種の dispatch で、RUN の長さは job の中身に依る。変異走行の 1 dispatch は RUN 10〜30 秒 (§4 の 3 件は 15.4 秒) なので、変異 harness で RUN 中に発火する主因は Pre-running の待ち (§5 の実走で 11 分 = 676 / 668 秒を観測) と混雑時の queue 待ちである。

## 3. 実測 B — 履歴の発火

### 3.1 receipt に残る infra 15 件 (出典: `evidence/receipt-segments.summary.json` の `firings` と明細)

| 日時 (JST) | request | 理由 | 発火時の状態 | 経過 (秒) | qdel gate | cleanup (秒) | job_may_remain | 投入時 QUE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 08-13 21:15 | 909493 | queue-wait-timeout (Q=900) | QUE | 901.5 | fresh-cancellable-snapshot | 0.15 | false | 2 |
| 08-13 21:15 | 909506 | queue-wait-timeout | QUE | 901.5 | fresh-cancellable-snapshot | 0.15 | false | 1 |
| 08-26 01:59 | 947995 | queue-wait-timeout | QUE | 903.6 | fresh-cancellable-snapshot | 0.26 | false | 75 |
| 09-18 08:18 | 5156 | queue-wait-timeout | QUE (qdel 時 Staging) | 902.7 | fresh-cancellable-snapshot | 10.47 | **true** | 9 |
| 08-17 22:45 | 919523 | SIGTERM (外側 watchdog) | QUE | 390.2 | fresh-cancellable-snapshot | 0.15 | false | 130 |
| 08-21 01:52 | 928116 | SIGTERM | QUE | 298.0 | fresh-cancellable-snapshot | 0.16 | false | 50 |
| 08-21 02:00 | 928128 | SIGTERM | QUE | 298.1 | fresh-cancellable-snapshot | 0.16 | false | 50 |
| 09-05 20:49 | 978653 | SIGTERM | QUE | 6.4 | fresh-cancellable-snapshot | 0.26 | false | 148 |
| 08-12 20:55 | 907709 | SIGTERM | RUN | 114.0 | state-not-cancellable | 0.10 | **true** | 0 |
| 08-25 20:25 | 947299 | SIGTERM | RUN | 113.8 | state-not-cancellable | 0.10 | **true** | 0 |
| 08-28 09:21 | 954415 | SIGTERM | RUN (Pre-running) | 179.8 | state-not-cancellable | 0.10 | **true** | 0 |
| 08-28 09:28 | 954432 | SIGTERM | RUN (Pre-running) | 179.8 | state-not-cancellable | 0.09 | **true** | 1 |
| 09-08 04:04 | 982504 | orphan-hold-release-failed | RUN | 298.1 | state-not-cancellable | 0.09 | **true** | 0 |
| 09-09 10:52 | 987143 | orphan-hold-release-failed | RUN | 175.4 | state-not-cancellable | 0.09 | **true** | 33 |
| 09-16 22:12 | 2117 | job bootstrap failure (result-guard) | END | 636.9 | request-absent | 0.14 | false | 0 |

読み方: SIGTERM の 298.0 / 298.1 秒は harness の `timeout_seconds=300` が dispatcher の時計より約 2 秒早く始まる (前段) ことの直接証拠。179.8 秒の 2 件は F185 再発 (2026-08-28、180 秒 timeout を Pre-running で超えた) の現物で、dispatcher は Pre-running を RUN と見て qdel しない。**queue 待ち中の発火は dispatcher が 0.3 秒以内に閉じられ、RUN / Pre-running 中の発火は job を残す。**

### 3.2 failures 台帳の記録 (receipt が消えた事例を含む)

| 台帳 | 日付 | 外側 timeout | 実際の待ち | 発火区間 | 帰結 |
| --- | --- | --- | --- | --- | --- |
| F185 再発 | 08-26 | hang 300 | queue 345 秒 | queue | orphan hold |
| F185 再発 | 08-28 | 180 | queue / Pre-running | Pre-running (上表 954432) | orphan hold、request 不在確認後に復旧 |
| F185 再発 | 09-09 | 300 | queue 8 分 (03:14 → 03:21:59) | queue → job は完走 | hold は誤検知、1,800 秒へ取り直し |
| F185 再発 | 09-16 | 600 | 他 session job 14 本 | queue | orphan hold、2,700 秒 + D612 上書きで完走 |
| F529 | (T-1480) | 300 | queue 5 分 17 秒、Elapse 10 秒 | queue | TIMEOUT を「hang」と誤読しかけた |
| F612 | — | dispatcher Q=900 | 903 秒 | queue (dispatcher 自身) | rc=16 PARSE_ERROR、5,400 秒へ |
| F762 再発 | 09-05 | dispatcher Q=900 | 903 秒 (M9) | queue (dispatcher 自身) | rc=16、`--resume` で完走 |
| F901 | 09-08 | hang 300 | job 内の真の hang | RUN | job は walltime 3,600 秒まで、45 分ブロック (982386) |
| F990 | — | (背景 job の片付け) | — | pending-qsub | hold 残留、job は完走 |
| F891 / F932 | 09-1x | collection gate `outer < Q+G` | — | 起動前 | rc=2 で 1 走も始まらない |
| F951 | 09-07 | 受入 Q 上書き 3,600 | shard 3 本が 3,291〜3,409 秒 | queue | lease TTL 2,400 秒超で receipt なし |

## 4. 実測 C-1 — 既存 artifact (t2195 spec、hang 900) を今日の混雑下で走らせた: 発火せず

- 時刻: 2026-09-18 09:33:49 〜 09:35:33 JST (harness 壁時計 104 秒)。gen_S は投入時 TOT 104 / QUE 67 / PRR 3 / RUN 34 (receipt の preflight)。
- spec: `output/insights/2026-09-07/t2195-policy-binding/mutation-spec-final.json` (sha256 `aabfcd1d…`) から M9 (`M9-gate-policy-drop-nofollow`、hang_risk、KILLED 期待) だけを残した subset (sha256 `20a707cc…`、`timeout_seconds=3600` / `hang_timeout_seconds=900` は原本と同一)。原本 22 変異は現行 main でも `--plan-only` rc=0 (anchor 全部一致)。
- 上書き: `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3000` / `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600`。collection gate `outer < Q+G` は 3,600 < 3,600 が偽で通る (等号は通る)。
- 結果 (台帳 `evidence/run1-mutation-m9.json`): collection 27.0 秒、baseline PASSED 27.2 秒、M9 KILLED 27.1 秒 (期待 node 一致)。3 dispatch (5430 / 5431 / 5432.nqsv) はいずれも 前段 1.3 秒 / queue 待ち 5.2 秒 / RUN 15.4 秒 / END 観測 21.8 秒 / END 後 約 5 秒。**外側 watchdog (900 秒) は発火していない。**
- 副観測: M9 の dispatch dir に 09:35:07 (dispatch.sh 09:35:06 の 1 秒後) に `orphan-hold.json` (phase `pending-qsub`、request_id null) が現れ、終端証拠の回収後に消えた。これは dispatcher が qsub 前に latch する正常な hold であって発火ではない。

## 5. 実測 C-2 — 発火の機構 (hang_timeout を 4 秒に縮めた派生 spec、run2)

原本 spec は今日の条件で発火しない (§4) ので、発火したときに harness / dispatcher / scheduler が何をするかを、M9 の `hang_timeout_seconds` だけを 4 秒にした派生 spec (`evidence/run2/spec-m9-hang4.json`、sha256 `c6e8b31c…`) で観測した。**これは原本の発火確率を示す実験ではない。** 上書きは §4 と同じ Q=3000 / G=600。

### 5.1 時系列 (JST、出典: `evidence/run2/attempts.json`、`receipts-excerpt.json`、`orphan-stop.json`、`timing.txt`)

| 時刻 | 主体 | 事象 |
| --- | --- | --- |
| 09:45:19 | harness | 起動 (`timing.txt`) |
| 09:45:49 〜 09:57:16 | collection (5441.nqsv、bnode054) | queue 待ち 5.2 秒 → **Pre-running に 676 秒** (09:45:50 → job 開始 09:57:03) → job 本体 1.6 秒 → END 観測 682.6 秒 |
| 09:57:29 〜 10:09:02 | baseline (5442.nqsv) | queue 待ち 5.2 秒 → **Pre-running に 668 秒** (job 開始 10:08:43) → END 観測 687.4 秒。PASSED |
| 10:09:06.72 | harness | M9 を注入し runner を起動 (`attempts.json` の `started_at`) |
| 10:09:07 | dispatcher | qsub → request 5452.nqsv (bnode042)。qsub 前に `pending-qsub` hold を latch |
| 10:09:08.0 | dispatcher | 最初の `qstat -f` (elapsed 1.26 秒) = QUE、hold を `5452.nqsv.json` へ昇格 |
| 10:09:08 | scheduler | Queued → **Pre-running** (Planned Start 10:09:29) |
| 10:09:10.9 | harness | `communicate(timeout=4)` が切れ、process group へ SIGTERM (`duration_s` 4.192) |
| 10:09:10 | dispatcher | SIGTERM → fresh-qstat gate: `Current State = Pre-running` → **`state-not-cancellable`、qdel せず** → `job_may_remain=true` → receipt を書いて終了 (`outcome.kind=infra`、rc=16、`_SignalAbort: signal 15`、`cleanup_elapsed_s` 0.097) |
| 10:09:14.8 | harness | `orphan-stop.json` を書き **rc=2** (`reason.code=orphan-hold`、`source_state=mutation-left-in-place`、dirty = `tools/pegasus/mocc_trace_pilot.sh`)。SIGKILL は不要だった (runner は 5 秒以内に終了) |
| 10:09:16 | job | 計算ノードで開始 (`compute-visible.json`)、10:09:22 `result.json`、10:09:31 終了 (.o/.e) — **変異が当たった source で走り切った** (harness は結果を回収しない) |
| 10:09:51 | 親 | `qstat -f 5452.nqsv` → `does not exist`、container は `M tools/pegasus/mocc_trace_pilot.sh`、hold 2 file (`status-before-restore.txt`) |
| 10:10:00 〜 10:10:09 | 親 | `git checkout --` で HEAD blob 一致を確認 → hold 2 file を退避して削除 (`restore.txt`)。復旧の手作業は 9 秒、hold の寿命は発火から 59 秒 |

### 5.2 読み方

- 4 秒の watchdog は queue 待ち (QUE) を狙ったが、scheduler は 1 秒で Pre-running へ遷移しており、発火時点の fresh qstat は RUN 扱いだった。**Pre-running では job はまだ始まっていないのに、gate は `state-not-cancellable` で qdel しない。** その後 job は変異を当てたまま走り (10:09:16 〜 10:09:31)、harness はその結果を見ない。
- dispatcher は SIGTERM から 0.1 秒で gate 判定と receipt 書出しを終え、harness の 5 秒の SIGTERM 猶予に収まった (§3.1 の 15 件も cleanup 0.09〜0.26 秒、例外は今朝の Staging 10.5 秒)。
- 同じ container で collection と baseline が Pre-running に 11 分ずつ留まった (bnode054 / bnode042 で異なる) 一方、M9 の job は 10 秒で始まった。**Pre-running の長さは投入ごとに 2 桁変わり、投入時の qstat では予測できない。**
- harness 側の帰結は timeout の発火区間に依らず同じ (code 読み、`tools/mutation_harness.py` の `_dispatch_orphan_stop`): `timed_out` なら dispatcher が qdel に成功していても `dispatch-runner-timeout` の hold を latch して rc=2、変異は残置。**区間の違いは「job が残るか」(scheduler 側) にだけ効く。**
- RUN 中 (job 実行中) の発火は run3 (hang 20 秒) で観測する予定だったが、機構は run2 と同じ gate (`state-not-cancellable`) で、§3.1 の receipt 6 件 (907709 / 947299 / 954415 / 954432 / 982504 / 987143) が既に同じ帰結を示しているため、queue を塞ぐ費用に見合わず実施しなかった。
- 復旧は hold の `recovery` field の順序どおりで 9 秒。所要の支配項は「job が自然終了するまでの待ち」で、真の hang (F901) なら walltime 3,600 秒 + G まで伸びる。

## 6. 裁定パッケージ — 契約 (a) の候補と実測値の対応 (本 wave は決めない)

記号: P = 前段 (≈ 1.3〜2 秒、harness の時計は dispatcher より約 2 秒早い)、Q = `queue_wait_timeout_s` (既定 900、D612 上書きで 1,200〜3,600)、W = walltime (3,600)、G = `overall_grace_s` (既定 300、上書き 600)、A = 回収猶予 60、C = cleanup 予算 90。dispatcher 自身の最長は `P + max(Q, q + W + G) + A + C` (q = 実際の queue 待ち)。

### 6.1 候補

| 候補 | 契約 | 必要な外側値 (既定 / 上書き 3600・600) | 過去 3,849 件での harness 先行発火 | 帰結 |
| --- | --- | --- | --- | --- |
| (a-1) 全区間を覆う | harness は dispatcher より先に切らない: `timeout_seconds ≥ P + Q + W + G + A + C` | 4,952 / 7,952 秒 | 0 件 (最長 1,784 秒) | timeout は全部 dispatcher の in-band (rc=16、fresh-qstat gate、`--resume` 可)。orphan hold は harness からは出ない。`hang_timeout_seconds` も同じ値になり、`DW-M06` の「dispatch では hang_timeout < walltime」と両立しない (改訂が要る) |
| (a-2) queue 待ち + grace を覆う (現行 collection gate の式) | `timeout_seconds ≥ Q + G`、RUN 中は dispatcher に委ねる | 1,200 / 4,200 秒 | 1,200 秒で 10 件 (0.26%): QUE 1 / RUN・Pre-running 9 → orphan hold 9 | 現状維持。`hang_timeout_seconds` は gate の対象外のまま (t2195 の 900 は既定でも Q+G=1,200 未満) |
| (a-3) queue 待ちだけを覆い、hang は dispatcher の walltime に委ねる | `hang_timeout_seconds` を外側 watchdog から外す (dispatch では job を kill できない、F901) か `= timeout_seconds` に固定 | (a-1) と同じ | 0 件 | hang_risk の意味を「local probe で観測し erratum で残す」(F901 の運用) に一本化。DW-M06 改訂が要る |
| (a-4) 区間認識の watchdog | harness が dispatcher の進行 (`compute-visible.json` の有無 = job 開始) を見て区間ごとに上限を持つ | 実装が要る ([T-2071] 見送りの再訪) | — | 受理集合に触れる新機構。本 wave の scope 外 |

### 6.2 実測が示す制約 (どの候補にも共通)

- queue 待ち ≥ 900 秒は 0.23% (9 / 3,849)、≥ 1,200 秒は 1 件、≥ 1,800 秒は 0 件。Pre-running ≥ 300 秒は 2.2%、≥ 600 秒は 0.37%。RUN (実) p99 207 秒、max 1,121 秒。
- **発火区間ごとの帰結**: QUE 中 → dispatcher が 0.3 秒以内に qdel し job は残らない (SIGTERM 4 件 + dispatcher 自身の Q timeout 3 件 = 7/8、例外は今朝の Staging 1 件 10.5 秒・remain=true)。Pre-running / RUN 中 → qdel せず job は自然終了まで残る (receipt 6 件 + 本 wave の run2 = 7/7)。harness 側は区間に依らず rc=2 + 変異残置 + hold。
- 投入時の gen_S QUE 数は自分の queue 待ち・Pre-running の予測にならない (§2)。よって「混雑時だけ値を変える」運用は receipt の preflight では組めない。
- D612 の上書きは queue 待ちの上限を伸ばすだけで、Pre-running・RUN の長さは変えない。

### 6.3 (c) 理由付き早期診断の具体案 (受理集合を動かさない、D2044 項 29 で採用済み、本 wave では実装しない)

1. 起動時: `hang_timeout_seconds < Q + G` および `timeout_seconds < P + Q + W + G + A + C` を、拒否せず stderr に理由付きで出す (どの区間で先行発火しうるか、過去 receipt での確率)。現行の collection gate は `timeout_seconds` しか見ないので、`hang_timeout_seconds` は無診断で通る。
2. 発火時: `orphan-stop.json` に submission dir の `compute-visible.json` の有無 (job が node で始まったか) と receipt の `qdel.gate.reason` を写す。「job が走っていないのに hold になった」(Pre-running 発火) と「job が走っている」を区別でき、復旧の待ち時間の見込みが立つ。

### 6.4 親の推奨 (裁定ではない)

(a-1) を `timeout_seconds` の契約とし、`hang_timeout_seconds` は (a-3) で外側から外す。理由: harness は dispatch mode で job を止められないので、先に切っても「hold + 変異残置 + job は自然終了まで残る」が増えるだけで、待ち時間は減らない (F901 の 45 分は dispatcher に任せても同じ)。in-band に寄せると rc=16 → `--resume` で続けられ、hold の手動復旧 (F453 / F530 の型) が消える。費用は 1 dispatch あたり最長 4,952 / 7,952 秒を harness が待つことだが、過去 3,849 件でその長さに達した dispatch は無い。関連の見送り [T-2071] (queue / Pre-running と child 実行の timeout 分離) は (a-4) に相当し、(a-1)/(a-3) を採るなら不要になる。

裁定に必要な追加の実測は無い。DW-M06 / DW-M07 の改訂と collection gate の式の扱い (D2044 項 29 の (b) 不採用と両立させる形) は裁定後の実装 wave が持つ。
