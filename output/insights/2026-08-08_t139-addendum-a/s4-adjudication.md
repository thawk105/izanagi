# [T-139] 追補 A 起草 — 段 4 裁定 (親)

```text
authority: none
default_effect: no-state-change
```

段 2 プラン 1 本、段 3 敵対レンズ 2 本 (A = 統計・推論、B = 運用・規律) を裁定する。
両レンズとも **NO-GO**、blocker は A が 5 件・B が 6 件の計 11 件。
重複を統合すると 11 件、**refuted は 1 件** (A8 の「悪用可能性」の部分だけ)。

親は各所見を独立に裏取りした。裏取りの逐語は §0 に置く。

---

## 0. 親が独立に検算したもの

| 主張 | 出所 | 親の検算 | 結果 |
|---|---|---|---|
| core digest = `ac939af4…` が `F=88d68f91` と作業木で一致、HEAD は F の子孫 | 段 1 | `git cat-file blob F:<path> \| sha256sum`、`git merge-base --is-ancestor` | **一致** |
| `throughput.tsv` digest = `755cfa7e…c4f2` | 段 2 `a12` | `sha256sum` | **一致** |
| patch digest `3b9cdf…1951`、CCBench pin `d706650c…`、run_commit `425ed190…` | 段 2 `a08` | `submission-receipt.md` §3 / §6 と照合 | **一致** |
| `a09` seed = `7df15572…615d` | 段 2 | `printf 't139-mainrun-a09-v1\|ac939af4…' \| sha256sum` | **一致** |
| `a12` seed = `01dad84c…8ed2` | 段 2 | 同型 | **一致** |
| `a01` の秒数総和 | 段 2 / レンズ B 所見 4 | `180+36×15+24×30+11×60+180+120 = 2400`、`+900 = 3300`、`+300 = 3600` | **一致** |
| `load1` の実測域 | レンズ B 所見 2 | `limited-screen.tsv` 36 行の min/max = `3.29` / `40.18` | **レンズ B が正しい。親 brief の「3.29→13.47」は 6 本の liveness 終了時点までの部分要約であり、36 行全体の要約ではない** |
| A8 の反例が primary を汚染するか | レンズ A 所見 8 | 反例 `(N̄,D̄)=(-1,-2)`, `S_ND=(Jr²/q²)I`, `r=0.1` → `A = 4 − 0.01 = 3.99 > 0` かつ `D̄ = −2 < 0` | **core §5 軸 2 の first-match 順 2 `degradation_absent` (正例 false) が、軸 1 の区間形を見る前に吸収する。primary は汚染されない** |

**親 brief の誤りを 1 件確認した** — `load1` の要約 (上表 8 行目)。訂正は本裁定を正とする。

---

## 1. 所見の裁定表

区分は段 3 の申告、判定は親。`scope 内` = 本 wave の追補 A 案・erratum 案・記録項目案で閉じる。
`scope 外` = 凍結 core の受理述語・D234 の署名・A/B 分割・未実測量に触るため、
`DW-S04` に従いユーザー裁定パッケージへ返す。

