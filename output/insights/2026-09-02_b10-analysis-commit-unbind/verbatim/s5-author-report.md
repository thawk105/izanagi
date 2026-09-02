## 変更した file

- [orchestrator/campaign/b10_backoff_shape_sweep.py:213](/work/1/SFC/tanab/izanagi/.codex/worktrees/b10-analysis-commit-unbind-author/orchestrator/campaign/b10_backoff_shape_sweep.py:213) — `core()` から `analysis_commit` を削除。[同 file:2360](/work/1/SFC/tanab/izanagi/.codex/worktrees/b10-analysis-commit-unbind-author/orchestrator/campaign/b10_backoff_shape_sweep.py:2360) — 過去 row の `analysis_commit` と `source_commit` の現行 HEAD 比較を削除。
- [orchestrator/tests/test_b10_backoff_shape_sweep.py:828](/work/1/SFC/tanab/izanagi/.codex/worktrees/b10-analysis-commit-unbind-author/orchestrator/tests/test_b10_backoff_shape_sweep.py:828) — WAL resume test を追加。[同 file:1238](/work/1/SFC/tanab/izanagi/.codex/worktrees/b10-analysis-commit-unbind-author/orchestrator/tests/test_b10_backoff_shape_sweep.py:1238) — 過去 block record test を追加。
- [orchestrator/tests/test_ccbench_spawn_sites.py:817](/work/1/SFC/tanab/izanagi/.codex/worktrees/b10-analysis-commit-unbind-author/orchestrator/tests/test_ccbench_spawn_sites.py:817) と [同 file:1961](/work/1/SFC/tanab/izanagi/.codex/worktrees/b10-analysis-commit-unbind-author/orchestrator/tests/test_ccbench_spawn_sites.py:1961) — AST で確認した sink 行 `2515` / `2911` を定義台帳と exact 集合へ反映。

## 追加したテスト

- `test_analysis_commit_drift_is_resumable_but_analysis_code_drift_is_not` — 受理: `analysis_commit` だけ異なる binding の `core()`、`as_dict()`、`binding_sha256` が一致し、既存同形の lock と `BUILD_START` を再開できます。拒否: `analysis_code_sha256` だけ異なる binding は `resume-binding` になります。
- `test_prior_block_record_allows_commit_drift_but_rejects_code_drift` — 受理: 過去の `analysis_commit` と `source_commit` を保持した row が、同一 code hash の別 HEAD binding で受理され、旧値も保持されます。拒否: nested binding を現行 code hash にそろえ、明示的 `analysis_code_sha256` だけ食い違わせると `resume-binding` になります。

## 実走結果

実装済み・未実走です。次の 5 nodeid を runner 経由で要求しました。

- `test_analysis_commit_drift_is_resumable_but_analysis_code_drift_is_not`
- `test_prior_block_record_allows_commit_drift_but_rejects_code_drift`
- `test_m17_and_p05_matching_bound_wal_is_resumable`
- `test_m08_legacy_wal_without_binding_is_rejected_for_one_reason`
- `test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`

Command:

```text
python3 tools/run_tests.py -q <上記5 nodeid>
```

結果は `qstat -Q preflight rc=1`、runner `rc=16`、`child_started=false` で、pytest は 0 件実行でした。2 test file 全体の `--collect-only` も同じ dispatch infrastructure failure で未実行です。

静的検査は成功しました。3 file の AST parse、保護対象の不変条件、台帳と実 sink の一致、`git diff --check` はすべて正常です。

## 波及の静的列挙

- `ident.py`、`loop.py`、`campaign_lock.py` は変更後の `as_dict()` を campaign identity と lock の不透明値として消費します。
- `build_admission.py`、`pipeline.py`、`wal.py`、`buildcache.py` は変更後の `binding_sha256` を receipt、WAL、cache identity へ伝播します。
- 共有 fixture `_binding()`、`_prior_block_record()` と既存 M17/M08 test は変更していません。
- direct consumer test として `test_campaign.py`、`test_p3_build_authority_cli.py`、`test_official_perf_closure.py`、`test_condition_meaning_gate.py` を確認しました。
- repo-wide AST・glob scanner も静的に探索しました。対象 predicate に変化はなく、行番号依存があった `test_ccbench_spawn_sites.py` の 2 箇所だけを更新しています。

## 総括

- プラン v2 の production 3 行削除と test 2 件追加を実装しました。
- `analysis_commit` field、形式検査、HEAD 記録、report・block row の provenance は維持しています。
- 6 個の内容束縛と `analysis_code_sha256` 比較も維持しています。
- 変更は指定された 3 file のみで、staging・commit・branch・remote 操作は行っていません。
- Pegasus dispatch 障害のため、状態は「実装済み・未実走」です。