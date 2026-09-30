# 1. 設計

以下の `cc/cicada/…` はすべて `external/ccbench/cc/cicada/…` を指す。実装対象は pin C `68106660` への inert patch とし、submodule 自体は変更しない。構成 B は timestamp、validation、GC の規則を維持し、版選択の配置だけを変える（`docs/vhash-evaluation-preregistration-draft.md:99-103,146`）。

| pin の位置 | patch の hunk と設計 |
|---|---|
| `include/tuple.hh:24-36` | `#if CICADA_VHASH_K` 内で Tuple に `seq`、件数、連続した K 個の `{uint64_t wts, Version* ptr}` を追加する。値と status は複製しない。K は 1/2/4/8 だけを許し、未定義または 0 では追加フィールドもコードも消す。`inline_ver_` は従来どおり Tuple 内に残す。 |
| `include/tuple.hh:38-52` | key ごとの writer lock を `seq` の偶数→奇数 CAS、奇数→次の偶数 release store で実装する。reader と writer が同じ記述子に触れるので、**件数・wts・ptr は atomic** とする。普通のフィールドを seqlock だけで保護すると C++ の data race になる。writer は CAS の acquire/release、記述子の書込みは relaxed、完了時の `seq` は release。reader は `seq` を acquire で前後に読み、同じ偶数のときだけコピーを採用する。 |
| `include/tuple.hh:74-108` | `init` の両 overload で公開前の hot を `{initial_wts, latest pointer}` 1 件にする。第 2 overload の `INLINE_VERSION_OPT=1` 側は引数 `ver` ではなく `&inline_ver_` を載せる。新 tuple は `transaction.cc:313-320` の `newVersionGeneration`→`init`→Masstree 公開の順なので、公開前に hot を完成させる。 |
| `transaction.cc:79-126` | `SINGLE_EXEC=0` の第 1 段、`102-107` の「wts が新しすぎる版を飛ばす」部分だけ置換する。hot の atomic 記述子をローカルへコピーし、`seq` 再確認後に scalar で先頭から比較する。奇数・変更検出時は**最初から** stock の `latest_` 走査へ戻る。hit なら最初の `wts ≤ trts` の ptr を `ver`、直前の ptr を `later_ver` とする。全件が新しすぎれば hot 末尾の ptr から cold を続ける。`108-126` の PENDING 待ち、ABORTED 飛ばし、deleted、read set 記録は維持する。 |
| `transaction.cc:463-531` | 各 install 試行の前に対象 Tuple の hot lock を取り、`492-509` の位置探索と `516-525` のどちらの CAS もその区間内で行う。CAS 成功時だけ hot 内の挿入位置を shift して更新し、偶数に戻してから `break`。CAS 失敗時も必ず unlock して再試行する。`493-495` の早期失敗と他の `goto FINISH_VALIDATION` に lock を持ち込まないよう、lock の寿命を内側の helper／scope に閉じる。`530` の `finish_version_install_` は解除後でもよい。 |
| `include/transaction.hh:343-368`、`transaction.cc:745-768` | install 済み abort は status を ABORTED にするだけ。hot から削除しない。未 install の `inline_ver_` の権利返却と heap 版の reuse は stock のまま。 |
| `transaction.cc:806-843`、`include/transaction.hh:173-197` | 既存の `gc_lock_` 取得後、`835` の tail 切断前に hot lock を取る。切断点より後ろにある記述子を除き、`next_=nullptr`、`min_wts_` 更新後に hot lock を離す。それから `gcAfterThisVersion` で inline 版の権利返却または heap 版の reuse を行う。lock 順は GC 側 `gc_lock_`→hot lock、install 側 hot lock のみと固定する。 |
| `include/version.hh:27-30,75-99,135-136` | Version の既存 `wts_`、`next_`、`status_` と release/acquire 公開を利用し、型や状態遷移は変えない。hot の ptr は GC が切り離した object の再利用前に消す。 |

**P3 の全列変更 site 監査。** `ldAcqNext` は読取りであり、書込み site は以下が全件である。`Version::set` と constructor の `next_=nullptr` は未公開版の初期化だが、再利用との関係で表に含める（`cc/cicada/include/version.hh:34-58,85-99,135-136`、`cc/cicada/transaction.cc:515-525,835`）。

