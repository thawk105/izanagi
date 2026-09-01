---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2135-tictoc-cicada-space
seq: 3
---

## 再発

### F717

- **再発: 2026-09-02** — 親が段 1 brief へ「tictoc の `PARTITION_TABLE` は `.cc`/`.hh` に出現 0 の
  死にフラグ」と書いたが、検索範囲が `cc/tictoc/*.cc` と `cc/tictoc/*.hh` だったため
  `cc/tictoc/include/` 部分木 (header 8 本) と 4 つの workload source を落としていた。
  段 6 レンズ A が「build 対象は `transaction.cc` だけではない」と指摘し、親が全件で測り直した
  (結論は維持、live site 0 件)。**F717 の恒久対応「不在を主張する 1 文にその主張が成り立つ範囲を
  同じ文の中に書く」を親が守らなかった**のが直接原因である。さらに段 6 焦点再レビュー 1 巡目も、
  親が射影に build 対象の全 file を入れなかったため独立検証できず partial を返した。
  2 巡目で全 file を射影して closed にした。**不在の主張は、検証する子への射影が build 対象の
  閉包を覆っていなければ独立検証が成立しない** — この射影側の義務が今回の追加分である。
