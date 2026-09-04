# 実測 1 — leaf ごとの rows / distinct / 申告総数 / 重複内訳と、attempt 間の集合差

probe の逐語ソースは `probe-src.md`。repo 外の使い捨て probe の出力であり、
入力は凍結 bundle `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` と
repo 内の `2026-09-02-axis1-search-catalog.json` だけである。

**`gap` は `申告総数 - distinct` の差そのものであって「取りこぼした件数」ではない。**
その解釈は本 bundle からは支持されない (正本文書 §2.3)。

```text
runs: 14
AX1-20260902-E1-Q1@openalex a01: pages=4 rows=736 distinct=736 declared=[736] dup_occ=0 boundary_pairs=0 within_page=0 nonadjacent=0 distinct-declared=0
AX1-20260902-E1-Q1@openalex a02: pages=4 rows=735 distinct=735 declared=[736] dup_occ=0 boundary_pairs=0 within_page=0 nonadjacent=0 distinct-declared=-1
AX1-20260902-E1-Q2@openalex a01: pages=9 rows=1607 distinct=1605 declared=[1606] dup_occ=2 boundary_pairs=2 within_page=0 nonadjacent=0 distinct-declared=-1
AX1-20260902-E1-Q2@openalex a02: pages=9 rows=1610 distinct=1606 declared=[1606] dup_occ=4 boundary_pairs=4 within_page=0 nonadjacent=0 distinct-declared=0
AX1-20260902-E1-Q3-SPRE1991@openalex a01: pages=5 rows=952 distinct=951 declared=[951] dup_occ=1 boundary_pairs=1 within_page=0 nonadjacent=0 distinct-declared=0
AX1-20260902-E1-Q3-SY1991@openalex a01: pages=1 rows=117 distinct=117 declared=[117] dup_occ=0 boundary_pairs=0 within_page=0 nonadjacent=0 distinct-declared=0
AX1-20260902-E1-Q3-SY1992@openalex a01: pages=1 rows=187 distinct=187 declared=[187] dup_occ=0 boundary_pairs=0 within_page=0 nonadjacent=0 distinct-declared=0
AX1-20260902-E1-Q3-SY1993@openalex a01: pages=1 rows=175 distinct=175 declared=[175] dup_occ=0 boundary_pairs=0 within_page=0 nonadjacent=0 distinct-declared=0
AX1-20260902-E1-Q3-SY1994@openalex a01: pages=1 rows=166 distinct=166 declared=[166] dup_occ=0 boundary_pairs=0 within_page=0 nonadjacent=0 distinct-declared=0
AX1-20260902-E1-Q3-SY1995@openalex a01: pages=1 rows=182 distinct=182 declared=[182] dup_occ=0 boundary_pairs=0 within_page=0 nonadjacent=0 distinct-declared=0
AX1-20260902-E1-Q3-SY1996@openalex a01: pages=1 rows=194 distinct=194 declared=[194] dup_occ=0 boundary_pairs=0 within_page=0 nonadjacent=0 distinct-declared=0
AX1-20260902-E1-Q4@openalex a01: pages=24 rows=4705 distinct=4694 declared=[4698] dup_occ=11 boundary_pairs=11 within_page=0 nonadjacent=0 distinct-declared=-4
AX1-20260902-E1-Q5@openalex a01: pages=31 rows=6130 distinct=6116 declared=[6122] dup_occ=14 boundary_pairs=14 within_page=0 nonadjacent=0 distinct-declared=-6
AX1-20260902-E1-Q6-SPRE1991@openalex a01: pages=1 rows=53 distinct=53 declared=[53] dup_occ=0 boundary_pairs=0 within_page=0 nonadjacent=0 distinct-declared=0

=== cross-attempt comparison ===
AX1-20260902-E1-Q1@openalex: |a01|=736 |a02|=735 inter=735 only_a01=1 only_a02=0 declared_a01=[736] declared_a02=[736]
    only in a01: https://openalex.org/W7168152262
AX1-20260902-E1-Q2@openalex: |a01|=1605 |a02|=1606 inter=1605 only_a01=0 only_a02=1 declared_a01=[1606] declared_a02=[1606]
    only in a02: https://openalex.org/W7161158986
```
