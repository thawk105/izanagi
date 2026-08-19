現行の受理/拒否挙動は不変（5 category・96 identifier と unconditional loop のみ拒否）。

変更: [test_coder_effect_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1357-deny-table-shrink-guard/orchestrator/tests/test_coder_effect_gate.py:69) に frozen literal、:125 に3テストと既知残存コメントを追加。production は不変。

新規テスト:
- `test_frozen_deny_identifier_still_triggers_its_category`（96 parametrized cases）
- `test_frozen_deny_identifiers_total_is_96`
- `test_frozen_deny_identifiers_is_a_literal_not_derived_from_deny_table`

pytest は実装済み・未実走。`tools/run_tests.py` は Pegasus `qstat -Q rc=1` で子プロセス未起動（nodeid実行なし）。

波及可能性: `p3_s4_loop.py`、`digest.py`、共有fixture、production callerへの変更・波及なし。commit/docs編集なし。

## 総括

指定された test-only 実装を完了。  
意味的な全96件 probe と AST 自己参照防止を追加。  
pytest はインフラ障害により未実走。