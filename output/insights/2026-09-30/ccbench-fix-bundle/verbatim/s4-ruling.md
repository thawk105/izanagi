# 段 4 裁定 — md_16 CCBench 修正束ね tip (2026-09-30 23 時台 JST、親)

入力: s1-brief.md、plan.md、consult-a.md (A1〜A6)、consult-b.md (B-1〜B-6)。段 4 直前の再走査: 開始後の local main (〜22010defb) に本件へ効く新裁定なし (D2331・D2332 は VHash)。

## 所見の裁定

| ID | 裁定 | 処置 |
|---|---|---|
| plan 前提 | real・採用 | (P1) を訂正: 合成 A = F に Silo F→dbac49b6、MOCC F→f4a5169e、Cicada F→16ad3eb8 (G・gc を含む集約) の 3 差分を 1 回ずつ `git apply`。U1 は A に入れない |
| A1 | real・採用 | 条件 (2) の証拠を 3 層に分けて記録する: (i) 修正 hunk manifest (F→各 tip の path・hunk 範囲・header の有無を merge と独立に固定)、(ii) F→A の blob が各修正 tip の blob と一致・他は F と一致、(iii) A→B′ の D297 pass (merge の解決と U1 が TRACE=0 に何も足さない)。「D297 が Cicada の修正 hunk を認証した」とは書かない |
| A2 | real・採用 (1 走の範囲で) | Cicada の 1 走は promotion 有効 genome (INLINE_VERSION_OPT=1・INLINE_VERSION_PROMOTION=1、他 0) の YCSB R cell (前 wave で修理前土台に巡回 359 が出た cell)。build 修正 (非既定 build) と promotion の修理 3 本の経路を通す。delete・GC の経路 (TPC-C) は通らないことを限界として明記。判定は巡回 0・integrity 数値項目 0・C 行 = commit 数・READ_WTS_MISMATCH 0、上限 indeterminate を certified と呼ばない |
| A3 | real・採用 | テストで report の define 集合が「16 値組合せ × 2 overlay」と厳密一致することを確かめ、4 macro それぞれについて「既定値と反対の値でだけ TRACE=0 が変わる」負例を置く (PROMOTION は OPT=1 の下で) |
| A4 | real・採用 | 一次資料に D297 の選定 context・consumer の範囲を書き、全 TU の同一性を名乗らない |
| A5 | real・採用 | MOCC の 1 走は判定器の観測 (巡回 0・integrity 0・C 行 = commit) に主張を限る。修理経路の発火は主張しない |
| A6・B-2 | real・採用 | 見積りは GCC 11 = 前例実測 (3,300 s)、GCC 12 = 推定、各 walltime 上限を分けて書き、投入前見積りと実績を別に残す |
| B-1 | 一部 real | md_16 項 4 と common-5 §4 第 1 項 (ユーザー本人が確認した委任「2 node 時間を超えそうなら land 調整役へ相談し GO を得て投げる」、同項は「下の記述より優先」と明記) は食い違う。委任はユーザーの直接の裁定で、md_16 項 4 は委任前の規則の写しと読む。ただし独断で上書きせず、調整役への相談文に md_16 項 4 の逐語を載せ、「止めよ」なら投入せず見積りを示して止める。GO なら投入する |
| B-3 | 一部採用 | Cicada 登録は依頼どおり行う。実データの生死確認は別 job にせず Cicada の正しさ job に同居させる (+1 分程度) |
| B-4 | 採用 | 入力照合 (bundle・OID・tree・親子) と clone を 1 つの小さな共通 script にまとめ、各 job は既存実行本体の必要な差分だけを持つ。照合は弱めない |
| B-5 | 採用 | 一次資料に索引表 (束ねた tip・A・B′ の OID、各 report の path と sha256、検査器の commit/sha256、正しさ 3 走の結果 JSON) を置く |
| B-6 | 採用 | login で merge・bundle・format・合成 A/B′ を済ませてから、GO 後に 6 job を同時投入。失敗した job だけやり直す |

## プラン v2

