## 1. inline 版の記録

**結論。** `INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0` でも、成功した点読みは `read_set_` から R、commit した更新は `write_set_` から W に出る。初期ロードの版は inline slot にある。ただし、**R の時刻を「読み手が選んだ版の時刻」と断定するには窓が残る**。`read_internal()` が版を選んでから、計装された `ReadElement` のコンストラクタが `ver->ldAcqWts()` を読むまでに、その slot が返却・再取得されれば、新しい版の時刻を保存しうる。現行 trace は選択時の時刻を別に保存しない。

**根拠。** 初期版の配置は `external/ccbench/cc/cicada/include/tuple.hh:74-85`。slot の返却と取得は同ファイル `:54-71`、新しい wts の設定は `include/transaction.hh:217-225`、GC からの返却は同 `:173-195`。読みの scan、read set 登録、payload の受け渡しは `transaction.cc:99-137,144-189`。計装は `patches/instr-cicada-trace.patch` の `cicada_op_element.hh` hunk で**登録時**の wts を取り、`transaction.hh` hunk の `traceCommit()` で R に使う。再読は既存 read set または write set を使う (`transaction.cc:153-165`) ので、同一 txn 内の再読ごとに R は増えない。W は commit 時の write set の最終操作を出す。read-only commit も R を出す (`transaction.cc:929-937` と計装 hunk)。

GC の境界は `transaction.cc:806-842` の `gcq.front().wts_ < MinRts` である。通常の読み手が保護されていれば、この窓で返却されないはずだが、**この静的確認だけでは MinRts と読み手の生存区間の安全性を証明できない**。したがって「窓がある」は条件付きのリスクであり、実際に誤記録すると決め付けない。

validation は `transaction.cc:543-569` で再走査した `Version*` と保存した `ver_` をポインタ比較する。inline slot は同じアドレスで再利用されるため、返却・再取得が読み手と重なれば ABA で一致しうる。さらに trace 時の再読が同じ新しい wts なら `READ_WTS_MISMATCH=0` となる。誤った wts が別の W と結び付けば巡回や orphan read が出る可能性はあるが、整合する別履歴に見えれば**いずれにも出ない**。逆に登録時には旧 wts を保存でき、commit 時までに slot が変わった場合には mismatch が出る。mismatch は原因の証明ではなく診断値である。

診断用の最小の重ね patch は repo 外に置く。既存 patch の bytes は変えない。`#if TRACE` 内で `ReadElement` に「登録時に `ver == &rcdptr->inline_ver_` だったか」を保持し、`traceCommit()` の R/W ループで **commit した R/W の総数と inline slot 件数**を加算する。W は `we.new_ver_ == &we.rcdptr_->inline_ver_` で判定する。終了時に例えば `CICADA_INLINE_TRACE R=<n> R_INLINE=<n> W=<n> W_INLINE=<n>` を stderr に一行出す。別に `newVersionGeneration()` の inline 取得件数を数えれば、`W_INLINE=0` が単なる低頻度かを判断できる。各カウンタの適用範囲は `#if INLINE_VERSION_OPT` の内部の `#if TRACE` とし、`OPT=0` でも compile できるよう参照を守る。診断 patch 自身も trace と実行特性を変えるので、その build の throughput は使わない。

**(P2) との食い違い。** 「版は読んだ時点に保存した wts」は登録時点については正しいが、scan で版を選んだ瞬間とは同一でない。また inline W の有無を数えるだけでは、R の時刻取り違えやポインタ ABA は検出できない。

## 2. BACK_OFF=0 と REUSE_VERSION=0 の経路

**結論。** `BACK_OFF=0` は abort 後の `backoff()` と leader の `leaderBackoffWork()` を外すだけで、C/R/W/E の emit site を変えない。abort と再試行の密度が変わるため、履歴の件数・競合は変わる。`REUSE_VERSION=0` は heap 版を GC 時に delete するが、inline slot の返却・再利用は止めない。`traceCommit()` の `re.ver_->ldAcqWts()` は、GC が読み手を守るという前提が破れれば、R の保存値と比較する前に解放済み heap 版を読む危険がある。

