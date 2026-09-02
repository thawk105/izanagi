## 1. `reverify` による被覆という親前提が偽

**所見:** 親 brief が本 wave から除外した report、oracle judge、verdict は、実際には選択 identity を強制していない。`_launch_validate` の選択検査は `LaunchValidatedFreeze` の場合だけで、`reverify_published_freeze` が指定する `ReverifiedFreeze` では通らない。plan もこの誤った所有範囲を訂正していない。

**根拠 (file:line):**

- [brief.md:29](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/brief.md:29>) は三 consumer を被覆済みとしている。
- [s8b_ratified_freeze.py:3303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3303) の identity 検査には `result_type is LaunchValidatedFreeze` 条件がある。
- [s8b_ratified_freeze.py:3662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3662) は `ReverifiedFreeze` を渡す。
- [test_s8b_ratified_verify.py:975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_verify.py:975) は historical reverify が current selection を適用しないことを明示的に固定している。
- 未検査のまま成果物を書く箇所は [s8b_oracle_report.py:2547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_report.py:2547)、[s8b_oracle_judge.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_judge.py:749)、[s8b_verdict.py:828](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_verdict.py:828)。

**成果物影響:** current namespace により早い適格 run があっても、observations、oracle verdict、combined verdict が旧 selected floor を参照したまま生成され得る。

**must-fix か nit か:** **must-fix。** 少なくとも「被覆済み」という brief/plan の主張を撤回する必要がある。oracle manifest consumer 群まで保証するなら、historical reverify 自体ではなく各公開 consumer に狭い helper を通す必要がある。

## 2. 有効な g1 が manifest を生成できる正例がない

**所見:** plan の fixture 選択は分類 **(a) 他 test module からの import** だが、追加正例は `no-approved-spec` で終了し、manifest 構築にも出力にも到達しない。したがって「有効な g1 が今までどおり manifest を作れる」を証明しない。

**根拠 (file:line):**

- [plan.md:97](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:97>) は `test_s8b_ratified_freeze` を import し、[plan.md:112](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:112>) でその builder を使う。共有 fixture への移設でも manifest test 内の再構築でもない。
- 正例の期待値は [plan.md:115](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:115>) の `no-approved-spec` であり、実装では [s8b_oracle_manifest.py:1213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1213) で停止する。実際の manifest 構築は [s8b_oracle_manifest.py:1244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1244)。
- 使用する builder は [test_s8b_ratified_freeze.py:1126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_freeze.py:1126) で `floor` は埋めるが `budget` は埋めない。基底 v1 の `budget` は null で、manifest は [s8b_oracle_manifest.py:678](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:678) で拒否する。
- 既存 consumer 正例は [plan.md:99](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:99>) により全て synthetic g2 となるため、g1 の出力正例を代替しない。

**成果物影響:** g1 固有の統合不具合によって approved manifest の受理集合が縮小しても、実 g1 の candidate bytes と `verify_manifest` 成功を要求する test がない。

**must-fix か nit か:** **must-fix。** 非 null budget、整合する approved spec、generator source を備えた genuine g1 で、実 loader、実 selection helper、実 manifest 構築、出力、再検証まで通す正例が必要。

## 3. genuine g1 正例の選択述語部分は構成上恒真

**所見:** 計画した genuine g1 正例は earlier candidate を置かない。selection core は selected 自身を最初から eligible 集合へ入れるため、この fixture では rule-mismatch 条件が構成上成立しない。正例が実 callee を通るという記述自体は正しいが、非自明なのは protocol、path、env の束縛部分だけである。

**根拠 (file:line):**

- [plan.md:110](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:110>) の正例には earlier result の追加がない。
- [s8b_holdout_freeze.py:1948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_holdout_freeze.py:1948) で selected が無条件に eligible 集合へ入る。mismatch は earlier derived-eligible が追加された場合だけ [s8b_holdout_freeze.py:1957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_holdout_freeze.py:1957) で発火する。
- 負例は [plan.md:121](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:121>) でこの非自明条件を作っている。

**成果物影響:** 負例が earlier candidate の列挙と mismatch を検査するため、単独の成果物影響はない。正例の証明範囲の説明だけが過大である。

**must-fix か nit か:** **nit。**

## 4. root 省略変異の KILL 帰属が実 callee ではない

**所見:** root 省略と `ROOT` 置換を一つの変異行にまとめているが、root 省略では二引数を記録する wrapper が先に引数不一致で落ちる可能性が高い。plan が主張する「実 callee が実 repository を探索して落ちる」経路を通るのは `ROOT` 置換側である。

**根拠 (file:line):**

- wrapper は candidate と root を記録して同じ引数で委譲すると [plan.md:100](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:100>) にある。
- root 省略と `ROOT` 置換は [plan.md:136](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:136>) で同一 KILL 説明にされている。
- helper の root 既定値は [s8b_ratified_freeze.py:3558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3558)。

**成果物影響:** 変異自体は test を落とすため成果物影響はないが、KILL の呼出し経路と帰属証拠が記述どおりではない。

**must-fix か nit か:** **nit。**

## 5. 三つの拒否理由のうち consumer 変換を検査するのは一つだけ

**所見:** 三理由はいずれも既存 callee 由来で、新しい理由の増設はない。ただし追加 test が consumer 層で保存を確認するのは `floor-selection-rule-mismatch` だけである。`floor-selection-eligibility-underivable` だけを `floor-selection-unverifiable` へ潰す選択的変異は全計画 test を通り得る。

**根拠 (file:line):**

- 理由集合の主張は [plan.md:38](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:38>)。
- callee の出所は [s8b_ratified_freeze.py:3622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3622) と [s8b_ratified_freeze.py:3644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3644)。
- consumer 負例と reason 変異は mismatch だけを使う [plan.md:119](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:119>)、[plan.md:138](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:138>)。

**成果物影響:** 受理集合と成果物 bytes は変わらず、拒否 reason の識別精度だけが落ちる。

**must-fix か nit か:** **nit。**

## 総括

must-fix は **2 件**。最も重い所見は、親 brief の誤った `reverify` 一般化により report、oracle judge、verdict が選択未検査のまま成果物を生成できる点である。規律2を弱める production 用 test 分岐や既存 assert の緩和は提案内に見つからず、pytest は実行していない。