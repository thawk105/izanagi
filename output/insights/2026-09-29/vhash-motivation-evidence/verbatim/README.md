# 段 6 の点検の逐語 (md_27)

- `s6-review.md`: Codex (`gpt-6-sol`、`medium`、read-only) の 1 回目のレビュー出力。
- `s6-focus.md`: 同じ構成の焦点再レビュー出力。

## 可逆な正規化の記録

`git diff --check` に抵触する行末空白 (Markdown の改行用の空白 2 つ) だけを外した。可視文字は変えていない。
復元するには、下の行の末尾に半角空白 2 つを足す。

| file | 原文 SHA-256 | 原文 bytes | 正規化後 SHA-256 | 正規化後 bytes | 外した箇所 |
|---|---|---|---|---|---|
| s6-review.md | 0769cffdd76b0e550aea45bfad3081d1730886a58efcb3ca7e33d420a7f26677 | 7602 | c9a3ec0359b65eaa0b2985aa18283b533ad83bfdc8e402e2dc0584364e76d7e4 | 7600 | 45 行目の末尾の空白 2 つ |
| s6-focus.md | 69b9c1d3e4be43471f41a97b0e1f5bce557e6d843ded8bd4889dd44e4430fc5a | 5533 | 4df3fe397c726da67b7a463f5f095d2b07ad66cb822035962fb81badb6d96004 | 5531 | 35 行目の末尾の空白 2 つ |
