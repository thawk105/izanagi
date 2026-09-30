# CCBench 各 CC の実装前提 (実ソース確認版)

- 出所: 本 wave の読み取り専用の調査役 (Claude opus の子、file の最終更新 2026-09-30 12:21:33 JST) が書き、親が次の 5 点を実物で抜き取り照合して一致を確かめた: `include/ycsb.hh:97-113` (操作列を `begin()` の前に作る)、`include/procedure.hh:8-12` (YCSB の操作は 3 種)、`cc/mvto`・`cc/ss2pl`・`cc/oze` の `CMakeLists.txt:3` (WORKLOADS)、`cc/cicada/include/version.hh` の pending 版。他の行は子の読みのままで、親は 1 行ずつは確かめていない。
- 判定の子は CC の性質をこの表だけから引く (`definition.md` §6)。

- 対象: `external/ccbench` pin `68106660686232781bca3be792a750d3e19d7a8a` (worktree で `git rev-parse HEAD` 一致を確認)
- 行番号はすべてファイル実物の行 (`#line` 指令ではない)。パスは `external/ccbench/` からの相対。
- 判定 (どのカードが入るか) はしていない。コメントと実装が食い違う箇所は「食い違い」と明記した。
- build は一度も行っていない。「compile できない/するはず」という記述は読解による推定で、build 未確認である。

## 0. 1 行要約表

| CC | 版 | timestamp | 施錠 | validation | GC | YCSB 操作 | TPC-C 取引 | 事前 key 集合 |
|---|---|---|---|---|---|---|---|---|
| silo | 単版 | global epoch (leader が 40ms 毎に進める) + commit 時に TID 計算 (max(読/書 TID)+1, 自 TID+1, 現 epoch) | commit 時に write set を (storage,key) 順に sort して tuple の TID word の lock bit を CAS。既定は no-wait (即 abort) | read set の TID 一致 + 他者 lock なし + masstree node version | 削除 tuple のみ epoch-2 以前で free | READ / WRITE(blind) / RMW | 5 種 (NO/Pay/OS/Del/SL) | YCSB: 可 (pro_set_) / TPC-C: 不可 |
| tictoc | 単版 (直前 1 世代の timestamp 履歴 pre_tsw_ あり) | データ駆動 wts/rts (wts 47bit + delta 15bit)。commit_ts = max(読 wts, 書 rts+1)。epoch は GC 専用 | commit 時に sort して TsWord lock bit を CAS。既定 no-wait。read は lock 中なら preemptive abort 判定しつつ spin | read set の rts 延長 (CAS) / wts 変化時は履歴で救済 + node version | 削除 tuple のみ epoch-2 以前で free | READ / WRITE / RMW | 5 種 | YCSB: 可 / TPC-C: 不可 |
| mocc | 単版 | silo と同じ epoch + TID 計算 | tuple ごとの RW lock (counter)。高温 record は read/write 時に pessimistic lock、低温は commit 時に write lock。lock 取得は Tuple* アドレス順で、順序違反分は一旦解放。既定 RWLOCK・blocking spin | read set の TID 一致 + 他者 write lock なし + node version | 削除 tuple のみ epoch-2 以前で free | READ / WRITE / RMW | 5 種 | YCSB: 可 / TPC-C: 不可 |
| cicada | 多版 (新→旧の next_ 連結、pending 版) | thread local clock: (rdtscp 由来 localClock<<8)\|thid。abort 後は +1µs 相当の clockBoost。rts=MinWts-1 | lock なし。commit 時に pending 版を CAS で設置 (読み手は pending を spin 待ち) | precheck + 版設置 + rts 更新 + read set 可視版不変 + write 側 rts<=ts + node version。read-only は検証なし | MinRts 未満の版を回収し既定で再利用 (REUSE_VERSION=1) | READ / WRITE / RMW (全 READ 取引は read-only 経路) | 5 種 | YCSB: 可 / TPC-C: 不可 |
| ermia | 多版 (新→旧の prev_ 連結、inflight 版) | begin: txid = 全 thread の lastcstamp の max+1。commit: cstamp = ++Lsn (global atomic) | lock なし。update 時に即 CAS で inflight 版を設置 (first-updater-wins、先行 inflight 版には待つか abort)。commit は latch-free (ssn_parallel_commit) | SSN: pstamp < sstamp の排他検査 (操作毎にも早期検査) + node version | leader が閾値を決め、閾値未満の版・TMT 要素を再利用へ。削除 tuple も | READ / WRITE / RMW | 5 種 | YCSB: 可 / TPC-C: 不可 |
| si | 多版 (ermia と同形) | ermia と同じ (txid / ++Lsn) | ermia と同じ版設置 (first-updater-wins) | SSN 検査なし。node version のみ | ermia と同じ | READ / WRITE / RMW | 5 種 | YCSB: 可 / TPC-C: 不可 |
| mvto | 多版 (cicada 同形、pending 版) | cicada と同じ clock (clockBoost 変更なし) | lock なし。既定 (preserve_write=false) は commit 時に先頭へ CAS で設置。読み手は pending を spin 待ち | read set 可視版不変 + write 側 rts<=ts。node version (phantom) 検査なし | cicada 同形 (再利用なしで delete) | YCSB driver なし | 5 種 | YCSB なし / TPC-C: 不可 |
| ss2pl | 単版 | なし | tuple の RW lock (counter)。既定 DLR1 = no-wait (try lock 失敗で即 abort)。read 時 r_lock、update 時 w_lock または tryupgrade。commit 後に一括解放 | なし | なし (削除 tuple は gc_records_ に積むだけで free しない) | YCSB driver なし (ss2pl.cc は build 対象外の旧 main) | 5 種 | YCSB なし / TPC-C: 不可 |
| oze | 多版 (新→旧 next_、tuple ごとに依存グラフ graph_) | TxID = (epoch 32, thid 8, tid 24)。epoch は全 thread の最小。OCC モードは silo 型 TupleId | Oze モード: tuple の RW lock を w_lock して graph を操作する latch として使う。OCC モード: commit 時 sort → w_lock (blocking)。既定は常に Oze モード | Oze: 依存グラフの cycle 検査 (forwarding あり) + scan 履歴。OCC: silo 型 | 削除 tuple のみ epoch で free。グラフは epoch で gc。旧版の回収コードは見当たらず | READ / WRITE / RMW | 5 種 | YCSB: 可 / TPC-C: 不可 |
| d2pl | (対象外) | — | — | — | — | driver なし (sbomb / dbomb のみ) | driver なし | — |

