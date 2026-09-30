# CCBench Cicada の既存欠陥 4 件を原因を実測で確かめてから直した — promotion 有効時の巡回 (読み取り専用 tx の格上げ)、promotion 後の書き込みの欠落、INLINE_VERSION_OPT=1 の insert の異常終了、abort の use-after-free。修理後の tip で promotion 有効の 8 genome が YCSB と TPC-C の小走行で巡回 0 (上限 indeterminate)・TPC-C 完走・ASan 報告 0。push はしていない (人間の手番)

authority: none
default_effect: no-state-change

- 日付: 2026-09-30
- wave: `dev-wave-cicada-promotion-uaf-fix` (branch `worktree-dev-wave-cicada-promotion-uaf-fix`)。着手時 local main `4f412c67bcd7ff9cca1e78ce9bd1dd7a15d46037` (開始 gate rc=0、`verbatim/startup-gate.log`)
- 依頼: VHash md_32 (`verbatim/md_32.txt`、共通指示 `verbatim/common.txt`)。台帳 item: [T-2922] (promotion) と [T-2925] (abort の UAF)。
- 既裁定: D2277 項 1・2 (上流 CI を通す品質、基盤の欠陥は使いながら直す)、第 40 回裁定 (D2305) 項 6 (Cicada 2 本は別々に push、束ねた pin tip は AI が作り改めて依頼)・項 10 (1 修正 1 PR)、D16・D18・D20 (push・PR は人間)、D297、D2310 (gc_records の修理)。
- job dir (使い捨て script・生 log・Codex receipt・bundle・計算の全出力): `/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/` (= `/work/1/SFC/tanab/tmp/...`)。以下 `$J`。

## 0. 結論

1. **branch:** CCBench の新しい local branch `izanagi-cicada-promotion-uaf-fix`。土台は `izanagi-cicada-build-fix` (G `eb93423b`) と `izanagi-cicada-gc-records-fix` (`81fc4a84`) の merge commit `aa8e36f1669001e75a6d6da9609287dcc9f9d29b` (自動 merge、衝突なし、コードの追加なし)。その上に修理 4 commit (1 修理 1 commit):
   | commit | 題 | 変えた file |
   |---|---|---|
   | `76159527681a726eaa855f66b5eca341517c38e5` | fix(cicada): avoid promotion in read-only transactions | cc/cicada/include/transaction.hh |
   | `938ee196ffbcf36ad8c5341f3bd5d3a3be09460f` | fix(cicada): apply updates after inline version promotion | cc/cicada/include/cicada_op_element.hh・transaction.hh・transaction.cc |
   | `86228b400350c9cab8e2cf453a28c36c720d8a18` | fix(cicada): clean inserted versions before freeing tuples on abort | cc/cicada/transaction.cc |
   | `16ad3eb8ca5f7bb3aea789bff99958e2192f6714` (tip) | fix(cicada): initialize inserted tuples from the inserted version | cc/cicada/include/tuple.hh |
   差分は Codex author、commit は親 (trailer = Codex author・Codex reviewer・Claude manager)。bundle = `$J/tip.bundle` (sha256 `4b955c51…`、complete history)。これは本 wave の **local 検証土台** であって第 40 回項 6 の「束ねた pin tip」ではない。既存 2 branch は動かしていない。
