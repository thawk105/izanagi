---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2153-witness-bc
seq: 1
title: [T-2153] 意味 witness の残件 (b)(c) — `#ifdef` の定義/未定義観測と非一意 directive の全箇所観測を足し、MISATTR / RUNG1 / TRIGGER_GATING を登録簿へ (枝選択 18 → 21)、REQUESTED_US は 4 箇所同時観測の残件 (コード + テスト、branch worktree-dev-wave-t2153-witness-bc、変異 matrix = baseline PASSED・9 変異中 8 KILLED + 等価 1 SURVIVED・MISMATCH 0・期待 node 完全一致 8/8)
---

## 本文

- ユーザー依頼は「未対応 8 件のうち機構変更で届く (b) `IZANAGI_BREAK_TRIGGER_MISATTR` (`#ifdef` 非識別) の定義/未定義観測と
  (c) RUNG1 ×2 / REQUESTED_US ×2 / TRIGGER_GATING ×12 の非一意に対する代表選択 (全箇所か決定的規則) を Codex author (D95) で
  実装し land まで。(d) SS2PL・探索 loop 配線・offline 供給・admission 永続化・S2 再走は含めない。変異 = 正例と負例。既存 stock /
  template の pre-image は byte 一致。規律 2 を緩めない。仮想リスク向けの gate・検査・台帳・一般化は scope 外」。一次資料は
  `output/insights/2026-09-20/t2153-witness-bc/README.md` (逐語は同 `verbatim/`)。prompt・log・patch・probe・cell 原本は job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-bc/` に保全。設計判断は {{D:witness-ifdef-and-multisite}}。
- **brief 前の前提実測が新事実を出した:** 現行 gate (main 947fd160a) で positive control MISATTR を要求 1 / 既定 0 で通すと
  **supply arm が `preprocess-bytes-identical` で赤** (`#ifdef` は `-D=0` でも定義済み) = `s8a_trigger_coverage` の misattr 腕は
  preflight で `RuntimeError` になる (実走記録なし)。既定を省くと supply green・meaning 未確立。他 3 macro は supply green・
  meaning 未確立。静的解析で 4 macro の全箇所が driver の genome で活性 (MISATTR だけ `#if BACKOFF_TRIGGER_GATING` の内側)。
- **判定 (実測):** 3 macro を登録し (枝選択 18 → 21、対応集合 19 → 22)、最終 production 登録簿 (b250dc9a9) の CLI を実 patch 木
  + official 同形供給で login (pegasus02) と計算ノード (bnode003) で実走: TRIGGER_GATING は coverage の 2 構成 (skeleton+instr /
  +misattr) とも **(12,12)/(0,12)**、MISATTR 1 vs 未定義は **(1,1)/(0,1)** (default define_value = null)、RUNG1 は **(2,2)/(0,2)**
  で全 cell green / admitted / 未確立 []。login と計算ノードで前処理 digest・bytes・owner TU sha・compiler が完全一致。MISATTR
  1 vs 0 は supply 赤 + factory None で拒否 (設計どおり)。**REQUESTED_US は登録しない** (transaction.cc 2 + backoff.hh 2 の 4 箇所
  同時観測には複数 file の宣言・capture・shadow・schema 拡張が要り、所有 TU の 2 箇所だけは D2161 (2) の部分登録) — 残件。
- **I1 (既存 macro の不変):** SORT / REPORT の record を変更前後で同 driver-id・同 configure で leaf 比較し、差は一時 path と
  それに派生する digest だけ (key 集合・前処理 digest・counts・reason は同一)。新規 MISATTR / RUNG1 は登録で共有 build root へ
  移るが前処理 digest・bytes は登録前後で一致。
- **段 3 (2 レンズ) の real 所見:** (A1) 12 箇所の主張は DefineSpec patch の逐語 12 箇所に限り、計装 patch の複合枝
  `#if BACKOFF_TRIGGER_GATING && TRACE` と `#ifndef` 番兵は対象外と record・docstring・insight に明記 (未宣言箇所の走査機構は
  足さない、裁定パッケージ候補); (A2/B2) supply の不在検査は `#ifdef` 登録 macro に限定 (全 `default=None` へ広げると
  NOINLINE 1/None の判定が変わる); (A3) 実 TU cell は coverage の 2 構成を分ける; (B1) `s1_verify_extime_calibration` は
  D1492 の対象だが capture が genome configure と offline 供給を渡さないため配線しない (別変更単位); (B3) 件数は現物 18 → 21;
  (B4) 新 field・汎用 validator・互換 framework は作らない (別 N mapping は採用)。refuted: 旧経路の受理拡大、全箇所観測の黙認、
  companion 化。
