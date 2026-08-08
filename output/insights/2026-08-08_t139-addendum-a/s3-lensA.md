### 所見 1 — pilot 前に固定できるのは scalar `q` ではなく写像 `J↦q(J)`

区分: minor

根拠: [`s2-plan.md:381`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:381) は各 `J` に対する最小根を一意に定義し、[`s2-plan.md:321`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:321) は pilot から `J` を選ぶ。ところが brief は scalar `q` を「完全に固定」と表現する（[`s1-brief.md:35`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s1-brief.md:35)）。

反例または検算: 固定された `α₁=0.025` では根は各 `J` で一意かつ有限で、静的計算では `q(4)≈10.99955`、`q(13)≈3.449997`。pilot が本走へ非 pool なら、pilot に条件付けた時点で `J` と `q(J)` は固定されるため、この適応自体は型 I 誤りを増やさない。`a12` も pass/fail だけで `q` を変更しない。したがって `J` 依存そのものは反証できない。ただし、実際の数値 `q` は pilot 後に確定する。

提案: 「pilot 前に `q` の全候補写像を固定」と書き換え、`J=4,…,13` の上向き丸め済み lookup table とその生成規則を追補 A に置く。alpha の根が固定されていない別の穴は所見 6。

### 所見 2 — IUT と次元 `p` は正しい

区分: minor

根拠: primary は workload 内・workload 間とも連言である（[`preregistration.md:97`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:97)、[`s2-plan.md:410`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:410)）。

反例または検算: 元の平均を `(S,D_g,X)` とすると、

\[
(N,H,G)^\top=
\begin{pmatrix}
0&-1&1\\
0.8&-1&0\\
1&0&-1
\end{pmatrix}
(S,D_g,X)^\top ,
\qquad \det=0.2=\kappa .
\]

したがって `N,H,G` は同じ三次元平均の独立な線形汎関数で、親 P2 の `p=3` は正しい。採用案は `(N,D)` に `p=2`、`H` に一次元 t、pilot の W1/W2 共同集合に `p=6` を使っており、次元の混同はない。

また、`H0,w={N≤0}∪{H≤0}∪{G≤0}`。global null は `H0,W1∪H0,W2` なので、global pass は少なくとも一つの null workload の false-pass の部分集合である。各 workload の size が `α_k` 以下なら全体も `α_k` 以下であり、W1/W2 の `α/2` 補正は不要。

提案: determinant と IUT の包含証明を追補へ明記する。これは blocker ではない。

### 所見 3 — 自由度は閉じているが、特異共分散で `C_w` と状態表が未定義になる

区分: blocker

根拠: 採用案は `S_ND^{-1}` を直接使う（[`s2-plan.md:355`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:355)）一方、pseudoinverse を禁止するだけで失敗時の写像を定めていない（[`s2-plan.md:408`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:408)）。core は状態表が全状態を尽くすとする（[`preregistration.md:126`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:126)）。

反例または検算: `J=4` で `N=(100,101,102,103)`、`D=2N` なら `S_ND` は rank 1 で逆行列がない。平均を十分大きくすれば `A>0` にできるため、`A≤0` の吸収枝にも入らない。ridge、pseudoinverse、一次元縮約、即失格のどれを選ぶかで結果が変わり、結果を見た後の裁量になる。

一方、自由度そのものには穴がない。採用案は `p=2,J≥4` なので `J-p≥2`、親 P2 でも `p=3,J=4` の `J-p=1`、pilot は `n_p-p=8-6=2`。`J_max=13` まで `q` は有限で、上限側の発散もない。

提案: `S_ND` の有限性・対称性・正定値性を事前条件にし、不成立時の唯一の fail-closed 状態を固定する。core の `invalid_representation` への写像で済むか、閉表の変更になるかはユーザー裁定が要る。

### 所見 4 — `a10` は数学的集合を定めても、同じ pilot から同じ `J` を再現できない

区分: blocker

