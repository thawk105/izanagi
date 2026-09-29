## 1. 置き場

**結論。** (P1) の重ね patch を採る。適用順は pin C または C1' → `instr-cicada-trace.patch` → 新規 `instr-cicada-trace-tpcc.patch` とする。ただし **TPC-C 用の重ね patch を pin C 単独へ適用して TRACE=1 でビルドする対象にはしない**。C1' の共有 header が必要である。既存 patch と YCSB の v2 出力 bytes を保持でき、C2' 系へ pin が進んだ後も同じ順序の厳密適用を検査できる。

**根拠。** C1' の差分は `include/trace.hh:122-173` 相当へ thread-local の取引種別と v3 emitter を追加し、`include/tpcc.hh:24-27,53-59,107-115` 相当で begin 直後の設定と TRACE build の commit 計数を追加する。現行計装は `patches/instr-cicada-trace.patch:1-148` のとおり `cc/cicada/` の 4 file だけを変更する。統合して C1' の helper を無条件に参照すると、pin C の TRACE=1 で動く md_14 の YCSB を壊す。Cicada 内に v3 emitter と取引種別を複製する案は、共有 header と意味を二重管理し、`tpcc.hh` の commit 計数修正も別途必要になる。新たなプリプロセッサ条件は `TRACE` だけとし、C1' の既存 `#if !TRACE` は再実装しない。

**brief との差。** 配置は (P1) に賛成。ただし「C2' 系でもそのまま厳密適用できる」は未実測の条件であり、pin 前進後に `git apply --check` 相当を取り直す。重ね patch の `traceCommit` は既存 patch の該当 hunk を文脈に使うので、既存 patch bytes の変更が不要であることも適用確認で確定する。

## 2. v3 hook

**結論。** `traceCommit()` の冒頭で `izanagi_trace::tpcc_tx_type()` を一度取得し、非 0 の場合だけ v3 を出す。0 の場合は既存 v2 の出力式を**そのまま残す**。v3 の C は `C txid thid hi lo nR nW 0 0 tx_type`、R/W は `static_cast<uint32_t>(re.storage_)` / `we.storage_` を表番号として v3 helper に渡す。E の直後に取引種別を clear する。read-only も既存の早期 return 前の hook を通す。

**根拠。** 既存 C/R/W/E と genesis 写像は `patches/instr-cicada-trace.patch:54-91`、書く取引と read-only の呼出点は同 patch `:99-130`、元の早期 return は `external/ccbench/cc/cicada/transaction.cc:929-937`。表は `external/ccbench/include/tpcc/tpcc_tables.hh:16-29` の `Storage` 0～10、取引種別は `include/tpcc/tpcc_query.hh:19-26` の 1～5。`tpcc_cicada.cc:29-31` の `makeDB(param)` 直後に、YCSB 計装 patch `:131-148` と同形で `initial_wts`・設定済み印・終了時報告を渡す。新しい TRACE 専用行には `#else` の `#line` を設け、元の `tpcc_cicada.cc:31` 以降および既存 `transaction.hh` の論理行番号を比較する。

**brief との差。** (P2) に概ね賛成。取引種別 clear は E の**直後**とし、abort 時は次の `tpcc.hh:53` の begin 直後の setter が上書きするという D2225 の契約に従う。共有 header が無い pin C でこの重ね patch を TRACE=1 にしないことを起動器で明示する。

## 3. insert / delete の意味

**結論。** 通常の committed insert は I、delete は D として出せる。ただし、**D2232 の段 1 存在検査を「削除・再挿入を含む意味の完全検査」とは扱えない**。特に insert の途中失敗と、同一取引内の操作を一つの W に畳む経路を生死確認で調べる。

**根拠。**

