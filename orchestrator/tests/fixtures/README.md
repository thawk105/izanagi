# verifier 単体テスト用フィクスチャ

手製の極小トレース。各ディレクトリ = 1 run (`trace_<thid>.log`)。形式は
`patches/README.md` / `include/trace.hh` と同一。**判定が既知**なので verifier
の緑/赤を固定する。キー: x=`…0001`, y=`…0002`, z=`…0003`。版 `1 0` = genesis。
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
| `r1_write_skew` | **non-serializable / G2** | 古典的 write-skew。2 本の rw で 2-cycle |
| `r2_lost_update` | **non-serializable / G2** | lost update。rw + ww の 2-cycle (2 スレッド) |
| `r3_cycle3` | **non-serializable / G2** | 3 trx の rw cycle (x→y→z→x) |
| `r4_mixed_cycle` | **non-serializable / G2** | 1 cycle に ww+wr+rw が全部乗る (定理の実例) |
| `r5_nonlatest_transitive` | **non-serializable / G2** | 古い版を読む trx の anti-dep が ww 推移で遠い overwriter まで届く |
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
