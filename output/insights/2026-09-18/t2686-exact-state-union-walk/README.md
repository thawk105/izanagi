# T-2686 exact-state union walk 回収

着手mainは b2037abfa1467507cf92c851c83f262239f81641、元実装は
6ac18eb40a336e3022ad3f9e06f792cbca2e7b9e。元資料は original-evidence/ に保全した。
元focus1は370 passed/3 failed。3件とも履歴logを数える観測wrapperがdiff --name-onlyを含めたことが原因だった。
回収authorは7つの観測/注入selectorだけを修正し、productionと既存assertを変えていない。

独立レビュー2本はこの根因を静的closedとし、期待値変更による緑化を否定した。
比較driverの正常完了未確認は両者が摘出したreal所見で、隔離fixと焦点再レビューで修正した。
正常なindeterminate/不要phaseは許し、timeout/error/truncatedを正常完了の証拠にしない。
driverはrepo外で実行する一回限りの測定資材で、verbatim/ab_compare.py.mdは逐語保全である。

## この時点の実測

- 関連4file: check_branch_landed、check_branch_rescue、acceptance_schedule_order、
  update_acceptance_duration_ledger。正規run_testsで373 passed / 52.10秒。
  メモリ自動判定による上限付きローカル実行、観測ピーク2637873152 bytes。受入全走ではない。
- 直前の1時間枠の焦点dispatchはQUEで開始予定22:55:29だったため、runnerへのSIGTERMで取消し。
  qdel=0、target-end-after-qdel、orphan hold削除、rc16はsignal-abortでテストの赤ではない。
  再投入は既存walltime overrideで10分枠にしたが、自動判定がlocalを選んだ。
- 回収tip30fe5cc34の全史provenance: 11461件、新規違反なし、既知違反2件を報告。
  初回監査はauthor終端commitと重なりHEAD変化でrc2。HEAD固定後に再監査した。
- author初回はCLI0だが必須総括見出し欠落でlauncher1/f43_fragmentの未受理だった。
  実装残差を保全し、独立review2本がコード自体を監査した。未受理報告を成功証拠にしていない。

## 主張の境界

既存定義のAST比較では72個が不変、変更は_find_exact_state/_proof_unit/assessだけ。
追加は供給classとparser。これは候補供給以外の判定関数を変えなかった証拠であり、
全DAGでの同一性や時間内完走集合の保存の証明ではない。
旧s4のargv説明「65536+固定費約700が128KiBの半分未満」は算術誤り。
正しくはpath部分を64KiBに制限して残りを固定費等に残す閾値であり、値は変えない。
