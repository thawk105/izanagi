## 仕様への所見

草案 v1 のまま実装すると、forwarding 後の検証に穴が残る。

| 箇所 | 草案への修正 |
|---|---|
| 可視版の探索 | 物理位置 `p` は pending・aborted を含め、`latest_` を位置 1 として数える。ただし stock の `read_internal` は「`wts > ts` を飛ばす」処理と pending を待つ処理が分かれている。候補 `ts′` の事前確認では、**候補時刻で可視な committed/deleted 版を先頭から探索**し、候補以下の pending に遭遇したら待たずに競合失敗とする。探索中の `nullptr` も失敗として扱う。根拠: `external/ccbench/cc/cicada/transaction.cc:102–126`、草案:21–27。 |
| `later_ver_` | 成功時は read set と write set の全要素を `nullptr` にする。`validation` と `precheckInValidation` がこれを探索開始点として使うため、旧時刻の値を残せない。失敗時は集合も時刻も変更しない。根拠: `transaction.cc:498–508,543–550`、`include/transaction.hh:275–281`。 |
| 書込み版 | 成功時、未設置の `new_ver_` の **atomic `wts_`** を全件書き換える。生成源は通常・inline・GC 再利用の三つで、いずれも同じ `Version` に着地する。`INSERT`/`DELETE` は対象外とする。根拠: `include/transaction.hh:217–245`、`include/version.hh:25–30,85–90`、`transaction.cc:300–408`。 |
| 書込み制約 | RMW は先頭版の `wts`、blind UPDATE は候補時刻の可視版の `rts` と状態を確認する。`update()` の早期 abort を既に受けた tx は forwarding の対象にせず、そのまま abort させる。事前確認は最終保証ではなく、`precheckInValidation` と pending 設置後の検証を候補時刻で必ず実施する。根拠: `transaction.cc:242–287,463–593`、`include/transaction.hh:247–307`。 |
| scan・read-only | `scan()` も `read_internal` を呼ぶので、専用の「scan 中」状態で発火を抑止する。read-only は `rts_` を使い、commit 時に検証しないため対象外。`INSERT`/`DELETE` を一度でも行った tx も以後対象外とし、それ以前に前進済みの tx で特殊操作を許さないよう、対象範囲を **通常 YCSB の READ/UPDATE/RMW** に限定する。根拠: `transaction.cc:410–460,919–957`、`include/ycsb.hh:117–147`、草案:14。 |
| 時刻・GC | `ts′=(clock(v_h)+(thid≤low8(v_h)))<<8\|thid` を overflow 検査付きで求め、成功時に `localClock_` を少なくとも `clock(ts′)+1` に上げる。`clockBoost_` は変更しない。次回 `generateTimeStamp()` はさらに boost を足すため前進先との重複を避けられるが、草案:46–47 の stock 固有の重複疑いは別件として残す。`ThreadWtsArray`/`ThreadRtsArray` は変更しない。古い `ThreadWtsArray` が GC の保護下限を保守的に保つ、という論証はコード上の `MinWts`/`MinRts` 計算に依存する。根拠: `include/time_stamp.hh:24–40`、`transaction.cc:34–43,745–760,806–857`、`util.cc:281–322`。 |
| F の再試行 | F 発火時は `status_=aborted` として read を戻す。YCSB は `abort()` 後、同じ procedure を `RETRY` から新しい `begin()` で再実行する。終了要求まで再試行し得るので、長い thread の commit/abort と F abort を別計数する。根拠: `include/ycsb.hh:108–169`、草案:51–53。 |

**仕様差分として追加する条件:** forwarding は「まだ共有版を設置していない、通常 YCSB の read-write tx の単一キー read」に限る。候補確認は読み取った各版の同一性と write set の制約を検査し、成功後も stock validation を省略しない。事前確認中に pending、欠損、時刻 overflow、対象外操作を見つけた場合は、旧時刻の stock 探索に戻る。根拠: `transaction.cc:79–138,463–609`、草案:21–44。並行実行下の正しさは静的検査だけでは確定しない。

## 単位 A プラン

所有物は `patches/cicada-forwarding-variant.patch` の unified diff 一つ。CCBench pin `68106660686232781bca3be792a750d3e19d7a8a` に適用する。既定無効の全追加を前処理分岐内に置き、stock と比較する `transaction.cc`・`ycsb_cicada.cc` の前処理結果を変えない。根拠: brief:6,26–30,47。

