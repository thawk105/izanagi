# 段 4 裁定 — md_19 ccbench-cicada-bugfix (2026-09-29 22:40 JST、親)

入力: brief-stage1.md、out/s3-consult-A.md (正しさ境界、sol)、out/s3-consult-B.md (実効性・過剰、luna)。両出力とも check_codex_output rc=0。
裁定 inbox 再走査: /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox の最新 (2026-09-29-interactive-evolution-verdicts.md、21:47) に CCBench / Cicada / T-2904 の語なし → 取り込む更新なし。
peer: md_23 が項目 3 (gc_records ERR, T-2908) を専任 (md_23.txt 21:35 を実物確認、了承済み)。

## 所見の裁定 (親が実物で確認した結果)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A-1 | promotion の read_set_ 二重 emplace (transaction.hh:209-210) が scan 結果を重複させ TPC-C OrderStatus で ERR し得る | 機構は real (scan は rset_init_size 以降の read_set_ 要素を全部 result へ積む、transaction.cc:450-455 を実物確認)。ただし TPC-C の反例は refuted — is_ronly_ を立てるのは include/ycsb.hh:106 だけで TPC-C は常に false、209 行の分岐に入らない (git grep 全数)。YCSB の Cicada は scan を使わない。 | **採用 (scope 内)**: 二重 emplace は read_internal が read_set_ に積むようになった後に取り残された同じ腐敗であり、YCSB の promotion genome の trace の R 行・validation・rts 更新を重複させる。行数不変で除去する (R1)。 |
| A-2 | YCSB の再試行で is_ronly_ が戻らない | real (ycsb.hh:106 は RETRY の外)。直列化可能性の反例ではない (再試行は RW 経路で validation される)。影響は promotion genome の read-only tx が promotion 後に abort した場合の再試行だけ。 | 不採用 (scope 外、insight に記録)。workload 共通 header (include/ycsb.hh) の設計問題で、直し方 (ronly に戻すか RW のまま再試行か) は上流作者の判断に属する。 |
| A-3 | early abort が Status に出ず TPC-C helper が値を使い続け得る | promotion 固有ではない (update の early abort は F 既存の挙動)。TPC-C は is_ronly_=false だが promotion の update は RW tx でも起きうるので、promotion で early abort の機会が増えることは real。ただし tx ループ末尾で abort されるので commit されない (A 自身の判定)。 | 不採用 (scope 外、insight に記録)。 |
| A-4 | P1 の「ERR の __LINE__」は誤り (NNN は __LINE__ を展開しない) | refuted — ERR は NNN を展開し、NNN の本体の `__LINE__` は使用箇所 (transaction.cc:337・853) の行番号に置換される (debug.hh:54-65 実物)。T-2854 §0 の 2 と同じ理解。 | 記録上の区別 (既定 context の preprocess 一致と物理行番号の維持を別に書く) は採用。 |
| A-5 | 待ち時間の積の overflow | 事実だが実害の範囲外 (2^64 / 2100 clock ≈ 8.8×10^15 µs ≈ 279,000 年)。 | 不採用 (nit)。 |
| A-6 | `#error` を外した使い捨て計装は promotion の観測として成立する | 採用。診断変種と明記し、W 行・C 行 = commit 数・R 行の実値を記録する (R6)。 |
| A-7 / B-3 | 小走行の合格は観測した cell に限る | 採用 (記録の書き方)。 |
| B-1 | W5 の待機を aggregate throughput だけで合格にしない | real。**採用**: 直接の実行証拠を trace の per-thread commit 数で取る (R5)。 |
| B-2 | D297 pass と「修正 TU の意図した差分」を別に記録 | 採用 (R8)。C→G の expected path = F の 3 file + cc/cicada の 2 file。 |
| B-3' | F で 8 genome を再 build する対照は不要 | 採用。対照は較正 wave の既存失敗ログ (pin C、cicada は C==F を実測) を使う。 |
| B-4 | CI 緑を項目 1・2 の検査として扱わない | 採用。非既定 build (24 genome・ADD_ANALYSIS=1・W5) を独立の合否にする。 |
| B-5 | T-2854 の judge / CI build は OID 置換だけでは走らない | real。採用 (R7・R8: 親 = F、expected path 5 file、G の complete-history bundle)。 |
| B-6 | md_17 起動器は C/C1 固定・OPT=0 固定・job 固定 | real。採用 (R6: job dir の複製を G 用に限定して改修)。 |
| B-7 | 較正 driver は pin.py と未定義 macro に束縛 | real。採用 — driver は使わず、driver と同じ cmake 引数の build 専用 script を書く (R4)。 |
| B-8 | A2 (ADD_ANALYSIS=1 の未定義 start) を外せる | 不採用 → **scope 内に残す** (R2)。同じ非既定区間の腐敗で、izanagi の診断 build (ADD_ANALYSIS=1) で promotion genome を使えない。1 行の置換で、成功を独立の合否にする。 |
| B-9 | tpcc_cicada.exe の promotion build・F cell × 1 thread・format の image 2 つは削れる | F cell × 1 thread と tpcc の単独 build は削る。format は login 14.0.0 + CI image `:latest` の 2 通りを T-2854 と同じく維持 (image 取得済み、秒単位)。TPC-C の promotion は R6 の診断 trace 走行で build される。 |
| B-10 | GCC 2 版の D297 は維持 | 採用。 |
| B-11 | 他 wave との重なりと適用順を一次資料へ | 採用。version-lifetime patch (他 wave) は同じ runtime flag を読む独自の待機 `IZANAGI_CICADA_LONGTX` を commit() 冒頭に足す (patch 828 行付近を実物確認) — G の WORKER1_INSERT_DELAY_RPHASE と同時に有効にすると二重に待つ。一次資料に書く。G への適用可否は R9 で cicada 系 patch 全部を実測し、C での実測を G へ一般化しない。 |
| B-12 | P7 は暫定見積り | 採用。 |

