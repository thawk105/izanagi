[patches/instr-si-trace-v2.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/patches/instr-si-trace-v2.patch) の C 行で、`thid_` を `std::size_t` に変換して数値として出力するよう直しました。patch 全文です。

```diff
diff --git a/cc/si/transaction.cc b/cc/si/transaction.cc
--- a/cc/si/transaction.cc
+++ b/cc/si/transaction.cc
@@ -526,7 +526,15 @@ void TxExecutor::si_commit() {
   // intact (cleared just below).
   {
     const std::uint64_t txid = izanagi_trace::next_txid();
-    izanagi_trace::emit_commit(thid_, txid, 1, this->cstamp_);
+    // SI trace v2: C <txid> <thid> <epoch> <tid> <read_count> <write_count>,
+    // followed by the existing R/W records and E <txid>. emit_commit remains
+    // the v1 helper in trace.hh. Counts come from the same R/W containers,
+    // so they are not an independent witness.
+    izanagi_trace::stream(thid_) << "C " << txid << ' '
+                                 << static_cast<std::size_t>(thid_) << ' '
+                                 << 1 << ' ' << this->cstamp_ << ' '
+                                 << read_set_.size() << ' ' << write_set_.size()
+                                 << '\n';
     for (auto& re : read_set_) {
       const std::uint32_t vc = re.ver_->cstamp_.load(std::memory_order_acquire);
       izanagi_trace::emit_read(thid_, txid, izanagi_trace::key_to_hex(re.key_),
@@ -545,5 +553,6 @@ void TxExecutor::si_commit() {
       izanagi_trace::emit_write(thid_, txid, izanagi_trace::key_to_hex(we.key_),
                                 op, 1, this->cstamp_);
     }
+    izanagi_trace::stream(thid_) << "E " << txid << '\n';
   }
 #endif
```

型を確認しました。`thid_` は [transaction.hh:30](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/external/ccbench/cc/si/include/transaction.hh:30) の `uint8_t` です。`txid` は [transaction.cc:539](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/external/ccbench/cc/si/transaction.cc:539) の `std::uint64_t`、`next_txid()` の戻り値も [trace.hh:45](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/external/ccbench/include/trace.hh:45) で `uint64_t` です。`cstamp_` は [transaction.hh:31](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/external/ccbench/cc/si/include/transaction.hh:31) の `uint32_t`、epoch の `1` は整数リテラル、件数は [transaction.hh:39](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/external/ccbench/cc/si/include/transaction.hh:39) の `vector` の `size()` が返す整数型です。E 行も数値型の `txid` を出力します。R/W 行は変更していません。

検査結果は `git -C external/ccbench apply --check` が **rc 0**、scratch に適用して `#if TRACE` ブロックを除いた比較が `TRACE blocks removed: base=1, patched=1; outside bytes equal: True` でした。scratch は削除済みで、`external/ccbench` の作業木は clean です。

## 総括

変更は指定の patch だけです。指示どおり build・run、`git add`・`git commit` は実行していません。