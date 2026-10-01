# Cicada の正しさの記録を中間案 M の水準へ上げた — 読んだ版の回収・公開の記録漏れ・読みの登録漏れを TRACE ビルドで全 tx 照合し、stock・最良設定・E-max で違反 0、人為的に入れた誤り 3 種で発火 (VHash 論文 md_33、2026-09-30)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-cicada-certified-m` (branch `worktree-dev-wave-cicada-certified-m`)、起点 local main `213d411c6` (開始 gate fresh rc 0、2026-09-30 14:4x JST)、CCBench submodule = pin C `68106660` (動かしていない)。
台帳 item = worklog「次の一手」[T-2874] (記録の水準は中間案 M に決定、D2305 項 4)。依頼は `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_33.txt` (逐語は `verbatim/request-md_33.txt`)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/` (段 1〜6 の全文、Codex の prompt と報告、repo 外の起動器 `launcher/launch_cicada_m.py` とその版、変異 patch `mutations/`、計算ノードの raw と result `runs/`)。段 1〜6 の主要な全文は `verbatim/` にも置いた (依頼 2 本、段 1 brief (O13 の追補を含む)、段 2 plan v2、段 3 相談 2 本、段 4 裁定 v2、段 6 レビュー 2 本・焦点再レビュー 3 巡・裁定 1〜9)。無効化した段 2〜4 の旧版は job dir の `invalidated-v1/` にある (§10)。
逐語の正規化 6 件 (`git diff --check` 抵触のため、Markdown 改行用の行末の半角空白だけを除去、可視文字不変。原文は job dir の同名元 file、復元はその file を写す。原文 sha256・byte 数 → 正規化後):
`verbatim/s3-consult-a.md` (元 `consult2-a.md`、21 行) `7b21ab4d…`・5,740 → `b3176467…`・5,698。`verbatim/s3-consult-b.md` (元 `consult2-b.md`、18 行) `6937f7ec…`・6,401 → `7625fbc7…`・6,365。
`verbatim/review-a.md` (19 行) `e923ccf5…`・5,657 → `63b68171…`・5,619。`verbatim/review-b.md` (25 行) `3d09bb1a…`・5,427 → `bbda4f5f…`・5,377。
`verbatim/focus1.md` (2 行) `d9f7281f…`・7,964 → `a8c89616…`・7,960。`verbatim/focus3.md` (2 行) `3ed4c88a…`・8,920 → `05e1b4b6…`・8,916。完全な sha256 は job dir の `verbatim-normalization.txt`。

**この資料は正しさの検査の記録であり、性能値を含まない。** TRACE=1 の build の throughput は測っていない (絶対規律 1)。

## 1. 依頼と結論

依頼 (md_33): Cicada の判定器は巡回の無い履歴を indeterminate としか言えず、VHash の芯 (前進を GC の回収境界へ反映する U0) の典型的な失敗 = 既読版の早すぎる回収・再利用は、今の検査の盲点にある (`../../2026-09-29/cicada-certified-evidence-design/README.md` §1 項 3)。D2305 項 4 で採った中間案 M を実装し、「TRACE ビルドで、生存中の tx が読んだ版が回収・再利用されていないこと、公開した全版が記録されていることを全 tx で照合し、違反 0」と書ける状態にする。

結論:

1. **M を実装した。** 既存の out-of-tree 計装 `patches/instr-cicada-trace.patch` (変えていない) の上に重ねる `patches/instr-cicada-trace-m.patch` が、`#if TRACE` の内側だけに 3 つの照合を足す (§3): **B (読み束縛)** = 読んだ版 object が、読み手の tx が終わるまで回収 (pool 積み・inline slot の返却) も再利用もされていないこと、**U (公開)** = `cpv()` が公開した版、validation で設置した版、W 行の三者が一致し、公開した版の wts が C 行の版と一致すること、**read 側 API** = `read()` の呼び出し単位で、外部 read は read set にちょうど 1 要素を登録し、返した body がその要素の版の body であること。違反は stderr に 1 件 1 行、終了時に集計 1 行を出し、trace の行と判定器は変えていない。
2. **段 1 の判断: 最良設定 (`INLINE_VERSION_OPT=1`、promotion 0) を M の範囲に含めた** (§2)。比較相手の観測最良設定と構成 E / E-max の実測がすべてこの設定の上にあり、範囲外にするとそれらの性能値を D2305 項 4 (2) の地位へ上げられないため。inline slot の返却・再取得も照合の事象に含め、実走で inline 版の回収・再利用の事象が数十万件起き、照合が inline 経路でも働くことを確かめた。
3. **負例 (通るべき): stock の既定設定と最良設定、E-max の全 18 run (異なる条件は 16) で、巡回 0・integrity の数値項目 0・C 行 = commit 数・M の違反 0** (§5)。照合の母集団の等式と照合件数 > 0 も全 run で成立した。
4. **正例 (落ちるべき): 人為的に入れた誤り 3 種を M が検出し、壊した tx に帰属した** (§4)。既読版の早すぎる回収 (D2295 で却下した P5 型: tx の途中で読み取り下限を最新へ上げる) は既定設定で 3,273 件、最良設定で 3,715 件の B 違反 (最良設定では inline 版の回収・再利用による 62 件を含む)、公開の記録漏れは 1 件の U 違反、読みの登録漏れは 1 件の API 違反。**3 本とも判定器の結果は巡回 0 の indeterminate で、判定器だけでは見えなかった** (§4)。
5. **TRACE=0 の命令列は pin と一致した** (§6)。4 target (ycsb・tpcc・bomb・sbomb) × 2 genome の pin C 対 pin C + instr + M、と E-max stack の M 無し対 M 有りの計 10 組。
6. **論文に書ける文と書けない文を §7 の表にまとめた。** 「Cicada 実装が一般に serializable を保つ」「certified」とは書かない。書けるのは「検査した有限の run について、観測した読みの 1SR と、M の照合の違反 0」まで。

