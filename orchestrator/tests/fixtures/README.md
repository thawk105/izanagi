# verifier 単体テスト用フィクスチャ

各ディレクトリ = 1 run (`trace_<thid>.log`)。形式は
`patches/README.md` / `include/trace.hh` と同一。**判定が既知**なので verifier
の緑/赤を固定する。**大半は手製の極小トレースだが、`g5_silo_real_prefix` だけは
実 emitter が吐いた bytes である** (下の「実データ fixture」節)。キー: x=`…0001`, y=`…0002`, z=`…0003`。版 `1 0` = genesis。
(x/y/z は正準フィクスチャの慣習。`r4_mixed_cycle`・`r5_nonlatest_transitive`・`p1_phantom_skew`
は各自の固有キーを使う — trace 本体が真実源。)

判定は2軸: `serializable` (DSG 非巡回というグラフ事実) と `verdict`/`certified`
(integrity 不良なら認証できず **indeterminate**)。詳細は `model.py` VerifyResult。

| fixture | verdict | 内容 |
|---|---|---|
| `g1_serial` | serializable | T0 が x を書き T1 がその版を読む (wr 辺のみ、DAG) |
| `g2_rmw_chain` | serializable | x 上の逐次 RMW 連鎖 (wr+ww、自己ループは辺にしない) |
| `g3_readonly` | serializable | 2 スレッド・読み取り専用 trx を含む (複数ファイル grouping のテスト) |
| `g4_rw_no_cycle` | serializable | rw 辺が 1 本あるが cycle 無し (「rw=即異常」の誤検出ガード) |
| `g5_silo_real_prefix` | serializable (certified) | **実 emitter 由来**。実 Silo 実行の commit-stamp prefix。1,345 txn / 8,466 辺 |
| `r1_write_skew` | **non-serializable / G2** | 古典的 write-skew。2 本の rw で 2-cycle |
| `r2_lost_update` | **non-serializable / G2** | lost update。rw + ww の 2-cycle (2 スレッド) |
| `r3_cycle3` | **non-serializable / G2** | 3 trx の rw cycle (x→y→z→x) |
| `r4_mixed_cycle` | **non-serializable / G2** | 1 cycle に ww+wr+rw が全部乗る (定理の実例) |
| `r5_nonlatest_transitive` | **non-serializable / G2** | 古い版を読む trx の anti-dep が ww 推移で遠い overwriter まで届く |
| `r6_epoch_version_order` | **non-serializable / G2** | epoch 境界を跨ぐ版順序。版を `tid` だけで並べると cycle が消える (positive control) |
| `r7_epoch_rw_successor` | **non-serializable / G2** | 読んだ版の**直後版が次 epoch**。rw 側の epoch 順序を固定する (r6 の ww 側と対) |
| `integrity_orphan` | **indeterminate** | 非 genesis なのに producer 不在の read (orphan)。cycle は無いが認証不能 |
| `m1_commit_at_genesis` | **indeterminate** | trx が番兵 (1,0) で commit (非物理)。wr 辺は落とさず弾く (FIX2 回帰) |
| `m2_version_dup` | **indeterminate** | 同一 (key,版) を 2 trx が産む malformed (FIX1 回帰) |
| `p1_phantom_skew` | serializable (限界) | 述語 phantom skew。key 粒度では見えない**スコープ限界** (insights 参照) |

`m*` (malformed) と `integrity_orphan` は **絶対規律2 の硬化**の回帰: integrity 不良の
trace で `serializable` を主張せず `indeterminate` を返す (辺が落ちて real cycle を
隠す false-green を防ぐ)。`p1_phantom_skew` は trace 形式の限界を固定する (バグではない)。

## なぜ赤フィクスチャが全部 G2 か (構造的事実)

このトレースは **版ID = commit (epoch,tid) の単一スタンプ**で、**committed trx
だけ**を記録する。すると:
- **ww 辺**: 版順 = commit 順なので必ず commit 順方向 (a.commit < b.commit)。
- **wr 辺**: b は a が commit 済みの版を読むので必ず a.commit < b.commit。
- **rw 辺 (anti-dependency)** だけが commit 順を**逆走**できる (古い版を読んだまま
  後から commit する = まさに異常)。

ゆえに **realizable な (物理的に起こりうる) トレースでは、DSG 上のあらゆる cycle は
必ず rw を 1 本以上含む = 常に G2**。**G0 (ww のみ) / G1c (wr のみ) の cycle は
realizable トレースでは出現しない** (それらは dirty read や複数版の独立タイムスタンプ
が要る)。これは roadmap §3.1「Serializable 狙いなら G2 まで見る」/ タスク0「`si`=
write-skew G2」と一致する。

注: コードは realizability を強制しないので、**非 realizable な手製/破損トレース**
(例: 複数 trx が版スタンプを共有) は G0/G1c に分類される cycle を作れる。ただし
verdict は cycle の有無だけで決まり分類に依存しないので無害。分類器の G0/G1c 枝は
防御的に残し、合成 `CycleEdge` で直接テストする
(`test_verifier.py::test_classify_branches`)。定義の全体像は `docs/isolation-phenomena.md`。

## 実データ fixture — `g5_silo_real_prefix`

**何であるか。** 実 CCBench Silo を trace-enabled build で走らせたときに **emitter が実際に
吐いた bytes** を、commit stamp の閾値で切り出したものである。手で作ったものではなく、
1 byte も改変していない。

**何を固定するか (純増検出力)。** 既存の手製 fixture が持たない性質は次の 3 点だけである。

1. **実 emitter の bytes そのもの。** trace v2 の framing (C 行は tag を含めて 7 field、
   16 進 key、`U` op、per-thread file の interleave) が実装からずれたら落ちる。
   手製 fixture は人が書いた形式なので、実装が動いてもズレを検出できない。
