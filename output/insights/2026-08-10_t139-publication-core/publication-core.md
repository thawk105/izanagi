# [T-139] 個別公表 — 事前登録 core 草案 (2026-08-10 起草。未凍結・未承認)

```text
authority: none
default_effect: no-state-change
study_label: rf_partial_recovery / paired_cluster / individual_publication / core
study_role: publication_only
source_study: rf_partial_recovery / paired_cluster / main_study / core
analysis_admission: requires_addendum_p
new_measurement: none
```

## 0. 本書の位置づけ、source study との関係、凍結の意味

本書は **[T-139] の個別公表 (6 セル固定表) の推論手続き — 未調整 `p` 値の構成、多重調整の方式、
同時区間の構成、正分母 guard — を、source study のデータを 1 点も見る前に固定する事前登録の
core** である。

**本書は別 study の core であって、source study の core の追補でも erratum でもない。**
ユーザー裁定 B4 (a) (2026-08-10) は「公表の検定手続きの正本を、現 core を書き換えない
新しい core を起こす別 study で凍結する」と定めた。本書はその新 core の**草案**である。

**本書は source study の core を 1 byte も変更しない。**本書が source core へ与える効力は無い。
source core の primary 判定、受理条件、状態の閉表、失敗分類、投入 gate、追補の閉集合は、
本書の存在によって一切変わらない。

### source study の同定 (片方向の束縛)

本書は source study を**次の 2 つの三つ組の組**で同定する。core だけでは足りない —
本書は追補 A の `a10` (6 成分の identity と `T_k`)、`a11` (`q` の導出規則)、`a13` (系列の根) を
規範的に参照するためである。source core 自身も「core 単独では完結した事前登録ではない」と書いている。

```text
source_core_path      = output/insights/2026-08-07_t139-mainrun-design/preregistration.md
source_core_commit    = 88d68f9127b31df5aafc3d59607896626a1652e8
source_core_sha256    = ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9

source_addendum_a_path   = output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md
source_addendum_a_commit = 622bd786191d40bda388596fa2adbf119ee84c9a
source_addendum_a_sha256 = f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec
```

これらは source study の**不変な同定子**である。束縛は**片方向**であり、
source study の受領証・binding は本書を参照しない。source study の投入可否は本書に依存しない。

**本書は source study の合成後 digest (erratum 適用後の effective core の digest) を pin しない。**
source study には未発行の erratum が予定されており (裁定 R2 (a)、core §7 の較正義務を
「事前固定 stress check」へ置換する第 2 erratum)、合成後 digest は将来変わる。
変わる値を pin すると、本書が発効した後に source 側の正当な erratum 発行だけで本書が stale になる。

### 無効化条件 (節番号ではなく実体で判定する)

source study の承認済み erratum 集合、または追補 A の再発行が、次の**いずれか**を変えたとき、
**本書は無効になる。**

1. 6 成分 (`N`・`H`・`G` × W1/W2) の定義、`κ` の値、または `T_k` の定義。
2. cluster の適格条件、代表値の作り方、または帰無の型 (weak mean null)。
3. 状態の閉表のラベル集合、first-match の順序、または `qualification_status` の値域。
4. 「6 セル全件を primary の成否にかかわらず固定表で公表する」という要求。
5. `q` の導出規則、`α₁`、`J` の候補集合、または `J` の選択規則。
6. 欠測・失敗の分類、または判定不能の定義。
7. **測定対象の同一性** — W1 / W2 の driver 引数一式 (追補 A `a07`)、3 arm の
   source / patch / build identity と compile argv (`a08`)、または block 実行順を選ぶ
   事前 seed と許容 schedule 集合 (`a09`)。
8. 公表系列の台帳の根、または primary 系列と公表系列を分ける規定 (`a13` を含む)。

7 と 8 は「本書が読む `Y_j` が、本書の凍結時点で想定していた測定と同じものか」を担保する。
**arm や workload の identity が変われば、同じ公表 core で別の測定対象を解析することになる。**

**節番号の一致では判定しない。**erratum が上のどれにも触れないなら、たとえ §3・§5・§7・§16 の
本文に当たる操作であっても本書は無効にならない。**とくに、予定されている core §7 の第 2 erratum
(較正義務を「事前固定 stress check」へ置換するもの) は、cluster の適格条件も帰無の型も
変えないので、本書を無効にしない。**

### 無効化されたときに再解析してよいか (できない)

**無効化は、既に観測した公表 dataset を別の手続きで解析し直す許可ではない。**

- 本書の手続きで公表表を**一度でも計算した後**は、その dataset に対して新しい公表 core を
  適用してはならない。無効化以後の新しい公表 core が対象にできるのは、
  **無効化の時点でまだ観測されていない dataset** だけである。
- 公表表を計算する前に無効化が起きた場合に限り、新しい公表 core を起こしてよい。
  その場合も**旧結果を置換せず**、無効化の事実・erratum の identity・時系列を記録する。
