/dev-wave の引数 (逐語、2026-09-28 07:5x JST 起動):

[T-2273] [T-2560] 受入 shard-0 の次の律速 (b) 発行 subprocess を縮める。D2271 で (a) (可視 output の写しを collection 中に作る) を
  land し対率中央値 12.7 % 短縮したが、5 分上限は未達 (B の W_max 中央値 317.2 秒)。対象は D2253 項 4 の診断で共有発行 key の builder
  に残る発行 child 約 87 秒 (CPU 支配: finalize_receipt 26.5・draft_receipt 20.4・validate_draft 19.8・gate_check 13.2・verify_receipt 6.6
  秒)。記録は output/insights/2026-09-27/t2273-shard0-precopy-impl/README.md。land 条件は (a) と同じ隣接対の形で測る前に事前登録し、W_1 と pre
  も補助量として見る。受領証の検査内容は緩めない (規律 2)。実装は Codex author (D95)。計算は job Elapse の実測単価で見積もり、検査込み 2 node
  時間以上ならユーザー確認。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh
  worktree を作る。
