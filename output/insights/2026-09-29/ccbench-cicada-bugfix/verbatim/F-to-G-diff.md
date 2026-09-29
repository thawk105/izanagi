# F `25898d00b9a6bbf09329ff8e8318c77d4f08b46e` → G `eb93423bbb27a2694d3d75861696c365f0fb8f7c` の commit (git show --format=fuller、逐語)

可逆の最小正規化 (git diff --check の末尾空白のため): 原文 4047 byte、sha256 `1f76b23b80f9263a3740dca184b1b0ed76ebfbde46ed1a2ede58dbf6ba700009`。行末の半角空白だけを 7 行で除いた (commit message の空行の字下げ 4 空白と、diff の空の文脈行の 1 空白)。復元: `git -C external/ccbench show --format=fuller eb93423bbb27a2694d3d75861696c365f0fb8f7c` を取り直す (可視文字は不変)。

```diff
commit eb93423bbb27a2694d3d75861696c365f0fb8f7c
Author:     thawk105 <thawk105@gmail.com>
AuthorDate: Tue Sep 29 23:03:38 2026 +0900
Commit:     thawk105 <thawk105@gmail.com>
CommitDate: Tue Sep 29 23:03:38 2026 +0900

    fix(cicada): repair non-default build options that no longer compile

    Three #if branches of Cicada fell out of step with the code around them
    and stopped compiling. None of them is enabled in the default build, so
    the default build and CI did not notice.

    1. INLINE_VERSION_OPT=1 with INLINE_VERSION_PROMOTION=1
       (cc/cicada/include/transaction.hh, inlineVersionPromotion):
       the promotion still called write(), which was renamed to update().
       GCC resolved the name to POSIX ::write(int, ...) and failed with
       "cannot convert 'Storage' to 'int'". It now calls update(). The
       promotion also appended the read to read_set_ a second time;
       read_internal() already records it before calling the promotion, so
       the second append is removed (in a read-only transaction the
       duplicate entry would be validated twice, and scan() would return
       the row twice).

    2. The same options with ADD_ANALYSIS=1 (cc/cicada/transaction.cc,
       read_internal): the promotion branch added "rdtscp() - start" to the
       read latency, but read_internal() has no start variable. read()
       already accounts for that latency, so the line is removed.

    3. WORKER1_INSERT_DELAY_RPHASE=1 (cc/cicada/transaction.cc, commit):
       the branch used the undeclared names thid, clock_delay and
       WORKER1_INSERT_DELAY_RPHASE_US. It now uses the member thid_,
       sleepTics() from include/util.hh (already included), and the runtime
       flag -worker1_insert_delay_rphase_us that README.md documents and
       util.cc prints, which the branch never read before.

    Every change replaces lines inside those #if branches; no line is added
    or removed, so the default build preprocesses to the same output and
    keeps its line numbers (ERR expands __LINE__ via NNN in
    include/debug.hh).

    AI-Agent: product=codex; model=gpt-6-sol; reasoning=medium; role=author
    AI-Agent: product=codex; model=gpt-6-sol; reasoning=medium; role=reviewer
    AI-Agent: product=claude; model=claude-opus-5-5-1m; reasoning=unknown; role=manager

diff --git a/cc/cicada/include/transaction.hh b/cc/cicada/include/transaction.hh
index dbaeb1b3c..cd4ab2a06 100644
--- a/cc/cicada/include/transaction.hh
+++ b/cc/cicada/include/transaction.hh
@@ -204,10 +204,10 @@ public:
         MinRts.load(std::memory_order_acquire) > ver->ldAcqWts() &&
         tuple->inline_ver_.status_.load(std::memory_order_acquire) ==
             VersionStatus::unused) {
-      write(s, key, TupleBody(ver->body_));
+      update(s, key, TupleBody(ver->body_));
       if (this->is_ronly_) {
         this->is_ronly_ = false;
-        read_set_.emplace_back(s, key, tuple, later_ver, ver);
+        (void) later_ver; // read_internal() already recorded this read.
       }
     }
   }
diff --git a/cc/cicada/transaction.cc b/cc/cicada/transaction.cc
index efcf02d75..fc708fd15 100644
--- a/cc/cicada/transaction.cc
+++ b/cc/cicada/transaction.cc
@@ -128,7 +128,7 @@ Version* TxExecutor::read_internal(Storage s, std::string_view key,
 #if INLINE_VERSION_OPT
 #if INLINE_VERSION_PROMOTION
 #if ADD_ANALYSIS
-  result_->local_read_latency_ += rdtscp() - start;
+  // No start timer here; read() times its own call.
 #endif // if ADD_ANALYSIS
   inlineVersionPromotion(s, key, tuple, later_ver, ver);
 #endif // if INLINE_VERSION_PROMOTION
@@ -921,8 +921,8 @@ bool TxExecutor::commit() {
    * Tanabe Optimization for analysis
    */
 #if WORKER1_INSERT_DELAY_RPHASE
-  if (unlikely(thid == 1) && WORKER1_INSERT_DELAY_RPHASE_US != 0) {
-    clock_delay(WORKER1_INSERT_DELAY_RPHASE_US * FLAGS_clocks_per_us);
+  if (unlikely(thid_ == 1) && FLAGS_worker1_insert_delay_rphase_us != 0) {
+    sleepTics(FLAGS_worker1_insert_delay_rphase_us * FLAGS_clocks_per_us);
   }
 #endif
```
