---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2153-witness-else-nested
seq: 1
title: [T-2153] 意味 witness を (a) 型 (#else + 入れ子) の 2 macro へ広げ、S2 検証較正へ配線した — (b)(c) は既存機構で届かないことを実測で示した (コード + テスト、branch worktree-dev-wave-t2153-witness-else-nested、変異 matrix = baseline PASSED・7/7 KILLED・SURVIVED 1 (等価 M0)・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「T-2153 の残り 13 件の型 (a)〜(f) のうち、既存機構で届く (a)(b)(c) から取る。Codex author +
  変異事前登録。本題の witness 追加だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。規律 2 を緩めない」。
- 一次資料は `output/insights/2026-09-17/t2153-witness-else-nested/README.md`。生死実験・probe・焦点走 log・変異 spec /
  report は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-else-nested/` に保全した (script は親が書いた
  使い捨てなので repo へ入れず、README に path と sha256 を書いた)。
- **段 1 で機構の制約を現物で確かめ、(a)(b)(c) のうち既存機構で届くのは (a) の 2 件だけと実測した。** probe は宣言指令の直前に
  自己完結の `#if M / SELECTED / #endif / COMPLETED` 塊を挿入するので、元の枝の `#else` と入れ子は marker の選択条件に
  入らない (toy TU + 実 compiler で要求 1 → (1,1)・既定 0 → (0,1) の green)。(b) `IZANAGI_BREAK_TRIGGER_MISATTR` は
  `#ifdef` で対照 `-D=0` でも定義済みなので非識別 red ((1,1)/(1,1)、gating の内側では (0,0)/(0,0))。(c) 3 件は所有 TU に
  同一逐語が 2・2・12 回あり一意性検査で red。いずれも toy 実測 + 実 patch の静的対応付けであり、4 件の実 patch を
  compiler に通した結果ではない。依頼の「(a)(b)(c) から取る」は機構上の拒否を根拠に (a) だけへ絞った。
- **段 2 plan が親の brief の漏れを 2 点補正した。** 既存 test `test_compile_time_factory_keeps_unregistered_macro_unestablished`
  が NOREAD を「未登録 macro」として使っていた (TRIGGER_MISATTR へ差し替え)。registry 追加で 2 macro が供給側の共有
  build root 分岐 (既存 8+3 の CXX_FLAGS macro と同形) に入るので、「supply 不変」は呼出しと configure 引数に限る。
- **段 3 の 2 レンズ (real の要点):** `source_rel` 変異は test helper の assert が factory より先に赤を出すため単一理由性が
  無く登録から外した (DW-M01)。S2 配線変異の主 killer は新 consumer test (factory 戻り値との `is` 同一性まで検査) に置いた。
  CLI (`--macro` は供給 domain 全体、cases 未指定なら factory 自動) は既配線で自動追随するので「配線先は S2 だけ」を
  「追加配線が要る専用 driver は S2 だけ」へ訂正。screening の拒否理由は既定 0 でなく route 不一致 (`screening-build-route-mismatch`)。
  現行 condition gate 下で S2 が実機で走った記録は無い (最終 2026-07-06、`condition_gates` を持たない JSON)。
- **段 4 裁定 (親):** 完了判定を「registry + S2 配線 + toy 生死確認 + toy fixture 上の実 family 規則
  (`unestablished_meaning_macros == ()`)」までとし、実機 S2 走行による JSON の縮小は未検証として持ち越す。理由はユーザー指示
  「本題の witness 追加だけ」と、S2 の実機再走が condition gate 導入後 1 度も無く依存供給 (D2059 と同型) を伴う別変更単位であること。
- **段 6 のレビュー 2 本は must-fix 0 だったが、親の consumer 回帰 (9 file、688 passed) が real 赤を 1 件出した。**
  `test_build_site_gate.py::test_m11_coverage_configure_gates_are_independent` — S2 の `_broken_build_and_verify` は site gate より
  前に condition gate を呼ぶため、配線後は meaning arm の configure (一時 dir prefix `izanagi_compile_time_branch_`) が test の
  `subprocess.run` 代役に落ち `AttributeError` になった。fix は代役の素通し集合に prefix を足す 1 行 (production 不変)。
  repo 外 probe で fix 無し = 再現 / fix 有り = 期待の `BuildError` + 非素通し call 0 件を実測してから fix 子へ渡した。
  レビューが取り逃したのは f2 完了前に投入したためで、consumer 回帰の log を段 6 の射影に含めるのが正しい順序だった。
- 主張の境界: D1490 のまま (所有 TU で define の値が枝の選択を決める、前処理成功時)。実 patch 適用後の CCBench TU
  (masstree `config.h`) と実機 S2 走行は未検証。S2 の `_broken_build_and_verify` 内の再検査でも meaning arm が走るようになり
  configure は patch あたり 4 → 8 回、実機の所要増分は未計測。件数は対応集合 13 → 15、未対応 25 → 23、1195 の残り
  13 件のうち現在未対応 12 → 10。
- 工数: codex 子 6 本 (plan 1 (+ model at capacity で成果物ゼロの 1 本)、consult 2、author 1、review 2、fix 1、
  全段 `gpt-6-astra` / `medium`)。計算ノード job: 焦点走 3、変異 probe 10 + 本走 10 走、受入 1 (結果は land の受領証が持つ)。

## 次の一手差分

### 更新

- [T-2153] **P2**: 意味 witness 対応集合 13 → 15 (枝選択 14 + BACKOFF_FIXED)。entry 1195 の残り 13 件のうち現在未対応は
  10 件: (b) `IZANAGI_BREAK_TRIGGER_MISATTR` (`#ifdef` は対照 `-D=0` でも定義済みで非識別、外側 `#if BACKOFF_TRIGGER_GATING`
  / `#if NO_WAIT_LOCKING_IN_VALIDATION` にも依存)、(c) `IZANAGI_SILO_LADDER_RUNG1` ×2 / `BACKOFF_REQUESTED_US` ×2 /
  `BACKOFF_TRIGGER_GATING` ×12 (所有 TU 内の同一逐語、一意性検査で red)、(d) `SS2PL_LOCK_IMPL` / `SS2PL_LOCK_KIND` /
  `SS2PL_DLR` / `SS2PL_WFG_DIAG`、(e) `SORT_VARIANT` (driver 配線が編集面を超える)、(f) `IZANAGI_SILO_LADDER_RUNG1_REPORT`。
  (b)(c) は既存機構では届かず、届かせるには機構変更 (定義/未定義の観測、複数箇所の代表選択) が要る。
  未確認事項: S2 を現行 condition gate 下で実機再走し `output/env/linux-baremetal/calibration/s2_verify_<…>.json →
  condition_gates[i].admission.unestablished_meaning_macros` が空になることは未検証 (S2 は依存供給先を gate へ渡さないので
  masstree `config.h` 欠落で supply / meaning とも前処理 red になりうる、D2059 と同型)。
  base: 9eb0b7c32629c38ab1bb0c51d2e7e4a2daee2c31990cf9f95646dbefb58d6658
