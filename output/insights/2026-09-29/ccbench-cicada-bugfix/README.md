# CCBench Cicada の build 不具合 2 件 (+ 計器 build 1 件) を F の子 commit G で直し、24 genome と W5 が build でき、上流 CI 2 本を手元で通した。promotion 有効の 8 genome は build できるようになったが、判定器が直列化違反を検出し TPC-C で異常終了するので失格。push はしていない (人間の手番)

authority: none
default_effect: no-state-change

- 日付: 2026-09-29
- wave: `dev-wave-ccbench-cicada-bugfix` (branch `worktree-dev-wave-ccbench-cicada-bugfix`)。着手時 local main `8fe87f852ec41e0a07a9be10bcb10e5d867117b4` (開始 gate rc=0、`verbatim/startup-gate.log`)
- 依頼: md_19 (`verbatim/md_19.txt`)。ユーザーの判断 (2026-09-29 21:3x JST)「CCBench の不具合は直したい」— 還元判断がユーザー確認待ちだった [T-2904] を「直す」で確定。
- 分担: md_19 の項目 3 (TPC-C 全 mix × 4 thread の `gc_records()` の ERR、[T-2908]) は、後から作られた専用依頼 md_23 (21:35 作成、md_19 は 21:30) が専任で扱う。md_23 の session からの連絡を md_23.txt の実物で確かめて了承した。本 wave は項目 1・2 だけを扱い、T-2908 の台帳項目に触れない。
- 既裁定: D2277 項 1・2 (上流 CI 2 本を通す品質、基盤の欠陥は使いながら直す)、D16・D18・D20 (push・PR は人間)、D297・D2255 (TRACE=0 同一性)、D2293 (T-2854 の整形 commit F)、D2279・D2294 (Cicada の trace)。
- job dir (使い捨て script・生 log・Codex receipt・bundle・計算の全出力): `/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/` (= `/work/1/SFC/tanab/tmp/...`)。以下 `$J`。

## 0. 結論

