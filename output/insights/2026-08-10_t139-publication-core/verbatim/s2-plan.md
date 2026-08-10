結論から言うと、P2 は採用可能、P3 は「Holm 推奨」という結論は維持できるものの理由を訂正、P4 は (a)「Holm と非整合であることを明記した Bonferroni 同時下限」を推奨します。新 core は現 core を置き換えず、検証済み cluster 代表値だけを入力にする公表専用の下流 study とします。

最大の未解決点は、新 core に束縛した追補が、現 core の `main_admission: requires_addendum_a_and_b` を満たせないことです。したがって新 core だけで本走を解禁してはなりません。

### 参照記号

- `S1`: [親 brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-publication-core/s1-brief.md:1)
- `C`: [現 core](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:1)
- `A`: [追補 A 再発行版](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:1)
- `B`: [追補 B 草案](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:1)
- `BP`: [追補 B 承認パッケージ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-09_t139-addendum-b/package.md:1)
- `R`: [roadmap](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/docs/roadmap.md:228)
- `E`: [addendum_envelope.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/orchestrator/preregistration/addendum_envelope.py:13)
- `T`: [binding tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/orchestrator/tests/test_t139_preregistration_binding.py:35)

## 1. 起草対象と新 core の骨格

予定する草案 path は次です。まだ存在しないため、下の行番号は起草時の割当て目安です。

`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/preregistration-draft.md`

| 予定行 | 新節 | 書き方 | 内容 |
|---:|---|---|---|
| 1–10 | metadata | 新規 | `authority: none`、公表専用 study。現 study の `pilot_admission` / `main_admission` を置かない。 |
| 11–52 | §0 位置づけ・凍結 | 新規 | 別 study、片方向の source binding、自己 digest 禁止、現 core を supersede しないこと。 |
| 53–69 | §1 公表上の問い | 新規＋参照 | 科学的問いは `C:45–50` を参照し、個別成分の公表であって primary の再判定ではないと書く。 |
| 70–115 | §2 入力と family | 新規＋参照 | 検証済み `Y_j` だけを入力にし、6 成分の固定順を定める。arm・workload・測定を再定義しない。 |
| 116–158 | §3 未調整 p 値 | 新規 | 仮説、`T_k`、片側 t p 値、自由度、非計算時の扱い。 |
| 159–205 | §4 多重調整 | 新規 | Holm の厳密な並べ替え、調整済み p 値、tie-break、棄却規則。 |
| 206–258 | §5 同時下限 | 新規 | Bonferroni 片側同時下限、Holm との非整合、`C_w(q)` を流用しない理由。 |
| 259–315 | §6 固定公表表・guard | 新規＋参照 | 6 行固定表、`qualification_status` 必須、`degradation_absent` の表示規則。 |
| 316–380 | §7 非正規性・stress check | 新規 | t の条件付き妥当性、事前固定診断、permutation を primary にしない理由。 |
| 381–425 | §8 公表系列台帳 | 新規 | primary と別台帳、同じ数値でも alias 禁止、新 core の fold と family root を区別。 |
| 426–475 | §9 追補の閉集合 | 新規 | `{p01,p02,p03}` だけ。公表手続き自体は追補へ送らない。 |
| 476–525 | §10 時点独立性・片方向性 | 新規 | source pilot 前の凍結、source admission を狭めない、結果の primary への逆流禁止。 |
| 526–555 | §11 主張しないこと | 新規 | 分布自由な保証、機序、新しい primary 判定、投入解禁を主張しない。 |

### 現 core 18 節の扱い

