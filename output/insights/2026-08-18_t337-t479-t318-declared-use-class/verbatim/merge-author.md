## 総括

- 競合 2 箇所を wave 側の必須 `declared_use_class` 仕様と main 側 fixture decorator の合成で解決。
- 指定 4 file は全て意味上噛み合っており、追加修正は不要。
- loop API の実欠落呼出しは production 0、test 0（意図的負例 1 件を除く）。
- 競合マーカーは 0 件。
- `check_codex_agents.py` と `check_docs.py` は成功。
- pytest は Pegasus の `qstat -Q` rc=1 により未実走。
- `git add`・commit・merge・reset は未実行。

### 競合解決

- [test_campaign.py:8511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/orchestrator/tests/test_campaign.py:8511): wave 側のテスト名・docstring・必須引数 TypeError 検査を残し、main 側の `ratified_enforcement_source` decorator を追加。
- [test_campaign.py:8624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/orchestrator/tests/test_campaign.py:8624): wave 側の `declared_use_class` identity 検査を残し、main 側の同 fixture decorator を追加。

### 4 file 監査

- `orchestrator/campaign/p3_autonomous_workload_trial.py` — 噛み合っている。main 側 helper 群を保持し、wave 側 `DECLARED_USE_CLASS = "exploration"` も保持。
- `orchestrator/tests/test_dev_wave_land.py` — 噛み合っている。fixture decorator と `declared_use_class="exploration"` を保持。
- `orchestrator/tests/test_p3_exploration_namespace.py` — 噛み合っている。module fixture、AST 閉包 helper、宣言 selector 検査を保持。
- `orchestrator/tests/test_p3_s4_loop_trigger_gating.py` — 噛み合っている。main 側 fixture decorator 群と wave 側 selector 検査を保持。

### 呼出し棚卸し

AST で repo の Python 553 file を確認。`orchestrator.campaign.loop.run_campaign` の直接呼出しは 45 件中 44 件が明示 selector 付き。欠落 1 件は `test_run_campaign_requires_declared_use_class` の意図的な負例で、実欠落は production 0 / test 0。別 API の `s8b_floor_campaign.run_campaign` は対象外。

### 検査・実走

- exact conflict marker: 0 件
- AST 構文エラー: 0 件
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- 実走 nodeid: なし。`tools/run_tests.py` は `qstat -Q` preflight rc=1、dispatch rc=16 で pytest 開始前に停止。実装済み・未実走。