# 試作 patch revS の逐語 (`ss2pl-lock-protocol-study-define-only.patch`、Codex `role=author` 段 5 + fix1。repo の `patches/` へは入れない。`.patch` 拡張子は provenance checker が実装面扱いするので `.md` に写す)

sha256 `8ccb4c59e467253c73f90f27b0891f5f67ba66311e9a65ca261582282580db50`、86,721 bytes。

```diff
diff --git a/cc/ss2pl/CMakeLists.txt b/cc/ss2pl/CMakeLists.txt
index 7cc2f407..2eed1239 100644
--- a/cc/ss2pl/CMakeLists.txt
+++ b/cc/ss2pl/CMakeLists.txt
@@ -1,7 +1,39 @@
+if(NOT CCBENCH_SS2PL_LOCK_IMPL MATCHES "^[01]$")
+  message(FATAL_ERROR "CCBENCH_SS2PL_LOCK_IMPL must be 0 or 1")
+endif()
+if(NOT CCBENCH_SS2PL_LOCK_KIND MATCHES "^[01]$")
+  message(FATAL_ERROR "CCBENCH_SS2PL_LOCK_KIND must be 0 or 1")
+endif()
+if(NOT CCBENCH_SS2PL_DLR MATCHES "^[012]$")
+  message(FATAL_ERROR "CCBENCH_SS2PL_DLR must be 0, 1, or 2")
+endif()
+if(NOT CCBENCH_SS2PL_WFG_DIAG MATCHES "^[01]$")
+  message(FATAL_ERROR "CCBENCH_SS2PL_WFG_DIAG must be 0 or 1")
+endif()
+
+
+set(_ss2pl_sources transaction.cc util.cc)
+if(CCBENCH_SS2PL_WFG_DIAG EQUAL 1)
+  list(APPEND _ss2pl_sources wfg.cc)
+endif()
+
 ccbench_add_protocol(ss2pl
-  SOURCES   transaction.cc util.cc
-  WORKLOADS bomb tpcc
+  SOURCES   ${_ss2pl_sources}
+  WORKLOADS ycsb bomb tpcc
   OPTIONS
     DLR1
     KEY_SORT=${CCBENCH_KEY_SORT}
+    SS2PL_LOCK_IMPL=${CCBENCH_SS2PL_LOCK_IMPL}
+    SS2PL_LOCK_KIND=${CCBENCH_SS2PL_LOCK_KIND}
+    SS2PL_DLR=${CCBENCH_SS2PL_DLR}
+    SS2PL_WFG_DIAG=${CCBENCH_SS2PL_WFG_DIAG}
 )
+
+# util.cc validates and displays the YCSB-prefixed flags only in the YCSB
+# binary.  The other workload binaries do not define those gflags.
+target_compile_definitions(ycsb_ss2pl.exe PRIVATE SS2PL_WORKLOAD_YCSB=1)
+
+option(CCBENCH_BUILD_SS2PL_TESTS "Build SS2PL unit tests" OFF)
+if(CCBENCH_BUILD_SS2PL_TESTS)
+  add_subdirectory(test)
+endif()
diff --git a/cc/ss2pl/bomb_ss2pl.cc b/cc/ss2pl/bomb_ss2pl.cc
index 051d732b..50153c27 100644
--- a/cc/ss2pl/bomb_ss2pl.cc
+++ b/cc/ss2pl/bomb_ss2pl.cc
@@ -3,6 +3,9 @@
 #include "include/common.hh"
 #include "include/result.hh"
 #include "include/transaction.hh"
+#if SS2PL_WFG_DIAG
+#include "include/ss2pl_wfg.hh"
+#endif
 #include "include/util.hh"
 
 // For BoMB with next-key/gap lock like phantom avoidance.
@@ -28,6 +31,10 @@ int main(int argc, char* argv[]) try {
 
   initResult(TotalThreadNum);
 
+#if SS2PL_WFG_DIAG
+  ss2pl_wfg_start(FLAGS_ss2pl_wfg_output, TotalThreadNum);
+#endif
+
   ccbench::RunnerOptions opts;
   opts.display_per_tx = true;
   opts.enable_bomb_dispatcher = FLAGS_bomb_mixed_mode;
@@ -55,5 +62,9 @@ int main(int argc, char* argv[]) try {
       },
       ccbench::NoOpHook{}, &BombWorkload<Tuple, void>::request_dispatcher);
 
+#if SS2PL_WFG_DIAG
+  ss2pl_wfg_stop();
+#endif
+
   return 0;
 } catch (const bad_alloc&) { ERR; }
diff --git a/cc/ss2pl/include/common.hh b/cc/ss2pl/include/common.hh
index 5b504661..05900ad3 100644
--- a/cc/ss2pl/include/common.hh
+++ b/cc/ss2pl/include/common.hh
@@ -30,26 +30,40 @@ alignas(CACHE_LINE_SIZE) GLOBAL MasstreeWrapper<Tuple> MT;
 DEFINE_uint64(clocks_per_us, 2100,
               "CPU_MHz. Use this info for measuring time.");
 DEFINE_uint64(extime, 3, "Execution time[sec].");
+#if !defined(SS2PL_WORKLOAD_YCSB) || !SS2PL_WORKLOAD_YCSB
 DEFINE_uint64(max_ope, 10,
               "Total number of operations per single transaction.");
 DEFINE_bool(rmw, false,
             "True means read modify write, false means blind write.");
 DEFINE_uint64(rratio, 50, "read ratio of single transaction.");
+#endif
 DEFINE_uint64(thread_num, 10, "Total number of worker threads.");
+#if !defined(SS2PL_WORKLOAD_YCSB) || !SS2PL_WORKLOAD_YCSB
 DEFINE_uint64(tuple_num, 1000000, "Total number of records.");
 DEFINE_bool(ycsb, true,
             "True uses zipf_skew, false uses faster random generator.");
 DEFINE_double(zipf_skew, 0, "zipf skew. 0 ~ 0.999...");
+#endif
+#if SS2PL_WFG_DIAG
+DEFINE_string(ss2pl_wfg_output, "", "Durable wait-for graph JSON path.");
+#endif
 #else
 DECLARE_uint64(clocks_per_us);
 DECLARE_uint64(extime);
+#if !defined(SS2PL_WORKLOAD_YCSB) || !SS2PL_WORKLOAD_YCSB
 DECLARE_uint64(max_ope);
 DECLARE_bool(rmw);
 DECLARE_uint64(rratio);
+#endif
 DECLARE_uint64(thread_num);
+#if !defined(SS2PL_WORKLOAD_YCSB) || !SS2PL_WORKLOAD_YCSB
 DECLARE_uint64(tuple_num);
 DECLARE_bool(ycsb);
 DECLARE_double(zipf_skew);
 #endif
+#if SS2PL_WFG_DIAG
+DECLARE_string(ss2pl_wfg_output);
+#endif
+#endif
 
 alignas(CACHE_LINE_SIZE) GLOBAL uint32_t TotalThreadNum;
diff --git a/cc/ss2pl/include/transaction.hh b/cc/ss2pl/include/transaction.hh
index cdcb7e82..ee6472ad 100644
--- a/cc/ss2pl/include/transaction.hh
+++ b/cc/ss2pl/include/transaction.hh
@@ -7,7 +7,7 @@
 #include "../../../include/backoff.hh"
 #include "../../../include/procedure.hh"
 #include "../../../include/result.hh"
-#include "../../../include/rwlock.hh"
+#include "ss2pl_lock.hh"
 #include "../../../include/string.hh"
 #include "../../../include/util.hh"
 #include "ss2pl_op_element.hh"
@@ -35,11 +35,30 @@ public:
   vector<Procedure> pro_set_;
   std::deque<Tuple*> gc_records_;
   const bool& quit_; // for thread termination control
+#if SS2PL_LOCK_IMPL == 1
+  SS2PLTxControl& control_;
+#elif SS2PL_WFG_DIAG
+  std::uint64_t diagnostic_attempt_ = 0;
+#endif
 
   bool reconnoitering_ = false;
   bool is_ronly_ = false;
   bool is_batch_ = false;
 
+#if SS2PL_LOCK_IMPL == 1
+  TxExecutor(int thid, Result* res, const bool& quit)
+      : thid_(thid), result_(res), backoff_(FLAGS_clocks_per_us), quit_(quit)
+#if SS2PL_LOCK_IMPL == 1
+        , control_(ss2pl_control(static_cast<std::uint32_t>(thid)))
+#endif
+  {
+#if SS2PL_LOCK_IMPL == 1
+    control_.initialize(static_cast<std::uint32_t>(thid), quit);
+#endif
+    //
+    //    genStringRepeatedNumber(write_val_, VAL_SIZE, thid);
+  }
+#else
   TxExecutor(int thid, Result* res, const bool& quit)
       : thid_(thid), result_(res), backoff_(FLAGS_clocks_per_us), quit_(quit) {
     //    read_set_.reserve(FLAGS_max_ope);
@@ -50,6 +69,7 @@ public:
     //
     //    genStringRepeatedNumber(write_val_, VAL_SIZE, thid);
   }
+#endif
 
   SetElement<Tuple>* searchReadSet(Storage s, std::string_view key);
 
@@ -87,6 +107,15 @@ public:
 
   void unlockList();
 
+#if SS2PL_LOCK_IMPL == 1
+  [[nodiscard]] bool hasReadLock(const ReaderWriteLock* lock) const;
+  [[nodiscard]] bool hasWriteLock(const ReaderWriteLock* lock) const;
+#endif
+
+#if SS2PL_LOCK_IMPL == 1 || SS2PL_WFG_DIAG
+  [[nodiscard]] std::uint64_t currentAttempt() const;
+#endif
+
   void reconnoiter_begin();
   void reconnoiter_end();
 
diff --git a/cc/ss2pl/include/tuple.hh b/cc/ss2pl/include/tuple.hh
index d670266e..2a8abf47 100644
--- a/cc/ss2pl/include/tuple.hh
+++ b/cc/ss2pl/include/tuple.hh
@@ -5,7 +5,7 @@
 
 #include "../../../include/cache_line_size.hh"
 #include "../../../include/inline.hh"
-#include "../../../include/rwlock.hh"
+#include "ss2pl_lock.hh"
 #include "../../../include/tuple_body.hh"
 
 using namespace std;
@@ -24,6 +24,8 @@ public:
 
   void init(TupleBody&& body) {
     body_ = std::move(body);
+#if SS2PL_LOCK_IMPL == 0
     lock_.w_lock();
+#endif
   }
 };
diff --git a/cc/ss2pl/test/CMakeLists.txt b/cc/ss2pl/test/CMakeLists.txt
index 176ebde3..d401a7c0 100644
--- a/cc/ss2pl/test/CMakeLists.txt
+++ b/cc/ss2pl/test/CMakeLists.txt
@@ -1,18 +1,47 @@
-file(GLOB SS2PL_SOURCES
-        "${PROJECT_SOURCE_DIR}/../common/result.cc"
-        "${PROJECT_SOURCE_DIR}/../common/util.cc"
-        "${PROJECT_SOURCE_DIR}/result.cc"
-        "${PROJECT_SOURCE_DIR}/transaction.cc"
-        "${PROJECT_SOURCE_DIR}/util.cc"
-        )
+get_filename_component(SS2PL_PROTOCOL_DIR "${CMAKE_CURRENT_LIST_DIR}/.."
+                       ABSOLUTE)
+get_filename_component(CCBENCH_SOURCE_DIR "${CMAKE_CURRENT_LIST_DIR}/../../.."
+                       ABSOLUTE)
+set(SS2PL_SOURCES
+    "${CCBENCH_SOURCE_DIR}/common/result.cc"
+    "${CCBENCH_SOURCE_DIR}/common/util.cc"
+    "${SS2PL_PROTOCOL_DIR}/transaction.cc"
+    "${SS2PL_PROTOCOL_DIR}/util.cc"
+)
+
+if(CCBENCH_SS2PL_WFG_DIAG EQUAL 1)
+    list(APPEND SS2PL_SOURCES "${SS2PL_PROTOCOL_DIR}/wfg.cc")
+endif()
 
 file (GLOB TEST_SOURCES
-"make_db_test.cpp"
+"make_db_test.cpp" "study_lock_test.cpp"
 )
 
+if(NOT CCBENCH_SS2PL_LOCK_IMPL MATCHES "^[01]$")
+    message(FATAL_ERROR "CCBENCH_SS2PL_LOCK_IMPL must be 0 or 1")
+endif()
+if(NOT CCBENCH_SS2PL_LOCK_KIND MATCHES "^[01]$")
+    message(FATAL_ERROR "CCBENCH_SS2PL_LOCK_KIND must be 0 or 1")
+endif()
+if(NOT CCBENCH_SS2PL_DLR MATCHES "^[012]$")
+    message(FATAL_ERROR "CCBENCH_SS2PL_DLR must be 0, 1, or 2")
+endif()
+if(NOT CCBENCH_SS2PL_WFG_DIAG MATCHES "^[01]$")
+    message(FATAL_ERROR "CCBENCH_SS2PL_WFG_DIAG must be 0 or 1")
+endif()
+
+if(CCBENCH_SS2PL_DLR EQUAL 0)
+    set(SS2PL_TEST_DLR_MARKER DLR0)
+elseif(CCBENCH_SS2PL_DLR EQUAL 1)
+    set(SS2PL_TEST_DLR_MARKER DLR1)
+elseif(CCBENCH_SS2PL_DLR EQUAL 2)
+    set(SS2PL_TEST_DLR_MARKER DLR2)
+else()
+    message(FATAL_ERROR "CCBENCH_SS2PL_DLR must be 0, 1, or 2")
+endif()
+
 # Build-time flags. The universal `-D` set comes from cmake/Options.cmake so
-# the test target uses the same flags as the ss2pl protocol body; DLR1 and
-# KEY_SORT are ss2pl-specific (mirrors cc/ss2pl/CMakeLists.txt).
+# the test target uses the same flags as the ss2pl protocol body.
 ccbench_universal_definitions(SS2PL_TEST_DEFINITIONS)
 
 foreach(src IN LISTS TEST_SOURCES)
@@ -24,11 +53,21 @@ foreach(src IN LISTS TEST_SOURCES)
     target_compile_definitions(${test_name}
             PRIVATE
             ${SS2PL_TEST_DEFINITIONS}
-            DLR1
+            ${SS2PL_TEST_DLR_MARKER}
             KEY_SORT=${CCBENCH_KEY_SORT}
+            SS2PL_LOCK_IMPL=${CCBENCH_SS2PL_LOCK_IMPL}
+            SS2PL_LOCK_KIND=${CCBENCH_SS2PL_LOCK_KIND}
+            SS2PL_DLR=${CCBENCH_SS2PL_DLR}
+            SS2PL_WFG_DIAG=${CCBENCH_SS2PL_WFG_DIAG}
     )
+    if(test_name STREQUAL "make_db_test")
+        target_compile_definitions(${test_name} PRIVATE SS2PL_WORKLOAD_YCSB=1)
+    elseif(test_name STREQUAL "study_lock_test")
+        target_compile_definitions(${test_name}
+                PRIVATE SS2PL_STUDY_LOCK_TESTING=1)
+    endif()
 
-    # All three deps now come from FetchContent (cmake/ThirdParty.cmake) —
+    # All three deps now come from FetchContent (cmake/ThirdParty.cmake) -
     # GTest::gtest{,_main} carry their own INTERFACE_INCLUDE_DIRECTORIES so
     # we no longer need the manual include path override.
     target_link_libraries(${test_name}
@@ -46,4 +85,4 @@ foreach(src IN LISTS TEST_SOURCES)
         NAME ${test_name}
         COMMAND ${test_name} --gtest_output=xml:${test_name}_gtest_result.xml
     )
-endforeach()
\ No newline at end of file
+endforeach()
diff --git a/cc/ss2pl/test/make_db_test.cpp b/cc/ss2pl/test/make_db_test.cpp
index bf0dc382..12da8b87 100644
--- a/cc/ss2pl/test/make_db_test.cpp
+++ b/cc/ss2pl/test/make_db_test.cpp
@@ -4,14 +4,24 @@
 #define GLOBAL_VALUE_DEFINE
 
 #include "../../../include/backoff.hh"
-#include "../../include/common.hh"
-#include "../../include/util.hh"
+#include "../include/common.hh"
+#include "../../../include/ycsb.hh"
+#include "../include/util.hh"
 
 #include "glog/logging.h"
 #include "gtest/gtest.h"
 
 namespace ccbench::testing {
 
+class YcsbTableView {
+public:
+  Tuple& operator[](std::uint64_t id) const {
+    SimpleKey<8> key;
+    YCSB::CreateKey(id, key.ptr());
+    return *Masstrees[get_storage(Storage::YCSB)].get_value(key.view());
+  }
+};
+
 class make_db_test : public ::testing::Test {
 public:
   static void call_once_f() {
@@ -28,13 +38,19 @@ private:
 };
 
 TEST_F(make_db_test, simple) { // NOLINT
-  makeDB();
+  FLAGS_ycsb_tuple_num = 8;
+  YcsbWorkload::makeDB<Tuple, void>(nullptr);
+  const YcsbTableView Table;
   // verify effect makeDb
-  for (std::uint64_t i = 0; i < FLAGS_tuple_num; ++i) {
-    ASSERT_EQ(Table[i].val_[0], 'a');
-    ASSERT_EQ(Table[i].val_[1], '\0');
+  for (std::uint64_t i = 0; i < FLAGS_ycsb_tuple_num; ++i) {
+    const YCSB& value = Table[i].body_.get_value().cast_to<YCSB>();
+    ASSERT_EQ(value.id_, i);
+#if SS2PL_LOCK_IMPL == 0
     ASSERT_EQ(Table[i].lock_.counter.load(std::memory_order_acquire), 0);
+#else
+    ASSERT_TRUE(Table[i].lock_.is_unlocked_for_test());
+#endif
   }
 }
 
-} // namespace ccbench::testing
\ No newline at end of file
+} // namespace ccbench::testing
diff --git a/cc/ss2pl/tpcc_ss2pl.cc b/cc/ss2pl/tpcc_ss2pl.cc
index 69993363..c3aa69d1 100644
--- a/cc/ss2pl/tpcc_ss2pl.cc
+++ b/cc/ss2pl/tpcc_ss2pl.cc
@@ -3,6 +3,9 @@
 #include "include/common.hh"
 #include "include/result.hh"
 #include "include/transaction.hh"
+#if SS2PL_WFG_DIAG
+#include "include/ss2pl_wfg.hh"
+#endif
 #include "include/util.hh"
 
 #include "../../include/cpu.hh"
@@ -26,6 +29,10 @@ int main(int argc, char* argv[]) try {
 
   initResult(TotalThreadNum);
 
+#if SS2PL_WFG_DIAG
+  ss2pl_wfg_start(FLAGS_ss2pl_wfg_output, TotalThreadNum);
+#endif
+
   ccbench::RunnerOptions opts;
   opts.display_per_tx = true;
 
@@ -43,5 +50,9 @@ int main(int argc, char* argv[]) try {
 #endif
       });
 
+#if SS2PL_WFG_DIAG
+  ss2pl_wfg_stop();
+#endif
+
   return 0;
 } catch (const bad_alloc&) { ERR; }
diff --git a/cc/ss2pl/transaction.cc b/cc/ss2pl/transaction.cc
index 4e5a7ed8..3ffdee73 100644
--- a/cc/ss2pl/transaction.cc
+++ b/cc/ss2pl/transaction.cc
@@ -1,4 +1,3 @@
-
 #include <stdio.h>
 #include <string.h>
 
@@ -10,6 +9,7 @@
 #include "../../include/result.hh"
 #include "include/common.hh"
 #include "include/transaction.hh"
+#include "include/ss2pl_wfg.hh"
 
 using namespace std;
 
@@ -35,25 +35,81 @@ inline SetElement<Tuple>* TxExecutor::searchWriteSet(Storage s,
   return nullptr;
 }
 
-/**
- * @brief function about abort.
- * Clean-up local read/write set.
- * Release locks.
- * @return void
- */
+#if SS2PL_LOCK_IMPL == 1
+bool TxExecutor::hasReadLock(const ReaderWriteLock* lock) const {
+  for (const ReaderWriteLock* held : r_lock_list_) {
+    if (held == lock) return true;
+  }
+  return false;
+}
+
+bool TxExecutor::hasWriteLock(const ReaderWriteLock* lock) const {
+  for (const ReaderWriteLock* held : w_lock_list_) {
+    if (held == lock) return true;
+  }
+  return false;
+}
+#endif
+
+#if SS2PL_LOCK_IMPL == 1 || SS2PL_WFG_DIAG
+std::uint64_t TxExecutor::currentAttempt() const {
+#if SS2PL_LOCK_IMPL == 1
+  return control_.attempt();
+#else
+  return diagnostic_attempt_;
+#endif
+}
+#endif
+
+#if SS2PL_WFG_DIAG
+namespace {
+
+void publish_wait(TxExecutor& tx, ReaderWriteLock* lock, SS2PLWfgMode mode) {
+#if SS2PL_DLR != 1
+  ss2pl_wfg_before_wait(static_cast<std::uint32_t>(tx.thid_),
+                        tx.currentAttempt(), lock, mode);
+#else
+  (void) tx;
+  (void) lock;
+  (void) mode;
+#endif
+}
+
+void publish_acquired(TxExecutor& tx, ReaderWriteLock* lock,
+                      SS2PLWfgMode mode, bool upgrade = false) {
+  ss2pl_wfg_acquired(static_cast<std::uint32_t>(tx.thid_), lock, mode);
+  ss2pl_wfg_record_acquire(mode, upgrade);
+}
+
+void publish_failed(TxExecutor& tx) {
+  ss2pl_wfg_acquire_failed(static_cast<std::uint32_t>(tx.thid_));
+#if SS2PL_DLR == 1
+  ss2pl_wfg_record_no_wait_failure();
+#endif
+}
+
+void publish_released(TxExecutor& tx, ReaderWriteLock* lock) {
+  ss2pl_wfg_released(static_cast<std::uint32_t>(tx.thid_), lock);
+}
+
+} // namespace
+#endif
+
 void TxExecutor::abort() {
-  /**
-   * Release locks
-   */
   unlockList();
 
-  /**
-   * Clean-up local read/write set.
-   */
   read_set_.clear();
   write_set_.clear();
 
+#if defined(SS2PL_WORKLOAD_YCSB) && SS2PL_WORKLOAD_YCSB
+// The workload owns the increment.
+#else
   ++result_->local_abort_counts_;
+#endif
+
+#if SS2PL_LOCK_IMPL == 1
+  control_.finish_abort();
+#endif
 
 #if BACK_OFF
 #if ADD_ANALYSIS
@@ -65,15 +121,19 @@ void TxExecutor::abort() {
 #if ADD_ANALYSIS
   result_->local_backoff_latency_ += rdtscp() - start;
 #endif
-
 #endif
 }
 
-/**
- * @brief success termination of transaction.
- * @return void
- */
 bool TxExecutor::commit() {
+#if SS2PL_LOCK_IMPL == 1
+  if (!control_.prepare_commit()) {
+    if (status_ != TransactionStatus::invalid) {
+      status_ = TransactionStatus::aborted;
+    }
+    return false;
+  }
+#endif
+
   for (auto itr = write_set_.begin(); itr != write_set_.end(); ++itr) {
     switch ((*itr).op_) {
       case OpType::UPDATE: {
@@ -85,11 +145,8 @@ bool TxExecutor::commit() {
         break;
       }
       case OpType::DELETE: {
-        // Return value intentionally ignored: a missing key still needs the
-        // record put on the GC queue below.
         Masstrees[get_storage((*itr).storage_)].remove_value_if_present(
             (*itr).key_);
-        // create information for garbage collection
         gc_records_.push_back((*itr).rcdptr_);
         break;
       }
@@ -98,41 +155,42 @@ bool TxExecutor::commit() {
     }
   }
 
-  /**
-   * Release locks.
-   */
   unlockList();
 
-  /**
-   * Clean-up local read/write set.
-   */
   read_set_.clear();
   write_set_.clear();
 
+#if SS2PL_LOCK_IMPL == 1
+  control_.finish_commit();
+#endif
   return true;
 }
 
-/**
- * @brief Initialize function of transaction.
- * Allocate timestamp.
- * @return void
- */
+#if SS2PL_LOCK_IMPL == 0 && !SS2PL_WFG_DIAG && (!defined(SS2PL_WORKLOAD_YCSB) || !SS2PL_WORKLOAD_YCSB)
 void TxExecutor::begin() { this->status_ = TransactionStatus::inflight; }
+#else
+void TxExecutor::begin() {
+  this->status_ = TransactionStatus::inflight;
+#if SS2PL_LOCK_IMPL == 1
+  control_.begin_attempt();
+#elif SS2PL_WFG_DIAG
+  ++diagnostic_attempt_;
+#endif
+#if SS2PL_WFG_DIAG
+  ss2pl_wfg_register_worker(
+      static_cast<std::uint32_t>(thid_), currentAttempt(),
+      result_->local_commit_counts_, result_->local_abort_counts_);
+#endif
+}
+#endif
 
-/**
- * @brief Transaction read function.
- * @param [in] key The key of key-value
- */
 Status TxExecutor::read(Storage s, std::string_view key, TupleBody** body) {
 #if ADD_ANALYSIS
   uint64_t start = rdtscp();
-#endif // ADD_ANALYSIS
+#endif
   TupleBody b;
   SetElement<Tuple>* e;
 
-  /**
-   * read-own-writes or re-read from local read set.
-   */
   e = searchReadSet(s, key);
   if (e) {
     *body = &(e->body_);
@@ -144,9 +202,6 @@ Status TxExecutor::read(Storage s, std::string_view key, TupleBody** body) {
     goto FINISH_READ;
   }
 
-  /**
-   * Search tuple from data structure.
-   */
   Tuple* tuple;
   tuple = Masstrees[get_storage(s)].get_value(key);
 #if ADD_ANALYSIS
@@ -155,6 +210,14 @@ Status TxExecutor::read(Storage s, std::string_view key, TupleBody** body) {
   if (tuple == nullptr) return Status::WARN_NOT_FOUND;
 
   read_internal(s, key, tuple);
+#if SS2PL_LOCK_IMPL == 1
+  if (status_ == TransactionStatus::aborted) {
+#if ADD_ANALYSIS
+    result_->local_read_latency_ += rdtscp() - start;
+#endif
+    return Status::ERROR_LOCK_FAILED;
+  }
+#endif
   *body = &(read_set_.back().body_);
 
 FINISH_READ:
@@ -169,23 +232,52 @@ void TxExecutor::read_internal(Storage s, std::string_view key, Tuple* tuple) {
 
   if (reconnoitering_) goto FINISH_READ_LOCK;
 
-#ifdef DLR0
-  /**
-   * Acquire lock with wait.
-   */
+#if SS2PL_LOCK_IMPL == 1
+  if (hasReadLock(&tuple->lock_) || hasWriteLock(&tuple->lock_)) {
+    goto FINISH_READ_LOCK;
+  }
+
+#if SS2PL_WFG_DIAG
+  publish_wait(*this, &tuple->lock_, SS2PLWfgMode::read);
+#endif
+  if (tuple->lock_.r_lock(control_)) {
+    r_lock_list_.emplace_back(&tuple->lock_);
+#if SS2PL_WFG_DIAG
+    publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::read);
+#endif
+    if (control_.state() == SS2PLAttemptState::wounded) {
+      status_ = TransactionStatus::aborted;
+      goto FINISH_READ;
+    }
+  } else {
+#if SS2PL_WFG_DIAG
+    publish_failed(*this);
+#endif
+    status_ = TransactionStatus::aborted;
+    goto FINISH_READ;
+  }
+#else
+#if SS2PL_DLR == 0
   tuple->lock_.r_lock();
   r_lock_list_.emplace_back(&tuple->lock_);
-#elif defined(DLR1)
+#if SS2PL_WFG_DIAG
+  publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::read);
+#endif
+#elif SS2PL_DLR == 1
   if (tuple->lock_.r_trylock()) {
     r_lock_list_.emplace_back(&tuple->lock_);
+#if SS2PL_WFG_DIAG
+    publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::read);
+#endif
   } else {
-    /**
-     * No-wait and abort.
-     */
+#if SS2PL_WFG_DIAG
+    publish_failed(*this);
+#endif
     this->status_ = TransactionStatus::aborted;
     goto FINISH_READ;
   }
 #endif
+#endif
 
 FINISH_READ_LOCK:
   body = TupleBody(tuple->body_.get_key(), tuple->body_.get_val(),
@@ -244,11 +336,7 @@ Status TxExecutor::scan(const Storage s, std::string_view left_key,
   return Status::OK;
 }
 
-/**
- * @brief transaction write operation
- * @param [in] key The key of key-value
- * @return void
- */
+#if SS2PL_LOCK_IMPL == 0 && !SS2PL_WFG_DIAG && (!defined(SS2PL_WORKLOAD_YCSB) || !SS2PL_WORKLOAD_YCSB)
 Status TxExecutor::update(Storage s, std::string_view key, TupleBody&& body) {
 #if ADD_ANALYSIS
   uint64_t start = rdtscp();
@@ -260,13 +348,13 @@ Status TxExecutor::update(Storage s, std::string_view key, TupleBody&& body) {
   for (auto rItr = read_set_.begin(); rItr != read_set_.end(); ++rItr) {
     if ((*rItr).storage_ != s) continue;
     if ((*rItr).key_ == key) { // hit
-#if DLR0
+#if SS2PL_DLR == 0
       // Workaround for handling static BoMB properly
       if (!(*rItr).rcdptr_->lock_.tryupgrade()) {
         this->status_ = TransactionStatus::aborted;
         goto FINISH_WRITE;
       }
-#elif defined(DLR1)
+#elif SS2PL_DLR == 1
       if (!(*rItr).rcdptr_->lock_.tryupgrade()) {
         this->status_ = TransactionStatus::aborted;
         goto FINISH_WRITE;
@@ -306,12 +394,12 @@ Status TxExecutor::update(Storage s, std::string_view key, TupleBody&& body) {
 #endif
   if (tuple == nullptr) return Status::WARN_NOT_FOUND;
 
-#if DLR0
+#if SS2PL_DLR == 0
   /**
    * Lock with wait.
    */
   tuple->lock_.w_lock();
-#elif defined(DLR1)
+#elif SS2PL_DLR == 1
   if (!tuple->lock_.w_trylock()) {
     /**
      * No-wait and abort.
@@ -333,6 +421,166 @@ FINISH_WRITE:
 #endif // ADD_ANALYSIS
   return Status::OK;
 }
+#else
+Status TxExecutor::update(Storage s, std::string_view key, TupleBody&& body) {
+#if ADD_ANALYSIS
+  uint64_t start = rdtscp();
+#endif
+  Status return_status = Status::OK;
+
+  if (searchWriteSet(s, key)) goto FINISH_WRITE;
+
+  for (auto rItr = read_set_.begin(); rItr != read_set_.end(); ++rItr) {
+    if ((*rItr).storage_ != s) continue;
+    if ((*rItr).key_ != key) continue;
+
+#if SS2PL_LOCK_IMPL == 0
+#if SS2PL_DLR == 0
+    if (!(*rItr).rcdptr_->lock_.tryupgrade()) {
+      this->status_ = TransactionStatus::aborted;
+      goto FINISH_WRITE;
+    }
+#elif SS2PL_DLR == 1
+    if (!(*rItr).rcdptr_->lock_.tryupgrade()) {
+      this->status_ = TransactionStatus::aborted;
+      goto FINISH_WRITE;
+    }
+#endif
+
+    for (auto lItr = r_lock_list_.begin(); lItr != r_lock_list_.end();
+         ++lItr) {
+      if (*lItr == &((*rItr).rcdptr_->lock_)) {
+        write_set_.emplace_back(s, key, (*rItr).rcdptr_, std::move(body),
+                                OpType::UPDATE);
+        w_lock_list_.emplace_back(&(*rItr).rcdptr_->lock_);
+        r_lock_list_.erase(lItr);
+        break;
+      }
+    }
+#else
+    ReaderWriteLock* lock = &(*rItr).rcdptr_->lock_;
+    if (hasWriteLock(lock)) {
+      write_set_.emplace_back(s, key, (*rItr).rcdptr_, std::move(body),
+                              OpType::UPDATE);
+      goto FINISH_WRITE;
+    }
+    if (!hasReadLock(lock)) {
+      status_ = TransactionStatus::aborted;
+      return_status = Status::ERROR_LOCK_FAILED;
+      goto FINISH_WRITE;
+    }
+#if SS2PL_WFG_DIAG
+    publish_wait(*this, lock, SS2PLWfgMode::write);
+#endif
+    if (!lock->upgrade(control_)) {
+#if SS2PL_WFG_DIAG
+      publish_failed(*this);
+#endif
+      status_ = TransactionStatus::aborted;
+      return_status = Status::ERROR_LOCK_FAILED;
+      goto FINISH_WRITE;
+    }
+    for (auto lItr = r_lock_list_.begin(); lItr != r_lock_list_.end();
+         ++lItr) {
+      if (*lItr == lock) {
+        r_lock_list_.erase(lItr);
+        break;
+      }
+    }
+    w_lock_list_.emplace_back(lock);
+    write_set_.emplace_back(s, key, (*rItr).rcdptr_, std::move(body),
+                            OpType::UPDATE);
+#if SS2PL_WFG_DIAG
+    publish_acquired(*this, lock, SS2PLWfgMode::write, true);
+#endif
+    if (control_.state() == SS2PLAttemptState::wounded) {
+      status_ = TransactionStatus::aborted;
+      return_status = Status::ERROR_LOCK_FAILED;
+    }
+#endif
+    goto FINISH_WRITE;
+  }
+
+  {
+    Tuple* tuple = Masstrees[get_storage(s)].get_value(key);
+#if ADD_ANALYSIS
+    ++result_->local_tree_traversal_;
+#endif
+    if (tuple == nullptr) return Status::WARN_NOT_FOUND;
+
+#if SS2PL_LOCK_IMPL == 1
+    if (hasWriteLock(&tuple->lock_)) {
+      write_set_.emplace_back(s, key, tuple, std::move(body), OpType::UPDATE);
+      goto FINISH_WRITE;
+    }
+    if (hasReadLock(&tuple->lock_)) {
+#if SS2PL_WFG_DIAG
+      publish_wait(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+      if (!tuple->lock_.upgrade(control_)) {
+#if SS2PL_WFG_DIAG
+        publish_failed(*this);
+#endif
+        status_ = TransactionStatus::aborted;
+        return_status = Status::ERROR_LOCK_FAILED;
+        goto FINISH_WRITE;
+      }
+      for (auto it = r_lock_list_.begin(); it != r_lock_list_.end(); ++it) {
+        if (*it == &tuple->lock_) {
+          r_lock_list_.erase(it);
+          break;
+        }
+      }
+      w_lock_list_.emplace_back(&tuple->lock_);
+#if SS2PL_WFG_DIAG
+      publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::write, true);
+#endif
+    } else {
+#if SS2PL_WFG_DIAG
+      publish_wait(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+      if (!tuple->lock_.w_lock(control_)) {
+#if SS2PL_WFG_DIAG
+        publish_failed(*this);
+#endif
+        status_ = TransactionStatus::aborted;
+        return_status = Status::ERROR_LOCK_FAILED;
+        goto FINISH_WRITE;
+      }
+      w_lock_list_.emplace_back(&tuple->lock_);
+#if SS2PL_WFG_DIAG
+      publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+    }
+    write_set_.emplace_back(s, key, tuple, std::move(body), OpType::UPDATE);
+    if (control_.state() == SS2PLAttemptState::wounded) {
+      status_ = TransactionStatus::aborted;
+      return_status = Status::ERROR_LOCK_FAILED;
+    }
+#else
+#if SS2PL_DLR == 0
+    tuple->lock_.w_lock();
+#elif SS2PL_DLR == 1
+    if (!tuple->lock_.w_trylock()) {
+      this->status_ = TransactionStatus::aborted;
+      goto FINISH_WRITE;
+    }
+#endif
+    w_lock_list_.emplace_back(&tuple->lock_);
+    write_set_.emplace_back(s, key, tuple, std::move(body), OpType::UPDATE);
+#if SS2PL_WFG_DIAG
+    publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+#endif
+  }
+
+FINISH_WRITE:
+#if ADD_ANALYSIS
+  result_->local_write_latency_ += rdtscp() - start;
+#endif
+  return return_status;
+}
+#endif
 
 Status TxExecutor::insert(Storage s, std::string_view key, TupleBody&& body) {
 #if ADD_ANALYSIS
@@ -345,19 +593,55 @@ Status TxExecutor::insert(Storage s, std::string_view key, TupleBody&& body) {
 #if ADD_ANALYSIS
   ++result_->local_tree_traversal_;
 #endif
   if (tuple != nullptr) { return Status::WARN_ALREADY_EXISTS; }
 
   tuple = new Tuple();
+#if SS2PL_LOCK_IMPL == 0
   tuple->init(std::move(body));
+#else
+  tuple->init(static_cast<std::size_t>(thid_), std::move(body), nullptr);
+#if SS2PL_WFG_DIAG
+  publish_wait(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+  if (!tuple->lock_.w_lock(control_)) {
+#if SS2PL_WFG_DIAG
+    publish_failed(*this);
+#endif
+    delete tuple;
+    status_ = TransactionStatus::aborted;
+    return Status::ERROR_LOCK_FAILED;
+  }
+  w_lock_list_.emplace_back(&tuple->lock_);
+#if SS2PL_WFG_DIAG
+  publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+#endif
 
   Status stat = Masstrees[get_storage(s)].insert_value(key, tuple);
   if (stat == Status::WARN_ALREADY_EXISTS) {
+#if SS2PL_LOCK_IMPL == 1
+    w_lock_list_.pop_back();
+#if SS2PL_WFG_DIAG
+    publish_released(*this, &tuple->lock_);
+#endif
+    tuple->lock_.w_unlock(control_);
+#endif
     delete tuple;
     return stat;
   }
 
   write_set_.emplace_back(s, key, tuple, OpType::INSERT);
+#if SS2PL_LOCK_IMPL == 0
   w_lock_list_.emplace_back(&tuple->lock_);
+#if SS2PL_WFG_DIAG
+  publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+#else
+  if (control_.state() == SS2PLAttemptState::wounded) {
+    status_ = TransactionStatus::aborted;
+    return Status::ERROR_LOCK_FAILED;
+  }
+#endif
 
 #if ADD_ANALYSIS
   result_->local_write_latency_ += rdtscp() - start;
@@ -365,6 +649,7 @@ Status TxExecutor::insert(Storage s, std::string_view key, TupleBody&& body) {
   return Status::OK;
 }
 
+#if SS2PL_LOCK_IMPL == 0 && !SS2PL_WFG_DIAG && (!defined(SS2PL_WORKLOAD_YCSB) || !SS2PL_WORKLOAD_YCSB)
 Status TxExecutor::delete_record(Storage s, std::string_view key) {
 #if ADD_ANALYSIS
   std::uint64_t start = rdtscp();
@@ -389,7 +674,82 @@ Status TxExecutor::delete_record(Storage s, std::string_view key) {
 #endif
   return Status::OK;
 }
+#else
+Status TxExecutor::delete_record(Storage s, std::string_view key) {
+#if ADD_ANALYSIS
+  std::uint64_t start = rdtscp();
+#endif
 
+  for (auto itr = write_set_.begin(); itr != write_set_.end(); ++itr) {
+    if ((*itr).storage_ != s) continue;
+    if ((*itr).key_ == key) {
+      write_set_.erase(itr);
+      break;
+    }
+  }
+
+  Tuple* tuple = Masstrees[get_storage(s)].get_value(key);
+#if ADD_ANALYSIS
+  ++result_->local_tree_traversal_;
+#endif
+  if (tuple == nullptr) return Status::WARN_NOT_FOUND;
+
+#if SS2PL_LOCK_IMPL == 1
+  if (!hasWriteLock(&tuple->lock_)) {
+    if (hasReadLock(&tuple->lock_)) {
+#if SS2PL_WFG_DIAG
+      publish_wait(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+      if (!tuple->lock_.upgrade(control_)) {
+#if SS2PL_WFG_DIAG
+        publish_failed(*this);
+#endif
+        status_ = TransactionStatus::aborted;
+        return Status::ERROR_LOCK_FAILED;
+      }
+      for (auto it = r_lock_list_.begin(); it != r_lock_list_.end(); ++it) {
+        if (*it == &tuple->lock_) {
+          r_lock_list_.erase(it);
+          break;
+        }
+      }
+      w_lock_list_.emplace_back(&tuple->lock_);
+#if SS2PL_WFG_DIAG
+      publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::write, true);
+#endif
+    } else {
+#if SS2PL_WFG_DIAG
+      publish_wait(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+      if (!tuple->lock_.w_lock(control_)) {
+#if SS2PL_WFG_DIAG
+        publish_failed(*this);
+#endif
+        status_ = TransactionStatus::aborted;
+        return Status::ERROR_LOCK_FAILED;
+      }
+      w_lock_list_.emplace_back(&tuple->lock_);
+#if SS2PL_WFG_DIAG
+      publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+    }
+  }
+  if (control_.state() == SS2PLAttemptState::wounded) {
+    status_ = TransactionStatus::aborted;
+    return Status::ERROR_LOCK_FAILED;
+  }
+#endif
+
+  write_set_.emplace_back(s, key, tuple, OpType::DELETE);
+
+#if ADD_ANALYSIS
+  result_->local_write_latency_ += rdtscp() - start;
+#endif
+  return Status::OK;
+}
+#endif
+
+#if SS2PL_LOCK_IMPL == 0 && !SS2PL_WFG_DIAG && (!defined(SS2PL_WORKLOAD_YCSB) || !SS2PL_WORKLOAD_YCSB)
 Status TxExecutor::read_lock(Storage s, std::string_view key) {
   Tuple* tuple;
   tuple = Masstrees[get_storage(s)].get_value(key);
@@ -408,19 +768,74 @@ Status TxExecutor::read_lock(Storage s, std::string_view key) {
     if (w_lock == &tuple->lock_) { return Status::OK; }
   }
 
-#ifdef DLR0
+#if SS2PL_DLR == 0
+  tuple->lock_.r_lock();
+#elif SS2PL_DLR == 1
+  if (!tuple->lock_.r_trylock()) {
+    this->status_ = TransactionStatus::aborted;
+    return Status::ERROR_LOCK_FAILED;
+  }
+#endif
+  r_lock_list_.emplace_back(&tuple->lock_);
+
+  return Status::OK;
+}
+#else
+Status TxExecutor::read_lock(Storage s, std::string_view key) {
+  Tuple* tuple = Masstrees[get_storage(s)].get_value(key);
+#if ADD_ANALYSIS
+  ++result_->local_tree_traversal_;
+#endif
+  if (reconnoitering_) return Status::OK;
+
+  if (tuple == nullptr) return Status::WARN_NOT_FOUND;
+
+#if SS2PL_LOCK_IMPL == 1
+  for (auto& r_lock : r_lock_list_) {
+    if (r_lock == &tuple->lock_) return Status::OK;
+  }
+  for (auto& w_lock : w_lock_list_) {
+    if (w_lock == &tuple->lock_) return Status::OK;
+  }
+
+#if SS2PL_WFG_DIAG
+  publish_wait(*this, &tuple->lock_, SS2PLWfgMode::read);
+#endif
+  if (!tuple->lock_.r_lock(control_)) {
+#if SS2PL_WFG_DIAG
+    publish_failed(*this);
+#endif
+    status_ = TransactionStatus::aborted;
+    return Status::ERROR_LOCK_FAILED;
+  }
+  r_lock_list_.emplace_back(&tuple->lock_);
+#if SS2PL_WFG_DIAG
+  publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::read);
+#endif
+  if (control_.state() == SS2PLAttemptState::wounded) {
+    status_ = TransactionStatus::aborted;
+    return Status::ERROR_LOCK_FAILED;
+  }
+#else
+#if SS2PL_DLR == 0
   tuple->lock_.r_lock();
-#elif defined(DLR1)
+#elif SS2PL_DLR == 1
   if (!tuple->lock_.r_trylock()) {
     this->status_ = TransactionStatus::aborted;
     return Status::ERROR_LOCK_FAILED;
   }
 #endif
   r_lock_list_.emplace_back(&tuple->lock_);
+#if SS2PL_WFG_DIAG
+  publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::read);
+#endif
+#endif
 
   return Status::OK;
 }
+#endif
 
+#if SS2PL_LOCK_IMPL == 0 && !SS2PL_WFG_DIAG && (!defined(SS2PL_WORKLOAD_YCSB) || !SS2PL_WORKLOAD_YCSB)
 Status TxExecutor::write_lock(Storage s, std::string_view key) {
   Tuple* tuple;
   tuple = Masstrees[get_storage(s)].get_value(key);
@@ -433,9 +848,9 @@ Status TxExecutor::write_lock(Storage s, std::string_view key) {
     if (w_lock == &tuple->lock_) { return Status::OK; }
   }
 
-#if DLR0
+#if SS2PL_DLR == 0
   tuple->lock_.w_lock();
-#elif defined(DLR1)
+#elif SS2PL_DLR == 1
   if (!tuple->lock_.w_trylock()) {
     this->status_ = TransactionStatus::aborted;
     return Status::ERROR_LOCK_FAILED;
@@ -445,12 +860,80 @@ Status TxExecutor::write_lock(Storage s, std::string_view key) {
 
   return Status::OK;
 }
+#else
+Status TxExecutor::write_lock(Storage s, std::string_view key) {
+  Tuple* tuple = Masstrees[get_storage(s)].get_value(key);
+#if ADD_ANALYSIS
+  ++result_->local_tree_traversal_;
+#endif
+  if (tuple == nullptr) return Status::WARN_NOT_FOUND;
 
+#if SS2PL_LOCK_IMPL == 1
+  for (auto& w_lock : w_lock_list_) {
+    if (w_lock == &tuple->lock_) return Status::OK;
+  }
 
-/**
- * @brief unlock and clean-up local lock set.
- * @return void
- */
+  if (hasReadLock(&tuple->lock_)) {
+#if SS2PL_WFG_DIAG
+    publish_wait(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+    if (!tuple->lock_.upgrade(control_)) {
+#if SS2PL_WFG_DIAG
+      publish_failed(*this);
+#endif
+      status_ = TransactionStatus::aborted;
+      return Status::ERROR_LOCK_FAILED;
+    }
+    for (auto it = r_lock_list_.begin(); it != r_lock_list_.end(); ++it) {
+      if (*it == &tuple->lock_) {
+        r_lock_list_.erase(it);
+        break;
+      }
+    }
+    w_lock_list_.emplace_back(&tuple->lock_);
+#if SS2PL_WFG_DIAG
+    publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::write, true);
+#endif
+  } else {
+#if SS2PL_WFG_DIAG
+    publish_wait(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+    if (!tuple->lock_.w_lock(control_)) {
+#if SS2PL_WFG_DIAG
+      publish_failed(*this);
+#endif
+      status_ = TransactionStatus::aborted;
+      return Status::ERROR_LOCK_FAILED;
+    }
+    w_lock_list_.emplace_back(&tuple->lock_);
+#if SS2PL_WFG_DIAG
+    publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+  }
+  if (control_.state() == SS2PLAttemptState::wounded) {
+    status_ = TransactionStatus::aborted;
+    return Status::ERROR_LOCK_FAILED;
+  }
+#else
+#if SS2PL_DLR == 0
+  tuple->lock_.w_lock();
+#elif SS2PL_DLR == 1
+  if (!tuple->lock_.w_trylock()) {
+    this->status_ = TransactionStatus::aborted;
+    return Status::ERROR_LOCK_FAILED;
+  }
+#endif
+  w_lock_list_.emplace_back(&tuple->lock_);
+#if SS2PL_WFG_DIAG
+  publish_acquired(*this, &tuple->lock_, SS2PLWfgMode::write);
+#endif
+#endif
+
+  return Status::OK;
+}
+#endif
+
+#if SS2PL_LOCK_IMPL == 0 && !SS2PL_WFG_DIAG && (!defined(SS2PL_WORKLOAD_YCSB) || !SS2PL_WORKLOAD_YCSB)
 void TxExecutor::unlockList() {
   for (auto itr = r_lock_list_.begin(); itr != r_lock_list_.end(); ++itr)
     (*itr)->r_unlock();
@@ -464,14 +947,52 @@ void TxExecutor::unlockList() {
   r_lock_list_.clear();
   w_lock_list_.clear();
 }
+#else
+void TxExecutor::unlockList() {
+  for (auto itr = r_lock_list_.begin(); itr != r_lock_list_.end(); ++itr) {
+#if SS2PL_WFG_DIAG
+    publish_released(*this, *itr);
+#endif
+#if SS2PL_LOCK_IMPL == 1
+    (*itr)->r_unlock(control_);
+#else
+    (*itr)->r_unlock();
+#endif
+  }
+
+  for (auto itr = w_lock_list_.begin(); itr != w_lock_list_.end(); ++itr) {
+#if SS2PL_WFG_DIAG
+    publish_released(*this, *itr);
+#endif
+#if SS2PL_LOCK_IMPL == 1
+    (*itr)->w_unlock(control_);
+#else
+    (*itr)->w_unlock();
+#endif
+  }
+
+  r_lock_list_.clear();
+  w_lock_list_.clear();
+}
+#endif
 
 void TxExecutor::reconnoiter_begin() { reconnoitering_ = true; }
 
 void TxExecutor::reconnoiter_end() {
+#if SS2PL_LOCK_IMPL == 0
   unlockList();
   read_set_.clear();
   reconnoitering_ = false;
   begin();
+#else
+  read_set_.clear();
+  reconnoitering_ = false;
+  if (!r_lock_list_.empty() || !w_lock_list_.empty()) {
+    status_ = TransactionStatus::aborted;
+    return;
+  }
+  if (control_.state() == SS2PLAttemptState::inactive) begin();
+#endif
 }
 
 bool TxExecutor::isLeader() { return this->thid_ == 0; }
diff --git a/cc/ss2pl/util.cc b/cc/ss2pl/util.cc
index a2b20f4e..1ab2327b 100644
--- a/cc/ss2pl/util.cc
+++ b/cc/ss2pl/util.cc
@@ -24,11 +24,24 @@
 #include "include/common.hh"
 #include "include/tuple.hh"
 #include "include/util.hh"
+#if SS2PL_WORKLOAD_YCSB
+#include "../../include/ycsb.hh"
+#endif
 
 void chkArg() {
   displayParameter();
 
-  if (FLAGS_rratio > 100) { ERR; }
+#if SS2PL_WORKLOAD_YCSB
+  if (FLAGS_ycsb_rratio > 100) { ERR; }
+#endif
+
+#if SS2PL_LOCK_IMPL == 1 || SS2PL_WFG_DIAG
+  if (FLAGS_thread_num > 64) { ERR; }
+#endif
+
+#if SS2PL_WFG_DIAG
+  if (FLAGS_ss2pl_wfg_output.empty()) { ERR; }
+#endif
 
   TotalThreadNum = FLAGS_thread_num;
 
@@ -43,13 +56,7 @@ void displayDB() {}
 void displayParameter() {
   cout << "#FLAGS_clocks_per_us:\t" << FLAGS_clocks_per_us << endl;
   cout << "#FLAGS_extime:\t\t" << FLAGS_extime << endl;
-  cout << "#FLAGS_max_ope:\t\t" << FLAGS_max_ope << endl;
-  cout << "#FLAGS_rmw:\t\t" << FLAGS_rmw << endl;
-  cout << "#FLAGS_rratio:\t\t" << FLAGS_rratio << endl;
   cout << "#FLAGS_thread_num:\t" << FLAGS_thread_num << endl;
-  cout << "#FLAGS_tuple_num:\t" << FLAGS_tuple_num << endl;
-  cout << "#FLAGS_ycsb:\t\t" << FLAGS_ycsb << endl;
-  cout << "#FLAGS_zipf_skew:\t" << FLAGS_zipf_skew << endl;
 }
 
 void partTableInit([[maybe_unused]] size_t thid,
@@ -65,7 +72,13 @@ void ShowOptParameters() {
        << ": DLR0 "
 #elif defined DLR1
        << ": DLR1 "
+#elif defined DLR2
+       << ": DLR2 "
 #endif
+       << ": SS2PL_LOCK_IMPL " << SS2PL_LOCK_IMPL
+       << ": SS2PL_LOCK_KIND " << SS2PL_LOCK_KIND
+       << ": SS2PL_DLR " << SS2PL_DLR
+       << ": SS2PL_WFG_DIAG " << SS2PL_WFG_DIAG
        << ": MASSTREE_USE " << MASSTREE_USE << ": KEY_SIZE " << KEY_SIZE
        << ": KEY_SORT " << KEY_SORT << ": VAL_SIZE " << VAL_SIZE << endl;
 }
diff --git a/cmake/Options.cmake b/cmake/Options.cmake
index b9a3c740..950ba064 100644
--- a/cmake/Options.cmake
+++ b/cmake/Options.cmake
@@ -48,6 +48,11 @@ set(CCBENCH_WAL                           0 CACHE STRING "silo")
 set(CCBENCH_TEMPERATURE_RESET_OPT         1 CACHE STRING "mocc")
 set(CCBENCH_WORKER1_INSERT_DELAY_RPHASE   0 CACHE STRING "cicada")
 
+set(CCBENCH_SS2PL_LOCK_IMPL  0 CACHE STRING "ss2pl: 0=stock, 1=study lock")
+set(CCBENCH_SS2PL_LOCK_KIND  1 CACHE STRING "ss2pl study lock: 0=exclusive, 1=reader-writer")
+set(CCBENCH_SS2PL_DLR        1 CACHE STRING "ss2pl: 0=wait, 1=no-wait, 2=wound-wait")
+set(CCBENCH_SS2PL_WFG_DIAG   0 CACHE STRING "ss2pl wait-for graph diagnostics")
+
 # Cicada and Oze share many flags but disagree on this one's default.
 # Keep two separate cache entries; protocols pick the one they want.
 set(CCBENCH_INLINE_VERSION_OPT_CICADA     0 CACHE STRING "cicada")
diff --git a/include/rwlock.hh b/include/rwlock.hh
index 856119f3..8eb7249c 100644
--- a/include/rwlock.hh
+++ b/include/rwlock.hh
@@ -5,6 +5,7 @@
 
 using namespace std;
 
+#if !defined(SS2PL_LOCK_IMPL) || SS2PL_LOCK_IMPL == 0
 class ReaderWriteLock {
 public:
   std::atomic<int> counter;
@@ -107,3 +108,4 @@ public:
     }
   }
 };
+#endif
diff --git a/include/ycsb.hh b/include/ycsb.hh
index c809adb6..bc10d947 100644
--- a/include/ycsb.hh
+++ b/include/ycsb.hh
@@ -148,6 +148,9 @@ public:
 
       if (tx.status_ == TransactionStatus::aborted) {
         tx.abort();
+#if defined(SS2PL_WORKLOAD_YCSB) && SS2PL_WORKLOAD_YCSB
+        if (loadAcquire(tx.quit_)) return;
+#endif
         ++tx.result_->local_abort_counts_;
 #if ADD_ANALYSIS
         ++tx.result_->local_early_aborts_;
@@ -160,6 +163,9 @@ public:
 
     if (!tx.commit()) {
       tx.abort();
+#if defined(SS2PL_WORKLOAD_YCSB) && SS2PL_WORKLOAD_YCSB
+      if (loadAcquire(tx.quit_)) return;
+#endif
       ++tx.result_->local_abort_counts_;
       goto RETRY;
     }
diff --git a/cc/ss2pl/include/ss2pl_lock.hh b/cc/ss2pl/include/ss2pl_lock.hh
new file mode 100644
--- /dev/null
+++ b/cc/ss2pl/include/ss2pl_lock.hh
@@ -0,0 +1,42 @@
+#ifndef CCBENCH_SS2PL_LOCK_HH_INCLUDED
+#define CCBENCH_SS2PL_LOCK_HH_INCLUDED
+
+#ifndef SS2PL_LOCK_IMPL
+#define SS2PL_LOCK_IMPL 0
+#endif
+
+#ifndef SS2PL_LOCK_KIND
+#define SS2PL_LOCK_KIND 1
+#endif
+
+#ifndef SS2PL_DLR
+#define SS2PL_DLR 1
+#endif
+
+#ifndef SS2PL_WFG_DIAG
+#define SS2PL_WFG_DIAG 0
+#endif
+
+#if SS2PL_LOCK_IMPL < 0 || SS2PL_LOCK_IMPL > 1
+#error "SS2PL_LOCK_IMPL must be 0 or 1"
+#endif
+#if SS2PL_LOCK_KIND < 0 || SS2PL_LOCK_KIND > 1
+#error "SS2PL_LOCK_KIND must be 0 or 1"
+#endif
+#if SS2PL_DLR < 0 || SS2PL_DLR > 2
+#error "SS2PL_DLR must be 0, 1, or 2"
+#endif
+#if SS2PL_WFG_DIAG < 0 || SS2PL_WFG_DIAG > 1
+#error "SS2PL_WFG_DIAG must be 0 or 1"
+#endif
+
+#if SS2PL_LOCK_IMPL == 0 && SS2PL_DLR == 2
+#error "SS2PL_DLR=2 with stock lock is outside this prototype"
+#endif
+
+#include "../../../include/rwlock.hh"
+#include "ss2pl_study_lock.hh"
+#if SS2PL_LOCK_IMPL == 1
+using ReaderWriteLock = SS2PLStudyLockT<SS2PL_LOCK_KIND, SS2PL_DLR>;
+#endif
+#endif
diff --git a/cc/ss2pl/include/ss2pl_study_lock.hh b/cc/ss2pl/include/ss2pl_study_lock.hh
new file mode 100644
--- /dev/null
+++ b/cc/ss2pl/include/ss2pl_study_lock.hh
@@ -0,0 +1,500 @@
+#ifndef CCBENCH_SS2PL_STUDY_LOCK_HH_INCLUDED
+#define CCBENCH_SS2PL_STUDY_LOCK_HH_INCLUDED
+
+#include <array>
+#include <atomic>
+#include <cstdint>
+#include <limits>
+#include <thread>
+#include <type_traits>
+
+#include <xmmintrin.h>
+
+#include "../../../include/atomic_wrapper.hh"
+#include "../../../include/cache_line_size.hh"
+
+#if SS2PL_LOCK_IMPL == 1
+enum class SS2PLAttemptState : std::uint8_t {
+  inactive = 0,
+  inflight = 1,
+  wounded = 2,
+  committing = 3,
+};
+
+class alignas(CACHE_LINE_SIZE) SS2PLTxControl {
+public:
+  static constexpr std::uint64_t kStateBits = 2;
+  static constexpr std::uint64_t kStateMask = 3;
+
+  void initialize(std::uint32_t thid, const bool& quit) {
+    thid_ = thid;
+    quit_ = &quit;
+    logical_ts_.store(0, std::memory_order_release);
+    attempt_state_.store(pack(0, SS2PLAttemptState::inactive),
+                         std::memory_order_release);
+    lock_release_generation_.store(0, std::memory_order_release);
+  }
+
+  void begin_attempt();
+
+  void finish_abort() {
+    const std::uint64_t current =
+        attempt_state_.load(std::memory_order_acquire);
+    attempt_state_.store(pack(unpack_attempt(current),
+                              SS2PLAttemptState::inactive),
+                         std::memory_order_release);
+  }
+
+  bool prepare_commit() {
+    const std::uint64_t current_attempt = attempt();
+    std::uint64_t expected =
+        pack(current_attempt, SS2PLAttemptState::inflight);
+    return attempt_state_.compare_exchange_strong(
+        expected, pack(current_attempt, SS2PLAttemptState::committing),
+        std::memory_order_acq_rel, std::memory_order_acquire);
+  }
+
+  void finish_commit() {
+    const std::uint64_t current =
+        attempt_state_.load(std::memory_order_acquire);
+    attempt_state_.store(pack(unpack_attempt(current),
+                              SS2PLAttemptState::inactive),
+                         std::memory_order_release);
+    logical_ts_.store(0, std::memory_order_release);
+  }
+
+  [[nodiscard]] bool wound_exact(std::uint64_t victim_attempt,
+                                 std::uint64_t requester_ts,
+                                 std::uint32_t requester_thid) {
+    if (requester_thid == thid_) return false;
+    if (requester_ts >= logical_ts()) return false;
+
+    std::uint64_t expected =
+        pack(victim_attempt, SS2PLAttemptState::inflight);
+    if (attempt_state_.load(std::memory_order_acquire) != expected) return false;
+    return attempt_state_.compare_exchange_strong(
+        expected, pack(victim_attempt, SS2PLAttemptState::wounded),
+        std::memory_order_acq_rel, std::memory_order_acquire);
+  }
+
+  [[nodiscard]] std::uint32_t thid() const { return thid_; }
+
+  [[nodiscard]] std::uint64_t logical_ts() const {
+    return logical_ts_.load(std::memory_order_acquire);
+  }
+
+  [[nodiscard]] std::uint64_t attempt() const {
+    return unpack_attempt(attempt_state_.load(std::memory_order_acquire));
+  }
+
+  [[nodiscard]] SS2PLAttemptState state() const {
+    return unpack_state(attempt_state_.load(std::memory_order_acquire));
+  }
+
+  [[nodiscard]] bool may_request_lock() const {
+    return state() == SS2PLAttemptState::inflight && !quit_requested();
+  }
+
+  [[nodiscard]] bool quit_requested() const {
+    return quit_ != nullptr && loadAcquire(*quit_);
+  }
+
+  void note_lock_release() {
+    lock_release_generation_.fetch_add(1, std::memory_order_release);
+  }
+
+  [[nodiscard]] std::uint64_t lock_release_generation() const {
+    return lock_release_generation_.load(std::memory_order_acquire);
+  }
+
+  [[nodiscard]] static constexpr std::uint64_t pack(
+      std::uint64_t attempt, SS2PLAttemptState state) {
+    return (attempt << kStateBits) | static_cast<std::uint64_t>(state);
+  }
+
+  [[nodiscard]] static constexpr std::uint64_t unpack_attempt(
+      std::uint64_t value) {
+    return value >> kStateBits;
+  }
+
+  [[nodiscard]] static constexpr SS2PLAttemptState unpack_state(
+      std::uint64_t value) {
+    return static_cast<SS2PLAttemptState>(value & kStateMask);
+  }
+
+private:
+  std::uint32_t thid_ = 0;
+  const bool* quit_ = nullptr;
+  std::atomic<std::uint64_t> logical_ts_{0};
+  std::atomic<std::uint64_t> attempt_state_{
+      pack(0, SS2PLAttemptState::inactive)};
+  std::atomic<std::uint64_t> lock_release_generation_{0};
+};
+
+static_assert(alignof(SS2PLTxControl) == CACHE_LINE_SIZE);
+static_assert(sizeof(SS2PLTxControl) % CACHE_LINE_SIZE == 0);
+
+inline std::atomic<std::uint64_t> SS2PLGlobalTimestamp{1};
+inline std::array<SS2PLTxControl, 64> SS2PLControls;
+
+inline SS2PLTxControl& ss2pl_control(std::uint32_t thid) {
+  return SS2PLControls[thid];
+}
+
+inline void SS2PLTxControl::begin_attempt() {
+  if (logical_ts_.load(std::memory_order_acquire) == 0) {
+    logical_ts_.store(
+        SS2PLGlobalTimestamp.fetch_add(1, std::memory_order_acq_rel),
+        std::memory_order_release);
+  }
+
+  const std::uint64_t current =
+      attempt_state_.load(std::memory_order_acquire);
+  const std::uint64_t next_attempt = unpack_attempt(current) + 1;
+  attempt_state_.store(pack(next_attempt, SS2PLAttemptState::inflight),
+                       std::memory_order_release);
+}
+
+enum class SS2PLLockMode : std::uint8_t { read = 0, write = 1 };
+
+struct SS2PLEmptyWriterPriorityState {};
+
+struct SS2PLWriterPriorityState {
+  std::uint64_t waiting_writers = 0;
+};
+
+template <int LockKind, int DeadlockResolution>
+class SS2PLStudyLockT {
+  static_assert(LockKind == 0 || LockKind == 1);
+  static_assert(DeadlockResolution >= 0 && DeadlockResolution <= 2);
+
+  static constexpr bool kWriterPriority =
+      LockKind == 1 && DeadlockResolution == 2;
+  using WriterPriorityState =
+      std::conditional_t<kWriterPriority, SS2PLWriterPriorityState,
+                         SS2PLEmptyWriterPriorityState>;
+
+public:
+  SS2PLStudyLockT() = default;
+  SS2PLStudyLockT(const SS2PLStudyLockT&) = delete;
+  SS2PLStudyLockT& operator=(const SS2PLStudyLockT&) = delete;
+
+  void init() {
+    latch();
+    writer_ = kNoOwner;
+    readers_ = 0;
+    if constexpr (kWriterPriority) {
+      writer_priority_.waiting_writers = 0;
+    }
+    unlatch();
+  }
+
+#ifdef SS2PL_STUDY_LOCK_TESTING
+  void observe_contention_for_test(std::atomic<bool>& reached) {
+    contention_observer_ = &reached;
+  }
+#endif
+
+  [[nodiscard]] bool r_lock(SS2PLTxControl& requester) {
+    return acquire(requester, SS2PLLockMode::read, false, false);
+  }
+
+  [[nodiscard]] bool r_trylock(SS2PLTxControl& requester) {
+    return acquire(requester, SS2PLLockMode::read, true, false);
+  }
+
+  [[nodiscard]] bool w_lock(SS2PLTxControl& requester) {
+    return acquire(requester, SS2PLLockMode::write, false, false);
+  }
+
+  [[nodiscard]] bool w_trylock(SS2PLTxControl& requester) {
+    return acquire(requester, SS2PLLockMode::write, true, false);
+  }
+
+  [[nodiscard]] bool upgrade(SS2PLTxControl& requester) {
+    return acquire(requester, SS2PLLockMode::write, false, true);
+  }
+
+  [[nodiscard]] bool tryupgrade(SS2PLTxControl& requester) {
+    return acquire(requester, SS2PLLockMode::write, true, true);
+  }
+
+  void r_unlock(SS2PLTxControl& owner) {
+    latch();
+    [[maybe_unused]] bool released = false;
+    if constexpr (LockKind == 0) {
+      if (writer_ == owner.thid()) {
+        writer_ = kNoOwner;
+        released = true;
+      }
+    } else {
+      const std::uint64_t bit = owner_bit(owner.thid());
+      if ((readers_ & bit) != 0) {
+        readers_ &= ~bit;
+        released = true;
+      }
+    }
+    unlatch();
+    if constexpr (DeadlockResolution == 2) {
+      if (released) owner.note_lock_release();
+    }
+  }
+
+  void w_unlock(SS2PLTxControl& owner) {
+    latch();
+    [[maybe_unused]] bool released = false;
+    if (writer_ == owner.thid()) {
+      writer_ = kNoOwner;
+      released = true;
+    }
+    unlatch();
+    if constexpr (DeadlockResolution == 2) {
+      if (released) owner.note_lock_release();
+    }
+  }
+
+  [[nodiscard]] bool is_held_by(std::uint32_t thid) {
+    latch();
+    const bool held = writer_ == thid || (readers_ & owner_bit(thid)) != 0;
+    unlatch();
+    return held;
+  }
+
+  [[nodiscard]] bool is_unlocked_for_test() {
+    latch();
+    const bool unlocked = writer_ == kNoOwner && readers_ == 0;
+    unlatch();
+    return unlocked;
+  }
+
+private:
+  static constexpr std::uint32_t kNoOwner =
+      std::numeric_limits<std::uint32_t>::max();
+
+  [[nodiscard]] static constexpr std::uint64_t owner_bit(
+      std::uint32_t thid) {
+    return std::uint64_t{1} << thid;
+  }
+
+  void latch() {
+    while (latch_.test_and_set(std::memory_order_acquire)) _mm_pause();
+  }
+
+  void unlatch() { latch_.clear(std::memory_order_release); }
+
+  [[nodiscard]] std::uint32_t first_older_waiting_writer(
+      const SS2PLTxControl& requester) const {
+    std::uint64_t waiters =
+        writer_priority_.waiting_writers & ~owner_bit(requester.thid());
+    while (waiters != 0) {
+      const std::uint32_t thid =
+          static_cast<std::uint32_t>(__builtin_ctzll(waiters));
+      const SS2PLTxControl& writer = ss2pl_control(thid);
+      if (writer.may_request_lock() &&
+          requester.logical_ts() >= writer.logical_ts()) {
+        return thid;
+      }
+      waiters &= waiters - 1;
+    }
+    return kNoOwner;
+  }
+
+  [[nodiscard]] std::uint32_t first_blocker(std::uint32_t requester,
+                                            SS2PLLockMode mode,
+                                            bool upgrading) const {
+    if (writer_ != kNoOwner && writer_ != requester) return writer_;
+
+    const bool shared_read = LockKind == 1 && mode == SS2PLLockMode::read;
+    if (shared_read) return kNoOwner;
+
+    std::uint64_t blockers = readers_;
+    if (upgrading || (blockers & owner_bit(requester)) != 0) {
+      blockers &= ~owner_bit(requester);
+    }
+    if (blockers == 0) return kNoOwner;
+    return static_cast<std::uint32_t>(__builtin_ctzll(blockers));
+  }
+
+  void register_waiting_writer(std::uint32_t requester) {
+    const std::uint64_t bit = owner_bit(requester);
+    if ((writer_priority_.waiting_writers & bit) == 0) {
+      writer_priority_.waiting_writers |= bit;
+    }
+  }
+
+  void unregister_waiting_writer(std::uint32_t requester) {
+    const std::uint64_t bit = owner_bit(requester);
+    if ((writer_priority_.waiting_writers & bit) != 0) {
+      writer_priority_.waiting_writers &= ~bit;
+    }
+  }
+
+  void install_owner(std::uint32_t requester, SS2PLLockMode mode,
+                     bool upgrading) {
+    if constexpr (LockKind == 0) {
+      writer_ = requester;
+      return;
+    }
+
+    if (mode == SS2PLLockMode::read) {
+      if (writer_ != requester) readers_ |= owner_bit(requester);
+      return;
+    }
+
+    if (upgrading) readers_ &= ~owner_bit(requester);
+    writer_ = requester;
+  }
+
+  void wait_for_owner_change(SS2PLTxControl& requester,
+                             std::uint32_t victim,
+                             std::uint64_t victim_attempt,
+                             std::uint64_t observed_release_generation) {
+    SS2PLTxControl& victim_control = ss2pl_control(victim);
+    std::uint32_t pause_count = 1;
+    // Poll only the cache-line-isolated owner control.  Waiters never acquire
+    // the tuple latch that the victim needs in order to release its locks.
+    while (victim_control.lock_release_generation() ==
+               observed_release_generation &&
+           victim_control.attempt() == victim_attempt &&
+           requester.may_request_lock()) {
+      for (std::uint32_t i = 0; i < pause_count; ++i) _mm_pause();
+      if (pause_count < 64) {
+        pause_count *= 2;
+      } else {
+        std::this_thread::yield();
+      }
+    }
+  }
+
+  void wait_for_waiting_writer_change(
+      SS2PLTxControl& requester, std::uint32_t writer,
+      std::uint64_t writer_attempt,
+      std::uint64_t observed_release_generation) {
+    SS2PLTxControl& writer_control = ss2pl_control(writer);
+    std::uint32_t pause_count = 1;
+    // A gated reader polls only the cache-line-isolated writer control.  It
+    // does not compete for the tuple latch needed by that writer or owners.
+    while (writer_control.lock_release_generation() ==
+               observed_release_generation &&
+           writer_control.attempt() == writer_attempt &&
+           writer_control.may_request_lock() &&
+           requester.may_request_lock()) {
+      for (std::uint32_t i = 0; i < pause_count; ++i) _mm_pause();
+      if (pause_count < 64) {
+        pause_count *= 2;
+      } else {
+        std::this_thread::yield();
+      }
+    }
+  }
+
+  [[nodiscard]] bool acquire(SS2PLTxControl& requester, SS2PLLockMode mode,
+                             bool try_only, bool upgrading) {
+    [[maybe_unused]] std::uint32_t last_victim = kNoOwner;
+    [[maybe_unused]] std::uint64_t last_victim_attempt = 0;
+    [[maybe_unused]] bool registered_as_waiting_writer = false;
+    for (;;) {
+      if constexpr (DeadlockResolution == 2) {
+        if (!requester.may_request_lock()) {
+          if constexpr (kWriterPriority) {
+            if (registered_as_waiting_writer) {
+              latch();
+              unregister_waiting_writer(requester.thid());
+              unlatch();
+            }
+          }
+          return false;
+        }
+      }
+
+      latch();
+      if constexpr (DeadlockResolution == 2) {
+        if (!requester.may_request_lock()) {
+          if constexpr (kWriterPriority) {
+            if (registered_as_waiting_writer) {
+              unregister_waiting_writer(requester.thid());
+            }
+          }
+          unlatch();
+          return false;
+        }
+      }
+
+      std::uint32_t blocker =
+          first_blocker(requester.thid(), mode, upgrading);
+      [[maybe_unused]] bool blocked_by_waiting_writer = false;
+      if constexpr (kWriterPriority) {
+        if (blocker == kNoOwner && mode == SS2PLLockMode::read) {
+          blocker = first_older_waiting_writer(requester);
+          blocked_by_waiting_writer = blocker != kNoOwner;
+        }
+      }
+      if (blocker == kNoOwner) {
+        if constexpr (kWriterPriority) {
+          if (registered_as_waiting_writer) {
+            unregister_waiting_writer(requester.thid());
+          }
+        }
+        install_owner(requester.thid(), mode, upgrading);
+        unlatch();
+        return true;
+      }
+
+      if constexpr (kWriterPriority) {
+        if (mode == SS2PLLockMode::write && !try_only &&
+            !registered_as_waiting_writer) {
+          register_waiting_writer(requester.thid());
+          registered_as_waiting_writer = true;
+        }
+      }
+
+      SS2PLTxControl& victim = ss2pl_control(blocker);
+      const std::uint64_t victim_attempt = victim.attempt();
+      const std::uint64_t observed_release_generation =
+          victim.lock_release_generation();
+#ifdef SS2PL_STUDY_LOCK_TESTING
+      std::atomic<bool>* const contention_observer = contention_observer_;
+      contention_observer_ = nullptr;
+#endif
+      unlatch();
+
+#ifdef SS2PL_STUDY_LOCK_TESTING
+      if (contention_observer != nullptr) {
+        contention_observer->store(true, std::memory_order_release);
+      }
+#endif
+      if (try_only || DeadlockResolution == 1) return false;
+
+      if constexpr (DeadlockResolution == 2) {
+        if constexpr (kWriterPriority) {
+          if (blocked_by_waiting_writer) {
+            wait_for_waiting_writer_change(
+                requester, blocker, victim_attempt,
+                observed_release_generation);
+            continue;
+          }
+        }
+        if (blocker != last_victim || victim_attempt != last_victim_attempt) {
+          (void) victim.wound_exact(victim_attempt, requester.logical_ts(),
+                                    requester.thid());
+          last_victim = blocker;
+          last_victim_attempt = victim_attempt;
+        }
+        wait_for_owner_change(requester, blocker, victim_attempt,
+                              observed_release_generation);
+      } else {
+        _mm_pause();
+      }
+    }
+  }
+
+  std::atomic_flag latch_ = ATOMIC_FLAG_INIT;
+  std::uint32_t writer_ = kNoOwner;
+  std::uint64_t readers_ = 0;
+  [[no_unique_address]] WriterPriorityState writer_priority_{};
+#ifdef SS2PL_STUDY_LOCK_TESTING
+  std::atomic<bool>* contention_observer_ = nullptr;
+#endif
+};
+#endif
+#endif
diff --git a/cc/ss2pl/include/ss2pl_wfg.hh b/cc/ss2pl/include/ss2pl_wfg.hh
new file mode 100644
--- /dev/null
+++ b/cc/ss2pl/include/ss2pl_wfg.hh
@@ -0,0 +1,24 @@
+#ifndef CCBENCH_SS2PL_WFG_HH_INCLUDED
+#define CCBENCH_SS2PL_WFG_HH_INCLUDED
+
+#include <cstdint>
+#include <string>
+
+#if SS2PL_WFG_DIAG
+enum class SS2PLWfgMode : std::uint8_t { read = 0, write = 1 };
+
+void ss2pl_wfg_start(const std::string& output_path, std::uint32_t thread_num);
+void ss2pl_wfg_stop();
+void ss2pl_wfg_register_worker(std::uint32_t thid, std::uint64_t attempt,
+                               std::uint64_t commits,
+                               std::uint64_t aborts);
+void ss2pl_wfg_before_wait(std::uint32_t thid, std::uint64_t attempt,
+                           const void* lock, SS2PLWfgMode mode);
+void ss2pl_wfg_acquired(std::uint32_t thid, const void* lock,
+                        SS2PLWfgMode mode);
+void ss2pl_wfg_acquire_failed(std::uint32_t thid);
+void ss2pl_wfg_released(std::uint32_t thid, const void* lock);
+void ss2pl_wfg_record_no_wait_failure();
+void ss2pl_wfg_record_acquire(SS2PLWfgMode mode, bool upgrade);
+#endif
+#endif
diff --git a/cc/ss2pl/test/study_lock_test.cpp b/cc/ss2pl/test/study_lock_test.cpp
new file mode 100644
--- /dev/null
+++ b/cc/ss2pl/test/study_lock_test.cpp
@@ -0,0 +1,335 @@
+#include <array>
+#include <atomic>
+#include <chrono>
+#include <cstdint>
+#include <functional>
+#include <thread>
+
+#define GLOBAL_VALUE_DEFINE
+
+#include "../include/common.hh"
+#include "../include/ss2pl_study_lock.hh"
+#include "../include/transaction.hh"
+
+#include "gtest/gtest.h"
+
+namespace {
+
+using namespace std::chrono_literals;
+
+bool wait_until(const std::function<bool()>& predicate,
+                std::chrono::steady_clock::duration timeout = 2s) {
+  const auto deadline = std::chrono::steady_clock::now() + timeout;
+  while (std::chrono::steady_clock::now() < deadline) {
+    if (predicate()) return true;
+    std::this_thread::yield();
+  }
+  return predicate();
+}
+
+class StudyLockTest : public ::testing::Test {
+protected:
+  void SetUp() override {
+    for (std::size_t index = 0; index < quits_.size(); ++index) {
+      const auto thid = static_cast<std::uint32_t>(index);
+      quits_[thid] = false;
+      ss2pl_control(thid).initialize(thid, quits_[thid]);
+    }
+  }
+
+  SS2PLTxControl& begin(std::uint32_t thid) {
+    SS2PLTxControl& control = ss2pl_control(thid);
+    control.begin_attempt();
+    return control;
+  }
+
+  std::array<bool, 8> quits_{};
+};
+
+TEST_F(StudyLockTest, OlderRequesterWoundsYoungerInflightOwner) {
+  using Lock = SS2PLStudyLockT<1, 2>;
+  Lock lock;
+  SS2PLTxControl& older = begin(0);
+  SS2PLTxControl& younger = begin(1);
+  ASSERT_TRUE(lock.w_lock(younger));
+
+  std::atomic<bool> acquired{false};
+  std::atomic<bool> finished{false};
+  std::thread requester([&]() {
+    acquired.store(lock.w_lock(older));
+    finished.store(true);
+  });
+
+  const bool wounded = wait_until(
+      [&]() { return younger.state() == SS2PLAttemptState::wounded; });
+  if (!wounded) storeRelease(quits_[older.thid()], true);
+  EXPECT_TRUE(wounded);
+  EXPECT_TRUE(lock.is_held_by(younger.thid()));
+  EXPECT_FALSE(lock.is_held_by(older.thid()));
+
+  lock.w_unlock(younger);
+  EXPECT_TRUE(wait_until([&]() { return finished.load(); }));
+  requester.join();
+  if (wounded) {
+    EXPECT_TRUE(acquired.load());
+  }
+  if (acquired.load()) lock.w_unlock(older);
+}
+
+TEST_F(StudyLockTest, YoungerRequesterWaitsForOlderOwner) {
+  using Lock = SS2PLStudyLockT<1, 2>;
+  Lock lock;
+  SS2PLTxControl& older = begin(0);
+  SS2PLTxControl& younger = begin(1);
+  ASSERT_TRUE(lock.w_lock(older));
+
+  std::atomic<bool> reached_conflict{false};
+  lock.observe_contention_for_test(reached_conflict);
+  std::atomic<bool> finished{false};
+  std::atomic<bool> acquired{false};
+  std::thread requester([&]() {
+    acquired.store(lock.w_lock(younger));
+    finished.store(true);
+  });
+
+  const bool reached = wait_until(
+      [&]() { return reached_conflict.load(std::memory_order_acquire); });
+  if (!reached) storeRelease(quits_[younger.thid()], true);
+  EXPECT_TRUE(reached);
+  if (reached) {
+    EXPECT_FALSE(finished.load());
+    EXPECT_EQ(older.state(), SS2PLAttemptState::inflight);
+  }
+  lock.w_unlock(older);
+  EXPECT_TRUE(wait_until([&]() { return finished.load(); }));
+  requester.join();
+  if (reached) {
+    EXPECT_TRUE(acquired.load());
+  }
+  if (acquired.load()) lock.w_unlock(younger);
+}
+
+TEST_F(StudyLockTest, StaleWoundCannotAbortNewAttempt) {
+  SS2PLTxControl& requester = begin(0);
+  SS2PLTxControl& victim = begin(1);
+  const std::uint64_t stale_attempt = victim.attempt();
+  victim.finish_abort();
+  victim.begin_attempt();
+
+  EXPECT_FALSE(victim.wound_exact(stale_attempt, requester.logical_ts(),
+                                  requester.thid()));
+  EXPECT_EQ(victim.state(), SS2PLAttemptState::inflight);
+}
+
+TEST_F(StudyLockTest, SelfOwnershipDoesNotWoundRequester) {
+  using Lock = SS2PLStudyLockT<1, 2>;
+  Lock lock;
+  SS2PLTxControl& owner = begin(0);
+  ASSERT_TRUE(lock.r_lock(owner));
+
+  std::atomic<bool> started{false};
+  std::atomic<bool> upgraded{false};
+  std::atomic<bool> finished{false};
+  std::thread requester([&]() {
+    started.store(true);
+    upgraded.store(lock.upgrade(owner));
+    finished.store(true);
+  });
+
+  const bool started_on_time = wait_until([&]() { return started.load(); });
+  const bool completed =
+      started_on_time && wait_until([&]() { return finished.load(); }, 1s);
+  if (!completed) {
+    storeRelease(quits_[owner.thid()], true);
+    EXPECT_TRUE(wait_until([&]() { return finished.load(); }));
+  }
+  requester.join();
+  EXPECT_TRUE(started_on_time);
+  EXPECT_TRUE(completed) << "self ownership caused upgrade to wait";
+  EXPECT_TRUE(upgraded.load());
+  EXPECT_EQ(owner.state(), SS2PLAttemptState::inflight);
+  if (upgraded.load()) {
+    lock.w_unlock(owner);
+  } else {
+    lock.r_unlock(owner);
+  }
+}
+
+TEST_F(StudyLockTest, LockKindChangesOnlyReadCompatibility) {
+  SS2PLTxControl& first = begin(0);
+  SS2PLTxControl& second = begin(1);
+
+  SS2PLStudyLockT<1, 1> reader_writer;
+  ASSERT_TRUE(reader_writer.r_lock(first));
+  EXPECT_TRUE(reader_writer.r_lock(second));
+  reader_writer.r_unlock(second);
+  reader_writer.r_unlock(first);
+
+  SS2PLStudyLockT<0, 1> exclusive;
+  ASSERT_TRUE(exclusive.r_lock(first));
+  EXPECT_FALSE(exclusive.r_lock(second));
+  exclusive.r_unlock(first);
+}
+
+TEST_F(StudyLockTest, WoundRequesterNeverForcesVictimUnlock) {
+  using Lock = SS2PLStudyLockT<0, 2>;
+  Lock lock;
+  SS2PLTxControl& older = begin(0);
+  SS2PLTxControl& younger = begin(1);
+  ASSERT_TRUE(lock.w_lock(younger));
+
+  std::atomic<bool> acquired{false};
+  std::atomic<bool> finished{false};
+  std::thread requester([&]() {
+    acquired.store(lock.w_lock(older));
+    finished.store(true);
+  });
+  const bool wounded = wait_until(
+      [&]() { return younger.state() == SS2PLAttemptState::wounded; });
+  if (!wounded) storeRelease(quits_[older.thid()], true);
+  EXPECT_TRUE(wounded);
+  EXPECT_TRUE(lock.is_held_by(younger.thid()));
+  EXPECT_FALSE(acquired.load());
+
+  lock.w_unlock(younger);
+  EXPECT_TRUE(wait_until([&]() { return finished.load(); }));
+  requester.join();
+  if (wounded) {
+    EXPECT_TRUE(acquired.load());
+  }
+  if (acquired.load()) lock.w_unlock(older);
+}
+
+TEST_F(StudyLockTest, RetryKeepsTimestampUntilSuccessfulCommit) {
+  SS2PLTxControl& control = begin(0);
+  const std::uint64_t original = control.logical_ts();
+  control.finish_abort();
+  control.begin_attempt();
+  EXPECT_EQ(control.logical_ts(), original);
+  ASSERT_TRUE(control.prepare_commit());
+  control.finish_commit();
+  EXPECT_EQ(control.logical_ts(), 0u);
+}
+
+#if SS2PL_LOCK_IMPL == 1
+TEST_F(StudyLockTest, ProductionReadLockRegistersExactlyOnce) {
+  Result result;
+  TxExecutor tx(0, &result, quits_[0]);
+  tx.begin();
+  Tuple tuple;
+  SimpleKey<8> key{};
+  assign_as_bigendian(std::uint64_t{0xf10001}, key.ptr());
+  constexpr Storage storage = static_cast<Storage>(0);
+  ASSERT_EQ(Masstrees[get_storage(storage)].insert_value(key.view(), &tuple),
+            Status::OK);
+
+  ASSERT_EQ(tx.read_lock(storage, key.view()), Status::OK);
+  ASSERT_EQ(tx.read_lock(storage, key.view()), Status::OK);
+  ASSERT_EQ(tx.r_lock_list_.size(), 1u);
+  EXPECT_TRUE(tx.w_lock_list_.empty());
+  tx.abort();
+  EXPECT_TRUE(tuple.lock_.is_unlocked_for_test());
+}
+
+TEST_F(StudyLockTest, ProductionUpgradeMovesSingleRegistration) {
+  Result result;
+  TxExecutor tx(0, &result, quits_[0]);
+  tx.begin();
+  Tuple tuple;
+  SimpleKey<8> key{};
+  assign_as_bigendian(std::uint64_t{0xf10002}, key.ptr());
+  constexpr Storage storage = static_cast<Storage>(0);
+  ASSERT_EQ(Masstrees[get_storage(storage)].insert_value(key.view(), &tuple),
+            Status::OK);
+
+  ASSERT_EQ(tx.read_lock(storage, key.view()), Status::OK);
+  ASSERT_EQ(tx.write_lock(storage, key.view()), Status::OK);
+  EXPECT_TRUE(tx.r_lock_list_.empty());
+  ASSERT_EQ(tx.w_lock_list_.size(), 1u);
+  tx.abort();
+  EXPECT_TRUE(tuple.lock_.is_unlocked_for_test());
+}
+
+#if SS2PL_DLR != 0
+TEST_F(StudyLockTest, ProductionFailedAcquireIsNotRegistered) {
+  Tuple tuple;
+  SimpleKey<8> key{};
+  assign_as_bigendian(std::uint64_t{0xf10003}, key.ptr());
+  constexpr Storage storage = static_cast<Storage>(0);
+  ASSERT_EQ(Masstrees[get_storage(storage)].insert_value(key.view(), &tuple),
+            Status::OK);
+
+  SS2PLTxControl& blocker = begin(1);
+  ASSERT_TRUE(tuple.lock_.w_lock(blocker));
+
+  Result result;
+  TxExecutor tx(0, &result, quits_[0]);
+  tx.begin();
+#if SS2PL_DLR == 2
+  storeRelease(quits_[0], true);
+#endif
+  EXPECT_EQ(tx.read_lock(storage, key.view()), Status::ERROR_LOCK_FAILED);
+  EXPECT_TRUE(tx.r_lock_list_.empty());
+  EXPECT_TRUE(tx.w_lock_list_.empty());
+  EXPECT_TRUE(tuple.lock_.is_held_by(blocker.thid()));
+  tx.abort();
+  tuple.lock_.w_unlock(blocker);
+  EXPECT_TRUE(tuple.lock_.is_unlocked_for_test());
+}
+#endif
+#endif
+
+TEST_F(StudyLockTest, TwoUpgradersResolveByTimestampOrder) {
+  using Lock = SS2PLStudyLockT<1, 2>;
+  Lock lock;
+  SS2PLTxControl& older = begin(0);
+  SS2PLTxControl& younger = begin(1);
+  ASSERT_TRUE(lock.r_lock(older));
+  ASSERT_TRUE(lock.r_lock(younger));
+
+  std::atomic<bool> start{false};
+  std::atomic<bool> older_result{false};
+  std::atomic<bool> younger_result{false};
+  std::atomic<bool> older_finished{false};
+  std::atomic<bool> younger_finished{false};
+  std::thread older_thread([&]() {
+    while (!start.load()) std::this_thread::yield();
+    const bool acquired = lock.upgrade(older);
+    older_result.store(acquired);
+    if (acquired) {
+      lock.w_unlock(older);
+    } else {
+      lock.r_unlock(older);
+    }
+    older_finished.store(true);
+  });
+  std::thread younger_thread([&]() {
+    while (!start.load()) std::this_thread::yield();
+    const bool acquired = lock.upgrade(younger);
+    younger_result.store(acquired);
+    if (acquired) {
+      lock.w_unlock(younger);
+    } else {
+      lock.r_unlock(younger);
+    }
+    younger_finished.store(true);
+  });
+
+  start.store(true);
+  const bool completed = wait_until(
+      [&]() { return older_finished.load() && younger_finished.load(); });
+  if (!completed) {
+    storeRelease(quits_[older.thid()], true);
+    storeRelease(quits_[younger.thid()], true);
+    EXPECT_TRUE(wait_until(
+        [&]() { return older_finished.load() && younger_finished.load(); }));
+  }
+  older_thread.join();
+  younger_thread.join();
+  EXPECT_TRUE(completed) << "concurrent upgrades exceeded their deadline";
+  EXPECT_TRUE(older_result.load());
+  EXPECT_FALSE(younger_result.load());
+  EXPECT_TRUE(lock.is_unlocked_for_test());
+}
+
+} // namespace
diff --git a/cc/ss2pl/wfg.cc b/cc/ss2pl/wfg.cc
new file mode 100644
--- /dev/null
+++ b/cc/ss2pl/wfg.cc
@@ -0,0 +1,420 @@
+#include "include/ss2pl_wfg.hh"
+
+#include <algorithm>
+#include <array>
+#include <atomic>
+#include <chrono>
+#include <cstdio>
+#include <cstdint>
+#include <fcntl.h>
+#include <mutex>
+#include <sstream>
+#include <string>
+#include <thread>
+#include <unistd.h>
+#include <utility>
+#include <vector>
+
+#include "../../include/debug.hh"
+
+namespace {
+
+constexpr std::size_t kMaxWorkers = 64;
+
+struct HeldLock {
+  std::uintptr_t lock_id = 0;
+  SS2PLWfgMode mode = SS2PLWfgMode::read;
+};
+
+struct WorkerState {
+  bool registered = false;
+  std::uint64_t attempt = 0;
+  bool waiting = false;
+  std::uintptr_t waiting_lock = 0;
+  SS2PLWfgMode waiting_mode = SS2PLWfgMode::read;
+  std::uint64_t commits = 0;
+  std::uint64_t aborts = 0;
+  std::vector<HeldLock> held;
+};
+
+struct Snapshot {
+  std::array<WorkerState, kMaxWorkers> workers;
+  std::uint32_t thread_num = 0;
+  std::uint64_t conflicts = 0;
+  std::uint64_t no_wait_failures = 0;
+  std::uint64_t read_acquires = 0;
+  std::uint64_t write_acquires = 0;
+  std::uint64_t upgrades = 0;
+};
+
+std::mutex RegistryMutex;
+std::array<WorkerState, kMaxWorkers> Workers;
+std::uint32_t WorkerCount = 0;
+std::uint64_t ConflictCount = 0;
+std::uint64_t NoWaitFailureCount = 0;
+std::uint64_t ReadAcquireCount = 0;
+std::uint64_t WriteAcquireCount = 0;
+std::uint64_t UpgradeCount = 0;
+std::string OutputPath;
+std::atomic<bool> StopRequested{false};
+std::atomic<bool> CycleWritten{false};
+std::thread Watchdog;
+
+[[nodiscard]] const char* mode_name(SS2PLWfgMode mode) {
+#if SS2PL_LOCK_IMPL == 1 && SS2PL_LOCK_KIND == 0
+  (void) mode;
+  return "write";
+#else
+  return mode == SS2PLWfgMode::read ? "read" : "write";
+#endif
+}
+
+[[nodiscard]] bool incompatible(SS2PLWfgMode requested,
+                                SS2PLWfgMode held) {
+#if SS2PL_LOCK_KIND == 1
+  return requested == SS2PLWfgMode::write || held == SS2PLWfgMode::write;
+#else
+  (void) requested;
+  (void) held;
+  return true;
+#endif
+}
+
+[[nodiscard]] Snapshot take_snapshot() {
+  std::lock_guard<std::mutex> guard(RegistryMutex);
+  Snapshot snapshot;
+  snapshot.workers = Workers;
+  snapshot.thread_num = WorkerCount;
+  snapshot.conflicts = ConflictCount;
+  snapshot.no_wait_failures = NoWaitFailureCount;
+  snapshot.read_acquires = ReadAcquireCount;
+  snapshot.write_acquires = WriteAcquireCount;
+  snapshot.upgrades = UpgradeCount;
+  return snapshot;
+}
+
+[[nodiscard]] std::vector<std::vector<std::uint32_t>> make_edges(
+    const Snapshot& snapshot) {
+  std::vector<std::vector<std::uint32_t>> edges(snapshot.thread_num);
+  for (std::uint32_t waiter = 0; waiter < snapshot.thread_num; ++waiter) {
+    const WorkerState& waiting = snapshot.workers[waiter];
+    if (!waiting.registered || !waiting.waiting) continue;
+
+    for (std::uint32_t holder = 0; holder < snapshot.thread_num; ++holder) {
+      if (holder == waiter) continue;
+      const WorkerState& owner = snapshot.workers[holder];
+      if (!owner.registered) continue;
+      for (const HeldLock& lock : owner.held) {
+        if (lock.lock_id == waiting.waiting_lock &&
+            incompatible(waiting.waiting_mode, lock.mode)) {
+          edges[waiter].push_back(holder);
+          break;
+        }
+      }
+    }
+  }
+  return edges;
+}
+
+bool find_cycle_from(std::uint32_t node,
+                     const std::vector<std::vector<std::uint32_t>>& edges,
+                     std::vector<std::uint8_t>& color,
+                     std::vector<std::uint32_t>& stack,
+                     std::vector<std::uint32_t>& cycle) {
+  color[node] = 1;
+  stack.push_back(node);
+  for (std::uint32_t next : edges[node]) {
+    if (color[next] == 0) {
+      if (find_cycle_from(next, edges, color, stack, cycle)) return true;
+    } else if (color[next] == 1) {
+      auto begin = stack.begin();
+      while (begin != stack.end() && *begin != next) ++begin;
+      cycle.assign(begin, stack.end());
+      return true;
+    }
+  }
+  stack.pop_back();
+  color[node] = 2;
+  return false;
+}
+
+[[nodiscard]] std::vector<std::uint32_t> find_cycle(
+    const std::vector<std::vector<std::uint32_t>>& edges) {
+  std::vector<std::uint8_t> color(edges.size(), 0);
+  std::vector<std::uint32_t> stack;
+  std::vector<std::uint32_t> cycle;
+  for (std::size_t node = 0; node < edges.size(); ++node) {
+    if (color[node] == 0 && find_cycle_from(static_cast<std::uint32_t>(node),
+                                            edges, color, stack, cycle)) {
+      break;
+    }
+  }
+  if (cycle.empty()) return cycle;
+
+  std::size_t minimum = 0;
+  for (std::size_t i = 1; i < cycle.size(); ++i) {
+    if (cycle[i] < cycle[minimum]) minimum = i;
+  }
+  std::rotate(cycle.begin(), cycle.begin() + minimum, cycle.end());
+  return cycle;
+}
+
+[[nodiscard]] std::string cycle_signature(
+    const Snapshot& snapshot, const std::vector<std::uint32_t>& cycle) {
+  std::ostringstream out;
+  for (std::uint32_t thid : cycle) {
+    const WorkerState& worker = snapshot.workers[thid];
+    out << thid << ':' << worker.attempt << ':' << worker.waiting_lock << ':'
+        << static_cast<unsigned>(worker.waiting_mode) << ':' << worker.commits
+        << ':' << worker.aborts << ';';
+  }
+  return out.str();
+}
+
+void write_all(int fd, const std::string& data) {
+  std::size_t offset = 0;
+  while (offset < data.size()) {
+    const ssize_t written =
+        ::write(fd, data.data() + offset, data.size() - offset);
+    if (written <= 0) ERR;
+    offset += static_cast<std::size_t>(written);
+  }
+}
+
+void durable_replace(const std::string& data) {
+  const std::string temporary = OutputPath + ".tmp";
+  const int fd = ::open(temporary.c_str(), O_CREAT | O_TRUNC | O_WRONLY, 0644);
+  if (fd < 0) ERR;
+  write_all(fd, data);
+  if (::fsync(fd) != 0) ERR;
+  if (::close(fd) != 0) ERR;
+  if (::rename(temporary.c_str(), OutputPath.c_str()) != 0) ERR;
+
+  const std::size_t slash = OutputPath.find_last_of('/');
+  const std::string directory =
+      slash == std::string::npos ? "." : OutputPath.substr(0, slash);
+  const int dir_fd = ::open(directory.c_str(), O_RDONLY | O_DIRECTORY);
+  if (dir_fd < 0) ERR;
+  if (::fsync(dir_fd) != 0) ERR;
+  if (::close(dir_fd) != 0) ERR;
+}
+
+[[nodiscard]] std::string cycle_json(
+    const Snapshot& snapshot,
+    const std::vector<std::vector<std::uint32_t>>& edges,
+    const std::vector<std::uint32_t>& cycle, std::uint64_t tick) {
+  std::ostringstream out;
+  out << "{\"schema\":\"ss2pl-wfg/v2\",\"event\":\"wfg_snapshot\",\"tick\":"
+      << tick << ",\"cycle_found\":true,\"conflict_count\":" << snapshot.conflicts
+      << ",\"no_wait_failure_count\":" << snapshot.no_wait_failures
+      << ",\"nodes\":[";
+  for (std::size_t i = 0; i < cycle.size(); ++i) {
+    const std::uint32_t thid = cycle[i];
+    const WorkerState& worker = snapshot.workers[thid];
+    if (i != 0) out << ',';
+    out << "{\"thread_id\":" << thid << ",\"attempt\":"
+        << worker.attempt << ",\"wait_lock_id\":\"0x" << std::hex
+        << worker.waiting_lock << std::dec << "\",\"request_mode\":\""
+        << mode_name(worker.waiting_mode) << "\",\"commit_count\":"
+        << worker.commits << ",\"abort_count\":" << worker.aborts
+        << ",\"held_locks\":[";
+    for (std::size_t j = 0; j < worker.held.size(); ++j) {
+      const HeldLock& held = worker.held[j];
+      if (j != 0) out << ',';
+      out << "{\"lock_id\":\"0x" << std::hex << held.lock_id << std::dec
+          << "\",\"mode\":\"" << mode_name(held.mode) << "\"}";
+    }
+    out << "]}";
+  }
+  out << "],\"edges\":[";
+  bool first = true;
+  for (std::uint32_t waiter : cycle) {
+    for (std::uint32_t holder : edges[waiter]) {
+      bool holder_in_cycle = false;
+      for (std::uint32_t node : cycle) {
+        if (node == holder) holder_in_cycle = true;
+      }
+      if (!holder_in_cycle) continue;
+      const HeldLock* held_lock = nullptr;
+      for (const HeldLock& held : snapshot.workers[holder].held) {
+        if (held.lock_id == snapshot.workers[waiter].waiting_lock) {
+          held_lock = &held;
+          break;
+        }
+      }
+      if (held_lock == nullptr) continue;
+      if (!first) out << ',';
+      first = false;
+      out << "{\"waiter_thread_id\":" << waiter << ",\"holder_thread_id\":" << holder
+          << ",\"lock_id\":\"0x" << std::hex
+          << snapshot.workers[waiter].waiting_lock << std::dec
+          << "\",\"request_mode\":\""
+          << mode_name(snapshot.workers[waiter].waiting_mode)
+          << "\",\"holder_mode\":\"" << mode_name(held_lock->mode)
+          << "\",\"compatible\":false}";
+    }
+  }
+  out << "]}\n";
+  return out.str();
+}
+
+void emit_snapshot(const std::string& data) {
+  std::lock_guard<std::mutex> guard(cout_mutex);
+  ::flockfile(stdout);
+  const std::size_t written = std::fwrite(data.data(), 1, data.size(), stdout);
+  const int flushed = std::fflush(stdout);
+  ::funlockfile(stdout);
+  if (written != data.size() || flushed != 0) ERR;
+}
+
+[[nodiscard]] std::string terminal_json(const Snapshot& snapshot) {
+  std::ostringstream out;
+  out << "{\"schema\":\"ss2pl-wfg/v2\",\"event\":\"wfg_terminal\",\"tick\":null"
+      << ",\"cycle_found\":false,\"conflict_count\":" << snapshot.conflicts
+      << ",\"no_wait_failure_count\":" << snapshot.no_wait_failures
+      << ",\"read_acquire_count\":" << snapshot.read_acquires
+      << ",\"write_acquire_count\":" << snapshot.write_acquires
+      << ",\"upgrade_count\":" << snapshot.upgrades
+      << ",\"nodes\":[],\"edges\":[]}\n";
+  return out.str();
+}
+
+void watchdog_main() {
+  std::string previous_signature;
+  std::uint32_t consecutive = 0;
+  std::uint64_t tick = 0;
+  while (!StopRequested.load(std::memory_order_acquire)) {
+    ++tick;
+    const Snapshot snapshot = take_snapshot();
+    const auto edges = make_edges(snapshot);
+    const auto cycle = find_cycle(edges);
+    const std::string signature = cycle_signature(snapshot, cycle);
+    if (!cycle.empty() && signature == previous_signature) {
+      ++consecutive;
+    } else if (!cycle.empty()) {
+      previous_signature = signature;
+      consecutive = 1;
+    } else {
+      previous_signature.clear();
+      consecutive = 0;
+    }
+
+    std::string emitted;
+    if (!cycle.empty()) {
+      emitted = cycle_json(snapshot, edges, cycle, tick);
+      emit_snapshot(emitted);
+    }
+    if (consecutive >= 3) {
+      durable_replace(emitted);
+      CycleWritten.store(true, std::memory_order_release);
+      return;
+    }
+    std::this_thread::sleep_for(std::chrono::milliseconds(10));
+  }
+}
+
+} // namespace
+
+void ss2pl_wfg_start(const std::string& output_path,
+                     std::uint32_t thread_num) {
+  std::lock_guard<std::mutex> guard(RegistryMutex);
+  Workers = {};
+  WorkerCount = thread_num;
+  ConflictCount = 0;
+  NoWaitFailureCount = 0;
+  ReadAcquireCount = 0;
+  WriteAcquireCount = 0;
+  UpgradeCount = 0;
+  OutputPath = output_path;
+  StopRequested.store(false, std::memory_order_release);
+  CycleWritten.store(false, std::memory_order_release);
+  Watchdog = std::thread(watchdog_main);
+}
+
+void ss2pl_wfg_stop() {
+  StopRequested.store(true, std::memory_order_release);
+  if (Watchdog.joinable()) Watchdog.join();
+  if (!CycleWritten.load(std::memory_order_acquire)) {
+    durable_replace(terminal_json(take_snapshot()));
+  }
+}
+
+void ss2pl_wfg_register_worker(std::uint32_t thid, std::uint64_t attempt,
+                               std::uint64_t commits,
+                               std::uint64_t aborts) {
+  std::lock_guard<std::mutex> guard(RegistryMutex);
+  WorkerState& worker = Workers[thid];
+  worker.registered = true;
+  worker.attempt = attempt;
+  worker.commits = commits;
+  worker.aborts = aborts;
+}
+
+void ss2pl_wfg_before_wait(std::uint32_t thid, std::uint64_t attempt,
+                           const void* lock, SS2PLWfgMode mode) {
+  std::lock_guard<std::mutex> guard(RegistryMutex);
+  WorkerState& worker = Workers[thid];
+  worker.attempt = attempt;
+  worker.waiting = true;
+  worker.waiting_lock = reinterpret_cast<std::uintptr_t>(lock);
+  worker.waiting_mode = mode;
+
+  for (std::uint32_t holder = 0; holder < WorkerCount; ++holder) {
+    if (holder == thid) continue;
+    for (const HeldLock& held : Workers[holder].held) {
+      if (held.lock_id == worker.waiting_lock && incompatible(mode, held.mode)) {
+        ++ConflictCount;
+        return;
+      }
+    }
+  }
+}
+
+void ss2pl_wfg_acquired(std::uint32_t thid, const void* lock,
+                        SS2PLWfgMode mode) {
+  std::lock_guard<std::mutex> guard(RegistryMutex);
+  WorkerState& worker = Workers[thid];
+  worker.waiting = false;
+  const std::uintptr_t lock_id = reinterpret_cast<std::uintptr_t>(lock);
+  for (HeldLock& held : worker.held) {
+    if (held.lock_id == lock_id) {
+      held.mode = mode;
+      return;
+    }
+  }
+  worker.held.push_back(HeldLock{lock_id, mode});
+}
+
+void ss2pl_wfg_acquire_failed(std::uint32_t thid) {
+  std::lock_guard<std::mutex> guard(RegistryMutex);
+  Workers[thid].waiting = false;
+}
+
+void ss2pl_wfg_released(std::uint32_t thid, const void* lock) {
+  std::lock_guard<std::mutex> guard(RegistryMutex);
+  auto& held = Workers[thid].held;
+  const std::uintptr_t lock_id = reinterpret_cast<std::uintptr_t>(lock);
+  for (auto it = held.begin(); it != held.end(); ++it) {
+    if (it->lock_id == lock_id) {
+      held.erase(it);
+      return;
+    }
+  }
+}
+
+void ss2pl_wfg_record_no_wait_failure() {
+  std::lock_guard<std::mutex> guard(RegistryMutex);
+  ++ConflictCount;
+  ++NoWaitFailureCount;
+}
+
+void ss2pl_wfg_record_acquire(SS2PLWfgMode mode, bool upgrade) {
+  std::lock_guard<std::mutex> guard(RegistryMutex);
+  if (upgrade) {
+    ++UpgradeCount;
+  } else if (mode == SS2PLWfgMode::read) {
+    ++ReadAcquireCount;
+  } else {
+    ++WriteAcquireCount;
+  }
+}
diff --git a/cc/ss2pl/ycsb_ss2pl.cc b/cc/ss2pl/ycsb_ss2pl.cc
new file mode 100644
--- /dev/null
+++ b/cc/ss2pl/ycsb_ss2pl.cc
@@ -0,0 +1,65 @@
+#define GLOBAL_VALUE_DEFINE
+
+#include "include/common.hh"
+#include "include/result.hh"
+#include "include/transaction.hh"
+#include "include/util.hh"
+#if SS2PL_WFG_DIAG
+#include "include/ss2pl_wfg.hh"
+#endif
+
+#include "../../include/cpu.hh"
+#include "../../include/debug.hh"
+#include "../../include/masstree_wrapper.hh"
+#include "../../include/result.hh"
+#include "../../include/tsc.hh"
+#include "../../include/util.hh"
+#include "../../include/ycsb.hh"
+
+#include "../../common/runner.hh"
+
+using namespace std;
+
+int main(int argc, char* argv[]) try {
+  gflags::SetUsageMessage("YCSB SS2PL benchmark.");
+  gflags::ParseCommandLineFlags(&argc, &argv, true);
+  chkArg();
+#if SS2PL_WFG_DIAG
+  ShowOptParameters();
+#endif
+  YcsbWorkload::displayWorkloadParameter();
+  YcsbWorkload::makeDB<Tuple, void>(nullptr);
+
+  initResult(TotalThreadNum);
+
+#if SS2PL_WFG_DIAG
+  ss2pl_wfg_start(FLAGS_ss2pl_wfg_output, TotalThreadNum);
+#endif
+
+  ccbench::run<TxExecutor, TransactionStatus, YcsbWorkload>(
+      TotalThreadNum, ccbench::RunnerOptions{},
+      [](size_t thid, const bool& quit, Backoff& /*unused*/) {
+        return TxExecutor(thid, &CCBenchResults[thid], quit);
+      },
+      [](TxExecutor& /*trans*/, size_t thid) {
+#ifdef Linux
+        setThreadAffinity(thid);
+#endif
+#if MASSTREE_USE
+        MasstreeWrapper<Tuple>::thread_init(int(thid));
+#endif
+      });
+
+  cout << "#ss2pl_thread_commit_counts:";
+  for (size_t thid = 0; thid < TotalThreadNum; ++thid) {
+    cout << (thid == 0 ? " " : ",")
+         << CCBenchResults[thid].local_commit_counts_;
+  }
+  cout << endl;
+
+#if SS2PL_WFG_DIAG
+  ss2pl_wfg_stop();
+#endif
+
+  return 0;
+} catch (const bad_alloc&) { ERR; }
```