- **無効化の必要性は、公表側の結果を 1 つも見ていない時点で確定していなければならない。**
  公表表を見た後に発行された source erratum を根拠に、本書を無効化して同じデータへ
  別の手続きを当てることはできない。

この 3 点は、§8.3 の「同一 dataset の再解析禁止」を無効化経由で迂回する経路を閉じるためのものである。

### 凍結の意味

凍結の実装は source study と同じく commit / path / blob 参照束縛とする。結果の記録は
本書の `<commit>` / `<path>` / blob SHA-256 の三つ組を参照し、当該 commit が解析 checkout の
祖先であることを検証側が確認する。**本書は自分自身の digest を本文へ書かない** (自己参照の禁止)。
作業木の bytes を固定する検査 (`FROZEN_MANIFEST` 型) は置かない。

**結果を見てから本書を書き換えてはならない。**書き換えたらそれは別 study である。
未確定として残る量は §9 の**追補**に閉集合で委ねてあり、追補は本書の推論内容を変更できない。

### 現在の段階

| 段階 | 状態 | 現在地 |
|---|---|---|
| 1 | 草案。`authority: none`。承認待ち | **← ここ** |
| 2 | 文書として発効 (承認決定を canonical 台帳へ fold した commit 以後)。機械 gate 未実装 | 承認後 |
| 3 | resolver・validator・consumer・台帳が実装され、gate が実際に発火する | 実装 wave 以降 |

## 1. 公表上の問い

**6 成分それぞれについて、母平均が 0 を超えるか。**

これは source study の primary (「代替 X は劣化を部分的に回復するか」) の**再判定ではない。**
primary は 6 成分の**連言**に対する 1 本の判定であり (source core §4)、本書が扱うのは
**成分ごとの個別公表**である。個別公表の結果から primary の判定を導いてはならない。
逆に primary の成否によって公表する行を選んでもならない (source core §16、§6 に再掲)。

## 2. 入力と公表 family

### 2.1 入力 (公表 dataset)

本 study は**新しい測定を 1 件も要求しない。**入力は source study が既に取得し、
source study の独立 validator が適格と確定した cluster level の代表値だけである。

```text
公表 dataset = source study の validator が本走について適格と確定した
               適格 cluster の全件。J はその件数であり、本書は J を選ばない。

各 cluster j について
Y_j = ( N_W1,j , H_W1,j , G_W1,j , N_W2,j , H_W2,j , G_W2,j )ᵀ ∈ R⁶
```

**部分集合・並べ替え・除外・追加を禁じる。**適格と確定した cluster のうち一部だけを
公表解析へ渡すことはできない。cluster の適格性は source study の規則 (source core §7・§9) だけで
決まり、本書は適格性の判定に一切関与しない。**本書は新しい失敗分類を作らない。**

source study が判定不能・`design_not_feasible`・候補の終端 reject で終わった場合、
公表表は生成されない。本書は救済経路を持たない。

### 2.2 family と固定順

公表 family は次の**固定順**の 6 成分とする。

```text
k = 1 : N_W1     k = 2 : H_W1     k = 3 : G_W1
k = 4 : N_W2     k = 5 : H_W2     k = 6 : G_W2
```

成分の意味 (`N` = 回復量、`D` = 劣化幅、`G` = 元の版までの残り、`H = D − κ·S`、`κ = 0.20`) は
source core §3 の定義をそのまま参照する。**本書は量を定義し直さない。**
`D` は family に含めない (`D = N + G` であり、`N` と `G` を公表すれば復元できる)。

## 3. 未調整 `p` 値

### 3.1 帰無仮説

成分 `k` の母平均を `μ_k` とし、各成分について

```text
H_{0,k} : μ_k ≤ 0
H_{1,k} : μ_k > 0
```

を検定する。3 成分とも「大きいほど主張が強い」向きである
(`N > 0` = 劣化版より速い、`G > 0` = 元の版に達していない、`H > 0` = 劣化幅が `κ·S` を超える)。

### 3.2 統計量と `p` 値

公表 dataset の標本平均を `μ̂`、**不偏**標本共分散 (分母 `J − 1`) を `Ŝ_J` とし、
`s_k = sqrt((Ŝ_J)_kk)` とする。

```text
T_k = √J · μ̂_k / s_k
p_k^unadj = 1 − F_{t, J−1}( T_k )
```

`F_{t, J−1}` は自由度 `J − 1` の**中心** `t` 分布の累積分布関数である。`p` 値は片側とする。

**`T_k` は source study の追補 A `a10` が定めた `T_k` と同一の量であり、新しい統計量ではない。**
ただし `a10` はこれを標本数設計のために導入した。**公表用 `p` 値としての意味と帰無仮説は
本書が新たに固定する。**本書は追補 A を権威文書として継承せず、上の式を独立に規範化する。

### 3.3 妥当性の条件と計算不能の枝

上の `p` 値が水準を守るために必要なのは、**各成分の周辺**が
`Y_{1k}, …, Y_{Jk} ~ iid N(μ_k, σ_kk)`、`σ_kk > 0` であることだけである。
成分間の独立性は要らない。`H` と `G` が `(S, D_g, X)` の線形結合であることも、
各周辺が非退化正規である限りこの条件を壊さない。`μ_k < 0` では非心度が負になるので
上側 `p` 値は super-uniform である。