1. **G:** CCBench の新しい local branch `izanagi-cicada-build-fix` = F `25898d00` の子 **G `eb93423bbb27a2694d3d75861696c365f0fb8f7c`** (tree `3ed13669`)。変更は `cc/cicada/include/transaction.hh` と `cc/cicada/transaction.cc` の 2 file・5 行の置換 (行の追加・削除なし、mode 不変)。作成は Codex author、commit は親 (trailer 3 行 = Codex author・Codex reviewer・Claude manager)。bundle = `$J/G.bundle` (3,191,534 byte、sha256 `d0bc871a…`、C・F・G を含む complete history)。差分の逐語 = `verbatim/F-to-G-diff.md`。
2. **build (完了条件 1):** 計算ノード (request 36302.nqsv、bnode073、Elapse 141 秒) で G の `ycsb_cicada.exe` を `CICADA_SPACE` の正準 24 genome すべて configure・build rc=0。compile_commands.json の 3 TU の `-D` はすべて期待値と一致、source は G。promotion 有効の 8 genome (INLINE_VERSION_OPT=1 ∧ INLINE_VERSION_PROMOTION=1) を含む。ADD_ANALYSIS=1 の promotion 2 genome と W5 の build (WORKER1_INSERT_DELAY_RPHASE=1) も rc=0 (計 27/27)。対照: F と同じ cicada の bytes を持つ pin C では、この 8 genome と W5 は compile できなかった (較正 wave の既存 build log、§1)。
3. **W5 (完了条件 2):** 待機は実行で入る。trace を入れた W5 build で thread 4・`-worker1_insert_delay_rphase_us=1000`・1 秒の走行では、worker 1 の commit は **2 件** (他の thread は 61,078 / 59,590 / 59,241 件)。待機 0 の同じ build では worker 1 は 47,551 件。事前登録した合格条件 (worker 1 が 1,000 件以下、かつ他の thread の中央値の半分未満) を満たす (§4.2)。trace なしの性能 build で事前に書いた throughput の予測は、向きは合ったが大きさが外れた (§4.1)。
4. **正しさ (完了条件 3):** 既定 genome の YCSB K・W・R × thread 1・4 と TPC-C M・R2 × thread 4、W5 の 2 走行の計 10 走行で、判定器は全部 `indeterminate` (Cicada の上限)・巡回 0・integrity 数値項目 0・C 行数 = commit 数・READ_WTS_MISMATCH 0 (§4.3)。計装 patch 2 本 (instr-cicada-trace・instr-cicada-trace-tpcc) は G にそのまま当たった。
5. **promotion 有効の 8 genome は失格 (規律 2)。** 計装の `#error` を外した診断用の変種で promotion genome の 1 設定 (BACK_OFF=0・REUSE_VERSION=1・WRITE_LATEST_ONLY=0) を走らせると、判定器は YCSB K で巡回 4 件 (G2)、R で 327 件を検出した (W・P は巡回 0)。TPC-C M・R2 は `std::bad_alloc` で異常終了した。promotion の経路はこれまで compile できず、一度も走っていなかった。**異常は 1 設定で観測したもので、安全側の判断として 8 設定すべてを VHash の比較・探索から除外する。build できることと正しく動くことは別である。** 切り分けの job で、G で除いた重複登録を戻しても YCSB K・R の巡回は残り (4 走行とも non-serializable)、計装なし (TRACE=0) でも TPC-C M・R2 は同じ `std::bad_alloc` で落ちた。つまり重複登録の除去は観測した巡回に必須ではなく、TPC-C の異常終了は計装なしでも再現する。原因そのものは未特定 (§5)。
6. **上流 CI (完了条件 4):** format: G の checkout で CI の step (`git ls-files -- cc include common | grep -E '\.(cc|hh|cpp)$' | xargs clang-format --dry-run --Werror`) が **213 file・rc=0**、login の clang-format 14.0.0 と CI image `:latest` の 14.0.6 の両方。build: CI image `:ci` (GCC 13.3.0・cmake 3.28.3・ccache 4.9.1) で CI と同じ Release・sanitizer OFF の全 protocol build が **configure・build rc=0、CCBench の実行 file 34 本、CCBench 本体 (`cc/` `include/` `common/`) の warning・error 0 件** (request 36307.nqsv、bnode005、Elapse 33 秒)。CI との差は T-2854 §3 と同じ (依存は手元 cache の clean clone、ccache は空から、image は 2026-09-29 取得時点の tag)。**CI の既定 build は今回直した非既定の分岐を compile しないので、CI 緑は項目 1・2 の検査ではない** (それは 0 の 2 が担う)。
7. **D297 (完了条件 5):** D297 検査器 (`tools/check_trace0_preprocess_identity.py`) は C→G を判定できなかった。cicada の transaction.cc が変わると、その条件指令が参照する cicada 固有の macro (INLINE_VERSION_OPT を含む計 4 つ) が検査器の既知の文脈に無いため、判定の前に fails-closed で止まる (GCC 11・12 とも rc=1、request 36352.nqsv)。検査器は変えていない。F→G の変更は cicada の 2 file だけで、D297 の選定文脈 (stock・mocc 0〜7・silo 0〜7) には cicada を取り込む TU が無いので、選定文脈について C→G で言えることは T-2854 の C→F の判定 (GCC 11.4・12.3 とも pass) と同じである — **これは推論であって、検査器の C→G pass ではない** (§6)。
8. **既存 patch への影響なし:** patches/ の cicada 系 patch 10 本の単独適用と既定の重ね順 7 系列の `git apply --check` の記録 (rc・offset の有無・verbose 出力・適用結果の計 160 field) は、G と F で完全に一致した (§7)。
9. **pin は C のまま。** gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・`patches/` は変えていない。push もしていない (§9)。

## 1. 直した不具合と原因

