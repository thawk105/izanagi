---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: worktree-dev-wave-t2153-witness-6
seq: 1
title: [T-2153] 意味 witness 対応集合を (d)(e)(f) の 6 macro で実 TU 実測し、SORT_VARIANT と RUNG1_REPORT を登録簿へ足した (15 → 17)、SS2PL 4 件は足さない理由を実測で確定 (コード + テスト、branch worktree-dev-wave-t2153-witness-6、変異 matrix = baseline PASSED・9 変異中 8 KILLED + 等価 1 SURVIVED・MISMATCH 0・期待 node 完全一致 8/8、初回 baseline の一過性赤と m7 の過剰決定は erratum)
---

## 本文

- ユーザー依頼は「残り 10 件のうち (d) SS2PL 4 件、(e) SORT_VARIANT、(f) RUNG1_REPORT を対象とし、各件を実 TU で witness が立つか
  実測してから対応集合へ足す。(b)(c) の機構変更と S2 driver の Pegasus 4 固定値変更は scope 外 (理由を記録)。Codex author (D95)。
  規律 2 を緩めない」。一次資料は `output/insights/2026-09-19/t2153-witness-6/README.md` (逐語は同 `verbatim/`)。
  probe 本体・cells.json 原本・launcher・log は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-6/` に保全
  (probe は Codex author 作、repo へ入れず README に path と sha256)。
- **判定 (実測):** SORT_VARIANT と RUNG1_REPORT は login (pegasus02) と計算ノード (bnode055) の official 同形供給で
  supply green / meaning green (1,1)/(0,1) / admitted / 未確立 [] → 登録簿 15 → 17。SS2PL_LOCK_IMPL / WFG_DIAG は
  meaning arm は緑だが唯一の一意 directive が複合行 1 本で他 19 / 44 箇所が非一意 = (c) 代表選択 (scope 外) かつ supply
  `dependency-closure-drift` → 足さない。SS2PL_DLR は meaning arm も `compile-command-drift` (CMake の DLR marker) → 既存機構では
  届かない。SS2PL_LOCK_KIND は所有 TU に directive なし → 宣言不能。設計判断は {{D:witness-registry-admission-by-real-tu}}。
- **配線 (D1492):** `silo_ladder_rung1` のみ 1 行 (admission が JSON へ載る)。S1 は既配線で official sort_best cell に自動発火。
  `p3_s4_loop_sort` (返却 dict が永続化されず、capture に offline 供給なし) と `s6_sort_sweep` (返り値を捨てる) は配線せず、
  探索 loop への配線 + offline 供給 + 永続化を別変更単位として insight §7 に置いた (未起票)。
- **brief 前の前提実測が entry 1195 の記述を 2 点で訂正した:** SORT の「driver 配線が編集面を超える」は factory 呼び出し 1 行
  + S1 既配線で解消。LOCK_KIND の「template のみ」は誤りで、`wfg.cc` に directive はある (所有 TU に無いだけ)。
- **段 3 (2 レンズ) の real 所見:** REPORT は登録で supply の対照 build root が共有化される → 登録前後の同一入力比較を事前登録
  (結果: 前処理 digest・bytes 完全一致)。P2 と P3 は複合式かどうかでは区別できず「観測可能だが採用しない」へ書き換え。
  companion 保証は gate 単体に無く公開 driver 契約に限定。親の事前実測は official 同形でない (BASE_DIR なし・PREFIX_PATH 引数)
  → env `CMAKE_PREFIX_PATH` + BASE_DIR + SOURCE_DIR ×3 に改めた。S6 は admission 非永続で配線対象外。refuted: 旧宣言経路の
  受理拡大、B-4 module 数 pin、known-axes / rung1 自己 hash / oracle manifest / check_docs の pin 更新要求。
- **段 6:** review 2 本は NO-GO (must = REPORT 正例の toy fixture が既定 0 で前処理出力 0 byte → supply `preprocess-output-empty`、
  F29 型の代表性)。fix 1 (Codex) で fixture に無条件行 + rung1 の実 helper 検査 (evaluator を観測 wrapper、factory / 登録簿は実物)。
  焦点走 = 374 passed、consumer 7 file 925 passed / 9 skipped (上位所要はすべて既存 t080 系)、閉包 9 file 350 passed / 2 skipped。
  焦点再レビュー = GO、新規 must-fix なし。全史 provenance 11,631 件・新規違反なし。
- **変異 matrix:** run 1 は baseline が一過性の PARSE_ERROR (受領証行 0) で中止 → 保持 container で手動実走 374 passed、resume は baseline を再走しないため別 scratch root で run 2。run 2 = baseline PASSED、m1〜m6 KILLED (期待 node 完全一致)、m0 等価 SURVIVED、m7 は MISMATCH (期待 4 に対し実 9 = `make_define_request` が spec companion を request へ写すため request 契約でも落ちる過剰決定、DW-M03)。m7 を 9 node で再登録し注入 seam だけを切る m7b を足して再走 → 両方 KILLED・完全一致。最終 8 KILLED + 等価 1 SURVIVED、MISMATCH 0。帰属表は insight §8。
- 統合 commit `7cc76d98b` (登録簿 +2、rung1 1 行、test 4 file)。author 2 巡 + fix 1 巡 + review 2 + focus 1 + plan 1 + consult 2
  (codex gpt-6-astra medium)。author の sandbox は `qstat -Q` preflight で test 未実走 (rc=16)、親が計算ノード dispatch で実走した。
- 受入 attempt 1 (main 32f0526bc を取り込んだ tip 7d9e74c48) は赤 6 = 3 shard × xdist worker internal error 2
  (`real_repo_receipt_memo` の `lock-acquire-failed` TimeoutError、session 開始時で test 未到達)。本 wave は同 module に
  非接触なので非帰属 (real-repo lock 競合の F945 族の変種、launcher の F945 grep には不一致) と判定し、同一 tip で 1 回だけ再投入した
  (DW-O18)。受入と land の最終結果は専用 handoff と land 受領証へ集約する。

## 次の一手差分

### 更新

- [T-2153] **P2**: 意味 witness 対応集合 15 → 17 (枝選択 16 + BACKOFF_FIXED)。entry 1195 の残り 13 件のうち現在未対応は
  8 件: (b) `IZANAGI_BREAK_TRIGGER_MISATTR` (`#ifdef` 非識別、外側条件)、(c) `IZANAGI_SILO_LADDER_RUNG1` ×2 /
  `BACKOFF_REQUESTED_US` ×2 / `BACKOFF_TRIGGER_GATING` ×12 (同一逐語の非一意)、(d) `SS2PL_LOCK_IMPL` / `SS2PL_WFG_DIAG`
  (複合行 1 本は観測可能だが代表選択を採らない、他は非一意、現行 patch は supply 拒否 = T-2737 §7 待ち)、`SS2PL_DLR`
  (CMake の DLR marker 同時変更で meaning arm も compile-command-drift)、`SS2PL_LOCK_KIND` (所有 TU に directive なし)。
  (e) SORT_VARIANT と (f) RUNG1_REPORT は 2026-09-19 に実 TU (login + 計算ノード、official 同形供給) で実測して登録した
  (insight `t2153-witness-6`、{{D:witness-registry-admission-by-real-tu}})。届かせるには (b)(c) の機構変更 (定義/未定義の
  観測、複数箇所の代表選択)、(d) は SS2PL patch の改訂 (T-2737 §7 裁定) と `owner_tus` の意味変更が要り、いずれも別変更単位。
  探索 loop (`p3_s4_loop_sort` / `s6_sort_sweep`) への meaning 配線 + offline 供給 + admission 永続化も別変更単位 (未起票)。
  S2 の実機再走は 2026-09-17 に Pegasus で実測済み (insight `t2153-s2-pegasus-calibration`): S2 driver を Pegasus で走らせて
  gate 3 点まで取るには compiler・依存供給・numactl・環境契約の 4 固定値の変更が要り、別変更単位 (未起票、必要が生じた
  時点で諮る)。
  base: e8e3fd7e0be1c20990e3a0a5d39d0c2fc0b1f4f274ab0e19482a4fed6d65f9e1
