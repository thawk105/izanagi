# [T-1068] trigger 骨格の宣言側と呼出依存を凍結した — wave 記録

branch `worktree-t1068-skeleton-decl-freeze` / 2026-09-27 14:3x 〜 (JST)。起点 local main `ad114fba0`。
依頼 (ユーザー直接起動の `/dev-wave`、逐語 = `verbatim/request.md`)。裁定 = 2026-08-16 /rulings 全件 第 3 回 項 22「trigger 骨格 = 凍結する (R4 / R5 / R7)」。
前 wave の記録 = `output/insights/2026-08-13/t1048-trigger-freeze-epilogue/README.md` (R4〜R7 の起票元)。

## 何を直したか

build admission の trigger 軸検査 (`orchestrator/campaign/build_admission.py` の `_require_materialized_trigger_axis_predicate`) は、
BEGIN..END の block と END 直後の epilogue の逐語一致だけを見ており、**BEGIN より前を 1 byte も読んでいなかった。**
そのため block と epilogue を逐語一致させたまま、次の 3 経路で gate を無効化できた (実証差分は T-1048 の段 3・段 6 の子成果物)。

| ID | 経路 | 実証差分 |
|---|---|---|
| R4 | prologue の `bool izanagi_gate_pass = true;` を `operator=(bool)` を無視し `false` に変換する型へ差し替え / BEGIN 前での `izanagi_abort_reason_ = kUnset;` | T-1048 consult-b.md 所見 1 |
| R5 | 宣言と BEGIN の間へ `return;` (hole と gated call が非到達) | T-1048 consult-a2.md 所見 2 |
| R7 | `const uint64_t FLAGS_clocks_per_us = 0;` などの局所 shadowing で `backoff(0)` | T-1048 review-b.md 所見 2 |

marker のある source について、**BEGIN 行頭直前の bytes が、`void TxExecutor::abort() {` から始まる凍結 2 形のどちらかで終わる**ことを論理積で足した。

1. 骨格のみ = `FROZEN_TEMPLATE_ABORT_HEAD_BYTES` + `FROZEN_TEMPLATE_PROLOGUE_BYTES`
2. 骨格 + S8a 計装 = HEAD の宣言行直後へ `FROZEN_TEMPLATE_ABORT_TALLY_BYTES` を挿入したもの + PROLOGUE

3 定数は `orchestrator/campaign/axis_trigger_gating.py` に置き、出所ごとの独立テストで固定した:
HEAD ↔ pin 6810666 の CCBench 原文 (`git show <CURRENT_PIN>:cc/silo/transaction.cc`)、PROLOGUE ↔ `patches/silo-backoff-trigger-gating-variant.patch`、
TALLY ↔ `patches/instr-silo-backoff-trigger-gating-tally.patch`。実行時には patch も CCBench も読まない。

## 変更後の受理言語 (T-1048 の条件 1〜3 に 4 を足す)

1. BEGIN と END が各 1 件、BEGIN が END より前。
2. BEGIN 行頭から END 行末までの block が pristine か、hole 1 行だけが 32 mask の emitter 出力と exact 一致。
3. END 行末の直後に凍結 epilogue が隣接する。
4. **(本 wave) BEGIN 行頭直前の bytes が上の 2 形のどちらかで終わる。宣言行より前の bytes は比較しない。**

source 不在の受理、marker も skeleton token も無い source (stock) の受理、block・epilogue の照合、呼出し元 (`derive_build_admission` / `require_build_admission`) は変えていない。
**受理集合は狭くなるだけである。**

## 閉じたもの、閉じていないもの

**閉じたのは、`abort()` 宣言行から BEGIN 行頭直前までの領域内での R4・R5・R7 の提示形と、同じ領域内への移設形である。**
案 A (BEGIN 直前の骨格 prologue 7 行だけを凍結) を採らなかったのはこのためで、案 A では `return;`・shadowing・reason reset を prologue の 1 行上 (同じ関数本体) へ動かすだけで通る。
変異 M2 (照合を prologue 7 行だけへ弱める) がこの差を実測で示している (移設版 4 件と tally 位置の `return;` が受理側へ落ちる)。

残る限界 (docstring に明記し、閉じたとは書かない):

- 宣言行より前の bytes (file scope の宣言、前処理器による識別子置換 = R1 族、行継続・`#line`・BOM)。byte 照合は C++ の意味を判定しない。
- 他 file (header の class member) による名前解決の差し替え。
- R1 (コメント化・raw string)、R3 (evidence 取得から compiler read までの ABA 窓)、R6 (epilogue 直後の dangling `else`、[T-1069] で別扱い)、source 不在の受理。
- 適用範囲は fresh admitted build (derive / require を通る経路: S1 direct comparison、S-1 extime、S8a coverage / freq / sweep、E 段 driver、S8b expected materialization)。
  S8b resume・非 admissible materializer には伝わらない (T-1048 から既知)。

## 設計の決着

- **凍結範囲 (段 1 の P1):** 案 B (関数冒頭から BEGIN まで)。段 2 plan・段 3 の 2 レンズとも支持。
- **受理形は 2 つだけ:** S8a の計装 tally は開き括弧の直後に入るので第 2 形が要る。misattr は `lockWriteSet` だけを変えるので専用形は置かない (段 3 レンズ B)。
- **CCBench 原文 bytes への結合:** HEAD は pin の原文 20 行に結合する。pin 前進で abort() 冒頭が変われば、HEAD ↔ pin 原文の独立テストが赤になって検出する。
  候補の C2' (`40a7f4acb`) の silo 差分は `writePhase` だけで abort() に触れないことを段 1 で確認した。
