---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2312-ceiling-ledger
seq: 1
title: [T-2312] 静的 backoff の上限拡張は着地済みだった — 持ち越されていた次の一手を実測で閉じる (docs のみ、branch worktree-dev-wave-t2312-ceiling-ledger)
---

## 本文

ユーザーが「停止した先行 wave の成果を回収して着地させよ」として起こした wave。**その前提が
現物で覆った (refuted)。** [T-2312] は停止しておらず、実装 commit `91a5bfca3` と記録 commit
`ded2598bb` が main の祖先で、entry 1330 に記録済みだった。本 wave は実装を行わず、
着地の確認と次の一手の訂正だけを行った。

- 残っていた worktree `.codex/worktrees/backoff-ceiling-author` (branch
  `impl-dev-wave-backoff-ceiling`) は同 wave の Codex 実装子の残骸であり、未着地の成果ではない。
  commit は 0 本で、staged の 17 file のうち 14 file が main と byte 一致。差がある 3 file
  (`b10_backoff_shape_sweep.py` / `test_b10_backoff_shape_sweep.py` / `patches/README.md`) の
  worktree 側固有行は、着地後に別 wave が書き換えた旧行だけだった。上限拡張の取り残しはゼロ。
  Codex 実装子 worktree は撤去対象外の慣行に従い残した。
- 能力を main `cc9bba523` の login node で実測した。`encode_static_backoff_us` /
  `decode_static_backoff_us` は 0→0・999→999・1000→3000・2000→4000・4000→6000・9999→11999 が
  往復一致し、10000 と −1 は `ValueError` で拒否した。[T-2418] が要る 3 点は現行 main の経路で
  構成でき (`fixed-2000us` / `fixed-4000us` / `fixed-9999us`)、下流
  `backoff_overthrottle._point_backoff_us` が読む物理値も 2000 / 4000 / 9999 で一致した。
  **1000 マイクロ秒以上を測ることへの物理的な塞ぎは既に無い。** 格子 `EXTENDED_SWEEP_US` へ
  点を足すのは [T-2418] (D1813) の仕事で、本 wave の scope 外とした。
- **wave 起動を招いた誤りの所在:** 着地を記録した entry 1330 自身の次の一手が
  `- [T-2312] (1329)` として同項を carry し、以後 1362 から 1367 まで運ばれていた。carry 鎖の
  実体本文 (`docs/archive/worklog-phase3-0904-1252.md`) は「1000 µs 以上の静的点は原理的に
  測れない」と書いており、現行 main では偽である。次の一手 stub は land 自身の fold が書くため、
  その land で済んだ項がそのまま持ち越されうる。
- 一次資料: 実装の経緯と変異 12/12 KILLED は
  `output/insights/2026-09-08_backoff-static-ceiling/`、worklog 本文は
  `docs/archive/worklog-phase3-0908-1330.md`。
- エージェント工数: 子の起動なし (docs のみ、実装面の差分ゼロ)。実装面ゼロのため変異 matrix は
  免除した (DW-S04)。実 repo を読む焦点走 (`test_check_docs` / `test_spool_fold` /
  `test_fold_gate_nodes_contract`) は 759 passed・3 skipped で緑、`check_docs` と
  `spool_fold --dry-run` と全史 provenance 監査 (8988 件) も rc=0。

## 次の一手差分

### 完了

- [T-2312] 静的 backoff の符号化上限は entry 1330 で 999 から 9999 マイクロ秒へ広げ済みで、
  1000 マイクロ秒以上の静的点が構成できることを現行 main で実測した。1000 超の格子点・
  停止基準・予算は [T-2418] が持つ。
  remaining: none
  base: 874238948fcd533efd24f1492778789967f51a6fb2df4242963ae177a2693a6b
