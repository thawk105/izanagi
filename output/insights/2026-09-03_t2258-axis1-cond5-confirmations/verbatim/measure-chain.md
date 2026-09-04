# 実測 6 — page evidence の field による走の連続性・独立性検査

probe の逐語ソースは `probe-src.md`。repo 外の使い捨て probe の出力であり、
入力は凍結 bundle `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` と
repo 内の `2026-09-02-axis1-search-catalog.json` だけである。

**`gap` は `申告総数 - distinct` の差そのものであって「取りこぼした件数」ではない。**
その解釈は本 bundle からは支持されない (正本文書 §2.3)。

```text
評価対象の走: 14
AX1-20260902-E1-Q1@openalex a01: 頁数=4 pass=1 attempt=1 先頭='*' -> OK
AX1-20260902-E1-Q1@openalex a02: 頁数=4 pass=1 attempt=2 先頭='*' -> OK
AX1-20260902-E1-Q2@openalex a01: 頁数=9 pass=1 attempt=1 先頭='*' -> OK
AX1-20260902-E1-Q2@openalex a02: 頁数=9 pass=1 attempt=2 先頭='*' -> OK
AX1-20260902-E1-Q3-SPRE1991@openalex a01: 頁数=5 pass=1 attempt=1 先頭='*' -> OK
AX1-20260902-E1-Q3-SY1991@openalex a01: 頁数=1 pass=1 attempt=1 先頭='*' -> OK
AX1-20260902-E1-Q3-SY1992@openalex a01: 頁数=1 pass=1 attempt=1 先頭='*' -> OK
AX1-20260902-E1-Q3-SY1993@openalex a01: 頁数=1 pass=1 attempt=1 先頭='*' -> OK
AX1-20260902-E1-Q3-SY1994@openalex a01: 頁数=1 pass=1 attempt=1 先頭='*' -> OK
AX1-20260902-E1-Q3-SY1995@openalex a01: 頁数=1 pass=1 attempt=1 先頭='*' -> OK
AX1-20260902-E1-Q3-SY1996@openalex a01: 頁数=1 pass=1 attempt=1 先頭='*' -> OK
AX1-20260902-E1-Q4@openalex a01: 頁数=24 pass=1 attempt=1 先頭='*' -> OK
AX1-20260902-E1-Q5@openalex a01: 頁数=31 pass=1 attempt=1 先頭='*' -> OK
AX1-20260902-E1-Q6-SPRE1991@openalex a01: 頁数=1 pass=1 attempt=1 先頭='*' -> OK

全走が先頭からの首尾一貫した独立走として検査を通った
```
