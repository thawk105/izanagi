# CCBench 解剖 (Phase 1 タスク0 成果物)

**対象:** `external/ccbench` @ `33d74a3` (tag `v1.1.0-117`, CMake 再構成版の v1 fork)。
**調査方法:** 多エージェントによるソース読解 + 高リスク項目の敵対的検証 + 実ホスト (Dell R760) でのビルド確認。全 file:line は `external/ccbench/` 相対。
**完了条件の充足:** 本ファイルを読めば「trace-hook をどこに刺すか」(§4-5) と「パラメータ探索をどの方式でやるか」(§1, §3) が判断できる。

> 注: 以下の引用は commit `33d74a3` 時点。CCBench を更新したら版を上げて再調査する。
> ±数行のズレが残りうる(検証で見つかった範囲は本文で明記)。

---

## 0. 要約 (Izanagi の意思決定に直結する事実)

1. **ビルドは CMake。protocol×workload ごとに別バイナリ** (`build/cc/<p>/<workload>_<p>.exe`、計34個)。
   **protocol 選択 = ビルドするターゲット。最適化 = ビルド時 `-D` define (cmake/Options.cmake)。workload パラメータ = ランタイム gflags。**
   → パラメータ探索は「ビルドし直し型」だが ccache で warm rebuild が安い (roadmap §6 の予想が確定)。
2. **プロトコルは10種。YCSB 対応は7種** (silo, tictoc, mocc, cicada, ermia, si, oze)。ss2pl/mvto/d2pl は YCSB バイナリを作らない。
   (external/ccbench/docs/protocols_en.md の上段表は ss2pl/mvto を YCSB ✓ と**誤記** → `output/insights/` に記録、§2 参照)
3. **`si` = `ermia` から SSN を剥がした Snapshot Isolation = 本物の write-skew (G2) を出す。**
   → Phase 1 タスク3「verifier が赤を出せる証明」の **positive control**。`ermia`(SSN)/`oze`(明示グラフ) は anti-dependency を実体化する **cross-check oracle**。
