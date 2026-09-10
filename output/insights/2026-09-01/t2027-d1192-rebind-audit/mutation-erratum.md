# 変異期待 node 集合 erratum

anchor `a9cb2ab4c821d139e0da039b420401c8637e1643`。

段 4 と段 6 で登録した 10 変異について、期待 node を推測で書かず **probe 走行で実測**した
(`DW-M07` / `DW-M08`)。probe は全件 SURVIVED 期待で登録し、観測 node を集めるためだけに回した。

- probe spec: `mutation-spec-probe.json` (sha256
  `f603760a88f58d9db4c3d19b189cc5a0925db3da8eb34b97e4e2af8fed449ca6`)
- probe 結果: `KILLED 0 / SURVIVED 0 / MISMATCH 10 / TIMEOUT 0`、baseline は失敗 node 0 件で緑。
  全 10 変異が赤を出したので MISMATCH は期待どおりであり、これが観測 node の採取である。
- 本走 spec: `mutation-spec-real.json` (sha256
  `db42f0d0467e77911a16cd7a08a46ac66968b950fdcd1dfeb66cba58da055e97`)。
  probe の観測集合をそのまま KILLED 期待の完全集合として登録した。

**前 wave が登録していた node 集合より広い。** 前 wave の baseline は 6 passed で、
期待 node だけを走らせていた。本 wave は焦点 4 file 全体を走らせているので、
同じ変異でも隣接 consumer の赤がより多く観測される。走行範囲が違うだけで、
どちらの集合もその範囲での完全集合である。

複数 node が落ちる変異 (M1=13、M2=8、M12=7、M8=4) は、診断文字列だけの追加赤ではなく、
**同じ受理条件を隣接 consumer が独立に拒否した結果**である。単一理由性は保たれている。

本 wave が追加した 3 変異 (M11 / M13 / M14) はいずれも、本 wave が追加したテストだけを
落とす単一理由の kill であり、修正が実際に受理集合を動かしていることを示す。

probe の生結果は repo 外の job dir へ保全し、削除していない。
