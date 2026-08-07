# [T-139] 本走 — 事前登録 core (2026-08-07 凍結、実走前に commit する)

```text
authority: none
default_effect: no-state-change
study_label: rf_partial_recovery / paired_cluster / main_study / core
pilot_admission: requires_addendum_a
main_admission: requires_addendum_a_and_b
```

## 0. 本書の位置づけと凍結の意味

本書は **[T-139] 本走の推論の構造 — 問い・estimand・受理条件・状態空間・設計・失敗規則 — を、
本 study の pilot と本走のデータを 1 点も見る前に固定する事前登録の core** である
(既存の J=1 engineering screen の結果は既に見ている。§17 を参照)。

**本事前登録は 2 段階である。**数値パラメータの一部 (時間予算・待機・driver 引数・arm identity・
`J_max` と `J` の導出手続き・同時信頼領域と臨界値 `q` の構成・primary 系列の有意水準) は本書では
名前だけを固定し、§14 の**追補 A** で確定する。追補 A も pilot 投入より前、すなわち本 study の
データを 1 点も見る前に commit する。**したがって本書単独では完結した事前登録ではない** —
完結するのは core と追補 A の組である。この点を「core だけで推論内容が完全に凍結済み」と
記述してはならない。
可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc であり、本書はそれらの正本ではない
(`authority: none` はその意味であって、拘束力がないという意味ではない)。

**発効点。** 本書と、本書を定める決定・roadmap の限定例外は、当該決定が canonical 台帳へ fold された
land 以後にのみ効力を持つ。fold 前の branch 上の checkout から得た cluster を適格として扱わない。

**凍結の実装は commit / blob 参照束縛である。** 本書の凍結単位は作業木の現在の bytes ではなく、
結果の記録が参照する `<commit>` / `<path>` / blob の SHA-256 の三つ組である。検証側は指定 commit の
tree から本書の path の blob を読み、その digest を記録と照合し、さらにその commit が測定 checkout の
祖先であることを確認する。現在の HEAD や作業木の bytes は、過去の結果の設計を上書きしない。
作業木の bytes を固定する検査 (`FROZEN_MANIFEST` 型) は**置かない** — main の前進を妨げる検査を作らない
というユーザー裁定に従う。本書は自分自身の digest を本文へ書かない (自己参照の禁止)。

**結果を見てから本書を書き換えてはならない** (D126 決定 (4))。書き換えたら別 study である。
未確定として残る量は §14 の**追補 (addendum)** に閉集合で委ねてあり、追補は本書の推論内容を変更できない。

**確定値の根拠。** 裁定**前**の問い・選択肢・推奨理由は同ディレクトリの `package.md`
(`authority: none`、凍結) と `preregistration-draft.md` を参照する。それらは裁定前に書かれた記録であり、
**採択後に書き換えない**ので、本文には今も「未裁定」と書かれている。
**採択結果の正本は `docs/worklog.md` のエントリ (299) / (300) と、本 wave が land する決定**であり、
本書はその結果を指定 commit / path / blob へ射影したものである。

## 1. 問い

代替 X (modeX) は、意図的に取り除いた最適化による劣化を、部分的に回復するか。
**部分回復とは、劣化版より速く、かつ元の版に達していないことをいう。**
元の版を超えた場合は「回復」と呼ばず「stock 超過」とだけ述べ、機序の帰属には別証拠を要求する。

## 2. arm と workload

| arm | 内容 |
|---|---|
| `stock` (S) | 元の版 |
| `mode1` (Dg) | 意図的に最適化を 1 つ外した劣化版 |
| `modeX` (X) | 合成システムが作った回復候補 (4 stripe、`alignas(64)` 分離、固定回数 mixer) |

workload は W1 (高競合 write) と W2 (中競合 mixed) の 2 本。
候補の exact bytes は request `892042` の `run_commit = 425ed190` に束縛する。

## 3. 量の定義 (cluster = 1 割当て、`j` を cluster 添字とする)

`m_{A,wj}` を workload `w`・arm `A`・cluster `j` の代表値とする。
**代表値は cluster 内反復の算術平均とする** (裁定 U7)。

```text
N_wj = m_X,wj  − m_Dg,wj      回復量
D_wj = m_S,wj  − m_Dg,wj      劣化幅
G_wj = m_S,wj  − m_X,wj       元の版までの残り
```

