## 結論

段 5 は brief どおり 3 実装単位に分けられる。依存は A（patch B）→ B（probe・registry）→ C（図）だが、define 名と JSON schema を先に固定すれば A/B/C の実装自体は並列化できる。

ただし、段 4 へ返すべき重要事項がある。

- `patches/ledger.json` は追記しない。依頼文が consumer として挙げる 3 ファイルは実際にはこの ledger を読まず、真の consumer である `silo_ladder_rung1_contract.py` が entry 数を 1 に固定している。
- 計数窓は leader の試行ごとに全 thread の commit counter を読むため、stock より O(thread数) の追加負荷を持つ。
- P2 の「初回の勾配」と P3 の「上限半減と移動の順序」は未規定なので、本案で具体化した規則を段 4 で裁定する。
- P6 の `3.6 s/run` は「既存 120 run が 8.5 分」という同じ brief の値からは導けない。後者なら 4.25 s/run であり、144 run は約 10.2 分になる。

以下の行番号は現在の pin/A 適用前 repo に対するもの。新規挿入後の deferred sink 行番号だけは実装後に AST から再採番する。

## patch B の実装面

新規 `patches/cicada-adaptive-dynamic.patch` は、pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` に A を当てた木だけを preimage とし、`cmake/Options.cmake` と `include/backoff.hh` の二ファイルだけを変更する。

A の SHA-256 は現 repo でも brief と一致する。

```text
9b2153e0547e167888ba2616750951365c4a075a80f9a95be6000e60b6f8f54b
```

差分案は次のとおり。hunk の old/new count は本文行数と整合させてある。実装時にはこれを手書きのまま採用せず、pin+A の隔離 checkout から `git diff --no-ext-diff` で再生成し、最後に `git apply --check` する。

```diff
diff --git a/cmake/Options.cmake b/cmake/Options.cmake
--- a/cmake/Options.cmake
+++ b/cmake/Options.cmake
@@ -21,9 +21,17 @@ set(CCBENCH_BACK_OFF      1 CACHE STRING "exponential backoff on abort")
 # Cicada's adaptive backoff constants. Defaults reproduce the stock source.
 # INCR_MILLI uses thousandths of a microsecond so sub-microsecond steps remain
 # integer CMake cache values (100000 = 100us).
 set(CCBENCH_BACKOFF_INCR_MILLI 100000 CACHE STRING "adaptive backoff step, thousandths of us (100000=stock)")
 set(CCBENCH_BACKOFF_MAX_US 1000 CACHE STRING "adaptive backoff ceiling in us (1000=stock)")
 set(CCBENCH_BACKOFF_UPDATE_US 10 CACHE STRING "adaptive backoff update interval in us (10=stock)")
+# Dynamic adaptive-backoff controls. Defaults preserve the stock controller.
+set(CCBENCH_BACKOFF_COUNT_WINDOW 0 CACHE STRING "commits per update window (0=time-only stock)")
+set(CCBENCH_BACKOFF_COUNT_CAP_US 0 CACHE STRING "count-window time cap in us (0=BACKOFF_UPDATE_US)")
+set(CCBENCH_BACKOFF_STEP_ADAPT 0 CACHE STRING "adaptive hill-climb step (0=off, 1=on)")
+set(CCBENCH_BACKOFF_STEP_MIN_MILLI 100000 CACHE STRING "minimum adaptive step, thousandths of us")
+set(CCBENCH_BACKOFF_STEP_MAX_MILLI 100000 CACHE STRING "maximum adaptive step, thousandths of us")
+set(CCBENCH_BACKOFF_DYN_CEILING 0 CACHE STRING "dynamic backoff ceiling (0=off, 1=on)")
+set(CCBENCH_BACKOFF_TRACE 0 CACHE STRING "bounded adaptive-backoff diagnostic trace (0=off)")
 set(CCBENCH_KEY_SIZE      8 CACHE STRING "key size in bytes (YCSB)")
 set(CCBENCH_MASSTREE_USE  1 CACHE STRING "use Masstree as the index")
 set(CCBENCH_VAL_SIZE      4 CACHE STRING "value size in bytes (YCSB)")
@@ -67,12 +75,19 @@ function(ccbench_universal_definitions out_var)
   set(${out_var}
     ADD_ANALYSIS=${CCBENCH_ADD_ANALYSIS}
     BACK_OFF=${CCBENCH_BACK_OFF}
+    BACKOFF_COUNT_CAP_US=${CCBENCH_BACKOFF_COUNT_CAP_US}
+    BACKOFF_COUNT_WINDOW=${CCBENCH_BACKOFF_COUNT_WINDOW}
+    BACKOFF_DYN_CEILING=${CCBENCH_BACKOFF_DYN_CEILING}
     BACKOFF_INCR_MILLI=${CCBENCH_BACKOFF_INCR_MILLI}
     BACKOFF_MAX_US=${CCBENCH_BACKOFF_MAX_US}
+    BACKOFF_STEP_ADAPT=${CCBENCH_BACKOFF_STEP_ADAPT}
+    BACKOFF_STEP_MAX_MILLI=${CCBENCH_BACKOFF_STEP_MAX_MILLI}
+    BACKOFF_STEP_MIN_MILLI=${CCBENCH_BACKOFF_STEP_MIN_MILLI}
+    BACKOFF_TRACE=${CCBENCH_BACKOFF_TRACE}
     BACKOFF_UPDATE_US=${CCBENCH_BACKOFF_UPDATE_US}
     KEY_SIZE=${CCBENCH_KEY_SIZE}
     MASSTREE_USE=${CCBENCH_MASSTREE_USE}
     VAL_SIZE=${CCBENCH_VAL_SIZE}
     TRACE=${CCBENCH_TRACE}
     PARENT_SCOPE)
 endfunction()
diff --git a/include/backoff.hh b/include/backoff.hh
--- a/include/backoff.hh
+++ b/include/backoff.hh
@@ -14,14 +14,41 @@
 // CMake supplies stock-equivalent defaults. Missing definitions must stop the
 // build: an absent tuning macro can otherwise silently become zero in an
 // arithmetic expression and turn the adaptive controller into fixed zero.
 #ifndef BACKOFF_INCR_MILLI
 #error "BACKOFF_INCR_MILLI must be defined (100000 = stock 100us step)"
 #endif
 #ifndef BACKOFF_MAX_US
 #error "BACKOFF_MAX_US must be defined (1000 = stock ceiling)"
 #endif
 #ifndef BACKOFF_UPDATE_US
 #error "BACKOFF_UPDATE_US must be defined (10 = stock update interval)"
 #endif
+#ifndef BACKOFF_COUNT_WINDOW
+#error "BACKOFF_COUNT_WINDOW must be defined (0 = stock time-only window)"
+#endif
+#ifndef BACKOFF_COUNT_CAP_US
+#error "BACKOFF_COUNT_CAP_US must be defined (0 = BACKOFF_UPDATE_US)"
+#endif
+#ifndef BACKOFF_STEP_ADAPT
+#error "BACKOFF_STEP_ADAPT must be defined (0 = stock fixed step)"
+#endif
+#ifndef BACKOFF_STEP_MIN_MILLI
+#error "BACKOFF_STEP_MIN_MILLI must be defined (100000 = stock step)"
+#endif
+#ifndef BACKOFF_STEP_MAX_MILLI
+#error "BACKOFF_STEP_MAX_MILLI must be defined (100000 = stock step)"
+#endif
+#ifndef BACKOFF_DYN_CEILING
+#error "BACKOFF_DYN_CEILING must be defined (0 = stock fixed ceiling)"
+#endif
+#ifndef BACKOFF_TRACE
+#error "BACKOFF_TRACE must be defined (0 = no diagnostic instrumentation)"
+#endif
+
+#if BACKOFF_TRACE
+#include <array>
+#include <cstdio>
+#include <cstdlib>
+#endif
 
 using namespace std;
