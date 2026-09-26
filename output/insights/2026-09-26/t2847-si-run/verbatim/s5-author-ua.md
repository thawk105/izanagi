2 本の patch を作成しました。どちらも **pin C → `instr-si-trace-v2.patch` → 壊し patch** の順で適用できます。build・実走はしていません。

検査では、各 patch の `git apply --check` と適用、マクロ枝を除去した場合の v2 適用後ファイルとのバイト一致、`IZANAGI_` token が指定マクロ 1 種だけであることを確認しました。touch set はそれぞれ `cc/si/transaction.cc` のみです。site 行番号は各 patch 適用後のファイルでの `#if <macro>` 行です。

| patch | site 数と行番号 | 診断の加算点 |
|---|---|---|
| [broken-si-first-updater-wins.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-ua/patches/broken-si-first-updater-wins.patch) | 7：4, 22, 46, 197, 224, 243, 714 | `reached` は元の abort 条件成立時、`changed` はその試行の CAS 成功時 |
| [broken-si-read-uncommitted-version.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-ua/patches/broken-si-read-uncommitted-version.patch) | 5：4, 22, 46, 177, 710 | `reached` と `changed` は snapshot 条件を満たす未確定版を選択した時 |

両方とも取引の印を `begin()` で戻し、印のある取引が `commit()` に成功した時だけ `committed` を 1 加算します。3 counter は relaxed atomic で、process 終了時に stderr へ指定 slug の `T2847_FIRED` を 1 行出します。診断は verifier の判定には使いません。

### `broken-si-first-updater-wins.patch` 全文

```diff
diff --git a/cc/si/transaction.cc b/cc/si/transaction.cc
--- a/cc/si/transaction.cc
+++ b/cc/si/transaction.cc
@@ -1,6 +1,9 @@
 #include <algorithm>
 #include <atomic>
 #include <bitset>
+#if IZANAGI_BREAK_SI_FIRST_UPDATER_WINS
+#include <cstdio>
+#endif
 #include <set>

 #include "../../include/atomic_wrapper.hh"
@@ -16,6 +19,23 @@
                        const uint64_t threshold);

 using namespace std;
+#if IZANAGI_BREAK_SI_FIRST_UPDATER_WINS
+namespace {
+static std::atomic<uint64_t> t2847_reached{0};
+static std::atomic<uint64_t> t2847_changed{0};
+static std::atomic<uint64_t> t2847_committed{0};
+static thread_local bool t2847_transaction_touched = false;
+struct T2847Report {
+  ~T2847Report() {
+    std::fprintf(stderr, "T2847_FIRED slug=si-first-updater-wins reached=%llu changed=%llu committed=%llu\n",
+        static_cast<unsigned long long>(t2847_reached.load(std::memory_order_relaxed)),
+        static_cast<unsigned long long>(t2847_changed.load(std::memory_order_relaxed)),
+        static_cast<unsigned long long>(t2847_committed.load(std::memory_order_relaxed)));
+  }
+};
+static T2847Report t2847_report;
+} // namespace
+#endif

 /**
  * @brief Initialize function of transaction.
@@ -23,6 +43,9 @@
  * @return void
  */
 void TxExecutor::begin() {
+#if IZANAGI_BREAK_SI_FIRST_UPDATER_WINS
+  t2847_transaction_touched = false;
+#endif
   TransactionTable *newElement, *tmt;

   tmt = loadAcquire(TMT[thid_]);
@@ -171,6 +194,9 @@
   Version* vertmp;
   Version* expected = tuple->latest_.load(memory_order_acquire);
   for (;;) {
+#if IZANAGI_BREAK_SI_FIRST_UPDATER_WINS
+    bool t2847_conflict_seen = false;
+#endif
     // w-w conflict
     // first updater wins rule
     if (expected->status_.load(memory_order_acquire) ==
@@ -195,6 +221,12 @@
       vertmp = vertmp->prev_;

     // vertmp is latest committed version.
+#if IZANAGI_BREAK_SI_FIRST_UPDATER_WINS
+    if (txid_ < vertmp->cstamp_.load(memory_order_acquire)) {
+      t2847_reached.fetch_add(1, std::memory_order_relaxed);
+      t2847_conflict_seen = true;
+    }
+#else
     if (txid_ < vertmp->cstamp_.load(memory_order_acquire)) {
       //  write - write conflict, first-updater-wins rule.
       // Writers must abort if they would overwirte a version created after
@@ -205,11 +237,23 @@
       gcobject_.reuse_version_from_gc_.emplace_back(desired);
       return Status::ERROR_CONCURRENT_WRITE_OR_DELETE;
     }
+#endif

     desired->prev_ = expected;
+#if IZANAGI_BREAK_SI_FIRST_UPDATER_WINS
+    if (tuple->latest_.compare_exchange_strong(
+            expected, desired, memory_order_acq_rel, memory_order_acquire)) {
+      if (t2847_conflict_seen) {
+        t2847_changed.fetch_add(1, std::memory_order_relaxed);
+        t2847_transaction_touched = true;
+      }
+      break;
+    }
+#else
     if (tuple->latest_.compare_exchange_strong(
             expected, desired, memory_order_acq_rel, memory_order_acquire))
       break;
+#endif
   }

   return Status::OK;
@@ -667,6 +711,10 @@
    * Maintenance phase
    */
   mainte();
+#if IZANAGI_BREAK_SI_FIRST_UPDATER_WINS
+  if (t2847_transaction_touched)
+    t2847_committed.fetch_add(1, std::memory_order_relaxed);
+#endif
   return true;
 }
```

