# erratum — 逐語 1 本の可逆最小正規化 (2026-09-01)

`codex-recommendation.md` は codex 子の出力そのままである。原文は markdown の hard line break の
ために行末へ半角空白 2 個を持つ行があり、`git diff --check` に抵触した。`DW-S07` に従い、
**可視文字を変えない可逆な最小正規化**だけを行った。

## 正規化の内容

行末の空白と tab を除去した (`sed -i 's/[ \t]*$//'`)。それ以外の byte は変えていない。
可視文字・行数・行の順序・文字符号化 (UTF-8 / LF) はいずれも不変である。

## 原文と正規化後の対応

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes |
|---|---|---|---|---|
| `codex-recommendation.md` | `ee26e3486390408e3fff78c66b42fcf5b4c9c15e0498ddbf0a23405caab2ac18` | 9033 | `ba6568fcde28ca2b06ab6145b07f9d2f35d52c56c2d427ee120a43b419b263cc` | 9021 |

差分は 12 bytes で、除去した行末空白の総量 (6 行 x 2 byte) に一致する。

## 復元法

除去したのは行末の空白のみで、どの行が空白を持っていたかは可視文字に残らないため、
正規化後の file だけからは一意に再現できない。原文は codex の job 成果物として
`/work/1/SFC/tanab/dev-wave-jobs/t434-ruling-consult/artifacts/t434-ruling-consult/recommendation.md`
に残る (上表の原文 sha256 で同一性を照合できる)。job dir は session 寿命に依存するため、
**この erratum の hash 表が原文の同一性を示す耐久記録**である。