共通事項 (全 CC):
- YCSB driver は共通の `YcsbWorkload` (include/ycsb.hh:86-213) で、操作は READ / WRITE / READ_MODIFY_WRITE の 3 種だけ (include/procedure.hh:8-12)。scan・insert・delete は YCSB driver から呼ばれない。
- TPC-C driver は共通の `TPCCWorkload` (include/tpcc.hh:28-132) で、9 CC すべてが同じ 5 取引を持つ。
- backoff は共通の `Backoff` (include/backoff.hh)。`BACK_OFF=1` が既定 (cmake/Options.cmake `CCBENCH_BACK_OFF 1`)。

---

## 共通部 (driver・backoff・build option)

### YCSB driver (include/ycsb.hh)
- flag: `ycsb_rmw=false` (blind write)、`ycsb_max_ope=10`、`ycsb_rratio=50`、`ycsb_tuple_num=1000000`、`ycsb_zipf_skew=0` (include/ycsb.hh:20-26)。
- `makeProcedure` (include/ycsb.hh:55-84): 各操作の key を zipf で、種別を rratio で決める。1 つの run 内の書き込みは `ycsb_rmw` により全部 RMW か全部 blind write のどちらか (70-74)。全操作が READ なら先頭要素に `ronly_=true` (78)。`#if KEY_SORT` なら `std::sort` (81-83)。
- `YcsbWorkload::run` (include/ycsb.hh:97-170): `makeProcedure(tx.pro_set_, ...)` を **RETRY ラベルより前** に呼ぶ (102、ラベル 108)。つまり abort 後の再試行は同じ操作列・同じ key 集合を再実行する。`tx.is_ronly_` を pro_set_ 先頭から設定 (106)。leader 判定 (109) → `tx.begin()` (113) → 各操作 (117-159)。操作後に `tx.status_ == aborted` なら `tx.abort()` して RETRY (149-156)。`tx.commit()` が false なら `tx.abort()` して RETRY (161-165)。
- READ は `tx.read`、WRITE は `tx.update` (blind)、RMW は `tx.read` の後に値を複写して `tx.update` (121-144)。
- `tx.read` の戻り値 Status は driver で見ていない (status_ だけ見る) (123-127)。

### TPC-C driver (include/tpcc.hh, include/tpcc/)
- 取引種別 enum: NewOrder, Payment, OrderStatus, Delivery, StockLevel (include/tpcc/tpcc_query.hh:19-25)。
- 既定比率: Payment 43, OrderStatus 4, Delivery 4, StockLevel 4 (残り 45 が NewOrder) (include/tpcc/tpcc_common.hh:6-11、閾値計算 include/tpcc/tpcc_query.hh:57-64)。`tpcc_num_wh=1` (tpcc_common.hh:6)、`tpcc_interactive_ms=0` (13)。
- 各取引が呼ぶ操作 (grep 集計): NewOrder = read/update/insert、Payment = read/update/insert、OrderStatus = read/scan、Delivery = read/update/scan/delete_record、StockLevel = read/scan (include/tpcc/tpcc_tx_*.hh)。
- `TPCCWorkload::run` (include/tpcc.hh:43-115): `query.generate` が **RETRY ラベルの後** にある (48-49)。abort 後の再試行は新しい query (別の取引・別の引数) になる。query は `run_new_order(tx, &query.new_order)` 等へ渡るだけで TxExecutor には渡らない (57-90)。`commit()` 失敗時に `status_ == invalid` なら再試行せず return (104)。
- TPC-C 用の header に CC 固有の `#if` はない (include/tpcc/ の `#if` は DEBUG / `#if 0` / FIXED_WAREHOUSE_PER_THREAD / GNUC のみ)。9 CC の tpcc_<cc>.cc はすべて `TPCCWorkload` を使う。

### runner (common/runner.hh)
- worker は `while (!quit) workload.run(trans)` (common/runner.hh:192-194)。`Backoff` は worker の stack に作り、cicada/ermia/mvto/oze/si は TxExecutor に渡し、silo/mocc/ss2pl/tictoc/d2pl は使わない (common/runner.hh:164-168, 179-183)。

### TxExecutor 契約
- 全 CC は `read / update / insert / delete_record / scan(2 種) / commit / abort` を持つことを concept で強制 (include/tx_executor_concept.hh:38-51)。したがって YCSB driver に無い操作も API としては全 CC にある。

### backoff (include/backoff.hh)
- `Backoff::backoff()` は大域値 `Backoff_` (µs) だけ `_mm_pause` で spin (94-108)。
- leader が 10µs 毎 (`check_update_backoff`, 37-42) に全 thread の commit 数から勾配を見て ±100µs、範囲 0〜1000µs で山登り調整 (44-92, 111-121)。
- abort 時の呼び方は CC ごとに下記。再試行そのものは driver の `goto RETRY`。

### build option (cmake/Options.cmake, 各 cc/<cc>/CMakeLists.txt)
- 全 CC 共通: `ADD_ANALYSIS=0`, `TRACE=0`, `BACK_OFF=1`, `KEY_SIZE=8`, `MASSTREE_USE=1`, `VAL_SIZE=4` (cmake/Options.cmake `ccbench_universal_definitions`)。
- `KEY_SORT` を渡すのは d2pl / ermia / mocc / si / ss2pl の CMakeLists だけ。silo / tictoc / cicada / oze には渡らず、`#if KEY_SORT` (include/ycsb.hh:81) は未定義 = 0 扱い。`CCBENCH_KEY_SORT` を 1 にしても silo/tictoc/cicada/oze の YCSB 操作列は sort されない。
- `PROCEDURE_SORT` と `PARTITION_TABLE` は cc/・include/・common/ のどこにも `#if` が無く、util.cc の表示にだけ出る (grep で `#if PROCEDURE_SORT` / `#if PARTITION_TABLE` の該当 0 件)。性質を変えない。
- 既定 macro を header で直接 `#define` している箇所はない (grep `define KEY_SORT|BACK_OFF|NO_WAIT|DLR|RWLOCK` 0 件)。

---

## silo (cc/silo/)