| # | 症状 (F / pin C) | 原因 | 直し方 (G) |
|---|---|---|---|
| 1 | INLINE_VERSION_OPT=1 ∧ INLINE_VERSION_PROMOTION=1 の 8 genome が `transaction.hh:207: cannot convert 'Storage' to 'int'` で compile できない | `inlineVersionPromotion()` が、`update()` に改名された旧 `write()` を呼んでいた。gcc は名前を POSIX の `::write(int, …)` に解決した | `write(` → `update(` |
| 1' | (compile できれば) 読み取り専用 tx が promotion するとき、読み取り集合に同じ要素を 2 回積む | `read_internal()` が読み取り集合に積むようになった後も、promotion 側の追加が残っていた。重複は validation と rts 更新を 2 回行い、読み取り専用 tx の `scan()` なら同じ行を 2 回返す (現行の YCSB は scan せず、TPC-C は読み取り専用の指定を立てないので、現行 workload では起きない) | 重複の `read_set_.emplace_back(...)` を除き、その行で `(void) later_ver;` と理由のコメントにした (引数名は F のまま残す — 計装 patch の hunk が引数行を文脈に含むため) |
| 2 | 同じ組で ADD_ANALYSIS=1 のとき `transaction.cc:131: 'start' was not declared` | `read_internal()` の promotion 分岐が、存在しない計時開始値で読み取り時間を加算していた。`read()` 自身が計時している | 加算の行をコメントに置換 |
| 3 | WORKER1_INSERT_DELAY_RPHASE=1 で `transaction.cc:924-925` が compile できない (`thid`・`WORKER1_INSERT_DELAY_RPHASE_US`・`clock_delay` が未宣言) | 分岐が member 名 `thid_`、待機関数、待ち時間の出所と食い違っていた。runtime flag `-worker1_insert_delay_rphase_us` (common.hh:61、util.cc:145 で表示、README.md:56 が「runtime 引数で設定した時間」と説明) はどこからも読まれていなかった | `thid_ == 1`、`FLAGS_worker1_insert_delay_rphase_us` (2 か所)、`sleepTics()` (include/util.hh:250、backoff.hh 経由で既に取り込み済み、include を足さない) |

- 1 と 3 の症状は較正 wave (`output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md` §8.1・§8.2) の build log で観測されたもの。2 は本 wave の段 1 で親が静的に見つけ、login の構文検査で確かめた。
- 親の構文検査 (予測、login、`g++-11 -std=c++20 -fsyntax-only`、transaction.cc の 1 TU、`verbatim/probe_syntax-2.log`): F は非既定の 3 文脈 (OPT+PROMO、それに ADD_ANALYSIS=1、WORKER1_INSERT_DELAY_RPHASE=1) で上の error をそのまま出し、G は 4 文脈 (既定を含む) とも rc=0。決め手は計算ノードの本 build (0 の 2)。
- **全部の変更は非既定の `#if` 区間の内側の行の置換で、物理行数は F と同じ (375 行 / 986 行)。** 既定文脈の preprocess 出力は変わらない見込み: 実装子が login で 2 file × ADD_ANALYSIS 0/1 の 4 比較を `#include` 行を除いた `g++ -E -P` で行い、F と byte 一致 (予測水準、`verbatim/s6-fix-A2.md`)。`ERR` (include/debug.hh の `NNN` 経由で使用箇所の `__LINE__` に展開) は transaction.cc の 337・853 行にあり、行数不変なのでその値も変わらない。

## 2. 直さなかったもの (scope 外、段 4 裁定で不採用)

- **YCSB の再試行で読み取り専用の指定が戻らない** (`include/ycsb.hh:106` は `is_ronly_` を再試行 label の外で 1 回だけ設定する。promotion で false にした tx が abort すると、再試行は読み書き tx として走る)。直列化可能性の反例ではない (再試行は validation を受ける) が、promotion genome の読み取り専用 tx の再試行の中身が変わる。workload 共通 header の設計の問題で、直し方は上流の作者の判断に属する。
- **`update()` の early abort が `Status` に出ない** (status_ を aborted にしても `Status::OK` を返す)。F 既存の挙動で promotion 固有ではない。tx ループの末尾で abort されるので commit はされない。
- **待ち時間の積の桁あふれ** (`FLAGS_worker1_insert_delay_rphase_us * FLAGS_clocks_per_us`、uint64)。起きるのは約 8.8×10^15 µs (約 28 万年) を超える指定だけ。

