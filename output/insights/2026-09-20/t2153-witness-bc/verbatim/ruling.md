# 段 4 裁定 — [T-2153] (b)(c) (dev-wave-t2153-witness-bc、2026-09-20 14:15 JST)

## 所見の裁定 (real / refuted、採用 / 不採用、scope 内 / 外)

| # | 出所 | 判定 | 採否 | 裁定 |
|---|---|---|---|---|
| A1 | 相談 A | real | 採用 (主張範囲の限定 + 記録) | TRIGGER_GATING の witness の主張範囲は **DefineSpec が宣言する patch (`silo-backoff-trigger-gating-variant.patch`) の全 12 箇所**に限る。重ね当て patch (`instr-silo-backoff-trigger-gating-tally.patch:9` の `#if BACKOFF_TRIGGER_GATING && TRACE`) が足す箇所と `#ifndef` 番兵は対象外で、record の `start_directive` + counts、insight、decisions fragment に明記する。「所有 TU 内の未宣言箇所の走査で red にする」機構 (undeclared-site scan) は `#ifndef` 番兵の免除規則を要し本題を超える → **実装せず裁定パッケージ候補として insight §scope 外へ** |
| A2 / B2 | A・B | real | 採用 | supply の対照「macro 不在」検査は **登録簿の directive が `#ifdef` 形の macro に限る**。全 domain の `default=None` へは広げない (既存 `BACKOFF_NOINLINE 1/None`・SORT `1/None` の判定を変えない = I1) |
| A3 | A | real | 採用 | 段 6 の実 TU cell は coverage の 2 構成を分ける: (i) skeleton+instr 木で GATING、(ii) skeleton+instr+misattr 木で MISATTR と GATING、(iii) rung1 木で RUNG1。login + 計算ノード。scratch に `ccbench-511c953-gating-instr` を足す |
| A4 / A5 / A7 | A | refuted / nit | 記録のみ | 不活性箇所・自己入れ子は completion 不足で red (fail-closed) — 負例に含める。factory=None は family 拒否でなく unestablished admit (既存境界) — 主張文に書く。REQUESTED_US 見送り・receipt 分離は妥当 |
| A6 | A | real | 採用 | schema 変異 test は T:1776 と同じく `_validate_arm_record_integrity(..., require_issuer=False)` 形で、正常 record が通り改変だけが落ちる構成にする |
| B1 | B | real | scope 外 (別変更単位) | `s1_verify_extime_calibration` は TRIGGER_GATING を要求し admission を JSON へ載せる (D1492 の対象) が、capture が genome configure と offline 供給を渡さない (`:91`) ため配線だけでは実 build と同形にならない。D2161 理由 (4) と同じく**配線と供給を同じ変更単位で扱う**べきで、本 wave は配線しない。driver 名・残る未確立 (TRIGGER_GATING) を insight と worklog に明記し起票候補にする |
| B3 | B | real | 採用 | 件数は現物: 枝選択 18 → 21、対応集合 19 → 22。所有 5 file (rung1 driver test:105 を含む) |
| B4 | B | refuted (N mapping) / 採用 (削除) | 採用 | 別 N mapping は採用。新 declaration/receipt field・汎用 validator・driver 別対照形 mapping・互換再生 framework は**作らない**。N>1 の不一致 reason `compile-time-branch-site-count-mismatch` は採用 (N=1 の `start-not-unique` 逐語は不変) |
| B5 | B | real | 採用 | 未登録例は `SS2PL_LOCK_IMPL` 1/0。`_patch_added_branch_declaration` は `matches == [expected_pair] * expected_N` (独立期待表)。T:1565 の重複拒否は不変 |
| B6 | B | real | 採用 | REQUESTED_US は登録しない (4 箇所同時観測に複数 file の宣言・capture・shadow・schema 拡張が要る)。「(c) 完了」とは書かず残件として明記 |
| B7 | B | real | 採用 | 完了主張は「CLI cell で成立 (login + 計算ノード)」と「公開 driver JSON (coverage / frequency / rung1) は本 wave では未取得」を分ける。MISATTR の枝選択は誤帰属の発火・検出を証明しない |
| B-pin | B | — | 採用 | `_COMPILE_TIME_BRANCH_MACROS` は末尾追加で既存順序維持、集合 pin は独立列挙、B-4 の 47 module pin は N helper を G 内に置いて不変、凍結 manifest・歴史 hash は不変。B の「`_assert_compile_time_branch_selection` は現物に無い」は誤り (G:3160 に実在) → refuted |
| plan-P4 | plan | — | 採用 | REQUESTED_US 未登録 (上) |
| plan-配線 | plan | — | 採用 | coverage の 2 箇所 (default None for MISATTR、factory) だけ。frequency は helper 共有で自動追随 (回帰確認)、rung1 は既配線 (test:105 更新)。sweep / backoff_sweep / requested_us は返り値廃棄で配線しない |