**`6×6` の標本共分散 `Ŝ_J` が正定値であることは要求しない。**必要なのは対角成分だけであり、
`J ≤ 6` では `Ŝ_J` の rank は高々 `J − 1 < 6` なので、正定値を要求すると
source study の受理集合を不当に狭める。

**計算不能の枝は source study から継承する。**source study の追補 A `a11` は、workload ごとの
`3×3` 標本共分散 `S_w` が正定値でなければ統計量を計算せず、source core §7 の**判定不能**へ写す。
その枝に入った workload については、本書も `p` 値・調整済み `p` 値・同時下限を計算しない。
**対角成分だけを使って救済してはならない。**

> **この禁止は現時点で文書上の規範であり、機械的に執行されていない** (§11 を参照)。

## 4. 多重調整 — Holm

### 4.1 手続き

6 個の未調整 `p` 値を非減少順に並べ、同値の場合の tie-break は §2.2 の固定順とする。

```text
p_(1) ≤ p_(2) ≤ … ≤ p_(6)

p_(i)^Holm = min{ 1 , max_{1 ≤ j ≤ i} [ (7 − j) · p_(j)^unadj ] }
```

これを元の成分順へ戻して公表する。成分 `k` の棄却は

```text
p_k^Holm < α_pub        (等号は棄却しない)
```

とする。数値の表示丸めを棄却判定の入力にしない。判定は倍精度以上で行い、
公表表に載せる丸めた値から再計算した結果を権威としない。

上式の running maximum により `p_(i)^Holm` は非減少であり、`α_pub < 1` のもとで
`p_(i)^Holm < α_pub` は「すべての `j ≤ i` について `p_(j)^unadj < α_pub/(7−j)`」と同値である。
すなわち逐次 Holm 手続きと同じ棄却集合を与える。tie-break の規定は棄却集合を変えない
(同値 block の先頭が閾値を通れば後続の閾値はより緩いので全て通り、先頭で止まれば全て止まる)。
固定順は再現性のためだけに置く。

### 4.2 Holm を採る理由と、採らない方式

**Holm は任意の依存構造のもとで familywise error rate を `α_pub` 以下に保つ。**必要なのは
各成分の marginal `p` 値が帰無のもとで super-uniform であることだけである。
6 成分は `(S, D_g, X)` の線形変換で構造的に相関するが、その相関構造を推定して使う手続きは、
相関推定の妥当性という追加の分布仮定を要する。小標本 (`J ≤ 13`) と非正規性が既知の攻撃面である
以上、ここで仮定を増やす根拠がない。

- **一般の closed testing は採らない。**相関を利用する有効な局所検定を置けば Holm より強くできるが、
  それには 63 個の intersection hypothesis すべてに局所検定を完全指定する必要があり、
  各局所検定の妥当性が新たな仮定になる。**「Holm は closed testing の shortcut だから
  劣らない」という論法は誤りである** — Holm は Bonferroni 局所検定を置いた closure に対応するに
  すぎず、より強い局所検定を持つ closed testing の方が強い。
- **BH (FDR) は採らない** (裁定 Q7)。「1 つでも偽の主張が入る確率」を制御しないためである。
- **実行時に別方式へ切り替えることを禁じる。**Simes、相関推定型 maxT、FDR 系のいずれへも、
  データを見た後に切り替えてはならない。

## 5. 同時下限

### 5.1 構成

```text
c_B = F_{t, J−1}^{-1}( 1 − α_pub / 6 )
L_k = μ̂_k − c_B · s_k / √J
I_k = [ L_k , ∞ )
```

各成分の marginal `t` 手続きが妥当であるという条件のもとで、Bonferroni の union bound により

```text
P( すべての k について μ_k ∈ I_k ) ≥ 1 − α_pub
```

が成り立つ。**成分間の独立性は仮定しない。**

### 5.2 Holm の棄却集合と一致しないこと

**有意セルの決定は Holm 列だけから行う。**`I_k` が 0 を含むかどうかは Holm の棄却集合を
再定義しない。**Holm が棄却した成分の `I_k` が 0 を含む場合がありうる。**
これは矛盾でもデータ破損でもなく、異なる familywise 手続きの結果である。
この現象を「不整合の検出」として扱い、値を修正・再計算・拒否してはならない。

**実例 (本書の起草時に検算した構成。実測データではない):**
`J = 13`、`α_pub = 0.025`、`s_k = 1`、未調整 `p` 値が
`(0.0020, 0.0045, 0.20, 0.30, 0.40, 0.50)` のとき、Holm は最初の 2 成分を棄却する
(`0.0020 < 0.025/6`、`0.0045 < 0.025/5`) が、第 2 成分の同時下限は
`L_2 = (T_2 − c_B)/√J = (3.111245194702 − 3.152681312170)/√13 = −0.011492311245 < 0`
となり、`I_2` は 0 を含む。