恒等式 `D = N + G` が成り立つ。primary endpoint は trace-disabled の `throughput_tps` 1 本
(裁定済み)。`throughput_tps` は大きいほど速いので、劣化版が遅ければ `D > 0` である。
abort 率等は説明用の副次指標であり、受理条件の family へ入れない。

回復率は `RF_w = E[N_w] / E[D_w]` (総回復率、裁定済み)。

**分母条件は総量型を採る** (裁定 U1 (a))。

```text
H_wj = D_wj − κ_w · S_wj        ただし S_wj = m_S,wj
```

とし、`E[H_w] > 0` を検定する。`E[S_w] > 0` のもとで、これは
`E[D_w] / E[S_w] > κ_w` すなわち「劣化幅が元の版の `κ_w` 倍を超える」と同値である。
`D`・`S`・`H` はいずれも `throughput_tps` の次元を持ち、`κ` は無次元である。

**閾値は `κ_W1 = κ_W2 = 0.20` に固定する** (裁定 U2、2026-08-07)。
これは元の版の throughput に対する**相対的な劣化幅**であり、パーセントポイントではない。
候補の測定結果と無関係にユーザーが定めた値である。
**判定は狭義の不等号による** — 劣化幅が元の版の 20% を**超えない** (`E[H_w] ≤ 0` の) workload では
「回復」を主張しない。ちょうど 20% は受理しない。

## 4. 受理条件 (primary)

workload ごとに、cluster level の標本平均・標本共分散から構成した**同時信頼領域** `C_w` について

```text
P_w  :=  inf_{C_w} N_w > 0
     AND inf_{C_w} H_w > 0
     AND inf_{C_w} G_w > 0
```

とし、primary は両 workload の連言 `P_W1 AND P_W2` **1 本**とする
(intersection-union なので多重補正は不要)。**受理条件は 3 つである** — 3 つ目 (`G > 0`) を落とすと、
元の版を追い越した候補まで「回復した」と認証できてしまう。

**区間推定は同じ同時領域の ratio projection として導出する。** 別構成の Fieller を二重に課さない —
同じ標本共分散と同じ臨界値 `q` から作れば、Fieller 集合の `r=0` 検査は `N` の検査、`r=1` 検査は
`−G` の検査であり、「有界な集合が `(0,1)` に含まれる」ことと `N>0 ∧ G>0` は**同値**である。
別構成にすると、正当な手続き差を「データ破損」として拒否する偽陰性経路になる。

**ただし分母条件 `H` はこの同値の外にある。** `RF` の区間が `(0,1)` に収まっても `H ≤ 0` はありうる
(例: `S=100, Dg=90, X=95` なら `N=5, D=10, G=5, RF=0.5` だが `H = 10 − 20 = −10`)。
§5 の状態表はこの領域を独立の状態として持つ。

Fieller 係数は
`A = D̄² − q²s_DD/J`、`B = N̄D̄ − q²s_ND/J`、`C = N̄² − q²s_NN/J` に対し `Ar² − 2Br + C ≤ 0`。

**同時信頼領域 `C_w` の構成 (信頼水準・分布近似・有限標本補正) と臨界値 `q` の導出規則は、
本 core では名前だけを固定し、数値と手続きは §14 の追補 A で確定する。**
追補 A は pilot より前、すなわち本 study のデータを 1 点も見る前に commit するので、
結果依存の選択にはならない。追補 A が存在しない間、`P_w` の判定も `J` の導出も行わない。

## 5. 状態の閉表 (2 軸)

**両軸とも「上から順に最初に一致した 1 つを採る」(first-match) で読む。**
条件を独立に並べると、空集合が複数のラベルに同時一致する (空集合は連結でもある) ため、
排他性は first-match で与える。

**軸 1 — 区間の形 `interval_shape`:**

| 順 | 値 | 条件 |
|---|---|---|
| 1 | `empty` | 解集合が空 (`A > 0` で判別式が負の場合、および `D_j ≡ 0`, `N_j ≡ 1` のとき `A=B=0, C=1` の場合を含む) |
| 2 | `bounded` | 解集合が非空かつ有界 |
| 3 | `disjoint` | 解集合が非連結 |
| 4 | `unbounded_connected` | 残り (非空・連結・非有界) |

**軸 2 — 適格性の状態 `qualification_status`:**

