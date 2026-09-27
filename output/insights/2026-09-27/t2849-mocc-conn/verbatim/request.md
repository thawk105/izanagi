# 依頼 (逐語、ユーザー直接起動の `/dev-wave`、2026-09-26 22:0x JST)

[T-2849] 残り (3) 第 2 プロトコル MOCC での疎通を行う (20〜40 候補 × 3 workload)。基盤は着地済み (harness `--protocol mocc`、MOCC
  の slot だけ campaign pin C、較正 records 1,000,000。insight output/insights/2026-09-26/t2849-mocc-insertion/README.md、D2248)。MOCC は silo
  と別の cohort 名・root で走らせ、stock 比で報告し、既知最良の参照が無いことを明記する (D2220 項 6)。直接 qsub では submit-tree を AI の
  worktree 置き場の外に job ごとに 1 本置き、third-party は submit-tree 内 staging へ hydrate する (同 insight §6)。着地した [T-2850] (b)
  の同時検査を使ってよいが、read-heavy・balanced に使うなら記憶量と静定待ちの上限を先に測る (entry 1871)。論文根拠の実験なので、job body で
  trace 保全口 IZANAGI_TRACE_ARCHIVE_ROOT の opt-in を有効にする ([T-2853] (1''))。1 タスクの job 合計が 2 node 時間以上なら、job Elapse
  の実測単価で見積りを示してユーザー確認後に投入する (D2212 項 4)。正しさゲートは不変 (規律 2)。コードを変えるなら Codex author
  (D95)。着手直前の local main から fresh worktree を作る。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