## 2. 段 1 の判断 — inline 版を M に含める

md_24 は M の対象を `INLINE_VERSION_OPT=0` に限っていた (`../../2026-09-29/cicada-certified-evidence-design/README.md` §3.5)。ところが比較相手 A の観測最良設定 (md_11) と、構成 C・E・B の実測 (md_14・md_21・md_23) は `INLINE_VERSION_OPT=1` の上にある (論文ストーリー 3 版目 §4.5)。範囲外と明記するだけにすると、M を実装しても最良設定の上の性能値を「M の照合を満たした」と書けない。

inline 版の回収・再利用・返却は、非 inline 版と同じ 3 関数 (`include/transaction.hh` の `gcAfterThisVersion`・`newVersionGeneration`・`writeSetClean`) の inline 分岐で起きる。`inline_ver_` は tuple の中にあり走行中に解放されないので、同じ世代番号の事象を置けば覆える (§3.1)。初期化は `Tuple::init(body, param)` (初期ロード、範囲内) と `Tuple::init(ver, initial_wts)` (INSERT 経路、範囲外) の 2 つがある。promotion = 1 との組は既存の `#error` のまま (D1464)。

実走で確かめたこと (§5 の表): 最良設定の run では `ev_gc_inline` + `ev_reuse_inline` (inline slot の返却と再取得の事象数) が 5,648〜2,681,878 件、既定設定の run では 0。最良設定の壊し B では inline 版の回収・再利用による B 違反が 62 件 (返却 2・再取得 60) 出た。

## 3. 実装

### 3.1 B — 読み束縛

- `Version` に TRACE 専用の単調な世代 `trace_gen_`、最後の事象の種類、所属 tuple を置く。版を再利用可能にする瞬間と再利用する瞬間 (GC の pool 積み・inline 返却、pool からの再取得・inline 権の取得、abort した未設置版の pool 返却・inline 返却) に、seqlock と同じ 2 段 (開始で奇数、状態を変えて、終了で偶数) で世代を進める。
- 読み手は `read_internal` の `read_set_.emplace_back` の直前に「世代 → wts・status・所属 → acquire fence → 世代」の snapshot を取り、世代が奇数、前後で不一致、所属 tuple が違う、status が committed でない、wts が読み手の基準時刻より大きい、のいずれかなら `B_WINDOW`。snapshot の世代を read set の要素に保存する。
- tx の終わり (書く tx は `writePhase` の emit の前、read-only は `commit` の早期 return の前、abort は read set を消す前) に、各要素の版の世代が保存値と一致することを照合し、不一致は `B_RETIRED` (最後の事象の種類を添える)。照合位置は、その経路で Cicada 本体が read set の版 pointer を最後に使った後。
- **登録前の窓の扱い (段 4 裁定の論拠):** 版 pointer を得てから snapshot を取るまでの間に、同じ object が再利用される窓は残る。snapshot の検査は、その窓の中で object が別の tuple・別の状態・読み手より新しい版に化けた場合を検出する。検出できないのは「同じ tuple の、確定済みで読み手の時刻以下の別の版として一貫した snapshot が取れた」場合だけで、そのとき R 行はその版の wts を出し、body の消費は登録の後 (`read()` は登録の後に body pointer を返し、YCSB は commit の前に消費する) なので、記録と実行は一致する。Cicada の版選択規則への適合は M の主張の外である (md_24 §3.1)。

### 3.2 U — 公開の照合

