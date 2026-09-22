## 0. 前提と採用案

以下、`W` は指定 worktree、`J` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3`、`CC` は `W/external/ccbench`。CCBench の行番号は pin `e9e477ca1b55348ab4530de0b1cf663ce4555290` の現物に対するものとする。

**単位 1・2 の実装は可能。P1〜P4・P6・P7 を以下の条件付きで採用し、P5 の説明を修正する。** 本段では読取りと静的確認だけを行った。編集・commit・configure・build・前処理比較・テスト・計算投入は実行していない。

本 wave の成果は「TPC-C v3 producer の構造・計数確認」と「YCSB v2 の既存認定維持」であり、TPC-C の直列化可能性認定そのものではない。現行 parser は C 7 token のみ受理し、pipeline は YCSB 以外を拒否する。本 wave ではどちらも変更しない。

根拠: `J/s1-brief.md:6`, `:9`, `:10`、`orchestrator/verifier/parse.py:321`、`orchestrator/campaign/pipeline.py:434`。

## 1. 単位 1 — `include/trace.hh`

### API と状態

既存の `#if TRACE` 内、namespace の終端より前へ追記する。既存 helper の定義・呼出規約・出力 bytes は変更しない。

```cpp
inline std::uint32_t& tpcc_tx_type_context() {
  static thread_local std::uint32_t value{0};
  return value;
}
inline void set_tpcc_tx_type(std::uint32_t value) {
  tpcc_tx_type_context() = value;
}
inline std::uint32_t tpcc_tx_type() {
  return tpcc_tx_type_context();
}
inline void clear_tpcc_tx_type() {
  tpcc_tx_type_context() = 0;
}
```

外部 linkage の inline 関数に置いた関数ローカル TLS とする。header の `static` 関数や無名 namespace に置くと、設定する `tpcc_silo.cc` と読む `transaction.cc` で状態が分離するため不可。0 は workload context が無い状態であり、v3 の `tx_type` として出力しない。

新 helper は次で固定する。

```cpp
inline void emit_commit_v3(
    std::size_t thid, std::uint64_t txid,
    std::uint64_t epoch, std::uint64_t tid,
    std::size_t nR, std::size_t nW,
    std::size_t nS, std::size_t nQ, std::uint32_t tx_type);

inline void emit_read_v3(
    std::size_t thid, std::uint64_t txid, std::uint32_t table,
    const std::string& key_hex,
    std::uint64_t ver_epoch, std::uint64_t ver_tid);

inline void emit_write_v3(
    std::size_t thid, std::uint64_t txid, std::uint32_t table,
    const std::string& key_hex, char op,
    std::uint64_t epoch, std::uint64_t tid);

inline void emit_lock_violation_v3(
    std::size_t thid, std::uint64_t txid, std::uint32_t table,
    const std::string& key_hex, const char* reason);
```

各実装は既存 `stream(thid)` への挿入演算だけとし、空白 1 byte・末尾 LF で次を出す。

```text
C txid thid epoch tid nR nW nS nQ tx_type
R txid table key_hex ver_epoch ver_tid
W txid table key_hex op epoch tid
X txid table key_hex reason
```

`emit_commit` は現在 **v1 の 5 token helper** である。これを v2/v3 化しない。silo の v2 C は現在どおり `transaction.cc` が直接出す。

根拠: `CC/include/trace.hh:25`, `:35`, `:41`, `:52`, `:78`, `:84`, `:91`, `:117`, `:122`、`J/verbatim/tpcc-design-README.md:43`。

### コンパイル・警告条件

新しい include は不要。型・TLS・関数本体のすべてを既存 `#if TRACE` 内に収める。全引数を出力で使用し、`uint8_t` を文字として stream へ流す形を避ける。未使用関数を生む file-local helper は追加しない。

新ブロックを元の 120 行の直前へ入れるなら、末尾を `#line 120` として元の空行・namespace 終端を続けられる。呼出元の行番号は include から戻る際に復元される。

受入では CMake の `-Wall -Wextra -Werror` を維持して両 TRACE 値を build する。静的には警告を生む要因を避けた案だが、警告 0 の実証は計算ノード build 待ちである。

根拠: `CC/cmake/CompileOptions.cmake:30`、`CC/cmake/ProtocolHelpers.cmake:58`。

## 2. 単位 1 — `include/tpcc.hh`

### 挿入位置と `#line`

既存 include 群と取引処理を動かさず、以下の位置に追加する。`#line N` は**次の物理行を元の論理行 N とする**。filename 引数は付けず、`__FILE__` の綴りを維持する。

| 元の位置 | 変更 | 復元 |
|---|---|---|
| 26 行の include 後 | `#if TRACE` 内で `#include "trace.hh"` | `#endif` 後に `#line 27`、元の空行を続ける |
| 55 行 `tx.begin();` 直後 | `set_tpcc_tx_type(get_tx_type(query.type));` | `#line 56` |
| 93 行 `tx.abort();` 直後 | `clear_tpcc_tx_type();` | `#line 94` |
| 103 行 `tx.abort();` 直後 | `clear_tpcc_tx_type();` | `#line 104` |
| 108 行、commit 成功の分岐を抜けた後 | `clear_tpcc_tx_type();` | `#line 109` |
| 110 行の quit 判定 | `#if !TRACE` で囲む | 下記 |

