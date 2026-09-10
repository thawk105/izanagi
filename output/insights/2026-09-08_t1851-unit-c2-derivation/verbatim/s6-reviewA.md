## 受理集合が広がった箇所

- 7-key schema の導入は単なる縮小ではない。例えば `returncode=0`、`execution_failure=False`、`counter_status="not_required"`、`throughput=100.0` の正常な 7-key observation は、変更前には余分な key として拒否され、現在は complete として受理される。[s8b_floor_campaign.py:1934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:1934)、[s8b_floor_stats.py:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_stats.py:487)
- `notes=["5/5 reps failed to execute"]` と正常な 7-key observation 5 本を持つ入力は、変更前には `exec_failures=5` となり無効、現在は notes を無視して `exec_failures=0`、有効となる。自然文を信頼経路から外すための意図的な拡張だが、commit 本文の「受理集合は狭まる方向にしか動かない」は誤りである。[s8b_floor_campaign.py:1954](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:1954)
- terminal evidence は、`reps=3`、finite throughput 2 本、`exec_failures=0`、`rep_integrity_failures=1` の非 zero rc ケースを新たに受理する。旧式は `2 + 0 + 0 != 3` で拒否した。これは B1 が要求した意図的な拡張である。[s8b_terminal_evidence.py:860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_terminal_evidence.py:860)

## 2 量の分離の破れ

producer、campaign、中央 verifier の主経路では分離されている。

- `exec_failures` は `execution_failure is True` の本数。
- `rep_integrity_failures` は complete でない rep の本数。
- 非 zero rc だけなら `(exec, integrity)=(0,1)` となり、一方を他方から導けない。[s8b_floor_stats.py:515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_stats.py:515)、[s8b_floor_stats.py:595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_stats.py:595)
- artifact、resume、sealed terminal の三面で top-level `exec_failures` と sink 再導出値を独立比較している。

ただし terminal の「4 分類を別々に数える」という説明は実装より強い。式は

`other_integrity = rep_integrity - exec`

なので、総数式では `exec` が相殺され、実質的に

`finite + nonfinite + rep_integrity == reps` と `exec <= rep_integrity`

だけを検査する。[s8b_terminal_evidence.py:860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_terminal_evidence.py:860)

seal 経路では sink 再導出との等値が先にあるため、新しい producer-side の穴にはなっていない。ただし replay 文書単体の式が「4 分類を独立に証明する」とは主張できない。

## padding の None が落ちる経路

`None` は最終 gate では `False` と同一視されない。

- `_derive_rep_integrity()` が exact bool 違反を返す。[s8b_floor_stats.py:515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_stats.py:515)
- artifact verifier はその error を結果へ載せる。[s8b_floor_stats.py:917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_stats.py:917)
- resume は最初の evidence error で拒否する。[s8b_floor_campaign.py:8368](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:8368)
- opened terminal は snapshot 時に拒否する。[s8b_terminal_evidence.py:642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_terminal_evidence.py:642)

ただし `_project_scalepoint()` 内では `is True` の和を取るため、`None` と `False` は一時的にどちらも `exec_failures` へ 0 を寄与する。[s8b_floor_campaign.py:1954](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:1954) `rep_integrity_failures` が全 rep 分立つため成功扱いにはならないが、campaign は schema error をその場で raise せず、不正な retryable session 行を組み立てた後、verifierまたは resume で落とす。現テストは `None` が書かれたことしか確認せず、下流拒否を通していない。

## 発火しない条件 (恒真)

- `execution_failure=True` と非 null throughput の拒否条件自体は発火する。exact 7-key gate の後に到達し、terminal 側でもこの診断が最初に出る。[s8b_floor_stats.py:589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_stats.py:589)
- ただし対応する terminal 負例は単一理由ではない。対象条件を消しても、fixture の campaign record が元の throughput、integrity count のままなので、後続の throughput 等値または integrity 等値で拒否される。[test_s8b_terminal_evidence.py:551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/tests/test_s8b_terminal_evidence.py:551)
- S4 の M6 が要求した「returncode=0、counter complete、flag True」の `_project_scalepoint()` 負例は存在しない。最も近い test は `returncode=None` なので、`execution_failure is False` を消しても別条件で incomplete のままである。[test_s8b_floor_campaign.py:9443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/tests/test_s8b_floor_campaign.py:9443)
- B5 test の `len(observation)==7` と exact bool assert は、test 自身が直前に作った literal の検査であり恒真。AST 部分も未変更の pipeline を読むだけなので、test 全体が変更前コードでも通る。[test_backoff_extended_sweep.py:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/tests/test_backoff_extended_sweep.py:205)

## 過剰拒否