**macro を三つに抑える案を推奨する。** `CICADA_FWD_ENABLE=0/1`、`CICADA_FWD_COUNT=0/1`、`CICADA_LONGTX=0/1`。C/F は compile 値で分けず、`ENABLE=1` の中で実行時 `--cicada_fwd_policy=c|f` を選ぶ。これなら各 macro の gate 対比が現行 witness の `1` 対 `0` に一致する。`--cicada_fwd_k=3`、`--cicada_long_threads=0`、`--cicada_long_ops=1000`、`--cicada_long_wait_us=0` を追加する。`COUNT=1` は `ENABLE=1` と `LONGTX=1` を build 契約で要求する。根拠: gate `condition_meaning_gate.py:1219–1242`、brief:39–45,52–59。C/F を単一 macro の値 `1/2` とする案は、現行 meaning witness が `requested=1, default=0` しか宣言できず、F 側の正確な admission を得られないため採らない。

- `transaction.cc:19–27` 付近: `ENABLE` 内に gflags 定義、`COUNT` 内に thread ごとの計数構造・集計構造・終了時出力を置く。thread local に保持し、worker 終了時に thread ID の専用 slot へ移し、process 終了時に **`CICADA_FWD_V1 ` に続く JSON 1 行**を出す。JSON は `schema`, `policy`, `k`, `by_class.normal|long` の `commits`, `aborts`, `f_aborts`, `eligible`, `attempts`, `success`, `failed_read_mismatch`, `failed_write_constraint`, `failed_conflict`, `ineligible`, `advance_clock_sum`, `position_before_sum`, `position_after_sum` と、各 thread の同項目を持つ。計数は tx オブジェクトまたは thread local とし、共有版へ追加しない。根拠: `transaction.cc:19–27`、`include/transaction.hh:38–66`、`common/runner.hh:172–195,294–332`。**終了時 callback の登録順と thread local 破棄順は smoke で確認する。**
- `transaction.cc:79–138`: `ENABLE` 内で `read_internal` の探索位置を数える。`p>K` となった時だけ、scan 中・read-only・特殊操作済みを除外し、C は先頭 K 版の最古 committed 版を候補にする。確認成功なら上記仕様差分に従って時刻とローカル集合を更新して先頭から再探索、失敗なら元の探索を続ける。F は abort 状態にして返す。K=0 や過大 K は起動時に拒否する。根拠: `transaction.cc:79–138`。
- `transaction.cc:144–190,410–460`: read 呼出しと scan 呼出しを区別する状態を `ENABLE` 内だけで追加し、scan 終了・早期 return でも解除する。`read()` は F abort 後に未初期化 `body` を使わない呼出し契約に合わせる。根拠: `transaction.cc:144–190,410–460`、`include/ycsb.hh:121–127`。
- `transaction.cc:196–298,300–408`: `update()` の早期 abort 状態を尊重し、INSERT/DELETE の対象外状態を記録する。`new_ver_->wts_` 書換は前進成功時に全 write element へ行う。根拠: `transaction.cc:196–408`。
- `transaction.cc:463–609,745–773,919–958`: validation 本体は改変せず、前進後の最終時刻で走らせる。abort/commit の分類計数をここで行う場合、YCSB の再試行による二重計数を避ける。根拠: 同各行。
- `ycsb_cicada.cc:23–52`: `LONGTX` 内だけで Cicada 専用 workload 型を定義し、`ccbench::run<TxExecutor,TransactionStatus,LongYcsbWorkload>` に差し替える。`prepare()` で thread ID を保存し、末尾 L 本を長い thread とする。thread 0 は leader のまま。通常 thread は既存 procedure と retry 手順を維持する。操作数型は長い thread に 1000 ops、rratio 90、少なくとも一つの WRITE を与える。待機型は **10 READ と一つの WRITE を済ませてから** 1000 µs 待ち、新たな read をせず commit する。これにより read-only 除外で実験が空にならず、待機中には発火しない。`include/ycsb.hh` と `common/runner.hh` は変更しない。根拠: `ycsb_cicada.cc:23–52`、`include/ycsb.hh:55–170`、`common/runner.hh:169–195,263–285`、メモ §16:908–932。

**注意:** `include/transaction.hh` に新 macro の `#if` を置くと、複数 TU に展開され owner TU が一意でなくなる。状態や helper は原則 `transaction.cc` の file scope に閉じ、header を触る場合も macro 条件を置かない設計を先に検討する。根拠: `condition_meaning_gate.py:1111–1142`、`include/transaction.hh:38–66`。

## 単位 B プラン