- 初期ロードだけが `param->initial_wts` を版に使う（`cc/cicada/include/tuple.hh:74-92`）。実行時 insert は新しい `Version` を `tuple->init(thid, new_ver, wts)` に渡す（`transaction.cc:313-315`、`tuple.hh:95-107`）。既存 key は木の検索と `insert_value` の双方で拒否される（`transaction.cc:305-323`）。この範囲では D2232 項 4 の二条件を満たす。
- **例外的な stock 経路がある。** 木への insert 成功後、`node_map_` の版不一致で abort 状態を返す箇所は `transaction.cc:324-340`。この時点では `write_set_` 登録が `:340` に達しておらず、`abort():745-756` の INSERT cleanup はその tuple を見つけられない。残存 tuple は後続 insert に「既存」と見えうる。この経路が TPC-C の実走で発火するか、発火時にどの trace integrity と結果になるかを記録し、stock が正常という前提だけで通さない。
- read-own-insert は write set から body を返し、read set へ R を追加しない（`transaction.cc:153-165`）。insert 後の update も既存 write set を見つけると同じ W に畳む（`:201-205`）。したがって trace は committed txn の最終的な I を記録する設計であり、取引内の各操作列ではない。
- delete は直前の同一 key の write set entry を消してから `new Version(wts)` を作る（`:348-401`）。この「cancel previous write」は insert→delete の同一 txn などを単純な I/D 二行としては表さない。典型的な Delivery は scan で見つけた NewOrder を delete する（`include/tpcc/tpcc_tx_delivery.hh:35-70,193-208`）。
- D 版は `cpv()` で deleted にされ木から除去される（`transaction.cc:687-719`）。`read_internal()` は deleted 版で nullptr を返し、R を追加しない（`:102-127`）。木に無い key も R を追加しない（`:170-178`）。deleted tuple の GC は版の wts と `MinRts` を見て後で行う（`:845-856`）。木から除去された後の同一 key insert は新 tuple になり、trace の同じ `(表,key)` 履歴には後続 I として現れる。
- validation (b) は write 対象の可視版が deleted なら abort する（`:573-592`）。scan が実際に読めた版は `read_internal()` を通り R になる（`:421-456`）が、空の結果や範囲・境界は R に出ない。phantom 防止に使う `node_map_` は検証される（`:595-602`）が trace にない。
- `INLINE_VERSION_OPT=1` の実行時 insert は `tuple.hh:101-106` で渡された `ver` を `latest_` に接続しない。既定の 0 に固定して実走し、1 は未対応として扱う。既存計装が promotion 組合せを TRACE=1 で止める契約（`patches/instr-cicada-trace.patch:32-45`）も維持する。

D2232 の `_check_existence` は、最初の committed write が I なら初期不存在と推論し、I-on-live、U/D-on-absent、D 版の R などを調べる（`orchestrator/verifier/dsg.py:385-450`）。不在読み自体は R が無いので検査対象外である。D2232 項 4 自身も削除・再挿入・範囲読みへの拡張を保留している。

**brief との差。** (P1) の「Cicada でも二条件が成り立つ見込み」は通常経路には正しいが、`transaction.cc:324-340` の cleanup 漏れ候補を除外できない。stock で存在履歴違反が出た場合、判定器を緩めず、この経路を先に調べる。

## 4. commit 計数

**結論。** `--expected-commits` は benchmark stdout の `commit_counts_:` から取る。C1' の `tpcc.hh` は TRACE build で commit 成功後の quit 早期 return を外してから計数するため、Cicada が出した C 行と一致させる狙いに合う。abort と rollback は C にも commit 数にも含めない。

**根拠。** C1' 差分の `include/tpcc.hh:107-115` 相当は `if (loadAcquire(tx.quit_)) return;` を `#if !TRACE` に入れる。元の abort と retry は `include/tpcc.hh:92-107`、Cicada の成功時 emit は `transaction.cc:895-917,919-957` に挿入された既存 hook。NewOrder の rollback 用の存在しない Item は `include/tpcc/tpcc_query.hh:120-125`、失敗した取引は `tpcc.hh:92-107` で abort/retry される。md_3 起動器は `launch_cicada_run.py:64` の正規表現で stdout を読み、`:641-651,543-556` で verifier に渡す。

**brief との差。** C1' の計数修正を使う (P1) に賛成。ただし「C 行 = commit 数」は trace 出力時点と benchmark の終了競合を含む実測事項であり、推論だけで負例合格にしない。

## 5. 判定器

**結論。** production の変更は現時点で不要。v3 と `--protocol cicada` の組合せをそのまま使う。受理失敗が出た場合だけ、その入力と原因を保存して最小修正を検討する。