## plan v2 (実装)

- **R1 (A1+A1'):** `cc/cicada/include/transaction.hh` inlineVersionPromotion: 207 行 `write(` → `update(`。209-210 行の `read_set_.emplace_back(s, key, tuple, later_ver, ver);` を除去し、`is_ronly_ = false` は残す。物理行数を変えない (空いた行はコメントで「read_internal() が既に read_set_ に積んだ」と書く等)。使われなくなる引数は `[[maybe_unused]]` 等で新しい警告を出さない。
- **R2 (A2):** `cc/cicada/transaction.cc` read_internal の PROMOTION 分岐内 `#if ADD_ANALYSIS` の `result_->local_read_latency_ += rdtscp() - start;` を、行数不変で無効化する (read() 側の計上は残す)。
- **R3 (A3):** `cc/cicada/transaction.cc:924-925` を `unlikely(thid_ == 1) && FLAGS_worker1_insert_delay_rphase_us != 0` と `sleepTics(FLAGS_worker1_insert_delay_rphase_us * FLAGS_clocks_per_us);` に置換 (行数不変、include を足さない)。
- 変更は上の 2 file、非既定 #if 区間の内側だけ。clang-format 14 の `--dry-run --Werror` を 2 file と全 213 file 前後で通す。commit は親 (Codex author・reviewer・Claude manager の trailer)、branch `izanagi-cicada-build-fix` (F の子 1 commit)。README.md (cc/cicada) の記述は flag の意味と一致するので変えない。

## 検証 (事前登録、結果を見る前に固定)

- **R4 build (job 1):** G の ycsb_cicada.exe を CICADA_SPACE の正準 24 genome (BACK_OFF・INLINE_VERSION_OPT・INLINE_VERSION_PROMOTION・REUSE_VERSION・WRITE_LATEST_ONLY、PROMOTION⇒OPT) で TRACE=0・ADD_ANALYSIS=0・gcc 11 (較正 driver と同じ cmake 引数・toolchain 解決)。合格 = 24/24 rc=0 かつ compile_commands の -D が genome と一致。加えて ADD_ANALYSIS=1 で promotion の 2 genome (BACK_OFF 0/1、他 1/1/1/0) rc=0。対照 = 較正 wave の既存失敗ログ (8 genome・W5、pin C)。
- **R5 W5 (job 1 + job 2):** (a) TRACE=0: 既定 genome + CCBENCH_WORKER1_INSERT_DELAY_RPHASE=1 の G build で YCSB rr50 (max_ope 10、tuple 較正 wave の W 系と同じ値)、extime 1、`-worker1_insert_delay_rphase_us` ∈ {0, 100000} を thread 2 で交互に 3 反復、対照に thread 1 × {0, 100000} を 1 反復ずつ。予測 (結果前に固定): thread 2・100000 の throughput は thread 1 の値と同程度 (+ 高々 extime × 10 commit)、thread 2・0 はその約 2 倍、thread 1 は flag で変わらない。(b) 直接証拠 (job 2): 同じ W5 build を TRACE=1 (計装 patch) で thread 4、flag 1000 µs、extime 1 で走らせ、trace の C 行を thid ごとに数える。合格 = thid 1 の commit 数 ≤ 1000 (1 s / 1 ms) かつ他の thid の中央値の 1/2 未満、判定器 R6 と同じ合格条件。flag 0 の同 build を対照に 1 本。
- **R6 正しさ小走行 (job 2):** md_17 起動器の job dir 複製を G 用に改修 (base = G、patch 順: 計装 → TPC-C 計装、identity plan・build_source_oids を G に)。判定器は変えない。cell: (i) 既定 genome YCSB K・W・R × thread 1・4、TPC-C M・R2 × thread 4 (標準の計装 patch 2 本)、(ii) promotion genome (OPT=1・PROMO=1、BACK_OFF=0・REUSE=1・WLO=0) YCSB K・W・R × thread 4 と TPC-C M・R2 × thread 4 — 計装 patch の `#error` 3 行を外しただけの診断変種 (job dir、repo 外)、(iii) R5(b)。各 1 反復。合格 = verdict indeterminate (上限)・total_cycles 0・integrity 数値項目 0・existence_violations 0 (v3)・C 行 = commit 数・CICADA_TRACE_READ_WTS_MISMATCH 0。promotion が起きたことの証拠として、(ii) に全操作が読み取りの cell P (YCSB rratio 100・rmw false・max_ope 4、他は K と同じ) × thread 4 を足し、その trace の W 行数 (> 0 なら promotion 由来に限られる) と commit 数を記録する。W 行 0 なら「promotion を観測できなかった」と書き、promotion の正しさを主張しない。一つでも anomaly なら G を出さず停止 (規律 2)。TPC-C F cell は項目 3 のため対象外。
- **R7 CI (job 3 + login):** T-2854 の run_ci_build.sh を親 = F、NEW = G、G の complete-history bundle に改修して CI image `:ci` で全 protocol Release build。合格 = configure・build rc=0、CCBench 本体の警告・error 0、実行 file 34 本。format: check_format_ci.sh で G の checkout に login clang-format 14.0.0 と image `:latest` の 2 通り、合格 = rc=0。
- **R8 D297 (job 4):** T-2854 の run_judge.sh を親 = F、C→G の expected path = {cc/cicada/include/transaction.hh, cc/cicada/transaction.cc, cc/mocc/transaction.cc, cc/silo/transaction.cc, include/trace.hh}、bundle head = G に改修し、GCC 11・12 並行。合格 = 両 rc=0。一次資料では「選定 configure (stock・mocc・silo) の pass」と「F→G の cicada 2 file の変更行と有効になる macro 条件 (意図した変更、D297 の対象外)」を分けて書く。
- **R9 patch 適用 (login、軽量):** G の checkout に patches/ の cicada 系 patch を、単独および既定の重ね順 (計装 → TPC-C 計装 → broken 系、forwarding 系の既定順) で `git apply --check` し、結果 (当たる / offset / 失敗) を記録する。patches/ は変えない。
- 計算: 4 job を別 checkout から同時 dispatch。暫定見積り 0.7 node 時間 (D297 0.28 + build 26 本 0.25 + trace 0.15 + CI 0.02)、確認線 2 node 時間の下。
- 変異 matrix: izanagi 側の実装面の差分は 0 (commit は insight と fragment) なので DW-S04 により免除。G の検査は非既定 build の成功 (旧 tip では失敗の既存ログ)、W5 の per-thread 対照、判定器の小走行が担う。

## 追補 1 (2026-09-29 23:20 JST、R8 の訂正)

R8 の「C→G の expected path = 5 file」は親の誤り。T-2854 の run_judge.sh が照合していたのは **直親 → 新 tip** (C2'→F の 3 file) の変更 path で、C→F ではない。実測: C→G は 6 file (cc/cicada の 2 + cc/mocc・cc/silo の transaction.cc + include/tpcc.hh + include/trace.hh)、F→G は 2 file。判定 job 1 回目 (request 36300.nqsv、Elapse 5 秒) は入力照合の「C to new changed paths differ from the five ruled files」で rc=2、検査器は起動していない。訂正: run_judge.sh の path 照合は T-2854 と同じく **直親 F → G = `cc/cicada/include/transaction.hh cc/cicada/transaction.cc`** とし、検査器の old は C のまま (判定は C→G の全差分に掛かる)。一次資料には C→G の 6 file と F→G の 2 file を分けて書く。

## 追補 2 (2026-09-29 23:35 JST、promotion の新事実)

**新事実 (trace-1、request 36301.nqsv、bnode070、結果 = evidence/trace-1/result-ALL.json):** promotion genome (OPT=1・PROMO=1・BACK_OFF=0・REUSE=1・WLO=0、診断変種の計装) の YCSB thread 4 で判定器が non-serializable を返した — K: total_cycles 4 (G2)、R: 327。W と P は indeterminate・巡回 0。integrity 数値項目はすべて 0、C 行 = commit 数、READ_WTS_MISMATCH 0。cell P (全読み取り) は W 行 0 で promotion を観測できなかった。TPC-C の M・R2 (thread 4) は `std::bad_alloc` の SIGABRT (rc=-6) で異常終了。既定 genome の 8 run と W5 の 2 run は全合格。

**裁定:**
1. 規律 2 により promotion の 8 genome (INLINE_VERSION_OPT=1 ∧ INLINE_VERSION_PROMOTION=1) は失格。G で build できる (R4 合格) ことと、正しく動くことを分けて記録する。VHash の比較・探索でこの 8 genome を使わない。
2. G の promotion 修正は取り消さない。F ではそもそも compile できず、G は他のどの build も変えない (既定前処理一致・R9 一致)。compile できることで欠陥が観測可能になった。上流への push 時に人間が判断できるよう、一次資料に明記する。
3. 本 wave で行う切り分けは 1 job に限る (診断、結果を見る前に登録):
   - D1: G の二重登録除去が原因でないこと — 同じ promotion genome に「除去した `read_set_.emplace_back(s, key, tuple, later_ver, ver);` を戻す」使い捨て patch を当てた build (PROMO_DUP_Y) と PROMO_Y を、YCSB K・R × thread 4 × 各 2 反復で同じ job 内で交互に走らせる。予測: どちらも non-serializable (巡回 > 0)。PROMO_DUP_Y だけ巡回 0 なら、除去が原因の疑い → G を見直す (停止して再裁定)。
   - D2: TPC-C の異常終了が計装由来でないこと — promotion genome を TRACE=0・patch なしで tpcc_cicada.exe を build し、M・R2 × thread 4 × 各 2 反復。予測: 異常終了 (rc≠0、bad_alloc) が再現する。
   - D3: PROMO_Y K の 1 反復は raw trace を job dir (repo 外) に残し、巡回の witness を後の原因調査に渡す。
4. 原因の特定と修理は本 wave で行わない (新しい T 項目、P2)。md_23 の gc_records 修理と同じく、原因を特定してから直す。

**追補 2 の結果 (23:41 JST、request 36355.nqsv、evidence/diag-1/result-DIAG.json):** D1 = PROMO_Y (K 7・8、R 313・297) と PROMO_DUP_Y (K 13・14、R 336・330) の 8 走行とも non-serializable → 予測どおり、G の重複除去は原因ではない (停止・再裁定の条件に当たらない)。D2 = PROMO_T0 (TRACE=0・patch なし) の TPC-C M・R2 × 2 反復が 4 走行とも SIGABRT・std::bad_alloc → 予測どおり計装由来ではない。D3 = raw trace を evidence/diag-1-kept-trace/ に保存 (174 MB)。

## 追補 3 (2026-09-29 23:40 JST、D297 検査器が C→G を判定できない)

**新事実 (judge-2、request 36352.nqsv、Elapse 9 秒、evidence/judge-2/gcc11.stderr・gcc12.stderr):** 検査器 (tools/check_trace0_preprocess_identity.py、GCC 11・12 とも) は rc=1 で、判定に入る前に「source_digest: cc/cicada/transaction.cc の条件指令が未知マクロ ['INLINE_VERSION_OPT', 'INLINE_VERSION_PROMOTION', 'SINGLE_EXEC', 'WORKER1_INSERT_DELAY_RPHASE'] を参照 … fails-closed で停止 (T-148)」と拒否した。検査器には path を除外する引数が無い (`--expect-paths` は厳密一致の要求)。

**裁定:**
1. 検査器を変えない (CONTEXT_MACROS への cicada macro の登録は gate の変更で本 wave の scope 外。緩和もしない、規律 2)。
2. md_19 の「修正で意味が変わる TU を除いて取り直す」は、次の形で満たす: F→G の変更 path は cicada の 2 file ちょうど (実測)。D297 の選定文脈 (stock・mocc 0〜7・silo 0〜7) の consumer に cicada の file は無い (T-2854 §0 の 5「未選定の調査 cicada 24 (consumer なし)」)。したがって選定文脈の TRACE=0 同一性について C→G で言えることは C→F の判定 (T-2854、GCC 11.4・12.3 とも pass) と同じ。これは推論であり、検査器の C→G pass ではない、と一次資料に書く。
3. 修正した cicada の 2 file は「意図した変更」として、変更行・有効になる macro 条件・既定文脈で無効であることの予測水準の実測 (実装子 A/A2 の login 前処理比較: 2 file × ADD_ANALYSIS 0/1 の 4 比較が F と byte 一致、#include 行を除く) を書く。
4. pin を G へ進める wave は D297 をこの拒否に当たる。申し送り (新 T 項目) に「cicada の文脈 macro の扱い (登録するか、cicada の変更を別途の同一性検査で扱うか) を決める」を入れる。

## 分割 (段 5)

- 実装子 A (child md19-cicada-fix-a、所有 = `R/ccbench/cc/cicada/include/transaction.hh`・`R/ccbench/cc/cicada/transaction.cc`): R1〜R3。login での確認は clang-format と、可能なら `g++ -fsyntax-only` 相当の軽い compile 確認 (4 文脈: 既定、OPT+PROMO、OPT+PROMO+ADD_ANALYSIS、WORKER1)。重い build は計算ノードで親が行う。
- 実装子 B (child md19-cicada-fix-b、所有 = `R/scripts/` 配下の新規): R4〜R9 の job body と診断変種 patch。G の OID は引数で受ける。

規模上限: A は 2 file・変更行 10 行以内。B は job body 5 本 + 起動器複製 1 + 変種 patch 1。
