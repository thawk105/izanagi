# [T-139] 本走の設計 — 段 4 裁定 (2026-08-07)

```text
authority: none
default_effect: no-state-change
```

段 2 プラン (`s2-plan.md`)、段 3 レンズ A (`s3-lensA.md`) / レンズ B (`s3-lensB.md`) の
全所見を real / refuted と scope 内 / 外へ裁定する。**両レンズとも NO-GO。段 2 自身も NO-GO。**
本 wave は `DW-S04` に従い**実装しない**と裁定する (`4→7→8→9`)。実装差分がないため
変異 matrix と受入全走は射程外である。

## 0. 親の誤り (すべて real。凍結 brief は書き換えず本書を正とする)

- **E1 (受理条件の書き落とし)。** brief (P3) は primary を `N>0 ∧ D>δ_D` の 2 条件としたが、
  裁定済みの受理条件は **`D > δ_D` かつ `N > 0` かつ `G > 0` の同時信頼領域**である。
  正本は worklog (142) と package.md Q9 であり、**D162 ではない** (段 2 の引用も同じ誤り。
  レンズ B 所見 6 が両方を訂正した)。`D = N + G` なので 2 条件では `G ≤ 0`、すなわち
  `RF ≥ 1` の stock 超過候補を排除できない。段 2 が示した W2 の負例が実際の反例である。
- **E2 (標準化効果の量の取り違え)。** brief は「W1 は N=93,373 に対し within sd 4,009」と書いたが、
  4,009 は **modeX arm 単体の sd** であり、paired contrast `N = modeX − mode1` の sd は
  **5,175** である。親が再計算して確認した。訂正後の within-cluster 標準化効果は
  W1 `N` 18.04 / `D` 69.72 / `G` 106.34、W2 `N` 42.14 / `D` 126.93 / `G` 98.70。
- **E3 (D162 発火条件の誤読)。実測で覆った。** brief と handoff は「発火条件 (i)(ii) は
  request `892042` で成立、残るは (iii) consumer だけ」と書いたが、**誤りである**。
  親が artifact を全文検索したところ、**`env_tag` も `attestation` も hit 0 件**であった。
  (ii) は「環境タグ・測定 checkout・pin・attestation」の連言であり、checkout
  (`preregistration-witness.tsv` の `repo_head` / `ccbench_head`) と pin
  (`dependency-witness.tsv`) はあるが、前 2 者が無いので **(ii) は未成立**である。
  レンズ B 所見 1 が real。
- **E4 (親が段 3 の後に見つけた新事実。両レンズと段 2 のいずれも触れていない)。**
  段 2 は 9 層すべてを `[new]` と見積もり「実装被覆 0/9」としたが、**過大見積りである**。
  `orchestrator/qualification/` に T-126 環境適格性のために作られた
  `attempt_ledger.py` (「Create-only, series-global submission and attempt ledger」)、
  `series.py` (series FSM + hash ledger)、`qsub_binding.py`、`atomic_publish.py`、
  `identity.py`、`submission.py` が既に存在し、Q10 が要求する
  「measurement-start receipt・全 attempt の双射・親系列 ID」に構造的に対応する。
  **D162 決定 (8) が禁じたのは T-126 の *artifact* を 3 arm 正例と読み替えることであって、
  *コード* の再利用ではない。** 再利用するか fork するかは設計択一だが、
  「ゼロから 9 層」を前提にした費用・順序の見積りは作り直す必要がある。
- **E5 (E3 の緩和。親が実測)。** ただし `env_tag` の**機構は既に存在する**。
  `orchestrator/qualification/contract.py` は `env_tag: "pegasus"` と
  `attestation_mode: "required"` を exact 契約として持つ ([T-296] は (162) で閉じている)。
  **欠けているのは機構ではなく、probe がそれを発行していないことだけ**である。
  これは後述の順序裁定を大きく変える。

