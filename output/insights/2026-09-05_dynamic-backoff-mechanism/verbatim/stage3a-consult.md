## 判定

このまま段 5 へ進めてはいけません。静的検査で **must-fix 13 件、nit 2 件**です。最初の停止点は、patch B が追加する条件付き `#include` と既存 source identity gate の衝突です。

## Must-fix 1 — patch B は source identity gate を通過できない

**位置:** [stage2-plan.md:106](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:106)、[source_digest.py:1848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/source_digest.py:1848)、[source_digest.py:2075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/source_digest.py:2075)

**指摘:** patch B 案は `<array>`、`<cstdio>`、`<cstdlib>` を追加するが、`assert_includes_match_head()` は dead branch 内も含む全 `#include` 行を HEAD と逐語比較する。したがって `applied(A)` 内で B を適用しても、最初の `source_digest.resolve_evidence()` が必ず停止し、build へ到達しない。

**受理の含意:** 現案を受理すると performance・診断・certify の全 A+B build が identity gate で赤になる。  
**拒否の含意:** include を増やさない実装へ変えるか、include 行と依存 closure を identity に安全に織り込む別変更が必要になる。

**成果物への影響:** certified 選択、性能レポート、診断 JSON は一件も生成できない。

**修正案:** 最小案は既存 include だけで実装できる raw array と明示 flush 構造へ変更すること。identity gate を変更するなら、単なる allowlist 追加ではなく、新 include 行と実際に取り込まれる header closure の hash を source/admission identity に含める。

## Must-fix 2 — `nm` の symbol 0 件は診断コード不在の証明にならない

**位置:** [stage2-plan.md:499](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:499)、同 `:919-923`

**指摘:** inline 化された関数、無名の局所状態、別名へ改名された計装は、命令が残っていても `izanagi_backoff_trace` symbol を生成しない。prefix を `#if` 外で検索する source test も、prefix を持たない分岐・atomic・field を検出しない。

**受理の含意:** symbol 0 を受理条件にすると、trace 命令が perf binary に残った偽陰性を緑にできる。  
**拒否の含意:** `nm` は補助証拠に格下げし、前処理後コードまたは loadable section の比較を主証拠にする必要がある。

**成果物への影響:** trace 混入 binary の性能値が headline report に入る危険がある。

**修正案:** `BACKOFF_TRACE=0` の owner TU 前処理出力に trace block の token・文字列・state が存在しないことを検査し、同一 build 条件で trace block 除去参照との `.text`/`.data` 比較を行う。`nm` は回帰検知として併用する。

## Must-fix 3 — 診断の影響は leader スレッド内に閉じない

**位置:** [stage2-plan.md:374](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:374)、同 `:484-490`、[backoff.hh:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/external/ccbench/include/backoff.hh:94)

**指摘:** writer の実行主体は leader だけだが、書込みで leader の次回試行・次回更新時刻が変わり、その leader が process-global `Backoff_` を更新するため全 worker の待ち時間へ間接的に伝播する。さらに trace static と `Backoff_` の cache-line 分離や address 検査がなく、false sharing も排除されていない。

**受理の含意:** 診断 run の軌跡を perf build の軌跡として受理すると、計装自身が変えた controller trajectory を機序証拠にできる。  
**拒否の含意:** 診断軌跡を「instrumented-system only」と限定し、共有状態の配置と overhead を別に評価する必要がある。

**成果物への影響:** 診断図と勾配符号的中率から perf build の機序を断定できなくなる。

**修正案:** trace state を cache line 分離し、symbol address/map を検査する。レポートには trajectory の非外挿を明記し、trace on/off の aggregate overhead・更新回数差を別 receipt に残す。

## Must-fix 4 — 計数窓の効果と O(threads) polling 負荷を識別できない

**位置:** [stage2-plan.md:438](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:438)、同 `:592-603`、brief (P1)/(P9)

**指摘:** K>0 の腕だけが leader の全試行で全 thread の counter を acquire-load するため、`tuned` 対 `cw` は窓の意味と 48-load scan の費用を同時に変える。sham polling 腕がないので throughput 差を count-based decision の効果へ帰属できない。

理想化すると `K/cap = 10000/0.04096 ≈ 244,141 tx/s` より高ければ K、低ければ cap が先に発火する。しかし実際の終端は次の leader poll なので、poll 遅延を δ、throughput を λ とすると K 側の overshoot は概ね λδ となり、δ 自体が abort・`Backoff_`・thread 数に依存する。

