# 2026-09-01 [T-434] 発効 topology の裁定 — 二段束縛を適用して認定記録の置き場を作る

ユーザーが 2026-09-01 に「codex に相談して決めて」と委任した範囲で、
`output/insights/2026-09-01_t434-cap-lift-receipt-v3/design-v3.md` §7 の 3 択に決着をつけた。

## 決着

3 択のいずれでもなく、**codex が提示した第 4 の道**を採った。決定本文は decisions 台帳を正本とする。

発効 topology を「内容 commit `G` + 発効 commit `A` (親集合が exact `{G}`、認定記録と受領証の
2 件だけを create-only 追加)」の二段束縛にする。**これは新機構ではなく D438 決定 (4) が
既に裁定した型の適用である。**

## codex が見つけた循環 (親が現物で追認した)

P6 の認定記録は `subject_revision_sha` に束縛される
(`output/insights/2026-08-04_t433-p6-sufficiency-contract/README.md` §8)。
対象 revision は実装を含む `G` が確定するまで決まらない。一方で先行設計 v2 §3 は
発効 commit が受領証 1 ファイルだけを追加すると書いていた
(`output/insights/2026-08-04_t434-cap-lift-receipt/design-v2.md`)。
両方を満たす commit が存在せず、**認定記録を置ける場所が無い**。
前 wave の段 2 プラン・段 3 の 2 レンズ・段 4 裁定のいずれもこれを見ていない。

## 親が独立に確かめたこと

- P6 の認定記録が revision 束縛であること、および失効規則。
- 条件評価の実装が `P6Unavailable` で無条件に停止すること
  (`orchestrator/campaign/reflux_formal_consumer.py`)。
- 発効 commit が追加してよい path 数を固定した既裁定は台帳に存在しないこと。
  したがって先行設計 v2 の当該一文は裁定済み択一 1〜10 の外にあり、精密化に
  ユーザー再裁定を要しない。
- D438 決定 (4) が同型の循環を二段束縛で解いた先例であること。

## file

| file | 中身 |
|---|---|
| `codex-recommendation.md` | codex の推奨の逐語 (read-only consult、reasoning=xhigh) |

先行する設計と裁定は `output/insights/2026-09-01_t434-cap-lift-receipt-v3/` を参照する。
