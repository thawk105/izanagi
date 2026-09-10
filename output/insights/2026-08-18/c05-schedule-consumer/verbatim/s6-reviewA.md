## 所見

### C05-AUTH-001 / major

- 対象: [s8c_schedule.py:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_schedule.py:167), [s8c_schedule.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_schedule.py:191), [s8c_schedule.py:269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_schedule.py:269)
- 主張: `validate_authority` は key 集合と外側の型、JSON化可能性しか検査しない。全 mapping を `{}`、配列を `[]`、文字列を `""` にしても通り、`regenerate` は authority の軸を使わず固定の `ARMS` / `HOLDOUTS` から6セルを生成する。
- 反証されうる条件: 全 caller がこの関数の前に、実在する workload、role、binding、axis の非空・内容スキーマを別の fail-closed 検査で保証している場合。
- 成果物影響: C05 有効化後、空または不正な権威に束縛された schedule が exact/shared 検証を通り、certified 選択、材料レポート、試行台帳の authority hash 参照が実体を表さない受理集合まで広がる。

## 変異耐性の予測

静的予測であり、ここでは pytest を実走していない。

| id | 予測 | 理由 |
|---|---|---|
| m01 | KILLED | [s8c_schedule.py:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_schedule.py:438) の先頭 return は、単一 bit 反転を拒否する [test_s8c_schedule.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/tests/test_s8c_schedule.py:203) を壊す。 |
| m02 | KILLED | 有効 artifact を検証する [s8c_schedule.py:426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_schedule.py:426) が常に失敗し、正常系テストが落ちる。 |
| m03 | SURVIVED | [s8c_schedule.py:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_schedule.py:424) の exact 再生成が digest も比較するため、shared 呼出し削除を受理系テストは検出しない。負の対照は shared 関数を直接呼ぶだけ。 |
| m04 | KILLED | master seed を落とすと alpha と beta の順序が同一になり、[test_s8c_schedule.py:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/tests/test_s8c_schedule.py:111) の固定順序・差分 assertion に反する。 |
| m05 | KILLED | 欠落 key 検査を消すと後続の [s8c_schedule.py:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_schedule.py:189) が `KeyError` になり、`ScheduleError` を期待する [test_s8c_schedule.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/tests/test_s8c_schedule.py:145) を壊す。 |
| m06 | KILLED | 全 search-space key を変更する [test_s8c_schedule.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/tests/test_s8c_schedule.py:163) が、落とした field で同一 digest を検出する。 |
| m07 | SURVIVED | cell 数検査は [s8c_schedule.py:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/s8c_schedule.py:337) と [s8c_schedule.py:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/s8c_schedule.py:390) に重複し、単一削除は他方に mask される。異常 cell 数の fixture もない。 |
| m08 | SURVIVED | 重複 index の負の fixture がない。通常の artifact 経路では [s8c_schedule.py:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/s8c_schedule.py:424) の exact 比較も mask する。 |
| m09 | KILLED | [s8c_schedule.py:484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/s8c_schedule.py:484) を削除すると `schedule` が得られず、正常な cell 返却を検証する [test_s8c_schedule.py:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/tests/test_s8c_schedule.py:219) が落ちる。 |
| m10 | SURVIVED | 直接 evaluator テストは consumer を常に用意している [test_s8c_preregistration_predicates.py:2274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/tests/test_s8c_preregistration_predicates.py:2274) ため、consumer 不在分岐を通らない。 |

## 削除行の確認

`integrated-snapshot.patch` の全体を確認したが、内容削除行（`-` で始まり `--` ではない行）は 0 件だった。既存保証や既存期待値を削除して弱めた箇所はない。

## 総括

canonical JSON は再帰的に型検査され、digest preimage の明白な field 落ちは見つからなかった。  
主所見は authority の中身と軸の意味を検査せず、空の権威を受理する点である。  
C05 evaluator は SATISFIED 経路を持たず、registry 未登録の現状も変わらない。  
m03、m07、m08、m10 は既存テスト上 SURVIVED しそうである。  
親の実測結果を前提にし、自身は静的レビューのみ実施した。