1. **版**: 単版。tuple は `Tidword tidword_` と `TupleBody body_` だけ (cc/silo/include/tuple.hh:33-37)。「(b) latest version の確認は単版なので省略」とコメント (cc/silo/transaction.cc:257-258)。
2. **timestamp**: 大域 `GlobalEpoch` (cc/silo/include/common.hh:19)。leader (thid 0) が `epoch_time=40`ms (common.hh:34) 経過かつ全 worker が現 epoch を読んだら +1 (cc/silo/util.cc:150-160)。worker は validation 中に `ThLocalEpoch` へ現 epoch を記録 (transaction.cc:441)。commit TID は writePhase で (a) read/write set の最大 TID+1、(b) 自分の直前 TID+1、(c) 現 epoch の最大 (transaction.cc:557-582)。
3. **施錠**: commit 時。write set を (storage, key) 順に sort (transaction.cc:408、比較子 cc/silo/include/silo_op_element.hh の `WriteElement::operator<`) → 各 tuple の Tidword の lock bit を CAS (transaction.cc:145-193)。lock の場所は tuple の word。既定 `NO_WAIT_LOCKING_IN_VALIDATION=1` で lock 済みなら即 abort (161-164)。`NO_WAIT_OF_TICTOC` は既定 0。両方 0 の場合、lock 済みを見ても `expected` を読み直さない spin になる (159-168、CAS 失敗時は `compareExchange` が expected を更新する: include/atomic_wrapper.hh:67-70)。deadlock は sort 順 + no-wait で回避。UPDATE 対象が absent なら abort (185-189)。
4. **validation**: read set の各 tuple の (epoch, tid) が読んだ時と同じか、他者に lock されていないか (自分の write set にあれば可) (transaction.cc:450-475)。masstree node version の不変 (478-485)。latest bit の検査はコメントアウト (463)。
5. **GC**: 版は無い。削除 tuple を `gc_records_` に積み、`ReclamationEpoch` (= 現 epoch-2、util.cc:157) 以前なら delete (transaction.cc:15-25, 686)。
6. **abort**: insert した tuple を index から外して delete、set を clear、`BACK_OFF` なら `Backoff::backoff` (transaction.cc:27-53)。validation 失敗時の unlock は validationPhase 内で済ませる (459, 471)。
7. **read**: 自分の read set → write set の順に探し、あれば自分の書いた値を返す (transaction.cc:211-220)。未 commit 値は読まない: lock bit が立っている間 spin し、値を複写後に TID word を読み直して一致するまで繰り返す (254-276)。
8. **driver**: ycsb_silo.cc / tpcc_silo.cc あり。CMake WORKLOADS = ycsb tpcc bomb sbomb (cc/silo/CMakeLists.txt:3)。YCSB 操作は共通 3 種。TPC-C は 5 取引。
9. **metadata**: `Tidword { lock:1, latest:1, absent:1, tid:29, epoch:32 }` (cc/silo/include/tuple.hh:12-22)。`Tuple { alignas(CACHE_LINE_SIZE) Tidword tidword_; TupleBody body_; }` (33-37)。ReadElement は読んだ Tidword と値の複写を持つ (silo_op_element.hh:8-35)。
10. **CMake**: `NO_WAIT_LOCKING_IN_VALIDATION=1`, `NO_WAIT_OF_TICTOC=0`, `SLEEP_READ_PHASE=0`, `WAL=0`, `PROCEDURE_SORT=0` (無効果), `PARTITION_TABLE=0` (無効果) (cc/silo/CMakeLists.txt:5-12, cmake/Options.cmake)。KEY_SORT は渡らない。
11. 該当なし。
12. YCSB では `pro_set_` が TxExecutor のメンバ (cc/silo/include/transaction.hh:37) で、`begin()` 前に埋まる。silo の transaction.cc は pro_set_ を読まない。TPC-C は不可 (共通部参照)。

---

## tictoc (cc/tictoc/)

1. **版**: 単版。ただし `pre_tsw_` に直前の TsWord を残す (timestamp history) (cc/tictoc/include/tuple.hh:41-45、書き込み transaction.cc:508-511)。値の旧版は持たない。
2. **timestamp**: tuple ごとの `wts` (47bit) と `delta` (15bit)、`rts = wts + delta` (tuple.hh:12-38)。commit_ts は read set の wts の最大 (transaction.cc:367) と write set の rts+1 の最大 (645) の max。rts 延長は CAS、delta 溢れ時は wts をずらす (431-446)。`appro_commit_ts_` を read/update 時に更新 (160, 241)。GlobalEpoch は GC 用だけで、leader が `gc_epoch_time=40`ms 毎に進める (cc/tictoc/util.cc:142-152, cc/tictoc/include/common.hh:35)。begin で ThLocalEpoch を更新 (transaction.cc:43)。
3. **施錠**: commit 時。write set を (storage,key) で sort (transaction.cc:554) → TsWord の lock bit を CAS (556-647)。既定 `NO_WAIT_LOCKING_IN_VALIDATION=1` で即 abort (564-573)。条件 `is_wonly_ == false` (563) の `is_wonly_` はどこでも true にされない (宣言 cc/tictoc/include/transaction.hh:46 のみ、grep 1 件) ので常に真。両 flag 0 なら読み直して spin 待ち (626)。
4. **validation**: read set の rts が commit_ts 未満なら、wts が変わっていれば TIMESTAMP_HISTORY で `pre_tsw_.wts <= commit_ts < 現 wts` なら救済、でなければ abort (transaction.cc:377-407)。他者 lock 中で rts 延長が必要なら abort (409-423)。自分が書く tuple なら延長を writePhase に任せる (429)。node version (454-461)。
5. **GC**: 削除 tuple のみ、削除時の ThLocalEpoch が ReclamationEpoch 以下なら delete (transaction.cc:518-526, 692-702)。
6. **abort**: insert 分を外し、gc、clear、`BACK_OFF` なら backoff (transaction.cc:468-497)。backoff の計測行は `++result_->local_backoff_latency_ += ...` (493) だが ADD_ANALYSIS=0 では消える。
7. **read**: read set → write set の順に自分の値を返す (transaction.cc:85-94)。lock 中は `PREEMPTIVE_ABORTS` で `rts < appro_commit_ts_` なら即 abort、それ以外は読み直し spin (128-139)。値複写後に TsWord 再確認 (146-150)。未 commit 値は読まない。
8. **driver**: ycsb / tpcc / bomb / sbomb (cc/tictoc/CMakeLists.txt:3)。
9. **metadata**: `TsWord { lock:1, absent:1, delta:15, wts:47 }` (pack 1) (tuple.hh:12-38)。`Tuple { alignas(CACHE_LINE_SIZE) TsWord tsw_; TsWord pre_tsw_; TupleBody body_; }` (41-45)。SetElement は読んだ TsWord を持つ (cc/tictoc/include/tictoc_op_element.hh:6-35)。
10. **CMake**: `NO_WAIT_LOCKING_IN_VALIDATION=1`, `NO_WAIT_OF_TICTOC=0`, `PREEMPTIVE_ABORTS=1`, `TIMESTAMP_HISTORY=1`, `SLEEP_READ_PHASE=0`, `PARTITION_TABLE=0` (無効果) (cc/tictoc/CMakeLists.txt:5-10)。
11. 該当なし。
12. pro_set_ メンバあり (cc/tictoc/include/transaction.hh:47)、CC 側では未使用。

---

## mocc (cc/mocc/)

