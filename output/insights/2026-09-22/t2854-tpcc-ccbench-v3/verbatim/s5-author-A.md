指定 clone 内の3ファイルに裁定 §2 を実装しました。変更は未 commit です。superproject の tracked file、`external/ccbench/`、Git index／HEAD は変更していません。

### 1) 変更の要約と差分全文

- `trace.hh`: TU 間で共有する inline TLS context と v3 C/R/W/X helper を追加。既存行は不変。
- `tpcc.hh`: TRACE 限定 include、begin 直後の setter、成功 commit 後の quit 判定の TRACE 限定除外を追加。
- Silo: context による排他的な v2/v3 選択、X 3箇所の選択、E 直後の clear、元行番号の復元を追加。P、validation、begin／abort、INSERT の X 除外は不変。

`git diff --stat`:

```text
 cc/silo/transaction.cc | 84 ++++++++++++++++++++++++++++++++++++++------------
 include/tpcc.hh        | 12 ++++++++
 include/trace.hh       | 49 +++++++++++++++++++++++++++++
 3 files changed, 126 insertions(+), 19 deletions(-)
```

`git diff -- include/trace.hh include/tpcc.hh cc/silo/transaction.cc` 全文:

```diff
diff --git a/cc/silo/transaction.cc b/cc/silo/transaction.cc
index 054a7e5f..4434447d 100644
--- a/cc/silo/transaction.cc
+++ b/cc/silo/transaction.cc
@@ -599,21 +599,40 @@ void TxExecutor::writePhase() {
   // outside this change's permitted edit surface, so Silo writes its v2 C line
   // directly while the existing R/W helpers remain unchanged.
   const std::uint64_t izanagi_txid = izanagi_trace::next_txid();
-  izanagi_trace::stream(thid_) << "C " << izanagi_txid << ' ' << thid_ << ' '
-                               << maxtid.epoch << ' ' << maxtid.tid << ' '
-                               << read_set_.size() << ' ' << write_set_.size()
-                               << '\n';
+  const std::uint32_t izanagi_tx_type = izanagi_trace::tpcc_tx_type();
+  if (izanagi_tx_type != 0) {
+    izanagi_trace::emit_commit_v3(
+        thid_, izanagi_txid, maxtid.epoch, maxtid.tid,
+        read_set_.size(), write_set_.size(), 0, 0, izanagi_tx_type);
+  } else {
+    izanagi_trace::stream(thid_) << "C " << izanagi_txid << ' ' << thid_ << ' '
+                                 << maxtid.epoch << ' ' << maxtid.tid << ' '
+                                 << read_set_.size() << ' ' << write_set_.size()
+                                 << '\n';
+  }
   for (auto& re : read_set_) {
     const Tidword v = re.get_tidword();
-    izanagi_trace::emit_read(thid_, izanagi_txid, izanagi_trace::key_to_hex(re.key_),
-                             v.epoch, v.tid);
+    if (izanagi_tx_type != 0) {
+      izanagi_trace::emit_read_v3(
+          thid_, izanagi_txid, get_storage(re.storage_),
+          izanagi_trace::key_to_hex(re.key_), v.epoch, v.tid);
+    } else {
+      izanagi_trace::emit_read(thid_, izanagi_txid, izanagi_trace::key_to_hex(re.key_),
+                               v.epoch, v.tid);
+    }
   }
   for (auto& we : write_set_) {
     const char op = (we.op_ == OpType::INSERT)   ? 'I'
                     : (we.op_ == OpType::DELETE) ? 'D'
                                                  : 'U';
-    izanagi_trace::emit_write(thid_, izanagi_txid, izanagi_trace::key_to_hex(we.key_),
-                              op, maxtid.epoch, maxtid.tid);
+    if (izanagi_tx_type != 0) {
+      izanagi_trace::emit_write_v3(
+          thid_, izanagi_txid, get_storage(we.storage_),
+          izanagi_trace::key_to_hex(we.key_), op, maxtid.epoch, maxtid.tid);
+    } else {
+      izanagi_trace::emit_write(thid_, izanagi_txid, izanagi_trace::key_to_hex(we.key_),
+                                op, maxtid.epoch, maxtid.tid);
+    }
   }
   // Entry lock-coverage check (D38, 裁定4 point 1 = acquisition coverage).
   // Every non-INSERT write must be covered, right now at writePhase entry, by a
@@ -626,12 +645,19 @@ void TxExecutor::writePhase() {
     Tidword cur;
     cur.obj_ = loadAcquire(we.rcdptr_->tidword_.obj_);
     if (!cur.lock || !izanagi_trace::holds_lock(we.rcdptr_)) {
-      izanagi_trace::emit_lock_violation(thid_, izanagi_txid,
-                                         izanagi_trace::key_to_hex(we.key_),
-                                         "not-locked-at-entry");
+      if (izanagi_tx_type != 0) {
+        izanagi_trace::emit_lock_violation_v3(
+            thid_, izanagi_txid, get_storage(we.storage_),
+            izanagi_trace::key_to_hex(we.key_), "not-locked-at-entry");
+      } else {
+        izanagi_trace::emit_lock_violation(thid_, izanagi_txid,
+                                           izanagi_trace::key_to_hex(we.key_),
+                                           "not-locked-at-entry");
+      }
     }
   }
 #endif
+#line 635

 #if WAL
   wal(maxtid.obj_);
@@ -649,12 +675,21 @@ void TxExecutor::writePhase() {
         {
           Tidword cur;
           cur.obj_ = loadAcquire((*itr).rcdptr_->tidword_.obj_);
-          if (!cur.lock)
-            izanagi_trace::emit_lock_violation(
-                thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_),
-                "lock-lost-before-write");
+          if (!cur.lock) {
+            if (izanagi_tx_type != 0) {
+              izanagi_trace::emit_lock_violation_v3(
+                  thid_, izanagi_txid, get_storage((*itr).storage_),
+                  izanagi_trace::key_to_hex((*itr).key_),
+                  "lock-lost-before-write");
+            } else {
+              izanagi_trace::emit_lock_violation(
+                  thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_),
+                  "lock-lost-before-write");
+            }
+          }
         }
 #endif
+#line 658
         memcpy((*itr).rcdptr_->body_.get_val_ptr(), (*itr).body_.get_val_ptr(),
                (*itr).body_.get_val_size());
         storeRelease((*itr).rcdptr_->tidword_.obj_, maxtid.obj_);
@@ -670,12 +705,21 @@ void TxExecutor::writePhase() {
         {
           Tidword cur;
           cur.obj_ = loadAcquire((*itr).rcdptr_->tidword_.obj_);
-          if (!cur.lock)
-            izanagi_trace::emit_lock_violation(
-                thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_),
-                "lock-lost-before-write");
+          if (!cur.lock) {
+            if (izanagi_tx_type != 0) {
+              izanagi_trace::emit_lock_violation_v3(
+                  thid_, izanagi_txid, get_storage((*itr).storage_),
+                  izanagi_trace::key_to_hex((*itr).key_),
+                  "lock-lost-before-write");
+            } else {
+              izanagi_trace::emit_lock_violation(
+                  thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_),
+                  "lock-lost-before-write");
+            }
+          }
         }
 #endif
+#line 679
         maxtid.absent = true;
         // Return value intentionally ignored: a missing key still needs the
         // tid bump and gc_records_ push below.
@@ -696,7 +740,9 @@ void TxExecutor::writePhase() {
   // E follows every entry/retention X check and clear_shadow(), so interruption
   // anywhere in the write loop leaves this v2 transaction detectably unterminated.
   izanagi_trace::stream(thid_) << "E " << izanagi_txid << '\n';
+  izanagi_trace::clear_tpcc_tx_type();
 #endif
+#line 700
   gc_records();
   read_set_.clear();
   write_set_.clear();
diff --git a/include/tpcc.hh b/include/tpcc.hh
index 5cd9c7f7..24e7d132 100644
--- a/include/tpcc.hh
+++ b/include/tpcc.hh
@@ -24,6 +24,10 @@
 #include "./tpcc/tpcc_tx_orderstatus.hh"
 #include "./tpcc/tpcc_tx_delivery.hh"
 #include "./tpcc/tpcc_tx_stocklevel.hh"
+#if TRACE
+#include "trace.hh"
+#endif
+#line 27

 template <typename Tuple, typename Param>
 class TPCCWorkload {
@@ -53,6 +57,10 @@ public:
     if (loadAcquire(tx.quit_)) return;

     tx.begin();
+#if TRACE
+    izanagi_trace::set_tpcc_tx_type(get_tx_type(query.type));
+#endif
+#line 56

     switch (query.type) {
       case TxType::NewOrder:
@@ -107,7 +115,11 @@ public:
       goto RETRY;
     }

+#if !TRACE
+#line 110
     if (loadAcquire(tx.quit_)) return;
+#endif
+#line 111
     tx.result_->local_commit_counts_++;
     tx.result_->local_commit_counts_per_tx_[get_tx_type(query.type)]++;

diff --git a/include/trace.hh b/include/trace.hh
index 570e35e3..1ff95bce 100644
--- a/include/trace.hh
+++ b/include/trace.hh
@@ -119,6 +119,55 @@ inline void emit_lock_violation(std::size_t thid, std::uint64_t txid,
   stream(thid) << "X " << txid << ' ' << key_hex << ' ' << reason << '\n';
 }

+// TPC-C v3 frames (T-2854); TRACE-only per D14 and absolute discipline #1.
+// External-linkage inline accessor shares this thread's context across TUs.
+inline std::uint32_t& tpcc_tx_type_context() {
+  static thread_local std::uint32_t value{0};
+  return value;
+}
+inline void set_tpcc_tx_type(std::uint32_t value) {
+  tpcc_tx_type_context() = value;
+}
+inline std::uint32_t tpcc_tx_type() {
+  return tpcc_tx_type_context();
+}
+inline void clear_tpcc_tx_type() {
+  tpcc_tx_type_context() = 0;
+}
+
+inline void emit_commit_v3(
+    std::size_t thid, std::uint64_t txid,
+    std::uint64_t epoch, std::uint64_t tid,
+    std::size_t nR, std::size_t nW,
+    std::size_t nS, std::size_t nQ, std::uint32_t tx_type) {
+  stream(thid) << "C " << txid << ' ' << thid << ' ' << epoch << ' ' << tid
+               << ' ' << nR << ' ' << nW << ' ' << nS << ' ' << nQ << ' '
+               << tx_type << '\n';
+}
+
+inline void emit_read_v3(
+    std::size_t thid, std::uint64_t txid, std::uint32_t table,
+    const std::string& key_hex,
+    std::uint64_t ver_epoch, std::uint64_t ver_tid) {
+  stream(thid) << "R " << txid << ' ' << table << ' ' << key_hex << ' '
+               << ver_epoch << ' ' << ver_tid << '\n';
+}
+
+inline void emit_write_v3(
+    std::size_t thid, std::uint64_t txid, std::uint32_t table,
+    const std::string& key_hex, char op,
+    std::uint64_t epoch, std::uint64_t tid) {
+  stream(thid) << "W " << txid << ' ' << table << ' ' << key_hex << ' ' << op
+               << ' ' << epoch << ' ' << tid << '\n';
+}
+
+inline void emit_lock_violation_v3(
+    std::size_t thid, std::uint64_t txid, std::uint32_t table,
+    const std::string& key_hex, const char* reason) {
+  stream(thid) << "X " << txid << ' ' << table << ' ' << key_hex << ' '
+               << reason << '\n';
+}
+
 } // namespace izanagi_trace

 #endif // TRACE
```

