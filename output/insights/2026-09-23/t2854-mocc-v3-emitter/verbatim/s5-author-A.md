1) 変更の要約と差分

指定 clone の `cc/mocc/transaction.cc` だけを変更しました。C1' の HEAD は `6aa7a58fccff9efa218067d1b7ce83026a75357d` です。commit・index 更新は行っていません。

- 取引種別を一度読み、非 0 なら C/R/W と X 4 箇所を v3 helper、0 なら既存 v2 式で出力します。
- v3 の表番号は各要素の `storage_`、C の nS/nQ はともに 0 です。
- E の直後に context をクリアし、`#line 1206` で後続の論理行番号を復元しました。
- 既存 v2 式・呼出しは、関数名からセミコロンまで継続行の空白も含めて保持しました。分岐に合わせた先頭行の字下げのみ変更しています。

`git diff --stat` 全文:

```text
 cc/mocc/transaction.cc | 71 +++++++++++++++++++++++++++++++++++++++++++-------
 1 file changed, 61 insertions(+), 10 deletions(-)
```

`git diff` 全文:

```diff
diff --git a/cc/mocc/transaction.cc b/cc/mocc/transaction.cc
index e393efbf..30bea5c2 100644
--- a/cc/mocc/transaction.cc
+++ b/cc/mocc/transaction.cc
@@ -1158,15 +1158,28 @@ void TxExecutor::writePhase() {

 #if TRACE
   const std::uint64_t izanagi_txid = izanagi_trace::next_txid();
-  izanagi_trace::stream(thid_) << "C " << izanagi_txid << ' ' << thid_ << ' '
+  const std::uint32_t izanagi_tx_type = izanagi_trace::tpcc_tx_type();
+  if (izanagi_tx_type != 0) {
+    izanagi_trace::emit_commit_v3(
+        thid_, izanagi_txid, maxtid.epoch, maxtid.tid,
+        read_set_.size(), write_set_.size(), 0, 0, izanagi_tx_type);
+  } else {
+    izanagi_trace::stream(thid_) << "C " << izanagi_txid << ' ' << thid_ << ' '
                                << maxtid.epoch << ' ' << maxtid.tid << ' '
                                << read_set_.size() << ' ' << write_set_.size()
                                << '\n';
+  }

   for (auto& re : read_set_) {
     const Tidword v = re.tidword_;
-    izanagi_trace::emit_read(
+    if (izanagi_tx_type != 0) {
+      izanagi_trace::emit_read_v3(
+          thid_, izanagi_txid, get_storage(re.storage_),
+          izanagi_trace::key_to_hex(re.key_), v.epoch, v.tid);
+    } else {
+      izanagi_trace::emit_read(
         thid_, izanagi_txid, izanagi_trace::key_to_hex(re.key_), v.epoch, v.tid);
+    }
     if (izanagi_mocc_g2_enabled())
       izanagi_mocc_g2_emit_lineage(thid_, izanagi_txid, re);
   }
@@ -1175,9 +1188,15 @@ void TxExecutor::writePhase() {
     const char op = (we.op_ == OpType::INSERT)   ? 'I'
                     : (we.op_ == OpType::DELETE) ? 'D'
                                                  : 'U';
-    izanagi_trace::emit_write(
+    if (izanagi_tx_type != 0) {
+      izanagi_trace::emit_write_v3(
+          thid_, izanagi_txid, get_storage(we.storage_),
+          izanagi_trace::key_to_hex(we.key_), op, maxtid.epoch, maxtid.tid);
+    } else {
+      izanagi_trace::emit_write(
         thid_, izanagi_txid, izanagi_trace::key_to_hex(we.key_), op,
         maxtid.epoch, maxtid.tid);
+    }
   }

   for (auto& we : write_set_) {
@@ -1192,9 +1211,15 @@ void TxExecutor::writePhase() {
     }
     if (!izanagi_cll_has_writer ||
         we.rcdptr_->rwlock_.ldAcqCounter() != W_LOCKED) {
-      izanagi_trace::emit_lock_violation(
+      if (izanagi_tx_type != 0) {
+        izanagi_trace::emit_lock_violation_v3(
+            thid_, izanagi_txid, get_storage(we.storage_),
+            izanagi_trace::key_to_hex(we.key_), "not-locked-at-entry");
+      } else {
+        izanagi_trace::emit_lock_violation(
           thid_, izanagi_txid, izanagi_trace::key_to_hex(we.key_),
           "not-locked-at-entry");
+      }
     }
   }
 #endif
@@ -1209,10 +1234,18 @@ void TxExecutor::writePhase() {
 #if TRACE
         if (izanagi_mocc_g2_enabled())
           izanagi_mocc_g2_stamp((*itr).body_, izanagi_txid);
-        if ((*itr).rcdptr_->rwlock_.ldAcqCounter() != W_LOCKED)
-          izanagi_trace::emit_lock_violation(
+        if ((*itr).rcdptr_->rwlock_.ldAcqCounter() != W_LOCKED) {
+          if (izanagi_tx_type != 0) {
+            izanagi_trace::emit_lock_violation_v3(
+                thid_, izanagi_txid, get_storage((*itr).storage_),
+                izanagi_trace::key_to_hex((*itr).key_),
+                "lock-lost-before-write");
+          } else {
+            izanagi_trace::emit_lock_violation(
               thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_),
               "lock-lost-before-write");
+          }
+        }
 #endif
 #line 1169
         memcpy((*itr).rcdptr_->body_.get_val_ptr(), (*itr).body_.get_val_ptr(),
@@ -1234,10 +1267,18 @@ void TxExecutor::writePhase() {
         // Return value intentionally ignored: a missing key still needs the
         // record put on the GC queue below.
 #if TRACE
-        if ((*itr).rcdptr_->rwlock_.ldAcqCounter() != W_LOCKED)
-          izanagi_trace::emit_lock_violation(
+        if ((*itr).rcdptr_->rwlock_.ldAcqCounter() != W_LOCKED) {
+          if (izanagi_tx_type != 0) {
+            izanagi_trace::emit_lock_violation_v3(
+                thid_, izanagi_txid, get_storage((*itr).storage_),
+                izanagi_trace::key_to_hex((*itr).key_),
+                "lock-lost-before-write");
+          } else {
+            izanagi_trace::emit_lock_violation(
               thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_),
               "lock-lost-before-write");
+          }
+        }
 #endif
 #line 1187
         Masstrees[get_storage((*itr).storage_)].remove_value_if_present(
@@ -1250,10 +1291,18 @@ void TxExecutor::writePhase() {
     }
 #if TRACE
     if ((*itr).op_ != OpType::INSERT &&
-        (*itr).rcdptr_->rwlock_.ldAcqCounter() != W_LOCKED)
-      izanagi_trace::emit_lock_violation(
+        (*itr).rcdptr_->rwlock_.ldAcqCounter() != W_LOCKED) {
+      if (izanagi_tx_type != 0) {
+        izanagi_trace::emit_lock_violation_v3(
+            thid_, izanagi_txid, get_storage((*itr).storage_),
+            izanagi_trace::key_to_hex((*itr).key_),
+            "lock-lost-before-publish");
+      } else {
+        izanagi_trace::emit_lock_violation(
           thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_),
           "lock-lost-before-publish");
+      }
+    }
 #endif
 #line 1195
     __atomic_store_n(&((*itr).rcdptr_->tidword_.obj_), maxtid.obj_,
@@ -1266,7 +1315,9 @@ void TxExecutor::writePhase() {

 #if TRACE
   izanagi_trace::stream(thid_) << "E " << izanagi_txid << '\n';
+  izanagi_trace::clear_tpcc_tx_type();
 #endif
+#line 1206

   unlockCLL();
   RLL_.clear();
```