追加する setter/clear 呼出しはそれぞれ `#if TRACE` 内。計数部分は次の形とする。

```cpp
#if !TRACE
#line 110
    if (loadAcquire(tx.quit_)) return;
#endif
#line 111
    tx.result_->local_commit_counts_++;
    tx.result_->local_commit_counts_per_tx_[get_tx_type(query.type)]++;
```

これで TRACE=0 の quit 判定と加算順序を保存し、TRACE=1 では成功 commit を必ず加算する。`#line` は TRACE=0 でも作用させる必要があるため、trace の条件枝の外へ置く。

根拠: `CC/include/tpcc.hh:26`, `:55`, `:88`, `:92`, `:102`, `:110`、`CC/include/debug.hh:54`、`CC/include/workload.hh:9`。

### 経路別の状態

| 経路 | context の推移 |
|---|---|
| 初回、begin 前の quit | 初期値 0 のまま return |
| 通常試行 | begin → `query.type` の 1〜5 を設定 |
| app 層 abort | `tx.abort()` → clear → abort 加算 → RETRY |
| commit 失敗 | `tx.abort()` → clear → invalid return または abort 加算・RETRY |
| silo commit 成功 | writePhase の E 後に clear。workload 側でも clear し、成功を加算 |
| 他 protocol の commit 成功 | workload 側の clear で 0 へ戻す |
| retry 後、begin 前の quit | 直前の失敗経路で 0 に戻っている |

成功側の clear を workload にも置く理由は、共有 `tpcc.hh` の変更が他 protocol にも入るため。単位 1 の commit 単独でも TLS を持ち越さない。silo の `begin()`・`abort()` を変更する必要はない。

`ERR` は既存どおり process を終了するため、その経路に次取引への復帰処理は不要。例外による継続実行を新しく導入しない。

根拠: `CC/include/tpcc.hh:48`, `:53`, `:88`, `:93`, `:103`、`CC/include/debug.hh:60`。

## 3. 単位 2 — `cc/silo/transaction.cc`

### v2/v3 の選択

既存の 584 行からの `#if TRACE` ブロック内で、txid の採番と同じ scope に取引種別を値で保存する。

```cpp
const std::uint64_t izanagi_txid = izanagi_trace::next_txid();
const std::uint32_t izanagi_tx_type = izanagi_trace::tpcc_tx_type();

if (izanagi_tx_type != 0) {
  izanagi_trace::emit_commit_v3(
      thid_, izanagi_txid, maxtid.epoch, maxtid.tid,
      read_set_.size(), write_set_.size(), 0, 0, izanagi_tx_type);
} else {
  // 現行 602〜605 行をそのまま置く。
}
```

C を出す箇所はこの排他的分岐だけ。旧 `emit_commit` を呼ばず、追加採番もしない。R/W の各ループでも同じ `izanagi_tx_type` で helper を選ぶ。v2 側の出力式は温存する。

表番号は `get_storage(re.storage_)` / `get_storage(we.storage_)` を使用する。既存関数が `static_cast<std::uint32_t>` を実装しており、`transaction.cc` に TPC-C の enum 定義を include する必要はない。

P1 の根拠は実コードと一致する。`ccbench_add_protocol` は同じ protocol source を workload ごとの target に同じ定義で組み込み、workload 名は CMake property にしか置いていない。

根拠: `CC/cc/silo/transaction.cc:584`, `:601`, `:606`, `:611`、`CC/include/workload.hh:5`、`CC/include/op_element.hh:19`、`CC/cmake/ProtocolHelpers.cmake:32`, `:41`, `:64`、`CC/cc/silo/CMakeLists.txt:1`。

### X・E と復元位置

| 箇所 | 変更 |
|---|---|
| entry X、629 行 | 既存の lock bit・shadow 判定を維持し、v3 時だけ table 付き helper |
| UPDATE retention X、653 行 | `if (!cur.lock)` に braces を付け、その内側で helper を選択 |
| DELETE retention X、674 行 | UPDATE と同形 |
| 698 行 E | 現行出力式を維持 |
| E 直後 | `clear_tpcc_tx_type()` |

INSERT の X 除外、UPDATE/DELETE の実書込み、GC、read/write set の clear は変更しない。特に E は全 X と実書込みループの後に置いたままとする。

後続の元行を復元する `#line` は次の 4 本で足りる。

- 元 634 行の `#endif` 後: `#line 635`。
- 元 657 行の `#endif` 後: `#line 658`。
- 元 678 行の `#endif` 後: `#line 679`。
- 元 699 行の `#endif` 後: `#line 700`。

冒頭 include・begin・abort を変更しないため `ERR` の元 106 行は動かない。後半の `ERR` は上記復元により元 690 行となる。機械比較でも両展開値を確認する。

根拠: `CC/cc/silo/transaction.cc:106`, `:624`, `:645`, `:658`, `:669`, `:690`, `:694`, `:700`。先例は commit `68106660686232781bca3be792a750d3e19d7a8a` の `cc/mocc/transaction.cc`、元 17・990・991・1158・1169・1187・1195 行への復元。

### P 行と現行 verifier