2. **巡回の原因 (修理 1):** 読み取り専用 tx は rts で可視版を選び `later_ver_` を rts 基準で記録する。promotion はその tx を読みの途中で読み書き tx に変え、validation の読み取り再検査は `later_ver_` から wts 未満まで下る。`later_ver_` が aborted で、その手前に rts と wts の間の確定版が入ると、再検査はそれを飛ばして読んだ版に行き着き古い読みが通る (§2)。修理前の代表 genome で判定器が報告した代表 witness 52 件 (4 走行) の全部が、この経路で通った commit tx を含んでいた。修理 = 読み取り専用 tx では promotion しない (原論文 §3.1・§3.3 と照合、§2)。
3. **書き込みの欠落 (修理 2):** promotion が積んだ書き込み要素 (読んだ版の写し) に、同じ tx の後続 `update()` が素通りして要求の body を捨てていた。TPC-C の注文 insert 失敗が promotion 無効の約 16〜22 倍に増えていた (§3)。
4. **TPC-C の異常終了の原因 (修理 4、新事実):** 前 wave が promotion の失格理由とした `std::bad_alloc` は **promotion ではなく INLINE_VERSION_OPT=1 の insert の欠陥** だった。新しい Tuple の inline 版は pending で始まるので insert の版は別確保になるが、`Tuple::init(…, ver, …)` が ver を無視して空の inline 版を latest にし、その空 body の複写が align 0 の確保で失敗する。promotion 無効の OPT=1 genome でも同じく落ちる (§4)。既定 genome (OPT=0) は影響しない。
5. **use-after-free (修理 3):** abort が INSERT の tuple を解放した後に writeSetClean が書く。ASan で修理前に検出 (既定・promotion の両 genome)、修理後 0 件 (§5)。
6. **確認 (修理前と対):** 修理後 tip で promotion 有効の 8 genome の YCSB K・W・R・P (32 走行) と TPC-C M・R2 (16 走行)、promotion 無効 OPT=1 代表の TPC-C M・R2 がすべて判定器の巡回 0 (上限 indeterminate)・integrity 数値項目 0・C 行 = commit 数・READ_WTS_MISMATCH 0。TPC-C は代表 genome の Release で M・R2 各 3 回完走、同じ job の土台は M・R2 とも異常終了。YCSB の土台 (代表 genome) は同じ job で K に巡回 9、R に 359 (§6)。
7. **正例:** `patches/broken-cicada-promotion-ronly-stale-recheck.patch` (修理 1 の条件だけを外す) を重ねると判定器は R で巡回 308 を検出し、代表 witness 20 件中 18 件で巡回の辺の端点が壊した経路の commit tx、辺の key が event の key と一致した (§7)。
8. **上流 CI:** 修理後 tip の 213 file に clang-format 14 `--dry-run --Werror`、login の 14.0.0 と CI image `:latest` の 14.0.6 の両方で rc=0。CI image `:ci` で CI と同じ Release・sanitizer OFF の全 protocol build が configure・build rc=0、実行 file 34 本、CCBench 本体の warning・error 0 件 (§8)。GitHub Actions の結果ではない (push していない)。
9. **D297:** 検査器は修理後 tip を cicada の未知 macro で fails-closed に拒否した (期待どおり、pass ではない)。修理後 tip の `cc/cicada/` だけを pin C の tree に戻した probe (他の path は tip と同一) は検査器 pass。修理で意味が変わる TU は cicada の 4 file だけで、意図した差分として §8 に範囲を書いた。
10. **計算:** 12 request、Elapse 合計 2,898 秒 (約 0.81 node 時間、確認線 2 node 時間の下)。pin は C のまま、push もしていない (§12)。

## 1. 土台と branch

- 土台を merge にした理由: promotion の 8 genome の build には G の修理が要り、TPC-C (削除を含む mix) と今後の比較には gc_records の修理が要る。merge は両 branch の SHA を保つので、人間は既存 2 branch を別々に push したうえで (第 40 回項 6) 本 branch を追加で push できる。cherry-pick は同じ内容の別 SHA を作るので採らなかった (段 4 R4)。
- merge の作成: wave 木の submodule を動かさないよう、job dir の使い捨て clone で `git merge --no-ff --no-commit` → `commit -F` (`$J/mk-base.sh`・`mk-base.log`)。merge と各親の差分はもう一方の修理だけ (G 側 transaction.cc 10+/4−、gc 側 transaction.hh 4・transaction.cc 6 行)。
- 修理 commit は 1 度作り直した: 1 回目 (tip `9da70164`) の commit message の 3 か所が観測を超えていた (焦点再レビュー、§10) ので、どの確認にも使う前に branch を土台へ戻し message だけを直して作り直した。tree は同一 (`29e2f42c`)、旧版は `$J/tip-attempt1.bundle`。

## 2. 修理 1 — 読み取り専用 tx では promotion しない

**原論文との照合** (Lim ほか SIGMOD 2017、逐語抜粋 `verbatim/cicada-paper-excerpt.txt`): §3.1「A read-only transaction uses (thread.rts) instead, and does not track or validate the read set」。§3.3 の promotion の条件は「(1) a transaction reads a non-inlined version v as the visible version; (2) (v.wts) < min_rts; (3) the inlined version is currently UNUSED」で、そのとき「Cicada automatically upgrades the read access to an RMW access」。rts で読む読み取り専用 tx の読みを RMW へ格上げする規則は書かれていない。CCBench の実装は読み取り専用 tx でも promotion し、`is_ronly_` を false にして読み書き tx へ転換していた。

**機序 (静的、段 3 相談 A が具体的な版鎖で確認):** rts=10・wts=30 の tx が `L(15, aborted) → V(5, committed)` の鎖で V を読み `later_ver_ = L` を記録した後、別の tx が `B(25, committed)` を先頭に置く。promotion の RMW が A(30) を置くと鎖は `A → B → L → V` になり、validation の再検査 (transaction.cc の version consistency check) は L から下りて V に行き着き通る。B は wts 30 で可視なのに飛ばされる。読み書き tx の `later_ver_` は wts 基準なのでこの穴に当たらない。前 wave の段 3 相談 A の「既存 read の検証に穴は見つからない」はこの鎖を見落としていた。

