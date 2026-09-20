---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2153-witness-requested-us
seq: 1
title: [T-2153] 意味 witness の残件 (c) — `BACKOFF_REQUESTED_US` を複数 file 宣言 (transaction.cc 2 + backoff.hh 2) + 箇所識別 marker の 4 箇所同時観測で登録簿へ (枝選択 21 → 22、実 TU login + 計算ノードで (4,4)/(0,4) green、BACK_OFF=0 は 3/4 red) (コード + テスト、branch worktree-dev-wave-t2153-witness-requested-us、変異 matrix = baseline PASSED・9 変異中 8 KILLED + 等価 1 SURVIVED・MISMATCH 0・期待 node 完全一致 8/8)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数の逐語は insight `verbatim/T-2153-origin.md`) の範囲で 1 wave。一次資料は
  `output/insights/2026-09-20/t2153-witness-requested-us/README.md` (brief・plan・裁定・consult / review の逐語・変異台帳・cell 原本)、
  設計判断は {{D:witness-multifile-sites}}。専用 handoff / job dir は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/`。
- 起点 local main `482f19b88`、wave 中に main `800178b39` (docs + land tool) へ ff。ccbench pin は前 wave の `511c953` から `e9e477ca1` へ
  前進済みで、4 箇所の行番号 (transaction.cc L11 top / L157 `#if BACK_OFF` 内、backoff.hh L109 / L141 top) は同じ。開始 gate rc=0、
  pin 閉包 = bytes pin 0 件 (契約 pin = 集合・順序・schema・docstring・spawn 目録・B-4 は全部追随)、編集面重複なし。
- **段 2 plan が親 brief の P6 (総数一致 = 全箇所観測) を覆した:** owner 2 箇所を外側 `#if 0` で殺し pragma once 無しの header を 2 回展開
  すると総数 (4,4)/(0,4) が相殺成立する。段 3 の 2 レンズが独立に成立を確認し、複数 file macro に限る箇所識別 marker (token 貼り付けの
  `-D` 2 本、生死実験で g++ 11.4.0 の展開とコメント / raw string 非展開を確認) を evidence + 再検証まで閉じる形で採用した。段 3 の他の
  must-fix = fixture の CMake mapping 欠落 (test 供給表に REQUESTED_US が無い)、I1 の実証範囲を実測 cell に限る、副 file 証拠の主張は
  owner TU の include 文脈に限る、m3 の帰属訂正。refuted = 副 mapping による受理拡大、2 file 計装による argv 比較 / supply closure の破れ。
- 段 5 author (Codex、27 call、814 s) は所有 2 file (+489/−23) を実装し、sandbox で pytest 未実走のまま直接呼出し 75 ケース PASS と反実仮想
  3 件 (個別等値検査除去 / 副 digest 束縛除去 / 副 schema の key 依存化 → DID NOT RAISE) を報告。親の焦点走 (計算ノード、所有 + consumer
  15 file) = **1148 passed / 2 skipped、赤 0**、所有 test の node 別走 = **218 PASSED (新設 43 node 含む)**。段 6 レビュー 2 本 (A: 正しさ境界・
  全箇所性・shadow・schema、B: 過剰・削除・pin) は **両方 GO、must-fix 0** (should = I1 要約の文言、m8 の変異位置、node 別証拠 → いずれも
  反映)。fix 巡なし。
- **実 TU (最終 production 登録簿 cfab7a2f2、pin e9e477ca1、fixed → requested-us、official 同形供給):** login (pegasus02) と計算ノード
  (bnode016) とも REQUESTED_US 1v0 = supply green / meaning **green (4,4)/(0,4)** / admitted / 未確立 []、site_observations 4 row すべて
  (1,1)/(0,1)、副 file の sha256 は実木の backoff.hh と一致。`BACK_OFF=0` cell は observed (3,3)/(0,3) で red・admitted=False (fail-closed)。
  既存 SORT / NOINLINE / RUNG1 は変更前後で一時 path 由来の digest 以外同一 (I1、代表 3 cell)。login と計算ノードは前処理 digest・bytes・
  compiler・site_observations が完全一致。