validation の設置 CAS の成功直後に設置記録、`cpv()` の各 store の直前に status が pending であること (`U_NOT_PENDING`)、store の後に status を読み直して期待値 (`U_STORE`) を確かめてから公開記録を積む。`traceCommit` の W 行の走査の前に、設置集合 = 公開集合 (版 pointer、`U_INSTALLED_UNPUBLISHED`・`U_PUBLISHED_UNINSTALLED`)、公開集合 = W 行の集合 (key・op の多重集合、`U_MISSING_W`・`U_EXTRA_W`)、公開時の版の wts = C 行の版 (`U_WTS`) を照合する。status を committed / deleted にする store は `cpv()` と `gcpv()` だけで、`group_commit=0` では `cpv()` だけが使われる。`group_commit != 0` は TRACE の実行時に異常終了させる。

**主張の範囲:** 「対象経路で `cpv()` が公開した版と、設置した版と、W 行の照合」まで。`cpv()` に届く前に write set から要素が消える失敗 (write API の意図の保存) は範囲外。

### 3.3 read 側 API の照合

公開 `read()` の呼び出しを母集団とし、入口で read set の大きさを控える。外部 read (tree を引いて `read_internal` が版を返す分岐) が `OK` で戻るときは、その呼び出しで read set に新しい要素がちょうど 1 つ増え、storage・key が一致し、返した body pointer がその要素の版の body であること (`API_EXTERNAL`)。read set の再読 (`API_REREAD`)・自分の書き込みの読み (`API_OWN_WRITE`) は新しい登録 0 と、返した pointer が既存要素の body であること。tx の終わりに、どの外部 read にも対応しない read set 要素 (過剰な登録) が 0 であること (`API_EXTRA_REGISTER`)。`WARN_NOT_FOUND` と forwarding の `ERROR_PREEMPTIVE_ABORT` などは別に数える。

### 3.4 出力と母集団の独立計数

違反行: `CICADA_M_VIOLATION kind=<13 種> thid tx_seq tx_wts outcome key ver gen_seen gen_now wts_seen event` (全件)。集計行: `CICADA_M_SUMMARY schema=1 …` (ちょうど 1 行、既存の `cicada_trace::report()` の中から)。集計には照合件数と、照合とは別の地点で数える母集団 (tx の begin・commit・abort、`read()` の呼び出し、read set 要素の登録、insert・delete・scan・`reconnoiter_end` の呼び出し) を並べる。

repo 外の起動器 (`launch_cicada_m.py`) の合否 (stock・E-max): 正常終了 ∧ 巡回 0 ∧ integrity の数値項目 0 (`integrity.clean` は Cicada では構造上偽なので使わない) ∧ C 行 = stdout の commit 数 ∧ 既存の `READ_WTS_MISMATCH` 0 ∧ M の集計行ちょうど 1 行 ∧ 違反行 0 ∧ 集計の違反 0 ∧ 次の等式 ∧ 照合件数 > 0 ∧ insert / delete / scan 0 ∧ `read_not_found` 0。

| 等式 | 独立性 |
|---|---|
| `tx_commit_write + tx_commit_ronly` = stdout の commit 数 = trace の C 行数 | 独立 (3 つの出所が別) |
| `0 ≤ tx_begin − (commit + abort) ≤ thread 数` | 独立 (begin と終端を別に数える) |
| `b_registered = b_elements_checked` | 独立 (登録の地点と終了照合の loop で別に数える、要素単位) |
| `api_checked + read_not_found + read_other_status = read_calls` | 独立 (呼び出しの入口と、比較を実行した地点で数える) |
| `tx_reconnoiter = 0` | 範囲の固定 |
| `b_end_checked_commit + b_end_checked_ronly + b_end_checked_abort = tx_end_reads_nonempty` | **独立でない** (今の配置では同じ条件の直後で数えるので実質恒真。焦点再レビュー 3 巡目 N4) |

### 3.5 置き場と重ね方

- `patches/instr-cicada-trace-m.patch` は `pin C → instr` の source に fuzz 0・offset 0 で当たる。E-max stack (`pin C → instr → cicada-forwarding-variant → -gc → -target → M`) では forwarding の 3 patch が同じ file を動かすので、同じ bytes が `transaction.cc` の 18 hunk で +660〜+940 行の offset (文脈は完全一致、fuzz 0) で当たる。起動器は stock では offset を拒否し、E-max では hunk ごとの offset を result に記録する。18 hunk の当たった関数が両 stack で一致することを Codex が照合した (途中の版では insert / delete の hunk が E-max で `update` に当たっており、固有の文脈へ移して直した)。
- 新しい `#if` の条件語は `TRACE` だけ (`orchestrator/tests/test_ccbench_spawn_sites.py` の定義一覧に影響しない)。patch の中に `IZANAGI_` の語は無い。
- 起動器・変異 patch・計測の raw は repo 外の job dir にある (md_3 以来の Cicada trace 起動器と同じ扱い)。
- 規模: M patch の追加行は 470 行 (最終版 2aff9ff54、`grep -c '^+[^+]'`)、起動器は 1,128 行 (v7)。md_24 の見積り (計装 +150〜250 行、起動器 +50〜100 行) を大きく超えた。主因は 13 種の違反と全集計 key、U の三者照合、呼び出し単位の API 照合、母集団の独立計数、起動器の TRACE=0 同一性・帰属・再分類。