| # | 所見 | 区分 | 判定 | 採否と scope |
|---|---|---|---|---|
| A1 | pilot 前に固定できるのは scalar `q` でなく写像 `J↦q(J)` | minor | **real** | 採用・scope 内。`a11` と package の文言を「`q` の**規則**を pilot 前に固定する。数値は `J` 確定と同時に決まり、それ以降動かない」へ改める |
| A2 | `N,H,G` は 3 次元平均の独立な線形汎関数 (`det = κ = 0.2`)、IUT に workload 間補正は不要 | minor | **real** | 採用・scope 内。行列式と IUT の包含証明を `a11` に明記 |
| A3 | 特異共分散で `C_w` と状態表が未定義 | blocker | **real** | 採用 (修正)・scope 内。§2.1 参照 |
| A4 | `a10` の数値手続きが再現不能 | blocker | **real** | 採用 (修正)・scope 内。§2.2 参照 |
| A5 | `a12` は cluster level の型 I 誤り較正ではない | blocker | **real** | **scope 外 → 裁定 R2**。案は書くが凍結しない |
| A6 | `a13` の級数は正しいが `b03` が root リセット経路を残す | blocker | **real** | **scope 外 → 裁定 R3**。案は書くが凍結しない |
| A7 | `record-items.md` の「1 割当て 6 件」は誤り、36 run が正しい | major | **real** | 採用・scope 内 |
| A8 | `RF⊂(0,1) ⇔ N>0∧G>0` は負分母枝で偽 | blocker | **数学的主張は real / 悪用可能性は refuted** | 部分採用・scope 内 + **裁定 R5**。§2.3 参照 |
| B1 | erratum が無検査の第 3 権威になる | blocker | **real** | **scope 外 → 裁定 R1**。契約を全文起草して返す |
| B2 | `a03` は形式上恒真でないが、正常割当てを通す証拠が 0 件 | blocker | **real** | **scope 外 → 裁定 R4**。§2.4 参照 |
| B3 | `a04` の marker bytes が必須化されていない | major | **real** | 採用・scope 内 |
| B4 | cap を hard deadline にする契約がない (`timeout` に `--kill-after` 無し) | minor | **real** | 採用・scope 内 |
| B5 | `a05` は「実際に exec された bytes」を独立再計算できない | blocker | **real** | 採用・scope 内 (残余の非保証は §15 の既存文言どおり明記) |
| B6 | `a07` は明示 argv だけ一致し effective workload を固定できていない | blocker | **real** | 採用・scope 内。実 run log から effective flag map を全件固定する |
| B7 | `a08` の `identity_sha256` は build 後の値で、事前固定されていない | blocker | **real** | 採用 (修正)・scope 内。§2.5 参照 |
| B8 | `a09` の hash preimage が実装依存 | major | **real** | 採用・scope 内。byte grammar を逐語固定し、導出表と digest は producer が投入前に発行、validator が再導出 |
| B9 | 受領証 closed schema が未完成 + 6 run 記述 | blocker | **real** | 採用・scope 内 (確定版 `record-items.md` に反映) |
| B10 | 「追補 A 確定済み」という状態名は不正確 | major | **real** | 採用・scope 内。3 段階の状態名を採る |

**refuted は A8 の「悪用可能性」1 件のみ。**残る 10 blocker はすべて real である。
段 2 プランの P1〜P5 に対する裁定は §3。

---

## 2. 修正採用した所見の確定形

### 2.1 A3 — 特異共分散 (scope 内)

段 2 案は `S_ND^{-1}` を直接使い、特異時の写像を持たない。**逆行列を使わない定義に改める。**

`C_w` を**支持関数**で定義する。任意の `c ∈ R^k` について

```text
inf_{v ∈ E(q)} c'v  =  c'v̂ − q · sqrt(c'Sc / J)
```

を満たす閉凸集合を `E(q)` とする。これは `S` が正則なら段 2 案の楕円と一致し、
特異でも右辺は定義される (`c'Sc ≥ 0`)。core §4 の Fieller 係数 `A/B/C` は
`s_DD`, `s_ND`, `s_NN` だけから作られるので、この定義で不変である。

そのうえで **`S_w` の正定値性を計算可能性の事前条件**とする。不成立なら
core §7 の既存文 (「pairing・順序均衡・受領証のいずれかが成立しなければ判定不能」) と同じ
**`判定不能`** へ写す。core §5 の閉表は `qualification_status` の分類であり、
「統計量が計算できない」はその軸の状態ではない。**新しい失敗分類は作らない。**

> 成果物影響: これを入れないと、rank 落ちした標本共分散で resolver / 解析が停止し、
> その場で ridge・pseudoinverse・一次元縮約のどれを採るかが**結果を見た後の裁量**になる。
> 受理集合が事後に動く。

### 2.2 A4 — `J` の一意導出 (scope 内)

段 2 案の「outward-rounded interval arithmetic による lexicographic branch-and-bound、
gap ≤ 1e-3」は仕様ではない。レンズ A の反例 (bracket `[0.7996, 0.8005]` を 2 人が別々に解決できる) は
正しい。**solver を凍結対象に含める案 (レンズ A の提案) は docs-only scope を超える**ので採らない。

代わりに **least-favourable configuration (LFC) + 固定 seed の Monte Carlo** へ置き換える。

1. `Θ = M × V` の定義は段 2 案のまま (平均 97.5% Hotelling region × 共分散 Loewner 区間、
   Bonferroni で共同被覆 ≥ 95%)。
2. **LFC を 1 点に固定する。**
   `μ_k^- = inf_{μ∈M} μ_k` (成分ごとの下限。閉形式 `Ȳ_k − sqrt(c_M · (S_p)_kk / n_p)`)、
   `Σ^+ = (ν/ℓ) S_p` (Loewner 最大)。LFC = `(μ^-, Σ^+)`。
