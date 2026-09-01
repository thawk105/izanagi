---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t2097-exclusion-closure-split
seq: 2
---

## {{D:acceptance-floor-is-longest-node-not-exclusion}}. 受入 wall の床は最長単体 node と report 外費用であり、排他閉包の細分化では下がらない

**決定:** 受入全走の wall を語るときは、最遅 shard の pytest wall を
`report 外費用 + 最大 worker occupancy` の 2 層で分解し、後者の下界を
`max(最長単体 node, 総仕事量 / worker 数)` とする。**排他閉包の細分化を wall 短縮の手段として
提案しない。** D1035 が指示した軸は実測で尽きている。

同時に、次の 1 手を**採らない**。`tools/acceptance_shards.py` の `_components()` が作る
file component から、`xdist_group` を持たない node を外して shard 間へ散らす案である。

**実測 (2026-09-01 08:15 の受入全走 3 shard と、同 artifact root の 14 走):**

- 最遅 shard の pytest wall 213.91 秒に対し、最大 worker occupancy は 135.68 秒、
  最長単体 node は 126.13 秒。**理論最適まで詰めても取れるのは 9.54 秒**である。
- node 粒度で 3 shard へ完璧に割り直した反実仮想でも、各 shard の LPT(48 worker) は
  126.1 / 122.4 / 118.5 秒で、最悪値は現行 shard-0 の理論最適 126.1 秒と一致する。
  **閉包を file から node へ細分化しても最悪 shard の occupancy は動かない。**
- 生きている xdist group の作業単位は同一走で最大 67.9 秒 (`s8c-predicate-snapshot`) しかなく、
  最長単体 126.13 秒を下回る。D1008 の資源別 lock により ccbench writer は 4 node・0.19 秒、
  reader は共有ロックで相互に待たない。
- shard 割付の閉包は file である。group を含む file はその file 全体が 1 component になるため、
  実走の最大成分は 23 file・3405 node・4187.6 秒 (最遅 shard の仕事量の 72.0%) に達するが、
  そのうち `REAL_REPO_ACCESS_BY_NODE` に載るのは 95 node・162.5 秒 (3.9%) だけである。
  拘束は大きいが、外しても最長単体が動かないため wall は下がらない。
- report 外費用は 14 走で再現し、中央値は最遅 shard 77.2 秒、他 2 shard 56.4 / 56.6 秒。
  **排他 group が 1 つも載らない shard でも 56 秒台ある。**

**理由:**

- D1035 は「床は排他鎖である」という前提の上で細分化を選んだ。D1008 と D1103 がその鎖を解いた後、
  前提は成立していない。前提が消えた裁定を、名指しされた操作だけを頼りに実行しても床は動かない。
- 採らない 1 手は**正しさを弱める**。対象 file の無印 node は実 source・実 calibration・実 policy・
  実 freeze を読むが `REAL_REPO_ACCESS_BY_NODE` の外にあり、protocol lock を無取得で通過する。
  D1008 は lock の保証範囲を同一 host・同一 filesystem までと明記しており、shard は別 job・
  別計算ノードで走る。速度のために排他の射程を縮める変更であり、絶対規律 2 に反する。
- D1103 の却下理由「閉包が確定していない排他を差し替えない」がそのまま当たる。
  本 wave の敵対レビューは登録外の writer は新たに見つけなかったが、登録外の reader と、
  shard 間に collection 完了 barrier が無いことを file:line で確認した。
- 仮に安全でも、効果量 9.54 秒は D1019 が記録した走間差 32.27 秒より小さく、
  現行の A/B 設計では判定できない。

**残す限界を決定の一部として明記する。**

- **最遅 shard 固有の report 外費用 約 21.9 秒 (14 走の中央値 20.3 秒、範囲 18.9〜27.9 秒) の正体は
  未計測である。** 資源 lock の取得は `pytest_runtest_protocol` の wrapper で setup report より前、
  controller prewarm も test protocol より前に走るため、どちらの待ちも JUnit にも
  `report.json` にも現れない。**「この 21.9 秒は排他待ちではない」とは実測で言えない。**
- 最長単体 126.13 秒は固定値ではない。14 走で 118.6〜219.3 秒に動く。
- 各 node の所要が割付から独立であるとは示していない。走ごとに総仕事量と最長単体が一緒に動くが、
  機械側の共通原因でも説明できる。
- 本決定は pytest wall の層についてだけ述べる。D1320 の job 層・session 層へ一般化しない。

**却下した選択肢:**

- **段 2 が出した 462 node の file component 分離を実装する** — 上記のとおり正しさを弱め、
  効果量も判定できない。
- **shard 割付の重みを node 数から所要へ変える** — D1019 が実測で否定済みで、
  本 wave の反実仮想でも最悪 shard の occupancy は動かない。
- **「床は排他鎖ではないので打つ手なし」と書いて終える** — 床の 2 成分 (最長単体 126.13 秒、
  共通 report 外費用 約 56 秒) はどちらも実在の短縮対象であり、いずれもユーザー裁定が要る。
  手が無いのではなく、**裁定済みの手が無い**。