P 行は変更しない。validation は採番より前に動き、後続検証で abort しうるため、取引種別 context があっても committed txid を付ける根拠にはならない。

また v2 の `izanagi_trace::emit_lock_violation(...)` 呼出しを各分岐に残す。現行 verifier の X 証拠面検出はこの関数名を compiled source 内で検索する。すべてを新 helper や header の dispatcher に置換すると、YCSB の認定条件を壊しうる。

根拠: `CC/cc/silo/transaction.cc:383`, `:413`, `:432`, `:706`、`orchestrator/verifier/model.py:45`, `:238`, `:290`、`J/verbatim/D296.md:3`。

## 4. 規律 1 — consumer TU と比較方法

### 全列挙

include 検索で確認できた consumer は **12 source path**。

| header | consumer と include 行 |
|---|---|
| `tpcc.hh` | `cc/cicada/tpcc_cicada.cc:16` |
| 同上 | `cc/ermia/tpcc_ermia.cc:15` |
| 同上 | `cc/mocc/tpcc_mocc.cc:13` |
| 同上 | `cc/mvto/tpcc_mvto.cc:14` |
| 同上 | `cc/oze/tpcc_oze.cc:14` |
| 同上 | `cc/si/tpcc_si.cc:15` |
| 同上 | `cc/silo/tpcc_silo.cc:16` |
| 同上 | `cc/ss2pl/tpcc_ss2pl.cc:12` |
| 同上 | `cc/tictoc/tpcc_tictoc.cc:12` |
| `trace.hh` | `cc/silo/transaction.cc:9` |
| 同上 | `cc/si/transaction.cc:13` |
| 同上 | `cc/mocc/transaction.cc:15` |

transaction.cc の 3 path は、それぞれ `ycsb/tpcc/bomb/sbomb` の 4 target に現れる。したがって compile database 上では、まず **9 + 3×4 = 21 entry** を期待集合とする。同じ flags でも黙って source path だけで重複排除しない。

候補の追加 include は TPC-C 9 TU にだけ増え、TRACE=0 では非活性でなければならない。依存出力でも consumer の漏れを照合する。

根拠: 上表、`CC/cc/{silo,si,mocc}/CMakeLists.txt:1`。

### D297 の再利用範囲

`tools/check_trace0_preprocess_identity.py` の `_comparison_evidence` は digest と実値の比較に再利用できる。一方、`check()` / `_compare_file()` をこの証拠の本体として流用しない。

理由は以下。

- header 差分を `_validate_diff()` が明示拒否する。
- `_mark_includes()` は include を marker に**置換**するため、header から供給される定義を評価しない。
- `_cpp_normalize()` は include を除去して `-nostdinc` で実行する。
- 現物の `_cpp_normalize()` は既に `-dD` を使用している。D297 決定時の「define が出力に残らない」という説明を、そのまま現行実装の説明にしない。
- `_lex_normalize()` は文字列内容を消す。完全展開出力の同一性検査には使わない。

job dir の script から import する場合は、引数で受けた `W` を `sys.path` に追加し、bytecode 書込みを無効にする。checker は変更しない。

根拠: `tools/check_trace0_preprocess_identity.py:180`, `:253`, `:366`, `:516`、`orchestrator/campaign/source_digest.py:1647`, `:1686`, `:1788`。

### 実施手順

1. pin と候補を別の一時 checkout に用意する。依存は同じ固定 source・生成 header・toolchain を使う。
2. 両側を `CCBENCH_TRACE=0`、`CMAKE_EXPORT_COMPILE_COMMANDS=ON` で configure。対象 target を build しなくても全 consumer の flags を得る。
3. compile command を `shlex` 等で argv 化する。`-c`・object 出力・依存 file 出力オプションだけを除去し、`-D/-U/-I/-isystem/-std` 等は保存する。
4. `-E -P -dD` で **実 header を展開**する。正規化は既知の source/build root の対応付けと空行処理に限定し、文字列・数値・`__LINE__` 展開値を消さない。
5. 別 pass の `-E -dI` で活性 include directive を採り、line marker の file 入退場情報も採る。既知 root を対応付けた、順序付きの「include 元・operand・展開先」を比較する。`-H` / dependency list は補助とし、集合一致だけで済ませない。
6. 21 entry それぞれの argv、compiler identity、旧新 digest、比較件数、差分先頭を記録する。失敗・欠落・比較 0 件を拒否する。
7. 最低限、計算ノードで binary を作る compiler と同じものによる比較を必須とする。利用可能な別 compiler の比較は追加証拠とし、別 compiler 間の出力を相互比較しない。

`-dI` を使うのは、include を置換せず、header が条件マクロを供給する実際の順序を維持して活性を採るためである。追加 `trace.hh` が TRACE=0 で活性化する負例を、この比較 script の自己試験に入れる。

**注意:** CMake configure 自体も compiler 判定の小さな try-compile を伴いうる。P2 の login configure は親の許可された環境で行う選択肢とし、必要な生成物・compiler が無ければ同じ計算 job 内で行う。依存未生成による前処理失敗を skip しない。

根拠: `CC/cmake/ProtocolHelpers.cmake:34`, `:41`, `:62`、`tools/check_trace0_preprocess_identity.py:636`, `:678`。

