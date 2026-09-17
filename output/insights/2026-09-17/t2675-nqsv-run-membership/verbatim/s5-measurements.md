# 段 5 の実測 (逐語) — [T-2675]

probe = `tools/probe_t2675_run_membership.py` (Codex `role=author`、656 行、30,373 bytes、
sha256 `f781162298f8885bd8d73f9e5d65d0d763fa14cc7e1673dd9961d42f9dc5b3e1`、repo へは残さない)。
親の login selftest: 13 passed / 0 failed、wall 32.64 秒、rc=0 (`selftest-parent.log`)。

投入は全条件 `output/pegasus-dispatch/<digest>/` を持つ worktree から直列・detached
(`run-probe.sh` の argv = s4-ruling §3.2)。`E` = `.e` の `Ended Request Time` (JST)、
`J` = trace `job-run-returned` の `time_ns`、`t0` = evidence `start` の `realtime_ns`、`δ = J − t0`。

## M1. 条件 D `no-child` (統制) — 2026-09-17 22:07:38 投入 → 22:14:25 終了

request `4006.nqsv`、submission dir `output/pegasus-dispatch/7dd5d255468e4cfd8b1f21e957facf60/`、bnode033。

- `Started Request Time: Thu Sep 17 22:14:08 2026` / `Ended Request Time: Thu Sep 17 22:14:14 2026` / `Elapse: 10S`
- trace: `result-dir-fsync-complete` (…854001389017) の後に `job-run-returned` `time_ns = 1789650854001417624` → 22:14:14.001418 JST
- evidence 2 行: `start` (realtime 1789650848976639459)、`parent-exit` (1789650853977643413、t0+5.001)。`recording_errors` = []
- **`E − J = −0.001 秒` (0 窓)、`δ = 5.025 秒`**
- receipt: `terminal_reason = scheduler-end-state`、outcome `kind=child rc=0 accounting_verified=True`、`qdel.attempted = False`
- `output/pegasus-dispatch/orphan-holds/` = 0 件
- 所属: probe pid 1581889、ppid 1581875 (bootstrap)、**sid = pgid = 1581848** (job の session)
- 内側 user ns: `resuid = [31609, 31609, 31609]`、`uid_map = "31609 0 1"` (内側 31609 → 外側 0)、`user_ns = user:[4026535834]`。
  **probe から見える uid は実 uid の数値である (a-6 / b-5 のとおり)**
- env_keys: (evidence 参照。PBS_* は無い)

## M2. 条件 K `keep` (陽性対照) — 22:15:10 投入 → 22:16:42 終了

request `4026.nqsv`、submission dir `output/pegasus-dispatch/58197e22c1daa9a36c1eab4197a29bd7/`、bnode028。

- `Started: 22:15:16` / `Ended: 22:16:31` / `Elapse: 79S`
- t0 = 22:15:16.431995、J = 22:15:21.453915、最終 trace = `job-run-returned`
- **`E − J = 69.546 秒` (70 窓)、`δ = 5.022`、`E − t0 = 74.568`**
- evidence 19 行: `start` / `fork` / `child-start` (t0+0.001) / `child-alive` ×14 (t0+5.001 … 70.001、予定どおり) / `parent-exit` (t0+5.001) /
  `child-exit` (t0+75.001)。`recording_errors` = []。子は親終了後 ppid 3010070 → **1** へ、**sid = pgid = 3010029 (job) のまま**。
  fd 1/2 は job の stdout/stderr を保持 (前 wave C 相当)
- receipt: `scheduler-end-state`、rc=0、accounting_verified=True、qdel.attempted=False。orphan hold 0 件
- 前 wave (A 69.731 / B 69.586 / C 69.870) と同じ 70 窓。**陽性対照は再現した (適格)**

## M3. 条件 S0 `setsid-now` — 22:17:24 投入 → 22:18:15 終了 (dispatch)、evidence 回収は 22:19:34 まで

request `4035.nqsv`、submission dir `output/pegasus-dispatch/7b18c319266eeaa03985a653feb82573/`、bnode061。