## 3. 他の wave との重なり

- **md_23 (gc_records の修理):** 同じ F の上に別の local branch を作る。md_23 の変更面は `gc_records()` 周辺 (transaction.cc:845-857 付近) の見込みで、G の変更行 (transaction.hh:207・210、transaction.cc:131・924-925) とは離れている。2 本を 1 本にまとめるかは push を担う人間の判断。
- **instr-cicada-version-lifetime.patch (他 wave):** `commit()` の冒頭に、同じ runtime flag `FLAGS_worker1_insert_delay_rphase_us` を読む独自の待機 (`#if IZANAGI_CICADA_LONGTX`) を足す。G の WORKER1_INSERT_DELAY_RPHASE と**同時に有効にすると worker 1 は 2 回待つ** (待ち時間が 2 倍になる)。どちらか一方だけを有効にする。
- 計装 patch・forwarding 系・broken 系の hunk の当たり方は G と F で同じ (§7)。

## 4. 検証の結果

事前登録 = 段 4 裁定 `verbatim/s4-ruling.md` の R4〜R9 (結果を見る前に固定)。job body はすべて Codex author (job dir の `scripts/`、sha256 = `verbatim/scripts-sha256.md`)、投入は親の `run-job.sh`。

### 4.1 W5 — trace なしの性能 build での throughput (R5(a))

W5 build (既定の正準点 + WORKER1_INSERT_DELAY_RPHASE=1、G)、YCSB rratio 50・rmw 0・max_ope 10・zipf 0.9・tuple 1,000,000、extime 1、同じ job 内で交互に走らせた。全走行で `#FLAGS_*` の表示値が argv と一致した。

| thread | 待機 (µs) | 反復 | throughput (tps) | abort 数 |
|---|---|---|---|---|
| 2 | 0 | 1 / 2 / 3 | 211,411 / 212,044 / 211,586 | 1,956 / 1,906 / 1,888 |
| 2 | 100,000 | 1 / 2 / 3 | 150,862 / 150,007 / 150,177 | 10 / 9 / 10 |
| 1 | 0 | 1 | 185,839 | 0 |
| 1 | 100,000 | 1 | 185,791 | 0 |

事前の予測と照合 (親が行った):
- 「thread 1 は flag で変わらない」— **成立** (185,839 と 185,791、worker 1 が存在しない対照)。
- 「thread 2・待機なしは thread 1 の約 2 倍」— **不成立** (1.14 倍)。この条件の 2 thread の伸びが小さい理由は調べていない。
- 「thread 2・100 ms 待機は thread 1 と同程度 (+ 高々 10 commit)」— **不成立**。thread 1 より 35,000 件前後少ない (150,177 対 185,839)。worker 1 が止まっている間に worker 0 が遅くなる機序は調べていない (最も古い tx が止まると GC の下限が進まない、という VHash の主題と同じ形の仮説はあるが未検証)。report の自動欄 `all_delayed_t2_within_t1_plus_10_commits: true` は片側だけの比較 (差が負でも真) なので、合格の根拠にしない。
- 待機を入れると throughput が下がり abort が減る、という向きは出ている。待機が入ったことの直接の証拠は 4.2。**この表の値は性能の主張に使わない** (同時刻の対照はあるが、目的は待機の実在の確認で、反復・node 条件を性能比較用に組んでいない)。

### 4.2 W5 — trace の thread 別 commit 数 (R5(b)、直接の証拠)

trace を入れた W5 build (計装 patch、TRACE=1)、YCSB K、thread 4、extime 1。trace の C 行を thid ごとに数えた。