`loadAcquire` は各 counter の可視性を与えるが、48 値の同時 snapshot ではない。uint64 の差分は一窓の aggregate commit が `2^64` 未満なら wrap を含め modulo で正しいが、その前提も契約化されていない。

**受理の含意:** 現行 6 cell を受理すると、`cw` の勝敗は count window と scan overhead の合成効果になる。  
**拒否の含意:** 同じ scan を行いながら従来の時間判定だけを使う sham 腕が必要になる。

**成果物への影響:** thread-axis report で `cw−tuned` を計数窓の効果として報告できない。

**修正案:** `K` を事実上到達不能、cap を tuned の 2560 µs にした `cw-scan-control` 等を追加するか、poll と decision を別 toggle に分離する。job/run 数と事前見積もりも更新する。

## Must-fix 5 — trace schema が K/cap・刻み・上限の作動を観測できない

**位置:** [stage2-plan.md:173](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:173)、同 `:492-497`、brief (P8)

**指摘:** record は TSC、`Backoff_`、gradient sign、次符号 hit しか持たない。`committed_diff`、`time_diff`、count/cap/both の発火理由、実際の刻み、`ceiling_`、ceiling hit/change がなく、どの機構が一度でも働いたか判別できない。

**受理の含意:** 現 schema を受理すると、「cap が支配した」「適応刻みが動いた」「動的上限は効果なし」を同じ JSON から区別できない。  
**拒否の含意:** controller の状態遷移と窓の実測値を trace record に追加する必要がある。

**成果物への影響:** 診断図は `Backoff_` の見た目を示すだけで、P1/P2/P3 の機序レポートにならない。

**修正案:** 少なくとも `window_commits`、`window_cycles/us`、`trigger=count|cap|both`、`step_us`、`ceiling_us`、`ceiling_changed` を記録する。parser は summary と全 event から各値を再計算・整合検査する。

## Must-fix 6 — sub-microsecond 刻みと `uint64_t last_backoff_` が勾配方向を壊す

**位置:** [stage2-plan.md:270](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:270)、同 `:468-474`、brief (P2)

**指摘:** stock の型を on-arm にまで流用すると、例えば `Backoff_` が `0.5→0.25` と減った後も `last_backoff_` は 0 なので、次の `backoff_diff` は `+0.25` となり実際と逆符号になる。`0.25→0` では偽のゼロになり、parity branch と step-halving を発火させる。

**受理の含意:** 現案を受理すると、P2 は「勾配符号への適応」ではなく量子化誤差と parity に適応する controller になる。  
**拒否の含意:** STEP_ADAPT on 時だけ、前回値を lossless な `double` で保持する必要がある。

**成果物への影響:** `cw-as` と `cw-as-dyn` の性能・hit-rate は意図した ×2/÷2 算法の成果として解釈できない。

**修正案:** stock 用 `uint64_t last_backoff_` は off branch に逐語温存し、`#if BACKOFF_STEP_ADAPT || BACKOFF_DYN_CEILING` 内に `double adaptive_last_backoff_` を追加する。遷移列 `0.5→0.25→0` を deterministic test にする。

## Must-fix 7 — 負勾配で動的上限が増える到達可能経路がある

**位置:** [stage2-plan.md:307](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:307)、同 `:320-329`、brief (P3)

**指摘:** step を先に倍増してから `floor=step*4` を計算するため、`ceiling=4, step=1` で連続する負勾配が来ると step=2、floor=8、`ceiling=max(2,8)=8` となる。これは「負勾配なら ceiling を半減」という P3 と逆である。

また現案は 1000 の ceiling を500へ下げた同じ更新で `Backoff_` も500へ clamp し、一歩ではなく約半減の不連続ジャンプを作る。この効果と次窓用 ceiling 更新を区別する裁定がない。

**受理の含意:** 現案を受理すると、負勾配が ceiling 拡大を起こし、adaptive-step と ceiling の振動を作れる。  
**拒否の含意:** `ceiling` の単調条件と `ceiling >= 4*step` の invariant を先に定義し、更新順序を固定する必要がある。

**成果物への影響:** `cw-as-dyn` の結果を「動的上限の効果なし／あり」と分類できない。

