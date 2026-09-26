| 所見 | 状態 | 根拠 |
|---|---|---|
| R6 | closed | T-2402 は取り下げ一覧と worklog の `完了` から消え、確認手番を残す項として [kept.tsv](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/output/insights/2026-09-26/carry-triage/kept.tsv:63) にある。[D2104 項26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/docs/decisions.md:65098) と整合する。 |
| N1 | closed | T-2402 に加え、同じ閉包の T-733・T-2344 と T-734 も残す側へ戻した。[fix-08-closure.tsv](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/output/insights/2026-09-26/carry-triage/verbatim/fix-08-closure.tsv:1)、[決定 fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/docs/spool/decisions/2026-09-26-dev-wave-carry-triage-20260926-2.md:30)。 |

N2 | nit | [worklog fragment:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/docs/spool/worklog/2026-09-26-dev-wave-carry-triage-20260926-1.md:14) | 「止める」裁定として D1075 だけを名指し、同じ文で残すとした T-734 の 2026-08-16 第 3 回裁定が抜けている。 | [決定 fragment:30–31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-carry-triage-20260926/docs/spool/decisions/2026-09-26-dev-wave-carry-triage-20260926-2.md:30) と同様に両裁定を記す。

## 総括

**GO。must-fix 0 件。** `all.tsv` の 619 項は取り下げ 502・残す 117 と一致した。取り下げの筆頭区分は **a 181 / b 116 / c 102 / old 90 / d 13**、old を含む項は **119**。段 6 で戻した 7 項と今回の 4 項も裁定表と一致する。worklog `完了` の 502 項はすべて取り下げ理由、`remaining: none`、`digests.txt` と一致する `base:` を持ち、old を含む項には再起票文がある。指定の 11 項はすべて `完了` から消えている。検査は静的照合のみ。