F1 の fixture 移行を working tree に残しました。production gate、docs、`output/`、git index/commit は変更していません。変更は所有 test 5ファイルだけです。

### 101件の対応表

| 塊 | 件数 | 状態 | 対応 |
|---|---:|---|---|
| ratified emitter 連鎖（verify 77、freeze 3、oracle-report 2、oracle-driver 12） | 94 | partial | pytest 専用入口へ移し、official core へ `build_fn` を渡さない形に変更。再実測は dispatch 障害で未完 |
| 旧 source-evidence fake（materialization、freeze_io、floor deterministic） | 3 | partial | source-bound fixture evidence と新しい build capability 引数を追加。再実測未完 |
| floor default seam | 1 | partial | official permit の局所 test patch を追加。再実測未完 |
| materializer registry | 1 | closed | `**build_args` の単一 literal dictを厳密展開。静的 sentinel 直接実行は PASS |
| oracle CLI T-080 epoch | 1 | partial | subprocess fixture の epoch を決定的な `never-issued` に固定。再実測未完 |
| silo_ladder content binding | 1 | partial・未修正 | 凍結済み `output/` 成果物の再 pin が必要になるため停止 |
| regressed | 0 | — | pytest を再実行できていないため、新規回帰の観測なし |

合計101件です。

### official gate

gate は弱めていません。

- production core は [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f1/orchestrator/campaign/s8b_floor_campaign.py:2728) で `official + build_fn` を副作用前に拒否し、official materializer を `buildcache.build_v2` に固定しています。
- 固定テストは [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f1/orchestrator/tests/test_s8b_floor_campaign.py:1117) です。
- 新しい pytest 専用入口は [test_s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f1/orchestrator/tests/test_s8b_ratified_freeze.py:721) にのみ存在し、core 呼出しへ `build_fn` を渡していません。
- official gate の直接 smoke は PASS、出力作成がないことも確認しました。

### silo_ladder

再 pin はしていません。対象 pin は [silo_ladder_rung1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f1/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:25) 内にあり、README が「committed 実証 JSON」と明記しています。現行 driver SHA は `df3fb11…`、凍結成果物の pin は `92affaab…` です。

したがって非凍結族ではなく、かつ `output/` 無編集契約に該当すると判断し、成果物も driver も変更していません。

### 検査

pytest は次の3 dispatchを試しましたが、すべて実行前に `qstat -Q preflight rc=1`、runner rc=16で停止しました。

- ratified verify: `semantic_happy_path_loads...` / `source_blob_mismatch_rejected`
- ratified freeze: `test_happy_path_resolves_and_loads` / `test_journal_manifest_may_precede_generation_and_executable_mode_is_accepted`
- floor: `test_run_campaign_core_rejects_official_materializer_injection_before_side_effects` / `test_materializer_registry_covers_all_python_build_launches`

実行済み pytest nodeid は0件で、green は主張しません。101件すべての再走、各 S8b test file のその他、フルスイート、build、campaign 実走は未実行です。

静的検査は以下が成功しました。

- 変更5ファイルの `py_compile`
- materializer registry sentinel の直接実行
- official materializer gate smoke
- `git diff --check`
- `tools/check_codex_agents.py`
- `tools/check_docs.py`

### 直さず報告した項目

- `silo_ladder` の1件：凍結済み `output/` の再 pin が必要。
- 期待値誤りと判断した項目、所有外ファイルを必要とする未修正項目はありません。

## 総括

1. official materializer gate は維持し、fixture のみを test-local 入口へ分離しました。
2. admission-aware build の新引数と source evidence は fixture 側で正規形を供給し、期待値は変更していません。
3. 確定して残る赤は silo_ladder の1件です。ほか100件は修正済みですが、計算ノード dispatch 障害のため受入確認待ちです。