# 依頼 (ユーザーの `/dev-wave` 引数、逐語)

[T-2868] MOCC read-heavy (48 thread・100 万 record・rr95) の固定 backoff literal 候補で slot 25 件中 6 件に出た G2 (write skew、1
  反復に巡回 1 件、zipf 上位 key、性能構成の verify で検出、stock slot 7 件は 0) の原因を、MOCC 本体の欠陥 / literal 差し込みの影響 / verifier
  の誤検出に切り分ける。材料 = output/insights/2026-09-27/t2849-mocc-conn/README.md §4 と保全済み trace (repo 外
  /work/1/SFC/tanab/izanagi-repro-archive/t2849-mocc-conn-20260926/)、既往 = stock MOCC の非認証 G2 観測 3 件 ([T-2774] [T-2779]
  [T-2780]、D2148 項 13)。まず保全 trace の witness を計算ノードで独立に再検査し、verifier の判定が trace
  と整合するかを確かめてから、必要最小の追加走 (例: 同じ throughput 域の stock 対照) を設計する。追加走の job 合計が 2 node
  時間以上なら実測単価で見積りを示してユーザー確認。規律 2 は不変 (reject は reject のまま)、切り分けまで論文の主張に使わない。CCBench
  本体の欠陥なら output/README.md の形式で insight に構造化し、上流報告は人間の判断。着手直前の local main から fresh
  worktree。本題だけ、仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