## 1. レンズ A (統計的妥当性) の裁定

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| 1 | brief P3 は stock 超過を認証しうる | **real** | 採用 = E1。primary を 3 条件へ固定 |
| 2 | `d_plan` の bound は 6 成分同時の下限でない | **real** | 採用。`γ` の向きの曖昧さも real |
| 3 | simulation の 99% LCB は真の検出力の下限でない | **real** | 採用。J 選択後の同時保証も欠く |
| 4 | `d_plan=min(1,…)` と `design_not_feasible` の閉じ方 | **real** | 採用。終端状態として閉じる |
| 5 | 中央値に `σ_W²/r` は使えず `k≤0.408` は不整合 | **real** | 採用。arm 代表値は裁定項目 |
| 6 | 同時領域と Fieller は同一構成なら同値 | **real** | 採用。最重要の 1 つ (下記 §3) |
| 7 | `E[D−κS]>0` は Q2 の一解釈にすぎない | **real** | 採用。レンズ B 所見 4 と独立一致 |
| 8 | primary 失敗後の Holm 公表 | **real だが nit** | 採用。6 cell 全件固定公表で閉じる |
| 9 | 候補系列 alpha と cell family の接続が未閉 | **real** | 採用。裁定項目へ |
| 10 | J=11 と J=13 は別の power 目標 | **real** | 採用。裁定項目へ |
| 11 | within-cluster の巨大な d は cluster 間の根拠にならない | **real** | 採用 = E2 の一般化 |

**所見 6 の重み。** 同じ標本共分散と同じ臨界値 `q` から構成すれば、Fieller 集合の `r=0` 検査は
`N` の検査、`r=1` 検査は `−G` の検査である。したがって
「`LCB(N)>0 ∧ LCB(G)>0`」と「有界 Fieller 集合が `(0,1)` に含まれる」は**同値**であり、
段 2 の `statistical_inconsistency` 拒否は受理集合を 1 つも縮めない**恒真な保証**になる。
逆に別々の `q` や片側/両側規則を使えば正当な不一致が起きるが、それを raw 破損として拒否すると
偽陰性を増やす。izanagi が繰り返した「謳うだけで発火しない assert」の型である。

## 2. レンズ B (手続き整合と実行可能性) の裁定

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| 1 | D162 発火条件は (i) だけ成立 | **real** | 採用 = E3。ただし E5 で解法が変わる |
| 2 | `declared_use_class` は未確定名 | **real だが既裁定の手順内** | T-479 択 (b) が既に手順を決めている |
| 3 | D19 / roadmap の原子性が未履行 | **real** | 採用。ユーザー裁定 (協議改訂) へ |
| 4 | `E[D−κS]>0` は Q2 の一意な帰結でない | **real** | 採用。反例を親が検算した (下記) |
| 5 | `d_plan` が d≈1.0 を結果依存で引き下げる | **real** | 採用。最重要の 1 つ |
| 6 | brief P3 は裁定違反、引用先も誤り | **real** | 採用 = E1 |
| 7 | 受理述語に自己申告根の恒真相当 gate | **real** | 採用。裁定項目 + 変異必須 kill へ |
| 8 | `weak_denominator_not_certifiable` が未結線 | **real** | 採用。shape と status を別軸へ |
| 9 | 6 rep + washout が allocation 予算に収まらない | **real** | 採用 (親が walltime 3600 / deadline 3300 を実測確認) |
| 10 | point 単価の測定方法が成立しない | **real** | 採用。総額上限の先行裁定へ |
| 11 | queue 待ち中の HEAD 進行に成功経路がない | **real** | 採用。batch ごとの凍結 checkout へ |
| 12 | P1〜P6 の再判定と arm 中央値 | **real、nit** | 採用。P2 の書き分けを採る |

**所見 4 の反例を親が検算した。** `(S,D) = (100,10), (1000,50)`、`κ=0.06` のとき
`E[D/S] = (0.10+0.05)/2 = 7.5% > 6%` で pass、
`E[D−κS] = ((10−6) + (50−60))/2 = −3 < 0` で fail。**同じ raw から受理が反転する。**
Q2 の裁定文は「stock 比の相対量」までしか書いておらず、
ratio-of-means と mean-of-ratios のどちらかを閉じていない。**未裁定である。**

**所見 5 の重み。** 段 2 の `d_plan = min(1.0, min_k Δ⁻/σ⁺)` は、pilot の下側効果が小さければ
`d_plan < 1` となり J が増える。これは worklog (142) の裁定
「d=0.5 の約 42 cluster を最初から払う必要はない」と逆方向であり、
**結果を見て費用裁定を書き換える経路**になる。planning alternative は d=1.0 に固定し、
下回るなら `design_not_feasible` で終えるか、新しい費用裁定へ返す。

**所見 2 の縮約。** `declared_use_class` は T-479 択 (b) で「第一候補とし、実装 wave が
D75 一意性検査を通る名で新 D に確定する」と既に手順が裁定済みである。
未確定であること自体は正しいが、**新しい blocker ではない**。scope 内の既定手順で閉じる。