## 4. 正例 — 誤りを入れた Cicada で M の照合が発火し、壊した tx に帰属する

壊し 3 本 (`patches/broken-cicada-m-*.patch`、無マクロの無条件 patch、`pin C → instr → M → 壊し` の順に厳密適用、`cc/cicada/transaction.cc` の 1 site)。事象は stderr の `CICADA_BREAK_EVENT` に全件、終了時に `CICADA_BREAK_FIRED` を 1 行出す。帰属と分類は repo 外の起動器が行い、同じ cell の stock 対照の合格を条件にする。値は最終版 (patch 2aff9ff54、SMOKE 5 回目 `runs/smoke-5/`)。

| 壊し | 壊し方 | cell | 発火診断 | M の違反 | 帰属 | 判定器 |
|---|---|---|---|---|---|---|
| `m-early-reclaim` (B、P5 型) | read-only tx を 1/64 で選び、commit の前に 5 ms 待つ間、50 µs ごとに自 thread の `ThreadRtsArray` を `max(現在値, MinWts−1)` へ上げ直し `GCFlag` を立て直す (D2295 で却下した「tx の途中で読み取り下限を最新へ上げる」) | tuple 32・rratio 75・max_ope 4・skew 0.8・thread 8、既定設定 | reached 1,227・下限を実際に上げた tx 1,013 | `B_RETIRED` 3,273 (事象: pool 積み 2,667・pool からの再利用 606) | 3,273 / 3,273 が下限を上げた tx に帰属 | 巡回 0 (indeterminate) |
| 同上 | 同上 | 同 cell、最良設定 | reached 1,376・上げた tx 1,047 | `B_RETIRED` 3,715 (pool 積み 2,889・再利用 764・inline 返却 2・inline 再取得 60) | 3,715 / 3,715 | 巡回 0 |
| `m-drop-published-write` (U) | `cpv()` の後・`traceCommit()` の前に、公開済みの write set 要素を 1 つ外す (run で 1 回) | K t4、既定設定 | reached 165,561・changed 1 | `U_MISSING_W` 1 | 1 / 1 (同じ tx と版) | 巡回 0 |
| `m-skip-read-register` (API) | 外部 read の read set 登録を 1 回だけ飛ばし、body は返す | K t4、既定設定 | reached 752,575・changed 1 | `API_EXTERNAL` 1 | 1 / 1 (同じ tx と key) | 巡回 0 |

- **読み方。** 3 本とも、判定器 (巡回の検出) は巡回 0 の indeterminate を返した。M の照合だけがこれらの誤りを捉えた。P5 型の誤りは、構成 E の開発中 (md_14 の段 4 の仮裁定) に実物で起き、保持版検査が 3,882〜3,938 件中 159〜174 件の変化を見つけた型である (`../../2026-09-29/vhash-gc-connection-prototype/README.md` §3.3)。
- **帰属の言い方 (焦点再レビュー 3 巡目 N2)。** B の帰属は tx 単位で判定した: 違反の (thread, tx 通番) が、壊しが実際に下限を上げた tx に含まれる。壊しは tx 単位で読み取り下限を動かし、その tx が読んだ全版が回収の対象になるので、この鍵は機序に合う。ただし「違反の全件が壊しによって起きた」という個別の因果は示していない。版 pointer 単位で壊しの事象行と一致したのは 1,925 / 6,988 件 (事象行は tx ごとに 1 つの版しか書かないため)。
- **到達の経緯。** 壊し B は最初の版 (待機の最初に 1 回だけ下限を上げる、間引き 1/1024) では既定設定で 162 回中 1 回しか下限を上げられず、違反 0 (未発火) だった。leader は全 worker の `GCFlag` が立ったときだけ `MinWts`・`MinRts` を更新する (`util.cc:281-322`) ので、待機中に進む境界に追随するよう上げ直す形にした。

**既存の壊し 3 本 (md_3) を M の上に重ねた回帰確認 (M の発火証拠ではない):**