1. **版**: 単版。
2. **timestamp**: silo と同じ epoch + TID 計算 (cc/mocc/transaction.cc:1140-1157、leader cc/mocc/util.cc:196-206)。ThLocalEpoch は validation 中に記録 (1029-1030)。
3. **施錠**: tuple ごとの `ReaderWriterLock rwlock_` (int counter、-1=write) (cc/mocc/include/tuple.hh:64-67, cc/mocc/include/lock.hh:137-139)。温度 `epotemp_.temp` が `temp_threshold=10` (cc/mocc/include/common.hh:40) 以上の record は read 時に read lock (transaction.cc:297-315)、update/delete 時に write lock (460, 567)。前回 abort 時に作った RLL にある record も事前 lock (281-296, 474, 581)。commit 時は write set を Tuple* アドレス順に sort (997、比較子 cc/mocc/include/mocc_op_element.hh:48-50) し全件 write lock (1016-1026)。`lock()` (721-901) は CLL (現保持 lock 列) をアドレス順に保ち、要求より大きいアドレスの保持 lock (順序違反) を解放してから RLL の間の分を取り直し、最後に対象を **blocking spin** で取る (835-891; `r_lock`/`w_lock` は cc/mocc/lock.cc:933-981)。「違反が多すぎる」条件は `vioctr > 100` の try-lock 分岐で、コメントは「test condition. mustn't enter」(766-771)。deadlock はアドレス順の取得で回避する設計。既定は `RWLOCK` (cc/mocc/CMakeLists.txt:5)。MQLOCK 分岐は既定では compile されない。
4. **validation**: read set の (epoch,tid) 一致 (transaction.cc:1033-1045)、他者が write lock 中でないか (自分の write set は可) (1048-1061)、node version (1067-1073)。
5. **GC**: 削除 tuple のみ epoch で free (transaction.cc:1297-1307)。
6. **abort**: insert 分を外す → `unlockCLL` → `construct_RLL` (今回の write set を W、検証失敗した read と高温 read を R として RLL に登録し、検証失敗 record の温度を確率 1/2^temp で +1、TEMPERATURE_RESET_OPT なら epoch 変化で温度 0 に戻す) → gc → clear → backoff (transaction.cc:1084-1117, 903-985)。
7. **read**: read set → write set で自分の値 (transaction.cc:223-232)。低温 record は OCC 読み: write lock 中は、保持 lock の末尾より小さいアドレスなら abort、でなければ spin (323-340)、値複写後 TID 再確認 (347-355)。高温・RLL 由来は read lock を取って読む (357-364)。未 commit 値は読まない。
8. **driver**: ycsb / tpcc / bomb / sbomb (cc/mocc/CMakeLists.txt:3)。
9. **metadata**: `Tidword { absent:1, tid:31, epoch:32 }` (lock bit なし) (tuple.hh:14-22)。`Epotemp { temp:32, epoch:32 }` を独立 cache line に (34-57)。`Tuple { alignas(CACHE_LINE_SIZE) Tidword tidword_; Epotemp epotemp_; TupleBody body_; ReaderWriterLock rwlock_; }` (59-70)。ReadElement に `failed_verification_` (mocc_op_element.hh:17)。
10. **CMake**: `RWLOCK` (定義のみ)、`TEMPERATURE_RESET_OPT=1`、`KEY_SORT=0` (cc/mocc/CMakeLists.txt:5-9)。
11. 観察 (依頼外、実物): read_internal の abort 経路 `read_set_.emplace_back(key, tuple)` (transaction.cc:334) は key が `std::string_view` なので、`ReadElement(uint64_t, T*)` (mocc_op_element.hh:26-28、`failed_verification_=true`) ではなく継承した `OpElement(std::string_view, T*)` (include/op_element.hh:28) が選ばれ、`failed_verification_` と `storage_` が未初期化になると読める (C++ の多重定義解決による読解、実行未確認)。abort 時の温度加算 (918) がこの要素で意図どおり動くかは未確認。
12. pro_set_ メンバあり (cc/mocc/include/transaction.hh:33)、CC 側では未使用。

---

## cicada (cc/cicada/)

1. **版**: 多版。`Tuple::latest_` から `Version::next_` で新→旧に連結 (cc/cicada/include/tuple.hh:30, cc/cicada/include/version.hh:25-30)。版状態 pending/aborted/committed/deleted/unused 等 (version.hh:15-23)。古い版を読む経路: `ts` より wts が大きい版を飛ばし、committed/deleted まで進む (cc/cicada/transaction.cc:102-118)。版の設置: validation で pending 版を `latest_` または途中の `next_` へ CAS (481-531)。INLINE_VERSION_OPT=0 が既定なので inline 版なし。
2. **timestamp**: thread local clock。`ts_ = (localClock_ << 8) | thid` (cc/cicada/include/time_stamp.hh:24-40)。begin で `generateTimeStamp` (transaction.cc:39)。abort 後は `clockBoost_ = clocks_per_us` (760)、commit 後 0 に戻す (910)。read-only 用 `rts_ = MinWts - 1` (42)。MinWts/MinRts は leader が全 thread の GCFlag が立ったときに全 thread の wts/rts の最小を取る (cc/cicada/util.cc:281-324)。
3. **施錠**: lock なし。pending 版の設置が事実上の書き込み予約で、読み手は pending を spin で待つ (transaction.cc:113, 553-559, 579-586)。
4. **validation**: (i) precheck: write set の前半を partial_sort し、`continuing_commit_ < 5` の record だけ最新版の wts/rts が自 ts を超えないか見る (cc/cicada/include/transaction.hh:247-293)、(ii) pending 版設置 (transaction.cc:481-531)、(iii) read set の版の rts を自 ts まで CAS で上げる (536、transaction.hh:295-307)、(iv) read set の各 key で今見える版が読んだ版と同じか (543-570)、(v) write set の直前の committed 版の rts が自 ts 以下で deleted でないか (576-593)、(vi) node version (596-602)。read-only 取引 (`is_ronly_`) は検証せず commit (934-937)。
   - 食い違い: precheck のコメントは「Sort write set by contention」「recent 5 commits なら両 step を省く」(transaction.hh:248-253) だが、実装の sort 比較子は (storage, key) 順 (cc/cicada/include/cicada_op_element.hh:53-57) で、contention 順ではない。省略も record 単位の `continuing_commit_` 判定 (266-267) で、partial_sort は常に行う。