1. **束ね (親、login):** worktree の submodule で F から `izanagi-fix-bundle` を作り、--no-ff merge を Silo dbac49b6 → MOCC f4a5169e → Cicada 16ad3eb8 → U1 dcb9a41f の順。merge commit は親 (コード追加なし、trailer = Claude manager)。検査: 差分 path 8 本、`#line` 6 本、6 tip + G・gc が祖先、F→tip = 3 修正の最終差分 + U1 差分。bundle と OID・tree・sha256 を job dir に置く。
2. **format (親、login):** 束ねた tip に login 14.0.0 と CI image :latest 14.0.6 で `--dry-run --Werror` (213 file 前後)。
3. **段 5 実装子 a (検査器 + テスト、Codex author):** 所有 = `tools/check_trace0_preprocess_identity.py`、`orchestrator/tests/test_check_trace0_preprocess_identity.py`。source_digest.py は編集しない。cc/cicada/ 配下の `.cc` だけ、Cicada の CMake 供給値を old/new 各 commit から得て 4 macro の 16 組合せ × 既存 overlay を列挙、期待数を path ごとに導出、他 path は現行 16 件/file を維持、未登録 macro は停止。テストは A3 のとおり + silo/mocc の件数不変の回帰。
4. **段 5 実装子 b (job script 群、Codex author):** 子の worktree の gitignored scratch (`output/runs/ccbench-fix-bundle/`) に書き、親が job dir へ移す。共通照合 script、合成 A/B′ 作成 (login 用)、CI build、D297 (1 compiler/job、`--expect-paths cc/silo/transaction.cc include/trace.hh include/ycsb.hh` + header 4 引数)、Silo 正しさ (起動器 v3 を束ねた tip 用、patch なし 1 build・2 workload、`--require-gate-witness`)、MOCC 正しさ (1 build・1 走)、Cicada 正しさ (promotion genome・YCSB R・1 走 + 登録の実データ生死確認 2 本)、投入 wrapper。
5. **計算 (GO 後):** 6 job 同時投入。見積り: D297 GCC 11 ≈3,300 s (前例)・GCC 12 ≈3,300〜3,600 s (推定)、CI ≈60 s、Silo ≈130 s、MOCC ≈180〜300 s、Cicada ≈180〜360 s → 7,150〜7,960 s ≈ 1.99〜2.21 node 時間 (walltime 上限の合計はこれより大きい)。
6. **受入:** 検査器の変更で izanagi 側に実装面あり → 変異 matrix と受入全走。

## 事前登録 (結果を見る前)

- D297 A→B′: GCC 11・12 とも rc=0・`result: pass`、diff path = 3 本、header 分岐の planned = executed。rc=1 なら「merge または U1 が TRACE=0 を変えた」として束ねを止め原因を調べる (例外を足さない)。
- CI: configure・build rc=0、実行 file 34、CCBench 本体の warning/error 0、TRACE=0 `ycsb_*.exe` の trace 記号なし 7 本。
- Silo: W-rmw・W-blind とも serializable・certified、D1・D2a・D2b 0、commit 件数一致。
- MOCC: 巡回 0・integrity 数値項目 0・C 行 = commit 数。判定不能・不一致は条件 (3) の不合格。
- Cicada: 上記 A2 の 4 項目。indeterminate は上限として受け入れ、異常終了・欠測は不合格。
- 登録の実データ生死: F → (F + cicada transaction.cc の修正 hunk のみ) は rc=1 で理由が「TRACE=0 正規化 preprocess 出力が不一致」(「未知マクロ」なら登録不成立)。F → (F + cicada transaction.cc の既存 `#if TRACE` 内のコメントのみ) は pass。

## 変異の事前登録 (DW-M01、段 6 で spec 化・単一理由性を実装後に確認)

- M1: cicada の列挙を既定値 1 組合せに縮める → 「既定では dead な枝の差」負例と define 集合厳密一致テストが赤。
- M2: 4 macro を既知集合に名前だけ足し、値を列挙しない → 同上の負例が赤。
- M3: 4 macro のうち 1 つ (WORKER1_INSERT_DELAY_RPHASE) を既定値に固定して 8 組合せにする → その macro の負例と集合一致テストが赤。
- M4: cicada 判定を外し silo 文脈で比べる → cicada 正例が「未知マクロ」で赤。
- M5: 未登録 macro の停止を cicada path で外す → `NEW_CICADA_MACRO` 負例が赤。
- M6: 期待件数を実比較数から導出する (恒真化) → 件数不足を作る注入テストが赤 (実装子が注入経路を用意できなければ登録を外し理由を記録)。

## 禁止 (署名) と通る正例

- 禁止: `check()` が cicada の `.cc` に対し、登録 4 macro の値を列挙せずに既知扱いして pass を返すこと。
- 通る正例: cicada/transaction.cc の既存 `#if TRACE` 枝の中だけにコメント行を足した commit は 32 文脈すべて一致で pass。

## erratum E1 (段 5 後、実装子 b の報告を親が実データで確認、結果を見る前)

F の `cc/cicada/transaction.cc` には `#if TRACE` 枝が 1 つも無い (条件指令は SINGLE_EXEC・INLINE_VERSION_OPT/PROMOTION・ADD_ANALYSIS・BACK_OFF・WORKER1_INSERT_DELAY_RPHASE だけ)。登録の実データ生死確認 (ii) と「通る正例」の「既存 `#if TRACE` 枝の中にコメント」は成立しない。改める: (ii) = F の同 file の末尾に新しい枝 `#if TRACE` / `static int izanagi_trace_probe = 0;` / `#endif` を足した合成 commit。事前登録は変えない (rc=0・pass・cicada 文脈 32 件)。検査器テストの正例 (fixture 上の既存 `#if TRACE`) はそのまま。

