/dev-wave [T-2273] D2243 項 2 のとおり、受入 shard-0 の候補 (a)「局所の写しを builder より前 (collection 中) に作る」の効果 = 実受入の
  shard-0 の最大 worker 占有と W_0 の短縮を、repo に入れない対照診断 (第 4 回と同じ型の
  probe、output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md) で先に測る。効果が乏しければ発行 subprocess の内訳 (draft / validate /
  finalize / verify / gate_check) を測って候補 (b) を判断する。(c) (D2242 の実装の land) は採らない。前回の対比
  output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md。計算は job Elapse の実測単価で見積もり、検査込みの合計が 2 node
  時間以上ならユーザー確認 (D2212 項 4)。5 分上限の超過は受容しない。着手直前の local main から fresh worktree
  を作る。本題だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
