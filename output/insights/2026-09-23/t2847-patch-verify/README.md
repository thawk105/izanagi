# 既存の silo 壊し patch 11 本を現 pin で実走し、検出期待表と突き合わせた ([T-2847] 残り (2) の一部、2026-09-23)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-t2847-patch-verify` (branch `worktree-t2847-patch-verify`)、起点 local main `3886a1fd3` (開始 gate rc 0、2026-09-23 JST)、CCBench submodule `e9e477ca` (`pin.CURRENT_PIN` = `e9e477c`)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/` (brief・Codex の prompt / 出力・起動器・driver の出力 JSON 全文・verifier 出力全文)。
段 1〜6 の全文は `verbatim/` (段 2 plan・段 3 相談 1 本・段 4 裁定・段 5 author・起動器の逐語・段 6 の read-only review 1 本 `s6-review.md` と焦点再レビュー)。段 6 review は NO-GO (must-fix 3・should 2・nit 1、数値の転記 328 項目は全一致) で、全件を採用して本文を直した。焦点再レビュー 1 巡目 `s6-focus-1.md` は NO-GO (前巡 6 件のうち closed 5・partial 1、新しい must-fix 1・should 1) で、これも採用して直した。2 巡目 `s6-focus-2.md` は前巡 3 件がすべて closed、新しい所見は worklog fragment の見積り式の書き方 (must-fix) と記録の参照先 (should) の 2 件で、採用して fragment を直し、親が照合して閉じた。

期待の出所は `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` (以下「設計書」) の §4 (検出期待表) と §5.1 (既存 patch の記録)。V 番号は設計書のもの。

## 1. 依頼と結論

依頼 (ユーザー直接起動の `/dev-wave [T-2847]`): 残り (2) の変異実走のうち、現 pin に文面がそのまま当たる既存の silo 壊し patch 11 本を、既存 driver (設計書 §8 の 2) で build・発火させ、§4 の期待と観測を 4 分類 (期待どおり / 別の層で検出 / 未発生 / その他、§4.6) で突き合わせる。mocc・trigger-misattr・新規 18 変異・コーパス test・容量・si は範囲外。検証は計算ノードの trace-enabled build で、性能値は取らない。

結論:

1. **11 本のうち 10 本を計算ノードで build・実走した** (表は §3)。分類は run ごとに付けた (1 本の patch を複数の条件で走らせたものは条件ごとに 1 行、計 13 run)。13 run のうち **12 run が期待どおり**で、内訳は期待した層で検出 7 run (norw 2・highkey 1・lockskip 1・early-unlock 1・permutation-erase 1・permutation-swap 1)、対象に届かない条件で期待どおり S 1 run (highkey の legacy 条件。検出ではない)、盲点として certified のまま通る 4 run (write-intent の erase・forge・opswap・ptrswap)。**残る 1 run は「別の層で検出」**: lockskip の 4 thread の run で、期待に書いた X と巡回に加えて、期待に書いていない version dup (6,692 件) が出た。未発生・誤検出は 0 run。patch 単位で見ると、10 本とも少なくとも 1 つの条件で期待した層 (または期待した盲点) の観測が得られた。
2. **sort-nonswo は未実走 (「その他」)。** 4 本の driver のどれもこの patch を扱わない。driver の build 経路 (`-DCMAKE_CXX_FLAGS=-D<macro>=1`) と、condition gate が確かめる供給経路 (`-DCCBENCH_SORT_VARIANT=1`) が一致しない。driver の既定の workload (`max_ope=5`) も、記録済みの hang 条件 (write set 16 要素以上) に届かない。走らせるには新しい実行経路の追加が要り、今回の範囲 (既存 driver) を超える。「実行できない」という意味ではない。
3. **write-intent の 4 本は、4 本とも S (certified) かつ `I` 行 0 件だった** (§3.2)。現 pin には write intent の `I` 行を出す emitter が無いので、これは設計書 §4.3 の盲点 (V09〜V12) の期待どおりの観測である。改竄が動的に起きたかは `I` 行では確かめられず、trace から見える範囲は patch ごとに違う。forge の trace には `I` (insert)、opswap の trace には `D` (delete) の書き込み操作が現れた (stock の同じ条件ではどちらも出ない)。erase と forge は取引あたりの書き込み行の平均が stock より約 1 少ない / 多い (7.78・9.78 対 8.78) が、これは平均の差であって、取引ごとの改竄を直接観測したものではない。ptrswap は trace から発火を確かめられない (8.78、操作は U だけ)。
4. **既存 driver は現行の Pegasus では改変なしに走らなかった。** 走らせるため、repo 外の起動器 (Codex author、`verbatim/launcher-source.md`) で次の 3 点を補った。(a) 依存物 (gflags・glog の使い捨て install、masstree・mimalloc・googletest の source、masstree の `config.h`) の供給。(b) compiler (driver 既定の g++-13 は計算ノードに無い。policy が選ぶ g++-11 を渡した)。(c) 出力先 (driver 既定は tracked JSON の上書き。job dir へ逸らした)。s2 は driver の `main()` が旧 pin `dff0f1e` 前提の較正を含むので、壊し patch の関数 `_broken_build_and_verify` だけを現 pin で呼んだ。patch 適用 (`git apply`、fuzz なし、pin と clean の照合)・condition gate・verifier・driver の checks は差し替えていない (§2)。
5. 計算ノードの使用は 4 job・計 668 秒 (job Elapse。約 0.19 node 時間)。