4. **Silo の trace 3 点 (read tidword / write key+value / commit maxtid) は全て CC-native フィールドに既存** → **trace 専用フィールドを足す必要なし** (絶対規律1 に最適)。例外は `ss2pl` のみ (ロックは版IDを持たないので producer-id の trace 専用フィールドが要る)。
5. **`#ifdef TRACE` には罠がある。** cmake が常に `-DTRACE=0` を定義すると `#ifdef TRACE` は常に真でコンパイルアウトされない (観測者効果が漏れ、絶対規律1違反)。**`#if TRACE` を使う**か、**0 のとき `-D` を出さない**こと (後者は `INSERT_*_DELAY_MS` に既存先例)。既存の `#if ADD_ANALYSIS` が数値マクロ契約の実装先例 (§5)。
6. **スレッドピンニングが既定で OFF。** `setThreadAffinity` は `#ifdef Linux` だが、protocol バイナリには `-DLinux` が**渡されていない** (`ProtocolHelpers.cmake`、flags.make で確認)。→ 96スレ/2ソケットでワーカーが両ソケットを浮遊し測定がスケジューラ依存に。**絶対規律4 のために `-DLinux` 追加か `numactl` ピンニングが必須** (§7)。
7. **`clocks_per_us` はランタイム gflag (default 2100、自動校正なし)。** calibrator がホストの TSC 周波数を実測して毎回 `-clocks_per_us` で渡す。`throughput[tps]` はこの値に**非依存** (OS sleep 秒で割る) だが、backoff/epoch の実挙動と latency 系メトリクスは依存 (§6)。
8. **ARM/Apple Silicon 懸念は消滅** (ここはネイティブ x86_64)。GCC 11.4 で `-Werror` 通過 (#44 は HEAD で解決済み)、`-mcx16`/`-march` 不要 (§7)。

---

## 1. ビルドシステム

- **CMake (≥3.10)。** トップ `CMakeLists.txt:65-67` が固定リスト `cicada d2pl ermia mocc mvto oze si silo ss2pl tictoc` を回して `add_subdirectory(cc/<p>)`。
- 各 `cc/<p>/CMakeLists.txt` は単一の `ccbench_add_protocol(...)` 呼び出し (`cmake/ProtocolHelpers.cmake:19`)。WORKLOAD タグ W ごとに `add_executable(W_<p>.exe  W_<p>.cc ...)` (`:32-34`)。
- **バイナリ命名/配置:** `build/cc/<protocol>/<workload>_<protocol>.exe`。protocol×workload は**全組み合わせが無条件登録**される (configure フラグで選ぶのではない)。
- **依存:** `find_package` で Threads/gflags/glog/Boost::filesystem。FetchContent (`cmake/ThirdParty.cmake`) で masstree (`thawk105/masstree-beta@b3c5d05`、autotools で out-of-tree ビルド)、mimalloc (`v2.3.2`)、googletest を SHA 固定取得。`common/{result,util}.cc` は `ccbench_common` 静的 libに1回だけコンパイルされ全 protocol がリンク。
- **ccache 自動有効** (`CMakeLists.txt:17-25`、`-DCCBENCH_CCACHE=OFF` で無効)。warm rebuild は TU 重複排除で安い。**ある protocol の `-D` フラグを変えるとその protocol のTUのみ再コンパイル** (他 protocol は無傷)。
- **1ターゲットだけビルド:** `cmake -S . -B build && cmake --build build --target ycsb_silo.exe`。
- **ビルド確認 (本ホスト R760):** `cmake -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF` + `make -j` を GCC 11.4 で実行 → **34バイナリ全て EXIT 0、ccbench 本体は `-Werror` で警告ゼロ**。残る警告は third-party masstree のみ (`-Werror` なし)。
- 既定が `Debug+ASan`、計測は `Release`。`silo` だけ非パラメタ化の `replay_test.exe` も作る (variant 探索には無関係)。

**Izanagi variant の同一性キー:** `(protocol N, build-flag-vector V)`。V は protocol N が**実際に参照する**ビルド時 `-D` の値のみ (参照しないフラグを変えても同一バイナリ→ ccache が重複排除するので genome から除外)。計測比較用 genome には instrumentation/sizing を含めない (§3, §5)。

---

## 2. プロトコル一覧と層1ベースCC選定

| protocol | 系統 | isolation | YCSB | anti-dep 追跡 | read / commit (file:line) |
|---|---|---|:-:|---|---|
| **silo** | OCC (単版) | serializable | ✓ | 暗黙 (commit時 TID-word 再検証) | read `cc/silo/transaction.cc:179` / commit `:557`→validation`:361`→writePhase`:489` |
| **tictoc** | OCC (TS) | serializable | ✓ | 暗黙 (rts 拡張) | read `cc/tictoc/transaction.cc:63` / commit `:683` |
| **mocc** | hybrid (OCC+温度で選択的2PL) | serializable | ✓ | 暗黙 (cold は OCC, hot は悲観ロック) | read `cc/mocc/transaction.cc:106` / commit `:1074` |
| **cicada** | MVCC | serializable | ✓ | TS順可視性 + commit検証 | read `cc/cicada/transaction.cc:144` / commit `:919` |
| **ermia** | MVCC + **SSN** | serializable (SSI) | ✓ | **明示** (SSN pstamp/sstamp) | read `cc/ermia/transaction.cc:92` / commit `:905`→ssn_parallel_commit`:594` |
| **si** | MVCC (ermia から SSN 除去) | **Snapshot Isolation (非 serializable)** | ✓ | **無し** → **G2 を出す** | read `cc/si/transaction.cc:92` / commit `:621`→si_commit`:470` |
| **oze** | MVCC + **明示シリアライゼーショングラフ** | serializable | ✓ | **最も明示的** (has_cycle) | read `cc/oze/transaction.cc:66` / commit `:1126`→validation`:540` |
| **ss2pl** | 2PL (strong strict) | serializable | — | 構造上 G2 不可 (悲観ロック) | read `cc/ss2pl/transaction.cc:126` / commit `:76`→unlockList`:454` |
| **mvto** | MVCC (Reed 1978) | serializable | — | 暗黙 (rts vs wts) | read `cc/mvto/transaction.cc:65` / commit `:459` |
| **d2pl** | 決定論的 2PL (事前宣言ロック) | serializable | — | 構造上 G2 不可 | read `cc/d2pl/transaction.cc:124` / commit `:74` |

**YCSB 対応の真実 = CMake の `WORKLOADS` 行** (= `ycsb_<p>.cc` の有無、自動生成 `build/PROTOCOL_MATRIX.md` と一致)。
YCSB=✓: silo, tictoc, mocc, cicada, ermia, si, oze (7)。YCSB=—: ss2pl, mvto, d2pl (3)。
⚠ `external/ccbench/docs/protocols_en.md:18,20` の**上段手書き表は ss2pl/mvto を YCSB ✓ と誤記**(同ファイル下段の自動生成表 `:44-45` とも矛盾)。→ CCBench 側の doc 不整合として `output/insights/ccbench-protocols-doc-ycsb-mismatch.md` に記録 (還元判断: ユーザー確認待ち)。

**層1ベースCC選定ガイド (YCSB で deployable なもの):**
- **read-heavy / low-contention → OCC:** `silo` (最も単純で速い read path、canonical baseline)、`tictoc` (commit_ts + TIMESTAMP_HISTORY で contention 耐性がやや高い)。**最有力 read-heavy シード。**
- **write-heavy / high-contention → MOCC** (`mocc`)。pure 2PL の `ss2pl`/`d2pl` は YCSB バイナリが無いので、YCSB では hot record を悲観ロックする `mocc` が高コンテンション代表。`ss2pl`/`d2pl` は TPC-C/BoMB のベースCC候補。
- **long-read / mixed → MVCC:** `cicada` (最も最適化ノブが多い MVCC シード)、`ermia` (SSN serializable)、`oze` (グラフ certified)。
- **推奨シードの序列:** 1) silo 2) tictoc 3) cicada 4) mocc 5) ermia。