- `Started: 22:17:29` / `Ended: 22:17:34` / **`Elapse: 9S`**
- t0 = 22:17:29.410828、J = 22:17:34.472919、最終 trace = `job-run-returned`
- **`E − J = −0.473 秒` (0 窓 = 待たない)、`δ = 5.062`、`E − t0 = 4.589`**
- 所属変更: `before-change` t0+0.002 (sid=pgid=2780317 = job)、syscall@t0+0.002、`after-change` **sid = pgid = 2780359 (= 子 pid)**、errno=None。成功
- evidence 14 行: `child-alive` は t0+5.001 … **40.001 の 8 回で途絶**。`child-exit` (t0+75) **無し**。`recording_errors` = [] (最終行まで)。
  親終了後 ppid 2780358 → 1。fd 1/2 は job の stdout/stderr を保持したまま
- 22:18:26 (t0+57) 時点で 14 行・最終 `child-alive`、22:19:34 (t0+125) でも 14 行。**t0+40 と t0+45 の間に子が消えたか記録不能になった**
  (job 終了 E = t0+4.6 の約 35〜40 秒後)。死因は evidence だけでは区別できない (SIGKILL / 停止 / I/O 障害)
- receipt: `scheduler-end-state`、rc=0、accounting_verified=True、qdel.attempted=False。orphan hold 0 件
- **読み (親、結果を見た後の解釈なので段 6 で攻撃対象):** E − J は 0 窓で、E より後の heartbeat が 8 回 (t0+10 … 40) あるので
  「E 時点の即時 kill」とは両立しない (§4.3 の 1 行目)。一方 §4.2 の「`child-exit` が t0+75±1 に無ければ打切り観測」と
  §5 の「早期死亡 → 実験不成立」の文言には当たる。**親は「E − J の分類 (待たない) は成立、子の寿命は t0+40 までしか言えない」と読む**

## M4. 条件 G0 `setpgid-now` — 22:20:47 投入 → 22:22:18 終了

request `4051.nqsv`、submission dir `output/pegasus-dispatch/d45ebf69b352e406846e5c797ad4c9a0/`、bnode028。

- `Started: 22:20:52` / `Ended: 22:22:08` / `Elapse: 80S`
- t0 = 22:20:53.218616、J = 22:20:58.243100、最終 trace = `job-run-returned`
- **`E − J = 69.757 秒` (70 窓 = 子の寿命まで待った)、`δ = 5.024`、`E − t0 = 74.781`**
- 所属変更: syscall@t0+0.002、`after-change` **pgid = 3095164 (= 子 pid)、sid = 3095122 (job のまま)**、errno=None。成功
- evidence 21 行: `child-alive` 14 回 (t0+5.001 … 70.001)、`child-exit` t0+75.001。`recording_errors` = []。親終了後 ppid → 1
- receipt: `scheduler-end-state`、rc=0、accounting_verified=True、qdel.attempted=False。orphan hold 0 件。**適格**

## M5. 条件 S30 `setsid-30` — 22:22:40 投入 → 22:23:56 終了 (dispatch)、evidence 回収は 22:25:28 (t0+163) まで

request `4056.nqsv`、submission dir `output/pegasus-dispatch/c3e9dab9db1109cf3805a4d7999e83b1/`、bnode033。

- `Started: 22:22:45` / `Ended: 22:23:15` / **`Elapse: 34S`**
- t0 = 22:22:45.309666、J = 22:22:50.331167、最終 trace = `job-run-returned`
- **`E − J = 24.669 秒` (25 窓 = 所属変更の時刻に会計終了が対応)、`δ = 5.022`、`E − t0 = 29.690`** (E は秒切捨て。setsid は t0+30.001 = 22:23:15.31、E = 22:23:15 → **setsid から 1 秒以内に job が終了**)
- 所属変更: t0+30 未満の heartbeat 6 回は sid=pgid=1661876 (job)、`before-change` t0+30.001、syscall@t0+30.001、`after-change` **sid = pgid = 1661918 (= 子 pid)**、errno=None。成功。30 秒の `child-alive` は変更の後 (t0+30.002)
- evidence 19 行: `child-alive` は t0+35 … **65.001 で途絶**、`child-exit` (t0+75) **無し**。`recording_errors` = []。22:25:28 (t0+163) でも 19 行
- **途絶は E (t0+29.7) の 35.3〜40.3 秒後。S0 (E = t0+4.6、途絶 t0+40〜45 = E の 35.4〜40.4 秒後) と同じ間隔** (2/2)
- receipt: `scheduler-end-state`、rc=0、accounting_verified=True、qdel.attempted=False。orphan hold 0 件