| 順 | 値 | 条件 | 正例 |
|---|---|---|---|
| 1 | `weak_denominator_not_certifiable` | `A ≤ 0` — 分母 `D_w` の信頼集合が 0 を除外できない | false |
| 2 | `degradation_absent` | `A > 0` かつ `D̄_w < 0` — 分母は 0 を強く除外するが符号が負。劣化版が元の版より速く、**劣化がそもそも存在しない** | false |
| 3 | `not_certifiable` | `A > 0`、`D̄_w > 0` かつ `interval_shape` が `empty` — 分母は健全だが解集合が空 | false |
| 4 | `boundary_ambiguous` | 区間が 0 または 1 を含む / 接する | false |
| 5 | `below_degraded` | 区間全体が 0 未満 | false |
| 6 | `stock_exceeding_unattributed` | 区間全体が 1 超 | false |
| 7 | `degradation_below_kappa` | 区間全体が `(0,1)` の内側だが `inf_{C_w} H_w ≤ 0` | false |
| 8 | `partial_recovery` | 区間全体が `(0,1)` の内側かつ `inf_{C_w} H_w > 0` (= `P_w` 成立) | **true 候補** |

`A > 0` は「分母の信頼集合が 0 を強く除外する」ことと同値である (`A = D̄² − q²s_DD/J > 0`
⟺ `|D̄| > q·sd(D̄)`)。したがって `A ≤ 0` は順 1 が吸収する。`D̄ = 0` は `A ≤ 0` を意味するので
順 1 へ落ち、順 2 の `D̄ < 0` と順 3 の `D̄ > 0` の間に穴はない。`A > 0` でも解集合が空になる場合が
あり、それは順 3 が受ける (軸 1 の `empty` は `A ≤ 0` 側とは限らない)。
順 1〜3 の否定のもとで解集合は非空・有界なので閉区間であり、順 4〜6 の否定のもとでは
必ず `(0,1)` の内側にある。**順 1〜8 は到達可能な全状態を尽くす。**

- **`degradation_absent`** は「劣化版の方が速い」領域である。`D̄ < 0` のとき `RF` の比は
  形式的には `(0,1)` に入りうるが、それは分子・分母がともに負であることによる**符号の偶然**であり、
  「回復」でも「浅い劣化」でもない。この状態を `degradation_below_kappa` と混同してはならない。
- **`degradation_below_kappa`** は「劣化は実在し回復も見えたが、**分母条件 `inf_{C_w} H_w > 0` を
  認証できない**」状態である。点推定が `κ` を超えていても信頼領域の下端が 0 以下ならここへ入るので、
  「劣化幅が `κ` 以下である」と読んではならない。いずれにせよ認証しない。

`empty` は有効な raw からも生じるので、表現不整合 (`invalid_representation`) と分離する。
`RF > 1` は「回復」とも「新規改善」とも帰属させず、stock 超過とだけ述べる (D162 決定 6)。

## 6. 標本数の決め方 (二段階)

**pilot (外部・非 pool)。** `J_p = 8` + 予備 2 (裁定 U5)。
pilot の raw は本走の推定・p 値・区間へ**一切合算しない**。合算すると「途中で見て足りなければ足す」
形になり、帰無仮説のもとでの誤り率が名目を超える。
pilot が推定するもの: 割当て間共分散、cluster 内残差と位置・直前 arm の効果、
待機後の環境復帰、割当ての実時間と infra failure 率、**計算ポイントの単価**。

**planning alternative は `d = 1.0` に固定する** (裁定 U4)。pilot の下側効果が 1 を下回っても
`d` を引き下げない (引き下げは結果依存の費用裁定変更にあたる)。下回る場合は
`design_not_feasible` を終端状態として本走を投入しない。

**本走の `J`。** 目標は **「6 成分の同時受理確率 80% 以上」** (裁定 U4、成分ごと 80% ではない)。
`J` は pilot 母数の**共同信頼集合上の最悪検出力**で評価し、候補 `J` 全体に同時保証を掛けた上で
最小の適格値を選ぶ。**単一の scalar `d` から一意に決めない** — 6 成分の相関と区間形状で
受理確率が変わるため。正規近似の目安は成分ごと 80% で `J≈11`、全体 80% で `J≈13`。
**これは sanity 値であって本走値ではない。**

