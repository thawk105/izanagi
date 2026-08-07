# [T-139] 本走の設計 — 逐語 (dev-wave 2026-08-07)

```text
authority: none
default_effect: no-state-change
```

本ディレクトリは dev-wave `[T-139] 本走の設計` の逐語成果物である。可変状態の正本は
worklog 末尾、採用済み判断の正本は decisions であり、ここには凍結した逐語を置く。
**本文書は可変状態の正本ではない。**

## 結論 (先に読むこと)

- **本走はまだ投入できない。** 段 2 の起草子と段 3 の敵対レンズ 2 本が独立に NO-GO を返した。
  投入不可の理由は 3 つ — (a) allocation 間分散が J=1 の probe から 1 点も推定できず標本数を
  固定できない、(b) cluster 内 6 反復 + 待機が 1 時間の allocation に収まらない、
  (c) D162 の機械化発火条件が **(i) だけ成立**である。
- **ユーザー裁定 11 件へ分解した。** 正本は `package.md`。**U1 (分母条件の母数) と
  U2 (閾値 `κ_w`) が先**であり、これらが決まらないと他は形式的にしか決められない。
- **親の誤りが 5 件ある。うち 1 件は親が「実測で確認した」と報告した内容が誤りだった** (§訂正)。
- **着手順序について、段 2 と両レンズの案を親が置き換えた。** `producer → pilot →
  validator/consumer → 本走` とすれば **D162 を supersede せずに発火条件を満たせる**。

## ファイル

| file | 内容 |
|---|---|
| `README.md` | 本文書 |
| `brief.md` | 段 1 brief (凍結。書き換えない。誤りは §「訂正」を正とする) |
| `s2-plan.md` | 段 2 プラン起草 (codex read-only, reasoning=max) — NO-GO |
| `s3-lensA.md` | 段 3 敵対レンズ A = 統計的妥当性 — NO-GO、blocker 10 件 + nit 1 件 |
| `s3-lensB.md` | 段 3 敵対レンズ B = 手続き整合と実行可能性 — NO-GO、blocker 11 件 + nit 1 件 |
| `s4-adjudication.md` | 段 4 裁定 (real/refuted、親の誤り、プラン v2 の骨子) |
| `package.md` | **ユーザー裁定パッケージ (11 件)** |
| `preregistration-draft.md` | **事前登録の草案** (未確定箇所は `【U#】` で明示。事前登録ではない) |

## 1. 実測 (親が本 wave で取ったもの)

**probe `892042` の生データから算出した cluster 内のばらつき** (`throughput.tsv`):

| 量 | W1 平均 | W1 sd | W1 `平均/sd` | W2 平均 | W2 sd | W2 `平均/sd` |
|---|---:|---:|---:|---:|---:|---:|
| `N = modeX − mode1` | 93,373 | 5,175 | 18.04 | 1,359,501 | 32,259 | 42.14 |
| `D = stock − mode1` | 690,109 | 9,899 | 69.72 | 9,409,778 | 74,135 | 126.93 |
| `G = stock − modeX` | 596,737 | 5,612 | 106.34 | 8,050,277 | 81,566 | 98.70 |

rep 単位の paired 回復率: W1 sd 0.00575 (CV 4.25%)、W2 sd 0.00366 (CV 2.53%)、各 5 rep。

**これらはすべて 1 allocation 内の値である。** 本走の標本数を決めるのは allocation 間の分散であり、
**そこは J=1 のため 1 点も推定されていない。**

**資源** (2026-08-07): `rbudgetcheck` = SFC 残 5236.04 / 初期 6000。
`pegasusinfo` = gen_S は 104 request 中 31 running。
probe の walltime は 3600 秒、内部絶対期限は 3300 秒 (`t139_positive_control_probe.pbs`)。
**1 allocation あたりの point 消費は測れなかった** — 照会は group 単位で、104 request が
併存するため差分を当該 study に帰属できない。

