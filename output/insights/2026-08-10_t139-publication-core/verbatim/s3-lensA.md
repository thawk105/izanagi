結論は **NO-GO、blocker 2 件**です。Holm の式、数値例、成分依存に対する周辺 t の扱いは倒れませんでした。倒れたのは、stress check の未定義枝と、`d=1, J=13` に関する上流の検出力説明です。

## 1. 未調整 p 値

### 1.1 成分依存は周辺 t を壊すか

**判定: refuted**

必要な仮定は、各固定成分について

\[
Y_{1k},\ldots,Y_{Jk}\overset{iid}{\sim}N(\mu_k,\sigma_{kk}),\qquad \sigma_{kk}>0
\]

です。このとき境界帰無 `μ_k=0` で

\[
T_k=\frac{\sqrt J\,\hat\mu_k}{s_k}\sim t_{J-1}.
\]

`μ_k<0` では非心度が負となるため、上側 p 値は super-uniform です。成分間独立性は要りません。

`H` と `G` が線形結合であることも壊しません。workload ごとの変換

\[
A=
\begin{pmatrix}
0&-1&1\\
1-\kappa&-1&0\\
1&0&-1
\end{pmatrix},\qquad \det A=\kappa=0.20
\]

は可逆です。`G=D-N` でも、`D` は公表 family の別成分ではありません。仮に成分間共分散が特異でも、各周辺が非退化正規なら周辺 t は成立します。

**成果物影響:** なし。依存を理由に p 値や Holm 棄却集合を変更する必要はありません。

### 1.2 正定値 guard は文面だけで発火するか

**判定: real。ただし actual p 値では直ちに blocker ではない**

[段2プラン](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-publication-core/s2-plan.md:96) の禁止は規範であって、現時点の active gate ではありません。これは docs-only・B8 本走不可という現在地とは整合しますが、「既に機械的に防いでいる」とは言えません。

また、区別すべきなのは source の workload 別 `3×3` 標本共分散 `S_w` と、公表側の `6×6` 標本共分散です。[追補A](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:817) が要求するのは前者です。後者を正定値必須とすると、`J≤6` では rank が高々 `J−1<6` なので必ず失敗し、source の受理集合を不当に狭めます。

actual publication は「source が `S_w` 非正定値として判定不能なら p を計算しない」という枝で閉じられます。ただし後述の synthetic stress check には同じ枝が定義されておらず、そこは blocker です。

**成果物影響:** source 判定不能を無視すれば、本来 `not computed` の6行に p 値・Holm 棄却が生じ、材料レポートの有意セルと proof chain が変わります。

### 1.3 片側性

**判定: refuted**

- `N=X-D_g>0`: 劣化版から改善。
- `G=S-X>0`: stock を追い越していない。
- `H=D-\kappa S>0`: 劣化幅が `κS` を超える。

いずれも `H_0:\mu_k\le0` 対 `H_1:\mu_k>0` で向きは正しいです。さらに `N>0` と `G>0` なら `D=N+G>0` なので `0<RF=N/D<1` です。

**成果物影響:** なし。符号反転は不要です。

## 2. Holm

**判定: refuted**

6個の p 値について

\[
\tilde p_{(i)}
=\min\left\{1,\max_{1\le j\le i}(7-j)p_{(j)}\right\}
\]

は正しい Holm 調整済み p 値です。

- running maximum なので `\tilde p_(i)` は非減少。
- `α_pub<1` だから

\[
\tilde p_{(i)}<\alpha_{\rm pub}
\iff
\forall j\le i:\quad
p_{(j)}<\frac{\alpha_{\rm pub}}{7-j},
\]

となり、strict 比較で定義した逐次 Holm と同値です。

同値 p の tie-break は棄却集合を変えません。tie block の最初が閾値を通れば、後続の閾値は緩くなるので全て通り、最初で止まれば全て棄却されません。固定順 tie-break は再現性のためだけです。

**成果物影響:** なし。調整済み p 値・棄却集合ともプランどおりです。

## 3. 非整合の数値例

### 3.1 数値

**判定: refuted**

自由度12で直接検算すると、

\[
t_{12,\,0.9955}=3.111245194702233,
\]

