[V20 の patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/patches/broken-silo-published-version-mismatch.patch:13) だけを修正しました。UPDATE の公開 epoch を `2^31` から `fetch_add(1, relaxed)` で増やし、公開 tid は `2^28` 固定、`lock=0`・`latest=1`・`absent=0` のままです。C/W 行、診断条件、`#if IZANAGI_BREAK_PUBLISHED_VERSION_MISMATCH` の **4 site** は変更していません。

`transaction.cc:560–590` は読取・書込版と worker の直前の版を進めて C/W 版を選びます。`tuple.hh` の epoch は 32 bit、tid は 29 bit です。したがって公開版は更新順に増え、公開版を読んだ後の C/W 版は同じ epoch で tid が `2^28+1` 以上になります。通常の低い epoch の C/W 版とも分離されます。巻き戻りには公開 UPDATE が `2^31` 回、または高い epoch 内で tid が `2^28` 回進む必要があります。**1 秒でそこに達しないことは source 上の厳密な上限ではなく、W4 の実行量についての前提です。** 厳密な保証が必要なら、両カウンタの上限を実行時に検査して run を失敗扱いにする方法があります。

`git -C external/ccbench apply --check` と `git diff --check` はともに rc=0。`unifdef` は無いため、scratch に適用して未定義枝を抽出し、pin の `transaction.cc` と `diff -u` で一致することを確認しました。構文確認・build・W4 実走は今回未実施です。既存テストの期待値と登録表は変更不要です。commit は作成していません。

## 総括

公開版の逆順化を解消する修正を patch だけに加え、単独適用と未定義時の一致を確認しました。実走での anomaly 判定は親側に残ります。