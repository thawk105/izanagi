判定は **NO-GO**。blocker は **6 件**。追補 A はこのまま凍結できない。

### 所見 1 — LFC は凍結 core の「共同信頼集合上の最悪検出力」を満たさない

区分: blocker

根拠: [core:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:183) は `J` を `Θ` 上の最悪検出力で決めると凍結している。一方、[addendum-a.md:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:447) は `π_J(LFC)` が相関方向を覆わず、`Θ` 全体の下限ではないと明記する。D234 は追補による core の変更を禁じる。

反例または検算: `μ_k^-` の閉形式は正しいが、`Σ^+=(ν/ℓ)S_p` を「Loewner 最大」と呼んでも、証明されているのは `Σ→cΣ` のスカラー方向だけである。`V` は相関を変える共分散も含み、同時受理確率は相関で変わる。したがって「下限ではないと正直に書く」ことは、core の worst-case 要件を満たす代わりにならない。

成果物影響: `J` が真の worst-case より小さく選ばれ、本走の割当て数・primary の検出力・certified 選択の受理集合が変わりうる。

提案: `inf_{(μ,Σ)∈Θ}π_J(μ,Σ)` を外向き誤差つきで認証する手続きを固定するか、要件を一点 LFC へ弱める新 core とユーザー裁定を起こす。

### 所見 2 — `a10` は同じ pilot から同じ `J` を再現できない

区分: blocker

根拠: [addendum-a.md:415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:415)、[同:452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:452)、[同:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:464)。

反例または検算:

- Wishart 極値分位点 `ℓ,u` を Bartlett 生成で求めると読めるが、その反復数・専用 domain・分位点の外向き誤差規則がない。数学的な真の分位点と読む場合も数値アルゴリズムがない。
- counter stream の `domain` の逐語、digest から一様乱数への写像、正規・χ²生成、共分散平方根の規則がない。
- 形式規則は「採る `j` より小さい候補だけ `UB<.80`」だが、直後の prose は「全候補のどれか一つでも跨げば DNF」。例えば `J=4` の `UB<.80`、`J=5` の `LB≥.80`、`J=6` が `[.799,.801]` なら、前者は `J=5`、後者は DNF を返す。
- 各候補の CP 信頼水準をそのまま使っており、候補横断の Monte Carlo 誤差補正もない。

`LB_j≥.80` と小さい候補の `UB<.80` は別候補に対する条件なので、同じ走行から得ても両立可能であり、それ自体は矛盾ではない。

成果物影響: 同じ pilot raw から `J=5`、別の `J`、または `design_not_feasible` が分岐し、本走本数と受理集合が変わる。

提案: Wishart 用反復数・全 domain tag・bit-to-random 写像・外向き丸め・候補横断誤差配分を固定し、跨ぎ規則を一つに統一した reference transcript を凍結する。

### 所見 3 — 単調性補題の分散方向は `μ_k≥0` の条件を欠く

区分: minor

根拠: [addendum-a.md:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:442)。

反例または検算: 平均方向は正しい。同じ残差を使って第 `k` 成分へ定数を加えると `S` は不変で、受理事象は点ごとに拡大する。独立性は不要である。分散方向は
\[
\mu_k/\sqrt c+Z_k-q\,s_k/\sqrt J>0
\]
なので、`μ_k>0` なら `c` とともに縮小するが、`μ_k<0` なら逆に拡大する。例えば一変量 `μ=-1` では `c=4` にすると非心度が 0 側へ動き、受理確率は増える。`d^-≥1` を先に通した現在の分岐では正値条件が成立するが、補題の逐語は planning model だけを条件にしており偽である。

成果物影響: 現行の `d^-` gate 後の値はこの符号穴だけでは変わらないが、レポートが補題を無条件保証として引用すると誤る。

提案: `min_k μ_k≥0` を明記し、スカラー拡大だけの補題と Loewner・相関方向を明確に分離する。

### 所見 4 — `a12` の呼び替えは core の「較正」義務を消していない

区分: blocker

根拠: [core:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:219) は weak-null 型 I 誤りを simulation で較正すると固定する。[addendum-a.md:550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:550) は見出しに「較正」を残しつつ、本文では真の cluster-level 誤りを較正しないと認める。D234 は追補による core の意味変更を禁じる。

