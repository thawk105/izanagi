# patches/ — Izanagi の CCBench 改変 (out-of-tree)

CCBench submodule (`external/ccbench`) は **commit `33d74a3` に固定し、本体は常にクリーンに保つ** (D6)。
Izanagi による改変はすべて**このディレクトリの patch ファイル**として明示的に存在し、必要なときに適用する。
これにより「CCBench 本体はクリーン / 改変は patches/ に追える」状態を保ち、上流還元すべき差分を綺麗に切り出せる。

## 適用 / revert フロー (D6)

```sh
SUB=external/ccbench
# 適用
git -C "$SUB" apply ../../patches/trace-hook.patch      # (cwd=repo root なら patches/trace-hook.patch)
# トレース有効ビルド (perf ビルドとは別ディレクトリ・別 run。絶対規律1)
cmake -S "$SUB" -B "$SUB/build-trace" -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF \
      -DCCBENCH_TRACE=1 -DCMAKE_C_COMPILER=gcc-13 -DCMAKE_CXX_COMPILER=g++-13
cmake --build "$SUB/build-trace" --target ycsb_silo.exe -j
# 実行 (trace を IZANAGI_TRACE_DIR に吐く)
IZANAGI_TRACE_DIR=/path/to/out "$SUB/build-trace/cc/silo/ycsb_silo.exe" \
      -clocks_per_us=<MHz> -thread_num=N -extime=T -ycsb_rmw=true ...
# クリーンに戻す (tracked 2ファイルを checkout、新規 trace.hh を削除)
git -C "$SUB" checkout -- cmake/Options.cmake cc/silo/transaction.cc
rm -f "$SUB/include/trace.hh"
```

orchestrator (Phase 1 タスク6) がこの「apply → build → run → revert」を自動化する。
**現状 active dev 中は submodule を patch 適用状態のまま置くことがある** (build-trace バイナリと source を一致させるため)。
その場合も **parent repo の gitlink は `33d74a3` のまま**で、submodule の working-tree dirt を parent に commit してはいけない。

`git apply --check patches/trace-hook.patch` でクリーン tree への適用可否を検証できる (round-trip 済み)。

---

## trace-hook.patch — Silo に `#if TRACE` の正しさトレースを足す (Phase 1 タスク1)

3ファイル・131挿入:
- `include/trace.hh` (新規) — `#if TRACE` で囲まれた per-thread トレース出力 (`izanagi_trace` namespace)
- `cmake/Options.cmake` — `CCBENCH_TRACE` cache 変数 + 全 protocol への `-DTRACE=<v>` 配線
- `cc/silo/transaction.cc` — `writePhase()` の `maxtid` 確定直後に emit フック

**観測者効果の分離 (絶対規律1) の実装:**
- コードは **`#if TRACE`** (NOT `#ifdef`)。cmake が常に `-DTRACE=0` を定義する規約のため、`#ifdef` だと perf ビルドでも真になり漏れる (→ `docs/decisions.md` D14)。`#if TRACE` なら `-DTRACE=0` (既定) で完全に消える
- 実証済み: `TRACE=0` ビルドのバイナリに `izanagi_trace` シンボル 0 個・`IZANAGI_TRACE_DIR` 文字列 0 個 (`nm`/`strings`)
- トレースは全て **CC-native フィールド** から取得 — tuple に検証専用フィールドを一切足していない (Tidword は元々 ReadElement にある)
- 別ビルド・別 run: perf = `build/` (`-DTRACE=0`)、correctness = `build-trace/` (`-DTRACE=1`)

**トレース取得点 (Silo, `writePhase` 内、`maxtid` 確定後):** commit した trx ごとに、commit順=`maxtid`、`read_set_` の各 read の版=`ReadElement::get_tidword()`、`write_set_` の各 write の key/op を emit。abort した trx は writePhase に到達しないので出力されない (verifier は committed のみ見る)。

### トレース形式 (verifier = タスク2 の入力)

