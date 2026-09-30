# B-post 実装 plan（読取専用の静的検査）

## 1. 遅れて更新してよい条件

**推奨は隣接確認つき B-post。ただし親の (P1)〜(P3) をそのまま実装してはいけない。** hot を「物理列の先頭の写し」から疎な手がかりに変えると、cold 経路を修正する必要がある。

[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:499) の挿入探索は `wts > tx.wts` の間だけ進み、先頭または途中の CAS（:516、:523）で挿入する。[time_stamp.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/include/time_stamp.hh:24) は clock と thread ID から時刻を作る。通常の異なる writer 間では時刻が一意であることを前提に、物理列は wts 降順となる。ただし時刻の wrap や clock 前提まで、この静的検査で証明したわけではない。

seqlock で一貫して写した `wts[i] ≤ trts` の最初の X について、**`i=0` は `latest == X`、`i>0` は `ptr[i−1]->next == X` を acquire load で確認する**。後者では `ptr[i−1].wts > trts` でもある。確認時点の列で X の直前がその版なら、降順性により stock の第1段（[transaction.cc:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:102)）は X で止まり、`later_ver` も一致する。失敗時は `latest` から stock 走査に戻す。確認後の挿入まで排除する主張ではなく、その先は stock 自身の並行実行の意味へ帰着する。

PENDING と ABORTED は hot から除かない。第1段で選んだ版を [transaction.cc:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:108) の第2段へそのまま渡すので、対象の PENDING を待つ。**より新しい PENDING でも `wts > trts` なら stock と同様に第1段で越える**、という区別を保つ。ABORTED を hot から省くと `later_ver` が変わる反例は [s2-plan.md §2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/output/insights/2026-09-29/vhash-hot-block-cicada/verbatim/s2-plan.md) にある。ro は [commit():934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:934) で validation をしないため、読み時の一致が必須。update は一致した `later_ver` から validation (a)（:543–570）が辿る。

**(P1) の cold は反例あり。** hot が `[A(wts=30), C(wts=10)]`、物理列が `[A(30), B(20), C(10)]`、`trts=25` なら、hot の全件が新しいわけではないので隣接確認が B の欠落を検出する。一方、hot が `[A(30)]`、物理列が `[A(30), B(20), C(10)]` で `trts=25` なら、全件 `>trts` として A から stock の `next` を辿れば B に到達する。しかし疎な hot の末尾が列の先頭から連続する保証はなく、例えば hot `[A(40), C(30)]`、列 `[A(40), B(35), C(30), D(20)]`、`trts=37` では C から始めると B を飛ばす。**cold は必ず latest から stock 走査**にする。

GC は [gc_versions():806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:806) と既存 variant 同様、`gc_lock → hot 書き区間 → trim → tail 切断 → 書き区間を閉じる → gcAfterThisVersion` とする。選択 hit の `i>0` では直前版の wts が `trts` より大きいため、`MinRts` より古い GC 切断点にはなれず、その `next` と X は確認中に切り離されない、という寿命論証を使う。`i=0` は `latest` を確認する。REUSE_VERSION と inline 版の再利用（[transaction.hh:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/include/transaction.hh:173)、:217）は trim と切断後なので、上記の保持条件の下で ABA を避ける。ただし `begin()` の ThreadRts 公開順と GC の同時進行に依存する stock 側の寿命前提（[transaction.cc:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:34)、[util.cc:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/util.cc:281)）を独立に証明したとは扱わない。

reader の copy → acquire fence → seq 再読込の順序は既存 variant の形を保ち、その**後**で隣接 pointer を参照する。隣接 load を copy や seq 確認より前へ移さない。read-own-write は [read():153–165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:153) が read set／write set から返すため、通常は hot に入らない。自 tx の版は validation 中の CAS 後、次の begin より前に hot に入れる。新 tuple の INSERT は [tuple.hh:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/include/tuple.hh:95) の初期化を維持する。

