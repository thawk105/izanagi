## 対応表

対象 HEAD：`6dc046add`。`88071a245` との差分を読取専用で検査した。

| 前巡所見 | 判定 | 対応 | 根拠 | 成果物影響（DW-G05） |
|---|---|---|---|---|
| M1：禁止された外挿と遵守の過大記録 | real | **closed** | [README.md:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:159)、[worklog fragment:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/docs/spool/worklog/2026-09-22-dev-wave-t2795-k2-pair-resubmit-1.md:17)。外挿禁止への違反、初投入前の確認漏れ、4 巡目前の取り直しを分けて開示。 | 遵守の過大記録は解消。測定値・判定の変更は不要。 |
| S1：候補間差の不確かさの言い過ぎ | real | **closed** | [README.md:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:126)。stock の観測差と候補間比較の不確かさを区別し、後者は未推定と明記。 | stock の差を不確かさの推定値と読ませる記述は解消。 |

## must-fix

残件なし。

**refuted：修正後も裁定遵守を過大・過小に開示している。**
[D2211 項1:70717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/docs/decisions.md:70717) は投入前の合計見積りと外挿禁止を明示する。採用可能な pair 実測がない時点で、設定された上限だけでも確認ラインを超えるため、「1 本目の前に確認を取るべきだった」は支持される。6 node 時間は実使用ではなく実験 2 job の上限であり、付随検査を加えても結論は変わらない。第31回項1は外挿禁止を解除していない。

[README.md:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:164) は実測100秒による取り直しを別扱いにしており、初投入を遡って正当化していない。brief の指定区間の `git diff` は空だった。

**成果物影響（DW-G05）：確認漏れの開示は適切で、測定・認定結果を撤回する根拠はない。**

## should

残件なし。

**refuted：fix が周辺記録との矛盾を生んだ。**
[README.md:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:33) の候補間比較・一般化の限定と、修正後§3は整合する。§1〜§5の数値は不変。[round 3 README.md:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-19/k2-loop-round3/README.md:214) と [phase3.md:536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/docs/phase3.md:536) も差分は空で、成立結果・比・還流未実施の記述は一致する。

**成果物影響（DW-G05）：修正による数値・主張範囲・完了状態の回帰なし。**

## nit

残件なし。

**refuted：派生値・正規化記録の不一致。**

| 検査 | 再計算・確認結果 |
|---|---|
| walltime 上限 | [job body:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/tools/pegasus/p3_s4_loop_pegasus.sh:4) は1 node、3時間。[qsub-submit-pair.sh:54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/qsub-submit-pair.sh:54) に上書きなし。`3 × 1 × 2 = 6 node 時間`。 |
| 実使用 | 両原本 `job.stderr:25` の Elapse は100秒・107秒。`207 / 3600 = 0.0575 ≈ 0.06 node 時間`。 |
| 行末空白 | 原文の15行に存在し、除去した30 B以外の変更なし。 |
| bytes | `5,806 → 5,776 B`。 |
| SHA-256 | 原文 `241309447bd0b16c94942cdbcdc7abc3bac4804c6b5e5d92edc9d5526f6a9990`、保存版 `8576ad1e0bbe4d3190880d68038c72b4417b9d667b2e04027f3e8298f8e67309`。 |
| 空白無視比較 | 原文と保存版の `diff -w -B` は出力なし、rc=0。 |

[README.md:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:193) の記録と一致した。

**成果物影響（DW-G05）：派生値・レビュー保存内容の訂正は不要。**

**refuted：failures fragment の形式・参照不備。**
[failures fragment:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/docs/spool/failures/2026-09-22-dev-wave-t2795-k2-pair-resubmit-2.md:9) は指定のH2・H3形式を満たす。タグ `[権限逸脱] [手順漏れ]` は台帳語彙に存在。恒久対応先の [memory:32](/home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/memory/experiment-compute-needs-user-confirmation.md:32) は実在し、対応内容も一致する。placeholder は worklog と完全一致し、frontmatter・ファイル名・LF・末尾改行も適合する。

**成果物影響（DW-G05）：形式違反・参照切れによる阻害なし。**

## 総括

**GO。** M1 / S1 はともに closed。
指定された派生値は再計算で一致し、開示・fragment形式・周辺記述に修正を要する問題は認めなかった。