したがって `p₂=0.0045` からの逆算値は正しいです。

\[
\hat\mu_2=\frac{3.111245194702233}{\sqrt{13}}
=0.862904160003065,
\]

\[
c_B=t_{12,\,1-0.025/6}
=3.152681312169884,
\]

\[
L_2^{Bonf}
=\frac{3.111245194702233-3.152681312169884}{\sqrt{13}}
=-0.011492311245059.
\]

Holm も

- `0.0020 < 0.025/6`
- `0.0045 < 0.025/5`
- `0.20 > 0.025/4`

なので最初の2件だけを棄却し、調整済み値は `0.0120`、`0.0225` です。

**成果物影響:** なし。Holm 棄却だが Bonferroni 下限が0以下、という例は成立します。

### 3.2 3-arm 標本として実現可能か

**判定: refuted**

6個の `(μ̂_k,s_k)` は完全に独立な原始量ではありませんが、この例は制約を満たして構成できます。

例えば各 workload の raw 変数 `(S,D_g,X)` に標本共分散

\[
Q=\operatorname{diag}(25/41,\,25/41,\,16/41)
\]

を与えると、

\[
\operatorname{Var}(N)=25/41+16/41=1,
\]

\[
\operatorname{Var}(H)=0.8^2(25/41)+25/41=1,
\]

\[
\operatorname{Var}(G)=25/41+16/41=1.
\]

`Q` は正定値で、可逆な `A` により `AQA^\top` も正定値です。`J=13` なら centered subspace の次元は12なので、6本の直交残差列からこの標本共分散を実現できます。

また `D=N+G` と置けば

\[
s_D^2=1+1+2s_{NG},\qquad
s_{DN}=1+s_{NG},
\]

ゆえに

\[
s_D^2+s_N^2-2s_{DN}=1=s_G^2.
\]

指摘された恒等式も破っていません。逆変換した raw 平均も、W1 は概ね `(1.818,0.591,1.576)`、W2 は `(0.388,0.238,0.388)` で正です。適切な Helmert 型残差を割り当てれば各 raw 観測も正に保てます。

**成果物影響:** なし。この反例を「独立に選んだ6個の架空量」として捨てることはできません。

## 4. `C_w(q)` を流用しない判断

**判定: 懸念の中心は refuted**

両 workload の領域を同時に `1−α_pub` で覆うなら、各 workload に `α_pub/2` を与える必要がある、という論証は正しいです。Hotelling 部分には周辺正規だけでなく `(N,D)` の同時正規性も必要なので、marginal t より強い仮定です。

ただし「Holm と互換でない」は Bonferroni 下限にも当てはまるため、それ単独では選択理由になりません。これは論証上の弱さですが、採用案を無効にはしません。

懸念された「primary pass だが公表 Bonferroni 下限が0以下」は、現在の数値では起きません。`J=13, α₁=α_pub=0.025` について、primary の [a11 の q](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:786) は

\[
(1+q^2/12)^{-11/2}+\Pr(t_{12}>q)=0.025
\]

を解いて

\[
q_{\rm primary}\approx3.449997402>c_B\approx3.152681312.
\]

したがって primary pass の `T_k>q_primary` は6成分すべての Bonferroni 下限正を含意します。`J=4..13` の固定候補全体でも `q_primary>c_B` です。

逆方向、すなわち公表成分が有意でも primary が fail することはあります。それは `qualification_status` guard が区別する意図された差です。

**成果物影響:** 懸念された primary-pass/publication-lower≤0 による受理集合変更はありません。

## 5. stress check

### 5.1 marginal セルだけで Holm FWER を押さえられるか

**判定: refuted**

正確な FWER 値は依存に左右されますが、Holm の**上限制御**には marginal bound だけで足ります。

真の帰無の個数を `r=|I₀|` とします。Holm が真の帰無を1つでも棄却したなら、

\[
\min_{k\in I_0}p_k<\alpha_{\rm pub}/r.
\]

したがって各真の帰無について

\[
\Pr(p_k<\alpha_{\rm pub}/r)\le\alpha_{\rm pub}/r
\]

なら、依存にかかわらず