- **凍結 JSON は再 pin しない:** `axis_trigger_gating.py` は凍結 JSON (known_axes / measurement / holdout) の記録値 `47507d9b…` と wave 前から不一致で、
  `s1_known_axes_freeze.py` の `_HISTORICAL_CODE_PATHS` が許容している。T-1048 と同じ扱い。

## fixture の更新 (受理・拒否の期待は変えていない)

- `test_build_admission.py` の `_trigger_source_bytes`、`test_campaign.py` の `_write_materialized_trigger_source` は HEAD + PROLOGUE を前に付ける。
- `test_reflux_campaign_issuer.py` の合成 checkout は実際に compile されるので、`static void exercise_trigger_gate()` を `TxExecutor::abort()` + 最小 stub に替えた。
  canonical HEAD が `#if ADD_ANALYSIS` を含むため、合成 `Options.cmake` に実 CCBench と同じ形で `ADD_ANALYSIS` を universal 定義として供給した。
  **source_digest の未知マクロ検査 (T-148) は変えていない。** 焦点走 1 でこの検査が fail-closed で止めたのが発見の経緯である (静的レビュー 4 本は見落とした)。
- `test_buildcache_v2.py::test_qualification_stock_build_case_dependency_options` の借用 checkout は `class Transaction { void abort() ... }` 形だったので、
  class と関数を丸ごと canonical な閉じた形へ置き換え、同じく `ADD_ANALYSIS` を供給した。観測点 (build option と configure 引数) は不変。

## 実測

| 何 | 結果 |
|---|---|
| 焦点走 f1 (commit `56b810852`、34 file、計算ノード 31344.nqsv) | 10 failed / 5,159 passed / 26 skipped (441 s)。赤は buildcache fixture 7 件 (ValueError) と reflux 合成 checkout 3 件 (ADD_ANALYSIS 未知マクロ) で、いずれも fixture の形 |
| 焦点走 f2 (commit `4ea4d601d`、fix した 2 file、31382.nqsv) | **271 passed / 0 failed** (10.67 s) |
| 単独走 (M3、`test_campaign.py` 1 file) | **458 passed / 3 skipped / 0 failed** (27.59 s) |
| 変異 probe (commit `4ea4d601d`、runner = `test_build_admission.py`、15:50〜16:17 JST) | baseline PASSED。観測 node は段 4 の見込みと完全一致、contract-loader drift の node は 0 |
| 変異 final (同 commit、16:18〜16:26 JST) | **baseline PASSED、7/7 KILLED、MISMATCH 0、SURVIVED 0、rc=0** |
| 検出語の機械走査 (`s8b_holdout_freeze search`、記録前) | rc=1。hit は既存の `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の 3 file だけで、本 wave が足した file は 0 件 |
| 受入全走 | 本 README を含む記録 commit の tip で実施する (記録時点では未実施) |

## 変異の帰属 (期待 node は probe で実測し、final で完全一致)

| ID | 変異 | 落ちた node | 種類 |
|---|---|---|---|
| M1 | 追加検査を削除 | 負例 10 件すべて (R4 2・R5・R7 2・移設版 4・tally 位置の `return;`) | 拒否側 |
| M2 | 照合を PROLOGUE 7 行だけの `endswith` へ弱化 (= 案 A) | 移設版 4 件 + tally 位置の `return;` | 拒否側 |
| M3 | tally 形を受理形から削除 | `test_trigger_axis_accepts_tally_abort_prefix` | 過剰拒否側 |
| M4 | 宣言行の前に改行を要求 (比較範囲を宣言行より前へ広げる) | `test_trigger_axis_accepts_bytes_before_abort_declaration` | 過剰拒否側 |
| M5 | 宣言行直後〜`  // remove inserted records` を任意 bytes で受理 | `tally-slot-return` だけ | 拒否側 |
| M6 | PROLOGUE 定数のコメント 1 語を変える | `test_frozen_trigger_prologue_matches_template_patch_bytes` だけ | 独立照合 |
| M7 | HEAD 定数のコメント 1 語を変える | `test_frozen_trigger_abort_head_matches_pin_source` だけ | 独立照合 (計算ノードで skip されず実走したことの証拠を兼ねる) |

M6・M7 は、定数から入力を作る他のテストが同時に動いて落ちないことを示す (T-1048 の MUT-3 と同型)。生台帳は repo 外
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/mutation/` (spec-probe / spec-final / *-results.json)。

## 子の工数

| 段 | model / effort | 結果 |
|---|---|---|
| 段 2 plan | gpt-6-sol / medium | accepted、model call 11 |
| 段 3 consult A (正しさ境界・実効性) | gpt-6-sol / medium | accepted、14 |
| 段 3 consult B (過剰・削除) | gpt-6-sol / medium | accepted、12 |
| 段 5 author | gpt-6-sol / medium | accepted、35 (241 変更行) |
| 段 6 review A / B | gpt-6-sol / medium | accepted、A = NO-GO (must-fix 1)、B = GO |
| 段 6 fix-1 | gpt-6-sol / medium | accepted (fixture 2 file、合算 276 変更行) |
| 段 6 焦点再レビュー | gpt-6-sol / medium | accepted、GO (A-1・F2 とも closed) |

Claude 子 1 本 (sonnet、Explore、trigger 骨格と重なる producer の棚卸し、read-only)。

## 逐語

`verbatim/` に依頼・brief・段 4 / 段 6 の裁定・段 2〜段 6 の子成果物を置く。
