結論から言うと、正式な段 7 の比較には案 A が必要です。案 B が規律 2 と整合できるのは、certified 比較から機械的に隔離された偵察用途に限られます。案 A の初手は ERMIA より MOCC を推奨します。

以下は ccbench pin `d706650cdb31e442bef45b9b4216951d4fb40969` の静的読解結果です。編集・commit・テスト実走はしておらず、緑は主張しません。

### 現行コードから確定した写像

| protocol | commit/version 写像 | 根拠 |
|---|---|---|
| Silo | native `(maxtid.epoch, maxtid.tid)` | `external/ccbench/cc/silo/transaction.cc:575-606` |
| SI | `(1, cstamp_)` | `external/ccbench/cc/si/transaction.cc:526-553` |
| ERMIA parallel（現行 active） | `(1, cstamp_)`。版にも raw `cstamp_` を格納 | `external/ccbench/cc/ermia/transaction.cc:594-606,755-767,905-913` |
| ERMIA serial（現行 dormant） | `(1, uint32_t(cstamp_ << 1))` | `external/ccbench/cc/ermia/transaction.cc:503-561` |
| MOCC | native `(maxtid.epoch, maxtid.tid)` | `external/ccbench/cc/mocc/transaction.cc:1017-1064` |

ERMIA の本当の難所は active path の 1-bit shift ではなく、`read_internal()` が一部の成功 read を `read_set_` に入れない点です。`v_sstamp` が既に確定 stamp の場合は `transaction.cc:162-168` の else に入り、現行 SI 型の「commit 時に read_set を列挙」では依存辺が脱落します。

## 案 A: 別 protocol への trace-hook 移植

### A-1. 編集面

#### trace 完全性と verifier の共通改修

S1 と同時に直すと明記された既知 false-green があるため、単に候補 protocol へ現行 C/R/W をコピーするだけでは不十分です。

| file:line | 変更 |
|---|---|
| `external/ccbench/include/trace.hh:17-23,25-124` | trace v2 を定義。各ファイルに schema header、`C` に期待 R/W 件数、全 txn-scoped event 後に `E` 終端と実件数を出す。ERMIA 用の `#if TRACE` 内 pending-read buffer もここへ置く。 |
| `external/ccbench/cc/silo/transaction.cc:584-624,630-686` | `C` 件数を渡し、R/W/X を出し終えた `:684` 付近で `E` を出す。既存 lock-shadow 検査は維持。 |
| `external/ccbench/cc/si/transaction.cc:526-554` | SI hook を trace v2 の C/R/W/E へ更新。 |
| `orchestrator/verifier/parse.py:4-28,89-225` | v2 header、C 件数、E、開いたまま EOF、新しい C が前 txn を追い越す場合、件数不一致を fails-closed で収集。 |
| `orchestrator/verifier/model.py:132-150,154-203` | `incomplete_txns`、`event_count_mismatches`、`commit_count_mismatch` を `Integrity.clean()` に追加。 |
| `orchestrator/verifier/core.py:17-113` | 上記 issue を構造化 integrity へ配線。新規 certified 経路では独立 commit 数が無い trace v1 を認証しない。 |
| `orchestrator/verifier/report.py:42-74,95-114` | JSON/text に新 integrity reason と trace schema を出す。 |
| `orchestrator/verifier/cli.py:28-72`、`orchestrator/verifier/__init__.py:9-23` | v2/expected-commit 契約を公開。歴史 v1 は明示的 legacy reader に分離し、新 campaign へ再投入不可にする。 |
| `orchestrator/campaign/pipeline.py:223-231,261-289` | stdout の `commit_counts_` と `batch_commit_counts_` も厳密に parse。これは `external/ccbench/common/result.cc:47-49` が既に出す独立値。 |
| `orchestrator/campaign/pipeline.py:843-918` | stdout commit 合計、C 行数、complete E block 数、`vr.n_txns` の完全一致を要求。不一致は `trace-commit-count-mismatch` 等で ABORT。 |
| `orchestrator/tests/test_verifier.py:601-638` | 現在の「false-green になる」characterization 2 件を反転。末尾 txn 全欠落と C 後の R/W 欠落を indeterminate にする。 |
| `orchestrator/tests/fixtures/*/trace_*.log:1` | 既存 16 trace fixture を v2 化。`test_verifier.py:28-35` に fixture ごとの独立 expected commit 数を固定。 |