**隣接確認なしは不採用。** 上の疎な hot の反例で ro は古い確定版を返して validation なしで commit できる。update も validation (a) で必ず救済されるとは置けない。md_23 の B2 は「commit 0」という結果前予測に反して T1 で 67 件、T2 で 4,331 件 commit した（[README §3.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/output/insights/2026-09-29/vhash-hot-block-cicada/README.md)）。

**未確定点:** stock 自体の時刻・GC 寿命前提の完全な証明、隣接確認直後の競合を含む実機での判定結果。

## 2. inert overlay patch の hunk

新規 `patches/cicada-vhash-hot-block-post.patch` を、pin → variant → post の順で適用し、md_23 variant の bytes を保つ。

| variant 適用後の箇所 | 変更 |
|---|---|
| `cc/cicada/include/tuple.hh` の既存 `vh_insert`（[variant patch:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/cicada-vhash-hot-block-variant.patch:55)） | 物理位置 `p` 引数を廃止し、書き区間内の既存 hot 記述子へ wts 降順で挿入。満杯なら最小 wts を落とす。同一 pointer／wts の重複を防ぎ、GC trim と init は維持。 |
| `transaction.cc` の hot 選択（[variant patch:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/cicada-vhash-hot-block-variant.patch:238)） | seq 確認後、hit に上記の隣接確認を追加。失敗は latest から fallback。cold も latest から fallback。hot 採用数は確認成功時だけ増やす。 |
| `transaction.cc` の validation install（[variant patch:295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/cicada-vhash-hot-block-variant.patch:295)） | `VHashGuard` を `for (;;)` の先頭から外し、stock の `later_ver_` 起点探索と先頭／途中 CAS を復元。CAS 成功後だけ短い guard を取得して hot に挿入し、**guard を閉じてから** `break`。 |
| `transaction.hh` の `VHashStats`（[variant patch:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/cicada-vhash-hot-block-variant.patch:99)）と `transaction.cc` の report（:137–179） | hot 書き区間の待ち・保持サイクルと件数、隣接確認成功・失敗数、読みで hot を使った回数を COUNT に出す。既存 `install_*` は意味を「CAS 後の区間」に更新し、旧 B と混同しない arm 名を JSON に付ける。 |

`goto FINISH_VALIDATION`（[stock:493–495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:493)）と CAS 失敗再試行は guard をまだ持たない。RMW／DELETE／`WRITE_LATEST_ONLY` の先頭 CAS も成功後に同じ更新 helper を呼ぶ。満杯時や挿入対象が最小より古い時でも guard は scope／RAII で閉じる。更新は validation (:463–609) の内部で完了させる。GC hunk（[variant patch:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/cicada-vhash-hot-block-variant.patch:376)）は保持する。

各変更ブロックの後に、pin 側の次行へ戻す無条件 `#line` を置く。pin 単独と pin＋variant＋post について、macro 未定義、同一 compiler argv の `transaction.cc`・`util.cc`・`ycsb_cicada.cc` の前処理出力を行 marker／空行を除いて比較する。`TRACE=0、COUNT=0、ADD_ANALYSIS=0` の perf compile command も照合する。

**未確定点:** overlay の正確な diff context と hunk 行数は作成後の厳密適用で確定する。ここでは build・前処理を実行していない。

## 3. 条件 gate と在庫

**新 macro は足さず、overlay を推奨する。** [condition_meaning_gate.py:684–775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/tests/test_ccbench_spawn_sites.py:684) の実装は、patch の**追加行**にある条件分岐から interface 候補を導く。既存 macro は `global_prior_tokens` に入るため、post overlay に新しい `#if CICADA_VHASH_COUNT`／`#if CICADA_VHASH_K` を追加しても、通常は post を「導入 patch」とは数えない（:753–765）。既存の登録は variant を指し（[condition_meaning_gate.py:277–289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/condition_meaning_gate.py:277)）、branch witness 件数も variant 由来の 9／19／4（:624–636）に留まる。overlay の分岐本体まで gate が証明する、とは主張しない。`_OVERLAY_BASE_DEFINE_INTERFACES`（[test_ccbench_spawn_sites.py:666–674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/tests/test_ccbench_spawn_sites.py:666)）も variant を導入元として明記している。

