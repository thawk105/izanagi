/dev-wave [T-2854] (P1、D2212 項 2) TPC-C 段 1 の CCBench 側として、設計 output/insights/2026-09-21/tpcc-trace-certification-design/README.md
  §7.1 の単位 1 (include/trace.hh の v3 helper、include/tpcc.hh の取引種別 context と trace build 限定の commit 計数) と単位 2 (silo の v3
  emitter) を、§3.1 の v3 frame と §8 の親決定どおり Codex author (D95) で CCBench の izanagi-trace 枝 (D16) に実装し、現 pin
  の上で内部の受入まで進める。mocc (単位 3)・superproject 側 (単位 4・5)・pin 前進 (単位 11) は対象外。trace は compile 時に完全除去 (規律
  1、D14)、規律 2 を緩めない。build は計算ノードで行い、合計 2 node 時間以上なら見積りを示してユーザー確認 (D2212 項 4)。push は人間
  (D16)。本題だけ、gate・検査・台帳の追加は scope 外。着手直前の local main から fresh worktree。