3. **単調性補題を planning model の一部として明記する。** 正規 planning model のもとで
   受理事象 `∩_k {μ̂_k − q·s_k/√J > 0}` の確率は (i) 各 `μ_k` について非減少、
   (ii) `Σ → cΣ` (`c > 1`) について非増加である。したがって
   `π_J(LFC) ≤ inf_{Θ'} π_J` が成り立つ範囲で LFC は保守側である。
   **`Θ` 全体に対する下界であることは主張しない** — Loewner 区間内の相関変化まで
   単調性で覆えないためである。この限定を追補 A に明記する (`DW-G05` の正直さ)。
4. **数値評価を完全に固定する。** 反復数 `B_pow = 1,000,000`、seed は
   `SHA-256("t139-mainrun-a10-v1|" || <core digest>)`、乱数 stream は `a12` と同じ counter mode、
   `Wishart` 生成は Bartlett 分解、分位点は正規化不完全ベータの逆で相対誤差 `1e-12` 以下。
   検出力の下側は片側 Clopper–Pearson lower bound (信頼水準 `1 − 1e-4`) を採る。
5. **選択規則から跨ぎを排除する。**
   `J = min{ j ∈ {4,…,13} : LB_j ≥ 0.80 }` を採るのは、
   **かつ**「`j` より小さい全候補で `UB_j < 0.80`」が成り立つときだけとする。
   閾値 `0.80` を Clopper–Pearson 区間が跨ぐ候補が 1 つでもあれば `design_not_feasible`。
   これで「もっと細かく分割すれば別の `J` になる」経路が消える。

> 成果物影響: これを入れないと、同じ pilot から 2 人が別の `J` を導ける。
> `J` は本走の割当て本数そのものなので、受理集合と費用の両方が事後裁量で動く。

### 2.3 A8 — Fieller 同値 (部分採用 + 裁定 R5)

親の検算 (§0) のとおり、反例は core §5 軸 2 の **first-match 順 2 `degradation_absent`** が
軸 1 (区間の形) を見る前に吸収する。`degradation_absent` の正例は `false` なので、
**primary が誤って true になる経路は存在しない。**したがって「悪用可能」は **refuted**。

一方、core §4 の逐語「有界な集合が `(0,1)` に含まれることと `N>0 ∧ G>0` は**同値**である」は、
負分母枝を除外していないので**主張としては不正確**である。これは real。

- **scope 内 (採用):** `a11` に「primary の権威は `N`・`H`・`G` の同時下限と §5 の first-match 表であり、
  `RF` の区間は §16 の公表用である」と明記する。これは core の文章を変更せず、
  追補が自分の担当 (`a11` = `C_w` の構成と `q` の導出規則) の中で読み方を閉じるだけである。
- **scope 外 (裁定 R5):** core §4 の文言そのものへ第 2 の erratum を当てるかは、
  ユーザーが授権した erratum (§15 の 2 箇所) の外である。親は当てない。

### 2.4 B2 — `a03` の未実測 (裁定 R4、ただし draft は書く)

レンズ B の指摘は正しい。`cpu_busy_core_equivalents ∈ [0,1]` は
「定数指標・実現値を必ず含む範囲・範囲なし」のいずれにも該当しないので**形式上は恒真でない**が、
**この閾値を正常な割当てが通る証拠が 1 件も無い。**既存 36 行は `load1` であって
`/proc/stat` counter ではないので、換算もできない。

親は次を確認した — probe は待機を 1 秒も置いていない (`t139_positive_control_probe.sh` に
run 間の `sleep` が無い) ので、**待機後の環境がどこまで戻るかは本 study の資料に存在しない**。

したがって `a03` は**案として書き、凍結しない**。裁定 R4 で 2 択を返す。

> 成果物影響: 閾値が厳しすぎると全 cluster が preflight で落ち、予備 2 本を使い切って
> `design_not_feasible` になる (割当て 26 本が無駄になる)。緩すぎると恒真化し、
> 待機の十分性検査が空文になる。どちらも受理集合を壊す。

### 2.5 B7 — `a08` の事前固定 (scope 内、修正)

`identity_sha256` は build の**結果**なので追補 A に書けない。両者を分離する。

- **追補 A (`a08`) が事前固定するもの:** source triple (repo commit / CCBench pin / patch digest)、
  arm ごとの mode macro、configure argv の**逐語 template**、
  正規化規則 (一時 root の token 化、対象 translation unit の集合)、
  performance = `TRACE=0, ADD_ANALYSIS=0` / correctness = `TRACE=1, ADD_ANALYSIS=1` の macro map、
  compiler の同定方法 (path + version + bytes の hash を record すること)。