2) 自己確認の結果

実走した確認:

| command | rc | 結果 |
|---|---:|---|
| `python3 - <<'PY' … PY` による文字処理照合 | 0 | TRACE ブロックと `#line` を除いた全文、および残存行の論理行番号対応が C1' と一致 |
| 同スクリプトの正規表現照合 | 0 | v2 C/R/W/X/E の式・呼出し bytes が一致 |
| 同スクリプトの前後照合 | 0 | `writePhase` より前、および `commit` 以降が完全一致 |
| `git diff --check` | 0 | 指摘なし |
| `git diff --stat` / `git diff` | 0 | 上記の差分 |
| clone の `git status --short` / `git diff --name-only` | 0 | 変更は `cc/mocc/transaction.cc` のみ |
| clone の `git diff --cached --name-only` | 0 | 空 |
| superproject の `git status --short` | 0 | 空 |

文字処理は `git show HEAD:cc/mocc/transaction.cc` と編集後ファイルをメモリ上で比較しました。`#if TRACE` 内のネストを数えてブロックを除き、`#line N` は次行の論理番号を N に設定して照合しています。これは完全な C++ 前処理比較ではありません。

`#line` 対応表（引用内は空白を含む先頭最大 40 文字、`''` は空行）:

| file | N | 編集後の直後の行 | C1' の論理行 N |
|---|---:|---|---|
| `cc/mocc/transaction.cc` | 17 | `''` | `''` |
| 同上 | 990 | `'  sort(write_set_.begin(), write_set_.en'` | `'  sort(write_set_.begin(), write_set_.en'` |
| 同上 | 991 | `'  for (auto itr = write_set_.begin(); it'` | `'  for (auto itr = write_set_.begin(); it'` |
| 同上 | 1158 | `''` | `''` |
| 同上 | 1169 | `'        memcpy((*itr).rcdptr_->body_.get'` | `'        memcpy((*itr).rcdptr_->body_.get'` |
| 同上 | 1187 | `'        Masstrees[get_storage((*itr).sto'` | `'        Masstrees[get_storage((*itr).sto'` |
| 同上 | 1195 | `'    __atomic_store_n(&((*itr).rcdptr_->t'` | `'    __atomic_store_n(&((*itr).rcdptr_->t'` |
| 同上 | 1206 | `''` | `''` |