これにより、部分的な R/W 欠落は C/E 件数で、txn 全体の末尾欠落は ccbench 集計との照合で検出できます。歴史的 v1 trace を新 verifier で黙って再認証してはいけません。

#### ERMIA 固有

| file:line | 変更 |
|---|---|
| `external/ccbench/cc/ermia/transaction.cc:1-13` | `trace.hh` を include。 |
| `external/ccbench/cc/ermia/transaction.cc:24-86` | `begin()` で TRACE-only pending reads を防御的に clear。 |
| `external/ccbench/cc/ermia/transaction.cc:146-174` | 成功して返す直前に key と実際に読んだ `ver->cstamp_` をコピー。`read_set_` に入らない `:165-168` の分岐も捕捉する。 |
| `external/ccbench/cc/ermia/transaction.cc:548-587` | dormant `ssn_commit()` に C/R/W/E。C/W は実際に格納した shifted `verCstamp` を使用。 |
| `external/ccbench/cc/ermia/transaction.cc:710-800` | active `ssn_parallel_commit()` の committed path、set clear 前に C/R/W/E。C/W は raw `cstamp_`。`:710-727` の abort pathでは emit しない。 |
| `external/ccbench/cc/ermia/transaction.cc:809-853` | `abort()` でも pending reads を clear。 |
| `external/ccbench/cc/ermia/transaction.cc:905-913` | コード変更は不要だが、active 経路が parallel のみであることを静的テストで固定。 |

`external/ccbench/cc/ermia/include/version.hh:9,18-24,92-99` の `TIDFLAG` は主に `Psstamp.sstamp_` の表現です。active version cstamp に一律 shift を適用してはいけません。

#### MOCC 固有

| file:line | 変更 |
|---|---|
| `external/ccbench/cc/mocc/transaction.cc:1-13` | `trace.hh` を include。 |
| `external/ccbench/cc/mocc/transaction.cc:1017-1071` | `maxtid` を各 tuple に格納した後、set clear 前に C/R/W/E。read version は validated `read_set_` の Tidword、write version は `maxtid`。 |
| `external/ccbench/cc/mocc/include/tuple.hh:14-31,74-82` | 変更不要。既に verifier と同じ `(epoch,tid)`、genesis `(1,0)`。 |
| `external/ccbench/cc/mocc/transaction.cc:156-268,888-953` | 変更不要。成功 read は両ロック形態とも保存され、同じ set が validation に使われる。 |

MOCC は ERMIA のような補助 read buffer が不要で、Silo 先例との差分が小さい候補です。

#### 遺伝子空間、source identity、allowlist

| file:line | 変更 |
|---|---|
| `orchestrator/campaign/genome.py:74-96` | `ERMIA_SPACE` と `MOCC_SPACE` を追加し `SPACES` へ登録。ERMIA は `BACK_OFF × KEY_SORT` = 4、MOCC は `BACK_OFF × KEY_SORT × TEMPERATURE_RESET_OPT` = 8。 |
| `external/ccbench/cc/ermia/CMakeLists.txt:1-8` | 変更不要。BACK_OFF は universal、KEY_SORT は既に供給。 |
| `external/ccbench/cc/mocc/CMakeLists.txt:1-10` | 変更不要。`RWLOCK` は bare fixed define なので genome 軸に入れない。 |
| `orchestrator/campaign/source_digest.py:73-82` | `EVOLVE_BLOCK_SOURCES_BY_PROTOCOL` と `ALLOWLIST_BY_PROTOCOL` を導入。Silo 定数は歴史 consumer 用 alias として残す。単純な全 protocol union は、別 protocol の dirty source を digest 外で許すため不可。 |
| `orchestrator/campaign/source_digest.py:560-566,640-746` | conditional guard、compute、include guard、diff-of-diffs、baseline を `genome.protocol` の対象集合で回す。 |
| `orchestrator/campaign/source_digest.py:620-637` | 既存 protocol CMake 解決を再利用し、`Options.cmake` と `cc/<protocol>/CMakeLists.txt` の実効入力/raw digest も identity に加える。`docs/phase3.md:888-895` の既知の Options 偽-hit をここで閉じる。 |
| `orchestrator/campaign/source_digest.py:791-890` | allowlist 検査へ genome/protocol を渡す。候補外の dirty file は停止。 |
| `orchestrator/campaign/buildcache.py:653-656,825-828` | protocol-aware allowlist 呼出しへ変更。 |
| `hooks/guard_write.py:36-38,118-131` | protocol map の写しと、hook 用 designated-path union を追加。build 時の protocol-specific gate が一次防壁。 |
| `hooks/README.md:48-52`、`orchestrator/tests/test_hooks.py:338-340` | 正本との map/union 一致を固定。 |
| `orchestrator/tests/test_campaign.py:8445-8461,8550-8626,8794-8816,9395-9447` | protocol 別 source set、allowlist、fake repo、diff-of-diffs の正負例へ一般化。 |