### 5.3 非整合が起こりうる枝の限定 (`α_pub` に依存する)

**`α_pub` が下記の条件を満たす場合に限り、source study の primary が pass する枝では
この非整合は起こらない。**この限定は無条件ではない。

source study の追補 A `a11` の臨界値 `q(J, α₁ = 0.025)` と本書の `c_B(J, α_pub)` を
候補 `J = 4, …, 13` の全てについて比較すると、

```text
すべての J ∈ {4, …, 13} で  q(J, 0.025) > c_B(J, α_pub)
⟺  α_pub > α*               (最初に破れるのは J = 13)

α* は  c_B(13, α*) = q(13, 0.025)  の解であり、
α* = 6 · [ 1 − F_{t,12}( q(13, 0.025) ) ] = 0.014415014983…
```

である。**判定は丸めた値ではなく上の等式で行う。**`α*` を切り捨てた値 (例 `0.0144150`) を
閾値にすると、`α_pub = 0.01441501` のように「切り捨て値は超えるが `α*` は超えない」値を
誤って合格させる (この値では `J = 13` で `c_B = 3.449997589 > q = 3.449997402` となり、
限定は成り立たない)。**丸めた閾値で機械判定するなら、`α*` を切り上げた `0.0144151` 以上を
要求する** (保守側。この値では `J = 4, …, 13` の全てで `q > c_B` である)。

`α_pub = 0.025` (追補 B 草案 `b02` が提案した値) はこの条件を満たし、
`J = 13` で `q = 3.449997 > c_B = 3.152681`、`J = 4` で `q = 10.999552 > c_B = 6.231543` となる。

**追補 P の `p02` が `α_pub ≤ α*` を選んだ場合、本節の限定は成り立たない。**
その場合、公表表には「primary が pass しても同時下限が 0 を含みうる」ことを明記しなければならない。
`p02` はこの条件を満たすか否かを**明示的に記録する** (§9)。
`a10` により primary の受理は `∩_k { T_k > q }` と一致するので、primary が pass するなら
すべての `k` で `T_k > q > c_B` であり、したがって

```text
L_k = (s_k/√J)(T_k − c_B) > 0        (6 成分すべて)
p_k^unadj < α_pub/6                   (6 成分すべて)
```

となり、**Holm は第 1 段で 6 件すべてを棄却し、同時下限も 6 本すべて正である。**
逆向き (公表側が有意でも primary が pass しない) は起こりうる。それは
`qualification_status` guard が区別する意図された差である (§6)。

### 5.4 source study の同時領域 `C_w(q)` を流用しない理由

`a11` の `C_w(q)` は workload ごとに `(N, D)` の 2 次元 Hotelling 領域と `H` の片側領域を
共通の `q` で束ねたものである。これを公表側の 6 成分同時被覆へ流用すると、

- 両 workload を同時に覆うために `q(J, α_pub/2)` が必要になり、primary と同じ `q` ではなくなる。
- Hotelling 部分は `(N, D)` の**同時**正規性を要求する。§3.3 の marginal 正規性より強い仮定である。

本書は marginal `t` の妥当性だけを要求する構成を選ぶ。
なお「Holm と互換にならない」ことは Bonferroni 下限にも等しく当てはまるので、
それは `C_w(q)` を退ける理由にならない。

## 6. 固定公表表と正分母 guard

裁定 R5 (a)+(d) (2026-08-09) は「source core は触らず、公表側に正分母 guard
(`qualification_status` の併記) を課す」と定めた。本節がその正本である。

### 6.1 固定表

公表表は §2.2 の固定順で**ちょうど 6 行**を持つ。primary の成否、各行の有意性、
`qualification_status` の値のいずれによっても行を省略・並べ替え・追加してはならない。

各行は少なくとも次を必須欄として持つ。

```text
workload, component, J, estimate (μ̂_k), s_k, T_k,
p_unadjusted, p_holm, holm_reject,
simultaneous_lower_bound (L_k),
qualification_status,
RF_point, RF_confidence_set, interval_shape
```

`RF_point`・`RF_confidence_set`・`interval_shape` は source study が
`a11` の ratio projection と source core §5 から確定した値であり、**本書は再構成しない。**

### 6.2 `qualification_status` の権威

`qualification_status` は、**source study の独立 validator が source study の `q` と
source core §5 の first-match 表から確定した当該 workload の値**を、その workload の
3 行すべてへ**逐語で複写する**。

- **公表用の `p` 値・Holm 棄却・同時下限から再計算してはならない。**
- **producer または renderer の自己申告値を用いてはならない。**
- 複写元が存在しない場合、公表表は生成できない。**「不明」「未確定」を値として書いてはならない。**

### 6.3 正分母 guard

`qualification_status` が `partial_recovery` でない行について、`RF_point` と
`RF_confidence_set` を「回復率が認証された」と解釈してはならない。
**個別成分が Holm で棄却されても、この禁止は変わらない。**