5. **GC**: commit した版を `gcq_` に積み、`MinRts` 未満になったら tuple の `gc_lock_` を取り、その版より古い版を切り離して回収 (transaction.cc:806-843)。`REUSE_VERSION=1` 既定で再利用列へ (transaction.hh:185-186)。削除 tuple も MinRts で free (845-857)。mainte は commit 後と abort 後に呼ぶ (954, 767)、間隔 `gc_inter_us=10` (cc/cicada/include/common.hh:42)。
6. **abort**: insert 分を外す、設置済み pending 版を aborted に、未設置版を再利用へ (transaction.hh:343-368)、clockBoost、mainte、`BACK_OFF` なら backoff (transaction.cc:745-773)。
7. **read**: read set → write set (自分の新版) の順 (transaction.cc:156-165)。未 commit 値は読まない (pending は待つ)。
8. **driver**: ycsb / tpcc / bomb / sbomb (cc/cicada/CMakeLists.txt:3)。YCSB で全操作 READ の取引は read-only 経路になる (include/ycsb.hh:78, 106 → transaction.cc:93-94, 934)。TPC-C では `is_ronly_` を立てる箇所がない (grep で cicada 内 is_ronly_ の代入は transaction.hh:209 の inline 昇格だけ)。
9. **metadata**: `Tuple { [inline_ver_ if INLINE_VERSION_OPT]; atomic<Version*> latest_; atomic<uint64_t> min_wts_; atomic<uint64_t> continuing_commit_; atomic<uint8_t> gc_lock_; TupleBody body_; }` (tuple.hh:24-34)。`Version { alignas(CACHE_LINE_SIZE) atomic<uint64_t> rts_; atomic<uint64_t> wts_; atomic<Version*> next_; atomic<VersionStatus> status_; TupleBody body_; }` (version.hh:25-32 付近)。
10. **CMake**: `INLINE_VERSION_OPT=0` (cicada 専用 cache 変数)、`INLINE_VERSION_PROMOTION=1` (OPT=0 なので無効)、`REUSE_VERSION=1`、`SINGLE_EXEC=0`、`WRITE_LATEST_ONLY=0`、`WORKER1_INSERT_DELAY_RPHASE=0` (cc/cicada/CMakeLists.txt:5-13, cmake/Options.cmake)。gflags: `group_commit=0`、`pre_reserve_version=10000` (common.hh:43, 50)。
11. 観察: `INLINE_VERSION_OPT=1 && INLINE_VERSION_PROMOTION=1` のときだけ入る `inlineVersionPromotion` が存在しない `write(...)` を呼ぶ (transaction.hh:207、cicada 内に `write` の定義なし)。既定では compile されないが、OPT=1 で build が通るかは未確認。
12. pro_set_ メンバあり (transaction.hh:48)。CC は `is_ronly_` (pro_set_ 由来) だけ使う。

---

## ermia (cc/ermia/)

1. **版**: 多版。`Tuple::latest_` から `Version::prev_` で新→旧 (cc/ermia/include/tuple.hh:11, cc/ermia/include/version.hh:92-99)。古い版を読む経路: committed/deleted でない版、または `cstamp > txid_` の版を飛ばす (cc/ermia/transaction.cc:152-158)。設置: update/delete 時に即 `install_version` で `latest_` を CAS (177-223, 294, 420)。
2. **timestamp**: begin で `txid_ = max(全 thread の TMT.lastcstamp) + 1` (transaction.cc:67-72)。commit 時 `cstamp_ = ++Lsn` (602、`Lsn` は大域 atomic cc/ermia/include/common.hh:20)。版の cstamp_ は inflight 中は書き手の txid、commit で cstamp (290-291, 765)。
3. **施錠**: tuple lock なし。`install_version` で先頭が inflight の場合、自 txid <= その版の cstamp (=書き手 txid) なら abort、そうでなければ読み直して待つ (spin) (183-195)。committed 最新版の cstamp が自 txid より新しければ abort (first-updater-wins) (198-214)。commit は latch-free の `ssn_parallel_commit` (906)。直列版 `ssn_commit` (大域 mutex `SsnLock` を使う、503-589) は定義のみで呼ばれない (grep で呼び出し 0 件)。
4. **validation**: SSN。read で読んだ版の sstamp から自 sstamp を下げ (160-168)、書きで上書きした版の pstamp から自 pstamp を上げ (309-310)、各操作後に `pstamp >= sstamp` なら早期 abort (171, 314, 855-861)。commit で sstamp の確定 (他 thread が committing なら cstamp 確定まで spin 待ち) (611-652)、readers bitmap から pstamp 確定 (657-704)、`pstamp < sstamp` なら commit (710-718)、node version (721-728)。
5. **GC**: leader が全 thread の txid 範囲から閾値を決め (transaction.cc:918-922, cc/ermia/garbage_collection.cc:16-49, cc/ermia/include/garbage_collection.hh:48-55)、worker が `gc_inter_us=10` 毎の mainte で閾値未満の版を再利用列へ、TMT 要素も再利用、削除 tuple は `MinQueuedCstamp` の guard 付きで free (transaction.cc:863-886, garbage_collection.cc:53-162)。mainte は commit 後のみ (912)。
6. **abort**: 上書き先版の sstamp 印を戻す、insert 分を外す、自版を aborted に、readers bit を下げる、`BACK_OFF` なら backoff (transaction.cc:809-853)。
7. **read**: read set → write set (DELETE なら NOT_FOUND) (transaction.cc:100-113)。inflight 版は飛ばして committed を読む (待たない) (152-158)。update 時は read set から当該要素を消す (「avoid false positive」) (246-256)。
8. **driver**: ycsb / tpcc / bomb / sbomb (cc/ermia/CMakeLists.txt:3)。
9. **metadata**: `Tuple { alignas(CACHE_LINE_SIZE) atomic<Version*> latest_; atomic<uint32_t> min_cstamp_; atomic<uint8_t> gc_lock_; TupleBody body_; }` (tuple.hh:9-15)。`Psstamp { pstamp_:32, sstamp_:32 }` の 64bit union (version.hh:18-27)。`Version { alignas(CACHE_LINE_SIZE) Psstamp psstamp_; Version* prev_; atomic<uint64_t> readers_; atomic<uint32_t> cstamp_; atomic<VersionStatus> status_; TupleBody body_; }` (version.hh:92-101)。sstamp の最下位 bit が TID flag (`TIDFLAG 1`, version.hh:9; tuple.hh:32-33 のコメント)。TMT `TransactionTable { txid_, cstamp_, sstamp_, lastcstamp_, status_ }` (cc/ermia/include/transaction_table.hh:9-15)。status に `committing` (cc/ermia/include/transaction_status.hh:5-10)。
10. **CMake**: `KEY_SORT=0` のみ (cc/ermia/CMakeLists.txt:5)。gflags `gc_inter_us=10`, `pre_reserve_version=10000` (common.hh:36, 42)。
11. **既知の注意の実物確認**:
    - (a) `cstamp << 1`: `ssn_commit()` 内で `verCstamp = cstamp_; verCstamp <<= 1; &= ~1` を版の `cstamp_` に書く (transaction.cc:553-555, 561)。`verSstamp` も同様 (549-551)。**ただし `ssn_commit()` は呼ばれない** (commit は `ssn_parallel_commit()`、906)。実際に動く経路では版の cstamp_ は shift なしで書く (765)。対になる `verCstamp >> 1` は `naiveGarbageCollection` (cc/ermia/util.cc:179, 204) にあるが、これも呼び出し 0 件 (宣言 cc/ermia/include/util.hh:15 のみ)。書き込み型は `uint64_t` を `atomic<uint32_t>` へ代入 (561)。
    - (a) readers bitmap: `upReadersBits` / `downReadersBits` が `expected | (1 << thid_)` / `& ~(1 << thid_)` (cc/ermia/include/transaction.hh:123, 134)。`1` は int、`thid_` は uint8_t (30) で int に昇格するので **int の shift**。`readers_` は `atomic<uint64_t>` (version.hh:97)。一方、読む側 `ssn_parallel_commit` は `uint64_t one = 1; one << worker` (transaction.cc:657, 670)。thid が 31 以上で書き側と読み側が食い違う (32 以上は未定義動作)。