`orchestrator/campaign/vhash_forwarding_prototype.py` に `smoke`, `run`, `aggregate` を設ける。`smoke` は pin、patch 適用、gate 2 腕、inert 前処理比較、最小実行を順に行う。`run --workload normal|many_ops|wait_after_reads --output ...` は 1 workload・1 node を担当し、`aggregate` は JSON だけを読み図入力を作る。`patchharness.checkout()` の中で `applied()` を使い、個別 build dir に CMake を構成して `ycsb_cicada.exe` のみ build する。根拠: `patchharness.py:246–263,345–364`、brief:42–50、`cc/cicada/CMakeLists.txt:1–14`。

build は stock perf、C/F 共用 perf、C/F 共用 count の **3 種**を基本とする。同じ binary でも C/F の各実行値について gate 証拠と binary hash を記録する。stock は `ENABLE=0,COUNT=0,LONGTX=1`、perf は `1,0,1`、count は `1,1,1`。C/F は `--cicada_fwd_policy` だけを変える。stock も長い workload が必要なので `LONGTX=1` とする。count build の throughput は必ず `perf_eligible=false` とし、性能比較に混ぜない。根拠: brief:23–24,39–45、`common.txt:23–27`。

条件は 48 thread、100 万件、zipf 0.9、rratio 50、max_ope 10、3 秒、2100 clocks/µs、NUMA interleave、workload 3 種 × GC 間隔 10/100/1000 µs × stock/C/F。各条件の perf は 3 rep、順序を `stock,C,F` → `C,F,stock` → `F,stock,C` と回す。count は C/F を各 1 rep。K=1,8 は many_ops・GC=100 で追加する。各 run の直前と job 冒頭に競合 binary の PID を調べ、検出・probe 失敗なら停止する。根拠: brief:42–49、`calibrator/runner.py:382–405`。

run JSON の最小 schema は `schema_version`, `source_pin`, `patch_sha256`, `driver_commit`, `binary_sha256`, `build_kind`, `perf_eligible`, `verification_status:"未検証の診断値"`, `workload`, `gc_inter_us`, `k`, `policy`, `rep`, `order_index`, `argv`, `node`, `start/end`, `exit_code`, `stdout_sha256`, `throughput`, `counter_json`, `gate_receipts`, `inert_receipt`, `competing_probe`。raw stdout/stderr も hash 付きで保存し、parser は `CICADA_FWD_V1 ` が count run でちょうど 1 行か確認する。検査器が導入された場合だけ別の検証状態を追加し、anomaly は失格にする。根拠: `md_6.txt:14–24`、`common.txt:30–36`。

`make_figures.py` は raw JSON から集計を再計算し、成功率、失敗理由、throughput 比の図を PNG/PDF で出す。各図の provenance JSON に入力 path・SHA256・条件・主要値を記録する。3 rep の点には小標本用 95% CI を描き、count 1 rep の内訳には `n=1` を明記する。保存前に bbox overlap を検査し、実データの全図種を計測機外で生成する。根拠: `FIGURE_CONVENTIONS.md:23–37,65–114`。

軽い pytest は、(1) 条件行列・順序回転、(2) count throughput の除外、(3) counter 行の重複・欠落・不整合拒否、(4) 競合 PID・probe 失敗での停止、(5) gate 未 admitted で build に進まないこと、(6) provenance の入力 hash 拘束、(7) 作図の実寸 fixture と本物の Figure の保存前検査、を `test_vhash_forwarding_prototype.py` に置く。いずれも fake process / fixture を使い、build・計測を起動しない。根拠: `FIGURE_CONVENTIONS.md:96–114`、brief:69–72。

投入 argv の形は次とする。walltime は smoke 20 分、各 workload job 30 分を初期上限とし、実測後に見直す。`generic` は shell を使わず argv をそのまま実行する。根拠: `dispatch_compute.py:66–75,114–160,1566–1576,4727–4764`。

```text
python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:20:00 -- python3 -m orchestrator.campaign.vhash_forwarding_prototype smoke
python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:30:00 -- python3 -m orchestrator.campaign.vhash_forwarding_prototype run --workload many_ops --output output/env/pegasus/vhash-forwarding-prototype/many_ops.json
```

## gate 登録

**P8～P10 の重大な差分:** `_DEFINE_SPECS` に Cicada entry を加えるだけなら `make_define_request(protocol="cicada")` は `request-contract-invalid` で拒否される。現状は `silo` と特例 `mocc/BACKOFF_FIXED` だけを通す。よって brief の「自分の entry だけ」「意味論・判定は変更しない」と、「Cicada の 2 腕を admitted にする」は同時には満たせない。`make_define_request` の protocol 許可を **登録済み Cicada macro に限って**拡張する修正が段 5 の前提であり、既存 `silo`/`mocc` の期待値は緩めない。根拠: `condition_meaning_gate.py:1111–1142`、brief:52–63。先例 `3867e6ec5` は SI entry を登録したが、commit 自身が `protocol="si"` は拒否のままと明記しており、今回の driver admission までは先例にならない。

