## 総括

**NO-GO、must-fix 1件。** 比較driverが未完了同士の一致を受入成功にできるため、現状で回収受理はできません。productionの追加修正は要求しません。

監査対象HEADは`30fe5cc34318dbb995b9a32d15a805eeb5ea9ee5`。比較起点から対象2ファイルは **719行追加／19行削除**。そのうち回収固有差分はテストselectorの **7行追加／7行削除**で、productionは取り込み時と同一です。repo外driverは117行です。

テスト・変異・性能測定は**未実走**。既報の370 pass／3 failは再検証していません。author未受理報告を成功証拠には使用していません。

## 所見

- **real／高／must-fix：正常完了を確認せず比較成功を返す。**
  [ab_compare.py:113](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2686-recovery-codex/ab_compare.py:113)の成功条件はcanonical一致、main一致、process減だけです。[check_branch_landed.py:2138](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2686-recovery-codex/tools/check_branch_landed.py:2138)ではtimeout・parse失敗も例外終了せずindeterminate payloadとして返ります。
  **静的再現根拠：** 4走のtiming以外が同じtimeout payload、mainが同一、process数が旧100／新90なら、現在の成功式は真になります。これは「正常完了時の同一」という親の受入要件を満たしません。
  **影響：** 未完了結果を正常完了比較の受領証として誤受理できます。
  **最小修正：** driver内で各走の正常完了状態を記録し、既存のphase・evidenceにtimeout／error／truncatedがある走を比較成功から除外してください。必要な処理の完了を確認し、正当に不要な`not-applicable`は許容する局所修正で十分です。単なる`verdict == landed`への置換は不要です。

- **refuted／テスト弱体化・計測カウンタ混同。**
  [test_check_branch_landed.py:2382](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2686-recovery-codex/orchestrator/tests/test_check_branch_landed.py:2382)で観測をunionの`log --name-only`へ限定し、期待0/1、hot path除外、同path複数unitのassertを維持しています。回収前後の全373個のassertはAST比較で一致しました。これはassert数であり、pass数ではありません。productionカウンタも変更されていません。

- **refuted／m10の複数理由変異。**
  [author-unaccepted.md:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2686-recovery-codex/author-unaccepted.md:10)の候補は正常parseと候補列distinct化を維持し、上限判定の計数単位だけをentry数へ変更します。[test_check_branch_landed.py:2280](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2686-recovery-codex/orchestrator/tests/test_check_branch_landed.py:2280)のfixtureは4 distinct commitsにmerge重複entryが加わるため、変異では`n > 4`による拒否が予測されます。構文破損や候補順変更によるkillではありません。ただしKILLEDの実証は未実走です。

driverの固定target・900秒・旧新旧新・全走main前後照合・source hash保存・timing除外範囲は説明と一致しています。基準版hashもhandoff記載値と一致しました。不要なgate・台帳・一般化の追加は認めませんでした。

## 根因対応表

| 根因 | 判定 | 根拠と限界 |
|---|---|---|
| 観測selector混同 | **closed（静的）** | `diff --name-only`を除外し、期待値・assert不変。3件の赤が解消したという実走確認は未了。 |
| timeout注入 | **closed（静的）** | [2430行](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2686-recovery-codex/orchestrator/tests/test_check_branch_landed.py:2430)の注入・例外観測と偽gitのselectorがunion logを対象とする。再走査ではattempt 2／実process 1の区別も維持。実際のtimeout発火・memo検査は未実走。 |

正証拠照合をlimit超過判定より先に行う順序、closed-world負判定、未証明時のindeterminateは差分上維持されています。時間内完走集合の同一性や一般的な速度改善は、この監査から主張できません。