per-thread ファイル `trace_<thid>.log`、1イベント1行。1 trx の records は連続 (C → その R/W 行):

```
C <txid> <thid> <epoch> <tid>             committed txn。<epoch>,<tid> = commit順 = この trx が産んだ版ID
R <txid> <key_hex> <ver_epoch> <ver_tid>  read。見た版 (ver_epoch,ver_tid)
W <txid> <key_hex> <op> <epoch> <tid>     write。op∈{U,I,D}。新版 = この trx の commit (epoch,tid)
```

- `txid` = グローバル単調 id (TRACE ビルド限定の atomic)。1 trx の C/R/W をまとめるためだけ。Silo の (epoch,tid) は非衝突 trx 間で重複しうるので、grouping には別 id が要る
- `key_hex` = キー生バイトの小文字 hex (YCSB は 8byte big-endian)
- **版ID = (epoch,tid)。** 同一キー上では (epoch,tid) が producer trx を一意に決める (同キーを書くと ww 競合で tid が上がるため)。実測で版重複 0 を確認
- **genesis 版 = (epoch=1, tid=0)** (初期 DB ロードの版、producer 無し。`Tuple::init` が epoch=1,tid=0 で初期化)

### verifier が辺を復元する方法 (タスク2 で実装)

- **wr 辺** (T_w → T_r): R の (key, e, t) を、commit (e,t) でその key を書いた W の trx (= producer) に対応付け
- **ww 辺**: 同一 key を書いた trx を (epoch,tid) 順に並べる
- **rw 辺 (anti-dependency)**: R が版 V を読み、別 trx が同 key により新しい版を書いたら T_r → T_w
- **G2**: rw 辺を1本以上含む cycle

### 検証実績 (タスク1)

`ycsb_silo -ycsb_rmw=true -ycsb_zipf_skew=0.9 -ycsb_tuple_num=200 -thread_num=2 -extime=1`:
- trace の C 行合計 = ベンチ報告 `commit_counts_` (327918) **完全一致** (取りこぼし・重複なし)
- 非 genesis read の **100%** が producer の write に matchable、**ORPHAN 0**、版重複 0

---

## broken-silo-norw-validation.patch — verifier の検出力証明 (Phase 1 タスク3, Approach A)

**わざと壊した CC** (positive control)。Silo の `validationPhase()` 条件#1 (read-set の
tidword 再検証 = anti-dependency / stale-read チェック) を **macro `IZANAGI_BREAK_NOREAD_VALIDATION`
で抜く**。stale read が abort されず commit するので、lost-update / write-skew の **G2 cycle が
trace に出現**し、verifier がそれを赤と判定できることを実証する。

- **既定 OFF**: macro 未定義時は `#else` で元の abort が compile-in されるので**挙動は完全に元の Silo**
  (inert)。**正しさ/性能の baseline には絶対に混ぜない** (絶対規律2)。
- **trace-hook patch の上に重ねて適用する** (validationPhase を触る。writePhase の trace-hook と非衝突)。

```sh
SUB=external/ccbench
git -C "$SUB" apply ../../patches/trace-hook.patch                  # まだなら
git -C "$SUB" apply ../../patches/broken-silo-norw-validation.patch # 壊しを重ねる
# 壊し+trace 専用ビルド (TRACE=1 かつ break flag。別 build dir)
cmake -S "$SUB" -B "$SUB/build-trace-broken" -DCMAKE_BUILD_TYPE=Release \
      -DENABLE_SANITIZER=OFF -DCCBENCH_TRACE=1 \
      -DCMAKE_C_COMPILER=gcc-13 -DCMAKE_CXX_COMPILER=g++-13 \
      -DCMAKE_CXX_FLAGS="-DIZANAGI_BREAK_NOREAD_VALIDATION=1"
cmake --build "$SUB/build-trace-broken" --target ycsb_silo.exe -j
# 高 contention で走らせ verifier にかける → NON-SERIALIZABLE (exit 1) になるはず
git -C "$SUB" checkout -- cc/silo/transaction.cc   # 壊しだけ revert (trace-hook は別途)
```

