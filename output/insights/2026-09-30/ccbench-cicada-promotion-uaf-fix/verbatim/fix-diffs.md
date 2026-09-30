# CCBench 修理差分 4 本 (Codex author、土台 aa8e36f1 から fix1 → fix4 の順に当たる)

commit は CCBench の local branch izanagi-cicada-promotion-uaf-fix (tip 16ad3eb8ca5f7bb3aea789bff99958e2192f6714)。bundle は job dir の tip.bundle。

## fix1-promotion-ronly.patch (sha256 eac73cb9900fb2bfad6c06a3e22ac5ee7ba2aec3797458845837208b034bde90)

```diff
diff --git a/cc/cicada/include/transaction.hh b/cc/cicada/include/transaction.hh
index cd4ab2a06..57a22fece 100644
--- a/cc/cicada/include/transaction.hh
+++ b/cc/cicada/include/transaction.hh
@@ -202,14 +202,14 @@ public:
                               Version* later_ver, Version* ver) {
     if (ver != &(tuple->inline_ver_) &&
         MinRts.load(std::memory_order_acquire) > ver->ldAcqWts() &&
+        !is_ronly_ &&
         tuple->inline_ver_.status_.load(std::memory_order_acquire) ==
             VersionStatus::unused) {
+      // Read-only transactions use an rts snapshot and do not validate reads;
+      // promotion would turn that snapshot read into an unvalidated write.
       update(s, key, TupleBody(ver->body_));
-      if (this->is_ronly_) {
-        this->is_ronly_ = false;
-        (void) later_ver; // read_internal() already recorded this read.
-      }
     }
+    (void) later_ver; // read_internal() already recorded this read.
   }
 #endif
 #endif
```

commit message:

```text
fix(cicada): avoid promotion in read-only transactions

Read-only transactions choose versions at rts and do not validate their
read set (Cicada paper, section 3.1). Inline version promotion turned such
a transaction into a read-write one in the middle of its read phase. The
reads it had already made keep later_ver_ pointers taken at rts, and
validation starts its re-check from them; when that later version was
aborted, the re-check walks down to the version that was read and skips a
committed version whose wts lies between rts and wts, so a stale read
passes validation. With INLINE_VERSION_OPT=1 and
INLINE_VERSION_PROMOTION=1 the serializability checker found G2 cycles on
small YCSB runs; all 52 representative witnesses it reported (in four
runs) contained a transaction that passed validation this way, and
disabling promotion in read-only transactions removed the cycles in the
same runs. Keep read-only transactions read-only; read-write transactions
still promote.

AI-Agent: product=codex; model=gpt-6-sol; reasoning=medium; role=author
AI-Agent: product=codex; model=gpt-6-sol; reasoning=medium; role=reviewer
AI-Agent: product=claude; model=claude-opus-5-5-1m; reasoning=not-exposed; role=manager
Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
```

## fix2-promotion-update-body.patch (sha256 64759cbba21dd60961ca4b93f9d4174cafb466df98c621fe4ed7f476f409eab8)

```diff
diff --git a/cc/cicada/include/cicada_op_element.hh b/cc/cicada/include/cicada_op_element.hh
index d18eb9efd..aebbbfb78 100644
--- a/cc/cicada/include/cicada_op_element.hh
+++ b/cc/cicada/include/cicada_op_element.hh
@@ -32,6 +32,9 @@ public:
 
   Version *later_ver_, *new_ver_;
   bool finish_version_install_;
+#if INLINE_VERSION_OPT && INLINE_VERSION_PROMOTION
+  bool from_promotion_ = false;
+#endif
 
   WriteElement(Storage s, std::string_view key, T* rcdptr, Version* later_ver,
                Version* new_ver, OpType op)
diff --git a/cc/cicada/include/transaction.hh b/cc/cicada/include/transaction.hh
index 57a22fece..bc41edaed 100644
--- a/cc/cicada/include/transaction.hh
+++ b/cc/cicada/include/transaction.hh
@@ -208,6 +208,11 @@ public:
       // Read-only transactions use an rts snapshot and do not validate reads;
       // promotion would turn that snapshot read into an unvalidated write.
+      const size_t write_set_size = write_set_.size();
       update(s, key, TupleBody(ver->body_));
+      if (status_ != TransactionStatus::aborted &&
+          write_set_.size() == write_set_size + 1) {
+        write_set_.back().from_promotion_ = true;
+      }
     }
     (void) later_ver; // read_internal() already recorded this read.
   }
diff --git a/cc/cicada/transaction.cc b/cc/cicada/transaction.cc
index 67fdd1d43..562df0f25 100644
--- a/cc/cicada/transaction.cc
+++ b/cc/cicada/transaction.cc
@@ -202,7 +202,14 @@ Status TxExecutor::update(Storage s, std::string_view key, TupleBody&& body) {
    * Update  from local write set.
    * Special treat due to performance.
    */
+#if INLINE_VERSION_OPT && INLINE_VERSION_PROMOTION
+  if (auto* we = searchWriteSet(s, key)) {
+    if (we->from_promotion_) { we->new_ver_->body_ = std::move(body); }
+    goto FINISH_WRITE;
+  }
+#else
   if (searchWriteSet(s, key)) goto FINISH_WRITE;
+#endif
 
   Tuple* tuple;
   bool rmw;
```

