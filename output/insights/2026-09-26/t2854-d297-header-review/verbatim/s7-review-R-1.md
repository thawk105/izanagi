## 所見

- **should — 前処理に生成物が必要な範囲を狭める。** [insight §2](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/output/insights/2026-09-26/t2854-d297-header-review/README.md:42)、[decisions fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/docs/spool/decisions/2026-09-26-t2854-d297-header-review-1.md:26)、[worklog fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/docs/spool/worklog/2026-09-26-t2854-d297-header-review-1.md:13) は「全 TU の前処理」に `config.h` が必要と読める。[相談 B 所見 5](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/output/insights/2026-09-26/t2854-d297-header-review/verbatim/s3-consult-B.md:13) と[段 4 裁定](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/output/insights/2026-09-26/t2854-d297-header-review/verbatim/s4-ruling.md:21) が確定したのは、試した走行の失敗と、**選定 entry に必要な生成物を用意する**ことまで。各箇所をその表現に直す。

そのほか、実物から再計算した **135 entry（source root 内 117）、consumer 21 entry／12 file、production consumer の silo・mocc・si、receipt の 13＋13＋13＝39 call・356.2＋166.7＋172.6＝695.5 秒**は記録と一致した。[consumer 実測](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/evidence/consumers-c.txt:1)、[genome configure 実測](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/evidence/genome-configure-measure.md:9)、[receipt（plan）](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/codex/t2854-d297-header-review/t2854d297-s2-plan-1/receipt.json)。17 configure の数え方、裁定の成立／不成立、D780・D2244・D2249 に関する名乗りの境界も整合する。worklog の更新項は単位 1〜5・11、人間の手番、残り (2) を保持し、次の二つの裁定を示している。decisions fragment の形式に不整合や角括弧つきの有効な T 番号は見当たらない。

## 総括

**GO** — 記録の採用を妨げる不一致はない。

- should：前処理に生成物が必要な範囲の表現を、採用済みの相談所見に合わせて直す。