## 3. 親が確定させたこと (プラン v2 の骨子)

段 5・6 は行わないので、以下は**実装ではなく裁定パッケージの推奨**として `package.md` へ送る。

1. **primary は workload ごとに `N>0 ∧ H>0 ∧ G>0` の同時信頼領域**とし、両 workload の
   global IUT 1 本を primary とする (`H` は分母条件の contrast。その定義は裁定項目 U1)。
2. **Fieller は同じ同時領域の ratio projection として導出**し、`q` と truth table を共通化する。
   別手続きとして二重に課さない (レンズ A 所見 6)。境界閉表は `fieller_shape` と
   `qualification_status` を**別軸**にし、空集合の valid / 表現不整合を分離する (レンズ B 所見 8)。
3. **planning alternative は d=1.0 固定。** pilot は共分散・schedule・infra 率・
   point 単価の推定にだけ使い、`d` を動かさない (レンズ B 所見 5)。
4. **pilot は external・非 pool。** 段 2 の naive pooling 反例 (`.05125 > .05`) は real である。
   ただしレンズ B 所見 12 のとおり、これは全 internal-pilot 手法の不可能性証明ではない。
   非 pool を**防御的既定**として採る。
5. **順序は E5 が解く (親の新しい推奨)。** 下記 §4。
6. **受理述語には環境 attestation・allocation accounting・liveness・単独性を明示連言で入れ**、
   correctness は boolean を信用せず raw verifier evidence から再計算する (レンズ B 所見 7)。
   「失敗 request を registry と raw の双方から落とす」「新 family ID で alpha を reset する」
   「anomaly を clean と申告する」の 3 変異を必須 kill とする。

## 4. 順序についての親の裁定 (E5 に基づく。段 2 と両レンズの案を置き換える)

段 2 は「9 層 vertical slice を原子的に許可」、レンズ B は
「新 probe を先に取るか D162(10) を明示 supersede するか」を求めた。**どちらも不要である。**

`env_tag: "pegasus"` と `attestation_mode: "required"` の契約は既に存在する (E5)。
したがって **pilot 自身が D162 の発火条件を満たす計測になる**。

```text
段 A  producer を実装する (raw receipt schema を確定。env_tag / attestation /
      checkout / pin / 全 attempt / actual schedule / correctness evidence を含む。
      適格性 field は closed schema で拒否。既存 T-126 stack の再利用可否をここで裁定)
段 B  pilot を走らせる (J_p allocation)。この時点で D162(10) の (i) と (ii) が成立する
段 C  (i)(ii) 成立を根拠に validator と最初の trusted consumer を実装する (= (iii) が成立)
段 D  pilot から J を導き、本走の事前登録を commit してから本走を投入する
```

**この順序の利点。** (a) D162 を supersede しない — 発火条件を**満たしてから**機械化する
`DW-G04` の規律をそのまま守る。(b) schema 変更 risk が pilot に閉じる — pilot の推定値は
数値なので schema が変わっても使え、再走 risk のある allocation は本走 J 本だけになる。
(c) 段 C の実装時間が、pilot 完了から本走投入までの待ち時間に収まる。

**この順序の残る risk。** 段 A の schema が段 C の validator 要求を取りこぼすと、
pilot は数値としては使えても「(i)(ii) を満たす計測」としては使えず、段 B のやり直しになる。
これは段 2 が指摘した再走 risk の縮小版であり、**消えてはいない**。
段 A の schema 確定を単独の裁定 gate にすることで緩和する。

## 5. scope 外として実装しないもの

- コード・テスト・gate・schema・凍結 bytes は 1 byte も変更しない。
- roadmap §3.6 の改訂と D19 の適用前提の限定 (レンズ B 所見 3) は**協議改訂**であり、
  親が独断で行わない。裁定項目 U3 として返す。
- point 単価の実測 (レンズ B 所見 10) は本 wave では行わない。`rbudgetcheck` は group 単位で、
  親の実測時点で gen_S に 104 request が併存していたため、差分を [T-139] に帰属できない。

## 6. 成果物影響 (`DW-G05`)

本 wave は docs のみで、certified 選択・材料レポート・proof chain・凍結 bytes・既存 gate・
受理集合はいずれも不変である。変わるのは [T-139] の状態が
「本走の設計待ち」から「**設計は起草済み。11 件のユーザー裁定待ち + 段 A〜D の実装待ち**」へ
分解されたことと、D162 発火条件の充足状況について記録されていた事実認定が
(i) のみ成立へ訂正されたことである。