### D297 本体の期待結果

親が pin→最終候補について通常 CLI を実行し、**rc=1、header 変更は保証範囲外という拒否**を記録する。`--expect-paths` は変更 3 file を指定する。

これは期待された制約の確認であって、D297 pass でも pin 前進の承認でもない。代替比較の成功とは別欄に記録し、単位 11 の未解決条件として残す。

根拠: `tools/check_trace0_preprocess_identity.py:195`, `:674`, `:728`, `:746`、`J/s1-brief.md:23`。

## 5. 計算ノード probe — 1 job

### 構成と build

B が job dir 用 probe を実装し、親が次の形で投入する。

```text
python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:30:00 --
  /usr/bin/python3 <J>/probe/run_probe.py
  --repo-root <W>
  --candidate-oid <C2>
  --bundle <J>/C.bundle
  --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache
  --scratch-root /scr
  --out <J>/evidence/compute.json
```

実際は改行を含まない argv 列として渡す。generic は shell 展開を行わず、環境 allowlist は空。親の `TMPDIR`・`PYTHONPATH`・`LD_LIBRARY_PATH`・`CC/CXX`・trace 環境を暗黙に引き継ぐ設計にしない。必要な path は引数、benchmark の `IZANAGI_TRACE_DIR` は子を起動する probe が設定する。

根拠: `tools/pegasus/dispatch_compute.py:155`, `:354`, `:1573`, `:1661`, `:1841`, `:1880`。

job 内の順序は次とする。

1. compute host・toolchain・入力 OID・bundle digest を照合。C1 の親=pin、C2 の親=C1、合成差分=変更 3 file を確認。
2. `/scr` の一意な専用 directory を作成。利用不能なら無断で共有領域へ大量 trace を出さず停止。
3. `fetch_third_party.py hydrate` で依存 cache を展開。gflags/glog の HEAD と clean 状態を確認。
4. gflags を static/PIC、`REGISTER_INSTALL_PREFIX=OFF` で install。glog はその prefix を使い、GTest/testing/unwind を無効化して install。
5. masstree・mimalloc・googletest は `FETCHCONTENT_SOURCE_DIR_*` で hydrated source に固定。
6. build 木は `pin TRACE=0`、`候補 TRACE=0`、`候補 TRACE=1` の 3 個。CCBench target は **`tpcc_silo.exe` と `ycsb_silo.exe` だけ**。
7. Release、sanitizer OFF、ccache OFF、compiler と launcher を明示。protocol options は silo stock の既定値を使い、mocc の `STOCK_G` を流用しない。
8. 上節の consumer 前処理比較、binary 比較、probe 自己試験、TPC-C/YCSB 各 1 run と検証を行う。

依存 preparation と toolchain binding は既存先例を再利用できるが、候補同定・mocc patch 適用・mocc target 固定の関数は呼ばない。先例の `_verify()` は expected-commits を渡していないので、そのまま流用しない。

根拠: `orchestrator/campaign/s3_mocc_lock_coverage.py:147`, `:190`, `:224`, `:257`, `:314`, `:387`, `:604`。

### 走行条件と容量

| 項目 | TPC-C | YCSB |
|---|---|---|
| threads | 2 | 2 |
| extime | 1 秒 | 1 秒 |
| dataset | 1 倉庫 | 200 records |
| mix | Payment=43、OrderStatus/Delivery/StockLevel=0 | rratio=50、rmw=true、max_ope=5、skew=0 |
| interactive delay | 0 | — |
| clocks_per_us | 2100 | 2100 |
| process timeout | ロード込み 120 秒 | ロード込み 120 秒 |

TPC-C の NewOrder 用 percentage flag は無い。上記の閾値設定で残りが NewOrder 57% になる。**生成比率であり、commit の件数比を 57:43 に一致させる試験にはしない。** 両取引種別の commit が観測されることは要求する。

2100 は Pegasus の既存 probe と揃える値で、今回新しく校正した値とは記さない。想定 host と異なる場合は取り直す。

根拠: `CC/include/tpcc/tpcc_common.hh:6`、`CC/include/tpcc/tpcc_query.hh:57`, `:289`、`CC/include/ycsb.hh:19`、`orchestrator/campaign/s3_mocc_lock_coverage.py:47`。

trace は `/scr/<一意名>/tpcc` と `/scr/<一意名>/ycsb` に分離する。各 run の directory は空から開始する。worker の file 数を最大 2 本に限定し、benchmark 子に `RLIMIT_FSIZE=512 MiB` を設定すれば trace の物理上限は各 run 1 GiB、両方保持しても 2 GiB。追加 file や上限到達、timeout、非 0 終了は失敗とし、部分 trace を合格にしない。

生成率・総 bytes・ロード込み時間・検証時間を記録する。生 trace は検査後に SHA-256、file 別 byte/C/E 数、各取引種別の少数の完全 frame、OrderLine 見本だけを残し削除する。digest だけでは後日の再検証ができないという保存限界も記す。

根拠: `CC/include/trace.hh:49`、`orchestrator/campaign/pipeline.py:421`, `:446`、`J/verbatim/tpcc-design-README.md:299`。

### (a) v3 構造検査

B の parser は streaming で処理し、次を要求する。

