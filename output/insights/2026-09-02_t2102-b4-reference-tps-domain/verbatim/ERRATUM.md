# erratum — 逐語の行末空白を可逆に正規化した

`git diff --check` が markdown の hard line break (行末 2 空白) を検出したため、
本 directory の 4 file から**行末の空白だけ**を除いた。可視文字は 1 文字も変えていない。

復元法: 各 file の該当行末へ空白を戻せば原文 bytes に一致する。原文そのものは
dev-wave job dir `2026-09-02_t2102-b4-reference-tps-range/t2102-b4-reference-tps-range/`
に残っている。

| file | 原文 sha256 | 原文 byte 数 |
|---|---|---|
| `s2-plan.md` | `2e5034164285c438e085f3f87e73e74494c11298aaf929dc0d6429b728972f45` | 13035 |
| `s3-sol.md` | `a825ab33e061325043ce1fa81b419b34122059cc02a6b94587b926f7aa969195` | 17729 |
| `s3-luna.md` | `4e31ebfeec7e4984bd9e1d5ea71310069ef39272002ac516e4b38f929286f514` | 13905 |
| `s3b-recheck.md` | `116ccd624f03a6a0af0b52cef541e95a91bff02b35d5e8124c737c964b4bd1ff` | 12365 |

`s1-brief.md`、`s4-ruling.md`、`measurement-addendum.md` は親が書いたもので、
行末空白を含まないため正規化していない。
