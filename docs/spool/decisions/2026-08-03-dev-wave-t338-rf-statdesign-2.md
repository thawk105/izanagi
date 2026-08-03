---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-03
wave: dev-wave-t338-rf-statdesign
seq: 2
---

## {{D:rf-statdesign-package}}. RF 統計設計は floor 単独では裁定できない — 推定量と最小識別幅を前提として足し、5 点を 11 件の裁定項目へ組み替えて返す

**背景:** ユーザー裁定は「RF 統計設計のうち **paired session 差による floor の取り方**を正例より
先に裁定する。残る統計設計 4 点も同じパッケージで提示する」だった。本 wave はそのパッケージを
起草し、段 3 で 2 本の敵対レンズ (統計的妥当性 / 整合と実効性) を並列に当てた。
両レンズが独立に NO-GO を返した。一次資料 =
`output/insights/2026-08-03_t338-rf-statistical-design/` (成果物本体は `package.md`)。

**決定 (1): floor 単独の先行裁定は実行できない。推定量と最小識別幅を前提として足す。**
`RF = E[N]/E[D]` (劣化幅で加重した総回復率) と `RF = E[N/D]` (session 等重みの典型回復率) は
別の母数であり、両者は session ごとの比と劣化幅が相関すると一致しない。また分母の識別を
`E[D] > 0` で見るか `E[D] > δ_D` で見るかで判定式そのものが変わる。**floor が守る線の意味は
これらが決まってはじめて定まる**ため、floor を先に決めることは形式的にしかできない。
これは元の裁定の否定ではなく、実行に必要な前提の追加である。**親の見落としである。**

**決定 (2): 本 wave では実装しない。** 実装差分はゼロであり、変異 matrix と受入全走は射程外である。
コード・テスト・gate・artifact・凍結 bytes・certified 選択・材料レポート・proof chain は
いずれも不変である。両レンズとも docs-only で終える scope 自体は正しいと判定した。

**決定 (3): paired を採るなら D19 と roadmap §3.6(3') の例外新設として扱い、限定を同じ変更単位で行う。**
roadmap §3.6(3') は「variant と baseline は決して同一セッションで測らない」ことを between-run floor の
根拠として書いており、RF の 3 arm を同一 block で測る設計ではこの前提が成り立たない。
D104 の paired 比較は受入全走施策の一次証拠に関する記述であり、**supersede の根拠にはならない**。
したがって採用時は roadmap の改訂と D19 の適用前提の限定を裁定と原子的に結び付ける
(roadmap は戦略層のため協議改訂の手続きに従う)。

**決定 (4): 自動 unpaired fallback を採らない。`pairing 不成立 ⇒ 判定不能` を fail-closed とする。**
同一 session の arm は相関しており、負の covariance では独立標本用の `√(s_a²+s_b²)` が
真の差分散を**過小評価する**。同じデータに 2 つの分析経路を用意すること自体が、
経路選択で受理を反転させられる穴である。段 2 と両レンズが独立に拒否した。

**決定 (5): 状態を producer の自己申告 field にしない。** `pairing_valid` や受理状態を
producer が宣言する形は、caller の自己申告が検出器でも意味 gate でもないと既に裁定した D127 と
同型の恒真 gate になる。allocation 受領証・raw run・schedule・測定 checkout・理由コードから
**独立 validator が再計算し、宣言値との不一致を拒否する**形を後続 scope の要件とする。
あわせて、層 3 の calibration floor の閉表を広げる形は採らない — 層 3 の floor 検索は
`(records, threads, workload)` だけで照合するため、候補や contrast ごとの trial 固有統計を
同じ表へ入れると識別できない。

**決定 (6): correctness failure を欠測処理に流さない。** arm 固有の verifier anomaly を
session 削除で消せる規則は、正しさゲートを緩める経路そのものである (規律 2)。
correctness anomaly は候補の**終端 reject** とし、結果を見る前に外部証拠で確定する
infra failure だけを予備 session で置換可能にする。走り始めた後の性能側の欠測は
既定で reject または判定不能とする。

**親の誤りの訂正 (本 D で確定):** 本 wave 中に親が書き、段 3 が実データで反証したものが 6 件ある。
(a)「paired にすれば floor は小さくできる」— `Var(A−B)=Var(A)+Var(B)−2Cov(A,B)` であり、
既存 calibration JSON は covariance を 1 つも持たないので符号が未知。
(b)「abort 率が高いほど run 間ドリフトが大きい」— 実測は逆を含む
(abort 81.95% で CV 0.666%、70.47% で 1.067%)。3 workload 各 1 系列では単調性も因果も識別できない。
(c)「fresh 下限と別時間窓の値の最大を取る」を RF へ移す案 — 独立成分なら合計は
`√(σ₁²+σ₂²)` で max より大きく、同じ量の推定 2 つの max にも所定の被覆はない。
**既存の between-run floor 値がこの経験則の産物であるという事実認定は維持する。**
(d)「paired 前提が崩れたら unpaired へ戻す」— 決定 (4) で撤回。
(e)「D104 が paired を承認済みの型として挙げている」— 射程を縮約。
(f)「別 allocation でなければ within-run 誤用の再演」— allocation ID は独立性の必要十分条件では
ない。独立単位は対象母集団と相関構造から定義し、node / 時間窓を cluster として数える。
**現存する 3 arm データが 1 allocation しかないという事実認定は維持する。**

**却下した選択肢:**
- **5 点のまま推奨を書いて返す** — 推定量と `δ_D` が未定のまま floor を決めると、
  同じ raw 値から正例の成立/不成立が反転する余地を残したまま「裁定済み」になる。
- **親が推定量を独断で固定して floor 裁定を通す** — 推定量の択一は目的
  (総回復率か典型 session の回復率か) から決まるものであり、受理集合を変える設計択一を
  親が独断で採らない。
- **標本数を固定値で先に決める** — 検出したい効果量と目標検出力から導かれておらず、
  中程度の効果を拾うなら 40〜50 cluster 規模が要る一方、大きい効果に限れば 10 台で足りる。
  これは計算資源の費用そのものなので、親が決めずユーザー裁定へ返す。
- **既存 between-run floor をそのまま RF へ流用する** — 別セッションで測る設計を前提にした
  周辺 CV であり、同一 block で 3 arm を測る誤差構造とは別物である。

**研究状態への影響:** certified 選択、材料レポート、proof chain、凍結 bytes、既存 gate、
受理集合はいずれも不変である。変わるのは、RF 統計設計の状態が「floor の先行裁定待ち」から
**「11 件のユーザー裁定待ち」**へ分解されたことと、正例 artifact の再走設計・適格性権威・
consumer 起票がいずれもこの裁定に従属すると確定したことである。
