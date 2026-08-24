# CCBench 還元候補 — SS2PL の YCSB バイナリ欠落、DLR0 の記述と実装の食い違い、他 3 件

- authority: none
- default_effect: no-state-change
- 還元判断: **ユーザー確認待ち**
- 発見: 2026-08-25、dev-wave `dev-wave-ss2pl-lock-study` の作業中
- CCBench commit: `511c9538e4e8efa54b45cda62e72389ed3b706ec`
- 環境: Pegasus 計算ノード (Intel Xeon Platinum 8468、48 physical core、
  `g++ 11.4.0`、`cmake 3.25.0`)

AI は発見を構造化するところまでを行う。上流 CCBench へ PR を出すかは人間が判断する。

---

## 発見 1 — SS2PL に YCSB バイナリが存在しない

**何が。** 現行の `cc/ss2pl/CMakeLists.txt` は `WORKLOADS bomb tpcc` しか登録していない。
`cc/ss2pl/ss2pl.cc` は旧 Makefile 時代の YCSB main の残骸で、
現行の `TxExecutor` が要求する 3 引数コンストラクタ (`thid`, `result`, `quit`) ではなく
2 引数版を呼ぶため、**ビルド対象からも外れている。**
結果として、**SS2PL では YCSB を 1 度も測れない。**

**再現条件。** `cmake --build <build> --target ycsb_ss2pl.exe` が
`No rule to make target` になる。`cc/silo` には `ycsb_silo.cc` が実在する。

**該当コード。** `cc/ss2pl/CMakeLists.txt:3`、`cc/ss2pl/ss2pl.cc:38`、
`cc/ss2pl/include/transaction.hh` の `TxExecutor` コンストラクタ。

**仮説。** cmake 移行 (`ccbench_add_protocol`) の際に、
`ycsb_<name>.cc` という命名規約に合わない `ss2pl.cc` が拾われずに落ちた。
`bomb_ss2pl.cc` と `tpcc_ss2pl.cc` は規約に合っていたので残った。

**確かめたこと。** `cc/silo/ycsb_silo.cc` (64 行) と `cc/ss2pl/bomb_ss2pl.cc` (59 行) を
雛形に `ycsb_ss2pl.cc` を書くと、共通 runner `ccbench::run<TxExecutor, TransactionStatus,
YcsbWorkload>` でそのまま動く。実測で 7 つのビルド構成すべてが通り、
1M records の YCSB-A が走った。

---

## 発見 2 — `DLR0` は README が言う timeout ではなく、解決機構を持たない素の待ちである

**何が。** `cc/ss2pl/README.md:43` は

> `DLR0` : Dead lock resolution is timeout.

と書く。しかし実装 (`cc/ss2pl/transaction.cc:172, 263, 309, 411, 436`) は
`r_lock()` / `w_lock()` / `tryupgrade()` を呼ぶだけで、**timeout も解決機構も存在しない。**
`DLR0` でビルドすると素の待ちになり、デッドロックが起きたらプロセスは終わらない。

**再現条件。** `DLR0` でビルドし、YCSB-A / 1,000,000 records / zipf skew 0.9 /
48 threads で走らせると、5 秒の実行時間指定に対して 60 秒でも終わらない (hard timeout が要る)。
wait-for graph を取ると閉路がある。実測した 2 node の閉路:

```
thread 20 (attempt 1, lock 0x14a0fc0041c0, 要求 read,  commit 0, abort 0)
thread 22 (attempt 1, lock 0x14a0fc003c80, 要求 write, commit 0, abort 0)
20 -> 22 (lock 0x14a0fc0041c0, holder mode write)
22 -> 20 (lock 0x14a0fc003c80, holder mode write)
```

100 records / 48 threads の高競合点では 6 node の閉路が立った。
一方 1M records で **skew を 0 (一様)** にすると 5 秒の観察窓では閉路が立たなかった
(競合 408 件のみ)。つまり 1M records でのデッドロックは競合の集中を要する。