## 2. 何をどう走らせたか

### 2.1 起動器と差し替え

起動器 `launch_patch_verify.py` (sha256 `bc955855…`、逐語は `verbatim/launcher-source.md`) は、driver 名を引数に取り、次の順で動く。

1. 実行前提の確認: Python ≥ 3.10、CMake ≥ 3.21、`s3_mocc_lock_coverage` の policy による compiler の解決と照合、s2 では numactl と `/usr/bin/time`。login node の hostname なら拒否する。
2. 依存物: 既存の `s3_mocc_lock_coverage._prepare_dependencies` と `silo_policy_coverage._prepare_build_dependencies` を呼ぶ。FetchContent の source dir を書いた CMake ファイルを job dir に生成し、環境変数 `CMAKE_TOOLCHAIN_FILE` と `CMAKE_PREFIX_PATH` で渡す (driver の cmake argv は変えない)。
3. 差し替え (driver module の名前だけ。`meta.json` の `replaced_names` に全件を記録):
   - s2: `PIN` ← `pin.CURRENT_PIN`
   - s2・s3・s5: `buildcache.DEFAULT_CC` / `DEFAULT_CXX` ← policy が選んだ compiler
   - s3・s5: `buildcache.build` に compiler (cc・cxx) と job dir 内の cache (`cache_root`) を明示で渡す
   - s3・s5: `source_digest.resolve_evidence` に同じ cxx だけを明示で渡す
   - s3・s5・t152: `repo_output_root` ← job dir
   - s3・s5: `ENV_TAG` ← `pegasus`
   - 全 driver: verifier を起動する `subprocess.run` の結果を受動的に保存する (返す値は元のまま)
4. driver の実行: s3・s5・t152 は driver の `main()`。s2 は driver の preflight (単独性・空き容量・pin と clean の照合・condition gate) の後、`_broken_build_and_verify` を norw と highkey について S2 条件と legacy 条件で呼び、driver の `main()` と同じ式で gate3 の 3 述語を評価した。

t152 は `IZANAGI_T152_CCBENCH_SHA` に現 submodule HEAD の 40 桁 (`e9e477ca1b55348ab4530de0b1cf663ce4555290`) を渡した。driver は `patchharness.checkout` の使い捨て worktree に patch を当てる。

