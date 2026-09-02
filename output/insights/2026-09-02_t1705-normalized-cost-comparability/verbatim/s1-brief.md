# [T-1705] 段 1 brief — 正規化 cost の arm 間比較可能性を生成物へ書かせる

## 覆った前提 (段 4 で再裁定する)

依頼引数は「cost の値は生成されておらず、version の provenance が装置へ束縛されているだけ」と
述べるが、実測でこれは覆った。部分正規化 cost の計算器は 2026-08-25 に [T-1434] で landed 済みで、
`tools/codex_reasoning_ab.py` の `_normalized_cost_metadata` / `_normalized_cost_for_attempt` /
`_aggregate_normalized_costs` が `resource_ledger[].normalized_cost` と
`normalized_cost_axis_ledger` を Decimal 8 桁・ROUND_HALF_EVEN で生成する。事前登録 §10 も同じ。
**したがって本 wave の純増は、依頼の後半にある「生成した値がどの arm 間で比較可能かを、
生成物自身に書かせること」だけである。** repo 全体で該当する自己宣言は 0 件。

## scope

`normalized_cost` の生成物 (per-attempt 行と axis ledger 行) に、その値がどの他行と比較可能かを
機械可読で自己宣言させる。計算層の内側だけ。

## 確定済みユーザー裁定

- D932: 部分被覆の費用は記述統計として出し、certified field にも判定 gate にもしない。
  malformed 入力の拒否だけは残す。軸ごとの行へ観測済み・観測不能・非発生の内訳を機械可読で出す。
- D831: price version の信頼の起点はコード側の凍結 literal であり、schedule の自己申告ではない。
- 引数の指示: 仮想リスク向けの gate・検査・台帳・一般化は scope 外。規律 2 は緩めない。

## 不変条件

- 受理集合を変えない。新しい `ValidationError` を足さず、既存の失敗理由の文言・発火条件も変えない。
- 凍結 snapshot (`output/t189-routing-preregistration/price-snapshot-v1.json`) の bytes を変えない。
  固定 path・SHA-256・version literal も変えない。
- 比較可能性の宣言を gate・certified field にしない。`certification_status` は `not-certified`、
  `coverage_status` は `partial` のまま。
- verifier / correctness 側の経路には触れない。

## 成果物の形

axis ledger の各行と per-attempt の各 cost 行が、(a) 会計基盤の同一性を表す比較基準キー、
(b) その行の値が他行と同列に読めるか (合計の分母が揃うか) を、行自身から判定できる形で持つ。

## (P1) 親の provisional 裁定 — 攻撃対象

比較可能性は 2 段である。**基盤の一致**は `price_version`・`currency`・`price_unit`・
`unaccounted_token_categories`・`coverage_status`・rounding が全一致すること。**合計の可読性**は
さらに分母 (`attempt_count` と `scheduled_attempt_count` の関係) が揃うこと。前者だけを宣言すると、
欠測数の違う arm の `accounted_amount` が同列に読まれる。`unit_prices` は model ごとに違ってよく、
一致を要求してはならない (正規化の目的そのもの)。

## 実アンカー

| anchor | 内容 |
|---|---|
| `tools/codex_reasoning_ab.py:9795` | `_AXIS_FIELDS` (arm を含まない 5 軸) |
| `tools/codex_reasoning_ab.py:9916` | `_normalized_cost_metadata` — 会計基盤 field の生成点 |
| `tools/codex_reasoning_ab.py:9968` | `_normalized_cost_for_attempt` — per-attempt 行 |
| `tools/codex_reasoning_ab.py:10053` | `_aggregate_normalized_costs` — axis 行と arm の合成点 |
| `tools/codex_reasoning_ab.py:10682` | `resource_ledger[].normalized_cost` の書込点 |
| `tools/codex_reasoning_ab.py:10791` | `result["normalized_cost_axis_ledger"]` の書込点 |
| `orchestrator/tests/test_codex_reasoning_ab.py:15565` | 既存 cost テストの helper 起点 (最初の cost test は :15641。段 3 レンズ A の指摘で訂正) |

## 成果物影響 (DW-G05)

放置すると、欠測数の異なる arm 行の `accounted_amount` が同列の cost 比較として読まれる。
台帳の値は変わらないが、そこから導く arm 間の費用差が偽になる。宣言を行自身に持たせると、
読み手も下流も行だけで可否を判定できる。

## 分割方針

段 2 plan 1 本、段 3 敵対相談 2 本 (レンズ: 受理集合の非変更 / 比較可能性の意味論)、
段 5 Codex `role=author` 1 本、段 6 review 2 本 + fix。受理集合に隣接するため軽量版にしない。

## 実測環境

login node の pytest 焦点走と受入全走。計算ノード job は投入しない。
