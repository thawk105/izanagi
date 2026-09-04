# 実測 4 — 申告総数の到達可能性と、非返却 record の境界位置

probe の逐語ソースは `probe-src.md`。repo 外の使い捨て probe の出力であり、
入力は凍結 bundle `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` と
repo 内の `2026-09-02-axis1-search-catalog.json` だけである。

**`gap` は `申告総数 - distinct` の差そのものであって「取りこぼした件数」ではない。**
その解釈は本 bundle からは支持されない (正本文書 §2.3)。

```text
=== 代替仮説の切り分け: 申告総数は到達可能か ===
同じ leaf の別の走が申告総数ちょうどの distinct を返していれば、
その申告総数は実在 record だけで満たせる = 幻の件数ではない。
AX1-20260902-E1-Q1@openalex: declared=736 最良 distinct=736 -> 到達可能 (幻でない)
AX1-20260902-E1-Q2@openalex: declared=1606 最良 distinct=1606 -> 到達可能 (幻でない)
AX1-20260902-E1-Q3-SPRE1991@openalex: declared=951 最良 distinct=951 -> 到達可能 (幻でない)
AX1-20260902-E1-Q3-SY1991@openalex: declared=117 最良 distinct=117 -> 到達可能 (幻でない)
AX1-20260902-E1-Q3-SY1992@openalex: declared=187 最良 distinct=187 -> 到達可能 (幻でない)
AX1-20260902-E1-Q3-SY1993@openalex: declared=175 最良 distinct=175 -> 到達可能 (幻でない)
AX1-20260902-E1-Q3-SY1994@openalex: declared=166 最良 distinct=166 -> 到達可能 (幻でない)
AX1-20260902-E1-Q3-SY1995@openalex: declared=182 最良 distinct=182 -> 到達可能 (幻でない)
AX1-20260902-E1-Q3-SY1996@openalex: declared=194 最良 distinct=194 -> 到達可能 (幻でない)
AX1-20260902-E1-Q4@openalex: declared=4698 最良 distinct=4694 -> 未到達 (幻を排除できない)
AX1-20260902-E1-Q5@openalex: declared=6122 最良 distinct=6116 -> 未到達 (幻を排除できない)
AX1-20260902-E1-Q6-SPRE1991@openalex: declared=53 最良 distinct=53 -> 到達可能 (幻でない)

=== 非返却 record は頁境界にあるか ===
AX1-20260902-E1-Q1@openalex a01 のみ https://openalex.org/W7168152262
    返した走での位置: 頁 2 の 199/200 (頁頭から 199、頁尾から 0) -> 境界隣接: True
    その走の score=0.90241885
    直前頁の cursor 鍵=[2.3634818, 1640995200000, 'https://openalex.org/W4285061198']
    この頁の cursor 鍵=[0.90241885, 1779235200000, 'https://openalex.org/W7168152262']
    落とした走の同じ境界付近の cursor 鍵:
      頁 1 -> [2.3634818, 1640995200000, 'https://openalex.org/W4285061198']
      頁 2 -> [0.902214, 1295308800000, 'https://openalex.org/W4245691793']
AX1-20260902-E1-Q2@openalex a02 のみ https://openalex.org/W7161158986
    返した走での位置: 頁 7 の 1/200 (頁頭から 1、頁尾から 198) -> 境界隣接: True
    その走の score=0.626107
    直前頁の cursor 鍵=[0.6265937, 1781481600000, 'https://openalex.org/W7164850278']
    この頁の cursor 鍵=[0.08617169, 1704067200000, 'https://openalex.org/W4401567087']
    落とした走の同じ境界付近の cursor 鍵:
      頁 6 -> [0.6260532, 1776816000000, 'https://openalex.org/W7155574501']
      頁 7 -> [0.068376064, 1679616000000, 'https://openalex.org/W4360962380']

=== 境界重複は隣接頁の末尾/先頭に集中するか ===
AX1-20260902-E1-Q2@openalex a01 頁0/1: https://openalex.org/W7137872824 前頁の頁尾から 1、次頁の頁頭から 0
AX1-20260902-E1-Q2@openalex a01 頁5/6: https://openalex.org/W3089320326 前頁の頁尾から 0、次頁の頁頭から 1
AX1-20260902-E1-Q2@openalex a02 頁1/2: https://openalex.org/W7108955742 前頁の頁尾から 0、次頁の頁頭から 1
AX1-20260902-E1-Q2@openalex a02 頁4/5: https://openalex.org/W4403570593 前頁の頁尾から 11、次頁の頁頭から 0
AX1-20260902-E1-Q2@openalex a02 頁4/5: https://openalex.org/W7126211752 前頁の頁尾から 0、次頁の頁頭から 1
AX1-20260902-E1-Q2@openalex a02 頁7/8: https://openalex.org/W4401567087 前頁の頁尾から 0、次頁の頁頭から 0
AX1-20260902-E1-Q3-SPRE1991@openalex a01 頁1/2: https://openalex.org/W2048310987 前頁の頁尾から 0、次頁の頁頭から 0
AX1-20260902-E1-Q4@openalex a01 頁2/3: https://openalex.org/W2935898307 前頁の頁尾から 0、次頁の頁頭から 0
AX1-20260902-E1-Q4@openalex a01 頁8/9: https://openalex.org/W4312590834 前頁の頁尾から 0、次頁の頁頭から 1
AX1-20260902-E1-Q4@openalex a01 頁9/10: https://openalex.org/W4402510380 前頁の頁尾から 3、次頁の頁頭から 2
AX1-20260902-E1-Q4@openalex a01 頁10/11: https://openalex.org/W3046753628 前頁の頁尾から 2、次頁の頁頭から 0
AX1-20260902-E1-Q4@openalex a01 頁12/13: https://openalex.org/W1493253787 前頁の頁尾から 0、次頁の頁頭から 0
AX1-20260902-E1-Q4@openalex a01 頁14/15: https://openalex.org/W7163686966 前頁の頁尾から 0、次頁の頁頭から 2
AX1-20260902-E1-Q4@openalex a01 頁15/16: https://openalex.org/W2951097601 前頁の頁尾から 2、次頁の頁頭から 3
AX1-20260902-E1-Q4@openalex a01 頁16/17: https://openalex.org/W7128478743 前頁の頁尾から 0、次頁の頁頭から 2
AX1-20260902-E1-Q4@openalex a01 頁18/19: https://openalex.org/W7168432258 前頁の頁尾から 0、次頁の頁頭から 1
AX1-20260902-E1-Q4@openalex a01 頁19/20: https://openalex.org/W7164357879 前頁の頁尾から 5、次頁の頁頭から 3
AX1-20260902-E1-Q4@openalex a01 頁21/22: https://openalex.org/W7119551616 前頁の頁尾から 0、次頁の頁頭から 0
AX1-20260902-E1-Q5@openalex a01 頁0/1: https://openalex.org/W2272535669 前頁の頁尾から 0、次頁の頁頭から 0
AX1-20260902-E1-Q5@openalex a01 頁6/7: https://openalex.org/W1964691382 前頁の頁尾から 0、次頁の頁頭から 0
AX1-20260902-E1-Q5@openalex a01 頁8/9: https://openalex.org/W2002016273 前頁の頁尾から 0、次頁の頁頭から 0
AX1-20260902-E1-Q5@openalex a01 頁9/10: https://openalex.org/W4221167659 前頁の頁尾から 0、次頁の頁頭から 0
AX1-20260902-E1-Q5@openalex a01 頁14/15: https://openalex.org/W2078161256 前頁の頁尾から 0、次頁の頁頭から 2
AX1-20260902-E1-Q5@openalex a01 頁15/16: https://openalex.org/W2068756387 前頁の頁尾から 0、次頁の頁頭から 1
AX1-20260902-E1-Q5@openalex a01 頁18/19: https://openalex.org/W2069437605 前頁の頁尾から 0、次頁の頁頭から 0
AX1-20260902-E1-Q5@openalex a01 頁19/20: https://openalex.org/W4415851441 前頁の頁尾から 0、次頁の頁頭から 0
AX1-20260902-E1-Q5@openalex a01 頁20/21: https://openalex.org/W1526276002 前頁の頁尾から 0、次頁の頁頭から 0
AX1-20260902-E1-Q5@openalex a01 頁22/23: https://openalex.org/W766044995 前頁の頁尾から 1、次頁の頁頭から 0
AX1-20260902-E1-Q5@openalex a01 頁23/24: https://openalex.org/W7108333387 前頁の頁尾から 1、次頁の頁頭から 0
AX1-20260902-E1-Q5@openalex a01 頁25/26: https://openalex.org/W7168379362 前頁の頁尾から 0、次頁の頁頭から 0
AX1-20260902-E1-Q5@openalex a01 頁25/26: https://openalex.org/W4403570593 前頁の頁尾から 1、次頁の頁頭から 13
AX1-20260902-E1-Q5@openalex a01 頁27/28: https://openalex.org/W4407244756 前頁の頁尾から 0、次頁の頁頭から 0
```