`qualification_status = degradation_absent` (source core §5 軸 2 の順 2、`D̄_w < 0`) の行では、
`RF_point` と `RF_confidence_set` を固定表から隠さない。ただし各行に次を必ず併記する。

```text
分母 D̄ は負であり、この RF は分子・分母がともに負になりうる形式上の比である。
値が (0,1) に入っても回復を意味しない。
```

`weak_denominator_not_certifiable` (`A ≤ 0`) の行にも、分母の信頼集合が 0 を除外できない旨を併記する。

## 7. 非正規性と事前固定 stress check

### 7.1 限界の明示

`J ≤ 13` で cluster 代表値が正規から外れる場合、`t` に基づく `p` 値は名目水準を守らない。
`E[Z] = 0` を満たす混合分布で破れる構成が存在する。**この限界は source study の primary にも
等しく及び、追補 A も既に明記している。本書はこの限界を解消しない。**

`t` に基づく手続きは「cluster 代表値の iid marginal 正規 model に**条件付き**」で採用する。
**「分布自由に妥当」「permutation より頑健」とは主張しない。**

### 7.2 permutation / randomization を primary に採らない理由

- 本 study の帰無は **weak mean null** である (source core §7)。Fisher randomization 検定が
  有限標本で厳密なのは、既知の割当て機構と **sharp null** がある場合である。
- studentized randomization は weak null に対し大標本で妥当になりうるが、`J ≤ 13` から
  有限標本の保証は導けない。
- cluster 内の block 実行順は事前 seed から**決定的に**導出され (追補 A `a09`)、
  各 cluster が全 6 順列をちょうど 1 回ずつ含む。これは順序効果を均衡させるが、
  確率的な割当て分布を作らない。観測後の label permutation を割当て分布と見なせない。
- cluster の符号反転 (sign-flip) は、`E[Y] = 0` に加えて `Y` と `−Y` の分布同一性
  (中心対称性) を要する。これは weak mean null より強い仮定である。

**これらは「`t` の方が頑健である」ことの証明ではなく、「厳密な代替が本設計では指定できない」
という結論に限られる。**

### 7.3 事前固定 stress check

本 check は、**固定した empirical model のもとで、本書の Holm 手続きが名目水準を超えないこと**を
確認する診断である。追補 A `a12` と同型だが、**独立に規定する**(追補 A を継承しない)。

**固定入力** (追補 A `a12` と同じ raw を独立に再指定する):

```text
path   = output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/throughput.tsv
sha256 = 755cfa7ea7c22ac763f404769103fd2ff0c49763c79369ac826db6a32b71c4f2
```

**data-generating model.** 各 workload `w`、rep `r = 1..5` について

```text
Z_{w,r} = ( X − D_g , (1−κ)S − D_g , S − X )      (κ = 0.20)
e_{w,r} = Z_{w,r} − (1/5) Σ_{s=1..5} Z_{w,s}
```

を作り、`{e_{w,r}}` を 3 次元 residual の empirical support とする。simulation 内の 1 cluster は、
6 permutation block へ `e_{w,r}` を復元抽出で 6 回割り当てた平均とする。
各 simulated dataset はこれを `J` cluster 生成する。

**格子と反復数:**

```text
J = 4, …, 13                     (10 通り)
k = 1, …, 6                      (成分)
r = 1, …, 6                      (Holm の順位。閾値 u_r = α_pub / r)
B = 1,000,000 dataset            (候補 J ごと。6 成分で共有する)
セル数 = 10 × 6 × 6 = 360        (セル = (J, k, r))
δ_MC = 0.001
```

**1 つの dataset は 6 成分すべての `p` 値を同時に与える。**成分ごとに別の dataset を
生成しない。したがって生成する dataset の総数は `10 × 1,000,000 = 1,000 万`、
`p` 値の計算は `6,000 万` 回、閾値比較は `3.6 億` 回である。

セル間の計数は同じ dataset を共有するので**独立ではない**。しかし各セルの上側限界は
marginal に妥当であり、360 セルへ `δ_MC/360` を配る Bonferroni は**依存によらず**成り立つので、
共有は保証を弱めない。

**実行時間の裏付けは本書の起草時点で得ていない。**完走しない場合は §7.5 に従う。

**乱数:**

```text
seed = 7ba4ba27d67b66b3aa3e3be9e7b649a08b1025c773ef3dddf43f3f9d55305ad9
```

これは次の ASCII byte 列 (末尾 newline なし) の SHA-256 である。

```text
t139-publication-core-stress-v1
```

**seed の preimage は source core の digest を含まない。**乱数 stream の domain separator に
provenance の意味を持たせないためである (source core には未発行の erratum が予定されており、
特定の digest を含めると有効 core の同定と食い違う)。本書自身の digest も含まない (自己参照の禁止)。

**乱数の生成規則 (実装間で同じ値が出るまで一意に定める)。**
`seed_bytes` は上の digest の**生の 32 bytes** とする (16 進 ASCII 文字列ではない)。

1 回の抽選は「候補 `J`・dataset 番号 `b`・cluster 番号 `c`・workload `w`・block 番号 `t`」で
一意に決まり、**評価順序に依存しない。**

