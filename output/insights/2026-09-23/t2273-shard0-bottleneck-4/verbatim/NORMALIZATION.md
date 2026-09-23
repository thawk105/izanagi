# 逐語の行末空白の可逆正規化 (DW-S07)

Codex の最終報告は markdown の改行として行末に空白 2 個を置く。`git diff --check` に抵触するので、次の 5 file で**行末の空白 2 個 (直前が非空白の行だけ) を削除**した。可視文字は変えていない。
復元法: 下表の行数ぶん、`## 総括` 節の各行 (最終行を除く) の行末へ空白 2 個を戻すと原文の sha256 に一致する。原本は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/codex/` に同名で残っている。

| file | 原文 sha256 | 原文 bytes | 削除した行数 |
|---|---|---:|---:|
| s3-consult-out.md | c49ddb94a858d6bcf0202f8c3b1baf8969c5e5a68eb6433c394c0bc2ecf6c8f8 | 9600 | 4 |
| s5-author-out.md | cefb551c0ea6436e8a22ce9fcc11c51818d2305d1cd37d025b8b2b8c63e653e4 | 5626 | 3 |
| s5-author-r2-out.md | 9dad1b04a0a0dff19536d436729f53405743ffe393a048c981a2977cdfaa1bfa | 5777 | 3 |
| s5-fix1-out.md | 290d4245018840fad5ff5089e0815441f924ff6824d1f0fb88deece897929bfc | 1694 | 2 |
| s5-fix2-out.md | 7d006e5260d565c23d89ee317510e2457b91ba86db9f110ab1d82c10af9f96e8 | 1429 | 2 |