**帰属 (実測、単位 D の診断、request 37912.nqsv、Elapse 280 秒、bnode037):** 代表 genome (OPT=1・PROMO=1・BACK_OFF=0・REUSE_VERSION=1・WRITE_LATEST_ONLY=0)、YCSB thread 4・1 秒、build 交互。Y0 = 土台 + promotion 診断変種 (計装から `#error` 1 行を外したもの、repo 外) + TPC-C 計装 + 使い捨て計器 (再検査を `later_ver_` 起点と最新版起点の両方で行い判定は変えず、食い違ったまま commit した tx を event に出す)。Y1 = Y0 + 読み取り専用 promotion の無効化だけ。

| build | cell・反復 | 判定器 rc | 巡回 (SCC) | 代表 witness | event の tx を含む witness | event の key の rw 辺を持つ witness | event 数 |
|---|---|---|---|---|---|---|---|
| Y0 | K r1 | 1 | 7 | 7 | 7 | 7 | 11 |
| Y0 | K r2 | 1 | 5 | 5 | 5 | 5 | 7 |
| Y0 | R r1 | 1 | 372 | 20 | 20 | 20 | 1,979 |
| Y0 | R r2 | 1 | 379 | 20 | 20 | 20 | 1,981 |
| Y1 | K r1・r2、R r1・r2 | 3 | 0 | 0 | — | — | 0 |

- event の `later_status` はすべて aborted (VersionStatus の値 2)。照合は判定器の代表 witness (最大 20 件) に限り、R の SCC 全部ではない。
- 1 回目の診断 (request 37853.nqsv、Elapse 250 秒) も同じ向き (Y0 の 3/4 走行が non-serializable、Y1 は 4/4 で巡回 0) だったが、job が判定器 JSON を読み違えて witness の照合が取れなかった (§10)。
- K (読み取り専用 tx がまれ: rratio 50・10 操作) の巡回が少なく R (rratio 90・4 操作) で多いこと、読み取り専用 tx が無い W と promotion が起きない P (初期版が inline) で前 wave が巡回 0 だったことも、この経路と整合する。

**修理:** `inlineVersionPromotion()` の条件に `!is_ronly_` を足し、読み取り専用 tx は rts の snapshot のまま commit させる。読み書き tx の promotion は残る。代案 (転換前の読みだけ最新版から再検査) は変更と証明範囲が広いので採らなかった (段 4 R1)。性能への影響 (読み取り専用が多い workload で inline 化の機会が減る) は測っていない。

## 3. 修理 2 — promotion 後の update の body を捨てない

**欠陥:** promotion は `update(s, key, TupleBody(ver->body_))` で読んだ版の写しを書き込み集合に積む。同じ tx が後で同じ key を `update()` すると、`searchWriteSet` が要素を見つけて body を使わずに戻る (transaction.cc の「Special treat due to performance」)。tx 自身の書き込みが失われ、読んだ値がそのまま書かれる。版の trace と判定器は値を見ないので、巡回としては現れない。

**観測 (単位 D の診断 4 回目、request 37976.nqsv、Elapse 151 秒、bnode050):** TPC-C Release TRACE=0、thread 4・1 秒、stdout の `insert order failed` 行数 / 走行 (4 thread の合計)。

| build (土台 + 使い捨て patch) | genome | M r1・r2 | R2 r1・r2 |
|---|---|---|---|
| T4 (Tuple::init の修理のみ) | OPT=1・PROMO=1 | 313,180・298,560 | 28,175・30,980 |
| T5 (T4 + UAF の修理) | 同 | 299,312・320,051 | 29,289・30,736 |
| T6 (T5 + update の body を移す) | 同 | 18,802・18,511 | 1,007・1,078 |
| T4p (Tuple::init の修理のみ) | OPT=1・PROMO=0 | 19,260・19,076 | 1,383・1,385 |

promotion 有効で修理 2 相当なしは promotion 無効の約 16 倍 (M、平均の比 15.96・16.16)・約 21〜22 倍 (R2、21.37・21.69)。修理 2 相当ありで promotion 無効と同じか少ない水準 (M 0.97 倍・R2 0.75 倍)。親の読み (NewOrder の district の次の注文番号の加算が握りつぶされ、同じ番号で insert し続ける) と整合するが、どの表のどの update が失われたかは計数していない。promotion 無効でも出る約 1.9 万件は並行 NewOrder どうしの注文番号の衝突の水準と見る (既定 genome OPT=0 の水準は測っていない)。

**修理:** promotion が要素を 1 つ積み、かつ tx が aborted でないときだけ、その要素に目印 `from_promotion_` を立て (`#if INLINE_VERSION_OPT && INLINE_VERSION_PROMOTION` の内側だけ)、後続の `update()` はその要素の新版へ body を移す。promotion 以外の二重 update (stock の素通り) は変えない。

## 4. 修理 4 — INLINE_VERSION_OPT=1 の insert で渡された版を使う

