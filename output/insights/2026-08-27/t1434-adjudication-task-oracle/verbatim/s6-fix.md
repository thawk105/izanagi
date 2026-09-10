実装済み・未実走です。RB1 専用の delegating-spy テストを追加し、production、RB2、既存テスト期待値には触れていません。

追加 nodeid:

- `orchestrator/tests/test_codex_reasoning_ab.py::test_replay_manifest_forwards_external_task_manifest_digest_at_loader_boundary`

[対象テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13660) は既存 4-slot paired fixture と実 `_replay_manifest` を使い、実 `_load_adjudication` へ委譲します。assert は外部 manifest と loader 受領値の canonical digest 比較 1 個だけです。mutation 台帳コメントも M7 をこの新規 node へ付け替えました。

受理の含意: 外部 alpha/beta manifest が replay から loader へそのまま渡る正例であり、alpha 2 slot、beta 2 slot の paired schedule が通ります。  
拒否の含意: M7 により組込み `TASK_MANIFEST` が渡されると、この digest 比較だけが不一致になり、既存 artifact・union 検査には帰属しません。

実走状況:

- sanctioned runner で新規 node を実行。
- `qstat -Q preflight rc=1`、runner rc=16。
- `child_started=false` のため pytest 本体は未起動です。
- AST parse、関数名一意性、assert 数 1、parametrize 数 0、`git diff --check` は静的確認済みです。
- runner が ignored な `output/pegasus-dispatch/.../receipt.json` を自動生成しました。手動編集や削除はしていません。

制約 meta-test として以下を洗い出しました。いずれも未実走です。

- `test_growth_test_holds_contract.py::test_inventory_count_and_key_digest_are_independently_pinned`
- `test_growth_test_holds_contract.py::test_complete_collection_rejects_valid_shape_function_typo`
- `test_pytest_collection_config.py::test_bare_pytest_collection_is_scoped_by_testpaths`
- `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`
- `test_pytest_collection_config.py::test_sanctioned_runner_ignore_keeps_growth_hold_completeness_guard`
- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
- `test_real_repo_serialization.py::test_receipt_memo_consumer_inventory_and_optouts_are_complete`
- `test_real_repo_serialization.py::test_oracle_environment_consumer_inventory_and_registry_are_complete`
- import 時の `growth_test_holds.enforce_held_functions`

静的には新規 node は growth-hold 未登録、real-repo group 未登録で、receipt/oracle inventory が走査する別ファイルにも該当しません。

波及可能性:

- ownership 外の production caller は `_replay_manifest -> _load_adjudication` の 1 箇所です。
- `_replay_manifest` の consumer は `verify_manifest`、その委譲 consumer は `aggregate_manifest` です。
- 共有 fixture の consumer は既存 replay 正例、cross-task parent/second-reader 負例、dimension-join 負例、および新規 spy node です。
- monkeypatch は関数 scope で復元され、共有 fixture自体は変更していません。
- 既存テスト期待値、production、docs、RB2 は変更していません。
- 開始時から存在した `tools/codex_reasoning_ab.py` の未 commit 変更と未追跡 insights はそのままです。
- commit、add、stash などは禁止された Git 操作は行っていません。

意図的に赤のまま残したテストはありません。ただし pytest 未起動のため、緑とも報告しません。

## 総括

RB1 の M7 帰属を、実 loader へ委譲する spy と canonical digest の単一 assert だけで独立させました。状態は実装済み・未実走です。