**根拠。** BACK_OFF の二箇所は `transaction.cc:770-772,962-967`。heap 版の GC による再利用と delete は `include/transaction.hh:173-195`、abort した未 install 版の返却と delete は同 `:343-367`。計装の mismatch 比較は `patches/instr-cicada-trace.patch` の `transaction.hh` hunk。`REUSE=0` なら allocator が同じアドレスを再利用する可能性もあるので、ポインタ同一性だけを版同一性の証明にはできない。`WRITE_LATEST_ONLY=0, rmw=0` の blind write は `transaction.cc:263-288` で時刻に応じた版位置を探し、`validation()` の `:497-527` で途中に install できる。読んでいない key に R を捏造せず、commit 時に W を一件出す扱いが適切である。

**brief との関係。** `REUSE=0` なら解放済み版の再読は「GC が安全なら起きない」という記述は条件付きとして維持する。mismatch が 0 でも安全性の証明にはならない。

## 3. build の束縛

**結論。** build spec ごとに五軸の値を持たせ、`configure_values()` が共通引数から `CCBENCH_BACK_OFF` を一度除いてから五軸を一度ずつ追加する。CMake の後勝ちには依存しない。cache、対象 target の三つの TU の compile command、binary hash を build ごとに保存・照合する。

| build | BACK_OFF | OPT | PROMOTION | REUSE | WLO | TRACE | ADD_ANALYSIS |
|---|---:|---:|---:|---:|---:|---:|---:|
| BEST | 0 | 1 | 0 | 1 | 0 | 1 | 0 |
| BEST100 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| CTRL | 1 | 0 | 0 | 1 | 0 | 1 | 0 |

**根拠。** 共通引数は `orchestrator/campaign/s3_mocc_lock_coverage.py:261-267` で `STOCK_G.cmake_defines()` を展開し、`STOCK_G` の `BACK_OFF=1` は同 `:49-50`。雛形は `launch_cicada_run.base-md17.py:32-39,237-255` の固定 `CMAKE_VALUES` を全 build に使い、`:1024-1038` で cache を照合する。md_11 の `tools/vhash_cicada_tuning/driver.py:59-91` の `check_compile_commands()` は target を `CMakeFiles/ycsb_cicada.exe.dir/` に限定して `transaction.cc`・`util.cc`・`ycsb_cicada.cc` を各一件確認し、重複 `-D` も拒否する。期待辞書の `TRACE` を 1、`ADD_ANALYSIS` を 0 として再利用できる。CMake 名への変換は同 `:250-252` と `model.py:22-24` に合わせる。

雛形の `cache_values()` (`:244-255`) は指定したキーしか見ないため、`CCBENCH_BACK_OFF` と `CCBENCH_ADD_ANALYSIS` も期待値に入れる。compile command の照合は cache 照合の代わりにならない。共通引数の `-DCCBENCH_BACK_OFF=1` の後に `=0` を足すだけだと、今回の CMake invocation でたまたま後勝ちでも、引数順序変更や cache 再利用で束縛を誤る。要求した CMake key 自体の重複を事前に拒否する。

**brief との食い違い。** 「BACK_OFF を上書き」は実装上は重複指定を作らず、共通引数から取り除いて一意に指定するのがよい。

## 4. matrix と規模

**結論。** 主検査は高競合の小さい tuple 集合を中心にし、1M・t48 は**短い実走を先に一件だけ較正**してから採否を決める。1M・t48・1秒を全設定へ無条件に掛ける案は trace 量と verifier の上限 900 秒に対して危険である。W4 は高 abort 率なので、trace build の commit 数を見て低すぎれば同じ事前登録条件で走行秒数を増やす。commit 数を見ずに「巡回なし」と解釈しない。

| 段 | workload | 設定 | tuple | thread | GC µs | extime | run 数 |
|---|---|---|---:|---:|---:|---:|---:|
| L0 inline 生死確認 | W2 | BEST、CTRL | 200 | 4 | 10 | 1 | 2 |
| J1 高競合 | W1/W2/W3 | BEST、CTRL | 200 | 4、48 | 各最良値、10（同値なら一回） | 1 | 最大 22 |
| J1 長い txn | W4 | BEST100、CTRL | 200、1,000 | 4、48 | 1,000、10 | 1 | 16 |
| J2 尺度確認 | W1/W2/W3/W4 | 対応 BEST、CTRL | 1,000,000 | 48 | 各最良値 | **較正後に決定** | 最大 8 |
| 正例 | W2 | BEST と同じ値の壊し build | 200 | 4 | 10 | 1 | 1 |

