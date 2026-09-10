# RF 正例 artifact 9 層の所在実測 — 2026-08-18

**この表は所在の実測であり、被覆の主張ではない。** 本 wave は 9 層を 1 層も実装していない
(D162 決定 (10)、D500 決定 (1)(2)(3))。列挙した実体はいずれも**別 protocol のもの**であり、
RF 正例 artifact の縦断被覆と読み替えてはならない。

層の定義は D162 が引く [T-339] の 9 層である。所在は段 2 プランと段 3 レンズ A が独立に測り、
食い違いは無かった。

| 層 | 実在する所在 | 判定 |
|---|---|---|
| 計測 producer | `orchestrator/campaign/pipeline.py`、`orchestrator/qualification/collector.py` | 実在するが campaign 評価と T-126 受領証のもの。RF receipt producer は**不在** |
| attempt registry | `orchestrator/qualification/attempt_ledger.py`、`s8b_floor_campaign.py` の私有 retry ordinal | T-126 / 床値用。RF の 3-arm registry では**ない** |
| schedule validator | `s8b_oracle_manifest.py`、呼び手 `s8b_oracle_driver.py` | oracle manifest 用。RF receipt へは**未接続** |
| RF calculator | `orchestrator/qualification/contract.py`、`series.py` | T-126 の relative 観測はある。RF calculator は**不在** |
| 適格性権威 | `s8b_floor_stats.py`、`s8b_oracle_judge.py` | 既存 floor / oracle の権威。RF artifact の authority では**ない** |
| 層 3 の次版 | `layer3_report.py` | 現行 report のみ。certified selection consumer は**未実装** |
| selector consumer | `s8b_selector_input.py`、`s8b_oracle_judge.py` | oracle selector はあるが RF artifact を**消費しない** |
| 材料レポート consumer | `layer3_report.py` | qualification lineage を**拒否する**既存 report のみ。RF consumer は不在 |
| 双射・変異検査 | `layer3_report.py`、`test_layer3_report.py`、`test_s8b_oracle_report.py` | 既存 protocol の検査。RF 用の双射・変異 matrix は**不在** |

## 被覆計画 (発火条件が揃ってからの順序)

D162 決定 (10) の発火条件は 3 点である。

1. 3 arm (stock / 劣化版 / 候補) を持ち、事前登録を実走前に commit した計測が 1 本以上存在する。
2. その計測が環境タグ・測定 checkout・CCBench pin・attestation を持つ。
3. RF decision を読む consumer の実 hook が実在する。

段 3 レンズ B の実測によれば、既存計測 `892042.nqsv` は条件 (i) だけを満たし、
環境タグと attestation を欠き、consumer hook は 0 件である
(一次資料 = `output/insights/2026-08-16_t338-rf-validator-trigger-audit/trigger-audit.md`)。
したがって発火条件は**未成立**である。

加えて D500 決定 (2) が、公表層とは別の閂として投入 gate (`PreregBinding` の非 export、
D264/D282) を同定した。**投入 gate が完成するまで受領証を書き出す producer は作れない。**
D500 決定 (3) は、その制約を引いた残余 (attempt registry + 純粋な組み立て + 否定検査) を
「producer 実装済み」として land することを名指しで禁じている。

よって被覆の順序は次になる。9 層の実装は最後尾であり、本 wave の射程外である。

1. 投入 gate の完成 (D264/D292 の解除権威はユーザーにある)。
2. 3 arm 計測の事前登録と実走 (条件 (i)(ii))。
3. RF decision を読む consumer hook の実在 (条件 (iii))。
4. 上記が揃って初めて 9 層の実装に着手する。

## 本 wave が動かしたもの / 動かしていないもの

**動かした:** campaign producer の種別宣言の機構と field 名。族の外延を宣言由来にした閉包検査。
D162 決定 (11) の land 禁止のうち campaign producer に関する部分の解除。

**動かしていない:** RF 9 層のいずれか、投入 gate、`PreregBinding`、凍結 artifact、
certified 選択の値、材料レポート、proof chain、既存 6 producer の出力 path。