**還元の選択肢 (人間が選ぶ)。**
(a) README を実装に合わせて「解決機構なし (待つ)」と直す。
(b) README が言うとおり timeout を実装する。
(c) `DLR0` を廃止する。

---

## 発見 3 — abort 数が protocol 側と workload 側で二重に加算される

**何が。** `include/ycsb.hh:151,163` は `tx.abort()` を呼んだ直後に
`local_abort_counts_` を加算する。一方 `cc/ss2pl/transaction.cc:56` の
`TxExecutor::abort()` も同じ counter を加算する。**SS2PL を YCSB へ載せると abort 数が 2 倍になる。**

`cc/silo/transaction.cc` の `abort()` は加算しない (grep で全 protocol を確認)。
つまり加算責任は workload 側にある、というのが現行の暗黙の規約であり、SS2PL がそれに従っていない。

**なぜ今まで露出しなかったか。** 発見 1 のとおり SS2PL に YCSB バイナリが無く、
BoMB / TPC-C 側の driver は別の計上経路を持つため。

**影響。** abort 率をそのまま報告すると 2 倍になる。throughput は影響を受けない。

---

## 発見 4 — 旧 YCSB フラグ定義が残り、表示と実データが食い違う

**何が。** `cc/ss2pl/include/common.hh` は
`tuple_num` / `rratio` / `max_ope` / `rmw` / `zipf_skew` / `ycsb` を今も `DEFINE_*` している。
現行の `include/ycsb.hh:19-32` は同じ意味の値を `ycsb_` 接頭辞付きで**別の gflag として**定義する。
両者は名前が違うので重複定義エラーにならない。

`cc/ss2pl/util.cc` の `chkArg()` は旧 `FLAGS_rratio` を検査し、
`displayParameter()` は旧値を表示する。一方 `YcsbWorkload::makeDB` は `FLAGS_ycsb_tuple_num` を読む。
したがって `-tuple_num=1000000 -ycsb_tuple_num=10000` を同時に渡すと、
**「1,000,000 records」と表示しながら実際には 10,000 件の DB で走る。**

`cc/silo/include/common.hh` は同じ旧名を `DECLARE_*` するだけで `DEFINE_*` していない。

**影響。** 測定条件のラベルが実データと食い違いうる。悪意がなくても、
古い実行スクリプトを流用しただけで成立する。

---

## 発見 5 — silo の YCSB が `VAL_SIZE=8` でビルドできない

**何が。** `-DCCBENCH_VAL_SIZE=8` で `ycsb_silo.exe` をビルドすると
`-Werror=array-bounds` で失敗する。`VAL_SIZE=4` (既定) なら通る。

```
cc/silo/include/log.hh:43  LogRecord::LogRecord(uint64_t, std::string_view, char*)
  <- cc/silo/transaction.cc:497  TxExecutor::wal(uint64_t)
error: forming offset [6, 7] is out of the bounds [0, 6] [-Werror=array-bounds]
```

`WAL` が既定 0 でも `TxExecutor::wal()` の本体はコンパイルされるため落ちる。
SS2PL は `VAL_SIZE=8` で問題なくビルドできる。

**影響。** payload 8 bytes の実験を silo で行えない。
本 wave は SS2PL が対象だったので障害にならなかった。

---

## 発見 6 — `cc/ss2pl/test/` がビルドグラフに繋がっていない

**何が。** `cc/ss2pl/test/CMakeLists.txt` は実在するが、
`cc/ss2pl/CMakeLists.txt` からも top-level からも `add_subdirectory` されていない。
したがって `make_db_test` は**1 度もビルドされていない。**
実際、`make_db_test.cpp` の include パス (`../../include/common.hh`) は実在しないファイルを指しており、
繋いだ瞬間にビルドエラーになる。

**影響。** SS2PL のテストが緑かどうかを誰も確かめていない。

---

## 本 wave での扱い

いずれも out-of-tree patch (`patches/ss2pl-lock-protocol-study.patch`) の中で局所的に対処し、
submodule の tracked file は 1 byte も変更していない (D16 / D18)。
上流への還元は人間の判断に委ねる。
