## 成果物

すべて [genopt_gl_scratch](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch) 内に作成しました。sha256 と行数は最終状態の値です。

| file・目的 | 行数 | sha256 |
|---|---:|---|
| [instr-silo-gate-witness.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/patches/instr-silo-gate-witness.patch) — Q/S 計装 | 149 | `61c64c1318c1efef8e8fc9061a9a8be112c5697b8e6384af0f5659ef19f5227d` |
| [broken-silo-b1-unregistered-first-read.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/patches/broken-silo-b1-unregistered-first-read.patch) — B1 変異 | 73 | `1820fc37c03e2215b5d0b967c50f3fdbfd3e6d6c86ccc54b2778442b067ee8d1` |
| [fix-silo-intra-txn-values.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/patches/fix-silo-intra-txn-values.patch) — Silo 修正案 | 35 | `2fca96512edab25ed5d097fb201b2d975782a7c8ef607e0adc50fba4f8618c3b` |
| [gate_check.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/gate_check.py) — Q/S と trace の照合 | 221 | `5583c1d9fd79d8191a4207a864d0800c634c4d3ce54f006427ca530de3e10202` |
| [test_gate_check.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/test_gate_check.py) —手製 fixture の自走 test | 107 | `64e236967a6b2dfb9e642747f19f8b4f499cbe7a4785e4ff38c1f46abbee38e9` |
| [launch_gate_liveness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/launch_gate_liveness.py) —計算ノード起動器 | 212 | `dda4e78ae1bae03692b8b85387fbb1a6cc39d8b5a2341ae5a56eaa7855c9f086` |
| [fmt_check.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/fmt_check.py) —全体 format 比較 | 84 | `142e3f9f97f101d81fab2fe7d4f0eac80477ee2d051ad4fbf31413e71e924288` |
| [make_patches.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/make_patches.py) — patch 再生成 | 197 | `1c1cbc85821fa18502b7f17c55d6c084577da6c5baf4105e290b9cca7842bfaf` |
| [verify_patches.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/verify_patches.py) —厳密適用・TRACE 除去検査 | 67 | `642428ce61a15a1c24cf49de92ba2cfa7c349bd8e10eea2c57e1c34d2e54cb3b` |
| [mutation_check.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/mutation_check.py) —照合器の比較除去検査 | 29 | `efdbc19dc016b80c52845f60556e54962e6809e647f352ce5f80de22aa7d54ce` |
| [patch-check.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/patch-check.json) —適用検査結果 | 45 | `257add6c581b3baaf2083fedcc6b94e7937a3d681486cc7b9f6f0dac5a3927a6` |
| [fmt-result.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/fmt-result.json) — format 検査結果 | 1727 | `a3ef652076bc6cb9ad950c4784d35d60b7cb648c3e3e3cc0b8c9cb7f6f9bae74` |

## patch の hunk

行番号は pin のものです。

- 計装: `include/trace.hh:28,73` に gate stream、直前の commit txid、Q/S helper。`include/ycsb.hh:13,105,124,139,163` に TRACE 限定の include、試行ごとの手順初期化、READ・WRITE・RMW の刻印、commit 後の Q。`cc/silo/transaction.cc:599,655` に txid 保持と UPDATE の memcpy 入力からの S。
- B1: `cc/silo/transaction.cc:1,52,229,713` に副 buffer と計数、begin での初期化、偶数 key の未登録一貫読み、commit 直前の read set 確認。
- 修正案: `cc/silo/transaction.cc:208` で read の write set 優先、`:526` で同一 key の後続 update が `body_` を置換。

## 静的検査と自走 test

`git apply --check` は複製 tree で、次の全段が **rc=0、stderr 先頭は空**でした。

| 順序 | 各 patch の rc |
|---|---|
| 計装 | `0` |
| 計装 → B1 | `0 → 0` |
| 計装 → 修正 | `0 → 0` |
| 修正単独 | `0` |

計装後の `include/trace.hh`、`include/ycsb.hh`、`cc/silo/transaction.cc` は、TRACE 枝を除いた bytes がそれぞれ pin と一致しました。

