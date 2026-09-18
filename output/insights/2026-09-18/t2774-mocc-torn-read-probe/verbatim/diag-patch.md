# 診断 patch の逐語 (job dir probe/mocc-close-version-counter-gap.patch)

sha256 `8a25bd0a5687437269c720cb34a4b26024a6f1f119adf1c16281d455b9ecaa1d`、1168 byte。
可逆最小正規化 (可視文字不変): 原文 (job dir `probe/mocc-close-version-counter-gap.patch`、上記 sha256 と byte 数) では unified diff の空 context 行が半角空白 1 個 (`" "`) であるが、`git diff --check` の末尾空白検出を避けるため本写しでは 3 行を空行にした。復元法 = fence 内の空行の先頭に半角空白 1 個を補う。

```diff
diff --git a/cc/mocc/transaction.cc b/cc/mocc/transaction.cc
--- a/cc/mocc/transaction.cc
+++ b/cc/mocc/transaction.cc
@@ -349,6 +349,13 @@
       b = TupleBody(tuple->body_.get_key(), tuple->body_.get_val(),
                     tuple->body_.get_val_align());

+#ifdef RWLOCK
+      if (tuple->rwlock_.ldAcqCounter() == W_LOCKED) {
+        status_ = TransactionStatus::aborted;
+        return Status::ERROR_LOCK_FAILED;
+      }
+#endif
+#line 350
       desired.obj_ = __atomic_load_n(&(tuple->tidword_.obj_), __ATOMIC_ACQUIRE);
       if (expected == desired)
         break;
@@ -1061,6 +1068,19 @@
     }
 #endif // RWLOCK

+    Tidword check_after_counter;
+    check_after_counter.obj_ =
+        __atomic_load_n(&((*itr).rcdptr_->tidword_.obj_), __ATOMIC_ACQUIRE);
+    if (check_after_counter.epoch != check.epoch ||
+        check_after_counter.tid != check.tid) {
+      (*itr).failed_verification_ = true;
+      this->status_ = TransactionStatus::aborted;
+#if ADD_ANALYSIS
+      ++result_->local_validation_failure_by_tid_;
+#endif
+      return false;
+    }
+#line 1038
     this->max_rset_ = max(this->max_rset_, (*itr).rcdptr_->tidword_);
   }

```
