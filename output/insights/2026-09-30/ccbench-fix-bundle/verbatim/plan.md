## 前提の確認

brief の実測値と読んだソースに食い違いはない。ただし **P1 の「5 本の修正 tip の F からの diff をそれぞれ `git apply`」は、そのままでは実装できない**。Cicada promotion-uaf tip `16ad3eb8…` は build G と gc の merge `aa8e36f1…` を祖先に含むため、3 本の F 起点差分は重複する。合成 A には、独立した修正内容として **Silo の F→tip、MOCC の F→tip、Cicada 3 本を含む F→promotion-uaf tip** の差分を各 1 回適用する。U1 は A に入れない。この読みなら、A は「F に 5 修正の最終内容を加えた tree」になる。

Cicada の既定値は `INLINE_VERSION_OPT=0`、`INLINE_VERSION_PROMOTION=1`、`SINGLE_EXEC=0`、`WORKER1_INSERT_DELAY_RPHASE=0` で、[Options.cmake](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/external/ccbench/cmake/Options.cmake:31) と [Cicada の CMakeLists.txt](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/external/ccbench/cc/cicada/CMakeLists.txt:3) が対応する。

## 1. 検査器の cicada 登録

[検査器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/tools/check_trace0_preprocess_identity.py:529) の `_compare_file` で、`cc/cicada/` 配下の `.cc` だけ専用文脈を選ぶ。Cicada には `Genome("cicada", {})` を使って `_head_defines` から old/new 各 commit の **Cicada CMake が供給する既定の `-D` 値**を得る。4 macro が両側の供給集合にあり、値が想定する `0` または `1` であることを確認してから、4 値の直積 **2⁴＝16 通り**で上書きする。`INLINE_VERSION_OPT=0` のとき promotion 枝が実質 dead でも組合せを間引かず、OPT と PROMOTION がともに 1 の枝も比較する。既定値 `(0,1,0,0)` を必ず含める。

既存の `_context_overlays()` は空文脈と `GLOBAL_VALUE_DEFINE=1` の 2 通りなので、Cicada `.cc` の期待比較数は **1 genome × 16 値組合せ × 2 overlays＝32 件／file**。その他の `.cc` は現行の **SILO_SPACE 8 genomes × 2 overlays＝16 件／file**を維持する。[`check()` の列挙と件数検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/tools/check_trace0_preprocess_identity.py:1096) は path ごとに期待数を導出し、空列挙と実比較数の不足を拒否する。report にも file ごとの期待数と実数を記す。include 活性の比較も同じ 32 文脈で行う。

