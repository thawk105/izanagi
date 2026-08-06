# [T-244] P3 ever-issued cell 台帳 (U-3) — 実装可否の検証と裁定

**結論: 実装しない。** ユーザー再裁定へ択一 3 件を返す。

## この dir の読み方

| ファイル | 内容 |
|---|---|
| `parent-measured.md` | 段 1 の前提実測 N1〜N9。N5 に erratum あり (両レンズが指摘した親の誤り) |
| `brief.md` | 段 1 brief。provisional 裁定 (P1)〜(P4) のうち 3 件は段 4 で撤回済み |
| `s4-adjudication.md` | **段 4 裁定の正本。**実装しない根拠 R1〜R4、所見の裁定表、返す択一 W-1〜W-3 |

段 2 のプランと段 3 の敵対 2 レンズの逐語は repo 外の wave job dir
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u3-ever-issued/`) の
`s2/plan.md`・`s3/lensA.md`・`s3/lensB.md` にある。

## 一文で

U-3 (a) が要求する「ever-issued」は台帳の**単調性**を要求するが、repo 内に置いた台帳は
authority と同じ主体が同じ commit で書き換えられるため単調にならず、単調性を与える 2 手段は
片方が既に却下済み (外部 append-only anchor) で、もう片方が未実装 (epoch router) である。

## 名乗りの上限

名乗ってよいのは「U-3 (a) の実装可否を段 2・3 で検証し、実装しないと裁定して択一を返した」まで。
P3 充足・provisioning 解禁・多世代開放・cap-lift・certified 選択は名乗らない。
「意味等価な再発行を防いだ」「全世代重複拒否を実装した」とも名乗らない。
実装差分が無いため、変異 matrix と実装後の受入全走は対象外である。