## プラン v2 (file:line は main 947fd160a 現物)

所有 (author 1 本、子木 `.codex/worktrees/t2153-bc-author`): `orchestrator/campaign/condition_meaning_gate.py`、`orchestrator/campaign/s8a_trigger_coverage.py`、`orchestrator/tests/test_condition_meaning_gate.py`、`orchestrator/tests/test_s8a_trigger_sweep.py`、`orchestrator/tests/test_silo_ladder_rung1_driver.py`。

1. **登録簿 (G:254–310):** 末尾に 3 entry を追加 — `IZANAGI_BREAK_TRIGGER_MISATTR: ("cc/silo/transaction.cc", "#ifdef IZANAGI_BREAK_TRIGGER_MISATTR")`、`IZANAGI_SILO_LADDER_RUNG1: ("cc/silo/transaction.cc", "#if IZANAGI_SILO_LADDER_RUNG1")`、`BACKOFF_TRIGGER_GATING: ("cc/silo/transaction.cc", "#if BACKOFF_TRIGGER_GATING")`。既存 18 entry の値・順序は不変。`_CONDITIONAL_BRANCH_SITE_COUNTS = {"IZANAGI_SILO_LADDER_RUNG1": 2, "BACKOFF_TRIGGER_GATING": 12}` を G:310 付近に置き、`_declared_site_count(macro) -> int` (未掲載 1) と `_declared_contrast_is_undefined(macro) -> bool` (登録 directive が `"#ifdef "` で始まる) の helper 2 つを G 内に置く (新 module なし)。
2. **factory (G:982–1003):** `#ifdef` 形 entry は requested `"1"` かつ default `None` かつ `source_rel in spec.owner_tus` のときだけ宣言。`#if` 形と NOINLINE 特例は不変。
3. **meaning 評価 (G:3160–3335):** G:3173–3180 の `default is None` 拒否を `#ifdef` 形にだけ外す (それ以外は不変)。comparison は `#ifdef` 形で `None`。期待は要求 `(N·int(v), N)`、対照 `(N·int(c), N)` で `None` は 0。`CompileTimeBranchSelectionObservation.define_value` と `_compile_time_observation` の `define_value` を `str | None` に。G:3115 の `observed_defines.get(macro) != define_value` は None で不在検査になる (そのまま)。`_instrument_declared_owner_source` (G:2952–2985) は改行除去の逐語完全一致を全箇所集め、件数 ≠ N なら N=1 は現行 `compile-time-branch-start-not-unique` (detail 逐語不変)、N>1 は `compile-time-branch-site-count-mismatch` (expected=N、observed=件数)。全箇所に現行と同じ `directive / SELECTED() / #endif / COMPLETED() / directive` を挿入し、元の `#endif` を探索しない。
4. **supply 対照の不在検査 (G:2261–2273 直後):** `expected_value is None and not stock_identity and _declared_contrast_is_undefined(request.macro)` のとき `request.macro in observed_defines` なら `supply-value-mismatch` (expected None、observed 値)。他の macro は不変。
5. **green record 再検証 (G:3824–3860、G:3988–4028):** 期待 default は `#ifdef` 形で None、N は登録簿から。`_validate_compile_time_branch_observation` に `completed_count` 期待 (既定 1) を足し、selected は `N·v`。argv 比較は `#ifdef` 形だけ、要求 argv から対象 macro の `-D<M>=1` / (`-D`, `<M>=1`) token を除去して対照 argv と比較。他 macro・`-U` は消さない。`#if` 形の placeholder 比較は不変。
6. **配線 (C:99–135):** `default_value=None if macro == MISATTR_DEFINE else 0`、`declaration=condition_meaning_gate.declare_define_runtime_meaning(request)`。`_build` (C:211–224) の呼び出し形は不変。
7. **test:** (T) `_COMPILE_TIME_BRANCH_MACROS` 末尾 +3; 独立期待表 (macro → (directive, N, contrast)) を registry から導出せず test 内に書く; `_patch_added_branch_declaration` は macro 別 expected directive (MISATTR は `#ifdef …`) で `matches == [pair] * N`; fixture builder は新規 macro に限り N 箇所 + 両腕に無条件本文 (F29 対策); 正例 3 macro (green (N,N)/(0,N)・admitted・未確立 []); 負例 = MISATTR 1/0 (factory None + `#ifdef` fixture の supply 同一出力 red)、対照に `-DM=0` / `-DM` / `-D M=0` 混入 → supply red、1 箇所逐語変更 → site-count-mismatch、1 箇所を `#if 0` に入れる → completed<N red、既定腕だけ 1 箇所選択 (箇所間で再定義) → red、owner prefix `#undef` → not-discriminating; 過剰拒否の正例 = `#if` 形 macro の `1/None` 要求で対照に CMake 既定 `-D<M>=0` があっても supply 判定が現行と同じ (不在検査が発火しない); schema 変異 test は `require_issuer=False` 形で正常 record 受理 + count / None / argv 改変の拒否; 評価側の直接検査 (`_assert_compile_time_branch_selection` を呼び `(2,2)/(1,2)` 拒否); 未登録例 → `SS2PL_LOCK_IMPL`; I1 = `ConditionalBranchMeaningDeclaration` / `CompileTimeBranchSelectionObservation` の field 名集合 pin と、既存 `#if` macro (SORT fixture) の green evidence key 集合 pin。(S) `test_coverage_condition_gate_passes_exact_factory_pair[misattr|gating]` = evaluator を観測 wrapper にし request の default (None / 0) と declaration (型・macro・directive) を検査 (factory / 登録簿は実物)。(rung1 test:105) RUNG1 宣言の型・macro・source_rel・directive を検査。既存 test の期待値は変えない。
8. **scope 外 (実装しない、記録):** REQUESTED_US (4 箇所同時観測)、S1 extime の配線 + 供給整合、undeclared-site scan、探索 loop、SS2PL、S2 再走。