| 列変更 site | 偶数時点で hot＝列の先頭 K 件を守る条件 |
|---|---|
| `include/tuple.hh:82,87,102,105` の `latest_` 初期化 | Tuple を公開する前に hot の 1 件を初期化する。 |
| `include/version.hh:34-58,85-99` の `next_=nullptr`／`set` | 未公開または回収済み object だけを対象とする。`newVersionGeneration` の inline/reuse 経路（`include/transaction.hh:217-245`）で、まだ hot が参照する ptr を再利用しないことを GC 側で保証する。 |
| `transaction.cc:515,522` の新 `next_` への release store | 新版はまだ列から到達不能。直後の公開 CAS まで hot lock を保持する。 |
| `transaction.cc:516-519` の `latest_` CAS | hot lock 中、成功時に先頭へ shift 挿入し、失敗時には hot を変えない。 |
| `transaction.cc:523-526` の `pre_ver->next_` CAS | hot lock 中、成功した位置が K 未満なら shift 挿入、K 以深なら hot は不変。失敗時は不変。 |
| `transaction.cc:835` の `next_=nullptr` | `gc_lock_` と hot lock の中で tail を切り、残る先頭 K 件だけを hot に残す。 |
| `include/transaction.hh:347-348` の ABORTED 化 | **列のリンクは変わらない。** hot も変えず、reader の既存の status 処理に任せる。 |

`transaction.cc:102-107` の reader は、hot の ptr を **seq の再確認前に dereference しない**。採用後の GC 安全性は、stock と同じ取引の公表済み rts と `MinRts` 境界に依存する（`transaction.cc:40-43,806-838`）。この依存と再利用競合は実装レビューと trace 検査の重点にする。

# 2. 意味の論証

列が wts 降順で hot が物理列の先頭 K 件を正確に写すなら、hot で最初に `wts ≤ trts` となる版は stock の `transaction.cc:102-107` が停止する版と同じである。hot に候補がなければ末尾から `next_` を辿るので、cold 側でも同じ版に達する。`later_ver` は候補の**直前の物理版**とし、候補が hot の 0 番なら null とする。これで `transaction.cc:543-570` の validation (a) が辿り始める位置も stock と同じになる。

選択後の PENDING 待ち、ABORTED の通過、deleted 判定は `transaction.cc:108-126` に残す。特に ABORTED を hot の段階で除外すると、候補と `later_ver` の物理的な隣接関係が崩れる。read-only は `rts_=MinWts−1` を使用し（`transaction.cc:34-43,92-97`）、commit 時に validation を行わない（`transaction.cc:929-942`）。従って read-only の誤選択は validation (a) では救われない。

反例: 物理列が `[A(aborted, wts=30), B(committed,20), C(committed,10)]`、K=2 で hot から A を消すと、hot が `[B,C]` になり P3 に反する。`trts=25` では stock の第 1 段は A を越えて B を選ぶが、`later_ver` は A である。圧縮 hot から B を直接選んで `later_ver=null` または別の ptr にすると validation (a) の開始点を変える（`transaction.cc:102-126,543-550`）。よって P4 の削除案は採らない。

# 3. macro・gate

| knob | 値・owner TU | 用途 |
|---|---|---|
| `CICADA_VHASH_K` | 未定義/0、1、2、4、8。`cc/cicada/transaction.cc` を gate owner、`include/tuple.hh` 等を companion として登録 | 配置と読取りをコンパイル時選択。0 は stock。K ごとに別 binary。 |
| `CICADA_VHASH_COUNT` | 0/1。owner は `cc/cicada/transaction.cc`、K 有効を companion 条件にする | hot hit/miss、fallback、cold hop、install 件数、hot lock の待ち時間／保持時間を thread 別に計数する。性能値には使わない。 |
| `CICADA_VHASH_WL` | 0/1。owner は `cc/cicada/ycsb_cicada.cc`、workload hunk は `external/ccbench/include/ycsb.hh:55-84,97-115` | `izanagi_ronly_pct=-1/0/50/95` を定義する。-1 は通常 YCSB の生成を維持。割合指定時は生成済み procedure を ro または少なくとも 1 write の update にし、`ronly_` を再計算してから `begin()` する。stock 対照にも同じ WL build を使う。md_15 の flag の先例は `patches/instr-cicada-version-lifetime.patch:212-216,349-380`。 |

