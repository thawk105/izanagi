## 判定

**NO-GO**

## 対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| 1 | closed | `failures-noscore.json` を再集計すると、15 系列と block job 3 本で投入 300・結果 300 の計 600 event はすべて `certified`、anomaly は 0。品質欠測 2 event は同一結果の投入・結果に対応する。[草稿 §11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/workload-description-critic-intervention-preregistration.md:338) の出典は整合する。 |
| 2 | partial | 予備の観察は本走の登録規則から外れ、結果に応じて実施・規模を選んだ場合の開示も加わった。一方、依頼は「本題の草稿と見積りだけ」だが、[insight §5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md:88) は予備の手順をユーザーの択一として残し、[草稿 §14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/workload-description-critic-intervention-preregistration.md:407) も確認事項にしている。 |
| 3 | closed | [insight §3.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md:70) は 10.9 時間を未測定の単純換算例とし、「上限」と 4 並列の暦見込みを外した。 |
| 4 | closed | [草稿 §7.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/workload-description-critic-intervention-preregistration.md:205) は同等分類と小さい差の識別に限定し、大きな差は分類されうると明記した。 |
| 5 | closed | [insight §2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md:22) の行番号は、harness の必須判定と `p3_s4_loop.py` の文法判定箇所に一致する。 |

## 新規所見

- **must-fix:** [決定断片の理由](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/spool/decisions/2026-09-28-dev-wave-t2852-p5-prereg-2.md:29) は「critic の解釈の有無以外を揃えられる」とするが、[草稿 §3.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/workload-description-critic-intervention-preregistration.md:109) は critic ありで失敗情報の重複も差に含むと明記する。決定断片の因果的な説明を草稿に合わせる必要がある。

## 総括

原データに基づく anomaly 件数と所見 3〜5 の修正は確認できた。予備の観察が依頼範囲内の選択肢として残る点と、決定断片の説明の矛盾が解消するまで、再レビューは NO-GO とする。