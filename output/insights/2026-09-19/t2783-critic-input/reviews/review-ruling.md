# 段6レビュー裁定

- A must real採用: originless文書hashの不一致は親の546 passed/1 failedで確認済み。既存補正定数だけをCodex fixし、他384項目と件数を維持して再走する。
- A/B should real採用: briefを「未送達と20再提案は別観測、因果未検証」「既存抽出器再利用の局所案」へ訂正した。
- B nit realだがscope外として記録: agent_outputs冒頭のmodule import禁止は、従来からp3_s4_loopがAO記録のため同moduleをimportしている現物とも合わない。今回明示bytesの純粋抽出はAO readerを呼ばず、入力側防壁の挙動を変えない。コードcomment訂正のため別変更を追加しない。
- A/Bとも新経路の追加mustなし。白板拡張・static schema整備・新launcher/receipt必須説はrefuted。
- 焦点再レビューはhash差追従と両レビュー指摘のclosed/partial/regressedだけを確認し、新たな仮想リスクを追加しない。
