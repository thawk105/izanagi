/dev-wave [T-2854] 残り (1) 単位 5 を実装する。着手直前の local main から fresh worktree。旧 result_to_dict・CLI・pipeline・受領証 digest へ
  v3 の表・取引種別・存在詳細を配線し (core.result_to_dict_v3)、orchestrator/campaign/pipeline.py の allowlist を tpcc + v3 + 57:43 の flag
  へ広げる。witness 試験と段 1 の正例・負例も足す (§6.1 の「genesis の誤用」は存在検査の read-unborn-genesis に帰属)。設計は
  output/insights/2026-09-21/tpcc-trace-certification-design/README.md §7.1、存在履歴は
  output/insights/2026-09-23/t2854-v3-existence/README.md。実 trace は
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/evidence/traces-2/ にある。実装は Codex author (D95)。pipeline が tpcc
  を受理した時点で、見送り台帳 [T-156] の発火条件を再評価する。単位 11 (pin 前進) は scope 外。T-2797 / T-2850 の発効束が束縛する commit
  は動かさない。規律 1・2 を緩めない。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