```text
domain(J,b,c,w,t) = ASCII("t139-pub-stress-v1|J=%d|b=%d|c=%d|w=%d|t=%d")
                    (%d は 10 進、前置ゼロなし。区切りは半角 |。末尾 newline なし)

block(n)  = SHA-256( seed_bytes || 0x00 || domain(J,b,c,w,t) || uint64_be(n) )
v(n)      = block(n) の先頭 8 bytes を big-endian の符号なし 64 bit 整数として読んだ値
```

`n = 0` から始め、`v(n) < floor(2^64 / 5) * 5` を満たす最初の `n` を採り、
`index = v(n) mod 5` (0 起点) とする。満たさなければ `n` を 1 増やして繰り返す
(modulo bias を避ける rejection sampling)。**counter は抽選ごとに 0 から始まり、
抽選を跨いで持ち越さない。**

範囲は `b = 1..B`、`c = 1..J`、`w ∈ {1, 2}` (1 = W1、2 = W2)、`t = 1..6` である。
`index` は当該 workload の 5 要素 empirical support `{e_{w,1}, …, e_{w,5}}` の添字とする
(`index = 0` が `e_{w,1}` に対応する)。

各 cluster の代表残差は workload ごとに 6 回の抽選の**算術平均**とし、
W1 の 3 成分と W2 の 3 成分を §2.2 の固定順に連結して 6 次元ベクトルを作る。
**W1 と W2 の抽選は独立に行い、同じ添字を共有しない。**

**すべての成分の母平均を 0 に置く** (empirical support は中心化済みなので、
上の生成でそのまま weak-null が成り立つ)。成分ごとに別の帰無配置を作らない。

**ライブラリ固有の PRNG に依存しない。**

**判定規則.** `x_{Jkr}` を「候補 `J` の `B` 個の dataset のうち、成分 `k` の未調整 `p` 値が
`u_r = α_pub/r` を**下回った**件数」とする (等号は数えない)。

```text
U_{Jkr} = Beta^{-1}( 1 − δ_MC/360 ;  x_{Jkr} + 1 ,  B − x_{Jkr} )     (x = B のとき U = 1)
pass  ⟺  全 360 セルで  U_{Jkr} ≤ u_r
```

### 7.4 縮退した synthetic dataset の数え方 (曖昧さを残さない)

empirical support からの復元抽出なので、**成分 `k` の `J` 個の cluster 値がすべて一致し
`s_k = 0` になる** dataset が正の確率で生じる。この dataset は、**その成分 `k` について**
`x_{Jkr}` の件数に数えない (非棄却として数える)。他の成分の計数には影響しない。

- **除外しない** (除外は分母 `B` を変える)。
- **再抽出しない** (再抽出は分布を変える)。
- `s_k = 0` かつ `μ̂_k > 0` を「`T_k = +∞` だから棄却」と数えることも**しない**。

**判定は成分ごとの `s_k` だけで行い、`6×6` 標本共分散の特異性では判定しない。**
`J ≤ 6` では `6×6` 標本共分散の rank は高々 `J − 1 < 6` なので**必ず**特異であり、
特異性で縮退枝へ送ると `J = 4, 5, 6` の 108 セルが手続きを 1 度も試さないまま
`x = 0` で通過してしまう (恒真な通過)。これは §3.3 が「`6×6` の正定値を要求しない」と
定めたことと同じ理由であり、simulation と実データで判定基準を変えてはならない。

この規則により、同じ seed から `x_{Jkr}` と pass/fail が一意に再生成される。

### 7.5 この check が保証すること・しないこと

**保証する.** 真の帰無の個数を `r` とすると、Holm が真の帰無を 1 つでも棄却したなら
`min_{k ∈ I₀} p_k < α_pub / r` である。したがって各真の帰無について
`Pr(p_k < α_pub/r) ≤ α_pub/r` が成り立てば、依存構造によらず union bound で
`FWER ≤ α_pub` が従う。360 セルはこの `r = 1..6` × 成分 × `J` を覆う。

**保証しない.** これは**固定した empirical support のもとでの診断**であり、
実世界の cluster 分布に対する較正ではない。**通過しても §7.1 の混合分布反例を排除しない。**
「任意の非正規分布に対して較正した」と記述してはならない。

**失敗時の帰結.** 1 セルでも超過、simulation が未完了、入力 digest 不一致、seed / 反復数の
不一致のいずれかなら、公表表に **FWER と同時被覆が制御されたという表示を付けてはならない**。
記述的な値 (`estimate`、`s_k`、`T_k`) は公表してよい。
**source study の失敗分類へは写さない。**`design_not_feasible` を含む source 側の終端状態を
本 check の結果から作ってはならない。`α_pub` を緩めること、`J` の候補を部分除外すること、
source の raw を使って再較正することも行わない。

## 8. 公表系列の累積台帳

source core §10 と裁定 U8 は、primary 系列と個別公表系列に**別々の**累積台帳を置くと定めた。
追補 A `a13` が primary 系列の根と ordinal を束縛している。本節は公表系列側を定める。