## M6. 条件 G30 `setpgid-30` — 22:25:51 投入 → 22:27:24 終了

request `4069.nqsv`、submission dir `output/pegasus-dispatch/69b0893b99c33cf4da15a1a8c197a1d7/`、bnode043。

- `Started: 22:25:57` / `Ended: 22:27:13` / `Elapse: 80S`
- t0 = 22:25:58.003679、J = 22:26:03.074075、最終 trace = `job-run-returned`
- **`E − J = 69.926 秒` (70 窓)、`δ = 5.070`、`E − t0 = 74.996`**
- 所属変更: `before-change` t0+30.001、syscall@t0+30.001、`after-change` **pgid = 1618115 (= 子 pid)、sid = 1618073 (job のまま)**、errno=None。成功
- evidence 21 行: `child-alive` 14 回、`child-exit` t0+75.001。`recording_errors` = []。**適格**
- receipt: `scheduler-end-state`、rc=0、accounting_verified=True、qdel.attempted=False。orphan hold 0 件

## M7. 集計 (6 条件、全 request の terminal_reason = scheduler-end-state、qdel.attempted = False、orphan hold 0)

| 条件 | request | node | Elapse | δ | **E − J** | 窓 | 所属変更 | 子の最終記録 |
|---|---|---|---|---|---|---|---|---|
| D `no-child` | 4006 | bnode033 | 10S | 5.025 | **−0.001** | 0 | — | (子なし) `parent-exit` t0+5.001 |
| K `keep` | 4026 | bnode028 | 79S | 5.022 | **69.546** | 70 | なし | `child-exit` t0+75.001 |
| S0 `setsid-now` | 4035 | bnode061 | 9S | 5.062 | **−0.473** | 0 | setsid @0.002 成功 | `child-alive` t0+40.001 (途絶、E+35.4〜40.4) |
| G0 `setpgid-now` | 4051 | bnode028 | 80S | 5.024 | **69.757** | 70 | setpgid @0.002 成功 | `child-exit` t0+75.001 |
| S30 `setsid-30` | 4056 | bnode033 | 34S | 5.022 | **24.669** | 25 | setsid @30.001 成功 | `child-alive` t0+65.001 (途絶、E+35.3〜40.3) |
| G30 `setpgid-30` | 4069 | bnode043 | 80S | 5.070 | **69.926** | 70 | setpgid @30.001 成功 | `child-exit` t0+75.001 |

数値ベクトル (S0, G0, S30, G30) = (0, 70, 25, 70)。**ただし S0 / S30 は `child-exit` 欠落で §4.2 不適格 (段 6 レビュー A-1 / B-1)** →
主解析は (不明, 70, 不明, 70) = B 類不適合、A / C / D 未分離。A 類との一致は事後解析。
**§3.3 (6) からの逸脱:** S0 の終端記録不足 (22:19:34 確認) の後に G0・S30・G30 を投入した。

## M8. 実験 2 (寿命短縮版、s4-ruling §8 で 22:45 に事前登録) — S0′ `setsid-now` 寿命 35 秒

22:40:34 投入 (detach)、NQSV Created 22:40:32 → **Pre-running (PRR) に 22:51:36 頃まで約 11 分停滞** (実行ホスト未割当。同時刻に親の他 session の
request 4115 / 4119 / 4124 / 4127 も PRR。原因は不明、qdel はしていない) → Started 22:51:40 → Ended 22:51:45 → dispatch 終了 22:52:27。

request `4108.nqsv`、submission dir `output/pegasus-dispatch/784ddc4ad67a80ec123fd8be601d1446/`、bnode037。