| 壊し | cell | 判定器 | witness の帰属 (md_3 の規則) | M の違反 |
|---|---|---|---|---|
| `broken-cicada-skip-read-recheck` | K t4 | non-serializable、巡回 8,791 | 21 | 0 |
| `broken-cicada-no-rts-update` | K t4 | non-serializable、巡回 759 | 25 | 0 |
| `broken-cicada-stale-read-ro` | R t4 | non-serializable、巡回 3,483 | 20 | 259 (`B_RETIRED` 220・`B_WINDOW` 39) |

**変異 (照合の単一理由性、段 4 裁定 v2 の事前登録、DW-M01)。** M の上に「1 つの照合の違反判定だけを常に合格にする」変異 patch (job dir の `mutations/mv-{b,u,api}.patch`) を重ね、対応する壊しを走らせた。kill = 起動器が壊しを「未発火」(事前登録した違反種別 0) と分類し、壊しの発火診断は到達を示すこと。変異は起動器が一時 checkout に重ね、tracked file は変えない。

| 変異 | 入力 | 1 回目 (mut-2) | 最終 (mut-3、Elapse 56 s) |
|---|---|---|---|
| MV-B (B の snapshot 判定と終了照合) | 壊し B、既定設定 BD t8 | killed | killed (違反 0、reached 1,252・下限を上げた tx 1,015) |
| MV-U (U の照合) | 壊し U、K t4 | **survived** — 変異が照合関数の呼び出しごと止め、W 行の計数 `u_w_rows` まで 0 にしたので、起動器の別の生存検査 (`u_reached`) が反応した。単一理由でないので kill と数えず、比較だけを無効にし計数を残す形に再照準した (段 6 裁定 8) | killed (違反 0、`u_w_rows` 777,318、changed 1) |
| MV-API (API の照合) | 壊し API、K t4 | killed | killed (違反 0、changed 1) |

stale-read-ro は read-only tx に 1 つ古い確定版を読ませる壊しで、M の B も、その古い版が読み手の生存中に回収・再利用されたことを 220 件捉えた (事象は pool 積み 214・再利用 6)。md_3 はこの壊しで既存の `READ_WTS_MISMATCH` が 43 / 60 件になったことを「版 object の再利用が起きたと推定 (未検証)」と記録していた (`../../2026-09-29/vhash-cicada-verifier/README.md` §2.3)。今回の B の事象はその推定と整合する (同じ run の比較ではない)。`B_WINDOW` 39 件のうち 2 件は事象の種類 `none` で、機序は調べていない。

## 5. 負例 — stock・最良設定・E-max で M の違反 0

全 run で判定 `pass` (§3.4 の式)。extime 1 秒・group_commit 0。cell: K = tuple 200・skew 0.9・rratio 50・max_ope 10、W = rratio 0・rmw・max_ope 5、R = rratio 90・max_ope 4、BD / BB = 壊し B の専用 cell (§4) の対照、E-max = 雛形 (md_21 の検査 cell) の A (tuple 50・skew 0.9) と B (tuple 10,000・skew 0) × GC 間隔 10 / 100 µs、thread 8、長い tx 2 本 (10 read の後に 10 ms 待つ)、`cicada_gc_mode=e`・前進先 max。