### 8.1 正規の根と種別

```text
family_root = 88d68f9127b31df5aafc3d59607896626a1652e8
              (source study の限定例外を canonical 台帳へ fold した commit)
本 study が占める entry = ( family_root , individual_publication , ordinal )
```

**本書が定めるのは公表系列の側だけである。**公表系列の entry が名乗ってよい種別は
`individual_publication` **の 1 値だけ**とし、公表側から他の値 (`exploratory` 等) を名乗って
新しい `k = 1` を取り直すことを禁じる。

**本書は primary 系列の種別名を定義しない。**primary 系列の根と ordinal の正本は
追補 A `a13` であり、その entry の key 形状を本書が名付け直すことは越権である。
実装は「公表系列の entry 空間が primary 系列の entry 空間と**互いに素**であること」だけを
保証すればよく、primary 側の key 形状は `a13` に従う。

**根は呼び手が選べない。**本書の freeze commit / path / blob は「文書の identity」であって
台帳の根ではない。**新 core を起こしたことを根拠に ordinal をリセットしてはならない。**

`family_root` が primary 系列と同じ commit であることは意図どおりである。
2 系列は balance・entry・ordinal を共有しない。
`α₁ = 0.025` と `α_pub` が同じ数値であっても、**同一の予算ではない。**

> **重複する記述がある。**追補 B 草案 (`b03`) も `ledger_kind = individual_publication` を
> 提案している。**どちらが公表系列の正本かは未確定であり、承認時のユーザー裁定に委ねる**
> (`package.md` の C-2)。本書はこの重複を自分の側で一方的に解決しない。

### 8.2 予約の規範

- 予約は **create-only** とし、失敗・中断した試行も番号を解放しない。
- 予約は producer が選べない canonical な台帳で原子的に行う。
- **本書の宣言は自己申告であり、それ自体は権威ではない。**台帳側の予約が無い、
  または重複しているなら公表表を生成しない。

> **本書だけでは閉じない。**この規範は、呼び手が選べない外部台帳が実在してはじめて防壁になる。
> 台帳の実体化は実装 wave の責務であり、本書はコードを追加しない (§11)。

### 8.3 同一データの再解析を禁じる

**同一の公表 dataset (§2.1) に対して、第 2 の公表 core を起こしてはならない。**
公表系列の ordinal は**新しい候補 (新しいデータ)** のためのものであり、
同じデータの再解析へ消費できない。

本書の手続きで得た結果が気に入らない場合に、別の公表 core を起こして次の ordinal と
spending を消費し、同じデータを別の手続きで解析し直すことを**禁じる**。
本書が無効になる場合の扱いは §0 の「無効化されたときに再解析してよいか」に従う —
**公表表を一度でも計算した後は、その dataset へ新しい公表 core を適用できない。**

> **この禁止は現時点で文書上の規範であり、機械的に執行されていない** (§11)。
> 公表台帳が実在するまで、違反する入力を拒否する層は存在しない。

## 9. 追補の閉集合

追補は**本書が書いた文章を一切変更しない。**追補が設定してよいのは次の field だけである。
それ以外の変更は本書の変更に当たり、本書を書き換える必要が生じたらそれは別 study である。
追補が閉集合の外の field を含んでいたら、その追補は解決に失敗しなければならない
(**この拒否を行う exact-key 検査は現時点で存在しない。**既存の検査は source study の
`a01`〜`a13` 専用である。§11 を参照)。

**追補 P — source study の pilot 1 本目の投入より前に commit する:**

| # | field | 内容 | core で決められない理由 |
|---|---|---|---|
| p01 | 公表系列の候補数上限と許容 ordinal | 資源と governance の裁定であり、統計量から導けない |
| p02 | 公表系列の累積 spending 関数の数値割当て (`α_pub` を含む) | familywise 予算の配分はユーザー裁定である |
| p03 | 公表台帳の予約規則の実装契約 (台帳の同定・原子性の要件) | 呼び手が選べない台帳の実体が決まらないと確定しない |

**field id は `p01`〜`p03` とし、source study の追補 A / B の名前空間 (`a01`〜`a13`、`b01`〜`b03`) と
二義化しない。**本書の追補は source study の追補 A / B の文書を継承・参照・合成しない。

**追補へ送ってはならないもの (本書の本文で決めるもの):** 6 成分の identity と固定順、
帰無仮説、`T_k`、未調整 `p` 値、Holm の式と tie-break、同時下限の構成、
`qualification_status` guard、stress check の仕様、公表 dataset の選択規則、時点の条件。

**追補が越えてはならない線:**

- 追補は `p` 値・調整方式・区間の**構成**を変えない。数値の配分だけを持つ。
- `p02` は、選んだ `α_pub` が §5.3 の条件 (`α_pub > α* = 0.014415014983…`) を
  **満たすか否かを明示的に記録する。**判定は §5.3 の等式で行い、丸めた閾値では行わない。
  満たさない場合、公表表は「primary が pass しても同時下限が 0 を含みうる」旨を併記する。