`trace.hh` 自体は live coder allowlist に入れません。人間レビュー済み submodule commit と pin で固定し、variant が verifier 入力形式を変異できないようにします。

#### build、pin、driver、成果物

| file:line | 変更 |
|---|---|
| `orchestrator/campaign/buildcache.py:494-515,653-668,835-848` | production 変更不要。target と binary path は既に `ycsb_<protocol>.exe` で parametric。ERMIA/MOCC の正負テストだけ追加。 |
| `orchestrator/campaign/buildcache.py:680-699,744-755,851-909,1021-1049` | perf 出口の nm に加え、`CMakeCache.txt` の `CCBENCH_TRACE=0` も要求する helper に強化。cache-hit/fresh、v2/legacy の全 4 出口で実行。 |
| `external/ccbench` gitlink | 新しい `izanagi-trace` commit へ前進。gitlink なので file line は無い。 |
| `orchestrator/campaign/pin.py:2-33` | `PREVIOUS_PIN=d706650`、`CURRENT_PIN=<new>` と履歴を更新。 |
| `orchestrator/campaign/build_admission.py:58-68,281-289` | `CROSS_PROTOCOL_CERTIFIED` generator ID を登録。policy hash 変更は content-addressed に扱う。 |
| `orchestrator/campaign/cross_protocol_calibration.py:1`（新規） | protocol/genome/pin/perf SHA を束縛した saturation、within-run、between-run floor を生成。共通比較 records は各 protocol の飽和点の保守側最大値。 |
| `orchestrator/campaign/cross_protocol_certified.py:1`（新規） | `space_for(protocol)` を列挙し、既存 `pipeline.evaluate()` の build→verify→bench→COMMIT だけを使う。独自 COMMIT writer は作らない。 |
| `orchestrator/campaign/cross_protocol_report.py:1`（新規） | 全 arm に certified COMMIT、同一 workload、protocol 別 calibration/floor、pin/binary/source receipt がある場合だけ比較表へ載せる。 |
| `docs/phase3.md:269,349-355,375-383,888-899` | S1 完了条件、対象 space、protocol 別床、trace completeness debt の閉鎖を記録。 |
| `docs/ccbench-anatomy.md:125-128,132-168,210-213` | ERMIA active mappingを訂正し、MOCC space と新 trace schema を記録。 |
| `docs/decisions.md:12548` | 選択 protocol、版写像、trace-v2、v1 historical boundary、pin 前進を新規 decision として追記。 |

pin 前進では `orchestrator/campaign/s8b_approved.py:28-30,65-67` の d706 SHA は凍結値として残し、`orchestrator/tests/test_s8b_approved.py:49-64` を「歴史承認 pin」と「現行 gitlink」の独立検査へ分離します。`orchestrator/tests/test_s6_sort_sweep.py:353`、`test_p3_s4_loop_sort.py:334`、`test_p3_s4_loop_trigger_gating.py:1825`、`test_s8a_trigger_sweep.py:431` の現行 pin drift-killer は裁定付きで更新します。一方、`silo_ladder_rung1.py:49`、`patches/ledger.json:6-18`、既存 S-1/8b の証拠 pin は `pin.py:11-18` の規約どおり変更しません。

### A-2. 実装コスト

先例との差分見積りです。計測時間は含みません。

| 候補 | 差分 | 見積り |
|---|---|---|
| MOCC を最初に載せる | Silo と同型の Tidword、validated read_set、commit 1 経路。共通 trace-v2、source registry、pin、driver/report が主コスト | 5〜8 人日 |
| ERMIA を最初に載せる | 共通改修に加え、read_set 非収録分岐、TRACE-only buffer、active/dormant 2 実装、異なる cstamp domain | 7〜11 人日 |
| 共通基盤後の追加 | MOCC 1〜2 人日、ERMIA 2〜4 人日 | protocol 別校正・計測時間は別 |

したがって「SI があるので二本目は安い」は hook の構文だけには当たりますが、certified S1 全体には当たりません。

### A-3. 検証可能性

既存機械検査として使えるものは次です。

