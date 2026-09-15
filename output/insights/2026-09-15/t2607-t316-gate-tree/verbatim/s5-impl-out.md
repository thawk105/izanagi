## 変更前の受理・拒否挙動

素の CCBench 木では、patch 由来の `CCBENCH_BACKOFF_FIXED` と未参照変数 3 件により関門が拒否します。

S6 は family 欠落、未発行 record、受領証不一致、許可された inert exact pair 以外を拒否します。この判定は変更していません。

## 実装した変更

変更ファイルは次の 3 件です。

- [probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/tools/pegasus/probes/t316_sandbox_backend_probe.py:1826)
- [probe.pbs](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:54)
- [test_t316_sandbox_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/orchestrator/tests/test_t316_sandbox_probe.py:1729)

実装内容：

- `checkout` 後、patch 前に requested の基底 identity を検査・記録。
- 1 回の `applied` 内で outside／inside の両 build を実行。
- 関門と両 build に同じ requested root、control に素の submodule を渡す。
- requested root を read-only mount に追加。scratch 内なら拒否。
- 共有 configure から指定された未参照変数 3 件を除去。
- Python／PBS の束縛一覧に patch と `patchharness.py` を追加。

残る configure の全 20 変数は、次の参照先を静的に確認しました。configure 実走による確認は未了です。

| 変数 | 参照先 |
|---|---|
| `CCBENCH_TRACE`、`BACK_OFF`、`BACKOFF_FIXED`、`ADD_ANALYSIS`（後三者も `CCBENCH_` 接頭辞） | `Options.cmake`、指定 patch |
| `CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION`、`CCBENCH_NO_WAIT_OF_TICTOC`、`CCBENCH_WAL` | silo の `CMakeLists.txt` |
| `ENABLE_SANITIZER`、`CCBENCH_CCACHE` | CCBench の CMake 設定 |
| `FETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST}` | `ThirdParty.cmake`／FetchContent |
| `CMAKE_BUILD_TYPE`、`CMAKE_TOOLCHAIN_FILE`、`CMAKE_PREFIX_PATH`、`CMAKE_CXX_FLAGS`、`CMAKE_{C,CXX}_COMPILER`、`CMAKE_{C,CXX}_COMPILER_LAUNCHER` | CMake 標準変数 |

`condition_meaning_gate.py`、schema、受領証の形、既存の拒否診断は変更していません。

## 追加したテストと制約 meta-test

新規 6 関数・8 node を追加しました。

- 関門／両 build の実 path、control の出所、適用回数・包含順序。
- requested 基底の wrong HEAD／dirty 拒否。
- outside 短絡／関門例外時の cleanup。
- 未参照変数 3 件の不在。
- scratch 内 requested の拒否・撤去。
- patch／harness の実行入力束縛。

実配線テストは実際の関数呼び出しを追跡し、関門や harness を stub に置換していません。小さな fixture の実行であり、実 CCBench の受入走とは別です。

既存 fixture に新しい束縛入力を追加し、dirty 検査の対象も追加しました。既存 assertion は緩和していません。新規 node は既存 `_run()` からも収集されます。

inventory は確認済みです。一時 repo を対象とする既存 patchharness テストと同じ除外範囲のため、更新していません。duration 台帳も未編集です。

## 実走した nodeid と結果

**pytest の実走 nodeid は 0 件です。**

新規テスト、既存 t316 全体、以下の meta-test／関連テストを runner に指定しましたが、全 3 回とも pytest 起動前に停止しました。

- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
- `test_official_perf_closure.py` 全体
- `test_hooks.py::test_bash_pegasus_execution_inventory_is_synchronized`
- `test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes`
- `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
- `test_campaign.py` の checkout／applied 関連 3 node

結果は `qstat -Q preflight rc=1`、runner 終了コード 16、`child_started=false` です。

実行できた静的 checker：

- `check_codex_agents.py`：終了コード 0。
- `check_docs.py`：終了コード 0、違反なし。

## 未実走・未解決

**実装済み・未実走**です。以下は未確認です。

- pytest、変異 M1〜M7、揮発源変更後の再検証。
- 実 CCBench の supply 緑、両 build、trace-disabled、walltime。
- Python／PBS の個別構文確認。

事前に想定した docs 由来の赤はありません。pytest が未起動のため、回帰の有無は判断できません。

## 波及可能性の静的列挙

- production caller：同ファイルの `observe_s6`／`run_probe`、起動元の `t316_sandbox_backend_probe.pbs`。
- 新規依存：`patchharness.checkout`／`applied`、`silo-backoff-fixed.patch`。
- 共有 fixture：`_prepare_execution_binding_repo` と、その execution-binding consumer tests。
- 外部の参照 test：`test_hooks.py`、`test_official_perf_closure.py`。
- 登録情報：`tools/pegasus/admission_registry.json`。実行体の追加はありません。

検索範囲内で `_execute_ccbench_build` の所有外 caller はありませんでした。

## 総括

plan v2 のコード・テストを実装しました。docs、台帳、Git の index／branch は変更せず、commit／push もしていません。親の受入全走が必要で、closed とは申告しません。

実行ガードは、テスト追記用 shell コマンドと Python／PBS の構文確認を拒否しました。理由はそれぞれ「保護対象パスと不透明構文の同居」「Pegasus 実行体のログインノード実行禁止」です。追記は専用編集ツールで完了しましたが、構文確認は未完了です。