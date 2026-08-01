是正は完了しました。commit / git add / push、docs 編集は行っていません。

1. 変更箇所

- [tools/codex_worker_ledger.py](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:42)
  - 段番号が stage を決め、`role=author` は権限名にすぎない旨をコメント化。
  - `段6 fix2 implementation author` を `fix` 規則へ移動。
  - `author` 規則から段6枝を削除し、段5限定へ復元。
- [test_codex_worker_ledger.py](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:505)
  - healthy-wave の fix2 期待値を `author` から `fix` へ復元。
- [test_codex_worker_ledger.py](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:726)
  - precedence fixture の期待値を `fix` へ復元。
  - 指定された8先頭行を表駆動テストで固定。

`STAGE_RULES` の最終順序は次のとおりです。

1. `focus`: 段6 focused reviewer
2. `fix`: 段6 Codex fix worker、fix2 implementation author
3. `plan`: 段2 planner
4. `consult`: 段3 adversarial consultant
5. `author`: 段5 implementation worker (`role=author`) のみ
6. `review`: 段6の非 focused reviewer

2. 8件を固定した nodeid

`orchestrator/tests/test_codex_worker_ledger.py::test_stage_rules_follow_wave_stage_not_role_words`

補完する fixture テスト:

`orchestrator/tests/test_codex_worker_ledger.py::test_stage_rules_keep_fix2_author_in_fix_and_focus_specific`

3. pytest 実走結果

- 上記2 nodeid: `2 passed in 0.15s`
- `orchestrator/tests/test_codex_worker_ledger.py`: `74 passed in 0.32s`
- `orchestrator/tests/test_check_codex_output.py`: `18 passed in 0.24s`

追加検査:

- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし

4. 赤

赤はありません。

## 総括

fix2 の回帰は閉じました。段6の役割語 `author` に引かれず `fix` となり、`author` は段5限定です。指定8分類、既存 precedence fixture、両テストファイル全走を維持しており、検出力は落としていません。

親側では実10 sessionを再集計し、`author=171,736`、`fix=605,734`、総和 `2,757,982`、10 session、434 model calls に戻ることを確認してください。今回分は既存 staged 成果に対する `AM` の unstaged 差分として残しています。