- verifier fixture と三値判定: `orchestrator/tests/test_verifier.py`
- trace-empty、verify reject、COMMIT 不在: `orchestrator/tests/test_campaign.py:6096-6202`
- COMMIT が certified branch 内だけにある AST gate: `orchestrator/tests/test_campaign.py:6323-6378`
- nm 漏洩検査: `orchestrator/tests/test_campaign.py:214-219`
- diff-of-diffs: `orchestrator/tests/test_campaign.py:9395-9447`
- build target/path: `orchestrator/tests/test_buildcache_v2.py:175-247,721-722`
- hook/source registry drift: `orchestrator/tests/test_hooks.py:338-340`

新規に必要なのは以下です。

- `orchestrator/tests/test_cross_protocol_trace_hooks.py:1`: 全 hook が `#if TRACE` 内、ERMIA の成功 read 両分岐、begin/abort reset、active commit が parallel のみ、MOCC が保存済み Tidword を使うことを固定。
- `orchestrator/tests/test_cross_protocol_pipeline.py:1`: ERMIA/MOCC の non-empty trace、integrity clean、target build→verify→bench→COMMIT、wrong-shift・read 欠落・stdout/trace count 不一致が ABORT。
- 旧 pin と新 pinについて、対象 TU の実 compile command で `TRACE=0` preprocessed translation unit が同一であることを比較する一回限りの observer-effect admission test。
- ERMIA は overwritten-version 分岐を確実に踏む正例、誤った SI-copy hook が orphan/missing-read で赤になる負例。
- SI write-skew が引き続き G2、stock ERMIA/MOCC が serializable、mapping mutant が integrity red になる protocol 別 positive/negative control。

確認できない部分もあります。静的検査と有限 workload では、任意の将来変異について「全 logical read が必ず trace された」と数学的には証明できません。MOCC は protocol 自身が検証する read_set と trace source が同じなので比較的強い一方、ERMIA の補助 buffer は追加 TCB です。ERMIA は hidden-read 分岐の実走正例なしでは受理すべきではありません。

### A-4. 規律との整合

規律 1について、全計装と pending buffer を `#if TRACE` 内に置き、trace/perf は既存どおり別 build・別 run とします。nm は protocol 非依存でそのまま効きます。diff-of-diffs は protocol-aware source registry へ直した後は効きますが、現状の Silo 固定のままでは ERMIA/MOCC を検査していません。

既存 diff-of-diffs は「新 pin 内の stock hookが無害か」までは証明しないため、旧 pin対新 pinの TRACE=0 translation-unit 同一検査が必要です。nm 単独には strip、inline、別 namespace の計装を見逃す穴があります。

規律 2については、trace-v2 の完全性、stdout commit 数照合、candidate-specific red controlを通したうえでのみ整合します。どの verify pass でも anomaly/integrity failure があれば既存 `pipeline.py:908-918` で ABORTし、fitness/COMMITを出しません。

規律 3についても、追加 integrity reasonを WAL の structured abortへ流すため既存の次手シグナルを維持できます。

### A-5. 成果物への影響

- certified 選択結果: 受理集合に、全 verify pass を通った ERMIA/MOCC genomeだけが追加される。
- 材料レポート: 両 protocolに対称な verifier、calibration/floor、pin、binary/source receipt参照が付く。
- 試行台帳: 候補 protocolにも BUILD→VERIFY→BENCH→COMMIT、失敗時は構造化 ABORTが記録される。

## 案 B: stock 専用の偵察計測経路

### B-1. 編集面

`pipeline.evaluate()` に `skip_verify=True` を足す設計は採りません。公式 WAL と別の探索 namespace・別 schema・別 runtime typeを作ります。