12. pro_set_ メンバあり (transaction.hh:42)、CC 側では未使用。

---

## si (cc/si/)

1. **版**: 多版、ermia と同じ構造 (cc/si/include/tuple.hh:9-15, cc/si/include/version.hh:92-101)。読む経路・設置も同じ (cc/si/transaction.cc:153-159, 170-216)。
2. **timestamp**: ermia と同じ。begin の txid (transaction.cc:68-73)、commit の `cstamp_ = ++Lsn` (479)。
3. **施錠**: ermia と同じ first-updater-wins の版設置 (transaction.cc:176-207)。lock なし。
4. **validation**: node version だけ (transaction.cc:485-492)。コメントどおり SSN 検査はない (463-470)。`verify_exclusion_or_abort` は空 (614-616)。
5. **GC**: ermia と同じ (transaction.cc:618-634, cc/si/garbage_collection.cc)。
6. **abort**: insert 分を外す、自版を aborted に、readers bit を下げる、backoff (transaction.cc:578-612)。ermia と違い、上書き先版の sstamp を戻す処理はない (SI の update / delete_record は sstamp に印を付けない: cc/si/transaction.cc:223-299, 348-409 に sstamp 書き込みなし)。
7. **read**: ermia と同じ (read set → write set、inflight 版は飛ばす) (transaction.cc:101-114, 153-159)。update 時に read set から当該要素を消す (239-249)。
8. **driver**: ycsb / tpcc / bomb / sbomb (cc/si/CMakeLists.txt:3)。
9. **metadata**: ermia と同じ (Psstamp・readers_ も持つが SI の commit 判定では使わない)。
10. **CMake**: `KEY_SORT=0` (cc/si/CMakeLists.txt:5)。
11. 参考: readers bitmap の int shift は si にもある (cc/si/include/transaction.hh:121, 132)。si では bitmap を読む処理がないので判定には効かない。
12. pro_set_ メンバあり、CC 側では未使用。

---

## mvto (cc/mvto/)

1. **版**: 多版、cicada と同形 (`latest_` → `next_`、pending/aborted/committed/deleted) (cc/mvto/include/tuple.hh:24-29, cc/mvto/include/version.hh:15-29)。古い版を読む経路 `get_latest_previous_version`: `wts >= 基準` を飛ばし、pending は spin 待ち、aborted は飛ばす (cc/mvto/include/transaction.hh:178-195)。設置: `install_version` は `latest_` の先頭へ無条件に CAS で積む (wts 順の位置探しはしない) (transaction.hh:161-171)。既定 `preserve_write=false` (cc/mvto/include/common.hh:49) では validation の冒頭で設置 (cc/mvto/transaction.cc:282-287)、true なら update 時に設置 (142, 212)。
2. **timestamp**: cicada と同じ TimeStamp (cc/mvto/include/time_stamp.hh:19-35)。begin で wts 生成、`rts_ = MinWts - 1` (transaction.cc:28-38)。`clockBoost_` を変更する箇所なし (grep: time_stamp.hh の宣言と加算のみ)。
3. **施錠**: lock なし。読み時に版の rts を CAS で上げる (transaction.cc:52、transaction.hh:197-206)。
4. **validation**: read set の各 key で今見える版が読んだ版と同じか (transaction.cc:294-306)、write set の直前版の rts <= 自 wts かつ deleted でない (312-320)。**node version による phantom 検査なし** (scan は callback なしで呼ぶ: 236-239、TxExecutor に node_map_ なし)。read-only は検証なし (465-467)。
5. **GC**: cicada 同形。MinRts 未満の版を delete (再利用なし) (transaction.cc:358-395, transaction.hh:140-151)、削除 tuple も (397-409)。maintenance は commit 後と abort 後 (482, 352)。
6. **abort**: insert 分を外し、設置済み版を aborted に (transaction.hh:242-254)、maintenance、`BACK_OFF` なら backoff (transaction.cc:350-356)。
7. **read**: read set → write set (自分の新版) (transaction.cc:77-86)。pending は待つので未 commit 値は読まない。
8. **driver**: **ycsb_mvto.cc は無い** (cc/mvto/ のファイルは bomb_mvto.cc, tpcc_mvto.cc, transaction.cc, util.cc と include/)。CMake WORKLOADS = bomb tpcc (cc/mvto/CMakeLists.txt:3)。TPC-C は 5 取引。
9. **metadata**: `Tuple { alignas(CACHE_LINE_SIZE) atomic<Version*> latest_; atomic<uint64_t> min_wts_; atomic<uint8_t> gc_lock_; TupleBody body_; }` (tuple.hh:24-29)。`Version { alignas(CACHE_LINE_SIZE) atomic<uint64_t> rts_; atomic<uint64_t> wts_; atomic<Version*> next_; atomic<VersionStatus> status_; TupleBody body_; }` (version.hh:22-29)。
10. **CMake**: INSERT_*_DELAY_MS (既定未設定) のみ (cc/mvto/CMakeLists.txt:5-6)。gflags `preserve_write=false`, `gc_inter_us=10` (common.hh:42, 49)。
11. (d) 確認: mvto に YCSB 版は無い (上記 8)。
12. pro_set_ メンバあり (transaction.hh:41)。YCSB driver が無いので実際には埋まらない。TPC-C は不可。

---

## ss2pl (cc/ss2pl/)

