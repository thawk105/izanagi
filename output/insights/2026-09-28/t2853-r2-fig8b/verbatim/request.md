# 依頼の逐語 (2026-09-28、/dev-wave の引数)

[T-2853] 再現パッケージの R2 として fig8b (fig8 を含む。B-10 静的右 tail の 2 cohort × 各 3 job) を、元の driver
  tools/pegasus/submit_b10_backoff_shape.sh で Pegasus の計算ノードに測り直す。固定 genome を LLM
  なしで検証・計測し、元の図と同じ生成器で描いて元の値と並べて記録する。投入単位は図 1 本 = 1 タスク
  (output/insights/2026-09-27/t2853-repro-rest/README.md §3.3)、見積り 1.40 node 時間でユーザー確認不要と確定済み (D2212 項
  4)。元データと経路は計画稿 output/insights/2026-09-23/t2853-figure-rerun-plan/README.md と repo 外
  /work/1/SFC/tanab/b10-backoff-grid-t2500-formal/。投入前に単独性を確認し、job は複数ノードへ同時に割る。新しい測定は元の cohort と合成せず別
  attempt として並記する (プールしない)。正しさ検査は元と同じく job 内で行い (規律 2 を緩めない)、trace 保全口の opt-in (D2233)
  はこの経路で使えるなら有効にする。driver の変更が要る、または実測単価で 2 node 時間を超えると判明したら、段 4
  で見積りを示して止める。本題の実行と記録だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh
  worktree を作る。

(2026-09-29 の session 再開時のユーザー発話: 「続けられる？」)
