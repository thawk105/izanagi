## 実装した内容

- [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/conftest.py:170)
  - `REAL_REPO_SERIAL_NODES` に裁定 R1 の22 nodeを追加。既存 node の削除は0件。
  - 誤った writer コメントを reader の over-approximation に修正。
  - slow oracle canary の誤った除外を削除。
  - 正本 node だけに `real_repo_serial_node` 印を付け、runtest protocol 全区間へ伝播。

- [patchharness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/patchharness.py:45)
  - pytest node 状態を `ContextVar` で保持。
  - `checkout()` が実 `external/ccbench` を受けた場合、未登録 node を fail-closed で拒否。
  - 例外に node id と「`REAL_REPO_SERIAL_NODES` へ追加せよ」を含めた。
  - pytest 外、登録済み node、tmp repo は従来どおり受理。

- [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_real_repo_serialization.py:37)
  - 独立 golden に同じ22 nodeを追加。
  - 既存 collection subprocess の per-item report に共有 fixture 閉包と consumer 集約を追加。
  - private API の欠落・型不一致は明示的に例外化。
  - canonical node による fixture 閉包検査、系統1/3の欠落 control、consumer 集約欠落 control を追加。
  - runtime guard 印が正本 node だけに付くことも監査。

- [repo_tree_util.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/repo_tree_util.py:21)
  - `_repo_status()` で危険な6個の Git env を除去。
  - `GIT_OPTIONAL_LOCKS=0` を設定。status bytes と既存 fails-closed 処理は不変。

- [source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/source_digest.py:761)
  - `_tracked_status_paths()` に同じ env 衛生を適用。
  - status の解析・非0終了拒否は不変。

- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_campaign.py:10216)
  - runtime guard の production pass、未登録拒否、tmp pass、登録済み pass を検査。
  - `source_digest` の env 上書き・危険変数除去を検査。

- [test_s8b_protocol_builder.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_s8b_protocol_builder.py:426)
  - `_repo_status()` の同型 env capture 回帰テストを追加。

R2・R3・R7、および AST 固定点解析は実装していません。保護対象2ファイルも未変更です。

## 実走結果

pytest node はすべて未実走です。`tools/run_tests.py` は次の投入すべてで、テスト開始前の `qstat -Q` preflight に失敗し rc=16 となりました。

- 閉包・golden 統合検査1 node: rc=16、未実走。
- 新規回帰3 node: rc=16、未実走。
- 影響を特定した meta-test 6 node: rc=16、未実走。
  - `test_real_repo_group_collection_exactly_matches_canonical_nodes`
  - `test_xdist_group_audit_rejects_synthetic_negative_controls`
  - `test_xdist_group_name_set_audit_rejects_isolated_negative_controls`
  - `test_canonical_real_repo_nodes_have_no_handwritten_xdist_group_decorator`
  - `test_real_repo_priority_order_is_literal_and_writers_follow_barrier`
  - `test_protocol_builder_repo_tree_guard_is_wired_to_real_root`

非 pytest 検査結果:

- `py_compile`（変更7ファイル）: rc=0
- `git diff --check`: rc=0
- 正本/golden一致・guard補助 probe: rc=0（65 node）
- fixture閉包・欠落・集約欠落補助 probe: rc=0
- 新規回帰関数の直接 probe: rc=0。ただしpytest緑とは数えていない。
- `tools/check_codex_agents.py`: rc=0
- `tools/check_docs.py`: rc=0

## 受理・拒否挙動の変更前後

変更前:

- 漏れていた22 nodeは real-repo loadgroup外。
- pytest中でも未登録 nodeによる実共有 submodule `checkout()` を受理。
- 2つのstatus経路は親のGit repository指定を継承し、optional refresh lockを許容。

変更後:

- 正本は43から65 node。追加22 nodeは同じ real-repo loadgroupへ入る。
- pytest中の実共有 submodule checkoutは、正本印付きnodeだけ受理し、未登録nodeを拒否。
- pytest外のproduction、tmp repo、正本nodeは従来どおり受理。
- status内容、dirty/clean判定、mandatory lock、非0終了のfail-closed拒否は不変。
- 変更は親Git envによるrepository誘導とoptional index refresh書込みだけを抑止。

## 波及可能性の静的列挙

- `patchharness.checkout()` の所有外 caller:
  - `s1_direct_comparison`
  - `p3_s4_loop*`
  - `p3_autonomous_workload_trial`
  - `s6_sort_sweep` / `s8a_trigger_sweep`
  - `t152_write_intent_coverage`
  - `silo_ladder_rung1`
- 共有 fixture:
  - `real_known_axes_doc` / `freeze_env` の11 consumer
  - `benchmark_snapshots` の17 consumer
- `_repo_status()` consumer:
  - protocol builder repo-tree guard
  - RuleOps inventory guard
  - serialization wiring meta-test
- `_tracked_status_paths()` consumer:
  - `assert_worktree_within_allowlist`
  - `resolve_evidence`
  - pipeline、buildcache、各 sweep/driverとそのconsumer test

## 予告した赤 / 環境由来の赤

- 実 submodule testはsandboxのindex/worktree管理領域制約で赤になり得ると事前予告したが、今回はrunner preflightで止まり未到達。
- 実際の停止は全投入で `qstat -Q preflight rc=1`、runner rc=16。
- 初回補助probeには総数を70と誤記したrc=1と、`skiputil` import path不足によるrc=1があった。65へ訂正し、`PYTHONPATH=orchestrator/tests:.`で再走して各rc=0。製品テストの期待値は変更していない。

## やり残し

- 上記pytest 9 nodeは実装済み・未実走。
- キューまたはログインノードのcgroup headroom回復後、`tools/run_tests.py`経由で再走が必要。
- 受入全走、実submodule canary、段6の変異matrixは親工程に残る。
- 指示どおりdocs編集・commitは行っていない。

## 総括

R1・R4・R5をコードとテストへ実装し、22 node追加、fixture閉包検査、runtime fail-closed guard、Git env衛生を反映しました。静的・補助検査は通過していますが、pytestはdispatch infrastructure rc=16のため未実走です。