| job | genome | stack | cell | commit 数 | B 登録 | U 公開 | read 呼び出し | 版の事象 (pool / inline) | M の違反 |
|---|---|---|---|---|---|---|---|---|---|
| SMOKE | 既定 | stock | K t4 | 164,445 | 749,313 | 766,158 | 853,713 | 1,511,959 / 0 | 0 |
| SMOKE | 最良 | stock | R t4 | 1,441,085 | 4,967,621 | 574,507 | 5,216,519 | 747,743 / 427,293 | 0 |
| SMOKE | 最良 | E-max | A10 t8 | 370,927 | 3,176,577 | 1,625,634 | 3,957,351 | 6,288,385 / 5,765 | 0 |
| SMOKE | 既定 | stock | BD t8 | 553,432 | 1,534,310 | 538,638 | 1,692,794 | 1,060,794 / 0 | 0 |
| SMOKE | 最良 | stock | BB t8 | 1,925,891 | 5,918,259 | 1,879,623 | 6,520,226 | 3,815,150 / 747,147 | 0 |
| MAIN-1 | 既定 | stock | K t1 | 173,853 | 762,393 | 811,193 | 867,979 | 1,622,365 / 0 | 0 |
| MAIN-1 | 既定 | stock | W t1 | 191,383 | 897,895 | 897,895 | 956,915 | 1,795,758 / 0 | 0 |
| MAIN-1 | 既定 | stock | W t4 | 179,875 | 878,383 | 844,124 | 936,009 | 1,665,391 / 0 | 0 |
| MAIN-1 | 既定 | stock | R t1 | 473,804 | 1,623,670 | 189,249 | 1,705,000 | 378,488 / 0 | 0 |
| MAIN-1 | 既定 | stock | R t4 | 867,678 | 2,983,565 | 344,617 | 3,133,436 | 696,772 / 0 | 0 |
| MAIN-2 | 最良 | stock | K t4 | 371,952 | 2,258,825 | 1,734,029 | 2,565,840 | 3,394,156 / 1,174,371 | 0 |
| MAIN-2 | 最良 | stock | K t48 | 352,106 | 22,024,483 | 1,640,124 | 24,194,185 | 26,006,729 / 2,681,878 | 0 |
| MAIN-2 | 最良 | stock | R t48 | 7,177,702 | 27,755,852 | 2,857,137 | 29,162,088 | 7,187,596 / 907,852 | 0 |
| MAIN-3 | 最良 | E-max | A100 t8 | 365,800 | 3,135,809 | 1,602,949 | 3,908,990 | 6,201,843 / 5,648 | 0 |
| MAIN-3 | 最良 | E-max | B10 t8 | 534,837 | 2,685,110 | 2,671,646 | 2,686,360 | 3,951,592 / 1,300,200 | 0 |
| MAIN-3 | 最良 | E-max | B100 t8 | 531,631 | 2,668,404 | 2,656,381 | 2,669,557 | 3,884,988 / 1,373,250 | 0 |
| MAIN-4 | 既定 | stock | K t4 (旧壊し RTS の対照) | 167,158 | 765,910 | 779,379 | 871,717 | 1,554,077 / 0 | 0 |
| MAIN-5 | 既定 | stock | R t4 (旧壊し STALE の対照) | 878,482 | 3,019,216 | 350,030 | 3,170,975 | 707,458 / 0 | 0 |

- 「版の事象」は B の世代を進めた回数 (pool = GC の pool 積み + pool からの再利用、inline = inline slot の返却 + 再取得)。どの run でも読み手の版を巡る回収・再利用は大量に起きており、そのうえで読み手の生存中に既読版へ事象が届いた件数が 0 だった。
- 全 run で巡回 0、integrity の数値項目 0、C 行 = commit 数、既存の `READ_WTS_MISMATCH` 0 も成立 (起動器の checks、`runs/*/result-*.json`)。
- 所要: 1 run の実行は約 1 秒、判定器は 4〜75 秒 (最大は最良設定 R t48、trace 1.6 GB)。

## 6. TRACE=0 の同一性 (絶対規律 1)

同じ計算ノードで、同じ compile command (source の root だけ置換して一致を確認) で左右を TRACE=0 build し、Cicada の各 target の 3 TU (`transaction.cc`・`util.cc`・workload の `.cc`) を比べた (ident-5、patch 2aff9ff54、起動器 v9 sha256 `6bb6c5f9…`、Elapse 228 s)。

| 比べた組 | 左 | 右 | 結果 |
|---|---|---|---|
| 既定設定 × ycsb・tpcc・bomb・sbomb (4 組) | pin C | pin C + instr + M | 一致 |
| 最良設定 × ycsb・tpcc・bomb・sbomb (4 組) | pin C | pin C + instr + M | 一致 |
| 既定設定・最良設定 × ycsb の E-max stack (2 組) | pin C + instr + variant + gc + target | 同 + M | 一致 |

「一致」は、全 TU で (1) `objdump -d` の命令列 (address・記号を除き分岐先を置換した正規化) の sha256、(2) `objdump -dr` の逆アセンブル (address・行き先・relocation の記号名を残す厳密比較) の sha256、(3) compile command、(4) 前処理出力の空行以外の行 (差分行 0)、(5) binary の `nm`・`strings`、がそれぞれ一致し、(6) trace の語 (`izanagi_trace`・`CICADA_TRACE`・`CICADA_M_`) の残存が 0。前処理出力は空行の数だけが違う (`#if TRACE` の block を除いた跡)。(2) は焦点再レビュー 3 巡目の N3 (正規化が呼び先の違いを消しうる) を受けて足した。

途中の版では (1) が 1 命令だけ違い (§8 の 9)、`#line` を直して一致した。E-max の組は forwarding 3 patch の macro を左右に同じく渡した。

## 7. 論文に書ける文と書けない文 (md_24 §7 の表の M の欄を実装後の事実で更新)