- **受領証 (`a05` 側) が事後記録するもの:** 実 `identity_sha256`、実 binary hash、
  compiler bytes hash、link argv、動的依存。

**追補 A は「期待値の template と正規化規則」を凍結し、実 digest は凍結しない。**
これは §14 の「a08 = 3 arm それぞれの source / patch / build identity と compile argv」の
実行可能な読みであり、恒真化ではない (template と正規化規則が一致しなければ拒否される)。

---

## 3. 段 2 プランの provisional 裁定 (P1〜P5) への裁定

| provisional | 段 2 の判断 | 親の裁定 |
|---|---|---|
| P1 = 1 cluster は 36 性能 run | 採用 | **採用。**両レンズが独立に、位置 2 回 / 直前 arm 2 回の数え上げから確認した (`DW-G03` の独立 2 例に相当)。`record-items.md` の 6 件は誤り |
| P2 = 3 次元 Hotelling | 式は正しいが不採用 | **段 2 の判断を採る。**`(N,D)` の 2 次元 region と `H` の片側 region を共通 `q` で束ね、union bound で被覆 `≥ 1−α_k` を確保する。理由は「3 次元は primary が使わない方向まで覆い、不要に広い `q` を課す」。**ただし `q` を union bound の最小根で定める点は保守側なので採る** |
| P3 = `b01` 非依存の spending | 採用 | **採用。**`α_k = 0.05/[k(k+1)]`、`Σ = 0.05`、本 study は `k=1` で `α₁ = 0.025`。ただし root の同定は裁定 R3 |
| P4 = simulation は pilot 前、失敗時 DNF | 採用 | **採用。ただし意味は裁定 R2 で確定する。**「較正」と呼べるかがレンズ A の争点 |
| P5 = 割当て外 build が主経路 | 修正採用 (verification allocation を 26 本へ算入、main 予備を 3→2) | **採用。**core §11 は「8+2+13+3」を**目安**とし固定は 26 だけなので、内訳変更は core と矛盾しない |

## 4. 変異事前登録 (`DW-M01`)

**本 wave の実装差分はゼロ**である (コード・テスト・機械配線を 1 行も足さない)。
`DW-S04` の免除条項に従い、**変異 matrix は射程外**とする。
**受入全走は免除しない** — 実 repo を読むテストがあるので段 7 の記録前に実走する。

## 5. 段 5 の形

docs-only のため実装子を起動しない。親が次の 4 本を書く。

| 成果物 | 内容 |
|---|---|
| `addendum-a.md` | `a01`〜`a13` を**それだけ**設定した追補 A の**案**。従属先 core の三つ組を明記。自己 digest は書かない |
| `erratum-core-s15.md` | §15 要件 5 と「通る正例」の `a01`〜`a12` を `a01`〜`a13` へ supersede する**案** |
| `record-items.md` | 受領証 closed schema の**確定案** (36 run 訂正 + nested 追加要件) |
| `package.md` | 裁定 R1〜R5 と凍結可否をユーザーへ返す確定パッケージ |

すべて `authority: none` / `default_effect: no-state-change` を持ち、**凍結しない**。
worklog へ書く状態名は B10 に従い 3 段階に分ける。

## 6. ユーザー裁定へ返す 5 件 (`package.md` が正本)

| ID | 論点 | 親の推奨 |
|---|---|---|
| R1 | erratum を resolver / `PreregBinding` / 受領証へどう束縛するか (D234 署名の改訂を伴う) | one-off exact replacement (core digest 束縛、supersede 箇所を 2 つに限定) |
| R2 | `a12` を「正規 planning model 下の stress check」と呼び替えるか、cluster 効果込みの worst-case 較正へ変えるか | 呼び替え + 限定の明記 |
| R3 | primary 系列の正規の根と ordinal を `a13` (pilot 前) へ移すか、`b03` (本走前) のままにするか | `a13` へ移す |
| R4 | `a03` の閾値を未実測の fail-closed 規範値として承認するか、凍結前に非 study の環境 probe を要求するか | **環境 probe を先に走らせる** (`DW-G01` の生死実験先行) |
| R5 | core §4 の Fieller 同値の文言へ第 2 の erratum を当てるか | 当てない (primary は §5 first-match が守っている)。将来の別 study で新 core を起こすときに直す |