@@ -29,22 +56,82 @@
 class Backoff {
 public:
   static std::atomic<double> Backoff_;
   static constexpr double kMinBackoff = 0;
   static constexpr double kMaxBackoff = static_cast<double>(BACKOFF_MAX_US);
   static constexpr double kIncrBackoff =
       static_cast<double>(BACKOFF_INCR_MILLI) / 1000.0;
   static constexpr size_t kUpdateBackoffUs =
       static_cast<size_t>(BACKOFF_UPDATE_US);
   static_assert(kIncrBackoff > 0, "hill-climb step must be positive");
   static_assert(kMaxBackoff > 0, "backoff ceiling must be positive");
   static_assert(BACKOFF_UPDATE_US > 0 &&
                     kUpdateBackoffUs == BACKOFF_UPDATE_US,
                 "update interval must be a positive whole number of us");
+  static constexpr uint64_t kCountWindow =
+      static_cast<uint64_t>(BACKOFF_COUNT_WINDOW);
+  static constexpr size_t kCountCapUs =
+      static_cast<size_t>(BACKOFF_COUNT_CAP_US);
+  static constexpr double kStepMin =
+      static_cast<double>(BACKOFF_STEP_MIN_MILLI) / 1000.0;
+  static constexpr double kStepMax =
+      static_cast<double>(BACKOFF_STEP_MAX_MILLI) / 1000.0;
+  static_assert(BACKOFF_COUNT_WINDOW >= 0 &&
+                    kCountWindow == BACKOFF_COUNT_WINDOW,
+                "count window must be a nonnegative whole number");
+  static_assert(BACKOFF_COUNT_CAP_US >= 0 &&
+                    kCountCapUs == BACKOFF_COUNT_CAP_US,
+                "count cap must be a nonnegative whole number of us");
+  static_assert(BACKOFF_STEP_ADAPT == 0 || BACKOFF_STEP_ADAPT == 1,
+                "step adaptation must be 0 or 1");
+  static_assert(kStepMin > 0 && kStepMax >= kStepMin,
+                "adaptive step bounds must be positive and ordered");
+  static_assert(!BACKOFF_STEP_ADAPT ||
+                    (kIncrBackoff >= kStepMin &&
+                     kIncrBackoff <= kStepMax),
+                "initial step must lie within adaptive step bounds");
+  static_assert(BACKOFF_DYN_CEILING == 0 || BACKOFF_DYN_CEILING == 1,
+                "dynamic ceiling must be 0 or 1");
+  static_assert(!BACKOFF_DYN_CEILING ||
+                    (BACKOFF_STEP_ADAPT ? kStepMax : kIncrBackoff) * 4 <=
+                        kMaxBackoff,
+                "dynamic ceiling needs room for four maximum steps");
+  static_assert(BACKOFF_TRACE == 0 || BACKOFF_TRACE == 1,
+                "backoff trace must be 0 or 1");
 
   uint64_t last_committed_txs_ = 0;
   double last_committed_tput_ = 0;
   uint64_t last_backoff_ = 0;
   uint64_t last_time_ = 0;
   size_t clocks_per_us_;
+#if BACKOFF_STEP_ADAPT
+  double adaptive_step_ = kIncrBackoff;
+  int last_gradient_sign_ = 0;
+  bool has_last_gradient_sign_ = false;
+#endif
+#if BACKOFF_DYN_CEILING
+  double ceiling_ = kMaxBackoff;
+#endif
+#if BACKOFF_TRACE
+  struct izanagi_backoff_trace_record {
+    uint64_t seq;
+    uint64_t tsc;
+    double backoff_us;
+    int gradient_sign;
+    int next_window_hit;
+  };
+  static constexpr size_t izanagi_backoff_trace_capacity = 65536;
+  inline static std::array<izanagi_backoff_trace_record, izanagi_backoff_trace_capacity> izanagi_backoff_trace_ring_{};
+  inline static size_t izanagi_backoff_trace_write_ = 0;
+  inline static size_t izanagi_backoff_trace_retained_ = 0;
+  inline static uint64_t izanagi_backoff_trace_total_ = 0;
+  inline static uint64_t izanagi_backoff_trace_dropped_ = 0;
+  inline static uint64_t izanagi_backoff_trace_scored_ = 0;
+  inline static uint64_t izanagi_backoff_trace_hits_ = 0;
+  inline static bool izanagi_backoff_trace_registered_ = false;
+#endif
+#if BACKOFF_STEP_ADAPT || BACKOFF_DYN_CEILING || BACKOFF_TRACE
+  static int izanagi_backoff_gradient_sign(double gradient) {
+    return (gradient > 0) - (gradient < 0);
+  }
+#endif
 
   Backoff(size_t clocks_per_us) { init(clocks_per_us); }
@@ -57,6 +144,20 @@
   bool check_update_backoff() {
+#if BACKOFF_COUNT_WINDOW > 0
+  bool check_update_backoff(const uint64_t committed_txs) {
+    if (committed_txs - last_committed_txs_ >= kCountWindow)
+      return true;
+    const size_t cap_us =
+        kCountCapUs == 0 ? kUpdateBackoffUs : kCountCapUs;
+    if (chkClkSpan(last_time_, rdtscp(), clocks_per_us_ * cap_us))
+      return true;
+    else
+      return false;
+  }
+#else
+  bool check_update_backoff() {
     if (chkClkSpan(last_time_, rdtscp(), clocks_per_us_ * kUpdateBackoffUs))
       return true;
     else
       return false;
   }
+#endif
@@ -64,51 +165,164 @@
-  void update_backoff(const uint64_t committed_txs) {
-    uint64_t now = rdtscp();
-    uint64_t time_diff = now - last_time_;
-    last_time_ = now;
-
-    double new_backoff = Backoff_.load(std::memory_order_acquire);
-    double backoff_diff = new_backoff - last_backoff_;
-
-    uint64_t committed_diff = committed_txs - last_committed_txs_;
-    double committed_tput = static_cast<double>(committed_diff) /
-                            (static_cast<double>(time_diff) / clocks_per_us_) *
-                            pow(10.0, 6);
-    double committed_tput_diff = committed_tput - last_committed_tput_;
-
-    last_committed_txs_ = committed_txs;
-    last_committed_tput_ = committed_tput;
-    last_backoff_ = new_backoff;
-    /*
-    cout << "=====" << endl;
-    cout << "committed_tput_diff:\t" <<
-    static_cast<int64_t>(committed_tput_diff) << endl; cout <<
-    "last_backoff_:\t" << last_backoff_ << endl; cout << "backoff_diff:\t" <<
-    backoff_diff << endl;
-    */
-
-    double gradient;
-    if (backoff_diff != 0)
-      gradient = committed_tput_diff / backoff_diff;
-    else
-      gradient = 0;
-
-    if (gradient < 0)
-      new_backoff -= kIncrBackoff;
-    else if (gradient > 0)
-      new_backoff += kIncrBackoff;
-    else {
-      if ((committed_txs & 1) == 0 ||
-          new_backoff == kMaxBackoff) // 確率はおよそ 1/2, すなわちランダム．
-        new_backoff -= kIncrBackoff;
-      else if ((committed_txs & 1) == 1 || new_backoff == kMinBackoff)
-        new_backoff += kIncrBackoff;
-    }
-
-    if (new_backoff < kMinBackoff)
-      new_backoff = kMinBackoff;
-    else if (new_backoff > kMaxBackoff)
-      new_backoff = kMaxBackoff;
-    Backoff_.store(new_backoff, std::memory_order_release);
-  }
-
-  static void backoff(size_t clocks_per_us) {
+  void update_backoff(const uint64_t committed_txs) {
+    uint64_t now = rdtscp();
+    uint64_t time_diff = now - last_time_;
+    last_time_ = now;
+
+    double new_backoff = Backoff_.load(std::memory_order_acquire);
+    double backoff_diff = new_backoff - last_backoff_;
+
+    uint64_t committed_diff = committed_txs - last_committed_txs_;
+    double committed_tput = static_cast<double>(committed_diff) /
+                            (static_cast<double>(time_diff) / clocks_per_us_) *
+                            pow(10.0, 6);
+    double committed_tput_diff = committed_tput - last_committed_tput_;
+
+    last_committed_txs_ = committed_txs;
+    last_committed_tput_ = committed_tput;
+    last_backoff_ = new_backoff;
+    /*
+    cout << "=====" << endl;
+    cout << "committed_tput_diff:\t" <<
+    static_cast<int64_t>(committed_tput_diff) << endl; cout <<
+    "last_backoff_:\t" << last_backoff_ << endl; cout << "backoff_diff:\t" <<
+    backoff_diff << endl;
+    */
+
+    double gradient;
+    if (backoff_diff != 0)
+      gradient = committed_tput_diff / backoff_diff;
+    else
+      gradient = 0;
+
+#if BACKOFF_STEP_ADAPT || BACKOFF_DYN_CEILING || BACKOFF_TRACE
+    const int gradient_sign = izanagi_backoff_gradient_sign(gradient);
+#endif
+#if BACKOFF_STEP_ADAPT || BACKOFF_DYN_CEILING
+    double step = kIncrBackoff;
+#endif
+#if BACKOFF_STEP_ADAPT
+    if (has_last_gradient_sign_) {
+      if (gradient_sign != 0 && gradient_sign == last_gradient_sign_)
+        adaptive_step_ = adaptive_step_ * 2 > kStepMax
+                             ? kStepMax : adaptive_step_ * 2;
+      else
+        adaptive_step_ = adaptive_step_ / 2 < kStepMin
+                             ? kStepMin : adaptive_step_ / 2;
+    }
+    last_gradient_sign_ = gradient_sign;
+    has_last_gradient_sign_ = true;
+    step = adaptive_step_;
+#endif
+#if BACKOFF_DYN_CEILING
+    if (new_backoff == ceiling_) {
+      if (gradient_sign < 0) {
+        const double floor = step * 4;
+        ceiling_ = ceiling_ / 2 < floor ? floor : ceiling_ / 2;
+      } else if (gradient_sign > 0) {
+        ceiling_ = ceiling_ * 2 > kMaxBackoff
+                       ? kMaxBackoff : ceiling_ * 2;
+      }
+    }
+#endif
+
+    if (gradient < 0)
+#if BACKOFF_STEP_ADAPT
+      new_backoff -= step;
+#else
+      new_backoff -= kIncrBackoff;
+#endif
+    else if (gradient > 0)
+#if BACKOFF_STEP_ADAPT
+      new_backoff += step;
+#else
+      new_backoff += kIncrBackoff;
+#endif
+    else {
+      if ((committed_txs & 1) == 0 ||
+#if BACKOFF_DYN_CEILING
+          new_backoff == ceiling_)
+#else
+          new_backoff == kMaxBackoff)
+#endif
+#if BACKOFF_STEP_ADAPT
+        new_backoff -= step;
+#else
+        new_backoff -= kIncrBackoff;
+#endif
+      else if ((committed_txs & 1) == 1 || new_backoff == kMinBackoff)
+#if BACKOFF_STEP_ADAPT
+        new_backoff += step;
+#else
+        new_backoff += kIncrBackoff;
+#endif
+    }
+
+    if (new_backoff < kMinBackoff)
+      new_backoff = kMinBackoff;
+#if BACKOFF_DYN_CEILING
+    else if (new_backoff > ceiling_)
+      new_backoff = ceiling_;
+#else
+    else if (new_backoff > kMaxBackoff)
+      new_backoff = kMaxBackoff;
+#endif
+    Backoff_.store(new_backoff, std::memory_order_release);
+#if BACKOFF_TRACE
+    izanagi_backoff_trace_record_update(now, new_backoff, gradient_sign);
+#endif
+  }
+
+#if BACKOFF_TRACE
+  static void izanagi_backoff_trace_flush() {
+    const size_t first =
+        izanagi_backoff_trace_retained_ == izanagi_backoff_trace_capacity
+            ? izanagi_backoff_trace_write_ : 0;
+    for (size_t offset = 0; offset < izanagi_backoff_trace_retained_; ++offset) {
+      const auto& record = izanagi_backoff_trace_ring_[
+          (first + offset) % izanagi_backoff_trace_capacity];
+      std::printf(
+          "IZANAGI_BACKOFF_TRACE v=1 seq=%llu tsc=%llu backoff_us=%.3f "
+          "gradient_sign=%d next_window_hit=%d\n",
+          static_cast<unsigned long long>(record.seq),
+          static_cast<unsigned long long>(record.tsc), record.backoff_us,
+          record.gradient_sign, record.next_window_hit);
+    }
+    std::printf(
+        "IZANAGI_BACKOFF_TRACE_SUMMARY v=1 updates=%llu retained=%zu "
+        "dropped=%llu scored=%llu hits=%llu\n",
+        static_cast<unsigned long long>(izanagi_backoff_trace_total_),
+        izanagi_backoff_trace_retained_,
+        static_cast<unsigned long long>(izanagi_backoff_trace_dropped_),
+        static_cast<unsigned long long>(izanagi_backoff_trace_scored_),
+        static_cast<unsigned long long>(izanagi_backoff_trace_hits_));
+  }
+
+  static void izanagi_backoff_trace_record_update(
+      uint64_t tsc, double backoff_us, int gradient_sign) {
+    if (!izanagi_backoff_trace_registered_) {
+      if (std::atexit(izanagi_backoff_trace_flush) != 0) std::abort();
+      izanagi_backoff_trace_registered_ = true;
+    }
+    if (izanagi_backoff_trace_retained_ != 0) {
+      const size_t previous =
+          (izanagi_backoff_trace_write_ + izanagi_backoff_trace_capacity - 1) %
+          izanagi_backoff_trace_capacity;
+      auto& record = izanagi_backoff_trace_ring_[previous];
+      record.next_window_hit =
+          gradient_sign != 0 && gradient_sign == record.gradient_sign ? 1 : 0;
+      ++izanagi_backoff_trace_scored_;
+      izanagi_backoff_trace_hits_ +=
+          static_cast<uint64_t>(record.next_window_hit);
+    }
+    izanagi_backoff_trace_ring_[izanagi_backoff_trace_write_] = {
+        izanagi_backoff_trace_total_, tsc, backoff_us, gradient_sign, -1};
+    izanagi_backoff_trace_write_ =
+        (izanagi_backoff_trace_write_ + 1) % izanagi_backoff_trace_capacity;
+    ++izanagi_backoff_trace_total_;
+    if (izanagi_backoff_trace_retained_ < izanagi_backoff_trace_capacity)
+      ++izanagi_backoff_trace_retained_;
+    else
+      ++izanagi_backoff_trace_dropped_;
+  }
+#endif
+
+  static void backoff(size_t clocks_per_us) {
@@ -131,11 +345,20 @@
 [[maybe_unused]] inline void
 leaderBackoffWork([[maybe_unused]] Backoff& backoff,
                   [[maybe_unused]] std::vector<Result>& res) {
+#if BACKOFF_COUNT_WINDOW > 0
+  uint64_t sum_committed_txs(0);
+  for (auto& th : res) {
+    sum_committed_txs += loadAcquire(th.local_commit_counts_);
+  }
+  if (backoff.check_update_backoff(sum_committed_txs))
+    backoff.update_backoff(sum_committed_txs);
+#else
   if (backoff.check_update_backoff()) {
     uint64_t sum_committed_txs(0);
     for (auto& th : res) {
       sum_committed_txs += loadAcquire(th.local_commit_counts_);
     }
     backoff.update_backoff(sum_committed_txs);
   }
+#endif
 }
```

なお上の第 3 hunk は表示上、旧 `bool check_update_backoff()` 行を context に残さず置換する必要がある。実 patch 生成時は、pin+A の実ファイルを編集して `git diff` に生成させること。これにより、前 wave の malformed header 再発を避ける。

## patch B の意味論

**計数窓。** [backoff.hh:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/external/ccbench/include/backoff.hh:37) と [leaderBackoffWork:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/external/ccbench/include/backoff.hh:111) を上記の二枝にする。

- `BACKOFF_COUNT_WINDOW=0` は既存の時刻判定→条件成立時だけ commit 集計、という制御流を逐語で残す。
- `>0` は leader の試行先頭で commit 集計し、`committed-last >= K` または時間 cap 到達で更新する。
- `BACKOFF_COUNT_CAP_US=0` は `BACKOFF_UPDATE_US` を cap に使う。
- K 到達時刻そのものではなく、次の leader 試行で遅延検知される。

**適応刻み。**

- 初回の勾配では `kIncrBackoff` をそのまま使う。
- 2 回目以降、非ゼロ符号が前回と一致すれば、その更新に使う刻みを `min(step×2,max)` にする。
- 反転または `gradient==0` は `max(step÷2,min)`。
- `STEP_ADAPT=0` の枝には既存の `kIncrBackoff` 文をそのまま置く。
- `last_backoff_` は stock の `uint64_t` のままにし、0.25/0.5 µs で生じる切り捨て挙動を勝手に修正しない。

**動的上限。**

- `ceiling_` は `kMaxBackoff` から開始する。
- 更新前の `Backoff_ == ceiling_` かつ負勾配なら ceiling を半減する。ただし下限はその更新で使う刻みの 4 倍。
- 同条件で正勾配なら ceiling を倍増し、`kMaxBackoff` で止める。
- ceiling 更新後に hill-climb の一歩を計算し、最後に新 ceiling へ clamp する。
- `DYN_CEILING=0` は既存 `kMaxBackoff` clamp を逐語で残す。

**診断。** `BACKOFF_TRACE` は `CCBENCH_TRACE` とは完全に別の macro とする。

- 固定長 65,536 件、約 2 MiB の process-global ring を使う。書き手は D1576 が固定する leader だけなので lock を追加しない。
- hot path は構造体代入だけ。`printf` は `atexit` に登録した flush で run 終了時にまとめて行う。
- `gradient_sign(t)` の的中は、次回の非ゼロ符号が同じ場合を 1、それ以外を 0 とする。最後の record は未評価なので `-1`。
- overflow は `dropped` に残す。probe の正式な診断結果は `dropped==0` を要求し、容量不足を黙って要約しない。
- 診断関連の関数・静的変数名はすべて `izanagi_backoff_trace` 接頭辞で、定義自体を `#if BACKOFF_TRACE` 内に置く。

stdout 契約は次の二形式だけを追加する。

```text
IZANAGI_BACKOFF_TRACE v=1 seq=<u64> tsc=<u64> backoff_us=<decimal> gradient_sign=<-1|0|1> next_window_hit=<-1|0|1>
IZANAGI_BACKOFF_TRACE_SUMMARY v=1 updates=<u64> retained=<u64> dropped=<u64> scored=<u64> hits=<u64>
```

通常 performance build では次を要求する。

```bash
nm -C ycsb_silo.exe | grep -F izanagi_backoff_trace
# rc=1、出力 0 行
```

既存 [buildcache.py:3448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/buildcache.py:3448) の checker は `izanagi_trace` だけを見るため、この新 prefix は probe/test 側で明示検査する。

## patch 適用と後始末

[patchharness.py:246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/patchharness.py:246) の `applied()` は enter 時に pinned-clean を要求するため、`applied(A)` と `applied(B)` を nest してはいけない。

[probe.py:41-53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:41) で次を行う。

```python
from orchestrator.campaign.patchharness import (
    applied,
    apply_patch,
    assert_pinned_clean,
    patch_files,
)

PATCH_A = ROOT / "patches" / "cicada-adaptive-params.patch"
PATCH_B = ROOT / "patches" / "cicada-adaptive-dynamic.patch"

with isolated_checkout(submodule, CURRENT_PIN) as work_root:
    with applied(str(PATCH_A), CURRENT_PIN, work_root) as a_files:
        b_files = patch_files(str(PATCH_B), work_root)
        if set(b_files) != set(a_files):
            raise RuntimeError("patch B must touch exactly the two A-owned files")
        for relative in b_files:
            subprocess.run(
                ["git", "-C", work_root, "cat-file", "-e", f"HEAD:{relative}"],
                check=True,
            )
        apply_patch(str(PATCH_B), work_root)
        # resolve evidence -> build -> run
```

明示的な二度目の `revert_worktree()` は不要である。[revert_worktree:214-240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/patchharness.py:214) は `files` だけでなく `git checkout -- .` により全 tracked change を戻す。B の path 集合を A と同一かつ HEAD に存在する二ファイルへ固定すれば、外側 `applied(A)` の exit が A+B を同時に戻す。その後 [isolated_checkout:316-342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:316) の最終 pinned-clean 検査を通す。

patch identity は単一 `patch_sha256` に A の hash だけを入れ続けてはいけない。各 JSON に次を追加する。

```json
{
  "patch_stack": [
    {"path": "patches/cicada-adaptive-params.patch", "sha256": "..."},
    {"path": "patches/cicada-adaptive-dynamic.patch", "sha256": "..."}
  ],
  "patch_stack_sha256": "<canonical JSON bytes of the ordered list>"
}
```

旧 `patch_sha256` を残す場合は A+B の順序付き stack digest に意味を変更し、certification row/group の比較も同じ値へ移す。

## cell 書式と Cell dataclass

[probe.py:137-156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:137) の `Cell` に次を追加する。

```python
count_window: int = 0
count_cap_us: int = 0
step_adapt: int = 0
step_min_us: float = 100.0
step_max_us: float = 100.0
dyn_ceiling: int = 0
extended: bool = False
```

`BACKOFF_TRACE` は arm の意味ではなく run mode なので cell text には入れない。`genome_for(cell, *, backoff_trace=False)` の引数で供給する。

受理書式は 5 field または 11 field だけとする。

```text
label:back_off:step_us:ceiling_us:update_us
label:back_off:step_us:ceiling_us:update_us:count_window:count_cap_us:step_adapt:step_min_us:step_max_us:dyn_ceiling
```

field 内の区切りは既存と同じ `:` だけであり、新 field のために `,`、`;`、`+` は使わない。`,` は Python CLI 内の cell list、`+` は PBS 境界の list transport に限る。

[parse_cells:203-233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:203) で次を固定する。

- 5 field は新値を stock default で埋め、`extended=False`。
- 11 field は `extended=True`。
- count 二値は非負整数、on/off は exact `0|1`。
- step min/max は 1/1000 µs で正確に表現できる正数。
- `step_min <= step_max`。
- `STEP_ADAPT=1` なら `step_min <= step_us <= step_max`。
- `COUNT_WINDOW=0` なら `COUNT_CAP_US=0`。
- `DYN_CEILING=1` なら最大刻み×4が固定上限以下。
- 5/11 以外、空 field、余剰 field、unsafe label を拒否する。

P9 の正式な 6 cell は次に固定する。

```text
none:0:100:1000:10
stock:1:100:1000:10
tuned:1:1:1000:2560
cw:1:1:1000:2560:10000:40960:0:100:100:0
cw-as:1:1:1000:2560:10000:40960:1:0.25:8:0
cw-as-dyn:1:1:1000:2560:10000:40960:1:0.25:8:1
```

ここでは P9 に書かれていない `cw` の `update_us` を tuned 継承の 2560、適応 off 時の min/max を stock default の 100/100 と仮置きした。段 4 裁定対象である。

## genome と grid contract

[genome_for:344-354](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:344) は次の互換形にする。

```python
def genome_for(cell: Cell, *, backoff_trace: bool = False) -> Genome:
    flags = {
        **BASE,
        "BACK_OFF": cell.back_off,
        "BACKOFF_INCR_MILLI": cell.incr_milli,
        "BACKOFF_MAX_US": cell.ceiling_us,
        "BACKOFF_UPDATE_US": cell.update_us,
    }
    if cell.extended or backoff_trace:
        flags.update(
            BACKOFF_COUNT_WINDOW=cell.count_window,
            BACKOFF_COUNT_CAP_US=cell.count_cap_us,
            BACKOFF_STEP_ADAPT=cell.step_adapt,
            BACKOFF_STEP_MIN_MILLI=cell.step_min_milli,
            BACKOFF_STEP_MAX_MILLI=cell.step_max_milli,
            BACKOFF_DYN_CEILING=cell.dyn_ceiling,
            BACKOFF_TRACE=int(backoff_trace),
        )
    return Genome("silo", flags)
```

これにより、既存 5-field cell の `Genome.canonical()` と `cmake_defines()` は拡張前と byte-identical のままになる。B 側の CMake default が新 macro を供給するので `#error` にも抵触しない。拡張 cell と診断 build では新 7 define を全件明示する。

[_validate_grid_contract:239-254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:239) は維持しつつ、configuration key を次へ拡張する。

```python
(
    back_off,
    incr_milli,
    ceiling_us,
    update_us,
    count_window,
    count_cap_us,
    step_adapt,
    step_min_milli,
    step_max_milli,
    dyn_ceiling,
)
```

不変条件は次のまま。

- disabled は `none:0:100:1000:10` ちょうど 1。
- stock control は既定 3 定数かつ新機構すべて default のものがちょうど 1。
- label 重複なし。
- effective build configuration 重複なし。
- 6 cell の全通常 build は A+B tree、`BACKOFF_TRACE=0`、`CCBENCH_TRACE=0`。

## performance と診断 mode

[argument parser:1593-1640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:1593) に `--backoff-trace` を `store_true` で追加する。`--mode certify` との同時指定は拒否する。

通常 performance path [main:2037-2221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:2037) は既存 `measure_point()` を維持する。各 `cells[]` row に次を追加する。

```text
count_window
count_cap_us
step_adapt
step_min_us
step_max_us
dyn_ceiling
backoff_trace=false
cell_format_fields=5|11
backoff_trace_symbol_count=0
```

診断 path は exact に次を要求する。

- cells = `cw`、`cw-as`、`cw-as-dyn` の順序付き 3 cell。
- workloads = `write-heavy,balanced,read-heavy`。
- threads = `24,48`。
- reps-per-job = 1、extime = 3。
- `genome_for(cell, backoff_trace=True)`。
- `buildcache.build(..., trace=False)`、すなわち correctness trace は off のまま。

raw stdout を得るために `runner.py` は変更しない。`measure_point()` の既存 `subprocess_runner` seam [runner.py:1057-1162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/calibrator/runner.py:1057) へ、`subprocess.run()` を呼んで `CompletedProcess.stdout` を保存する wrapper を渡す。`require_all_reps=True` とし、既存 argv・cwd・DB 構築・timeout・metric parser を再利用する。

診断 JSON は別 schema にする。

```text
izanagi-dynamic-backoff-trace/v1
kind = diagnostic-backoff-trace
headline_eligible = false
```

`trace_runs[]` は cell/workload/thread/genome/binary SHA、trace event 全件、summary、throughput/abort を持つ。ただし throughput は明示的に diagnostic-only とし、性能図へ混ぜない。

parser は次を fail-closed に検査する。

- record line と summary line が exact regex に一致。
- seq が 0 から連続。
- TSC が単調増加。
- `gradient_sign ∈ {-1,0,1}`。
- 最終 record だけ `next_window_hit=-1`、それ以前は `0|1`。
- `updates == retained == len(events)`、`dropped==0`。
- `scored == max(updates-1,0)`。
- `hits` が event 再計算値と一致。
- `0 <= hits <= scored`。
- `nm -C` に `izanagi_backoff_trace` symbol が 1 件以上ある。

## PBS の変更

[PBS:43-120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:43) に次を追加する。

```bash
BACKOFF_TRACE=${IZANAGI_T2187_BACKOFF_TRACE:-0}
if [[ "$BACKOFF_TRACE" != 0 && "$BACKOFF_TRACE" != 1 ]]; then
  echo "IZANAGI_T2187_BACKOFF_TRACE must be 0 or 1" >&2
  exit 2
fi
```

trace のときは `CELLS_RAW`、workloads、threads を上記 exact 値へ束縛し、`BACKOFF_TRACE_ARGS=(--backoff-trace)` とする。通常 performance branch [PBS:277-286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:277) へ配列を展開する。

qsub 例は次になる。

```bash
qsub -v 'IZANAGI_T2187_BACKOFF_TRACE=1,IZANAGI_T2187_CELLS=cw:1:1:1000:2560:10000:40960:0:100:100:0+cw-as:1:1:1000:2560:10000:40960:1:0.25:8:0+cw-as-dyn:1:1:1000:2560:10000:40960:1:0.25:8:1,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48' \
  tools/pegasus/probes/t2187_adaptive_const_probe.pbs
```

既存の plus→comma 変換 [PBS:118-120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:118) は維持する。

## certification の exact 2 値化

[probe.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:156) を次へ分ける。

```python
CERT_TUNED_CELL = Cell("tuned", 1, 1.0, 1_000, 2_560)
CERT_DYNAMIC_CELL = Cell(
    "cw-as-dyn", 1, 1.0, 1_000, 2_560,
    count_window=10_000,
    count_cap_us=40_960,
    step_adapt=1,
    step_min_us=0.25,
    step_max_us=8.0,
    dyn_ceiling=1,
    extended=True,
)
CERT_CELLS = (CERT_TUNED_CELL, CERT_DYNAMIC_CELL)
```

[_certification_contract:395-488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:395) は「入力が 1 cell ちょうど、かつその値が `CERT_CELLS` のどちらか」とする。二つを同時に渡すことは拒否する。

次の全箇所を同時に変える。

- [個別 payload:1688-1718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:1688): 新 6 field、ordered patch stack、cell-specific allowed claim を保存。
- [row validation:1095-1195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:1095): 文書の全 field から exact `Cell` を再構成し、二値集合へ照合する。
- [group aggregation:1303-1421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:1303): 24 row の cell identity、genome SHA、source SHA、patch stack SHA が各 1 値であることを要求する。
- [published group validation:1424-1487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:1424): group の cell identity と claim も再照合する。
- [PBS:88-117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:88): `CELLS_RAW` が legacy tuned または extended dynamic のどちらか exact であることを要求する。

既存文字列 `tuned:1:1:1000:2560` は変更せず、そのまま受理する。5-field parse と legacy genome も byte-identical なので既存呼出しは同じ挙動になる。

認証の連言 10 項は [T-2189 insight:68-100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/output/insights/2026-09-04_t2189-adaptive-serializability-certification.md:68) のまま変更しない。

- trace-enabled cache identity
- run rc=0
- run 前の空 trace directory
- exact target trace path
- verifier exit=0、非 lenient、exact proof surface
- commit witness と batch=0
- txn/read/write/edge/abort の非空振り
- integrity.clean
- 同一 job の陽性対照
- verifier closure identity

24 request は workload 3 × slot 8 のまま。陽性対照、performance artifact SHA、verifier manifest SHA、source/genome identity、全 result path の explicit binding も緩めない。

## 登録簿の追随

[condition_meaning_gate.py:71-103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/condition_meaning_gate.py:71) の `_DEFINE_SPECS` に次を追加する。`owner_tus` と target は A の 3 define と同じでよい。

| macro | patch_rel | inert_values |
|---|---|---|
| `BACKOFF_COUNT_WINDOW` | `patches/cicada-adaptive-dynamic.patch` | `("0",)` |
| `BACKOFF_COUNT_CAP_US` | 同上 | `("0",)` |
| `BACKOFF_STEP_ADAPT` | 同上 | `("0",)` |
| `BACKOFF_STEP_MIN_MILLI` | 同上 | `("100000",)` |
| `BACKOFF_STEP_MAX_MILLI` | 同上 | `("100000",)` |
| `BACKOFF_DYN_CEILING` | 同上 | `("0",)` |
| `BACKOFF_TRACE` | 同上 | `("0",)` |

`patch_rel` は [_patch_changed_paths:2082-2099](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/condition_meaning_gate.py:2082) が `diff --git` path 集合を得る用途だけなので、B が A 後の差分であることとは衝突しない。

[screening_driver.py:49-75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/screening_driver.py:49) の `_CONDITION_DEFAULTS` に同じ default 値を追加する。

[test_condition_meaning_gate.py:2392-2433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_condition_meaning_gate.py:2392) は supply domain に 7 macro を追加し、CMake route 件数を 12→19、新 macro の `patch_rel` と `inert_values` を exact に検査する。

[test_ccbench_spawn_sites.py:907-929](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_ccbench_spawn_sites.py:907) と同テストの golden [2671-2678](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_ccbench_spawn_sites.py:2671) は、probe 編集後に AST が返す二つの実行番号へ更新する。推測で加算せず、最終 source の `ast.Call.lineno` を採る。理由文も「tuned only/A only」から「exact two cells/A+B stack」へ更新する。

[hooks admission golden:3445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_hooks.py:3445) は変更しない。probe と PBS の path は不変で、登録済み class も既に `dispatch-required` だからである。

## patches/ledger.json の結論

`patches/ledger.json` には entry を足さない。

依頼文に挙げられた consumer の実態は次のとおり。

- `tools/mutation_fanout.py:601` の `ledger.json` は各 shard の runtime ledger であり、`patches/ledger.json` を読まない。
- `tools/check_branch_rescue.py:29-97` の ledger は `izanagi-unreachable-object-ledger-v1` であり、patch ledger ではない。
- `orchestrator/campaign/s1_direct_comparison.py:54-55,937-991` の ledger は S-1 budget/session ledger であり、patch ledger ではない。

実際に patch ledger を読む一般 consumer は [projection_guard.py:168-230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/projection_guard.py:168) である。これは `ability_probe=false` entry 自体は受理できる。

しかし既存 rung1 の真の contract は [silo_ladder_rung1_contract.py:495-535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/silo_ladder_rung1_contract.py:495) で、

```text
len(entries) == 1
全 entry が ability-probe 用 closed schema
```

を exact に要求する。さらに [silo_ladder_rung1.py:3971-3997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/silo_ladder_rung1.py:3971) の実 correctness path がこの contract を毎回通す。

したがって D18 第3類の合成 variant entry を追加すると、classification を正直に書いても既存 consumer が壊れる。P7 の条件を満たさないため no-entry が唯一の整合的結論である。登録は `patches/README.md` と `DefineSpec` に限定する。

## README の追随

[patches/README.md:6-21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/patches/README.md:6) の分類表は変更不要で、B は「合成 variant」に該当する。その後の backoff 節付近へ次を追加する。

- B は D18 第3類の合成 variant。
- preimage は pin+A。
- 7 define と stock defaults。
- count window、adaptive step、dynamic ceiling の意味。
- `BACKOFF_TRACE` は D14 の `#if` 診断計器で性能 build から完全除去。
- driver は既存 T-2187 probe。
- `patches/ledger.json` 非登録の理由は rung1 exact-one contract。

`tools/plotting/README.md:157-185` に新 generator の入力 7+1、出力名、未認証性能値、診断 throughput 非 headline を追記する。これは親 docs lane が担当し、段 5 の実装単位には数えない。

## 図生成器

新規 `tools/plotting/plot_dynamic_backoff.py` は [plot_t2187_adaptive_consts.py:39-46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_t2187_adaptive_consts.py:39) の schema 定数、[strict JSON:61-94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_t2187_adaptive_consts.py:61)、[Student-t CI:129-222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_t2187_adaptive_consts.py:129)、[layout check:896-940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_t2187_adaptive_consts.py:896)、[atomic save/provenance:942-1034](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_t2187_adaptive_consts.py:942) の構造に合わせる。

CLI は次に固定する。

```text
python3 tools/plotting/plot_dynamic_backoff.py \
  OUT_PREFIX \
  --trace-json DIAGNOSTIC.json \
  PERF_REP0.json ... PERF_REP6.json
```

入力 contract は exact に、

- performance JSON 7 file、rep index `0..6`
- 各 file は 6 cell × 3 workload × 8 thread = 144 row
- thread 軸は `{6,12,18,24,30,36,42,48}`
- 診断 JSON 1 file
- 診断は dynamic 3 cell × 3 workload × `{24,48}` = 18 run
- pin、env、records、extime、ordered patch stack が全入力で一致

とする。

出力は次の 5 file とする。

```text
OUT_PREFIX-thread-axis.png
OUT_PREFIX-thread-axis.pdf
OUT_PREFIX-diagnostic.png
OUT_PREFIX-diagnostic.pdf
OUT_PREFIX.provenance.json
```

**thread-axis 図。** 2 行×3 列。

- 上段 throughput、下段 abort rate。
- 列は write-heavy / balanced / read-heavy。
- 6 系列は none / stock / tuned / cw / cw-as / cw-as-dyn。
- none と tuned を D1506 の基準線として太さ・破線を区別する。
- stock は陽性対照として描くが、機構比較の基準線とは呼ばない。
- 各点は 7 node の生値平均、誤差棒は `t_(0.975,6)·s/√7`。

**診断図。** 同じく 2 行×3 列。

- 上段は `(tsc-first_tsc)/clocks_per_us` を秒へ変換した横軸と `Backoff_` の軌跡。dynamic 3 arm × thread 2 値を重ねる。
- 下段は arm ごとの `hits/scored`。24/48 thread を別 marker にする。
- n=1 の診断には CI を付けず、caption に明記する。
- diagnostic build の throughput は描かない。

provenance は全 8 input の absolute path/SHA、generator SHA、全 output SHA、PBS job id、patch stack、測定条件、performance 集約値、trace summary、図へ描いた trajectory/hit rate、再現 argvを保存する。

FIGURE_CONVENTIONS §9 に従い、保存先へ公開する前に本物の Figure の bbox を検査する。

## テスト計画

実装後は直接 `pytest` ではなく `tools/run_tests.py` を通す。今回の read-only plan 段では走らせない。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_five_field_cells_preserve_legacy_cell_and_genome_bytes`  
  5-field parse、`Cell` defaults、拡張前と同一の `Genome.canonical()` / CMake define list を固定する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_extended_cells_parse_all_dynamic_fields`  
  11-field の三動的腕と milliunit 正規化を固定する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_extended_cells_reject_invalid_shape_and_inert_or_impossible_combinations`  
  6〜10/12 field、非整数 K/cap、非法 toggle、lossy step、逆転 bounds、cap-only、ceiling floor 不成立を拒否する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_grid_contract_requires_exact_none_stock_and_unique_effective_builds`  
  none 1、stock 1、effective build 重複なしを新 field 込みで固定する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_patch_b_requires_a_and_applies_to_exact_pin`  
  pure pin 上の `git apply --check B` は失敗、A 適用後は成功することを固定する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_patch_stack_touches_only_existing_a_owned_files_and_reverts_clean`  
  B に新規 file がなく、外側 `applied(A)` の exit 後に pinned-clean へ戻ることを固定する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_patch_b_defaults_select_stock_control_flow`  
  K/STEP_ADAPT/DYN_CEILING/TRACE=0 で各 `#else` が既存 stock 文を保持することを固定する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_backoff_trace_uses_numeric_if_and_has_no_outside_symbols`  
  `#if BACKOFF_TRACE` だけを認め、`#ifdef` と block 外の `izanagi_backoff_trace` 定義を拒否する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_perf_binary_has_no_backoff_trace_symbol`  
  A+B、全新 define default の Release binary に `nm` 上の prefix が 0 件であることを固定する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_trace_parser_requires_exact_bounded_sequence_and_summary`  
  stdout の record/summary、seq、TSC、hit 再計算、overflow 拒否を固定する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_backoff_trace_mode_is_separate_and_never_headline_eligible`  
  `BACKOFF_TRACE=1`、`CCBENCH_TRACE=0`、診断専用 JSON、通常性能値との分離を固定する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_public_certification_accepts_each_exact_cell`  
  tuned と全機構 on dynamic の二値をそれぞれ単独で受理する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_public_certification_exact_axes_reject_widening`  
  既存 node を拡張し、第三 cell、二 cell 同時、動的 field 1 箇所 drift を拒否する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_group_receipt_requires_one_exact_certification_cell_identity`  
  24 row 中の tuned/dynamic 混在、genome/patch-stack/source identity drift を拒否する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_pbs_certify_mode_preserves_legacy_literal_and_exact_two_value_set`  
  旧 tuned 文字列を byte-identical で残し、PBS が exact 二値以外を拒否する。

- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_pbs_backoff_trace_contract_uses_only_colon_and_plus_transport`  
  extended field に comma/semicolon/plus を使わず、plus は cell list transport にだけ使うことを固定する。

- `orchestrator/tests/test_condition_meaning_gate.py::test_v1_domain_and_claim_boundaries_are_exact`  
  supply domain、CMake route 19 件、7 macro の inert 値を固定する。

- `orchestrator/tests/test_screening_driver.py::test_screening_condition_requests_cover_exact_define_specs`  
  `_CONDITION_DEFAULTS` と `DEFINE_SPECS` の集合一致を既存 node で固定する。

- `orchestrator/tests/test_ccbench_spawn_sites.py::test_patch_define_inventory_matches_condition_gate_registry`  
  B が公開する 7 define と registry の一対一対応を固定する。

- `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_has_no_unreviewed_ungated_member`  
  新 define が未分類 build sink を生まないことを固定する。

- `orchestrator/tests/test_ccbench_spawn_sites.py::test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`  
  編集後の二つの build sink 行番号を exact に固定する。

- `orchestrator/tests/test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes`  
  path/class が変わっていないことを既存 golden で確認する。ファイル編集はしない。

- `orchestrator/tests/test_plot_dynamic_backoff.py::test_full_size_inputs_write_both_figures_and_provenance`  
  7×(6×3×8) performance row と 3×3×2 trace run の実寸 fixtureを本物の Figure/layout checkerへ通す。

- `orchestrator/tests/test_plot_dynamic_backoff.py::test_performance_uses_student_t_ci_and_hashes_all_eight_inputs`  
  t 分布 CI と 8 input SHA を固定する。

- `orchestrator/tests/test_plot_dynamic_backoff.py::test_rejects_incomplete_performance_or_diagnostic_grid`  
  cell/workload/thread/rep、trace run、patch-stack の欠落・重複を拒否する。

- `orchestrator/tests/test_plot_dynamic_backoff.py::test_layout_failure_publishes_no_partial_outputs`  
  bbox 失敗時に PNG/PDF/provenance を公開しないことを固定する。

さらに login-node 生死確認では、同じ toolchain/options で tuned を A-only と A+B-default の二度 build し、binary SHA を記録する。一致しなくても即失敗にはしないが、A+B 内の基準線同士だけで性能比較する。両 binary を 1 秒ずつ走らせ、A+B-default の `nm` prefix 0 と正常終了を要求する。

## 段 5 の分割

| 単位 | 所有ファイル | 依存 |
|---|---|---|
| A | `patches/cicada-adaptive-dynamic.patch` | pin+A の source shapeだけ |
| B | `tools/pegasus/probes/t2187_adaptive_const_probe.py`、`.pbs`、`orchestrator/campaign/condition_meaning_gate.py`、`screening_driver.py`、`orchestrator/tests/test_condition_meaning_gate.py`、`test_ccbench_spawn_sites.py`、`test_t2187_adaptive_const_probe.py` | brief 固定 define/schema。A の実 bytes は統合時だけ必要 |
| C | `tools/plotting/plot_dynamic_backoff.py`、`orchestrator/tests/test_plot_dynamic_backoff.py` | B と合意した JSON schema。fixture で先行実装可能 |

三集合は素である。A と B は define 名が固定済みなので並列可、C も schema contract を上記で固定すれば B と並列可。統合順は A→B→Cとし、A+B の適用検査、probe fixture、plot fixture の順で確認する。

`patches/README.md` と `tools/plotting/README.md` は親の docs lane が実装単位の統合後に更新する。`patches/ledger.json` は非変更。

## 投入設計の検算

**性能 7 job。** [probe.py:63-64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:63) は extime 3 秒、run timeout 180 秒。[main:2153-2169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:2153) は workload→thread→cell の直列 loop である。

```text
6 cell × 3 workload × 8 thread × 1 rep = 144 process/job
extime だけの下限 = 144 × 3 s = 432 s = 7.2 min
```

各 process は [runner.py:1088-1162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/calibrator/runner.py:1088) で独立起動され、CCBench は毎回 [ycsb_silo.cc:24-33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/external/ccbench/cc/silo/ycsb_silo.cc:24) の `makeDB()` を通る。[ycsb.hh:194-204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/external/ccbench/include/ycsb.hh:194) は 1,000,000 record を毎 process 再構築するため、3 秒だけを積算してはいけない。

brief の「120 run=8.5分」を比例利用すると、

```text
8.5 min / 120 = 4.25 s/process
144 × 4.25 s = 10.2 min
+ prologue 約2 min
+ 6 build 約3 min
= 約15.2 min/job
```

となる。したがって PBS の 40 分は約 2.6 倍の余裕を持ち、維持可能。ただし `3.6 s/process` ではなく 4.25 秒を事前登録の根拠にする。

**診断 1 job。**

```text
3 dynamic cell × 3 workload × 2 thread = 18 process
18 × 4.25 s ≈ 1.3 min
+ prologue 2 min
+ 3 build 1.5〜3 min
+ bounded stdout flush/parse
= 約5〜7 min、8 min見積もりは妥当
```

walltime は既存 40 分をそのまま使える。

**認証 24 job。** [probe.py:64-79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:64) の hard budget は、

```text
prologue 540
+ build 900
+ run 180
+ positive control 120
+ verifier 5400
+ exit margin 300
= 7440 s = 2:04:00
```

で、outer walltime 8100 秒=2:15:00より 660 秒小さい。[contract:474-487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:474) の strict inequality を満たす。

T-2189 の repo 記録では target verify は 87.1〜458.9 秒である。[insight:118-126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/output/insights/2026-09-04_t2189-adaptive-serializability-certification.md:118) したがって 55 分期待値は保守的だが、コードから保証できる上限は 2:15 である。

24 job は既存 PBS 呼出し形をそのまま使える。追加 env 変数は不要で、`IZANAGI_T2187_CELLS` を extended dynamic exact stringへ変え、既存の以下を別 attempt/output directoryで供給する。

```text
IZANAGI_T2187_GROUP_RECEIPT_OUT
IZANAGI_T2187_GROUP_RESULT_PATHS
IZANAGI_T2187_ATTEMPT_ID
IZANAGI_T2187_PERFORMANCE_ARTIFACT
IZANAGI_T2187_PERFORMANCE_ARTIFACT_SHA256
IZANAGI_T2187_EXPECTED_VERIFIER_IDENTITY
IZANAGI_T2187_EXPECTED_VERIFIER_IDENTITY_SHA256
```

診断用 `IZANAGI_T2187_BACKOFF_TRACE` は certify job では 0 のままにする。

期待ノード時間は brief の実績期待値なら約24時間だが、walltime 上限ベースでは最大約54ノード時間である。queue 待ちは別勘定。

## brief への指摘

**P1。** 実装可能。ただし現在の API では count 判定前に全 `res` を走査するしかなく、leader の全試行に48 atomic loadが入る。これは制御機構の効果と計測 overhead を交絡させる。診断 JSONに更新回数を残し、none/tuned 基準線とは必ず A+B 同 job で比較する必要がある。

**P2。** 初回の比較対象と「刻みを更新してから現在の一歩に使うか」が未規定。本案は初回だけ初期刻み、その後は現在観測した符号から刻みを更新して同じ更新に使う。段 4 で固定が必要。また `last_backoff_` が `uint64_t` のため、0.25/0.5 µs は既知の偽ゼロ勾配を受ける。

**P3。** 上限半減と hill-climb の順序が未規定。本案では ceiling を先に半減し、その後の値を新 ceiling へ clamp する。この場合、上限で負勾配が出ると一歩ではなくほぼ半減位置まで大きく下がる。これが意図でなければ「一歩移動後に次窓用 ceiling を更新」へ変える裁定が必要。

**P4。** 実装可能。全機構 on の dynamic 1腕だけを新規24 requestで認証し、tuned は legacy exact cell として受理集合に残す。他2腕は未認証と明記する。

**P5。** 実装可能。二重 `applied()` は不可能だが、外側 `applied(A)` 内の `apply_patch(B)` と、B path⊆A path の検査で単純化できる。外側の `git checkout -- .` が両方を戻す。A-only/A+B binary SHA 一致は保証できず、source line/debug情報や source identity により不一致でも機構差とは限らない。

**P6。** 144 run、診断18 run、認証24 requestの個数は正しい。一方 `120 run=8.5分` と `3.6 s/run` は算術上一致しない。DB再構築込みの4.25秒を使うと性能 job は約15.2分。40分 walltimeは維持可能。

**P7。brief との不一致。** 指定された三 consumer は patch ledger consumer ではない。実 consumer の rung1 contract が exact-oneを要求するため、新 entry は追加不能。README + DefineSpecだけが正しい。

**P8。** 実装可能だが `measure_point()` の戻り値から raw stdout は得られない。runnerを改造せず、既存 `subprocess_runner` seamで stdoutを横取りするのが最小変更。

**P9。** K=10,000は 4 M tps×2,560 µs≈10,240 commit と整合する。一方 `cw` の `update_us` と adapt-off時のmin/maxが未記載。本案では2560と100/100を採った。段 4 裁定が必要。

加えて、実測対象は `Genome("silo", ...)` と `ycsb_silo.exe` であり、「Cicada」は protocol 名ではなく adaptive backoff 算法の由来である。成果物では「Silo 上の Cicada 型 adaptive backoff」と書く。

## 総括

- **brief との不一致:** P7 の consumer 指定は repo の実態と合わず、真の rung1 contract は ledger entry を1件に固定している。P6 の 3.6秒/run も brief 内の8.5分/120 runと一致しない。
- **実装不能と判断した項目:** 現 schema/consumerを維持したまま `patches/ledger.json` へD18第3類 entryを追加すること。その他は実装可能だが、P2初回規則、P3更新順序、P9省略値は段4裁定が必要。
- **段 5 の単位数:** **3単位**。A=patch B、B=probe/PBS/tests/registry、C=plot generator/test。defineとJSON schemaを本計画どおり固定すれば並列実装できる。
