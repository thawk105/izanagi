## 対応表

| 所見 ID | 判定 | 根拠 |
|---|---|---|
| M1 | closed | [README.md:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/output/insights/2026-09-27/t2853-repro-rest/README.md:118)・同119、122、125 と同149–151 は試算の確認欄を「暫定で不要」に変更。同24、159 と [fragment:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/docs/spool/worklog/2026-09-27-wave-t2853-repro-rest-1.md:20) は、投入単位の全 job の Elapse 見積りで判定し直すと明記している。 |
| M2 | closed | [README.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/output/insights/2026-09-27/t2853-repro-rest/README.md:24) と [fragment:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/docs/spool/worklog/2026-09-27-wave-t2853-repro-rest-1.md:20) の要約は正典 306 session の **8.88〜9.83**。README 同121、154、159 は **4.18〜4.62** を floor を除いた標本だけの参考値と区別している。正典の内訳は[結果稿:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/docs/paper-story/results/2026-09-20-s1a-nine-pair-direct-comparison.md:130)。 |
| S1 | partial | [README.md:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/output/insights/2026-09-27/t2853-repro-rest/README.md:88) は調べた3箇所に範囲を限定した。一方、同17の「T-2850 試走 v2 は trace 保全を指定していない」は、試走全体についての断定のまま残る。 |

「不要」の全出現は README 13箇所、fragment 1箇所。試算について確定した「確認不要」は残っていない。内訳は、試算を**暫定**とする README 24、118、119、122、125、149–151、159 と fragment 20、実測 fig8b の確定判定が README 123、148、別の認可を要する fig15 が README 128、旧所見を説明する引用が README 172。

数値も一致する。[Elapse 記録:1–9](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/output/insights/2026-09-27/t2853-repro-rest/verbatim/elapse.log:1) から fig8b は (2,518＋2,514)÷3,600＝**1.40**、単価 104.5〜115.6 秒を24 variant に当てた fig2b は **0.70〜0.77**。同単価を正典306 session／標本144 session に当てると、それぞれ **8.88〜9.83**／**4.18〜4.62**。fig6 の **1.70** と fig11 の **1.69** は[計画稿:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/output/insights/2026-09-23/t2853-figure-rerun-plan/README.md:79)・同84の B-7 Elapse を用いた試算と合う。README §3.2・§3.3 の値と出所区分も、この範囲では整合する。

## 新規所見

- **N1・should-fix** — [README.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/output/insights/2026-09-27/t2853-repro-rest/README.md:17) は、同88で限定した調査結果を試走 v2 全体の「trace 保全を指定していない」に広げており、§0 と §2.3 が食い違う。**放置時の影響:** 未調査の保存経路を写しの完全性判断から外しかねない。**修正案:** §0 も「調べた3箇所では trace 保全設定が見つからず、保全先は特定できなかった」とする。

## 総括

NO-GO。M1・M2 と指定数値の照合は閉じた。S1 は §0 の断定が残るため partial。§0 を §2.3 の調査範囲に揃える修正が必要。