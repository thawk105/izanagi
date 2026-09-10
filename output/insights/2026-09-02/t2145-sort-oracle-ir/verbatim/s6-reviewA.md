## 所見 1 — body の異常が parameter signature 違反へ誤分類される

所見: 親所見のとおり、`return` が parameter 定義へ混入しているため、正しい署名の後で body が `while`、`throw`、呼び出しなどから始まる入力も `sort-ir.parameter-signature.v1` になる。受理可否は正しいが、決定順序と規律 3 を破る。

根拠 (file:line): [`sort_swo_oracle.py:596`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:596) で両 parameter tuple が `{`, `return` まで含み、[`sort_swo_oracle.py:727`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:727) で expression parser より前に signature reject する。

成果物影響 1 行: 受理集合は変わらないが、材料レポートと試行台帳へ誤った原因が入り、次の合成が正しい署名を修正対象にしてしまう。

must-fix か nit か: must-fix

推奨: `return` を parameter tuple から外し、署名確定後に body production として判定して、当該例を `expression-shape` へ帰属させる。

## 所見 2 — 正準 IR の compile/run failure が候補 REJECT のまま残る

所見: byte exact の行列不一致自体は正しく `UNAVAILABLE` になる。一方、候補ではなく trusted renderer が生成した正準 TU の compile failure、および行列取得前の timeout・execution・nondeterminism finding は旧分類のまま最終 `REJECT` へ流れる。R2 が定めた「実 TU conformance 違反は実装・環境 drift、したがって UNAVAILABLE」に反する。

根拠 (file:line): [`sort_swo_oracle.py:3263`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:3263) で compile 対象は正準形だが、[`sort_swo_oracle.py:3275`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:3275) の finding と [`sort_swo_oracle.py:2893`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:2893) の run finding は [`sort_swo_oracle.py:3380`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:3380) で REJECT になる。既存テストも [`test_sort_swo_oracle.py:1493`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:1493) でこの旧期待を固定している。裁定は [`s4-adjudication.md:94`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2145-sort-oracle-ir/s4-adjudication.md:94)。

成果物影響 1 行: 正当な IR が候補 REJECT として試行台帳と critic へ混入し、その値の certified 選択を失わせる。

must-fix か nit か: must-fix

推奨: `ir` 付き評価では compile/run finding を candidate finding にせず `UNAVAILABLE` へ帰属させ、旧 raw harness 用の `ir=None` の分類だけを維持する。

## 所見 3 — 恒真化した SWO・closed-region 検査が auditor の実効 veto に残る

所見: admission 通過後は 79 個の構成的 SWO 正準形だけなのに、実 auditor は非 SWO、追加関数、呼び出し、loop、throw を候補違反として判定するよう指示されたままで、その verdict は acceptance を狭める実効 veto である。

根拠 (file:line): [`auditor.md:58`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/.claude/agents/auditor.md:58) と [`auditor.md:66`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/.claude/agents/auditor.md:66) が型 14・17〜21 を auditor の職務にしている。機械 admission 後の結果は [`p3_s4_loop_sort.py:193`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/p3_s4_loop_sort.py:193) から auditor veto へ入り、reject/uncertain は [`auditor_gate.py:219`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/auditor_gate.py:219) で実際に拒否される。

成果物影響 1 行: auditor の誤判定だけで正準 IR が試行台帳の reject となり、受理集合と certified 選択が不当に狭まる。

must-fix か nit か: must-fix

推奨: sort IR では型 14・17〜21を renderer/admission の事後条件と明記して auditor veto の根拠から外し、依然可変な marker 侵食と fairness 監査は維持する。

## 所見 4 — 現役の保証記述が旧「動的反例 gate」を数え続ける

所見: oracle 本体と receipt は更新されたが、現役 driver docstring、運用 runbook、s6 sweep の説明は依然として「候補の SWO 反例を動的に探す gate」と記述している。R10 と実装後の保証境界に反する。

根拠 (file:line): [`p3_s4_loop_sort.py:47`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/p3_s4_loop_sort.py:47)、[`phase3-s5-sort-runbook.md:190`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/docs/phase3-s5-sort-runbook.md:190)、[`s6_sort_sweep.py:28`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/s6_sort_sweep.py:28)。裁定は [`s4-adjudication.md:97`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2145-sort-oracle-ir/s4-adjudication.md:97)。

成果物影響 1 行: 値と受理集合は直接変わらないが、材料レポートと運用参照が発火不能な旧 gate を保証根拠として指し、試行分類の読み方を誤らせる。

must-fix か nit か: must-fix

推奨: 現役記述だけを「IR membership + trusted evaluator + 実 TU conformance」へ更新し、歴史的な D344 の raw 実験記録は変更しない。

## 所見 5 — 既存の public rejection テストが private 恒真 postcondition へ弱められた

所見: qualified `std::sort` と複数 statement の既存テストは、public oracle の REJECT 検査から `_validate_single_sort_statement` の直接検査へ変更された。これは恒真化した旧 validator を再び検査根拠にし、public admission の既存期待を弱めている。

根拠 (file:line): 変更は [`s5.patch:1619`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2145-sort-oracle-ir/s5.patch:1619)、現行テストは [`test_sort_swo_oracle.py:1322`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:1322)。新しい public 負例集合 [`test_sort_swo_oracle.py:347`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:347) はこの exact 2 例を保持していない。

成果物影響 1 行: 現在の値は変わらないが、public 受理境界がこの 2 例を通す退行でも既存テスト参照が赤にならなくなる。

must-fix か nit か: must-fix

推奨: 同じ 2 例を public `check_materialized_sort_swo` 経路へ戻し、期待理由だけを新しい `sort-ir.*` 分類へ追随させる。

## 総括

(1) must-fix: 5 件。診断帰属、正準 TU failure の REJECT、auditor の恒真 veto、旧保証記述、public テストの弱化。token 化・正準化から受理集合が広がる経路、および行列不一致が PASS になる経路は見つからなかった。  
(2) nit: 無し。pointer rank は arena の単調 allocation、null、別 allocation、corpus 外 fail-closed と整合している。pytest は 0 件で、緑とは判定していない。  
(3) 新しい policy 選択が要る箇所: 無し。