**verifier (G2) との関係:** anti-dependency を**実体化する**のは `ermia` (SSN) と `oze` (明示グラフ)。
**検証器テストの決定打 = `ermia`(SSN on=serializable, G2無) vs `si`(SSN off=SI, write-skew G2 を出す) の ablation。** 同一エンジンの SSN on/off で、`si` が positive control、それ以外が negative。silo/tictoc/cicada/mvto/mocc は serializability を暗黙強制するので明示的 anti-dep 辺を吐かない → verifier が TRACE ログ (読んだ版 + commit 順) から G2 を再構成する。

---

## 3. 最適化フラグ・カタログ (層2 探索空間)

**二層構造:**
- **ランタイム gflags (再ビルド不要)** — workload/scale/skew: `thread_num`, `extime`, `epoch_time`, `clocks_per_us`, `ycsb_tuple_num`, `ycsb_max_ope`, `ycsb_rratio`, `ycsb_rmw`, `ycsb_zipf_skew`, MOCC の `temp_threshold` ほか。`DEFINE_uint64` 等で定義 (`include/ycsb.hh:20-26`, `cc/<p>/include/common.hh`)。
- **ビルド時 `-D` define (再コンパイル必須)** — 最適化。`cmake/Options.cmake` の `CCBENCH_*` CACHE 変数 → `ccbench_add_protocol` が target-private `-D<NAME>=<value>` に写像 (`ProtocolHelpers.cmake:41-43`)。`cmake -DCCBENCH_BACK_OFF=0` 等でファイル編集なしに上書き可能。

**カタログ (category = VLDB 論文の3分類: cpu-cache / delay-on-conflict / version-lifetime):**

| flag | protocols | category | 既定 | 効果 (要点) | codeSites |
|---|---|---|:-:|---|---|
| `NO_WAIT_LOCKING_IN_VALIDATION` | silo, tictoc | delay-on-conflict | 1 | validation でロック済 write を見たら即 abort (no-wait) | `cc/silo/transaction.cc:153`, `cc/tictoc/transaction.cc:340,564` |
| `NO_WAIT_OF_TICTOC` | silo, tictoc | delay-on-conflict | 0 | 上記の `#elif` 分岐: abort せず再検証/retry (TicToc 変種)。**上と相互排他** | `cc/silo/transaction.cc:157`, `cc/tictoc/transaction.cc:574` |
| `PREEMPTIVE_ABORTS` | tictoc | delay-on-conflict | 1 | ロック待ちを spin せず、serialize 不能と判れば早期 abort | `cc/tictoc/transaction.cc:134` |
| `TIMESTAMP_HISTORY` | tictoc | version-lifetime | 1 | 1段前の wts (`pre_tsw_`) を持ち、過去版に対して serializable なら commit 許可 | `cc/tictoc/transaction.cc:381,508,587` |
| `BACK_OFF` | **全10** | delay-on-conflict | 1 | abort 後の指数バックオフ。各 protocol に2サイト | `cc/silo/transaction.cc:41,570` ほか |
| `INLINE_VERSION_OPT` | cicada(0), oze(1) | version-lifetime/cpu-cache | 異 | 最新版を tuple 埋め込み slot に置き malloc 回避 (cache 局所) | `cc/cicada/include/tuple.hh:27,54,81`, `transaction.hh:219` |
| `INLINE_VERSION_PROMOTION` | cicada | version-lifetime | 1 | MinRts 未満の長命版を inline slot へ移送。**`INLINE_VERSION_OPT` 依存** | call `cc/cicada/transaction.cc:133` (`#if` は `:129`), `transaction.hh:200` |
| `REUSE_VERSION` | cicada, oze | version-lifetime | 1 | 死んだ Version をスレッドローカル free-list で再利用 | `cc/cicada/include/transaction.hh:185,229` |
| `SINGLE_EXEC` | cicada | version-lifetime | 0 | MVCC を単版に退化 (inline_ver_ 直接)。**正しさ意味論を変える** | `cc/cicada/transaction.cc:85,235,705,762,952` |
| `WRITE_LATEST_ONLY` | cicada, oze | version-lifetime | 0 | 最新版のみへ write。**`#ifdef` でなく runtime 定数 `if`** (両分岐コンパイル) | `cc/cicada/transaction.cc:242,491,512` |
| `MERGE_ON_READ` | oze | other | 0 | read 時に依存グラフを eager マージ。**cycle 検出タイミング=正しさに影響** | `cc/oze/transaction.cc:182` |
| `TEMPERATURE_RESET_OPT` | mocc | delay-on-conflict | 1 | 古くなった温度を 0 にリセットし cooled record を楽観 path へ戻す | `cc/mocc/util.cc:208`, `transaction.cc:827` |
| `RWLOCK` | mocc | delay-on-conflict | (bare, 常ON) | MOCC の R/W ロック実装選択。hot record の**可視 read** 機構 | `cc/mocc/transaction.cc:166,...`, `lock.cc:932` |
| `DLR1` | ss2pl | delay-on-conflict | (bare, 常ON) | SS2PL の no-wait デッドロック解決 (r_trylock 失敗で即 abort) | `cc/ss2pl/transaction.cc:178,269,314,413,438` |
| `KEY_SORT` | d2pl,ermia,mocc,si,ss2pl | delay-on-conflict | 0 | tx の op をキー順 sort しロック順序デッドロック回避 | `include/ycsb.hh:81` |
| `WAL` | silo (+ss2pl driver) | other (durability) | 0 | commit 時に write-ahead log。perf コスト | `cc/silo/transaction.cc:516`, `*_silo.cc` |