登録案は次のとおり。site 数は **patch 完成時に added `#if` の実数へ固定する暫定値**で、指定した owner TU のみに置く。`COUNT` は `ENABLE=1` を companion define とする。根拠: `condition_meaning_gate.py:65–73,80–94,351–355,488–531,1219–1242`。

| macro | `DefineSpec(route, owner_tus, target, patch_rel, companion_defines, inert_values)` | exact witness |
|---|---|---|
| `CICADA_FWD_ENABLE` | `ROUTE_CMAKE_CXX_FLAGS`, `("cc/cicada/transaction.cc",)`, `"ycsb_cicada.exe"`, `"patches/cicada-forwarding-variant.patch"`, `()`, `("0",)` | `("cc/cicada/transaction.cc", "#if CICADA_FWD_ENABLE")` |
| `CICADA_FWD_COUNT` | 同 route/owner/target/patch、`(("CICADA_FWD_ENABLE","1"),)`, `("0",)` | `("cc/cicada/transaction.cc", "#if CICADA_FWD_COUNT")` |
| `CICADA_LONGTX` | 同 route/target/patch、owner `("cc/cicada/ycsb_cicada.cc",)`、`()`, `("0",)` | `("cc/cicada/ycsb_cicada.cc", "#if CICADA_LONGTX")` |

追随箇所は `_DEFINE_SPECS` と owner 定数 (`condition_meaning_gate.py:76–80,334–344`)、witness と実 site 数 (`:356–540`)、`make_define_request` の Cicada 許可 (`:1111–1142`)、`test_condition_meaning_gate.py` の `_COMPILE_TIME_BRANCH_MACROS` (`:47–91`)、`_NEW_BRANCH_EXPECTATIONS` (`:101–175`)、supply 完全集合・spec・件数・CXX route 件数 (`:3475–3543,3629–3634`)、docstring の `61→64` と `Forty-three→Forty-six` (`condition_meaning_gate.py:10–16,1119`; test `:3753–3756`) である。`test_ccbench_spawn_sites.py` の patch inventory (`:2917–2938`) は登録で整合させ、sink 件数の固定値 (`:3571–3582,3605–3615`) は新 macro の reachability を算出して自分の 3 entry 分だけ更新する。binary 起動 site は実装した関数名・呼出し数で `_DIRECT_CCBENCH_DIAGNOSTIC_SITES` (`:77–91`) へ登録する。`test_p3_s4_loop.py:8547–8705` は本案の macro に `IZANAGI_` がないため変更不要で、単なる回避として扱わず gate に全件登録する。根拠: `test_ccbench_spawn_sites.py:657–748,2917–2938`、先例 `3867e6ec5` の 6-file diff。

driver は `silo_policy_coverage.py:308–360` と同形で、各 macro の `capture_define_inputs` → `make_define_request` → compile commands → supply/meaning → `require_condition_gate_family` を実施する。C/F runtime policy は同一 `ENABLE=1` の binary なので、gate receipt は compile 条件へ束縛し、実行時 policy 値は run JSON に別記する。`cc/cicada/CMakeLists.txt:1–14` は target を宣言するが、gate の owner compile entry 一意性・実際の admitted は静的には言えない。smoke の**最初の手**で各 macro の 2 腕を実走し、`owner-tu-unresolved` を含む拒否時は build/計測へ進まない。根拠: `condition_meaning_gate.py:2043–2073`、brief:58–63。

P2 は ledger が現在 1 entry を要求するため妥当。ただし原依頼の ledger entry と衝突するので、`patches/README.md` の登録と一次資料に理由を記す。P3 は裸 macro の検査対象が `IZANAGI_` である点だけなら通るが、**gate 登録を行うことが条件**であり、検査の代替ではない。根拠: `silo_ladder_rung1_contract.py:513–520`、`test_p3_s4_loop.py:8681–8690`、`test_ccbench_spawn_sites.py:657–748`、`md_6.txt:21–27`。

## 変異候補

段 4 で次を事前登録する。静的・login pytest が殺せるのは driver と登録契約の変異までで、C++ の意味論変異は計算ノードの smoke と将来の検査器が必要である。

