# C2' 40a7f4ac → F 25898d00 の unified diff (逐語、親が C2' の blob と退避 file から作成、job dir review/C2p-to-F.diff)

```diff
--- a/cc/mocc/transaction.cc
+++ b/cc/mocc/transaction.cc
@@ -25,10 +25,8 @@
 namespace {
 
 constexpr std::uint64_t izanagi_mocc_g2_magic = UINT64_C(0x495a);
-constexpr std::uint64_t izanagi_mocc_g2_txid_mask =
-    (UINT64_C(1) << 48) - 1;
-constexpr const char* izanagi_mocc_g2_marker =
-    "IZANAGI_MOCC_G2_WATERMARK_V1";
+constexpr std::uint64_t izanagi_mocc_g2_txid_mask = (UINT64_C(1) << 48) - 1;
+constexpr const char* izanagi_mocc_g2_marker = "IZANAGI_MOCC_G2_WATERMARK_V1";
 
 bool izanagi_mocc_g2_enabled() {
   static const bool enabled = [] {
@@ -88,9 +86,8 @@
   const bool has_producer = izanagi_mocc_g2_decode(read.body_, producer);
   const Tidword version = read.tidword_;
   auto& witness = izanagi_mocc_g2_stream(thid);
-  witness << "L " << reader_txid << ' '
-          << izanagi_trace::key_to_hex(read.key_) << ' ' << version.epoch << ' '
-          << version.tid << ' ';
+  witness << "L " << reader_txid << ' ' << izanagi_trace::key_to_hex(read.key_)
+          << ' ' << version.epoch << ' ' << version.tid << ' ';
   if (has_producer)
     witness << "T " << producer;
   else
@@ -106,13 +103,14 @@
   if (!izanagi_mocc_g2_decode(write.rcdptr_->body_, stored_producer))
     std::abort();
   izanagi_mocc_g2_stream(thid)
-      << "S " << writer_txid << ' '
-      << izanagi_trace::key_to_hex(write.key_) << ' ' << version.epoch << ' '
-      << version.tid << ' ' << stored_producer << '\n';
+      << "S " << writer_txid << ' ' << izanagi_trace::key_to_hex(write.key_)
+      << ' ' << version.epoch << ' ' << version.tid << ' ' << stored_producer
+      << '\n';
 }
 
 } // namespace
 #endif
+#line 115
 
 /**
  * @brief Search xxx set
@@ -1160,25 +1158,26 @@
   const std::uint64_t izanagi_txid = izanagi_trace::next_txid();
   const std::uint32_t izanagi_tx_type = izanagi_trace::tpcc_tx_type();
   if (izanagi_tx_type != 0) {
-    izanagi_trace::emit_commit_v3(
-        thid_, izanagi_txid, maxtid.epoch, maxtid.tid,
-        read_set_.size(), write_set_.size(), 0, 0, izanagi_tx_type);
+    izanagi_trace::emit_commit_v3(thid_, izanagi_txid, maxtid.epoch, maxtid.tid,
+                                  read_set_.size(), write_set_.size(), 0, 0,
+                                  izanagi_tx_type);
   } else {
-    izanagi_trace::stream(thid_) << "C " << izanagi_txid << ' ' << thid_ << ' '
-                               << maxtid.epoch << ' ' << maxtid.tid << ' '
-                               << read_set_.size() << ' ' << write_set_.size()
-                               << '\n';
+    izanagi_trace::stream(thid_)
+        << "C " << izanagi_txid << ' ' << thid_ << ' ' << maxtid.epoch << ' '
+        << maxtid.tid << ' ' << read_set_.size() << ' ' << write_set_.size()
+        << '\n';
   }
 
   for (auto& re : read_set_) {
     const Tidword v = re.tidword_;
     if (izanagi_tx_type != 0) {
-      izanagi_trace::emit_read_v3(
-          thid_, izanagi_txid, get_storage(re.storage_),
-          izanagi_trace::key_to_hex(re.key_), v.epoch, v.tid);
+      izanagi_trace::emit_read_v3(thid_, izanagi_txid, get_storage(re.storage_),
+                                  izanagi_trace::key_to_hex(re.key_), v.epoch,
+                                  v.tid);
     } else {
-      izanagi_trace::emit_read(
-        thid_, izanagi_txid, izanagi_trace::key_to_hex(re.key_), v.epoch, v.tid);
+      izanagi_trace::emit_read(thid_, izanagi_txid,
+                               izanagi_trace::key_to_hex(re.key_), v.epoch,
+                               v.tid);
     }
     if (izanagi_mocc_g2_enabled())
       izanagi_mocc_g2_emit_lineage(thid_, izanagi_txid, re);
@@ -1193,9 +1192,9 @@
           thid_, izanagi_txid, get_storage(we.storage_),
           izanagi_trace::key_to_hex(we.key_), op, maxtid.epoch, maxtid.tid);
     } else {
-      izanagi_trace::emit_write(
-        thid_, izanagi_txid, izanagi_trace::key_to_hex(we.key_), op,
-        maxtid.epoch, maxtid.tid);
+      izanagi_trace::emit_write(thid_, izanagi_txid,
+                                izanagi_trace::key_to_hex(we.key_), op,
+                                maxtid.epoch, maxtid.tid);
     }
   }
 
@@ -1216,9 +1215,9 @@
             thid_, izanagi_txid, get_storage(we.storage_),
             izanagi_trace::key_to_hex(we.key_), "not-locked-at-entry");
       } else {
-        izanagi_trace::emit_lock_violation(
-          thid_, izanagi_txid, izanagi_trace::key_to_hex(we.key_),
-          "not-locked-at-entry");
+        izanagi_trace::emit_lock_violation(thid_, izanagi_txid,
+                                           izanagi_trace::key_to_hex(we.key_),
+                                           "not-locked-at-entry");
       }
     }
   }
@@ -1242,8 +1241,8 @@
                 "lock-lost-before-write");
           } else {
             izanagi_trace::emit_lock_violation(
-              thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_),
-              "lock-lost-before-write");
+                thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_),
+                "lock-lost-before-write");
           }
         }
 #endif
@@ -1275,8 +1274,8 @@
                 "lock-lost-before-write");
           } else {
             izanagi_trace::emit_lock_violation(
-              thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_),
-              "lock-lost-before-write");
+                thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_),
+                "lock-lost-before-write");
           }
         }
 #endif
@@ -1295,12 +1294,11 @@
       if (izanagi_tx_type != 0) {
         izanagi_trace::emit_lock_violation_v3(
             thid_, izanagi_txid, get_storage((*itr).storage_),
-            izanagi_trace::key_to_hex((*itr).key_),
-            "lock-lost-before-publish");
+            izanagi_trace::key_to_hex((*itr).key_), "lock-lost-before-publish");
       } else {
         izanagi_trace::emit_lock_violation(
-          thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_),
-          "lock-lost-before-publish");
+            thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_),
+            "lock-lost-before-publish");
       }
     }
 #endif
--- a/cc/silo/transaction.cc
+++ b/cc/silo/transaction.cc
@@ -360,8 +360,10 @@
     storeRelease((*itr).rcdptr_->tidword_.obj_, desired.obj_);
   }
 #if TRACE
-  izanagi_trace::clear_shadow();  // abort/retry exit -> reset coverage shadow (D38, 裁定7)
+  izanagi_trace::
+      clear_shadow(); // abort/retry exit -> reset coverage shadow (D38, 裁定7)
 #endif
+#line 365
 }
 
 void TxExecutor::unlockWriteSet(
@@ -376,8 +378,10 @@
     storeRelease((*itr).rcdptr_->tidword_.obj_, desired.obj_);
   }
 #if TRACE
-  izanagi_trace::clear_shadow();  // partial unlock (retry/abort) -> reset shadow (D38, 裁定7)
+  izanagi_trace::
+      clear_shadow(); // partial unlock (retry/abort) -> reset shadow (D38, 裁定7)
 #endif
+#line 381
 }
 
 bool TxExecutor::validationPhase() { // Validation Phase
@@ -601,24 +605,25 @@
   const std::uint64_t izanagi_txid = izanagi_trace::next_txid();
   const std::uint32_t izanagi_tx_type = izanagi_trace::tpcc_tx_type();
   if (izanagi_tx_type != 0) {
-    izanagi_trace::emit_commit_v3(
-        thid_, izanagi_txid, maxtid.epoch, maxtid.tid,
-        read_set_.size(), write_set_.size(), 0, 0, izanagi_tx_type);
+    izanagi_trace::emit_commit_v3(thid_, izanagi_txid, maxtid.epoch, maxtid.tid,
+                                  read_set_.size(), write_set_.size(), 0, 0,
+                                  izanagi_tx_type);
   } else {
-    izanagi_trace::stream(thid_) << "C " << izanagi_txid << ' ' << thid_ << ' '
-                                 << maxtid.epoch << ' ' << maxtid.tid << ' '
-                                 << read_set_.size() << ' ' << write_set_.size()
-                                 << '\n';
+    izanagi_trace::stream(thid_)
+        << "C " << izanagi_txid << ' ' << thid_ << ' ' << maxtid.epoch << ' '
+        << maxtid.tid << ' ' << read_set_.size() << ' ' << write_set_.size()
+        << '\n';
   }
   for (auto& re : read_set_) {
     const Tidword v = re.get_tidword();
     if (izanagi_tx_type != 0) {
-      izanagi_trace::emit_read_v3(
-          thid_, izanagi_txid, get_storage(re.storage_),
-          izanagi_trace::key_to_hex(re.key_), v.epoch, v.tid);
+      izanagi_trace::emit_read_v3(thid_, izanagi_txid, get_storage(re.storage_),
+                                  izanagi_trace::key_to_hex(re.key_), v.epoch,
+                                  v.tid);
     } else {
-      izanagi_trace::emit_read(thid_, izanagi_txid, izanagi_trace::key_to_hex(re.key_),
-                               v.epoch, v.tid);
+      izanagi_trace::emit_read(thid_, izanagi_txid,
+                               izanagi_trace::key_to_hex(re.key_), v.epoch,
+                               v.tid);
     }
   }
   for (auto& we : write_set_) {
@@ -630,8 +635,9 @@
           thid_, izanagi_txid, get_storage(we.storage_),
           izanagi_trace::key_to_hex(we.key_), op, maxtid.epoch, maxtid.tid);
     } else {
-      izanagi_trace::emit_write(thid_, izanagi_txid, izanagi_trace::key_to_hex(we.key_),
-                                op, maxtid.epoch, maxtid.tid);
+      izanagi_trace::emit_write(thid_, izanagi_txid,
+                                izanagi_trace::key_to_hex(we.key_), op,
+                                maxtid.epoch, maxtid.tid);
     }
   }
   // Entry lock-coverage check (D38, 裁定4 point 1 = acquisition coverage).
@@ -736,7 +742,8 @@
   }
 
 #if TRACE
-  izanagi_trace::clear_shadow();  // success path -> reset coverage shadow (D38, 裁定7)
+  izanagi_trace::
+      clear_shadow(); // success path -> reset coverage shadow (D38, 裁定7)
   // E follows every entry/retention X check and clear_shadow(), so interruption
   // anywhere in the write loop leaves this v2 transaction detectably unterminated.
   izanagi_trace::stream(thid_) << "E " << izanagi_txid << '\n';
--- a/include/trace.hh
+++ b/include/trace.hh
@@ -108,14 +108,17 @@
 }
 inline void record_lock(const void* rcd) { lock_shadow().insert(rcd); }
 inline void clear_shadow() { lock_shadow().clear(); }
-inline bool holds_lock(const void* rcd) { return lock_shadow().count(rcd) != 0; }
+inline bool holds_lock(const void* rcd) {
+  return lock_shadow().count(rcd) != 0;
+}
 
 // A lock-coverage violation: writePhase wrote (or is about to write) a tuple
 // without holding its lock. reason in {not-locked-at-entry, lock-lost-before-write}.
 // The verifier maps X lines to Integrity.lock_coverage_violations -> indeterminate
 // (a torn-read window makes version stamps untrustworthy; not a cycle). D38.
 inline void emit_lock_violation(std::size_t thid, std::uint64_t txid,
-                                const std::string& key_hex, const char* reason) {
+                                const std::string& key_hex,
+                                const char* reason) {
   stream(thid) << "X " << txid << ' ' << key_hex << ' ' << reason << '\n';
 }
 
@@ -128,42 +131,36 @@
 inline void set_tpcc_tx_type(std::uint32_t value) {
   tpcc_tx_type_context() = value;
 }
-inline std::uint32_t tpcc_tx_type() {
-  return tpcc_tx_type_context();
-}
-inline void clear_tpcc_tx_type() {
-  tpcc_tx_type_context() = 0;
-}
+inline std::uint32_t tpcc_tx_type() { return tpcc_tx_type_context(); }
+inline void clear_tpcc_tx_type() { tpcc_tx_type_context() = 0; }
 
-inline void emit_commit_v3(
-    std::size_t thid, std::uint64_t txid,
-    std::uint64_t epoch, std::uint64_t tid,
-    std::size_t nR, std::size_t nW,
-    std::size_t nS, std::size_t nQ, std::uint32_t tx_type) {
+inline void emit_commit_v3(std::size_t thid, std::uint64_t txid,
+                           std::uint64_t epoch, std::uint64_t tid,
+                           std::size_t nR, std::size_t nW, std::size_t nS,
+                           std::size_t nQ, std::uint32_t tx_type) {
   stream(thid) << "C " << txid << ' ' << thid << ' ' << epoch << ' ' << tid
                << ' ' << nR << ' ' << nW << ' ' << nS << ' ' << nQ << ' '
                << tx_type << '\n';
 }
 
-inline void emit_read_v3(
-    std::size_t thid, std::uint64_t txid, std::uint32_t table,
-    const std::string& key_hex,
-    std::uint64_t ver_epoch, std::uint64_t ver_tid) {
+inline void emit_read_v3(std::size_t thid, std::uint64_t txid,
+                         std::uint32_t table, const std::string& key_hex,
+                         std::uint64_t ver_epoch, std::uint64_t ver_tid) {
   stream(thid) << "R " << txid << ' ' << table << ' ' << key_hex << ' '
                << ver_epoch << ' ' << ver_tid << '\n';
 }
 
-inline void emit_write_v3(
-    std::size_t thid, std::uint64_t txid, std::uint32_t table,
-    const std::string& key_hex, char op,
-    std::uint64_t epoch, std::uint64_t tid) {
+inline void emit_write_v3(std::size_t thid, std::uint64_t txid,
+                          std::uint32_t table, const std::string& key_hex,
+                          char op, std::uint64_t epoch, std::uint64_t tid) {
   stream(thid) << "W " << txid << ' ' << table << ' ' << key_hex << ' ' << op
                << ' ' << epoch << ' ' << tid << '\n';
 }
 
-inline void emit_lock_violation_v3(
-    std::size_t thid, std::uint64_t txid, std::uint32_t table,
-    const std::string& key_hex, const char* reason) {
+inline void emit_lock_violation_v3(std::size_t thid, std::uint64_t txid,
+                                   std::uint32_t table,
+                                   const std::string& key_hex,
+                                   const char* reason) {
   stream(thid) << "X " << txid << ' ' << table << ' ' << key_hex << ' '
                << reason << '\n';
 }
```