## erratum E2 (計算 job 実走後、2026-10-01 00:2x JST、親)

Cicada 正しさ job (40088.nqsv、Elapse 32 s) は build・走行 rc=0 だが `trace files missing` で不合格 (rc=1、事前登録どおりの扱い)。原因: CCBench の Cicada には trace の出力が無く、前例 (promotion-uaf-fix の launch_promo_confirm.py) は izanagi の `patches/instr-cicada-trace.patch` (sha256 f4db2abd…) を当てて TRACE=1 build していた。段 4 の指定の欠落 (親の誤り)。改める: Cicada 正しさ job は束ねた tip の clone に同 patch を `git apply --check` → `git apply` (厳密適用、fuzz なし) で当ててから TRACE=1 build する。login で束ねた tip への `git apply --check` rc=0 を確認済み。判定器・cell・genome・事前登録は変えない。patch の sha256 を result.json に記録する。TPC-C 用 patch は当たらない (本件の 1 走は YCSB なので不要) ことを一次資料に書く。再投入は `submit_one.sh cicada cicada-retry-1` (失敗 `.done` 付き)。GO の範囲内の小幅な取り直し。

## erratum E3 (Cicada 再投入 1 回目の後、2026-10-01 00:3x JST、親)

cicada-retry-1 (40116.nqsv、Elapse 31 s) は build rc≠0 で不合格。本文: `cc/cicada/include/transaction.hh:216: #error "Cicada TRACE cannot observe writes from inline version promotion"`。repo の `patches/instr-cicada-trace.patch` は INLINE_VERSION_OPT=1・PROMOTION=1 と TRACE=1 の組合せを #error で禁じる (promotion の書き込みを trace に出せないため)。前例 (promotion-uaf-fix の launch_promo_confirm.py の ycsb()) は promotion 有効 genome の YCSB に repo の patch ではなく診断 patch `/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/instr-cicada-trace-promotion-diag.patch` (sha256 feaab9b6a98baf4be13cdb93e4cc7478ae5eeaf41aa3830a247dd5bfd8c1b3a3、全追加が `#if TRACE` の内側で promotion の書き込みも trace に出す) だけを当てていた。E2 で前例の patch 列を最後まで読まなかった親の誤り。改める: Cicada 正しさ job は同診断 patch を sha256 照合のうえ厳密適用する (repo の patch は当てない)。束ねた tip への `git apply --check` rc=0 を login で確認済み。genome・cell・判定器・事前登録は変えない。一次資料には「promotion 有効 genome の trace 計装は repo 外の診断 patch (前例と同一 bytes)」と書く。原因は E2 と別 (E2 = trace 無し、E3 = patch の選択違いで build 不能)。

## erratum E4 (2026-10-01 00:4x JST、land 調整役の確認依頼を受けて、投入前)

E3 の診断 patch は repo の計装から `#error` 1 行を消しただけ (記録の仕組みは同一)。`#error` の根拠は D1464 (promotion の内部 write は workload の write と区別して verifier に見せる)。診断 patch は promotion の write を workload の W 行として出すので D1464 を満たさず、その判定は条件 (3) の正しさ合格に数えられない。E3 の適用は取り消し、診断 patch の job は投げない (fix-b4 の成果物は使わない)。promotion 有効 genome の正しさは現行の計装では判定できないと記録する。代案 (1) promotion 無効の OPT=1 genome で repo の計装を当てた 1 走、(2) D1464 準拠の計装・verifier 拡張の起票、を調整役へ相談中。返事まで計算は投げない。前例 (promotion-uaf-fix) の promotion genome の判定も同じ計装の上であることを一次資料に限界として書く。

## erratum E5 (2026-10-01 00:5x JST、調整役 GO「(1)+(2)」の後、投入前)

条件 (3) の Cicada 1 走の genome を promotion 無効の OPT=1 (INLINE_VERSION_OPT=1・INLINE_VERSION_PROMOTION=0・BACK_OFF=0・REUSE_VERSION=0・WRITE_LATEST_ONLY=0・SINGLE_EXEC=0・WORKER1_INSERT_DELAY_RPHASE=0) に替え、repo の `patches/instr-cicada-trace.patch` (sha256 f4db2abd…) を厳密適用する (#error は PROMOTION=1 のときだけ)。cell (YCSB R)・判定器・事前登録 (巡回 0・integrity 数値項目 0・C 行 = commit 数・READ_WTS_MISMATCH 0、上限 indeterminate を certified と呼ばない) は不変。通る経路 = build 修正 G の非既定 build と insert の初期化修正 (修理 4)。通らない経路 = promotion の修理 1・2、gc_records・scan・abort (TPC-C を回さないため) → 一次資料に限界として書く。投入は 1 回だけ (Cicada job の 3 回目、原因を変えた再投入)。通らなければ FAIL-2 で止める。fix-b4 (診断 patch 版) は投入前に停止し、成果物は使わない。
