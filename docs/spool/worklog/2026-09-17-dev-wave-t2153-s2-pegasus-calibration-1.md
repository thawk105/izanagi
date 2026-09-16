---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2153-s2-pegasus-calibration
seq: 1
title: [T-2153] S2 縮小 verify 較正を現行 condition gate 下で Pegasus 計算ノードで実走した — driver そのままは gate の compiler 解決で止まり JSON を産まず、同じ request に供給を足した gate CLI では 2 macro とも unestablished_meaning_macros が空 (docs のみ、branch worktree-dev-wave-t2153-s2-pegasus-calibration、変異 matrix = 実装面差分ゼロにつき免除)
---

## 本文

- ユーザー依頼は「[T-2153] の未検証事項を実測する: S2 縮小 verify 構成の較正 (gate 3 点) を現行 condition gate 下で Pegasus
  計算ノード (generic dispatch) で実走し、`condition_gates[i].admission.unestablished_meaning_macros` が空になるかを確かめる。
  masstree `config.h` 欠落で前処理 red になりうる (D2059 同型) — その場合は理由を構造化して insight に返し、修正実装へ広げない。
  実装差分ゼロ (計測成果物 + docs)、DW-S04 の変異免除。B-10 の meaning witness に関わる事実として記録する。gate・検査・台帳の
  追加は scope 外。規律 1・2 を緩めない」。
- 一次資料は `output/insights/2026-09-17/t2153-s2-pegasus-calibration/README.md`。dispatch の request / receipt / job stdout・stderr と
  login 走の逐語は同 `verbatim/`。使い捨て launcher と login log は job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-s2-pegasus-calibration/` に保全 (repo へ入れず README に path と sha256)。
- **brief 前の前提実測が依頼の前提を 2 点で覆した。** (N1) S2 driver は pin `dff0f1e` を固定し現行 submodule `511c953` では
  `assert_pinned_clean` で止まる (pin.py が定める設計、再走手順 = submodule を `dff0f1e` へ)。(N2) Pegasus に `g++-13`
  (`buildcache.DEFAULT_CXX`) / `numactl` / gflags / glog が無く、gate は configure より前に `compiler-failed` になる — 依頼が予期した
  D2059 型 (`preprocess-failed`) には届かない。段 4 で裁定し、ユーザー指示 (実装差分ゼロ) を守ったまま届く最遠点を測る計画に確定した。
- **結果 1 (依頼の本題):** detached submit-tree (submodule `dff0f1e`) から driver そのままを計算ノード bnode002 (`2731.nqsv`、Elapse
  7 秒) で走らせると、単独性・空きディスク・pinned-clean を通過した直後、条件 gate 前処理の 1 本目で RuntimeError
  `condition gate rejected IZANAGI_BREAK_NOREAD_VALIDATION: supply=red/compiler-failed, meaning=red/compiler-failed`。JSON / md は未生成で、
  `unestablished_meaning_macros` は **S2 driver 経由では観測できない**。
- **結果 2 (切り分け):** 同じ request (driver_id / macro / requested 1 / default 0 / S2 の configure 引数 5 本) を gate CLI
  `condition_meaning_gate` に渡し、Pegasus で使える compiler (g++-11) と依存供給 (既存 gflags / glog prefix、永続 thirdparty cache) を
  `--configure-arg=` で足すと、`IZANAGI_BREAK_NOREAD_VALIDATION` (`2732.nqsv`) と `IZANAGI_BREAK_HIGHKEY_VALIDATION` (`2733.nqsv`) の
  両方が bnode003 で supply green / meaning green (`declared-compile-time-branch-selection-observed`) / admitted、
  `unestablished_meaning_macros = []`。NORW は login 走と前処理 bytes・digest が一致 (4,514,644 / 4,514,738 bytes)。
  **T-2153 が toy fixture でしか示せていなかった (a) 型の意味 witness が、実 CCBench TU + 実 patch + 実 compiler で立つことの初の実機実測。**
  B-10 の macro そのものは測っていない (機構が実 TU で働くことまで)。
- **S2 driver が Pegasus で JSON を産むには 4 固定値の変更が要る (列挙のみ、実装しない):** compiler (`g++-13`)、依存供給 (gate にも
  legacy `buildcache.build` にも渡さない)、`numactl` 前置、`ENV_TAG` / `clocks_per_us` / 出力 path (linux-baremetal 固定、D924)。gate 3 点
  (contention 再現 / trace 規模 / 赤検出力) は届かないため未測定。既存 `output/env/linux-baremetal/calibration/s2_verify_*.json` の bytes は不変。
- 踏んだ罠: 同一 checkout からの generic dispatch は 1 本ずつ。dispatcher の pending orphan hold (`phase: pending-qsub`) は qsub 受理後も
  receipt 永続化 (job 終端) まで残り、5 秒後に同じ worktree から投げた 2 本目は `orphan-hold` で rc=16 (child 未起動)。終端後の投げ直しで通った。
  別 checkout (submit-tree) からの同時投入は通る。
- 軽量版 (docs-only): codex 子ゼロ、段 2・3・5・6 省略。変異 matrix は実装面差分ゼロにつき免除。計算ノード job 3 本 (合計 Elapse 24 秒)、
  login probe 2 本。受入全走は記録 commit 後に land 前 1 回 (結果は land の受領証が持つ)。

## 次の一手差分

### 更新

- [T-2153] **P2**: 意味 witness 対応集合 13 → 15 (枝選択 14 + BACKOFF_FIXED)。entry 1195 の残り 13 件のうち現在未対応は
  10 件: (b) `IZANAGI_BREAK_TRIGGER_MISATTR` (`#ifdef` は対照 `-D=0` でも定義済みで非識別、外側 `#if BACKOFF_TRIGGER_GATING`
  / `#if NO_WAIT_LOCKING_IN_VALIDATION` にも依存)、(c) `IZANAGI_SILO_LADDER_RUNG1` ×2 / `BACKOFF_REQUESTED_US` ×2 /
  `BACKOFF_TRIGGER_GATING` ×12 (所有 TU 内の同一逐語、一意性検査で red)、(d) `SS2PL_LOCK_IMPL` / `SS2PL_LOCK_KIND` /
  `SS2PL_DLR` / `SS2PL_WFG_DIAG`、(e) `SORT_VARIANT` (driver 配線が編集面を超える)、(f) `IZANAGI_SILO_LADDER_RUNG1_REPORT`。
  (b)(c) は既存機構では届かず、届かせるには機構変更 (定義/未定義の観測、複数箇所の代表選択) が要る。
  S2 の実機再走は 2026-09-17 に Pegasus で実測した (insight `t2153-s2-pegasus-calibration`): driver そのままは gate の compiler 解決
  (`g++-13` 不在) で止まり JSON を産まない。同じ request に供給を足した gate CLI では NORW / HIGHKEY とも計算ノードで
  `unestablished_meaning_macros == []` (実 TU で (a) 型 witness が立つ)。S2 driver を Pegasus で走らせて gate 3 点まで取るには
  compiler・依存供給・numactl・環境契約の 4 固定値の変更が要り、別変更単位 (未起票、必要が生じた時点で諮る)。
  base: 4c81ae5eba84065a7390708bb3c34ce3f8d8637b21b4264228b200010ce9baeb
