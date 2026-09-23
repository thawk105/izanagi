3 版 merge の結果を [merge-result/test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-fix-2/merge-result/test_ccbench_spawn_sites.py) に書きました。

- **wave 側:** 共通祖先の 2935 行目で、`_build_variant` の期待行番号を `382` から `386` に変更。
- **main 側:** 共通祖先の 93 行目の直後に、trace archive 圧縮の説明と `_compress_trace_archive` の登録を 2 行追加。
- **重なり:** なし。結果の差分には両変更だけが含まれ、Python 構文解析も通りました。
- **SHA-256:** `3705281db8904351969853d3449ea8771f5d816c9d85554dc3a4cc3b75c9d219`

## 総括

両側の変更を取り込んだ 1 ファイルを作成しました。