`CICADA_VHASH_K` の gate は 0 対 1 の branch 選択だけで 2/4/8 の値域や正しさを証明しない。driver が 1/2/4/8 の compile command と binary hash を個別に照合する。`#if` の site 件数は**実 patch の directive を数えた数**を pin として登録し、作成前の推測値を固定しない。`#if K` の owner TU と header companion、COUNT、WL の各 site を `condition_meaning_gate.py:82-89,394-400,449-465,550-605` の `DEFINE_SPECS`・witness・件数へ追加する。`materializer_admission.py:103-117` に新 driver の非採用 materializer、`screening_driver.py:51-97` に 3 macro の default 0 を追加する。`orchestrator/tests/test_condition_meaning_gate.py:47-71,189-202` の集合・exact directive・件数、`test_ccbench_spawn_sites.py:38-98` の起動 site、`test_p3_build_authority_cli.py:161-183,1240-1271` の materializer 集合、`test_p3_s4_loop.py:8551-8557` の `allowed_non_variant_tokens` を追随させる。先例の変更閉包は `git show --stat 02c382253`、`a3bc64e3b`、`315c1d125` の一覧で確認した。

macro なしの inert 証拠は、依存 build 後に YCSB target の compile command を一意に選び、pin と patch 後を同じ argv で `-E` し、空行と行 marker だけを除いて比較する。変更した header を含む他 target も必要に応じて比較する。各追加 hunk 後の `#line` を忘れない（`orchestrator/campaign/vhash_forwarding_prototype.py:173-229`、`output/insights/2026-09-29/vhash-forwarding-prototype/README.md:260-268`）。条件 gate の supply/meaning は build 前に通すが、その証拠はコンパイル条件の選択に限る（`orchestrator/campaign/vhash_forwarding_prototype.py:104-152`）。

# 4. 壊し

- **B1、古い hot 記述子を選ぶ:** `read_internal` の hot hit で、選んだ版より 1 つ古い committed 版を ro の一部の読みに返す。`patches/broken-cicada-stale-read-ro.patch:52-69` と同様、reached／changed／committed 事象を全件記録し、trace の R と突き合わせる。ro は validation を持たないため、同一 snapshot 内の不整合から判定器の巡回を期待する（`transaction.cc:929-937`、`output/insights/2026-09-29/vhash-cicada-verifier/README.md:100-110`）。
- **B2、PENDING を飛ばす:** hot が指した PENDING 版を待たずに次の確定版へ進む。update tx では validation (a) が版の不一致を検出して abort しうる（`transaction.cc:543-570`）。ro ではその検査がないため、ro を含む cell も用意する。ただし単発の古い read が必ず巡回になるとは限らない。到達・変更・commit・帰属 witness を別々に報告する。
- **B3、必要時の追加候補:** `later_ver` だけを誤って hot 候補の 1 つ前ではなく null にし、update tx の validation (a) を攻撃する。B1/B2 が発火しても期待経路の帰属 witness が得られない場合にだけ投入する。事前に壊し点と期待 witness を固定し、判定器や trace の判定条件は変えない。

trace は pin→`instr-cicada-trace.patch`→本 patch→壊し patch の順に重ねる。判定器は `python -m verifier <dir> --json --quiet --protocol cicada` に通し、rc 0/1/3 を判定結果、2 を使用法エラーとして扱う。巡回が出た variant は即失格とし、巡回 0 でも上限は indeterminate（`output/insights/2026-09-29/vhash-cicada-verifier/README.md:64-85,135-149`、`CLAUDE.md:54-69`）。

# 5. driver と計算量

置き場は `orchestrator/campaign/vhash_cicada_hot_block.py` とする。条件 gate、materializer 登録、compute site と binary 起動の監査が先例と同じため（`orchestrator/campaign/vhash_forwarding_prototype.py:33-41,104-152,726-803`）。作図生成器は `tools/plotting/plot_vhash_cicada_hot_block.py`。subcommand は `smoke`、`run --job-index 0|1|2`、`trace`、`aggregate --raw …` とする。`dispatch_compute.py --task generic --walltime … -- python3 -m …` で 3 job を別 node に同時投入し、各 job 内は単独ベンチにする（`orchestrator/campaign/vhash_forwarding_prototype.py:6-8,769-803`）。

