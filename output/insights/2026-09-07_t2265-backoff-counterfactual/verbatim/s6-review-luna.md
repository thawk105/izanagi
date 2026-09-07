## 赤 4 の帰属は誤り。新 sink ではなく行番号 pin の失効

深刻度: blocker

根拠: [`test_ccbench_spawn_sites.py:939`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/orchestrator/tests/test_ccbench_spawn_sites.py:939) の deferred 判定は path・kind・scope・line の完全一致である。台帳は `2718` / `3074` のままだが、現物 sink は driver の追記によって [`2919`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/tools/pegasus/probes/t2187_adaptive_const_probe.py:2919) / [`3275`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/tools/pegasus/probes/t2187_adaptive_const_probe.py:3275) へ移動している。13 件はすべて後者の同一 sink であり、新 sink ではない。

13 define は `BACKOFF_COUNT_CAP_US`, `BACKOFF_COUNT_WINDOW`, `BACKOFF_DYN_CEILING`, `BACKOFF_INCR_MILLI`, `BACKOFF_MAX_US`, `BACKOFF_STEP_ADAPT`, `BACKOFF_STEP_MAX_MILLI`, `BACKOFF_STEP_MIN_MILLI`, `BACKOFF_STEP_POLICY`, `BACKOFF_STEP_POLICY_SEED`, `BACKOFF_TRACE`, `BACKOFF_UPDATE_US`, `IZANAGI_BREAK_NOREAD_VALIDATION`。既存 11 件まで「新 define が作った」とした `reds.md:70` の帰属も誤りである。

正しい追随は件数削除ではなく次である。

- [`test_ccbench_spawn_sites.py:922`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/orchestrator/tests/test_ccbench_spawn_sites.py:922): `2718` を `2919` へ更新。
- 同 `:934`: `3074` を `3275` へ更新。
- 同 `:915-930`: 両理由文の `A+B stack` を現物どおり `A+B+C stack` へ更新。
- 同 `:2679` / `:2683` と `:2694-2704`: exact ledger の写しも同じ line と理由へ更新。
- 同 `:2920`: S1 sink は `covered=4, proven-unreachable=33`。31→33 は sink 増加ではなく、新 define 2 本が同じ S1 sink で到達不能になった分。
- 同 `:2923`: S8B sink は全 37 define を覆うため `covered=37`。

台帳 entry が生きた sink を名指しする条件は path・kind・scope・line の全一致に加え、各 entry がちょうど 1 sink と一致すること (`:2714-2725`) である。

成果物影響: 3 件の赤が残り、build sink 閉包を受理できない。

## pin 閉包は seed と複数の exact pin を落としている

深刻度: must-fix

根拠: `pin-closure.md:1,14-16` は新 define を `BACKOFF_STEP_POLICY` 1 本として扱い、CMake-cache 件数を 19→20 としている。しかし実装は [`condition_meaning_gate.py:124`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/orchestrator/campaign/condition_meaning_gate.py:124) から policy と seed の 2 spec を追加し、正しい件数は [`test_condition_meaning_gate.py:2505`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/orchestrator/tests/test_condition_meaning_gate.py:2505) の 21 である。

残り漏れは次である。

- `BACKOFF_STEP_POLICY_SEED` の `DefineSpec`、screening default、driver flag、遷移テスト define。
- 上記 build sink cross-product 台帳と 35→37 の exact 件数。
- `pin-closure.md:31` の不変 literal 集合に `COUNTERFACTUAL_TRACE_CELLS_TEXT` がない。
- [`tools/plotting/README.md:189`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/tools/plotting/README.md:189) は入力 schema を v2 のみと記載したまま。
- naked-macro 台帳は列挙済みだが、後述の path 単位 allowlist では閉包にならない。

`admission_registry.json` は既存 driver/PBS の path を既に登録しているため、新規 entry が不要という判断は正しい。

成果物影響: 親の pin 閉包を完全集合として再利用すると seed、件数、schema 文書が再び脱落する。

## 赤 3 の path 単位 allowlist は実際に gate を弱める

深刻度: must-fix

根拠: [`test_p3_s4_loop.py:7357`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/orchestrator/tests/test_p3_s4_loop.py:7357) は patch 全文から `IZANAGI_*` を抽出した後、`:7368` で path が allowlist にあれば全 token を免除する。patch C を `known_non_variant_patches` に加えると、将来同 patch に本物の裸マクロが再導入されても検出されない。

patch B と patch C の trace marker は同型である。いずれも `#if BACKOFF_TRACE` 内の stdout 文字列であり、赤 1 の seed 用マクロを除去した後なら現在の false positive の理由に差はない。ただし現在の patch C には [`cicada-adaptive-counterfactual.patch:266`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/patches/cicada-adaptive-counterfactual.patch:266) の実マクロもあるため、赤 1 修正前に path を免除するのは明確な弱体化である。