根拠: `Θ` と真の `L_J` は定義されているが、数値手続きは「compact parameterize」「lexicographic branch-and-bound」「gap ≤ 1e-3」までしかない（[`s2-plan.md:250`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:250)、[`s2-plan.md:313`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:313)）。`d^-` の最適化には数値規則すらない。

反例または検算: ある候補で certified bracket が `[0.7996,0.8005]`、gap `0.0009` なら、一人は規定 gap 到達として「下側から証明不能、不適格」にできる。別の人はさらに分割して lower bound `0.80005` を得て適格にできる。双方が現行文面を満たし、異なる `J` を返す。さらに、小さい `J` が未解決のまま大きい `J` を選ぶ規則は、式の `min{J:L_J≥.80}` と一致しない。離散的な単調性を仮定してよいとも書かれていない。

共同集合の保証自体は正しい。平均 97.5% と共分散 97.5% を Bonferroni で束ねれば共同被覆は少なくとも95%、同じ `Θ` を全 `J` に使うので候補ごとの補正も不要。`d=1` も「1 未満へ引き下げない floor」と読む限り D229 と整合する（[`decisions.md:10742`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/docs/decisions.md:10742)）。

提案: quantile 定義、演算精度、外向き丸め、分岐順、bound 式、停止順を固定した reference implementation と hash を pilot 前に束縛する。選択には「選んだ `J` の lower≥.80」に加え、全ての小さい `J` の upper<.80 を要求し、閾値を跨ぐ候補が一つでもあれば `design_not_feasible` とする。docs-only scope でこれを閉じられないなら brief の scope 自体を改める。

### 所見 5 — `a12` は cluster-level 型 I 誤りの較正ではない

区分: blocker