代案の新 `CICADA_VHASH_POST` macro は登録面を増やす。必要箇所は `condition_meaning_gate.py` の `DEFINE_SPECS`（:277 付近）、owner 条件と witness site 件数（:487、:624 付近）、[test_condition_meaning_gate.py:3664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/tests/test_condition_meaning_gate.py:3664)、必要なら `_OVERLAY_BASE_DEFINE_INTERFACES`（[test_ccbench_spawn_sites.py:669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/tests/test_ccbench_spawn_sites.py:669)）と条件在庫、driver の build macro request となる。既存 macro で overlay に収めればこれらの登録変更は不要。[materializer_admission.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/materializer_admission.py:113)、[test_official_perf_closure.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/tests/test_official_perf_closure.py:47)、[test_p3_build_authority_cli.py:162,185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/tests/test_p3_build_authority_cli.py:162) は既存 driver／build 関数を維持すれば変更不要。新しい subprocess site を作らず、[test_ccbench_spawn_sites.py:82,110–112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/tests/test_ccbench_spawn_sites.py:82) の件数を維持する。

md_23 の導入閉包は `git log --oneline -- patches/cicada-vhash-hot-block-variant.patch` で初回が **`27e492111`** と確認した。その `git log -1 --stat` では variant・壊し2本・driver・test・plot・patch README の7 file が入り、条件 gate 登録は後続単位と commit 本文に記されている。後続 fix は `dd80b7156`。

**未確定点:** 作成する overlay の実際の追加条件が既存 macro だけであることを、patch 完成後に在庫 test で確認する。

## 4. 壊しと B2 機序の診断

既存 B1／B2 は [variant patch:256–259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/cicada-vhash-hot-block-variant.patch:256) の直後の context に hunk を当てる（[B1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/broken-cicada-vhash-stale-hot.patch)、[B2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/broken-cicada-vhash-skip-pending.patch)）。post は同じ選択箇所へ隣接確認を入れるので、**無変更で当たると仮定しない**。厳密 `git apply --check` で確認し、当たらなければ `broken-cicada-vhash-post-stale-hot.patch` と `...post-skip-pending.patch` を新設する。両者の変更 hunk は post の「隣接確認成功後、stock 第2段へ渡す直前」に置き、既存の reached／changed／committed event と witness 帰属を保つ。

新しい遅延 hot 壊しは `broken-cicada-vhash-post-stale-gap.patch` とする。writer 側の CAS 成功後 hot 更新を決定的に一部省き、reader 側の隣接確認を外す。`latest=A(40) → B(35) → C(30)`、hot `[A,C]`、`trts=37` なら C を返す到達経路を作れる。ただし壊し hunk は **cold の stock fallback まで外すか否かを明示**し、上記は hit の `i=1` で成立させる。ro が validation なしで commit すれば判定器の巡回と event 帰属を期待する。T1 は ro 95% で古い snapshot が多いが、隙間と hit が同時に必要なので到達数の事前見込みは「少なくとも1、0なら未到達として未検出」、T2 も同条件で記録する。正例の B-post は T1・T2・T3、K=1・8 の全6走で巡回0、integrity と C 行数を確認する。判定上限は indeterminate。

B2 の計器版は **md_23 の B、K=4** に重ね、T1・T2 を各1走。event ごとに `is_ronly_`、tx wts／rts、選択 PENDING の pointer・wts・read 時と validation 時の status、返した older の pointer・wts、`later_ver_`、validation (a) の開始 pointer と最終 pointer、commit／abort、GC 世代または再利用を識別できる tuple＋版 generation を記録する。trace の C/R/W/E 行は変えない。1走で分ける仮説は次の通り。

