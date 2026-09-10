## 実装した内容

- [s8c_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/campaign/s8c_preregistration.py:36)
  - 既存 bootstrap を逐語維持。
  - 独立した top-level `__main__` block で canonical module alias を代入。
- [s8c_gate_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/campaign/s8c_gate_report.py:10)
  - `import sys` を追加。
  - 最初の相対 import 前に `DIRECT_BOOTSTRAP` と byte-for-byte 一致する bootstrap を追加。
- [test_s8c_cli_entrypoints.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/test_s8c_cli_entrypoints.py:1)
  - live bytes 4 ファイルから一時 Git repo と1 commitを生成。
  - oracle は module scope で1回だけ評価。
  - blob・12 reason code の健全性を事前検査。
  - prereg/gate × path/module の4実プロセス入口を検査。

最終 diff は以下です。

- `s8c_preregistration.py`: +3行
- `s8c_gate_report.py`: +5行
- `test_s8c_cli_entrypoints.py`: +182行
- 合計: +190行、削除なし

変更は許可された3ファイルだけです。worktreeに対する `git add`、commit、stash、branch作成はしていません。

## 実走結果 (nodeid と rc)

すべて `PYTHONPATH=. python3 <test-file>` の自走 harness で実行しました。

- `test_s8c_cli_entrypoints.py::test_cli_entrypoint_matches_library_report[...]`
  - `[prereg-path]`
  - `[prereg-module]`
  - `[gate-path]`
  - `[gate-module]`
  - 4 passed、rc=0
- `test_s8c_gate_report.py::*`: 21 passed、rc=0
- `test_plain_runner_coverage.py::*`: 3 passed、rc=0
- `test_t671_source_binding.py::*`: 265 passed、rc=0
- `test_artifact_admission.py::*`: 146 passed、rc=0
- `test_ccbench_spawn_sites.py::*`: 44 passed、rc=0
- `test_pytest_collection_config.py::*`: 76 passed、rc=0
- `test_campaign_import_invariant.py::*`: rc=1、収集前に `GrowthTestHoldBypassRefused`。実装済み・未実走であり、緑とは扱っていません。
- `DIRECT_BOOTSTRAP` と gate側3行の逐語 `diff`: rc=0
- `git diff --check`: rc=0

関連する `test_s8c_preregistration_core.py`、`test_s8c_preregistration_invariant.py`、`test_s8c_preregistration_predicates.py`、trial/reflux系全suiteは実装済み・未実走です。指定に従い `tools/run_tests.py` と `python3 -m pytest` は使用していません。

## 未修正コードで落ちることの確認

新規 test fileだけを作り、production 2ファイルが未修正の状態で4ケースを実走しました。

- rc=1、3 failed / 1 passed
- `prereg-path`: oracleとの差で失敗。CLI側は12件一律 `ERROR / evaluator-exception`
- `prereg-module`: 同じ理由で失敗
- `gate-path`: stdoutが空で `JSONDecodeError`。相対 import tracebackが発生
- `gate-module`: 対照ケースとして通過

したがって、新設検査が現行欠陥に対して恒真でないことを実測済みです。

## meta-test と波及

新規 test file に直接反応する制約として、全 `test_*.py` の自走性を検査する `test_plain_runner_coverage.py` と pytest collection契約を確認し、いずれも緑でした。production形状を検査する campaign import invariant は growth hold により未実走ですが、bootstrapの逐語一致は別途確認済みです。

静的な波及候補は以下です。

- 所有外 caller:
  - `s8c_preregistration_evidence.py`
  - `p3_autonomous_workload_trial.py`
  - `trial_registry.py`
  - `campaign_lock.py`
- consumer test:
  - `test_s8c_gate_report.py`
  - `test_s8c_preregistration_{core,invariant,predicates}.py`
  - `test_p3_autonomous_workload_trial.py`
  - `test_reflux_origin_binding.py`
  - `test_trial_registry.py`
  - `test_t671_source_binding.py`
  - `test_artifact_admission.py`
  - `test_ccbench_spawn_sites.py`
- meta/shared fixture:
  - campaign repository scan
  - plain-runner/pytest collection
  - s8c candidate fixtureの `git add -A` 面

新規 fixture は当該 test file 内だけの module scopeで、一時repoは構築後read-onlyです。共有fixtureは変更していません。

## 受理集合が不変であることの根拠

変更前はlibrary oracleが非一律の12判定を返して `effective=False` である一方、prereg CLI 2経路は二重実体化により一律 `evaluator-exception`、gate pathはImportErrorでした。

変更後は4 CLI経路すべてで、commit、12組の `(id, status, reason_code)`、`effective` がlibrary oracleと完全一致し、`effective=False`、rc=1でした。

変更したのは `__main__` 時のmodule identityと直接起動bootstrapだけです。通常import時には新alias blockは実行されません。以下はすべて不変です。

- `_normalize_predicate_results` の型・件数・ID集合・evidence検査
- predicate/conjunction論理
- `DECIDER_VERSION` (`s8c-decider/v9`)
- 凍結成果物とdocs
- campaign lockのclosure集合と順序

coreは既存closure内のまま、gate reportはclosure外のままです。よって権威APIの受理集合・拒否理由集合は変わらず、壊れていたCLI transportだけが権威APIへ収束しました。

## 残った懸念・親へ返す判断

- campaign import invariantはholdを解除していないため未実走です。
- commit前なので、未実走suiteではHEAD blob束縛由来の指定済み赤が出る可能性があります。今回実走したsource-binding/admission suiteでは赤は出ませんでした。
- 親commit後に最初の焦点走を行い、裁定A-7の所要台帳登録を実施する必要があります。
- docs、凍結成果物、closure、既存テストは変更していません。

## 総括

裁定v2どおり3ファイルだけを変更し、CLI 4経路をlibrary oracleへ一致させました。修正後の関連実走は559件すべて緑で、唯一の未実走対象は明示的growth holdまたは今回走らせていない関連suiteです。commitは作成していません。