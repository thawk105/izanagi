## 総括

静的に追った範囲では、2 本目の pair job は系列 counter から別の計測 identity を作り、候補と stock に同じ計測 cfg・layout・認可 session を渡します。従来の claim によって build 前に止まる経路は解消されています。ただし、T1 の digest 検査には生成時点のずれがあり、runbook には系列 dir について誤った記述があります。

## 所見

1. **must-fix — T1 の digest 期待値が stock 実行後の WAL を使う。** 根拠: [test_p3_s4_loop_policy.py:842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:842)、[p3_s4_loop_policy.py:479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:479)。実装は候補の後、stock の前に digest を保存しますが、test は stock 終了後の admitted view から期待値を作ります。**放置時:** 正しい digest を赤にするか、stock を含む誤った digest を正例として要求し、レポートの参照範囲を変えます。**最小修正:** 完成後の view との全文一致を外し、2 本目の候補の証跡を含み stock の証跡を含まないことを確認する。**正例:** 2 本目の候補を含み、同じ job の stock を含まない系列 digest が通る。

2. **should — runbook の「系列 dir には 3 ファイルだけ」は誤り。** 根拠: [phase3-silo-policy-runbook.md:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/docs/phase3-silo-policy-runbook.md:108)、[p3_s4_loop_policy.py:515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:515)。既存の `record-reject` は系列 layout に WAL を記録します。**放置時:** 系列 WAL を異常な成果物と誤認し、レポートで参照すべき拒否記録を見落とし得ます。**最小修正:** 「系列 state・履歴・critic digest の保存先は系列 dir。pair の計測 WAL は計測 dir」と置換する。**正例:** login で `record-reject` した後の系列 WAL も説明と整合する。

3. **should — 測定しなかった停止結果に計測 campaign ID を載せる。** 根拠: [p3_s4_loop_policy.py:673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:673)。`stopped-before` では claim も計測 dir も作らない裁定なのに、stdout に予定上の ID を付けます。**放置時:** レポートが存在しない計測 campaign を参照し得ます。**最小修正:** 停止分岐では ID を付けず、対応する既存 test の期待値を戻す。**正例:** 予算停止時の stdout は `stopped-before` を示し、計測 ID を示さない。

4. **nit — runbook の欠番に対する一律の閲覧禁止は裁定より強い。** 根拠: [phase3-silo-policy-runbook.md:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/docs/phase3-silo-policy-runbook.md:169)。裁定は欠番と証跡の残存を定めています。**放置時:** 部分的な WAL まで確認対象から外れ、台帳と障害調査の参照が狭まります。**最小修正:** 「欠番の計測 dir は完了した pair の評価結果として数えない」とする。**正例:** 強制終了後の claim と WAL を証跡として確認しつつ、完了件数には数えない。

## 成立しなかった点検項目

- 指定された射影に job body は含まれないため、`tools/pegasus/p3_s4_loop_pegasus.sh` の実際の引数と stdout 保存経路は確認できませんでした。runbook の記載は driver の CLI と整合します。
- 焦点 test と計算ノードでの生死確認はこの review では実行していません。test の build・trace・bench は差し替えられており、実計算ノードでの完走結果の代わりにはなりません。

## 削除・簡略化の提案

- [test_p3_s4_loop_policy.py:825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:825) の claim 数と名前の一意性は、期待する `claim.stem` 集合との一致だけで足ります。
- [test_p3_s4_loop_policy.py:838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:838) の全 record に対する variant 存在確認は、直後の候補・stock の `STAGE_BUILD_START` 確認と重複します。後者を両 variant との集合一致にすると短く、build 到達も直接示せます。
- T3 は [T1 の 2 process 実行後](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:811) に state を巻き戻して追加実行すれば、独立した初回成功 process を 1 本減らせます。
- [test_p3_s4_loop_policy.py:788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:788) は各子 process でこの test module と大きな `test_campaign` fixture module を import します。小さな harness に必要な fixture だけを移せば起動費用を下げられます。ただし、移設に伴う重複が大きいなら現状維持が妥当です。
- [phase3-silo-policy-runbook.md:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/docs/phase3-silo-policy-runbook.md:122) の「campaign dir」は「系列 dir」に置換すると、直前の 2 layout 説明と揃います。