`python3 genopt_gl_scratch/test_gate_check.py` を実走し、`test_valid_and_abort_attempt_excluded`、`test_q_missing`、`test_q_extra`、`test_s_missing`、`test_s_extra`、`test_s_w_key_mismatch`、`test_stamp_out_of_range`、`test_d1_a`、`test_d1_b1`、`test_d1_b2`、`test_d2b_i`、`test_d2b_ii`、`test_malformed_q` の **13 PASS、0 FAIL**。D1(b1) の比較を一時除去すると `test_d1_b1`、D2b(ii) を一時除去すると `test_d2b_ii` が各 rc=1 で赤になりました。変更は一時ファイル内だけで、元の照合器は変更していません。

## format 検査

`fmt_check.py` を login で実走しました。対象は 213 files。clang-format 14 の警告は **pin 46 件 → pin＋修正 46 件**、修正行に掛かる警告は 0 件です。内訳は pin で MOCC transaction 26、Silo transaction 17、trace.hh 3。全体 CI 相当の format 判定は pin＋修正でも赤です。

## 起動器と外部交点

起動器は**実装済み・未実走**です。build・benchmark・計算ノード投入は行っていません。計算ノードでは `stock`、`b1`、`fix` ごとに checkout と patch 適用、TRACE build、W-rmw/W-blind、既存 verifier と照合器を実行し、`<out-dir>/result.json`・`meta.json`、各 run の stdout/stderr、verifier 出力、gate JSON、trace tar.gz を残す形です。CMake 引数は `STOCK_G.cmake_defines()`、`CCBENCH_TRACE=1`、Release、sanitizer OFF、policy の C/C++ compiler と依存物の `FETCHCONTENT_SOURCE_DIR_*`。fix の CI 比較だけは pin と pin＋修正で全体 build を別 checkout に行います。

import 先の signature は、[s3_mocc_lock_coverage.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/orchestrator/campaign/s3_mocc_lock_coverage.py:120) の `_load_policy(path)`、`:147` の `_resolve_toolchain(policy)`、`:224` の `_prepare_dependencies(root, policy, cache_root, scratch, toolchain)`、[silo_policy_coverage.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/orchestrator/campaign/silo_policy_coverage.py:740) の `_prepare_build_dependencies(scratch, toolchain, dependencies)`、[patchharness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/orchestrator/campaign/patchharness.py:174) の `assert_pinned_clean(sub, pin_commit)` と `:346` の `checkout(pin_commit, base_dir)`、[pipeline.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/orchestrator/campaign/pipeline.py:326) の `_parse_abort_counts(stdout)` と `:351` の `_parse_commit_witness(stdout)`、[site_policy.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/orchestrator/campaign/site_policy.py:66) の `current_site(require_evidence=False)`、`:95` の `refuses_heavy_work(site)`、`:130` の `default_build_jobs(site)` を読んで確認しました。[s2_verify_calibration.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/orchestrator/campaign/s2_verify_calibration.py:140) の `_assert_free_disk(path)` と、同 module が import する `_assert_single_tenant()` も使用します。これら repo の file は編集していません。

## 未解決の照合点と作業木

指定された未使用 tag の grep では、`Q` は既存 trace 出力に見つかりませんでした。一方、**`S` は既存の MOCC 計装に存在します**（[cc/mocc/transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/external/ccbench/cc/mocc/transaction.cc:109)）。その出力先は `witness_<thid>.log` で、今回の Silo の `gate_<thid>.log` とは別です。「CCBench の `#if TRACE` 内で S が未使用」という裁定の確認条件は、逐語では満たせません。この点を親の一次資料へ引き継ぐ必要があります。

最終確認の出力は、`git -C external/ccbench status --porcelain` が**空**、`git status --porcelain` も**空**でした。

## 総括

scratch 内の実装と login で許された検査は完了しました。計算ノードでの実走結果と、既存 MOCC の `S` tag に関する裁定条件の扱いは親の後続作業に残ります。