`_head_defines(..., source_rel=path)` は、現在の [EVOLVE_BLOCK_SOURCE_PROTOCOLS](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/orchestrator/campaign/source_digest.py:90) に Cicada がないため使えない。Cicada genome の `protocol` から `cc/cicada/CMakeLists.txt` を引く経路を使い、digest 対象 source の登録は増やさない。[`CONTEXT_MACROS` と `_context_overlays()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/orchestrator/campaign/source_digest.py:351) は変更しない。4 macro は TU 注入 macro ではなく CMake が値を供給する macro であり、ここへ追加すると単発文脈列の制限に触れ、digest bytes にも波及する。`_assert_conditional_macros_covered` には各文脈の実効 defines を渡す。4 macro を「名前だけ既知」にしないので、未登録の新 macro は従来どおり停止する。[`_head_defines` と条件 macro 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/orchestrator/campaign/source_digest.py:2116) は変更不要で、digest bytes 不変は `source_digest.py` が無変更であることと既存 digest 回帰検査で示す。

[既存 fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/orchestrator/tests/test_check_trace0_preprocess_identity.py:110) と同じ一時 Git repo に Cicada の Options と CMake を置き、次を追加する。

- Cicada `.cc` の `#if TRACE` 内だけを変えた正例は pass、report の文脈は **32 件**で既定値を含む。
- 既定値では dead な `#if SINGLE_EXEC` 内の TRACE=0 出力だけを変えた負例は「正規化 preprocess 出力が不一致」で拒否する。列挙を既定値 1 文脈に縮める変異を殺す。
- `#if NEW_CICADA_MACRO` の負例は「未知マクロ」で拒否する。4 名を無条件に既知扱いする実装への回帰を防ぐ。
- Cicada 文脈を空または途中までしか積まない変異は、期待 **32** と実数の不一致で赤にする。[既存の 0 件・件数検査テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/orchestrator/tests/test_check_trace0_preprocess_identity.py:638) に沿わせる。名前だけを既知にして値を列挙しない変異は `SINGLE_EXEC` 負例が殺す。

実データの生死確認は計算ノードの使い捨て clone で 2 つの合成 commit を F の子として作る。片方は promotion-uaf tip から **`cc/cicada/transaction.cc` の修正 hunk のみ**を F に適用し、header を含めない。D297 は `--expect-paths cc/cicada/transaction.cc` で実行し、未知 macro ではなく TRACE=0 正規化出力の不一致、rc=1 を要求する。もう片方は F の同 file の既存 `#if TRACE` 内にコメントだけを加え、同じ検査で pass を要求する。clone・commit・照合・両検査を 1 job に置き、**約 5 分**を予約する。これは登録の生死確認であり、合成 A→B′ の判定とは別に保存する。

## 2. 束ねる手順

親が worktree の `external/ccbench` で各 tip の完全 OID、F 祖先関係、作業木の清潔さを再確認し、F から `izanagi-fix-bundle` を作る。`git merge --no-ff` を **Silo `dbac49b6…` → MOCC `f4a5169e…` → Cicada promotion-uaf `16ad3eb8…` → U1 `dcb9a41f…`** の順に行う。Cicada の merge が build G・gc を祖先として取り込むことを確認する。英語の message 骨子は `Merge Silo intra-transaction fix`、`Merge MOCC validation fix`、`Merge Cicada promotion and GC fixes`、`Merge gate witness trace` とし、trailer は親が加える。

各 merge の両親と最終 tip を記録する。最終 tree の F との差分 path は `cc/silo/transaction.cc`、`cc/mocc/transaction.cc`、`cc/cicada/transaction.cc`、`cc/cicada/include/{cicada_op_element,transaction,tuple}.hh`、`include/{trace,ycsb}.hh` の **8 path**に厳密一致させる。Silo の `#line` **365・381・638・661・682・703**を Silo tip と比較し、6 tip（G・gc を含む）が全て最終 tip の祖先であることを `merge-base --is-ancestor` で調べる。F→最終 tip の各 blob を、3 修正の最終差分と U1 差分を独立適用した tree と比較する。衝突解決が発生したら、その内容を個別に審査する。

`/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/` に branch の Git bundle、完全 OID、tree OID、bundle の SHA-256 を置く。land 後は [前例の非 force fetch](/work/SFC/tanab/tmp/silo-intra-txn-fix-line-2026-09-30/wave/fetch-line-to-main.sh:1) と同様、主 checkout の submodule git dir に bundle を verify してから branch を fast-forward または新規作成し、前後の submodule HEAD と superproject gitlink が動かないことを照合する。push は親から人間へ依頼する。

## 3. 合成 A/B′

job dir の使い捨て clone だけで、F の tree に **Silo F→tip、MOCC F→tip、Cicada F→promotion-uaf tip** の patch を `git apply --check`、`git apply` で順に当てる。各 patch の path を固定し、U1 の path は混ぜない。作者・committer・日時を固定して `git commit-tree <A-tree> -p F` で A を作る。[前例の合成 commit 手順](/work/SFC/tanab/tmp/silo-intra-txn-fix-line-2026-09-30/wave/mk-synth2.sh:1) に合わせる。A の各修正対象 blob が対応 tip の blob と一致し、その他は F と一致することを manifest で検査する。

次に `git commit-tree <bundle-tip^{tree}> -p A` で B′ を作り、B′ tree と束ねた tip tree の一致、親子関係を検査する。A→B′ の差分 path は **`cc/silo/transaction.cc include/trace.hh include/ycsb.hh`**に厳密一致させる。A は merge の結果から作らず F と修正 tip の patch から作るため、merge の解決や U1 が修正差分へ紛れた場合に B′との差として露出する。B′の差分はそのまま D297 に渡し、「意図差分」の例外は加えない。

## 4. 計算 job script 群

全 script を job dir に**新しい名前**で作り、各 job は bundle・OID・tree・script hash・入力依存を記録する。投入は [`dispatch_compute.py --task generic`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/tools/pegasus/dispatch_compute.py:4728) に `-- /usr/bin/bash <script> ...` を渡す。[runbook](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/docs/pegasus-runbook.md:615) に従い walltime は `HH:MM:SS` とし、各 job は node-local `$TMPDIR` の clone を使う。

| job | 手順と事前登録 |
| --- | --- |
| CI build | [promotion-uaf の CI image script](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/confirm/run_ci_image.sh:29) を基にする。単一親 OID の照合を、**束ねた tip OID・tree OID・4 merge の親列・F 祖先**の照合へ置換する。`:ci` image、Release、sanitizer OFF、全 protocol を configure・buildし、34 executable、CCBench 本体の warning/error 0、TRACE=0 の `ycsb_*.exe` 7 本の trace 記号なしを要求する。 |
| D297 GCC 11／GCC 12 | **別 job**、各 `--walltime 01:30:00`。合成 bundle の head が B′、`B′^=A`、`A^=F`、`B′^{tree}=bundle-tip^{tree}` と差分 3 path を job 内で照合する。[`run_judge_v3.sh`](/work/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/u1-final/scripts/run_judge_v3.sh:1) のループを 1 compiler／job にし、`--expect-paths cc/silo/transaction.cc include/trace.hh include/ycsb.hh`、`--header-cc`、`--third-party-cache`、`--dependency-prefix`、`--scratch-root` の header 4 引数を渡す。両方 rc=0 と report の一致を要求する。 |
| Silo 正しさ | [起動器 v3](/work/SFC/tanab/tmp/silo-intra-txn-fix-line-2026-09-30/wave/review/scripts/launch_gate_liveness_v3.py:54) の source・親 OID・祖先検査を束ねた tip 用に替え、**patch なし、1 build、2 workload**とする。TRACE=1 `ycsb_silo.exe`、200 record、4 thread、各 1 秒、W-rmw と W-blind。両方 `--require-gate-witness`、commit 件数照合、`serializable` かつ `certified` を事前登録する。 |
| MOCC 正しさ | 束ねた tip の TRACE=1 `ycsb_mocc.exe` を 1 build・1 走。[既存 MOCC cell](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/output/insights/2026-09-29/mocc-validation-fix/README.md:52) の 48 thread・100 万 record・95% read・3 秒を流用し、`--protocol mocc` で判定する。期待は巡回 0、integrity 数値項目 0、C 行＝commit 数。判定不能・不一致は条件 (3) の合格に数えない。1 回は先例の 112 走の統計的代替ではない。 |
| Cicada 正しさ | 束ねた tip の TRACE=1 `ycsb_cicada.exe` を**既定 genome**で 1 build・1 走。[既存 Cicada K cell](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:84) の 200 record・4 thread・1 秒を使い、`--protocol cicada`。期待は巡回 0、integrity 数値項目 0、C 行＝commit 数、READ_WTS_MISMATCH 0。判定器の既知の上限 `indeterminate` は**certified と呼ばず**、事前登録した無巡回の観測として記録する。異常終了・欠測・項目不一致は不合格。 |
| Cicada 登録の生死 | §1 の負例・正例を同じ短い job で実行し、拒否理由と pass report を別々に保存する。 |

正しさは **3 job に分けて並行投入**する。Silo は先例で 1 条件約 117〜130 秒、Cicada の小 cell も build と判定を含めて数分、MOCC は高負荷 cell の判定時間に変動があるため 5 分を目安に上限を置き、超過や判定不能を成功へ読み替えない。

## 5. format

束ねた tip の checkout で、上流と同じ `git ls-files -- cc include common` の `.cc/.hh/.cpp` を対象に `clang-format --dry-run --Werror` を実行する。[既存の CI format 前例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:20) の約 **213 file**を、login の 14.0.0 と CI image `:latest` の 14.0.6 の両方で照合する。対象 file 数と版、rc を記録する。

## 6. 計算の見積り

前例の Elapse を単価とした投入前見積りは次のとおり。

| job | 本数 × 単価 | node 秒 |
| --- | ---: | ---: |
| D297 GCC 11・12 | 2 × 3,300〜3,600 秒 | 6,600〜7,200 |
| CI build・記号検査 | 1 × 約 60 秒 | 60 |
| Silo 正しさ | 1 × 約 130 秒 | 130 |
| MOCC・Cicada 正しさ | 2 × 約 120〜180 秒 | 240〜360 |
| Cicada 登録の生死 | 1 × 約 300 秒 | 300 |
| **合計** | **7 job** | **7,330〜8,050 秒＝約 2.04〜2.24 node 時間** |

D297 の単価は [U1 の GCC 11 実測](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/output/insights/2026-09-30/gen-opt-gate-verifier/README.md:149) に基づく。GCC 12 は同条件の完了実測がないため推定である。**2 node 時間以上**なので、common-5 §4 に従い land 調整役へ目的・7 job の単価・分割・処置と node の割付け・削った計算を 1 通で示し、GO 前には投入しない。md_16 項 4 の「見積りを示して止める」との文言差も相談に明記する。

GCC 11・12 を T-2854 型で 1 job 内並行にしても消費 node 時間が必ず半減するとは見込めず、同時実行のメモリ競合と失敗時の切り分けが増える。依頼に明記された**別 job**を維持する。D297 の header consumer 走査は検査器に shard 機能がなく、1 job 約 1 時間という 5 分目安からの逸脱を記録する。

## 7. 所有の分割

| 段 5 author | 所有 file |
| --- | --- |
| 検査器＋テスト | `tools/check_trace0_preprocess_identity.py`、`orchestrator/tests/test_check_trace0_preprocess_identity.py`。header 規則の回帰確認に `orchestrator/tests/test_check_trace0_header_rule.py` を使うが、原則編集しない。`orchestrator/campaign/source_digest.py` は編集しない。 |
| job script 群 | `/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/` 配下に新設する合成 A/B′、CI build、D297 2 job、正しさ 3 job、Cicada 生死、投入 wrapper の script。既存 wave の script と repo file は編集しない。 |

branch の merge、bundle、最終 OID、一次資料、push 依頼文は親が所有する。

## 未解決・親の裁定が要る点

- **P1 の表現修正:** 「5 tip の F 起点差分を個別適用」ではなく、Cicada 3 tip を含む **F→promotion-uaf tip の集約差分**を 1 回適用する。5 修正の内容と各 tip の祖先性は別々に照合する。
- **計算投入:** 見積りは 2 node 時間を超える。common-5 §4 の調整役 GO が必要で、GO が得られなければ job は投入しない。
- **条件 (3) の限界:** MOCC と Cicada の各 1 走は小さい正しさ再確認であり、MOCC の既存 112 走の再現や Cicada の certified 判定を意味しない。この範囲を一次資料と push 依頼文に明記する。

## 総括

Cicada の 4 macro は検査器内で **16 値組合せ、既存 overlay 込みで 32 比較／`.cc`**として扱い、digest を変えずに D297 の未知 macro 停止を解消する。F から独立に作る合成 A と、束ねた tree の B′を GCC 11・12 の別 job で照合する。計算見積りは約 **2.04〜2.24 node 時間**であり、親は調整役の GO を得てから投入し、format・CI build・3 本の正しさと併せて結果を記録した後、完全 SHA を添えた push 依頼文を置いて止める。