\[
FWER
\le
\sum_{k\in I_0}\Pr(p_k<\alpha_{\rm pub}/r)
\le r\frac{\alpha_{\rm pub}}r
=\alpha_{\rm pub}.
\]

よって `r=1..6` の6閾値を各成分で確認する設計は、固定 empirical DGM 内では Holm の全真偽配置を覆います。`δ_MC/360` の同時上側限界が全セルを覆う限り、この主張は Monte Carlo confidence `1−δ_MC` 付きです。

一方、実世界の cluster 分布に対する保証ではありません。[プラン自身](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-publication-core/s2-plan.md:422)も「固定 empirical support に対する診断」と限定しており、この点は正しいです。

**成果物影響:** なし。依存を理由に360セル設計を捨てる必要はありません。

### 5.2 非正定値・ゼロ分散の synthetic dataset

**判定: real — blocker 1**

empirical support から復元抽出する以上、複数 cluster が同じ residual count vector を取る事象には正の確率があります。そのとき標本共分散は特異になり、対象成分では `s_k=0` も起こり得ます。

しかしプランの

\[
x_{Jkr}=\#\{p_{Jk,b}<u_r\}
\]

は、その dataset を

- 非棄却として数えるのか、
- cell failure とするのか、
- 除外・再抽出するのか、
- source の `S_w` 正定値 gate を適用するのか

を定めていません。選択により `x`、`U`、stress pass が変わります。actual source の「対角だけで救済しない」という文は synthetic dataset の数え方を一意にしません。

**成果物影響:** stress pass/fail と、材料レポートが FWER・同時被覆を「固定 empirical model 下で支持された」と表示できるかが変わります。現仕様のままでは同じ seed から一意に再生成できません。

### 5.3 計算量

**判定: real だが非 blocker**

`360セル × 10^6 dataset` ではありません。プランは同じ `(J,k)` の100万個の p 値を6閾値へ再利用するため、

- dataset 生成: `10×6×10^6 = 6,000万`
- 閾値比較: `3.6億`

です。a12 も dataset 数は6,000万でした。独立 seed で再度6,000万を生成するため総量は増えますが、6倍の dataset ではありません。

実行時間の根拠は示されていないので実現性は未確認です。ただし「不可能」と判定する証拠もありません。

**成果物影響:** 完走しなければ publication stress は未完了となり、支持表示を出せません。source の certified 選択自体は変えません。

### 5.4 seed の旧 core digest

**判定: refuted**

`ac939af4…` は不変な source-core blob identity です。erratum が composed identity を変えても、旧 blob 自体は stale になりません。また seed は完全な provenance digest ではなく乱数 stream の domain separator です。

将来の別仕様は新 core/addendum の identity で区別すべきで、旧結果を見た後に seed を変える方が危険です。

**成果物影響:** なし。seed の再導出は不要です。

## 6. 非正規性と permutation

**判定: 3理由はいずれも refuted。ただし限界自体は real**

1. Fisher randomization が有限標本 exact なのは、既知のランダム割当て機構と sharp null がある場合です。weak mean null だけでは通常の label permutation は exact ではありません。

2. studentized randomization が weak null で漸近的に妥当でも、`J≤13` から有限標本保証は導けません。ただしこれは「t の方が頑健」という証明ではなく、「exact な代替がまだ指定されていない」という結論に限られます。

3. schedule は固定文字列から決定的に導出され、各 cluster で全6順列を1回ずつ実行します。これは順序効果を均衡させますが、確率的な割当て分布を作りません。観測後の label permutation を exact にするには、sharp null、block exchangeability、または真のランダム割当てという追加条件が必要です。

cluster sign-flip も、`E[Y]=0` だけでは exact になりません。少なくとも `Y` と `−Y` の分布同一性という中心対称性が必要で、weak mean null より強い仮定です。

したがって plan の defensible な結論は「t は iid marginal normal model に条件付きで採用し、stress check は診断」とするところまでです。「t が分布自由に妥当」または「permutation より実際に頑健」は言えません。プランは前者を既に否定しています。

**成果物影響:** 正規 model が不適切なら、`p_unadjusted`、`p_holm`、同時下限は model-based な記述値に留まり、weak-null FWER の certified claim は出せません。現プランはこの限定を明記しているため、新たな blocker には数えません。

