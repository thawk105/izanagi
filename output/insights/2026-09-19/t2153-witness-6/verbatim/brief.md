# 段 1 brief — [T-2153] 意味 witness 対応集合を既存機構で届く範囲だけ広げる ((d)(e)(f) の 6 macro)

- 日付: 2026-09-19。base = local main `a99425b66` (worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6`、branch `worktree-dev-wave-t2153-witness-6`)。job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-6/`。
- 研究前進: B-10 / certified 選択の条件 gate で「意味の節が空のまま受理」される macro (D1569 が問題視) を減らす。完了判定 = 対象 6 件それぞれについて「実 TU で witness が立つ (登録簿へ足す)」か「既存機構では届かない (理由を一次資料に構造化)」が実測で決まり、足した分の consumer で `unestablished_meaning_macros` が実際に縮む (D1492)。
- 正本: `docs/archive/worklog-phase3-0917-1598.md` [T-2153]、`output/insights/2026-09-17/t2153-s2-pegasus-calibration/README.md`、entry 1195 (`output/insights/2026-09-02/t2153-meaning-witness/README.md` の「動かせなかった 13 件」)、D1490 / D1491 / D1492 / D1569 / D1613、T-2737 (`output/insights/2026-09-18/t2737-ss2pl-gate-controls/README.md` §2 §7、D2141)。

## scope (確定済みユーザー裁定)
- 対象: (d) `SS2PL_LOCK_IMPL` / `SS2PL_LOCK_KIND` / `SS2PL_DLR` / `SS2PL_WFG_DIAG`、(e) `SORT_VARIANT`、(f) `IZANAGI_SILO_LADDER_RUNG1_REPORT`。各件を実 TU で witness が立つか実測してから `CONDITIONAL_BRANCH_WITNESSES` へ足す。
- scope 外 (理由を記録するだけ): (b)(c) の機構変更 (定義/未定義の観測・複数箇所の代表選択)、S2 driver の Pegasus 4 固定値変更、追加 gate・一般化。規律 2 を緩めない。実装は `condition_meaning_gate.py` 系、Codex author (D95)。

## brief 前の実測 (login pegasus02、production CLI そのまま、登録簿未変更、逐語 = job dir `pre-*.stdout.jsonl`)
- 実 patch 適用後の所有 TU (scratch `/work/1/SFC/tanab/dev-wave-scratch/t2153-witness-6-20260919/ccbench-511c953-{ss2pl,sort,rung1}`、pin `511c953`) の directive 逐語出現数と、gate の supply arm:
  | macro | 所有 TU 内の一意 directive (要求 1 → 選択 / 既定 0 → 非選択) | 他の出現 | supply (現行) |
  |---|---|---|---|
  | SORT_VARIANT | `#if SORT_VARIANT` ×1 | なし | green (admitted) |
  | RUNG1_REPORT | `#if IZANAGI_SILO_LADDER_RUNG1 && IZANAGI_SILO_LADDER_RUNG1_REPORT` ×1 (所有 TU `cc/silo/ycsb_silo.cc`、companion RUNG1=1) | なし | green (admitted) |
  | SS2PL_LOCK_IMPL | `#if SS2PL_LOCK_IMPL == 1 \|\| SS2PL_WFG_DIAG` ×1 (複合) | `== 1` ×15、`== 0` ×4 | red `dependency-closure-drift` |
  | SS2PL_WFG_DIAG | 同じ複合行 ×1 | `#if SS2PL_WFG_DIAG` ×44、`#elif` ×1 | red `dependency-closure-drift` |
  | SS2PL_DLR | `#if SS2PL_DLR == 1` ×1 | `!= 1` ×1 | red `compile-command-drift` (CMake が `DLR0`/`DLR1` marker を同時に変える) |
  | SS2PL_LOCK_KIND | **なし** (実体は `wfg.cc:74` と `ss2pl_lock.hh:52` の template 引数) | — | green (admitted、未確立) |
- 機構の制約 (現物): 宣言は `source_rel ∈ spec.owner_tus` (header 不可、BACKOFF_NOINLINE だけ例外) かつ要求 "1" / 既定 "0"。directive 逐語は所有 file 内にちょうど 1 回。期待対は要求 (1,1) / 既定 (0,1)。meaning arm は CMake configure 由来の実 argv を使い、要求/既定の argv が試験 macro の -D 以外で一致することを要求 (`compile-command-drift`)。dependency closure は meaning arm では比較しない。companion は presence 検査のみ。
- 登録簿会員の supply 側への影響は `ROUTE_CMAKE_CXX_FLAGS` の共有 build root 分岐だけ → RUNG1_REPORT のみ該当。
- consumer (D1492 の配線対象候補): SORT_VARIANT = `p3_s4_loop_sort._require_condition_gate` (要求 value / 既定 0、`declaration=None`)、`s6_sort_sweep._require_condition_gate` (1/0、`declaration=None`)、**`s1_direct_comparison` (factory 配線済み、`_CONDITION_DEFAULTS` に SORT_VARIANT: 0 → s8b floor / oracle / s8c の official sort_best cell で自動発火)**。RUNG1_REPORT = `silo_ladder_rung1` (1/0、rung-liveness build のみ、RUNG1=1 を同時要求し実 flag 照合、`declaration=None`)。paper_story_a2 は `defaults` が BACKOFF 2 件のみで非該当。SS2PL runner (`tools/pegasus/run_ss2pl_lock_study.py`) は KIND 0 vs 1 / DLR 0 vs 1 で登録簿の 1/0 対と不一致、現行 patch は supply 全 arm 拒否 (T-2737 §2 と本 wave 実測が一致)。
- DW-O09 閉包: gate module・3 driver の現行 sha256 は output/・凍結成果物に出現なし。`s1_known_axes_freeze._HISTORICAL_CODE_PATHS` が sort 2 driver を歴史記録扱い。`test_condition_meaning_gate.py` は `_COMPILE_TIME_BRANCH_MACROS` (順序 tuple) と `_patch_added_branch_declaration` (patch の `+#if {macro}` 逐語ちょうど 1 件) で登録簿を pin → 複合 directive / companion は helper 拡張が要る。`MEANING_SUPPORTED_MACROS` の集合 pin もある。

## 親の provisional 裁定 (攻撃対象)
- (P1) **SORT_VARIANT を足す。** entry 1195 の不採用理由「driver 配線が編集面を超える」は、配線が `declaration=None` → `declare_define_runtime_meaning(request)` の 1 行 ×2 driver (p3_s4_loop_sort / s6_sort_sweep) で済み、s1 は既配線で自動発火するため解消。受理集合は狭まる向きのみ (unestablished→green admit / red reject)。official sort_best cell に初めて meaning arm が走る — 環境要因の偽赤 (masstree `config.h`) は s8b の shared dependency prebuild と `_condition_gate_offline_configure_args` の同形供給で回避されるはず (要検証)。
- (P2) **RUNG1_REPORT を足す** (companion RUNG1=1 下の witness、所有 TU `cc/silo/ycsb_silo.cc`)。entry 1195 の懸念「再注入で実 build に RUNG1=1 が無くても緑」は唯一の consumer が rung-liveness build でのみ REPORT を要求し RUNG1 も同時要求・実 flag 照合するため到達不能 (F707 型の隙間は driver 側契約で閉じている)。配線は silo_ladder_rung1 の 1 行。supply 側は共有 build root 分岐へ移る (実測で確認)。
- (P3) **SS2PL_LOCK_IMPL / SS2PL_WFG_DIAG は足さない。** 唯一の一意 directive は複合行 1 本で、本来の意味を担う 19 / 45 箇所は非一意 = (c) 型。複合行 1 本を代表にするのは entry 1195 が退けた「代表 1 箇所で macro 全体の意味を過大主張」そのもので、(c) 代表選択の機構変更は scope 外。加えて現行 patch は supply 赤で family は拒否のまま (T-2737 §7 の裁定待ち)。meaning arm 単独の実測 (緑/赤) は記録のために取る (段 5 の job-dir probe)。
- (P4) **SS2PL_DLR は足さない。** 一意 directive はあるが CMake が marker define を同時に変え、meaning arm の argv 比較で `compile-command-drift` になる (既存機構では届かない)。実測で確認。
- (P5) **SS2PL_LOCK_KIND は足せない** (所有 TU に指令なし、静的事実)。`owner_tus` へ `wfg.cc` を足すのは DefineSpec の意味変更 (supply arm の対象 TU も動く) で scope 外。
- (P6) 実測は login (pegasus02) の production CLI + 段 5 の Codex 製 job-dir probe (shadow 登録簿、≤100 行、DW-G01)。計算ノード再走はしない (T-2153 S2 で login / 計算ノードの前処理 bytes 一致を実測済み、本件は pass/fail)。official 経路の同形供給 (`-DFETCHCONTENT_BASE_DIR` + SOURCE_DIR 3 本 + PREFIX_PATH) でも 1 回通す。
- (P7) 順序: 段 5 で Codex author が (i) job-dir probe で 5 候補 (LOCK_IMPL / WFG_DIAG / DLR / SORT_VARIANT / RUNG1_REPORT) の meaning arm を実 patched tree で実測 → 親が結果を確認 → (ii) 同 author が確定集合 (P1・P2 が緑なら 2 件) の登録簿 + test + 配線 3 行を実装。赤なら足さず理由を記録。

## 不変条件
- 規律 2: 受理集合は狭まる向きだけ。旧 `MeaningWitnessDeclaration` / CLI の `--meaning-case` 経路は BACKOFF_FIXED 固定のまま (D1491)。factory の要求 1 / 既定 0 条件、probe の挿入形、一意性・非識別・完了 marker の検査、`DEFINE_SPECS` は 1 行も変えない。
- 凍結成果物の bytes 不変。durable manifest の再発行なし。既存 `output/env/**/calibration/*.json` 不変。
- 実装面は Codex author のみ。親は docs (insight / spool fragment / handoff) だけ。

## 成果物
- 実装: `orchestrator/campaign/condition_meaning_gate.py` (`_CONDITIONAL_BRANCH_WITNESSES` +2 見込み)、`orchestrator/tests/test_condition_meaning_gate.py` (pin と fixture の拡張、複合 directive + companion の正例・負例)、配線 `p3_s4_loop_sort.py` / `s6_sort_sweep.py` / `silo_ladder_rung1.py` 各 1 行 + その test。
- 記録: `output/insights/2026-09-19/t2153-witness-6/README.md` (6 件の判定表、実測逐語、届かない理由)、spool fragment (worklog / decisions)。

## 並列分割
- 段 2 plan 1 本、段 3 consult 2 本 (レンズ A = 正しさ防壁・受理集合・F707/恒真ゲート、レンズ B = 閉包・pin・consumer 回帰・official 経路の偽赤)、段 5 author 1 本 (probe → 実装の 2 段)、段 6 review 2 本 + fix。