- `Elapse: 9S`、t0 = 22:51:40.417631、J = 22:51:45.456130
- **`E − J = −0.456 秒` (0 窓)、`δ = 5.038`、`E − t0 = 4.582`**
- 所属変更: syscall@t0+0.013、`after-change` sid = pgid = 3780609 (= 子 pid)、errno=None。成功
- evidence 13 行: `child-alive` 6 回 (t0+5 … 30)、**`child-exit` t0+35.001 (E の約 30.4 秒後)**。`recording_errors` = []。**§8 の適格性を満たす**
- receipt: `scheduler-end-state`、rc=0、accounting_verified=True、qdel.attempted=False。orphan hold 0 件
- §8 の予測: A / D 類 = 0 窓 (一致)、C 類 = [25, 35] (不適合)

## M9. 実験 2 — S30′ `setsid-30` 寿命 60 秒

22:55:15 投入 (detach)、NQSV Created 22:55:12 → Started 22:55:25 → Ended 22:55:57 → dispatch 終了 22:56:3x、evidence 回収 22:56:49 (t0+83)。

request `4133.nqsv`、submission dir `output/pegasus-dispatch/26c387b8329f0a9f91c6055f269a1977/`、bnode028。

- `Elapse: 35S`、t0 = 22:55:26.146833、J = 22:55:31.166615
- **`E − J = 25.833 秒` (25 窓)、`δ = 5.020`、`E − t0 = 30.853`** (setsid は t0+30.001 = 22:55:56.148、E = 22:55:57 → setsid から 0.85〜1.85 秒で会計終了)
- 所属変更: t0+30 未満の heartbeat 5 回は sid=pgid=4165974 (job)、syscall@t0+30.001、`after-change` sid = pgid = 4166017 (= 子 pid)、errno=None。成功
- evidence 18 行: `child-alive` 11 回 (t0+5 … 55)、**`child-exit` t0+60.001 (E の約 29.1 秒後)**。`recording_errors` = []。**§8 の適格性を満たす**
- receipt: `scheduler-end-state`、rc=0、accounting_verified=True、qdel.attempted=False。orphan hold 0 件
- §8 の予測: A 類 = [20, 30] (一致)、D 類 = [50, 60] (不適合)、C 類 = [50, 60] (不適合)

## M10. 最終集計

| 走 | 条件 | request | node | 寿命 | δ | `E − J` | 窓 | `child-exit` | 適格 |
|---|---|---|---|---|---|---|---|---|---|
| 実験 1 | D `no-child` | 4006 | bnode033 | — | 5.025 | −0.001 | 0 | — | ○ |
| 実験 1 | K `keep` | 4026 | bnode028 | 75 | 5.022 | 69.546 | 70 | t0+75.001 | ○ |
| 実験 1 | S0 `setsid-now` | 4035 | bnode061 | 75 | 5.062 | −0.473 | 0 | 無 (最終 t0+40.001) | × |
| 実験 1 | G0 `setpgid-now` | 4051 | bnode028 | 75 | 5.024 | 69.757 | 70 | t0+75.001 | ○ |
| 実験 1 | S30 `setsid-30` | 4056 | bnode033 | 75 | 5.022 | 24.669 | 25 | 無 (最終 t0+65.001) | × |
| 実験 1 | G30 `setpgid-30` | 4069 | bnode043 | 75 | 5.070 | 69.926 | 70 | t0+75.001 | ○ |
| 実験 2 | S0′ `setsid-now` | 4108 | bnode037 | 35 | 5.038 | −0.456 | 0 | t0+35.001 | ○ |
| 実験 2 | S30′ `setsid-30` | 4133 | bnode028 | 60 | 5.020 | 25.833 | 25 | t0+60.001 | ○ |

**事前登録どおりの最終ベクトル (S0′, G0, S30′, G30) = (0, 70, 25, 70) = A 類。** B 類 (G0 / G30)、C 類 (S0′ / S30′)、D 類 (S30′) は不適合。
実験 1 の不適格走 S0 / S30 の数値 (−0.473 / 24.669) は実験 2 の適格走 (−0.456 / 25.833) と同じ窓にある (事後解析の参考)。