`J_max`、pilot 本数、再設計の禁止は **pilot 前に固定する**。pilot 本数と再設計の禁止は本 core が
固定した (`J_p = 8` + 予備 2、`d` を下げない)。**`J_max` の数値と、26 割当ての内訳 (本走と予備の境界)、
および pilot 推定から `J` を一意に導く手続き (共同信頼集合の取り方と最悪検出力の評価法) は
§14 の追補 A で確定する。**
`design_not_feasible` は当該候補・親系列の**終端状態**とし、
再開は全試行を保持した新 study・新しい有意水準割当てに限る。

**本走開始後の追加は一切行わない** (D126 決定 4)。

## 7. paired cluster の適格条件

1 割当てを 1 cluster とする。**cluster 内は 6 反復、3 arm の全 6 順列を各 1 回**とする
(裁定 U6 (a))。これにより arm 位置と直前 arm がともにちょうど 2 回ずつ現れ、厳密に均衡する。

- 推定量・検定統計量・区間は cluster 間の標本平均と標本共分散だけから構成する。
  cluster 内の反復・block・個々の測定値を独立標本や追加の自由度として数えない。
- block の実行順は事前 seed で許容集合から選び、runtime 乱数を使わない。
  W1 / W2 の block 順は cluster 間で差 1 以内に均衡させる。
- 結果を見た後の cluster 選別・順序変更をしない。全 attempt を保存する。
- 性能を測る 3 arm はすべて **trace-disabled ビルド**で揃える。correctness 検証は trace-enabled の
  別ビルド・別 run で行い、同一割当ての中で性能測定と混ぜない (絶対規律 1)。
- pairing・順序均衡・cluster の受領証のいずれかが成立しなければ「判定不能」とし、
  unpaired 推定へも通常の campaign compare へも自動 fallback しない。
- **適格性は producer の自己申告では決まらない。**保存した生の受領証から独立 validator が
  bytes を自ら読み直して再計算した結果だけが権威である (D162 決定 (3))。
  **消費側 (certified 選択・レポート) は decision を入力として受け取らず、信頼された validator を
  同一呼出しの中で再実行する** (D162 決定 (4))。validator の source hash が decision に載っていることは
  「その validator が実行された」証拠にならない。検査は単一 fd / snapshot で読み、hash と parse を
  同一 byte buffer に対して行う (D162 決定 (5))。

**帰無仮説は weak mean null を primary とし** (estimand が平均 contrast のため)、
sharp null は副次感度分析とする。weak null の型 I 誤りは、同じ許容 schedule 集合を使う
事前 simulation で較正する。

## 8. 実行順序・待機・時間予算 (裁定 U11 — 数値は追補で確定する)

**主経路は割当ての時間予算を組み直すこと** (裁定 U11 (a))。具体的には build を割当ての外で済ませ、
使用するバイナリの identity を hash で束縛する。**この経路が成立しない場合にだけ**、
より長い walltime を要求する予備経路 (U11 (b)) を採る。

現時点で、build・run・待機・検証・後片付け・安全余裕を含む**承認済みの数値表は存在しない**。
待機の原案は arm 間 30 秒・block 間および workload 切替時 60 秒だが、**現データはこの十分性を
実証していない。**待機後に環境が戻ったことを確認する指標と、戻らなかった場合の失敗分類も未確定である。

したがって本 core は数値を書かない。数値は §14 の **追補 A** で確定する。
**追補 A が存在しない間、pilot を投入してはならない** (§15 の gate)。
これは値なし前方参照でも placeholder でもなく、閉じた禁止規則である。

## 9. 欠測と失敗

- **correctness anomaly は候補の終端 reject。** 削除も置換もしない (絶対規律 2 の直接適用)。
- 性能測定の**開始前**の infra failure だけ、結果を見る前に外部証拠で確定した上で
  事前順序固定の予備から置換可。
- 性能測定の**開始後**の失敗は reject または判定不能。予備で置き換えない。
- 救済する場合は worst-case bound と感度分析を併記する。
- 失敗分類は本節の集合を正本とし、追補が新しい分類を作ってはならない。

## 10. 有意水準の台帳 (裁定 U8 — 数値は追補で確定する)

primary 系列と個別公表系列に**別々の累積台帳**を置く。台帳は最初の正式試行より前の正規の根へ
束縛し、新しい親系列 ID の自己申告でリセットできないようにする。
**候補数上限と累積 spending の数値は未確定**であり、§14 の **追補 B** で確定する。
**追補 B は本走の投入より前に commit する** — verdict の直前ではない。
pilot の raw を見た後に本走の有意水準を選べる経路を残さないためである。
追補 B が存在しない間、本走を投入してはならない。