### 実証 (2026-06-18, clean ablation)

同一ワークロード `-ycsb_rmw=true -ycsb_zipf_skew=0.9 -ycsb_tuple_num=50 -ycsb_max_ope=5 -thread_num=4 -extime=1`:
- **壊し ON**: 293,803 commit → trace に **1310 G2 cycle** → verifier **NON-SERIALIZABLE (exit 1)**
- **壊し OFF (素の Silo)**: 285,047 commit → verifier **certified SERIALIZABLE (exit 0)**
- 差は read validation の有無のみ → verifier は壊れた CC を赤・正しい CC を緑と判定する番人だと確認。

---

## trace-hook-si.patch — `si` (Snapshot Isolation) の trace-hook (Phase 1 タスク3, Approach B)

**本物の positive control。** 無改変の `si` は SSN を持たず write-skew (G2) を admit する。si エンジン
(`cc/si/transaction.cc::si_commit()`) に trace 出力を足し、**実 CC が出す本物の異常**を verifier が捕まえ
られることを示す。trace.hh / Options.cmake の TRACE 配線は全 protocol 共通なので**再利用**(この patch は
`cc/si/transaction.cc` への include + emit のみ。trace-hook.patch の上に重ねる)。

- **版ID写像:** si の版ID = `Version::cstamp_` (commit LSN、単調 uint)。これを `(epoch=1, tid=cstamp)` と
  emit。**初期ロード版は cstamp=0** (`tuple.hh`)、実 txn は `++Lsn≥1` なので、初期版 read が `(1,0)`=genesis
  番兵に**自然に一致**し verifier の既存モデル (FIX2 の producer-absence 含む) がそのまま効く。
- **emit 点:** `si_commit` の write install ループ直後 (cstamp 確定・版 commit 済み・read_set_/write_set_ 健在)。
  node-validation abort は `FINISH_SI_COMMIT` へ飛び到達しないので committed のみ emit。

```sh
SUB=external/ccbench
git -C "$SUB" apply ../../patches/trace-hook.patch     # trace.hh + Options.cmake (まだなら)
git -C "$SUB" apply ../../patches/trace-hook-si.patch  # si emit
cmake --build "$SUB/build-trace" --target ycsb_si.exe -j   # build-trace は CCBENCH_TRACE=1
IZANAGI_TRACE_DIR=out "$SUB/build-trace/cc/si/ycsb_si.exe" \
   -ycsb_rmw=false -ycsb_rratio=50 -ycsb_zipf_skew=0.9 -ycsb_tuple_num=30 \
   -ycsb_max_ope=10 -thread_num=8 -extime=1 -clocks_per_us=2100
python3 ../../orchestrator/verify.py out    # NON-SERIALIZABLE (G2) になるはず
```

### 実証 (2026-06-18) — real-CC discrimination

同一 workload `-ycsb_rmw=false -ycsb_rratio=50 -ycsb_zipf_skew=0.9 -ycsb_tuple_num=30 -ycsb_max_ope=10 -thread_num=8 -extime=1`:
- **`si` (Snapshot Isolation)**: 171,037 commit → **3576 G2 cycle** → **NON-SERIALIZABLE**、integrity clean
- **`silo` (serializable OCC)**: 208,904 commit → **certified SERIALIZABLE**
- 差は分離レベルのみ → verifier は workload でなく**正しさそのもの**を見ている。

### 将来: `ermia` cross-check の罠

`ermia` (SSN on=serializable) を green の cross-check oracle にするには `cc/ermia/transaction.cc` にも
同様の hook を足すが、**版 cstamp が `cstamp<<1` (低ビット=SSN flag, `ssn_commit:561`)** で si と違う。
また commit 経路が `ssn_commit` / `ssn_parallel_commit` の2系統。version id 写像をこの shift に合わせないと
全 read が orphan 化する。次の増分で対応。