## 変異事前登録 (DW-M01、期待 node は段 6 baseline 後に完全集合へ確定)

| id | 変異 (位置) | 期待 | 単一理由 |
|---|---|---|---|
| m0 | G 登録簿近傍の comment 等価変更 | SURVIVED (等価) | — |
| m1 | C: MISATTR の default を 0 に戻す | KILLED | S の実 helper test [misattr] (request.default 観測) |
| m2 | C: declaration を None に戻す | KILLED | S の実 helper test [misattr][gating] (declaration 型) |
| m3 | G: `_CONDITIONAL_BRANCH_SITE_COUNTS` の GATING 12 → 11 | KILLED | T の GATING 正例 (site-count-mismatch) + patch 束縛 test (`[pair]*N`) |
| m4 | G: 評価側の対照期待を「selected ≤ N·c」へ緩める | KILLED | T の直接検査 (`(2,2)/(1,2)` 拒否) |
| m5 | G: schema 側の default selected 検査を緩める | KILLED | T の schema test (require_issuer=False、partial default 拒否) |
| m6 | G: supply 対照の不在検査を外す | KILLED | T の supply 単独 test (対照に `-DM=0` 混入、数値差 fixture で meaning 側と切り離す) |
| m7 | G: MISATTR entry を登録簿から削除 | KILLED | T の `#ifdef` factory 正例 + 集合 pin (KeyError 型は帰属表で分ける) |
| m8 (過剰拒否の正例) | G: 不在検査を全 `default=None` へ広げる | KILLED | T の過剰拒否正例 (`#if` 形 1/None が現行どおり) |

runner = `tools/mutation_worktree.py` (dispatch mode、独立 clone、固定 commit)、test = `tools/run_tests.py test_condition_meaning_gate.py test_s8a_trigger_sweep.py test_silo_ladder_rung1_driver.py -q -rf`。

## 完了判定 (再掲、訂正込み)

- 登録簿 18 → 21、対応集合 19 → 22。REQUESTED_US は残件。
- 最終 production 登録簿で login + 計算ノードの CLI cell (A3 の 3 構成、official 同形供給、外側条件有効) が MISATTR (1,1)/(0,1)、RUNG1 (2,2)/(0,2)、GATING (12,12)/(0,12) で green / admitted / 未確立 []。
- I1: 前 wave の SORT / REPORT 木で変更前後の CLI record を比較し、key 集合・digest・counts・reason が一致 (path 等の揮発は除く)。
- 公開 driver JSON (coverage / frequency / rung1) の縮小は本 wave では未取得と書く。