個別公表は primary の成否にかかわらず **6 セル全件を固定表で公表**する
(成功セルだけを抜き出さない)。

## 11. 着手順序と費用 (裁定 U9 / U10)

```text
段 A  producer を実装する (記録項目を確定。適格性の申告は受け付けない)
段 B  pilot を走らせる → この時点で D162 の発火条件 (i)(ii) が成立する
段 C  それを根拠に validator と最初の消費側を実装する → (iii) が成立する
段 D  pilot から標本数を導き、本走を投入する
```

D162 は書き換えない。pilot 自身を「発火条件を満たす計測」にすることで、
「条件が揃ってから機械化する」規律をそのまま守る。
段 A の記録項目確定は**単独の裁定 gate** とする。

**総ポイント上限は 26 割当て相当**とする (裁定 U10)。`8 + 2 + 13 + 3` という内訳は裁定時の
**目安**であって確定値ではない — 本走の `J` と予備の境界 (`J_max`) は追補 A の `a10` で確定する。
上限 26 だけが固定である。
**単価は未知である。** pilot の 1 本目で scheduler の会計痕跡を取得して検証し、1 本ずつ保守的に
上限を更新する。費用未知のまま全割当てを一括承認しない。
pilot から求めた `J` が残余上限内に無ければ `design_not_feasible` とする。

## 12. 記録項目 (raw receipt。producer が書き、validator が読み直す)

適格性状態・pairing の成否・受理状態・validator の identity / 結果は
**closed schema で拒否する** (D162 決定 2)。producer が宣言できるのは
利用意図を示す閉集合の種別 (field 名は実装 wave の新 D で確定する) と
raw な実行事実・証拠 pointer だけである。

必須項目:

- 事前登録の束縛 — core の `<commit>` / `<path>` / blob SHA-256、追補 A の同三つ組、
  および本走では追補 B の同三つ組。加えて限定例外を発効させた fold commit。
- 環境タグ (`pegasus`) と**環境証明** (`attestation_mode` を要求扱いにする)。
- 測定 checkout (repo / CCBench の head)、依存の pin、build identity、compile argv、
  割当て外 build を採る場合は使用バイナリの hash。
- 割当て ID・node・時刻・会計痕跡・単独性検査の結果。
- 3 arm の source / binary / compile identity。
- 計画した実行順序と**実際の**実行順序、各 run の位置・直前 arm・timestamp・raw TPS。
- correctness の**証拠** (boolean の申告ではなく、verifier が再実行できる形)。
- liveness、admission telemetry。
- **全 attempt**、理由コード、置換関係、親系列 ID。

## 13. 必須の否定検査 (実装時に必ず kill する変異)

1. 失敗した投入を台帳と raw の**双方**から落として双射を成立させる。
2. 新しい親系列 ID を自己申告して累積有意水準をリセットする。
3. correctness anomaly を clean と申告する。
4. 適格性 field を raw へ足す (closed schema が拒否するか)。
5. 事前登録した `J` に対し cluster が 1 本足りない状態で受理する。
6. 実際の実行順序が計画と異なる / 待機が不足している状態で受理する。
7. core と異なる blob を core として申告する、または追補が §14 の閉集合の外の field を設定する。
8. 追補が環境復帰の判定を恒真化する、または性能測定の開始後の失敗を開始前の infra failure へ写す。
9. 限定例外の fold より前の checkout から得た cluster を適格として受理する。

## 14. 追補 (addendum) の閉集合

追補は **core が書いた文章を一切変更しない。**追補が設定してよいのは次の field だけであり、
それ以外の変更は core の変更に当たる。core を変更する必要が生じたら、それは**別 study** であり、
新しい core を起こしてユーザー裁定へ戻す (本 core を書き換えない)。追補が閉集合の外の field を
含んでいたら、その追補は解決に失敗する (§15 の gate が拒否する)。

**追補 A — 本 study のデータを 1 点も見る前、すなわち pilot 1 本目の投入より前に commit する:**

