/dev-wave [T-2273] [T-2560] 受入の律速を実測で特定し直す診断 wave (実装差分ゼロ、D1936 項 35)。起点は insight
  output/insights/2026-09-21/t2825-ledger-refresh-ab/README.md。refresh 後も shard-0 の W_0 は 310.7〜344.9 秒で、全体 5
  分の上限を超えている。最大占有 worker は、t=0 から並ぶ active_v2 系 8 node (209.7〜246.3 秒、L =
  test_t080_failed_launch_preserves_receipt_refusal の 222.3〜246.3 秒) の後に 20〜31 秒の item が 1〜2 個続く形である。この形から律速を特定し
  (A で t≈55 秒から先頭に立った同系 node 189.98〜208.09 秒の原因は未測定)、効果の見込みを実測で示して次の一手を 1 つ選ぶ。標本の時点は --as-of
  で固定する。[T-2845] (Path.resolve 縮約) は D2219 項 4 で今は起こさない。未実測の prewarm・共有 cache
  は先行実装しない。既存の検査は削らない。診断 job は計算ノードで走らせる。job 合計が 2 node 時間以上なら、job Elapse
  の実測単価で見積りを示し、投入前にユーザー確認を取る。本題の診断だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。着手直前の
  local main から fresh worktree を作る。
