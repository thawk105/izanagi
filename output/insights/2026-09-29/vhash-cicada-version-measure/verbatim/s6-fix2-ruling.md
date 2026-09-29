# 段 6 fix 2 巡目の裁定 (2026-09-29 05:2x JST)

入力: codex/out/s6-focus1.md (焦点再レビュー 1 巡目、NO-GO、must-fix 3)。base = fix 1 統合 commit c87d39bc0。
F1・F5・F7・F8・F9・B2・P1 は closed (再レビューの判定を採用)。F2 は計算ノード smoke の実 binary 比較待ち (コード修正なし)。

| # | 所見 | 判定 | fix の内容 |
|---|---|---|---|
| G1 (F3 残) | 最初の `VLIFE_VISIT` で pending と観測した版が、外側ループの条件評価より前に committed へ確定すると待機本体に入らず、確定 status で記録されない | real | read_internal の走査が終わって選択版が決まった時点で、その版を最初の観測で pending として扱っていたなら確定 status で 1 回だけ記録し直す (先頭 K 候補と `vlife_selected_upper`)。追加の鎖走査・二重計数をしない |
| G2 (F4 残) | deleted 版で失敗する read でも `vlife_reads_`・L・U を更新する | real | 既読集合 (L・U・`vlife_reads_`) は read が成功して read_set_ に入る経路だけで更新する。失敗 read (nullptr、deleted) は位置・hop のヒストグラムには数えてよいが、既読には入れない |
| G3 (F6 残) | measure が smoke JSON の自己申告の `selected_records` をそのまま受ける | real | measure は smoke JSON から (a) witness (`.text`・`.rodata` 一致、izanagi 文字列 0 件) と短い走の成功を確認し、(b) probe の maxrss と `l3_bytes` から選定規則 (maxrss > 4×L3 の最小 N、無ければ 1M) を再計算して `selected_records` と一致することを確かめる。どれかが外れたら拒否 |

変異の事前登録の追加:
- MUT-8 (G3): measure の選定再計算を外して自己申告の `selected_records` を受理 → 再計算不一致の拒否 test が KILLED