**送出点 (単位 D の診断 1 回目、gdb の catch throw、`$J/evidence/diag-1/logs/DBG-M-r1.stdout`):** `HeapObject::allocate(size=0, align=0)` ← `HeapObject::deep_copy_from` ← `TupleBody::operator=` ← `Tuple::init(thid=3, ver, initial_wts)` (tuple.hh:103) ← `TxExecutor::insert` (transaction.cc:315) ← Payment の `insert_history`。

**機序 (静的):** `Version()` は status を pending で初期化する (version.hh)。`insert()` は `new Tuple()` の inline 版を `getInlineVersionRight()` (unused のときだけ成功) で取れず、新版を別に確保する。ところが INLINE_VERSION_OPT=1 の `Tuple::init(thid, ver, initial_wts)` は ver を無視して `latest_ = &inline_ver_` (pending・空 body) とし、`body_` にその空 body を複写する。空 body の align は 0 で、`operator new(0, align_val_t(0))` が `std::bad_alloc` を投げる。

**一要因対照 (同じ診断 4 回目):** M・R2 × 各 2 反復。

| build | genome | M | R2 |
|---|---|---|---|
| T0 = 土台 | OPT=1・PROMO=1 | SIGABRT 2/2 | SIGABRT 2/2 |
| T1 = + UAF 修理相当 | 同 | SIGABRT 2/2 | SIGABRT 2/2 |
| T2 = + update の body 修理相当 | 同 | SIGABRT 2/2 | SIGABRT 2/2 |
| T3 = + 読み取り専用 promotion 無効 | 同 | SIGABRT 2/2 | SIGABRT 2/2 |
| T4 = + Tuple::init 修理相当 | 同 | 完走 2/2 | 完走 2/2 |
| T5 = T4 + UAF 修理相当 | 同 | 完走 2/2 | 完走 2/2 |
| T6 = T5 + update の body 修理相当 | 同 | 完走 2/2 | 完走 2/2 |
| T0p = 土台 | OPT=1・PROMO=0 | SIGABRT 2/2 | SIGABRT 2/2 |
| T4p = + Tuple::init 修理相当 | OPT=1・PROMO=0 | 完走 2/2 | 完走 2/2 |

SIGABRT の stderr は `std::bad_alloc` の terminate (一部は複数 thread の `terminate called recursively` が先頭に来て bad_alloc の文字列が先頭 3 行に入らない)。事前登録 (段 4 追補 1: T0 と T0p がともに落ち、T4・T4p・T5 が全反復で完走) を満たした。予測 (T1〜T3 も落ちる) も当たった。

**帰結:** [T-2922] の「TPC-C M・R2 × thread 4 が bad_alloc」は promotion の欠陥ではなく INLINE_VERSION_OPT=1 の 16 genome (promotion 無効の 8 を含む) の欠陥だった。前 wave (`output/insights/2026-09-29/ccbench-cicada-bugfix/README.md` §5) の「promotion 有効の 8 genome は失格」のうち TPC-C の部分の帰属を、ここで追記により訂正する (前 wave の記録は変えない)。gc_records 修理の一次資料 §6 の限界「INLINE_VERSION_OPT=1 の insert 経路では空 key が残りうる」も、同じ空の inline body に由来すると見られる (未確認)。

**修理:** `#if INLINE_VERSION_OPT` の分岐で `latest_ = ver`、`body_` を `ver->body_` から取る (OPT=0 の分岐と同じ意味)。新しい Tuple の inline 版を使えるようにする (unused で初期化する) 変更はしていない — inline 化の機会の話で、正しさには要らない。

## 5. 修理 3 — abort で tuple を解放する前に writeSetClean する

**欠陥 (前 wave の gc_records 修理の一次資料 §6 で報告済み):** `abort()` が INSERT の tuple を `delete` した後に `writeSetClean()` が同じ tuple の `continuing_commit_` (と OPT=1 なら inline 版の status) に書く。

**ASan (Debug・ENABLE_SANITIZER=ON・`ASAN_OPTIONS=detect_leaks=0:halt_on_error=0`、TPC-C M・thread 4):** 修理前は最初の heap-use-after-free で rc=1 終了 (`-fsanitize-recover` なしでは halt_on_error=0 でも止まる)。報告の frame は `#1 TxExecutor::writeSetClean()` (transaction.hh:345、`continuing_commit_` の store) ← `#2 TxExecutor::abort()`、解放は `abort()` (transaction.cc:752)。

| genome | 土台 (修理前) | 修理後 tip |
|---|---|---|
| 既定 (OPT=0・PROMO=0) | UAF 1 件・rc=1 (確認 job) | 0 件・rc=0 (確認 job) |
| 代表 promotion (OPT=1・PROMO=1) | UAF 1 件・rc=1 (単位 D の診断 1・2・4 回目、同土台 SHA・同 genome・同 argv、計装なし Debug ASan) | 0 件・rc=0 × 2 (確認 job) |