**死にフラグ (この fork では `#if` ガード無し = トグルしても同一バイナリ。探索空間から除外):**
- `NO_WAIT_OF_TICTOC` … 宣言・出力のみ、挙動 `#if` 無し。
- `PARTITION_TABLE` … `ShowOptParameters()` の print のみ (`cc/silo/util.cc:167` 等)、挙動分岐ゼロ。
- `PROCEDURE_SORT` (silo) … print のみ。意図 (キー順アクセス) は実際には `KEY_SORT` だけが実装、しかも silo はそれを渡していない。
- `SLEEP_READ_PHASE`, `WORKER1_INSERT_DELAY_RPHASE`, `INSERT_{READ,BATCH}_DELAY_MS` … 実験/計測撹乱ノブであり最適化ではない。perf では OFF 固定。`DEBUG_MSG`(oze)/`ADD_ANALYSIS` は instrumentation (§5)。

**相互排他 / 依存 (探索の制約として符号化する):**
- `NO_WAIT_LOCKING_IN_VALIDATION` XOR `NO_WAIT_OF_TICTOC` (同一 `#if`/`#elif`)
- `DLR0` XOR `DLR1` (ss2pl、既定で DLR1 のみ build)、`RWLOCK` XOR `MQLOCK` (mocc、既定 RWLOCK のみ)
- `INLINE_VERSION_PROMOTION` は `INLINE_VERSION_OPT` に hard 依存 (cicada 既定では `INLINE_VERSION_OPT_CICADA=0` なので両者 default で no-op)
- `RWLOCK`(mocc)/`DLR1`(ss2pl) は CACHE entry 無しの bare define で CMakeLists にハードコード → `-DCCBENCH_*` で直交トグルできない (protocol 固有として扱う。off 分岐 `#else/#elif` はソースに存在するので、探索したいなら CMakeLists 編集が要る)。

**invisible reads (Phase 1 タスク5):**
- **Silo に内在。フラグではない。** `read_internal` (`cc/silo/transaction.cc:227-267`) は `tidword_` を load → body コピー → 再 load → 比較 のみで**共有メモリに一切書かない** (read lock も read timestamp 公開もしない)。結果はスレッドローカル `read_set_` (`:261`) にのみ追記。`cc/silo` に可視 read への `#ifdef` は存在しない。
- **可視 read の対は別 protocol = MOCC。** `mocc` の `read_internal` は record 温度が `FLAGS_temp_threshold` を超えると共有 read-lock を取る (`cc/mocc/transaction.cc:198-204`)。
- **on/off A/B のやり方:** `temp_threshold` は**ランタイム gflag** なので再ビルド不要。OFF(invisible)= `silo`、または `mocc -temp_threshold=<大>` (誰もロックせず silo 相当)。ON(visible)= `mocc -temp_threshold=0` (全 read が可視 read-lock)。
  注意: silo と mocc は read 可視性以外も異なる (mocc はロック失敗 abort/RLL) ので、性能差を invisible reads だけに帰属させない。
  - **🔴 gflag 内交絡 (タスク5b 実測, D/insight 2026-06-19):** `temp_threshold` は read だけでなく **update (`cc/mocc/transaction.cc:361`) / delete (`:468`) の write-lock も gate する** = 温度ベースの「悲観ロック vs OCC」セレクタ。よって同一 mocc バイナリの A/B でも、`rratio<100` では write 経路 (CLL violation 検出 `:642-663` / RLL 再取得 `:736-783` / trylock 失敗 abort) の差が混入する。**`rratio=0` (write-only) の差は invisible reads ではなく [B]⑥ temperature-gated 悲観 write-locking の効果。invisible reads (read 可視性) のクリーン計測は `rratio=100` (read-only) のみ。** 実測 clean 点 ≈ **1.28x** (read-heavy で効く = 論文/roadmap と整合、phase1 の「write-intensive」は誤記訂正済み)。

