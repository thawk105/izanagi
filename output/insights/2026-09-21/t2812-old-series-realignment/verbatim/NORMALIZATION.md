# 逐語の可逆最小正規化 (行末空白の除去)

Codex 子の出力は Markdown の強制改行に行末 2 空白を使うため、そのままでは `git diff --check` が
trailing whitespace で赤になる。DW-S07 が許す**可逆な最小正規化**として、各行の**行末空白だけ**を
除去した (可視文字は 1 byte も変えていない)。原文は job dir (repo 外) に無改変で残っている。

| repo 内の file | 原文 (job dir `dev-wave-jobs/dev-wave-t2812-old-series-realignment/codex/`) | 原文 sha256 | 原文 bytes |
|---|---|---|---|
| `s2-plan.md` | `s2-plan.md` | `abc546c611e6b14e591712cf228fd654aeef95ac4173822a2e2c3369e37c5d27` | 25274 |
| `s3-consult-A.md` | `s3-consult-A.md` | `8822bc0771982d24a393f0217d84568ffba8c1672bd6e5c79eb2ecf36157649f` | 10513 |
| `s3-consult-B.md` | `s3-consult-B.md` | `3b5fe49112c25ba8881cfada650a7d00926d1e0b258ae4f39d15d8cfdde1eed8` | 11762 |
| `s6-review-A.md` | `s6-review-A.md` | `46b9367d16c62baae6bf9f5b225c22a3e3efe1a38f5b980d23cb80574e93f2a9` | 10651 |
| `probe-author-report.md` | `probe-author.md` | `7b1226d5f2a36aa00fe690a85b520ab3dec96aa9d025b79056e3396ab6e76582` | 4921 |
| `probe-fix1-report.md` | `probe-fix1.md` | `4810d19a5f639c0ecc277b7a6e7698f9f150c4b658410f205391982de6fd04ef` | 1718 |

**復元法:** 原文が失われた場合、repo 内の file から原文 bytes を機械的に復元することはできない
(除去した空白の位置は保存していない)。上の sha256 は原文の同一性照合に使う。原文の逐語が要る
consumer は job dir の file を参照する。正規化後の file も、**可視文字・行数・行の順序は原文と同じ**である。
