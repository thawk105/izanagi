# 親の追加実測 (段 2 の後、段 3 の前)

## 1. (P2) 相方の同定 (companion_check.py、session 5141225c、refresh 後台帳)

xdist の LoadScope/LoadGroup scheduling は各 worker に初期 2 unit (#277 heuristic) を配り、group 無し node は 1 node = 1 unit である。shard 内は台帳 cost 降順に reorder されるので、worker k は cost 順 index k と 48+k を持つ。最長 node `test_s8b_oracle_driver.py::…_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]` は cost 順 2 番目 (台帳 240.0、1 番目と tie) → その worker の 2 個目は index 49 = `test_codex_reasoning_ab.py::test_m3_ignored_extra_and_missing` (台帳 22 秒) で、観測 tail 19.9 秒と整合する。最長 node が終わる頃には workqueue が空なので 3 個目は来ない。したがって「相方 約 20 秒」は初期 2 unit の構造であり、割付ではなく reorder 側の pairing (最長 unit の worker へ最小 unit を対にする) で削れる可能性がある (本 wave の scope 外、次の一手候補)。tail が 7.5〜8.7 秒だった 3 走 (09:45/09:47/09:52、nsel=9004 = 旧台帳割付の branch) は cost 順が違い相方が別 test だった。

## 2. (P3) 最長 node の所要と競合 (contention_check.py、99 session)

- corr(最長 node 所要, 同 shard の他 47 worker の平均占有) = **0.993**
- corr(最長 node 所要, 別ノードで走る shard-1 + shard-2 の最大占有) = **0.069** (shard-1 −0.088 / shard-2 0.112)
- corr(最長 node 所要, shard-0 の selected 数) = −0.031
- nsel > 6000 (旧台帳割付、n=81): 最長 node 中央値 255.1 (200.0〜577.5)、平均占有中央値 197.1、wall 中央値 355.1
- nsel ≤ 6000 (refresh 後割付、n=18): 最長 node 中央値 261.6 (225.1〜499.7)、平均占有中央値 186.0、wall 中央値 347.7

読み: 最長 node の膨らみは**同じ計算ノード内**の要因と強く結び付き、別ノードの shard とは無関係。ただし同一割付内では仕事量が一定なので、この相関は「ノード状態が全 worker を同時に膨らませる」で説明でき、「仕事量を減らせば最長 node が速くなる」の証拠にはならない (旧/新割付の仕事量は 8852 対 8569 秒でほぼ同じ、対比較にならない)。親は (P3) を「既存 data では分離できない」のまま維持する。
