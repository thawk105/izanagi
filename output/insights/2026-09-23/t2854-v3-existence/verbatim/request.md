/dev-wave [T-2854] の残り (1) (P1) — 設計 §3.3 の存在履歴 (初期キー集合・insert 前の不存在・delete 版の読みの不整合) を verifier
  に実装し、成立を確かめてから印 Integrity.v3_existence_unverified を撤去する (Codex author、D95)。設計 =
  output/insights/2026-09-21/tpcc-trace-certification-design/README.md §3.3、単位 4 の記録 =
  output/insights/2026-09-22/t2854-tpcc-verifier-v3/README.md §6、実 trace =
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/evidence/traces-2/ (zstd)。正例・負例と変異で検出を示す。単位 5 (pipeline
  配線)・単位 3・単位 11 は含めない (単位 5 は稼働中の T-2849 実装 wave と評価経路で重なるため)。T-2847 (1) の wave が新規 test file
  を並走で足すので、その file は触らない。正しさゲートは緩めず (規律 2)、判定できない場合は認定しない側へ倒す。計算は 2 node
  時間以上ならユーザー確認後。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh
  worktree を作る。
