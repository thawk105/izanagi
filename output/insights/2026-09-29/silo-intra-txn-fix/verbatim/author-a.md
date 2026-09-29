## 変更内容

作業場所は `output/runs/silo-fix` 配下のみです。repo の tracked file と `patches/` は変更していません。clone に commit は残していません。

| File | 内容 | SHA-256 |
|---|---|---|
| [cc/silo/transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/ccbench/cc/silo/transaction.cc) | 指定 patch の 2 hunk を適用 | `481628c119ffab56da68dde2d1558d7f5ae165b47556e3733eb1db6da77b4ec0` |
| [commit-msg.txt](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/commit-msg.txt) | 英語 commit message の下書き | `134ba9841c057530c1c446c2b23087c2b5dc4b3acb88b6f35b35e1a0e07c831f` |
| [instr-silo-gate-witness-F.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/patches/instr-silo-gate-witness-F.patch) | F 向け計装 | `76a4234dc0f76518b2ee8b124d7d4c2eeacc3f6a063fdf420714a09afc458cd6` |
| [launch_gate_liveness_v2.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/scripts/launch_gate_liveness_v2.py) | 2 build × 2 workload 起動器 | `8054937a9d0115b3a2a9c297fe4d699bd22a08f0fbbb798979a9887a3bfbca49` |
| [run_judge_v2.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/scripts/run_judge_v2.sh) | D297 の 2 比較 × GCC 11・12 | `a42de160d6747bfe18b4a49eb958bdbc09273ddf21fa742457ec2274d09fc0d5` |
| [run_ci_build_v2.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/scripts/run_ci_build_v2.sh) | 親 OID を引数化 | `69eefbb291ef4117463fa7c27fd399c838ca9d8d95226491cfbab3026aefca34` |
| [run_ci_then_judge.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/scripts/run_ci_then_judge.sh) | CI と D297 を順に起動 | `9711f226eadfd91ed130731b6e2a61f5e8682dd0b109ac3b3f064c8690124479` |
| [inventory_silo_patches.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/scripts/inventory_silo_patches.py) | 棚卸し script | `eab33d8d08b0628e9dfa109801e5853aa0d43de50a2a488322d79300c024184a` |
| [check_instr_v2.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/scripts/check_instr_v2.py) | 計装の自己確認 script | `f5ee4771881337288860bc9ac103d02aaa5fb064c2c7ea29731a6f5ba2367b79` |

## 計装の再配置

[計装 patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/patches/instr-silo-gate-witness-F.patch:1) は、`include/ycsb.hh` の read・write・RMW と commit 後に Q 用の操作記録を置き、RMW の `val_` コピー後に `id_` を刻印します。`cc/silo/transaction.cc` では F の YCSB 側 commit 枝（元 file の 609 行付近）で txid を対応付け、UPDATE の `memcpy` 直前（696 行付近）でその時点の `body_` 先頭 8 byte を V に出します。追加部分は `#if TRACE` 内です。

## 棚卸しの結果

**分類件数と B・C・D・E の patch 名は未取得です。** 自己走は誤った一時 commit OID を渡したため `invalid reference` で rc=1 となり、分類前に停止しました。正しい一時 commit OID は `e7164bded8e32ce66e9f170bcbb6ffd6fa2311a6` でした。一時 branch と commit を除去し、clone は F detached、`cc/silo/transaction.cc` の指定修正だけが未 commit の状態へ戻しました。

## 実走した command と rc

- `git apply ../patches/fix-silo-intra-txn-values.patch`: **0**。`git diff --stat`: 1 file、2 hunk。
- `/usr/bin/clang-format --dry-run --Werror .../cc/silo/transaction.cc`: **0**。`check_format_ci.sh ... /usr/bin/clang-format`: 全 213 file、**0**。
- `python3 scripts/check_instr_v2.py ...`: **0**。F と F+修正の両方で計装 patch の `git apply --check`・実適用が成功。3 file の `#if TRACE` 条件群を丸ごと除いた bytes は各土台と一致。
- `bash -n`（v2 shell script 3 本）: **0**。`python3 -m py_compile`（v2 起動器・棚卸し）: **0**。
- 棚卸し自己走: **1**。渡した TIP OID が実在せず、`fatal: invalid reference`。再試行していません。
- clone 復元の `git switch --detach F`、一時 branch 削除、修正 patch 再適用: いずれも **0**。

## 未実走・残る懸念

計算ノード用 script は**実装済み・未実走**で、実行時の受入確認は済んでいません。棚卸し JSON・表も未生成です。新規 shell script の実行権限と、起動器が build の全 stdout/stderr を保存する要件も未確認です。

## 総括

指定修正、commit message、F 向け計装と静的確認までは完了しました。棚卸しの入力 OID 誤りによる失敗時点で、指示どおり推測による再試行を止めました。