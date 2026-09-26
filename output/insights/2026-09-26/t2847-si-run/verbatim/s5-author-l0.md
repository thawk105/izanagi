SI の trace v2 patch と L0 起動器を作成しました。現行 SI の C 行は 5 field の v1 形式で、[parser](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/orchestrator/verifier/parse.py:359) が明示的に拒否します。今回の patch は C を 7 field にし、R/W の後に必須の E 行を出します。

### Patch 全文

[patches/instr-si-trace-v2.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/patches/instr-si-trace-v2.patch)

```diff
diff --git a/cc/si/transaction.cc b/cc/si/transaction.cc
--- a/cc/si/transaction.cc
+++ b/cc/si/transaction.cc
@@ -526,7 +526,14 @@ void TxExecutor::si_commit() {
   // intact (cleared just below).
   {
     const std::uint64_t txid = izanagi_trace::next_txid();
-    izanagi_trace::emit_commit(thid_, txid, 1, this->cstamp_);
+    // SI trace v2: C <txid> <thid> <epoch> <tid> <read_count> <write_count>,
+    // followed by the existing R/W records and E <txid>. emit_commit remains
+    // the v1 helper in trace.hh. Counts come from the same R/W containers,
+    // so they are not an independent witness.
+    izanagi_trace::stream(thid_) << "C " << txid << ' ' << thid_ << ' '
+                                 << 1 << ' ' << this->cstamp_ << ' '
+                                 << read_set_.size() << ' ' << write_set_.size()
+                                 << '\n';
     for (auto& re : read_set_) {
       const std::uint32_t vc = re.ver_->cstamp_.load(std::memory_order_acquire);
       izanagi_trace::emit_read(thid_, txid, izanagi_trace::key_to_hex(re.key_),
@@ -545,5 +552,6 @@ void TxExecutor::si_commit() {
       izanagi_trace::emit_write(thid_, txid, izanagi_trace::key_to_hex(we.key_),
                                 op, 1, this->cstamp_);
     }
+    izanagi_trace::stream(thid_) << "E " << txid << '\n';
   }
 #endif
```

`git -C external/ccbench apply --check <patch の絶対パス>` は **rc 0**。scratch に適用して `#if TRACE` ブロックを除いた全文を比較した結果は `TRACE blocks removed: base=1, patched=1; outside bytes equal: True` でした。scratch は削除済みです。patch に裸の `IZANAGI_*` token はありません。

### 起動器

[.t2847-launcher/launch_si_run.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/.t2847-launcher/launch_si_run.py) は untracked のままです。呼び出し形は次のとおりです。

```text
/usr/bin/python3.10 launch_si_run.py --job L0 --third-party-cache <abs> --out-dir <abs> --repo-root <abs> [--dry-run]
```

`py_compile` と `--help` は rc 0。指定された引数での dry-run も rc 0 で、出力は次のとおりです。

```json
{
  "job": "L0",
  "source_oid": "68106660686232781bca3be792a750d3e19d7a8a",
  "builds": [
    {
      "build": "V2",
      "macro": null,
      "patches": [
        {
          "path": "/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/patches/instr-si-trace-v2.patch",
          "sha256": "6206a14f10a3d6532d7a7896b2b5537e03f69c54d185367c0732e8d6baf16cbe",
          "touch_set": ["cc/si/transaction.cc"],
          "apply_check": {"rc": 0, "stderr": ""}
        }
      ],
      "cells": ["K-t1", "K-t4", "W-t1", "W-t4"]
    }
  ]
}
```

起動器は [_load_policy・_resolve_toolchain・_prepare_dependencies](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/orchestrator/campaign/s3_mocc_lock_coverage.py:120)、[checkout・assert_pinned_clean・patch_files・apply_patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/orchestrator/campaign/patchharness.py:155)、[_assert_single_tenant と実行定数](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/orchestrator/campaign/s3_mocc_mutation_proof.py:45)、[current_site・refuses_heavy_work](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/orchestrator/campaign/site_policy.py:66) を import します。X/P/I 状態は [verifier の評価関数](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/orchestrator/verifier/model.py:233) から記録します。

局所版は patch 適用、SI target の build、run、verify、行数集計、結果要約です。run の argv 形・`IZANAGI_TRACE_DIR`・trace dir を cwd とする点・120 秒 timeout・非ゼロ rc の扱いは [mocc の `_run_trace`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/orchestrator/campaign/s3_mocc_mutation_proof.py:200) に合わせました。verify は同 driver の `_verify` と同じ CLI 形で `--protocol si` を渡します。判定は verifier CLI に委ね、verifier・parser・driver・条件 gate は編集していません。SI の flag は [YCSB 定義](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/external/ccbench/include/ycsb.hh:20) と [SI 共通定義](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/external/ccbench/cc/si/include/common.hh:33) に存在し、[SI 実行体](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/external/ccbench/cc/si/ycsb_si.cc:23) が gflags を解析します。

波及を静的に確認しました。`patches/*.patch` を読む [裸マクロ登録 test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/orchestrator/tests/test_p3_s4_loop.py:8491) と [define inventory test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/orchestrator/tests/test_ccbench_spawn_sites.py:666) は、この patch に新しい define がないため登録追加を要しません。[mocc template test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-l0/orchestrator/tests/test_mocc_template_proof.py:94) の glob にも入りますが、mocc marker は追加していません。patch 一覧と README の一致を要求する test は見つかりませんでした。これらの test は実走していません。

## 総括

**patch と起動器は実装済み・未実走**です。build・benchmark・verify の実測は、指定どおり親による計算ノード実行を待ちます。`git add` と `git commit` は実行していません。