| file:line | 変更 |
|---|---|
| `orchestrator/campaign/cross_protocol_stock_scout.py:1`（新規） | `STOCK_PROTOCOLS={"ermia","mocc"}` の閉 registry。`Genome(protocol,{})`、現行 exact pin、`src_token=="stock"`、`tracked_clean=True`、`trace=False` のみ許可。Silo参照も同じ時間窓で trace-disabled binaryを再計測する。 |
| `orchestrator/campaign/stock_scout_ledger.py:1`（新規） | `runs/stock-scout.jsonl` 用の別 schema/runtime type。event は START/MEASURED/FAILED のみ。`STAGE_COMMIT`、`certified`、`fitness_tps` を schemaで禁止。 |
| 同上 | 各測定に `correctness_status:"not-evaluated"`、`eligible_for_certified_selection:false`、`eligible_for_headline:false`、protocol、pin/source receipt、binary SHA、TRACE=0、argv、全標本、CV、calibration/floor refを必須化。 |
| `orchestrator/campaign/stock_scout_report.py:1`（新規） | 探索 artifact exact typeだけを読む。数値表には常に「Izanagi correctness未検証・偵察専用」。winner/selected/certified/headlineという verdictを生成しない。 |
| `orchestrator/campaign/layout.py:430-465` | `ExplorationCampaignLayout.stock_scout_ledger_file` を追加。既存 `wal_file` は使わない。 |
| `orchestrator/campaign/build_admission.py:58-68,281-289` | `CROSS_PROTOCOL_STOCK_SCOUT` generator IDを登録。実際の source classは clean current pinなので `STOCK_BASELINE` のまま。 |
| `orchestrator/campaign/buildcache.py:680-699,744-755,851-909,1021-1049` | 案Aと同じ TRACE=0 CMakeCache + nm のperf contract強化。 |
| `docs/orchestrator-design.md:110-123` | stock scoutのnamespace/schemaと「公式consumerへ流さない」境界を追記。 |
| `docs/phase3.md:269,349-352,375-383` | BはS1解消や段7 certified比較ではなく、候補選定用偵察だけと明記。 |
| `docs/decisions.md:12548` | この隔離条件とpromote禁止を裁定として記録。 |
| `orchestrator/tests/test_cross_protocol_stock_scout.py:1`（新規） | dirty source、非stock flags、TRACE=1、未登録protocol、rep失敗、非finite値を拒否。公式WAL/COMMIT/fitnessが一切出ないことを固定。 |
| `orchestrator/tests/test_p3_exploration_namespace.py:303-310,353-431` | official consumerがstock-scout artifact/rootを拒否する正負例を追加。 |
| `orchestrator/tests/test_campaign.py:6323-6378` | AST gateへ「scoutはpipeline.evaluate、wal.log、STAGE_COMMITを参照しない」を追加。 |

`genome.py:87-96` の `SPACES` は変更しません。stockは空 flagsの閉 registryであり、探索空間ではないためです。

`source_digest.py:73-82` も変更しません。現行集合は候補sourceのdiff-of-diffsには使えませんが、Bは exact Git commitかつtracked cleanだけを許し、commit SHAがtree全体を束縛します。dirty candidate sourceを受け入れた時点でこの根拠は失われるため、即停止です。

build targetは既に `buildcache.py:500,667,835-848` でparametricなのでproduction変更は不要です。

### B-2. 実装コスト

C++、verifier、genome space、submodule pin変更はありません。一方、規律2と整合する隔離は単なる一分岐ではなく、driver・ledger・strict loader・report・negative testsが必要です。

- 厳格なstock scout経路: 3〜5人日
- raw値だけを外部一時領域へ出す最小probe: 1〜2人日。ただし比較表、順位、材料レポートには使用不可
- protocol別calibration/floorの実測時間は別

### B-3. 検証可能性

確認できるもの:

- exact current pin、clean tree、stock flags、TRACE=0 build
- buildcacheのCMakeCache/nm検査
- 同一workload・同一records・同一時間窓・全rep成功
- exploration namespace、別ledger、official consumer拒否
- certified selection/WAL/fitnessへの到達不能

確認できないもの:

- 候補runのserializability、trace integrity、anomalyの不存在
- protocol固有の実装bugや今回のworkloadだけで発火する正しさ違反
- 「未検証stockの高いtpsが有効な競争結果である」こと

つまりBで得られるのは性能観測であって、正しさを伴う比較値ではありません。

### B-4. 規律との整合

規律 1は、候補が無改変stock、両armがtrace-disabledの別run、同一時間窓である限り保てます。既存nmは効きます。diff-of-diffsは候補targetを見ていませんが、variant diff自体を禁止し、exact clean Git treeで代替します。nm単独ではstripや匿名/inlined計装を完全には検出できないため、CMakeCacheとstock pinが必要条件です。

規律 2について、親briefの「stockをcertified外と宣言すればよい」だけでは不十分です。次の全条件を満たす場合に限り、Bは規律2に抵触しません。

