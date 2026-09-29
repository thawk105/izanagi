## 変更内容 (diff 全文)

[cc/mocc/transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/moccfix-a/output/runs/moccfix/ccbench/cc/mocc/transaction.cc:1061) の validation の read set 走査だけを変更しました。

```diff
diff --git a/cc/mocc/transaction.cc b/cc/mocc/transaction.cc
index cc1c72877..a914efa11 100644
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

## 検査の実走結果

以下の `<clone>` は `/work/1/SFC/tanab/izanagi/.codex/worktrees/moccfix-a/output/runs/moccfix/ccbench` です。

| 実走した command | rc | 出力の要点 |
|---|---:|---|
| `git -C <clone> diff --stat` | 0 | `cc/mocc/transaction.cc \| 17 ++++++++++++++++-`、1 file changed |
| `git -C <clone> diff -- cc/mocc/transaction.cc` | 0 | 全文を上に掲載。validation 内の 1 hunk のみ |
| `git -C <clone> diff --name-only` | 0 | `cc/mocc/transaction.cc` のみ |
| `cd <clone> && /usr/bin/clang-format --dry-run --Werror cc/mocc/transaction.cc` | 0 | 出力なし。編集前も rc=0 |
| `git -C <clone> diff --check` | 0 | 出力なし |
| `cd <clone> && /usr/bin/g++-11 -std=c++20 -fsyntax-only -DRWLOCK -DTRACE=0 -I. -Iinclude -Icc/mocc cc/mocc/transaction.cc` | 1 | `config.h: No such file or directory` |
| 同じ command の `-DTRACE=1` | 1 | 同じ `config.h` 欠落 |

**構文検査は実装済み・未実走**です。両設定ともコンパイラ起動は試しましたが、第三者ヘッダー `config.h` の欠落で対象 TU の構文検査には到達していません。clone 内の `config.h` 検索も該当なしでした。

## 受理集合への影響

現行の版不一致と writer lock による拒否は維持しました。変更後は、それらを通過しても、lock 検査後の再読で epoch または tid が `check` と異なる取引を追加で拒否します。lock 検査後に別取引が publish した場合も追加拒否になり得ます。`max_rset_` には検査済みの `check` を使います。有限幅の版が周回する場合まで ABA 不在を保証するものではありません。

## 所有外への波及

- `patches/`: 既往の診断 patch は旧 `max_rset_` 行を context に含むため、適用可否の再確認が必要です。patch 自体は未変更・未検査です。既存の `#line` 値は維持しました。
- trace 区間: `#if TRACE` の行は未変更です。TRACE=0/1 の構文検査は上記理由で未完了です。
- 他 protocol: 変更 path は MOCC の 1 file のみです。Silo を含む他 protocol のコードは未変更です。

## 総括

裁定 R1〜R3 に沿う修理を 1 file に実装し、差分範囲と clang-format を確認しました。commit、branch、reset、checkout、push は行っていません。