根拠: raw は一つの allocation における 2 workload × 3 arm × 5 rep の30行だけ（[`README.md:39`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-05_t139-alt-x-probe/README.md:39)、[`throughput.tsv:1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/throughput.tsv:1)）。core 自身も allocation 間変動は一点も推定されていないと明記する（[`preregistration.md:448`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:448)）。プランも 5/6 permutation・無待機であることを認める（[`s2-plan.md:433`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:433)）。

反例または検算: J=1 residual と同じ cluster 内残差に、未観測の cluster 効果

\[
P(U=a)=0.99,\qquad P(U=-99a)=0.01
\]

を加えると `E[U]=0` で weak mean null を満たす。微小な連続 jitter を足せば共分散も正定値にできる。それでも `J≤13` の全 cluster が正側になる確率は少なくとも `0.99^{13}≈0.878` で、有限の `q` に対する片側 lower bound は高確率で正になる。J=1 データからこの cluster 効果は識別できない。

較正判定は恒真でも恒偽でもない。`x=0` なら CP 上限は約 `1.1×10^-5<.025` で通り、`x=B` なら `U=1` で落ちる。しかし、通過が証明するのは選んだ empirical stress DGM だけで、実際の cluster-level weak-null error ではない。

提案: 多変量正規モデルを推論仮定として明示し `a12` を「感度 stress check」と呼ぶか、cluster 効果を含む事前固定分布族に対する worst-case 保証へ変更する。core の「較正」と意味が変わるためユーザー裁定が要る。pilot raw による再較正は認めない。

### 所見 6 — `a13` の級数は正しいが、pilot 後の `b03` が alpha root のリセット経路を残す

区分: blocker

根拠: A は根を同定せず「本 study は `k=1`」と自己宣言し、B が後で root と台帳を同定する（[`s2-plan.md:502`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:502)、[`s2-plan.md:527`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:527)）。core でも root の同定は `b03` に置かれ、B は pilot 後まで凍結不要である（[`preregistration.md:248`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:248)、[`preregistration.md:343`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:343)）。現 `record-items` に root、ordinal reservation、ledger digest もない（[`record-items.md:22`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-producer-adjudication/record-items.md:22)）。

反例または検算:

\[
\sum_{k\ge1}\frac{0.05}{k(k+1)}=0.05,\qquad \alpha_1=0.025
\]

は正しい。`b01` の cap に tail を戻さず、`b02` を別 family に置く限り干渉もしない。しかし、root を三つ自己申告して各 study を `k=1` にすれば、独立な三つの真の帰無で全体誤り率は

\[
1-(1-0.025)^3\approx0.0731>0.05
\]

になる。「B が再現できなければ拒否」は、B 自身の root 選択が pilot 後なら防壁にならない。

提案: 最初の pilot 前に canonical family root、domain tag、既存 ledger digest、create-only の ordinal reservation を権威台帳へ固定し、失敗・中断も保持する。`b03` を含む B 全体を pilot 前に凍結するか、root binding を A の `a13` に移す必要がある。現 core の A/B 分割に触れるためユーザー裁定が要る。

### 所見 7 — P1 の36 run が正しく、現 `record-items.md` の6件が誤り

区分: major

根拠: core は「3 arm の全6順列を各1回」とする（[`preregistration.md:198`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:198)）。一方、現 schema は `planned_execution.runs[]` を1割当て6件とする（[`record-items.md:76`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-producer-adjudication/record-items.md:76)）。段2プラン自身は訂正を予定している（[`s2-plan.md:573`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:573)）。

反例または検算: 6順列は `SDX,SXD,DSX,DXS,XSD,XDS`。一つの順列は3 run なので、

\[
2\ workloads\times6\ blocks\times3\ arms=36\ runs/cluster .
\]

各 workload での実数え上げは次のとおり。

| arm | 位置1 | 位置2 | 位置3 | 直前 arm |
|---|---:|---:|---:|---|
| S | 2 | 2 | 2 | `START×2, D×2, X×2` |
| D | 2 | 2 | 2 | `START×2, S×2, X×2` |
| X | 2 | 2 | 2 | `START×2, S×2, D×2` |

したがって「位置と直前 arm がちょうど2回ずつ」も36-run 解釈だけが満たす。

提案: 承認前に schema を `12 blocks / 36 runs` へ実際に直す。completed attempt は36件の完全双射、post-performance failure はその厳密 prefix とする。プランに訂正案があるため単独 blocker とは数えないが、現ファイルのままは承認不可。

### 所見 8 — `RF⊂(0,1) ⇔ N>0∧G>0` は負の分母枝で偽

区分: blocker

根拠: core と D229 は無条件の同値を主張する（[`preregistration.md:109`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:109)、[`decisions.md:10727`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/docs/decisions.md:10727)）。しかし core の状態表自身は負の分母で比が `(0,1)` に入ることを認める（[`preregistration.md:161`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:161)）。

反例または検算: 任意の有限 `q` に対し、`(N,D)` 楕円を中心 `(-1,-2)`、半径 `r=0.1` の円にするよう

\[
S_{ND}=\frac{Jr^2}{q^2}I
\]

と置く。このとき `A=4-r²>0`、`D̄<0` で分母は0を含まない。楕円全体で `N<0` かつ `G=D-N<0` だから、比 `N/D` は有界でおよそ `[0.445,0.557]⊂(0,1)`。しかし `inf N<0`、`inf G<0` であり、主張された同値は破れる。`q` の選び方では救えない。

提案: 同値を

\[
A>0\land\bar D>0\land RF\subset(0,1)
\iff
\inf_C N>0\land\inf_C G>0
\]

の正分母枝に限定する。primary は従来どおり `N,H,G` の lower bound を権威とし、RF 区間だけから pass を導かせない。この修正は親 brief の §15 exact-key erratum の範囲外で、D229 にも触れるためユーザー裁定が要る。

## 総括

- blocker: **5件**
- 判定: **NO-GO**
- ユーザー裁定が要る点:
  1. Fieller 同値の追加 erratum か、新 core への切替
  2. `a12` を正規モデル下の stress check とするか、cluster-level worst-case 較正へ変更するか
  3. alpha root を pilot 前へ移す方法（B 前倒し／A-B 分割変更）
  4. 特異共分散を既存 `invalid_representation` に写せるか、状態表を改訂するか
  5. `a10` の一意性のため reference solver を追補凍結対象に含め、docs-only scope を広げるか

テスト、build、Pegasus 実走、power solver、`a12` simulation は実行しておらず、緑は主張しない。