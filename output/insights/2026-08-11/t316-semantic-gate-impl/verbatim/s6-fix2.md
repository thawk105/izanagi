2件ともテスト側のみ修正しました。production/docs/commit 変更はありません。

| 項目 | 状態 | 対応 |
|---|---|---|
| R-1 | partial（実装済み・未実走） | 両 driver 用の最小 `L.PlannerProposal` をテスト内で直接構築。behavioral kill は維持 |
| R-2 | partial（実装済み・未実走） | 空白区切りの `x` identifier 列へ変更。4096 tokens の非発火と 4097 tokens の fail-closed を明示 |

変更箇所:

- [test_p3_s4_loop.py:934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:934)
- [test_coder_effect_gate.py:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:219)

実走を試みた nodeid:

- `orchestrator/tests/test_p3_s4_loop.py::test_both_real_auditor_drivers_reject_post_generation_contradiction`
- `orchestrator/tests/test_coder_effect_gate.py::test_hole_token_limit_fails_closed`

いずれも `tools/run_tests.py` が開始前に `qstat -Q preflight rc=1`、runner `rc=16` で停止しました。ログインノードの余裕も不足していたため、pytest は未実走です。親の全走を代替しません。

静的検査:

- `git diff --check`: pass
- `python3 tools/check_codex_agents.py`: pass
- `python3 tools/check_docs.py`: pass

所有外への波及可能性:

- R-1 は sort/trigger driver の引数契約、reject WAL、whiteboard projection に依存しますが、production は変更していません。
- R-2 は private lexer `_tokens` の maximal-munch/token-count 契約を明示的に固定します。lexer仕様変更時は境界テストも追随が必要です。
- 既知の `codex_roles` subset 赤、共有 fixture、他 consumer testには触れていません。

## 総括

R-1/R-2とも修正実装は完了していますが、実行基盤の `rc=16` により検証状態は `partial（実装済み・未実走）` です。選択した入力は、1 identifierが1 tokenになる空白区切りの `x` 列です。