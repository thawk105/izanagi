# [T-139] `a12` 事前 simulation — 実装と完走の材料

wave `dev-wave-t139-a12-stress-check` / 2026-08-12。
第 3 束裁定 (authority: user) R1 (a) 「`a12` を独立 wave で先行」の成果。

## 結論

**`verdict = pass`。** 全 60 セル (J=4..13 × W1/W2 × N/H/G)、B=1,000,000。
Clopper-Pearson 上界の最大は `J=12 W2:G` の `U = 0.003900439` で、名目 `α₁ = 0.025` の **15.6%**。

`pass` が意味するのは次だけである。

- 固定 input・seed・B・J・60 セルで a12 simulation が完走した。
- 全 60 セルで Clopper-Pearson 上界が `α₁ = 0.025` 以下だった。
  同時非被覆確率は最大 `δ_MC = 0.001`。
- **事前固定した empirical residual stress model のもとで**、各 weak-null face の
  marginal false-pass 上界が基準を満たした。

**主張しないこと。** core §7 の weak-null 較正が完了したとは主張しない
(追補 A `a12` の逐語が「本 field が core §7 の義務を満たしたと扱ってはならない」と定め、
第 2 erratum は未承認である)。真の cluster 間変動を含む型 I 誤りを較正・保証したとも主張しない
(cluster 間変動は依然として 1 点も観測されていない)。pilot が投入可能になったとも主張しない。

## pilot 前提への効果

`dev-wave-t139-pilot-precheck.md` の前提表で **#3 が未充足から充足へ動いた**。
充足済みは #2 (α 予約) と #3 の 2 件。**残る 7 件 (#1・#4〜#9) は未充足のままであり、
pilot は依然として投入できない。**

## 正本の走行

```text
transcript  output/env/pegasus/t139-a12-stress-check/full-v1/stress-check-simulation.json
job         907407.nqsv (gen_S)、計算ノード bnode013
runtime     48 worker / 5.32 秒、Python 3.10.12 / numpy 2.2.6
経路        qsub_compute
入力        output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/throughput.tsv
            sha256 = 755cfa7ea7c22ac763f404769103fd2ff0c49763c79369ac826db6a32b71c4f2
seed        01dad84c523b0a476655b91979c91d7174e40bb5a27757ada312abf2fe158ed2
```

セル別の結果は `cells-table.md`。

## 独立実装との一致 (4 段)

親が repo 外に**別ソースで**書いた oracle と照合した。

1. `q(J, α₁)` の 10 値が厳密一致 (追補 A 段 3 レンズ A の記載 `q(4)≈10.99955` /
   `q(13)≈3.449997` とも一致)。
2. `U(x=0, B=1e6) = 1.1002039318325741e-05` が段 3 敵対レンズの独立算出値と一致。
3. PRNG stream が 4 セルの先頭 5,000 抽選で完全一致。分割取得 (chunk 境界の持ち越し) でも同一。
4. **正本の本走と親 oracle の false-pass 件数 `x` が全 60 セルで一致。**

## 仕様の自由度と、その感度

`a12` は実装を一意に決めない箇所を持つ。段 4 で凍結した内容と、結論への感度は次のとおり。

| 自由度 | 凍結した内容 | 感度 (実測) |
|---|---|---|
| 棄却規則 | byte 255 のみ棄却 | `>= 250` 棄却でも `pass`。最悪 U は 0.003825 対 0.003885、セル率の差は最大 0.000159 |
| support の範囲 | workload ごとの 5 点 (pool しない) | pool しても `pass`。最大 false-pass 率 0.00377 対 0.00432、いずれも α₁ の 6 分の 1 以下 |
| counter | 0 始まり、exact 8 raw bytes の big endian | — |
| 抽選順 | dataset → cluster → block position | — |
| chunk 境界 | 未消費 raw byte を持ち越す | — |
| arm 記号 | `D_g ≡ D = mode1` | — |

**2 つの自由度はいずれも判定を変えない。** これは「後から別の grammar を選べば別の結果が出る」
という段 3 レンズ B の懸念への定量的な答えである。ただし `x` の値そのものは変わるので、
grammar は transcript に逐語で記録してある。

## ゼロ分散は実際に起きる

1 cluster は 5 点 support から 6 回復元抽出した平均であり、J cluster が全部同値になると
標本分散が 0 になる。親の検算 (全 210 通りの count vector を列挙):

```text
P(J=4 で全 cluster 同値)          = 2.031409e-06
うち共通平均が正 (W1:N の場合)    = 9.056693e-07
B=1e6 での期待件数                = 0.89 〜 1.14 (セルによる)
J=13 では 1e-21 台で事実上起きない
```

段 4 で「PD filter を掛けず、`s=0` かつ `mean>0` は false-pass として数える」と固定した
(保守側)。段 3 レンズ A の算出値を桁まで再現している。

## 変異 (段 6、親が実測)

**12 件すべて KILLED、生存ゼロ。** 内訳は worklog と `mutation-run1/2/3.log`。

特筆すべきは、段 6 の敵対レビューが **fix 前の時点で V8 (dataset 再中心化) と V10 (棄却規則) の
生存を静的に見抜いた**ことである。テストが helper を直接呼んでおり、production 呼び出し側に
同じ変異を置くと迂回される構造だった。レビューが提示した golden hash は、親が独立実装で
再現してから採用した (実装の現在値を焼き込む循環を避けた)。

```text
_IndexStream(4,"W1","N").take(512) の accepted index 列 SHA-256
  正しい値 (棄却 = byte 255 のみ) e53e3e0a46bc9875dec544a6c9dca7573c433055f9d365ea747e7eda268dcd55
  棄却 >= 250 の変異での値        da61a121b21906a146adc9815aa3619db8d742963c3827f8f1a7d71e0821a7f3
  2 つの stream は 2 番目の抽選で既に食い違う
```

## 実行経路について

段 4 は「queue が `DIS`/`INA` なら login ノードで上限付き実行」を fallback として書いたが、
**この fallback は成立しなかった。** `hooks/guard_bash.py` が未登録 Pegasus 実行体を拒否するため、
`tools/pegasus/run_t139_a12_stress_check.py` は login で走らせられない。
本走の経路は `qsub` の 1 本だけである。admission registry への登録は本 wave の scope 外とした。

## scope 外 (裁定パッケージ候補)

- `a12` の PRNG byte grammar と golden vector を事前登録 core または追補へ昇格するか。
- `D_g ≡ D` の束縛を追補の逐語として明文化するか。
- 第 4 束の凍結チェーン検証保留と「科学的入力 digest」の境界を decisions へ明文化するか。
- `run_t139_a12_stress_check.py` を admission registry へ登録するか。
- codex の evidence gate が NFC 逸脱で健全な成果物を全損させる設計を救済するか。