## 7. 検出力

### 7.1 公表側の各成分

**判定: 「全部非有意になりやすい」は refuted**

`d=1, J=13` では非心度は

\[
\delta=\sqrt{13}=3.60555.
\]

Bonferroni の臨界値 `3.152681312` に対する成分検出力は

\[
\Pr\{t_{12}(\delta)>3.152681312\}\approx0.67049.
\]

Holm の順位別閾値での marginal power は次です。

| 分母 `r` | 閾値 `0.025/r` | power |
|---:|---:|---:|
| 6 | 0.0041667 | 0.6705 |
| 5 | 0.0050000 | 0.7006 |
| 4 | 0.0062500 | 0.7364 |
| 3 | 0.0083333 | 0.7799 |
| 2 | 0.0125000 | 0.8354 |
| 1 | 0.0250000 | 0.9107 |

各成分の実際の Holm power は他成分との順位・依存により、この範囲で変わります。ただし `p_k<0.025/6` なら必ず当該成分まで棄却されるため、各成分の下限は約67%です。

「全部非有意」は Holm の第1段が止まる事象なので、

\[
P(\text{棄却ゼロ})
=P\left(\min_kp_k\ge0.025/6\right)
\le1-0.67049=0.32951.
\]

独立なら

\[
(1-0.67049)^6\approx0.00128.
\]

依存が未指定なので正確な確率は出せませんが、「高い」と一般化することはできません。

**成果物影響:** 公表表が全部非有意になるとの理由で Holm/Bonferroni を変更する根拠はありません。

### 7.2 上流の `d=1`・同時80%説明

**判定: real — blocker 2**

[現 core](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:179) は `d=1.0` を planning alternative とし、6成分同時80%、`J≈13` を sanity 値としています。

しかし `J=13, α₁=0.025` の primary 臨界値は上記のとおり

\[
q_{\rm primary}\approx3.449997402.
\]

`d=1` での各成分 primary pass power は

\[
\Pr\{t_{12}(\sqrt{13})>q_{\rm primary}\}
\approx0.57628.
\]

したがって依存がどれほど有利でも

\[
P(\text{6成分すべて pass})\le0.57628<0.80.
\]

さらに [追補Aの実際の選択式](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:709) では

\[
L_{13}=\max\{0,1-6(1-0.57628)\}=0.
\]

よって `d^-=1` では `J=13` すら選ばれず、固定候補 `J=4..13` に適格値はありません。6成分が同じ standardized effect なら、union-bound 下界80%に必要な `d` は概算 `1.562` です。

なお、source の a10 gate が実際に `L_J≥0.80` を満たして main を許した場合は、`q_primary>c_B` なので primary pass は公表 Bonferroni 全6成分の正下限と Holm 全棄却を含意します。したがって欠陥は公表 Holm ではなく、「`d=1, J≈13` で同時80%」という上流説明です。

**成果物影響:** `d^-` が1付近なら source は `design_not_feasible` で終端し、本走の試行台帳、certified 選択、材料レポート、公表表はいずれも生成されません。sanity 文だけを根拠に `J=13` を通せば、80% power の proof chain が偽になります。

## Nits

- `C_w(q)` 不採用理由のうち「Holm と非互換」は Bonferroni 下限にも当てはまり、比較理由として弱いです。追加の同時正規性と区間の保守性が実質的な理由です。
- 6,000万 dataset の計算時間・資源上限は未提示です。ただし本レビューでは実走していないため、非現実的とまでは断定しません。
- Holm の `<` は通常見かける `≤` より境界で保守的ですが、文書内で一貫しており誤りではありません。

## 総括

**NO-GO — blocker 2 件。**

1. empirical stress check が、非正定値共分散・`s_k=0` の synthetic dataset をどう数えるか未定義で、`x_Jkr` と pass/fail を一意に再生成できない。
2. `d=1, J=13` では primary の成分 power が約57.6%にすぎず、6成分同時80%は数学的に不可能。追補Aの規則では `L₁₃=0` となる。

指定6文書はすべて読取済みです。ファイル変更、pytest、build、Monte Carlo simulation は実行していません。