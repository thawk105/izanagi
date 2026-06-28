# 発見: BACK_OFF=1 + ADD_ANALYSIS=1 が leaderWork で segfault (CCBench 潜在バグ)

- **発見日:** 2026-06-22 (P2 backoff ケーススタディの over-throttling 直接測定を試行中)
- **種別:** CCBench のフラグ組合せ固有の segfault (探索で露呈した潜在バグ)
- **重大度:** 中 (Izanagi の探索には ADD_ANALYSIS 不要で迂回可。ただし backoff の内部計測を塞ぐ)
- **還元判断:** 上流 PR は出さず insight に留める (CLAUDE.md「勝手に上流へ PR を出さない」)。根本原因の
  行特定は ASan ビルドが要る → 人間が判断。WAL XOR (#116) / 両no-wait livelock に続く**フラグ超立方体探索が
  露呈した 3 例目**

## 観測

backoff ケーススタディの [P1]「stock 適応の収束 backoff 量 = over-throttling を外挿でなく実測する」ため、
既存フラグ `ADD_ANALYSIS=1` の出力 `backoff_latency_rate` (= total_backoff_latency / 全スレッドサイクル)
を使おうとしたら、**BACK_OFF=1 + ADD_ANALYSIS=1 のバイナリが segfault** した。

| genome | thread | 結果 |
|---|---|---|
| BACK_OFF=0 + ADD_ANALYSIS=1 (none) | 48 | **完走** (tps 1,872,486, backoff 無し) |
| BACK_OFF=1 + ADD_ANALYSIS=1 (adaptive) | 1 | **SIGSEGV (rc=139)** |
| BACK_OFF=1 + ADD_ANALYSIS=1 (adaptive) | 4 | **SIGSEGV** |
| BACK_OFF=1 + ADD_ANALYSIS=1 (static fix10) | 48 | **SIGSEGV** |
| BACK_OFF=1 (ADD_ANALYSIS=0) — sweep 全 16 | 48 | **完走・全 certified** (ケーススタディ本体) |

- **thread 数非依存** (thread=1 でも crash)。**適応/静的 非依存** (BACKOFF_FIXED=-1 も 10 も crash)。
- **BACK_OFF=1 単体は完走** (ケーススタディの sweep 全点)。**BACK_OFF=0 + ADD_ANALYSIS も完走** (none)。
  → **BACK_OFF=1 × ADD_ANALYSIS=1 の交互作用に固有。**

## 局所化 (gdb backtrace)

```
Thread "ycsb_silo.exe" received signal SIGSEGV
#0  TxExecutor::leaderWork()
#1  YcsbWorkload::run<TxExecutor, TransactionStatus>(TxExecutor&)
#2  ccbench::runner_detail::worker_body<...>(...)
```

`leaderWork()` (`cc/silo/transaction.cc`) は 2 つを呼ぶ:
```cpp
void TxExecutor::leaderWork() {
  siloLeaderWork(epoch_timer_start, epoch_timer_stop);   // epoch 管理
#if BACK_OFF
  leaderBackoffWork(backoff_, CCBenchResults);           // backoff 適応更新
#endif
}
```
- `siloLeaderWork` は BACK_OFF=0 でも毎回呼ばれ、**none (BACK_OFF=0+ADD_ANALYSIS) が完走**している →
  siloLeaderWork × ADD_ANALYSIS は無実。
- 残るは **`#if BACK_OFF` の `leaderBackoffWork(backoff_, CCBenchResults)` × ADD_ANALYSIS** に crash が限局。
  `leaderBackoffWork` (`include/backoff.hh`) は `CCBenchResults` (`std::vector<Result>`, `result.cc:26` で
  `resize(thread_count)`) を走査し `loadAcquire(th.local_commit_counts_)` を読む。`local_commit_counts_` は
  ADD_ANALYSIS 非 gate (result.hh:18) なのでフィールド不在ではない。ADD_ANALYSIS が `Result` に足す
  フィールド (result.hh:24/72/136/199) でレイアウト/初期化順が変わり、leader が CCBenchResults を**未初期化
  /無効状態で**読む競合か、別の ADD_ANALYSIS 計装由来のメモリ破壊が leaderWork で顕在化する、のいずれか。
  **正確な行は Release シンボルだけでは出ず ASan (`-DENABLE_SANITIZER=ON`) ビルドが要る** (本セッションでは未実施)。

## 含意

- **Izanagi の探索には影響なし。** ケーススタディの性能計測は ADD_ANALYSIS=0 (perf build, 規律1) で行い、
  16+3+6 genome 全て完走・certified。ADD_ANALYSIS は backoff 内部の診断にしか使わない任意計装。
- **塞がれたこと:** `backoff_latency_rate` 経由で「stock 適応の backoff スピン占有率」を直接測る道。
  → over-throttling は当面 **ipc/latency vs 固定 100us 点の比較からの外挿のまま** (敵対的検証で「独立に
  頑健」と裁定済み: 適応の ipc 0.43/0.38 < 固定 100us 点の 0.59/0.49 → 適応は 100us より重い域に駐車)。
  直接実測したいなら (a) この segfault を ASan で特定して修正、または (b) `Backoff_` 収束値を結果出力に
  dump する小 patch (ADD_ANALYSIS 非依存) を別途入れる。
- **CCBench 本体としては** ADD_ANALYSIS は分析用の正規フラグなので BACK_OFF と併用できるべき。現状は
  併用で確実に落ちる = 普段 ADD_ANALYSIS + backoff を同時ビルドしていないことの証跡 (フラグ空間の隅)。