**修理:** INSERT の tuple を退避 → 索引から外す → `writeSetClean()` → 退避した tuple を delete。退避が要るのは `writeSetClean()` が末尾で write set を clear するため。**直していないもの:** 索引から外す前に tuple pointer を得た並行の読み手の寿命 (正常な delete は `gc_records` で遅延解放されるが、abort した insert は即時解放のまま)。OPT=0 で INSERT の別確保版が回収されない既存の未回収 (修理の前後で同じ)。どちらも今回の ASan 走行では検出されなかったが、証明ではない。

## 6. 確認 (修理後 tip と修理前の対)

job 本体は Codex author (`$J/confirm/launch_promo_confirm.py`)、投入は親の `$J/run-job.sh`。tip の `cc/cicada/` が「土台 + fix1〜4」と byte 一致すること、patch の sha256、compile_commands の `-D`、実行 file が表示した `#FLAGS_*` と argv (表示されない tpcc_* は argv で束縛) を全 build・全走行で照合。判定の受理 = 判定器 rc∈{0,3}・巡回 0・integrity 数値項目 0・C 行 = commit 数・READ_WTS_MISMATCH 0 (Cicada では `integrity.clean` は構造上 false なので使わない)。計算ノードでは自分以外の CCBench 実行が無いことを pgrep で確かめた (全 job で 0 件)。

**YCSB (request 38175.nqsv、Elapse 652 秒、bnode128):** genome の 3 桁は BACK_OFF・REUSE_VERSION・WRITE_LATEST_ONLY (いずれも OPT=1・PROMO=1)。cell は前 wave と同じ (tuple 200・zipf 0.9・thread 4・extime 1、K = rratio 50・10 操作、W = rratio 0・rmw・5 操作、R = rratio 90・4 操作、P = rratio 100・4 操作)。trace は promotion 診断変種 (repo 外) + TPC-C 計装。

| genome | K | W | R | P |
|---|---|---|---|---|
| 000 | 0 (222,492) | 0 (240,413) | 0 (1,371,789) | 0 (2,319,964) |
| 001 | 0 (219,773) | 0 (230,327) | 0 (1,384,305) | 0 (2,342,677) |
| 010 (代表) | 0 (375,941) | 0 (412,789) | 0 (1,644,767) | 0 (2,428,839) |
| 011 | 0 (365,152) | 0 (408,707) | 0 (1,577,549) | 0 (2,367,005) |
| 100 | 0 (161,727) | 0 (175,494) | 0 (815,968) | 0 (2,395,904) |
| 101 | 0 (162,732) | 0 (177,408) | 0 (783,939) | 0 (2,435,099) |
| 110 | 0 (183,851) | 0 (201,438) | 0 (908,672) | 0 (2,412,874) |
| 111 | 0 (184,895) | 0 (199,858) | 0 (911,349) | 0 (2,389,428) |

数字は巡回数 (括弧内は commit 数 = C 行数)。32 走行とも判定器 rc=3 (indeterminate)。同じ job の土台 (代表 genome) は K で巡回 9 (commit 384,647)、R で 359 (1,503,789)、いずれも rc=1。

**TPC-C (request 38176.nqsv、Elapse 327 秒、bnode053):** trace + 判定器 (warehouse 1、thread 4、extime 1、M = payment/order_status/delivery/stock_level 43/0/0/0、R2 = 43/4/0/20): promotion 8 genome × M・R2 = 16 走行と、OPT=1・PROMO=0 の代表 genome の M・R2、計 18 走行がすべて rc=3・巡回 0 (commit 数 27,636〜77,411)。Release TRACE=0 の代表 genome: 修理後 tip は M・R2 各 3 回すべて完走、同じ job の土台は M・R2 とも SIGABRT (bad_alloc)。修理後の `insert order failed` は Release の M で 18,246〜18,553 件、R2 で 1,011〜1,069 件 / 走行 (§3 の promotion 無効の水準)。

Delivery を含む mix は今回走らせていない (gc_records の修理は土台に入っているが、本 wave の確認対象外)。

## 7. 正例 — broken-cicada-promotion-ronly-stale-recheck

修理 1 の条件だけを外し、promotion した read 要素で再検査の `later_ver_` 起点と最新版起点が食い違ったまま commit した tx を `CICADA_BREAK_EVENT` に出す無条件 patch (`patches/README.md` の同名節)。修理後 tip → 診断変種 → TPC-C 計装 → 壊し、代表 genome、YCSB R (事前登録どおり R から始め、成立したので K は走らせなかった)。

- 判定器 rc=1、巡回 308、代表 witness 20 件。そのうち 18 件で、巡回の辺の端点に event の commit tx があり、その辺の key が event の key と一致 (`m1_killed` = true)。integrity 数値項目 0・C 行 = commit 数 (1,540,140)・READ_WTS_MISMATCH 0 で、巡回だけが赤の理由。
- 発火: `CICADA_BREAK_FIRED slug=promotion-ronly-stale-recheck reached=189 changed=183 committed=176`。
- 注記: 壊し走行の記録名が job の実装で一律 `no_cycle_upper_bound_indeterminate` になっている (記録名の付け方の誤り、判定と `m1_killed` には影響しない)。