- tag/token 数: C=10、R=6、W=7、X=5、P=2、E=2。
- ASCII、各行 LF 終端、整数 field は符号無し十進。未知 tag、I/A/S/Q、v1/v2 C、table の無い旧 R/W/X を拒否。
- txid は `0..2^64−1`、thid は `0..1` かつ file 名と一致。
- epoch は `0..2^32−1`、tid は `0..2^29−1`。C の genesis `(1,0)` は拒否、R の genesis は許容する。
- count は非負整数、段 1 では nS=nQ=0。table は 0〜10、tx_type は **この probe では 1〜2**。
- key は非空の偶数長 lowercase hex。OrderLine 復号では厳密に 8 byte を要求する。OrderSecondary は 16 byte なので全表一律 8 byte にしない。
- W の op は U/I/D、W の epoch/tid は所属 C と一致。
- file ごとに open frame は高々 1 個。C→R群→W群→X群→E、全 txid 相関が一致。E の欠落・重複・余分な後続行を拒否。
- nR/nW は E 時点の実行数と一致。X は nW に加算しない。
- txid は全 file を通じて一意、集合は 0 始まりの密連番。thread 内では増加を要求するが、他 thread の採番が挟まるので差分 1 は要求しない。
- P は txid 非相関として読む。正常 producer では frame 間に出る。正しい形の X/P も「構造が読める」と「正常対照の合格」を分け、正常 run の受入は X=P=0。
- 両 tx_type、R、W、OrderLine INSERT が正の件数であることを要求し、空入力を合格にしない。

根拠: `CC/cc/silo/include/tuple.hh:12`、`CC/include/tpcc/tpcc_tables.hh:16`, `:295`, `:329`、`CC/include/trace.hh:41`、`orchestrator/verifier/parse.py:20`, `:321`, `:402`, `:473`。

### (b) stdout witness

`orchestrator/campaign/pipeline.py:347` の `_parse_commit_witness()` を read-only import して使用する。stdout 全文から `commit_counts_` と `batch_commit_counts_` がそれぞれ一意な非負整数であることを要求する。

受入条件は次の完全一致。

```text
process rc == 0
commit_counts_ > 0
batch_commit_counts_ == 0
全 file の C 行数 == commit_counts_
全 file の E 行数 == C 行数
```

per-tx の `commits:` 行を総 witness と混同しない。stdout 欠落・重複・負数・batch 非 0 を拒否する。`_run_trace()` は TPC-C を拒否するので呼ばず、起動部分は job-local probe に置く。

根拠: `CC/common/result.cc:47`, `:685`, `:735`、`orchestrator/campaign/pipeline.py:328`, `:347`, `:434`。

### (c) YCSB の既存認定

YCSB の C がすべて 7 token、R/W/X が v2 の token 数であることを確認し、得た witness を現行 CLI に渡す。

```text
python3 <W>/orchestrator/verify.py <ycsb-trace-dir>
  --expected-commits <stdoutから得た値>
  --protocol silo
  --ccbench-root <実際にbuildした候補source>
  --json
```

rc=0、`runs=1`、`certified_serializable=1`、個別結果の `certified=true` と txn 数一致を要求する。`--lenient` は使用しない。`--ccbench-root` に pin の source を渡して候補の証拠面欠落を隠さない。

根拠: `orchestrator/verifier/cli.py:38`, `:65`, `:80`, `:105`。

### (d) TRACE=0 binary 比較

pin/candidate の `tpcc_silo.exe`、`ycsb_silo.exe` の 2 組を比較する。

- compiler・依存・全 macro/optimization flags を揃える。
- source/build の絶対 path 差で `__FILE__` が変わるため、両 build に対称な `-ffile-prefix-map` を与え同じ論理 root にする。追加比較用 flag として明記する。
- 各 binary の `nm -C` で `izanagi_trace`/追加 context/helper 記号が 0。
- `strings -a` で `izanagi_trace`、`IZANAGI_TRACE_DIR`、固有の trace reason 等が 0。汎用的な文字列 `trace` 全体を禁止しない。
- `objdump -d --no-show-raw-insn` を同名相対 binary に対して実行し、先例の address-label 正規化後を完全一致で比較する。
- operand・即値・分岐先・関数名を消して一致させない。差があれば調査して止め、正規化を拡張して緑にしない。

compiler flags、binary digest、正規化 disassembly digest、差分を保存する。これは選定構成での証拠であり、全 compiler・全 macro 組合せの保証とはしない。

根拠: `orchestrator/campaign/s3_mocc_lock_coverage.py:439`, `:444`, `:844`、`J/verbatim/D297.md:3`。

### (e) OrderLine の復号と P5 の修正

`W ... table=8 ... op=I` を対象に、hex を bytes に戻す。

| byte offset | 内容 |
|---|---|
| 0〜1 | warehouse、big-endian uint16 |
| 2 | district、uint8 |
| 3〜6 | order ID、big-endian uint32 |
| 7 | line number、uint8 |

`min(line_number)=0` と、少数の `(txid,w,d,o,line)` を記録する。同じ注文の line 集合が 0 始まりであることも確認する。

根拠: `CC/include/tpcc/tpcc_tables.hh:331`、`CC/include/tpcc/tpcc_tx_neworder.hh:314`, `:334`。