**発火条件の照合** (`grep -rn "env_tag\|attestation" <artifact dir>` = **hit 0 件**):
request `892042` は測定 checkout (`preregistration-witness.tsv`) と pin
(`dependency-witness.tsv`) を持つが、**環境タグと環境証明を持たない**。

**機構の実在** (`orchestrator/qualification/contract.py`): `env_tag: "pegasus"` と
`attestation_mode: "required"` を exact 契約として持つ。**機構は既にある。**

## 2. 敵対検証が投入前に止めたもの

段 3 の 2 レンズが計 23 件の所見を返し、**親は全件を real と裁定した (refuted 0 件)。** 主なもの:

- **受理条件の 3 つ目 (`G>0`) の書き落とし** — 2 条件だけだと元の版を追い越した候補まで
  正例にできる。レンズ B が引用先の誤り (D162 ではなく Q9 / worklog (142)) も訂正した。
- **区間と同時領域を別構成で二重に課すと恒真な検査になる** — 同じ臨界値と共分散なら同値であり、
  受理集合を 1 つも縮めない。
- **分母条件 `E[D−κS]>0` は Q2 の一意な帰結ではない** — 両レンズが独立に指摘した。
  親が反例を検算: `(S,D)=(100,10),(1000,50)`、`κ=0.06` で比の平均は pass・総量の比は fail。
- **段 2 の `d_plan` は pilot 結果を見て目標効果量を引き下げる** — 裁定 (142) と逆方向で、
  結果を見て費用裁定を書き換える経路になる。
- **6 反復 + 待機が 1 時間の allocation に収まらない** — 現 probe は内部期限 3300 秒に対し
  最悪 3298 秒で余白 2 秒しかない。
- **受理述語に自己申告根の恒真相当 gate が 3 件** — 失敗投入を台帳と raw の双方から落とす、
  新しい親系列 ID で有意水準をリセットする、anomaly を clean と申告する。
- **queue 待ち中の HEAD 進行に成功経路がない** — 24 割当てを跨ぐ設計では batch ごとの
  凍結 checkout が要る。

## 3. 訂正 (親 brief の誤りを本 README が正とする)

- **訂正 1 (受理条件)。** `brief.md` (P3) は primary を `N>0 ∧ D>δ_D` の 2 条件としたが、
  裁定済みの受理条件は **`D > δ_D` かつ `N > 0` かつ `G > 0`** の 3 条件である。
  正本は worklog (142) と `package.md` (T-338) Q9。**D162 ではない。**
- **訂正 2 (標準化効果の量)。** `brief.md` の「W1 は N=93,373 に対し within sd 4,009」は誤り。
  4,009 は **modeX arm 単体**の sd で、paired contrast `N` の sd は **5,175** である
  (親が再計算)。訂正後も within-cluster の効果は極めて大きいが、
  **cluster 間設計の根拠にはならない。**
- **訂正 3 (D162 発火条件)。最も重い誤り。** `brief.md` と handoff とユーザーへの中間報告は
  「(i)(ii) は成立、残るは (iii) だけ」としたが、**(ii) は未成立**である (§1 の照合)。
  成立しているのは **(i) だけ**。詳細は `s4-adjudication.md` §0 の E3。
- **訂正 4 (実装被覆)。** 段 2 の「9 層すべて新規・被覆 0/9」は過大である。
  `orchestrator/qualification/` の T-126 用 stack が Q10 の要求に構造的に対応する
  (親が段 3 の後に発見。段 2 も両レンズも触れていない)。
- **訂正 5 (段 2 の予算数値)。** 段 2 は probe の worst-case を 3290 秒としたが、
  レンズ B の再計算では 3298 秒である。親は walltime 3600 / 内部期限 3300 を実測確認した。

## 4. 本書が主張しないこと

- 代替 X が適格である、とは主張しない。成立しているのは J=1 の engineering screen だけである。
- 推奨した標本数が正しい、とは主張しない。allocation 間のばらつきは未推定である。
- 機序の帰属はしない (3 変更を同時に入れたため。ablation は別 study)。
- 実装差分がないため、**変異 matrix と受入全走は射程外**である。