build は dependency、perf の stock＋K1/2/4/8、COUNT の K1/2/4/8、TRACE の stock＋K1/K8。perf は `TRACE=0, ADD_ANALYSIS=0, COUNT=0`、COUNT は別走、TRACE は `TRACE=1, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0`。TRACE の組合せ制限は `output/insights/2026-09-29/vhash-cicada-verifier/README.md:51-54` に従う。ro workload 用 WL は stock と各 K に同じく有効にする。forwarding patch は重ねない。

主格子は ro 指定率 `{0,50,95}`×GC `{10,1000,100000}` の 9 cell（update procedure 内の read 比率は rr50）、通常 YCSB rr5/rr50/rr95 と md_11 の各最良 GC の 3 cell、計 12 cell。共通設定は 48 thread、N=1M、skew 0.9、max_ope 10、rmw 0、extime 3 秒、`BACK_OFF=0, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0`（`output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md:16-20,114-119`）。3 job に 4 cell ずつ割り、**各 cell の stock と全 K は同一 job／node で round ごとに交互実行**する。5 round の腕順は `stock,1,2,4,8` を 1 つずつ回転する。これで perf 300 run。COUNT は各 cell×K の 1 回、1 秒を別 build で走らせ、探索・hit・fallback・writer lock 費用を記録する。RSS は run の maxrss と、Tuple 追加量の下限 `N×(8+16K)` B の両方を示す。構造体の alignment、atomic 件数、allocator により実増分はこの式と一致しない。

1 run の見積りは、先例の `33 records / 173 s` と `55 / 258 s`（build 込みで約 4.7〜5.2 秒/record、`output/insights/2026-09-29/vhash-forwarding-prototype/README.md:122-129`）を保守的に **5.3 秒/3 秒 run** とする。perf 300×5.3=1,590 秒。推測: COUNT 48 run を各 4 秒＝192 秒、11 build 相当×3 job×30 秒＝990 秒、smoke/TRACE/判定に 600 秒を確保しても合計 **3,372 秒＝0.94 node 時間**。2 node 時間未満。投入前に smoke の実 Elapse で再見積りし、7,200 秒以上なら結果を見ずに **5→3 round**、なお超えれば ro×GC の 9 cell を ro `{0,95}`×GC `{10,100000}` の 4 cell に縮める。なお超えるなら投入を止め、見積りを一次資料へ記録する。md_11 の J2 は 36 run/job 相当で 164〜214 秒だった（`output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md:207-218`）。

raw JSON は node、時刻、job ID、pin・patch・binary hash、compile command、gate receipt、build 種別、cell、K、round、argv、stdout/stderr hash、rc、elapsed、throughput、maxrss、COUNT、trace integrity と verifier 判定、`perf_eligible` を持たせる。aggregate は同一 cell・round の K/stock 比を作り、round 比の中央値と各腕の値を出す。図は K×throughput、ro 比率×利得、K×書込み側費用の 3 枚を raw から再集計し、PNG/PDF と provenance を一次資料に置く（`output/insights/2026-09-29/vhash-forwarding-prototype/README.md:98-101`）。md_20 の最良設定の正しさ結果が main に無い場合は、その限界を明記する。

# 6. テスト

`orchestrator/tests/test_vhash_cicada_hot_block.py` を追加し、K の値域、格子 12 cell、3 job の分割、5 round の腕順、perf/COUNT/TRACE の分離、集計の対応付け、欠落・重複・hash 不一致の fail closed、2 node 時間の見積りと縮小順を検査する。記述子更新は小さな列モデルで、先頭／途中／K 以深への挿入、CAS 失敗、ABORTED 化、GC tail 切断、K=1/2/4/8、inline ptr と reuse ptr の再利用境界を照合する。実機 smoke では `seq` が奇数の fallback、再確認失敗、install と GC の競合を重点確認する。テスト実行は本 plan 段では行わない。

