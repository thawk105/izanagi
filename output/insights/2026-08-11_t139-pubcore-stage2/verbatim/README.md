# 逐語の凍結 — [T-139] 公表 core 段階 2

段 1〜段 6 の親 brief・裁定と、codex 子の出力を**そのまま**凍結したもの。
結論の正本は 1 つ上のディレクトリの `package.md` と 3 文書であり、本ディレクトリは経緯の証拠である。

| ファイル | 何か | 判定 |
|---|---|---|
| `s1-brief.md` | 段 1 親 brief | — |
| `s2-plan.md` | 段 2 プラン起草 (codex sol / max) | GO |
| `s3-lensA.md` | 段 3 敵対相談 レンズ A (sol / max、凍結境界と正しさ) | **NO-GO** blocker 3 |
| `s3-lensB.md` | 段 3 敵対相談 レンズ B (luna / max、裁定整合と実効性) | **NO-GO** blocker 8 |
| `s4-adjudication.md` | 段 4 親裁定 (real 15 / refuted 2、新事実 N1〜N4) | — |
| `s6-lensC.md` | 段 6 敵対レビュー レンズ C (書かれた bytes の検査) | **NO-GO** blocker 3 |
| `s6-lensD.md` | 段 6 敵対レビュー レンズ D (裁定整合と記録の正確性) | **NO-GO** blocker 6 |
| `s6-focus.md` | 段 6 焦点再レビュー 1 巡目 | **NO-GO** closed 35 / partial 5 / regressed 4 / not-addressed 2 |
| `s6-focus2.md` | 段 6 焦点再レビュー 2 巡目 | **NO-GO** closed 6 / partial 3 / **regressed 0** / not-addressed 2 |

fix は 3 巡行い (`DW-O16` の上限)、3 巡目で partial 3 件を閉じた。
残る not-addressed 2 件は、追補 B の envelope 説明と実 parser の fence 規則が逆という 1 つの
事実を 2 レンズが別々に挙げたものである。**現 bytes には該当する fenced 見出しが無く受理集合を
変えない**ため、初版の逐語保存を優先して直していない (`package.md` §4 に記録)。

## erratum — `s6-lensC.md` の可逆 defang (D88)

`s6-lensC.md` の 1 行で、レンズ C が `check_docs.py` の placeholder 検査 literal 3 つを
逐語引用していた。**凍結逐語が gate の検出語を含む状態を避けるため、D88 に従って
角括弧を `«` `»` へ置換した** (可視文字のみの可逆変換。他の bytes は変えていない)。

- **defang 前の原文 sha256** = `4c70f4bcd184c9959928cc801079ec1ab7a821ecdf1ffd01ac3b24b9b773ff21`
- **復元法** = 当該行の `«` を `<` へ、`»` を `>` へ戻す。置換は当該 1 行の 3 対のみ。
- 本 wave の実測時点では `tools/check_docs.py` は本ファイルを走査しない
  (insights の列挙が `output/insights/*.md` で再帰しないため) が、
  **将来の再帰的検査に備えて先に defang した。**gate が赤だったための処置ではない。
