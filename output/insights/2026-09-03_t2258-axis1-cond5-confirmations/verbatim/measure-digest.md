# 実測 3 — production の primary_key_digest 定義の再現と独立再走の一致検査

probe の逐語ソースは `probe-src.md`。repo 外の使い捨て probe の出力であり、
入力は凍結 bundle `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` と
repo 内の `2026-09-02-axis1-search-catalog.json` だけである。

**`gap` は `申告総数 - distinct` の差そのものであって「取りこぼした件数」ではない。**
その解釈は本 bundle からは支持されない (正本文書 §2.3)。

```text
=== primary_key_digest (production 定義の再現) ===
AX1-20260902-E1-Q1@openalex a01: pages=4 distinct=736 digest=6f59704dae82329eaecae2333843b5ef4ded955ab100d37992c5bf7cd5ea727f
AX1-20260902-E1-Q1@openalex a02: pages=4 distinct=735 digest=01db82426a3d8430503625ee0f9d6676107a9a0d062604dfaf2e69986fb349ac
AX1-20260902-E1-Q2@openalex a01: pages=9 distinct=1605 digest=80ae633e938cede45c6a9b9be872bc20f9fbd632a4bd016f07a0405a8459f6a2
AX1-20260902-E1-Q2@openalex a02: pages=9 distinct=1606 digest=1402d9fa6a4f0d5d67290e108ed45de8c9e73e74b5a6a29b6c313e25eeb0662c
AX1-20260902-E1-Q3-SPRE1991@openalex a01: pages=5 distinct=951 digest=21d11e1fe8bf8672760280f4d8b01e460cab7c685ef9725b13bcfc05750d008c
AX1-20260902-E1-Q3-SY1991@openalex a01: pages=1 distinct=117 digest=45e9c788491fc6bdb749f4c9b49f26b2500ee1d601b47d545c5e5136ef782e08
AX1-20260902-E1-Q3-SY1992@openalex a01: pages=1 distinct=187 digest=d2ee1779d6340b5076ef592952bf3c991e4c5ea98507cdd0f8bfd6885f215834
AX1-20260902-E1-Q3-SY1993@openalex a01: pages=1 distinct=175 digest=bd0b667adffd286ff2aca1a7e01f65676b0366649a62a52e865fa028d2a8fb4b
AX1-20260902-E1-Q3-SY1994@openalex a01: pages=1 distinct=166 digest=227d96da4a0294e67a05c84e581b5dd0d63d7d725f58bfbb2689d25a9443c60a
AX1-20260902-E1-Q3-SY1995@openalex a01: pages=1 distinct=182 digest=c86647b4a67aae44f7a0e4c6996b74795b4172f61ce11065731f0583a7b1274c
AX1-20260902-E1-Q3-SY1996@openalex a01: pages=1 distinct=194 digest=2fa89db9c6f7b700efbfd3ba6c4d22213d0ac7b5e6aaa3b36ef91e5a895edea4
AX1-20260902-E1-Q4@openalex a01: pages=24 distinct=4694 digest=825884229687b5fc4f51e835fbe78d4f6992eef904713c769f2832ec8e79edff
AX1-20260902-E1-Q5@openalex a01: pages=31 distinct=6116 digest=d59d3bb73fe4f701b20804e3144cb24c2a950513825e501daf4cd5cd19b7efab
AX1-20260902-E1-Q6-SPRE1991@openalex a01: pages=1 distinct=53 digest=c44986414b55adbc04c3892f7e6b4ca29f1c7b7fb15de97a3a5191e7ae5b8139

=== 独立再走の digest 一致 (条件 5 の第 2 走要求と同じ関数) ===
AX1-20260902-E1-Q1@openalex: pages=4 a01==a02 -> MISMATCH
AX1-20260902-E1-Q2@openalex: pages=9 a01==a02 -> MISMATCH

=== 頁数と gap の対応 (gap = declared - distinct) ===
gap は差そのものであって『取りこぼした件数』ではない。
その解釈には失敗走の申告母集合が固定されていることが要り、本 bundle からは言えない。
AX1-20260902-E1-Q1@openalex a01: pages=4 declared=736 distinct=736 gap=0
AX1-20260902-E1-Q1@openalex a02: pages=4 declared=736 distinct=735 gap=1
AX1-20260902-E1-Q2@openalex a01: pages=9 declared=1606 distinct=1605 gap=1
AX1-20260902-E1-Q2@openalex a02: pages=9 declared=1606 distinct=1606 gap=0
AX1-20260902-E1-Q3-SPRE1991@openalex a01: pages=5 declared=951 distinct=951 gap=0
AX1-20260902-E1-Q3-SY1991@openalex a01: pages=1 declared=117 distinct=117 gap=0
AX1-20260902-E1-Q3-SY1992@openalex a01: pages=1 declared=187 distinct=187 gap=0
AX1-20260902-E1-Q3-SY1993@openalex a01: pages=1 declared=175 distinct=175 gap=0
AX1-20260902-E1-Q3-SY1994@openalex a01: pages=1 declared=166 distinct=166 gap=0
AX1-20260902-E1-Q3-SY1995@openalex a01: pages=1 declared=182 distinct=182 gap=0
AX1-20260902-E1-Q3-SY1996@openalex a01: pages=1 declared=194 distinct=194 gap=0
AX1-20260902-E1-Q4@openalex a01: pages=24 declared=4698 distinct=4694 gap=4
AX1-20260902-E1-Q5@openalex a01: pages=31 declared=6122 distinct=6116 gap=6
AX1-20260902-E1-Q6-SPRE1991@openalex a01: pages=1 declared=53 distinct=53 gap=0

1 頁 leaf: 7/7 走が gap 0 (保証ではなく、この bundle での観測)
多頁 leaf: 3/7 走が gap 0 (保証ではなく、この bundle での観測)
```