**根拠。** `parse.py:262-268,345-375` は v3 の表番号 0～10、取引種別 1～5、`nS=nQ=0` と新整数欄の ASCII 正規十進を要求する。`Storage` と `TxType` の値域は §2 のとおり一致する。wts の下位 32 bit は `parse.py:376-429` で Python の `int` として読み、2³¹ 以上を拒否する条件は無い。compact 側の signed 64 bit に収まらないときは legacy 側へ戻す設計（`parse.py:218-229`）なので、その fallback の記録も残す。v3 の existence は `dsg.py:385-450` で走る。`cli.py:68-90,105-110` は v3 を `result_to_dict_v3` で JSON 化し、巡回があれば rc 1、indeterminate は rc 3。`core.py:194-218` は `integrity.existence_violations` / `existence_violation_details`、`anomalies[].cycle_nodes`、各辺の `reasons[].table` を追加する。Cicada の証拠面は unavailable なので、無巡回でも認定上限は indeterminate（`model.py:233-275`、D2279）。

**brief との差。** (P3) に賛成。負例の「integrity 数値項目 0」は `clean=true` と同義ではない。Cicada の証拠面 unavailable を変えない。

## 6. 壊し patch

**結論。** 完了条件に使う第一候補は **insert を含む NewOrder に限定して read timestamp 更新を飛ばす**変異とする。第二候補は delete を含む Delivery に限定して read set 再検査を飛ばす変異とする。いずれも巡回の発生は静的には保証できないため、段 4 で事前登録し、発火・commit・witness の同一事象を照合する。第三候補の「delete の木からの除去を飛ばす」は存在履歴・進行異常の検査用で、巡回の正例には数えない。

| 候補 | 単一 site と機序 | 巡回候補・妨げる検査 |
|---|---|---|
| insert 限定 no-rts | `cc/cicada/transaction.cc:533-536` の `readTimestampUpdateInValidation()` 呼出しを、write set に INSERT がある取引だけ省く。NewOrder は District を更新し Order・NewOrder・OrderLine を insert（`include/tpcc/tpcc_tx_neworder.hh:301-324`）。NewOrder N が Customer を読み、Payment P がその Customer を更新すれば `N→P` の rw。P が District を読み、N が更新すれば `P→N` の rw、G2 候補。 | 既存 `broken-cicada-no-rts-update.patch` と同じ欠陥を insert 取引へ絞る。validation (a) `:543-570`、(b) `:573-592`、early abort がこの interleaving を止める可能性があるため、発火だけで成功扱いにしない。 |
| delete 限定 read recheck 省略 | `transaction.cc:566-569` の不一致時 abort を、write set に DELETE がある取引に限って通す。Delivery は NewOrder を scan で読み D にし、Order・OrderLine・Customer も扱う（`include/tpcc/tpcc_tx_delivery.hh:35-70,193-220`）。他の Delivery/Payment との交錯で、古い R から後続 W への rw と共有 Customer/Order の逆向き依存ができれば G2。 | validation (b) と `node_map_`（`transaction.cc:573-602`）が残る。特定の二取引・key で逆向き辺が実際に出ることを trace で確認するまでは**仮説**。 |
| delete の物理除去省略 | `transaction.cc:708-712` の `remove_value` を省く。D 版が木に残るため後続 scan/insert の挙動が変わる。 | 不在 R は出ず、再 insert は既存 key として失敗しうる。存在履歴違反や進行異常に偏るため、巡回の完了条件とは別枠。 |

生死確認は warehouse 1・thread 1・`extime=1` の stock と、候補別 thread 4 の短走にする。本走は NewOrder 比率を上げた 57:43、Delivery を含む mix、warehouse 1・thread 4、必要なら 8 を候補とする。`tpcc_perc_*` と `thread_num` は §8 の実名を使う。診断は既存三 patch と同様、`CICADA_BREAK_FIRED slug=... reached=... changed=... committed=...` を終了時に、commit した変化の**全件**を `CICADA_BREAK_EVENT slug=... tx_wts=... table=... key=... a_wts=... b_wts=...` として出す（既存形式は `patches/broken-cicada-*.patch`、起動器 `launch_cicada_run.py:449-466`）。`IZANAGI_` は patch 本文に含めない。帰属は事象の `tx_wts` から C の txid を引き、witness の `reasons[].table/key/u_ver/v_ver` と突き合わせる（既存実装 `launch_cicada_run.py:471-509` を v3 表付きに拡張）。`changed>0`、`committed>0`、該当辺を含む cycle、変異 run 自身の integrity 数値 0 と C=commit をすべて必要とする。