J1 は組合せの重複を除いた上限であり、総数は最大 49。W4 の 1,000 tuple は 200 tuple で commit が少ない場合の事前登録した第二尺度である。別の cell で代用しない。J2 は L0/J1 の trace 行数と verifier 秒数から、予測 trace 行数・処理時間・空きメモリを算出し、**1 run の verifier 予測が 600 秒以上なら投入しない**縮小梯子にする。その場合 1M は未検査と明記する。

**根拠と見積り。** md_3 の K t4 は約 18万 commit (`vhash-cicada-verifier/README.md:70-84`)、既存 job は build と複数 run を含め 69〜101秒 (`:162-173`)。md_17 の TPC-C は約 1.0〜1.3百万 trace 行で約 30〜43千 commit (`vhash-cicada-verifier-ext/README.md:61-70`)、3〜4 run と build を含む job が約 1.5〜3.5分 (`:142-153`)。これらは workload が違うため、単価を固定値として外挿できない。親 brief の「2,000万 txn で約23分」という verifier 単価を使うなら約 **69 µs/txn** だが、既存起動器の `verify()` は **900秒で timeout** (`launch_cicada_run.base-md17.py:791-812`)。1M・t48 は md_11 の無計装値では W3 約1,105万 commit/秒であり、trace build が大幅に遅くなっても大容量になりうる (`vhash-cicada-baseline-tuning/README.md:110-134`)。trace 行数は txn 数に操作数が掛かるので、この単価だけで実行可とは言えない。

2 node 時間は **job の Elapse の総和**で管理する。L0 を一ノード、J1 を workload 別の数ノードに分け、各 job が build を共用する。J2 は L0/J1 の実測を使い、投入前に `build + run + verifier + 余裕` を各 job で積算して総和 7,200秒未満を確認する。W4 は md_11 で BEST100 の abort 率 0.916 (`:134`) だが、無計装では約9.6万 commit/秒なので「必ず commit 不足」とは言えない。trace 下の実数で判断する。

**(P1) との食い違い。** 1M・t48 は性能較正には必要だったが、trace 判定の必須全 cell としては予算・timeout を超えるおそれがある。200 tuple・t48 も abort 増大で commit が減るため、t4 と両方取る。

## 5. 正例対照

**結論。** 既存の `broken-cicada-skip-read-recheck.patch` は、計装 patch の後に重ねる設計で、BEST の `OPT=1, PROMOTION=0, B0` とソース上の変更箇所は衝突しない見込みである。ただし hunk の実適用と build は親の検査で確定する。同じ W2・200 tuple・t4・GC 10 の BEST stock と正例を並べ、`changed>0`、`committed>0`、巡回>0、witness の rw 辺が事象の key・a_wts に一致することを要求する。巡回が出なければ「未発火」「盲点」「検出したが帰属不能」を区別する。

**根拠。** 壊し patch は `transaction.cc` の validation 比較 `:563-569` を変え、計装 patch は commit 付近 (`:907,934` の hunk) を変える。既存起動器は `[INSTR, broken-cicada-skip-read-recheck.patch]` を既に登録する (`launch_cicada_run.base-md17.py:39-44`)。md_3 の既定 K t4 では巡回 7,517、代表 witness 20/20 が事象に帰属した (`vhash-cicada-verifier/README.md:98-110`)。これは BEST での検出を保証しないため、その設定での正例が必要である。

inline slot を早く返す専用の壊しは、ABA 窓の検出力を直接問える価値がある。一方で、返却時点・読み手の保護・slot 再取得を意図的に競合させる必要があり、単一 site の変更でもクラッシュや未定義動作になりやすい。今回の必須正例にはせず、L0 の inline 件数または mismatch に異常が出た場合の repo 外追加実験とする。

**(P3) との食い違い。** 既定設定での正例実績を BEST にそのまま移せない。BEST で同じ cell の正例を取り直す。

## 6. TRACE=0 同一性