**VLDB「7最適化」× 3カテゴリ → 本 fork の live フラグ:**
- **[A] CPU-cache:** ① invisible reads (Silo 内在) ② version inline/local cache (`INLINE_VERSION_OPT` + `_PROMOTION` + `REUSE_VERSION`)
- **[B] delay-on-conflict:** ③ no-wait in validation (`NO_WAIT_LOCKING_IN_VALIDATION`、2PL 版は `DLR1`/`KEY_SORT`) ④ backoff (`BACK_OFF`) ⑤ preemptive aborts (`PREEMPTIVE_ABORTS`) ⑥ 温度適応悲観ロック (MOCC `RWLOCK`+`temp_threshold`+`TEMPERATURE_RESET_OPT`)
- **[C] version-lifetime:** ⑦ timestamp history / version reuse / GC (`TIMESTAMP_HISTORY`, `REUSE_VERSION`, `SINGLE_EXEC`, `WRITE_LATEST_ONLY`)

**探索空間サイズ (生きた最適化フラグのみ、全て on/off):**
cicada 2^6=64、oze 2^7=128、silo 2^4=16、tictoc 2^4=16、mocc 2^3=8、ss2pl 4、ermia 4、si 4、d2pl 4、mvto 2 ≈ **250 個の最適化バイナリ** (この一覧の単純和。× protocol ごとの workload 数)。純粋なブール超立方体 (KEY_SIZE/VAL_SIZE は sizing で固定)。**初手の全探索が現実的** (roadmap §2 (a) の前提が確定)。mocc の軸は `TEMPERATURE_RESET_OPT`・`KEY_SORT`・全 protocol 共通の `BACK_OFF` の 3 つ — `RWLOCK` は bare define で cache option から操作できないため、ss2pl の `DLR1` と同様に数えない (2026-09-14 訂正、旧記載は `RWLOCK` を数えて 2^4=16 としていた)。実体化済み軸集合の正本は `orchestrator/campaign/genome.py` で、silo と mocc はこの数と一致する。tictoc・cicada の項は同 file の登録軸と食い違うが、未検証のまま残す。

**正しさに影響する (= verifier 必須通過) フラグ:** `SINGLE_EXEC` (MVCC→単版退化)、`WRITE_LATEST_ONLY` (版配置制約)、`MERGE_ON_READ` (cycle 検出タイミング)。これらをトグルしたら必ず verifier を通す。

---

## 4. trace-hook 挿入点 (Phase 1 タスク1/2 の前提)

verifier が必要とするのは、commit した各 tx について: 各 READ の (キー, 読んだ版ID, その版を書いた tx)、各 WRITE の (キー, 値)、グローバルな COMMIT 順。anti-dep (rw) 辺には「reader が見た版」と「後でそれを上書きした版」が要る。

**workload ループ (protocol 非依存層) — `include/ycsb.hh`:**
- tx 境界: begin `:113` / commit `:161` / abort `:150,162` / RETRY ラベル `:108` / commit カウンタ `:166-167`。
- read 発行: `:123` (READ)、`:136` (RMW)。値は `body->get_value().cast_to<YCSB>()` (`:126,138`)。
- write 発行: `:132-133` (WRITE)、`:142-143` (RMW)。
- op plan は `makeProcedure` (`:55-84`)、`ycsb_rmw` gflag で WRITE→RMW、`KEY_SORT` (build時) で並べ替え。キーは8byte big-endian (`parse_bigendian`, `:120`)。
- **この層で取れるのは (op, key, 意図した値) まで。protocol 非依存。** だが「実際に読んだ版ID」と「commit TID」は各 protocol の `read_internal`/`commit` 内部にあるので、そこは `cc/<p>/` に個別に刺す。

**Silo フック (3点とも CC-native、trace 専用フィールド不要):**
| 目的 | file:line | 取る局所変数 | 備考 |
|---|---|---|---|
| read-version | `cc/silo/transaction.cc:261` | `expected` (Tidword) | `read_set_` の `ReadElement::tidword_` (`silo_op_element.hh:35`) に既存。validation (`:385`) が既に消費 |
| write-value | `cc/silo/transaction.cc:479` | `body` (TupleBody) + `key` | `WriteElement::body_` (`silo_op_element.hh:43`)。実書込は writePhase memcpy `:525` |
| commit-order | `cc/silo/transaction.cc:511` | `maxtid` (Tidword) | serialization point。`max(tid_a,tid_b,tid_c)`。tuple へ stamp (`:527`)= 新版ID |

