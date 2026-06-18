# patches/ — Izanagi の CCBench 改変

CCBench (`external/ccbench` submodule = `thawk105/ccbench`) への Izanagi 由来の改変は
**性質ごとに行き先を分ける** (D16。当初は全て out-of-tree patch だった = D6):

| 改変 | 性質 | 行き先 |
|---|---|---|
| スレッドピンニング (`-DLinux`) | CCBench 本物のバグ修正 (Izanagi 非依存) | **submodule `master`** に還元 |
| trace-hook (Silo/si の `#if TRACE` 検証計装) | Izanagi の verifier 入力。`#if TRACE` で観測者効果セーフ | **submodule `izanagi-trace` ブランチ** (submodule が追う) |
| broken-silo (わざと壊した Silo) | verifier の赤検出用 positive control = **テスト用の意図的バグ** | **out-of-tree patch** (このディレクトリ。永久) |

**broken-silo を patch に隔離する理由 (絶対規律2):** 壊した CC をブランチに commit すると
baseline として誤ビルドされる危険がある。out-of-tree patch なら「赤検出証明をするときだけ
明示的に重ねる」inert 状態を保てる。

## submodule の階層

```
master (CCBench 本体 + pinning 修正)
  └─ izanagi-trace (+ trace-hook Silo/si)   ← submodule が pin する (.gitmodules の branch)
       └─ broken-silo-norw-validation.patch  ← 赤検出 ablation のときだけ重ねる (out-of-tree)
```

submodule は `izanagi-trace` の特定 commit を pin する (`.gitmodules` の `branch = izanagi-trace`)。
**parent の gitlink は常に特定 commit を固定する**ので再現性は patch 運用時と同じく保たれる。
trace-hook の追加開発は submodule の `izanagi-trace` ブランチに直接コミットし、parent の
gitlink を前進させる (submodule の working-tree dirt を放置しない方針に変わった = D16)。

ビルドモード (絶対規律1: 観測者効果分離):
- **perf ビルド** (`build/`, 既定 `-DTRACE=0`): trace は `#if TRACE` で完全に消える。
  pinning は master 由来で常に有効。性能計測・calibration はこれに当てる。
- **trace ビルド** (`build-trace/`, `-DCCBENCH_TRACE=1`): trace を吐く。正しさ検証専用。
- 実証済み: `TRACE=0` ビルドのバイナリに `izanagi_trace` シンボル 0 個 (`nm`/`strings`)。

---

## broken-silo-norw-validation.patch — verifier の検出力証明 (Phase 1 タスク3, Approach A)

**わざと壊した CC** (positive control)。Silo の `validationPhase()` 条件#1 (read-set の
tidword 再検証 = anti-dependency / stale-read チェック) を **macro `IZANAGI_BREAK_NOREAD_VALIDATION`
で抜く**。stale read が abort されず commit するので、lost-update / write-skew の **G2 cycle が
trace に出現**し、verifier がそれを赤と判定できることを実証する。

- **既定 OFF**: macro 未定義時は `#else` で元の abort が compile-in されるので**挙動は完全に元の
  Silo** (inert)。**正しさ/性能の baseline には絶対に混ぜない** (絶対規律2)。
- **`izanagi-trace` (trace-hook 入り) の上に重ねて適用する** (validationPhase を触る。trace-hook の
  writePhase と非衝突。`git apply --check` で round-trip 確認済み)。