**結論。** 同一性は BEST と BEST100 の CMake 値で各一組取る。雛形 `trace_zero_identity()` の pin と計装済み checkout の双方へ**同じ genome**を渡し、三 TU の compile command、前処理の非空行、命令列、`nm`、`strings` を照合する。`#line` は PROMOTION=0 では内部昇格関数の `#if INLINE_VERSION_PROMOTION` hunk が無効になるが、計装の他の hunk には引き続き効く。実際の命令列一致で確定する。

**根拠。** 雛形は `launch_cicada_run.base-md17.py:353-408` で二 checkout を作り、現状は固定 `CMAKE_VALUES` を両方へ使う。`identity_plan()` は同 `:114-128`。計装 patch の `#line` は `cicada_op_element.hh`、`transaction.hh`、`transaction.cc`、`ycsb_cicada.cc` の各 hunk にある。md_3 は既定に近い値で YCSB 三 TU の命令列一致を確認した (`vhash-cicada-verifier/README.md:115-123`) が、BEST と BEST100 は未確認。

性能値を出さない wave でも、TRACE=0 時に試作 patch が stock の実行コードを変えないという主張を BEST の build 値に拡張する価値がある。ただし予算が逼迫したら、同一性は正しさの実走より優先しない。既存計装の bytes を変えない今回、同一性を性能比較の成立条件と呼ぶ必要はない。

**(P4) との食い違い。** BEST/BEST100 での再確認は有用だが、今回の「巡回の有無」を判定する必須条件とは分ける。

## 7. 判定と事前登録

**結論。** run の受理条件は `stock_pass()` を基礎に、巡回 0、integrity の各数値 0、C 行と stdout commit 数一致、全 W の wts が initial_wts より大、異常終了なしを個別に保存する。判定語は「その条件で巡回なし（上限 indeterminate）」とする。`READ_WTS_MISMATCH>0` は**診断異常として stock_pass を不合格**にし、件数・設定・raw を残す。mismatch を直列化違反の証明とは呼ばない。

**根拠。** 雛形の検査は `launch_cicada_run.base-md17.py:211-226,731-747,845-922`。Cicada の `integrity.clean` は証拠面 unavailable のため使えず、md_3 が列挙する数値項目を照合する (`vhash-cicada-verifier/README.md:74-86`)。D2279 により certified の判定には到達しない。

巡回が出たら判定器の witness から `cycle`、各辺の種別、始点・終点 txid、key、読んだ版、次版、trace の C/R/W 行の所在を構造化する。追加 build は次のとおり、**元の巡回 cell のみ**走らせる。

| 巡回した設定 | 追加 build | B | O | P | R | W |
|---|---|---:|---:|---:|---:|---:|
| BEST | CTRL＋B0 | 0 | 0 | 0 | 1 | 0 |
| BEST | CTRL＋O1 | 1 | 1 | 0 | 1 | 0 |
| BEST100 | CTRL＋B0 | 0 | 0 | 0 | 1 | 0 |
| BEST100 | CTRL＋R0 | 1 | 0 | 0 | 0 | 0 |

元 build と各単独 build の差で、単独効果と組合せ効果を区別する。単独 build が陰性でも原因軸を否定しない。条件付き mode は、保存済み結果 JSON を入力し、巡回がある run から対象 cell と追加 build だけを生成する形にする。結果を見る前に表と生成規則を固定し、run ごとの再試行を恣意的に増やさない。

**brief との食い違い。** brief は mismatch を「版 object が読み手の生存中に再利用された」所見としているが、0 以外は再利用の**可能性を示す診断**であり、原因の断定はできない。また inline ABA の一部は mismatch が 0 のまま隠れる。

## 8. 起動器の変更点

**結論。** md_17 の repo 外起動器を写し、YCSB 専用の build spec と cell を追加する。既存の repo 内 patch・判定器・CCBench は変更しない。最初は `CICADA-BEST-L0` 一 job で build 束縛、inline R/W 件数、commit 数、判定器到達を確認し、その raw を見て `CICADA-BEST-J1-W1`〜`W4`、必要なら `CICADA-BEST-J2-SCALE` を複数ノードへ分ける。条件付き切り分けは `CICADA-BEST-FOCUS` とする。

