| 所見 | 状態 | 根拠 |
|---|---|---|
| R1 | closed | 登録 78・取得証拠あり 77・未走 1 に訂正。[README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/output/insights/2026-09-26/carry-triage/README.md:62)、[worklog](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/docs/spool/worklog/2026-09-26-dev-wave-carry-triage-20260926-1.md:586)、[決定 fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/docs/spool/decisions/2026-09-26-dev-wave-carry-triage-20260926-2.md:59) |
| R2 | closed | T-2323 を残す側へ戻した。[kept.tsv](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/output/insights/2026-09-26/carry-triage/kept.tsv:54) |
| R3 | closed | T-2754 を既存の穴の局所修正として残した。[kept.tsv](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/output/insights/2026-09-26/carry-triage/kept.tsv:87) |
| R4 | closed | T-2755 を残し、同型の実測を持つ T-2726・T-2727 も戻した。[kept.tsv](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/output/insights/2026-09-26/carry-triage/kept.tsv:82)、[T-2755](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/output/insights/2026-09-26/carry-triage/kept.tsv:88) |
| R5 | closed | T-1883 を残す側へ戻した。[kept.tsv](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/output/insights/2026-09-26/carry-triage/kept.tsv:27) |
| R6 | partial | T-2402 は (c) から (a) に直したが、「実害の実測が無い」を理由に確認手番ごと取り下げた。[worklog](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/docs/spool/worklog/2026-09-26-dev-wave-carry-triage-20260926-1.md:1063)。この根拠は下記 N1 のとおり D1884・D2104 と整合しない。 |
| R7 | closed | T-2092 の件数不一致調査を残した。[kept.tsv](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/output/insights/2026-09-26/carry-triage/kept.tsv:35) |
| R8 | closed | T-1768 を文書訂正の (b) に改めた。[worklog](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/docs/spool/worklog/2026-09-26-dev-wave-carry-triage-20260926-1.md:463) |
| R9 | closed | T-2466 に旧系列タグと再起票文を加えた。[worklog](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/docs/spool/worklog/2026-09-26-dev-wave-carry-triage-20260926-1.md:1147) |
| R10 | closed | 変更の射程を「持ち越しの走査対象から 506 項を外した」に訂正した。[決定 fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/docs/spool/decisions/2026-09-26-dev-wave-carry-triage-20260926-2.md:35) |

N1 | must-fix | [T-2402 の取り下げ理由](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/docs/spool/worklog/2026-09-26-dev-wave-carry-triage-20260926-1.md:1063) | [D2104 項26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/docs/decisions.md:65098)は閉包への帰属確認と、その結果に応じた実装・再諮問を残す。[D1884](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/docs/decisions.md:56946)は推移閉包の段階実装を継続し、実害 0 件を据え置きの根拠にできないと明記する。修正後の「実害の実測が無い」は、確認手番を消す根拠にならない | T-2402 を残す側へ戻すか、両決定を変更した後続裁定を示して理由と件数を直す。

## 総括

**NO-GO。must-fix 1 件。** 静的照合では `all.tsv` の 619 項と最終一覧の **取り下げ 506・残す 113** が一致し、筆頭区分 **a 185 / b 116 / c 102 / old 90 / d 13**、old を含む **119** も一致した。worklog の `### 完了` にある 506 項は、各項の理由・`remaining: none`・`base:` と `digests.txt` の一致、旧系列の再起票文を確認した。指定の 7 項はすべて `完了` から消えている。受領証も相談 4 本が **21〜33 call・206〜318 秒**、レビュー 1 本が **32 call・400 秒**で記述と一致した。