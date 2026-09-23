# 依頼の逐語 (2026-09-23 JST、/dev-wave の引数)

[T-2853] 残り (5) 主要図の再実行計画を書く。着手直前の local main から fresh worktree。論文の主要図 (docs/paper-story/ の図一覧)
  ごとに「描き直し / R2 (再検証) / 独立探索のやり直し」のどれが要るかを一次資料
  (output/insights/2026-09-22/t2853-repro-package-estimate/README.md、output/insights/2026-09-23/t2853-repro-package-archive/README.md)
  から決め、図ごとの node 時間を実測単価で積み上げた計画を新しい insight に書く。job は投げない。合計が 2 node
  時間以上の部分は、実行時にユーザー確認が要ると明記する (D2212 項 4)。(1) trace 保全口は T-2849 の担当、(4) は P1 と同じ wave
  の担当なので触れない。provenance は粗い粒度でよい (D320)。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