**P5 は限定修正する。** この trace が実証するのは実行時 INSERT の 0 始まりである。初期ロードの 1 始まりは `tpcc_initializer.hh:279` の静的根拠であり、初期ロード key の実測や隣 order を scan する現象の再現とは呼ばない。

他所見も一括して「到達しない」と書かない。

- 公開後・write set 登録前 return: scan→insert が必要で、現行段 1 では到達しない。
- abort 即時解放: abort 自体は段 1 でも起こるが、問題となる競合参照の再現は今回対象外。
- si の read set 消去・v1 trace: Payment 等でも関係するが、**si を走らせないため未検証**。
- OrderStatus・Delivery 固有所見: mix から除外されている。

根拠: `J/verbatim/tpcc-design-README.md:347`、`J/verbatim/D2219.md` 項 7。

### (f) probe の自己試験

少数の手書き正常 frame と複数 thread fixture を用意し、各負例を単独変異として拒否理由まで確認する。

| 負例 | 期待 |
|---|---|
| C/R/W/X/E の token 過不足、非数値、負数、上限超過 | 構造拒否 |
| table=-1/11、tx_type=0/3/6、nS/nQ 非 0 | 段 1 契約拒否 |
| 大文字・奇数長・非 hex key、OrderLine の長さ違い | key 拒否 |
| nR/nW 改変、R/W 1 行削除 | count mismatch |
| E 削除・重複・別 txid、C の入れ子 | frame 拒否 |
| 別 txid の R/W/X 割込み、閉じた frame への追記 | 相関拒否 |
| 同一/別 file の C 重複、txid 欠番、thid/file 不一致 | 一意性・連続性拒否 |
| W 版を C と不一致にする、未知 op | version/op 拒否 |
| v2 frame/旧 R/W/X、I/A/S/Q を混入 | schema 拒否 |
| 正しい形の X または P を追加 | parse 可、正常対照は不合格 |
| 末尾 frame・最大 txid frame・thread file を丸ごと削除 | witness 不一致 |
| stdout label 欠落・重複・負数・batch 非 0 | witness 拒否 |
| 空 trace、非 ASCII、最終 LF 欠落、process 非 0 | 実行受入拒否 |

表 5 と表 6 に同じ key が出る fixture は正常として受理する。別表を key 単独で重複扱いする検査器にしない。

根拠: `J/verbatim/tpcc-design-README.md:75`, `:245`、`orchestrator/verifier/parse.py:343`, `:365`, `:402`。

### 所要見積り

推測として、依存 preparation・3 build 木・前処理比較・2 run・検証で **0.3〜0.5 node 時間**。再投入 1 回を含め 1.0、superproject 受入 1〜2 回を約 0.25 ずつ加え、合計 **1.25〜1.5 node 時間**を予算とする。

job の Elapse で更新し、再試行を含む合計見込みが **2 node 時間以上**になる前に親が確認する。queue 待ちと Codex の所要は別計上。probe の赤を理由なく再走して偶然の緑を採らない。

根拠: `J/s1-brief.md:37`、`J/verbatim/D2219.md` 項 1。

## 6. commit 経路と停止地点

### 2 commit の切れ目

- **C1:** `include/trace.hh` と `include/tpcc.hh`。v3 API/context、全終了経路の clear、TRACE 限定計数修正。
- **C2:** `cc/silo/transaction.cc`。C/R/W/X の選択、E 後 clear、`#line` 復元。
- ancestry は `pin → C1 → C2`。branch は `izanagi-tpcc-v3-trace`。
- C1 単独では silo は従来の trace を出す。内部受入は C2 に対して行う。

根拠: `J/s1-brief.md:24`、`J/verbatim/tpcc-design-README.md:278`。

### 親の操作順

1. A の disposable clone の起点と差分 3 file を確認し、親が単位別 patch と最終 blob digest を採る。
2. T-2844 の先例同様、wave submodule の object store から `J/C-worktree` に pin の detached worktree を作る。
3. branch の既存 local/ref 衝突を確認。別 OID の同名 branch があれば停止。
4. 単位 1 patch を `git apply --check` → apply。staged path を 2 file と照合して C1 を `commit -F`。
5. 単位 2 patch を同じ順序で適用し、staged path を 1 file と照合して C2。
6. C1/C2 の親、tree、変更 blob、最終差分を記録。author clone と最終 3 blob が一致することを確認。
7. branch 全体の自己完結 bundle を作り verify。C1/C2 OID と bundle digest を保存する。
8. 主 checkout の `external/ccbench` 保管庫へ、bundle から `refs/heads/izanagi-tpcc-v3-trace` を**非 force fetch**。同名 ref が別 OID なら停止。同一 OID なら再作成しない。
9. wave/main 双方の submodule HEAD・working tree・outer gitlink が pin のままであることを照合する。

先例との差分は、単一 blob 固定から 3 blob 固定、1 commit から C1/C2、mocc 専用 branch/patch/検証を TPC-C 用へ変更する点。失敗時に一時 worktree を force 削除する先例部分は踏襲せず、診断材料を保持して停止する。

