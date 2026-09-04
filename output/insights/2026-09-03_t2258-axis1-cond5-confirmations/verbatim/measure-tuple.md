# 実測 5 — 境界重複 record の三つ組比較と 2 走間の score 差分

probe の逐語ソースは `probe-src.md`。repo 外の使い捨て probe の出力であり、
入力は凍結 bundle `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` と
repo 内の `2026-09-02-axis1-search-catalog.json` だけである。

**`gap` は `申告総数 - distinct` の差そのものであって「取りこぼした件数」ではない。**
その解釈は本 bundle からは支持されない (正本文書 §2.3)。

```text
=== 頁境界で重複した record の三つ組比較 ===
重複 occurrence 総数: 32
  三つ組が同一のまま再出現: 0
  三つ組が変わって再出現:   32
  そのうち前頁の cursor 鍵の ID と一致: 23

AX1-20260902-E1-Q2@openalex a01 頁0->1 https://openalex.org/W7137872824
    前頁: score=13.707714 date=2026-03-14
    次頁: score=13.697786 date=2026-03-14   三つ組=変化
    前頁 cursor 鍵 = [13.70483, 1763424000000, 'https://openalex.org/W4417215361']
    cursor 鍵の ID と一致: False
AX1-20260902-E1-Q2@openalex a01 頁5->6 https://openalex.org/W3089320326
    前頁: score=0.7657841 date=2020-09-23
    次頁: score=0.7650734 date=2020-09-23   三つ組=変化
    前頁 cursor 鍵 = [0.7657841, 1600819200000, 'https://openalex.org/W3089320326']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q2@openalex a02 頁1->2 https://openalex.org/W7108955742
    前頁: score=7.006365 date=2025-12-04
    次頁: score=7.006049 date=2025-12-04   三つ組=変化
    前頁 cursor 鍵 = [7.006365, 1764806400000, 'https://openalex.org/W7108955742']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q2@openalex a02 頁4->5 https://openalex.org/W4403570593
    前頁: score=0.8871775 date=2026-05-14
    次頁: score=0.883389 date=2026-05-14   三つ組=変化
    前頁 cursor 鍵 = [0.88342386, 1769644800000, 'https://openalex.org/W7126211752']
    cursor 鍵の ID と一致: False
AX1-20260902-E1-Q2@openalex a02 頁4->5 https://openalex.org/W7126211752
    前頁: score=0.88342386 date=2026-01-29
    次頁: score=0.8830689 date=2026-01-29   三つ組=変化
    前頁 cursor 鍵 = [0.88342386, 1769644800000, 'https://openalex.org/W7126211752']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q2@openalex a02 頁7->8 https://openalex.org/W4401567087
    前頁: score=0.08617169 date=2024-01-01
    次頁: score=0.08608341 date=2024-01-01   三つ組=変化
    前頁 cursor 鍵 = [0.08617169, 1704067200000, 'https://openalex.org/W4401567087']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q3-SPRE1991@openalex a01 頁1->2 https://openalex.org/W2048310987
    前頁: score=16.563131 date=1988-12-01
    次頁: score=16.558 date=1988-12-01   三つ組=変化
    前頁 cursor 鍵 = [16.563131, 596937600000, 'https://openalex.org/W2048310987']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q4@openalex a01 頁2->3 https://openalex.org/W2935898307
    前頁: score=21.70782 date=2018-01-01
    次頁: score=21.707573 date=2018-01-01   三つ組=変化
    前頁 cursor 鍵 = [21.70782, 1514764800000, 'https://openalex.org/W2935898307']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q4@openalex a01 頁8->9 https://openalex.org/W4312590834
    前頁: score=4.405989 date=2022-09-06
    次頁: score=4.4010644 date=2022-09-06   三つ組=変化
    前頁 cursor 鍵 = [4.405989, 1662422400000, 'https://openalex.org/W4312590834']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q4@openalex a01 頁9->10 https://openalex.org/W4402510380
    前頁: score=3.8567219 date=2024-07-18
    次頁: score=3.846237 date=2024-07-18   三つ組=変化
    前頁 cursor 鍵 = [3.8540874, 1787529600000, 'https://openalex.org/W7204143370']
    cursor 鍵の ID と一致: False
AX1-20260902-E1-Q4@openalex a01 頁10->11 https://openalex.org/W3046753628
    前頁: score=3.343257 date=2020-06-30
    次頁: score=3.337358 date=2020-06-30   三つ組=変化
    前頁 cursor 鍵 = [3.3378983, 1780099200000, 'https://openalex.org/W7162872430']
    cursor 鍵の ID と一致: False
AX1-20260902-E1-Q4@openalex a01 頁12->13 https://openalex.org/W1493253787
    前頁: score=1.4882214 date=1999-08-04
    次頁: score=1.4874754 date=1999-08-04   三つ組=変化
    前頁 cursor 鍵 = [1.4882214, 933724800000, 'https://openalex.org/W1493253787']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q4@openalex a01 頁14->15 https://openalex.org/W7163686966
    前頁: score=0.80695856 date=2026-06-04
    次頁: score=0.80684435 date=2026-06-04   三つ組=変化
    前頁 cursor 鍵 = [0.80695856, 1780531200000, 'https://openalex.org/W7163686966']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q4@openalex a01 頁15->16 https://openalex.org/W2951097601
    前頁: score=0.74070126 date=2007-12-07
    次頁: score=0.73816395 date=2007-12-07   三つ組=変化
    前頁 cursor 鍵 = [0.7404885, 1783209600000, 'https://openalex.org/W7167427330']
    cursor 鍵の ID と一致: False
AX1-20260902-E1-Q4@openalex a01 頁16->17 https://openalex.org/W7128478743
    前頁: score=0.6761543 date=2026-02-10
    次頁: score=0.6760744 date=2026-02-10   三つ組=変化
    前頁 cursor 鍵 = [0.6761543, 1770681600000, 'https://openalex.org/W7128478743']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q4@openalex a01 頁18->19 https://openalex.org/W7168432258
    前頁: score=0.57768553 date=2026-07-13
    次頁: score=0.57764417 date=2026-07-13   三つ組=変化
    前頁 cursor 鍵 = [0.57768553, 1783900800000, 'https://openalex.org/W7168432258']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q4@openalex a01 頁19->20 https://openalex.org/W7164357879
    前頁: score=0.53749907 date=2026-06-11
    次頁: score=0.534869 date=2026-06-11   三つ組=変化
    前頁 cursor 鍵 = [0.5358529, 1561852800000, 'https://openalex.org/W2981552732']
    cursor 鍵の ID と一致: False
AX1-20260902-E1-Q4@openalex a01 頁21->22 https://openalex.org/W7119551616
    前頁: score=0.36753914 date=2025-01-18
    次頁: score=0.36751628 date=2025-01-18   三つ組=変化
    前頁 cursor 鍵 = [0.36753914, 1737158400000, 'https://openalex.org/W7119551616']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q5@openalex a01 頁0->1 https://openalex.org/W2272535669
    前頁: score=137.76848 date=2016-06-14
    次頁: score=137.76366 date=2016-06-14   三つ組=変化
    前頁 cursor 鍵 = [137.76848, 1465862400000, 'https://openalex.org/W2272535669']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q5@openalex a01 頁6->7 https://openalex.org/W1964691382
    前頁: score=26.193602 date=2010-12-21
    次頁: score=26.192652 date=2010-12-21   三つ組=変化
    前頁 cursor 鍵 = [26.193602, 1292889600000, 'https://openalex.org/W1964691382']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q5@openalex a01 頁8->9 https://openalex.org/W2002016273
    前頁: score=14.082521 date=2012-02-16
    次頁: score=14.079399 date=2012-02-16   三つ組=変化
    前頁 cursor 鍵 = [14.082521, 1329350400000, 'https://openalex.org/W2002016273']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q5@openalex a01 頁9->10 https://openalex.org/W4221167659
    前頁: score=11.74826 date=2022-04-25
    次頁: score=11.748041 date=2022-04-25   三つ組=変化
    前頁 cursor 鍵 = [11.74826, 1650844800000, 'https://openalex.org/W4221167659']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q5@openalex a01 頁14->15 https://openalex.org/W2078161256
    前頁: score=6.3949327 date=2014-07-01
    次頁: score=6.3928146 date=2014-07-01   三つ組=変化
    前頁 cursor 鍵 = [6.3949327, 1404172800000, 'https://openalex.org/W2078161256']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q5@openalex a01 頁15->16 https://openalex.org/W2068756387
    前頁: score=5.7456546 date=2010-01-01
    次頁: score=5.743462 date=2010-01-01   三つ組=変化
    前頁 cursor 鍵 = [5.7456546, 1262304000000, 'https://openalex.org/W2068756387']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q5@openalex a01 頁18->19 https://openalex.org/W2069437605
    前頁: score=3.8040228 date=1994-04-01
    次頁: score=3.8040004 date=1994-04-01   三つ組=変化
    前頁 cursor 鍵 = [3.8040228, 765158400000, 'https://openalex.org/W2069437605']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q5@openalex a01 頁19->20 https://openalex.org/W4415851441
    前頁: score=3.1697054 date=2025-11-04
    次頁: score=3.1664772 date=2025-11-04   三つ組=変化
    前頁 cursor 鍵 = [3.1697054, 1762214400000, 'https://openalex.org/W4415851441']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q5@openalex a01 頁20->21 https://openalex.org/W1526276002
    前頁: score=2.0808458 date=2003-01-01
    次頁: score=2.0802884 date=2003-01-01   三つ組=変化
    前頁 cursor 鍵 = [2.0808458, 1041379200000, 'https://openalex.org/W1526276002']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q5@openalex a01 頁22->23 https://openalex.org/W766044995
    前頁: score=1.0101566 date=2011-03-28
    次頁: score=1.0100197 date=2011-03-28   三つ組=変化
    前頁 cursor 鍵 = [1.010123, 1325376000000, 'https://openalex.org/W2466844719']
    cursor 鍵の ID と一致: False
AX1-20260902-E1-Q5@openalex a01 頁23->24 https://openalex.org/W7108333387
    前頁: score=0.878196 date=2025-12-02
    次頁: score=0.878104 date=2025-12-02   三つ組=変化
    前頁 cursor 鍵 = [0.8781775, 1767225600000, 'https://openalex.org/W7167804605']
    cursor 鍵の ID と一致: False
AX1-20260902-E1-Q5@openalex a01 頁25->26 https://openalex.org/W7168379362
    前頁: score=0.70850056 date=2026-06-03
    次頁: score=0.7084816 date=2026-06-03   三つ組=変化
    前頁 cursor 鍵 = [0.70850056, 1780444800000, 'https://openalex.org/W7168379362']
    cursor 鍵の ID と一致: True
AX1-20260902-E1-Q5@openalex a01 頁25->26 https://openalex.org/W4403570593
    前頁: score=0.7085745 date=2026-05-14
    次頁: score=0.7051244 date=2026-05-14   三つ組=変化
    前頁 cursor 鍵 = [0.70850056, 1780444800000, 'https://openalex.org/W7168379362']
    cursor 鍵の ID と一致: False
AX1-20260902-E1-Q5@openalex a01 頁27->28 https://openalex.org/W4407244756
    前頁: score=0.60876584 date=2025-02-05
    次頁: score=0.6085304 date=2025-02-05   三つ組=変化
    前頁 cursor 鍵 = [0.60876584, 1738713600000, 'https://openalex.org/W4407244756']
    cursor 鍵の ID と一致: True

=== 2 走に共通する ID の score 差分 (Q1 / Q2) ===
AX1-20260902-E1-Q1@openalex: 共通 ID=735 score が変わった ID=334 (45.4%)
    https://openalex.org/W100705868: 6.9179745 -> 6.9180555
    https://openalex.org/W143221248: 1.0798092 -> 1.0798069
    https://openalex.org/W1519706220: 43.99587 -> 43.999825
    https://openalex.org/W1527821982: 22.504786 -> 22.505362
    https://openalex.org/W1595683865: 28.343555 -> 28.341671
    相対差 中央値=1.063e-04 最大=8.631e-03
AX1-20260902-E1-Q2@openalex: 共通 ID=1605 score が変わった ID=829 (51.7%)
    https://openalex.org/W1025092411: 0.33967942 -> 0.33988637
    https://openalex.org/W143221248: 0.8646555 -> 0.8646527
    https://openalex.org/W1493253787: 1.5115485 -> 1.5106757
    https://openalex.org/W1501251577: 2.5818439 -> 2.5818093
    https://openalex.org/W1515827528: 0.12993336 -> 0.12990904
    相対差 中央値=1.242e-04 最大=8.840e-03
```