| 層 | 書ける文 | 書けない文・限定 |
|---|---|---|
| 一般論証 | 小モデル仕様 v1 で forwarding は直列化可能性を保つ (D2292)。実装の条件 W* と GC 接続 G4〜G7 は主張しない | 「Cicada 実装 (forwarding + GC 接続) は一般に serializable を保つ」 |
| 実装の観測履歴 (巡回) | 「検査した run で、観測した実行の依存グラフに巡回は無かった。巡回を生む誤り 3 種を入れた版では巡回として検出された」 | 巡回 0 は indeterminate であって certified ではない |
| 実装の観測履歴 (M の照合) | 「TRACE ビルドで、生存中の tx が読んだ版が、登録から tx 終了まで回収・再利用されていないこと、`cpv()` が公開した版・設置した版・記録した書き込みが一致すること、外部の読みが read set に漏れなく登録されることを全 tx で照合し、stock の既定設定と最良設定、および forwarding と GC 接続の試作 (E-max) の 18 run で違反は 0 だった。これらの照合は、早すぎる回収・公開の記録漏れ・読みの登録漏れを人為的に入れた版で発火し、その 3 種はいずれも巡回の検査では見えなかった」 | 範囲は YCSB の point read / update、`REUSE_VERSION=1`、`group_commit=0`、promotion なし (§3.5)。読んだ版は「登録時点で同じ key の確定済み可視版として一貫していた」までで、版を選んだ瞬間から登録までの窓で同じ object が同じ key の別の確定版として再利用された場合は、その版の読みとして記録される (§3.1)。Cicada の版選択規則への適合、終状態の正しさは主張しない。公開の照合は `cpv()` を通る公開に限り、write set に入る前の書き込みの喪失は範囲外。API の照合のうち発火を確かめたのは外部 read の登録漏れだけ (再読・自分の書き込みの読み・過剰な登録は未確認)。設置と公開の照合の発火も未確認 (壊し U は公開と記録の間で要素を外す型) |
| 性能値の地位 (D2305 項 4 (2)) | 照合を満たした設定の TRACE=0 build の測定値は「照合の中身を明記した測定値」として論文で扱ってよい。M の範囲の設定 (既定・最良の stock、E-max の検査 cell) はこの wave で照合を満たした | izanagi 内部の判定は indeterminate のままで、certified とは呼ばない。検査したのは各条件 1 秒の run で、主比較の条件 (tuple 100 万・3 秒) そのものではない |
| TRACE=0 | 計装は `#if TRACE` の内側だけで、TRACE=0 の命令列は pin と一致した (§6) | — |

## 8. 実機で見つけて直した欠陥 (段 6)

静的なレビューと Codex の適用確認では見つからず、計算ノードの SMOKE・本走で初めて見えた欠陥。すべて Codex の fix 子が直し、同じ計測を取り直した。

| # | 症状 (実測) | 原因 | 修正 |
|---|---|---|---|
| 1 | 起動器が M patch を「offset 付き適用」で拒否 | M の hunk header が `pin C → instr` 後の source とずれていた。子の確認は `git apply --check` だけで、offset を失敗として扱わない | hunk header を直し stock で offset 0。E-max では文脈完全一致の offset を許し記録する (段 6 裁定 1) |
| 2 | 同一性 build の cmake configure が rc 1 | CCBench の `.gitattributes` が `oze* export-ignore` を指定し、起動器の `git archive` による展開から `cc/oze` が抜けた | 雛形 (md_23 の起動器) と同じ pinned full checkout に戻した |
| 3 | 壊し B が compile できない | 同じ TU に宣言の無い `clock_delay` を使った | `rdtscp()` と `FLAGS_clocks_per_us` の busy wait |
| 4 | build 失敗の後の configure が連鎖で失敗 | 起動器が同じ build dir を使い回した | build ごとに一意な dir |
| 5 | 起動器が違反行の解析を拒否 | M が `kind=v_U_MISSING_W` のように集計 key の接頭辞を付けて出した (出力契約違反) | 接頭辞なしに |
| 6 | 壊し B が既定設定で未発火 (下限を上げたのは 162 回中 1 回) | 待機の最初に 1 回だけ上げていた | 待機中に上げ直す、間引き 1/64 |
| 7 | 壊し B が発火しているのに不合格 | 起動器が md_3 の計数の順序 (reached ≥ changed ≥ committed) を B に当てた。B の committed は選んだ tx の commit 数で changed の部分集合でない | B の順序を定義し直し、帰属を tx 単位に (段 6 裁定 5) |
| 8 | E-max で insert / delete の hunk が `update` 関数に当たった | 同じ文脈が別の関数にもあり、offset 付き適用が別の位置に一致した | 各関数固有の文脈へ移し、18 hunk の関数の一致を照合 |
| 9 | TRACE=0 の命令列が 1 命令だけ pin と違う (`gc_records()` の `ERR` の `__LINE__` が 853 → 854) | `#line N` の後の `#endif` 行も行番号を進めるので、M の `#line` が 1 行ずれた | 42 本の `#line` を両 stack で M 適用前の行と機械照合し不一致 0 に |
| 10 | 同一性が不一致と判定される (命令列・compile command・nm・strings は一致) | 前処理出力の比較が、TRACE ブロックを除いた後の空行の増減まで数えた | md_3 と同じ「空行以外の差分 0」に |
| 11 | 変異 MV-U が kill されない | 変異が U の照合関数の呼び出しごと止め、W 行の計数まで 0 にしたので、起動器の別の生存検査が反応した | 照合の比較だけを無効にし計数を残す形へ再照準 (§4 の変異の表に初回の結果を残す) |