根拠: T-2844 `mk-C-commit.sh:28`, `:34`, `:37`, `:43`, `:52`, `:70`、`fetch-C-to-main.sh:19`, `:20`, `:26`。

### provenance

message file の最終 trailer block は次の形式とする。値は実際の author/reviewer/親の実行記録から埋め、先例のモデル値をコピーしない。

```text
AI-Agent: product=codex; model=<表示値>; reasoning=<表示値>; role=author; scope=ccbench-v3
AI-Agent: product=<実際の製品>; model=<表示値>; reasoning=<表示値>; role=reviewer; scope=ccbench-v3
AI-Agent: product=<実際の製品>; model=<表示値>; reasoning=<表示値>; role=integrator; scope=ccbench-v3
```

実質的に寄与した role だけ記載する。不明値は規約の `unknown` / `not-exposed` に従う。message 検査、commit 後監査を親の通常経路で行う。

根拠: `docs/ai-provenance.md:8`, `:23`, `:44`, `:65`, `:79`。

### hook・classifier の停止条件

- `external/ccbench/include/{trace,tpcc}.hh` の直接編集は guard_write の編集面外。試みない。
- A の作業面は F546 の disposable clone。submodule への symlink や同じ作業 file の別名を使わない。
- login での直接 build/benchmark は行わない。`guard_bash` が検知しない間接実行面でも同じ規律を守る。
- clone 作成、patch 適用、worktree、commit、bundle/fetch のいずれかで hook/classifier が拒否したら、その操作で止める。shell・別 path・別 tool・hook 無効化で同じ操作を通さない。
- 特に D41 の拒否先例があるため、P7 は「F546 と今回 scope に基づく予定経路」であり、classifier が必ず許可するとの断定はしない。

根拠: `hooks/guard_write.py:44`, `:323`、`hooks/guard_bash.py:1337`, `:2914`, `:2926`、`J/verbatim/D41-excerpt.md:10`、`J/verbatim/F546.md:10`。

## 7. 既存 patch への影響

変更 3 file を対象に検索した結果、`include/tpcc.hh` / `include/trace.hh` に hunk を持つ patch は無く、`cc/silo/transaction.cc` に触れるものは **17 本**。

| patch | 静的予測 |
|---|---|
| `broken-silo-write-intent-ptrswap.patch:5` | validation 後半の文脈を維持。今回差分による衝突は見込まない |
| `broken-silo-write-intent-opswap.patch:5` | 同上 |
| `broken-silo-write-intent-forge.patch:5` | 同上 |
| `broken-silo-write-intent-erase.patch:5` | 同上 |
| `broken-silo-sort-nonswo.patch:5` | sort/P 付近は不変。適用維持見込み |
| `broken-silo-permutation-erase.patch:5` | 同上 |
| `broken-silo-permutation-swap.patch:5` | 同上 |
| `silo-sort-variant.patch:34` | 同上。Options.cmake の hunk も今回不変 |
| `broken-silo-norw-validation.patch:5` | read validation 不変 |
| `broken-silo-highkey-validation.patch:4` | 同上 |
| `broken-silo-lockskip-validation.patch:5` | lockWriteSet 不変 |
| `broken-silo-early-unlock-validation.patch:5` | 元 640 行の write loop 文脈を維持。`#line 635` が hunk 外に収まる案なので維持見込み |
| `silo_ladder_rung1.patch:5` | 冒頭と CAS 文脈を維持。ycsb_silo.cc も不変 |
| `silo-backoff-trigger-gating-variant.patch:34` | 冒頭・begin/abort・validation の文脈を維持 |
| `broken-silo-trigger-misattr.patch:5` | trigger-gating skeleton が前提。素の pin への失敗は今回の回帰ではない |
| `instr-silo-backoff-trigger-gating-tally.patch:5` | trigger-gating 用の計装。前提を揃えた適用確認が必要 |
| `silo-backoff-requested-us.patch:51` | transaction の冒頭・abort は維持。Options/backoff の前提 patch が必要 |

以上は**推測であり、適用成功の実証ではない**。本案で直接衝突が予測される hunk は無いが、不要な冒頭変更、begin/abort への clear 追加、P 周辺への `#line` 追加をすると影響面が増える。

親は pin と候補の clean scratch checkout の両方で、各 patch の `git apply --check` を実行して rc/stderr を保存する。前提付き patch は前提列と digest を明記した別の使い捨て checkout で確認する。候補だけの結果から「17 本すべて回帰」と数えず、今回新しく失敗したものを区別する。patch bytes は修正しない。

根拠: 上表、`J/s1-brief.md:28`。

## 8. 負例・変異の選択

P4 の DW-S04 免除想定を採用する。ただし、probe の `.py/.sh/.patch` を superproject の tracked 成果物へ含めないことが条件。含めれば「実装面差分 0」ではなくなる。probe 本体と実行資材は job dir、repo の記録は Markdown・結果に留める。

根拠: `J/s1-brief.md:25`, `:31`、`docs/ai-provenance.md:46`。

優先するのは §5(f) の決定的な自己試験。追加 C++ build を伴う変異は次の評価とする。

