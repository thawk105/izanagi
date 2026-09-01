# erratum — 逐語 2 本の可逆最小正規化 (2026-09-01)

`s3-lensA.md` と `s3-lensB.md` は段 3 の codex 子の出力そのままである。原文は markdown の
hard line break のために行末へ半角空白 2 個を持つ行があり、`git diff --check` に抵触した。
`DW-S07` に従い、**可視文字を変えない可逆な最小正規化**だけを行った。

## 正規化の内容

行末の空白と tab を除去した (`sed -i 's/[ \t]*$//'`)。それ以外の byte は変えていない。
可視文字・行数・行の順序・文字符号化 (UTF-8 / LF) はいずれも不変である。

## 原文と正規化後の対応

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes |
|---|---|---|---|---|
| `s3-lensA.md` | `b7055e6826bb52299e7ded055aa4a036ae644494c6c94cd2e4cb40ae116cede0` | 12129 | `d108d51dfde34f9d9aa1d99c344fbcffe25d1b6bf6e71753c7717a89151d54e6` | 12057 |
| `s3-lensB.md` | `cfe5468c23a1aa8bba63de4dd87761a2002a68bbc08d1a99cb4262e5de596f17` | 18688 | `e96b4c47e0969ad8eae500a73b07c803a2b8ff6fec18ea1fa7c77fa106389333` | 18628 |

差分は `s3-lensA.md` が 72 bytes、`s3-lensB.md` が 60 bytes で、いずれも除去した行末空白の総量に一致する。

## 復元法

除去したのは行末の空白のみで、位置は正規化後の file から一意に再現できない (どの行が
2 個の空白を持っていたかは可視文字に残らない)。原文そのものは codex の job 成果物として
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/artifacts/dev-wave-t434-cap-lift-receipt/`
配下の `s3-lensA.md` / `s3-lensB.md` に残る (上表の原文 sha256 で同一性を照合できる)。
job dir は session 寿命に依存するため、**この erratum の hash 表が原文の同一性を示す耐久記録**である。