**version-producer recovery (どの tx がその版を書いたか):**
- **Silo:** 版ID = 生産 tx の commit TID。`Tidword` (`cc/silo/include/tuple.hh:12-22`) は64bit union: bit0 lock / bit1 latest / bit2 absent / tid:29 / epoch:32。commit 時に `maxtid` を tuple に stamp (`:527`)、reader はそれを `ReadElement::tidword_` にスナップ (`:261`)。→ read の `tidword.{epoch,tid}` == 生産者の commit `maxtid.{epoch,tid}`。**G2 rw 辺:** reader が見た版 = read の tidword、上書き版 = 同キーに次に commit した maxtid (全 commit TID をキーごとに順序付ければ再構成可能)。
- **cicada (MVCC):** read で `read_set_.emplace_back(s,key,tuple,later_ver,ver)` (`cc/cicada/transaction.cc:126`)。`ver` = 観測した `Version*` (自前 `wts_`/`rts_`/`status_` を持つ、`version.hh:25-32`)、`later_ver` = 次に新しい版 → **rw 辺の両端が CC-native。** 生産者 = `ver_->wts_` (writer の commit ts、`:706` で設定)。commit 順 = tx の `wts_` (生成 `time_stamp.hh:39`: `ts_=(localClock_<<8)|tid`、低 byte が thid)。
- **ss2pl (ロックのみ): 唯一 trace 専用フィールドが要る。** 版ID/commit TID が無い。`read_internal` で r_lock 取得後に `read_set_.emplace_back(s,key,tuple,body)` (`:193`、DLR0=wait/DLR1=no-wait で gate)。serialization point は commit 内 `unlockList()` (`:104`)。→ **D14 の `#if TRACE` 下で global commit sequence number を `:104` で発番**し、各 record の last-writer を記録して rw 辺を再構成する。

**注意 (read-own-write 短絡):** silo `read()` は read/write set ヒット時に `ReadElement` を**追加せず**早期 return (`cc/silo/transaction.cc:195-204`、cicada `:156-165`、ss2pl `:136-145`)。verifier はこれを「既記録版の再観測」として扱い、欠落 read と誤認しないこと。

---

## 5. 観測者効果分離の実装指針 (絶対規律1) — `ADD_ANALYSIS` 先例

CCBench には既に **`ADD_ANALYSIS`** という「数値マクロを `#if` で判定し、計測計装を完全コンパイルアウトする」機構があり、Izanagi の `#if TRACE` のほぼ完全な先例になる。
- **完全コンパイルアウト (全軸):** counter フィールド自体が `#if ADD_ANALYSIS` (`include/result.hh:24-62,72-112`)、計測サイトの `rdtscp()`/`+=` も `#if` (`cc/silo/transaction.cc:42-50`)、集計 (`common/result.cc:688-729`)、表示も全て gate。**runtime 分岐 (`if(enabled)`) ではない真の `#if`。** → 絶対規律1 が要求する「false でも分岐予測ミス・命令キャッシュ汚染で性能に効くのを避ける」を既に満たす実装パターン。
- **Izanagi が `TRACE` を足すときの手順:** `cmake/Options.cmake` に `CCBENCH_TRACE 0 CACHE STRING` を足し、`ccbench_universal_definitions` (`:55-63`) 経由で target-private `-DTRACE=<v>` に流す。read/write/commit の既存 `rdtscp` ブラケットサイトがそのまま TRACE emit 点になる。
- **⚠ 致命的な罠:** `ADD_ANALYSIS` は `#if ADD_ANALYSIS` (**常に定義される数値マクロ**)。cmake が常に
  `-DTRACE=0` を定義する契約では **`#ifdef TRACE` は常に真**になる。D14 どおり `#if TRACE` を使わないと
  コンパイルアウトされず観測者効果が漏れる (絶対規律1違反)。CLAUDE.md は具体記法を D14 へ委譲する。
  **対策のどちらかを取る:** (a) コード側を **`#if TRACE`** にする (ADD_ANALYSIS と統一、推奨)、または (b) cmake 側で 0 のとき `-DTRACE` を出さない (`INSERT_*_DELAY_MS` が空値で drop される `ccbench_normalize_options` `:68-82` が先例)。**この設計判断は decisions.md に記録すべき候補** (絶対規律1 のコンパイルアウト要件を CCBench のマクロ規約と整合させる手段の確定)。