1. **版**: 単版。`Tuple { alignas(CACHE_LINE_SIZE) ReaderWriteLock lock_; TupleBody body_; }` (cc/ss2pl/include/tuple.hh:13-16)。
2. **timestamp**: なし (begin は status を inflight にするだけ、cc/ss2pl/transaction.cc:120)。
3. **施錠**: tuple 内の RW lock (int counter、-1 = write) (include/rwlock.hh:8-109)。既定 `DLR1` (cc/ss2pl/CMakeLists.txt:5) = no-wait: read は `r_trylock` 失敗で abort (transaction.cc:178-187)、update は read 済みなら `tryupgrade` (upgrade は reader が自分 1 人のときだけ成功) (260-296)、未読なら `w_trylock` (314-321)。insert は新 tuple を w_lock 済みで作る (tuple.hh:25-28, transaction.cc:350-360)。deadlock は no-wait で回避。書き込みは write set に buffer し commit で反映 (77-99)、その後一括解放 (104, 454-466)。`DLR0` を定義すれば blocking 版 (172-177, 309-313)。
4. **validation**: なし。
5. **GC**: 削除 tuple を `gc_records_` に積むが free する箇所はない (grep: transaction.cc:93 の push と宣言のみ)。
6. **abort**: 全 lock 解放、set を clear、`BACK_OFF` なら backoff (transaction.cc:44-70)。
7. **read**: read set → write set で自分の値 (transaction.cc:136-145)。read lock を取ってから値を複写するので未 commit 値は読まない (178-193)。
8. **driver**: CMake WORKLOADS = bomb tpcc (cc/ss2pl/CMakeLists.txt:3)。**YCSB の build 対象はない**。TPC-C は 5 取引。
9. **metadata**: 上記 1。lock list `r_lock_list_` / `w_lock_list_` は TxExecutor 側 (cc/ss2pl/include/transaction.hh:28-29)。
10. **CMake**: `DLR1` (定義のみ)、`KEY_SORT=0` (cc/ss2pl/CMakeLists.txt:5-6)。
11. **(c) ss2pl に YCSB 版があるか**: 無い。cc/ss2pl/ss2pl.cc は旧形式の単独 main (YCSB 風の worker、cc/ss2pl/ss2pl.cc:34-92) だが、
    - CMake は `W_ss2pl.cc` (W = bomb, tpcc) しか build しない (cmake/ProtocolHelpers.cmake:32-34, cc/ss2pl/CMakeLists.txt:3)。ss2pl.cc はどの target にも入らない。
    - 現行 API と食い違う: `TxExecutor trans(thid, &myres)` (ss2pl.cc:38) に対し ctor は 3 引数 (include/transaction.hh:43)。`trans.update(key)` (ss2pl.cc:69) に対し uint64_t 版 update の宣言なし (transaction.hh:73 は Storage 版のみ)。`trans.read(key)` / `trans.readWrite(key)` は uint64_t 版の宣言 (transaction.hh:60, 72, 75) はあるが transaction.cc に定義がない。`makeProcedure` 12 引数呼び出し (ss2pl.cc:56-58) に対し現行 include/ycsb.hh:55 は 3 引数、旧版は include/util.hh:111, 165 でコメントアウト。
    - よって「読んだ限り build されず、build しても compile が通らない旧コード」。build は試していない。
    - cc/ss2pl/test/CMakeLists.txt (gtest) も top CMake から add_subdirectory されていない (grep 0 件)。
    - 観察 (依頼外、実物): `delete_record` は lock を取らずに write set へ積む (transaction.cc:368-391)。`abort()` は insert した tuple を index から外さない (44-70; 他 CC は外す)。scan は node version 検査なし (213-216)。TPC-C の Delivery (delete) と NewOrder/Payment (insert) で効く可能性があるが影響は未確認。
12. pro_set_ メンバあり (transaction.hh:35)、現行 build では埋まらない。

---

## oze (cc/oze/)

1. **版**: 多版。`latest_` → `next_` (新→旧)、状態 pending/deleting/aborted/committed/deleted 等 (cc/oze/include/version.hh:15-32)。版に timestamp は無く、書き手の `TxID` を持つ (version.hh:28)。tuple ごとに依存グラフ `Graph graph_` (TxID → TxNode、readBy/writtenBy/from の辺) と `version_index_` (cc/oze/include/tuple.hh:38-47, cc/oze/include/oze.hh:30-50)。古い版を読む経路 (Oze モード): 先頭から committed/deleted まで進み、途中の pending/deleting 版は「follower」として反依存辺を張って飛ばす (待たない) (cc/oze/include/transaction.hh:434-467, 502-634)。読む版で cycle ができれば 1 つ古い版に移って再試行 (581-629)。OCC モードは pending を spin 待ち (688-723)。設置: Oze モードは write_validation 中に `insert_version` で先頭、または forwarding 時は follower の後ろへ挿入 (cc/oze/transaction.cc:758、transaction.hh:1040-1066)。OCC モードは writePhase で設置 (transaction.cc:1098-1105)。
2. **timestamp**: `TxID { tid:24, thid:8, epoch:32 }` (cc/oze/include/txid.hh:5-14)。begin で全 thread の epoch の最小を自 epoch に、epoch が同じなら tid++ (transaction.cc:36-43, transaction.hh:867-874)。大域 epoch は leader が `epoch_time=40`ms 毎に進める (cc/oze/util.cc:70-81, cc/oze/include/common.hh:41)。OCC モード用に silo 型 `TupleId { tid:32, epoch:32 }` (tuple.hh:20-36) と `decide_tuple_id` (transaction.hh:1125-1143)。
3. **施錠**: tuple ごとの `RWLock lock_` (cc/oze/include/lock.hh:8-, tuple.hh:41)。Oze モードでは read (transaction.cc:148-191)・write_validation (698-795)・insert_validation (812-869)・read-only 検証 (554-565) の間、graph 操作の latch として w_lock する (取引をまたいで保持しない)。OCC モードは write set を sort (1027) して `lock_write_set` で blocking w_lock (transaction.hh:1091-1109)、writePhase で解放 (transaction.cc:1104)。
4. **validation**: Oze モード: write/delete ごとに tuple の graph に自分と reader の辺を足し cycle なら forwarding (版を follower の後ろに入れる) を試し、なお cycle なら abort (transaction.cc:684-800)。read した tuple 群へ伝播して cycle 検査 (877-、593-606)。insert は epoch ごとの scan 履歴と照合 (802-875)。read-only 取引は読んだ tuple ごとにグラフを merge して cycle 検査 (552-567)。`validation_th_num>1` なら std::thread を起こして並列検証 (608-630、既定 1)。他 thread が OCC モードなら追加で OCC 検証 (1140-1141)。OCC モード: silo 型 (1024-1067)。
5. **GC**: 削除 tuple を epoch で free (transaction.cc:1069-1079)。グラフは write_validation / read_validation で `gc(graph, reclamation_epoch_)` (705, 901、transaction.hh:889-)。scan 履歴は insert_validation で古い epoch 分を削除 (844-860)。**旧版を回収するコードは見当たらない** (grep で `delete` の対象は tuple・ScanEntry・abort 時の insert 版だけ: transaction.cc:301, 322, 848, 856, 1076, transaction.hh:215-216)。
6. **abort**: 版を aborted に、insert 分は index から外して delete (transaction.hh:209-220)、各 set とグラフを clear、mainte、`BACK_OFF` なら backoff (transaction.cc:987-1022)。
7. **read**: read set → write set (自分の新版) (transaction.cc:84-93)。未 commit 値は返さない (committed/deleted の版だけ返す)。Oze モードは pending を待たず飛ばす。
8. **driver**: ycsb / tpcc / bomb (sbomb なし) (cc/oze/CMakeLists.txt:3)。
9. **metadata**: `Tuple { alignas(CACHE_LINE_SIZE) TupleId tuple_id_; RWLock lock_; atomic<Version*> latest_; TupleBody body_; Graph graph_; std::map<uint64_t, vector<Version*>> version_index_; }` (tuple.hh:38-47)。`Version { TxID txid_; atomic<Version*> next_; atomic<VersionStatus> status_; TupleBody body_; }` (version.hh:26-32)。`TxNode { id_, status_, is_aborted, readSet_, writeSet_, readBy_, writtenBy_, from_ }` (oze.hh:30-44)。
10. **CMake**: `INLINE_VERSION_OPT=1`、`INLINE_VERSION_PROMOTION=1`、`REUSE_VERSION=1`、`SINGLE_EXEC=0`、`WRITE_LATEST_ONLY=0`、`PARTITION_TABLE=0`、`MERGE_ON_READ=0`、`DEBUG_MSG=0` (cc/oze/CMakeLists.txt:5-12)。このうち oze のソースで `#if` に使われるのは `MERGE_ON_READ` (transaction.cc:182) と `DEBUG_MSG` だけで、INLINE_VERSION_* は grep 0 件、REUSE_VERSION / SINGLE_EXEC / WRITE_LATEST_ONLY / PARTITION_TABLE は util.cc の表示だけ (util.cc:86-90)。`WAIT_PENDING_VERSION` / `NAIVE_VERSION_SELECTION` / `USE_FIRST_READ_EPOCH` / `SYNC_GRAPH_AGGRESSIVELY` / `GC_ABORTED_TX` / `ORDERED_MAPSET` は CMake で定義されない (grep 0 件) ので既定経路は「pending を待たない」「最新から探索」。gflags: `forwarding=true`, `validation_threshold=100`, `validation_th_num=1`, `cc_mode=OZE_MODE(2)` (common.hh:53-57)。
11. **(b) protocol 切替判定が常に false の TODO**: 確認。`should_switch_to_occ()` と `should_switch_to_oze()` は本体が `// TODO: implement` とコメントアウトされた条件で、`return false;` のみ (cc/oze/include/transaction.hh:1157-1171)。初期モードは `FLAGS_cc_mode` (既定 `DEFAULT_CC_MODE = OZE_MODE`、cc/oze/include/cc_mode.hh:9, common.hh:57) を各 thread に設定 (util.cc:39)。全 thread が OZE なら `get_next_cc_mode` は常に OZE を返す (transaction.hh:1181-1182)。よって既定では常に Oze モードで、OCC 経路は `--cc_mode=1` を与えたときだけ動く (その場合も OCC のまま切り替わらない、1178-1179)。
    - 観察 (依頼外、実物): `isLeader()` は `thid_ == 1` (transaction.cc:1164)。他 CC は 0。一方 `epoch_timer_start_` を初期化するのは thid 0 だけ (cc/oze/ycsb_oze.cc:47, tpcc_oze.cc:54) で、ctor でも初期化しない (transaction.hh:74-82)。leader (thid 1) の最初の epoch 判定は未初期化値との比較になると読める。thread 数 1 なら leader が存在せず epoch も backoff も更新されない。いずれも実行未確認。