### 2) 自己確認

実行場所はすべて指定 clone。比較元は `e9e477ca1b55348ab4530de0b1cf663ce4555290`。

| 実走 command | rc | 結果 |
|---|---:|---|
| `git rev-parse HEAD` | 0 | 指定 pin と一致 |
| `git show 68106660686232781bca3be792a750d3e19d7a8a -- cc/mocc/transaction.cc` | 0 | 7本の復元先例を確認 |
| `python3 - <<'PY' … PY`（文字処理・元行照合） | 0 | 下記静的 assertion が全件成功 |
| `git diff --check` | 0 | 空白エラーなし |
| `git diff --name-only` | 0 | 指定3ファイルだけ |
| `git diff --stat`／上記 `git diff` | 0 | 掲載した差分 |
| `rg -n` による include／追加識別子検索 | 0 | consumer と識別子を確認 |

文字処理では、両版から `#if TRACE` ブロックと `#line` を除き、`#if !TRACE` は本体を保持して wrapper を除去しました。3ファイルとも残る文字列が完全一致しました。これは依存 header を展開した前処理比較ではありません。

さらに次を確認しました。

- `trace.hh` は追加 API 部分だけを除去すると pin の全 bytes に一致。
- v2 R/W/X の既存呼出しは字下げを除き一致。旧 `emit_lock_violation(` は3箇所とも残存。
- C は同一の `if/else` で片方だけ出力。採番は従来の1箇所。
- `ERR` の論理行番号は `tpcc.hh:88`、Silo `transaction.cc:106`／`:690` のまま。