| 候補 | 費用・検出性 | 判断 |
|---|---|---|
| `#if !TRACE` を戻して旧計数へ | header 変更なので tpcc TU の再 build が必要。終了時に成功 commit が重なるかは非決定的 | 既定では行わない |
| tx_type setter を 0 にする | tpcc TU 再 build。TPC-C に v2 C が出るため検出は確実 | 必要時の第一候補 |
| v3 C の nW を `size()+1` にする | transaction TU 再 build。W のある run で確実に count mismatch | 安価だが自己試験との重複が大きい |
| E 出力を消す | transaction TU 再 build。確実に missing-end | 同上 |
| `#line` を外す | build 前の実前処理比較で検出可能 | 比較 script の負例に向く |

旧計数への戻しを 1 秒走で検出できても、未検出でも、境界条件の決定的証明にはならない。厳密な帰属には「commit 成功直後に quit を立てる」制御が必要で、今回の 3 木・2 run の最小構成には加えない。追加が必要になった場合は B/A の scratch 診断資材に限定し、費用を再積算する。

根拠: `CC/include/tpcc.hh:102`, `:110`、`J/verbatim/tpcc-design-README.md:254`。

## 9. 所有 path・接点・順序

### 素集合の所有

| 担当 | 書込み所有 |
|---|---|
| Codex author A | `W/output/runs/t2854-ccbench-v3/ccbench/include/trace.hh` |
| 同上 | `W/output/runs/t2854-ccbench-v3/ccbench/include/tpcc.hh` |
| 同上 | `W/output/runs/t2854-ccbench-v3/ccbench/cc/silo/transaction.cc` |
| Codex author B | `W/output/runs/t2854-ccbench-v3/probe/` 配下の probe・自己試験・比較・実行補助 script |
| 親 | A の patch 抽出、B 資材の `J/probe/` への退避、`J/C-worktree` の適用・commit、bundle/fetch、投入・受入・記録 |

A/B は互いの path、実 `external/ccbench`、既存 verifier/pipeline/checker、既存 patches を編集しない。追加/fix は所有 author へ返す。B が commit 補助 script を実装しても、実際の Git 統合操作は親が行う。

根拠: `J/s1-brief.md:34`、`J/verbatim/F546.md:10`、`J/verbatim/D95.md:10`。

### 接点の固定

並列着手前に固定するのは次の 4 点。

1. v3 の field 順、C/R/W/X/P/E の token 数、table/tx_type の数値対応。
2. stdout witness は `commit_counts_:` と `batch_commit_counts_:` の一意な行。
3. probe が受けるのは C2 OID・bundle・repo-root。未 commit の A 作業面を直接測定しない。
4. C2 の差分 3 file と blob digest、正常 TPC-C は `structure+witness pass`、YCSB は `certified` と結果名称を分ける。

根拠: `CC/common/result.cc:47`、`J/s1-brief.md:19`、`orchestrator/verifier/cli.py:84`。

順序は「frame/context 契約固定 → A/B 並列作成 → 親の 2 commit 固定 → login の可能な静的比較・D297 拒否記録・patch 検査 → compute 1 job → review/fix → superproject 受入 → docs 記録・bundle 保全・主保管庫 fetch」。修正で C2 が変わった場合は、その最終 source に対応する必要な証拠を取り直す。

## 総括

- **実装:** `trace.hh` に外部 linkage の inline TLS accessor と v3 helper、`tpcc.hh` に begin 後 setter・全終了経路の clear・TRACE 限定計数修正、silo に排他的な v2/v3 emitter を入れる。C は 1 txn 1 本。根拠: `CC/include/tpcc.hh:55`、`CC/cc/silo/transaction.cc:601`。
- **P1 賛成、補強:** 成功時だけでなく abort・commit 失敗時も clear。既存 compile 定義に workload 区別が無い点は確認できた。
- **P2 条件付き賛成:** 実 header を展開する 12 TU・21 compile entry の比較が必要。D297 本体は header 拒否を記録し、pass と称さない。根拠: `tools/check_trace0_preprocess_identity.py:195`。
- **P3 賛成:** `pin→C1(headers)→C2(silo)` の 2 commit。内部受入は C2。根拠: `J/s1-brief.md:24`。
- **P4 賛成:** 3 build 木・2 target・短い 2 run と決定的な probe 自己試験。TPC-C の結果は構造・witness 合格まで。根拠: `J/s1-brief.md:6`, `:25`。
- **P5 一部修正:** runtime OrderLine の 0 始まりを実測する。初期ロードとの相違は静的根拠との対比。si 所見は「到達不能」ではなく「対象外・未検証」。根拠: `CC/include/tpcc/tpcc_initializer.hh:279`、`CC/include/tpcc/tpcc_tx_neworder.hh:314`。
- **P6 賛成:** 対象 patch は 17 本。pin/candidate と前提列を揃えて比較し、今回の適用回帰だけを識別する。
- **P7 条件付き賛成:** F546 の disposable clone と親の一時 worktree 経路を使う。hook/classifier の拒否時はその地点で停止する。根拠: `J/verbatim/F546.md:10`、`hooks/guard_write.py:323`。
- **未確定:** 実 toolchain での警告 0、全 consumer の前処理/include 活性一致、binary 一致、patch 適用結果、trace/witness/YCSB 認定結果、実 node 所要、classifier の許可。いずれも本 read-only plan では実証していない。