| 変異位置・内容 | 殺す検査 | 単一理由 |
|---|---|---|
| driver の rep 順を常に stock→C→F に固定 | `test_vhash_forwarding_prototype.py::test_order_rotation` | 時間順の対照が崩れる。根拠: brief:30,45 |
| count build の `perf_eligible` を true にする | 同 `::test_count_throughput_is_ineligible` | 観測者効果を性能値へ混入。根拠: brief:24 |
| counter prefix の重複を最後の行で上書き | 同 `::test_counter_line_is_unique` | 壊れた出力を正常集計。根拠: 設計上の JSON 契約 |
| gate 拒否後も build を起動 | 同 `::test_gate_rejection_stops_build` | admission 境界を破る。根拠: `silo_policy_coverage.py:320–335` |
| `later_ver_` 破棄を削除 | login pytest では殺せない。計算ノード smoke の競合 fixture、後続の Cicada 検査器で検出 | 旧時刻の探索起点から新時刻の版を見落とす。根拠: `transaction.cc:498–508,543–550` |
| `new_ver_->wts_` 書換を削除 | 同上。smoke は forward 成功を伴う RMW/blind UPDATE を必須とする | 設置版の時刻と tx 時刻が乖離。根拠: `include/transaction.hh:217–245` |
| pending への遭遇を「競合失敗」から読み飛ばしに変える | 計算ノード smoke の pending 競合ケース、検査器 | 候補時刻の可視版が未確定。根拠: `transaction.cc:108–118` |
| F abort 後に `RETRY` せず return | smoke の長い thread `f_aborts>0` と commit/abort 計数 | F の比較対象が再実行を失う。根拠: `include/ycsb.hh:149–169` |

## 見積り

条件は主系列 3 workload × 3 GC ×〔perf 9 run＋count 2 run〕＝**99 run**、K 追加は 2 K ×〔perf 9＋count 2〕＝**22 run**、計 **121 run**。3 秒の本走だけで 363 秒、これに DB 初期化、process 起動、単独性 probe、3 build/job、gate configure・前処理を加える。根拠: brief:42–46、`common/runner.hh:294–300`。**build 1 回、初期化込み run 1 回の実測値は未取得**なので、brief の「各 job 20～25 分」は仮見積りである。仮に build 3 分、run 8 秒なら、通常・待機型各 `3×11×8秒 + 3×3分 ≈13.4分`、操作数型 `55×8秒 + 9分 ≈16.3分`、smoke 15 分で合計約 **58 分の node 時間**。gate や長い tx の待機で倍化しても 2 node 時間未満を見込むが、smoke で所要を測り直す。根拠: brief:45–46,61–63。

2 node 時間に迫る場合は、まず K=1,8 の補助系列、次に GC=1000 の補助的な count run を削り、主比較の stock/C/F 同時刻 3 rep は維持する。投入前に `実測 build 秒×build 数 + 実測 run 秒×run 数 + gate/初期化` で再積算し、2 node 時間以上なら common の指示どおり停止する。根拠: `common.txt:22–27`。

## 未解決

1. **gate の Cicada protocol 許可は、brief P8 の「自分の entry だけ」を超える。** 上記の限定拡張を段 4 の確定事項にしない限り、段 5 の driver は admitted を得られない。根拠: `condition_meaning_gate.py:1111–1127`、brief:52–63。
2. `transaction.cc` だけで counter を process 終了後に 1 行へまとめる方法は、thread local の破棄順と `atexit` callback を smoke で確認する必要がある。確認できなければ per-thread JSON 行と driver 集計へ仕様変更する。根拠: `common/runner.hh:281–300`。
3. `test_ccbench_spawn_sites.py` の cross product 固定件数と、patch 内 `#if` site 数は完成した diff から確定する。現時点で数値を決め打ちしない。根拠: `test_ccbench_spawn_sites.py:3571–3615`、`condition_meaning_gate.py:488–531`。
4. Cicada の正しさ検査器はこの wave の前提にない。smoke が完走しても serializability は証明できず、結果はすべて「未検証の診断値」とする。根拠: `md_6.txt:19`、`common.txt:30–33`。

## 総括

実装の中心は、**単一キー read で K を越えた時だけ候補時刻を選び、既読・書込み制約を確認し、成功後も stock validation を最終時刻で通す**ことにある。段 5 に進む前に、Cicada を gate の request として受ける限定修正、macro 三つの owner TU、counter 出力契約を段 4 で固定する。今回行ったのは指定資料と pin の静的検査だけであり、patch 適用・build・pytest・計測の実測は行っていない。