| 待機 (µs) | thid 0 | thid 1 | thid 2 | thid 3 |
|---|---|---|---|---|
| 1,000 | 61,078 | **2** | 59,590 | 59,241 |
| 0 (対照) | 42,015 | 47,551 | 49,339 | 49,435 |

事前登録の合格条件「worker 1 の commit ≤ 1,000 (1 秒 / 1 ms) かつ他の thread の中央値の半分未満」を満たす。1 ms の待機で worker 1 の commit が 1,000 件に届かず 2 件まで落ちたのは、待っている間に他の worker の書き込みと衝突して abort し続けたためと見られる (abort の内訳は数えていない)。2 走行とも判定器は巡回 0 (4.3)。

### 4.3 正しさの小走行 (R6)

起動器 = md_17 の起動器を G 用に改修した複製 (job dir、判定器は変えない)。request 36301.nqsv、bnode070、Elapse 266 秒。全 build の source = G、compile_commands の `-D` と `#FLAGS_*` の照合は全 run で一致。判定器は `python -m verifier --protocol cicada` (TPC-C は v3)。

| build | cell | thread | commit 数 (= C 行数) | 判定 | 巡回 |
|---|---|---|---|---|---|
| 既定 (計装) | YCSB K | 1 / 4 | 207,597 / 187,227 | indeterminate | 0 / 0 |
| 既定 (計装) | YCSB W | 1 / 4 | 233,096 / 202,509 | indeterminate | 0 / 0 |
| 既定 (計装) | YCSB R | 1 / 4 | 577,405 / 953,207 | indeterminate | 0 / 0 |
| 既定 (計装 + TPC-C 計装) | TPC-C M | 4 | 44,975 | indeterminate | 0 |
| 既定 (計装 + TPC-C 計装) | TPC-C R2 | 4 | 33,589 | indeterminate | 0 |
| W5 (計装) | YCSB K、待機 1,000 µs | 4 | 179,911 | indeterminate | 0 |
| W5 (計装) | YCSB K、待機 0 | 4 | 188,340 | indeterminate | 0 |
| promotion (診断変種) | YCSB K | 4 | 384,357 | **non-serializable** | **4** |
| promotion (診断変種) | YCSB W | 4 | 394,668 | indeterminate | 0 |
| promotion (診断変種) | YCSB R | 4 | 1,525,445 | **non-serializable** | **327** |
| promotion (診断変種) | YCSB P (全読み取り) | 4 | 2,402,178 | indeterminate | 0 |
| promotion (診断変種 + TPC-C 計装) | TPC-C M / R2 | 4 | — | **異常終了** (`std::bad_alloc`、SIGABRT) | — |

- job 全体の rc は 1 (request 36301.nqsv の child rc=1)。内訳は promotion の TPC-C 2 走行の異常終了 (rc=-6) で、他の 14 走行は rc=0。
- 判定器が結果を返した 14 走行ではすべて、integrity の数値項目 (orphan_reads・version_dups・dup_txids・genesis_commits・missing_txids・write_version_mismatch・malformed_keys・framing・lock_coverage・write_intent・permutation) は 0、`CICADA_TRACE_READ_WTS_MISMATCH n=0`。異常終了した 2 走行には判定器の結果が無い。`integrity.clean` は Cicada では構造上 false なので合否に使っていない。上限は `indeterminate` で、certified は名乗らない。
- cell の定義: YCSB K = rratio 50・max_ope 10、W = rratio 0・rmw・max_ope 5、R = rratio 90・max_ope 4、P = rratio 100・max_ope 4 (いずれも tuple 200・zipf 0.9・extime 1)。TPC-C M = payment/order_status/delivery/stock_level 43/0/0/0、R2 = 43/4/0/20、warehouse 1、extime 1。Delivery を含む cell は項目 3 (md_23) の欠陥のため対象外。
- **promotion の診断変種:** 計装 patch は promotion と TRACE=1 の組を `#error` で止めている (md_3 の判断、当時は promotion が compile できなかった)。その `#error` の 1 行だけを除いた変種 (job dir `scripts/instr-cicada-trace-promotion-diag.patch`、repo 外) で走らせた。promotion の書き込みは write_set_ に入るので traceCommit の W 行に出る (段 3 相談 A の静的確認)。標準の計器で保証された結果ではない。
- cell P (全読み取り) は W 行が 0 で、promotion を観測できなかった (初期版が inline 版にあると promotion の条件 `ver != &tuple->inline_ver_` が成り立たないため、と見られる。未確認)。K・R の W 行のうち promotion 由来の数は trace から区別できない。
- **観測した cell の結果に限る。** 巡回 0 は全スケジュールの直列化可能性の証明ではない。