正しい修正は path 集合ではなく、path ごとの許容 token exact 集合にすること。patch B/C では `IZANAGI_BACKOFF_TRACE` と `IZANAGI_BACKOFF_TRACE_SUMMARY` だけを差し引き、それ以外が 1 件でもあれば赤にするべきである。

成果物影響: 単純な patch C allowlist では裸マクロ防壁の将来回帰検出を失う。

## v2 互換は図生成器では正しいが certification 系では未完了

深刻度: must-fix

根拠: 図生成器は [`plot_dynamic_backoff.py:266`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/tools/plotting/plot_dynamic_backoff.py:266) で A+B / A+B+C の path・順序・digest 対応を完全一致させ、`:391-423` と `:602-632` で stack に応じて v2/v3 を連言している。したがって別順序、A+C、余分な patch、schema/stack 不一致は拒否される。既存 A+B の全経路テストも [`test_plot_dynamic_backoff.py:437`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/orchestrator/tests/test_plot_dynamic_backoff.py:437) にある。

一方 driver は legacy certification/group 定数を [`t2187_adaptive_const_probe.py:49`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/tools/pegasus/probes/t2187_adaptive_const_probe.py:49) に置くだけで、certification row は `:1928`、既存 group receipt は `:2388` で v3 のみを受理する。`test_legacy_v2_performance_artifact_remains_readable` も `:1950-1968` の三項目だけの浅い performance 検査であり、旧 certification/group artifact を覆わない。

旧 A+B 互換を artifact 全体へ主張するなら、stack と schema の組を versioned に検査する reader と v2 certification/group fixture が必要である。互換対象が図入力だけなら、未使用の legacy certification/group 定数を除去し、その境界を明記すべきである。

成果物影響: 旧 A+B の図は再生成できるが、旧 certification 結果の再集約と group receipt の再確認は失敗する。

## PBS の 11/12 field テストは挙動を検査していない

深刻度: must-fix

根拠: [`test_t2187_adaptive_const_probe.py:2282`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/orchestrator/tests/test_t2187_adaptive_const_probe.py:2282) は条件式の文字列が存在することしか見ない。PBS の [`HAS_EXTENDED_CELL=1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:133) や [`NEEDS_DYNAMIC_OUT=1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-counterfactual/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:192) を 0 に壊してもこのテストは緑のままである。M20 の指定された一行戻しは検出するが、12-field 分類の挙動の歯ではない。

対して `_cell_from_document` の key 検査は 5/11-field への余分な key を含む negative case (`test...:1429-1444`) があるため、M17 を殺せる。trace の版連言も parser `:1005-1009,1061-1063` と mixed/mismatch cases `test...:1805-1824` が対応しており恒真ではない。2 層 literal も Python `:259-268` と PBS `:20-21` が `,`→`+` 以外 byte 一致し、テストは `PBS.read_text()` した現物を抽出している (`test...:2263-2279`)。

成果物影響: 12-field の非 trace PBS 投入が早期拒否されず、driver 側で遅れて停止する回帰を見逃す。

## M4・M6 は現状では殺せず、M1 の冗長分類も誤り

深刻度: blocker

根拠: M4 の唯一の想定 test は親実測で既に赤 (`reds.md:32-33`)、M6 も唯一の test が既に赤 (`reds.md:34-35`) である。baseline red の node は変異による赤への遷移を示せないため、現状では M4/M6 を killed と認定できない。場面設定修正後の baseline green が先である。

M1 も [`ruling.md:113`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-backoff-counterfactual/ruling.md:113) の「冗長 gate」は成立しない。patch C には policy 条件が `:265`, `:470`, `:532`, `:540` と複数あり、1-site の対象が特定されていない。たとえば `:265` の policy=2 state guard を `#ifdef` にしても policy=0 の遷移値は変わらず、`test_policy_zero_matches_patch_b_transitions_exactly` は赤にならない。殺すのは静的 `#ifdef` 検査だけである。

M7 と M23 の冗長性はコード上成立する。M2、M3、M5、M7〜M24には指定変異へ差分感応する assertion が確認でき、M25 は意図した survivor である。ただし M20 は前節のとおり指定文字列変異に限定した歯である。

成果物影響: 現在の DW-M01 実測では M4/M6 の kill 判定と M1 の冗長証拠を受理できない。

## 総括

blocker は赤 4 の誤帰属と、baseline red のため殺せない M4/M6。  
literal 2 層、trace v1/v2 連言、図の A+B/A+B+C exact 判定は静的に整合している。  
pin 閉包は seed、37 define、build sink 台帳、新 literal、schema 文書を追記する必要がある。  
pytest は実行しておらず、親の `reds.md` と静的分類結果のみを用いた。