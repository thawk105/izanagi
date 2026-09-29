## 変更内容

- [transaction.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-a/output/runs/md19-cicada-fix/ccbench/cc/cicada/include/transaction.hh:201): 未使用になる `later_ver` を無名引数にし、207 行の `write()` を `update()` に変更。210 行の重複した `read_set_` 追加をコメントに置換しました。
- [transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-a/output/runs/md19-cicada-fix/ccbench/cc/cicada/transaction.cc:131): 未定義の `start` を使う計上行をコメントに置換。924–925 行で worker 番号、runtime flag、待機関数を裁定どおり修正しました。

差分は **2 ファイル・6 行置換**、directive の変更なし、物理行数は F と同じ **375／986 行**です。commit はしていません。最終差分の全文は次のとおりです。

```diff
diff --git a/cc/cicada/include/transaction.hh b/cc/cicada/include/transaction.hh
index dbaeb1b3c..d54b7fca9 100644
--- a/cc/cicada/include/transaction.hh
+++ b/cc/cicada/include/transaction.hh
@@ -199,15 +199,15 @@ public:
 #if INLINE_VERSION_OPT
 #if INLINE_VERSION_PROMOTION
   void inlineVersionPromotion(Storage s, std::string_view key, Tuple* tuple,
-                              Version* later_ver, Version* ver) {
+                              Version* /*later_ver*/, Version* ver) {
     if (ver != &(tuple->inline_ver_) &&
         MinRts.load(std::memory_order_acquire) > ver->ldAcqWts() &&
         tuple->inline_ver_.status_.load(std::memory_order_acquire) ==
             VersionStatus::unused) {
-      write(s, key, TupleBody(ver->body_));
+      update(s, key, TupleBody(ver->body_));
       if (this->is_ronly_) {
         this->is_ronly_ = false;
-        read_set_.emplace_back(s, key, tuple, later_ver, ver);
+        // read_internal() already recorded this read in read_set_.
       }
     }
   }
diff --git a/cc/cicada/transaction.cc b/cc/cicada/transaction.cc
index efcf02d75..499dd8545 100644
--- a/cc/cicada/transaction.cc
+++ b/cc/cicada/transaction.cc
@@ -128,7 +128,7 @@ Version* TxExecutor::read_internal(Storage s, std::string_view key,
 #if INLINE_VERSION_OPT
 #if INLINE_VERSION_PROMOTION
 #if ADD_ANALYSIS
-  result_->local_read_latency_ += rdtscp() - start;
+  // read() already accounts for local read latency.
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

以下、相対パスの基点は `R/ccbench` です。

| command・範囲 | rc・結果 |
|---|---|
| `git diff --stat`、`git diff`、`git diff --numstat`、`git status --short`、`git diff --check` | 全て 0。変更は指定の 2 ファイルのみ。stat は `2 files changed, 6 insertions(+), 6 deletions(-)` |
| `wc -l cc/cicada/include/transaction.hh cc/cicada/transaction.cc` | 0。375／986 行で F と一致 |
| `/usr/bin/clang-format --dry-run --Werror`、対象 2 ファイル | 0。clang-format 14.0.0 |
| `git ls-files -- cc include common \| grep -E '\.(cc\|hh\|cpp)$' \| xargs /usr/bin/clang-format --dry-run --Werror` | 0。対象 **213 ファイル** |
| `python3 ../tmp/preprocess_compare.py` | 0。`#include` 行を除き、CMake 既定 macro・`TRACE=0` で `g++ -E -P -x c++` を実行。両ファイル × `ADD_ANALYSIS=0/1` の **4 比較全て F と byte 一致** |
| `g++-11 -std=c++17 -fsyntax-only -I. -Icc/cicada -I/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree -DADD_ANALYSIS=0 -DTRACE=0 -DBACK_OFF=1 -DKEY_SIZE=8 -DMASSTREE_USE=1 -DVAL_SIZE=4 -DINLINE_VERSION_OPT=0 -DINLINE_VERSION_PROMOTION=1 -DREUSE_VERSION=1 -DSINGLE_EXEC=0 -DWRITE_LATEST_ONLY=0 -DWORKER1_INSERT_DELAY_RPHASE=0 -DPARTITION_TABLE=0 -DLinux cc/cicada/transaction.cc` | **1**。`cc/cicada/include/common.hh:15:10: fatal error: gflags/gflags.h: No such file or directory` |

## 未実走・残る懸念

構文検査は既定文脈の依存 header 不足で止まりました。したがって、F/G の 4 文脈の構文検査は**未実走**であり、非既定分岐が compile を通るとは報告できません。cache には gflags・glog の生成前 `.h.in` があり、確認した system include path に完成 header はありませんでした。

所有外への静的な波及箇所は、`include/ycsb.hh` の `is_ronly_` 設定、Cicada の `include/common.hh`・`util.cc`・`CMakeLists.txt`・`README.md` の flag 定義と表示です。`patches/` では trace、TPC-C trace、version-lifetime、broken 系 4 本、forwarding 系 2 本が対象ファイルに hunk を持ちます。特に trace patch の `#line 200/909/934` と commit 付近の context、version-lifetime patch の同じ commit 冒頭の待機追加に注意が必要です。**patch 適用可否は実測していません。** これら所有外ファイルは編集していません。

## 総括

R1〜R3 の指定置換と行数・整形・既定前処理の確認は完了しました。構文検査だけは `gflags/gflags.h` 不足により判定不能です。