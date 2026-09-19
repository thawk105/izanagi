---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2789-acceptance-ops-docs
seq: 1
title: [T-2789] 受入投入・再走の既存運用を docs に整理し、repo に正本があるものと job dir にしか無いものを分けた (docs のみ、branch worktree-dev-wave-t2789-acceptance-ops-docs)
---

## 本文

- D2148 項 12 の「既存運用の整理」だけを 1 wave で行った (兄弟項の fixture 待機上限は [T-2790]、entry 1699 で着地済み)。docs のみ、実装面差分ゼロ
  (変異 matrix 免除)。軽量版で段 2・3 を省き、段 6 に read-only review 1 本 (一次資料から事実を再抽出する docs-only の型)。
  専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2789-acceptance-ops-docs/HANDOFF.md`。
- 成果物は `docs/pegasus-runbook.md` §7.3 末尾の小節「受入投入・再走の運用の所在」(正本ポインタ表 / job dir のみ表 / 注意 3 点、36 行) と
  `output/insights/2026-09-20/t2789-acceptance-ops-inventory/README.md` (棚卸しの一次資料)。dev-wave の新 L2 節・門番条件値の採用・自動再投入の採用・
  `postcheck` の変更・機構/gate/台帳の追加はしていない。
- 段 1 前の実測で分かったこと: (1) 待ち手・受理・判定主体・再走制限・取り込み・待ち行列・判定器の契約は repo に正本がある (runbook §7.3、DW-O18/O20/O26/O27、
  D662/D688/D690)。(2) 投入時刻を選ぶ門番と赤の型で再投入する loop は job dir にしか無い — `run-acceptance-gated.sh` 46 本 (2026-09-17 09:20〜09-20 03:15)、
  条件形 4 種以上 (`l1 < l5` 18 本、`≤ 30` 15 本、`workers` 8 本、`gate.conf` 読み 23 本)、attempt 上限 3/4/5、撤回済み (09-18 14:35) の pigz 条件が撤回後の写し
  11 本に残る。(3) F945 台帳の回収追補 (09-18) が「署名で分類した自動再投入は DW-O18 の親判定と同等の手順を満たしたとは記録しない」と既に判定している。
  (4) inbox 資料の実測 (09-18 11:06〜14:35) は 252e24b4f 以前の regime で、F945 は 09-20 に supersede 済み (以後 24 走で setup error 0)。
- 相関と因果の分離: 資料が投入・停止として直接観測したのは「門番の load 条件 (`l1 < l5 ∧ l1 ≤ 30`) が閉じていて 3 wave が計約 6 時間 claim 前のまま」と
  「`postcheck` rc=70 は取り込み後の main への遅れを検出して止める (runbook 既載の残余 race とは別の窓)」など。同時受入本数・load・pigz と F945 型の関係は
  相関にとどまり、資料自身が「同時本数は主因ではない」「門番の条件でこれ以上できることは無い」と結んでいる (上限 1 でも 2/2 赤、pigz 予測力なし)。
- 段 4 の自己裁定: 新 F は起票しない — 門番待ち 6 時間という失敗型について、既存正本への参照だけでは再発を防ぐ具体的対応を資料から示せないため、
  起票先と恒久対応は未裁定として残す (inbox の C)。B (slot)・postcheck 再検討も insight §7 に未採用のまま列挙した。
- 段 6 review 1 本 (gpt-6-astra、read-only、2 レンズ): must-fix 2 / nit 7 / refuted 1、全 real 所見を採用し親が docs を直接直した (対応表は insight §10)。
  must-fix は「MAXTRY は tip を跨ぐ回数」(誤り → 起動 1 回内の投入回数で同一 tip の再走回数を管理しない) と「T-2484 型も文字列一致の分類で、
  親判定の代替に見える書き分け」(→ 署名分類 + 単独再走型に改名し、保証しない旨を明記)。nit で runbook 小節を所在表 + 注意 3 点に縮約 (41 → 36 行)、
  「直接観測した因果は 2 点だけ」を「投入・停止の直接観測」に改め、`postcheck` が検出する競走と runbook 既載の残余 race を別の窓として分けた。
- 受入: 本 wave も job dir の門番 script (leaders ≤ 1 ∧ load1 ≤ 60、自前 merge なし、赤は型を問わず停止、テスト未走の rc=70 だけ再投入) で投入する。
  最終受入の成否はこの記録後の共通受領証で確定する (記録 commit → 最終受入 → land の順)。
- 工数: codex 1 本 (review)、計算ノード job = 受入のみ。

## 次の一手差分

### 完了

- [T-2789] 受入投入・再走の既存運用を docs に整理した。runbook §7.3 の小節と insight `2026-09-20/t2789-acceptance-ops-inventory`。
  門番条件値・自動再投入・新 slot・postcheck 変更は採らず、inbox の B / postcheck 再検討 / C の起票先は未裁定のまま insight §7 に列挙。
  remaining: none
  base: 4847b7e89a3b1ce1b710cf6c9e2325d769cee509e96e7b127254f379cbf9130e