正当だった旧 6-key の measured session は一律に拒否される。具体的には、全 rep が `returncode=0`、完全 counter、有限 throughput の旧 journal でも、resume と artifact verifier の exact-key gate で拒否される。

これは S4 B7 が明示的に要求した前向き互換性の廃止であり、意図しない過剰拒否ではない。ただし「受理集合は狭まるだけ」という説明とは両立しない。新しい 7-key 入力の受理も同時に増えているため、実態は schema 集合の置換である。

## v1 側への波及

attempt-registry v1 の受理集合への波及は見つからない。

- v1 の profile、event key 集合、core、registry のいずれにも本 wave の差分はない。
- v1 の retryable reason 集合は空のままで、v2 専用 `measurement_retry_reason` と sealed terminal validator は v2 profile にだけ接続されている。[s8b_attempt_profile.py:649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_profile.py:649)、[s8b_attempt_profile.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_profile.py:701)
- shared runner の observation 出力は変わるが、v1 registry event の key 判定経路へは接続されていない。

## 診断だけの変化

次は kill または成果物挙動の変化として数えられない。

- B5 の test 全体。未変更 consumer の AST とローカル literal を検査する静的 pin であり、変更前でも通る。
- terminal の矛盾負例。対象 predicate を消しても後続等値 gate が拒否するため、現在の fixture が固定するのは最初の診断文字列である。
- stats の `test_verify_rejects_exec_count_mismatch_independently_of_integrity_count`。exec 等値検査を消しても、`exec_failures=1` に対して既存の session/cell 値を更新していないため、cell 再計算で artifact は拒否されたままになる。[test_s8b_floor_stats.py:1760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/tests/test_s8b_floor_stats.py:1760)
- exact な error 文字列の全件一致 assert は、拒否の有無に加えて wording まで固定する部分については診断 pin である。

## 過去の型の再発

- **F28 / F820 / F900 / F877:** M6 の殺し手が無く、M9 と terminal M12 の負例が後続 gate に mask される。S4 が明記した単一理由性を満たしていない。
- **F86:** 赤になる node と受理集合を変える kill を混同している。上記 M9/M12 は現状では diagnostic sensitivity である。
- **F822 / F836:** B5 は consumer 実体を呼ばず、読みやすい AST 面だけを固定している。ただし実 consumer は `observation.get("throughput")` の subset read のみであり、コード上の取り残し自体はない。[pipeline.py:2837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/pipeline.py:2837)
- **F82 / F1:** commit 説明の「受理集合は狭まる方向だけ」が実装と食い違う。
- **F879:** padding の unknown を top-level exec count では 0 に落とす代理化がある。ただし integrity と最終 schema gate が残るため、最終的な成功受理までは広がっていない。
- **F75:** 実装面 3 commit はすべて Codex `role=author` trailer を持つ。この停止条件には該当しない。

## blocker と nit の仕分け

Blocker:

- **FORMULA_ID gate 違反。** S4 B6 は、4 量のうち 1 つでも動けば停止し、据え置いてはならないと定める。[s4-adjudication.md:136](/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s4-adjudication.md:136) 実装 test 自身が post-spawn exception ごとに `rep_integrity_failures` が増えると固定している一方、`FORMULA_ID` は v2 のままである。[test_s8b_floor_stats.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/tests/test_s8b_floor_stats.py:429)、[s8b_floor_stats.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_stats.py:16) 診断も formula の一部だと正本が明記しているため、session validity と median が不変でも据え置き条件を満たさない。ユーザー裁定なしにこの wave を受入完了にはできない。
- **S4 の変異単一理由性未達。** M6 の負例欠落、M9/M12 の masking を解消しない限り、段 4 の受入基準を満たさない。

Nit:

- padding `None` は最終 gate で拒否されるが、その end-to-end 負例が無い。
- terminal の式は producer-side では正しいが、「4 分類を別々に数える」という説明を、実際の「integrity 総数と exec subset」に合わせる必要がある。
- B5 の AST test は将来の consumer drift pin としては有用だが、今回の 7-key 対応を動的に通した証拠ではない。

## 総括

コード上、`exec_failures` と `rep_integrity_failures` の直接的な代理化、padding `None` の最終受理、v1 registry への波及は見つからない。一方で受理集合は明確に広がっており、「狭まるだけ」という説明は誤りである。

受入を止める主因は、実測で `rep_integrity_failures` が変わったにもかかわらず `FORMULA_ID` を据え置いた B6 違反である。加えて M6、M9、M12 の単一理由性が実装後コードで成立しておらず、F28/F900 型が再発している。こちらではテストを実行しておらず、親の 675 passed / 3 skipped は提示済み事実としてのみ扱った。