| 現 core | 行 | 新 core での扱い |
|---|---:|---|
| §0 位置づけ・凍結 | `C:11–44` | **文章は継承しない。** 別 study 固有の freeze/binding を新 §0 に書く。commit/path/blob 方式だけを設計原則として用いる。 |
| §1 問い | `C:45–50` | **参照のみ。** 科学的問いを再定義しない。 |
| §2 arm/workload | `C:51–61` | **参照のみ。** 名前・bytes・workload を複製しない。 |
| §3 量の定義 | `C:62–94` | **定義は参照。** 新 core は6成分の family と帰無仮説だけを書く。 |
| §4 primary 受理条件 | `C:95–125` | **参照のみ。** primary を所有しない。公表下限は新 §5 に別目的で書く。 |
| §5 状態閉表 | `C:126–170` | **表を複製しない。** source validator が出した `qualification_status` を新 §6 が参照する。 |
| §6 標本数 | `C:171–197` | **参照のみ。** source study が選んだ `J` を入力とする。 |
| §7 paired cluster | `C:198–222` | **参照のみ。** 新 study は raw run から cluster を再構成しない。weak mean null だけ明示的に参照する。 |
| §8 時間・待機 | `C:223–236` | **持たない。** 測定 protocol を所有しない。 |
| §9 欠測・失敗 | `C:237–245` | **参照のみ。** 新しい失敗分類を作らず、救済もしない。 |
| §10 台帳 | `C:246–257` | primary 部分は参照。公表台帳だけを新 §8 に書く。 |
| §11 費用 | `C:258–277` | **持たない。** 新規測定・割当てを要求しない。 |
| §12 raw receipt | `C:278–298` | **参照のみ。** schema を増やさない。新 core は検証済み source 出力を読む。 |
| §13 否定検査 | `C:299–310` | **持たない。** 本 wave は実装面ゼロ。文書上の禁止は新 §§0,10 に書く。 |
| §14 追補閉集合 | `C:311–365` | **新しく書く。** `p01`〜`p03` だけを持ち、`a` / `b` 文書を接続しない。 |
| §15 投入 gate | `C:366–437` | **持たない。** source pilot/main admission を変更しない。新 §10 は公表 study の時点有効性だけを定める。 |
| §16 本走後 | `C:438–443` | **新 §§3–6 で具体化。** ここだけが現 core の未確定部分を新規に正本化する。 |
| §17 非主張 | `C:444–450` | 新 §11として公表 study 固有の限界を書く。 |

## 2. 未調整 p 値

### 検証結果

P2 の統計量は採用できます。

- `A:686–694` が `T_k = √J·μ̂_k/s_k` と6成分を既に逐語定義しています。
- `A:695–699` は `a11` の受理条件が `∩_{k=1}^6 {T_k>q}` と一致すると明記しています。
- したがって新しい統計量は発明しません。ただし `a10` では標本数設計のために導入されたため、**公表 p 値として使う規範的意味**は新 core が書く必要があります。`B:132–138` もこの区別を明記しています。
- `q` は primary の `α₁` から来る一方、公表 Holm は別の `α_pub` を使うので、primary pass と公表棄却は同一ではありません（`A:680–683, 916–917`、`B:140–142`）。

### 逐語案

```text
公表 family は、固定順
(N_W1, H_W1, G_W1, N_W2, H_W2, G_W2)
の 6 成分とする。成分 k の母平均を μ_k とし、

    H0,k : μ_k ≤ 0
    H1,k : μ_k > 0

を検定する。

source study が権威あるものとして確定した J 個の適格 cluster について、
標本平均を μ̂_k、不偏標本共分散（分母 J−1）の対角平方根を s_k とし、

    T_k = √J · μ̂_k / s_k
    p_k^unadj = 1 − F_t,J−1(T_k)

とする。F_t,J−1 は自由度 J−1 の中心 t 分布の累積分布関数である。
p 値は片側であり、cluster 内反復を標本数または自由度へ加えない。

この T_k は source study の a10 が定めた T_k と同一であり、新しい統計量ではない。
ただし公表用 p 値の意味と帰無仮説は本 core が新たに固定する。

source study が既存の失敗分類または判定不能により権威ある Y_j と J を
確定できない場合、本 study は対角成分だけを用いて計算を救済しない。
```

最後の禁止は重要です。`a11` は共分散が正定値でなければ計算せず既存の判定不能へ写します（`A:817–819`）。公表側が対角分散だけで計算すると、その fail-closed を迂回します。

## 3. 多重調整

### Holm と closed testing の違い

P3 の「Holm は closed testing の shortcut で、closed testing より検出力で劣らない」は正しくありません。

- Holm は、各 intersection hypothesis に Bonferroni 局所検定を置いた closure の逐次 shortcut と解釈できます。
- 一般の closed testing は、相関を利用する有効な局所検定があれば Holm より強くできます。Holm 自身の原論文も、モデル固有の closed test が Holm より強い例を述べています。[Holm (1979)](https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf)
- `G=D−N` ですが、family に `D` は含まれません。さらに `(N,H,G)` は `(S,D_g,X)` の可逆な線形変換で、行列式は `κ=0.20` です（`A:755–764`）。したがって6帰無仮説の真偽構成に、直ちに使える論理的排他制約はありません。
- 構造的相関はありますが、それだけでは intersection test は定まりません。相関推定型 maxT、Hotelling、Simes 等を採れば追加の分布仮定・較正規則が必要です。小標本・非正規性が既知の攻撃面なので、ここで追加する根拠がありません。

