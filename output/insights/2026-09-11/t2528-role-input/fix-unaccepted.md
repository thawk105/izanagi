**実装済み・未実走です。**

| 状態 | 差分・検査・所見 |
|---|---|
| partial | [対象helper](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2528-role-input/orchestrator/tests/test_reflux_originless_compatibility.py:622)のみ訂正。planner・trigger-gating各々の固定old/new hashでjournal 6箇所＋report 1箇所を検査・置換。 |
| partial | pytestは親の実測待ち。既存job991683の1 FAILが解消したとは未確認。`git diff --check`は問題なし。 |
| regressed | 新たな回帰の実測なし。既存helper・比較集合・assertion・受理／拒否集合は維持。 |
| closed | 該当なし。未実走のため完了判定は保留。 |

文書bytesと`HEAD`旧版から独立確認した固定SHA-256：

| role | old → new |
|---|---|
| planner | `3a3d35fafbaaeac5b63c8f36a1cd4542fba4e7cef2793c71cc59fc40884c8374` → `1d6b1603dbbb7c776202cd20a300e60e01b9119b55068ddfcce3e83714f646da` |
| trigger-gating | `a03045c86027ec09e01d0727557eaa653c8f04d0929c007a4f129902742a2db0` → `00405a9639b150372cf0881699090090cf688d4a61fa22651e0aee27e8d5279a` |

直接consumerは`test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set`。共有fixtureは`test_p3_autonomous_workload_trial.t325_registered_trial`、実行経路は`A.run_trial`／`FixtureRoleProvider`。関連consumer検査はoriginless、codex_agents／role_runtime、p3_s4_loop、p3_autonomous_workload_trial、claude_transport／effort_levels／role_session_isolationです。

docs・adapter等への編集、add／commit／mergeは行っていません。