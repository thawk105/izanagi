# F `25898d00` → X `f4a5169e` の差分 (judge2 の成果物 `F-to-X.diff` の逐語、sha256 1741eaa6a27ba361c384b6d45665a92ac7ad17e7dae18fc94c0ce10d2a28bf8f)

```diff
diff --git a/cc/mocc/transaction.cc b/cc/mocc/transaction.cc
index cc1c728..a914efa 100644
--- a/cc/mocc/transaction.cc
+++ b/cc/mocc/transaction.cc
@@ -1058,7 +1058,22 @@ bool TxExecutor::validation() {
     }
 #endif // RWLOCK

-    this->max_rset_ = max(this->max_rset_, (*itr).rcdptr_->tidword_);
+    // Version and writer lock are separate words. Recheck the version after
+    // the lock read to catch a writer that published and unlocked meanwhile.
+    Tidword check_after_lock;
+    check_after_lock.obj_ =
+        __atomic_load_n(&((*itr).rcdptr_->tidword_.obj_), __ATOMIC_ACQUIRE);
+    if (check_after_lock.epoch != check.epoch ||
+        check_after_lock.tid != check.tid) {
+      (*itr).failed_verification_ = true;
+      this->status_ = TransactionStatus::aborted;
+#if ADD_ANALYSIS
+      ++result_->local_validation_failure_by_tid_;
+#endif
+      return false;
+    }
+
+    this->max_rset_ = max(this->max_rset_, check);
   }

   // validate the node set
```
