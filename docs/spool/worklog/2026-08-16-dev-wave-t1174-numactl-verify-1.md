---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1174-numactl-verify
seq: 1
title: S2 verify の判定を bench と同一 launch prefix かへ正し、8c live pilot に残っていた最後の閂を外した (コード + テスト + docs、branch worktree-dev-wave-t1174-numactl-verify)
---

## 本文

- **裁定どおりの実装である。** 2026-08-16 のユーザー一括裁定 (第 2 回) 択 (d) 新案
  ([T-1174]) に従い、`pipeline.py` の S2 gate を「numactl 文字列が非空か」から
  「verify の launch prefix が bench の権威である解決済み環境契約の numactl と exact 一致するか」
  へ変えた。択 (a) (契約へ numactl を足す) と択 (b) (extra_correctness を外す) は
  裁定どおり採っていない。
- **これは受理集合の一方向な緩和ではない。** 空 prefix が契約である pegasus は通るようになる一方、
  **契約と異なる非空 prefix を指定した verify は新たに拒否される**。従来の述語は
  「非空でありさえすれば通す」ため、bench と異なるメモリ配置での verify を見逃していた。
  この新しい拒否をテストで固定した。
- **権威の選び方**: `evaluate` の必須 keyword `authorization_contract`
  (検証済み activation state と current contract の process-local receipt) の `.contract.numactl`
  を使う。呼び手が渡した値ではない。`qualification_policy` 経路は同関数内に
  Pegasus 契約との exact 照合を既に持つため、従来どおり本 gate の対象外とした。
- **閂であったことの実測**: 2026-08-16 の 8c live pilot 実機 2 走 ([T-1112]) で、
  transport 通過・claude CLI 実行・coder 合成・campaign 起動・build・verify 到達まで確認され、
  残る閂がこの環境契約の矛盾 1 点に絞られていた。
- **同日の別 wave が bench 側の閂 (perf 不在) を外している** (branch
  `worktree-dev-wave-perf-optional`)。両方が land すれば 8c live pilot は
  verify を越えて bench まで進む見込みである。ただし**実際に進むかは次の実走で測る**もので、
  本 wave はそこまでは主張しない。
- 実装子は sandbox の制約で pytest を起動できず (`qstat -Q` が `EACCTAUTH Unknown user-id`、
  rc=16)、**実走は親が計算ノードで行った** (3 件緑)。子の非実走を緑と記録していない。

## 次の一手差分

### 新規

- {{T:s2-verify-live-rerun}} **P1・新規**: 本 wave と perf 非依存化が land した後に
  8c live pilot を再投入し、S2 verify を越えて bench まで到達するかを実機で測る。
  到達したら、そこで初めて「8c の閂が外れた」と記録する。到達しない場合は
  次の閂を同じ方式 (実機走の WAL stage で切り分ける) で特定する。
