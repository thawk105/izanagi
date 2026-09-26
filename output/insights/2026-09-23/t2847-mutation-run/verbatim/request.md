ユーザー直接起動の `/dev-wave` 引数 (逐語、2026-09-23):

[T-2847] 残り (2) 変異の実走のうち、pin C に依存しない部分を行う。着手直前の local main から fresh worktree。本体は trigger-misattr
  (trigger-gating 骨格の上) の計算ノード実走。新規 18 変異 (D16 第 3 類の out-of-tree patch) は、現 pin e9e477ca
  上で作れて取り込めるものだけ同じ wave で実走する。設計は output/insights/2026-09-22/t2847-verifier-detection-design/README.md
  §4、既存の実走と起動器 (依存物・compiler・出力先の供給) は output/insights/2026-09-23/t2847-patch-verify/README.md。結果は検出表
  (期待した層で検出 / 別の層で検出 / 盲点として certified / 未発生・誤検出) に実測で書く。mocc 4 本 (C の計装の上) と sort-nonswo (driver
  に経路が無い) は scope 外。1 タスクの job 合計が 2 node 時間以上になるなら、実測単価 (1 job Elapse 134〜209 秒)
  で見積りを示し、投入前にユーザー確認する (D2212 項 4)。規律 2 を緩めない。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外。