## 9. 確かめたこと・確かめていないこと

確かめたこと:
- §4〜§6 の各値は、計算ノードで得た result (`runs/<tag>/result-*.json`) と raw stderr から、起動器の合否と親の照合で読んだ。
- M の B は inline slot を含む版の回収・再利用の事象を数え、最良設定と E-max の run でその事象が実際に起きた (§5 の表)。
- 3 種の誤りは巡回の判定器では見えず、M の照合で見えた (§4)。

確かめていないこと:
- **一般の正しさ。** 検査は各条件 1 秒の有限の run についてである。主比較の条件 (tuple 100 万・thread 48・3 秒) そのものは走らせていない (最良設定の R t48 と K t48 は tuple 200)。
- **範囲外の構成。** TPC-C・scan・insert・delete、`REUSE_VERSION=0`、`group_commit>0`、promotion 有効、`SINGLE_EXEC=1`。M の起動器は insert / delete / scan の呼び出し 0 を要求し、範囲外の実行を不合格にする。
- **版を選んだ瞬間から登録までの窓** (§3.1 の論拠で扱い、実験では窓の中の再利用を狙った壊しは作っていない)。
- **API 照合のうち再読・自分の書き込みの読み・過剰な登録、U 照合のうち設置と公開の照合の発火** (正例を作っていない)。
- **B の違反の個別の因果** (tx 単位の帰属まで、§4)。
- tx 単位の B 母集団等式は独立な検査になっていない (§3.4)。
- stale-read-ro の `B_WINDOW` のうち事象の種類 `none` の 2 件の機序。
- 走行中の版 object の解放経路が無いことは、範囲内の source と forwarding 3 patch の読解による陰性であって、全経路の不存在証明ではない (§3.5 の範囲の固定で補う)。

## 10. 工程と計算

- **段 1〜4 のやり直し。** 段 2 の前に読むべき dev-wave の条件節 DW-O13 (検査を新設する wave は、述語の入力の実在と要求値の到達可能性を先に実測する) を読み落としたまま段 2〜4 を進め、段 5 の前に気づいて段 2〜4 を無効化し (job dir `invalidated-v1/`)、brief に追補して段 2 から取り直した。
- **子の構成。** 段 2 plan (Codex、read-only) 1 本、段 3 相談 2 本 (Codex、レンズ = 正しさ境界 / 過剰・削除)、段 5 実装子 2 単位 (Codex author: U1 = patch 4 本と変異 patch、U2 = repo 外の起動器)、段 6 レビュー 2 本 (Codex、レンズ = 照合と起動器の正しさ / 過剰・削除)、焦点再レビュー 3 巡 (上限、Codex)、fix 子 13 本 (Codex、段 6 裁定 1〜9)。起動器の実行経路の調査に read-only の調査子 (Claude sonnet) を 1 本使った。
- **裁定。** 段 4 裁定 v2 (`verbatim/s4-ruling.md`)、段 6 裁定 1〜9 (`verbatim/s6-ruling-*.md`)。焦点再レビュー 3 巡目の後に残った 4 所見 (N2〜N4 と MV-U) は親が実測と文言で閉じた (裁定 9)。
- **計算ノード。** job 22 本 (SMOKE 5・MAIN 10・IDENT 4・MUT 3)、Elapse 合計 2,549 s (約 0.71 node 時間)、1 本の最大 228 s。途中で同じ計測用 checkout から 6 本を同時に dispatch して 5 本が起動前に拒否された (同一 checkout の dispatch は直列が規則) ので、以後は checkout を 3 本に分けて並行させた。provenance 監査の dispatch 1 本 (Elapse 8 s) は別。
- **repo の成果物。** `patches/instr-cicada-trace-m.patch`、`patches/broken-cicada-m-{early-reclaim,drop-published-write,skip-read-register}.patch`、`patches/README.md` の entry、本資料、spool fragment。`patches/ledger.json` は変えていない (Cicada の trace 系 patch は登録しない先例、md_3)。判定器 (`orchestrator/verifier/`)・campaign・既存 patch は変えていない。