よって **Holm を推奨**します。任意の依存に耐え、必要なのは各 marginal p 値の妥当性だけです。BH は Q7 により不採用です（`S1:10`）。

### 逐語案

```text
6 個の未調整 p 値を非減少順に

    p_(1) ≤ p_(2) ≤ ... ≤ p_(6)

と並べる。同値の場合の tie-break は family の固定順
(N_W1, H_W1, G_W1, N_W2, H_W2, G_W2) とする。

Holm 調整済み p 値は

    p_(i)^Holm
      = min{ 1, max_{1≤j≤i} [(7−j) · p_(j)^unadj] }

とし、元の成分順へ戻して公表する。
成分 k の棄却は p_k^Holm < α_pub とする。等号は棄却しない。
数値の表示丸めは棄却判定の入力にしない。

本手続きは Bonferroni 局所検定の closure に対応する Holm 手続きである。
相関推定型の別の closed testing、Simes、BH、FDR 手続きへ実行時に
切り替えてはならない。
```

## 4. 同時区間

### 非整合の具体例

`J=13`、自由度12、`α_pub=0.025`、各成分の `s_k=1` とします。未調整 p 値を

```text
(0.0020, 0.0045, 0.20, 0.30, 0.40, 0.50)
```

とすると、Holm の最初の2閾値は

```text
0.025/6 = 0.0041666667
0.025/5 = 0.005
```

なので最初の2成分を棄却します。調整済み p 値はそれぞれ `0.0120` と `0.0225` です。

一方、Bonferroni の片側臨界値は

```text
t_{12, 1−0.025/6} = 3.152681312170
```

です。第2成分では

```text
T_2       = 3.111245194702
μ̂_2      = T_2 / √13 = 0.862904160003
L_2^Bonf  = μ̂_2 − 3.152681312170/√13
          = −0.011492311245
```

となります。したがって **Holm では棄却されるが、Bonferroni 同時区間 `[L_2^Bonf,∞)` は 0 を含む**ことが実際に起こります。

この例は実現可能です。`A:755–764` の変換が可逆なので、該当する平均と正定値共分散を持つ `(N,H,G)` 標本を構成できます。

### 選択肢の評価

- **(a) 非整合を明記して両方出す — 推奨。** Holm は決定列、Bonferroni 下限は同時不確実性列として役割を分けます。
- **(b) closed-testing 互換区間。** 原理上は可能ですが、全ての shifted intersection null の局所検定と inversion が必要です。互換領域は一般に非矩形になり、成分ごとの投影下限が情報を失うこともあります。[Magirr et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC4806862/) 現 core にこの構成はありません。
- **(c) 区間だけ別水準。** Holm の閾値は順位ごとに変わるため、単一の別水準では整合しません。さらに検定と区間で別の familywise budget を持つことになり、推奨しません。

### 逐語案

```text
公表する成分 k の片側同時下限を

    c_B = F_t,J−1^−1(1 − α_pub/6)
    L_k^Bonf = μ̂_k − c_B · s_k/√J
    I_k^Bonf = [L_k^Bonf, ∞)

とする。6 成分の marginal t 手続きが妥当であるという条件の下で、
Bonferroni union bound により

    P(∀k: μ_k ∈ I_k^Bonf) ≥ 1 − α_pub

である。成分間の独立性は仮定しない。

有意セルの決定は Holm 列だけから行う。
I_k^Bonf が 0 を含むかどうかは Holm の棄却集合を再定義しない。
Holm が棄却しても I_k^Bonf が 0 を含む場合があり、これは矛盾または
データ破損ではなく、異なる familywise 手続きの結果である。
```

### `C_w(q)` を流用しない理由

`a11` の `C_w(q)` は workload ごとに `(N,D)` の Hotelling 領域と `H` の片側領域を束ねます（`A:766–805`）。primary は intersection-union なので W1/W2 に `α/2` を配りません（`A:821–823`）。

しかし公表側で6下限を同時被覆するなら、同じ `q(J,α_pub)` を両 workload に使った場合の全体被覆は union bound 上 `1−2α_pub` にしかなりません。流用するなら少なくとも

```text
q_publication = q(J, α_pub/2)
```

とする必要があり、primary と同じ `q` ではありません。しかもこれは Holm と互換にならず、2次元正規性まで要求します。したがって、流用可能ではあるものの採る利点がなく、単純な marginal Bonferroni 下限を推奨します。