**brief との差。** (P4) の「1～2 本」は妥当だが、delete 限定案の巡回は静的証明がない。第一候補も TPC-C の共有 key と時刻の交錯に依存する。「発火したから正例」は不可。delete 物理除去案は存在・進行の別枠であり、完了条件に数えない。

## 7. TRACE=0

**結論。** 全対象 target の compile entry を列挙し、同一 target・同一 TU・同一 configure 値・同一 compiler flags の命令列を比較する。(i) pin C 対 pin C＋既存 instr は tpcc / bomb / sbomb の各 target、(ii) pin C 対 C1'＋既存 instr＋重ね patch は tpcc target で行う。

**根拠。** `external/ccbench/cc/cicada/CMakeLists.txt:1-14` は共通 `transaction.cc`・`util.cc` と `WORKLOADS ycsb tpcc bomb sbomb` を指定する。対象は各 target の `transaction.cc`、`util.cc`、各 workload の `tpcc_cicada.cc` / `bomb_cicada.cc` / `sbomb_cicada.cc` の **3 TU ずつ**。md_3 起動器の identity は `launch_cicada_run.py:213-269` で compile command と objdump を採り、`:289-350` で pin と patch 版を比較する。`build_variant():396-408` は現状 YCSB target 固定なので target 引数化が必要。`compile_entry():213-235` の target directory も同様。C1' 側は checkout OID を変え、`-ffile-prefix-map`、CMake cache、normalized compile command を揃える。命令列の正規化だけを同一判定に使い、前処理差分と nm/strings は診断として残す。

C1' の `tpcc.hh` は TRACE=0 側にも `#line 27` などの論理行番号指定を置く（C1' 差分 `include/tpcc.hh:24-27,53-59,107-115` 相当）。`__LINE__` が診断 macro に展開されれば literal や命令列へ影響しうる。`include/debug.hh:17-45` などの診断 macro と、実際の compile entry の前処理・命令列で確かめる。単に「`#if TRACE` 内だから同一」と推定しない。

**brief との差。** (P5) の二比較に賛成。ただし比較 (ii) は C1' の共有 header 差分も含むため、(i) の結果を流用できない。D2225 の header 差分は D297 合格と呼ばない契約も維持する。

## 8. 起動器と実走

**結論。** md_3 の repo 外起動器を複製し、base OID、target、schema、patch 順を build spec に持たせる。最初の 1 job は stock TPC-C の TRACE=1 と TRACE=0 identity、および最小の壊し発火診断を行う。本走は生死確認の値を見てから、cell と期待を固定して走らせる。

**根拠。** 変更点は `launch_cicada_run.py:24-93` の build/cell/job 定義、`:213-350` の target 別 identity、`:353-408` の checkout/build、`:412-466` の trace と診断集計、`:471-541` の v3 表付き帰属・stock 判定、`:595-660` の実行 flags と stdout commit 抽出、`:671-765` の base OID・patch 適用、`:790-878` の CLI/dry-run。C1' を選ぶ build だけ `6aa7a58f` を checkout し、pin C の stock は identity 対照に用いる。実走の TPC-C trace build は C1' を使う。flags は `include/tpcc/tpcc_common.hh:6-14` の `tpcc_num_wh`、`tpcc_perc_payment`、`tpcc_perc_order_status`、`tpcc_perc_delivery`、`tpcc_perc_stock_level`、`tpcc_interactive_ms`、共通 `thread_num`・`extime`・`group_commit=0`。NewOrder 比率は他の比率の残余なので、57:43 cell は後四比率を `43,0,0,0` とする。Delivery cell は例えば `43,0,4,0` とし、NewOrder は 53% となる。

事前登録する負例は「巡回 0、existence_violations 0、全 integrity 数値 0、C=stdout commit、上限 indeterminate」。正例は §6 の発火・commit・帰属した cycle と同じ健全性条件。生死確認は build 2～3、1 秒走行数個、identity 2 系列。本走は各候補と同時刻 stock を組にし、1/4 thread と必要時 8 thread を各 1 秒から開始する。見積りは build/identity が支配的で**約 1 node 時間、上限 2 node 時間未満を投入前に再見積り**する。これは計測値ではない。

**brief との差。** (P7) の 57:43 と Delivery 入り mix に賛成。ただし 57:43 cell に Delivery は入らない。二つを別 cell と明記する。warehouse 1 でも初期ロードは大きいので、所要時間と trace 量は生死確認で測って本走を決める。