2. **rw 辺を大量に含みながら非巡回。** 手製側の rw 辺は `g4_rw_no_cycle` の 1 本だけである。
3. **規模。** 1,345 txn / 8,466 辺 / 199 key。手製側は 1 桁 txn。

**判定既知の意味 — ここは正確に読むこと。** この fixture の期待値
(`serializable` / `certified`) は、**検査対象である verifier 自身の出力**である。
手製 fixture が「人が判定を設計した」のと同じ意味では既知ではない。
したがってこれは **stock Silo の実行を根拠にした実データ golden regression** であって、
**verifier の正しさを独立に証明するものではない**。独立性の根拠は verifier の外側にある —
stock Silo は write-set を施錠し read-set を再検証してから commit する
(CCBench submodule の `cc/silo/transaction.cc`) ので、その実行が serializable であることは
protocol 側の予測であり、verifier がそれを追認している、という二重性だけが担保である。

**期待値 (親が実測。テストが exact に固定している値)。**

- 統計: `txns=1345 / reads=6311 / writes=3244 / keys=199 / edges=8466`
- 判定: `serializable` / `certified` / `integrity.clean()` / `orphan_reads=0` / anomaly 0
- 辺の型組合せ別の `(src,dst)` 組数:
  `wr` のみ 2,677 / `rw` のみ 2,724 / `wr`+`ww` 2,934 / `rw`+`wr`+`ww` 62 / `rw`+`wr` 69
  (延べでは wr 5,742 / rw 2,855 / ww 2,996)。
  **`adj` は型別 multiset ではなく `(src,dst)` の set である** — ww の 2,996 組はすべて wr と
  同じ組に重なる。型組合せ別の pin は rw 側の脱落 (rw のみの 2,724 組が消える) を撃つが、
  **ww 生成器の脱落は撃たない**。`DSG._reasons()` は版列と write-set から型を再計算するので、
  `_add_ww_edges()` が辺を追加したかどうかとは独立だからである。
  この fixture では ww 生成器を止めても観測可能な出力が一切変わらない (等価変異)。
  ww 生成器の gate は手製 fixture 側 (`r2_lost_update` ほか) が担う。
- bytes: `trace_0.log` 43,140 / `trace_1.log` 110,139 / `trace_2.log` 111,402 /
  `trace_3.log` 51,209、合計 315,890。SHA-256 は `test_verifier.py` が exact に固定する。
  repo root の `.gitattributes` が `-text` で checkout 時の改行変換を止めている。

**由来 (provenance)。**

- producer: `ycsb_silo.exe` を `-DCCBENCH_TRACE=1` で build して 1 秒実行したもの。
- producer の clone HEAD: `511c9538e4e8efa54b45cda62e72389ed3b706ec` (`izanagi-trace` ブランチ)。
  依存は gflags / glog を static install。
- 完全 argv: `-ycsb_tuple_num=200 -ycsb_zipf_skew=0.9 -ycsb_rratio=50 -ycsb_rmw=true
  -ycsb_max_ope=5 -thread_num=4 -extime=1`
- 実行側の独立 witness: `commit_counts_ = 244971` (trace 外の counter)。
- source の 4 file とその SHA-256:

```
ed5da50e2da1a8ad6afbbf981ca42fc3a07aca68c66d2464123308224e047417  trace_0.log
d65e077e0a1f3c8df6b1542d971a505af595b26b32d04b0e8476b8fc33edc8bf  trace_1.log
46d6c55a76939f9bc7e7f680f8179e61174a70a46fa5f8977171284dff718bc7  trace_2.log
a3a1fd75f0a22a95c323ecdac4e3a30a56fc1147df2b7690d2282cd888bf7956  trace_3.log
```

**再生成 (抽出) 手順。** source の各 file に対して、次を実行したものがこの fixture である。

```sh
awk '$1=="C"{keep=($4==1 && $5<=1000); buf=""} keep{buf=buf $0 "\n"} \
     $1=="E" && keep{printf "%s", buf; keep=0}' SRC/trace_N.log > g5_silo_real_prefix/trace_N.log
```

述語は「`C` 行の commit stamp が `epoch == 1` かつ `tid <= 1000`」で、`C` から対応する `E` までの
raw block を元 file・元順序のまま残す。**保証する範囲を混同しないこと。**

- 「同じ source trace から同じ prefix を導出できる」— **保証する** (上の command は決定論的)。
- 「producer を再実行して同じ bytes を再現できる」— **保証しない**。4 thread の並行実行に依存する。

**なぜこの閾値なのか。** commit stamp の閾値でのフィルタが producer を切り落とさないのは、
Silo の TID が自分の読んだ・書いた全 record の TID より大きく採られるため、read が見た版の
stamp が必ず読み手の stamp より小さいからである (validation phase)。
実測でも `orphan_reads=0` かつ `missing_txids=0` (= 密な txid prefix) である。
`missing_txids != 0` は `integrity.clean()` を偽にするので、疎な部分集合は使えない。

**この fixture が押さえない範囲。** epoch 1 だけなので epoch 境界を跨ぐ依存を含まない
(そこは `r6_epoch_version_order` と `r7_epoch_rw_successor` が担う — 前者は ww 側、後者は
rw の直後版側の epoch 順序を固定する)。また 244,971 txn の元 trace が持つ規模
(長い版連鎖、大きい txid 空間、約 966MB の peak state) は縮小で失われるので、
**中規模までの保証**として読むこと。大規模側は任意入力 `output/runs/silo-sample` が
置かれた機体でだけ追加検証される。