12. pro_set_ メンバあり (transaction.hh:40)、CC 側では未使用。

---

## d2pl (cc/d2pl/)

- driver は sbomb / dbomb のみ (cc/d2pl/CMakeLists.txt:3、ファイル dbomb_d2pl.cc, sbomb_d2pl.cc)。ycsb / tpcc の driver は無い。
- 参考: tuple RW lock (include/rwlock.hh を include、cc/d2pl/include/transaction.hh:10, 28-29)、`lockList()` (cc/d2pl/transaction.cc:314) あり。詳細は未精査。

---

## 12. 事前の操作列・key 集合 (まとめ)

- **YCSB**: 可。`makeProcedure` が取引の全操作 (種別と key) を `tx.pro_set_` に作ってから `tx.begin()` を呼ぶ (include/ycsb.hh:102, 113)。pro_set_ は各 CC の TxExecutor の public メンバなので、CC の `begin()` から読める。再試行は同じ pro_set_ を使う (RETRY は makeProcedure の後、108)。ただし現状どの CC も pro_set_ の中身を読まない (grep: pro_set_ の使用は宣言・reserve・clear のみ)。pro_set_ 由来で CC に渡る情報は `is_ronly_` だけ (ycsb.hh:106) で、使うのは cicada (と YCSB driver の無い mvto)。`KEY_SORT` を渡す CC (ermia/mocc/si/ss2pl/d2pl) では makeProcedure 内で key 順に sort できる (既定 0)。
- **TPC-C**: 不可 (改変なしでは)。取引の引数 (`Query`) は workload 側で生成され取引関数に渡るだけで、TxExecutor には渡らない (include/tpcc.hh:45-90)。scan の結果に依存して後続の key が決まる取引 (OrderStatus・Delivery・StockLevel) もある。再試行ごとに query を作り直す (48-49)。
- **bomb 系**: `reconnoiter_begin()` で事前に読む経路がある (include/bomb.hh:542 ほか)。本調査の対象外で、未精査。

---

## 未確認の一覧

1. build は一切していない。以下は読解のみで、compile 可否は未確認:
   - ss2pl.cc が現行 API と合わず compile できないこと。
   - cicada で `INLINE_VERSION_OPT=1 && INLINE_VERSION_PROMOTION=1` にすると未定義の `write(...)` 呼び出しが入ること。
   - mocc の `MQLOCK` 分岐 (既定では無効) が compile できるか。
2. mocc read_internal の abort 経路で作る ReadElement の `failed_verification_` が未初期化になる件の実行時の影響 (温度更新が意図どおりか)。
3. ss2pl の delete 無施錠・abort 時に insert tuple を残す件の、TPC-C での実害。
4. oze の leader (thid 1) の `epoch_timer_start_` 未初期化、および thread 1 本時の挙動。
5. oze で旧版が回収されないこと (grep で回収コードが見つからないことまでは確認。別経路で回収されていないことの網羅確認はしていない)。
6. mvto の `install_version` が wts 順を保たずに先頭へ積むことが、可視版の選択や validation に与える影響。
7. silo / tictoc で `NO_WAIT_*` を両方 0 にした場合の spin (silo は expected を読み直さない) が実際に停止しないか。
8. bomb / sbomb / dbomb の各 driver の操作種別と reconnoiter の詳細。
9. d2pl の施錠・deadlock 処理の詳細。
10. 各 CC の `util.cc` の `chkArg()` が YCSB 用 flag (FLAGS_max_ope 等、各 CC の common.hh 側) と `FLAGS_ycsb_*` (include/ycsb.hh 側) をどう扱うか (YcsbWorkload が `FLAGS_ycsb_*` を読むことだけ確認)。
