## 総括

(a) guard は [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/check_docs.py:3925) に追加しました。

- 可視対象節が exact 1 件
- 対応する raw byte slice が exact 1 件

この両方を満たす場合だけ waiter consumer 義務を検査します。適用箇所は `9 段状態機械`、`DW-C00`、`DW-O01` です。canonical target の regular-file 検査は独立して常時実行されます。

これにより、`DW-O01` 重複と malformed `DW-C00—` は既存の構造検査だけが報告し、新設検査の cascade は止まります。壊れた入力自体は引き続き fail-closed です。

(b) negative 9 件は構造 guard を通過します。

- stage 6/9・decoy 系 6 件: `9 段状態機械` H2 と byte sliceを維持したまま本文だけを変異
- `dw-c00-fenced`: `DW-C00` の節構造を維持し、義務行だけを不可視化
- `dw-o01-wrong-pid-source`: `DW-O01` の節構造を維持し、義務内容だけを変更
- `target-symlinked`: docs 構造と無関係な、常時実行される target 検査で検出

したがって guard 後も各 finding 分岐へ到達します。既存 2 テストの期待値と negative 9 件は編集していません。

(c) 実走結果:

- `python3 tools/check_docs.py`: rc=0、`違反なし`
- `python3 tools/check_codex_agents.py`: rc=0
- `git diff --check`: rc=0
- 焦点 pytest 11 node: runner rc=16（`qstat -Q preflight rc=1`）。pytest 本体は未実走のため、緑は主張しません。

(d) 今回編集したファイル:

- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/check_docs.py:3925) — 構造 guard と guarded consumer 検査（〜4009行）

[orchestrator/tests/test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/orchestrator/tests/test_check_docs.py:2957) は段 5 の既存未commit差分のままで、今回編集していません。docs 編集・commit も行っていません。