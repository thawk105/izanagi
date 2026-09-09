## production の修正

- F1: seal 走査から `__pycache__` と `*.pyc` を除外。
- F2: arXiv 日付 delimiter は balanced な `[...]` / `"..."` のみ正規化。
- F4: OpenAlex の `B5-CTL-AND2023` cutoff を `2023-12-31` に固定。
- F5: live 集約器を private seam 化し、loader で status・media type・transport error・索引別観測形を検証。
- F6: 4 module の `__file__` を実 repo path に束縛。
- F7: live schema 内の registration seal 制約を standalone schema と同等化。

主要変更: [preflight.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1/orchestrator/axis_b5_search/preflight.py)、[runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1/orchestrator/axis_b5_search/runner.py)、[live schema](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1/orchestrator/schemas/axis_b5_search_live_preflight.schema.json)

## test の修正

T1〜T8 を既存 nodeid のまま実装しました。

- F3 の OpenAlex fixture を登録 OQO 構造へ修正。`get_rows` は `"200"` のまま。
- 2023 control の独立 literal AST、実 repo seal、cursor 終端、`非収録`、`run_leaf`、30-response transport、6 条件統合正例を追加。
- retry test に定数凍結 test である旨を明記。
- test 数は executor 34、parser 20、合計54で増減なし。

## 台帳

指定 producer を最後に一度だけ実行しました。

```text
mode=add-only
added=54
skipped_existing=0
excluded_total=0
```

## 実走した test

すべて指定の自走 harness です。

- `orchestrator/tests/test_axis_b5_search_executor.py` の全34 nodeid: `test_registration_accepts_exact_commit_tree_and_returns_schema_valid_seal` から `test_live_missing_member_is_schema_valid_and_false_side` まで。結果: 34 passed。
- `orchestrator/tests/test_axis_b5_search_parsers.py` の全20 nodeid: `test_contract_1_accepts_valid_page_with_b5_parser` から `test_saved_real_openalex_lookup_and_404_are_not_search_pages` まで。結果: 20 passed。
- `test_plain_runner_coverage.py::{test_allowlist_has_no_stale_or_self_runnable_entries,test_every_test_file_is_self_runnable_or_allowlisted,test_this_metatest_is_itself_self_runnable}`。結果: 3 passed。

## 波及可能性

production の live preflight 出力形式は変更していません。seal 成功条件と durable record の受理条件のみ厳格化されています。catalog、docs、軸1実装には触れておらず、外部 network も使用していません。

## 未実走・未実装

依頼された must-fix に未実装項目はありません。実 network を使う live preflight は禁止に従って未実走です。commit は作成していません。

## 総括

production 7件、test 8件、受入所要時間台帳更新を完了し、指定57 test はすべて通過しました。