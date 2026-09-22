# 逐語の可逆最小正規化 (DW-S07、`git diff --check` 対応)

可視文字は変えていない。原本は repo 外の job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/codex/s2-plan.md`) に残る。

| file | 原文 sha256 | 原文 bytes | 除去したもの | 正規化後 sha256 | 正規化後 bytes | 復元法 |
|---|---|---:|---|---|---:|---|
| `verbatim/s2-plan.md` | `519fe0e5f45d34ca11c2a03d32bed04e5d038fd9a49c273468f0aed8f6a2061f` | 42,726 | 430 行目の行末空白 2 個 (markdown の強制改行) | `7eacd4523ce85ccf0a90d3e81b890d457d060119aae46f87a01eafc1b92a11f3` | 42,724 | 430 行目の末尾に空白 2 個を足す |