| # | field |
|---|---|
| a01 | 1 割当ての時間予算表 (build・run・待機・検証・後片付け・安全余裕の秒数と合計) |
| a02 | arm 間・block 間・workload 切替時の待機秒数 |
| a03 | 待機後の環境復帰を判定する指標と、その事前登録した許容範囲 |
| a04 | 復帰しなかった場合の失敗の写像先 (§9 の既存分類のどれに写すか) |
| a05 | 割当て外 build を採る場合の binary identity 束縛方法 (hash の対象と記録先) |
| a06 | 予備経路を採る場合の要求 walltime |
| a07 | W1 / W2 の driver 引数一式 (thread 数・record 数・skew・read 比・測定時間) |
| a08 | 3 arm それぞれの source / patch / build identity と compile argv (候補は既に `425ed190` に束縛済み) |
| a09 | block 実行順を選ぶ事前 seed と、許容 schedule 集合の定義 |
| a10 | `J_max` の数値、26 割当ての内訳 (本走と予備の境界)、pilot 推定から `J` を一意に導く手続き |
| a11 | 同時信頼領域 `C_w` の構成 (信頼水準・分布近似・有限標本補正) と臨界値 `q` の導出規則 |
| a12 | weak null の型 I 誤りを較正する事前 simulation の仕様 |
| a13 | **primary 系列に割り当てる有意水準**。`q` はここから導くので、追補 B では動かせない |

**追補 B — 本走の投入より前に commit する** (verdict の直前ではない。pilot の raw を見た後に
本走の判定基準を選べる経路を残さないため)**:**

| # | field |
|---|---|
| b01 | 候補数上限 |
| b02 | 個別公表系列の累積 spending 関数の数値割当て |
| b03 | 累積台帳を束縛する正規の根の同定方法 (親系列 ID の自己申告でリセットできないこと) |

**追補が越えてはならない線 (これを破る追補は core の変更であり、別 study である):**

- a03 の指標と許容範囲は、環境復帰の判定を**恒真化してはならない**。定数を返す指標、
  実現値を必ず含む許容範囲、範囲を持たない指標は認めない。指標は割当てごとに変動しうる実測量とし、
  許容範囲は pilot 前に固定した有限区間とする。
- a04 は §9 の分類への**写像だけ**を決める。新しい分類を作らない。
  **性能測定の開始後に起きた失敗を、開始前の infra failure へ写してはならない**
  (写せると予備置換の禁止が空文になる)。
- a02 の待機秒数は測定プロトコルを固定するものであり、推定量・検定・区間の式を変えない。
  ただし待機は測定値そのものを動かすので、pilot より前に固定し、pilot 後に変更しない。
- a07 / a08 は workload と arm の同一性を固定するものであり、pilot 後に変更しない。
  変更は別 study である。
- a11 と a13 は `q` の導出規則と primary 系列の有意水準を固定するものであり、pilot の結果を見て
  `q` を選び直すことを許さない。**追補 B は `q` に影響する量を一切持たない** — B が持つのは
  個別公表系列の候補数上限・spending・台帳の根だけである。これにより primary の判定基準は
  pilot より前に完全に固定される。

追補は core と同じく実走前に commit し、結果の記録がその `<commit>` / `<path>` / blob digest を
参照する。**追補は自分が従属する core の canonical path・commit・blob digest の三つ組を明記する**
(path だけでは、同じ path の別 blob へ従属を付け替えられる)。

## 15. 投入 gate (順序検査。機械配線は producer 実装 wave の責務)

本 gate は「事前登録が存在しない状態で投入しない」という**順序**の検査であり、作業木の前進を
縛るものではない。**本 wave は文書上の契約だけを定める。**producer・validator・consumer・
投入 script・受領証への機械配線は producer 実装 wave が行い、本 wave では追加しない。

署名 (3 段。receipt の照合は投入の**前提にしない** — 投入後にしか存在しないため):

```text
resolve_effective_preregistration(
    repository_root, *,
    core_ref     = (commit, path, sha256),
    addendum_a   = (commit, path, sha256),
    addendum_b   = (commit, path, sha256) | None,
) -> PreregBinding        # measurement_head は repository_root の実 checkout から導出して binding に含める

submit_pilot(*, binding: PreregBinding) -> submission_id
submit_main(*, binding: PreregBinding) -> submission_id

verify_receipt(*, binding: PreregBinding, receipt) -> None
```

**禁止:** `submit_pilot` は、次をすべて満たす `binding` が `resolve_effective_preregistration` から
返っていない限り実行してはならない。

1. `core_ref.path` が、本 study の決定が定める canonical core path と byte 一致する
   (producer は core を自由選択できない)。
2. `core_ref.commit` の tree に `core_ref.path` の blob が実在し、その SHA-256 が
   `core_ref.sha256` と一致する。