## 5. promotion の失格と切り分け

§4.3 の結果を受けて、段 4 追補 2 で promotion の 8 genome を失格とし (規律 2)、G で除いた重複登録を戻すと YCSB の巡回が消えるか、計装なしでも TPC-C が異常終了するか、の 2 点だけを 1 job で確かめた (結果を見る前に予測を登録)。request 36355.nqsv、Elapse 236 秒、全 build の source = G、compile_commands の `-D` と `#FLAGS_*` の照合は全 run で一致 (`verbatim/evidence/result-DIAG.json`)。

**D1 — G の重複登録の除去が原因か:** promotion genome (計装の診断変種) に、G で除いた `read_set_.emplace_back(s, key, tuple, later_ver, ver);` を戻す使い捨て patch (job dir `scripts/restore-promotion-dup-emplace.patch`、1 行置換) を当てた build (PROMO_DUP_Y) と、G のままの build (PROMO_Y) を、同じ job 内で交互に走らせた (YCSB thread 4、各 2 反復)。

| cell | 反復 | G のまま: commit 数・巡回 | 重複登録を戻す: commit 数・巡回 |
|---|---|---|---|
| K | 1 | 367,646・7 | 368,983・13 |
| K | 2 | 368,830・8 | 378,786・14 |
| R | 1 | 1,491,990・313 | 1,506,400・336 |
| R | 2 | 1,466,145・297 | 1,488,450・330 |

登録した予測 (どちらも non-serializable) どおり、8 走行とも non-serializable。重複登録を戻しても観測した K・R の巡回は消えないので、G の除去はこの巡回に必須ではない (巡回の件数は戻した側がやや多いが、この差の意味は調べていない)。§4.3 の本走 (K 4 件・R 327 件) と合わせ、promotion genome (G のまま) の K・R の巡回は独立した 2 job・計 3 回の走行で再現した。TRACE=0 の YCSB で巡回が出るかは判定器が掛けられないので調べていない。

**D2 — TPC-C の異常終了は計装由来か:** promotion genome を TRACE=0・patch なしで build し (tpcc_cicada.exe、compile_commands で TRACE=0・OPT=1・PROMO=1 を確認)、TPC-C M・R2 × thread 4 × 各 2 反復を走らせた。4 走行とも SIGABRT (rc=-6)、stderr は `terminate called after throwing an instance of 'std::bad_alloc'`。登録した予測どおり計装なしでも再現した。TPC-C の異常終了に計装は必須ではない (どの箇所で起きるかは調べていない)。

**D3:** 巡回 7 件の PROMO_Y・K・反復 1 の raw trace を job dir `evidence/diag-1-kept-trace/PROMO_Y-K-t4-r1.trace` (174 MB、repo 外) に残した。原因調査 (新しい台帳項目) の入口にする。

**言えること・言えないこと:** promotion 有効の Cicada (G の上) は、観測した YCSB cell で直列化違反の履歴を出し、TPC-C で異常終了する。原因は特定していない。候補の例として、読み取り専用として rts で読んだ後に書き込み tx へ変わる経路の validation、promotion が他の版の本体 (`ver->body_`) を copy する時点でその版が回収・再利用されている可能性 (bad_alloc は壊れた長さの copy と整合する) があるが、どちらも未検証である。言えるのは、F ではこの経路が compile できず比べる正しい挙動が無かったこと、重複登録を戻しても観測した巡回が残ること、TPC-C の異常終了が計装なしでも起きることまでで、G の変更全体や計装全体が原因でないことを証明したのではない。