- **`TRACE` は `ADD_ANALYSIS` と別マクロにする** (現状 fork に `TRACE` は存在しない = Izanagi が新規追加)。正しさ trace build と perf-analysis build を分離可能に保つため。**genome (性能比較キー) に `TRACE`/`ADD_ANALYSIS`/`DEBUG_MSG` を絶対に含めない。**

---

## 6. 計測の意味論 (calibrator / measurement stability §3.6 への接続)

**出力形式:** 標準出力に `<label>:\t<value>` (タブ区切り)、1行1メトリック。JSON でも struct でもない → 親が stdout を捕捉してパース。組み立ては `common/runner.hh:316-331` → `common/result.cc:displayAllResult`。
- **主要 throughput = `throughput[tps]:`** (commits/sec, 整数)。`common/result.cc:53-54` で `(total_commit_counts_)/FLAGS_extime` の**整数切り捨て**。`throughput[ops]:` は一部 protocol のみ。
- **パース注意:** label は trailing `_` を持つ (`commit_counts_:` 等) → 最初のタブで split しリテラル一致。`batch_abort_rate` は batch 無しで `nan`/`-nan`。`maxrss:` は `printf` で末尾 ` kB`。
- **`#ShowOptParameters()` 行 = この binary がコンパイルされたビルド時最適化 `-D` の権威的記録** (`cc/silo/util.cc:162-177`) → **WAL に variant の genome fingerprint として取り込む** (Phase 1 タスク6)。
- **`#FLAGS_*` 行** = workload param echo (provenance)。

**測定の意味論と Izanagi への含意:**
- **warmup/ramp 無し。** barrier が開いた瞬間から計測 (`common/runner.hh:281-307`)。DB は makeDB で事前構築済みなので index/tuple は warm だが、cache warming は測定窓に含まれる。→ **roadmap §3.6(1)「冒頭を warmup として破棄」を CCBench はネイティブに満たさない。** Izanagi 側で extime を十分長く取るか、warmup 破棄を別途実装する。
- **`throughput[tps]` は nominal `FLAGS_extime`** (OS sleep 目標) で割る。`actual_extime` (`runner.hh:305-307` = TSC 実測秒) は print されるが tps 計算に**使われない**。→ **`actual_extime` vs `FLAGS_extime` の乖離 = scheduling noise 検出シグナル**。§3.6(2) の外れ値検出/再測定の安価な実材料。精度が要るなら生 `commit_counts_` から tps を再計算する。
- **`clocks_per_us` はランタイム gflag (default 2100、自動校正なし)。** `/proc/cpuinfo`/CPUID 0x15/壁時計測定のコードは無い (`cc/silo/include/common.hh:32-33`)。
  - `throughput[tps]` は clocks_per_us に**非依存** (OS sleep 秒で割るため) → 誤設定でも生 tps は歪まない。
  - だが latency/rate 系メトリクス、`actual_extime`、**epoch 進行間隔と backoff 持続は clocks_per_us 依存** → **誤設定は run の実挙動を変える** (低すぎる値は backoff/epoch を実時間で短縮)。
  - **calibrator の責務:** 本ホストで TSC 周波数を1回実測 (例 `rdtscp` を `clock_gettime(CLOCK_MONOTONIC)` 区間で挟む) し、整数 MHz を毎 run `-clocks_per_us` で渡す。invariant TSC 前提 (この Xeon クラスは真)。本ホスト `/proc/cpuinfo` は 2600 MHz を表示 (要 TSC base 確認、calibrator で実測する)。

---

## 7. ポータビリティ / ホスト適合 (Dell R760)