- ro で PENDING の wts が rts 以下になる。`begin()` の MinWts 公開時点・writer の公開順を記録して調べる。
- update で PENDING が ABORTED に変わり、validation (a) が同じ older を返して commit する。この場合 B2 の reached／changed／committed は「コミット時点でも不正だった」の証拠にはならない。
- PENDING は COMMITTED になったが、validation (a) がその版を見ない。`later_ver_` が置換された、開始点が違う、あるいは時刻比較（[transaction.cc:545–550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:545)）で越えた経路を識別する。
- B2 の `older=ptr[i+1]` または `next` が GC 切断・REUSE_VERSION・inline 再利用を受け、read 時と validation 時に pointer の指す版が変わる。既存 B1 T2 の orphan read はこの疑いを強めるが、機序は未確定。
- read set に載った版と trace に記録した版が異なる、または ro／update の分類が予測と違う。`ReadElement` の作成（[transaction.cc:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:126)）と commit 分岐を照合する。

**未確定点:** 既存 B1／B2 の post 上での context 一致、壊しの実到達数、B2 の真の機序。

## 5. T-2927 の計器・estimate・図

COUNT を `schema_version=2` にし、`snapshot_lag_cycles` を定義する。`cycles = max(0, wts−rts) >> 8`。bucket は **0、各 `[2^j, 2^(j+1)−1]`（j=0…39）、`2^40+` の42個**とし、上限は `2^40` cycles 以上を overflow bucket にまとめる。個々の cycles の換算は `lag_us = cycles / clocks_per_us`（本走は 2100）。bucket からは µs の範囲だけが得られ、厳密平均は復元できない。必要なら合計 cycles と件数も別 scalar に出す。[time_stamp.hh:24–40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/include/time_stamp.hh:24) と既存18 bucket（[variant patch:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/cicada-vhash-hot-block-variant.patch:146)）が根拠。

[driver:411–456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/vhash_cicada_hot_block.py:411) は v2 の bucket 長・scalar・単位を検証して aggregate する。旧 md_23 raw の COUNT `schema_version=1` は新 aggregate で**読めなくてよい**。旧 raw を再表示する必要があれば旧 commit の driver／図を使う、と一次資料に書く。新 aggregate schema も v2 とし、旧作図を暗黙に受理しない。

[estimate():183–191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/vhash_cicada_hot_block.py:183) の `2 × max(trace job runs)` を `sum(len(plan_trace(j)) × trace_wall for j in (0,1))` に直し、job 別 walltime も別々に出す。新診断2走と壊しを plan_trace に含めてから数える。

[fig-write:128–154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/tools/plotting/plot_vhash_cicada_hot_block.py:128) の下段は、同じ count cell・腕ごとに **待ち cycles／update commit と保持 cycles／update commit** を並べるか積み上げず横並びにする。待ちと保持を凡例・単位で区別し、分母0は欠測表示にする。

**未確定点:** clock 間のずれと boost を含む `wts−rts` は壁時計時間そのものではないため、µs 表示は timestamp clock に基づく換算値と明記する。

## 6. driver と測定量

[driver:30–55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/vhash_cicada_hot_block.py:30) に `arm ∈ {stock, B-k1, B-k8, post-k1, post-k8}` を導入する。build spec（:98–113）は stock／B を pin＋variant、post を pin＋variant＋post とし、trace だけ先頭に `instr-cicada-trace.patch`、壊しを最後に重ねる。perf／count／trace は別 binary。K=0 stock は既存 WL=1 の対照を使う。perf 回転（:116–136）は arm を5水準として round と cell ごとに回す。count（:139–142）は代表4 cell×5腕、trace（:145–155）は T1・T2・T3×正例腕、壊しと B2 診断を追加する。aggregate（:690–795）は `(job, round, cell, arm)` の完備性、binary・patch hash、同 job／node／round の stock 対照、失格腕除外を維持し、B と post の stock 比に加え post/B の対比を出す。旧 `k` 単独キーに依存する fixture を更新する。

