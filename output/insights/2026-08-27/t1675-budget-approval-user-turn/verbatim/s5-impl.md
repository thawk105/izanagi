## 実装したもの

- `tools/s8b_budget_approval_preflight.py`
  - `skeleton` と read-only `verify` を実装済み。
  - production loader の受理条件を再現し、budget validator を再利用。
  - production の受理集合・pin・canonical path は無変更。
- `orchestrator/tests/test_s8b_budget_approval_preflight.py`
  - N1、過剰決定である旨を明記した N2、無変更検査、各 validation 契約を実装済み。
- `orchestrator/tests/README.md`
  - pytest 専用 allowlist に新規 test file を 1 行登録。

## 実走結果

- 試行範囲: `orchestrator/tests/test_s8b_budget_approval_preflight.py` 全体
- 実行: `python3 tools/run_tests.py -q orchestrator/tests/test_s8b_budget_approval_preflight.py`
- 結果: **未実走**。Pegasus dispatch が `qstat -Q preflight rc=1`、runner rc=16 で child 未起動。
- runner が禁止面 `output/pegasus-dispatch/264c14e7b93784a14b2351477b628433/receipt.json` を作成したため、指示どおり直ちに停止した。削除も行っていない。
- 緑と申告できる nodeid はない。

## 洗い出した meta-test

以下を母集合検査として特定したが、停止条件発生のため未実走。

- `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`
- `test_campaign_import_invariant.py` の real repository scan nodes
- `test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control`
- `test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`
- `test_login_headroom.py::test_local_budget_constants_are_defined_only_in_login_headroom_leaf`

## 波及可能性

- production caller `build_v2_g1_candidate` の受理・拒否挙動は未変更。
- `_load_budget_approval`、`_validate_budget`、`BUDGET_APPROVAL_SHA256` は未編集。
- active v1 freeze は `verify` の holdout 集合取得時に read-only で参照する。
- 共有 fixture `s8b_v2_freeze_fixture.py` と既存 consumer tests は未変更。
- 新規 test file により pytest collection、plain-runner coverage、repo-wide AST/import scan の母集合が増える。

## 総括

実装差分は許可された 3 面だけに限定した。  
`git add` と `git commit` は実行していない。  
現行 production は pin が `None` なら入力前に拒否し、loader 到達時は exact schema と canonical bytes 等を要求する。  
今回、その受理集合は変更していない。  
新規実装とテストは作成済みだが、テスト child は一件も起動していない。  
正規 runner 自身が禁止された `output/` へ receipt を書いたため、停止条件に従って作業を終了した。