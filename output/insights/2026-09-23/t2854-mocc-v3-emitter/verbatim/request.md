/dev-wave [T-2854] の残り・単位 3 (P1) — mocc の trace v3 emitter を CCBench の local branch に載せる。設計 =
  output/insights/2026-09-21/tpcc-trace-certification-design/README.md §7.1、単位 1・2 の記録 =
  output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md (C1 56b5cb709628c9cac98e4e18ff676defc77a9117 の v3 helper を使う)、土台 = T-2844
  の候補 C 68106660686232781bca3be792a750d3e19d7a8a (branch
  izanagi-mocc-xp-instrumentation、output/insights/2026-09-21/t2844-mocc-xp-hook-branch/README.md)。候補 C の上に新しい local branch を切って
  C1 の helper を載せ、mocc の v3 emitter を書く (Codex author、D16/D18/D20)。計算ノードで v3 の構造・witness・TRACE=0 での完全除去 (規律 1)
  を単位 1・2 と同じ形で確かめる。pin 前進 (単位 11)・gitlink 変更・GitHub push はしない (push は人間手番)。izanagi-mocc-xp-instrumentation
  自体は動かさない (稼働中の T-2858 が C を材料として固定している)。計算は 2 node 時間以上ならユーザー確認後。規律 2
  は緩めない。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh worktree を作る。