md_23 の12 cell と trace T1～T3 を再利用する。基準値は [md_23 README §8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/output/insights/2026-09-29/vhash-hot-block-cicada/README.md)：smoke 308 s、build 247 s、perf 518＋518＋521 s、count 85 s、trace 254＋32 s。**同じ5腕・同じ360 perf run なので基本計 2,483 s（0.69 node 時間）**。追加 binary と trace 壊し・診断を見込んでも概算 3,000 s 前後で、7,200 s 未満。ただしこれは md_23 の Elapse からの外挿であり、post の実走時間を保証しない。smoke の実 Elapse で [estimate():158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/vhash_cicada_hot_block.py:158) を再計算し、7,200 s 以上なら**結果を見る前に**6→4 round、ro 格子縮小、最後に K 水準縮小という梯子を適用する。今回は既に K={1,8} なので最後の段は削れず、なお超えれば投入を止める。perf 3 job を別 node へ同時投入し、他の計測 wave と同居させない。性能値は trace／COUNT のない build のみ。

**未確定点:** smoke 後の実見積り、使用 node と同居状況、post の性能・判定結果。

## 7. テストと波及

[driver test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/tests/test_vhash_cicada_hot_block.py:71) を、5腕の回転・360 perf run・count 20 run・trace／壊しの完備性、arm をまたぐ hash 混同、同時刻の対、失格腕の除外、v2 COUNT の42 bucket と換算式、trace job 走数の**和**、7,200 s の縮小順に更新する。hot の小列モデルには「疎な hot の hit 隣接失敗」「疎な cold は latest fallback」「CAS 失敗後の retry」「満杯時」「GC trim と再利用」を入れる。patch 構造は厳密適用、`#line`、macro 未定義の前処理同値、trace 重ね順で確かめる。[plot test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/tests/test_plot_vhash_hot_block.py:1) の該当 fixture を arm／v2 schema に合わせ、待ち・保持の図と欠測を確認する。

所有外 caller は増やさず、既存 `_build_one` と `run_one` を使う。共有 fixture が旧 `KS`／`k`／schema v1 を参照する箇所だけ更新対象を洗い出す。既存の materializer・spawn site・perf closure 在庫は第3節の通り維持する。段2のこの作業ではテストも build も実行していない。実装後は関連テストと所定 checker、計算ノード上の smoke・判定器・壊しを順に実行する。

**未確定点:** 共有 fixture の全参照と overlay 厳密適用の成否は実装後に確認する。

## 8. 実装単位と依存順

所有 path を重ねない分割とする。

1. **U1・C++ patch:** `patches/cicada-vhash-hot-block-post.patch`、新しい post 用 B1／B2／stale-gap 壊し、md_23 B2 計器 patch、`patches/README.md` の該当節。macro・COUNT v2 JSON 名・event 名をここで固定する。
2. **U2・driver／図:** `orchestrator/campaign/vhash_cicada_hot_block.py`、`orchestrator/tests/test_vhash_cicada_hot_block.py`、`tools/plotting/plot_vhash_cicada_hot_block.py`、`orchestrator/tests/test_plot_vhash_hot_block.py`。U1 の契約に依存する。
3. **統合・実測・記録:** patch 適用と inert／gate、関連 test、smoke、事前見積り、正例 trace と壊し、同時刻 perf／count、aggregate／図、`output/insights/2026-09-30/vhash-hot-block-cicada-v2/README.md` と T-2926／T-2927 の spool fragment。判定器に巡回が出た腕は即失格にする。

**未確定点:** U1 で確定する overlay context と JSON／event 名、smoke 後の計算縮小の要否。

## 総括

推奨設計は **CAS 後に hot を短時間で更新し、hit は隣接確認、cold は latest から stock 走査**する B-post。最大のリスクは、遅延更新で疎になった hot と GC／版再利用の競合による誤選択である。親が段4で裁定すべき択一は、**(P1) の cold 継続を撤回して stock fallback にすること**、および **隣接確認なし案を採らないこと**。この plan は静的検査であり、正しさ・性能の実測結果はまだない。