| 雛形の位置 | 変更 |
|---|---|
| `launch_cicada_run.base-md17.py:32-61` | 五軸を build spec の値に移し、BEST・BEST100・CTRL・正例を登録。診断 patch は repo 外の明示パスと hash で管理 |
| `:63-113` | W1〜W4、tuple・thread・GC の明示 cell と L0/J1/J2/FOCUS job を登録。既存 TPCC job は写しで不要なら起動しない |
| `:114-128,353-408` | BEST/BEST100 の TRACE=0 比較に同じ CMake 値を二 checkout へ渡す |
| `:237-255,466-480` | BACK_OFF 重複除去、cache 期待値、三 TU の compile command 照合、binary sha256 を build record に追加 |
| `:483-506,845-937` | trace 行数・byte 数、inline 診断、mismatch、run 秒数、verifier 秒数、全 W の版順を記録 |
| `:940-1094` | stock と正例の合否を分け、各 run 後に JSON を保存。予算上限・J2 縮小判断を記録 |
| `:1151-1220` | 保存済み JSON を読む FOCUS mode と dry-run の build/cell 展開を追加 |

出力 JSON には少なくとも `repo_head`、pin、patch と launcher の sha256、build ごとの genome・CMake argv/cache・三 TU の `-D` 照合・binary sha256、run ごとの flags・raw path/hash・C/R/W/E 件数・inline R/W 件数・commit 数・mismatch・W 版順・verifier の verdict/integrity/cycles/witness・wall 秒、job Elapse と累積 node 秒を残す。失敗・timeout・未実行も空欄ではなく理由を持つ状態として残す。

**根拠。** 雛形は `:940-1094` で各 build と run を JSON に逐次保存し、`:1151-1220` に `CUSTOM` と dry-run の入口がある。既存の patch 全件走査や `orchestrator/tests/test_ccbench_spawn_sites.py` に波及させないため、診断 patch は repo の `patches/` に置かず、repo 外起動器から明示的に適用する。これは D2294 の「既存 instr patch bytes 不変」とも合う。親が適用 hunk・build・テストを実行して確定する。

**brief との食い違い。** 「repo への実装面差分ゼロ」は維持できる。ただし診断 patch を `patches/` に追加すると consumer の走査範囲が広がるため、使い捨て patch の置き場を repo 外に固定する。

## brief への異議

1. (P2) `trace_read_wts_` は「scan が版を選んだ時刻」ではなく `ReadElement` 構築時の再読値である。選択と構築の間の返却・再利用は静的に無視できない。
2. (P2) validation のポインタ比較は inline slot 再利用時に ABA になりうる。mismatch、巡回、orphan read のいずれも必ず出るわけではない。
3. (P1) 1M・t48・1秒を全条件の標準 cell にすると、trace と verifier の量を md_11 の無計装 throughput から見て過小評価する。まず一件で実測較正が要る。
4. (P3) 既定設定での壊し patch の巡回実績は BEST の検出力の代用にならない。同じ BEST cell で発火・帰属まで確認する。
5. (P4) TRACE=0 同一性は有用な追加証拠だが、この wave の巡回判定そのものの必要条件ではない。
6. 「BACK_OFF を後勝ちで上書き」は重複指定を残す。CMake cache と compile command が合っても、その指定手順は脆い。

## 総括

1. 段4では、inline 読みの scan→`ReadElement` 構築の窓とポインタ ABA を**未証明の観測限界**として一次資料に書くかを決める。
2. 診断は repo 外の重ね patch で commit 済み inline R/W 件数を数え、既存 instr patch の bytes を保つ。
3. BEST・BEST100・CTRL の五軸は build ごとに一意に指定し、cache と三 TU の `-D` で固定する。
4. 主検査は 200 tuple の t4/t48 とし、W4 は commit 数を確認して 1,000 tuple を加える。
5. 1M・t48 は L0/J1 の trace 量と verifier 秒数で投入可否を事前判定し、未実行なら限界に記す。
6. BEST の同一 cell で skip-read-recheck 正例の発火、巡回、witness 帰属を確認する。
7. mismatch は診断異常として保存し、再利用の機序を断定しない。巡回が出た設定は主比較から外す。
8. 追加の一軸 build は巡回が出た cell に限り、累積 job Elapse を 2 node 時間未満に保つ。