```sh
SUB=external/ccbench
# submodule は既に izanagi-trace (trace-hook 入り) を pin している。壊しを重ねる:
git -C "$SUB" apply ../../patches/broken-silo-norw-validation.patch
# 壊し+trace 専用ビルド (別 build dir)
cmake -S "$SUB" -B "$SUB/build-trace-broken" -DCMAKE_BUILD_TYPE=Release \
      -DENABLE_SANITIZER=OFF -DCCBENCH_TRACE=1 \
      -DCMAKE_C_COMPILER=gcc-13 -DCMAKE_CXX_COMPILER=g++-13 \
      -DCMAKE_CXX_FLAGS="-DIZANAGI_BREAK_NOREAD_VALIDATION=1"
cmake --build "$SUB/build-trace-broken" --target ycsb_silo.exe -j
# 高 contention で走らせ verifier にかける → NON-SERIALIZABLE (exit 1) になるはず
git -C "$SUB" checkout -- cc/silo/transaction.cc   # 壊しだけ revert (izanagi-trace に戻る)
```

### 実証 (2026-06-18, clean ablation)

同一ワークロード `-ycsb_rmw=true -ycsb_zipf_skew=0.9 -ycsb_tuple_num=50 -ycsb_max_ope=5 -thread_num=4 -extime=1`:
- **壊し ON**: 293,803 commit → trace に **1310 G2 cycle** → verifier **NON-SERIALIZABLE (exit 1)**
- **壊し OFF (素の Silo)**: 285,047 commit → verifier **certified SERIALIZABLE (exit 0)**
- 差は read validation の有無のみ → verifier は壊れた CC を赤・正しい CC を緑と判定する番人だと確認。

---

## トレース形式 (verifier = タスク2 の入力契約)

trace-hook の**実装**は submodule `izanagi-trace` ブランチにある (Silo は `writePhase` の `maxtid`
確定後、si は `si_commit` の write install 直後に emit)。出力する**形式**は verifier
(`orchestrator/verifier/`) の入力契約なのでここに記録する。

per-thread ファイル `trace_<thid>.log`、1イベント1行。1 trx の records は連続 (C → その R/W 行):

```
C <txid> <thid> <epoch> <tid>             committed txn。<epoch>,<tid> = commit順 = この trx が産んだ版ID
R <txid> <key_hex> <ver_epoch> <ver_tid>  read。見た版 (ver_epoch,ver_tid)
W <txid> <key_hex> <op> <epoch> <tid>     write。op∈{U,I,D}。新版 = この trx の commit (epoch,tid)
```

- `txid` = グローバル単調 id (TRACE ビルド限定の atomic)。1 trx の C/R/W をまとめるためだけ。
- `key_hex` = キー生バイトの小文字 hex (YCSB は 8byte big-endian)
- **版ID = (epoch,tid)。** 同一キー上では producer trx を一意に決める (ww 競合で tid が単調増加)。
- **genesis 版 = (epoch=1, tid=0)** (初期 DB ロード、producer 無し)。si は cstamp=0 がこれに自然一致。

### verifier が辺を復元する方法

- **wr 辺** (T_w → T_r): R の (key,e,t) を、commit (e,t) でその key を書いた W の trx (producer) に対応付け
- **ww 辺**: 同一 key を書いた trx を (epoch,tid) 順に並べる
- **rw 辺 (anti-dependency)**: R が版 V を読み、別 trx が同 key により新しい版を書いたら T_r → T_w
- **G2**: rw 辺を1本以上含む cycle

### trace-hook の検証実績

- タスク1 (Silo): trace の C 行合計 = ベンチ `commit_counts_` 完全一致、非 genesis read の 100% が
  producer に matchable・ORPHAN 0・版重複 0、`TRACE=0` ビルドに trace シンボル 0。
- タスク3B (si): si=本物の write-skew を 3576 G2 として検出、同 workload で Silo は緑 (real-CC discrimination)。
- **ermia cross-check の罠 (将来増分):** `ermia` (SSN on=serializable) を green oracle にするには
  `cc/ermia/transaction.cc` にも hook が要るが、版 cstamp が `cstamp<<1` (低ビット=SSN flag,
  `ssn_commit:561`) で si と違い、commit 経路も `ssn_commit`/`ssn_parallel_commit` の2系統。
  version id 写像をこの shift に合わせないと全 read が orphan 化する。`izanagi-trace` に追加する想定。
