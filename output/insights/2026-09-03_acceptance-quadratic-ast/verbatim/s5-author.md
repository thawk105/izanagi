## 実装したもの

- **単位 A:** [p3_b4_wiring_probe.py:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/campaign/p3_b4_wiring_probe.py:722) に CR/LF/CRLF 専用 splitter、UTF-8 byte offset 対応 helper を追加。[同:776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/campaign/p3_b4_wiring_probe.py:776) で行列を visitor に共有し、[同:882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/campaign/p3_b4_wiring_probe.py:882) で module あたり一度だけ分割。guard、strip、else、fallback は保存。
- **単位 B:** [test_p3_b4_wiring_probe.py:563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/tests/test_p3_b4_wiring_probe.py:563) と [同:1122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/tests/test_p3_b4_wiring_probe.py:1122) を `static` 作成後に `_load_runtime(guard, static)` を呼ぶ順序へ変更。
- **単位 C:** [同:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/tests/test_p3_b4_wiring_probe.py:153) から、全45 module oracle、UTF-8・全改行境界、guard/fallback 配線、module あたり分割一回 spy の4テストを追加。M-A1〜M-A6 の事前登録経路を網羅。

## 実走したもの

pytest nodeid はすべて **実装済み・未実走**です。緑とは申告しません。

補助検査では、両ファイルの構文、`git diff --check`、製品コードの stdlib private API 非依存、合成境界での stdlib 等価性、guard/fallback 配線、分割回数 `1` を確認しました。変更ファイルは指定された2件だけです。

射影内の meta-test `test_source_and_test_are_the_only_non_output_worktree_changes` は確認済みですが未実走です。射影外を読めないため、repo 全体の別の命名 meta-test は探索していません。

## 受理集合への影響

valid AST、構文エラー、inventory、seal、static manifest、proof switchpoint の受理・拒否条件は変更していません。同一 source の guard は従来の `ast.get_source_segment` と同じ文字列になり、`ast.unparse` fallback も維持されます。

単位 B は stable source での受理集合を変えず、static graph と runtime import を同一 snapshot に揃えます。既存の `attempts == 1` と `["exec", "import"]` は未変更です。

## 波及可能性

- 製品 caller: `_load_static_modules`、`_load_runtime` の省略時 fallback、`main`、および下流の `_proof_switchpoint` と `_build_inventory`。
- 共有 fixture: `static_runtime` と、その static/runtime を消費する静的 proof・inventory・main 系テスト。
- private caller: `_FunctionCallVisitor` を直接生成する所有外コードがあれば、第一引数は source 文字列から行列へ変わります。射影された範囲内に直接 caller はありません。
- consumer test: producer interdiction、exec/import 拒否、全 driver positive baseline、既存 guard 逐語検査。
- 射影外の caller・test は契約上未調査です。

## 総括

- 単位 A/B/C を指定2ファイルだけに実装しました。
- C-4 の一回 spy を含む4テストを追加しました。
- guard 抽出と受理・拒否意味論は維持しています。
- pytest は未実走で、親による実測が必要です。
- commit、add、docs 編集は行っていません。