## 5. 正分母 guard の逐語案

```text
公表表は固定順
(N_W1, H_W1, G_W1, N_W2, H_W2, G_W2)
の exactly 6 行を持つ。primary の成否または各行の有意性により
行を省略してはならない。

各行は少なくとも workload、component、estimate、p_unadjusted、
p_holm、holm_reject、simultaneous_lower_bound、RF_point、
RF_confidence_set、interval_shape、qualification_status を必須欄として持つ。

qualification_status は、公表用 p 値または公表用同時下限から再計算しない。
source study の validator が、source study の q と core §5 の first-match 表から
確定した同一 workload の値を、当該 workload の 3 行すべてへ逐語で複写する。
producer または renderer の自己申告値を用いてはならない。

qualification_status が partial_recovery でない行について、
RF の数値または区間を「回復率が認証された」と解釈してはならない。
個別成分が Holm で棄却されても、この禁止は変わらない。

qualification_status = degradation_absent の場合も RF_point と
RF_confidence_set は固定表から隠さない。ただし必ず
「分母 D̄ は負であり、この RF は分子・分母がともに負になりうる形式上の比である。
(0,1) に入っても回復を意味しない」
と併記し、回復・浅い劣化・partial recovery の根拠に使用しない。
```

これは `C:141–166`、特に `degradation_absent` の符号の偶然を説明する `C:161–166` を参照するだけで、状態表を再定義しません。RF の source Fieller 区間も新 core で作り直しません。

## 6. 新 core の追補閉集合

exact-key は **`{p01,p02,p03}`** だけを推奨します。

| field | 内容 | core で決めない理由 | 推奨値 |
|---|---|---|---|
| `p01` | 公表系列の候補数上限と許容 ordinal | 統計量から導けない資源・governance 裁定であり、B1 が未裁定 | `candidate_cap=1`、ordinal `{1}`、失敗時も解放しない |
| `p02` | 公表系列の累積 spending 数値 | familywise budget の配分はユーザー裁定であり、B2 が未裁定 | `0.05/[k(k+1)]`、今回 `k=1, α_pub=0.025`、tail 再配分なし |
| `p03` | canonical publication root、ordinal、予約規則 | trust root は文書起草者が自己宣言して確定できず、canonical 裁定を要する | `(fold_commit=88d68f91…, ledger_kind=individual_publication)`、ordinal 1、create-only |

次は **core 本文で決める**ため、追補へ送ってはいけません。

- 6セルの identity と順序
- 仮説、`T_k`、未調整 p 値
- Holm の式と tie-break
- Bonferroni 同時下限
- `qualification_status` guard
- 非正規性の stress check
- source data の選択規則
- pre-pilot の時点条件

`T139_EXACT_FIELDS` は `a01`〜`a13` だけです（`E:13–29`）。既存の approved-A 検査もその集合へ固定されています（`E:152–186`、`T:323–330,467–489`）。したがって `pNN` を既存 A envelope に混ぜると余剰です。新追補は既存 A/B の文書を composition せず、新 core の三つ組へだけ従属します。

## 7. 凍結時点

新 core とその `p01`〜`p03` 追補は、**source study の本走より前では足りず、source pilot 1 本目の投入より前**に承認・commit・fold 済みでなければなりません。

理由は、pilot が本走 `J` と分散構造を明らかにするためです。pilot 後に Holm/closed testing、区間、`α_pub` を選べれば結果依存になります。B6 も同じ問題を指摘しています（`BP:168–179`）。

時系列は次です。

```text
草案 authority:none
→ ユーザー裁定
→ 新 core の canonical commit
→ 新 core に束縛した p 追補の canonical commit
→ source pilot 1 本目
→ source main
→ 公表 study の解析
```

この条件は、現 core の `pilot_admission: requires_addendum_a` を変更しません（`C:3–9`）。

- 新 core は「自分が事前登録として有効であるための時点条件」を書くだけです。
- `submit_pilot` に新 core を追加必須とする案は出しません。それを行えば現 admission を狭めます。
- 新 core が間に合わず pilot が走った場合、source study 自体の admission を遡って失敗扱いにはせず、**公表 study を事前登録済みとは扱えない**だけです。
- 現在は B8 により pilot/main とも不可なので、実際の投入前にこの順序を満たす余地があります（`S1:8–9,31`）。

新 core 本文には自己 digest を書きません。新追補は新 core の path/commit/blob digest を持てますが、新追補自身の digest は書きません。

