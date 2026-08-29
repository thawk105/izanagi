# [T-1905] B-10 待ち方 grid の事前登録を v4 へ再設計した

## 結論

物理残差 probe の 18 cell を全件開示したうえで、**上限 1.0% exclusive を緩めずに満たす 2 形 grid**
へ改訂し、既存 probe の該当 12 値を転記して**発効版**にした。probe の再走を要さない。
実測 (build / verify / perf) の投入は本 wave では行っていない。

登録 grid は `{constant, symmetric-modulo}` × μ 6 点 × workload 3。
登録 12 cell の最大絶対偏差は `constant` / μ = 2 の 0.5616942857142844% で、上限 1.0% を満たす。

## binary を外した根拠 (式の側)

指示待ち量 `X` の期待値の μ からのずれを、撹拌語の最上位 bit `H` (`p = P(H = 1)`) と
補助 draw `r` の条件付き期待値で記号展開する。仮定は `E[r | H = 0] = E[r | H = 1] = m` である。

| 形 | `E[X] − μ` | `(p − 1/2)` の係数 |
|---|---|---|
| `constant` | `0` | なし |
| `symmetric-modulo` | `(p − 1/2)(μ − m)` | `(μ − m)` へ抑制される |
| `binary` | `μ(p − 1/2)` | `μ` そのもの。抑制されない |

**登録するのは `(p − 1/2)` の係数が μ そのものにならない形だけ**とした (事前登録 §2 の R1)。
判定は式からのみ行い、probe の実測値も `p` の推定値も参照しない。

## この wave が主張しないこと

- **`p ≠ 1/2` であるとは主張しない。** probe は待機ループの経過サイクルだけを保存しており、
  最上位 bit の出現数を記録していない。`p` は測っていない。
  主張するのは (a) binary の平均が `(p − 1/2)` に無防備であること (式) と
  (b) binary の実現平均が 4 cell で上限を超えたこと (実測) の 2 点だけである。
  (b) の原因が (a) であるとは認証しない。
- **binary を外した判断そのものは事前登録ではない。** probe を見た後の改訂 (probe-informed amendment)
  である。前向きに固定したと言えるのは、shape grid の throughput を一度も観測していない時点で
  R1〜R5 と v4 spec を固定したことだけである。
- **「呼び出し回数を増やせば直る」の決定的証拠は持たない。** 公平 bit 仮定なら 100,000 回での
  相対標準誤差は 0.158114% で、観測した 4.350306666666667% はその約 27.5 倍にあたるが、
  実測値には固定オーバーヘッド・実行時雑音・bit の非独立性が混ざっており、
  Bernoulli の標準誤差だけで標準化した検定統計量ではない。理想化した健全性検査に留める。
- **待ち方と待ち量の直交切り分けを一般には閉じない。** 閉じるのは
  `constant` 対 `symmetric-modulo` の 1 contrast の範囲だけである。
- **A-2 の逆転や過抑制域の機序を説明しない。** それらは B-10 の別項目である。

## 開示した材料

物理残差 probe 18 cell (`output/insights/2026-08-28_t1905-b10-backoff-shape-run/probe-result.json`、
SHA-256 `6e7d8ed7d27be091ce94de4b85ac61a50e99d97167e75c4328e8a54982224bc3`) の全値は
事前登録 §4.1 にある。上限を超えたのは `binary` の μ = 2 / 5 / 10 / 50 の 4 cell で、
最大は μ = 2 の 4.350306666666667% である。

A-2 実走 (`output/insights/2026-08-28_t2022-a2-certification-run/`) の
rr5 −46.3902%、rr50 −65.9080%、outer `reject` も §4.3 で開示した。役割は
`motivation-and-prior-evidence-not-parameter-selection` として spec に固定し、
μ grid・閾値・判定手続きを動かす根拠にしていない。

## 機械的に固定したもの

事前登録 §5 の `registration_rules` (8 field) と `physical_residual.provenance` (13 field) は、
driver が**辞書全体の exact 比較**で検査する。key の存在だけを見る実装ではない。
`maximum_absolute_deviation_pct_exclusive` は exact 1.0 だけを受理し、
runtime の判定は `>=` (exclusive) を維持してちょうど 1.0% の cell を拒否する。

## 実装で塞いだ受理集合の穴

段 6 の敵対レビューが 3 件の must-fix を出し、すべて閉じた。

1. provenance が key 集合しか閉じておらず、`probe_clocks_per_us = 2101` のような偽の identity を
   持つ v4 文書が受理できた。全 13 field の exact 比較へ直した。
2. prior block record が自称する `shape` / `mean_us` / `encoded` / `genome` を point の正規 metadata と
   照合しておらず、`shape=binary, encoded=2002` の古い record が resume 経路から report へ
   再流入できた。完全一致を要求する検査を足した。
3. 変異 M7 (residual 件数 guard の除去) が、先頭行削除という変異入力では直後の順序検査に
   mask されて殺せていなかった。末尾へ有効な 13 行目を追加する形へ照準し直した。

`exact_model()` を一度も呼ばずに検査していた恒真な test 1 件も、実体を呼ぶ形へ直した。

## 親の誤りと訂正

親が書いた v4 初版は `external_floor_reference_widths` を v3 の object 形式から flat list へ
作り替え、登録済みの `terminology` と `reference_width_pct` (write-heavy 1.9、balanced 3.0、
read-heavy 0.62) を落としていた。自分の裁定 R2 / R5 (形の削減に伴う派生量以外は変えない) への
違反である。新旧 spec の構造比較で検出し、v3 と同一へ戻して commit した。
段 5 実装子はこの誤った文書に忠実に追随していたため、fix 子でコード側も戻した。

## 検査

- 焦点走: 518 passed / 3 skipped、child rc=0。対象は
  `test_b10_backoff_shape_sweep`、`test_condition_meaning_gate`、`test_ccbench_spawn_sites`、
  `test_official_perf_closure`、`test_p3_build_authority_cli`、`test_campaign`。
- 変異 matrix: baseline PASSED、M1〜M12 の 12/12 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0、
  期待 node 完全一致。spec SHA-256 `7a54906d54cee80e2bc20e6c04c88655167e916c5cdbcfca9429a115a2e6262f`。
  期待 node は推測せず、全件 SURVIVED 期待の probe 走 (`mutation-probe-report.json`) で
  観測した完全集合を焼き込んだ。
- M11 は過剰拒否を検出する正例で、正当な v4 文書を拒否する変異を実文書の parse で殺す。

## 未取得のまま残るもの

shape grid の throughput、正しさ certification、待ち方の効果、過抑制域の機序、ピーク位置の再現、
balanced profile、本走中の要求待ち量分布、`binary` を含む 3 水準 ladder とばらつきの用量反応、
乱数計算と撹拌器のオーバーヘッドの分離、結果を見ていない設計による独立追試。

後継設計として、二値を折り返し構造へ変えて `(p − 1/2)` 依存を積へ落とす案を事前登録 §9 に
記録した。formula と patch の SHA が変わるので、D1098 / D1281 に従って旧 formula の消費者を
別名で凍結し、新しい placeholder を凍結してから probe を走らせ直す別 wave になる。本 wave では実装していない。