## 8. 上流 CI

- **format:** 修理後 tip の checkout (子木 F の submodule、HEAD = tip・clean を確認) で、前 wave の `check_format_ci.sh` (CI の step と同じ `git ls-files -- cc include common | grep -E '\.(cc|hh|cpp)$'` → `clang-format --dry-run --Werror`) を login の clang-format 14.0.0 と CI image `:latest` (sif sha256 `64132a2f…`) の 14.0.6 で回し、**どちらも 213 file・rc=0** (`$J/format-tip.log`)。確認 job の中で回そうとした 2 回は、計算ノードに clang-format-14 が無い (1 回目) と build 用の `:ci` image に clang-format が無い (2 回目) で format に届かなかった (§10)。確認 job は format-tip.log の sha256 と要約を記録するだけで、中身 (tip・件数・rc) を合否に使っていない (焦点再レビュー 2 の残る限定)。format の合格の根拠はこの log そのもの。
- **build:** CI image `:ci` (`ghcr.io/thawk105/ccbench-devcontainer:ci` を 2026-09-29 に sif 化したもの、sha256 `cb8cd1c3…`、GCC 13.3.0・cmake 3.28.3・ccache 4.9.1) で CI と同じ `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF` → `cmake --build build -j 48`。configure・build rc=0、**CCBench の実行 file 34 本、CCBench 本体 (`cc/` `include/` `common/`) の warning・error 0 件** (warning 12 件は依存の masstree と autoconf)。request 38254.nqsv (bnode026、Elapse 51 秒)。CI との差は T-2854 §3 と同じ (依存は手元 cache の clean clone、ccache は空から、image は取得時点の tag)。**CI の既定 build は promotion・OPT=1 の非既定分岐を compile しないので、CI 緑は修理の検査ではない** (それは §6 の 8 genome の build と走行が担う)。
- **計装 patch の当たり方:** 修理後 tip に `instr-cicada-trace.patch`、その上に `instr-cicada-trace-tpcc.patch`、`instr-cicada-trace.patch` の上に壊し patch が、いずれも `git apply` (fuzz なし) rc=0 (同 job の patch 適用表)。他の cicada 系 patch (forwarding・ro-gcflag・hot-block・既存の壊し・fix-cicada-gc-records*) の修理後 tip への当たり方は調べていない (gc 修理 2 本は tip に含まれるので不要)。
- **D297 (request 38293.nqsv、bnode023、Elapse 1,021 秒、GCC 11):** (1) 検査器 `tools/check_trace0_preprocess_identity.py` を pin C → 修理後 tip で走らせると rc=1、stderr は「source_digest: cc/cicada/transaction.cc の条件指令が未知マクロ ['INLINE_VERSION_OPT', 'INLINE_VERSION_PROMOTION', 'SINGLE_EXEC', 'WORKER1_INSERT_DELAY_RPHASE'] を参照 … fails-closed で停止」— 前 wave (C→G) と同じ拒否で、pass ではない。(2) 修理後 tip の clone で `cc/cicada` を `git rm` → pin C から `git checkout` した使い捨て probe (`cc/cicada` の tree = pin C の `0db663e4…`、`cc/cicada` 以外の tree manifest は tip と一致、sha256 `33e56564…`) を pin C → probe で判定すると **rc=0 (pass)**。つまり修理後 tip の非 cicada の bytes について、選定文脈 (stock・mocc・silo) の TRACE=0 正規化 preprocess 出力と include 活性は pin C と同一。1 回目 (request 38254.nqsv) は probe が file の bytes だけを戻し実行ビットを落として検査器が mode 変更で止まった (§10)。
- **意図した差分 (cicada の TU):** 修理後 tip と F の差は `cc/cicada/` の 4 file (transaction.cc・include/transaction.hh・include/cicada_op_element.hh・include/tuple.hh) だけ。既定文脈 (各 `#if` が既定値、TRACE=0) の前処理出力の差は、行番号を正規化すると修理 3 の abort 本文だけ (`verbatim/evidence/default-preprocessed-normalized.diff.txt`)、生の比較ではそれで行がずれた `ERR` の `__LINE__` 展開 2 か所も変わる (実装子 F の login 検査、`verbatim/s5-author-F2.md`)。OPT=1・PROMO=0 ではそれに加えて修理 4 の `Tuple::init` の 2 行 (`verbatim/evidence/opt1_promo0-*.diff.txt`)。修理 1・2 は promotion 有効の文脈にしか現れない。

## 9. 変異 (事前登録 = 段 4 裁定 `verbatim/s4-ruling.md`、M3 は追補 3 の erratum)