**patch の適用は driver と同じ `patchharness` (`git apply`、fuzz なし) を通した。** 設計書 §5.1 の `git apply --check` のとおり、norw・highkey (offset 67 行)、early-unlock (56 行)、permutation の 2 本 (1 行)、write-intent の 4 本 (−51 行) は offset つきで当たった。fuzz での適用ではない。適用できたことは検証の成功に数えていない。各 build で macro が実際に効いたことは、driver の condition gate の記録 (s2 は norw・highkey とも `admitted: true`) と、§3 の発火の観測で確かめた。

### 2.2 実行条件と job

| job | request | Elapse | 実行ノード | driver の rc | 条件 (driver 既定) |
|---|---|---|---|---|---|
| s3 (lockskip・early-unlock) | `18931.nqsv` | 140 s | bnode032 | 0 (checks 5 件すべて真) | 200 tuple・zipf 0.9・rratio 50・rmw・max_ope 5・1 s。1 thread と 4 thread |
| s5 (permutation-erase・swap) | `18993.nqsv` | 134 s | bnode051 | 0 (checks 8 件すべて真) | 同上の 1 thread |
| t152 (write-intent 4 本) | `18994.nqsv` | 185 s | bnode023 | 1 (変異 4 本の check が偽) | 200 tuple・1 thread・zipf 0.9・rratio 0・rmw=false・max_ope 10・1 s。ほかに stock の abort 条件 (2 thread) と BOMB smoke |
| s2 (norw・highkey) | `18995.nqsv` | 209 s | bnode020 | 0 (gate3 の 3 述語すべて真) | S2 = 100 万 tuple・48 thread・zipf 0.9・rratio 50・rmw=false・max_ope 10・3 s。legacy = 200 tuple・4 thread・zipf 0.9・rratio 50・rmw・max_ope 5・1 s |

生の行は `raw/dispatch-elapse.txt`、各 job の meta (hostname・compiler・差し替え・rc) は `raw/meta-*.json`。compiler は 4 job とも policy が選んだ `x86_64-linux-gnu-g++-11` (11.4.0)。t152 の出力 JSON は `host_role` を `"login-node"` の固定文字列で書くが、実行場所の証拠ではない (起動器の meta の hostname が計算ノードを示す)。

## 3. 観測と期待の突き合わせ

数値は verifier の出力 (`raw/verifier-summary.jsonl`、job dir の `runs/*/verifier/*.json` の全文から jq で抜き出した生 stdout)。「巡回」は `total_cycles` (強連結成分の数)、報告された巡回はすべて G2 に分類された (報告は既定で最大 20 本)。X・P・I は lock 被覆・並べ替え保存・write intent の違反行の数。integrity の他の項目 (orphan read・version dup・txid の重複と欠番・genesis への commit・版の不一致・frame の破れ) は、表に書いたもの以外すべて 0。

### 3.1 検出を期待した 6 本 (9 run)

