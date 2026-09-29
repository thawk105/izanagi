[T-2871] 方策 loop (orchestrator/campaign/p3_s4_loop_policy.py) を Pegasus で複数 iteration 回せるようにする。現状、Pegasus の
  campaign claim は identity ごとに一度きり (D464・D553) で、job をまたぐ同じ loop campaign の 2 本目の pair job が ClaimError で build
  前に止まる (2026-09-27 実測、output/insights/2026-09-27/t2865-silo-policy-iter2/README.md §3.4、D2274、F1019)。claim leaf と one-shot
  性は変えず、claim を手で退避する運用も採らず、driver 側で解く。設計択一が割れるので段 2・3 は 2 レンズで回し、段 1 で backoff 軸 loop
  (p3_s4_loop.py) の Pegasus 系列が iteration をどう分けているかを実測して先例にする。結合検査は実 _authorize_measurement・実 acquire_claim を
  2 process で通す形を含め、計算ノードでの生死確認の形は段 1 で決める (単価の参考: pair 786 秒・bootstrap stock 309 秒)。実装は Codex author
  (D95)、正しさゲートは緩めない (規律 2)。計算は job Elapse の実測単価で見積もり、検査込み 2 node
  時間以上ならユーザー確認。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh
  worktree を作る。