| ID | 変異 | 期待 | 結果 |
|---|---|---|---|
| M1 | 修理後 tip + 壊し patch (修理 1 の条件を外す) | 判定器 non-serializable、witness の辺の端点に壊し event の commit tx と key | **KILLED** — R で巡回 308、代表 witness 20 件中 18 件が一致 (§7) |
| M2 | 修理後 tip から fix3 だけを逆適用 (代表 promotion genome、Debug ASan) | heap-use-after-free、最初の報告で `writeSetClean` の呼出し元が `abort` | **KILLED** — UAF 1 件、`#1 writeSetClean` → `#2 abort` |
| M3 | 修理後 tip から fix2 だけを逆適用 (代表 promotion genome、Release TPC-C M) と修理後 tip を同じ job で交互 | `insert order failed` が 逆適用版 > 5 × 修理後 tip (kill に数えない感度 pin) | **到達** — 逆適用版 305,335 件 対 修理後 18,306 件 (約 16.7 倍)。job の自動欄は thread 接頭辞付きの行名を数え損ねて 0/0・`not_reached` と出した。値は記録済みの thread 別件数 (76,018・76,351・76,380・76,586 と 4,549・4,547・4,614・4,596) から親が再計算した (§10) |

- 初回登録の M3 (fix2 逆適用 + 単位 D の計器で update の素通りを数える) は、計器 patch が fix2 を戻した木に厳密に当たらず実行不能と分かり、結果を見る前に差し替えた (追補 3)。初回登録は `verbatim/s4-ruling.md` に残す。
- izanagi の pytest が消費する実装面の変更は無い (repo 内の実装面は壊し patch 1 本、CCBench は submodule の branch で gitlink 不変) ので、pytest の変異 matrix は置いていない。

## 10. 工程の失敗と訂正

- **Codex 実装子の編集経路:** 単位 F の 1 回目は `external/ccbench/` の非 EVOLVE-BLOCK file への直接編集が hook (guard_write、hooks/README.md「編集面の限定」) に拒否され未実装で終わった。子木内の使い捨て clone で修理し差分を出す形で投げ直した。
- **診断 job:** (1) 前 wave の promotion 診断変種は計装 patch の「置き換え」なのに「重ね」として順序を組み当たらなかった (親の適用検査で発見)、(2) 判定器の stdout と stderr が連結されて JSON を読めず witness 照合が 0 件になった、(3) ASan の halt_on_error=1 と `#FLAGS` 照合で後続が止まった、(4) TPC-C の実行 file は tpcc_* の flag を表示しないのに照合を必須にしていた、(5) 使い捨て patch が promotion 無効 genome で未使用変数 (-Werror) になり build が止まった。どれも走行を止める側に倒れ、誤った値を受理してはいない。4 回の診断 request の合計 Elapse は 779 秒。
- **確認 job:** 1 回目は genome の CMake 変数名 (INLINE_VERSION_OPT の cache 名は `CCBENCH_INLINE_VERSION_OPT_CICADA`) の誤りを compile の `-D` 照合が検出して止まった。M3 の自動欄は stdout の thread 接頭辞付きの行名を数え損ねて 0/0 (`not_reached`) を出した — 親が記録済みの thread 別件数から再計算した値を §9 に書く。
- **commit message:** 1 回目の修理 commit の message は「every reported witness」(代表 witness に限ると書いていない)、TPC-C の district の記述 (未計数)、「first inserts」(未検証) の 3 か所が観測を超えていた。確認に使う前に作り直した (§1)。
- **親の cd:** 診断 job の dry-run で子木へ cd して session が閉じ込められ、`EnterWorktree(path)` で 1 回で復帰した (F100 の同型)。
- **CI part:** 1 回目は計算ノードに clang-format-14 が無く、2 回目は build 用の `:ci` image に clang-format が無く、3 回目は D297 の probe が実行ビットを落として検査器が mode 変更で止まった。format は親が login で回し (§8)、probe は `git checkout` で mode ごと戻す形に直して 4 回目で通った。親の fix prompt が必読資料を相対表現で書き、実装子が「読めなければ即停止」に従って 1 本空振りした (X6)。

## 11. 確かめたこと・確かめていないこと

確かめた: §0 の 1〜10 (観測した cell・genome・反復の範囲で)。

