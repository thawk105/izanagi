# [T-1068] 段 1 brief — trigger 骨格の宣言側と呼出依存の凍結

- wave: `t1068-skeleton-decl-freeze`、worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze`
  (branch `worktree-t1068-skeleton-decl-freeze`、起点 local main `ad114fba03e83de65453f098246e8f0deea7bb64`、開始 gate rc=0)
- 依頼逐語: 同 job dir `request.md`。裁定: 2026-08-16 /rulings 全件 第 3 回 項 22「[T-1068] trigger 骨格 = 凍結する (R4 / R5 / R7 の 3 経路)」、
  理由「凍結領域が『文字は同じだが意味は死んでいる』状態を許すなら凍結という保証が空語になる。合成 variant の受理集合に直結」
  (`docs/archive/worklog-phase3-0816-595-596.md` の [T-1068] 項)。2026-09-26 持ち越し整理 (D2257) で keep、D2260 項 2 (T-733/734 停止) の対象外。

## 研究前進 (土台)
trigger-gating 軸 (D48) の build admission が「mask M の gate」と受理した binary が、実際には常時 backoff / 無 backoff になりうる穴を閉じる。
放置時の成果物影響 (DW-G05): R4/R5/R7 型の source が admitted class で build され、選択結果・材料レポートの「mask M」が実 binary の挙動と食い違う (受理集合が偽を含む)。

## scope
- 対象: `orchestrator/campaign/build_admission.py` `_require_materialized_trigger_axis_predicate` (現 170-219 行) に、BEGIN より前の凍結照合を論理積で足す。
  凍結定数は `orchestrator/campaign/axis_trigger_gating.py` (既存 `FROZEN_TEMPLATE_BLOCK_BYTES` / `FROZEN_TEMPLATE_EPILOGUE_BYTES` の隣)。
- 3 経路の実証差分 (逐語は `output/insights/2026-08-13/t1048-trigger-freeze-epilogue/verbatim/`):
  R4 = consult-b.md 所見 1 (prologue の `bool izanagi_gate_pass = true;` を `struct GatePass {operator=(bool) no-op; explicit operator bool() false}` に差し替え。同所見の 2 例目 = BEGIN 前への `izanagi_abort_reason_ = IzanagiAbortReason::kUnset;` 挿入)、
  R5 = consult-a2.md 所見 2 (宣言と BEGIN の間へ `return;`)、R7 = review-b.md 所見 2 (`#endif` と BEGIN の間へ `const uint64_t FLAGS_clocks_per_us = 0;`、`Backoff` の local shadowing も同型)。
- 同じ単位に置くもの: 3 経路それぞれの負例 (拒否) と、既存の凍結済み差分の正例 (引き続き受理: pristine block、32 mask の hole、epilogue 後の後続 bytes、S8a の計装 tally 重ね当て形)。
- scope 外: R6 dangling else ([T-1069])、R1 (コメント化・raw string・前処理器による識別子置換)、R3 (ABA 窓)、`FileNotFoundError` の受理、S8b resume、非 admissible materializer、
  凍結 JSON の再 pin、patch bytes の変更、仮想リスク向けの gate・検査・台帳・一般化。