- **x86_64 ネイティブ。ARM/Apple Silicon 懸念は消滅。** GCC 11.4 で `-Wall -Wextra -Werror` 通過 (#44 は HEAD で防御的初期化済み: `cc/cicada/transaction.cc:488`, `cc/mocc/transaction.cc:629`)。clang 15 も利用可。
- **特別な ISA `-m` フラグ不要。** 全 atomic は `__atomic_*` builtin (`include/atomic_wrapper.hh`)、**128bit CAS / cmpxchg16b 不使用** → `-mcx16` 不要。`_mm_pause`/`rdtsc`/`rdtscp` は x86_64 baseline。実コンパイル行は `-O3 -DNDEBUG -Wall -Wextra -Werror -std=c++20` のみ (`-march` 無し)。`_mm_clwb` 等は opt-in microbench (`-DCCBENCH_BUILD_MICROBENCH=ON`、既定 OFF) のみ。
- **🔴 スレッドピンニングが既定で OFF (本ホストで最重要の計測ギャップ):** `setThreadAffinity` (`include/cpu.hh:30-41`、`sched_setaffinity`+`SYS_gettid`) は `#ifdef Linux` で囲われているが、`ccbench_add_protocol` は protocol バイナリに **`-DLinux` を定義しない** (flags.make の `CXX_DEFINES` に `-DLinux` 無しを確認)。→ **as-built ではワーカーが一切ピンされず、OS スケジューラが両ソケット間を移動する。**
  - **絶対規律4 への直撃:** 2ソケット機での unpinned run はスケジューラ依存でノイズが大きい。many-core の cache 競合が再現されず歪む。
  - **対策:** `ccbench_add_protocol` 内に `if(CMAKE_SYSTEM_NAME STREQUAL "Linux") target_compile_definitions(${target} PRIVATE Linux) endif()` を足す (`MicrobenchHelpers.cmake:43-45` に先例)、**または** run を `numactl`/`taskset` で包む。これは CCBench への改変なので **patches/ で管理** (D6)。
- **NUMA 非対応。** `libnuma`/`numa_alloc`/`mbind` 一切なし。ピンしても `myid % nproc` 順でロケーリティ制御なし → cross-socket トラフィック非制御。**reproducible な96スレ/2NUMA run には `numactl` で明示ピン (interleave or local 方針を固定) する。**
- `<linux/fs.h>`/`fdatasync` は WAL path のみ (`#ifdef Linux` + build時 `WAL=0` 既定)。O_DIRECT/hugepages/mmap は無し。

**残課題 (Phase 1 で配線/対処):**
1. protocol target に `-DLinux` を patch でつける (ピンニング有効化)。
2. `numactl` ラッパーで NUMA ポリシーを固定 (calibrator / orchestrator)。
3. calibrator で TSC 周波数を実測し `-clocks_per_us` を確定。
4. `#if TRACE` (または cmake で 0 のとき未定義) で trace-hook を追加 (§5)。

---

## 8. Izanagi 次タスクへの申し送り

- **タスク1 (trace-hook):** Silo から着手。3点とも CC-native (§4) なので trace 専用フィールド不要。`#if TRACE` 方式 + cmake `CCBENCH_TRACE` で配線 (§5)。改変の行き先は `izanagi-trace` ブランチ = submodule pin (D16。本文書執筆時の D6 案 = patches/ 配下の単一 trace-hook patch は D16 で改訂済み)。同 patch に **`-DLinux` ピンニング修正**も束ねるか別 patch にするか要判断。
- **S1 (trace-hook の他 protocol 移植) の既知の罠 — ermia の版 ID 写像 (worklog 2026-06-18 から昇格、2026-09-14 に現物で訂正):** si の版 ID は `cstamp` (単 uint) をそのまま `(epoch=1, tid=cstamp)` に写像でき、**ermia の active な版 ID も同じ raw cstamp** である。`TxExecutor::commit()` が呼ぶ commit 経路は `ssn_parallel_commit()` だけで、そこは `ver_->cstamp_.store(this->cstamp_)` と raw を書き、read 側の可視版選択 (`read_internal`) も raw の `txid_` と raw の `ver_->cstamp_` を比べる。`cstamp<<1` (低ビット = TID フラグ `TIDFLAG`) を書くのは (a) 呼び出しが 1 つも無い dormant な `ssn_commit()` と (b) sstamp (`verSstamp`) 側だけ。**罠は「1 ビットシフトに合わせること」ではなく、dormant な `ssn_commit()` を読んで写像を決めること** — シフトを入れると版 ID が実物と食い違い**全 read が orphan 化**する。si の trace-hook はそのまま流用できる。Phase 3 主実験 headline 2 (クロスプロトコル) で S1 が発火する際の必須知識 (phase3.md must 表 S1 行)。
- **タスク2 (verifier):** TRACE ログから ww/wr/rw 辺を構築し G2 cycle 検出。版ID は Silo=Tidword(epoch,tid)、cicada=Version.wts_+chain、ss2pl=発番した producer-id。read-own-write 短絡を「再観測」として扱う。
- **タスク3 (赤を出せる証明):** **`si` を positive control に** (SSN 剥がし= SI = 本物の write-skew G2)。`ermia`(SSN)/`oze`(明示グラフ) を cross-check oracle に。これは「わざと壊した CC」より自然で、CCBench 内に既に存在する本物の anomaly。
- **タスク4 (calibrator):** `clocks_per_us` 実測、`-DLinux`/`numactl` ピンニング、`actual_extime` 監視 (§6)、cache-miss 飽和点 (perf 動作確認済み)。
- **タスク6 (orchestrator):** `#ShowOptParameters()` 行を variant genome として WAL に格納、死にフラグ (`NO_WAIT_OF_TICTOC`/`PARTITION_TABLE`/`PROCEDURE_SORT`) を探索から除外、ccache 活用、ビルドキャッシュキー = 参照フラグのみのハッシュ。
