---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-t2884-gate-verifier
seq: 1
title: [T-2884] gen-opt md_14: 正しさ関門の記録 (CCBench の手順列・値の刻印) と判定器 (意味の版 2) を正式化し、修正なしの Silo は D2b で赤・修正ありは certified・壊し B1 は D1 で赤を計算ノードで確かめた (branch worktree-dev-wave-t2884-gate-verifier)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14.txt` (共通指示 common-4.txt)。一次資料 `output/insights/2026-09-30/gen-opt-gate-verifier/README.md`、事前登録 `prereg.md` (計算の前に commit)、設計判断 {{D:gate-witness-verifier-v2}}、失敗の再発 F109。
- 結論 (一次資料 §0): CCBench の local branch `izanagi-gate-witness-trace` = `dcb9a41f3` (F の子、push なし、gitlink 不変)。判定器は gate file の照合 (D1・D2a・D2b 全 key・D5) を足して意味の版 2。計算ノードで修正なしの Silo は D2b で赤、Silo 修正を当てると D1・D2 とも 0 件で certified、壊し B1 は D1(b1) の違反数が発火数と一致して赤。判定器への変異 17 本はすべて KILLED。GCC 11 の D297 pass、GCC 12 は walltime で打ち切られ未取得。
- 生死確認の 1 回目は修正ありの条件だけ事前登録と不一致だった: D1・D2 は 0 件なのに、判定器の D5 の include 検査が実物の `#include "../../include/ycsb.hh"` を落とした (fixture が実物と違う簡略形で、test 200 件・review 2 本・焦点再レビューが通していた、F109 の再発)。判定器を直して取り直し、2 回目は 4 条件すべて一致。1 回目の記録も残す。
- 棄却・限定した所見: 段 6 レビュー B の「D1(b2) の包含の向きが逆」は refuted (コードは `reads ⊆ q_read`)。段 2 plan の「要求 keyword を既定値なしにする」は不採用 ({{D:gate-witness-verifier-v2}} の却下案)。焦点再レビューの新規所見 F1〜F3 は受理集合を変えないので nit。
- 計算ノード: 合計 7,221 s ≈ 2.01 node 時間 (内訳は一次資料 §7)。投入時の見積り 1.05〜1.65 を D297 (全 protocol が include する ycsb.hh の変更で consumer 1,820 entry、GCC 11 だけで約 55 分) が押し上げ、2 node 時間の線に届いたので GCC 12 の D297 は取り直さず gitlink 前進の wave へ回した。D297 の job script が GCC 11・12 を直列にしていたのが walltime 超過の原因。
- セッションの異常: 段 5・6 の待ち手の終端 commit が 2 本とも `add-all` で失敗し、子木に空の `index.lock` が残った (process 0 を確かめて削除、残差は親が所有 path だけ子 branch へ commit)。親が変異用 clone の作成 script を誤った SHA で起動し (update-ref で停止、無害)、作り直した。段 4 裁定と fix 投入の時刻を推定で書いて誤り、mtime で訂正した。
- 子の工数: Codex plan 1・相談 2・author 2・review 2・fix 4 (U1 1、U2 3)・焦点再レビュー 1。codex 子は pytest を回せないので、焦点走 6 回・生死確認 2 回・変異 2 回はすべて親が実測した。

## 次の一手差分

### 完了

- [T-2884] 正しさ関門の記録と判定器を正式化した。CCBench の branch `izanagi-gate-witness-trace` (`dcb9a41f3`、`#if TRACE` 内の手順列 `Q`・刻印 `V`、刻印は `YCSB::id_`)、判定器の意味の版 2 (gate file の照合 D1・D2a・D2b 全 key・D5、要求は `require_gate_witness`)、test と変異 17 本 KILLED、計算ノードの生死確認 (修正なしは D2b 赤、修正ありは certified、B1 は D1 赤) を一次資料 `output/insights/2026-09-30/gen-opt-gate-verifier/README.md` に記録した ({{D:gate-witness-verifier-v2}})。GCC 12 の D297 と gitlink 前進は {{T:gate-witness-pin-integration}} へ、gen-opt driver の接続は {{T:gate-witness-driver-require}} へ移した。
  remaining: none
  base: 95a5390637c7b97f845dddae152486776a787bd00924f07461385fe8f83dd888

### 更新

- [T-2889] **P2・前提の一部充足、計算は経路次第で確認が要る**: 迂回の変異 7 本 (B1〜B7) と負例 4 本 (N1〜N4) を trace build で走らせ、事前登録した期待と照合する。記録と判定器 ([T-2884]、`output/insights/2026-09-30/gen-opt-gate-verifier/README.md`) は揃い、Silo 修正後の stock で D1・D2 が 0 件になることも確かめた。残る前提: B2〜B7 の壊し patch を U1 tip (`izanagi-gate-witness-trace`) 用に作ること (Codex author、B1 の U1 用 patch と起動器 v3 は job dir `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/u1-final/`)、N2 (手書き方策) の build 経路、Silo 修正 ([T-2905]) を重ねるかの決定。**計算の見積り:** 本 wave の起動器 (1 条件 1 build・2 workload) の実測単価 1 条件 117〜130 秒で 11 条件 ≈ 0.36〜0.40 node 時間、再走 2 条件込みで ≈ 0.42〜0.47 node 時間 (2 未満)。方策の pipeline 経由 (1 評価 0.21〜0.22 node 時間) なら ≈ 2.3〜2.9 node 時間で、その経路ならユーザー確認が要る。根拠: 設計資料 `output/insights/2026-09-29/gen-opt-correctness-gate/README.md` §3.4・§7 の U6。
  base: 757b078096a77e30421220cbcfa14cd09c5c887b164cdff7440df4ad47b43a88

### 新規

- {{T:gate-witness-pin-integration}} **P2・新規 (前提待ち)**: 正しさ関門の記録 (CCBench の local branch `izanagi-gate-witness-trace`、`dcb9a41f3`、F の子) を評価対象の pin へ入れる。push はユーザー (D16)。Silo 修正の branch ([T-2905]・[T-2917]) と同じ file (`cc/silo/transaction.cc`、U1 は writePhase、修正は read・update) を触るので、統合した tip を作り、その tip で上流 CI 2 本・D297 (**GCC 11・12 を別 job で並行に**、1 本 約 1 時間を見込む。本 wave では GCC 11 だけ pass、GCC 12 は未取得)・生死確認 (本 wave の起動器 v3 と判定器、S・X・B) を取り直す。**U1 だけを先に pin へ入れると修正前の Silo の trace は D2b で全部 indeterminate になる** (照合は緩めない) ので、Silo 修正と同時か後に入れる。根拠: `output/insights/2026-09-30/gen-opt-gate-verifier/README.md` §6.3・§8。
- {{T:gate-witness-driver-require}} **P2・新規 (段 A の軸の後)**: gen-opt の軸の driver から判定器を `require_gate_witness=True` で呼び、capability 経路 (`verify_trace_dir_with_capability`・`pipeline.py`) に要求を通し、D5 を build の source snapshot に束縛する (設計資料 §7 の U5 の一部)。それまで gen-opt の候補は certified を名乗れない (要求しない呼び出しは gate file の在否だけで照合する)。根拠: {{D:gate-witness-verifier-v2}}、`output/insights/2026-09-30/gen-opt-gate-verifier/README.md` §8。