## 6. D297

- judge 1 回目 (request 36300.nqsv、Elapse 5 秒): 親の段 4 裁定の誤り (C→G の変更 path を 5 file と書いた。T-2854 の判定 job が照合していたのは直親 → 新 tip の path で、実測では C→G は 6 file、F→G は 2 file) で、判定 job の入力照合が rc=2。検査器は起動していない。裁定を「F→G = cicada の 2 file」に訂正した (`verbatim/s4-ruling.md` 追補 1)。
- judge 2 回目 (request 36352.nqsv、Elapse 9 秒): 検査器が GCC 11・12 とも rc=1。stderr (逐語 = `verbatim/evidence/judge-2-gcc11.stderr.md`): 「source_digest: cc/cicada/transaction.cc の条件指令が未知マクロ ['INLINE_VERSION_OPT', 'INLINE_VERSION_PROMOTION', 'SINGLE_EXEC', 'WORKER1_INSERT_DELAY_RPHASE'] を参照 … fails-closed で停止 (T-148)」。検査器に path を除外する引数は無い。
- 扱い (段 4 追補 3): 検査器を変えない (cicada の macro を CONTEXT_MACROS に登録するのは gate の変更で本 wave の範囲外、緩和もしない)。選定文脈についての結論は C→F の判定 (T-2854) と同じと**推論**する (F→G は cicada の 2 file だけ、選定文脈の consumer に cicada は無い)。cicada の 2 file の変更は「意図した変更」として §1 に書いた。
- **pin を G へ進める wave は、D297 のこの拒否に当たる。** cicada の文脈 macro をどう扱うか (登録するか、cicada の変更を別の同一性検査で扱うか) を決める必要がある (新しい台帳項目)。

## 7. 既存 patch の当たり方 (R9)

`scripts/check_patch_apply.sh` (Codex author) で、G と F の clean な checkout に patches/ の cicada 系 patch 10 本を 1 本ずつ、および既定の重ね順 7 系列 (計装 → TPC-C 計装 → broken 4 本の各々、計装 → TPC-C 計装、forwarding variant → GC → GC の壊し、計装 → forwarding variant → GC) を `git apply --check` (fuzz なし) した。結果 (`verbatim/evidence/patch-apply-G.json`・`patch-apply-F.json`、比較 = `verbatim/compare_patch_apply.log`):
- 記録された 160 field (単独 10 段 × 4 field、系列 20 段 × 6 field。rc・offset の有無・verbose 出力・適用結果を含む) が G と F で完全に一致。
- 単独で rc=0 は 3 本 (instr-cicada-trace・instr-cicada-version-lifetime・cicada-forwarding-variant)。他の 7 本は前提の patch が要るので単独では当たらない (G 固有ではなく F でも同じ)。
- 7 系列はどの段も rc=0。offset 付きで当たる段 (broken 系 3 本、forwarding の GC 系) も F と同じ。
- 重ね順は起動器と各 patch の前提から組んだもので、patches/README.md との逐一の照合は行っていない。

## 8. 工程と費用