commit message:

```text
fix(cicada): apply updates after inline version promotion

Promotion adds a write element holding a copy of the body that was read.
A later update() of the same key in the same transaction found that
element and returned without using the requested body, so the
transaction's own write was lost. On small TPC-C runs, failed order
inserts were about 16 to 22 times as frequent as with promotion
disabled, and at or below that level with this change. Mark the element that
promotion adds and move the body of a later update into its pending
version. Other repeated updates keep their current behavior.

AI-Agent: product=codex; model=gpt-6-sol; reasoning=medium; role=author
AI-Agent: product=codex; model=gpt-6-sol; reasoning=medium; role=reviewer
AI-Agent: product=claude; model=claude-opus-5-5-1m; reasoning=not-exposed; role=manager
Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
```

## fix3-abort-insert-uaf.patch (sha256 beb381298f40ab0bcad76f0fcf8a42046260e82866bfdb73669e638a7c2a54f5)

```diff
diff --git a/cc/cicada/transaction.cc b/cc/cicada/transaction.cc
index 562df0f25..5312bf7ba 100644
--- a/cc/cicada/transaction.cc
+++ b/cc/cicada/transaction.cc
@@ -753,14 +753,16 @@ void TxExecutor::gcpv() {
  */
 void TxExecutor::abort() {
   // remove inserted records
+  std::vector<Tuple*> inserted_tuples;
   for (auto& we : write_set_) {
     if (we.op_ == OpType::INSERT) {
+      inserted_tuples.push_back(we.rcdptr_);
       Masstrees[get_storage(we.storage_)].remove_value(we.key_);
-      delete we.rcdptr_;
     }
   }
 
   writeSetClean();
+  for (Tuple* tuple : inserted_tuples) { delete tuple; }
   read_set_.clear();
   node_map_.clear();
 
```

commit message:

```text
fix(cicada): clean inserted versions before freeing tuples on abort

abort() deleted the tuples it had inserted and then called
writeSetClean(), which still stores to their continuing_commit_ (and,
with INLINE_VERSION_OPT=1, to their inline version). AddressSanitizer
reports this as a heap-use-after-free. Save the inserted tuples, remove
their index entries, clean the write set, then free them. The pointers
have to be saved because writeSetClean() clears the write set.

AI-Agent: product=codex; model=gpt-6-sol; reasoning=medium; role=author
AI-Agent: product=codex; model=gpt-6-sol; reasoning=medium; role=reviewer
AI-Agent: product=claude; model=claude-opus-5-5-1m; reasoning=not-exposed; role=manager
Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
```

## fix4-inline-insert-init.patch (sha256 a5575bd4babfba59b361c0ceebb4be9e95550ab9a896342c923d16545e94726b)

```diff
diff --git a/cc/cicada/include/tuple.hh b/cc/cicada/include/tuple.hh
index 1d5e61f3b..9892b3e5f 100644
--- a/cc/cicada/include/tuple.hh
+++ b/cc/cicada/include/tuple.hh
@@ -99,8 +99,8 @@ public:
     continuing_commit_.store(0, std::memory_order_release);
 
 #if INLINE_VERSION_OPT
-    latest_ = &inline_ver_;
-    body_ = std::ref(inline_ver_.body_);
+    latest_ = ver;
+    body_ = std::ref(ver->body_);
 #else
     latest_.store(ver, std::memory_order_release);
     body_ = std::ref((latest_.load(std::memory_order_acquire))->body_);
```

commit message:

```text
fix(cicada): initialize inserted tuples from the inserted version

A new Tuple's inline version starts as pending, so insert() cannot take
it and allocates the new version outside the tuple. With
INLINE_VERSION_OPT=1, Tuple::init() ignored that version, made the empty
inline version the latest one and copied its body, which asks for a
zero-size allocation with alignment 0 and throws std::bad_alloc from
insert() (TPC-C runs aborted, also with promotion disabled). Use the
inserted version as the latest
version and take the body from it, as the non-inline branch does.

AI-Agent: product=codex; model=gpt-6-sol; reasoning=medium; role=author
AI-Agent: product=codex; model=gpt-6-sol; reasoning=medium; role=reviewer
AI-Agent: product=claude; model=claude-opus-5-5-1m; reasoning=not-exposed; role=manager
Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
```