| V | patch | 条件 | 期待 (設計書 §4) | 観測 | 分類 |
|---|---|---|---|---|---|
| V01 | norw | S2 | N (巡回)。起きなければ S | **N**: 巡回 3,262 (G2)、integrity は全項目 0、取引 1,607,870 | 期待どおり |
| V01 | norw | legacy | 同上 | **N**: 巡回 703 (G2)、integrity は全項目 0、取引 268,070 | 期待どおり |
| V02 | highkey | S2 | N。key ≥ 1000 に競合が届かなければ S | **N**: 巡回 3 (G2)、integrity は全項目 0、取引 1,620,494 | 期待どおり |
| V02 | highkey | legacy (200 tuple) | 対象 key に届かないので S | **S** (certified): 巡回 0、取引 269,179 | 期待どおり (到達しない条件で S) |
| V03 | lockskip | 1 thread | X。1 thread は I | **I**: 巡回 0、X 910,280 (入口の未施錠 455,140・書き込み前の lock 喪失 455,140)、他の違反 0、取引 188,257 | 期待どおり |
| V03 | lockskip | 4 thread | X。巡回が併発すれば N | **N**: 巡回 5,510 (G2)、X 1,213,194 (両 reason 606,597)、**version dup 6,692**、取引 250,939 | **別の層で検出** (期待した X と巡回も出たが、期待に書いていない version dup が非 0。段 4 裁定の定義「期待と違う層の counter が非 0」に当たる) |
| V04 | early-unlock | 1 thread | X (保持破れ) だけ。I | **I**: 巡回 0、X 494,700 (すべて書き込み前の lock 喪失)、他の違反 0、取引 204,423 | 期待どおり |
| V05 | permutation-erase | 1 thread | P (size-changed)。I | **I**: 巡回 0、P 251,087 (すべて size-changed)、他の違反 0、取引 259,129 | 期待どおり |
| V06 | permutation-swap | 1 thread | P (rcdptr-set-changed)。I。二重 lock での abort / 停止もありうる | **I**: 巡回 0、P 756,171 (すべて rcdptr-set-changed)、他の違反 0、**commit した取引 0 件** | 期待どおり (注: commit が 0 件なので、I は P からも空の履歴からも決まる) |

同じ job の stock 対照は、s3 が S (巡回 0・X 0、取引 228,588)、s5 が S (巡回 0・P 0、取引 233,022)。s2 は壊し patch の関数だけを呼んだので、同じ job の stock 対照は無い。highkey の legacy 条件の S が、同じ build で verifier が緑を返しうることの対照を兼ねる。

過去の記録との関係: norw は 2026-06-18 に 50 tuple・4 thread で 1,310 巡回、highkey は 2026-07-06 に S2 条件で G2 5 本 (設計書 §5.1)。今回は pin・機体・verifier の版・条件が違うので、件数を比べない。「巡回が出る」「200 tuple では出ない」という型は同じだった。

### 3.2 盲点として certified のまま通る (4 本)

設計書の期待は「現行 pin では S になりうる (`I` の emitter が無い)」。t152 の 7 run はすべて **S (certified)**、X・P・I・integrity の違反はすべて 0。

| V | patch | 取引 | trace の書き込み行 (verifier の `stats.writes`) | 取引あたり | trace の書き込み操作 | driver の check | 分類 |
|---|---|---|---|---|---|---|---|
| (対照) | stock (1 thread) | 133,991 | 1,176,794 | 8.7826 | U | stock_silent 真 | — |
| V09 | write-intent-erase | 140,714 | 1,094,995 | 7.7817 | U | erase 偽 | 期待どおり (盲点) |
| V10 | write-intent-forge | 129,883 | 1,269,833 | 9.7767 | **I**, U | forge 偽 | 期待どおり (盲点) |
| V11 | write-intent-opswap | **1** | 6 | 6.0 | **D**, U | opswap 偽 | 期待どおり (盲点) |
| V12 | write-intent-ptrswap | 135,589 | 1,190,447 | 8.7798 | U | ptrswap 偽 | 期待どおり (盲点) |