- 追補は §2.1 の dataset 規則を狭めも広げもしない。
- 追補は §7.4 の縮退枝の数え方を変えない。
- 追補は source study の受理集合・失敗分類・`pilot_admission` へ一切影響しない。

追補は本書と同じく解析前に commit し、結果の記録がその `<commit>` / `<path>` / blob digest を
参照する。**追補は自分が従属する本書の canonical path・commit・blob digest の三つ組を明記する。**

## 10. 時点の条件と片方向性

### 10.1 凍結の時点

**本書と追補 P は、source study の pilot 1 本目の投入より前に承認・commit・fold されていなければ
ならない。**本走より前では足りない。pilot は本走の `J` と分散構造を明らかにするため、
pilot 後に手続き・区間・`α_pub` を選べる経路が残ると結果依存の選択になる。

### 10.2 source study の受理条件を狭めない

**本書は source study の `pilot_admission: requires_addendum_a` にも
`main_admission: requires_addendum_a_and_b` にも条件を足さない。**
`submit_pilot` / `submit_main` が本書の存在を要求するようにしてはならない。
これらを変えることは source core の変更であり、本書の権限の外である。

本書が間に合わないまま source の pilot が走った場合、**source study の admission を遡って
失敗扱いにはしない。**帰結は「本 study を事前登録済みとして扱えない」ことだけである。
その場合、公表表は事前登録済みの解析としては公表できない。

### 10.3 片方向性 (結果の逆流禁止)

**公表側の結果を source study の primary へ逆流させてはならない。**
`p_k^unadj`、`p_k^Holm`、`holm_reject`、`L_k` のいずれも、certified 選択・primary の受理判定・
`qualification_status` の決定の入力にしてはならない。依存の向きは
**source → publication の一方向だけ**である。

### 10.4 実装時に必ず kill する変異 (文書上の要件)

実装 wave はこれらを機械的に拒否できることを示す。**本 wave はこれを実装しない。**

1. 適格 cluster の一部だけを公表 dataset として受理する (§2.1 の全件性)。
2. 6 行のうち有意でない行、または `qualification_status` が `partial_recovery` でない行を
   固定表から落とす (§6.1)。
3. `qualification_status` を公表側の `p` 値・下限から再計算する、または producer の申告値を使う (§6.2)。
4. `6×6` 標本共分散の対角だけを使って、source が判定不能とした workload の `p` 値を計算する (§3.3)。
5. Holm の閾値比較を `<` から `≤` へ緩める、または表示丸めの値で判定する (§4.1)。
6. 実行時に BH / Simes / 相関推定型 maxT へ切り替える (§4.2)。
7. `ledger_kind` に閉集合外の値を名乗って新しい `k = 1` を取る (§8.1)。
8. 同一 dataset に対する第 2 の公表 core の結果を受理する (§8.3)。
9. 追補 P が §9 の閉集合の外の field を設定する。
10. stress check が縮退 dataset を除外・再抽出して `x_{Jkr}` を変える (§7.4)。
11. 公表側の結果を certified 選択の入力へ渡す (§10.3)。

## 11. 本書が主張しないこと

- **本書が機械的に執行されている、とは主張しない。**本書が定めるのは文書上の契約である。
  次の層はいずれも**存在しない**。

  | 層 | 公表表が出るために必要な処理 | 現状 |
  |---|---|---|
  | producer / 受領証 | source の binding と公表 dataset pointer を記録する | T-139 の producer は未完成 |
  | source validator | raw 受領証から cluster・`J`・`Y_j`・`qualification_status` を再計算する | 未実装 (§6.2 の複写元が無い) |
  | publication validator | `T_k`・未調整 `p`・Holm・同時下限・6 行固定表を再計算する | 未実装 |
  | consumer / renderer | source validator を同一呼出しで再実行し、6 行を省略しない | 未配線 |
  | 公表台帳 | 根・ordinal・spending を原子的に予約・照合する | 実体なし |
  | `p` 追補の exact-key 検査 | `p01`〜`p03` の過不足を拒否する | 実装なし (既存検査は `a01`〜`a13` 専用) |

- **本書が時点独立性を証明した、とは主張しない。**「pilot の raw を見る前に凍結された」ことは
  文面からは検証できない。承認と台帳予約の**運用手順**によってのみ担保される。
- **`p` 値・区間が分布自由に妥当である、とは主張しない** (§7.1)。
- **本書が source study の本走を投入可能にした、とは主張しない。**source core の
  `main_admission: requires_addendum_a_and_b` が要求する追補 B は source core に従属する文書であり、
  **本書に従属する追補 P はその追補 B にはなれない。**本書の承認は本走の投入可否を変えない。
- **公表側の有意判定から回復の機序を帰属できる、とは主張しない。**機序の帰属は本 study でも
  source study でも行わない (3 変更を同時に入れたため)。
- **`RF > 1` を「回復」とも「新規改善」とも帰属しない** (source core §5・§16 をそのまま継承)。