確かめていない:
- GitHub Actions の CI が緑であること (push 前)。
- 巡回 0 は観測した cell・1 秒の小走行での 0 で、上限は indeterminate。全スケジュールの直列化可能性の証明ではない。promotion の診断変種 (repo 外、`#error` を外したもの) で取った trace は標準の計器で保証された観測ではない (W 行は promotion 由来か本来の update か区別しない)。
- 修理 1 の witness 照合は判定器の代表 witness (最大 20 件) の範囲で、R の数百の SCC 全部ではない。
- 修理 2 の効果は `insert order failed` の件数で見た。どの表のどの update が失われていたかは計数していない。既定 genome (OPT=0) の insert 失敗の水準は測っていない。
- 性能値 (修理で throughput がどう変わるか、読み取り専用 tx の promotion を止めた影響) は取っていない (規律 1: 取るなら trace と計器を外した build で同時刻の対照を置く別 item)。
- promotion 有効 8 genome の md_11 の較正の空間への再計測 (依頼どおり別 item)。
- Delivery を含む TPC-C mix、warehouse > 1、thread 4 以外、BoMB・SBOMB。
- 並行の読み手から見た、abort した insert の tuple の即時解放 (§5)。OPT=0 の INSERT 版の未回収 (§5)。
- 他の cicada 系 patch (forwarding・ro-gcflag・hot-block・既存の壊し) の修理後 tip への当たり方と生死。
- 前 wave の §2 で scope 外にした「YCSB の再試行で読み取り専用の指定が戻らない」— 修理 1 の後は読み取り専用 tx が promotion で転換しないので、この経路は promotion からは起きなくなった (静的な読み、未実測)。

## 12. push とその後 (人間の手番)

1. 第 40 回裁定 (D2305) 項 6 のとおり、既存の `izanagi-cicada-build-fix` (G) と `izanagi-cicada-gc-records-fix` を別々に push したうえで、本 branch `izanagi-cicada-promotion-uaf-fix` (tip `16ad3eb8…`) を別名の新 branch として push する (force 不要)。本 branch は 2 本の merge を土台に含むので、先に 2 本が上がっていれば差分は merge commit と修理 4 commit だけ。
2. GitHub の Actions で build・format が緑であることを確かめる。
3. 上流還元 (項 10、1 修正 1 PR) は修理 4 commit がそれぞれ独立した 1 PR の候補 (修理 2 は修理 1 の後の文脈に当たる。修理 3・4 は独立)。PR の説明文は AI が起草、作成と merge は人間。
4. pin の前進 (gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・patch の厳密適用・D297) は push と CI 緑の後の別 wave。D297 は cicada の文脈 macro の扱い ([T-2921] の (a)) が未決のまま。束ねた pin tip は第 40 回項 6 のとおり AI が作り改めて依頼する。
5. pin が本 branch を含むまで、promotion 有効の 8 genome と INLINE_VERSION_OPT=1 の TPC-C は pin C では使えない (修理は branch にだけあり、out-of-tree の修理 patch は作っていない)。
6. branch の所在: 子木 F の submodule git dir と `$J/tip.bundle`。本 wave の land 後に主 checkout の submodule git dir へ bundle から非 force で fetch する。

## 13. 工程と費用

- 段構成: 軽量版ではなく正しさと基盤に関わるので段 2 plan 1・段 3 相談 2 (正しさ境界 sol・実効性/過剰 luna)・段 6 レビュー 2 (正しさ・過剰削除)・焦点再レビュー 2 を置いた。
- Codex 子: plan 1、相談 2、author 4 (D・F・F2・X)、fix 12 (D1〜D4・F1・X1〜X7)、review 2、focus 2。F の 1 回目 (hook 拒否) と X6 (prompt の path) は空振り。
- 計算 (Elapse、Pegasus gen_S、1 request = 1 node): 診断 250 + 280 + 98 + 151 秒、確認 1 回目 17 × 3 秒、確認 2 回目 652 + 327 + 17 秒、CI 3 回目 51 秒、CI 4 回目 1,021 秒、計 2,898 秒 (約 0.81 node 時間)。gen_S は 1 request が 1 node の 48 CPU を使い切るので、並走 wave (md_18・md_29・md_31) の request と node を共有しない (`docs/pegasus-runbook.md`)。各 job は計算ノード上で自分以外の CCBench 実行が無いことを確かめた (全 job で 0 件)。login では format・patch の適用検査・1 TU の構文検査・dry-run だけを行った。

## 14. 再現資料

- `verbatim/`: 依頼・共通指示・原論文の抜粋・段 1 brief・段 4 裁定と追補 1〜3・plan・相談 2・実装子と fix の報告・レビュー 2・焦点再レビュー 2・開始 gate の log・修理差分 4 本と commit message (`fix-diffs.md`)。
- `verbatim/evidence/`: 診断 2・4 回目と確認 (ycsb・tpcc・ci 4 回目) の result.json、CI image の report、gdb の backtrace、ASan の報告、前処理比較、format の log、merge と branch 作り直しの log。
- job dir `$J`: 使い捨て script (Codex author の `diag/`・`confirm/`、親の `run-job.sh`・`mk-base.sh`・`mk-fix.sh`・`redo-fix-branch.sh`・`run-format.sh` ほか)、Codex receipt (`codex/`)、`base.bundle`・`tip.bundle`・`tip-attempt1.bundle`、計算の全出力 (`evidence/`、修理前の巡回ありの raw trace `evidence/diag-2-kept-trace/` 174 MB)。
