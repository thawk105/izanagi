/dev-wave [T-2847] 残り (4): si の trace emitter を v2 (C 行に read/write 件数 + E 行) にし、si の変異 V28・V29・V36 を実走して検出期待表
  (output/insights/2026-09-22/t2847-verifier-detection-design/README.md §4) の si 行を埋める。v2 化は silo の先例
  (external/ccbench/cc/silo/transaction.cc の v2 frame の注記) と同じく cc/si/transaction.cc の中だけで行い、共有 header
  (include/trace.hh・tpcc.hh) は変えない (D297 の header 裁定待ち ([T-2854]) に掛けない)。最初に、既存の実走
  (output/insights/2026-09-26/t2847-mocc-run/README.md、pin C 68106660 に patch を単独で当てる形) と同じく pin 前進なしに patch として当てて
  build・verify できるかを確かめ、できなければ実装差分ゼロでその事実を返して止める。si は X/P
  の証拠面が無いので上限は「巡回の検出」で、certified とは呼ばない (設計 §5.3)。CCBench 側は patch か local branch に置き、上流への push
  は人間の判断 (D16)。実装は Codex author (D95)、規律 2 を緩めない。計算は job Elapse の実測単価 (変異 1 job 139〜194 秒、mocc 1 job 157〜540
  秒) で見積もり、検査込みの合計が 2 node 時間以上ならユーザー確認 (D2212 項 4)。harness mode の直接 qsub は tools/pegasus/README.md §7
  に従う。着手直前の local main から fresh worktree を作る。本題だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