3. **`core_ref.sha256` が、承認済み core の digest と一致する。**承認済み core とは
   `F:<canonical core path>` の blob である (`F` は下記の fold commit)。
   すなわち `core_ref.commit` は `F` でも `F` の子孫でもよいが、**bytes は `F` 時点のものと
   同一でなければならない**。これがないと、`F` の子孫で同じ path を書き換えた blob を
   「core」と申告できてしまう (caller が渡した digest との自己整合だけでは防げない)。
   `F` の同定は次で一意である — **`F` = 本 study の決定を `docs/decisions.md` へ追記した
   main 上の fold commit**。その SHA は land 後に worklog へ記録する。
4. `addendum_a` も (1)(2) と同型に解決でき、その追補が従属先として記す core の
   **path・commit・blob digest の三つ組**が `core_ref` と一致する。
5. `addendum_a` が §14 の閉集合 `a01`〜`a12` を **exact-key で満たす** — 全件が存在し、
   かつ閉集合の外の field を含まない (欠落も余剰も解決失敗)。§14 の「越えてはならない線」に
   触れる値を持たない。同じ検査を `addendum_b` に適用するときは、その対応する閉集合
   (`b01`〜`b03`) を基準にする。
6. `core_ref.commit` と `addendum_a.commit` が `measurement_head` の祖先である
   (`orchestrator/campaign/trial_registry.py` の `assert_prereg_ancestor` と同型の検査)。
   **`measurement_head` は caller の引数ではなく、`repository_root` の実 checkout から
   resolver が導出する** — 署名に引数として置かない。
7. core の `pilot_admission` が要求する追補が (4)(5) ですべて解決済みである。

`submit_main` は上記に加え、`addendum_b` が (1)(2)(4)(5)(6) と同型に解決でき、core の
`main_admission` が要求する追補がすべて揃っていることを要する。**追補 B は本走の投入前に要る** —
verdict の直前ではない。

`verify_receipt` は投入**後**に、receipt が記録した三つ組と `measurement_head` が `binding` と
一致することを確認する。これを admission の前提に置くと、投入前に存在しない値を前提にする
時間逆転になる。

**通る正例 (1 つ):** 限定例外の決定が fold された commit を `F` とする。core が `F` の子孫 `C` の
path `P` に blob `B` として存在し `h = SHA-256(B)`、追補 A が commit `C2`・path `P2` に blob `B2` として
存在し `h2 = SHA-256(B2)`、`B2` が従属先として `(P, C, h)` を記し `a01`〜`a12` だけを設定しており、
`C` と `C2` がともに実 checkout の HEAD の祖先であるとき、
`resolve_effective_preregistration(repo, core_ref=(C,P,h), addendum_a=(C2,P2,h2))` は成功し、
他の admission 条件を満たせば `submit_pilot` へ進める。
**この正例は現時点では成立しない** — 追補 A がまだ存在しないためである (要件 4・5・7 が不成立)。
gate は恒真な deny ではなく、追補 A の land によって到達可能になる。
ただし**追補 A が land しただけでは pilot は走らない** — 本 gate を実際に実行する producer と
resolver がまだ実装されていない (次節)。

**この gate が保証しないこと:** 台帳の外で走らせた投入は見えない。producer が実際とは異なる
bytes や schedule で走らせながら整合した受領証を作る偽造も、外部の時刻根拠なしには検出できない。
現在の作業木や main の同 path の bytes が過去の blob と異なることは**検出対象ではない**
(過去の結果は commit の blob に束縛されるため)。

## 16. 本走の後

`RF` の点推定と区間、6 セルすべての調整済み p 値と同時区間を、**primary の成否にかかわらず
固定表で公表する** (成功セルだけを抜き出さない)。
機序の帰属は本 study では行わない (3 変更を同時に入れたため。ablation は別の事前登録 study)。

## 17. 本書が主張しないこと

- 代替 X が適格である、とは主張しない。現時点で成立しているのは J=1 の engineering screen だけである。
- 回復の機序が stripe 数・cache line 分離・固定回数計算のどれによるか、は主張しない。
- 推奨した標本数が正しい、とは主張しない。割当て間のばらつきは 1 点も推定されておらず、
  pilot の前に確定できない。
- **本 wave が投入 gate を機械的に実装した、とは主張しない。**本書が定めるのは文書上の契約である。