## 9. 所有と波及

**結論。** repo 内変更は新規 `patches/instr-cicada-trace-tpcc.patch`、採択した新規 `patches/broken-cicada-*.patch` 1～2 本、`patches/README.md` の節、一次資料と spool fragment に限る。起動器は repo 外 job dir。`patches/ledger.json` は触れない。

**根拠。** 全 patch 走査では `orchestrator/tests/test_p3_s4_loop.py:8684-8719` が `IZANAGI_` 語を未登録 patch に見つけると失敗する。`test_ccbench_spawn_sites.py:667-725,2927-2942` は追加された `#if` 等から bare define を抽出し gate 登録と照合する。`test_mocc_template_proof.py:94-111` も全 patch を読み、MOCC marker の有無を調べる。新 patch 名の固定 bytes pin は今回の `rg` では見つからなかったが、**新規 file が作られた後**に完全一致 path と hash の検索を再実行する。既存 `instr-cicada-trace.patch` の消費者は md_14 の重ね patch と md_3 起動器（`launch_cicada_run.py:30-39`）なので、その bytes と YCSB v2 は保持する。README には適用順と base OID、v2/v3 切替、I/D の限界、負例/正例の判定、TRACE=0 の比較範囲、phantom 未対応、pin 前進時の再検査を記す（現節 `patches/README.md:873-899` と「トレース形式」`:900-952`）。

**brief との差。** (P1)/(P4) の新規 file 方針に賛成。新 patch 名の bytes pin が現時点で無いことは、将来の登録不要を意味しない。全件走査の影響確認は追加後に必要である。

## 10. phantom

**結論。** 今回は S/Q を emit せず、範囲読みの phantom は未対応と明記する。段 2 の設計メモには、scan の範囲と結果の双方を表す S/Q 行、木の初期 key 集合、insert/delete による範囲 membership の変化、`node_map_` の検証結果をどう verifier の辺・integrity に対応させるかを記す。

**根拠。** Cicada の scan は返った tuple だけ `read_internal()` を通して R にする（`transaction.cc:421-456`）。木の node version は `node_map_` に保存され、validation で照合される（`:595-602`）が現 trace にない。v3 parser は `nS/nQ≠0` を拒否する（`orchestrator/verifier/parse.py:369-375`）。D2224 は S/Q を段 2 とした。

**brief との差。** (P6) に賛成。今回の stock 無巡回は phantom を含む完全な TPC-C 正しさ証明ではない。

## brief への異議

1. `s1-brief.md` の「D2232 項 4 の二条件が Cicada でも成り立つ見込み」は通常の insert には合うが、木への挿入後・write set 登録前の abort 経路（`transaction.cc:324-340`）を含めた断定には使えない。
2. 「delete は `new Version(wts)` を積む」だけでは、同一取引の以前の W を先に消す処理（`transaction.cc:353-357`）と、commit で木から除去する処理（`:708-712`）が抜ける。trace の I/D 解釈に影響する。
3. (P4) の insert/delete 変異が巡回になるという含意は、TPC-C の具体的な逆向き依存と validation を通る interleaving の実測前には成立しない。§6 の二候補は事前登録する**仮説**である。
4. (P5) の `nm / strings` は TRACE 語の残存を調べる補助証拠で、命令列同一の代用にはならない。C1' の `#line` がある以上、比較 (ii) を独立に実施する。

## 総括

1. 重ね patch を採り、既存 instr patch と YCSB v2 の bytes を保持する。
2. TPC-C trace build の base は C1'、pin C は TRACE=0 比較対照とする。
3. insert 後の `node_map_` 不一致で残る tuple の扱いを、生死確認の重点項目にする。
4. 第一の巡回正例候補は INSERT 取引限定の read timestamp 更新省略とし、診断と witness を同じ表・key・版で照合する。
5. Delivery 限定候補は逆向き依存が実測で出なければ完了条件へ数えず、別候補を再裁定する。
6. stock と変異の双方で integrity 数値 0・C=commit を要求し、存在違反だけの変異を巡回正例に数えない。
7. TRACE=0 は tpcc / bomb / sbomb の各 3 TU と、C1' を含む独立した tpcc 比較を行う。
8. phantom は S/Q と初期 key 集合の設計メモに留め、今回の判定範囲から明示的に除く。