**修正案:** 負勾配枝で `new_ceiling <= old_ceiling` を必須にし、step を `old_ceiling/4` 以下へ cap するか、ceiling floor を旧 ceiling 以内に制限する。到達可能な状態列を使い、負勾配で ceiling が増える mutation を単独で赤にする。

## Must-fix 8 — binary SHA 不一致を許した後の inert 判定がない

**位置:** brief (P5)、[stage2-plan.md:976](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:976)、同 `:128-157`

**指摘:** 新しい constexpr・static_assert は feature `#if` の外に残るため、source は A-only と同一ではない。SHA 一致は、同一 compiler/linker/options、再現可能 build、path・timestamp 等の metadata 正規化まで揃った場合にだけ強い直接証拠になる。

SHA が違っても inert を主張できるのは、差が非 loadable metadata に限定され、`.text`、loadable `.rodata/.data`、symbol/layout、hot-path disassembly が同一だと局在化できた場合である。現案の「差を記録して1秒走らせる」だけではその条件を満たさない。

**受理の含意:** SHA 不一致を無条件に受理すると、実行コード差を「source line/debug 情報だろう」と推測して stock 同値を宣言できる。  
**拒否の含意:** binary 差の section 単位の局在化を inert gate に追加する必要がある。

**成果物への影響:** A+B baseline 自体が stock 同値でないまま性能レポートの基準線になり得る。

**修正案:** 同一 source/build path で二 build を作り、SHA 一致なら直接証拠、不一致なら `readelf`/`objdump` による loadable section と対象関数の一致を必須にする。実行 section が違えば inert は拒否する。

## Must-fix 9 — A の既知 hash と patch-stack identity が実行時に固定されない

**位置:** brief 不変条件、[stage2-plan.md:541](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:541)、[t2187_adaptive_const_probe.py:1718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:1718)

**指摘:** 現 probe は A の現在 bytes を hash して記録するだけで、既知値 `9b2153...f54b` と比較しない。A と B が一緒に変更されれば dependency test、apply test、receipt が自己整合的に緑のままになる。

plan `:553` の「旧 `patch_sha256` の意味を A+B stack digest へ変更」は既存 T-2189 field の意味を破壊する。また「canonical JSON bytes」の serialization、domain separator、key order、separator、newline が未定義である。

`resolve_evidence()` 自体は B 適用後に呼ばれるため、include 問題を除けば A+B の source bytes/full diff を読み、buildcache も出口で再照合する。この部分の順序は正しい。

**受理の含意:** 現案を受理すると、同じ field 名・同じ arm 名で別 A/B bytes の結果を認証できる。  
**拒否の含意:** A の既知 SHA、B の凍結 SHA、ordered stack digest を別々に固定する必要がある。

**成果物への影響:** certification receipt と性能 provenance が、実際に評価した patch stack を一意に識別できない。

**修正案:** `patch_sha256` は永久に A の hash という旧意味を維持し、`dynamic_patch_sha256`、`patch_stack`、domain-separated `patch_stack_sha256` を追加する。実行前に A の literal expected SHA と、凍結後の B/stack SHA を fail-closed で照合する。

## Must-fix 10 — certify の schema と claim が cell identity に閉じていない

**位置:** [t2187_adaptive_const_probe.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:44)、同 `:86-91`、同 `:1403-1410`、[stage2-plan.md:733](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:733)

**指摘:** 現行 claim は「調整済み定数」専用の単一 constant である。plan は cell-specific claim と書くが、exact mapping、row/group 再照合、claim mutation test を定義していない。

さらに既存 v1 schema のまま patch stack と6 fieldを必須化すると、凍結済み T-2189 v1 receipt が同じ schema 名の現 validatorで拒否される。optional にすれば新 A+B identity の欠落を受理する。

既存 `tuned:1:1:1000:2560` は parser/PBS の受理値と `Genome.canonical()` を維持でき、連言10項、陽性対照、24 request、非 lenient、exact trace pathにも緩和案は見当たらない。ただし A+B source/admission/artifact bytes まで旧走行と同一にはならない。

**受理の含意:** schema/claim を現状のまま受理すると、dynamic group が tuned の文章を発行するか、旧 v1 receipt の意味を事後変更する。  
**拒否の含意:** A+B 用 v2 schemaと cell→claim の全単射が必要になる。