反例または検算: `P(U=a)=.99, P(U=-99a)=.01` の未観測 cluster 効果は平均 0 だが、13 cluster がすべて正側になる確率は `.99^13≈.878` である。J=1 residual だけの DGM はこれを排除できない。`pass ⇔ 全60セルでU_{Jk}≤α₁` という機械条件自体は一意だが、その意味は選んだ empirical DGM に対する `1−δ_MC` の上側信頼主張であり、真の weak-null 較正ではない。

成果物影響: stress check 通過を core 所定の較正完了として扱うと、未制御の型 I 誤りで main admission と certified pass が可能になる。

提案: core の義務を stress check へ変える明示 erratum／新 core、または独立 cluster データを用いた事前固定の較正設計が必要。R2(a) の呼び替えだけでは閉じない。

### 所見 5 — `a13` は root を名指しただけで ordinal の一意性を強制しない

区分: blocker

根拠: [addendum-a.md:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:637) は root `F` と `k=1` を宣言するが、[record-items.md:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/record-items.md:35) の schema に canonical ledger path、予約 ID、予約時 digest、ordinal の authority がない。[同:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/record-items.md:166) も transcript pointer しか要求しない。

反例または検算: 3 個の `study_id`／receipt がそれぞれ同じ `F` と `k=1` を記録しても、現在の resolver 契約には create-only 台帳の重複を拒否する入力がない。各真の帰無が独立なら
\[
1-(1-.025)^3=0.07314>0.05.
\]
「新しい parent ID ではリセットできない」という prose は外部権威を作らない。

成果物影響: 複数 study がすべて `α=.025` と小さい `q` を使え、系列全体の false certification 率が `.05` を超える。

提案: pilot 前に、caller 非選択の canonical ledger へ `(family_root, ordinal)` を原子的に予約し、その path・entry digest・reservation commit を binding と receipt に必須化する。

### 所見 6 — A8 の primary 反例は成立しないが、偽の同値を残す理由にはならない

区分: major

根拠: [core:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:109)、[core:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:145)、[package.md:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/package.md:154)。

反例または検算: 要求された配置は存在しない。`degradation_absent` が発火せず、先行状態も発火しないなら `A>0` かつ `D̄>0` であり、楕円全体で `D>0`。ratio projection が `(0,1)` に含まれれば各点で `0<N<D`、よって compactness から `inf N>0` かつ `inf G>0` となる。負分母反例は必ず `D̄<0` なので順2に吸収される。したがって親の「primary exploit はない」は正しい。ただし無条件の同値そのものは負分母枝で偽であり、公表用説明には残る。

成果物影響: certified 選択は変わらないが、材料レポート／proof chain が負分母枝でも偽の Fieller 同値を保証として記載しうる。

提案: 正分母条件を付した狭い erratum または forward correction を置き、公開表にも分母符号を必須表示する。R5(a) の「実害なし」は推奨理由として不足する。

### 所見 7 — erratum の「受理集合は狭い側」は逆である

区分: blocker

根拠: [erratum-core-s15.md:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md:35)、[同:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md:70)、[package.md:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/package.md:46)。

反例または検算: literal core は §14 で exact 13、§15 で exact 12 を同時要求するため、受理される追補は空集合である。erratum 後は exact 13 の追補が受理されるので、受理集合は `∅` から非空へ**拡大**する。「新たに受理するものはない」は偽である。なお key 集合としては `{a01..a12}⊂{a01..a13}` であり、「集合自体が互いに素」でもない。互いに素なのは exact equality を満たす文書クラスである。

成果物影響: resolver が新たに exact-13 追補を admission する変更なのに、台帳とユーザー裁定へ「狭化」と誤記される。

提案: 「literal gate の矛盾を解消して空集合を非空化する受理拡大」と明記し、その変更を明示承認対象にする。

### 所見 8 — `record-items.md` は closed schema を名乗れるだけの閉包を持たない

区分: blocker

根拠: [record-items.md:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/record-items.md:33) は全 nested object に `additionalProperties:false` を課すが、[同:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/record-items.md:152) 以下は追加 field の断片だけである。

反例または検算: `allocations[]`、`liveness[]`、`admission_telemetry[]`、`attempts[]` の全 exact key・必須性・型が列挙されていない。例えば `allocations[].exclusivity` は否定検査で参照されるが schema 定義がない。二つの実装が未知 field の扱い、null、attempt 参照を異ならせても本文に適合できる。