1. official WAL、COMMIT、fitness、accept setと別namespace・別schema・別runtime typeである。
2. official report/selector/optimizerが機械的に拒否する。
3. stockのみで、variant生成や性能フィードバックに使わない。
4. 数値はcorrectness未評価と表示し、winner・採用・headlineを出さない。
5. 後からAを実装しても、Bの値やartifactをcertifiedへ昇格・再ラベルしない。
6. 正式比較にはA経路で新しくbuild→verify→bench→COMMITをやり直す。

この条件を一つでも外し、verifyなしの候補を正式な比較、順位、選択、headlineの片側に置けば、対抗馬だけ正しさゲートを免除するため規律2違反です。したがってB単独では段7のcertified cross-protocol比較を完成できません。

規律3については、Bをiterative synthesisやLLMの次variant生成へ接続しないことが条件です。人間が「どのprotocolのA移植に工数を使うか」を決める偵察材料に限ります。

### B-5. 成果物への影響

- certified 選択結果: 変更なし。候補protocolの受理行は増えない。
- 材料レポート: official版は変更なし。別exploration reportに未検証の生値だけを置く。
- 試行台帳: official WALは変更なし。stock-scout ledgerにはCOMMIT/certified/fitnessが存在しない。

## 第3の選択肢

「Bで偵察し、Aで本比較」は成立します。ただし第三の受理経路ではなく、実装順序です。

成立条件は、Bをexploration namespaceに閉じ、候補選定への利用をadaptive selectionとして記録し、Aの最終比較を新しい事前登録・新しい測定窓・新しいcalibration/floorでやり直すことです。Bで最速だった値をAの最終標本へ再利用するとselection biasが入るため不可です。

この段階案は、複数候補を全部移植する前に投資対象を絞る用途には合理的です。正式結果の初手としては、実装リスクの低いMOCCをAへ載せる方が直接的です。

## 親 brief の M/P 監査

| 項目 | 判定 | 実コードとの差 |
|---|---|---|
| M1 | 一部食い違い | SI hookの存在と写像は正しい。Siloの実 `#if TRACE` directiveは `transaction.cc:147,174,362,378,390,410,584,635,659,684` の10区画であり、「13箇所」はdirective数としては不正確。 |
| M2 | 一致 | `genome.py:88-96` はSiloのみ、build targetはparametric。 |
| M3 | 一致 | `_run_trace()` は `pipeline.py:283-289` でC行を数えるため、hook無しは `:868-875` のtrace-empty。COMMITはcertified後のみ。 |
| M4 | 一致、ただし限定的 | nm判定はprotocol非依存。ただし `buildcache.py:1034` 自身がstrip済みbinaryの穴を認め、diff-of-diffsの代替にはならない。 |
| M5 | 不完全 | 二定数だけの単純拡張では不十分。全protocol unionはoff-protocol dirty sourceを許す。protocol別map、全consumer、buildcache callsite、hook複製定数、Options identity gapの更新が必要。 |
| M6 | 食い違い | shifted cstampはdormant `ssn_commit:553-561` のみ。active `ssn_parallel_commit:765` はraw cstampで、`commit:905-913` はparallelだけを呼ぶ。二実装はあるが二つのactive経路ではない。 |
| M7 | 一致 | Bをofficial比較に使えば対抗馬だけverify免除となる。 |
| P1 | 一部食い違い | SI先例でhook構文は安くなるが、ERMIAのコスト増理由はactive shiftではなくhidden read-setと二実装、さらにtrace completeness debt。 |
| P2 | 食い違い | 「certified外と宣言」だけでは足りない。公式受理集合・順位・headlineから機械隔離されたscoutに限り整合する。 |
| P3 | 条件付きで一致 | B値を再利用せず、Aでfresh rerunし、adaptive candidate selectionを開示する場合に成立。 |

関連して、`docs/ccbench-anatomy.md:126` の「mocc 2^4」も現行CMakeと一致しません。`mocc/CMakeLists.txt:5-9` で自由に切り替えられる最適化軸はBACK_OFF、KEY_SORT、TEMPERATURE_RESET_OPTの3つで、RWLOCKはbare fixed defineです。

## 総括

- 案Aだけが段7の正式なcertified cross-protocol比較を成立させる。
- 初手は版写像とread-setがSilo型に近いMOCCを推奨する。
- ERMIA active版はshiftされておらず、本当の難所はread_setに残らない成功readである。
- 案AではS1と同時にtrace末尾欠落の既知false-greenも閉じる必要がある。
- 案Bは別namespace・別ledger・official拒否を備えた偵察に限り規律2と整合する。
- 実務上の推奨順は「必要ならBで候補絞り込み → MOCCをAでfresh certified比較」である。