## 確定済みの不変条件
- 規律 2 を緩めない: 受理集合は狭くなるだけ。既存の三分岐 (ENOENT 受理 / marker も token も無い stock 受理 / marker ありは照合) と block・epilogue 照合は変えない。
- 既存テストの期待値を変えない (fixture の形を実物へ寄せる更新は可。ただし受理・拒否の期待は変えない)。patches/*.patch は変更しない。
- `axis_trigger_gating.py` の sha256 は凍結 JSON (known_axes / measurement / holdout) の記録値 47507d9b… と wave 前から不一致で、
  `s1_known_axes_freeze.py` の `_HISTORICAL_CODE_PATHS` が許容している。再 pin しない (T-1048 と同じ扱い)。
- `build_admission.py` と `axis_trigger_gating.py` は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` の閉包 (HEAD blob 束縛) に入る。
  未 commit の変異は contract-loader-drift 層でも殺されるので、変異の期待 node は probe で実測し drift 層分を分けて登録する (段 4)。
- 変更前 sha256: build_admission.py 3991861580de…、test_build_admission.py 87df6529…、axis_trigger_gating.py efb6fc64…。

## 前提の実測 (親、2026-09-27)
- 骨格適用後の abort() 全文 = 同 job dir `evidence/transaction.cc.skeleton-applied` (pin 6810666 の CCBench に骨格 patch を当てたもの)。
  関数冒頭 (`void TxExecutor::abort() {` 〜 `#endif` + 空行、CCBench 原文 20 行) → 骨格 prologue (`#if BACKOFF_TRIGGER_GATING` + コメント 4 行 + `bool izanagi_gate_pass = true;` + `#endif`、patch 所有 7 行) → BEGIN。
- 骨格に重ねる producer は S8a characterization の `s8a_trigger_coverage.py` (tally + misattr) と `s8a_trigger_freq.py` (tally) だけ。どちらも admitted 経路。
  tally patch は abort() の開き括弧の直後 (`// remove inserted records` の前) に `#if BACKOFF_TRIGGER_GATING && TRACE` block を挿入する。misattr は lockWriteSet だけ。
  他の producer (S1 direct comparison・S-1 extime・S8a sweep・E 段 driver・S8b expected materialization) は骨格 + hole 置換のみ。
- C2' (`40a7f4acb`、pin 前進の候補) の silo 差分は writePhase だけで abort() に触れない。
- test fixture: `test_build_admission.py` の `_trigger_source_bytes` (BEGIN 前は説明コメント 1 行)、`test_campaign.py` の `_write_materialized_trigger_source`、
  `test_buildcache_v2.py::test_qualification_stock_build_case_dependency_options` (実 checkout の block を上書き)、
  `test_reflux_campaign_issuer.py::_synthetic_silo_checkout` (実際に compile して走らせる合成 checkout。関数は `static void exercise_trigger_gate()`、BEGIN 前は `bool izanagi_gate_pass = true;` 1 行のみ)。

## 親の provisional 裁定 (攻撃対象)
- (P1) 凍結範囲。案 A = BEGIN 直前に隣接する骨格 prologue (patch 所有 7 行) だけを凍結。案 B = `void TxExecutor::abort() {` から BEGIN までを凍結し、
  受理形は「骨格のみ」と「骨格 + tally」の 2 形。**親の provisional は B。** 理由: A は R5 の `return;` と R7 の shadowing 行を prologue の 1 行上 (同じ関数本体) へ動かすだけで通り、
  3 経路を閉じたことにならない (裁定理由の「空語」がそのまま残る)。B は abort() 内で呼出より前にある全ての局所宣言・制御流を固定する。攻撃点: CCBench 原文 bytes への結合 (pin 前進時)、合成 fixture の書換え費用、tally 形の受理が穴にならないか。
- (P2) 照合方式は T-1048 と同型の逐語照合 (BEGIN 行頭から後ろ向きに凍結 bytes の隣接一致)。C++ 字句解析・制御流解析は作らない。
- (P3) 凍結定数の正本性は独立テストで固定する: 骨格 prologue 部分は `silo-backoff-trigger-gating-variant.patch`、tally 部分は `instr-silo-backoff-trigger-gating-tally.patch`、CCBench 原文部分は pin の CCBench source と照合 (方法は plan に委ねる)。
- (P4) 残る限界 (docstring に明記): 前処理器マクロによる置換 (R1 族)、他 file (header の class member) による名前解決の差し替え、file scope の宣言、R6、R3、ENOENT。
- (P5) 実装は 1 単位 (build_admission.py + axis_trigger_gating.py + テスト 4 file の fixture)。所有が分かれないので Codex author 1 本。

## 成果物
- 実装差分 (Codex author)、正例・負例テスト、変異 matrix (段 4 で事前登録)、受入全走、insight `output/insights/2026-09-27/t1068-skeleton-decl-freeze/README.md`、spool fragment (worklog / decisions)、phase3 の該当チェック (あれば)。

## 受入・実測環境
- テストは計算ノード (`tools/dev_wave_wait.py acceptance`)。実走所在は worklog、機体固有は `docs/pegasus-runbook.md`。login node で pytest を回さない。