- 軽量版 (段 2 省略)。正しさと基盤に関わるので段 3 相談 2 本 (正しさ境界 A = sol、実効性・過剰 B = luna)、段 6 のレビューを修正 2 本 + 焦点 1 本、検証 script に 2 本 + 焦点 1 本。
- 段 3 の主な採用: promotion の重複登録の除去 (A、TPC-C の反例は親が refuted — TPC-C は読み取り専用の指定を立てない)、W5 を throughput だけで合格にしない (B)、CI 緑を項目 1・2 の検査として扱わない (B)、流用 script の固定値 (B)。
- 段 6 の must-fix: 無名引数化で計装 patch の hunk の文脈が変わり当たらなくなる (レビュー B2 — 親の「行数不変なら当たる」予測の反例) → 引数名を戻して `(void) later_ver;` にした。検証 script の偽の緑 6 件と起動失敗 2 件 (SA・SB) → 修正。いずれも焦点再レビューで closed。
- 段 7 の記録レビュー (本資料と fragment 3 本を証拠と照合、`verbatim/s6-review-R7.md`) は NO-GO で 6 件 (原因の切り分けの言い過ぎ、異常終了した走行を含めた integrity の量化、job 数、8 genome と実測範囲の区別、計算 job の rc の書き漏らし、patch 適用の field の内訳)。反映後の焦点再確認 (`verbatim/s6-review-FR7.md`) で残った 2 件と新しい 2 件 (macro の数、decisions と worklog の範囲) も直し、2 回目の焦点再確認 (`verbatim/s6-review-FR7b.md`) で 8 件すべて closed・GO。
- G は 1 度作り直した。1 回目 `09b8eef43` は commit message の「重複要素は scan() で 2 回返されていた」が言い過ぎ (現行 workload では起きない) だったので、どの検証にも使う前に branch を消して message だけを直した (tree は同じ `3ed13669`、`verbatim/mk-G-attempt1.log`)。
- 計算 job の rc: buildci-1 = 0、trace-1 = 1 (promotion の TPC-C 2 走行の異常終了、§4.3)、judge-1 = 2 (入力照合、§6)、judge-2 = 1 (検査器の拒否、§6)、diag-1 = 0。
- 計算 (Elapse): build 141 秒 + CI 33 秒 + trace 266 秒 + judge 5 秒 + 9 秒 + 診断 236 秒 = 690 秒 ≈ 0.19 node 時間 (6 request、確認線 2 node 時間の下)。login では format と patch 適用の検査、構文の予測検査だけを行った。

## 9. push とその後 (人間の手番)

G の branch は land 後に主 checkout の submodule へ非 force で取り込む (本 wave の段 9)。その後、主 checkout で:

```
cd external/ccbench
git push origin izanagi-cicada-build-fix
```

別名の新 branch なので force は不要。F (`25898d00`、T-2854) がまだ GitHub に無ければ祖先として一緒に上がる。md_23 の branch (同じ F の子) と 1 本にまとめるかは push のときの判断。push 後に GitHub の Actions で build・format が緑であることを確かめてから、pin の前進 (gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・patch の厳密適用) を別 wave で行う。その wave は §6 の D297 の拒否と、§5 の promotion の失格を前提にする。

## 10. 確かめたこと・確かめていないこと

確かめた: 0 の 1〜8。確かめていない:
- GitHub Actions の CI が緑であること (push 前)。
- promotion genome の直列化違反と異常終了の原因 (§5)。promotion 以外の genome の直列化可能性も、観測した cell の範囲でしか言えない。
- 8 genome と W5 の性能値 (pin 前進後の別 wave)。4.1 の throughput は待機の実在の確認用で性能値ではない。
- D297 検査器による C→G の pass (§6)。
- ADD_ANALYSIS=1 の promotion 以外の genome の build (今回は promotion の 2 genome だけ)。TPC-C の target の非既定 genome の build (promotion の診断走行で build されたものを除く)。
- W5 の待機が 1 ms で worker 1 の commit を 2 件まで落とした機序 (abort の内訳)。

## 11. 再現資料

- `verbatim/`: brief・段 4 裁定 (追補 1〜3)・相談 2 本・実装子と fix の報告・レビュー・F→G の差分・G の commit log・開始 gate・login 検査の log・構文 probe。
- `verbatim/evidence/`: build・CI・trace・診断の report JSON、judge の stderr、patch 適用の JSON。
- job dir: 使い捨て script (Codex author の `scripts/`、親の `run-job.sh`・`mk-G.sh` ほか)、Codex receipt (`codex/`)、`G.bundle`、計算の全 log (`evidence/`)。
