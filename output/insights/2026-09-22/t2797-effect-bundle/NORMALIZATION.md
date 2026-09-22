# 逐語の可逆最小正規化 (DW-S07、`git diff --check` 対応)

可視文字は変えていない。原本は repo 外の job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/codex/` の同名 file) に残る。

| file | 原文 sha256 | 原文 bytes | 除去したもの | 正規化後 sha256 | 正規化後 bytes | 復元法 |
|---|---|---:|---|---|---:|---|
| `verbatim/s2-plan.md` | `519fe0e5f45d34ca11c2a03d32bed04e5d038fd9a49c273468f0aed8f6a2061f` | 42,726 | 430 行目の行末空白 2 個 (markdown の強制改行) | `7eacd4523ce85ccf0a90d3e81b890d457d060119aae46f87a01eafc1b92a11f3` | 42,724 | 430 行目の末尾に空白 2 個を足す |
| `verbatim/s6-fix-B2.md` | `09c4f3d90d403e09c6a4dd415b1a2e764f6ff06f3d69fea48f548d9a8612b249` | 1,658 | 25 行目 (空白 3 個だけの行) の空白 3 個 | `e36bf39daba4e6ef86b7d31f20375be393c028e4be8eab4cdd667180498efa35` | 1,655 | 25 行目に空白 3 個を置く |
| `verbatim/s6-fix-A1.md` | `e1830c1be7f53e59726f0852e49b23f986457d23339c0edbb01aa93b0be3f16e` | 1,740 | 17 行目 (空白 3 個だけの行) の空白 3 個 | `53b88a83a14333926d7619f2041940297f87ad9c63e83fadf6c2c8d20e8386a8` | 1,737 | 17 行目に空白 3 個を置く |
