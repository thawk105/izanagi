H1 と M12 を実装しました。commit、index 操作、docs 編集は行っていません。

| 所見 | 状態 | 対応 |
|---|---|---|
| H1 | partial | 実装とテスト追加は完了。pytest は基盤障害で未実走 |
| M12 | partial | 単一判定式と期待赤テストを追加。変異実走は未確認 |
| regressed | なし | 静的確認上、既存の決定層・closure・解決処理は変更なし |

変更内容:

- worklog の `title:` を canonical H2 と照合し、`identity_unit.outcome` を `matched` / `not-matched` / `not-applicable` で出力。
- decisions / failures は placeholder を除いた見出し本文を identity として利用。利用不能時は理由付き `not-applicable`。
- `signal_strength` を追加し、`strong` / `weak-positive` / `weak` を区別。
- `hit_targets` を file ごとの `matched_units`、`matched_structural_units`、`identity_unit_matched` を持つ構造へ変更。
- identity 一致時も `decisive: false` のままで、verdict は `indeterminate` を維持。
- 正の worklog title、title 不一致の負対照、placeholder identity、verdict 非決定性、新しい `hit_targets` schema のテストを追加。

M12 の判定式は [tools/check_branch_landed.py:1065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:1065) の 1 箇所です。正のテストでは本文一致数を 0 にして per-probe の `strong` を直接 assert するため、identity 規則を無効化すると `weak` になり、他層では masking されません。

F1〜F17、G1、G2、M1〜M11 については、closure 列挙、merge の積集合、exact-state 探索、候補の先行照合、closed-world history scan、receipt 判定、commit-ish 解決、ref 再取得、branch verdict 合成を変更していません。特に receipt 不在の `indeterminate`、probe の非決定性、`not-landed` の負証拠条件は維持されています。

テスト状況:

- pytest: 実装済み・未実走
- `python3 tools/run_tests.py orchestrator/tests/test_check_branch_landed.py` を再試行しましたが、いずれも `qstat -Q preflight rc=1`、child 未起動、rc=16 でした。
- focused 4 nodeid の実行も同じ基盤障害でした。
- 緑と報告できる pytest nodeid はありません。
- 両 Python file の AST parse と tool の `--help` 起動は rc=0。
- wrapper が生成した失敗 receipt 3 件は、許可範囲外の副産物を残さないため exact path で削除済みです。
- 最終 `git status --short` は許可された 2 file だけです。

## 総括

実装上は H1 と M12 を閉じ、既存の決定層には接続していません。閉じていないのは pytest による実証で、理由は Pegasus dispatch preflight 障害です。残る不確実性は対象 test file 全体の実走結果と実データ上の probe 出力です。親は基盤復旧後に対象 test file 全体、実データの着地済み worklog fragment、未着地 cleanup fragment 2 本、M12 変異の期待赤を確認してください。