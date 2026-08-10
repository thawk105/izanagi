---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t673-residual
seq: 2
---

## 新規

### {{F:mutation-spec-field-contract-unwritten}}. 変異 spec の field 契約が走行時 reference に無く、preflight を 2 度やり直した [手順漏れ]

- 事象: [T-673] wave の変異 preflight で、spec の `estimated_run_seconds` を「総所要」と誤読して
  値を決め、**preflight を 2 度やり直した**。同 wave はさらに、`DW-M08` が義務づける「新旧両走」に
  **同一 spec を使い回せない**ことを走行設計の途中で知った。後者に実害は出ていない — 候補ごとに
  spec を分けて回避しており、insights の変異台帳 7 本はいずれも `MISMATCH` 0 である。
- 根本原因: harness が要求する field の意味 (`estimated_run_seconds` は総量でなく 1 run あたり、
  `SURVIVED` / `TIMEOUT` 期待では `expected_nodes` が空必須) は `tools/mutation_harness.py` に
  しか無く、走行時に読む `docs/dev-wave/mutation.md` の `DW-M05` / `DW-M08` には書かれていない。
  同 reference の L1.5 読量予算は上限ちょうどで余白が無く、追記は 2 波連続で見送られた
  ([T-627]、[T-673])。予算のために安全記述を削らない契約と、予算値を上げない方針の交点に落ちた
  知見である。
- 恒久対応: memory `mutation-spec-field-contract` に 2 つの field 契約を置いた (docs 予算に依らない
  到達面)。使い捨て worktree 経路と `--scratch-root` の要件は、単節予算に余白のある L2 節
  `DW-O19` へ採録した。振り分けは §56 の [T-673] (7) 裁定に基づく。
- 再発検知: (a) `tools/mutation_harness.py` の preflight が
  `mutation estimate: N mutation(s) x X.XXXs, baseline=B run(s), total=M run(s)/Y.YYYs` を出力し、
  1 run あたりと総量を分けて表示する。総量として決めた値なら `total` が想定と桁で食い違う。
  (b) 同 tool の spec 検証が `SURVIVED 期待では expected_nodes は空でなければならない` で
  fail-closed に落ちる。(c) 使い回した spec で走らせた場合は `MISMATCH` になり `KILLED` には
  ならない (`failed_keys == expected_keys` の完全一致契約)。
- 近縁: F185 (同じ field を local 実測から決めて dispatch 経路の下限を割った)、
  F87 (`MISMATCH` を期待 node の過少列挙として読む型)。