- **段 5 → 段 6:** author は sandbox で test 未実走 (qstat preflight rc=16)、親が計算ノード dispatch で実走。所有 3 file 302 passed /
  1 failed (docstring 件数 pin の未追随)、consumer 18 file 1695 passed / 45 failed = S1 direct comparison 44 (fixture helper が
  要求 macro ごとに 1 箇所しか足さず GATING N=12 で `site-count-mismatch`; 未確立持ち越し例が GATING 1/0 を使う) + B-4 probe の
  clean-tree test 1 (未 commit dirt 由来)。review A / B とも NO-GO (must = m4 が等価変異 + 直接検査が schema に遮られる →
  m4′ (対照 selected 検査だけ除去) と独立 node 化; baseline 赤; GATING 境界の docstring; 計算ノード cell)。fix 1 (Codex) は
  docstring pin・S1 fixture の N 箇所化・持ち越し例 GATING 0/0 → 親 probe で 0/0 は stock-inert 経路になり S1 fixture の stock
  root が FIXED/NOINLINE の CMake mapping を欠くため `compile-command-drift` (fixture の限界) → fix 2 (Codex) で持ち越し例を
  GATING 2/0 (非対値 = factory None、供給は同 root で green) へ、直接検査を独立 node へ、module docstring に主張範囲 1 文。
  再走 (計算ノード) = 所有 4 file **445 passed**、consumer 20 file (clean tree) **1791 passed / 2 skipped**。全史 provenance
  11,883 件・新規違反なし。
- **変異 matrix (`tools/mutation_worktree.py`、独立 clone、固定 commit b250dc9a9、dispatch):** probe 走 (全 SURVIVED 登録で観測
  node を収集) → final 走 (観測 node を完全集合で登録)。final = baseline PASSED、**m1〜m8 KILLED (期待 node 完全一致 8/8)、m0
  等価 SURVIVED、MISMATCH 0**。帰属表は insight §8 (m3 / m7 の複数 node は単一 seam の波及、m4′ は独立 node の直接検査 +
  公開 evaluator の reason 差、m6 は `=0` 2 形が green 化・裸 `-DM` は別理由の赤)。
- 統合 commit b250dc9a9 (gate module・coverage driver・test 4 file)。author 1 巡 + fix 2 巡 + review 2 + plan 1 + consult 2
  (codex gpt-6-astra medium)。計算ノード job: 焦点走 5 (own1 / cons1 / own3 / cons2 / provenance) + cell 1 + 変異 2 走。
  login から `run_tests.py` を投げると headroom があれば bounded local に落ち S1 24 件が `/tmp/.git` 由来の偽赤 (1 走無駄) →
  `--force-dispatch` で計算ノードへ固定。
- 公開 driver (coverage / frequency / rung1) の JSON は本 wave では未取得。「未確立一覧が縮む」は CLI cell で実証した範囲。
- 受入と land の最終結果は専用 handoff と land 受領証へ集約する。

## 次の一手差分

### 更新

- [T-2153] **P2**: 意味 witness 対応集合 19 → 22 (枝選択 21 + BACKOFF_FIXED)。entry 1195 の残り 13 件のうち現在未対応は
  5 件: (c) `BACKOFF_REQUESTED_US` (transaction.cc 2 + backoff.hh 2 の 4 箇所同時観測 = 1 macro に複数 file の箇所群を宣言し
  同じ shadow で計装する拡張が要る、所有 TU 2 箇所だけの登録は部分登録で採らない)、(d) `SS2PL_LOCK_IMPL` / `SS2PL_WFG_DIAG`
  (複合行 1 本は観測可能だが代表選択を採らない、他は非一意、現行 patch は supply 拒否 = T-2737 §7 待ち)、`SS2PL_DLR` (CMake の
  DLR marker 同時変更で meaning arm も compile-command-drift)、`SS2PL_LOCK_KIND` (所有 TU に directive なし)。
  (b) MISATTR と (c) RUNG1 / TRIGGER_GATING は 2026-09-20 に `#ifdef` の未定義対照と N 箇所観測で実 TU (login + 計算ノード) 実測のうえ
  登録した (insight `t2153-witness-bc`、{{D:witness-ifdef-and-multisite}})。配線は `s8a_trigger_coverage` (MISATTR の request は
  default None)。`s1_verify_extime_calibration` (TRIGGER_GATING を要求し JSON へ載せるが genome configure と offline 供給を capture へ
  渡さない) の配線 + 供給整合、探索 loop (`p3_s4_loop_*` / `s6_sort_sweep`) への配線 + offline 供給 + admission 永続化、所有 TU 内の
  未宣言箇所 (重ね当て patch の複合枝) の走査、公開 driver JSON の取得は別変更単位 (未起票)。S2 の実機再走は 2026-09-17 に実測済み
  (insight `t2153-s2-pegasus-calibration`、4 固定値の変更が要り別変更単位)。
  base: a64b7ab08441e431190b0ed9e5879bf1cd81b9492075f22e5619a4db3a1abcb2
