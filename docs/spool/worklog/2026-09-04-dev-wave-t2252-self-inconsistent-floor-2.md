---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2252-self-inconsistent-floor
seq: 2
title: 段 8 — 改善候補 1 件 (変異 spec の category は閉集合) は L1 予算で docs へ入らず、memory へ寄せた事実を記録する (docs のみ、branch worktree-dev-wave-t2252-self-inconsistent-floor、実装面の差分 0)
---

## 本文

- **候補 1: 変異 spec の `category` は `tools/mutation_harness.py` の閉集合 `negative` / `positive` /
  `both-layers` で、等価変異に `equivalent` と書くと `--plan-only` の段階で「category が未知」として
  拒否される** (本 wave で 1 回空振り、実測)。`DW-M01`〜`DW-M08` のどれにも値域の記載が無い。
  routing 3 に従い `DW-M01` へ 1 文 (約 125 bytes) を足して `tools/check_docs.py` を回したところ、
  `docs/dev-wave/**: L1 unique footprint 10750 bytes > 予算 10625 bytes` で赤になった。
  予算のために既存の安全義務を圧縮する手順 (D730 / D782) は exact pin を壊す前歴があり、候補の
  実害は spec の preflight 1 回の空振りに留まるので、**docs は変更せず戻し**、値域と
  「spec の構文検査は HEAD blob 照合より先に走るので未 commit でも `--plan-only` で category と
  key の誤りは潰せる」事実を親の memory (`mutation-discipline`) へ書いた。上限は引き上げていない。
  L1 予算による docs 不採用は、`DW-S07` の走査器名 (2026-09-01、2026-09-04) に続く同型の別候補である。
- 候補 2 (preflight の検査順序の知見) は候補 1 に含めた。それ以外の候補は無い。
- 実装面の差分は 0。本エントリは fragment 1 本だけである。

## 次の一手差分
