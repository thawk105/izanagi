# patches/ — Izanagi の CCBench 改変

CCBench (`external/ccbench` submodule = `thawk105/ccbench`) への Izanagi 由来の改変は
**性質ごとに行き先を分ける** (D16。当初は全て out-of-tree patch だった = D6):

| 改変 | 性質 | 行き先 |
|---|---|---|
| スレッドピンニング (`-DLinux`) | CCBench 本物のバグ修正 (Izanagi 非依存) | **submodule `master`** に還元 |
| trace-hook (Silo/si の `#if TRACE` 検証計装) | Izanagi の verifier 入力。`#if TRACE` で観測者効果セーフ | **submodule `izanagi-trace` ブランチ** (submodule が追う) |
| broken-silo (わざと壊した Silo) | verifier の赤検出用 positive control = **テスト用の意図的バグ** | **out-of-tree patch** (このディレクトリ。永久) |
| 合成 variant (例: 静的 backoff `BACKOFF_FIXED`) | Izanagi がフラグ空間外に合成した**評価中の正当な variant** (D18) | **out-of-tree patch** (価値確定まで。昇格は人間判断) |

**broken-silo を patch に隔離する理由 (絶対規律2):** 壊した CC をブランチに commit すると
baseline として誤ビルドされる危険がある。out-of-tree patch なら「赤検出証明をするときだけ
明示的に重ねる」inert 状態を保てる。

**合成 variant を patch に置く理由 (D18):** フラグ空間 (CCBench 定義の最適化フラグ) の外へ
合成した variant は、価値が確定するまで submodule 本体に焼かない。default で stock 不変 (inert)
なので baseline を汚さず、verifier が毎回正しさを確認する。勝てば昇格、負ければ patch のまま記録。

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

## silo-backoff-fixed.patch — 静的 backoff (合成 variant, D18) + noinline (診断計器, P2-4)

このパッチは izanagi の silo backoff 追加を 2 つ束ねる: **(1) `BACKOFF_FIXED`** = 量を単一軸に固定する合成 variant (D18)、**(2) `BACKOFF_NOINLINE`** = perf 帰属用の診断計器 (P2-4)。どちらも `cmake/Options.cmake` + `include/backoff.hh` を触り、既定値で inert (stock 不変)。

**フラグ空間外への最初の踏み出し** (Phase 2→3 の橋渡し)。CCBench の backoff は Cicada 由来の
**適応 backoff** (leader が throughput 勾配で global backoff 値を hill-climbing) で、それが 48thread
高競合で throughput を殺す値に収束しているのが `BACK_OFF=1` の正体だった (critic の帰属、
`output/insights/2026-06-22_p2-3-critic-leading-indicator-attribution.md`)。そこで backoff の*量*を
**静的固定する新フラグ `CCBENCH_BACKOFF_FIXED`** を導入し、量を単一軸として sweep する。

- 変更: `cmake/Options.cmake` (cache var + `ccbench_universal_definitions` に `BACKOFF_FIXED`) と
  `include/backoff.hh` (`backoff()` 内で `#if BACKOFF_FIXED >= 0` なら固定値、`#else` で stock の
  適応 `Backoff_`)。
- **既定 -1 で inert**: preprocess 後ソースが原本と同一になる (`#else` 句を選ぶ) → stock genome は
  cache hit で実証 (B0-L-W0 perf hash 不変)。baseline を汚さない (絶対規律2)。
- **わざと壊したものではない**: backoff は timing のみ変え CC 論理は不変 → serializable。verifier で
  certified を確認済み (`BACKOFF_FIXED=50` で 355,549 commit / 0 anomaly)。pipeline が毎評価ゲートする。
- 使い方: genome に `BACKOFF_FIXED` フラグを足すと `-DCCBENCH_BACKOFF_FIXED=<us>` が渡る。
  driver = `orchestrator/campaign/backoff_sweep.py` (BACK_OFF=1 + 量 sweep を高 abort workload で計測)。

### BACKOFF_NOINLINE — perf 帰属用の診断計器 (P2-4)

backoff ケーススタディ [P0] の機序純度を解くため、backoff() の `_mm_pause`+`rdtscp` busy-wait スピンを
perf record で分離して「有用 IPC」を測る計器。`backoff()` は -O2 で `TxExecutor::abort` に inline され
独立シンボルにならない (perf で spin を関数単位に切り出せない)。`#if BACKOFF_NOINLINE` で
`__attribute__((noinline))` を付け、`Backoff::backoff` を独立シンボル化する。

- **既定 0 で inert**: noinline を付けないので命令列・挙動とも stock 不変。観測者効果も実測で確認
  (BACKOFF_NOINLINE=1 fix10 = 2,623,221 tps vs stock 2,603,521 = +0.76%、between-run floor 3.0% 内)。
  → 機序分析 (spin%/有用 IPC) は noinline build で測り、headline throughput は stock build を引く。
- 使い方: genome に `BACKOFF_NOINLINE` を足すと `-DCCBENCH_BACKOFF_NOINLINE=1`。
  driver = `orchestrator/campaign/backoff_profile.py` (`perf record -e cycles,instructions` →
  `Backoff::backoff` の cycle%/instruction% を分離 → 有用 IPC)。**規律1**: trace と直交 (診断専用)。
  **規律4**: 単一テナント直列・pgrep gate。perf 下 tps は overhead 込みなので headline には使わない。

```sh
SUB=external/ccbench
# izanagi-trace の上に重ねる (Options.cmake / backoff.hh を触る。trace-hook と非衝突)
git -C "$SUB" apply ../../patches/silo-backoff-fixed.patch
# 例: 静的 backoff=50us の variant を build (BACK_OFF=1 必須)
cmake -S "$SUB" -B "$SUB/build-bf50" -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF \
      -DCMAKE_C_COMPILER=gcc-13 -DCMAKE_CXX_COMPILER=g++-13 \
      -DCCBENCH_BACK_OFF=1 -DCCBENCH_BACKOFF_FIXED=50
cmake --build "$SUB/build-bf50" --target ycsb_silo.exe -j
```

価値が確定したら (sweep で stock を上回るなら) izanagi-trace / upstream への昇格は**人間が判断**する
(D18、CLAUDE.md「勝手に上流へ PR を出さない」)。

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