### `broken-si-read-uncommitted-version.patch` 全文

```diff
diff --git a/cc/si/transaction.cc b/cc/si/transaction.cc
--- a/cc/si/transaction.cc
+++ b/cc/si/transaction.cc
@@ -1,6 +1,9 @@
 #include <algorithm>
 #include <atomic>
 #include <bitset>
+#if IZANAGI_BREAK_SI_READ_UNCOMMITTED_VERSION
+#include <cstdio>
+#endif
 #include <set>

 #include "../../include/atomic_wrapper.hh"
@@ -16,6 +19,23 @@
                        const uint64_t threshold);

 using namespace std;
+#if IZANAGI_BREAK_SI_READ_UNCOMMITTED_VERSION
+namespace {
+static std::atomic<uint64_t> t2847_reached{0};
+static std::atomic<uint64_t> t2847_changed{0};
+static std::atomic<uint64_t> t2847_committed{0};
+static thread_local bool t2847_transaction_touched = false;
+struct T2847Report {
+  ~T2847Report() {
+    std::fprintf(stderr, "T2847_FIRED slug=si-read-uncommitted-version reached=%llu changed=%llu committed=%llu\n",
+        static_cast<unsigned long long>(t2847_reached.load(std::memory_order_relaxed)),
+        static_cast<unsigned long long>(t2847_changed.load(std::memory_order_relaxed)),
+        static_cast<unsigned long long>(t2847_committed.load(std::memory_order_relaxed)),
+        static_cast<unsigned long long>(t2847_committed.load(std::memory_order_relaxed)));
+  }
+};
+static T2847Report t2847_report;
+} // namespace
+#endif

 /**
  * @brief Initialize function of transaction.
@@ -23,6 +43,9 @@
  * @return void
  */
 void TxExecutor::begin() {
+#if IZANAGI_BREAK_SI_READ_UNCOMMITTED_VERSION
+  t2847_transaction_touched = false;
+#endif
   TransactionTable *newElement, *tmt;

   tmt = loadAcquire(TMT[thid_]);
@@ -151,12 +174,29 @@
    */
   Version* ver;
   ver = tuple->latest_.load(memory_order_acquire);
+#if IZANAGI_BREAK_SI_READ_UNCOMMITTED_VERSION
+  for (;;) {
+    const VersionStatus status = ver->status_.load(memory_order_acquire);
+    if (txid_ >= ver->cstamp_.load(memory_order_acquire)) {
+      if (status != VersionStatus::committed &&
+          status != VersionStatus::deleted) {
+        t2847_reached.fetch_add(1, std::memory_order_relaxed);
+        t2847_changed.fetch_add(1, std::memory_order_relaxed);
+        t2847_transaction_touched = true;
+      }
+      break;
+    }
+    ver = ver->prev_;
+    if (ver == nullptr) { return nullptr; }
+  }
+#else
   while ((ver->status_.load(memory_order_acquire) != VersionStatus::committed &&
           ver->status_.load(memory_order_acquire) != VersionStatus::deleted) ||
          txid_ < ver->cstamp_.load(memory_order_acquire)) {
     ver = ver->prev_;
     if (ver == nullptr) { return nullptr; }
   }
+#endif

   // SI: just record the version we observed in the snapshot.
   // (ERMIA tracked sstamp via psstamp_ for SSN's anti-dependency check;
@@ -667,6 +707,10 @@
    * Maintenance phase
    */
   mainte();
+#if IZANAGI_BREAK_SI_READ_UNCOMMITTED_VERSION
+  if (t2847_transaction_touched)
+    t2847_committed.fetch_add(1, std::memory_order_relaxed);
+#endif
   return true;
 }
```

**source 上の評価:** V29 は inflight 分岐と CAS 再試行を残し、版の解放経路を増やしていません。競合が続けば停止しうる既存の再試行ループですが、新たな無限ループや二重解放を加える変更はありません。V28 は snapshot 条件と `prev_ == nullptr` での終了を残し、解放処理を加えていません。一方、裁定どおり未完成 `body_` の読みや回収後に再利用された版の参照は起こりえます。異常終了・停止の有無は実走結果で確認が必要です。

所有外への波及先は条件 gate の macro 登録と site 数、screening driver、対応する表固定テスト、起動器の build 列です。これらは本作業では編集していません。

## 総括

指定の 2 patch を作成し、scratch で適用順・未定義時のバイト一致・macro 種類・touch set を確認しました。build と benchmark は未実走です。