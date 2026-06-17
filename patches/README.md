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