`#line` の照合結果です。引用内は先頭空白を含む最大40文字、`""` は空行です。全件、行全体でも一致しています。

| file | 値 | 直後の物理行の先頭40文字 | pin の N 行目の先頭40文字 |
|---|---:|---|---|
| `include/tpcc.hh` | 27 | `""` | `""` |
| `include/tpcc.hh` | 56 | `""` | `""` |
| `include/tpcc.hh` | 110 | `"    if (loadAcquire(tx.quit_)) return;"` | `"    if (loadAcquire(tx.quit_)) return;"` |
| `include/tpcc.hh` | 111 | `"    tx.result_->local_commit_counts_++;"` | `"    tx.result_->local_commit_counts_++;"` |
| `cc/silo/transaction.cc` | 635 | `""` | `""` |
| `cc/silo/transaction.cc` | 658 | `"        memcpy((*itr).rcdptr_->body_.get"` | `"        memcpy((*itr).rcdptr_->body_.get"` |
| `cc/silo/transaction.cc` | 679 | `"        maxtid.absent = true;"` | `"        maxtid.absent = true;"` |
| `cc/silo/transaction.cc` | 700 | `"  gc_records();"` | `"  gc_records();"` |

単体前処理は、ファイルを書き出さず、Python の subprocess から pin／候補の本文をそれぞれ stdin に渡しました。実行 argv は次です。`<親directory>` は `include` または `cc/silo`。

