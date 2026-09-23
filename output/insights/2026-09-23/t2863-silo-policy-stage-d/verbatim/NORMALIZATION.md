# 逐語の正規化の記録

DW-S07 に従い、`git diff --check` に掛かる行末空白 (markdown の改行用の 2 空白) だけを可逆に除いた (可視文字は不変)。
原本は wave の job dir (`/home/SFC/tanab/.claude/jobs/8c90adaa/wave/`) に同名で残る。復元は、原本と同じ行の行末へ除いた空白を戻すこと
(原本の sha256 で照合する)。

| file | 原本の sha256 | 原本の byte 数 | 行末空白を持つ行数 | 正規化後の sha256 | 正規化後の byte 数 |
|---|---|---|---|---|---|
| `s2-plan.md` | `d0b3bf9cf36a217792b7e4bc536121009d14cd71dde63d93cdafa053aaec66ed` | 25242 | 2 | `ff464dbbf269a43e3677558754087294475305e2c6fdb39673e34483f91b36fb` | 25238 |
| `s6-focus-1.md` | `c2fb25350d7cd3e247255786acc9b786e36e2cb6998bd98cfa30baf32cab70f4` | 2899 | 2 | `4ea4d9f8f2a16352e8e35775f15f39ce915037684ba57e655e62310a659e43db` | 2895 |
| `s6-review-A.md` | `2f3195bcd53117fd9957610a976e86f54c84879c776d2da1d1fab020a2142529` | 1773 | 9 | `249ddc82d23009d712a352d8f6dae0c24cdf2ec98b3126c2ff7a15e308cf9785` | 1755 |
| `s6-review-B.md` | `29340cb007e851bf0d06f59cf45d8085898a5c8b647f81ab2e7d7a3fd4e8ce5b` | 2081 | 4 | `3af0d743b483cacbbb7f2b6e0f4595570f7278cb3a74a9652b6db2a2d405b58b` | 2073 |
