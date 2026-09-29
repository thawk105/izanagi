## 変更内容

- [transaction.hh:201](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-a/output/runs/md19-cicada-fix/ccbench/cc/cicada/include/transaction.hh:201): 引数行を F と同じ `Version* later_ver, Version* ver) {` に戻しました。[210行](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-a/output/runs/md19-cicada-fix/ccbench/cc/cicada/include/transaction.hh:210) は、重複登録せずに引数を使用済みにする1文と理由のコメントにしました。
- [transaction.cc:131](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-a/output/runs/md19-cicada-fix/ccbench/cc/cicada/transaction.cc:131): 計時開始値がないため計上行を除いた、と分かるコメントに直しました。

F（`25898d00`）との差分全文です。

```diff
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

## 実走した command と rc

以下の `ccbench` は `R/ccbench`、`applycheck` は `R/tmp/applycheck` です。

| command | rc・結果 |
|---|---|
| `git diff --stat`、`git diff 25898d00`、`git diff --check 25898d00`、`git status --short` | 全て 0。変更は所有する2ファイルだけ。Fとの差分は5行置換 |
| `wc -l` と `git show 25898d00:<path> \| wc -l` | 全て 0。`transaction.hh` は双方375行、`transaction.cc` は双方986行 |
| `/usr/bin/clang-format --dry-run --Werror cc/cicada/include/transaction.hh cc/cicada/transaction.cc` | 0。clang-format 14 |
| `git ls-files -- cc include common \| grep -E '\.(cc\|hh\|cpp)$' \| xargs /usr/bin/clang-format --dry-run --Werror` | 0。対象213ファイル |
| `python3 ../tmp/preprocess_compare.py` | 0。`g++ -E -P -x c++` による2ファイル×`ADD_ANALYSIS=0/1`の4比較すべて、Fとbyte一致 |
| `cp -a R/ccbench/. R/tmp/applycheck/` | 0 |
| `git apply --check -v patches/instr-cicada-trace.patch`（`applycheck`） | 0。4ファイルの `Checking patch` を表示、offset表示なし |
| `git apply patches/instr-cicada-trace.patch`（`applycheck`） | 0 |
| `git apply --check -v patches/instr-cicada-trace-tpcc.patch`（計装適用後の`applycheck`） | 0。2ファイルの `Checking patch` を表示、offset表示なし |

`git apply` は fuzz なしで照合しました。元の `R/ccbench` に計装 patch は当てていません。

## 未実走・残る懸念

今回の変更後の構文検査、build、実行時検証は実走していません。前回の構文検査は `gflags/gflags.h` 不足で止まっており、レビューにある親の4文脈の構文検査結果を今回の実走結果には数えていません。

## 総括

指定箇所を修正し、行数・整形・既定文脈の不変と、計装 patch 2本の順次適用可能性を確認しました。commit はしていません。