既存 7 本の値は保持し、1206 だけを追加しています。

前処理は、C1' と編集後の各本文を標準入力に渡して、それぞれ次を実走しました。

```sh
g++ -std=c++17 -E -P -DTRACE=0 -x c++ -iquote cc/mocc -
```

両方とも **rc=1**。以下の include 不足で停止したため、一致とは判定していません。

```text
cc/mocc/include/../../../include/masstree_wrapper.hh:20:10:
fatal error: config.h: No such file or directory
```

TRACE=0/1 の警告ゼロ、構文検査、build・link・実行、binary 比較、trace/witness/content 検査、変異検査は **実装済み・未実走**です。

3) 裁定 §2 から外れた箇所と理由

なし。

4) 所有外への波及の静的列挙

`cc/mocc/CMakeLists.txt` では共通ソース `transaction.cc`・`util.cc`・`lock.cc` が 4 workload に指定されています。今回変更した `transaction.cc` の compile entry は次の 4 target に波及します。

| target | workload の TU |
|---|---|
| `ycsb_mocc` | `cc/mocc/ycsb_mocc.cc` |
| `tpcc_mocc` | `cc/mocc/tpcc_mocc.cc` |
| `bomb_mocc` | `cc/mocc/bomb_mocc.cc` |
| `sbomb_mocc` | `cc/mocc/sbomb_mocc.cc` |

これらのファイルと header は編集していません。

TRACE=1 で確認すべき追加箇所は、`izanagi_tx_type` の宣言・参照、C/R/W/X の helper 呼出し、`get_storage(...)` の引数型、および追加した分岐です。静的には次を確認しています。

- `izanagi_tx_type` は全 4 target の共通コードで使用され、workload による未使用変数にはなりません。
- read/write 要素は `OpElement` から `Storage storage_` を継承し、`get_storage` の戻り値は helper が受ける `std::uint32_t` です。
- 全追加分岐は波括弧付きです。既存 v2 呼出しの継続行の空白は bytes 保持のためそのままです。
- TRACE=0 では追加した C++ はすべて除去対象です。

警告の有無はコンパイラで未確認のため、警告ゼロとは報告しません。

## 総括

- 実装済み: 指定 1 file の v3 切替、既存 v2 呼出し保持、E 後の context クリア、論理行番号復元。
- 確認済み: TRACE 部分を除く本文・論理行番号の一致、v2 式の bytes 保持、変更範囲、`git diff --check`。
- 未実走: 正常完了する前処理比較、TRACE=0/1 の警告・構文検査、build・link・実行、binary・trace・変異検査。
- 親が計算ノードで確認すること: 裁定 §3 の実 flag による 21 entry の前処理・include 活性・構文検査、TRACE=0 binary 比較、TPC-C/YCSB の witness・内容・認定と登録変異。D297 合格および TPC-C certified は主張していません。