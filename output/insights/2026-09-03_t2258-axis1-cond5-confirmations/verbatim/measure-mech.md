# 実測 2 — 頁ごとの first / last / next_cursor、境界重複の位置、差分 ID の素性

probe の逐語ソースは `probe-src.md`。repo 外の使い捨て probe の出力であり、
入力は凍結 bundle `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` と
repo 内の `2026-09-02-axis1-search-catalog.json` だけである。

**`gap` は `申告総数 - distinct` の差そのものであって「取りこぼした件数」ではない。**
その解釈は本 bundle からは支持されない (正本文書 §2.3)。

```text
=== AX1-20260902-E1-Q1@openalex a01 pages=4 ===
  p0: n=200 first=https://openalex.org/W2116145395 last=https://openalex.org/W7166594119 next_cursor="[8.014954, 1782691200000, 'https://openalex.org/W7166594119']"
  p1: n=200 first=https://openalex.org/W4399939767 last=https://openalex.org/W4285061198 next_cursor="[2.3634818, 1640995200000, 'https://openalex.org/W4285061198']"
  p2: n=200 first=https://openalex.org/W4402823926 last=https://openalex.org/W7168152262 next_cursor="[0.90241885, 1779235200000, 'https://openalex.org/W7168152262']"
  p3: n=136 first=https://openalex.org/W4245691793 last=https://openalex.org/W7204093479 next_cursor=None

=== AX1-20260902-E1-Q1@openalex a02 pages=4 ===
  p0: n=200 first=https://openalex.org/W2116145395 last=https://openalex.org/W7166594119 next_cursor="[8.014954, 1782691200000, 'https://openalex.org/W7166594119']"
  p1: n=200 first=https://openalex.org/W4399939767 last=https://openalex.org/W4285061198 next_cursor="[2.3634818, 1640995200000, 'https://openalex.org/W4285061198']"
  p2: n=200 first=https://openalex.org/W4402823926 last=https://openalex.org/W4245691793 next_cursor="[0.902214, 1295308800000, 'https://openalex.org/W4245691793']"
  p3: n=135 first=https://openalex.org/W7118609440 last=https://openalex.org/W7204093479 next_cursor=None

=== AX1-20260902-E1-Q2@openalex a01 pages=9 ===
  p0: n=200 first=https://openalex.org/W2116145395 last=https://openalex.org/W4417215361 next_cursor="[13.70483, 1763424000000, 'https://openalex.org/W4417215361']"
  p1: n=200 first=https://openalex.org/W7137872824 last=https://openalex.org/W4416238713 next_cursor="[7.013113, 1762992000000, 'https://openalex.org/W4416238713']"
  p2: n=200 first=https://openalex.org/W7118580657 last=https://openalex.org/W2153583326 next_cursor="[4.833924, 1041379200000, 'https://openalex.org/W2153583326']"
  p3: n=200 first=https://openalex.org/W4226124328 last=https://openalex.org/W4312460971 next_cursor="[1.2093778, 1640995200000, 'https://openalex.org/W4312460971']"
  p4: n=200 first=https://openalex.org/W4414648397 last=https://openalex.org/W7126211752 next_cursor="[0.88342386, 1769644800000, 'https://openalex.org/W7126211752']"
  p5: n=200 first=https://openalex.org/W4416085123 last=https://openalex.org/W3089320326 next_cursor="[0.7657841, 1600819200000, 'https://openalex.org/W3089320326']"
  p6: n=200 first=https://openalex.org/W4416854470 last=https://openalex.org/W7155574501 next_cursor="[0.6260532, 1776816000000, 'https://openalex.org/W7155574501']"
  p7: n=200 first=https://openalex.org/W2477151755 last=https://openalex.org/W4360962380 next_cursor="[0.068376064, 1679616000000, 'https://openalex.org/W4360962380']"
  p8: n=7 first=https://openalex.org/W4404316278 last=https://openalex.org/W4402983529 next_cursor=None
  DUP across p0/p1: https://openalex.org/W7137872824 posA=198/200 posB=0/200
  DUP across p5/p6: https://openalex.org/W3089320326 posA=199/200 posB=1/200

=== AX1-20260902-E1-Q2@openalex a02 pages=9 ===
  p0: n=200 first=https://openalex.org/W2116145395 last=https://openalex.org/W4417215361 next_cursor="[13.70483, 1763424000000, 'https://openalex.org/W4417215361']"
  p1: n=200 first=https://openalex.org/W7128724798 last=https://openalex.org/W7108955742 next_cursor="[7.006365, 1764806400000, 'https://openalex.org/W7108955742']"
  p2: n=200 first=https://openalex.org/W7118580657 last=https://openalex.org/W2153583326 next_cursor="[4.8337383, 1041379200000, 'https://openalex.org/W2153583326']"
  p3: n=200 first=https://openalex.org/W4226124328 last=https://openalex.org/W4312460971 next_cursor="[1.2089183, 1640995200000, 'https://openalex.org/W4312460971']"
  p4: n=200 first=https://openalex.org/W4414648397 last=https://openalex.org/W7126211752 next_cursor="[0.88342386, 1769644800000, 'https://openalex.org/W7126211752']"
  p5: n=200 first=https://openalex.org/W4403570593 last=https://openalex.org/W4320165707 next_cursor="[0.76776505, 1675900800000, 'https://openalex.org/W4320165707']"
  p6: n=200 first=https://openalex.org/W4290727263 last=https://openalex.org/W7164850278 next_cursor="[0.6265937, 1781481600000, 'https://openalex.org/W7164850278']"
  p7: n=200 first=https://openalex.org/W7155574501 last=https://openalex.org/W4401567087 next_cursor="[0.08617169, 1704067200000, 'https://openalex.org/W4401567087']"
  p8: n=10 first=https://openalex.org/W4401567087 last=https://openalex.org/W4320718809 next_cursor=None
  DUP across p1/p2: https://openalex.org/W7108955742 posA=199/200 posB=1/200
  DUP across p4/p5: https://openalex.org/W4403570593 posA=188/200 posB=0/200
  DUP across p4/p5: https://openalex.org/W7126211752 posA=199/200 posB=1/200
  DUP across p7/p8: https://openalex.org/W4401567087 posA=199/200 posB=0/10

AX1-20260902-E1-Q1@openalex only-a01 https://openalex.org/W7168152262: page=2 ordinal=199/200 rel=0.90241885 pubdate=2026-05-20 created=2026-07-14T00:00:00 updated=2026-07-14T05:52:30
    title=Functor Reasoning Models: A Sheaf-Theoretic Alternative to Chain-of-Thought Inference
AX1-20260902-E1-Q2@openalex only-a02 https://openalex.org/W7161158986: page=7 ordinal=1/200 rel=0.626107 pubdate=2026-05-13 created=2026-05-15T00:00:00 updated=2026-07-28T07:46:37
    title=Good Agentic Friends Do Not Just Give Verbal Advice: They Can Update Your Weights
```