## 8. study 同一性と閉集合迂回

### (i) roadmap の限定例外

roadmap は例外を `[T-139] RF 3-arm paired cluster study` に限定し、他 study へ自動一般化しないとしています（`R:228–240`）。また preregistration path として現 core を名指ししています（`R:232–233`）。

したがって新 core は次の境界を守る必要があります。

- 入力は、現 study の validator が既に確定した完全な `Y_j` 列と `J`。
- raw run から cluster、pairing、arm contrast、適格性を再構成しない。
- source receipt の core ref は引き続き現 coreであり、新 coreへ差し替えない。
- 新 study は paired-design 例外を再行使せず、例外下で生成済みの検証済み出力を下流解析するだけ。

この限定なら例外の拡張ではないと解釈できます。ただし roadmap の「他の study へ一般化しない」が下流再解析まで禁止する読みも残るため、承認時のユーザー裁定には次を明記すべきです。

> 検証済み cluster-level `Y_j` の事前登録済み下流解析は、新たな paired measurement または例外の一般化ではない。

この明示が得られず、新 core が raw から contrast を再生成するなら roadmap に抵触します。

### (ii) 公表系列台帳の根

新 core の fold commit を新しい family root にすると、同じ T-139 候補が新しい `k=1` と `α_pub` を取り直せるため不可です。

推奨する根は B 草案の値を独立に再採用した

```text
(fold_commit = 88d68f9127b31df5aafc3d59607896626a1652e8,
 ledger_kind = individual_publication)
```

です（`B:148–179`）。新 core の freeze commit/path/blob はこの root とは別の「分析文書 identity」です。

primary 側も fold commit `88d68f91…` を使いますが（`A:919–930`）、`ledger_kind`、balance、entry、ordinal は共有しません。同じ数値 `0.025` でも alias しません。

### (iii) 現 core §14 の抜け穴を閉じる条件

新 core は次を全て満たす場合にだけ正当な別 study です。

1. source pilot 前に凍結する。
2. source dataset は全適格 main clusters に一意固定し、cluster/cell の選択を許さない。
3. 現 primary、`P_W1∧P_W2`、`q`、first-match 状態、失敗分類を一切変更しない。
4. 公表結果を source primary へ逆流させない。
5. 変更版の公表 core を結果後に作る場合、既存結果を置換せず同じ公表 root の次 ordinal と spending を消費する。
6. p addendum の閉集合外で推論手続きを変更できない。
7. 新 core は現 core の erratum/addendum として compose されない。

これにより「別 core を起こせば §14 の外を自由に変えられる」という抜け道を、時点・dataset・ledger の三面で閉じます。

### source main の addendum B 問題

ここは real blocker です。

- 現 core は本走に A+B を要求します（`C:7–8,414–416`）。
- 現 resolver 契約では addendum は従属先 core の三つ組と一致しなければなりません（`C:402–407`）。
- 新 core に束縛した `p01`〜`p03` 追補は、現 core の B にはなりません。
- したがって新 coreと新追補だけでは、同じデータを生む source main を投入できません。

推奨する解決は、将来の同一裁定・同一 land 境界で次の二つを別々に成立させることです。

1. 現 B を、現 core にだけ従属する source-study addendum B として発効させる。
2. 同じ値を独立に再記述した `p01`〜`p03` 追補を、新 core に従属させる。

新 study は現 B 文書を参照せず、値だけが一致します。この二重束縛をユーザーが明示的に裁定しない限り、本走不可を維持すべきです。

## 9. 非正規性

`t`、Holm、Bonferroni のうち、Holm/Bonferroni は marginal p 値・区間が妥当なら依存に耐えます。しかし marginal t 自体は正規性に依存します。`A:958–965` と `B:217–221` がこの限界を認めています。

permutation/randomization への置換は推奨しません。

