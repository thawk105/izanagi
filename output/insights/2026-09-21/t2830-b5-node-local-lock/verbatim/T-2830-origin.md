# [T-2830] 依頼の逐語 (/dev-wave の引数、2026-09-21)

[T-2830] (entry 1779、D2199、Codex author) B-5 本走前の実装: tools/pegasus/p3_s4_loop_pegasus.sh の B-5 mode (または job 全体) で
  IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock" を B-10 / A-5 の job body (tools/pegasus/b10_backoff_grid.sh / a5_second_boot_backoff_sweep.sh)
  と同じ node-local に設定し、tools/pegasus/b5_contrast_launch.py を job ごとの submit-tree (または cache 公開競合の検査) に対応させる。試走で
  home 共有 ~/.izanagi/bench.lock の待ちが wall の 59% を占めた (一次資料 output/insights/2026-09-20/t2797-b5-contrast/README.md §6・§8)。既存
  3 経路の argv・bytes 不変を test で固定、変異負例。着手条件 = [T-2795] 修復 wave が main に land 済みであること (同 p3_s4_loop_pegasus.sh
  を編集する)。land 前なら段 1 で待ち、その land を含む local main から fresh worktree を作り直し、先行の認可契約・結合検査を維持する。同じ
  file を編集する別の稼働 wave があれば同様に直列化する。B-5 本走は未認可 (裁定パッケージは同 README §8) なので投入しない。規律 2
  を緩めない。本題だけ。gate・検査・台帳の追加は scope 外。