共有 fixture と所有外 caller の追随は `orchestrator/tests/test_ccbench_spawn_sites.py:38-98` の新起動箇所、`test_condition_meaning_gate.py:47-71,189-202` の登録集合・site 件数、`test_p3_build_authority_cli.py:161-183,1240-1271` の materializer 集合、`test_p3_s4_loop.py:8551-8557` の patch token 許可で閉じる。既存 verifier fixture や verifier 本体は変更しない。完了段では関連テストを `tools/run_tests.py` 経由で実行し、`tools/check_codex_agents.py`、`tools/check_docs.py`、commit 後の `tools/check_ai_provenance.py` を実行する（`AGENTS.md` のクラス 2/3 完了規律）。

# 7. 分割

所有 path を重ねず、依存順を U1→U2→U3 とする。

1. **U1:** `patches/cicada-vhash-hot-block-variant.patch`、新規 `patches/broken-cicada-vhash-*.patch`、`patches/README.md` の節、条件 gate 関連 3 production file と登録簿の既存 4 test。macro 名、WL flag、記述子・JSON の schema をここで固定する。
2. **U2:** 新 driver、`orchestrator/tests/test_vhash_cicada_hot_block.py`、新作図生成器。U1 の schema と gate を利用する。
3. **U3:** `output/insights/2026-09-29/vhash-hot-block-cicada/` の raw 参照・README・図・provenance、`docs/spool/` の worklog/decisions fragment。smoke、trace、壊し、計測の順に証拠を記録する。`patches/ledger.json` は entry 1 件固定なので変更しない（`output/insights/2026-09-29/vhash-cicada-verifier/README.md:58-60`）。

# 8. brief への異議

| 番号 | 裁定 |
|---|---|
| P1 | **修正案:** 記述子のみには賛成。seqlock 下でも C++ data race を避けるため、件数・wts・ptr を atomic にする。`include/version.hh:27-30`。 |
| P2 | **賛成、条件付き:** 奇数・変更時の stock fallback は妥当。ただし ptr の dereference は seq 再確認後。`transaction.cc:102-107`。 |
| P3 | **修正案:** install と GC の全公開 site を lock 内に入れる。ABORTED も物理列の要素として数える場合にだけ不変条件が成立する。`transaction.cc:516-525,835`。 |
| P4 | **反対:** ABORTED の hot 削除は物理列との一致を破り、`later_ver` を変えうる。削除せず status を既存第 2 段で飛ばす。`include/transaction.hh:343-349`、`transaction.cc:108-126`。 |
| P5 | **修正案:** hot で見つけた版の直前の**物理** ptr を `later_ver` とし、cold は hot 末尾から開始。`transaction.cc:102-107,543-550`。 |
| P6 | **修正案:** 「選ばれないはず」だけで済ませず、GC の tail 切断と hot 更新を同じ hot lock に含め、再利用前の除去を確認する。`transaction.cc:831-840`、`include/transaction.hh:173-197`。 |
| P7 | **修正案:** 3 macro と inert 方針に賛成。WL の実装には共通 `include/ycsb.hh:55-84,97-115` への hunk と YCSB owner TU の witness が必要。site 数は patch 完成後に exact に数える。 |
| P8 | **賛成:** snapshot の古さは GC 軸で扱う。ただし `gc_inter_us` は snapshot 年齢そのものではない。実測の年齢が取れない場合は「GC 間隔別」と表記する。`output/insights/2026-09-29/vhash-readonly-share/README.md:72-75`。 |
| P9 | **修正案:** 12 cell×5 腕×5 round は採用可能。5 round は同一 job 内で stock と K を交互にする。見積り更新と事前縮小規則を付ける。`output/insights/2026-09-29/vhash-forwarding-prototype/README.md:115-129`。 |
| P10 | **修正案:** K1/K8 の trace に賛成。B2 は validation に止められる可能性があるので、ro cell と発火・commit・帰属を別記録する。巡回 0 は indeterminate。`transaction.cc:543-570,929-942`。 |

## 総括

最優先の設計修正は、ABORTED を hot に残して物理列との一致を守り、記述子を atomic にすること。install・GC の列変更を key ごとの hot lock 内に収め、第 1 段だけを置換すれば stock の版選択と validation の開始点を保てる。推測を含む投入前見積りは約 0.94 node 時間で、上限超過時の縮小順も固定した。本段は read-only の静的 plan であり、build・テスト・実測は行っていない。