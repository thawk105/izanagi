# 実測 7 — 凍結実行記録・checkpoint・catalog との照合と、条件 5 の現在の状態

probe の逐語ソースは `probe-src.md`。repo 外の使い捨て probe の出力であり、
入力は凍結 bundle `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` と
repo 内の `2026-09-02-axis1-search-catalog.json` だけである。

**`gap` は `申告総数 - distinct` の差そのものであって「取りこぼした件数」ではない。**
その解釈は本 bundle からは支持されない (正本文書 §2.3)。

```text
=== 1. 凍結実行記録 §3 の表との照合 ===
AX1-20260902-E1-Q1@openalex a01: 記録=(736, 736, 736, 0) probe=(736, 736, 736, 0) -> 一致
AX1-20260902-E1-Q2@openalex a01: 記録=(1606, 1607, 1605, 2) probe=(1606, 1607, 1605, 2) -> 一致
AX1-20260902-E1-Q4@openalex a01: 記録=(4698, 4705, 4694, 11) probe=(4698, 4705, 4694, 11) -> 一致
AX1-20260902-E1-Q5@openalex a01: 記録=(6122, 6130, 6116, 14) probe=(6122, 6130, 6116, 14) -> 一致
照合対象 4 件: 全件一致

=== 2. checkpoint の production digest との照合 ===
000001.json AX1-20260902-E1-Q3-SPRE1991@openalex: production=21d11e1fe8bf8672… probe=21d11e1fe8bf8672… -> 一致
000002.json AX1-20260902-E1-Q6-SPRE1991@openalex: production=c44986414b55adbc… probe=c44986414b55adbc… -> 一致
000003.json AX1-20260902-E1-Q3-SY1991@openalex: production=45e9c788491fc6bd… probe=45e9c788491fc6bd… -> 一致
000004.json AX1-20260902-E1-Q3-SY1992@openalex: production=d2ee1779d6340b50… probe=d2ee1779d6340b50… -> 一致
000005.json AX1-20260902-E1-Q3-SY1993@openalex: production=bd0b667adffd286f… probe=bd0b667adffd286f… -> 一致
000006.json AX1-20260902-E1-Q3-SY1994@openalex: production=227d96da4a0294e6… probe=227d96da4a0294e6… -> 一致
000007.json AX1-20260902-E1-Q3-SY1995@openalex: production=c86647b4a67aae44… probe=c86647b4a67aae44… -> 一致
000008.json AX1-20260902-E1-Q3-SY1996@openalex: production=2fa89db9c6f7b700… probe=2fa89db9c6f7b700… -> 一致
照合対象 8 件: 全件一致

=== 3. catalog の leaf 件数と independent_pass_required ===
OpenAlex の論理 query: 80 件 (内訳 {'leaf': 78, 'aggregate': 2})
  independent_pass_required=True : 76 件
  independent_pass_required=False: 4 件
  False の内訳:
    AX1-20260902-E1-Q1@openalex
    AX1-20260902-E1-Q2@openalex
    AX1-20260902-E1-Q4@openalex
    AX1-20260902-E1-Q5@openalex
登録 leaf: 78 件 / 走行のある leaf: 12 件 / 未走 leaf: 66 件

=== 4. 条件 5 の現在の状態 (検査器は最後の attempt を採る) ===
gap = declared - distinct。最後の attempt の gap が 0 でない leaf が現在の不成立である。
AX1-20260902-E1-Q1@openalex: 最終 attempt=a02 gap=1  <- 条件 5 不成立
AX1-20260902-E1-Q2@openalex: 最終 attempt=a02 gap=0
AX1-20260902-E1-Q3-SPRE1991@openalex: 最終 attempt=a01 gap=0
AX1-20260902-E1-Q3-SY1991@openalex: 最終 attempt=a01 gap=0
AX1-20260902-E1-Q3-SY1992@openalex: 最終 attempt=a01 gap=0
AX1-20260902-E1-Q3-SY1993@openalex: 最終 attempt=a01 gap=0
AX1-20260902-E1-Q3-SY1994@openalex: 最終 attempt=a01 gap=0
AX1-20260902-E1-Q3-SY1995@openalex: 最終 attempt=a01 gap=0
AX1-20260902-E1-Q3-SY1996@openalex: 最終 attempt=a01 gap=0
AX1-20260902-E1-Q4@openalex: 最終 attempt=a01 gap=4  <- 条件 5 不成立
AX1-20260902-E1-Q5@openalex: 最終 attempt=a01 gap=6  <- 条件 5 不成立
AX1-20260902-E1-Q6-SPRE1991@openalex: 最終 attempt=a01 gap=0
現在 条件 5 が不成立の leaf: 3 件 -> ['AX1-20260902-E1-Q1@openalex', 'AX1-20260902-E1-Q4@openalex', 'AX1-20260902-E1-Q5@openalex']
```
