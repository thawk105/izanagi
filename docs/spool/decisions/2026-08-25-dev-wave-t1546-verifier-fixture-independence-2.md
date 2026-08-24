---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1546-verifier-fixture-independence
seq: 2
---

## {{D:verifier-fixture-independence-scope}}. verifier の実データ地面は「判定が verifier の外で決まる」緑赤の対で作り、その射程を 2 つの定数 verdict 実装の拒否に限定して明記する

**背景 (実測)。** `g5_silo_real_prefix` は実 emitter の bytes だが、期待値
(`serializable` / `certified`) は**検査対象である verifier 自身の出力**であり、
実データ golden regression であって独立証明ではなかった。全 fixture の census を実走した結果、
実 emitter 由来の赤 fixture 0 件、1 thread の実 trace 0 件、1 trace に G2 が複数同時に出る
fixture 0 件 (赤 7 件はすべて anomaly 1 / cycle 1、最大 5 txn) だった。

**決定 (1): 独立性は緑赤の対で作る。** 1 thread の自明直列 trace (`g6_silo_serial_1thread`) と、
read-set 再検証を抜いた broken-Silo の trace (`r8_silo_broken_norw`) を実 emitter の bytes として
置く。前者は「常に non-serializable と答える」実装を、後者は「常に serializable と答える」実装を
殺す。ユーザー裁定 (2026-08-23) が採った (a) と (c) がこれに当たる。

**決定 (2): 射程を誇張しない。** この対が拒否するのは上記 **2 つの定数 verdict 実装だけ**であり、
verifier 全体の独立証明ではない。次の壊れ方は 2 つとも通す — 分類器が常に `G2` を返す、
版比較が epoch を無視する、長さ 4 以上の巡回を無視する、framing violation を常に 0 にする、
fixture の hash で結果を返す。**これを `fixtures/README.md` に限界として書く。**

**決定 (3): 独立に決まる述語と golden を assert の節で分ける。** g6 の独立根拠は
`serializable` というラベルだけで、integrity・統計・bytes は verifier 由来の golden である。
r8 の独立根拠は「G2 が少なくとも 1 本実在する」ことまでで、巡回数・txid・辺の理由は golden である。
テストは独立根拠 / そこから派生する受理結果 / golden の 3 層をコメントで分ける。

**決定 (4): bytes 照合は独立 node へ切り出す。** semantic assert と同じ node に bytes の SHA 照合を
置くと、fixture を変える変異が必ず SHA で先に落ち、semantic assert が死んでいても KILLED になる。
帰属を成立させるため node を分ける。

**決定 (5): 独立性の裏取りに repo 内の第二 checker を作らない。** 固定 bytes に G2 が実在することは
**verifier を使わない 1 回限りの raw 監査**で確かめ、結論を docs の散文として残す。
これはユーザーが見送りを確定させた案 (b)「verifier と実装を共有しない checker を保存する」とは
別物である。監査に使った補助 script は repo 外に置く。

**却下した案:** (a) prefix を大きくして長さ 4 以上の巡回を得る — 実測で `tid <= 1000` まで上げても
witness の長さは 2 か 3 のままだった。原因は規模ではなく `DSG.anomalies()` が各 SCC の**最短**
巡回を報告する実装であり、**規模では買えない**。(b) g5 と同じ prefix 閾値に揃える —
g5 は `tid <= 1000`、新 fixture は `tid <= 200` で、揃えても得られる性質は増えず bytes だけ 4.3 倍になる。
(c) 「g5 / g6 / r8 は 1 因子ずつ違う対照系列」と記述する — g5 と g6 は thread 数と閾値の
2 因子が違うので成立しない。clean ablation として引用してよいのは patch の有無だけを変えた
対照実験である。