```text
g++ -std=c++17 -E -P -DTRACE=0 -x c++ \
    -iquote <親directory> -Iinclude -Icc/silo -
```

| 入力 | pin rc | 候補 rc | 結果 |
|---|---:|---:|---|
| `include/trace.hh` | 0 | 0 | stdout 完全一致、各8 bytes |
| `include/tpcc.hh` | 1 | 1 | `gflags/gflags.h` 不足で失敗 |
| `cc/silo/transaction.cc` | 1 | 1 | Masstree が要求する `config.h` 不足で失敗 |

header 単体を stdin の主入力にしたため、両 header には両版とも `#pragma once in main file` 警告が出ています。警告0の build を実証したものではありません。失敗2件の部分出力は一致の証拠に数えていません。

**実装済み・未実走:** TRACE=0／1 の `-Wall -Wextra -Werror` build、全21 consumer entry の前処理／include 活性比較と TRACE=1 構文検査、TU 間 TLS 共有の実行確認、binary 比較、trace／witness／内容検査、YCSB 認定、D1・M1〜M5。build・link・benchmark は実行していません。D297 checker も実行せず、pass は主張しません。

### 3) 裁定 §2 からの逸脱

なし。

### 4) 所有外への波及の静的列挙

`tpcc.hh` の直接 consumer は以下の9 TU です。TRACE=1 では全てに context setter と成功 commit の計数修正が入ります。

```text
cc/cicada/tpcc_cicada.cc:16
cc/ermia/tpcc_ermia.cc:15
cc/mocc/tpcc_mocc.cc:13
cc/mvto/tpcc_mvto.cc:14
cc/oze/tpcc_oze.cc:14
cc/si/tpcc_si.cc:15
cc/silo/tpcc_silo.cc:16
cc/ss2pl/tpcc_ss2pl.cc:12
cc/tictoc/tpcc_tictoc.cc:12
```

既存の `trace.hh` 直接 consumer は以下の3 TU です。

```text
cc/silo/transaction.cc:9
cc/si/transaction.cc:13
cc/mocc/transaction.cc:15
```

候補では `tpcc.hh` 経由でも TRACE=1 に限り `trace.hh` が入ります。plan の期待集合は12 source／21 compile entry で、compile database による実照合は未実走です。

追加識別子の検索では、定義・使用は今回の3ファイル内だけでした。新 API は `izanagi_trace` 内の外部 linkage の inline 関数で、件数は `std::size_t`、表・種別は `std::uint32_t` を使用しています。静的には名前衝突や未使用変数の要因を認めませんが、生成 header／実 flag を含む警告0の確認は未実走です。

他 protocol は v3 helper を呼びません。共有 workload の setter により context は設定されますが、裁定どおり workload 側には clear を追加しておらず、次の試行の begin 直後に上書きされます。他 protocol の source と既存 emitter は変更していません。

## 総括

- 指定3ファイルに裁定 §2 を実装。v2 の式・旧 X 呼出しを保持し、v3 は1 txn に C を1本出す排他的分岐にした。
- 静的な既存コード照合、8本の `#line` 照合、`git diff --check` は成功。`trace.hh` 単体の TRACE=0 前処理も一致。
- 残る2ファイルの単体前処理は依存 header 不足で失敗。build・link・実行・認定は未実走。
- 親は計算ノードで全21 entry、両 TRACE build の警告0、binary 同一性、TPC-C の構造・witness・内容、YCSB v2 認定、D1・M1〜M5 を確認すること。