- primary は weak mean null です（`C:219–221`）。
- exact な Fisher randomization は、欠測 potential outcome を一意に補える sharp null に対するものです。
- studentized randomization は weak null に大標本で妥当になり得ますが、有限標本 exact ではありません。[Wu & Ding, JASA](https://par.nsf.gov/servlets/purl/10167780)
- `J≤13` ではその漸近保証に依存できません。
- arm の block 順は固定 seed から決定的に導出されます（`A:552–605`）。観測後の label permutation を実験の割当て分布とみなすこともできません。
- sign-flip は contrast 分布の対称性という、weak mean null より強い仮定を追加します。

したがって次を推奨します。

1. t ベース手続きは「cluster 代表値の正規 model に条件付き」と明記する。
2. `a12` と同型だが、公表 Holm の全臨界値を対象にした事前固定 stress check を置く。
3. stress check 通過を「任意の非正規分布に対する較正」と呼ばない。
4. 失敗しても source study の失敗分類を増やさず、FWER/同時被覆が制御されたという表示だけを禁止する。

### stress check の具体案

`A:843–856` の入力 path/hash と empirical residual の値を新 core に独立に再記述し、次を固定します。

```text
J = 4,...,13
k = 1,...,6
r = 1,...,6
u_r = α_pub/r
B = 1,000,000 datasets per (J,k)
δ_MC = 0.001
```

同じ `(J,k)` の B 個の p 値を6閾値へ同時評価し、

```text
x_Jkr = #{b : p_Jk,b^unadj < u_r}

U_Jkr = Beta^−1(
            1 − δ_MC/360;
            x_Jkr + 1,
            B − x_Jkr
         )
```

とします。`x=B` なら `U=1`。360 は `10×6×6` です。全ての `U_Jkr≤u_r` を確認します。`r=6` は Bonferroni 下限の偽除外も同時に検査します。

独立 seed の提案値は

```text
f0f433116d03c45ddb06f5c66efae4926a0f1ca5d8042915bb7a5656dc1c2f5a
```

で、preimage は末尾 newline なしの

```text
t139-publication-stress-v1|ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
```

です。新 core 自身の digest を使っていないため自己参照ではありません。

この check は固定 empirical support に対する診断にすぎません。通過しても混合分布反例を排除せず、失敗時も `design_not_feasible` 等の source 分類へ写してはいけません。

## 10. 親が決めてよいこと／ユーザーへ返すこと

### 親が決めてよいこと

- 上記12節の配置、見出し名、参照の書式。
- 6成分の固定順と tie-break。
- `p<閾値` の strict 比較、表示丸めを判定に使わない規則。
- 既裁定 R5 をそのまま射影した表 schema。
- stress check の独立 seed・counter domain・360セルの逐語化。
- 現 core/A/B の bytes を触らず、新文書だけを起草すること。
- 新 core の source binding を片方向にすること。

### ユーザーが決めるべきこと

| 論点 | 推奨 |
|---|---|
| Holm か、別の局所検定を定めた closed testing か | **Holm**。一般 closed testing を選ぶなら63 intersection の局所検定を別途完全指定する。 |
| 同時区間 (a)/(b)/(c) | **(a)** Holm と Bonferroni の非整合を明記して両方出す。 |
| `p01` 候補数上限 | **1** |
| `p02` spending | **`0.05/[k(k+1)]`、今回は0.025** |
| `p03` family root | **`(88d68f91…, individual_publication)` を維持**。新 core fold でリセットしない。 |
| 非正規性 | **t を model-based として採用し、stress check は診断に限定**。分布自由な有限標本保証が必須なら現設計では停止。 |
| roadmap の別 study 条項 | 検証済み `Y_j` の下流利用は例外拡張ではない、と明示裁定する。 |
| 現 B と新 p 追補の関係 | 現 B は source core 用、新 p 追補は新 core 用として別々に発効させる。文書接続はせず値だけ一致させる。 |
| 凍結時点 | 両文書を source pilot 前に凍結するが、現 `pilot_admission` の述語は変更しない。 |

## 11. 静的確認

- 現 core の SHA-256 は `ac939af4…60e9`、追補 A は `f7db96ce…cfec` で、作業木と pin commit の blob が一致しました。pin 実体は `T:35–50` です。
- `p01`〜`p19` の既存使用は指定範囲に見つかりませんでした。
- `git status --short` は空でした。
- ファイル変更は行っていません。
- pytest、build、simulation は実走していません。したがって「テストが緑」とは主張しません。

## 総括

新 core は、現 study の検証済み6次元 cluster 代表値だけを入力とする公表専用の別 study とし、primary・状態表・失敗分類・測定 protocol は参照に留めます。未調整 p 値は既存 `T_k` の片側 t、調整は Holm、同時下限は非整合を明記した Bonferroni を推奨します。追補は `p01`〜`p03` だけに閉じ、core と追補を source pilot 前に凍結します。

ただし、新 core の追補は現 core の addendum B を代替できません。現 B を source study 用、新 p 追補を publication study 用として別々に成立させる裁定がない限り、本走不可を維持する必要があります。