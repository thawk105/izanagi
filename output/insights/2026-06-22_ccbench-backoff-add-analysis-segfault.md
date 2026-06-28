# 発見: BACK_OFF=1 + ADD_ANALYSIS=1 が leaderWork で segfault (CCBench 潜在バグ)

- **発見日:** 2026-06-22 (P2 backoff ケーススタディの over-throttling 直接測定を試行中)
- **種別:** CCBench のフラグ組合せ固有の segfault (探索で露呈した潜在バグ)
- **重大度:** 中 (Izanagi の探索には ADD_ANALYSIS 不要で迂回可。ただし backoff の内部計測を塞ぐ)
- **還元判断:** **本物の CCBench ビルドバグ (Izanagi 非依存) → D16 で master 還元相当。** 修正を fix branch
  `fix/ccbench-common-universal-defines` に用意した (push/PR は人間。WAL XOR #116 と同じ流れ)。WAL XOR /
  両no-wait livelock に続く**フラグ超立方体探索が露呈した 3 例目**
- **状態:** ASan で根本原因を確定し**修正・検証済み** (下記「根本原因 + 修正」)

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
  ADD_ANALYSIS 非 gate (result.hh:18) なのでフィールド不在ではない。残るは ADD_ANALYSIS が `Result` に足す
  フィールド (result.hh:24/72/136/199) による**レイアウト変化** — これを ASan で確定した (下記)。

## 根本原因 (ASan で確定) — ODR 違反 (sizeof(Result) の TU 間不一致)

`-DENABLE_SANITIZER=ON` (gcc-13 Debug) でビルドして thread=1 で再現 → **heap-buffer-overflow**:
```
ERROR: AddressSanitizer: heap-buffer-overflow ... READ of size 8
  #0 loadAcquire<uint64_t>            atomic_wrapper.hh:34
  #1 leaderBackoffWork(...)           include/backoff.hh:124   ← CCBenchResults を range-for で走査
  #2 TxExecutor::leaderWork()         cc/silo/transaction.cc:597
  ...overflowed buffer は↓で確保:
  #7 initResult(...)                  common/result.cc:26      ← CCBenchResults.resize(thread_count)
```

**機構 (ODR 違反):**
- `Result` は `#if ADD_ANALYSIS` でフィールドが増える (result.hh)。`sizeof(Result)` が ADD_ANALYSIS で変わる。
- `CCBenchResults` (`std::vector<Result>`) を確保するのは `common/result.cc` (= **`ccbench_common` 静的ライブラリ**)。
- **`ccbench_common` は universal definitions を一切受けずビルドされていた** (CMake の `ccbench_common.dir`
  の DEFINES が空)。`ccbench_add_protocol` は universal defs を各プロトコル target に PRIVATE 適用するが
  (`ProtocolHelpers.cmake:29,42`)、`ccbench_common` は `set_compile_options` (警告/標準のみ) しか受けない。
- → `ccbench_common` は `Result` を **ADD_ANALYSIS=0 の小レイアウト**で確保 (`resize` の stride 小)。silo
  ターゲットは **ADD_ANALYSIS=1 の大レイアウト**で `leaderBackoffWork` の range-for を回す (stride 大)。
  vector の `end()` は小 stride で設定されているので、大 stride のループが **1 要素分 end を追い越して
  buffer 末尾を越えて読む** (thread=1 でも発生 = サイズ非依存)。これが segfault。
- **なぜ BACK_OFF×ADD_ANALYSIS 固有か:** `leaderBackoffWork` (CCBenchResults を silo 側 stride で走査する
  唯一の箇所) は `#if BACK_OFF` 内。BACK_OFF=0 では呼ばれない (none 完走)。ADD_ANALYSIS=0 では大小 stride が
  一致 (sweep 全点完走)。両方 1 のときだけ stride 不一致 × 走査 が揃う。

## 修正 (検証済み, fix branch 用意)

**2 ファイル:**
1. `CMakeLists.txt`: `ccbench_common` に universal definitions を適用 (`ccbench_universal_definitions()` →
   `target_compile_definitions(ccbench_common PRIVATE ...)`)。これで common も protocol と同じ ADD_ANALYSIS で
   `Result` をビルドし sizeof 一致。`include(Options)` を early に追加 (関数が ccbench_common 定義時に要る)。
2. `common/result.cc`: 上記で初めてコンパイルされる ADD_ANALYSIS 専用 `displayForwardingCount()` の dead 変数
   `num_txns` (使用箇所が全てコメントアウト) を `[[maybe_unused]]` に (-Werror=unused-variable 回避)。

**検証 (gcc-13):** BACK_OFF=1+ADD_ANALYSIS=1 が ASan clean (rc=0)・`backoff_latency_rate` を出力 (thread=8 で
**0.7654** = 適応 backoff がスレッドサイクルの 76.5% をスピンに浪費 = over-throttling の直接実測)。default
(ADD_ANALYSIS=0) と Release -Werror ビルドは無影響 (silo は 48thread で従来どおり完走)。

**還元:** fix branch `fix/ccbench-common-universal-defines` を submodule に用意 (master ベース, +1 commit)。
**push/PR は人間** (この環境に push 認証なし)。D16「本物のバグ修正 → master 還元」に該当。

## 含意

- **Izanagi の探索には影響なし。** ケーススタディの性能計測は ADD_ANALYSIS=0 (perf build, 規律1) で行い、
  16+3+6 genome 全て完走・certified。
- **解消されたこと:** この fix で `backoff_latency_rate` が使えるようになり、over-throttling を ipc/latency からの
  外挿でなく**直接実測**できる (適応が thread-cycle の 76.5% をスピンに費やすことを確認)。ケーススタディの [P1]
  「適応収束値の実測」は fix が master/izanagi-trace に入れば実施可能。
- **CCBench 本体として:** ADD_ANALYSIS は分析用の正規フラグで BACK_OFF と併用できるべき。本バグは `ccbench_common`
  が universal defs を受けないという**ビルドシステムの構造的欠陥**で、ADD_ANALYSIS 以外にも layout/挙動を変える
  universal フラグがあれば同種の不整合を起こしうる (今回の fix はそれらも一括で揃える)。
