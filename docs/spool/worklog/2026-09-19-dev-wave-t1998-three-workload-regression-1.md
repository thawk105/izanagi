---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-t1998-three-workload-regression
seq: 1
title: [T-2610] 採用候補 fixed 5 µs を 3 workload で同時期に測り、read-heavy だけが床値超の退行と判定した (コード + 計測 + docs、branch worktree-dev-wave-t1998-three-workload-regression)
---

## 本文

- ユーザー裁定 (2026-09-19、逐語は {{D:b7-fixed5-three-workload-regression-authorization}}): 候補 = T-1998 事前登録の採用 arm、
  床値 = D1639 の between-run noise floor、判定 = 対差 < −floor で退行、退行込みで 3 workload 全件を報告、B-7 充足は判定しない
  (D2044 項 3 維持)、機構 = A-2 / A-6 の certification 経路を descriptive に使う、既存材料と併記しプールしない。
- 実装 (Codex author 1 本、commit `c18a80967`): 新 study `paper-story-b7-fixed5-regression` (rr5 / rr50 / rr95 × stock / fixed5、
  全 workload の採用値 5 µs、nodes 5) を A-6 追加 (60605bec3) と同形で closed set へ足した。module 4 箇所 + 文言、submitter 2 箇所
  (投入 env と receipt 再構成の両方)、tests 20 case。A-2 / A-6 policy・job body・partial 境界・正しさ gate は不変。
  親の実走: 対象 2 file 307 passed (login)、meta 5 file 1071 passed / 6 skipped (計算ノード)。
- 段 2 plan 1・段 3 相談 2・段 6 レビュー 2: must-fix 0。相談で refuted/訂正した親の前提 — 「同一 build」は「同一候補・同一ソース条件から
  workload ごとに別 build」へ言い換え (binary は別)、A-6 の 73 分は nodes=1 の実測 (brief の誤り)、fp-* との bench.lock 競合前提は
  撤回、判定不能行と再投入規則を結果前に固定。裁定パッケージ候補なし。
- 計測 attempt `b7f5-20260919a` (22:32 JST 投入、3 request 各 5 node、queue 待ち 254 / 1641 / 1381 s、Elapse 386 / 841 / 1218 s、
  driver_rc 0 × 3)。collect は submit-tree の module で行う必要があった (submission receipt が submit-tree の policy path を束縛、
  wave worktree から呼ぶと `qsub -v is not bound` で rc=2。1 回目の記録は job dir に退避)。
- 結果 (権威 bytes `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/certification.json`): effects rr5 +0.6789675418265144 /
  rr50 +0.12671651401806727 / rr95 −0.11378696258180376。結果前固定の規則で **rr95 だけ床値 (0.0022283754708938273) 超の退行**、
  rr5 / rr50 は退行なし。outer `reject` (論理積の帰結)、6 cell とも certified・anomaly 0。3 workload の adopted `source_bytes_sha256`
  は T-1998 prereg の target `678b7203…` と全桁一致、stock は baseline `2d691b45…` と一致。稿は
  `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md` (限定 14 件、図は材料のみ)。
- 変異: probe (全件 SURVIVED 期待) で観測集合を採り、review A の静的導出と一致。本走の結果は同 wave の insight README に記録。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2)。専用 handoff は repo 外 job dir の `HANDOFF.md`。
  land 調停役 (peer session) へ予定を返信し、GO 待ちで land する。

## 次の一手差分

### 更新

- [T-2610] **P1・裁定済み (D2044 項 3) → 未了で維持、材料 1 attempt 追加**:
  B-7 の要件充足へ昇格させない (D2044 項 3 は不変)。同一 variant (fixed 5 µs) の 3 workload 横断比較と床値超の判定を供給する
  材料 1 attempt 分を `results/2026-09-19-b7-fixed5-three-workload-regression.md` に置いた (read-heavy が床値超の退行)。
  要件充足の判定・反復 attempt・図の作成は未了。
  base: c8ed2e2f321545d2f595719f117cde9cbc7d484681e510170a7a6955aa447713
