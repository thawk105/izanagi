## 対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| レビュー A must-fix 1 | partial（実装済み・未実走） | module-level import を除去し、関数内 import 化。構文・import smoke は成功 |
| レビュー B must-fix 1 | partial（実装済み・未実走） | T12 に T13 と同じ resolver double を追加 |
| 帰結 3 | partial（実装済み・未実走） | T1〜T13 内の `S.sort_swo_oracle.ORACLE_CONTRACT_ID` は 0 件 |

## 実装した内容

- [p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/p3_s4_loop_sort.py:68) の import を指定の一行へ逐語で復元しました。
- `_require_sort_oracle_contract()` は [関数内 import](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/p3_s4_loop_sort.py:337) を使い、exact `str`・契約 ID 完全一致・不一致時 `ValueError` を維持しています。
- [T12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/tests/test_p3_s4_loop_sort.py:1792) に `lambda *_args, **_kwargs: request.evidence` を追加しました。
- 契約 ID を使う各 test/helper は `sort_swo_oracle` から直接 import します。`test_buildcache_v2.py` は未変更です。

## 実走結果

- `tools/run_tests.py orchestrator/tests/test_p3_s4_loop_sort.py`
- `tools/run_tests.py orchestrator/tests/test_p3_s4_loop_sort.py::test_bound_evidence_token_is_the_cache_authority`

両方とも `qstat -Q preflight rc=1`、runner `rc=16` で子が起動せず、実走済みの緑 nodeid はありません。自動生成された一時 dispatch receipt 2 件は削除し、禁止領域への残存変更はありません。

静的検査は `compile()`、`git diff --check`、結合文字検査に成功しました。driver、`p3_b4_launcher`、`s6_sort_sweep`、trigger test の import smoke では、driver の `sort_swo_oracle` module 属性が存在しないことを確認しました。

## 所有外への波及

grep で確認した主な import consumer は次のとおりです。

- production: `p3_b4_launcher.py`、`s6_sort_sweep.py`、遅延 import の `p3_b4_closed_critic.py`、`s1_direct_comparison.py`、`s8b_expected_materialization.py`
- tests: `test_p3_s4_loop.py`、`test_p3_s4_loop_trigger_gating.py`、`test_p3_exploration_namespace.py`、`test_p3_b4_launcher.py`、`test_campaign.py`、`test_s1_direct_comparison.py`
- source/path consumer: `p3_b4_wiring_probe.py`、`p3_b4_raw_record_producer.py`、`t080_freeze_migration.py`、`test_pytest_collection_config.py`、duration ledger / serialization tests

driver の直接 top-level edgeと module 属性は実装前の形へ戻りました。なお oracle module 自体は既存の `orchestrator.critic.digest` 経由でもロードされますが、これは今回追加した依存ではありません。

`git diff --name-only` は指定された 2 ファイルだけです。verify / oracle / diff 検疫 / auditor の受理集合、`default_cfg` / `search_config`、backoff、引数なし caller の bytes は変更していません。

## 総括

- 3 所見とも実装修正は完了しています。
- runner infrastructure failure のため、状態は closed ではなく partial（実装済み・未実走）です。
- 指示外の受理集合変更はありません。
- 親側で T1〜T13 と既存の焦点範囲を再実走してください。