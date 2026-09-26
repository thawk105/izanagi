/dev-wave [T-2847] 残り (2) のうち mocc の既存 broken patch 4 本と新規 V25・V34 を、現 pin C (68106660、main に着地済み)
  の上で計算ノードで実走し、検出表を実測で埋める。正本は worklog の [T-2847] carry、設計
  output/insights/2026-09-22/t2847-verifier-detection-design/README.md §4・§5.1、手順の先例は
  output/insights/2026-09-23/t2847-mutation-run/README.md と D2239 (発火診断で「盲点」と「未発生」を分ける、同時投入は job ごとに別
  checkout)。実測単価は 1 job 139〜194 秒。1 タスクの合計が 2 node 時間以上になりそうなら、投入前に見積りを示してユーザーの確認を取る (D2212 項
  4)。着手直前の local main から fresh worktree を作る。patch と実装は Codex author (D95)。規律 2
  は緩めない。本題の実装だけで、仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