成果物影響: 同じ receipt が validator A では適格、validator B では未知 field／欠落として拒否され、cluster 集合と certified 判定が変わる。

提案: pilot 前に完全な機械可読 schema と cross-field 制約を発行し、その blob digest を `PreregBinding` へ固定する。

### 所見 9 — 非保証リストは model 条件と Monte Carlo 誤判定を漏らしている

区分: major

根拠: [addendum-a.md:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:406) は iid 正規を planning model とする一方、[同:515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:515) は被覆を無限定に記し、末尾 [同:653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:653) と [README.md:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/README.md:58) に model 条件がない。

反例または検算: Hotelling と t の有限標本分布は iid 多変量正規に依存し、非正規 cluster では `1−α_k` 被覆を保証しない。また `a12` の CP gate は `δ_MC=.001` の確率で誤った上側認証をしうる。「pass」は数学的確定証明ではない。

成果物影響: レポートが model 条件・Monte Carlo error を落とすと、保証していない被覆率と型 I 誤り制御を保証済みとして公表する。

提案: 末尾と README に「有限標本保証は iid 正規モデル条件付き」「MC pass は familywise `1−δ_MC` の主張」「Wishart 数値誤差は未認証」を追加し、consumer 文言にも固定する。

### 所見 10 — R1〜R5 の選択肢は網羅的でなく、推奨も理由から導けない

区分: major

根拠: [package.md:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/package.md:34) 以下。

反例または検算:

| 問 | 落ちている選択肢／推奨の穴 |
|---|---|
| R1 | erratum ref を resolver の明示引数にする案と、trusted registry から暗黙解決する案が区別されていない。推奨理由の「狭化」は所見7のとおり偽 |
| R2 | 独立 cluster データを先に集める案、または core の simulation 義務を明示 supersede する案がない。呼び替えだけでは core と不整合 |
| R3 | caller 非選択の global ledger で ordinal を原子的予約する案がない。`a13` への移動だけでは所見5を閉じない |
| R4 | probe の本数・threshold 導出写像を先に凍結する案と、study を中止する案がない。「測ってから閾値を確定」は裁量を残す |
| R5 | core を触らず report/consumer に正分母 guard を課す案がない。「primary 無害」から「偽の文言を残す」は導けない |

成果物影響: ユーザーが推奨案を選んでも blocker が残り、承認済みと記録された追補・台帳・レポートの受理集合または保証文言が未確定のままになる。

提案: 上記の選択肢を追加し、所見1・4・5・7を閉じた後に推奨を再計算する。

## 総括

- blocker: **6 件**
- 判定: **NO-GO**
- 段3レンズAの5 blocker再判定:
  - A3: **closed**。`E=\hat v+(q/\sqrt J)S^{1/2}B` が存在し、全方向の支持関数は閉凸集合を一意に定める。特異 `S` でも成立する。
  - A4: **open**。LFC の core 不整合と数値再現性の二重 blocker。
  - A5: **open**。pass 条件は一意だが、意味は stress check であり core 所定の較正ではない。
  - A6: **open**。root の時期は前倒しされたが、ordinal の外部権威がない。
  - A8: **primary exploit は refuted**。ただし偽の同値を公表文言へ残す major は未解消。
- `q` の union bound は正しい。Hotelling 第1項の自由度・定数は `p=2` の標準式、t 項は `J−1` が正しい。`J=4…13` では左辺が `q=0` で `1.5`、`q→∞` で `0` へ連続減少するため、`α₁=.025` の根は全候補で存在する。
- workload IUT も model 条件付きでは正しい。各 workload の false-pass がその `C_w` の非被覆事象に含まれ、global pass は null workload の false-pass の部分集合なので `α/2` は不要。系列横断だけが root/ordinal blocker で破れる。
- ユーザー裁定が必要なのは、(1) full-`Θ` worst-case を復活させるか新 core にするか、(2) `a12` の core 義務、(3) canonical alpha ledger、(4) erratum の実際の受理拡大と束縛方式、(5) 完全な receipt schema、(6) Fieller 文言の訂正方式。
- テスト・build・power simulation は実行しておらず、緑は主張しない。