**成果物への影響:** group receipt の certified arm と公開文章が食い違い、既存 T-2189 証拠の再検証互換性も失われる。

**修正案:** performance/certification/group を v2 に上げ、v1 tuned readerを凍結互換として残す。`CERT_CLAIMS = {CERT_TUNED_CELL: old_exact_claim, CERT_DYNAMIC_CELL: dynamic_exact_claim}` を定義し、個別 row、group、published group の全段で exact 比較する。

## Must-fix 11 — 例示 qsub は凍結済み結果 directory へ書く

**位置:** [t2187_adaptive_const_probe.pbs:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:14)、[stage2-plan.md:724](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:724)、brief 不変条件

**指摘:** PBS の既定先は `izanagi-job-evidence/t2187-adaptive-3const/results` のままで、plan の診断 qsub 例は `IZANAGI_T2187_OUT_DIR` を渡していない。これは「凍結 artifact に書かない」「本 wave は dynamic-backoff/」に反する。

**受理の含意:** 例示どおり投入すると既存 T-2187 evidence namespace に新 JSON を作る。  
**拒否の含意:** dynamic/trace/certify の出力先を PBS と driver の両方で exact に束縛する必要がある。

**成果物への影響:** 凍結 evidence の directory identity と新 wave の report input 集合が混ざる。

**修正案:** legacy 5-field performance だけ旧 default を許し、extended・`--backoff-trace`・新 dynamic certify では `IZANAGI_T2187_OUT_DIR` を必須化して canonical dynamic-backoff prefix を検査する。全 qsub 例にも明示する。

## Must-fix 12 — `DefineSpec.inert_values` は結合条件を表現できない

**位置:** [stage2-plan.md:779](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:779)、[condition_meaning_gate.py:904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/condition_meaning_gate.py:904)、[screening_driver.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/screening_driver.py:98)

**指摘:** 新値の stock 同値性は unary ではない。`COUNT_CAP_US=0` は K>0 なら `BACKOFF_UPDATE_US` を実際の cap として使い、STEP_MIN/MAX=100000 は STEP_ADAPT=1 なら刻みを100に固定するか初期刻み条件を失敗させる。

ところが `_is_inert_value()` は requested/default の一致または `inert_values` membershipだけで stock comparison を選ぶ。`_CONDITION_DEFAULTS` も genome 内の他 toggle を見ずに default equality を stock と扱うため、結合機構に誤った stock-inert gate を発行する。

**受理の含意:** plan の表を受理すると、機能中の cap/bounds が stock-inert と分類される。  
**拒否の含意:** activation dependency を registry と request derivation に導入する必要がある。

**成果物への影響:** condition-gate receipt と将来の screening admission が、動作中 parameter を stock と誤記録する。

**修正案:** `COUNT_WINDOW=0`、`STEP_ADAPT=0`、`DYN_CEILING=0`、`TRACE=0` の off switch と、その配下 parameter を区別する。`stock_comparison` は一 macro の default equality ではなく、関連 toggle を含む全機構の既定状態から導出する。

## Must-fix 13 — 受入閉包と変異検査に恒真・多重理由が残る

**位置:** [stage2-plan.md:894](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:894)、[test_screening_driver.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_screening_driver.py:244)、[test_ccbench_spawn_sites.py:2636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_ccbench_spawn_sites.py:2636)

**指摘:** 閉包は次のように非対称である。

| 漏れ・誤り | 現計画での結果 |
|---|---|
| patch B の define を `DefineSpec` へ未登録 | patch inventory が赤 |
| `DefineSpec` と `_CONDITION_DEFAULTS` の key 集合不一致 | screening test が赤 |
| supply-domain test 一覧未更新 | exact set test が赤 |
| deferred sink の行番号未更新 | live-sink exact test が赤 |
| `patches/README.md` 追記漏れ | 緑のまま |
| `_CONDITION_DEFAULTS` の値が誤り | key集合 testは緑のまま |
| deferred reason が旧「tuned only/A only」のまま | nonempty なので緑のまま |
| current-wave owner へ更新せず旧 t2187/t2189 のまま | planどおり goldenも据置なら緑 |
| `ledger.json` に entryを足さない | 正しい。逆に追加すると rung1 exact-one contract が赤 |

