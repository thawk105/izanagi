判定は **GO** です。第2巡の R1〜R4 と残 nit 2件はすべて **closed**。新規 blocker はありません。

pytest・build・Monte Carlo simulation は実走していません。全文の静的照合、SHA-256 照合、分布式の決定論的数値評価だけを行い、ファイルは変更していません。

## 第2巡所見の対応表

| 対象 | 状態 | 修正後の確認 | 未修正だった場合の成果物影響 |
|---|---|---|---|
| R1 無効化閉包 | **closed** | 無効化項目7に `a07`〜`a09`、項目8に台帳根・系列分離が追加された。[core §0](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:51) | 異なる workload・arm・schedule の `Y_j` を同一公表coreで受け、推定値・p値・台帳参照が分岐する |
| R2 package の `6×6` | **closed** | 成分ごとの `s_k=0` のみで判定し、`6×6` 特異性では判定しないと明記。[package](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:55) の他の `6×6` 記述も正しい否定説明であり、旧規則は残っていない | `J=4..6` の108セルが恒真通過し、材料レポートのFWER支持表示を誤受理する |
| R3 `ledger_kind` 2値 | **closed** | package要約は公表側の `individual_publication` 1値だけを定め、primary側を `a13` に委ねた。[package 表](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:34) | primary予約のkeyを越権定義し、拒否・二重予約・試行台帳参照が分岐する |
| R4 `α*` の丸め | **closed** | exact等式、`0.01441501` の反例、丸め判定時の `0.0144151` 以上が明記された。[core §5.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:277)。§9の`p02`も同じexact基準。[core §9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:623) | 境界直下の`α_pub`を合格させ、材料レポートに誤った「6下限すべて正」の表示を付ける |
| nit: packageの無条件§5.3要約 | **closed** | `α_pub > α*` の条件つきに修正。[package](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:64) | coreの受理集合は不変だが、承認パッケージが保証範囲を過大表示する |
| nit: `d⁻=1`なら全候補で`L_J=0` | **closed** | `L_J≤0.57628<0.80`、一般には`L_J=0`でないと訂正。[package C-1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:87) | `design_not_feasible`の受理集合は不変だが、材料レポートの検出力下界説明が誤る |

## R4の独立検算

`a11` の式を直接評価すると、

```text
q_raw(13, 0.025) = 3.449997401747738
α* = 6·[1 − F_t,12(q_raw)] = 0.014415014982840
```

となり、本文の `0.014415014983…` を再現する。`a11` の小数第9位切り上げ後の operational `q` は `3.449997402`。

`α_pub=0.01441501` では、

```text
J=13: c_B = 3.449997589098 > q = 3.449997402
```

なので条件を満たさない。

`α_pub=0.0144151` の全候補での比較は次のとおり。

| J | q | c_B | q − c_B |
|---:|---:|---:|---:|
| 4 | 10.999552322 | 7.557028527 | +3.442523795 |
| 5 | 6.670582267 | 5.659333642 | +1.011248625 |
| 6 | 5.264618683 | 4.818437042 | +0.446181641 |
| 7 | 4.589935668 | 4.353354455 | +0.236581213 |
| 8 | 4.197925515 | 4.060750859 | +0.137174656 |
| 9 | 3.942872072 | 3.860571337 | +0.082300735 |
| 10 | 3.764081508 | 3.715352281 | +0.048729227 |
| 11 | 3.631963536 | 3.605351121 | +0.026612415 |
| 12 | 3.530428656 | 3.519220999 | +0.011207657 |
| 13 | 3.449997402 | 3.449994205 | +0.000003197 |

全10候補で狭義に `q>c_B`。最初に破れる境界が `J=13` であることも再現した。

## R1の13 field閉包

| field | 無効化条件との対応 |
|---|---|
| `a01` | phase cap等がcluster受理を変える場合は項目2、失敗枝を変える場合は項目6、build identityを変える場合は項目7 |
| `a02` | 待機秒数は測定プロトコル兼cluster適格条件なので項目2 |
| `a03` | 環境復帰指標・許容範囲はcluster適格条件なので項目2。不成立枝は項目6 |
| `a04` | 失敗の写像先なので項目6 |
| `a05` | binary/build identityは項目7、identity照合による適格条件は項目2 |
| `a06` | 予備経路のwalltime・build受理が変われば項目2または7 |
| `a07` | driver引数一式として項目7に明記 |
| `a08` | arm/source/patch/build/compile argvとして項目7に明記 |
| `a09` | seed・許容schedule集合として項目7に明記 |
| `a10` | 6成分・`T_k`は項目1、`J`候補集合・選択規則は項目5 |
| `a11` | `q`導出規則は項目5。計算可能性・判定不能枝は項目2・6 |
| `a12` | それ自体は`Y_j`の定義・測定対象を変えない。weak nullを変えれば項目2、失敗帰結を変えれば項目6 |
| `a13` | `α₁`は項目5、primary系列の根・ordinalと系列分離は項目8 |

`Y_j` の同一性に影響しうる変更は覆われている。無効化条件は節番号やbytes変更ではなく、8項目の意味変更で発火するため、誤字修正だけの追補A再発行は本書を無効にしない。予定されたsource core §7 erratumも同様に明示除外されている。

## `L_J`の独立検算

`d⁻=1` の最弱成分について全候補を評価すると、検出力 `1-p_k` は `J` とともに増え、最大は

```text
J=13:
p_k = 0.423720051524
1 − p_k = 0.576279948476
```

したがって他5成分が任意に強くても、

```text
L_J ≤ 0.576279948476 < 0.80
```

であり、適格候補は存在しない。一方、他5成分の失敗確率が0へ近づけば `L_13` は `0.57628` へ近づくため、一般に `L_J=0` ではない。6成分すべてが `d=1` の場合に限れば `6p_k>1` となり `L_J=0`。訂正は正しい。

source coreと追補Aの現在のSHA-256も、core §0に記載された値と一致した。§0の再解析禁止、§8.3、§5.3、§9、package間に新たな矛盾は認めなかった。

## 総括

**GO — 残 blocker 0件。**