- driver の変異 4 本の check は、いずれも `I` 行 (`write_intent_total > 0`) を要求するので偽になった。driver の rc=1 はこの 4 件だけによる。stock・abort・BOMB・producer・三者照合の check は真 (`t152_write_intent_coverage.json` の `checks`)。
- **rc=1 そのものを盲点の証拠には数えない。** 証拠は、各 run の verdict が S で、`I` 行が 0 件であることの組み合わせである。
- 改竄が動的に起きたかは、`I` 行ではなく trace の書き込みから推測できる範囲だけを書く。erase と forge は取引あたりの書き込み行の平均が stock より約 1 少ない / 多い (平均の差であり、取引ごとの改竄を直接観測したものではない)。forge の trace には YCSB の update だけの workload には無い `I` 操作が、opswap の trace には `D` 操作が出た。ptrswap は取引あたりの書き込み行も操作の種類も stock と区別できず、trace からは発火を確かめられない。
- opswap は 1 取引 (書き込み 6 行) しか commit しなかった。driver の記録は `abort_exercised=true` で abort が起きたことを示すが、その原因と時系列は trace にも driver の記録にも出ない (verifier の `abort_reasons` は空)。「delete への置換の後の取引が commit できなかった」は未検証の仮説である。certified の対象は観測された 1 取引であり、この build が進み続けることの保証ではない。
- 設計書 §5.1 の記録 (2026-07-29、`I` emitter のある別 branch では 4 本とも `I` だけで indeterminate) と今回の S は、emitter が無いという設計上の期待と整合する。ただし pin・compiler・機体も違うので、差を emitter の有無だけに帰属させない。

### 3.3 その他 (1 本)

| V | patch | 分類 | 理由 |
|---|---|---|---|
| V07 | sort-nonswo | その他 (未実走) | §1 の 2。4 driver の patch 一覧 (s2・s3・s5・t152) に無い。`SORT_VARIANT` は condition gate に登録済み (`condition_meaning_gate.py` の `_DEFINE_SPECS`) なので、「gate 未登録」は理由ではない |

### 3.4 4 分類の集計

分類の単位は run (patch × 条件)。集計は run 数で数え、patch 単位の見方を最後の行に添える。

| 分類 | run 数 | 内訳 |
|---|---|---|
| 期待どおり | 12 | 期待した層で検出 7 (V01 の S2・legacy、V02 の S2、V03 の 1 thread、V04、V05、V06)。対象に届かない条件で期待どおり S 1 (V02 の legacy。検出ではない)。盲点として S 4 (V09〜V12) |
| 別の層で検出 | 1 | V03 の 4 thread (期待した X と巡回に加え、期待外の version dup 6,692) |
| 未発生 | 0 | |
| その他 | 0 | 実走した run には無い。stock 対照の異常 (誤検出) も 0 |
| 計 | 13 | |

patch 単位の別記: 11 本のうち 10 本は少なくとも 1 つの条件で期待どおりの観測が得られ、1 本 (V07 sort-nonswo) は未実走で「その他」。

## 4. 限界・言わないこと

- 各行は 1 回の有限の走の観測である。schedule 依存の行 (V01・V02・V03 の 4 thread) で「起きた」ことは言えるが、別の seed・thread 数・長さでの件数は言えない。巡回の件数は pin・機体・verifier の版に依存し、過去の記録とは比べない。
- s2 には同じ job 内の stock 対照が無い。norw の legacy 条件の N と highkey の legacy 条件の S が同じ条件で分かれたことが、build と verifier が一律に赤を返していない傍証である。
- 起動器は driver の外から名前を差し替えて走らせた。差し替えの一覧は `meta.json` の `replaced_names` にあり、patch 適用・condition gate・verifier・checks は差し替えていない。ただし driver を無改変の `main()` で走らせた記録ではない (s2 は `main()` を呼んでいない)。
- write-intent の 4 本で改竄が動的に起きたことは、ptrswap では確かめられず、erase・forge は平均の差、forge・opswap は操作の種類からの推測である (§3.2)。opswap の certified は 1 取引だけの履歴についての判定である。
- raw trace は driver が走の後に消すので残っていない。残っているのは verifier の出力全文 (job dir) と driver の JSON。
- mocc の 4 本・trigger-misattr・新規 18 変異・si は走らせていない (範囲外)。
- 性能値は取っていない。job の Elapse は計算資源の記録で、性能の主張には使わない。
- tracked の CCBench・verifier・`test_verifier.py`・driver は編集していない。repo に入れたのは本書と `raw/`・`verbatim/` の記録だけで、実装面の差分はゼロ。