変異帰属にも問題がある。tuned/dynamic row 混在は cell identity、genome、genome SHA、source bytesを同時に変えるため単一理由にならず、`test_screening_condition_requests_cover_exact_define_specs` は期待値を同じ registryから生成するため誤った値を固定できない。unchanged hooks test は本変更の歯ではなく、`nm` test も前述の偽陰性を持つ。

さらに OR→AND、×2↔÷2、ceiling 更新削除、負勾配での ceiling 増大を直接赤にする production transition test がない。parser・patch適用・性能走行だけでは controller の意味を固定しない。

**受理の含意:** 現テスト計画を受理すると、acceptance 全緑でも registry の意味、controller 遷移、deferred attribution が壊れた状態を許す。  
**拒否の含意:** 各層の直接 unit test と end-to-end defense-in-depth testを分け、mutation ごとの唯一の期待 reason を固定する必要がある。

**成果物への影響:** DW-M01 変異台帳の「歯がある」という主張と、登録簿の完全性を信用できない。

**修正案:** 新7 defineの完全な `DefineSpec`/default mapを独立 literalで検査し、deferred owner/reasonも exact に固定する。production が使う純粋 transition helperを作り、K/cap OR、step更新、clamp、ceiling invariantを合成入力で検査する。

## 確認できた境界

- patch案の field、関数、ring、呼出しは数値 `#if BACKOFF_TRACE` 内にあり、`BACKOFF_TRACE=0` で予定された診断 runtime state は前処理上消える。外にある CMake optionと`static_assert`は runtime observer effectではない。
- full dynamic の performance/certify buildでは STEP_ADAPT、DYN_CEILING は compile-time on、`cw`/`cw-as` では該当枝が compile-time offになる。したがって P4 の「部分集合」は runtime 分岐という意味ではない。
- certify の二値化案は、一回の request に一 cellだけ、group 内cell identity一値、24 workload/slot、陽性対照、非 lenient、exact trace pathを維持する限り、連言10項を緩めない。
- `revert_worktree()` の `git checkout -- .` は tracked な A+B の両変更を戻す。B path=A pathかつHEADに存在する検査も、新規 file残骸を避ける条件として妥当である。
- include問題を解消すれば、B適用後の `resolve_evidence()` と buildcache の出口再照合はA+B treeを読む。ordered patch stackはそれとは別の成果物 identityとして必要である。

## Nit 1 — 「全機構 on を認証」の語は branch 被覆を含まない

**位置:** brief (P4)、[stage2-plan.md:733](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:733)

**指摘:** abort>0 は backoff 経路の行使を示すが、K発火、step doubling、ceiling hit/change の全行使は示さない。証明できるのは「全 toggle on の binaryによる観測24走行がserializable」までである。

**受理の含意:** 「全機構を認証」とだけ書くと、全遷移を検査したように読める。  
**拒否の含意:** build configuration認証とbranch-coverage診断を別表現にする。

**成果物への影響:** certified 選択の脚注が必要になる。

**修正案:** 「full-on build の観測24走行を認証、機構各枝の被覆は未認証」と固定する。

## Nit 2 — P6 の 3.6 秒/run は brief 内で自己矛盾している

**位置:** brief (P6)、[stage2-plan.md:1001](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/codex/dynamic-backoff-mechanism/stage2-plan.md:1001)

**指摘:** 8.5分/120 run は4.25秒/runであり、3.6秒/runではない。planの約15.2分/jobという再計算が正しい。

**受理の含意:** briefの3.6秒を受理すると run 部分を約15%過小評価する。  
**拒否の含意:** preregと投入表を4.25秒基準へ統一する。

**成果物への影響:** preregistration の時間見積もりだけが変わり、40分walltimeの可否は変わらない。

**修正案:** brief P6 をplanの計算へ合わせる。

## 総括

- **must-fix: 13件**
- **nit: 2件**
- **反証した (P):** P2、P3、P5、P6。P7は結論ではなく、列挙されたconsumerが `patches/ledger.json` を読むという前提を反証した。
- **反証ではないが識別不能のまま:** P1、P8、P9。特に sham polling腕と、実窓・trigger・step・ceilingを持つtraceが必要。
- **維持可能:** P4のcompile-time部分集合、連言10項・陽性対照・24 request・非lenient・exact trace-dirの正しさ境界。

pytest/buildは依頼どおり実行せず、read-onlyの静的検査だけを行った。