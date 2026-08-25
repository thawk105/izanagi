## 対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F1 | closed | cluster、argfile、`-o`、ini/config 注入を親・`_job_run` 共通 validator で拒否 |
| F2 | closed | binding、bound envelope、正規 PBS ID を現行 request に必須化。legacy tests/provenance は維持 |
| F3 | closed | local、detached、同一 Python、`tools/run_tests.py` を両側で構造検証 |
| F4 | closed | 4 種の comprehension の element、iterator、条件式を taint 追跡 |
| F5 | closed | legacy v1 の 4 キーを literal fixture と exact assertion で固定 |
| F6 | closed | hook テストから日本語診断文の assertion を除去し、拒否結果だけを固定 |

## 直した内容

- [tools/pegasus/dispatch_compute.py:745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:745)
  - mutation wrapper/runner の構造検証
  - cluster、`@argfile`、`-o`、`--override-ini`、`-c`、`--config-file` と省略形の拒否
- [tools/pegasus/dispatch_compute.py:854](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:854)
  - PBS job ID と bound envelope の検証
- [tools/pegasus/dispatch_compute.py:951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:951)
  - 現行 request の binding/envelope/PBS 三重 gate
  - legacy 無束縛分岐の限定維持
- [tools/check_docs.py:3357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/check_docs.py:3357)
  - `ListComp`、`SetComp`、`DictComp`、`GeneratorExp` の taint 追跡
- [orchestrator/tests/test_pegasus_dispatch_compute.py:3972](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_pegasus_dispatch_compute.py:3972)
  - 現行 bound envelope と legacy envelope を区別する fixture
- [orchestrator/tests/test_pegasus_dispatch_compute.py:4062](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_pegasus_dispatch_compute.py:4062)
  - legacy v1 の 4 キーを literal 固定
- [orchestrator/tests/test_check_docs.py:2584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_check_docs.py:2584)
  - comprehension 4 種の負例
- [orchestrator/tests/test_hooks.py:3993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_hooks.py:3993)
  - 診断文依存を除去

## F1 の残余

塞いだ綴り:

- 直接指定の `-k`、`-m`、`-p`
- `-qkselected`、`-qmslow`、`-qpforeign_plugin`
- `-qoaddopts=...` を含む cluster
- `@file`
- `-o addopts=...`、`--override-ini=...` と省略形
- `-c`、`--config-file` と省略形
- 既存の nodeid、deselect、ignore、環境変数、force-dispatch 経路

能動探索では、親と compute 子は同じ `_validate_task_argv` を通り、runner tail を無検査で渡す別経路は見つかりませんでした。正常な `-q`、`-rf`、tracked test path は引き続き受理します。

## F2 の残余

現行 request は次を同時に満たさなければ子を起動しません。

- `request_binding == sha256-job-script/v1`
- request path/hash/export/exec を含む実在 `dispatch.sh` と probe
- `request.json` という envelope 配置
- 正規形式の `PBS_JOBID`
- request bytes と指定 hash の一致

2 引数 CLI と公開 3 引数 CLI はともに同じ `_job_run` gateへ収束します。他の CLI 起動分岐は見つかりませんでした。

互換分岐は意図どおり残しています。hash marker のない既存 envelope、正規 PBS ID、task が tests/provenance の全条件を満たす v1/v2 request だけが無束縛で通ります。mutation/generic はこの分岐を通りません。

## 追加した負例

- F1 親側:
  - `::test_mutation_argv_policy_rejects_before_qsub[...]`
  - `cluster-k`、`cluster-m`、`cluster-p`、`argfile`、`short-addopts`、`cluster-addopts`、`long-addopts`、`abbreviated-addopts`、`config-file`、`abbreviated-config-file`
  - qsub 前の拒否を証明
- F1 forged `_job_run` 側:
  - `::test_mutation_argv_policy_fires_independently_in_job_run[...]`
  - 同じ spellings が child 起動前に拒否されることを証明
- F2:
  - `::test_public_three_arg_job_run_requires_bound_pbs_envelope[...]`
  - mutation/generic それぞれで binding、envelope、PBS 欠落・不正を拒否
  - `::test_unbound_new_request_is_rejected_but_inflight_v2_tests_survives`
  - v1 tests、v2 tests、v2 provenance の in-flight 互換を証明
- F3:
  - `::test_mutation_structure_policy_rejects_before_qsub[...]`
  - `::test_mutation_structure_policy_fires_independently_in_job_run[...]`
  - `dispatch-mode`、`missing-detached`、`foreign-python`、`foreign-runner`、`abbreviated-mode-override`
- F4:
  - `::test_dispatch_inventory_rejects_tasks_alias_through_list_comp`
  - `::test_dispatch_inventory_rejects_tasks_alias_through_set_comp`
  - `::test_dispatch_inventory_rejects_tasks_alias_through_dict_comp`
  - `::test_dispatch_inventory_rejects_tasks_alias_through_generator_exp`

F5 は負例ではなく、既存正例を 4 literal key の独立 fixture に変更しました。

## 未実走

pytest、qsub、Web 検索は実行していません。

実施した静的確認:

- `python3 tools/check_docs.py`: `check_docs: 違反なし`
- 全 5 対象ファイルの AST parse: 成功
- parametrized case と `ids` の件数照合: 成功
- `git diff --check`: 成功
- U+0300〜U+036F の混入検査: なし

補助 compile コマンドは既存 hook がコマンド中のファイル名を Pegasus 実行体と誤認して拒否したため未実行です。commit、add、branch、push は行っていません。

## 総括

F1〜F6 はすべて closed です。attempt 契約と mutation harness/wrapper の受理契約には触れず、legacy in-flight 互換を維持したまま、指定された 5 ファイル内だけを変更しました。