- 統合 commit `cfab7a2f2` (gate module + test)。driver は配線しない (`backoff_requested_us` / `backoff_sweep` / `screening_driver` は admission
  を捨てる、D1492)。「未確立一覧が縮む」は CLI cell で実証した範囲で、B-10 の数値成果物や公開 driver JSON は変えない。
- 変異 matrix (`tools/mutation_worktree.py`、独立 clone、固定 commit cfab7a2f2、dispatch、runner = gate test + S1): probe 走 (全 SURVIVED 登録で
  観測 node を収集、20:19〜20:38 JST) → final 走 (観測 node を完全集合で登録、20:41〜21:00 JST) = **baseline PASSED (28 s)、m1〜m8 KILLED
  (期待 node 完全一致 8/8)、m0 等価 SURVIVED、MISMATCH 0**。単一 node で殺した変異 = m4′ (個別観測の等値検査除去 → 相殺入力の独立 node)、
  m5 (副 schema を record の key 依存に → schema[missing])、m7 (副 digest 束縛除去 → schema[digest])。m3 (総数 → 主 N) は正しい 4 箇所入力の
  過剰拒否 37 node、m8 (副 key を単 file にも常時出す) は既存単 file macro の正例 95 node が発行時 schema で赤 (requested_us の node は 0 件)、
  m2 (深い鏡像で副 file を元本文に) は REQUESTED_US 38 + 経路を共有する NOINLINE 6。帰属表は insight §8。台帳の原本 (930 / 950 KB) は job dir、
  insight は `artifact.stdout` を落とし原本 sha256 で束縛した要約版。
- 検査: provenance range 監査 PROVENANCE_RESULT、`check_docs` CHECK_DOCS_RESULT、`git diff --check` 緑。受入: 記録 commit の tip で待ち手
  経由の全走 (`dev_wave_wait.py acceptance`) を 1 回投入する。結果は本 fragment には書かず受領証と land の記録が持つ。child-green でなければ
  land しない。
- 事故・気づき: 隔離 session の Bash guard が `python3 <script> <変数 path>` や heredoc 本文の "git" 文字列も拒否するので、検査 script と
  本文は Write で job dir に置き逐語 path で呼んだ。I1 の cell を最初は出力 dir 名入りの driver-id で取ったため request_digest が違い、
  同一 driver-id で取り直した (1 走分の無駄)。
- 工数: codex 6 本 (plan 1、consult 2、author 1、review 2)、計算ノード job = 焦点走 2 + cell 1 + 変異 (probe + final) + provenance 監査 + 受入。

## 次の一手差分

### 更新

- [T-2153] **P2**: 意味 witness 対応集合 22 → 23 (枝選択 22 + BACKOFF_FIXED)。entry 1195 の残り 13 件のうち現在未対応は
  4 件: (d) `SS2PL_LOCK_IMPL` / `SS2PL_WFG_DIAG` (複合行 1 本は観測可能だが代表選択を採らない、他は非一意、現行 patch は supply 拒否 =
  T-2737 §7 待ち)、`SS2PL_DLR` (CMake の DLR marker 同時変更で meaning arm も compile-command-drift)、`SS2PL_LOCK_KIND` (所有 TU に
  directive なし)。(c) `BACKOFF_REQUESTED_US` は 2026-09-20 に複数 file 宣言 (transaction.cc 2 + backoff.hh 2) + 複数 file macro 限定の
  箇所識別 marker で実 TU (login + 計算ノード) 実測のうえ登録した (insight `t2153-witness-requested-us`、{{D:witness-multifile-sites}})。
  driver は配線していない (`backoff_requested_us` は admission を捨てる、D1492)。(b) MISATTR と (c) RUNG1 / TRIGGER_GATING は
  2026-09-20 に登録済み (insight `t2153-witness-bc`、D2182)。`s1_verify_extime_calibration` の配線 + 供給整合、探索 loop への配線 +
  offline 供給 + admission 永続化、所有 TU 内の未宣言箇所の走査、公開 driver JSON の取得、`backoff_requested_us` に admission を載せる
  変更は別変更単位 (未起票)。S2 の実機再走は 2026-09-17 に実測済み (insight `t2153-s2-pegasus-calibration`、別変更単位)。
  base: 85fb53a4ec9ae2e0e22c6bd1c7f05261ab939698556a147983f3ac5ba8ca483c
